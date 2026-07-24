import numpy as np
import data
from model import (expected_score, neutral_distance, score_components,
                   _lie_probs, tee_outcomes, benchmark_score)
from montecarlo import simulate_hole

def test_default_width_unchanged():
    # threading the parameter must not move any default-path number
    assert abs(expected_score(400, 15) - 5.204051925307641) < 1e-12
    for tier in (0, 20):
        assert expected_score(400, tier) == expected_score(400, tier, fairway_width=36.0)

def test_narrower_costs_more_wider_less():
    for tier in (5, 15, 25):
        e25 = expected_score(400, tier, fairway_width=25)
        e36 = expected_score(400, tier)
        e45 = expected_score(400, tier, fairway_width=45)
        assert e25 > e36 > e45

def test_decomposition_reproduces_expected_score():
    for tier in (0, 15, 30):
        for club in ("driver", "wood", "seven_iron"):
            for W in (24, 36, 48):
                c = score_components(400, tier, club)
                lp = _lie_probs(data.DRIVER[tier]["sd_lat"] * data.CLUBS[club]["lat_ratio"], fairway_width=W)
                e_direct = expected_score(400, tier, club, fairway_width=W)
                e_decomp = c["base"] + lp["fairway"] * c["gap"] + lp["trouble"] * c["tc_eff"]
                assert abs(e_direct - e_decomp) < 1e-9, (tier, club, W)

def test_cost_line_moves_right_when_narrow():
    r36 = neutral_distance(400, 15)["threshold"]
    r25 = neutral_distance(400, 15, fairway_width=25)["threshold"]
    assert r25 is None or r25 > r36  # narrow hole demands more distance, or never reaches benchmark

def test_benchmark_ignores_width():
    b = benchmark_score(400, 15)
    _ = expected_score(400, 15, fairway_width=25)
    assert benchmark_score(400, 15) == b

def test_montecarlo_matches_at_nondefault_width():
    rng = np.random.default_rng(20260720)
    mc = simulate_hole(400, 15, fairway_width=27, n=200_000, rng=rng)
    an = expected_score(400, 15, fairway_width=27)
    assert abs(mc - an) < 0.03, (mc, an)
