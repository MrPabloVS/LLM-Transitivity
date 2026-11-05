# LLM Transitivity

## Case families

**Benchmark case**: A reasoning question with its experimental conditions and
source labels. A source label does not establish audited logical validity.

**Case family**: The distinction between hypothetical syllogism cases (HS) and
metainferential hypothetical syllogism cases (mHS).

**Source case type**: The case-type label stored in an original record. It can
be `HS` in both case families and does not by itself identify the family.

**HS**: Instances of hypothetical syllogism, expressed with conditionals.

**mHS**: Metainferential instances of hypothetical syllogism. These cases express
relationships between inferences. The dataset includes formulations in terms of
assumptions and inference, and formulations that explicitly mention inferences.

## Dataset and pilot

**HF (high frequency)**: The lexical condition that uses high-frequency words.

**LF (low frequency)**: The lexical condition that uses low-frequency words.

**NS (nonsense)**: The lexical condition that uses pseudowords. It is a separate
condition, not a lower frequency category.

**PR (present)**: The present-tense condition.

**PA (past)**: The past-tense condition.

**FU (future)**: The future-tense condition.

**Canonical form**: The source distinction between the standard premise order
(`canonic`) and the reversed premise order (`non-canonic`).

**Original dataset**: A versioned input file preserved as research evidence.

**Working dataset**: A copy used for execution. Its sentences and records match
the original except for the explicitly approved label translations.

**Stratum**: A group within one dataset with the same case type, frequency,
verbal time, connectors, source validity label, and canonical form label.

**Coverage pilot**: A small selection with cases from every observed stratum in
the working datasets. It checks the experiment workflow across these conditions;
it does not establish statistical accuracy or cover every distinct sentence.

**Source-label agreement**: Agreement between a model answer and the label stored
in the original dataset. This does not establish the logical validity of the case.

**Preflight**: A check that uses the same single source case across all selected
models before the coverage pilot. It checks access and response evidence, not
coverage across strata or statistical accuracy.

**Model generation group**: A set of models from the same relative generation
in this comparison. Each earlier or later group contains one model from each
of OpenAI, Anthropic, and Google.
_Avoid_: Model family when referring to an earlier or later group.
