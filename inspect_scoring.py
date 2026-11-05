"""Compatibility exports for Inspect scoring."""

from llm_transitivity.inspect.scoring import (
    response_rates,
    source_agreement,
    source_label_match,
)

__all__ = ["response_rates", "source_agreement", "source_label_match"]
