# OpenAI: GPT-6 Luna

## Sources

- Model ID: `openai/gpt-6-luna`.
- Catalog page: [OpenRouter model card](https://openrouter.ai/openai/gpt-6-luna).
- Catalog source: [public model catalog](https://openrouter.ai/api/v1/models).
- Catalog fetched at UTC: `2026-11-05T22:14:11.709930+00:00`.
- Endpoint source: [public endpoint listing](https://openrouter.ai/api/v1/models/openai/gpt-6-luna/endpoints).
- Endpoints fetched at UTC: `2026-11-05T22:14:11.858262+00:00`.

## Published model information

- Canonical slug: `openai/gpt-6-luna-20260922`.
- Context length: 1050000 tokens.
- Top-provider output limit: 128000 tokens.
- Knowledge cutoff: Not reported.
- Expiration date: Not reported.

The complete source description, architecture, pricing, default parameters,
supported parameters, links, and any additional fields remain in [model.json](model.json).
Missing values and explicit null values remain distinct in the JSON snapshot.

## Experiment endpoint decision

- Requested endpoint slug: `openai/flex`.
- Requested service tier: `flex`.
- Routing: one provider only; fallback disabled; parameter support required.
- Optional reasoning: disabled.
- Status: approved decision; applying it to executable routing is pending.
- Actual endpoint and tier: not verified by this snapshot.

- Published endpoint name: OpenAI | openai/gpt-6-luna-20260922.
- Input price: USD 0.05000000 per million text tokens.
- Output price: USD 0.25000000 per million text tokens.

These are endpoint quotes, not a billing guarantee. Account access and actual
routing need separate runtime evidence. See the [pilot decision](../../pilot.md).

The [complete endpoint response](endpoints.json) retains all provider variants,
supported parameters, limits, pricing fields, statuses and other returned data.

## Integrity

- `model.json` SHA-256: `c518cd2c33cae9e47e052fb83a78f58f1032ec5a541df70c3c21ead2e93e45c3`.
- `endpoints.json` SHA-256: `c0521a85f58787cfbb89f16ad3d6b3e2d7a92171d48341cb2a129b5f0441cba7`.
