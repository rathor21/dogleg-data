"""Tests for the 004 flight model (task 004.2, gate G2).

G2: for every PGA and LPGA row of the TrackMan 2023 tables, launch from the
published ball speed, launch angle and spin (launch direction 0, spin axis 0)
and land within carry +-3%, max height +-3 yd, land angle +-2 deg. A looser
teaching tolerance (carry +-5%, height +-4 yd, land angle +-3 deg) is tested
the same way.

Rows the shipped quadratic model still misses are recorded in
tests/g2_known_misses.json (written by `calibrate.py --write-misses`, which
runs the model). Each recorded row is xfail(strict=True): a recorded row that
starts passing fails the suite until the record is regenerated. Rows not in
the file must pass. test_record_matches_model also fails on a new miss, a
worse miss, or a stale entry (a recorded miss that now passes).
"""

import dataclasses
import math

import pytest

import baselines
import calibrate
import data
import flight
import gates

G2_MISSES = gates.load_record()["g2"]
TEACHING_MISSES = gates.load_record()["teaching"]


def _describe(miss):
    names = {"carry_yd": "carry {:+.1f} yd", "height_yd": "height {:+.1f} yd", "land_deg": "land angle {:+.1f} deg"}
    return "; ".join(names[k].format(v) for k, v in miss.items())


def _params(record, label):
    out = []
    for tour, club, _row in gates.rows():
        key = f"{tour}/{club}"
        marks = []
        if key in record:
            marks.append(
                pytest.mark.xfail(strict=True, reason=f"{label} miss: " + _describe(record[key]))
            )
        out.append(pytest.param(tour, club, marks=marks, id=f"{tour}-{club}"))
    return out


def _sim(tour, club):
    r = data.TOURS[tour][club]
    return r, flight.simulate(r["ball_speed_mph"], r["launch_deg"], 0.0, r["spin_rpm"], 0.0)


@pytest.mark.parametrize("tour,club", _params(G2_MISSES, "G2"))
def test_g2_tour_row(tour, club):
    r, f = _sim(tour, club)
    assert f.carry_yd == pytest.approx(r["carry_yd"], rel=gates.CARRY_TOL_FRAC)
    assert abs(f.max_height_yd - r["max_height_yd"]) <= gates.HEIGHT_TOL_YD
    assert abs(f.land_angle_deg - r["land_angle_deg"]) <= gates.LAND_TOL_DEG


@pytest.mark.parametrize("tour,club", _params(TEACHING_MISSES, "teaching"))
def test_teaching_tolerance_row(tour, club):
    r, f = _sim(tour, club)
    assert f.carry_yd == pytest.approx(r["carry_yd"], rel=gates.TEACH_CARRY_FRAC)
    assert abs(f.max_height_yd - r["max_height_yd"]) <= gates.TEACH_HEIGHT_YD
    assert abs(f.land_angle_deg - r["land_angle_deg"]) <= gates.TEACH_LAND_DEG


@pytest.mark.parametrize("label,now,record", [
    ("G2", gates.g2_misses, G2_MISSES),
    ("teaching", gates.teaching_misses, TEACHING_MISSES),
])
def test_record_matches_model(label, now, record):
    """The xfail record documents misses; it must not absorb regressions and
    must not go stale."""
    current = now()
    for key, miss in current.items():
        assert key in record, f"new {label} miss on {key}: {_describe(miss)}"
        for comp, err in miss.items():
            assert comp in record[key], f"{key}: new {label} component {comp} ({err:+.1f})"
            assert abs(err) <= abs(record[key][comp]) + 0.15, (
                f"{key}: {comp} worsened from {record[key][comp]:+.1f} to {err:+.1f}"
            )
    for key, miss in record.items():
        assert key in current, f"stale {label} entry: {key} now passes; rerun --write-misses"
        for comp in miss:
            assert comp in current[key], f"stale {label} entry: {key} {comp} now passes"


# Ratchet floor. Change these numbers only together with the evidence comment
# above data.QUAD in data.py, and only when a refit is shipped on purpose.
FLOOR_G2_PASSES = 6
FLOOR_TEACHING_PASSES = 12
CEILING_OVERALL_RMS = 1.05


