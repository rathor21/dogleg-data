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
import math
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import data    # noqa: E402
import model   # noqa: E402
import sketch  # noqa: E402
import fit_camera as fc  # noqa: E402 -- reuses round six's normalized-DLT homography fit

HERE = pathlib.Path(__file__).resolve().parent
CANDIDATES_DIR = HERE / "hero_candidates"
CANVAS_W, CANVAS_H = 1600, 900
TPS_LAMBDA = 1e-6

# Round seven's own regularization, used only for the final r6_4 build (see
# build_r6_4_correspondences_v2/__main__ below), not for r6_3 or for the
# per-landmark exactness this module's docstring otherwise promises.
#
# The near-exact fit (TPS_LAMBDA=1e-6) registers every real landmark almost
# exactly, but a thin-plate spline minimizes bending energy subject to
# hitting every control point exactly -- and a handful of real landmarks
# here (bunker centroids and green-boundary points measured or interpolated
# by different methods) are not perfectly mutually consistent with a single
# smooth ground plane. Forcing exact interpolation through slightly
# inconsistent points, even with a dense synthetic backbone in between,
# produced flight paths that loop back on themselves: verified by removing
# every real landmark and fitting the synthetic backbone alone (same
# loops), by densifying the backbone up to 15x20 (same loops), and by
# replacing raw-pixel targets with homography-baseline residuals (loops
# persisted, just smaller). Only relaxing exact interpolation removed them.
# A sweep over lambda (self-intersection count via segment-pair testing on
# all 5 curated shots' actual flight paths, monotonicity folds, and whether
# all 3 pins still land inside the green-boundary polygon) found:
#   lambda <  50: still folds in the centerline check (tiny, sub-few-px,
#     but present) and/or an occasional self-intersection on a curved shot.
#   lambda =  60: zero self-intersections across all 5 shots, zero folds,
#     all 3 pins inside the green, max real-landmark error 59px (3.7% of
#     canvas width) -- the smallest lambda in the sweep clearing every bar.
#   lambda >= 300: pins start falling outside the green boundary as the
#     fit over-smooths toward the (imperfect) homography backbone.
# 60 is the chosen value: the least smoothing that satisfies every
# acceptance check, not a round number picked for convenience.
R6_4_LAMBDA = 60

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
# Round seven (correction pass): a perspective backbone plus a green-
# boundary correspondence set, replacing r6_4's sparse 15-point fit above.
#
# The round-six TPS registered every landmark it was given, but it was only
# given landmarks at the green complex (y=124-184yd) and at the tee
# (y=-1yd) -- a 125-yard stretch of model depth with nothing in between. A
# TPS is a smooth interpolant with no notion of "ground plane," so across
# that empty stretch it bent however the RBF terms happened to want to,
# which is what produced looping flight arcs and an exploded lateral scale
# near the tee. Likewise, the green was constrained by only its four
# parallelogram corners, so interior points (the pins) had nothing nearby
# to anchor to and could interpolate outside the painted green's own oval
# footprint.
#
# The fix has two parts:
#   1. A perspective backbone: fit a plain homography H0 on the tee markers
#      plus the creek far-bank samples (the same 9-point pairing round
#      six's own diagnostic fit already showed works reasonably, see
#      art/README.md round six Part 2/"headline finding"), then generate a
#      5x5 grid of SYNTHETIC control points across the fairway
#      (x=-15..15yd, y=5..120yd) by projecting through H0. These fill the
#      empty depth range with a smooth, if imperfect, perspective guess --
#      enough to keep the TPS from bending freely there. Tagged
#      "source": "synthetic_h0".
#   2. Eight green-boundary correspondences sampled every 45 degrees by
#      angle from the green polygon's own centroid, matched to the painted
#      green's boundary at the same angle. Four of these fall on the front
#      (creek-side) edge, where the far-bank curve already gives an exact
#      pixel; the other four (right/back/left edges) are hand-anchored,
#      interpolated linearly in pixel space between the two nearest
#      previously-accepted green-corner picks -- see green_boundary_points
#      below for the reasoning and README round seven for the crops this
#      was checked against.
# ---------------------------------------------------------------------------

