"""Analytic expected-strokes model for release 002.

Own-tier baseline. All interpolation between published anchors is MODELED.
"""
from functools import lru_cache
from math import erf, sqrt

import numpy as np
import data

DRIVE_GRID = np.arange(140, 321, 2)
COST_MARGIN = data.COST_MARGIN  # strokes; the cost line's default margin (see data.py)

def strokes_to_holeout(dist, lie, tier):
    """Expected strokes to hole out from dist yards, given lie, for tier.

    Linear interpolation on the gate-verified anchor table. Below the first
    anchor: clamp to the first anchor value. Above the last anchor: extend
    the last segment's slope (long-leftover extrapolation, MODELED).

    Result is multiplied by data.HOLEOUT_SCALE[tier] before returning; this
    factor is calibrated per tier (see data.HOLEOUT_SCALE and the Task 7
    Calibration section of docs/sources/002_Source_Log.md).
    """
    table = data.E_HOLEOUT[tier][lie]
    xs = np.array([p[0] for p in table], dtype=float)
    ys = np.array([p[1] for p in table], dtype=float)
    if dist <= xs[0]:
        result = float(ys[0])
    elif dist >= xs[-1]:
        slope = (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
        result = float(ys[-1] + slope * (dist - xs[-1]))
    else:
        result = float(np.interp(dist, xs, ys))
    return result * data.HOLEOUT_SCALE[tier]


_NODES, _WEIGHTS = np.polynomial.hermite_e.hermegauss(15)
_WEIGHTS = _WEIGHTS / _WEIGHTS.sum()

def _phi(z):
    return 0.5 * (1.0 + erf(z / sqrt(2.0)))

def hazard_share(fairway_width=None):
    """Share of the trouble zone priced at OB cost instead of playable trouble.

    Zero at or above the published 36-yd reference width (so every default-
    width number and the Task 7 calibration are untouched), rising linearly
    to 1.0 at the floor width. MODELED; see data.HAZARD_GEOMETRY and the
    source log's rev 5 section.
    """
    W = fairway_width if fairway_width is not None else data.GEOMETRY["fairway_half_width"] * 2
    ref = data.HAZARD_GEOMETRY["ref_width"]
    floor = data.HAZARD_GEOMETRY["floor_width"]
    if W >= ref:
        return 0.0
    return float(min(1.0, (ref - W) / (ref - floor)))

def trouble_increment(tier, fairway_width=None):
    """Strokes added over the rough holeout when the tee ball finds trouble,
    blended between playable trouble and OB by the width-scaled hazard share."""
    h = hazard_share(fairway_width)
    return (1.0 - h) * data.TROUBLE_COST[tier] + h * data.OB_COST

def _lie_probs(sd_lat, fairway_width=None):
    """P(fairway/rough/trouble) from lateral dispersion vs hole geometry.

    fairway_width is the full fairway width in yards; half of it is the
    lateral distance a tee shot must stay inside to be "in the fairway".
    Defaults to the published width (data.GEOMETRY["fairway_half_width"] * 2
    = 36 yd, Stagner, anchor F). The rough band beyond the fairway edge scales
    with W/36 below the reference width and stays put above it (rev 5).
    """
    width = fairway_width if fairway_width is not None else data.GEOMETRY["fairway_half_width"] * 2
    fw = width / 2.0
    # Tight corridors carry thin rough before the trouble: the band scales
    # with W/ref below the reference width, and stays put above it (rev 5).
    band_scale = min(width / data.HAZARD_GEOMETRY["ref_width"], 1.0)
    edge = fw + data.GEOMETRY["rough_band"] * band_scale
    p_fw = _phi(fw / sd_lat) - _phi(-fw / sd_lat)
    p_trouble = 2.0 * (1.0 - _phi(edge / sd_lat))
    return {"fairway": p_fw, "rough": 1.0 - p_fw - p_trouble, "trouble": p_trouble}

def tee_outcomes(club, tier, drive_mean=None, *, fairway_width=None):
    """Discretized tee-shot outcome distribution for one swing.

    Returns (carries, weights, lie_probs_per_node). The distribution is a
    mixture: clean strike (gauss quadrature nodes scaled by the distance
    standard deviation) plus a tier-specific severe-mishit branch that lands
    in the rough at the MISHIT carry_frac fraction of the intended distance.

    fairway_width (yards, full width) is forwarded to _lie_probs; None uses
    the published 36-yd default.
    """
    c = data.CLUBS[club]
    base = drive_mean if drive_mean is not None else data.DRIVER[tier]["mean"]
    mean = base * c["dist_ratio"]
    sd_d = mean * data.DRIVER[tier]["sd_dist_frac"]
    sd_lat = data.DRIVER[tier]["sd_lat"] * c["lat_ratio"]
    p_miss = data.MISHIT[tier]

    clean_carries = mean + sd_d * _NODES
    clean_weights = _WEIGHTS * (1.0 - p_miss)
    clean_lie = _lie_probs(sd_lat, fairway_width=fairway_width)

    carries = np.append(clean_carries, mean * data.MISHIT["carry_frac"])
    weights = np.append(clean_weights, p_miss)
    lies = [dict(clean_lie) for _ in range(len(clean_carries))] + [{"fairway": 0.0, "rough": 1.0, "trouble": 0.0}]
    return carries, weights, lies


def expected_score(hole_yards, tier, club="driver", drive_mean=None, *, fairway_width=None):
    """Full-hole expected strokes on a par 4 of hole_yards for tier.

    fairway_width (yards, full width) is forwarded to tee_outcomes/_lie_probs;
    None uses the published 36-yd default.
    """
    carries, weights, lies = tee_outcomes(club, tier, drive_mean, fairway_width=fairway_width)
    total = 1.0  # the tee stroke
    for carry, w, lp in zip(carries, weights, lies):
        leftover = max(hole_yards - carry, data.LEFTOVER_FLOOR_YD)
        e_fair = strokes_to_holeout(leftover, "fairway", tier)
        e_rough = strokes_to_holeout(leftover, "rough", tier)
        e_trouble = e_rough + trouble_increment(tier, fairway_width)
        total += w * (lp["fairway"] * e_fair + lp["rough"] * e_rough + lp["trouble"] * e_trouble)
    return float(total)


def score_components(hole_yards, tier, club="driver", drive_mean=None):
    """Width-independent decomposition of expected_score, for the tool.

    Returns {"base", "gap", "tc_pl", "tc_hz"} such that, for any width W,
    expected_score(hole_yards, tier, club, drive_mean, fairway_width=W) equals
    base + p_fw(W) * gap + p_tr(W) * ((1-h(W)) * tc_pl + h(W) * tc_hz),
    with h = hazard_share(W), and where p_fw/p_tr are
    _lie_probs(sd_lat, fairway_width=W)["fairway"/"trouble"] for this club's
    lateral sd. base = 1 + p_miss * e_holeout(mishit leftover, rough) +
    (1 - p_miss) * E_rough_nodes; gap = (1 - p_miss) * (E_fair_nodes -
    E_rough_nodes); tc_pl/tc_hz = (1 - p_miss) times TROUBLE_COST[tier] and
    OB_COST. E_fair_nodes
    and E_rough_nodes are the quadrature-weighted holeout expectations over
    the clean-strike branch only, with weights renormalized to sum to 1 over
    that branch (the mishit branch is handled separately in base, since it
    never reaches the fairway or trouble buckets). The tool consumes this
    decomposition to recompute E(W) client-side at any width without
    re-deriving the model.
    """
    carries, weights, _ = tee_outcomes(club, tier, drive_mean)
    p_miss = data.MISHIT[tier]

    clean_carries = carries[:-1]
    clean_weights = weights[:-1]
    w_norm = clean_weights / clean_weights.sum()

    e_fair_sum = 0.0
    e_rough_sum = 0.0
    for carry, w in zip(clean_carries, w_norm):
        leftover = max(hole_yards - carry, data.LEFTOVER_FLOOR_YD)
        e_fair_sum += w * strokes_to_holeout(leftover, "fairway", tier)
        e_rough_sum += w * strokes_to_holeout(leftover, "rough", tier)

    mishit_leftover = max(hole_yards - carries[-1], data.LEFTOVER_FLOOR_YD)
    e_mishit = strokes_to_holeout(mishit_leftover, "rough", tier)

    base = 1.0 + p_miss * e_mishit + (1.0 - p_miss) * e_rough_sum
    gap = (1.0 - p_miss) * (e_fair_sum - e_rough_sum)
    tc_pl = (1.0 - p_miss) * data.TROUBLE_COST[tier]
    tc_hz = (1.0 - p_miss) * data.OB_COST
    # E(W) = base + p_fw(W)*gap + p_tr(W)*((1-h(W))*tc_pl + h(W)*tc_hz)
    return {"base": float(base), "gap": float(gap),
            "tc_pl": float(tc_pl), "tc_hz": float(tc_hz)}

# Cache key must track benchmark_score's full argument list: today that is
# (hole_yards, tier) with club/drive_mean fixed at tier defaults. If
# benchmark_score ever gains club or drive_mean parameters, extend this key
# in lockstep or stale cross-club values will be served.
@lru_cache(maxsize=4096)
def _benchmark_cached(hole_yards_rounded, tier):
    return expected_score(float(hole_yards_rounded), tier)

def benchmark_score(hole_yards, tier):
    """Typical score for this tier on a par 4 of this length.

    MODELED: this is the model's own expected score at the tier's average
    drive and dispersion. Its level is pinned to the published Shot Scope
    aggregate par-4 scores (data.BENCHMARK_AGG) by the Task 7 calibration.
    No published (tier x length) scoring table exists; see the source log's
    Benchmark decision.

    Always evaluated at the published default fairway width, never the
    caller's fairway_width: the benchmark describes a typical hole, so a
    narrower fairway should read as strokes lost against it, not as a moved
    goalpost.
    """
    return _benchmark_cached(round(float(hole_yards), 1), tier)

def neutral_distance(hole_yards, tier, club="driver", margin=COST_MARGIN, *, fairway_width=None):
    """The cost line: smallest drive distance where expected score stays
    within `margin` strokes of the tier benchmark on this hole.

    Returns {"threshold": yd or None, "always_at_benchmark": bool,
    "never_at_benchmark": bool}. Edge cases: a short hole can sit within
    margin across the whole grid (threshold None, always True); a brutal
    hole can exceed margin everywhere (threshold None, never True).

    fairway_width (yards, full width) varies the width-varied expected-score
    curve; the benchmark itself always stays at the published default width
    (see benchmark_score), so a narrow fairway_width can push the cost line
    right, or off the grid entirely (never_at_benchmark).
    """
    bench = benchmark_score(hole_yards, tier)
    scores = np.array([
        expected_score(hole_yards, tier, club, float(d), fairway_width=fairway_width)
        for d in DRIVE_GRID
    ])
    within = scores <= bench + margin
    if within.all():
        return {"threshold": None, "always_at_benchmark": True, "never_at_benchmark": False}
    if not within.any():
        return {"threshold": None, "always_at_benchmark": False, "never_at_benchmark": True}
    i = int(np.argmax(within))
    if i == 0:
        return {"threshold": float(DRIVE_GRID[0]), "always_at_benchmark": False, "never_at_benchmark": False}
    x0, x1 = float(DRIVE_GRID[i - 1]), float(DRIVE_GRID[i])
    y0, y1 = float(scores[i - 1]), float(scores[i])
    if y0 == y1:
        t = x1
    else:
        t = x0 + (y0 - (bench + margin)) * (x1 - x0) / (y0 - y1)
    return {"threshold": float(t), "always_at_benchmark": False, "never_at_benchmark": False}

def club_verdict(hole_yards, tier, drive_mean=None, *, fairway_width=None):
    """Expected score per club at this golfer's distances; best = lowest.

    fairway_width (yards, full width) is forwarded to expected_score for
    every club; None uses the published 36-yd default.
    """
    scores = {
        club: expected_score(hole_yards, tier, club, drive_mean, fairway_width=fairway_width)
        for club in data.CLUBS
    }
    best = min(scores, key=scores.get)
    return {"best": best, "scores": scores}


def bailout_threshold(hole_yards, tier, alt_club="wood", drive_mean=None, ob_cost=None, *, fairway_width=None):
    """Excess OB rate at which the driver stops beating alt_club off the tee.

    Returns the per-drive probability p* of an out-of-bounds drive, over and
    above whatever OB risk alt_club carries, at which the driver's expected
    score plus OB cost equals the alternative club's expected score:
    p* = (E_alt - E_driver) / OB_COST. MODELED: each OB costs a flat
    ob_cost strokes (stroke and distance); see the source log. Returns None
    when the alternative club already beats the driver outright (p* <= 0
    would be nonsensical to report as an OB rate).

    fairway_width (yards, full width) is forwarded to expected_score for
    both clubs; None uses the published 36-yd default.
    """
    cost = ob_cost if ob_cost is not None else data.OB_COST
    e_driver = expected_score(hole_yards, tier, "driver", drive_mean, fairway_width=fairway_width)
    e_alt = expected_score(hole_yards, tier, alt_club, drive_mean, fairway_width=fairway_width)
    p = (e_alt - e_driver) / cost
    return float(p) if p > 0 else None
