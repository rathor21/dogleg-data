import data
from model import expected_score

TOLERANCE = 0.15  # strokes; peer review records the achieved max gap

def _mix_average(tier):
    return sum(w * expected_score(L, tier) for L, w in data.LENGTH_MIX)

def test_model_reproduces_published_aggregates():
    worst = 0.0
    for tier in data.PUBLISHED_TIERS:
        gap = abs(_mix_average(tier) - data.BENCHMARK_AGG[tier])
        worst = max(worst, gap)
        assert gap < TOLERANCE, (tier, _mix_average(tier), data.BENCHMARK_AGG[tier])
    print(f"max aggregate gap: {worst:.3f} strokes")

def test_calibration_knobs_inside_declared_ranges():
    for t in data.TIERS:
        assert 0.0 < data.MISHIT[t] < 0.25
        assert 0.2 <= data.TROUBLE_COST[t] <= 2.0
        assert 0.8 <= data.HOLEOUT_SCALE[t] <= 1.6, "holeout scale drifting past defensible range"
