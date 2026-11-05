"""Adapt the project datasets to Inspect AI without changing source records."""

import json
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import ChatMessageSystem, ChatMessageUser
from inspect_ai.solver import generate

from dataset_validation import load_dataset
from experiment_metadata import EXPERIMENT_ID, SCORING_VERSION
from inspect_scoring import source_label_match
from openrouter_telemetry import capture_openrouter_http, collect_openrouter_details
from prepare_pilot import digest, record_digest, stratum, verified_pilot

PROJECT_ROOT = Path(__file__).resolve().parent


@task
def hs_zero_shot(dataset: str = "HS") -> Task:
    """Measure agreement with source labels while preserving source records."""
    path = PROJECT_ROOT / "datasets" / f"{dataset}.json"
    provenance = None
    if dataset.startswith("pilot/"):
        rows, provenance = verified_pilot(PROJECT_ROOT, dataset.removeprefix("pilot/"))
        path = PROJECT_ROOT / provenance["pilot_path"]
    else:
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
    if provenance is not None:
        originals = json.loads(
            (PROJECT_ROOT / provenance["original_path"]).read_text(encoding="utf-8")
        )
        for sample, origin in zip(samples, provenance["selected_rows"]):
            sample.id = origin["original_row"]
            sample.metadata.update(
                {
                    "working_dataset": provenance["dataset"],
                    "original_path": provenance["original_path"],
                    "original_row": origin["original_row"],
                    "sentence_sha256": origin["sentence_sha256"],
                    "original_record_sha256": origin["original_record_sha256"],
                    "working_record_sha256": origin["working_record_sha256"],
                    "original_labels": {
                        "validity": originals[origin["original_row"] - 1][6],
                        "canonical_form": originals[origin["original_row"] - 1][7],
                    },
                }
            )
    family = (provenance["dataset"] if provenance else path.stem).split("_")[0]
    for sample, row in zip(samples, rows):
        md = sample.metadata
        md.update(
            {
                "experiment_id": EXPERIMENT_ID,
                "dataset_family": family,
                "protocol": "zeroShot",
                "expected_answer": sample.target,
                "label_basis": "source labels; logical validity not audited",
                "logical_validity_audited": False,
                "stratum_id": record_digest(list(stratum(row)))[:16],
                "sample_uid": f"{md.get('working_dataset', dataset)}:{sample.id}:{digest(row[2].encode('utf-8'))[:16]}",
                "tags": [
                    f"family:{family}",
                    f"frequency:{row[3]}",
                    f"tense:{row[4]}",
                    f"validity:{row[6]}",
                    f"form:{row[7]}",
                    f"connectors:{row[5]}",
                ],
            }
        )
    pilot_name = path.stem
    metadata = {
        "experiment_id": EXPERIMENT_ID,
        "system_prompt": "zeroShot",
        "system_prompt_sha256": digest(system_path.read_bytes()),
        "scoring": "source-label agreement",
        "scoring_version": SCORING_VERSION,
        "dataset_name": pilot_name,
        "dataset_family": family,
        "dataset_path": str(path.relative_to(PROJECT_ROOT)),
        "dataset_sha256": digest(path.read_bytes()),
        "sample_count": len(rows),
        "frequency": sorted({row[3] for row in rows}),
        "verbal_time": sorted({row[4] for row in rows}),
        "connectors": sorted({row[5] for row in rows}),
        "source_validity": sorted({row[6] for row in rows}),
        "canonical_form": sorted({row[7] for row in rows}),
    }
    if provenance:
        metadata["provenance"] = {
            key: provenance[key]
            for key in [
                "dataset",
                "original_path",
                "original_sha256",
                "working_path",
                "working_sha256",
                "case_count",
                "pilot_sha256",
            ]
        }
    return Task(
        name=f"zeroShot_{pilot_name}",
        display_name=f"{pilot_name} | zeroShot",
        dataset=MemoryDataset(samples, name=dataset, location=str(path)),
        solver=[capture_openrouter_http(), generate(), collect_openrouter_details()],
        scorer=source_label_match(),
        score_on_error=False,
        tags=[
            "project:llm-transitivity",
            "protocol:zeroShot",
            f"dataset:{pilot_name}",
            f"family:{family}",
        ]
        + [f"frequency:{value}" for value in metadata["frequency"]]
        + [f"tense:{value}" for value in metadata["verbal_time"]]
        + [f"connectors:{value}" for value in metadata["connectors"]],
        metadata=metadata,
    )
