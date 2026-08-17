"""Aim-point optimizer for release 003 (Augusta 12 aim-point piece).

Turns model.expected_score into the verdicts the article's "The move"
section quotes: for each (tier, pin, wind) combination, the aim point that
minimizes expected score, reported as a lateral offset from the pin and a
carry/club adjustment (both signed yards), plus the expected score at that
optimum, at the pin, and the strokes saved between them.

Both aim-plane axes are searched continuously, never snapped to a discrete
club ladder. The #7 review found a genuine one-extra-club benefit at the
Sunday pin for a 20-handicap that reverses past about two clubs; a club
ladder coarse enough to skip that reversal would misreport the verdict, so
the carry dimension is searched the same way the lateral dimension is: a
coarse grid to localize the neighborhood, then coordinate-descent pattern
search to polish it.

Verdict-grade numbers run at elevated integration resolution (VERDICT_N_GRID
= 121 by default). The #7 review measured 0.01-0.03 stroke truncation noise
at model.py's default n_grid=41 near hazard boundaries -- noise on that
order could relabel a genuine tossup as a real edge, or vice versa.
test_optimizer.py checks the optimum stays stable between n_grid=81 and 121.

Search range is bounded, but the reason for the bound has changed since #8's
review. That review found the front-left pin's ("left," front_frac=0.15)
long_trouble price a fixed constant with no distance term, so an unbounded
search kept finding a lower score the farther past the green it aimed --
confirmed by hand up to a 150-yard carry adjustment, i.e. a >300-yard
"approach shot," which is not a real club selection. model.py now prices a
distance falloff on that leg (model._recovery_strokes's overshoot_yd blend,
data.LONG_TROUBLE_FALLOFF_YD): every tier x pin's expected score has a
genuine interior minimum in carry now, confirmed by
tests/test_model.py's test_long_trouble_falloff_gives_every_tier_and_pin_an_
interior_minimum, so the search box is no longer standing between the
optimizer and an unbounded asymptote. DEFAULT_CARRY_RANGE_YD (45 yd) is
still a stated, bounded budget -- a search box should have a limit on
principle, and the box is still what optimize_aim's pattern-search polish
clamps to (see the comment in optimize_aim) -- but it is now sized to
comfortably contain the true interior optimum in every tier x pin x wind
combination this release publishes (confirmed by hand: the front-left pin's
worst case, tier 20 under wind, has its true argmin around 38 yd of carry;
40 yd is close enough to be inside the search's own truncation-noise band,
which is why 45 yd is used instead, for real margin), rather than being a
deliberately tight cap against a runaway. hit_search_boundary() still exists
and is still
checked by build_outputs.py -- a future model or geometry change could
reintroduce a combination whose true optimum sits outside this box, and the
flag is how that would be caught -- but it is expected to report zero rows
against this release's own model and data.
"""

from collections import namedtuple

import numpy as np

import data
import model
import tour

Verdict = namedtuple("Verdict", [
    "lateral_offset_yd",    # aim_x - pin_x, signed yd; positive = toward Sunday/right
    "carry_adjustment_yd",  # aim_y - pin_y, signed yd; positive = long
    "score_optimum",        # expected score at the optimal aim point
    "score_at_pin",         # expected score aiming directly at the pin
    "delta",                # score_at_pin - score_optimum: strokes saved by moving off the pin
])

# Elevated resolution for verdict-grade numbers (module docstring; #7 review).
VERDICT_N_GRID = 121
# The pair test_optimizer.py's n_grid-stability test compares.
STABILITY_N_GRID_PAIR = (81, 121)
# Cheaper resolution used only to localize the neighborhood in stage 1 of the
# search (position only, never the reported score); a wrong catchment basin
# here would need noise on the order of the coarse_step_yd itself, far above
# the review's 0.01-0.03 stroke band, so this is safe even though it is not
# the verdict-grade resolution.
SEARCH_N_GRID = 41

# A recommendation "flips" from attack-the-pin to bail-to-center-of-green
# once the strokes saved by bailing clears this threshold. Set comfortably
# above the review's 0.01-0.03 stroke truncation-noise band at n_grid=41 (the
# review's own phrasing: "the optimizer's tossup-band threshold should sit
# comfortably above this noise band, or the default resolution should go
# up" -- this release does both).
TOSSUP_THRESHOLD_STROKES = 0.05

DEFAULT_LATERAL_RANGE_YD = 20.0
DEFAULT_CARRY_RANGE_YD = 45.0
DEFAULT_COARSE_STEP_YD = 2.0
DEFAULT_REFINE_TOL_YD = 0.05

