# Pilot 3 results

Coverage completed 108 tasks and 3,240 saved samples, with no final sample
execution errors. The separate six-call preflight and coverage technical review
both passed. No full-corpus run was launched.

## Design

The six models received the same 540 selected source cases each. Pilot 3
replaced Sonnet 4.6 with Haiku 5.5 and increased samples per task from 32 to 64.
These simultaneous changes prevent a causal comparison of either change alone.
Haiku and Sonnet are different model families; group slots are not generations.

Providers were fixed and fallback disabled. Haiku 5.5 requested disabled
reasoning and medium effort. Sonnet 5.5 retained low effort with reasoning
enabled; Gemini 3.5 retained minimal effort with reasoning enabled. The other
controls, source text, labels, scoring v3, output cap, and selected UIDs remained
unchanged. See [the procedure](pilot3.md).

## Coverage outcomes

Agreement divides source-label matches by interpretable answers. Format and
interpretation coverage retain all 540 samples. Logical validity was not audited.

| Model | Agreement / interpreted | Strict format / 540 | Filters | Known USD |
| --- | ---: | ---: | ---: | ---: |
| openai/gpt-4o-mini | 405/540 | 506/540 | 0 | 0.00804330 |
| openai/gpt-6-luna | 458/540 | 540/540 | 0 | 0.00321430 |
| anthropic/claude-haiku-5.5 | 397/533 | 533/540 | 7 | 0.00785330 |
| anthropic/claude-sonnet-5.5 | 539/539 | 427/540 | 0 | 0.28594400 |
| google/gemini-3.1-flash-lite | 540/540 | 539/540 | 0 | 0.00615725 |
| google/gemini-3.5-flash-lite | 522/540 | 540/540 | 0 | 0.00757680 |

Seven Haiku 5.5 filters remain recorded as outcomes in Inspect. One Sonnet 5.5
response was not interpretable under the fixed deterministic rules. Neither
category was treated as a source-label disagreement or silently dropped.

## Execution and costs

Coverage took **215.22 seconds (3.59 minutes)** from its start event to its passed review.
There were **3,901 HTTP attempts**, including **655 failed attempts**, for 3,246 final samples across both phases.
Known reported cost, including preflight: **USD 0.319071025**.
There are **8 generation IDs with unknown costs** and **654 attempts without generation IDs**.
These amounts are not zero. Reported cost is incomplete and is not an invoice audit.

The automatic report counts identified generation IDs in its `generation_attempts`
field. Use the HTTP attempt count above for retries without IDs. No provider
fallback or replacement generation for a filter was used.

## Interpretation and next step

Haiku 5.5 was cheaper than Sonnet 4.6 in the preceding pilot, but had lower
source-label agreement and more filters. The unchanged models also vary between
runs. This is a small coverage selection with nondeterministic generations.

The larger concurrency did not remove retry overhead. Compare retry rates and
unknown costs before selecting sustained full-corpus concurrency. Completion
alone does not validate this schedule for 324,000 responses. No default model
replacement or full-corpus launch is automatic.

## Evidence

- [Frozen campaign](../results/pilot/2026-11-06_00-22-17-4747886d-pilot-3/campaign.json).
- [Native report](../results/pilot/2026-11-06_00-22-17-4747886d-pilot-3/report-ffb35997.md).
- [Event journal](../results/pilot/2026-11-06_00-22-17-4747886d-pilot-3/events.jsonl).
