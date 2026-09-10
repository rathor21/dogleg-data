import csv
import os
from math import hypot

import pytest

import data
import model
import optimizer

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_CSV_PATH = os.path.join(HERE, "outputs", "003_results.csv")


def _load_results_csv():
    """{(tier, pin, wind): row} from outputs/003_results.csv, read directly
    rather than through export.load_results_csv so this test module keeps
    its existing dependency footprint (data/model/optimizer only, no
    art.sketch import via export.py)."""
    rows = {}
    with open(RESULTS_CSV_PATH, newline="") as f:
        for row in csv.DictReader(f):
            key = (int(row["tier"]), row["pin"], row["wind"] == "True")
            rows[key] = row
    return rows


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
# Empirically confirmed (not assumed): at tiers 5 and 15, aiming under wind
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
# rather than farther -- the opposite direction from every other tier at
# the time.
#
# Tier 10 moved out of the pair this pass (region-geometry fix, #12): the
# finite creek band plus short_fairway's own distance falloff reshape the
# short side of the Sunday-pin surface enough that tier 10's windy optimum
# now sits marginally CLOSER to the pin than calm too (confirmed by hand at
# n_grid=81 and 121: 20.5-21.9 yd windy vs 22.5-22.9 yd calm, a small but
# consistent reversal, not resolution noise). Tier 15 replaces it: both
# n_grid=81 and 121 show a large, consistent gap (calm ~18.4-18.6 yd, windy
# ~29.5-29.6 yd), well above anything this test's other pairs treat as
# noise.
#
# Tier 20 remains excluded (unlike test_optimal_aim_moves_away_from_pin_
# as_oval_widens_at_sunday above, which only needs the two extreme tiers
# and so never hits this): the windy optimum now sits close enough to
# optimizer.py's search-box edge (see build_outputs.py's own boundary-hit
# report after the region-geometry fix) that its exact distance from the
# pin is a resolution/box-size artifact, not a stable modeled effect.
# ---------------------------------------------------------------------------

def test_wind_pushes_optimal_aim_farther_from_sunday_pin():
    for tier in (5, 15):
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
# Re-taken after the region-geometry fix (#12: finite creek band plus
# short_fairway, model.region_at/model._recovery_strokes). That fix removes
# the old inflated, distance-independent water penalty for any short miss,
# which was previously the dominant reason to bail off ANY pin (not just
# Sunday). With that risk correctly priced down, the flip-set shrinks
# sharply and its shape changes:
#
#   - "sunday" no longer flips ANYWHERE in the sensitivity rectangle
#     (previously it cracked once, at (20, "sunday", True)'s anisotropy=3.5
#     corner, under the pre-fix creek rule). Bailing off Sunday is now a
#     MORE robust finding, not a less robust one: the old inflated risk
#     applied diffusely to every pin, so removing it sharpens Sunday's own
#     real risk relative to the other two rather than eroding it.
#   - "left" and "center" both move toward "either works" as their
#     baseline almost everywhere (see test_flip_set_baseline_labels_
#     sunday_always_bail_left_and_center_are_the_tossup_pins below):
#     without the old inflated short-miss penalty, attacking either pin
#     directly costs barely more than the safest nearby alternative at
#     most tiers, so only a few sensitivity-corner combinations still flip
#     at all, mostly from "either works" baseline TO "bail" at the
#     sensitivity rectangle's extreme corners (wide anisotropy or shallow
#     front-third depth), the opposite direction from most of the pre-fix
#     flip set.
#
# Confirmed via flip_set's own (cheaper) default settings, matching how the
# function is actually used in practice; frozen here as the golden snapshot
# so a future model or optimizer change that moves this picture fails
# loudly instead of silently changing the article's sensitivity disclosure.
#
# Re-taken after rev 6 (Sunny's mishit-mixture finding, #7/#8): the mixture
# raises every tier's expected score somewhat (short misses now split
# between a solid-strike core and a short-mishit tail rather than one
# symmetric spread, and the wider BANK_ROLLBACK_YD band prices more of that
# tail as water), which shifts a handful of near-tossup corners across their
# own label boundary. (0, "left", True) no longer flips (now a stable
# "either works" everywhere in the sensitivity rectangle) -- dropped from
# rev 5's set. (5, "left", True) and (5, "center", True) newly join the
# flip set, both baseline "either works" flipping to "bail" at their own
# corners, the same direction as the pre-existing (0, "left", calm) and
# (5, "left", calm) flips. (0, "center", True) also still flips, but its
# own BASELINE moved from "either works" (rev 5) to "bail" (rev 6: the
# mixture's added short-miss risk pushed this already-near-tossup corner,
# delta 0.0431 in the rev-5 CSV, just past TOSSUP_THRESHOLD_STROKES), so it
# is the one cell in this set that flips bail -> either works rather than
# either works -> bail. "sunday" still never flips anywhere in the
# rectangle -- the sucker-pin finding remains the most robust of the three
# pins' verdicts.
#
# Re-taken again after rev 7 (GIR-anchored core, MISHIT_PCT x1.25/MISHIT_
# SHORT_FRAC 0.25/ANISOTROPY ratio 2.5): the retuned mixture shape moves
# scores again, and "sunday" loses its rev-6 status as the pin that never
# flips anywhere in the rectangle -- (10, "sunday", True), (15, "sunday",
# True), and (20, "sunday", True) now each flip bail -> either works at one
# or more sensitivity corners. This is disclosed, not silently absorbed:
# the SUCKER-PIN FINDING ITSELF still holds at every tier and wind state at
# flip_set's own (cheap) default settings (test_flip_set_baseline_labels_
# sunday_always_bail_left_and_center_are_the_tossup_pins below still passes
# unmodified), and calm sunday stays "bail" at verdict-grade resolution for
# every tier too -- only WINDY sunday at the higher tiers has sensitivity-
# rectangle corners where the finding is no longer unanimous, and the
# published verdict-grade CSV (outputs/003_results.csv, VERDICT_N_GRID=121)
# shows one of those near-tossup cells, (15, "sunday", wind), actually
# cross the line at its own BASELINE settings (delta 0.0552 -> 0.0488;
# see VALIDATION_NOTES.md's rev 7 section). (5, "center", True) drops out
# of the flip set entirely (a stable "either works" everywhere in the
# rectangle this pass). (0, "left", False) and (0, "center", True) both
# still flip, but now bail -> either works rather than either works ->
# bail -- their own BASELINES moved past the tossup line this pass.
# ---------------------------------------------------------------------------

