"""Calculate full-corpus tables from verified, compact SQLite records."""

import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path

from llm_transitivity.analysis.calculations import percentile90
from llm_transitivity.analysis.full_store import STATUSES, require, timestamp

DIMENSIONS = {
    "family": "family",
    "frequency": "frequency",
    "tense": "tense",
    "canonical": "canonical",
    "validity": "validity",
    "formulation": "formulation",
    "dataset": "dataset",
    "stratum": "stratum",
}


def query(db, sql, args=()):
    return [dict(r) for r in db.execute(sql, args)]


def aggregate(db, dimension=None) -> list[dict]:
    group = f",c.{DIMENSIONS[dimension]} AS condition" if dimension else ""
    by = f",c.{DIMENSIONS[dimension]}" if dimension else ""
    rows = query(
        db,
        f"""SELECT r.model{group},COUNT(*) AS samples,
        SUM(r.matched) AS matched,
        SUM(r.status='answered' AND NOT r.matched) AS disagreed,
        SUM(r.strict) AS strict,
        {",".join(f"SUM(r.status='{s}') AS {s}" for s in STATUSES)}
        FROM results r JOIN cases c USING(uid) WHERE r.phase='corpus'
        GROUP BY r.model{by} ORDER BY r.model{by}""",
    )
    for r in rows:
        require(
            sum(r[s] for s in STATUSES) == r["samples"], "Outcome categories do not sum"
        )
        require(
            r["matched"] + r["disagreed"] == r["answered"],
            "Agreement counts do not sum",
        )
        r.update(
            agreement=r["matched"] / r["answered"] if r["answered"] else None,
            coverage=r["answered"] / r["samples"] if r["samples"] else None,
            format_rate=r["strict"] / r["samples"] if r["samples"] else None,
            matched_total=r["matched"] / r["samples"] if r["samples"] else None,
        )
    return rows


def pairwise(db, models):
    rows = []
    for a, b in itertools.combinations(models, 2):
        r = dict(
            db.execute(
                """SELECT COUNT(*) paired_cases,
          SUM(a.status='answered' AND b.status='answered') both_interpreted,
          SUM(a.status='answered' AND b.status='answered' AND a.answer=b.answer) same_answer,
          SUM(a.status='answered' AND b.status='answered' AND a.matched AND b.matched) both_match,
          SUM(a.status='answered' AND b.status='answered' AND NOT a.matched AND NOT b.matched) both_disagree,
          SUM(a.status='answered' AND b.status='answered' AND a.matched AND NOT b.matched) a_only_match,
          SUM(a.status='answered' AND b.status='answered' AND b.matched AND NOT a.matched) b_only_match
          FROM results a JOIN results b ON a.uid=b.uid
          WHERE a.phase='corpus' AND b.phase='corpus' AND a.model=? AND b.model=?""",
                (a, b),
            ).fetchone()
        )
        r.update(model_a=a, model_b=b)
        r["not_both_interpreted"] = r["paired_cases"] - r["both_interpreted"]
        r["answer_agreement"] = (
            r["same_answer"] / r["both_interpreted"] if r["both_interpreted"] else None
        )
        require(
            r["both_match"] + r["both_disagree"] + r["a_only_match"] + r["b_only_match"]
            == r["both_interpreted"],
            "Pairwise cells do not sum",
        )
        rows.append(r)
    return rows


def cost_rows(db):
    return query(
        db,
        """WITH linked AS (
      SELECT l.phase,l.model,l.generation_id,MAX(l.final) final,
        MAX(r.generation_id IS NULL) unresolved
      FROM generation_links l JOIN results r ON r.phase=l.phase AND r.model=l.model AND r.uid=l.uid
      GROUP BY l.phase,l.model,l.generation_id
    ) SELECT l.phase,l.model,
      CASE WHEN final THEN 'final' WHEN unresolved THEN 'unresolved' ELSE 'additional' END kind,
      COUNT(*) generations,COUNT(g.cost) known_cost_ids,
      SUM(g.cost IS NULL) unknown_cost_ids,SUM(g.cost) known_usd
      FROM linked l JOIN generations g ON g.id=l.generation_id GROUP BY l.phase,l.model,kind
      ORDER BY l.phase,l.model,kind""",
    )


