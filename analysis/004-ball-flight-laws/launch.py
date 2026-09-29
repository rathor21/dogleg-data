"""Delivery to launch for release 004: club delivery in, ball launch out.

    deliver(club_speed, attack, path, face, dyn_loft, club) -> Launch

feeds flight.simulate(ball_speed_mph, launch_deg, launch_dir_deg, spin_rpm,
spin_axis_deg). Everything here is a MODELED approximation of the D-plane,
fitted to the published tables (see data.LAUNCH_MODEL and calibrate_launch.py).

Frame and signs (TrackMan, right-handed golfer): x downrange, y right, z up.
Angles are positive right, positive path is in-to-out, positive face is open to
the target, face-to-path = face - path, positive spin axis curves the ball right.

Model:
  1. Club direction d from path and attack angle. Face normal n from face angle
     and dynamic loft (azimuth = face, elevation = dynamic loft). Spin loft is
     the 3D angle between d and n. It equals dynamic loft minus attack angle when
     path and face are both zero.
  2. Launch vector u = normalize((1 - k) d + k n), with k linear in spin loft.
     Launch angle and launch direction both come from u. u lies in the plane of d
     and n, so that plane is the D-plane and its normal is the spin axis.
  3. Smash factor and spin rate are functions of spin loft (and ball speed).
  4. Spin axis is the tilt of the D-plane normal times one constant c. The
     constant is calibrated so face-to-path maps to TrackMan's published curvature
     (see calibrate_launch.py and ADR 0004).
"""

from dataclasses import dataclass
from math import atan2, cos, degrees, radians, sin, sqrt, tan

import data


@dataclass(frozen=True)
class Launch:
    ball_speed_mph: float
    smash: float
    launch_deg: float
    launch_dir_deg: float
    spin_rpm: float
    spin_axis_deg: float
    spin_loft_deg: float
    face_to_path_deg: float


# ---------------------------------------------------------------------------
# Vector helpers (plain math so the port to JS is line for line).
# ---------------------------------------------------------------------------


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm(a):
    return sqrt(_dot(a, a))


def _unit(a):
    n = _norm(a)
    return (a[0] / n, a[1] / n, a[2] / n)


def club_direction(path_deg, attack_deg):
    p, a = radians(path_deg), radians(attack_deg)
    return (cos(a) * cos(p), cos(a) * sin(p), sin(a))


def face_normal(face_deg, dyn_loft_deg):
    f, l = radians(face_deg), radians(dyn_loft_deg)
    return (cos(l) * cos(f), cos(l) * sin(f), sin(l))


def spin_loft_deg(path_deg, attack_deg, face_deg, dyn_loft_deg):
    """3D angle between the club direction and the face normal, degrees."""
    d = club_direction(path_deg, attack_deg)
    n = face_normal(face_deg, dyn_loft_deg)
    return degrees(atan2(_norm(_cross(d, n)), _dot(d, n)))


# ---------------------------------------------------------------------------
# The fitted pieces. `p` is a parameter dict shaped like data.LAUNCH_MODEL, so
# calibrate_launch.py can fit them before they are pasted into data.py.
# ---------------------------------------------------------------------------


def k_of(sl, p=None):
    """Weight of the face normal in the launch vector. Linear in spin loft,
    held flat outside the spin loft range of the four fitting points."""
    p = data.LAUNCH_MODEL if p is None else p
    s = min(max(sl, p["k_sl_lo"]), p["k_sl_hi"])
    return p["k0"] + p["k1"] * s


def smash_of(sl, p=None):
    p = data.LAUNCH_MODEL if p is None else p
    s = max(sl, 0.0)
    return min(p["smash_a"] + p["smash_b"] * s + p["smash_c"] * s * s, p["smash_cap"])


def spin_of(ball_speed_mph, sl, p=None):
    p = data.LAUNCH_MODEL if p is None else p
    return p["spin_a"] * ball_speed_mph * max(sl, 0.0) ** p["spin_b"]


def axis_scale(p=None):
    p = data.LAUNCH_MODEL if p is None else p
    return p["axis_c"]


def launch_vector(path_deg, attack_deg, face_deg, dyn_loft_deg, p=None):
    """(launch angle deg, launch direction deg, spin loft deg)."""
    d = club_direction(path_deg, attack_deg)
    n = face_normal(face_deg, dyn_loft_deg)
    sl = degrees(atan2(_norm(_cross(d, n)), _dot(d, n)))
    k = k_of(sl, p)
    u = _unit(tuple((1.0 - k) * d[i] + k * n[i] for i in range(3)))
    return degrees(atan2(u[2], sqrt(u[0] * u[0] + u[1] * u[1]))), degrees(atan2(u[1], u[0])), sl


