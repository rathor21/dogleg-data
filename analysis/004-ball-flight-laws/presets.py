"""Player presets for release 004: a club delivery per club and player.

    preset(club, player) -> dict(club_speed, attack, dyn_loft, path=0, face=0, spin_trim, ...)

player is "pga", "lpga" or "amateur". Club ids match data.py.

  pga, lpga   club speed and attack angle from the TrackMan 2023 tables
              (Anchors 1 and 2). Dynamic loft is derived: data.TOUR_DYN_LOFT
              holds an inversion of the launch model
              (launch_tools.derive_dyn_loft) so path 0 and face 0 reproduce the
              table's launch angle. Only the driver and 6 iron loft are
              published, and the derivation is checked against them.
  amateur     Driver: TrackMan Combine, average golfer (14.5), measured.
              6 iron and PW: TrackMan Optimizer defaults for the average male
              golfer, which are TrackMan model defaults and NOT measurements.
              Every other club is MODELED: club speed, attack angle and dynamic
              loft interpolate between the anchored clubs (driver, 6 iron, PW),
              placed by where the PGA Tour value for that club falls between
              the PGA values of the two anchor clubs, held to the range between the
              two anchors.

Each preset also carries spin_trim, a MODELED multiplier for deliver(...,
spin_trim=). It is the published spin over the model's spin at the preset
delivery (path 0, face 0), so the "ideal" preset reproduces its published row.
It stands for where on the face each player group strikes the ball, which the
published averages include and the model does not. It stays fixed as sliders
move, so the model supplies only the response to delivery changes. Amateur
clubs between the anchors interpolate the trim by club speed.

LPGA has no 3 iron. preset("3i", "lpga") returns the 4 iron and says so in
"note" and "club".

Ideal delivery. preset()["ideal"] and ideal_delivery(club, player, club_speed)
give the delivery the tool calls ideal. For every club but the driver it is the
preset itself. For the driver it is data.DRIVER_IDEAL: the player's club speed,
attack +5, dynamic loft chart.optimal_loft(speed, 5), the mean of the TrackMan
2010 carry chart and total chart lofts, path 0, face 0, spin trim 1.0 (the chart's own strike, the basis
the flight model is calibrated to). preset()["ideal"] is at the preset club
speed. scale_speed does not move it, so call ideal_delivery(club, player,
speed) for the ideal at another club speed.

Loft follows attack. loft_for_attack(club, player, attack) is the input loft the
lab uses when a student moves the attack angle and the loft moves with it
(data.LOFT_PER_ATTACK, MODELED). The independent path, fly(p, attack=a) with the
preset loft, is unchanged.
"""

from math import exp

import data
import flight
import launch
from chart import optimal_loft

# Explicit ladder, longest club first. LPGA has no 3i.
CLUBS = ("driver", "3w", "5w", "hybrid", "3i", "4i", "5i", "6i", "7i", "8i", "9i", "pw")
PLAYERS = ("pga", "lpga", "amateur")
_ANCHOR_ORDER = ("driver", "6i", "pw")
_TOUR_NAME = {"pga": "PGA", "lpga": "LPGA"}
_KEYS = ("club_speed", "attack", "dyn_loft")


def _pga_values(club):
    r = data.PGA[club]
    return {"club_speed": r["club_speed_mph"], "attack": r["attack_deg"], "dyn_loft": data.TOUR_DYN_LOFT[("PGA", club)]}


def _model_spin(club, vals):
    """Model spin (trim 1) at a preset delivery: path 0, face 0."""
    return launch.deliver(vals["club_speed"], vals["attack"], 0.0, 0.0, vals["dyn_loft"], club).spin_rpm


def _clamp01(t):
    return min(max(t, 0.0), 1.0)


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
    pga = {"lo": _pga_values(lo), "hi": _pga_values(hi), "club": _pga_values(club)}
    amateur_lo, amateur_hi = _amateur(lo)[0], _amateur(hi)[0]
    vals = {}
    for key in _KEYS:
        # Where the PGA value for this club falls between the PGA anchor values,
        # held to [0, 1] so a club never leaves the amateur anchor range.
        t = _clamp01((pga["club"][key] - pga["lo"][key]) / (pga["hi"][key] - pga["lo"][key]))
        vals[key] = amateur_lo[key] + t * (amateur_hi[key] - amateur_lo[key])
        if key == "club_speed":
            t_speed = t
    vals["spin_trim"] = amateur_lo["spin_trim"] + t_speed * (amateur_hi["spin_trim"] - amateur_lo["spin_trim"])
    return vals, f"MODELED: between amateur {lo} and {hi}, PGA shape", True


