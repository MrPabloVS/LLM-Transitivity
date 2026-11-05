import json
from collections import Counter
from pathlib import Path

import pytest
from inspect_ai.model import GenerateConfig
from inspect_flow import FlowModel
from inspect_flow.api import run

from llm_transitivity.runs import runner as run_pilot
from pilot_config import MODEL_GROUPS, build_pilot_spec
from prepare_pilot import digest

ROOT = Path(__file__).resolve().parents[1]


def small_spec(tmp_path):
    spec = build_pilot_spec()
    spec.tasks = [spec.tasks[0]]
    spec.tasks[0].model = FlowModel(
        name="mockllm/model", config=GenerateConfig(max_tokens=1024)
    )
    spec.log_dir = str(tmp_path / "one-run" / "inspect")
    spec.options.limit = 1
    spec.options.display = "none"
    return spec


def test_all_results_and_evidence_stay_in_one_archive(tmp_path):
    spec = small_spec(tmp_path)
    assert run_pilot.execute(spec, ROOT)
    archive = tmp_path / "one-run"
    assert {p.name for p in archive.iterdir()} == {
        "inspect",
        "openrouter_calls",
        "provenance",
        "summary",
    }
    assert len(list((archive / "inspect").glob("*.eval"))) == 1
    assert len(list((archive / "openrouter_calls").glob("*.json"))) == 1
    frozen = json.loads((archive / "provenance/run.json").read_text())
    assert frozen["experiment_run_id"] == spec.options.metadata["experiment_run_id"]
    assert (archive / "provenance/flow_spec.json").is_file()
    hashes = json.loads((archive / "provenance/snapshot_hashes.json").read_text())
    assert {"experiment_config.py", "benchmark_cases.py"} <= hashes.keys()
    for relative, expected in hashes.items():
        assert (
            digest((archive / "provenance/snapshot" / relative).read_bytes())
            == expected
        )
    index = json.loads((archive / "summary/log_index.json").read_text())
    assert index["flow_success"] is True
    assert index["call_export_status"] == "exported"
    assert index["logs"][0]["generation_group"] == "earlier"
    assert index["logs"][0]["sample_count"] == 1
    with pytest.raises(FileExistsError):
        run_pilot.execute(spec, ROOT)


def test_failure_leaves_provenance_and_error_index(tmp_path, monkeypatch):
    spec = small_spec(tmp_path)

    def fail(**kwargs):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(run_pilot, "run", fail)
    with pytest.raises(RuntimeError, match="simulated failure"):
        run_pilot.execute(spec, ROOT)
    index = json.loads((tmp_path / "one-run/summary/log_index.json").read_text())
    assert index["runner_error_type"] == "RuntimeError"
    assert index["flow_success"] is None
    assert index["call_export_status"] == "no logs"


def test_dry_run_does_not_create_archive(tmp_path):
    spec = small_spec(tmp_path)
    run(spec=spec, dry_run=True)
    assert not (tmp_path / "one-run").exists()


def test_generation_groups_and_shared_folder():
    assert Counter(MODEL_GROUPS.values()) == {"earlier": 3, "later": 3}
    spec = build_pilot_spec()
    assert Counter(task.metadata["generation_group"] for task in spec.tasks) == {
        "earlier": 54,
        "later": 54,
    }
    assert Path(spec.log_dir).name == "inspect"
    assert Path(spec.log_dir).parent.parent == ROOT / "results/pilot"
    assert spec.log_dir_create_unique is False
    for task in spec.tasks:
        assert f"generation_group:{task.metadata['generation_group']}" in task.tags


def test_preflight_is_one_identical_case_on_each_model():
    spec = build_pilot_spec(preflight=True)
    assert len(spec.tasks) == 6
    assert len({task.model.name for task in spec.tasks}) == 6
    assert len({task.args["dataset"] for task in spec.tasks}) == 1
    assert len({tuple(task.sample_id) for task in spec.tasks}) == 1
    assert len(spec.tasks[0].sample_id) == 1
    assert spec.options.metadata["planned_responses"] == 6
    assert spec.options.metadata["selected_cases_per_model"] == 1
    assert spec.options.metadata["phase"] == "preflight"
    assert Path(spec.log_dir).parent.name.endswith("_preflight")
    assert all("phase:preflight" in task.tags for task in spec.tasks)
