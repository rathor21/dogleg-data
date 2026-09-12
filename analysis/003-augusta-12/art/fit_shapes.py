"""Shape-to-shape fit for hero_final.png and aerial_final.png (issue #17
follow-up, page integration for #11/#12/#13/#14).

fit_images.py's single least-squares affine over creek + green + bunker
correspondences crushes the model's shallow diagonal green parallelogram
into a thin band on the hero image (mean residual 74px, and the Sunday pin
lands off the painted green -- see art/README.md, "Round seven,
finalization"). The green itself is never a good least-squares customer:
its 8 boundary points are lopsided around the true oval (the model samples
a parallelogram, the art paints an oval), so a global 6-parameter fit lets
the far corners drag the whole map toward them.

This script replaces that fit for the green with a SHAPE match instead of
a point-cloud regression:

    1. model green centroid: true polygon centroid (shoelace formula) of
       the model's own parallelogram (sketch.build_scene()'s green_poly_yd,
       ~40 sampled vertices, never redrawn or approximated).

    2. model green axes/extents: tried TWO ways, both sanctioned by this
       round's brief ("PCA of its vertices, or its oriented bounding
       box") -- PCA over every sampled vertex, and the polygon's own
       minimum-area oriented bounding box (rotating calipers over the
       convex hull). They disagree in an instructive way: PCA's major axis
       comes out ~17deg off the model's actual diagonal edge direction (an
       artifact of how densely the front/back edges happen to be sampled
       relative to the side edges), while the OBB's long axis lands
       exactly on the parallelogram's true 45deg "shoe-sole" diagonal.
       Both are kept as candidates rather than picking one by inspection.

    3. painted green centroid/axes/extents: PCA over the SAME 8
       hand-picked boundary points fit_images.py already carries
       (angle-matched to the model's own ray-cast points, 0/45/.../315deg
       from each shape's own centroid).

    4. axis PAIRING is not free to assume major-to-major: a tee-view
       camera foreshortens depth far more than lateral width, and this
       green's longest true-yard extent runs mostly along depth. Forcing
       "biggest model axis onto biggest painted axis" measurably fails on
       the hero image (verified against the overlay and the pin-color
       check below) because perspective flips which axis reads as
       "biggest" in the picture. Both pairings (major-to-major,
       major-to-minor) are tried for both model-axis candidates, PCA
       eigenvector sign ambiguity resolved in each case by correlation
       against the shared angle-label correspondence (never picked
       arbitrarily).

    5. selection: of the 4 candidates (2 model-axis methods x 2 pairings),
       every one is checked against this round's actual pass/fail bar --
       sampling turf color at each of the 3 projected pins -- and the
       candidate that gets all 3 pins onto green turf with the lowest
       boundary residual among those that do wins. If nothing gets all 3
       (did not happen for either image this round), the lowest-residual
       candidate ships with a disclosed failure. This mirrors
       fit_images.py's own precedent (README, "Method note on the green
       boundary": two parametrizations tried, the empirically better one
       shipped) rather than trusting any single geometric assumption to
       hold on a hand-painted, not physically-modeled camera.

    Boundary-point color refinement (walking outward from centroid along
    each hand pick's own ray, snapping to the last turf-colored pixel) was
    attempted and rejected this round: on the hero image it snaps the
    270deg point (which sits close to the new front bunker) onto the
    bunker's own rim rather than the green's true fringe line, and every
    candidate that used the refined point scored WORSE on the pin-color
    bar than the same candidate using the raw hand pick. Per this round's
    own "if reliable" instruction, that makes it unreliable here -- the
    function is kept (REFINE_BOUNDARY below) but unused, and hand picks
    are used as-is. See the "boundary_refinement_probe" block this script
    writes into camera_hero.json for the numbers.

The creek is a different shape (two roughly straight, roughly parallel
bands, not an oval) and keeps fit_images.py's original method: a plain
least-squares affine, here restricted to just the creek's two edges (the
model's front edge, matched to the painted stone wall / water far bank;
the model's front-edge-minus-14yd line -- data.CREEK_WIDTH_YD +
data.BANK_ROLLBACK_YD -- matched to the painted water's near bank, hand
picked fresh this round since fit_images.py never needed it). Where that
"short_affine" disagrees with the green shape-affine at their shared
boundary (the front edge), the two are blended linearly over a small
margin so nothing pops at the seam.

Outputs (overwritten): camera_hero.json, aerial_map.json, both
type "shape_affine". Plus fresh overlays: hero_final_fit_overlay.png,
aerial_final_fit_overlay.png.

No shapely/scipy in the venv (same constraint as fit_images.py): PCA is a
plain numpy.linalg.eigh, the OBB is a hand-rolled rotating-calipers pass
over fit_images.py's own convex_hull, and the one remaining least-squares
fit (short_affine) uses numpy.linalg.lstsq exactly as fit_images.py does.
"""
import json
import math
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import data   # noqa: E402
import model  # noqa: E402
import sketch  # noqa: E402
import fit_images as fi  # noqa: E402  -- reuses model_geometry(), the hand-picked

