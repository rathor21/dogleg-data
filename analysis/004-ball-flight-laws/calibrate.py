"""Fit the aero coefficient model to the TrackMan tour tables (gate G2).

Run:
  .venv/bin/python calibrate.py                 table for the shipped model (data.QUAD)
  .venv/bin/python calibrate.py --fit           quadratic fit: PGA-only, LPGA-only, all rows
  .venv/bin/python calibrate.py --nathan        baseline: Nathan's forms, Cd0 flat, two multipliers
  .venv/bin/python calibrate.py --nathan-re     baseline: Nathan's forms with the Re branch on
  .venv/bin/python calibrate.py --write-misses  regenerate tests/g2_known_misses.json

None of these edit data.py. Paste the printed parameters into data.QUAD by hand.

Errors are normalized by the G2 tolerances, so a residual of 1.0 sits on the
gate: carry error / (3% of published carry), height error / 3 yd, land angle
error / 2 deg. Every parameter is shared by all clubs and both tours. scipy is
used here and never in flight.py.
"""

import json
import os
import sys

import numpy as np

import data
import flight

# G2 tolerances (task 004.2). Shared with tests/test_flight.py.
CARRY_TOL_FRAC = 0.03
HEIGHT_TOL_YD = 3.0
LAND_TOL_DEG = 2.0
# Teaching tolerance: a looser bar every row must clear (coordinator, task 004.2).
TEACH_CARRY_FRAC = 0.05
TEACH_HEIGHT_YD = 4.0
TEACH_LAND_DEG = 3.0

MISSES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "g2_known_misses.json")

QUAD_KEYS = ("d0", "d1", "d2", "d3", "l0", "l1", "l2")
# Bounds are wide sanity boxes; the real constraints are the penalties below.
QUAD_LO = (0.0, -2.0, -5.0, -0.3, -0.2, -2.0, -8.0)
QUAD_HI = (0.6, 3.0, 5.0, 0.3, 0.5, 5.0, 8.0)
K_UNIT = 1.0e-5  # the vector holds k in units of 1e-5 (SI)
K_BOUNDS = (1.0, 6.0)  # k in [1.0e-5, 6.0e-5] SI (task 004.2, round 3)
LOGISTIC_W = 0.15  # MODELED fixed width of the logistic drag rise, units of 1e5 in Re

