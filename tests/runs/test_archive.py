"""Keep results, source snapshots, and failure evidence in one run archive."""

import json
from pathlib import Path

import pytest
from inspect_flow.api import run

from llm_transitivity.evidence.serialization import digest
from llm_transitivity.runs import runner
from tests.paths import PROJECT_ROOT


def test_all_results_and_evidence_stay_in_one_archive(tmp_path, mock_run_spec):
    spec = mock_run_spec
    assert runner.execute(spec, PROJECT_ROOT)
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
    assert {
        "src/llm_transitivity/domain/config.py",
        "src/llm_transitivity/domain/cases.py",
    } <= hashes.keys()
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
        runner.execute(spec, PROJECT_ROOT)


def test_failure_leaves_provenance_and_error_index(
    tmp_path, monkeypatch, mock_run_spec
):
    spec = mock_run_spec

    def fail(**kwargs):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(runner, "run", fail)
    with pytest.raises(RuntimeError, match="simulated failure"):
        runner.execute(spec, PROJECT_ROOT)
    index = json.loads((tmp_path / "one-run/summary/log_index.json").read_text())
    assert index["runner_error_type"] == "RuntimeError"
    assert index["flow_success"] is None
    assert index["call_export_status"] == "no logs"


def test_dry_run_does_not_create_archive(tmp_path, mock_run_spec):
    spec = mock_run_spec
    run(spec=spec, dry_run=True)
    assert not (tmp_path / "one-run").exists()


@pytest.mark.parametrize("changed", ["source", "manifest"])
def test_changed_evidence_stops_before_archive_creation(mock_run_spec, changed):
    from llm_transitivity.runs.archive import prepare_archive

    spec = mock_run_spec
    if changed == "source":
        path = next(iter(spec.options.metadata["source_sha256"]))
        spec.options.metadata["source_sha256"][path] = "0" * 64
    else:
        spec.options.metadata["pilot_manifest_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="evidence changed"):
        prepare_archive(spec, PROJECT_ROOT)
    assert not Path(spec.log_dir).parent.exists()