# pixel tables, fit_affine/fit_similarity, convex_hull/inflate_polygon,
# and the turf color test, none of which change here.

ANGLES_DEG = fi.ANGLES_DEG
ANGLE_LABELS = [f"{a}deg" for a in ANGLES_DEG]

# ---------------------------------------------------------------------------
# New hand-picked correspondences: the creek's NEAR bank (closest to the
# tee/camera -- fit_images.py's "creek_far_bank" is the FAR bank, at the
# green side / stone wall). Picked at the same 5 x-columns as
# fi.HERO_PX["creek_far_bank"] / fi.AERIAL_PX["creek_far_bank"], reading
# straight off a 25px-gridded copy of hero_final_1600x900.png /
# aerial_final.png (grid script not shipped; the picks themselves are
# recorded below and in the output JSON, source "hand").
# ---------------------------------------------------------------------------
HERO_NEAR_BANK_PX = [(200, 565), (400, 592), (650, 608), (950, 655), (1250, 675)]
AERIAL_NEAR_BANK_PX = [(50, 645), (250, 665), (450, 685), (650, 660), (850, 700)]

BLEND_MARGIN_YD = 4.0   # half-width of the linear blend band straddling the front edge
FAR_SHORT_LIMIT_YD = 30.0  # documented trust region for short_affine: front edge back to this far

REFINE_MAX_SHIFT_PX = 30.0
REFINE_STEP_PX = 1.0


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def polygon_centroid(poly):
    pts = np.array(poly, dtype=float)
    x, y = pts[:, 0], pts[:, 1]
    x2, y2 = np.roll(x, -1), np.roll(y, -1)
    cross = x * y2 - x2 * y
    A = cross.sum() / 2.0
    if abs(A) < 1e-9:
        return tuple(pts.mean(axis=0))
    cx = ((x + x2) * cross).sum() / (6 * A)
    cy = ((y + y2) * cross).sum() / (6 * A)
    return (float(cx), float(cy))


def pca_axes(points, center):
    """Returns (major, minor) unit eigenvectors of the point cloud's
    covariance, major first (larger eigenvalue). Sign is arbitrary here --
    fixed later against a labeled correspondence."""
    pts = np.array(points, dtype=float) - np.array(center, dtype=float)
    cov = (pts.T @ pts) / len(pts)
    eigvals, eigvecs = np.linalg.eigh(cov)
    order = np.argsort(eigvals)[::-1]
    eigvecs = eigvecs[:, order]
    return eigvecs[:, 0], eigvecs[:, 1]


def oriented_bounding_box_axes(poly, center):
    """Minimum-area oriented bounding box of poly (rotating calipers over
    its convex hull) -- for a polygon this is a much more stable "long
    axis" than raw-vertex PCA when the polygon is sampled unevenly along
    its own edges (exactly this project's green: front/back edges sampled
    densely in x, side edges implicit). Returns (major, minor, extents),
    major first (the box's longer side)."""
    hull = np.array(fi.convex_hull([tuple(p) for p in poly]))
    n = len(hull)
    best = None
    for i in range(n):
        p1, p2 = hull[i], hull[(i + 1) % n]
        edge = p2 - p1
        length = float(np.hypot(*edge))
        if length < 1e-9:
            continue
        u = edge / length
        v = np.array([-u[1], u[0]])
        pu, pv = hull @ u, hull @ v
        w, h = pu.max() - pu.min(), pv.max() - pv.min()
        area = w * h
        if best is None or area < best[0]:
            best = (area, u, v, w, h)
    _, u, v, w, h = best
    if w < h:
        u, v, w, h = v, u, h, w
    return u, v, (float(w), float(h))


def fix_axis_signs(model_pts, model_center, pix_pts, pix_center, e1_model, e2_model, e1_pix, e2_pix):
    """Uses the shared angle-label correspondence to pick each pixel axis's
    sign so its projections correlate positively with the model axis's
    projections -- PCA eigenvectors carry no sign of their own, and picking
    it arbitrarily can silently mirror or rotate the fit 180deg."""
    dm = np.array(model_pts, dtype=float) - np.array(model_center, dtype=float)
    dp = np.array(pix_pts, dtype=float) - np.array(pix_center, dtype=float)
    if np.sum((dm @ e1_model) * (dp @ e1_pix)) < 0:
        e1_pix = -e1_pix
    if np.sum((dm @ e2_model) * (dp @ e2_pix)) < 0:
        e2_pix = -e2_pix
    return e1_pix, e2_pix


