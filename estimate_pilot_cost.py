"""Estimate pilot costs from actual inputs and public fixed-provider quotes."""

import json
from datetime import UTC, datetime
from decimal import Decimal
from functools import partial
from pathlib import Path

import requests
import tiktoken

from pilot_config import MODELS, PROJECT_ROOT, build_pilot_spec
from prepare_pilot import MANIFEST, digest, json_bytes


def generation_cost(
    input_tokens: int,
    output_per_case: int,
    multiplier: int = 1,
    *,
    cases: int,
    input_price: Decimal,
    output_price: Decimal,
    request_price: Decimal,
) -> float:
    """Include input, output and per-request charges for every planned attempt."""
    return float(
        (
            input_tokens * input_price
            + cases * (output_per_case * output_price + request_price)
        )
        * multiplier
    )


def estimate(root: Path) -> dict:
    spec = build_pilot_spec()
    manifest = json.loads((root / MANIFEST).read_text())
    system = json.loads((root / manifest["system_prompt"]["path"]).read_text())[0]
    prompts = [
        row[2]
        for entry in manifest["datasets"]
        for row in json.loads((root / entry["pilot_path"]).read_text())
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
    config = spec.tasks[0].model.config
    attempts = config.max_retries + 1
    for task in spec.tasks:
        if (
            task.model.config.max_tokens != config.max_tokens
            or task.model.model_args["max_retries"] != 0
        ):
            raise ValueError("Unexpected output or SDK retry configuration")
    rows = []
    for model, provider, _ in MODELS:
        url = f"https://openrouter.ai/api/v1/models/{model}/endpoints"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        endpoints = [
            e
            for e in response.json()["data"]["endpoints"]
            if e.get("tag") == provider and e.get("status") == 0
        ]
        if len(endpoints) != 1:
            raise ValueError(
                f"{model}: expected one available standard endpoint for {provider}"
            )
        pricing = endpoints[0]["pricing"]
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
                "source": url,
                "pricing_snapshot": pricing,
                "cases": len(prompts),
                "input_usd_per_million": float(input_price * 1000000),
                "output_usd_per_million": float(output_price * 1000000),
                "short_4_output_tokens_usd": cost(proxy_tokens, 4),
                "verbose_128_output_tokens_usd": cost(proxy_tokens, 128),
                "output_cap_1024_usd": cost(proxy_tokens, config.max_tokens),
                "byte_input_output_cap_all_attempts_usd": cost(
                    byte_scenario, config.max_tokens, attempts
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
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "estimator_sha256": digest((root / "estimate_pilot_cost.py").read_bytes()),
        "manifest_sha256": digest((root / MANIFEST).read_bytes()),
        "configuration_sha256": digest((root / "pilot_config.py").read_bytes()),
        "pilot_cases_per_model": len(prompts),
        "models": len(MODELS),
        "planned_responses": len(prompts) * len(MODELS),
        "output_token_limit": config.max_tokens,
        "inspect_max_retries": config.max_retries,
        "sdk_max_retries": 0,
        "maximum_planned_attempts_per_response": attempts,
        "input_proxy_tokens_per_model": proxy_tokens,
        "input_byte_scenario_tokens_per_model": byte_scenario,
        "assumptions": [
            "o200k_base text counts plus 16 framing tokens per case are a proxy, not each provider's native count.",
            "The byte-input scenario uses UTF-8 text bytes plus 256 framing tokens per case; it is a planning envelope, not a proven tokenizer bound.",
            "Standard short-prompt provider rates; no reasoning, tools, cache or batch discounts.",
            "Short and verbose scenarios use 4 or 128 output tokens per case with one attempt.",
            "The final scenario charges every possible attempt for the full output cap, including failed attempts.",
            "Account funding fees, taxes, unreported provider behavior and future price changes are excluded.",
            "These estimates do not enforce an account or run spending limit.",
        ],
        "quotes": rows,
        "totals_usd": {key: sum(row[key] for row in rows) for key in scenarios},
    }


if __name__ == "__main__":
    report = estimate(PROJECT_ROOT)
    path = PROJECT_ROOT / "docs/pilot_cost_estimate.json"
    path.write_bytes(json_bytes(report))
    print(json.dumps(report["totals_usd"], indent=2))
    print(f"Saved {path}")
