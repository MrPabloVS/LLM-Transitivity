"""Verify saved report data and derive descriptive cross-condition results."""

import csv
import hashlib
import json
import math
from pathlib import Path

RUN_ID = "2026-11-06_01-23-40-040fd7b7"
VERSION = "interpretation-v1"
COUNTS = """
 count(*) AS samples,
 count(*) FILTER (WHERE matched = 1) AS matched,
 count(*) FILTER (WHERE matched = 0 AND status = 'answered') AS disagreed,
 count(*) FILTER (WHERE status = 'answered') AS answered,
 count(*) FILTER (WHERE strict = 1) AS strict,
 count(*) FILTER (WHERE status = 'content_filter') AS content_filter,
 count(*) FILTER (WHERE status = 'empty') AS empty,
 count(*) FILTER (WHERE status = 'ambiguous') AS ambiguous,
 count(*) FILTER (WHERE status = 'invalid_format') AS invalid_format,
 count(*) FILTER (WHERE status = 'error') AS error,
 count(*) FILTER (WHERE status = 'answered' AND strict = 0) AS nonstrict_answered,
 count(*) FILTER (WHERE answer = 'yes' AND status = 'answered') AS yes,
 count(*) FILTER (WHERE answer = 'no' AND status = 'answered') AS no
"""
CROSSES = {
    "totals": [],
    "family": ["family"],
    "order_label": ["family", "canonical", "validity"],
    "formulation": ["family", "formulation", "canonical", "validity"],
    "lexical": ["family", "frequency"],
    "tense": ["family", "tense"],
    "stratum": [
        "dataset",
        "stratum",
        "family",
        "canonical",
        "validity",
        "formulation",
        "frequency",
        "tense",
    ],
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def rows(connection, sql):
    result = connection.execute(sql)
    keys = [d[0] for d in result.description]
    return [dict(zip(keys, row, strict=True)) for row in result.fetchall()]


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def aggregate(connection, dimensions):
    columns = ", ".join(["model", *dimensions])
    result = rows(
        connection,
        f"SELECT {columns}, {COUNTS} FROM results GROUP BY {columns} ORDER BY {columns}",
    )
    for row in result:
        for key, numerator, denominator in (
            ("agreement", "matched", "answered"),
            ("coverage", "answered", "samples"),
            ("format_rate", "strict", "samples"),
            ("matched_total", "matched", "samples"),
        ):
            row[key] = ratio(row[numerator], row[denominator])
    return result


def validate_keys(
    connection, models, case_count=54000, stratum_count=108, stratum_size=500
):
    require(
        connection.execute("SELECT count(*), count(DISTINCT uid) FROM cases").fetchone()
        == (case_count, case_count),
        "Case UID count or uniqueness mismatch",
    )
    require(
        connection.execute("SELECT count(*) FROM results").fetchone()[0]
        == case_count * len(models),
        "Response count mismatch",
    )
    require(
        not rows(
            connection,
            "SELECT uid, model FROM results GROUP BY ALL HAVING count(*) != 1",
        ),
        "Duplicate response keys",
    )
    actual = rows(
        connection,
        "SELECT model, count(*) AS n, count(DISTINCT uid) AS u FROM results GROUP BY model",
    )
    require({r["model"] for r in actual} == set(models), "Model set mismatch")
    require(
        all(r["n"] == r["u"] == case_count for r in actual), "Incomplete model coverage"
    )
    strata = rows(
        connection, "SELECT stratum, count(*) AS n FROM cases GROUP BY stratum"
    )
    require(
        len(strata) == stratum_count and all(r["n"] == stratum_size for r in strata),
        "Stratum counts mismatch",
    )


def paired(connection):
    return rows(
        connection,
        """
        SELECT a.model AS model_a, b.model AS model_b, count(*) AS paired_cases,
          count(*) FILTER (WHERE a.status='answered' AND b.status='answered') AS both_interpreted,
          count(*) FILTER (WHERE a.status='answered' AND b.status='answered' AND a.answer=b.answer) AS same_answer,
          count(*) FILTER (WHERE a.status='answered' AND b.status='answered' AND a.matched=1 AND b.matched=1) AS both_match,
          count(*) FILTER (WHERE a.status='answered' AND b.status='answered' AND a.matched=0 AND b.matched=0) AS both_disagree,
          count(*) FILTER (WHERE a.status='answered' AND b.status='answered' AND a.matched=1 AND b.matched=0) AS a_only_match,
          count(*) FILTER (WHERE a.status='answered' AND b.status='answered' AND a.matched=0 AND b.matched=1) AS b_only_match
        FROM results a JOIN results b ON a.uid=b.uid AND a.model<b.model
        GROUP BY a.model,b.model ORDER BY a.model,b.model
    """,
    )


def compare_counts(actual, expected, keys, fields):
    a = {tuple(r[k] for k in keys): r for r in actual}
    e = {tuple(r[k] for k in keys): r for r in expected}
    require(
        len(a) == len(actual) and len(e) == len(expected), "Duplicate aggregate keys"
    )
    require(a.keys() == e.keys(), f"Aggregate keys differ: {keys}")
    for key in a:
        for field in fields:
            x, y = a[key][field], e[key][field]
            require(
                x == y
                or (
                    x is not None
                    and y is not None
                    and math.isclose(float(x), float(y), abs_tol=1e-10)
                ),
                f"Aggregate mismatch: {key} / {field}",
            )


def examples(connection):
    output, used = [], set()
    for family in ("HS", "mHS"):
        for category, predicate in (
            (
                "different answers",
                "count(DISTINCT answer) FILTER (WHERE status='answered') > 1",
            ),
            ("content filter", "count(*) FILTER (WHERE status='content_filter') > 0"),
            (
                "interpretable outside strict format",
                "count(*) FILTER (WHERE status='answered' AND strict=0) > 0",
            ),
        ):
            candidates = rows(
                connection,
                f"SELECT uid FROM results WHERE family='{family}' GROUP BY uid HAVING {predicate} ORDER BY sha256(uid), uid",
            )
            uid = next((r["uid"] for r in candidates if r["uid"] not in used), None)
            if uid is None:
                output.append({"family": family, "category": category, "case": None})
                continue
            used.add(uid)
            case = rows(
                connection, f"SELECT * EXCLUDE (responses) FROM cases WHERE uid='{uid}'"
            )[0]
            answers = rows(
                connection,
                f"SELECT model,raw,status,answer,matched,strict FROM results WHERE uid='{uid}' ORDER BY model",
            )
            output.append(
                {
                    "family": family,
                    "category": category,
                    "case": case,
                    "answers": answers,
                }
            )
    return output


def prepare(source: Path, connection):
    validation = json.loads((source / "validation.json").read_text())
    require(
        all(
            validation.get(k) is True
            for k in (
                "complete",
                "native_metrics_reconciled",
                "source_text_and_hashes_verified",
                "protected_inputs_unchanged",
            )
        ),
        "Source report is not fully validated",
    )
    summary = json.loads((source / "summary.json").read_text())
    require(
        summary["run_id"] == RUN_ID,
        "This interpretation is defined for the completed November 6 run",
    )
    require(
        summary["configuration"]["scoring_version"] == "source-label-deterministic-v3",
        "Unexpected scorer",
    )
    source_literal = str(source).replace("'", "''")
    connection.execute(
        f"CREATE TABLE cases AS SELECT * FROM read_json_auto('{source_literal}/data/*.json', union_by_name=true)"
    )
    connection.execute(
        f"CREATE TABLE saved_responses AS SELECT * FROM read_csv_auto('{source_literal}/tables/responses.csv', sample_size=-1, types={{'answer': 'VARCHAR', 'raw': 'VARCHAR'}})"
    )
    connection.execute("""CREATE TABLE results AS SELECT r.*, c.* EXCLUDE(uid, responses)
        FROM saved_responses r JOIN cases c USING(uid) WHERE phase='corpus'""")
    validate_keys(connection, summary["models"])
    require(
        connection.execute(
            "SELECT count(*) FROM cases WHERE sha256(prompt) != sentence_hash OR target NOT IN ('yes','no') OR target != CASE WHEN validity='valid' THEN 'yes' WHEN validity='invalid' THEN 'no' END"
        ).fetchone()[0]
        == 0,
        "Text hashes or targets differ",
    )
    fields = [
        "phase",
        "model",
        "uid",
        "raw",
        "status",
        "answer",
        "matched",
        "strict",
        "log",
        "log_hash",
        "generation_id",
        "input_tokens",
        "output_tokens",
        "reasoning_tokens",
        "started",
        "ended",
        "duration",
    ]
    nested = ",".join("r." + f for f in fields)
    flat = ",".join(fields)
    connection.execute(
        f"CREATE VIEW json_responses AS SELECT {nested} FROM cases, unnest(responses) AS u(r)"
    )
    for a, b in (("json_responses", "results"), ("results", "json_responses")):
        require(
            connection.execute(
                f"SELECT count(*) FROM (SELECT {flat} FROM {a} EXCEPT ALL SELECT {flat} FROM {b})"
            ).fetchone()[0]
            == 0,
            "JSON/CSV response mismatch",
        )
    require(
        connection.execute(
            "SELECT count(*) FROM saved_responses WHERE phase='corpus'"
        ).fetchone()[0]
        == 324000,
        "Extra corpus responses",
    )
    require(
        connection.execute(
            "SELECT count(*) FROM saved_responses WHERE phase='preflight'"
        ).fetchone()[0]
        == 6,
        "Preflight count mismatch",
    )
    require(
        connection.execute(
            "SELECT count(DISTINCT (model,dataset)) FROM results"
        ).fetchone()[0]
        == 108,
        "Task count mismatch",
    )
    tables = {name: aggregate(connection, dims) for name, dims in CROSSES.items()}
    fields = [
        "samples",
        "matched",
        "disagreed",
        "strict",
        "answered",
        "content_filter",
        "empty",
        "ambiguous",
        "invalid_format",
        "error",
        "agreement",
        "coverage",
        "format_rate",
        "matched_total",
    ]
    compare_counts(tables["totals"], summary["totals"], ["model"], fields)
    expected = [
        dict(r, stratum=r["condition"]) for r in summary["breakdowns"]["stratum"]
    ]
    compare_counts(tables["stratum"], expected, ["model", "stratum"], fields)
    for group in tables.values():
        for model in summary["models"]:
            require(
                sum(r["samples"] for r in group if r["model"] == model) == 54000,
                "Cross-condition totals differ",
            )
    tables["pairs"] = paired(connection)
    require(len(tables["pairs"]) == 15, "Expected 15 model pairs")
    expected_pairs = []
    for r in summary["pairwise"]:
        r = dict(r)
        if r["model_a"] > r["model_b"]:
            r["model_a"], r["model_b"] = r["model_b"], r["model_a"]
            r["a_only_match"], r["b_only_match"] = r["b_only_match"], r["a_only_match"]
        expected_pairs.append(r)
    compare_counts(
        tables["pairs"],
        expected_pairs,
        ["model_a", "model_b"],
        [k for k in tables["pairs"][0] if k not in ("model_a", "model_b")],
    )
    tables["concentration"] = rows(
        connection,
        """SELECT disagrees, count(*) AS cases FROM (
        SELECT uid, count(*) FILTER (WHERE status='answered' AND matched=0) AS disagrees
        FROM results GROUP BY uid) GROUP BY disagrees ORDER BY disagrees""",
    )
    tables["answer_bias"] = aggregate(connection, ["family", "validity"])
    tables["design"] = rows(
        connection,
        "SELECT dataset, family, frequency, tense, formulation, canonical, validity, stratum, count(*) AS cases FROM cases GROUP BY ALL ORDER BY dataset,stratum",
    )
    compare_counts(
        tables["design"],
        summary["stratum_definitions"],
        [
            "dataset",
            "stratum",
            "family",
            "frequency",
            "tense",
            "formulation",
            "validity",
            "canonical",
        ],
        ["cases"],
    )
    require(
        sum(r["cases"] for r in tables["concentration"]) == 54000,
        "Concentration totals differ",
    )
    require(
        sum(r["cases"] * r["disagrees"] for r in tables["concentration"])
        == sum(r["disagreed"] for r in tables["totals"]),
        "Concentration disagreements differ",
    )
    for name in ("costs", "latencies", "tokens", "attempts"):
        tables[name] = rows(
            connection,
            f"SELECT * FROM read_csv_auto('{source_literal}/tables/{name}.csv', sample_size=-1)",
        )
    # The source ledger already deduplicates generation IDs; validate before reuse.
    ledger = rows(
        connection,
        f"SELECT count(*) AS ids, count(DISTINCT id) AS unique_ids, count(cost) AS known_ids, sum(cost) AS known_usd FROM read_csv_auto('{source_literal}/tables/generations.csv', sample_size=-1)",
    )[0]
    require(
        ledger["ids"] == ledger["unique_ids"] == summary["ledger"]["ids"],
        "Generation ledger duplicates or count mismatch",
    )
    require(
        ledger["known_ids"] == summary["ledger"]["known_ids"]
        and math.isclose(
            ledger["known_usd"], summary["ledger"]["known_usd"], abs_tol=1e-8
        ),
        "Generation costs differ",
    )
    require(
        math.isclose(
            sum(r["known_usd"] or 0 for r in tables["costs"]),
            ledger["known_usd"],
            abs_tol=1e-8,
        ),
        "Cost roles do not reconcile",
    )
    require(
        sum(r["unknown_cost_ids"] for r in tables["costs"])
        == summary["ledger"]["unknown_ids"],
        "Unknown cost count differs",
    )
    return {"source": summary, "tables": tables, "examples": examples(connection)}


def write_tables(output, tables):
    output.mkdir()
    for name, records in tables.items():
        with (output / f"{name}.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
