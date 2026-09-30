"""Draws the architecture diagrams (Figures 6.1, 6.2, 7.1) as SVG + 300 dpi PNG into docs/figures/.

Colour language (same in every figure):
  blue = data / storage   green = LLM call   orange = verification / check
  grey = user / UI        red  = abstain / refuse exit
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

OUT = Path(__file__).parent / "figures"
OUT.mkdir(exist_ok=True)

PAL = {
    "blue": ("#DCEBFA", "#2B6CB0"),
    "green": ("#DDF3E4", "#2F855A"),
    "orange": ("#FDE9CF", "#C05621"),
    "grey": ("#E9ECEF", "#4A5568"),
    "red": ("#FCE0E0", "#C53030"),
    "white": ("#FFFFFF", "#2D3748"),
}
FONT = "DejaVu Sans"
plt.rcParams["font.family"] = FONT


def canvas(w, h, xlim, ylim):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("auto")
    ax.axis("off")
    fig.subplots_adjust(0.01, 0.01, 0.99, 0.99)
    return fig, ax


def box(ax, x, y, w, h, text, kind="white", fs=10, bold=False, lw=1.6):
    fc, ec = PAL[kind]
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=fc, ec=ec, lw=lw, zorder=3))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal",
            color="#1A202C", zorder=4, linespacing=1.25)
    return (x, y, w, h)


def diamond(ax, x, y, w, h, text, kind="orange", fs=9.5):
    fc, ec = PAL[kind]
    ax.add_patch(Polygon([(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)], closed=True,
                         fc=fc, ec=ec, lw=1.6, zorder=3))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color="#1A202C", zorder=4, linespacing=1.2)
    return (x, y, w, h)


def cylinder(ax, x, y, w, h, text, kind="blue", fs=10):
    fc, ec = PAL[kind]
    e = h * 0.22
    ax.add_patch(Rectangle((x - w / 2, y - h / 2 + e / 2), w, h - e, fc=fc, ec="none", zorder=3))
    ax.plot([x - w / 2] * 2, [y - h / 2 + e / 2, y + h / 2 - e / 2], color=ec, lw=1.6, zorder=4)
    ax.plot([x + w / 2] * 2, [y - h / 2 + e / 2, y + h / 2 - e / 2], color=ec, lw=1.6, zorder=4)
    ax.add_patch(Ellipse((x, y - h / 2 + e / 2), w, e, fc=fc, ec=ec, lw=1.6, zorder=3))
    ax.add_patch(Ellipse((x, y + h / 2 - e / 2), w, e, fc=fc, ec=ec, lw=1.6, zorder=5))
    ax.text(x, y - 0.05, text, ha="center", va="center", fontsize=fs, color="#1A202C", zorder=6, linespacing=1.25)


def arrow(ax, p, q, label="", color="#2D3748", rad=0.0, lpos=0.5, dx=0.0, dy=0.0, fs=8.5, lw=1.5, ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=13, color=color, lw=lw, ls=ls,
                                 connectionstyle=f"arc3,rad={rad}", zorder=2, shrinkA=0, shrinkB=0))
    if label:
        lx, ly = p[0] + (q[0] - p[0]) * lpos + dx, p[1] + (q[1] - p[1]) * lpos + dy
        ax.text(lx, ly, label, fontsize=fs, ha="center", va="center", color=color, zorder=6,
                bbox=dict(fc="white", ec="none", pad=1.2))


def legend(ax, x, y, items, fs=8.5, dy=0.42):
    for i, (kind, label) in enumerate(items):
        fc, ec = PAL[kind]
        ax.add_patch(FancyBboxPatch((x, y - i * dy), 0.36, 0.26, boxstyle="round,pad=0.01,rounding_size=0.06",
                                    fc=fc, ec=ec, lw=1.3))
        ax.text(x + 0.5, y - i * dy + 0.13, label, fontsize=fs, va="center", color="#1A202C")


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", dpi=300, facecolor="white")
    fig.savefig(OUT / f"{name}.svg", facecolor="white")
    plt.close(fig)
    print("wrote", name)


# ------------------------------------------------------------------ Figure 6.1
def fig_architecture():
    fig, ax = canvas(8.3, 12.6, (0, 8.3), (-1.9, 11.6))

    ax.text(1.55, 11.3, "INGESTION (once per PDF)", ha="center", fontsize=10.5, fontweight="bold", color=PAL["blue"][1])
    ax.text(5.25, 11.3, "QUERY (every question)", ha="center", fontsize=10.5, fontweight="bold", color="#2D3748")

    # ingestion lane (left column)
    ix = 1.55
    box(ax, ix, 10.3, 2.4, 0.75, "PDF upload", "blue")
    box(ax, ix, 8.95, 2.4, 0.85, "PyMuPDF parser\n(text per page)", "blue")
    box(ax, ix, 7.5, 2.5, 1.05, "Sentence chunker\n~350 tokens, overlap,\npage number kept", "blue", fs=9.5)
    box(ax, ix, 5.95, 2.5, 0.95, "MiniLM embedder\nall-MiniLM-L6-v2", "blue")
    cylinder(ax, ix, 4.3, 2.2, 1.35, "ChromaDB\n(cosine)")
    for a, b in [(9.92, 9.38), (8.52, 8.03), (6.97, 6.43), (5.47, 5.0)]:
        arrow(ax, (ix, a), (ix, b))

    # query lane (middle column)
    qx = 5.25
    box(ax, qx, 10.3, 2.5, 0.75, "User question", "grey")
    box(ax, qx, 9.15, 2.5, 0.7, "Embed question", "blue")
    box(ax, qx, 8.0, 2.5, 0.7, "Retrieve top-k chunks", "blue")
    diamond(ax, qx, 6.55, 2.7, 1.35, "Best similarity\n≥ cutoff?")
    box(ax, qx, 4.85, 3.2, 1.1, "Generator (Groq LLM)\nanswers from sources only,\ncites [n]", "green", fs=9.5)
    diamond(ax, qx, 3.35, 2.7, 1.25, "Model said\nNOT_FOUND?")
    box(ax, qx, 2.0, 3.2, 0.9, "Grounding verifier\n(LLM or NLI)", "orange")
    box(ax, qx, 0.85, 2.2, 0.6, "Decision", "orange", bold=True)
    arrow(ax, (qx, 9.92), (qx, 9.5))
    arrow(ax, (qx, 8.8), (qx, 8.35))
    arrow(ax, (qx, 7.65), (qx, 7.23))
    arrow(ax, (qx, 5.88), (qx, 5.4), "Yes", dx=0.3)
    arrow(ax, (qx, 4.3), (qx, 3.98))
    arrow(ax, (qx, 2.72), (qx, 2.45), "No", dx=0.3, dy=0.03)
    arrow(ax, (qx, 1.55), (qx, 1.15))

    # ChromaDB -> retrieve (elbow)
    ax.plot([ix + 1.1, 3.0, 3.0], [4.3, 4.3, 8.0], color="#2D3748", lw=1.5, zorder=2)
    arrow(ax, (3.0, 8.0), (qx - 1.25, 8.0), "search", dy=0.22)
    # embedder note: question is embedded with the same model
    

    # red exits (right column)
    rx = 7.4
    box(ax, rx, 6.55, 1.75, 1.05, "Not found\n(no LLM call)", "red", fs=9)
    arrow(ax, (qx + 1.35, 6.55), (rx - 0.7, 6.55), "No", color=PAL["red"][1], dy=0.2)
    box(ax, rx, 3.35, 1.4, 0.8, "Not found", "red", fs=9)
    arrow(ax, (qx + 1.35, 3.35), (rx - 0.7, 3.35), "Yes", color=PAL["red"][1], dy=0.2)

    # outcomes + UI
    ys = -0.75
    outs = [(1.05, "Grounded", "green"), (3.15, "Partial\n(flag weak claims)", "orange"),
            (5.3, "Ungrounded\n(withhold answer)", "red"), (7.3, "Unverified\n(verifier failed)", "orange")]
    for x, t, k in outs:
        box(ax, x, ys + 0.55, 1.9, 0.75, t, k, fs=8.8)
        arrow(ax, (qx + (x - qx) * 0.3, 0.55), (x, ys + 0.93), color="#4A5568", lw=1.2, rad=0.0)
    box(ax, 4.15, -1.55, 7.6, 0.45, "Streamlit UI: badge, claim-by-claim supported / unsupported, highlighted evidence", "grey", fs=9)
    for x, _, _ in outs:
        arrow(ax, (x, ys + 0.17), (x, -1.32), color="#4A5568", lw=1.1)

    legend(ax, 0.2, 2.75, [("blue", "Data / storage"), ("green", "LLM call"), ("orange", "Check / decision"),
                           ("grey", "User / UI"), ("red", "Abstain / refuse")])
    save(fig, "fig_6_1_architecture")


# ------------------------------------------------------------------ Figure 6.2
def fig_decision():
    fig, ax = canvas(8.3, 9.0, (0, 8.3), (-0.6, 8.4))
    ax.text(2.0, 8.05, "Checks, in order", ha="center", fontsize=10.5, fontweight="bold")
    ax.text(6.65, 8.05, "Final status", ha="center", fontsize=10.5, fontweight="bold")

    cx = 2.0
    steps = [(7.15, "Best chunk\nsimilarity <\nMIN_SIMILARITY?"), (5.65, "Model reply\n= NOT_FOUND?"),
             (4.25, "Grounding\nswitched off?"), (2.9, "Verifier crashed\nor bad JSON?")]
    for y, t in steps:
        diamond(ax, cx, y, 2.9, 1.15, t, fs=9)
    box(ax, cx, 1.35, 2.9, 0.95, "Count supported\nclaims (k of n)", "orange", fs=9.5)
    box(ax, cx, 7.9 - 0.02, 0.01, 0.01, "", "white", lw=0)
    for (y1, _), (y2, _) in zip(steps[:-1], steps[1:]):
        arrow(ax, (cx, y1 - 0.58), (cx, y2 + 0.58), "no", dx=0.3, fs=8)
    arrow(ax, (cx, steps[-1][0] - 0.58), (cx, 1.83), "no", dx=0.3, fs=8)

    sx = 6.65
    status = [
        (7.15, "not_found", "no LLM call, answer:\n“Not found in the document”", "red"),
        (5.65, "not_found", "model itself abstained", "red"),
        (4.25, "unchecked", "baseline RAG, answer shown\nwithout any check", "grey"),
        (2.9, "unverified", "fail closed: shown with a\nwarning, never “grounded”", "orange"),
        (1.95, "grounded", "k = n: every claim supported", "green"),
        (1.0, "partial", "0 < k < n: weak claims flagged", "orange"),
        (0.15, "ungrounded", "k = 0: answer withheld,\ndraft behind an expander", "red"),
    ]
    for y, name, note, kind in status:
        box(ax, sx, y, 2.9, 0.78, f"{name}\n{note}", kind, fs=8.2)
    for y, *_ in status[:4]:
        arrow(ax, (cx + 1.45, y), (sx - 1.45, y), "yes", fs=8)
    for y, lab in [(1.95, "k = n"), (1.0, "0 < k < n"), (0.15, "k = 0")]:
        arrow(ax, (cx + 1.45, 1.35), (sx - 1.45, y), lab, fs=8, lpos=0.45)
    ax.text(0.25, -0.3, "Red = abstain, orange = flagged or warned,\ngreen = fully supported, grey = unchecked.",
            fontsize=8, va="bottom", color="#4A5568")
    save(fig, "fig_6_2_decision")


# ------------------------------------------------------------------ Figure 7.1
def fig_verifier():
    fig, ax = canvas(8.3, 8.2, (0, 8.3), (-0.7, 7.5))
    cols = {"Pipeline": 1.0, "Verifier LLM\n(Groq, JSON mode)": 3.2, "quote_in_text()\n(plain Python)": 5.35, "Verdict": 7.3}
    kinds = ["grey", "green", "orange", "white"]
    for (name, x), k in zip(cols.items(), kinds):
        box(ax, x, 6.95, 1.7, 0.7, name, k, fs=8.8)
        ax.plot([x, x], [6.6, 0.0], color="#A0AEC0", lw=1.1, ls=(0, (4, 3)), zorder=1)
    x0, x1, x2, x3 = cols.values()
    ax.add_patch(Rectangle((x1 + 0.3, 0.2), x3 - x1 + 0.1, 2.85, fc="#FFF7E6", ec=PAL["orange"][1], lw=2, ls="--", zorder=0))
    ax.text(x1 + 0.45, 2.85, "SAFEGUARD: the verifier cannot just assert support", fontsize=8.8,
            color=PAL["orange"][1], fontweight="bold", va="center")

    arrow(ax, (x0, 6.0), (x1, 6.0), "1  answer + numbered sources", dy=0.25, fs=8.4)
    ax.text(x1 + 0.15, 5.3, "2  split the answer into atomic claims", fontsize=8.4, va="center")
    arrow(ax, (x1, 4.55), (x0, 4.55), "3  JSON: claim, supported,\nsource, quote", dy=0.36, fs=8.4)
    arrow(ax, (x0, 3.5), (x2, 3.5), "4  for each supported claim: cited chunk + quote", dy=0.25, fs=8.4)
    ax.text(x2 + 0.15, 2.3, "5  is the quote verbatim in the\ncited chunk? (normalised)", fontsize=8.4, va="center")
    arrow(ax, (x2, 1.6), (x3, 1.6), "yes: claim stays\nsupported", color=PAL["green"][1], dy=0.36, fs=8.4)
    arrow(ax, (x2, 0.85), (x3, 0.85), "no: demoted to\nunsupported", color=PAL["red"][1], dy=-0.36, fs=8.4)
    ax.text(0.3, -0.4, "6  supported / total decides grounded, partial or ungrounded (Figure 6.2)", fontsize=8.4)
    save(fig, "fig_7_1_verifier_sequence")


if __name__ == "__main__":
    fig_architecture()
    fig_decision()
    fig_verifier()
