# Pilot result details

These tables use the derived v3 scoring. Each cell is source-label agreements /
interpreted responses. All selected responses are interpretable after correction.
The same cases are compared across models; source logical validity is not audited.

Column order: GPT-4o mini, GPT-6 Luna, Sonnet 4.5, Sonnet 5, Gemini 2.5 Flash-Lite,
and Gemini 3.1 Flash-Lite. All breakdowns refer to the same 540 cases per model.

## dataset_family

| Condition | 4o mini | Luna | Sonnet 4.5 | Sonnet 5 | Gemini 2.5 | Gemini 3.1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| HS | 165/180 | 162/180 | 180/180 | 180/180 | 158/180 | 180/180 |
| mHS | 247/360 | 288/360 | 360/360 | 360/360 | 259/360 | 360/360 |

## frequency

| Condition | 4o mini | Luna | Sonnet 4.5 | Sonnet 5 | Gemini 2.5 | Gemini 3.1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| HF | 141/180 | 154/180 | 180/180 | 180/180 | 141/180 | 180/180 |
| LF | 133/180 | 130/180 | 180/180 | 180/180 | 134/180 | 180/180 |
| NS | 138/180 | 166/180 | 180/180 | 180/180 | 142/180 | 180/180 |

## verbal_time

| Condition | 4o mini | Luna | Sonnet 4.5 | Sonnet 5 | Gemini 2.5 | Gemini 3.1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| FU | 136/180 | 148/180 | 180/180 | 180/180 | 144/180 | 180/180 |
| PA | 131/180 | 148/180 | 180/180 | 180/180 | 133/180 | 180/180 |
| PR | 145/180 | 154/180 | 180/180 | 180/180 | 140/180 | 180/180 |

## canonical_form

| Condition | 4o mini | Luna | Sonnet 4.5 | Sonnet 5 | Gemini 2.5 | Gemini 3.1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| canonic | 240/270 | 240/270 | 270/270 | 270/270 | 229/270 | 270/270 |
| non-canonic | 172/270 | 210/270 | 270/270 | 270/270 | 188/270 | 270/270 |

## connectors

| Condition | 4o mini | Luna | Sonnet 4.5 | Sonnet 5 | Gemini 2.5 | Gemini 3.1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| assuming that we can infer / thus | 134/180 | 165/180 | 180/180 | 180/180 | 102/180 | 180/180 |
| from the inference (therefore) / does the inference follow | 113/180 | 123/180 | 180/180 | 180/180 | 157/180 | 180/180 |
| if then / therefore | 165/180 | 162/180 | 180/180 | 180/180 | 158/180 | 180/180 |

## source_validity

| Condition | 4o mini | Luna | Sonnet 4.5 | Sonnet 5 | Gemini 2.5 | Gemini 3.1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| invalid | 262/270 | 180/270 | 270/270 | 270/270 | 147/270 | 270/270 |
| valid | 150/270 | 270/270 | 270/270 | 270/270 | 270/270 | 270/270 |

## working_dataset

| Condition | 4o mini | Luna | Sonnet 4.5 | Sonnet 5 | Gemini 2.5 | Gemini 3.1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| HS_HF_FU_2000 | 20/20 | 20/20 | 20/20 | 20/20 | 18/20 | 20/20 |
| HS_HF_PA_2000 | 20/20 | 20/20 | 20/20 | 20/20 | 18/20 | 20/20 |
| HS_HF_PR_2000 | 19/20 | 20/20 | 20/20 | 20/20 | 18/20 | 20/20 |
| HS_LF_FU_2000 | 19/20 | 13/20 | 20/20 | 20/20 | 20/20 | 20/20 |
| HS_LF_PA_2000 | 16/20 | 12/20 | 20/20 | 20/20 | 15/20 | 20/20 |
| HS_LF_PR_2000 | 18/20 | 17/20 | 20/20 | 20/20 | 15/20 | 20/20 |
| HS_NS_FU_2000 | 17/20 | 20/20 | 20/20 | 20/20 | 19/20 | 20/20 |
| HS_NS_PA_2000 | 16/20 | 20/20 | 20/20 | 20/20 | 16/20 | 20/20 |
| HS_NS_PR_2000 | 20/20 | 20/20 | 20/20 | 20/20 | 19/20 | 20/20 |
| mHS_HF_FU_4000 | 26/40 | 30/40 | 40/40 | 40/40 | 29/40 | 40/40 |
| mHS_HF_PA_4000 | 27/40 | 33/40 | 40/40 | 40/40 | 28/40 | 40/40 |
| mHS_HF_PR_4000 | 29/40 | 31/40 | 40/40 | 40/40 | 30/40 | 40/40 |
| mHS_LF_FU_4000 | 25/40 | 28/40 | 40/40 | 40/40 | 28/40 | 40/40 |
| mHS_LF_PA_4000 | 26/40 | 28/40 | 40/40 | 40/40 | 27/40 | 40/40 |
| mHS_LF_PR_4000 | 29/40 | 32/40 | 40/40 | 40/40 | 29/40 | 40/40 |
| mHS_NS_FU_4000 | 29/40 | 37/40 | 40/40 | 40/40 | 30/40 | 40/40 |
| mHS_NS_PA_4000 | 26/40 | 35/40 | 40/40 | 40/40 | 29/40 | 40/40 |
| mHS_NS_PR_4000 | 30/40 | 34/40 | 40/40 | 40/40 | 29/40 | 40/40 |

