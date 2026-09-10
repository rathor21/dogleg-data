"""Analytic expected-strokes model for release 003 (Augusta 12 aim-point
piece), amateur ovals.

Vocabulary (CONTEXT.md, binding): a dispersion oval belongs to a golfer-club
pair; an aim point is where a golfer should aim, chosen to minimize expected
score; a sucker pin raises expected score for the tier aiming at it; a
short-sided miss is priced through the recovery leg, never treated as merely
"a missed green."

Three-step oval construction:

  1. Radial miss scale. data.py inverts Anchor 1's proximity and GIR-by-
     distance figures into an isotropic radial miss sigma per tier, scaled to
     the 155-yard tee shot (data.SIGMA_ISO_FT). See data.py's module
     docstring for the full derivation.
  2. Anisotropy split. oval_for_tier() below splits that isotropic sigma into
     a distance-sd and a line-sd using the amateur anisotropy ratio (default
     3.0, Anchor 2, sensitivity range 2.0-3.5), preserving total variance.
  3. Hole placement. score_for_oval() below places the resulting 2D oval on
     Augusta 12's anchor-and-range hole geometry (data.HOLE, data.PINS) and
     integrates it over named outcome regions -- green (by section), front
     bunker, back bunkers, creek/drop, and short-sided vs. long recovery --
     to price expected strokes. expected_score() is the tier-facing wrapper.

Own-tier baseline. Every MODELED constant lives in data.py with its
sensitivity range; this module's job is the construction and integration
logic, not new numbers.

Rev 6 (Sunny's finding): distance error is a two-component mixture, not one
symmetric Gaussian. mishit_mixture_params() below re-splits Step 1's
isotropic sigma into a tighter solid-strike core plus a short mishit tail;
expected_score() becomes the mixture-weighted sum of two score_for_oval()
calls instead of one. Rev 6 solved that core to preserve Step 1+2's own
anchored second moment -- disclosed in ADR 0003 as not narrow enough to
fully fix either of Sunny's findings (a single symmetric Gaussian let a
20-handicap post a lower water rate than a scratch player at the same aim,
and still showed water risk at a 200-yd carry).

Rev 7 (GIR-anchored core): mishit_mixture_params() now solves the
solid-strike core so the full mixture reproduces each tier's own published
green-hit RATE at its own anchor distance (data.solid_strike_sigma_iso_ft),
not a second moment. See that function's docstring and data.py's
GIR-anchored-core append block for the construction, and VALIDATION_NOTES.md's
rev 7 section for the sweep that chose this pass's MISHIT_PCT/MISHIT_SHORT_
FRAC/ANISOTROPY ratio and the residual violations that remain.
"""

from math import exp, pi, sqrt

import numpy as np

import data

FT_PER_YD = 3.0

# Single source of truth for region names (region-geometry fix, this pass):
# montecarlo.py, tour.py, and export.py all branch on these names, so a new
# region gets added here once rather than drifting across four files.
# "short_fairway" is a pitch over Rae's Creek from the fairway short of the
# creek-plus-bank band (see region_at's docstring) -- NOT water, priced as a
# non-sand recovery leg, never the creek penalty.
REGION_NAMES = (
    "green", "front_bunker", "back_bunker", "creek", "short_fairway",
    "long_trouble", "long_rough", "greenside_rough",
)


# ---------------------------------------------------------------------------
# Step 2: anisotropy split (and its inverse, for the round-trip test).
# ---------------------------------------------------------------------------

def _anisotropy_split(sigma_iso_yd, ratio):
    """(sigma_distance_yd, sigma_line_yd): split an isotropic radial sigma
    into anisotropic distance/line axes at the given ratio, preserving total
    variance (sigma_d**2 + sigma_l**2 == 2 * sigma_iso**2). Shared by
    oval_for_tier (the plain, pre-mixture oval) and mishit_mixture_params
    (rev 7's GIR-anchored solid-strike core) so the two never drift apart on
    the split formula itself."""
    sigma_l = sigma_iso_yd * sqrt(2.0 / (ratio ** 2 + 1.0))
    sigma_d = ratio * sigma_l
    return sigma_d, sigma_l


