"""Fit the delivery-to-launch model to the TrackMan tables (gates G3 and G4).

Run:
  .venv/bin/python calibrate_launch.py               tables for the shipped model (data.LAUNCH_MODEL)
  .venv/bin/python calibrate_launch.py --fit         refit every parameter and print the tables
  .venv/bin/python calibrate_launch.py --write-misses  regenerate tests/g3_known_misses.json

Never edits data.py. Paste the printed LAUNCH_MODEL values into data.py by hand.

Fit order (each step uses the ones before it):
  1. k(spin loft): the four published (dynamic loft, attack angle, launch)
     triples, PGA and LPGA driver and 6 iron. Exact k per row, then a straight
     line in spin loft.
  2. Default dynamic loft per row: invert the launch model so the table's
     attack angle plus that loft reproduce the table's launch angle.
  3. Smash factor vs spin loft: printed smash, all 23 rows.
  4. Spin rate vs ball speed and spin loft: printed spin, all 23 rows, with
     club-class factors for the driver and the 3-wood and 5-wood.
  5. Spin axis scale c(spin loft), linear: the eight Anchor 5(b) curvature
     examples, flown through flight.simulate from the 2019 rows they quote.

Step 5 runs the flight model, so it absorbs that model's own curvature per
degree of axis (it over-curves short irons; see ADR 0004).
"""

import json
import os
import sys
from math import atan2, cos, degrees, radians, sin

import numpy as np
from scipy.optimize import least_squares

import data
import flight
import launch

# G3 tolerances (design doc, task 004.3). Shared with tests/test_launch.py.
G3_LAUNCH_DEG = 1.0
G3_SPIN_FRAC = 0.10
G3_BALL_FRAC = 0.02
DL_CHECK_DEG = 1.0  # inverted dynamic loft vs published, driver and 6 iron
SL_CHECK_DEG = 1.0  # spin loft vs published, driver and 6 iron
SL_CHECK_SLACK = 1e-6  # PGA driver sits on the line: 13.7 against 14.7
# Curvature examples: the larger of 20 percent and 3 yd.
CURVE_REL = 0.20
CURVE_ABS_YD = 3.0

MISSES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "g3_known_misses.json")

K_POINTS = (("PGA", "driver"), ("PGA", "6i"), ("LPGA", "driver"), ("LPGA", "6i"))


def rows(tours=("PGA", "LPGA")):
    for tour in tours:
        for club, r in data.TOURS[tour].items():
            yield tour, club, r


# ---------------------------------------------------------------------------
# 1. k
# ---------------------------------------------------------------------------


def exact_k(attack_deg, dyn_loft_deg, launch_deg):
    """k that reproduces the launch angle for path = face = 0, by bisection on
    the vector blend (exact, no small-angle step)."""
    lo, hi = 0.05, 0.999
    d = launch.club_direction(0.0, attack_deg)
    n = launch.face_normal(0.0, dyn_loft_deg)

    def elev(k):
        u = [(1 - k) * d[i] + k * n[i] for i in range(3)]
        return degrees(atan2(u[2], (u[0] ** 2 + u[1] ** 2) ** 0.5))

    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if elev(mid) < launch_deg:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def k_points():
    out = []
    for tour, club in K_POINTS:
        r = data.TOURS[tour][club]
        dl = data.DYNAMIC_LOFT_DEG[(tour, club)]
        a = r["attack_deg"]
        out.append((tour, club, dl - a, exact_k(a, dl, r["launch_deg"])))
    return out


def fit_k():
    pts = k_points()
    x = np.array([p[2] for p in pts])
    y = np.array([p[3] for p in pts])
    k1, k0 = np.polyfit(x, y, 1)
    return dict(k0=float(k0), k1=float(k1), k_sl_lo=float(x.min()), k_sl_hi=float(x.max()))


# ---------------------------------------------------------------------------
# 2. Derived dynamic loft and spin loft per table row
# ---------------------------------------------------------------------------


def derived(p):
    """{(tour, club): (dyn loft, spin loft)} with path = face = 0."""
    out = {}
    for tour, club, r in rows():
        dl = launch.derive_dyn_loft(r["launch_deg"], r["attack_deg"], p)
        out[(tour, club)] = (dl, dl - r["attack_deg"])
    return out


# ---------------------------------------------------------------------------
# 3 and 4. Smash and spin
# ---------------------------------------------------------------------------


