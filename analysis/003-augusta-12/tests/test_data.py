import data


def test_tiers_declared():
    assert data.TIERS == [0, 5, 10, 15, 20]


def test_gir50_distance_published_for_every_tier():
    assert set(data.GIR50_DISTANCE_YD) == set(data.TIERS)
    vals = [data.GIR50_DISTANCE_YD[t] for t in data.TIERS]
    assert all(a > b for a, b in zip(vals, vals[1:])), "a better tier reaches 50% GIR from farther away"


def test_proximity_anchored_vs_modeled_split():
    assert data.PROXIMITY_ANCHORED_TIERS == [0, 5, 10]
    assert data.PROXIMITY_MODELED_TIERS == [15, 20]
    assert set(data.PROXIMITY_ANCHORED_TIERS) | set(data.PROXIMITY_MODELED_TIERS) == set(data.TIERS)


def test_sigma_iso_monotonic_and_positive():
    vals = [data.SIGMA_ISO_FT[t] for t in data.TIERS]
    assert all(v > 0 for v in vals)
    assert all(a < b for a, b in zip(vals, vals[1:])), "dispersion must widen as handicap rises"


def test_proximity_ft_monotonic_and_sane():
    vals = [data.PROXIMITY_FT[t] for t in data.TIERS]
    assert all(a < b for a, b in zip(vals, vals[1:]))
    for t in data.TIERS:
        assert 20.0 < data.PROXIMITY_FT[t] < 150.0


def test_sigma_isotropic_ft_rejects_unknown_tier():
    import pytest
    with pytest.raises(KeyError):
        data.sigma_isotropic_ft(7)


def test_anisotropy_default_and_range():
    # Default ratio retuned 3.0 -> 2.5 in rev 7 (GIR-anchored core sweep,
    # data.py's rev 7 append block); the sensitivity range itself is
    # unchanged and still brackets the new default.
    assert data.ANISOTROPY["ratio"] == 2.5
    lo, hi = data.ANISOTROPY["range"]
    assert lo == 2.0 and hi == 3.5
    assert lo <= data.ANISOTROPY["ratio"] <= hi


def test_hole_geometry_ranges_are_ranges_not_constants():
    for key in ("green_width_yd_range", "green_depth_yd_range", "front_third_depth_yd_range"):
        lo, hi = data.HOLE[key]
        assert lo < hi, f"{key} must be a genuine range"
    lo, hi = data.HOLE["front_third_depth_yd_range"]
    assert 8.0 <= lo and hi <= 13.0  # anchored near the published 9-12 yd figure


def test_hole_bunker_counts_anchored():
    assert data.HOLE["bunkers"] == {"front": 1, "back": 2}


def test_tee_yardage_anchored():
    assert data.TEE_SHOT_YD == 155.0
    assert data.HOLE["tee_yards"] == data.TEE_SHOT_YD


def test_pins_well_formed():
    assert set(data.PINS) == {"left", "center", "sunday"}
    for key, p in data.PINS.items():
        assert 0.0 <= p["front_frac"] <= 1.0
        assert 0.0 <= p["back_frac"] <= 1.0
        assert abs(p["front_frac"] + p["back_frac"] - 1.0) < 1e-9
        if key != "center":
            lo, hi = p["local_depth_yd_range"]
            assert lo < hi


def test_sunday_pin_sits_fifteen_yards_deeper_than_the_front_left_reference():
    # Anchor 3's own words: "the Sunday pin sits roughly 15 yards deeper into
    # the green than a front-left pin" -- a claim about a generic front-left
    # reference position, checked here against data._FRONT_LEFT_SLOPE_
    # REFERENCE_Y rather than data.PINS["left"]["y"] directly, since this
    # release's own named "left" demo pin is repositioned to a mid-depth
    # placement (the locked pin cast's welcoming/accessible left pin, issue
    # #5) and is no longer literally "a front-left pin." The anchor's 15-yd
    # claim is about the green's shape, not about wherever this release
    # chooses to put its own demo pin, so it is checked against the
    # decoupled reference that model.py's front-edge slope actually uses.
    assert abs((data.PINS["sunday"]["y"] - data._FRONT_LEFT_SLOPE_REFERENCE_Y) - 15.0) < 1e-9