def test_flip_set_runs_and_matches_golden_snapshot():
    flips = optimizer.flip_set()
    flips_by_key = {(f["tier"], f["pin"], f["wind"]): f for f in flips}
    assert set(flips_by_key) == {
        (0, "left", False), (0, "center", True),
        (5, "left", False), (5, "left", True),
        (10, "sunday", True), (15, "sunday", True), (20, "sunday", True),
    }

    # either works -> bail flips: both tier-5 "left" corners.
    for key in [(5, "left", False), (5, "left", True)]:
        assert flips_by_key[key]["baseline_label"] == "either works"
        assert {d["label"] for d in flips_by_key[key]["flipped_at"]} == {"bail"}

    # bail -> either works: tier 0's own two flips (both BASELINES moved
    # past the tossup line this pass) plus all three windy "sunday" cells
    # (see the comment above -- the sucker-pin finding's own robustness,
    # not its baseline verdict, is what erodes here).
    for key in [(0, "left", False), (0, "center", True),
                (10, "sunday", True), (15, "sunday", True), (20, "sunday", True)]:
        assert flips_by_key[key]["baseline_label"] == "bail"
        assert {d["label"] for d in flips_by_key[key]["flipped_at"]} == {"either works"}


def test_flip_set_baseline_labels_sunday_always_bail_left_and_center_are_the_tossup_pins():
    # Companion to the golden snapshot above: confirms flip_set is actually
    # exercising real (non-degenerate) baseline verdicts, not e.g. silently
    # returning [] because every call errored out and got swallowed, and
    # pins the actual post-rev-6 (mishit mixture, Sunny's finding) label
    # pattern: "sunday" never reads anything but "bail"; "left" still sits
    # near the tossup line (either "bail" or "either works" depending on
    # tier/wind); "center" reads "either works" at every tier and wind
    # state EXCEPT (0, "center", wind=True), which now reads "bail" -- the
    # mishit mixture's wider short-miss risk (rev 6) pushed that single
    # near-tossup corner (already the closest to the line pre-rev-6, delta
    # 0.0431 in the rev-5 CSV) just past TOSSUP_THRESHOLD_STROKES. Neither
    # pin ever reads "attack" -- optimize_aim's own search always evaluates
    # the pin as a candidate, so a genuine delta < 0 never happens here.
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

    left_labels = {k: v for k, v in labels.items() if k[1] == "left"}
    assert "bail" in left_labels.values(), "left should still read as bail somewhere"

    # "center" reads "either works" at every tier and wind state EXCEPT
    # (0, "center", wind=True), which reads "bail" as of rev 6 (see the
    # docstring above) -- a single near-tossup corner crossing the line,
    # not a wholesale change to center's own tossup-pin character.
    center_labels = {k: v for k, v in labels.items() if k[1] == "center"}
    assert set(center_labels.values()) == {"either works", "bail"}
    assert labels[(0, "center", True)] == "bail"
    non_flipped_center = {k: v for k, v in center_labels.items() if k != (0, "center", True)}
    assert set(non_flipped_center.values()) == {"either works"}


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


# ---------------------------------------------------------------------------
# published_move (issue #13): the "full shot" window rule the article
# quotes for its aim verdicts (see optimizer.published_move's docstring).
# ---------------------------------------------------------------------------

