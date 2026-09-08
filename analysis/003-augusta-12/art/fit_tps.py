"""Round six, integration: fit a thin-plate-spline (TPS) camera to a hero
art candidate instead of a planar homography (issue #11).

fit_camera.py's round-six homography could not reconcile the near field
(creek, tee) with the far field (the green complex's own depth) in either
r6_2 or r6_4: a single 8-degree-of-freedom planar map enforces one
consistent, uncheated perspective, and painterly Augusta-12 art compresses
the green complex's depth by its own amount, different from the model's own
stylized camera and different again from any other painting's. A TPS does
not have that limitation: it is a smooth interpolant that registers every
control point exactly by construction (zero residual at each of its own
landmarks) while staying smooth in between, so a near-field cheat and a
far-field cheat can coexist in the same warp.

This module fits two finalist candidates, both generated with no sketch
reference (round six, Part 1): r6_3 (photoreal painted matte, three
bunkers -- front, back-left, back-right -- matching the model's own bunker
count) and r6_4 (painterly, the round's looks-winner, but only two back
bunkers, no front bunker touching the creek).

Correspondences (CORRESPONDENCES below) are entirely hand-picked from
gridded 1600x900 crops of each candidate (hero_candidates/r6_3_*.png /
r6_4_*.png, generated and discarded by this pass -- the crops themselves
are scratch, not committed). r6_4's creek-far-bank and back-bunker pixels
are the one exception: they are carried over verbatim from round six's own
segmentation code (hero_candidates/r6_4_fit.json), which already measured
them by thresholding rather than by eye, and re-measuring them by hand
would only add noise. Every point in CORRESPONDENCES carries an explicit
"source" tag ("hand" or "r6_4_fit.json") per the brief's requirement to
flag hand-picked landmarks.

TPS formulation (standard): a smooth radial-basis interpolant per output
channel (screen x, screen y),

    f(x, y) = a0 + a1*x + a2*y + sum_i w_i * U(||(x,y) - p_i||)
    U(r) = r^2 * log(r), U(0) = 0

solved as the linear system

    [K + lambda*I   P] [w]   [v]
    [P^T             0] [a] = [0]

where K_ij = U(|p_i - p_j|), P's rows are [1, x_i, y_i], v is the target
pixel channel, and lambda = 1e-6 is a small ridge term for numerical
conditioning (the brief's own suggested value). Two independent 1-D fits
(x-channel, y-channel) share the same control points and the same K/P
matrices.

"Registration" is now leave-one-out residual, not the fitted (in-sample)
residual: a TPS interpolates its own control points exactly by
construction, so the in-sample error is ~0 everywhere and tells us nothing.
Each landmark's honest error is measured by refitting the TPS on every
*other* landmark and predicting the held-out one.

Usage: python3 fit_tps.py --all        (both candidates, this round's pair)
       python3 fit_tps.py r6_3
"""
import json
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import data    # noqa: E402
import model   # noqa: E402
import sketch  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
CANDIDATES_DIR = HERE / "hero_candidates"
CANVAS_W, CANVAS_H = 1600, 900
TPS_LAMBDA = 1e-6

# ---------------------------------------------------------------------------
# Model-side values, read once from sketch.build_scene()/model.py -- nothing
# here is a second, disconnected copy of the model's own geometry.
# ---------------------------------------------------------------------------

_regions, _landmarks = sketch.build_scene()
_geom = _landmarks["geom"]
_left_edge, _right_edge = _landmarks["green_left_right_edge_yd"]

GREEN_CORNERS_YD = {
    # front_left is simultaneously the green polygon's leftmost AND
    # frontmost (nearest-camera) point under sketch.py's own camera --
    # checked directly (project() puts it at both the minimum screen x and
    # the maximum screen y among the four corners). front_right is the
    # rightmost, back_right the backmost (farthest/highest on screen).
    # back_left achieves none of the four screen-space extremes; it is
    # still picked by hand as a fourth, "interior" correspondence, since
    # leaving it out would starve the TPS of any information about the
    # green's far-left region.
    "front_left": (_left_edge, model._front_edge_yd(_left_edge, _geom)),
    "front_right": (_right_edge, model._front_edge_yd(_right_edge, _geom)),
    "back_right": (_right_edge, model._back_edge_yd(_right_edge, _geom)),
    "back_left": (_left_edge, model._back_edge_yd(_left_edge, _geom)),
}
FRONT_BUNKER_YD = _landmarks["front_bunker_centroid_yd"]
BACK_BUNKER_L_YD = _landmarks["back_bunkers"][0]["centroid_yd"]   # x-range (-15,-8)
BACK_BUNKER_R_YD = _landmarks["back_bunkers"][1]["centroid_yd"]   # x-range (6,13)
TEE_MARKERS_YD = _landmarks["tee_markers_yd"]                     # [left, right]


