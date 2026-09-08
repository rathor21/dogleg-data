"""Layout sketch for release 003's hero art (issue #11).

Renders a flat-fill schematic of Augusta 12 in the elevated three-quarter
perspective chosen by the prototype (docs/plans/2026-08-13-003-prototype-findings.md):
camera behind the tee, looking down the fairway, tee box in the foreground,
Rae's Creek and the green receding toward a horizon near the top of frame.

Every hazard boundary comes from the model itself:
- the green's diagonal front (creek-side) and back edges are read straight
  off model._front_edge_yd / model._back_edge_yd, sampled across x -- never
  redrawn or approximated by hand.
- the green's width and the pins' (x, y) positions come straight off
  data.HOLE and data.PINS.
- the bunker locations come straight off data.HOLE's x-ranges and depths,
  anchored to the same edge functions.

The one thing this file adds that data.py/model.py do not model: the
pixel-space camera projection used to turn (x, y) yards into (px, py)
screen coordinates -- an ART-ONLY constant block, called out below and
recorded in sketch_coords.json's "projection" block, so later tickets can
map model yards to art pixels without re-deriving this file's choices.
CREEK_WIDTH_YD used to be a second, disconnected art-only figure (model.py
carried only a single front-edge line, since scoring only needed to know
"short of the green" vs. "on it"); the region-geometry fix now prices a
finite creek band in model.region_at too, so this file reads the shared
data.CREEK_WIDTH_YD instead of inventing its own. Nothing in data.py or
model.py is modified or reimplemented here.

Colors are drawn from the brand palette (.impeccable.md / Dogleg_Data_Brand_Spec.md)
plus a small number of tan/cream variants in the same family, standing in
for grass/sand/water tones without introducing green or yellow -- this is a
geometry-registration reference for image-to-image generation, not the
final artwork, so it stays schematic rather than photorealistic.

Usage: python3 sketch.py [--out sketch.png] [--coords sketch_coords.json]
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import data   # noqa: E402
import model  # noqa: E402

from PIL import Image, ImageDraw  # noqa: E402

# ---------------------------------------------------------------------------
# Brand palette (exact hex from .impeccable.md), plus tan/cream family
# variants used only to separate regions (rough vs. fairway vs. green) that
# the 7-token brand palette doesn't itself distinguish. No green, no yellow.
# ---------------------------------------------------------------------------

INK = "#1C1B18"
CREAM_BG = "#F4EDE0"
CREAM_CARD = "#FBF7EE"
CLAY = "#C05A36"
BLUE = "#5B7FA6"
MUTED = "#8A7F6E"
LINE = "#E2D8C6"

BACKDROP = "#7D7359"      # deep muted olive-saddle -- distant trees/azalea ledge, top of frame
ROUGH = "#C2B184"         # golden tan -- out-of-corridor ground, clearly darker than fairway
FAIRWAY = "#EEE4CC"       # light warm cream -- short grass corridor
GREEN_FILL = "#F8F2E2"    # lightest cream -- putting surface
SHAVED_BANK = "#E4D8B9"   # transition tone -- mown bank around the front bunker
TEE_FILL = CREAM_CARD

# ---------------------------------------------------------------------------
# ART-ONLY constants: not in data.py/model.py, documented here and in
# art/README.md, EXCEPT CREEK_WIDTH_YD below, which now reads data.py's own
# modeled figure instead of carrying a second, disconnected one. Tee box
# extent is decorative foreground dressing.
# ---------------------------------------------------------------------------

CREEK_WIDTH_YD = data.CREEK_WIDTH_YD  # MODELED in data.py (region-geometry fix, this
                                       # pass), range 4.0-8.0 yd; no longer a separate
                                       # art-only figure
TEE_BOX_HALF_WIDTH_YD = 7.0  # ART-ONLY: decorative tee box footprint
TEE_BOX_BACK_YD = -6.0       # ART-ONLY: how far behind y=0 the tee box extends
BUNKER_HALO_YD = 1.6         # ART-ONLY: shaved-bank halo margin around each bunker
FAIRWAY_HALF_WIDTH_YD = 20.0  # ART-ONLY: width of the mown corridor either side of centerline

# ---------------------------------------------------------------------------
# Camera / projection. A stylized elevated three-quarter camera, not a
# physically exact pinhole model, matching the prototype's brief ("beauty,
# not physical accuracy") and the findings' note that the whole composition
# is 2D perspective math. Two separate easings, tuned so the green/creek/
# bunker complex -- the point of the picture -- gets real screen presence
# instead of collapsing into a sliver near the horizon the way a single
# physically literal 1/depth projection would over a 190-yard hole:
#
# - depth (screen_y): three-segment piecewise-linear budget across three
#   yardage bands (tee box / fairway / green complex), each given its own
#   fixed pixel allowance, so the far band (where all the interesting
#   geometry lives) is not starved by a smooth curve favoring the near
#   field.
# - width (half-width px): a single gamma<1 power curve over the full
#   range, front-loaded so most of the lateral convergence happens over the
#   long boring fairway and the green complex plateaus at a legible width
#   instead of pinching to a point.
#
# y_break (the fairway/green-complex boundary) is derived from the model's
# own front_edge_yd at x=0 minus the art-only creek width, not a hand-typed
# yardage, so this stays correct if the geometry ranges ever change.
# ---------------------------------------------------------------------------

CANVAS_W, CANVAS_H = 1600, 900       # 16:9, matches the hero art's target aspect
Y_MIN_YD = TEE_BOX_BACK_YD           # nearest point ever projected (tee box back edge)
Y_MAX_YD = 200.0                     # farthest point ever projected (past long-trouble buffer)

GROUND_NEAR_PX = 862.0               # screen y at Y_MIN_YD (tee box back edge, bottom of frame)
TEE_FRONT_PX = 798.0                 # screen y at y=0 (tee line)
MID_PX = 520.0                       # screen y at y_break (creek near bank, fairway/green boundary)
HORIZON_PX = 150.0                   # screen y approached as depth -> Y_MAX_YD

GAMMA_X = 0.55                       # width-easing exponent, <1 = shrink front-loaded near the tee
NEAR_HALF_WIDTH_PX = 760.0           # half-width in px at Y_MIN_YD
FAR_HALF_WIDTH_PX = 210.0            # half-width in px at Y_MAX_YD (kept legible, not a pinpoint)
FRAME_HALF_WIDTH_YD = 34.0           # yards of lateral spread mapped to the current half-width px


def _lerp(a, b, t):
    return a + (b - a) * t


def screen_y_for(y_yd, y_break):
    """Piecewise-linear depth budget: tee box, fairway, green complex."""
    if y_yd <= 0.0:
        t = (y_yd - Y_MIN_YD) / (0.0 - Y_MIN_YD)
        t = min(1.0, max(0.0, t))
        return _lerp(GROUND_NEAR_PX, TEE_FRONT_PX, t)
    if y_yd <= y_break:
        t = y_yd / y_break
        t = min(1.0, max(0.0, t))
        return _lerp(TEE_FRONT_PX, MID_PX, t)
    t = (y_yd - y_break) / (Y_MAX_YD - y_break)
    t = max(0.0, t)  # allow slight overshoot past Y_MAX_YD for backdrop dressing
    return _lerp(MID_PX, HORIZON_PX, t)


def half_width_px_for(y_yd):
    t_lin = (y_yd - Y_MIN_YD) / (Y_MAX_YD - Y_MIN_YD)
    t_lin = max(0.0, t_lin)
    t_eased = t_lin ** GAMMA_X
    return _lerp(NEAR_HALF_WIDTH_PX, FAR_HALF_WIDTH_PX, t_eased)


def make_projector(y_break):
    """Bind y_break (derived from the model's own geometry) and return a
    project(x_yd, y_yd) -> (px, py) closure. y_yd: carry distance from the
    tee. x_yd: lateral offset, positive = right / Sunday side, matching
    data.py's convention exactly -- no sign flip."""
    def project(x_yd, y_yd):
        py = screen_y_for(y_yd, y_break)
        half_w_px = half_width_px_for(y_yd)
        px_per_yard = half_w_px / FRAME_HALF_WIDTH_YD
        px = CANVAS_W / 2.0 + x_yd * px_per_yard
        return px, py
    return project


def _proj_pts(pts_yd, project):
    return [project(x, y) for x, y in pts_yd]


def _sample_edge(x_lo, x_hi, edge_fn, geom, n=24):
    """Sample edge_fn(x, geom) at n points from x_lo to x_hi -> [(x, y), ...]."""
    if n < 2:
        n = 2
    step = (x_hi - x_lo) / (n - 1)
    out = []
    for i in range(n):
        x = x_lo + step * i
        out.append((x, edge_fn(x, geom)))
    return out


def diagonal_band_polygon(x_lo, x_hi, lo_edge_fn, hi_edge_fn, geom, n=16):
    """Polygon (model-space yd points) for the band between two possibly-
    diagonal edge functions of x, from x_lo to x_hi. Both edges sampled (not
    just their endpoints) so the nonlinear pixel projection renders the true
    diagonal, not a chord approximation."""
    bottom = _sample_edge(x_lo, x_hi, lo_edge_fn, geom, n)
    top = _sample_edge(x_hi, x_lo, hi_edge_fn, geom, n)  # reversed, closes the loop
    return bottom + top


def build_scene():
    """Compute every region polygon (in yards) and landmark point, using
    model.py's own geometry functions throughout. Returns (regions, landmarks)."""
    geom = model._resolve_geometry()  # published-range midpoints, same defaults expected_score() uses

    def front_edge(x, g):
        return model._front_edge_yd(x, g)

    def back_edge(x, g):
        return model._back_edge_yd(x, g)

    half_width = geom["width"] / 2.0
    left_edge, right_edge = -half_width, half_width

    # --- fairway: tee line (y=0) up to the creek's near bank ---
    def creek_near_bank(x, g):
        return front_edge(x, g) - CREEK_WIDTH_YD

    fairway_x_lo, fairway_x_hi = -FAIRWAY_HALF_WIDTH_YD, FAIRWAY_HALF_WIDTH_YD
    fairway_poly = diagonal_band_polygon(
        fairway_x_lo, fairway_x_hi,
        lambda x, g: 0.0, creek_near_bank, geom, n=20,
    )

    # --- creek: near bank (art-only offset) to far bank (model._front_edge_yd, exact) ---
    creek_poly = diagonal_band_polygon(
        fairway_x_lo, fairway_x_hi,
        creek_near_bank, front_edge, geom, n=24,
    )
    # Camera depth breakpoint: where the fairway band ends and the green
    # complex band begins, derived from the model's own front edge at
    # centerline minus the art-only creek width -- not a hand-typed yardage.
    y_break = creek_near_bank(0.0, geom)
    creek_far_bank_samples = _sample_edge(fairway_x_lo, fairway_x_hi, front_edge, geom, n=9)
    creek_near_bank_samples = _sample_edge(fairway_x_lo, fairway_x_hi, creek_near_bank, geom, n=9)

    # --- green: parallelogram bounded by the two diagonal edges and the fixed width ---
    green_poly = diagonal_band_polygon(left_edge, right_edge, front_edge, back_edge, geom, n=20)

    # --- front bunker: data.HOLE's x-range, sitting against the green's front edge ---
    fb_lo, fb_hi = data.HOLE["front_bunker_x_range"]

    def front_bunker_bottom(x, g):
        return front_edge(x, g) - data.HOLE["front_bunker_depth_yd"]

    front_bunker_poly = diagonal_band_polygon(fb_lo, fb_hi, front_bunker_bottom, front_edge, geom, n=10)
    front_bunker_halo_poly = diagonal_band_polygon(
        fb_lo - BUNKER_HALO_YD, fb_hi + BUNKER_HALO_YD,
        lambda x, g: front_bunker_bottom(x, g) - BUNKER_HALO_YD,
        front_edge, geom, n=10,
    )
    fb_cx = (fb_lo + fb_hi) / 2.0
    front_bunker_centroid_yd = (fb_cx, front_edge(fb_cx, geom) - data.HOLE["front_bunker_depth_yd"] / 2.0)

    # --- back bunkers: two, each its own x-range, sitting against the green's back edge ---
    back_bunkers = []
    for i, (bb_lo, bb_hi) in enumerate(data.HOLE["back_bunker_x_ranges"]):
        def back_bunker_top(x, g):
            return back_edge(x, g) + data.HOLE["back_bunker_depth_yd"]
        poly = diagonal_band_polygon(bb_lo, bb_hi, back_edge, back_bunker_top, geom, n=10)
        halo = diagonal_band_polygon(
            bb_lo - BUNKER_HALO_YD, bb_hi + BUNKER_HALO_YD,
            back_edge, lambda x, g: back_bunker_top(x, g) + BUNKER_HALO_YD, geom, n=10,
        )
        cx = (bb_lo + bb_hi) / 2.0
        centroid_yd = (cx, back_edge(cx, geom) + data.HOLE["back_bunker_depth_yd"] / 2.0)
        back_bunkers.append({"poly": poly, "halo": halo, "centroid_yd": centroid_yd, "x_range": (bb_lo, bb_hi)})

    # --- tee box: decorative, art-only ---
    tee_poly = [
        (-TEE_BOX_HALF_WIDTH_YD, TEE_BOX_BACK_YD),
        (TEE_BOX_HALF_WIDTH_YD, TEE_BOX_BACK_YD),
        (TEE_BOX_HALF_WIDTH_YD, 0.0),
        (-TEE_BOX_HALF_WIDTH_YD, 0.0),
    ]
    tee_markers_yd = [(-TEE_BOX_HALF_WIDTH_YD * 0.5, -1.0), (TEE_BOX_HALF_WIDTH_YD * 0.5, -1.0)]
    tee_center_yd = (0.0, TEE_BOX_BACK_YD / 2.0)

    regions = {
        "backdrop": None,  # drawn as a fixed pixel band, not a yard polygon
        "rough": None,     # drawn as full-canvas base fill
        "fairway": fairway_poly,
        "creek": creek_poly,
        "green": green_poly,
        "front_bunker": front_bunker_poly,
        "front_bunker_halo": front_bunker_halo_poly,
        "back_bunkers": back_bunkers,
        "tee": tee_poly,
    }

    landmarks = {
        "geom": geom,
        "tee_center_yd": tee_center_yd,
        "tee_markers_yd": tee_markers_yd,
        "tee_poly_yd": tee_poly,
        "green_poly_yd": green_poly,
        "front_bunker_centroid_yd": front_bunker_centroid_yd,
        "front_bunker_x_range": (fb_lo, fb_hi),
        "back_bunkers": back_bunkers,
        "creek_far_bank_samples_yd": creek_far_bank_samples,
        "creek_near_bank_samples_yd": creek_near_bank_samples,
        "fairway_half_width_yd": FAIRWAY_HALF_WIDTH_YD,
        "green_left_right_edge_yd": (left_edge, right_edge),
        "y_break_yd": y_break,
    }

    return regions, landmarks


def render(regions, landmarks, project):
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), ROUGH)
    draw = ImageDraw.Draw(img)

    # Backdrop band (distant trees / azalea ledge), top of frame, behind everything.
    draw.rectangle([0, 0, CANVAS_W, HORIZON_PX + 60], fill=BACKDROP)

    def poly_px(poly_yd):
        return _proj_pts(poly_yd, project)

    # Fairway
    draw.polygon(poly_px(regions["fairway"]), fill=FAIRWAY, outline=INK, width=2)

    # Creek (far bank is the model's own _front_edge_yd, exactly)
    draw.polygon(poly_px(regions["creek"]), fill=BLUE, outline=INK, width=2)

    # Front bunker: shaved-bank halo first, bunker on top
    draw.polygon(poly_px(regions["front_bunker_halo"]), fill=SHAVED_BANK, outline=None)
    draw.polygon(poly_px(regions["front_bunker"]), fill=CLAY, outline=INK, width=2)

    # Green
    draw.polygon(poly_px(regions["green"]), fill=GREEN_FILL, outline=INK, width=3)

    # Back bunkers: halo then bunker, each
    for bb in regions["back_bunkers"]:
        draw.polygon(poly_px(bb["halo"]), fill=SHAVED_BANK, outline=None)
        draw.polygon(poly_px(bb["poly"]), fill=CLAY, outline=INK, width=2)

    # Tee box
    draw.polygon(poly_px(regions["tee"]), fill=TEE_FILL, outline=INK, width=2)
    for mx, my in landmarks["tee_markers_yd"]:
        px, py = project(mx, my)
        r = 5
        draw.ellipse([px - r, py - r, px + r, py + r], fill=INK)

    # Pins: flagstick + pennant + base dot, uniform ink, no text (kept clean
    # for the image-to-image reference so the model has nothing to try to
    # transcribe -- the final art brief is explicit: no text, no logos).
    pin_px = {}
    for key, p in data.PINS.items():
        px, py = project(p["x"], p["y"])
        pin_px[key] = (px, py)
        stick_h = 46
        draw.line([(px, py), (px, py - stick_h)], fill=INK, width=3)
        draw.polygon([(px, py - stick_h), (px + 18, py - stick_h + 7), (px, py - stick_h + 14)],
                     fill=CREAM_CARD, outline=INK)
        r = 6
        draw.ellipse([px - r, py - r, px + r, py + r], fill=INK)

    return img, pin_px


