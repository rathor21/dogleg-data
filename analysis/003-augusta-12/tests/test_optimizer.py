from math import hypot

import pytest

import data
import model
import optimizer


def _distance_from_pin(verdict):
    return hypot(verdict.lateral_offset_yd, verdict.carry_adjustment_yd)


# ---------------------------------------------------------------------------
# Optimal aim moves away from the pin as the oval widens (direction-of-
# motion test, #8's first acceptance criterion): tier 20's Sunday aim sits
# farther from the pin than tier 0's.
# ---------------------------------------------------------------------------

def test_optimal_aim_moves_away_from_pin_as_oval_widens_at_sunday():
    v0 = optimizer.optimize_aim(0, "sunday", wind=False, n_grid=81)
    v20 = optimizer.optimize_aim(20, "sunday", wind=False, n_grid=81)
    assert _distance_from_pin(v20) > _distance_from_pin(v0)


# Not tested: strict monotonicity of the exact (lateral, carry) coordinates
# across every intermediate tier. The score surface near the optimum is
# genuinely close to flat along the carry axis for several tiers at Sunday
# (see test_optimum_stable_between_n_grid_81_and_121's docstring) -- several
# yards of carry adjustment score within ~0.01-0.02 strokes of each other --
# so the arg-min carry coordinate is not a well-determined single point and
# a few yards of search noise can make the *reported* Euclidean distance
# from the pin non-monotonic between adjacent tiers even though the
# qualitative bail-farther-as-the-oval-widens direction (tested above between
# the two extreme tiers, where the effect is large enough to clear the
# noise) holds.


# ---------------------------------------------------------------------------
# The optimizer never returns an aim worse than center-green aim.
# ---------------------------------------------------------------------------

def test_optimizer_never_worse_than_center_green_aim():
    for tier in (0, 10, 20):
        for pin in data.PINS:
            for wind in (False, True):
                v = optimizer.optimize_aim(tier, pin, wind, n_grid=81)
                center_s = optimizer.center_aim_score(tier, pin, wind, n_grid=81)
                assert v.score_optimum <= center_s + 1e-6, (tier, pin, wind)


def test_optimizer_matches_center_aim_score_when_pin_is_center():
    # The center pin's own aim point IS the center-of-green candidate, so
    # score_at_pin and the center-aim bailout score should coincide exactly.
    v = optimizer.optimize_aim(15, "center", wind=False, n_grid=81)
    center_s = optimizer.center_aim_score(15, "center", wind=False, n_grid=81)
    assert abs(v.score_at_pin - center_s) < 1e-9


# ---------------------------------------------------------------------------
# Wind pushes the optimal aim farther from the Sunday pin.
#
# Empirically confirmed (not assumed): at tiers 5 and 10, aiming under wind
# moves the optimal aim clearly farther from the Sunday pin than aiming in
# calm air -- well above the search's own truncation-noise band. Both
# dimensions widen under data.WIND (carry_penalty shortens the mean shot,
# dispersion_inflation widens both oval axes), so a bigger miss pattern
# pushes the safe aim point further off the flag, same direction as the
# tier effect above.
#
# Tier 0 moved out of this pair after the Anchor-8 putting-curve fix
# (model.putt_probabilities/tour.tour_putt_probabilities, #9 follow-up):
# scratch's own anchored make percentages are much higher at short range
# than the old invented `1.5 + 0.012*ft` floor assumed, which reshapes the
# near-green portion of the score surface enough that scratch's windy
# optimum now sits marginally CLOSER to the Sunday pin than its calm one
# (confirmed by hand: 7.35 yd windy vs 8.22 yd calm) rather than farther --
# the opposite direction from every other tier. This is a genuine change in
# the model's own finding at this specific tier x pin combination, not a
# search artifact; tiers 5/10/15/20 all still show the expected
# wind-pushes-aim-farther direction post-fix, so the pair tested here moved
# from (0, 10) to (5, 10) rather than dropping the check.
#
# Tier 20 is deliberately excluded here (unlike test_optimal_aim_moves_away_
# from_pin_as_oval_widens_at_sunday above, which only needs the two extreme
# tiers and so never hits this): after FIX 1's long_trouble falloff
# reshaped the score surface, the tier-20 Sunday-pin surface both with and
# without wind is genuinely near-flat across several yards in multiple
# directions (confirmed by hand: candidate points 2-4 yd apart in the
# neighborhood of each optimum score within ~0.005-0.01 strokes of each
# other at n_grid=121, the same class of flat valley
# test_optimum_stable_between_n_grid_81_and_121 already documents for
# (15, "sunday", calm)) -- calm and windy land in different, comparably-
# scored basins whose raw Euclidean distance from the pin differs by only
# ~0.2 yd, well inside that noise band and in either direction depending on
# search settings. Asserting a strict ordering there would be testing search
# noise, not a real modeled effect; the qualitative "wind pushes the aim
# farther out" conclusion is not well-determined at this specific tier x pin
# combination, so this test does not claim it is.
# ---------------------------------------------------------------------------

