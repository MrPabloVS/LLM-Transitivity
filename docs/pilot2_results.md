# Pilot 2.0 results

Run: `2026-11-05_23-57-32-0cdb9b69-pilot-2.0`.

## Decision summary

The pilot saved all planned responses and passed its technical checks. Gemini
3.1 Flash-Lite and Sonnet 5.5 matched all 540 source labels. Sonnet 4.6 matched
all 538 interpretable responses and filtered two cases. Higher version numbers
did not improve every result: Gemini 3.5 Flash-Lite had 13 disagreements.

The 108-task schedule completed in 3.79 minutes, but recovery required 456
additional HTTP attempts. Do not use completion alone as evidence that this
schedule is efficient or suitable for a sustained full-corpus run.

## What ran

Six models each received the same 540 cases from the preserved pilot selection.
Coverage completed 108 tasks and 3,240 saved samples. The separate preflight
completed six tasks and six samples. Both technical reviews passed. No final
sample execution errors remain. Agreement is with source labels; independent
logical validity has not been audited.

The comparison has mixed reasoning conditions. Sonnet 5.5 requested enabled
reasoning at `low`; Gemini 3.5 Flash-Lite requested enabled reasoning at
`minimal`. The other four models retain their earlier controls. Actual provider,
tier, request controls, and reported usage passed the per-model review.

All tasks fixed one provider and disabled fallback. Generation prompts, labels,
output cap, deterministic scoring v3, streaming, and caching policies retain
their specified values. The full 54,000-case corpus was not run.

## Inputs and experimental conditions

The full corpus has 54,000 records. This pilot uses 540 distinct source cases
(1% of the corpus), repeated across six models. It is a balanced coverage test,
not a random sample that supports population confidence claims.

The selection covers 18 datasets and 108 strata, with five cases per stratum.
There are 180 HS cases and 360 mHS cases. Conditions retain word-frequency
classes HF/LF/NS, tense FU/PA/PR, source validity, canonical or reversed order,
and connector forms. mHS denotes metainferential hypothetical syllogism cases.
The manifests retain original row numbers, stable UIDs, text hashes, source
identifiers, and labels. Source sentences and selection files were not changed.