def preset(club, player):
    if player not in PLAYERS:
        raise ValueError(f"player must be one of {PLAYERS}, got {player!r}")
    if club not in CLUBS:
        raise ValueError(f"club must be one of {CLUBS}, got {club!r}")
    note = ""
    used = club
    if player == "lpga" and club not in data.LPGA:
        used = "4i"
        note = "LPGA table has no 3-iron; 4-iron values used"
    if player == "amateur":
        vals, source, modeled = _amateur(used)
    else:
        tour = _TOUR_NAME[player]
        r = data.TOURS[tour][used]
        vals = {
            "club_speed": float(r["club_speed_mph"]),
            "attack": r["attack_deg"],
            "dyn_loft": data.TOUR_DYN_LOFT[(tour, used)],
        }
        vals["spin_trim"] = r["spin_rpm"] / _model_spin(used, vals)
        source = f"TrackMan 2023 {tour} table; dynamic loft from data.TOUR_DYN_LOFT"
        modeled = False
    out = dict(
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
    out["ideal"] = _ideal(club, player, out, out["club_speed"])
    return out


def _check_speed(club_speed):
    lo, hi = data.DOMAIN["club_speed_mph"]
    if not (club_speed == club_speed and lo <= club_speed <= hi):  # NaN fails both
        raise ValueError(f"club_speed must be within {lo:g} to {hi:g} mph, got {club_speed!r}")


def _ideal(club, player, p, club_speed):
    """The ideal delivery for a club, player and club speed, given the preset p."""
    if club == "driver":
        d = data.DRIVER_IDEAL
        ol = optimal_loft(club_speed, d["attack_deg"])
        return dict(
            club_speed=float(club_speed), attack=d["attack_deg"], dyn_loft=ol.dyn_loft_deg, path=0.0, face=0.0,
            spin_trim=d["spin_trim"], club="driver", label=d["label"],
            source="TrackMan 2010 Driver Fitting Chart (model output): dynamic loft midway between the CARRY and "
                   f"TOTAL optimizers at this club speed and attack +{d['attack_deg']:g}; spin trim 1.0, the chart's own strike",
            modeled=True, speed_clamped=ol.speed_clamped,
        )
    return dict(
        club_speed=float(club_speed), attack=p["attack"], dyn_loft=p["dyn_loft"], path=0.0, face=0.0,
        spin_trim=p["spin_trim"], club=p["club"], label=p["source"], source=p["source"], modeled=p["modeled"],
        speed_clamped=False,
    )


def ideal_delivery(club, player, club_speed=None):
    """The ideal delivery for a club and player at a club speed (default the
    preset's). Same keys as a preset's `ideal`. Raises ValueError for a speed
    outside data.DOMAIN, or a club or player that does not exist."""
    p = preset(club, player)
    speed = p["club_speed"] if club_speed is None else club_speed
    _check_speed(speed)
    return _ideal(club, player, p, speed)


def _followed_change(raw):
    """Loft change for a raw change of m * (attack - preset attack). Upward (raw >= 0) it is
    the raw change. Downward it follows the slope for the first LOFT_FOLLOW_DELOFT_LINEAR
    degrees of deloft, then rolls off exponentially to LOFT_FOLLOW_DELOFT_MAX (value and
    slope continuous at the join)."""
    if raw >= 0.0:
        return raw
    lin, top = data.LOFT_FOLLOW_DELOFT_LINEAR, data.LOFT_FOLLOW_DELOFT_MAX
    deloft = -raw
    if deloft > lin:
        deloft = lin + (top - lin) * (1.0 - exp(-(deloft - lin) / (top - lin)))
    return -deloft


def loft_for_attack(club, player, attack):
    """Input dynamic loft for a club, player and attack angle when the loft follows
    the attack angle (MODELED, data.LOFT_PER_ATTACK).

    Hybrids, fairway woods, irons and wedges: preset dynamic loft + m * (attack -
    preset attack), m = 1.4 degrees of loft per degree of attack (hitting up adds
    loft and loses compression). Below the preset attack the loft taken off is
    limited: it follows the slope for the first 3 degrees of deloft and rolls off
    to at most 5 (a golfer can only lean the shaft so far, and the slope has
    evidence from attack -6 to +2 only), so a steep attack never turns a wood into
    a putter. The driver keeps the TrackMan 2010 chart's optimal loft at the preset
    club speed and this attack angle (chart.optimal_loft). The result goes through
    launch.clamp_loft, so it is always a loft deliver() accepts. Raises ValueError
    for a club or player that does not exist, or an attack angle that is not finite
    or outside data.DOMAIN. At the preset attack angle a non-driver club returns
    its preset loft."""
    p = preset(club, player)
    lo, hi = data.DOMAIN["attack_deg"]
    if not (attack == attack and lo <= attack <= hi):  # NaN fails both
        raise ValueError(f"attack must be within {lo:g} to {hi:g} deg, got {attack!r}")
    if club == "driver":
        dl = optimal_loft(p["club_speed"], attack).dyn_loft_deg
    else:
        dl = p["dyn_loft"] + _followed_change(data.LOFT_PER_ATTACK * (attack - p["attack"]))
    return launch.clamp_loft(dl, attack)


def scale_speed(preset_dict, club_speed):
    """Copy of a preset with only the club speed changed. The spin trim stays.
    Raises ValueError for a speed outside data.DOMAIN."""
    _check_speed(club_speed)
    out = dict(preset_dict)
    out["club_speed"] = float(club_speed)
    return out


_FLY_KEYS = ("club_speed", "attack", "path", "face", "dyn_loft", "spin_trim")


def fly(preset_dict, **overrides):
    """(Launch, Flight) for a preset delivery: launch.deliver then flight.simulate.

    overrides replace preset keys (club_speed, attack, path, face, dyn_loft,
    spin_trim) for this call only, for example fly(p, path=5.0, face=2.0). An
    unknown key raises ValueError. deliver's input contract applies."""
    unknown = sorted(set(overrides) - set(_FLY_KEYS))
    if unknown:
        raise ValueError(f"unknown override {unknown}, expected some of {_FLY_KEYS}")
    q = dict(preset_dict, **overrides)
    ln = launch.deliver(q["club_speed"], q["attack"], q["path"], q["face"], q["dyn_loft"], q["club"],
                        spin_trim=q["spin_trim"])
    f = flight.simulate(ln.ball_speed_mph, ln.launch_deg, ln.launch_dir_deg, ln.spin_rpm, ln.spin_axis_deg)
    return ln, f
