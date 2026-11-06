"""Stop full-corpus calls after a failed preflight and retain primary errors."""

import json

import pytest

from llm_transitivity.runs import full


def prepared(root):
    stages = []
    for name in ["preflight", "corpus"]:
        phase = root / name
        (phase / "provenance").mkdir(parents=True)
        (phase / "summary").mkdir()
        path = phase / "provenance/flow_spec.json"
        path.write_text(
            json.dumps({"tasks": [], "options": {}, "log_dir": str(phase / "inspect")})
        )
        stages.append({"name": name, "spec": str(path.relative_to(root))})
    (root / "full_manifest.json").write_text(json.dumps({"stages": stages}))


def test_failed_preflight_prevents_full_corpus_calls(tmp_path, monkeypatch):
    prepared(tmp_path)
    monkeypatch.setattr(full, "_validate", lambda *args: None)
    monkeypatch.setattr(full, "init", lambda **kwargs: None)
    calls = []
    monkeypatch.setattr(
        full, "_phase_run", lambda root, phase, spec: calls.append(phase.name) or True
    )
    monkeypatch.setattr(full, "review_phase", lambda *args: {"technical_pass": False})
    assert full.execute(tmp_path, tmp_path) is False
    assert calls == ["preflight"]
    assert json.loads((tmp_path / "worker.json").read_text())["status"] == "stopped"


def test_worker_records_execution_failure_and_preserves_it(tmp_path, monkeypatch):
    prepared(tmp_path)
    monkeypatch.setattr(full, "_validate", lambda *args: None)
    monkeypatch.setattr(full, "init", lambda **kwargs: None)

    def fail(*args):
        raise ValueError("primary")

    monkeypatch.setattr(full, "_phase_run", fail)
    with pytest.raises(ValueError, match="primary"):
        full.execute(tmp_path, tmp_path)
    assert json.loads((tmp_path / "worker.json").read_text())["status"] == "failed"


def test_resume_skips_passed_phases_without_generations(tmp_path, monkeypatch):
    from llm_transitivity.evidence.serialization import digest

    prepared(tmp_path)
    monkeypatch.setattr(full, "_validate", lambda *args: None)
    monkeypatch.setattr(full, "init", lambda **kwargs: None)
    for stage in ["preflight", "corpus"]:
        path = tmp_path / stage / "summary/closure.json"
        path.write_text('{"complete": true}')
        full._event(
            tmp_path,
            stage=stage,
            status="passed",
            review=str(path.relative_to(tmp_path)),
            review_sha256=digest(path.read_bytes()),
        )

    def forbidden(*args):
        raise AssertionError("Completed phase must not request generations")

    monkeypatch.setattr(full, "_phase_run", forbidden)
    assert full.execute(tmp_path, tmp_path)
