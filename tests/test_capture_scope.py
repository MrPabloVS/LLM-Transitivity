"""Check cleanup and sample isolation across generation outcomes."""

import asyncio
from unittest.mock import Mock

import pytest
from inspect_ai.solver import TaskState

from llm_transitivity.inspect import telemetry
from llm_transitivity.openrouter import capture


def state(number):
    return TaskState(
        model="openrouter/openai/gpt-4o-mini",
        sample_id=number,
        epoch=1,
        input="test",
        messages=[],
    )


@pytest.mark.parametrize(
    "error", [None, RuntimeError("failed"), asyncio.CancelledError()]
)
def test_generation_restores_prior_context_and_keeps_attempts(monkeypatch, error):
    async def generation(sample, _):
        capture._capture.get().append({"attempt": sample.sample_id})
        if error is not None:
            raise error
        return sample

    monkeypatch.setattr(telemetry, "generate_solver", lambda: generation)
    monkeypatch.setattr(telemetry, "_install_capture", Mock())

    async def run():
        prior = []
        with capture.capture_scope(prior):
            sample = state(1)
            solver = telemetry.generate_with_capture()
            if error is None:
                assert await solver(sample, None) is sample
            else:
                with pytest.raises(type(error)):
                    await solver(sample, None)
            assert capture._capture.get() is prior
            assert prior == []
            assert sample.metadata["openrouter_http_calls"] == [{"attempt": 1}]
        assert capture._capture.get() is None

    asyncio.run(run())


def test_concurrent_samples_keep_separate_attempts(monkeypatch):
    async def generation(sample, _):
        records = capture._capture.get()
        records.append({"sample": sample.sample_id, "attempt": 1})
        await asyncio.sleep(0)
        assert capture._capture.get() is records
        records.append({"sample": sample.sample_id, "attempt": 2})
        return sample

    monkeypatch.setattr(telemetry, "generate_solver", lambda: generation)
    monkeypatch.setattr(telemetry, "_install_capture", Mock())

    async def run():
        samples = [state(1), state(2)]
        solver = telemetry.generate_with_capture()
        await asyncio.gather(*(solver(sample, None) for sample in samples))
        for sample in samples:
            assert sample.metadata["openrouter_http_calls"] == [
                {"sample": sample.sample_id, "attempt": 1},
                {"sample": sample.sample_id, "attempt": 2},
            ]
        assert capture._capture.get() is None

    asyncio.run(run())
