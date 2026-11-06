# Pilot scope and decision report

Status: the scope is verified and pilot execution is complete. All 108 final
tasks succeeded, with 3,240 saved responses and no final sample errors.
Results below use a derived reevaluation. The decision to run the full experiment
remains with the researcher.
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

## Pilot results

All 108 final tasks succeeded: 540 responses per model, 3,240 in total, and
no final execution errors. All six models received the same case IDs, texts,
labels, and condition combinations. Recovery did not add new cases.

The following table uses the corrected extraction rule
`initial_or_final_line_v2`, scoring version `source-label-deterministic-v3`.
Agreement is correct interpreted answers divided by interpreted answers.
Strict format is compliant responses divided by all 540 scored samples.
All 540 responses per model are interpretable under the corrected rule.

| Model | Agree / interpreted | Agreement | Disagree | Strict yes/no | Strict format |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPT-4o mini | 412/540 | 76.3% | 128 | 513/540 | 95.0% |
| GPT-6 Luna | 450/540 | 83.3% | 90 | 540/540 | 100.0% |
| Sonnet 4.5 | 540/540 | 100.0% | 0 | 73/540 | 13.5% |
| Sonnet 5 | 540/540 | 100.0% | 0 | 540/540 | 100.0% |
| Gemini 2.5 Flash-Lite | 417/540 | 77.2% | 123 | 540/540 | 100.0% |
| Gemini 3.1 Flash-Lite | 540/540 | 100.0% | 0 | 539/540 | 99.8% |

Sonnet 4.5, Sonnet 5, and Gemini 3.1 Flash-Lite agree with every selected source
label after correction. This is a descriptive result on 540 selected cases,
not proof of perfect reasoning on the complete corpus. GPT-6 Luna has more
agreements than GPT-4o mini on this selection. See the
[condition tables and paired comparisons](pilot_results_details.md) for where
differences occur. Source labels have not been independently audited.

### Evaluator correction and response formats

The historical rule rejected 48 Sonnet 4.5 responses whose final answer was
explicit: 47 ended in `**yes**` or `**Yes**`; one ended in `Therefore, yes.`.
The new rule accepts balanced bold yes/no at the beginning or on the final
line, and a final complete line `Therefore, yes/no`, with optional final
punctuation. Case handling, ambiguity checks, and strict formatting are unchanged.
This is a post-run scoring correction, applied to all six models.

| Outcome | Historical scoring | Derived scoring |
| --- | ---: | ---: |
| Interpretable responses, all models | 3,192 | 3,240 |
| Sonnet 4.5 agreement count / denominator | 492/492 | 540/540 |
| Sonnet 4.5 responses rejected by extraction | 48 | 0 |
| Strict-format responses, all models | 2,745 | 2,745 |
| Ambiguous, empty, filtered, or output-error responses | 0 | 0 |

No other sample changes classification, extracted answer, or strict compliance.
There are 495 strict-format violations:

| Form | Responses | Historical interpretation |
| --- | ---: | --- |
| Explanation with an initial or final plain answer | 418 | Accepted |
| Short answer with a period, such as `Yes.` | 29 | Accepted |
| Final answer in bold | 47 | Rejected |
| Final `Therefore, yes.` | 1 | Rejected |

Of these violations, 467 are from Sonnet 4.5, 27 from GPT-4o mini, and one
from Gemini 3.1 Flash-Lite. The other three models always meet strict formatting.
Sonnet 4.5's explanations remain ordinary output tokens, even though optional
reasoning is disabled. Disabling reasoning does not force a short answer.

### Routing, retries, and unresolved evidence

All 3,240 final response payloads report the requested model ID and tier,
the expected provider name, routing metadata, and zero reasoning tokens.
All prompts retain the fixed provider request. Provider names and tiers do not
independently prove the identity of an endpoint UUID or the model internals.

There are 3,254 distinct captured generation IDs: 3,240 final responses and
14 additional GPT-6 Luna attempts. The latter returned HTTP 200 but contained
an internal 502 error: Flex processing was temporarily unavailable. These are
provider errors, not successful answers. Retries eventually produced all final
responses. Duplicate observations in original, recovered, and retry logs are
counted once by generation ID.

