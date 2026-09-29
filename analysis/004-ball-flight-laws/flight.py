"""Point-mass golf ball flight for release 004.

Launch conditions in, 3D trajectory out. Plain math and a hand-written RK4 so
the port to JS is line for line. numpy is used only to hand back arrays.

Internal frame (right-handed, SI): x downrange, y LEFT, z up. The public
output flips y so that lateral distance is positive to the RIGHT of the target
line, as seen from behind a right-handed golfer (TrackMan convention).

Forces on the ball (Anchor 7, see data.py):
    gravity, drag along -v, Magnus lift along normalize(omega_hat x v_hat).
    S  = R * omega / |v|                 spin factor, omega is the decayed spin
    CD = cd(S, Re), CL = cl(S, Re)       pluggable Aero model
        shipped: quadratic family (data.QUAD), CD = d0 + d1 S + d2 S^2 + d3 (Re - pivot)
        baseline: Nathan's workbook forms (nathan_model)
    d(omega)/dt = -SPIN_DECAY_COEF * v * omega / R   (tau = R / (2.0e-5 v))

The spin axis is fixed in space at launch (drag torque only shrinks omega).
POSITIVE spin_axis_deg tilts the lift vector to the right, so the ball curves
right (fade or slice for a right-hander).
"""

from dataclasses import dataclass
from typing import Callable
from math import atan, atan2, cos, exp, hypot, pi, radians, sin, sqrt, tan, degrees

import numpy as np

import data


@dataclass(frozen=True)
class Air:
    density: float = data.AIR_DENSITY_KG_M3
    viscosity: float = data.AIR_VISCOSITY_PA_S


STANDARD = Air()


@dataclass
class Flight:
    t: np.ndarray
    x: np.ndarray  # yards downrange
    y: np.ndarray  # yards lateral, positive RIGHT
    z: np.ndarray  # yards up
    carry_yd: float  # downrange distance at landing
    side_yd: float  # lateral distance at landing, positive right
    max_height_yd: float
    apex_x_yd: float
    land_angle_deg: float  # descent angle below horizontal at landing
    flight_time_s: float
    curve_yd: float  # side_yd minus carry * tan(launch_dir)
    land_speed_mph: float
    launch_dir_deg: float = 0.0


def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _unit(a):
    n = sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])
    return (a[0] / n, a[1] / n, a[2] / n)


def _lift_dir_launch(vhat, spin_axis_deg):
    """Lift direction for a spin axis tilted about the velocity vector.

    a0 is the horizontal unit vector to the right of travel (pure backspin
    axis). L0 = a0 x vhat is the lift direction of pure backspin. Tilting by
    theta about vhat swings the lift toward the right: L = cos L0 + sin a0.
    """
    a0 = _unit(_cross(vhat, (0.0, 0.0, 1.0)))
    l0 = _cross(a0, vhat)
    th = radians(spin_axis_deg)
    return (
        cos(th) * l0[0] + sin(th) * a0[0],
        cos(th) * l0[1] + sin(th) * a0[1],
        cos(th) * l0[2] + sin(th) * a0[2],
    )


@dataclass(frozen=True)
class Aero:
    """Coefficient model: cd(S, re) and cl(S, re). S is the spin factor
    R*omega/v; re is the Reynolds number in units of 1e5."""

    name: str
    cd: Callable[[float, float], float]
    cl: Callable[[float, float], float]
    spin_decay: float = data.SPIN_DECAY_COEF  # k in tau = R / (k v), SI


def nathan_model(p=None, name="nathan"):
    """Nathan's workbook forms (Anchor 7 Source 1) with optional multipliers."""
    p = data.NATHAN if p is None else p
    lo, hi = p["re_low"], p["re_high"]
    cdl, cdh, cds = p["cd_low_re"], p["cd_high_re"], p["cd_spin"]
    amp, ex = p["cl_amp"], p["cl_exp"]
    branch, lm, dm = p["re_branch"], p["lift_mult"], p["drag_mult"]

    def cd(spin, re):
        if not branch or re >= hi:
            cd0 = cdh
        elif re <= lo:
            cd0 = cdl
        else:
            cd0 = cdl + (cdh - cdl) * (re - lo) / (hi - lo)
        return (cd0 + cds * spin) * dm

    def cl(spin, re):
        return amp * spin**ex * lm

    return Aero(name, cd, cl)


def quad_model(p=None, name="quad"):
    """Quadratic family (Anchor 7 Source 4 form), parameters from data.QUAD.

    CL = l0 + l1 S + l2 S^2. CD = d0 + d1 S + d2 S^2 + speed term, where the
    speed term is d3 (Re - pivot) for form "linear" or the logistic rise
    d3 / (1 + exp((Re - re0) / w)) for form "logistic". p["k"] optionally sets
    the spin decay coefficient (default: the Anchor 7 value).
    """
    p = data.QUAD if p is None else p
    d0, d1, d2, d3 = p["d0"], p["d1"], p["d2"], p["d3"]
    l0, l1, l2 = p["l0"], p["l1"], p["l2"]
    piv = data.RE_PIVOT
    k = p.get("k", data.SPIN_DECAY_COEF)

    if p.get("form", "linear") == "logistic":
        re0, w = p["re0"], p["w"]

        def cd(spin, re):
            return d0 + d1 * spin + d2 * spin * spin + d3 / (1.0 + exp((re - re0) / w))

    else:

        def cd(spin, re):
            return d0 + d1 * spin + d2 * spin * spin + d3 * (re - piv)

    def cl(spin, re):
        return l0 + l1 * spin + l2 * spin * spin

    return Aero(name, cd, cl, k)


