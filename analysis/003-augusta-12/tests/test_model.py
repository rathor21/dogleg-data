from math import sqrt

import pytest

import data
import model
import tour


# ---------------------------------------------------------------------------
# Step 1+2: oval inversion round-trips its published input aggregates.
# ---------------------------------------------------------------------------

def test_oval_round_trips_proximity_at_155yd():
    for tier in data.TIERS:
        sd, sl = model.oval_for_tier(tier)
        assert abs(model.mean_radial_ft(sd, sl) - data.PROXIMITY_FT[tier]) < 1e-6


def test_oval_preserves_total_variance_under_anisotropy_override():
    for ratio in (2.0, 3.0, 3.5):
        sd, sl = model.oval_for_tier(15, anisotropy_ratio=ratio)
        assert abs(sd - ratio * sl) < 1e-9
        iso_sq = data.sigma_isotropic_ft(15) / model.FT_PER_YD
        assert abs((sd ** 2 + sl ** 2) - 2 * iso_sq ** 2) < 1e-9


def test_gir_reproduces_fifty_percent_at_each_tiers_own_magic_number():
    # An algebraic consequence of the inversion (P=50% by definition at the
    # published GIR50 distance); confirms the pipeline (not just the algebra
    # on paper) actually reproduces it.
    for tier in data.TIERS:
        sigma_iso_yd = data.sigma_isotropic_ft(tier, shot_yd=data.GIR50_DISTANCE_YD[tier]) / model.FT_PER_YD
        gir = model.gir_probability(sigma_iso_yd)
        assert abs(gir - 0.5) < 0.035  # tier 10 (direct anchor) sits off exact 50% by ~3 pts, everyone else is exact


def test_tier10_round_trips_its_direct_matched_pair():
    # The one tier with both a proximity figure AND a GIR% at the same band
    # (Anchor 1, Source 1/3): 62 ft, 43%, at the 125-149 yd band midpoint.
    sigma_iso_yd = data.sigma_isotropic_ft(10, shot_yd=data.PROXIMITY_10_ANCHOR_BAND_MID_YD) / model.FT_PER_YD
    proximity_ft = sigma_iso_yd * model.FT_PER_YD * sqrt(3.14159265358979 / 2.0)
    assert abs(proximity_ft - data.PROXIMITY_10_ANCHOR_FT) < 1e-6
    assert abs(model.gir_probability(sigma_iso_yd) - data.GIR_10_ANCHOR_PCT) < 1e-6


# ---------------------------------------------------------------------------
# Expected score returned for every tier x pin x wind combination, arbitrary
# aim points.
# ---------------------------------------------------------------------------

def test_expected_score_every_tier_pin_wind_combination():
    for tier in data.TIERS:
        for pin in data.PINS:
            aim = (data.PINS[pin]["x"], data.PINS[pin]["y"])
            for wind in (False, True):
                s = model.expected_score(tier, pin, aim, wind=wind)
                assert isinstance(s, float)
                assert 1.0 < s < 12.0


def test_expected_score_at_arbitrary_aim_points():
    for aim in [(-20.0, 130.0), (0.0, 155.0), (15.0, 175.0), (-3.5, 148.25), (40.0, 200.0)]:
        s = model.expected_score(15, "center", aim)
        assert 1.0 < s < 15.0


def test_expected_score_rejects_unknown_tier_or_pin():
    with pytest.raises(KeyError):
        model.expected_score(7, "center", (0.0, 155.0))
    with pytest.raises(KeyError):
        model.expected_score(15, "nowhere", (0.0, 155.0))


# ---------------------------------------------------------------------------
# Green width/depth and anisotropy enter as parameters with stated ranges,
# never single constants.
# ---------------------------------------------------------------------------

def test_green_width_is_an_overridable_parameter():
    aim = (data.PINS["center"]["x"], data.PINS["center"]["y"])
    lo, hi = data.HOLE["green_width_yd_range"]
    s_narrow = model.expected_score(15, "center", aim, green_width_yd=lo)
    s_wide = model.expected_score(15, "center", aim, green_width_yd=hi)
    assert s_narrow != s_wide
    assert s_narrow >= s_wide - 1e-9  # a narrower green never scores better on average


def test_front_third_depth_is_an_overridable_parameter():
    aim = (data.PINS["center"]["x"], data.PINS["center"]["y"])
    lo, hi = data.HOLE["front_third_depth_yd_range"]
    s_shallow = model.expected_score(15, "center", aim, front_third_depth_yd=lo)
    s_deep = model.expected_score(15, "center", aim, front_third_depth_yd=hi)
    assert s_shallow != s_deep


def test_anisotropy_ratio_is_an_overridable_parameter():
    aim = (data.PINS["center"]["x"], data.PINS["center"]["y"])
    lo, hi = data.ANISOTROPY["range"]
    s_lo = model.expected_score(15, "center", aim, anisotropy_ratio=lo)
    s_hi = model.expected_score(15, "center", aim, anisotropy_ratio=hi)
    assert s_lo != s_hi


# ---------------------------------------------------------------------------
# Wind worsens expected score at every pin.
# ---------------------------------------------------------------------------

def test_wind_worsens_expected_score_at_every_pin():
    for tier in data.TIERS:
        for pin in data.PINS:
            aim = (data.PINS[pin]["x"], data.PINS[pin]["y"])
            calm = model.expected_score(tier, pin, aim, wind=False)
            windy = model.expected_score(tier, pin, aim, wind=True)
            assert windy > calm, (tier, pin)


