"""Fit the aero coefficient model to the TrackMan tour tables (gate G2).

Run (one mode per call):
  .venv/bin/python calibrate.py                 table for the shipped model (data.QUAD)
  .venv/bin/python calibrate.py --fit [--variant quad7|A|B]
                                                fit on PGA only, LPGA only and all rows
  .venv/bin/python calibrate.py --compare       fit every variant, print the comparison table
  .venv/bin/python calibrate.py --nathan        baseline: Nathan's forms, Cd0 flat, two multipliers
  .venv/bin/python calibrate.py --nathan-re     baseline: Nathan's forms with the Re branch on
  .venv/bin/python calibrate.py --fit-chart [--chart-weight W]
                                                quad7 fit on the tour rows and the 60 chart rows
  .venv/bin/python calibrate.py --compare-chart fit chart variants, held out both ways
  .venv/bin/python calibrate.py --fit-roll      fit roll to chart total minus carry (shipped aero)
  .venv/bin/python calibrate.py --chart-report  chart tables for the shipped model
  .venv/bin/python calibrate.py --write-misses [--force]
                                                regenerate tests/g2_known_misses.json

None of these edit data.py. Paste printed parameters into data.QUAD by hand.
--write-misses prints a diff against the existing file and refuses a worse
result unless --force is given.

Errors are normalized by the G2 tolerances (see gates.py), so a residual of 1.0
sits on the gate. Every parameter is shared by all clubs and both tours. scipy
is used here and never in flight.py. Variant plumbing (the logistic drag form
and the fitted spin decay k) lives here, not in flight.py, which is ported to JS.
"""

import argparse
import dataclasses
import json
import sys
import warnings
from math import exp

import numpy as np

import baselines
import data
import flight
import gates
from gates import (  # noqa: F401  (re-exported for the reports below)
    chart_misses,
    chart_total_misses,
    chart_normalized,
    chart_rms,
    chart_rows,
    run_chart_row,
    HEIGHT_TOL_YD,
    LAND_TOL_DEG,
    CARRY_TOL_FRAC,
    TEACH_CARRY_FRAC,
    TEACH_HEIGHT_YD,
    TEACH_LAND_DEG,
    errors,
    g2_misses,
    n_rows,
    normalized,
    rms,
    rows,
    run_row,
    teaching_misses,
)

QUAD_KEYS = ("d0", "d1", "d2", "d3", "l0", "l1", "l2")
# Bounds are wide sanity boxes; the real constraints are the penalties below.
QUAD_LO = (0.0, -2.0, -5.0, -0.3, -0.2, -2.0, -8.0)
QUAD_HI = (0.6, 3.0, 5.0, 0.3, 0.5, 5.0, 8.0)
K_UNIT = 1.0e-5  # the vector holds k in units of 1e-5 (SI)
K_BOUNDS = (1.0, 6.0)  # k in [1.0e-5, 6.0e-5] SI (task 004.2, round 3)
LOGISTIC_W = 0.15  # MODELED fixed width of the logistic drag rise, units of 1e5 in Re


def logistic_model(p, name="logistic"):
    """Variant B: CD = d0 + d1 S + d2 S^2 + d3 / (1 + exp((Re - re0) / w)); lift
    as in flight.quad_model. Built directly as an Aero, not through flight.py."""
    d0, d1, d2, d3, re0, w = p["d0"], p["d1"], p["d2"], p["d3"], p["re0"], p["w"]
    l0, l1, l2 = p["l0"], p["l1"], p["l2"]

    def cd(spin, re):
        return d0 + d1 * spin + d2 * spin * spin + d3 / (1.0 + exp((re - re0) / w))

    def cl(spin, re):
        return l0 + l1 * spin + l2 * spin * spin

    return flight.Aero(name, cd, cl)


LOW_S_EXP_SCALE = 0.05  # MODELED width of the low-S lift term in variant "exp"


