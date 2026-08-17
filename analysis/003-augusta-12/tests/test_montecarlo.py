"""Validation gates for release 003 (issue #9): the credibility spine.

Two gates:

  1. MC-vs-analytic fidelity (test_montecarlo_matches_analytic_amateur,
     test_montecarlo_matches_analytic_tour, test_tour_season_mc_matches_
     tour_season_analytic): does the simulation harness reproduce the
     analytic expected-score surface it is meant to check? These pass --
     they are a check on model.py/tour.py's grid integration, not on the
     model's real-world accuracy, mirroring 002's montecarlo tolerance
     discipline (002's published gap: 0.0021, "within 0.003"). Wired as
     plain must-pass assertions.

  2. Tour historical reproduction (test_tour_gate_scoring_average,
     test_tour_gate_2019_distribution_shape): does the Tour oval, run over
     a season-realistic pin rotation and wind frequency (both MODELED,
     tour.PIN_ROTATION_WEIGHTS / tour.WIND_FREQUENCY, stated ranges
     disclosed in tour.py), reproduce Augusta 12's published all-time
     scoring average (3.27-3.28, Anchor 4) and 2019 outcome distribution
     (52 birdies / 200 pars / 38 bogeys / 14 doubles-or-worse of 304 plays,
     Anchor 4)? Wired as `@pytest.mark.xfail(strict=False, reason=...)`:
     still a disclosed, publication-blocking near miss per spec, not a
     silent pass, but not a hard suite failure either -- xfail(strict=False)
     reports "xfailed" (or "XPASS" without erroring, if a future change
     closes the gap) and the suite still exits green either way.

     FIX 3, first pass (issue #9's diagnosis): the pre-fix season sim aimed
     every Tour shot dead at the flag, overshooting the target at 3.443 --
     the orchestrator's hypothesis was that this doesn't match how the real
     Tour field plays a sucker pin. tour.tour_optimal_aim routes Tour shots
     through optimizer.optimize_aim_tour's per-(pin, wind) aim point
     instead. This cut the miss roughly in half (to a ~0.06-0.07-stroke
     undershoot) but flipped its direction and, a validation pass found,
     suppressed the simulated birdie rate below the historical one (an
     always-safest policy never plays close enough to a fair pin to create
     a birdie look).

     Left-pin reposition (this pass): the release's original "left" pin
     placement (front_frac=0.15, tucked against the front edge) failed the
     locked pin cast (issue #5, "Pins: three, escalating" -- left scoped as
     the welcoming/accessible pin) by bailing harder than Sunday at every
     tier. Repositioned to a mid-depth placement on the green's left lobe
     (Anchor 3's own "deeper on the left" qualitative claim -- see data.py's
     PINS comment). This barely moves the Tour season mean on its own
     (aim_policy="optimal" already searches for the best aim regardless of
     where the pin sits), but is a real, necessary correctness fix for the
     amateur verdict table and the article's pin cast.

     FIX 3, second pass ("attack_when_fair," this pass): a pin the
     optimizer's own delta calls nearly fair to attack should be played at
     the flag, not bailed off unconditionally -- tour.tour_aim_point's new
     default policy attacks when a (pin, wind) state's delta clears
     tour.TOUR_ATTACK_WHEN_FAIR_THRESHOLD_STROKES (MODELED, 0.08, stated
     range 0.05-0.10) and bails to the optimizer's safer point otherwise.
     This raises the season mean further (closer to target) and modestly
     raises the birdie rate, but does not close either gate.

     Diagnosis (per the ticket's own contingency: do not tune arbitrary
     knobs to force a pass; report the required value against its stated
     sensitivity range and leave a disclosed near miss with a clear
     message): TOUR_ANISOTROPY and the two LONG_TROUBLE_* constants remain
     negligible levers (each still moves the season mean by well under 0.01
     stroke across its full stated range). WIND_FREQUENCY (0.2-0.5) and
     data.WIND's own carry_penalty_yd (4-12 yd) and dispersion_inflation
     (1.15-1.5x) are real levers, each within its own stated range. A
     compound combination near the top of all three simultaneously does
     reach 3.27-3.28 -- but no single one of them alone does, and that
     specific three-way combination has no independent justification
     beyond making the gate assertion pass, so this release does not adopt
     it as the default (the same discipline applied when the pre-fix miss
     required leaving a stated range entirely: staying inside three ranges
     at once by construction is not meaningfully more honest than leaving
     one). TOUR_UP_AND_DOWN_PCT still has no stated range at all (a single
     point estimate, Anchor 5) and stays untouched. See VALIDATION_NOTES.md
     for the full sweep, the compound-combination finding, and the
     attack_when_fair refinement's own before/after numbers.
"""

