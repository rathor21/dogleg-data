"""Round six: fit the model's camera to a chosen hero-art candidate as a
ground-plane homography, instead of asking the generator to respect the
model's geometry (issue #11).

The pipeline inverts what every prior round did. Rounds one through five
treated the model's geometry (via sketch.py's stylized camera) as the fixed
reference and scored generated art against it. Sunny rejected every
geometry-first render as looking like a diagram, not Golden Bell -- the two
candidates that looked most like the real hole (r5_scratch_1/2) were never
constrained to that geometry at all. Round six flips the relationship: a
candidate's own painted geometry is now the reference, and a 3x3 homography
matrix mapping model yards (x, y, 1) to that candidate's image pixels is
FIT to it. "Registration" becomes the residual of that fit at a handful of
hand-identified landmarks, not a pass/fail color-threshold sweep against a
sketch nothing was asked to match.

Steps, per candidate:
1. Segment the candidate (resized to 1600x900) for water/sand/green regions
   and the tee box, by color, and extract landmark points from the masks
   (build_landmarks_from_image below). Annotated sanity-check image saved
   as hero_candidates/<name>_landmarks.png.
2. Build the corresponding model-space (yards) points from sketch.build_scene()
   (model_correspondences below) -- the same function every prior round's
   sketch.py has used, so nothing about the model's own geometry changes.
3. Fit a homography via the normalized DLT (fit_homography_dlt): correspondences
   are translated/scaled to have centroid at the origin and mean distance
   sqrt(2) from it (Hartley's normalization, standard practice for DLT
   numerical conditioning) before the SVD solve, then denormalized back.
4. Report residuals (fit_and_report) and draw the model's geometry through
   the fitted homography over the art (draw_overlay) for visual acceptance.

Usage: python3 fit_camera.py <candidate_name>   (e.g. r6_2, r6_4)
       python3 fit_camera.py --all             (r6_2 and r6_4, this round's pick)
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

# ---------------------------------------------------------------------------
# Per-candidate segmentation ROIs and thresholds. Hand-set by eye against a
# gridded pixel overlay of each resized (1600x900) candidate -- the same
# thing a person does when they say "the water starts about a third of the
# way down and stops before the tee." Every one of these boxes is a search
# region, not a claimed hazard boundary: the actual mask still comes from
# thresholding pixel color inside the box, and only the largest / most
# plausible connected component is kept. This is the "hand-tuned" half of
# the extraction the brief allows; the other half (does a detected point
# look right) is checked visually against *_landmarks.png below.
# ---------------------------------------------------------------------------

ROI = {
    "r6_2": {
        "water": (150, 300, 800, 470),      # creek + reflection, left 2/3 of frame
        "water_x_extent": (260, 620),        # restrict far-bank sampling to the near-monotonic run (the creek hooks back right of ~630px)
        # Bunkers hand-boxed individually (not one shared box + top-3), after
        # a shared box's simple color threshold split the front bunker into
        # two pieces on internal shading and let pale azalea highlights
        # outscore it for "largest 3" -- see README, round six, Part 2.
        "bunker_front": (400, 350, 590, 410),
        "bunker_near": (890, 350, 1120, 410),   # nearer/bigger of the two back bunkers -> model back-left (nearer model point)
        "bunker_far": (860, 310, 1000, 345),    # farther/smaller -> model back-right (farther model point)
        "green": (420, 335, 1030, 430),
        "tee": (250, 750, 1500, 850),
    },
    "r6_4": {
        "water": (150, 400, 1580, 650),
        "water_x_extent": (170, 1520),
        # r6_4 draws only two sand blobs, both to the right of and behind the
        # flag (no distinct bunker touches the creek in front of the green
        # the way r6_2's does) -- see README, round six Part 2. There is no
        # "bunker_front" box for this candidate; the fit uses only the two
        # back bunkers.
        "bunker_front": None,
        "bunker_far": (850, 310, 1080, 375),    # smaller/farther of the two -> model back-right (farther model point)
        "bunker_near": (900, 375, 1150, 445),   # bigger/nearer -> model back-left (nearer model point)
        "green": (250, 300, 1050, 430),
        "tee": (150, 650, 1500, 780),
    },
}

# ---------------------------------------------------------------------------
# Hand-picked green corners (image px), used in place of automatic
# segmentation for this one landmark. The putting surface in both
# candidates is a smooth, continuously-shaded patch with no sharp
# hue/saturation break from the surrounding fairway (unlike the creek,
# bunkers, and tee markers, which all have a hard color contrast against
# their surroundings) -- an automatic threshold either grabbed a thin
# symmetric "core" lens with no trace of the model's diagonal tilt, or
# leaked into the azalea band above it. Both candidates' four extreme
# points were instead read directly off a fine (20px-gridded, 1:1 scale)
# crop of each green complex -- see README, round six Part 2, for the
# specific crops and the reasoning. front_left is the average of the
# image's own leftmost and bottommost points, since the model's own
# front-left corner is simultaneously the nearest and the leftmost point
# of the green polygon under this camera (see model_correspondences).
HAND_GREEN_CORNERS = {
    "r6_2": {"front_left": (540.0, 385.0), "front_right": (1140.0, 365.0), "back_right": (1000.0, 370.0)},
    "r6_4": {"front_left": (445.0, 390.0), "front_right": (1000.0, 355.0), "back_right": (950.0, 335.0)},
}


def load_resized(path):
    im = Image.open(path).convert("RGB")
    if im.size != (CANVAS_W, CANVAS_H):
        im = im.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
    return im


def hsv_arrays(im):
    h, s, v = im.convert("HSV").split()
    return np.array(h, dtype=np.int16), np.array(s, dtype=np.int16), np.array(v, dtype=np.int16)


def connected_components(mask):
    """4-connectivity two-pass union-find labeling. mask: 2D bool array.
    Returns an int32 label array (0 = background, 1..N = components), and
    the number of components N. No scipy/cv2 available in this venv, so
    this is a small hand-rolled labeler restricted to the True pixels only
    (the masks this is called on are always small ROI crops or sparse
    thresholds, at most a few hundred thousand pixels)."""
    H, W = mask.shape
    labels = np.zeros((H, W), dtype=np.int32)
    parent = [0]

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            if ra < rb:
                parent[rb] = ra
            else:
                parent[ra] = rb

    ys, xs = np.nonzero(mask)
    next_label = 1
    for y, x in zip(ys.tolist(), xs.tolist()):
        left = labels[y, x - 1] if x > 0 and mask[y, x - 1] else 0
        up = labels[y - 1, x] if y > 0 and mask[y - 1, x] else 0
        if left == 0 and up == 0:
            labels[y, x] = next_label
            parent.append(next_label)
            next_label += 1
        elif left != 0 and up == 0:
            labels[y, x] = left
        elif left == 0 and up != 0:
            labels[y, x] = up
        else:
            labels[y, x] = left if left < up else up
            if left != up:
                union(left, up)
    for y, x in zip(ys.tolist(), xs.tolist()):
        labels[y, x] = find(labels[y, x])
    return labels, next_label - 1


def largest_components(mask, n=3, min_area=25):
    labels, count = connected_components(mask)
    if count == 0:
        return []
    areas = [(lbl, int((labels == lbl).sum())) for lbl in range(1, count + 1)]
    areas = [a for a in areas if a[1] >= min_area]
    areas.sort(key=lambda t: -t[1])
    out = []
    for lbl, area in areas[:n]:
        ys, xs = np.nonzero(labels == lbl)
        out.append({
            "label": lbl, "area": area,
            "centroid": (float(xs.mean()), float(ys.mean())),
            "bbox": (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())),
            "mask": (labels == lbl),
        })
    return out


def crop_box(arr, box):
    x0, y0, x1, y1 = box
    return arr[y0:y1, x0:x1], (x0, y0)


# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------

def segment_water(im, H, S, V, roi, x_extent):
    """Water mask via adaptive (percentile) low-saturation threshold inside
    the ROI -- these candidates render Rae's Creek as a muted, often
    pinkish-gray reflective surface rather than a saturated blue-cyan, so a
    fixed hue-band threshold (tried first, see README) badly under-detects.
    Saturation inside the ROI is bimodal (turf vs. water); the 40th
    percentile of the ROI's own saturation lands reliably in the trough."""
    box = roi["water"]
    s_roi, origin = crop_box(S, box)
    v_roi, _ = crop_box(V, box)
    thresh = np.percentile(s_roi, 40)
    mask_roi = (s_roi <= thresh) & (v_roi > 25)
    full = np.zeros_like(S, dtype=bool)
    x0, y0 = origin
    full[y0:y0 + mask_roi.shape[0], x0:x0 + mask_roi.shape[1]] = mask_roi
    comps = largest_components(full, n=1, min_area=200)
    if not comps:
        return None, full
    water_mask = comps[0]["mask"]

    x_lo, x_hi = x_extent
    xs_sample = np.linspace(x_lo, x_hi, 7)
    far_bank_pts = []
    for x in xs_sample:
        xi = int(round(x))
        col = water_mask[:, xi]
        ys = np.nonzero(col)[0]
        if len(ys) == 0:
            # nearest column with any water, search outward
            for dx in range(1, 15):
                for xj in (xi - dx, xi + dx):
                    if 0 <= xj < water_mask.shape[1]:
                        ys = np.nonzero(water_mask[:, xj])[0]
                        if len(ys):
                            break
                if len(ys):
                    break
        if len(ys):
            far_bank_pts.append((float(x), float(ys.min())))
    return far_bank_pts, water_mask


