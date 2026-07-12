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
    assert os.path.exists(os.path.join(HERE, "outputs", "002_results.csv"))
