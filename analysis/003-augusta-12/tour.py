"""Tour-tier analytic surface for release 003's validation gate (issue #9).

model.py's tier-facing functions (oval_for_tier, score_for_oval,
expected_score) gate on `tier in data.TIERS`, and data.TIERS is fixed to the
amateur ladder ([0, 5, 10, 15, 20]) so #8's optimizer work sees a
byte-for-byte-unchanged amateur surface -- see data.py's Anchor 7 append
block for why the Tour entry there is a self-contained dict rather than a
new key merged into the amateur tables.

This module runs the Tour oval through the SAME three-step construction
(data.py's Anchor-7 inversion -> anisotropy split -> hole-geometry
placement) without touching model.py or data.TIERS:

  1. Radial miss scale: data.TOUR["sigma_iso_ft"] (Anchor 7's direct
     matched proximity+GIR pair at 150-175 yd, the band containing the
     155-yd shot).
  2. Anisotropy split: tour_oval() below, the identical variance-preserving
     formula model.oval_for_tier() uses, sourced from data.TOUR's Broadie
     pro ratio instead of the amateur ANISOTROPY constant.
  3. Hole placement: tour_score_for_oval() below reuses model.region_at
     verbatim (it takes no tier argument -- hazard geometry does not depend
     on skill tier) and mirrors model.py's _green_strokes /
     _recovery_strokes / _creek_strokes / _region_strokes formulas exactly,
     substituting data.TOUR's rates for the amateur THREE_PUTT_RATE /
     UP_AND_DOWN_PCT dict lookups those functions perform.

Any change here is additive to the package; model.py, data.TIERS, and every
amateur dict in data.py are read-only from this module's point of view.
"""

from math import exp, sqrt

import numpy as np

import data
import model


def tour_oval(anisotropy_ratio=None, shot_yd=data.TEE_SHOT_YD):
    """(sigma_distance_yd, sigma_line_yd) for the Tour tier.

    Identical math to model.oval_for_tier: total variance is preserved
    (sigma_d**2 + sigma_l**2 == 2 * sigma_iso**2), sourced from
    data.TOUR["sigma_iso_ft"] scaled to shot_yd rather than the amateur
    data.SIGMA_ISO_FT table.
    """
    ratio = data.TOUR["anisotropy"]["ratio"] if anisotropy_ratio is None else anisotropy_ratio
    sigma_iso_yd = (data._K_TOUR_PER_YD * shot_yd) / model.FT_PER_YD
    sigma_l = sigma_iso_yd * sqrt(2.0 / (ratio ** 2 + 1.0))
    sigma_d = ratio * sigma_l
    return sigma_d, sigma_l


def tour_mishit_mixture_params(anisotropy_ratio=None, shot_yd=data.TEE_SHOT_YD):
    """(sigma_solid_d_yd, sigma_l_yd, p_mis, k_mis_yd): the Tour-tier
    counterpart to model.mishit_mixture_params, still using rev 6's
    total-second-moment-preservation algebra (unlike the amateur tiers,
    which rev 7 moved to a GIR-anchored construction -- the Tour mixture is
    out of that pass's scope; see data.TOUR_MISHIT_SHORT_FRAC's own comment
    for why), sourced from tour_oval's own sigma_d instead of the amateur
    oval_for_tier, and data.TOUR_MISHIT_PCT (a single scalar, far below the
    amateur tiers' own lowest figure) in place of the amateur tier-keyed
    data.MISHIT_PCT dict. data.TOUR_MISHIT_SHORT_FRAC (frozen at the rev 6
    value, 0.15) is used here instead of the amateur data.MISHIT_SHORT_FRAC
    (retuned to 0.25 by rev 7) -- the two were shared through rev 6, when
    both used the same algebra and value; decoupled in rev 7 so retuning
    the amateur mixture's own shape cannot silently move the Tour season-
    mean gate (ADR 0002, must-pass, no xfail) through a shared constant."""
    sigma_d, sigma_l = tour_oval(anisotropy_ratio, shot_yd)
    p_mis = data.TOUR_MISHIT_PCT
    k_mis = data.TOUR_MISHIT_SHORT_FRAC * shot_yd
    sigma_solid_sq = sigma_d ** 2 - p_mis * k_mis ** 2
    if sigma_solid_sq <= 0.0:
        raise ValueError(
            f"tour mishit mixture second-moment equation has no real solution: "
            f"sigma_d={sigma_d:.4f} yd, p_mis={p_mis}, k_mis={k_mis:.4f} yd"
        )
    sigma_solid = sqrt(sigma_solid_sq)
    return sigma_solid, sigma_l, p_mis, k_mis


