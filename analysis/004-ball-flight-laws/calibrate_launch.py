"""Fit the delivery-to-launch model to the TrackMan tables (gates G3 and G4).

Run:
  .venv/bin/python calibrate_launch.py                        tables for the shipped model (data.LAUNCH_MODEL)
  .venv/bin/python calibrate_launch.py --fit                  refit every parameter and print the tables
  .venv/bin/python calibrate_launch.py --write-misses [--force]   regenerate tests/g3_known_misses.json
  .venv/bin/python calibrate_launch.py --write-tour-dyn-loft  print data.TOUR_DYN_LOFT for the shipped model
  .venv/bin/python calibrate_launch.py --write-golden         regenerate tests/golden_launch.json

Never edits data.py. Paste the printed LAUNCH_MODEL and TOUR_DYN_LOFT values
into data.py by hand.

Fit order (each step uses the ones before it):
  1. k(spin loft): the four published (dynamic loft, attack angle, launch)
     triples, PGA and LPGA driver and 6 iron. Exact k per row, then a straight
     line in spin loft.
  2. Default dynamic loft per row: invert the launch model so the table's
     attack angle plus that loft reproduce the table's launch angle.
  3. Smash factor vs spin loft: ball speed over club speed, all 23 rows.
  4. Spin rate vs ball speed and spin loft: printed spin, all 23 rows, with
     club-class factors for the driver and the 3-wood and 5-wood.
  5. Spin axis scale c, one constant: the eight Anchor 5(b) curvature
     examples, flown through flight.simulate from the 2019 rows they quote,
     each with its own spin trim.

Step 5 runs the flight model, so it absorbs that model's own curvature per
degree of axis (it over-curves short irons; see ADR 0004). The fit is repeated
at dt 0.005 to show it does not depend on the step size.
"""

import argparse
import json
import sys

import numpy as np
from scipy.optimize import least_squares

import calibrate
import data
import gates_launch as gl
import launch
import launch_tools
import presets

K_POINTS = (("PGA", "driver"), ("PGA", "6i"), ("LPGA", "driver"), ("LPGA", "6i"))
FIT_DT = 0.01
STABILITY_DT = 0.005
STABILITY_TOL = 0.01  # relative change in c between the two step sizes
CLUB_CLASS = launch.SPIN_CLASS


def _require(sol, name):
    if not sol.success:
        raise RuntimeError(f"{name} fit did not converge: {sol.message}")


# ---------------------------------------------------------------------------
# 1. k
# ---------------------------------------------------------------------------


def exact_k(attack_deg, dyn_loft_deg, launch_deg):
    """k that reproduces the launch angle for path = face = 0, by bisection on
    the vector blend (exact, no small-angle step)."""
    lo, hi = 0.05, 0.999
    d = launch.club_direction(0.0, attack_deg)
    n = launch.face_normal(0.0, dyn_loft_deg)

    def elevation(k):
        u = launch.blend(d, n, k)
        return np.degrees(np.arctan2(u[2], np.hypot(u[0], u[1])))

    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if elevation(mid) < launch_deg:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def k_points():
    """[(tour, club, spin loft, exact k)] for the four published triples."""
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


def derived(params):
    """{(tour, club): (dyn loft, spin loft)} with path = face = 0."""
    out = {}
    for tour, club, r in gl.rows():
        dl = launch_tools.derive_dyn_loft(r["launch_deg"], r["attack_deg"], params=params)
        out[(tour, club)] = (dl, dl - r["attack_deg"])
    return out


# ---------------------------------------------------------------------------
# 3 and 4. Smash and spin
# ---------------------------------------------------------------------------


def fit_smash(params):
    """Quadratic in spin loft, fitted to ball speed over club speed for all 23
    rows. The gate compares ball speed, so the fit uses the published speeds.
    The printed smash column differs from that ratio by up to 0.03 (log,
    Anchor 2 and Gaps). smash_floor is the fit's value at spin loft 45."""
    dv = derived(params)
    sl = np.array([dv[(t, c)][1] for t, c, r in gl.rows()])
    ratio = np.array([r["ball_speed_mph"] / r["club_speed_mph"] for t, c, r in gl.rows()])
    quad, lin, const = np.polyfit(sl, ratio, 2)
    cap = max(r["smash"] for t, c, r in gl.rows())
    floor = const + lin * 45.0 + quad * 45.0 ** 2
    return dict(smash_a=float(const), smash_b=float(lin), smash_c=float(quad),
                smash_cap=float(cap), smash_floor=float(floor))