def peaks(db, table):
    require(table in {"results", "attempts"}, "Unexpected interval table")
    current = defaultdict(int)
    peak = defaultdict(int)
    global_current = global_peak = 0
    for (
        model,
        _,
        delta,
    ) in db.execute(f"""SELECT model,started AS at,1 AS delta FROM {table}
      WHERE phase='corpus' AND started IS NOT NULL AND ended>started
      UNION ALL SELECT model,ended AS at,-1 AS delta FROM {table}
      WHERE phase='corpus' AND started IS NOT NULL AND ended>started ORDER BY at,delta"""):
        current[model] += delta
        global_current += delta
        peak[model] = max(peak[model], current[model])
        global_peak = max(global_peak, global_current)
    return {"global": global_peak, "models": dict(peak)}


def example_cases(db):
    conditions = {
        "different answers": "COUNT(DISTINCT CASE WHEN r.status='answered' THEN r.answer END)>1",
        "content filter": "SUM(r.status='content_filter')>0",
        "interpretable, non-strict format": "SUM(r.status='answered' AND NOT r.strict)>0",
    }
    selected, used = [], set()
    for family in ("HS", "mHS"):
        for category, having in conditions.items():
            candidates = db.execute(
                f"""SELECT c.uid FROM cases c JOIN results r USING(uid)
              WHERE c.family=? AND r.phase='corpus' GROUP BY c.uid HAVING {having}
              ORDER BY c.uid_hash,c.uid""",
                (family,),
            )
            uid = next((r[0] for r in candidates if r[0] not in used), None)
            if uid:
                used.add(uid)
            selected.append({"family": family, "category": category, "uid": uid})
    return selected


def build_summary(db, run: Path, config: dict, tasks: list[dict]) -> dict:
    models = list(config["requested_routing"])
    totals = aggregate(db)
    require(
        len(totals) == 6 and all(r["samples"] == 54000 for r in totals),
        "Expected 54000 results per model",
    )
    require(
        db.execute("SELECT COUNT(*) FROM results WHERE phase='preflight'").fetchone()[0]
        == 6,
        "Expected six preflight samples",
    )
    strata = aggregate(db, "stratum")
    require(
        len(strata) == 648 and all(r["samples"] == 500 for r in strata),
        "Expected 648 model-stratum cells of 500",
    )
    breakdowns = {k: aggregate(db, k) for k in DIMENSIONS}
    for dimension, rows in breakdowns.items():
        for total in totals:
            parts = [r for r in rows if r["model"] == total["model"]]
            require(
                all(
                    sum(r[k] for r in parts) == total[k]
                    for k in ("samples", "matched", "strict", *STATUSES)
                ),
                f"Breakdown does not reconcile: {dimension}",
            )
    events = [json.loads(l) for l in (run / "events.jsonl").read_text().splitlines()]
    start = timestamp(
        next(
            e["at_utc"]
            for e in events
            if e["stage"] == "corpus" and e["status"] == "started"
        )
    )
    closed = timestamp(
        next(
            e["at_utc"]
            for e in events
            if e["stage"] == "corpus" and e["status"] == "passed"
        )
    )
    corpus_tasks = [t for t in tasks if t["phase"] == "corpus"]
    first = min(t["started"] for t in corpus_tasks)
    last = max(t["ended"] for t in corpus_tasks)
    history = {
        json.dumps(v, sort_keys=True): v
        for t in corpus_tasks
        for v in t["adaptive_history"]
    }
    attempts = query(
        db,
        """SELECT phase,model,COUNT(*) attempts,SUM(failed) failed_attempts,
      SUM(generation_id IS NULL) attempts_without_id,
      SUM(ended IS NULL) attempts_without_end FROM attempts GROUP BY phase,model""",
    )
    tokens = query(
        db,
        """SELECT phase,model,COUNT(*) samples,
      SUM(input_tokens) input_tokens,SUM(output_tokens) output_tokens,SUM(reasoning_tokens) reasoning_tokens,
      SUM(input_tokens IS NULL) unknown_input,SUM(output_tokens IS NULL) unknown_output,
      SUM(reasoning_tokens IS NULL) unknown_reasoning FROM results GROUP BY phase,model""",
    )
    latencies = []
    for model in models:
        r = {"model": model}
        for table, column in (("results", "duration"), ("attempts", "seconds")):
            values = [
                row[0]
                for row in db.execute(
                    f"SELECT {column} FROM {table} WHERE phase='corpus' AND model=? AND {column} IS NOT NULL ORDER BY {column}",
                    (model,),
                )
            ]
            r[f"{table}_observed"] = len(values)
            r[f"{table}_mean_seconds"] = sum(values) / len(values) if values else None
            r[f"{table}_p90_seconds"] = percentile90(values) if values else None
        latencies.append(r)
    return {
        "run_id": run.name,
        "models": models,
        "configuration": config,
        "cases": query(
            db,
            "SELECT dataset,family,frequency,tense,COUNT(*) cases,COUNT(DISTINCT stratum) strata FROM cases GROUP BY dataset ORDER BY dataset",
        ),
        "stratum_definitions": query(
            db,
            "SELECT dataset,stratum,family,frequency,tense,formulation,validity,canonical,COUNT(*) cases FROM cases GROUP BY dataset,stratum ORDER BY dataset,stratum",
        ),
        "totals": totals,
        "breakdowns": breakdowns,
        "pairwise": pairwise(db, models),
        "examples": example_cases(db),
        "costs": cost_rows(db),
        "answer_distribution": query(
            db,
            "SELECT model,answer,COUNT(*) samples FROM results WHERE phase='corpus' AND status='answered' GROUP BY model,answer",
        ),
        "confusion": query(
            db,
            "SELECT r.model,c.target,r.answer,COUNT(*) samples FROM results r JOIN cases c USING(uid) WHERE phase='corpus' AND status='answered' GROUP BY r.model,c.target,r.answer",
        ),
        "ledger": dict(
            db.execute(
                "SELECT COUNT(*) ids,COUNT(cost) known_ids,SUM(cost) known_usd,SUM(cost IS NULL) unknown_ids FROM generations"
            ).fetchone()
        ),
        "cost_conflicts": db.execute("SELECT COUNT(*) FROM cost_conflicts").fetchone()[
            0
        ],
        "attempts": attempts,
        "tokens": tokens,
        "latencies": latencies,
        "sample_concurrency": peaks(db, "results"),
        "http_concurrency": peaks(db, "attempts"),
        "conditions": query(
            db,
            """SELECT phase,model,COUNT(*) samples,SUM(request_count=0) missing_requests,
          SUM(request_faults!='[]') samples_with_faults,SUM(reasoning_reported) reasoning_observed,
          SUM(reasoning_nonzero) nonzero_reasoning FROM conditions GROUP BY phase,model""",
        ),
        "reported_routes": query(
            db,
            "SELECT phase,model,reported_providers,reported_tiers,COUNT(*) samples FROM conditions GROUP BY phase,model,reported_providers,reported_tiers",
        ),
        "adaptive_history": sorted(
            history.values(), key=lambda v: (v["timestamp"], v["model"])
        ),
        "timing": {
            "corpus_started": start,
            "first_task_started": first,
            "last_task_completed": last,
            "corpus_closed": closed,
            "startup_seconds": first - start,
            "evaluation_seconds": last - first,
            "finalization_seconds": closed - last,
            "total_seconds": closed - start,
        },
    }