def tour_putt_probabilities(dist_ft):
    """(p1, p2, p3): probability of holing out in one, two, or three-plus
    putts from dist_ft, PGA Tour tier.

    ANCHORED directly from Anchor 8 (docs/sources/003_Source_Log.md#anchor-8,
    Golfing Focus/Broadie, corroborated by Golf.com): data.TOUR_MAKE_PCT_BY_FT
    interpolated for p1, data.TOUR_THREE_PUTT_PCT_BY_FT (0 below 5 ft, per
    the log) interpolated for p3, p2 the remainder. Replaces the release's
    original invented `1.5 + 0.012*ft` curve, which priced a Tour player at
    roughly 1.6 putts from 3 ft against a published 96% make rate there."""
    p1 = model._lerp_table(data.TOUR_MAKE_PCT_BY_FT, dist_ft)
    p3 = 0.0 if dist_ft <= 5.0 else model._lerp_table(data.TOUR_THREE_PUTT_PCT_BY_FT, dist_ft)
    p2 = max(0.0, 1.0 - p1 - p3)
    return p1, p2, p3


def _tour_green_strokes(dist_to_pin_ft):
    """Mirrors model._green_strokes exactly, using tour_putt_probabilities
    instead of the amateur putt_probabilities(tier, ...)."""
    p1, p2, p3 = tour_putt_probabilities(dist_to_pin_ft)
    return p1 + 2.0 * p2 + 3.0 * p3


def _tour_recovery_strokes(is_short_sided, sand, trouble=False, overshoot_yd=0.0, far_short_yd=0.0):
    """Mirrors model._recovery_strokes exactly, using data.TOUR's own
    recovery rates instead of data.UP_AND_DOWN_PCT[tier] (Anchor 10, this
    pass: a bunker miss uses data.TOUR["sand_save_pct"], every other
    non-sand miss uses data.TOUR["scrambling_pct"] -- previously both drew
    from a single anchorless data.TOUR["up_and_down_pct"]=0.50), including
    the distance falloff on overshoot_yd (#8's long_trouble fix): deeper
    misses past the buffer blend toward _tour_creek_strokes's hazard-like
    price over data.LONG_TROUBLE_FALLOFF_YD, same as the amateur surface.
    Also uses data.TOUR["missed_up_and_down_strokes"] (Anchor 10, derived)
    in place of the shared amateur data.MISSED_UP_AND_DOWN_STROKES; the
    amateur path (model._recovery_strokes) is untouched and keeps using
    data.MISSED_UP_AND_DOWN_STROKES.

    data.ROUGH_RECOVERY_EASE (the amateur path's MODELED "non-sand is a bit
    easier than sand" multiplier, applied on top of a single shared
    up-and-down rate) is NOT applied here: TOUR_SCRAMBLING_PCT and
    TOUR_SAND_SAVE_PCT are now two directly anchored figures with the
    sand-vs-non-sand gap already built in (0.58 vs 0.50), so layering the
    amateur tier's own MODELED easing multiplier on top would double-count
    that gap.

    far_short_yd (short_fairway legs only, region-geometry fix): mirrors
    model._recovery_strokes's own far_short_yd blend exactly, fading this
    leg's up-and-down odds toward zero as distance short of the creek
    band's own near edge grows (data.SHORT_FAIRWAY_FALLOFF_YD), converging
    on data.TOUR["missed_up_and_down_strokes"] rather than a hazard-like
    price -- the Tour-specific "recovery didn't work" ceiling, not the
    shared amateur one."""
    updown = data.TOUR["sand_save_pct"] if sand else data.TOUR["scrambling_pct"]
    if trouble:
        updown = updown * data.LONG_TROUBLE_UPDOWN_MULT
    e = updown * 2.0 + (1.0 - updown) * data.TOUR["missed_up_and_down_strokes"]
    if is_short_sided:
        e *= data.SHORT_SIDE_PENALTY
    if trouble and overshoot_yd > 0.0:
        hazard_like = _tour_creek_strokes(is_short_sided)
        blend = 1.0 - exp(-overshoot_yd / data.LONG_TROUBLE_FALLOFF_YD)
        e = e * (1.0 - blend) + hazard_like * blend
    if far_short_yd > 0.0:
        ceiling = data.TOUR["missed_up_and_down_strokes"] * (data.SHORT_SIDE_PENALTY if is_short_sided else 1.0)
        blend = 1.0 - exp(-far_short_yd / data.SHORT_FAIRWAY_FALLOFF_YD)
        e = e * (1.0 - blend) + ceiling * blend
    return e


