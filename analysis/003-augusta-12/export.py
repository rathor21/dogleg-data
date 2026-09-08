"""Build the browser-facing export seam for release 003 (issue #10):

  outputs/003_sandbox_grids.json -- lets the browser sandbox recompute
    expected score, water rate, and strokes-versus-optimal for any aim
    point with no server, by reading a grid of pre-computed nodes per
    (tier, pin, wind) and bilinearly interpolating between them.

  outputs/003_manifest.json -- feeds the hero animation: camera constants
    to reproduce art/sketch.py's projection in JS, hole geometry in model
    yards, five curated shot arcs (aim, landing, outcome), and a 1000-point
    Monte Carlo scatter per shot's own scenario. Every landing point comes
    from the model; nothing is hand-placed. Each shot's landing is the
    medoid of its outcome class: 2000 seeded samples are drawn at the
    shot's own (tier, pin, wind, aim), classified into outcome classes, and
    the sample nearest the centroid of its class is kept, so the curated
    arc shows a typical member of the class rather than a random (possibly
    tail) one.

Neither file touches data.py, model.py, optimizer.py, montecarlo.py, or the
results CSV -- this module only reads them. The two JSON blobs are the
site's data contract, the 003 analogue of 002's outputs/tool_data.json.
"""
import csv
import json
import os
import subprocess
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import data      # noqa: E402
import model     # noqa: E402
import optimizer  # noqa: E402
import art.sketch as sketch  # noqa: E402

OUT = os.path.join(HERE, "outputs")
CSV_PATH = os.path.join(OUT, "003_results.csv")
GRIDS_PATH = os.path.join(OUT, "003_sandbox_grids.json")
MANIFEST_PATH = os.path.join(OUT, "003_manifest.json")

# ---------------------------------------------------------------------------
# Sandbox grid axes. 1-yd step across the full search box the optimizer
# itself uses (optimizer.DEFAULT_LATERAL_RANGE_YD / DEFAULT_CARRY_RANGE_YD),
# stated up front rather than discovered by a size fallback: at n_grid=41
# this already produces a ~1-2 MB file (see the size check build_grids
# prints), matching the spec's stated fallback axes exactly, so there is no
# finer default to coarsen from. If a future change grows the file past
# the ~2 MB budget, drop "p_green" first (kept last in each cell dict for
# that reason) before touching the axes. build_grid_for_combo also computes
# a "p_short" (short_fairway probability) grid per combo, cheap to compute
# but NOT cheap to store: adding a fourth full grid per cell pushed the file
# to ~2.27 MB, past budget, so it is returned to callers but not written
# into the JSON cells (region-geometry fix, this pass).
# ---------------------------------------------------------------------------

LATERAL_MIN_YD, LATERAL_MAX_YD = -20.0, 20.0
CARRY_MIN_YD, CARRY_MAX_YD = -20.0, 45.0
AXIS_STEP_YD = 1.0

# Matches model.expected_score's own default integration resolution -- the
# grid cells are exactly what the model would return at that aim point, not
# a cheaper approximation.
GRID_N_GRID = 41
GRID_N_STD = 4.0

REGION_CODES = {
    "green": 0,
    "front_bunker": 1,
    "back_bunker": 2,
    "creek": 3,
    "long_trouble": 4,
    "long_rough": 5,
    "greenside_rough": 6,
    "short_fairway": 7,
}


def git_short_sha():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=HERE, capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except Exception:
        return "unknown"


def generated_from():
    return f"analysis/003-augusta-12 @ {git_short_sha()}"


def _axis(lo, hi, step):
    n = int(round((hi - lo) / step)) + 1
    return [round(lo + i * step, 6) for i in range(n)]


LATERAL_AXIS = _axis(LATERAL_MIN_YD, LATERAL_MAX_YD, AXIS_STEP_YD)
CARRY_AXIS = _axis(CARRY_MIN_YD, CARRY_MAX_YD, AXIS_STEP_YD)


def load_results_csv(path=CSV_PATH):
    """{(tier:int, pin:str, wind:bool): row-dict-of-floats} from
    outputs/003_results.csv, the single source of optimum verdicts."""
    rows = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            tier = int(row["tier"])
            pin = row["pin"]
            wind = row["wind"] == "True"
            rows[(tier, pin, wind)] = {
                "aim_lateral_offset_yd": float(row["aim_lateral_offset_yd"]),
                "aim_carry_adjustment_yd": float(row["aim_carry_adjustment_yd"]),
                "score_optimum": float(row["score_optimum"]),
                "score_at_pin": float(row["score_at_pin"]),
                "score_center_aim": float(row["score_center_aim"]),
                "delta_vs_at_pin_strokes": float(row["delta_vs_at_pin_strokes"]),
                "verdict_label": row["verdict_label"],
            }
    return rows


def _oval_and_mean_shift(tier, wind):
    """(sigma_d, sigma_l, mean_shift_y) exactly as model.expected_score
    builds them, before calling score_for_oval -- duplicated here (not
    imported as a private helper) so this module has one obvious place that
    mirrors model.py's wind handling, matching the docstring's promise that
    grid cells equal model.expected_score at the same aim point."""
    sigma_d, sigma_l = model.oval_for_tier(tier)
    mean_shift_y = 0.0
    if wind:
        mean_shift_y = -data.WIND["carry_penalty_yd"]
        sigma_d = sigma_d * data.WIND["dispersion_inflation"]
        sigma_l = sigma_l * data.WIND["dispersion_inflation"]
    return sigma_d, sigma_l, mean_shift_y


