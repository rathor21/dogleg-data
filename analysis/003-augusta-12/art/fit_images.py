"""Round seven, finalization: fit the model's own geometry to hero_final.png
and aerial_final.png (issue #17).

Two independent fits, both built entirely from hand-picked pixel
correspondences (source: "hand" throughout) paired against model.py's own
yard-space geometry, read through sketch.build_scene() -- nothing here
invents a new hazard boundary or bunker location.

camera_hero.json (hero, tee-view):
    (a) green_local: a 6-parameter affine (least squares) from model yards to
        hero pixels, fit on the green outline's 8 points, the creek far
        bank's 5 points, and the bunker centroids (all three -- the front
        bunker edit succeeded on the hero image, see README).
    (b) tee: an exact similarity (rotation + uniform scale + translation)
        from the two front tee-box corners to the two painted tee markers,
        used to extrapolate the box's back corners with the same lateral
        scale.
    Also playfield_polygon_px (green + bunkers + creek band + 10% margin,
    projected through green_local) and horizon_px.

aerial_map.json (aerial, top-down):
    A single 6-parameter affine (least squares) from model yards to aerial
    pixels, fit on the green outline, creek far bank, the two bunkers, and
    the two tee markers (their real model coordinates, not a simplification
    -- the aerial is close to orthographic, so near-tee and far-green points
    can share one global map).

Both fits report residuals; both write an overlay PNG that redraws the
model's green, creek far bank, bunkers, tee box, and pins through the fit.
"""
import json
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import data   # noqa: E402
import model  # noqa: E402
import sketch  # noqa: E402

ANGLES_DEG = [0, 45, 90, 135, 180, 225, 270, 315]


# ---------------------------------------------------------------------------
# Model-space geometry (shared by both fits)
# ---------------------------------------------------------------------------

def convex_ray_intersect(poly, center, angle_deg):
    """Intersection of the ray from `center` at `angle_deg` (0=+x, 90=+y,
    standard math convention, counterclockwise) with the boundary of the
    convex polygon `poly` (list of (x, y)). Returns (x, y)."""
    theta = np.radians(angle_deg)
    dx, dy = np.cos(theta), np.sin(theta)
    cx, cy = center
    best_t = None
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        ex, ey = x2 - x1, y2 - y1
        # Solve center + t*(dx,dy) = (x1,y1) + s*(ex,ey), t>=0, 0<=s<=1
        denom = dx * ey - dy * ex
        if abs(denom) < 1e-9:
            continue
        s = ((x1 - cx) * dy - (y1 - cy) * dx) / denom
        if s < -1e-9 or s > 1 + 1e-9:
            continue
        # t from the x or y equation, whichever direction vector is larger
        if abs(dx) > abs(dy):
            t = (x1 + s * ex - cx) / dx
        else:
            t = (y1 + s * ey - cy) / dy
        if t < 1e-9:
            continue
        if best_t is None or t < best_t:
            best_t = t
    if best_t is None:
        raise ValueError(f"no intersection at angle {angle_deg}")
    return (cx + best_t * dx, cy + best_t * dy)


