# Corpus correction: eate to ate

The amendment `eate-to-ate-v1` corrects 612 questions: 204 HS HF PA and
408 mHS HF PA. Each question has two replacements. Only the complete word
`eate` changes to `ate`. Source labels and conditions do not change.

Original prompts and frozen runs retain their bytes. Working datasets use the
approved correction manifest. Pilot and load selections retain their original
source rows; new sentence hashes do not change the selection ranking.

Use `uv run --locked transitivity correction --dry-run` to verify 12 tasks and
3,672 replacement responses. Use `--prepare-only` to freeze the inputs, then
`--resume <directory>` to execute. `--detach` starts a separate worker.
The worker runs six preflight calls before the replacement tasks. Filters remain
outcomes. A failed technical check stops advancement. Resume uses completed
samples and preserves previous log indexes and closures.

The model settings come from the original full-run Flow snapshot, including
routing, reasoning, retries, output limits, streaming, and concurrency. Package
versions present in the original lock must remain equal; added reporting
packages do not change the execution dependencies.

A corrected principal corpus replaces each affected case and all six results.
It is a composite of two executions, not one continuous run. Original evidence
remains available. Costs and elapsed times retain their execution provenance.

## Completed correction

The correction archive is
`results/corrections/2026-11-06_15-37-32-64caf3fd-eate-to-ate-v1`.
Its six preflight calls and 12 replacement tasks passed the technical checks.
The composite contains 3,672 new responses and 320,328 unchanged responses.
The 612 affected questions have 172 changes in interpreted answers and 50 more
matches with source labels. These differences can include model variability and
service changes; they do not measure the effect of spelling alone.

Read the [principal report](../reports/full/2026-11-06_01-23-40-040fd7b7/analysis-v3/report.md)
and [static interpretation](../reports/full/2026-11-06_01-23-40-040fd7b7/interpretation-v2/report.md).
Their replacement table links each old result to its new result. The cost tables
separate retained responses, superseded responses, replacements, and preflights.

To rebuild the report without model calls, use:

```sh
uv run --locked transitivity report --run results/full/2026-11-06_01-23-40-040fd7b7 --correction results/corrections/2026-11-06_15-37-32-64caf3fd-eate-to-ate-v1 --output reports/full/2026-11-06_01-23-40-040fd7b7/new-analysis
```

The output directory must not exist. Use the corrected report directory with
`transitivity interpret` and `transitivity explore`. DuckDB uses a different
local database for each report path.
