# Six-model preflight review

Run: `2026-11-05_20-33-37-585189bb_preflight`.

Code revision: `8688c6a1e7a43068b231d3f1d9c9a4474ddce0e5`. The code was clean before launch.

All six requests returned HTTP 200 in one attempt each. Total reported generation cost: **USD 0.002935525**.

All six returned the requested provider and service tier and reported zero reasoning tokens. The routing metadata header reached each request and its response object was captured.

| Model | Requested endpoint | Tier | Input | Output | Cost USD | Source agreement | Strict format |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| `openai/gpt-4o-mini` | `openai` | `default` | 74 | 2 | 0.0000123 | True | False |
| `openai/gpt-6-luna` | `openai/flex` | `flex` | 73 | 5 | 0.0000049 | True | True |
| `anthropic/claude-sonnet-4.5` | `anthropic` | `default` | 72 | 164 | 0.002676 | True | False |
| `anthropic/claude-sonnet-5` | `anthropic` | `default` | 95 | 4 | 0.00023 | True | True |
| `google/gemini-2.5-flash-lite` | `google-ai-studio/flex` | `flex` | 65 | 1 | 0.00000345 | True | True |
| `google/gemini-3.1-flash-lite` | `google-ai-studio/flex` | `flex` | 65 | 1 | 0.000008875 | True | True |

## Response format

GPT-4o mini returned `Yes.`. Sonnet 4.5 returned an explanation ending with a separate `Yes`. Both agree with the source label but fail the exact yes/no format rule. The other four responses meet that rule. No output or score was changed.

Sonnet 4.5 used 164 ordinary output tokens while reporting zero reasoning tokens. Visible explanation text is retained as completion output.

## Evidence

All models used the same source row and stable sample UID. Original text and source identifiers match. Native log hashes and every frozen source snapshot hash were checked. Credentials were absent from parsed native logs and call exports.

Immediate generation lookups were unavailable. A read-only export refresh returned HTTP 200 for all six generation IDs. Refreshed costs match the original responses. Original logs and exports remain unchanged.

Observed endpoint IDs and canonical model identifiers are retained in [the JSON review](preflight_review.json). The public saved cards do not map endpoint IDs to routing slugs. Provider and tier agreement is verified; an independent ID-to-slug mapping is not claimed.

Native task metadata keeps its configuration-time verification placeholders. This review records observed evidence separately. Stored-content lookups were not requested.

## Next step

The complete pilot has not run. Review the format outcomes and agree on a budget before requesting 3,240 responses. One shared case does not establish accuracy or lexical coverage. Source-label agreement does not establish audited logical validity.
