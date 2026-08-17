"""Build outputs/003_results.csv: the canonical aim-verdict numbers table.

One row per (tier, pin, wind) combination -- 5 tiers x 3 pins x 2 wind
scenarios = 30 rows -- each carrying the optimizer's full verdict: the
optimal aim (lateral offset and carry/club adjustment from the pin, both
signed yards), the expected score there, the expected score aiming directly
at the pin, the expected score of the center-of-green bailout, the strokes
saved by moving off the pin, the qualitative attack/bail label (see
optimizer.verdict_label), and whether that verdict landed on the search's
club-adjustment budget cap rather than an interior optimum (see
optimizer.hit_search_boundary and optimizer.py's module docstring for why
that happens and what it means).

This is the single source the article and charts quote, the 003 analogue of
analysis/002-tee-shot-distance/outputs/002_results.csv (same cross-release
rule from CONTEXT.md/the spec: any number quoted elsewhere must match this
CSV exactly). Every row runs at optimizer.VERDICT_N_GRID (121), the
elevated integration resolution test_optimizer.py checks for stability
against n_grid=81.
"""
import csv
import os

import data
import optimizer

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)

FIELDNAMES = [
    "tier", "pin", "wind",
    "aim_lateral_offset_yd", "aim_carry_adjustment_yd",
    "score_optimum", "score_at_pin", "score_center_aim",
    "delta_vs_at_pin_strokes",
    "verdict_label", "hit_search_boundary",
]


def build_rows(n_grid=optimizer.VERDICT_N_GRID):
    rows = []
    for tier in data.TIERS:
        for pin in data.PINS:
            for wind in (False, True):
                v = optimizer.optimize_aim(tier, pin, wind, n_grid=n_grid)
                center_s = optimizer.center_aim_score(tier, pin, wind, n_grid=n_grid)
                rows.append({
                    "tier": tier,
                    "pin": pin,
                    "wind": wind,
                    "aim_lateral_offset_yd": round(v.lateral_offset_yd, 3),
                    "aim_carry_adjustment_yd": round(v.carry_adjustment_yd, 3),
                    "score_optimum": round(v.score_optimum, 4),
                    "score_at_pin": round(v.score_at_pin, 4),
                    "score_center_aim": round(center_s, 4),
                    "delta_vs_at_pin_strokes": round(v.delta, 4),
                    "verdict_label": optimizer.verdict_label(v),
                    "hit_search_boundary": optimizer.hit_search_boundary(v),
                })
    return rows


if __name__ == "__main__":
    rows = build_rows()
    out_path = os.path.join(OUT, "003_results.csv")
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("wrote", out_path, f"({len(rows)} rows)")

    boundary_rows = [r for r in rows if r["hit_search_boundary"]]
    if boundary_rows:
        print(f"\n{len(boundary_rows)} row(s) hit the search boundary "
              "(bounded best-within-budget, not a converged interior optimum "
              "-- see optimizer.py's module docstring):")
        for r in boundary_rows:
            print(f"  tier={r['tier']} pin={r['pin']} wind={r['wind']} "
                  f"lateral={r['aim_lateral_offset_yd']} carry={r['aim_carry_adjustment_yd']}")
