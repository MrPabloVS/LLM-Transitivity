"""Estimate phase counts from verified inputs without constructing tasks."""

import importlib

from tests.paths import PROJECT_ROOT


def test_followup_quotes_count_each_model_phase(monkeypatch):
    module = importlib.import_module("llm_transitivity.costs.estimate")
    monkeypatch.setattr(
        module,
        "provider_quote",
        lambda model: (
            "https://example.test/quote",
            {"prompt": "0.000001", "completion": "0.000005"},
        ),
    )
    report = module.estimate(PROJECT_ROOT, profile="haiku", followup=True)
    assert report["planned_responses"] == 2382
    assert report["pilot_cases_per_model"] == 540
    assert report["input_proxy_tokens_per_model"] is None
    assert {r["cases"] for r in report["quotes"]} == {217, 757}
    assert sum(r["cases"] for r in report["quotes"]) == 2382
