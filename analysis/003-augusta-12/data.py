"""Gate-verified anchors for release 003 (Augusta 12 aim-point piece), amateur side.

EVERY numeric literal in this file comes from docs/sources/003_Source_Log.md.
Anchor numbers (1..6) cite that log's sections. Values marked MODELED are
derivations or assumptions built on published anchors; each carries a comment
saying what was assumed and, where the log states one, a sensitivity range
for peer review. Nothing here was typed from memory.

Vocabulary (CONTEXT.md, binding): dispersion oval, aim point, sucker pin,
short-sided. This module builds the raw per-tier inputs to the dispersion
oval; model.py performs the anisotropy split and hole-geometry placement.

Where an anchor did not resolve at the resolution this release needs (no
published lateral coordinates for hole 12's hazards, no pin-specific green
depth beyond the center pin's "narrowest middle" figure), this file says so
in the comment next to the value rather than presenting an interpretive
choice as if it were sourced.
"""

from math import log, pi, sqrt

TIERS = [0, 5, 10, 15, 20]  # scratch, 5, 10, 15, 20-handicap; matches 002's tier-0-is-scratch convention

# ---------------------------------------------------------------------------
# Anchor 3: the 12th hole's tee yardage. ANCHORED, consistent across every
# source fetched in the hunt (PGA.com, golfguidebook.com, others).
# ---------------------------------------------------------------------------

TEE_SHOT_YD = 155.0

# ---------------------------------------------------------------------------
# Anchor 1: approach proximity and GIR-by-distance, ~150-160 yd.
#
# GIR50_DISTANCE_YD: PUBLISHED (Source 2, Arccos "magic number" table) for
#   all five tiers directly: the yardage at which each tier hits 50% of
#   greens. scratch 165, 5-hcp 147, 10-hcp 129, 15-hcp 110, 20-hcp 92.
#
# PROXIMITY_10_ANCHOR_FT / GIR_10_ANCHOR_PCT: PUBLISHED (Source 1/3, Arccos
#   and Shot Scope, directly quoted text), a matched pair for the 10-handicap
#   tier from the 125-149 yd band (midpoint ~137 yd): 62 ft average proximity,
#   43% GIR. This is the one tier with BOTH a proximity figure and a GIR% at
#   the SAME distance band, so it is the only tier that can self-calibrate an
#   implied "effective green radius" without borrowing an unpublished number.
#
# Inversion (mirrors 002's fairway-hit% -> sd_lat probability inversion):
#   1. Rayleigh mean relation, isotropic 2D Gaussian miss: E[R] = sigma*sqrt(pi/2).
#      62 ft -> sigma_10_at_137 ~= 49.5 ft.
#   2. GIR is P(within a circular green of radius R): 1 - exp(-R^2/2*sigma^2).
#      Solving at 43% with sigma_10_at_137 gives an implied green radius
#      R ~= 52.4 ft (~17.5 yd) -- MODELED: this treats the Shot Scope/Arccos
#      "found the green" statistic as if every green in their pooled sample
#      were this one effective circular size. It is a calibration artifact of
#      this inversion, not a claim about Augusta 12's own green (that green's
#      size is handled separately, as a range, in HOLE below).
#   3. sigma scales ~linearly with shot distance for a fixed tier (same
#      distance-proportional dispersion assumption 002 uses via sd_dist_frac):
#      sigma(D) = k_tier * D. For the 10-handicap, k_10 = sigma_10_at_137/137,
#      read directly off its own matched pair. For every other tier, the
#      only anchor is GIR50_DISTANCE_YD (50% GIR by definition), and at
#      exactly 50% GIR, sigma = R/sqrt(2*ln(2)) is a fixed constant (call it
#      SIGMA_HALF_FT; an algebraic consequence of P=50% and a shared R, not a
#      separate assumption), so k_tier = SIGMA_HALF_FT / GIR50_DISTANCE_YD[tier].
#
# ANCHORED vs MODELED split (per the log's own gate verdict language): for
#   scratch/5/10-handicap, GIR50_DISTANCE_YD sits within 26 yd of the 155-yd
#   shot ("brackets... for the low-handicap tiers... 5 and 10-handicap sit
#   inside it" -- log, Anchor 1), so scaling k_tier up to 155 yd is a short,
#   trustworthy extrapolation, and the 10-handicap has the direct matched-pair
#   treatment on top. For 15/20-handicap, GIR50_DISTANCE_YD sits 45-63 yd
#   short of 155 yd -- the log's own words: "a below-average-odds shot for
#   them specifically" -- so the same formula's output is labeled MODELED
#   (interpolated/extrapolated across a materially longer gap), not ANCHORED.
#   The computation is identical for every tier; only the confidence label
#   differs, and it differs because the log itself says so.
# ---------------------------------------------------------------------------