def dplane_tilt_deg(path_deg, attack_deg, face_deg, dyn_loft_deg):
    """Tilt of the D-plane normal about the launch direction, degrees, positive
    curves right. With small angles this is atan2(face - path, dyn loft - attack)."""
    d = club_direction(path_deg, attack_deg)
    n = face_normal(face_deg, dyn_loft_deg)
    m = _cross(d, n)
    if _norm(m) < 1e-9:
        return 0.0
    # Any u in the plane of d and n is perpendicular to m, so use d + n to get
    # the reference axes without depending on k.
    u = _unit((d[0] + n[0], d[1] + n[1], d[2] + n[2]))
    right = _unit(_cross((0.0, 0.0, 1.0), u))  # horizontal, to the right of travel
    up = _cross(u, right)  # the up direction seen from the ball, perpendicular to u
    if _dot(m, right) < 0.0:
        m = (-m[0], -m[1], -m[2])
    return degrees(atan2(-_dot(m, up), _dot(m, right)))


def deliver(club_speed_mph, attack_deg, path_deg, face_deg, dyn_loft_deg, club=None, p=None):
    """Club delivery to launch conditions. `club` is accepted so callers can
    pass it through; the shipped fit is shared by all clubs (no per-club terms)."""
    p = data.LAUNCH_MODEL if p is None else p
    launch_deg, launch_dir, sl = launch_vector(path_deg, attack_deg, face_deg, dyn_loft_deg, p)
    smash = smash_of(sl, p)
    ball = smash * club_speed_mph
    spin = spin_of(ball, sl, p)
    axis = axis_scale(p) * dplane_tilt_deg(path_deg, attack_deg, face_deg, dyn_loft_deg)
    return Launch(
        ball_speed_mph=ball,
        smash=smash,
        launch_deg=launch_deg,
        launch_dir_deg=launch_dir,
        spin_rpm=spin,
        spin_axis_deg=axis,
        spin_loft_deg=sl,
        face_to_path_deg=face_deg - path_deg,
    )


def horizontal_face_share(attack_deg, dyn_loft_deg, p=None):
    """Weight of the face angle in launch direction for a small face-to-path,
    k cos(L) / ((1 - k) cos(A) + k cos(L)). Compare with the unverified
    85 / 75 and 87 / 81 shares in Anchor 5(a); this is model output, not a fit
    to them."""
    sl = dyn_loft_deg - attack_deg
    k = k_of(sl, p)
    cl, ca = cos(radians(dyn_loft_deg)), cos(radians(attack_deg))
    return k * cl / ((1.0 - k) * ca + k * cl)


def derive_dyn_loft(launch_deg, attack_deg, p=None, hi=80.0):
    """Dynamic loft that makes path = face = 0 launch at `launch_deg` for the
    given attack angle. Bisection on the launch vector model."""
    lo_dl, hi_dl = attack_deg + 0.01, attack_deg + hi

    def g(dl):
        return launch_vector(0.0, attack_deg, 0.0, dl, p)[0] - launch_deg

    if g(lo_dl) > 0.0 or g(hi_dl) < 0.0:
        raise ValueError("launch angle outside the range the model can reach")
    for _ in range(80):
        mid = 0.5 * (lo_dl + hi_dl)
        if g(mid) < 0.0:
            lo_dl = mid
        else:
            hi_dl = mid
    return 0.5 * (lo_dl + hi_dl)


_TOUR_DL_CACHE = {}


def tour_dyn_loft(tour, club):
    """Default dynamic loft for a Tour table row, from derive_dyn_loft with the
    shipped parameters. MODELED (only the driver and 6 iron are published)."""
    key = (tour, club)
    if key not in _TOUR_DL_CACHE:
        r = data.TOURS[tour][club]
        _TOUR_DL_CACHE[key] = derive_dyn_loft(r["launch_deg"], r["attack_deg"])
    return _TOUR_DL_CACHE[key]


def swing_path(swing_dir_deg, attack_deg, plane_deg=None):
    """Club path with the swing direction held: CP = HSP - AA * tan(90 - VSP).

    FORUM FORMULA (Anchor 5(c) Source 2, Brian Manzella Golf forum, poster
    cwdlaw223, 2011), not TrackMan's. TrackMan says only that vertical swing
    plane, swing direction and attack angle combine to give path. Hitting down
    (AA < 0) moves path right, the same direction TrackMan's statement implies.
    plane_deg defaults to the Combine average golfer's driver swing plane
    (data.SWING_PLANE_DEG).
    """
    plane = data.SWING_PLANE_DEG if plane_deg is None else plane_deg
    return swing_dir_deg - attack_deg * tan(radians(90.0 - plane))
