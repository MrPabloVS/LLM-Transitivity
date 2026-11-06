"""Read closed native logs into a compact, source-verified report database."""

import hashlib
import json
import math
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from llm_transitivity.datasets.corpus import verify_dataset
from llm_transitivity.domain.scoring import EXTRACTION_RULE, interpret_response
from llm_transitivity.domain.selection import stratum
from llm_transitivity.evidence.serialization import digest, record_digest

VERSION = "full-corpus-report-v1"
STATUSES = (
    "answered",
    "content_filter",
    "empty",
    "ambiguous",
    "invalid_format",
    "error",
)


def file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text())


def require(condition, message: str) -> None:
    if not condition:
        raise ValueError(message)


def timestamp(value: str | None) -> float | None:
    return datetime.fromisoformat(value).timestamp() if value else None


def database(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE cases (
      uid TEXT PRIMARY KEY, dataset TEXT, row_number INTEGER, family TEXT,
      frequency TEXT, tense TEXT, formulation TEXT, validity TEXT, canonical TEXT,
      stratum TEXT, prompt TEXT, target TEXT, source_id TEXT, original_path TEXT,
      sentence_hash TEXT, original_hash TEXT, working_hash TEXT, uid_hash TEXT
    );
    CREATE TABLE results (
      phase TEXT, model TEXT, uid TEXT REFERENCES cases(uid), raw TEXT,
      status TEXT, answer TEXT, matched INTEGER, strict INTEGER,
      log TEXT, log_hash TEXT, generation_id TEXT,
      input_tokens INTEGER, output_tokens INTEGER, reasoning_tokens INTEGER,
      started REAL, ended REAL, duration REAL,
      PRIMARY KEY (phase,model,uid)
    );
    CREATE TABLE generations (id TEXT PRIMARY KEY, model TEXT, cost REAL, cost_source TEXT);
    CREATE TABLE generation_links (
      phase TEXT, model TEXT, uid TEXT, generation_id TEXT REFERENCES generations(id),
      final INTEGER, PRIMARY KEY (phase,model,uid,generation_id)
    );
    CREATE TABLE observations (
      generation_id TEXT, source TEXT, reference TEXT, cost REAL, details TEXT,
      UNIQUE(generation_id,source,reference,details,cost)
    );
    CREATE TABLE cost_conflicts (generation_id TEXT, previous REAL, observed REAL, source TEXT, reference TEXT);
    CREATE TABLE attempts (
      phase TEXT, model TEXT, uid TEXT, number INTEGER, generation_id TEXT,
      http_status INTEGER, failed INTEGER, started REAL, ended REAL, seconds REAL,
      PRIMARY KEY (phase,model,uid,number)
    );
    CREATE TABLE conditions (
      phase TEXT,model TEXT,uid TEXT, request_count INTEGER,
      request_faults TEXT, reported_providers TEXT, reported_tiers TEXT,
      reasoning_reported INTEGER, reasoning_nonzero INTEGER,
      PRIMARY KEY (phase,model,uid)
    );
    CREATE INDEX results_model ON results(phase,model,status);
    CREATE INDEX results_uid ON results(uid);
    CREATE INDEX cases_stratum ON cases(dataset,stratum);
    CREATE INDEX generation_links_id ON generation_links(generation_id);
    CREATE INDEX attempts_model ON attempts(phase,model);
    """)
    return db


def observe_generation(db, identifier, model, source, reference, cost, details) -> None:
    """Prefer captured costs, retain nulls and every conflicting observation."""
    if not identifier:
        return
    if cost is not None:
        require(
            isinstance(cost, (int, float)) and math.isfinite(cost),
            "Invalid reported cost",
        )
    prior = db.execute("SELECT * FROM generations WHERE id=?", (identifier,)).fetchone()
    if prior:
        require(prior["model"] == model, "Generation ID belongs to different models")
    encoded = json.dumps(details, sort_keys=True)
    if db.execute(
        "SELECT 1 FROM observations WHERE generation_id=? AND source=? AND reference=? AND cost IS ? AND details=?",
        (identifier, source, reference, cost, encoded),
    ).fetchone():
        return
    if prior:
        if (
            prior["cost"] is not None
            and cost is not None
            and abs(prior["cost"] - cost) > 1e-10
        ):
            db.execute(
                "INSERT INTO cost_conflicts VALUES (?,?,?,?,?)",
                (identifier, prior["cost"], cost, source, reference),
            )
        if cost is not None and (
            prior["cost"] is None
            or (source == "captured_response" and prior["cost_source"] != source)
        ):
            db.execute(
                "UPDATE generations SET cost=?,cost_source=? WHERE id=?",
                (cost, source, identifier),
            )
    else:
        db.execute(
            "INSERT INTO generations VALUES (?,?,?,?)",
            (identifier, model, cost, source if cost is not None else None),
        )
    db.execute(
        "INSERT OR IGNORE INTO observations VALUES (?,?,?,?,?)",
        (identifier, source, reference, cost, json.dumps(details, sort_keys=True)),
    )


def link_generation(db, phase, model, uid, identifier, final) -> None:
    if identifier:
        db.execute(
            """INSERT INTO generation_links VALUES (?,?,?,?,?)
          ON CONFLICT(phase,model,uid,generation_id) DO UPDATE SET final=MAX(final,excluded.final)""",
            (phase, model, uid, identifier, int(final)),
        )


def validate_closed_run(run: Path) -> dict:
    closure = read_json(run / "corpus/summary/closure.json")
    require(
        closure.get("complete") is True
        and closure.get("saved_samples") == 324000
        and closure.get("sample_errors") == 0,
        "Corpus closure is incomplete",
    )
    require(
        read_json(run / "worker.json").get("status") == "complete",
        "Run worker is not complete",
    )
    require(
        read_json(run / "preflight/summary/closure.json").get("technical_pass") is True,
        "Preflight did not pass",
    )
    index = read_json(run / "corpus/summary/log_index.json")
    require(
        index.get("call_export_status") == "exported" and len(index["logs"]) == 108,
        "Corpus exports or task index are incomplete",
    )
    return closure


def load_cases(db, root: Path, run: Path) -> tuple[dict, dict]:
    snapshot = run / "corpus/provenance/snapshot"
    manifest = read_json(snapshot / "datasets/pilot/manifest.json")
    config = read_json(run / "corpus/provenance/run.json")
    for entry in manifest["datasets"]:
        verified = verify_dataset(root, manifest["baseline_revision"], entry["dataset"])
        frozen = read_json(snapshot / entry["working_path"])
        require(frozen == verified.records, "Frozen input differs from verified source")
        require(
            verified.working_sha256 == entry["working_sha256"],
            "Working input hash differs",
        )
        for number, (row, original) in enumerate(
            zip(frozen, verified.originals, strict=True), 1
        ):
            sh = digest(row[2].encode())
            uid = f"{entry['dataset']}:{number}:{sh[:16]}"
            db.execute(
                "INSERT INTO cases VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    uid,
                    entry["dataset"],
                    number,
                    entry["dataset"].split("_")[0],
                    row[3],
                    row[4],
                    row[5],
                    row[6],
                    row[7],
                    record_digest(list(stratum(row)))[:16],
                    row[2],
                    "yes" if row[6] == "valid" else "no",
                    json.dumps(row[1], ensure_ascii=False),
                    entry["original_path"],
                    sh,
                    record_digest(original),
                    record_digest(row),
                    digest(uid.encode()),
                ),
            )
    require(
        db.execute("SELECT COUNT(*),COUNT(DISTINCT prompt) FROM cases").fetchone()[:]
        == (54000, 54000),
        "Expected 54000 distinct cases",
    )
    sizes = db.execute(
        "SELECT COUNT(*) n FROM cases GROUP BY dataset,stratum"
    ).fetchall()
    require(
        len(sizes) == 108 and all(r["n"] == 500 for r in sizes), "Invalid source strata"
    )
    db.commit()
    return manifest, config


def validate_sample(sample, case, system_prompt: str) -> dict:
    md = sample["metadata"]
    require(sample.get("error") is None, "Final sample has an execution error")
    require(
        sample["id"] == case["row_number"] and sample.get("epoch", 1) == 1,
        "Unexpected sample ID or epoch",
    )
    messages = sample["input"]
    require(
        [(v["role"], v["content"]) for v in messages]
        == [("system", system_prompt), ("user", case["prompt"])],
        "Sample text differs from source",
    )
    require(
        sample["target"] == case["target"] == md["expected_answer"],
        "Sample target differs",
    )
    mapping = {
        "dataset_family": "family",
        "frequency": "frequency",
        "verbal_time": "tense",
        "connectors": "formulation",
        "source_validity": "validity",
        "canonical_form": "canonical",
        "stratum_id": "stratum",
        "sentence_sha256": "sentence_hash",
        "working_record_sha256": "working_hash",
        "original_record_sha256": "original_hash",
        "original_row": "row_number",
        "original_path": "original_path",
    }
    require(
        all(md.get(k) == case[v] for k, v in mapping.items()),
        "Sample conditions or hashes differ",
    )
    require(
        md["source_id"] == json.loads(case["source_id"]), "Source identifier differs"
    )
    score = sample["scores"]["source_label_match"]
    sc = score["metadata"]
    output = sample["output"]
    raw = output.get("completion", "")
    filtered = bool(
        output.get("choices")
        and output["choices"][0].get("stop_reason") == "content_filter"
    )
    result = interpret_response(
        raw, error=bool(output.get("error")), content_filtered=filtered
    )
    require(sc.get("extraction_rule") == EXTRACTION_RULE, "Unexpected extraction rule")
    require(
        sc["status"] == result.status
        and sc["extracted_answer"] == result.extracted_answer
        and sc["format_compliant"] == result.format_compliant,
        "Native interpretation differs from frozen rule",
    )
    value = (
        ("C" if result.extracted_answer == case["target"] else "I")
        if result.status == "answered"
        else "N"
    )
    require(
        score["value"] == value
        and sc["expected"] == case["target"]
        and score["answer"] == raw,
        "Native score does not reconcile",
    )
    return {
        "raw": raw,
        "status": result.status,
        "answer": result.extracted_answer,
        "matched": int(value == "C"),
        "strict": int(result.format_compliant),
    }


def capture_sample(
    db, phase, model, uid, sample, routing, reasoning, reference
) -> None:
    """Store transport observations without fetching metadata or changing outcomes."""
    output = sample["output"]
    final_id = output.get("response_id")
    if final_id:
        observe_generation(db, final_id, model, "final_output", reference, None, {})
        link_generation(db, phase, model, uid, final_id, True)
    faults, providers, tiers, reasoning_values = [], set(), set(), []
    calls = sample["metadata"].get("openrouter_http_calls", [])
    for number, call in enumerate(calls, 1):
        data = (call.get("response_body") or {}).get("json") or {}
        if not isinstance(data, dict):
            data = {}
        request = (call.get("request_body") or {}).get("json") or {}
        if not isinstance(request, dict):
            request = {}
        provider = request.get("provider") or {}
        if (
            provider.get("only") != routing["provider_only"]
            or provider.get("allow_fallbacks") is not False
            or request.get("service_tier") != routing["service_tier"]
        ):
            faults.append(f"attempt {number}: requested routing mismatch")
        if request.get("max_tokens", request.get("max_completion_tokens")) != 1024:
            faults.append(f"attempt {number}: output limit mismatch")
        if (
            request.get("model") != model
            or provider.get("require_parameters") is not True
        ):
            faults.append(f"attempt {number}: model or required-parameter mismatch")
        reasoning_request = request.get("reasoning") or {}
        if reasoning["policy"] in {"enabled", "disabled"}:
            if reasoning_request.get("enabled") is not (
                reasoning["policy"] == "enabled"
            ):
                faults.append(f"attempt {number}: reasoning enabled flag mismatch")
            if (
                reasoning["effort"]
                and reasoning_request.get("effort") != reasoning["effort"]
            ):
                faults.append(f"attempt {number}: reasoning effort mismatch")
        usage = data.get("usage") or {}
        token_value = (usage.get("completion_tokens_details") or {}).get(
            "reasoning_tokens"
        )
        if token_value is not None:
            reasoning_values.append(token_value)
        if data.get("provider"):
            providers.add(str(data["provider"]))
        if data.get("service_tier"):
            tiers.add(str(data["service_tier"]))
        identifier = data.get("id")
        if identifier:
            observe_generation(
                db,
                identifier,
                model,
                "captured_response",
                f"{reference}:http:{number}",
                usage.get("cost"),
                {
                    "http_status": call.get("http_status"),
                    "provider": data.get("provider"),
                    "error": data.get("error"),
                },
            )
            link_generation(db, phase, model, uid, identifier, identifier == final_id)
        http_status = call.get("http_status")
        failed = http_status is None or http_status >= 400 or bool(data.get("error"))
        db.execute(
            "INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                phase,
                model,
                uid,
                number,
                identifier,
                http_status,
                int(failed),
                timestamp(call.get("request_started_utc")),
                timestamp(call.get("response_received_utc")),
                call.get("http_seconds"),
            ),
        )
    for lookup in sample["metadata"].get("openrouter_calls", []):
        identifier = lookup.get("generation_id")
        if not identifier:
            continue
        observe_generation(
            db, identifier, model, "lookup_reference", reference, None, {}
        )
        link_generation(db, phase, model, uid, identifier, identifier == final_id)
        for number, attempt in enumerate(
            (lookup.get("generation") or {}).get("attempts", []), 1
        ):
            data = (attempt.get("response_json") or {}).get("data") or {}
            if attempt.get("http_status") != 200 or not isinstance(data, dict):
                continue
            observe_generation(
                db,
                identifier,
                model,
                "generation_lookup",
                f"{reference}:lookup:{identifier}:{number}",
                data.get("total_cost"),
                data,
            )
            if data.get("provider_name"):
                providers.add(str(data["provider_name"]))
            if data.get("service_tier"):
                tiers.add(str(data["service_tier"]))
            if data.get("native_tokens_reasoning") is not None:
                reasoning_values.append(data["native_tokens_reasoning"])
    if reasoning["policy"] == "disabled" and any(v != 0 for v in reasoning_values):
        faults.append("nonzero reasoning reported while disabled")
    db.execute(
        "INSERT INTO conditions VALUES (?,?,?,?,?,?,?,?,?)",
        (
            phase,
            model,
            uid,
            len(calls),
            json.dumps(sorted(set(faults))),
            json.dumps(sorted(providers)),
            json.dumps(sorted(tiers)),
            int(bool(reasoning_values)),
            int(any(v != 0 for v in reasoning_values)),
        ),
    )


def ingest_phase(
    db,
    root: Path,
    run: Path,
    phase: str,
    system_prompt: str,
    config: dict,
    provenance: dict,
) -> list[dict]:
    directory = run / phase
    index = read_json(directory / "summary/log_index.json")
    tasks = []
    for position, entry in enumerate(index["logs"], 1):
        path = directory / entry["path"]
        require(
            path.resolve().is_relative_to(directory.resolve()),
            "Log path leaves run directory",
        )
        require(
            file_hash(path) == entry["sha256"], "Native log hash differs from closure"
        )
        provenance[str(path.relative_to(root))] = entry["sha256"]
        with ZipFile(path) as archive:
            header = json.loads(archive.read("header.json"))
            require(header["version"] == 2, "Unsupported native log format")
            require(header["status"] == "success", "Native task did not succeed")
            md = header["eval"]["metadata"]
            require(
                md.get("scoring_version") == "source-label-deterministic-v3",
                "Unexpected scoring version",
            )
            model = header["eval"]["model"].removeprefix("openrouter/")
            require(model in config["requested_routing"], "Unexpected model")
            dataset = md["dataset_name"]
            if phase == "corpus":
                require(
                    db.execute(
                        "SELECT COUNT(*) FROM cases WHERE dataset=?", (dataset,)
                    ).fetchone()[0]
                    in (2000, 4000),
                    "Unexpected full dataset",
                )
            counts = Counter()
            members = [
                n
                for n in archive.namelist()
                if n.startswith("samples/") and n.endswith(".json")
            ]
            require(len(members) == len(set(members)), "Duplicate native sample member")
            for member in members:
                sample = json.loads(archive.read(member))
                uid = sample["metadata"]["sample_uid"]
                case = db.execute("SELECT * FROM cases WHERE uid=?", (uid,)).fetchone()
                require(case is not None, "Sample is not in the full source corpus")
                if phase == "corpus":
                    require(
                        case["dataset"] == dataset, "Sample dataset differs from task"
                    )
                outcome = validate_sample(sample, case, system_prompt)
                usage = sample["output"].get("usage") or {}
                values = (
                    phase,
                    model,
                    uid,
                    outcome["raw"],
                    outcome["status"],
                    outcome["answer"],
                    outcome["matched"],
                    outcome["strict"],
                    str(path.relative_to(root)),
                    entry["sha256"],
                    sample["output"].get("response_id"),
                    usage.get("input_tokens"),
                    usage.get("output_tokens"),
                    usage.get("reasoning_tokens"),
                    timestamp(sample.get("started_at")),
                    timestamp(sample.get("completed_at")),
                    sample.get("total_time"),
                )
                db.execute(
                    "INSERT INTO results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    values,
                )
                capture_sample(
                    db,
                    phase,
                    model,
                    uid,
                    sample,
                    config["requested_routing"][model],
                    config["model_reasoning_policies"][model],
                    f"{path.name}:{member}",
                )
                counts[outcome["status"]] += 1
                counts["matched"] += outcome["matched"]
                counts["strict"] += outcome["strict"]
            require(
                len(members)
                == header["results"]["completed_samples"]
                == entry["sample_count"],
                "Task count does not reconcile",
            )
            native = next(
                s
                for s in header["results"]["scores"]
                if s["name"] == "source_label_match"
            )
            expected = {f"{s}_rate": counts[s] / len(members) for s in STATUSES}
            expected["format_compliant_rate"] = counts["strict"] / len(members)
            if counts["answered"]:
                expected["source_agreement"] = counts["matched"] / counts["answered"]
            require(
                all(
                    abs(native["metrics"][k]["value"] - v) < 1e-10
                    for k, v in expected.items()
                ),
                "Native task metrics do not reconcile",
            )
            tasks.append(
                {
                    "phase": phase,
                    "model": model,
                    "dataset": dataset,
                    "samples": len(members),
                    "started": timestamp(header["stats"]["started_at"]),
                    "ended": timestamp(header["stats"]["completed_at"]),
                    "adaptive_history": header["stats"].get(
                        "connection_limit_history", []
                    ),
                    "log": str(path.relative_to(root)),
                }
            )
        db.commit()
        print(f"{phase}: verified {position}/{len(index['logs'])} tasks", flush=True)
    return tasks
