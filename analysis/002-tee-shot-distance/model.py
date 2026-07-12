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
