"""Export per-call Inspect records and optionally refresh OpenRouter metadata."""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from inspect_ai.event import ModelEvent
from inspect_ai.log import read_eval_log

from openrouter_telemetry import generation_details, redact
from prepare_pilot import digest


def export_log(
    path: Path, *, fetch: bool = False, include_content: bool = False
) -> list[dict]:
    log = read_eval_log(str(path))
    log_hash = digest(path.read_bytes())
    records = []
    for sample in log.samples or []:
        lookup_cache = {}
        for number, event in enumerate(
            (e for e in sample.events if isinstance(e, ModelEvent)), 1
        ):
            response = event.call.response if event.call else None
            response_id = response.get("id") if isinstance(response, dict) else None
            response_id = response_id or event.output.response_id
            record = {
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
                "sample_error": sample.error.model_dump(mode="json")
                if sample.error
                else None,
                "model_event": event.model_dump(mode="json"),
            }
            if fetch and str(event.model).startswith("openrouter/"):
                ids = [response_id] if response_id else []
                for call in (sample.metadata or {}).get("openrouter_http_calls", []):
                    payload = call.get("response_body", {}).get("json")
                    if isinstance(payload, dict) and isinstance(payload.get("id"), str):
                        ids.append(payload["id"])
                for generation_id in dict.fromkeys(ids or [None]):
                    if generation_id not in lookup_cache:
                        lookup_cache[generation_id] = generation_details(
                            generation_id,
                            os.environ.get("OPENROUTER_API_KEY"),
                            include_content=include_content,
                        )
                record["generation_lookups"] = list(lookup_cache.values())
            records.append(redact(record, os.environ.get("OPENROUTER_API_KEY", "")))
        if not any(isinstance(e, ModelEvent) for e in sample.events):
            records.append(
                {
                    "inspect_log": str(path),
                    "sample_id": sample.id,
                    "sample_uid": (sample.metadata or {}).get("sample_uid"),
                    "status": "no model event",
                    "sample_error": sample.error.model_dump(mode="json")
                    if sample.error
                    else None,
                }
            )
    return records


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
        filename = (
            f"{path.stem}-{digest(str(path).encode())[:12]}-{os.urandom(4).hex()}.json"
        )
        with (output_dir / filename).open("x", encoding="utf-8") as file:
            file.write(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_dir", type=Path)
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Refresh generation metadata using read-only OpenRouter requests",
    )
    parser.add_argument(
        "--include-stored-content",
        action="store_true",
        help="Also request stored content; may require management-key access",
    )
    args = parser.parse_args()
    if args.include_stored_content and not args.fetch:
        parser.error("--include-stored-content requires --fetch")
    load_dotenv(Path(__file__).resolve().parent / ".env")
    try:
        output = export_run(
            args.log_dir, fetch=args.fetch, include_content=args.include_stored_content
        )
    except ValueError as error:
        parser.error(str(error))
    print(f"Exported calls to {output}. Original Inspect logs were not modified.")


if __name__ == "__main__":
    main()
