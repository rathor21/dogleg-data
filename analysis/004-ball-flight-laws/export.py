"""Site data export for release 004: the JSON the ball flight page reads.

    .venv/bin/python export.py

Writes site/ball-flight/data/{model,presets,windows,ideals,camera,golden}.json
and copies the range art to site/assets/img/004_range.png and
004_range_mobile.png (same pattern as analysis/003-augusta-12/export_site_assets.py).
Idempotent and deterministic: sorted keys, floats rounded to 6 significant
digits (model.json keeps 12 because 2 pi / 60 and the air viscosity are derived
constants, golden.json keeps 9 so the JS parity test can hold 1e-6, and
camera.json keeps every digit of the fit), no NaN, no negative zero. build()
returns the bytes without touching disk, and the tests run it twice.

Files:
  model.json    every constant and coefficient the JS port needs to recompute a
                shot: flight, launch, classify, domain.
  presets.json  clubs in order with names and groups, every preset for the three
                players, and the published table rows.
  windows.json  the 27 nine-window recipes (3 players, 7 iron), MODELED.
  ideals.json   ideal bands per club and player at the preset speed, and for the
                driver the two optimizer grids so the page can interpolate live.
  camera.json   the fitted art cameras, "wide" and "mobile".
  golden.json   the JS parity fixture: tests/golden_launch.json cases with
                classify() output, sampled trajectories for 12 of them, and the
                PGA 7 iron windows.
"""

import inspect
import json
import os
import shutil
from math import isfinite

import classify
import data
import flight
import gates_launch as gl
import ideals
import launch
import presets
import windows

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, "..", "..", "site"))
DATA_DIR = os.path.join(SITE, "ball-flight", "data")
IMG_DIR = os.path.join(SITE, "assets", "img")

SIG = 6  # significant digits in presets, windows and ideals
MODEL_SIG = 12  # model.json: derived constants (2 pi / 60, viscosity) need more than 6 to keep parity
GOLDEN_SIG = 9  # golden.json: tight enough that the JS parity test can hold 1e-6
TRAJECTORY_STRIDE = 10

IMAGE_COPIES = [
    ("range_final.png", "004_range.png"),
    ("range_final_mobile.png", "004_range_mobile.png"),
]

CLUB_NAMES = {
    "driver": "Driver", "3w": "3-wood", "5w": "5-wood", "hybrid": "Hybrid", "3i": "3-iron", "4i": "4-iron",
    "5i": "5-iron", "6i": "6-iron", "7i": "7-iron", "8i": "8-iron", "9i": "9-iron", "pw": "Pitching wedge",
}
CLUB_GROUP = {
    "driver": "driver", "3w": "wood", "5w": "wood", "hybrid": "long_iron", "3i": "long_iron", "4i": "long_iron",
    "5i": "long_iron", "6i": "long_iron", "7i": "short_iron", "8i": "short_iron", "9i": "short_iron", "pw": "wedge",
}
GROUPS = [
    {"id": "driver", "name": "Driver"},
    {"id": "wood", "name": "Woods"},
    {"id": "long_iron", "name": "Long irons"},
    {"id": "short_iron", "name": "Short irons"},
    {"id": "wedge", "name": "Wedge"},
]
PLAYER_NAMES = {"pga": "PGA Tour", "lpga": "LPGA Tour", "amateur": "Average amateur"}

# 12 golden cases that also carry a sampled trajectory.
TRAJECTORY_CASES = (
    "preset_pga_driver", "preset_pga_7i", "preset_pga_pw", "preset_lpga_3w", "preset_amateur_7i",
    "golfer_straight", "golfer_push_draw", "golfer_left_left", "golfer_push_slice", "golfer_pull_hook",
    "curvature_pga_driver_+5", "edge_slow_7i",
)


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------


