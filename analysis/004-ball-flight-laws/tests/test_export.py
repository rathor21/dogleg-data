"""Tests for export.py (task 004.4): deterministic JSON the page reads."""

import json
import os

import pytest

import classify
import data
import export
import flight
import launch
import presets

NAMES = ("model.json", "presets.json", "windows.json", "ideals.json", "camera.json", "golden.json")


@pytest.fixture(scope="module")
def built():
    return export.build()


def test_build_is_deterministic(built):
    again = export.build()
    assert set(built) == set(NAMES)
    for name in NAMES:
        assert built[name] == again[name], name


def test_files_parse_and_hold_no_nan(built):
    for name, blob in built.items():
        obj = json.loads(blob.decode("utf-8"), parse_constant=lambda c: pytest.fail(f"{name}: {c}"))
        assert isinstance(obj, dict)
        assert blob.endswith(b"\n")
        assert b"NaN" not in blob and b"Infinity" not in blob
        assert b"-0.0," not in blob and b"-0.0}" not in blob and b"-0.0]" not in blob


def test_keys_are_sorted(built):
    for name, blob in built.items():
        text = blob.decode("utf-8")
        obj = json.loads(text)
        assert json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n" == text, name


def test_floats_are_rounded_to_six_significant_digits(built):
    def walk(o):
        if isinstance(o, float):
            yield o
        elif isinstance(o, dict):
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)

    for name in ("presets.json", "windows.json", "ideals.json"):
        for x in walk(json.loads(built[name])):
            assert float(f"{x:.6g}") == x, (name, x)


def test_disk_copy_matches_a_fresh_build(built):
    """Run `export.py` after any model change. The committed files must equal a fresh build."""
    for name in NAMES:
        with open(os.path.join(export.DATA_DIR, name), "rb") as fh:
            assert fh.read() == built[name], f"{name} is stale, rerun export.py"


def test_images_are_copied():
    for src, dst in export.IMAGE_COPIES:
        with open(os.path.join(export.HERE, "art", src), "rb") as a, open(os.path.join(export.IMG_DIR, dst), "rb") as b:
            assert a.read() == b.read(), dst


def test_model_json_carries_the_constants(built):
    m = json.loads(built["model.json"])
    assert m["aero"]["quad"] == pytest.approx(data.QUAD, rel=1e-5)
    assert m["aero"]["spin_decay_coef"] == data.SPIN_DECAY_COEF
    assert m["units"]["rpm_to_rads"] == pytest.approx(data.RPM_TO_RADS, rel=1e-11)
    assert m["air"]["viscosity_pa_s"] == pytest.approx(data.AIR_VISCOSITY_PA_S, rel=1e-11)
    assert m["ball"]["radius_m"] == pytest.approx(data.BALL_RADIUS_M, rel=1e-11)
    assert m["launch_model"] == data.LAUNCH_MODEL
    assert m["domain"]["club_speed_mph"] == [40.0, 140.0]
    assert m["classify"] == data.CLASSIFY
    assert m["spin_class"] == launch.SPIN_CLASS
    assert m["flight"] == {"dt": 0.01, "integrator": "rk4", "max_flight_s": flight.MAX_FLIGHT_S, "v_floor_ms": flight.V_FLOOR_MS}
    assert m["roll"] == {"cos_power": data.ROLL_COS_POWER, "k": data.ROLL_K, "max_yd": data.ROLL_MAX_YD}
    assert m["swing_plane_default_deg"] == data.SWING_PLANE_DEG


def test_presets_json(built):
    p = json.loads(built["presets.json"])
    assert [c["id"] for c in p["clubs"]] == list(presets.CLUBS)
    groups = {}
    for c in p["clubs"]:
        groups.setdefault(c["group"], []).append(c["id"])
    assert groups == {"driver": ["driver"], "wood": ["3w", "5w"], "long_iron": ["hybrid", "3i", "4i", "5i", "6i"],
                      "short_iron": ["7i", "8i", "9i"], "wedge": ["pw"]}
    assert set(p["presets"]) == {"pga", "lpga", "amateur"}
    for player in presets.PLAYERS:
        assert set(p["presets"][player]) == set(presets.CLUBS)
        for club in presets.CLUBS:
            live = presets.preset(club, player)
            got = p["presets"][player][club]
            assert got["spin_trim"] == pytest.approx(live["spin_trim"], rel=1e-5)
            assert got["modeled"] is live["modeled"]
            assert got["note"] == live["note"]
            assert got["club_speed"] == pytest.approx(live["club_speed"], rel=1e-5)
    assert "4-iron" in p["presets"]["lpga"]["3i"]["note"]
    assert p["published"]["pga"]["7i"]["carry_yd"] == 176
    assert "3i" not in p["published"]["lpga"]
    assert set(p["published"]["amateur"]) == {"driver", "6i", "pw"}


