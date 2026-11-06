# Anthropic: Claude Haiku 5.5

Status: candidate for the `later` group. This capture does not change the
executable model catalog or replace the completed Sonnet pilot.

## Sources

- Model ID: `anthropic/claude-haiku-5.5`.
- [OpenRouter catalog card](https://openrouter.ai/anthropic/claude-haiku-5.5).
- [Public model catalog](https://openrouter.ai/api/v1/models), fetched at UTC `2026-11-06T00:49:46.168929+00:00`.
- [Public endpoint listing](https://openrouter.ai/api/v1/models/anthropic/claude-haiku-5.5/endpoints), fetched at UTC `2026-11-06T00:49:46.615122+00:00`.
- [Manufacturer overview](https://platform.claude.com/docs/en/models/haiku-5-5/overview).
- [Manufacturer system card](https://www.anthropic.com/document/claude-haiku-5-5-system-card); [complete saved PDF](system-card.pdf), fetched at UTC `2026-11-06T00:49:48.824446+00:00`.
- [Manufacturer thinking controls](https://platform.claude.com/docs/en/build-with-claude/thinking#configuring-thinking).

## Published model information

- Canonical slug: `anthropic/claude-haiku-5.5-20261007`.
- Context length: 1000000 tokens.
- Top-provider output limit: 128000 tokens.

The [complete catalog record](model.json) retains the source description,
architecture, prices, supported parameters, defaults, nulls, and unknown fields.
The [complete endpoint response](endpoints.json) retains all provider variants.

## Candidate endpoint and prices

- Proposed `provider.only`: `["anthropic"]`.
- Proposed service tier: `default`; provider fallback disabled; parameter support required.
- Published endpoint: Anthropic | anthropic/claude-haiku-5.5-20261007.
- Input: USD 0.10 per million text tokens.
- Output: USD 0.50 per million text tokens.

These are published endpoint quotes for short prompts, not observed charges.
All pricing fields and overrides remain in the endpoint snapshot. Haiku 5.5
has higher prices above its published long-prompt threshold; the current
benchmark questions are far below that threshold. Public availability does
not prove account access or effective routing.

## Reasoning compatibility

Haiku 5.5 enables adaptive thinking by default. The native API accepts
`thinking: {"type": "disabled"}` at `low`, `medium`, or `high` effort.
It rejects that combination at `xhigh` or `max`. Lower effort alone does not
disable thinking. The new tokenizer uses approximately 30% more tokens for
the same text than Haiku 4.5; the exact increase depends on the text.

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

- `model.json` SHA-256: `7ebfd1495207031fa251c23fe1f5fdc319a34b0a7156ab211033ea658789b944`.
- `endpoints.json` SHA-256: `8eeba3c35da24724076814739da76f26e504b736097fb4858e095a45d13a940d`.
- `system-card.pdf` SHA-256: `d5dbaab6996c02ad6ff28b032ce5a9c7582e59af09b5d1bc0975cf0235535da9`.