def oval_for_tier(tier, anisotropy_ratio=None, shot_yd=data.TEE_SHOT_YD):
    """(sigma_distance_yd, sigma_line_yd): the dispersion oval for tier at
    shot_yd yards.

    Splits data.SIGMA_ISO_FT[tier] (Step 1, an isotropic radial sigma in
    feet) into anisotropic distance/line axes using anisotropy_ratio
    (default data.ANISOTROPY["ratio"] = 2.5; sensitivity range
    data.ANISOTROPY["range"], Anchor 2 -- a parameter, never a buried
    constant). Total variance is preserved: sigma_d**2 + sigma_l**2 ==
    2 * sigma_iso**2, so widening the ratio redistributes spread between axes
    without changing the golfer's overall miss magnitude.
    """
    ratio = data.ANISOTROPY["ratio"] if anisotropy_ratio is None else anisotropy_ratio
    sigma_iso_yd = data.sigma_isotropic_ft(tier, shot_yd) / FT_PER_YD
    return _anisotropy_split(sigma_iso_yd, ratio)


def mishit_mixture_params(tier, anisotropy_ratio=None, shot_yd=data.TEE_SHOT_YD):
    """(sigma_solid_d_yd, sigma_l_yd, p_mis, k_mis_yd): rev 7's GIR-anchored
    two-component distance-error mixture (data.py's GIR-anchored-core append
    block). Rev 6 solved the mixture's solid-strike sigma so the mixture's
    TOTAL second moment matched the OLD symmetric-Gaussian sigma_d exactly;
    that kept the core almost as wide as the old anchor (4-12% narrower), not
    tight enough to fix either of Sunny's two findings (water probability
    falling with tier at some pins; nonzero water risk at an absurd 200-yd
    carry). This release's own published anchor is a green-hit RATE at each
    tier's own anchor distance (data.GIR50_DISTANCE_YD, or tier 10's matched
    proximity/GIR pair), not a variance -- so rev 7 re-solves the solid-
    strike core to reproduce that RATE directly, letting the mishit tail
    (unchanged mechanism, MISHIT_PCT/MISHIT_SHORT_FRAC) carry the short-side
    skew instead of the core absorbing it as extra symmetric width.

    Distance error is a mixture: with probability 1 - p_mis, N(0,
    sigma_solid) (a solid strike); with probability p_mis (data.MISHIT_PCT
    [tier], MODELED, sensitivity range a 0.5x-1.5x multiplier), N(-k_mis,
    sigma_solid) (a mishit, same spread as the solid strike, its mean
    shifted short by k_mis = data.MISHIT_SHORT_FRAC * shot_yd, MODELED,
    sensitivity range 0.20-0.30 of shot distance). Unlike rev 6, sigma_l is
    NOT frozen at oval_for_tier's own plain-Gaussian value -- it comes from
    the same anisotropy split applied to the new, tighter solid-strike
    isotropic core, since the anchored quantity being reproduced (a circular
    GIR rate) is inherently two-axis, not a distance-only second moment.

    data.solid_strike_sigma_iso_ft(tier, shot_yd) does the actual anchor
    work: it solves, via 2D numeric integration and bisection (see that
    module's docstring), the isotropic sigma at which the two-component
    mixture reproduces the tier's target GIR% AT ITS OWN ANCHOR DISTANCE
    (using k_mis evaluated at that anchor distance, not at shot_yd), then
    scales that anchor sigma linearly to shot_yd the same way data.
    sigma_isotropic_ft's own k_tier construction does. This function then
    applies _anisotropy_split to that scaled isotropic core (the same split
    oval_for_tier uses) and builds k_mis at the ACTUAL shot distance
    (shot_yd, not the anchor distance) for use downstream in
    score_for_oval's mean shift -- the anchor-distance k_mis is an internal
    detail of data.solid_strike_sigma_iso_ft's own solve, never returned
    here.

    See tests/test_model.py::test_mixture_reproduces_anchored_gir_at_anchor_
    distance for the round-trip check (rev 6's second-moment test is
    retired -- rev 7 no longer targets a second moment at all).
    """
    ratio = data.ANISOTROPY["ratio"] if anisotropy_ratio is None else anisotropy_ratio
    sigma_solid_iso_yd = data.solid_strike_sigma_iso_ft(tier, shot_yd) / FT_PER_YD
    sigma_solid_d, sigma_l = _anisotropy_split(sigma_solid_iso_yd, ratio)
    p_mis = data.MISHIT_PCT[tier]
    k_mis = data.MISHIT_SHORT_FRAC * shot_yd
    return sigma_solid_d, sigma_l, p_mis, k_mis


