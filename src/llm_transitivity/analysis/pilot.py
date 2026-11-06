"""Reevaluate a frozen pilot and save new analysis without model requests."""

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, median

from inspect_ai.log import read_eval_log

from llm_transitivity.analysis.calculations import (
    cost_projection,
    interval_union,
    measures,
    merge_generation,
    percentile90,
    queue_seconds,
    task_overhead,
)
from llm_transitivity.domain.scoring import EXTRACTION_RULE, interpret_response
from llm_transitivity.domain.selection import stratum
from llm_transitivity.evidence.metadata import SCORING_VERSION, package_sources
from llm_transitivity.evidence.serialization import digest, record_digest

CONDITIONS = (
    "dataset_family",
    "frequency",
    "verbal_time",
    "canonical_form",
    "connectors",
    "source_validity",
    "working_dataset",
    "stratum_id",
)


def _timestamp(value: str) -> float:
    return datetime.fromisoformat(value).timestamp()


def _payload(call: dict, key: str) -> dict:
    return (call.get(key) or {}).get("json") or {}


def _score(raw: str, output, expected: str) -> dict:
    result = interpret_response(
        raw,
        error=bool(output.error),
        content_filtered=bool(
            output.choices and output.stop_reason == "content_filter"
        ),
    )
    return {
        **asdict(result),
        "value": ("C" if result.extracted_answer == expected else "I")
        if result.status == "answered"
        else "N",
        "extraction_rule": EXTRACTION_RULE,
    }


def _old_score(score) -> dict:
    return {"value": score.value, **score.metadata}


def _read_logs(run: Path) -> tuple[list, dict]:
    logs, latest = [], {}
    for path in sorted((run / "inspect").glob("*.eval")):
        log = read_eval_log(str(path))
        logs.append((path, log))
        if log.status != "success":
            continue
        key = (log.eval.model, log.eval.metadata["dataset_name"])
        order = (log.stats.completed_at, log.eval.created, path.name)
        if key not in latest or order > latest[key][0]:
            latest[key] = (order, path, log)
    return logs, latest


def _capture_ledger(logs: list) -> dict:
    ledger = {}
    for path, log in logs:
        for sample in log.samples or []:
            for call in sample.metadata.get("openrouter_http_calls", []):
                data = _payload(call, "response_body")
                identifier = data.get("id")
                if identifier:
                    merge_generation(
                        ledger,
                        identifier,
                        {
                            "model": log.eval.model,
                            "source": "captured_response",
                            "log": path.name,
                            "request_started_utc": call["request_started_utc"],
                            "cost_usd": (data.get("usage") or {}).get("cost"),
                            "http_status": call.get("http_status"),
                            "provider_error_code": (data.get("error") or {}).get(
                                "code"
                            ),
                        },
                    )
            for lookup in sample.metadata.get("openrouter_calls", []):
                for attempt in (lookup.get("generation") or {}).get("attempts", []):
                    data = (attempt.get("response_json") or {}).get("data") or {}
                    if attempt.get("http_status") == 200 and data:
                        merge_generation(
                            ledger,
                            lookup["generation_id"],
                            {
                                "model": log.eval.model,
                                "source": "generation_lookup",
                                "log": path.name,
                                "cost_usd": data.get("total_cost"),
                                "streamed": data.get("streamed"),
                                "service_tier": data.get("service_tier"),
                            },
                        )
    return ledger