# Sensitivity ranges the flip-set check sweeps, matching CONTEXT.md/the
# spec's testing decisions verbatim: the anisotropy ratio (data.ANISOTROPY)
# and the green-depth range. Only front_third_depth_yd is exposed as an
# overridable geometry parameter on model.expected_score (green_width_yd is
# the other override, but the spec names "green-depth," not width), so that
# is the depth range swept here.
FLIP_SENSITIVITY_ANISOTROPY_RANGE = data.ANISOTROPY["range"]
FLIP_SENSITIVITY_DEPTH_RANGE_YD = data.HOLE["front_third_depth_yd_range"]


def _score(tier, pin, aim, wind, n_grid, **geometry_overrides):
    return model.expected_score(tier, pin, aim, wind=wind, n_grid=n_grid, **geometry_overrides)


def _tour_score(pin, aim, wind, n_grid, **geometry_overrides):
    return tour.tour_expected_score(pin, aim, wind=wind, n_grid=n_grid, **geometry_overrides)


def _center_of_green_offset(pin):
    """(dx, dy) from `pin` to the center-of-green aim point (data.PINS
    "center"'s coordinates), the bailout every optimizer run is checked
    against."""
    p = data.PINS[pin]
    c = data.PINS["center"]
    return c["x"] - p["x"], c["y"] - p["y"]


def center_aim_score(tier, pin, wind=False, *, n_grid=VERDICT_N_GRID, **geometry_overrides):
    """Expected score for `tier` at `pin`'s scoring (short-siding, putt
    distance) when aiming at the center-of-green point instead of the pin --
    the "center-aim (bailout)" column the #7 review's table reports and the
    results CSV reproduces per tier x pin x wind."""
    p = data.PINS[pin]
    c = data.PINS["center"]
    return _score(tier, pin, (c["x"], c["y"]), wind, n_grid, **geometry_overrides)


def _search_aim(score_fn, pin, *,
                 n_grid, search_n_grid, lateral_range_yd, carry_range_yd,
                 coarse_step_yd, refine_tol_yd):
    """Shared two-stage search behind both optimize_aim (amateur, tier-keyed
    via model.expected_score) and optimize_aim_tour (Tour, via
    tour.tour_expected_score). score_fn(dx, dy, ngrid) scores the aim point
    `pin` + (dx, dy) at resolution ngrid -- everything tier/pin/wind/
    geometry-specific is already closed over by the caller's score_fn, so
    this function itself never branches on which surface it is searching.

    See optimize_aim's docstring for the search's own description (coarse
    localization, then a clamped coordinate-descent polish, then the pin and
    center-of-green safety-net candidates); this function is that search,
    factored out so the Tour aim policy (issue #9's near-miss fix) gets the
    exact same search behavior instead of a second, hand-maintained copy.
    """
    def f(dx, dy, ngrid):
        return score_fn(dx, dy, ngrid)

    # Stage 1: coarse localization (cheap resolution, position only).
    lat_offsets = np.arange(-lateral_range_yd, lateral_range_yd + 1e-9, coarse_step_yd)
    carry_offsets = np.arange(-carry_range_yd, carry_range_yd + 1e-9, coarse_step_yd)
    best_dx, best_dy = 0.0, 0.0
    best_coarse = f(0.0, 0.0, search_n_grid)
    for dx in lat_offsets:
        for dy in carry_offsets:
            s = f(float(dx), float(dy), search_n_grid)
            if s < best_coarse:
                best_dx, best_dy, best_coarse = float(dx), float(dy), s

    # Stage 2: coordinate-descent polish at verdict-grade resolution, clamped
    # to the same +/- lateral_range_yd x +/- carry_range_yd box stage 1
    # searched. model.py now prices a real distance falloff on long_trouble
    # (module docstring), so every combination this release publishes has a
    # genuine interior minimum inside the box -- but the clamp stays as a
    # defense-in-depth bound on principle (a search box should have a limit),
    # and hit_search_boundary() below is how a future change that pushes a
    # true optimum back outside the box would be caught rather than silently
    # truncated.
    best_s = f(best_dx, best_dy, n_grid)
    step = coarse_step_yd
    while step > refine_tol_yd:
        improved = False
        for ddx, ddy in ((step, 0.0), (-step, 0.0), (0.0, step), (0.0, -step)):
            nx, ny = best_dx + ddx, best_dy + ddy
            if abs(nx) > lateral_range_yd or abs(ny) > carry_range_yd:
                continue
            ns = f(nx, ny, n_grid)
            if ns < best_s - 1e-9:
                best_dx, best_dy, best_s = nx, ny, ns
                improved = True
        if not improved:
            step /= 2.0

    # Two explicit safety-net candidates, both at verdict-grade resolution,
    # so the reported optimum can never lose to either regardless of
    # whether the grid search happened to land on them: the pin itself
    # (guarantees delta >= 0 even in a genuine tossup, where the coarse
    # search's cheaper resolution could otherwise pick a neighbor that
    # scores fractionally worse once re-evaluated at n_grid) and the
    # center-of-green bailout (the #8 acceptance criterion).
    score_at_pin = f(0.0, 0.0, n_grid)
    if score_at_pin < best_s:
        best_dx, best_dy, best_s = 0.0, 0.0, score_at_pin

    center_dx, center_dy = _center_of_green_offset(pin)
    center_s = f(center_dx, center_dy, n_grid)
    if center_s < best_s:
        best_dx, best_dy, best_s = center_dx, center_dy, center_s

    return Verdict(
        lateral_offset_yd=best_dx,
        carry_adjustment_yd=best_dy,
        score_optimum=best_s,
        score_at_pin=score_at_pin,
        delta=score_at_pin - best_s,
    )