def mean_radial_ft(sigma_d_yd, sigma_l_yd):
    """Inverse of Step 1+2: mean radial miss (ft) implied by an oval.

    Recombines the anisotropic axes into the isotropic radial sigma that
    would produce them (sigma_iso**2 = (sigma_d**2 + sigma_l**2) / 2) and
    applies the Rayleigh mean relation E[R] = sigma*sqrt(pi/2). Used by the
    round-trip test to confirm oval_for_tier reproduces the published input
    proximity aggregates it was inverted from.
    """
    sigma_iso_yd = sqrt((sigma_d_yd ** 2 + sigma_l_yd ** 2) / 2.0)
    return sigma_iso_yd * FT_PER_YD * sqrt(pi / 2.0)


def gir_probability(sigma_iso_yd, green_radius_ft=None, shot_yd=None):
    """P(land within green_radius_ft of the aim point), isotropic Gaussian
    miss. Used by the round-trip test to confirm each tier's oval reproduces
    50% GIR at that tier's own published GIR50 distance (data.GIR50_DISTANCE_YD)."""
    r = data.GREEN_RADIUS_FT if green_radius_ft is None else green_radius_ft
    sigma_ft = sigma_iso_yd * FT_PER_YD
    return 1.0 - exp(-(r ** 2) / (2.0 * sigma_ft ** 2))


# ---------------------------------------------------------------------------
# Step 3: hole geometry placement and outcome-region pricing.
# ---------------------------------------------------------------------------

def _resolve_geometry(green_width_yd=None, front_third_depth_yd=None):
    """Merge caller overrides with the published-range defaults (midpoint of
    the range) for the geometry parameters the ticket calls out by name:
    green width and the center pin's front-third depth. Also resolves the
    green's overall front-to-back depth (data.HOLE["green_depth_yd_range"]),
    ANCHORED as a range but not previously wired into region_at -- see
    _front_edge_yd/_back_edge_yd below. Never a single buried constant, all
    three are data.HOLE ranges unless overridden."""
    w_lo, w_hi = data.HOLE["green_width_yd_range"]
    width = green_width_yd if green_width_yd is not None else 0.5 * (w_lo + w_hi)
    ft_lo, ft_hi = data.HOLE["front_third_depth_yd_range"]
    center_depth = front_third_depth_yd if front_third_depth_yd is not None else 0.5 * (ft_lo + ft_hi)
    d_lo, d_hi = data.HOLE["green_depth_yd_range"]
    total_depth = 0.5 * (d_lo + d_hi)
    return {"width": width, "center_depth": center_depth, "total_depth": total_depth}


def _pin_local_depth(pin_key, geom):
    """The PIN's own local section depth (used only for short-siding and
    putt-distance shaping, never for the green/hazard boundary itself -- see
    region_at's docstring for why those two things are no longer the same
    computation)."""
    if pin_key == "center":
        return geom["center_depth"]
    lo, hi = data.PINS[pin_key]["local_depth_yd_range"]
    return 0.5 * (lo + hi)


# Diagonal front (creek) edge slope, yards of required carry per yard of
# lateral offset. Derived, not invented: Anchor 3's one ANCHORED quantitative
# diagonal signal is "the Sunday pin sits roughly 15 yards deeper into the
# green than a front-left pin"; dividing that 15-yd offset by the (MODELED)
# lateral separation between that front-left reference point and the Sunday
# pin gives the green's front-edge slope. Reads data._FRONT_LEFT_SLOPE_
# REFERENCE_X/Y -- a fixed reference point decoupled from data.PINS["left"]
# -- rather than the "left" pin's own coordinates, specifically so that
# repositioning the named "left" demo pin (see data.py's PINS comment) never
# quietly changes this ANCHORED slope. The qualitative "shoe-sole" shape is
# ANCHORED; this specific linear form is MODELED, matching this release's
# usual disclosure.
_FRONT_EDGE_SLOPE_YD_PER_YD = (
    (data.PINS["sunday"]["y"] - data._FRONT_LEFT_SLOPE_REFERENCE_Y)
    / (data.PINS["sunday"]["x"] - data._FRONT_LEFT_SLOPE_REFERENCE_X)
)


def _front_edge_yd(x, geom):
    """The green's front (creek-side) edge, y-yards-from-tee, at lateral
    position x. A single hazard boundary shared by every pin and every aim
    point -- unlike a per-pin box, this makes carry-to-clear-the-creek grow
    with x regardless of which pin is currently being scored, per Anchor 3's
    diagonal/shoe-sole description: the green (and the water fronting it)
    angles away from the tee moving right, toward the Sunday side. Anchored
    at x=0 using the center pin's own front-third figure (Anchor 3's
    best-corroborated single number, the "narrowest middle pin" section),
    then extrapolated with _FRONT_EDGE_SLOPE_YD_PER_YD."""
    front_at_center = data.PINS["center"]["y"] - geom["center_depth"]
    return front_at_center + _FRONT_EDGE_SLOPE_YD_PER_YD * x


