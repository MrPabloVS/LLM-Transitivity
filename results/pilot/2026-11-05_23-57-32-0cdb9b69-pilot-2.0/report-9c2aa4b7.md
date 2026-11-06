# Pilot 2.0 results

Campaign: `0cdb9b69-7eca-41a7-aaa6-6f1099d11756`.

The experiment compares six models on the same 540 source cases per model.
Coverage configures 108 active tasks and 32 samples per task. The configured
ceiling is 3456. Dataset sizes reduce the effective sample ceiling to 2808.
Shared connection pools allow 576 requests per model. All selected providers
are fixed. Observed concurrency and response checks are reported below.

Agreement uses source labels, not independently audited logical validity.
Filters remain outcomes, with missing usage and costs unverified. No filter
triggers a replacement generation. Strict format requires only yes or no.

Known reported cost: USD 0.505449725. Unknown cost IDs: 7.
Captured generation attempts: 3251.

| Phase | Model | Samples | Agreement / interpreted | Strict format | Filters | Attempts / failed | Sample / HTTP peak | Known USD |
| --- | --- | ---: | --- | --- | ---: | --- | --- | ---: |
| preflight | openai/gpt-4o-mini | 1 | 1/1 | 1/1 | 0 | 1/0 | 1/1 | 0.000011700 |
| preflight | openai/gpt-6-luna | 1 | 1/1 | 1/1 | 0 | 1/0 | 1/1 | 0.000004900 |
| preflight | anthropic/claude-sonnet-4.6 | 1 | 1/1 | 1/1 | 0 | 1/0 | 1/1 | 0.000279000 |
| preflight | anthropic/claude-sonnet-5.5 | 1 | 1/1 | 1/1 | 0 | 1/0 | 1/1 | 0.000234000 |
| preflight | google/gemini-3.1-flash-lite | 1 | 1/1 | 1/1 | 0 | 1/0 | 1/1 | 0.000008875 |
| preflight | google/gemini-3.5-flash-lite | 1 | 1/1 | 1/1 | 0 | 1/0 | 1/1 | 0.000011000 |
| coverage | openai/gpt-4o-mini | 540 | 407/540 | 500/540 | 0 | 624/84 | 465/381 | 0.008046900 |
| coverage | openai/gpt-6-luna | 540 | 448/540 | 540/540 | 0 | 615/75 | 461/391 | 0.003214300 |
| coverage | anthropic/claude-sonnet-4.6 | 540 | 538/538 | 535/540 | 2 | 643/103 | 458/355 | 0.192201000 |
| coverage | anthropic/claude-sonnet-5.5 | 540 | 540/540 | 429/540 | 0 | 614/74 | 461/387 | 0.287704000 |
| coverage | google/gemini-3.1-flash-lite | 540 | 540/540 | 539/540 | 0 | 583/43 | 463/420 | 0.006157250 |
| coverage | google/gemini-3.5-flash-lite | 540 | 527/540 | 540/540 | 0 | 617/77 | 463/386 | 0.007576800 |

Technical reviews retain all sample UIDs, conditions, responses, missing fields,
source hashes, and configuration faults. Native logs and source data are unchanged.
No full-corpus run or default model replacement is automatic.
