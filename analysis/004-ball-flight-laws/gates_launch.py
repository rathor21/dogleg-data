"""Gate scoring for release 004.3: G3 tolerances, the curvature and preset
checks, and the miss lists.

Shared by calibrate_launch.py (fitting and reports) and tests/test_launch.py.
No scipy here. The recorded misses live in tests/g3_known_misses.json, written
by `calibrate_launch.py --write-misses` and read on demand by load_record().
Reuses gates.rows from the flight gates.

Functions that take `params` use the shipped data.LAUNCH_MODEL and the shipped
data.TOUR_DYN_LOFT table when it is None. With candidate parameters they derive
the dynamic loft live, so the fitters can score a model before it is shipped.
"""

import dataclasses
import json
import os
from typing import NamedTuple

import data
import flight
import gates
import launch
import launch_tools
import presets

# G3 tolerances (design doc, task 004.3).
G3_LAUNCH_DEG = 1.0
G3_SPIN_FRAC = 0.10
G3_BALL_FRAC = 0.02
DL_CHECK_DEG = 1.0  # inverted dynamic loft vs published, driver and 6 iron
SL_CHECK_DEG = 1.0  # spin loft vs published, driver and 6 iron
SL_CHECK_SLACK = 1e-6  # PGA driver sits on the line: 13.7 against 14.7
# Curvature examples: the larger of 20 percent and 3 yd.
CURVE_REL = 0.20
CURVE_ABS_YD = 3.0
# Presets: spin within 1 percent (the trim guarantees it), launch and ball
# speed as G3 for the amateur anchors.
PRESET_TOL = {"launch_deg": 1.0, "spin_pct": 1.0, "ball_pct": 2.0}
TABLE_DL_TOL_DEG = 0.05  # data.TOUR_DYN_LOFT against a live inversion

MISSES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "g3_known_misses.json")
SECTIONS = ("g3", "published", "presets")

rows = gates.rows


def load_record(path=MISSES_PATH):
    """The recorded {"g3": ..., "published": ..., "presets": ...} misses. Read on call, never at import."""
    with open(path) as fh:
        return json.load(fh)


def n_rows():
    return gates.n_rows()


# ---------------------------------------------------------------------------
# G3: table delivery against the table
# ---------------------------------------------------------------------------


class G3Result(NamedTuple):
    launch_err_deg: float
    spin_err_frac: float
    ball_err_frac: float
    launch: "launch.Launch"
    dyn_loft_deg: float


def tour_dyn_loft(tour, club, params=None):
    """Default dynamic loft: the shipped table, or a live inversion for candidate params."""
    if params is None:
        return data.TOUR_DYN_LOFT[(tour, club)]
    r = data.TOURS[tour][club]
    return launch_tools.derive_dyn_loft(r["launch_deg"], r["attack_deg"], params=params)


def g3_row(tour, club, params=None):
    """G3 errors for one table row at path 0, face 0, default dynamic loft."""
    r = data.TOURS[tour][club]
    dl = tour_dyn_loft(tour, club, params)
    ln = launch.deliver(r["club_speed_mph"], r["attack_deg"], 0.0, 0.0, dl, club, params=params)
    return G3Result(
        ln.launch_deg - r["launch_deg"],
        ln.spin_rpm / r["spin_rpm"] - 1.0,
        ln.ball_speed_mph / r["ball_speed_mph"] - 1.0,
        ln,
        dl,
    )


def g3_misses(params=None):
    """{"PGA/3w": {"spin_pct": err, ...}} for rows outside G3, components that miss only."""
    out = {}
    for tour, club, _row in rows():
        res = g3_row(tour, club, params)
        miss = {}
        if abs(res.launch_err_deg) > G3_LAUNCH_DEG:
            miss["launch_deg"] = round(res.launch_err_deg, 2)
        if abs(res.spin_err_frac) > G3_SPIN_FRAC:
            miss["spin_pct"] = round(100.0 * res.spin_err_frac, 1)
        if abs(res.ball_err_frac) > G3_BALL_FRAC:
            miss["ball_pct"] = round(100.0 * res.ball_err_frac, 1)
        if miss:
            out[f"{tour}/{club}"] = miss
    return out


def published_checks(params=None):
    """Driver and 6 iron against the published dynamic loft and spin loft.
    [(key, default DL, published DL, spin loft at the published DL, published SL)].
    The default DL tests the fit of k. The spin loft at the published DL tests
    the geometry (published SL is close to DL - AoA, with unexplained gaps)."""
    out = []
    for (tour, club), dl_pub in data.DYNAMIC_LOFT_DEG.items():
        r = data.TOURS[tour][club]
        sl = launch.spin_loft_deg(0.0, r["attack_deg"], 0.0, dl_pub)
        out.append((f"{tour}/{club}", tour_dyn_loft(tour, club, params), dl_pub, sl, data.SPIN_LOFT_DEG[(tour, club)]))
    return out