def model_geometry():
    regions, landmarks = sketch.build_scene()
    green_poly = landmarks["green_poly_yd"]
    green_centroid = tuple(np.mean(np.array(green_poly), axis=0))

    # Ray-cast from the green polygon's own centroid at each hand-labeled
    # angle (0=+x/right, 90=+y/further-from-tee, counterclockwise -- the
    # same convention used when the angle-labeled points were hand-picked
    # around the painted oval). Tried an alternative (perimeter-fraction
    # sampling around the parallelogram's 4 corners, since the model green
    # is a very elongated diagonal parallelogram and a literal angle ray
    # clusters several labels on the same edge) and it fit worse (hero mean
    # 115px vs 74px) -- kept the angle-ray version. See README: the round
    # two note that "the model's green is a diagonal parallelogram and the
    # painted green is an oval, so expect the corners to overshoot" already
    # anticipates this mismatch; the residual table below reports it plainly
    # rather than picking whichever parametrization scores lower.
    green_boundary_yd = {
        f"{a}deg": convex_ray_intersect(green_poly, green_centroid, a)
        for a in ANGLES_DEG
    }

    geom = landmarks["geom"]
    fx_lo, fx_hi = -20.0, 20.0  # fairway_half_width_yd, matches sketch.py
    creek_far_bank_yd = [
        (x, model._front_edge_yd(x, geom))
        for x in np.linspace(fx_lo, fx_hi, 5)
    ]

    back_bunkers = landmarks["back_bunkers"]

    def side(bb):
        lo, hi = bb["x_range"]
        return "left" if (lo + hi) / 2 < 0 else "right"

    back_bunker_centroids_yd = {side(bb): bb["centroid_yd"] for bb in back_bunkers}
    front_bunker_centroid_yd = landmarks["front_bunker_centroid_yd"]

    tee_poly_yd = landmarks["tee_poly_yd"]  # [BL, BR, FR, FL] per sketch.py
    tee_back_left_yd, tee_back_right_yd, tee_front_right_yd, tee_front_left_yd = tee_poly_yd
    tee_markers_yd = landmarks["tee_markers_yd"]  # [left, right]

    return {
        "regions": regions,
        "landmarks": landmarks,
        "green_poly_yd": green_poly,
        "green_centroid_yd": green_centroid,
        "green_boundary_yd": green_boundary_yd,
        "creek_far_bank_yd": creek_far_bank_yd,
        "back_bunker_centroids_yd": back_bunker_centroids_yd,
        "front_bunker_centroid_yd": front_bunker_centroid_yd,
        "tee_front_left_yd": tee_front_left_yd,
        "tee_front_right_yd": tee_front_right_yd,
        "tee_back_left_yd": tee_back_left_yd,
        "tee_back_right_yd": tee_back_right_yd,
        "tee_markers_yd": {"left": tee_markers_yd[0], "right": tee_markers_yd[1]},
        "pins_yd": {k: (p["x"], p["y"]) for k, p in data.PINS.items()},
    }


# ---------------------------------------------------------------------------
# Hand-picked pixel correspondences
# ---------------------------------------------------------------------------

HERO_PX = {
    "green_boundary": {
        "0deg": (1019.0, 331.0), "45deg": (939.0, 301.3), "90deg": (746.0, 289.0),
        "135deg": (553.0, 301.3), "180deg": (473.0, 331.0), "225deg": (553.0, 360.7),
        "270deg": (746.0, 373.0), "315deg": (939.0, 360.7),
    },
    "creek_far_bank": [(200, 370), (400, 380), (650, 386), (950, 428), (1250, 460)],
    "bunker_left": (505, 285),
    "bunker_right": (1065, 280),
    "bunker_front": (892, 375),
    "tee_marker_left": (99, 669),
    "tee_marker_right": (943, 637),
}

AERIAL_PX = {
    "green_boundary": {
        "0deg": (730.0, 470.0), "45deg": (671.4, 406.4), "90deg": (530.0, 380.0),
        "135deg": (388.6, 406.4), "180deg": (330.0, 470.0), "225deg": (388.6, 533.6),
        "270deg": (530.0, 560.0), "315deg": (671.4, 533.6),
    },
    "creek_far_bank": [(50, 565), (250, 608), (450, 568), (650, 587), (850, 558)],
    "bunker_left": (355, 418),
    "bunker_right": (705, 422),
    "tee_marker_left": (421, 872),
    "tee_marker_right": (566, 870),
}


def hand(pt):
    return {"point": list(pt), "source": "hand"}


# ---------------------------------------------------------------------------
# Affine (6-param, least squares) fit
# ---------------------------------------------------------------------------

def fit_affine(corrs):
    """corrs: list of ((x_yd, y_yd), (px, py)). Returns (M, residuals) where
    M maps [x, y, 1] -> [px, py] via a 2x3 matrix, and residuals is a list of
    per-point Euclidean pixel error."""
    A = []
    bx = []
    by = []
    for (x, y), (px, py) in corrs:
        A.append([x, y, 1])
        bx.append(px)
        by.append(py)
    A = np.array(A)
    bx = np.array(bx)
    by = np.array(by)
    coeff_x, *_ = np.linalg.lstsq(A, bx, rcond=None)
    coeff_y, *_ = np.linalg.lstsq(A, by, rcond=None)
    M = np.vstack([coeff_x, coeff_y])  # 2x3

    residuals = []
    for (x, y), (px, py) in corrs:
        pred = M @ np.array([x, y, 1.0])
        err = float(np.hypot(pred[0] - px, pred[1] - py))
        residuals.append(err)
    return M, residuals


def apply_affine(M, x, y):
    pred = M @ np.array([x, y, 1.0])
    return float(pred[0]), float(pred[1])


