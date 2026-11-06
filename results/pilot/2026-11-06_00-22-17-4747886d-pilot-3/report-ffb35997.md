# Pilot 3 results

Campaign: `4747886d-3505-4d29-8399-88abc3c317f5`.

The experiment compares six models on the same 540 source cases per model.
Coverage configures 108 active tasks and 64 samples per task. The configured
ceiling is 6912. Dataset sizes reduce the effective sample ceiling to 3240.
Shared connection pools allow 1152 requests per model. All selected providers
are fixed. Observed concurrency and response checks are reported below.

Agreement uses source labels, not independently audited logical validity.
Filters remain outcomes, with missing usage and costs unverified. No filter
triggers a replacement generation. Strict format requires only yes or no.

Known reported cost: USD 0.319071025. Unknown cost IDs: 8.
Captured generation attempts: 3247.

| Phase | Model | Samples | Agreement / interpreted | Strict format | Filters | Attempts / failed | Sample / HTTP peak | Known USD |
| --- | --- | ---: | --- | --- | ---: | --- | --- | ---: |
| preflight | openai/gpt-4o-mini | 1 | 1/1 | 1/1 | 0 | 1/0 | 1/1 | 0.000011700 |
| preflight | openai/gpt-6-luna | 1 | 1/1 | 1/1 | 0 | 1/0 | 1/1 | 0.000004900 |
| preflight | anthropic/claude-haiku-5.5 | 1 | 1/1 | 1/1 | 0 | 1/0 | 1/1 | 0.000011600 |
| preflight | anthropic/claude-sonnet-5.5 | 1 | 1/1 | 1/1 | 0 | 1/0 | 1/1 | 0.000234000 |
| preflight | google/gemini-3.1-flash-lite | 1 | 1/1 | 1/1 | 0 | 1/0 | 1/1 | 0.000008875 |
| preflight | google/gemini-3.5-flash-lite | 1 | 1/1 | 1/1 | 0 | 1/0 | 1/1 | 0.000011000 |
| coverage | openai/gpt-4o-mini | 540 | 405/540 | 506/540 | 0 | 612/72 | 539/467 | 0.008043300 |
| coverage | openai/gpt-6-luna | 540 | 458/540 | 540/540 | 0 | 689/149 | 539/391 | 0.003214300 |
| coverage | anthropic/claude-haiku-5.5 | 540 | 397/533 | 533/540 | 7 | 655/115 | 498/383 | 0.007853300 |
| coverage | anthropic/claude-sonnet-5.5 | 540 | 539/539 | 427/540 | 0 | 632/92 | 538/446 | 0.285944000 |
| coverage | google/gemini-3.1-flash-lite | 540 | 540/540 | 539/540 | 0 | 640/100 | 537/437 | 0.006157250 |
| coverage | google/gemini-3.5-flash-lite | 540 | 522/540 | 540/540 | 0 | 667/127 | 539/412 | 0.007576800 |

Technical reviews retain all sample UIDs, conditions, responses, missing fields,
source hashes, and configuration faults. Native logs and source data are unchanged.
No full-corpus run or default model replacement is automatic.
