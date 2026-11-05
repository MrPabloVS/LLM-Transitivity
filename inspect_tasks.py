"""Adapt the project datasets to Inspect AI without changing source records."""

import json
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import ChatMessageSystem, ChatMessageUser
from inspect_ai.solver import generate

from dataset_validation import load_dataset
from inspect_scoring import source_label_match

PROJECT_ROOT = Path(__file__).resolve().parent


@task
def hs_zero_shot(dataset: str = "HS") -> Task:
    """Measure agreement with source labels while preserving source records."""
    path = PROJECT_ROOT / "datasets" / f"{dataset}.json"
    rows = load_dataset(path)
    for number, row in enumerate(rows, start=1):
        if row[6] not in {"valid", "invalid"}:
            raise ValueError(
                f"{path}: case {number}: unknown source validity {row[6]!r}"
            )
    system_path = PROJECT_ROOT / "prompts" / "systemPrompts" / "zeroShot.json"
    system = json.loads(system_path.read_text(encoding="utf-8"))
    if (
        not isinstance(system, list)
        or len(system) != 1
        or not isinstance(system[0], str)
        or not system[0].strip()
    ):
        raise ValueError(f"{system_path}: expected one non-empty system message")

    samples = [
        Sample(
            id=number,
            target="yes" if row[6] == "valid" else "no",
            input=[
                ChatMessageSystem(content=system[0]),
                ChatMessageUser(content=row[2]),
            ],
            metadata={
                "source_dataset": dataset,
                "source_row": number,
                "source_id": row[1],
                "case_type": row[0],
                "frequency": row[3],
                "verbal_time": row[4],
                "connectors": row[5],
                "source_validity": row[6],
                "canonical_form": row[7],
            },
        )
        for number, row in enumerate(rows, start=1)
    ]
    return Task(
        dataset=MemoryDataset(samples, name=dataset, location=str(path)),
        solver=generate(),
        scorer=source_label_match(),
        score_on_error=False,
        metadata={"system_prompt": "zeroShot", "scoring": "source-label agreement"},
    )
