# Six-model pilot

Status: pilot preparation restarted after the code and routing changes.
The local checks and new cost estimate are complete. A new live preflight is
required before the complete pilot. Earlier estimates and preflight reports are no longer
part of the active preparation.
Saved model availability and price references were captured on November 5, 2026, through the
[OpenRouter model catalog](https://openrouter.ai/api/v1/models) and its provider
endpoint listings. A catalog entry does not establish access through our account.

## Current preparation status

Local checks passed again on November 5, 2026: 54,000 full records, 108 strata,
and 540 selected cases; 149 tests; and both dry-runs (108 pilot tasks and six
preflight tasks). Original inputs and selected files remain unchanged. Ruff
passes for package sources and tests. Global Ruff checks still report the
existing lint and format failures in the preserved `runBenchmark.py`.

A new [cost estimate](../results/cost_estimates/2026-11-05_19-47-28-e1bd86b6/estimate.json)
was saved on November 5, 2026, using all six selected endpoints and current
verified inputs. The one-attempt scenarios total USD 0.35 for four output tokens,
USD 2.14 for 128 output tokens, and USD 15.11 at the 1,024-token output cap.
The byte-input scenario with all three attempts totals USD 49.66. These are
planning scenarios, not spending limits or reported charges.

The earlier estimate attempt stopped because our quote filter required endpoint
`status: 0`. Quote retrieval now uses the exact published endpoint tag regardless
of status. The GPT-6 Luna Flex listing includes prices with `status: -2`.
This status is not interpreted as an access or outage result. The new live
preflight remains pending; no model generation was requested for the estimate.

## Goal

Compare two model versions from each of three model developers: OpenAI,
Anthropic, and Google. Use the same inputs and disable optional reasoning.
Measure agreement with the dataset labels, response format, and response coverage.

These are comparisons of specific model versions. Differences also include
training, model size, and tokenization. They do not isolate the effect of a
generation change. Sonnet also has a higher price than the other model families.

## Selected models, endpoints and service tiers

The executable catalog in `src/llm_transitivity/domain/config.py` defines the
requested model IDs, endpoints, tiers, and execution policy.

The [saved model cards](model_cards/README.md) retain the public catalog and
endpoint data for all six models, with sources, capture times and hashes.

Routing decision approved on November 5, 2026. Flex is selected for GPT-6 Luna
and both Gemini Flash-Lite models. The other three models use the default tier.
The executable model catalog and Flow configuration now set these endpoint and
tier pairs explicitly. A new live preflight is pending.
Saved model cards describe their capture
time; this guide records the current execution configuration.

The dated quotes below are USD per million text tokens for the selected
endpoints and short prompts. They are reference prices, not a new pilot estimate. They were checked against the linked public endpoint listings on
November 5, 2026. They exclude cache and batch discounts, retries, and account
charges. Published availability does not establish access through our account.

| Model ID in OpenRouter | Provider | Exact `provider.only` slug | Explicit `service_tier` | Input | Output |
| --- | --- | --- | --- | ---: | ---: |
| [openai/gpt-4o-mini](https://openrouter.ai/api/v1/models/openai/gpt-4o-mini/endpoints) | OpenAI | `openai` | `default` | $0.15 | $0.60 |
| [openai/gpt-6-luna](https://openrouter.ai/api/v1/models/openai/gpt-6-luna/endpoints) | OpenAI | `openai/flex` | `flex` | $0.05 | $0.25 |
| [anthropic/claude-sonnet-4.5](https://openrouter.ai/api/v1/models/anthropic/claude-sonnet-4.5/endpoints) | Anthropic | `anthropic` | `default` | $3.00 | $15.00 |
| [anthropic/claude-sonnet-5](https://openrouter.ai/api/v1/models/anthropic/claude-sonnet-5/endpoints) | Anthropic | `anthropic` | `default` | $2.00 | $10.00 |
| [google/gemini-2.5-flash-lite](https://openrouter.ai/api/v1/models/google/gemini-2.5-flash-lite/endpoints) | Google AI Studio | `google-ai-studio/flex` | `flex` | $0.05 | $0.20 |
| [google/gemini-3.1-flash-lite](https://openrouter.ai/api/v1/models/google/gemini-3.1-flash-lite/endpoints) | Google AI Studio | `google-ai-studio/flex` | `flex` | $0.125 | $0.75 |

For every model, request one slug in `provider.only`, `allow_fallbacks=false`,
`require_parameters=true`, and the explicit `service_tier` shown above. Keep the
model IDs unchanged, optional reasoning disabled, and endpoint selection fixed
without price sorting. The published default slugs are `openai` and `anthropic`;
there is no `/default` suffix in this contract.

OpenRouter uses prefix matching for base provider slugs. The explicit default
tier excludes other tiers; it does not certify the effective endpoint identity.
See [provider selection](https://openrouter.ai/docs/guides/routing/provider-selection)
and [service tiers](https://openrouter.ai/docs/guides/features/service-tiers).

Run and task metadata record the requested endpoint and tier; task tags include
`service_tier`. The request sends the tier as a top-level body field through
Inspect's `extra_body`. Compare the request with the reported endpoint
ID, provider, model or permaslug, and service tier when available. Missing fields
remain unverified. A preflight must check this evidence, reported reasoning
usage, capture, and cost before the complete pilot.

Flex has lower processing priority. This experiment compares answers, not latency
between service tiers. Review timeout suitability separately; this decision does
not change timeouts or retry counts. The 50% price reduction applies to the three
Flex model tariffs, not to the full pilot cost. Calculate a new full estimate
from the executable routing configuration.

Inspect model names need the additional `openrouter/` prefix.

The comparison has two generation groups, each with one model per developer:

| Group | OpenAI | Anthropic | Google |
| --- | --- | --- | --- |
| `earlier` | GPT-4o mini | Sonnet 4.5 | Gemini 2.5 Flash-Lite |
| `later` | GPT-6 Luna | Sonnet 5 | Gemini 3.1 Flash-Lite |

These are explicit comparison groups, not synchronized release generations.
The group is stored in Inspect task metadata and tags.

## Pilot conditions

See [the architecture guide](architecture.md) before changing module boundaries.

The package domain configuration defines the model catalog and immutable
execution policy. The catalog lives in `llm_transitivity.domain.config`.
The Flow configuration and run metadata use these same definitions. `MODELS` and `MODEL_GROUPS` remain derived views in the package Flow adapter. New runs
archive the configuration source and its hash with the other source evidence.

Follow the [cost procedure](pilot_costs.md) to create a new estimate before
selecting a budget. An estimate is not a spending limit; budget enforcement
is still pending.

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

Use the scoring rules documented in the [README](../README.md#inspect-flow-pilot).
Report agreement with source labels separately from format compliance. These
labels have not been audited for logical validity.

`transitivity pilot` builds the coverage pilot through the package Flow adapter: 18 datasets
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
uv run --locked transitivity datasets verify
uv run --locked pytest -q
uv run --locked transitivity pilot --dry-run
```

The verifier checks all 54,000 full records against a fixed Git revision. It
allows only the two approved label translations, reproduces the selection,
and checks all pilot files and the system prompt. The
[manifest](../datasets/pilot/manifest.json) records source paths, hashes,
original row numbers, and selected record hashes. Rebuilding refuses to
overwrite existing evidence. The generated inventory retains capture-time
commands for byte verification. Use the commands here for current work.
Existing model logs are outside this verification.

Run both current previews:

```sh
uv run --locked transitivity pilot --dry-run
uv run --locked transitivity pilot --preflight --dry-run
```

Expect 108 tasks and 3,240 planned responses for the pilot, and six tasks and
six planned responses for the preflight. Previews confirm local task
construction, not provider access or model behavior. Do not use an earlier
dry-run report as evidence for the current code.

This provides reproducible evidence of exact sentence preservation, including
spaces, case, punctuation, and Unicode. It does not audit logical validity.
Tests also alter sentences, labels, identifiers, row order, original files,
pilot files, the manifest, and the system prompt to verify rejection.

After the trial, inspect all 3,240 outcomes, their metadata, errors, response
categories, token usage, and recorded costs before expanding the experiment.

## Readiness sequence

1. Verify the full corpus, manifest, source labels, and selected cases.
2. Run the tests and both previews with the current code.
3. Create a new cost estimate and review the requested endpoints and tiers.
4. Run a new live preflight. Check actual routing, reasoning usage, output,
   capture, generation lookups, and reported cost for all six models.
5. Resolve missing evidence and execution errors before the complete pilot.

Keep the original inputs and the deterministic selection. Restarting preparation
does not require a different sample. The verifier must reproduce its bytes and
hashes. Model cards remain dated catalog evidence, not proof of live access.

## Result directories

After the local checks and cost review, run one identical source case on each model:

```sh
uv run --locked transitivity pilot --preflight --dry-run
uv run --locked transitivity pilot --preflight
```

This selects one verified original row from the first pilot dataset, creates six
tasks, and records `phase:preflight`. Its result folder ends in `_preflight`.
The complete 540-case selection remains unchanged.

Use the managed entry point for a paid run:

```sh
uv run --locked transitivity pilot
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

`transitivity pilot --dry-run` creates no result archive. The installed command
provides the managed archive and finalization behavior for paid runs.