def test_wind_pushes_optimal_aim_farther_from_sunday_pin():
    for tier in (5, 10):
        calm = optimizer.optimize_aim(tier, "sunday", wind=False, n_grid=81)
        windy = optimizer.optimize_aim(tier, "sunday", wind=True, n_grid=81)
        assert _distance_from_pin(windy) > _distance_from_pin(calm), tier


# ---------------------------------------------------------------------------
# n_grid stability: the optimum found at n_grid=81 and n_grid=121 should
# agree closely -- the #7 review's reason for elevating verdict-grade
# resolution in the first place (0.01-0.03 stroke truncation noise at the
# model's default n_grid=41).
# ---------------------------------------------------------------------------

def test_optimum_stable_between_n_grid_81_and_121():
    # Stability means the reported SCORE is stable, and each resolution's
    # chosen aim point stays near-optimal when re-scored at the other
    # resolution -- not that the exact (lateral, carry) coordinates match to
    # the yard. At (15, "sunday", calm), the score surface runs within
    # ~0.01-0.02 strokes across several yards of carry adjustment near the
    # optimum (confirmed by hand: dy in [-5, 5] at the optimal lateral offset
    # all score 4.17-4.18), so the arg-min carry coordinate genuinely shifts
    # a few yards between n_grid=81 and 121 while the score itself barely
    # moves. Asserting raw coordinate closeness there would fail on a true
    # feature of the model (a flat valley), not an optimizer defect.
    for tier, pin, wind in [(15, "sunday", False), (20, "sunday", True), (0, "center", False)]:
        v81 = optimizer.optimize_aim(tier, pin, wind, n_grid=81)
        v121 = optimizer.optimize_aim(tier, pin, wind, n_grid=121)
        assert abs(v81.score_optimum - v121.score_optimum) < 0.02, (tier, pin, wind, "score")

        p = data.PINS[pin]
        aim_81 = (p["x"] + v81.lateral_offset_yd, p["y"] + v81.carry_adjustment_yd)
        aim_121 = (p["x"] + v121.lateral_offset_yd, p["y"] + v121.carry_adjustment_yd)
        cross_81_at_121 = model.expected_score(tier, pin, aim_81, wind=wind, n_grid=121)
        cross_121_at_81 = model.expected_score(tier, pin, aim_121, wind=wind, n_grid=81)
        assert cross_81_at_121 < v121.score_optimum + 0.03, (tier, pin, wind, "81's aim not near-optimal at 121")
        assert cross_121_at_81 < v81.score_optimum + 0.03, (tier, pin, wind, "121's aim not near-optimal at 81")

        # Coordinates are not required to match exactly, but a genuinely
        # unstable/buggy search (not just a flat valley) would drift far
        # more than this; a coarse sanity bound still catches that.
        assert hypot(v81.lateral_offset_yd - v121.lateral_offset_yd,
                     v81.carry_adjustment_yd - v121.carry_adjustment_yd) < 8.0, (tier, pin, wind)


def test_optimum_stable_pair_constant_matches_module_contract():
    assert optimizer.STABILITY_N_GRID_PAIR == (81, 121)


# ---------------------------------------------------------------------------
# Search range is a stated, bounded budget (roughly two clubs), not an
# unconstrained search -- see optimizer.py's module docstring: model.py's
# long_trouble price has no distance falloff, so an unbounded search chases
# an unrealistic "fly it as far as possible" asymptote for the front-left
# pin. hit_search_boundary() flags verdicts that land on that cap.
# ---------------------------------------------------------------------------

def test_hit_search_boundary_false_after_long_trouble_falloff_fix():
    # FIX 1 regression guard: this exact combination (front-left pin, wind,
    # widest tier) was #8's own "confirmed by hand" example of a search that
    # capped out against an unbounded long_trouble asymptote. Now that
    # model.py prices a distance falloff (true argmin around ~38 yd of
    # carry), it must converge to a genuine interior optimum instead -- at
    # VERDICT_N_GRID, the resolution build_outputs.py actually publishes at
    # (this combination's score surface approaching the cap is shallow
    # enough, per hit_search_boundary's own docstring, that the cheaper
    # n_grid=81 sanity resolution can still drift within a yard of the box
    # edge; that noise is a resolution artifact, not a re-opened defect --
    # see test_optimum_stable_between_n_grid_81_and_121 for the same
    # near-boundary shallow-valley behavior documented elsewhere).
    v = optimizer.optimize_aim(20, "left", wind=True, n_grid=optimizer.VERDICT_N_GRID)
    assert not optimizer.hit_search_boundary(v)


