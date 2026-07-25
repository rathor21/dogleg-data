"""Build outputs/002_results.csv and outputs/tool_data.json.

tool_data.json contract (consumed by site/tee-shot-distance/tool.html):
  holes:     [280,290,...,500]
  drives:    [140,145,...,320]   (the golfer's DRIVER distance)
  tiers:     {"0": "0-hcp (scratch)", ..., "30": "30-hcp (modeled)"}
  clubs:     {"driver": {"label": "Driver", "dist_ratio": 1.0}, ...}
  benchmark: benchmark[tier][hole_idx] = tier benchmark for the hole
             (MODELED: calibrated model at tier defaults, always evaluated
             at the published default fairway width regardless of the
             width the golfer picks; see model.benchmark_score. A narrow
             fairway therefore reads as strokes lost against a fixed
             goalpost, not a moved one.)
  base:      base[tier][club][hole_idx][drive_idx], gap: same shape, both
             from model.score_components(hole, tier, club, drive_mean=drive)
             ("base"/"gap"), rounded to 4 decimals. Four, not three: the
             width decomposition below compounds rounding across base, gap,
             and the tc terms, and the old single curves grid does not.
  tc_pl/tc_hz: per-tier trouble increments, playable and hazard: tc_pl[tier]
             and tc_hz[tier] from model.score_components. Both depend only
             on tier (MISHIT[tier] and
             TROUBLE_COST[tier]), never on hole/club/drive, so build time
             asserts every club produces the identical value before storing
             it once per tier, rounded to 4 decimals.
  sd_lat:    sd_lat[tier][club] = data.DRIVER[tier]["sd_lat"] *
             data.CLUBS[club]["lat_ratio"], rounded to 3 decimals: the
             lateral dispersion (yd) that width-dependent lie odds are
             computed from for that club.
  mishit:    mishit[tier] = data.MISHIT[tier], the per-tier severe-mishit
             probability (the mishit branch always lands in the rough, per
             model.tee_outcomes, so it is not width-dependent).
  geometry:  {"rough_band": 22, "default_width": 36, "hazard_ref_width": 36,
             "hazard_floor_width": 16}, from data.GEOMETRY and
             data.HAZARD_GEOMETRY (default_width = fairway_half_width * 2,
             the Stagner anchor, anchor F).
  margin:    0.10 (the cost-line margin used)
  ob_cost:   data.OB_COST, strokes charged per out-of-bounds tee shot
  driver_holes_per_round: 14 (display constant, the standard count of
             driving holes on an 18-hole round: 18 holes minus the par 3s
             a golfer doesn't tee off with a driver on)
  modeled:   ["30"]

curves, lies, and cost_line (all present in the pre-rev-3 contract) are
dropped: the tool now recomputes expected score, the lie mix, and the cost
line client-side, at any fairway width the golfer picks, from this
decomposition. The formula, straight out of model.score_components and
model._lie_probs:

    E(W) = base + p_fw(W) * gap + p_tr(W) * ((1-h(W))*tc_pl + h(W)*tc_hz)
    h(W) = 0 at W >= hazard_ref_width, else min(1, (ref - W)/(ref - floor))

where, for lateral sd sd_lat and fairway half-width fw = W / 2:

    p_fw(W) = Phi(fw / sd_lat) - Phi(-fw / sd_lat)
    p_tr(W) = 2 * (1 - Phi((fw + rough_band * min(W/ref, 1)) / sd_lat))

Phi is the standard normal CDF (tool.html implements it via the
Abramowitz-Stegun erf approximation, ~1e-7 accurate, well inside the blob's
4-decimal rounding). The displayed lie mix at width W is
(1 - mishit) * p_fw for fairway and (1 - mishit) * p_tr for trouble, with
rough as the remainder (1 minus the other two): the severe-mishit branch
(probability `mishit`) always lands in the rough regardless of width.

tests/test_outputs.py::test_blob_decomposition_matches_model recomputes E
from base/gap/tc terms/sd_lat with Python's own Phi and checks it against
model.expected_score(..., fairway_width=W) directly, so this contract stays
provably exact, not just internally consistent.
"""
import csv, json, os
import data
from model import score_components, benchmark_score, neutral_distance

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)

HOLES = list(range(280, 501, 10))
DRIVES = list(range(140, 321, 5))

def tier_label(t):
    base = "0-hcp (scratch)" if t == 0 else f"{t}-hcp"
    return base + (" (modeled)" if t in data.MODELED_TIERS else "")

blob = {
    "holes": HOLES,
    "drives": DRIVES,
    "tiers": {str(t): tier_label(t) for t in data.TIERS},
    "clubs": {k: {"label": v["label"], "dist_ratio": v["dist_ratio"]} for k, v in data.CLUBS.items()},
    "benchmark": {}, "base": {}, "gap": {}, "tc_pl": {}, "tc_hz": {}, "sd_lat": {}, "mishit": {},
    "geometry": {
        "rough_band": data.GEOMETRY["rough_band"],
        "default_width": data.GEOMETRY["fairway_half_width"] * 2,
        "hazard_ref_width": data.HAZARD_GEOMETRY["ref_width"],
        "hazard_floor_width": data.HAZARD_GEOMETRY["floor_width"],
    },
    "margin": data.COST_MARGIN,
    "modeled": [str(t) for t in data.MODELED_TIERS],
    "ob_cost": data.OB_COST,
    "driver_holes_per_round": 14,  # standard count of driving holes on an 18-hole round
}
for t in data.TIERS:
    ts = str(t)
    blob["benchmark"][ts] = [round(benchmark_score(h, t), 3) for h in HOLES]
    blob["base"][ts] = {}
    blob["gap"][ts] = {}
    blob["sd_lat"][ts] = {}
    blob["mishit"][ts] = data.MISHIT[t]

    tc_pls = set()
    tc_hzs = set()
    for club in data.CLUBS:
        base_grid = []
        gap_grid = []
        for h in HOLES:
            base_row = []
            gap_row = []
            for dv in DRIVES:
                comp = score_components(h, t, club, drive_mean=float(dv))
                base_row.append(round(comp["base"], 4))
                gap_row.append(round(comp["gap"], 4))
                tc_pls.add(round(comp["tc_pl"], 9))
                tc_hzs.add(round(comp["tc_hz"], 9))
            base_grid.append(base_row)
            gap_grid.append(gap_row)
        blob["base"][ts][club] = base_grid
        blob["gap"][ts][club] = gap_grid
        blob["sd_lat"][ts][club] = round(data.DRIVER[t]["sd_lat"] * data.CLUBS[club]["lat_ratio"], 3)

    assert len(tc_pls) == 1 and len(tc_hzs) == 1, f"tc terms differ across club/hole/drive for tier {t}"
    blob["tc_pl"][ts] = round(tc_pls.pop(), 4)
    blob["tc_hz"][ts] = round(tc_hzs.pop(), 4)

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
