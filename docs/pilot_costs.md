# Pilot cost procedure

Create a new estimate after changes to inputs, models, routing, or execution
policy. Earlier estimates are not evidence for the current pilot.

```sh
uv run --locked transitivity datasets verify
uv run --locked transitivity costs
```

The cost command queries public OpenRouter endpoint prices. It does not request
model generations, load Inspect, or create a pilot run. It reads the verified
pilot inputs and the shared model catalog and execution policy.

Each estimate is saved under
`results/cost_estimates/<local-date-time>-<id>/estimate.json`.
The command prints the exact path. Each capture uses a new directory and does
not replace earlier captures. Use the capture from the current preparation.

Check the capture time, source hashes, input manifest hash, all six model IDs,
provider slugs, requested tiers, output limit, and retry assumptions. A published
endpoint quote does not establish access through the account. Quote retrieval
requires one exact endpoint tag. It does not filter or interpret endpoint
`status`. The live preflight checks access and observed routing separately.

The estimator reports short-answer, verbose-answer, full-output, and retry
scenarios. Input token counts are planning proxies, not each provider's native
token counts. The byte-input scenario is not a proven upper bound. The output
limit is a maximum, not a fixed charge.

An estimate is not a spending limit. Agree on a budget and enforcement before
the complete pilot. Use a new live preflight to check reported usage and cost.
Missing usage must remain unresolved, not zero. Follow the readiness sequence
in [the pilot guide](pilot.md).