# ---------------------------------------------------------------------------
# Sensible edge behavior.
# ---------------------------------------------------------------------------

def test_aiming_far_off_the_green_scores_worse_than_aiming_at_pin():
    pin_aim = (data.PINS["center"]["x"], data.PINS["center"]["y"])
    far_aim = (pin_aim[0] + 100.0, pin_aim[1])
    s_pin = model.expected_score(15, "center", pin_aim)
    s_far = model.expected_score(15, "center", far_aim)
    assert s_far > s_pin
    assert s_far < 20.0  # still finite and bounded, no blow-up


def test_near_zero_dispersion_oval_matches_exact_point_price():
    pin = "center"
    p = data.PINS[pin]
    aim = (p["x"], p["y"])
    region, short_sided = model.region_at(aim[0], aim[1], pin)
    assert region == "green"
    expected = 1.0 + model._green_strokes(20, 0.0)
    got = model.score_for_oval(1e-9, 1e-9, 20, pin, aim)
    assert abs(got - expected) < 1e-3


def test_near_zero_dispersion_oval_off_green_matches_hazard_price():
    pin = "left"
    geom = model._resolve_geometry()
    bunker_hi = data.HOLE["front_bunker_x_range"][1]
    aim_x = bunker_hi + 5.0
    front_edge = model._front_edge_yd(aim_x, geom)
    aim = (aim_x, front_edge - 2.0)  # short of the green, off the bunker's lateral band
    region, short_sided = model.region_at(aim[0], aim[1], pin)
    assert region == "creek"
    expected = 1.0 + model._creek_strokes(20, short_sided)
    got = model.score_for_oval(1e-9, 1e-9, 20, pin, aim)
    assert abs(got - expected) < 1e-3


# ---------------------------------------------------------------------------
# Sanity direction: aiming at the creek edge scores worse than center green,
# 20-handicap.
# ---------------------------------------------------------------------------

def test_creek_edge_aim_worse_than_center_green_aim_for_low_dispersion_tiers():
    # This directional check only holds for tiers whose distance dispersion
    # is small relative to the creek band (data.CREEK_WIDTH_YD +
    # data.BANK_ROLLBACK_YD, 9 yd default). Before the region-geometry fix
    # (creek band finite, short_fairway priced as a plain recovery leg
    # instead of the creek penalty), every non-bunker short miss was priced
    # as the creek penalty however far short it landed, so this held for
    # every tier. Tier 20's own distance sigma (~33.6 yd at the 155-yd
    # shot) dwarfs the 9-yd band: most of its short misses now land in the
    # cheap short_fairway region regardless of aim point, so aiming right
    # at the creek's edge and aiming at the pin both mostly avoid the water,
    # and the ordering this test checks is no longer guaranteed for that
    # tier -- see VALIDATION_NOTES.md's creek-band-fix section for the
    # tier-by-tier numbers (it flips at tier 10 and stays flipped through
    # 20). Scratch and the 5-handicap tier, with much tighter dispersion,
    # still show the expected direction cleanly.
    pin = "center"
    p = data.PINS[pin]
    geom = model._resolve_geometry()
    front_edge = model._front_edge_yd(0.0, geom)
    creek_aim = (0.0, front_edge - 1.0)
    pin_aim = (p["x"], p["y"])
    for tier in (0, 5):
        s_creek = model.expected_score(tier, pin, creek_aim)
        s_pin = model.expected_score(tier, pin, pin_aim)
        assert s_creek > s_pin, (tier, s_creek, s_pin)


def test_better_tier_scores_better_at_every_pin():
    for pin in data.PINS:
        aim = (data.PINS[pin]["x"], data.PINS[pin]["y"])
        vals = [model.expected_score(t, pin, aim) for t in data.TIERS]
        assert all(a <= b + 1e-9 for a, b in zip(vals, vals[1:])), pin


# ---------------------------------------------------------------------------
# region_at classification sanity.
# ---------------------------------------------------------------------------

def test_region_at_on_pin_is_always_green():
    for pin, p in data.PINS.items():
        region, short_sided = model.region_at(p["x"], p["y"], pin)
        assert region == "green"
        assert short_sided is False


def test_region_at_rejects_unknown_pin():
    with pytest.raises(KeyError):
        model.region_at(0.0, 155.0, "nowhere")


def test_short_sided_flagged_correctly_for_front_and_back_pins():
    # None of this release's three named pins is a front pin (front_frac <
    # 0.5) after "left" was repositioned to a mid-depth placement (issue
    # #5's locked welcoming/accessible left pin -- see data.py's PINS
    # comment), so the front-pin short-siding branch is exercised here
    # against a temporary synthetic pin (region_at requires its pin argument
    # to be a data.PINS key) rather than losing this coverage entirely.
    synthetic_front = {
        "label": "test-front-pin", "x": -6.0, "y": data._FRONT_LEFT_SLOPE_REFERENCE_Y,
        "front_frac": 0.15, "back_frac": 0.85,
        "local_depth_yd_range": (12.0, 16.0),
    }
    data.PINS["_test_front"] = synthetic_front
    try:
        front_edge = model._front_edge_yd(synthetic_front["x"], model._resolve_geometry())
        _, short_sided = model.region_at(synthetic_front["x"], front_edge - 1.0, "_test_front")
        assert short_sided is True
    finally:
        del data.PINS["_test_front"]

    # "sunday" is a back pin (back_frac < 0.5): a miss LONG of it is short-sided.
    p = data.PINS["sunday"]
    back_edge = model._back_edge_yd(p["x"], model._resolve_geometry())
    _, short_sided = model.region_at(p["x"], back_edge + 1.0, "sunday")
    assert short_sided is True


