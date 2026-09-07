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

def test_creek_edge_aim_worse_than_center_green_aim_for_20_handicap():
    pin = "center"
    p = data.PINS[pin]
    geom = model._resolve_geometry()
    front_edge = model._front_edge_yd(0.0, geom)
    creek_aim = (0.0, front_edge - 1.0)
    pin_aim = (p["x"], p["y"])
    s_creek = model.expected_score(20, pin, creek_aim)
    s_pin = model.expected_score(20, pin, pin_aim)
    assert s_creek > s_pin


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
    s = model.expected_score(20, "center", (data.PINS["center"]["x"], data.PINS["center"]["y"]))
    assert 4.0 < s < 4.6


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
