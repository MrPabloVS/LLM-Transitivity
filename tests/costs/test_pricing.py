"""Published prices do not certify endpoint access or availability."""

from unittest.mock import Mock

import pytest

from llm_transitivity.costs import pricing
from llm_transitivity.domain.config import MODEL_SPECS

MODEL = next(model for model in MODEL_SPECS if model.provider == "openai/flex")
PRICES = {"prompt": "0.00000005", "completion": "0.00000025"}


@pytest.mark.parametrize("status", [0, -2, None])
def test_quote_uses_exact_endpoint_without_interpreting_status(monkeypatch, status):
    response = Mock()
    response.json.return_value = {
        "data": {
            "endpoints": [
                {"tag": "openai", "status": 0, "pricing": {"prompt": "999"}},
                {"tag": MODEL.provider, "status": status, "pricing": PRICES},
            ]
        }
    }
    get = Mock(return_value=response)
    monkeypatch.setattr(pricing.requests, "get", get)
    url, result = pricing.provider_quote(MODEL)
    assert result == PRICES
    get.assert_called_once_with(url, timeout=30)
    response.raise_for_status.assert_called_once_with()


@pytest.mark.parametrize("matches", [0, 2])
def test_quote_rejects_missing_or_duplicate_selected_endpoint(monkeypatch, matches):
    response = Mock()
    response.json.return_value = {
        "data": {
            "endpoints": [
                {"tag": MODEL.provider, "pricing": PRICES} for _ in range(matches)
            ]
            + [{"tag": "openai", "status": 0, "pricing": PRICES}]
        }
    }
    monkeypatch.setattr(pricing.requests, "get", Mock(return_value=response))
    with pytest.raises(
        ValueError, match="exactly one published endpoint for openai/flex"
    ):
        pricing.provider_quote(MODEL)