GIR50_DISTANCE_YD = {0: 165.0, 5: 147.0, 10: 129.0, 15: 110.0, 20: 92.0}  # ANCHORED, Anchor 1 Source 2

PROXIMITY_10_ANCHOR_FT = 62.0        # ANCHORED, Anchor 1 Source 1/3
GIR_10_ANCHOR_PCT = 0.43             # ANCHORED, Anchor 1 Source 1/3
PROXIMITY_10_ANCHOR_BAND_MID_YD = 137.0  # midpoint of the published 125-149 yd band

PROXIMITY_ANCHORED_TIERS = [0, 5, 10]  # GIR50 distance within 26 yd of the 155-yd shot, or a direct matched pair
PROXIMITY_MODELED_TIERS = [15, 20]     # GIR50 distance 45-63 yd short of the 155-yd shot; log: "below-average-odds shot"


def _rayleigh_sigma_from_mean(mean_ft):
    """Isotropic radial sigma (ft) implied by a mean radial miss distance,
    via the Rayleigh-distribution relation E[R] = sigma * sqrt(pi/2)."""
    return mean_ft / sqrt(pi / 2.0)


def _green_radius_from_sigma_gir(sigma_ft, gir_pct):
    """Effective circular green radius (ft) implied by a GIR% at a known
    sigma, from P(within R) = 1 - exp(-R^2 / (2*sigma^2))."""
    return sigma_ft * sqrt(-2.0 * log(1.0 - gir_pct))


_SIGMA_10_AT_BAND_FT = _rayleigh_sigma_from_mean(PROXIMITY_10_ANCHOR_FT)  # ~49.5 ft
GREEN_RADIUS_FT = _green_radius_from_sigma_gir(_SIGMA_10_AT_BAND_FT, GIR_10_ANCHOR_PCT)  # ~52.4 ft; MODELED calibration artifact, see docstring above
_K_10_PER_YD = _SIGMA_10_AT_BAND_FT / PROXIMITY_10_ANCHOR_BAND_MID_YD  # ~0.361 ft/yd
SIGMA_HALF_FT = GREEN_RADIUS_FT / sqrt(2.0 * log(2.0))  # implied sigma at any tier's own 50%-GIR distance


def sigma_isotropic_ft(tier, shot_yd=TEE_SHOT_YD):
    """Isotropic radial miss sigma (ft) for tier, scaled to shot_yd yards.

    tier 10 uses its own directly-anchored per-yard rate (_K_10_PER_YD); every
    other tier scales SIGMA_HALF_FT by shot_yd / that tier's own GIR50 distance
    (Anchor 1, Source 2). See the module-level comment above for the full
    derivation and the ANCHORED/MODELED split.
    """
    if tier not in TIERS:
        raise KeyError(f"unknown tier {tier!r}; expected one of {TIERS}")
    k = _K_10_PER_YD if tier == 10 else SIGMA_HALF_FT / GIR50_DISTANCE_YD[tier]
    return k * shot_yd


SIGMA_ISO_FT = {t: sigma_isotropic_ft(t) for t in TIERS}  # at the 155-yd tee shot
PROXIMITY_FT = {t: SIGMA_ISO_FT[t] * sqrt(pi / 2.0) for t in TIERS}  # mean radial miss (ft) at 155 yd, Rayleigh mean