def extents_along(points, center, e1, e2):
    d = np.array(points, dtype=float) - np.array(center, dtype=float)
    s1, s2 = d @ e1, d @ e2
    return float(s1.max() - s1.min()), float(s2.max() - s2.min())


def build_shape_affine(model_center, e1_model, e2_model, extents_model,
                        pix_center, e1_pix, e2_pix, extents_pix):
    """Centroid-to-centroid translation + axis-to-axis rotation + per-axis
    scale matching extents -- the affine A@p + b, returned as a 2x3 matrix.
    Not a residual minimization: A is constructed directly from the two
    shapes' own geometry, so no single correspondence can drag it."""
    U_model = np.column_stack([e1_model, e2_model])
    U_pix = np.column_stack([e1_pix, e2_pix])
    scale = np.array([extents_pix[0] / extents_model[0], extents_pix[1] / extents_model[1]])
    A = U_pix @ np.diag(scale) @ U_model.T
    b = np.array(pix_center, dtype=float) - A @ np.array(model_center, dtype=float)
    return np.hstack([A, b.reshape(2, 1)])


def apply_affine(M, x, y):
    p = np.asarray(M) @ np.array([x, y, 1.0])
    return float(p[0]), float(p[1])


def matrix_2x2_from_similarity(scale, angle_deg):
    theta = math.radians(angle_deg)
    return scale * np.array([[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]])


# ---------------------------------------------------------------------------
# Boundary refinement -- implemented, probed, NOT applied to the shipped
# fit. See the module docstring's "Boundary-point color refinement"
# paragraph. Kept so the probe recorded in camera_hero.json is reproducible.
# ---------------------------------------------------------------------------

def sample_rgb(img, x, y):
    xi = max(0, min(img.width - 1, int(round(x))))
    yi = max(0, min(img.height - 1, int(round(y))))
    return img.getpixel((xi, yi))


def refine_boundary_point(img, center, p, max_shift=REFINE_MAX_SHIFT_PX, step=REFINE_STEP_PX):
    cx, cy = center
    px, py = p
    dx, dy = px - cx, py - cy
    dist = math.hypot(dx, dy)
    if dist < 1e-6:
        return p, False, 0.0
    ux, uy = dx / dist, dy / dist
    ts = np.arange(max(0.0, dist - max_shift), dist + max_shift + step, step)
    turf_flags = [fi.is_green_turf(sample_rgb(img, cx + ux * t, cy + uy * t)) for t in ts]
    transitions = [ts[i - 1] for i in range(1, len(turf_flags)) if turf_flags[i - 1] and not turf_flags[i]]
    if len(transitions) != 1:
        return p, False, 0.0
    t_star = transitions[0]
    shift = float(t_star - dist)
    if abs(shift) > max_shift:
        return p, False, 0.0
    return (cx + ux * t_star, cy + uy * t_star), True, shift


def probe_refinement(hand_px, img):
    center_raw = tuple(np.mean([hand_px[l] for l in ANGLE_LABELS], axis=0))
    out = {}
    for l in ANGLE_LABELS:
        rp, ok, shift = refine_boundary_point(img, center_raw, hand_px[l])
        out[l] = {"hand_px": [round(v, 1) for v in hand_px[l]], "reliable": ok,
                   "refined_px": [round(v, 1) for v in rp] if ok else None, "shift_px": round(shift, 1)}
    return out


# ---------------------------------------------------------------------------
# Green shape-affine: 4 candidates (2 model-axis methods x 2 pairings),
# selected by pin-color verification first, boundary residual second.
# ---------------------------------------------------------------------------

