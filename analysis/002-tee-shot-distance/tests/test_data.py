import data

def test_tiers_declared():
    assert data.PUBLISHED_TIERS == [0, 5, 10, 15, 20, 25]
    assert data.MODELED_TIERS == [30]
    assert data.TIERS == data.PUBLISHED_TIERS + data.MODELED_TIERS

def test_driver_table_monotonic():
    means = [data.DRIVER[t]["mean"] for t in data.TIERS]
    assert all(a > b for a, b in zip(means, means[1:])), "driver distance must fall as handicap rises"
    lats = [data.DRIVER[t]["sd_lat"] for t in data.TIERS]
    assert all(a <= b + 1e-9 for a, b in zip(lats, lats[1:])), "lateral dispersion must not shrink as handicap rises"

def test_club_ratios_ordered():
    r = data.CLUBS
    assert r["driver"]["dist_ratio"] == 1.0
    assert 1.0 > r["wood"]["dist_ratio"] > r["hybrid"]["dist_ratio"] > r["iron"]["dist_ratio"] > 0.5
    for club in r.values():
        assert 0.4 <= club["lat_ratio"] <= 1.0

def test_holeout_tables_well_formed():
    for tier in data.TIERS:
        for lie in ("fairway", "rough"):
            table = data.E_HOLEOUT[tier][lie]
            xs = [p[0] for p in table]
            ys = [p[1] for p in table]
            assert xs == sorted(xs) and len(xs) >= 4
            assert all(a <= b + 1e-9 for a, b in zip(ys, ys[1:])), "strokes to hole out must not fall with distance"

def test_rough_costs_more_at_anchors():
    for tier in data.TIERS:
        fair = dict(data.E_HOLEOUT[tier]["fairway"])
        rough = dict(data.E_HOLEOUT[tier]["rough"])
        for d in set(fair) & set(rough):
            assert rough[d] > fair[d]

def test_holeout_tier_ordering():
    # a worse tier never holes out in fewer expected strokes at shared anchor distances
    for lie in ("fairway", "rough"):
        for i, t_better in enumerate(data.TIERS[:-1]):
            t_worse = data.TIERS[i + 1]
            better = dict(data.E_HOLEOUT[t_better][lie])
            worse = dict(data.E_HOLEOUT[t_worse][lie])
            for d in set(better) & set(worse):
                assert worse[d] >= better[d] - 1e-9

def test_benchmark_agg_monotonic():
    vals = [data.BENCHMARK_AGG[t] for t in data.TIERS]
    assert all(a < b for a, b in zip(vals, vals[1:])), "aggregate par-4 score must rise with handicap"
    assert 3.9 < data.BENCHMARK_AGG[0] < 4.5

def test_every_anchor_carries_source():
    assert isinstance(data.SOURCES, dict)
    for key in ("DRIVER", "CLUBS", "E_HOLEOUT", "BENCHMARK_AGG", "GEOMETRY", "MISHIT", "TROUBLE_COST"):
        assert key in data.SOURCES and "002_Source_Log.md" in data.SOURCES[key]["log"]
