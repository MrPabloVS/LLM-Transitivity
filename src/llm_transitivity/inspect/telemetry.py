"""Adapt OpenRouter capture and metadata collection to Inspect solvers."""

import asyncio
import os

from inspect_ai.model import get_model
from inspect_ai.solver import Generate, Solver, TaskState, solver

from llm_transitivity.openrouter import capture
from llm_transitivity.openrouter.client import generation_details


@solver
def capture_openrouter_http() -> Solver:
    """Capture each transport attempt, including SDK and Inspect retry responses."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        if not str(state.model).startswith("openrouter/"):
            return state
        records = []
        state.metadata["openrouter_http_calls"] = records
        capture._capture.set(records)
        # The SDK client type is supplied by Inspect, avoiding httpx/httpx2 mixing.
        client = get_model().api.http_client
        if not getattr(client, "_llm_transitivity_capture", False):
            client.event_hooks["request"].append(capture.capture_request)
            client.event_hooks["response"].append(capture.capture_response)
            client._llm_transitivity_capture = True
        return state

    return solve


@solver
def collect_openrouter_details() -> Solver:
    """Attach full generation metadata to the Inspect sample after generation."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        if not str(state.model).startswith("openrouter/"):
            return state
        ids = []
        for call in state.metadata.get("openrouter_http_calls", []):
            payload = call.get("response_body", {}).get("json")
            if isinstance(payload, dict) and isinstance(payload.get("id"), str):
                ids.append(payload["id"])
        if state.output.response_id:
            ids.append(state.output.response_id)
        for generation_id in dict.fromkeys(ids or [None]):
            record = await asyncio.to_thread(
                generation_details, generation_id, os.environ.get("OPENROUTER_API_KEY")
            )
            state.metadata.setdefault("openrouter_calls", []).append(record)
        capture._capture.set(None)
        return state

    return solve