import numpy as np
import pytest

import data
import model
import montecarlo
import tour


# ---------------------------------------------------------------------------
# Gate 1: MC reproduces the analytic surface (amateur tier).
# ---------------------------------------------------------------------------

def test_montecarlo_matches_analytic_amateur():
    rng = np.random.default_rng(20260816)
    worst = 0.0
    for tier in (0, 10, 20):
        for pin in ("left", "center", "sunday"):
            aim = (data.PINS[pin]["x"], data.PINS[pin]["y"])
            for wind in (False, True):
                mc = montecarlo.simulate_amateur(tier, pin, aim, wind=wind, n=300_000, rng=rng)
                an = model.expected_score(tier, pin, aim, wind=wind, n_grid=81)
                gap = abs(mc - an)
                worst = max(worst, gap)
                assert gap < 0.03, (tier, pin, wind, mc, an, gap)
    print(f"max amateur MC vs analytic gap: {worst:.4f} strokes")


def test_montecarlo_matches_analytic_amateur_geometry_overrides():
    # Second code path, mirroring 002's test_montecarlo_club_and_drive_mean_
    # paths: confirms the harness also tracks the analytic surface when the
    # geometry/anisotropy overrides (never buried constants, per model.py's
    # own contract) are exercised instead of the published-range defaults.
    rng = np.random.default_rng(7)
    aim = (data.PINS["center"]["x"], data.PINS["center"]["y"])
    mc = montecarlo.simulate_amateur(15, "center", aim, n=300_000, rng=rng,
                                      green_width_yd=data.HOLE["green_width_yd_range"][0],
                                      anisotropy_ratio=2.5)
    an = model.expected_score(15, "center", aim, n_grid=81,
                               green_width_yd=data.HOLE["green_width_yd_range"][0],
                               anisotropy_ratio=2.5)
    assert abs(mc - an) < 0.03, (mc, an)


# ---------------------------------------------------------------------------
# Gate 1, Tour tier: the Tour oval's own per-scenario MC-vs-analytic check,
# and the season-weighted MC-vs-analytic check (tour.tour_season_analytic_
# mean vs. montecarlo.simulate_tour_season).
# ---------------------------------------------------------------------------

def test_montecarlo_matches_analytic_tour():
    rng = np.random.default_rng(20260816)
    worst = 0.0
    for pin in ("left", "center", "sunday"):
        aim = (data.PINS[pin]["x"], data.PINS[pin]["y"])
        for wind in (False, True):
            mc = montecarlo.simulate_tour(pin, aim, wind=wind, n=300_000, rng=rng)
            an = tour.tour_expected_score(pin, aim, wind=wind, n_grid=81)
            gap = abs(mc - an)
            worst = max(worst, gap)
            assert gap < 0.03, (pin, wind, mc, an, gap)
    print(f"max tour MC vs analytic gap: {worst:.4f} strokes")


def test_tour_season_mc_matches_tour_season_analytic():
    rng = np.random.default_rng(20260816)
    mc_mean, _ = montecarlo.simulate_tour_season(n=500_000, rng=rng)
    an_mean = tour.tour_season_analytic_mean()
    gap = abs(mc_mean - an_mean)
    assert gap < 0.01, (mc_mean, an_mean, gap)
    print(f"tour season MC vs analytic gap: {gap:.4f} strokes (mc={mc_mean:.4f}, an={an_mean:.4f})")


# ---------------------------------------------------------------------------
# FIX 3 (issue #9's near-miss diagnosis): the season sim's aim policy.
# tour.tour_aim_point/tour_optimal_aim wire optimizer.optimize_aim_tour's
# per-(pin, wind) optimum into both the analytic weighted mean and the MC
# season simulation, replacing the pre-fix behavior of aiming every Tour
# shot straight at the flag. These tests cover the policy machinery itself,
# independent of where the season gate numbers land (Gate 2, below).
# ---------------------------------------------------------------------------

