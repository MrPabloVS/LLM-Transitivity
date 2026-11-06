"""Keep pilot records and their source provenance intact in Inspect."""

import json
import re
from collections import Counter
from pathlib import Path

import pytest

from llm_transitivity.datasets import pilot
from llm_transitivity.evidence import serialization
from llm_transitivity.inspect import tasks as inspect_tasks
from tests.paths import PROJECT_ROOT


@pytest.mark.parametrize("name", pilot.dataset_names())
def test_every_pilot_sentence_and_metadata_reaches_inspect_unchanged(name):
    rows, entry = pilot.verified_pilot(PROJECT_ROOT, name)
    full = json.loads((PROJECT_ROOT / entry["working_path"]).read_text())
    original = json.loads((PROJECT_ROOT / entry["original_path"]).read_text())
    pilot_name = Path(entry["pilot_path"]).stem
    evaluation = inspect_tasks.hs_zero_shot(
        f"pilot/{pilot_name}", root=str(PROJECT_ROOT)
    )
    samples = list(evaluation.dataset)
    assert Path(evaluation.dataset.location).is_file()
    assert int(pilot_name.rsplit("_", 1)[1]) == len(rows)
    system = json.loads(
        (PROJECT_ROOT / "prompts/systemPrompts/zeroShot.json").read_text()
    )[0]
    assert len(rows) == len(samples) == len(entry["strata"]) * 5
    counts = Counter(pilot.stratum(row) for row in rows)
    assert set(counts.values()) == {5}
    assert len(counts) == len(entry["strata"])
    for row, sample, origin in zip(rows, samples, entry["selected_rows"]):
        index = origin["original_row"] - 1
        assert row == full[index]
        expected_text = original[index][2]
        if name in {"HS_HF_PA_2000", "mHS_HF_PA_4000"}:
            expected_text = re.sub(r"\beate\b", "ate", expected_text)
        assert sample.input[1].content == expected_text == row[2]
        assert sample.input[0].content == system
        assert sample.metadata["source_id"] == original[index][1]
        assert sample.metadata["original_row"] == sample.id == index + 1
        assert sample.metadata["frequency"] == row[3]
        assert sample.metadata["verbal_time"] == row[4]
        assert sample.metadata["connectors"] == row[5]
        assert sample.metadata["source_validity"] == row[6]
        assert sample.metadata["canonical_form"] == row[7]


@pytest.mark.parametrize(
    "change",
    [
        "sentence",
        "label",
        "identifier",
        "order",
        "original",
        "pilot",
        "manifest",
        "system",
    ],
)
def test_corruption_is_rejected_before_inspect_builds_task(
    isolated_source, monkeypatch, change
):
    root, name, entry = isolated_source
    path = root / entry["working_path"]
    rows = json.loads(path.read_text())
    if change == "sentence":
        rows[0][2] += " "
    elif change == "label":
        rows[0][6] = "invalid" if rows[0][6] == "valid" else "valid"
    elif change == "identifier":
        rows[0][1] = "changed"
    elif change == "order":
        rows[0], rows[1] = rows[1], rows[0]
    elif change == "original":
        path = root / entry["original_path"]
        path.write_bytes(path.read_bytes() + b" ")
    elif change == "pilot":
        path = root / entry["pilot_path"]
        data = json.loads(path.read_text())
        data[0][2] += " "
        path.write_bytes(serialization.json_bytes(data))
    elif change == "manifest":
        path = root / pilot.MANIFEST
        data = json.loads(path.read_text())
        next(e for e in data["datasets"] if e["dataset"] == name)["selected_rows"][0][
            "original_row"
        ] += 1
        path.write_bytes(serialization.json_bytes(data))
    else:
        (root / "prompts/systemPrompts/zeroShot.json").write_text('["changed"]')
    if change in {"sentence", "label", "identifier", "order"}:
        path.write_bytes(serialization.json_bytes(rows))
    with pytest.raises(ValueError):
        inspect_tasks.hs_zero_shot(f"pilot/{name}", root=str(root))
