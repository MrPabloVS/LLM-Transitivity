"""Verify Haiku reasoning controls through the installed Inspect and OpenAI SDKs."""

import json

import pytest
from inspect_ai import eval as inspect_eval
from inspect_ai.model import get_model

from llm_transitivity.inspect import telemetry
from llm_transitivity.inspect.flow import build_pilot_spec
from tests.paths import PROJECT_ROOT


@pytest.mark.parametrize(
    "identifier",
    [
        "anthropic/claude-haiku-4.5",
        "anthropic/claude-haiku-5.5",
        "anthropic/claude-sonnet-5.5",
        "google/gemini-3.5-flash-lite",
    ],
)
def test_model_reasoning_controls_reach_real_sdk_wire(
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
    spec = build_pilot_spec(
        PROJECT_ROOT,
        profile="pilot2"
        if identifier in {"anthropic/claude-sonnet-5.5", "google/gemini-3.5-flash-lite"}
        else "haiku",
        preflight=True,
    )
    task = next(t for t in spec.tasks if t.metadata["requested_model"] == identifier)
    backend = get_model(
        task.model.name,
        memoize=False,
        config=task.model.config,
        **task.model.model_args,
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
    enabled = identifier in {
        "anthropic/claude-sonnet-5.5",
        "google/gemini-3.5-flash-lite",
    }
    assert requests[0]["reasoning"]["enabled"] is enabled
    effort = (
        "low"
        if "sonnet-5.5" in identifier
        else "minimal"
        if "gemini-3.5" in identifier
        else "medium"
    )
    if identifier.endswith("5.5") or "gemini-3.5" in identifier:
        assert requests[0]["reasoning"]["effort"] == effort
    assert requests[0]["provider"]["only"] == (
        ["google-ai-studio/flex"] if "gemini" in identifier else ["anthropic"]
    )
    assert (
        result.samples[0].metadata["openrouter_http_calls"][0]["response_body"]["json"][
            "usage"
        ]["cost"]
        == 0
    )


@pytest.mark.parametrize(
    "filtered_mode",
    [
        None,
        "missing",
        "empty",
        "wrong_tier",
        "reasoning",
        "http_error",
        "pilot2",
        "catalog_changed",
    ],
)
def test_preflight_auditor_accepts_complete_sdk_captures_for_six_models(
    tmp_path, monkeypatch, filtered_mode
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
        if filtered_mode == "http_error" and identifier.endswith("haiku-5.5"):
            return httpx2.Response(
                400, json={"error": {"code": 400, "message": "Reasoning is mandatory"}}
            )
        provider = {
            "openai": "OpenAI",
            "anthropic": "Anthropic",
            "google": "Google AI Studio",
        }[identifier.split("/")[0]]
        payload = {
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
        }
        if filtered_mode and identifier.endswith("haiku-5.5"):
            payload["choices"][0].update(
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "refusal": "" if filtered_mode == "empty" else "Filtered",
                    },
                    "finish_reason": "content_filter",
                }
            )
            payload["service_tier"] = "wrong" if filtered_mode == "wrong_tier" else None
            payload.pop("usage")
            if filtered_mode == "reasoning":
                payload["usage"] = {
                    "prompt_tokens": 10,
                    "completion_tokens": 1,
                    "total_tokens": 11,
                    "completion_tokens_details": {"reasoning_tokens": 1},
                }
        return httpx2.Response(200, json=payload)

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
    spec = build_pilot_spec(
        PROJECT_ROOT,
        profile="pilot2" if filtered_mode in {"pilot2", "catalog_changed"} else "haiku",
        preflight=True,
    )
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
                fail_on_error=False,
            )[0].status
            == "success"
        )
    if filtered_mode == "catalog_changed":
        from dataclasses import replace

        from llm_transitivity.analysis import followup as reviewing
        from llm_transitivity.domain.config import profile_models

        changed = tuple(
            replace(m, reasoning_enabled=False, reasoning_effort="high")
            for m in profile_models("pilot2")
        )
        monkeypatch.setattr(reviewing, "profile_models", lambda profile: changed)
    report = review_phase(tmp_path, phase, dump_spec(spec))
    assert report["technical_pass"] is (
        filtered_mode in (None, "missing", "empty", "pilot2", "catalog_changed")
    )
    assert len(report["models"]) == 6
    assert all(
        v["samples"] == 1 and v["known_cost_usd"] == 0
        for v in report["models"].values()
    )

    if filtered_mode in {"pilot2", "catalog_changed"}:
        assert not any(v["faults"] for v in report["models"].values())
        return
    haiku = report["models"]["anthropic/claude-haiku-5.5"]
    if filtered_mode == "http_error":
        assert haiku["faults"]
        assert haiku["failed_attempts"] == 1
        assert haiku["unidentified_attempts"] == 1
        assert not haiku["filtered_uids"]
        return
    if filtered_mode:
        assert len(haiku["filtered_uids"]) == 1
        assert haiku["missing_cost_ids"]
        assert {v["kind"] for v in haiku["unverified_fields"]} >= {
            "final reported cost"
        }
        if filtered_mode in ("missing", "empty"):
            assert len(haiku["unverified_fields"]) == 3
            assert not haiku["faults"]
        else:
            assert haiku["faults"]