# ---------------------------------------------------------------------------
# Anchor 2: distance-vs-line anisotropy. MODELED for the 100-160 yd approach
# band (Broadie's numeric ~3:1 ratio is measured on 20-60 yd short game and
# 0-50 yd sand shots, not approach irons; the 100-150 yd ellipses in the same
# paper are described only qualitatively). Sensitivity range 2:1 to 3.5:1,
# floored below the published short-game ratio and capped at its upper bound.
# ---------------------------------------------------------------------------

ANISOTROPY = {"ratio": 3.0, "range": (2.0, 3.5)}

# ---------------------------------------------------------------------------
# Anchor 3: hole geometry. Yardage, bunker count/position, diagonal shoe-sole
# orientation, and the Sunday-pin depth offset are ANCHORED. Green width and
# depth are PUBLISHED but not reconcilable across four disagreeing sources
# (16-35 yd wide, 9-33 yd deep depending on section and source) -- carried as
# ranges, never a single confident figure, per the log's own verdict.
#
# front_third_depth_yd_range is the log's best-corroborated single figure:
# golfguidebook.com's "9 yards deep" at the "narrowest middle pin," which
# this release assigns to the CENTER pin below -- that is the exact section
# the source names, and it is also this release's demonstration pin for
# CONTEXT.md's sucker-pin definition (fair for scratch, marginal for 15).
# ---------------------------------------------------------------------------

HOLE = {
    "tee_yards": TEE_SHOT_YD,                        # ANCHORED, Anchor 3
    "green_width_yd_range": (16.0, 35.0),             # PUBLISHED range, not reconcilable to one figure; Anchor 3
    "green_depth_yd_range": (20.0, 33.0),             # PUBLISHED range, overall diagonal depth; Anchor 3
    "front_third_depth_yd_range": (9.0, 12.0),        # PUBLISHED range, center-pin/"narrowest middle pin" section; Anchor 3
    "bunkers": {"front": 1, "back": 2},               # ANCHORED, Anchor 3 (NBC Sports/Golf Channel + The Fried Egg)
    "creek_note": "short of the green, fed by a shaved bank off the front bunker",  # ANCHORED narrative, Anchor 3
    # Lateral hazard bands and bunker depths below have NO published numeric
    # coordinate anywhere in the source hunt -- Anchor 3 confirms bunker
    # COUNT and general SIDE ("front bunker on left side" per one source, a
    # minor cross-source disagreement the log notes but does not resolve) but
    # no yardage-from-centerline figure exists for any hazard on this hole.
    # MODELED placements, kept narrow enough to sit inside the green-width
    # range above; sensitivity untested beyond the tests in this package.
    "front_bunker_x_range": (-10.0, 2.0),             # MODELED, left-of-center per the one source with a side call
    "front_bunker_depth_yd": 6.0,                     # MODELED, no published bunker depth
    "back_bunker_x_ranges": [(-15.0, -8.0), (6.0, 13.0)],  # MODELED, two bands either side of center for the two ANCHORED back bunkers
    "back_bunker_depth_yd": 6.0,                      # MODELED
}

# ---------------------------------------------------------------------------
# Anchor 3: the three pin positions. y = distance from tee (yd), x = lateral
# offset from the hole's centerline (yd, positive = right / Sunday side).
#
# CENTER's y is the ANCHORED 155-yd tee yardage, treated as the officially
# quoted reference distance. SUNDAY's y is CENTER's front-pin sibling plus
# the ANCHORED "roughly 15 yards deeper" offset (Anchor 3). LEFT's y (half
# that offset short of center) and every x lateral coordinate are MODELED:
# no source in the hunt publishes a lateral yardage for any pin on this hole,
# only the qualitative shape ("diagonal, shoe-sole, shallow right / deep
# left"). front_frac/back_frac split each pin's local green depth budget
# into the share sitting short of / long of the hole, used by model.py to
# decide which misses are short-sided (CONTEXT.md definition); MODELED, no
# numeric anchor, chosen to match the qualitative description that a front
# pin has little green in front of it and a back pin has little green behind.
# local_depth_yd_range is MODELED for left/sunday (no published figure for
# those specific sections); center reuses HOLE["front_third_depth_yd_range"].
# ---------------------------------------------------------------------------