Use [the execution guide](pilot2.md) for fixed providers, tiers, reasoning controls,
and the [shared model cards](model_cards/README.md#pilot-20) for saved manufacturer
and OpenRouter documents. Generation uses zero-shot prompts, a 1,024-token output
cap, disabled streaming and caching, and no provider fallback. The output cap
covers reasoning plus final text. Native logs retain complete captured responses.

## Coverage results

| Model | Agreement / interpreted | Strict format / 540 | Filters | Known reported USD |
| --- | ---: | ---: | ---: | ---: |
| openai/gpt-4o-mini | 407/540 | 500/540 | 0 | 0.00804690 |
| openai/gpt-6-luna | 448/540 | 540/540 | 0 | 0.00321430 |
| anthropic/claude-sonnet-4.6 | 538/538 | 535/540 | 2 | 0.19220100 |
| anthropic/claude-sonnet-5.5 | 540/540 | 429/540 | 0 | 0.28770400 |
| google/gemini-3.1-flash-lite | 540/540 | 539/540 | 0 | 0.00615725 |
| google/gemini-3.5-flash-lite | 527/540 | 540/540 | 0 | 0.00757680 |

Filters remain in coverage counts and are excluded from agreement denominators.
Inspect stores `status: content_filter`, the `content_filter_rate` metric, the
complete responses, and the captured OpenRouter payloads. No filter triggered
a replacement generation or fallback.

## Agreement, coverage, and format percentages

Agreement divides matches by interpretable answers. Interpretation coverage
and strict-format compliance divide by all 540 samples. An explanation can
agree with a source label while failing strict format.

| Model | Agreement | Interpretation coverage | Strict format |
| --- | ---: | ---: | ---: |
| openai/gpt-4o-mini | 75.37% | 100.00% | 92.59% |
| openai/gpt-6-luna | 82.96% | 100.00% | 100.00% |
| anthropic/claude-sonnet-4.6 | 100.00% | 99.63% | 99.07% |
| anthropic/claude-sonnet-5.5 | 100.00% | 100.00% | 79.44% |
| google/gemini-3.1-flash-lite | 100.00% | 100.00% | 99.81% |
| google/gemini-3.5-flash-lite | 97.59% | 100.00% | 100.00% |

## Reported reasoning usage

These are returned token counts, not proof about unreported internal processing.

| Model | Reported reasoning tokens | Samples with positive count | Missing usage |
| --- | ---: | ---: | ---: |
| openai/gpt-6-luna | 0 | 0 | 0 |
| anthropic/claude-sonnet-4.6 | 0 | 0 | 2 |
| anthropic/claude-sonnet-5.5 | 0 | 0 | 0 |
| google/gemini-3.5-flash-lite | 0 | 0 | 0 |
| google/gemini-3.1-flash-lite | 0 | 0 | 0 |
| openai/gpt-4o-mini | 0 | 0 | 0 |

## Execution and concurrency

Coverage took **227.52 seconds (3.79 minutes)** between its start event and passed review.
This includes task setup and finalization within the phase, not the separate
preflight. The schedule configured 108 active tasks and 32 samples per task.
The configured ceiling was 3,456; dataset sizes reduced the effective sample
ceiling to 2,808. Shared model connection limits were 576 per model.

| Model | HTTP attempts | Failed attempts | No generation ID | Observed sample peak | Observed HTTP peak | Sample p90 seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai/gpt-4o-mini | 624 | 84 | 84 | 465 | 381 | 132.51 |
| openai/gpt-6-luna | 615 | 75 | 70 | 461 | 391 | 160.79 |
| anthropic/claude-sonnet-4.6 | 643 | 103 | 103 | 458 | 355 | 161.63 |
| anthropic/claude-sonnet-5.5 | 614 | 74 | 74 | 461 | 387 | 148.05 |
| google/gemini-3.1-flash-lite | 583 | 43 | 43 | 463 | 420 | 158.81 |
| google/gemini-3.5-flash-lite | 617 | 77 | 77 | 463 | 386 | 144.37 |

HTTP peaks use captured complete response intervals; they do not establish
a peak for attempts with no response timestamp. Per-model peaks can occur at
different times and must not be added as a simultaneous global peak.
Across both phases there were **3,702 HTTP attempts** for **3,246 final samples**.
There were 456 failed attempts: 451 without a captured HTTP response and five
provider error responses inside HTTP 200. Configured retries recovered them.
These retries kept the same model, provider, and service tier.

## Costs and limits

Known reported cost, including preflight: **USD 0.505449725**.
There are **7 identified generations with unknown cost** and **451 attempts without generation IDs**.
Missing costs are unknown, not zero. A timeout does not prove that the provider
did no billable work. These costs cover this retained run only and are not an
independent invoice reconciliation.

The automatic report field `generation_attempts` counts identified generation
IDs. It does not count HTTP attempts without an ID; the complete HTTP attempt
count is shown above and in the per-model reviews.

## Full-corpus cost scenarios

A full pass has 54,000 responses per model: 162,000 per generation group,
or 324,000 across both groups. These scenarios scale observed final-response
costs by 100. They exclude preflight and unreported retry charges.

For the two Sonnet 4.6 filters, assume that each is charged at the mean cost
of its 538 non-filtered responses. This is an imputation, not a returned charge.
The seven unknown generation costs and 451 attempts without IDs remain unknown
in the observed-cost section.

| Model | Full-pass base USD |
| --- | ---: |
| openai/gpt-4o-mini | 0.80 |
| openai/gpt-6-luna | 0.32 |
| anthropic/claude-sonnet-4.6 | 19.29 |
| anthropic/claude-sonnet-5.5 | 28.77 |
| google/gemini-3.1-flash-lite | 0.62 |
| google/gemini-3.5-flash-lite | 0.76 |

| Scope | Responses | Base USD | Three charged attempts per response USD |
| --- | ---: | ---: | ---: |
| earlier | 162,000 | 20.71 | 62.14 |
| later | 162,000 | 29.85 | 89.56 |
| both | 324,000 | 50.56 | 151.69 |

The three-attempt scenario charges the same estimated token use three times.
It is a sensitivity scenario, not a maximum bill or a spending limit. Failures
can have different usage, and future response lengths and provider prices can
change. Do not transfer the original Sonnet 5 cost estimate to Sonnet 5.5.

## Full-corpus time scenario

Scaling the 227.52-second coverage phase by 100 gives **6.32 hours** for all
six models. This is a simple throughput scenario, not a validated runtime
forecast. The pilot tasks have only 20 or 40 cases; full tasks have 2,000 or
4,000. Setup, queueing, retry rates, and sustained provider limits will not
necessarily scale linearly. This run has no controlled lower-concurrency
baseline. Do not divide this time by two to estimate either generation group.
Measure the selected schedule before giving a firm full-run duration.

## Next step

Review model agreement and conditions before replacing any default models.
For a low-cost reference, retain Gemini 3.1 Flash-Lite: it matched all source
labels at a much lower observed cost than either Sonnet. Keep the Sonnet pair
if a comparison within that model family is part of the research question.
Review the 13 Gemini 3.5 disagreements and the two Sonnet 4.6 filtered cases
by source UID and condition before choosing the final model set. These results
do not establish that source labels are logically correct.
The run completed, but 456 failed attempts out of 3,702 total attempts (12.32%)
show that this parallel schedule needs review before a full-corpus launch.
Use a controlled load comparison or lower concurrency to measure retry overhead;
do not assume that the largest configured concurrency is the best sustained rate.
No full-corpus launch or model replacement is automatic.

## Evidence

- [Frozen campaign](../results/pilot/2026-11-05_23-57-32-0cdb9b69-pilot-2.0/campaign.json).
- [Preflight review](../results/pilot/2026-11-05_23-57-32-0cdb9b69-pilot-2.0/preflight/summary/review-d0359354.json).
- [Coverage review](../results/pilot/2026-11-05_23-57-32-0cdb9b69-pilot-2.0/coverage/summary/review-60b2b602.json).
- [Native automatic report](../results/pilot/2026-11-05_23-57-32-0cdb9b69-pilot-2.0/report-9c2aa4b7.md).
- [Event journal](../results/pilot/2026-11-05_23-57-32-0cdb9b69-pilot-2.0/events.jsonl).