def test_left_pin_mid_depth_placement_is_never_short_sided():
    # FIX (this pass): "left" was repositioned to front_frac == back_frac ==
    # 0.5, the model's encoding of the locked pin cast's welcoming/
    # accessible left pin -- plenty of green both short and long of the
    # flag, so neither direction of miss should read as short-sided, the
    # same symmetric behavior the "center" pin already has.
    p = data.PINS["left"]
    geom = model._resolve_geometry()
    front_edge = model._front_edge_yd(p["x"], geom)
    back_edge = model._back_edge_yd(p["x"], geom)
    _, short_sided_short = model.region_at(p["x"], front_edge - 1.0, "left")
    _, short_sided_long = model.region_at(p["x"], back_edge + 1.0, "left")
    assert short_sided_short is False
    assert short_sided_long is False


# ---------------------------------------------------------------------------
# Sanity-sweep regression tests (finding 1: Sunday-pin thesis inversion;
# finding 2: absolute-score calibration). Each documents the mechanism it
# guards against, not just the bound.
# ---------------------------------------------------------------------------

def test_front_edge_is_diagonal_not_flat():
    # Anchor 3: the green is diagonal, "shoe-sole"-shaped, requiring more
    # carry over Rae's Creek as the target moves toward the Sunday (right)
    # side. A flat front edge (constant y regardless of x) silently drops
    # this hazard for every pin except the one directly being scored, which
    # is what let the Sunday pin's short-right water risk go unpriced.
    geom = model._resolve_geometry()
    left_x, sunday_x = data.PINS["left"]["x"], data.PINS["sunday"]["x"]
    assert sunday_x > left_x
    front_left = model._front_edge_yd(left_x, geom)
    front_sunday = model._front_edge_yd(sunday_x, geom)
    assert front_sunday > front_left, "carry required to clear the creek must grow moving right"


def test_green_region_uses_full_green_depth_not_just_local_pin_pocket():
    # The center pin's front-third figure (9-12 yd, Anchor 3's best-corroborated
    # single number) describes ONE section of the green, not the whole putting
    # surface. Gating the "green" outcome on that narrow local pocket alone
    # (instead of data.HOLE["green_depth_yd_range"], ANCHORED as a range but
    # never wired into region_at) shrinks the scorable green far below the
    # ~35-yd-diameter effective green data.py's own sigma calibration assumes,
    # which is what inflated every tier's expected score.
    geom = model._resolve_geometry()
    center = data.PINS["center"]
    depth_lo, depth_hi = data.HOLE["green_depth_yd_range"]
    # A point well past the center pin's own local front-third pocket, but
    # still inside the green's overall published depth range, must be "green".
    y = center["y"] + 0.5 * (depth_lo + depth_hi) * 0.5  # comfortably inside the full green, past the local pocket
    region, _ = model.region_at(center["x"], y, "center")
    assert region == "green"


def test_sunday_sucker_pin_thesis_holds_for_marginal_tiers():
    # CONTEXT.md's sucker-pin definition: aiming directly at a sucker pin
    # raises expected score for the tier in question versus playing safely
    # (here: aiming at the center of the green while the flag stays at
    # Sunday). The piece's whole argument rests on this holding for the
    # marginal/high tiers; before the geometry fix, the flat creek edge and
    # the too-small green target inverted it for every tier.
    for tier in (10, 15, 20):
        at_pin = model.expected_score(tier, "sunday", (data.PINS["sunday"]["x"], data.PINS["sunday"]["y"]))
        center_aim = model.expected_score(tier, "sunday", (data.PINS["center"]["x"], data.PINS["center"]["y"]))
        assert center_aim < at_pin, (tier, at_pin, center_aim)


def test_scratch_center_aim_expected_score_is_credible():
    # Finding 2's calibration bound: a scratch amateur's expected score on a
    # 155-yd par 3, aiming at the center pin in calm air, should land near
    # 3.3-3.5, not the ~3.7 the mis-sized green previously produced.
    s = model.expected_score(0, "center", (data.PINS["center"]["x"], data.PINS["center"]["y"]))
    assert 3.15 < s < 3.6


def test_twenty_handicap_center_aim_expected_score_is_credible():
    # Bound lowered from 4.0-4.6 to 3.85-4.6 (region-geometry fix, this
    # pass): the old infinite-creek rule priced every short miss, however
    # far short, as a penalty drop, inflating this score. A 20-handicap's
    # own distance sigma (~33.6 yd) means most short misses now land in the
    # cheap short_fairway region instead, landing at 3.945 -- still a
    # believable price for a mediocre approach on a 155-yd hole, not the
    # unrealistically cheap number an under-priced hazard would produce.
    s = model.expected_score(20, "center", (data.PINS["center"]["x"], data.PINS["center"]["y"]))
    assert 3.85 < s < 4.6


