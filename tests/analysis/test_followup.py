"""Check direct load gates and internal provider failures."""

import pytest

from llm_transitivity.analysis.followup import (
    failed_attempt,
    load_gate,
    peak_concurrency,
)


@pytest.mark.parametrize(
    "call,failed",
    [
        ({}, True),
        ({"http_status": 429}, True),
        ({"http_status": 502}, True),
        (
            {"http_status": 200, "response_body": {"json": {"error": {"code": 502}}}},
            True,
        ),
        (
            {
                "http_status": 200,
                "response_body": {"json": {"id": "id", "choices": [{}]}},
            },
            False,
        ),
    ],
)
def test_provider_body_errors_count_even_with_http_200(call, failed):
    assert failed_attempt(call) is failed


def test_direct_gate_does_not_invent_a_speedup_requirement():
    value = {"faults": [], "failed_attempt_rate": 0.05, "peak_samples": 64}
    assert load_gate(value, 64) == []
    for changed in [
        {"faults": [{"kind": "unknown usage"}]},
        {"failed_attempt_rate": None},
        {"failed_attempt_rate": 0.05001},
        {"peak_samples": 63},
    ]:
        assert load_gate({**value, **changed}, 64)


def test_effective_concurrency_counts_overlap_without_double_counting_ties():
    assert peak_concurrency([(0, 1), (1, 2)]) == 1
    assert peak_concurrency([(0, 2), (1, 3), (2, 4)]) == 2
    assert peak_concurrency([]) == 0
