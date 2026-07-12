# Release 002 "How Far Do You Need to Hit It?" Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Dogleg Data release 002: the analysis of how far you need to hit your tee shot for zero strokes gained against your own handicap tier, with the approach shot priced in, plus five charts, a par-4 calculator tool page, caption, peer review doc, and /cite exports. Ship date Monday, July 20, 2026.

**Architecture:** A small Python package at `analysis/002-tee-shot-distance/` holds gate-verified data anchors (`data.py`), an analytic expected-strokes model (`model.py`), a Monte Carlo validation harness (`montecarlo.py`), an output builder that exports the tool's JSON and a results CSV, and five chart scripts. The site gets `site/tee-shot-distance/` with an article page and a self-contained Chart.js tool page following the `site/fairway-vs-rough/` pattern. Spec: [2026-07-11-002-tee-shot-distance-design.md](2026-07-11-002-tee-shot-distance-design.md).

**Tech Stack:** Python 3 (numpy, matplotlib, pytest), vanilla JS + Chart.js 4 (CDN, same pinned version as the existing dashboard), static HTML matching existing site pages.

**Two facts every task must respect:**

1. **Numbers in this plan are provisional.** Every anchor value shown in `data.py` below is a placeholder from memory or from 001. Task 2 (the verification gate) produces `docs/sources/002_Source_Log.md` with the real published values, and Task 3 copies values from that log, never from this plan. Tests assert structure and internal consistency, never the provisional values.
2. **Published vs modeled labeling is a standing rule.** Tier 30 is always modeled. Any interpolated curve is modeled. Every chart, caption, table, and tool label that shows a modeled number carries the label. Copy the `badge-modeled` / starred-value conventions from `site/fairway-vs-rough/dashboard.html` and `brand/percentages_card_gen.py`.

**Reference files to study before starting any task:**