## Paired comparisons

Each pair uses the same 540 sample UIDs. Correct means agreement with the source
label under v3. These counts describe this selection; they are not significance tests.

| Developer | Both agree | Only earlier agrees | Only later agrees | Neither agrees |
| --- | ---: | ---: | ---: | ---: |
| OpenAI | 325 | 87 | 125 | 3 |
| Anthropic | 540 | 0 | 0 | 0 |
| Google | 417 | 0 | 123 | 0 |

## Original disagreement examples

The following questions and outputs are copied without changes. IDs and native
log links permit review of each example. All 3,240 raw outputs and before/after
scores remain in the [sample analysis](../results/analyses/pilot-2026-11-05-scoring-v3-verified/samples.jsonl).

### GPT-4o mini

Sample `HS_HF_PR_2000:1320:9b68f9ee1aa18754`. Source target: `yes`. Model answer: `no`.

> If the woman pays the building, then the girl buys the food; if the kid sees the car, then the woman pays the building; therefore if the kid sees the car, then the girl buys the food?

[Native log](../results/pilot/2026-11-05_20-46-51-b3f8bb12/inspect/2026-11-05T23-47-05-00-00_zeroShot-HS-HF-PR-20_U6RdNaEJiaj6iVo9NmWhRC.eval).

### Gemini 2.5 Flash-Lite

Sample `HS_HF_FU_2000:1730:1032ebb4e14a1bba`. Source target: `no`. Model answer: `yes`.

> If the man will see the paper, then the manager will hate the school; if the teacher will love the book, then the man will see the paper; therefore if the manager will hate the school, then the teacher will love the book?

[Native log](../results/pilot/2026-11-05_20-46-51-b3f8bb12/inspect/2026-11-06T00-04-55-00-00_zeroShot-HS-HF-FU-20_NhwP5HQwzgAWnPnJRKMVg8.eval).

### GPT-6 Luna

Sample `HS_LF_FU_2000:529:874b11709af6e376`. Source target: `no`. Model answer: `yes`.

> If the audiophile will federalize the rocketry, then the herpetologist will sass the metalurgist; if the herpetologist will sass the metalurgist, then the bibliophile will prepay the coronograph; therefore if the bibliophile will prepay the coronograph, then the audiophile will federalize the rocketry?

[Native log](../results/pilot/2026-11-05_20-46-51-b3f8bb12/inspect/2026-11-05T23-47-06-00-00_zeroShot-HS-LF-FU-20_PGMsAj8bs3bDrHc2hKzHtx.eval).

## Extraction correction example

Sonnet 4.5 sample `HS_HF_PA_2000:325:46dc38758878e5e2` ends with:

> **yes**

Historical extraction: `invalid_format`, score `N`. Derived extraction:
`answered`, score `C`. Strict format remains false. The full explanation and
the unchanged source response remain in the sample analysis.

[Native log](../results/pilot/2026-11-05_20-46-51-b3f8bb12/inspect/2026-11-06T00-04-53-00-00_zeroShot-HS-HF-PA-20_ekP96Brv9qL6mKMiPJaZuz.eval).