def build_aero(p):
    """Aero for a parameter dict: logistic drag if p["form"] == "logistic", else
    the linear quad_model. Variant lift forms add one term l3: "cubic" adds
    l3 S^3 and "exp" adds l3 exp(-S / LOW_S_EXP_SCALE), a bump at low S. A "k5"
    entry (spin decay in units of 1e-5) sets spin_decay."""
    form = p.get("form")
    aero = logistic_model(p) if form == "logistic" else flight.quad_model(p)
    if "l3" in p:
        l3, base = p["l3"], aero.cl
        if form == "cubic":
            aero = dataclasses.replace(aero, cl=lambda s, re: base(s, re) + l3 * s**3)
        else:
            aero = dataclasses.replace(aero, cl=lambda s, re: base(s, re) + l3 * exp(-s / LOW_S_EXP_SCALE))
    if "k5" in p:
        aero = dataclasses.replace(aero, spin_decay=p["k5"] * K_UNIT)
    return aero


# Variants. "keys" order is the parameter vector order.
VARIANTS = {
    # 7-parameter quadratic (k fixed at the Anchor 7 value)
    "quad7": dict(
        keys=QUAD_KEYS, lo=QUAD_LO, hi=QUAD_HI, fixed={},
        starts=[(0.22, 0.30, 0.0, 0.0, 0.05, 0.9, -0.8), (0.25, 0.2, 0.3, 0.02, 0.1, 0.5, 0.0)],
        # start for fits that include the chart rows: the objective is flat along
        # a d2 / l2 valley, and the tour-only starts stop at max_nfev short of it
        chart_starts=[(0.1666, 0.7153, -0.5680, -0.0307, 0.0579, 1.2969, -1.2256)],
    ),
    # A: quad7 plus fitted spin decay k
    "A": dict(
        keys=QUAD_KEYS + ("k5",), lo=QUAD_LO + (K_BOUNDS[0],), hi=QUAD_HI + (K_BOUNDS[1],), fixed={},
        starts=[
            (0.20, 0.52, -0.50, -0.09, 0.056, 1.36, -1.35, 2.0),
            (0.20, 0.52, -0.50, -0.09, 0.056, 1.36, -1.35, 4.0),
        ],
    ),
    # B: logistic low-Re drag rise (d2 = 0, width fixed) plus fitted k
    "B": dict(
        keys=("d0", "d1", "d3", "re0", "l0", "l1", "l2", "k5"),
        lo=(0.0, -2.0, 0.0, 0.5, -0.2, -2.0, -8.0, K_BOUNDS[0]),
        hi=(0.6, 3.0, 0.6, 2.0, 0.5, 5.0, 8.0, K_BOUNDS[1]),
        fixed={"form": "logistic", "d2": 0.0, "w": LOGISTIC_W},
        starts=[
            (0.2356, 0.0894, 0.18, 0.92, 0.10, 0.95, -0.87, 2.0),
            (0.2356, 0.0894, 0.18, 0.92, 0.10, 0.95, -0.87, 4.0),
        ],
    ),
    # Chart-fit variants (task 004-copy-pass), all with the published k.
    # cub / exp: quad7 plus one lift term l3. logi: logistic low-Re drag rise
    # (width fixed) with d2 free. Compared by `--compare-chart`.
    "cub": dict(
        keys=QUAD_KEYS + ("l3",), lo=QUAD_LO + (-3.0,), hi=QUAD_HI + (3.0,), fixed={"form": "cubic"},
        starts=[(0.179, 0.63, -0.53, -0.052, 0.062, 1.32, -1.29, 0.0)],
    ),
    "exp": dict(
        keys=QUAD_KEYS + ("l3",), lo=QUAD_LO + (-3.0,), hi=QUAD_HI + (3.0,), fixed={"form": "lowS_exp"},
        starts=[(0.174, 0.636, -0.515, -0.053, 0.0, 1.34, -1.29, 0.04)],
    ),
    "logi": dict(
        keys=("d0", "d1", "d2", "d3", "re0", "l0", "l1", "l2"),
        lo=(0.0, -2.0, -5.0, 0.0, 0.5, -0.2, -2.0, -8.0), hi=(0.6, 3.0, 5.0, 0.6, 2.0, 0.5, 5.0, 8.0),
        fixed={"form": "logistic", "w": LOGISTIC_W},
        starts=[(0.179, 0.63, -0.53, 0.15, 1.0, 0.062, 1.32, -1.29)],
    ),
}


# ---------------------------------------------------------------------------
# Constraint penalties on the quadratic family
# ---------------------------------------------------------------------------

