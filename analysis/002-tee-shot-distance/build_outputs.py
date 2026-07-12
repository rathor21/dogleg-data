"""Build outputs/002_results.csv and outputs/tool_data.json.

tool_data.json contract (consumed by site/tee-shot-distance/tool.html):
  holes:     [280,290,...,500]
  drives:    [140,145,...,320]   (the golfer's DRIVER distance)
  tiers:     {"0": "0-hcp (scratch)", ..., "30": "30-hcp (modeled)"}
  clubs:     {"driver": {"label": "Driver", "dist_ratio": 1.0}, ...}
  curves:    curves[tier][club][hole_idx][drive_idx] = expected strokes when a
             golfer whose DRIVER goes drives[drive_idx] hits club
  benchmark: benchmark[tier][hole_idx] = tier benchmark for the hole
             (MODELED: calibrated model at tier defaults, see model.benchmark_score)
  cost_line: cost_line[tier][hole_idx] = the 0.10-margin cost line drive
             distance for the hole, or null when no threshold exists
  margin:    0.10 (the cost-line margin used)
  modeled:   ["30"]
"""
import csv, json, os
import data
from model import expected_score, benchmark_score, neutral_distance

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)

HOLES = list(range(280, 501, 10))
DRIVES = list(range(140, 321, 5))

def tier_label(t):
    base = "0-hcp (scratch)" if t == 0 else f"{t}-hcp"
    return base + (" (modeled)" if t in data.MODELED_TIERS else "")

def _cost_line_yd(r):
    return None if r["threshold"] is None else round(r["threshold"], 1)

blob = {
    "holes": HOLES,
    "drives": DRIVES,
    "tiers": {str(t): tier_label(t) for t in data.TIERS},
    "clubs": {k: {"label": v["label"], "dist_ratio": v["dist_ratio"]} for k, v in data.CLUBS.items()},
    "curves": {}, "benchmark": {}, "cost_line": {},
    "margin": data.COST_MARGIN,
    "modeled": [str(t) for t in data.MODELED_TIERS],
}
for t in data.TIERS:
    blob["benchmark"][str(t)] = [round(benchmark_score(h, t), 3) for h in HOLES]
    blob["cost_line"][str(t)] = [_cost_line_yd(neutral_distance(h, t)) for h in HOLES]
    blob["curves"][str(t)] = {}
    for club in data.CLUBS:
        blob["curves"][str(t)][club] = [
            [round(expected_score(h, t, club, drive_mean=float(dv)), 3) for dv in DRIVES]
            for h in HOLES
        ]
with open(os.path.join(OUT, "tool_data.json"), "w") as f:
    json.dump(blob, f, separators=(",", ":"))

with open(os.path.join(OUT, "002_results.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["tier", "hole_yards", "benchmark", "cost_line_margin", "cost_line_yd",
                "always_at_benchmark", "never_at_benchmark"])
    for t in data.TIERS:
        for h in HOLES:
            r = neutral_distance(h, t)
            w.writerow([t, h, round(benchmark_score(h, t), 3), data.COST_MARGIN,
                        "" if r["threshold"] is None else round(r["threshold"], 1),
                        r["always_at_benchmark"], r["never_at_benchmark"]])

print("wrote", OUT)
for t in (10, 15, 20):
    r = neutral_distance(400, t)
    print(f"cost line, 400yd par 4, {t}-hcp:", r)
