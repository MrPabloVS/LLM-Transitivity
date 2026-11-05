import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from llm_transitivity.inspect import tasks as inspect_tasks

ROOT = Path(__file__).resolve().parents[1]


def test_trial_preserves_all_prompts_and_metadata():
    rows = json.loads((ROOT / "datasets" / "HS.json").read_text())
    system = json.loads((ROOT / "prompts/systemPrompts/zeroShot.json").read_text())[0]
    evaluation = inspect_tasks.hs_zero_shot(root=str(ROOT))
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
    with pytest.raises(ValueError, match="case 1"):
        inspect_tasks.hs_zero_shot("bad", root=str(tmp_path))


def test_invalid_last_case_stops_inspect_before_calls_or_writes(tmp_path, monkeypatch):
    row = [
        "HS",
        1,
        "Does it follow?",
        "HF",
        "PR",
        "if then / therefore",
        "valid",
        "canonic",
    ]
    datasets = tmp_path / "datasets"
    datasets.mkdir()
    (datasets / "bad.json").write_text(json.dumps([row, row[:7]]))
    generate = Mock(side_effect=AssertionError("Unexpected generation setup"))
    monkeypatch.setattr(inspect_tasks, "generate_with_capture", generate)
    with pytest.raises(ValueError, match="case 2"):
        inspect_tasks.hs_zero_shot("bad", root=str(tmp_path))
    generate.assert_not_called()
    assert {path.name for path in tmp_path.iterdir()} == {"datasets"}
