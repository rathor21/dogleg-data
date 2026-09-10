"""Monte Carlo validation harness for release 003 (issue #9).

Peer-review artifact, same framing 002's montecarlo.py uses: nothing here
feeds a published chart. It simulates the SAME distributions model.py (and
tour.py, for the Tour tier) integrate analytically -- oval_for_tier's
variance-preserving anisotropy split, rev 6's mishit mixture on top of it
(mishit_mixture_params/tour_mishit_mixture_params: a per-sample coin flip
picks the solid-strike or mishit component, Sunny's finding), data.WIND's
mean shift and dispersion inflation when wind is on -- and prices each
sampled landing point through the SAME region_at classification and
_region_strokes formulas the analytic grid uses per cell. Agreement is
therefore a check on the grid integration, not independent evidence of
anything model.py/tour.py assumes.

Two harnesses:

  simulate_amateur / simulate_tour: per-scenario mean strokes, sampled
    continuously (real-valued strokes per sample, exactly like
    model._region_strokes / tour._tour_region_strokes return), for the
    must-pass "MC reproduces the analytic surface" gate (tests/test_
    montecarlo.py's test_montecarlo_matches_analytic_amateur and
    test_montecarlo_matches_analytic_tour).

  simulate_tour_season: the Tour reproduction gate itself (issue #9's second
    must-pass gate). Samples a pin and a wind state per simulated hole play
    from tour.season_weights (the season-realistic pin rotation and wind
    frequency, both MODELED and disclosed in tour.py), then discretizes each
    play into an INTEGER score: the green leg draws an integer putt count
    from tour.tour_putt_probabilities' anchored (p1, p2, p3) distribution
    (see _sample_putts below, Anchor 8), and any recovery leg (bunker/rough/
    creek/long_trouble/short_fairway) still uses stochastic rounding of its real-valued
    expected-strokes price (see _stochastic_round below), since no anchored
    discrete outcome distribution exists for those legs the way putting now
    has. Reports a real birdie/par/bogey/double-or-worse distribution, not
    just a mean, checked against the 2019 season breakdown and the modern-
    era yearly averages (data source: docs/sources/003_Source_Log.md
    Anchor 4, Anchor 9).
"""

import numpy as np

import data
import model
import tour


def simulate_amateur(tier, pin, aim_point, wind=False, *, n=300_000, rng=None,
                      green_width_yd=None, front_third_depth_yd=None, anisotropy_ratio=None):
    """Mean strokes over n sampled amateur approach shots. Mirrors
    model.expected_score's distributions exactly: model.mishit_mixture_
    params's two-component distance-error mixture (rev 6, Sunny's finding --
    a solid-strike core plus a short mishit tail, drawn per sample here
    rather than integrated analytically), data.WIND's mean shift/dispersion
    inflation when wind=True, region_at for classification, and
    _region_strokes for pricing -- the same functions the analytic grid in
    model.score_for_oval calls per cell, called here per random sample
    instead.
    """
    rng = rng if rng is not None else np.random.default_rng()
    sigma_solid, sigma_l, p_mis, k_mis = model.mishit_mixture_params(tier, anisotropy_ratio)
    mean_shift_y = 0.0
    if wind:
        mean_shift_y = -data.WIND["carry_penalty_yd"]
        sigma_solid = sigma_solid * data.WIND["dispersion_inflation"]
        sigma_l = sigma_l * data.WIND["dispersion_inflation"]
    mean_x, mean_y = aim_point[0], aim_point[1] + mean_shift_y

    is_mishit = rng.random(n) < p_mis
    y_shift = np.where(is_mishit, -k_mis, 0.0)
    ys = rng.normal(mean_y, sigma_solid, n) + y_shift
    xs = rng.normal(mean_x, sigma_l, n)
    total = 0.0
    for xi, yi in zip(xs, ys):
        region, short_sided = model.region_at(float(xi), float(yi), pin,
                                               green_width_yd=green_width_yd,
                                               front_third_depth_yd=front_third_depth_yd)
        total += model._region_strokes(region, short_sided, tier, float(xi), float(yi), pin,
                                        green_width_yd=green_width_yd,
                                        front_third_depth_yd=front_third_depth_yd)
    return 1.0 + total / n


