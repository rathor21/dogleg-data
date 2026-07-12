"""Chart 1, the headline: the cost line vs par-4 length, one line per tier.

The cost line is the minimum drive distance before a hole starts costing a
golfer more than COST_MARGIN (0.10) strokes against their own tier's typical
score (model.neutral_distance). Own-tier baseline throughout: a tier's line
never gets compared against another tier's benchmark.

Renders outputs/chart1_cost_line.png at full size, and, when CITE_EXPORT=1,
a second render at 1280x720 to outputs/cite/chart1_cost_line_1280x720.png.
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT_DIR = os.path.join(HERE, "outputs")
CITE_DIR = os.path.join(OUT_DIR, "cite")

import data
import style
from model import neutral_distance

# ---------------------------------------------------------------------------
# Data prep (exact, per the 002 chart-pipeline plan): the cost-line threshold
# for every tier across a 300-480 yd par-4 grid, imported from the model.
# ---------------------------------------------------------------------------
holes = np.arange(300, 481, 10)
series = {}
for t in data.TIERS:
    ys = []
    for h in holes:
        r = neutral_distance(int(h), t)
        ys.append(np.nan if r["threshold"] is None else r["threshold"])
    series[t] = np.array(ys, dtype=float)

# The headline annotation: the 15-handicap cost line at 400 yards, rounded to
# the nearest 5 yd. Computed from the model, never hand-typed.
ANNOTATE_HOLE = 400
ANNOTATE_TIER = 15
_ann_raw = neutral_distance(ANNOTATE_HOLE, ANNOTATE_TIER)["threshold"]
ANNOTATE_YD = int(round(_ann_raw / 5.0) * 5)

# Headline gap (0-hcp vs 30-hcp cost line at 400 yd), used in the title. Also
# computed from the model, never hand-typed.
_gap_400 = float(series[0][list(holes).index(400)] - series[30][list(holes).index(400)])
GAP_400_YD = int(round(_gap_400 / 5.0) * 5)


def tier_label(t):
    base = "0-handicap (scratch)" if t == 0 else f"{t}-handicap"
    return base + " (modeled)" if t in data.MODELED_TIERS else base


def build_figure(figsize, dpi, outpath):
    plt.rcParams['font.family'] = style.FONT

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor(style.BG)
    ax.set_facecolor(style.BG)

    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)
    for spine in ('left', 'bottom'):
        ax.spines[spine].set_color(style.AXIS_LINE)
    ax.grid(axis='y', color=style.GRID, linewidth=0.8, zorder=0)

    for t in data.TIERS:
        color = style.TIER_COLORS[t]
        ys = series[t]
        label = tier_label(t)
        if t in data.MODELED_TIERS:
            ax.plot(holes, ys, color=color, linewidth=2.4, linestyle=(0, (6, 3)),
                     label=label, zorder=4)
        else:
            ax.plot(holes, ys, color=color, linewidth=2.6, label=label, zorder=4)

    # ---- Annotation: 15-handicap at 400 yd ----
    ann_color = style.TIER_COLORS[ANNOTATE_TIER]
    ann_y_actual = float(series[ANNOTATE_TIER][list(holes).index(ANNOTATE_HOLE)])
    ax.scatter([ANNOTATE_HOLE], [ann_y_actual], color=ann_color, s=42, zorder=6,
               edgecolor='white', linewidth=1.0)
    bbox = dict(boxstyle='round,pad=0.5', facecolor=style.BG, edgecolor=ann_color,
                linewidth=1.1, alpha=0.97)
    ax.annotate(f'A 15 needs about {ANNOTATE_YD} yards here',
                xy=(ANNOTATE_HOLE, ann_y_actual),
                xytext=(ANNOTATE_HOLE - 62, ann_y_actual + 34),
                color=ann_color, fontsize=11.5, fontweight='bold', ha='left', va='bottom',
                bbox=bbox, zorder=7,
                arrowprops=dict(arrowstyle='-', color=ann_color, lw=1.2, linestyle=':'))

    ax.set_xlim(300, 480)
    ax.set_xlabel('Par-4 length (yards)', color=style.SUBINK, fontsize=12)
    ax.set_ylabel('Cost-line drive distance (yards)', color=style.SUBINK, fontsize=12)
    ax.tick_params(colors=style.SUBINK, labelsize=11)
    ax.legend(loc='lower right', frameon=False, fontsize=11, labelcolor=style.INK, ncol=2)

    fig.suptitle(
        f'Scratch golfers need about {GAP_400_YD} more yards than 30-handicaps to protect par',
        color=style.INK, fontsize=18, fontweight='bold', x=0.09, y=0.965, ha='left',
        fontfamily=style.TITLE_FONT)
    fig.text(0.09, 0.915,
              'The cost line: the drive distance where a hole starts costing more than 0.1 strokes\n'
              "against your handicap's typical score. The benchmark is modeled, calibrated to "
              'published Shot Scope averages.',
              color=style.SUBINK, fontsize=11.5, va='top')

    fig.text(0.09, 0.05,
              'No line = any reasonable drive keeps that tier within a tenth of a stroke of its own benchmark.',
              color=style.FAINT, fontsize=9.2, style='italic')
    fig.text(0.09, 0.028, style.SOURCE_LINE, color=style.FAINT, fontsize=9.2)

    plt.subplots_adjust(left=0.09, right=0.97, top=0.87, bottom=0.14)
    style.stamp(fig)

    fig.savefig(outpath, facecolor=style.BG)
    plt.close(fig)


if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    build_figure((13.4, 9.6), 200, os.path.join(OUT_DIR, 'chart1_cost_line.png'))
    print('saved', os.path.join(OUT_DIR, 'chart1_cost_line.png'))
    print('neutral_distance(400, 15)["threshold"] =', neutral_distance(400, 15)["threshold"])

    if os.environ.get('CITE_EXPORT') == '1':
        os.makedirs(CITE_DIR, exist_ok=True)
        cite_path = os.path.join(CITE_DIR, 'chart1_cost_line_1280x720.png')
        build_figure((12.8, 7.2), 100, cite_path)
        print('saved', cite_path)
