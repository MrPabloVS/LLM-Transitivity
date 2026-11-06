"""Compose corrected results without editing either native execution."""

import json
from pathlib import Path

from llm_transitivity.analysis.full_store import (
    file_hash,
    ingest_phase,
    read_json,
    require,
    timestamp,
)
from llm_transitivity.analysis.full_summary import aggregate, query
from llm_transitivity.datasets.correction import CORRECTION_ID, MANIFEST, SOURCE_RUN
from llm_transitivity.evidence.serialization import digest


def validate_correction(root, directory, provenance):
    manifest = read_json(directory / "correction_manifest.json")
    require(
        manifest["id"] == CORRECTION_ID and manifest["source_run"] == SOURCE_RUN,
        "Unexpected correction source",
    )
    require(
        read_json(directory / "worker.json")["status"] == "complete",
        "Correction is not complete",
    )
    events = [
        json.loads(line)
        for line in (directory / "events.jsonl").read_text().splitlines()
    ]
    indexes = {}
    for stage in manifest["stages"]:
        event = next(
            e
            for e in reversed(events)
            if e.get("stage") == stage["name"] and e.get("status") == "passed"
        )
        closure = directory / event["review"]
        require(
            file_hash(closure) == event["review_sha256"],
            "Correction closure hash differs",
        )
        review = read_json(closure)
        require(review["technical_pass"], "Correction technical check failed")
        selected_index = directory / review["selected_log_index"]
        require(
            file_hash(selected_index) == review["selected_log_index_sha256"],
            "Selected log index changed",
        )
        indexes[stage["name"]] = selected_index
        provenance[str(selected_index.relative_to(root))] = file_hash(selected_index)
        count = 1 if stage["name"] == "preflight" else 612
        require(
            len(review["models"]) == 6
            and all(
                r["samples"] == count and not r["faults"]
                for r in review["models"].values()
            ),
            "Incomplete replacement coverage",
        )
        spec = directory / stage["spec"]
        require(file_hash(spec) == stage["spec_sha256"], "Correction spec hash differs")
        hashes = spec.parent / "snapshot_hashes.json"
        for rel, expected in read_json(hashes).items():
            path = spec.parent / "snapshot" / rel
            require(file_hash(path) == expected, "Correction snapshot hash differs")
            provenance[str(path.relative_to(root))] = expected
        for path in (closure, spec, hashes):
            provenance[str(path.relative_to(root))] = file_hash(path)
    for path in (
        directory / "correction_manifest.json",
        directory / "events.jsonl",
        directory / "worker.json",
    ):
        provenance[str(path.relative_to(root))] = file_hash(path)
    amendment = directory / "corpus/provenance/snapshot" / MANIFEST
    require(
        file_hash(amendment) == manifest["correction_manifest_sha256"],
        "Correction amendment hash differs",
    )
    require(
        read_json(amendment) == read_json(root / MANIFEST),
        "Correction differs from approved manifest",
    )
    original = read_json(root / SOURCE_RUN / "corpus/provenance/flow_spec.json")
    frozen_models = {
        (t["model"]["name"], t["args"]["dataset"]): t["model"]
        for t in original["tasks"]
    }
    for stage in manifest["stages"]:
        for task in read_json(directory / stage["spec"])["tasks"]:
            require(
                task["model"]
                == frozen_models[(task["model"]["name"], task["args"]["dataset"])],
                "Replacement model configuration differs",
            )
    return read_json(amendment), indexes


def scoped_costs(db, label, where, args=()):
    return [
        {"scope": label, **r}
        for r in query(
            db,
            f"""SELECT l.model,COUNT(DISTINCT g.id) generation_ids,
        COUNT(DISTINCT CASE WHEN g.cost IS NULL THEN g.id END) unknown_cost_ids,
        SUM(g.cost) known_usd FROM generations g JOIN
        (SELECT DISTINCT model,generation_id FROM generation_links WHERE {where}) l
        ON l.generation_id=g.id GROUP BY l.model""",
            args,
        )
    ]


