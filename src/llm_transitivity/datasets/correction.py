"""Authorize one exact text correction against the immutable source corpus."""

import json
import re
from pathlib import Path

from llm_transitivity.evidence.serialization import digest, record_digest

CORRECTION_ID = "eate-to-ate-v1"
SOURCE_RUN = "results/full/2026-11-06_01-23-40-040fd7b7"
MANIFEST = Path(f"datasets/corrections/{CORRECTION_ID}.json")
DATASETS = {"HS_HF_PA_2000": 204, "mHS_HF_PA_4000": 408}


def changes(name: str, originals: list[list]) -> list[dict]:
    """Describe only whole-word replacements in the two authorized datasets."""
    if name not in DATASETS:
        return []
    rows = []
    for number, record in enumerate(originals, 1):
        before = record[2]
        after, count = re.subn(r"\beate\b", "ate", before)
        if not count:
            continue
        corrected = record.copy()
        corrected[2] = after
        old_hash, new_hash = digest(before.encode()), digest(after.encode())
        rows.append(
            {
                "dataset": name,
                "original_row": number,
                "source_identity": f"{name}:{number}",
                "original_uid": f"{name}:{number}:{old_hash[:16]}",
                "corrected_uid": f"{name}:{number}:{new_hash[:16]}",
                "original_text": before,
                "corrected_text": after,
                "original_sentence_sha256": old_hash,
                "sentence_sha256": new_hash,
                "original_record_sha256": record_digest(record),
                "working_record_sha256": record_digest(corrected),
                "replacements": count,
                "reason": "Correct the past tense of eat: eate to ate",
            }
        )
    if (
        len(rows) != DATASETS[name]
        or sum(r["replacements"] for r in rows) != 2 * DATASETS[name]
    ):
        raise ValueError("Correction source counts differ: " + name)
    return rows


def approved_changes(root: Path, name: str, originals: list[list]) -> dict[int, dict]:
    path = root / MANIFEST
    if not path.exists():
        return {}
    manifest = json.loads(path.read_text())
    if manifest.get("id") != CORRECTION_ID or manifest.get("source_run") != SOURCE_RUN:
        raise ValueError("Unknown corpus correction")
    expected = changes(name, originals)
    actual = [r for r in manifest["cases"] if r["dataset"] == name]
    if actual != expected or {r["dataset"] for r in manifest["cases"]} != set(DATASETS):
        raise ValueError(
            "Correction manifest differs from authorized source transformation"
        )
    if (
        len(manifest["cases"]) != 612
        or sum(r["replacements"] for r in manifest["cases"]) != 1224
    ):
        raise ValueError("Correction manifest counts differ")
    return {r["original_row"]: r for r in expected}


def selection_records(dataset) -> list[list]:
    """Retain the original selection ranking, including label normalization."""
    rows = []
    for original, working in zip(dataset.originals, dataset.records, strict=True):
        row = working.copy()
        row[2] = original[2]
        rows.append(row)
    return rows