def published_misses(params=None):
    """{"LPGA/driver": {"spin_loft_deg": err}} where the spin loft at the
    published dynamic loft is more than SL_CHECK_DEG from the published spin loft."""
    out = {}
    for key, _dl, _dl_pub, sl, sl_pub in published_checks(params):
        if abs(sl - sl_pub) > SL_CHECK_DEG + SL_CHECK_SLACK:
            out[key] = {"spin_loft_deg": round(sl - sl_pub, 2)}
    return out


# ---------------------------------------------------------------------------
# Curvature examples (Anchor 5(b))
# ---------------------------------------------------------------------------


def curve_tol(published):
    return max(CURVE_REL * abs(published), CURVE_ABS_YD)


def curvature_delivery(tour, club, f2p, params=None):
    """(deliver arguments, keyword arguments) for one Anchor 5(b) example: the
    2019 row of that tour and club, path 0, face = face-to-path, dynamic loft
    inverted from the 2019 launch. The spin trim is that row's own 2019 spin
    over the model's spin at path 0 and face 0, held fixed as the face opens,
    like a preset's trim."""
    r = data.SUPERSEDED_2019[(tour, club)]
    dl = launch_tools.derive_dyn_loft(r["launch_deg"], r["attack_deg"], params=params)
    base = launch.deliver(r["club_speed_mph"], r["attack_deg"], 0.0, 0.0, dl, club, params=params)
    trim = r["spin_rpm"] / base.spin_rpm
    return (r["club_speed_mph"], r["attack_deg"], 0.0, f2p, dl, club), {"params": params, "spin_trim": trim}


def fly(ln, dt=0.01):
    return flight.simulate(ln.ball_speed_mph, ln.launch_deg, ln.launch_dir_deg, ln.spin_rpm, ln.spin_axis_deg, dt=dt)


def curvature_example(tour, club, f2p, params=None, dt=0.01):
    args, kwargs = curvature_delivery(tour, club, f2p, params)
    ln = launch.deliver(*args, **kwargs)
    return ln, fly(ln, dt)


def curvature_errors(params=None, dt=0.01):
    """[(tour, club, f2p, published, model curve, normalized error)]; 1.0 sits on the tolerance."""
    out = []
    for tour, club, f2p, pub in data.CURVATURE_EXAMPLES:
        _ln, f = curvature_example(tour, club, f2p, params, dt)
        out.append((tour, club, f2p, pub, f.curve_yd, (f.curve_yd - pub) / curve_tol(pub)))
    return out


def curvature_passes(params=None, dt=0.01):
    return sum(1 for *_x, err in curvature_errors(params, dt) if abs(err) <= 1.0)


# ---------------------------------------------------------------------------
# Presets against their published rows
# ---------------------------------------------------------------------------

_TOUR_OF = {"pga": "PGA", "lpga": "LPGA"}


def preset_keys():
    """[(player, club)] for every preset with a published row. Static, runs no model."""
    keys = [(player, club) for player in ("pga", "lpga") for club in data.TOURS[_TOUR_OF[player]]]
    return keys + [("amateur", club) for club in data.AMATEUR_ANCHORS]


def preset_published(player, club):
    """The published launch, spin and ball speed a preset should reproduce."""
    if player == "amateur":
        a = data.AMATEUR_ANCHORS[club]
        return dict(launch=a["launch_deg"], spin=a["spin_rpm"], ball=a["ball_speed_mph"])
    r = data.TOURS[_TOUR_OF[player]][club]
    return dict(launch=r["launch_deg"], spin=r["spin_rpm"], ball=r["ball_speed_mph"])


def preset_errors(player, club):
    """(launch err deg, spin err percent, ball speed err percent) for a preset."""
    p = presets.preset(club, player)
    pub = preset_published(player, club)
    ln = launch.deliver(p["club_speed"], p["attack"], p["path"], p["face"], p["dyn_loft"], p["club"], spin_trim=p["spin_trim"])
    return (
        ln.launch_deg - pub["launch"],
        100.0 * (ln.spin_rpm / pub["spin"] - 1.0),
        100.0 * (ln.ball_speed_mph / pub["ball"] - 1.0),
    )


def preset_misses():
    """{"amateur/driver": {...}} for presets outside their tolerances. Tour
    presets are scored on spin only: their launch and ball speed are the G3
    row's numbers, recorded once under "g3"."""
    out = {}
    for player, club in preset_keys():
        err_launch, err_spin, err_ball = preset_errors(player, club)
        miss = {}
        if abs(err_spin) > PRESET_TOL["spin_pct"]:
            miss["spin_pct"] = round(err_spin, 2)
        if player == "amateur":
            if abs(err_launch) > PRESET_TOL["launch_deg"]:
                miss["launch_deg"] = round(err_launch, 2)
            if abs(err_ball) > PRESET_TOL["ball_pct"]:
                miss["ball_pct"] = round(err_ball, 2)
        if miss:
            out[f"{player}/{club}"] = miss
    return out