def test_windows_json(built):
    w = json.loads(built["windows.json"])
    assert w["modeled"] is True and "Tiger" in w["note"]
    assert set(w["players"]) == {"pga", "lpga", "amateur"}
    for player, ws in w["players"].items():
        assert set(ws) == {f"{h}_{s}" for h in ("low", "mid", "high") for s in ("draw", "straight", "fade")}
        for key, win in ws.items():
            assert win["modeled"] is True
            assert abs(win["flight"]["side_yd"]) <= 1.5
            assert win["classification"]["name"]


def test_ideals_json(built):
    i = json.loads(built["ideals.json"])
    assert set(i["bands"]) == {"pga", "lpga", "amateur"}
    assert set(i["bands"]["pga"]["7i"]) == set(i["metrics"])
    assert i["bands"]["pga"]["7i"]["smash"]["hi"] is None
    d = i["driver"]
    assert len(d["trackman_carry_2010"]["launch_deg"]) == 10 and len(d["trackman_carry_2010"]["launch_deg"][0]) == 3
    assert len(d["ping_2019"]["launch_deg"]) == 11 and len(d["ping_2019"]["launch_deg"][0]) == 11
    assert d["ping_2019"]["ball_speed_mph"] == sorted(d["ping_2019"]["ball_speed_mph"])
    assert d["ping_2019"]["launch_deg"][-1][5] == 10.4  # 180 mph, AoA 0
    assert d["trackman_carry_2010"]["spin_rpm"][8][1] == 2919  # 115 mph, AoA 0
    assert "launch_deg" in i["bands"]["pga"]["driver"] and "detail" in i["bands"]["pga"]["driver"]["launch_deg"]


def test_camera_json_copies_the_art_files(built):
    c = json.loads(built["camera.json"])
    for key, name in (("wide", "art_camera_final.json"), ("mobile", "art_camera_final_mobile.json")):
        with open(os.path.join(export.HERE, "art", name), encoding="utf-8") as fh:
            assert c[key] == json.load(fh)


# ---------------------------------------------------------------------------
# golden.json round trip against the live model
# ---------------------------------------------------------------------------

REL = 1e-6


@pytest.fixture(scope="module")
def golden(built):
    return json.loads(built["golden.json"])


def test_golden_covers_the_launch_cases(golden):
    with open(os.path.join(export.HERE, "tests", "golden_launch.json"), encoding="utf-8") as fh:
        base = json.load(fh)
    assert [c["id"] for c in golden["cases"]] == [c["id"] for c in base["cases"]]
    assert golden["dt"] == base["dt"]
    assert sum(1 for c in golden["cases"] if "trajectory" in c) == 12
    assert {c["id"] for c in golden["cases"] if "trajectory" in c} == set(export.TRAJECTORY_CASES)


def test_golden_round_trips_against_the_live_model(golden):
    for case in golden["cases"]:
        ln = launch.deliver(*case["args"], **case["kwargs"])  # from the stored (rounded) arguments
        f = flight.simulate(ln.ball_speed_mph, ln.launch_deg, ln.launch_dir_deg, ln.spin_rpm, ln.spin_axis_deg, dt=golden["dt"])
        for k, v in case["launch"].items():
            assert getattr(ln, k) == pytest.approx(v, rel=REL, abs=REL), (case["id"], k)
        for k, v in case["flight"].items():
            assert getattr(f, k) == pytest.approx(v, rel=REL, abs=REL), (case["id"], k)
        cls = classify.classify(ln.launch_dir_deg, ln.spin_axis_deg, f.curve_yd, f.side_yd, f.carry_yd)
        stored = case["classification"]
        assert stored["name"] == cls["name"] and stored["start"] == cls["start"] and stored["shape"] == cls["shape"], case["id"]
        assert stored["finish_yd"] == pytest.approx(cls["finish_yd"], rel=REL, abs=REL)
        assert stored["finish_text"] == cls["finish_text"], case["id"]
        if "trajectory" in case:
            tr = case["trajectory"]
            idx = tr["indices"]
            assert idx[0] == 0 and idx[-1] == len(f.t) - 1
            assert idx[:-1] == list(range(0, idx[-2] + 1, tr["stride"]))
            for key in ("t", "x", "y", "z"):
                live = getattr(f, key)
                assert tr[key] == pytest.approx([float(live[i]) for i in idx], rel=REL, abs=REL), (case["id"], key)
            assert tr["z"][-1] == 0.0


def test_golden_pga_7i_windows(golden):
    w = golden["windows_pga_7i"]
    assert len(w) == 9
    for key, win in w.items():
        d = win["delivery"]
        ln = launch.deliver(d["club_speed_mph"], d["attack_deg"], d["path_deg"], d["face_deg"], d["dyn_loft_deg"], "7i",
                            spin_trim=win["spin_trim"])
        f = flight.simulate(ln.ball_speed_mph, ln.launch_deg, ln.launch_dir_deg, ln.spin_rpm, ln.spin_axis_deg)
        for k, v in win["launch"].items():
            assert getattr(ln, k) == pytest.approx(v, rel=REL, abs=REL), (key, k)
        assert f.carry_yd == pytest.approx(win["flight"]["carry_yd"], rel=REL, abs=REL), key
        assert f.max_height_yd == pytest.approx(win["flight"]["max_height_yd"], rel=REL, abs=REL), key
