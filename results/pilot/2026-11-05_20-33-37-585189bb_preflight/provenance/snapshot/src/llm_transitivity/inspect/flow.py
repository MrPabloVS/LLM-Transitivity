"""Compose the coverage pilot from verified inputs and shared execution policy."""

from copy import deepcopy
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
)
from llm_transitivity.evidence.metadata import EXPERIMENT_ID, run_metadata
from llm_transitivity.inspect.tasks import hs_zero_shot

MODELS = [
    (model.identifier, model.provider, model.supports_reasoning)
    for model in MODEL_SPECS
]
MODEL_GROUPS = {model.identifier: model.generation_group for model in MODEL_SPECS}


def _reasoning_policy(model: ModelSpec, policy: GenerationPolicy) -> str:
    if not model.supports_reasoning:
        return "not supported"
    return "enabled" if policy.reasoning_enabled else "disabled"


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
        args["reasoning_enabled"] = policy.reasoning_enabled
    return FlowModel(
        name=f"openrouter/{model.identifier}",
        model_args=args,
        config=GenerateConfig(
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
    root: Path, manifest: dict, policy: GenerationPolicy, preflight: bool
) -> dict:
    context = run_metadata(root, manifest, policy=policy)
    context["phase"] = "preflight" if preflight else "coverage-pilot"
    context["planned_responses"] = (
        len(MODELS) if preflight else context["pilot_case_count"] * len(MODELS)
    )
    context["selected_cases_per_model"] = (
        1 if preflight else context["pilot_case_count"]
    )
    timestamp = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    folder = f"{timestamp}-{context['experiment_run_id'][:8]}"
    if preflight:
        folder += "_preflight"
    context["results_root"] = str(Path("results/pilot") / folder)
    context["results_folder_timezone"] = "America/Argentina/Buenos_Aires"
    context["generation_groups"] = dict(MODEL_GROUPS)
    context["requested_routing"] = {
        model.identifier: {
            "provider_only": [model.provider],
            "service_tier": model.service_tier,
            "allow_fallbacks": policy.provider_fallback,
            "require_parameters": policy.require_parameters,
        }
        for model in MODEL_SPECS
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
        factory=hs_zero_shot,
        args={"dataset": f"pilot/{Path(entry['pilot_path']).stem}", "root": str(root)},
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
            f"generation_group:{MODEL_GROUPS[model.identifier]}",
            reasoning_tag,
        ],
        # Flow replaces factory metadata, so retain the complete dataset context.
        metadata={
            **deepcopy(prepared.metadata),
            "phase": phase,
            "selected_case_count": 1 if preflight else len(entry["selected_rows"]),
            "pilot_manifest_sha256": context["pilot_manifest_sha256"],
            "original_revision": context["original_revision"],
            "requested_model": model.identifier,
            "generation_group": MODEL_GROUPS[model.identifier],
            "requested_provider": model.provider,
            "requested_service_tier": model.service_tier,
            "actual_service_tier": None,
            "service_tier_verified": False,
            "actual_provider": None,
            "reasoning_verified": False,
            "reasoning_policy": reasoning,
        },
    )


def build_pilot_spec(root: Path, *, preflight: bool = False) -> FlowSpec:
    manifest = verify(root)
    policy = GENERATION_POLICY
    context = _run_context(root, manifest, policy, preflight)
    # Validate every dataset in either phase before constructing runnable tasks.
    prepared = {
        entry["dataset"]: hs_zero_shot(
            f"pilot/{Path(entry['pilot_path']).stem}", root=str(root)
        )
        for entry in manifest["datasets"]
    }
    selected = manifest["datasets"][:1] if preflight else manifest["datasets"]
    tasks = [
        _flow_task(root, entry, prepared[entry["dataset"]], model, policy, context)
        for model in MODEL_SPECS
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
            tags=[f"experiment:{EXPERIMENT_ID}", f"phase:{context['phase']}"],
            metadata=context,
            log_samples=True,
            log_model_api=True,
        ),
        tasks=tasks,
    )
