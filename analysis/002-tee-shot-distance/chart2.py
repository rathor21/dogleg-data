"""Chart 2, the flat zone: expected score vs drive distance, 400-yd par 4,
one panel per tier (5/10/15/20), the audience core.

Each panel shows the expected-score curve as drive distance varies at a
fixed hole length, with the tier benchmark and cost-line margin marked, the
cost-line drive distance dropped to the axis, and the within-margin zone
shaded: every drive distance where the hole costs no more than a tenth of a
stroke against the tier's own number. The shading starts at the cost line by
construction, which is the chart's point.

Renders outputs/chart2_flat_zone.png at full size, and, when CITE_EXPORT=1,
a second render at 1280x720 to outputs/cite/chart2_flat_zone_1280x720.png.
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
from model import expected_score, benchmark_score, neutral_distance

# ---------------------------------------------------------------------------
# Data prep (exact, per the 002 chart-pipeline plan).
# ---------------------------------------------------------------------------
HOLE_YARDS = 400
drives = np.arange(150, 311, 5)
TIERS4 = [5, 10, 15, 20]
curves = {t: np.array([expected_score(HOLE_YARDS, t, "driver", drive_mean=float(d)) for d in drives]) for t in TIERS4}
benches = {t: benchmark_score(HOLE_YARDS, t) for t in TIERS4}
lines = {t: neutral_distance(HOLE_YARDS, t)["threshold"] for t in TIERS4}

# ---------------------------------------------------------------------------
# Sanity guard: the cost line must sit below the tier's average drive for
# every tier shown (the release's finding). If this fails, the chart would
# visually contradict the data it's built from; print and stop.
# ---------------------------------------------------------------------------
for t in TIERS4:
    tier_avg = data.DRIVER[t]["mean"]
    if lines[t] is None or lines[t] >= tier_avg:
        print(f"SANITY FAIL tier {t}: cost line {lines[t]} vs tier average drive {tier_avg:.1f}")
        raise SystemExit(1)


def build_figure(figsize, dpi, outpath):
    plt.rcParams['font.family'] = style.FONT

    fig, axes = plt.subplots(2, 2, figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor(style.BG)
    axes = axes.ravel()

    for ax, t in zip(axes, TIERS4):
        color = style.TIER_COLORS[t]
        ys = curves[t]
        ax.set_facecolor(style.BG)
        for spine in ('top', 'right'):
            ax.spines[spine].set_visible(False)
        for spine in ('left', 'bottom'):
            ax.spines[spine].set_color(style.AXIS_LINE)
        ax.grid(axis='y', color=style.GRID, linewidth=0.7, zorder=0)

        ax.plot(drives, ys, color=color, linewidth=2.6, zorder=4)

        bench = benches[t]
        thresh = lines[t]

        # within-margin shading: drives where the hole costs <= 0.10 vs the benchmark
        in_zone = ys <= bench + data.COST_MARGIN
        ax.fill_between(drives, ys.min() - 0.3, ys.max() + 0.3,
                         where=in_zone, color=color, alpha=0.10, zorder=1)

        # benchmark line (dashed) and cost-margin line (dotted)
        ax.axhline(bench, color=style.SUBINK, linewidth=1.2, linestyle=(0, (6, 3)), zorder=3)
        ax.axhline(bench + data.COST_MARGIN, color=style.SUBINK, linewidth=1.2, linestyle=(0, (1, 2)), zorder=3)

        ax.text(drives[0] + 3, bench - 0.05, 'benchmark', color=style.SUBINK, fontsize=9,
                va='top', ha='left')
        ax.text(drives[0] + 3, bench + data.COST_MARGIN + 0.05, '+0.10 (cost line margin)',
                color=style.SUBINK, fontsize=9, va='bottom', ha='left')

        # dotted vertical drop from the cost-line crossing to the x axis
        if thresh is not None:
            y_at_thresh = bench + data.COST_MARGIN
            ax.plot([thresh, thresh], [y_at_thresh, ys.max() + 0.35], color=color,
                     linewidth=1.1, linestyle=(0, (1, 2)), zorder=3)
            ax.text(thresh, ys.max() + 0.38, f'{thresh:.0f} yd', color=color, fontsize=9.5,
                    fontweight='bold', ha='center', va='bottom')

        # tier average drive marker
        tier_avg = data.DRIVER[t]["mean"]
        avg_score = float(np.interp(tier_avg, drives, ys))
        ax.scatter([tier_avg], [avg_score], color=color, s=38, zorder=6,
                   edgecolor='white', linewidth=1.0)
        ax.annotate('tier average', xy=(tier_avg, avg_score),
                    xytext=(tier_avg + 12, avg_score + 0.18),
                    color=color, fontsize=9, ha='left', va='bottom',
                    arrowprops=dict(arrowstyle='-', color=color, lw=0.8, linestyle=':'))

        ax.set_ylim(ys.min() - 0.15, ys.max() + 0.55)
        ax.set_xlim(150, 310)
        ax.tick_params(colors=style.SUBINK, labelsize=9.5)
        ax.set_title(f'{t}-handicap', color=style.INK, fontsize=13.5, fontweight='bold',
                     fontfamily=style.TITLE_FONT, loc='left')

    for ax in axes[2:]:
        ax.set_xlabel('Drive distance (yards)', color=style.SUBINK, fontsize=10.5)
    for ax in (axes[0], axes[2]):
        ax.set_ylabel('Expected strokes, 400-yd par 4', color=style.SUBINK, fontsize=10.5)

    fig.suptitle('Past the cost line, extra yards buy almost nothing',
                 color=style.INK, fontsize=18, fontweight='bold', x=0.055, y=0.975, ha='left',
                 fontfamily=style.TITLE_FONT)
    fig.text(0.055, 0.925,
              'Expected strokes on a 400-yd par 4 as drive distance varies, own-tier dispersion held fixed. The '
              'benchmark is modeled, calibrated to published Shot Scope aggregates.',
              color=style.SUBINK, fontsize=11, va='top')

    fig.text(0.055, 0.028, style.SOURCE_LINE, color=style.FAINT, fontsize=9.2)

    plt.subplots_adjust(left=0.075, right=0.965, top=0.86, bottom=0.125, hspace=0.42, wspace=0.24)
    style.stamp(fig)

    fig.savefig(outpath, facecolor=style.BG)
    plt.close(fig)


if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    outpath = os.path.join(OUT_DIR, 'chart2_flat_zone.png')
    build_figure((13.4, 9.6), 200, outpath)
    print('saved', outpath)
    for t in TIERS4:
        print(f'tier {t}: cost line {lines[t]:.1f} yd, tier average drive '
              f'{data.DRIVER[t]["mean"]:.1f} yd, headroom {data.DRIVER[t]["mean"] - lines[t]:.1f} yd')

    if os.environ.get('CITE_EXPORT') == '1':
        os.makedirs(CITE_DIR, exist_ok=True)
        cite_path = os.path.join(CITE_DIR, 'chart2_flat_zone_1280x720.png')
        build_figure((12.8, 7.2), 100, cite_path)
        print('saved', cite_path)
