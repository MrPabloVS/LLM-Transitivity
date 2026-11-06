"""Compose Inspect tasks from validated datasets and framework adapters."""

from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset

from llm_transitivity.datasets.inputs import load_input
from llm_transitivity.inspect.samples import build_samples, task_metadata, task_tags
from llm_transitivity.inspect.scoring import source_label_match
from llm_transitivity.inspect.telemetry import (
    collect_openrouter_details,
    generate_with_capture,
)


@task
def hs_zero_shot(dataset: str = "HS", *, root: str) -> Task:
    """Measure agreement with source labels while preserving source records."""
    data = load_input(Path(root), dataset)
    samples = build_samples(data)
    metadata = task_metadata(data)
    pilot_name, path = data.path.stem, data.path
    return Task(
        name=f"zeroShot_{pilot_name}",
        display_name=f"{pilot_name} | zeroShot",
        dataset=MemoryDataset(samples, name=dataset, location=str(path)),
        solver=[generate_with_capture(), collect_openrouter_details()],
        scorer=source_label_match(),
        score_on_error=False,
        tags=task_tags(data, metadata),
        metadata=metadata,
    )


@task
def load_zero_shot(*, root: str) -> Task:
    """Pool verified source cases while retaining each case's provenance."""
    from llm_transitivity.datasets.load_pool import verify_load_pool

    directory = Path(root)
    manifest = verify_load_pool(directory)
    names = list(dict.fromkeys(row["pilot_path"] for row in manifest["selected_rows"]))
    # Read every source before creating any samples or solvers.
    inputs = [load_input(directory, "pilot/" + Path(name).stem) for name in names]
    samples = {
        sample.metadata["sample_uid"]: sample
        for data in inputs
        for sample in build_samples(data)
    }
    pooled = []
    for origin in manifest["selected_rows"]:
        sample = samples[origin["sample_uid"]]
        sample.id = origin["sample_uid"]
        sample.metadata["phase"] = "load-validation"
        pooled.append(sample)
    metadata = {
        "dataset_name": "load_216",
        "sample_count": 216,
        "source_datasets": [data.provenance["dataset"] for data in inputs],
        "system_prompt_sha256": inputs[0].system_sha256,
        "scoring_version": task_metadata(inputs[0])["scoring_version"],
        "load_manifest": "datasets/load/manifest.json",
    }
    return Task(
        name="zeroShot_load_216",
        dataset=MemoryDataset(pooled, name="load_216"),
        solver=[generate_with_capture(), collect_openrouter_details()],
        scorer=source_label_match(),
        score_on_error=False,
        tags=["phase:load-validation", "protocol:zeroShot", "family:HS", "family:mHS"],
        metadata=metadata,
    )