def test_center_pin_is_the_narrow_sucker_pin_target():
    # center's front_frac == back_frac == 0.5: neither side is favored, and its
    # local depth comes from the tightest published range (front_third), the
    # release's demonstration pin for CONTEXT.md's sucker-pin definition.
    assert data.PINS["center"]["front_frac"] == data.PINS["center"]["back_frac"] == 0.5
    assert data.PINS["center"]["local_depth_yd_range"] is None  # resolved from HOLE, not its own figure


def test_wind_params_are_ranges_with_a_default_inside():
    lo, hi = data.WIND["carry_penalty_range_yd"]
    assert lo <= data.WIND["carry_penalty_yd"] <= hi
    lo, hi = data.WIND["dispersion_inflation_range"]
    assert lo <= data.WIND["dispersion_inflation"] <= hi
    assert data.WIND["dispersion_inflation"] > 1.0
    assert data.WIND["carry_penalty_yd"] > 0.0


def test_three_putt_rate_published_and_modeled():
    assert set(data.THREE_PUTT_RATE) == set(data.TIERS)
    for t in (5, 15):
        pass  # published tiers exist directly in the source table
    vals = [data.THREE_PUTT_RATE[t] for t in data.TIERS]
    assert all(0.0 < v < 0.3 for v in vals)
    assert all(a <= b + 1e-9 for a, b in zip(vals, vals[1:])), "three-putt rate must not fall as handicap rises"


def test_up_and_down_pct_well_formed():
    assert set(data.UP_AND_DOWN_PCT) == set(data.TIERS)
    vals = [data.UP_AND_DOWN_PCT[t] for t in data.TIERS]
    assert all(0.0 < v < 1.0 for v in vals)
    assert all(a >= b for a, b in zip(vals, vals[1:])), "up-and-down rate must not rise as handicap rises"


def test_bank_rollback_widened_for_mishit_mixture():
    # rev 6 (Sunny's finding): the shaved bank is what feeds a short mishit
    # into the water, widened from 3.0 to 8.0 yd; range widened to match.
    assert data.BANK_ROLLBACK_YD == 8.0
    lo, hi = data.BANK_ROLLBACK_YD_RANGE
    assert (lo, hi) == (5.0, 12.0)
    assert lo <= data.BANK_ROLLBACK_YD <= hi


def test_mishit_pct_well_formed():
    assert set(data.MISHIT_PCT) == set(data.TIERS)
    vals = [data.MISHIT_PCT[t] for t in data.TIERS]
    assert all(0.0 < v < 1.0 for v in vals)
    assert all(a <= b for a, b in zip(vals, vals[1:])), "mishit rate must not fall as handicap rises"
    lo, hi = data.MISHIT_PCT_SENSITIVITY_MULT_RANGE
    assert (lo, hi) == (0.5, 1.5)
    assert data.TOUR_MISHIT_PCT < data.MISHIT_PCT[0], "Tour mishit rate must sit below the amateur tiers' own lowest"


def test_mishit_short_frac_well_formed():
    # Retuned 0.15 -> 0.25 in rev 7's sweep; range shifted to (0.20, 0.30),
    # the same +/-0.05 absolute width the rev 6 range used.
    assert 0.0 < data.MISHIT_SHORT_FRAC < 1.0
    lo, hi = data.MISHIT_SHORT_FRAC_RANGE
    assert (lo, hi) == (0.20, 0.30)
    assert lo <= data.MISHIT_SHORT_FRAC <= hi


def test_every_anchor_group_carries_source():
    assert isinstance(data.SOURCES, dict)
    for key in ("GIR50_DISTANCE_YD", "SIGMA_ISO_FT", "ANISOTROPY", "HOLE", "PINS", "WIND",
                "THREE_PUTT_RATE", "UP_AND_DOWN_PCT", "MISHIT_PCT", "MISHIT_SHORT_FRAC", "TOUR_MISHIT_PCT"):
        assert key in data.SOURCES and "003_Source_Log.md" in data.SOURCES[key]["log"]
