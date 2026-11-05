# Retired six-model preflight

Historical run: `2026-11-05_18-10-26_3081c9ea_preflight`.

Status: retired. Its 61 result and provenance files were removed at the user's
request on November 5, 2026. The summary below records the previous observation;
it does not validate the current code or the selected Flex routing decision.
The complete pilot remains unrun. A replacement preflight is pending.

After the selected endpoint and tier settings are implemented, the replacement
command is `uv run --locked transitivity pilot --preflight`. It makes paid model
requests. This cleanup did not run that command.

Total reported generation cost: **USD 0.00215715**. All six requests returned HTTP 200. Each model used one HTTP attempt.

| Model | Provider | Input tokens | Output tokens | Reasoning tokens | Cost USD | Strict format |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| openai/gpt-4o-mini | OpenAI | 74 | 1 | 0 | 0.00001170 | True |
| openai/gpt-6-luna | OpenAI | 73 | 5 | 0 | 0.00000980 | True |
| anthropic/claude-sonnet-5 | Anthropic | 95 | 4 | 0 | 0.00023000 | True |
| google/gemini-2.5-flash-lite | Google AI Studio | 65 | 1 | 0 | 0.00000690 | True |
| anthropic/claude-sonnet-4.5 | Anthropic | 72 | 111 | 0 | 0.00188100 | False |
| google/gemini-3.1-flash-lite | Google AI Studio | 65 | 1 | 0 | 0.00001775 | True |

Immediate generation lookups returned HTTP 404. Later read-only lookups returned HTTP 200 for all six calls. The original logs were preserved during that refresh; the run archive has now
been removed as stated above.

Costs in the generation lookup match costs in the original response for all six calls. The refreshed exports retain full lookup payloads, including native token counts and provider details.

Sonnet 4.5 ends with Yes after an explanation. The initial-answer parser used in this run records invalid_format and does not extract that final answer. The raw response is preserved.

The later `initial_or_final_line_v1` rule extracts this final Yes and records
source-label agreement with `format_compliant=false`. This was checked offline
against the stored response. That offline comparison did not change the original scores. The archive was
removed later as stated above.

The full 3,240-response pilot has not started. One case per model does not estimate accuracy or output length across all strata. This run does not set a spending limit.

The removed archive remains recoverable from local Git commit `3312a4c` under
`results/pilot/2026-11-05_18-10-26_3081c9ea_preflight/`. No Git history was rewritten.