def test_long_trouble_beyond_back_bunkers_prices_worse_than_plain_rough():
    # Anchor 3: the two back bunkers sit "cut into an azalea-lined ledge."
    # A miss that clears the bunkers entirely still lands in that ledge
    # (pine straw / azalea, a materially tougher recovery), not plain rough.
    # Pricing it identically to a close miss lets an aim-point search treat
    # "way overclub the green" as a free way to dodge the creek.
    tier, short_sided = 15, False
    rough = model._region_strokes("greenside_rough", short_sided, tier, 0.0, 0.0, "center")
    trouble = model._region_strokes("long_trouble", short_sided, tier, 0.0, 0.0, "center")
    assert trouble > rough


def test_overclubbing_well_past_the_green_carries_a_real_penalty():
    # A 20-handicap taking dramatically more club than the Sunday pin needs
    # (well past the back bunkers, deep into the azalea ledge) must not score
    # better than playing the pin itself -- there should be no free lunch in
    # "just fly it over all the trouble."
    p = data.PINS["sunday"]
    at_pin = model.expected_score(20, "sunday", (p["x"], p["y"]))
    way_long = model.expected_score(20, "sunday", (p["x"], p["y"] + 50.0))
    assert way_long >= at_pin - 1e-9


# ---------------------------------------------------------------------------
# FIX 1 (#8's flagged defect): long_trouble pricing had no distance falloff,
# so expected score kept improving without bound the farther an aim point
# carried past the green -- the #8 optimizer review traced this out to a
# 150-yd carry adjustment before capping its search at a stated budget.
# model._recovery_strokes now blends the trouble price toward a hazard-like
# (creek) price as overshoot_yd grows (data.LONG_TROUBLE_FALLOFF_YD, MODELED,
# sensitivity range data.LONG_TROUBLE_FALLOFF_YD_RANGE), which must produce a
# genuine interior minimum in expected score as a function of carry past the
# green, for every tier and every pin -- not just the Sunday pin this test
# module already exercises above.
# ---------------------------------------------------------------------------

def test_long_trouble_falloff_gives_every_tier_and_pin_an_interior_minimum():
    # No improvement at +40 yd of carry vs +15 yd, for every tier x pin: the
    # regression guard for the exact failure mode #8 found (an unbounded
    # "just carry it farther" asymptote with no interior optimum).
    for tier in data.TIERS:
        for pin in data.PINS:
            p = data.PINS[pin]
            s15 = model.expected_score(tier, pin, (p["x"], p["y"] + 15.0), n_grid=41)
            s40 = model.expected_score(tier, pin, (p["x"], p["y"] + 40.0), n_grid=41)
            assert s40 >= s15 - 1e-9, (tier, pin, s15, s40)


def test_long_trouble_falloff_price_grows_with_overshoot():
    # Directly on the pricing function #8 flagged: at fixed short-sidedness,
    # a deeper overshoot must never price cheaper than a shallower one, and a
    # large overshoot must price strictly worse than sitting right at the
    # buffer edge (overshoot_yd=0) -- the flat-price defect made these equal
    # at every distance.
    tier, short_sided = 15, False
    at_buffer = model._recovery_strokes(tier, short_sided, sand=False, trouble=True, overshoot_yd=0.0)
    shallow = model._recovery_strokes(tier, short_sided, sand=False, trouble=True, overshoot_yd=10.0)
    deep = model._recovery_strokes(tier, short_sided, sand=False, trouble=True, overshoot_yd=40.0)
    assert at_buffer <= shallow + 1e-9 <= deep + 1e-9
    assert deep > at_buffer, "distance falloff must make a materially deeper miss cost more"


def test_long_trouble_falloff_never_exceeds_the_hazard_like_ceiling():
    # The blend approaches, but should not exceed, the creek's price -- the
    # "trending toward a hazard-like cost" ceiling named in the fix, not an
    # unbounded penalty of its own.
    tier, short_sided = 10, False
    ceiling = model._creek_strokes(tier, short_sided)
    very_deep = model._recovery_strokes(tier, short_sided, sand=False, trouble=True, overshoot_yd=500.0)
    assert very_deep <= ceiling + 1e-6


def test_implied_gir_near_published_anchor_at_center_pin():
    # data.GIR50_DISTANCE_YD says scratch reaches 50% GIR from 165 yd; at the
    # shorter 155-yd tee shot, GIR against the ACTUAL Augusta 12 green should
    # sit comfortably above a coin flip, not the ~19% the local-pocket-only
    # green produced.
    aim = (data.PINS["center"]["x"], data.PINS["center"]["y"])
    sigma_d, sigma_l = model.oval_for_tier(0)
    import numpy as np
    n_std, n_grid = 4.0, 61
    mean_x, mean_y = aim
    ys = np.linspace(mean_y - n_std * sigma_d, mean_y + n_std * sigma_d, n_grid)
    xs = np.linspace(mean_x - n_std * sigma_l, mean_x + n_std * sigma_l, n_grid)
    wy = np.exp(-0.5 * ((ys - mean_y) / sigma_d) ** 2); wy /= wy.sum()
    wx = np.exp(-0.5 * ((xs - mean_x) / sigma_l) ** 2); wx /= wx.sum()
    green_mass = 0.0
    for yi, wyi in zip(ys, wy):
        for xi, wxi in zip(xs, wx):
            region, _ = model.region_at(float(xi), float(yi), "center")
            if region == "green":
                green_mass += wyi * wxi
    assert green_mass > 0.40


