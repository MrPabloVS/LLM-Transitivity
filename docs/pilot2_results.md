# Pilot 2.0 results

Run: `2026-11-05_23-57-32-0cdb9b69-pilot-2.0`.

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

## Next step

Review model agreement and conditions before replacing any default models.
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
