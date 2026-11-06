# Pilot scope and decision report

Status: the scope is verified and pilot execution is complete. All 108 final
tasks succeeded, with 3,240 saved responses and no final sample errors.
Analysis of the answers and the decision to run the full experiment are pending.
Scope tables below describe the planned experiment.

## What we test

We ask six language models to answer reasoning questions with `yes` or `no`.
Every model receives the same 540 questions. We compare their answers with the
source labels and check whether they follow the requested response format.

The pilot covers every observed combination of experimental conditions in the
corpus. It lets us review model behavior, input coverage, failures, and cost
before we decide whether to run all 54,000 questions. It does not establish
statistical accuracy or independently audit the source labels.

## Which models we compare

We use two model versions from each of OpenAI, Anthropic, and Google.
Each comparison group contains one model from each developer.

| Group | Developer | Exact model ID | Pilot questions | Requested provider | Tier |
| --- | --- | --- | ---: | --- | --- |
| `earlier` | OpenAI | [openai/gpt-4o-mini](model_cards/openai--gpt-4o-mini/card.md) | 540 | `openai` | default |
| `earlier` | Anthropic | [anthropic/claude-sonnet-4.5](model_cards/anthropic--claude-sonnet-4.5/card.md) | 540 | `anthropic` | default |
| `earlier` | Google | [google/gemini-2.5-flash-lite](model_cards/google--gemini-2.5-flash-lite/card.md) | 540 | `google-ai-studio/flex` | flex |
| `later` | OpenAI | [openai/gpt-6-luna](model_cards/openai--gpt-6-luna/card.md) | 540 | `openai/flex` | flex |
| `later` | Anthropic | [anthropic/claude-sonnet-5](model_cards/anthropic--claude-sonnet-5/card.md) | 540 | `anthropic` | default |
| `later` | Google | [google/gemini-3.1-flash-lite](model_cards/google--gemini-3.1-flash-lite/card.md) | 540 | `google-ai-studio/flex` | flex |
| **Total** | **3 developers** | **6 models** | **3,240 responses** | | |

`earlier` and `later` name the two groups in this comparison. They do not imply
synchronized release dates or isolate the effect of a generation change.
Models can also differ in training, size, and tokenization.
Providers are fixed; fallback is disabled. The
[saved model cards](model_cards/README.md) retain dated catalog evidence.

## Which questions we use

The original corpus contains 18 datasets and 54,000 distinct question texts.
Each question is one complete reasoning case. A case can contain several clauses
or sentences; the counts refer to complete cases, not individual clauses.

There are two case families:

| Family | Meaning | Full datasets | Full cases | Pilot cases per model |
| --- | --- | ---: | ---: | ---: |
| HS | Hypothetical syllogisms, expressed with conditionals | 9 | 18,000 | 180 |
| mHS | Metainferential instances of hypothetical syllogism, expressed as relationships between inferences | 9 | 36,000 | 360 |
| **Total** | | **18** | **54,000** | **540** |

Both families vary word choice and verbal time:

| Code | Condition | Pilot cases per model |
| --- | --- | ---: |
| HF | High-frequency words | 180 |
| LF | Low-frequency words | 180 |
| NS | Pseudowords | 180 |
| PR | Present tense | 180 |
| PA | Past tense | 180 |
| FU | Future tense | 180 |

Frequency and verbal time are separate dimensions. Their counts describe the
same 540 questions and must not be added together. NS is a separate lexical
condition, not a lower frequency category.

The following table shows all nine lexical and tense combinations. Every row
includes one HS dataset and one mHS dataset, for 18 datasets in total.

| Word condition | Tense | HS pilot cases | mHS pilot cases | Total per model |
| --- | --- | ---: | ---: | ---: |
| HF | PR | 20 | 40 | 60 |
| HF | PA | 20 | 40 | 60 |
| HF | FU | 20 | 40 | 60 |
| LF | PR | 20 | 40 | 60 |
| LF | PA | 20 | 40 | 60 |
| LF | FU | 20 | 40 | 60 |
| NS | PR | 20 | 40 | 60 |
| NS | PA | 20 | 40 | 60 |
| NS | FU | 20 | 40 | 60 |
| **Total** | | **180** | **360** | **540** |

Within these datasets, the pilot also includes:

- 270 cases labeled `valid` and 270 labeled `invalid` by the source.
- 270 cases labeled `canonic` and 270 labeled `non-canonic`. These labels
  distinguish standard premise order from reversed premise order.
- One connector formulation for HS: `if then / therefore`.
- Two connector formulations for mHS: 180 cases use
  `assuming that we can infer / thus`; 180 use
  `from the inference (therefore) / does the inference follow`.

These are source conditions. Source validity labels have not been independently
verified as logical truth. The [glossary](../GLOSSARY.md) defines the terms.

### Examples from the selected questions

The following texts are exact copies from the pilot files. They illustrate the
question types; no wording was corrected for this report.

HS, high-frequency words, present tense, source label `valid`, canonical order,
from [HS_HF_PR_20.json](../datasets/pilot/HS_HF_PR_20.json):