def segment_one_bunker(S, V, box):
    """Centroid of low-saturation/high-value ("sand") pixels inside a single
    hand-boxed bunker ROI. A tight, single-bunker box is used instead of one
    shared box + top-3-components: a shared box's fixed threshold split a
    bunker's own sand into two pieces on internal shading gradients, and let
    pale azalea highlights outscore a real bunker for "largest 3" (see
    README, round six Part 2). Taking the centroid of all thresholded
    pixels in a tight box sidesteps both failure modes."""
    s_roi, origin = crop_box(S, box)
    v_roi, _ = crop_box(V, box)
    mask_roi = (s_roi < 70) & (v_roi > 140)
    x0, y0 = origin
    ys, xs = np.nonzero(mask_roi)
    full = np.zeros_like(S, dtype=bool)
    full[y0:y0 + mask_roi.shape[0], x0:x0 + mask_roi.shape[1]] = mask_roi
    if len(xs) < 30:
        return None, full
    centroid = (float(xs.mean() + x0), float(ys.mean() + y0))
    return centroid, full


def segment_sand(im, H, S, V, roi):
    if roi.get("bunker_front") is not None:
        front, front_mask = segment_one_bunker(S, V, roi["bunker_front"])
    else:
        front, front_mask = None, np.zeros_like(S, dtype=bool)
    near, near_mask = segment_one_bunker(S, V, roi["bunker_near"])
    far, far_mask = segment_one_bunker(S, V, roi["bunker_far"])
    full = front_mask | near_mask | far_mask
    return {"front": front, "near": near, "far": far}, full