_S_GRID = np.linspace(data.S_MIN, data.S_MAX, 19)
_RE_GRID = np.linspace(data.RE_RANGE[0], data.RE_RANGE[1], 5)
PENALTY = 1000.0  # residual units per unit of violation (coefficient units), large on purpose


def constraint_violations(p):
    """Vector of non-negative violations; all zero means every constraint holds.
    p: dict with QUAD keys."""
    return constraint_violations_aero(build_aero(p))


def constraint_violations_aero(m):
    """Same, for an Aero model."""
    v = []
    cl = np.array([m.cl(s, 1.0) for s in _S_GRID])
    v.extend(np.maximum(0.0, 0.02 - cl))  # CL > 0 (with a 0.02 floor)
    v.extend(np.maximum(0.0, cl - data.CL_MAX))
    v.extend(np.maximum(0.0, cl[:-1] - cl[1:]))  # non-decreasing
    for re in _RE_GRID:
        cd = np.array([m.cd(s, re) for s in _S_GRID])
        v.extend(np.maximum(0.0, data.CD_BAND[0] - cd))
        v.extend(np.maximum(0.0, cd - data.CD_BAND[1]))
    return np.array(v)


def constraints_ok(p, tol=1e-9):
    return bool(np.all(constraint_violations(p) <= tol))


def _vec_to_p(x, variant="quad7"):
    v = VARIANTS[variant]
    return {**v["fixed"], **{key: float(val) for key, val in zip(v["keys"], x)}}


def quad_residuals(x, subset, dt, variant="quad7", chart_w=0.0):
    """Normalized residuals plus constraint penalties. With chart_w == 0 this is
    the tour-only objective. With chart_w > 0 each set is divided by the square
    root of its residual count, so the two sets carry equal total weight at
    chart_w = 1: tour rows (carry, height, land angle) and chart rows (carry
    only, in units of 3 percent), the chart scaled by chart_w."""
    p = _vec_to_p(x, variant)
    aero = build_aero(p)
    tour = []
    for tour_name, club, r in rows(subset):
        tour.extend(normalized(run_row(r, aero, dt), r))
    tour = np.array(tour)
    out = [tour]
    if chart_w > 0:
        chart = np.array([chart_normalized(run_chart_row(r, aero, dt), r) for _c, _l, r in chart_rows()])
        if len(tour):
            out = [tour / np.sqrt(len(tour)), chart_w * chart / np.sqrt(len(chart))]
        else:
            out = [chart_w * chart / np.sqrt(len(chart))]
    out.append(PENALTY * constraint_violations(p))
    return np.concatenate(out)


def fit_quad(subset=("PGA", "LPGA"), dt=0.02, variant="quad7", verbose=False, max_nfev=400, chart_w=0.0):
    from scipy.optimize import least_squares

    v = VARIANTS[variant]
    best = None
    starts = v.get("chart_starts", v["starts"]) if (chart_w > 0 or not subset) else v["starts"]
    if chart_w > 0:
        max_nfev = max(max_nfev, 800)
    for x0 in starts:
        sol = least_squares(
            quad_residuals,
            np.array(x0),
            bounds=(v["lo"], v["hi"]),
            args=(subset, dt, variant, chart_w),
            diff_step=1e-4,
            x_scale=0.1,
            max_nfev=max_nfev,
        )
        if sol.status == 0 or not sol.success:
            warnings.warn(
                f"fit_quad({variant}, {subset}) from start {x0}: stopped at max_nfev={max_nfev} "
                f"or did not converge (status {sol.status}, {sol.message})"
            )
        cost = float(np.sum(sol.fun**2))
        if verbose:
            print(f"  {variant} start {x0} -> cost {cost:.2f}")
        if best is None or cost < best[0]:
            best = (cost, sol)
    return _vec_to_p(best[1].x, variant)


def fit_nathan(re_branch, dt=0.02):
    from scipy.optimize import least_squares

    def res(x):
        p = dict(data.NATHAN, re_branch=re_branch, lift_mult=x[0], drag_mult=x[1])
        aero = baselines.nathan_model(p)
        out = []
        for _t, _c, r in rows():
            out.extend(normalized(run_row(r, aero, dt), r))
        return np.array(out)

    sol = least_squares(res, np.array([1.0, 1.0]), diff_step=1e-3)
    return dict(data.NATHAN, re_branch=re_branch, lift_mult=float(sol.x[0]), drag_mult=float(sol.x[1]))


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


