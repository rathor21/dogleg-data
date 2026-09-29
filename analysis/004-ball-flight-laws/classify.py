"""Shot classifier for release 004: launch and flight numbers in, ball flight name out.

    classify(launch_dir_deg, spin_axis_deg, curve_yd, side_yd, carry_yd)
        -> dict(start, shape, name, worked_back, finish_yd, finish_text)

Right-handed frame, positive is right. A lefty display is a mirror done by the
page, so nothing here knows about handedness.

Rules (thresholds live in data.CLASSIFY):
  start   pull when launch direction is left of -START_STRAIGHT_DEG, push when
          right of +START_STRAIGHT_DEG, straight between. START_STRAIGHT_DEG
          is TrackMan's plus or minus 2 deg guidance (Anchor 5(a)).
  shape   straight when |spin axis| is at most AXIS_STRAIGHT_DEG (TrackMan's
          Spin Axis page, Anchor 5(b)). Otherwise a draw or fade when the curve
          is at most CURVE_HOOK_FRAC of the carry, and a hook or slice beyond
          that. Negative curve is left (draw, hook), positive is right (fade,
          slice). CURVE_HOOK_FRAC is MODELED and instructor adjustable: TrackMan's
          PGA driver example (face-to-path +5, 44 yd on 275 carry, 16 percent)
          reads as a slice and the PGA 6 iron example (+2, 8 yd on 183, 4.4
          percent) reads as a fade.
  on target  |side| is at most ON_TARGET_FRAC of the carry. MODELED and
          instructor adjustable.
  name    follows how instructors talk about the finish:
            straight start          the shape alone: Draw, Fade, Hook, Slice.
            straight shape          Straight, or Pull or Push after a bad start.
            start and curve oppose  (starts right and curves left, or the
                                    reverse) and the ball finishes on target:
                                    the shape alone. The ball was worked back
                                    to the target, and worked_back is True.
            start and curve oppose  and it finishes off target, either crossed
                                    over the target line or short on the start
                                    side: start plus shape, "Push hook",
                                    "Pull slice", "Push draw", "Pull fade".
            start and curve agree   start plus shape: "Push slice", "Pull hook".
          The first word is capitalized.
  finish  where the ball ends, side_yd, and a sentence for it.

The boundaries are inclusive on the straight side and on the on-target side: a
start of 2.0 deg and a spin axis of 2.0 deg both read as straight, matching
"between -2 and 2", and a finish at ON_TARGET_FRAC of the carry is on
target.
"""

import data

START_STRAIGHT_DEG = data.CLASSIFY["start_straight_deg"]
AXIS_STRAIGHT_DEG = data.CLASSIFY["axis_straight_deg"]
CURVE_HOOK_FRAC = data.CLASSIFY["curve_hook_frac"]
ON_TARGET_FRAC = data.CLASSIFY["on_target_frac"]
ON_LINE_YD = 1.0  # finish inside this many yards of the target line reads "on line"

STARTS = ("pull", "straight", "push")
SHAPES = ("straight", "draw", "fade", "hook", "slice")


def _start(launch_dir_deg):
    if launch_dir_deg < -START_STRAIGHT_DEG:
        return "pull"
    if launch_dir_deg > START_STRAIGHT_DEG:
        return "push"
    return "straight"


def _shape(spin_axis_deg, curve_yd, carry_yd):
    if abs(spin_axis_deg) <= AXIS_STRAIGHT_DEG:
        return "straight"
    left = curve_yd < 0.0
    sharp = abs(curve_yd) > CURVE_HOOK_FRAC * carry_yd
    if left:
        return "hook" if sharp else "draw"
    return "slice" if sharp else "fade"


_SHAPE_SIDE = {"draw": "left", "hook": "left", "fade": "right", "slice": "right"}
_START_SIDE = {"pull": "left", "push": "right"}


def _name(start, shape, on_target):
    """(name, worked_back)."""
    if start == "straight":
        return shape.capitalize(), False
    if shape == "straight":
        return start.capitalize(), False
    if _START_SIDE[start] != _SHAPE_SIDE[shape] and on_target:
        return shape.capitalize(), True  # started one side, curved back to the target
    return f"{start.capitalize()} {shape}", False


def _finish_text(side_yd):
    if abs(side_yd) < ON_LINE_YD:
        return "finishes on line"
    side = "right" if side_yd > 0.0 else "left"
    return f"finishes {abs(side_yd):.0f} yd {side}"


def classify(launch_dir_deg, spin_axis_deg, curve_yd, side_yd, carry_yd):
    start = _start(launch_dir_deg)
    shape = _shape(spin_axis_deg, curve_yd, carry_yd)
    on_target = abs(side_yd) <= ON_TARGET_FRAC * carry_yd
    name, worked_back = _name(start, shape, on_target)
    return {
        "start": start,
        "shape": shape,
        "name": name,
        "worked_back": worked_back,
        "finish_yd": side_yd,
        "finish_text": _finish_text(side_yd),
    }