def test_published_move_returns_namedtuple_fields():
    m = optimizer.published_move(10, "left", n_grid=81)
    assert m._fields == (
        "lateral_offset_yd", "carry_adjustment_yd", "score_optimum", "score_at_pin", "delta",
        "strict_lateral_offset_yd", "strict_carry_adjustment_yd", "strict_score_optimum",
        "layup_edge_strokes", "layup_is_tossup",
    )
    assert isinstance(m.layup_edge_strokes, float)
    assert isinstance(m.layup_is_tossup, (bool,))


def test_published_move_carry_adjustment_stays_inside_the_full_shot_window():
    # Every tier x pin x wind combination's PUBLISHED carry adjustment must
    # sit inside +/- PUBLISHED_CARRY_RANGE_YD (10 yd) by construction (the
    # search box itself is clamped there) -- this is a sanity check on the
    # clamp, not a discovery.
    for tier in data.TIERS:
        for pin in data.PINS:
            for wind in (False, True):
                m = optimizer.published_move(tier, pin, wind, n_grid=81)
                assert abs(m.carry_adjustment_yd) <= optimizer.PUBLISHED_CARRY_RANGE_YD + 1e-6, \
                    (tier, pin, wind, m.carry_adjustment_yd)


def test_published_move_agrees_with_results_csv_when_strict_optimum_inside_window():
    # Wherever outputs/003_results.csv's own strict optimum already sits
    # inside the +/- 10 yd published window (i.e. the model's unconstrained
    # answer IS a full shot already), there is no real edge left to find by
    # searching outside it: the layup edge should be small and the
    # full-shot score should match the CSV's own optimum closely. This does
    # NOT assert the two searches land on bit-identical (lateral, carry)
    # coordinates -- optimize_aim's coarse-then-descent search is heuristic,
    # not exhaustive, and two independently-run searches over different-
    # sized boxes can settle in different, comparably-good basins on this
    # surface's known shallow-valley stretches (see published_move's
    # docstring). Score agreement is the real invariant; exact coordinates
    # are not.
    results = _load_results_csv()
    for (tier, pin, wind), row in results.items():
        strict_carry = float(row["aim_carry_adjustment_yd"])
        if abs(strict_carry) > optimizer.PUBLISHED_CARRY_RANGE_YD:
            continue
        m = optimizer.published_move(tier, pin, wind, n_grid=81)
        assert abs(m.score_optimum - float(row["score_optimum"])) < 0.02, (tier, pin, wind)
        assert m.layup_edge_strokes < 0.02, (tier, pin, wind, m.layup_edge_strokes)


def test_published_move_layup_edge_always_nonnegative_and_reports_exceedances():
    # Every published_move's layup_edge_strokes is >= 0 (optimizer.
    # published_move floors it there by construction, since the two
    # independent searches it compares are not exhaustive and can disagree
    # by search noise on a near-flat surface -- see the function's
    # docstring). Any row whose edge clears TOSSUP_THRESHOLD_STROKES is
    # collected and printed rather than asserted against, since
    # VALIDATION_NOTES.md's own hand-check found the Sunday pin's higher
    # tiers (10/15/20) sit close to that line and a future model change
    # could legitimately push one of them over it.
    exceeded = []
    for tier in data.TIERS:
        for pin in data.PINS:
            for wind in (False, True):
                m = optimizer.published_move(tier, pin, wind, n_grid=81)
                assert m.layup_edge_strokes >= 0.0, (tier, pin, wind, m.layup_edge_strokes)
                assert m.layup_is_tossup == (m.layup_edge_strokes <= optimizer.TOSSUP_THRESHOLD_STROKES)
                if not m.layup_is_tossup:
                    exceeded.append((tier, pin, wind, m.layup_edge_strokes))
    if exceeded:
        print(f"\n{len(exceeded)} (tier, pin, wind) row(s) whose strict-optimum "
              f"layup edge exceeds TOSSUP_THRESHOLD_STROKES ({optimizer.TOSSUP_THRESHOLD_STROKES}):")
        for tier, pin, wind, edge in exceeded:
            print(f"  tier={tier} pin={pin} wind={wind} layup_edge_strokes={edge}")


def test_published_move_sunday_pin_layup_edges_are_small_and_disclosed():
    # Sunday pin, tiers 10/15/20 (VALIDATION_NOTES.md's "Sunday layup check",
    # rev 5): the strict optimum's edge over the full-shot aim should stay
    # small (comfortably under two tenths of a stroke at this release's
    # defaults) even where it is not a strict tossup.
    for tier in (10, 15, 20):
        for wind in (False, True):
            m = optimizer.published_move(tier, "sunday", wind, n_grid=optimizer.VERDICT_N_GRID)
            assert 0.0 <= m.layup_edge_strokes < 0.2, (tier, wind, m.layup_edge_strokes)