def fit_smash(p):
    """Quadratic in spin loft, fitted to ball speed over club speed for all 23
    rows. The gate compares ball speed, so the fit uses the published speeds.
    The printed smash column differs from that ratio by up to 0.03 (log,
    Anchor 2 and Gaps), and is reported by print_g3 as a check."""
    dv = derived(p)
    sl = np.array([dv[(t, c)][1] for t, c, r in rows()])
    ratio = np.array([r["ball_speed_mph"] / r["club_speed_mph"] for t, c, r in rows()])
    c, b, a = np.polyfit(sl, ratio, 2)
    cap = max(r["smash"] for t, c_, r in rows())
    return dict(smash_a=float(a), smash_b=float(b), smash_c=float(c), smash_cap=float(cap))


def fit_spin(p):
    """spin = class_factor * a * ball_speed * spin_loft^b on printed speeds, spin
    and derived spin loft. Four parameters fitted together: a, b, f_driver (the
    driver rows) and f_wood (3-wood and 5-wood rows); every other row has
    factor 1. Soft-L1 loss on relative error, as the tables hold rows whose spin
    sits off the club ladder and a plain fit lets them drag every iron."""
    dv = derived(p)
    rs = list(rows())
    sl = np.array([dv[(t, c)][1] for t, c, r in rs])
    v = np.array([r["ball_speed_mph"] for t, c, r in rs], dtype=float)
    sp = np.array([r["spin_rpm"] for t, c, r in rs], dtype=float)
    cls = [launch.SPIN_CLASS.get(c) for t, c, r in rs]
    is_d = np.array([k == "driver" for k in cls])
    is_w = np.array([k == "wood" for k in cls])

    def res(x):
        f = np.where(is_d, x[2], np.where(is_w, x[3], 1.0))
        return f * x[0] * v * sl ** x[1] / sp - 1.0

    sol = least_squares(res, [0.4, 1.5, 1.0, 1.0], loss="soft_l1", f_scale=0.1)
    return dict(spin_a=float(sol.x[0]), spin_b=float(sol.x[1]),
                spin_f_driver=float(sol.x[2]), spin_f_wood=float(sol.x[3]))


# ---------------------------------------------------------------------------
# 5. Spin axis scale, from the Anchor 5(b) curvature examples
# ---------------------------------------------------------------------------


def curvature_example(tour, club, f2p, p):
    """Fly one Anchor 5(b) example: 2019 row of that tour and club, path 0,
    face = face-to-path, default dynamic loft inverted from the 2019 launch."""
    r = data.SUPERSEDED_2019[(tour, club)]
    dl = launch.derive_dyn_loft(r["launch_deg"], r["attack_deg"], p)
    ln = launch.deliver(r["club_speed_mph"], r["attack_deg"], 0.0, f2p, dl, club, p)
    f = flight.simulate(ln.ball_speed_mph, ln.launch_deg, ln.launch_dir_deg, ln.spin_rpm, ln.spin_axis_deg)
    return ln, f


def curve_tol(published):
    return max(CURVE_REL * abs(published), CURVE_ABS_YD)


def fit_axis(p):
    """c(spin loft) = c0 + c1 * SL, two parameters. With the driver spin factor
    in place a single constant fails the two LPGA driver examples (the LPGA
    driver's low derived spin loft leaves it 1900 rpm and under-curved), so c
    takes a slope."""

    def res(x):
        q = dict(p, axis_c0=x[0], axis_c1=x[1])
        out = []
        for tour, club, f2p, pub in data.CURVATURE_EXAMPLES:
            _, f = curvature_example(tour, club, f2p, q)
            out.append((f.curve_yd - pub) / curve_tol(pub))
        return out

    sol = least_squares(res, [1.6, -0.026], diff_step=1e-3)
    return dict(axis_c0=float(sol.x[0]), axis_c1=float(sol.x[1]))


def fit_all(verbose=True):
    p = {}
    p.update(fit_k())
    p.update(fit_smash(p))
    p.update(fit_spin(p))
    p.update(axis_c0=1.0, axis_c1=0.0)
    p.update(fit_axis(p))
    return p


# ---------------------------------------------------------------------------
# G3 checks
# ---------------------------------------------------------------------------


def g3_row(tour, club, p=None):
    """Errors for one table row: (launch deg, spin frac, ball speed frac)."""
    r = data.TOURS[tour][club]
    dl = launch.derive_dyn_loft(r["launch_deg"], r["attack_deg"], p)
    ln = launch.deliver(r["club_speed_mph"], r["attack_deg"], 0.0, 0.0, dl, club, p)
    return (
        ln.launch_deg - r["launch_deg"],
        ln.spin_rpm / r["spin_rpm"] - 1.0,
        ln.ball_speed_mph / r["ball_speed_mph"] - 1.0,
        ln,
        dl,
    )


