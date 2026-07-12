"""Gate-verified anchors for release 002 (How Far Do You Need to Hit It?).

EVERY numeric literal in this file comes from docs/sources/002_Source_Log.md.
Anchor letters (A..F) cite that log's sections. Values marked MODELED are
derivations or assumptions built on published anchors; each carries a comment
saying what was assumed and, where relevant, a sensitivity range for peer
review. Nothing here was typed from memory.

Tier 30 is always MODELED: neither Shot Scope nor Arccos publishes a clean
30-handicap band (anchor A), so every tier-30 value is a least-squares line
fit across ALL six published bands evaluated at 30, never a single last delta.
"""

from statistics import NormalDist

PUBLISHED_TIERS = [0, 5, 10, 15, 20, 25]
MODELED_TIERS = [30]  # least-squares extrapolation across all published bands
TIERS = PUBLISHED_TIERS + MODELED_TIERS


# ---------------------------------------------------------------------------
# Shared helpers: least-squares line fit (the standing tier-30 rule) and
# linear interpolation on a published table.
# ---------------------------------------------------------------------------

def _lsq_line(xs, ys):
    """Ordinary least-squares line through (xs, ys); returns (intercept, slope)."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    return my - slope * mx, slope


def _lsq_at(xs, ys, x):
    """Value of the least-squares line through (xs, ys), evaluated at x."""
    b, m = _lsq_line(xs, ys)
    return b + m * x


def _interp(x, xs, ys):
    """Linear interpolation, assumes xs sorted and x inside [xs[0], xs[-1]]."""
    for i in range(1, len(xs)):
        if x <= xs[i]:
            t = (x - xs[i - 1]) / (xs[i] - xs[i - 1])
            return ys[i - 1] + t * (ys[i] - ys[i - 1])
    return ys[-1]


# ---------------------------------------------------------------------------
# DRIVER: mean carry-plus-roll (yd), distance sd as a fraction of the mean,
# lateral sd (yd) at driver range.
#
# mean: PUBLISHED, anchor A (Shot Scope P-Avg driver distance via MyGolfSpy):
#   285 / 261 / 259 / 236 / 225 / 204 for handicap 0/5/10/15/20/25.
#   Tier 30 is the least-squares line across all six bands evaluated at 30
#   (about 191 yd). Anchor A's independent Arccos cross-check disagrees on
#   levels (0-4.9 band = 250.0 yd vs Shot Scope 0-hcp = 285); the log flags
#   this and the release discloses Arccos as the sensitivity check.
#
# sd_dist_frac: MODELED, no published anchor found in the hunt. 0.06 flat
#   across tiers; peer-review sensitivity range (0.04, 0.09).
#
# sd_lat: COMPUTED from published values (anchors A + F). Shot Scope publishes
#   fairway-hit % by band (anchor A): 48 / 49 / 49 / 47 / 46 / 47 for
#   0/5/10/15/20/25. Stagner's tee-shot-target analysis (anchor F) publishes
#   the 36-yard fairway those percentages are inverted through, so
#   half-width = 18 yd and, for a centered normal lateral miss,
#       P(fairway) = 2 * Phi(18 / sd) - 1   =>   sd = 18 / Phi_inv((1 + p) / 2).
#   The published percentages are near-flat across bands, so the implied sd_lat
#   is near-flat too (about 27 to 29 yd); that is what the published data says.
#   Cross-check (anchor B, Broadie 2008 Table 1): sigma-alpha 5.4 to 8.1
#   degrees at 248 to 216 yd implies about 23 to 31 yd of lateral sd, the same
#   ballpark. Because the published fairway-hit % is non-monotonic in handicap
#   (49% at 5 and 10 vs 48% at 0), the per-tier sd_lat used by the model is a
#   least-squares line fit across the six computed values (MODELED smoothing;
#   raw inverted values kept below in _SD_LAT_RAW). Tier 30 extrapolates from
#   the same fit.
# ---------------------------------------------------------------------------

_DRIVER_MEAN_PUB = {0: 285, 5: 261, 10: 259, 15: 236, 20: 225, 25: 204}  # anchor A
_FAIRWAY_HIT_PUB = {0: 0.48, 5: 0.49, 10: 0.49, 15: 0.47, 20: 0.46, 25: 0.47}  # anchor A
_SD_DIST_FRAC = 0.06  # MODELED, flat; sensitivity range (0.04, 0.09)

_ND = NormalDist()

# Raw inversion of anchor A fairway-hit % through the 18-yd half-width (anchor F).
_SD_LAT_RAW = {
    t: 18.0 / _ND.inv_cdf((1.0 + p) / 2.0) for t, p in _FAIRWAY_HIT_PUB.items()
}

# MODELED smoothing: least-squares line across the six computed sd_lat values,
# enforcing the physical expectation that dispersion does not shrink as
# handicap rises (the raw values wobble because the published %s do).
_SD_LAT_FIT = {
    t: _lsq_at(PUBLISHED_TIERS, [_SD_LAT_RAW[p] for p in PUBLISHED_TIERS], t)
    for t in TIERS
}

DRIVER = {
    t: {
        "mean": (
            float(_DRIVER_MEAN_PUB[t])
            if t in PUBLISHED_TIERS
            else _lsq_at(PUBLISHED_TIERS, [_DRIVER_MEAN_PUB[p] for p in PUBLISHED_TIERS], t)
        ),
        "sd_dist_frac": _SD_DIST_FRAC,
        "sd_lat": _SD_LAT_FIT[t],
    }
    for t in TIERS
}


# ---------------------------------------------------------------------------
# CLUBS: distance and lateral-dispersion ratios vs driver.
#
# dist_ratio: COMPUTED from published values, anchor C (Shot Scope club ladder
# via MyGolfSpy). Each ratio is the mean of the per-band club/driver ratios,
# rounded to 3 decimals:
#   wood (3-wood, all six bands):
#     261/285, 234/261, 227/259, 215/236, 195/225, 178/204
#     = 0.916, 0.897, 0.876, 0.911, 0.867, 0.873 -> mean 0.890
#   hybrid (3H P-avg, the four published bands 0/5/15/25):
#     219/285, 207/261, 195/236, 161/204
#     = 0.768, 0.793, 0.826, 0.789 -> mean 0.794
#   iron (4-iron, all six bands):
#     223/285, 201/261, 199/259, 186/236, 169/225, 151/204
#     = 0.782, 0.770, 0.768, 0.788, 0.751, 0.740 -> mean 0.767
#
# lat_ratio: MODELED. Under the constant-angle dispersion in anchor B
# (Broadie 2008 reports sigma in degrees), lateral spread already scales with
# distance, and shorter clubs also launch straighter, so
# lat_ratio = dist_ratio * 0.92 for wood/hybrid/iron. The 0.92 loft-tightening
# factor is MODELED with sensitivity range (0.85, 1.0). Driver = 1.0.
# ---------------------------------------------------------------------------

_LOFT_TIGHTEN = 0.92  # MODELED; sensitivity range (0.85, 1.0)

_WOOD_RATIO = round(
    sum(r for r in (261 / 285, 234 / 261, 227 / 259, 215 / 236, 195 / 225, 178 / 204)) / 6, 3
)  # anchor C, 3-wood over driver per band
_HYBRID_RATIO = round(
    sum(r for r in (219 / 285, 207 / 261, 195 / 236, 161 / 204)) / 4, 3
)  # anchor C, 3H P-avg over driver at the four published bands
_IRON_RATIO = round(
    sum(r for r in (223 / 285, 201 / 261, 199 / 259, 186 / 236, 169 / 225, 151 / 204)) / 6, 3
)  # anchor C, 4-iron over driver per band

CLUBS = {
    "driver": {"dist_ratio": 1.0, "lat_ratio": 1.0, "label": "Driver"},
    "wood": {
        "dist_ratio": _WOOD_RATIO,
        "lat_ratio": round(_WOOD_RATIO * _LOFT_TIGHTEN, 3),
        "label": "3-wood",
    },
    "hybrid": {
        "dist_ratio": _HYBRID_RATIO,
        "lat_ratio": round(_HYBRID_RATIO * _LOFT_TIGHTEN, 3),
        "label": "Hybrid",
    },
    "iron": {
        "dist_ratio": _IRON_RATIO,
        "lat_ratio": round(_IRON_RATIO * _LOFT_TIGHTEN, 3),
        "label": "Mid-iron",
    },
}


# ---------------------------------------------------------------------------
# E_HOLEOUT: expected strokes to hole out, {tier: {lie: [(yd, strokes), ...]}}.
# CONSTRUCTED at import by _build_holeout(). MODELED, from published pieces:
#
# Step 1 (PUBLISHED base). Broadie (2011) ShotLink Table 9 tour curves,
#   copied from 001's data.py (anchor D notes the reuse): average strokes for
#   a PGA TOUR player to finish the hole from each distance, fairway and
#   rough. Interpolated to this release's anchor distances (30..225 yd).
#
# Step 2 (MODELED tour-to-scratch offset). Scratch is not tour. Offset
#   derivation: a scratch drive averages 285 yd (anchor A) so on a mid-length
#   par 4 the leftover sits near 100-130 yd; the tour holeout there is about
#   2.9-3.1 strokes, putting the pre-offset expected hole score near 4.0,
#   while anchor E publishes 4.2 for scratch. A flat +0.20 stroke offset
#   closes that gap. MODELED; sensitivity range (0.10, 0.30).
#
# Step 3 (MODELED per-tier scale from anchor E columns). Expected strokes to
#   finish from a tier-typical approach position, built from anchor E's
#   published GIR % and putts-per-GIR:
#       E_pos(tier) = 1 (the approach swing)
#                   + putts_per_GIR          (putting cost)
#                   + (1 - GIR)              (one extra short-game stroke on a miss)
#   The "putts after a chip = putts per GIR" and "one stroke per miss"
#   simplifications are MODELED. Scale s(tier) = E_pos(tier) / E_pos(0):
#   1.000 / 1.054 / 1.108 / 1.150 / 1.210 / 1.228 for 0/5/10/15/20/25.
#   Cross-check (anchor D, Broadie 2008 Table 2): skill-group ratios point the
#   same way; e.g. at 100-150 yd from the fairway, green-hit % falls 63 -> 46
#   -> 25 from Am1 to Am3 and median FRL doubles (8.7% -> 17.3%), so a scale
#   rising with handicap and staying under 2x is consistent with the published
#   skill-group spread. The same table's fairway vs rough columns show the
#   rough penalty holds at every amateur level, which supports Step 4.
#
# Step 4 (MODELED rough treatment). Both lies scale by the same s(tier), so
#   the tour fairway-rough gap grows in proportion with tier. Anchor D's
#   fairway/rough columns confirm the direction (rough always costs amateurs
#   green-hit % and proximity); the proportional size is a modeling choice.
#
# Step 5 (MODELED tier 30). Per (lie, distance) column, least-squares line
#   across the six built tiers evaluated at 30, per the standing rule.
#
# The construction is a level-setter, not the final calibration: Task 7
# adjusts MISHIT and TROUBLE_COST (and HOLEOUT_SCALE if needed) so the full
# model reproduces anchor E's aggregate par-4 scores.
# ---------------------------------------------------------------------------

# Broadie (2011), ShotLink Table 9, copied verbatim from 001's data.py
# (/Users/sunny/Documents/Claude/Projects/Golf Agent/Fairway_vs_Rough_Post/
# source/data.py). PUBLISHED; anchor D records the reuse.
TOUR_DIST = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 220, 240, 260]
TOUR_FAIRWAY = [2.18, 2.40, 2.52, 2.60, 2.66, 2.70, 2.72, 2.75, 2.77, 2.80, 2.85, 2.91, 2.98, 3.08, 3.19, 3.32, 3.45, 3.58]
TOUR_ROUGH = [2.34, 2.59, 2.70, 2.78, 2.87, 2.91, 2.93, 2.96, 2.99, 3.02, 3.08, 3.15, 3.23, 3.31, 3.42, 3.53, 3.64, 3.74]

_TOUR_TO_SCRATCH_OFFSET = 0.20  # MODELED (Step 2); sensitivity range (0.10, 0.30)

_HOLEOUT_DISTANCES = (30, 75, 125, 175, 225)  # anchor grid for this release

# Anchor E published columns used by Step 3 (and stored in BENCHMARK_CONTEXT).
_GIR_PCT_PUB = {0: 0.52, 5: 0.44, 10: 0.36, 15: 0.27, 20: 0.15, 25: 0.09}
_PUTTS_PER_GIR_PUB = {0: 1.85, 5: 1.95, 10: 2.05, 15: 2.10, 20: 2.18, 25: 2.18}


def _tier_scale():
    """Step 3: per-tier holeout scale from anchor E's GIR % and putts per GIR."""
    e_pos = {
        t: 1.0 + _PUTTS_PER_GIR_PUB[t] + (1.0 - _GIR_PCT_PUB[t])
        for t in PUBLISHED_TIERS
    }
    return {t: e_pos[t] / e_pos[0] for t in PUBLISHED_TIERS}


