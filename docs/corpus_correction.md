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