def write_json(path: Path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    )


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def export_tables(db, output: Path, summary: dict):
    tables = output / "tables"
    tables.mkdir()
    for key in (
        "totals",
        "cases",
        "stratum_definitions",
        "pairwise",
        "costs",
        "attempts",
        "tokens",
        "latencies",
        "conditions",
        "reported_routes",
        "adaptive_history",
        "answer_distribution",
        "confusion",
    ):
        write_csv(tables / f"{key}.csv", summary[key])
    for dimension, rows in summary["breakdowns"].items():
        write_csv(tables / f"by_{dimension}.csv", rows)
    for table in ("generations", "cost_conflicts"):
        write_csv(tables / f"{table}.csv", query(db, f"SELECT * FROM {table}"))
    data = output / "data"
    data.mkdir()
    for dataset in summary["cases"]:
        cases = query(
            db,
            "SELECT * FROM cases WHERE dataset=? ORDER BY row_number",
            (dataset["dataset"],),
        )
        by_uid = {case["uid"]: case for case in cases}
        for case in cases:
            case["source_id"] = json.loads(case["source_id"])
            case["responses"] = []
        for row in db.execute(
            """SELECT r.* FROM results r JOIN cases c USING(uid)
          WHERE phase='corpus' AND c.dataset=? ORDER BY r.uid,r.model""",
            (dataset["dataset"],),
        ):
            by_uid[row["uid"]]["responses"].append(dict(row))
        write_json(data / f"{dataset['dataset']}.json", cases)
    # CSV streams from SQLite; no event payload is duplicated here.
    cursor = db.execute("SELECT * FROM results ORDER BY phase,model,uid")
    with (tables / "responses.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow([v[0] for v in cursor.description])
        writer.writerows(cursor)
    write_json(output / "summary.json", summary)