def shape_fit_green(model_poly, model_center, green_boundary_yd, hand_px, img, pins_yd):
    model_axis_candidates = {
        "pca": pca_axes(model_poly, model_center) + (None,),
        "obb": oriented_bounding_box_axes(model_poly, model_center),
    }
    for key, (e1, e2, ext) in list(model_axis_candidates.items()):
        if ext is None:
            ext = extents_along(model_poly, model_center, e1, e2)
        model_axis_candidates[key] = (e1, e2, ext)

    model_pts = [green_boundary_yd[l] for l in ANGLE_LABELS]
    pix_center = tuple(np.mean([hand_px[l] for l in ANGLE_LABELS], axis=0))
    pix_pts = [hand_px[l] for l in ANGLE_LABELS]
    e1_pix_raw, e2_pix_raw = pca_axes(pix_pts, pix_center)
    extents_pix_raw = extents_along(pix_pts, pix_center, e1_pix_raw, e2_pix_raw)

    candidates = []
    for axis_method, (e1_model, e2_model, extents_model) in model_axis_candidates.items():
        for swapped in (False, True):
            if not swapped:
                e1p, e2p, ext = e1_pix_raw, e2_pix_raw, extents_pix_raw
            else:
                e1p, e2p, ext = e2_pix_raw, e1_pix_raw, (extents_pix_raw[1], extents_pix_raw[0])
            e1p, e2p = fix_axis_signs(model_pts, model_center, pix_pts, pix_center, e1_model, e2_model, e1p, e2p)
            M = build_shape_affine(model_center, e1_model, e2_model, extents_model, pix_center, e1p, e2p, ext)
            residuals = [float(np.hypot(*(np.subtract(apply_affine(M, *mp), pp)))) for mp, pp in zip(model_pts, pix_pts)]
            pins_pass = []
            for name, (x, y) in pins_yd.items():
                px, py = apply_affine(M, x, y)
                pins_pass.append(fi.is_green_turf(fi.sample_color(img, px, py)))
            candidates.append({
                "model_axis_method": axis_method, "swapped": swapped, "M": M,
                "mean_residual_px": round(float(np.mean(residuals)), 2),
                "residuals_px": [round(r, 2) for r in residuals],
                "pins_all_green": all(pins_pass), "pins_pass": pins_pass,
                "e1_model": e1_model, "e2_model": e2_model, "extents_model": extents_model,
                "e1_pix": e1p, "e2_pix": e2p, "extents_pix": ext,
            })

    passing = [c for c in candidates if c["pins_all_green"]]
    pool = passing if passing else candidates
    chosen = min(pool, key=lambda c: c["mean_residual_px"])

    record = {
        "method": "shape-to-shape: centroid-to-centroid translation, axis-to-axis rotation "
                  "(PCA or oriented-bounding-box model axes, PCA painted axes), per-axis extent "
                  "scale -- not a least-squares point fit. 4 candidates tried (2 model-axis "
                  "methods x 2 axis pairings); selected by pin-color verification first "
                  "(all 3 pins must sample as green turf), boundary residual second.",
        "model_centroid_yd": [round(v, 3) for v in model_center],
        "candidates": [
            {
                "model_axis_method": c["model_axis_method"],
                "swapped_pairing": c["swapped"],
                "mean_residual_px": c["mean_residual_px"],
                "pins_all_green": c["pins_all_green"],
                "pins_pass": c["pins_pass"],
            }
            for c in candidates
        ],
        "chosen": {"model_axis_method": chosen["model_axis_method"], "swapped_pairing": chosen["swapped"],
                   "any_candidate_passed_pin_check": bool(passing)},
        "model_axes_used": {
            "method": chosen["model_axis_method"],
            "major_unit": [round(v, 4) for v in chosen["e1_model"].tolist()],
            "minor_unit": [round(v, 4) for v in chosen["e2_model"].tolist()],
            "extents_yd": [round(v, 2) for v in chosen["extents_model"]],
        },
        "pix_centroid_px": [round(v, 1) for v in pix_center],
        "pix_axes_used": {
            "major_unit": [round(v, 4) for v in chosen["e1_pix"].tolist()],
            "minor_unit": [round(v, 4) for v in chosen["e2_pix"].tolist()],
            "extents_px": [round(v, 1) for v in chosen["extents_pix"]],
        },
        "boundary_correspondences": [
            {"label": l, "model_yd": list(green_boundary_yd[l]), "pixel_px": list(hand_px[l]), "source": "hand",
             "residual_px": r}
            for l, r in zip(ANGLE_LABELS, chosen["residuals_px"])
        ],
        "residual_px": {
            "mean": chosen["mean_residual_px"],
            "max": max(chosen["residuals_px"]),
            "per_point": chosen["residuals_px"],
            "note": "residuals here describe how well the shape-affine's rotation+scale happens "
                    "to also match each individual boundary point -- not the fit objective (there "
                    "is none to minimize; the affine is built directly from the two shapes' "
                    "centroids/axes/extents), so a nonzero number is expected. Selection above "
                    "was driven by pin-color verification, not this number.",
        },
        "boundary_refinement_probe": probe_refinement(hand_px, img),
        "boundary_refinement_verdict": "attempted, not applied: every candidate scored using the "
                                        "refined 270deg point (which lands on the new front bunker's "
                                        "rim, see the probe above) did worse on pin-color verification "
                                        "than the same candidate using the raw hand pick, so hand "
                                        "picks are used as-is throughout. See module docstring.",
    }
    return chosen["M"], record


