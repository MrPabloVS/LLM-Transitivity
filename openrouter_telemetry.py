"""Compatibility exports for OpenRouter evidence capture."""

from llm_transitivity.inspect.telemetry import (
    capture_openrouter_http,
    collect_openrouter_details,
)
from llm_transitivity.openrouter.capture import capture_request, capture_response
from llm_transitivity.openrouter.client import (
    SECRET_FIELDS,
    body_snapshot,
    fetch_endpoint,
    generation_details,
    redact,
)

__all__ = [
    "SECRET_FIELDS",
    "body_snapshot",
    "capture_openrouter_http",
    "capture_request",
    "capture_response",
    "collect_openrouter_details",
    "fetch_endpoint",
    "generation_details",
    "redact",
]