- `site/fairway-vs-rough/dashboard.html` (tool page pattern: CSS tokens, tabs, controls, JSON blob, Chart.js config)
- `site/fairway-vs-rough/index.html` (article page pattern)
- `/Users/sunny/Documents/Claude/Projects/Golf Agent/Fairway_vs_Rough_Post/source/` (001's `model.py`, `data.py`, `style.py`, `chart1.py`..`chart5.py`; read-only reference, do not modify)
- `docs/sources/Peer_Review_Fairway_vs_Rough.md` (peer review format)

---

### Task 1: Scaffold the analysis package

**Files:**
- Create: `analysis/002-tee-shot-distance/requirements.txt`
- Create: `analysis/002-tee-shot-distance/README.md`
- Create: `analysis/002-tee-shot-distance/tests/__init__.py` (empty)
- Create: `analysis/002-tee-shot-distance/conftest.py` (empty, makes pytest resolve the package dir)

- [ ] **Step 1: Create the directory and requirements**

`analysis/002-tee-shot-distance/requirements.txt`:

```
numpy>=1.26
matplotlib>=3.8
pytest>=8.0
```

- [ ] **Step 2: Write the README**

`analysis/002-tee-shot-distance/README.md`:

```markdown
# 002 — How Far Do You Need to Hit It?

Analysis package for Dogleg Data release 002. Spec:
docs/plans/2026-07-11-002-tee-shot-distance-design.md

## Order of operations
1. `docs/sources/002_Source_Log.md` is the verification gate. `data.py`
   values come from that log only.
2. `pytest` from this directory runs all model and consistency tests.
3. `python build_outputs.py` writes `outputs/002_results.csv` and
   `outputs/tool_data.json`.
4. `python chart1.py` .. `python chart5.py` write PNGs to `outputs/`
   (site copies happen in the site tasks).

## Modeling stance
Own-tier baseline: strokes gained 0 = you played the hole like a typical
golfer at your handicap. Full-hole expected strokes, drive dispersion ->
lie odds -> approach expected strokes to hole-out. Tier 30 and all
between-anchor interpolation are MODELED and labeled.
```

- [ ] **Step 3: Create empty test scaffolding and verify pytest runs**

Create empty `analysis/002-tee-shot-distance/tests/__init__.py` and empty `analysis/002-tee-shot-distance/conftest.py`.

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest`
Expected: `no tests ran` (exit code 5 is fine at this stage)

- [ ] **Step 4: Commit**

```bash
git add analysis/002-tee-shot-distance
git commit -m "002: scaffold analysis package"
```

---

### Task 2: Verification gate, the source hunt

**Files:**
- Create: `docs/sources/002_Source_Log.md`

This task is research, not code. Use web search and page fetches. The gate is a standing rule: no charts, no `data.py` values, until this log exists with URLs and retrieval dates.

- [ ] **Step 1: Hunt each required anchor**

For each row below, find the primary published source, record the exact URL, retrieval date (2026-07-XX), and the actual table values into `docs/sources/002_Source_Log.md`. Where a value cannot be found at the stated resolution, record FAILED with what was found instead.

| # | Anchor | Primary target | Fallback |
|---|---|---|---|
| A | Driving distance by handicap band (0/5/10/15/20/25) | Shot Scope benchmark pages | Arccos/Lou Stagner published distance tables |
| B | Driver lateral dispersion by handicap | Stagner/Arccos dispersion posts; GOLFTEC data as used in 001 | 001 source log values, reused and cited |
| C | Club distances relative to driver (3-wood, hybrid, mid-iron) by handicap | Shot Scope club benchmark pages | Arccos club averages; TrackMan amateur tables |
| D | Expected strokes to hole out by distance and lie (fairway/rough) for amateurs, ideally by band | Broadie 2011 / Every Shot Counts amateur tables | Shot Scope SG ebook baselines; Stagner newsletter tables |
| E | Average par-4 score by hole length by handicap (the benchmark) | Stagner newsletter (Arccos par-4 scoring by length) | Shot Scope average-score benchmarks; if only aggregate exists, benchmark becomes model-calibrated and the log says so |
| F | Fairway-width and penalty-frequency context | 001 landing model assumptions (reuse) | none needed |

- [ ] **Step 2: Make the reframe decision**

The spec pre-approves this: if anchor C fails at handicap resolution, the release reframes from "club verdict" to "distance threshold" and clubs become labeled distance bands (driver-length, wood-length, hybrid-length, iron-length, defined as ratios of the golfer's driver distance, labeled modeled). Record the decision in the log under a `## Gate decision` heading: CLUB VERDICT or DISTANCE BANDS, with one paragraph of reasoning.

- [ ] **Step 3: Structure the log**

`docs/sources/002_Source_Log.md` must have: one `## Anchor X` section per row above with URL(s), retrieval date, the pulled values as a markdown table, and a PUBLISHED/MODELED note; the `## Gate decision` section; a `## Benchmark decision` section stating whether anchor E gave an external benchmark at (band, length) resolution or the fallback calibration path is in play.

- [ ] **Step 4: Commit**

```bash
git add docs/sources/002_Source_Log.md
git commit -m "002: verification gate source log"
```

---

### Task 3: data.py, anchors from the source log

**Files:**
- Create: `analysis/002-tee-shot-distance/data.py`
- Create: `analysis/002-tee-shot-distance/tests/test_data.py`

**Every numeric literal in `data.py` must come from `docs/sources/002_Source_Log.md`, with the anchor letter cited in a comment.** The values below define the SCHEMA and show plausible provisional magnitudes only.

- [ ] **Step 1: Write the failing tests**

`analysis/002-tee-shot-distance/tests/test_data.py`:

```python
import data

def test_tiers_declared():
    assert data.PUBLISHED_TIERS == [0, 5, 10, 15, 20, 25]
    assert data.MODELED_TIERS == [30]
    assert data.TIERS == data.PUBLISHED_TIERS + data.MODELED_TIERS

def test_driver_table_monotonic():
    means = [data.DRIVER[t]["mean"] for t in data.TIERS]
    assert all(a > b for a, b in zip(means, means[1:])), "driver distance must fall as handicap rises"
    lats = [data.DRIVER[t]["sd_lat"] for t in data.TIERS]
    assert all(a <= b for a, b in zip(lats, lats[1:])), "lateral dispersion must not shrink as handicap rises"

def test_club_ratios_ordered():
    r = data.CLUBS
    assert r["driver"]["dist_ratio"] == 1.0
    assert 1.0 > r["wood"]["dist_ratio"] > r["hybrid"]["dist_ratio"] > r["iron"]["dist_ratio"] > 0.5
    for club in r.values():
        assert 0.4 <= club["lat_ratio"] <= 1.0

def test_holeout_tables_well_formed():
    for tier in data.TIERS:
        for lie in ("fairway", "rough"):
            table = data.E_HOLEOUT[tier][lie]
            xs = [p[0] for p in table]
            ys = [p[1] for p in table]
            assert xs == sorted(xs) and len(xs) >= 4
            assert all(a <= b for a, b in zip(ys, ys[1:])), "strokes to hole out must not fall with distance"

def test_rough_costs_more_at_anchors():
    for tier in data.TIERS:
        fair = dict(data.E_HOLEOUT[tier]["fairway"])
        rough = dict(data.E_HOLEOUT[tier]["rough"])
        for d in set(fair) & set(rough):
            assert rough[d] > fair[d]

def test_benchmark_tables_well_formed():
    for tier in data.TIERS:
        table = data.BENCHMARK_PAR4[tier]
        xs = [p[0] for p in table]
        ys = [p[1] for p in table]
        assert xs == sorted(xs) and len(xs) >= 3
        assert all(a < b for a, b in zip(ys, ys[1:])), "longer par 4s must average higher scores"

def test_every_anchor_carries_source():
    assert isinstance(data.SOURCES, dict)
    for key in ("DRIVER", "CLUBS", "E_HOLEOUT", "BENCHMARK_PAR4", "GEOMETRY", "MISHIT", "TROUBLE_COST"):
        assert key in data.SOURCES and "002_Source_Log.md" in data.SOURCES[key]["log"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest tests/test_data.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'data'`

- [ ] **Step 3: Write data.py**

Schema (values are PROVISIONAL, replace every number from the source log):

```python
"""Gate-verified anchors for release 002.

EVERY numeric literal here comes from docs/sources/002_Source_Log.md.
Anchor letters (A..F) refer to that log's sections. PROVISIONAL values
must not survive Task 3 review.
"""

PUBLISHED_TIERS = [0, 5, 10, 15, 20, 25]
MODELED_TIERS = [30]          # least-squares extrapolation across all published bands
TIERS = PUBLISHED_TIERS + MODELED_TIERS

# Anchor A + B. mean carry-plus-roll driver distance (yd), distance sd as a
# fraction of mean, lateral sd (yd) at driver range.
DRIVER = {
    0:  {"mean": 251, "sd_dist_frac": 0.055, "sd_lat": 19},
    5:  {"mean": 240, "sd_dist_frac": 0.060, "sd_lat": 22},
    10: {"mean": 230, "sd_dist_frac": 0.065, "sd_lat": 25},
    15: {"mean": 220, "sd_dist_frac": 0.070, "sd_lat": 28},
    20: {"mean": 209, "sd_dist_frac": 0.075, "sd_lat": 31},
    25: {"mean": 198, "sd_dist_frac": 0.080, "sd_lat": 34},
    30: {"mean": 188, "sd_dist_frac": 0.085, "sd_lat": 37},  # MODELED
}

# Anchor C. distance and dispersion ratios vs driver. If the gate decision is
# DISTANCE BANDS, keep the same structure; the labels become band names.
CLUBS = {
    "driver": {"dist_ratio": 1.00, "lat_ratio": 1.00, "label": "Driver"},
    "wood":   {"dist_ratio": 0.92, "lat_ratio": 0.85, "label": "3-wood"},
    "hybrid": {"dist_ratio": 0.84, "lat_ratio": 0.75, "label": "Hybrid"},
    "iron":   {"dist_ratio": 0.74, "lat_ratio": 0.65, "label": "Mid-iron"},
}

# Anchor D. expected strokes to hole out: {tier: {lie: [(yd, strokes), ...]}}
# Anchors at published distance points; model.py interpolates between them
# (interpolation = MODELED).
E_HOLEOUT = {
    0:  {"fairway": [(30, 2.55), (75, 2.75), (125, 2.95), (175, 3.25), (225, 3.70)],
         "rough":   [(30, 2.75), (75, 3.00), (125, 3.25), (175, 3.60), (225, 4.10)]},
    # ... one entry per tier in TIERS, same distance grid ...
    30: {"fairway": [(30, 3.30), (75, 3.60), (125, 3.95), (175, 4.45), (225, 5.05)],   # MODELED
         "rough":   [(30, 3.55), (75, 3.95), (125, 4.40), (175, 4.95), (225, 5.65)]},  # MODELED
}

# Anchor E. average par-4 score by hole length: {tier: [(yd, score), ...]}
BENCHMARK_PAR4 = {
    0:  [(320, 3.95), (380, 4.15), (440, 4.40)],
    # ... per tier ...
    30: [(320, 5.35), (380, 5.75), (440, 6.20)],  # MODELED
}

# Anchor F (reused 001 landing assumptions). Yards.
GEOMETRY = {"fairway_half_width": 16, "rough_band": 22}

# MODELED with stated ranges; peer-review sensitivity axes.
# p: probability of a severe mishit off the tee (topped/fat), carry_frac: its carry.
MISHIT = {0: 0.01, 5: 0.02, 10: 0.03, 15: 0.05, 20: 0.07, 25: 0.09, 30: 0.11,
          "carry_frac": 0.45, "sensitivity_p": (0.5, 1.5)}
# strokes added on top of the rough hole-out when the tee ball reaches trouble
# (penalty, trees, recovery). Sensitivity range 0.5 to 1.5.
TROUBLE_COST = {0: 0.55, 5: 0.60, 10: 0.65, 15: 0.70, 20: 0.75, 25: 0.80, 30: 0.85}

SOURCES = {
    "DRIVER":         {"log": "docs/sources/002_Source_Log.md#anchor-a", "status": "published"},
    "CLUBS":          {"log": "docs/sources/002_Source_Log.md#anchor-c", "status": "published-or-modeled-per-gate"},
    "E_HOLEOUT":      {"log": "docs/sources/002_Source_Log.md#anchor-d", "status": "published-anchors-modeled-interp"},
    "BENCHMARK_PAR4": {"log": "docs/sources/002_Source_Log.md#anchor-e", "status": "published-or-calibrated-per-gate"},
    "GEOMETRY":       {"log": "docs/sources/002_Source_Log.md#anchor-f", "status": "reused-001"},
    "MISHIT":         {"log": "docs/sources/002_Source_Log.md#anchor-f", "status": "modeled"},
    "TROUBLE_COST":   {"log": "docs/sources/002_Source_Log.md#anchor-f", "status": "modeled"},
}
```

Fill EVERY tier (0, 5, 10, 15, 20, 25, 30) in `E_HOLEOUT` and `BENCHMARK_PAR4`. Tier 30 rows are least-squares extrapolations across the six published bands (fit a line per column across tiers, evaluate at 30), never a single last delta.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest tests/test_data.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add analysis/002-tee-shot-distance/data.py analysis/002-tee-shot-distance/tests/test_data.py
git commit -m "002: gate-verified data anchors"
```

---

### Task 4: strokes_to_holeout (model part 1)

**Files:**
- Create: `analysis/002-tee-shot-distance/model.py`
- Create: `analysis/002-tee-shot-distance/tests/test_model.py`

- [ ] **Step 1: Write the failing tests**

`analysis/002-tee-shot-distance/tests/test_model.py`:

```python
import numpy as np
import data
from model import strokes_to_holeout

def test_holeout_monotonic_in_distance():
    for tier in data.TIERS:
        for lie in ("fairway", "rough"):
            grid = np.arange(20, 261, 5)
            vals = [strokes_to_holeout(d, lie, tier) for d in grid]
            assert all(a <= b + 1e-9 for a, b in zip(vals, vals[1:])), (tier, lie)

def test_holeout_rough_worse_than_fairway():
    for tier in data.TIERS:
        for d in (40, 90, 140, 190, 240):
            assert strokes_to_holeout(d, "rough", tier) > strokes_to_holeout(d, "fairway", tier)

def test_holeout_worse_tier_worse_everywhere():
    for lie in ("fairway", "rough"):
        for d in (40, 90, 140, 190):
            vals = [strokes_to_holeout(d, lie, t) for t in data.TIERS]
            assert all(a <= b + 1e-9 for a, b in zip(vals, vals[1:])), (lie, d)

def test_holeout_hits_anchors_exactly():
    for tier in data.TIERS:
        for lie in ("fairway", "rough"):
            for d, s in data.E_HOLEOUT[tier][lie]:
                assert abs(strokes_to_holeout(d, lie, tier) - s) < 1e-9

def test_holeout_extends_beyond_last_anchor():
    tier = 20
    last_d, last_s = data.E_HOLEOUT[tier]["fairway"][-1]
    assert strokes_to_holeout(last_d + 40, "fairway", tier) > last_s
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest tests/test_model.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'model'`

- [ ] **Step 3: Implement**

Top of `analysis/002-tee-shot-distance/model.py`:

```python
"""Analytic expected-strokes model for release 002.

Own-tier baseline. All interpolation between published anchors is MODELED.
"""
import numpy as np
import data

def strokes_to_holeout(dist, lie, tier):
    """Expected strokes to hole out from dist yards, given lie, for tier.

    Linear interpolation on the gate-verified anchor table. Below the first
    anchor: clamp to the first anchor value. Above the last anchor: extend
    the last segment's slope (long-leftover extrapolation, MODELED).
    """
    table = data.E_HOLEOUT[tier][lie]
    xs = np.array([p[0] for p in table], dtype=float)
    ys = np.array([p[1] for p in table], dtype=float)
    if dist <= xs[0]:
        return float(ys[0])
    if dist >= xs[-1]:
        slope = (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
        return float(ys[-1] + slope * (dist - xs[-1]))
    return float(np.interp(dist, xs, ys))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest tests/test_model.py -v`
Expected: all PASS. If `test_holeout_worse_tier_worse_everywhere` fails, the data tables cross between tiers; fix `data.py` values against the source log rather than loosening the test.

- [ ] **Step 5: Commit**

```bash
git add analysis/002-tee-shot-distance/model.py analysis/002-tee-shot-distance/tests/test_model.py
git commit -m "002: strokes-to-holeout curves"
```

---

### Task 5: Tee-shot outcome model (model part 2)

**Files:**
- Modify: `analysis/002-tee-shot-distance/model.py`
- Modify: `analysis/002-tee-shot-distance/tests/test_model.py`

- [ ] **Step 1: Write the failing tests (append to test_model.py)**

```python
from model import tee_outcomes

def test_tee_outcomes_probabilities_sum_to_one():
    for tier in data.TIERS:
        carries, weights, lies = tee_outcomes("driver", tier)
        assert abs(weights.sum() - 1.0) < 1e-9
        for lp in lies:
            assert abs(lp["fairway"] + lp["rough"] + lp["trouble"] - 1.0) < 1e-9

def test_tee_outcomes_mean_near_input():
    carries, weights, _ = tee_outcomes("driver", 15, drive_mean=250)
    mean = float((carries * weights).sum())
    # mishit branch drags the mean below the clean-strike mean
    assert 250 * 0.90 < mean < 250

def test_shorter_club_finds_more_fairways():
    _, wd, ld = tee_outcomes("driver", 20)
    _, wi, li = tee_outcomes("iron", 20)
    p_fw_driver = float(sum(w * lp["fairway"] for w, lp in zip(wd, ld)))
    p_fw_iron = float(sum(w * lp["fairway"] for w, lp in zip(wi, li)))
    assert p_fw_iron > p_fw_driver

def test_better_tier_finds_more_fairways():
    def p_fw(tier):
        _, w, l = tee_outcomes("driver", tier)
        return float(sum(wi * lp["fairway"] for wi, lp in zip(w, l)))
    assert p_fw(0) > p_fw(15) > p_fw(30)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest tests/test_model.py -v -k tee_outcomes or fairways`
Expected: FAIL with `ImportError: cannot import name 'tee_outcomes'`

- [ ] **Step 3: Implement (append to model.py)**

```python
from math import erf, sqrt

_NODES, _WEIGHTS = np.polynomial.hermite_e.hermegauss(15)
_WEIGHTS = _WEIGHTS / _WEIGHTS.sum()

def _phi(z):
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))

