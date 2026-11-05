# Anthropic: Claude Sonnet 4.5

## Sources

- Model ID: `anthropic/claude-sonnet-4.5`.
- Catalog page: [OpenRouter model card](https://openrouter.ai/anthropic/claude-sonnet-4.5).
- Catalog source: [public model catalog](https://openrouter.ai/api/v1/models).
- Catalog fetched at UTC: `2026-11-05T22:14:11.709930+00:00`.
- Endpoint source: [public endpoint listing](https://openrouter.ai/api/v1/models/anthropic/claude-sonnet-4.5/endpoints).
- Endpoints fetched at UTC: `2026-11-05T22:14:11.862490+00:00`.

## Published model information

- Canonical slug: `anthropic/claude-4.5-sonnet-20250929`.
- Context length: 1000000 tokens.
- Top-provider output limit: 64000 tokens.
- Knowledge cutoff: 2025-01-31.
- Expiration date: Not reported.

The complete source description, architecture, pricing, default parameters,
supported parameters, links, and any additional fields remain in [model.json](model.json).
Missing values and explicit null values remain distinct in the JSON snapshot.

## Experiment endpoint decision

- Requested endpoint slug: `anthropic`.
- Requested service tier: `default`.
- Routing: one provider only; fallback disabled; parameter support required.
- Optional reasoning: disabled.
- Status: approved decision; applying it to executable routing is pending.
- Actual endpoint and tier: not verified by this snapshot.

- Published endpoint name: Anthropic | anthropic/claude-4.5-sonnet-20250929.
- Input price: USD 3.000000 per million text tokens.
- Output price: USD 15.000000 per million text tokens.

These are endpoint quotes, not a billing guarantee. Account access and actual
routing need separate runtime evidence. See the [pilot decision](../../pilot.md).

The [complete endpoint response](endpoints.json) retains all provider variants,
supported parameters, limits, pricing fields, statuses and other returned data.

## Integrity

- `model.json` SHA-256: `f0801e97590aba4620b1de1c264b7242475191a15497aae6728559226d0a1d13`.
- `endpoints.json` SHA-256: `a557b2761f4d728b80158ef46f4726fc86a53d043f4eb109361ae6aa5e3768ce`.
