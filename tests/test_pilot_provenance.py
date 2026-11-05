import json
from collections import Counter
from pathlib import Path

import pytest

from llm_transitivity.datasets import pilot as prepare_pilot
from llm_transitivity.evidence import serialization
from llm_transitivity.inspect import tasks as inspect_tasks
from pilot_config import MODELS, build_pilot_spec

ROOT = Path(__file__).resolve().parents[1]


def test_full_corpus_and_deterministic_selection():
    manifest = prepare_pilot.verify(ROOT)
    assert len(manifest["datasets"]) == 18
    assert sum(e["case_count"] for e in manifest["datasets"]) == 54000
    assert sum(len(e["strata"]) for e in manifest["datasets"]) == 108
    assert sum(len(e["selected_rows"]) for e in manifest["datasets"]) == 540


@pytest.mark.parametrize("name", prepare_pilot.dataset_names())
def test_every_pilot_sentence_and_metadata_reaches_inspect_unchanged(name):
    rows, entry = prepare_pilot.verified_pilot(ROOT, name)
    full = json.loads((ROOT / entry["working_path"]).read_text())
    original = json.loads((ROOT / entry["original_path"]).read_text())
    pilot_name = Path(entry["pilot_path"]).stem
    evaluation = inspect_tasks.hs_zero_shot(f"pilot/{pilot_name}", root=str(ROOT))
    samples = list(evaluation.dataset)
    assert Path(evaluation.dataset.location).is_file()
    assert int(pilot_name.rsplit("_", 1)[1]) == len(rows)
    system = json.loads((ROOT / "prompts/systemPrompts/zeroShot.json").read_text())[0]
    assert len(rows) == len(samples) == len(entry["strata"]) * 5
    counts = Counter(prepare_pilot.stratum(row) for row in rows)
    assert set(counts.values()) == {5}
    assert len(counts) == len(entry["strata"])
    for row, sample, origin in zip(rows, samples, entry["selected_rows"]):
        index = origin["original_row"] - 1
        assert row == full[index]
        assert sample.input[1].content == original[index][2] == row[2]
        assert sample.input[0].content == system
        assert sample.metadata["source_id"] == original[index][1]
        assert sample.metadata["original_row"] == sample.id == index + 1
        assert sample.metadata["frequency"] == row[3]
        assert sample.metadata["verbal_time"] == row[4]
        assert sample.metadata["connectors"] == row[5]
        assert sample.metadata["source_validity"] == row[6]
        assert sample.metadata["canonical_form"] == row[7]


@pytest.fixture
def isolated_source(tmp_path, monkeypatch):
    name = "HS_LF_PR_2000"
    saved = json.loads((ROOT / prepare_pilot.MANIFEST).read_text())
    entry = next(e for e in saved["datasets"] if e["dataset"] == name)
    paths = [
        entry["working_path"],
        entry["original_path"],
        entry["pilot_path"],
        saved["system_prompt"]["path"],
        str(prepare_pilot.MANIFEST),
    ]
    baseline = {
        entry["original_path"]: (ROOT / entry["original_path"]).read_bytes(),
        saved["system_prompt"]["path"]: (
            ROOT / saved["system_prompt"]["path"]
        ).read_bytes(),
    }
    for path in paths:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / path).read_bytes())
    monkeypatch.setattr(
        prepare_pilot, "git_bytes", lambda root, revision, path: baseline[path]
    )
    return tmp_path, name, entry


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
        path = root / prepare_pilot.MANIFEST
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


def test_preparation_refuses_to_replace_evidence():
    with pytest.raises(ValueError, match="already exist"):
        prepare_pilot.prepare(ROOT, 5)


def test_six_models_cover_all_eighteen_datasets_without_reasoning_or_fallback():
    spec = build_pilot_spec()
    assert len(spec.tasks) == 108
    assert len(MODELS) == 6
    assert len({task.args["dataset"] for task in spec.tasks}) == 18
    for task in spec.tasks:
        assert task.model.config.max_tokens == 1024
        args = task.model.model_args
        assert args["max_retries"] == 0
        assert args["provider"]["allow_fallbacks"] is False
        assert len(args["provider"]["only"]) == 1
        if "gpt-4o-mini" not in task.model.name:
            assert args["reasoning_enabled"] is False
