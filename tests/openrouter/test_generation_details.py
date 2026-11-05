"""Check complete metadata lookups, retries, and credential redaction."""

import json
from unittest.mock import Mock

import pytest
import requests

from llm_transitivity.openrouter import client as telemetry
from tests.support.http import response


def test_all_fields_null_and_zero_survive_and_secrets_are_removed():
    get = Mock(
        return_value=response(
            payload={
                "data": {
                    "id": "gen-test",
                    "native_tokens_reasoning": 0,
                    "total_cost": 0,
                    "future_field": {"unknown": None},
                    "authorization": "Bearer secret",
                    "message": "echo secret",
                }
            }
        )
    )
    record = telemetry.generation_details(
        "gen-test", "secret", include_content=True, get=get
    )
    raw = record["generation"]["attempts"][0]["response_json"]["data"]
    assert raw["future_field"] == {"unknown": None}
    assert raw["native_tokens_reasoning"] == raw["total_cost"] == 0
    assert record["reported"]["native_tokens_cached"] is None
    assert record["reported"]["service_tier"] is None
    assert record["reported"]["endpoint_id"] is None
    assert "secret" not in json.dumps(record)
    assert record["stored_content"]["status"] == "available"
    assert get.call_count == 2


def test_delayed_generation_is_retried_and_all_lookup_attempts_survive(monkeypatch):
    monkeypatch.setattr(telemetry.time, "sleep", lambda _: None)
    get = Mock(side_effect=[response(404, {"error": "pending"}), response()])
    record = telemetry.generation_details("gen-test", "key", get=get)
    assert record["lookup_status"] == "available"
    assert [r["http_status"] for r in record["generation"]["attempts"]] == [404, 200]


@pytest.mark.parametrize(
    "obj",
    [
        response(403, {"error": "forbidden"}),
        response(200, []),
        response(200, text="not JSON"),
    ],
)
def test_lookup_failure_does_not_invent_usage(obj):
    record = telemetry.generation_details("gen-test", "key", get=Mock(return_value=obj))
    assert record["lookup_status"] == "unavailable"
    assert "reported" not in record


def test_network_failure_is_recorded_without_exception_secrets(monkeypatch):
    monkeypatch.setattr(telemetry.time, "sleep", lambda _: None)
    get = Mock(side_effect=requests.Timeout("secret-url-key"))
    record = telemetry.generation_details("gen-test", "key", get=get)
    assert record["lookup_status"] == "unavailable"
    assert "secret-url" not in json.dumps(record)
    assert len(record["generation"]["attempts"]) == 3


def test_missing_ids_or_keys_do_not_call_endpoint():
    get = Mock(side_effect=AssertionError("unexpected request"))
    assert (
        telemetry.generation_details(None, "key", get=get)["lookup_status"]
        == "missing generation id"
    )
    assert (
        telemetry.generation_details("gen-test", None, get=get)["lookup_status"]
        == "missing credentials"
    )