def _back_edge_yd(x, geom):
    """The green's back edge, y-yards-from-tee, at lateral position x: the
    diagonal front edge plus the green's overall published depth
    (data.HOLE["green_depth_yd_range"]). Kept parallel to the front edge
    (same slope) -- no source in the hunt gives the back edge its own
    diagonal figure, so this is the minimal extension consistent with the
    front-edge anchor rather than a second invented slope."""
    return _front_edge_yd(x, geom) + geom["total_depth"]


def region_at(x, y, pin, *, green_width_yd=None, front_third_depth_yd=None):
    """Classify a landing point (x, y yards, tee-shot frame: y = carry
    distance from tee, x = lateral offset, positive = right/Sunday side) into
    one of Augusta 12's outcome regions.

    The green/hazard boundary (front edge, back edge, width) is ONE shape
    shared by every pin -- computed from x and y alone, never from which pin
    is being aimed at -- matching the real hole: there is a single green and
    a single creek, and the flag's position within that green does not move
    the water. Only two things are pin-specific: is_short_sided (which side
    of THIS pin has little green to work with, CONTEXT.md's definition) and,
    downstream in _region_strokes, the distance-to-pin used for putts.

    Returns (region, is_short_sided). region is one of model.REGION_NAMES:
    "green", "front_bunker", "back_bunker", "creek", "short_fairway",
    "long_trouble", "long_rough", "greenside_rough". "long_trouble" is a
    miss that clears the back bunkers by data.LONG_TROUBLE_BUFFER_YD or
    more -- Anchor 3's azalea-lined ledge, priced worse than plain rough
    (see _recovery_strokes) rather than folded into "long_rough" at the
    same price, which previously let overclubbing the green look like a
    free way to dodge the creek.

    "creek" is now a FINITE band short of the front edge (region-geometry
    fix, this pass), not every yard back to the tee: Rae's Creek itself
    (data.CREEK_WIDTH_YD) plus the shaved bank in front of it that rolls a
    ball back into the water (data.BANK_ROLLBACK_YD, Anchor 3's 2019
    Koepka/Molinari narrative). A non-bunker miss short of that combined
    band is "short_fairway" -- a pitch over the creek from the short grass,
    priced as a plain non-sand recovery leg, never the creek's drop-and-
    replay penalty. Before this fix, every non-bunker miss short of the
    front edge, however far short, was "creek," which overpriced a
    27-yard-short 15-handicap miss on the Sunday pin as a water penalty.
    """
    if pin not in data.PINS:
        raise KeyError(f"unknown pin {pin!r}; expected one of {sorted(data.PINS)}")
    geom = _resolve_geometry(green_width_yd, front_third_depth_yd)
    p = data.PINS[pin]
    py = p["y"]

    front_edge = _front_edge_yd(x, geom)
    back_edge = _back_edge_yd(x, geom)
    half_width = geom["width"] / 2.0
    left_edge, right_edge = -half_width, half_width

    if front_edge <= y <= back_edge and left_edge <= x <= right_edge:
        return "green", False

    # Which side of the pin the miss sits on, and whether that is the pin's
    # short side (CONTEXT.md: little green between ball and pin). Relative to
    # the AIM pin specifically, unlike the hazard boundary above.
    on_front_side = y < py
    is_short_sided = (on_front_side and p["front_frac"] < 0.5) or ((not on_front_side) and p["back_frac"] < 0.5)

    if y < front_edge:
        bunker_lo, bunker_hi = data.HOLE["front_bunker_x_range"]
        bunker_front = front_edge - data.HOLE["front_bunker_depth_yd"]
        if bunker_lo <= x <= bunker_hi and bunker_front <= y < front_edge:
            return "front_bunker", is_short_sided
        creek_near_edge = front_edge - (data.CREEK_WIDTH_YD + data.BANK_ROLLBACK_YD)
        if creek_near_edge <= y < front_edge:
            return "creek", is_short_sided
        return "short_fairway", is_short_sided

    if y > back_edge:
        bunker_back = back_edge + data.HOLE["back_bunker_depth_yd"]
        for lo, hi in data.HOLE["back_bunker_x_ranges"]:
            if lo <= x <= hi and back_edge < y <= bunker_back:
                return "back_bunker", is_short_sided
        trouble_back = bunker_back + data.LONG_TROUBLE_BUFFER_YD
        if y > trouble_back:
            return "long_trouble", is_short_sided
        return "long_rough", is_short_sided

    return "greenside_rough", is_short_sided