All final responses have captured usage and cost. Immediate generation lookups
were usually unavailable. A later read-only lookup for each of the 14 failed
attempts also remained unavailable. Their charge is unknown, not assumed zero.
The [saved lookup responses](../results/analyses/pilot-generation-lookups-2026-11-05.json)
retain that limitation. No new model generations were requested for this report.
Some available lookup records report `streamed: true`, while the captured client
requests omit the stream field and capture complete JSON responses. We do not
use that field to certify upstream streaming behavior or infer a billing change.

## Reported pilot cost and full-corpus cost scenarios

The known reported cost of the 3,240 final responses is **USD 1.60749575**.
This excludes unknown charges for the 14 failed Flex attempts. It is returned
usage evidence, not an independent check of the account invoice.
Captured response cost takes precedence over a lookup quote for the same ID;
no conflicting quotes were found. Both observations remain in the cost ledger.

| Model | Known pilot USD | Output tokens | Full-pass central USD | Three-attempt sensitivity USD |
| --- | ---: | ---: | ---: | ---: |
| GPT-4o mini | 0.00803910 | 567 | 0.8039 | 2.4117 |
| GPT-6 Luna | 0.00321580 | 2,706 | 0.3216 | 0.9647 |
| Sonnet 4.5 | 1.43093100 | 84,797 | 143.0931 | 429.2793 |
| Sonnet 5 | 0.15674400 | 1,890 | 15.6744 | 47.0232 |
| Gemini 2.5 Flash-Lite | 0.00240860 | 540 | 0.2409 | 0.7226 |
| Gemini 3.1 Flash-Lite | 0.00615725 | 541 | 0.6157 | 1.8472 |

Each full stratum contains 500 cases; the pilot contains five. We multiply the
observed mean final-response cost within each stratum by its full population,
then sum strata and models. Here this equals 100 times the pilot final-response
cost because every stratum has the same expansion factor. It assumes comparable
input and output usage and unchanged endpoint prices. Verbosity and request
failure rates can differ in the complete corpus.

The three-attempt sensitivity assumes three attempts per case, each with the
same average charge as a final response. It is a stress scenario, not an
expected bill, confidence bound, enforced budget, or guaranteed maximum.
Unknown failed-attempt charges remain outside the central projection.

| Full-corpus scope | Models | Distinct questions | Planned responses | Central USD | Three-attempt USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| earlier | 3 | 54,000 | 162,000 | 144.14 | 432.41 |
| later | 3 | 54,000 | 162,000 | 16.61 | 49.84 |
| all | 6 | 54,000 | 324,000 | 160.75 | 482.25 |

These are new full passes; they do not subtract the completed pilot. Running
both groups reuses the same 54,000 questions, not 108,000 different questions.
Sonnet 4.5 contributes about 89% of the six-model central cost, mainly because
it produced 84,797 output tokens in the pilot. The `earlier` group is much more
expensive than `later`; halving the six-model estimate would be misleading.

## Observed time and full-corpus time scenarios

From the first saved sample start to the last sample completion, elapsed time
was **33.54 minutes**. The union of all sample execution intervals was
**22.02 minutes**. The remaining **11.52 minutes** had no active saved sample;
it includes the interruption, restart preparation, and gaps between tasks.
It is not an exact measurement of downtime caused only by the interruption.
Initial preparation before the first sample and final export after the last
sample are outside this time window.

The projections below keep 16 concurrent samples, 16 connections, and one active
task. For each full dataset, a fixed-capacity queue schedules cases in source
order. The central scenario uses the mean observed end-to-end sample time in
each stratum. The slow scenario uses its interpolated 90th percentile. These
times include retries and generation-metadata collection inside each sample.
Five observations per stratum do not establish a reliable tail distribution.

Add the model's median nonnegative task overhead once per dataset. Overhead is
task wall time minus a queue simulation of its observed sample durations.
Use 107 tasks whose samples belong to their execution window; exclude the
recovered Luna task. Task timestamps have whole-second precision, so overhead
below about one second cannot be measured precisely. Do not charge the restart
gap once per projected case or scale the interrupted wall clock by 100.

| Model | Observed active minutes | Full central hours | Full slow-scenario hours |
| --- | ---: | ---: | ---: |
| GPT-4o mini | 2.57 | 3.17 | 3.40 |
| GPT-6 Luna | 6.24 | 4.66 | 6.91 |
| Sonnet 4.5 | 4.91 | 5.91 | 6.60 |
| Sonnet 5 | 3.14 | 3.89 | 4.10 |
| Gemini 2.5 Flash-Lite | 2.56 | 3.18 | 3.47 |
| Gemini 3.1 Flash-Lite | 2.60 | 3.25 | 3.48 |