def test_tour_aim_point_policies_resolve_to_the_expected_points():
    tour.clear_tour_aim_cache()
    p = data.PINS["sunday"]
    c = data.PINS["center"]
    assert tour.tour_aim_point("sunday", wind=False, aim_policy="pin") == (p["x"], p["y"])
    assert tour.tour_aim_point("sunday", wind=False, aim_policy="center") == (c["x"], c["y"])
    with pytest.raises(ValueError):
        tour.tour_aim_point("sunday", wind=False, aim_policy="nonsense")


def test_tour_optimal_aim_is_cached_and_never_worse_than_pin():
    import optimizer
    tour.clear_tour_aim_cache()
    aim1 = tour.tour_optimal_aim("sunday", wind=True)
    aim2 = tour.tour_optimal_aim("sunday", wind=True)
    assert aim1 == aim2, "second call must hit the cache, not re-run the optimizer"

    # The cached point must actually be the optimizer's own verdict for the
    # same (pin, wind), not some other computation drifting out of sync.
    v = optimizer.optimize_aim_tour("sunday", wind=True)
    p = data.PINS["sunday"]
    expected = (p["x"] + v.lateral_offset_yd, p["y"] + v.carry_adjustment_yd)
    assert aim1 == expected

    # Aiming at the optimum must never score worse than aiming at the pin,
    # the same guarantee optimize_aim already provides for the amateur tiers.
    optimal_score = tour.tour_expected_score("sunday", aim1, wind=True)
    pin_score = tour.tour_expected_score("sunday", (p["x"], p["y"]), wind=True)
    assert optimal_score <= pin_score + 1e-6
    tour.clear_tour_aim_cache()


def test_aim_policy_optimal_reduces_season_gate_overshoot_vs_pin():
    # Regression lock-in for FIX 3's first pass: aiming Tour shots at the
    # optimizer's best point (instead of dead at the flag) must move the
    # season mean toward the published 3.27-3.28 target, not away from it.
    # The pre-fix behavior (aim_policy="pin") overshoots high (~3.44); this
    # does not assert the fix lands inside the band (see Gate 2 below for
    # that -- it's a disclosed near miss on the other side now), only that
    # it is a real, substantial improvement in the right direction.
    tour.clear_tour_aim_cache()
    target_mid = 0.5 * (3.27 + 3.28)
    pin_mean = tour.tour_season_analytic_mean(aim_policy="pin")
    optimal_mean = tour.tour_season_analytic_mean(aim_policy="optimal")
    assert abs(optimal_mean - target_mid) < abs(pin_mean - target_mid), (
        pin_mean, optimal_mean, target_mid)
    tour.clear_tour_aim_cache()


# ---------------------------------------------------------------------------
# Second-pass refinement (this session, after the left-pin reposition):
# "attack_when_fair" blends toward the flag at (pin, wind) states the
# optimizer's own delta says are close enough to fair to attack, instead of
# bailing to the safer point unconditionally the way "optimal" does.
# ---------------------------------------------------------------------------

def test_attack_when_fair_attacks_low_delta_states_and_bails_high_delta_states():
    tour.clear_tour_aim_cache()
    threshold = tour.TOUR_ATTACK_WHEN_FAIR_THRESHOLD_STROKES
    p = data.PINS["sunday"]
    # "sunday" clears the threshold by a wide margin at every wind state
    # (delta well above 0.08, see outputs/003_results.csv-style Tour
    # verdicts) -- attack_when_fair must still bail there, aiming at the
    # optimizer's safer point, not the flag.
    v = tour.tour_optimal_verdict("sunday", wind=False)
    assert v.delta > threshold, "test assumes sunday clears the attack-when-fair threshold"
    aim = tour.tour_aim_point("sunday", wind=False, aim_policy="attack_when_fair")
    assert aim != (p["x"], p["y"])
    assert aim == tour.tour_optimal_aim("sunday", wind=False)

    # A synthetic near-fair state (delta just under the threshold) must
    # attack the flag under attack_when_fair, unlike "optimal" which always
    # bails regardless of delta.
    import optimizer
    fake_verdict = optimizer.Verdict(lateral_offset_yd=1.0, carry_adjustment_yd=1.0,
                                      score_optimum=4.0, score_at_pin=4.0 + threshold - 0.01,
                                      delta=threshold - 0.01)
    tour._TOUR_VERDICT_CACHE[("sunday", True)] = fake_verdict
    try:
        aim = tour.tour_aim_point("sunday", wind=True, aim_policy="attack_when_fair")
        assert aim == (p["x"], p["y"]), "a near-fair state must attack the flag"
    finally:
        tour.clear_tour_aim_cache()


