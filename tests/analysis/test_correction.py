"""Exercise replacement composition with synthetic responses and no HTTP."""

import json

import pytest

from llm_transitivity.analysis import correction
from llm_transitivity.analysis.full_store import database, load_cases
from llm_transitivity.datasets.correction import MANIFEST, SOURCE_RUN
from tests.paths import PROJECT_ROOT


def test_incomplete_correction_is_rejected(tmp_path):
    (tmp_path / "correction_manifest.json").write_text(
        json.dumps({"id": "eate-to-ate-v1", "source_run": SOURCE_RUN})
    )
    (tmp_path / "worker.json").write_text('{"status":"running"}')
    with pytest.raises(ValueError, match="not complete"):
        correction.validate_correction(PROJECT_ROOT, tmp_path, {})


def test_composition_replaces_only_authorized_responses(tmp_path, monkeypatch):
    db = database(tmp_path / "test.sqlite")
    _, config = load_cases(db, PROJECT_ROOT, PROJECT_ROOT / SOURCE_RUN)
    for model in config["requested_routing"]:
        db.execute(
            "INSERT INTO results SELECT 'corpus',?,uid,'yes','answered','yes',target='yes',1,'old.eval','old-hash',NULL,0,0,0,1,2,1 FROM cases",
            (model,),
        )
    db.commit()
    amendment = json.loads((PROJECT_ROOT / MANIFEST).read_text())
    monkeypatch.setattr(
        correction,
        "validate_correction",
        lambda *args: (amendment, {"corpus": None, "preflight": None}),
    )
    uids = [r["corrected_uid"] for r in amendment["cases"]]

    def ingest(db, root, run, phase, system, config, provenance, index):
        for uid in uids if phase == "corpus" else uids[:1]:
            for model in config["requested_routing"]:
                db.execute(
                    "INSERT INTO results VALUES (?,?,?,'no','answered','no',0,1,'new.eval','new-hash',NULL,0,0,0,3,4,1)",
                    (phase, model, uid),
                )
        return []

    monkeypatch.setattr(correction, "ingest_phase", ingest)
    # The result directory must be within the repository for provenance paths.
    directory = PROJECT_ROOT / "tmp/correction-unit-events"
    directory.mkdir(parents=True, exist_ok=True)
    events = directory / "events.jsonl"
    events.write_text(
        "\n".join(
            json.dumps({"stage": "corpus", "status": status, "at_utc": at})
            for status, at in [
                ("started", "2026-11-06T10:00:00Z"),
                ("passed", "2026-11-06T10:01:00Z"),
            ]
        )
    )
    try:
        result = correction.apply_correction(
            db, PROJECT_ROOT, directory, config, "system", {}
        )
    finally:
        events.unlink()
        directory.rmdir()
    assert result["responses"] == 3672
    assert (
        db.execute("SELECT COUNT(*) FROM results WHERE phase='corpus'").fetchone()[0]
        == 324000
    )
    assert (
        db.execute("SELECT COUNT(*) FROM results WHERE log='old.eval'").fetchone()[0]
        == 320328
    )
    assert (
        db.execute(
            "SELECT COUNT(*) FROM replacements WHERE after_json IS NOT NULL"
        ).fetchone()[0]
        == 3672
    )
    assert (
        db.execute(
            "SELECT COUNT(*) FROM results WHERE phase='correction_preflight'"
        ).fetchone()[0]
        == 6
    )
    assert all(
        r["samples"] == 612 and r["changed_answers"] == 612 for r in result["changes"]
    )
    db.close()
