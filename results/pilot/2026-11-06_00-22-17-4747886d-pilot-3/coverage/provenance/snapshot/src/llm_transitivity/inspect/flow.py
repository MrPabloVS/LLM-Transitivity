"""Compose the coverage pilot from verified inputs and shared execution policy."""

import json
from copy import deepcopy
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from inspect_ai import Task
from inspect_ai.model import GenerateConfig
from inspect_flow import FlowModel, FlowOptions, FlowSpec, FlowTask

from llm_transitivity.datasets.pilot import verify
from llm_transitivity.domain.config import (
    GENERATION_POLICY,
    MODEL_SPECS,
    GenerationPolicy,
    ModelSpec,
    profile_models,
)
from llm_transitivity.evidence.metadata import EXPERIMENT_ID, run_metadata
from llm_transitivity.evidence.serialization import digest
from llm_transitivity.inspect.tasks import hs_zero_shot, load_zero_shot

MODELS = [
    (model.identifier, model.provider, model.supports_reasoning)
    for model in MODEL_SPECS
]
MODEL_GROUPS = {model.identifier: model.generation_group for model in MODEL_SPECS}


def _reasoning_policy(model: ModelSpec, policy: GenerationPolicy) -> str:
    if not model.supports_reasoning:
        return "not supported"
    enabled = (
        policy.reasoning_enabled
        if model.reasoning_enabled is None
        else model.reasoning_enabled
    )
    return "enabled" if enabled else "disabled"


def _flow_model(model: ModelSpec, policy: GenerationPolicy) -> FlowModel:
    """Build independent mutable request settings for one task."""
    args = {
        "stream": policy.stream,
        "max_retries": policy.sdk_max_retries,
        "provider": {
            "only": [model.provider],
            "allow_fallbacks": policy.provider_fallback,
            "require_parameters": policy.require_parameters,
        },
    }
    if model.supports_reasoning:
        args["reasoning_enabled"] = _reasoning_policy(model, policy) == "enabled"
    return FlowModel(
        name=f"openrouter/{model.identifier}",
        model_args=args,
        config=GenerateConfig(
            reasoning_effort=model.reasoning_effort,
            max_tokens=policy.max_output_tokens,
            max_connections=policy.max_connections,
            max_retries=policy.request_max_retries,
            timeout=policy.request_timeout_seconds,
            cache_prompt=policy.cache_prompt,
            extra_body={"service_tier": model.service_tier},
            extra_headers={"X-OpenRouter-Metadata": "enabled"},
        ),
    )


def _run_context(
    root: Path,
    manifest: dict,
    policy: GenerationPolicy,
    preflight: bool,
    models: tuple[ModelSpec, ...],
    profile: str,
    load: bool,
) -> dict:
    context = run_metadata(root, manifest, policy=policy)
    if profile in {"pilot2", "pilot3"}:
        base = Path("docs/model_cards")
        card_manifest = base / (
            "pilot-3-manifest.json"
            if profile == "pilot3"
            else "pilot-2.0-manifest.json"
        )
        cards = json.loads((root / card_manifest).read_text())
        if {entry["model_id"] for entry in cards["models"]} != {
            m.identifier for m in profile_models(profile)
        }:
            raise ValueError("Pilot 2.0 cards do not match the model profile")
        context["pilot_name"] = "Pilot 3" if profile == "pilot3" else "Pilot 2.0"
        context["model_reasoning_policies"] = {
            model.identifier: {
                "policy": _reasoning_policy(model, policy),
                "effort": model.reasoning_effort,
            }
            for model in models
        }
        context["generation_policy"]["reasoning"] = (
            "per-model; see model_reasoning_policies"
        )
        context["model_cards_manifest"] = str(card_manifest)
        context["source_sha256"][str(card_manifest)] = digest(
            (root / card_manifest).read_bytes()
        )
        for entry in cards["models"]:
            for name in ("card.md", "model.json", "endpoints.json"):
                relative = base / entry["files"][name]["path"]
                actual = digest((root / relative).read_bytes())
                if actual != entry["files"][name]["sha256"]:
                    raise ValueError("Pilot 2.0 model card changed: " + str(relative))
                context["source_sha256"][str(relative)] = actual
    context["phase"] = (
        "preflight" if preflight else "load-validation" if load else "coverage-pilot"
    )
    context["profile"] = profile
    context["concurrency"] = policy.max_samples
    context["planned_responses"] = (
        len(models)
        if preflight
        else (216 if load else context["pilot_case_count"]) * len(models)
    )
    context["selected_cases_per_model"] = (
        1 if preflight else 216 if load else context["pilot_case_count"]
    )
    timestamp = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    folder = f"{timestamp}-{context['experiment_run_id'][:8]}"
    if preflight:
        folder += "_preflight"
    context["results_root"] = str(Path("results/pilot") / folder)
    context["results_folder_timezone"] = "America/Argentina/Buenos_Aires"
    context["generation_groups"] = {
        model.identifier: model.generation_group for model in models
    }
    context["requested_routing"] = {
        model.identifier: {
            "provider_only": [model.provider],
            "service_tier": model.service_tier,
            "allow_fallbacks": policy.provider_fallback,
            "require_parameters": policy.require_parameters,
        }
        for model in models
    }
    return context


