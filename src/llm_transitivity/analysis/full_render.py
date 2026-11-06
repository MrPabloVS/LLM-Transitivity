"""Present one verified summary as readable Markdown, HTML, and SVG figures."""

import html
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import markdown
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from llm_transitivity.analysis.full_store import file_hash, read_json, require
from llm_transitivity.analysis.full_summary import query, write_json

LABELS = {
    "openai/gpt-4o-mini": "GPT-4o mini",
    "openai/gpt-6-luna": "GPT-6 Luna Flex",
    "anthropic/claude-haiku-5.5": "Claude Haiku 5.5",
    "anthropic/claude-sonnet-5.5": "Claude Sonnet 5.5",
    "google/gemini-3.1-flash-lite": "Gemini 3.1 Flash-Lite Flex",
    "google/gemini-3.5-flash-lite": "Gemini 3.5 Flash-Lite Flex",
}


def ratio(n, d):
    return f"{n:,}/{d:,} ({100 * n / d:.2f}%)" if d else f"{n:,}/{d:,} (undefined)"


def money(value):
    return "unknown" if value is None else f"{value:.6f}"


def table(headers, rows):
    def cell(v):
        return html.escape(str(v)).replace("|", "&#124;").replace("\n", " ")

    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *["| " + " | ".join(cell(v) for v in row) + " |" for row in rows],
        ]
    )


def literal(text):
    return "<pre>" + html.escape(text) + "</pre>"


