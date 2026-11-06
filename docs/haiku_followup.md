# Haiku follow-up and direct 64-slot load

The user authorized preparation and execution of this follow-up, with no
spend-triggered pause. The later instruction selects direct load at 64;
16/32 load stages are omitted. Coverage stays at 16 to match the Sonnet pilot.
The default Sonnet profile and its historical evidence remain unchanged.

| Stage | Models | Tasks | Responses | Samples / connections | Active tasks |
| --- | ---: | ---: | ---: | ---: | ---: |
| Preflight | 6, Haiku profile | 6 | 6 | 16 / 16 | 1 |
| Haiku coverage | Haiku 4.5 and 5.5 | 36 | 1,080 | 16 / 16 | 1 |
| Direct load | 6, Haiku profile | 6 | 1,296 | 64 / 64 | 1 |
| Total | | 48 | 2,382 | | |

The load selection has 216 questions: two of the existing five cases in each
of 108 strata. It includes 72 HS and 144 mHS cases. SHA-256 ranking selects
cases, then restores dataset and source-row order. All original fields and
texts remain unchanged. The saved files are
[cases_216.json](../datasets/load/cases_216.json) and
[manifest.json](../datasets/load/manifest.json). Global sample UIDs distinguish
source row numbers that overlap between datasets.

## Latest execution

The [follow-up results](haiku_followup_results.md) record six preflight responses,
1,080 coverage responses, and 1,296 load responses. All six models passed the
direct 64-slot load gate, including observed sample and HTTP peaks of 64. The
known reported cost is USD 0.110887425; eleven generation IDs have unknown cost.

The first review stopped on missing telemetry for six filtered coverage responses.
The corrected policy treats confirmed filters as experimental outcomes. Missing
tier, reasoning usage, and cost remain explicitly unverified; contradictory
reported values still block execution. Filters do not trigger new generations.

Use `followup --continue-from <campaign> --detach` to derive new reviews from
saved preflight and coverage responses and run only load-64 under a new frozen
source snapshot. The continuation checks parent snapshots, input bytes, review
hashes, and native response hashes. It preserves the original stop review.
Ordinary `--resume` still requires unchanged source code. This continuation has
already completed; use its explicit directory to resume without new generations.

## Commands

```sh
uv run --locked transitivity datasets verify-load
uv run --locked transitivity followup --dry-run
uv run --locked transitivity costs --profile haiku --followup
uv run --locked transitivity followup --detach
uv run --locked transitivity followup --resume results/pilot/<campaign-directory> --detach
```

`prepare-load` creates the load files exclusively; `verify-load` reproduces
them from verified inputs. Dry-run does not create a run, request credentials,
fetch quotes, or call models. The default `pilot` remains Sonnet at 16.
Explicit pilot flags are `--profile`, repeated `--model`, `--concurrency`, and
`--load`; `--preflight` remains compatible and conflicts with `--load`.

A campaign has one root with frozen phase specs and snapshots, a fresh price
estimate, an event journal, detached PID and console, and per-phase native logs,
exports, and reviews. `execution.lock` prevents two local POSIX workers from
running the same campaign. Resume uses explicit frozen paths, verifies source
and snapshot hashes, reuses completed phases, and preserves partial Inspect
files in a checkpoint before native recovery. New closing indexes never
replace earlier ones. Interrupted in-flight requests may have unknown charges;
only completed saved samples can be reused with certainty.

## Technical checks

Both Haiku models request `anthropic`, tier `default`, no fallback, and explicit
reasoning disabled. Haiku 5.5 also requests `medium` effort. Preflight must
confirm emitted settings, reported provider/model/tier, zero reported reasoning
tokens, complete final capture, and reported cost. Missing fields are unverified.
Agreement and strict formatting are measured, not preflight acceptance criteria.
A failed technical phase prevents later phases.

Load is technically validated only if every model has all 216 final samples,
verified conditions, zero final errors, at most 5% failed attempts, and an
observed sample peak of 64. HTTP 4xx/5xx, missing responses, and provider errors
inside HTTP 200 count as failed attempts. Peak HTTP requests are reported
separately. One task active means at most 64 samples in progress; Inspect's
sample limit applies per task, so activating two tasks would change that limit.

No matched load at 16 or 32 is run. No measured speedup, 10% improvement, or
p90 ratio against those levels is claimed. Failure to validate 64 produces a
review recommendation; it does not launch fallback loads automatically.

All costs are deduplicated by generation ID across phases. Loads are separate
from coverage accuracy. Unknown cost remains unknown and does not stop the
program solely because of its amount. Provider/default reasoning settings,
metadata capture, retries, and output limits remain fixed.

## Decision and report

The campaign writes a separate Markdown report and machine-readable reviews.
It compares Haiku coverage with the same 540 case UIDs from the corrected
Sonnet pilot, retains per-case conditions and raw outputs, and projects full
costs by model and generation group. Time projections use the new 64-slot load;
they remain conditional on those measured latencies. No model replacement,
full-corpus launch, or push is automatic. Review the proposed design jointly.
