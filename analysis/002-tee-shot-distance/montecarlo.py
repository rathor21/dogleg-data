"""Monte Carlo validation harness for release 002.

Peer-review artifact only; nothing here feeds a published chart. Simulates
the same distributions model.py integrates analytically, so agreement is a
check on the integration, not independent evidence.
"""
import numpy as np
import data
from model import trouble_increment

def simulate_hole(hole_yards, tier, club="driver", drive_mean=None, fairway_width=None, n=200_000, rng=None):
    """Simulate n plays of a par 4 and return mean strokes.

    Mirrors model.expected_score's distributions exactly: carry is normal
    (mean = drive_mean-or-tier-average times the club's dist_ratio), a
    tier-probability mishit branch lands in the rough at carry_frac of the
    intended distance, lateral error sets the lie via GEOMETRY (and
    fairway_width, mirroring model._lie_probs), and holeout uses the same
    anchor tables, scale, and trouble cost. drive_mean is the golfer's
    DRIVER distance; fairway_width is the full fairway width in yards
    (None uses the published 36-yd default, matching model._lie_probs);
    rng an optional np.random.Generator.
    """
    rng = rng if rng is not None else np.random.default_rng()
    c = data.CLUBS[club]
    base = drive_mean if drive_mean is not None else data.DRIVER[tier]["mean"]
    mean = base * c["dist_ratio"]
    sd_d = mean * data.DRIVER[tier]["sd_dist_frac"]
    sd_lat = data.DRIVER[tier]["sd_lat"] * c["lat_ratio"]

    mishit = rng.random(n) < data.MISHIT[tier]
    carry = rng.normal(mean, sd_d, n)
    carry[mishit] = mean * data.MISHIT["carry_frac"]

    lateral = np.abs(rng.normal(0.0, sd_lat, n))
    width = fairway_width if fairway_width is not None else data.GEOMETRY["fairway_half_width"] * 2
    fw = width / 2.0
    band_scale = min(width / data.HAZARD_GEOMETRY["ref_width"], 1.0)
    edge = fw + data.GEOMETRY["rough_band"] * band_scale
    _trouble_inc = trouble_increment(tier, width)
    lie = np.where(lateral <= fw, 0, np.where(lateral <= edge, 1, 2))  # 0 fw, 1 rough, 2 trouble
    lie[mishit] = 1  # mishit lands in rough, never trouble, per tee_outcomes

    leftover = np.maximum(hole_yards - carry, data.LEFTOVER_FLOOR_YD)

    # vectorized strokes_to_holeout per lie via np.interp over the anchor tables
    strokes = np.ones(n)
    for lie_code, lie_name in ((0, "fairway"), (1, "rough"), (2, "rough")):
        mask = lie == lie_code
        if not mask.any():
            continue
        table = data.E_HOLEOUT[tier][lie_name]
        xs = np.array([p[0] for p in table], float)
        ys = np.array([p[1] for p in table], float)
        lo = leftover[mask]
        # np.interp clamps to ys[0] below xs[0], matching strokes_to_holeout's
        # explicit below-first-anchor clamp.
        vals = np.interp(lo, xs, ys)
        # extend last segment's slope beyond the final anchor, mirror strokes_to_holeout
        slope = (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
        beyond = lo > xs[-1]
        vals[beyond] = ys[-1] + slope * (lo[beyond] - xs[-1])
        vals *= data.HOLEOUT_SCALE[tier]
        if lie_code == 2:
            vals += _trouble_inc  # trouble = scaled rough holeout + unscaled trouble cost
        strokes[mask] += vals
    return float(strokes.mean())
