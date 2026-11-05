import json
import runpy
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from dataset_validation import load_dataset

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CASE = [
    "HS",
    [["S1", "V1", "O1"]],
    "Does the conclusion follow?",
    "HF",
    "PR",
    "if then / therefore",
    "valid",
    "canonic",
]


def test_valid_dataset_preserves_content(tmp_path):
    path = tmp_path / "valid.json"
    path.write_text(json.dumps([CASE]), encoding="utf-8")
    assert load_dataset(path) == [CASE]


@pytest.mark.parametrize("rows", [[], {}, [CASE[:7]], [None]])
def test_incompatible_structure(tmp_path, rows):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(ValueError, match=str(path)):
        load_dataset(path)


@pytest.mark.parametrize("value", [None, [], "", "   "])
def test_invalid_prompt_reports_case_and_field(tmp_path, value):
    row = CASE.copy()
    row[2] = value
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([CASE, row]), encoding="utf-8")
    with pytest.raises(ValueError, match=r"case 2: prompt \(field 2\)"):
        load_dataset(path)


def test_missing_file(tmp_path):
    with pytest.raises(ValueError, match="cannot read dataset"):
        load_dataset(tmp_path / "missing.json")


def test_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("[", encoding="utf-8")
    with pytest.raises(ValueError, match="cannot decode dataset"):
        load_dataset(path)


def test_invalid_last_case_stops_runner_before_calls_or_writes(
    tmp_path, monkeypatch, capsys
):
    runner = tmp_path / "runBenchmark.py"
    runner.write_bytes((PROJECT_ROOT / "runBenchmark.py").read_bytes())
    datasets = tmp_path / "datasets"
    datasets.mkdir()
    (datasets / "bad.json").write_text(json.dumps([CASE, CASE[:7]]), encoding="utf-8")
    post = Mock(side_effect=AssertionError("Unexpected model call"))
    monkeypatch.setattr("requests.post", post)
    monkeypatch.setattr(sys, "argv", [str(runner), "bad"])
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(runner), run_name="__main__")
    assert error.value.code == 2
    assert "case 2" in capsys.readouterr().err
    post.assert_not_called()
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "logs").exists()


@pytest.mark.parametrize(
    "path", sorted((PROJECT_ROOT / "datasets").glob("*.json")), ids=lambda p: p.name
)
def test_current_datasets(path):
    assert load_dataset(path)