H0_SRC = (
    [(x, model._front_edge_yd(x, _geom)) for x, _, _ in _R6_4_CREEK_IMG]
    + [tuple(TEE_MARKERS_YD[0]), tuple(TEE_MARKERS_YD[1])]
)
H0_DST = (
    [(u, v) for _, u, v in _R6_4_CREEK_IMG]
    + [(249.3405172413793, 708.1508620689655), (1200.0653266331658, 707.4874371859296)]
)


def fit_h0_backbone():
    """Homography fit on the 9-point tee+creek pairing (round six's own
    diagnostic showed this reconciles the near field on its own -- see
    art/README.md round six, "the headline finding"). Returns (H, per-point
    residuals in px), so callers can check whether the tee markers land
    within the brief's 5px bar for dropping them as separate TPS control
    points."""
    H = fc.fit_homography_dlt(H0_SRC, H0_DST)
    residuals = []
    for (x, y), (u, v) in zip(H0_SRC, H0_DST):
        pu, pv = fc.apply_homography(H, x, y)
        residuals.append(float(np.hypot(pu - u, pv - v)))
    return H, residuals


SYNTHETIC_XS_YD = [-15.0, -7.5, 0.0, 7.5, 15.0]
# The brief's own grid is 5,35,65,95,120; a 140yd row was added after the
# first fit showed a kink in the seam between the backbone's last row (120)
# and the real creek/green data (starting ~124.5yd) -- exactly the failure
# mode the brief's own note anticipated ("add a synthetic row at y=140 if
# the transition into the green complex kinks"). See README round seven.
SYNTHETIC_YS_YD = [5.0, 35.0, 65.0, 95.0, 120.0, 140.0]


def synthetic_grid_points(H):
    """5x5 fairway grid, projected through H0, tagged synthetic_h0. These
    are not real landmarks -- they carry no independent evidence about the
    art, only H0's own (imperfect but smooth) perspective guess -- so
    leave-one-out residuals are not reported for them (see run(), which
    filters the printed/committed table to real landmarks only)."""
    pts = []
    for y in SYNTHETIC_YS_YD:
        for x in SYNTHETIC_XS_YD:
            u, v = fc.apply_homography(H, x, y)
            pts.append({
                "label": f"synthetic_h0:{x:g},{y:g}",
                "model_yd": (x, y),
                "image_px": (u, v),
                "source": "synthetic_h0",
            })
    return pts


# Green parallelogram corners: front_left/front_right on the creek far-bank
# curve (interpolated, exact by construction since the green's front edge
# and the creek's far bank are the same model curve); back_left/back_right
# are round six's own accepted hand picks (camera_tps.json's prior
# green_back_left/back_right targets), kept as-is rather than re-picked --
# they are still inside the painted grass shelf (checked by eye against the
# gridded crops in hero_candidates/), and re-picking them fresh would only
# add noise on top of an already-inspected pair.
_GREEN_CORNERS_PX_R6_4 = {
    "front_left": _interp_creek_img(_R6_4_CREEK_IMG, GREEN_CORNERS_YD["front_left"][0]),
    "front_right": _interp_creek_img(_R6_4_CREEK_IMG, GREEN_CORNERS_YD["front_right"][0]),
    "back_right": (1060.0, 420.0),
    "back_left": (960.0, 375.0),
}


def _green_centroid_yd():
    corners = [GREEN_CORNERS_YD[k] for k in ("front_left", "front_right", "back_right", "back_left")]
    cx = sum(c[0] for c in corners) / 4.0
    cy = sum(c[1] for c in corners) / 4.0
    return cx, cy


def _ray_polygon_intersect(cx, cy, angle_deg, poly):
    """First edge a ray from (cx, cy) at angle_deg hits, poly given as an
    ordered list of (x, y) vertices. Returns (point, edge_index)."""
    theta = math.radians(angle_deg)
    dx, dy = math.cos(theta), math.sin(theta)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        ex, ey = x2 - x1, y2 - y1
        denom = dx * ey - dy * ex
        if abs(denom) < 1e-9:
            continue
        s = ((x1 - cx) * dy - (y1 - cy) * dx) / denom
        t = ((x1 - cx) * ey - (y1 - cy) * ex) / denom
        if -1e-9 <= s <= 1 + 1e-9 and t > 1e-9:
            return (cx + t * dx, cy + t * dy), i
    return None, None