def _lie_probs(sd_lat):
    """P(fairway/rough/trouble) from lateral dispersion vs hole geometry."""
    fw = data.GEOMETRY["fairway_half_width"]
    edge = fw + data.GEOMETRY["rough_band"]
    p_fw = _phi(fw / sd_lat) - _phi(-fw / sd_lat)
    p_trouble = 2.0 * (1.0 - _phi(edge / sd_lat))
    return {"fairway": p_fw, "rough": 1.0 - p_fw - p_trouble, "trouble": p_trouble}

def tee_outcomes(club, tier, drive_mean=None):
    """Discretized tee-shot outcome distribution for one swing.

    Returns (carries, weights, lie_probs_per_node). The distribution is a
    mixture: clean strike (gauss quadrature over the distance sd) plus a
    tier-specific severe-mishit branch that lands in the rough at
    MISHIT carry_frac of the intended distance.
    """
    c = data.CLUBS[club]
    base = drive_mean if drive_mean is not None else data.DRIVER[tier]["mean"]
    mean = base * c["dist_ratio"]
    sd_d = mean * data.DRIVER[tier]["sd_dist_frac"]
    sd_lat = data.DRIVER[tier]["sd_lat"] * c["lat_ratio"]
    p_miss = data.MISHIT[tier]

    clean_carries = mean + sd_d * _NODES
    clean_weights = _WEIGHTS * (1.0 - p_miss)
    clean_lie = _lie_probs(sd_lat)

    carries = np.append(clean_carries, mean * data.MISHIT["carry_frac"])
    weights = np.append(clean_weights, p_miss)
    lies = [clean_lie] * len(clean_carries) + [{"fairway": 0.0, "rough": 1.0, "trouble": 0.0}]
    return carries, weights, lies
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest tests/test_model.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add analysis/002-tee-shot-distance/model.py analysis/002-tee-shot-distance/tests/test_model.py
git commit -m "002: tee-shot outcome distribution"
```

---

### Task 6: Expected score, benchmark, neutral distance, club verdict (model part 3)

**Files:**
- Modify: `analysis/002-tee-shot-distance/model.py`
- Modify: `analysis/002-tee-shot-distance/tests/test_model.py`

- [ ] **Step 1: Write the failing tests (append to test_model.py)**

```python
from model import expected_score, benchmark_score, neutral_distance, club_verdict

