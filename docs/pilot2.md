# Pilot 2.0

Status: the preflight and coverage pilot completed. See [the results](pilot2_results.md).
The historical Sonnet and Haiku results remain separate from this experiment.
The historical Sonnet and Haiku results remain unchanged.

## Models and fixed providers

| Group | OpenRouter model | Provider | Tier | Input USD/M | Output USD/M |
| --- | --- | --- | --- | ---: | ---: |
| earlier | `openai/gpt-4o-mini` | `openai` | default | 0.15 | 0.60 |
| later | `openai/gpt-6-luna` | `openai/flex` | flex | 0.05 | 0.25 |
| earlier | `anthropic/claude-sonnet-4.6` | `anthropic` | default | 3.00 | 15.00 |
| later | `anthropic/claude-sonnet-5.5` | `anthropic` | default | 2.00 | 10.00 |
| earlier | `google/gemini-3.1-flash-lite` | `google-ai-studio/flex` | flex | 0.125 | 0.75 |
| later | `google/gemini-3.5-flash-lite` | `google-ai-studio/flex` | flex | 0.15 | 1.25 |

Prices above are the selected endpoint quotes captured for this preparation.
They are not the standard Google API prices. The
[saved cards](model_cards/README.md#pilot-20) retain complete endpoint payloads
and manufacturer documents. Their manifest records sources and hashes.
Groups are relative to this comparison. The original group assignments remain
unchanged in historical results. Haiku is not part of Pilot 2.0.

## Cases and concurrency

Use the existing 540 selected cases across 18 datasets and 108 strata. Do not
regenerate the selection, change source sentences, or change source labels.
Each model receives the same cases. Total coverage is 3,240 responses in 108 tasks.
A separate preflight adds six responses in six tasks.

Coverage uses 108 active tasks and at most 32 samples per task. The configured
sample ceiling is 3,456. Each of nine HS datasets has 20 cases, and each of nine
mHS datasets has 40. The effective ceiling is therefore
`6 * (9 * 20 + 9 * 32) = 2,808` samples.

Inspect shares its connection pool across tasks for the same model and account.
Set the shared connection limit to `18 * 32 = 576` per model. This permits the
requested per-task schedule; it does not prove that the provider will sustain
that load. Native capture times establish observed concurrency and throughput.
Preflight remains sequential, with one active task and one selected case per model.

## Request and result policy

Keep zero-shot prompts, output cap 1,024 tokens, scoring v3, retry policy,
no caching, no streaming, fixed provider, and no fallback. Every task sets
`provider.allow_fallbacks: false`, exactly one `provider.only` entry, and
`provider.require_parameters: true`. Retries use that same model, endpoint,
and tier. Provider errors do not authorize a different model, provider, or tier.
The user authorized reasoning only for the two endpoints that require it:

| Model | Requested reasoning | Effort |
| --- | --- | --- |
| GPT-4o mini | Not supported | Omitted |
| GPT-6 Luna | Disabled | Omitted |
| Sonnet 4.6 | Disabled | medium |
| Sonnet 5.5 | Enabled | **low** |
| Gemini 3.1 Flash-Lite | Disabled | Omitted |
| Gemini 3.5 Flash-Lite | Enabled | **minimal** |

These are the lowest published effort levels for the two enabled models. See
[Sonnet effort](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide)
and [Gemini 3.5 Flash-Lite](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-5-flash-lite).
This comparison has mixed reasoning conditions. Do not describe all six models
as running without reasoning. The output cap includes reasoning and final text.
Preflight checks emitted controls, routing, and returned usage per model.
Disabled models must report zero reasoning tokens. Enabled models can report
zero or positive reasoning usage; missing usage remains unverified. Runtime
reviews use the controls frozen in each native log, not a later catalog value.

Inspect stores filtered responses with score metadata `status: content_filter`
and reports the task metric `content_filter_rate`. Their score value is `N`
(uninterpretable). They remain outside the source-agreement denominator, while
response coverage and filter counts retain every sample. Full responses and
OpenRouter capture fields remain in the native logs and exports.

Content filters are outcomes. They do not stop the program or trigger
replacement generations. Missing tier, reasoning usage, and costs on confirmed
filtered responses remain unverified. Reported contradictory values remain faults.
Agreement is with source labels, not independently audited logical validity.

Each phase has its own native logs, call exports, source snapshots, and closing
review under a common Pilot 2.0 campaign. Tags retain all source conditions,
model, provider, tier, group, phase, profile, active tasks, and sample limit.
The model-card manifest and effective JSON cards are included in source snapshots.
Manufacturer documents retain their original bytes in the separate card capture.

## Commands

```sh
uv run --locked transitivity followup --profile pilot2 --dry-run
uv run --locked transitivity costs --profile pilot2
uv run --locked transitivity followup --profile pilot2 --prepare-only
```

Prepare-only fetches public quotes and freezes both phase specs. It does not
load credentials or request model generations. Use the returned explicit directory
for a later launch:

```sh
uv run --locked transitivity followup --resume results/pilot/<pilot2-directory> --detach
```

The worker verifies frozen hashes before each phase. A failed technical preflight
prevents coverage. It records complete exports and a separate report. It does not
start the full corpus or change the historical default Sonnet profile.
