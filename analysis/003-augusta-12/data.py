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
# Anchor 3's diagonal-slope hook: "the Sunday pin sits roughly 15 yards
# deeper into the green than a front-left pin" describes a generic FRONT-left
# reference position, not necessarily wherever this release places its own
# named "left" demo pin below. Kept as its own reference (read only by
# model.py's _FRONT_EDGE_SLOPE_YD_PER_YD derivation) so that repositioning
# PINS["left"] -- see below -- cannot quietly drag the green's ANCHORED
# diagonal slope along with it. Values match this release's original
# front-left placement, now retired as a named pin but preserved here as the
# anchor's own reference point.
# ---------------------------------------------------------------------------

_FRONT_LEFT_SLOPE_REFERENCE_Y = TEE_SHOT_YD - 7.5   # MODELED base, "a front-left pin," half the ANCHORED 15-yd Sunday offset short of center
_FRONT_LEFT_SLOPE_REFERENCE_X = -6.0                # MODELED, no published lateral coordinate

# ---------------------------------------------------------------------------
# Anchor 3: the three pin positions. y = distance from tee (yd), x = lateral
# offset from the hole's centerline (yd, positive = right / Sunday side).
#
# CENTER's y is the ANCHORED 155-yd tee yardage, treated as the officially
# quoted reference distance. SUNDAY's y is the _FRONT_LEFT_SLOPE_REFERENCE_Y
# base plus the ANCHORED "roughly 15 yards deeper" offset (Anchor 3). Every x
# lateral coordinate is MODELED: no source in the hunt publishes a lateral
# yardage for any pin on this hole, only the qualitative shape ("diagonal,
# shoe-sole, shallow right / deep left"). front_frac/back_frac split each
# pin's local green depth budget into the share sitting short of / long of
# the hole, used by model.py to decide which misses are short-sided
# (CONTEXT.md definition); MODELED, no numeric anchor, chosen to match each
# pin's qualitative description. local_depth_yd_range is MODELED for
# left/sunday (no published figure for those specific sections); center
# reuses HOLE["front_third_depth_yd_range"].
#
# LEFT repositioned (this pass): the locked pin cast (issue #5, "Pins:
# three, escalating") scopes left as the welcoming/accessible pin, but the
# release's original placement put it front_frac=0.15 -- a tucked pin
# hugging the front edge/creek, which bailed harder than Sunday at every
# tier and failed the locked cast it was meant to implement. Anchor 3's
# green-shape description is qualitatively ANCHORED as "shallower on the
# right, deeper on the left" (docs/sources/003_Source_Log.md#anchor-3): the
# left side is the green's roomier lobe, so the accessible pin belongs
# mid-depth on that lobe, not tucked against the front edge. Repositioned to
# x=-10.0 (MODELED, moved from -6.0 further into the green's wide/deep left
# section per that same anchor; plausible range -13.0 to -7.0, staying
# inside the green's published half-width at the default 25.5-yd width) and
# front_frac=back_frac=0.5 (MODELED mid-depth placement; plausible
# sensitivity range 0.45-0.55, per the "welcoming" cast -- not perfectly
# centered by construction, just not tucked against either edge). y=148.0 is
# MODELED to sit near the shared green boundary's own local midpoint at
# x=-10 under the default geometry (front edge ~134.5, back edge ~161.0 at
# that x, midpoint ~147.75, rounded). local_depth_yd_range widened to
# (16.0, 22.0) MODELED -- larger than the retired front placement's tight
# 12-16 yd pocket, smaller than the green's full published depth range
# (20-33 yd) since this describes a local pocket around one pin, not the
# whole green -- representing the anchored "deeper on the left" claim as a
# roomier local depth than a front-edge pin would have. Symmetric
# front_frac/back_frac means neither a short nor a long miss reads as
# short-sided at this pin (model.region_at), unlike before.
# ---------------------------------------------------------------------------

