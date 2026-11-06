"""Reevaluate the complete saved pilot without network or evidence changes."""

import json
from pathlib import Path

import pytest
import requests

from llm_transitivity.analysis.pilot import analyze

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "results/pilot/2026-11-05_20-46-51-b3f8bb12"


def test_saved_pilot_reconciles_all_samples_and_the_48_extraction_changes(
    tmp_path, monkeypatch
):
    def forbidden(*args, **kwargs):
        raise AssertionError("Analysis must not request HTTP calls")

    monkeypatch.setattr(requests.sessions.Session, "request", forbidden)
    summary = analyze(
        ROOT,
        RUN,
        tmp_path / "analysis",
        ROOT / "results/analyses/pilot-generation-lookups-2026-11-05.json",
    )
    assert summary["additional_lookup_status"] == {"unavailable": 14}
    rows = [
        json.loads(line)
        for line in (tmp_path / "analysis/samples.jsonl").read_text().splitlines()
    ]
    assert summary["final_tasks"] == 108
    assert summary["final_samples"] == 3240
    assert summary["changed_samples"] == 48
    assert summary["before"]["answered"] == 3192
    assert summary["after"]["answered"] == 3240
    assert (
        summary["before"]["format_compliant"]
        == summary["after"]["format_compliant"]
        == 2745
    )
    assert all(
        row["model"].endswith("claude-sonnet-4.5") for row in rows if row["changed"]
    )
    assert sum(
        v["billing"]["known_cost_usd"] for v in summary["models"].values()
    ) == pytest.approx(1.60749575)
    assert summary["groups"]["all"]["central_cost_usd"] == pytest.approx(160.749575)
    assert (
        sum(len(v["billing"]["missing_cost_ids"]) for v in summary["models"].values())
        == 14
    )
    assert (
        sum(
            v["time_projection"]["clean_tasks_for_overhead"]
            for v in summary["models"].values()
        )
        == 107
    )
    with pytest.raises(FileExistsError):
        analyze(ROOT, RUN, tmp_path / "analysis")


@pytest.mark.parametrize("field", ["prompt", "target"])
def test_saved_inputs_must_match_verified_cases_even_when_uids_are_unchanged(field):
    from llm_transitivity.analysis.pilot import _validate_selection
    from llm_transitivity.domain.selection import stratum
    from llm_transitivity.evidence.serialization import record_digest

    manifest = json.loads((ROOT / "datasets/pilot/manifest.json").read_text())
    cases = []
    for entry in manifest["datasets"]:
        records = json.loads((ROOT / entry["pilot_path"]).read_text())
        for origin, record in zip(entry["selected_rows"], records, strict=True):
            cases.append(
                {
                    "sample_uid": f"{entry['dataset']}:{origin['original_row']}:{origin['sentence_sha256'][:16]}",
                    "prompt": record[2],
                    "target": "yes" if record[6] == "valid" else "no",
                    "stratum": entry["dataset"]
                    + ":"
                    + record_digest(list(stratum(record)))[:16],
                }
            )
    rows = [{**case, "model": f"model-{model}"} for model in range(6) for case in cases]
    _validate_selection(rows, manifest, ROOT)
    rows[0][field] += " altered"
    with pytest.raises(ValueError, match="verified source cases"):
        _validate_selection(rows, manifest, ROOT)