def segment_green(im, H, S, V, roi):
    box = roi["green"]
    h_roi, origin = crop_box(H, box)
    s_roi, _ = crop_box(S, box)
    v_roi, _ = crop_box(V, box)
    # putting surface: green hue, brighter and a bit more saturated than the
    # surrounding rough/fairway within this same tight box (calibrated per
    # candidate against the box's own median, since absolute tone varies
    # with each painting's light).
    v_thresh = np.percentile(v_roi, 55)
    mask_roi = (h_roi > 35) & (h_roi < 100) & (s_roi > 60) & (v_roi >= v_thresh)
    full = np.zeros_like(H, dtype=bool)
    x0, y0 = origin
    full[y0:y0 + mask_roi.shape[0], x0:x0 + mask_roi.shape[1]] = mask_roi
    comps = largest_components(full, n=1, min_area=300)
    if not comps:
        return None, full
    gm = comps[0]["mask"]
    ys, xs = np.nonzero(gm)
    leftmost = (float(xs.min()), float(ys[xs == xs.min()].mean()))
    rightmost = (float(xs.max()), float(ys[xs == xs.max()].mean()))
    topmost = (float(xs[ys == ys.min()].mean()), float(ys.min()))
    bottommost = (float(xs[ys == ys.max()].mean()), float(ys.max()))
    return {"leftmost": leftmost, "rightmost": rightmost, "topmost": topmost,
            "bottommost": bottommost}, gm