def _creek_far_bank_yd(xs):
    return [(x, model._front_edge_yd(x, _geom)) for x in xs]


CREEK_XS = [-20.0, -10.0, 0.0, 10.0, 20.0]

# ---------------------------------------------------------------------------
# Hand-picked (and, for r6_4's creek/back-bunkers, code-segmented-in-round-
# six) image correspondences. Every entry: model_yd, image_px, source.
# ---------------------------------------------------------------------------

# r6_3's creek far bank and its three bunker centroids come from the same
# color-threshold + largest-connected-component method fit_camera.py used
# in round six (segment_water's percentile-saturation trough, restricted to
# columns right of the bridge since the bridge's stone reads as the same
# low saturation as water and would otherwise poison the mask; largest-3
# sand components inside a y=380..560 band, which cleanly separates the
# three real bunkers from the dogwood/azalea white-flower false positives
# nano-banana painted at similar brightness -- both checked by hand against
# *_landmarks-style crops before being accepted). green front_left/
# front_right are NOT independently detected: they sit exactly on the same
# front_edge_yd curve the creek far bank already measures (the green's
# front edge and the creek's far bank are the same model curve by
# construction -- see sketch.py), so their image pixels are linearly
# interpolated between the two nearest measured creek-bank samples rather
# than re-eyeballed, which is both more accurate and guarantees the two
# curves cannot disagree with each other. green back_left/back_right are
# hand-placed close to the empirically-detected back-bunker centroids they
# sit next to in model space (~1-3 yd away in both x and y).
_R6_3_CREEK_IMG = [(-18.87, 350.0, 573.0), (-9.48, 600.0, 584.0), (-0.09, 850.0, 564.0),
                   (7.42, 1050.0, 563.0), (16.81, 1300.0, 533.0)]
_R6_4_CREEK_IMG = [(-20.0, 170.0, 402.0), (-13.333333333333332, 395.0, 400.0),
                   (-6.666666666666666, 620.0, 456.0), (0.0, 845.0, 459.0),
                   (6.666666666666668, 1070.0, 470.0), (13.333333333333336, 1295.0, 579.0),
                   (20.0, 1520.0, 606.0)]


def _interp_creek_img(creek_img, x):
    """Linear interpolation of the (already measured) creek-bank image
    pixel at an arbitrary model x, between its two bracketing samples."""
    xs = [c[0] for c in creek_img]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1] or xs[i + 1] <= x <= xs[i]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i])
            ux = creek_img[i][1] + t * (creek_img[i + 1][1] - creek_img[i][1])
            uy = creek_img[i][2] + t * (creek_img[i + 1][2] - creek_img[i][2])
            return ux, uy
    raise ValueError(f"x={x} outside creek sample range")


