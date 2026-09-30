"""Tests for classify.py (task 004.4): start, shape, name and finish text."""

import itertools

import pytest

import classify
import data
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
    assert classify.ON_TARGET_FRAC == data.CLASSIFY["on_target_frac"] == 0.04  # MODELED
    assert classify.ON_LINE_YD == data.CLASSIFY["on_line_yd"] == 1.0  # MODELED


# Off-target finish for the "missed" names: 40 yd is 20 percent of the carry.
OFF_LEFT, OFF_RIGHT = -40.0, 40.0


def _off_target_side(start, shape):
    """A finish 20 percent of the carry off the line, on the curve side, so no
    start and shape pair reads as worked back."""
    if start == "straight" or shape == "straight":
        return 0.0
    return OFF_LEFT if SHAPE_INPUT[shape][1] < 0 else OFF_RIGHT


@pytest.mark.parametrize("start,shape", list(itertools.product(START_DIR, SHAPE_INPUT)))
def test_every_start_and_shape_is_reachable(start, shape):
    axis, curve = SHAPE_INPUT[shape]
    out = classify.classify(START_DIR[start], axis, curve, _off_target_side(start, shape), CARRY)
    assert out["start"] == start
    assert out["shape"] == shape
    assert out["name"] == _name(start, shape)
    assert out["worked_back"] is False


def test_fifteen_distinct_names():
    names = {
        classify.classify(START_DIR[s], SHAPE_INPUT[h][0], SHAPE_INPUT[h][1], _off_target_side(s, h), CARRY)["name"]
        for s, h in itertools.product(START_DIR, SHAPE_INPUT)
    }
    assert len(names) == 15
    assert {"Straight", "Pull", "Push", "Draw", "Fade", "Hook", "Slice", "Pull hook", "Push draw", "Pull fade",
            "Push slice", "Pull draw", "Push fade", "Pull slice", "Push hook"} == names


# (start deg, shape, side yd on a 200 yd carry) -> (name, worked_back). On target is 8 yd (4 percent).
FINISH_NAMES = [
    # starts right, curves left
    (3.0, "draw", -2.0, "Draw", True),  # worked back to the target
    (3.0, "hook", 5.0, "Hook", True),
    (3.0, "draw", 8.0, "Draw", True),  # 4 percent, inclusive
    (3.0, "draw", 8.5, "Push draw", False),  # short of the target on the start side
    (3.0, "draw", -8.5, "Push draw", False),  # crossed over would also be off target
    (3.0, "hook", -30.0, "Push hook", False),  # crossed over to the curve side
    (3.0, "hook", 30.0, "Push hook", False),
    # starts left, curves right
    (-3.0, "fade", 2.0, "Fade", True),
    (-3.0, "slice", -5.0, "Slice", True),
    (-3.0, "fade", -8.5, "Pull fade", False),
    (-3.0, "slice", 30.0, "Pull slice", False),
    # start and curve agree: never worked back, even on target
    (3.0, "fade", 0.0, "Push fade", False),
    (3.0, "slice", 0.0, "Push slice", False),
    (-3.0, "draw", 0.0, "Pull draw", False),
    (-3.0, "hook", 0.0, "Pull hook", False),
    (-3.0, "hook", -30.0, "Pull hook", False),
    # straight start keeps the shape alone, straight shape keeps Pull, Push, Straight
    (0.0, "draw", 30.0, "Draw", False),
    (0.0, "slice", -30.0, "Slice", False),
    (-3.0, "straight", 0.0, "Pull", False),
    (3.0, "straight", -30.0, "Push", False),
    (0.0, "straight", 30.0, "Straight", False),
]


@pytest.mark.parametrize("start_deg,shape,side,name,worked_back", FINISH_NAMES)
def test_finish_aware_names(start_deg, shape, side, name, worked_back):
    axis, curve = SHAPE_INPUT[shape]
    out = classify.classify(start_deg, axis, curve, side, CARRY)
    assert out["name"] == name
    assert out["worked_back"] is worked_back


def test_on_target_boundary_scales_with_carry():
    """4 percent of the carry, inclusive: 8 yd on 200, 4 yd on 100."""
    args = (3.0, -5.0, -5.0)
    assert classify.classify(*args, 8.0, 200.0)["name"] == "Draw"
    assert classify.classify(*args, 8.01, 200.0)["name"] == "Push draw"
    assert classify.classify(*args, 4.0, 100.0)["name"] == "Draw"
    assert classify.classify(*args, 4.5, 100.0)["name"] == "Push draw"


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
    # round half up on the absolute value, like JS Math.round(Math.abs(x))
    (0.5, "finishes on line"), (-0.5, "finishes on line"),
    (1.5, "finishes 2 yd right"), (-1.5, "finishes 2 yd left"),
    (2.5, "finishes 3 yd right"), (-2.5, "finishes 3 yd left"),
    (8.5, "finishes 9 yd right"), (-8.5, "finishes 9 yd left"),
    (8.49, "finishes 8 yd right"), (1.0, "finishes 1 yd right"),
])
def test_finish_text(side, text):
    out = classify.classify(0.0, 0.0, 0.0, side, CARRY)
    assert out["finish_text"] == text
    assert out["finish_yd"] == side