def rms(aero, subset=("PGA", "LPGA"), dt=0.01):
    vals = np.array([normalized(run_row(r, aero, dt), r) for _t, _c, r in rows(subset)])
    return np.sqrt(np.mean(vals**2, axis=0)), np.sqrt(np.mean(vals**2))


def print_table(aero, title, subset=("PGA", "LPGA")):
    print(f"\n{title}")
    print(
        f"{'row':12}{'carry pub/model/err':>26}{'height pub/model/err':>26}"
        f"{'land pub/model/err':>26}{'land mph':>9}  G2  teach"
    )
    npass = ntp = n = 0
    for tour, club, r in rows(subset):
        f = run_row(r, aero)
        ec, eh, ea = errors(f, r)
        g2 = (
            abs(ec) <= CARRY_TOL_FRAC * r["carry_yd"]
            and abs(eh) <= HEIGHT_TOL_YD
            and abs(ea) <= LAND_TOL_DEG
        )
        te = (
            abs(ec) <= TEACH_CARRY_FRAC * r["carry_yd"]
            and abs(eh) <= TEACH_HEIGHT_YD
            and abs(ea) <= TEACH_LAND_DEG
        )
        n += 1
        npass += g2
        ntp += te
        print(
            f"{tour + ' ' + club:12}"
            f"{r['carry_yd']:8.0f}{f.carry_yd:8.1f}{ec:+8.1f}"
            f"{r['max_height_yd']:10.0f}{f.max_height_yd:8.1f}{eh:+8.1f}"
            f"{r['land_angle_deg']:10.0f}{f.land_angle_deg:8.1f}{ea:+8.1f}"
            f"{f.land_speed_mph:9.1f}  {'pass' if g2 else 'MISS':4}{'pass' if te else 'MISS'}"
        )
    comp, tot = rms(aero, subset)
    print(
        f"G2 pass {npass}/{n}, teaching pass {ntp}/{n}; rms normalized (carry, height, land) = "
        f"{comp[0]:.2f}, {comp[1]:.2f}, {comp[2]:.2f}; overall {tot:.2f}"
    )


# Anchor 5(b) Source 2 spin axis curvature examples (a check, never a fit target).
CURVATURE_EXAMPLES = [
    # (tour, club standing in for the "optimized" shot, spin axis deg, published curve yd)
    ("LPGA", "3w", 2.0, 3.0),  # optimized 200 yd shot
    ("LPGA", "3w", 10.0, 15.0),
    ("LPGA", "6i", 2.0, 2.2),  # optimized 150 yd shot; closest Tour carry is LPGA 6i (155)
    ("LPGA", "6i", 10.0, 11.0),
]


def curvature_report(aero, title):
    print(f"\n{title}: spin axis curvature vs Anchor 5(b) examples (check only)")
    for tour, club, axis, pub in CURVATURE_EXAMPLES:
        r = data.TOURS[tour][club]
        f = flight.simulate(
            r["ball_speed_mph"], r["launch_deg"], 0.0, r["spin_rpm"], axis, aero=aero
        )
        print(
            f"  {tour} {club} carry {f.carry_yd:5.1f}  axis {axis:4.1f}  "
            f"published ~{pub:5.1f}  model {f.side_yd:5.1f}  ({(f.side_yd / pub - 1) * 100:+.0f}%)"
        )


def landing_report(aero):
    print("\nLanding speed (mph):")
    for tour, club in (("PGA", "driver"), ("PGA", "7i"), ("PGA", "pw"), ("LPGA", "driver"), ("LPGA", "pw")):
        f = run_row(data.TOURS[tour][club], aero)
        print(f"  {tour} {club}: {f.land_speed_mph:.1f}")