def current_misses():
    return {"g3": g3_misses(), "published": published_misses(), "presets": preset_misses()}


# ---------------------------------------------------------------------------
# Golden vectors for the JS parity test (tests/golden_launch.json)
# ---------------------------------------------------------------------------

GOLDEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "golden_launch.json")
GOLDEN_DT = 0.01
GOLDEN_CLUBS = ("driver", "3w", "4i", "7i", "pw")  # one per group: driver, wood, long iron, short iron, wedge

# (path, face) of the five golfer cases on the PGA 7 iron preset.
GOLFER_CASES = (("straight", 0.0, 0.0), ("push_draw", 5.0, 2.0), ("left_left", -3.0, -3.0),
                ("push_slice", -3.0, 4.0), ("pull_hook", 2.0, -4.0))


def golden_cases():
    """[(id, args, kwargs)] for about 40 deliveries: presets for every player
    and club group, the golfer cases, the curvature examples, domain edges and
    the smallest allowed spin loft (dynamic loft = attack + 1) with face-to-path
    of plus and minus 5."""
    cases = []
    for player in presets.PLAYERS:
        for club in GOLDEN_CLUBS:
            p = presets.preset(club, player)
            args = (p["club_speed"], p["attack"], p["path"], p["face"], p["dyn_loft"], p["club"])
            cases.append((f"preset_{player}_{club}", args, {"spin_trim": p["spin_trim"]}))
    p7 = presets.preset("7i", "pga")
    for name, path, face in GOLFER_CASES:
        args = (p7["club_speed"], p7["attack"], path, face, p7["dyn_loft"], "7i")
        cases.append((f"golfer_{name}", args, {"spin_trim": p7["spin_trim"]}))
    for tour, club, f2p, _pub in data.CURVATURE_EXAMPLES:
        args, kwargs = curvature_delivery(tour, club, f2p)
        cases.append((f"curvature_{tour.lower()}_{club}_{f2p:+.0f}", args, {"spin_trim": kwargs["spin_trim"]}))
    edges = (
        ("slow_7i", (40.0, 0.0, 0.0, 0.0, 30.0, "7i")),
        ("fast_driver", (140.0, -2.0, 0.0, 0.0, 12.0, "driver")),
        ("attack_min", (90.0, -10.0, 0.0, 0.0, 20.0, "8i")),
        ("attack_max", (100.0, 10.0, 0.0, 0.0, 20.0, "driver")),
        ("path_right_face_left", (92.0, -3.0, 15.0, -15.0, 25.0, "7i")),
        ("path_left_face_right", (92.0, -3.0, -15.0, 15.0, 25.0, "7i")),
        ("loft_zero", (80.0, -10.0, 0.0, 0.0, 0.0, "pw")),
        ("loft_max", (60.0, 10.0, 5.0, 5.0, 65.0, "pw")),
    )
    for name, args in edges:
        cases.append((f"edge_{name}", args, {}))
    for attack in (0.0, 5.0):
        for f2p in (-5.0, 5.0):
            args = (90.0, attack, 0.0, f2p, attack + data.DOMAIN["min_spin_loft_deg"], "7i")
            cases.append((f"minloft_attack{attack:+.0f}_f2p{f2p:+.0f}", args, {}))
    return cases


def golden_entry(case_id, args, kwargs):
    ln = launch.deliver(*args, **kwargs)
    f = fly(ln, GOLDEN_DT)
    return {
        "id": case_id,
        "args": list(args),
        "kwargs": dict(kwargs),
        "launch": dataclasses.asdict(ln),
        "flight": {
            "carry_yd": f.carry_yd, "side_yd": f.side_yd, "curve_yd": f.curve_yd,
            "max_height_yd": f.max_height_yd, "apex_x_yd": f.apex_x_yd,
            "land_angle_deg": f.land_angle_deg, "flight_time_s": f.flight_time_s,
            "land_speed_mph": f.land_speed_mph,
        },
    }


def golden_record():
    return {
        "dt": GOLDEN_DT,
        "note": "deliver outputs and flight summaries; regenerate with calibrate_launch.py --write-golden",
        "domain": {k: list(v) if isinstance(v, tuple) else v for k, v in data.DOMAIN.items()},
        "launch_model": dict(data.LAUNCH_MODEL),
        "cases": [golden_entry(*c) for c in golden_cases()],
    }
