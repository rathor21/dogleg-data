"""Choose the art camera against real flights, write the JSON and draw the overlay.

Usage (from the release folder, with the release venv so flight.py imports):
    .venv/bin/python art/art_overlay.py art/landmarks_art.json art/art_camera_final.json art/range_final_art_overlay.jpg
    .venv/bin/python art/art_overlay.py art/landmarks_art_mobile.json art/art_camera_final_mobile.json art/range_final_mobile_art_overlay.jpg

Steps
-----
1. Assign target yardages to the painted greens (5 yd grid, inside each green's allowed
   range, ordered by ground row) and fit h, d0, p to the green rows with the ball at
   row r0. A hard floor keeps the 300 yd ground row on painted fairway.
2. Sweep z_eff. For each candidate simulate the flights from flight.py (PGA driver,
   7-iron, PW straight, 7-iron 12 yd draw and fade, plus a driver tuned to carry 300 yd)
   and require: every apex inside the frame with the margin (check 1), landings on
   fairway below the tree base (checks 3 and 4).
3. Rank the passing candidates by how close the painted green widths fall to 10 to 25 yd.
4. Check 2 (driver arc height). If it fails at the chosen z_eff, build a zoom rectangle
   per club group so the arc reads at least 120 px tall on screen.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import data  # noqa: E402
import flight  # noqa: E402
from art_camera import ArtCamera, fit_row_curve  # noqa: E402

MARGIN_PX = 30
ARC_MIN_PX = 120
WIDTH_LO, WIDTH_HI = 10.0, 25.0

FORMULA = [
    "x <- max(x, 0)",
    "row(x) = h + (r0 - h) / (1 + x/d0)^p",
    "s(x) = (row(x) - h) / z_eff            (px per yd, for y and z)",
    "t(x) = (r0 - row(x)) / (r0 - h)",
    "u_vp(x) = u0 + (uh - u0) * t(x)        (straight line from the ball pixel to the vanishing point)",
    "u = u_vp(x) + y * s(x)",
    "v = row(x) - z * s(x)",
]

# club groups for the per-group views. Each entry is a list of (club, axis, launch_dir) shots.
GROUPS = {
    "wedge": ["pw"],
    "short_iron": ["9i", "8i", "7i", "7i_draw", "7i_fade"],
    "long_iron": ["4i", "5i"],
    "woods": ["3w", "5w"],
    "driver": ["driver", "driver_300"],
}


def shot(club, axis=0.0, tour="PGA"):
    r = data.TOURS[tour][club]
    return flight.simulate(r["ball_speed_mph"], r["launch_deg"], 0.0, r["spin_rpm"], axis)


def side_shot(club, side):
    lo, hi = -30.0, 30.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if shot(club, mid).side_yd < side:
            lo = mid
        else:
            hi = mid
    return shot(club, (lo + hi) / 2), (lo + hi) / 2


def long_drive(carry=300.0):
    r = data.PGA["driver"]
    lo, hi = 150.0, 230.0
    for _ in range(35):
        m = (lo + hi) / 2
        f = flight.simulate(m, r["launch_deg"], 0.0, r["spin_rpm"], 0.0)
        if f.carry_yd < carry:
            lo = m
        else:
            hi = m
    return f, m


def build_flights():
    fl = {}
    for c in ("driver", "3w", "5w", "4i", "5i", "7i", "8i", "9i", "pw"):
        fl[c] = shot(c)
    fl["7i_draw"], ax_d = side_shot("7i", -12.0)
    fl["7i_fade"], ax_f = side_shot("7i", 12.0)
    fl["driver_300"], speed = long_drive(300.0)
    meta = dict(draw_axis_deg=round(ax_d, 2), fade_axis_deg=round(ax_f, 2),
                driver_300_ball_speed_mph=round(speed, 1))
    return fl, meta


HEADLINE = ("driver", "7i", "pw", "7i_draw", "7i_fade")


def path_px(cam, f):
    u, v = cam.project(f.x, f.y, f.z)
    return u, v


def evaluate(cam, fl, W, H, tree_base, land_margin):
    """Checks 1, 3, 4 and the driver arc numbers for the full frame."""
    out = {}
    tops = {k: float(path_px(cam, f)[1].min()) for k, f in fl.items()}
    lands = {k: float(cam.project(f.x[-1], f.y[-1], 0.0)[1]) for k, f in fl.items()}
    out["top_row"] = tops
    out["land_row"] = lands
    out["min_top_headline"] = min(tops[k] for k in HEADLINE)
    out["min_top_all"] = min(tops.values())
    out["min_land_all"] = min(lands.values())
    out["row_300"] = float(cam.row(300.0))
    d = fl["driver"]
    u, v = path_px(cam, d)
    out["driver_top_row"] = float(v.min())
    out["driver_land_row"] = float(v[-1])
    out["driver_apex_to_land_px"] = float(v[-1] - v.min())
    out["driver_extent_px"] = float(v.max() - v.min())
    out["driver_true_apex_row"] = float(cam.project(d.apex_x_yd, 0.0, d.max_height_yd)[1])
    out["check1_apex_margin_ok"] = bool(out["min_top_all"] >= MARGIN_PX)
    out["check2_driver_arc_ok"] = bool(out["driver_apex_to_land_px"] >= ARC_MIN_PX)
    out["check3_landings_ok"] = bool(out["min_land_all"] >= tree_base + land_margin)
    out["check4_300_ok"] = bool(min(lands["driver_300"], out["row_300"]) >= tree_base + land_margin)
    return out


def green_widths(cam, greens, assign):
    res = []
    for g, x in zip(greens, assign):
        s = float(cam.scale(x))
        w = None
        if g.get("left") and g.get("right"):
            w = (g["right"][0] - g["left"][0]) / s
        elif g.get("right"):
            w = None  # clipped by the frame: lower bound only
        res.append(w)
    return res


def choose(lm, fl):
    W, H = lm["width"], lm["height"]
    r0 = lm["ball"][1]
    tb = lm["tree_base_row"]
    lmg = lm.get("land_margin_px", 2)
    greens = sorted(lm["greens"], key=lambda g: -g["center"][1])  # nearest (largest row) first
    rows = [g["center"][1] for g in greens]
    grids = [list(range(g["yard_range"][0], g["yard_range"][1] + 1, 5)) for g in greens]
    import itertools
    cands = []
    for assign in itertools.product(*grids):
        if any(assign[i] > assign[i + 1] for i in range(len(assign) - 1)):
            continue
        r = fit_row_curve(r0, list(assign), rows,
                          np.arange(lm["h_min"], lm["h_max"], 1.0), far=(300.0, tb + lmg))
        if r is None or r[3] > 3.0:
            continue
        cands.append((r, assign))
    best = None
    for (h, d0, p, rms), assign in cands:
        for z_eff in np.arange(4.0, 30.01, 0.25):
            cam = ArtCamera(r0, lm["ball"][0], h, lm["vp_col"], d0, p, z_eff, W, H)
            ev = evaluate(cam, fl, W, H, tb, lmg)
            if not (ev["check1_apex_margin_ok"] and ev["check3_landings_ok"] and ev["check4_300_ok"]):
                continue
            ws = green_widths(cam, greens, assign)
            viol = sum(max(WIDTH_LO - w, w - WIDTH_HI, 0.0) for w in ws if w is not None)
            score = viol + 0.3 * rms + 0.2 * p
            if best is None or score < best[0]:
                best = (score, cam, assign, rms, ev, ws)
    return best, greens


def view_rect(cam, group_flights, W, H, extra_px=None):
    """Largest zoom rectangle (same aspect as the image) that holds the group's flights.

    The rectangle is in full-image pixels. Margin is MARGIN_PX on screen at the top and
    sides, and 25 screen px under the ball. Zoom is capped at 3.
    """
    us, vs = [], []
    for f in group_flights:
        u, v = path_px(cam, f)
        us.append(u)
        vs.append(v)
    u = np.concatenate(us)
    v = np.concatenate(vs)
    bx0, bx1, by0, by1 = float(u.min()), float(u.max()), float(v.min()), float(v.max())
    ball_u, ball_v = cam.u0, cam.r0
    best = None
    for zoom in np.arange(3.0, 0.999, -0.01):
        rw, rh = W / zoom, H / zoom
        top = by0 - MARGIN_PX / zoom
        bottom = top + rh
        need_bottom = max(by1, ball_v) + 25.0 / zoom
        if bottom < need_bottom:
            continue
        if bottom > H:
            top = H - rh
            bottom = H
            if top > by0 - MARGIN_PX / zoom:
                continue
        # horizontal: centre on the center line, then shift to hold the bbox
        left = cam.uh - rw / 2
        left = min(left, bx0 - MARGIN_PX / zoom)
        right = left + rw
        if right < bx1 + MARGIN_PX / zoom:
            left = bx1 + MARGIN_PX / zoom - rw
        left = max(0.0, min(left, W - rw))
        right = left + rw
        if left > bx0 - MARGIN_PX / zoom + 1e-6 or right < bx1 + MARGIN_PX / zoom - 1e-6:
            continue
        if top < -1e-6:
            continue
        best = (zoom, left, top, rw, rh)
        break
    if best is None:
        best = (1.0, 0.0, 0.0, float(W), float(H))
    zoom, left, top, rw, rh = best
    return dict(zoom=round(float(zoom), 3), rect=[round(left, 1), round(top, 1), round(left + rw, 1),
                                                   round(top + rh, 1)])


def draw(cam, lm, fl, greens, assign, out_png, views=None):
    W, H = lm["width"], lm["height"]
    im = Image.open(os.path.join(HERE, lm["image"])).convert("RGB")
    dr = ImageDraw.Draw(im, "RGBA")
    sc = W / 1376.0 if W > H else W / 768.0
    lw = max(2, int(round(2 * sc + 0.5)))
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", max(15, int(20 * sc)))
    small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", max(13, int(16 * sc)))
    for x in (50, 100, 150, 200, 250, 300):
        ys = np.linspace(-30, 30, 61)
        u, v = cam.project(np.full_like(ys, x), ys, np.zeros_like(ys))
        dr.line(list(zip(u, v)), fill=(255, 255, 0, 220), width=lw)
        dr.text((float(u[-1]) + 6, float(v[-1]) - 22), f"{x}", fill=(255, 255, 0, 255), font=font)
    for y in (-20, -10, 10, 20):
        xs = np.linspace(0, 320, 200)
        u, v = cam.project(xs, np.full_like(xs, y), np.zeros_like(xs))
        dr.line(list(zip(u, v)), fill=(0, 255, 255, 150), width=1)
    xs = np.linspace(0, 320, 200)
    u, v = cam.project(xs, 0 * xs, 0 * xs)
    dr.line(list(zip(u, v)), fill=(255, 0, 255, 200), width=1)
    cols = {"driver": (255, 255, 255), "7i": (255, 170, 60), "pw": (120, 200, 255),
            "7i_draw": (90, 255, 130), "7i_fade": (255, 90, 220)}
    for k in HEADLINE:
        f = fl[k]
        u, v = cam.project(f.x, f.y, f.z)
        dr.line(list(zip(u, v)), fill=cols[k] + (255,), width=lw + 1)
        i = int(np.argmin(v))
        dr.ellipse((u[i] - 5, v[i] - 5, u[i] + 5, v[i] + 5), outline=cols[k] + (255,), width=2)
        dr.ellipse((u[-1] - 5, v[-1] - 5, u[-1] + 5, v[-1] + 5), fill=cols[k] + (255,))
    # 300 yd carry driver, dashed by dots
    f = fl["driver_300"]
    u, v = cam.project(f.x, f.y, f.z)
    for a, b in zip(u[::3], v[::3]):
        dr.ellipse((a - 1.5, b - 1.5, a + 1.5, b + 1.5), fill=(255, 255, 255, 200))
    for g, x in zip(greens, assign):
        cu, cv = g["center"]
        dr.ellipse((cu - 8 * sc, cv - 8 * sc, cu + 8 * sc, cv + 8 * sc), outline=(255, 60, 60, 255), width=lw)
        dr.text((cu + 12 * sc, cv - 26 * sc), f"{g['name']} {x} yd", fill=(255, 130, 130, 255), font=font)
    tb = lm["tree_base_row"]
    dr.line((0, tb, W, tb), fill=(255, 128, 0, 200), width=1)
    dr.text((8, tb - 20), "tree base", fill=(255, 160, 0, 255), font=small)
    dr.line((0, MARGIN_PX, W, MARGIN_PX), fill=(255, 0, 0, 160), width=1)
    dr.text((8, MARGIN_PX + 2), f"{MARGIN_PX} px margin", fill=(255, 120, 120, 255), font=small)
    if views:
        for name, vw in views.items():
            l, t, r, b = vw["rect"]
            dr.rectangle((l, t, r, b), outline=(180, 180, 255, 140), width=1)
            dr.text((l + 4, t + 4), name, fill=(190, 190, 255, 255), font=small)
    im.convert("RGB").save(out_png, quality=82)


def main():
    lm_path, out_json, out_png = sys.argv[1:4]
    lm = json.load(open(lm_path))
    W, H = lm["width"], lm["height"]
    fl, meta = build_flights()
    best, greens = choose(lm, fl)
    if best is None:
        sys.exit("no candidate passes checks 1, 3 and 4 with a single z_eff")
    score, cam, assign, rms, ev, ws = best
    views = None
    groups_needed = not ev["check2_driver_arc_ok"]
    if groups_needed:
        views = {}
        for name, clubs in GROUPS.items():
            vw = view_rect(cam, [fl[c] for c in clubs], W, H)
            zoom = vw["zoom"]
            # driver arc on screen for this group's view
            u, v = path_px(cam, fl["driver"])
            vw["clubs"] = clubs
            if name == "driver":
                vw["driver_arc_on_screen_px"] = round(float((v[-1] - v.min()) * zoom), 1)
                l, t, r, b = vw["rect"]
                vw["driver_top_margin_on_screen_px"] = round(float((v.min() - t) * zoom), 1)
            views[name] = vw
    # greens
    gj = []
    for g, x, w in zip(greens, assign, ws):
        s = float(cam.scale(x))
        yy = (g["center"][0] - float(cam.u_vp(x))) / s
        gj.append(dict(name=g["name"], label=g["label"], pixel=g["center"], row=g["center"][1],
                       yardage=int(x), lateral_yd=round(float(yy), 1),
                       width_px=(g["right"][0] - g["left"][0]) if g.get("left") and g.get("right") else None,
                       width_yd=round(float(w), 1) if w is not None else None,
                       width_note=("lower bound only, left edge is outside the frame"
                                   if not g.get("left") else None),
                       row_fit_px=round(float(cam.row(x)), 1),
                       row_error_px=round(float(cam.row(x)) - g["center"][1], 1)))
    ground_table = {str(x): round(float(cam.row(x)), 1) for x in (0, 25, 50, 100, 150, 200, 250, 300)}
    scale_table = {str(x): round(float(cam.scale(x)), 2) for x in (0, 25, 50, 100, 150, 200, 250, 300)}
    out = dict(
        image=lm["image"], width=W, height=H,
        params=dict(cam.params()),
        formula=FORMULA,
        fit=dict(row_rms_px=round(rms, 2), method="grid over h and d0, p by log-space least squares",
                 h_note=("h is set by the painted green rows with a floor that keeps row(300) on fairway. "
                         "The center-line taper and stripe convergence point to a lower vanishing row "
                         "(about 340 to 390 in the wide image) but the far green sits at row 313, "
                         "so h cannot be that low on screen.")),
        tree_base_row=lm["tree_base_row"],
        ground_row_by_yd=ground_table, px_per_yd_by_yd=scale_table,
        greens=gj,
        flights=dict(
            clubs={k: dict(carry_yd=round(f.carry_yd, 1), apex_yd=round(f.max_height_yd, 1),
                           apex_x_yd=round(f.apex_x_yd, 1), side_yd=round(f.side_yd, 1))
                   for k, f in fl.items()}, **meta),
        checks=dict(
            margin_px=MARGIN_PX, arc_min_px=ARC_MIN_PX,
            check1_apex_margin_ok=ev["check1_apex_margin_ok"],
            min_top_row_headline=round(ev["min_top_headline"], 1),
            min_top_row_all_flights=round(ev["min_top_all"], 1),
            top_row_by_flight={k: round(v, 1) for k, v in ev["top_row"].items()},
            check2_driver_arc_ok=ev["check2_driver_arc_ok"],
            driver_top_row=round(ev["driver_top_row"], 1),
            driver_landing_row=round(ev["driver_land_row"], 1),
            driver_apex_to_landing_px=round(ev["driver_apex_to_land_px"], 1),
            driver_extent_ball_to_top_px=round(ev["driver_extent_px"], 1),
            driver_true_apex_row=round(ev["driver_true_apex_row"], 1),
            check3_landings_ok=ev["check3_landings_ok"],
            landing_row_by_flight={k: round(v, 1) for k, v in ev["land_row"].items()},
            check4_300_ok=ev["check4_300_ok"], row_300_yd=round(ev["row_300"], 1),
            driver_300_landing_row=round(ev["land_row"]["driver_300"], 1)),
        per_group_views_needed=bool(groups_needed),
        views=views,
        view_note=("Each view is a zoom rectangle [left, top, right, bottom] in full-image pixels, "
                   "same aspect as the image. The page draws that rectangle scaled to the canvas. "
                   "The mapping itself stays in full-image pixels.") if views else None,
        assumptions=[
            "target yardages for the painted greens are assigned by us (fictional range), 5 yd grid",
            "ball pixel is the mat center on the white center line, no ball is painted",
            "flights are PGA TrackMan averages run through flight.py, straight unless noted",
            "7-iron draw and fade use the spin axis that lands 12 yd left and right of the target line",
            "z_eff is chosen so that checks 1, 3 and 4 hold for every flight in the set",
        ],
    )
    json.dump(out, open(out_json, "w"), indent=1)
    draw(cam, lm, fl, greens, assign, out_png, views)
    print(json.dumps(dict(params=out["params"], assign=list(map(int, assign)), rms=round(rms, 2),
                          checks=out["checks"], widths=[g["width_yd"] for g in gj],
                          views=views), indent=1))


if __name__ == "__main__":
    main()
