# Six-model pilot

Status: coverage pilot prepared and verified without paid model calls.
Model availability and prices checked on November 5, 2026, through the
[OpenRouter model catalog](https://openrouter.ai/api/v1/models) and its provider
endpoint listings. A catalog entry does not establish access through our account.

## Goal

Compare two model versions from each of three model developers: OpenAI,
Anthropic, and Google. Use the same inputs and disable optional reasoning.
Measure agreement with the dataset labels, response format, and response coverage.

These are comparisons of specific model versions. Differences also include
training, model size, and tokenization. They do not isolate the effect of a
generation change. Sonnet also has a higher price than the other model families.

## Proposed models and providers

Prices are USD per million text tokens for standard requests with short prompts.
They exclude cache and batch discounts, retries, and account-level charges.
Provider means the endpoint selected within OpenRouter.

| Model ID in OpenRouter | Provider | Provider slug | Input | Output |
| --- | --- | --- | ---: | ---: |
| [openai/gpt-4o-mini](https://openrouter.ai/openai/gpt-4o-mini) | OpenAI | `openai` | $0.15 | $0.60 |
| [openai/gpt-6-luna](https://openrouter.ai/openai/gpt-6-luna) | OpenAI | `openai` | $0.10 | $0.50 |
| [anthropic/claude-sonnet-4.5](https://openrouter.ai/anthropic/claude-sonnet-4.5) | Anthropic | `anthropic` | $3.00 | $15.00 |
| [anthropic/claude-sonnet-5](https://openrouter.ai/anthropic/claude-sonnet-5) | Anthropic | `anthropic` | $2.00 | $10.00 |
| [google/gemini-2.5-flash-lite](https://openrouter.ai/google/gemini-2.5-flash-lite) | Google AI Studio | `google-ai-studio` | $0.10 | $0.40 |
| [google/gemini-3.1-flash-lite](https://openrouter.ai/google/gemini-3.1-flash-lite) | Google AI Studio | `google-ai-studio` | $0.25 | $1.50 |

Inspect model names need the additional `openrouter/` prefix.

The comparison has two generation groups, each with one model per developer:

| Group | OpenAI | Anthropic | Google |
| --- | --- | --- | --- |
| `earlier` | GPT-4o mini | Sonnet 4.5 | Gemini 2.5 Flash-Lite |
| `later` | GPT-6 Luna | Sonnet 5 | Gemini 3.1 Flash-Lite |

These are explicit comparison groups, not synchronized release generations.
The group is stored in Inspect task metadata and tags.

## Pilot conditions

See the [cost scenarios](pilot_cost_estimate.md) and
[quoted prices and inputs](pilot_cost_estimate.json) before selecting a budget.
The estimate is not a spending limit; budget enforcement is still pending.

- Use five cases from every observed stratum across the 18 full datasets.
  This gives 540 cases per model and 3,240 planned responses across six models.
  Retries can increase the number of requests.
- Each HS dataset contributes 20 cases. Each mHS dataset contributes 40 cases.
  Pilot filenames use these actual counts, such as `HS_HF_PR_20.json` and
  `mHS_HF_PR_40.json`. Full dataset filenames keep their counts of 2,000 or 4,000.
  All 108 observed strata are covered. See the
  [generated inventory](dataset_inventory.md) for counts and coverage limits.
- Preserve the prompt text, source labels, and case order. Keep source identifiers
  in the Inspect sample metadata.
- Use the exact system message from `prompts/systemPrompts/zeroShot.json`:
  `Answer only with 'yes' or 'no' and nothing else.`
- Use one independent conversation per case and one system and user message.
- Fix the provider listed above and disable provider fallback. A provider failure
  must remain visible instead of silently changing the experimental condition.
- Disable optional reasoning explicitly. GPT-4o mini has no reasoning mode in
  the catalog; the other five models list reasoning as optional.
- Check the effective request settings, selected provider, and reported reasoning
  token usage during the trial. Missing usage data is not evidence of zero usage.
- Keep raw outputs and execution errors in Inspect logs. Record the exact model
  IDs, configuration, dataset hashes, package versions, and run command.

Hiding reasoning output does not disable reasoning or its billing. See
[OpenRouter reasoning controls](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)
and [provider routing](https://openrouter.ai/docs/guides/routing/provider-selection).
Sonnet 5.5 and Gemini 3.5 Flash-Lite are excluded because the checked catalog
marks their reasoning as mandatory.

## Scoring and readiness

See [Inspect tags and metadata](inspect_metadata.md) for the evaluation, task,
and sample fields, native log fields, and requested-versus-observed conditions.

Use the scoring rules documented in the [README](../README.md#inspect-flow-trial).
Report agreement with source labels separately from format compliance. These
labels have not been audited for logical validity.

`flow.py` now builds the coverage pilot through `pilot_config.py`: 18 datasets
times six models, or 108 evaluation tasks. It verifies the complete corpus and
manifest before constructing the spec. Each task checks its source chain again
before constructing Inspect samples. The 10-case `HS.json` remains a separate
smoke dataset and is not included in this coverage pilot.

The configuration fixes each provider, disables fallbacks, and sends
`reasoning_enabled=False` for models with optional reasoning. It uses 1,024 output
tokens, two connections, at most two concurrent samples, and one active task.
Prompt caching is disabled. Temperature, top-p, and seed are omitted for all
models; provider defaults apply and generated answers are not deterministic.
The deterministic guarantee applies to input preservation and selection only.
The Inspect model request retry limit is two, and SDK retries are disabled.
There are at most three planned HTTP attempts per logical generation instead
of two nested retry layers. The Flow evaluation-set attempt limit is
one, with failed logs retained. Runtime reasoning behavior still needs to be
confirmed from actual requests and reported usage.
Streaming is disabled. Each sample also retains HTTP attempt snapshots and
complete OpenRouter generation metadata, as described in the metadata guide.

## Reproduce the checks

```sh
uv run --locked prepare_pilot.py verify
uv run --locked pytest -q
uv run --locked run_pilot.py --dry-run
```

The verifier checks all 54,000 full records against a fixed Git revision. It
allows only the two approved label translations, reproduces the selection,
and checks all pilot files and the system prompt. The
[manifest](../datasets/pilot/manifest.json) records source paths, hashes,
original row numbers, and selected record hashes. Rebuilding refuses to
overwrite existing evidence. Existing model logs are outside this verification.

The [dry-run summary](pilot_dry_run.json) records 108 tasks, 3,240 planned
responses, zero completed samples, and the manifest and configuration hashes.
It confirms local task construction, not provider access or model behavior.

This provides reproducible evidence of exact sentence preservation, including
spaces, case, punctuation, and Unicode. It does not audit logical validity.
Tests also alter sentences, labels, identifiers, row order, original files,
pilot files, the manifest, and the system prompt to verify rejection.

After the trial, inspect all 3,240 outcomes, their metadata, errors, response
categories, token usage, and recorded costs before expanding the experiment.

## Result directories

First run one identical source case on each model:

```sh
uv run --locked run_pilot.py --preflight --dry-run
uv run --locked run_pilot.py --preflight
```

This selects one verified original row from the first pilot dataset, creates six
tasks, and records `phase:preflight`. Its result folder ends in `_preflight`.
The complete 540-case selection remains unchanged.

Use the managed entry point for a paid run:

```sh
uv run --locked run_pilot.py
```

One directory holds the complete run, across all six models and 18 datasets:

```text
results/pilot/<local-date-time>-<run-id>/
  inspect/             # All native .eval logs and Flow files
  openrouter_calls/    # Complete call exports
  provenance/          # Frozen metadata, Flow spec, inputs, code, and hashes
  summary/             # Log index, statuses, and sample error counts
```

Folder timestamps use `America/Argentina/Buenos_Aires`. The ID suffix prevents
collisions within one second. An existing directory is never reused by a new
managed launch. All tasks share that root and the same experiment run ID.

Before the first model call, `provenance/` receives `run.json`, `flow_spec.json`,
`snapshot_hashes.json`, and a `snapshot/` tree with the pilot inputs, system
prompt, manifest, code, and lockfile. Hash checks detect changes between spec
construction and snapshot creation. Credentials and `.env` are excluded.

When the run returns or unwinds through an error or interruption, the managed
runner exports existing calls without extra API requests and writes
`summary/log_index.json`. The index records individual log statuses and errors;
it is not yet an aggregate metrics or billing report. Partial and unreadable
logs are recorded as such. A force-killed process cannot finalize; its existing
logs and provenance remain available for later export.

`run_pilot.py --dry-run` creates no result archive. Direct `flow run flow.py`
remains a low-level entry point; use the managed command above to get the full
archive and finalization behavior.