def score_and_region_probs(sigma_d_yd, sigma_l_yd, tier, pin, aim_point, mean_shift_y=0.0, *,
                            green_width_yd=None, front_third_depth_yd=None,
                            n_std=GRID_N_STD, n_grid=GRID_N_GRID):
    """(score, p_water, p_green): one pass over the SAME truncated product-
    Gaussian grid model.score_for_oval integrates (identical grid points,
    identical density weights, identical renormalization), additionally
    accumulating the probability mass landing in the creek ("p_water",
    region == "creek") and on the green ("p_green", region == "green").

    Deliberately duplicates score_for_oval's loop rather than calling
    model.expected_score and a second helper: doing both in one pass costs
    the same as one model.expected_score call instead of two, and the
    identical arithmetic (same numpy ops, same order) means `score` here
    matches model.expected_score bit-for-bit at the same aim point.
    model.py itself is never modified or reimplemented with different math,
    only its published public functions (region_at, _region_strokes) are
    called from here.

    This is the slow, obviously-correct per-aim-point reference: one call
    per aim point, same as model.expected_score's own cost. build_sandbox_
    grids uses the vectorized bulk builder below instead (same formulas,
    numpy-broadcast over every aim point and integration node in a combo at
    once) to build the full grid in seconds rather than minutes; tests/
    test_export.py's round-trip test spot-checks the fast builder's stored
    values against this slow function (and against model.expected_score
    directly) at a handful of nodes, so an error in the vectorized
    reimplementation below cannot slip past uncaught.
    """
    sigma_d = max(sigma_d_yd, 1e-6)
    sigma_l = max(sigma_l_yd, 1e-6)
    mean_x, mean_y = aim_point[0], aim_point[1] + mean_shift_y

    ys = np.linspace(mean_y - n_std * sigma_d, mean_y + n_std * sigma_d, n_grid)
    xs = np.linspace(mean_x - n_std * sigma_l, mean_x + n_std * sigma_l, n_grid)
    wy = np.exp(-0.5 * ((ys - mean_y) / sigma_d) ** 2)
    wx = np.exp(-0.5 * ((xs - mean_x) / sigma_l) ** 2)
    wy = wy / wy.sum()
    wx = wx / wx.sum()

    total = 0.0
    p_water = 0.0
    p_green = 0.0
    for yi, wyi in zip(ys, wy):
        if wyi == 0.0:
            continue
        for xi, wxi in zip(xs, wx):
            w = wyi * wxi
            if w == 0.0:
                continue
            region, short_sided = model.region_at(float(xi), float(yi), pin,
                                                    green_width_yd=green_width_yd,
                                                    front_third_depth_yd=front_third_depth_yd)
            total += w * model._region_strokes(region, short_sided, tier, float(xi), float(yi), pin,
                                                green_width_yd=green_width_yd,
                                                front_third_depth_yd=front_third_depth_yd)
            if region == "creek":
                p_water += w
            elif region == "green":
                p_green += w
    return 1.0 + total, p_water, p_green


def _recovery_leg_constants(tier):
    """The four possible non-green recovery-leg prices for `tier`, each
    independent of WHERE on the miss side the ball sits (model._recovery_
    strokes' formula only branches on sand/short-sided/trouble, never on
    the exact (x, y)) -- computed once per tier via model.py's own function
    so the vectorized builder below never re-derives the recovery pricing
    formula, only broadcasts these four numbers across the short-sided
    mask."""
    return {
        "nonsand_easy": model._recovery_strokes(tier, False, sand=False),
        "nonsand_short": model._recovery_strokes(tier, True, sand=False),
        "sand_easy": model._recovery_strokes(tier, False, sand=True),
        "sand_short": model._recovery_strokes(tier, True, sand=True),
    }


