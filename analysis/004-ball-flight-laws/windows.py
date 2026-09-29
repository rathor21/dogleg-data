"""Nine windows for release 004: low, mid and high against draw, straight and fade.

    solve_window(club, player, height, shape) -> dict
    nine_windows(player, club=None)           -> list of nine dicts

Anchor 6 (TaylorMade, "Tiger Woods' Nine Windows", 2021) anchors the concept
and the name. It holds no numbers, so every recipe here is model output, is
labeled MODELED and is never attributed to Tiger Woods. Targets are in
data.WINDOWS.

For a player and club (default 7 iron) each window solves three unknowns, club
path, face angle and a height lever h, so that the flight from launch.deliver
and flight.simulate hits three targets:
    peak height   = height_mult x the preset's modeled peak height
    curve         = curve_frac x this window's own carry (draw negative)
    side          = 0, the ball finishes on the target line (tolerance
                    data.WINDOWS["side_tol_yd"], checked by the tests)
The height lever moves dynamic loft and attack angle together:
    dyn_loft = preset dynamic loft + h
    attack   = preset attack angle + attack_per_loft * h
MODELED: a lower shot comes from a ball played further back, which delofts and
steepens the blow at once. Club speed and spin trim stay at the preset.

Every trial stays inside data.DOMAIN (bounds on the unknowns, and dynamic loft
minus attack angle above the spin loft floor).

A draw that finishes on the line has to start right of it by about
atan(curve_frac). At the default 5 percent that is 2.9 deg, past TrackMan's plus
or minus 2 deg start guidance, but the ball is worked back to the target, so
classify() names the window "Draw" (and the mirror "Fade").
"""

import numpy as np
from scipy.optimize import least_squares

import classify
import data
import flight
import launch
import presets

HEIGHTS = tuple(data.WINDOWS["heights"])  # low, mid, high
SHAPES = tuple(data.WINDOWS["curve_frac"])  # draw, straight, fade

# Starting points for the solver: (height lever h, path, face). A window with a
# lower or higher peak starts with a rough loft shift, and a draw or fade with
# a rough path and face pair.
_H_START = {"low": -6.0, "mid": 0.0, "high": 5.0}
_PATH_FACE_START = {"draw": (4.0, 1.5), "straight": (0.0, 0.0), "fade": (-4.0, -1.0)}


def _fly(p, path, face, h):
    attack = p["attack"] + data.WINDOWS["attack_per_loft"] * h
    dyn_loft = p["dyn_loft"] + h
    ln = launch.deliver(p["club_speed"], attack, path, face, dyn_loft, p["club"], spin_trim=p["spin_trim"])
    f = flight.simulate(ln.ball_speed_mph, ln.launch_deg, ln.launch_dir_deg, ln.spin_rpm, ln.spin_axis_deg)
    return attack, dyn_loft, ln, f


def _bounds(p):
    """Bounds on (path, face, h) that keep every trial inside data.DOMAIN."""
    dom = data.DOMAIN
    apl = data.WINDOWS["attack_per_loft"]
    h_lo = max(dom["dyn_loft_deg"][0] - p["dyn_loft"], (dom["attack_deg"][0] - p["attack"]) / apl)
    h_hi = min(dom["dyn_loft_deg"][1] - p["dyn_loft"], (dom["attack_deg"][1] - p["attack"]) / apl)
    return ([dom["path_deg"][0], dom["face_deg"][0], h_lo], [dom["path_deg"][1], dom["face_deg"][1], h_hi])


def preset_flight(club, player):
    """(preset dict, launch, flight) at the preset delivery, path 0 and face 0."""
    p = presets.preset(club, player)
    _, _, ln, f = _fly(p, 0.0, 0.0, 0.0)
    return p, ln, f


def solve_window(club, player, height, shape):
    """One window. Raises RuntimeError if the solver misses a target by more
    than the tolerances in data.WINDOWS."""
    p, _, base = preset_flight(club, player)
    target_height = data.WINDOWS["heights"][height] * base.max_height_yd
    curve_frac = data.WINDOWS["curve_frac"][shape]
    path0, face0 = _PATH_FACE_START[shape]
    lo, hi = _bounds(p)

    def residual(x):
        _, _, _, f = _fly(p, x[0], x[1], x[2])
        return [f.max_height_yd - target_height, f.curve_yd - curve_frac * f.carry_yd, f.side_yd]

    x0 = np.clip([path0, face0, _H_START[height]], lo, hi)
    sol = least_squares(residual, x0, bounds=(lo, hi), x_scale=[1.0, 1.0, 1.0], diff_step=1e-4, xtol=1e-12, ftol=1e-12, gtol=1e-12)
    path, face, h = (float(v) for v in sol.x)
    attack, dyn_loft, ln, f = _fly(p, path, face, h)
    err = residual(sol.x)
    if abs(err[0]) > 0.05 or abs(err[1]) > 0.05 or abs(err[2]) > 0.05:
        raise RuntimeError(f"window {player} {club} {height} {shape} did not converge, residuals {err}")
    cls = classify.classify(ln.launch_dir_deg, ln.spin_axis_deg, f.curve_yd, f.side_yd, f.carry_yd)
    return {
        "player": player,
        "club": p["club"],
        "height": height,
        "shape": shape,
        "modeled": True,
        "height_lever_deg": h,
        "target": {
            "max_height_yd": target_height,
            "curve_yd": curve_frac * f.carry_yd,
            "side_yd": 0.0,
        },
        "delivery": {
            "club_speed_mph": p["club_speed"],
            "attack_deg": attack,
            "path_deg": path,
            "face_deg": face,
            "dyn_loft_deg": dyn_loft,
        },
        "spin_trim": p["spin_trim"],
        "launch": {
            "ball_speed_mph": ln.ball_speed_mph,
            "smash": ln.smash,
            "launch_deg": ln.launch_deg,
            "launch_dir_deg": ln.launch_dir_deg,
            "spin_rpm": ln.spin_rpm,
            "spin_axis_deg": ln.spin_axis_deg,
            "spin_loft_deg": ln.spin_loft_deg,
            "face_to_path_deg": ln.face_to_path_deg,
        },
        "flight": {
            "carry_yd": f.carry_yd,
            "side_yd": f.side_yd,
            "curve_yd": f.curve_yd,
            "max_height_yd": f.max_height_yd,
            "apex_x_yd": f.apex_x_yd,
            "land_angle_deg": f.land_angle_deg,
            "flight_time_s": f.flight_time_s,
            "land_speed_mph": f.land_speed_mph,
        },
        "classification": cls,
    }


def nine_windows(player, club=None):
    club = data.WINDOWS["club"] if club is None else club
    return [solve_window(club, player, h, s) for h in HEIGHTS for s in SHAPES]
