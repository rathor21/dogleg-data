"""Fit a pinhole camera to a painted driving-range image (numpy only).

Usage:
    python fit_camera.py landmarks_final.json camera_final.json
    python fit_camera.py landmarks_final_mobile.json camera_final_mobile.json

PROJECTION FORMULA (the page's JS reimplements exactly this)
------------------------------------------------------------
World frame, units yards:
    x = downrange along the target line, y = lateral (positive to the RIGHT as
    seen from behind the golfer), z = up. Origin at the ball on the mat.
Camera parameters: f (px), cx, cy (principal point, image centre), position
C = (xc, yc, zc), yaw psi, pitch th, roll phi (radians in the maths, degrees in
the JSON).

Camera basis, expressed in world coordinates:
    fwd  = ( cos th * cos psi,  cos th * sin psi, -sin th)     # optical axis
    r0   = (-sin psi,           cos psi,           0      )     # right, no roll
    u0   = ( sin th * cos psi,  sin th * sin psi,  cos th )     # up, no roll
    right = r0 * cos phi + u0 * sin phi
    up    = -r0 * sin phi + u0 * cos phi
Positive yaw turns the camera toward +y (to the right). Positive pitch tilts the
camera DOWN. Positive roll rotates the image so that its right edge goes up
(counter-clockwise on screen as the picture is viewed).

Project a world point P:
    d  = P - C
    Xc = d . right
    Yc = d . up
    Zc = d . fwd            (depth, must be > 0)
    u  = cx + f * Xc / Zc
    v  = cy - f * Yc / Zc   (v grows downward, like image rows)

Back-project a pixel (u, v) onto the ground plane z = 0:
    ray = fwd + ((u - cx) / f) * right - ((v - cy) / f) * up
    t   = -zc / ray_z        (needs ray_z < 0, i.e. the pixel is below the horizon)
    P   = C + t * ray        -> (x, y, 0)

FIT
---
Fixed by assumption: camera height zc, camera 3 yd behind the ball (xc = -3),
yc = 0 (camera on the target line), principal point at the image centre.
Solved by Levenberg-Marquardt (numeric Jacobian): f, pitch, yaw, roll, stripe
width w, stripe offset y0, the lateral offsets of the left and right floodlight
pole rows, and the pole height H. Residuals (pixels):
  - each measured point on a straight ground line (centre line y=0, stripe edges
    y=y0+k*w, pole bases y=yL or yR at z=0, pole tops at z=H) is scored by its
    perpendicular pixel distance to the projected line;
  - the ball pixel, scored by its 2D distance to the projection of (0,0,0).
A weak prior holds roll near 0. Stripe integer indices k are found by search.
"""
import itertools
import json
import sys

import numpy as np

XC = -3.0
ZC = 1.8


def basis(yaw, pitch, roll):
    cy_, sy_ = np.cos(yaw), np.sin(yaw)
    cp, sp = np.cos(pitch), np.sin(pitch)
    fwd = np.array([cp * cy_, cp * sy_, -sp])
    r0 = np.array([-sy_, cy_, 0.0])
    u0 = np.array([sp * cy_, sp * sy_, cp])
    cr, sr = np.cos(roll), np.sin(roll)
    right = r0 * cr + u0 * sr
    up = -r0 * sr + u0 * cr
    return fwd, right, up


def project(P, cam):
    """cam: dict with f, cx, cy, C, yaw, pitch, roll (radians). Returns (u, v, depth)."""
    fwd, right, up = basis(cam["yaw"], cam["pitch"], cam["roll"])
    d = np.asarray(P, float) - np.asarray(cam["C"], float)
    xc, yc, zc = d @ right, d @ up, d @ fwd
    return cam["cx"] + cam["f"] * xc / zc, cam["cy"] - cam["f"] * yc / zc, zc


def backproject_ground(u, v, cam):
    fwd, right, up = basis(cam["yaw"], cam["pitch"], cam["roll"])
    ray = fwd + ((u - cam["cx"]) / cam["f"]) * right - ((v - cam["cy"]) / cam["f"]) * up
    if ray[2] >= -1e-9:
        return None
    t = -cam["C"][2] / ray[2]
    P = np.asarray(cam["C"], float) + t * ray
    return float(P[0]), float(P[1])


def make_cam(p, W, H, zc):
    return dict(f=p[0], pitch=p[1], yaw=p[2], roll=p[3], cx=W / 2.0, cy=H / 2.0,
                C=(XC, 0.0, zc))


PNAMES = ["f", "pitch", "yaw", "roll", "w", "y0", "yL", "yR", "H"]


