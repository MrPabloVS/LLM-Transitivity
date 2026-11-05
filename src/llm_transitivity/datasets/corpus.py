"""Verify complete datasets against the preserved main revision."""

import json
from pathlib import Path

from llm_transitivity.datasets.pilot import (
    dataset_names,
    describe_dataset,
    describe_system,
)

MAIN_REVISION = "7ccba3fb581a14f0c1dab5ceba5e1dac341d49ef"


def verified_full_dataset(root: Path, name: str) -> tuple[list, dict]:
    """Return all verified records with original row provenance."""
    if name not in dataset_names():
        raise ValueError(f"Unknown full dataset: {name}")
    entry, payload = describe_dataset(root, MAIN_REVISION, name, 500)
    describe_system(root, MAIN_REVISION)
    # Selecting every source row retains source order and records every hash.
    entry.pop("pilot_path")
    entry.pop("pilot_sha256")
    entry["original_revision"] = MAIN_REVISION
    return json.loads(payload), entry
