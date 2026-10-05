"""Tests for the swing arc (task 004-physics-2, ADR 0004 addendum 5): a change
of attack angle with the swing direction held moves the club path, by the
vertical swing plane of the club.

    path = swing direction - attack * tan(90 - plane)      (launch.swing_path)
    swing direction = path + attack * tan(90 - plane)      (launch.swing_direction)

The driver's plane is the Combine average golfer's 49 degrees (measured), the 6
iron's is Tuxen's 60 degree example, and the other clubs are MODELED between and
beyond them (data.SWING_PLANE_BY_CLUB).
"""

import math

import pytest

import data
import flight
import launch
import presets

LADDER = presets.CLUBS


def test_every_club_has_a_plane_and_the_two_anchors_hold():
    assert set(data.SWING_PLANE_BY_CLUB) == set(LADDER) == set(data.PGA)
    assert data.SWING_PLANE_BY_CLUB["driver"] == data.SWING_PLANE_DEG == 49.0
    assert data.SWING_PLANE_BY_CLUB["6i"] == 60.0
    lo, hi = data.DOMAIN["swing_plane_deg"]
    for plane in data.SWING_PLANE_BY_CLUB.values():
        assert lo < plane < hi


def test_the_plane_steepens_down_the_ladder():
    """Shorter clubs swing on a steeper plane: the table never flattens from the driver to the PW
    (the PW shares the 9 iron's lie, so it shares its plane)."""
    planes = [data.SWING_PLANE_BY_CLUB[c] for c in LADDER]
    assert all(b >= a for a, b in zip(planes, planes[1:]))
    assert planes[0] < planes[-1]
    assert 45.0 <= data.SWING_PLANE_BY_CLUB["driver"] <= 50.0  # TrackMan: a driver sits between 45 and 50
    assert 57.0 <= data.SWING_PLANE_BY_CLUB["9i"] <= 62.0  # Tuxen's 8 or 9 iron example sits at 57


def test_irons_follow_the_lie_ladder_from_the_six_iron():
    for club in ("3i", "4i", "5i", "6i", "7i", "8i", "9i", "pw"):
        assert data.SWING_PLANE_BY_CLUB[club] == pytest.approx(60.0 + data.LIE_DEG[club] - data.LIE_DEG["6i"])


def test_woods_and_hybrid_sit_on_the_line_from_driver_to_three_iron():
    d, t = data.SWING_PLANE_BY_CLUB["driver"], data.SWING_PLANE_BY_CLUB["3i"]
    assert data.SWING_PLANE_BY_CLUB["3w"] == pytest.approx(d + 0.25 * (t - d))
    assert data.SWING_PLANE_BY_CLUB["5w"] == pytest.approx(d + 0.50 * (t - d))
    assert data.SWING_PLANE_BY_CLUB["hybrid"] == pytest.approx(d + 0.75 * (t - d))


def test_swing_plane_for_reads_the_table_and_defaults_to_the_driver():
    assert launch.swing_plane_for() == data.SWING_PLANE_DEG
    assert launch.swing_plane_for(None) == data.SWING_PLANE_DEG
    for club in LADDER:
        assert launch.swing_plane_for(club) == data.SWING_PLANE_BY_CLUB[club]
    with pytest.raises(ValueError, match="club"):
        launch.swing_plane_for("2i")


def test_tuxen_worked_examples():
    """Anchor 12 Source 1 (Tuxen 2009): swing direction 0, attack -5 on a 45 degree plane gives a
    path near +5; attack +2 on 45 gives -2, and swing direction +2 brings it to 0; a 6 iron at
    attack -5 on a 60 degree plane gives about +2.5 (his rounded figure; the geometry gives 2.9),
    and swing direction -2.5 brings it near 0."""
    assert launch.swing_path(0.0, -5.0, 45.0) == pytest.approx(5.0)
    assert launch.swing_path(0.0, 2.0, 45.0) == pytest.approx(-2.0)
    assert launch.swing_path(2.0, 2.0, 45.0) == pytest.approx(0.0)
    assert launch.swing_path(0.0, -5.0, 60.0) == pytest.approx(2.89, abs=0.01)
    assert abs(launch.swing_path(-2.5, -5.0, 60.0)) < 0.4


