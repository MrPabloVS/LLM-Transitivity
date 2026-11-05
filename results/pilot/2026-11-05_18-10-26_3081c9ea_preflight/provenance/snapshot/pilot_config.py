"""Create the six-model coverage pilot after checking the full source chain."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from inspect_ai.model import GenerateConfig
from inspect_flow import FlowModel, FlowOptions, FlowSpec, FlowTask

from experiment_metadata import EXPERIMENT_ID, run_metadata
from inspect_tasks import PROJECT_ROOT, hs_zero_shot
from prepare_pilot import MANIFEST, digest, verify

MODELS = [
    ("openai/gpt-4o-mini", "openai", False),
    ("openai/gpt-6-luna", "openai", True),
    ("anthropic/claude-sonnet-4.5", "anthropic", True),
    ("anthropic/claude-sonnet-5", "anthropic", True),
    ("google/gemini-2.5-flash-lite", "google-ai-studio", True),
    ("google/gemini-3.1-flash-lite", "google-ai-studio", True),
]
MODEL_GROUPS = {
    "openai/gpt-4o-mini": "earlier",
    "anthropic/claude-sonnet-4.5": "earlier",
    "google/gemini-2.5-flash-lite": "earlier",
    "openai/gpt-6-luna": "later",
    "anthropic/claude-sonnet-5": "later",
    "google/gemini-3.1-flash-lite": "later",
}


def build_pilot_spec(*, preflight: bool = False) -> FlowSpec:
    manifest = verify(PROJECT_ROOT)
    common = run_metadata(PROJECT_ROOT, manifest)
    phase = "preflight" if preflight else "coverage-pilot"
    common["phase"] = phase
    common["planned_responses"] = (
        len(MODELS) if preflight else common["pilot_case_count"] * len(MODELS)
    )
    common["selected_cases_per_model"] = 1 if preflight else common["pilot_case_count"]
    timestamp = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    run_folder = f"{timestamp}_{common['experiment_run_id'][:8]}"
    if preflight:
        run_folder += "_preflight"
    results = Path("results/pilot") / run_folder
    common["results_root"] = str(results)
    common["results_folder_timezone"] = "America/Argentina/Buenos_Aires"
    common["generation_groups"] = MODEL_GROUPS
    # FlowTask metadata replaces factory metadata, so preserve it explicitly.
    prepared = {
        entry["dataset"]: hs_zero_shot(f"pilot/{Path(entry['pilot_path']).stem}")
        for entry in manifest["datasets"]
    }
    tasks = []
    for model, provider, supports_reasoning in MODELS:
        model_args = {
            "stream": False,
            "max_retries": 0,
            "provider": {
                "only": [provider],
                "allow_fallbacks": False,
                "require_parameters": True,
            },
        }
        if supports_reasoning:
            model_args["reasoning_enabled"] = False
        for entry in manifest["datasets"][:1] if preflight else manifest["datasets"]:
            tasks.append(
                FlowTask(
                    factory=hs_zero_shot,
                    args={"dataset": f"pilot/{Path(entry['pilot_path']).stem}"},
                    model=FlowModel(
                        name=f"openrouter/{model}",
                        model_args=model_args,
                        config=GenerateConfig(
                            max_tokens=1024,
                            max_connections=2,
                            max_retries=2,
                            timeout=60,
                            cache_prompt=False,
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
                        "reasoning:disabled"
                        if supports_reasoning
                        else "reasoning:not-supported",
                    ],
                    metadata={
                        **prepared[entry["dataset"]].metadata,
                        "phase": phase,
                        "selected_case_count": 1
                        if preflight
                        else len(entry["selected_rows"]),
                        "pilot_manifest_sha256": digest(
                            (PROJECT_ROOT / MANIFEST).read_bytes()
                        ),
                        "original_revision": manifest["baseline_revision"],
                        "requested_model": model,
                        "generation_group": MODEL_GROUPS[model],
                        "requested_provider": provider,
                        "actual_provider": None,
                        "reasoning_verified": False,
                        "reasoning_policy": "disabled"
                        if supports_reasoning
                        else "not supported",
                    },
                )
            )
    return FlowSpec(
        log_dir=str(PROJECT_ROOT / results / "inspect"),
        log_dir_create_unique=False,
        store=None,
        options=FlowOptions(
            max_tasks=1,
            max_samples=2,
            retry_attempts=1,
            retry_cleanup=False,
            tags=[f"experiment:{EXPERIMENT_ID}", f"phase:{phase}"],
            metadata=common,
            log_samples=True,
            log_model_api=True,
        ),
        tasks=tasks,
    )
