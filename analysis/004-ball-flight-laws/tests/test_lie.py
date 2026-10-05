"""Tests for the lie at impact (task 004-physics-2, ADR 0004 addendum 5).

A lie change is a rotation of the head about the target line. Toe up (a flat
lie, lie_deg > 0) opens the face by about tan(loft) per degree, toe down (an
upright lie, heel dug in) closes it, and the loft barely moves. The effect grows
with loft: a wedge is the most sensitive club and a driver the least
(docs/sources/004_Physics_Research.md, Topic 6).
"""

import math

import pytest

import data
import launch
import presets

CASES = [(club, player) for player in presets.PLAYERS for club in presets.CLUBS]


def test_lie_is_in_the_domain_and_checked():
    assert data.DOMAIN["lie_deg"] == (-10.0, 10.0)
    for bad in (-10.5, 10.5, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="lie_deg"):
            launch.deliver(92.0, -3.0, 0.0, 0.0, 23.0, "7i", lie_deg=bad)
    launch.deliver(92.0, -3.0, 0.0, 0.0, 23.0, "7i", lie_deg=-10.0)
    launch.deliver(92.0, -3.0, 0.0, 0.0, 23.0, "7i", lie_deg=10.0)


def test_lie_zero_changes_nothing_and_keeps_the_fields_exact():
    a = launch.deliver(92.0, -3.9, 2.0, -1.0, 23.354, "7i")
    b = launch.deliver(92.0, -3.9, 2.0, -1.0, 23.354, "7i", lie_deg=0.0)
    assert a == b
    assert a.face_input_deg == a.face_deg == -1.0
    assert a.face_to_path_deg == -3.0


def test_tilt_geometry_matches_the_derivation():
    """Face change per degree of lie is atan(tan(loft) * sin(1 deg)): 0.19 for 10.5 deg of loft,
    0.67 at 34, 1.04 at 46 and 1.60 at 58 (research file, Topic 6)."""
    for loft, per_deg in ((10.5, 0.19), (20.0, 0.36), (34.0, 0.67), (46.0, 1.04), (58.0, 1.60)):
        n = launch.tilt_about_target_line(launch.face_normal(0.0, loft), 1.0)
        face, loft_after = launch.normal_angles(n)
        assert face == pytest.approx(per_deg, abs=0.006)
        assert face == pytest.approx(math.degrees(math.atan(math.tan(math.radians(loft)) * math.sin(math.radians(1.0)))), abs=1e-9)
        assert abs(loft_after - loft) < 0.03


def test_toe_up_opens_the_face_and_toe_down_closes_it_by_tan_loft():
    for club in presets.CLUBS:
        p = presets.preset(club, "pga")
        up = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], club, lie_deg=3.0)
        down = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], club, lie_deg=-3.0)
        expect = math.degrees(math.atan(math.tan(math.radians(p["dyn_loft"])) * math.sin(math.radians(3.0))))
        assert up.face_deg == pytest.approx(expect, abs=1e-9) and down.face_deg == pytest.approx(-expect, abs=1e-9)
        assert up.face_input_deg == down.face_input_deg == 0.0
        assert up.face_to_path_deg == pytest.approx(up.face_deg) and down.face_to_path_deg == pytest.approx(down.face_deg)
        # toe up: starts right and fades; toe down: starts left and draws
        assert up.launch_dir_deg > 0.0 and up.spin_axis_deg > 0.0
        assert down.launch_dir_deg < 0.0 and down.spin_axis_deg < 0.0
        assert abs(up.dyn_loft_deg - p["dyn_loft"]) < 0.1 and abs(down.dyn_loft_deg - p["dyn_loft"]) < 0.1


def test_a_wedge_is_more_sensitive_to_lie_than_a_driver():
    moved = {}
    for club in presets.CLUBS:
        p = presets.preset(club, "pga")
        ln = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], club, lie_deg=2.0)
        moved[club] = ln.face_deg
    assert moved["driver"] < moved["hybrid"] < moved["6i"] < moved["pw"]
    assert moved["driver"] == pytest.approx(0.45, abs=0.05)  # 12.7 deg of loft, 2 degrees of lie
    assert moved["pw"] == pytest.approx(1.34, abs=0.05)  # 33.8 deg of loft


def test_retailer_claim_two_degrees_of_lie_moves_a_seven_iron_shot_a_few_yards():
    """Golf Club Brokers (research file, Topic 6): 2 degrees of lie moves a shot 8 to 10 yd at
    typical iron distances. The geometry alone gives about 5 yd for a Tour 7 iron (the file's
    own estimate), so the model lands in the lower half of the claim and on its side."""
    p = presets.preset("7i", "pga")
    _ln, f = presets.fly(p, lie=-2.0)
    assert -8.0 < f.side_yd < -3.5
    _ln2, f2 = presets.fly(p, lie=2.0)
    assert f2.side_yd == pytest.approx(-f.side_yd, abs=0.3)  # a square face mirrors


@pytest.mark.parametrize("club,player", CASES)
def test_lie_mirrors_through_the_face_for_every_preset(club, player):
    """Toe up by t with the face closed by its own opening is a square face again, and a left
    and right mirror of the delivery mirrors the lie's effect."""
    p = presets.preset(club, player)
    up = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], club, lie_deg=4.0)
    mirror = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], club, lie_deg=-4.0)
    assert mirror.face_deg == pytest.approx(-up.face_deg, abs=1e-9)
    assert mirror.launch_dir_deg == pytest.approx(-up.launch_dir_deg, abs=1e-9)
    assert mirror.spin_axis_deg == pytest.approx(-up.spin_axis_deg, abs=1e-9)
    assert mirror.spin_rpm == pytest.approx(up.spin_rpm, rel=1e-9) and mirror.launch_deg == pytest.approx(up.launch_deg, abs=1e-9)


def test_lie_comes_after_the_face_to_loft_coupling():
    """The coupling reads the input face (the rotation about the shaft); the lie tilt is a different
    rotation and does not feed back into it."""
    ln = launch.deliver(92.0, -3.9, 0.0, -4.0, 23.354, "7i", lie_deg=5.0)
    assert ln.dyn_loft_deg == pytest.approx(23.354 - data.KAPPA["7i"] * 4.0, abs=0.4)  # the tilt moves loft a little
    assert ln.face_deg > -4.0  # toe up opened the closed face part way back
    assert ln.face_to_path_deg == pytest.approx(ln.face_deg)


def test_presets_fly_takes_a_lie_override():
    p = presets.preset("7i", "pga")
    ln, _f = presets.fly(p, lie=3.0)
    assert ln.face_deg > 0.5
    with pytest.raises(ValueError, match="unknown override"):
        presets.fly(p, lie_deg=3.0)