def apply_correction(db, root: Path, directory: Path, config, system, provenance):
    amendment, indexes = validate_correction(root, directory, provenance)
    cases = amendment["cases"]
    require(
        len(cases) == 612 and len({r["original_uid"] for r in cases}) == 612,
        "Invalid replacement identities",
    )
    db.execute(
        "CREATE TABLE replacements (model TEXT, original_uid TEXT, corrected_uid TEXT, before_json TEXT, after_json TEXT, PRIMARY KEY(model,original_uid))"
    )
    db.execute("CREATE TEMP TABLE affected(uid TEXT PRIMARY KEY)")
    db.executemany(
        "INSERT INTO affected VALUES (?)", [(r["original_uid"],) for r in cases]
    )
    before = aggregate(db)
    costs = scoped_costs(
        db,
        "retained_original_corpus",
        "phase='corpus' AND uid NOT IN (SELECT uid FROM affected)",
    )
    costs += scoped_costs(
        db,
        "superseded_original_corpus",
        "phase='corpus' AND uid IN (SELECT uid FROM affected)",
    )
    costs += scoped_costs(db, "original_preflight", "phase='preflight'")
    unchanged = [
        tuple(r)
        for r in db.execute(
            "SELECT * FROM results WHERE phase='corpus' AND uid NOT IN (SELECT uid FROM affected) ORDER BY model,uid"
        )
    ]
    for change in cases:
        old = db.execute(
            "SELECT * FROM cases WHERE uid=?", (change["original_uid"],)
        ).fetchone()
        require(
            old is not None
            and old["prompt"] == change["original_text"]
            and old["sentence_hash"] == change["original_sentence_sha256"],
            "Correction source case mismatch",
        )
        require(
            change["corrected_text"] == old["prompt"].replace("eate", "ate"),
            "Unexpected replacement text",
        )
        rows = query(
            db,
            "SELECT * FROM results WHERE phase='corpus' AND uid=?",
            (change["original_uid"],),
        )
        require(
            len(rows) == 6
            and {r["model"] for r in rows} == set(config["requested_routing"]),
            "Replacement model set differs",
        )
        for row in rows:
            db.execute(
                "INSERT INTO replacements VALUES (?,?,?,?,NULL)",
                (
                    row["model"],
                    change["original_uid"],
                    change["corrected_uid"],
                    json.dumps(row, ensure_ascii=False),
                ),
            )
        for table in ("results", "generation_links", "attempts", "conditions"):
            db.execute(
                f"DELETE FROM {table} WHERE phase='corpus' AND uid=?",
                (change["original_uid"],),
            )
        require(
            db.execute(
                "SELECT count(*) FROM results WHERE uid=?", (change["original_uid"],)
            ).fetchone()[0]
            == 0,
            "An affected case is used by another phase",
        )
        db.execute(
            "UPDATE cases SET uid=?,prompt=?,sentence_hash=?,working_hash=?,uid_hash=? WHERE uid=?",
            (
                change["corrected_uid"],
                change["corrected_text"],
                change["sentence_sha256"],
                change["working_record_sha256"],
                digest(change["corrected_uid"].encode()),
                change["original_uid"],
            ),
        )
    replacement_tasks = ingest_phase(
        db, root, directory, "corpus", system, config, provenance, indexes["corpus"]
    )
    for row in query(db, "SELECT * FROM replacements"):
        result = db.execute(
            "SELECT * FROM results WHERE phase='corpus' AND model=? AND uid=?",
            (row["model"], row["corrected_uid"]),
        ).fetchone()
        require(result is not None, "Replacement response is missing")
        db.execute(
            "UPDATE replacements SET after_json=? WHERE model=? AND original_uid=?",
            (
                json.dumps(dict(result), ensure_ascii=False),
                row["model"],
                row["original_uid"],
            ),
        )
    changed = [r["corrected_uid"] for r in cases]
    db.execute("DELETE FROM affected")
    db.executemany("INSERT INTO affected VALUES (?)", [(uid,) for uid in changed])
    actual = [
        tuple(r)
        for r in db.execute(
            "SELECT * FROM results WHERE phase='corpus' AND uid NOT IN (SELECT uid FROM affected) ORDER BY model,uid"
        )
    ]
    require(actual == unchanged and len(actual) == 320328, "Unaffected results changed")
    costs += scoped_costs(
        db, "replacement_corpus", "phase='corpus' AND uid IN (SELECT uid FROM affected)"
    )
    ingest_phase(
        db,
        root,
        directory,
        "preflight",
        system,
        config,
        provenance,
        indexes["preflight"],
    )
    for table in ("results", "generation_links", "attempts", "conditions"):
        db.execute(
            f"UPDATE {table} SET phase='correction_preflight' WHERE phase='preflight' AND uid IN (SELECT uid FROM affected)"
        )
    costs += scoped_costs(db, "correction_preflight", "phase='correction_preflight'")
    changes = query(
        db,
        """SELECT model,COUNT(*) samples,
        SUM(json_extract(before_json,'$.answer') IS NOT json_extract(after_json,'$.answer')) changed_answers,
        SUM(json_extract(before_json,'$.matched')) before_matched,SUM(json_extract(after_json,'$.matched')) after_matched,
        SUM(json_extract(before_json,'$.strict')) before_strict,SUM(json_extract(after_json,'$.strict')) after_strict,
        SUM(json_extract(before_json,'$.status')='answered') before_answered,SUM(json_extract(after_json,'$.status')='answered') after_answered,
        SUM(json_extract(before_json,'$.status')='content_filter') before_filtered,SUM(json_extract(after_json,'$.status')='content_filter') after_filtered,
        SUM(json_extract(before_json,'$.answer')='yes' AND c.target='no') before_fp,SUM(json_extract(after_json,'$.answer')='yes' AND c.target='no') after_fp,
        SUM(json_extract(before_json,'$.answer')='no' AND c.target='yes') before_fn,SUM(json_extract(after_json,'$.answer')='no' AND c.target='yes') after_fn
        FROM replacements JOIN cases c ON c.uid=corrected_uid GROUP BY model""",
    )
    events = [
        json.loads(line)
        for line in (directory / "events.jsonl").read_text().splitlines()
    ]
    start = timestamp(
        next(
            e["at_utc"]
            for e in events
            if e.get("stage") == "corpus" and e.get("status") == "started"
        )
    )
    end = timestamp(
        next(
            e["at_utc"]
            for e in reversed(events)
            if e.get("stage") == "corpus" and e.get("status") == "passed"
        )
    )
    db.commit()
    return {
        "id": CORRECTION_ID,
        "source_run": SOURCE_RUN,
        "replacement_run": str(directory.relative_to(root)),
        "cases": 612,
        "responses": 3672,
        "retained_responses": 320328,
        "before_totals": before,
        "changes": changes,
        "costs": costs,
        "replacement_tasks": replacement_tasks,
        "replacement_seconds": end - start,
    }