def g3_misses(p=None):
    """{"PGA/3w": {"spin_pct": err, ...}} for rows outside G3, components that
    miss only."""
    out = {}
    for tour, club, _r in rows():
        el, es, eb, _ln, _dl = g3_row(tour, club, p)
        miss = {}
        if abs(el) > G3_LAUNCH_DEG:
            miss["launch_deg"] = round(el, 2)
        if abs(es) > G3_SPIN_FRAC:
            miss["spin_pct"] = round(100.0 * es, 1)
        if abs(eb) > G3_BALL_FRAC:
            miss["ball_pct"] = round(100.0 * eb, 1)
        if miss:
            out[f"{tour}/{club}"] = miss
    return out


def published_checks(p=None):
    """Driver and 6 iron against the published dynamic loft and spin loft.
    [(key, inverted DL, published DL, spin loft at the published DL, published SL)].
    The inverted DL tests the fit of k. The spin loft at the published DL tests
    the geometry (published SL is close to DL - AoA, with unexplained gaps)."""
    out = []
    for (tour, club), dl_pub in data.DYNAMIC_LOFT_DEG.items():
        r = data.TOURS[tour][club]
        dl = launch.derive_dyn_loft(r["launch_deg"], r["attack_deg"], p)
        sl = launch.spin_loft_deg(0.0, r["attack_deg"], 0.0, dl_pub)
        out.append((f"{tour}/{club}", dl, dl_pub, sl, data.SPIN_LOFT_DEG[(tour, club)]))
    return out


def published_misses(p=None):
    """{"LPGA/driver": {"spin_loft_deg": err}} where the spin loft at the
    published dynamic loft is more than SL_CHECK_DEG from the published spin loft."""
    out = {}
    for key, _dl, _dl_pub, sl, sl_pub in published_checks(p):
        if abs(sl - sl_pub) > SL_CHECK_DEG + SL_CHECK_SLACK:
            out[key] = {"spin_loft_deg": round(sl - sl_pub, 2)}
    return out


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------


def print_params(p):
    print("\nLAUNCH_MODEL (paste into data.py, MODELED):")
    for key in ("k0", "k1", "k_sl_lo", "k_sl_hi", "smash_a", "smash_b", "smash_c", "smash_cap",
                "spin_a", "spin_b", "spin_f_driver", "spin_f_wood", "axis_c0", "axis_c1"):
        print(f"    {key!r}: {p[key]:.6g},")


def print_k(p):
    print("\nk per published triple (exact) against the line k0 + k1 * spin loft:")
    print(f"{'row':<12}{'SL':>7}{'k exact':>9}{'k line':>9}{'launch err':>12}")
    for tour, club, sl, k in k_points():
        r = data.TOURS[tour][club]
        dl = data.DYNAMIC_LOFT_DEG[(tour, club)]
        el = launch.launch_vector(0.0, r["attack_deg"], 0.0, dl, p)[0] - r["launch_deg"]
        print(f"{tour + '/' + club:<12}{sl:>7.1f}{k:>9.3f}{launch.k_of(sl, p):>9.3f}{el:>+12.2f}")
    print("\nimplied horizontal face share (small face-to-path), against the unverified claims")
    print("  85 / 75 (PGA Academy, unattributed) and 87 / 81 (forum, driver / 6 iron or PW):")
    for (tour, club), dl in data.DYNAMIC_LOFT_DEG.items():
        a = data.TOURS[tour][club]["attack_deg"]
        print(f"  {tour}/{club}: {100 * launch.horizontal_face_share(a, dl, p):.1f} percent")
    for tour, club, r in rows():
        if club in ("pw", "7i"):
            dl = launch.derive_dyn_loft(r["launch_deg"], r["attack_deg"], p)
            print(f"  {tour}/{club} (derived dynamic loft {dl:.1f}): "
                  f"{100 * launch.horizontal_face_share(r['attack_deg'], dl, p):.1f} percent")


