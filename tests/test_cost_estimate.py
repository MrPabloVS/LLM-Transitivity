from decimal import Decimal

from estimate_pilot_cost import generation_cost


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


def test_estimate_uses_saved_quotes_without_run_setup(monkeypatch):
    import json
    import subprocess
    import uuid
    from pathlib import Path
    from unittest.mock import Mock

    import pytest

    import estimate_pilot_cost
    import pilot_config
    from experiment_config import GENERATION_POLICY
    from prepare_pilot import digest

    root = Path(__file__).resolve().parents[1]
    saved_path = root / "docs/pilot_cost_estimate.json"
    saved_bytes = saved_path.read_bytes()
    saved = json.loads(saved_bytes)
    quotes = {row["source"]: row for row in saved["quotes"]}
    requested = []

    def get(url, *, timeout):
        requested.append(url)
        assert timeout == 30
        row = quotes[url]
        response = Mock()
        response.json.return_value = {
            "data": {
                "endpoints": [
                    {
                        "tag": row["provider"],
                        "status": 0,
                        "pricing": row["pricing_snapshot"],
                    },
                    {"tag": "other-provider", "status": 0, "pricing": {}},
                ]
            }
        }
        return response

    def forbidden(*args, **kwargs):
        raise AssertionError("Unexpected run setup or generation")

    original_check_output = subprocess.check_output

    def baseline_only(command, **kwargs):
        assert command[:1] == ["git"] and command[3] == "show", command
        return original_check_output(command, **kwargs)

    monkeypatch.setattr(estimate_pilot_cost.requests, "get", get)
    monkeypatch.setattr(estimate_pilot_cost.requests, "post", forbidden)
    monkeypatch.setattr(pilot_config, "build_pilot_spec", forbidden)
    monkeypatch.setattr(uuid, "uuid4", forbidden)
    monkeypatch.setattr(subprocess, "check_output", baseline_only)
    report = estimate_pilot_cost.estimate(root)
    assert set(requested) == set(quotes)
    assert len(requested) == 6
    assert report["planned_responses"] == 3240
    assert (
        report["input_proxy_tokens_per_model"] == saved["input_proxy_tokens_per_model"]
    )
    assert report["totals_usd"] == pytest.approx(saved["totals_usd"])
    assert report["output_token_limit"] == GENERATION_POLICY.max_output_tokens
    assert report["inspect_max_retries"] == GENERATION_POLICY.request_max_retries
    assert report["sdk_max_retries"] == GENERATION_POLICY.sdk_max_retries
    assert report["maximum_planned_attempts_per_response"] == 3
    assert report["experiment_config_sha256"] == digest(
        (root / "experiment_config.py").read_bytes()
    )
    assert saved_path.read_bytes() == saved_bytes


def test_estimator_import_does_not_load_evaluation_frameworks():
    import subprocess
    import sys

    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import estimate_pilot_cost; "
                "assert not {'inspect_ai', 'inspect_flow', 'pilot_config', "
                "'experiment_metadata', 'inspect_tasks'} & sys.modules.keys()"
            ),
        ],
        check=True,
    )
