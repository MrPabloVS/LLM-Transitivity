# Pilot cost estimate

This saved estimate uses the previous all-standard routing. The executable
catalog now selects three Flex endpoints and three default endpoints, as recorded
in [the pilot guide](pilot.md). New estimates use those selected endpoints and
record each requested tier. This document and its JSON snapshot retain the
original standard-tier calculation; they are not a current Flex budget.

Quotes checked on November 5, 2026, against the exact standard-provider endpoints
listed in [the machine-readable estimate](pilot_cost_estimate.json). The estimate
uses the 540 actual pilot inputs for each of six models, or 3,240 planned answers.
No model generation was requested to calculate it.

## Scenarios

| Scenario | Total USD |
| --- | ---: |
| 4 output tokens per answer; one attempt | $0.36 |
| 128 output tokens per answer; one attempt | $2.24 |
| 1,024 output tokens per answer; one attempt | $15.79 |
| Byte-input planning envelope, 1,024 output tokens and all three attempts charged | $51.87 |

The first three scenarios use `o200k_base` text counts plus 16 framing tokens
per case as a common proxy: 54,026 input tokens per model. This is not the native
tokenizer of every provider. The last scenario uses UTF-8 input bytes plus 256
framing tokens per case: 322,502 planning tokens per model. It is a conservative
planning envelope, not a proven upper bound or an enforced spending limit.

The 1,024-token limit is a maximum, not a fixed charge. A short answer costs less
than a response that uses the full output allowance. Retried attempts can still
be billed, so the last scenario charges full input and output for every attempt.

## Quotes and per-model estimates

| Model | Fixed provider | Input USD / 1M | Output USD / 1M | Short-answer scenario | Full-output scenario, one attempt |
| --- | --- | ---: | ---: | ---: | ---: |
| GPT-4o mini | OpenAI | $0.15 | $0.60 | $0.0094 | $0.3399 |
| GPT-6 Luna | OpenAI | $0.10 | $0.50 | $0.0065 | $0.2819 |
| Sonnet 4.5 | Anthropic | $3.00 | $15.00 | $0.1945 | $8.4565 |
| Sonnet 5 | Anthropic | $2.00 | $10.00 | $0.1297 | $5.6377 |
| Gemini 2.5 Flash-Lite | Google AI Studio | $0.10 | $0.40 | $0.0063 | $0.2266 |
| Gemini 3.1 Flash-Lite | Google AI Studio | $0.25 | $1.50 | $0.0167 | $0.8429 |

These quotes assume standard short-prompt prices, disabled reasoning, no tools,
no caching, and no batch discounts. Taxes, credit-funding fees, future price
changes, and unexpected provider behavior are outside the calculation.
The JSON retains each endpoint's price payload and the exact input manifest hash.

## Retry policy and next decision

The SDK previously defaulted to two retries in addition to Inspect's two retries.
That could multiply to nine HTTP attempts. The pilot now sets SDK retries to zero
and keeps Inspect's two retries: at most three planned attempts per generation.
No extra Flow evaluation-set retry is enabled. This policy does not cover a
manual relaunch of the pilot.

The budget amount and enforcement mechanism are not yet agreed or configured.
Choose them before the full pilot. The authorized six-call preflight cost
USD 0.00215715. It confirmed the fixed providers and zero reported reasoning
tokens. See [the retired preflight summary](pilot_preflight.md). Missing usage must
remain unresolved, not zero.

Recalculate current quotes and assumptions with:

```sh
uv run --locked transitivity costs
```

This command makes public pricing queries and saves a new snapshot under
`results/cost_estimates/<local-date-time>-<id>/estimate.json`. It prints the
snapshot path. Each capture uses a new directory and exclusive file creation;
existing captures and the historical JSON linked above remain unchanged.
The command does not launch a pilot or enforce a budget. Compare new snapshots
with the assumptions in this historical report when reviewing current costs.

## Configuration source

The estimator reads the package domain model catalog and execution policy.
The catalog lives in `llm_transitivity.domain.config`. The estimator verifies
the pilot inputs without constructing Inspect tasks or creating a run identity. Future reports include `experiment_config_sha256`
and `source_sha256` for the package implementation, in addition to the existing
hash fields, now calculated from package sources. The saved quote snapshot
above keeps the evidence from its original calculation.