def segment_tee_markers(im, H, S, V, roi):
    """Two small, low-saturation tee markers near the bottom of frame --
    white in r6_2, dark charcoal in r6_4 (see README), so this looks for
    low saturation at EITHER extreme of value (bright white or dark
    charcoal) rather than assuming white."""
    box = roi["tee"]
    s_roi, origin = crop_box(S, box)
    v_roi, _ = crop_box(V, box)
    mask_roi = (s_roi < 60) & ((v_roi > 150) | (v_roi < 55))
    full = np.zeros_like(S, dtype=bool)
    x0, y0 = origin
    full[y0:y0 + mask_roi.shape[0], x0:x0 + mask_roi.shape[1]] = mask_roi
    comps = largest_components(full, n=2, min_area=15)
    comps.sort(key=lambda c: c["centroid"][0])  # left marker first
    return comps, full


# ---------------------------------------------------------------------------
# Model-space correspondences (yards), from sketch.build_scene()
# ---------------------------------------------------------------------------

def model_correspondences():
    regions, landmarks = sketch.build_scene()
    geom = landmarks["geom"]

    creek_x_lo, creek_x_hi = -20.0, 20.0  # sketch.py's own fairway_half_width_yd extent
    creek_far_bank_yd = [
        (x, model._front_edge_yd(x, geom))
        for x in np.linspace(creek_x_lo, creek_x_hi, 7)
    ]

    left_edge, right_edge = landmarks["green_left_right_edge_yd"]
    front_left = (left_edge, model._front_edge_yd(left_edge, geom))
    front_right = (right_edge, model._front_edge_yd(right_edge, geom))
    back_right = (right_edge, model._back_edge_yd(right_edge, geom))
    back_left = (left_edge, model._back_edge_yd(left_edge, geom))

    return {
        "creek_far_bank_yd": creek_far_bank_yd,
        "front_bunker_yd": landmarks["front_bunker_centroid_yd"],
        "back_bunkers_yd": [bb["centroid_yd"] for bb in landmarks["back_bunkers"]],
        "green_corners_yd": {
            "front_left": front_left, "front_right": front_right,
            "back_right": back_right, "back_left": back_left,
        },
        "tee_markers_yd": landmarks["tee_markers_yd"],
        "landmarks": landmarks,
        "regions": regions,
    }


# ---------------------------------------------------------------------------
# Homography: normalized DLT
# ---------------------------------------------------------------------------

def _normalize_points(pts):
    pts = np.asarray(pts, dtype=np.float64)
    centroid = pts.mean(axis=0)
    d = pts - centroid
    mean_dist = np.sqrt((d ** 2).sum(axis=1)).mean()
    scale = np.sqrt(2) / mean_dist if mean_dist > 0 else 1.0
    T = np.array([
        [scale, 0, -scale * centroid[0]],
        [0, scale, -scale * centroid[1]],
        [0, 0, 1],
    ])
    pts_h = np.hstack([pts, np.ones((len(pts), 1))])
    pts_n = (T @ pts_h.T).T
    return pts_n[:, :2], T


def fit_homography_dlt(src_pts, dst_pts):
    """Normalized DLT: src (model yards) -> dst (image px). >=4 correspondences."""
    src_n, T_src = _normalize_points(src_pts)
    dst_n, T_dst = _normalize_points(dst_pts)

    A = []
    for (x, y), (u, v) in zip(src_n, dst_n):
        A.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
        A.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
    A = np.array(A)
    _, _, Vt = np.linalg.svd(A)
    H_n = Vt[-1].reshape(3, 3)

    H = np.linalg.inv(T_dst) @ H_n @ T_src
    H = H / H[2, 2]
    return H


def apply_homography(H, x, y):
    p = H @ np.array([x, y, 1.0])
    return p[0] / p[2], p[1] / p[2]