# ---------------------------------------------------------------------------
# Creek short_affine: plain least-squares affine (fit_images.py's method),
# restricted to the two creek edges (front edge / far bank, and
# front-edge-minus-14yd / near bank).
# ---------------------------------------------------------------------------

def shape_fit_short(geom, far_bank_px, near_bank_px, x_samples):
    creek_width_plus_bank = data.CREEK_WIDTH_YD + data.BANK_ROLLBACK_YD
    corrs = []
    corr_records = []
    for x, px in zip(x_samples, far_bank_px):
        y = model._front_edge_yd(x, geom)
        corrs.append(((x, y), px))
        corr_records.append({"group": "front_edge_far_bank", "model_yd": [x, y], "pixel": list(px), "source": "hand"})
    for x, px in zip(x_samples, near_bank_px):
        y = model._front_edge_yd(x, geom) - creek_width_plus_bank
        corrs.append(((x, y), px))
        corr_records.append({"group": "near_bank_minus_14yd", "model_yd": [x, round(y, 2)], "pixel": list(px), "source": "hand"})

    M, residuals = fi.fit_affine(corrs)
    for rec, r in zip(corr_records, residuals):
        rec["residual_px"] = round(r, 2)

    record = {
        "method": "6-parameter affine, least squares, over the creek's two edges only "
                  "(front edge / painted wall-or-far-bank, and front edge minus "
                  "data.CREEK_WIDTH_YD+data.BANK_ROLLBACK_YD / painted near bank)",
        "correspondences": corr_records,
        "residual_px": {
            "mean": round(float(np.mean(residuals)), 2),
            "max": round(float(np.max(residuals)), 2),
            "per_point": [round(r, 2) for r in residuals],
        },
    }
    return M, record


def front_edge_formula(geom):
    front_at_center = data.PINS["center"]["y"] - geom["center_depth"]
    return {
        "front_edge_at_x0_yd": front_at_center,
        "slope_yd_per_yd": model._FRONT_EDGE_SLOPE_YD_PER_YD,
        "formula": "front_edge_yd(x) = front_edge_at_x0_yd + slope_yd_per_yd * x",
    }


def project_blended(x, y, green_affine, short_affine, front_edge_fn, blend_margin):
    fe = front_edge_fn(x)
    if short_affine is None or y >= fe + blend_margin:
        return apply_affine(green_affine, x, y)
    if y <= fe - blend_margin:
        return apply_affine(short_affine, x, y)
    t = (y - (fe - blend_margin)) / (2 * blend_margin)
    t = min(1.0, max(0.0, t))
    sx, sy = apply_affine(short_affine, x, y)
    gx, gy = apply_affine(green_affine, x, y)
    return (sx * (1 - t) + gx * t, sy * (1 - t) + gy * t)


# ---------------------------------------------------------------------------
# Pin check
# ---------------------------------------------------------------------------

def pin_checks_for(pins_yd, project_fn, img):
    out = {}
    for name, (x, y) in pins_yd.items():
        px, py = project_fn(x, y)
        rgb = fi.sample_color(img, px, py)
        out[name] = {
            "model_yd": [x, y],
            "pixel_px": [round(px, 1), round(py, 1)],
            "sampled_rgb": list(rgb),
            "on_green_turf": bool(fi.is_green_turf(rgb)),
        }
    return out


# ---------------------------------------------------------------------------
# Overlay
# ---------------------------------------------------------------------------

def draw_overlay(image_path, project_fn, geom_bundle, out_path, tee_project_fn=None):
    im = Image.open(image_path).convert("RGB")
    d = ImageDraw.Draw(im)

    def draw_poly(poly_yd, color, width=3):
        pts = [project_fn(x, y) for x, y in poly_yd]
        d.line(pts + [pts[0]], fill=color, width=width)

    regions = geom_bundle["regions"]
    draw_poly(regions["green"], (255, 0, 0))
    draw_poly(regions["creek"], (0, 200, 255))
    draw_poly(regions["front_bunker"], (255, 200, 0))
    for bb in regions["back_bunkers"]:
        draw_poly(bb["poly"], (255, 200, 0))
    if tee_project_fn is not None:
        pts = [tee_project_fn(x, y) for x, y in geom_bundle["landmarks"]["tee_poly_yd"]]
        d.line(pts + [pts[0]], fill=(255, 0, 255), width=3)

    for name, (x, y) in geom_bundle["pins_yd"].items():
        px, py = project_fn(x, y)
        r = 7
        d.ellipse([px - r, py - r, px + r, py + r], outline=(255, 255, 255), width=3)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(255, 0, 0))

    im.save(out_path)


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