def _build_holeout():
    """Steps 1-5 above: tour base -> scratch offset -> tier scale -> tier 30."""
    scale = _tier_scale()
    tables = {}
    for t in PUBLISHED_TIERS:
        tables[t] = {}
        for lie, tour_ys in (("fairway", TOUR_FAIRWAY), ("rough", TOUR_ROUGH)):
            tables[t][lie] = [
                (d, (_interp(d, TOUR_DIST, tour_ys) + _TOUR_TO_SCRATCH_OFFSET) * scale[t])
                for d in _HOLEOUT_DISTANCES
            ]
    tier30 = {}
    for lie in ("fairway", "rough"):
        tier30[lie] = []
        for i, d in enumerate(_HOLEOUT_DISTANCES):
            ys = [tables[t][lie][i][1] for t in PUBLISHED_TIERS]
            tier30[lie].append((d, _lsq_at(PUBLISHED_TIERS, ys, 30)))
    tables[30] = tier30
    return tables


E_HOLEOUT = _build_holeout()


# ---------------------------------------------------------------------------
# BENCHMARK_AGG: published average par-4 score per tier, aggregate across all
# hole lengths. PUBLISHED, anchor E (Shot Scope via MyGolfSpy). No published
# (band x length) table exists (anchor E FAILED at that resolution), so the
# length-resolved benchmark is model-calibrated against these aggregates
# (see the log's Benchmark decision). Tier 30 is the least-squares line
# across the six published bands evaluated at 30 (about 6.13), MODELED.
# ---------------------------------------------------------------------------