def test_hit_search_boundary_detects_an_artificially_capped_verdict():
    # hit_search_boundary's own detection logic, independent of whether any
    # real (tier, pin, wind) combination currently lands on the cap.
    Verdict = optimizer.Verdict
    capped = Verdict(lateral_offset_yd=5.0, carry_adjustment_yd=optimizer.DEFAULT_CARRY_RANGE_YD,
                      score_optimum=4.0, score_at_pin=4.2, delta=0.2)
    interior = Verdict(lateral_offset_yd=5.0, carry_adjustment_yd=10.0,
                        score_optimum=4.0, score_at_pin=4.2, delta=0.2)
    assert optimizer.hit_search_boundary(capped)
    assert not optimizer.hit_search_boundary(interior)


def test_hit_search_boundary_false_for_a_clean_interior_optimum():
    v = optimizer.optimize_aim(0, "sunday", wind=False, n_grid=81)
    assert not optimizer.hit_search_boundary(v)


def test_optimizer_respects_declared_search_box():
    # Regression guard for the bug this package's optimize_aim once had: an
    # unclamped pattern-search polish that wandered tens of yards past the
    # declared lateral/carry range. Every returned aim point must sit inside
    # the box (center-of-green candidate included, since it can fall outside
    # the box for far pins and is intentionally allowed to override the cap
    # -- so this checks the *searched* range specifically via a tight box
    # that excludes the center-of-green candidate for the "left" pin, whose
    # center offset is small).
    v = optimizer.optimize_aim(20, "left", wind=True, n_grid=81,
                                lateral_range_yd=20.0, carry_range_yd=25.0)
    assert abs(v.lateral_offset_yd) <= 20.0 + 1e-6
    assert abs(v.carry_adjustment_yd) <= 25.0 + 1e-6


# ---------------------------------------------------------------------------
# verdict_label / tossup threshold.
# ---------------------------------------------------------------------------

def test_verdict_label_bail_either_works_or_attack_by_threshold():
    # FIX 2: the 002 tossup convention (|delta| <= 0.05 strokes -> "either
    # works," mirroring site/tee-shot-distance/tool.html's sandbox band)
    # replaces the old two-way bail/attack split inside that band.
    Verdict = optimizer.Verdict
    bail = Verdict(lateral_offset_yd=-5.0, carry_adjustment_yd=0.0,
                    score_optimum=4.0, score_at_pin=4.10, delta=0.10)
    tossup = Verdict(lateral_offset_yd=0.0, carry_adjustment_yd=0.0,
                      score_optimum=4.0, score_at_pin=4.02, delta=0.02)
    tossup_at_boundary = Verdict(lateral_offset_yd=0.0, carry_adjustment_yd=0.0,
                                  score_optimum=4.0, score_at_pin=4.05, delta=0.05)
    attack = Verdict(lateral_offset_yd=0.0, carry_adjustment_yd=0.0,
                      score_optimum=4.10, score_at_pin=4.0, delta=-0.10)
    assert optimizer.verdict_label(bail) == "bail"
    assert optimizer.verdict_label(tossup) == "either works"
    assert optimizer.verdict_label(tossup_at_boundary) == "either works"
    assert optimizer.verdict_label(attack) == "attack"


# ---------------------------------------------------------------------------
# Flip-set enumeration runs and its contents are asserted against a golden
# snapshot.
#
# Re-taken after the Anchor-8 putting-curve fix (#9 follow-up: model.
# putt_probabilities / tour.tour_putt_probabilities replace the invented
# `1.5 + 0.012*ft` formula; see data.py's Anchor 8 block and VALIDATION_
# NOTES.md). That fix changes every tier's near-green pricing, which moves
# the flip-set again: (0, "left", False) and (15, "center", False) no
# longer flip anywhere in the sensitivity rectangle, and -- new this pass --
# (20, "sunday", True) now flips at the sweep's anisotropy=3.5 corner. At
# TOSSUP_THRESHOLD_STROKES = 0.05 and the default corner-only sweep of the
# anisotropy range (2.0-3.5) and the front-third-depth range (9-12 yd):
#
#   - "sunday" is still "bail" at every tier and wind state at the sweep's
#     own MIDPOINT baseline (see test_flip_set_baseline_labels_sunday_
#     always_bail_left_and_center_are_the_tossup_pins below, which checks
#     baseline labels, not sensitivity extremes) -- reads as a trap at
#     every tier, as CONTEXT.md's scoping expected. But it is no longer
#     perfectly robust across the full sensitivity rectangle: at tier 20
#     under wind, the anisotropy=3.5 corner (either front-third depth) now
#     flips it to "either works," a real (small) crack in the "sunday never
#     flips" finding introduced by the more accurate near-pin putting curve.
#   - "left" and "center" remain genuinely close to the tossup line, tipped
#     one way or the other by tier, wind, and the front-third-depth
#     sensitivity corner, the same picture as before the putting fix.
#
# Confirmed via flip_set's own (cheaper) default settings, matching how the
# function is actually used in practice; frozen here as the golden snapshot
# so a future model or optimizer change that moves this picture fails
# loudly instead of silently changing the article's sensitivity disclosure.
# ---------------------------------------------------------------------------