def fit_spin(params):
    """spin = class_factor * a * ball_speed * spin_loft^b on printed speeds, spin
    and derived spin loft. Four parameters fitted together: a, b, f_driver (the
    driver rows) and f_wood (3-wood and 5-wood rows); every other row has
    factor 1. Soft-L1 loss on relative error, as the tables hold rows whose spin
    sits off the club ladder and a plain fit lets them drag every iron."""
    dv = derived(params)
    table_rows = list(gl.rows())
    sl = np.array([dv[(t, c)][1] for t, c, r in table_rows])
    v = np.array([r["ball_speed_mph"] for t, c, r in table_rows], dtype=float)
    spin = np.array([r["spin_rpm"] for t, c, r in table_rows], dtype=float)
    classes = [CLUB_CLASS.get(c) for t, c, r in table_rows]
    is_driver = np.array([k == "driver" for k in classes])
    is_wood = np.array([k == "wood" for k in classes])

    def residuals(x):
        factor = np.where(is_driver, x[2], np.where(is_wood, x[3], 1.0))
        return factor * x[0] * v * sl ** x[1] / spin - 1.0

    sol = least_squares(residuals, [0.4, 1.5, 1.0, 1.0], loss="soft_l1", f_scale=0.1)
    _require(sol, "spin")
    return dict(spin_a=float(sol.x[0]), spin_b=float(sol.x[1]),
                spin_f_driver=float(sol.x[2]), spin_f_wood=float(sol.x[3]))


# ---------------------------------------------------------------------------
# 5. Spin axis scale, from the Anchor 5(b) curvature examples
# ---------------------------------------------------------------------------


def fit_axis(params, dt=FIT_DT):
    """One constant c on the D-plane tilt, fitted to the eight examples with
    the spin trims applied. Returns the fit and the normalized residuals."""

    def residuals(x):
        candidate = dict(params, axis_c=x[0])
        return [err for *_rest, err in gl.curvature_errors(candidate, dt)]

    sol = least_squares(residuals, [1.0], diff_step=1e-3)
    _require(sol, "axis")
    return dict(axis_c=float(sol.x[0])), list(sol.fun)


def fit_all(verbose=True):
    """Fit every parameter in order. Returns (params, diagnostics)."""
    params = {}
    diag = {}
    params.update(fit_k())
    pts = k_points()
    resid_k = [launch.launch_vector(0.0, data.TOURS[t][c]["attack_deg"], 0.0, data.DYNAMIC_LOFT_DEG[(t, c)],
                                    params=params)[0] - data.TOURS[t][c]["launch_deg"] for t, c, _sl, _k in pts]
    diag["k: launch residual (deg)"] = resid_k
    params.update(fit_smash(params))
    params.update(fit_spin(params))
    params["axis_c"] = 1.0
    fit, resid_axis = fit_axis(params, FIT_DT)
    params.update(fit)
    diag["axis: normalized curve error"] = resid_axis
    # Rows scored by G3 after the fit
    ball, spin = [], []
    for tour, club, _r in gl.rows():
        res = gl.g3_row(tour, club, params)
        ball.append(res.ball_err_frac)
        spin.append(res.spin_err_frac)
    diag["smash: ball speed error (fraction)"] = ball
    diag["spin: spin error (fraction)"] = spin
    check, _ = fit_axis(params, STABILITY_DT)
    rel = abs(check["axis_c"] - params["axis_c"]) / params["axis_c"]
    diag["axis c at dt 0.005"] = [check["axis_c"], rel]
    if rel > STABILITY_TOL:
        raise RuntimeError(f"axis fit depends on the step size: c {params['axis_c']:.4f} at dt {FIT_DT}, "
                           f"{check['axis_c']:.4f} at dt {STABILITY_DT}")
    return params, diag


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------


def print_params(params):
    print("\nLAUNCH_MODEL (paste into data.py, MODELED):")
    for key in ("k0", "k1", "k_sl_lo", "k_sl_hi", "smash_a", "smash_b", "smash_c", "smash_cap", "smash_floor",
                "spin_a", "spin_b", "spin_f_driver", "spin_f_wood", "axis_c"):
        print(f"    {key!r}: {params[key]:.6g},")


def print_diagnostics(diag):
    print("\nFit quality (rms and largest absolute error):")
    for name, vals in diag.items():
        if name.startswith("axis c at"):
            print(f"  {name}: c = {vals[0]:.4f}, relative change {vals[1]:.4%}")
            continue
        arr = np.array(vals, dtype=float)
        print(f"  {name}: rms {np.sqrt(np.mean(arr ** 2)):.4f}, max {np.abs(arr).max():.4f}")