def print_params(p, title):
    print(f"\n{title}")
    print("QUAD = {")
    for k, val in p.items():
        if isinstance(val, float):
            print(f'    "{k}": {val:.5g},' if abs(val) < 1e-3 else f'    "{k}": {val:.5f},')
    print("}")
    print(f"constraints satisfied: {constraints_ok(p, 1e-3)}")
    m = build_aero(p)
    for s in (0.075, 0.15, 0.30, 0.45):
        print(f"  S={s:.3f}: CD(Re=1.5)={m.cd(s, 1.5):.3f}  CL={m.cl(s, 1.5):.3f}")


def _side10(aero, tour, club):
    r = data.TOURS[tour][club]
    return flight.simulate(
        r["ball_speed_mph"], r["launch_deg"], 0.0, r["spin_rpm"], 10.0, aero=aero
    ).side_yd


def compare(variants=("quad7", "A", "B")):
    """Fit each variant on all rows, PGA only and LPGA only; print one table."""
    results = {}
    for name in variants:
        allp = fit_quad(("PGA", "LPGA"), variant=name)
        pga = fit_quad(("PGA",), variant=name)
        lpga = fit_quad(("LPGA",), variant=name)
        aa = build_aero(allp)
        n_g2 = n_rows() - len(g2_misses(aa))
        n_te = n_rows() - len(teaching_misses(aa))
        _, tot = rms(aa)
        _, h_pl = rms(build_aero(pga), ("LPGA",))
        _, h_lp = rms(build_aero(lpga), ("PGA",))
        s3, s6 = _side10(aa, "LPGA", "3w"), _side10(aa, "LPGA", "6i")
        results[name] = dict(params=allp, g2=n_g2, teach=n_te, rms=tot, pga_to_lpga=h_pl,
                             lpga_to_pga=h_lp, held=(h_pl + h_lp) / 2, side3w=s3, side6i=s6)
    print(
        f"{'variant':8}{'nparams':>8}{'G2':>5}{'teach':>7}{'all rms':>9}{'PGA>LPGA':>10}"
        f"{'LPGA>PGA':>10}{'held mean':>10}{'3w@10':>8}{'6i@10':>8}{'3w>6i':>7}"
    )
    for name, r in results.items():
        n = len(VARIANTS[name]["keys"])
        print(
            f"{name:8}{n:8d}{r['g2']:5d}{r['teach']:7d}{r['rms']:9.3f}{r['pga_to_lpga']:10.3f}"
            f"{r['lpga_to_pga']:10.3f}{r['held']:10.3f}{r['side3w']:8.1f}{r['side6i']:8.1f}"
            f"{'yes' if r['side3w'] > r['side6i'] else 'NO':>7}"
        )
    for name, r in results.items():
        print(f"\n{name} all-rows parameters:")
        print(json.dumps(r["params"], indent=2))
    return results


# ---------------------------------------------------------------------------
# TrackMan 2010 chart: combined fit, held-out comparison, roll fit, tables
# ---------------------------------------------------------------------------

CHART_WEIGHT = 2.0  # MODELED: weight of the chart set against the tour set (each divided by sqrt of its residual count)
CHART_FIT_DT = 0.05  # RK4 at 0.05 s agrees with 0.01 s to 0.001 yd on a driver flight
CHART_VARIANTS = ("quad7", "cub", "exp", "logi")


def chart_gains(aero, speeds=(90, 105, 115), dt=0.01):
    """{(chart, speed): (model gain, chart gain)}: carry at attack +5 minus
    carry at -5, from the chart's own launch conditions."""
    got = {}
    for chart, _label, r in chart_rows():
        if r["club_speed_mph"] in speeds and r["attack_deg"] in (-5, 5):
            got[(chart, r["club_speed_mph"], r["attack_deg"])] = (run_chart_row(r, aero, dt).carry_yd, r["carry_yd"])
    return {
        (c, cs): (got[(c, cs, 5)][0] - got[(c, cs, -5)][0], got[(c, cs, 5)][1] - got[(c, cs, -5)][1])
        for c in ("C", "T")
        for cs in speeds
    }


def _fit_variant_job(args):
    variant, dt = args
    both = fit_quad(("PGA", "LPGA"), dt=dt, variant=variant, chart_w=CHART_WEIGHT)
    tour_only = fit_quad(("PGA", "LPGA"), dt=dt, variant=variant)
    chart_only = fit_quad((), dt=dt, variant=variant, chart_w=CHART_WEIGHT)
    return variant, both, tour_only, chart_only


