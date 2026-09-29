"""Ideal bands for the TrackMan-style tiles, release 004.

    ideal_bands(club, player, club_speed=None, attack=None) -> {metric: band}

band = dict(lo, hi, target, source, modeled[, published][, detail]). lo or hi is
None when that side is open (smash and landing angle only have a floor).

Delivery bands for a straight target shot: path -2 to +2, face -1 to +1 (to the
target), face-to-path -1.5 to +1.5, launch direction -2 to +2 (TrackMan, Anchor
5(a)), spin axis -2 to +2 (TrackMan, Anchor 5(b)), side 5 percent of carry and
curve 4 percent of carry. Widths are in data.IDEAL_TOL, and only the launch
direction and spin axis widths are sourced. The rest are MODELED.

Non-driver clubs: centers are the MODEL's preset outputs (deliver plus
simulate at the preset, spin trim included), not table values, so the ideal
preset sits inside its own bands. The published table value goes in
`published` where one exists. Launch +-1.5 deg, spin +-10 percent, peak height
+-3 yd, landing angle at least preset minus 3 deg (top open), attack +-1.5 deg,
dynamic loft +-2 deg, spin loft +-2 deg, smash at least preset minus 0.03 (top
open). Ball speed and carry come from the ideal delivery scaled to the current
club speed (presets.scale_speed, same spin trim), +-3 percent. Club speed is
the preset speed +-5 percent, an informational band: the tile says how the
player's speed compares with the player group's.

Driver (task 004-copy-pass): the ideal is data.DRIVER_IDEAL, not the Tour average.
The attack band is +2 to +5 with target +4, from TrackMan's 2010 chart, where
carry and total rise with attack angle (see data.DRIVER_IDEAL). Dynamic loft is
chart.optimal_loft(current club speed, current attack) +-1.5 deg. Ball speed,
carry and total come from the model at the ideal delivery at the current club
speed, +-3 percent (spin trim 1.0, the chart's own strike). Spin loft, smash,
peak height and landing angle are the ideal delivery's model outputs at the
preset club speed. Launch and spin come from the two optimizer sources at the
current club speed and attack angle. Bands default to the ideal attack angle
(+4), not the Tour average, so the optimizer lookups match the ideal delivery.
    TrackMan Carry Optimizer (2010), club speed 75 to 120 by attack angle -5, 0, +5.
    PING Optimal Launch & Spin (2019), ball speed 80 to 180 by attack angle -10 to +10.
Bilinear interpolation, clamped to each table's range. PING is read at the
ideal delivery's ball speed at the current club speed. The band runs from the
lower of the two sources minus a margin to the higher plus a margin (1 deg
launch, 200 rpm spin, MODELED). The sources disagree by 0.7 to 3.3 deg of
launch (Anchor 4), and `detail` carries both values.

Known exceptions, kept on record (see exceptions()): the metrics where the
model's ideal delivery falls outside its own band. exceptions() runs the ideal
delivery of every club and player against its bands at the preset club speed.
For clubs other than the driver that is the preset (a Tour or amateur average).

club_speed scales ball speed, carry and total (and moves the driver's optimizer
lookups and dynamic loft band). attack moves only the driver's optimizer lookups
and dynamic loft band. Neither moves the other bands.
"""

from math import isfinite

import data
import flight
import presets
from chart import _PING_AOAS, _PING_SPEEDS, _TRACKMAN, _TRACKMAN_AOAS, _TRACKMAN_SPEEDS, optimal_loft, ping_2019, trackman_carry_2010  # noqa: F401

METRICS = (
    "club_speed", "attack_deg", "club_path_deg", "face_deg", "face_to_path_deg", "dyn_loft_deg", "spin_loft_deg",
    "ball_speed_mph", "smash", "launch_deg", "launch_dir_deg", "spin_rpm", "spin_axis_deg", "max_height_yd",
    "land_angle_deg", "carry_yd", "total_yd", "side_yd", "curve_yd",
)