def _tour_creek_strokes(is_short_sided):
    """Mirrors model._creek_strokes exactly."""
    return data.CREEK_PENALTY_STROKES + _tour_recovery_strokes(is_short_sided, sand=False)


def _tour_short_fairway_strokes(is_short_sided, far_short_yd):
    """Mirrors model._short_fairway_strokes exactly (rev 5, issue #8's
    pitch-over-water risk fix), using data.TOUR_PITCH_OVER_WATER_DUNK_PCT
    (a single scalar, not a tier-keyed dict) in place of the amateur
    data.PITCH_OVER_WATER_DUNK_PCT[tier] lookup.

    Expected strokes = (1 - p) * recovery + p * (CREEK_PENALTY_STROKES + 1.0
    + recovery_after_drop) -- see model._short_fairway_strokes's docstring
    for the full reasoning behind each term."""
    p = data.TOUR_PITCH_OVER_WATER_DUNK_PCT
    recovery = _tour_recovery_strokes(is_short_sided, sand=False, far_short_yd=far_short_yd)
    recovery_after_drop = _tour_recovery_strokes(is_short_sided, sand=False)
    dunk = data.CREEK_PENALTY_STROKES + 1.0 + recovery_after_drop
    return (1.0 - p) * recovery + p * dunk


def _tour_region_strokes(region, is_short_sided, x, y, pin, *,
                          green_width_yd=None, front_third_depth_yd=None):
    """Mirrors model._region_strokes exactly, dispatching to the _tour_*
    pricing helpers above instead of the tier-keyed amateur ones."""
    if region == "green":
        p = data.PINS[pin]
        dist_to_pin_ft = sqrt((x - p["x"]) ** 2 + (y - p["y"]) ** 2) * model.FT_PER_YD
        return _tour_green_strokes(dist_to_pin_ft)
    if region == "creek":
        return _tour_creek_strokes(is_short_sided)
    if region in ("front_bunker", "back_bunker"):
        return _tour_recovery_strokes(is_short_sided, sand=True)
    if region == "long_trouble":
        geom = model._resolve_geometry(green_width_yd, front_third_depth_yd)
        overshoot_yd = model._long_trouble_overshoot_yd(x, y, geom)
        return _tour_recovery_strokes(is_short_sided, sand=False, trouble=True, overshoot_yd=overshoot_yd)
    if region == "short_fairway":
        geom = model._resolve_geometry(green_width_yd, front_third_depth_yd)
        far_short_yd = model._short_fairway_overshoot_yd(x, y, geom)
        return _tour_short_fairway_strokes(is_short_sided, far_short_yd)
    # long_rough, greenside_rough: plain non-sand Tour scrambling rate
    # (data.TOUR["scrambling_pct"]), no penalty stroke.
    return _tour_recovery_strokes(is_short_sided, sand=False)


def tour_score_for_oval(sigma_d_yd, sigma_l_yd, pin, aim_point, mean_shift_y=0.0, *,
                         green_width_yd=None, front_third_depth_yd=None,
                         n_std=4.0, n_grid=41):
    """Mirrors model.score_for_oval's truncated-Gaussian product-grid
    integration exactly, routed through _tour_region_strokes so the Tour
    tier's pricing never touches the amateur-only THREE_PUTT_RATE /
    UP_AND_DOWN_PCT tables. See model.score_for_oval's docstring for the
    method; this is the same grid, same weighting, same +1.0 approach-stroke
    convention."""
    if pin not in data.PINS:
        raise KeyError(f"unknown pin {pin!r}; expected one of {sorted(data.PINS)}")
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
            region, short_sided = model.region_at(float(xi), float(yi), pin,
                                                    green_width_yd=green_width_yd,
                                                    front_third_depth_yd=front_third_depth_yd)
            total += w * _tour_region_strokes(region, short_sided, float(xi), float(yi), pin,
                                               green_width_yd=green_width_yd,
                                               front_third_depth_yd=front_third_depth_yd)
    return 1.0 + total