def build_grid_for_combo(tier, pin, wind, *, n_grid=GRID_N_GRID, n_std=GRID_N_STD):
    """(score, p_water, p_green, p_short): the full (len(CARRY_AXIS) x
    len(LATERAL_AXIS)) grids for one (tier, pin, wind) combo, in one
    vectorized pass.

    Mirrors model.score_for_oval / model.region_at / model._region_strokes
    exactly, but broadcast over every (carry, lateral) aim point and every
    (y, x) integration node in the combo at once with numpy, instead of
    Python loops calling those functions one aim point and one grid cell at
    a time (score_and_region_probs above, and by extension model.
    expected_score, cost ~2 ms per aim point; this module needs 2706 aim
    points x 30 combos = ~81000 of them, which would take minutes). The
    boundary comparisons (front/back edge, bunker ranges, short-siding) are
    reproduced here as numpy comparisons rather than calling region_at
    itself, since region_at's Python `if`/`elif` chain does not accept
    array inputs; model._front_edge_yd/_back_edge_yd (pure arithmetic) ARE
    called directly on numpy arrays, unmodified. tests/test_export.py's
    round-trip test cross-checks this function's output against model.
    expected_score and against score_and_region_probs above at sampled
    nodes, so a mismatch here cannot pass silently.
    """
    sigma_d, sigma_l, mean_shift_y = _oval_and_mean_shift(tier, wind)
    sigma_d = max(sigma_d, 1e-6)
    sigma_l = max(sigma_l, 1e-6)
    geom = model._resolve_geometry()
    p = data.PINS[pin]
    px, py = p["x"], p["y"]
    front_frac, back_frac = p["front_frac"], p["back_frac"]
    half_width = geom["width"] / 2.0
    left_edge, right_edge = -half_width, half_width

    rel_y = np.linspace(-n_std * sigma_d, n_std * sigma_d, n_grid)
    rel_x = np.linspace(-n_std * sigma_l, n_std * sigma_l, n_grid)
    wy = np.exp(-0.5 * (rel_y / sigma_d) ** 2)
    wy = wy / wy.sum()
    wx = np.exp(-0.5 * (rel_x / sigma_l) ** 2)
    wx = wx / wx.sum()
    weight4d = np.outer(wy, wx)[None, None, :, :]

    carry_arr = np.array(CARRY_AXIS)
    lateral_arr = np.array(LATERAL_AXIS)
    mean_y_arr = py + carry_arr + mean_shift_y
    mean_x_arr = px + lateral_arr

    # (n_carry, n_lateral, n_grid, n_grid): absolute landing coordinates for
    # every (aim point, integration node) pair in this combo at once.
    YY = mean_y_arr[:, None, None, None] + rel_y[None, None, :, None]
    XX = mean_x_arr[None, :, None, None] + rel_x[None, None, None, :]

    front_edge_arr = model._front_edge_yd(XX, geom)
    back_edge_arr = model._back_edge_yd(XX, geom)

    m_green = (YY >= front_edge_arr) & (YY <= back_edge_arr) & (XX >= left_edge) & (XX <= right_edge)
    m_front_side = (~m_green) & (YY < front_edge_arr)
    m_back_side = (~m_green) & (~m_front_side) & (YY > back_edge_arr)
    m_greenside_rough = (~m_green) & (~m_front_side) & (~m_back_side)

    on_front_side = YY < py
    is_short_sided = (on_front_side & (front_frac < 0.5)) | ((~on_front_side) & (back_frac < 0.5))

    bunker_lo, bunker_hi = data.HOLE["front_bunker_x_range"]
    bunker_front_arr = front_edge_arr - data.HOLE["front_bunker_depth_yd"]
    m_front_bunker = (m_front_side & (XX >= bunker_lo) & (XX <= bunker_hi)
                      & (YY >= bunker_front_arr) & (YY < front_edge_arr))
    # Finite creek band (region-geometry fix, this pass): only the strip
    # between the front edge and CREEK_WIDTH_YD + BANK_ROLLBACK_YD short of
    # it is "creek" -- mirrors model.region_at exactly. Anything short of
    # that band, short of the pin's front side and not in the front bunker,
    # is "short_fairway": a pitch over the water from the fairway, not a
    # hazard. m_creek is NOT "everything short of the green" any more.
    creek_near_edge_arr = front_edge_arr - (data.CREEK_WIDTH_YD + data.BANK_ROLLBACK_YD)
    m_creek = m_front_side & (~m_front_bunker) & (YY >= creek_near_edge_arr)
    m_short_fairway = m_front_side & (~m_front_bunker) & (YY < creek_near_edge_arr)

    bunker_back_arr = back_edge_arr + data.HOLE["back_bunker_depth_yd"]
    m_back_bunker = np.zeros_like(m_back_side)
    for lo, hi in data.HOLE["back_bunker_x_ranges"]:
        m_back_bunker = m_back_bunker | (m_back_side & (XX >= lo) & (XX <= hi)
                                          & (YY > back_edge_arr) & (YY <= bunker_back_arr))
    trouble_back_arr = bunker_back_arr + data.LONG_TROUBLE_BUFFER_YD
    m_long_trouble = m_back_side & (~m_back_bunker) & (YY > trouble_back_arr)
    m_long_rough = m_back_side & (~m_back_bunker) & (~m_long_trouble)

    # Green: vectorized model.putt_probabilities / model._green_strokes,
    # using np.interp for model._lerp_table (same flat-extrapolation
    # behavior outside the table's own range).
    dist_ft = np.sqrt((XX - px) ** 2 + (YY - py) ** 2) * model.FT_PER_YD
    make_table = data.AMATEUR_MAKE_PCT_BY_BAND[tier]
    mk_keys = sorted(make_table)
    mk_vals = [make_table[k] for k in mk_keys]
    p1 = np.interp(dist_ft, mk_keys, mk_vals)
    tp_keys = sorted(data.TOUR_THREE_PUTT_PCT_BY_FT)
    tp_vals = [data.TOUR_THREE_PUTT_PCT_BY_FT[k] for k in tp_keys]
    tour_p3_shape = np.where(dist_ft <= 5.0, 0.0, np.interp(dist_ft, tp_keys, tp_vals))
    p3_raw = tour_p3_shape * data.AMATEUR_THREE_PUTT_SHAPE_SCALE[tier]
    p3 = np.minimum(p3_raw, np.maximum(0.0, 1.0 - p1))
    p2 = np.maximum(0.0, 1.0 - p1 - p3)
    green_strokes = p1 + 2.0 * p2 + 3.0 * p3

    rc = _recovery_leg_constants(tier)
    recovery_nonsand = np.where(is_short_sided, rc["nonsand_short"], rc["nonsand_easy"])
    recovery_sand = np.where(is_short_sided, rc["sand_short"], rc["sand_easy"])
    creek_strokes = data.CREEK_PENALTY_STROKES + recovery_nonsand
    rough_strokes = recovery_nonsand
    bunker_strokes = recovery_sand

    updown = data.UP_AND_DOWN_PCT[tier]
    updown = min(0.95, updown * data.ROUGH_RECOVERY_EASE)
    updown = updown * data.LONG_TROUBLE_UPDOWN_MULT
    e_easy = updown * 2.0 + (1.0 - updown) * data.MISSED_UP_AND_DOWN_STROKES
    e_short = e_easy * data.SHORT_SIDE_PENALTY
    hazard_easy = data.CREEK_PENALTY_STROKES + rc["nonsand_easy"]
    hazard_short = data.CREEK_PENALTY_STROKES + rc["nonsand_short"]
    overshoot = np.maximum(0.0, YY - trouble_back_arr)
    blend = 1.0 - np.exp(-overshoot / data.LONG_TROUBLE_FALLOFF_YD)
    e_arr = np.where(is_short_sided, e_short, e_easy)
    hazard_arr = np.where(is_short_sided, hazard_short, hazard_easy)
    long_trouble_strokes = e_arr * (1.0 - blend) + hazard_arr * blend

    # short_fairway distance falloff (region-geometry fix): mirrors
    # model._recovery_strokes's far_short_yd blend exactly -- fades this
    # leg's up-and-down odds toward zero the farther short of the creek
    # band's own near edge the miss sits, converging on MISSED_UP_AND_DOWN_
    # STROKES (never a hazard-like price). Without this, a flat price with
    # no distance term reproduces #8's "no interior minimum" defect on the
    # short side of the green (see data.SHORT_FAIRWAY_FALLOFF_YD's comment).
    far_short = np.maximum(0.0, creek_near_edge_arr - YY)
    short_blend = 1.0 - np.exp(-far_short / data.SHORT_FAIRWAY_FALLOFF_YD)
    ceiling_easy = data.MISSED_UP_AND_DOWN_STROKES
    ceiling_short = data.MISSED_UP_AND_DOWN_STROKES * data.SHORT_SIDE_PENALTY
    ceiling_arr = np.where(is_short_sided, ceiling_short, ceiling_easy)
    short_fairway_recovery = rough_strokes * (1.0 - short_blend) + ceiling_arr * short_blend

    # Pitch-over-water risk fix (rev 5, issue #8): mirrors model.
    # _short_fairway_strokes exactly -- (1 - p) * recovery + p *
    # (CREEK_PENALTY_STROKES + 1.0 + recovery_after_drop), where
    # recovery_after_drop is the same non-sand recovery leg as
    # `rough_strokes` above (a drop and replay right at the creek's edge,
    # never carrying the far_short_yd falloff `short_fairway_recovery`
    # itself carries). p = data.PITCH_OVER_WATER_DUNK_PCT[tier], a scalar
    # for this whole grid (build_grid_for_combo is called once per tier).
    dunk_pct = data.PITCH_OVER_WATER_DUNK_PCT[tier]
    dunk_strokes = data.CREEK_PENALTY_STROKES + 1.0 + rough_strokes
    short_fairway_strokes = (1.0 - dunk_pct) * short_fairway_recovery + dunk_pct * dunk_strokes

    strokes = np.where(m_green, green_strokes, 0.0)
    strokes = np.where(m_creek, creek_strokes, strokes)
    strokes = np.where(m_short_fairway, short_fairway_strokes, strokes)
    strokes = np.where(m_front_bunker | m_back_bunker, bunker_strokes, strokes)
    strokes = np.where(m_long_trouble, long_trouble_strokes, strokes)
    strokes = np.where(m_long_rough | m_greenside_rough, rough_strokes, strokes)

    score = 1.0 + (weight4d * strokes).sum(axis=(2, 3))
    p_water = (weight4d * m_creek).sum(axis=(2, 3))  # short_fairway is explicitly excluded -- it is not water
    p_green = (weight4d * m_green).sum(axis=(2, 3))
    p_short = (weight4d * m_short_fairway).sum(axis=(2, 3))
    return score, p_water, p_green, p_short