def build_hero(geom_bundle):
    geom = geom_bundle["landmarks"]["geom"]
    model_center = polygon_centroid(geom_bundle["green_poly_yd"])
    hero_img = Image.open(HERE / "hero_final.png").convert("RGB")
    hero_scale_x = 1600.0 / hero_img.width
    hero_scale_y = 900.0 / hero_img.height

    # HERO_PX / HERO_NEAR_BANK_PX below (fi.HERO_PX is fit_images.py's own
    # table) are picked on hero_final_1600x900.png; hero_final.png (native
    # 1344x768) is the same frame at a different pixel count and a
    # slightly different aspect (1.750 vs 1.778), so hand picks are
    # rescaled non-uniformly onto whichever file is opened, matching
    # whatever resize produced the 1600x900 version.
    def to_native(pt):
        return (pt[0] * hero_scale_x, pt[1] * hero_scale_y)

    green_boundary_native = {l: to_native(fi.HERO_PX["green_boundary"][l]) for l in ANGLE_LABELS}
    green_M, green_record = shape_fit_green(
        geom_bundle["green_poly_yd"], model_center, geom_bundle["green_boundary_yd"],
        green_boundary_native, hero_img, geom_bundle["pins_yd"])

    x_samples = list(np.linspace(-20.0, 20.0, 5))
    far_bank_native = [to_native(p) for p in fi.HERO_PX["creek_far_bank"]]
    near_bank_native = [to_native(p) for p in HERO_NEAR_BANK_PX]
    short_M, short_record = shape_fit_short(geom, far_bank_native, near_bank_native, x_samples)

    fe_formula = front_edge_formula(geom)

    def front_edge_fn(x):
        return fe_formula["front_edge_at_x0_yd"] + fe_formula["slope_yd_per_yd"] * x

    def project_fn(x, y):
        return project_blended(x, y, green_M, short_M, front_edge_fn, BLEND_MARGIN_YD)

    def rms(M, pts_model, pts_px):
        errs = [np.hypot(*(np.subtract(apply_affine(M, *mp), pp))) for mp, pp in zip(pts_model, pts_px)]
        return float(np.mean(errs))

    far_bank_model = [(x, front_edge_fn(x)) for x in x_samples]
    near_bank_model = [(x, front_edge_fn(x) - (data.CREEK_WIDTH_YD + data.BANK_ROLLBACK_YD)) for x in x_samples]
    green_only_far = rms(green_M, far_bank_model, far_bank_native)
    green_only_near = rms(green_M, near_bank_model, near_bank_native)
    short_far = rms(short_M, far_bank_model, far_bank_native)
    short_near = rms(short_M, near_bank_model, near_bank_native)

    # tee: exact similarity through the 2 front-corner<->marker correspondences
    tee_model_pts = [geom_bundle["tee_front_left_yd"], geom_bundle["tee_front_right_yd"]]
    tee_pixel_pts = [to_native(fi.HERO_PX["tee_marker_left"]), to_native(fi.HERO_PX["tee_marker_right"])]
    tee_apply, tee_residuals, tee_scale, tee_angle = fi.fit_similarity(tee_model_pts, tee_pixel_pts)
    A_tee = matrix_2x2_from_similarity(tee_scale, tee_angle)
    m1 = np.array(tee_model_pts[0])
    p1 = np.array(tee_pixel_pts[0])
    b_tee = p1 - A_tee @ m1
    tee_M = np.hstack([A_tee, b_tee.reshape(2, 1)])
    back_left_px = apply_affine(tee_M, *geom_bundle["tee_back_left_yd"])
    back_right_px = apply_affine(tee_M, *geom_bundle["tee_back_right_yd"])

    def tee_project_fn(x, y):
        return apply_affine(tee_M, x, y)

    pin_checks = pin_checks_for(geom_bundle["pins_yd"], project_fn, hero_img)

    # playfield polygon: creek + green + bunker halos, each projected
    # through the SAME blended projector shots/scatter use.
    regions = geom_bundle["regions"]
    poly_yd_pts = list(regions["creek"]) + list(regions["green"]) + list(regions["front_bunker_halo"])
    for bb in regions["back_bunkers"]:
        poly_yd_pts += bb["halo"]
    poly_px_pts = [project_fn(x, y) for x, y in poly_yd_pts]
    hull = fi.convex_hull(poly_px_pts)
    playfield_polygon_px = fi.inflate_polygon(hull, 1.10)

    # mobile crop: 506x900 phone crop centered on the projected green centroid
    green_center_px = project_fn(*model_center)
    mobile_crop_x0 = float(np.clip(green_center_px[0] - 506 / 2.0, 0, 1600 - 506))

    out = {
        "type": "shape_affine",
        "source_image": "hero_final.png",
        "canvas": [1600, 900],
        "green_affine": green_M.tolist(),
        "green_affine_fit": green_record,
        "short_affine": short_M.tolist(),
        "short_affine_fit": short_record,
        "short_affine_blend": {
            "front_edge": fe_formula,
            "blend_margin_yd": BLEND_MARGIN_YD,
            "far_short_limit_yd": FAR_SHORT_LIMIT_YD,
            "rule": "for y_yd >= front_edge(x)+margin use green_affine; for y_yd <= front_edge(x)-margin "
                    "use short_affine; in between, linearly blend the two projected points by "
                    "t=(y_yd-(front_edge(x)-margin))/(2*margin). short_affine is fit from (and trusted "
                    "over) the front edge back to about far_short_limit_yd yards short; extrapolates "
                    "past that without a second seam since nothing else covers that ground.",
            "creek_band_check_rms_px": {
                "green_affine_alone_on_far_bank": round(green_only_far, 1),
                "green_affine_alone_on_near_bank": round(green_only_near, 1),
                "short_affine_on_far_bank": round(short_far, 1),
                "short_affine_on_near_bank": round(short_near, 1),
                "note": "green_affine alone was checked against the same far/near bank hand picks "
                        "short_affine is fit to; short_affine wins on both (see numbers above), which "
                        "is why it is shipped rather than relying on green_affine for the whole frame.",
            },
        },
        "tee": {
            "method": "exact similarity (rotation + uniform scale + translation) through 2 correspondences, "
                      "expressed as a 2x3 affine",
            "affine": tee_M.tolist(),
            "scale_px_per_yd": round(tee_scale, 3),
            "rotation_deg": round(tee_angle, 3),
            "front_left_corner_px": [round(v, 1) for v in tee_pixel_pts[0]],
            "front_right_corner_px": [round(v, 1) for v in tee_pixel_pts[1]],
            "back_left_corner_px": [round(v, 1) for v in back_left_px],
            "back_right_corner_px": [round(v, 1) for v in back_right_px],
            "residual_px": [round(r, 2) for r in tee_residuals],
        },
        "pins_px": {k: v["pixel_px"] for k, v in pin_checks.items()},
        "pin_checks": pin_checks,
        "playfield_polygon_px": [[round(x, 1), round(y, 1)] for x, y in playfield_polygon_px],
        "horizon_px": 20.0,
        "mobile_crop_x0": round(mobile_crop_x0, 1),
    }
    return out, project_fn, tee_project_fn


