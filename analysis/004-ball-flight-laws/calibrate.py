"""Fit the two global aero multipliers (lift, drag) to the TrackMan tour tables (gate G2).

Run:  .venv/bin/python calibrate.py [--fit] [--nathan-re]

Without --fit it prints the table for the multipliers now stored in data.py.
With --fit it runs least squares on normalized errors over every PGA and LPGA
row, prints the fit, and prints the two lines to paste into data.py. It never
edits data.py itself.

Errors are normalized by the G2 tolerances, so a residual of 1.0 sits exactly
on the gate: carry error / (3% of published carry), height error / 3 yd,
land angle error / 2 deg. Only two parameters exist (LIFT_MULT, DRAG_MULT),
shared by every club and both tours. scipy is used here and never in flight.py.
"""

import sys

import numpy as np

import data
import flight

# G2 tolerances (task 004.2). Shared with tests/test_flight.py.
CARRY_TOL_FRAC = 0.03
HEIGHT_TOL_YD = 3.0
LAND_TOL_DEG = 2.0


def rows():
    for tour, table in data.TOURS.items():
        for club, r in table.items():
            yield tour, club, r


def run_row(r, dt=0.01):
    return flight.simulate(
        r["ball_speed_mph"], r["launch_deg"], 0.0, r["spin_rpm"], 0.0, dt=dt
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


def residual_vector(params, dt=0.01):
    data.LIFT_MULT, data.DRAG_MULT = params
    out = []
    for _tour, _club, r in rows():
        out.extend(normalized(run_row(r, dt), r))
    return np.array(out)


def print_table():
    print(
        f"LIFT_MULT={data.LIFT_MULT:.4f}  DRAG_MULT={data.DRAG_MULT:.4f}\n"
        f"{'row':12}{'carry pub/model/err':>26}{'height pub/model/err':>26}{'land pub/model/err':>26}  gate"
    )
    for tour, club, r in rows():
        f = run_row(r)
        ec, eh, ea = errors(f, r)
        ok = (
            abs(ec) <= CARRY_TOL_FRAC * r["carry_yd"]
            and abs(eh) <= HEIGHT_TOL_YD
            and abs(ea) <= LAND_TOL_DEG
        )
        print(
            f"{tour + ' ' + club:12}"
            f"{r['carry_yd']:8.0f}{f.carry_yd:8.1f}{ec:+8.1f}"
            f"{r['max_height_yd']:10.0f}{f.max_height_yd:8.1f}{eh:+8.1f}"
            f"{r['land_angle_deg']:10.0f}{f.land_angle_deg:8.1f}{ea:+8.1f}"
            f"  {'pass' if ok else 'MISS'}"
        )


def fit(start=(1.0, 1.0)):
    from scipy.optimize import least_squares

    sol = least_squares(residual_vector, x0=np.array(start), args=(0.02,), diff_step=1e-3)
    data.LIFT_MULT, data.DRAG_MULT = (float(sol.x[0]), float(sol.x[1]))
    return sol


if __name__ == "__main__":
    if "--nathan-re" in sys.argv:
        data.RE_DEPENDENT_DRAG = True  # evidence run: Nathan's full Cd0(Re) branch
    if "--fit" in sys.argv:
        print("Pure Nathan coefficients (multipliers 1.0, 1.0):")
        data.LIFT_MULT = data.DRAG_MULT = 1.0
        print_table()
        sol = fit()
        print("\nFit (least squares on G2-normalized errors):")
        print(f"LIFT_MULT = {sol.x[0]:.4f}\nDRAG_MULT = {sol.x[1]:.4f}")
        r = sol.fun.reshape(-1, 3)
        print(
            "rms normalized residual (carry, height, land): "
            + ", ".join(f"{np.sqrt(np.mean(r[:, i] ** 2)):.2f}" for i in range(3))
        )
        print()
    print_table()