def build_sandbox_grids(results=None):
    results = results if results is not None else load_results_csv()

    pins = {
        key: {**{k: v for k, v in p.items()}, "label": p["label"], "x": p["x"], "y": p["y"]}
        for key, p in data.PINS.items()
    }

    modeled = [
        {
            "name": "anisotropy_ratio", "value": data.ANISOTROPY["ratio"],
            "range": data.ANISOTROPY["range"], **data.SOURCES["ANISOTROPY"],
        },
        {
            "name": "front_third_depth_yd",
            "value": sum(data.HOLE["front_third_depth_yd_range"]) / 2.0,
            "range": data.HOLE["front_third_depth_yd_range"], **data.SOURCES["HOLE"],
        },
        {
            "name": "wind_carry_penalty_yd", "value": data.WIND["carry_penalty_yd"],
            "range": data.WIND["carry_penalty_range_yd"], **data.SOURCES["WIND"],
        },
        {
            "name": "wind_dispersion_inflation", "value": data.WIND["dispersion_inflation"],
            "range": data.WIND["dispersion_inflation_range"], **data.SOURCES["WIND"],
        },
        {
            "name": "up_and_down_pct_by_tier", "value": data.UP_AND_DOWN_PCT,
            "range": None, **data.SOURCES["UP_AND_DOWN_PCT"],
        },
    ]

    cells = {}
    for tier in data.TIERS:
        for pin in data.PINS:
            for wind in (False, True):
                # p_short (short_fairway probability) is intentionally not
                # stored below -- see the module-level budget comment above.
                score, p_water, p_green, _p_short = build_grid_for_combo(tier, pin, wind)
                score_grid = np.round(score, 4).tolist()
                water_grid = np.round(p_water, 4).tolist()
                green_grid = np.round(p_green, 4).tolist()

                row = results[(tier, pin, wind)]
                verdict = optimizer.Verdict(
                    lateral_offset_yd=row["aim_lateral_offset_yd"],
                    carry_adjustment_yd=row["aim_carry_adjustment_yd"],
                    score_optimum=row["score_optimum"],
                    score_at_pin=row["score_at_pin"],
                    delta=row["score_at_pin"] - row["score_optimum"],
                )
                recomputed_label = optimizer.verdict_label(verdict)
                assert recomputed_label == row["verdict_label"], (
                    f"verdict label mismatch for tier={tier} pin={pin} wind={wind}: "
                    f"csv={row['verdict_label']!r} recomputed={recomputed_label!r}"
                )

                key = f"{tier}|{pin}|{int(wind)}"
                cells[key] = {
                    "score": score_grid,
                    "p_water": water_grid,
                    "optimum": {
                        "lateral_offset_yd": row["aim_lateral_offset_yd"],
                        "carry_adjustment_yd": row["aim_carry_adjustment_yd"],
                        "score": row["score_optimum"],
                    },
                    "score_at_pin": row["score_at_pin"],
                    "score_center_aim": row["score_center_aim"],
                    "verdict_label": row["verdict_label"],
                    "p_green": green_grid,
                }

    return {
        "schema": "dogleg-003-sandbox-grids/1",
        "generated_from": generated_from(),
        "tiers": list(data.TIERS),
        "pins": pins,
        "wind": data.WIND,
        "axes": {
            "lateral_offset_yd": LATERAL_AXIS,
            "carry_adjustment_yd": CARRY_AXIS,
        },
        "tossup_threshold_strokes": optimizer.TOSSUP_THRESHOLD_STROKES,
        "modeled": modeled,
        "cells": cells,
    }