def build_coords_json(landmarks, pin_px, project, tee_center_px, tee_corners_px, front_bunker_centroid_px, back_bunker_centroids_px):
    def pt(p):
        return {"x_px": round(p[0], 1), "y_px": round(p[1], 1)}

    coords = {
        "canvas": {"width": CANVAS_W, "height": CANVAS_H},
        "projection": {
            "note": "ART-ONLY stylized elevated three-quarter camera, not a physical pinhole model. "
                    "Depth (screen_y) is a 3-segment piecewise-linear budget across "
                    "[y_min_yd, 0] (tee box) -> [ground_near_px, tee_front_px], "
                    "[0, y_break_yd] (fairway) -> [tee_front_px, mid_px], and "
                    "[y_break_yd, y_max_yd] (green complex) -> [mid_px, horizon_px]. "
                    "y_break_yd is the model's own front_edge_yd(0) minus the art-only creek "
                    "width, not a hand-typed yardage. Width: t = ((y_yd - y_min_yd) / "
                    "(y_max_yd - y_min_yd)) ** gamma_x (floored at 0); "
                    "half_w_px = near_half_width_px - (near_half_width_px - far_half_width_px) * t; "
                    "px = canvas_width / 2 + x_yd * (half_w_px / frame_half_width_yd).",
            "y_min_yd": Y_MIN_YD,
            "y_max_yd": Y_MAX_YD,
            "y_break_yd": landmarks["y_break_yd"],
            "ground_near_px": GROUND_NEAR_PX,
            "tee_front_px": TEE_FRONT_PX,
            "mid_px": MID_PX,
            "horizon_px": HORIZON_PX,
            "gamma_x": GAMMA_X,
            "near_half_width_px": NEAR_HALF_WIDTH_PX,
            "far_half_width_px": FAR_HALF_WIDTH_PX,
            "frame_half_width_yd": FRAME_HALF_WIDTH_YD,
        },
        "art_only_constants": {
            "creek_width_yd": CREEK_WIDTH_YD,
            "tee_box_half_width_yd": TEE_BOX_HALF_WIDTH_YD,
            "tee_box_back_yd": TEE_BOX_BACK_YD,
            "bunker_halo_yd": BUNKER_HALO_YD,
            "fairway_half_width_yd": FAIRWAY_HALF_WIDTH_YD,
        },
        "model_geometry_used": {
            "resolved_geom": landmarks["geom"],
            "green_left_right_edge_yd": landmarks["green_left_right_edge_yd"],
        },
        "tee": {
            "center_px": pt(tee_center_px),
            "center_yd": landmarks["tee_center_yd"],
            "corners_px": [pt(p) for p in tee_corners_px],
            "corners_yd": landmarks["tee_poly_yd"],
        },
        "pins": {
            key: {
                "label": data.PINS[key]["label"],
                "x_yd": data.PINS[key]["x"],
                "y_yd": data.PINS[key]["y"],
                **pt(pin_px[key]),
            }
            for key in data.PINS
        },
        "green": {
            "corners_px": [pt(project(x, y)) for x, y in landmarks["green_poly_yd"]],
            "corners_yd": landmarks["green_poly_yd"],
        },
        "bunkers": {
            "front": {
                "centroid_px": pt(front_bunker_centroid_px),
                "centroid_yd": landmarks["front_bunker_centroid_yd"],
                "x_range_yd": landmarks["front_bunker_x_range"],
            },
            "back": [
                {
                    "centroid_px": pt(back_bunker_centroids_px[i]),
                    "centroid_yd": bb["centroid_yd"],
                    "x_range_yd": bb["x_range"],
                }
                for i, bb in enumerate(landmarks["back_bunkers"])
            ],
        },
        "creek": {
            "far_bank_samples": [
                {"x_yd": x, "y_yd": y, **pt(project(x, y))}
                for x, y in landmarks["creek_far_bank_samples_yd"]
            ],
            "near_bank_samples": [
                {"x_yd": x, "y_yd": y, **pt(project(x, y))}
                for x, y in landmarks["creek_near_bank_samples_yd"]
            ],
            "far_bank_source": "model._front_edge_yd(x, geom), exact -- not a redrawn approximation",
        },
    }
    return coords


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(pathlib.Path(__file__).parent / "sketch.png"))
    ap.add_argument("--coords", default=str(pathlib.Path(__file__).parent / "sketch_coords.json"))
    args = ap.parse_args()

    regions, landmarks = build_scene()
    project = make_projector(landmarks["y_break_yd"])
    img, pin_px = render(regions, landmarks, project)

    tee_center_px = project(*landmarks["tee_center_yd"])
    tee_corners_px = [project(x, y) for x, y in landmarks["tee_poly_yd"]]
    front_bunker_centroid_px = project(*landmarks["front_bunker_centroid_yd"])
    back_bunker_centroids_px = [project(*bb["centroid_yd"]) for bb in landmarks["back_bunkers"]]

    coords = build_coords_json(
        landmarks, pin_px, project, tee_center_px, tee_corners_px,
        front_bunker_centroid_px, back_bunker_centroids_px,
    )

    out_path = pathlib.Path(args.out)
    coords_path = pathlib.Path(args.coords)
    img.save(out_path)
    coords_path.write_text(json.dumps(coords, indent=2))
    print(f"wrote {out_path}")
    print(f"wrote {coords_path}")


if __name__ == "__main__":
    main()