| Full-corpus scope | Central hours | Slow-scenario hours |
| --- | ---: | ---: |
| earlier | 12.26 | 13.47 |
| later | 11.81 | 14.49 |
| all | 24.07 | 27.96 |

These are scenarios, not delivery guarantees. They assume similar provider
load, sample durations, and fixed concurrency. Flex queues, failed attempts,
rate limits, local interruptions, and different lookup availability can change
completion time. The slow scenario does not add a second retry multiplier:
observed sample times already include their retry behavior.

## Recommendation and next steps

**Keep all six models for the full comparison, after the following checks.**
The pilot covers all intended conditions and shows useful differences in
source-label agreement, format adherence, and output cost. Removing a version
would remove its paired earlier/later comparison. No new generation run is
started or authorized by this report.

1. Review the derived scoring correction and its 48 changed cases. Use the new
   version consistently for future runs. Keep the historical scores visible.
2. Review the disagreement examples and a small set of source labels manually,
   including non-canonical and mHS cases. Three models matched every pilot label;
   check the interpretation of that result before claiming reasoning accuracy.
3. Plan for approximately **USD 161 of final-response charges and 24–28 hours**
   for all six models under the stated scenarios. Resolve or explicitly accept
   the unknown charges for failed attempts and select an operational reserve.
   The existing runner does not enforce a spending limit.
4. Use a durable launch and verified recovery procedure. Review completed
   dataset blocks, provider errors, and costs as the full run progresses. Point
   Inspect only at its native log directory so exported JSON does not block it.
5. Keep models, prompts, providers, and output limits unchanged for this
   comparison. A shorter Sonnet prompt or a different endpoint would be a new
   experimental condition and would require a separate pilot.

If execution must be staged, the `later` group is the lower-cost first stage
(about USD 16.61), followed by `earlier` (about USD 144.14), preserving the plan
to compare both. Running only `earlier` would retain most of the expense while
removing half the responses and all cross-version comparisons.

## Candidate Haiku follow-up

The proposed Anthropic alternatives have saved cards:
[Haiku 4.5](model_cards/anthropic--claude-haiku-4.5/card.md) for `earlier` and
[Haiku 5.5](model_cards/anthropic--claude-haiku-5.5/card.md) for `later`.
Each capture includes the complete catalog record, endpoint response, and
manufacturer system-card PDF. These are candidates, not models evaluated in
the results above. The executable catalog remains unchanged.

## Evidence and reproduction

The source run is
[`2026-11-05_20-46-51-b3f8bb12`](../results/pilot/2026-11-05_20-46-51-b3f8bb12/provenance/run.json).
The separate six-call preflight is excluded. Original logs and historical
scores remain unchanged. New analysis uses working-tree code; its source
hashes, base revision, and dirty-state flag are recorded explicitly.

- [Verification results and protected-file hashes](../results/analyses/pilot-2026-11-05-scoring-v3-verified/verification.json).
- [Analysis summary, source hashes, condition measures, and projections](../results/analyses/pilot-2026-11-05-scoring-v3-verified/summary.json).
- [All 3,240 samples with raw output, before/after scores, IDs, and log hashes](../results/analyses/pilot-2026-11-05-scoring-v3-verified/samples.jsonl).
- [Generation cost ledger, including unknown charges and repeated observations](../results/analyses/pilot-2026-11-05-scoring-v3-verified/generations.json).
- [Detailed condition tables, paired comparisons, and original examples](pilot_results_details.md).

Reproduce into a **new** output directory. The command verifies the corpus,
reads saved evidence, and makes no API requests:

```sh
uv run --locked python -m llm_transitivity.analysis.pilot --root "$PWD" \
  --run results/pilot/2026-11-05_20-46-51-b3f8bb12 \
  --lookup-evidence results/analyses/pilot-generation-lookups-2026-11-05.json \
  --output results/analyses/pilot-scoring-v3-reproduction
```

The analyzer refuses an existing output directory. The
[pilot guide](pilot.md) retains the execution and recovery procedure.