def simulate_tour(pin, aim_point, wind=False, *, n=300_000, rng=None,
                   green_width_yd=None, front_third_depth_yd=None, anisotropy_ratio=None):
    """Tour-tier analog of simulate_amateur, routed through tour.py's
    mishit-mixture and pricing helpers instead of the amateur tier-keyed
    ones."""
    rng = rng if rng is not None else np.random.default_rng()
    sigma_solid, sigma_l, p_mis, k_mis = tour.tour_mishit_mixture_params(anisotropy_ratio)
    mean_shift_y = 0.0
    if wind:
        mean_shift_y = -data.WIND["carry_penalty_yd"]
        sigma_solid = sigma_solid * data.WIND["dispersion_inflation"]
        sigma_l = sigma_l * data.WIND["dispersion_inflation"]
    mean_x, mean_y = aim_point[0], aim_point[1] + mean_shift_y

    is_mishit = rng.random(n) < p_mis
    y_shift = np.where(is_mishit, -k_mis, 0.0)
    ys = rng.normal(mean_y, sigma_solid, n) + y_shift
    xs = rng.normal(mean_x, sigma_l, n)
    total = 0.0
    for xi, yi in zip(xs, ys):
        region, short_sided = model.region_at(float(xi), float(yi), pin,
                                               green_width_yd=green_width_yd,
                                               front_third_depth_yd=front_third_depth_yd)
        total += tour._tour_region_strokes(region, short_sided, float(xi), float(yi), pin,
                                            green_width_yd=green_width_yd,
                                            front_third_depth_yd=front_third_depth_yd)
    return 1.0 + total / n


# ---------------------------------------------------------------------------
# Tour reproduction gate: a season of hole plays, discretized to integer
# scores, checked against both the all-time scoring average (3.27-3.28) and
# the 2019 shot distribution (52 birdies / 200 pars / 38 bogeys / 14
# doubles-or-worse of 304 plays -- Anchor 4).
# ---------------------------------------------------------------------------

def _stochastic_round(mean_val, rng, n):
    """n integer draws whose sample mean converges to mean_val exactly in
    expectation: floor(mean_val) with probability 1-frac, floor(mean_val)+1
    with probability frac, frac = mean_val - floor(mean_val). Used for
    recovery legs (bunker/rough/creek/long_trouble/short_fairway), which have no anchored
    discrete outcome distribution the way putting now does (see
    _sample_putts below) -- only a real-valued expected-strokes price."""
    lo = np.floor(mean_val)
    frac = mean_val - lo
    u = rng.random(n)
    return np.where(u < frac, lo + 1.0, lo)


def _sample_putts(putt_probs, rng, n):
    """n integer putt-count draws (1, 2, or 3) from an explicit (p1, p2, p3)
    distribution (tour.tour_putt_probabilities, Anchor 8). Replaces
    _stochastic_round's implicit "floor(E)/floor(E)+1" two-outcome discretization
    for the green leg: that scheme turned the old floored-at-1.5 putting
    formula's expectation into a one-putt probability of `2 - E`, which
    capped one-putts at 50% from any distance and is the actual mechanism
    behind the pre-fix birdie deficit VALIDATION_NOTES had attributed to aim
    policy. Sampling directly from the anchored (p1, p2, p3) triple lets a
    3-foot putt hole out at its real ~96% rate instead."""
    p1, p2, _p3 = putt_probs
    u = rng.random(n)
    return np.where(u < p1, 1.0, np.where(u < p1 + p2, 2.0, 3.0))


