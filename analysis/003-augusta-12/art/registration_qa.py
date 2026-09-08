"""Registration QA for release 003's hero art candidates (issue #11).

RETIRED (2026-09-08, issue #16): this script measures a candidate against
sketch.py's stencil-camera coordinates (sketch_coords.json), the camera
every round used through round five. Round six replaced that pipeline with
a TPS camera fitted directly to the accepted painting (fit_tps.py), and the
registration record for hero.png as shipped is that fit's own leave-one-out
residual table, not this script's color-threshold check against a sketch
the art is no longer asked to match. Kept in the repo for the historical
record of rounds one through five (see art/README.md); do not run this
against hero.png as a release gate. See art/README.md's "registration_qa.py
is retired" note and "Round six, camera correction" for the current record.

For each candidate in hero_candidates/:
1. Builds an overlay PNG: the sketch blended at reduced opacity on top of the
   candidate, resized to the candidate's resolution, so a human can eyeball
   whether hazard boundaries line up.
2. Runs a localized, color-threshold measurement of three high-contrast
   landmark types the sketch also encodes exactly: the three pin flags
   (white), the creek band (blue) at several lateral sample columns, and the
   three bunker centroids (tan/sand). Each measurement searches a window
   around the sketch's own recorded pixel position (sketch_coords.json,
   scaled to the candidate's resolution) rather than scanning the whole
   frame, then reports the offset between the sketch's position and the
   nearest matching color cluster, in pixels and as a percentage of image
   width (the ticket's stated tolerance unit).

This is a best-effort automated check on top of visual judgment, not a
replacement for it -- painterly illustration doesn't threshold as cleanly as
a flat-fill sketch. Both the measurement and a visual verdict are recorded in
art/README.md.
"""
import glob
import json
import pathlib

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).parent
TOLERANCE_PCT = 5.0  # "a few percent of image width" per issue #11


def load_coords():
    return json.loads((HERE / "sketch_coords.json").read_text())


def scale_factor(candidate_size, sketch_canvas):
    return candidate_size[0] / sketch_canvas["width"]


def make_overlay(sketch_img, candidate_img, opacity=0.4):
    sketch_resized = sketch_img.resize(candidate_img.size).convert("RGBA")
    base = candidate_img.convert("RGBA")
    sketch_resized.putalpha(int(255 * opacity))
    return Image.alpha_composite(base, sketch_resized).convert("RGB")


def _window_mask(arr, cx, cy, half, pred):
    h, w = arr.shape[:2]
    x0, x1 = max(0, int(cx - half)), min(w, int(cx + half))
    y0, y1 = max(0, int(cy - half)), min(h, int(cy + half))
    region = arr[y0:y1, x0:x1]
    if region.size == 0:
        return None
    mask = pred(region)
    if not mask.any():
        return None
    ys, xs = np.nonzero(mask)
    return (x0 + xs.mean(), y0 + ys.mean(), mask.sum())


def is_whiteish(region):
    r, g, b = region[..., 0].astype(int), region[..., 1].astype(int), region[..., 2].astype(int)
    bright = (r > 215) & (g > 215) & (b > 200)
    low_sat = (np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)) < 35
    return bright & low_sat


def is_blueish(region):
    r, g, b = region[..., 0].astype(int), region[..., 1].astype(int), region[..., 2].astype(int)
    return (b > r + 10) & (b > 70) & (b >= g - 10)


def is_sandy(region):
    r, g, b = region[..., 0].astype(int), region[..., 1].astype(int), region[..., 2].astype(int)
    return (r > 170) & (g > 130) & (r > b + 35) & (g > b + 5)