def compare_chart(variants=CHART_VARIANTS, dt=CHART_FIT_DT):
    """Fit each variant on both sets, on the tour rows only and on the chart
    rows only (in parallel), and print the comparison. Held-out: tour-only fit
    scored on the chart, chart-only fit scored on the tour rows."""
    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor(max_workers=len(variants)) as pool:
        fits = list(pool.map(_fit_variant_job, [(v, dt) for v in variants]))
    print(
        f"{'variant':8}{'nparams':>8}{'tour rms':>10}{'chart rms':>10}{'G2':>5}{'teach':>7}"
        f"{'max chart %':>12}{'tour>chart':>11}{'chart>tour':>11}{'held mean':>10}"
    )
    out = {}
    for variant, both, tour_only, chart_only in fits:
        aa = build_aero(both)
        _, tour_rms = rms(aa)
        n_g2, n_te = n_rows() - len(g2_misses(aa)), n_rows() - len(teaching_misses(aa))
        crms = chart_rms(aa)
        cmax = max(abs(chart_normalized(run_chart_row(r, aa), r)) for _c, _l, r in chart_rows()) * 3
        held_tc = chart_rms(build_aero(tour_only))
        held_ct = rms(build_aero(chart_only))[1]
        print(
            f"{variant:8}{len(VARIANTS[variant]['keys']):8d}{tour_rms:10.3f}{crms:10.3f}{n_g2:5d}{n_te:7d}"
            f"{cmax:12.1f}{held_tc:11.3f}{held_ct:11.3f}{(held_tc + held_ct) / 2:10.3f}"
        )
        out[variant] = both
    for variant, p in out.items():
        print(f"\n{variant} both-sets parameters:\n{json.dumps(p, indent=2)}")
    return out


ROLL_KEYS = ("k", "cos_power", "spin_power")


def _roll_arrays(aero, dt=0.01):
    """Per chart row: (target roll = chart total - chart carry, land angle, land
    speed, landing spin), flown from the chart's launch conditions."""
    tgt, la, vl, sl = [], [], [], []
    for _c, _l, r in chart_rows():
        f = run_chart_row(r, aero, dt)
        tgt.append(r["total_yd"] - r["carry_yd"])
        la.append(f.land_angle_deg)
        vl.append(f.land_speed_mph)
        sl.append(f.land_spin_rpm)
    return [np.array(v) for v in (tgt, la, vl, sl)]


def roll_form(p, la, vl, sl):
    spin = np.maximum(sl, data.ROLL_SPIN_FLOOR_RPM)
    r = p[0] * vl * np.cos(np.radians(la)) ** p[1] * (data.ROLL_SPIN_REF_RPM / spin) ** p[2]
    return np.clip(r, 0.0, data.ROLL_MAX_YD)


def fit_roll(aero, dt=0.01):
    """Fit roll = k v cos(la)^p (ref / spin)^q to total minus carry on the 60
    chart rows, soft-L1 (scale 5 yd) because the log flags two totals at 100 mph
    as likely printing errors. Returns (params, rms yd, largest yd)."""
    from scipy.optimize import least_squares

    tgt, la, vl, sl = _roll_arrays(aero, dt)
    sol = least_squares(lambda p: roll_form(p, la, vl, sl) - tgt, [1.3, 4.0, 0.6], loss="soft_l1", f_scale=5.0)
    e = roll_form(sol.x, la, vl, sl) - tgt
    return dict(zip(ROLL_KEYS, (float(v) for v in sol.x))), float(np.sqrt(np.mean(e**2))), float(np.abs(e).max())


