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
"""

from math import exp, pi, sqrt

import numpy as np

import data

FT_PER_YD = 3.0


# ---------------------------------------------------------------------------
# Step 2: anisotropy split (and its inverse, for the round-trip test).
# ---------------------------------------------------------------------------

def oval_for_tier(tier, anisotropy_ratio=None, shot_yd=data.TEE_SHOT_YD):
    """(sigma_distance_yd, sigma_line_yd): the dispersion oval for tier at
    shot_yd yards.

    Splits data.SIGMA_ISO_FT[tier] (Step 1, an isotropic radial sigma in
    feet) into anisotropic distance/line axes using anisotropy_ratio
    (default data.ANISOTROPY["ratio"] = 3.0; sensitivity range
    data.ANISOTROPY["range"], Anchor 2 -- a parameter, never a buried
    constant). Total variance is preserved: sigma_d**2 + sigma_l**2 ==
    2 * sigma_iso**2, so widening the ratio redistributes spread between axes
    without changing the golfer's overall miss magnitude.
    """
    ratio = data.ANISOTROPY["ratio"] if anisotropy_ratio is None else anisotropy_ratio
    sigma_iso_yd = data.sigma_isotropic_ft(tier, shot_yd) / FT_PER_YD
    sigma_l = sigma_iso_yd * sqrt(2.0 / (ratio ** 2 + 1.0))
    sigma_d = ratio * sigma_l
    return sigma_d, sigma_l


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

    Returns (region, is_short_sided). region is one of "green",
    "front_bunker", "back_bunker", "creek", "long_trouble", "long_rough",
    "greenside_rough". "long_trouble" is a miss that clears the back bunkers
    by data.LONG_TROUBLE_BUFFER_YD or more -- Anchor 3's azalea-lined ledge,
    priced worse than plain rough (see _recovery_strokes) rather than folded
    into "long_rough" at the same price, which previously let overclubbing
    the green look like a free way to dodge the creek.
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
        return "creek", is_short_sided

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


def _green_strokes(tier, dist_to_pin_ft):
    """Expected strokes to finish from on the green: expected putts only (the
    approach stroke itself is charged once, in score_for_oval).

    Putts-by-distance shape is MODELED -- no published putts-by-distance-
    and-handicap curve exists in the source log -- scaled by the tier's
    ANCHORED three-putt rate (data.THREE_PUTT_RATE, Anchor 5) so a tier that
    three-putts more often averages more putts overall, folding the one
    genuinely anchored short-game figure into the pricing.
    """
    base_putts = min(3.0, max(1.0, 1.5 + 0.012 * dist_to_pin_ft))  # MODELED putts-by-distance shape
    tier_scale = 1.0 + data.THREE_PUTT_RATE[tier]  # ANCHORED anchor folded in as a multiplicative adjustment
    return base_putts * tier_scale


def _recovery_strokes(tier, is_short_sided, sand, trouble=False, overshoot_yd=0.0):
    """Expected strokes to finish from a greenside miss (bunker, rough, or
    long trouble).

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
    return e


def _creek_strokes(tier, is_short_sided):
    """Expected strokes after finding the creek: a penalty stroke
    (data.CREEK_PENALTY_STROKES, a drop-and-replay convention, same spirit as
    002's OB_COST) plus a recovery leg from the drop area, priced like a
    non-sand recovery."""
    return data.CREEK_PENALTY_STROKES + _recovery_strokes(tier, is_short_sided, sand=False)


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
    # long_rough, greenside_rough
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

    green_width_yd/front_third_depth_yd/anisotropy_ratio: override the
    published-range defaults (data.HOLE, data.ANISOTROPY) instead of a
    single buried constant; None uses each range's midpoint (or, for
    anisotropy, data.ANISOTROPY["ratio"]).
    """
    sigma_d, sigma_l = oval_for_tier(tier, anisotropy_ratio)
    mean_shift_y = 0.0
    if wind:
        mean_shift_y = -data.WIND["carry_penalty_yd"]
        sigma_d = sigma_d * data.WIND["dispersion_inflation"]
        sigma_l = sigma_l * data.WIND["dispersion_inflation"]

    return score_for_oval(sigma_d, sigma_l, tier, pin, aim_point, mean_shift_y,
                           green_width_yd=green_width_yd,
                           front_third_depth_yd=front_third_depth_yd,
                           n_std=n_std, n_grid=n_grid)
