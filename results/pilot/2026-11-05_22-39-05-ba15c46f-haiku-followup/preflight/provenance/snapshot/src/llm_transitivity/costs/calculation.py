"""Calculate token and request costs without external dependencies."""

from decimal import Decimal


def generation_cost(
    input_tokens: int,
    output_per_case: int,
    multiplier: int = 1,
    *,
    cases: int,
    input_price: Decimal,
    output_price: Decimal,
    request_price: Decimal,
) -> float:
    """Include input, output and per-request charges for every planned attempt."""
    return float(
        (
            input_tokens * input_price
            + cases * (output_per_case * output_price + request_price)
        )
        * multiplier
    )