def print_g3(p):
    print("\nG3: table delivery (path 0, face 0, derived dynamic loft) against the table")
    print(f"{'row':<13}{'DL':>6}{'SL':>6}{'launch':>8}{'smash':>7}{'ball':>6}{'ball%':>7}{'spin':>7}{'tbl':>6}{'spin%':>7}  flag")
    misses = 0
    for tour, club, r in rows():
        el, es, eb, ln, dl = g3_row(tour, club, p)
        bad = abs(el) > G3_LAUNCH_DEG or abs(es) > G3_SPIN_FRAC or abs(eb) > G3_BALL_FRAC
        misses += bad
        print(f"{tour + '/' + club:<13}{dl:>6.1f}{ln.spin_loft_deg:>6.1f}{ln.launch_deg:>8.2f}{ln.smash:>7.3f}"
              f"{ln.ball_speed_mph:>6.1f}{100 * eb:>+7.1f}{ln.spin_rpm:>7.0f}{r['spin_rpm']:>6}{100 * es:>+7.1f}  {'MISS' if bad else ''}")
    print(f"rows outside G3: {misses} of 23")
    print("\nPublished driver and 6 iron (tolerance 1 deg): inverted dynamic loft, and spin loft at the published loft:")
    for key, dl, dl_pub, sl, sl_pub in published_checks(p):
        flag = "" if abs(dl - dl_pub) <= DL_CHECK_DEG and abs(sl - sl_pub) <= SL_CHECK_DEG + SL_CHECK_SLACK else "  MISS"
        print(f"  {key:<12} DL {dl:5.1f} vs {dl_pub:5.1f} ({dl - dl_pub:+.1f})   SL {sl:5.1f} vs {sl_pub:5.1f} ({sl - sl_pub:+.1f}){flag}")


def print_curvature(p):
    print("\nAnchor 5(b) curvature examples (2019 rows, path 0, face = face-to-path):")
    print(f"{'example':<14}{'F2P':>5}{'carry':>7}{'2019':>6}{'axis':>7}{'curve':>8}{'pub':>6}{'tol':>6}{'err%':>7}  flag")
    bad = 0
    for tour, club, f2p, pub in data.CURVATURE_EXAMPLES:
        ln, f = curvature_example(tour, club, f2p, p)
        err = f.curve_yd - pub
        flag = abs(err) > curve_tol(pub)
        bad += flag
        carry_pub = data.SUPERSEDED_2019[(tour, club)]["carry_yd"]
        print(f"{tour + '/' + club:<14}{f2p:>+5.0f}{f.carry_yd:>7.0f}{carry_pub:>6}{ln.spin_axis_deg:>+7.1f}"
              f"{f.curve_yd:>+8.1f}{pub:>+6.0f}{curve_tol(pub):>6.1f}{100 * err / abs(pub):>+7.1f}  {'MISS' if flag else ''}")
    print(f"examples outside max(20 percent, 3 yd): {bad} of 8")


def print_held_out(p):
    print("\nHeld out (not fit): TrackMan Optimizer defaults and the Combine driver.")
    print(f"{'row':<22}{'launch':>8}{'pub':>7}{'spin':>7}{'pub':>7}{'ball':>7}{'pub':>6}{'SL':>6}{'pub':>6}")
    for club, cs, aoa, dl, bs, la, sp, sl in data.OPTIMIZER_DEFAULTS:
        ln = launch.deliver(cs, aoa, 0.0, 0.0, dl, club, p)
        print(f"{'Optimizer ' + club:<22}{ln.launch_deg:>8.1f}{la:>7.1f}{ln.spin_rpm:>7.0f}{sp:>7}{ln.ball_speed_mph:>7.1f}{bs:>6}{ln.spin_loft_deg:>6.1f}{sl:>6.1f}")
    a = data.AMATEUR_ANCHORS["driver"]
    ln = launch.deliver(a["club_speed_mph"], a["attack_deg"], 0.0, 0.0, a["dyn_loft_deg"], "driver", p)
    print(f"{'Combine avg driver':<22}{ln.launch_deg:>8.1f}{12.6:>7.1f}{ln.spin_rpm:>7.0f}{3275:>7}{ln.ball_speed_mph:>7.1f}{133:>6}{ln.spin_loft_deg:>6.1f}{18.3:>6.1f}")


def print_all(p):
    print_params(p)
    print_k(p)
    print_g3(p)
    print_curvature(p)
    print_held_out(p)


def main(argv):
    if "--write-misses" in argv:
        record = {"g3": g3_misses(), "published": published_misses()}
        with open(MISSES_PATH, "w") as fh:
            json.dump(record, fh, indent=2)
            fh.write("\n")
        print(f"wrote {len(record['g3'])} G3 misses and {len(record['published'])} published-loft misses to {MISSES_PATH}")
        return
    if "--fit" in argv:
        p = fit_all()
        print_all(p)
        return
    print_all(dict(data.LAUNCH_MODEL))


if __name__ == "__main__":
    main(sys.argv[1:])