> If the kid finds the sugar, then the manager pays the table; if the manager pays the table, then the woman hates the program; therefore if the kid finds the sugar, then the woman hates the program?

mHS, high-frequency words, present tense, source label `valid`, canonical order,
from [mHS_HF_PR_40.json](../datasets/pilot/mHS_HF_PR_40.json):

> Assuming that the woman eats the food, we can infer that the family pays the car. Assuming that the family pays the car, we can infer that the girl reads the paper. Thus, assuming that the woman eats the food, can we infer that the girl reads the paper?

The [dataset inventory](dataset_inventory.md) lists all 18 selected files.
The [selection manifest](../datasets/pilot/manifest.json) identifies every
selected original row and its hashes.

## How we select the 540 questions

We select five cases from each of 108 observed strata. A stratum is a group
within a dataset with the same case type, word condition, verbal time,
connectors, source validity label, and canonical form label.

Each HS dataset has four strata: two validity labels times two premise orders.
Each mHS dataset has eight: those four combinations times two connector
formulations. Thus, nine HS datasets contribute 36 strata and nine mHS datasets
contribute 72. Each stratum contains 500 original cases.

Selection uses a fixed SHA-256 ranking, with source row number as the tie
breaker, then restores source order. Five of 500 cases per stratum gives a
1% selection: 540 distinct questions from 54,000. All six models receive that
same selection, which permits comparisons on the same cases.

Verification compares all 54,000 working records with the fixed original Git
revision. It preserves question text, including spaces, case, punctuation,
and Unicode. Only the approved `valido` to `valid` and `canonico` to `canonic`
label translations are allowed in the two LF/PR working copies. The pilot does
not rewrite the original questions. The separate 10-case smoke file is excluded.

## What each model receives

Each question starts an independent conversation. The system message is:

> Answer only with 'yes' or 'no' and nothing else.

The user message contains the original question. There are no worked examples
or previous answers in the conversation: this is a zero-shot condition.
Source labels and identifiers are retained for analysis, not sent as answers
in the prompt.

Optional reasoning is disabled. Each response has a cap of 1,024 output tokens.
Temperature, top-p, and seed are omitted; provider defaults apply. The answers
are not deterministic. The deterministic guarantee concerns input preservation
and selection. The run permits 16 concurrent samples within one active task.

## What the pilot must tell us before expansion

Results will be reviewed together after execution. They must show:

| Decision question | Evidence to review |
| --- | --- |
| Did every condition run? | Completed and missing cases by model and all 18 datasets; execution errors and retries |
| Do answers agree with the source labels? | Agreement by model, HS/mHS, lexical condition, tense, premise order, and connector formulation |
| Do models follow the requested format? | Exact yes/no compliance, separate from agreement; ambiguous, empty, filtered, and unrecognized outputs |
| Did the requested model conditions hold? | Observed provider, tier, and reasoning usage; fields that remain unverified |
| What would expansion cost and take? | Reported per-model cost, token usage, retry counts, and observed throughput |

Agreement uses interpreted answers as its denominator. Format and response
category rates use all scored samples. Execution errors remain separate.
Missing or filtered answers are not treated as `no`. Agreement with source
labels must not be presented as independently audited logical correctness.

No acceptance threshold or decision to expand is recorded yet. The pilot
covers all observed condition combinations but uses only five cases per stratum.
A small difference between models does not by itself establish a reliable
ranking. Findings must support an explicit decision about the scope below.

## What running the full corpus would mean

| Scope | Models | Distinct questions | Responses per model | Total planned responses |
| --- | ---: | ---: | ---: | ---: |
| Pilot, both groups | 6 | 540 | 540 | 3,240 |
| Full corpus, `earlier` only | 3 | 54,000 | 54,000 | 162,000 |
| Full corpus, `later` only | 3 | 54,000 | 54,000 | 162,000 |
| Full corpus, both groups | 6 | 54,000 | 54,000 | 324,000 |

The full corpus contains 18,000 HS and 36,000 mHS questions. Both groups reuse
the same 54,000 questions; adding models increases responses, not distinct
questions. These totals describe a full pass and do not subtract pilot cases.
Retries can increase HTTP request counts.

Cost and duration projections are pending. Calculate them separately for each
model, then sum the selected group. A simple cost projection scales pilot
usage by 100 because each stratum grows from five to 500 cases. State that
assumption and account for observed retries. Do not assume the two groups cost
the same. Duration must account for concurrency, task size, lookup time,
provider queues, and interruptions.

After review, the options are to run both groups, run one group, or resolve
identified problems before expansion. This report does not authorize a new run.

## Evidence and execution notes

The pilot archive is
[`2026-11-05_20-46-51-b3f8bb12`](../results/pilot/2026-11-05_20-46-51-b3f8bb12/provenance/run.json).
It records 108 model/dataset tasks and 3,240 planned responses. The separate
six-call preflight checked access and telemetry; it is not part of those totals.

The original process stopped before finalization for an unknown reason.
Recovery uses the frozen configuration and existing logs. Final analysis must
avoid counting reused responses twice and report the interruption separately
from active execution time. The [pilot guide](pilot.md) retains operational
settings and the recovery checkpoint link. Results remain pending here.
