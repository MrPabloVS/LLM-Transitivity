import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from llm_transitivity.openrouter import client as telemetry


def response(status=200, payload=None, text=""):
    obj = Mock(
        status_code=status,
        headers={"x-request-id": "lookup", "set-cookie": "secret-cookie"},
        text=text,
    )
    if text:
        obj.json.side_effect = ValueError("not JSON")
    else:
        obj.json.return_value = (
            payload if payload is not None else {"data": {"id": "gen-test"}}
        )
    return obj


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


def test_transport_capture_and_export_with_mocked_openrouter(tmp_path, monkeypatch):
    import httpx2
    from inspect_ai import eval
    from inspect_ai.model._providers.openai_compatible import OpenAICompatibleAPI
    from openai import DefaultAsyncHttpxClient

    from llm_transitivity.inspect.tasks import hs_zero_shot
    from llm_transitivity.runs.export import export_log

    count = 0

    async def handle(request):
        nonlocal count
        count += 1
        if count == 1:
            return httpx2.Response(
                503,
                json={"id": "gen-retry", "error": {"message": "busy", "code": 503}},
                headers={"x-request-id": "req-retry"},
            )
        return httpx2.Response(
            200,
            json={
                "id": "gen-success",
                "created": 0,
                "object": "chat.completion",
                "model": "openai/gpt-4o-mini",
                "provider": "OpenAI",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "yes"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 50,
                    "completion_tokens": 1,
                    "total_tokens": 51,
                    "cost": 0.0001,
                    "completion_tokens_details": {"reasoning_tokens": 0},
                },
                "new_unknown_field": {"zero": 0, "null": None},
            },
            headers={"x-request-id": "req-success", "set-cookie": "private-cookie"},
        )

    monkeypatch.setattr(
        OpenAICompatibleAPI,
        "_create_http_client",
        lambda self: DefaultAsyncHttpxClient(transport=httpx2.MockTransport(handle)),
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-secret")
    monkeypatch.setattr(
        telemetry.requests,
        "get",
        Mock(
            return_value=response(
                payload={
                    "data": {
                        "provider_name": "OpenAI",
                        "total_cost": 0.0001,
                        "native_tokens_reasoning": 0,
                        "unknown_generation_field": "preserved",
                    }
                }
            )
        ),
    )
    logs = eval(
        hs_zero_shot(
            "pilot/HS_HF_FU_20", root=str(Path(__file__).resolve().parents[1])
        ),
        model="openrouter/openai/gpt-4o-mini",
        model_args={"stream": False},
        limit=1,
        log_dir=str(tmp_path),
        display="none",
        log_model_api=True,
        max_retries=2,
    )
    assert logs[0].status == "success"
    metadata = logs[0].samples[0].metadata
    calls = metadata["openrouter_http_calls"]
    assert [call["http_status"] for call in calls] == [503, 200]
    assert calls[1]["response_body"]["json"]["new_unknown_field"] == {
        "zero": 0,
        "null": None,
    }
    assert (
        calls[1]["request_body"]["json"]["messages"][0]["content"]
        == "Answer only with 'yes' or 'no' and nothing else."
    )
    assert {x["generation_id"] for x in metadata["openrouter_calls"]} == {
        "gen-retry",
        "gen-success",
    }
    assert "test-secret" not in json.dumps(metadata)
    assert "private-cookie" not in json.dumps(metadata)
    path = next(Path(tmp_path).glob("*.eval"))
    exported = export_log(path)
    assert exported[0]["generation_id"] == "gen-success"
    assert (
        exported[0]["sample_metadata"]["openrouter_calls"][0]["reported"][
            "native_tokens_reasoning"
        ]
        == 0
    )
    refreshed = export_log(path, fetch=True)
    assert {item["generation_id"] for item in refreshed[0]["generation_lookups"]} == {
        "gen-retry",
        "gen-success",
    }