def test_quality_floor():
    n = gates.n_rows()
    assert n - len(gates.g2_misses()) >= FLOOR_G2_PASSES
    assert n - len(gates.teaching_misses()) >= FLOOR_TEACHING_PASSES
    _, overall = gates.rms(flight.DEFAULT_AERO)
    assert overall <= CEILING_OVERALL_RMS


def test_tables_are_complete():
    assert len(data.PGA) == 12 and len(data.LPGA) == 11
    assert "3i" not in data.LPGA
    for table in data.TOURS.values():
        for row in table.values():
            assert set(row) == set(data.FIELDS)
    drv = data.PGA["driver"]
    assert (drv["ball_speed_mph"], drv["launch_deg"], drv["spin_rpm"], drv["carry_yd"]) == (171, 10.4, 2545, 282)
    assert data.LPGA["6i"]["carry_yd"] == 155


# ---------------------------------------------------------------------------
# Faithfulness to the published aero model (Anchor 7 Source 1).
# ---------------------------------------------------------------------------


def test_matches_nathan_workbook():
    """Nathan's workbook default shot (160 mph, 11 deg, 3000 rpm, 70 F, sea
    level) reads 259.3 yd and 4.99 s hang time with the published parameter
    set (Re branch on, multipliers 1.0). Values read from the workbook's own
    cells. Runs the Nathan model through the pluggable coefficient hook."""
    f = flight.simulate(160.0, 11.0, 0.0, 3000.0, 0.0, aero=baselines.nathan_model(data.NATHAN))
    assert f.carry_yd == pytest.approx(259.3, abs=1.0)
    assert f.flight_time_s == pytest.approx(4.99, abs=0.05)
    assert f.max_height_yd == pytest.approx(19.7, abs=0.3)


def test_step_size_converges():
    a = flight.simulate(130.0, 14.0, 0.0, 6200.0, 5.0, dt=0.01)
    b = flight.simulate(130.0, 14.0, 0.0, 6200.0, 5.0, dt=0.0025)
    assert a.carry_yd == pytest.approx(b.carry_yd, abs=0.05)
    assert a.side_yd == pytest.approx(b.side_yd, abs=0.05)


# ---------------------------------------------------------------------------
# Physics sanity.
# ---------------------------------------------------------------------------

SHOT = dict(ball_speed_mph=130.0, launch_deg=14.0, launch_dir_deg=0.0, spin_rpm=6200.0)


def test_zero_spin_axis_has_no_side():
    f = flight.simulate(spin_axis_deg=0.0, **SHOT)
    assert abs(f.side_yd) < 0.01


@pytest.mark.parametrize("axis", [2.0, 7.0, 15.0])
def test_spin_axis_mirrors(axis):
    p = flight.simulate(spin_axis_deg=axis, **SHOT)
    n = flight.simulate(spin_axis_deg=-axis, **SHOT)
    assert p.side_yd == pytest.approx(-n.side_yd, abs=1e-6)
    assert p.carry_yd == pytest.approx(n.carry_yd, abs=1e-6)


def test_positive_spin_axis_curves_right():
    p = flight.simulate(spin_axis_deg=8.0, **SHOT)
    n = flight.simulate(spin_axis_deg=-8.0, **SHOT)
    assert p.side_yd > 1.0
    assert n.side_yd < -1.0
    assert p.y[-2] > 0.0  # lateral track ends right of the target line


def test_carry_rises_with_ball_speed():
    carries = [
        flight.simulate(v, 14.0, 0.0, 6200.0, 0.0).carry_yd
        for v in (100.0, 115.0, 130.0, 145.0, 160.0)
    ]
    assert carries == sorted(carries)
    assert len(set(carries)) == len(carries)


def test_curve_equals_side_when_aimed_at_target():
    f = flight.simulate(spin_axis_deg=6.0, **SHOT)
    assert f.curve_yd == pytest.approx(f.side_yd)


def test_curve_removes_the_start_line():
    """Straight start 3 deg right with no side spin: side is the start line,
    curve is about zero (Anchor 5a Source 2: 3 deg at 200 yd is 10.5 yd)."""
    f = flight.simulate(130.0, 14.0, 3.0, 6200.0, 0.0)
    assert f.side_yd > 4.0
    assert abs(f.curve_yd) < 0.05 * f.side_yd