def _sample_row(root: Path, path: Path, log, sample, ledger: dict) -> dict:
    if sample.error:
        raise ValueError("Final samples must not contain execution errors")
    md = sample.metadata
    score = sample.scores["source_label_match"]
    before = _old_score(score)
    after = _score(sample.output.completion, sample.output, md["expected_answer"])
    if before["format_compliant"] != after["format_compliant"]:
        raise ValueError("Strict response formatting changed")
    final_id = sample.output.response_id
    call = next(
        (
            c
            for c in md.get("openrouter_http_calls", [])
            if _payload(c, "response_body").get("id") == final_id
        ),
        None,
    )
    if call is None or final_id not in ledger:
        raise ValueError("Final response has no captured generation")
    data = _payload(call, "response_body")
    request = _payload(call, "request_body")
    return {
        "model": log.eval.model,
        "group": log.eval.metadata["generation_group"],
        "sample_uid": md["sample_uid"],
        "sample_id": sample.id,
        "dataset": md["working_dataset"],
        "stratum": md["working_dataset"] + ":" + md["stratum_id"],
        "conditions": {key: md[key] for key in CONDITIONS},
        "prompt": sample.input[-1].content,
        "raw_response": sample.output.completion,
        "target": md["expected_answer"],
        "before": before,
        "after": after,
        "changed": any(
            before.get(key) != after.get(key)
            for key in (
                "value",
                "status",
                "extracted_answer",
                "format_compliant",
                "extraction_position",
            )
        ),
        "source_log": str(path.relative_to(root)),
        "source_log_sha256": digest(path.read_bytes()),
        "historical_scoring_version": log.eval.metadata["scoring_version"],
        "scoring_version": SCORING_VERSION,
        "final_generation_id": final_id,
        "final_cost_usd": ledger[final_id]["cost_usd"],
        "usage": data.get("usage"),
        "routing": {
            "requested_model": log.eval.model.removeprefix("openrouter/"),
            "requested_provider": request.get("provider"),
            "requested_tier": request.get("service_tier"),
            "requested_reasoning": request.get("reasoning"),
            "requested_stream": request.get("stream", "omitted"),
            "observed_model": data.get("model"),
            "observed_provider": data.get("provider"),
            "observed_tier": data.get("service_tier"),
            "routing_metadata": data.get("openrouter_metadata"),
        },
        "sample_seconds": sample.total_time,
        "started_at": sample.started_at,
        "completed_at": sample.completed_at,
    }


def _validate_selection(rows: list[dict], manifest: dict, root: Path) -> None:
    expected = {
        f"{entry['dataset']}:{row['original_row']}:{row['sentence_sha256'][:16]}"
        for entry in manifest["datasets"]
        for row in entry["selected_rows"]
    }
    models = {row["model"] for row in rows}
    if len(expected) != 540 or len(models) != 6 or len(rows) != 3240:
        raise ValueError("Expected six models and 3240 final samples")
    source_cases = {}
    for entry in manifest["datasets"]:
        records = json.loads((root / entry["pilot_path"]).read_text())
        for selected, record in zip(entry["selected_rows"], records, strict=True):
            uid = f"{entry['dataset']}:{selected['original_row']}:{selected['sentence_sha256'][:16]}"
            source_cases[uid] = (record[2], "yes" if record[6] == "valid" else "no")
    if any(
        source_cases.get(row["sample_uid"]) != (row["prompt"], row["target"])
        for row in rows
    ):
        raise ValueError("Saved prompts or targets do not match verified source cases")
    for model in models:
        selected = [row for row in rows if row["model"] == model]
        if len(selected) != 540 or {r["sample_uid"] for r in selected} != expected:
            raise ValueError("Model sample IDs do not match the manifest")
        strata = Counter(row["stratum"] for row in selected)
        if len(strata) != 108 or set(strata.values()) != {5}:
            raise ValueError("Expected five samples in each of 108 strata")
    paired = defaultdict(set)
    for row in rows:
        paired[row["sample_uid"]].add((row["prompt"], row["target"]))
    if any(len(values) != 1 for values in paired.values()):
        raise ValueError("Paired model inputs or targets differ")


def _time_projection(
    root: Path, model_rows: list[dict], latest: dict, manifest: dict
) -> dict:
    by_stratum = defaultdict(list)
    by_dataset = defaultdict(list)
    for row in model_rows:
        if row["sample_seconds"] is None:
            raise ValueError("Missing sample duration")
        by_stratum[row["stratum"]].append(row["sample_seconds"])
        by_dataset[row["dataset"]].append(row)
    overheads, recovered = [], []
    for _, path, log in latest.values():
        if log.eval.model != model_rows[0]["model"]:
            continue
        task_start, task_end = (
            _timestamp(log.stats.started_at),
            _timestamp(log.stats.completed_at),
        )
        rows = by_dataset[log.samples[0].metadata["working_dataset"]]
        ordered = sorted(rows, key=lambda r: r["sample_id"])
        measured = task_overhead(
            [
                (
                    _timestamp(r["started_at"]),
                    _timestamp(r["completed_at"]),
                    r["sample_seconds"],
                )
                for r in ordered
            ],
            task_start,
            task_end,
            16,
        )
        if measured is None:
            recovered.append(path.name)
            continue
        overheads.append(measured)
    overhead = median(overheads) if overheads else 0.0
    totals = {"central_seconds": 0.0, "slow_seconds": 0.0}
    for entry in manifest["datasets"]:
        full = json.loads((root / entry["working_path"]).read_text())
        keys = [
            entry["dataset"] + ":" + record_digest(list(stratum(row)))[:16]
            for row in full
        ]
        for name, estimator in [
            ("central_seconds", mean),
            ("slow_seconds", percentile90),
        ]:
            durations = {key: estimator(values) for key, values in by_stratum.items()}
            totals[name] += (
                queue_seconds([durations[key] for key in keys], 16) + overhead
            )
    return {
        **totals,
        "median_task_overhead_seconds": overhead,
        "clean_tasks_for_overhead": len(overheads),
        "recovered_tasks_excluded": recovered,
        "sample_active_seconds": interval_union(
            [
                (_timestamp(r["started_at"]), _timestamp(r["completed_at"]))
                for r in model_rows
            ]
        ),
    }