# ---------------------------------------------------------------------------
# Anchor 8 (#9 follow-up): anchored putting curve replaces the invented
# `1.5 + 0.012*ft` formula, which floored expected putts at 1.5 from any
# distance including a tap-in and priced a Tour player at ~1.6 putts from 3
# feet against a published 96% make rate. model.putt_probabilities and
# tour.tour_putt_probabilities are the two ANCHORED replacement curves.
# ---------------------------------------------------------------------------

_TEST_DISTANCES_FT = [0.0, 1.0, 3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 40.0, 60.0, 90.0]


def test_putt_probabilities_sum_to_one_at_every_tested_distance():
    for tier in data.TIERS:
        for ft in _TEST_DISTANCES_FT:
            p1, p2, p3 = model.putt_probabilities(tier, ft)
            assert p1 >= 0.0 and p2 >= 0.0 and p3 >= 0.0, (tier, ft, p1, p2, p3)
            assert abs((p1 + p2 + p3) - 1.0) < 1e-9, (tier, ft, p1, p2, p3)
    for ft in _TEST_DISTANCES_FT:
        p1, p2, p3 = tour.tour_putt_probabilities(ft)
        assert p1 >= 0.0 and p2 >= 0.0 and p3 >= 0.0, (ft, p1, p2, p3)
        assert abs((p1 + p2 + p3) - 1.0) < 1e-9, (ft, p1, p2, p3)


def test_tour_expected_putts_reproduces_anchor_8_arithmetic():
    # Anchor 8's own arithmetic check: expected putts = 1*make + 2*(1-make-
    # three_putt) + 3*three_putt, computed from the two ANCHORED Tour tables,
    # reproduces the release brief's recalled curve to two decimal places.
    target_by_ft = {5: 1.23, 10: 1.61, 20: 1.87, 30: 1.98, 60: 2.21}
    for ft, target in target_by_ft.items():
        got = tour._tour_green_strokes(float(ft))
        assert abs(got - target) < 0.02, (ft, got, target)


def test_putt_expected_value_increases_monotonically_with_distance_for_every_tier():
    for tier in data.TIERS:
        values = [model._green_strokes(tier, ft) for ft in _TEST_DISTANCES_FT]
        assert all(a <= b + 1e-9 for a, b in zip(values, values[1:])), (tier, values)
    tour_values = [tour._tour_green_strokes(ft) for ft in _TEST_DISTANCES_FT]
    assert all(a <= b + 1e-9 for a, b in zip(tour_values, tour_values[1:])), tour_values


def test_twenty_handicap_needs_more_putts_than_scratch_at_every_distance():
    for ft in _TEST_DISTANCES_FT:
        scratch = model._green_strokes(0, ft)
        twenty = model._green_strokes(20, ft)
        assert twenty >= scratch - 1e-9, (ft, scratch, twenty)
    # At least one tested distance must show a real (non-degenerate) gap,
    # confirming this isn't trivially true because both curves are flat.
    assert any(model._green_strokes(20, ft) > model._green_strokes(0, ft) + 1e-6
               for ft in _TEST_DISTANCES_FT)


def test_tap_in_expected_putts_below_1point1_for_every_tier():
    for tier in data.TIERS:
        assert model._green_strokes(tier, 1.0) < 1.1, (tier, model._green_strokes(tier, 1.0))


# ---------------------------------------------------------------------------
# Region-geometry fix (this pass, #12): Rae's Creek is a finite band short
# of the green's front edge (data.CREEK_WIDTH_YD + data.BANK_ROLLBACK_YD),
# not every yard of short miss back to the tee. Before this fix,
# model.region_at classified any non-bunker miss short of the front edge as
# "creek," however far short, which overpriced a 15/20-handicap's ordinary
# short miss as a water penalty. See model.region_at's docstring and
# VALIDATION_NOTES.md's "Creek band fix (rev 4)" section for the full
# before/after picture.
# ---------------------------------------------------------------------------

def test_one_yard_short_of_front_edge_is_creek():
    # x offset outside the front bunker's lateral band (data.HOLE
    # ["front_bunker_x_range"]) so a short miss here classifies purely on
    # the creek-band boundary, not the bunker's own depth window.
    pin = "center"
    geom = model._resolve_geometry()
    x = data.HOLE["front_bunker_x_range"][1] + 5.0
    front_edge = model._front_edge_yd(x, geom)
    region, _ = model.region_at(x, front_edge - 1.0, pin)
    assert region == "creek"


def test_past_the_creek_and_bank_band_is_short_fairway():
    pin = "center"
    geom = model._resolve_geometry()
    x = data.HOLE["front_bunker_x_range"][1] + 5.0
    front_edge = model._front_edge_yd(x, geom)
    band = data.CREEK_WIDTH_YD + data.BANK_ROLLBACK_YD
    region, _ = model.region_at(x, front_edge - (band + 1.0), pin)
    assert region == "short_fairway"


