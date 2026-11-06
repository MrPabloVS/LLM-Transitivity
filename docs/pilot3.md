# Pilot 3

Pilot 3 replaces Sonnet 4.6 with Haiku 5.5 in the Pilot 2.0 model selection.
The other five models and their request controls remain unchanged.

Models: GPT-4o mini, GPT-6 Luna Flex, Haiku 5.5, Sonnet 5.5,
Gemini 3.1 Flash-Lite Flex, and Gemini 3.5 Flash-Lite Flex.

Use the same 540 cases per model, with unchanged source texts, labels, UIDs,
and deterministic scoring. Coverage has 108 active tasks, 64 samples per task,
and 3,240 planned responses. Dataset sizes limit the effective sample ceiling
to 3,240; the configured ceiling is 6,912. Each shared model pool allows 1,152
connections. These are configured limits, not measured achieved capacity.

Haiku 5.5 requests reasoning disabled and medium effort, as in the completed
Haiku follow-up. Sonnet 5.5 retains enabled reasoning at low effort. Gemini 3.5
Flash-Lite retains enabled reasoning at minimal effort. Other controls retain
their previous values. Providers stay fixed, with no fallback. The output cap
remains 1,024 tokens, including reasoning and final text where applicable.

A six-call preflight must pass before coverage. Filters remain recorded outcomes
in Inspect and do not trigger replacement generations. Retries keep the same
model, provider, and tier. Unknown costs remain unknown.

This changes both a model and task concurrency relative to Pilot 2.0; differences
do not isolate either change. Haiku and Sonnet are different model families.
The earlier/later group labels describe comparison slots, not Haiku generations.

The [card manifest](model_cards/pilot-3-manifest.json) references the shared
cards without per-pilot copies. Preparation saves fresh endpoint quotes and
freezes source code before paid calls.

```sh
uv run --locked transitivity followup --profile pilot3 --dry-run
uv run --locked transitivity followup --profile pilot3 --prepare-only
```

The full corpus is not part of this run.