def _lerp_table(table, x):
    """Linear interpolation of `table` (a {ft: value} dict) at distance x.
    Flat extrapolation outside the table's own range: x at or below the
    smallest key returns that key's value, x at or above the largest key
    returns that key's value -- interpolation never invents a value below
    the last anchor it has evidence for."""
    keys = sorted(table)
    if x <= keys[0]:
        return table[keys[0]]
    if x >= keys[-1]:
        return table[keys[-1]]
    for lo, hi in zip(keys, keys[1:]):
        if lo <= x <= hi:
            t = (x - lo) / (hi - lo)
            return table[lo] + t * (table[hi] - table[lo])
    return table[keys[-1]]  # unreachable, defensive


def putt_probabilities(tier, dist_ft):
    """(p1, p2, p3): probability of holing out in one, two, or three-plus
    putts from dist_ft, for amateur tier.

    Anchor 8 (docs/sources/003_Source_Log.md#anchor-8) replaces the release's
    original invented `1.5 + 0.012*ft` curve, which floored expected putts
    at 1.5 from any distance including a tap-in.

    p1: linear interpolation of data.AMATEUR_MAKE_PCT_BY_BAND[tier] (Shot
    Scope's own six distance-band midpoints, plus a definitional 1.0 at 0
    ft), ANCHORED.

    p3: MODELED. No source publishes amateur three-putt rate broken out by
    distance, so this scales the Tour three-putt-BY-DISTANCE shape
    (data.TOUR_THREE_PUTT_PCT_BY_FT) by data.AMATEUR_THREE_PUTT_SHAPE_SCALE
    [tier] -- the ratio of this tier's own ANCHORED per-hole three-putt rate
    (Anchor 5) to a MODELED implied Tour per-hole rate. Capped so p1+p3 never
    exceeds 1 (a long tier-scaled p3 could otherwise push the total over 1
    at distances where p1 is not yet small).

    p2 is whatever probability mass is left: 1 - p1 - p3.
    """
    p1 = _lerp_table(data.AMATEUR_MAKE_PCT_BY_BAND[tier], dist_ft)
    if dist_ft <= 5.0:
        tour_p3_shape = 0.0
    else:
        tour_p3_shape = _lerp_table(data.TOUR_THREE_PUTT_PCT_BY_FT, dist_ft)
    p3_raw = tour_p3_shape * data.AMATEUR_THREE_PUTT_SHAPE_SCALE[tier]
    p3 = min(p3_raw, max(0.0, 1.0 - p1))
    p2 = max(0.0, 1.0 - p1 - p3)
    return p1, p2, p3


def _green_strokes(tier, dist_to_pin_ft):
    """Expected strokes to finish from on the green: expected putts only (the
    approach stroke itself is charged once, in score_for_oval).

    putt_probabilities (Anchor 8) replaces the release's original invented
    `1.5 + 0.012*ft * (1 + three_putt_rate)` formula, which floored expected
    putts at 1.5 from any distance -- a Tour player faced a ~1.6-putt price
    from 3 feet against a published 96% make rate there. The three-putt
    anchor now enters through p3 directly, not as a separate multiplier.
    """
    p1, p2, p3 = putt_probabilities(tier, dist_to_pin_ft)
    return p1 + 2.0 * p2 + 3.0 * p3