def test_finite_creek_band_scores_better_than_the_old_all_creek_rule():
    # Monkeypatch the band out to 1000 yd (CREEK_WIDTH_YD=1000, BANK_
    # ROLLBACK_YD=0) to reproduce the pre-fix rule -- every non-bunker short
    # miss, however far short, priced as the creek penalty -- and confirm
    # the fix's whole point: a 25-yd-short aim for a 20-handicap now scores
    # strictly better than it did under that old rule.
    pin = "center"
    p = data.PINS[pin]
    aim = (p["x"], p["y"] - 25.0)  # 25 yd short of the center pin
    fixed_score = model.expected_score(20, pin, aim)
    orig_creek, orig_bank = data.CREEK_WIDTH_YD, data.BANK_ROLLBACK_YD
    try:
        data.CREEK_WIDTH_YD, data.BANK_ROLLBACK_YD = 1000.0, 0.0
        old_rule_score = model.expected_score(20, pin, aim)
    finally:
        data.CREEK_WIDTH_YD, data.BANK_ROLLBACK_YD = orig_creek, orig_bank
    assert fixed_score < old_rule_score, (fixed_score, old_rule_score)


def test_sunday_sucker_pin_thesis_still_holds_after_creek_band_fix():
    # Restates test_sunday_sucker_pin_thesis_holds_for_marginal_tiers under
    # this pass's own name: attacking the Sunday pin still costs more than
    # bailing to the center of the green, for every marginal tier, with the
    # creek band now finite rather than infinite.
    for tier in (10, 15, 20):
        at_pin = model.expected_score(tier, "sunday", (data.PINS["sunday"]["x"], data.PINS["sunday"]["y"]))
        center_aim = model.expected_score(tier, "sunday", (data.PINS["center"]["x"], data.PINS["center"]["y"]))
        assert center_aim < at_pin, (tier, at_pin, center_aim)


def test_creek_band_width_sensitivity_on_sunday_verdict_label():
    # Sweep CREEK_WIDTH_YD + BANK_ROLLBACK_YD across the combined
    # sensitivity range (6-13 yd, the two constants' own stated ranges),
    # holding BANK_ROLLBACK_YD at its default and varying CREEK_WIDTH_YD to
    # hit each combined total. The Sunday-pin verdict label (bail/either
    # works/attack) must not change at tiers 10/15/20, calm, across the
    # sweep -- the sucker-pin finding should not be an artifact of exactly
    # where this MODELED band sits. flip_set's own cheaper search settings
    # (FLIP_SET_*) keep the sweep fast. See VALIDATION_NOTES.md for the
    # recorded delta swing.
    import optimizer

    orig_creek, orig_bank = data.CREEK_WIDTH_YD, data.BANK_ROLLBACK_YD
    bank = orig_bank
    totals = (6.0, orig_creek + orig_bank, 13.0)
    labels = {}
    deltas = {}
    try:
        for total in totals:
            data.CREEK_WIDTH_YD = total - bank
            data.BANK_ROLLBACK_YD = bank
            for tier in (10, 15, 20):
                v = optimizer.optimize_aim(tier, "sunday", False,
                                            n_grid=optimizer.FLIP_SET_N_GRID,
                                            search_n_grid=optimizer.FLIP_SET_SEARCH_N_GRID,
                                            coarse_step_yd=optimizer.FLIP_SET_COARSE_STEP_YD,
                                            lateral_range_yd=optimizer.FLIP_SET_LATERAL_RANGE_YD,
                                            carry_range_yd=optimizer.FLIP_SET_CARRY_RANGE_YD)
                labels[(total, tier)] = optimizer.verdict_label(v)
                deltas[(total, tier)] = v.delta
    finally:
        data.CREEK_WIDTH_YD, data.BANK_ROLLBACK_YD = orig_creek, orig_bank

    for tier in (10, 15, 20):
        tier_labels = {labels[(t, tier)] for t in totals}
        assert tier_labels == {"bail"}, (tier, labels)

    spread = max(deltas.values()) - min(deltas.values())
    assert spread < 0.07, (
        f"Sunday verdict delta swings {spread:.4f} strokes across the "
        "creek-band sensitivity range, wider than expected"
    )


# ---------------------------------------------------------------------------
# Pitch-over-water risk fix (rev 5, issue #8): the short_fairway leg (rev 4's
# creek-band fix) priced the pitch back over Rae's Creek as a plain non-sand
# recovery leg with no water risk at all -- this section's tests check the
# new dunk-risk mixture formula directly, and that the Sunday-pin bail
# verdict is not an artifact of exactly where data.PITCH_OVER_WATER_DUNK_PCT
# sits.
# ---------------------------------------------------------------------------

def test_short_fairway_prices_the_pitch_over_water_dunk_risk():
    # model._short_fairway_strokes's own formula, checked directly against
    # its primitives: (1 - p) * recovery + p * (CREEK_PENALTY_STROKES + 1.0
    # + recovery_after_drop). recovery_after_drop is the same non-sand
    # recovery leg as `recovery`, but replayed from the drop area right at
    # the creek's edge (far_short_yd=0), never carrying the far_short_yd
    # falloff `recovery` itself may carry.
    for tier in data.TIERS:
        p = data.PITCH_OVER_WATER_DUNK_PCT[tier]
        for is_short_sided in (False, True):
            for far_short_yd in (0.0, 5.0, 15.0):
                recovery = model._recovery_strokes(tier, is_short_sided, sand=False, far_short_yd=far_short_yd)
                recovery_after_drop = model._recovery_strokes(tier, is_short_sided, sand=False)
                expected = (1.0 - p) * recovery + p * (data.CREEK_PENALTY_STROKES + 1.0 + recovery_after_drop)
                priced = model._short_fairway_strokes(tier, is_short_sided, far_short_yd)
                assert priced == pytest.approx(expected, abs=1e-9), (tier, is_short_sided, far_short_yd)
                # The whole point of the fix: this leg must now cost strictly
                # more than the plain (rev 4) recovery price it replaced,
                # since PITCH_OVER_WATER_DUNK_PCT is positive at every tier
                # and the dunk branch is always worse than the plain leg.
                assert priced > recovery, (tier, is_short_sided, far_short_yd)


