"""Prepare a separate load selection without changing the coverage pilot."""

import json
from collections import defaultdict
from pathlib import Path

from llm_transitivity.datasets.pilot import MANIFEST, verify
from llm_transitivity.domain.selection import stratum
from llm_transitivity.evidence.serialization import digest, json_bytes, record_digest

LOAD_DIRECTORY = Path("datasets/load")


def derive_load_pool(root: Path) -> tuple[list, dict]:
    manifest = verify(root)
    from llm_transitivity.datasets.correction import MANIFEST as CORRECTIONS

    changes = (
        json.loads((root / CORRECTIONS).read_text())["cases"]
        if (root / CORRECTIONS).exists()
        else []
    )
    original_text = {
        (r["dataset"], r["original_row"]): r["original_text"] for r in changes
    }

    def selection_hash(pair, dataset):
        row, origin = pair
        before = row.copy()
        before[2] = original_text.get((dataset, origin["original_row"]), row[2])
        return record_digest(before)

    records, selected = [], []
    for entry in manifest["datasets"]:
        source = json.loads((root / entry["pilot_path"]).read_text())
        groups = defaultdict(list)
        for row, origin in zip(source, entry["selected_rows"], strict=True):
            groups[stratum(row)].append((row, origin))
        choices = [
            choice
            for group in groups.values()
            for choice in sorted(
                group,
                key=lambda pair: (
                    selection_hash(pair, entry["dataset"]),
                    pair[1]["original_row"],
                ),
            )[:2]
        ]
        for row, origin in sorted(choices, key=lambda pair: pair[1]["original_row"]):
            records.append(row)
            selected.append(
                {
                    **origin,
                    "dataset": entry["dataset"],
                    "pilot_path": entry["pilot_path"],
                    "sample_uid": f"{entry['dataset']}:{origin['original_row']}:{origin['sentence_sha256'][:16]}",
                    "stratum_id": record_digest(list(stratum(row)))[:16],
                }
            )
    if len(records) != 216 or len({r["sample_uid"] for r in selected}) != 216:
        raise ValueError("Expected 216 unique load cases")
    return records, {
        "version": 1,
        "selection": "two lowest record SHA-256 values per pilot stratum; source row breaks ties; retain dataset and source order",
        "case_count": 216,
        "strata": 108,
        "cases_per_stratum": 2,
        "pilot_manifest_sha256": digest((root / MANIFEST).read_bytes()),
        "cases_sha256": digest(json_bytes(records)),
        "selected_rows": selected,
    }


def prepare_load_pool(root: Path) -> dict:
    records, manifest = derive_load_pool(root)
    directory = root / LOAD_DIRECTORY
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "cases_216.json").write_bytes(json_bytes(records))
    (directory / "manifest.json").write_bytes(json_bytes(manifest))
    return manifest


def verify_load_pool(root: Path) -> dict:
    records, manifest = derive_load_pool(root)
    for filename, value in [("cases_216.json", records), ("manifest.json", manifest)]:
        if (root / LOAD_DIRECTORY / filename).read_bytes() != json_bytes(value):
            raise ValueError(f"Load selection differs from verified source: {filename}")
    return manifest