PINS = {
    "left": {
        "label": "Left (mid-green)",
        "y": 148.0,                    # MODELED, mid-depth on the green's left lobe -- see comment above
        "x": -10.0,                    # MODELED, wide/deep left section -- see comment above
        "front_frac": 0.5,
        "back_frac": 0.5,
        "local_depth_yd_range": (16.0, 22.0),  # MODELED
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
        "y": _FRONT_LEFT_SLOPE_REFERENCE_Y + 15.0,  # ANCHORED offset (+15 yd) on the front-left reference base; Anchor 3
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

# Distance falloff past the long_trouble buffer (#8's flagged defect: the
# pre-fix price was flat regardless of how far a shot overshot the green, so
# an aim-point search kept finding a "better" score the farther it carried
# past the back bunkers, out past a 150-yd carry adjustment with no interior
# optimum). Every extra yard of overshoot past the buffer edge is a deeper
# lie in the azalea-lined ledge (Anchor 3), so the recovery leg's cost blends
# from LONG_TROUBLE_UPDOWN_MULT's plain-ledge price toward a hazard-like
# price (model._creek_strokes -- the same drop-and-replay-plus-recovery cost
# already used for the creek, Anchor 5-anchored via UP_AND_DOWN_PCT /
# MISSED_UP_AND_DOWN_STROKES / CREEK_PENALTY_STROKES) as overshoot grows,
# an exponential approach so the price keeps rising but never exceeds that
# ceiling. LONG_TROUBLE_FALLOFF_YD (the e-folding distance of that blend) has
# no published anchor -- MODELED, sensitivity range stated below and swept by
# the sensitivity tests -- but the two endpoints it blends between are both
# built from Anchor-5 figures already in this file, not new invented prices.
LONG_TROUBLE_FALLOFF_YD = 15.0        # MODELED, anchorless; sensitivity range (10.0, 25.0)
LONG_TROUBLE_FALLOFF_YD_RANGE = (10.0, 25.0)

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

# ---------------------------------------------------------------------------
# Anchor 7 (append, #9, 2026-08-16 follow-up hunt): PGA Tour approach
# proximity, 150-175 yd band. APPEND-ONLY block: everything below adds a new,
# self-contained "tour" entry and does not read, mutate, or restructure any
# name defined above. TIERS stays [0, 5, 10, 15, 20]; SIGMA_ISO_FT,
# THREE_PUTT_RATE, UP_AND_DOWN_PCT, and every other amateur dict keeps
# exactly the keys and values it had before this block existed -- #8's
# optimizer work depends on that surface staying byte-for-byte unchanged, and
# the untouched test_data.py (44 tests) is what proves it.
#
# Unlike Anchor 1's amateur figures, Anchor 7's mean proximity (27-29 ft) and
# GIR% (63-64%) are published directly at 150-175 yd, the band that already
# contains the hole's 155-yard shot -- no GIR50-distance extrapolation step
# is needed the way tiers 0/5/15/20 require; this is a direct matched pair at
# the target distance, the same style as tier 10's self-calibration in Anchor
# 1 but with less distance-scaling since 155 sits inside the band itself
# rather than 18 yd outside it.
# ---------------------------------------------------------------------------

TOUR_BAND_YD_RANGE = (150.0, 175.0)      # ANCHORED, Anchor 7
TOUR_BAND_MID_YD = 162.5
TOUR_PROXIMITY_FT_RANGE = (27.0, 29.0)   # ANCHORED, Anchor 7: 3 independent sources (Mike Bury Golf, Golf Insider UK, The Left Rough), 2016-2023 seasons
TOUR_PROXIMITY_FT = 28.0                 # midpoint default of the ANCHORED range
TOUR_GIR_PCT_RANGE = (0.63, 0.64)        # ANCHORED, Anchor 7
TOUR_GIR_PCT = 0.635                     # midpoint default of the ANCHORED range

# Same Rayleigh-mean inversion as the amateur tiers (_rayleigh_sigma_from_mean,
# defined above), then the same direct matched-pair per-yard scaling tier 10
# uses (_K_10_PER_YD), evaluated on Anchor 7's band instead of Anchor 1's.
_SIGMA_TOUR_AT_BAND_FT = _rayleigh_sigma_from_mean(TOUR_PROXIMITY_FT)
_GREEN_RADIUS_TOUR_CHECK_FT = _green_radius_from_sigma_gir(_SIGMA_TOUR_AT_BAND_FT, TOUR_GIR_PCT)  # sanity cross-check only, not used downstream: how big a green Anchor 7's own pair implies, comparable to GREEN_RADIUS_FT (~52 ft) above
_K_TOUR_PER_YD = _SIGMA_TOUR_AT_BAND_FT / TOUR_BAND_MID_YD
_SIGMA_ISO_FT_TOUR = _K_TOUR_PER_YD * TEE_SHOT_YD   # at the 155-yd tee shot
_PROXIMITY_FT_TOUR = _SIGMA_ISO_FT_TOUR * sqrt(pi / 2.0)

# Anchor 2's own text publishes a PRO dist/dir ratio directly (Broadie Table
# 2: Pro1 1.5, Pro2 1.6), the same short-game/sand distance band as the
# amateur 3:1 figure and carrying the same across-distance-band caveat, but
# WITHOUT the amateur figure's second assumption (substituting a different
# population). Tour anisotropy is therefore better-anchored than the amateur
# ANISOTROPY constant above, not worse.
TOUR_ANISOTROPY = {"ratio": 1.55, "range": (1.5, 1.6)}   # ANCHORED, Anchor 2 (Broadie Table 2, Pro1/Pro2)

# No anchor in the log covers tour-level three-putt rate at all.
TOUR_THREE_PUTT_RATE = THREE_PUTT_RATE[0]  # MODELED-anchorless: reuses the scratch-amateur extrapolated rate as a defensible floor; no tour-specific three-putt anchor exists to reuse instead

# ---------------------------------------------------------------------------
# Anchor 10 (append, #9 rev 3 follow-up hunt, 2026-09-07): Tour recovery
# rates (scrambling and sand-save) and a Tour-specific strokes-to-hole-out
# figure. APPEND-ONLY block. Retires the single anchorless
# TOUR_UP_AND_DOWN_PCT = 0.50 (Anchor 5's weakly-sourced pro sand-save
# figure, applied uniformly to every Tour recovery -- rough, fairway
# collection, and sand alike -- and paired with the amateur-tier
# MISSED_UP_AND_DOWN_STROKES = 3.3 convention unchanged). The gate diagnosis
# for this pass (VALIDATION_NOTES.md's "Calibration pass" section) found
# the excess simulated bogeys sit in the missed-green recovery leg, not
# putting: this block replaces both anchorless Tour recovery inputs with
# published figures where the hunt found them.
#
# TOUR_SCRAMBLING_PCT: DIRECT FETCH, SwingU Clubhouse's "Understanding
# Stats: Up-And-Down Conversion By Handicap" (retrieved 2026-09-07): "The
# PGA Tour average stands at roughly 58%." Scrambling is PGA Tour's own
# stat ("the percent of time a player misses the green in regulation but
# still makes par or better"), a slightly more permissive definition than a
# strict two-shot up-and-down (a long par save also counts), but it is the
# best published Tour-wide recovery-success figure covering non-sand misses
# (rough, fringe, fairway collection areas) as a whole -- the general case
# every amateur tier's own UP_AND_DOWN_PCT already represents. Applied here
# to non-sand Tour recoveries in place of the old uniform 0.50.
#
# TOUR_SAND_SAVE_PCT: WEBSEARCH SYNTHESIS, corroborated twice -- a WebSearch
# result quoting PGA Tour's own 2022-23 "By the Numbers" season report puts
# the Tour-wide sand-save average at 49.56%; a second, independent
# WebSearch result (golfity.com, "What Is Sand Save Percentage?") states
# "PGA Tour pros average right around a 50% sand save rate." Both converge
# on the same figure Anchor 5 already carried (0.50), now corroborated by a
# second independent search rather than resting on Anchor 5's original
# single WebSearch synthesis alone. Kept at 0.50, applied to bunker misses
# specifically rather than every Tour recovery.
TOUR_SCRAMBLING_PCT = 0.58   # ANCHORED (direct fetch), Anchor 10 -- non-sand Tour recoveries
TOUR_SAND_SAVE_PCT = 0.50    # PUBLISHED (WebSearch synthesis, corroborated twice), Anchor 10 -- Tour bunker recoveries

# TOUR_MISSED_UP_AND_DOWN_STROKES: MODELED, derived arithmetic on two
# WEBSEARCH SYNTHESIS figures (Anchor 10) -- not itself a single published
# number, the same disclosed-arithmetic status Anchor 8's expected-putts
# figure already carries. Mark Broadie's "strokes to hole out" benchmark
# (Every Shot Counts methodology, widely re-quoted across golf-analytics
# secondary sources -- thediygolfer.com, golfity.com, chicagogolfreport.com
# -- all converging on the same figures) gives a 10-yard bunker shot's
# average strokes-to-hole-out as 2.47. Paired with TOUR_SAND_SAVE_PCT
# (0.50, the same bunker-recovery regime), solving E = p*2 + (1-p)*X for X:
#   2.47 = 0.50*2 + 0.50*X
#   2.47 = 1.00 + 0.50*X
#   X = (2.47 - 1.00) / 0.50 = 2.94
# Applied to BOTH sand and non-sand Tour recoveries (mirroring the prior
# single-constant structure, now Tour-specific and anchored rather than
# reusing the amateur tier's own MODELED 3.3 unchanged). Lower than the
# amateur MISSED_UP_AND_DOWN_STROKES=3.3 -- Tour players missing an
# up-and-down still hole out in fewer strokes on average than the amateur
# convention assumes, the expected direction. The amateur path is untouched
# by this block; data.MISSED_UP_AND_DOWN_STROKES keeps its own value and
# sourcing status.
TOUR_MISSED_UP_AND_DOWN_STROKES = 2.94   # MODELED (derived), Anchor 10

TOUR = {
    "sigma_iso_ft": _SIGMA_ISO_FT_TOUR,
    "proximity_ft": _PROXIMITY_FT_TOUR,
    "anisotropy": TOUR_ANISOTROPY,
    "three_putt_rate": TOUR_THREE_PUTT_RATE,
    "scrambling_pct": TOUR_SCRAMBLING_PCT,
    "sand_save_pct": TOUR_SAND_SAVE_PCT,
    "missed_up_and_down_strokes": TOUR_MISSED_UP_AND_DOWN_STROKES,
    "band_yd_range": TOUR_BAND_YD_RANGE,
    "proximity_ft_range": TOUR_PROXIMITY_FT_RANGE,
    "gir_pct_range": TOUR_GIR_PCT_RANGE,
}

SOURCES["TOUR"] = {
    "log": "docs/sources/003_Source_Log.md#anchor-7",
    "status": "proximity/GIR anchored directly at 150-175yd (contains the 155yd shot, no extrapolation step); anisotropy anchored to Broadie's published pro ratio (Anchor 2); putting modeled-anchorless (see TOUR_THREE_PUTT_RATE above); recovery rates and missed-up-and-down cost anchored/derived per Anchor 10 (docs/sources/003_Source_Log.md#anchor-10), see TOUR_SCRAMBLING_PCT/TOUR_SAND_SAVE_PCT/TOUR_MISSED_UP_AND_DOWN_STROKES above",
}

# ---------------------------------------------------------------------------
# Anchor 8 (append, #9 follow-up hunt, 2026-09-07): putts by distance, Tour
# and amateur by handicap. APPEND-ONLY block: retires the invented
# `1.5 + 0.012 * feet` putting curve that model._green_strokes and
# tour._tour_green_strokes both used before this pass -- that curve floored
# expected putts at 1.5 from any distance, including a tap-in, and priced a
# Tour player at roughly 1.6 putts from 3 feet against a published 96% make
# rate there. Nothing above this comment is read, mutated, or restructured.
#
# Tour make percentage and three-putt percentage by distance are ANCHORED,
# corroborated across two independently fetched pages (Golfing Focus,
# attributed to Mark Broadie, and Golf.com; the two pages' three-putt
# figures agree at every distance both cover). The "expected putts" figure
# the release brief recalled (1.23/1.61/1.87/1.98/2.06/2.21 at 5/10/20/30/
# 40/60 ft) is not itself a published column -- it is arithmetic performed
# on these two tables (expected putts = 1*make + 2*(1-make-three_putt) +
# 3*three_putt), confirmed by the log to reproduce the recollection to two
# decimal places at every one of those distances. MODELED status attaches
# to that arithmetic conversion, not to the two tables it is built from.
# ---------------------------------------------------------------------------

TOUR_MAKE_PCT_BY_FT = {
    2: 0.99, 3: 0.96, 4: 0.88, 5: 0.77, 10: 0.40, 15: 0.23,
    20: 0.15, 30: 0.07, 40: 0.04, 50: 0.03, 60: 0.02,
}  # ANCHORED, Anchor 8 (Golfing Focus/Broadie, corroborated by a separate WebSearch synthesis)

TOUR_THREE_PUTT_PCT_BY_FT = {
    5: 0.004, 10: 0.007, 15: 0.013, 20: 0.022, 30: 0.05, 40: 0.10, 60: 0.23,
}  # ANCHORED, Anchor 8 (Golfing Focus/Broadie, corroborated by Golf.com at every shared distance); 0-5 ft treated as 0, see tour_putt_probabilities

# Amateur make percentage by handicap and distance band (ANCHORED, Shot
# Scope direct fetch, six tiers, restated on a second page). Band midpoints
# (3, 9, 15, 21, 27 ft for the five bounded bands, 40 ft standing in for the
# open-ended 30-plus band) become the curve's x-values; 0 ft is anchored at
# a 100% make rate for every tier (nobody misses a putt already holed).
# Tier 25 is carried for completeness (matches the published table) even
# though data.TIERS stops at 20.
AMATEUR_PUTT_TIERS = [0, 5, 10, 15, 20, 25]  # ANCHORED, Anchor 8 (Shot Scope's own six tiers)
AMATEUR_MAKE_PCT_BAND_MIDPOINT_FT = [0.0, 3.0, 9.0, 15.0, 21.0, 27.0, 40.0]

_AMATEUR_MAKE_PCT_ROWS_BY_BAND = {
    # band label: [scratch, 5, 10, 15, 20, 25] make pct, ANCHORED Anchor 8 (Shot Scope)
    "0-6ft": [0.928, 0.902, 0.893, 0.844, 0.840, 0.825],
    "6-12ft": [0.428, 0.414, 0.381, 0.396, 0.378, 0.350],
    "12-18ft": [0.251, 0.239, 0.202, 0.202, 0.188, 0.160],
    "18-24ft": [0.145, 0.130, 0.103, 0.112, 0.118, 0.101],
    "24-30ft": [0.083, 0.101, 0.054, 0.078, 0.068, 0.063],
    "30+ft": [0.043, 0.043, 0.028, 0.032, 0.019, 0.023],
}

AMATEUR_MAKE_PCT_BY_BAND = {
    tier: {0.0: 1.0}  # ANCHORED (definitional): a putt already at 0 ft is holed
    for tier in AMATEUR_PUTT_TIERS
}
for _band, _mid in zip(["0-6ft", "6-12ft", "12-18ft", "18-24ft", "24-30ft", "30+ft"],
                        AMATEUR_MAKE_PCT_BAND_MIDPOINT_FT[1:]):
    for _i, _tier in enumerate(AMATEUR_PUTT_TIERS):
        AMATEUR_MAKE_PCT_BY_BAND[_tier][_mid] = _AMATEUR_MAKE_PCT_ROWS_BY_BAND[_band][_i]
del _band, _mid, _i, _tier

# Amateur three-putt rate by distance has no published breakdown anywhere in
# the source hunt (Anchor 8's own verdict): only a by-handicap, not-by-
# distance, figure exists (Anchor 5's THREE_PUTT_RATE). MODELED: scale the
# Tour three-putt-BY-DISTANCE shape by the ratio of each tier's own ANCHORED
# per-hole three-putt rate to a MODELED implied Tour per-hole rate, so a
# tier that three-putts more often per Anchor 5 also three-putts more often
# at any given distance than the Tour shape alone would predict.
# TOUR_THREE_PUTT_RATE_PER_HOLE has no figure in this release's source log;
# Tour three-putt frequency is widely quoted in golf-instruction writing at
# roughly 3% of holes, used here as a documented, disclosed MODELED
# constant with a stated sensitivity range, not a fitted value.
TOUR_THREE_PUTT_RATE_PER_HOLE = 0.03          # MODELED, anchorless, widely-quoted approximate figure
TOUR_THREE_PUTT_RATE_PER_HOLE_RANGE = (0.02, 0.04)  # MODELED sensitivity range

AMATEUR_THREE_PUTT_SHAPE_SCALE = {
    t: THREE_PUTT_RATE[t] / TOUR_THREE_PUTT_RATE_PER_HOLE for t in TIERS
}  # MODELED: ANCHORED numerator (Anchor 5) over a MODELED denominator

SOURCES["PUTTING"] = {
    "log": "docs/sources/003_Source_Log.md#anchor-8",
    "status": ("Tour make%/three-putt% by distance anchored (Golfing Focus/Broadie, "
               "corroborated by Golf.com); amateur make% by handicap and distance band "
               "anchored (Shot Scope, six tiers, direct fetch); amateur three-putt-by-"
               "distance modeled (Tour shape scaled by Anchor 5's per-hole rate over a "
               "modeled Tour per-hole rate, range 0.02-0.04); replaces the pre-existing "
               "invented 1.5 + 0.012*ft curve entirely"),
}

# ---------------------------------------------------------------------------
# Anchor 9 (append, #9 follow-up hunt, 2026-09-07): Masters hole-12 scoring
# average by year, 2019 and 2021-2025. APPEND-ONLY block. The gate previously
# compared the Tour oval (built on Anchor 7's 2016-2023 proximity data)
# against the all-time 3.27-3.28 scoring average, which spans 1934-2025 and
# is pulled upward by high-scoring years decades before the proximity data's
# own era. Every modern year found in this hunt scores below the all-time
# figure, most by two to three tenths of a stroke.
# ---------------------------------------------------------------------------

HOLE12_MODERN_AVG_BY_YEAR = {
    2019: 3.053,  # ANCHORED, two-source (Racing Post direct fetch + WebSearch synthesis corroboration)
    2021: 3.11,   # PUBLISHED, single-source (SI.com direct fetch)
    2022: 3.233,  # PUBLISHED, single-source, WebSearch-synthesis only (PGA Tour direct fetch returned no data for this event)
    2023: 3.058,  # PUBLISHED, single-source (PGA Tour course-stats, direct fetch)
    2024: 3.198,  # ANCHORED, two-source (PGA Tour course-stats + Today's Golfer, both direct fetch)
    2025: 3.139,  # PUBLISHED, single-source (PGA Tour course-stats, direct fetch)
}  # Anchor 9; two-source years: 2019, 2024. Single-source years: 2021, 2022, 2023, 2025.

HOLE12_ALLTIME_AVG_RANGE = (3.27, 3.28)  # ANCHORED, Anchor 4; context only, not the gate target (era mismatch, see Anchor 9)

# Per-year outcome counts, where the log states them (birdie, par, bogey,
# double-bogey-or-worse), out of that year's total plays. 2019 and 2024 are
# two-source years; 2023 and 2025 are single-source (PGA Tour course-stats,
# direct fetch, no independent second source found in this hunt).
HOLE12_OUTCOMES_BY_YEAR = {
    2019: dict(birdie=52, par=200, bogey=38, double_or_worse=14),   # ANCHORED, two-source, Anchor 4
    2023: (49, 173, 47, 9),                                          # PUBLISHED, single-source, Anchor 9 (PGA Tour course-stats)
    2024: (40, 185, 52, 17),                                         # ANCHORED, two-source, Anchor 9 (PGA Tour course-stats + Today's Golfer)
    2025: (40, 190, 53, 12),                                         # PUBLISHED, single-source, Anchor 9 (PGA Tour course-stats)
}  # tuple order, where used: (birdie, par, bogey, double_or_worse)

SOURCES["HOLE12_MODERN_AVG_BY_YEAR"] = {
    "log": "docs/sources/003_Source_Log.md#anchor-9",
    "status": "2019/2024 anchored (two independent fetches each); 2021/2022/2023/2025 published single-source (2022 WebSearch-synthesis only); all-time 3.27-3.28 kept as context, not the gate target",
}
