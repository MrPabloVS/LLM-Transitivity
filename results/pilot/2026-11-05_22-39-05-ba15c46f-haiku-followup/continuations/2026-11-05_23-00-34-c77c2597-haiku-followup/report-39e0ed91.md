# Haiku follow-up results

Campaign: `c77c2597-242c-4ea2-9d0e-473628d27c40`.

The user selected direct 64-slot load, with one active task. Load at 16 and 32
was omitted by request. Coverage still uses 16 slots. Original Sonnet evidence
is unchanged. The full corpus was not run and no default model was replaced.

## Phase results

| Stage | Samples | Technical checks | Known reported USD | Unknown cost IDs |
| --- | ---: | --- | ---: | ---: |
| preflight | 6 | Passed | 0.00013752 | 0 |
| coverage | 1080 | Passed | 0.07349660 | 6 |
| load-64 | 1296 | Passed | 0.03725330 | 5 |

Total known reported cost: **USD 0.11088742**; 11 generation IDs have unknown cost.
Missing costs are not zero. These are returned charges, not an independent invoice audit.
Confirmed content filters are experimental outcomes. Missing tier, reasoning usage,
and cost remain unverified. Passed checks do not imply these fields were reported.
Filtered samples by phase: `{'preflight': 0, 'coverage': 6, 'load-64': 3}`.
Unverified field counts by phase: `{'preflight': 0, 'coverage': 18, 'load-64': 9}`.

## Haiku answers

| Model | Agreement / interpreted | Strict format / scored |
| --- | ---: | ---: |
| anthropic/claude-haiku-4.5 | 540/540 | 172/540 |
| anthropic/claude-haiku-5.5 | 403/534 | 534/540 |

Agreement refers to source labels, not independently audited logical validity.
Load responses are excluded from this accuracy table. Pairing, case details,
conditions, outputs, and source hashes are retained in the per-phase reviews.

## Direct 64-slot load

| Model | Cases/min | Sample p90 seconds | Peak samples | Peak HTTP | Failed attempts |
| --- | ---: | ---: | ---: | ---: | ---: |
| openai/gpt-4o-mini | 576.1520542893318 | 7.829000000000001 | 64 | 64 | 0/216 |
| openai/gpt-6-luna | 385.8281035230203 | 8.7405 | 64 | 64 | 2/218 |
| anthropic/claude-haiku-4.5 | 578.2767679539859 | 7.938 | 64 | 64 | 0/216 |
| anthropic/claude-haiku-5.5 | 532.7515611706646 | 7.8345 | 64 | 64 | 0/216 |
| google/gemini-2.5-flash-lite | 573.5456831771899 | 7.132999999999999 | 64 | 64 | 0/216 |
| google/gemini-3.1-flash-lite | 661.6396014834125 | 7.077 | 64 | 64 | 0/216 |

64-slot technical validation: **True**.
Validation requires complete verified samples, zero final errors, at most 5%
failed attempts per model, and observed peak sample concurrency of 64.
An internal provider error in HTTP 200 counts as a failed attempt.
No 10% speedup or p90 ratio against 16/32 can be tested without matched loads.

## Full-pass scenarios

| Group | Responses | Projected USD | Central hours at 64 | Slow hours at 64 |
| --- | ---: | ---: | ---: | ---: |
| earlier | 162000 | 7.61 | 4.07 | 4.35 |
| later | 162000 | not available | 4.14 | 4.47 |
| all | 324000 | not available | 8.21 | 8.82 |

Cost scales final-response usage within the balanced coverage selection by 100.
The four unchanged models retain their original pilot cost basis. Haiku uses
the new 540-case pilot. Unknown failed-attempt charges are excluded.
Time schedules the full source order at 64 using mean and interpolated p90
durations from the 216-case load, plus measured nonnegative task overhead
once per dataset. There are only two observations per stratum. These are
conditional scenarios, not confidence bounds or delivery guarantees.

## Recommendation

Review Haiku agreement, format, costs, and paired cases jointly before replacing
Sonnet. Review mHS and reversed-order source labels manually. No accuracy
threshold automatically selects a model.
The direct load supports considering 64 for this profile; it does not prove a speedup.

Keep the current default profile until that review. No spend-triggered pause was
configured, as requested. A complete corpus run needs a separate decision.

[Machine-readable comparison and projections](report-39e0ed91.json).