# ---------------------------------------------------------------------------
# Landmark extraction driver
# ---------------------------------------------------------------------------

def build_landmarks_from_image(name):
    path = CANDIDATES_DIR / f"{name}.png"
    im = load_resized(path)
    H, S, V = hsv_arrays(im)
    roi = ROI[name]

    creek_pts, water_mask = segment_water(im, H, S, V, roi, roi["water_x_extent"])
    sand_comps, sand_mask = segment_sand(im, H, S, V, roi)
    green_pts, green_mask = segment_green(im, H, S, V, roi)
    tee_comps, tee_mask = segment_tee_markers(im, H, S, V, roi)

    # Three bunkers come from three separately hand-boxed ROIs (see ROI
    # dict). Note this left/right label is a *relative* match by depth, not
    # an absolute left/right position match: the model's back-left bunker
    # sits outside the green's own left edge, while both candidates draw
    # their two back bunkers to the right of the green's centerline
    # (matching the real hole's tee-view look, not the model's own
    # mirrored-looking layout) -- see README.
    front_bunker_img = sand_comps["front"]
    # Bunker pairing was decided empirically, not assumed: for each
    # candidate, both possible pairings of {near, far} image bunkers to
    # {model back-left, model back-right} were fit (holding every other
    # landmark fixed) and scored by residual -- see README, round six Part
    # 2, "Which back bunker is which". Both candidates score better with
    # the farther-looking image bunker paired to the model's NEARER back
    # bunker (back-left, y=162.5) and the nearer-looking image bunker
    # paired to the model's FARTHER one (back-right, y=183.5) -- i.e. image
    # apparent depth and model depth run opposite here, most likely because
    # bunker size in these paintings tracks its role/composition rather
    # than strict camera distance.
    back_left_img = sand_comps["far"]
    back_right_img = sand_comps["near"]
    hand_corrections = []
    if roi.get("bunker_front") is None:
        hand_corrections.append(
            f"{name}: no front-bunker box -- this candidate draws only two sand "
            f"blobs, both back-right of the flag, none touching the creek. The fit "
            f"uses only the two back-bunker correspondences."
        )
    elif front_bunker_img is None:
        hand_corrections.append(f"{name}: bunker 'front' ROI found no sand pixels above the area threshold.")
    for k, v in (("near/backL", back_left_img), ("far/backR", back_right_img)):
        if v is None:
            hand_corrections.append(f"{name}: bunker '{k}' ROI found no sand pixels above the area threshold.")

    # Green corners: hand-picked (see HAND_GREEN_CORNERS docstring above) --
    # automatic segmentation (segment_green, still run above for the debug
    # mask/visualization only) either grabbed a thin symmetric core with no
    # trace of the model's diagonal tilt, or leaked into the azalea band,
    # because this candidate's putting surface has no hard color break from
    # the surrounding turf the way the creek/bunkers/tee markers do.
    green_corners_img = HAND_GREEN_CORNERS.get(name)
    hand_corrections.append(
        f"{name}: green corners are hand-picked from a fine gridded crop, not "
        f"auto-segmented (segment_green's threshold found either a thin symmetric "
        f"lens with no diagonal tilt, or azalea-band false positives -- see README). "
        f"front_left is the average of the green's own leftmost and bottommost "
        f"points, since those coincide at one model corner under this camera."
    )

    tee_img = [c["centroid"] for c in tee_comps] if len(tee_comps) == 2 else None
    if tee_img is None:
        hand_corrections.append(f"{name}: tee marker detection did not find exactly 2 blobs ({len(tee_comps)} found).")

    result = {
        "image_size": im.size,
        "creek_far_bank_img": creek_pts,
        "front_bunker_img": front_bunker_img,
        "back_left_img": back_left_img,
        "back_right_img": back_right_img,
        "green_corners_img": green_corners_img,
        "tee_markers_img": tee_img,
        "hand_corrections": hand_corrections,
        "_debug": {
            "water_mask": water_mask, "sand_mask": sand_mask,
            "green_mask": green_mask, "tee_mask": tee_mask,
            "sand_comps": sand_comps,
        },
    }
    return im, result