def test_swing_direction_inverts_swing_path():
    for club in LADDER:
        plane = launch.swing_plane_for(club)
        for path in (-8.0, -2.0, 0.0, 3.5, 12.0):
            for attack in (-9.0, -4.0, 0.0, 2.5, 8.0):
                hsp = launch.swing_direction(path, attack, plane)
                assert launch.swing_path(hsp, attack, plane) == pytest.approx(path, abs=1e-12)
    assert launch.swing_direction(0.0, -4.0) == launch.swing_direction(0.0, -4.0, data.SWING_PLANE_DEG)
    assert launch.swing_direction(0.0, 0.0, 49.0) == 0.0 and math.copysign(1.0, launch.swing_direction(-0.0, -0.0)) == 1.0


def test_swing_direction_validates_like_swing_path():
    for bad in (20.0, 80.0, float("nan")):
        with pytest.raises(ValueError, match="plane_deg"):
            launch.swing_direction(0.0, -3.0, bad)
    with pytest.raises(ValueError, match="attack_deg"):
        launch.swing_direction(0.0, float("inf"), 49.0)


def test_steepening_moves_the_path_right_more_on_a_flat_plane():
    """Hitting down moves the path right for every club, and more for the driver (flat plane)
    than for a wedge (steep plane): tan(41) = 0.87 against tan(28.5) = 0.54 per degree."""
    per_degree = {club: -(launch.swing_path(0.0, -1.0, launch.swing_plane_for(club)) - launch.swing_path(0.0, 0.0, launch.swing_plane_for(club))) for club in LADDER}
    for club, v in per_degree.items():
        assert v < 0  # path rises (moves right) as attack falls
    gain = {club: launch.swing_path(0.0, -1.0, launch.swing_plane_for(club)) for club in LADDER}
    assert gain["driver"] == pytest.approx(math.tan(math.radians(41.0)), abs=1e-9)
    assert gain["pw"] == pytest.approx(math.tan(math.radians(28.5)), abs=1e-9)
    assert gain["driver"] > gain["3w"] > gain["hybrid"] > gain["6i"] > gain["pw"]


@pytest.mark.parametrize("player", presets.PLAYERS)
def test_steepening_the_driver_with_the_swing_direction_held_hooks_the_ball(player):
    """The lab's path-follows-attack switch: from the preset with path 0 and face 0, hit 4 degrees
    steeper holding the swing direction and the face. The path moves right (in-to-out), the face
    is now closed to it, the ball starts a little right and draws or hooks left, and the closed
    face takes loft off so launch and spin fall against the same attack with the path held."""
    p = presets.preset("driver", player)
    plane = launch.swing_plane_for("driver")
    hsp = launch.swing_direction(p["path"], p["attack"], plane)
    attack = p["attack"] - 4.0
    path = launch.swing_path(hsp, attack, plane)
    assert path == pytest.approx(p["path"] + 4.0 * math.tan(math.radians(90.0 - plane)))
    ln, f = presets.fly(p, attack=attack, path=path)
    held_ln, held_f = presets.fly(p, attack=attack)
    assert ln.launch_dir_deg > 0.0 and f.curve_yd < -15.0
    assert ln.face_to_path_deg == pytest.approx(-path)
    assert ln.dyn_loft_deg < held_ln.dyn_loft_deg and ln.spin_rpm < held_ln.spin_rpm and ln.launch_deg < held_ln.launch_deg


def test_a_wedge_moves_less_path_than_a_driver_for_the_same_steepening():
    hsp = 0.0
    drv = launch.swing_path(hsp, -4.0, launch.swing_plane_for("driver")) - launch.swing_path(hsp, 0.0, launch.swing_plane_for("driver"))
    pw = launch.swing_path(hsp, -4.0, launch.swing_plane_for("pw")) - launch.swing_path(hsp, 0.0, launch.swing_plane_for("pw"))
    assert drv == pytest.approx(3.48, abs=0.01) and pw == pytest.approx(2.17, abs=0.01)
