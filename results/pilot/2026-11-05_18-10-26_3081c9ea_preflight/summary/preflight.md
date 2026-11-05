# Six-model preflight

Run: `2026-11-05_18-10-26_3081c9ea_preflight`. Command: `uv run --locked run_pilot.py --preflight`.

Total reported generation cost: **USD 0.00215715**. All six requests returned HTTP 200. Each model used one HTTP attempt.

| Model | Provider | Input tokens | Output tokens | Reasoning tokens | Cost USD | Strict format |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| openai/gpt-4o-mini | OpenAI | 74 | 1 | 0 | 0.00001170 | True |
| openai/gpt-6-luna | OpenAI | 73 | 5 | 0 | 0.00000980 | True |
| anthropic/claude-sonnet-5 | Anthropic | 95 | 4 | 0 | 0.00023000 | True |
| google/gemini-2.5-flash-lite | Google AI Studio | 65 | 1 | 0 | 0.00000690 | True |
| anthropic/claude-sonnet-4.5 | Anthropic | 72 | 111 | 0 | 0.00188100 | False |
| google/gemini-3.1-flash-lite | Google AI Studio | 65 | 1 | 0 | 0.00001775 | True |

Immediate generation lookups returned HTTP 404. Later read-only lookups returned HTTP 200 for all six calls. Original Inspect logs remain unchanged.

Costs in the generation lookup match costs in the original response for all six calls. The refreshed exports retain full lookup payloads, including native token counts and provider details.

Sonnet 4.5 ends with Yes after an explanation. The current initial-answer parser records invalid_format and does not extract that final answer. The raw response is preserved.

The full 3,240-response pilot has not started. One case per model does not estimate accuracy or output length across all strata. This run does not set a spending limit.

See `preflight.json` for log and export paths. See `../provenance/` for frozen inputs and the run configuration.
