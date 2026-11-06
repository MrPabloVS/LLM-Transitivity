"""Capture redacted transport attempts without depending on Inspect."""

import time
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime

from llm_transitivity.openrouter.client import body_snapshot, redact

_capture = ContextVar("openrouter_call_capture", default=None)


async def capture_request(request) -> None:
    context = _capture.get()
    if context is None or request.url.host != "openrouter.ai":
        return
    key = request.headers.get("authorization", "").removeprefix("Bearer ")
    record = {
        "http_attempt": len(context) + 1,
        "request_started_utc": datetime.now(UTC).isoformat(),
        "method": request.method,
        "url": str(request.url),
        "request_headers": redact(dict(request.headers), key),
        "request_body": body_snapshot(await request.aread(), key),
        "response_status": "not received",
    }
    request.extensions["llm_transitivity_capture"] = (record, time.monotonic())
    context.append(record)


async def capture_response(response) -> None:
    captured = response.request.extensions.get("llm_transitivity_capture")
    if captured is None:
        return
    record, started = captured
    key = response.request.headers.get("authorization", "").removeprefix("Bearer ")
    record.update(
        {
            "response_received_utc": datetime.now(UTC).isoformat(),
            "http_status": response.status_code,
            "response_headers": redact(dict(response.headers), key),
            "response_body": body_snapshot(await response.aread(), key),
            "response_status": "received",
            "http_seconds": time.monotonic() - started,
        }
    )


@contextmanager
def capture_scope(records: list):
    """Restore the previous context on success, error or cancellation."""
    token = _capture.set(records)
    try:
        yield
    finally:
        _capture.reset(token)