def draw_landmarks_image(name, im, result):
    out = im.copy()
    draw = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except Exception:
        font = ImageFont.load_default()

    def dot(pt, color, label):
        x, y = pt
        r = 6
        draw.ellipse([x - r, y - r, x + r, y + r], outline=color, width=3)
        draw.text((x + 8, y - 8), label, fill=color, font=font)

    if result["creek_far_bank_img"]:
        for i, (x, y) in enumerate(result["creek_far_bank_img"]):
            dot((x, y), "#00CFFF", f"creek{i}")
    if result["front_bunker_img"]:
        dot(result["front_bunker_img"], "#FF7A00", "bunker-front")
    if result["back_left_img"]:
        dot(result["back_left_img"], "#FF7A00", "bunker-backL")
    if result["back_right_img"]:
        dot(result["back_right_img"], "#FF7A00", "bunker-backR")
    if result["green_corners_img"]:
        for k, pt in result["green_corners_img"].items():
            dot(pt, "#00FF66", f"green-{k}")
    if result["tee_markers_img"]:
        for i, pt in enumerate(result["tee_markers_img"]):
            dot(pt, "#FFFFFF", f"tee{i}")

    out.save(CANDIDATES_DIR / f"{name}_landmarks.png")
    return out


# ---------------------------------------------------------------------------
# Fit + report
# ---------------------------------------------------------------------------

def fit_and_report(name, img_landmarks):
    corr = model_correspondences()
    src, dst, labels = [], [], []

    if img_landmarks["creek_far_bank_img"]:
        model_pts = corr["creek_far_bank_yd"]
        for i, (px, py) in enumerate(img_landmarks["creek_far_bank_img"]):
            if i < len(model_pts):
                src.append(model_pts[i])
                dst.append((px, py))
                labels.append(f"creek_far_bank:{i}")

    if img_landmarks["front_bunker_img"]:
        src.append(corr["front_bunker_yd"]); dst.append(img_landmarks["front_bunker_img"]); labels.append("bunker_front")
    bb = corr["back_bunkers_yd"]
    # back_bunkers_yd[0] has x_range (-15,-8) -> left; [1] has x_range (6,13) -> right
    if img_landmarks["back_left_img"]:
        src.append(bb[0]); dst.append(img_landmarks["back_left_img"]); labels.append("bunker_backL")
    if img_landmarks["back_right_img"]:
        src.append(bb[1]); dst.append(img_landmarks["back_right_img"]); labels.append("bunker_backR")

    if img_landmarks["green_corners_img"]:
        gc = corr["green_corners_yd"]
        gi = img_landmarks["green_corners_img"]
        for k in ("front_left", "front_right", "back_right"):
            src.append(gc[k]); dst.append(gi[k]); labels.append(f"green_{k}")

    if img_landmarks["tee_markers_img"]:
        for i, (mx, my) in enumerate(corr["tee_markers_yd"]):
            src.append((mx, my)); dst.append(img_landmarks["tee_markers_img"][i]); labels.append(f"tee_marker:{i}")

    src = np.array(src, dtype=np.float64)
    dst = np.array(dst, dtype=np.float64)

    Hmat = fit_homography_dlt(src, dst)

    residuals = []
    for (x, y), (u, v), lbl in zip(src, dst, labels):
        pu, pv = apply_homography(Hmat, x, y)
        err_px = float(np.hypot(pu - u, pv - v))
        residuals.append({
            "label": lbl, "model_yd": (float(x), float(y)), "image_px": (float(u), float(v)),
            "fitted_px": (float(pu), float(pv)), "error_px": err_px,
            "error_pct_width": 100.0 * err_px / CANVAS_W,
        })

    max_err = max(r["error_px"] for r in residuals)
    mean_err = float(np.mean([r["error_px"] for r in residuals]))
    max_pct = max(r["error_pct_width"] for r in residuals)
    mean_pct = float(np.mean([r["error_pct_width"] for r in residuals]))

    # Horizon line: image of the line at infinity of the ground plane.
    # For a homography H mapping model-plane (x,y,1)->image px, the vanishing
    # line of the plane is given by the last row of H^{-1} (points at
    # infinity (x,y,0) map to H @ (x,y,0); the horizon in the image is the
    # set of vanishing points of all directions, i.e. the image line l such
    # that l^T is proportional to the third row of H^{-1}).
    Hinv = np.linalg.inv(Hmat)
    horizon_line = Hinv[2, :]  # a*u + b*v + c = 0 in image coords

    def horizon_y_at(u):
        a, b, c = horizon_line
        if abs(b) < 1e-9:
            return None
        return -(a * u + c) / b

    horizon_ys = [horizon_y_at(u) for u in (0, CANVAS_W / 2, CANVAS_W)]

    # Orientation check: does +x_yd move rightward and +y_yd move "upward"
    # (toward smaller screen py, since larger y_yd = farther = higher on
    # screen) under the fitted H, at a representative ground point?
    x0, y0 = 0.0, 140.0
    u0, v0 = apply_homography(Hmat, x0, y0)
    ux, vx = apply_homography(Hmat, x0 + 1.0, y0)
    uy, vy = apply_homography(Hmat, x0, y0 + 1.0)
    orientation = {
        "dx_du": float(ux - u0), "dx_dv": float(vx - v0),
        "dy_du": float(uy - u0), "dy_dv": float(vy - v0),
        "positive_x_moves_right": bool((ux - u0) > 0),
        "positive_y_moves_up_on_screen": bool((vy - v0) < 0),
    }

    return {
        "candidate": name,
        "homography_model_yd_to_image_px": Hmat.tolist(),
        "correspondences": residuals,
        "residual_summary": {
            "max_error_px": max_err, "mean_error_px": mean_err,
            "max_error_pct_width": max_pct, "mean_error_pct_width": mean_pct,
            "n_correspondences": len(residuals),
        },
        "horizon": {
            "line_image_coords_au_bv_c=0": horizon_line.tolist(),
            "y_at_u=0,W/2,W": horizon_ys,
        },
        "orientation_check": orientation,
        "hand_corrections": img_landmarks["hand_corrections"],
    }


