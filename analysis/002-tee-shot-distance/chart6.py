"""Chart 6, the bailout threshold.

For a 400-yard par 4, the excess out-of-bounds rate p* at which the driver
stops beating an alternative club (wood or hybrid) off the tee: the OB rate,
over and above whatever the alternative club itself carries, that makes the
driver's expected score (with OB_COST strokes charged per OB drive) equal the
alternative club's expected score. model.bailout_threshold computes p* per
tier; this chart renders it as grouped horizontal bars, one group per tier.

Renders outputs/chart6_bailout.png; CITE_EXPORT=1 adds the 1280x720 cite
variant.
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
from model import bailout_threshold

HOLE_YARDS = 400
ALT_CLUBS = ("wood", "hybrid")
ALT_COLORS = {"wood": "#5B7FA6", "hybrid": "#C05A36"}  # denim / baked clay

# p* per tier per alt club. bailout_threshold returns None when the alt club
# already beats the driver outright; none of the published tiers hit that at
# 400 yd (absent OB risk the driver's extra distance always pays),
# but the chart tolerates it (bar simply omitted, annotated "n/a").
THRESHOLDS = {
    club: {t: bailout_threshold(HOLE_YARDS, t, club) for t in data.TIERS}
    for club in ALT_CLUBS
}

# Headline verdict number: the wood's threshold at tier 15, expressed as
# "one extra OB every N driver holes." Computed here, never hand-typed.
_T15_WOOD = THRESHOLDS["wood"][15]
assert _T15_WOOD is not None and _T15_WOOD > 0
N_HOLES_T15 = round(1.0 / _T15_WOOD)

TITLE = (
    f'The 3-wood only pays off once you lose an extra ball every '
    f'{N_HOLES_T15} driver holes'
)


def tier_label(t):
    base = 'Scratch' if t == 0 else f'{t} hcp'
    return base + (' (modeled)' if t in data.MODELED_TIERS else '')


def build_figure(figsize, dpi, outpath):
    plt.rcParams['font.family'] = style.FONT

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor(style.BG)
    ax.set_facecolor(style.BG)

    for spine in ('top', 'right'):
        ax.spines[spine].set_visible(False)
    for spine in ('left', 'bottom'):
        ax.spines[spine].set_color(style.AXIS_LINE)
    ax.grid(axis='x', color=style.GRID, linewidth=0.8, zorder=0)

    tiers = data.TIERS
    n_tiers = len(tiers)
    bar_h = 0.34
    y_base = np.arange(n_tiers)[::-1]  # tier 0 at top

    for j, club in enumerate(ALT_CLUBS):
        offset = (0.5 - j) * (bar_h + 0.03)
        ys = y_base + offset
        vals = [100.0 * (THRESHOLDS[club][t] or 0.0) for t in tiers]
        bars = ax.barh(ys, vals, height=bar_h, color=ALT_COLORS[club],
                        label=data.CLUBS[club]["label"], zorder=3)
        for y, t, v in zip(ys, tiers, vals):
            p = THRESHOLDS[club][t]
            label = f'{v:.1f}%' if p is not None else 'n/a'
            ax.text(v + 0.18, y, label, color=style.INK, fontsize=9.5,
                    va='center', ha='left', zorder=4)
            if club == 'wood' and p is not None:
                n = round(1.0 / p)
                ax.text(v + 1.55, y, f'≈ 1 extra OB / {n} driver holes',
                        color=style.SUBINK, fontsize=8.6, va='center', ha='left',
                        style='italic', zorder=4)

    ax.set_yticks(y_base)
    ax.set_yticklabels([tier_label(t) for t in tiers], fontsize=11, color=style.INK)
    ax.set_xlabel('Excess OB rate that justifies switching off driver (%)',
                   color=style.SUBINK, fontsize=11.5)
    ax.set_xlim(0, 13.5)
    ax.tick_params(colors=style.SUBINK, labelsize=10.5)
    ax.legend(loc='lower right', frameon=False, fontsize=11, labelcolor=style.INK)

    fig.suptitle(TITLE, color=style.INK, fontsize=17.5, fontweight='bold',
                 x=0.055, y=0.965, ha='left', fontfamily=style.TITLE_FONT)
    fig.text(0.055, 0.905,
             f'A {HOLE_YARDS}-yard par 4. Each bar is the extra out-of-bounds rate, over the wood or '
             'hybrid’s own OB risk, that makes the driver’s expected score worse than switching. '
             'OB is modeled at 2.0 strokes (stroke and distance); benchmark modeled, calibrated to '
             'published Shot Scope aggregates.',
             color=style.SUBINK, fontsize=10.5, va='top', wrap=True)
    fig.text(0.055, 0.03, style.SOURCE_LINE, color=style.FAINT, fontsize=9.2)

    plt.subplots_adjust(left=0.14, right=0.97, top=0.84, bottom=0.17)
    style.stamp(fig)

    fig.savefig(outpath, facecolor=style.BG)
    plt.close(fig)


if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    outpath = os.path.join(OUT_DIR, 'chart6_bailout.png')
    build_figure((13.4, 9.6), 200, outpath)
    print('saved', outpath)
    print(f'title: {TITLE}')
    for club in ALT_CLUBS:
        for t in data.TIERS:
            p = THRESHOLDS[club][t]
            if p is None:
                print(f'{club:>6} tier {t:>2}: n/a (alt club already beats driver)')
            else:
                n = round(1.0 / p)
                print(f'{club:>6} tier {t:>2}: p*={p:.4f} ({p*100:.2f}%), 1 extra OB / {n} holes')

    if os.environ.get('CITE_EXPORT') == '1':
        os.makedirs(CITE_DIR, exist_ok=True)
        build_figure((12.8, 7.2), 100, os.path.join(CITE_DIR, 'chart6_bailout_1280x720.png'))
        print('saved cite variant')
