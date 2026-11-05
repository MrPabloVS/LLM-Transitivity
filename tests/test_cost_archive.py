"""Protect existing estimates when saving a new capture."""

import json
from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import UUID

import pytest

from llm_transitivity.cli import costs
from llm_transitivity.costs import archive

REPORT = {
    "checked_at_utc": "2026-11-05T22:00:00+00:00",
    "totals_usd": {"scenario": 0.35},
}


def test_cost_command_saves_each_capture_and_preserves_historical_report(
    tmp_path, monkeypatch, capsys
):
    historical = tmp_path / "docs/unrelated_report.json"
    historical.parent.mkdir()
    historical.write_bytes(b'{"historical":true}\n')
    monkeypatch.setattr(costs, "estimate", Mock(return_value=REPORT))
    costs.main(tmp_path, [])
    costs.main(tmp_path, [])
    captures = sorted((tmp_path / "results/cost_estimates").glob("*/estimate.json"))
    assert len(captures) == 2
    assert captures[0].parent != captures[1].parent
    assert all(json.loads(path.read_text()) == REPORT for path in captures)
    assert historical.read_bytes() == b'{"historical":true}\n'
    output = capsys.readouterr().out
    assert all(str(path) in output for path in captures)


def test_capture_collision_keeps_original_bytes(tmp_path, monkeypatch):
    fixed = datetime(2026, 11, 5, 22, 0, tzinfo=UTC)
    monkeypatch.setattr(archive, "datetime", Mock(now=Mock(return_value=fixed)))
    monkeypatch.setattr(archive, "uuid4", lambda: UUID(int=0))
    path = archive.save_estimate(tmp_path, REPORT)
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        archive.save_estimate(tmp_path, {"replacement": True})
    assert path.read_bytes() == before


def test_failed_estimate_creates_no_capture(tmp_path, monkeypatch):
    monkeypatch.setattr(
        costs, "estimate", Mock(side_effect=RuntimeError("quote failed"))
    )
    with pytest.raises(RuntimeError, match="quote failed"):
        costs.main(tmp_path, [])
    assert not (tmp_path / "results").exists()