def green_boundary_points():
    """Eight points around the green polygon's boundary, sampled every 45
    degrees by angle from its own centroid (0deg = +x/east, going
    counterclockwise), each matched to the painted green at the same angle.

    Edge 0 (front_left->front_right, the creek-side edge) is sampled off
    the creek far-bank curve directly -- exact, not a hand guess, since
    that curve and the green's front edge are the identical model curve.
    Edges 1/2/3 (right/back/left) have no comparably reliable painted
    boundary: r6_4's putting surface is a smooth, continuously-shaded patch
    with no hue/saturation break from the fairway around it (the same
    finding round six's own segment_green hit), so those three points are
    linearly interpolated in PIXEL space between the two nearest
    previously-accepted green-corner picks bounding that edge -- e.g. the
    right-edge midpoint sits halfway (by the model's own y-fraction)
    between front_right's and back_right's pixels. This is a declared
    approximation, not a detection: every point derived this way is tagged
    "interpolated (linear, hand-picked green corners)". Colors were sampled
    at each resulting pixel against art/hero.png as a sanity check (all
    land on grass, none on sand/water/mulch -- see README round seven).

    Any point landing within 0.2yd of an existing creek_far_bank sample
    (front-edge points near x=0 and x=6.667 do, since 45-degree sampling
    happens to land close to those two model x's) is dropped as a
    duplicate correspondence -- it would otherwise put two near-identical
    rows in the TPS's K matrix for no new information.
    """
    cx, cy = _green_centroid_yd()
    corners_yd = [GREEN_CORNERS_YD[k] for k in ("front_left", "front_right", "back_right", "back_left")]
    corners_px = [_GREEN_CORNERS_PX_R6_4[k] for k in ("front_left", "front_right", "back_right", "back_left")]

    def edge_px(edge_idx, pt_yd):
        """Pixel for a point known to lie on edge edge_idx of the
        parallelogram (0=front, 1=right, 2=back, 3=left)."""
        x, y = pt_yd
        if edge_idx == 0:
            return _interp_creek_img(_R6_4_CREEK_IMG, x)
        p1_yd, p2_yd = corners_yd[edge_idx], corners_yd[(edge_idx + 1) % 4]
        p1_px, p2_px = corners_px[edge_idx], corners_px[(edge_idx + 1) % 4]
        # Parametrize by whichever coordinate actually varies along this edge.
        if abs(p2_yd[0] - p1_yd[0]) > abs(p2_yd[1] - p1_yd[1]):
            t = (x - p1_yd[0]) / (p2_yd[0] - p1_yd[0])
        else:
            t = (y - p1_yd[1]) / (p2_yd[1] - p1_yd[1])
        return (p1_px[0] + t * (p2_px[0] - p1_px[0]), p1_px[1] + t * (p2_px[1] - p1_px[1]))

    creek_xs = [c[0] for c in _R6_4_CREEK_IMG]
    out = []
    for ang in range(0, 360, 45):
        pt, edge_idx = _ray_polygon_intersect(cx, cy, ang, corners_yd)
        if pt is None:
            continue
        if edge_idx == 0 and any(abs(pt[0] - cxs) < 0.2 for cxs in creek_xs):
            continue  # duplicate of an existing creek_far_bank sample
        px = edge_px(edge_idx, pt)
        edge_name = ["front", "right", "back", "left"][edge_idx]
        out.append({
            "label": f"green_boundary:{ang}deg({edge_name})",
            "model_yd": pt,
            "image_px": px,
            "source": ("interpolated (on the creek far-bank curve)" if edge_idx == 0
                       else "interpolated (linear, hand-picked green corners)"),
        })
    return out


