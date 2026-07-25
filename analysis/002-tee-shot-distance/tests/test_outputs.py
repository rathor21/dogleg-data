import json, math, os, subprocess, sys

from model import expected_score

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_build_outputs_writes_valid_tool_json():
    subprocess.run([sys.executable, os.path.join(HERE, "build_outputs.py")], check=True, cwd=HERE)
    with open(os.path.join(HERE, "outputs", "tool_data.json")) as f:
        blob = json.load(f)
    assert blob["holes"] == list(range(280, 501, 10))
    assert blob["drives"] == list(range(140, 321, 5))
    assert set(blob["tiers"]) == {"0", "5", "10", "15", "20", "25", "30"}
    assert blob["modeled"] == ["30"]
    assert blob["margin"] == 0.10
    assert blob["geometry"] == {"rough_band": 22, "default_width": 36, "hazard_ref_width": 36.0, "hazard_floor_width": 16.0}
    for tier in blob["tiers"]:
        assert set(blob["base"][tier]) == set(blob["clubs"])
        assert set(blob["gap"][tier]) == set(blob["clubs"])
        for club in blob["clubs"]:
            base_grid = blob["base"][tier][club]
            gap_grid = blob["gap"][tier][club]
            assert len(base_grid) == len(blob["holes"])
            assert len(gap_grid) == len(blob["holes"])
            assert all(len(row) == len(blob["drives"]) for row in base_grid)
            assert all(len(row) == len(blob["drives"]) for row in gap_grid)
        assert len(blob["benchmark"][tier]) == len(blob["holes"])
        assert set(blob["sd_lat"][tier]) == set(blob["clubs"])
        assert isinstance(blob["tc_pl"][tier], float)
        assert isinstance(blob["tc_hz"][tier], float)
        assert blob["tc_hz"][tier] > blob["tc_pl"][tier]
        assert isinstance(blob["mishit"][tier], float)
    assert blob["ob_cost"] == 2.0
    assert os.path.exists(os.path.join(HERE, "outputs", "002_results.csv"))


def _phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def test_blob_decomposition_matches_model():
    with open(os.path.join(HERE, "outputs", "tool_data.json")) as f:
        blob = json.load(f)
    rough_band = blob["geometry"]["rough_band"]
    ref = blob["geometry"]["hazard_ref_width"]
    floor = blob["geometry"]["hazard_floor_width"]
    hole_idx = {h: i for i, h in enumerate(blob["holes"])}
    drive_idx = {d: i for i, d in enumerate(blob["drives"])}

    for tier in (0, 15, 30):
        ts = str(tier)
        tc_pl = blob["tc_pl"][ts]
        tc_hz = blob["tc_hz"][ts]
        for club in ("driver", "seven_iron"):
            sd_lat = blob["sd_lat"][ts][club]
            for hole in (280, 400, 500):
                hi = hole_idx[hole]
                for drive in (140, 220, 320):
                    di = drive_idx[drive]
                    base = blob["base"][ts][club][hi][di]
                    gap = blob["gap"][ts][club][hi][di]
                    for W in (25, 36, 48):
                        fw = W / 2.0
                        p_fw = _phi(fw / sd_lat) - _phi(-fw / sd_lat)
                        band_scale = min(W / ref, 1.0)
                        p_tr = 2.0 * (1.0 - _phi((fw + rough_band * band_scale) / sd_lat))
                        h = 0.0 if W >= ref else min(1.0, (ref - W) / (ref - floor))
                        e_blob = base + p_fw * gap + p_tr * ((1.0 - h) * tc_pl + h * tc_hz)
                        e_model = expected_score(
                            hole, tier, club, drive_mean=float(drive), fairway_width=W
                        )
                        assert abs(e_blob - e_model) < 0.005, (
                            tier, club, hole, drive, W, e_blob, e_model
                        )


def test_tool_page_embeds_current_tool_data():
    import re
    page = open(os.path.join(HERE, "..", "..", "site", "tee-shot-distance", "tool.html")).read()
    m = re.search(r'<script type="application/json" id="tool-data">(.*?)</script>', page, re.S)
    assert m, "tool-data blob missing"
    embedded = json.loads(m.group(1))
    with open(os.path.join(HERE, "outputs", "tool_data.json")) as f:
        built = json.load(f)
    assert embedded == built, "tool.html blob is stale; re-embed outputs/tool_data.json"
