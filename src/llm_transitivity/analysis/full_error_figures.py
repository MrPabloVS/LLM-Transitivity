"""Plot directional disagreements with source labels and explicit denominators."""

import textwrap

import matplotlib.pyplot as plt
import numpy as np


def error_figures(output, summary, labels):
    models = summary["models"]
    dest = output / "figures"
    indexed = {r["model"]: r for r in summary["totals"]}
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), layout="constrained")
    for ax, metric, count, denominator, title, color in zip(
        axes,
        ["fpr", "fnr"],
        ["fp", "fn"],
        ["negative_answered", "positive_answered"],
        [
            "False positives / interpreted negatives",
            "False negatives / interpreted positives",
        ],
        ["#D55E00", "#6A51A3"],
        strict=True,
    ):
        values = [indexed[m][metric] for m in models]
        ax.barh(
            [labels[m] for m in models],
            [0 if v is None else 100 * v for v in values],
            color=color,
        )
        for i, m in enumerate(models):
            r = indexed[m]
            label = (
                f"{r[count]:,}/{r[denominator]:,} ("
                + (f"{100 * r[metric]:.2f}%" if r[metric] is not None else "undefined")
                + ")"
            )
            ax.text(
                (100 * r[metric] if r[metric] is not None else 0) + 1,
                i,
                label,
                va="center",
                fontsize=8,
            )
        ax.set(
            xlim=(0, 100),
            xlabel="Percent of interpretable responses in the source class",
            title=title,
        )
        ax.invert_yaxis()
    fig.suptitle(
        "Direction of disagreement: yes is positive; source labels are not audited truth"
    )
    save(fig, dest / "false_rates")
    files = {}
    for dimension, records in summary["breakdowns"].items():
        conditions = sorted({r["condition"] for r in records})
        lookup = {(r["model"], r["condition"]): r for r in records}
        files[dimension] = []
        for start in range(0, len(conditions), 18):
            subset = conditions[start : start + 18]
            name = f"false_rates_{dimension}_{start // 18 + 1}"
            fig, axes = plt.subplots(
                1,
                2,
                figsize=(17, max(4.8, 2.7 + len(subset) * 0.52)),
                layout="constrained",
            )
            for ax, metric, count, denom, title in zip(
                axes,
                ["fpr", "fnr"],
                ["fp", "fn"],
                ["negative_answered", "positive_answered"],
                ["FPR: FP / interpreted negatives", "FNR: FN / interpreted positives"],
                strict=True,
            ):
                values = np.array(
                    [
                        [
                            np.nan
                            if lookup[m, c][metric] is None
                            else lookup[m, c][metric] * 100
                            for m in models
                        ]
                        for c in subset
                    ]
                )
                palette = plt.get_cmap("YlOrRd").copy()
                palette.set_bad("#e0e0e0")
                heat = ax.imshow(values, vmin=0, vmax=100, cmap=palette, aspect="auto")
                ax.set(
                    xticks=range(len(models)),
                    xticklabels=[
                        "\n".join(textwrap.wrap(labels[m], 14)) for m in models
                    ],
                    yticks=range(len(subset)),
                    yticklabels=["\n".join(textwrap.wrap(str(c), 32)) for c in subset],
                    title=title,
                )
                ax.tick_params(axis="both", length=0, labelsize=7)
                for i, c in enumerate(subset):
                    for j, m in enumerate(models):
                        r = lookup[m, c]
                        value = (
                            "undefined"
                            if r[metric] is None
                            else f"{100 * r[metric]:.1f}%"
                        ) + f"\n{r[count]:,}/{r[denom]:,}"
                        ax.text(
                            j,
                            i,
                            value,
                            ha="center",
                            va="center",
                            fontsize=6.5,
                            color="white" if values[i, j] > 60 else "black",
                        )
                fig.colorbar(heat, ax=ax, shrink=0.7, label="Percent")
            fig.suptitle(f"{dimension}: source-label error rates (gray = undefined)")
            save(fig, dest / name)
            files[dimension].append(name)
    return files


def save(fig, path):
    fig.savefig(path.with_suffix(".svg"), metadata={"Date": None}, bbox_inches="tight")
    fig.savefig(path.with_suffix(".png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
