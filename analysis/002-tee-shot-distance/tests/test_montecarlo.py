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

def test_montecarlo_club_and_drive_mean_paths():
    rng = np.random.default_rng(7)
    mc = simulate_hole(400, 20, club="iron", drive_mean=240, n=200_000, rng=rng)
    an = expected_score(400, 20, club="iron", drive_mean=240)
    assert abs(mc - an) < 0.03, (mc, an)