# ---------------------------------------------------------------------------
# Reference lookup: the formula the browser sandbox ports to JS.
# ---------------------------------------------------------------------------

def _axis_fraction(axis, value):
    """(index, frac) so that axis[index] + frac*(axis[index+1]-axis[index])
    == clamp(value, axis[0], axis[-1]). index is clamped to
    [0, len(axis)-2] so a value at or past the top edge interpolates within
    the last cell at frac=1.0 rather than indexing out of range."""
    lo, hi = axis[0], axis[-1]
    v = min(max(value, lo), hi)
    step = axis[1] - axis[0]
    idx = int((v - lo) / step)
    idx = min(idx, len(axis) - 2)
    frac = (v - axis[idx]) / step
    frac = min(max(frac, 0.0), 1.0)
    return idx, frac


def _bilinear(grid, row_axis, col_axis, row_val, col_val):
    ri, rf = _axis_fraction(row_axis, row_val)
    ci, cf = _axis_fraction(col_axis, col_val)
    v00 = grid[ri][ci]
    v01 = grid[ri][ci + 1]
    v10 = grid[ri + 1][ci]
    v11 = grid[ri + 1][ci + 1]
    top = v00 + (v01 - v00) * cf
    bot = v10 + (v11 - v10) * cf
    return top + (bot - top) * rf


def sandbox_lookup(grids, tier, pin, wind, lateral, carry):
    """dict(score, p_water, p_green, delta_vs_optimum, tossup) for an
    arbitrary aim point, bilinearly interpolated between the four grid
    nodes surrounding (lateral, carry), clamped to the axes' range. The
    browser implements this identical formula (axis lookup + bilinear
    blend) directly against the same JSON so no server round-trip is
    needed."""
    key = f"{tier}|{pin}|{int(bool(wind))}"
    cell = grids["cells"][key]
    lateral_axis = grids["axes"]["lateral_offset_yd"]
    carry_axis = grids["axes"]["carry_adjustment_yd"]

    score = _bilinear(cell["score"], carry_axis, lateral_axis, carry, lateral)
    p_water = _bilinear(cell["p_water"], carry_axis, lateral_axis, carry, lateral)
    result = {"score": score, "p_water": p_water}
    if "p_green" in cell:
        result["p_green"] = _bilinear(cell["p_green"], carry_axis, lateral_axis, carry, lateral)
    delta_vs_optimum = score - cell["optimum"]["score"]
    result["delta_vs_optimum"] = delta_vs_optimum
    result["tossup"] = abs(delta_vs_optimum) <= grids["tossup_threshold_strokes"]
    return result


# ---------------------------------------------------------------------------
# Manifest: camera, hole geometry, five curated shots, MC scatter.
# ---------------------------------------------------------------------------

