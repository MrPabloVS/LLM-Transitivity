"""Compose all verified source cases with the Pilot 3 model controls."""

from copy import deepcopy
from pathlib import Path

from inspect_ai.util import AdaptiveConcurrency

from llm_transitivity.datasets.inputs import load_input
from llm_transitivity.datasets.pilot import verify
from llm_transitivity.inspect.flow import build_pilot_spec
from llm_transitivity.inspect.samples import task_metadata, task_tags


def build_full_spec(root: Path):
    manifest = verify(root)
    inputs = {
        e["dataset"]: load_input(root, e["dataset"]) for e in manifest["datasets"]
    }
    if sum(len(data.records) for data in inputs.values()) != 54000:
        raise ValueError("Expected 54000 verified corpus records")
    spec = build_pilot_spec(root, profile="pilot3", concurrency=32, max_tasks=108)
    context = spec.options.metadata
    context.update(
        phase="full-corpus",
        corpus_case_count=54000,
        selected_cases_per_model=54000,
        planned_responses=324000,
        configured_sample_ceiling=3456,
        effective_sample_ceiling=3456,
        max_connections_per_model=None,
        connection_limit_scope="adaptive shared model endpoint pool",
        selection="All verified source rows in original dataset order",
        cases_per_stratum=500,
    )
    adaptive = AdaptiveConcurrency(
        min=10,
        start=20,
        max=576,
        cooldown_seconds=15,
        decrease_factor=0.8,
        scale_up_percent=0.05,
    )
    context["adaptive_connections"] = adaptive.model_dump()
    context["generation_policy"]["adaptive_connections"] = adaptive.model_dump()
    context["generation_policy"]["max_connections"] = None
    context["results_root"] = context["results_root"].replace(
        "results/pilot/", "results/full/"
    )
    spec.log_dir = str(root / context["results_root"] / "inspect")
    spec.options.tags = [
        t for t in spec.options.tags if not t.startswith(("phase:", "pilot:"))
    ] + ["phase:full-corpus", "profile:pilot3"]
    names = {Path(e["pilot_path"]).stem: e["dataset"] for e in manifest["datasets"]}
    for entry in manifest["datasets"]:
        path = entry["working_path"]
        context["source_sha256"][path] = inputs[entry["dataset"]].dataset_sha256
    for task in spec.tasks:
        task.model.config.max_connections = None
        task.model.config.adaptive_connections = adaptive.model_copy(deep=True)
        data = inputs[names[Path(task.args["dataset"]).stem]]
        task.args["dataset"] = data.dataset
        metadata = task_metadata(data)
        task.metadata.update(deepcopy(metadata))
        task.metadata.update(phase="full-corpus", selected_case_count=len(data.records))
        task.tags = (
            task_tags(data, metadata)
            + [
                t
                for t in task.tags
                if t.startswith(
                    (
                        "model:",
                        "model_family:",
                        "provider:",
                        "service_tier:",
                        "generation_group:",
                        "reasoning:",
                        "reasoning_effort:",
                    )
                )
            ]
            + ["phase:full-corpus", "profile:pilot3"]
        )
    return spec