def fit_similarity(model_pts, pixel_pts):
    """Exact similarity (rotation + uniform scale + translation) through
    exactly two point correspondences, via complex-number division."""
    (mx1, my1), (mx2, my2) = model_pts
    (px1, py1), (px2, py2) = pixel_pts
    m1, m2 = complex(mx1, my1), complex(mx2, my2)
    p1, p2 = complex(px1, py1), complex(px2, py2)
    k = (p2 - p1) / (m2 - m1)  # scale * rotation

    def apply(x, y):
        m = complex(x, y)
        p = p1 + (m - m1) * k
        return (p.real, p.imag)

    residuals = []
    for (mx, my), (px, py) in zip(model_pts, pixel_pts):
        qx, qy = apply(mx, my)
        residuals.append(float(np.hypot(qx - px, qy - py)))
    scale = abs(k)
    angle_deg = float(np.degrees(np.angle(k)))
    return apply, residuals, scale, angle_deg


# ---------------------------------------------------------------------------
# hero: camera_hero.json
# ---------------------------------------------------------------------------

def build_camera_hero(geom):
    corrs = []
    corr_records = []

    for a in ANGLES_DEG:
        key = f"{a}deg"
        m_pt = geom["green_boundary_yd"][key]
        px_pt = HERO_PX["green_boundary"][key]
        corrs.append((m_pt, px_pt))
        corr_records.append({"group": "green_boundary", "label": key,
                              "model_yd": list(m_pt), "pixel": list(px_pt), "source": "hand"})

    for i, m_pt in enumerate(geom["creek_far_bank_yd"]):
        px_pt = HERO_PX["creek_far_bank"][i]
        corrs.append((m_pt, px_pt))
        corr_records.append({"group": "creek_far_bank", "label": f"pt{i}",
                              "model_yd": list(m_pt), "pixel": list(px_pt), "source": "hand"})

    for side in ("left", "right"):
        m_pt = geom["back_bunker_centroids_yd"][side]
        px_pt = HERO_PX[f"bunker_{side}"]
        corrs.append((m_pt, px_pt))
        corr_records.append({"group": "back_bunker_centroid", "label": side,
                              "model_yd": list(m_pt), "pixel": list(px_pt), "source": "hand"})

    m_pt = geom["front_bunker_centroid_yd"]
    px_pt = HERO_PX["bunker_front"]
    corrs.append((m_pt, px_pt))
    corr_records.append({"group": "front_bunker_centroid", "label": "front",
                          "model_yd": list(m_pt), "pixel": list(px_pt), "source": "hand",
                          "note": "highest residual of any correspondence: data.HOLE's front_bunker_x_range (-10,2) is MODELED left-of-center ('per the one source with a side call', data.py), while the round seven prompt and the successful hero edit both place the painted bunker right of center -- a genuine model-vs-art disagreement on which side of the green the front bunker sits, not a hand-pick error. Left in the fit per this round's instructions; see README."})

    M, residuals = fit_affine(corrs)
    for rec, res in zip(corr_records, residuals):
        rec["residual_px"] = round(res, 2)

    # tee: exact similarity from the two front corners to the two markers
    tee_model_pts = [geom["tee_front_left_yd"], geom["tee_front_right_yd"]]
    tee_pixel_pts = [HERO_PX["tee_marker_left"], HERO_PX["tee_marker_right"]]
    tee_apply, tee_residuals, tee_scale, tee_angle = fit_similarity(tee_model_pts, tee_pixel_pts)

    back_left_px = tee_apply(*geom["tee_back_left_yd"])
    back_right_px = tee_apply(*geom["tee_back_right_yd"])

    tee_corrs = [
        {"label": "front_left_corner_to_left_marker", "model_yd": list(geom["tee_front_left_yd"]),
         "pixel": list(tee_pixel_pts[0]), "source": "hand", "residual_px": round(tee_residuals[0], 2)},
        {"label": "front_right_corner_to_right_marker", "model_yd": list(geom["tee_front_right_yd"]),
         "pixel": list(tee_pixel_pts[1]), "source": "hand", "residual_px": round(tee_residuals[1], 2)},
    ]
    tee_extrapolated = {
        "back_left_corner_px": [round(v, 1) for v in back_left_px],
        "back_right_corner_px": [round(v, 1) for v in back_right_px],
        "note": "back corners extrapolated with the same lateral scale/rotation derived from the two front-corner<->marker correspondences (an exact 2-point similarity), not independently fit.",
    }

    # pin check
    pin_checks = {}
    for name, (x, y) in geom["pins_yd"].items():
        px, py = apply_affine(M, x, y)
        pin_checks[name] = {"model_yd": [x, y], "pixel_px": [round(px, 1), round(py, 1)]}

    # playfield polygon: creek + green + bunker halos, projected, hulled, inflated 10%
    regions = geom["regions"]
    poly_yd_pts = []
    poly_yd_pts += regions["creek"]
    poly_yd_pts += regions["green"]
    poly_yd_pts += regions["front_bunker_halo"]
    for bb in regions["back_bunkers"]:
        poly_yd_pts += bb["halo"]
    poly_px_pts = [apply_affine(M, x, y) for x, y in poly_yd_pts]
    hull = convex_hull(poly_px_pts)
    playfield_polygon_px = inflate_polygon(hull, 1.10)

    horizon_px = 20.0  # visual read of hero_final.png: tree canopy fills nearly to the top of frame

    return {
        "source_image": "hero_final.png",
        "green_local": {
            "method": "6-parameter affine, least squares",
            "matrix_model_yd_to_px": M.tolist(),
            "correspondences": corr_records,
            "residual_px": {
                "mean": round(float(np.mean(residuals)), 2),
                "max": round(float(np.max(residuals)), 2),
                "per_point": [round(r, 2) for r in residuals],
                "mean_excluding_front_bunker": round(float(np.mean(residuals[:-1])), 2),
                "note": "the front_bunker_centroid correspondence (last row above) is the single largest residual by a wide margin; mean_excluding_front_bunker shows the fit quality over the other 15 points alone. See that correspondence's own note.",
            },
        },
        "tee": {
            "method": "exact similarity (rotation + uniform scale + translation) through 2 correspondences",
            "scale_px_per_yd": round(tee_scale, 3),
            "rotation_deg": round(tee_angle, 3),
            "correspondences": tee_corrs,
            "extrapolated_back_corners": tee_extrapolated,
        },
        "pin_checks": pin_checks,
        "playfield_polygon_px": [[round(x, 1), round(y, 1)] for x, y in playfield_polygon_px],
        "horizon_px": horizon_px,
    }, M, tee_apply