_BENCHMARK_AGG_PUB = {0: 4.2, 5: 4.5, 10: 4.8, 15: 5.1, 20: 5.4, 25: 5.9}  # anchor E

BENCHMARK_AGG = dict(_BENCHMARK_AGG_PUB)
BENCHMARK_AGG[30] = _lsq_at(
    PUBLISHED_TIERS, [_BENCHMARK_AGG_PUB[t] for t in PUBLISHED_TIERS], 30
)  # MODELED

# Anchor E context columns for the published tiers; tier 30 has no published row.
# fairway_pct here is anchor E's par-4 fairway column; it differs a little from
# anchor A's driver-accuracy fairway % (different Shot Scope pulls), and the
# sd_lat inversion above uses anchor A per the log.
BENCHMARK_CONTEXT = {
    0: {"fairway_pct": 0.50, "gir_pct": 0.52, "putts_per_gir": 1.85},
    5: {"fairway_pct": 0.48, "gir_pct": 0.44, "putts_per_gir": 1.95},
    10: {"fairway_pct": 0.45, "gir_pct": 0.36, "putts_per_gir": 2.05},
    15: {"fairway_pct": 0.43, "gir_pct": 0.27, "putts_per_gir": 2.10},
    20: {"fairway_pct": 0.47, "gir_pct": 0.15, "putts_per_gir": 2.18},
    25: {"fairway_pct": 0.46, "gir_pct": 0.09, "putts_per_gir": 2.18},
}


