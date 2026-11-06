"""Check denominators, unique charges, and fixed-capacity projections."""

import pytest

from llm_transitivity.analysis.calculations import (
    cost_projection,
    interval_union,
    measures,
    merge_generation,
    percentile90,
    queue_seconds,
)


def test_reused_charge_and_missing_zero_cost_are_distinct():
    ledger = {}
    quote = {"model": "model", "source": "captured_response", "cost_usd": 0}
    merge_generation(ledger, "zero", quote)
    merge_generation(ledger, "zero", {**quote, "source": "generation_lookup"})
    merge_generation(ledger, "unknown", {**quote, "cost_usd": None})
    assert len(ledger) == 2
    assert ledger["zero"]["cost_usd"] == 0
    assert ledger["unknown"]["cost_usd"] is None
    assert len(ledger["zero"]["observations"]) == 2


def test_conflicting_quotes_are_retained_without_double_counting():
    ledger = {}
    merge_generation(
        ledger, "id", {"model": "m", "source": "generation_lookup", "cost_usd": 1}
    )
    merge_generation(
        ledger, "id", {"model": "m", "source": "captured_response", "cost_usd": 2}
    )
    assert ledger["id"]["cost_usd"] == 2
    assert ledger["id"]["cost_conflicts"] == [{"previous": 1, "observed": 2}]
    with pytest.raises(ValueError, match="different models"):
        merge_generation(ledger, "id", {"model": "other"})


def test_stratum_costs_use_their_populations_and_do_not_impute_missing_values():
    rows = [
        {"stratum": "a", "final_cost_usd": 0},
        {"stratum": "b", "final_cost_usd": 2},
    ]
    result = cost_projection(rows, {"a": 500, "b": 100})
    assert result["central_usd"] == 200
    assert result["three_attempts_usd"] == 600
    rows[0]["final_cost_usd"] = None
    assert cost_projection(rows, {"a": 500, "b": 100})["central_usd"] is None
    with pytest.raises(ValueError, match="strata"):
        cost_projection(rows, {"a": 500})


def test_agreement_does_not_hide_nonresponses_or_format_violations():
    rows = [
        {"after": {"status": status, "value": value, "format_compliant": strict}}
        for status, value, strict in [
            ("answered", "C", True),
            ("answered", "I", False),
            ("invalid_format", "N", False),
        ]
    ]
    assert measures(rows) == {
        "samples": 3,
        "categories": {"answered": 2, "invalid_format": 1},
        "correct": 1,
        "incorrect": 1,
        "answered": 2,
        "agreement": 0.5,
        "coverage": 2 / 3,
        "format_compliant": 1,
        "format_rate": 1 / 3,
    }
    assert measures([])["agreement"] is None


def test_queue_keeps_capacity_and_does_not_charge_overlap_twice():
    assert queue_seconds([3, 1, 2], 2) == 3
    assert queue_seconds([], 16) == 0
    assert interval_union([(0, 4), (1, 2), (3, 5), (10, 12)]) == 7
    assert interval_union([]) == 0
    assert percentile90([1, 2, 3, 4, 5]) == 4.6
    assert percentile90([0]) == 0
    with pytest.raises(ValueError):
        queue_seconds([1], 0)


def test_whole_second_task_times_do_not_exclude_fractional_sample_times():
    from llm_transitivity.analysis.calculations import task_overhead

    assert task_overhead([(10.1, 14.75, 4.65)], 10, 14, 16) == 0
    assert task_overhead([(10.1, 14.75, 2)], 10, 14, 16) == 2
    assert task_overhead([(1, 3, 2)], 10, 14, 16) is None
    assert task_overhead([(10.1, 15.1, 5)], 10, 14, 16) is None
