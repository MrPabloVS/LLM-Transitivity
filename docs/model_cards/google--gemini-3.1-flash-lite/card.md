# Google: Gemini 3.1 Flash Lite

## Sources

- Model ID: `google/gemini-3.1-flash-lite`.
- Catalog page: [OpenRouter model card](https://openrouter.ai/google/gemini-3.1-flash-lite).
- Catalog source: [public model catalog](https://openrouter.ai/api/v1/models).
- Catalog fetched at UTC: `2026-11-05T22:14:11.709930+00:00`.
- Endpoint source: [public endpoint listing](https://openrouter.ai/api/v1/models/google/gemini-3.1-flash-lite/endpoints).
- Endpoints fetched at UTC: `2026-11-05T22:14:12.070419+00:00`.

## Published model information

- Canonical slug: `google/gemini-3.1-flash-lite-20260507`.
- Context length: 1048576 tokens.
- Top-provider output limit: 65536 tokens.
- Knowledge cutoff: Not reported.
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

- Published endpoint name: Google AI Studio | google/gemini-3.1-flash-lite-20260507.
- Input price: USD 0.125000000 per million text tokens.
- Output price: USD 0.75000000 per million text tokens.

These are endpoint quotes, not a billing guarantee. Account access and actual
routing need separate runtime evidence. See the [pilot decision](../../pilot.md).

The [complete endpoint response](endpoints.json) retains all provider variants,
supported parameters, limits, pricing fields, statuses and other returned data.

## Integrity

- `model.json` SHA-256: `9d0d2b2f05eb6e3fe0e8c5536fb23940e8d769f4156cc8add6cd92bf39a9172b`.
- `endpoints.json` SHA-256: `8fb15bc3f1f85f45a4aff38efee1da49c8e4cdf9a5abda5ccd5594d546edec8a`.