def test_expected_score_reasonable_range():
    for tier in data.TIERS:
        s = expected_score(400, tier)
        assert 3.5 < s < 7.5, (tier, s)

def test_expected_score_falls_with_more_distance():
    # holding dispersion at tier level, more carry must not hurt on a long par 4
    scores = [expected_score(430, 20, drive_mean=d) for d in (160, 200, 240, 280)]
    assert all(a >= b - 1e-6 for a, b in zip(scores, scores[1:]))

def test_benchmark_interpolates_and_orders():
    for tier in data.TIERS:
        assert benchmark_score(340, tier) < benchmark_score(430, tier)
    vals = [benchmark_score(400, t) for t in data.TIERS]
    assert all(a < b for a, b in zip(vals, vals[1:]))

def test_neutral_distance_shape():
    res = neutral_distance(400, 15)
    assert set(res) == {"threshold", "always_at_benchmark", "never_at_benchmark"}
    if res["threshold"] is not None:
        assert 140 <= res["threshold"] <= 320
        assert not res["always_at_benchmark"] and not res["never_at_benchmark"]

def test_neutral_distance_monotonic_in_hole_length():
    # thresholds, where they exist, must not fall as the hole gets longer
    ths = []
    for L in (340, 380, 420, 460):
        r = neutral_distance(L, 15)
        if r["threshold"] is not None:
            ths.append(r["threshold"])
    assert len(ths) >= 2
    assert all(a <= b + 2.0 for a, b in zip(ths, ths[1:]))

def test_short_hole_edge_case():
    # a short par 4 for a scratch golfer should tend toward always-at-benchmark
    r = neutral_distance(300, 0)
    assert r["threshold"] is None or r["threshold"] <= 220

def test_club_verdict_returns_known_club():
    v = club_verdict(400, 15)
    assert v["best"] in data.CLUBS
    assert set(v["scores"]) == set(data.CLUBS)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest tests/test_model.py -v`
Expected: FAIL with `ImportError: cannot import name 'expected_score'`

- [ ] **Step 3: Implement (append to model.py)**

```python
DRIVE_GRID = np.arange(140, 321, 2)

def expected_score(hole_yards, tier, club="driver", drive_mean=None):
    """Full-hole expected strokes on a par 4 of hole_yards for tier."""
    carries, weights, lies = tee_outcomes(club, tier, drive_mean)
    total = 1.0  # the tee stroke
    for carry, w, lp in zip(carries, weights, lies):
        leftover = max(hole_yards - carry, 8.0)
        e_fair = strokes_to_holeout(leftover, "fairway", tier)
        e_rough = strokes_to_holeout(leftover, "rough", tier)
        e_trouble = e_rough + data.TROUBLE_COST[tier]
        total += w * (lp["fairway"] * e_fair + lp["rough"] * e_rough + lp["trouble"] * e_trouble)
    return float(total)

