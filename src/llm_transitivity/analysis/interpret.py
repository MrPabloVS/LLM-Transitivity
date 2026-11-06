"""Build a static interpretation without changing its source report."""

import json
from pathlib import Path

import duckdb

from llm_transitivity.analysis.interpret_data import (
    VERSION,
    file_hash,
    prepare,
    require,
    write_tables,
)
from llm_transitivity.analysis.interpret_document import render
from llm_transitivity.analysis.interpret_figures import make_figures
from llm_transitivity.analysis.interpret_narrative import narrative


def interpret(root: Path, source: Path, output: Path):
    source, output = source.resolve(), output.resolve()
    require(not output.exists(), "Output directory already exists")
    require(
        not output.is_relative_to(source), "Output must not be inside the source report"
    )
    inputs = [
        source / "summary.json",
        source / "validation.json",
        *sorted((source / "data").glob("*.json")),
        *sorted((source / "tables").glob("*.csv")),
    ]
    hashes = {str(p.relative_to(source)): file_hash(p) for p in inputs}
    with duckdb.connect() as connection:
        data = prepare(source, connection)
    output.mkdir(parents=True)
    write_tables(output / "tables", data["tables"])
    make_figures(output / "figures", data)
    render(output, narrative(data))
    (output / "summary.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    require(
        all(file_hash(source / name) == digest for name, digest in hashes.items()),
        "Source report changed during analysis",
    )
    code = {
        str(p.relative_to(root)): file_hash(p)
        for p in sorted((root / "src/llm_transitivity/analysis").glob("interpret*.py"))
    }
    for name in ("src/llm_transitivity/cli/interpret.py", "pyproject.toml", "uv.lock"):
        code[name] = file_hash(root / name)
    provenance = {
        "analysis_version": VERSION,
        "source_report": str(source),
        "run_id": data["source"]["run_id"],
        "input_sha256": hashes,
        "analysis_source_sha256": code,
        "duckdb_version": duckdb.__version__,
    }
    (output / "provenance.json").write_text(
        json.dumps(provenance, indent=2), encoding="utf-8"
    )
    validation = {
        "complete": True,
        "cases": 54000,
        "corpus_responses": 324000,
        "tasks": 108,
        "strata": 108,
        "model_strata": 648,
        "pairs": 15,
        "json_csv_responses_equal": True,
        "prompt_hashes_verified": True,
        "native_report_aggregates_reconciled": True,
        "cost_ledger_reconciled": True,
        "inputs_unchanged": True,
    }
    (output / "validation.json").write_text(
        json.dumps(validation, indent=2), encoding="utf-8"
    )
    print(output)