def optimize_aim(tier, pin, wind=False, *,
                  n_grid=VERDICT_N_GRID,
                  search_n_grid=SEARCH_N_GRID,
                  lateral_range_yd=DEFAULT_LATERAL_RANGE_YD,
                  carry_range_yd=DEFAULT_CARRY_RANGE_YD,
                  coarse_step_yd=DEFAULT_COARSE_STEP_YD,
                  refine_tol_yd=DEFAULT_REFINE_TOL_YD,
                  **geometry_overrides):
    """Search the aim plane around `pin` for the (lateral offset, carry
    adjustment) that minimizes model.expected_score(tier, pin, aim, wind,
    **geometry_overrides), for one of the amateur data.TIERS.

    Two-stage search over both axes at once -- lateral offset and carry
    (club) adjustment are optimized jointly, not one dimension snapped to a
    ladder while the other is searched:

      1. Coarse grid localization, evaluated at the cheaper `search_n_grid`
         resolution, over +/- lateral_range_yd x +/- carry_range_yd around
         the pin in coarse_step_yd steps.
      2. Coordinate-descent pattern search from the coarse winner, evaluated
         at the verdict-grade `n_grid` resolution, with a step that shrinks
         by half whenever no neighbor improves, until it falls below
         refine_tol_yd.

    The center-of-green aim point is always evaluated as an explicit extra
    candidate, at the same verdict-grade resolution, and wins if it scores
    better than the polished search result. This guarantees the optimizer
    never reports an aim worse than that bailout, regardless of whether the
    grid search happened to cover it -- the #8 acceptance criterion.

    geometry_overrides are forwarded to model.expected_score (green_width_yd,
    front_third_depth_yd, anisotropy_ratio): the same sensitivity knobs
    flip_set() sweeps.

    Returns a Verdict. See _search_aim for the shared search implementation
    (also used by optimize_aim_tour, the Tour-tier analog below)."""
    pin_x, pin_y = data.PINS[pin]["x"], data.PINS[pin]["y"]

    def score_fn(dx, dy, ngrid):
        return _score(tier, pin, (pin_x + dx, pin_y + dy), wind, ngrid, **geometry_overrides)

    return _search_aim(score_fn, pin, n_grid=n_grid, search_n_grid=search_n_grid,
                        lateral_range_yd=lateral_range_yd, carry_range_yd=carry_range_yd,
                        coarse_step_yd=coarse_step_yd, refine_tol_yd=refine_tol_yd)


