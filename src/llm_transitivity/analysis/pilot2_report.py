"""Report the Pilot 2.0 coverage experiment without new requests."""

from pathlib import Path
from uuid import uuid4

from llm_transitivity.evidence.serialization import json_bytes


def write_report(root: Path, directory: Path, manifest: dict, reviews: dict) -> Path:
    generations = {}
    for review in reviews.values():
        for identifier, value in review["generations"].items():
            if identifier not in generations or value["cost_usd"] is not None:
                generations[identifier] = value
    known = sum(
        v["cost_usd"] for v in generations.values() if v["cost_usd"] is not None
    )
    missing = [k for k, v in generations.items() if v["cost_usd"] is None]
    summary = {
        "campaign_id": manifest["campaign_id"],
        "profile": manifest.get("profile", "pilot2"),
        "known_cost_usd": known,
        "missing_cost_ids": missing,
        "generation_attempts": len(generations),
        "phases": {
            name: {
                k: v for k, v in review.items() if k not in {"samples", "generations"}
            }
            for name, review in reviews.items()
        },
    }
    suffix = uuid4().hex[:8]
    path = directory / f"report-{suffix}.json"
    path.write_bytes(json_bytes(summary))
    if manifest.get("profile") == "pilot3":
        schedule = (
            "Coverage configures 108 active tasks and 64 samples per task. The configured",
            "ceiling is 6912. Dataset sizes reduce the effective sample ceiling to 3240.",
            "Shared connection pools allow 1152 requests per model. All selected providers",
        )
    else:
        schedule = (
            "Coverage configures 108 active tasks and 32 samples per task. The configured",
            "ceiling is 3456. Dataset sizes reduce the effective sample ceiling to 2808.",
            "Shared connection pools allow 576 requests per model. All selected providers",
        )
    lines = [
        f"# {manifest.get('pilot_name', 'Pilot 2.0')} results",
        "",
        f"Campaign: `{manifest['campaign_id']}`.",
        "",
        "The experiment compares six models on the same 540 source cases per model.",
        *schedule,
        "are fixed. Observed concurrency and response checks are reported below.",
        "",
        "Agreement uses source labels, not independently audited logical validity.",
        "Filters remain outcomes, with missing usage and costs unverified. No filter",
        "triggers a replacement generation. Strict format requires only yes or no.",
        "",
        f"Known reported cost: USD {known:.9f}. Unknown cost IDs: {len(missing)}.",
        f"Captured generation attempts: {len(generations)}.",
        "",
        "| Phase | Model | Samples | Agreement / interpreted | Strict format | Filters | Attempts / failed | Sample / HTTP peak | Known USD |",
        "| --- | --- | ---: | --- | --- | ---: | --- | --- | ---: |",
    ]
    for phase, review in reviews.items():
        for model, v in review["models"].items():
            m = v["measures"]
            lines.append(
                f"| {phase} | {model} | {v['samples']} | {m['correct']}/{m['answered']} | {m['format_compliant']}/{m['samples']} | {len(v['filtered_uids'])} | {v['attempts']}/{v['failed_attempts']} | {v['peak_samples']}/{v['peak_http_requests']} | {v['known_cost_usd']:.9f} |"
            )
    lines += [
        "",
        "Technical reviews retain all sample UIDs, conditions, responses, missing fields,",
        "source hashes, and configuration faults. Native logs and source data are unchanged.",
        "No full-corpus run or default model replacement is automatic.",
        "",
    ]
    path.with_suffix(".md").write_text("\n".join(lines))
    return path
