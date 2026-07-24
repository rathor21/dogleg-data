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


def test_driver_trouble_rate_in_published_band():
    """Model trouble rates must stay inside the published Arccos/Shot Scope band.

    Arccos publishes ~17-25% per-drive trouble; Shot Scope strict penalties
    are 1-3%. The model's combined trouble bucket sits between those bands;
    guard 10-20% so a dispersion or geometry edit that breaks the realism
    fails loudly (see the source log's Trouble-rate cross-check).
    """
    from model import tee_outcomes
    for tier in data.TIERS:
        _, w, lies = tee_outcomes("driver", tier)
        trouble = float(sum(wi * lp["trouble"] for wi, lp in zip(w, lies)))
        assert 0.10 < trouble < 0.20, (tier, trouble)
