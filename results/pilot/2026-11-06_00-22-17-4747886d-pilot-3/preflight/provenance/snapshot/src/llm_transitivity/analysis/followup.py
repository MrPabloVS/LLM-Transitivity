"""Review follow-up phases without making HTTP or model requests."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import median

from inspect_ai.log import read_eval_log

from llm_transitivity.analysis.calculations import measures, percentile90
from llm_transitivity.analysis.pilot import _capture_ledger
from llm_transitivity.domain.config import profile_models
from llm_transitivity.domain.scoring import EXTRACTION_RULE
from llm_transitivity.evidence.serialization import digest


def failed_attempt(call: dict) -> bool:
    status = call.get("http_status")
    body = (call.get("response_body") or {}).get("json") or {}
    return status is None or status >= 400 or bool(body.get("error"))


def peak_concurrency(intervals: list[tuple[float, float]]) -> int:
    events = sorted(
        [(start, 1) for start, end in intervals if end > start]
        + [(end, -1) for start, end in intervals if end > start]
    )
    active = peak = 0
    for _, change in events:
        active += change
        peak = max(peak, active)
    return peak


def _time(value: str) -> float:
    return datetime.fromisoformat(value).timestamp()


def load_gate(model: dict, capacity: int) -> list[str]:
    reasons = []
    if model["faults"]:
        reasons.append("experimental conditions or completeness failed")
    if model["failed_attempt_rate"] is None or model["failed_attempt_rate"] > 0.05:
        reasons.append("failed attempt rate exceeds 5% or is unknown")
    if model["peak_samples"] < capacity:
        reasons.append("configured sample concurrency was not reached")
    return reasons


def review_phase(root: Path, phase: Path, spec: dict) -> dict:
    logs = [
        (p, read_eval_log(str(p))) for p in sorted((phase / "inspect").glob("*.eval"))
    ]
    latest = {}
    for path, log in logs:
        key = (log.eval.model, log.eval.metadata.get("dataset_name"))
        rank = (log.status == "success", log.stats.completed_at or "", path.name)
        if key not in latest or rank > latest[key][0]:
            latest[key] = (rank, path, log)
    ledger = _capture_ledger(logs)
    models = {
        m.identifier: m
        for m in profile_models(spec["options"]["metadata"].get("profile", "haiku"))
    }
    wanted = spec["options"]["metadata"]["generation_groups"]
    source_manifest = json.loads((root / "datasets/pilot/manifest.json").read_text())
    source_cases = {}
    first_uid = None
    for entry in source_manifest["datasets"]:
        for row, origin in zip(
            json.loads((root / entry["pilot_path"]).read_text()),
            entry["selected_rows"],
            strict=True,
        ):
            uid = f"{entry['dataset']}:{origin['original_row']}:{origin['sentence_sha256'][:16]}"
            source_cases[uid] = (row[2], "yes" if row[6] == "valid" else "no")
            if first_uid is None:
                first_uid = uid
    phase_name = spec["options"]["metadata"]["phase"]
    expected_uids = {first_uid} if phase_name == "preflight" else set(source_cases)
    if phase_name == "load-validation":
        expected_uids = {
            r["sample_uid"]
            for r in json.loads((root / "datasets/load/manifest.json").read_text())[
                "selected_rows"
            ]
        }
    by_model = {}
    sample_records = []
    for identifier in wanted:
        model = models[identifier]
        faults, seen, attempts, intervals, http_intervals, durations, scored = (
            [],
            [],
            {},
            [],
            [],
            [],
            [],
        )
        final_ids, unverified, filtered_uids = [], [], []
        for _, path, log in latest.values():
            if log.eval.model != "openrouter/" + identifier:
                continue
            if log.status != "success":
                faults.append({"log": path.name, "kind": "task did not succeed"})
            for sample in log.samples or []:
                md = sample.metadata
                uid = md.get("sample_uid")
                seen.append(uid)
                raw = sample.output.completion
                if sample.error:
                    faults.append({"uid": uid, "kind": "sample error or empty output"})
                if source_cases.get(uid) != (
                    sample.input[-1].content,
                    md.get("expected_answer"),
                ):
                    faults.append(
                        {"uid": uid, "kind": "source prompt or target differs"}
                    )
                score = (sample.scores or {}).get("source_label_match")
                if score is None:
                    faults.append({"uid": uid, "kind": "missing v3 score"})
                if score and score.metadata.get("extraction_rule") != EXTRACTION_RULE:
                    faults.append(
                        {"uid": uid, "kind": "wrong scoring extraction version"}
                    )
                if score:
                    value = {"value": score.value, **score.metadata}
                    scored.append({"after": value})
                    sample_records.append(
                        {
                            "model": identifier,
                            "sample_uid": uid,
                            "review_policy": "content-filter-outcome-v2",
                            "phase": phase_name,
                            "conditions": {
                                k: md.get(k)
                                for k in [
                                    "dataset_family",
                                    "frequency",
                                    "verbal_time",
                                    "canonical_form",
                                    "connectors",
                                    "source_validity",
                                    "stratum_id",
                                ]
                            },
                            "prompt": sample.input[-1].content,
                            "raw_response": raw,
                            "target": md.get("expected_answer"),
                            "after": value,
                            "source_log": str(path.relative_to(root)),
                            "source_log_sha256": digest(path.read_bytes()),
                            "seconds": sample.total_time,
                            "generation_id": sample.output.response_id,
                        }
                    )
                if sample.started_at and sample.completed_at:
                    intervals.append(
                        (_time(sample.started_at), _time(sample.completed_at))
                    )
                if sample.total_time is not None:
                    durations.append(sample.total_time)
                final_id = sample.output.response_id
                final_ids.append(final_id)
                calls = md.get("openrouter_http_calls", [])
                final = None
                for call in calls:
                    key = (call.get("request_started_utc"), call.get("url"))
                    attempts[key] = call
                    if call.get("response_received_utc"):
                        http_intervals.append(
                            (
                                _time(call["request_started_utc"]),
                                _time(call["response_received_utc"]),
                            )
                        )
                    body = (call.get("response_body") or {}).get("json") or {}
                    if body.get("id") == final_id:
                        final = (call, body)
                if final is None:
                    faults.append({"uid": uid, "kind": "missing final HTTP capture"})
                    continue
                call, body = final
                request = (call.get("request_body") or {}).get("json") or {}
                provider = request.get("provider") or {}
                reasoning = request.get("reasoning") or {}
                expected_provider = {
                    "openai": "OpenAI",
                    "anthropic": "Anthropic",
                    "google": "Google AI Studio",
                }[identifier.split("/")[0]]
                usage = body.get("usage") or {}
                expected_reasoning = (
                    log.eval.metadata.get("reasoning_policy", "disabled") == "enabled"
                )
                expected_effort = log.eval.model_generate_config.reasoning_effort
                reasoning_tokens = (usage.get("completion_tokens_details") or {}).get(
                    "reasoning_tokens"
                )
                checks = {
                    "request model": request.get("model") == identifier,
                    "single provider": provider.get("only") == [model.provider],
                    "fallback disabled": provider.get("allow_fallbacks") is False,
                    "parameter support": provider.get("require_parameters") is True,
                    "request tier": request.get("service_tier") == model.service_tier,
                    "response model": body.get("model") == identifier,
                    "response provider": body.get("provider") == expected_provider,
                    "response tier": body.get("service_tier") == model.service_tier,
                    "reasoning usage": (
                        isinstance(reasoning_tokens, int) and reasoning_tokens >= 0
                    )
                    if expected_reasoning
                    else reasoning_tokens == 0,
                    "final reported cost": usage.get("cost") is not None,
                }
                filtered = (
                    bool(sample.output.choices)
                    and sample.output.stop_reason == "content_filter"
                    and score is not None
                    and score.metadata.get("status") == "content_filter"
                    and any(
                        choice.get("finish_reason") == "content_filter"
                        for choice in body.get("choices", [])
                    )
                )
                if not raw.strip() and not filtered:
                    faults.append({"uid": uid, "kind": "sample error or empty output"})
                if filtered:
                    filtered_uids.append(uid)
                    missing = {
                        "response tier": body.get("service_tier") is None,
                        "reasoning usage": (
                            usage.get("completion_tokens_details") or {}
                        ).get("reasoning_tokens")
                        is None,
                        "final reported cost": usage.get("cost") is None,
                    }
                    for name, absent in missing.items():
                        if absent:
                            unverified.append({"uid": uid, "kind": name})
                            checks.pop(name)
                if model.supports_reasoning:
                    checks["reasoning control"] = (
                        reasoning.get("enabled") is expected_reasoning
                    )
                if expected_effort:
                    checks["explicit effort"] = (
                        reasoning.get("effort") == expected_effort
                    )
                faults.extend(
                    {"uid": uid, "kind": name}
                    for name, passed in checks.items()
                    if not passed
                )
        if len(seen) != len(expected_uids) or set(seen) != expected_uids:
            faults.append(
                {
                    "kind": "case coverage differs",
                    "saved": len(seen),
                    "expected": len(expected_uids),
                }
            )
        entries = [
            v for v in ledger.values() if v["model"] == "openrouter/" + identifier
        ]
        failures = sum(failed_attempt(c) for c in attempts.values())
        window = max((end for start, end in intervals), default=0) - min(
            (start for start, end in intervals), default=0
        )
        by_model[identifier] = {
            "samples": len(seen),
            "expected_samples": len(expected_uids),
            "faults": faults,
            "filtered_uids": filtered_uids,
            "unverified_fields": unverified,
            "measures": measures(scored),
            "attempts": len(attempts),
            "failed_attempts": failures,
            "unidentified_attempts": sum(
                not (((c.get("response_body") or {}).get("json") or {}).get("id"))
                for c in attempts.values()
            ),
            "failed_attempt_rate": failures / len(attempts) if attempts else None,
            "peak_samples": peak_concurrency(intervals),
            "peak_http_requests": peak_concurrency(list(set(http_intervals))),
            "sample_p50_seconds": median(durations) if durations else None,
            "sample_p90_seconds": percentile90(durations) if durations else None,
            "task_window_seconds": window,
            "cases_per_minute": len(seen) * 60 / window if window else None,
            "known_cost_usd": sum(
                v["cost_usd"] for v in entries if v["cost_usd"] is not None
            ),
            "missing_cost_ids": [
                v["generation_id"] for v in entries if v["cost_usd"] is None
            ],
            "generation_ids": [v["generation_id"] for v in entries],
            "final_generation_ids": final_ids,
            "provider_errors": dict(
                Counter(code for v in entries for code in v["provider_error_codes"])
            ),
        }
    passed = all(not v["faults"] for v in by_model.values())
    load_reasons = (
        {key: load_gate(value, 64) for key, value in by_model.items()}
        if phase_name == "load-validation"
        else {}
    )
    return {
        "review_policy": "content-filter-outcome-v2",
        "phase": phase_name,
        "technical_pass": passed
        and (
            all(not reasons for reasons in load_reasons.values())
            if load_reasons
            else True
        ),
        "models": by_model,
        "load64_validated": bool(load_reasons)
        and all(not reasons for reasons in load_reasons.values()),
        "load_reasons": load_reasons,
        "samples": sample_records,
        "generations": ledger,
        "note": "Direct 64-slot load; no matched 16/32 load or measured speedup is claimed.",
    }