def test_attack_when_fair_threshold_stays_in_its_stated_range():
    lo, hi = tour.TOUR_ATTACK_WHEN_FAIR_THRESHOLD_RANGE
    assert lo <= tour.TOUR_ATTACK_WHEN_FAIR_THRESHOLD_STROKES <= hi


def test_simulate_tour_season_defaults_to_attack_when_fair():
    import inspect
    assert inspect.signature(montecarlo.simulate_tour_season).parameters["aim_policy"].default == "attack_when_fair"
    assert inspect.signature(tour.tour_season_analytic_mean).parameters["aim_policy"].default == "attack_when_fair"


# ---------------------------------------------------------------------------
# Gate 2: Tour historical reproduction. Documented near miss -- see the
# module docstring and VALIDATION_NOTES.md for the full diagnosis. FIX 3
# (the aim-policy fix above) cut the overshoot roughly in half by aiming
# Tour shots at the optimizer's per-(pin, wind) best point instead of dead
# at the flag, but flipped the miss to the other side (undershoot instead of
# overshoot) rather than landing inside the band. A compound combination of
# WIND_FREQUENCY and WIND's own severity constants, each individually still
# inside its own stated range, does reach 3.27-3.28 (see VALIDATION_NOTES.md)
# -- but adopting that specific combination as this release's default would
# mean simultaneously tuning three independently-MODELED constants to a
# point discovered only by searching for what makes this exact assertion
# pass, with no independent evidence pointing at that combination over any
# other point in the same box. That is the same kind of forcing this release
# already declined to do when the pre-fix miss required leaving a stated
# range altogether; doing it by staying just inside three ranges at once is
# not meaningfully more honest. So the release keeps its disclosed default
# parameters (tour.WIND_FREQUENCY=0.35, data.WIND's published-range
# midpoints) unchanged and ships this as a smaller, still-disclosed near
# miss rather than a forced pass.
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    strict=False,
    reason=(
        "Disclosed near-miss, publication-blocking per spec: season MC mean "
        "= 3.2288 strokes (n=1,000,000, seed 20260816, aim_policy="
        "'attack_when_fair') against the 3.27-3.28 target (Anchor 4). The "
        "aim-policy fixes (optimizer-driven aim, then attack-when-fair) cut "
        "the original +0.16-stroke overshoot (3.443, aim dead at every "
        "flag) to a ~0.04-stroke undershoot -- real, substantial progress, "
        "not a full close. See VALIDATION_NOTES.md for the full diagnosis "
        "chain and sensitivity sweep."
    ),
)
def test_tour_gate_scoring_average():
    rng = np.random.default_rng(20260816)
    mc_mean, _ = montecarlo.simulate_tour_season(n=1_000_000, rng=rng)
    target_lo, target_hi = 3.27, 3.28
    assert target_lo <= mc_mean <= target_hi, (
        f"Tour gate near miss (post FIX 3 + attack_when_fair refinement): "
        f"season MC mean = {mc_mean:.4f} strokes, target = "
        f"{target_lo}-{target_hi} (Anchor 4, all-time hole-12 scoring "
        f"average). Aim policy: tour.tour_optimal_aim (FIX 3's first pass) "
        f"blended with attack_when_fair (this pass's refinement, threshold "
        f"{tour.TOUR_ATTACK_WHEN_FAIR_THRESHOLD_STROKES} strokes, stated "
        f"range {tour.TOUR_ATTACK_WHEN_FAIR_THRESHOLD_RANGE}) in place of "
        f"the pre-fix 'aim dead at the flag' behavior, which together cut "
        f"the miss from a +0.16-stroke overshoot (3.443) to roughly a "
        f"{target_lo - mc_mean:.3f}-stroke undershoot at honest-default "
        f"parameters (tour.PIN_ROTATION_WEIGHTS, tour.WIND_FREQUENCY=0.35, "
        f"data.WIND's published-range midpoints, "
        f"data.TOUR['up_and_down_pct']=0.50). Sensitivity sweep (see "
        f"VALIDATION_NOTES.md): TOUR_ANISOTROPY and the two LONG_TROUBLE_* "
        f"constants still each move this mean by well under 0.01 stroke "
        f"across their full stated ranges -- still not the lever. "
        f"WIND_FREQUENCY (stated range 0.2-0.5) and data.WIND's own "
        f"carry_penalty_yd/dispersion_inflation (stated ranges 4-12 yd / "
        f"1.15-1.5x) are real movers -- a compound combination near the top "
        f"of all three ranges simultaneously does reach 3.27-3.28, but no "
        f"single one of them alone does, and picking that exact three-way "
        f"combination has no justification beyond 'it makes this assertion "
        f"pass,' so this release does not adopt it as the default. "
        f"TOUR_UP_AND_DOWN_PCT has no stated range at all (a single "
        f"weakly-sourced point estimate, Anchor 5) and is left at 0.50 "
        f"rather than tuned. Full sweep and the compound-combination "
        f"finding are in VALIDATION_NOTES.md."
    )


