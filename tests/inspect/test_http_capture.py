"""Check HTTP capture and export through the real SDK with mocked transport."""

import json
from pathlib import Path
from unittest.mock import Mock

from llm_transitivity.openrouter import client as telemetry
from tests.paths import PROJECT_ROOT
from tests.support.http import response


def test_transport_capture_and_export_with_mocked_openrouter(tmp_path, monkeypatch):
    import httpx2
    from inspect_ai import eval
    from inspect_ai.model._providers.openai_compatible import OpenAICompatibleAPI
    from openai import DefaultAsyncHttpxClient

    from llm_transitivity.inspect.tasks import hs_zero_shot
    from llm_transitivity.runs.export import export_log

    count = 0
    router_metadata = {
        "requested": "openai/gpt-4o-mini",
        "region": None,
        "attempt": 1,
        "future_field": {"zero": 0},
    }

    async def handle(request):
        nonlocal count
        count += 1
        if count == 1:
            return httpx2.Response(
                503,
                json={
                    "id": "gen-retry",
                    "error": {"message": "busy", "code": 503},
                    "openrouter_metadata": router_metadata,
                },
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
        hs_zero_shot("pilot/HS_HF_FU_20", root=str(PROJECT_ROOT)),
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
    assert calls[0]["response_body"]["json"]["openrouter_metadata"] == router_metadata
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
    assert [item["generation_id"] for item in metadata["openrouter_calls"]] == [
        "gen-retry",
        "gen-success",
    ]
    assert "test-secret" not in json.dumps(metadata)
    assert "private-cookie" not in json.dumps(metadata)
    path = next(Path(tmp_path).glob("*.eval"))
    exported = export_log(path)
    assert exported[0]["generation_id"] == "gen-success"
    assert (
        exported[0]["sample_metadata"]["openrouter_http_calls"][0]["response_body"][
            "json"
        ]["openrouter_metadata"]
        == router_metadata
    )
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

    assert [item["generation_id"] for item in refreshed[0]["generation_lookups"]] == [
        "gen-success",
        "gen-retry",
    ]