def line_dist(pt, cam, y, z):
    a = project((5.0, y, z), cam)
    b = project((3000.0, y, z), cam)
    if a[2] <= 0 or b[2] <= 0:
        return 500.0
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    L = np.hypot(bx - ax, by - ay)
    if L < 1e-6:
        return 500.0
    return ((bx - ax) * (pt[1] - ay) - (by - ay) * (pt[0] - ax)) / L


def residuals(p, lm, ks, W, H, zc, weights):
    cam = make_cam(p, W, H, zc)
    w, y0, yL, yR, Hp = p[4], p[5], p[6], p[7], p[8]
    res = []
    for ln in lm["lines"]:
        kind = ln["kind"]
        if kind == "center":
            y, z = 0.0, 0.0
        elif kind == "stripe":
            y, z = y0 + ks[ln["name"]] * w, 0.0
        elif kind == "pole":
            y = yL if ln["side"] == "left" else yR
            z = Hp if ln["level"] == "top" else 0.0
        else:
            raise ValueError(kind)
        wt = weights[kind]
        for pt in ln["points"]:
            res.append(wt * line_dist(pt, cam, y, z))
    bu, bv, _ = project((0, 0, 0), cam)
    res.append(weights["ball"] * (bu - lm["ball"][0]))
    res.append(weights["ball"] * (bv - lm["ball"][1]))
    res.append(weights["roll_prior"] * np.degrees(p[3]))
    return np.array(res)


def lm_fit(p0, fun, lo, hi, iters=80):
    p = np.array(p0, float)
    lam = 1e-2
    r = fun(p)
    cost = r @ r
    for _ in range(iters):
        J = np.zeros((len(r), len(p)))
        for i in range(len(p)):
            h = 1e-5 * max(1.0, abs(p[i]))
            q = p.copy()
            q[i] += h
            J[:, i] = (fun(q) - r) / h
        A = J.T @ J
        g = J.T @ r
        improved = False
        for _ in range(12):
            try:
                dp = -np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-9), g)
            except np.linalg.LinAlgError:
                lam *= 10
                continue
            q = np.clip(p + dp, lo, hi)
            rq = fun(q)
            cq = rq @ rq
            if cq < cost:
                p, r, cost = q, rq, cq
                lam = max(lam / 3, 1e-9)
                improved = True
                break
            lam *= 4
        if not improved:
            break
    return p, cost


