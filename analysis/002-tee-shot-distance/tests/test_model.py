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

def test_tee_outcomes_structure():
    carries, weights, lies = tee_outcomes("driver", 15, drive_mean=250)
    assert len(carries) == len(weights) == len(lies) == 16
    assert abs(carries[-1] - 250 * data.MISHIT["carry_frac"]) < 1e-9
    assert lies[-1] == {"fairway": 0.0, "rough": 1.0, "trouble": 0.0}
    lies[0]["fairway"] = -1.0  # mutation must not leak across nodes
    assert lies[1]["fairway"] != -1.0

from model import expected_score, benchmark_score, neutral_distance, club_verdict

def test_expected_score_reasonable_range():
    for tier in data.TIERS:
        s = expected_score(400, tier)
        assert 3.5 < s < 7.5, (tier, s)

def test_expected_score_falls_with_more_distance():
    scores = [expected_score(430, 20, drive_mean=d) for d in (160, 200, 240, 280)]
    assert all(a >= b - 1e-6 for a, b in zip(scores, scores[1:]))

def test_expected_score_rises_with_hole_length():
    for tier in (0, 15, 30):
        scores = [expected_score(L, tier) for L in (320, 360, 400, 440, 480)]
        assert all(a < b for a, b in zip(scores, scores[1:])), tier

def test_benchmark_is_model_at_tier_defaults():
    for tier in (0, 15, 30):
        for L in (340, 400, 460):
            assert abs(benchmark_score(L, tier) - expected_score(L, tier)) < 1e-9

def test_benchmark_orders_across_tiers():
    vals = [benchmark_score(400, t) for t in data.TIERS]
    assert all(a < b for a, b in zip(vals, vals[1:]))

def test_cost_line_shape_and_semantics():
    res = neutral_distance(400, 15)
    assert set(res) == {"threshold", "always_at_benchmark", "never_at_benchmark"}
    assert res["threshold"] is not None
    t = res["threshold"]
    assert 140 <= t <= data.DRIVER[15]["mean"]
    # at the cost line the score sits within margin of benchmark; well below it, outside
    bench = benchmark_score(400, 15)
    assert expected_score(400, 15, drive_mean=t + 2) <= bench + 0.10 + 1e-6
    assert expected_score(400, 15, drive_mean=max(t - 30, 140)) > bench + 0.10 - 1e-6

def test_cost_line_monotonic_in_hole_length():
    ths = []
    for L in (340, 380, 420, 460):
        r = neutral_distance(L, 15)
        if r["threshold"] is not None:
            ths.append(r["threshold"])
    assert len(ths) >= 2
    assert all(a <= b + 2.0 for a, b in zip(ths, ths[1:]))

def test_cost_line_short_hole_scratch():
    r = neutral_distance(300, 0)
    assert r["threshold"] is None or r["threshold"] <= data.DRIVER[0]["mean"]

def test_club_verdict_returns_known_club():
    v = club_verdict(400, 15)
    assert v["best"] in data.CLUBS
    assert set(v["scores"]) == set(data.CLUBS)