DEFAULT_AERO = quad_model()


def _make_deriv(air, omega_hat, aero):
    m = data.BALL_MASS_KG
    d = data.BALL_DIAMETER_M
    r = data.BALL_RADIUS_M
    area = pi * r * r
    kf = 0.5 * air.density * area / m
    re_per_v = air.density * d / air.viscosity / data.RE_UNIT
    g = data.G
    decay = aero.spin_decay
    cd_fn, cl_fn = aero.cd, aero.cl

    def deriv(s):
        vx, vy, vz, w = s[3], s[4], s[5], s[6]
        v = sqrt(vx * vx + vy * vy + vz * vz)
        spin = r * w / v
        re = re_per_v * v
        cd = cd_fn(spin, re)
        cl = cl_fn(spin, re)
        vh = (vx / v, vy / v, vz / v)
        lx, ly, lz = _unit(_cross(omega_hat, vh))
        ad = kf * cd * v  # drag: -ad * v_vec
        al = kf * cl * v * v  # lift: al * L_hat
        return (
            vx,
            vy,
            vz,
            -ad * vx + al * lx,
            -ad * vy + al * ly,
            -ad * vz + al * lz - g,
            -decay * v * w / r,
        )

    return deriv


def _rk4(deriv, s, dt):
    k1 = deriv(s)
    k2 = deriv([s[i] + 0.5 * dt * k1[i] for i in range(7)])
    k3 = deriv([s[i] + 0.5 * dt * k2[i] for i in range(7)])
    k4 = deriv([s[i] + dt * k3[i] for i in range(7)])
    return [s[i] + dt / 6.0 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) for i in range(7)]


def simulate(
    ball_speed_mph,
    launch_deg,
    launch_dir_deg,
    spin_rpm,
    spin_axis_deg,
    air=STANDARD,
    dt=0.01,
    aero=None,
):
    """Fly one shot. Angles in degrees, spin in rpm, output in yards.

    launch_deg: vertical launch angle. launch_dir_deg: horizontal start
    direction, positive right of the target line. spin_axis_deg: positive
    curves the ball right. aero: an Aero coefficient model (default
    DEFAULT_AERO, the shipped quadratic fit).
    """
    aero = DEFAULT_AERO if aero is None else aero
    v0 = ball_speed_mph * data.MPH_TO_MS
    gam = radians(launch_deg)
    psi = radians(launch_dir_deg)
    vhat = (cos(gam) * cos(psi), -cos(gam) * sin(psi), sin(gam))  # y is left
    lhat = _lift_dir_launch(vhat, spin_axis_deg)
    omega_hat = _cross(vhat, lhat)  # for omega perp v: v x (omega x v) = omega
    w0 = spin_rpm * data.RPM_TO_RADS

    deriv = _make_deriv(air, omega_hat, aero)
    s = [0.0, 0.0, 0.0, v0 * vhat[0], v0 * vhat[1], v0 * vhat[2], w0]
    ts = [0.0]
    states = [s]
    t = 0.0
    max_steps = int(60.0 / dt)
    for _ in range(max_steps):
        s_new = _rk4(deriv, s, dt)
        t_new = t + dt
        if s_new[2] < 0.0:
            f = s[2] / (s[2] - s_new[2])  # linear interpolation to z = 0
            s_land = [s[i] + f * (s_new[i] - s[i]) for i in range(7)]
            ts.append(t + f * dt)
            states.append(s_land)
            break
        ts.append(t_new)
        states.append(s_new)
        s, t = s_new, t_new
    else:
        raise RuntimeError("ball did not land within 60 s")

    m2yd = 1.0 / data.YD_TO_M
    arr = np.array(states)
    x = arr[:, 0] * m2yd
    y = -arr[:, 1] * m2yd  # flip to positive right
    z = arr[:, 2] * m2yd
    z[-1] = 0.0
    tt = np.array(ts)

    land = states[-1]
    vh = hypot(land[3], land[4])
    land_angle = degrees(atan2(-land[5], vh))
    land_speed = sqrt(land[3] ** 2 + land[4] ** 2 + land[5] ** 2) / data.MPH_TO_MS
    i_apex = int(np.argmax(z))
    carry = float(x[-1])
    side = float(y[-1])
    return Flight(
        t=tt,
        x=x,
        y=y,
        z=z,
        carry_yd=carry,
        side_yd=side,
        max_height_yd=float(z[i_apex]),
        apex_x_yd=float(x[i_apex]),
        land_angle_deg=land_angle,
        flight_time_s=float(tt[-1]),
        curve_yd=side - carry * tan(psi),
        land_speed_mph=land_speed,
        launch_dir_deg=launch_dir_deg,
    )


def roll(flight):
    """Total distance in yards: carry plus a simple bounce and roll estimate.

    MODELED. No source covers bounce and roll (log, Gaps item 8). Roll grows
    with landing speed and shrinks fast as the ball comes in steeper:
        roll = ROLL_K * land_speed_mph * cos(land_angle)^ROLL_COS_POWER,
    bounded to [0, ROLL_MAX_YD]. Constants are chosen for a plausible spread
    (driver about 20 to 30 yd, wedge a few yd) and are not fitted to data.
    """
    c = cos(radians(flight.land_angle_deg))
    r = data.ROLL_K * flight.land_speed_mph * c**data.ROLL_COS_POWER
    r = min(max(r, 0.0), data.ROLL_MAX_YD)
    return flight.carry_yd + r
