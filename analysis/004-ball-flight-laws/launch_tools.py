"""Fitting and table-building helpers for launch.py (not part of the JS port).

derive_dyn_loft inverts the launch model. The shipped tour table of default
dynamic lofts (data.TOUR_DYN_LOFT) comes from it, built by
`calibrate_launch.py --write-tour-dyn-loft`.
"""

from math import cos, radians

import data
import launch


def derive_dyn_loft(launch_deg, attack_deg, club=None, *, params=None):
    """Dynamic loft that makes path = face = 0 launch at `launch_deg` for the
    given attack angle, by bisection on the launch vector model. The search
    runs from attack angle plus the domain's spin loft floor up to the domain's
    largest dynamic loft, and raises ValueError if the launch angle is outside
    what that range reaches."""
    lo_dl = attack_deg + data.DOMAIN["min_spin_loft_deg"]
    hi_dl = data.DOMAIN["dyn_loft_deg"][1]

    def gap(dl):
        return launch.launch_vector(0.0, attack_deg, 0.0, dl, club, params=params)[0] - launch_deg

    if gap(lo_dl) > 0.0 or gap(hi_dl) < 0.0:
        raise ValueError(
            f"launch angle {launch_deg!r} deg is not reachable with attack angle {attack_deg!r} deg "
            f"and dynamic loft between {lo_dl:g} and {hi_dl:g} deg"
        )
    for _ in range(80):
        mid = 0.5 * (lo_dl + hi_dl)
        if gap(mid) < 0.0:
            lo_dl = mid
        else:
            hi_dl = mid
    return 0.5 * (lo_dl + hi_dl)


def horizontal_face_share(attack_deg, dyn_loft_deg, club=None, *, params=None):
    """Weight of the face angle in launch direction for a small face-to-path,
    k cos(L) / ((1 - k) cos(A) + k cos(L)). Compare with the unverified
    85 / 75 and 87 / 81 shares in Anchor 5(a); this is model output, not a fit
    to them."""
    k = launch.k_of(dyn_loft_deg - attack_deg, club, params=params)
    cos_loft, cos_attack = cos(radians(dyn_loft_deg)), cos(radians(attack_deg))
    return k * cos_loft / ((1.0 - k) * cos_attack + k * cos_loft)
