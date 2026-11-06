"""Verify Haiku reasoning controls through the installed Inspect and OpenAI SDKs."""

import json

import pytest
from inspect_ai import eval as inspect_eval
from inspect_ai.model import get_model

from llm_transitivity.inspect import telemetry
from llm_transitivity.inspect.flow import build_pilot_spec
from tests.paths import PROJECT_ROOT


@pytest.mark.parametrize(
    "identifier", ["anthropic/claude-haiku-4.5", "anthropic/claude-haiku-5.5"]
)
def test_haiku_reasoning_disabled_reaches_real_sdk_wire(
    identifier, tmp_path, monkeypatch
):
    import httpx2
    from inspect_ai.model._providers.openai_compatible import OpenAICompatibleAPI
    from openai import DefaultAsyncHttpxClient

    requests = []

    async def handle(request):
        body = json.loads(request.content)
        requests.append(body)
        return httpx2.Response(
            200,
            json={
                "id": "gen-haiku-wire",
                "created": 0,
                "object": "chat.completion",
                "model": identifier,
                "provider": "Anthropic",
                "service_tier": "default",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "yes"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 1,
                    "total_tokens": 11,
                    "cost": 0,
                    "completion_tokens_details": {"reasoning_tokens": 0},
                },
            },
        )

    monkeypatch.setattr(
        OpenAICompatibleAPI,
        "_create_http_client",
        lambda self: DefaultAsyncHttpxClient(transport=httpx2.MockTransport(handle)),
    )
    monkeypatch.setattr(
        telemetry,
        "generation_details",
        lambda identifier, *args: {
            "generation_id": identifier,
            "lookup_status": "unavailable",
        },
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-haiku-fake-key")
    spec = build_pilot_spec(PROJECT_ROOT, profile="haiku", preflight=True)
    task = next(t for t in spec.tasks if t.metadata["requested_model"] == identifier)
    backend = get_model(
        task.model.name, config=task.model.config, **task.model.model_args
    )
    result = inspect_eval(
        task.factory(**task.args),
        model=backend,
        limit=1,
        log_dir=str(tmp_path),
        display="none",
    )[0]
    assert result.status == "success"
    assert len(requests) == 1
    assert requests[0]["reasoning"]["enabled"] is False
    if identifier.endswith("5.5"):
        assert requests[0]["reasoning"]["effort"] == "medium"
    assert requests[0]["provider"]["only"] == ["anthropic"]
    assert (
        result.samples[0].metadata["openrouter_http_calls"][0]["response_body"]["json"][
            "usage"
        ]["cost"]
        == 0
    )


def test_preflight_auditor_accepts_complete_sdk_captures_for_six_models(
    tmp_path, monkeypatch
):
    import httpx2
    from inspect_ai.model._providers.openai_compatible import OpenAICompatibleAPI
    from inspect_flow.api import dump_spec
    from openai import DefaultAsyncHttpxClient

    from llm_transitivity.analysis.followup import review_phase

    (tmp_path / "datasets").symlink_to(
        PROJECT_ROOT / "datasets", target_is_directory=True
    )
    phase = tmp_path / "phase"
    phase.mkdir()

    async def handle(request):
        body = json.loads(request.content)
        identifier = body["model"]
        provider = {
            "openai": "OpenAI",
            "anthropic": "Anthropic",
            "google": "Google AI Studio",
        }[identifier.split("/")[0]]
        return httpx2.Response(
            200,
            json={
                "id": "gen-" + identifier.replace("/", "-"),
                "created": 0,
                "object": "chat.completion",
                "model": identifier,
                "provider": provider,
                "service_tier": body["service_tier"],
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "yes"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 1,
                    "total_tokens": 11,
                    "cost": 0,
                    "completion_tokens_details": {"reasoning_tokens": 0},
                },
            },
        )

    monkeypatch.setattr(
        OpenAICompatibleAPI,
        "_create_http_client",
        lambda self: DefaultAsyncHttpxClient(transport=httpx2.MockTransport(handle)),
    )
    monkeypatch.setattr(
        telemetry,
        "generation_details",
        lambda identifier, *args: {
            "generation_id": identifier,
            "lookup_status": "unavailable",
        },
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-followup-audit-key")
    spec = build_pilot_spec(PROJECT_ROOT, profile="haiku", preflight=True)
    for flow_task in spec.tasks:
        task = flow_task.factory(**flow_task.args)
        task.metadata = flow_task.metadata
        backend = get_model(
            flow_task.model.name,
            memoize=False,
            config=flow_task.model.config,
            **flow_task.model.model_args,
        )
        assert (
            inspect_eval(
                task,
                model=backend,
                limit=1,
                log_dir=str(phase / "inspect"),
                display="none",
            )[0].status
            == "success"
        )
    report = review_phase(tmp_path, phase, dump_spec(spec))
    assert report["technical_pass"] is True
    assert len(report["models"]) == 6
    assert all(
        v["samples"] == 1 and v["known_cost_usd"] == 0
        for v in report["models"].values()
    )