def _recovery_strokes(tier, is_short_sided, sand, trouble=False, overshoot_yd=0.0, far_short_yd=0.0):
    """Expected strokes to finish from a greenside miss (bunker, rough,
    long trouble, or short_fairway).

    data.UP_AND_DOWN_PCT (MODELED, Anchor 5) sets the split between a
    successful up-and-down (2 strokes: recovery shot + 1 putt) and a missed
    one (data.MISSED_UP_AND_DOWN_STROKES, MODELED). Non-sand recovery is
    MODELED slightly easier (data.ROUGH_RECOVERY_EASE). trouble=True (Anchor
    3's azalea-lined ledge behind the back bunkers) applies a further MODELED
    discount, data.LONG_TROUBLE_UPDOWN_MULT, sensitivity range
    data.LONG_TROUBLE_UPDOWN_MULT_RANGE -- a miss that clears the bunkers by
    a wide margin is not an easier lie than one that finds them, and pricing
    it as if it were let an aim-point search dodge the creek for free by
    badly overclubbing. A short-sided miss (CONTEXT.md definition) applies
    data.SHORT_SIDE_PENALTY on top, per the glossary's instruction to price
    short-siding through the recovery leg.

    overshoot_yd (trouble legs only): yards carried past the long_trouble
    buffer edge (region_at's trouble_back boundary), i.e. how deep into the
    ledge the miss sits. #8 found the pre-fix trouble price flat in this
    distance, so an aim-point search kept "improving" its score the farther
    it carried past the green with no interior optimum. Deeper overshoot
    blends this leg's price toward _creek_strokes's hazard-like cost (an
    exponential approach over data.LONG_TROUBLE_FALLOFF_YD, MODELED,
    anchorless, sensitivity range data.LONG_TROUBLE_FALLOFF_YD_RANGE) so the
    price keeps climbing with distance rather than plateauing, trending
    toward -- but never exceeding -- the same drop-and-replay-plus-recovery
    price already charged for finding the creek outright.

    far_short_yd (short_fairway legs only, region-geometry fix): yards short
    of the creek band's own near edge the miss sits. The same "flat price,
    no interior minimum" defect #8 found on the long side reappears on the
    short side if this leg's price never changes with distance: an
    aim-point search would keep improving without bound the farther it
    aimed short of the creek band (steadily lower odds of ever reaching the
    green/creek/bunker mix), hitting optimizer.py's search-box edge at an
    unrealistic ~45-yd layup rather than a genuine aim-point finding. A
    recovery shot from well short of the green is a fuller approach, not a
    greenside chip, so it should not keep the near-green "up-and-down in 2"
    convention's benefit of the doubt the farther short it starts: deeper
    far_short_yd fades this leg's up-and-down odds toward zero (an
    exponential approach over data.SHORT_FAIRWAY_FALLOFF_YD, MODELED,
    anchorless, sensitivity range data.SHORT_FAIRWAY_FALLOFF_YD_RANGE),
    converging on data.MISSED_UP_AND_DOWN_STROKES -- the same "recovery
    didn't work" ceiling every other leg already uses, not a new invented
    price, and never a hazard-like price, since being farther from the
    green on the fairway side of the creek is not a step toward the water.
    """
    updown = data.UP_AND_DOWN_PCT[tier]
    if not sand:
        updown = min(0.95, updown * data.ROUGH_RECOVERY_EASE)
    if trouble:
        updown = updown * data.LONG_TROUBLE_UPDOWN_MULT
    e = updown * 2.0 + (1.0 - updown) * data.MISSED_UP_AND_DOWN_STROKES
    if is_short_sided:
        e *= data.SHORT_SIDE_PENALTY
    if trouble and overshoot_yd > 0.0:
        hazard_like = _creek_strokes(tier, is_short_sided)
        blend = 1.0 - exp(-overshoot_yd / data.LONG_TROUBLE_FALLOFF_YD)
        e = e * (1.0 - blend) + hazard_like * blend
    if far_short_yd > 0.0:
        ceiling = data.MISSED_UP_AND_DOWN_STROKES * (data.SHORT_SIDE_PENALTY if is_short_sided else 1.0)
        blend = 1.0 - exp(-far_short_yd / data.SHORT_FAIRWAY_FALLOFF_YD)
        e = e * (1.0 - blend) + ceiling * blend
    return e


def _creek_strokes(tier, is_short_sided):
    """Expected strokes after finding the creek: a penalty stroke
    (data.CREEK_PENALTY_STROKES, a drop-and-replay convention, same spirit as
    002's OB_COST) plus a recovery leg from the drop area, priced like a
    non-sand recovery."""
    return data.CREEK_PENALTY_STROKES + _recovery_strokes(tier, is_short_sided, sand=False)


def _short_fairway_strokes(tier, is_short_sided, far_short_yd):
    """Expected strokes for the short_fairway leg (rev 5, issue #8's
    pitch-over-water risk fix): a pitch from the fairway that has to carry
    Rae's Creek to reach the green, not a plain recovery with no hazard in
    front of it the way rev 4's fix priced it.

    Expected strokes = (1 - p) * recovery + p * (CREEK_PENALTY_STROKES + 1.0
    + recovery_after_drop), where:

    - p = data.PITCH_OVER_WATER_DUNK_PCT[tier] (MODELED, anchorless): the
      share of these pitches a golfer of this tier fats or thins into the
      creek instead of carrying it.
    - recovery is the existing plain non-sand recovery leg, with the
      existing far_short_yd distance falloff (_recovery_strokes), unchanged
      from rev 4 -- the price when the pitch clears the water.
    - the dunk branch charges CREEK_PENALTY_STROKES (the standard
      drop-and-replay convention, same as _creek_strokes) PLUS 1.0 (the
      pitch stroke itself, wasted in the water) PLUS recovery_after_drop, a
      second plain non-sand recovery leg (no far_short_yd -- the drop area
      sits right at the creek's edge, a genuine greenside chip, not another
      long pitch) priced identically to _creek_strokes's own recovery term:
      a drop and replay from the same side.
    """
    p = data.PITCH_OVER_WATER_DUNK_PCT[tier]
    recovery = _recovery_strokes(tier, is_short_sided, sand=False, far_short_yd=far_short_yd)
    recovery_after_drop = _recovery_strokes(tier, is_short_sided, sand=False)
    dunk = data.CREEK_PENALTY_STROKES + 1.0 + recovery_after_drop
    return (1.0 - p) * recovery + p * dunk


