# Saved model cards

These are OpenRouter catalog cards, not manufacturer system cards. The JSON
snapshots retain every published field returned during capture. Each readable
card links to its source, extracted model record, and complete endpoint response.

These files describe their capture time. Statements inside a card such as
"applying it to executable routing is pending" record that time, not current
readiness. Use [the pilot guide](../pilot.md) for the current routing decision,
preparation status, and live preflight requirements. Preserve the captured cards
and their hashes.

The model-level pricing and top-provider fields can differ from the selected
experiment endpoint. Use the selected endpoint section for its quoted prices.
Published availability is separate from account access and observed routing.

| Model | Saved card | Experiment endpoint | Requested tier |
| --- | --- | --- | --- |
| `openai/gpt-4o-mini` | [Card](openai--gpt-4o-mini/card.md) | `openai` | `default` |
| `openai/gpt-6-luna` | [Card](openai--gpt-6-luna/card.md) | `openai/flex` | `flex` |
| `anthropic/claude-sonnet-4.5` | [Card](anthropic--claude-sonnet-4.5/card.md) | `anthropic` | `default` |
| `anthropic/claude-sonnet-5` | [Card](anthropic--claude-sonnet-5/card.md) | `anthropic` | `default` |
| `google/gemini-2.5-flash-lite` | [Card](google--gemini-2.5-flash-lite/card.md) | `google-ai-studio/flex` | `flex` |
| `google/gemini-3.1-flash-lite` | [Card](google--gemini-3.1-flash-lite/card.md) | `google-ai-studio/flex` | `flex` |

[manifest.json](manifest.json) records sources, UTC capture times, file hashes
and requested routing choices. The snapshots use no credentials or model
generations. Existing run evidence remains unchanged.

Preserve these files when refreshing cards. Save a future capture separately.
