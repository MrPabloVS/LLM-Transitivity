"""Keep known zero costs when phase records overlap."""

import json

from llm_transitivity.analysis.pilot2_report import write_report


def test_report_deduplicates_without_replacing_known_cost_with_unknown(tmp_path):
    reviews = {
        "preflight": {"models": {}, "generations": {"same": {"cost_usd": 0}}},
        "coverage": {
            "models": {},
            "generations": {"same": {"cost_usd": None}, "missing": {"cost_usd": None}},
        },
    }
    path = write_report(tmp_path, tmp_path, {"campaign_id": "test"}, reviews)
    report = json.loads(path.read_text())
    assert report["known_cost_usd"] == 0
    assert report["missing_cost_ids"] == ["missing"]
    assert report["generation_attempts"] == 2
    assert "Pilot 2.0" in path.with_suffix(".md").read_text()