def tour_expected_score(pin, aim_point, wind=False, *,
                         green_width_yd=None, front_third_depth_yd=None,
                         anisotropy_ratio=None, n_std=4.0, n_grid=41):
    """Tour-tier expected strokes at Augusta 12, mirroring
    model.expected_score's wind handling exactly (data.WIND's carry penalty
    and dispersion inflation, the same amateur-sourced narrative-anchored
    constants, applied to the Tour tier as a MODELED extension -- Anchor 6
    is a narrative anchor only and was never tier-specific).

    Rev 6 (Sunny's finding): mirrors model.expected_score's mishit-mixture
    change exactly -- the mixture-weighted sum of two tour_score_for_oval
    calls (tour_mishit_mixture_params's solid-strike and mishit components)
    instead of one, using data.TOUR_MISHIT_PCT in place of the amateur
    tier-keyed data.MISHIT_PCT."""
    sigma_solid, sigma_l, p_mis, k_mis = tour_mishit_mixture_params(anisotropy_ratio)
    mean_shift_y = 0.0
    if wind:
        mean_shift_y = -data.WIND["carry_penalty_yd"]
        sigma_solid = sigma_solid * data.WIND["dispersion_inflation"]
        sigma_l = sigma_l * data.WIND["dispersion_inflation"]
    score_solid = tour_score_for_oval(sigma_solid, sigma_l, pin, aim_point, mean_shift_y,
                                       green_width_yd=green_width_yd,
                                       front_third_depth_yd=front_third_depth_yd,
                                       n_std=n_std, n_grid=n_grid)
    if p_mis <= 0.0:
        return score_solid
    score_mis = tour_score_for_oval(sigma_solid, sigma_l, pin, aim_point, mean_shift_y - k_mis,
                                     green_width_yd=green_width_yd,
                                     front_third_depth_yd=front_third_depth_yd,
                                     n_std=n_std, n_grid=n_grid)
    return (1.0 - p_mis) * score_solid + p_mis * score_mis


# ---------------------------------------------------------------------------
# Season-realistic pin rotation and wind frequency (issue #9). Both are
# MODELED: the source log has no published pin-selection frequency or
# wind-frequency figure for hole 12. Weights are stated here, used
# identically by the analytic weighted-average surface and by
# montecarlo.py's season simulation, so the two paths are compared on the
# same assumed rotation rather than two different guesses.
#
# Rotation rationale: Masters tradition is widely reported (golf broadcasts,
# not this release's source log) to reserve the back-right "Sunday" hole
# location for the final round; the other three rounds use the more
# traditional left/center locations. Modeled as 1 of 4 rounds on the Sunday
# pin (25%), the remaining 3 rounds split evenly between left and center
# (37.5% each) absent any published split between them.
# ---------------------------------------------------------------------------

PIN_ROTATION_WEIGHTS = {"left": 0.375, "center": 0.375, "sunday": 0.25}  # MODELED, stated weights, no log anchor

# Amen Corner's wind is ANCHORED as a narrative fact (Anchor 6: the tee sits
# sheltered, the green is exposed, "up to a four-club differential"; 2019's
# final-round gusts hit "around 20 mph"), but the log gives no figure for how
# OFTEN meaningful wind is present at hole 12 across a season. MODELED at
# 35%, i.e. a bit over one round in three -- disclosed, not measured.
WIND_FREQUENCY = 0.35  # MODELED, stated weight, no log anchor
WIND_FREQUENCY_RANGE = (0.2, 0.5)  # sensitivity band used by the sensitivity-pass test


def season_weights(pin_rotation=None, wind_frequency=None):
    """(pin, wind) -> probability, the full season scenario weighting used
    by both the analytic weighted average and the MC season simulation."""
    rotation = PIN_ROTATION_WEIGHTS if pin_rotation is None else pin_rotation
    wf = WIND_FREQUENCY if wind_frequency is None else wind_frequency
    weights = {}
    for pin, p_pin in rotation.items():
        weights[(pin, True)] = p_pin * wf
        weights[(pin, False)] = p_pin * (1.0 - wf)
    return weights