def camera_block():
    regions, landmarks = sketch.build_scene()
    formula = (
        "lerp(a, b, t) = a + (b - a) * t. "
        "screen_y(y_yd): if y_yd <= 0, t = clamp((y_yd - y_min_yd) / (0 - y_min_yd), 0, 1), "
        "return lerp(ground_near_px, tee_front_px, t); "
        "elif y_yd <= y_break_yd, t = clamp(y_yd / y_break_yd, 0, 1), "
        "return lerp(tee_front_px, mid_px, t); "
        "else t = max(0, (y_yd - y_break_yd) / (y_max_yd - y_break_yd)), "
        "return lerp(mid_px, horizon_px, t). "
        "half_width_px(y_yd): t_lin = max(0, (y_yd - y_min_yd) / (y_max_yd - y_min_yd)), "
        "t_eased = t_lin ** gamma_x, "
        "return lerp(near_half_width_px, far_half_width_px, t_eased). "
        "project(x_yd, y_yd): px = canvas_width / 2 + x_yd * (half_width_px(y_yd) / frame_half_width_yd), "
        "py = screen_y(y_yd)."
    )
    return {
        "canvas": {"width": sketch.CANVAS_W, "height": sketch.CANVAS_H},
        "horizon_px": sketch.HORIZON_PX,
        "y_min_yd": sketch.Y_MIN_YD,
        "y_max_yd": sketch.Y_MAX_YD,
        "y_break_yd": landmarks["y_break_yd"],
        "ground_near_px": sketch.GROUND_NEAR_PX,
        "tee_front_px": sketch.TEE_FRONT_PX,
        "mid_px": sketch.MID_PX,
        "gamma_x": sketch.GAMMA_X,
        "near_half_width_px": sketch.NEAR_HALF_WIDTH_PX,
        "far_half_width_px": sketch.FAR_HALF_WIDTH_PX,
        "frame_half_width_yd": sketch.FRAME_HALF_WIDTH_YD,
        "formula": formula,
    }, regions, landmarks


def geometry_yd_block(regions, landmarks):
    bunkers = [{"name": "front", "polygon": regions["front_bunker"]}]
    for i, bb in enumerate(regions["back_bunkers"]):
        bunkers.append({"name": f"back_{i + 1}", "polygon": bb["poly"]})

    return {
        "tee_box": landmarks["tee_poly_yd"],
        "fairway": regions["fairway"],
        "creek": {
            "polygon": regions["creek"],
            "near_bank": landmarks["creek_near_bank_samples_yd"],
            "far_bank": landmarks["creek_far_bank_samples_yd"],
        },
        "green": regions["green"],
        "bunkers": bunkers,
        "pins": {key: {"x": p["x"], "y": p["y"]} for key, p in data.PINS.items()},
        "horizon": {
            "y_min_yd": sketch.Y_MIN_YD,
            "y_break_yd": landmarks["y_break_yd"],
            "y_max_yd": sketch.Y_MAX_YD,
        },
    }


# Deterministic tee positions: five distinct x's spread across the tee box
# width (+/- TEE_BOX_HALF_WIDTH_YD), all at the box's own mid-depth y (the
# same y sketch.py's tee_center_yd uses) -- the prototype's "widen the fan"
# requirement, satisfied by construction rather than by hand-picking points.
_TEE_Y_YD = sketch.TEE_BOX_BACK_YD / 2.0
_TEE_XS_YD = np.linspace(
    -sketch.TEE_BOX_HALF_WIDTH_YD * 0.8, sketch.TEE_BOX_HALF_WIDTH_YD * 0.8, 5
).tolist()

SHOT_SPECS = [
    {
        "id": "pin_hunter", "label": "Pin hunter",
        "tier": 15, "pin": "sunday", "wind": False,
        "aim": None,  # resolved to the pin itself below
        "shape": "straight", "curve_yd": 0,
        # "mode_nongreen": the outcome class is not fixed in advance. It is
        # the most frequent non-green class among the shot's own sampled
        # population, resolved in _select_medoid_landing and disclosed via
        # the manifest's outcome_class / class_frequencies fields.
        "designated_class": "mode_nongreen",
        "seed": 15001,
    },
    {
        "id": "safe_center", "label": "Safe center",
        "tier": 15, "pin": "sunday", "wind": False,
        "aim": "csv_optimum",
        "shape": "straight", "curve_yd": 0,
        "designated_class": "green",
        "seed": 15002,
    },
    {
        "id": "draw", "label": "Working draw",
        "tier": 10, "pin": "center", "wind": False,
        "aim": "csv_optimum",
        "shape": "draw", "curve_yd": -4,
        "designated_class": "green",
        "seed": 10003,
    },
    {
        "id": "fade", "label": "Leaked fade",
        "tier": 10, "pin": "sunday", "wind": False,
        "aim": None,  # the pin itself
        "shape": "fade", "curve_yd": 4,
        "designated_class": "mode_nongreen",
        "seed": 10004,
    },
    {
        "id": "under_clubbed", "label": "Under-clubbed",
        "tier": 20, "pin": "center", "wind": False,
        "aim": "carry_short_8",
        "shape": "straight", "curve_yd": 0,
        "designated_class": "water",
        "seed": 20005,
    },
]


def _resolve_aim(spec, results):
    pin_x, pin_y = data.PINS[spec["pin"]]["x"], data.PINS[spec["pin"]]["y"]
    if spec["aim"] is None:
        return pin_x, pin_y
    if spec["aim"] == "csv_optimum":
        row = results[(spec["tier"], spec["pin"], False)]
        return pin_x + row["aim_lateral_offset_yd"], pin_y + row["aim_carry_adjustment_yd"]
    if spec["aim"] == "carry_short_8":
        return pin_x, pin_y - 8.0
    raise ValueError(spec["aim"])