def optimize_aim_tour(pin, wind=False, *,
                       n_grid=VERDICT_N_GRID,
                       search_n_grid=SEARCH_N_GRID,
                       lateral_range_yd=DEFAULT_LATERAL_RANGE_YD,
                       carry_range_yd=DEFAULT_CARRY_RANGE_YD,
                       coarse_step_yd=DEFAULT_COARSE_STEP_YD,
                       refine_tol_yd=DEFAULT_REFINE_TOL_YD,
                       **geometry_overrides):
    """Tour-tier analog of optimize_aim: the identical _search_aim two-stage
    search (coarse localization, clamped coordinate-descent polish, pin and
    center-of-green safety-net candidates), scored through
    tour.tour_expected_score instead of model.expected_score(tier, ...).

    Issue #9's Tour-gate near-miss fix: the season Monte Carlo overshot the
    published 3.27-3.28 all-time scoring average at 3.443 while aiming every
    Tour shot straight at the flag. Real Tour play does not do that --
    sucker pins get played away from the hole as doctrine, the same logic
    this optimizer already applies to the amateur tiers -- so tour.py's
    season aim policy calls this (cached per (pin, wind), see
    tour.tour_optimal_aim) instead of aiming dead at the pin.

    Returns a Verdict."""
    pin_x, pin_y = data.PINS[pin]["x"], data.PINS[pin]["y"]

    def score_fn(dx, dy, ngrid):
        return _tour_score(pin, (pin_x + dx, pin_y + dy), wind, ngrid, **geometry_overrides)

    return _search_aim(score_fn, pin, n_grid=n_grid, search_n_grid=search_n_grid,
                        lateral_range_yd=lateral_range_yd, carry_range_yd=carry_range_yd,
                        coarse_step_yd=coarse_step_yd, refine_tol_yd=refine_tol_yd)


def hit_search_boundary(verdict, *, lateral_range_yd=DEFAULT_LATERAL_RANGE_YD,
                         carry_range_yd=DEFAULT_CARRY_RANGE_YD, tol_yd=1.5):
    """True if `verdict`'s aim point sits within tol_yd of the declared
    search box edge on either axis: a signal that optimize_aim's bounded
    polish (see its docstring) landed on the cap rather than an interior
    optimum, so the model's true best lies farther out than the declared
    search box. Before model.py's long_trouble distance falloff (#8's
    finding), this was expected on the front-left pin under wind -- a flat
    price with no falloff meant no interior optimum existed at all, so every
    search capped out. After the falloff fix, every combination this release
    publishes has a genuine interior optimum comfortably inside
    DEFAULT_CARRY_RANGE_YD (confirmed in build_outputs.py's run and by
    tests/test_model.py's interior-minimum regression test), so this
    function is expected to return False everywhere in the published table;
    a True here now would mean a future model or geometry change pushed a
    true optimum back outside the box, which is exactly the case this flag
    exists to catch.

    tol_yd defaults wider than a single refine_tol_yd step (1.5 yd, not
    0.05) so a shallow, near-flat approach to the cap doesn't let the exact
    converged coordinate's yard-or-more drift between n_grid=81 and 121
    dodge the flag at one resolution and not the other."""
    return (abs(abs(verdict.lateral_offset_yd) - lateral_range_yd) < tol_yd or
            abs(abs(verdict.carry_adjustment_yd) - carry_range_yd) < tol_yd)


def verdict_label(verdict, tossup_threshold=TOSSUP_THRESHOLD_STROKES):
    """Classify a Verdict's qualitative recommendation using 002's tossup
    convention (site/tee-shot-distance/tool.html's sandbox band: |delta| <=
    0.05 strokes reads "Either club works here," the same threshold this
    module's TOSSUP_THRESHOLD_STROKES already sets): "either works" when the
    optimum and the at-pin score sit within tossup_threshold strokes of each
    other, "bail" when moving off the pin clears that band by saving
    strokes (delta > threshold, CONTEXT.md's sucker pin), "attack" when
    playing directly at the pin actually beats the reported optimum by more
    than the band (delta < -threshold; optimize_aim's own search always
    evaluates the pin as a candidate, so its own verdicts never produce this
    case, but the check stays generic for a caller-constructed Verdict)."""
    if abs(verdict.delta) <= tossup_threshold:
        return "either works"
    return "bail" if verdict.delta > tossup_threshold else "attack"


# flip_set's own search settings, distinct from VERDICT_N_GRID/SEARCH_N_GRID:
# this check only needs the attack/bail label at each of 5 sensitivity
# points per (tier, pin, wind) combination (150 optimizer runs by default),
# not the published verdict score, so it trades search precision for
# runtime -- a coarser stage-1 grid and a wider coarse step than the
# verdict-grade optimize_aim defaults. TOSSUP_THRESHOLD_STROKES (0.05) still
# sits comfortably above this resolution's truncation noise.
FLIP_SET_N_GRID = 61
FLIP_SET_SEARCH_N_GRID = 21
FLIP_SET_COARSE_STEP_YD = 3.0
FLIP_SET_LATERAL_RANGE_YD = 15.0
FLIP_SET_CARRY_RANGE_YD = 20.0