def figures(output, summary):
    dest = output / "figures"
    dest.mkdir()
    plt.rcParams.update(
        {
            "svg.hashsalt": "full-corpus-v1",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    models = summary["models"]
    rows = {r["model"]: r for r in summary["totals"]}
    fig, ax = plt.subplots(figsize=(12, 6.5), layout="constrained")
    left = np.zeros(len(models))
    for key, label, color in (
        ("tp", "True positive (source yes)", "#0072B2"),
        ("tn", "True negative (source no)", "#009E73"),
        ("fp", "False positive (source no)", "#D55E00"),
        ("fn", "False negative (source yes)", "#6A51A3"),
        ("content_filter", "Content filter", "#bd8a24"),
        ("ambiguous", "Ambiguous", "#777b85"),
        ("empty", "Empty", "#aaaaaa"),
        ("invalid_format", "Unsupported format", "#bbaacc"),
        ("error", "Output error", "#444444"),
    ):
        values = np.array(
            [
                (
                    rows[m][key]
                    if key != "other"
                    else rows[m]["samples"]
                    - rows[m]["answered"]
                    - rows[m]["content_filter"]
                )
                / rows[m]["samples"]
                * 100
                for m in models
            ]
        )
        ax.barh(
            [LABELS[m] for m in models], values, left=left, label=label, color=color
        )
        left += values
    ax.invert_yaxis()
    ax.set(
        xlabel="Percent of all 54,000 cases per model",
        xlim=(0, 100),
        title="What each model returned",
    )
    ax.legend(loc="upper center", bbox_to_anchor=(0.35, -0.17), ncols=2, frameon=False)
    fig.savefig(dest / "outcomes.svg", metadata={"Date": None})
    fig.savefig(
        (dest / "outcomes.svg").with_suffix(".png"), dpi=150, bbox_inches="tight"
    )
    plt.close(fig)
    datasets = [r["dataset"] for r in summary["cases"]]
    for dimension, conditions, title in (
        ("dataset", datasets, "Source-label agreement by dataset"),
        ("family", ["HS", "mHS"], "Source-label agreement by case family"),
    ):
        lookup = {
            (r["model"], r["condition"]): r["agreement"]
            for r in summary["breakdowns"][dimension]
        }
        values = np.array(
            [
                [
                    np.nan if lookup[(m, c)] is None else lookup[(m, c)] * 100
                    for m in models
                ]
                for c in conditions
            ]
        )
        fig, ax = plt.subplots(
            figsize=(11, 2.2 + len(conditions) * 0.35), layout="constrained"
        )
        heat = ax.imshow(values, vmin=0, vmax=100, cmap="YlGnBu", aspect="auto")
        ax.set_xticks(
            range(len(models)), [LABELS[m] for m in models], rotation=28, ha="right"
        )
        ax.set_yticks(range(len(conditions)), conditions)
        for i in range(len(conditions)):
            for j in range(len(models)):
                ax.text(
                    j,
                    i,
                    "—" if np.isnan(values[i, j]) else f"{values[i, j]:.1f}",
                    ha="center",
                    va="center",
                    color="white" if values[i, j] > 65 else "black",
                    fontsize=8,
                )
        ax.set_title(title + "\nDenominator: interpretable answers in each cell")
        fig.colorbar(heat, ax=ax, label="Percent")
        fig.savefig(dest / f"{dimension}_agreement.svg", metadata={"Date": None})
        fig.savefig(
            (dest / f"{dimension}_agreement.svg").with_suffix(".png"),
            dpi=150,
            bbox_inches="tight",
        )
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    start = summary["timing"]["corpus_started"]
    end = (summary["timing"]["last_task_completed"] - start) / 60
    for model in models:
        changes = [
            c
            for c in summary["adaptive_history"]
            if c["model"].removeprefix("openrouter/") == model
        ]
        xs = [0] + [(c["timestamp"] - start) / 60 for c in changes] + [end]
        ys = [20] + [c["new_limit"] for c in changes]
        ys.append(ys[-1])
        ax.step(xs, ys, where="post", label=LABELS[model], alpha=0.75)
    ax.set(
        xlabel="Minutes after corpus phase start",
        ylabel="Connection limit per model",
        title="Recorded adaptive limits (not observed request concurrency)",
    )
    ax.legend(fontsize=7, loc="lower right")
    fig.savefig(dest / "adaptive_limits.svg", metadata={"Date": None})
    fig.savefig(
        (dest / "adaptive_limits.svg").with_suffix(".png"), dpi=150, bbox_inches="tight"
    )
    plt.close(fig)


def copy_cards(root, run, output):
    manifest_path = (
        run / "corpus/provenance/snapshot/docs/model_cards/pilot-3-manifest.json"
    )
    manifest = read_json(manifest_path)
    links = {}
    for entry in manifest["models"]:
        model = entry["model_id"]
        slug = model.replace("/", "--")
        directory = output / "cards" / slug
        directory.mkdir(parents=True)
        for key, info in entry["files"].items():
            path = root / "docs/model_cards" / info["path"]
            require(
                file_hash(path) == info["sha256"], "Model card evidence hash differs"
            )
            shutil.copyfile(path, directory / path.name)
            if key == "card.md":
                links[model] = f"cards/{slug}/{path.name}"
    write_json(output / "cards/manifest.json", manifest)
    return links


def narrative(db, summary, card_links):
    models = summary["models"]
    totals = {r["model"]: r for r in summary["totals"]}
    config = summary["configuration"]
    best = max(
        summary["totals"],
        key=lambda r: r["agreement"] if r["agreement"] is not None else -1,
    )
    matches = sum(r["matched"] for r in totals.values())
    filtered = sum(r["content_filter"] for r in totals.values())
    other = sum(
        r["samples"] - r["answered"] - r["content_filter"] for r in totals.values()
    )
    lines = [
        "# Full-corpus results: what we tested and what we found",
        "",
        f"Run: `{summary['run_id']}`. Analysis: `{summary['analysis_version']}`.",
        "",
        "[Interactive tables](explorer.html#aggregate) · [Case explorer](explorer.html#explorer)",
        "",
        "[Continuous PDF](report.pdf) \u00b7 [Detailed setup guide (Spanish)](https://github.com/MrPabloVS/LLM-Transitivity/blob/tobe/runs-2026-11-05/docs/guia_informe_es.md)",
        "",
        "## Main findings",
        "",
        "Six models answered the same 54,000 distinct questions. All 108 tasks completed. The corpus has 324,000 saved responses and zero final sample execution errors.",
        f"There were {matches:,} source-label matches, {filtered:,} content filters, and {other:,} other non-interpretable responses across all models. These are separate outcomes.",
        f"{LABELS[best['model']]} had the highest observed agreement with source labels: {ratio(best['matched'], best['answered'])}. This comparison concerns this corpus and this run. Source labels have not been independently audited for logical validity.",
        "",
        "Sonnet 5.5 and Gemini 3.1 Flash-Lite are close in source-label agreement, but differ in format compliance and reported cost. See the tables below for exact counts and missing cost evidence.",
        "",
        "[TOC]",
        "",
        "## What question does the experiment ask?",
        "",
        "We test how six language models answer hypothetical syllogism and metainferential hypothetical syllogism questions under different lexical and grammatical conditions. We compare each answer with the label supplied by the dataset. We also test whether the model follows a strict response-format instruction.",
        "",
        "Every case uses a new conversation, one system message, and one original question. No examples are supplied in the prompt (zero-shot). The system message is:",
        "",
        literal(summary["system_prompt"]),
        "",
        "A case is one complete reasoning question. It can contain several clauses or sentences. We count cases, not individual clauses. The 54,000 question texts are distinct by exact text comparison.",
        "",
        "## What cases are in the corpus?",
        "",
        table(
            ["Code", "Meaning", "Cases"],
            [
                ["HS", "Hypothetical syllogism expressed with conditionals", "18,000"],
                [
                    "mHS",
                    "Metainferential hypothetical syllogism: relations between inferences",
                    "36,000",
                ],
                [
                    "HF / LF / NS",
                    "High-frequency words / low-frequency words / pseudowords",
                    "18,000 each",
                ],
                ["PR / PA / FU", "Present / past / future", "18,000 each"],
                [
                    "canonic / non-canonic",
                    "Standard / reversed premise order, as labeled by the source",
                    "27,000 each",
                ],
                ["valid / invalid", "Source validity label", "27,000 each"],
            ],
        ),
        "",
        "NS is a pseudoword condition, not another level of word frequency. The filename identifies HS versus mHS; the original internal case-type field is HS in both families. We preserve that field and report family separately.",
        "",
        "Each HS dataset has four strata: source validity crossed with premise order. Each mHS dataset has eight strata: those four combinations crossed with two formulations. The formulations are `assuming that we can infer / thus` and `from the inference (therefore) / does the inference follow`. Each stratum contains 500 cases. The complete design has 108 strata.",
        "",
        table(
            ["Dataset", "Family", "Lexical condition", "Tense", "Cases", "Strata"],
            [
                [
                    r[k]
                    for k in (
                        "dataset",
                        "family",
                        "frequency",
                        "tense",
                        "cases",
                        "strata",
                    )
                ]
                for r in summary["cases"]
            ],
        ),
        "",
        "mHS accounts for two thirds of the corpus. Overall results weight each case equally, so mHS has twice the weight of HS. Family-specific results are shown separately. The source labels are balanced: 27,000 valid and 27,000 invalid cases.",
        "",
        "Working inputs preserve the original question text, order, source identifiers, and all record fields, except the approved translations of `valido` to `valid` and `canonico` to `canonic` in the two LF/PR datasets. The analysis verifies every saved prompt and target against the frozen inputs and the Git source revision.",
        "",
        "## Which models answered?",
        "",
        "The exact model IDs identify the experiment. Provider, service tier, and reasoning settings are part of each model condition. These differences prevent us from attributing differences to a model name or reasoning setting alone.",
        "",
    ]
    lines += [
        table(
            ["Model ID", "Fixed endpoint", "Tier", "Reasoning requested", "Effort"],
            [
                [
                    m,
                    config["requested_routing"][m]["provider_only"][0],
                    config["requested_routing"][m]["service_tier"],
                    config["model_reasoning_policies"][m]["policy"],
                    config["model_reasoning_policies"][m]["effort"] or "omitted",
                ]
                for m in models
            ],
        ),
        "",
    ]
    lines += [f"- [{LABELS[m]}: archived model card]({card_links[m]})" for m in models]
    lines += [
        "",
        "Providers were fixed and fallbacks disabled. The output limit was 1,024 tokens, including reasoning where the provider counts it in the output budget. Temperature, top-p, and seed were omitted. Responses are not deterministic. Caching and streaming were disabled.",
        "",
        "The archived `earlier` and `later` tags are comparison slots. They are not equivalent generations across developers. Haiku and Sonnet are different model families. The main results therefore compare six individual models.",
        "",
        "## How are answers counted?",
        "",
        table(
            ["Measure", "Numerator", "Denominator"],
            [
                ["Source-label agreement", "Matches", "Interpretable answers"],
                [
                    "Interpretation coverage",
                    "Interpretable answers",
                    "All planned cases",
                ],
                [
                    "Strict-format compliance",
                    "Only yes or no, ignoring case and outer whitespace",
                    "All planned cases",
                ],
                ["Matches over all cases", "Matches", "All planned cases"],
            ],
        ),
        "",
        "Scoring uses `source-label-deterministic-v3` and extraction rule `initial_or_final_line_v2`. It can read a supported yes/no answer at the beginning or on the final line. Explanations, punctuation, and bold answers may be interpretable but still fail the strict-format instruction. A response containing both complete terms yes and no is ambiguous. Errors, filters, empty responses, ambiguity, and unsupported formats keep their existing precedence. They are never converted to no.",
        "",
        "A source-label disagreement is not automatically a logical error. A source-label match is not independent proof of logical validity. We do not change source labels or scores in this report.",
        "",
        "## What did each model return?",
        "",
        table(
            [
                "Model",
                "Agreement / interpreted",
                "Coverage / 54,000",
                "Strict / 54,000",
                "Matches / 54,000",
            ],
            [
                [
                    LABELS[m],
                    ratio(totals[m]["matched"], totals[m]["answered"]),
                    ratio(totals[m]["answered"], totals[m]["samples"]),
                    ratio(totals[m]["strict"], totals[m]["samples"]),
                    ratio(totals[m]["matched"], totals[m]["samples"]),
                ]
                for m in models
            ],
        ),
        "",
        table(
            [
                "Model",
                "Matches",
                "Disagreements",
                "FP",
                "FN",
                "Filters",
                "Empty",
                "Ambiguous",
                "Unsupported format",
                "Errors",
            ],
            [
                [
                    LABELS[m],
                    *[
                        f"{totals[m][k]:,}"
                        for k in (
                            "matched",
                            "disagreed",
                            "fp",
                            "fn",
                            "content_filter",
                            "empty",
                            "ambiguous",
                            "invalid_format",
                            "error",
                        )
                    ],
                ]
                for m in models
            ],
        ),
        "",
        "![Outcomes over all cases](figures/outcomes.svg)",
        "",
        "### False positives and false negatives",
        "",
        "Positive means yes. FP is an interpreted yes when the source target is no; FN is an interpreted no when the source target is yes. TP and TN match the source target. These terms refer to source labels, not audited logical truth. Filters and other non-interpretable outcomes remain separate.",
        "",
        "FPR = FP / (FP + TN), among interpreted source-negative cases. FNR = FN / (FN + TP), among interpreted source-positive cases. Class coverage uses every planned case of that source class. Undefined means that the denominator is zero; it does not mean a zero error rate.",
        "",
        error_table(summary["totals"]),
        "",
        "![False positive and negative rates](figures/false_rates.svg)",
        "",
        "Haiku and Luna have more false positives than false negatives in this run. GPT-4o mini has more false negatives. Sonnet and Gemini 3.1 have no false positives among their interpreted responses; their disagreements are false negatives. This describes the direction of source-label disagreement, not its cause.",
        "",
        "### Yes and no answers",
        "",
        table(
            ["Model", "Interpreted answer", "Count"],
            [
                [LABELS[r["model"]], r["answer"], r["samples"]]
                for r in summary["answer_distribution"]
            ],
        ),
        "",
        "The [source-label confusion table](tables/confusion.csv) crosses the expected answer with the interpreted answer. It excludes non-interpretable responses, whose counts remain above.",
        "",
        "## Where do results differ?",
        "",
        "The following tables compare observed results within the corpus. They do not establish causal effects. Each cell states its denominator. Comparisons between models use the same source cases; comparisons between conditions do not assume that cases are matched pairs.",
        "",
        "![Agreement by family](figures/family_agreement.svg)",
        "",
    ]
    names = {
        "family": "Case family",
        "frequency": "Lexical condition",
        "tense": "Verbal time",
        "canonical": "Premise order",
        "validity": "Source validity label",
        "formulation": "Question formulation",
    }
    for dimension, title in names.items():
        values = summary["breakdowns"][dimension]
        by_model = {
            m: [r for r in values if r["model"] == m and r["agreement"] is not None]
            for m in models
        }
        gaps = [
            (
                max(rows, key=lambda r: r["agreement"]),
                min(rows, key=lambda r: r["agreement"]),
            )
            for rows in by_model.values()
            if len(rows) > 1
        ]
        high, low = max(
            gaps, key=lambda pair: pair[0]["agreement"] - pair[1]["agreement"]
        )
        gap = (high["agreement"] - low["agreement"]) * 100
        lines += [
            f"### {title}",
            "",
            f"The largest observed range across {title.lower()} is for {LABELS[high['model']]}: {gap:.2f} percentage points between {high['condition']} ({ratio(high['matched'], high['answered'])}) and {low['condition']} ({ratio(low['matched'], low['answered'])}). This is a descriptive comparison.",
            "",
        ]
        lines += [
            table(
                ["Model", "Condition", "Agreement", "Coverage", "Strict format"],
                [
                    [
                        LABELS[r["model"]],
                        r["condition"],
                        ratio(r["matched"], r["answered"]),
                        ratio(r["answered"], r["samples"]),
                        ratio(r["strict"], r["samples"]),
                    ]
                    for r in summary["breakdowns"][dimension]
                ],
            ),
            "",
        ]
        lines += [error_table(values, condition=True), ""]
        for figure in summary["error_figures"][dimension]:
            lines += [f"![FPR and FNR by {dimension}](figures/{figure}.svg)", ""]
    lines += [
        "### Datasets and complete strata",
        "",
        "![Agreement by dataset](figures/dataset_agreement.svg)",
        "",
        "The [dataset table](tables/by_dataset.csv) contains all 108 model/dataset cells. The [stratum results](tables/by_stratum.csv) contain all 648 model/stratum cells. Join them to the [stratum definitions](tables/stratum_definitions.csv) by stratum. The HTML report supports combined condition filters.",
        "",
        error_table(summary["breakdowns"]["dataset"], condition=True),
        "",
        *[
            item
            for dimension in ("dataset", "stratum")
            for figure in summary["error_figures"][dimension]
            for item in (f"![FPR and FNR by {dimension}](figures/{figure}.svg)", "")
        ],
        "Every heatmap uses the same 0-100% scale and prints its numerator and denominator. Gray cells are undefined, not zero. Stratum IDs map to tables/stratum_definitions.csv. The condition CSVs retain all counts and class coverage values. The separate explorer recomputes rates from counts when filters are combined.",
        "",
        "## Do models disagree on the same cases?",
        "",
        "Each pair contains the same 54,000 UIDs. Agreement between answers and one-model-only source matches use only cases where both models gave interpretable answers. The excluded count remains visible. No missing answer is treated as a disagreement.",
        "",
        table(
            [
                "Model A",
                "Model B",
                "Same answer / both interpreted",
                "Only A matches",
                "Only B matches",
                "Both match",
                "Both disagree",
                "Not both interpreted",
            ],
            [
                [
                    LABELS[r["model_a"]],
                    LABELS[r["model_b"]],
                    ratio(r["same_answer"], r["both_interpreted"]),
                    r["a_only_match"],
                    r["b_only_match"],
                    r["both_match"],
                    r["both_disagree"],
                    r["not_both_interpreted"],
                ]
                for r in summary["pairwise"]
            ],
        ),
        "",
        "## Cases that make the results concrete",
        "",
        "Examples are selected by the smallest SHA-256 hash of the UID for each family and category, without repeating a case. Family order is HS then mHS; category order is different answers, content filter, then interpretable non-strict format. These examples illustrate outcomes; they do not estimate prevalence. The HTML explorer exposes every case.",
        "",
    ]
    for example in summary["examples"]:
        lines += [f"### {example['family']}: {example['category']}", ""]
        if not example["uid"]:
            lines += ["No unused case meets this category.", ""]
            continue
        case = dict(
            db.execute("SELECT * FROM cases WHERE uid=?", (example["uid"],)).fetchone()
        )
        responses = query(
            db,
            "SELECT * FROM results WHERE phase='corpus' AND uid=? ORDER BY model",
            (case["uid"],),
        )
        lines += [
            f"UID: `{case['uid']}`. Dataset: `{case['dataset']}`; original row {case['row_number']}. Source label: `{case['validity']}`; expected answer: `{case['target']}`.",
            "",
            literal(case["prompt"]),
            "",
            table(
                ["Model", "Interpreted answer", "Outcome", "Strict format"],
                [
                    [
                        LABELS[r["model"]],
                        r["answer"] or "not interpreted",
                        r["status"]
                        if r["status"] != "answered"
                        else "match"
                        if r["matched"]
                        else "disagreement",
                        bool(r["strict"]),
                    ]
                    for r in responses
                ],
            ),
            "",
        ]
        for r in responses:
            lines += [
                f"**{LABELS[r['model']]} — original response**",
                "",
                literal(r["raw"]),
                "",
            ]
    lines += [
        "## What did the run cost?",
        "",
        "These are costs reported by OpenRouter, not an independent invoice audit. Costs are deduplicated by generation ID. A captured response cost takes precedence over a later lookup; conflicting observations remain in the database and conflict table. Zero is retained as zero. Missing costs remain unknown.",
        "",
        table(
            [
                "Phase",
                "Model",
                "Generation role",
                "IDs with cost / all IDs",
                "Unknown-cost IDs",
                "Known USD",
            ],
            [
                [
                    r["phase"],
                    LABELS[r["model"]],
                    r["kind"],
                    f"{r['known_cost_ids']}/{r['generations']}",
                    r["unknown_cost_ids"],
                    money(r["known_usd"]),
                ]
                for r in summary["costs"]
            ],
        ),
        "",
        f"Across this run's corpus and six-call preflight, known reported cost is **USD {money(summary['ledger']['known_usd'])}**. There are **{summary['ledger']['unknown_ids']:,} generation IDs with unknown cost** and **{summary['cost_conflicts']:,} conflicting cost observations**. Amounts from earlier runs are excluded.",
        "",
        "Final generations have an explicit final response ID. Additional generations are other identified attempts for a sample with a final ID. Unresolved generations belong to samples without an explicit final ID; their role is not guessed. Attempts without IDs cannot be assigned a deduplicated cost.",
        "",
        table(
            [
                "Phase",
                "Model",
                "HTTP attempts",
                "Failed attempts",
                "Attempts without ID",
                "Without end timestamp",
            ],
            [
                [
                    r["phase"],
                    LABELS[r["model"]],
                    r["attempts"],
                    r["failed_attempts"],
                    r["attempts_without_id"],
                    r["attempts_without_end"],
                ]
                for r in summary["attempts"]
            ],
        ),
        "",
        "A failed HTTP attempt has no response, HTTP status 4xx/5xx, or an error payload inside HTTP 200. The count of attempts beyond one per sample measures additional HTTP attempts; it does not add new cases. A filter is a recorded response outcome and does not by itself trigger a replacement generation.",
        "",
        "### Tokens in final responses",
        "",
        table(
            [
                "Phase",
                "Model",
                "Input tokens",
                "Output tokens",
                "Reasoning tokens",
                "Unknown input/output/reasoning samples",
            ],
            [
                [
                    r["phase"],
                    LABELS[r["model"]],
                    r["input_tokens"],
                    r["output_tokens"],
                    r["reasoning_tokens"],
                    f"{r['unknown_input']}/{r['unknown_output']}/{r['unknown_reasoning']}",
                ]
                for r in summary["tokens"]
            ],
        ),
        "",
        "Token totals come from final output usage. They exclude usage missing from that field and do not count the usage of failed attempts as zero. Reported zero reasoning tokens do not prove the absence of unreported internal processing.",
        "",
        "## What conclusions are supported?",
        "",
        "The results describe these six model/provider/reasoning conditions on this fixed corpus in one execution. Interpret agreement together with coverage and strict-format compliance. Review the condition tables before using the overall ranking: mHS has twice the weight of HS.",
        "",
        "Models can differ on the same question, and the paired table quantifies those differences without changing the cases. Filters and unparsed responses describe limits in usable coverage. Explanatory text that is interpreted successfully can still violate the requested format.",
        "",
        "Next, review source labels for cases with widespread disagreement and inspect mHS and reversed-order formulations. A logical audit should be a separate versioned analysis. Repeated independent runs would be needed to measure response variability. This report includes no confidence intervals, significance tests, causal claims, or cross-pilot comparisons.",
        "",
        "## Operational appendix: time and concurrency",
        "",
    ]
    timing = summary["timing"]
    clock = lambda t: datetime.fromtimestamp(
        t, ZoneInfo("America/Argentina/Buenos_Aires")
    ).strftime("%Y-%m-%d %H:%M:%S %Z")
    lines += [
        table(
            ["Interval", "Minutes"],
            [
                [
                    "Preparation and dispatch after corpus start",
                    f"{timing['startup_seconds'] / 60:.2f}",
                ],
                [
                    "First task start to last task completion",
                    f"{timing['evaluation_seconds'] / 60:.2f}",
                ],
                [
                    "Finalization and exports after last task",
                    f"{timing['finalization_seconds'] / 60:.2f}",
                ],
                [
                    "Full corpus phase including closure",
                    f"{timing['total_seconds'] / 60:.2f}",
                ],
            ],
        ),
        "",
        f"Corpus phase started at {clock(timing['corpus_started'])} and closed at {clock(timing['corpus_closed'])}. Task duration includes generation, waits, retries, metadata collection, and scoring. It is not pure provider processing time. The preflight is separate.",
        "",
        "The run allowed six active tasks and 32 samples per task, for a 192-slot configured ceiling. Adaptive limits were min 10, start 20, max 64 per model. The controller can reduce limits after rate limits; transient errors pause growth. Limits are not measured request concurrency.",
        "",
        f"The observed peak was **{summary['sample_concurrency']['global']} concurrent samples** and **{summary['http_concurrency']['global']} concurrent captured HTTP intervals with both timestamps**. Missing HTTP end timestamps prevent a complete bound on transport concurrency.",
        "",
        "![Adaptive connection limits](figures/adaptive_limits.svg)",
        "",
        table(
            [
                "Model",
                "Sample peak",
                "HTTP interval peak",
                "Mean sample seconds",
                "P90 sample seconds",
                "Mean HTTP seconds",
                "P90 HTTP seconds",
            ],
            [
                [
                    LABELS[r["model"]],
                    summary["sample_concurrency"]["models"].get(r["model"], 0),
                    summary["http_concurrency"]["models"].get(r["model"], 0),
                    *[
                        f"{r[k]:.2f}" if r[k] is not None else "unknown"
                        for k in (
                            "results_mean_seconds",
                            "results_p90_seconds",
                            "attempts_mean_seconds",
                            "attempts_p90_seconds",
                        )
                    ],
                ]
                for r in summary["latencies"]
            ],
        ),
        "",
        "### Request and returned metadata checks",
        "",
        table(
            [
                "Phase",
                "Model",
                "Samples",
                "Missing captured requests",
                "Samples with condition faults",
                "Samples with reasoning usage reported",
                "Nonzero reasoning reported",
            ],
            [
                [
                    r["phase"],
                    LABELS[r["model"]],
                    *[
                        r[k]
                        for k in (
                            "samples",
                            "missing_requests",
                            "samples_with_faults",
                            "reasoning_observed",
                            "nonzero_reasoning",
                        )
                    ],
                ]
                for r in summary["conditions"]
            ],
        ),
        "",
        "The [returned routing table](tables/reported_routes.csv) preserves reported provider and tier values, including empty sets. Missing evidence is not proof of a setting. The SQLite conditions table retains request-level fault descriptions. Native logs retain complete payloads and fields that this report does not project.",
        "",
        "## Evidence, definitions, and reproduction",
        "",
        "[Summary JSON](summary.json) · [Validation record](validation.json) · [Source and analysis hashes](provenance.json) · [SQLite analysis](analysis.sqlite) · [Response table](tables/responses.csv) · [Generation ledger](tables/generations.csv) · [Cost conflicts](tables/cost_conflicts.csv)",
        "",
        "The report uses only the closed full-corpus run and its separate preflight. Inputs, original responses, native scores, logs, and exports are preserved. Every sample links to its native log and hash in the response table; every case includes source row, original identifiers, and record hashes in the dataset JSON files.",
        "",
        "To rebuild offline, run `uv run --locked transitivity report --run results/full/"
        + summary["run_id"]
        + " --output <new-directory>`. The destination must not exist. No provider API requests are made. To browse the HTML bundle, serve the repository with `uv run --locked python -m http.server 8000` and open this folder's `index.html` through localhost. All runtime assets and case shards are local.",
        "",
    ]
    return with_contents("\n".join(lines))


def with_contents(text):
    """Expand the TOC marker to links that work in plain Markdown."""
    from markdown.extensions.toc import slugify

    entries = []
    for line in text.splitlines():
        if line.startswith(("## ", "### ")):
            level, title = line.split(" ", 1)
            indent = "  " if level == "###" else ""
            entries.append(f"{indent}- [{title}](#{slugify(title, chr(45))})")
    return text.replace("[TOC]", "## Table of contents\n\n" + "\n".join(entries))


def render(db, root: Path, run: Path, output: Path, summary: dict):
    figures(output, summary)
    from llm_transitivity.analysis.full_error_figures import error_figures

    summary["error_figures"] = error_figures(output, summary, LABELS)
    write_json(output / "summary.json", summary)
    links = copy_cards(root, run, output)
    text = narrative(db, summary, links)
    (output / "report.md").write_text(text)
    article = markdown.markdown(text, extensions=["tables", "toc", "fenced_code"])
    assets = Path(__file__).parent / "report_assets"
    for path in assets.iterdir():
        if path.suffix in {".css", ".js"}:
            shutil.copyfile(path, output / path.name)
    shutil.copyfile(assets / "explorer.html", output / "explorer.html")
    template = (assets / "index.html").read_text()
    (output / "index.html").write_text(template.replace("{{REPORT}}", article))
    from llm_transitivity.analysis.full_pdf import render_pdf

    render_pdf(output, article)


def error_table(records, condition=False):
    headers = (
        ["Model"]
        + (["Condition"] if condition else [])
        + [
            "TP",
            "TN",
            "FP",
            "FN",
            "FPR: FP / negatives interpreted",
            "FNR: FN / positives interpreted",
            "Negative coverage",
            "Positive coverage",
        ]
    )
    return table(
        headers,
        [
            [LABELS[r["model"]]]
            + ([r["condition"]] if condition else [])
            + [
                r["tp"],
                r["tn"],
                r["fp"],
                r["fn"],
                ratio(r["fp"], r["negative_answered"]),
                ratio(r["fn"], r["positive_answered"]),
                ratio(r["negative_answered"], r["negative_samples"]),
                ratio(r["positive_answered"], r["positive_samples"]),
            ]
            for r in records
        ],
    )
