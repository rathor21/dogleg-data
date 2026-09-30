"""Delivery to launch for release 004: club delivery in, ball launch out.

    deliver(club_speed_mph, attack_deg, path_deg, face_deg, dyn_loft_deg,
            club=None, *, params=None, spin_trim=1.0) -> Launch

feeds flight.simulate(ball_speed_mph, launch_deg, launch_dir_deg, spin_rpm,
spin_axis_deg). Everything here is a MODELED approximation of the D-plane,
fitted to the published tables (see data.LAUNCH_MODEL and calibrate_launch.py).

This module is the JS port surface: deliver, its helpers, swing_path and
Launch. Fitting and table-building helpers live in launch_tools.py.

Frame and signs (TrackMan, right-handed golfer): x downrange, y right, z up.
Angles are positive right, positive path is in-to-out, positive face is open to
the target, face-to-path = face - path, positive spin axis curves the ball right.

Model:
  0. Face-to-loft coupling. The dynamic loft argument is the loft with the face
     square to the path. The effective dynamic loft, the loft TrackMan would
     measure, is
         dyn_loft_effective = dyn_loft + kappa(club) * (face - path),
     kappa = cot(lie angle) per club (data.KAPPA, data.LIE_DEG). Closing the face
     to the path removes loft and opening it adds loft. MODELED: it reads the
     face change as a rotation of the head about the shaft, which leans at the
     lie angle, with no shaft lean and no yaw of the whole club (a pure yaw
     gives kappa 0), so it is the upper end of what the geometry allows. Every
     step below uses the effective loft. At face = path the two lofts are equal.
     A club that is not named has kappa 0. The effective loft is held to at least
     max(attack + data.DOMAIN["min_spin_loft_deg"], data.DOMAIN["min_effective_loft_deg"])
     and at most the domain's largest dynamic loft (clamp_loft).
  1. Club direction d from path and attack angle. Face normal n from face angle
     and effective dynamic loft (azimuth = face, elevation = effective dynamic
     loft). Spin loft is the 3D angle between d and n. It equals dynamic loft
     minus attack angle when path, face and their difference are all zero.
  2. Launch vector u = normalize((1 - k) d + k n), with k linear in spin loft
     (one line for the driver, one for every other club).
     Launch angle and launch direction both come from u. u lies in the plane of d
     and n, so that plane is the D-plane and its normal is the spin axis.
  3. Smash factor and spin rate are functions of spin loft (and ball speed).
     The driver has its own spin law, the 3-wood and 5-wood a factor on the
     iron law.
  4. Spin axis is the tilt of the D-plane normal times c(spin loft), linear. The
     scale is calibrated so face-to-path maps to TrackMan's published
     curvature (see calibrate_launch.py and ADR 0004).

Input contract. deliver raises ValueError, naming the argument, on a non-finite
value, a value outside data.DOMAIN, dynamic loft minus attack angle under
data.DOMAIN["min_spin_loft_deg"], a spin_trim that is not positive, or a club
that is not None or a key of data.PGA. Outputs never carry a negative zero.
"""

from dataclasses import dataclass
from math import atan2, cos, degrees, isfinite, radians, sin, sqrt, tan

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
    dyn_loft_input_deg: float  # the argument: loft with the face square to the path
    dyn_loft_deg: float  # effective loft after the face-to-loft coupling, as TrackMan would measure it


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


def _angle_between(a, b):
    """Angle between two vectors in degrees, from atan2 of |a x b| and a . b."""
    return degrees(atan2(_norm(_cross(a, b)), _dot(a, b)))


def _no_negative_zero(x):
    return x + 0.0  # -0.0 + 0.0 is 0.0


def coupling_kappa(club=None):
    """Loft change per degree of (face - path): cot(lie angle) for a named club, 0 otherwise."""
    return data.KAPPA.get(club, 0.0)


def clamp_loft(dyn_loft_deg, attack_deg):
    """The one clamp on an effective dynamic loft: at least attack + data.DOMAIN
    ["min_spin_loft_deg"] (the D-plane needs a spin loft) and at least
    data.DOMAIN["min_effective_loft_deg"] (never a negative loft), at most the
    domain's largest dynamic loft."""
    low = max(attack_deg + data.DOMAIN["min_spin_loft_deg"], data.DOMAIN["min_effective_loft_deg"])
    return min(max(dyn_loft_deg, low), data.DOMAIN["dyn_loft_deg"][1])


def effective_loft(dyn_loft_deg, path_deg, face_deg, attack_deg, club=None):
    """Effective dynamic loft: dyn_loft + kappa(club) * (face - path), through clamp_loft."""
    return clamp_loft(dyn_loft_deg + coupling_kappa(club) * (face_deg - path_deg), attack_deg)


def club_direction(path_deg, attack_deg):
    p, a = radians(path_deg), radians(attack_deg)
    return (cos(a) * cos(p), cos(a) * sin(p), sin(a))