def test_result_keys():
    assert set(classify.classify(0.0, 0.0, 0.0, 0.0, CARRY)) == {"start", "shape", "name", "worked_back", "finish_yd", "finish_text"}


# ---------------------------------------------------------------------------
# The five golfer cases on the PGA 7 iron preset, through deliver and simulate.
# ---------------------------------------------------------------------------

P7 = presets.preset("7i", "pga")


def _golfer(path, face):
    ln, f = presets.fly(P7, path=path, face=face)
    return ln, f, classify.classify(ln.launch_dir_deg, ln.spin_axis_deg, f.curve_yd, f.side_yd, f.carry_yd)


@pytest.mark.parametrize("path,face,name,worked_back", [
    (0.0, 0.0, "Straight", False),
    (5.0, 2.0, "Draw", True),  # starts 2.86 right, finishes 4 yd left of a 173 yd carry (2.1 percent)
    (-3.0, -3.0, "Pull", False),
    (-3.0, 5.0, "Push slice", False),
    (2.0, -4.0, "Pull hook", False),
])
def test_golfer_cases(path, face, name, worked_back):
    out = _golfer(path, face)[2]
    assert out["name"] == name
    assert out["worked_back"] is worked_back


def test_golfer_push_slice_sits_on_the_start_boundary_at_face_4():
    """Face +4, path -3 launches 1.955 deg right (with the face-to-loft coupling on,
    the open face adds loft and pulls the start line in), 0.045 deg inside
    TrackMan's 2 deg line, so it reads Slice. Face +5 is the push slice case."""
    ln, f, out = _golfer(-3.0, 4.0)
    assert 1.9 < ln.launch_dir_deg < classify.START_STRAIGHT_DEG
    assert out["name"] == "Slice"
    assert out["shape"] == "slice"
    assert _golfer(-3.0, 5.0)[0].launch_dir_deg > classify.START_STRAIGHT_DEG


def test_golfer_push_draw_starts_right_curves_left_and_is_worked_back():
    ln, f, out = _golfer(5.0, 2.0)
    assert out["start"] == "push" and out["shape"] == "draw"
    assert out["worked_back"] is True
    assert abs(out["finish_yd"]) < classify.ON_TARGET_FRAC * f.carry_yd


# ---------------------------------------------------------------------------
# Input validation and the axis tiebreak
# ---------------------------------------------------------------------------

BAD = [float("nan"), float("inf"), float("-inf")]


@pytest.mark.parametrize("index", range(5))
@pytest.mark.parametrize("bad", BAD)
def test_non_finite_input_raises(index, bad):
    args = [0.0, 0.0, 0.0, 0.0, CARRY]
    args[index] = bad
    with pytest.raises(ValueError, match="finite"):
        classify.classify(*args)


@pytest.mark.parametrize("carry", [0.0, -1.0, -200.0])
def test_carry_of_zero_or_less_raises(carry):
    with pytest.raises(ValueError, match="carry_yd"):
        classify.classify(0.0, 0.0, 0.0, 0.0, carry)


def test_tiny_positive_carry_is_accepted():
    assert classify.classify(0.0, 0.0, 0.0, 0.0, 1e-9)["name"] == "Straight"


@pytest.mark.parametrize("axis,shape", [(-5.0, "draw"), (5.0, "fade"), (-2.5, "draw"), (2.5, "fade")])
def test_zero_curve_takes_the_side_of_the_axis(axis, shape):
    """Curve equal to 0 with the axis past the straight band: the axis sign is the tiebreak."""
    assert classify.classify(0.0, axis, 0.0, 0.0, CARRY)["shape"] == shape
    assert classify.classify(0.0, axis, -0.0, 0.0, CARRY)["shape"] == shape  # negative zero is still zero


def test_axis_tiebreak_never_overrides_a_nonzero_curve():
    assert classify.classify(0.0, 5.0, -0.001, 0.0, CARRY)["shape"] == "draw"
    assert classify.classify(0.0, -5.0, 0.001, 0.0, CARRY)["shape"] == "fade"
