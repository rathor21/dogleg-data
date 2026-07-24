# Dogleg Data brand system — shared style constants for the chart pipeline.
#
# Ported from Fairway_vs_Rough_Post/source/style.py (release 001) for release
# 002 (Tee Shot Distance). Changes vs 001, per the 002 chart-pipeline plan:
#   - stamp() badge text carries the release slug: "DOGLEG DATA · 002 ·
#     TEE SHOT DISTANCE" instead of the plain "Dogleg Data" wordmark.
#   - SOURCE_LINE is new: the shared source-credit string for 002 charts.
#   - BG/PANEL_BG are white (site whitened chart backgrounds in the July
#     rework, see "Whiten chart backgrounds..." commit); 001 used a cream
#     BG = '#F4EDE0'.
#   - Fonts point at 001's fonts/ directory by absolute path (002 has no
#     fonts/ of its own), with the same graceful fallback to matplotlib
#     defaults if that directory isn't present at runtime.
#   - TIER_COLORS added: the seven 002 tiers (0/5/10/15/20/25/30), matching
#     the site dashboard ramp (site/fairway-vs-rough/dashboard.html:259).
#     "tour" is dropped; 002 has no tour tier.
import os
import matplotlib.font_manager as fm

# ---- Palette ----
BG        = '#FFFFFF'      # white (site whitened chart backgrounds; 001 was cream '#F4EDE0')
PANEL_BG  = '#FFFFFF'
INK       = '#1C1B18'      # primary text
SUBINK    = '#8A7F6E'      # secondary text / axis labels
FAINT     = '#B3A896'      # source lines / faint text
GRID      = '#E2D8C6'
AXIS_LINE = '#C9BFA9'

# Categorical palette (legacy 001 4-tier shorthand; kept for compatibility)
C_TOUR = '#1C1B18'   # ink
C_10   = '#5B7FA6'   # denim blue
C_20   = '#C05A36'   # baked clay
C_30   = '#7D362E'   # oxblood

# Tier color ramp for 002's seven handicap tiers, matching the site dashboard
# ramp (site/fairway-vs-rough/dashboard.html:259). "tour" dropped: 002 has no
# tour tier (see data.TIERS).
TIER_COLORS = {
    0:  '#313C47',
    5:  '#465E77',
    10: '#5B7FA6',
    15: '#8F6C6E',
    20: '#C05A36',
    25: '#9E4832',
    30: '#7D362E',
}

# ---- Brand text ----
BADGE_TEXT  = 'DOGLEG DATA · 002 · TEE SHOT DISTANCE'
SOURCE_LINE = 'Source: Shot Scope · Stagner/Arccos · Broadie · modeled values labeled'

# ---- Fonts ----
# 002 has no fonts/ dir of its own; point at 001's absolute path. Falls back
# to matplotlib defaults if that directory isn't present at runtime (e.g. a
# checkout without the sibling Golf Agent project).
_FONT_DIR = '/Users/sunny/Documents/Claude/Projects/Golf Agent/Fairway_vs_Rough_Post/source/fonts'
_HAVE_BRAND_FONTS = False
if os.path.isdir(_FONT_DIR):
    for _f in sorted(os.listdir(_FONT_DIR)):
        if _f.lower().endswith(('.ttf', '.otf')):
            try:
                fm.fontManager.addfont(os.path.join(_FONT_DIR, _f))
                _HAVE_BRAND_FONTS = True
            except Exception:
                pass

_FALLBACK = 'DejaVu Sans'
_available = {f.name for f in fm.fontManager.ttflist} if _HAVE_BRAND_FONTS else set()
# Lists give matplotlib (>=3.7) per-glyph fallback for symbols the webfont
# subsets don't cover (arrows, almost-equal, etc.).
FONT       = ['Inter', _FALLBACK] if 'Inter' in _available else _FALLBACK
TITLE_FONT = ['Fraunces', _FALLBACK] if 'Fraunces' in _available else _FALLBACK
MONO_FONT  = ['IBM Plex Mono', _FALLBACK] if 'IBM Plex Mono' in _available else _FALLBACK


def stamp(fig):
    """Draw the Dogleg Data brand badge in the bottom-right corner of a figure.

    A rounded ink strip containing a small cream dogleg mark (a vertical
    stroke bending 90 degrees right, ending in a clay dot) and the release
    badge text (BADGE_TEXT). Placed in figure fraction so it never overlaps
    axes content.
    """
    from matplotlib.patches import FancyBboxPatch
    from matplotlib.lines import Line2D

    W, H = 0.34, 0.045
    x0, y0 = 1.0 - W - 0.012, 0.008
    ax = fig.add_axes([x0, y0, W, H], zorder=50)
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # rounded ink strip
    ax.add_patch(FancyBboxPatch((0.01, 0.06), 0.98, 0.88,
                                boxstyle='round,pad=0.02,rounding_size=0.06',
                                mutation_aspect=W / H,
                                facecolor=INK, edgecolor='none',
                                transform=ax.transAxes, clip_on=False))

    # dogleg mark: vertical stroke bending 90 degrees right, clay dot at end
    ax.add_line(Line2D([0.05, 0.05, 0.085], [0.24, 0.68, 0.68],
                       color=BG, linewidth=2.2, solid_capstyle='round',
                       solid_joinstyle='round', transform=ax.transAxes,
                       clip_on=False, zorder=51))
    ax.scatter([0.098], [0.68], s=12, color=C_20, transform=ax.transAxes,
               clip_on=False, zorder=52)

    ax.text(0.15, 0.47, BADGE_TEXT, color=BG, fontsize=8.2,
            family=TITLE_FONT, va='center', ha='left',
            transform=ax.transAxes, zorder=52)
    return ax
