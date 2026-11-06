# Full-corpus startup analysis

The adaptive attempt `2026-11-06_01-05-10-8879bdd9` stopped at the user's request.
It used 108 active tasks, 32 sample slots per task, and adaptive connections
with minimum 10, start 20, and maximum 576 per model. Its six-call preflight
passed. The corpus target was 324,000 responses.

## Observed evidence

- The interrupted native logs contain 3,440 samples and no saved sample errors.
- Those samples contain 3,440 captured HTTP attempts, all with HTTP 200.
- Saved sample duration: median 62.76 seconds; p90 104.91 seconds.
- Captured HTTP duration: median 1.96 seconds; p90 18.26 seconds.
- At the 11-minute check, the process used about 100% CPU and 8 GB RSS.
- The live control query failed after eight 15-second response timeouts. Inspect
  reported that the evaluation event loop was busy.
- The console records repeated sample timeouts and retries. These in-flight
  samples are not represented by the 3,440 saved successful samples.
- SIGINT and SIGTERM did not stop the worker. SIGKILL was required. The worker
  is no longer running. Existing logs, source snapshots, and input hashes remain.

Local evidence is under
`results/full/2026-11-06_01-05-10-8879bdd9/`: the interruption record is
`operator_interruption.json`, and native logs are under `corpus/inspect/`.
These partial results are not included in this source commit.
The attempt did not reach normal finalization. These counts describe saved
samples only. They do not establish the number of requests that the provider
processed or billed. Unknown charges remain unknown.

## Interpretation and change

Local CPU load and delayed control responses support reducing active work in
this process. They do not identify the exact hot function or exclude provider
problems. Sample duration includes connection waits, generation, retries, and
metadata collection; its difference from HTTP duration is not a CPU measurement.
The successful-sample subset cannot measure the overall HTTP failure rate.

The next configuration uses six active tasks with 32 sample slots each, for a
192-slot ceiling. Each model retains adaptive connections with minimum 10,
start 20, and maximum 64. The cooldown, reduction, and growth settings remain
15 seconds, 0.8, and 0.05. Task order is dataset then model so the first six tasks
include all six models. Later model overlap depends on completion order.

The log buffer changes from 200 to 32 samples to shorten the interval before
completed samples reach disk. This can add write overhead; it is not a fix for
CPU saturation. Models, fixed providers, fallback restrictions, prompts,
source cases, targets, scoring, output cap, reasoning controls, request timeouts,
and retry budgets remain unchanged. The total remains 108 tasks and 324,000
responses. These changes require live validation before claiming stability.

This analysis does not launch another paid attempt. Do not edit the interrupted
run's frozen configuration or bypass its source-hash checks. The changed code
cannot directly resume that old snapshot. Reuse of saved responses requires an
explicit recovery step that preserves the original evidence and records the
new execution controls. Do not assume a new full run will reuse them.
