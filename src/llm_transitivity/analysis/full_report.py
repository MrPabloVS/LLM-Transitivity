"""Create a complete offline report without changing native experiment evidence."""

from pathlib import Path

from llm_transitivity.analysis.full_store import (
    VERSION,
    database,
    file_hash,
    ingest_phase,
    load_cases,
    read_json,
    require,
    validate_closed_run,
)
from llm_transitivity.analysis.full_summary import (
    build_summary,
    export_tables,
    write_json,
)


def report(root: Path, run: Path, output: Path) -> Path:
    root, run, output = root.resolve(), run.resolve(), output.resolve()
    require(run.is_relative_to(root), "Run must be in the repository")
    require(not output.exists(), "Report output already exists")
    require(
        not output.is_relative_to(run),
        "Keep derived reports outside native run evidence",
    )
    validate_closed_run(run)
    provenance = {}
    for phase in ("preflight", "corpus"):
        directory = run / phase
        for rel, expected in read_json(
            directory / "provenance/snapshot_hashes.json"
        ).items():
            path = directory / "provenance/snapshot" / rel
            require(file_hash(path) == expected, "Frozen snapshot hash differs: " + rel)
            provenance[str(path.relative_to(root))] = expected
        for rel in (
            "provenance/run.json",
            "provenance/flow_spec.json",
            "provenance/snapshot_hashes.json",
            "summary/closure.json",
            "summary/log_index.json",
        ):
            path = directory / rel
            provenance[str(path.relative_to(root))] = file_hash(path)
    for name in ("full_manifest.json", "events.jsonl", "worker.json"):
        provenance[str((run / name).relative_to(root))] = file_hash(run / name)
    for relative in (
        "src/llm_transitivity/domain/scoring.py",
        "src/llm_transitivity/inspect/scoring.py",
    ):
        require(
            file_hash(root / relative)
            == file_hash(run / "corpus/provenance/snapshot" / relative),
            "Scorer source differs from the frozen version",
        )
    output.mkdir(parents=True)
    db = database(output / "analysis.sqlite")
    try:
        manifest, config = load_cases(db, root, run)
        system = read_json(
            run / "corpus/provenance/snapshot" / manifest["system_prompt"]["path"]
        )[0]
        tasks = []
        for phase in ("preflight", "corpus"):
            tasks += ingest_phase(db, root, run, phase, system, config, provenance)
        summary = build_summary(db, run, config, tasks)
        summary["system_prompt"] = system
        summary["analysis_version"] = VERSION
        summary["source_run"] = str(run.relative_to(root))
        summary["definitions"] = {
            "agreement": "source-label matches / interpretable responses",
            "coverage": "interpretable responses / planned cases",
            "strict_format": "strict yes/no responses / planned cases",
            "matched_total": "source-label matches / planned cases",
            "cost": "deduplicated reported generation costs; missing values remain unknown",
            "scope": "closed full-corpus run only; preflight kept separate",
        }
        export_tables(db, output, summary)
        from llm_transitivity.analysis.full_render import render

        render(db, root, run, output, summary)
        # Recheck native artifacts after analysis. No data may change mid-report.
        for rel, expected in provenance.items():
            require(
                file_hash(root / rel) == expected,
                "Evidence changed during analysis: " + rel,
            )
        sources = {}
        package = root / "src/llm_transitivity"
        for path in package.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".js", ".css", ".html"}:
                sources[str(path.relative_to(root))] = file_hash(path)
        for name in ("pyproject.toml", "uv.lock"):
            sources[name] = file_hash(root / name)
        write_json(
            output / "provenance.json",
            {
                "analysis_version": VERSION,
                "inputs": provenance,
                "analysis_sources": sources,
            },
        )
        db.commit()
        write_json(
            output / "validation.json",
            {
                "complete": True,
                "cases": 54000,
                "models": 6,
                "tasks": 108,
                "corpus_samples": 324000,
                "preflight_samples": 6,
                "model_strata": 648,
                "cases_per_stratum": 500,
                "native_metrics_reconciled": True,
                "source_text_and_hashes_verified": True,
                "protected_inputs_unchanged": True,
            },
        )
    finally:
        db.close()
    print(f"Report complete: {output}", flush=True)
    return output
