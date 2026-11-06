"""Check frozen-phase recovery, no duplicated work, and error precedence."""

import json
from types import SimpleNamespace

import pytest

from llm_transitivity.evidence.serialization import digest, json_bytes
from llm_transitivity.runs import followup


def campaign(root):
    directory = root / "campaign"
    directory.mkdir()
    price = root / "quote.json"
    price.write_text("{}")
    manifest = {
        "price_estimate": "quote.json",
        "price_estimate_sha256": digest(price.read_bytes()),
        "stages": [],
    }
    for name in ["preflight", "coverage", "load-64"]:
        phase = directory / name
        (phase / "provenance").mkdir(parents=True)
        (phase / "summary").mkdir()
        spec = {
            "log_dir": str(phase / "inspect"),
            "tasks": [],
            "options": {"metadata": {}},
        }
        path = phase / "provenance/flow_spec.json"
        path.write_bytes(json_bytes(spec))
        (path.parent / "snapshot_hashes.json").write_text("{}")
        manifest["stages"].append(
            {
                "name": name,
                "spec": str(path.relative_to(directory)),
                "spec_sha256": digest(path.read_bytes()),
            }
        )
    (directory / "campaign.json").write_bytes(json_bytes(manifest))
    return directory


def test_resume_does_not_launch_already_verified_phases(tmp_path, monkeypatch):
    directory = campaign(tmp_path)
    calls = []
    monkeypatch.setattr(followup, "init", lambda **kwargs: None)
    monkeypatch.setattr(
        followup,
        "_phase_run",
        lambda root, phase, spec: calls.append(phase.name) or True,
    )
    monkeypatch.setattr(
        followup, "review_phase", lambda *args: {"technical_pass": True}
    )
    import llm_transitivity.analysis.followup_report as reporting

    monkeypatch.setattr(reporting, "write_report", lambda *args: None)
    assert followup.execute(tmp_path, directory)
    assert calls == ["preflight", "coverage", "load-64"]
    calls.clear()
    assert followup.execute(tmp_path, directory)
    assert calls == []


def test_failed_preflight_prevents_later_model_calls(tmp_path, monkeypatch):
    directory = campaign(tmp_path)
    calls = []
    monkeypatch.setattr(followup, "init", lambda **kwargs: None)
    monkeypatch.setattr(
        followup,
        "_phase_run",
        lambda root, phase, spec: calls.append(phase.name) or True,
    )
    monkeypatch.setattr(
        followup, "review_phase", lambda *args: {"technical_pass": False}
    )
    import llm_transitivity.analysis.followup_report as reporting

    monkeypatch.setattr(reporting, "write_report", lambda *args: None)
    assert followup.execute(tmp_path, directory) is False
    assert calls == ["preflight"]
    events = [
        json.loads(line)
        for line in (directory / "events.jsonl").read_text().splitlines()
    ]
    assert [e["stage"] for e in events if e["status"] == "omitted"] == [
        "coverage",
        "load-64",
    ]


def test_changed_frozen_spec_prevents_all_calls(tmp_path, monkeypatch):
    directory = campaign(tmp_path)
    manifest = json.loads((directory / "campaign.json").read_text())
    (directory / manifest["stages"][0]["spec"]).write_text("{} changed")
    monkeypatch.setattr(followup, "init", lambda **kwargs: None)
    with pytest.raises(ValueError, match="Frozen Flow spec changed"):
        followup.execute(tmp_path, directory)


def test_execution_error_survives_a_second_finalization_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(followup, "_checkpoint", lambda phase: None)

    def fail_run(**kwargs):
        raise ValueError("original")

    def fail_close(*args):
        raise OSError("secondary")

    monkeypatch.setattr(followup, "run", fail_run)
    monkeypatch.setattr(followup, "_finalize", fail_close)
    with pytest.raises(ValueError, match="original") as caught:
        followup._phase_run(tmp_path, tmp_path, SimpleNamespace())
    assert caught.value.__notes__ == ["Finalization failed: OSError"]
