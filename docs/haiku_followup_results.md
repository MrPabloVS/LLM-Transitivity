# Haiku follow-up results and load decision

Status: preflight passed and all 1,080 coverage responses were saved. The coverage
review stopped the program because six Haiku 5.5 filtered responses omit tier,
usage, and cost. The 64-slot load was not executed. No 16/32 loads were scheduled.

## What ran

| Phase | Completed tasks | Saved responses | State |
| --- | ---: | ---: | --- |
| Six-model preflight | 6 | 6 | Passed request and response checks |
| Two-model Haiku coverage at 16 | 36 | 1,080 | Execution complete; six unverified filtered responses |
| Six-model load at 64 | 0 of 6 | 0 of 1,296 | Omitted by the technical gate |

All 42 executed tasks have native status `success`, with no final sample execution
errors. A successful Inspect task can contain a filtered response. Task execution
success is distinct from complete experimental verification. No responses were
regenerated, no provider fallback was used, and no full-corpus run was started.

## Agreement and response format

Every candidate received the same 540 source questions as its Sonnet comparison.
Agreement uses interpretable answers; format uses all 540 scored samples.
Source logical validity has not been independently audited.

| Model | Agree / interpreted | Agreement | Strict format / scored | Filtered | Known coverage USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| anthropic/claude-haiku-4.5 | 540/540 | 100.00% | 172/540 (31.85%) | 0 | 0.06563200 |
| anthropic/claude-sonnet-4.5 (prior pilot) | 540/540 | 100.00% | 73/540 (13.52%) | 0 | 1.43093100 |
| anthropic/claude-haiku-5.5 | 403/534 | 75.47% | 534/540 (98.89%) | 6 | 0.00786460 |
| anthropic/claude-sonnet-5 (prior pilot) | 540/540 | 100.00% | 540/540 (100.00%) | 0 | 0.15674400 |

Haiku 4.5 matched all selected source labels at much lower reported cost than
Sonnet 4.5. Its strict-format compliance is still only 31.85%; punctuation and
other output forms remain separate from source-label agreement. Haiku 5.5 had
131 disagreements and six filtered responses. Do not fold the filters into `no`
or exclude them silently from coverage reporting.

## Why the load stopped

The six blocked responses report `finish_reason: content_filter` and native
reason `refusal`. They contain no usage object and report `service_tier: null`.
The provider refusal text classifies the requests under its explosives policy,
although the saved requests are formal reasoning questions, including pseudowords.
This is an observed provider response, not a judgment that the benchmark asks for
such instructions. The source questions and provider settings were not changed.

The other 534 Haiku 5.5 responses passed the routing, usage, and cost checks.
The six refusals leave actual tier, reasoning-token count, and charge unverified.
A later read-only lookup for each of their generation IDs remained unavailable.
Unknown cost is not zero. Provider-suggested fallback was not enabled.

| Filtered sample UID | Family | Words | Tense | Source target |
| --- | --- | --- | --- | --- |
| `HS_LF_FU_2000:340:a166a2ef3f0b4329` | HS | LF | FU | yes |
| `HS_NS_FU_2000:1476:dba3b1067eac8e36` | HS | NS | FU | yes |
| `HS_NS_PR_2000:173:310db17b135d5eb8` | HS | NS | PR | yes |
| `mHS_LF_FU_4000:21:f9abcbce92077710` | mHS | LF | FU | yes |
| `mHS_NS_FU_4000:422:adf88b36a28db81f` | mHS | NS | FU | yes |
| `mHS_NS_PA_4000:1390:b66edbc84e1dfd3a` | mHS | NS | PA | no |

## Condition results

Each cell is agreement count / interpretable count. All selected cases remain
represented in the per-case review; filtered cases reduce only the interpretation
denominator. The category tables above retain their separate count.

### dataset_family

| Condition | Haiku 4.5 | Haiku 5.5 | Haiku 5.5 filters |
| --- | ---: | ---: | ---: |
| HS | 180/180 | 120/177 | 3 |
| mHS | 360/360 | 283/357 | 3 |

### frequency

| Condition | Haiku 4.5 | Haiku 5.5 | Haiku 5.5 filters |
| --- | ---: | ---: | ---: |
| HF | 180/180 | 149/180 | 0 |
| LF | 180/180 | 118/178 | 2 |
| NS | 180/180 | 136/176 | 4 |

### verbal_time

| Condition | Haiku 4.5 | Haiku 5.5 | Haiku 5.5 filters |
| --- | ---: | ---: | ---: |
| FU | 180/180 | 126/176 | 4 |
| PA | 180/180 | 136/179 | 1 |
| PR | 180/180 | 141/179 | 1 |

### canonical_form

| Condition | Haiku 4.5 | Haiku 5.5 | Haiku 5.5 filters |
| --- | ---: | ---: | ---: |
| canonic | 270/270 | 200/265 | 5 |
| non-canonic | 270/270 | 203/269 | 1 |

### source_validity

| Condition | Haiku 4.5 | Haiku 5.5 | Haiku 5.5 filters |
| --- | ---: | ---: | ---: |
| invalid | 270/270 | 139/269 | 1 |
| valid | 270/270 | 264/265 | 5 |

### connectors