def convex_hull(points):
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def inflate_polygon(poly, factor):
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    return [(cx + (x - cx) * factor, cy + (y - cy) * factor) for x, y in poly]


# ---------------------------------------------------------------------------
# aerial: aerial_map.json
# ---------------------------------------------------------------------------

def build_aerial_map(geom):
    corrs = []
    corr_records = []

    for a in ANGLES_DEG:
        key = f"{a}deg"
        m_pt = geom["green_boundary_yd"][key]
        px_pt = AERIAL_PX["green_boundary"][key]
        corrs.append((m_pt, px_pt))
        corr_records.append({"group": "green_boundary", "label": key,
                              "model_yd": list(m_pt), "pixel": list(px_pt), "source": "hand"})

    for i, m_pt in enumerate(geom["creek_far_bank_yd"]):
        px_pt = AERIAL_PX["creek_far_bank"][i]
        corrs.append((m_pt, px_pt))
        corr_records.append({"group": "creek_far_bank", "label": f"pt{i}",
                              "model_yd": list(m_pt), "pixel": list(px_pt), "source": "hand"})

    for side in ("left", "right"):
        m_pt = geom["back_bunker_centroids_yd"][side]
        px_pt = AERIAL_PX[f"bunker_{side}"]
        corrs.append((m_pt, px_pt))
        corr_records.append({"group": "back_bunker_centroid", "label": side,
                              "model_yd": list(m_pt), "pixel": list(px_pt), "source": "hand",
                              "note": "aerial edit did not add a front bunker; only these 2 exist"})

    for side in ("left", "right"):
        m_pt = geom["tee_markers_yd"][side]
        px_pt = AERIAL_PX[f"tee_marker_{side}"]
        corrs.append((m_pt, px_pt))
        corr_records.append({"group": "tee_marker", "label": side,
                              "model_yd": list(m_pt), "pixel": list(px_pt), "source": "hand"})

    M, residuals = fit_affine(corrs)
    for rec, res in zip(corr_records, residuals):
        rec["residual_px"] = round(res, 2)

    pin_checks = {}
    for name, (x, y) in geom["pins_yd"].items():
        px, py = apply_affine(M, x, y)
        pin_checks[name] = {"model_yd": [x, y], "pixel_px": [round(px, 1), round(py, 1)]}

    return {
        "source_image": "aerial_final.png",
        "method": "6-parameter affine, least squares (single global map: aerial is close to orthographic)",
        "matrix_model_yd_to_px": M.tolist(),
        "correspondences": corr_records,
        "residual_px": {
            "mean": round(float(np.mean(residuals)), 2),
            "max": round(float(np.max(residuals)), 2),
            "per_point": [round(r, 2) for r in residuals],
        },
        "pin_checks": pin_checks,
        "up_direction": "tee at bottom of frame; +model_y (downrange) points toward the top of the image",
    }, M