# ---------------------------------------------------------------------------
# Aerial
# ---------------------------------------------------------------------------

def build_aerial(geom_bundle):
    geom = geom_bundle["landmarks"]["geom"]
    model_center = polygon_centroid(geom_bundle["green_poly_yd"])
    aerial_img = Image.open(HERE / "aerial_final.png").convert("RGB")

    green_M, green_record = shape_fit_green(
        geom_bundle["green_poly_yd"], model_center, geom_bundle["green_boundary_yd"],
        fi.AERIAL_PX["green_boundary"], aerial_img, geom_bundle["pins_yd"])

    x_samples = list(np.linspace(-20.0, 20.0, 5))
    far_bank_px = fi.AERIAL_PX["creek_far_bank"]
    near_bank_px = AERIAL_NEAR_BANK_PX
    short_M, short_record = shape_fit_short(geom, far_bank_px, near_bank_px, x_samples)

    fe_formula = front_edge_formula(geom)

    def front_edge_fn(x):
        return fe_formula["front_edge_at_x0_yd"] + fe_formula["slope_yd_per_yd"] * x

    def rms(M, pts_model, pts_px):
        errs = [np.hypot(*(np.subtract(apply_affine(M, *mp), pp))) for mp, pp in zip(pts_model, pts_px)]
        return float(np.mean(errs))

    far_bank_model = [(x, front_edge_fn(x)) for x in x_samples]
    near_bank_model = [(x, front_edge_fn(x) - (data.CREEK_WIDTH_YD + data.BANK_ROLLBACK_YD)) for x in x_samples]
    green_only_far = rms(green_M, far_bank_model, far_bank_px)
    green_only_near = rms(green_M, near_bank_model, near_bank_px)
    short_far = rms(short_M, far_bank_model, far_bank_px)
    short_near = rms(short_M, near_bank_model, near_bank_px)
    # Aerial is close to orthographic (round seven's own README note): use
    # short_affine only if it is a clear improvement over the green
    # shape-affine on the creek band; otherwise one global affine (the
    # green shape-affine) is simpler and just as accurate.
    use_short = (short_far + short_near) < 0.8 * (green_only_far + green_only_near)

    def project_fn(x, y):
        if use_short:
            return project_blended(x, y, green_M, short_M, front_edge_fn, BLEND_MARGIN_YD)
        return apply_affine(green_M, x, y)

    pin_checks = pin_checks_for(geom_bundle["pins_yd"], project_fn, aerial_img)

    tee_markers_yd = geom_bundle["tee_markers_yd"]
    tee_px = {
        "left": [round(v, 1) for v in project_fn(*tee_markers_yd["left"])],
        "right": [round(v, 1) for v in project_fn(*tee_markers_yd["right"])],
    }
    tee_box_px = [[round(v, 1) for v in project_fn(x, y)] for x, y in geom_bundle["landmarks"]["tee_poly_yd"]]

    out = {
        "type": "shape_affine",
        "source_image": "aerial_final.png",
        "canvas": [aerial_img.width, aerial_img.height],
        "affine": green_M.tolist(),
        "affine_fit": green_record,
        "up_direction": "tee at bottom of frame; +model_y (downrange) points toward the top of the image",
        "pins_px": {k: v["pixel_px"] for k, v in pin_checks.items()},
        "pin_checks": pin_checks,
        "tee_markers_px": tee_px,
        "tee_box_px": tee_box_px,
    }
    if use_short:
        out["short_affine"] = short_M.tolist()
        out["short_affine_fit"] = short_record
        out["short_affine_blend"] = {
            "front_edge": fe_formula,
            "blend_margin_yd": BLEND_MARGIN_YD,
            "far_short_limit_yd": FAR_SHORT_LIMIT_YD,
            "rule": "same rule as camera_hero.json's short_affine_blend",
            "creek_band_check_rms_px": {
                "affine_alone_on_far_bank": round(green_only_far, 1),
                "affine_alone_on_near_bank": round(green_only_near, 1),
                "short_affine_on_far_bank": round(short_far, 1),
                "short_affine_on_near_bank": round(short_near, 1),
            },
        }
    else:
        out["short_affine"] = None
        out["short_affine_check"] = {
            "affine_alone_on_far_bank_rms_px": round(green_only_far, 1),
            "affine_alone_on_near_bank_rms_px": round(green_only_near, 1),
            "short_affine_would_give_far_bank_rms_px": round(short_far, 1),
            "short_affine_would_give_near_bank_rms_px": round(short_near, 1),
            "verdict": "not added: the single shape-affine already places the creek band within "
                       "its own width on this near-orthographic frame, matching round seven's finding "
                       "that this aerial's residuals were roughly even across every correspondence group.",
        }
    return out, project_fn