def _long_trouble_overshoot_yd(x, y, geom):
    """Yards `y` sits past region_at's long_trouble boundary at lateral
    position `x` (region_at's own trouble_back computation, duplicated here
    rather than threaded back out of region_at so region_at's return shape
    -- (region, is_short_sided) -- stays the stable two-value API every
    caller, including montecarlo.py, already depends on)."""
    back_edge = _back_edge_yd(x, geom)
    bunker_back = back_edge + data.HOLE["back_bunker_depth_yd"]
    trouble_back = bunker_back + data.LONG_TROUBLE_BUFFER_YD
    return max(0.0, y - trouble_back)


def _short_fairway_overshoot_yd(x, y, geom):
    """Yards `y` sits short of region_at's creek-band near edge at lateral
    position `x` (region_at's own creek_near_edge computation, duplicated
    here for the same reason _long_trouble_overshoot_yd duplicates
    trouble_back: region_at's return shape stays the stable two-value API
    every caller depends on). Zero for any point at or past that edge
    (i.e. inside the creek band or beyond); positive only for genuine
    short_fairway points."""
    front_edge = _front_edge_yd(x, geom)
    creek_near_edge = front_edge - (data.CREEK_WIDTH_YD + data.BANK_ROLLBACK_YD)
    return max(0.0, creek_near_edge - y)


def _region_strokes(region, is_short_sided, tier, x, y, pin, *,
                     green_width_yd=None, front_third_depth_yd=None):
    if region == "green":
        p = data.PINS[pin]
        dist_to_pin_ft = sqrt((x - p["x"]) ** 2 + (y - p["y"]) ** 2) * FT_PER_YD
        return _green_strokes(tier, dist_to_pin_ft)
    if region == "creek":
        return _creek_strokes(tier, is_short_sided)
    if region in ("front_bunker", "back_bunker"):
        return _recovery_strokes(tier, is_short_sided, sand=True)
    if region == "long_trouble":
        geom = _resolve_geometry(green_width_yd, front_third_depth_yd)
        overshoot_yd = _long_trouble_overshoot_yd(x, y, geom)
        return _recovery_strokes(tier, is_short_sided, sand=False, trouble=True, overshoot_yd=overshoot_yd)
    if region == "short_fairway":
        geom = _resolve_geometry(green_width_yd, front_third_depth_yd)
        far_short_yd = _short_fairway_overshoot_yd(x, y, geom)
        return _short_fairway_strokes(tier, is_short_sided, far_short_yd)
    # long_rough, greenside_rough: a plain non-sand recovery leg, no penalty
    # stroke.
    return _recovery_strokes(tier, is_short_sided, sand=False)


