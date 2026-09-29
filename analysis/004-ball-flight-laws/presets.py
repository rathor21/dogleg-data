"""Player presets for release 004: a club delivery per club and player.

    preset(club, player) -> dict(club_speed, attack, dyn_loft, path=0, face=0, spin_trim, ...)

player is "pga", "lpga" or "amateur". Club ids match data.py.

  pga, lpga   club speed and attack angle from the TrackMan 2023 tables
              (Anchors 1 and 2). Dynamic loft is derived: launch.tour_dyn_loft
              inverts the launch model so path 0 and face 0 reproduce the
              table's launch angle. Only the driver and 6 iron loft are
              published, and the derivation is checked against them.
  amateur     Driver: TrackMan Combine, average golfer (14.5), measured.
              6 iron and PW: TrackMan Optimizer defaults for the average male
              golfer, which are TrackMan model defaults and NOT measurements.
              Every other club is MODELED: club speed, attack angle and dynamic
              loft interpolate between the anchored clubs (driver, 6 iron, PW),
              placed by where the PGA Tour value for that club falls between
              the PGA values of the two anchor clubs.

Each preset also carries spin_trim, a MODELED multiplier for deliver(...,
spin_trim=). It is the published spin over the model's spin at the preset
delivery (path 0, face 0), so the "ideal" preset reproduces its published row.
It stands for where on the face each player group strikes the ball, which the
published averages include and the model does not. It stays fixed as sliders
move, so the model supplies only the response to delivery changes. Amateur
clubs between the anchors interpolate the trim by club speed.

LPGA has no 3 iron. preset("3i", "lpga") returns the 4 iron and says so in
"note" and "club".
"""

import data
import launch

CLUBS = tuple(data.PGA)  # driver, 3w, 5w, hybrid, 3i, 4i, 5i, 6i, 7i, 8i, 9i, pw
PLAYERS = ("pga", "lpga", "amateur")
_ANCHOR_ORDER = ("driver", "6i", "pw")


def _pga_values(club):
    r = data.PGA[club]
    return {"club_speed": r["club_speed_mph"], "attack": r["attack_deg"], "dyn_loft": launch.tour_dyn_loft("PGA", club)}


def _model_spin(club, vals):
    """Model spin (trim 1) at a preset delivery: path 0, face 0."""
    ln = launch.deliver(vals["club_speed"], vals["attack"], 0.0, 0.0, vals["dyn_loft"], club)
    return ln.spin_rpm


def _amateur(club):
    """(values, source, modeled) for one club. values includes spin_trim."""
    anchors = data.AMATEUR_ANCHORS
    if club in anchors:
        a = anchors[club]
        vals = {"club_speed": float(a["club_speed_mph"]), "attack": a["attack_deg"], "dyn_loft": a["dyn_loft_deg"]}
        vals["spin_trim"] = a["spin_rpm"] / _model_spin(club, vals)
        return vals, a["source"], club != "driver"
    idx = CLUBS.index(club)
    lo = max((c for c in _ANCHOR_ORDER if CLUBS.index(c) < idx), key=CLUBS.index)
    hi = min((c for c in _ANCHOR_ORDER if CLUBS.index(c) > idx), key=CLUBS.index)
    p_lo, p_hi, p_c = _pga_values(lo), _pga_values(hi), _pga_values(club)
    a_lo, a_hi = anchors[lo], anchors[hi]
    amateur = {
        "club_speed": (a_lo["club_speed_mph"], a_hi["club_speed_mph"]),
        "attack": (a_lo["attack_deg"], a_hi["attack_deg"]),
        "dyn_loft": (a_lo["dyn_loft_deg"], a_hi["dyn_loft_deg"]),
    }
    vals = {}
    for key, (v0, v1) in amateur.items():
        t = (p_c[key] - p_lo[key]) / (p_hi[key] - p_lo[key])
        vals[key] = v0 + t * (v1 - v0)
    t_speed = (p_c["club_speed"] - p_lo["club_speed"]) / (p_hi["club_speed"] - p_lo["club_speed"])
    trims = [_amateur(c)[0]["spin_trim"] for c in (lo, hi)]
    vals["spin_trim"] = trims[0] + t_speed * (trims[1] - trims[0])
    return vals, f"MODELED: between amateur {lo} and {hi}, PGA shape", True


def preset(club, player):
    if player not in PLAYERS:
        raise ValueError(f"player must be one of {PLAYERS}, got {player!r}")
    if club not in data.PGA:
        raise ValueError(f"unknown club {club!r}")
    note = ""
    used = club
    if player == "lpga" and club not in data.LPGA:
        used = "4i"
        note = "LPGA table has no 3-iron; 4-iron values used"
    if player == "amateur":
        vals, source, modeled = _amateur(used)
    else:
        tour = "PGA" if player == "pga" else "LPGA"
        r = data.TOURS[tour][used]
        vals = {
            "club_speed": float(r["club_speed_mph"]),
            "attack": r["attack_deg"],
            "dyn_loft": launch.tour_dyn_loft(tour, used),
        }
        vals["spin_trim"] = r["spin_rpm"] / _model_spin(used, vals)
        source = f"TrackMan 2023 {tour} table; dynamic loft derived by the launch model"
        modeled = False
    return dict(
        club_speed=vals["club_speed"],
        attack=vals["attack"],
        dyn_loft=vals["dyn_loft"],
        path=0.0,
        face=0.0,
        spin_trim=vals["spin_trim"],
        club=used,
        source=source,
        modeled=modeled,
        note=note,
    )


def scale_speed(p, club_speed):
    """Copy of a preset with only the club speed changed. The spin trim stays."""
    out = dict(p)
    out["club_speed"] = float(club_speed)
    return out