def print_k(params):
    print("\nk per published triple (exact) against the line k0 + k1 * spin loft:")
    print(f"{'row':<12}{'SL':>7}{'k exact':>9}{'k line':>9}{'launch err':>12}")
    for tour, club, sl, k in k_points():
        r = data.TOURS[tour][club]
        dl = data.DYNAMIC_LOFT_DEG[(tour, club)]
        err = launch.launch_vector(0.0, r["attack_deg"], 0.0, dl, params=params)[0] - r["launch_deg"]
        print(f"{tour + '/' + club:<12}{sl:>7.1f}{k:>9.3f}{launch.k_of(sl, params):>9.3f}{err:>+12.2f}")
    print("\nimplied horizontal face share (small face-to-path), against the unverified claims")
    print("  85 / 75 (PGA Academy, unattributed) and 87 / 81 (forum, driver / 6 iron or PW):")
    for (tour, club), dl in data.DYNAMIC_LOFT_DEG.items():
        a = data.TOURS[tour][club]["attack_deg"]
        print(f"  {tour}/{club}: {100 * launch_tools.horizontal_face_share(a, dl, params=params):.1f} percent")
    for tour, club, r in gl.rows():
        if club in ("pw", "7i"):
            dl = gl.tour_dyn_loft(tour, club, params)
            share = launch_tools.horizontal_face_share(r["attack_deg"], dl, params=params)
            print(f"  {tour}/{club} (derived dynamic loft {dl:.1f}): {100 * share:.1f} percent")


def print_g3(params):
    print("\nG3: table delivery (path 0, face 0, derived dynamic loft) against the table")
    print(f"{'row':<13}{'DL':>6}{'SL':>6}{'launch':>8}{'smash':>7}{'ball':>6}{'ball%':>7}{'spin':>7}{'tbl':>6}{'spin%':>7}  flag")
    misses = 0
    for tour, club, r in gl.rows():
        res = gl.g3_row(tour, club, params)
        ln = res.launch
        bad = (abs(res.launch_err_deg) > gl.G3_LAUNCH_DEG or abs(res.spin_err_frac) > gl.G3_SPIN_FRAC
               or abs(res.ball_err_frac) > gl.G3_BALL_FRAC)
        misses += bad
        print(f"{tour + '/' + club:<13}{res.dyn_loft_deg:>6.1f}{ln.spin_loft_deg:>6.1f}{ln.launch_deg:>8.2f}{ln.smash:>7.3f}"
              f"{ln.ball_speed_mph:>6.1f}{100 * res.ball_err_frac:>+7.1f}{ln.spin_rpm:>7.0f}{r['spin_rpm']:>6}"
              f"{100 * res.spin_err_frac:>+7.1f}  {'MISS' if bad else ''}")
    print(f"rows outside G3: {misses} of {gl.n_rows()}")
    print("\nPublished driver and 6 iron (tolerance 1 deg): default dynamic loft, and spin loft at the published loft:")
    for key, dl, dl_pub, sl, sl_pub in gl.published_checks(params):
        ok = abs(dl - dl_pub) <= gl.DL_CHECK_DEG and abs(sl - sl_pub) <= gl.SL_CHECK_DEG + gl.SL_CHECK_SLACK
        print(f"  {key:<12} DL {dl:5.1f} vs {dl_pub:5.1f} ({dl - dl_pub:+.1f})   SL {sl:5.1f} vs {sl_pub:5.1f} ({sl - sl_pub:+.1f}){'' if ok else '  MISS'}")


def print_curvature(params, dt=FIT_DT):
    print("\nAnchor 5(b) curvature examples (2019 rows with their own spin trim, path 0, face = face-to-path):")
    print(f"{'example':<14}{'F2P':>5}{'carry':>7}{'2019':>6}{'axis':>7}{'curve':>8}{'pub':>6}{'tol':>6}{'err%':>7}  flag")
    bad = 0
    for tour, club, f2p, pub in data.CURVATURE_EXAMPLES:
        ln, f = gl.curvature_example(tour, club, f2p, params, dt)
        err = f.curve_yd - pub
        flag = abs(err) > gl.curve_tol(pub)
        bad += flag
        carry_pub = data.SUPERSEDED_2019[(tour, club)]["carry_yd"]
        print(f"{tour + '/' + club:<14}{f2p:>+5.0f}{f.carry_yd:>7.0f}{carry_pub:>6}{ln.spin_axis_deg:>+7.1f}"
              f"{f.curve_yd:>+8.1f}{pub:>+6.0f}{gl.curve_tol(pub):>6.1f}{100 * err / abs(pub):>+7.1f}  {'MISS' if flag else ''}")
    print(f"examples outside max(20 percent, 3 yd): {bad} of {len(data.CURVATURE_EXAMPLES)}")


