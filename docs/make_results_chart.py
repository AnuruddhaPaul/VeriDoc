"""Figure 9.1: grouped bars built ONLY from eval/results/results_run2.json and results_heldout.json."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "eval" / "results"
OUT = ROOT / "docs" / "figures"

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e3e2dd"
SERIES = [("none", "Baseline RAG (no check)", "#2a78d6"),
          ("llm", "LLM verifier", "#eb6834"),
          ("nli", "NLI verifier", "#1baf7a")]
SETS = [("Development set\n12 + 10 questions", "results_run2.json"),
        ("Held-out set\n10 + 10 questions", "results_heldout.json")]
PANELS = [("answer_rate", "Correct answers shown to answerable questions", "higher is better"),
          ("hallucination_rate", "Answers shown to unanswerable questions", "lower is better")]

plt.rcParams["font.family"] = "DejaVu Sans"
data = {label: {s["config"]: s for s in json.load(open(RES / f))["summary"]} for label, f in SETS}

fig, axes = plt.subplots(1, 2, figsize=(8.3, 4.6), facecolor=SURFACE)
bar_w, gap = 0.24, 0.02
for ax, (key, title, hint) in zip(axes, PANELS):
    ax.set_facecolor(SURFACE)
    for gi, (label, _) in enumerate(SETS):
        for si, (cfg, _, color) in enumerate(SERIES):
            v = data[label][cfg][key] * 100
            x = gi + (si - 1) * (bar_w + gap)
            ax.bar(x, max(v, 0.0), bar_w, color=color, zorder=3, linewidth=0)
            ax.text(x, v + 2.0, f"{v:.0f}%", ha="center", va="bottom", fontsize=9, color=INK, zorder=4)
    ax.set_xticks(range(len(SETS)))
    ax.set_xticklabels([s[0] for s in SETS], fontsize=8.3, color=INK2)
    ax.set_ylim(0, 112)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels([f"{t}%" for t in [0, 25, 50, 75, 100]], fontsize=8.5, color=INK2)
    ax.grid(axis="y", color=GRID, lw=0.8, zorder=0)
    ax.tick_params(length=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.set_title(f"{title}\n({hint})", fontsize=9.5, color=INK, loc="left", pad=10)

fig.legend(handles=[Patch(color=c, label=n) for _, n, c in SERIES], loc="lower center", ncol=3,
           frameon=False, fontsize=9, labelcolor=INK)
fig.subplots_adjust(left=0.07, right=0.98, top=0.83, bottom=0.2, wspace=0.18)
fig.savefig(OUT / "fig_9_1_results.png", dpi=300, facecolor=SURFACE)
fig.savefig(OUT / "fig_9_1_results.svg", facecolor=SURFACE)
print("wrote fig_9_1_results")
