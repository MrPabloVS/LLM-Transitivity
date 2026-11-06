# Full-corpus report, revision 2

Read [the report](report.md), [the continuous PDF](report.pdf), or
[the HTML report](index.html). Serve this folder over localhost to use the
[interactive tables and case explorer](explorer.html).

This revision separates TP, TN, FP, and FN relative to source labels.
Positive means yes. FPR and FNR use interpretable responses in the relevant
source class; class coverage includes every planned case of that class.
Undefined rates are not zero. No source label or score was changed.

The [previous report](../analysis-v1/report.md) and
[separate interpretation](../interpretation-v1/report.md) remain unchanged.

The CSV tables and summary JSON include the new fields. Case JSON, response
CSV, costs, tokens, and operational results retain their previous values.
`validation.json` records native verification; `provenance.json` records hashes.

Git LFS stores `analysis.sqlite.gz` and `tables/responses.csv`. After cloning,
run `git lfs pull`. To restore the database, run `gzip -dk analysis.sqlite.gz`
in this directory only when `analysis.sqlite` does not exist. The uncompressed
database stays local. The PDF and HTML do not need database decompression.

Rebuild from the same native evidence into a new directory:

```sh
uv run --locked transitivity report --run results/full/2026-11-06_01-23-40-040fd7b7 --output reports/full/2026-11-06_01-23-40-040fd7b7/new-analysis
```

This command makes no provider API calls. It also generates the continuous PDF.
