"""Load and validate all task inputs before constructing Inspect objects."""

import json
from dataclasses import dataclass
from pathlib import Path

from llm_transitivity.datasets.corpus import dataset_names, verified_full_source
from llm_transitivity.datasets.pilot import verified_pilot_source
from llm_transitivity.datasets.validation import load_dataset
from llm_transitivity.domain.cases import BenchmarkCase
from llm_transitivity.evidence.serialization import digest


@dataclass(frozen=True)
class DatasetInput:
    """Keep task records, checked originals, and prompt evidence together."""

    dataset: str
    path: Path
    relative_path: str
    records: list[list]
    cases: list[BenchmarkCase]
    originals: list[list] | None
    provenance: dict | None
    system_message: str
    system_sha256: str
    dataset_sha256: str

    @property
    def family(self) -> str:
        name = self.provenance["dataset"] if self.provenance else self.path.stem
        return name.split("_")[0]


def load_input(root: Path, dataset: str) -> DatasetInput:
    path = root / "datasets" / f"{dataset}.json"
    provenance = None
    originals = None
    if dataset.startswith("pilot/"):
        source, provenance = verified_pilot_source(root, dataset.removeprefix("pilot/"))
        records = [
            source.records[row["original_row"] - 1]
            for row in provenance["selected_rows"]
        ]
        originals = source.originals
        path = root / provenance["pilot_path"]
    elif dataset in dataset_names():
        source, provenance = verified_full_source(root, dataset)
        records, originals = source.records, source.originals
        path = root / provenance["working_path"]
    else:
        records = load_dataset(path)
    cases = [BenchmarkCase.from_record(row) for row in records]
    for number, case in enumerate(cases, start=1):
        if case.source_validity not in {"valid", "invalid"}:
            raise ValueError(
                f"{path}: case {number}: unknown source validity {case.source_validity!r}"
            )
    system_path = root / "prompts/systemPrompts/zeroShot.json"
    system = json.loads(system_path.read_text(encoding="utf-8"))
    if (
        not isinstance(system, list)
        or len(system) != 1
        or not isinstance(system[0], str)
        or not system[0].strip()
    ):
        raise ValueError(f"{system_path}: expected one non-empty system message")
    return DatasetInput(
        dataset=dataset,
        path=path,
        relative_path=str(path.relative_to(root)),
        records=records,
        cases=cases,
        originals=originals,
        provenance=provenance,
        system_message=system[0],
        system_sha256=digest(system_path.read_bytes()),
        dataset_sha256=digest(path.read_bytes()),
    )
