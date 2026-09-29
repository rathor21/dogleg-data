"""Tests for export.py (task 004.4): deterministic JSON the page reads."""

import json
import os
import re

import pytest

import classify
import data
import export
import flight
import ideals
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


def _same(a, b, path=""):
    """Structural equality with a relative tolerance on floats."""
    if isinstance(a, dict):
        assert isinstance(b, dict) and set(a) == set(b), path
        for k in a:
            _same(a[k], b[k], f"{path}/{k}")
    elif isinstance(a, list):
        assert isinstance(b, list) and len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            _same(x, y, f"{path}[{i}]")
    elif isinstance(a, float) or isinstance(b, float):
        assert a == pytest.approx(b, rel=1e-4, abs=1e-6), path
    else:
        assert a == b, path


def test_disk_copy_matches_a_fresh_build(built):
    """Run `export.py` after any model change. The committed files must equal a
    fresh build. windows.json comes from a least-squares solve, so it is compared
    with a tolerance and every other file byte for byte."""
    for name in NAMES:
        with open(os.path.join(export.DATA_DIR, name), "rb") as fh:
            disk = fh.read()
        if name == "windows.json":
            _same(json.loads(disk), json.loads(built[name]))
        else:
            assert disk == built[name], f"{name} is stale, rerun export.py"
    with open(os.path.join(export.DATA_DIR, "SCHEMA.md"), encoding="utf-8") as fh:
        assert fh.read() == export.SCHEMA, "SCHEMA.md is stale, rerun export.py"


def test_images_are_copied():
    for src, dst in export.IMAGE_COPIES:
        with open(os.path.join(export.HERE, "art", src), "rb") as a, open(os.path.join(export.IMG_DIR, dst), "rb") as b:
            data = b.read()
            assert a.read() == data, dst
        assert dst.endswith(".jpg") and data[:3] == b"\xff\xd8\xff", f"{dst} must hold JPEG data"


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
    assert m["classify"]["on_target_frac"] == 0.04 and m["classify"]["on_line_yd"] == 1.0
    assert m["spin_class"] == launch.SPIN_CLASS
    assert m["flight"] == {"dt": 0.01, "integrator": "rk4", "max_flight_s": flight.MAX_FLIGHT_S, "v_floor_ms": flight.V_FLOOR_MS}
    assert {k: m["roll"][k] for k in ("cos_power", "k", "max_yd")} == {
        "cos_power": data.ROLL_COS_POWER, "k": data.ROLL_K, "max_yd": data.ROLL_MAX_YD}
    assert "total_yd" in m["roll"]["form"]
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
            for old, new in export.DELIVERY_NAMES.items():
                assert got[new] == pytest.approx(live[old], rel=1e-5, abs=1e-9), (player, club, new)
                assert old not in got
            assert got["at_preset"]["flight"]["total_yd"] > got["at_preset"]["flight"]["carry_yd"]
    assert "4-iron" in p["presets"]["lpga"]["3i"]["note"]
    assert set(p["published"]) == {"pga", "lpga", "amateur"}  # nested {player: {club: row}}, lowercase
    assert p["published"]["pga"]["7i"]["carry_yd"] == 176
    assert p["published"]["pga"]["driver"]["dyn_loft_deg"] == 12.8 and p["published"]["lpga"]["6i"]["spin_loft_deg"] == 25.9
    assert "dyn_loft_deg" not in p["published"]["pga"]["7i"]
    assert "3i" not in p["published"]["lpga"]
    assert set(p["published"]["amateur"]) == {"driver", "6i", "pw"}
    assert p["published"]["amateur"]["driver"]["spin_rpm"] == 3275


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
    assert len(i["metrics"]) == 18 and "club_speed_mph" in i["metrics"] and "path_deg" in i["metrics"]
    assert "club_speed" not in i["metrics"] and "club_path_deg" not in i["metrics"]
    for player in i["bands"]:
        for club, bands in i["bands"][player].items():
            assert set(bands) == set(i["metrics"]), (player, club)
            for metric, band in bands.items():
                assert "source" not in band and band["source_id"] in i["sources"], (player, club, metric)
    assert i["bands"]["pga"]["7i"]["smash"]["hi"] is None
    assert i["bands"]["pga"]["driver"]["launch_deg"]["source_id"] == "launch_deg_driver"
    assert i["bands"]["pga"]["7i"]["launch_deg"]["source_id"] == "launch_deg"
    assert set(i["sources"]) == set(i["metrics"]) | {"launch_deg_driver", "spin_rpm_driver"}
    d = i["driver"]
    assert len(d["trackman_carry_2010"]["launch_deg"]) == 10 and len(d["trackman_carry_2010"]["launch_deg"][0]) == 3
    assert len(d["ping_2019"]["launch_deg"]) == 11 and len(d["ping_2019"]["launch_deg"][0]) == 11
    assert d["ping_2019"]["ball_speed_mph"] == sorted(d["ping_2019"]["ball_speed_mph"])
    assert d["ping_2019"]["launch_deg"][-1][5] == 10.4  # 180 mph, AoA 0
    assert d["trackman_carry_2010"]["spin_rpm"][8][1] == 2919  # 115 mph, AoA 0
    assert "detail" in i["bands"]["pga"]["driver"]["launch_deg"]
    assert d["trackman_carry_2010"] == export.clean(ideals.optimizer_grids()["trackman_carry_2010"])
    ex = i["known_exceptions"]
    assert [(e["club"], e["player"], e["metric"]) for e in ex] == [("driver", "lpga", "launch_deg")]
    assert ex[0]["value"] < ex[0]["lo"]


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
    for c, b in zip(golden["cases"], base["cases"]):  # same deliveries as the launch fixture
        d = c["delivery"]
        assert [d[k] for k in ("club_speed_mph", "attack_deg", "path_deg", "face_deg", "dyn_loft_deg")] \
            == pytest.approx(b["args"][:5], rel=1e-8, abs=1e-8), c["id"]
        assert d["club"] == b["args"][5] and d["spin_trim"] == pytest.approx(b["kwargs"].get("spin_trim", 1.0), rel=1e-8)
    assert golden["dt"] == base["dt"]
    assert sum(1 for c in golden["cases"] if "trajectory" in c) == 12
    assert {c["id"] for c in golden["cases"] if "trajectory" in c} == set(export.TRAJECTORY_CASES)