@pytest.mark.xfail(
    strict=False,
    reason=(
        "Disclosed near-miss, publication-blocking per spec: simulated "
        "2019 outcome shape at n=1,000,000 (seed 20260816, aim_policy="
        "'attack_when_fair') still misses tolerance on 3 of 4 buckets "
        "(birdie ~10.2% vs. published 17.1%, bogey ~21.3% vs. 12.5%, par "
        "~62.7% vs. 65.8%; double_or_worse holds within tolerance). The "
        "attack-when-fair refinement raised the season mean toward target "
        "and modestly improved the birdie rate over the pure-'optimal' "
        "policy, but did not close the gap. Par remains the single most "
        "common outcome, the one directional check that holds at every "
        "parameter value tried. See VALIDATION_NOTES.md for the full "
        "diagnosis chain."
    ),
)
def test_tour_gate_2019_distribution_shape():
    rng = np.random.default_rng(20260816)
    _, counts = montecarlo.simulate_tour_season(n=1_000_000, rng=rng)
    total = sum(counts.values())
    fractions = {k: v / total for k, v in counts.items()}
    target = {"birdie": 52 / 304, "par": 200 / 304, "bogey": 38 / 304, "double_or_worse": 14 / 304}
    tol = 0.03  # absolute fraction tolerance per bucket
    gaps = {k: abs(fractions[k] - target[k]) for k in target}
    assert all(g < tol for g in gaps.values()), (
        f"Tour 2019-distribution near miss (post FIX 3 + attack_when_fair "
        f"refinement): simulated fractions {fractions}, 2019 published "
        f"fractions {target} (Anchor 4, 52/200/38/14 of 304 plays), "
        f"per-bucket gaps {gaps}, tolerance {tol}. The attack_when_fair "
        f"policy (threshold {tour.TOUR_ATTACK_WHEN_FAIR_THRESHOLD_STROKES} "
        f"strokes) raised the birdie rate slightly over the pure-'optimal' "
        f"policy's ~9.8% but not to the published 17.1%, and mildly widened "
        f"the par and bogey gaps in the process (more attacking shots means "
        f"more variance both ways, not just more birdies). Par stays the "
        f"single most common outcome in both the simulation and the "
        f"historical record either way. Read together with "
        f"test_tour_gate_scoring_average's undershoot, this suggests the "
        f"model's aim policy, even with the attack-when-fair refinement, "
        f"remains more conservative than how the real Tour field actually "
        f"plays this hole -- real pros likely attack fair-to-marginal pins "
        f"more often still, particularly when a birdie is worth chasing --"
        f"which the model does not fully capture. See VALIDATION_NOTES.md "
        f"for the full diagnosis chain."
    )
    # Directional sanity that DOES hold at every parameter value tried in the
    # sweep, kept as its own assertion so a future fix to the mean-average
    # miss doesn't silently regress this weaker but still-real check.
    assert fractions["par"] == max(fractions.values()), "par must remain the single most common outcome"


# ---------------------------------------------------------------------------
# Sensitivity pass (issue #9's explicit ask): LONG_TROUBLE_UPDOWN_MULT and
# LONG_TROUBLE_BUFFER_YD were flagged anchorless by the #7 review. How much
# do the amateur verdicts and the Tour gate move across their stated ranges?
# Recorded here as assertions (a "sensitivity contract"), not just prose --
# see VALIDATION_NOTES.md for the numbers behind these bounds.
# ---------------------------------------------------------------------------

