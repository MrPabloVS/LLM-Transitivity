# Dataset catalog

The working collection has 18 datasets and 54,000 cases. The coverage pilot
has 540 cases: five from each of the 108 observed strata.

## Filename labels

Working and pilot files use the same naming scheme:

```text
<family>_<lexical-condition>_<tense>_<case-count>.json
```

The codes are defined in the [project glossary](../GLOSSARY.md):

- Family: `HS` or `mHS`.
- Lexical condition: `HF`, `LF`, or `NS`.
- Verbal time: `PR`, `PA`, or `FU`.
- The final number is the actual number of cases in that file.

For example, `mHS_HF_FU_40.json` contains 40 metainferential instances of
hypothetical syllogism with high-frequency words in the future-tense condition.

## Active files

| Family | Lexical condition | Time | Working dataset | Cases | Pilot sample | Cases |
| --- | --- | --- | --- | ---: | --- | ---: |
| `HS` | `HF` | `FU` | [HS_HF_FU_2000.json](../datasets/HS_HF_FU_2000.json) | 2000 | [HS_HF_FU_20.json](../datasets/pilot/HS_HF_FU_20.json) | 20 |
| `HS` | `HF` | `PA` | [HS_HF_PA_2000.json](../datasets/HS_HF_PA_2000.json) | 2000 | [HS_HF_PA_20.json](../datasets/pilot/HS_HF_PA_20.json) | 20 |
| `HS` | `HF` | `PR` | [HS_HF_PR_2000.json](../datasets/HS_HF_PR_2000.json) | 2000 | [HS_HF_PR_20.json](../datasets/pilot/HS_HF_PR_20.json) | 20 |
| `HS` | `LF` | `FU` | [HS_LF_FU_2000.json](../datasets/HS_LF_FU_2000.json) | 2000 | [HS_LF_FU_20.json](../datasets/pilot/HS_LF_FU_20.json) | 20 |
| `HS` | `LF` | `PA` | [HS_LF_PA_2000.json](../datasets/HS_LF_PA_2000.json) | 2000 | [HS_LF_PA_20.json](../datasets/pilot/HS_LF_PA_20.json) | 20 |
| `HS` | `LF` | `PR` | [HS_LF_PR_2000.json](../datasets/HS_LF_PR_2000.json) | 2000 | [HS_LF_PR_20.json](../datasets/pilot/HS_LF_PR_20.json) | 20 |
| `HS` | `NS` | `FU` | [HS_NS_FU_2000.json](../datasets/HS_NS_FU_2000.json) | 2000 | [HS_NS_FU_20.json](../datasets/pilot/HS_NS_FU_20.json) | 20 |
| `HS` | `NS` | `PA` | [HS_NS_PA_2000.json](../datasets/HS_NS_PA_2000.json) | 2000 | [HS_NS_PA_20.json](../datasets/pilot/HS_NS_PA_20.json) | 20 |
| `HS` | `NS` | `PR` | [HS_NS_PR_2000.json](../datasets/HS_NS_PR_2000.json) | 2000 | [HS_NS_PR_20.json](../datasets/pilot/HS_NS_PR_20.json) | 20 |
| `mHS` | `HF` | `FU` | [mHS_HF_FU_4000.json](../datasets/mHS_HF_FU_4000.json) | 4000 | [mHS_HF_FU_40.json](../datasets/pilot/mHS_HF_FU_40.json) | 40 |
| `mHS` | `HF` | `PA` | [mHS_HF_PA_4000.json](../datasets/mHS_HF_PA_4000.json) | 4000 | [mHS_HF_PA_40.json](../datasets/pilot/mHS_HF_PA_40.json) | 40 |
| `mHS` | `HF` | `PR` | [mHS_HF_PR_4000.json](../datasets/mHS_HF_PR_4000.json) | 4000 | [mHS_HF_PR_40.json](../datasets/pilot/mHS_HF_PR_40.json) | 40 |
| `mHS` | `LF` | `FU` | [mHS_LF_FU_4000.json](../datasets/mHS_LF_FU_4000.json) | 4000 | [mHS_LF_FU_40.json](../datasets/pilot/mHS_LF_FU_40.json) | 40 |
| `mHS` | `LF` | `PA` | [mHS_LF_PA_4000.json](../datasets/mHS_LF_PA_4000.json) | 4000 | [mHS_LF_PA_40.json](../datasets/pilot/mHS_LF_PA_40.json) | 40 |
| `mHS` | `LF` | `PR` | [mHS_LF_PR_4000.json](../datasets/mHS_LF_PR_4000.json) | 4000 | [mHS_LF_PR_40.json](../datasets/pilot/mHS_LF_PR_40.json) | 40 |
| `mHS` | `NS` | `FU` | [mHS_NS_FU_4000.json](../datasets/mHS_NS_FU_4000.json) | 4000 | [mHS_NS_FU_40.json](../datasets/pilot/mHS_NS_FU_40.json) | 40 |
| `mHS` | `NS` | `PA` | [mHS_NS_PA_4000.json](../datasets/mHS_NS_PA_4000.json) | 4000 | [mHS_NS_PA_40.json](../datasets/pilot/mHS_NS_PA_40.json) | 40 |
| `mHS` | `NS` | `PR` | [mHS_NS_PR_4000.json](../datasets/mHS_NS_PR_4000.json) | 4000 | [mHS_NS_PR_40.json](../datasets/pilot/mHS_NS_PR_40.json) | 40 |

## Variants within each file

- Each HS dataset uses `if then / therefore` and has four strata: the two
  source validity labels crossed with the two canonical-form labels.
- Each mHS dataset has eight strata. It crosses those four combinations with
  two formulations: `assuming that we can infer / thus` and
  `from the inference (therefore) / does the inference follow`.
- Every full stratum has 500 cases. Each pilot stratum has five cases.

Validity labels are `valid` and `invalid`. Canonical-form labels are `canonic`
and `non-canonic`. These are source classifications, not audited logical truth.

The filename prefix distinguishes HS from mHS. The original case-type field
inside both families is `HS`; it remains unchanged. Inspect records the filename
family separately as `dataset_family`.

## Format and provenance

Each case has eight fields in this order:

```text
[case_type, source_id, prompt, frequency, verbal_time, connectors, validity, canonical_form]
```

The legacy `frequency` field carries the lexical-condition code, including `NS`.
Source identifiers can be structured JSON values. They are preserved as such.

Original files remain in `prompts/userPrompts/`. Working filenames use actual
counts instead of the historical `_500_complete` suffix. Only the approved
translations `valido` to `valid` and `canonico` to `canonic` were applied in
the HS/LF/PR and mHS/LF/PR working copies. Sentences are unchanged.

The [pilot manifest](../datasets/pilot/manifest.json) records the original file,
fixed Git revision, hashes, and selected source rows. The
[generated inventory](dataset_inventory.md) describes deterministic selection
and its coverage limits. Verify the complete source chain with:

```sh
uv run --locked transitivity datasets verify
```

The separate [10-case smoke dataset](../datasets/HS.json) is retained for quick
checks. It is not included in the 18-dataset coverage pilot. Historical `Csf`,
`Csf2`, and `HS_test` files are outside this active catalog.

## Case adaptation

The package domain case adapter gives validated records named fields for Inspect.
The case type lives in `llm_transitivity.domain.cases`.
The adapter preserves field values, source identifiers, and original labels.
The original
records remain the input to selection and hashing. `case_type` is the source
label; the dataset name supplies `dataset_family`. New run archives include the
case adapter source and its hash.