def simulate_tour_season(n=300_000, rng=None, pin_rotation=None, wind_frequency=None,
                          aim_policy="attack_when_fair",
                          attack_when_fair_threshold=None):
    """Simulate n Augusta-12 tour plays across the season pin rotation and
    wind frequency (tour.season_weights). Returns (mean_strokes,
    counts) where counts is {"birdie": int, "par": int, "bogey": int,
    "double_or_worse": int} over n plays, and mean_strokes is the sample
    mean (checked against the published 3.27-3.28 all-time average).

    Each play: sample (pin, wind) from the season weights, sample a landing
    point from tour.tour_mishit_mixture_params's two-component mixture (rev
    6, Sunny's finding: a per-play coin flip on p_mis picks the solid-strike
    or mishit component) around the aim point tour.tour_aim_point resolves
    for that (pin, wind, aim_policy) (wind-shifted/inflated exactly as
    tour.tour_expected_score does), classify it with model.region_at
    (unmodified, tier-agnostic), then discretize tour.py's exact pricing
    formula for that region (_tour_green_strokes for "green",
    _tour_recovery_strokes/_tour_creek_strokes otherwise) via
    _stochastic_round. Total strokes = 1 (tee shot) + [creek penalty, if
    any] + the discretized putts-or-recovery leg.

    aim_policy: "attack_when_fair" (default, this pass's refinement -- Tour
    shots aim at the flag when the optimizer's own delta says the pin is
    close enough to fair to attack, and at optimizer.optimize_aim_tour's
    cached safer point otherwise), "optimal" (issue #9's first-pass fix,
    always the safer point), "pin" (the original pre-fix behavior, always
    the flag), or "center" (always the center-of-green bailout). See
    tour.tour_aim_point. attack_when_fair_threshold defaults to
    tour.TOUR_ATTACK_WHEN_FAIR_THRESHOLD_STROKES when None.
    """
    rng = rng if rng is not None else np.random.default_rng()
    if attack_when_fair_threshold is None:
        attack_when_fair_threshold = tour.TOUR_ATTACK_WHEN_FAIR_THRESHOLD_STROKES
    weights = tour.season_weights(pin_rotation, wind_frequency)
    scenarios = list(weights.keys())
    probs = np.array([weights[s] for s in scenarios])
    probs = probs / probs.sum()
    draw = rng.choice(len(scenarios), size=n, p=probs)

    strokes = np.empty(n)
    for pin_name in {s[0] for s in scenarios}:
        for wind_on in (False, True):
            idx = [i for i, s in enumerate(scenarios) if s == (pin_name, wind_on)]
            if not idx:
                continue
            mask = draw == idx[0]
            m = int(mask.sum())
            if m == 0:
                continue
            sigma_solid, sigma_l, p_mis, k_mis = tour.tour_mishit_mixture_params()
            mean_shift_y = 0.0
            if wind_on:
                mean_shift_y = -data.WIND["carry_penalty_yd"]
                sigma_solid = sigma_solid * data.WIND["dispersion_inflation"]
                sigma_l = sigma_l * data.WIND["dispersion_inflation"]
            aim_x, aim_y = tour.tour_aim_point(pin_name, wind_on, aim_policy, attack_when_fair_threshold)
            mean_x, mean_y = aim_x, aim_y + mean_shift_y
            is_mishit = rng.random(m) < p_mis
            y_shift = np.where(is_mishit, -k_mis, 0.0)
            ys = rng.normal(mean_y, sigma_solid, m) + y_shift
            xs = rng.normal(mean_x, sigma_l, m)

            geom = model._resolve_geometry()
            sub_strokes = np.empty(m)
            for j, (xi, yi) in enumerate(zip(xs, ys)):
                region, short_sided = model.region_at(float(xi), float(yi), pin_name)
                if region == "green":
                    pp = data.PINS[pin_name]
                    dist_ft = ((xi - pp["x"]) ** 2 + (yi - pp["y"]) ** 2) ** 0.5 * model.FT_PER_YD
                    putt_probs = tour.tour_putt_probabilities(dist_ft)
                    putts = _sample_putts(putt_probs, rng, 1)[0]
                    sub_strokes[j] = 1.0 + putts
                elif region == "creek":
                    mean_leg = tour._tour_recovery_strokes(short_sided, sand=False)
                    leg = _stochastic_round(mean_leg, rng, 1)[0]
                    sub_strokes[j] = 1.0 + data.CREEK_PENALTY_STROKES + leg
                elif region in ("front_bunker", "back_bunker"):
                    mean_leg = tour._tour_recovery_strokes(short_sided, sand=True)
                    leg = _stochastic_round(mean_leg, rng, 1)[0]
                    sub_strokes[j] = 1.0 + leg
                elif region == "long_trouble":
                    overshoot_yd = model._long_trouble_overshoot_yd(float(xi), float(yi), geom)
                    mean_leg = tour._tour_recovery_strokes(short_sided, sand=False, trouble=True,
                                                            overshoot_yd=overshoot_yd)
                    leg = _stochastic_round(mean_leg, rng, 1)[0]
                    sub_strokes[j] = 1.0 + leg
                elif region == "short_fairway":
                    far_short_yd = model._short_fairway_overshoot_yd(float(xi), float(yi), geom)
                    mean_leg = tour._tour_short_fairway_strokes(short_sided, far_short_yd)
                    leg = _stochastic_round(mean_leg, rng, 1)[0]
                    sub_strokes[j] = 1.0 + leg
                else:  # long_rough, greenside_rough
                    mean_leg = tour._tour_recovery_strokes(short_sided, sand=False)
                    leg = _stochastic_round(mean_leg, rng, 1)[0]
                    sub_strokes[j] = 1.0 + leg
            strokes[mask] = sub_strokes

    counts = {
        "birdie": int((strokes <= 2).sum()),
        "par": int((strokes == 3).sum()),
        "bogey": int((strokes == 4).sum()),
        "double_or_worse": int((strokes >= 5).sum()),
    }
    return float(strokes.mean()), counts
