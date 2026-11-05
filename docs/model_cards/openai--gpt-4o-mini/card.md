# OpenAI: GPT-4o-mini

## Sources

- Model ID: `openai/gpt-4o-mini`.
- Catalog page: [OpenRouter model card](https://openrouter.ai/openai/gpt-4o-mini).
- Catalog source: [public model catalog](https://openrouter.ai/api/v1/models).
- Catalog fetched at UTC: `2026-11-05T22:14:11.709930+00:00`.
- Endpoint source: [public endpoint listing](https://openrouter.ai/api/v1/models/openai/gpt-4o-mini/endpoints).
- Endpoints fetched at UTC: `2026-11-05T22:14:11.860939+00:00`.

## Published model information

- Canonical slug: `openai/gpt-4o-mini`.
- Context length: 128000 tokens.
- Top-provider output limit: 16384 tokens.
- Knowledge cutoff: 2023-10-31.
- Expiration date: Not reported.

The complete source description, architecture, pricing, default parameters,
supported parameters, links, and any additional fields remain in [model.json](model.json).
Missing values and explicit null values remain distinct in the JSON snapshot.

## Experiment endpoint decision

- Requested endpoint slug: `openai`.
- Requested service tier: `default`.
- Routing: one provider only; fallback disabled; parameter support required.
- Optional reasoning: disabled.
- Status: approved decision; applying it to executable routing is pending.
- Actual endpoint and tier: not verified by this snapshot.

- Published endpoint name: OpenAI | openai/gpt-4o-mini.
- Input price: USD 0.15000000 per million text tokens.
- Output price: USD 0.6000000 per million text tokens.

These are endpoint quotes, not a billing guarantee. Account access and actual
routing need separate runtime evidence. See the [pilot decision](../../pilot.md).

The [complete endpoint response](endpoints.json) retains all provider variants,
supported parameters, limits, pricing fields, statuses and other returned data.

## Integrity

- `model.json` SHA-256: `dc0d1f977fa77898f06797a2600d3a711cfca9cb8a80e254f118e6202ab8990b`.
- `endpoints.json` SHA-256: `56d75aa413c870c9adfe9c88c7aa4b8708fbf395eed0a8a03f49794639b20019`.
