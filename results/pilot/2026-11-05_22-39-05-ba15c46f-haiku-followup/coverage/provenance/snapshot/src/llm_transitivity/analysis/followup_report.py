"""Write a separate follow-up report and observed-usage projections."""

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from uuid import uuid4

from llm_transitivity.analysis.calculations import percentile90, queue_seconds
from llm_transitivity.domain.selection import stratum
from llm_transitivity.evidence.serialization import json_bytes, record_digest

BASELINE = Path("results/analyses/pilot-2026-11-05-scoring-v3-verified")


def write_report(root: Path, directory: Path, manifest: dict, reviews: dict) -> Path:
    baseline = json.loads((root / BASELINE / "summary.json").read_text())
    baseline_rows = [
        json.loads(line)
        for line in (root / BASELINE / "samples.jsonl").read_text().splitlines()
    ]
    all_generations = {}
    for review in reviews.values():
        for identifier, entry in review["generations"].items():
            if identifier not in all_generations or entry["cost_usd"] is not None:
                all_generations[identifier] = entry
    known = sum(
        e["cost_usd"] for e in all_generations.values() if e["cost_usd"] is not None
    )
    missing = [k for k, e in all_generations.items() if e["cost_usd"] is None]
    projections, comparisons = {}, {}
    coverage = reviews.get("coverage", {})
    mapping = {
        "anthropic/claude-haiku-4.5": "openrouter/anthropic/claude-sonnet-4.5",
        "anthropic/claude-haiku-5.5": "openrouter/anthropic/claude-sonnet-5",
    }
    for model, old_model in mapping.items():
        current = {
            r["sample_uid"]: r
            for r in coverage.get("samples", [])
            if r["model"] == model
        }
        old = {r["sample_uid"]: r for r in baseline_rows if r["model"] == old_model}
        paired = defaultdict(int)
        for uid in current.keys() & old.keys():
            key = (
                old[uid]["after"]["value"] == "C",
                current[uid]["after"]["value"] == "C",
            )
            paired[str(key)] += 1
        comparisons[model] = {
            "baseline_model": old_model,
            "paired_cases": len(current.keys() & old.keys()),
            "complete_pairing": set(current) == set(old),
            "paired_agreement": dict(paired),
        }
    for old_model, old in baseline["models"].items():
        if "/anthropic/" not in old_model:
            projections[old_model.removeprefix("openrouter/")] = {
                "group": old["group"],
                "cost_usd": old["cost_projection"]["central_usd"],
                "cost_basis": "original 540-case pilot",
                "central_hours_at64": None,
                "slow_hours_at64": None,
            }
    for model, value in coverage.get("models", {}).items():
        if value["samples"] == 540 and not value["faults"]:
            ids = set(value["final_generation_ids"])
            costs = [coverage["generations"][i]["cost_usd"] for i in ids]
            projections[model] = {
                "group": "earlier" if model.endswith("4.5") else "later",
                "cost_usd": sum(costs) * 100
                if len(ids) == 540 and all(v is not None for v in costs)
                else None,
                "cost_basis": "Haiku 540-case coverage pilot",
                "central_hours_at64": None,
                "slow_hours_at64": None,
            }
    load = reviews.get("load-64", {})
    source_manifest = json.loads((root / "datasets/pilot/manifest.json").read_text())
    full_keys = [
        [
            entry["dataset"] + ":" + record_digest(list(stratum(row)))[:16]
            for row in json.loads((root / entry["working_path"]).read_text())
        ]
        for entry in source_manifest["datasets"]
    ]
    for model, value in load.get("models", {}).items():
        if model not in projections or value["faults"]:
            continue
        latencies = defaultdict(list)
        for row in load["samples"]:
            if row["model"] == model and row["seconds"] is not None:
                dataset = row["sample_uid"].split(":")[0]
                latencies[dataset + ":" + row["conditions"]["stratum_id"]].append(
                    row["seconds"]
                )
        if len(latencies) != 108:
            continue
        for label, estimator in [
            ("central_hours_at64", mean),
            ("slow_hours_at64", percentile90),
        ]:
            durations = {k: estimator(v) for k, v in latencies.items()}
            overhead = max(
                0,
                value["task_window_seconds"]
                - queue_seconds(
                    [
                        row["seconds"]
                        for row in load["samples"]
                        if row["model"] == model
                    ],
                    64,
                ),
            )
            projections[model][label] = (
                sum(
                    queue_seconds([durations[k] for k in keys], 64) + overhead
                    for keys in full_keys
                )
                / 3600
            )
    groups = {}
    for group in ["earlier", "later", "all"]:
        selected = [
            v for v in projections.values() if group == "all" or v["group"] == group
        ]
        complete = len(selected) == (6 if group == "all" else 3)
        groups[group] = {
            field: sum(v[field] for v in selected)
            if complete and all(v[field] is not None for v in selected)
            else None
            for field in ["cost_usd", "central_hours_at64", "slow_hours_at64"]
        }
    report = {
        "campaign_id": manifest["campaign_id"],
        "known_cost_usd": known,
        "missing_cost_ids": missing,
        "comparisons": comparisons,
        "projections": projections,
        "groups": groups,
        "load64_validated": load.get("load64_validated", False),
        "load_reasons": load.get("load_reasons", {}),
        "executed_stages": list(reviews),
        "note": "No 16/32 matched load exists. No measured speedup or model replacement is claimed.",
    }
    suffix = uuid4().hex[:8]
    summary_path = directory / f"report-{suffix}.json"
    summary_path.write_bytes(json_bytes(report))
    lines = [
        "# Haiku follow-up results",
        "",
        f"Campaign: `{manifest['campaign_id']}`.",
        "",
        "The user selected direct 64-slot load, with one active task. Load at 16 and 32",
        "was omitted by request. Coverage still uses 16 slots. Original Sonnet evidence",
        "is unchanged. The full corpus was not run and no default model was replaced.",
        "",
        "## Phase results",
        "",
        "| Stage | Samples | Technical checks | Known reported USD | Unknown cost IDs |",
        "| --- | ---: | --- | ---: | ---: |",
    ]
    for name in ["preflight", "coverage", "load-64"]:
        review = reviews.get(name)
        if review is None:
            lines.append(f"| {name} | 0 | Omitted after a failed prior stage | — | — |")
        else:
            values = review["models"].values()
            lines.append(
                f"| {name} | {sum(v['samples'] for v in values)} | {'Passed' if review['technical_pass'] else 'Stopped; review faults'} | {sum(v['known_cost_usd'] for v in values):.8f} | {sum(len(v['missing_cost_ids']) for v in values)} |"
            )
    lines += [
        "",
        f"Total known reported cost: **USD {known:.8f}**; {len(missing)} generation IDs have unknown cost.",
        "Missing costs are not zero. These are returned charges, not an independent invoice audit.",
        "",
        "## Haiku answers",
        "",
        "| Model | Agreement / interpreted | Strict format / scored |",
        "| --- | ---: | ---: |",
    ]
    for model, value in coverage.get("models", {}).items():
        m = value["measures"]
        lines.append(
            f"| {model} | {m['correct']}/{m['answered']} | {m['format_compliant']}/{m['samples']} |"
        )
    lines += [
        "",
        "Agreement refers to source labels, not independently audited logical validity.",
        "Load responses are excluded from this accuracy table. Pairing, case details,",
        "conditions, outputs, and source hashes are retained in the per-phase reviews.",
        "",
        "## Direct 64-slot load",
        "",
        "| Model | Cases/min | Sample p90 seconds | Peak samples | Peak HTTP | Failed attempts |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for model, value in load.get("models", {}).items():
        rate = value["cases_per_minute"]
        p90 = value["sample_p90_seconds"]
        lines.append(
            f"| {model} | {rate if rate is not None else 'unknown'} | {p90 if p90 is not None else 'unknown'} | {value['peak_samples']} | {value['peak_http_requests']} | {value['failed_attempts']}/{value['attempts']} |"
        )
    lines += [
        "",
        f"64-slot technical validation: **{report['load64_validated']}**.",
        "Validation requires complete verified samples, zero final errors, at most 5%",
        "failed attempts per model, and observed peak sample concurrency of 64.",
        "An internal provider error in HTTP 200 counts as a failed attempt.",
        "No 10% speedup or p90 ratio against 16/32 can be tested without matched loads.",
        "",
        "## Full-pass scenarios",
        "",
        "| Group | Responses | Projected USD | Central hours at 64 | Slow hours at 64 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for group, values in groups.items():
        cells = [
            f"{v:.2f}" if v is not None else "not available" for v in values.values()
        ]
        lines.append(
            f"| {group} | {324000 if group == 'all' else 162000} | {' | '.join(cells)} |"
        )
    lines += [
        "",
        "Cost scales final-response usage within the balanced coverage selection by 100.",
        "The four unchanged models retain their original pilot cost basis. Haiku uses",
        "the new 540-case pilot. Unknown failed-attempt charges are excluded.",
        "Time schedules the full source order at 64 using mean and interpolated p90",
        "durations from the 216-case load, plus measured nonnegative task overhead",
        "once per dataset. There are only two observations per stratum. These are",
        "conditional scenarios, not confidence bounds or delivery guarantees.",
        "",
        "## Recommendation",
        "",
    ]
    if not coverage.get("technical_pass"):
        lines += [
            "Resolve the failed preflight or coverage checks before running more generations."
        ]
    else:
        lines += [
            "Review Haiku agreement, format, costs, and paired cases jointly before replacing",
            "Sonnet. Review mHS and reversed-order source labels manually. No accuracy",
            "threshold automatically selects a model.",
        ]
        lines += [
            "The direct load supports considering 64 for this profile; it does not prove a speedup."
            if report["load64_validated"]
            else "64 is not fully validated. Review the per-model load reasons before a full run."
        ]
    lines += [
        "",
        "Keep the current default profile until that review. No spend-triggered pause was",
        "configured, as requested. A complete corpus run needs a separate decision.",
        "",
        f"[Machine-readable comparison and projections]({summary_path.name}).",
        "",
    ]
    path = directory / f"report-{suffix}.md"
    path.write_text("\n".join(lines))
    return path
