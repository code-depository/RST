"""
generate_figure4.py
Figure 4 for the letter: minimization pipeline overview and method
comparison, replacing Table 1 (categorical content, now rendered as a
figure per the letter's figures-over-tables preference).

Corrects two overclaims present in an earlier hand-drawn version of
this figure:
    - RST's scalability beyond n=10 is achieved via greedy reduct mode,
      whose quality is empirically consistent with exact reducts at
      n<=10 (84/84 instances, module_8.py) but UNVERIFIED at the n=16
      scale where greedy mode is actually required (Scalability Limits section).
      Labeling this flatly "High" alongside Espresso's would overstate
      what has actually been checked.
    - "Scalable Minimization" (implying minimization quality scales)
      is replaced with "Scalable Reduct Search" -- what scales is
      finding the reduct, not a guarantee on minimization quality.

No numeric computation is performed here; this figure is a schematic/
categorical summary of results established elsewhere (module_4.py's
run_benchmark output pattern across Figures 1-3, and module_8.py's
84/84 greedy-quality finding), not a new experiment.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D


def draw_box(ax, x, y, w, h, text, facecolor, fontsize=13, fontweight="bold", textcolor="black"):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.02",
                          facecolor=facecolor, edgecolor="black", linewidth=1.3, zorder=2)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
             fontsize=fontsize, fontweight=fontweight, color=textcolor, zorder=3)
    return box


def draw_arrow(ax, xy_start, xy_end, color="black"):
    arrow = FancyArrowPatch(xy_start, xy_end, arrowstyle="-|>", mutation_scale=16,
                             linewidth=1.4, color=color, zorder=1)
    ax.add_patch(arrow)


def generate_figure4(path):
    fig = plt.figure(figsize=(11, 9))

    # ---------------- Top panel: pipeline diagram ----------------
    ax1 = fig.add_axes([0.03, 0.60, 0.94, 0.36])
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 4)
    ax1.axis("off")

    draw_box(ax1, 0.2, 1.5, 1.8, 1.2, "Input\nBoolean\nFunction", "#AFCBE8", fontsize=12)

    method_boxes = [
        (3.0, 2.7, "QMC", "#E8A33D", ["Exact minimization", "Limited scalability"]),
        (3.0, 1.5, "Espresso", "#B49BD8", ["Heuristic minimization", "Scalable optimization"]),
        (3.0, 0.3, "RST", "#8FBF6E", ["Minimal reducts", "Scalable reduct search*"]),
    ]
    for bx, by, label, color, bullets in method_boxes:
        draw_box(ax1, bx, by, 1.8, 1.0, label, color, fontsize=13)
        for i, b in enumerate(bullets):
            ax1.text(bx + 2.0, by + 0.72 - i * 0.42, f"\u2022 {b}", fontsize=10, va="center")
        draw_arrow(ax1, (2.0, 2.1), (bx, by + 0.5))

    draw_box(ax1, 8.1, 1.5, 1.7, 1.2, "Optimized\nCircuit", "#E8B93D", fontsize=12)
    for bx, by, *_ in method_boxes:
        draw_arrow(ax1, (bx + 1.8, by + 0.5), (8.1, 2.1))

    ax1.text(5.0, 3.85, "Figure 4a. Minimization pipeline: three methods applied to the same input.",
              ha="center", fontsize=10.5, style="italic")

    # ---------------- Bottom panel: comparison table ----------------
    ax2 = fig.add_axes([0.03, 0.03, 0.94, 0.52])
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 5.4)
    ax2.axis("off")

    headers = ["Minimizer", "Minimum-cost\ncover", "Scalability\nbeyond n \u2248 10",
               "Variable\nredundancy", "Gate count\noutput"]
    col_x = [0.1, 2.0, 4.1, 6.2, 8.1]
    col_w = [1.7, 1.9, 1.9, 1.7, 1.8]

    header_y = 4.7
    for cx, cw, h in zip(col_x, col_w, headers):
        ax2.text(cx + cw / 2, header_y, h, ha="center", va="center", fontsize=10.5, fontweight="bold")
    ax2.add_line(Line2D([0, 10], [4.35, 4.35], color="black", linewidth=1.2))

    rows = [
        ("QMC", "#4472C4", ["Exact", "Limited", "No report", "Exact minimum"]),
        ("Espresso", "#B49BD8", ["Heuristic", "High", "No report", "Empirical match with RST"]),
        ("RST", "#70AD47", ["Exact / greedy", "High (greedy,\nunverified quality*)",
                             "Minimal reduct", "Empirical match with Espresso"]),
    ]
    row_h = 1.15
    row_top = 4.15
    for i, (name, color, cells) in enumerate(rows):
        ry = row_top - i * row_h
        draw_box(ax2, col_x[0], ry - row_h + 0.15, col_w[0], row_h - 0.3, name, color,
                 fontsize=11, textcolor="white")
        for j, cell_text in enumerate(cells):
            ax2.text(col_x[j + 1] + col_w[j + 1] / 2, ry - row_h / 2 + 0.075, cell_text,
                      ha="center", va="center", fontsize=9.5)
        if i < len(rows) - 1:
            ax2.add_line(Line2D([0, 10], [ry - row_h + 0.15, ry - row_h + 0.15],
                                 color="#cccccc", linewidth=0.8))

    ax2.text(0.0, 0.55,
             "* Greedy-mode reduct quality matches the exact minimum in 84/84 tested instances at\n"
             "n \u2264 10; at n = 16, global minimality is unverified, but irredundancy (no single\n"
             "variable removable) is confirmed for tested outputs (see\n"
             "Scalability Limits for the n = 12 exact verified case).",
             fontsize=8.7, style="italic", va="top")

    ax2.text(5.0, 5.15, "Figure 4b. Capability comparison: QMC, Espresso, and RST.",
              ha="center", fontsize=10.5, style="italic")

    fig.suptitle("Figure 4. Minimization pipeline and method comparison", fontsize=13, y=0.985)
    fig.savefig(path, dpi=200, format="jpg", bbox_inches="tight")
    plt.close(fig)
    return path


if __name__ == "__main__":
    out = generate_figure4("figure4_method_comparison.jpg")
    print(f"Figure 4 written: {out}")
