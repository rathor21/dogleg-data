"""Tests for ideals.py (task 004.4): ideal bands for the TrackMan-style tiles."""

import pytest

import data
import flight
import ideals
import launch
import presets

CASES = [(c, p) for p in presets.PLAYERS for c in presets.CLUBS]

# Metrics where the model's own ideal preset falls outside its band. Recorded,
# not fudged. Strict: an entry that starts passing, or a new miss, fails.
KNOWN_EXCEPTIONS = {
    ("driver", "lpga", "launch_deg"),  # model launch 12.60 against band 13.24 to 15.79
}


def _metrics(club, player):
    p = presets.preset(club, player)
    ln = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], p["club"], spin_trim=p["spin_trim"])
    f = flight.simulate(ln.ball_speed_mph, ln.launch_deg, ln.launch_dir_deg, ln.spin_rpm, ln.spin_axis_deg)
    return {
        "club_speed": p["club_speed"], "attack_deg": p["attack"], "club_path_deg": p["path"], "face_deg": p["face"],
        "face_to_path_deg": ln.face_to_path_deg, "dyn_loft_deg": p["dyn_loft"], "spin_loft_deg": ln.spin_loft_deg,
        "ball_speed_mph": ln.ball_speed_mph, "smash": ln.smash, "launch_deg": ln.launch_deg,
        "launch_dir_deg": ln.launch_dir_deg, "spin_rpm": ln.spin_rpm, "spin_axis_deg": ln.spin_axis_deg,
        "max_height_yd": f.max_height_yd, "land_angle_deg": f.land_angle_deg, "carry_yd": f.carry_yd,
        "side_yd": f.side_yd, "curve_yd": f.curve_yd,
    }


def _inside(band, v):
    return (band["lo"] is None or v >= band["lo"] - 1e-9) and (band["hi"] is None or v <= band["hi"] + 1e-9)


def test_every_metric_has_a_band():
    b = ideals.ideal_bands("7i", "pga")
    assert set(b) == set(ideals.METRICS)
    assert len(ideals.METRICS) == 18
    for m, band in b.items():
        assert {"lo", "hi", "target", "source", "modeled"} <= set(band), m
        assert band["source"], m
        if band["lo"] is not None and band["hi"] is not None:
            assert band["lo"] <= band["target"] <= band["hi"], m


def test_ideal_preset_sits_inside_its_own_bands():
    misses = set()
    for club, player in CASES:
        bands = ideals.ideal_bands(club, player)
        for metric, v in _metrics(club, player).items():
            if not _inside(bands[metric], v):
                misses.add((club, player, metric))
    assert misses == KNOWN_EXCEPTIONS


def test_non_driver_bands_follow_the_stated_widths():
    b = ideals.ideal_bands("7i", "pga")
    m = _metrics("7i", "pga")
    assert (b["club_path_deg"]["lo"], b["club_path_deg"]["hi"]) == (-2.0, 2.0)
    assert (b["face_deg"]["lo"], b["face_deg"]["hi"]) == (-1.0, 1.0)
    assert (b["face_to_path_deg"]["lo"], b["face_to_path_deg"]["hi"]) == (-1.5, 1.5)
    assert (b["launch_dir_deg"]["lo"], b["launch_dir_deg"]["hi"]) == (-2.0, 2.0)
    assert (b["spin_axis_deg"]["lo"], b["spin_axis_deg"]["hi"]) == (-2.0, 2.0)
    assert b["launch_deg"]["hi"] - b["launch_deg"]["lo"] == pytest.approx(3.0)
    assert b["launch_deg"]["target"] == pytest.approx(m["launch_deg"])
    assert b["spin_rpm"]["lo"] == pytest.approx(0.9 * m["spin_rpm"])
    assert b["spin_rpm"]["hi"] == pytest.approx(1.1 * m["spin_rpm"])
    assert b["max_height_yd"]["hi"] - b["max_height_yd"]["lo"] == pytest.approx(6.0)
    assert b["land_angle_deg"]["lo"] == pytest.approx(m["land_angle_deg"] - 3.0) and b["land_angle_deg"]["hi"] is None
    assert b["smash"]["lo"] == pytest.approx(m["smash"] - 0.03) and b["smash"]["hi"] is None
    assert b["attack_deg"]["hi"] - b["attack_deg"]["lo"] == pytest.approx(3.0)
    assert b["dyn_loft_deg"]["hi"] - b["dyn_loft_deg"]["lo"] == pytest.approx(4.0)
    assert b["spin_loft_deg"]["hi"] - b["spin_loft_deg"]["lo"] == pytest.approx(4.0)
    assert b["side_yd"]["hi"] == pytest.approx(0.05 * m["carry_yd"])
    assert b["curve_yd"]["hi"] == pytest.approx(0.04 * m["carry_yd"])
    assert b["carry_yd"]["hi"] == pytest.approx(1.03 * m["carry_yd"])
    assert b["ball_speed_mph"]["lo"] == pytest.approx(0.97 * m["ball_speed_mph"])


def test_sourced_and_modeled_flags():
    b = ideals.ideal_bands("7i", "pga")
    assert b["launch_dir_deg"]["modeled"] is False and "Anchor 5a" in b["launch_dir_deg"]["source"]
    assert b["spin_axis_deg"]["modeled"] is False and "Anchor 5b" in b["spin_axis_deg"]["source"]
    assert all(band["modeled"] for m, band in b.items() if m not in ("launch_dir_deg", "spin_axis_deg"))


