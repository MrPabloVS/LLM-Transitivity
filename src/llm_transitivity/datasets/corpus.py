"""Verify source preservation independently of pilot selection and Inspect."""

import json
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from itertools import product
from pathlib import Path

from llm_transitivity.datasets.validation import load_dataset
from llm_transitivity.domain.selection import stratum
from llm_transitivity.evidence.serialization import digest, record_digest

MAIN_REVISION = "7ccba3fb581a14f0c1dab5ceba5e1dac341d49ef"
TRANSLATED = {"HS_LF_PR_2000", "mHS_LF_PR_4000"}


@dataclass(frozen=True)
class VerifiedDataset:
    """Retain checked source records and describe their original row provenance."""

    name: str
    original_path: str
    working_path: str
    original_sha256: str
    working_sha256: str
    originals: list[list]
    records: list[list]
    groups: dict[tuple, list[int]]

    def provenance(self, numbers: list[int], selected_per_stratum: int) -> dict:
        return {
            "dataset": self.name,
            "original_path": self.original_path,
            "original_sha256": self.original_sha256,
            "working_path": self.working_path,
            "working_sha256": self.working_sha256,
            "case_count": len(self.records),
            "strata": [
                {
                    "values": list(key),
                    "population": len(rows),
                    "selected": selected_per_stratum,
                }
                for key, rows in sorted(self.groups.items())
            ],
            "selected_rows": [
                {
                    "original_row": number,
                    "sentence_sha256": digest(
                        self.records[number - 1][2].encode("utf-8")
                    ),
                    "original_record_sha256": record_digest(self.originals[number - 1]),
                    "working_record_sha256": record_digest(self.records[number - 1]),
                }
                for number in numbers
            ],
        }


def dataset_names() -> list[str]:
    return [
        f"{kind}_{frequency}_{tense}_{size}"
        for kind, size in [("HS", 2000), ("mHS", 4000)]
        for frequency, tense in product(("HF", "LF", "NS"), ("FU", "PA", "PR"))
    ]


def git_bytes(root: Path, revision: str, path: str) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(root), "show", f"{revision}:{path}"]
    )


def verify_dataset(root: Path, revision: str, name: str) -> VerifiedDataset:
    """Check original bytes and every working field before any sample selection."""
    family, frequency, tense, size = name.split("_")
    original_path = (
        f"prompts/userPrompts/{family}_{frequency}_{tense}_500_complete.json"
    )
    working_path = f"datasets/{name}.json"
    baseline = git_bytes(root, revision, original_path)
    if (root / original_path).read_bytes() != baseline:
        raise ValueError(f"{original_path}: original differs from Git baseline")
    original = json.loads(baseline)
    working = load_dataset(root / working_path)
    if len(original) != len(working) or len(working) != int(size):
        raise ValueError(
            f"{working_path}: case count differs from baseline or filename"
        )
    from llm_transitivity.datasets.correction import approved_changes

    corrections = approved_changes(root, name, original)
    groups = defaultdict(list)
    for number, (before, after) in enumerate(zip(original, working), start=1):
        expected = before.copy()
        if name in TRANSLATED:
            expected[6] = {"valido": "valid"}.get(before[6], before[6])
            expected[7] = {"canonico": "canonic"}.get(before[7], before[7])
        if number in corrections:
            expected[2] = corrections[number]["corrected_text"]
        if expected[2] != after[2]:
            raise ValueError(
                f"{working_path}: case {number}: sentence differs from original"
            )
        if record_digest(after) != record_digest(expected):
            raise ValueError(
                f"{working_path}: case {number}: unexpected metadata change"
            )
        if after[0] != "HS" or after[3:5] != [frequency, tense]:
            raise ValueError(
                f"{working_path}: case {number}: filename and metadata disagree"
            )
        if after[6] not in {"valid", "invalid"} or after[7] not in {
            "canonic",
            "non-canonic",
        }:
            raise ValueError(f"{working_path}: case {number}: unknown label")
        groups[stratum(after)].append(number)
    expected_connectors = (
        ["if then / therefore"]
        if family == "HS"
        else [
            "assuming that we can infer / thus",
            "from the inference (therefore) / does the inference follow",
        ]
    )
    expected_groups = {
        ("HS", frequency, tense, connector, validity, form)
        for connector, validity, form in product(
            expected_connectors, ("valid", "invalid"), ("canonic", "non-canonic")
        )
    }
    if set(groups) != expected_groups or any(
        len(numbers) != 500 for numbers in groups.values()
    ):
        raise ValueError(
            f"{working_path}: expected all source strata with 500 cases each"
        )
    return VerifiedDataset(
        name=name,
        original_path=original_path,
        working_path=working_path,
        original_sha256=digest(baseline),
        working_sha256=digest((root / working_path).read_bytes()),
        originals=original,
        records=working,
        groups=dict(groups),
    )


def describe_system(root: Path, revision: str) -> dict:
    path = "prompts/systemPrompts/zeroShot.json"
    baseline = git_bytes(root, revision, path)
    if (root / path).read_bytes() != baseline:
        raise ValueError(f"{path}: system prompt differs from Git baseline")
    return {"path": path, "sha256": digest(baseline)}


def verified_full_source(root: Path, name: str) -> tuple[VerifiedDataset, dict]:
    """Retain checked originals for consumers that also need source labels."""
    if name not in dataset_names():
        raise ValueError(f"Unknown full dataset: {name}")
    dataset = verify_dataset(root, MAIN_REVISION, name)
    describe_system(root, MAIN_REVISION)
    entry = dataset.provenance(list(range(1, len(dataset.records) + 1)), 500)
    entry["original_revision"] = MAIN_REVISION
    return dataset, entry


def verified_full_dataset(root: Path, name: str) -> tuple[list, dict]:
    """Return all verified records with original row provenance, without sampling."""
    dataset, entry = verified_full_source(root, name)
    return dataset.records, entry
