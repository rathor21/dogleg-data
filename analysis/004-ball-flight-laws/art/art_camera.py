"""Art camera: a 2.5D mapping fitted to the painting's own ground (numpy only).

The pinhole fit (fit_camera.py) squeezes 50 to 300 yd into about 20 px because
the painting is not perspective-consistent. This module fits the model to the art
instead: the ground rows of the painted greens, the painted center line and the
ball pixel decide the mapping.

MAPPING (world yards: x downrange, y right, z up)
-------------------------------------------------
    x   <- max(x, 0)                                   (no mapping behind the ball)
    row(x)   = h + (r0 - h) / (1 + x/d0)**p             ground row of the target line
    s(x)     = (row(x) - h) / z_eff                     px per yd, used for y and z
    t(x)     = (r0 - row(x)) / (r0 - h)                 0 at the ball, 1 at the vanishing row
    u_vp(x)  = u0 + (uh - u0) * t                       straight line from the ball pixel
                                                        (u0, r0) to the vanishing point (uh, h)
    u = u_vp(x) + y * s(x)
    v = row(x) - z * s(x)

r0 is the ball pixel row (mat center) and (u0, r0) is the ball pixel. h is the
ground's own vanishing row (free), d0 and p shape the depth compression, z_eff is
the vertical scale in yards (a bigger z_eff makes heights smaller on screen).

FIT
---
h, d0, p are solved by least squares on the painted green rows against their
assigned yardages (the yardages are chosen, this is a fictional range).
z_eff is chosen in art_overlay.py against real flight.py trajectories.

Usage:
    python art_camera.py landmarks_art.json art_camera_final.json
"""
import json
import sys

import numpy as np


class ArtCamera:
    def __init__(self, r0, u0, h, uh, d0, p, z_eff, width=None, height=None):
        self.r0, self.u0, self.h, self.uh = float(r0), float(u0), float(h), float(uh)
        self.d0, self.p, self.z_eff = float(d0), float(p), float(z_eff)
        self.width, self.height = width, height

    def row(self, x):
        x = np.maximum(np.asarray(x, float), 0.0)
        return self.h + (self.r0 - self.h) / (1.0 + x / self.d0) ** self.p

    def scale(self, x):
        return (self.row(x) - self.h) / self.z_eff

    def u_vp(self, x):
        t = (self.r0 - self.row(x)) / (self.r0 - self.h)
        return self.u0 + (self.uh - self.u0) * t

    def project(self, x, y=0.0, z=0.0):
        """World (x, y, z) in yards to pixel (u, v). Accepts scalars or arrays."""
        x, y, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float),
                                      np.asarray(z, float))
        row = self.row(x)
        s = (row - self.h) / self.z_eff
        t = (self.r0 - row) / (self.r0 - self.h)
        u = self.u0 + (self.uh - self.u0) * t + y * s
        v = row - z * s
        return u, v

    def ground_from_row(self, v):
        """Inverse of row(x): downrange yards at a ground pixel row (v > h)."""
        v = np.asarray(v, float)
        return self.d0 * (((self.r0 - self.h) / (v - self.h)) ** (1.0 / self.p) - 1.0)

    def ground_from_pixel(self, u, v):
        x = self.ground_from_row(v)
        s = self.scale(x)
        y = (u - self.u_vp(x)) / s
        return x, y

    def params(self):
        return dict(r0=self.r0, u0=self.u0, h=self.h, uh=self.uh, d0=self.d0, p=self.p,
                    z_eff=self.z_eff)

    @classmethod
    def from_json(cls, path):
        d = json.load(open(path))
        q = d["params"]
        return cls(q["r0"], q["u0"], q["h"], q["uh"], q["d0"], q["p"], q["z_eff"],
                   d.get("width"), d.get("height"))


def fit_row_curve(r0, xs, rows, h_grid, d0_grid=None, far=None):
    """Fit h, d0, p to (yardage, row) anchors. The ball (x=0, row r0) is exact.

    For each h, ln((r0 - h)/(row - h)) = p * ln(1 + x/d0). Grid over h and d0 (vectorized),
    p by linear least squares in log space. Returns (h, d0, p, rms_px).
    """
    xs = np.asarray(xs, float)
    rows = np.asarray(rows, float)
    hg = np.asarray(h_grid, float)
    dg = np.geomspace(2.0, 400.0, 200) if d0_grid is None else np.asarray(d0_grid, float)
    H, D = np.meshgrid(hg, dg, indexing="ij")            # (nh, nd)
    ok = np.all(rows[None, :] > hg[:, None] + 0.3, axis=1)
    lhs = np.log((r0 - hg[:, None]) / np.maximum(rows[None, :] - hg[:, None], 1e-6))  # (nh, n)
    basis = np.log1p(xs[None, None, :] / dg[None, :, None])                           # (1, nd, n)
    p = (basis * lhs[:, None, :]).sum(2) / (basis * basis).sum(2)                     # (nh, nd)
    pred = H[..., None] + (r0 - H[..., None]) / (1 + xs[None, None, :] / D[..., None]) ** p[..., None]
    rms = np.sqrt(np.mean((pred - rows[None, None, :]) ** 2, axis=2))
    bad = (~ok)[:, None] | (p < 0.2) | (p > 6.0)
    if far is not None:
        rf = H + (r0 - H) / (1 + far[0] / D) ** p
        bad = bad | (rf < far[1])
    rms = np.where(bad, np.inf, rms)
    i, j = np.unravel_index(np.argmin(rms), rms.shape)
    if not np.isfinite(rms[i, j]):
        return None
    return float(hg[i]), float(dg[j]), float(p[i, j]), float(rms[i, j])


def main():
    lm = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    z_eff = lm.get("z_eff")
    xs = [g["yardage"] for g in lm["greens"] if g.get("use_row", True)]
    rows = [g["center"][1] for g in lm["greens"] if g.get("use_row", True)]
    h, d0, p, rms = fit_row_curve(lm["ball"][1], xs, rows,
                                  np.arange(lm.get("h_min", 250), lm.get("h_max", 312), 0.5))
    cam = ArtCamera(lm["ball"][1], lm["ball"][0], h, lm["vp_col"], d0, p, z_eff,
                    lm["width"], lm["height"])
    print(json.dumps(cam.params()), "row rms", round(rms, 2))


if __name__ == "__main__":
    main()
