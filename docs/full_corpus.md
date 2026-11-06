# Full-corpus run

The user authorized all 54,000 verified cases for each of the six Pilot 3 models.
The run has 108 tasks and 324,000 planned corpus responses. A separate six-call
preflight checks access, capture, routing, and the per-model reasoning controls.
A failed technical preflight prevents corpus generations.

Use 108 active tasks, 64 samples per task, and a static shared model connection
limit of 1,152. The configured sample ceiling is 6,912. Adaptive connections are
not used. Fixed providers, tiers, disabled fallbacks, retry policy, caching,
streaming, output cap, and reasoning controls remain those of
[Pilot 3](pilot3.md). Sonnet 5.5 uses low effort and Gemini 3.5 Flash-Lite uses
minimal effort; both have reasoning enabled. Other models retain their controls.

Selection includes every source row in original dataset order. The original
inputs and labels, existing normalized datasets, and pilot selection remain
unchanged. Native sample UIDs, provenance, targets, source identifiers, tags,
and deterministic scoring retain their definitions. Filters remain outcomes
and do not trigger replacement generations. Unknown costs remain unknown.

The [Pilot 3 report](pilot3_results.md) records retry overhead. The full-run
schedule is the user's selected static configuration; it is not a claim that
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
