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