def build_r6_4_correspondences_v2():
    """Round seven's full r6_4 correspondence set: the original creek
    samples and back-bunker centroids (kept, per the brief), the new
    8-point (minus duplicates) green boundary, the raw tee markers (kept as
    direct TPS control points -- H0 does not reproduce them within 5px, see
    the module docstring and README), and the 5x5 synthetic fairway grid."""
    H0, h0_residuals = fit_h0_backbone()
    tee_residuals = h0_residuals[-2:]  # last two H0_SRC/DST entries are the tee markers
    keep_raw_tee = any(r > 5.0 for r in tee_residuals)

    base = [c for c in CORRESPONDENCES["r6_4"]
            if c["label"].startswith("creek_far_bank") or c["label"].startswith("bunker_back")]
    green_pts = green_boundary_points()
    tee_pts = [c for c in CORRESPONDENCES["r6_4"] if c["label"].startswith("tee_marker")] if keep_raw_tee else []
    synthetic_pts = synthetic_grid_points(H0)

    corr = base + green_pts + tee_pts + synthetic_pts
    return corr, {"H0": H0.tolist(), "H0_residuals_px": h0_residuals, "tee_residuals_px": tee_residuals,
                  "kept_raw_tee_markers": keep_raw_tee}


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


def leave_one_out_residuals(corr, lam=TPS_LAMBDA):
    src = np.array([c["model_yd"] for c in corr], dtype=np.float64)
    dst = np.array([c["image_px"] for c in corr], dtype=np.float64)
    n = len(corr)
    rows = []
    for i in range(n):
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        cam_loo = TPSCamera(src[mask], dst[mask, 0], dst[mask, 1], lam=lam)
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

# Lateral fold checks: 155 is the original centerline-ish check; 140/170/183
# span the green complex's own front-to-back depth (front edge 131.75-157.25,
# back edge 158.25-183.75 across the green's width) -- the brief's "fold
# check ... across the green depth," not just at one representative y.
LATERAL_CHECK_YS_YD = [140.0, 155.0, 170.0, 183.0]


def check_monotonicity(cam, lateral_ys=LATERAL_CHECK_YS_YD):
    """Centerline x=0: screen y must decrease as model y increases 0->200.
    Across x at each y in lateral_ys: screen x must increase with model x.
    Returns a dict with every trace and a list of fold descriptions (empty
    if none)."""
    folds = []

    ys = np.linspace(0.0, 200.0, 101)
    xs0 = np.zeros_like(ys)
    _, py = cam.project_many(np.stack([xs0, ys], axis=1))
    d = np.diff(py)
    bad = np.where(d > 0)[0]
    for i in bad:
        folds.append(f"centerline fold: screen_y increased from y={ys[i]:.1f}yd (py={py[i]:.1f}) "
                      f"to y={ys[i+1]:.1f}yd (py={py[i+1]:.1f})")

    lateral_traces = {}
    xs = np.linspace(-30.0, 30.0, 121)
    for y_level in lateral_ys:
        ys_level = np.full_like(xs, y_level)
        px, _ = cam.project_many(np.stack([xs, ys_level], axis=1))
        lateral_traces[y_level] = px.tolist()
        d2 = np.diff(px)
        bad2 = np.where(d2 < 0)[0]
        for i in bad2:
            folds.append(f"lateral fold at y={y_level:.0f}yd: screen_x decreased from x={xs[i]:.1f}yd (px={px[i]:.1f}) "
                          f"to x={xs[i+1]:.1f}yd (px={px[i+1]:.1f})")

    return {
        "centerline_y_yd": ys.tolist(), "centerline_screen_py": py.tolist(),
        "lateral_x_yd": xs.tolist(), "lateral_screen_px_by_y": lateral_traces,
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

def run(name, corr=None, lam=TPS_LAMBDA, extra_meta=None, write_camera=False):
    corr = corr if corr is not None else CORRESPONDENCES[name]

    cam = fit_camera(corr) if lam == TPS_LAMBDA else TPSCamera(
        np.array([c["model_yd"] for c in corr]),
        np.array([c["image_px"] for c in corr])[:, 0],
        np.array([c["image_px"] for c in corr])[:, 1],
        lam=lam,
    )
    loo_all = leave_one_out_residuals(corr, lam=lam)
    loo = [r for r, c in zip(loo_all, corr) if c["source"] != "synthetic_h0"]
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
        "lambda": lam,
        "leave_one_out": loo,
        "residual_summary": {
            "max_error_px": max_err, "mean_error_px": mean_err,
            "max_error_pct_width": max_pct, "mean_error_pct_width": mean_pct,
            "n_correspondences": len(loo), "n_control_points_total": len(corr),
        },
        "monotonicity": {"folds": mono["folds"]},
        "has_front_bunker": any(c["label"] == "bunker_front" for c in corr),
    }
    if extra_meta:
        report["backbone"] = extra_meta
    (CANDIDATES_DIR / f"{name}_tps.json").write_text(json.dumps(report, indent=2))
    draw_overlay(name, cam, corr)

    print(f"--- {name} ---")
    print(json.dumps(report["residual_summary"], indent=2))
    print("folds:", mono["folds"] if mono["folds"] else "none")

    if write_camera:
        write_camera_tps_json(name, cam, corr, report, mono)

    return report, cam