def draw_overlay(name, im, Hmat):
    corr = model_correspondences()
    regions = corr["regions"]
    landmarks = corr["landmarks"]
    out = im.copy()
    draw = ImageDraw.Draw(out)

    def proj(x, y):
        return apply_homography(Hmat, x, y)

    def poly_px(poly_yd):
        return [proj(x, y) for x, y in poly_yd]

    draw.line(poly_px(regions["creek"]) + [poly_px(regions["creek"])[0]], fill="#00CFFF", width=3)
    draw.polygon(poly_px(regions["green"]), outline="#00FF66", width=3)
    draw.polygon(poly_px(regions["front_bunker"]), outline="#FF7A00", width=3)
    for bb in regions["back_bunkers"]:
        draw.polygon(poly_px(bb["poly"]), outline="#FF7A00", width=3)
    draw.polygon(poly_px(regions["tee"]), outline="#FFFFFF", width=3)

    for key, p in data.PINS.items():
        px, py = proj(p["x"], p["y"])
        r = 10
        draw.line([(px - r, py - r), (px + r, py + r)], fill="#FF00AA", width=3)
        draw.line([(px - r, py + r), (px + r, py - r)], fill="#FF00AA", width=3)

    out.save(CANDIDATES_DIR / f"{name}_fit_overlay.png")
    return out


def run(name):
    im, img_landmarks = build_landmarks_from_image(name)
    draw_landmarks_image(name, im, img_landmarks)
    report = fit_and_report(name, img_landmarks)
    (CANDIDATES_DIR / f"{name}_fit.json").write_text(json.dumps(report, indent=2))
    Hmat = np.array(report["homography_model_yd_to_image_px"])
    draw_overlay(name, im, Hmat)
    print(f"--- {name} ---")
    print(json.dumps(report["residual_summary"], indent=2))
    print("horizon y at u=0,W/2,W:", report["horizon"]["y_at_u=0,W/2,W"])
    print("orientation:", report["orientation_check"])
    for c in report["hand_corrections"]:
        print("HAND CORRECTION:", c)
    return report


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args == ["--all"]:
        names = ["r6_2", "r6_4"]
    else:
        names = args
    for n in names:
        run(n)