CORRESPONDENCES = {
    "r6_3": (
        [{"label": f"creek_far_bank:{i}", "model_yd": (x, model._front_edge_yd(x, _geom)),
          "image_px": (ux, uy), "source": "detected (largest-component, saturation-trough threshold, bridge columns excluded)"}
         for i, (x, ux, uy) in enumerate(_R6_3_CREEK_IMG)]
        + [
            # comp1 (largest sand blob, 11px from the detected water mask --
            # effectively touching it) is the bunker the model calls
            # "front"; comp2 (the lobe directly above/connected to it) and
            # comp3 (the separate kidney further left) are its two back
            # bunkers. The front bunker's model x (-4, just left of center)
            # does not match its image position (screen-right of center) --
            # an artist-composition choice, not a geometric one, the same
            # kind of empirical (not left/right-preserving) pairing round
            # six's own README documents for r6_2/r6_4's back bunkers.
            {"label": "bunker_front", "model_yd": FRONT_BUNKER_YD, "image_px": (1140.68, 506.08),
             "source": "detected (largest sand component, touches water mask)"},
            {"label": "bunker_backL", "model_yd": BACK_BUNKER_L_YD, "image_px": (655.32, 447.58),
             "source": "detected (2nd-largest sand component)"},
            {"label": "bunker_backR", "model_yd": BACK_BUNKER_R_YD, "image_px": (1171.64, 452.29),
             "source": "detected (3rd-largest sand component)"},
            {"label": "green_front_left", "model_yd": GREEN_CORNERS_YD["front_left"],
             "image_px": _interp_creek_img(_R6_3_CREEK_IMG, GREEN_CORNERS_YD["front_left"][0]),
             "source": "interpolated (on the creek far-bank curve)"},
            {"label": "green_front_right", "model_yd": GREEN_CORNERS_YD["front_right"],
             "image_px": _interp_creek_img(_R6_3_CREEK_IMG, GREEN_CORNERS_YD["front_right"][0]),
             "source": "interpolated (on the creek far-bank curve)"},
            {"label": "green_back_left", "model_yd": GREEN_CORNERS_YD["back_left"], "image_px": (610.0, 465.0),
             "source": "hand (anchored near bunker_backL)"},
            {"label": "green_back_right", "model_yd": GREEN_CORNERS_YD["back_right"], "image_px": (1210.0, 448.0),
             "source": "hand (anchored near bunker_backR)"},
            {"label": "tee_marker:0", "model_yd": TEE_MARKERS_YD[0], "image_px": (330.0, 778.0), "source": "hand"},
            {"label": "tee_marker:1", "model_yd": TEE_MARKERS_YD[1], "image_px": (1310.0, 787.0), "source": "hand"},
        ]
    ),
    "r6_4": (
        [{"label": f"creek_far_bank:{i}", "model_yd": (x, model._front_edge_yd(x, _geom)),
          "image_px": (ux, uy), "source": "r6_4_fit.json (round six's own segment_water detection)"}
         for i, (x, ux, uy) in enumerate(_R6_4_CREEK_IMG)]
        + [
            # r6_4 draws no bunker touching the creek -- no bunker_front entry (see art/README.md, round six Part 1/2).
            {"label": "bunker_backL", "model_yd": BACK_BUNKER_L_YD, "image_px": (992.3368760064412, 359.6447665056361),
             "source": "r6_4_fit.json"},
            {"label": "bunker_backR", "model_yd": BACK_BUNKER_R_YD, "image_px": (1020.5666405638215, 423.2538762725137),
             "source": "r6_4_fit.json"},
            {"label": "green_front_left", "model_yd": GREEN_CORNERS_YD["front_left"],
             "image_px": _interp_creek_img(_R6_4_CREEK_IMG, GREEN_CORNERS_YD["front_left"][0]),
             "source": "interpolated (on the creek far-bank curve)"},
            {"label": "green_front_right", "model_yd": GREEN_CORNERS_YD["front_right"],
             "image_px": _interp_creek_img(_R6_4_CREEK_IMG, GREEN_CORNERS_YD["front_right"][0]),
             "source": "interpolated (on the creek far-bank curve)"},
            {"label": "green_back_left", "model_yd": GREEN_CORNERS_YD["back_left"], "image_px": (960.0, 375.0),
             "source": "hand (anchored near bunker_backL)"},
            {"label": "green_back_right", "model_yd": GREEN_CORNERS_YD["back_right"], "image_px": (1060.0, 420.0),
             "source": "hand (anchored near bunker_backR)"},
            {"label": "tee_marker:0", "model_yd": TEE_MARKERS_YD[0], "image_px": (249.3405172413793, 708.1508620689655),
             "source": "r6_4_fit.json"},
            {"label": "tee_marker:1", "model_yd": TEE_MARKERS_YD[1], "image_px": (1200.0653266331658, 707.4874371859296),
             "source": "r6_4_fit.json"},
        ]
    ),
}


# ---------------------------------------------------------------------------
# Thin-plate spline
# ---------------------------------------------------------------------------

def _u(r):
    with np.errstate(divide="ignore", invalid="ignore"):
        out = r * r * np.log(r)
    return np.where(r <= 1e-12, 0.0, out)


def _pairwise_u(a, b):
    d = a[:, None, :] - b[None, :, :]
    r = np.sqrt((d ** 2).sum(axis=-1))
    return _u(r)


