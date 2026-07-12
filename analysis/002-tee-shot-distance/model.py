"""Analytic expected-strokes model for release 002.

Own-tier baseline. All interpolation between published anchors is MODELED.
"""
import numpy as np
import data
from math import erf, sqrt

def strokes_to_holeout(dist, lie, tier):
    """Expected strokes to hole out from dist yards, given lie, for tier.

    Linear interpolation on the gate-verified anchor table. Below the first
    anchor: clamp to the first anchor value. Above the last anchor: extend
    the last segment's slope (long-leftover extrapolation, MODELED).

    Result is multiplied by data.HOLEOUT_SCALE[tier] before returning; this
    factor is 1.0 for all tiers today and may be calibrated in Task 7.
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
    mixture: clean strike (gauss quadrature nodes scaled by the distance
    standard deviation) plus a tier-specific severe-mishit branch that lands
    in the rough at the MISHIT carry_frac fraction of the intended distance.
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
    lies = [dict(clean_lie) for _ in range(len(clean_carries))] + [{"fairway": 0.0, "rough": 1.0, "trouble": 0.0}]
    return carries, weights, lies


from functools import lru_cache

DRIVE_GRID = np.arange(140, 321, 2)
COST_MARGIN = 0.10  # strokes; the cost line's default margin (one shot per ten rounds)

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
    """
    return _benchmark_cached(round(float(hole_yards), 1), tier)

def neutral_distance(hole_yards, tier, club="driver", margin=COST_MARGIN):
    """The cost line: smallest drive distance where expected score stays
    within `margin` strokes of the tier benchmark on this hole.

    Returns {"threshold": yd or None, "always_at_benchmark": bool,
    "never_at_benchmark": bool}. Edge cases: a short hole can sit within
    margin across the whole grid (threshold None, always True); a brutal
    hole can exceed margin everywhere (threshold None, never True).
    """
    bench = benchmark_score(hole_yards, tier)
    scores = np.array([expected_score(hole_yards, tier, club, float(d)) for d in DRIVE_GRID])
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

def club_verdict(hole_yards, tier, drive_mean=None):
    """Expected score per club at this golfer's distances; best = lowest."""
    scores = {club: expected_score(hole_yards, tier, club, drive_mean) for club in data.CLUBS}
    best = min(scores, key=scores.get)
    return {"best": best, "scores": scores}