| Condition | Haiku 4.5 | Haiku 5.5 | Haiku 5.5 filters |
| --- | ---: | ---: | ---: |
| assuming that we can infer / thus | 180/180 | 161/177 | 3 |
| from the inference (therefore) / does the inference follow | 180/180 | 122/180 | 0 |
| if then / therefore | 180/180 | 120/177 | 3 |

## Original cases for manual review

These are exact source texts and saved outputs. Review source labels separately
from model agreement, especially for mHS and reversed premise order.

### HS disagreement

Sample `HS_HF_FU_2000:1542:d2dab6b2eb8f440e`. Source target `no`; Haiku 5.5 returned `yes`.

> If the student will see the computer, then the teacher will hate the program; if the girl will lose the book, then the student will see the computer; therefore if the teacher will hate the program, then the girl will lose the book?

[Native log](../results/pilot/2026-11-05_22-39-05-ba15c46f-haiku-followup/coverage/inspect/2026-11-06T01-39-42-00-00_zeroShot-HS-HF-FU-20_Kwj8UKpL94siLuQHJ9Ai3u.eval).

### mHS disagreement

Sample `mHS_HF_FU_4000:3286:69b321e2d65fd1d4`. Source target `no`; Haiku 5.5 returned `yes`.

> Assuming that the officer will pay the sugar, we can infer that the family will buy the newspaper. Assuming that the woman will love the money, we can infer that the officer will pay the sugar. Thus, assuming that the family will buy the newspaper, can we infer that the woman will love the money?

[Native log](../results/pilot/2026-11-05_22-39-05-ba15c46f-haiku-followup/coverage/inspect/2026-11-06T01-39-42-00-00_zeroShot-mHS-HF-FU-40_a23RgKTcmzALRmQMbNe5YD.eval).

### Filtered pseudoword case

Sample `HS_NS_FU_2000:1476:dba3b1067eac8e36`. Source target `yes`. Provider result: `content_filter`.

> If the prackler will prant the blorrack, then the bruggant will frike the flendop; if the brettent will blemp the ploodnum, then the prackler will prant the blorrack; therefore if the brettent will blemp the ploodnum, then the bruggant will frike the flendop?

[Native log, including the complete refusal](../results/pilot/2026-11-05_22-39-05-ba15c46f-haiku-followup/coverage/inspect/2026-11-06T01-39-42-00-00_zeroShot-HS-NS-FU-20_QeuhuXqy4Yj4gCLXLS7pcW.eval).

## Cost and time projections

Known reported follow-up cost, including preflight: **USD 0.073634125**.
There were 1,086 captured generation attempts and no generation retries. Six
generation IDs have no reported cost. This is not an independently reconciled
account invoice. Read-only metadata refreshes requested no new generations.

The complete `earlier` group with Haiku 4.5 projects to **USD 7.61** for
162,000 responses: USD 6.5632 from Haiku 4.5 plus the observed-cost projections
for GPT-4o mini and Gemini 2.5 Flash-Lite. Haiku 4.5 alone is substantially
below the Sonnet 4.5 full-pass projection of USD 143.0931.

The six-model known-component subtotal would be **USD 9.331735** if known
coverage charges were scaled by 100 and combined with the four unchanged
models. It is **not a complete total**: it excludes the unknown charges for
six filtered Haiku 5.5 cases. No amount is imputed for those records.

**There is no new validated runtime estimate at 64.** The load never started.
Earlier 6–7 hour figures used unchanged Sonnet latency as an unmeasured scenario;
they must not be described as observed Haiku throughput or a verified speedup.

## Recommendation

Do not automatically replace the Sonnet pair or declare 64 validated. Haiku 4.5
is a promising lower-cost candidate on these cases. Haiku 5.5 needs joint review
because of its lower agreement, filters, and missing refusal telemetry.

The next decision is how to handle provider refusals that omit usage: keep the
current requirement and stop, or explicitly revise the protocol to retain those
cases as filtered outcomes with unverified fields. Any revised gate needs a new
version and tests; historical responses and the stopped review must stay intact.
Do not reword source questions, enable fallback, or rerun the 540 cases to hide
the refusals. A future authorized load can use the saved 216-case selection
without repeating the completed coverage pilot.

For a concurrency comparison, one task at 64 can later be compared with two
tasks at 32. Inspect limits samples per task, so two tasks at 64 could have
128 samples in progress. That comparison was not executed here.

## Evidence

- [Automatic campaign report](../results/pilot/2026-11-05_22-39-05-ba15c46f-haiku-followup/report-75df9de6.md).
- [Frozen campaign and stage plan](../results/pilot/2026-11-05_22-39-05-ba15c46f-haiku-followup/campaign.json).
- [Coverage review with all cases, conditions, outputs, and log hashes](../results/pilot/2026-11-05_22-39-05-ba15c46f-haiku-followup/coverage/summary/review-44c59cb9.json).
- [Read-only metadata refresh for filtered responses](../results/pilot/2026-11-05_22-39-05-ba15c46f-haiku-followup/postrun-filter-lookups.json).
- [Event journal, including the omitted load reason](../results/pilot/2026-11-05_22-39-05-ba15c46f-haiku-followup/events.jsonl).