def face_normal(face_deg, dyn_loft_deg):
    f, l = radians(face_deg), radians(dyn_loft_deg)
    return (cos(l) * cos(f), cos(l) * sin(f), sin(l))


def blend(d, n, k):
    """Unit vector along (1 - k) d + k n."""
    return _unit((
        (1.0 - k) * d[0] + k * n[0],
        (1.0 - k) * d[1] + k * n[1],
        (1.0 - k) * d[2] + k * n[2],
    ))


def spin_loft_deg(path_deg, attack_deg, face_deg, dyn_loft_deg):
    """3D angle between the club direction and the face normal, degrees."""
    return _angle_between(club_direction(path_deg, attack_deg), face_normal(face_deg, dyn_loft_deg))


# ---------------------------------------------------------------------------
# The fitted pieces. `params` is a dict shaped like data.LAUNCH_MODEL, so
# calibrate_launch.py can fit them before they are pasted into data.py.
# ---------------------------------------------------------------------------


def _params(params):
    return data.LAUNCH_MODEL if params is None else params


def k_of(sl, club=None, *, params=None):
    """Weight of the face normal in the launch vector. Linear in spin loft and
    held flat outside the spin loft range it was fitted on. The driver has its
    own line and range (fitted to the TrackMan 2010 chart and the published
    driver rows, down to spin loft 6.3); every other club uses the line fitted
    to the four published triples (12.7 to 25.9)."""
    m = _params(params)
    if SPIN_CLASS.get(club) == "driver":
        s = min(max(sl, m["k_sl_lo_driver"]), m["k_sl_hi_driver"])
        return m["k0_driver"] + m["k1_driver"] * s
    s = min(max(sl, m["k_sl_lo"]), m["k_sl_hi"])
    return m["k0"] + m["k1"] * s


def smash_of(sl, params=None):
    """Quadratic in spin loft, capped at the largest published smash and floored
    at the fit's value at spin loft 45 (a quadratic keeps falling past the last
    fitted row, and nothing supports that)."""
    m = _params(params)
    s = max(sl, 0.0)
    raw = m["smash_a"] + m["smash_b"] * s + m["smash_c"] * s * s
    return max(min(raw, m["smash_cap"]), m["smash_floor"])


SPIN_CLASS = {"driver": "driver", "3w": "wood", "5w": "wood"}  # every other club is an iron class


def spin_of(ball_speed_mph, sl, club=None, *, params=None):
    """Spin rate from ball speed and spin loft. The driver has its own power law
    (spin_a_driver, spin_b_driver), fitted to the TrackMan 2010 chart and the
    published driver rows. The 3-wood and 5-wood take the iron law times
    spin_f_wood. Hybrids, irons, wedges and an unnamed club take the iron law."""
    m = _params(params)
    s = max(sl, 0.0)
    cls = SPIN_CLASS.get(club)
    if cls == "driver":
        return m["spin_a_driver"] * ball_speed_mph * s ** m["spin_b_driver"]
    factor = 1.0 if cls is None else m["spin_f_" + cls]
    return factor * m["spin_a"] * ball_speed_mph * s ** m["spin_b"]


def axis_scale(sl, params=None):
    """Scale on the D-plane tilt: axis_c0 + axis_c1 * spin loft, held flat outside
    the spin loft range of the eight curvature examples it was calibrated on
    (axis_sl_lo to axis_sl_hi)."""
    m = _params(params)
    s = min(max(sl, m["axis_sl_lo"]), m["axis_sl_hi"])
    return m["axis_c0"] + m["axis_c1"] * s


def dplane_tilt_deg(d, n):
    """Tilt of the D-plane normal about the launch direction, degrees, positive
    curves right. d is the club direction and n the face normal. With small
    angles this is atan2(face - path, dyn loft - attack)."""
    m = _cross(d, n)
    if _norm(m) < 1e-9:
        return 0.0
    # Any u in the plane of d and n is perpendicular to m, so use d + n to get
    # the reference axes without depending on k.
    u = _unit((d[0] + n[0], d[1] + n[1], d[2] + n[2]))
    right = _unit(_cross((0.0, 0.0, 1.0), u))  # horizontal, to the right of travel
    up = _cross(u, right)  # the up direction seen from the ball, perpendicular to u
    m_right = _dot(m, right)
    m_up = _dot(m, up)
    # Orient the normal to the backspin side, breaking an exact tie toward +90.
    if m_right < 0.0 or (m_right == 0.0 and m_up > 0.0):
        m_right = -m_right
        m_up = -m_up
    return degrees(atan2(-m_up, m_right))


def launch_vector(path_deg, attack_deg, face_deg, dyn_loft_deg, club=None, *, params=None):
    """(launch angle deg, launch direction deg, spin loft deg). No input checks:
    the fitters and launch_tools call this outside the domain."""
    d = club_direction(path_deg, attack_deg)
    n = face_normal(face_deg, effective_loft(dyn_loft_deg, path_deg, face_deg, attack_deg, club))
    sl = _angle_between(d, n)
    u = blend(d, n, k_of(sl, club, params=params))
    return degrees(atan2(u[2], sqrt(u[0] * u[0] + u[1] * u[1]))), degrees(atan2(u[1], u[0])), sl