def fit_tps_channel(src, vals, lam=TPS_LAMBDA):
    """src: (n,2) model-yd control points. vals: (n,) one pixel channel.
    Returns (w (n,), a (3,)) -- RBF weights and the affine term [a0,a1,a2]."""
    n = len(src)
    K = _pairwise_u(src, src) + lam * np.eye(n)
    P = np.hstack([np.ones((n, 1)), src])
    A = np.zeros((n + 3, n + 3))
    A[:n, :n] = K
    A[:n, n:] = P
    A[n:, :n] = P.T
    b = np.zeros(n + 3)
    b[:n] = vals
    sol = np.linalg.solve(A, b)
    return sol[:n], sol[n:]


def eval_tps_channel(src, w, a, query):
    """query: (m,2). Returns (m,) predicted pixel channel."""
    U = _pairwise_u(query, src)
    return a[0] + query[:, 0] * a[1] + query[:, 1] * a[2] + U @ w


class TPSCamera:
    """Two independent TPS fits (screen x, screen y) sharing one set of
    model-yard control points. project(x, y) -> (px, py)."""

    def __init__(self, src, dst_x, dst_y, lam=TPS_LAMBDA):
        self.src = np.asarray(src, dtype=np.float64)
        self.wx, self.ax = fit_tps_channel(self.src, np.asarray(dst_x, dtype=np.float64), lam)
        self.wy, self.ay = fit_tps_channel(self.src, np.asarray(dst_y, dtype=np.float64), lam)

    def project_many(self, xy):
        xy = np.asarray(xy, dtype=np.float64)
        px = eval_tps_channel(self.src, self.wx, self.ax, xy)
        py = eval_tps_channel(self.src, self.wy, self.ay, xy)
        return px, py

    def project(self, x, y):
        px, py = self.project_many(np.array([[x, y]]))
        return float(px[0]), float(py[0])


def fit_camera(corr):
    src = np.array([c["model_yd"] for c in corr], dtype=np.float64)
    dst = np.array([c["image_px"] for c in corr], dtype=np.float64)
    return TPSCamera(src, dst[:, 0], dst[:, 1])


def leave_one_out_residuals(corr):
    src = np.array([c["model_yd"] for c in corr], dtype=np.float64)
    dst = np.array([c["image_px"] for c in corr], dtype=np.float64)
    n = len(corr)
    rows = []
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        cam_loo = TPSCamera(src[mask], dst[mask, 0], dst[mask, 1])
        pred_x, pred_y = cam_loo.project(*src[i])
        err_px = float(np.hypot(pred_x - dst[i, 0], pred_y - dst[i, 1]))
        rows.append({
            "label": corr[i]["label"],
            "source": corr[i]["source"],
            "model_yd": [float(src[i, 0]), float(src[i, 1])],
            "image_px": [float(dst[i, 0]), float(dst[i, 1])],
            "loo_predicted_px": [float(pred_x), float(pred_y)],
            "loo_error_px": err_px,
            "loo_error_pct_width": 100.0 * err_px / CANVAS_W,
        })
    return rows


# ---------------------------------------------------------------------------
# Monotonicity check
# ---------------------------------------------------------------------------

def check_monotonicity(cam):
    """Centerline x=0: screen y must decrease as model y increases 0->200.
    Across x at y=155: screen x must increase with model x. Returns a dict
    with both traces and a list of fold descriptions (empty if none)."""
    folds = []

    ys = np.linspace(0.0, 200.0, 101)
    xs0 = np.zeros_like(ys)
    _, py = cam.project_many(np.stack([xs0, ys], axis=1))
    d = np.diff(py)
    bad = np.where(d > 0)[0]
    for i in bad:
        folds.append(f"centerline fold: screen_y increased from y={ys[i]:.1f}yd (py={py[i]:.1f}) "
                      f"to y={ys[i+1]:.1f}yd (py={py[i+1]:.1f})")

    xs = np.linspace(-30.0, 30.0, 121)
    ys155 = np.full_like(xs, 155.0)
    px, _ = cam.project_many(np.stack([xs, ys155], axis=1))
    d2 = np.diff(px)
    bad2 = np.where(d2 < 0)[0]
    for i in bad2:
        folds.append(f"lateral fold at y=155yd: screen_x decreased from x={xs[i]:.1f}yd (px={px[i]:.1f}) "
                      f"to x={xs[i+1]:.1f}yd (px={px[i+1]:.1f})")

    return {
        "centerline_y_yd": ys.tolist(), "centerline_screen_py": py.tolist(),
        "lateral_x_yd": xs.tolist(), "lateral_screen_px": px.tolist(),
        "folds": folds,
    }


