"""Quote all full-corpus cases without generation requests."""

import importlib

from tests.paths import PROJECT_ROOT


def test_full_estimate_uses_full_inputs_and_six_fixed_models(monkeypatch):
    module = importlib.import_module("llm_transitivity.costs.estimate")
    monkeypatch.setattr(
        module,
        "provider_quote",
        lambda model: (
            "mock://quote",
            {"prompt": "0.000001", "completion": "0.000005"},
        ),
    )
    report = module.estimate(PROJECT_ROOT, profile="pilot3", full=True)
    assert report["planned_responses"] == 324000
    assert report["full_cases_per_model"] == 54000
    assert report["pilot_cases_per_model"] == 540
    assert report["scope"] == "full-corpus"
    assert all(row["cases"] == 54000 for row in report["quotes"])