def _flow_task(
    root: Path,
    entry: dict,
    prepared: Task,
    model: ModelSpec,
    policy: GenerationPolicy,
    context: dict,
) -> FlowTask:
    phase = context["phase"]
    preflight = phase == "preflight"
    reasoning = _reasoning_policy(model, policy)
    reasoning_tag = (
        f"reasoning:{reasoning}"
        if model.supports_reasoning
        else "reasoning:not-supported"
    )
    return FlowTask(
        factory=load_zero_shot if phase == "load-validation" else hs_zero_shot,
        args={"root": str(root)}
        if phase == "load-validation"
        else {"dataset": f"pilot/{Path(entry['pilot_path']).stem}", "root": str(root)},
        model=_flow_model(model, policy),
        fail_on_error=False,
        sample_id=[entry["selected_rows"][0]["original_row"]] if preflight else None,
        tags=list(prepared.tags or [])
        + [
            f"phase:{phase}",
            f"model:{model.identifier}",
            f"model_family:{model.identifier.split('/')[0]}",
            f"provider:{model.provider}",
            f"service_tier:{model.service_tier}",
            f"generation_group:{model.generation_group}",
            reasoning_tag,
            *(
                [f"reasoning_effort:{model.reasoning_effort}"]
                if model.reasoning_effort
                else []
            ),
        ],
        # Flow replaces factory metadata, so retain the complete dataset context.
        metadata={
            **deepcopy(prepared.metadata),
            "phase": phase,
            "selected_case_count": 1 if preflight else len(entry["selected_rows"]),
            "pilot_manifest_sha256": context["pilot_manifest_sha256"],
            "original_revision": context["original_revision"],
            "requested_model": model.identifier,
            "generation_group": model.generation_group,
            "requested_provider": model.provider,
            "requested_service_tier": model.service_tier,
            "actual_service_tier": None,
            "service_tier_verified": False,
            "actual_provider": None,
            "reasoning_verified": False,
            "reasoning_policy": reasoning,
        },
    )


def build_pilot_spec(
    root: Path,
    *,
    preflight: bool = False,
    profile: str = "sonnet",
    selected_models: tuple[str, ...] | None = None,
    concurrency: int | None = None,
    load: bool = False,
    max_tasks: int | None = None,
) -> FlowSpec:
    if (concurrency is not None and concurrency not in {16, 32, 64}) or (
        load and preflight
    ):
        raise ValueError("Invalid concurrency or conflicting execution phases")
    if max_tasks is not None and max_tasks < 1:
        raise ValueError("Active task count must be positive")
    models = profile_models(profile, selected_models)
    manifest = verify(root)
    policy = (
        GENERATION_POLICY
        if concurrency is None
        else replace(
            GENERATION_POLICY, max_samples=concurrency, max_connections=concurrency
        )
    )
    if max_tasks is not None:
        datasets_per_model = 1 if preflight or load else len(manifest["datasets"])
        policy = replace(
            policy,
            max_tasks=max_tasks,
            max_connections=policy.max_samples * min(max_tasks, datasets_per_model),
        )
    context = _run_context(root, manifest, policy, preflight, models, profile, load)
    if max_tasks is not None:
        context["max_connections_per_model"] = policy.max_connections
        context["connection_limit_scope"] = "shared model endpoint pool"
        limits = [
            min(policy.max_samples, 1 if preflight else len(entry["selected_rows"]))
            for entry in (
                manifest["datasets"][:1] if preflight else manifest["datasets"]
            )
            for _ in models
        ]
        context["configured_sample_ceiling"] = policy.max_samples * min(
            max_tasks, len(limits)
        )
        context["effective_sample_ceiling"] = sum(
            sorted(limits, reverse=True)[:max_tasks]
        )

    selected = manifest["datasets"][:1] if preflight else manifest["datasets"]
    prepared = {}
    if not load:
        prepared = {
            entry["dataset"]: hs_zero_shot(
                f"pilot/{Path(entry['pilot_path']).stem}", root=str(root)
            )
            for entry in manifest["datasets"]
        }
    if load:
        from llm_transitivity.datasets.load_pool import verify_load_pool

        pool = verify_load_pool(root)
        prepared = {"load_216": load_zero_shot(root=str(root))}
        selected = [{"dataset": "load_216", "selected_rows": pool["selected_rows"]}]
        for relative in ["datasets/load/manifest.json", "datasets/load/cases_216.json"]:
            context["source_sha256"][relative] = digest((root / relative).read_bytes())
    tasks = [
        _flow_task(root, entry, prepared[entry["dataset"]], model, policy, context)
        for model in models
        for entry in selected
    ]
    return FlowSpec(
        log_dir=str(root / context["results_root"] / "inspect"),
        log_dir_create_unique=False,
        store=None,
        options=FlowOptions(
            max_tasks=policy.max_tasks,
            max_samples=policy.max_samples,
            retry_attempts=policy.flow_retry_attempts,
            retry_cleanup=policy.flow_retry_cleanup,
            tags=[f"experiment:{EXPERIMENT_ID}", f"phase:{context['phase']}"]
            + (
                ["pilot:3"]
                if profile == "pilot3"
                else ["pilot:2.0"]
                if profile == "pilot2"
                else []
            ),
            metadata=context,
            log_samples=True,
            log_model_api=True,
        ),
        tasks=tasks,
    )
