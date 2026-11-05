# Anthropic: Claude Sonnet 5

## Sources

- Model ID: `anthropic/claude-sonnet-5`.
- Catalog page: [OpenRouter model card](https://openrouter.ai/anthropic/claude-sonnet-5).
- Catalog source: [public model catalog](https://openrouter.ai/api/v1/models).
- Catalog fetched at UTC: `2026-11-05T22:14:11.709930+00:00`.
- Endpoint source: [public endpoint listing](https://openrouter.ai/api/v1/models/anthropic/claude-sonnet-5/endpoints).
- Endpoints fetched at UTC: `2026-11-05T22:14:12.149345+00:00`.

## Published model information

- Canonical slug: `anthropic/claude-sonnet-5-20260630`.
- Context length: 1000000 tokens.
- Top-provider output limit: 128000 tokens.
- Knowledge cutoff: Not reported.
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

- Published endpoint name: Anthropic | anthropic/claude-sonnet-5-20260630.
- Input price: USD 2.000000 per million text tokens.
- Output price: USD 10.00000 per million text tokens.

These are endpoint quotes, not a billing guarantee. Account access and actual
routing need separate runtime evidence. See the [pilot decision](../../pilot.md).

The [complete endpoint response](endpoints.json) retains all provider variants,
supported parameters, limits, pricing fields, statuses and other returned data.

## Integrity

- `model.json` SHA-256: `98fab05e4c3efa6a60357ad2b5f65b72404be85ab7f45afeefb5ff2025896084`.
- `endpoints.json` SHA-256: `867d9163e4e5f17ca820f561811523991aa074f540255ae482095d960bf35062`.