# ---------------------------------------------------------------------------
# Overlay
# ---------------------------------------------------------------------------

def load_resized(name):
    im = Image.open(CANDIDATES_DIR / f"{name}.png").convert("RGB")
    if im.size != (CANVAS_W, CANVAS_H):
        im = im.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
    return im


def draw_overlay(name, cam, corr):
    im = load_resized(name)
    draw = ImageDraw.Draw(im)

    def proj(x, y):
        return cam.project(x, y)

    def poly_px(poly_yd):
        return [proj(x, y) for x, y in poly_yd]

    # Coordinate grid: every 10yd in x, every 20yd in y, 0..200.
    for x in range(-30, 31, 10):
        pts = [proj(x, y) for y in np.linspace(0, 200, 41)]
        draw.line(pts, fill=(255, 255, 255), width=1)
    for y in range(0, 201, 20):
        pts = [proj(x, y) for x in np.linspace(-30, 30, 41)]
        draw.line(pts, fill=(255, 255, 255), width=1)

    creek_pts = [proj(x, model._front_edge_yd(x, _geom)) for x in np.linspace(-20, 20, 60)]
    draw.line(creek_pts, fill="#00CFFF", width=3)

    draw.polygon(poly_px(_regions["green"]), outline="#00FF66", width=3)
    if any(c["label"] == "bunker_front" for c in corr):
        draw.polygon(poly_px(_regions["front_bunker"]), outline="#FF7A00", width=3)
    for bb in _regions["back_bunkers"]:
        draw.polygon(poly_px(bb["poly"]), outline="#FF7A00", width=3)
    draw.polygon(poly_px(_regions["tee"]), outline="#FFFFFF", width=3)

    for key, p in data.PINS.items():
        px, py = proj(p["x"], p["y"])
        r = 10
        draw.line([(px - r, py - r), (px + r, py + r)], fill="#FF00AA", width=3)
        draw.line([(px - r, py + r), (px + r, py - r)], fill="#FF00AA", width=3)

    out_path = CANDIDATES_DIR / f"{name}_tps_overlay.png"
    im.save(out_path)
    return out_path


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def run(name):
    corr = CORRESPONDENCES[name]
    cam = fit_camera(corr)
    loo = leave_one_out_residuals(corr)
    mono = check_monotonicity(cam)

    max_err = max(r["loo_error_px"] for r in loo)
    mean_err = float(np.mean([r["loo_error_px"] for r in loo]))
    max_pct = max(r["loo_error_pct_width"] for r in loo)
    mean_pct = float(np.mean([r["loo_error_pct_width"] for r in loo]))

    src = cam.src.tolist()
    dst = np.array([c["image_px"] for c in corr]).tolist()

    report = {
        "candidate": name,
        "canvas": [CANVAS_W, CANVAS_H],
        "control_points_yd": src,
        "targets_px": dst,
        "labels": [c["label"] for c in corr],
        "sources": [c["source"] for c in corr],
        "weights": {"wx": cam.wx.tolist(), "wy": cam.wy.tolist()},
        "affine": {"ax": cam.ax.tolist(), "ay": cam.ay.tolist()},
        "lambda": TPS_LAMBDA,
        "leave_one_out": loo,
        "residual_summary": {
            "max_error_px": max_err, "mean_error_px": mean_err,
            "max_error_pct_width": max_pct, "mean_error_pct_width": mean_pct,
            "n_correspondences": len(loo),
        },
        "monotonicity": {"folds": mono["folds"]},
        "has_front_bunker": any(c["label"] == "bunker_front" for c in corr),
    }
    (CANDIDATES_DIR / f"{name}_tps.json").write_text(json.dumps(report, indent=2))
    draw_overlay(name, cam, corr)

    print(f"--- {name} ---")
    print(json.dumps(report["residual_summary"], indent=2))
    print("folds:", mono["folds"] if mono["folds"] else "none")
    return report, cam


if __name__ == "__main__":
    args = sys.argv[1:]
    names = ["r6_3", "r6_4"] if (not args or args == ["--all"]) else args
    for n in names:
        run(n)
