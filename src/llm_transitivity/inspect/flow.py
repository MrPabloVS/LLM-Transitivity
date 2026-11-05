"""Create the six-model coverage pilot after checking the full source chain."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from inspect_ai.model import GenerateConfig
from inspect_flow import FlowModel, FlowOptions, FlowSpec, FlowTask

from llm_transitivity.datasets.pilot import MANIFEST, verify
from llm_transitivity.domain.config import GENERATION_POLICY, MODEL_SPECS
from llm_transitivity.evidence.metadata import EXPERIMENT_ID, run_metadata
from llm_transitivity.evidence.serialization import digest
from llm_transitivity.inspect.tasks import hs_zero_shot

# Preserve existing imports while deriving each view from the model catalog.
MODELS = [
    (model.identifier, model.provider, model.supports_reasoning)
    for model in MODEL_SPECS
]
MODEL_GROUPS = {model.identifier: model.generation_group for model in MODEL_SPECS}


def build_pilot_spec(root: Path, *, preflight: bool = False) -> FlowSpec:
    manifest = verify(root)
    policy = GENERATION_POLICY
    common = run_metadata(root, manifest, policy=policy)
    phase = "preflight" if preflight else "coverage-pilot"
    common["phase"] = phase
    common["planned_responses"] = (
        len(MODELS) if preflight else common["pilot_case_count"] * len(MODELS)
    )
    common["selected_cases_per_model"] = 1 if preflight else common["pilot_case_count"]
    timestamp = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    run_folder = f"{timestamp}-{common['experiment_run_id'][:8]}"
    if preflight:
        run_folder += "_preflight"
    results = Path("results/pilot") / run_folder
    common["results_root"] = str(results)
    common["results_folder_timezone"] = "America/Argentina/Buenos_Aires"
    common["generation_groups"] = MODEL_GROUPS
    # FlowTask metadata replaces factory metadata, so preserve it explicitly.
    prepared = {
        entry["dataset"]: hs_zero_shot(
            f"pilot/{Path(entry['pilot_path']).stem}", root=str(root)
        )
        for entry in manifest["datasets"]
    }
    tasks = []
    for model_spec in MODEL_SPECS:
        model = model_spec.identifier
        provider = model_spec.provider
        supports_reasoning = model_spec.supports_reasoning
        model_args = {
            "stream": policy.stream,
            "max_retries": policy.sdk_max_retries,
            "provider": {
                "only": [provider],
                "allow_fallbacks": policy.provider_fallback,
                "require_parameters": policy.require_parameters,
            },
        }
        reasoning_policy = (
            ("enabled" if policy.reasoning_enabled else "disabled")
            if supports_reasoning
            else "not supported"
        )
        reasoning_tag = (
            f"reasoning:{reasoning_policy}"
            if supports_reasoning
            else "reasoning:not-supported"
        )
        if supports_reasoning:
            model_args["reasoning_enabled"] = policy.reasoning_enabled
        for entry in manifest["datasets"][:1] if preflight else manifest["datasets"]:
            tasks.append(
                FlowTask(
                    factory=hs_zero_shot,
                    args={
                        "dataset": f"pilot/{Path(entry['pilot_path']).stem}",
                        "root": str(root),
                    },
                    model=FlowModel(
                        name=f"openrouter/{model}",
                        model_args=model_args,
                        config=GenerateConfig(
                            max_tokens=policy.max_output_tokens,
                            max_connections=policy.max_connections,
                            max_retries=policy.request_max_retries,
                            timeout=policy.request_timeout_seconds,
                            cache_prompt=policy.cache_prompt,
                        ),
                    ),
                    fail_on_error=False,
                    sample_id=[entry["selected_rows"][0]["original_row"]]
                    if preflight
                    else None,
                    tags=list(prepared[entry["dataset"]].tags or [])
                    + [
                        f"phase:{phase}",
                        f"model:{model}",
                        f"model_family:{model.split('/')[0]}",
                        f"provider:{provider}",
                        f"generation_group:{MODEL_GROUPS[model]}",
                        reasoning_tag,
                    ],
                    metadata={
                        **prepared[entry["dataset"]].metadata,
                        "phase": phase,
                        "selected_case_count": 1
                        if preflight
                        else len(entry["selected_rows"]),
                        "pilot_manifest_sha256": digest((root / MANIFEST).read_bytes()),
                        "original_revision": manifest["baseline_revision"],
                        "requested_model": model,
                        "generation_group": MODEL_GROUPS[model],
                        "requested_provider": provider,
                        "actual_provider": None,
                        "reasoning_verified": False,
                        "reasoning_policy": reasoning_policy,
                    },
                )
            )
    return FlowSpec(
        log_dir=str(root / results / "inspect"),
        log_dir_create_unique=False,
        store=None,
        options=FlowOptions(
            max_tasks=policy.max_tasks,
            max_samples=policy.max_samples,
            retry_attempts=policy.flow_retry_attempts,
            retry_cleanup=policy.flow_retry_cleanup,
            tags=[f"experiment:{EXPERIMENT_ID}", f"phase:{phase}"],
            metadata=common,
            log_samples=True,
            log_model_api=True,
        ),
        tasks=tasks,
    )
