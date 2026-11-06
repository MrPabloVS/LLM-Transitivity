# Saved model cards

The readable cards summarize OpenRouter catalog information. The JSON
snapshots retain every published field returned during capture. Each readable
card links to its source, extracted model record, and complete endpoint response.
The new Haiku candidate captures also include complete manufacturer system-card
PDFs, with their own source URLs, capture times, and hashes.

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

## Haiku candidates

These candidates have not replaced the six models above. The completed Sonnet
pilot and its results remain unchanged. Native thinking controls are documented;
OpenRouter transport behavior, account access, and live usage remain unverified.

| Candidate model | Proposed group | Saved card | Proposed provider and tier |
| --- | --- | --- | --- |
| `anthropic/claude-haiku-4.5` | `earlier` | [Card](anthropic--claude-haiku-4.5/card.md) | `anthropic`, `default` |
| `anthropic/claude-haiku-5.5` | `later` | [Card](anthropic--claude-haiku-5.5/card.md) | `anthropic`, `default` |

[haiku-candidates-manifest.json](haiku-candidates-manifest.json) records this
new capture. The original six-model manifest and snapshots retain their bytes.

## Pilot 2.0

The [Pilot 2.0 manifest](pilot-2.0-manifest.json) references the shared files
below. There are no per-pilot model-card copies. Each model has one shared
directory. Identical files are reused. Changed captures have content-hash
filenames, so historical files retain their bytes.

| Group | Model | Selected card | Provider | Tier |
| --- | --- | --- | --- | --- |
| earlier | `openai/gpt-4o-mini` | [Card](openai--gpt-4o-mini/card-6c7e5c7c37f6.md) | `openai` | `default` |
| later | `openai/gpt-6-luna` | [Card](openai--gpt-6-luna/card-c92cf782bf12.md) | `openai/flex` | `flex` |
| earlier | `anthropic/claude-sonnet-4.6` | [Card](anthropic--claude-sonnet-4.6/card.md) | `anthropic` | `default` |
| later | `anthropic/claude-sonnet-5.5` | [Card](anthropic--claude-sonnet-5.5/card.md) | `anthropic` | `default` |
| earlier | `google/gemini-3.1-flash-lite` | [Card](google--gemini-3.1-flash-lite/card-118a223e4e22.md) | `google-ai-studio/flex` | `flex` |
| later | `google/gemini-3.5-flash-lite` | [Card](google--gemini-3.5-flash-lite/card.md) | `google-ai-studio/flex` | `flex` |

The manifest records all local file paths, source URLs, capture times, byte
counts, and SHA-256 hashes. It includes manufacturer PDFs and HTML documents.
The GPT-4o system card is a family document, not a dedicated mini card. Luna
documents describe their own release scope and do not prove the API revision.
See [Pilot 2.0 results](../pilot2_results.md) for the completed preflight and runtime checks.

Pilot 2.0 now uses reasoning only for Sonnet 5.5 (`low`) and Gemini 3.5
Flash-Lite (`minimal`). See [the current request policy](../pilot2.md). Saved
cards retain their capture-time descriptions; they do not replace that policy.