def test_published_values_are_recorded_where_they_exist():
    b = ideals.ideal_bands("7i", "pga")
    assert b["launch_deg"]["published"] == data.PGA["7i"]["launch_deg"]
    assert b["carry_yd"]["published"] == 176 and b["spin_rpm"]["published"] == 7124
    assert "published" not in b["dyn_loft_deg"]  # only the driver and 6 iron are published
    assert ideals.ideal_bands("6i", "pga")["dyn_loft_deg"]["published"] == 20.2
    assert ideals.ideal_bands("driver", "lpga")["spin_loft_deg"]["published"] == 15.0
    assert ideals.ideal_bands("driver", "amateur")["spin_rpm"]["published"] == 3275
    assert "published" not in ideals.ideal_bands("7i", "amateur")["spin_rpm"]
    assert ideals.ideal_bands("3i", "lpga")["carry_yd"]["published"] == data.LPGA["4i"]["carry_yd"]  # 4 iron stands in


def test_club_speed_scales_ball_speed_and_carry_only():
    base = ideals.ideal_bands("7i", "pga")
    slow = ideals.ideal_bands("7i", "pga", club_speed=80.0)
    assert slow["ball_speed_mph"]["target"] == pytest.approx(base["ball_speed_mph"]["target"] * 80.0 / 92.0)
    assert slow["carry_yd"]["target"] < base["carry_yd"]["target"]
    assert slow["side_yd"]["hi"] == pytest.approx(0.05 * slow["carry_yd"]["target"])
    for m in ("launch_deg", "spin_rpm", "max_height_yd", "dyn_loft_deg", "smash", "club_speed"):
        assert slow[m] == base[m], m


def test_club_speed_outside_the_domain_raises():
    with pytest.raises(ValueError):
        ideals.ideal_bands("7i", "pga", club_speed=10.0)


def test_explicit_preset_speed_and_attack_match_the_defaults():
    p = presets.preset("driver", "pga")
    assert ideals.ideal_bands("driver", "pga", p["club_speed"], p["attack"]) == ideals.ideal_bands("driver", "pga")


# ---------------------------------------------------------------------------
# Driver optimizer lookups
# ---------------------------------------------------------------------------


def test_trackman_grid_points_read_back_exactly():
    for row in data.TRACKMAN_CARRY_2010:
        assert ideals.trackman_carry_2010(row[0], row[1]) == pytest.approx((row[3], row[4]))
    assert ideals.trackman_carry_2010(115, 0) == pytest.approx((9.8, 2919))


def test_ping_grid_points_read_back_exactly():
    for bs, cells in data.PING_2019.items():
        for aoa, cell in zip(data.PING_2019_AOA_DEG, cells):
            assert ideals.ping_2019(bs, aoa) == pytest.approx(cell)
    assert ideals.ping_2019(170, -2) == pytest.approx((9.6, 2750))


def test_optimizer_lookups_interpolate_and_clamp():
    lo, hi = ideals.trackman_carry_2010(112.5, 0)
    assert lo == pytest.approx(0.5 * (10.5 + 9.8)) and hi == pytest.approx(0.5 * (2970 + 2919))
    assert ideals.trackman_carry_2010(115, 2.5) == pytest.approx((0.5 * (9.8 + 13.0), 0.5 * (2919 + 2358)))
    assert ideals.trackman_carry_2010(200, 20) == ideals.trackman_carry_2010(120, 5)  # clamped to the table
    assert ideals.trackman_carry_2010(10, -20) == ideals.trackman_carry_2010(75, -5)
    assert ideals.ping_2019(400, 50) == ideals.ping_2019(180, 10)
    assert ideals.ping_2019(10, -50) == ideals.ping_2019(80, -10)


def test_driver_bands_span_both_sources_with_the_margin():
    for player in presets.PLAYERS:
        b = ideals.ideal_bands("driver", player)
        d = b["launch_deg"]["detail"]
        tm, pg = d["trackman_carry_2010"], d["ping_2019"]
        assert b["launch_deg"]["lo"] == pytest.approx(min(tm["launch_deg"], pg["launch_deg"]) - 1.0)
        assert b["launch_deg"]["hi"] == pytest.approx(max(tm["launch_deg"], pg["launch_deg"]) + 1.0)
        assert b["spin_rpm"]["lo"] == pytest.approx(min(tm["spin_rpm"], pg["spin_rpm"]) - 200.0)
        assert b["spin_rpm"]["hi"] == pytest.approx(max(tm["spin_rpm"], pg["spin_rpm"]) + 200.0)
        assert "TrackMan" in b["launch_deg"]["source"] and "PING" in b["launch_deg"]["source"]


def test_driver_bands_follow_speed_and_attack():
    base = ideals.ideal_bands("driver", "pga")
    higher = ideals.ideal_bands("driver", "pga", attack=3.0)
    assert higher["launch_deg"]["target"] > base["launch_deg"]["target"]  # more attack, more optimal launch
    assert higher["spin_rpm"]["target"] < base["spin_rpm"]["target"]
    assert higher["attack_deg"] == base["attack_deg"]  # the attack band stays on the preset
    slow = ideals.ideal_bands("driver", "pga", club_speed=90.0)
    assert slow["launch_deg"]["target"] > base["launch_deg"]["target"]  # slower swings want more launch


def test_driver_models_against_the_optimizer_bands():
    """Records the model's ideal driver against the optimizer bands: PGA and
    amateur sit inside both, the LPGA driver launches 0.6 deg under the band."""
    for player, in_launch in (("pga", True), ("lpga", False), ("amateur", True)):
        b = ideals.ideal_bands("driver", player)
        m = _metrics("driver", player)
        assert _inside(b["spin_rpm"], m["spin_rpm"]), player
        assert _inside(b["launch_deg"], m["launch_deg"]) is in_launch, player
