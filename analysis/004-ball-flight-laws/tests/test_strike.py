"""Tests for the strike location (task 004-physics-2, ADR 0004 addendum 5):
gear effect, bulge and roll, and smash loss for a strike off the face center.

    strike_toe_mm > 0 toward the toe, strike_up_mm > 0 above center.

Sources (docs/sources/004_Physics_Research.md Topic 7, source log Anchor 13):
Tuxen's four gear-effect rows (driver heel strikes fade, 6 iron toe strikes
draw), TrackMan's bulge and roll numbers (10 mm toe, 2 deg more open; 10 mm
low, 2 deg less loft), Tutelman's vertical-to-horizontal ratio, and the smash
losses Tuxen and TrackMan quote.
"""

import math

import pytest

import data
import flight
import launch
import presets

MM_PER_IN = 25.4


def _ball(club):
    return data.SUPERSEDED_2019[("PGA", club)]


def test_domains_and_checks():
    assert data.DOMAIN["strike_toe_mm"] == (-20.0, 20.0) and data.DOMAIN["strike_up_mm"] == (-15.0, 15.0)
    for name, bad in (("strike_toe_mm", 20.5), ("strike_toe_mm", float("nan")), ("strike_up_mm", -15.5), ("strike_up_mm", float("inf"))):
        with pytest.raises(ValueError, match=name):
            launch.deliver(115.0, -0.9, 0.0, 0.0, 12.75, "driver", **{name: bad})
    launch.deliver(115.0, -0.9, 0.0, 0.0, 12.75, "driver", strike_toe_mm=20.0, strike_up_mm=-15.0)


def test_center_strike_changes_nothing():
    a = launch.deliver(115.0, -0.9, 3.0, -2.0, 12.75, "driver", spin_trim=0.74)
    b = launch.deliver(115.0, -0.9, 3.0, -2.0, 12.75, "driver", spin_trim=0.74, strike_toe_mm=0.0, strike_up_mm=0.0)
    assert a == b and a.gear_side_rpm == 0.0 and a.gear_back_rpm == 0.0


def test_gear_coefficient_is_the_mean_of_tuxens_four_rows():
    """Each row's spin axis, read as sidespin over the 2019 row's backspin, gives the same coefficient
    within 3 percent (0.461 to 0.482 rpm per mm per mph), and the constant is their mean."""
    coefs = []
    for club, toe_mm, axis in data.GEAR_EXAMPLES:
        row = _ball(club)
        side = math.tan(math.radians(axis)) * row["spin_rpm"]
        coefs.append(side / (row["ball_speed_mph"] * -toe_mm))
    assert min(coefs) > 0.46 and max(coefs) < 0.483
    assert data.GEAR_H_RPM_PER_MM_MPH == pytest.approx(sum(coefs) / len(coefs), abs=0.001)
    assert len(data.GEAR_EXAMPLES) == 4 and {c for c, _t, _a in data.GEAR_EXAMPLES} == {"driver", "6i"}


def test_gear_effect_reproduces_tuxens_rows_with_bulge_off():
    """The gear effect alone (no bulge: pass the 6 iron's flat face, or compute from the helper)
    returns Tuxen's axis for each row within a degree."""
    for club, toe_mm, axis in data.GEAR_EXAMPLES:
        row = _ball(club)
        spin, tilt, side, back = launch.gear_effect(row["spin_rpm"], 0.0, row["ball_speed_mph"], club, toe_mm, 0.0)
        assert tilt == pytest.approx(axis, abs=0.7)
        assert back == 0.0  # no vertical strike
        assert math.copysign(1.0, side) == math.copysign(1.0, axis)
        assert spin > row["spin_rpm"]  # the sidespin adds to the total


def test_toe_strike_draws_and_heel_strike_fades_on_every_club():
    for player in presets.PLAYERS:
        for club in presets.CLUBS:
            p = presets.preset(club, player)
            toe = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], p["club"], spin_trim=p["spin_trim"], strike_toe_mm=8.0)
            heel = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], p["club"], spin_trim=p["spin_trim"], strike_toe_mm=-8.0)
            assert toe.gear_side_rpm < 0.0 < heel.gear_side_rpm
            assert toe.spin_axis_deg < 0.0 < heel.spin_axis_deg
            assert heel.gear_side_rpm == pytest.approx(-toe.gear_side_rpm)
            # the sidespin adds to the D-plane spin as a vector. On a flat face (no bulge) the D-plane
            # has no tilt here, so the whole sidespin is the gear effect.
            if p["club"] not in data.BULGE_ROLL_CLUBS:
                assert toe.spin_rpm * math.sin(math.radians(toe.spin_axis_deg)) == pytest.approx(toe.gear_side_rpm, rel=1e-9)