def measure_candidate(candidate_path, coords, sketch_img):
    candidate = Image.open(candidate_path).convert("RGB")
    arr = np.asarray(candidate)
    sf = scale_factor(candidate.size, coords["canvas"])
    win = max(candidate.size) * 0.12  # search window half-width, px

    results = {"points": [], "pass": True}

    def record(label, expected_px, pred, win_override=None):
        ex, ey = expected_px[0] * sf, expected_px[1] * sf
        found = _window_mask(arr, ex, ey, win_override or win, pred)
        if found is None:
            results["points"].append({"label": label, "expected_px": [ex, ey], "found": False})
            results["pass"] = False
            return
        fx, fy, weight = found
        offset_px = float(((fx - ex) ** 2 + (fy - ey) ** 2) ** 0.5)
        offset_pct = 100.0 * offset_px / candidate.size[0]
        ok = bool(offset_pct <= TOLERANCE_PCT)
        results["points"].append({
            "label": label, "expected_px": [round(ex, 1), round(ey, 1)],
            "found_px": [round(float(fx), 1), round(float(fy), 1)],
            "offset_px": round(offset_px, 1), "offset_pct_width": round(offset_pct, 2),
            "pass": ok,
        })
        if not ok:
            results["pass"] = False

    # Pins sit close together (as near as ~65px apart at this canvas size),
    # closer than the general 12%-of-width search window -- a wide window
    # risks centroiding onto a neighboring pin's flag instead of its own.
    # Flags also fly ~35-45px above their recorded base point by design (the
    # pennant is at the top of the pole), so the window still needs to
    # reach that far up, just not sideways into the next pin.
    pin_win = 40
    for key, p in coords["pins"].items():
        record(f"pin:{key}", (p["x_px"], p["y_px"]), is_whiteish, win_override=pin_win)

    # Consecutive creek-bank samples sit ~45-55px apart along one diagonal
    # line -- a window wider than that gap lets every sample's search snap
    # onto whichever spot along the whole line is bluest, rather than its
    # own local point.
    creek_win = 24
    for i, s in enumerate(coords["creek"]["far_bank_samples"]):
        record(f"creek_far_bank:{i}", (s["x_px"], s["y_px"]), is_blueish, win_override=creek_win)

    # Bunkers are elongated bands, not circles -- a wide window can pull the
    # detected sandy centroid toward whichever end has more sand pixels
    # rather than the polygon's true geometric centroid.
    bunker_win = 55
    fb = coords["bunkers"]["front"]["centroid_px"]
    record("bunker:front", (fb["x_px"], fb["y_px"]), is_sandy, win_override=bunker_win)
    for i, b in enumerate(coords["bunkers"]["back"]):
        c = b["centroid_px"]
        record(f"bunker:back_{i}", (c["x_px"], c["y_px"]), is_sandy, win_override=bunker_win)

    overlay = make_overlay(sketch_img, candidate)
    overlay_path = candidate_path.parent / f"{candidate_path.stem}_overlay.png"
    overlay.save(overlay_path)
    results["overlay_path"] = str(overlay_path.relative_to(HERE))
    results["candidate_size"] = list(candidate.size)
    results["scale_factor_vs_sketch"] = round(sf, 4)
    results["tolerance_pct_width"] = TOLERANCE_PCT
    n = len(results["points"])
    n_pass = sum(1 for p in results["points"] if p.get("pass"))
    results["summary"] = f"{n_pass}/{n} landmarks within {TOLERANCE_PCT}% of image width"
    return results


def main():
    import sys
    coords = load_coords()
    sketch_img = Image.open(HERE / "sketch.png")
    report = {}

    if len(sys.argv) > 1:
        # Explicit target(s), e.g. `python3 registration_qa.py hero.png` --
        # used to re-check the stencil composite, which lives outside
        # hero_candidates/.
        paths = [HERE / a for a in sys.argv[1:]]
        out = HERE / "registration_report_hero.json"
    else:
        paths = sorted(pathlib.Path(p) for p in glob.glob(str(HERE / "hero_candidates" / "*.png")))
        paths = [p for p in paths if not p.stem.endswith("_overlay")]
        out = HERE / "hero_candidates" / "registration_report.json"

    for p in paths:
        print(f"measuring {p.name} ...")
        report[p.name] = measure_candidate(p, coords, sketch_img)
        print(f"  {report[p.name]['summary']} -> overall {'PASS' if report[p.name]['pass'] else 'FAIL'}")

    out.write_text(json.dumps(report, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
