"""Gate scoring for release 004.2: tolerances, rows, and the miss lists.

Shared by calibrate.py (fitting and reports) and tests/test_flight.py. No
scipy here. The recorded misses live in tests/g2_known_misses.json, written by
`calibrate.py --write-misses` and loaded lazily by load_record().
"""

import json
import os

import numpy as np

import data
import flight

# G2 tolerances (task 004.2).
CARRY_TOL_FRAC = 0.03
HEIGHT_TOL_YD = 3.0
LAND_TOL_DEG = 2.0
# Teaching tolerance: a looser bar (coordinator, task 004.2).
TEACH_CARRY_FRAC = 0.05
TEACH_HEIGHT_YD = 4.0
TEACH_LAND_DEG = 3.0

# Chart gate (task 004-copy-pass): model carry from the chart's own launch
# conditions against the TrackMan 2010 chart (model output), 60 rows.
CHART_CARRY_TOL_FRAC = 0.03
# Total distance (carry plus roll) against the chart's total column: within 5
# percent. Looser than carry because roll is a MODELED, three-parameter form.
CHART_TOTAL_TOL_FRAC = 0.05

MISSES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "tests", "g2_known_misses.json"
)

TOURS = ("PGA", "LPGA")


def rows(tours=TOURS):
    for tour in tours:
        for club, r in data.TOURS[tour].items():
            yield tour, club, r


def n_rows(tours=TOURS):
    return sum(1 for _ in rows(tours))


def run_row(r, aero=None, dt=0.01):
    return flight.simulate(
        r["ball_speed_mph"], r["launch_deg"], 0.0, r["spin_rpm"], 0.0, dt=dt, aero=aero
    )


def errors(f, r):
    """(carry error yd, height error yd, land angle error deg), model minus published."""
    return (
        f.carry_yd - r["carry_yd"],
        f.max_height_yd - r["max_height_yd"],
        f.land_angle_deg - r["land_angle_deg"],
    )


def normalized(f, r):
    """Errors in units of the G2 tolerances: 1.0 sits on the gate."""
    ec, eh, ea = errors(f, r)
    return (ec / (CARRY_TOL_FRAC * r["carry_yd"]), eh / HEIGHT_TOL_YD, ea / LAND_TOL_DEG)


def rms(aero, tours=TOURS, dt=0.01):
    """(rms per component, overall rms) of the normalized errors."""
    vals = np.array([normalized(run_row(r, aero, dt), r) for _t, _c, r in rows(tours)])
    return np.sqrt(np.mean(vals**2, axis=0)), float(np.sqrt(np.mean(vals**2)))


def _misses(aero, dt, carry_frac, height_yd, land_deg):
    """{"PGA/3w": {"carry_yd": err, ...}} for rows outside the given tolerances,
    listing only the components that miss. Runs the model."""
    out = {}
    for tour, club, r in rows():
        ec, eh, ea = errors(run_row(r, aero, dt), r)
        miss = {}
        if abs(ec) > carry_frac * r["carry_yd"]:
            miss["carry_yd"] = round(ec, 1)
        if abs(eh) > height_yd:
            miss["height_yd"] = round(eh, 1)
        if abs(ea) > land_deg:
            miss["land_deg"] = round(ea, 1)
        if miss:
            out[f"{tour}/{club}"] = miss
    return out


def g2_misses(aero=None, dt=0.01):
    return _misses(aero, dt, CARRY_TOL_FRAC, HEIGHT_TOL_YD, LAND_TOL_DEG)


def teaching_misses(aero=None, dt=0.01):
    return _misses(aero, dt, TEACH_CARRY_FRAC, TEACH_HEIGHT_YD, TEACH_LAND_DEG)


def load_record(path=MISSES_PATH):
    """The recorded {"g2": ..., "teaching": ...} misses. Read on call, never at import."""
    with open(path) as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# TrackMan 2010 Driver Fitting Chart (data.TRACKMAN_CARRY_2010 and
# TRACKMAN_TOTAL_2010, "TrackMan 2010 chart (TrackMan model output)")
# ---------------------------------------------------------------------------

CHART_NAMES = ("C", "T")  # C: carry optimizer rows, T: total optimizer rows


def chart_rows():
    """(chart, label, row dict) for the 60 chart rows. label is like "C115/+5"."""
    for chart, table in (("C", data.TRACKMAN_CARRY_2010), ("T", data.TRACKMAN_TOTAL_2010)):
        for vals in table:
            r = dict(zip(data.TRACKMAN_CARRY_2010_FIELDS, vals))
            yield chart, f"{chart}{r['club_speed_mph']}/{r['attack_deg']:+d}", r


def n_chart_rows():
    return sum(1 for _ in chart_rows())


def run_chart_row(r, aero=None, dt=0.01):
    """Fly a chart row from its published ball speed, launch and spin (no axis)."""
    return flight.simulate(r["ball_speed_mph"], r["launch_deg"], 0.0, r["spin_rpm"], 0.0, dt=dt, aero=aero)


def chart_normalized(f, r):
    """Carry error in units of 3 percent of the chart carry: 1.0 sits on the gate."""
    return (f.carry_yd - r["carry_yd"]) / (CHART_CARRY_TOL_FRAC * r["carry_yd"])


def chart_rms(aero, dt=0.01):
    v = np.array([chart_normalized(run_chart_row(r, aero, dt), r) for _c, _l, r in chart_rows()])
    return float(np.sqrt(np.mean(v**2)))


def chart_misses(aero=None, dt=0.01):
    """{"C115/+5": {"carry_yd": error}} for chart rows whose carry is outside 3 percent."""
    out = {}
    for _c, label, r in chart_rows():
        e = run_chart_row(r, aero, dt).carry_yd - r["carry_yd"]
        if abs(e) > CHART_CARRY_TOL_FRAC * r["carry_yd"]:
            out[label] = {"carry_yd": round(e, 1)}
    return out


def chart_total_error(f, r):
    """Model total minus chart total, yd, with the model's own carry and roll."""
    return flight.roll(f) - r["total_yd"]


def chart_total_misses(aero=None, dt=0.01):
    """{"C115/+5": {"total_yd": error}} for chart rows whose model total (own
    carry plus roll) is outside 5 percent of the chart total."""
    out = {}
    for _c, label, r in chart_rows():
        e = chart_total_error(run_chart_row(r, aero, dt), r)
        if abs(e) > CHART_TOTAL_TOL_FRAC * r["total_yd"]:
            out[label] = {"total_yd": round(e, 1)}
    return out
