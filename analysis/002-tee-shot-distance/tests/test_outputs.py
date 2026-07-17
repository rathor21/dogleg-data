import json, os, subprocess, sys

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
    for tier in blob["tiers"]:
        assert set(blob["curves"][tier]) == set(blob["clubs"])
        for club in blob["clubs"]:
            grid = blob["curves"][tier][club]
            assert len(grid) == len(blob["holes"])
            assert all(len(row) == len(blob["drives"]) for row in grid)
        assert len(blob["benchmark"][tier]) == len(blob["holes"])
        assert len(blob["cost_line"][tier]) == len(blob["holes"])
        assert set(blob["lies"][tier]) == set(blob["clubs"])
        for club in blob["clubs"]:
            mix = blob["lies"][tier][club]
            assert set(mix) == {"fairway", "rough", "trouble"}
            assert abs(sum(mix.values()) - 1.0) < 1e-6
    assert blob["ob_cost"] == 2.0
    assert os.path.exists(os.path.join(HERE, "outputs", "002_results.csv"))


def test_tool_page_embeds_current_tool_data():
    import re
    page = open(os.path.join(HERE, "..", "..", "site", "tee-shot-distance", "tool.html")).read()
    m = re.search(r'<script type="application/json" id="tool-data">(.*?)</script>', page, re.S)
    assert m, "tool-data blob missing"
    embedded = json.loads(m.group(1))
    with open(os.path.join(HERE, "outputs", "tool_data.json")) as f:
        built = json.load(f)
    assert embedded == built, "tool.html blob is stale; re-embed outputs/tool_data.json"