def test_tour_short_fairway_mirrors_amateur_formula_with_tour_dunk_pct():
    # tour._tour_short_fairway_strokes mirrors model._short_fairway_strokes
    # exactly, using the scalar data.TOUR_PITCH_OVER_WATER_DUNK_PCT in place
    # of the amateur tier-keyed dict.
    p = data.TOUR_PITCH_OVER_WATER_DUNK_PCT
    for is_short_sided in (False, True):
        for far_short_yd in (0.0, 5.0, 15.0):
            recovery = tour._tour_recovery_strokes(is_short_sided, sand=False, far_short_yd=far_short_yd)
            recovery_after_drop = tour._tour_recovery_strokes(is_short_sided, sand=False)
            expected = (1.0 - p) * recovery + p * (data.CREEK_PENALTY_STROKES + 1.0 + recovery_after_drop)
            priced = tour._tour_short_fairway_strokes(is_short_sided, far_short_yd)
            assert priced == pytest.approx(expected, abs=1e-9), (is_short_sided, far_short_yd)



# ---------------------------------------------------------------------------
# Mishit mixture (rev 6, Sunny's finding): a single symmetric Gaussian per
# tier for distance error let a 20-handicap post a LOWER water rate than a
# scratch player at the same aim, and still showed water risk at a 200-yd
# carry -- both wrong on the real hole. model.mishit_mixture_params splits
# each tier's anchored, anisotropy-split distance sigma into a solid-strike
# core plus a short mishit tail; these tests check the algebra directly and
# the Sunday-pin verdict's stability across the new constants' own
# sensitivity ranges. See tests/test_export.py for the water-rate
# acceptance checks themselves (both disclosed as xfail near-misses).
# ---------------------------------------------------------------------------

def test_mixture_preserves_anchored_second_moment():
    # sigma_solid^2 + p_mis * k_mis^2 must equal the anchored, anisotropy-
    # split sigma_d^2 (model.oval_for_tier's own sigma_d), to high
    # precision, for every tier -- the algebra model.mishit_mixture_params'
    # docstring states. This is what keeps the tier's anchored mean
    # proximity reproduced to first order despite the mixture.
    for tier in data.TIERS:
        sigma_d, sigma_l_plain = model.oval_for_tier(tier)
        sigma_solid, sigma_l, p_mis, k_mis = model.mishit_mixture_params(tier)
        assert abs(sigma_l - sigma_l_plain) < 1e-12, "sigma_l must be untouched by the mixture"
        lhs = sigma_solid ** 2 + p_mis * k_mis ** 2
        assert abs(lhs - sigma_d ** 2) < 1e-6, (tier, lhs, sigma_d ** 2)
        # sigma_solid must be strictly positive (the equation has a real
        # solution) and strictly less than sigma_d (some of the total
        # spread now lives in the mishit tail's offset, not the core).
        assert 0.0 < sigma_solid < sigma_d, (tier, sigma_solid, sigma_d)


def test_mishit_mixture_params_matches_data_constants():
    for tier in data.TIERS:
        _sigma_solid, _sigma_l, p_mis, k_mis = model.mishit_mixture_params(tier)
        assert p_mis == data.MISHIT_PCT[tier]
        assert abs(k_mis - data.MISHIT_SHORT_FRAC * data.TEE_SHOT_YD) < 1e-9


def test_tour_mishit_mixture_preserves_anchored_second_moment():
    sigma_d, sigma_l_plain = tour.tour_oval()
    sigma_solid, sigma_l, p_mis, k_mis = tour.tour_mishit_mixture_params()
    assert abs(sigma_l - sigma_l_plain) < 1e-12
    assert p_mis == data.TOUR_MISHIT_PCT
    lhs = sigma_solid ** 2 + p_mis * k_mis ** 2
    assert abs(lhs - sigma_d ** 2) < 1e-6
    assert 0.0 < sigma_solid < sigma_d


def test_expected_score_mixture_matches_manual_weighted_sum():
    # model.expected_score must equal (1 - p_mis) * score_for_oval(solid) +
    # p_mis * score_for_oval(mishit), computed directly against the same
    # primitives, for both calm and windy conditions.
    for tier in (0, 20):
        for wind in (False, True):
            pin = "sunday"
            p = data.PINS[pin]
            aim = (p["x"], p["y"])
            sigma_solid, sigma_l, p_mis, k_mis = model.mishit_mixture_params(tier)
            mean_shift_y = 0.0
            if wind:
                mean_shift_y = -data.WIND["carry_penalty_yd"]
                sigma_solid = sigma_solid * data.WIND["dispersion_inflation"]
                sigma_l = sigma_l * data.WIND["dispersion_inflation"]
            score_solid = model.score_for_oval(sigma_solid, sigma_l, tier, pin, aim, mean_shift_y)
            score_mis = model.score_for_oval(sigma_solid, sigma_l, tier, pin, aim, mean_shift_y - k_mis)
            expected = (1.0 - p_mis) * score_solid + p_mis * score_mis
            got = model.expected_score(tier, pin, aim, wind=wind)
            assert abs(got - expected) < 1e-9, (tier, wind, got, expected)