def _model_summary(
    root: Path, rows: list[dict], ledger: dict, latest: dict, manifest: dict
) -> dict:
    model = rows[0]["model"]
    entries = [v for v in ledger.values() if v["model"] == model]
    final_ids = {row["final_generation_id"] for row in rows}
    populations = {
        entry["dataset"] + ":" + record_digest(s["values"])[:16]: s["population"]
        for entry in manifest["datasets"]
        for s in entry["strata"]
    }
    breakdowns = {
        condition: {
            value: measures([r for r in rows if r["conditions"][condition] == value])
            for value in sorted({r["conditions"][condition] for r in rows})
        }
        for condition in CONDITIONS
    }
    return {
        "group": rows[0]["group"],
        "before": measures(rows, "before"),
        "after": measures(rows),
        "changed_samples": sum(row["changed"] for row in rows),
        "breakdowns": breakdowns,
        "billing": {
            "unique_ids": len(entries),
            "final_response_ids": len(final_ids),
            "additional_ids": len({v["generation_id"] for v in entries} - final_ids),
            "known_cost_usd": sum(
                v["cost_usd"] for v in entries if v["cost_usd"] is not None
            ),
            "missing_cost_ids": [
                v["generation_id"] for v in entries if v["cost_usd"] is None
            ],
            "conflicting_cost_ids": [
                v["generation_id"] for v in entries if v["cost_conflicts"]
            ],
            "provider_errors": dict(
                Counter(code for v in entries for code in v["provider_error_codes"])
            ),
        },
        "cost_projection": cost_projection(rows, populations),
        "time_projection": _time_projection(root, rows, latest, manifest),
        "tokens": {
            field: sum((r["usage"] or {}).get(field, 0) for r in rows)
            for field in ["prompt_tokens", "completion_tokens", "total_tokens"]
        },
        "routing": {
            "observed_providers": dict(
                Counter(r["routing"]["observed_provider"] for r in rows)
            ),
            "observed_tiers": dict(
                Counter(r["routing"]["observed_tier"] for r in rows)
            ),
            "model_mismatches": sum(
                r["routing"]["observed_model"] != r["routing"]["requested_model"]
                for r in rows
            ),
            "tier_mismatches": sum(
                r["routing"]["observed_tier"] != r["routing"]["requested_tier"]
                for r in rows
            ),
            "reasoning_tokens": dict(
                Counter(
                    str(
                        ((r["usage"] or {}).get("completion_tokens_details") or {}).get(
                            "reasoning_tokens"
                        )
                    )
                    for r in rows
                )
            ),
            "routing_metadata_present": sum(
                bool(r["routing"]["routing_metadata"]) for r in rows
            ),
        },
    }