def _classify_outcome(region, short_sided):
    if region == "creek":
        return "water"
    if region in ("front_bunker", "back_bunker"):
        return "bunker"
    if region == "short_fairway":
        # Displayed on the site as "short of the creek" -- a pitch over
        # Rae's Creek from the fairway, not a hazard outcome (region-
        # geometry fix, this pass). Not folded into "short_sided": a
        # short_fairway miss can still be short-sided (the pin's own
        # front_frac rule applies here too), but the class name should
        # read as "played short," not "trouble," either way.
        return "short"
    if short_sided:
        return "short_sided"
    if region in ("long_trouble", "long_rough"):
        return "long"
    return region


MEDOID_N_SAMPLES = 2000


def _sample_landings(tier, pin, aim, wind, seed, n_samples):
    """(xs, ys): n_samples seeded Monte Carlo landings at (tier, pin, aim,
    wind) -- the same distributions montecarlo.simulate_amateur draws,
    drawn ys-then-xs from one rng so the sequence is reproducible from the
    seed alone (tests/test_export.py's reproducibility test replays this
    exact call)."""
    rng = np.random.default_rng(seed)
    sigma_d, sigma_l = model.oval_for_tier(tier)
    mean_shift_y = 0.0
    if wind:
        mean_shift_y = -data.WIND["carry_penalty_yd"]
        sigma_d = sigma_d * data.WIND["dispersion_inflation"]
        sigma_l = sigma_l * data.WIND["dispersion_inflation"]
    mean_x, mean_y = aim[0], aim[1] + mean_shift_y
    ys = rng.normal(mean_y, sigma_d, n_samples)
    xs = rng.normal(mean_x, sigma_l, n_samples)
    return xs, ys


def _select_medoid_landing(tier, pin, aim, wind, designated_class, seed, n_samples=MEDOID_N_SAMPLES):
    """Curated-shot landing selection (issue #10 fix): draw n_samples seeded
    Monte Carlo samples at (tier, pin, aim, wind), classify each one with
    model.region_at + _classify_outcome, resolve the shot's outcome class,
    then return the in-class sample nearest (Euclidean, yards) to that
    subset's centroid -- the medoid -- instead of the first sample that
    happened to match. The first-match rule picked whatever tail event the
    seed drew first; the medoid is the typical member of the class.

    `designated_class` is either a fixed class ("green", "water") or the
    sentinel "mode_nongreen", meaning the class is not chosen in advance:
    it is the most frequent non-green class actually drawn, so a pin-seeking
    shot's miss bucket (short-sided, bunker, long, ...) is disclosed by the
    sample rather than assumed.

    Returns a dict: x, y, region, short_sided, outcome_class, sample_index
    (index into this draw, so seed + sample_index reproduces the landing),
    n_samples, n_in_class, class_frequencies (sampled share of every class
    drawn, keyed by class name), and selection_rule (a prose disclosure
    string stored in the manifest).
    """
    xs, ys = _sample_landings(tier, pin, aim, wind, seed, n_samples)
    regions = [None] * n_samples
    short_sideds = [None] * n_samples
    classes = [None] * n_samples
    for i in range(n_samples):
        region, short_sided = model.region_at(float(xs[i]), float(ys[i]), pin)
        regions[i] = region
        short_sideds[i] = short_sided
        classes[i] = _classify_outcome(region, short_sided)

    counts = Counter(classes)
    class_frequencies = {cls: round(count / n_samples, 4) for cls, count in sorted(counts.items())}

    if designated_class == "mode_nongreen":
        nongreen_counts = {cls: c for cls, c in counts.items() if cls != "green"}
        if not nongreen_counts:
            raise RuntimeError(f"no non-green samples drawn for tier={tier} pin={pin} "
                                f"aim={aim} wind={wind} seed={seed} n_samples={n_samples}")
        # Ties broken alphabetically for determinism; at n_samples=2000 an
        # exact tie between two miss classes is not expected in practice.
        outcome_class = max(sorted(nongreen_counts), key=lambda c: nongreen_counts[c])
    else:
        outcome_class = designated_class

    in_class_idx = [i for i in range(n_samples) if classes[i] == outcome_class]
    n_in_class = len(in_class_idx)
    if n_in_class == 0:
        raise RuntimeError(f"no samples classified as {outcome_class!r} for tier={tier} pin={pin} "
                            f"aim={aim} wind={wind} seed={seed} n_samples={n_samples}")

    centroid_x = float(np.mean([xs[i] for i in in_class_idx]))
    centroid_y = float(np.mean([ys[i] for i in in_class_idx]))
    medoid_i = min(in_class_idx, key=lambda i: (xs[i] - centroid_x) ** 2 + (ys[i] - centroid_y) ** 2)

    return {
        "x": float(xs[medoid_i]),
        "y": float(ys[medoid_i]),
        "region": regions[medoid_i],
        "short_sided": short_sideds[medoid_i],
        "outcome_class": outcome_class,
        "sample_index": medoid_i,
        "n_samples": n_samples,
        "n_in_class": n_in_class,
        "class_frequencies": class_frequencies,
        "selection_rule": (
            f"medoid: drew {n_samples} seeded Monte Carlo samples at this shot's "
            f"(tier, pin, wind, aim); kept the {n_in_class} classified as "
            f"outcome_class '{outcome_class}'; the landing is the kept sample "
            "nearest (Euclidean distance, yards) to that subset's centroid."
        ),
    }