# ---------------------------------------------------------------------------
# GEOMETRY: fairway_half_width = 18 yd, PUBLISHED (anchor F, Stagner's
# 36-yard-wide fairway, the one concrete fairway width the hunt found).
# rough_band (yards of rough beyond the fairway edge before trouble) is
# MODELED with no published anchor; sensitivity range (15, 30).
# ---------------------------------------------------------------------------

GEOMETRY = {"fairway_half_width": 18, "rough_band": 22}


# ---------------------------------------------------------------------------
# MISHIT: per-tier severe-mishit probability off the tee (top/fat/pop-up),
# MODELED calibration knob. Informed by two published-but-incompatible rates
# in the log: Shot Scope's strict penalty % (anchor A: 1/1/2/2/3/3 % for
# 0..25) and Arccos's much broader trouble rate (anchor F: about 17% for low
# handicaps up to 25% for 30+, which includes punch-outs and recoveries).
# The gate addendum reconciles them as a MODELED parameter that Task 7
# calibrates; starting values sit between the two published scales.
# carry_frac: fraction of intended distance a severe mishit carries, MODELED.
# sensitivity_p: multiplicative range on the per-tier probabilities.
# ---------------------------------------------------------------------------

MISHIT = {
    0: 0.01, 5: 0.02, 10: 0.03, 15: 0.05, 20: 0.07, 25: 0.09, 30: 0.11,
    "carry_frac": 0.45,
    "sensitivity_p": (0.5, 1.5),
}