def print_chart_tables(aero, title="Shipped model"):
    """Chart carry and total errors by club speed and attack angle, the attack
    angle gains, and roll on tour irons and wedges."""
    print(f"\n{title}: TrackMan 2010 chart carry error, model minus chart (yd, percent)")
    for chart in ("C", "T"):
        print(f"  {'carry optimizer rows' if chart == 'C' else 'total optimizer rows'}")
        print(f"  {'mph':>5}" + "".join(f"{'AoA ' + str(a):>20}" for a in (-5, 0, 5)))
        for cs in range(75, 125, 5):
            cells = []
            for a in (-5, 0, 5):
                r = next(rr for c, _l, rr in chart_rows() if c == chart and rr["club_speed_mph"] == cs and rr["attack_deg"] == a)
                f = run_chart_row(r, aero)
                cells.append(f"{f.carry_yd - r['carry_yd']:+7.1f} ({(f.carry_yd / r['carry_yd'] - 1) * 100:+5.1f}%)")
            print(f"  {cs:5d}" + "".join(f"{c:>20}" for c in cells))
    print(f"\n{title}: TrackMan 2010 chart TOTAL error (model carry + roll minus chart total, yd)")
    for chart in ("C", "T"):
        print(f"  {'carry optimizer rows' if chart == 'C' else 'total optimizer rows'}")
        print(f"  {'mph':>5}" + "".join(f"{'AoA ' + str(a):>14}" for a in (-5, 0, 5)))
        for cs in range(75, 125, 5):
            cells = []
            for a in (-5, 0, 5):
                r = next(rr for c, _l, rr in chart_rows() if c == chart and rr["club_speed_mph"] == cs and rr["attack_deg"] == a)
                f = run_chart_row(r, aero)
                cells.append(f"{flight.roll(f) - r['total_yd']:+7.1f}")
            print(f"  {cs:5d}" + "".join(f"{c:>14}" for c in cells))
    print(f"\n{title}: gain from attack -5 to +5 at the chart's own launch conditions (yd)")
    g = chart_gains(aero)
    print(f"  {'chart':6}{'mph':>5}{'carry: model':>14}{'chart':>8}{'total: model':>14}{'chart':>8}")
    for (c, cs), (mg, cg) in g.items():
        rows5 = {
            a: next(rr for cc, _l, rr in chart_rows() if cc == c and rr["club_speed_mph"] == cs and rr["attack_deg"] == a)
            for a in (-5, 5)
        }
        mt = {a: flight.roll(run_chart_row(rows5[a], aero)) for a in (-5, 5)}
        print(f"  {c:6}{cs:5d}{mg:14.1f}{cg:8.1f}{mt[5] - mt[-5]:14.1f}{rows5[5]['total_yd'] - rows5[-5]['total_yd']:8.1f}")
    print(f"\n{title}: roll on Tour irons and wedges (yd, model)")
    for tour, club in (("PGA", "driver"), ("PGA", "5i"), ("PGA", "7i"), ("PGA", "9i"), ("PGA", "pw"), ("LPGA", "driver"), ("LPGA", "pw")):
        f = run_row(data.TOURS[tour][club], aero)
        print(f"  {tour} {club:7} carry {f.carry_yd:6.1f}  roll {flight.roll(f) - f.carry_yd:5.1f}  land {f.land_angle_deg:4.1f} deg  {f.land_speed_mph:4.1f} mph  spin {f.land_spin_rpm:5.0f}")


def is_worse(old, new, slack=0.15):
    """True if `new` misses more than `old`: a new row, a new component, or a
    component error larger in magnitude by more than `slack`."""
    for key, miss in new.items():
        if key not in old:
            return True
        for comp, err in miss.items():
            if comp not in old[key] or abs(err) > abs(old[key][comp]) + slack:
                return True
    return False


def diff_lines(label, old, new):
    out = []
    for key in sorted(set(old) | set(new)):
        if key not in new:
            out.append(f"  {label} {key}: now passes (was {old[key]})")
        elif key not in old:
            out.append(f"  {label} {key}: NEW miss {new[key]}")
        elif old[key] != new[key]:
            out.append(f"  {label} {key}: {old[key]} -> {new[key]}")
    return out


SECTIONS = ("g2", "teaching", "chart", "chart_total")


def current_misses():
    return {"g2": g2_misses(), "teaching": teaching_misses(), "chart": chart_misses(), "chart_total": chart_total_misses()}


