"""Plate-sky + code-rendered-ground composite for release 003's hero art
(issue #11, round four).

Round two and three pushed nano-banana textures through masks for the whole
picture, ground included. The orchestrator's round-three verdict: the
composited ground still failed on sight -- a blurred green-on-green smear,
a green with no presence, pale smudged bunkers, a thin dark creek stripe.
Two rounds of that approach were enough. Round four keeps nano-banana for
what it demonstrably does well (the strip above the horizon: sky, pine tree
line, azalea beds) and renders the entire ground plane in code instead,
in render_ground.py, in the register of a clean editorial yardage-book
illustration (docs/plans/assets/003-proto-desktop.png).

Pipeline:
1. Load the environment plate (round three's horizon-aligned crop, unchanged
   -- see load_aligned_plate), patch its stray bunkers.
2. Render the ground with render_ground.render() -- flat-ish base colors,
   crisp region edges, and explicit relief cues (rim lines, shadows, a
   waterline, bunker lips, rake lines), all drawn with code from the same
   sketch.build_scene()/masks.build_masks() geometry every round has used.
3. Blend the two: plate above the horizon and for the next
   TRANSITION_PX below it, code-rendered ground beneath that. The plate
   contributes only sky/trees/azaleas now -- its own ground (sculpted,
   dark, blurred) is discarded entirely by this blend.
4. Draw pin flags at the model's exact projected positions (same style as
   every prior round).
5. Save hero.png (1600x900) and hero_mobile_crop.png (a 9:16 center crop).
   Also render hero_variant_b.png, the same pipeline with one deliberate
   ground-render difference (see render_ground.render's variant="b").

Usage: python3 composite.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sketch  # noqa: E402
import render_ground  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

HERE = pathlib.Path(__file__).parent
CANVAS = (sketch.CANVAS_W, sketch.CANVAS_H)

# How far below sketch.py's own camera horizon (HORIZON_PX) the plate-to-
# ground crossfade runs. Above HORIZON_PX the stencil never draws anything
# (masks.py uses this exact same projector), so the plate alone is correct
# there; TRANSITION_PX below it is a soft handoff rather than a seam.
TRANSITION_PX = 40


def build_blend_mask(canvas_size, horizon_px, transition_px):
    """0 = pure plate, 255 = pure ground. A vertical ramp: solid plate above
    horizon_px, solid ground from horizon_px + transition_px down, linear
    in between."""
    w, h = canvas_size
    rows = np.arange(h, dtype=np.float64)
    t = np.clip((rows - horizon_px) / transition_px, 0.0, 1.0)
    row_vals = (t * 255).astype(np.uint8)
    arr = np.repeat(row_vals[:, None], w, axis=1)
    return Image.fromarray(arr, mode="L")


# Round three's environment_plate.png still left three stray sand bunkers in
# the midground (native 1344x768 plate coordinates, before the horizon-
# alignment crop below). Clone-stamp each out with a patch of clean grass
# sampled from directly below it in the same plate. Boxes are specific to
# this plate image; if the plate is regenerated, re-check them.
STRAY_BUNKER_PATCH_BOXES = [
    (95, 185, 495, 272),   # large bunker, left-center
    (545, 165, 700, 225),  # small bunker, center-left
    (665, 160, 845, 225),  # small bunker, center-right
]
STRAY_BUNKER_PATCH_SOURCE_Y_OFFSET = 160  # clean fairway grass this far below each box


def patch_stray_bunkers(plate_img):
    from PIL import ImageFilter
    out = plate_img.copy()
    for box in STRAY_BUNKER_PATCH_BOXES:
        x0, y0, x1, y1 = box
        w, h = x1 - x0, y1 - y0
        src = out.crop((x0, y0 + STRAY_BUNKER_PATCH_SOURCE_Y_OFFSET, x1, y0 + STRAY_BUNKER_PATCH_SOURCE_Y_OFFSET + h))
        patch_mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(patch_mask).ellipse([w * 0.04, h * 0.04, w * 0.96, h * 0.96], fill=255)
        patch_mask = patch_mask.filter(ImageFilter.GaussianBlur(radius=14))
        out.paste(src, (x0, y0), patch_mask)
    return out


# Round three: horizon alignment. sketch.py's camera horizon
# (sketch.HORIZON_PX = 150 of a 900px canvas, 16.7% down) doesn't match the
# plate's own native tree-line placement, so a fixed fraction of pure sky is
# cropped off the plate's top before resizing to the canvas -- see the
# README's "Round three" section for the worked arithmetic. Unchanged this
# round: only the ground below the plate's tree line is being replaced, not
# how the plate itself is aligned.
PLATE_CROP_TOP_FRAC = 0.099


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


def draw_pins(img, project):
    """Same flag style every round has used, at the exact projected
    positions, so pin geometry matches sketch_coords.json exactly. Round
    four: slightly larger pennant and a 1px dark outline on the pole so pins
    stay legible at phone width against the now-brighter green."""
    draw = ImageDraw.Draw(img)
    for key, p in sketch.data.PINS.items():
        px, py = project(p["x"], p["y"])
        stick_h = 50
        draw.ellipse([px - 9, py - 4, px + 9, py + 4], fill=(20, 20, 15, 60))
        draw.line([(px, py), (px, py - stick_h)], fill=(20, 19, 16), width=4)
        draw.polygon(
            [(px, py - stick_h), (px + 21, py - stick_h + 8), (px, py - stick_h + 16)],
            fill=(250, 248, 240), outline=(20, 19, 16), width=1,
        )
        r = 6
        draw.ellipse([px - r, py - r, px + r, py + r], fill=(20, 19, 16))


def build_hero(variant="a"):
    regions, landmarks = sketch.build_scene()
    project = sketch.make_projector(landmarks["y_break_yd"])

    plate = load_aligned_plate(HERE / "environment_plate.png")
    ground = render_ground.render(regions, landmarks, project, variant=variant)

    blend_mask = build_blend_mask(CANVAS, sketch.HORIZON_PX, TRANSITION_PX)
    base = Image.composite(ground, plate, blend_mask)

    draw_pins(base, project)
    return base


def save_outputs(base, hero_name, crop_name=None):
    hero_path = HERE / hero_name
    base.save(hero_path)
    print(f"wrote {hero_path}")

    if crop_name:
        crop_w = round(CANVAS[1] * 9 / 16)
        x0 = (CANVAS[0] - crop_w) // 2
        crop = base.crop((x0, 0, x0 + crop_w, CANVAS[1]))
        crop_path = HERE / crop_name
        crop.save(crop_path)
        print(f"wrote {crop_path}")


def main():
    hero = build_hero(variant="a")
    save_outputs(hero, "hero.png", "hero_mobile_crop.png")

    variant_b = build_hero(variant="b")
    save_outputs(variant_b, "hero_variant_b.png")


if __name__ == "__main__":
    main()
