"""Stencil/texture composite for release 003's hero art (issue #11, revised
architecture).

Geometry is a stencil, not a generation request: masks.py rasterizes the
model's own regions (green, creek, bunkers, fairway/bank) at the exact
sketch.py camera, and this script paints each region with a nano-banana
texture tile, laid over a loosely-generated environment plate (trees,
azaleas, sky -- everything outside the playfield). nano-banana never has to
respect pixel geometry; Pillow enforces it by construction.

Pipeline:
1. Load the environment plate, upscale to the mask canvas (1600x900).
2. Load each texture tile, tile it across the canvas, color-match it toward
   the plate's own lighting/mood (partial mean/contrast transfer, not a full
   hue override -- water stays water-colored, sand stays sand-colored).
3. Composite each textured region onto the plate through its feathered mask,
   in a fixed z-order (fairway/bank -> creek -> bunkers -> green), matching
   sketch.py's own layering.
4. Legibility touches, programmatic: a crisp waterline along the creek's far
   (green-side) bank -- exactly model._front_edge_yd, sampled the same way
   sketch.py samples it, since flight-path arcs will terminate near this
   line in a later ticket; a soft shadow under the green's back edge; a
   light vignette.
5. Pin flags at the model's exact pin positions (same draw code as
   sketch.py), so registration_qa.py has real pin geometry to measure.
6. Save hero.png (1600x900) and a phone-width center crop, hero_mobile_crop.png.

Usage: python3 composite.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sketch  # noqa: E402
import masks as masks_mod  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

HERE = pathlib.Path(__file__).parent
CANVAS = (sketch.CANVAS_W, sketch.CANVAS_H)

# Tile repeat size in YARDS (not px): how many model-yards one texture
# repeat spans, tuned per region so small regions (bunkers) don't read as
# one giant sand dune and large regions (fairway) don't look like confetti.
# Yards, not pixels, is what makes the perspective mapping below correct --
# a repeat fixed in yards naturally gets denser on screen with depth, the
# same way the model's own geometry does.
TILE_REPEAT_YD = {
    "green": 2.5,
    "fairway": 4.5,
    "bank": 3.0,
    "creek": 5.5,
    "bunkers": 2.0,
}

# Per-region tint applied on top of the color-matched tile, so green and
# fairway (which share the same nano-banana "mown grass" tile, per the
# ticket's 4-tile budget) read as visually distinct: green brighter/cooler
# and finer-scaled, fairway a touch duller/warmer.
REGION_TINT = {
    "green": (1.06, 1.10, 1.02),     # slightly brighter, slightly cooler-green
    "fairway": (0.99, 0.99, 0.98),   # round three: nearly untinted, so color-match to the
                                      # plate's own grass (below) does the work instead of a
                                      # tint fighting it
    "bank": (1.0, 1.0, 1.0),
    "creek": (1.02, 1.02, 1.05),      # a touch cooler/deeper, reads as water rather than haze
    "bunkers": (1.10, 1.04, 0.90),    # push warmer and brighter, sand should pop against the green
}

# How much of each tile's own mean color moves toward the plate's overall
# mood (its environment-region mean/std). Grass regions sit close in hue to
# that mood already, so they can move most of the way for coherence; water
# and sand are hue-distinct from a green/brown backdrop, so a big transfer
# would desaturate them toward mud. Contrast (std) always matches more than
# color does -- that's what reads as "same light," without stealing hue.
# Round three: fairway's transfer raised from 0.32 -> 0.58 -- it's now the
# region blending into the plate's own grass rather than a bounded shape, so
# it needs to sit much closer to the plate's own color, not just "coherent."
REGION_MEAN_STRENGTH = {
    "green": 0.32, "fairway": 0.42, "bank": 0.34, "creek": 0.12, "bunkers": 0.15,
}
STD_TRANSFER_CLAMP = (0.75, 1.3)  # how much contrast can be pulled toward the plate

# Round three: per-mask feather radius. Round two used one fixed radius
# (2.5px) for every region, which read fine for small, naturally-crisp
# shapes (green, bunkers, creek) but made the fairway corridor -- a huge
# shape sitting directly on top of the plate's own grass, with no boundary
# feature (no waterline, no sand rim) to justify a hard edge -- look like a
# sticker. Fairway/bank now feather over 60-90px (radius ~28/14, and a
# Gaussian's visible falloff runs 2-3x its radius) so the corridor blends
# into the plate's grass instead of stopping at a drawn line.
FEATHER_RADIUS = {
    "green": 3.0,
    "fairway": 20.0,
    "bank": 12.0,
    "creek": 3.0,
    "bunkers": 4.0,
}

# Round three: how much to flatten the tile's own local contrast (mow-stripe
# darkness, sand ripple depth, ...) before tinting/color-matching, per
# region. Only the fairway needed this -- its stripe contrast read bolder
# than the plate's own grass rendering right at the corridor's edge (see
# round two's "Honest assessment"). 1.0 = untouched.
REGION_CONTRAST_SOFTEN = {
    "fairway": 0.72,
}


def load_mask(name):
    return Image.open(HERE / "masks" / f"{name}.png").convert("L")


def y_yd_for_screen_y(py, y_break):
    """Inverse of sketch.screen_y_for: pixel row -> model y-yards. sketch.py's
    depth budget is 3-segment piecewise-linear, so this inverts each segment
    in turn. Used to texture-map perspective correctly (see
    perspective_texture) instead of tiling at one flat screen scale."""
    py = min(max(py, sketch.HORIZON_PX), sketch.GROUND_NEAR_PX)
    if py >= sketch.TEE_FRONT_PX:
        t = (py - sketch.GROUND_NEAR_PX) / (sketch.TEE_FRONT_PX - sketch.GROUND_NEAR_PX)
        return sketch.Y_MIN_YD + t * (0.0 - sketch.Y_MIN_YD)
    if py >= sketch.MID_PX:
        t = (py - sketch.TEE_FRONT_PX) / (sketch.MID_PX - sketch.TEE_FRONT_PX)
        return t * y_break
    t = (py - sketch.MID_PX) / (sketch.HORIZON_PX - sketch.MID_PX)
    return y_break + t * (sketch.Y_MAX_YD - y_break)


def perspective_texture(tile_img, canvas_size, repeat_yd, y_break):
    """Full inverse-perspective texture map: every output pixel is mapped
    back to model (x_yd, y_yd) through the exact camera sketch.py/masks.py
    use (y_yd_for_screen_y for depth, sketch.half_width_px_for for the
    lateral scale), then that yard position is sampled from the tile modulo
    repeat_yd in both axes.

    This is the fix for a texture that only reads as a flat sticker under a
    naive fixed-px tiling: fixed-px tiling can only ever be right at one
    depth, and for a texture whose main pattern varies along a single axis
    (this project's mow-stripe tile varies row-to-row, not column-to-column)
    a naive per-row width squeeze does nothing at all -- it has to be the
    model's own depth coordinate driving the sample, in both directions, not
    a screen-space approximation of it."""
    w, h = canvas_size
    tile = np.asarray(tile_img.convert("RGB"))
    th, tw = tile.shape[:2]

    y_yd_row = np.array([y_yd_for_screen_y(py, y_break) for py in range(h)])          # (h,)
    px_per_yard_row = np.array([sketch.half_width_px_for(y) for y in y_yd_row]) / sketch.FRAME_HALF_WIDTH_YD  # (h,)

    cx = w / 2.0
    cols = np.arange(w)
    x_yd_grid = (cols[None, :] - cx) / px_per_yard_row[:, None]   # (h, w)
    y_yd_grid = np.repeat(y_yd_row[:, None], w, axis=1)            # (h, w)

    sx = ((x_yd_grid % repeat_yd) / repeat_yd * tw).astype(np.int32) % tw
    sy = ((y_yd_grid % repeat_yd) / repeat_yd * th).astype(np.int32) % th

    out = tile[sy, sx]
    return Image.fromarray(out.astype("uint8"))


def region_mean_std(arr, mask_arr):
    """Per-channel (mean, std) of arr's pixels where mask_arr > 128."""
    sel = mask_arr > 128
    if not sel.any():
        return arr.reshape(-1, 3).mean(axis=0), arr.reshape(-1, 3).std(axis=0)
    pix = arr[sel]
    return pix.mean(axis=0), pix.std(axis=0) + 1e-6


def color_match(tile_arr, target_mean, target_std, tint, mean_strength):
    src_mean = tile_arr.reshape(-1, 3).mean(axis=0)
    src_std = tile_arr.reshape(-1, 3).std(axis=0) + 1e-6
    ratio = np.clip(target_std / src_std, *STD_TRANSFER_CLAMP)
    out = (tile_arr - src_mean) * ratio + src_mean
    out = out + mean_strength * (target_mean - src_mean)
    out = out * np.array(tint)
    return np.clip(out, 0, 255)


def soften_contrast(arr, factor):
    """Flatten arr's local contrast around its own mean by factor (<1 =
    flatter). Applied before tinting/color-matching so a bold tile pattern
    (mow stripes) doesn't out-contrast the plate it's blending into."""
    if factor >= 1.0:
        return arr
    mean = arr.reshape(-1, arr.shape[-1]).mean(axis=0)
    return (arr - mean) * factor + mean


def make_textured_layer(tile_name, region_key, plate_env_mean, plate_env_std, y_break):
    tile_img = Image.open(HERE / "tiles" / f"tile_{tile_name}.png")
    repeat_yd = TILE_REPEAT_YD[region_key]
    tiled = perspective_texture(tile_img, CANVAS, repeat_yd, y_break)
    arr = np.asarray(tiled, dtype=np.float64)
    arr = soften_contrast(arr, REGION_CONTRAST_SOFTEN.get(region_key, 1.0))
    tint = REGION_TINT.get(region_key, (1.0, 1.0, 1.0))
    mean_strength = REGION_MEAN_STRENGTH.get(region_key, 0.25)
    matched = color_match(arr, plate_env_mean, plate_env_std, tint, mean_strength)
    # A light blur softens the tile-repeat seams; this is a stylized painted
    # texture, not a photo, so "seamless-ish" per the ticket is enough.
    img = Image.fromarray(matched.astype("uint8"))
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    return img


def feather(mask_img, radius=2.5):
    return mask_img.filter(ImageFilter.GaussianBlur(radius=radius))


def draw_waterline(base_img, creek_far_bank_px, color=(18, 52, 96)):
    """Crisp darker stroke along the creek's far (green-side) bank -- the
    model's own front_edge_yd line, exactly. A later ticket's flight-path
    arcs terminate near this line, so it must read clearly.

    Round three: the front bunker's x-range (-10 to 2yd) sits directly on
    top of this same curve for part of its length (see sketch.py -- the
    front bunker occupies the front slice of the creek's own depth budget,
    by design), so part of this line is drawn over warm sand, not grass.
    round two's paler, low-alpha teal (35,58,63 at 170/255 core alpha)
    blended toward sand's high red channel read as sandy-brown, not blue,
    and registration_qa.py's creek_far_bank:3 landmark (which sits at
    x=-5yd, deep inside the bunker's span) failed as a result. A deeper,
    more saturated blue at higher alpha reads as water over either
    background -- verified against both the fairway and the bunker's own
    warm sand tone by hand."""
    line_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(line_layer)
    pts = [(x, y) for x, y in creek_far_bank_px]
    draw.line(pts, fill=color + (245,), width=6, joint="curve")
    soft = line_layer.filter(ImageFilter.GaussianBlur(radius=3))
    # Composite: soft glow first, then a slightly crisper core on top.
    base_img.paste(Image.alpha_composite(base_img.convert("RGBA"), soft).convert("RGB"), (0, 0))
    crisp = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    ImageDraw.Draw(crisp).line(pts, fill=color + (235,), width=3, joint="curve")
    base_img.paste(Image.alpha_composite(base_img.convert("RGBA"), crisp).convert("RGB"), (0, 0))


def draw_edge_band(base_img, edge_px, push_py, color, alpha, width, blur):
    """Soft colored band running along a projected edge curve, pushed
    push_py pixels into whichever region the caller wants shaded (positive
    = toward the camera/larger py, negative = away from camera/smaller py).
    Shared by every relief cue below (green shadows/rim, bunker rims, creek
    near-bank shadow) so they all read as the same kind of mark."""
    layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    pts = [(x, y + push_py) for x, y in edge_px]
    draw.line(pts, fill=color + (alpha,), width=width, joint="curve")
    if blur:
        layer = layer.filter(ImageFilter.GaussianBlur(radius=blur))
    base_img.paste(Image.alpha_composite(base_img.convert("RGBA"), layer).convert("RGB"), (0, 0))


def draw_green_shadow(base_img, back_edge_px, color=(30, 40, 22)):
    """Soft shadow just inside the green's back edge, suggesting a slight
    grade change -- a legibility cue, not a geometry change. Pushed +py
    (toward the camera / into the green's own surface), as if the back
    collar's lip casts a shadow forward onto the putting surface."""
    draw_edge_band(base_img, back_edge_px, push_py=6, color=color, alpha=90, width=14, blur=8)


def draw_green_front_shadow(base_img, front_edge_px, color=(28, 36, 20)):
    """Round three: matching shadow along the green's creek-side (front)
    edge, so the green reads as raised on both the back AND the bank facing
    the creek, not just the back. Pushed -py (away from the camera / into
    the green's own surface from its near edge, i.e. toward the back edge)."""
    draw_edge_band(base_img, front_edge_px, push_py=-5, color=color, alpha=80, width=12, blur=7)


def draw_green_rim(base_img, edge_px, color=(232, 226, 205)):
    """Round three: a thin lighter rim line right along a green boundary
    curve, suggesting a mown collar catching light -- cheap but effective
    "raised surface" cue to pair with the shadows above."""
    draw_edge_band(base_img, edge_px, push_py=0, color=color, alpha=110, width=2, blur=1.2)


def draw_bunker_rim_shadow(base_img, far_edge_px, color=(75, 58, 38)):
    """Round three: thin dark rim just inside a bunker's far edge (the edge
    away from the camera -- front_edge for the front bunker, back_edge+depth
    for the back bunkers -- see sketch.py's own bunker geometry), as if the
    grass lip on that side overhangs and shades the sand. Pushed +py (into
    the bunker's own sand from its far edge)."""
    draw_edge_band(base_img, far_edge_px, push_py=5, color=color, alpha=130, width=9, blur=5)


def draw_creek_near_bank_shadow(base_img, near_bank_px, color=(18, 28, 32)):
    """Round three: a softer, darker line along the creek's near (fairway-
    side) bank, pairing with the existing crisp far-bank waterline so the
    creek reads as a channel with two banks, not a flat stripe. Deliberately
    softer/less crisp than the far waterline -- that one has to stay crisp
    for a later ticket's flight-path arcs; this one is a pure legibility cue."""
    draw_edge_band(base_img, near_bank_px, push_py=-4, color=color, alpha=150, width=7, blur=4)


def darken_creek_toward_banks(creek_layer_img, creek_mask_img, strength=0.35, erode_px=15):
    """Round three: 'slightly darker water toward the banks,' so the creek
    reads as a channel with depth instead of a flat-colored band. Erodes the
    creek mask (PIL has no erosion filter, so a single wide MinFilter pass
    approximates one -- MinFilter(k) shrinks a binary-ish mask by about
    k//2 px) to find the interior, then darkens creek_layer_img in the band
    between the eroded interior and the full mask -- i.e. near both banks --
    proportionally to how close to the edge each pixel is."""
    k = erode_px * 2 + 1
    eroded = creek_mask_img.filter(ImageFilter.MinFilter(k))
    mask_arr = np.asarray(creek_mask_img, dtype=np.float64) / 255.0
    eroded_arr = np.asarray(eroded, dtype=np.float64) / 255.0
    edge_band = np.clip(mask_arr - eroded_arr, 0, 1)
    darken = 1.0 - strength * edge_band
    arr = np.asarray(creek_layer_img, dtype=np.float64) * darken[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype("uint8"))


def add_vignette(img, strength=0.22):
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w / 2.0, h / 2.0
    d = np.sqrt(((xx - cx) / (w / 2.0)) ** 2 + ((yy - cy) / (h / 2.0)) ** 2)
    d = np.clip(d, 0, 1.4)
    mult = 1.0 - strength * (d ** 2.2)
    mult = np.clip(mult, 1 - strength, 1.0)
    arr = np.asarray(img, dtype=np.float64) * mult[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype("uint8"))


def draw_pins(img, project):
    """Same flag style as sketch.py, at the exact same projected positions,
    so pin geometry in the composite matches sketch_coords.json exactly."""
    draw = ImageDraw.Draw(img)
    for key, p in sketch.data.PINS.items():
        px, py = project(p["x"], p["y"])
        stick_h = 46
        # soft drop shadow first
        draw.ellipse([px - 9, py - 4, px + 9, py + 4], fill=(20, 20, 15, 60))
        draw.line([(px, py), (px, py - stick_h)], fill=(25, 24, 20), width=3)
        draw.polygon([(px, py - stick_h), (px + 18, py - stick_h + 7), (px, py - stick_h + 14)],
                     fill=(250, 248, 240), outline=(25, 24, 20))
        r = 5
        draw.ellipse([px - r, py - r, px + r, py + r], fill=(25, 24, 20))


# Round three's environment_plate.png (regenerated for the horizon fix, see
# README) is a different image from round two's, generated with the same
# explicit no-hazards prompt; it still left three stray sand bunkers in the
# midground (native 1344x768 plate coordinates, before the horizon-alignment
# crop below) -- the same "competing hole layout" collage risk round two
# hit once. Clone-stamp each out with a patch of clean grass sampled from
# directly below it in the same plate. Boxes are specific to this plate
# image; if the plate is regenerated, re-check them (see plate_candidates/
# in the round-three git history for how these were located).
STRAY_BUNKER_PATCH_BOXES = [
    (95, 185, 495, 272),   # large bunker, left-center
    (545, 165, 700, 225),  # small bunker, center-left
    (665, 160, 845, 225),  # small bunker, center-right
]
STRAY_BUNKER_PATCH_SOURCE_Y_OFFSET = 160  # clean fairway grass this far below each box


def patch_stray_bunkers(plate_img):
    out = plate_img.copy()
    for box in STRAY_BUNKER_PATCH_BOXES:
        x0, y0, x1, y1 = box
        w, h = x1 - x0, y1 - y0
        src = out.crop((x0, y0 + STRAY_BUNKER_PATCH_SOURCE_Y_OFFSET, x1, y0 + STRAY_BUNKER_PATCH_SOURCE_Y_OFFSET + h))
        # Feathered elliptical mask so the clone-stamp blends instead of leaving a hard rectangle.
        patch_mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(patch_mask).ellipse([w * 0.04, h * 0.04, w * 0.96, h * 0.96], fill=255)
        patch_mask = patch_mask.filter(ImageFilter.GaussianBlur(radius=14))
        out.paste(src, (x0, y0), patch_mask)
    return out


# Round three: horizon alignment. sketch.py's camera horizon (the screen y
# its depth projection approaches at its far clamp, Y_MAX_YD) is
# sketch.HORIZON_PX = 150 out of a 900px-tall canvas -- 16.7% down from the
# top. Round two's plate put its tree-line base around 56% down, so the
# green and back bunkers, which the stencil correctly projects up near
# y=150-240, ended up floating in what the plate rendered as open sky. The
# round-three regeneration prompt asked for the tree line confined to the
# top 15% of frame; the winning candidate (see README) still landed its
# tree-line base around row 190 of its native 768px height (24.7%), close
# but not exact. Rather than re-roll for a pixel-perfect match, this crops
# a bit of pure sky off the plate's top before resizing to the canvas: that
# shrinks the *denominator* the tree-line-base row is measured against,
# pushing its effective fraction down to just under HORIZON_PX/900 (see the
# worked arithmetic in the README's "Round three" section). The crop is
# centered horizontally afterward to hold the plate's own 16:9 aspect so
# the final resize to CANVAS is a uniform scale, not a stretch.
PLATE_CROP_TOP_FRAC = 0.099  # fraction of the plate's native height to drop off the top


def load_aligned_plate(path):
    raw = Image.open(path).convert("RGB")
    raw = patch_stray_bunkers(raw)
    sw, sh = raw.size
    crop_top = round(sh * PLATE_CROP_TOP_FRAC)
    cropped_h = sh - crop_top
    target_aspect = CANVAS[0] / CANVAS[1]
    cropped_w = min(sw, round(cropped_h * target_aspect))
    x0 = (sw - cropped_w) // 2
    box = (x0, crop_top, x0 + cropped_w, sh)
    return raw.crop(box).resize(CANVAS, Image.LANCZOS)


def main():
    regions, landmarks = sketch.build_scene()
    project = sketch.make_projector(landmarks["y_break_yd"])
    geom = landmarks["geom"]

    plate = load_aligned_plate(HERE / "environment_plate.png")
    plate_arr = np.asarray(plate, dtype=np.float64)

    env_mask_arr = np.asarray(load_mask("environment"))
    plate_env_mean, plate_env_std = region_mean_std(plate_arr, env_mask_arr)

    base = plate.copy()

    layers = [
        ("fairway", "grass", "fairway"),
        ("bank", "rough", "bank"),
        ("creek", "water", "creek"),
        ("bunkers", "sand", "bunkers"),
        ("green", "grass", "green"),
    ]
    for mask_name, tile_name, region_key in layers:
        raw_mask = load_mask(mask_name)
        mask_img = feather(raw_mask, radius=FEATHER_RADIUS.get(mask_name, 2.5))
        textured = make_textured_layer(tile_name, region_key, plate_env_mean, plate_env_std, landmarks["y_break_yd"])
        if mask_name == "creek":
            # Darken toward both banks before compositing, using the
            # *unfeathered* mask so the erosion below reads the creek's true
            # shape rather than an already-softened edge.
            textured = darken_creek_toward_banks(textured, raw_mask)
        base = Image.composite(textured, base, mask_img)

    # --- Legibility / relief touches (round three adds several of these to
    # make each region read as physical ground rather than a flat fill) ---

    left_edge, right_edge = landmarks["green_left_right_edge_yd"]
    front_edge_samples_yd = sketch._sample_edge(left_edge, right_edge, sketch.model._front_edge_yd, geom, n=16)
    back_edge_samples_yd = sketch._sample_edge(left_edge, right_edge, sketch.model._back_edge_yd, geom, n=16)
    front_edge_px = [project(x, y) for x, y in front_edge_samples_yd]
    back_edge_px = [project(x, y) for x, y in back_edge_samples_yd]

    # Draw order below matters more than usual: the front bunker's far edge,
    # the green's front edge, and the creek's far bank are the *same* curve
    # (model._front_edge_yd) by construction, so whichever of these effects
    # is drawn last wins that curve. The crisp far waterline has a hard
    # requirement (registration_qa.py's creek_far_bank landmarks measure it,
    # and a later ticket's flight-path arcs terminate on it) to stay a
    # legible blue line, so every other edge effect that shares its curve is
    # drawn first and the waterline goes on top, last.

    # Bunkers: a thin rim shadow just inside each bunker's far edge (the
    # side away from the camera), so each reads as a pocket rather than a
    # flat patch. Front bunker's far edge is the green's own front edge;
    # each back bunker's far edge is its outer boundary away from the green.
    fb_lo, fb_hi = landmarks["front_bunker_x_range"]
    front_bunker_far_px = [project(x, sketch.model._front_edge_yd(x, geom))
                            for x in np.linspace(fb_lo, fb_hi, 10)]
    draw_bunker_rim_shadow(base, front_bunker_far_px)
    for bb in landmarks["back_bunkers"]:
        bb_lo, bb_hi = bb["x_range"]

        def _far_y(x, g=geom):
            return sketch.model._back_edge_yd(x, g) + sketch.data.HOLE["back_bunker_depth_yd"]

        back_bunker_far_px = [project(x, _far_y(x)) for x in np.linspace(bb_lo, bb_hi, 8)]
        draw_bunker_rim_shadow(base, back_bunker_far_px)

    # Green: shadows on both the back edge and the creek-side front edge, so
    # it reads as a raised surface all the way around, plus a thin lighter
    # rim tracing both edges (a mown-collar highlight).
    draw_green_front_shadow(base, front_edge_px)
    draw_green_shadow(base, back_edge_px)
    draw_green_rim(base, front_edge_px)
    draw_green_rim(base, back_edge_px)

    # Creek: softer near-bank shadow first, then the crisp far waterline
    # last of all so it stays on top of the front bunker's rim shadow and
    # the green's front rim/shadow wherever they share its curve.
    creek_far_bank_px = [project(x, y) for x, y in landmarks["creek_far_bank_samples_yd"]]
    creek_near_bank_px = [project(x, y) for x, y in landmarks["creek_near_bank_samples_yd"]]
    draw_creek_near_bank_shadow(base, creek_near_bank_px)
    draw_waterline(base, creek_far_bank_px)

    base = add_vignette(base, strength=0.20)
    draw_pins(base, project)

    hero_path = HERE / "hero.png"
    base.save(hero_path)
    print(f"wrote {hero_path}")

    # Phone-width center crop: full canvas height, width = height * 9/16,
    # centered horizontally -- the composition's tee-to-green axis sits on
    # the canvas's horizontal center by construction (sketch.py's camera).
    crop_w = round(CANVAS[1] * 9 / 16)
    x0 = (CANVAS[0] - crop_w) // 2
    crop = base.crop((x0, 0, x0 + crop_w, CANVAS[1]))
    crop_path = HERE / "hero_mobile_crop.png"
    crop.save(crop_path)
    print(f"wrote {crop_path}")


if __name__ == "__main__":
    main()
