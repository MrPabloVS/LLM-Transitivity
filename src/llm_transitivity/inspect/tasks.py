"""Adapt the project datasets to Inspect AI without changing source records."""

import json
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import ChatMessageSystem, ChatMessageUser

from llm_transitivity.datasets.pilot import verified_pilot
from llm_transitivity.datasets.validation import load_dataset
from llm_transitivity.domain.cases import BenchmarkCase
from llm_transitivity.domain.selection import stratum
from llm_transitivity.evidence.metadata import EXPERIMENT_ID, SCORING_VERSION
from llm_transitivity.evidence.serialization import digest, record_digest
from llm_transitivity.inspect.scoring import source_label_match
from llm_transitivity.inspect.telemetry import (
    collect_openrouter_details,
    generate_with_capture,
)


@task
def hs_zero_shot(dataset: str = "HS", *, root: str) -> Task:
    """Measure agreement with source labels while preserving source records."""
    project_root = Path(root)
    path = project_root / "datasets" / f"{dataset}.json"
    provenance = None
    if dataset.startswith("pilot/"):
        rows, provenance = verified_pilot(project_root, dataset.removeprefix("pilot/"))
        path = project_root / provenance["pilot_path"]
    else:
        rows = load_dataset(path)
    cases = [BenchmarkCase.from_record(row) for row in rows]
    for number, case in enumerate(cases, start=1):
        if case.source_validity not in {"valid", "invalid"}:
            raise ValueError(
                f"{path}: case {number}: unknown source validity {case.source_validity!r}"
            )
    system_path = project_root / "prompts" / "systemPrompts" / "zeroShot.json"
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
            target="yes" if case.source_validity == "valid" else "no",
            input=[
                ChatMessageSystem(content=system[0]),
                ChatMessageUser(content=case.prompt),
            ],
            metadata={
                "source_dataset": dataset,
                "source_row": number,
                "source_id": case.source_id,
                "case_type": case.case_type,
                "frequency": case.frequency,
                "verbal_time": case.verbal_time,
                "connectors": case.connectors,
                "source_validity": case.source_validity,
                "canonical_form": case.canonical_form,
            },
        )
        for number, case in enumerate(cases, start=1)
    ]
    if provenance is not None:
        originals = json.loads(
            (project_root / provenance["original_path"]).read_text(encoding="utf-8")
        )
        for sample, origin in zip(samples, provenance["selected_rows"]):
            original = BenchmarkCase.from_record(originals[origin["original_row"] - 1])
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
                        "validity": original.source_validity,
                        "canonical_form": original.canonical_form,
                    },
                }
            )
    family = (provenance["dataset"] if provenance else path.stem).split("_")[0]
    for sample, case, row in zip(samples, cases, rows):
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
                "sample_uid": f"{md.get('working_dataset', dataset)}:{sample.id}:{digest(case.prompt.encode('utf-8'))[:16]}",
                "tags": [
                    f"family:{family}",
                    f"frequency:{case.frequency}",
                    f"tense:{case.verbal_time}",
                    f"validity:{case.source_validity}",
                    f"form:{case.canonical_form}",
                    f"connectors:{case.connectors}",
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
        "dataset_path": str(path.relative_to(project_root)),
        "dataset_sha256": digest(path.read_bytes()),
        "sample_count": len(rows),
        "frequency": sorted({case.frequency for case in cases}),
        "verbal_time": sorted({case.verbal_time for case in cases}),
        "connectors": sorted({case.connectors for case in cases}),
        "source_validity": sorted({case.source_validity for case in cases}),
        "canonical_form": sorted({case.canonical_form for case in cases}),
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
        solver=[generate_with_capture(), collect_openrouter_details()],
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