PINS = {
    "left": {
        "label": "Front-left",
        "y": TEE_SHOT_YD - 7.5,       # MODELED: half the ANCHORED 15-yd Sunday offset, short of center
        "x": -6.0,                    # MODELED, no published lateral coordinate
        "front_frac": 0.15,
        "back_frac": 0.85,
        "local_depth_yd_range": (12.0, 16.0),  # MODELED
    },
    "center": {
        "label": "Center",
        "y": TEE_SHOT_YD,              # ANCHORED, Anchor 3
        "x": 0.0,
        "front_frac": 0.5,
        "back_frac": 0.5,
        "local_depth_yd_range": None,  # resolved from HOLE["front_third_depth_yd_range"] by model.py
    },
    "sunday": {
        "label": "Sunday (back right)",
        "y": TEE_SHOT_YD - 7.5 + 15.0,  # ANCHORED offset (+15 yd) on a MODELED base (left's y); Anchor 3
        "x": 9.0,                       # MODELED, no published lateral coordinate
        "front_frac": 0.85,
        "back_frac": 0.15,
        "local_depth_yd_range": (10.0, 14.0),  # MODELED, tight back corner per Anchor 3's "azalea-lined ledge"
    },
}

# ---------------------------------------------------------------------------
# Anchor 6: wind. Narrative anchor only (2019's ~20 mph gusts, SI.com's "up
# to a four-club differential"), not a numeric model input. carry_penalty_yd
# and dispersion_inflation are both MODELED with stated sensitivity ranges;
# no source publishes a wind-yardage or wind-dispersion coefficient for this
# hole or for amateur approach shots generally.
# ---------------------------------------------------------------------------

WIND = {
    "carry_penalty_yd": 8.0, "carry_penalty_range_yd": (4.0, 12.0),
    "dispersion_inflation": 1.3, "dispersion_inflation_range": (1.15, 1.5),
}

# ---------------------------------------------------------------------------
# Anchor 5: short-game/recovery pricing.
#
# THREE_PUTT_RATE: ANCHORED at 5/15/25-handicap (Shot Scope, direct fetch,
#   text-quoted "holes per three-putt": 16.7 / 9.7 / 7.6, converted to a
#   per-hole rate). 0/10/20 have no direct anchor; filled by least-squares
#   line through the three published points (same standing rule 002 uses for
#   its tier-30 extrapolation), MODELED for those three tiers only.
#
# UP_AND_DOWN_PCT: MODELED. The log flags this whole table as WebSearch-
#   synthesis-only -- GolfWRX and MyGolfSpy both returned HTTP 403 on direct
#   fetch, so the numbers were never independently confirmed against readable
#   source text this session (Anchor 5's own verdict: "usable for a
#   sensitivity range or narrative color, not for a chart claiming a specific
#   published figure"). Kept as the release's working recovery-pricing input
#   with that caveat carried in SOURCES below, since no better anchor exists.
# ---------------------------------------------------------------------------

_THREE_PUTT_RATE_PUB = {5: 1.0 / 16.7, 15: 1.0 / 9.7, 25: 1.0 / 7.6}  # ANCHORED, Anchor 5
_THREE_PUTT_PUB_TIERS = sorted(_THREE_PUTT_RATE_PUB)


