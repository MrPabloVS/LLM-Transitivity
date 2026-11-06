"""Regressions for static interpretation and preservation boundaries."""

import json

import duckdb
import markdown
import pytest

from llm_transitivity.analysis.interpret import interpret
from llm_transitivity.analysis.interpret_data import (
    aggregate,
    compare_counts,
    examples,
    paired,
    prepare,
    ratio,
    validate_keys,
)
from llm_transitivity.analysis.interpret_document import render


@pytest.fixture
def connection():
    with duckdb.connect() as con:
        con.execute("""CREATE TABLE results (
            uid VARCHAR, model VARCHAR, family VARCHAR, status VARCHAR,
            answer VARCHAR, matched INTEGER, strict INTEGER, raw VARCHAR
        )""")
        con.execute("""INSERT INTO results VALUES
            ('u1','a','HS','answered','yes',1,1,'yes'),
            ('u1','b','HS','answered','no',0,1,'no'),
            ('u2','a','HS','content_filter',NULL,NULL,0,''),
            ('u2','b','HS','answered','yes',1,0,'Yes, it follows.'),
            ('u3','a','mHS','ambiguous',NULL,NULL,0,'yes or no'),
            ('u3','b','mHS','answered','no',1,1,'no')
        """)
        yield con


def test_categories_denominators_and_absent_combinations(connection):
    result = aggregate(connection, ["family"])
    a_hs = next(r for r in result if r["model"] == "a" and r["family"] == "HS")
    assert a_hs["samples"] == 2
    assert a_hs["matched_total"] == 0.5
    assert a_hs["agreement"] == 1
    assert a_hs["content_filter"] == 1
    assert a_hs["no"] == 0
    a_mhs = next(r for r in result if r["model"] == "a" and r["family"] == "mHS")
    assert a_mhs["agreement"] is None
    assert a_mhs["ambiguous"] == 1
    assert ratio(0, 0) is None
    connection.execute("DELETE FROM results WHERE model='b' AND family='mHS'")
    assert len(aggregate(connection, ["family"])) == 3


def test_pairs_exclude_uninterpretable_answers(connection):
    pair = paired(connection)[0]
    assert pair["paired_cases"] == 3
    assert pair["both_interpreted"] == 1
    assert pair["same_answer"] == 0
    assert pair["a_only_match"] == 1
    assert pair["b_only_match"] == 0


def test_format_change_does_not_change_interpretation(connection):
    before = aggregate(connection, [])
    connection.execute(
        "UPDATE results SET raw='**yes**', strict=0 WHERE uid='u1' AND model='a'"
    )
    after = aggregate(connection, [])
    assert before[0]["agreement"] == after[0]["agreement"]
    assert before[0]["strict"] == after[0]["strict"] + 1


def test_duplicate_results_rejected(connection):
    connection.execute(
        "CREATE TABLE cases AS SELECT DISTINCT uid, 's' AS stratum FROM results"
    )
    validate_keys(connection, ["a", "b"], 3, 1, 3)
    connection.execute("DELETE FROM results WHERE uid='u3' AND model='a'")
    connection.execute(
        "INSERT INTO results SELECT * FROM results WHERE uid='u1' AND model='a'"
    )
    with pytest.raises(ValueError, match="Duplicate"):
        validate_keys(connection, ["a", "b"], 3, 1, 3)


def test_examples_are_stable_and_unique(connection):
    connection.execute(
        "CREATE TABLE cases AS SELECT DISTINCT uid, [] AS responses FROM results"
    )
    first = examples(connection)
    second = examples(connection)
    assert first == second
    ids = [r["case"]["uid"] for r in first if r["case"]]
    assert len(ids) == len(set(ids))
    assert any(r["case"] is None for r in first)


def test_null_is_not_zero_in_reconciliation():
    with pytest.raises(ValueError, match="mismatch"):
        compare_counts(
            [{"id": "x", "cost": None}], [{"id": "x", "cost": 0}], ["id"], ["cost"]
        )
    compare_counts([{"id": "x", "cost": 0}], [{"id": "x", "cost": 0}], ["id"], ["cost"])


def test_incomplete_source_and_existing_destination(tmp_path):
    output = tmp_path / "exists"
    output.mkdir()
    with pytest.raises(ValueError, match="already exists"):
        interpret(tmp_path, tmp_path / "missing", output)
    (tmp_path / "validation.json").write_text(json.dumps({"complete": False}))
    with (
        duckdb.connect() as con,
        pytest.raises(ValueError, match="not fully validated"),
    ):
        prepare(tmp_path, con)


def test_three_formats_share_text_and_escape_markup(tmp_path):
    blocks = [
        {"kind": "heading", "level": 1, "text": "Static analysis"},
        {"kind": "text", "text": "54,000 cases & 324,000 responses"},
        {"kind": "literal", "text": '<script>alert("x")</script> ¿A → B?'},
        {
            "kind": "table",
            "headers": ["Cost", "Meaning"],
            "rows": [[0, "zero"], ["unknown", "not zero"]],
        },
    ]
    render(tmp_path, blocks)
    md = (tmp_path / "report.md").read_text()
    html = (tmp_path / "index.html").read_text()
    assert markdown.markdown(md, extensions=["tables"]) in html
    assert "<script>" not in html
    assert (tmp_path / "report.pdf").read_bytes().startswith(b"%PDF")
    assert json.loads((tmp_path / "document.json").read_text()) == blocks
