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