# ---------------------------------------------------------------------------
# TROUBLE_COST: strokes added on top of the rough holeout when the tee ball
# reaches trouble (penalty, trees, forced punch-out). MODELED calibration
# knob, no published per-tier anchor; informed by the same anchor A / F
# penalty and trouble rates as MISHIT. Sensitivity range (0.5, 1.5)
# multiplicative. Task 7 adjusts these within range.
# ---------------------------------------------------------------------------

TROUBLE_COST = {0: 0.55, 5: 0.60, 10: 0.65, 15: 0.70, 20: 0.75, 25: 0.80, 30: 0.85}

# ---------------------------------------------------------------------------
# HOLEOUT_SCALE: per-tier multiplicative scale applied to E_HOLEOUT values by
# the model. The third calibration knob named by the gate addendum: if MISHIT
# and TROUBLE_COST cannot reproduce anchor E's aggregate scores within
# tolerance on their own, Task 7 moves these off 1.0 and records it in the
# log's Calibration section. MODELED.
# ---------------------------------------------------------------------------

HOLEOUT_SCALE = {t: 1.0 for t in TIERS}

# ---------------------------------------------------------------------------
# LENGTH_MIX: par-4 hole-length mix used to average the model's expected score
# into a single per-tier aggregate for calibration against BENCHMARK_AGG.
# MODELED (no published mix; sensitivity-checked per the gate addendum).
# [(hole_yards, weight), ...]; weights sum to 1.
# ---------------------------------------------------------------------------

LENGTH_MIX = [(320, 0.25), (360, 0.30), (400, 0.30), (440, 0.15)]


# ---------------------------------------------------------------------------
# SOURCES: one row per exported constant; log fragments point at the anchor
# sections of docs/sources/002_Source_Log.md.
# ---------------------------------------------------------------------------

SOURCES = {
    "DRIVER": {
        "log": "docs/sources/002_Source_Log.md#anchor-a",
        "status": "means published (anchor A); sd_lat computed-from-published, then LSQ-smoothed across tiers (modeled); sd_dist_frac modeled; tier 30 modeled",
    },
    "CLUBS": {
        "log": "docs/sources/002_Source_Log.md#anchor-c",
        "status": "computed-from-published (dist_ratio); lat_ratio modeled",
    },
    "E_HOLEOUT": {
        "log": "docs/sources/002_Source_Log.md#anchor-d",
        "status": "modeled (constructed from published Broadie 2011 tour curves and anchor D/E ratios)",
    },
    "BENCHMARK_AGG": {
        "log": "docs/sources/002_Source_Log.md#anchor-e",
        "status": "published (tiers 0-25); tier 30 modeled",
    },
    "BENCHMARK_CONTEXT": {
        "log": "docs/sources/002_Source_Log.md#anchor-e",
        "status": "published",
    },
    "GEOMETRY": {
        "log": "docs/sources/002_Source_Log.md#anchor-f",
        "status": "published (fairway_half_width); rough_band modeled",
    },
    "MISHIT": {
        "log": "docs/sources/002_Source_Log.md#anchor-f",
        "status": "calibration-knob (modeled, informed by anchor A/F published rates)",
    },
    "TROUBLE_COST": {
        "log": "docs/sources/002_Source_Log.md#anchor-f",
        "status": "calibration-knob (modeled)",
    },
    "HOLEOUT_SCALE": {
        "log": "docs/sources/002_Source_Log.md#anchor-e",
        "status": "calibration-knob (modeled, per gate addendum)",
    },
    "LENGTH_MIX": {
        "log": "docs/sources/002_Source_Log.md#anchor-e",
        "status": "modeled (calibration length mix, sensitivity-checked)",
    },
    "TOUR_CURVES": {
        "log": "docs/sources/002_Source_Log.md#anchor-d",
        "status": "published (Broadie 2011 Table 9, reused verbatim from 001)",
    },
}