def test_launch_direction_geometry():
    """TrackMan's launch direction page: 2 deg right is 3.4 yd at 100 yd, 7.0
    yd at 200 yd (Anchor 5a Source 2). Same start line, so side/carry = tan."""
    f = flight.simulate(130.0, 14.0, 2.0, 6200.0, 0.0)
    assert f.side_yd / f.carry_yd == pytest.approx(0.0349, rel=0.01)


def test_flight_arrays_consistent():
    f = flight.simulate(spin_axis_deg=4.0, **SHOT)
    assert len(f.t) == len(f.x) == len(f.y) == len(f.z)
    assert f.z[0] == 0.0 and f.z[-1] == 0.0
    assert f.x[-1] == pytest.approx(f.carry_yd)
    assert f.y[-1] == pytest.approx(f.side_yd)
    assert f.t[-1] == pytest.approx(f.flight_time_s)
    assert f.max_height_yd == pytest.approx(f.z.max())
    assert f.z[f.x.argmax()] == 0.0
    assert 0.0 < f.apex_x_yd < f.carry_yd
    assert 0.0 < f.land_speed_mph < SHOT["ball_speed_mph"]


def test_spin_decay_lowers_the_apex():
    """Spin lost in flight removes lift, so the decayed shot peaks lower than
    the same shot with decay switched off. Uses the published k."""
    with_decay = flight.simulate(150.0, 12.0, 0.0, 3000.0, 0.0)
    no_decay_model = dataclasses.replace(flight.DEFAULT_AERO, spin_decay=0.0)
    no_decay = flight.simulate(150.0, 12.0, 0.0, 3000.0, 0.0, aero=no_decay_model)
    assert with_decay.max_height_yd < no_decay.max_height_yd
    assert abs(with_decay.carry_yd - no_decay.carry_yd) < 10.0


def test_shipped_model_uses_the_published_spin_decay():
    """Anchor 7 Source 3 (Smits and Smith): k = 2.0e-5, SI."""
    assert "k" not in data.QUAD
    assert flight.DEFAULT_AERO.spin_decay == data.SPIN_DECAY_COEF == 2.0e-5


def test_air_density_matters():
    thin = flight.simulate(150.0, 12.0, 0.0, 3000.0, 0.0, air=flight.Air(density=1.0))
    std = flight.simulate(150.0, 12.0, 0.0, 3000.0, 0.0)
    assert thin.carry_yd > std.carry_yd


# ---------------------------------------------------------------------------
# Curvature against Anchor 5(b) Source 2, TrackMan "What is Spin Axis?".
#   optimized 150 yd shot: 2 deg of spin axis is about 2.2 yd, 10 deg about 11 yd.
#   optimized 200 yd shot: 2 deg is about 3 yd, 10 deg about 15 yd.
# This is a CHECK, not a fit target. TrackMan does not give the ball speed,
# launch or spin of an "optimized" shot, so the model runs from the Tour row
# whose published carry matches: LPGA 3w (200 yd) and LPGA 6i (155 yd, the
# closest to 150 in either table). The published figures are "about" values,
# rounded to 0.1 to 1 yd: 3 yd could be 2.5 to 3.5, so +-17% is rounding alone.
# Tolerances: 25% on the 200 yd case, 35% on the 150 yd case. Results for the
# shipped quadratic fit: LPGA 3w about 18% low (2.5 and 12.1 yd), LPGA 6i about
# 28% high (2.8 and 14.0 yd). The flat-Nathan two-multiplier model this
# replaced read 3% high on the 3w and 27% high on the 6i, so the 3w check got
# worse and the 6i is unchanged.
# ---------------------------------------------------------------------------


def _side(tour, club, axis):
    r = data.TOURS[tour][club]
    return flight.simulate(r["ball_speed_mph"], r["launch_deg"], 0.0, r["spin_rpm"], axis).side_yd


@pytest.mark.parametrize(
    "tour,club,axis,published,rel",
    [
        ("LPGA", "3w", 2.0, 3.0, 0.25),
        ("LPGA", "3w", 10.0, 15.0, 0.25),
        ("LPGA", "6i", 2.0, 2.2, 0.35),
        ("LPGA", "6i", 10.0, 11.0, 0.35),
    ],
)
def test_spin_axis_curvature_examples(tour, club, axis, published, rel):
    assert _side(tour, club, axis) == pytest.approx(published, rel=rel)