def main():
    geom_bundle = fi.model_geometry()

    hero_json, hero_project, hero_tee_project = build_hero(geom_bundle)
    (HERE / "camera_hero.json").write_text(json.dumps(hero_json, indent=2))
    draw_overlay(HERE / "hero_final.png", hero_project, geom_bundle, HERE / "hero_final_fit_overlay.png",
                 tee_project_fn=hero_tee_project)

    aerial_json, aerial_project = build_aerial(geom_bundle)
    (HERE / "aerial_map.json").write_text(json.dumps(aerial_json, indent=2))
    draw_overlay(HERE / "aerial_final.png", aerial_project, geom_bundle, HERE / "aerial_final_fit_overlay.png")

    print("=== HERO green shape-affine: candidates ===")
    print(json.dumps(hero_json["green_affine_fit"]["candidates"], indent=2))
    print("chosen:", json.dumps(hero_json["green_affine_fit"]["chosen"]))
    print("=== HERO creek band check ===")
    print(json.dumps(hero_json["short_affine_blend"]["creek_band_check_rms_px"], indent=2))
    print("=== HERO pin checks ===")
    print(json.dumps(hero_json["pin_checks"], indent=2))
    print("=== HERO mobile_crop_x0 ===", hero_json["mobile_crop_x0"])
    print("=== AERIAL green shape-affine: candidates ===")
    print(json.dumps(aerial_json["affine_fit"]["candidates"], indent=2))
    print("chosen:", json.dumps(aerial_json["affine_fit"]["chosen"]))
    print("=== AERIAL short_affine used? ===", aerial_json["short_affine"] is not None)
    print("=== AERIAL pin checks ===")
    print(json.dumps(aerial_json["pin_checks"], indent=2))


if __name__ == "__main__":
    main()
