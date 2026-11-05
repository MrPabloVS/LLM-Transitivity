import json
from pathlib import Path

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


@pytest.mark.parametrize(
    "path", sorted((PROJECT_ROOT / "datasets").glob("*.json")), ids=lambda p: p.name
)
def test_current_datasets(path):
    assert load_dataset(path)
