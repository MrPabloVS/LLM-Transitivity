"""Keep execution failures visible when archive finalization also fails."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from llm_transitivity.runs import archive, runner


@pytest.mark.parametrize(
    "primary", [RuntimeError("primary"), KeyboardInterrupt(), asyncio.CancelledError()]
)
def test_primary_failure_survives_failed_finalization(
    monkeypatch, tmp_path, capsys, primary
):
    monkeypatch.setattr(runner, "prepare_archive", lambda *_: tmp_path)
    monkeypatch.setattr(runner, "run", Mock(side_effect=primary))
    monkeypatch.setattr(
        runner, "finalize_archive", Mock(side_effect=OSError("private-secondary"))
    )
    with pytest.raises(type(primary)) as caught:
        runner.execute(object(), tmp_path)
    assert caught.value is primary
    assert "OSError" in capsys.readouterr().err
    assert "private-secondary" not in " ".join(primary.__notes__)


def test_finalization_failure_after_success_is_fatal(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "prepare_archive", lambda *_: tmp_path)
    monkeypatch.setattr(runner, "run", Mock(return_value=SimpleNamespace(success=True)))
    monkeypatch.setattr(
        runner, "finalize_archive", Mock(side_effect=OSError("archive failed"))
    )
    with pytest.raises(OSError, match="archive failed"):
        runner.execute(object(), tmp_path)


def test_export_failure_keeps_index_and_fails_finalization(monkeypatch, tmp_path):
    (tmp_path / "inspect").mkdir()
    (tmp_path / "summary").mkdir()
    (tmp_path / "inspect" / "partial.eval").write_bytes(b"incomplete log")
    monkeypatch.setattr(
        archive, "read_eval_log", Mock(side_effect=ValueError("incomplete"))
    )
    monkeypatch.setattr(
        archive, "export_run", Mock(side_effect=OSError("export failed"))
    )
    with pytest.raises(OSError, match="export failed"):
        archive.finalize_archive(tmp_path, flow_success=True)
    report = json.loads((tmp_path / "summary/log_index.json").read_text())
    assert report["call_export_status"] == "failed: OSError"
