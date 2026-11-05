"""Query OpenRouter metadata and retain its complete redacted responses."""

import json
import time
from datetime import UTC, datetime

import requests

SECRET_FIELDS = {
    "authorization",
    "proxy-authorization",
    "api_key",
    "apikey",
    "cookie",
    "set-cookie",
    "x-api-key",
}


def redact(value, api_key: str = ""):
    """Keep unknown data fields while removing credentials and session cookies."""
    if isinstance(value, dict):
        return {
            key: "[REDACTED]"
            if key.lower().replace("_", "-")
            in {name.replace("_", "-") for name in SECRET_FIELDS}
            else redact(item, api_key)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item, api_key) for item in value]
    if isinstance(value, str) and api_key:
        return value.replace(api_key, "[REDACTED]")
    return value


def body_snapshot(content: bytes, api_key: str) -> dict:
    try:
        return {"json": redact(json.loads(content), api_key)}
    except ValueError, UnicodeDecodeError:
        return {"text": redact(content.decode("utf-8", errors="replace"), api_key)}


def fetch_endpoint(generation_id: str, api_key: str, endpoint: str, get=None) -> dict:
    """Retain every lookup attempt, including unavailable or non-JSON responses."""
    get = get or requests.get
    attempts = []
    for attempt in range(3):
        started = time.monotonic()
        record = {"fetched_at_utc": datetime.now(UTC).isoformat()}
        try:
            response = get(
                f"https://openrouter.ai/api/v1/{endpoint}",
                params={"id": generation_id},
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15,
                allow_redirects=False,
            )
            record.update(
                {
                    "http_status": response.status_code,
                    "response_headers": redact(dict(response.headers), api_key),
                }
            )
            try:
                record["response_json"] = redact(response.json(), api_key)
            except ValueError, requests.exceptions.JSONDecodeError:
                record["response_text"] = redact(response.text, api_key)
            retry = response.status_code in {404, 429, 500, 502, 503, 504}
        except requests.RequestException as error:
            record["transport_error_type"] = type(error).__name__
            retry = True
        record["lookup_seconds"] = time.monotonic() - started
        attempts.append(record)
        if not retry or attempt == 2:
            break
        time.sleep(0.25 * (attempt + 1))
    last = attempts[-1]
    payload = last.get("response_json")
    ok = (
        last.get("http_status") == 200
        and isinstance(payload, dict)
        and isinstance(payload.get("data"), dict)
    )
    return {
        "endpoint": endpoint,
        "status": "available" if ok else "unavailable",
        "attempts": attempts,
    }


def captured_generation_ids(calls: list[dict]) -> list[str]:
    """Read IDs in capture order; callers retain their own deduplication policy."""
    ids = []
    for call in calls:
        payload = call.get("response_body", {}).get("json")
        if isinstance(payload, dict) and isinstance(payload.get("id"), str):
            ids.append(payload["id"])
    return ids


def generation_details(
    generation_id: str | None,
    api_key: str | None,
    *,
    include_content: bool = False,
    get=None,
) -> dict:
    record = {"generation_id": generation_id, "lookup_status": "not attempted"}
    if not generation_id:
        return record | {"lookup_status": "missing generation id"}
    if not api_key:
        return record | {"lookup_status": "missing credentials"}
    record["generation"] = fetch_endpoint(generation_id, api_key, "generation", get)
    record["lookup_status"] = record["generation"]["status"]
    if include_content:
        record["stored_content"] = fetch_endpoint(
            generation_id, api_key, "generation/content", get
        )
    else:
        record["stored_content"] = {
            "status": "not requested; may require management-key access and stored content"
        }
    if record["generation"]["status"] == "available":
        data = record["generation"]["attempts"][-1]["response_json"]["data"]
        record["reported"] = {
            key: data.get(key)
            for key in [
                "provider_name",
                "endpoint_id",
                "model_permaslug",
                "provider_responses",
                "model",
                "request_id",
                "upstream_id",
                "total_cost",
                "native_tokens_prompt",
                "native_tokens_completion",
                "native_tokens_reasoning",
                "native_tokens_cached",
                "finish_reason",
                "native_finish_reason",
                "latency",
                "generation_time",
                "moderation_latency",
                "is_byok",
                "service_tier",
                "data_region",
            ]
        }
    return record
