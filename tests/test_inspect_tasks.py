import json

import pytest

import inspect_tasks


def test_trial_preserves_all_prompts_and_metadata():
    rows = json.loads((inspect_tasks.PROJECT_ROOT / "datasets" / "HS.json").read_text())
    system = json.loads(
        (inspect_tasks.PROJECT_ROOT / "prompts/systemPrompts/zeroShot.json").read_text()
    )[0]
    evaluation = inspect_tasks.hs_zero_shot()
    assert len(evaluation.dataset) == len(rows) == 10
    assert evaluation.scorer is not None
    for number, (sample, row) in enumerate(zip(evaluation.dataset, rows), start=1):
        assert sample.id == number
        assert sample.target == ("yes" if row[6] == "valid" else "no")
        assert [(m.role, m.content) for m in sample.input] == [
            ("system", system),
            ("user", row[2]),
        ]
        expected = {
            "source_dataset": "HS",
            "source_row": number,
            "source_id": row[1],
            "case_type": row[0],
            "frequency": row[3],
            "verbal_time": row[4],
            "connectors": row[5],
            "source_validity": row[6],
            "canonical_form": row[7],
        }
        assert all(sample.metadata[key] == value for key, value in expected.items())
        assert sample.metadata["expected_answer"] == sample.target
        assert sample.metadata["sample_uid"]


def test_bad_dataset_is_rejected_before_task_creation(tmp_path, monkeypatch):
    datasets = tmp_path / "datasets"
    datasets.mkdir()
    (datasets / "bad.json").write_text(json.dumps([["HS"]]))
    monkeypatch.setattr(inspect_tasks, "PROJECT_ROOT", tmp_path)
    with pytest.raises(ValueError, match="case 1"):
        inspect_tasks.hs_zero_shot("bad")