def build_shots(results):
    shots = []
    for i, spec in enumerate(SHOT_SPECS):
        aim = _resolve_aim(spec, results)
        selection = _select_medoid_landing(
            spec["tier"], spec["pin"], aim, spec["wind"], spec["designated_class"], spec["seed"]
        )
        expected_score_at_aim = model.expected_score(spec["tier"], spec["pin"], aim, wind=spec["wind"])
        pin_x, pin_y = data.PINS[spec["pin"]]["x"], data.PINS[spec["pin"]]["y"]
        distance_from_pin_yd = round(float(np.hypot(selection["x"] - pin_x, selection["y"] - pin_y)), 4)
        shots.append({
            "id": spec["id"],
            "label": spec["label"],
            "tier": spec["tier"],
            "pin": spec["pin"],
            "wind": spec["wind"],
            "aim": {"x": round(aim[0], 4), "y": round(aim[1], 4)},
            "shape": spec["shape"],
            "curve_yd": spec["curve_yd"],
            "tee": {"x": round(float(_TEE_XS_YD[i]), 4), "y": round(float(_TEE_Y_YD), 4)},
            "landing": {"x": round(selection["x"], 4), "y": round(selection["y"], 4)},
            "region": selection["region"],
            "short_sided": selection["short_sided"],
            "outcome_class": selection["outcome_class"],
            "distance_from_pin_yd": distance_from_pin_yd,
            "expected_score_at_aim": round(expected_score_at_aim, 4),
            "seed": spec["seed"],
            "n_samples": selection["n_samples"],
            "n_in_class": selection["n_in_class"],
            "sample_index": selection["sample_index"],
            "class_frequencies": selection["class_frequencies"],
            "selection_rule": selection["selection_rule"],
        })
    return shots


def build_scatter(shots, n=1000):
    """1000 seeded MC landings per shot's own (tier, pin, wind, aim)
    scenario -- a different, fixed seed from the shot's own landing draw
    (scatter seed = 900000 + landing seed) so the single curated landing
    point and the background scatter cloud are independently reproducible."""
    scatter = {}
    for shot in shots:
        key = f"{shot['tier']}|{shot['pin']}|{int(shot['wind'])}"
        if key in scatter:
            continue
        seed = 900_000 + shot["seed"]
        rng = np.random.default_rng(seed)
        tier, pin, wind = shot["tier"], shot["pin"], shot["wind"]
        aim = (shot["aim"]["x"], shot["aim"]["y"])
        sigma_d, sigma_l = model.oval_for_tier(tier)
        mean_shift_y = 0.0
        if wind:
            mean_shift_y = -data.WIND["carry_penalty_yd"]
            sigma_d = sigma_d * data.WIND["dispersion_inflation"]
            sigma_l = sigma_l * data.WIND["dispersion_inflation"]
        mean_x, mean_y = aim[0], aim[1] + mean_shift_y
        ys = rng.normal(mean_y, sigma_d, n)
        xs = rng.normal(mean_x, sigma_l, n)
        points = []
        for xi, yi in zip(xs, ys):
            region, _short_sided = model.region_at(float(xi), float(yi), pin)
            points.append([round(float(xi), 3), round(float(yi), 3), REGION_CODES[region]])
        scatter[key] = {"aim": {"x": round(aim[0], 4), "y": round(aim[1], 4)}, "points": points}
    return scatter


def build_manifest(results=None):
    results = results if results is not None else load_results_csv()
    camera, regions, landmarks = camera_block()
    geometry_yd = geometry_yd_block(regions, landmarks)
    with open(os.path.join(HERE, "art", "sketch_coords.json")) as f:
        landmarks_px = json.load(f)
    shots = build_shots(results)
    scatter = build_scatter(shots)

    return {
        "schema": "dogleg-003-manifest/1",
        "generated_from": generated_from(),
        "camera": camera,
        "landmarks_px": landmarks_px,
        "geometry_yd": geometry_yd,
        "shots": shots,
        "scatter": scatter,
        "region_codes": REGION_CODES,
        "notes": {
            "curve_yd": "Rendering hint only (signed lateral bow at the arc's apex, in yards). "
                        "It does not change the model's landing point -- the aim, tee, and landing "
                        "coordinates are the ones the model and the seeded Monte Carlo draw produced.",
        },
    }


def _write_json(obj, path, *, compact):
    kwargs = {"separators": (",", ":")} if compact else {"indent": 1}
    with open(path, "w") as f:
        json.dump(obj, f, sort_keys=False, **kwargs)
        f.write("\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    results = load_results_csv()

    grids = build_sandbox_grids(results)
    _write_json(grids, GRIDS_PATH, compact=True)
    grids_size = os.path.getsize(GRIDS_PATH)
    print(f"wrote {GRIDS_PATH} ({grids_size / 1e6:.2f} MB)")
    if grids_size > 2_100_000:
        print("WARNING: 003_sandbox_grids.json exceeds the ~2 MB budget; "
              "drop p_green before touching the axes (see export.py's module docstring).")

    manifest = build_manifest(results)
    _write_json(manifest, MANIFEST_PATH, compact=False)
    manifest_size = os.path.getsize(MANIFEST_PATH)
    print(f"wrote {MANIFEST_PATH} ({manifest_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
