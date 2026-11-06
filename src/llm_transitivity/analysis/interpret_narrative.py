"""Reviewed editorial reading of one fixed full-corpus experiment."""

from llm_transitivity.analysis.interpret_figures import LABELS


def fraction(n, d):
    return f"{n:,}/{d:,} ({100 * n / d:.2f}%)" if d else f"{n:,}/{d:,} (undefined)"


def narrative(data):
    blocks = []

    def heading(text, level=2):
        blocks.append({"kind": "heading", "level": level, "text": text})

    def text(value):
        blocks.append({"kind": "text", "text": value})

    def literal(value):
        blocks.append({"kind": "literal", "text": value})

    def table(headers, rr):
        blocks.append({"kind": "table", "headers": headers, "rows": rr})

    def figure(name, title, reading, pattern, limit):
        blocks.append({"kind": "figure", "name": name, "alt": title})
        text("What it shows. " + title + " How to read it. " + reading)
        text("What we find. " + pattern + " What it cannot show. " + limit)

    source = data["source"]
    t = data["tables"]
    models = source["models"]
    totals = {r["model"]: r for r in t["totals"]}
    fam = {(r["model"], r["family"]): r for r in t["family"]}
    heading("Full-corpus results: analysis and interpretation", 1)
    text(
        "A static reading for research and communication. Run: "
        + source["run_id"]
        + ". This document uses one closed execution, not a comparison of pilots. It covers 54,000 complete questions, six models, 108 tasks, and 324,000 corpus responses. The preflight has six separate responses. No final execution errors were recorded."
    )
    heading("The main reading")
    text(
        "There is no single result called performance here. Agreement with source labels, usable response coverage, and compliance with the requested answer format are different outcomes. Sonnet 5.5 and Gemini 3.1 Flash-Lite have near-complete source-label agreement. Sonnet often adds text. Gemini 3.5 Flash-Lite matches every HS label but has more disagreements on mHS. The other three models show large differences between conditions that their overall means hide."
    )
    text(
        "The strongest practical conclusion is to inspect conditions before selecting a model. The strongest methodological limit is equally important: the labels are source labels, not an independent logical audit. A model can disagree with a source label for several reasons. These results do not identify which reason applies."
    )
    heading("1. What the experiment asks")
    text(
        "Each case is a complete question and can contain several sentences. HS uses hypothetical syllogisms expressed with conditionals. mHS uses metainferential hypothetical syllogisms: relationships between inferences. Its two formulations use assumptions and inference, or explicitly refer to an inference. Zero-shot means that the request supplies no worked examples."
    )
    text("The exact system prompt is:")
    literal(source["system_prompt"])
    text(
        "HF uses high-frequency words. LF uses low-frequency words. NS uses pseudowords; it is not a lower frequency level. PR means present, PA past, and FU future. Canonical and reversed refer to source premise-order labels. A source valid label sets target yes; invalid sets target no. None of these labels is changed here."
    )
    figure(
        "01_design",
        "The number of distinct cases by family.",
        "Bar length is a case count; each case is submitted to all six models.",
        "mHS contributes 36,000 cases and HS 18,000. Thus mHS has twice the weight in each overall rate.",
        "A larger family does not establish that its questions are harder or more representative of general reasoning.",
    )
    table(
        ["Family", "Datasets", "Strata", "Cases per stratum", "Cases per model"],
        [
            ["HS", 9, 36, 500, "18,000"],
            ["mHS", 9, 72, 500, "36,000"],
            ["Total", 18, 108, 500, "54,000"],
        ],
    )
    text(
        "Each family crosses three lexical conditions and three verbal times. Each HS dataset has four observed order/label strata. Each mHS dataset has eight strata, adding two formulations. The full observed design is in tables/design.csv. Only observed combinations enter the analysis; absent combinations are not zeros."
    )
    heading("2. Which models and conditions were compared")
    config = source["configuration"]
    table(
        ["Exact model identifier", "Provider / tier", "Reasoning policy / effort"],
        [
            [
                m,
                ", ".join(config["requested_routing"][m]["provider_only"])
                + " / "
                + config["requested_routing"][m]["service_tier"],
                config["model_reasoning_policies"][m]["policy"]
                + " / "
                + str(config["model_reasoning_policies"][m]["effort"] or "not set"),
            ]
            for m in models
        ],
    )
    text(
        "All models have a maximum output of 1,024 tokens and no provider fallbacks. Prompt caching is disabled. Temperature and seed were omitted, so repeated outputs are not guaranteed to be identical. Reasoning is enabled for Sonnet 5.5 at low effort and Gemini 3.5 Flash-Lite at minimal effort. Reported reasoning tokens are zero when present; that telemetry does not establish that internal reasoning was absent. Archived cards and the full frozen policy remain in the source report bundle."
    )
    text(
        "Compare individual model/provider/reasoning conditions. The earlier/later metadata does not define equivalent model generations. In particular, Haiku and Sonnet are different families. This is not an isolated test of model size, generation, provider, or reasoning effort."
    )
    heading("3. Four measures, four different questions")
    table(
        ["Measure", "Numerator / denominator", "Question"],
        [
            [
                "Agreement",
                "Matches / interpretable responses",
                "When we can interpret an answer, does it match the label?",
            ],
            [
                "Coverage",
                "Interpretable responses / all planned cases",
                "How often do we obtain a usable yes/no interpretation?",
            ],
            [
                "Strict format",
                "Only yes or no / all planned cases",
                "How often does the model follow the output instruction?",
            ],
            [
                "Matches over total",
                "Matches / all planned cases",
                "How many planned questions produce a matching answer?",
            ],
        ],
    )
    text(
        "Interpretation uses the saved source-label-deterministic-v3 scores and initial_or_final_line_v2 extraction. Strict format allows only yes or no after trimming spaces and ignoring case. Some explanations, punctuation, bold answers, and complete final conclusions can be interpreted but fail strict format. Ambiguous, filtered, empty, invalid-format, and error outcomes are not converted to no. They remain separate categories in every derived table."
    )
    table(
        ["Model", "Matches / total", "Agreement", "Coverage", "Strict format"],
        [
            [
                LABELS[m],
                fraction(totals[m]["matched"], 54000),
                fraction(totals[m]["matched"], totals[m]["answered"]),
                fraction(totals[m]["answered"], 54000),
                fraction(totals[m]["strict"], 54000),
            ]
            for m in models
        ],
    )
    figure(
        "02_overall",
        "Matches, strict format, coverage, and agreement by model.",
        "Three panels use all cases; agreement uses interpretable responses. Each bar gives its numerator, denominator, and percentage.",
        "The model with the most matches need not have the most strict-format responses. Luna follows the format on all 54,000 cases, but its answers do not all match the source labels.",
        "Format compliance is not evidence of logical correctness, and a longer response is not automatically a wrong interpretation.",
    )
    figure(
        "02_ceiling",
        "The high-match models on an enlarged scale.",
        "This axis starts at 97%, not zero. Use the counts to judge the absolute differences.",
        f"Sonnet has {totals['anthropic/claude-sonnet-5.5']['matched']:,} matches; Gemini 3.1 has {totals['google/gemini-3.1-flash-lite']['matched']:,}. Their absolute difference is {abs(totals['anthropic/claude-sonnet-5.5']['matched'] - totals['google/gemini-3.1-flash-lite']['matched']):,} matches over 54,000 cases. Their format behavior differs substantially.",
        "One execution does not establish a stable advantage on repeated requests or other corpora.",
    )
    heading("4. Family changes the reading")
    figure(
        "03_family",
        "HS and mHS matches over all cases for each model.",
        "Circles mark HS; squares mark mHS. The line connects two descriptive rates, not paired variants of the same sentence.",
        "GPT-4o mini and Luna have lower matches on mHS. Haiku has higher matches on mHS than HS. Sonnet and both Gemini models match all HS labels in this run.",
        "Family, formulation, vocabulary, and case composition differ. This plot alone cannot identify a cause.",
    )
    table(
        ["Model", "HS matches", "mHS matches", "mHS minus HS (pp)"],
        [
            [
                LABELS[m],
                fraction(fam[m, "HS"]["matched"], 18000),
                fraction(fam[m, "mHS"]["matched"], 36000),
                f"{100 * (fam[m, 'mHS']['matched_total'] - fam[m, 'HS']['matched_total']):+.2f}",
            ]
            for m in models
        ],
    )
    text(
        "The overall mean is one-third of the HS rate plus two-thirds of the mHS rate when the denominator is all cases. It is not an equal-weight family comparison. Keep the family table beside any overall ranking."
    )
    heading("5. Order and labels expose the largest contrasts")
    figure(
        "04_order_label",
        "Matches within family, premise order, and source label.",
        "Every cell gives matches / planned cases. Color uses a common 0-100% scale.",
        "GPT-4o mini is particularly low on reversed mHS with a valid label. Luna is lowest on reversed mHS with an invalid label. Haiku is lowest on canonical HS with an invalid label. The weak groups are not the same across models.",
        "Order associations do not prove an order effect: this analysis does not establish matched sentence pairs across orders.",
    )
    weakest = []
    for m in models:
        r = min(
            (r for r in t["order_label"] if r["model"] == m),
            key=lambda r: (
                r["matched_total"],
                r["family"],
                r["canonical"],
                r["validity"],
            ),
        )
        weakest.append(
            [
                LABELS[m],
                r["family"],
                r["canonical"],
                r["validity"],
                fraction(r["matched"], r["samples"]),
            ]
        )
    table(
        ["Model", "Family", "Order", "Source label", "Lowest observed group"], weakest
    )
    text(
        "These are the lowest groups selected after inspecting the complete table. They locate patterns for review, not independently tested hypotheses. For a valid target, an interpreted no is a disagreement; for an invalid target, an interpreted yes is a disagreement. A broad tendency to answer yes or no can therefore look very different across labels."
    )
    table(
        ["Model / family / source label", "Yes / interpreted", "No / interpreted"],
        [
            [
                f"{LABELS[r['model']]} / {r['family']} / {r['validity']}",
                fraction(r["yes"], r["answered"]),
                fraction(r["no"], r["answered"]),
            ]
            for r in t["answer_bias"]
        ],
    )
    heading("6. Formulation, vocabulary, and tense")
    figure(
        "05_formulation",
        "The two mHS formulations within order and label.",
        "Read across models within one row before comparing rows. Counts use the observed subgroup, not all mHS cases.",
        "The explicit-inference formulation contains especially low groups for mini and Luna. Gemini 3.5 also has its largest local deficit in explicit-inference, canonical, invalid-labeled cases.",
        "A phrasing association is not proof that the connective itself caused the response.",
    )
    figure(
        "05_lexical",
        "Lexical conditions within HS and mHS.",
        "HF, LF, and NS are separate source conditions. Each cell pools tense, order, labels, and applicable formulations.",
        "The differences are model-specific. For example, Haiku's lowest HS lexical group is LF, while GPT-4o mini's lowest mHS lexical group is HF.",
        "These pooled rates do not measure an isolated word-frequency mechanism or a general language ability.",
    )
    figure(
        "05_tense",
        "Verbal-time conditions within HS and mHS.",
        "PA is past, PR present, and FU future. Use the same color scale and the cell denominators.",
        "Temporal patterns are smaller than some order/label contrasts, but not uniform across models. The complete stratum table allows the pooled patterns to be checked at finer resolution.",
        "A tense association can reflect other details of the particular questions. No causal effect is estimated.",
    )
    text(
        "Tables/formulation.csv, lexical.csv, tense.csv, and stratum.csv contain all counts, coverage, format, answer categories, and rates behind these plots. The stratum table has 648 model/stratum rows with 500 cases each. Do not treat the visually selected low groups as the only results."
    )
    heading("7. Do models disagree on the same cases?")
    figure(
        "06_pairs",
        "Agreement between every pair of model answers.",
        "The denominator contains only cases interpreted by both models. The diagonal is the same model, not an independent repeat.",
        "High answer agreement indicates similar decisions on the same UIDs. Low agreement locates different response patterns. It does not by itself tell which model matches the source label.",
        "Agreement between models is neither an independent logical audit nor a measure of response stability.",
    )
    table(
        [
            "Model A / Model B",
            "Both interpreted / 54,000",
            "Same answer / both",
            "Only A matches",
            "Only B matches",
        ],
        [
            [
                LABELS[r["model_a"]] + " / " + LABELS[r["model_b"]],
                fraction(r["both_interpreted"], 54000),
                fraction(r["same_answer"], r["both_interpreted"]),
                fraction(r["a_only_match"], r["both_interpreted"]),
                fraction(r["b_only_match"], r["both_interpreted"]),
            ]
            for r in t["pairs"]
        ],
    )
    figure(
        "06_concentration",
        "The count of disagreeing models for each question.",
        "Count only interpreted answers that disagree with the source label. A bar at zero can still contain a filtered or otherwise uninterpretable answer.",
        f"There are {sum(r['cases'] for r in t['concentration'] if r['disagrees'] == 1):,} cases with one disagreeing model and {sum(r['cases'] for r in t['concentration'] if r['disagrees'] >= 2):,} with two or more. Another {sum(r['cases'] for r in t['concentration'] if r['disagrees'] == 0):,} have no interpreted disagreement. Shared disagreement is a useful queue for manual review of prompts, labels, and model answers.",
        "Even unanimous disagreement would not prove that a source label is wrong. Models can share mistakes.",
    )
    heading("8. Usable answers and strict format")
    figure(
        "07_format_filters",
        "Interpretable format violations and content filters.",
        "These are counts over 54,000 responses per model. The two panels have different count scales.",
        "Sonnet supplies many interpretable responses outside the requested format. Haiku accounts for the content filters. These are different operational problems: parsing can recover some format violations, but cannot recover a filtered answer.",
        "The deterministic parser does not certify that an explanation is logically sound. Filters do not imply a yes or no answer.",
    )
    table(
        [
            "Model",
            "Interpretable non-strict",
            "Filters",
            "Empty",
            "Ambiguous",
            "Invalid format",
            "Output error",
        ],
        [
            [
                LABELS[m],
                totals[m]["nonstrict_answered"],
                totals[m]["content_filter"],
                totals[m]["empty"],
                totals[m]["ambiguous"],
                totals[m]["invalid_format"],
                totals[m]["error"],
            ]
            for m in models
        ],
    )
    text(
        "All category counts in this table use 54,000 planned responses per model. Full category counts by condition are included in every cross-condition CSV. Final execution errors and scorer output-error categories are distinct; neither is folded into a negative answer."
    )
    filtered = [r for r in t["lexical"] if r["content_filter"]]
    text(
        "Haiku filters occur in these lexical groups: "
        + "; ".join(
            f"{r['family']} {r['frequency']}: {fraction(r['content_filter'], r['samples'])}"
            for r in filtered
        )
        + ". There are no HF filters. This distribution does not establish why the provider filtered a request."
    )
    heading("9. Original cases for close reading")
    text(
        "The following cases are selected by ascending SHA-256 of the UID within each family and category: model disagreement, filter, and interpretable non-strict output. A case is never reused. This deterministic rule makes examples reproducible, not statistically representative. All six raw responses are shown. The source labels remain unchanged and any logical concern needs a separate audit."
    )
    for example in data["examples"]:
        heading(example["family"] + ": " + example["category"], 3)
        c = example["case"]
        if c is None:
            text(
                "No case is available in this category after excluding previously selected cases."
            )
            continue
        text(
            f"UID: {c['uid']}. Source: {c['original_path']}; row {c['row_number']}. Source label: {c['validity']}; target: {c['target']}. Conditions: {c['frequency']}, {c['tense']}, {c['canonical']}; {c['formulation']}."
        )
        literal(c["prompt"])
        for r in example["answers"]:
            text(
                f"{LABELS[r['model']]}: category {r['status']}; interpretation {r['answer'] if r['answer'] is not None else 'none'}; matched {r['matched']}; strict format {r['strict']}. Raw response:"
            )
            literal(r["raw"] or "[No response text]")
        text(
            "Reading: compare the raw response with the stored interpretation before comparing it with the target. This case illustrates the named category; it does not establish the frequency or cause of that behavior."
        )
    heading("10. Cost and time: secondary decision evidence")
    figure(
        "08_cost_time",
        "Known corpus costs and observed sample durations.",
        "Costs include known final and additional-attempt charges. Time markers show mean and p90 for 54,000 observed samples per model.",
        "Sonnet accounts for most of the known cost. Sample times are much closer than costs. A low cost or short sample time does not repair a source-label disagreement.",
        "Missing charges prevent a complete bill. Concurrent sample durations cannot be added to infer elapsed run time or used as a guaranteed future speed.",
    )
    table(
        [
            "Phase / model / role",
            "Generation IDs",
            "Known IDs",
            "Unknown IDs",
            "Known USD",
        ],
        [
            [
                f"{r['phase']} / {LABELS[r['model']]} / {r['kind']}",
                r["generations"],
                r["known_cost_ids"],
                r["unknown_cost_ids"],
                "unknown" if r["known_usd"] is None else f"{r['known_usd']:.8f}",
            ]
            for r in t["costs"]
        ],
    )
    table(
        [
            "Phase / model",
            "Input tokens",
            "Output tokens",
            "Reported reasoning tokens",
            "Missing input / output / reasoning",
        ],
        [
            [
                f"{r['phase']} / {LABELS[r['model']]}",
                r["input_tokens"],
                r["output_tokens"],
                r["reasoning_tokens"],
                f"{r['unknown_input']} / {r['unknown_output']} / {r['unknown_reasoning']}",
            ]
            for r in t["tokens"]
        ],
    )
    corpus_cost = sum(r["known_usd"] or 0 for r in t["costs"] if r["phase"] == "corpus")
    preflight_cost = sum(
        r["known_usd"] or 0 for r in t["costs"] if r["phase"] == "preflight"
    )
    text(
        f"Known corpus charges total USD {corpus_cost:.8f}; preflight adds USD {preflight_cost:.9f}. The ledger has {source['ledger']['unknown_ids']:,} generation IDs with unknown costs: 352 final Haiku filter outcomes and 426 additional Luna attempts. There is also an additional Gemini 3.1 attempt without a generation ID. It cannot be assigned a known charge. These missing values prevent a complete total."
    )
    timing = source["timing"]
    text(
        f"The evaluation interval was {timing['evaluation_seconds'] / 3600:.2f} hours, followed by {timing['finalization_seconds'] / 60:.2f} minutes of closure/export. Including startup, total duration was {timing['total_seconds'] / 3600:.2f} hours. These are observed workflow intervals, not pure model generation time. The run used six active tasks, 32 sample slots per task, and adaptive per-model connections. The source report contains the operational telemetry and its limitations."
    )
    text(
        "Charges are deduplicated by generation ID in the source ledger. Unknown costs remain unknown; known zero charges remain zero. Preflight stays separate. Additional attempts are cost evidence, not additional independent corpus answers. This analysis does not extrapolate a new full-corpus cost because the full corpus has already been run."
    )
    heading("11. Conclusions and next analyses")
    text(
        "For this corpus and these fixed conditions, Gemini 3.1 Flash-Lite combines very high source-label agreement, near-complete strict format, and low known cost. Sonnet has slightly more matching answers but many more format violations and a much higher known cost. This supports a practical shortlist, not a universal recommendation or a claim that one model reasons better in general."
    )
    text(
        "Do not select mini, Luna, or Haiku from the overall mean alone. Their condition profiles differ sharply. A system that needs a specific type of mHS question can encounter much lower agreement than the model's average. For Gemini 3.5, the perfect HS result also hides mHS disagreements. A newer label does not guarantee a better result on this task."
    )
    text(
        "Next, conduct a separate logical audit of a prespecified selection from low-agreement groups and shared disagreements. Include controls from high-agreement groups to avoid reviewing only failures. Preserve the source labels and publish any audited labels as a new version. Then use repeated independent runs on a fixed subset to measure response variation. Neither step is performed here."
    )
    text(
        "Possible mechanisms include response tendencies, sensitivity to formulation, and problems in source labels. These are hypotheses, not findings established by this execution. Model versions, providers, tiers, and reasoning controls differ together. The corpus is structured and finite; it does not sample all language or reasoning tasks."
    )
    heading("12. Reproduction and data checks")
    text(
        "All numbers and figures come from the derived tables in this folder. summary.json contains the same analytical data; document.json contains the shared editorial blocks used for Markdown, HTML, and the continuous PDF. provenance.json records input and analysis-source hashes. validation.json records the completed checks. Inputs were read from the validated analysis-v1 bundle, not regenerated from model requests."
    )
    text(
        "Validation checks 54,000 unique cases; six model responses per UID; 108 model/dataset tasks; 108 source strata with 500 cases each; 648 model/stratum groups; and 15 model pairs. Prompt hashes and all response fields are checked between JSON and CSV. Totals, strata, pairs, and the generation cost ledger reconcile with the published report. This is a verification of the derived inputs, not a new logical audit of the original questions."
    )
    literal(
        "uv run --locked transitivity interpret --report reports/full/2026-11-06_01-23-40-040fd7b7/analysis-v1 --output reports/full/2026-11-06_01-23-40-040fd7b7/new-interpretation"
    )
    text(
        "The output directory must not exist. The command performs no provider API calls. Open index.html directly: it needs no server, JavaScript, or external assets. Original logs, scores, source records, and the earlier report remain unchanged."
    )
    if source.get("correction"):
        correction = source["correction"]
        blocks.insert(
            1,
            {
                "kind": "text",
                "text": "Corrected principal corpus: 320,328 original responses and 3,672 replacement responses for 612 corrected questions. Only eate changed to ate. This combines two executions. Source labels are unchanged. Response changes do not isolate the causal effect of the text correction.",
            },
        )
        for block in blocks:
            if block["kind"] == "text":
                block["text"] = block["text"].replace("analysis-v1", "analysis-v3")
                if "The evaluation interval was" in block["text"]:
                    block["text"] = (
                        "Original execution only. "
                        + block["text"]
                        + f" The separate replacement corpus phase took {correction['replacement_seconds'] / 60:.2f} minutes including closure. The composite has no continuous execution duration."
                    )
                if "Known corpus charges total" in block["text"]:
                    block["text"] = (
                        f"Known costs for retained and replacement corpus responses total USD {corpus_cost:.8f}. The original preflight adds USD {preflight_cost:.9f}. The cost table separately records superseded calls and the correction preflight. Unknown charges remain unknown; these totals are not a complete bill."
                    )
    return blocks