def test_gear_sidespin_is_about_the_same_in_rpm_across_the_set():
    """Tuxen: 500 rpm of sidespin tilts a driver's axis 11 degrees at 2500 rpm and a wedge's 2.8
    at 10,000. The model's sidespin per mm scales with ball speed only, so the tilt per mm falls
    from the driver to the wedge."""
    tilts = {}
    for club in ("driver", "7i", "pw"):
        p = presets.preset(club, "pga")
        ln = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], club, spin_trim=p["spin_trim"], strike_toe_mm=10.0)
        tilts[club] = ln.spin_axis_deg
    assert tilts["driver"] < tilts["7i"] < tilts["pw"] < 0.0  # all draws, the driver tilts most


def test_bulge_opens_the_face_toward_the_toe_on_woods_only():
    for club in data.BULGE_ROLL_CLUBS:
        p = presets.preset(club, "pga")
        ln = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], club, strike_toe_mm=10.0)
        assert ln.face_deg == pytest.approx(2.0) and ln.face_input_deg == 0.0
        assert ln.face_to_path_deg == pytest.approx(2.0)
        assert ln.launch_dir_deg > 1.0  # the open impact-point face starts the ball right
    for club in ("hybrid", "3i", "7i", "pw"):
        p = presets.preset(club, "pga")
        ln = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], club, strike_toe_mm=10.0)
        assert ln.face_deg == 0.0 and ln.launch_dir_deg == 0.0


def test_a_heel_strike_on_a_driver_starts_left_and_fades():
    """Tuxen: bulge closes the face on a heel strike, starts the ball left and tilts the D-plane
    toward a draw, which offsets part of the gear-effect fade. The net is still a fade."""
    p = presets.preset("driver", "pga")
    ln, f = presets.fly(p, strike_toe=-0.5 * MM_PER_IN)
    assert ln.face_deg == pytest.approx(-2.54)
    assert ln.launch_dir_deg < -1.5
    assert ln.gear_side_rpm > 800.0
    assert 3.0 < ln.spin_axis_deg < 15.0  # Tuxen's 20 is the gear effect alone
    assert f.curve_yd > 5.0


def test_roll_adds_loft_above_center_and_the_vertical_gear_takes_spin_off():
    p = presets.preset("driver", "pga")
    center = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], "driver", spin_trim=p["spin_trim"])
    high = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], "driver", spin_trim=p["spin_trim"], strike_up_mm=10.0)
    low = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], "driver", spin_trim=p["spin_trim"], strike_up_mm=-10.0)
    assert high.dyn_loft_deg == pytest.approx(p["dyn_loft"] + 2.0) and low.dyn_loft_deg == pytest.approx(p["dyn_loft"] - 2.0)
    assert high.launch_deg > center.launch_deg > low.launch_deg
    assert high.gear_back_rpm < 0.0 < low.gear_back_rpm
    assert high.spin_rpm < center.spin_rpm < low.spin_rpm
    assert high.spin_axis_deg == 0.0 == low.spin_axis_deg
    # the vertical gear effect is 1.5 to 2 times the horizontal one for the same offset (Tutelman)
    toe = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], "driver", spin_trim=p["spin_trim"], strike_toe_mm=10.0)
    assert abs(low.gear_back_rpm) / abs(toe.gear_side_rpm) == pytest.approx(data.GEAR_V_RATIO, rel=0.03)
    assert 1.5 <= data.GEAR_V_RATIO <= 2.0


def test_irons_have_no_vertical_gear_effect_or_roll():
    p = presets.preset("7i", "pga")
    high = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], "7i", strike_up_mm=10.0)
    center = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], "7i")
    assert high.gear_back_rpm == 0.0 and high.dyn_loft_deg == center.dyn_loft_deg and high.launch_deg == center.launch_deg
    assert high.ball_speed_mph < center.ball_speed_mph  # smash loss still applies
    assert high.spin_rpm < center.spin_rpm  # through the lower ball speed only


