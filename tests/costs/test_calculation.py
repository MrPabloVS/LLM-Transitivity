"""Check cost arithmetic without HTTP or the evaluation framework."""

from decimal import Decimal

from llm_transitivity.costs.calculation import generation_cost


def test_cost_includes_failed_attempts_and_request_charges():
    assert (
        generation_cost(
            1000000,
            1000,
            3,
            cases=1000,
            input_price=Decimal("0.000001"),
            output_price=Decimal("0.000002"),
            request_price=Decimal("0.0001"),
        )
        == 9.3
    )


def test_no_generated_tokens_still_accounts_for_input():
    assert (
        generation_cost(
            1000000,
            0,
            cases=1000,
            input_price=Decimal("0.000001"),
            output_price=Decimal("0.000002"),
            request_price=Decimal(0),
        )
        == 1
    )