# ---------------------------------------------------------------------------
# Tour aim policy (issue #9's near-miss fix, plus a second-pass refinement).
# The season gate originally modeled every Tour shot as aimed straight at
# the flag, at every pin -- including "sunday," this release's own sucker
# pin -- and overshot the published 3.27-3.28 all-time scoring average at
# 3.443. Real Tour play does not aim dead at every flag as a matter of
# course; playing away from a dangerous pin is baseline course-management
# doctrine, the exact same logic #8's amateur optimizer already applies.
#
# First pass ("optimal"): instead of (pin_x, pin_y), Tour shots aim at
# optimizer.optimize_aim_tour's optimal aim point for that (pin, wind)
# state. This roughly halved the season-mean miss but flipped it from an
# overshoot to an undershoot, and a validation pass found a side effect: an
# always-safest aim policy suppresses the simulated birdie rate well below
# the historical one, since it never plays close enough to a fair pin to
# create a look at birdie.
#
# Second pass ("attack_when_fair," this pass, after the left-pin
# reposition): a pin the optimizer itself finds nearly fair to attack
# (small delta between playing the flag and playing the computed optimum)
# should actually be played at the flag -- bailing off a pin that costs
# almost nothing to attack is not real course management, it is just extra
# caution the model was applying uniformly. TOUR_ATTACK_WHEN_FAIR_
# THRESHOLD_STROKES gates this: MODELED, mirrors optimizer.
# TOSSUP_THRESHOLD_STROKES (0.05) as its floor, stated sensitivity range
# (0.05, 0.10). Every Tour (pin, wind) state's own delta (see
# outputs/003_results.csv-style verdicts, but for the Tour tier) is checked
# once and cached; states whose delta clears the threshold still bail to
# the optimizer's safer point, exactly as "optimal" already did.
#
# The optimizer search is expensive (a two-stage grid search at verdict
# resolution), so each (pin, wind) state's full Verdict (aim point AND
# delta, needed by "attack_when_fair") is computed once and cached -- there
# are only 6 states total (3 pins x 2 wind states), reused across every
# hole play in both the analytic weighted mean and the MC season
# simulation.
# ---------------------------------------------------------------------------

TOUR_ATTACK_WHEN_FAIR_THRESHOLD_STROKES = 0.08   # MODELED, stated sensitivity range (0.05, 0.10)
TOUR_ATTACK_WHEN_FAIR_THRESHOLD_RANGE = (0.05, 0.10)

_TOUR_VERDICT_CACHE = {}


def clear_tour_aim_cache():
    """Test/sensitivity-sweep helper: clears the cached optimizer-verdict
    lookup. Needed whenever a caller monkeypatches a data.* constant that
    feeds tour_expected_score's pricing (e.g. the LONG_TROUBLE_* sensitivity
    tests) and wants the cached verdict recomputed under the new value
    rather than reused from a prior call made under the defaults."""
    _TOUR_VERDICT_CACHE.clear()


def tour_optimal_verdict(pin, wind):
    """The Tour-tier optimizer's full Verdict (aim offsets, score_optimum,
    score_at_pin, delta) for (pin, wind), cached after the first call.
    Import of optimizer is local (deferred to call time) rather than at
    module load: optimizer.py does `import tour` at its own module level to
    reach tour_expected_score for optimize_aim_tour, so a top-level `import
    optimizer` here would be a circular import; by the time this function is
    actually called, both modules have already finished loading either
    way."""
    key = (pin, wind)
    if key not in _TOUR_VERDICT_CACHE:
        import optimizer
        _TOUR_VERDICT_CACHE[key] = optimizer.optimize_aim_tour(pin, wind)
    return _TOUR_VERDICT_CACHE[key]


def tour_optimal_aim(pin, wind):
    """The Tour-tier optimizer's aim point (x, y yd, tee-shot frame) for
    (pin, wind) -- tour_optimal_verdict's aim offsets applied to the pin's
    own coordinates."""
    v = tour_optimal_verdict(pin, wind)
    p = data.PINS[pin]
    return p["x"] + v.lateral_offset_yd, p["y"] + v.carry_adjustment_yd


def tour_aim_point(pin, wind, aim_policy="attack_when_fair",
                    attack_when_fair_threshold=TOUR_ATTACK_WHEN_FAIR_THRESHOLD_STROKES):
    """Resolve an aim point (x, y yd) for `pin`/`wind` under one of four
    policies: "attack_when_fair" (this pass's default -- tour_optimal_aim's
    point when the optimizer's own delta exceeds attack_when_fair_threshold,
    the flag itself when it does not, see the module comment above),
    "optimal" (always tour_optimal_aim's point, issue #9's first-pass fix),
    "pin" (aim straight at the flag, the original pre-fix behavior), or
    "center" (always bail all the way to the center of the green, a
    comparison policy)."""
    p = data.PINS[pin]
    if aim_policy == "pin":
        return p["x"], p["y"]
    if aim_policy == "center":
        c = data.PINS["center"]
        return c["x"], c["y"]
    if aim_policy == "optimal":
        return tour_optimal_aim(pin, wind)
    if aim_policy == "attack_when_fair":
        v = tour_optimal_verdict(pin, wind)
        if v.delta <= attack_when_fair_threshold:
            return p["x"], p["y"]
        return p["x"] + v.lateral_offset_yd, p["y"] + v.carry_adjustment_yd
    raise ValueError(f"unknown aim_policy {aim_policy!r}; expected 'attack_when_fair', "
                      f"'optimal', 'pin', or 'center'")