def test_golden_round_trips_against_the_live_model(golden):
    for case in golden["cases"]:
        d = case["delivery"]
        assert set(d) == {"club_speed_mph", "attack_deg", "path_deg", "face_deg", "dyn_loft_deg", "club", "spin_trim"}
        # from the stored (rounded) delivery, the way the JS port will
        ln = launch.deliver(d["club_speed_mph"], d["attack_deg"], d["path_deg"], d["face_deg"], d["dyn_loft_deg"],
                            d["club"], spin_trim=d["spin_trim"])
        f = flight.simulate(ln.ball_speed_mph, ln.launch_deg, ln.launch_dir_deg, ln.spin_rpm, ln.spin_axis_deg, dt=golden["dt"])
        for k, v in case["launch"].items():
            assert getattr(ln, k) == pytest.approx(v, rel=REL, abs=REL), (case["id"], k)
        assert set(case["flight"]) == {"carry_yd", "side_yd", "curve_yd", "max_height_yd", "apex_x_yd", "land_angle_deg",
                                       "flight_time_s", "land_speed_mph", "total_yd"}
        for k, v in case["flight"].items():
            live = flight.roll(f) if k == "total_yd" else getattr(f, k)
            assert live == pytest.approx(v, rel=REL, abs=REL), (case["id"], k)
        if f.carry_yd <= 0.0:
            assert case["classification"] is None and case["id"] == "edge_loft_zero"
            continue
        cls = classify.classify(ln.launch_dir_deg, ln.spin_axis_deg, f.curve_yd, f.side_yd, f.carry_yd)
        stored = case["classification"]
        assert stored["name"] == cls["name"] and stored["start"] == cls["start"] and stored["shape"] == cls["shape"], case["id"]
        assert stored["worked_back"] is cls["worked_back"], case["id"]
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