# ---------------------------------------------------------------------------
# Pin-on-green sampling check
# ---------------------------------------------------------------------------

def sample_color(img, x, y):
    x = int(round(x))
    y = int(round(y))
    x = max(0, min(img.width - 1, x))
    y = max(0, min(img.height - 1, y))
    return img.getpixel((x, y))


def is_green_turf(rgb):
    r, g, b = rgb[:3]
    # putting-surface green: G channel clearly dominant over R and B, not white sand / not dark shadow-black
    return (g > r + 5) and (g > b + 10) and (g > 60)


# ---------------------------------------------------------------------------
# Overlays
# ---------------------------------------------------------------------------

def draw_overlay(image_path, apply_fn, geom, out_path, extra_tee_fn=None):
    im = Image.open(image_path).convert("RGB")
    d = ImageDraw.Draw(im)

    def proj_poly(poly_yd):
        return [apply_fn(x, y) for x, y in poly_yd]

    def draw_poly(poly_yd, color, width=3):
        pts = proj_poly(poly_yd)
        d.line(pts + [pts[0]], fill=color, width=width)

    regions = geom["regions"]
    draw_poly(regions["green"], (255, 0, 0))
    draw_poly(regions["creek"], (0, 200, 255))
    draw_poly(regions["front_bunker"], (255, 200, 0))
    for bb in regions["back_bunkers"]:
        draw_poly(bb["poly"], (255, 200, 0))
    draw_poly(regions["tee"], (255, 0, 255))

    for name, (x, y) in geom["pins_yd"].items():
        px, py = apply_fn(x, y)
        r = 7
        d.ellipse([px - r, py - r, px + r, py + r], outline=(255, 255, 255), width=3)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(255, 0, 0))

    if extra_tee_fn is not None:
        pts = [extra_tee_fn(x, y) for x, y in geom["landmarks"]["tee_poly_yd"]]
        d.line(pts + [pts[0]], fill=(255, 0, 255), width=3)

    im.save(out_path)
    return im


def main():
    geom = model_geometry()

    hero_json, hero_M, tee_apply = build_camera_hero(geom)

    # pin-on-green color check for hero
    hero_img = Image.open(HERE / "hero_final.png").convert("RGB")
    for name, rec in hero_json["pin_checks"].items():
        px, py = rec["pixel_px"]
        rgb = sample_color(hero_img, px, py)
        rec["sampled_rgb"] = list(rgb)
        rec["on_green_turf"] = bool(is_green_turf(rgb))

    (HERE / "camera_hero.json").write_text(json.dumps(hero_json, indent=2))

    def hero_apply(x, y):
        # green_local for far-field points; tee for the tee box overlay uses tee_apply directly
        return apply_affine(hero_M, x, y)

    draw_overlay(HERE / "hero_final.png", hero_apply, geom, HERE / "hero_final_fit_overlay.png",
                 extra_tee_fn=tee_apply)

    aerial_json, aerial_M = build_aerial_map(geom)
    aerial_img = Image.open(HERE / "aerial_final.png").convert("RGB")
    for name, rec in aerial_json["pin_checks"].items():
        px, py = rec["pixel_px"]
        rgb = sample_color(aerial_img, px, py)
        rec["sampled_rgb"] = list(rgb)
        rec["on_green_turf"] = bool(is_green_turf(rgb))

    (HERE / "aerial_map.json").write_text(json.dumps(aerial_json, indent=2))

    def aerial_apply(x, y):
        return apply_affine(aerial_M, x, y)

    draw_overlay(HERE / "aerial_final.png", aerial_apply, geom, HERE / "aerial_final_fit_overlay.png")

    print("=== HERO green_local residuals (px) ===")
    print(json.dumps(hero_json["green_local"]["residual_px"], indent=2))
    print("=== HERO tee correspondences ===")
    print(json.dumps(hero_json["tee"]["correspondences"], indent=2))
    print("=== HERO pin checks ===")
    print(json.dumps(hero_json["pin_checks"], indent=2))
    print("=== AERIAL residuals (px) ===")
    print(json.dumps(aerial_json["residual_px"], indent=2))
    print("=== AERIAL pin checks ===")
    print(json.dumps(aerial_json["pin_checks"], indent=2))


if __name__ == "__main__":
    main()