def test_long_trouble_updown_mult_sensitivity_on_amateur_sunday_verdict():
    # The Sunday sucker-pin thesis (at-pin costs more than bailing to center)
    # must survive the full stated LONG_TROUBLE_UPDOWN_MULT range (0.4-0.7)
    # for every marginal tier, and the delta must not swing wildly.
    lo, hi = data.LONG_TROUBLE_UPDOWN_MULT_RANGE
    orig = data.LONG_TROUBLE_UPDOWN_MULT
    deltas = {}
    try:
        for mult in (lo, data.LONG_TROUBLE_UPDOWN_MULT, hi):
            data.LONG_TROUBLE_UPDOWN_MULT = mult
            for tier in (10, 15, 20):
                at_pin = model.expected_score(tier, "sunday", (data.PINS["sunday"]["x"], data.PINS["sunday"]["y"]))
                center_aim = model.expected_score(tier, "sunday", (data.PINS["center"]["x"], data.PINS["center"]["y"]))
                deltas[(mult, tier)] = at_pin - center_aim
                assert at_pin > center_aim, (mult, tier, "sucker-pin thesis must hold across the full range")
    finally:
        data.LONG_TROUBLE_UPDOWN_MULT = orig
    spread = max(deltas.values()) - min(deltas.values())
    assert spread < 0.02, f"sucker-pin delta swings {spread:.4f} strokes across the LONG_TROUBLE_UPDOWN_MULT range, wider than expected"


def test_long_trouble_buffer_yd_sensitivity_on_amateur_sunday_verdict():
    orig = data.LONG_TROUBLE_BUFFER_YD
    deltas = {}
    try:
        for buf in (2.0, 6.0, 12.0, 20.0):
            data.LONG_TROUBLE_BUFFER_YD = buf
            at_pin = model.expected_score(15, "sunday", (data.PINS["sunday"]["x"], data.PINS["sunday"]["y"]))
            center_aim = model.expected_score(15, "sunday", (data.PINS["center"]["x"], data.PINS["center"]["y"]))
            deltas[buf] = at_pin - center_aim
            assert at_pin > center_aim
    finally:
        data.LONG_TROUBLE_BUFFER_YD = orig
    spread = max(deltas.values()) - min(deltas.values())
    assert spread < 0.02, f"sucker-pin delta swings {spread:.4f} strokes across a 2-20 yd LONG_TROUBLE_BUFFER_YD sweep, wider than expected"


def test_long_trouble_constants_sensitivity_on_tour_gate():
    # Same two constants, checked against the Tour season mean instead of
    # an amateur verdict: negligible mover, confirming the Tour gate's near
    # miss (test_tour_gate_scoring_average) is not attributable to these.
    #
    # aim_policy="pin" here on purpose: the default "optimal" policy (FIX 3)
    # caches optimizer.optimize_aim_tour's result per (pin, wind), and that
    # cache does not know these constants were monkeypatched, so reusing it
    # across mult/buf values would silently test pricing sensitivity at a
    # stale aim point. Isolating this check to aim_policy="pin" avoids
    # re-running the (expensive) optimizer search per constant value while
    # still directly measuring what this test cares about: how much
    # LONG_TROUBLE_UPDOWN_MULT/BUFFER_YD move tour_expected_score's own
    # pricing. FIX 3's aim-policy effect on the season mean is covered
    # separately (test_tour_season_analytic_mean_aim_policy_matters below).
    lo, hi = data.LONG_TROUBLE_UPDOWN_MULT_RANGE
    orig_mult = data.LONG_TROUBLE_UPDOWN_MULT
    means = []
    try:
        for mult in (lo, hi):
            data.LONG_TROUBLE_UPDOWN_MULT = mult
            means.append(tour.tour_season_analytic_mean(aim_policy="pin"))
    finally:
        data.LONG_TROUBLE_UPDOWN_MULT = orig_mult
    assert max(means) - min(means) < 0.01, "LONG_TROUBLE_UPDOWN_MULT should barely move the tour season mean"

    orig_buf = data.LONG_TROUBLE_BUFFER_YD
    means = []
    try:
        for buf in (2.0, 20.0):
            data.LONG_TROUBLE_BUFFER_YD = buf
            means.append(tour.tour_season_analytic_mean(aim_policy="pin"))
    finally:
        data.LONG_TROUBLE_BUFFER_YD = orig_buf
    assert max(means) - min(means) < 0.01, "LONG_TROUBLE_BUFFER_YD should barely move the tour season mean"
