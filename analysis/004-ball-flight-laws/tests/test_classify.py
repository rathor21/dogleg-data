"""Tests for classify.py (task 004.4): start, shape, name and finish text."""

import itertools

import pytest

import classify
import data
import flight
import launch
import presets

CARRY = 200.0

START_DIR = {"pull": -3.0, "straight": 0.0, "push": 3.0}
# (spin axis, curve yd) for each shape word, on a 200 yd carry. Hook and slice
# curve 16 percent, draw and fade 5 percent (the CURVE_HOOK_FRAC line is 8).
SHAPE_INPUT = {
    "straight": (0.0, 0.0),
    "draw": (-5.0, -10.0),
    "fade": (5.0, 10.0),
    "hook": (-10.0, -32.0),
    "slice": (10.0, 32.0),
}


def _name(start, shape):
    if start == "straight":
        return shape.capitalize()
    if shape == "straight":
        return start.capitalize()
    return f"{start.capitalize()} {shape}"


def test_thresholds_come_from_data():
    assert classify.START_STRAIGHT_DEG == data.CLASSIFY["start_straight_deg"] == 2.0  # TrackMan, Anchor 5(a)
    assert classify.AXIS_STRAIGHT_DEG == data.CLASSIFY["axis_straight_deg"] == 2.0  # TrackMan, Anchor 5(b)
    assert classify.CURVE_HOOK_FRAC == data.CLASSIFY["curve_hook_frac"] == 0.08  # MODELED


@pytest.mark.parametrize("start,shape", list(itertools.product(START_DIR, SHAPE_INPUT)))
def test_every_name_is_reachable(start, shape):
    axis, curve = SHAPE_INPUT[shape]
    out = classify.classify(START_DIR[start], axis, curve, 0.0, CARRY)
    assert out["start"] == start
    assert out["shape"] == shape
    assert out["name"] == _name(start, shape)


def test_fifteen_distinct_names():
    names = {
        classify.classify(START_DIR[s], SHAPE_INPUT[h][0], SHAPE_INPUT[h][1], 0.0, CARRY)["name"]
        for s, h in itertools.product(START_DIR, SHAPE_INPUT)
    }
    assert len(names) == 15
    assert {"Straight", "Pull", "Push", "Draw", "Fade", "Hook", "Slice", "Pull hook", "Push draw", "Pull fade",
            "Push slice", "Pull draw", "Push fade", "Pull slice", "Push hook"} == names


@pytest.mark.parametrize("launch_dir,start", [
    (-2.0001, "pull"), (-2.0, "straight"), (-1.9999, "straight"), (0.0, "straight"),
    (1.9999, "straight"), (2.0, "straight"), (2.0001, "push"),
])
def test_start_boundary_is_inclusive_on_the_straight_side(launch_dir, start):
    assert classify.classify(launch_dir, 0.0, 0.0, 0.0, CARRY)["start"] == start


@pytest.mark.parametrize("axis,shape", [
    (-2.0001, "draw"), (-2.0, "straight"), (0.0, "straight"), (2.0, "straight"), (2.0001, "fade"),
])
def test_spin_axis_boundary(axis, shape):
    curve = -10.0 if axis < 0 else 10.0
    assert classify.classify(0.0, axis, curve, 0.0, CARRY)["shape"] == shape


def test_a_straight_axis_ignores_curve():
    """The spin axis decides straight. Curve only splits draw from hook."""
    assert classify.classify(0.0, 1.9, 40.0, 0.0, CARRY)["shape"] == "straight"


@pytest.mark.parametrize("curve,shape", [
    (-16.0, "draw"), (-16.01, "hook"), (16.0, "fade"), (16.01, "slice"), (-0.1, "draw"), (0.1, "fade"),
])
def test_hook_fraction_boundary(curve, shape):
    """0.08 of a 200 yd carry is 16 yd, inclusive on the draw and fade side."""
    assert classify.classify(0.0, 5.0 if curve > 0 else -5.0, curve, 0.0, CARRY)["shape"] == shape


