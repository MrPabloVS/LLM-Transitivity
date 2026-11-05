"""Check the six approved routes through the real SDK with mocked HTTP."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from inspect_ai import eval
from inspect_ai.model import get_model

from llm_transitivity.inspect.flow import build_pilot_spec
from llm_transitivity.openrouter import client

ROOT = Path(__file__).resolve().parents[1]
ROUTES = [
    ("openai/gpt-4o-mini", "openai", "default"),
    ("openai/gpt-6-luna", "openai/flex", "flex"),
    ("anthropic/claude-sonnet-4.5", "anthropic", "default"),
    ("anthropic/claude-sonnet-5", "anthropic", "default"),
    ("google/gemini-2.5-flash-lite", "google-ai-studio/flex", "flex"),
    ("google/gemini-3.1-flash-lite", "google-ai-studio/flex", "flex"),
]


@pytest.fixture(scope="module")
def spec():
    return build_pilot_spec(ROOT, preflight=True)


@pytest.mark.parametrize("model,endpoint,tier", ROUTES)
def test_route_reaches_http_and_keeps_observed_identifiers(
    spec, model, endpoint, tier, tmp_path, monkeypatch
):
    import httpx2
    from inspect_ai.model._providers.openai_compatible import OpenAICompatibleAPI
    from openai import DefaultAsyncHttpxClient

    flow_task = next(t for t in spec.tasks if t.metadata["requested_model"] == model)
    assert flow_task.metadata["requested_provider"] == endpoint
    assert flow_task.metadata["requested_service_tier"] == tier
    assert flow_task.metadata["actual_service_tier"] is None
    assert flow_task.metadata["service_tier_verified"] is False
    assert f"service_tier:{tier}" in flow_task.tags
    assert spec.options.metadata["requested_routing"][model]["service_tier"] == tier
    requests = []

    async def handle(request):
        body = json.loads(request.content)
        requests.append(body)
        return httpx2.Response(
            200,
            json={
                "id": "gen-route-test",
                "created": 0,
                "object": "chat.completion",
                "model": model,
                "provider": endpoint.split("/")[0],
                "service_tier": tier,
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
                },
            },
        )

    monkeypatch.setattr(
        OpenAICompatibleAPI,
        "_create_http_client",
        lambda self: DefaultAsyncHttpxClient(transport=httpx2.MockTransport(handle)),
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-routing-secret")
    reported = {
        "provider_name": endpoint.split("/")[0],
        "model": model,
        "model_permaslug": f"{model}-version-test",
        "service_tier": tier,
        "provider_responses": [
            {"endpoint_id": "endpoint-test", "provider_name": endpoint.split("/")[0]}
        ],
        "native_tokens_reasoning": 0,
    }
    response = Mock(status_code=200, headers={})
    response.json.return_value = {"data": reported}
    monkeypatch.setattr(client.requests, "get", Mock(return_value=response))
    backend = get_model(
        flow_task.model.name,
        config=flow_task.model.config,
        **flow_task.model.model_args,
    )
    log = eval(
        flow_task.factory(**flow_task.args),
        model=backend,
        limit=1,
        log_dir=str(tmp_path),
        display="none",
    )[0]
    assert log.status == "success"
    assert len(requests) == 1
    request = requests[0]
    assert request["model"] == model
    assert request["service_tier"] == tier
    assert request["provider"] == {
        "only": [endpoint],
        "allow_fallbacks": False,
        "require_parameters": True,
    }
    if model != "openai/gpt-4o-mini":
        assert request["reasoning"]["enabled"] is False
    metadata = log.samples[0].metadata
    assert (
        metadata["openrouter_http_calls"][0]["response_body"]["json"]["service_tier"]
        == tier
    )
    details = metadata["openrouter_calls"][0]["reported"]
    assert details["service_tier"] == tier
    assert details["model_permaslug"] == f"{model}-version-test"
    assert details["provider_responses"][0]["endpoint_id"] == "endpoint-test"
