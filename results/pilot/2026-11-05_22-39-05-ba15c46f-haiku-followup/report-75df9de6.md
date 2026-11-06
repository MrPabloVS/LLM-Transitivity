# Haiku follow-up results

Campaign: `ba15c46f-5b76-48a1-b804-5f1f830c20ff`.

The user selected direct 64-slot load, with one active task. Load at 16 and 32
was omitted by request. Coverage still uses 16 slots. Original Sonnet evidence
is unchanged. The full corpus was not run and no default model was replaced.

## Phase results

| Stage | Samples | Technical checks | Known reported USD | Unknown cost IDs |
| --- | ---: | --- | ---: | ---: |
| preflight | 6 | Passed | 0.00013752 | 0 |
| coverage | 1080 | Stopped; review faults | 0.07349660 | 6 |
| load-64 | 0 | Omitted after a failed prior stage | — | — |

Total known reported cost: **USD 0.07363412**; 6 generation IDs have unknown cost.
Missing costs are not zero. These are returned charges, not an independent invoice audit.

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

64-slot technical validation: **False**.
Validation requires complete verified samples, zero final errors, at most 5%
failed attempts per model, and observed peak sample concurrency of 64.
An internal provider error in HTTP 200 counts as a failed attempt.
No 10% speedup or p90 ratio against 16/32 can be tested without matched loads.

## Full-pass scenarios

| Group | Responses | Projected USD | Central hours at 64 | Slow hours at 64 |
| --- | ---: | ---: | ---: | ---: |
| earlier | 162000 | 7.61 | not available | not available |
| later | 162000 | not available | not available | not available |
| all | 324000 | not available | not available | not available |

Cost scales final-response usage within the balanced coverage selection by 100.
The four unchanged models retain their original pilot cost basis. Haiku uses
the new 540-case pilot. Unknown failed-attempt charges are excluded.
Time schedules the full source order at 64 using mean and interpolated p90
durations from the 216-case load, plus measured nonnegative task overhead
once per dataset. There are only two observations per stratum. These are
conditional scenarios, not confidence bounds or delivery guarantees.

## Recommendation

Resolve the failed preflight or coverage checks before running more generations.

Keep the current default profile until that review. No spend-triggered pause was
configured, as requested. A complete corpus run needs a separate decision.

[Machine-readable comparison and projections](report-75df9de6.json).