def analyze(
    root: Path, run: Path, output: Path, lookup_evidence: Path | None = None
) -> dict:
    """Validate before writing a new, exclusive analysis directory."""
    if output.exists():
        raise FileExistsError(output)
    snapshot = run / "provenance/snapshot"
    hashes = json.loads((run / "provenance/snapshot_hashes.json").read_text())
    for relative, expected in hashes.items():
        if digest((snapshot / relative).read_bytes()) != expected:
            raise ValueError("Historical pilot snapshot changed: " + relative)
    manifest = json.loads((snapshot / "datasets/pilot/manifest.json").read_text())
    logs, latest = _read_logs(run)
    if len(latest) != 108:
        raise ValueError("Expected 108 successful final tasks")
    inputs = {
        str(path.relative_to(root)): digest(path.read_bytes()) for path, _ in logs
    }
    for name in ["run.json", "flow_spec.json", "snapshot_hashes.json"]:
        path = run / "provenance" / name
        inputs[str(path.relative_to(root))] = digest(path.read_bytes())
    ledger = _capture_ledger(logs)
    refresh_status = Counter()
    if lookup_evidence is not None:
        inputs[str(lookup_evidence.relative_to(root))] = digest(
            lookup_evidence.read_bytes()
        )
        for lookup in json.loads(lookup_evidence.read_text()):
            identifier = lookup["generation_id"]
            if identifier not in ledger:
                raise ValueError("Lookup ID is outside the captured pilot")
            refresh_status[lookup["lookup_status"]] += 1
            for attempt in (lookup.get("generation") or {}).get("attempts", []):
                data = (attempt.get("response_json") or {}).get("data") or {}
                if attempt.get("http_status") == 200 and data:
                    if data.get("id", identifier) != identifier:
                        raise ValueError("Lookup response ID differs from its query")
                    merge_generation(
                        ledger,
                        identifier,
                        {
                            "model": ledger[identifier]["model"],
                            "source": "generation_lookup",
                            "evidence": str(lookup_evidence.relative_to(root)),
                            "cost_usd": data.get("total_cost"),
                        },
                    )
    rows = [
        _sample_row(root, path, log, sample, ledger)
        for _, path, log in latest.values()
        for sample in log.samples or []
    ]
    _validate_selection(rows, manifest, snapshot)
    models = {
        model: _model_summary(
            root, [r for r in rows if r["model"] == model], ledger, latest, manifest
        )
        for model in sorted({r["model"] for r in rows})
    }
    groups = {}
    for group in ["earlier", "later", "all"]:
        selected = [v for v in models.values() if group == "all" or v["group"] == group]
        groups[group] = {
            "models": len(selected),
            "full_responses": len(selected) * 54000,
            "central_cost_usd": sum(
                v["cost_projection"]["central_usd"] for v in selected
            )
            if all(v["cost_projection"]["central_usd"] is not None for v in selected)
            else None,
            "three_attempts_cost_usd": sum(
                v["cost_projection"]["three_attempts_usd"] for v in selected
            )
            if all(
                v["cost_projection"]["three_attempts_usd"] is not None for v in selected
            )
            else None,
            "central_seconds": sum(
                v["time_projection"]["central_seconds"] for v in selected
            ),
            "slow_seconds": sum(v["time_projection"]["slow_seconds"] for v in selected),
        }
    starts = [_timestamp(r["started_at"]) for r in rows]
    ends = [_timestamp(r["completed_at"]) for r in rows]
    active = interval_union(list(zip(starts, ends)))
    summary = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source_run": str(run.relative_to(root)),
        "scoring_version": SCORING_VERSION,
        "extraction_rule": EXTRACTION_RULE,
        "final_tasks": len(latest),
        "final_samples": len(rows),
        "changed_samples": sum(r["changed"] for r in rows),
        "additional_lookup_status": dict(refresh_status),
        "before": measures(rows, "before"),
        "after": measures(rows),
        "models": models,
        "groups": groups,
        "elapsed_sample_window_seconds": max(ends) - min(starts),
        "active_sample_union_seconds": active,
        "no_active_sample_seconds": max(ends) - min(starts) - active,
        "inputs_sha256": inputs,
        "analysis_sources_sha256": {
            p: digest((root / p).read_bytes()) for p in package_sources(root)
        },
        "code_revision": subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip(),
        "code_dirty": bool(
            subprocess.check_output(
                ["git", "-C", str(root), "status", "--porcelain"], text=True
            )
        ),
    }
    for relative, expected in inputs.items():
        if digest((root / relative).read_bytes()) != expected:
            raise ValueError("Source evidence changed during analysis: " + relative)
    output.mkdir(parents=True, exist_ok=False)
    for name, value in [("summary.json", summary), ("generations.json", ledger)]:
        (output / name).write_text(
            json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        )
    with (output / "samples.jsonl").open("x") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lookup-evidence", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    summary = analyze(
        root,
        (root / args.run).resolve(),
        (root / args.output).resolve(),
        (root / args.lookup_evidence).resolve() if args.lookup_evidence else None,
    )
    print(
        json.dumps(
            {
                "samples": summary["final_samples"],
                "changed": summary["changed_samples"],
                "groups": summary["groups"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
