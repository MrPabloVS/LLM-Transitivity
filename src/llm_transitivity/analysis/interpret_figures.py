"""Static figures for verified descriptive results."""

import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

LABELS = {
    "openai/gpt-4o-mini": "GPT-4o mini",
    "openai/gpt-6-luna": "GPT-6 Luna Flex",
    "anthropic/claude-haiku-5.5": "Haiku 5.5",
    "anthropic/claude-sonnet-5.5": "Sonnet 5.5",
    "google/gemini-3.1-flash-lite": "Gemini 3.1 Flash-Lite Flex",
    "google/gemini-3.5-flash-lite": "Gemini 3.5 Flash-Lite Flex",
}
COLORS = ["#0072B2", "#56B4E9", "#D55E00", "#E69F00", "#009E73", "#8C6BB1"]


def make_figures(output, data):
    output.mkdir()
    models = data["source"]["models"]
    labels = [LABELS[m] for m in models]
    tables = data["tables"]
    plt.rcParams.update(
        {
            "font.size": 10,
            "svg.hashsalt": "interpretation-v1",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )

    def save(fig, name):
        fig.savefig(output / f"{name}.svg", bbox_inches="tight")
        fig.savefig(output / f"{name}.png", dpi=170, bbox_inches="tight")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 3.2), layout="constrained")
    ax.barh(["HS", "mHS"], [18000, 36000], color=["#0072B2", "#009E73"])
    for y, n in enumerate([18000, 36000]):
        ax.text(n + 500, y, f"{n:,} / 54,000 ({100 * n / 54000:.1f}%)", va="center")
    ax.set(
        xlim=(0, 53000),
        xlabel="Distinct complete questions",
        title="1. Corpus design: mHS has twice the weight of HS",
    )
    save(fig, "01_design")

    totals = {r["model"]: r for r in tables["totals"]}
    fig, axes = plt.subplots(2, 2, figsize=(13, 9.5), layout="constrained")
    for i, (field, title) in enumerate(
        [
            ("matched_total", "Matches / all cases"),
            ("format_rate", "Strict format / all cases"),
            ("coverage", "Interpretable / all cases"),
            ("agreement", "Matches / interpretable responses"),
        ]
    ):
        ax = axes.flat[i]
        ax.barh(labels, [100 * totals[m][field] for m in models], color=COLORS)
        ax.invert_yaxis()
        ax.set(
            xlim=(0, 116), xlabel="Percent (denominator shown in each bar)", title=title
        )
        for j, m in enumerate(models):
            r = totals[m]
            numerator = r[
                {
                    "matched_total": "matched",
                    "format_rate": "strict",
                    "coverage": "answered",
                    "agreement": "matched",
                }[field]
            ]
            denominator = r["answered"] if field == "agreement" else r["samples"]
            ax.text(
                1,
                j,
                f"{numerator:,}/{denominator:,}  |  {100 * r[field]:.2f}%",
                va="center",
                color="#102030" if j in (1, 3) else "white",
                fontweight="bold",
                fontsize=9,
            )
    fig.suptitle("2. Matching a source label and following the format are different")
    save(fig, "02_overall")
    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    high = [m for m in models if totals[m]["matched_total"] > 0.97]
    for m in high:
        ax.scatter(
            100 * totals[m]["matched_total"],
            LABELS[m],
            s=90,
            color=COLORS[models.index(m)],
        )
        ax.annotate(
            f"{totals[m]['matched']:,}/54,000",
            (100 * totals[m]["matched_total"], LABELS[m]),
            xytext=(-5, 12),
            textcoords="offset points",
            ha="right",
        )
    ax.set(
        xlim=(97, 100.12),
        xlabel="Matches / all cases (%) - enlarged scale starts at 97%",
        title="Near the ceiling: small rates still represent distinct cases",
    )
    save(fig, "02_ceiling")

    fig, ax = plt.subplots(figsize=(11, 5.3), layout="constrained")
    lookup = {(r["model"], r["family"]): r for r in tables["family"]}
    for i, m in enumerate(models):
        rates = [100 * lookup[m, f]["matched_total"] for f in ("HS", "mHS")]
        ax.plot(rates, [i, i], color=COLORS[i], linewidth=2)
        for f, marker in [("HS", "o"), ("mHS", "s")]:
            r = lookup[m, f]
            ax.scatter(
                100 * r["matched_total"], i, marker=marker, color=COLORS[i], s=65
            )
            ax.annotate(
                f"{f}: {r['matched']:,}/{r['samples']:,}",
                (100 * r["matched_total"], i),
                xytext=(-4, 10 if f == "HS" else -17),
                textcoords="offset points",
                ha="right",
                fontsize=8,
            )
    ax.set(
        yticks=range(6),
        yticklabels=labels,
        xlim=(0, 110),
        ylim=(-0.6, 5.7),
        xlabel="Matches / all cases (%)",
        title="3. Family contrasts: circles = HS; squares = mHS",
    )
    ax.invert_yaxis()
    save(fig, "03_family")

    def heat(name, title, records, dimensions):
        conditions = sorted({tuple(r[d] for d in dimensions) for r in records})
        lookup = {(r["model"], tuple(r[d] for d in dimensions)): r for r in records}
        values = np.full((len(conditions), len(models)), np.nan)
        for y, condition in enumerate(conditions):
            for x, m in enumerate(models):
                if (m, condition) in lookup:
                    values[y, x] = 100 * lookup[m, condition]["matched_total"]
        fig, ax = plt.subplots(
            figsize=(13, max(4.6, len(conditions) * 0.66)), layout="constrained"
        )
        palette = plt.get_cmap("YlGnBu").copy()
        palette.set_bad("#dddddd")
        picture = ax.imshow(values, vmin=0, vmax=100, cmap=palette, aspect="auto")
        cond_labels = []
        for condition in conditions:
            parts = [
                v.replace(
                    "from the inference (therefore) / does the inference follow",
                    "explicit inference",
                )
                .replace("assuming that we can infer / thus", "assumption / infer")
                .replace("non-canonic", "reversed")
                .replace("canonic", "canonical")
                for v in condition
            ]
            cond_labels.append(" | ".join(parts))
        ax.set(
            xticks=range(6),
            xticklabels=["\n".join(textwrap.wrap(x, 18)) for x in labels],
            yticks=range(len(conditions)),
            yticklabels=cond_labels,
            title=title,
        )
        ax.tick_params(axis="both", length=0)
        for y, condition in enumerate(conditions):
            for x, m in enumerate(models):
                r = lookup.get((m, condition))
                text = (
                    "Absent"
                    if r is None
                    else f"{values[y, x]:.2f}%\n{r['matched']:,}/{r['samples']:,}"
                )
                ax.text(
                    x,
                    y,
                    text,
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white" if values[y, x] > 65 else "black",
                )
        fig.colorbar(picture, ax=ax, label="Matches / all cases (%)", shrink=0.7)
        save(fig, name)

    heat(
        "04_order_label",
        "4. Family, premise order, and source label",
        tables["order_label"],
        ["family", "canonical", "validity"],
    )
    heat(
        "05_formulation",
        "5a. mHS formulations within order and source label",
        [r for r in tables["formulation"] if r["family"] == "mHS"],
        ["formulation", "canonical", "validity"],
    )
    heat(
        "05_lexical",
        "5b. Lexical condition within each family",
        tables["lexical"],
        ["family", "frequency"],
    )
    heat(
        "05_tense",
        "5c. Verbal time within each family",
        tables["tense"],
        ["family", "tense"],
    )

    fig, ax = plt.subplots(figsize=(11, 7), layout="constrained")
    matrix = np.eye(6) * 100
    annotations = {}
    for r in tables["pairs"]:
        i, j = models.index(r["model_a"]), models.index(r["model_b"])
        matrix[i, j] = matrix[j, i] = 100 * r["same_answer"] / r["both_interpreted"]
        annotations[i, j] = annotations[j, i] = (
            f"{matrix[i, j]:.2f}%\n{r['same_answer']:,}/{r['both_interpreted']:,}"
        )
    img = ax.imshow(matrix, vmin=0, vmax=100, cmap="YlGnBu")
    ax.set(
        xticks=range(6),
        xticklabels=["\n".join(textwrap.wrap(x, 15)) for x in labels],
        yticks=range(6),
        yticklabels=labels,
        title="6a. Same answer, among cases interpreted by both models",
    )
    for i in range(6):
        for j in range(6):
            ax.text(
                j,
                i,
                "Same model" if i == j else annotations[i, j],
                ha="center",
                va="center",
                fontsize=8,
                color="white" if matrix[i, j] > 65 else "black",
            )
    fig.colorbar(img, ax=ax, label="Same answer / both interpreted (%)", shrink=0.7)
    save(fig, "06_pairs")
    fig, ax = plt.subplots(figsize=(10, 3.5), layout="constrained")
    rr = tables["concentration"]
    ax.bar([r["disagrees"] for r in rr], [r["cases"] for r in rr], color="#0072B2")
    for r in rr:
        ax.text(
            r["disagrees"],
            r["cases"] + 400,
            f"{r['cases']:,}/54,000",
            ha="center",
            fontsize=9,
        )
    ax.set(
        xticks=range(7),
        xlabel="Number of models with an interpretable disagreement",
        ylabel="Distinct cases",
        ylim=(0, max(r["cases"] for r in rr) * 1.18),
        title="6b. How many models disagree on each question?",
    )
    save(fig, "06_concentration")

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), layout="constrained")
    for ax, field, title in zip(
        axes,
        ["nonstrict_answered", "content_filter"],
        ["Interpretable but outside strict format", "Content filters"],
        strict=True,
    ):
        vals = [totals[m][field] for m in models]
        ax.barh(labels, vals, color=COLORS)
        for i, v in enumerate(vals):
            ax.text(v + max(vals) * 0.015, i, f"{v:,}/54,000", va="center", fontsize=8)
        ax.set(
            xlim=(0, max(vals) * 1.4),
            xlabel="Response count (different scales)",
            title=title,
        )
        ax.invert_yaxis()
    save(fig, "07_format_filters")

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), layout="constrained")
    cost = [
        sum(
            r["known_usd"] or 0
            for r in tables["costs"]
            if r["model"] == m and r["phase"] == "corpus"
        )
        for m in models
    ]
    axes[0].barh(labels, cost, color=COLORS)
    for i, v in enumerate(cost):
        axes[0].text(v + 0.2, i, f"${v:.3f}", va="center", fontsize=8)
    axes[0].set(
        xlim=(0, max(cost) * 1.2),
        xlabel="Known corpus USD; unknown charges excluded",
        title="8a. Observed cost is not a complete bill",
    )
    for i, m in enumerate(models):
        r = next(r for r in tables["latencies"] if r["model"] == m)
        axes[1].plot(
            [r["results_mean_seconds"], r["results_p90_seconds"]],
            [i, i],
            color=COLORS[i],
        )
        axes[1].scatter(r["results_mean_seconds"], i, color=COLORS[i], marker="o")
        axes[1].scatter(r["results_p90_seconds"], i, color=COLORS[i], marker="s")
        axes[1].text(
            r["results_p90_seconds"] + 0.15,
            i,
            f"{r['results_mean_seconds']:.2f} / {r['results_p90_seconds']:.2f}",
            va="center",
            fontsize=8,
        )
    axes[1].set(
        yticks=range(6),
        yticklabels=labels,
        xlim=(0, 16),
        xlabel="Seconds; circle = mean, square = p90",
        title="8b. Sample time, including workflow overhead",
    )
    for ax in axes:
        ax.invert_yaxis()
    save(fig, "08_cost_time")
