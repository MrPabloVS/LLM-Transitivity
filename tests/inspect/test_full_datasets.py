"""Preserve every complete source record through the Inspect adapter."""

import json
from unittest.mock import Mock

import pytest

from llm_transitivity.datasets import corpus, pilot
from llm_transitivity.datasets.corpus import MAIN_REVISION
from llm_transitivity.evidence.serialization import record_digest
from llm_transitivity.inspect import tasks
from tests.paths import PROJECT_ROOT


@pytest.mark.parametrize("name", pilot.dataset_names())
def test_all_full_records_reach_inspect_from_main(name):
    family, frequency, tense, count = name.split("_")
    source_path = f"prompts/userPrompts/{family}_{frequency}_{tense}_500_complete.json"
    original = json.loads(pilot.git_bytes(PROJECT_ROOT, MAIN_REVISION, source_path))
    evaluation = tasks.hs_zero_shot(name, root=str(PROJECT_ROOT))
    assert len(evaluation.dataset) == int(count) == len(original)
    assert evaluation.metadata["provenance"]["original_revision"] == MAIN_REVISION
    assert evaluation.dataset.location == str(PROJECT_ROOT / f"datasets/{name}.json")
    for number, (sample, before) in enumerate(zip(evaluation.dataset, original), 1):
        expected = before.copy()
        if name in pilot.TRANSLATED:
            expected[6] = {"valido": "valid"}.get(before[6], before[6])
            expected[7] = {"canonico": "canonic"}.get(before[7], before[7])
        md = sample.metadata
        restored = [
            md["case_type"],
            md["source_id"],
            sample.input[1].content,
            md["frequency"],
            md["verbal_time"],
            md["connectors"],
            md["source_validity"],
            md["canonical_form"],
        ]
        assert record_digest(restored) == record_digest(expected)
        assert sample.id == md["original_row"] == number
        assert sample.target == ("yes" if expected[6] == "valid" else "no")
        assert md["original_record_sha256"] == record_digest(before)
        assert md["dataset_family"] == family
        assert md["original_labels"] == {
            "validity": before[6],
            "canonical_form": before[7],
        }
        assert f"family:{family}" in md["tags"]
        assert f"frequency:{frequency}" in md["tags"]
        assert f"tense:{tense}" in md["tags"]


@pytest.mark.parametrize(
    "change", ["space", "unicode", "label", "identifier", "order", "original", "system"]
)
def test_full_dataset_corruption_stops_before_solver_setup(
    copy_source_files, monkeypatch, change
):
    name = "HS_LF_PR_2000"
    original_path = "prompts/userPrompts/HS_LF_PR_500_complete.json"
    system_path = "prompts/systemPrompts/zeroShot.json"
    working_path = f"datasets/{name}.json"
    tmp_path = copy_source_files([original_path, system_path, working_path])
    if change in {"original", "system"}:
        path = tmp_path / (original_path if change == "original" else system_path)
        path.write_bytes(path.read_bytes() + b" ")
    else:
        path = tmp_path / working_path
        rows = json.loads(path.read_text())
        if change == "space":
            rows[-1][2] += " "
        elif change == "unicode":
            rows[-1][2] += "\u200b"
        elif change == "label":
            rows[-1][6] = "invalid" if rows[-1][6] == "valid" else "valid"
        elif change == "identifier":
            rows[-1][1] = {"changed": True}
        else:
            rows[0], rows[-1] = rows[-1], rows[0]
        path.write_text(json.dumps(rows))
    generate = Mock(side_effect=AssertionError("Unexpected solver setup"))
    monkeypatch.setattr(tasks, "generate_with_capture", generate)
    with pytest.raises(ValueError):
        tasks.hs_zero_shot(name, root=str(tmp_path))
    generate.assert_not_called()
    assert not (tmp_path / "results").exists()


def test_numeric_source_id_type_changes_are_rejected(tmp_path, monkeypatch):
    name = "HS_HF_PR_2000"
    original_path = "prompts/userPrompts/HS_HF_PR_500_complete.json"
    before = json.loads((PROJECT_ROOT / original_path).read_text())
    before[0][1] = 1
    after = json.loads(json.dumps(before))
    after[0][1] = True
    (tmp_path / original_path).parent.mkdir(parents=True)
    baseline = json.dumps(before).encode()
    (tmp_path / original_path).write_bytes(baseline)
    (tmp_path / "datasets").mkdir()
    (tmp_path / f"datasets/{name}.json").write_text(json.dumps(after))
    monkeypatch.setattr(corpus, "git_bytes", lambda root, revision, path: baseline)
    with pytest.raises(ValueError, match="unexpected metadata change"):
        tasks.hs_zero_shot(name, root=str(tmp_path))
