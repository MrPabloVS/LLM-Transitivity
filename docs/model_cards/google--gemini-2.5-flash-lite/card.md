# Google: Gemini 2.5 Flash Lite

## Sources

- Model ID: `google/gemini-2.5-flash-lite`.
- Catalog page: [OpenRouter model card](https://openrouter.ai/google/gemini-2.5-flash-lite).
- Catalog source: [public model catalog](https://openrouter.ai/api/v1/models).
- Catalog fetched at UTC: `2026-11-05T22:14:11.709930+00:00`.
- Endpoint source: [public endpoint listing](https://openrouter.ai/api/v1/models/google/gemini-2.5-flash-lite/endpoints).
- Endpoints fetched at UTC: `2026-11-05T22:14:12.066648+00:00`.

## Published model information

- Canonical slug: `google/gemini-2.5-flash-lite`.
- Context length: 1048576 tokens.
- Top-provider output limit: 65535 tokens.
- Knowledge cutoff: 2025-01-31.
- Expiration date: Not reported.

The complete source description, architecture, pricing, default parameters,
supported parameters, links, and any additional fields remain in [model.json](model.json).
Missing values and explicit null values remain distinct in the JSON snapshot.

## Experiment endpoint decision

- Requested endpoint slug: `google-ai-studio/flex`.
- Requested service tier: `flex`.
- Routing: one provider only; fallback disabled; parameter support required.
- Optional reasoning: disabled.
- Status: approved decision; applying it to executable routing is pending.
- Actual endpoint and tier: not verified by this snapshot.

- Published endpoint name: Google AI Studio | google/gemini-2.5-flash-lite.
- Input price: USD 0.05000000 per million text tokens.
- Output price: USD 0.2000000 per million text tokens.

These are endpoint quotes, not a billing guarantee. Account access and actual
routing need separate runtime evidence. See the [pilot decision](../../pilot.md).

The [complete endpoint response](endpoints.json) retains all provider variants,
supported parameters, limits, pricing fields, statuses and other returned data.

## Integrity

- `model.json` SHA-256: `4da5ea71f0a55dd2720113918609042fa14378388c62b928c4b9a1a2a53c666b`.
- `endpoints.json` SHA-256: `86aef478b3891f6281d8db06b025baf65f47697191992b6bd35ad7757c5566ca`.