def _lsq_line(xs, ys):
    """Ordinary least-squares line through (xs, ys); returns (intercept, slope)."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    return my - slope * mx, slope


def _lsq_at(xs, ys, x):
    """Value of the least-squares line through (xs, ys), evaluated at x."""
    b, m = _lsq_line(xs, ys)
    return b + m * x


THREE_PUTT_RATE = {
    t: (_THREE_PUTT_RATE_PUB[t] if t in _THREE_PUTT_RATE_PUB
        else _lsq_at(_THREE_PUTT_PUB_TIERS, [_THREE_PUTT_RATE_PUB[p] for p in _THREE_PUTT_PUB_TIERS], t))
    for t in TIERS
}

UP_AND_DOWN_PCT = {0: 0.54, 5: 0.50, 10: 0.40, 15: 0.35, 20: 0.30}  # MODELED, weakly-sourced; Anchor 5

ROUGH_RECOVERY_EASE = 1.05    # MODELED: a non-sand recovery is a bit easier than a bunker shot; no anchor
MISSED_UP_AND_DOWN_STROKES = 3.3  # MODELED average strokes after a failed up-and-down; sensitivity range (3.0, 3.6)
SHORT_SIDE_PENALTY = 1.2      # MODELED multiplier on the recovery leg for a short-sided miss (CONTEXT.md definition)
CREEK_PENALTY_STROKES = 1.0   # MODELED: standard drop-and-replay convention for a water hazard, same spirit as 002's OB_COST; not itself a source-log anchor

# Anchor 3: the two back bunkers sit "cut into an azalea-lined ledge" (NBC
# Sports/Golf Channel, corroborated by The Fried Egg) -- ANCHORED qualitative
# description of real trouble behind the green, not open rough. A miss that
# clears the back bunkers by a wide margin is realistically in that ledge
# (pine straw, azalea roots, a severe drop), not a plain chip-and-putt lie.
# Neither figure below is published anywhere in the source hunt; both are
# MODELED, kept as a further discount on the already-MODELED UP_AND_DOWN_PCT
# rather than a new invented base rate, with a stated sensitivity range.
LONG_TROUBLE_BUFFER_YD = 6.0          # MODELED: extra carry past the back bunkers before a miss counts as "in the ledge" rather than merely long of the green; matches back_bunker_depth_yd's own scale
LONG_TROUBLE_UPDOWN_MULT = 0.55       # MODELED discount vs. plain rough's up-and-down odds
LONG_TROUBLE_UPDOWN_MULT_RANGE = (0.4, 0.7)

# ---------------------------------------------------------------------------
# SOURCES: one row per exported anchor group; log fragments point at the
# anchor sections of docs/sources/003_Source_Log.md.
# ---------------------------------------------------------------------------

SOURCES = {
    "GIR50_DISTANCE_YD": {"log": "docs/sources/003_Source_Log.md#anchor-1", "status": "published, all five tiers"},
    "PROXIMITY_10_ANCHOR_FT": {"log": "docs/sources/003_Source_Log.md#anchor-1", "status": "published"},
    "SIGMA_ISO_FT": {"log": "docs/sources/003_Source_Log.md#anchor-1", "status": "computed-from-published for 0/5/10 (anchored); modeled/interpolated for 15/20"},
    "ANISOTROPY": {"log": "docs/sources/003_Source_Log.md#anchor-2", "status": "modeled; sensitivity range 2:1 to 3.5:1"},
    "HOLE": {"log": "docs/sources/003_Source_Log.md#anchor-3", "status": "yardage/bunker-count/orientation anchored; width/depth/hazard-lateral-position modeled ranges"},
    "PINS": {"log": "docs/sources/003_Source_Log.md#anchor-3", "status": "center yardage and sunday depth offset anchored; lateral coordinates and left/sunday local depth modeled"},
    "WIND": {"log": "docs/sources/003_Source_Log.md#anchor-6", "status": "narrative anchor only; carry penalty and dispersion inflation modeled"},
    "THREE_PUTT_RATE": {"log": "docs/sources/003_Source_Log.md#anchor-5", "status": "published at 5/15/25; modeled (lsq) at 0/10/20"},
    "UP_AND_DOWN_PCT": {"log": "docs/sources/003_Source_Log.md#anchor-5", "status": "modeled, weakly-sourced (websearch synthesis, direct fetch failed 403)"},
}
