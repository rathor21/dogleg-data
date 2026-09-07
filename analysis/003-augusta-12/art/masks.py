"""Per-region alpha masks for the stencil/texture-composite hero art
architecture (issue #11, revised architecture).

Reuses sketch.py's own geometry functions and camera (build_scene,
make_projector) so every mask is pixel-identical to sketch.png's regions --
no new geometry, no redrawing. Renders each region at 4x supersample and
downsamples with LANCZOS for anti-aliased edges (PIL's polygon fill has no
native AA).

Masks written to art/masks/, each a single-channel "L" PNG, 1600x900 (the
same canvas as sketch.py), where pixel value = coverage (0..255):

- green.png            the putting surface
- creek.png             the full creek band (far bank = model._front_edge_yd)
- bunker_front.png      the front bunker's sand
- bunker_back_0.png     the first back bunker's sand (x-range order from data.HOLE)
- bunker_back_1.png     the second back bunker's sand
- bunkers.png           union of the three bunker masks (compositing convenience)
- fairway.png           the mown corridor + tee box (fairway/bank grass mask,
                         "fairway" half)
- bank.png              the shaved-bank halo strips around each bunker, with
                         the bunker's own footprint subtracted (fairway/bank
                         grass mask, "bank" half)
- playfield.png         union of every region above (green/creek/bunkers/
                         fairway/bank) -- the hole itself
- environment.png       1 - playfield: everything outside the hole (rough
                         beside the corridor, the backdrop/sky band), where
                         the environment plate shows through unclipped

Usage: python3 masks.py [--out-dir masks]
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sketch  # noqa: E402  (sketch.py itself wires up the parent path for data/model)

from PIL import Image, ImageDraw  # noqa: E402
import numpy as np  # noqa: E402

SUPERSAMPLE = 4


def _rasterize(poly_px, size, fill=255):
    """Anti-aliased single-channel mask for one polygon (px coords, already
    projected). Supersample-then-downsample since PIL's polygon fill has no
    native anti-aliasing."""
    w, h = size
    big = Image.new("L", (w * SUPERSAMPLE, h * SUPERSAMPLE), 0)
    draw = ImageDraw.Draw(big)
    scaled = [(x * SUPERSAMPLE, y * SUPERSAMPLE) for x, y in poly_px]
    draw.polygon(scaled, fill=fill)
    return big.resize((w, h), Image.LANCZOS)


def _union(masks):
    arr = np.zeros(np.asarray(masks[0]).shape, dtype=np.float32)
    for m in masks:
        arr = np.maximum(arr, np.asarray(m, dtype=np.float32))
    return Image.fromarray(arr.astype("uint8"))


def _subtract(a, b):
    """a with b's coverage removed, floored at 0."""
    aa = np.asarray(a, dtype=np.float32)
    bb = np.asarray(b, dtype=np.float32)
    out = np.clip(aa - bb, 0, 255)
    return Image.fromarray(out.astype("uint8"))


def build_masks():
    regions, landmarks = sketch.build_scene()
    project = sketch.make_projector(landmarks["y_break_yd"])
    size = (sketch.CANVAS_W, sketch.CANVAS_H)

    def poly_px(poly_yd):
        return sketch._proj_pts(poly_yd, project)

    masks = {}
    masks["green"] = _rasterize(poly_px(regions["green"]), size)
    masks["creek"] = _rasterize(poly_px(regions["creek"]), size)
    masks["bunker_front"] = _rasterize(poly_px(regions["front_bunker"]), size)

    back_bunker_masks = []
    for i, bb in enumerate(regions["back_bunkers"]):
        m = _rasterize(poly_px(bb["poly"]), size)
        masks[f"bunker_back_{i}"] = m
        back_bunker_masks.append(m)

    all_bunker_masks = [masks["bunker_front"]] + back_bunker_masks
    masks["bunkers"] = _union(all_bunker_masks)

    masks["fairway"] = _union([
        _rasterize(poly_px(regions["fairway"]), size),
        _rasterize(poly_px(regions["tee"]), size),
    ])

    # Bank = shaved-bank halo strips, minus whatever bunker sand sits inside
    # them (the halo polygons are drawn slightly larger than their bunkers
    # on purpose -- see sketch.py's BUNKER_HALO_YD).
    halo_masks = [_rasterize(poly_px(regions["front_bunker_halo"]), size)]
    halo_masks += [_rasterize(poly_px(bb["halo"]), size) for bb in regions["back_bunkers"]]
    bank_union = _union(halo_masks)
    masks["bank"] = _subtract(bank_union, masks["bunkers"])

    masks["playfield"] = _union([
        masks["green"], masks["creek"], masks["bunkers"], masks["fairway"], masks["bank"],
    ])
    env_arr = 255 - np.asarray(masks["playfield"], dtype=np.int16)
    masks["environment"] = Image.fromarray(np.clip(env_arr, 0, 255).astype("uint8"))

    return masks, regions, landmarks, project


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(pathlib.Path(__file__).parent / "masks"))
    args = ap.parse_args()
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    masks, regions, landmarks, project = build_masks()
    for name, img in masks.items():
        path = out_dir / f"{name}.png"
        img.save(path)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