_TOL = data.IDEAL_TOL

DRIVER_ATTACK_SOURCE = (
    "MODELED design choice from TrackMan's 2010 Driver Fitting Chart (TrackMan model output): carry and total rise "
    "with attack angle from -5 to 0 to +5 at every club speed, and +5 is the chart's top row. Band +2 to +5, "
    "target +4"
)
DRIVER_LOFT_SOURCE = (
    "TrackMan Carry Optimizer 2010 dynamic loft at the current club speed and attack angle (TrackMan model "
    "output), bilinear on the chart, +-1.5 deg (MODELED width)"
)


def _band(lo, hi, target, source, modeled=True):
    return {"lo": lo, "hi": hi, "target": target, "source": source, "modeled": modeled}


def _around(center, half, source, modeled=True):
    return _band(center - half, center + half, center, source, modeled)


def _published(club, player, p):
    """Published table values for the preset row, keyed by metric name."""
    used = p["club"]
    out = {}
    if player in ("pga", "lpga"):
        tour = "PGA" if player == "pga" else "LPGA"
        r = data.TOURS[tour][used]
        out.update(
            club_speed=r["club_speed_mph"], attack_deg=r["attack_deg"], ball_speed_mph=r["ball_speed_mph"],
            smash=r["smash"], launch_deg=r["launch_deg"], spin_rpm=r["spin_rpm"], max_height_yd=r["max_height_yd"],
            land_angle_deg=r["land_angle_deg"], carry_yd=r["carry_yd"],
        )
        if (tour, used) in data.DYNAMIC_LOFT_DEG:
            out["dyn_loft_deg"] = data.DYNAMIC_LOFT_DEG[(tour, used)]
            out["spin_loft_deg"] = data.SPIN_LOFT_DEG[(tour, used)]
    elif used in data.AMATEUR_ANCHORS:
        a = data.AMATEUR_ANCHORS[used]
        out.update(
            club_speed=a["club_speed_mph"], attack_deg=a["attack_deg"], dyn_loft_deg=a["dyn_loft_deg"],
            ball_speed_mph=a["ball_speed_mph"], launch_deg=a["launch_deg"], spin_rpm=a["spin_rpm"],
            spin_loft_deg=a["spin_loft_deg"],
        )
    return out


