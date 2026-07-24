"""Chart 3, the decomposition: where the cost of a shorter tee shot lives.

Two panels, tier 15 on a 400-yd par 4 (Sunny's 220-drive/180-in example):

Left: strokes lost vs tier-average driving as the drive gets shorter, same
club. In this model, as in the published Shot Scope accuracy table, a
shorter drive with the same club does not buy fairways (lateral dispersion
is set by the club and tier, not the carry), so the whole cost is the longer
approach. The script asserts the frozen-lie decomposition confirms this.

Right: the club trade, at the tier's average driver distance. Each club's
net cost vs driver splits into the approach cost of the shorter position
(frozen lie mix) and the accuracy gain of the tighter club (the remainder).

Renders outputs/chart3_decomposition.png; CITE_EXPORT=1 adds the 1280x720
cite variant.
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
from model import expected_score, tee_outcomes, strokes_to_holeout

TIER = 15
HOLE_YARDS = 400
DRIVES = [180, 200, 220, 240, 260]
CLUBS = ["wood", "hybrid", "iron"]

BASE = expected_score(HOLE_YARDS, TIER)
TIER_AVG = data.DRIVER[TIER]["mean"]

# ---------------------------------------------------------------------------
# Frozen-lie score: carries and weights from the candidate swing, lie mix
# from tier-average driver. Isolates the leftover-distance (approach) effect.
# ---------------------------------------------------------------------------
_, _, LIES_DRIVER_AVG = tee_outcomes("driver", TIER)

def frozen_lie_score(club, drive_mean=None):
    carries, weights, _ = tee_outcomes(club, TIER, drive_mean)
    total = 1.0
    for carry, w, lp in zip(carries, weights, LIES_DRIVER_AVG):
        leftover = max(HOLE_YARDS - carry, data.LEFTOVER_FLOOR_YD)
        e_fair = strokes_to_holeout(leftover, "fairway", TIER)
        e_rough = strokes_to_holeout(leftover, "rough", TIER)
        total += w * (lp["fairway"] * e_fair + lp["rough"] * e_rough
                      + lp["trouble"] * (e_rough + data.TROUBLE_COST[TIER]))
    return total

# Panel A data: same club, shorter drives. Assert the lie component is zero
# (same-club dispersion does not depend on carry in this model), so the whole
# delta is approach.
drive_deltas = []
for d in DRIVES:
    total = expected_score(HOLE_YARDS, TIER, "driver", drive_mean=float(d)) - BASE
    approach = frozen_lie_score("driver", float(d)) - BASE
    assert abs(total - approach) < 1e-9, (d, total, approach)
    drive_deltas.append(total)

# Panel B data: club trade at tier-average driver distance.
club_rows = []
for club in CLUBS:
    total = expected_score(HOLE_YARDS, TIER, club) - BASE
    approach = frozen_lie_score(club) - BASE
    lie = total - approach
    assert abs(approach + lie - total) < 1e-9
    club_rows.append((club, total, approach, lie))

COLOR = style.TIER_COLORS[TIER]
MUTED = "#8A7F6E"  # saddle, the secondary segment


def build_figure(figsize, dpi, outpath):
    plt.rcParams['font.family'] = style.FONT

    fig, (axA, axB) = plt.subplots(1, 2, figsize=figsize, dpi=dpi)
    fig.patch.set_facecolor(style.BG)

    for ax in (axA, axB):
        ax.set_facecolor(style.BG)
        for spine in ('top', 'right'):
            ax.spines[spine].set_visible(False)
        for spine in ('left', 'bottom'):
            ax.spines[spine].set_color(style.AXIS_LINE)
        ax.grid(axis='x', color=style.GRID, linewidth=0.7, zorder=0)
        ax.axvline(0, color=style.SUBINK, linewidth=1.0, zorder=2)
        ax.tick_params(colors=style.SUBINK, labelsize=9.5)

    # ---- Panel A: shorter drives, same club ----
    ypos = np.arange(len(DRIVES))[::-1]
    axA.barh(ypos, drive_deltas, height=0.62, color=COLOR, zorder=3)
    axA.set_xlim(min(drive_deltas) - 0.07, max(drive_deltas) + 0.07)
    for y, d, v in zip(ypos, DRIVES, drive_deltas):
        ha = 'left' if v >= 0 else 'right'
        off = 0.01 if v >= 0 else -0.01
        axA.text(v + off, y, f'{v:+.2f}', color=style.INK, fontsize=10,
                 va='center', ha=ha, fontweight='bold')
    axA.set_yticks(ypos)
    axA.set_yticklabels([f'{d} yd drive' for d in DRIVES], fontsize=10.5, color=style.INK)
    axA.set_xlabel('Strokes vs your tier benchmark (400-yd par 4)', color=style.SUBINK, fontsize=10.5)
    axA.set_title('Shorter drive, same club: the whole cost is the approach',
                  color=style.INK, fontsize=12.5, fontweight='bold',
                  fontfamily=style.TITLE_FONT, loc='left', pad=12)

    i220 = DRIVES.index(220)
    axA.annotate('220 off the tee leaves 180 in.\nThe approach is where the stroke goes.',
                 xy=(drive_deltas[i220], ypos[i220]),
                 xytext=(max(drive_deltas) * 0.55, ypos[i220] - 1.15),
                 color=style.INK, fontsize=10,
                 arrowprops=dict(arrowstyle='-', color=style.SUBINK, lw=0.9, linestyle=':'),
                 va='top', ha='left',
                 bbox=dict(boxstyle='round,pad=0.4', facecolor=style.BG,
                           edgecolor=style.AXIS_LINE, linewidth=0.8))

    # ---- Panel B: the club trade at tier-average driver distance ----
    yposB = np.arange(len(club_rows))[::-1]
    BARW = 0.30
    for y, (club, total, approach, lie) in zip(yposB, club_rows):
        axB.barh(y + BARW / 2 + 0.03, approach, height=BARW, color=MUTED, zorder=3,
                 label='If accuracy did not improve (approach cost alone)' if y == yposB[0] else None)
        axB.barh(y - BARW / 2 - 0.03, total, height=BARW, color=COLOR, zorder=3,
                 label='Actual net cost vs driver' if y == yposB[0] else None)
        axB.text(approach + 0.008, y + BARW / 2 + 0.03, f'+{approach:.2f}', color=MUTED,
                 fontsize=9.5, va='center', ha='left')
        axB.text(total + 0.008, y - BARW / 2 - 0.03, f'{total:+.2f}', color=style.INK,
                 fontsize=10, va='center', ha='left', fontweight='bold')
    axB.set_xlim(0, max(a for _, _, a, _ in club_rows) + 0.09)
    axB.set_yticks(yposB)
    axB.set_yticklabels([data.CLUBS[c]["label"] for c, *_ in club_rows], fontsize=10.5, color=style.INK)
    axB.set_xlabel('Strokes vs hitting driver (400-yd par 4)', color=style.SUBINK, fontsize=10.5)
    axB.set_title('Shorter club: accuracy pays back part of the approach cost',
                  color=style.INK, fontsize=12.5, fontweight='bold',
                  fontfamily=style.TITLE_FONT, loc='left', pad=12)
    axB.legend(loc='upper right', bbox_to_anchor=(1.0, 1.02), fontsize=9,
               frameon=False, labelcolor=style.INK)

    fig.suptitle('The price of a shorter tee shot is paid at the approach',
                 color=style.INK, fontsize=18, fontweight='bold', x=0.055, y=0.97, ha='left',
                 fontfamily=style.TITLE_FONT)
    fig.text(0.055, 0.905,
             f'15-handicap, 400-yd par 4, vs the tier average drive of {TIER_AVG:.0f} yd. Lie mix frozen at the '
             'tier-average driver mix to isolate the approach effect; with the same club, a shorter drive buys no '
             'fairways (published accuracy is nearly flat), so accuracy only enters when the club changes. '
             'Benchmark modeled, calibrated to published Shot Scope aggregates.',
             color=style.SUBINK, fontsize=10.5, va='top', wrap=True)

    fig.text(0.055, 0.03, style.SOURCE_LINE, color=style.FAINT, fontsize=9.2)

    plt.subplots_adjust(left=0.13, right=0.965, top=0.80, bottom=0.14, wspace=0.32)
    style.stamp(fig)

    fig.savefig(outpath, facecolor=style.BG)
    plt.close(fig)


if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    outpath = os.path.join(OUT_DIR, 'chart3_decomposition.png')
    build_figure((13.4, 9.6), 200, outpath)
    print('saved', outpath)
    print('drive deltas:', {d: round(v, 3) for d, v in zip(DRIVES, drive_deltas)})
    for club, total, approach, lie in club_rows:
        print(f'{club}: net {total:+.3f} = approach {approach:+.3f} + lie {lie:+.3f}')

    if os.environ.get('CITE_EXPORT') == '1':
        os.makedirs(CITE_DIR, exist_ok=True)
        build_figure((12.8, 7.2), 100, os.path.join(CITE_DIR, 'chart3_decomposition_1280x720.png'))
        print('saved cite variant')
