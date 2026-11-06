# Corrected principal corpus

Read [the report](report.md), [HTML](index.html), or [continuous PDF](report.pdf).
Serve this folder locally to use [interactive tables and cases](explorer.html).

This revision replaces 3,672 responses for 612 corrected questions. It retains
320,328 responses unchanged. All 54,000 cases still have six model responses.
Original labels and scoring rules are unchanged. The correction preflight is
separate from the corpus and from the original preflight.

See `tables/replacements.csv` for the original and replacement results.
`tables/correction_changes.csv` contains before/after measures.
`tables/correction_costs.csv` separates retained, superseded, replacement, and
preflight charges. Unknown costs are not zero. The report combines two executions;
its operational time table describes the original execution only.

The [previous report](../analysis-v2/report.md) and
[previous interpretation](../interpretation-v1/report.md) remain available.
Read the [updated static interpretation](../interpretation-v2/report.md).

Git LFS stores the compressed SQLite database and response CSV. Run `git lfs pull`
after cloning. Restore the local database with `gzip -dk analysis.sqlite.gz`
only when `analysis.sqlite` does not exist. HTML does not need decompression.

Rebuild offline into a new directory:

```sh
uv run --locked transitivity report --run results/full/2026-11-06_01-23-40-040fd7b7 --correction results/corrections/2026-11-06_15-37-32-64caf3fd-eate-to-ate-v1 --output reports/full/2026-11-06_01-23-40-040fd7b7/new-analysis
```