def test_hook_fraction_scales_with_carry():
    """The same 10 yd of curve is a fade on a long carry and a slice on a short one."""
    assert classify.classify(0.0, 5.0, 10.0, 0.0, 200.0)["shape"] == "fade"  # 5 percent
    assert classify.classify(0.0, 5.0, 10.0, 0.0, 130.0)["shape"] == "fade"  # 7.7 percent
    assert classify.classify(0.0, 5.0, 10.0, 0.0, 120.0)["shape"] == "slice"  # 8.3 percent
    assert classify.classify(0.0, 5.0, 10.0, 0.0, 100.0)["shape"] == "slice"  # 10 percent


def test_anchor_5b_examples_read_as_the_text_says():
    """PGA driver f2p +5: 44 yd on 275 carry, a slice. PGA 6i f2p +2: 8 on 183, a fade."""
    assert classify.classify(0.0, 6.0, 44.0, 0.0, 275.0)["shape"] == "slice"
    assert classify.classify(0.0, 3.0, 8.0, 0.0, 183.0)["shape"] == "fade"


@pytest.mark.parametrize("side,text", [
    (0.0, "finishes on line"), (0.99, "finishes on line"), (-0.99, "finishes on line"),
    (1.0, "finishes 1 yd right"), (-1.0, "finishes 1 yd left"), (-3.7, "finishes 4 yd left"),
    (33.3, "finishes 33 yd right"),
])
def test_finish_text(side, text):
    out = classify.classify(0.0, 0.0, 0.0, side, CARRY)
    assert out["finish_text"] == text
    assert out["finish_yd"] == side


def test_result_keys():
    assert set(classify.classify(0.0, 0.0, 0.0, 0.0, CARRY)) == {"start", "shape", "name", "finish_yd", "finish_text"}


# ---------------------------------------------------------------------------
# The five golfer cases on the PGA 7 iron preset, through deliver and simulate.
# ---------------------------------------------------------------------------

P7 = presets.preset("7i", "pga")


def _golfer(path, face):
    ln = launch.deliver(P7["club_speed"], P7["attack"], path, face, P7["dyn_loft"], "7i", spin_trim=P7["spin_trim"])
    f = flight.simulate(ln.ball_speed_mph, ln.launch_deg, ln.launch_dir_deg, ln.spin_rpm, ln.spin_axis_deg)
    return ln, f, classify.classify(ln.launch_dir_deg, ln.spin_axis_deg, f.curve_yd, f.side_yd, f.carry_yd)


@pytest.mark.parametrize("path,face,name", [
    (0.0, 0.0, "Straight"),
    (5.0, 2.0, "Push draw"),
    (-3.0, -3.0, "Pull"),
    (2.0, -4.0, "Pull hook"),
])
def test_golfer_cases(path, face, name):
    assert _golfer(path, face)[2]["name"] == name


@pytest.mark.xfail(strict=True, reason=(
    "Face +4, path -3 on the PGA 7 iron launches 1.997 deg right, inside TrackMan's +-2 deg start guidance, "
    "so it reads 'Slice' and not 'Push slice'. Thresholds left as sourced (task 004.4 report)."))
def test_golfer_push_slice_reads_push_slice():
    assert _golfer(-3.0, 4.0)[2]["name"] == "Push slice"


def test_golfer_push_slice_sits_on_the_start_boundary():
    """Records why the case above reads Slice: the start is 0.003 deg inside the line."""
    ln, f, out = _golfer(-3.0, 4.0)
    assert 1.99 < ln.launch_dir_deg < classify.START_STRAIGHT_DEG
    assert out["name"] == "Slice"
    assert out["shape"] == "slice"


def test_golfer_push_draw_starts_right_and_finishes_near_the_line():
    ln, f, out = _golfer(5.0, 2.0)
    assert out["start"] == "push" and out["shape"] == "draw"
    assert abs(out["finish_yd"]) < 6.0