def test_flip_set_runs_and_matches_golden_snapshot():
    flips = optimizer.flip_set()
    flips_by_key = {(f["tier"], f["pin"], f["wind"]): f for f in flips}
    assert set(flips_by_key) == {
        (0, "center", False),
        (5, "left", False), (5, "center", False),
        (10, "left", False), (10, "center", False),
        (15, "left", True),
        (20, "center", True), (20, "sunday", True),
    }
    # "sunday" now appears exactly once, at (20, True) -- see the comment
    # above for why this is a real (small) post-putting-fix change, not a
    # search artifact. It never flips at any other tier or wind state.
    assert {(t, p, w) for (t, p, w) in flips_by_key if p == "sunday"} == {(20, "sunday", True)}

    # bail -> either works flips (low/mid tiers, plus wind cases at "left"
    # and, new this pass, "sunday").
    for key in [(0, "center", False), (5, "left", False),
                (15, "left", True), (20, "sunday", True)]:
        assert flips_by_key[key]["baseline_label"] == "bail"
        assert {d["label"] for d in flips_by_key[key]["flipped_at"]} == {"either works"}

    # either works -> bail flips (mid tiers, calm, plus one wind case at
    # "center"), every one of them at the narrow 9-yd front-third-depth
    # corner.
    for key in [(5, "center", False), (10, "left", False),
                (10, "center", False), (20, "center", True)]:
        assert flips_by_key[key]["baseline_label"] == "either works"
        assert {d["label"] for d in flips_by_key[key]["flipped_at"]} == {"bail"}
        assert all(d["front_third_depth_yd"] == 9.0 for d in flips_by_key[key]["flipped_at"])


def test_flip_set_baseline_labels_sunday_always_bail_left_and_center_are_the_tossup_pins():
    # Companion to the golden snapshot above: confirms flip_set is actually
    # exercising real (non-degenerate) baseline verdicts, not e.g. silently
    # returning [] because every call errored out and got swallowed, and
    # pins the actual post-reposition label pattern: "sunday" never reads
    # anything but "bail"; "left" and "center" both sit near the tossup
    # line (either "bail" or "either works" depending on tier/wind, never
    # "attack" -- optimize_aim's own search always evaluates the pin as a
    # candidate, so a genuine delta < 0 never happens here).
    labels = {}
    for tier in data.TIERS:
        for pin in data.PINS:
            for wind in (False, True):
                v = optimizer.optimize_aim(tier, pin, wind,
                                            n_grid=optimizer.FLIP_SET_N_GRID,
                                            search_n_grid=optimizer.FLIP_SET_SEARCH_N_GRID,
                                            coarse_step_yd=optimizer.FLIP_SET_COARSE_STEP_YD,
                                            lateral_range_yd=optimizer.FLIP_SET_LATERAL_RANGE_YD,
                                            carry_range_yd=optimizer.FLIP_SET_CARRY_RANGE_YD,
                                            anisotropy_ratio=data.ANISOTROPY["ratio"],
                                            front_third_depth_yd=0.5 * sum(data.HOLE["front_third_depth_yd_range"]))
                labels[(tier, pin, wind)] = optimizer.verdict_label(v)

    for tier in data.TIERS:
        for wind in (False, True):
            assert labels[(tier, "sunday", wind)] == "bail", (tier, wind)

    for pin in ("left", "center"):
        pin_labels = {k: v for k, v in labels.items() if k[1] == pin}
        assert set(pin_labels.values()) <= {"bail", "either works"}
        assert "either works" in pin_labels.values(), f"{pin} should read as a genuine tossup somewhere"
        assert "bail" in pin_labels.values(), f"{pin} should still read as bail somewhere"


# ---------------------------------------------------------------------------
# Edge cases / API sanity.
# ---------------------------------------------------------------------------

def test_optimize_aim_rejects_unknown_tier_or_pin():
    with pytest.raises(KeyError):
        optimizer.optimize_aim(7, "center")
    with pytest.raises(KeyError):
        optimizer.optimize_aim(15, "nowhere")


def test_optimize_aim_returns_verdict_namedtuple_fields():
    v = optimizer.optimize_aim(10, "left", n_grid=81)
    assert v._fields == ("lateral_offset_yd", "carry_adjustment_yd",
                          "score_optimum", "score_at_pin", "delta")
    assert isinstance(v.delta, float)
    assert v.delta >= -1e-6  # optimum is never worse than at-pin either
