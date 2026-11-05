"""Redact errors even when a sample has no model events."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from llm_transitivity.runs import export


@pytest.mark.parametrize("has_error", [False, True])
def test_eventless_export_uses_the_same_redaction_policy(
    tmp_path, monkeypatch, has_error
):
    secret = "test-export-key-not-real"
    error = {
        "message": f"Request failed with {secret}",
        "unknown": {"zero": 0, "null": None},
    }
    sample = SimpleNamespace(
        id=1,
        metadata={"sample_uid": "source-row-1"},
        events=[],
        error=Mock(model_dump=Mock(return_value=error)) if has_error else None,
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", secret)
    monkeypatch.setattr(
        export, "read_eval_log", Mock(return_value=SimpleNamespace(samples=[sample]))
    )
    path = tmp_path / "failed.eval"
    path.write_bytes(b"mock log")
    records = export.export_log(path)
    assert secret not in json.dumps(records)
    assert records[0]["status"] == "no model event"
    assert records[0]["sample_uid"] == "source-row-1"
    if has_error:
        assert records[0]["sample_error"]["message"] == "Request failed with [REDACTED]"
        assert records[0]["sample_error"]["unknown"] == {"zero": 0, "null": None}
    else:
        assert records[0]["sample_error"] is None
