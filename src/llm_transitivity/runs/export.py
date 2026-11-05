"""Build, enrich, and write complete per-call Inspect records."""

import json
import os
from pathlib import Path

from inspect_ai.event import ModelEvent
from inspect_ai.log import read_eval_log

from llm_transitivity.evidence.serialization import digest
from llm_transitivity.openrouter.client import (
    captured_generation_ids,
    generation_details,
    redact,
)


def _event_record(
    log, sample, event: ModelEvent, number: int, path: Path, log_hash: str
) -> dict:
    response = event.call.response if event.call else None
    response_id = response.get("id") if isinstance(response, dict) else None
    response_id = response_id or event.output.response_id
    return {
        "inspect_log": str(path),
        "inspect_log_sha256": log_hash,
        "inspect_eval_id": log.eval.eval_id,
        "inspect_run_id": log.eval.run_id,
        "experiment_run_id": (log.eval.metadata or {}).get("experiment_run_id"),
        "sample_id": sample.id,
        "sample_epoch": sample.epoch,
        "sample_uid": (sample.metadata or {}).get("sample_uid"),
        "model_event_index": number,
        "generation_id": response_id,
        "evaluation_metadata": log.eval.metadata,
        "sample_metadata": sample.metadata,
        "sample_error": sample.error.model_dump(mode="json") if sample.error else None,
        "model_event": event.model_dump(mode="json"),
    }


def _empty_record(path: Path, sample) -> dict:
    return {
        "inspect_log": str(path),
        "sample_id": sample.id,
        "sample_uid": (sample.metadata or {}).get("sample_uid"),
        "status": "no model event",
        "sample_error": sample.error.model_dump(mode="json") if sample.error else None,
    }


def _enrich_record(
    record: dict, sample, cache: dict, api_key: str | None, include_content: bool
) -> None:
    response_id = record["generation_id"]
    ids = [response_id] if response_id else []
    ids += captured_generation_ids(
        (sample.metadata or {}).get("openrouter_http_calls", [])
    )
    for generation_id in dict.fromkeys(ids or [None]):
        if generation_id not in cache:
            cache[generation_id] = generation_details(
                generation_id, api_key, include_content=include_content
            )
    record["generation_lookups"] = list(cache.values())


def export_log(
    path: Path, *, fetch: bool = False, include_content: bool = False
) -> list[dict]:
    log = read_eval_log(str(path))
    log_hash = digest(path.read_bytes())
    api_key = os.environ.get("OPENROUTER_API_KEY")
    records = []
    for sample in log.samples or []:
        events = [event for event in sample.events if isinstance(event, ModelEvent)]
        if not events:
            records.append(redact(_empty_record(path, sample), api_key or ""))
            continue
        lookup_cache = {}
        for number, event in enumerate(events, 1):
            record = _event_record(log, sample, event, number, path, log_hash)
            if fetch and str(event.model).startswith("openrouter/"):
                _enrich_record(record, sample, lookup_cache, api_key, include_content)
            records.append(redact(record, api_key or ""))
    return records


def _write_export(output_dir: Path, path: Path, records: list[dict]) -> None:
    filename = (
        f"{path.stem}-{digest(str(path).encode())[:12]}-{os.urandom(4).hex()}.json"
    )
    with (output_dir / filename).open("x", encoding="utf-8") as file:
        file.write(json.dumps(records, ensure_ascii=False, indent=2) + "\n")


def export_run(
    log_dir: Path,
    *,
    output_dir: Path | None = None,
    fetch: bool = False,
    include_content: bool = False,
) -> Path:
    """Export into a run's sibling directory, preserving previous exports."""
    if (log_dir / "inspect").is_dir():
        log_dir = log_dir / "inspect"
    paths = sorted(log_dir.rglob("*.eval"))
    if not paths:
        raise ValueError("No Inspect .eval files found")
    if output_dir is None:
        output_dir = (
            log_dir.parent if log_dir.name == "inspect" else log_dir
        ) / "openrouter_calls"
    output_dir.mkdir(exist_ok=True)
    for path in paths:
        records = export_log(path, fetch=fetch, include_content=include_content)
        _write_export(output_dir, path, records)
    return output_dir