def ideal_bands(club, player, club_speed=None, attack=None):
    p = presets.preset(club, player)
    ideal0 = p["ideal"]  # at the preset club speed
    ln0, f0 = presets.fly(ideal0)
    speed = p["club_speed"] if club_speed is None else club_speed
    ideal_s = presets.ideal_delivery(club, player, speed)  # raises ValueError outside data.DOMAIN
    ln_s, f_s = (ln0, f0) if speed == p["club_speed"] else presets.fly(ideal_s)
    aoa = ideal0["attack"] if attack is None else attack
    lo_a, hi_a = data.DOMAIN["attack_deg"]
    if not (isfinite(aoa) and lo_a <= aoa and aoa <= hi_a):
        raise ValueError(f"attack must be within {lo_a:g} to {hi_a:g} deg, got {aoa!r}")
    tour_src = "MODELED: model preset output for this club and player"
    pub = _published(club, player, p)
    carry = f_s.carry_yd
    total = flight.roll(f_s)
    driver = club == "driver"
    di = data.DRIVER_IDEAL

    b = {}
    b["club_speed"] = _around(p["club_speed"], _TOL["club_speed_frac"] * p["club_speed"],
                              "MODELED: preset club speed +-5 percent, informational")
    if driver:
        b["attack_deg"] = _band(di["attack_lo_deg"], di["attack_hi_deg"], di["attack_deg"], DRIVER_ATTACK_SOURCE)
    else:
        b["attack_deg"] = _around(p["attack"], _TOL["attack_deg"], tour_src + " +-1.5 deg")
    b["club_path_deg"] = _around(0.0, _TOL["path_deg"], "MODELED: straight target shot, path +-2 deg")
    b["face_deg"] = _around(0.0, _TOL["face_deg"], "MODELED: straight target shot, face to target +-1 deg")
    b["face_to_path_deg"] = _around(0.0, _TOL["face_to_path_deg"], "MODELED: straight target shot, face to path +-1.5 deg")
    if driver:
        loft = optimal_loft(speed, aoa).dyn_loft_deg
        b["dyn_loft_deg"] = _around(loft, di["dyn_loft_half_deg"], DRIVER_LOFT_SOURCE)
    else:
        b["dyn_loft_deg"] = _around(p["dyn_loft"], _TOL["dyn_loft_deg"], tour_src + " +-2 deg")
    b["spin_loft_deg"] = _around(ln0.spin_loft_deg, _TOL["spin_loft_deg"], tour_src + " +-2 deg")
    b["ball_speed_mph"] = _around(ln_s.ball_speed_mph, _TOL["ball_speed_frac"] * ln_s.ball_speed_mph,
                                  "MODELED: ideal delivery scaled to the current club speed +-3 percent")
    b["smash"] = _band(ln0.smash - _TOL["smash_below"], None, ln0.smash, tour_src + ", at least preset minus 0.03")
    b["launch_deg"] = _around(ln0.launch_deg, _TOL["launch_deg"], tour_src + " +-1.5 deg")
    b["launch_dir_deg"] = _around(0.0, _TOL["launch_dir_deg"],
                                  "TrackMan, What is Launch Direction? (keep within ±2 degrees)", modeled=False)
    b["spin_rpm"] = _around(ln0.spin_rpm, _TOL["spin_frac"] * ln0.spin_rpm, tour_src + " +-10 percent")
    b["spin_axis_deg"] = _around(0.0, _TOL["spin_axis_deg"],
                                 "TrackMan, What is Spin Axis? (-2 to 2 counts as straight)", modeled=False)
    b["max_height_yd"] = _around(f0.max_height_yd, _TOL["max_height_yd"], tour_src + " +-3 yd")
    b["land_angle_deg"] = _band(f0.land_angle_deg - _TOL["land_angle_below_deg"], None, f0.land_angle_deg,
                                tour_src + ", at least preset minus 3 deg")
    b["carry_yd"] = _around(carry, _TOL["carry_frac"] * carry,
                            "MODELED: ideal delivery scaled to the current club speed +-3 percent")
    b["total_yd"] = _around(total, _TOL["total_frac"] * total,
                            "MODELED: ideal delivery scaled to the current club speed, carry plus modeled roll, +-3 percent")
    b["side_yd"] = _around(0.0, _TOL["side_frac"] * carry, "MODELED: straight target shot, 5 percent of carry")
    b["curve_yd"] = _around(0.0, _TOL["curve_frac"] * carry, "MODELED: straight target shot, 4 percent of carry")

    if driver:
        tm_launch, tm_spin = trackman_carry_2010(speed, aoa)
        pg_launch, pg_spin = ping_2019(ln_s.ball_speed_mph, aoa)
        ml, mr = _TOL["driver_launch_margin_deg"], _TOL["driver_spin_margin_rpm"]
        lo_l, hi_l = min(tm_launch, pg_launch) - ml, max(tm_launch, pg_launch) + ml
        lo_s, hi_s = min(tm_spin, pg_spin) - mr, max(tm_spin, pg_spin) + mr
        detail = {
            "trackman_carry_2010": {"launch_deg": tm_launch, "spin_rpm": tm_spin},
            "ping_2019": {"launch_deg": pg_launch, "spin_rpm": pg_spin},
            "inputs": {"club_speed_mph": speed, "ball_speed_mph": ln_s.ball_speed_mph, "attack_deg": aoa},
        }
        b["launch_deg"] = _band(
            lo_l, hi_l, 0.5 * (tm_launch + pg_launch),
            f"TrackMan Carry Optimizer 2010 {tm_launch:.1f} deg, PING 2019 {pg_launch:.1f} deg; "
            f"band is the lower minus {ml:g} to the higher plus {ml:g} deg (MODELED margin)")
        b["launch_deg"]["detail"] = detail
        b["spin_rpm"] = _band(
            lo_s, hi_s, 0.5 * (tm_spin + pg_spin),
            f"TrackMan Carry Optimizer 2010 {tm_spin:.0f} rpm, PING 2019 {pg_spin:.0f} rpm; "
            f"band is the lower minus {mr:g} to the higher plus {mr:g} rpm (MODELED margin)")
        b["spin_rpm"]["detail"] = detail
    for metric, value in pub.items():
        b[metric]["published"] = value
    return b