def test_golden_classify_vectors(golden):
    vecs = golden["classify_vectors"]
    assert len(vecs) == 7 * 8 * 10
    for v in vecs:
        live = classify.classify(*v["args"])
        got = v["result"]
        assert {k: got[k] for k in ("start", "shape", "name", "worked_back", "finish_text")} == \
            {k: live[k] for k in ("start", "shape", "name", "worked_back", "finish_text")}, v["args"]
    names = {v["result"]["name"] for v in vecs}
    assert {"Draw", "Push draw", "Pull fade", "Push slice", "Pull hook", "Straight"} <= names
    assert any(v["result"]["worked_back"] for v in vecs)


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


# ---------------------------------------------------------------------------
# One vocabulary, lowercase ids, and the schema doc
# ---------------------------------------------------------------------------

LEGACY_KEYS = {"club_speed", "attack", "path", "face", "dyn_loft", "club_path_deg"}


def _all_keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from _all_keys(v)
    elif isinstance(o, list):
        for v in o:
            yield from _all_keys(v)


def test_no_legacy_names_in_any_file(built):
    for name in ("model.json", "presets.json", "windows.json", "ideals.json", "golden.json"):
        keys = set(_all_keys(json.loads(built[name])))
        assert not keys & LEGACY_KEYS, (name, keys & LEGACY_KEYS)
        assert not {k for k in keys if k != k.lower() and k in ("PGA", "LPGA")}, name


def test_player_ids_are_lowercase_everywhere(built):
    for name in ("presets.json", "windows.json", "ideals.json"):
        obj = json.loads(built[name])
        for key in ("presets", "published", "players", "bands"):
            if key in obj and isinstance(obj[key], dict):
                assert set(obj[key]) <= {"pga", "lpga", "amateur", "note"}, (name, key)
    assert {p["id"] for p in json.loads(built["presets.json"])["players"]} == {"pga", "lpga", "amateur"}
    assert not any(":" in k for k in _all_keys(json.loads(built["presets.json"])))  # no "PGA:driver" style keys


def test_schema_names_every_exported_key(built):
    """SCHEMA.md must mention each key, backticked, at the levels where the keys are fixed."""
    schema = export.SCHEMA
    groups = []
    for name in NAMES:
        groups.append((name, list(json.loads(built[name]))))
    p = json.loads(built["presets.json"])
    groups.append(("preset", list(p["presets"]["pga"]["7i"]) + list(p["presets"]["pga"]["7i"]["at_preset"]["flight"])
                   + list(p["presets"]["pga"]["7i"]["at_preset"]["launch"])))
    groups.append(("published", list(p["published"]["pga"]["driver"]) + list(p["published"]["amateur"]["driver"])))
    w = json.loads(built["windows.json"])
    win = w["players"]["pga"]["mid_draw"]
    groups.append(("window", list(win) + list(win["delivery"]) + list(win["target"]) + list(win["classification"])
                   + list(w["targets"])))
    i = json.loads(built["ideals.json"])
    groups.append(("ideals", list(i["driver"]) + list(i["driver"]["ping_2019"]) + list(i["driver"]["trackman_carry_2010"])
                   + list(i["bands"]["pga"]["driver"]["launch_deg"]) + list(i["bands"]["pga"]["driver"]["launch_deg"]["detail"])
                   + list(i["known_exceptions"][0])))
    m = json.loads(built["model.json"])
    groups.append(("model", [k for sec in ("units", "ball", "air", "aero", "roll", "flight", "launch_model", "classify", "domain")
                             for k in m[sec]]))
    g = json.loads(built["golden.json"])
    c = next(c for c in g["cases"] if "trajectory" in c)
    groups.append(("golden", list(c) + list(c["delivery"]) + list(c["trajectory"]) + list(g["classify_vectors"][0])))
    for label, keys in groups:
        for k in keys:
            if k.startswith("_"):
                continue
            assert re.search(rf"(?<!\w){re.escape(k)}(?!\w)", schema), f"{label}: {k} missing from SCHEMA"