def print_held_out(params):
    print("\nHeld out (not fit): the TrackMan Combine driver and Optimizer defaults (amateur anchors).")
    print(f"{'row':<22}{'launch':>8}{'pub':>7}{'spin':>7}{'pub':>7}{'ball':>7}{'pub':>6}{'SL':>6}{'pub':>6}")
    for club, a in data.AMATEUR_ANCHORS.items():
        ln = launch.deliver(a["club_speed_mph"], a["attack_deg"], 0.0, 0.0, a["dyn_loft_deg"], club, params=params)
        label = "Amateur " + club + (" (Combine)" if club == "driver" else " (Optimizer)")
        print(f"{label:<22}{ln.launch_deg:>8.1f}{a['launch_deg']:>7.1f}{ln.spin_rpm:>7.0f}{a['spin_rpm']:>7}"
              f"{ln.ball_speed_mph:>7.1f}{a['ball_speed_mph']:>6}{ln.spin_loft_deg:>6.1f}{a['spin_loft_deg']:>6.1f}")


def print_trims():
    print("\nSpin trim per preset (published spin / model spin at the preset delivery), shipped model:")
    print(f"{'club':<8}{'PGA':>8}{'LPGA':>8}{'amateur':>9}")
    for club in presets.CLUBS:
        cells = "".join(f"{presets.preset(club, pl)['spin_trim']:>{w}.3f}" for pl, w in (("pga", 8), ("lpga", 8), ("amateur", 9)))
        print(f"{club:<8}{cells}")
    print("preset misses (spin 1 pct for every preset; launch 1 deg and ball speed 2 pct for the amateur anchors,")
    print("since a Tour preset's launch and ball speed are its G3 row's):")
    misses = gl.preset_misses()
    for key, miss in misses.items():
        print(f"  {key}: {miss}")
    if not misses:
        print("  none")


def print_all(params, diag=None):
    print_params(params)
    if diag:
        print_diagnostics(diag)
    print_k(params)
    print_g3(params)
    print_curvature(params)
    print_held_out(params)
    print_trims()


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------


def write_misses(force=False):
    new = gl.current_misses()
    try:
        old = gl.load_record()
    except FileNotFoundError:
        old = None
    if old is not None:
        lines, worse = [], False
        for section in gl.SECTIONS:
            lines += calibrate.diff_lines(section, old.get(section, {}), new[section])
            worse = worse or calibrate.is_worse(old.get(section, {}), new[section])
        print("diff against the existing record:" if lines else "no change against the existing record")
        print("\n".join(lines))
        if worse and not force:
            print("REFUSED: the new result is worse than the recorded one. Pass --force to overwrite.")
            return 1
    with open(gl.MISSES_PATH, "w") as fh:
        json.dump(new, fh, indent=2)
        fh.write("\n")
    print("wrote " + ", ".join(f"{len(new[s])} {s}" for s in gl.SECTIONS) + f" misses to {gl.MISSES_PATH}")
    return 0


def write_tour_dyn_loft():
    """Print data.TOUR_DYN_LOFT: the live inversion for every Tour row with the shipped model."""
    print("TOUR_DYN_LOFT = {")
    for tour, club, r in gl.rows():
        dl = launch_tools.derive_dyn_loft(r["launch_deg"], r["attack_deg"])
        print(f'    ("{tour}", "{club}"): {dl:.3f},')
    print("}")
    return 0


def write_golden():
    record = gl.golden_record()
    with open(gl.GOLDEN_PATH, "w") as fh:
        json.dump(record, fh, indent=1)
        fh.write("\n")
    print(f"wrote {len(record['cases'])} golden cases to {gl.GOLDEN_PATH}")
    return 0


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--fit", action="store_true", help="refit every parameter and print the tables")
    mode.add_argument("--write-misses", action="store_true", help="regenerate tests/g3_known_misses.json")
    mode.add_argument("--write-tour-dyn-loft", action="store_true", help="print data.TOUR_DYN_LOFT")
    mode.add_argument("--write-golden", action="store_true", help="regenerate tests/golden_launch.json")
    ap.add_argument("--force", action="store_true", help="with --write-misses: accept a worse result")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.force and not args.write_misses:
        build_parser().error("--force applies to --write-misses only")
    if args.write_misses:
        return write_misses(args.force)
    if args.write_tour_dyn_loft:
        return write_tour_dyn_loft()
    if args.write_golden:
        return write_golden()
    if args.fit:
        params, diag = fit_all()
        print_all(params, diag)
        return 0
    print_all(dict(data.LAUNCH_MODEL))
    return 0


if __name__ == "__main__":
    sys.exit(main())