def benchmark_score(hole_yards, tier):
    """Published average score on a par 4 of this length at this tier (anchor E)."""
    table = data.BENCHMARK_PAR4[tier]
    xs = np.array([p[0] for p in table], dtype=float)
    ys = np.array([p[1] for p in table], dtype=float)
    if hole_yards <= xs[0]:
        slope = (ys[1] - ys[0]) / (xs[1] - xs[0])
        return float(ys[0] + slope * (hole_yards - xs[0]))
    if hole_yards >= xs[-1]:
        slope = (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
        return float(ys[-1] + slope * (hole_yards - xs[-1]))
    return float(np.interp(hole_yards, xs, ys))

def neutral_distance(hole_yards, tier, club="driver"):
    """The drive distance where expected score crosses the tier benchmark.

    Returns {"threshold": yd or None, "always_at_benchmark": bool,
             "never_at_benchmark": bool}. Spec edge cases: a short hole can sit
    at-or-under benchmark across the whole grid (threshold None, always True);
    a brutal hole can never reach benchmark on distance alone (threshold None,
    never True).
    """
    bench = benchmark_score(hole_yards, tier)
    scores = np.array([expected_score(hole_yards, tier, club, d) for d in DRIVE_GRID])
    at_or_under = scores <= bench
    if at_or_under.all():
        return {"threshold": None, "always_at_benchmark": True, "never_at_benchmark": False}
    if not at_or_under.any():
        return {"threshold": None, "always_at_benchmark": False, "never_at_benchmark": True}
    i = int(np.argmax(at_or_under))
    x0, x1 = DRIVE_GRID[i - 1], DRIVE_GRID[i]
    y0, y1 = scores[i - 1], scores[i]
    t = x0 + (y0 - bench) * (x1 - x0) / (y0 - y1)
    return {"threshold": float(t), "always_at_benchmark": False, "never_at_benchmark": False}

def club_verdict(hole_yards, tier, drive_mean=None):
    """Expected score per club at this golfer's distances; best = lowest."""
    scores = {club: expected_score(hole_yards, tier, club, drive_mean) for club in data.CLUBS}
    best = min(scores, key=scores.get)
    return {"best": best, "scores": scores}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest tests/test_model.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add analysis/002-tee-shot-distance/model.py analysis/002-tee-shot-distance/tests/test_model.py
git commit -m "002: expected score, benchmark, neutral distance, club verdict"
```

---

### Task 7: Calibration against published benchmarks

**Files:**
- Create: `analysis/002-tee-shot-distance/tests/test_consistency.py`
- Possibly modify: `analysis/002-tee-shot-distance/data.py` (MISHIT / TROUBLE_COST within stated ranges)

The spec's must-pass check: the model, fed a tier's average drive, reproduces that tier's published benchmark score.

- [ ] **Step 1: Write the failing test**

`analysis/002-tee-shot-distance/tests/test_consistency.py`:

```python
import data
from model import expected_score, benchmark_score

TOLERANCE = 0.30  # strokes; peer review records the achieved max gap

def test_model_reproduces_published_benchmarks():
    worst = 0.0
    for tier in data.PUBLISHED_TIERS:
        for hole in (340, 380, 420, 460):
            gap = abs(expected_score(hole, tier) - benchmark_score(hole, tier))
            worst = max(worst, gap)
            assert gap < TOLERANCE, (tier, hole, gap)
    print(f"max benchmark gap: {worst:.3f} strokes")
```

- [ ] **Step 2: Run and calibrate**

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest tests/test_consistency.py -v -s`

If it fails: adjust ONLY `MISHIT` per-tier probabilities and `TROUBLE_COST` in `data.py`, staying inside the sensitivity ranges those dicts declare. These two dicts are the modeled calibration knobs; that is their documented job. If calibration cannot reach tolerance inside the ranges, STOP and flag for review: an anchor table is probably wrong against the source log. Never touch `E_HOLEOUT` or `BENCHMARK_PAR4` to force calibration; those are published anchors.

- [ ] **Step 3: Record the calibration**

Append a `## Calibration` section to `docs/sources/002_Source_Log.md`: final MISHIT and TROUBLE_COST values, the max benchmark gap achieved, one sentence on what moved and why.

- [ ] **Step 4: Run the full suite**

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add analysis/002-tee-shot-distance docs/sources/002_Source_Log.md
git commit -m "002: calibrate model to published tier benchmarks"
```

---

### Task 8: Monte Carlo validation harness

**Files:**
- Create: `analysis/002-tee-shot-distance/montecarlo.py`
- Create: `analysis/002-tee-shot-distance/tests/test_montecarlo.py`

- [ ] **Step 1: Write the failing test**

`analysis/002-tee-shot-distance/tests/test_montecarlo.py`:

```python
import numpy as np
import data
from model import expected_score
from montecarlo import simulate_hole

def test_montecarlo_matches_analytic():
    rng = np.random.default_rng(20260720)
    worst = 0.0
    for tier in (0, 15, 30):
        for hole in (340, 400, 460):
            mc = simulate_hole(hole, tier, n=200_000, rng=rng)
            an = expected_score(hole, tier)
            gap = abs(mc - an)
            worst = max(worst, gap)
            assert gap < 0.03, (tier, hole, mc, an)
    print(f"max MC vs analytic gap: {worst:.4f} strokes")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest tests/test_montecarlo.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'montecarlo'`

- [ ] **Step 3: Implement**

`analysis/002-tee-shot-distance/montecarlo.py`:

```python
"""Monte Carlo validation harness for release 002.

Peer-review artifact only; nothing here feeds a published chart. Simulates
the same distributions model.py integrates analytically, so agreement is a
check on the integration, not independent evidence.
"""
import numpy as np
import data
from model import strokes_to_holeout, _lie_probs

def simulate_hole(hole_yards, tier, club="driver", drive_mean=None, n=200_000, rng=None):
    rng = rng or np.random.default_rng()
    c = data.CLUBS[club]
    base = drive_mean if drive_mean is not None else data.DRIVER[tier]["mean"]
    mean = base * c["dist_ratio"]
    sd_d = mean * data.DRIVER[tier]["sd_dist_frac"]
    sd_lat = data.DRIVER[tier]["sd_lat"] * c["lat_ratio"]

    mishit = rng.random(n) < data.MISHIT[tier]
    carry = rng.normal(mean, sd_d, n)
    carry[mishit] = mean * data.MISHIT["carry_frac"]

    lateral = np.abs(rng.normal(0.0, sd_lat, n))
    fw = data.GEOMETRY["fairway_half_width"]
    edge = fw + data.GEOMETRY["rough_band"]
    lie = np.where(lateral <= fw, 0, np.where(lateral <= edge, 1, 2))  # 0 fw, 1 rough, 2 trouble
    lie[mishit] = 1

    leftover = np.maximum(hole_yards - carry, 8.0)
    strokes = np.ones(n)
    for i, lo in enumerate(leftover):
        if lie[i] == 0:
            strokes[i] += strokes_to_holeout(lo, "fairway", tier)
        elif lie[i] == 1:
            strokes[i] += strokes_to_holeout(lo, "rough", tier)
        else:
            strokes[i] += strokes_to_holeout(lo, "rough", tier) + data.TROUBLE_COST[tier]
    return float(strokes.mean())
```

If the loop is too slow at n=200,000, vectorize `strokes_to_holeout` with `np.interp` over the anchor tables; keep the seed and tolerances unchanged.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest tests/test_montecarlo.py -v -s`
Expected: PASS with max gap printed

- [ ] **Step 5: Commit**

```bash
git add analysis/002-tee-shot-distance/montecarlo.py analysis/002-tee-shot-distance/tests/test_montecarlo.py
git commit -m "002: Monte Carlo validation harness"
```

---

### Task 9: Output builder (results CSV + tool JSON)

**Files:**
- Create: `analysis/002-tee-shot-distance/build_outputs.py`
- Create: `analysis/002-tee-shot-distance/tests/test_outputs.py`

- [ ] **Step 1: Write the failing test**

`analysis/002-tee-shot-distance/tests/test_outputs.py`:

```python
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
    for tier in blob["tiers"]:
        assert set(blob["curves"][tier]) == set(blob["clubs"])
        for club in blob["clubs"]:
            grid = blob["curves"][tier][club]
            assert len(grid) == len(blob["holes"])
            assert all(len(row) == len(blob["drives"]) for row in grid)
        assert len(blob["benchmark"][tier]) == len(blob["holes"])
    assert os.path.exists(os.path.join(HERE, "outputs", "002_results.csv"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest tests/test_outputs.py -v`
Expected: FAIL (build_outputs.py does not exist)

- [ ] **Step 3: Implement**

`analysis/002-tee-shot-distance/build_outputs.py`:

```python
"""Build outputs/002_results.csv and outputs/tool_data.json.

tool_data.json contract (consumed by site/tee-shot-distance/tool.html):
  holes:    [280,290,...,500]
  drives:   [140,145,...,320]   (the golfer's DRIVER distance)
  tiers:    {"0": "0-hcp (scratch)", ..., "30": "30-hcp (modeled)"}
  clubs:    {"driver": {"label": "Driver", "dist_ratio": 1.0}, ...}
  curves:   curves[tier][club][hole_idx][drive_idx] = expected strokes when a
            golfer whose DRIVER goes `drives[drive_idx]` hits `club`
  benchmark: benchmark[tier][hole_idx] = published tier average for the hole
  modeled:  ["30"]
"""
import csv, json, os
import numpy as np
import data
from model import expected_score, benchmark_score, neutral_distance

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
os.makedirs(OUT, exist_ok=True)

HOLES = list(range(280, 501, 10))
DRIVES = list(range(140, 321, 5))

def tier_label(t):
    base = {0: "0-hcp (scratch)"}.get(t, f"{t}-hcp")
    return base + (" (modeled)" if t in data.MODELED_TIERS else "")

blob = {
    "holes": HOLES,
    "drives": DRIVES,
    "tiers": {str(t): tier_label(t) for t in data.TIERS},
    "clubs": {k: {"label": v["label"], "dist_ratio": v["dist_ratio"]} for k, v in data.CLUBS.items()},
    "curves": {}, "benchmark": {}, "modeled": [str(t) for t in data.MODELED_TIERS],
}
for t in data.TIERS:
    blob["benchmark"][str(t)] = [round(benchmark_score(h, t), 3) for h in HOLES]
    blob["curves"][str(t)] = {}
    for club in data.CLUBS:
        blob["curves"][str(t)][club] = [
            [round(expected_score(h, t, club, drive_mean=dv), 3) for dv in DRIVES]
            for h in HOLES
        ]
with open(os.path.join(OUT, "tool_data.json"), "w") as f:
    json.dump(blob, f, separators=(",", ":"))

with open(os.path.join(OUT, "002_results.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["tier", "hole_yards", "benchmark", "neutral_distance",
                "always_at_benchmark", "never_at_benchmark"])
    for t in data.TIERS:
        for h in HOLES:
            r = neutral_distance(h, t)
            w.writerow([t, h, round(benchmark_score(h, t), 3),
                        "" if r["threshold"] is None else round(r["threshold"], 1),
                        r["always_at_benchmark"], r["never_at_benchmark"]])

print("wrote", OUT)
for t in (10, 15, 20):
    r = neutral_distance(400, t)
    print(f"neutral distance, 400yd par 4, {t}-hcp:", r)
```

- [ ] **Step 4: Run tests, eyeball the printed thresholds**

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest tests/test_outputs.py -v -s`
Expected: PASS. Sanity-check the printed 400-yard thresholds against the theory (mid-handicap thresholds should land meaningfully below tier average driver distance; if they land above, investigate before proceeding).

- [ ] **Step 5: Commit (outputs stay untracked; commit code only)**

```bash
git add analysis/002-tee-shot-distance/build_outputs.py analysis/002-tee-shot-distance/tests/test_outputs.py
echo "outputs/" > analysis/002-tee-shot-distance/.gitignore
git add analysis/002-tee-shot-distance/.gitignore
git commit -m "002: output builder for tool JSON and results CSV"
```

---

### Task 10: Chart style module + Chart 1 (the headline)

**Files:**
- Create: `analysis/002-tee-shot-distance/style.py`
- Create: `analysis/002-tee-shot-distance/chart1.py`

- [ ] **Step 1: Port the brand style**

Copy `/Users/sunny/Documents/Claude/Projects/Golf Agent/Fairway_vs_Rough_Post/source/style.py` into `analysis/002-tee-shot-distance/style.py` unchanged except: update any 001-specific stamp text so the badge reads `DOGLEG DATA · 002 · TEE SHOT DISTANCE` and the source line cites this release's sources (`Shot Scope · Stagner/Arccos · Broadie 2011 · modeled values labeled`). Keep the white chart background convention from the recent site rework (commit d3f6749: whitened chart backgrounds), so if 001's `BG` token is cream, set `BG = "#FFFFFF"` here and note it.

- [ ] **Step 2: Build chart 1**

`analysis/002-tee-shot-distance/chart1.py` renders the headline: minimum neutral drive distance vs hole length, one line per tier.

Data prep (exact):

```python
import numpy as np
import matplotlib.pyplot as plt
import data
from model import neutral_distance
from style import *  # brand tokens: BG, INK, tier colors, FONT, stamp helper

holes = np.arange(300, 481, 10)
series = {}
for t in data.TIERS:
    ys = []
    for h in holes:
        r = neutral_distance(int(h), t)
        ys.append(np.nan if r["threshold"] is None else r["threshold"])
    series[t] = np.array(ys)
```

Layout spec: single panel, x = par-4 length (300 to 480), y = neutral drive distance. One line per tier using the tier color ramp from the dashboard (`TIER_COLORS` in `site/fairway-vs-rough/dashboard.html` line 259); tier 30 dashed with a "(modeled)" legend suffix. No reference line; keep the panel clean. Annotate one example: the 15-handicap value at 400 yards, with a short callout box in the 001 annotation style ("A 15 needs just NNN yards here"), value computed, never hand-typed. Gaps (NaN) where no threshold exists must break the line, and a footnote explains: "no line = any reasonable drive keeps that tier at benchmark." Badge and source line via `stamp()`. Output: `outputs/chart1_neutral_distance.png` at figsize (13.4, 9.6), dpi 200, same as 001 charts.

- [ ] **Step 3: Render and inspect**

Run: `cd "analysis/002-tee-shot-distance" && python3 chart1.py && open outputs/chart1_neutral_distance.png`
Check: every tier visible, no overlapping labels, modeled labels present, annotation value matches `002_results.csv`.

- [ ] **Step 4: Commit**

```bash
git add analysis/002-tee-shot-distance/style.py analysis/002-tee-shot-distance/chart1.py
git commit -m "002: brand style module and headline chart"
```

---

### Task 11: Charts 2 and 3 (the flat zone, the decomposition)

**Files:**
- Create: `analysis/002-tee-shot-distance/chart2.py`
- Create: `analysis/002-tee-shot-distance/chart3.py`

- [ ] **Step 1: Chart 2, the flat zone**

Expected strokes vs drive distance on a 400-yard par 4, per tier.

Data prep (exact):

```python
drives = np.arange(150, 311, 5)
curves = {t: [expected_score(400, t, "driver", drive_mean=float(d)) for d in drives] for t in data.TIERS}
benches = {t: benchmark_score(400, t) for t in data.TIERS}
```

Layout spec: one panel per tier is too many; use a 2-column grid of four panels for tiers 5, 10, 15, 20 (the audience core, and the home of Sunny's theory), each with its expected-score curve, a horizontal dashed line at the tier benchmark, the crossing point dotted down to the x-axis, and shading over the region where the curve sits within 0.05 strokes of its minimum (the flat zone). Title carries the claim ("Past the threshold, extra yards buy almost nothing"). Tier colors from the ramp. Badge, source line, modeled labels. Output: `outputs/chart2_flat_zone.png`.

- [ ] **Step 2: Render and inspect chart 2**

Run: `cd "analysis/002-tee-shot-distance" && python3 chart2.py && open outputs/chart2_flat_zone.png`
Check: crossing points match `002_results.csv` thresholds at 400 yards.

- [ ] **Step 3: Chart 3, the decomposition**

Where the cost moves as the drive gets shorter: Sunny's 220-drive/180-in example rendered. For a 400-yard par 4 at tier 15, decompose the expected-score delta vs the tier-average drive into (a) lie mix change and (b) longer approach, at drive distances 180, 200, 220, 240, 260.

Data prep (exact): for each drive distance d, compute total delta = `expected_score(400, 15, drive_mean=d) - expected_score(400, 15)`. Approach component: recompute with lie probabilities FROZEN at the tier-average-drive mix (copy `tee_outcomes`, override the lie dicts) so the remaining delta isolates leftover-distance cost; lie component = total minus approach component. Render as a stacked horizontal bar per drive distance, two segments (approach cost, lie cost), with the 220-yard bar annotated: "220 off the tee leaves 180 in; the approach is where the stroke goes." Output: `outputs/chart3_decomposition.png`.

- [ ] **Step 4: Render and inspect chart 3**

Run: `cd "analysis/002-tee-shot-distance" && python3 chart3.py && open outputs/chart3_decomposition.png`
Check: segments sum to the total delta (assert this in the script), signs read correctly.

- [ ] **Step 5: Commit**

```bash
git add analysis/002-tee-shot-distance/chart2.py analysis/002-tee-shot-distance/chart3.py
git commit -m "002: flat zone and decomposition charts"
```

---

### Task 12: Charts 4 and 5 (club verdict map, quote card)

**Files:**
- Create: `analysis/002-tee-shot-distance/chart4.py`
- Create: `analysis/002-tee-shot-distance/chart5.py`

- [ ] **Step 1: Chart 4, the club verdict map**

Data prep (exact):

```python
holes = np.arange(300, 481, 20)
verdicts = {t: [club_verdict(int(h), t)["best"] for h in holes] for t in data.TIERS}
```

Layout spec: a categorical heat grid, x = hole length, y = tier (0 at top, 30 at bottom, 30 row hatched + "(modeled)"), cell color by club (driver = clay #C05A36, wood = denim #5B7FA6, hybrid = ink #1C1B18 at 70%, iron = saddle #8A7F6E), cell text = club label. Legend below. Caption line inside the chart: "Best expected score off the tee, at each tier's real distances." If the gate decision was DISTANCE BANDS, labels come from `data.CLUBS[...]["label"]` band names instead; the script must not hardcode club names anywhere. Output: `outputs/chart4_club_map.png`.

- [ ] **Step 2: Render and inspect chart 4**

Run: `cd "analysis/002-tee-shot-distance" && python3 chart4.py && open outputs/chart4_club_map.png`

- [ ] **Step 3: Chart 5, the quote card**

The single most counterintuitive verified number. Selection rule, in order of preference: (1) a mid-handicap neutral threshold far below that tier's average driver distance on a common hole length (e.g. "a 15 needs only NNN yards on a 380-yard par 4"); (2) a hole-length row where the club map says iron/hybrid for multiple tiers; (3) the flattest flat-zone width. Compute candidates from `002_results.csv`, pick per the rule, and render a big-number card in the style of 001's quote card (`launch/quote_card_150yd.png` for reference): Fraunces 900 number, one-line claim, badge, source line, modeled label if the number touches tier 30. The number must be computed in the script from the model, never typed. Output: `outputs/chart5_quote_card.png`.

- [ ] **Step 4: Render and inspect chart 5**

Run: `cd "analysis/002-tee-shot-distance" && python3 chart5.py && open outputs/chart5_quote_card.png`

- [ ] **Step 5: Commit**

```bash
git add analysis/002-tee-shot-distance/chart4.py analysis/002-tee-shot-distance/chart5.py
git commit -m "002: club verdict map and quote card"
```

---

### Task 13: Site chart assets + /cite exports

**Files:**
- Create: `site/assets/img/002_chart1_neutral_distance.png` (and 002_chart2..5)
- Create: `site/assets/cite/002_chart1_neutral_distance_1280x720.png` (and 2..5)
- Create: `analysis/002-tee-shot-distance/export_site_assets.py`

- [ ] **Step 1: Write the exporter**

`export_site_assets.py`: copies the five `outputs/chart*.png` to `site/assets/img/` with the `002_` prefix, and renders 1280x720 versions to `site/assets/cite/` (re-render at figsize (12.8, 7.2) dpi 100 by re-invoking each chart script with an env var `CITE_EXPORT=1` that each chart script honors: when set, chart scripts write `outputs/cite/<name>_1280x720.png` with the same content at that size). Add the env-var branch to each chart script (five small edits: read `os.environ.get("CITE_EXPORT")`, switch figsize/dpi/output path).

- [ ] **Step 2: Run it, verify dimensions**

Run: `cd "analysis/002-tee-shot-distance" && python3 export_site_assets.py && file ../../site/assets/cite/002_*.png`
Expected: five files in each destination; cite files report 1280 x 720.

- [ ] **Step 3: Commit**

```bash
git add site/assets/img/002_*.png site/assets/cite/002_*.png analysis/002-tee-shot-distance
git commit -m "002: site chart assets and cite exports"
```

---

### Task 14: The tool page

**Files:**
- Create: `site/tee-shot-distance/tool.html`

- [ ] **Step 1: Build the page skeleton from the existing pattern**

Copy the head, CSS token block, header, footer, and layout classes from `site/fairway-vs-rough/dashboard.html` (lines 1 to 115 cover head + styles). Page identity: title "How far do you need to hit it? · Dogleg Data", canonical `https://doglegdata.com/tee-shot-distance/tool.html`, matching og/twitter/JSON-LD blocks (WebApplication schema, description: "Enter a par 4, your handicap, and your typical drive. Get the strokes-gained verdict, the neutral distance for that hole, and the club that buys you nothing."). No tabs nav; this page is a single card.

- [ ] **Step 2: Controls and outputs**

Three controls, same markup classes as the existing dashboard controls:
- Hole length slider: id `ts-hole`, min 280, max 500, step 10, default 400
- Handicap select: id `ts-tier`, options from the JSON tiers (30 option text carries "(modeled)")
- Typical drive slider: id `ts-drive`, min 140, max 320, step 5, default 220

Outputs:
- KPI row (reuse `.kpi` classes): "Your expected score" / "Typical NN-hcp scores" / "Strokes gained vs your tier" / "Neutral distance for this hole"
- Verdict block (reuse `.verdict` classes, fairway = gaining, rough = losing): headline "You're not losing strokes off the tee here" or "Distance is costing you strokes here", detail line includes the club comparison: compute expected score for each club at `drive x dist_ratio` and name the shortest club within 0.05 strokes of the best ("Your 3-wood gives up nothing on this hole" / "This hole wants the driver").
- Chart (`.chart-box`, one canvas): expected strokes vs drive distance for the selected tier and hole, solid line in the tier color; dashed horizontal benchmark line; a scatter dot at the user's drive; a vertical dotted line at the neutral distance when it exists. When `threshold` is null: no vertical line, and the note under the chart explains which edge case applies ("any reasonable drive keeps you at benchmark here" vs "distance alone doesn't close the gap on this hole").
- Modeled badge (`.badge-modeled`) on the tier label when tier 30, same mechanism as the existing dashboard's `isExtrapolated`.

- [ ] **Step 3: Wire the data and logic**

Embed `outputs/tool_data.json` as the `<script type="application/json" id="tool-data">` blob (same pattern as `dashboard-data`). JS logic (vanilla, mirroring the existing page):

```js
const DATA = JSON.parse(document.getElementById('tool-data').textContent);
// bilinear interpolation over (holes, drives) for a tier+club grid
function scoreAt(tier, club, hole, drive){
  const H = DATA.holes, D = DATA.drives, G = DATA.curves[tier][club];
  const hi = Math.min(Math.max(H.findIndex(h => h >= hole), 1), H.length - 1);
  const di = Math.min(Math.max(D.findIndex(d => d >= drive), 1), D.length - 1);
  const th = (hole - H[hi-1]) / (H[hi] - H[hi-1]);
  const td = (drive - D[di-1]) / (D[di] - D[di-1]);
  const a = G[hi-1][di-1]*(1-td) + G[hi-1][di]*td;
  const b = G[hi][di-1]*(1-td) + G[hi][di]*td;
  return a*(1-th) + b*th;
}
function benchmarkAt(tier, hole){ /* 1-D interp over DATA.holes on DATA.benchmark[tier] */ }
function neutralAt(tier, hole){
  // walk DATA.drives, find first drive where driver-club score <= benchmark; interpolate
  // return {threshold, always, never} exactly like the Python model's contract
}
```

Strokes gained shown = `benchmarkAt - scoreAt(tier,'driver',hole,drive)`, positive = gaining, formatted `+0.31` / `-0.42`. All three inputs re-render on `input` events, chart updates via `chart.update('none')`, same as the existing page.

- [ ] **Step 4: Verify against the Python model**

Add a fixed test grid to `analysis/002-tee-shot-distance/tests/test_outputs.py`:

```python
def test_tool_json_matches_model_on_grid():
    import data as data_mod
    from model import expected_score
    with open(os.path.join(HERE, "outputs", "tool_data.json")) as f:
        blob = json.load(f)
    for tier in ("0", "15", "30"):
        for club in ("driver", "iron"):
            for hi, hole in [(0, 280), (12, 400), (22, 500)]:
                for di, drive in [(0, 140), (16, 220), (36, 320)]:
                    got = blob["curves"][tier][club][hi][di]
                    want = expected_score(hole, int(tier), club, drive_mean=drive)
                    assert abs(got - want) < 0.005, (tier, club, hole, drive)
```

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest tests/test_outputs.py -v`
Expected: PASS

- [ ] **Step 5: Verify the page in the browser**

Open the page (preview tools or `open site/tee-shot-distance/tool.html`). Check: chart renders; moving each slider updates KPIs, verdict, and chart; tier 30 shows the modeled badge; the 400-yard/15-hcp/220-drive case shows values matching `002_results.csv`; no console errors; mobile width (375px) keeps controls usable.

- [ ] **Step 6: Commit**

```bash
git add site/tee-shot-distance/tool.html analysis/002-tee-shot-distance/tests/test_outputs.py
git commit -m "002: par-4 tee shot calculator tool page"
```

---

### Task 15: Caption + X alt version

**Files:**
- Create: `docs/sources/002_Tee_Shot_Caption.md`

- [ ] **Step 1: Write the long-form caption**

Structure (mirror `docs/sources/Fairway_vs_Rough_Caption.md`): hook paragraph stating the finding with the chart-1 headline number; the theory framing (distance culture vs the math); how to read each of the five charts, one short paragraph each; the 220/180 worked example walked through in prose; the published-vs-modeled disclosure paragraph (name what is modeled: tier 30, interpolation, mishit and trouble-cost calibration); source credits with links (Shot Scope, Stagner/Arccos, Broadie, GOLFTEC); the tool call-to-action ("run your own hole at doglegdata.com/tee-shot-distance/tool.html"). Every number quoted must be re-derived from `002_results.csv`, cross-checked at write time. Follow the global writing rules in the user CLAUDE.md (no em dashes, no adverbs, active voice).

- [ ] **Step 2: Write the X alt version**

Same file, `## X version` section: under 280 characters plus the chart-1 image, leading with the quote-card number, ending with the tool link.

- [ ] **Step 3: Commit**

```bash
git add docs/sources/002_Tee_Shot_Caption.md
git commit -m "002: long-form caption and X alt"
```

---

### Task 16: The article page

**Files:**
- Create: `site/tee-shot-distance/index.html`

- [ ] **Step 1: Build from the 001 article pattern**

Copy structure from `site/fairway-vs-rough/index.html`: head block (title "How far do you need to hit it? · Dogleg Data", canonical, og/twitter, Article JSON-LD with Sunny Rathor byline, same fonts/CSS), header, article body, footer. Body content adapts the long-form caption from Task 15 into the article voice, with the five charts as `<figure>` blocks using `site/assets/img/002_*.png`, each with alt text that states the chart's claim and its key number, and modeled labels in captions where they apply. Include a prominent link card to the tool page and a sources section matching 001's.

- [ ] **Step 2: Verify in browser**

Open the page. Check: images load, layout matches the 001 article at desktop and 375px width, all internal links resolve, no console errors.

- [ ] **Step 3: Commit**

```bash
git add site/tee-shot-distance/index.html
git commit -m "002: analysis article page"
```

---

### Task 17: Site integration (home, sitemap, llms.txt, cite page)

**Files:**
- Modify: `site/index.html`
- Modify: `site/sitemap.xml`
- Modify: `site/llms.txt`
- Modify: `site/cite/index.html`

- [ ] **Step 1: Homepage**

Add an analysis card for 002 alongside the existing 001 card/link block (around lines 91 to 108 of `site/index.html`), linking to `tee-shot-distance/index.html` and `tee-shot-distance/tool.html`. Keep the hero buttons pointing at the newest release: swap "Read the first analysis" to point at 002 with updated copy ("Read the latest analysis"), keep a link to 001 in the body.

- [ ] **Step 2: Sitemap and llms.txt**

Add `https://doglegdata.com/tee-shot-distance/index.html` and `.../tool.html` entries to `site/sitemap.xml` with `lastmod` = ship date. Add both pages with one-line descriptions to `site/llms.txt`.

- [ ] **Step 3: Cite page**

Add a 002 section to `site/cite/index.html` following the existing per-chart pattern: the five `site/assets/cite/002_*_1280x720.png` exports with download links, the credit line, and the quote-card number called out as the citable stat.

- [ ] **Step 4: Verify and commit**

Open the homepage and cite page, click through every new link.

```bash
git add site/index.html site/sitemap.xml site/llms.txt site/cite/index.html
git commit -m "002: wire release into home, sitemap, llms.txt, cite"
```

---

### Task 18: Peer review document

**Files:**
- Create: `docs/sources/Peer_Review_002_Tee_Shot.md`

- [ ] **Step 1: Run the review**

Format follows `docs/sources/Peer_Review_Fairway_vs_Rough.md`: must-fix / should-fix / minor, with sign-off line. The review must cover, at minimum:

1. Source log audit: every `data.py` literal traceable to `002_Source_Log.md`; URLs live; retrieval dates present.
2. Benchmark reproduction: the achieved max gap from Task 7, restated, with the calibration values and their declared ranges.
3. Monte Carlo agreement: the achieved max gap from Task 8.
4. Sensitivity analysis: rerun `build_outputs.py` with MISHIT probabilities at 0.5x and 1.5x and TROUBLE_COST at its range ends; report how much the 400-yard thresholds move per tier. If any headline number moves by more than 15 yards across the sensitivity range, the caption must state the range, not the point value.
5. Cross-release consistency: any number shared with 001 (dispersion anchors, GOLFTEC values) matches 001's published values.
6. Labeling audit: every chart, the tool, the article, and the caption carry modeled labels wherever tier 30, interpolation, or calibrated values appear.
7. Chart-to-copy consistency: every number in the caption and article re-derived from `002_results.csv`.

- [ ] **Step 2: Fix what the review finds**

Must-fix items block publication. Apply fixes, rerun the full test suite (`python3 -m pytest`), rebuild outputs and charts if data changed.

- [ ] **Step 3: Commit**

```bash
git add docs/sources/Peer_Review_002_Tee_Shot.md
git commit -m "002: peer review with sensitivity analysis"
```

---

### Task 19: Final verification sweep

**Files:** none new

- [ ] **Step 1: Full test suite**

Run: `cd "analysis/002-tee-shot-distance" && python3 -m pytest -v`
Expected: all PASS

- [ ] **Step 2: Rebuild everything from scratch**

Run: `cd "analysis/002-tee-shot-distance" && rm -rf outputs && python3 build_outputs.py && for i in 1 2 3 4 5; do python3 chart$i.py; done && python3 export_site_assets.py`
Expected: clean rebuild, no errors, site assets refreshed. `git status` shows no unexpected site-asset diffs (if it does, a chart script is non-deterministic; fix it).

- [ ] **Step 3: Browser pass**

Open home, article, tool, and cite pages. Verify every link, chart image, and the tool's three inputs one more time. Confirm the tool's displayed values for (400 yd, 15 hcp, 220 drive) match `002_results.csv`.

- [ ] **Step 4: Ship checklist snapshot**

Confirm the five deliverables exist and are committed: charts (site/assets/img + cite exports), caption doc, tool page, peer review doc, article + site wiring. Print a one-paragraph summary of headline numbers for the launch post. Do NOT publish anything externally; publishing is Sunny's call on ship day.

- [ ] **Step 5: Final commit if anything moved**

```bash
git add analysis/002-tee-shot-distance site docs && git commit -m "002: final verification sweep"
```

(Never `git add -A`: stray files at the repo root are not part of this release.)

---

## Task order and dependencies

1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17 → 18 → 19

Tasks 10-12 (charts) can run in parallel with 14 (tool page) once 9 is done. Task 15 needs 9 (numbers) but not the charts. Everything else is sequential.