def write_misses(force=False):
    new = current_misses()
    try:
        old = gates.load_record()
    except FileNotFoundError:
        old = None
    if old is not None:
        lines, worse = [], False
        for sec in SECTIONS:
            lines += diff_lines(sec, old.get(sec, {}), new[sec])
            worse = worse or is_worse(old.get(sec, {}), new[sec])
        print("diff against the existing record:" if lines else "no change against the existing record")
        print("\n".join(lines))
        if worse and not force:
            print("REFUSED: the new result is worse than the recorded one. Pass --force to overwrite.")
            return 1
    with open(gates.MISSES_PATH, "w") as fh:
        json.dump(new, fh, indent=2)
        fh.write("\n")
    print("wrote " + ", ".join(f"{len(new[s])} {s}" for s in SECTIONS) + f" misses to {gates.MISSES_PATH}")
    return 0


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--fit", action="store_true", help="fit one variant on PGA, LPGA and all rows")
    mode.add_argument("--compare", action="store_true", help="fit all variants and print the comparison")
    mode.add_argument("--nathan", action="store_true", help="baseline: Nathan forms, flat Cd0, 2 multipliers")
    mode.add_argument("--nathan-re", action="store_true", help="baseline: Nathan forms with the Re branch")
    mode.add_argument("--fit-chart", action="store_true", help="quad7 fit on the tour rows and the 60 chart rows")
    mode.add_argument("--compare-chart", action="store_true", help="fit chart variants, held-out both ways")
    mode.add_argument("--fit-roll", action="store_true", help="fit roll to chart total minus carry")
    mode.add_argument("--chart-report", action="store_true", help="chart tables for the shipped model")
    mode.add_argument("--write-misses", action="store_true", help="regenerate tests/g2_known_misses.json")
    ap.add_argument("--variant", choices=sorted(VARIANTS), default="quad7", help="with --fit and --fit-chart")
    ap.add_argument("--chart-weight", type=float, default=CHART_WEIGHT, help="with --fit-chart: weight of the chart set")
    ap.add_argument("--force", action="store_true", help="with --write-misses: accept a worse result")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.nathan or args.nathan_re:
        p = fit_nathan(args.nathan_re)
        print(
            f"Nathan forms, re_branch={args.nathan_re}: "
            f"lift_mult={p['lift_mult']:.3f} drag_mult={p['drag_mult']:.3f}"
        )
        aero = baselines.nathan_model(p)
        print_table(aero, "Nathan baseline fit")
        landing_report(aero)
        curvature_report(aero, "Nathan baseline")
    elif args.write_misses:
        return write_misses(args.force)
    elif args.compare:
        compare()
    elif args.compare_chart:
        compare_chart()
    elif args.fit_chart:
        p = fit_quad(("PGA", "LPGA"), dt=CHART_FIT_DT, variant=args.variant, chart_w=args.chart_weight, verbose=True)
        print_params(p, f"QUAD fit on tour + chart rows (chart weight {args.chart_weight})")
        aero = build_aero(p)
        print_table(aero, "Tour rows, fit on tour + chart")
        print(f"chart rms {chart_rms(aero):.3f}; misses beyond 3 percent: {chart_misses(aero)}")
    elif args.fit_roll:
        p, r, m = fit_roll(flight.DEFAULT_AERO)
        print(f"roll fit on the shipped aero: {p}  rms {r:.2f} yd, largest {m:.1f} yd")
    elif args.chart_report:
        print_chart_tables(flight.DEFAULT_AERO)
    elif args.fit:
        v = args.variant
        pga = fit_quad(("PGA",), variant=v)
        lpga = fit_quad(("LPGA",), variant=v)
        allp = fit_quad(("PGA", "LPGA"), variant=v, verbose=True)
        print_params(allp, f"ALL-ROWS FIT, variant {v}")
        print_table(build_aero(allp), "ALL-ROWS fit, all rows (in sample)")
        print_table(build_aero(pga), "PGA-only fit predicting LPGA (held out)", ("LPGA",))
        print_table(build_aero(lpga), "LPGA-only fit predicting PGA (held out)", ("PGA",))
        landing_report(build_aero(allp))
        curvature_report(build_aero(allp), f"Variant {v}")
    else:
        print_params(data.QUAD, "Shipped data.QUAD")
        print_table(flight.DEFAULT_AERO, "Shipped model")
        landing_report(flight.DEFAULT_AERO)
        curvature_report(flight.DEFAULT_AERO, "Shipped model")
    return 0


if __name__ == "__main__":
    sys.exit(main())