def exceptions():
    """(club, player, metric) for every metric where the model's ideal delivery
    (path 0, face 0) falls outside its own band at the preset club speed. Each
    item is a dict with club, player, metric, value, lo, hi. For the driver the
    ideal is data.DRIVER_IDEAL, for every other club the preset."""
    out = []
    for player in presets.PLAYERS:
        for club in presets.CLUBS:
            i = presets.preset(club, player)["ideal"]
            ln, f = presets.fly(i)
            values = {
                "club_speed": i["club_speed"], "attack_deg": i["attack"], "club_path_deg": i["path"],
                "face_deg": i["face"], "face_to_path_deg": ln.face_to_path_deg, "dyn_loft_deg": i["dyn_loft"],
                "spin_loft_deg": ln.spin_loft_deg, "ball_speed_mph": ln.ball_speed_mph, "smash": ln.smash,
                "launch_deg": ln.launch_deg, "launch_dir_deg": ln.launch_dir_deg, "spin_rpm": ln.spin_rpm,
                "spin_axis_deg": ln.spin_axis_deg, "max_height_yd": f.max_height_yd,
                "land_angle_deg": f.land_angle_deg, "carry_yd": f.carry_yd, "total_yd": flight.roll(f),
                "side_yd": f.side_yd, "curve_yd": f.curve_yd,
            }
            bands = ideal_bands(club, player)
            for metric in METRICS:
                v, b = values[metric], bands[metric]
                if (b["lo"] is not None and v < b["lo"] - 1e-9) or (b["hi"] is not None and v > b["hi"] + 1e-9):
                    out.append({"club": club, "player": player, "metric": metric, "value": v, "lo": b["lo"], "hi": b["hi"]})
    return out


def optimizer_grids():
    """The two driver optimizer tables as plain lists, so a page can interpolate
    live. Each grid is indexed [row][column] as its `layout` says, rows and
    columns ascending."""
    speeds, aoas = _TRACKMAN_SPEEDS, _TRACKMAN_AOAS

    def tm(idx):
        return [[_TRACKMAN[(s, a)][idx] for a in aoas] for s in speeds]

    return {
        "trackman_carry_2010": {
            "source": "TrackMan Driver Fitting Chart (2010), CARRY Optimizer (Anchor 4, Source 1)",
            "layout": "[club speed index][attack angle index]",
            "club_speed_mph": list(speeds),
            "attack_deg": list(aoas),
            "ball_speed_mph": tm(2),
            "launch_deg": tm(3),
            "spin_rpm": tm(4),
            "carry_yd": tm(5),
            "dyn_loft_deg": tm(7),
        },
        "ping_2019": {
            "source": "PING Optimal Launch & Spin Chart (2019) (Anchor 4, Source 2)",
            "layout": "[ball speed index][attack angle index]",
            "ball_speed_mph": list(_PING_SPEEDS),
            "attack_deg": list(_PING_AOAS),
            "launch_deg": [[c[0] for c in data.PING_2019[s]] for s in _PING_SPEEDS],
            "spin_rpm": [[c[1] for c in data.PING_2019[s]] for s in _PING_SPEEDS],
        },
    }
