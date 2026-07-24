"""Chart 5, the quote card.

Selection rule (from the plan): the largest gap between a mid-handicap
tier's average driver distance and its cost line on a common par-4 length.
The card's number is computed here from the model, never typed.

Renders outputs/chart5_quote_card.png; CITE_EXPORT=1 adds the 1280x720 cite
variant.
"""
import os
import sys

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

# Rule 1: max headroom (tier average minus cost line) across the core tiers
# and common lengths.
candidates = []
for t in (10, 15, 20):
    for L in (360, 380, 400, 420):
        th = neutral_distance(L, t)["threshold"]
        candidates.append((data.DRIVER[t]["mean"] - th, t, L, th))
GAP, TIER, HOLE, THRESH = max(candidates)
assert GAP >= 15, f"rule 1 failed (max gap {GAP:.1f}); fall back to rule 2"

CARD_YD = int(round(THRESH / 5.0) * 5)
LEFTOVER = HOLE - CARD_YD


def build_figure(figsize, dpi, outpath):
    plt.rcParams['font.family'] = style.FONT

    fig = plt.figure(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor(style.BG)

    # thin brand rule top and bottom, quote-card idiom
    fig.add_artist(plt.Line2D([0.055, 0.945], [0.90, 0.90], color=style.INK, linewidth=2.2,
                              transform=fig.transFigure))
    fig.add_artist(plt.Line2D([0.055, 0.945], [0.115, 0.115], color=style.INK, linewidth=2.2,
                              transform=fig.transFigure))

    fig.text(0.055, 0.845, f'A {TIER}-handicap on a {HOLE}-yard par 4 needs',
             color=style.SUBINK, fontsize=21, va='top')

    fig.text(0.5, 0.52, f'{CARD_YD}', color=style.TIER_COLORS[TIER],
             fontsize=150, fontweight=900, fontfamily=style.TITLE_FONT,
             ha='center', va='center')
    fig.text(0.5, 0.335, 'yards off the tee', color=style.INK, fontsize=23,
             fontfamily=style.TITLE_FONT, fontweight='bold', ha='center', va='center')

    fig.text(0.055, 0.255,
             f'to stay within a tenth of a stroke of a typical {TIER}-handicap score, '
             f'{LEFTOVER} yards in and all.',
             color=style.INK, fontsize=15.5, va='top')
    fig.text(0.055, 0.195,
             f'That is {GAP:.0f} yards less than the tier’s average drive. '
             'Benchmark modeled, calibrated to published Shot Scope aggregates.',
             color=style.SUBINK, fontsize=11.5, va='top')

    fig.text(0.055, 0.055, style.SOURCE_LINE, color=style.FAINT, fontsize=9.2)
    style.stamp(fig)

    fig.savefig(outpath, facecolor=style.BG)
    plt.close(fig)


if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    outpath = os.path.join(OUT_DIR, 'chart5_quote_card.png')
    build_figure((13.4, 9.6), 200, outpath)
    print('saved', outpath)
    print(f'card: {TIER}-hcp, {HOLE}-yd hole, threshold {THRESH:.1f} -> {CARD_YD} yd, gap {GAP:.1f}')

    if os.environ.get('CITE_EXPORT') == '1':
        os.makedirs(CITE_DIR, exist_ok=True)
        build_figure((12.8, 7.2), 100, os.path.join(CITE_DIR, 'chart5_quote_card_1280x720.png'))
        print('saved cite variant')
