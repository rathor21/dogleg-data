"""Code-rendered ground plane for release 003's hero art, round four (issue #11).

Round three's verdict: two rounds of nano-banana textures pushed through
masks never produced an illustration -- the composited ground read as a
blurred green-on-green smear, the green as a small dark parallelogram, the
bunkers as pale smudges, the creek as a thin dark stripe. This module
replaces every generated ground texture with a direct, procedural render in
the register of a clean editorial yardage-book illustration (see
docs/plans/assets/003-proto-desktop.png, the prototype's accepted flat-style
composition): flat-ish base colors, crisp region edges, and a small number
of explicit relief cues (rim lines, shadow bands, a waterline, bunker lips,
rake lines) drawn with code, not sampled from a generated tile.

Geometry is untouched: every region comes from sketch.build_scene() and
masks.build_masks(), the same functions round two and three already used, so
this module adds zero new geometry -- only paint.

Usage: imported by composite.py. Not meant to be run standalone, but
`python3 render_ground.py --out ground_debug.png` renders variant "a" alone
for inspection.
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sketch  # noqa: E402
import masks as masks_mod  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

HERE = pathlib.Path(__file__).parent
CANVAS = (sketch.CANVAS_W, sketch.CANVAS_H)

# ---------------------------------------------------------------------------
# Palette. Hex values are the brief's own guidance; final RGB tuning (mostly
# the rough/fringe/lip derived tones) done by eye against rendered output.
# ---------------------------------------------------------------------------

TURF_MID = np.array([0x6F, 0x8F, 0x4A], dtype=np.float64)          # base fairway turf
ROUGH_BASE = np.array([0x5D, 0x6D, 0x39], dtype=np.float64)         # warmer + noticeably darker than turf
TEE_LIGHT = np.array([0x9B, 0xB6, 0x6C], dtype=np.float64)
CREEK_WATER = np.array([0x2F, 0x5D, 0x6B], dtype=np.float64)
CREEK_HILITE = np.array([0x7E, 0xAE, 0xB0], dtype=np.float64)
BANK_FAR_LINE = (0xD9, 0xD2, 0xB8)                                   # cream stone/shaved-bank line
BANK_NEAR_SHADOW = (0x12, 0x22, 0x26)
GREEN_BRIGHT = np.array([0x9C, 0xCF, 0x6A], dtype=np.float64)
GREEN_RIM = (0xE6, 0xF2, 0xC9)
GREEN_SHADOW = (0x2A, 0x38, 0x1E)
SAND = np.array([0xE6, 0xD9, 0xB0], dtype=np.float64)
SAND_LIP = (0x8C, 0x70, 0x40)
BANK_STRIP = np.array([0xA9, 0xB4, 0x62], dtype=np.float64)          # shaved-bank halo (lighter/yellower)

STRIPE_YD_TURF = 4.0
STRIPE_YD_GREEN = 2.0
STRIPE_CONTRAST_TURF = 0.05     # 5%, brief's own "4 to 6 percent"
STRIPE_CONTRAST_GREEN = 0.045

GRAIN_SIGMA = 6.0                # ~2.4% of 255, per-pixel independent noise
FAIRWAY_FEATHER_PX = 20          # the ticket's own number for the fairway/rough transition
BANK_FEATHER_PX = 3
CREEK_FEATHER_PX = 2
BUNKER_FEATHER_PX = 1.5
GREEN_FEATHER_PX = 2
TEE_FEATHER_PX = 1.5

FRINGE_WIDTH_YD = 1.5
BUNKER_WOBBLE_PX = 1.6


# ---------------------------------------------------------------------------
# Inverse camera: screen row -> model y-yards. Identical to composite.py's
# own y_yd_for_screen_y (duplicated here rather than imported, so this module
# has no dependency on composite.py -- composite.py imports *this* module,
# not the other way around).
# ---------------------------------------------------------------------------

def y_yd_for_screen_y(py, y_break):
    py = min(max(py, sketch.HORIZON_PX), sketch.GROUND_NEAR_PX)
    if py >= sketch.TEE_FRONT_PX:
        t = (py - sketch.GROUND_NEAR_PX) / (sketch.TEE_FRONT_PX - sketch.GROUND_NEAR_PX)
        return sketch.Y_MIN_YD + t * (0.0 - sketch.Y_MIN_YD)
    if py >= sketch.MID_PX:
        t = (py - sketch.TEE_FRONT_PX) / (sketch.MID_PX - sketch.TEE_FRONT_PX)
        return t * y_break
    t = (py - sketch.MID_PX) / (sketch.HORIZON_PX - sketch.MID_PX)
    return y_break + t * (sketch.Y_MAX_YD - y_break)


def yd_grids(canvas_size, y_break):
    """Per-pixel (x_yd, y_yd) grids over the whole canvas, via the exact
    camera sketch.py/masks.py use. y_yd varies by row only; x_yd depends on
    both row (lateral scale) and column."""
    w, h = canvas_size
    y_yd_row = np.array([y_yd_for_screen_y(py, y_break) for py in range(h)])
    px_per_yard_row = np.array([sketch.half_width_px_for(y) for y in y_yd_row]) / sketch.FRAME_HALF_WIDTH_YD
    cx = w / 2.0
    cols = np.arange(w)
    x_yd_grid = (cols[None, :] - cx) / px_per_yard_row[:, None]
    y_yd_grid = np.repeat(y_yd_row[:, None], w, axis=1)
    return x_yd_grid, y_yd_grid


def row_resolution_fade(y_yd_row, stripe_yd):
    """Anti-Moire fade, not a hand-picked depth cutoff: a stripe pattern
    with period stripe_yd aliases into hard noise the moment one screen row
    spans more than about a quarter of that period (fewer than ~4 screen
    rows per stripe), which happens well before the literal horizon because
    the camera's depth budget compresses distance heavily near the top of
    frame. Measuring the actual yards-per-row at each row and fading the
    stripe contrast out as that resolution degrades is what "fading out
    toward the horizon" has to mean for a procedural stripe -- a fixed
    fraction-of-Y_MAX cutoff either aliases before it kicks in or throws
    away stripes that would still have been resolvable."""
    dy = np.abs(np.gradient(y_yd_row))
    lo, hi = stripe_yd * 0.25, stripe_yd * 1.0
    return np.clip(1.0 - (dy - lo) / (hi - lo), 0.0, 1.0)


def stripe_multiplier(y_yd_grid, stripe_yd, contrast, row_fade=None):
    """Alternating +/-contrast bands every stripe_yd of depth. row_fade (h,)
    -- from row_resolution_fade -- suppresses the pattern per-row once the
    screen can no longer resolve it, instead of letting floor() alias."""
    band = np.floor(y_yd_grid / stripe_yd).astype(np.int64)
    alt = (band % 2).astype(np.float64) * 2.0 - 1.0
    if row_fade is None:
        row_fade = np.ones(y_yd_grid.shape[0])
    return 1.0 + alt * contrast * row_fade[:, None]


def corner_darken(canvas_size, strength=0.11):
    """Subtle radial falloff toward the two bottom corners only (not a full
    vignette) -- distance to the nearer of the two bottom corners,
    normalized to the canvas size."""
    w, h = canvas_size
    xs = np.arange(w)
    ys = np.arange(h)
    X, Y = np.meshgrid(xs, ys)
    dl = np.sqrt((X / w) ** 2 + ((h - Y) / h) ** 2)
    dr = np.sqrt(((w - X) / w) ** 2 + ((h - Y) / h) ** 2)
    d = np.minimum(dl, dr)
    falloff = np.clip(1.0 - d, 0.0, 1.0) ** 2
    return 1.0 - strength * falloff


def film_grain(canvas_size, sigma, seed=7):
    rng = np.random.default_rng(seed)
    w, h = canvas_size
    return rng.normal(0.0, sigma, size=(h, w, 1))


def mask_to_arr(mask_img, feather_px=0.0):
    if feather_px > 0:
        mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=feather_px))
    return np.asarray(mask_img, dtype=np.float64) / 255.0


def composite_rgb(base, add_rgb, alpha):
    """base, add_rgb: (h,w,3) float arrays. alpha: (h,w,1) or (h,w) float
    0..1. Standard over-composite."""
    if alpha.ndim == 2:
        alpha = alpha[..., None]
    return base * (1.0 - alpha) + add_rgb * alpha


def wobble_mask(mask_img, amp_px=BUNKER_WOBBLE_PX, seed=0):
    """Perturb a mask's boundary with smooth low-frequency displacement (a
    coarse random field upsampled with bicubic interpolation, then used to
    resample the mask), so bunker edges read as drawn/irregular rather than
    a clean polygon. Displacement amplitude is small (1-2px) by design --
    this is meant to read as a hand-drawn boundary, not a jagged one."""
    arr = np.asarray(mask_img, dtype=np.uint8)
    h, w = arr.shape
    rng = np.random.default_rng(seed)
    small = 12
    dx_small = rng.uniform(-1.0, 1.0, size=(small, small))
    dy_small = rng.uniform(-1.0, 1.0, size=(small, small))
    dx_img = Image.fromarray(((dx_small * 0.5 + 0.5) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    dy_img = Image.fromarray(((dy_small * 0.5 + 0.5) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    dx = (np.asarray(dx_img, dtype=np.float64) / 255.0 * 2.0 - 1.0) * amp_px
    dy = (np.asarray(dy_img, dtype=np.float64) / 255.0 * 2.0 - 1.0) * amp_px
    ys, xs = np.mgrid[0:h, 0:w]
    sx = np.clip(np.round(xs + dx).astype(np.int64), 0, w - 1)
    sy = np.clip(np.round(ys + dy).astype(np.int64), 0, h - 1)
    return Image.fromarray(arr[sy, sx])


def draw_soft_line(canvas_arr, pts, color, alpha255, width, blur):
    """Draw a soft line into an (h,w,3) float array and return the updated
    array. Shared by every relief cue (rims, shadows, waterline, bunker
    lips) so they read as one consistent kind of mark."""
    h, w = canvas_arr.shape[:2]
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(layer).line(pts, fill=tuple(color) + (alpha255,), width=width, joint="curve")
    if blur:
        layer = layer.filter(ImageFilter.GaussianBlur(radius=blur))
    layer_arr = np.asarray(layer, dtype=np.float64)
    a = layer_arr[..., 3:4] / 255.0
    return canvas_arr * (1.0 - a) + layer_arr[..., :3] * a


def rake_lines(canvas_arr, mask_arr, y_yd_grid, row_fade, spacing_yd=2.0, contrast=0.06):
    """Faint rake lines inside a bunker: a low-contrast stripe pattern,
    masked to the bunker's own footprint so it never bleeds outside it. Uses
    the same row_resolution_fade as the turf/green stripes -- bunkers sit
    far enough out that this often fades to near-nothing, which is correct:
    a rake mark 150+ yards from camera isn't individually resolvable, so it
    should recede rather than alias into bars."""
    mult = stripe_multiplier(y_yd_grid, spacing_yd, contrast, row_fade=row_fade)
    out = canvas_arr * mult[..., None]
    a = mask_arr[..., None]
    return canvas_arr * (1.0 - a) + out * a


def render(regions, landmarks, project, variant="a", seed=7):
    """Render the full ground plane (1600x900) as an RGB PIL Image. Includes
    the whole canvas, not just below the horizon -- composite.py crossfades
    this against the environment plate near the horizon, so what this
    function draws above the true horizon is simply discarded/blended away
    there and never needs to look correct on its own."""
    w, h = CANVAS
    geom = landmarks["geom"]
    y_break = landmarks["y_break_yd"]
    x_yd, y_yd = yd_grids(CANVAS, y_break)

    warm_turf = variant == "b"
    stripe_boost = 1.5 if variant == "b" else 1.0

    turf_mid = TURF_MID + (np.array([14, 4, -10]) if warm_turf else 0.0)

    masks, _regions2, _landmarks2, _project2 = masks_mod.build_masks()

    y_yd_row = y_yd[:, 0]
    turf_row_fade = row_resolution_fade(y_yd_row, STRIPE_YD_TURF)
    green_row_fade = row_resolution_fade(y_yd_row, STRIPE_YD_GREEN)

    # ---- base turf / rough, mow stripes, corner falloff, grain ----
    stripe_mult = stripe_multiplier(y_yd, STRIPE_YD_TURF, STRIPE_CONTRAST_TURF * stripe_boost, row_fade=turf_row_fade)
    turf_rgb = turf_mid[None, None, :] * stripe_mult[..., None]
    rough_rgb = ROUGH_BASE[None, None, :] * stripe_mult[..., None]

    fairway_alpha = mask_to_arr(masks["fairway"], feather_px=FAIRWAY_FEATHER_PX)
    base = composite_rgb(rough_rgb, turf_rgb, fairway_alpha)

    corner_mult = corner_darken(CANVAS)
    base = base * corner_mult[..., None]
    base = base + film_grain(CANVAS, GRAIN_SIGMA, seed=seed)

    # ---- tee box: lighter, crisper rectangle + two markers ----
    tee_alpha = mask_to_arr(masks_mod._rasterize(
        sketch._proj_pts(regions["tee"], project), CANVAS), feather_px=TEE_FEATHER_PX)
    tee_rgb = np.broadcast_to(TEE_LIGHT, (h, w, 3))
    base = composite_rgb(base, tee_rgb, tee_alpha)

    # ---- shaved-bank halo strips (bunker surrounds), lighter/yellower ----
    bank_alpha = mask_to_arr(masks["bank"], feather_px=BANK_FEATHER_PX)
    bank_rgb = BANK_STRIP[None, None, :] * stripe_mult[..., None]
    base = composite_rgb(base, bank_rgb, bank_alpha)

    # ---- creek: deep water, center reflective streak, horizontal ripple ----
    front_edge_grid = sketch.model._front_edge_yd(x_yd, geom)
    near_bank_grid = front_edge_grid - sketch.CREEK_WIDTH_YD
    band_t = np.clip((y_yd - near_bank_grid) / (front_edge_grid - near_bank_grid + 1e-6), 0.0, 1.0)
    streak_weight = np.clip(1.0 - np.abs(2.0 * band_t - 1.0), 0.0, 1.0) ** 1.6

    rng = np.random.default_rng(seed + 1)
    row_phase = rng.uniform(0, 2 * np.pi, size=h)
    ripple = 0.035 * np.sin(x_yd * 1.6 + row_phase[:, None]) + 0.02 * np.sin(x_yd * 3.7 - row_phase[:, None] * 1.3)
    creek_rgb = CREEK_WATER[None, None, :] * (1.0 + ripple[..., None])
    creek_rgb = creek_rgb + (CREEK_HILITE - CREEK_WATER)[None, None, :] * (streak_weight[..., None] * 0.55)

    creek_alpha = mask_to_arr(masks["creek"], feather_px=CREEK_FEATHER_PX)
    base = composite_rgb(base, creek_rgb, creek_alpha)

    # ---- bunkers: sand, wobbled crisp edges, far-side lip shadow, rake lines ----
    bunker_defs = [
        ("bunker_front", regions["front_bunker"]),
    ] + [
        (f"bunker_back_{i}", bb["poly"]) for i, bb in enumerate(regions["back_bunkers"])
    ]
    sand_mult = 1.0 + 0.02 * np.sin(x_yd * 3.1 + y_yd * 2.3)  # faint, fine-grained mottling, not a blur
    sand_rgb_full = SAND[None, None, :] * sand_mult[..., None]

    for i, (mask_name, _poly_yd) in enumerate(bunker_defs):
        raw_mask = masks[mask_name]
        wobbled = wobble_mask(raw_mask, seed=seed + 10 + i)
        alpha = mask_to_arr(wobbled, feather_px=BUNKER_FEATHER_PX)
        sand_with_rake = rake_lines(sand_rgb_full, alpha, y_yd, green_row_fade, spacing_yd=2.0, contrast=0.06)
        base = composite_rgb(base, sand_with_rake, alpha)

    # ---- green: brightest surface, fine stripes, fringe collar underneath ----
    left_edge, right_edge = landmarks["green_left_right_edge_yd"]

    fringe_poly_yd = sketch.diagonal_band_polygon(
        left_edge - FRINGE_WIDTH_YD, right_edge + FRINGE_WIDTH_YD,
        lambda x, g: sketch.model._front_edge_yd(x, g) - FRINGE_WIDTH_YD,
        lambda x, g: sketch.model._back_edge_yd(x, g) + FRINGE_WIDTH_YD,
        geom, n=20,
    )
    fringe_mask_full = masks_mod._rasterize(sketch._proj_pts(fringe_poly_yd, project), CANVAS)
    fringe_mask = masks_mod._subtract(fringe_mask_full, masks["green"])
    fringe_alpha = mask_to_arr(fringe_mask, feather_px=GREEN_FEATHER_PX)
    fringe_rgb = (turf_mid * 0.55 + GREEN_BRIGHT * 0.45)[None, None, :] * stripe_mult[..., None]
    base = composite_rgb(base, fringe_rgb, fringe_alpha)

    green_stripe_mult = stripe_multiplier(y_yd, STRIPE_YD_GREEN, STRIPE_CONTRAST_GREEN * stripe_boost, row_fade=green_row_fade)
    green_rgb = GREEN_BRIGHT[None, None, :] * green_stripe_mult[..., None]
    green_alpha = mask_to_arr(masks["green"], feather_px=GREEN_FEATHER_PX)
    base = composite_rgb(base, green_rgb, green_alpha)

    # ---- relief cues: bunker lips, green rim/shadow, creek banks ----
    front_edge_samples_yd = sketch._sample_edge(left_edge, right_edge, sketch.model._front_edge_yd, geom, n=20)
    back_edge_samples_yd = sketch._sample_edge(left_edge, right_edge, sketch.model._back_edge_yd, geom, n=20)
    front_edge_px = [project(x, y) for x, y in front_edge_samples_yd]
    back_edge_px = [project(x, y) for x, y in back_edge_samples_yd]
    left_side_yd = [(left_edge, y) for y in np.linspace(
        sketch.model._front_edge_yd(left_edge, geom), sketch.model._back_edge_yd(left_edge, geom), 10)]
    left_side_px = [project(x, y) for x, y in left_side_yd]

    fb_lo, fb_hi = landmarks["front_bunker_x_range"]
    front_bunker_far_px = [project(x, sketch.model._front_edge_yd(x, geom))
                            for x in np.linspace(fb_lo, fb_hi, 12)]
    base = draw_soft_line(base, front_bunker_far_px, SAND_LIP, 150, width=6, blur=1.6)
    for bb in landmarks["back_bunkers"]:
        bb_lo, bb_hi = bb["x_range"]

        def _far_y(x, g=geom):
            return sketch.model._back_edge_yd(x, g) + sketch.data.HOLE["back_bunker_depth_yd"]

        pts = [project(x, _far_y(x)) for x in np.linspace(bb_lo, bb_hi, 10)]
        base = draw_soft_line(base, pts, SAND_LIP, 150, width=5, blur=1.4)

    # Green: soft shadow along back edge and the screen-left edge (x = -half
    # width, per sketch.py's own "positive x = right/Sunday side" convention
    # -- so the -half-width edge is the one on the left of the frame), plus
    # a thin lighter rim traced along every green boundary.
    base = draw_soft_line(base, back_edge_px, GREEN_SHADOW, 64, width=8, blur=4)
    base = draw_soft_line(base, left_side_px, GREEN_SHADOW, 55, width=7, blur=4)
    for pts in (front_edge_px, back_edge_px, left_side_px):
        base = draw_soft_line(base, pts, GREEN_RIM, 130, width=2, blur=1.0)

    # Creek: darker near-bank shadow, then the crisp cream far-bank line last
    # (it sits on the same curve as the green's front edge and the front
    # bunker's far edge for part of its length, so it must be drawn on top
    # to stay legible -- same ordering constraint round three documented).
    creek_far_bank_px = [project(x, y) for x, y in landmarks["creek_far_bank_samples_yd"]]
    creek_near_bank_px = [project(x, y) for x, y in landmarks["creek_near_bank_samples_yd"]]
    base = draw_soft_line(base, creek_near_bank_px, BANK_NEAR_SHADOW, 150, width=6, blur=3)
    base = draw_soft_line(base, creek_far_bank_px, BANK_FAR_LINE, 235, width=2, blur=0.6)

    return Image.fromarray(np.clip(base, 0, 255).astype("uint8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "ground_debug.png"))
    ap.add_argument("--variant", default="a")
    args = ap.parse_args()

    regions, landmarks = sketch.build_scene()
    project = sketch.make_projector(landmarks["y_break_yd"])
    img = render(regions, landmarks, project, variant=args.variant)
    img.save(args.out)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