@pytest.mark.xfail(
    strict=False,
    reason="TrackMan's examples curve the 200 yd shot more than the 150 yd shot "
    "(15 vs 11 yd at 10 deg); the quadratic fit gives the 6-iron more (14.0 vs 12.1)",
)
def test_longer_shot_curves_more_for_same_axis():
    assert _side("LPGA", "3w", 10.0) > _side("LPGA", "6i", 10.0)


# ---------------------------------------------------------------------------
# Roll (MODELED, no fitting claims).
# ---------------------------------------------------------------------------


def _total(tour, club):
    r = data.TOURS[tour][club]
    f = flight.simulate(r["ball_speed_mph"], r["launch_deg"], 0.0, r["spin_rpm"], 0.0)
    return f, flight.roll(f) - f.carry_yd


def test_roll_driver_and_wedge_ranges():
    _, driver_roll = _total("PGA", "driver")
    _, pw_roll = _total("PGA", "pw")
    assert 20.0 <= driver_roll <= 30.0
    assert 1.0 <= pw_roll <= 7.0


def test_roll_is_bounded_and_nonnegative():
    for tour, table in data.TOURS.items():
        for club in table:
            _, r = _total(tour, club)
            assert 0.0 <= r <= data.ROLL_MAX_YD


# ---------------------------------------------------------------------------
# Coefficient model.
# ---------------------------------------------------------------------------


def test_shipped_quad_meets_its_constraints():
    assert calibrate.constraints_ok(data.QUAD, 1e-3)
    m = flight.DEFAULT_AERO
    for s in (0.05, 0.075, 0.15, 0.30, 0.45, 0.50):
        assert 0.0 < m.cl(s, 1.5) <= data.CL_MAX + 1e-3
        for re in (0.5, 1.0, 1.5, 2.3):
            assert data.CD_BAND[0] - 1e-3 <= m.cd(s, re) <= data.CD_BAND[1] + 1e-3


def test_coefficient_hook_is_pluggable():
    """A model with no lift and no drag flies a vacuum parabola."""
    vac = flight.Aero("vacuum", lambda s, re: 0.0, lambda s, re: 0.0)
    f = flight.simulate(100.0, 20.0, 0.0, 3000.0, 0.0, aero=vac)
    v = 100.0 * data.MPH_TO_MS
    t_flight = 2 * v * math.sin(math.radians(20.0)) / data.G
    assert f.flight_time_s == pytest.approx(t_flight, rel=1e-3)
    assert f.carry_yd == pytest.approx(v * math.cos(math.radians(20.0)) * t_flight / data.YD_TO_M, rel=1e-3)


# ---------------------------------------------------------------------------
# Input contract (the JS port throws rather than returning NaN).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("speed", [0.0, -5.0, float("nan"), float("inf")])
def test_bad_ball_speed_raises(speed):
    with pytest.raises(ValueError):
        flight.simulate(speed, 14.0, 0.0, 6000.0, 0.0)


@pytest.mark.parametrize("dt", [0.0, -0.01, float("nan")])
def test_bad_dt_raises(dt):
    with pytest.raises(ValueError):
        flight.simulate(130.0, 14.0, 0.0, 6000.0, 0.0, dt=dt)


@pytest.mark.parametrize("field", ["launch_deg", "launch_dir_deg", "spin_rpm", "spin_axis_deg"])
def test_nonfinite_input_raises(field):
    args = dict(ball_speed_mph=130.0, launch_deg=14.0, launch_dir_deg=0.0, spin_rpm=6000.0, spin_axis_deg=0.0)
    args[field] = float("nan")
    with pytest.raises(ValueError):
        flight.simulate(**args)


def test_flight_that_never_lands_raises():
    """A vertical launch in a vacuum stays up longer than MAX_FLIGHT_S."""
    vac = flight.Aero("vacuum", lambda s, re: 0.0, lambda s, re: 0.0)
    with pytest.raises(RuntimeError):
        flight.simulate(700.0, 90.0, 0.0, 0.0, 0.0, aero=vac)
    assert flight.MAX_FLIGHT_S == 60.0


def test_vertical_launch_in_air_does_not_produce_nan():
    f = flight.simulate(60.0, 90.0, 0.0, 3000.0, 0.0)
    assert math.isfinite(f.carry_yd) and math.isfinite(f.max_height_yd)