# Variants. "keys" order is the parameter vector order.
VARIANTS = {
    # 7-parameter quadratic shipped in round 2 (k fixed at the Anchor 7 value)
    "quad7": dict(
        keys=QUAD_KEYS, lo=QUAD_LO, hi=QUAD_HI, fixed={},
        starts=[(0.22, 0.30, 0.0, 0.0, 0.05, 0.9, -0.8), (0.25, 0.2, 0.3, 0.02, 0.1, 0.5, 0.0)],
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
}


def rows(tours=("PGA", "LPGA")):
    for tour in tours:
        for club, r in data.TOURS[tour].items():
            yield tour, club, r


def run_row(r, aero=None, dt=0.01):
    return flight.simulate(
        r["ball_speed_mph"], r["launch_deg"], 0.0, r["spin_rpm"], 0.0, dt=dt, aero=aero
    )


def errors(f, r):
    """(carry error yd, height error yd, land angle error deg), model minus published."""
    return (
        f.carry_yd - r["carry_yd"],
        f.max_height_yd - r["max_height_yd"],
        f.land_angle_deg - r["land_angle_deg"],
    )


def normalized(f, r):
    ec, eh, ea = errors(f, r)
    return (ec / (CARRY_TOL_FRAC * r["carry_yd"]), eh / HEIGHT_TOL_YD, ea / LAND_TOL_DEG)


def g2_misses(aero=None, dt=0.01):
    """{"PGA/3w": {"carry_yd": err, ...}} for rows outside the published G2
    tolerances, listing only the components that miss. Runs the model."""
    out = {}
    for tour, club, r in rows():
        ec, eh, ea = errors(run_row(r, aero, dt), r)
        miss = {}
        if abs(ec) > CARRY_TOL_FRAC * r["carry_yd"]:
            miss["carry_yd"] = round(ec, 1)
        if abs(eh) > HEIGHT_TOL_YD:
            miss["height_yd"] = round(eh, 1)
        if abs(ea) > LAND_TOL_DEG:
            miss["land_deg"] = round(ea, 1)
        if miss:
            out[f"{tour}/{club}"] = miss
    return out


def teaching_misses(aero=None, dt=0.01):
    out = {}
    for tour, club, r in rows():
        ec, eh, ea = errors(run_row(r, aero, dt), r)
        miss = {}
        if abs(ec) > TEACH_CARRY_FRAC * r["carry_yd"]:
            miss["carry_yd"] = round(ec, 1)
        if abs(eh) > TEACH_HEIGHT_YD:
            miss["height_yd"] = round(eh, 1)
        if abs(ea) > TEACH_LAND_DEG:
            miss["land_deg"] = round(ea, 1)
        if miss:
            out[f"{tour}/{club}"] = miss
    return out


# ---------------------------------------------------------------------------
# Constraint penalties on the quadratic family
# ---------------------------------------------------------------------------

_S_GRID = np.linspace(data.S_MIN, data.S_MAX, 19)
_RE_GRID = np.linspace(data.RE_RANGE[0], data.RE_RANGE[1], 5)
PENALTY = 1000.0  # residual units per unit of violation (coefficient units), large on purpose


def constraint_violations(p):
    """Vector of non-negative violations; all zero means every constraint holds.
    p: dict with QUAD keys."""
    m = flight.quad_model(p)
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
    p = dict(v["fixed"])
    for key, val in zip(v["keys"], x):
        if key == "k5":
            p["k"] = float(val) * K_UNIT
        else:
            p[key] = float(val)
    return p


def quad_residuals(x, subset, dt, variant="quad7"):
    p = _vec_to_p(x, variant)
    aero = flight.quad_model(p)
    out = []
    for tour, club, r in rows(subset):
        out.extend(normalized(run_row(r, aero, dt), r))
    out.extend(PENALTY * constraint_violations(p))
    return np.array(out)


def fit_quad(subset=("PGA", "LPGA"), dt=0.02, variant="quad7", verbose=False):
    from scipy.optimize import least_squares

    v = VARIANTS[variant]
    best = None
    for x0 in v["starts"]:
        sol = least_squares(
            quad_residuals,
            np.array(x0),
            bounds=(v["lo"], v["hi"]),
            args=(subset, dt, variant),
            diff_step=1e-4,
            x_scale=0.1,
            max_nfev=400,
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
        aero = flight.nathan_model(p)
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
    for k in QUAD_KEYS:
        print(f'    "{k}": {p[k]:.5f},')
    print("}")
    print(f"constraints satisfied: {constraints_ok(p, 1e-3)}")
    m = flight.quad_model(p)
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
        aa = flight.quad_model(allp)
        n_g2 = 23 - len(g2_misses(aa))
        n_te = 23 - len(teaching_misses(aa))
        _, tot = rms(aa)
        _, h_pl = rms(flight.quad_model(pga), ("LPGA",))
        _, h_lp = rms(flight.quad_model(lpga), ("PGA",))
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


def main(argv):
    if "--nathan" in argv or "--nathan-re" in argv:
        branch = "--nathan-re" in argv
        p = fit_nathan(branch)
        print(f"Nathan forms, re_branch={branch}: lift_mult={p['lift_mult']:.3f} drag_mult={p['drag_mult']:.3f}")
        aero = flight.nathan_model(p)
        print_table(aero, "Nathan baseline fit")
        landing_report(aero)
        curvature_report(aero, "Nathan baseline")
        return
    if "--write-misses" in argv:
        misses = {"g2": g2_misses(), "teaching": teaching_misses()}
        with open(MISSES_PATH, "w") as fh:
            json.dump(misses, fh, indent=2, sort_keys=False)
            fh.write("\n")
        print(
            f"wrote {len(misses['g2'])} G2 misses and {len(misses['teaching'])} "
            f"teaching misses to {MISSES_PATH}"
        )
        return
    if "--compare" in argv:
        compare()
        return
    if "--fit" in argv:
        variant = argv[argv.index("--variant") + 1] if "--variant" in argv else "quad7"
        pga = fit_quad(("PGA",), variant=variant)
        lpga = fit_quad(("LPGA",), variant=variant)
        allp = fit_quad(("PGA", "LPGA"), variant=variant, verbose=True)
        print_params(allp, f"ALL-ROWS FIT, variant {variant} (shipped candidate)")
        print_table(flight.quad_model(allp), "ALL-ROWS fit, all rows (in sample)")
        print_table(flight.quad_model(pga), "PGA-only fit predicting LPGA (held out)", ("LPGA",))
        print_table(flight.quad_model(lpga), "LPGA-only fit predicting PGA (held out)", ("PGA",))
        landing_report(flight.quad_model(allp))
        curvature_report(flight.quad_model(allp), f"Variant {variant}")
        return
    print_params(data.QUAD, "Shipped data.QUAD")
    print_table(flight.DEFAULT_AERO, "Shipped model")
    landing_report(flight.DEFAULT_AERO)
    curvature_report(flight.DEFAULT_AERO, "Shipped model")


if __name__ == "__main__":
    main(sys.argv[1:])