def test_mishit_pct_and_short_frac_sensitivity_on_sunday_verdict_label():
    # Sweep MISHIT_PCT by its own stated 0.5x-1.5x multiplier and
    # MISHIT_SHORT_FRAC across its own stated 0.10-0.20 range (a 3x3 grid,
    # flip_set's own cheaper search settings) and confirm the Sunday-pin
    # verdict label stays "bail" at tiers 10/15/20, calm, at every sweep
    # point -- the sucker-pin finding should not be an artifact of exactly
    # where these two new MODELED constants sit. See VALIDATION_NOTES.md
    # for the recorded carry-adjustment swing and what else moves.
    import optimizer

    orig_pct = dict(data.MISHIT_PCT)
    orig_frac = data.MISHIT_SHORT_FRAC
    labels = {}
    carries = {}
    try:
        for pct_mult in (0.5, 1.0, 1.5):
            for frac in (0.10, 0.15, 0.20):
                data.MISHIT_PCT = {t: v * pct_mult for t, v in orig_pct.items()}
                data.MISHIT_SHORT_FRAC = frac
                for tier in (10, 15, 20):
                    v = optimizer.optimize_aim(tier, "sunday", False,
                                                n_grid=optimizer.FLIP_SET_N_GRID,
                                                search_n_grid=optimizer.FLIP_SET_SEARCH_N_GRID,
                                                coarse_step_yd=optimizer.FLIP_SET_COARSE_STEP_YD,
                                                lateral_range_yd=optimizer.FLIP_SET_LATERAL_RANGE_YD,
                                                carry_range_yd=optimizer.FLIP_SET_CARRY_RANGE_YD)
                    labels[(pct_mult, frac, tier)] = optimizer.verdict_label(v)
                    carries[(pct_mult, frac, tier)] = v.carry_adjustment_yd
    finally:
        data.MISHIT_PCT = orig_pct
        data.MISHIT_SHORT_FRAC = orig_frac

    for tier in (10, 15, 20):
        tier_labels = {labels[(m, f, tier)] for m in (0.5, 1.0, 1.5) for f in (0.10, 0.15, 0.20)}
        assert tier_labels == {"bail"}, (tier, labels)

    for tier in (10, 15, 20):
        tier_carries = [carries[(m, f, tier)] for m in (0.5, 1.0, 1.5) for f in (0.10, 0.15, 0.20)]
        spread = max(tier_carries) - min(tier_carries)
        # Recorded (not just bounded), matching this file's other
        # sensitivity sweeps, so VALIDATION_NOTES.md can quote the exact
        # swing; a generous bound still catches a runaway regression.
        assert spread < 15.0, (
            f"tier {tier}: Sunday carry-adjustment swings {spread:.2f} yd "
            "across the mishit-mixture sensitivity sweep, wider than expected"
        )


def test_pitch_over_water_dunk_pct_sensitivity_on_sunday_verdict_label():
    # Sweep PITCH_OVER_WATER_DUNK_PCT by its own stated multiplicative
    # sensitivity range (0.5x-1.5x on every tier's own figure) and confirm
    # the Sunday-pin verdict label stays "bail" at tiers 10/15/20, calm, at
    # every sweep point -- the sucker-pin finding should not be an artifact
    # of exactly where this MODELED dunk rate sits. flip_set's own cheaper
    # search settings (FLIP_SET_*) keep the sweep fast. See
    # VALIDATION_NOTES.md for the recorded carry-adjustment swing.
    import optimizer

    orig = dict(data.PITCH_OVER_WATER_DUNK_PCT)
    mults = (0.5, 1.0, 1.5)
    labels = {}
    carries = {}
    try:
        for mult in mults:
            data.PITCH_OVER_WATER_DUNK_PCT = {t: v * mult for t, v in orig.items()}
            for tier in (10, 15, 20):
                v = optimizer.optimize_aim(tier, "sunday", False,
                                            n_grid=optimizer.FLIP_SET_N_GRID,
                                            search_n_grid=optimizer.FLIP_SET_SEARCH_N_GRID,
                                            coarse_step_yd=optimizer.FLIP_SET_COARSE_STEP_YD,
                                            lateral_range_yd=optimizer.FLIP_SET_LATERAL_RANGE_YD,
                                            carry_range_yd=optimizer.FLIP_SET_CARRY_RANGE_YD)
                labels[(mult, tier)] = optimizer.verdict_label(v)
                carries[(mult, tier)] = v.carry_adjustment_yd
    finally:
        data.PITCH_OVER_WATER_DUNK_PCT = orig

    for tier in (10, 15, 20):
        tier_labels = {labels[(m, tier)] for m in mults}
        assert tier_labels == {"bail"}, (tier, labels)

    for tier in (10, 15, 20):
        spread = max(carries[(m, tier)] for m in mults) - min(carries[(m, tier)] for m in mults)
        # Recorded (not just bounded) so VALIDATION_NOTES.md can quote the
        # exact swing; a generous bound still catches a runaway regression.
        assert spread < 15.0, (
            f"tier {tier}: Sunday carry-adjustment swings {spread:.2f} yd "
            "across the dunk-pct sensitivity sweep, wider than expected"
        )
