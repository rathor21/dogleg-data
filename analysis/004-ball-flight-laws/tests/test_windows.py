"""Tests for windows.py (task 004.4): the nine windows solve and classify."""

import pytest

import classify
import data
import launch
import presets
import windows

TOL = data.WINDOWS


@pytest.fixture(scope="module")
def all_windows():
    return {p: {(w["height"], w["shape"]): w for w in windows.nine_windows(p)} for p in presets.PLAYERS}


CASES = [(p, h, s) for p in presets.PLAYERS for h in windows.HEIGHTS for s in windows.SHAPES]


@pytest.mark.parametrize("player,height,shape", CASES)
def test_window_hits_its_targets(all_windows, player, height, shape):
    w = all_windows[player][(height, shape)]
    f = w["flight"]
    tol = TOL["solver_tol_yd"]  # the solver's own tolerance, far tighter than the teaching tolerances
    assert abs(f["max_height_yd"] - w["target"]["max_height_yd"]) <= tol
    assert abs(f["curve_yd"] - TOL["curve_frac"][shape] * f["carry_yd"]) <= tol
    assert abs(f["side_yd"]) <= tol <= TOL["side_tol_yd"]


def test_targets_come_from_the_preset(all_windows):
    for player in presets.PLAYERS:
        _, _, base = windows.preset_flight("7i", player)
        for (height, shape), w in all_windows[player].items():
            assert w["target"]["max_height_yd"] == pytest.approx(TOL["heights"][height] * base.max_height_yd)
        assert all_windows[player][("mid", "straight")]["flight"]["max_height_yd"] == pytest.approx(base.max_height_yd, abs=0.05)


@pytest.mark.parametrize("player,height,shape", CASES)
def test_window_shape_classifies(all_windows, player, height, shape):
    c = all_windows[player][(height, shape)]["classification"]
    assert c["name"] == shape.capitalize()  # Draw, Straight or Fade
    assert c["shape"] == shape


def test_windows_report_total_distance(all_windows):
    for player in presets.PLAYERS:
        for w in all_windows[player].values():
            assert w["flight"]["total_yd"] > w["flight"]["carry_yd"]


def test_windows_are_labeled_modeled(all_windows):
    assert all(w["modeled"] for p in all_windows.values() for w in p.values())


@pytest.mark.parametrize("player,height,shape", CASES)
def test_window_delivery_is_inside_the_domain_and_reproduces(all_windows, player, height, shape):
    w = all_windows[player][(height, shape)]
    d = w["delivery"]
    p = presets.preset("7i", player)
    assert d["club_speed_mph"] == p["club_speed"]  # club speed fixed at the preset
    assert w["spin_trim"] == p["spin_trim"]
    # The height lever moves loft and attack together.
    h = w["height_lever_deg"]
    assert d["dyn_loft_deg"] == pytest.approx(p["dyn_loft"] + h)
    assert d["attack_deg"] == pytest.approx(p["attack"] + TOL["attack_per_loft"] * h)
    ln = launch.deliver(d["club_speed_mph"], d["attack_deg"], d["path_deg"], d["face_deg"], d["dyn_loft_deg"], "7i",
                        spin_trim=w["spin_trim"])  # raises outside the domain
    assert ln.launch_deg == pytest.approx(w["launch"]["launch_deg"])
    assert ln.spin_rpm == pytest.approx(w["launch"]["spin_rpm"])


def test_low_is_lower_and_steeper_high_is_higher(all_windows):
    for player in presets.PLAYERS:
        w = all_windows[player]
        low, mid, high = (w[(h, "straight")] for h in windows.HEIGHTS)
        assert low["delivery"]["dyn_loft_deg"] < mid["delivery"]["dyn_loft_deg"] < high["delivery"]["dyn_loft_deg"]
        assert low["delivery"]["attack_deg"] < mid["delivery"]["attack_deg"] < high["delivery"]["attack_deg"]
        assert low["flight"]["max_height_yd"] < mid["flight"]["max_height_yd"] < high["flight"]["max_height_yd"]
        assert low["flight"]["carry_yd"] > mid["flight"]["carry_yd"] > high["flight"]["carry_yd"]


def test_draws_and_fades_are_not_mirrors_but_flip_path_and_face(all_windows):
    """Same height, opposite curve: path and face flip sign and stay close, the draw's closed
    face delofts the club and the fade's open face adds loft (effective loft), and the draw
    carries and totals more."""
    for player in presets.PLAYERS:
        for height in windows.HEIGHTS:
            d, f = all_windows[player][(height, "draw")], all_windows[player][(height, "fade")]
            assert d["delivery"]["path_deg"] > 0.0 > f["delivery"]["path_deg"]
            assert d["delivery"]["face_deg"] > 0.0 > f["delivery"]["face_deg"]
            assert d["delivery"]["path_deg"] == pytest.approx(-f["delivery"]["path_deg"], abs=1.5)
            assert d["launch"]["dyn_loft_deg"] < f["launch"]["dyn_loft_deg"]  # at the same height the fade flies the higher loft
            assert d["launch"]["dyn_loft_deg"] < d["launch"]["dyn_loft_input_deg"]  # closed face delofts
            assert f["launch"]["dyn_loft_deg"] > f["launch"]["dyn_loft_input_deg"]  # open face adds loft
            assert d["flight"]["carry_yd"] > f["flight"]["carry_yd"]
            assert d["flight"]["total_yd"] > f["flight"]["total_yd"]


def test_on_target_draw_starts_right_and_reads_draw(all_windows):
    """Finishing on the line with a 5 percent draw needs a start about 2.9 deg
    right, past TrackMan's +-2 deg start line. The ball was worked back to the
    target, so it reads Draw, and a fade reads Fade."""
    for player in presets.PLAYERS:
        for height in windows.HEIGHTS:
            d = all_windows[player][(height, "draw")]
            f = all_windows[player][(height, "fade")]
            assert d["launch"]["launch_dir_deg"] > classify.START_STRAIGHT_DEG
            assert d["classification"]["start"] == "push" and d["classification"]["name"] == "Draw"
            assert d["classification"]["worked_back"] is True
            assert f["launch"]["launch_dir_deg"] < -classify.START_STRAIGHT_DEG
            assert f["classification"]["start"] == "pull" and f["classification"]["name"] == "Fade"
            assert f["classification"]["worked_back"] is True
            s = all_windows[player][(height, "straight")]["classification"]
            assert s["name"] == "Straight" and s["worked_back"] is False