def flip_set(*, tiers=None, pins=None, winds=(False, True),
             n_grid=FLIP_SET_N_GRID, search_n_grid=FLIP_SET_SEARCH_N_GRID,
             coarse_step_yd=FLIP_SET_COARSE_STEP_YD,
             lateral_range_yd=FLIP_SET_LATERAL_RANGE_YD,
             carry_range_yd=FLIP_SET_CARRY_RANGE_YD,
             corner_only=True,
             tossup_threshold=TOSSUP_THRESHOLD_STROKES,
             **optimize_kwargs):
    """Which (tier, pin, wind) verdicts change their qualitative
    recommendation ("attack" vs "bail," see verdict_label) anywhere inside
    the anisotropy sensitivity range (2:1-3.5:1, data.ANISOTROPY["range"])
    and the green-depth sensitivity range (9-12 yd front-third depth,
    data.HOLE["front_third_depth_yd_range"]) -- the spec's testing decision
    that "the headline verdicts must state which conclusions flip anywhere
    inside" those two ranges.

    corner_only=True (the default) samples the baseline midpoint plus the
    four corners of the (anisotropy, depth) rectangle, rather than a dense
    2D sweep. Both parameters act close to monotonically on expected score
    over their stated ranges (anisotropy trades line spread for distance
    spread at fixed total variance; front-third depth shifts the front/back
    hazard edges directly), so the rectangle's corners bound the range's
    effect on the attack/bail classification without a combinatorial sweep.
    Pass corner_only=False for a denser 5x5 grid instead (25 points per
    tier/pin/wind combination rather than 4); this is an offline/ad hoc
    option, not exercised by the default test.

    n_grid/search_n_grid/coarse_step_yd/lateral_range_yd/carry_range_yd
    default to the cheaper FLIP_SET_* settings above rather than
    optimize_aim's verdict-grade defaults: this check runs 150 optimizer
    calls by default (5 sensitivity points x 30 tier/pin/wind combinations)
    and only needs the attack/bail label at each, not the published score.
    Pass any of them explicitly for a slower, higher-precision sweep.

    Returns a list of dicts, one per combination whose label flips somewhere
    in the sweep: {"tier", "pin", "wind", "baseline_label", "flipped_at":
    [{"anisotropy_ratio", "front_third_depth_yd", "label"}, ...]}. Feeds the
    article's sensitivity disclosure.
    """
    tiers = data.TIERS if tiers is None else tiers
    pins = list(data.PINS) if pins is None else pins
    aniso_lo, aniso_hi = FLIP_SENSITIVITY_ANISOTROPY_RANGE
    depth_lo, depth_hi = FLIP_SENSITIVITY_DEPTH_RANGE_YD
    aniso_mid = data.ANISOTROPY["ratio"]
    depth_mid = 0.5 * (depth_lo + depth_hi)

    if corner_only:
        sweep_points = [(aniso_lo, depth_lo), (aniso_lo, depth_hi),
                         (aniso_hi, depth_lo), (aniso_hi, depth_hi)]
    else:
        aniso_vals = np.linspace(aniso_lo, aniso_hi, 5)
        depth_vals = np.linspace(depth_lo, depth_hi, 5)
        sweep_points = [(float(a), float(d)) for a in aniso_vals for d in depth_vals
                         if not (a == aniso_mid and d == depth_mid)]

    def run(tier, pin, wind, ratio, depth):
        return optimize_aim(tier, pin, wind, n_grid=n_grid, search_n_grid=search_n_grid,
                             coarse_step_yd=coarse_step_yd, lateral_range_yd=lateral_range_yd,
                             carry_range_yd=carry_range_yd, anisotropy_ratio=ratio,
                             front_third_depth_yd=depth, **optimize_kwargs)

    flips = []
    for tier in tiers:
        for pin in pins:
            for wind in winds:
                baseline = run(tier, pin, wind, aniso_mid, depth_mid)
                baseline_label = verdict_label(baseline, tossup_threshold)
                flipped_at = []
                for ratio, depth in sweep_points:
                    v = run(tier, pin, wind, ratio, depth)
                    label = verdict_label(v, tossup_threshold)
                    if label != baseline_label:
                        flipped_at.append({
                            "anisotropy_ratio": ratio,
                            "front_third_depth_yd": depth,
                            "label": label,
                        })
                if flipped_at:
                    flips.append({
                        "tier": tier, "pin": pin, "wind": wind,
                        "baseline_label": baseline_label,
                        "flipped_at": flipped_at,
                    })
    return flips
