# Anthropic: Claude Haiku 4.5

Status: candidate for the `earlier` group. This capture does not change the
executable model catalog or replace the completed Sonnet pilot.

## Sources

- Model ID: `anthropic/claude-haiku-4.5`.
- [OpenRouter catalog card](https://openrouter.ai/anthropic/claude-haiku-4.5).
- [Public model catalog](https://openrouter.ai/api/v1/models), fetched at UTC `2026-11-06T00:49:46.168929+00:00`.
- [Public endpoint listing](https://openrouter.ai/api/v1/models/anthropic/claude-haiku-4.5/endpoints), fetched at UTC `2026-11-06T00:49:48.485229+00:00`.
- [Manufacturer overview](https://platform.claude.com/docs/en/models/haiku-4-5/overview).
- [Manufacturer system card](https://www.anthropic.com/claude-haiku-4-5-system-card); [complete saved PDF](system-card.pdf), fetched at UTC `2026-11-06T00:49:48.654366+00:00`.
- [Manufacturer thinking controls](https://platform.claude.com/docs/en/build-with-claude/thinking#configuring-thinking).

## Published model information

- Canonical slug: `anthropic/claude-4.5-haiku-20251001`.
- Context length: 200000 tokens.
- Top-provider output limit: 64000 tokens.

The [complete catalog record](model.json) retains the source description,
architecture, prices, supported parameters, defaults, nulls, and unknown fields.
The [complete endpoint response](endpoints.json) retains all provider variants.

## Candidate endpoint and prices

- Proposed `provider.only`: `["anthropic"]`.
- Proposed service tier: `default`; provider fallback disabled; parameter support required.
- Published endpoint: Anthropic | anthropic/claude-4.5-haiku-20251001.
- Input: USD 1.00 per million text tokens.
- Output: USD 5.00 per million text tokens.

These are published endpoint quotes for short prompts, not observed charges.
All pricing fields and overrides remain in the endpoint snapshot. Haiku 5.5
has higher prices above its published long-prompt threshold; the current
benchmark questions are far below that threshold. Public availability does
not prove account access or effective routing.

## Reasoning compatibility

Haiku 4.5 uses manual extended thinking. The native API supports
`thinking: {"type": "disabled"}`. Thinking is off when omitted.

The selected OpenRouter endpoint lists `reasoning` support. This listing does
not prove that the transport maps the setting correctly or that a live call
uses zero reasoning tokens. Verify the emitted request and returned usage
before declaring the candidate compatible with the no-reasoning condition.
No paid model generation was made for this capture.

## Experiment interpretation

The proposed pair compares Haiku versions within the same model range.
It changes the Anthropic component of the design. Sonnet responses and their
historical and derived scores remain separate evidence. Haiku response length,
latency, and accuracy have not been measured on these 540 questions.

## Integrity

- `model.json` SHA-256: `acbbd1f27c3e6ac29c9185cf63fad5a34ee500cad057c1e89f59be27d6a9bbfb`.
- `endpoints.json` SHA-256: `11946b71e5c759b99bac92339cbfb52568d6cd91bf526cd2ef9b67bc8eff7fac`.
- `system-card.pdf` SHA-256: `1b9ae5f4f66a65c1b37a031179af3dba35959471a3a5d195e4fe700b87558141`.
