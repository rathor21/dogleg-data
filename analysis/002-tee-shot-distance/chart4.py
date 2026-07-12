"""Chart 4, the price of the safe club.

The categorical best-club map came out 100% driver (more distance nearly
always helps in this model), so per the plan's pre-approved pivot this chart
shows what the safe club costs instead: strokes lost hitting the 3-wood off
the tee rather than the best club (the driver), per tier and hole length.
The finding is the smallness of the numbers.

Renders outputs/chart4_club_map.png; CITE_EXPORT=1 adds the 1280x720 cite
variant.
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT_DIR = os.path.join(HERE, "outputs")
CITE_DIR = os.path.join(OUT_DIR, "cite")

import data
import style
from model import club_verdict

HOLES = np.arange(300, 481, 20)

best = {t: [club_verdict(int(h), t)["best"] for h in HOLES] for t in data.TIERS}
flat = [b for row in best.values() for b in row]
driver_share = flat.count("driver") / len(flat)
assert driver_share > 0.9, (
    f"driver share {driver_share:.2f}; the categorical map has variety, render that instead")

wood_price = np.array([
    [club_verdict(int(h), t)["scores"]["wood"] - min(club_verdict(int(h), t)["scores"].values())
     for h in HOLES]
    for t in data.TIERS
])
MAX_PRICE = float(wood_price.max())

CMAP = LinearSegmentedColormap.from_list("dogleg", ["#EDF1F6", "#5B7FA6", "#C05A36"])


def build_figure(figsize, dpi, outpath):
    plt.rcParams['font.family'] = style.FONT

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor(style.BG)
    ax.set_facecolor(style.BG)

    mesh = ax.pcolormesh(np.arange(len(HOLES) + 1), np.arange(len(data.TIERS) + 1),
                          wood_price, cmap=CMAP, vmin=0.0, vmax=max(MAX_PRICE, 0.15),
                          edgecolors=style.BG, linewidth=3.0)

    for i, t in enumerate(data.TIERS):
        for j, h in enumerate(HOLES):
            v = wood_price[i, j]
            dark = v > 0.6 * max(MAX_PRICE, 0.15)
            ax.text(j + 0.5, i + 0.5, f'{v:.2f}',
                    color=('#FFFFFF' if dark else style.INK), fontsize=10.5,
                    ha='center', va='center',
                    fontweight='bold' if v == MAX_PRICE else 'normal')

    ax.set_xticks(np.arange(len(HOLES)) + 0.5)
    ax.set_xticklabels([f'{h}' for h in HOLES], fontsize=10, color=style.SUBINK)
    ax.set_yticks(np.arange(len(data.TIERS)) + 0.5)
    ax.set_yticklabels([('scratch' if t == 0 else f'{t} hcp') + (' (modeled)' if t in data.MODELED_TIERS else '')
                        for t in data.TIERS], fontsize=10.5, color=style.INK)
    ax.invert_yaxis()  # tier 0 on top
    ax.set_xlabel('Par-4 length (yards)', color=style.SUBINK, fontsize=11)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)

    cbar = fig.colorbar(mesh, ax=ax, shrink=0.75, pad=0.02)
    cbar.set_label('Strokes lost hitting 3-wood instead of driver', color=style.SUBINK, fontsize=10)
    cbar.ax.tick_params(colors=style.SUBINK, labelsize=9)
    cbar.outline.set_visible(False)

    fig.suptitle('The 3-wood off the tee costs almost nothing, at every handicap',
                 color=style.INK, fontsize=18, fontweight='bold', x=0.055, y=0.965, ha='left',
                 fontfamily=style.TITLE_FONT)
    fig.text(0.055, 0.90,
             f'Expected strokes lost hitting 3-wood instead of the best club (the driver, in every cell '
             f'of this grid). Worst case anywhere: {MAX_PRICE:.2f} strokes. The driver is always best on '
             'average, and it is never best by much. Benchmark modeled, calibrated to published Shot Scope aggregates.',
             color=style.SUBINK, fontsize=11, va='top', wrap=True)
    fig.text(0.055, 0.03, style.SOURCE_LINE, color=style.FAINT, fontsize=9.2)

    plt.subplots_adjust(left=0.13, right=0.98, top=0.83, bottom=0.11)
    style.stamp(fig)

    fig.savefig(outpath, facecolor=style.BG)
    plt.close(fig)


if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    outpath = os.path.join(OUT_DIR, 'chart4_club_map.png')
    build_figure((13.4, 9.6), 200, outpath)
    print('saved', outpath)
    print(f'driver share {driver_share:.2f}, max wood price {MAX_PRICE:.3f}')

    if os.environ.get('CITE_EXPORT') == '1':
        os.makedirs(CITE_DIR, exist_ok=True)
        build_figure((12.8, 7.2), 100, os.path.join(CITE_DIR, 'chart4_club_map_1280x720.png'))
        print('saved cite variant')
