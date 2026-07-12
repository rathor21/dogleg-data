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