def score_for_oval(sigma_d_yd, sigma_l_yd, tier, pin, aim_point, mean_shift_y=0.0, *,
                    green_width_yd=None, front_third_depth_yd=None,
                    n_std=4.0, n_grid=41):
    """Expected strokes to finish the hole, given an explicit oval.

    sigma_d_yd/sigma_l_yd: the two dispersion-oval axes (yards), independent
    after the anisotropy split. tier: one of data.TIERS, used only for the
    recovery/putting pricing (data.THREE_PUTT_RATE, data.UP_AND_DOWN_PCT),
    never to rebuild the oval -- pass whatever sigma pair you like. pin: one
    of data.PINS. aim_point: (x, y) yards in the tee-shot frame the golfer
    aims at. mean_shift_y: applied to the oval's mean carry (wind's carry
    penalty; negative shortens the shot). green_width_yd/front_third_depth_yd:
    geometry overrides, see region_at.

    Integrates the bivariate normal (independent axes) over Augusta 12's
    outcome regions on a truncated (n_grid x n_grid) product grid spanning
    +/- n_std standard deviations of each axis, weighted by the normal
    density and renormalized so the (slightly truncated) weights sum to 1.
    +1 for the approach stroke itself.

    sigma_d_yd/sigma_l_yd may be arbitrarily small (down to a floor that
    keeps the grid numerically well-defined); a near-zero oval collapses the
    grid onto the single point nearest aim_point and returns 1 plus that
    point's exact regional price, the sensible degenerate limit.
    """
    if tier not in data.TIERS:
        raise KeyError(f"unknown tier {tier!r}; expected one of {data.TIERS}")
    sigma_d = max(sigma_d_yd, 1e-6)
    sigma_l = max(sigma_l_yd, 1e-6)
    mean_x, mean_y = aim_point[0], aim_point[1] + mean_shift_y

    ys = np.linspace(mean_y - n_std * sigma_d, mean_y + n_std * sigma_d, n_grid)
    xs = np.linspace(mean_x - n_std * sigma_l, mean_x + n_std * sigma_l, n_grid)
    wy = np.exp(-0.5 * ((ys - mean_y) / sigma_d) ** 2)
    wx = np.exp(-0.5 * ((xs - mean_x) / sigma_l) ** 2)
    wy = wy / wy.sum()
    wx = wx / wx.sum()

    total = 0.0
    for yi, wyi in zip(ys, wy):
        if wyi == 0.0:
            continue
        for xi, wxi in zip(xs, wx):
            w = wyi * wxi
            if w == 0.0:
                continue
            region, short_sided = region_at(float(xi), float(yi), pin,
                                             green_width_yd=green_width_yd,
                                             front_third_depth_yd=front_third_depth_yd)
            total += w * _region_strokes(region, short_sided, tier, float(xi), float(yi), pin,
                                          green_width_yd=green_width_yd,
                                          front_third_depth_yd=front_third_depth_yd)
    return 1.0 + total


def expected_score(tier, pin, aim_point, wind=False, *,
                    green_width_yd=None, front_third_depth_yd=None,
                    anisotropy_ratio=None, n_std=4.0, n_grid=41):
    """Expected strokes to finish Augusta 12's amateur approach shot.

    tier: one of data.TIERS (0/5/10/15/20). pin: one of data.PINS
    ("left"/"center"/"sunday"). aim_point: (x, y) yards in the tee-shot frame
    the golfer aims at -- not necessarily the pin; CONTEXT.md's aim point is
    chosen to minimize this function.

    wind: bool. When True, applies data.WIND's carry penalty (shortens the
    mean landing distance) and dispersion inflation (widens both oval axes),
    MODELED with a stated sensitivity range (Anchor 6 is narrative only).
    Both the carry penalty and the dispersion inflation apply identically to
    the mishit mixture's two components (see mishit_mixture_params): the
    carry penalty shifts both components' means by the same amount, and the
    dispersion inflation scales the shared sigma_solid/sigma_l both
    components use.

    green_width_yd/front_third_depth_yd/anisotropy_ratio: override the
    published-range defaults (data.HOLE, data.ANISOTROPY) instead of a
    single buried constant; None uses each range's midpoint (or, for
    anisotropy, data.ANISOTROPY["ratio"]).

    Rev 6 (Sunny's finding): the distance axis is a two-component mixture,
    not one symmetric Gaussian (see mishit_mixture_params) -- this function
    is the mixture-weighted sum of two score_for_oval calls, one for each
    component (mean_shift_y unshifted for the solid strike, shifted an
    additional -k_mis for the mishit), each with the SAME sigma_solid/
    sigma_l (the mixture only shifts the mishit component's mean, never its
    spread).
    """
    sigma_solid, sigma_l, p_mis, k_mis = mishit_mixture_params(tier, anisotropy_ratio)
    mean_shift_y = 0.0
    if wind:
        mean_shift_y = -data.WIND["carry_penalty_yd"]
        sigma_solid = sigma_solid * data.WIND["dispersion_inflation"]
        sigma_l = sigma_l * data.WIND["dispersion_inflation"]

    score_solid = score_for_oval(sigma_solid, sigma_l, tier, pin, aim_point, mean_shift_y,
                                  green_width_yd=green_width_yd,
                                  front_third_depth_yd=front_third_depth_yd,
                                  n_std=n_std, n_grid=n_grid)
    if p_mis <= 0.0:
        return score_solid
    score_mis = score_for_oval(sigma_solid, sigma_l, tier, pin, aim_point, mean_shift_y - k_mis,
                                green_width_yd=green_width_yd,
                                front_third_depth_yd=front_third_depth_yd,
                                n_std=n_std, n_grid=n_grid)
    return (1.0 - p_mis) * score_solid + p_mis * score_mis
