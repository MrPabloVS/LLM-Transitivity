"""Estimate pilot costs from actual inputs and public fixed-provider quotes."""

import json
from datetime import UTC, datetime
from decimal import Decimal
from functools import partial
from pathlib import Path

import tiktoken

from llm_transitivity.costs.calculation import generation_cost
from llm_transitivity.costs.pricing import provider_quote
from llm_transitivity.datasets.pilot import MANIFEST, verify
from llm_transitivity.domain.config import GENERATION_POLICY, profile_models
from llm_transitivity.evidence.metadata import package_sources
from llm_transitivity.evidence.serialization import digest


def estimate(
    root: Path, *, profile: str = "sonnet", followup: bool = False, full: bool = False
) -> dict:
    if full and followup:
        raise ValueError("Full corpus and pilot follow-up are separate estimates")
    if followup and profile != "haiku":
        raise ValueError("The follow-up schedule requires the haiku profile")
    manifest = verify(root)
    policy = GENERATION_POLICY
    system = json.loads((root / manifest["system_prompt"]["path"]).read_text())[0]
    prompts = [
        row[2]
        for entry in manifest["datasets"]
        for row in json.loads(
            (root / entry["working_path" if full else "pilot_path"]).read_text()
        )
    ]
    encoding = tiktoken.get_encoding("o200k_base")
    proxy_tokens = sum(
        len(encoding.encode(system, disallowed_special=()))
        + len(encoding.encode(text, disallowed_special=()))
        + 16
        for text in prompts
    )
    byte_scenario = sum(
        len(system.encode("utf-8")) + len(text.encode("utf-8")) + 256
        for text in prompts
    )
    attempts = policy.maximum_planned_attempts
    rows = []
    models = profile_models(profile)
    coverage_prompts = prompts
    if followup:
        from llm_transitivity.datasets.load_pool import verify_load_pool

        verify_load_pool(root)
        load_prompts = [
            row[2]
            for row in json.loads((root / "datasets/load/cases_216.json").read_text())
        ]
    for model_spec in models:
        prompts = coverage_prompts
        if followup:
            prompts = [coverage_prompts[0]] + load_prompts
            if "claude-haiku" in model_spec.identifier:
                prompts = prompts + coverage_prompts
        proxy_tokens = sum(
            len(encoding.encode(system, disallowed_special=()))
            + len(encoding.encode(text, disallowed_special=()))
            + 16
            for text in prompts
        )
        byte_scenario = sum(
            len(system.encode()) + len(text.encode()) + 256 for text in prompts
        )
        model = model_spec.identifier
        provider = model_spec.provider
        url, pricing = provider_quote(model_spec)
        input_price = Decimal(pricing["prompt"])
        output_price = Decimal(pricing["completion"])
        request_price = Decimal(pricing.get("request", "0"))

        cost = partial(
            generation_cost,
            cases=len(prompts),
            input_price=input_price,
            output_price=output_price,
            request_price=request_price,
        )

        rows.append(
            {
                "model": model,
                "provider": provider,
                "service_tier": model_spec.service_tier,
                **(
                    {
                        "reasoning_enabled": model_spec.reasoning_enabled
                        if model_spec.reasoning_enabled is not None
                        else policy.reasoning_enabled,
                        "reasoning_effort": model_spec.reasoning_effort,
                    }
                    if profile in {"pilot2", "pilot3"}
                    else {}
                ),
                "source": url,
                "pricing_snapshot": pricing,
                "cases": len(prompts),
                "input_proxy_tokens": proxy_tokens,
                "input_byte_scenario_tokens": byte_scenario,
                "input_usd_per_million": float(input_price * 1000000),
                "output_usd_per_million": float(output_price * 1000000),
                "short_4_output_tokens_usd": cost(proxy_tokens, 4),
                "verbose_128_output_tokens_usd": cost(proxy_tokens, 128),
                "output_cap_1024_usd": cost(proxy_tokens, policy.max_output_tokens),
                "byte_input_output_cap_all_attempts_usd": cost(
                    byte_scenario, policy.max_output_tokens, attempts
                ),
            }
        )
    scenarios = [
        "short_4_output_tokens_usd",
        "verbose_128_output_tokens_usd",
        "output_cap_1024_usd",
        "byte_input_output_cap_all_attempts_usd",
    ]
    return {
        "source_sha256": {
            path: digest((root / path).read_bytes()) for path in package_sources(root)
        },
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "estimator_sha256": digest(
            (root / "src/llm_transitivity/costs/estimate.py").read_bytes()
        ),
        "manifest_sha256": digest((root / MANIFEST).read_bytes()),
        "configuration_sha256": digest(
            (root / "src/llm_transitivity/inspect/flow.py").read_bytes()
        ),
        "experiment_config_sha256": digest(
            (root / "src/llm_transitivity/domain/config.py").read_bytes()
        ),
        "pilot_cases_per_model": sum(
            len(e["selected_rows"]) for e in manifest["datasets"]
        )
        if full
        else len(coverage_prompts),
        "models": len(models),
        "profile": profile,
        "followup": followup,
        **(
            {
                "scope": "full-corpus",
                "full_cases_per_model": len(coverage_prompts),
                "pilot_cases_per_model": sum(
                    len(e["selected_rows"]) for e in manifest["datasets"]
                ),
            }
            if full
            else {}
        ),
        "planned_responses": sum(row["cases"] for row in rows),
        "output_token_limit": policy.max_output_tokens,
        "inspect_max_retries": policy.request_max_retries,
        "sdk_max_retries": policy.sdk_max_retries,
        "maximum_planned_attempts_per_response": attempts,
        "input_proxy_tokens_per_model": None if followup else proxy_tokens,
        "input_byte_scenario_tokens_per_model": None if followup else byte_scenario,
        "assumptions": [
            "o200k_base text counts plus 16 framing tokens per case are a proxy, not each provider's native count.",
            "The byte-input scenario uses UTF-8 text bytes plus 256 framing tokens per case; it is a planning envelope, not a proven tokenizer bound.",
            (
                "Standard short-prompt rates; output scenarios include reasoning and final text for the two enabled Pilot 2.0 models; no tools, cache or batch discounts."
                if profile in {"pilot2", "pilot3"}
                else "Standard short-prompt provider rates; no reasoning, tools, cache or batch discounts."
            ),
            "Short and verbose scenarios use 4 or 128 output tokens per case with one attempt.",
            "The final scenario charges every possible attempt for the full output cap, including failed attempts.",
            "Account funding fees, taxes, unreported provider behavior and future price changes are excluded.",
            "These estimates do not enforce an account or run spending limit.",
        ],
        "quotes": rows,
        "totals_usd": {key: sum(row[key] for row in rows) for key in scenarios},
    }