def clean(obj, sig=SIG):
    """Recursively round floats to `sig` significant digits, turn tuples into
    lists and keys into strings, and reject NaN and infinity. Negative zero
    becomes zero, and so does anything under 1e-12."""
    if isinstance(obj, bool) or obj is None or isinstance(obj, (int, str)):
        return obj
    if isinstance(obj, float):
        if not isfinite(obj):
            raise ValueError(f"non-finite value in export: {obj!r}")
        if abs(obj) < 1e-12:
            return 0.0  # solver noise such as 1.5e-15 yd of side
        return float(f"{obj:.{sig}g}") + 0.0
    if isinstance(obj, dict):
        return {str(k): clean(v, sig) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v, sig) for v in obj]
    raise TypeError(f"cannot export {type(obj).__name__}")


def dumps(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


# ---------------------------------------------------------------------------
# model.json
# ---------------------------------------------------------------------------


def build_model():
    dt = inspect.signature(flight.simulate).parameters["dt"].default
    return {
        "note": "Constants the JS port needs to recompute a shot. Frame: x downrange, y right (output), z up. "
                "Positive spin axis curves right. Everything modeled unless data.py says sourced.",
        "units": {"mph_to_ms": data.MPH_TO_MS, "yd_to_m": data.YD_TO_M, "rpm_to_rads": data.RPM_TO_RADS, "g": data.G},
        "ball": {"mass_kg": data.BALL_MASS_KG, "diameter_m": data.BALL_DIAMETER_M, "radius_m": data.BALL_RADIUS_M},
        "air": {"density_kg_m3": data.AIR_DENSITY_KG_M3, "viscosity_pa_s": data.AIR_VISCOSITY_PA_S},
        "aero": {
            "quad": dict(data.QUAD),
            "re_unit": data.RE_UNIT,
            "re_pivot": data.RE_PIVOT,
            "spin_decay_coef": data.SPIN_DECAY_COEF,
            "forms": "CD = d0 + d1 S + d2 S^2 + d3 (Re/1e5 - re_pivot); CL = l0 + l1 S + l2 S^2; S = R w / v; "
                     "Re = density v D / viscosity; dw/dt = -spin_decay_coef v w / R",
        },
        "roll": {"k": data.ROLL_K, "cos_power": data.ROLL_COS_POWER, "max_yd": data.ROLL_MAX_YD},
        "flight": {"dt": dt, "max_flight_s": flight.MAX_FLIGHT_S, "v_floor_ms": flight.V_FLOOR_MS, "integrator": "rk4"},
        "launch_model": dict(data.LAUNCH_MODEL),
        "spin_class": dict(launch.SPIN_CLASS),
        "domain": {k: list(v) if isinstance(v, tuple) else v for k, v in data.DOMAIN.items()},
        "classify": dict(data.CLASSIFY),
        "swing_plane_default_deg": data.SWING_PLANE_DEG,
    }


# ---------------------------------------------------------------------------
# presets.json
# ---------------------------------------------------------------------------


def _summaries(ln, f):
    return (
        {k: getattr(ln, k) for k in ln.__dataclass_fields__},
        {
            "carry_yd": f.carry_yd, "side_yd": f.side_yd, "curve_yd": f.curve_yd, "max_height_yd": f.max_height_yd,
            "apex_x_yd": f.apex_x_yd, "land_angle_deg": f.land_angle_deg, "flight_time_s": f.flight_time_s,
            "land_speed_mph": f.land_speed_mph,
        },
    )


def build_presets():
    out_presets = {}
    for player in presets.PLAYERS:
        out_presets[player] = {}
        for club in presets.CLUBS:
            p = presets.preset(club, player)
            ln = launch.deliver(p["club_speed"], p["attack"], p["path"], p["face"], p["dyn_loft"], p["club"],
                                spin_trim=p["spin_trim"])
            f = flight.simulate(ln.ball_speed_mph, ln.launch_deg, ln.launch_dir_deg, ln.spin_rpm, ln.spin_axis_deg)
            launch_out, flight_out = _summaries(ln, f)
            entry = dict(p)
            entry["at_preset"] = {"launch": launch_out, "flight": flight_out}
            out_presets[player][club] = entry
    published = {
        "pga": {c: dict(r) for c, r in data.PGA.items()},
        "lpga": {c: dict(r) for c, r in data.LPGA.items()},
        "amateur": {c: dict(a) for c, a in data.AMATEUR_ANCHORS.items()},
        "dynamic_loft_deg": {f"{t}:{c}": v for (t, c), v in data.DYNAMIC_LOFT_DEG.items()},
        "spin_loft_deg": {f"{t}:{c}": v for (t, c), v in data.SPIN_LOFT_DEG.items()},
        "note": "PGA and LPGA rows are the TrackMan 2023 tables (Anchors 1 and 2). LPGA has no 3-iron. "
                "Amateur rows exist for the driver (Combine) and the 6-iron and PW (Optimizer defaults, model output). "
                "Dynamic and spin loft are published for the driver and 6-iron only.",
    }
    return {
        "clubs": [{"id": c, "name": CLUB_NAMES[c], "group": CLUB_GROUP[c]} for c in presets.CLUBS],
        "groups": GROUPS,
        "players": [{"id": p, "name": PLAYER_NAMES[p]} for p in presets.PLAYERS],
        "presets": out_presets,
        "published": published,
    }


# ---------------------------------------------------------------------------
# windows.json
# ---------------------------------------------------------------------------


def _all_windows():
    return {player: windows.nine_windows(player) for player in presets.PLAYERS}


def build_windows(all_windows):
    return {
        "modeled": True,
        "note": "Nine-window recipes are model output. Anchor 6 anchors the concept and name only: no source "
                "publishes numbers for any window. Do not attribute them to Tiger Woods.",
        "club": data.WINDOWS["club"],
        "targets": {k: v for k, v in data.WINDOWS.items() if k != "club"},
        "height_lever": "dyn_loft = preset dyn_loft + h; attack = preset attack + attack_per_loft * h",
        "heights": list(windows.HEIGHTS),
        "shapes": list(windows.SHAPES),
        "players": {p: {f"{w['height']}_{w['shape']}": w for w in ws} for p, ws in all_windows.items()},
    }


# ---------------------------------------------------------------------------
# ideals.json
# ---------------------------------------------------------------------------


def _grid_trackman():
    speeds = ideals._TRACKMAN_SPEEDS
    aoas = ideals._TRACKMAN_AOAS

    def table(idx):
        return [[ideals._TRACKMAN[(s, a)][idx] for a in aoas] for s in speeds]

    return {
        "source": "TrackMan Driver Fitting Chart (2010), CARRY Optimizer (Anchor 4, Source 1)",
        "club_speed_mph": speeds,
        "attack_deg": aoas,
        "layout": "[club speed index][attack angle index]",
        "ball_speed_mph": table(2),
        "launch_deg": table(3),
        "spin_rpm": table(4),
        "carry_yd": table(5),
        "dyn_loft_deg": table(7),
    }


def _grid_ping():
    speeds = ideals._PING_SPEEDS
    return {
        "source": "PING Optimal Launch & Spin Chart (2019) (Anchor 4, Source 2)",
        "ball_speed_mph": speeds,
        "attack_deg": ideals._PING_AOAS,
        "layout": "[ball speed index][attack angle index]",
        "launch_deg": [[c[0] for c in data.PING_2019[s]] for s in speeds],
        "spin_rpm": [[c[1] for c in data.PING_2019[s]] for s in speeds],
    }


def build_ideals():
    bands = {p: {c: ideals.ideal_bands(c, p) for c in presets.CLUBS} for p in presets.PLAYERS}
    return {
        "metrics": list(ideals.METRICS),
        "tolerances": dict(data.IDEAL_TOL),
        "bands": bands,
        "scaling": {
            "note": "Bands are computed at the preset club speed and attack angle. Two families move with the "
                    "player's club speed, and the page recomputes them live with the model.",
            "ball_speed_mph": "target = smash * club_speed, half-width ball_speed_frac of the target",
            "carry_yd": "simulate the preset delivery at the current club speed with the preset spin trim, "
                        "half-width carry_frac of that carry",
            "side_yd_curve_yd": "half-width side_frac and curve_frac of the scaled carry",
            "fixed": "Every other band keeps its preset-speed value. Open sides are null.",
        },
        "driver": {
            "rule": "launch band = [min(sources) - margin, max(sources) + margin]; same for spin. Sources are "
                    "read by bilinear interpolation clamped to each grid: TrackMan at (club speed, attack angle), "
                    "PING at (ball speed of the ideal delivery at that club speed, attack angle).",
            "launch_margin_deg": data.IDEAL_TOL["driver_launch_margin_deg"],
            "spin_margin_rpm": data.IDEAL_TOL["driver_spin_margin_rpm"],
            "trackman_carry_2010": _grid_trackman(),
            "ping_2019": _grid_ping(),
        },
    }


# ---------------------------------------------------------------------------
# camera.json
# ---------------------------------------------------------------------------


def build_camera():
    def load(name):
        with open(os.path.join(HERE, "art", name), encoding="utf-8") as fh:
            return json.load(fh)

    return {"wide": load("art_camera_final.json"), "mobile": load("art_camera_final_mobile.json")}


# ---------------------------------------------------------------------------
# golden.json
# ---------------------------------------------------------------------------


def _trajectory(f):
    n = len(f.t)
    idx = list(range(0, n, TRAJECTORY_STRIDE))
    if idx[-1] != n - 1:
        idx.append(n - 1)  # always keep the landing sample
    return {
        "stride": TRAJECTORY_STRIDE,
        "indices": idx,
        "t": [float(f.t[i]) for i in idx],
        "x": [float(f.x[i]) for i in idx],
        "y": [float(f.y[i]) for i in idx],
        "z": [float(f.z[i]) for i in idx],
    }


def build_golden(all_windows):
    with open(gl.GOLDEN_PATH, encoding="utf-8") as fh:
        base = json.load(fh)
    cases = []
    for case in base["cases"]:
        entry = dict(case)
        ln = launch.deliver(*case["args"], **case["kwargs"])
        f = flight.simulate(ln.ball_speed_mph, ln.launch_deg, ln.launch_dir_deg, ln.spin_rpm, ln.spin_axis_deg, dt=base["dt"])
        entry["classification"] = classify.classify(ln.launch_dir_deg, ln.spin_axis_deg, f.curve_yd, f.side_yd, f.carry_yd)
        if case["id"] in TRAJECTORY_CASES:
            entry["trajectory"] = _trajectory(f)
        cases.append(entry)
    have = {c["id"] for c in cases if "trajectory" in c}
    if have != set(TRAJECTORY_CASES):
        raise RuntimeError(f"trajectory cases missing from golden_launch.json: {sorted(set(TRAJECTORY_CASES) - have)}")
    return {
        "note": "JS parity fixture. cases: tests/golden_launch.json (deliver args and outputs, flight summaries) "
                "plus classify() output for every case and sampled trajectories (steps 0, 10, 20 and the landing "
                "step) for 12. Rounded to 9 significant digits. windows_pga_7i: the nine PGA 7-iron recipes.",
        "sig_digits": GOLDEN_SIG,
        "dt": base["dt"],
        "cases": cases,
        "windows_pga_7i": {f"{w['height']}_{w['shape']}": w for w in all_windows["pga"]},
    }


# ---------------------------------------------------------------------------
# Build and write
# ---------------------------------------------------------------------------


def build():
    """{filename: bytes} for every JSON file. No disk access beyond reading inputs."""
    all_windows = _all_windows()
    return {
        "model.json": dumps(clean(build_model(), MODEL_SIG)),
        "presets.json": dumps(clean(build_presets())),
        "windows.json": dumps(clean(build_windows(all_windows))),
        "ideals.json": dumps(clean(build_ideals())),
        "camera.json": dumps(clean(build_camera(), 17)),  # 17 digits keeps every double, drops -0.0
        "golden.json": dumps(clean(build_golden(all_windows), GOLDEN_SIG)),
    }


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(IMG_DIR, exist_ok=True)
    for name, blob in build().items():
        path = os.path.join(DATA_DIR, name)
        with open(path, "wb") as fh:
            fh.write(blob)
        print(f"wrote {name} ({len(blob)} bytes)")
    for src_name, dst_name in IMAGE_COPIES:
        src = os.path.join(HERE, "art", src_name)
        dst = os.path.join(IMG_DIR, dst_name)
        shutil.copyfile(src, dst)
        print(f"copied {src_name} -> {dst}")


if __name__ == "__main__":
    main()
