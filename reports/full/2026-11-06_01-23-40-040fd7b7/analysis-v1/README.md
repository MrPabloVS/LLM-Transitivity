# Report bundle

Read [the report](report.md). Serve this directory through a local HTTP server
and open [the case explorer](index.html) to compare all six saved responses.

Git contains the report, figures, aggregate tables, case files, model cards,
summary, and validation records. The complete local bundle also contains
`analysis.sqlite` and `tables/responses.csv`. These two derived files exceed
GitHub's file size limit and are excluded from Git. Links to these files in the
report require the complete local bundle.

Rebuild the complete bundle from the preserved native run evidence:

```sh
uv run --locked transitivity report --run results/full/2026-11-06_01-23-40-040fd7b7 --output <new-directory>
```

The destination must not exist. This command makes no provider API calls.
Native run logs are kept separately from this report bundle.
