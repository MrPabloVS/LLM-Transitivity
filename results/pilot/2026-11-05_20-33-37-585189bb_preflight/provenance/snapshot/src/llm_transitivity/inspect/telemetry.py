"""Adapt OpenRouter capture and metadata collection to Inspect solvers."""

import asyncio
import os

from inspect_ai.model import get_model
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.solver import generate as generate_solver

from llm_transitivity.openrouter import capture
from llm_transitivity.openrouter.client import (
    captured_generation_ids,
    generation_details,
)


@solver
def collect_openrouter_details() -> Solver:
    """Attach full generation metadata to the Inspect sample after generation."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        if not str(state.model).startswith("openrouter/"):
            return state
        ids = captured_generation_ids(state.metadata.get("openrouter_http_calls", []))
        if state.output.response_id:
            ids.append(state.output.response_id)
        for generation_id in dict.fromkeys(ids or [None]):
            record = await asyncio.to_thread(
                generation_details, generation_id, os.environ.get("OPENROUTER_API_KEY")
            )
            state.metadata.setdefault("openrouter_calls", []).append(record)
        return state

    return solve


def _install_capture() -> None:
    # The SDK client type is supplied by Inspect, avoiding httpx/httpx2 mixing.
    client = get_model().api.http_client
    if not getattr(client, "_llm_transitivity_capture", False):
        client.event_hooks["request"].append(capture.capture_request)
        client.event_hooks["response"].append(capture.capture_response)
        client._llm_transitivity_capture = True


@solver
def generate_with_capture() -> Solver:
    """Bound transport capture to one generation, including failed attempts."""
    generation = generate_solver()

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        if not str(state.model).startswith("openrouter/"):
            return await generation(state, generate)
        records = []
        state.metadata["openrouter_http_calls"] = records
        with capture.capture_scope(records):
            _install_capture()
            return await generation(state, generate)

    return solve
