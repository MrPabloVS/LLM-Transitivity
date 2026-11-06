"""Check local report views without downloading or starting the UI."""

import json

import duckdb
import pytest

from llm_transitivity.cli.explore import main, register_views


def test_report_views_preserve_text_and_null_cost(tmp_path):
    report = tmp_path / "report's data"
    (report / "tables").mkdir(parents=True)
    (report / "data").mkdir()
    csv = report / "tables" / "costs.csv"
    csv.write_text("model,cost\na,0\nb,\n")
    (report / "tables" / "cost_conflicts.csv").touch()
    cases = report / "data" / "cases.json"
    cases.write_text(json.dumps([{"uid": "x", "prompt": "¿A → B?", "responses": []}]))
    original = {p: p.read_bytes() for p in [csv, cases]}
    with duckdb.connect() as connection:
        register_views(connection, report)
        assert connection.execute(
            "SELECT cost FROM report.costs ORDER BY model"
        ).fetchall() == [(0,), (None,)]
        assert connection.execute(
            "SELECT prompt FROM report.case_details"
        ).fetchone() == ("¿A → B?",)
    assert all(path.read_bytes() == content for path, content in original.items())


def test_missing_report_does_not_create_database(tmp_path):
    with pytest.raises(SystemExit):
        main(tmp_path, ["--report", "missing"])
    assert not (tmp_path / ".local").exists()


def test_invalid_port(tmp_path):
    with pytest.raises(SystemExit):
        main(tmp_path, ["--report", "missing", "--port", "0"])
