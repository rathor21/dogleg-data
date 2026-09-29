"""TrackMan 2010 and PING 2019 driver chart lookups, and optimal_loft.

Bilinear interpolation over the two published driver optimizer tables, clamped
to each table's range. Shared by ideals.py (driver launch and spin bands) and
presets.py (the driver's ideal delivery). Ported to flight.js as bracket,
bilinear, trackmanCarry2010, ping2019 and optimalLoft.

    TrackMan Carry Optimizer (2010), club speed 75 to 120 by attack angle -5, 0, +5.
    PING Optimal Launch & Spin (2019), ball speed 80 to 180 by attack angle -10 to +10.

optimal_loft is the dynamic loft column of the TrackMan carry chart. Club speed
clamps to 75 to 120 mph. Attack angle outside -5 to +5 extrapolates with the
edge slope (the loft change per degree between the two nearest chart rows), and
the result says so.
"""

from math import isfinite
from typing import NamedTuple

import data

_TRACKMAN_SPEEDS = sorted({int(r[0]) for r in data.TRACKMAN_CARRY_2010})
_TRACKMAN_AOAS = sorted({int(r[1]) for r in data.TRACKMAN_CARRY_2010})
_TRACKMAN = {(r[0], r[1]): r for r in data.TRACKMAN_CARRY_2010}
_PING_SPEEDS = sorted(data.PING_2019)
_PING_AOAS = list(data.PING_2019_AOA_DEG)
_LOFT_INDEX = 7  # dynamic loft column of TRACKMAN_CARRY_2010


def bracket(grid, x):
    """(lower index, upper index, fraction) of x in a sorted grid, clamped to its range."""
    if x <= grid[0]:
        return 0, 0, 0.0
    if x >= grid[-1]:
        return len(grid) - 1, len(grid) - 1, 0.0
    hi = next(i for i, g in enumerate(grid) if g >= x)
    lo = hi - 1
    return lo, hi, (x - grid[lo]) / (grid[hi] - grid[lo])


def bilinear(row_grid, col_grid, cell, row, col):
    """cell(i, j) -> (a, b). Bilinear in both, clamped. Returns (a, b)."""
    r0, r1, fr = bracket(row_grid, row)
    c0, c1, fc = bracket(col_grid, col)
    out = []
    for k in (0, 1):
        top = cell(r0, c0)[k] * (1 - fc) + cell(r0, c1)[k] * fc
        bot = cell(r1, c0)[k] * (1 - fc) + cell(r1, c1)[k] * fc
        out.append(top * (1 - fr) + bot * fr)
    return out[0], out[1]


def trackman_carry_2010(club_speed_mph, attack_deg):
    """(launch deg, spin rpm) from the TrackMan 2010 CARRY Optimizer."""
    def cell(i, j):
        r = _TRACKMAN[(_TRACKMAN_SPEEDS[i], _TRACKMAN_AOAS[j])]
        return r[3], r[4]
    return bilinear(_TRACKMAN_SPEEDS, _TRACKMAN_AOAS, cell, club_speed_mph, attack_deg)


def ping_2019(ball_speed_mph, attack_deg):
    """(launch deg, spin rpm) from the PING 2019 Optimal Launch & Spin chart."""
    def cell(i, j):
        return data.PING_2019[_PING_SPEEDS[i]][j]
    return bilinear(_PING_SPEEDS, _PING_AOAS, cell, ball_speed_mph, attack_deg)


class OptimalLoft(NamedTuple):
    dyn_loft_deg: float
    extrapolated: bool  # attack outside the chart's -5 to +5, edge slope used
    speed_clamped: bool  # club speed outside 75 to 120 mph, edge row used


def optimal_loft(club_speed_mph, attack_deg):
    """Dynamic loft from the TrackMan 2010 CARRY chart, bilinear over club speed
    (75 to 120, clamped) and attack angle (-5, 0, +5). Outside -5 to +5 the loft
    extrapolates along the edge slope and `extrapolated` is True. Raises
    ValueError for a non-finite input."""
    for name, v in (("club_speed_mph", club_speed_mph), ("attack_deg", attack_deg)):
        if not isfinite(v):
            raise ValueError(f"{name} must be finite, got {v!r}")
    s0, s1, fs = bracket(_TRACKMAN_SPEEDS, club_speed_mph)
    loft = []  # loft at attack -5, 0, +5 for this club speed
    for a in _TRACKMAN_AOAS:
        lo = _TRACKMAN[(_TRACKMAN_SPEEDS[s0], a)][_LOFT_INDEX]
        hi = _TRACKMAN[(_TRACKMAN_SPEEDS[s1], a)][_LOFT_INDEX]
        loft.append(lo * (1 - fs) + hi * fs)
    a_lo, a_mid, a_hi = _TRACKMAN_AOAS
    speed_clamped = club_speed_mph < _TRACKMAN_SPEEDS[0] or club_speed_mph > _TRACKMAN_SPEEDS[-1]
    if attack_deg > a_hi:
        slope = (loft[2] - loft[1]) / (a_hi - a_mid)
        return OptimalLoft(loft[2] + slope * (attack_deg - a_hi), True, speed_clamped)
    if attack_deg < a_lo:
        slope = (loft[1] - loft[0]) / (a_mid - a_lo)
        return OptimalLoft(loft[0] + slope * (attack_deg - a_lo), True, speed_clamped)
    if attack_deg <= a_mid:
        t = (attack_deg - a_lo) / (a_mid - a_lo)
        return OptimalLoft(loft[0] * (1 - t) + loft[1] * t, False, speed_clamped)
    t = (attack_deg - a_mid) / (a_hi - a_mid)
    return OptimalLoft(loft[1] * (1 - t) + loft[2] * t, False, speed_clamped)