def test_backspin_never_falls_below_the_floor():
    p = presets.preset("driver", "pga")
    worst = launch.deliver(140.0, 10.0, 0.0, 0.0, 12.0, "driver", spin_trim=0.5, strike_up_mm=15.0)
    ref = launch.deliver(140.0, 10.0, 0.0, 0.0, 12.0, "driver", spin_trim=0.5)
    # the roll adds 3 degrees of loft, so compare with the same loft and no strike
    same_loft = launch.deliver(140.0, 10.0, 0.0, 0.0, 15.0, "driver", spin_trim=0.5)
    assert worst.spin_rpm >= data.GEAR_BACKSPIN_FLOOR_FRAC * same_loft.spin_rpm * worst.ball_speed_mph / same_loft.ball_speed_mph * 0.99
    assert worst.spin_rpm > 0.0 and ref.spin_rpm > worst.spin_rpm


def test_smash_loss_grows_with_distance_from_center():
    assert launch.smash_strike_factor(0.0, 0.0) == 1.0
    assert launch.smash_strike_factor(10.0, 0.0) == pytest.approx(0.98)  # Tuxen's half-thin hit, 1.48 to 1.45
    assert launch.smash_strike_factor(0.0, 10.0) == pytest.approx(0.98)
    assert launch.smash_strike_factor(12.7, 0.0) == pytest.approx(1.0 - 0.0002 * 12.7 ** 2)
    assert launch.smash_strike_factor(20.0, 15.0) == pytest.approx(0.875)  # the domain corner
    p = presets.preset("driver", "pga")
    center = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], "driver")
    off = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], "driver", strike_toe_mm=-6.0, strike_up_mm=-8.0)
    # the roll moved the loft, so compare with the smash law at the struck shot's own spin loft
    assert off.smash == pytest.approx(launch.smash_of(off.spin_loft_deg) * launch.smash_strike_factor(-6.0, -8.0))
    assert off.smash < center.smash
    assert off.ball_speed_mph < center.ball_speed_mph


def test_trackman_off_center_example_direction():
    """TrackMan's 10 Fundamentals: 92 mph off center gave 129 mph (1.40) and 196 yd, 88 mph at
    center gave 132 mph (1.50) and 204 yd. The offset is unstated; at 15 mm low on the heel the
    model gives a comparable smash gap and a shorter carry."""
    p = presets.preset("driver", "amateur")
    off_ln, off_f = presets.fly(p, club_speed=92.0, strike_toe=-11.0, strike_up=-11.0)
    on_ln, on_f = presets.fly(p, club_speed=88.0)
    assert off_ln.smash < on_ln.smash - 0.05
    assert off_f.carry_yd < on_f.carry_yd


def test_high_toe_strike_robot_direction():
    """golf.com robot (95 mph, attack 0): a high toe strike launched about 2.5 degrees higher with
    under 300 rpm less spin and carried 5.5 yd shorter; a low heel strike launched 2.5 lower with
    600 rpm more and carried 19 yd shorter. Directions, not sizes, are the check."""
    p = presets.preset("driver", "amateur")
    base = dict(club_speed=95.0, attack=0.0, dyn_loft=15.1)
    c_ln, c_f = presets.fly(p, **base)
    ht_ln, ht_f = presets.fly(p, strike_toe=8.0, strike_up=6.0, **base)
    lh_ln, lh_f = presets.fly(p, strike_toe=-8.0, strike_up=-8.0, **base)
    assert ht_ln.launch_deg > c_ln.launch_deg > lh_ln.launch_deg
    assert ht_ln.spin_rpm < c_ln.spin_rpm < lh_ln.spin_rpm
    assert lh_f.carry_yd < c_f.carry_yd
    assert ht_ln.spin_axis_deg < 0.0 < lh_ln.spin_axis_deg  # toe draws, heel fades


def test_presets_fly_takes_strike_overrides_and_the_golden_cases_fly():
    p = presets.preset("3w", "lpga")
    ln, f = presets.fly(p, strike_toe=-20.0, strike_up=15.0)
    assert f.carry_yd > 0.0 and ln.gear_back_rpm < 0.0 < ln.gear_side_rpm
    corner = launch.deliver(40.0, -10.0, -15.0, -15.0, 0.0, "3w", lie_deg=-10.0, strike_toe_mm=-20.0, strike_up_mm=-15.0)
    assert math.isfinite(corner.spin_rpm) and corner.spin_rpm > 0.0
    f2 = flight.simulate(corner.ball_speed_mph, corner.launch_deg, corner.launch_dir_deg, corner.spin_rpm, corner.spin_axis_deg)
    assert f2.carry_yd >= 0.0
