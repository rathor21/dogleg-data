"""Draw a QA overlay for a fitted camera.

Usage: python overlay_fit.py camera_final.json out.jpg
"""
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from fit_camera import project


def main():
    cam_json, out = sys.argv[1], sys.argv[2]
    d = json.load(open(cam_json))
    cam = dict(f=d["f"], cx=d["cx"], cy=d["cy"], C=tuple(d["cam_pos"]),
               yaw=np.radians(d["yaw_deg"]), pitch=np.radians(d["pitch_deg"]),
               roll=np.radians(d["roll_deg"]))
    im = Image.open(d["image"]).convert("RGB")
    dr = ImageDraw.Draw(im, "RGBA")
    W, H = im.size
    sc = W / 1376.0 if W > H else W / 768.0 * 1.0
    lw = max(2, int(round(2 * sc + 0.5)))
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", max(14, int(18 * sc)))

    def P(x, y, z=0.0):
        u, v, dep = project((x, y, z), cam)
        return (u, v) if dep > 0 else None

    def poly(pts, fill, width):
        pts = [p for p in pts if p is not None]
        if len(pts) > 1:
            dr.line(pts, fill=fill, width=width)

    # ground lines across the fairway at fixed downrange distances
    for x in (50, 100, 150, 200, 250, 300):
        poly([P(x, y) for y in np.linspace(-30, 30, 61)], (255, 255, 0, 230), lw)
        p = P(x, 30)
        if p:
            dr.text((min(p[0] + 6, W - 60), p[1] - 22), f"{x}", fill=(255, 255, 0, 255), font=font)
    # centre line and lateral lines
    poly([P(x, 0) for x in np.linspace(1, 320, 200)], (255, 0, 255, 230), lw)
    for y in (-20, -10, 10, 20):
        poly([P(x, y) for x in np.linspace(2, 320, 200)], (0, 255, 255, 200), max(1, lw - 1))
    # greens back-projected
    for g in d["greens"]:
        if not g.get("ground_yd"):
            continue
        u, v = g["pixel"]
        dr.ellipse((u - 7 * sc - 3, v - 7 * sc - 3, u + 7 * sc + 3, v + 7 * sc + 3),
                   outline=(255, 60, 60, 255), width=lw)
        gx, gy = g["ground_yd"]
        pp = P(gx, gy)
        if pp:
            dr.line((pp[0] - 8, pp[1], pp[0] + 8, pp[1]), fill=(255, 255, 255, 255), width=lw)
            dr.line((pp[0], pp[1] - 8, pp[0], pp[1] + 8), fill=(255, 255, 255, 255), width=lw)
        dr.text((u + 12 * sc, v - 24 * sc), f"{g['name'][0]} {gx:.0f}yd", fill=(255, 120, 120, 255), font=font)
    # sample tracers: driver straight, and 25 yd draw (right to left, so toward -y)
    xs = np.linspace(0, 280, 120)
    z = 35.0 * (1 - ((xs - 165.0) / 165.0) ** 2)
    straight = [P(x, 0.0, zz) for x, zz in zip(xs, z)]
    draw_ = [P(x, -25.0 * (x / 280.0) ** 2, zz) for x, zz in zip(xs, z)]
    poly(straight, (255, 255, 255, 255), lw + 1)
    poly(draw_, (80, 255, 120, 255), lw + 1)
    for pts, col in ((straight, (255, 255, 255)), (draw_, (80, 255, 120))):
        pts = [p for p in pts if p]
        top = min(pts, key=lambda p: p[1])
        dr.ellipse((top[0] - 5, top[1] - 5, top[0] + 5, top[1] + 5), outline=col + (255,), width=2)
    vp = project((1e6, 0, 0), cam)
    dr.line((0, vp[1], W, vp[1]), fill=(255, 128, 0, 200), width=1)
    dr.text((8, vp[1] - 22), "horizon", fill=(255, 160, 0, 255), font=font)
    im.convert("RGB").save(out, quality=82)
    top_v = min(p[1] for p in straight if p)
    print(out, "apex row (straight):", round(top_v, 1), "of", H,
          "| 300yd ground row:", round(P(300, 0)[1], 1), "horizon:", round(vp[1], 1),
          "| draw apex row:", round(min(p[1] for p in draw_ if p), 1),
          "| draw end pixel:", tuple(round(c, 1) for c in draw_[-1]))


if __name__ == "__main__":
    main()