def tour_season_analytic_mean(pin_rotation=None, wind_frequency=None, aim_policy="attack_when_fair",
                               attack_when_fair_threshold=TOUR_ATTACK_WHEN_FAIR_THRESHOLD_STROKES, **kwargs):
    """Weighted-average analytic expected score across the season pin
    rotation and wind frequency: sum over (pin, wind) of
    weight * tour_expected_score(pin, aim, wind), where `aim` is resolved
    per aim_policy (see tour_aim_point) -- "attack_when_fair" by default
    (this pass's refinement on top of issue #9's near-miss fix): Tour shots
    aim at the flag when the optimizer's own delta says the pin is close
    enough to fair to attack, and at the optimizer's safer point otherwise,
    since a sucker pin played at the pin every time (the original bug) and a
    fair pin bailed off every time (the first-pass fix's own side effect)
    are both not how the real Tour field plays this hole.
    """
    weights = season_weights(pin_rotation, wind_frequency)
    total = 0.0
    for (pin, wind), w in weights.items():
        aim = tour_aim_point(pin, wind, aim_policy, attack_when_fair_threshold)
        total += w * tour_expected_score(pin, aim, wind=wind, **kwargs)
    return total


# ---------------------------------------------------------------------------
# Wind-frequency calibration (issue #9's shape-gate re-target, this pass).
# Anchor 9 gives per-year published scoring averages but no per-year wind-
# frequency figure -- there is no anchor for how often meaningful wind hit
# hole 12 in any specific year, only the season-wide MODELED WIND_FREQUENCY
# default (0.35). Rather than compare a single fixed wind frequency against
# a specific year's shot distribution (comparing two different things: a
# season-average assumption against one year's actual weather), this
# calibrates the ONE disclosed parameter a season model can reasonably fit
# per year -- wind_frequency -- so the analytic season MEAN matches that
# year's published average exactly, then checks whether the resulting
# shot-outcome BUCKETS (birdie/par/bogey/double-or-worse) also match that
# year's published distribution. The mean is fit by construction; the shape
# is not, so a shape match is real evidence, not circular.
# ---------------------------------------------------------------------------

def fit_wind_frequency_for_mean(target_mean, *, pin_rotation=None,
                                 aim_policy="attack_when_fair",
                                 attack_when_fair_threshold=TOUR_ATTACK_WHEN_FAIR_THRESHOLD_STROKES,
                                 lo=0.0, hi=1.0, tol=1e-5, max_iter=60, **kwargs):
    """Bisect for the wind_frequency in [lo, hi] whose
    tour_season_analytic_mean equals target_mean, to within tol strokes.

    Bisection is valid because the season mean is monotonically increasing
    in wind_frequency: wind always worsens expected score at every pin
    (data.WIND's carry penalty shortens the mean shot and its dispersion
    inflation widens the miss pattern; tests/test_model.py's
    test_wind_worsens_expected_score_at_every_pin confirms this holds for
    every tier/pin), so raising the fraction of windy rounds can only raise
    the weighted average, never lower it. Raises ValueError if target_mean
    is not bracketed by wind_frequency in [lo, hi] (should not happen for
    any published hole-12 year average, since those all sit inside the calm-
    to-windy score range this model produces).
    """
    def mean_at(wf):
        return tour_season_analytic_mean(pin_rotation=pin_rotation, wind_frequency=wf,
                                          aim_policy=aim_policy,
                                          attack_when_fair_threshold=attack_when_fair_threshold,
                                          **kwargs)

    f_lo = mean_at(lo) - target_mean
    f_hi = mean_at(hi) - target_mean
    if f_lo > 0.0 or f_hi < 0.0:
        raise ValueError(
            f"target_mean {target_mean} not bracketed by wind_frequency in "
            f"[{lo}, {hi}]: mean(lo)={f_lo + target_mean}, mean(hi)={f_hi + target_mean}")
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        f_mid = mean_at(mid) - target_mean
        if abs(f_mid) < tol:
            return mid
        if f_mid > 0.0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)