def main():
    lm_path, out_path = sys.argv[1], sys.argv[2]
    zc = float(sys.argv[3]) if len(sys.argv) > 3 else ZC
    lm = json.load(open(lm_path))
    W, H = lm["width"], lm["height"]
    weights = dict(center=1.0, pole=1.0, stripe=lm.get("stripe_weight", 0.35), ball=0.4,
                   roll_prior=2.0)
    stripes = [ln["name"] for ln in lm["lines"] if ln["kind"] == "stripe"]
    lo = np.array([200, np.radians(-5), np.radians(-15), np.radians(-5), 3.0, -20, -80, 0, 0.5])
    hi = np.array([2500, np.radians(35), np.radians(15), np.radians(5), 12.0, 20, 0, 80, 60])
    # Stage 1: everything except the stripes (poles, centre line, ball), a few starts.
    fun0 = lambda p: residuals(p, lm, {n: 0 for n in stripes}, W, H, zc,
                               dict(weights, stripe=0.0))
    best0 = None
    for f0 in (500.0, 800.0, 1200.0):
        for th0 in (0.03, 0.12, 0.25):
            p0 = [f0, th0, 0.0, 0.0, 6.0, 0.0, -8.0, 9.0, 3.0]
            p, c = lm_fit(p0, fun0, lo, hi)
            if best0 is None or c < best0[1]:
                best0 = (p, c)
    # Stage 2: stripes. Camera fixed at the stage 1 solution; choose the integer indices k
    # (unique) and solve stripe width w and offset y0 for each combination by linear least
    # squares on the pixel residual (lines are linear in w and y0 for fixed k). The stripe
    # lines are advisory: they do not move the camera (see README, they disagree with the
    # pole rows about the vanishing row).
    cam0 = make_cam(best0[0], W, H, zc)
    best = None
    combos = itertools.product(range(-4, 5), repeat=len(stripes)) if stripes else [()]
    ln_by_name = {ln["name"]: ln for ln in lm["lines"]}
    for combo in combos:
        if len(set(combo)) != len(combo):
            continue
        for w in np.arange(4.0, 8.01, 0.25):
            # y0 by 1-D golden-free scan (cheap: 3 lines only)
            for y0 in np.arange(-12.0, 12.01, 0.5):
                c = 0.0
                for name, k in zip(stripes, combo):
                    y = y0 + k * w
                    for pt in ln_by_name[name]["points"]:
                        c += line_dist(pt, cam0, y, 0.0) ** 2
                if best is None or c < best[1]:
                    best = (w, c, y0, dict(zip(stripes, combo)))
    p = best0[0].copy()
    if stripes:
        p[4], p[5], ks = best[0], best[2], best[3]
    else:
        ks = {}
    best = (p, best0[1], ks)
    p, c, ks = best
    cam = make_cam(p, W, H, zc)
    # unweighted RMS over all line points and the ball (pixels)
    pix = []
    for ln in lm["lines"]:
        kind = ln["kind"]
        if kind == "center":
            y, z = 0.0, 0.0
        elif kind == "stripe":
            y, z = p[5] + ks[ln["name"]] * p[4], 0.0
        else:
            y = p[6] if ln["side"] == "left" else p[7]
            z = p[8] if ln["level"] == "top" else 0.0
        for pt in ln["points"]:
            pix.append(line_dist(pt, cam, y, z))
    bu, bv, _ = project((0, 0, 0), cam)
    pix.append(np.hypot(bu - lm["ball"][0], bv - lm["ball"][1]))
    # headline RMS: camera-defining constraints only (centre line, pole rows, ball)
    npts = [len(ln["points"]) for ln in lm["lines"]]
    core = []
    i = 0
    for ln, n in zip(lm["lines"], npts):
        if ln["kind"] != "stripe":
            core.extend(pix[i:i + n])
        i += n
    core.append(pix[-1])
    rms = float(np.sqrt(np.mean(np.square(core))))
    per_kind = {}
    i = 0
    for ln in lm["lines"]:
        k = ln["kind"]
        n = len(ln["points"])
        per_kind.setdefault(k, []).extend(pix[i:i + n])
        i += n
    per_kind_rms = {k: round(float(np.sqrt(np.mean(np.square(v)))), 2) for k, v in per_kind.items()}
    greens = []
    for g in lm.get("greens", []):
        gp = backproject_ground(*g["center"], cam)
        gl = backproject_ground(*g["left"], cam)
        gr = backproject_ground(*g["right"], cam)
        greens.append(dict(name=g["name"], pixel=g["center"],
                           ground_yd=[round(gp[0], 1), round(gp[1], 1)] if gp else None,
                           left_edge_yd=[round(gl[0], 1), round(gl[1], 1)] if gl else None,
                           right_edge_yd=[round(gr[0], 1), round(gr[1], 1)] if gr else None))
    vp = project((1e6, 0, 0), cam)
    out = dict(
        image=lm["image"], width=W, height=H, f=round(float(p[0]), 2), cx=W / 2.0, cy=H / 2.0,
        cam_pos=[XC, 0.0, zc],
        yaw_deg=round(float(np.degrees(p[2])), 3), pitch_deg=round(float(np.degrees(p[1])), 3),
        roll_deg=round(float(np.degrees(p[3])), 3),
        residual_px_rms=round(rms, 2), residual_by_kind=per_kind_rms,
        residual_note="residual_px_rms covers the centre line, pole rows and ball anchor. Stripe lines are advisory (see residual_by_kind.stripe).",
        horizon_row=round(float(vp[1]), 1), vanishing_point=[round(float(vp[0]), 1), round(float(vp[1]), 1)],
        stripe_width_yd=round(float(p[4]), 2) if stripes else None,
        stripe_offset_yd=round(float(p[5]), 2) if stripes else None,
        stripe_indices=ks, pole_row_lateral_yd=dict(left=round(float(p[6]), 2), right=round(float(p[7]), 2)),
        pole_height_yd=round(float(p[8]), 2),
        assumptions=[
            f"camera height zc = {zc} yd above the ground (standing viewer's eye)",
            "camera 3 yd behind the ball (x = -3) and on the target line (y = 0)",
            "principal point at the image centre, square pixels, no lens distortion",
            "ball at the marked mat pixel (no ball is painted, mat centre used)",
            "mowing stripes parallel to the target line with constant width",
            "floodlight poles are vertical, equal height, in a straight row per side",
            "ground is flat (z = 0)",
        ],
        greens=greens,
        projection=("u = cx + f*Xc/Zc ; v = cy - f*Yc/Zc with Xc,Yc,Zc = (P-C).right, (P-C).up, (P-C).fwd; "
                    "see fit_camera.py docstring"),
    )
    json.dump(out, open(out_path, "w"), indent=2)
    print(json.dumps({k: v for k, v in out.items() if k not in ("assumptions", "projection")}, indent=1))


if __name__ == "__main__":
    main()
