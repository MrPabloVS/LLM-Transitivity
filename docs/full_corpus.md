# Full-corpus run

The user authorized all 54,000 verified cases for each of the six Pilot 3 models.
The run has 108 tasks and 324,000 planned corpus responses. A separate six-call
preflight checks access, capture, routing, and the per-model reasoning controls.
A failed technical preflight prevents corpus generations.

Use six active tasks out of 108 total tasks and 32 samples per task. The configured sample ceiling is
192. Each model has an independent adaptive connection controller shared by its
18 datasets: minimum 10, start 20, maximum 64. The controller uses a 15-second
cooldown, a decrease factor of 0.8, and steady-state growth of 0.05. Explicit
`max_connections` is unset so it does not disable adaptation. The six models
start with a combined connection limit of 120. The maximum is a ceiling, not a
throughput target. Waiting samples still occupy task sample slots. Tasks are
ordered by dataset, then model. Thus the first six tasks cover all six models.
As tasks finish at different times, six active tasks does not guarantee one task
per model throughout the run. Inspect flushes completed samples every 32 samples.
See the [startup analysis](full_corpus_startup.md) for the evidence and limits.

HTTP 429 responses reduce the connection limit. Timeouts, network errors, and
5xx responses pause growth but do not reduce it. Thus adaptation does not prove
that the earlier startup problem is resolved. Inspect records the observed
changes in `stats.connection_limit_history`. See the
[Inspect concurrency guide](https://inspect.aisi.org.uk/models-concurrency.html).

The earlier static full-corpus attempt was interrupted without saved corpus
samples. Its local files and quote were removed at the user's request. Start a
new run with new frozen sources and a new quote; do not resume that attempt.

Fixed providers, tiers, disabled fallbacks, retry policy, caching,
streaming, output cap, and reasoning controls remain those of
[Pilot 3](pilot3.md). Sonnet 5.5 uses low effort and Gemini 3.5 Flash-Lite uses
minimal effort; both have reasoning enabled. Other models retain their controls.

Selection includes every source row in original dataset order. The original
inputs and labels, existing normalized datasets, and pilot selection remain
unchanged. Native sample UIDs, provenance, targets, source identifiers, tags,
and deterministic scoring retain their definitions. Filters remain outcomes
and do not trigger replacement generations. Unknown costs remain unknown.

The [Pilot 3 report](pilot3_results.md) records retry overhead. The full-run
schedule is the user's selected adaptive configuration; it is not a claim that
this capacity is optimal or sustained. Reported failures are retained.

```sh
uv run --locked transitivity full --dry-run
uv run --locked transitivity full --prepare-only
uv run --locked transitivity full --detach
uv run --locked transitivity full --resume results/full/<directory> --detach
```

Preparation verifies all records, saves fresh quotes for the actual full inputs,
and freezes source code, working datasets, model-card references, and both phase
specifications. It creates a unique directory under `results/full/`. Quotes
exclude the extra six preflight calls and are scenarios, not spending limits.

The detached worker records its PID, console, phase events, native Inspect logs,
call exports, and closure indexes. A lock prevents concurrent workers for one
directory. Resume verifies frozen hashes, skips passed phases, and uses Inspect
recovery with a checkpoint to reuse saved samples. Completed closure requires
108 final successful tasks, 324,000 saved samples, and zero final sample errors.
Per-call routing, usage, cost, and response analysis remains separate from that
completion check. Historical pilots remain unchanged.