def _green_polygon_center_px(cam):
    corners = [GREEN_CORNERS_YD[k] for k in ("front_left", "front_right", "back_right", "back_left")]
    pxs = [cam.project(x, y)[0] for x, y in corners]
    return sum(pxs) / len(pxs)


def write_camera_tps_json(name, cam, corr, report, mono):
    """Commits art/camera_tps.json -- the file export.py and hero.js actually
    read. mobile_crop_x0 is recomputed from THIS fit's own projection of the
    green polygon (the TPS-projected horizontal center minus half the 506px
    mobile crop width); playfield_y_max_yd is unchanged (pure model-space
    geometry, the farther back bunker's model y plus 15yd -- not something
    this pass's camera correction touches)."""
    # Unchanged from round six: the green's own back-right corner model y
    # (183.75) plus a 15yd buffer -- pure model-space geometry, untouched by
    # this pass's camera correction.
    playfield_y_max_yd = GREEN_CORNERS_YD["back_right"][1] + 15.0
    green_center_px = _green_polygon_center_px(cam)
    mobile_crop_x0 = round(green_center_px - 506 / 2.0)

    formula = (
        "TPS (thin-plate spline), fit separately per screen channel (px, py). "
        "For a query model point (x, y): "
        "f(x, y) = a0 + a1*x + a2*y + sum_i w_i * U(||(x,y) - p_i||), "
        "U(r) = r^2 * log(r) with U(0) = 0, p_i = control_points_yd[i]. "
        "wx/ax give px = f(x,y); wy/ay give py = f(x,y). "
        "Weights solved from [[K + lambda*I, P], [P^T, 0]] @ [w; a] = [v; 0], "
        "K_ij = U(|p_i - p_j|), P rows = [1, x_i, y_i]. "
        "Clip to playfield_y_max_yd before projecting; subtract mobile_crop_x0 "
        "from px when rendering the mobile crop."
    )

    out = {
        "winner": name,
        "canvas": [CANVAS_W, CANVAS_H],
        "control_points_yd": report["control_points_yd"],
        "targets_px": report["targets_px"],
        "labels": report["labels"],
        "sources": report["sources"],
        "weights": report["weights"],
        "affine": report["affine"],
        "lambda": report["lambda"],
        "formula": formula,
        "mobile_crop_x0": mobile_crop_x0,
        "playfield_y_max_yd": playfield_y_max_yd,
        "leave_one_out": report["leave_one_out"],
        "monotonicity_folds": mono["folds"],
        "backbone": report.get("backbone"),
    }
    (HERE / "camera_tps.json").write_text(json.dumps(out, indent=2))
    print(f"wrote {HERE / 'camera_tps.json'} (mobile_crop_x0={mobile_crop_x0}, "
          f"playfield_y_max_yd={playfield_y_max_yd})")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args == ["--all"]:
        run("r6_3")
        corr_v2, meta = build_r6_4_correspondences_v2()
        run("r6_4", corr=corr_v2, lam=R6_4_LAMBDA, extra_meta=meta, write_camera=True)
    else:
        for n in args:
            if n == "r6_4":
                corr_v2, meta = build_r6_4_correspondences_v2()
                run("r6_4", corr=corr_v2, lam=R6_4_LAMBDA, extra_meta=meta, write_camera=True)
            else:
                run(n)
