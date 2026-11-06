"""Build Inspect samples and task labels from already validated input values."""

from inspect_ai.dataset import Sample
from inspect_ai.model import ChatMessageSystem, ChatMessageUser

from llm_transitivity.datasets.inputs import DatasetInput
from llm_transitivity.domain.cases import BenchmarkCase
from llm_transitivity.domain.selection import stratum
from llm_transitivity.evidence.metadata import EXPERIMENT_ID, SCORING_VERSION
from llm_transitivity.evidence.serialization import digest, record_digest


def build_samples(data: DatasetInput) -> list[Sample]:
    samples = []
    for number, (case, row) in enumerate(zip(data.cases, data.records), 1):
        sample_id = number
        expected = "yes" if case.source_validity == "valid" else "no"
        metadata = {
            "source_dataset": data.dataset,
            "source_row": number,
            "source_id": case.source_id,
            "case_type": case.case_type,
            "frequency": case.frequency,
            "verbal_time": case.verbal_time,
            "connectors": case.connectors,
            "source_validity": case.source_validity,
            "canonical_form": case.canonical_form,
        }
        if data.provenance is not None:
            origin = data.provenance["selected_rows"][number - 1]
            sample_id = origin["original_row"]
            original = BenchmarkCase.from_record(data.originals[sample_id - 1])
            metadata.update(
                {
                    "working_dataset": data.provenance["dataset"],
                    "original_path": data.provenance["original_path"],
                    "original_row": sample_id,
                    "sentence_sha256": origin["sentence_sha256"],
                    "original_record_sha256": origin["original_record_sha256"],
                    "working_record_sha256": origin["working_record_sha256"],
                    "original_labels": {
                        "validity": original.source_validity,
                        "canonical_form": original.canonical_form,
                    },
                }
            )
        if (
            data.originals is not None
            and case.prompt != data.originals[sample_id - 1][2]
        ):
            from llm_transitivity.datasets.correction import CORRECTION_ID

            metadata.update(
                correction_id=CORRECTION_ID,
                source_identity=f"{metadata['working_dataset']}:{sample_id}",
                original_sample_uid=f"{metadata['working_dataset']}:{sample_id}:{digest(data.originals[sample_id - 1][2].encode())[:16]}",
            )
        metadata.update(
            {
                "experiment_id": EXPERIMENT_ID,
                "dataset_family": data.family,
                "protocol": "zeroShot",
                "expected_answer": expected,
                "label_basis": "source labels; logical validity not audited",
                "logical_validity_audited": False,
                "stratum_id": record_digest(list(stratum(row)))[:16],
                "sample_uid": f"{metadata.get('working_dataset', data.dataset)}:{sample_id}:{digest(case.prompt.encode('utf-8'))[:16]}",
                "tags": [
                    f"family:{data.family}",
                    f"frequency:{case.frequency}",
                    f"tense:{case.verbal_time}",
                    f"validity:{case.source_validity}",
                    f"form:{case.canonical_form}",
                    f"connectors:{case.connectors}",
                ],
            }
        )
        samples.append(
            Sample(
                id=sample_id,
                target=expected,
                input=[
                    ChatMessageSystem(content=data.system_message),
                    ChatMessageUser(content=case.prompt),
                ],
                metadata=metadata,
            )
        )
    return samples


def task_metadata(data: DatasetInput) -> dict:
    cases, rows = data.cases, data.records
    provenance, family = data.provenance, data.family
    pilot_name = data.path.stem
    metadata = {
        "experiment_id": EXPERIMENT_ID,
        "system_prompt": "zeroShot",
        "system_prompt_sha256": data.system_sha256,
        "scoring": "source-label agreement",
        "scoring_version": SCORING_VERSION,
        "dataset_name": pilot_name,
        "dataset_family": family,
        "dataset_path": data.relative_path,
        "dataset_sha256": data.dataset_sha256,
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
                "original_revision",
            ]
            if key in provenance
        }
    return metadata


def task_tags(data: DatasetInput, metadata: dict) -> list[str]:
    pilot_name, family = data.path.stem, data.family
    return (
        [
            "project:llm-transitivity",
            "protocol:zeroShot",
            f"dataset:{pilot_name}",
            f"family:{family}",
        ]
        + [f"frequency:{value}" for value in metadata["frequency"]]
        + [f"tense:{value}" for value in metadata["verbal_time"]]
        + [f"connectors:{value}" for value in metadata["connectors"]]
    )
