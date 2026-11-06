"""Check report denominators, paired outcomes, source integrity, and cost evidence."""

import json

import pytest

from llm_transitivity.analysis.full_render import literal, ratio
from llm_transitivity.analysis.full_report import report
from llm_transitivity.analysis.full_store import (
    capture_sample,
    database,
    observe_generation,
    validate_sample,
)
from llm_transitivity.analysis.full_summary import aggregate, pairwise
from llm_transitivity.domain.selection import stratum
from llm_transitivity.evidence.serialization import digest, record_digest


@pytest.fixture
def db(tmp_path):
    connection = database(tmp_path / "report.sqlite")
    yield connection
    connection.close()


def add_case(db, number=1):
    prompt = f"If café {number}, then B. Does C follow? <b>Original</b>"
    row = [
        "HS",
        ["S2", "V7", "O3"],
        prompt,
        "HF",
        "PR",
        "if then / therefore",
        "valid",
        "canonic",
    ]
    sh = digest(prompt.encode())
    uid = f"HS_HF_PR_2000:{number}:{sh[:16]}"
    values = (
        uid,
        "HS_HF_PR_2000",
        number,
        "HS",
        "HF",
        "PR",
        row[5],
        "valid",
        "canonic",
        record_digest(list(stratum(row)))[:16],
        prompt,
        "yes",
        json.dumps(row[1]),
        "prompts/original.json",
        sh,
        record_digest(row),
        record_digest(row),
        digest(uid.encode()),
    )
    db.execute("INSERT INTO cases VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
    return db.execute("SELECT * FROM cases WHERE uid=?", (uid,)).fetchone()


def add_result(db, model, uid, status, answer, matched, strict):
    db.execute(
        "INSERT INTO results (phase,model,uid,raw,status,answer,matched,strict) VALUES ('corpus',?,?,?,?,?,?,?)",
        (model, uid, answer or "", status, answer, matched, strict),
    )


def test_filters_remain_outside_agreement_but_inside_coverage(db):
    for i, values in enumerate(
        (
            ("answered", "yes", 1, 1),
            ("answered", "no", 0, 0),
            ("content_filter", None, 0, 0),
            ("ambiguous", None, 0, 0),
        ),
        1,
    ):
        add_result(db, "a", add_case(db, i)["uid"], *values)
    r = aggregate(db)[0]
    assert (r["samples"], r["answered"], r["matched"], r["disagreed"]) == (4, 2, 1, 1)
    assert r["agreement"] == r["coverage"] == 0.5
    assert r["format_rate"] == r["matched_total"] == 0.25
    assert r["content_filter"] == r["ambiguous"] == 1


def test_empty_interpretable_denominator_is_unknown(db):
    add_result(db, "a", add_case(db)["uid"], "content_filter", None, 0, 0)
    r = aggregate(db)[0]
    assert r["agreement"] is None
    assert r["coverage"] == 0
    assert "undefined" in ratio(0, 0)


def test_pairs_use_same_uid_and_expose_missing_answers(db):
    cases = [add_case(db, i)["uid"] for i in range(1, 5)]
    for uid, a, b in zip(
        cases,
        [
            ("answered", "yes", 1, 1),
            ("answered", "yes", 1, 1),
            ("answered", "no", 0, 1),
            ("content_filter", None, 0, 0),
        ],
        [
            ("answered", "no", 0, 1),
            ("answered", "yes", 1, 1),
            ("answered", "yes", 1, 1),
            ("answered", "yes", 1, 1),
        ],
        strict=True,
    ):
        add_result(db, "a", uid, *a)
        add_result(db, "b", uid, *b)
    row = pairwise(db, ["a", "b"])[0]
    assert row["paired_cases"] == 4
    assert row["both_interpreted"] == 3
    assert row["a_only_match"] == row["b_only_match"] == row["both_match"] == 1
    assert row["not_both_interpreted"] == 1


def test_costs_preserve_null_zero_conflict_and_deduplicate(db):
    observe_generation(db, "g", "m", "final_output", "r", None, {})
    assert db.execute("SELECT cost FROM generations").fetchone()[0] is None
    observe_generation(
        db, "g", "m", "generation_lookup", "r", 1.0, {"unknown_field": "retained"}
    )
    observe_generation(db, "g", "m", "captured_response", "r", 0.0, {})
    observe_generation(db, "g", "m", "captured_response", "r", 0.0, {})
    assert db.execute("SELECT cost FROM generations").fetchone()[0] == 0.0
    assert db.execute("SELECT COUNT(*) FROM generations").fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM cost_conflicts").fetchone()[0] == 1
    assert db.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 3
    assert (
        "unknown_field"
        in db.execute(
            "SELECT details FROM observations WHERE source='generation_lookup'"
        ).fetchone()[0]
    )
    with pytest.raises(ValueError, match="different models"):
        observe_generation(db, "g", "other", "final_output", "r", None, {})


def native_sample(case, raw="**yes**", status="answered", filtered=False):
    interpreted = "yes" if status == "answered" else None
    md = {
        "sample_uid": case["uid"],
        "expected_answer": "yes",
        "source_id": ["S2", "V7", "O3"],
        "dataset_family": "HS",
        "frequency": "HF",
        "verbal_time": "PR",
        "connectors": case["formulation"],
        "source_validity": "valid",
        "canonical_form": "canonic",
        "stratum_id": case["stratum"],
        "sentence_sha256": case["sentence_hash"],
        "working_record_sha256": case["working_hash"],
        "original_record_sha256": case["original_hash"],
        "original_row": case["row_number"],
        "original_path": case["original_path"],
    }
    return {
        "id": case["row_number"],
        "input": [
            {"role": "system", "content": "Only yes or no."},
            {"role": "user", "content": case["prompt"]},
        ],
        "target": "yes",
        "metadata": md,
        "output": {
            "completion": raw,
            "choices": [{"stop_reason": "content_filter" if filtered else "stop"}],
        },
        "scores": {
            "source_label_match": {
                "value": "C" if status == "answered" else "N",
                "answer": raw,
                "metadata": {
                    "status": status,
                    "expected": "yes",
                    "extracted_answer": interpreted,
                    "format_compliant": False,
                    "extraction_rule": "initial_or_final_line_v2",
                },
            }
        },
    }


def test_source_text_and_scores_checked_without_format_reclassification(db):
    case = add_case(db)
    sample = native_sample(case)
    result = validate_sample(sample, case, "Only yes or no.")
    assert result["matched"] == 1 and result["strict"] == 0
    sample["input"][1]["content"] += " "
    with pytest.raises(ValueError, match="text differs"):
        validate_sample(sample, case, "Only yes or no.")


def test_filter_is_not_reinterpreted_as_no(db):
    case = add_case(db)
    sample = native_sample(case, raw="no", status="content_filter", filtered=True)
    result = validate_sample(sample, case, "Only yes or no.")
    assert result["answer"] is None and result["matched"] == 0


def test_http_200_error_and_token_alias_are_handled(db):
    routing = {"provider_only": ["openai/flex"], "service_tier": "flex"}
    reasoning = {"policy": "disabled", "effort": None}
    request = {
        "model": "m",
        "provider": {
            "only": ["openai/flex"],
            "allow_fallbacks": False,
            "require_parameters": True,
        },
        "service_tier": "flex",
        "max_completion_tokens": 1024,
        "reasoning": {"enabled": False},
    }
    sample = {
        "output": {"response_id": "final"},
        "metadata": {
            "openrouter_http_calls": [
                {
                    "request_body": {"json": request},
                    "response_body": {"json": {"id": "bad", "error": {"code": 502}}},
                    "http_status": 200,
                },
                {
                    "request_body": {"json": request},
                    "response_body": {
                        "json": {
                            "id": "final",
                            "usage": {
                                "cost": 0,
                                "completion_tokens_details": {"reasoning_tokens": 0},
                            },
                        }
                    },
                    "http_status": 200,
                },
            ]
        },
    }
    capture_sample(db, "corpus", "m", "u", sample, routing, reasoning, "ref")
    assert db.execute("SELECT SUM(failed) FROM attempts").fetchone()[0] == 1
    assert db.execute("SELECT request_faults FROM conditions").fetchone()[0] == "[]"
    assert db.execute(
        "SELECT reasoning_reported,reasoning_nonzero FROM conditions"
    ).fetchone()[:] == (1, 0)
    assert (
        db.execute("SELECT cost FROM generations WHERE id='bad'").fetchone()[0] is None
    )
    assert (
        db.execute("SELECT cost FROM generations WHERE id='final'").fetchone()[0] == 0
    )


def test_report_refuses_existing_output_without_modification(tmp_path):
    out = tmp_path / "output"
    out.mkdir()
    marker = out / "keep"
    marker.write_text("unchanged")
    with pytest.raises(ValueError, match="already exists"):
        report(tmp_path, tmp_path / "run", out)
    assert marker.read_text() == "unchanged"


def test_report_refuses_incomplete_run_before_creating_output(tmp_path):
    run = tmp_path / "run"
    folder = run / "corpus/summary"
    folder.mkdir(parents=True)
    (folder / "closure.json").write_text('{"complete": false}')
    with pytest.raises(ValueError, match="incomplete"):
        report(tmp_path, run, tmp_path / "new")
    assert not (tmp_path / "new").exists()


def test_response_markup_is_escaped():
    rendered = literal('<script>alert("x")</script><img src=x onerror=alert(1)>')
    assert "<script>" not in rendered and "<img" not in rendered
    assert "&lt;script&gt;" in rendered
