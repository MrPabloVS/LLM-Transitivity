# Report bundle

Read [the report](report.md). Serve this directory through a local HTTP server
and open [the case explorer](index.html) to compare all six saved responses.

Git contains the report, figures, aggregate tables, case files, model cards,
summary, and validation records. Git LFS tracks `analysis.sqlite.gz` and
`tables/responses.csv`. The gzip archive contains the complete SQLite database.
The uncompressed `analysis.sqlite` stays local. Compression preserves its bytes.

After a clone, download the LFS objects from the repository root:

```sh
git lfs pull
```

In this report directory, restore the database with `gzip -dk analysis.sqlite.gz`.
Do this only if `analysis.sqlite` does not exist. Links to the SQLite database in
the report work after decompression. The CSV needs no decompression.

Rebuild the complete bundle from the preserved native run evidence:

```sh
uv run --locked transitivity report --run results/full/2026-11-06_01-23-40-040fd7b7 --output <new-directory>
```

The destination must not exist. This command makes no provider API calls.
Native run logs are kept separately from this report bundle.
