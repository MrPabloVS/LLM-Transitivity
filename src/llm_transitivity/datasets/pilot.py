"""Build and verify a pilot against originals anchored to a Git revision."""

import json
import subprocess
from collections import defaultdict
from itertools import product
from pathlib import Path

from llm_transitivity.datasets.validation import load_dataset
from llm_transitivity.domain.selection import select_rows, stratum
from llm_transitivity.evidence.serialization import digest, json_bytes, record_digest

MANIFEST = Path("datasets/pilot/manifest.json")
DIMENSIONS = [
    "case_type",
    "frequency",
    "verbal_time",
    "connectors",
    "source_validity",
    "canonical_form",
]
TRANSLATED = {"HS_LF_PR_2000", "mHS_LF_PR_4000"}


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


def describe_dataset(
    root: Path, revision: str, name: str, count: int
) -> tuple[dict, bytes]:
    """Compare full records, then select rows by a stable SHA-256 ranking."""
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
    groups = defaultdict(list)
    for number, (before, after) in enumerate(zip(original, working), start=1):
        expected = before.copy()
        if name in TRANSLATED:
            expected[6] = {"valido": "valid"}.get(before[6], before[6])
            expected[7] = {"canonico": "canonic"}.get(before[7], before[7])
        if before[2] != after[2]:
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
    selected = select_rows(working, groups, count)
    pilot = [working[number - 1] for number in selected]
    payload = json_bytes(pilot)
    entry = {
        "dataset": name,
        "original_path": original_path,
        "original_sha256": digest(baseline),
        "working_path": working_path,
        "working_sha256": digest((root / working_path).read_bytes()),
        "case_count": len(working),
        "strata": [
            {"values": list(key), "population": len(numbers), "selected": count}
            for key, numbers in sorted(groups.items())
        ],
        "pilot_path": f"datasets/pilot/{name.rsplit('_', 1)[0]}_{len(pilot)}.json",
        "pilot_sha256": digest(payload),
        "selected_rows": [
            {
                "original_row": number,
                "sentence_sha256": digest(working[number - 1][2].encode("utf-8")),
                "original_record_sha256": record_digest(original[number - 1]),
                "working_record_sha256": record_digest(working[number - 1]),
            }
            for number in selected
        ],
    }
    return entry, payload


def describe_system(root: Path, revision: str) -> dict:
    path = "prompts/systemPrompts/zeroShot.json"
    baseline = git_bytes(root, revision, path)
    if (root / path).read_bytes() != baseline:
        raise ValueError(f"{path}: system prompt differs from Git baseline")
    return {"path": path, "sha256": digest(baseline)}


def construct(root: Path, revision: str, count: int) -> tuple[dict, dict]:
    if not 1 <= count <= 500:
        raise ValueError("Cases per stratum must be between 1 and 500")
    entries, payloads = [], {}
    for name in dataset_names():
        entry, payload = describe_dataset(root, revision, name, count)
        entries.append(entry)
        payloads[entry["pilot_path"]] = payload
    return {
        "version": 1,
        "baseline_revision": revision,
        "selection": "sha256 of compact UTF-8 JSON row, then source row; preserve source order",
        "cases_per_stratum": count,
        "stratum_dimensions": DIMENSIONS,
        "system_prompt": describe_system(root, revision),
        "datasets": entries,
    }, payloads