# ---------------------------------------------------------------------------
# Input contract
# ---------------------------------------------------------------------------


def _check_range(name, value, key):
    if not isfinite(value):
        raise ValueError(f"{name} must be finite, got {value!r}")
    lo, hi = data.DOMAIN[key]
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be within {lo:g} to {hi:g}, got {value!r}")


def check_club(club):
    if club is not None and club not in data.PGA:
        raise ValueError(f"club must be None or one of {tuple(data.PGA)}, got {club!r}")


def check_delivery(club_speed_mph, attack_deg, path_deg, face_deg, dyn_loft_deg, club=None, spin_trim=1.0):
    """Raise ValueError, naming the argument, for anything deliver rejects."""
    _check_range("club_speed_mph", club_speed_mph, "club_speed_mph")
    _check_range("attack_deg", attack_deg, "attack_deg")
    _check_range("path_deg", path_deg, "path_deg")
    _check_range("face_deg", face_deg, "face_deg")
    _check_range("dyn_loft_deg", dyn_loft_deg, "dyn_loft_deg")
    floor = data.DOMAIN["min_spin_loft_deg"]
    if dyn_loft_deg - attack_deg < floor:
        raise ValueError(
            f"dyn_loft_deg - attack_deg must be at least {floor:g} deg, got {dyn_loft_deg - attack_deg:g}"
        )
    if not isfinite(spin_trim) or spin_trim <= 0.0:
        raise ValueError(f"spin_trim must be finite and positive, got {spin_trim!r}")
    check_club(club)


def deliver(club_speed_mph, attack_deg, path_deg, face_deg, dyn_loft_deg, club=None, *, params=None, spin_trim=1.0):
    """Club delivery to launch conditions. `club` picks the spin class factor
    (driver, fairway woods, everything else) and the coupling kappa. `dyn_loft_deg`
    is the input loft, the loft with the face square to the path, and the Launch
    returns both it and the effective loft. `spin_trim` multiplies spin_rpm
    and nothing else: a preset-level correction (presets.preset returns one)
    that stands for where on the face a player group strikes the ball."""
    check_delivery(club_speed_mph, attack_deg, path_deg, face_deg, dyn_loft_deg, club, spin_trim)
    m = _params(params)
    dl_eff = effective_loft(dyn_loft_deg, path_deg, face_deg, attack_deg, club)
    d = club_direction(path_deg, attack_deg)
    n = face_normal(face_deg, dl_eff)
    sl = _angle_between(d, n)
    u = blend(d, n, k_of(sl, club, params=m))
    launch_deg = degrees(atan2(u[2], sqrt(u[0] * u[0] + u[1] * u[1])))
    launch_dir = degrees(atan2(u[1], u[0]))
    smash = smash_of(sl, m)
    ball = smash * club_speed_mph
    spin = spin_of(ball, sl, club, params=m) * spin_trim
    axis = axis_scale(sl, m) * dplane_tilt_deg(d, n)
    return Launch(
        ball_speed_mph=_no_negative_zero(ball),
        smash=_no_negative_zero(smash),
        launch_deg=_no_negative_zero(launch_deg),
        launch_dir_deg=_no_negative_zero(launch_dir),
        spin_rpm=_no_negative_zero(spin),
        spin_axis_deg=_no_negative_zero(axis),
        spin_loft_deg=_no_negative_zero(sl),
        face_to_path_deg=_no_negative_zero(face_deg - path_deg),
        dyn_loft_input_deg=_no_negative_zero(dyn_loft_deg),
        dyn_loft_deg=_no_negative_zero(dl_eff),
    )


def swing_path(swing_dir_deg, attack_deg, plane_deg=None):
    """Club path with the swing direction held: CP = HSP - AA * tan(90 - VSP).

    FORUM FORMULA (Anchor 5(c) Source 2, Brian Manzella Golf forum, poster
    cwdlaw223, 2011), not TrackMan's. TrackMan says only that vertical swing
    plane, swing direction and attack angle combine to give path. Hitting down
    (AA < 0) moves path right, the same direction TrackMan's statement implies.
    plane_deg defaults to the Combine average golfer's driver swing plane
    (data.SWING_PLANE_DEG) and must lie inside data.DOMAIN["swing_plane_deg"], ends excluded.
    """
    plane = data.SWING_PLANE_DEG if plane_deg is None else plane_deg
    for name, value in (("swing_dir_deg", swing_dir_deg), ("attack_deg", attack_deg), ("plane_deg", plane)):
        if not isfinite(value):
            raise ValueError(f"{name} must be finite, got {value!r}")
    lo, hi = data.DOMAIN["swing_plane_deg"]
    if not lo < plane < hi:
        raise ValueError(f"plane_deg must be between {lo:g} and {hi:g} (exclusive), got {plane!r}")
    return _no_negative_zero(swing_dir_deg - attack_deg * tan(radians(90.0 - plane)))