def inventory(manifest: dict) -> str:
    # Retain historical command text to verify the existing inventory bytes.
    entries = manifest["datasets"]
    strata = sum(len(e["strata"]) for e in entries)
    population = sum(e["case_count"] for e in entries)
    selected = sum(len(e["selected_rows"]) for e in entries)
    lines = [
        "# Dataset inventory and pilot coverage",
        "",
        (
            "Generated by `uv run --locked prepare_pilot.py prepare --per-stratum "
            f"{manifest['cases_per_stratum']}`. Verify with `uv run --locked prepare_pilot.py verify`."
        ),
        "",
        f"Original Git baseline: `{manifest['baseline_revision']}`.",
        "",
        (
            f"{len(entries)} datasets; {population:,} full cases; {strata} observed strata; "
            f"{selected} pilot cases; {selected * 6:,} planned responses across six models."
        ),
        "",
        (
            "A stratum combines case type, frequency, verbal time, connectors, source validity, "
            "and canonical form within a dataset. Every observed stratum has 500 source cases."
        ),
        "",
        (
            "This pilot covers all observed metadata combinations. It is not a statistical "
            "accuracy estimate or a proof of lexical coverage or logical validity."
        ),
        "",
        "| Dataset | Full cases | Strata | Pilot cases | Pilot file |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    lines += [
        f"| `{e['dataset']}` | {e['case_count']} | {len(e['strata'])} | {len(e['selected_rows'])} | `{Path(e['pilot_path']).name}` |"
        for e in entries
    ]
    lines += [
        "",
        "## Integrity",
        "",
        (
            "The manifest records file hashes, selected original row numbers, sentence hashes, "
            "record hashes, and every stratum. Selection ranks rows by SHA-256 and takes the "
            "specified count per stratum. Ties use source row numbers. Output keeps source order."
        ),
        "",
        (
            "Verification compares all full records with the Git baseline. Only `valido` to "
            "`valid` and `canonico` to `canonic` are allowed in the two LF/PR copies. "
            "It then reproduces every selection and checks the pilot bytes and system prompt. "
            "No Unicode, case, whitespace, or punctuation normalization is applied to sentences."
        ),
        "",
        (
            "The Git revision anchors the originals; the manifest detects accidental changes. "
            "It is not an independent signature against coordinated changes to code and evidence."
        ),
        "",
    ]
    return "\n".join(lines)


def prepare(root: Path, count: int) -> dict:
    revision = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    manifest, payloads = construct(root, revision, count)
    payloads[str(MANIFEST)] = json_bytes(manifest)
    payloads["docs/dataset_inventory.md"] = inventory(manifest).encode("utf-8")
    if any((root / path).exists() for path in payloads):
        raise ValueError(
            "Pilot artifacts already exist; verify them instead of replacing the baseline"
        )
    for path, payload in payloads.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    return manifest


def verify(root: Path) -> dict:
    saved = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    expected, payloads = construct(
        root, saved["baseline_revision"], saved["cases_per_stratum"]
    )
    if saved != expected:
        raise ValueError(
            "Manifest differs from the verified corpus and deterministic selection"
        )
    actual_paths = {
        str(p.relative_to(root)) for p in (root / "datasets/pilot").glob("*.json")
    }
    if actual_paths != set(payloads) | {str(MANIFEST)}:
        raise ValueError("Pilot file inventory differs from the manifest")
    for path, payload in payloads.items():
        if (root / path).read_bytes() != payload:
            raise ValueError(f"{path}: pilot differs from the verified selection")
    if (root / "docs/dataset_inventory.md").read_text(encoding="utf-8") != inventory(
        saved
    ):
        raise ValueError("Dataset inventory differs from the manifest")
    return saved


def verified_pilot(root: Path, name: str) -> tuple[list, dict]:
    """Check one task's source chain again when Inspect constructs its samples."""
    saved = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    entry = next(
        (
            e
            for e in saved["datasets"]
            if name in {e["dataset"], Path(e["pilot_path"]).stem}
        ),
        None,
    )
    if entry is None or entry["dataset"] not in dataset_names():
        raise ValueError(f"Unknown pilot dataset: {name}")
    name = entry["dataset"]
    actual, payload = describe_dataset(
        root, saved["baseline_revision"], name, saved["cases_per_stratum"]
    )
    if actual != entry or (root / entry["pilot_path"]).read_bytes() != payload:
        raise ValueError(f"{name}: pilot provenance check failed")
    if describe_system(root, saved["baseline_revision"]) != saved["system_prompt"]:
        raise ValueError("System prompt manifest check failed")
    return json.loads(payload), entry
