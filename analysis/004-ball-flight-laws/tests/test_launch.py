"""Tests for the delivery-to-launch model (task 004.3, gates G3 and G4).

G3: for every PGA and LPGA row of the TrackMan 2023 tables, deliver(table club
speed, table attack angle, path 0, face 0, default dynamic loft) reproduces the
table's launch angle within 1 deg, spin within 10 percent and ball speed within
2 percent. Rows the shipped model still misses are recorded in
tests/g3_known_misses.json (written by `calibrate_launch.py --write-misses`,
which runs the model) and are xfail(strict=True): a recorded row that starts
passing fails the suite until the record is regenerated. Rows not in the record
must pass. test_record_matches_model also fails on a new miss, a worse miss or
a stale entry, in all three sections (g3, published, presets). No model runs at
collection time: the record is a file read, and parameter ids come from data.

These tests import gates_launch, not calibrate_launch, so they need no scipy.

G4: physics sanity (symmetry, monotonicity, the same face-to-path curving the
driver more than the irons, attack angle and swing direction coupling) and the
five golfer cases on the PGA 7-iron preset.
"""

import dataclasses
import json
import math

import pytest

import data
import flight
import gates_launch as gl
import launch
import launch_tools
import presets

_RECORD = gl.load_record()  # a file read, no model run
G3_MISSES = _RECORD["g3"]
PUBLISHED_MISSES = _RECORD["published"]
PRESET_MISSES = _RECORD["presets"]

_NAMES = {"launch_deg": "launch {:+.2f} deg", "spin_pct": "spin {:+.1f}%", "ball_pct": "ball speed {:+.1f}%",
          "spin_loft_deg": "spin loft {:+.1f} deg"}


def _describe(miss):
    return "; ".join(_NAMES[k].format(v) for k, v in miss.items())


def _marks(record, key, label):
    if key in record:
        return [pytest.mark.xfail(strict=True, reason=f"{label} miss: " + _describe(record[key]))]
    return []


# Ratchet floors. Change these numbers only together with the evidence in the
# data.LAUNCH_MODEL comment and ADR 0004, and only when a refit is shipped on
# purpose.
FLOOR_G3_PASSES = 17  # of 23 rows, all three tolerances
FLOOR_CURVATURE_PASSES = 8  # of 8 examples
FLOOR_AMATEUR_ANCHOR_PASSES = 1  # of 3 anchored amateur presets, all three tolerances (the PW)


@pytest.fixture(scope="module")
def current():
    return gl.current_misses()


# ---------------------------------------------------------------------------
# G3
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tour,club",
    [pytest.param(t, c, marks=_marks(G3_MISSES, f"{t}/{c}", "G3"), id=f"{t}-{c}") for t, c, _ in gl.rows()],
)
def test_g3_tour_row(tour, club):
    res = gl.g3_row(tour, club)
    assert abs(res.launch_err_deg) <= gl.G3_LAUNCH_DEG
    assert abs(res.spin_err_frac) <= gl.G3_SPIN_FRAC
    assert abs(res.ball_err_frac) <= gl.G3_BALL_FRAC


@pytest.mark.parametrize("section", gl.SECTIONS)
def test_record_matches_model(section, current):
    """The xfail record documents misses; it must not absorb regressions and
    must not go stale."""
    record, now = _RECORD[section], current[section]
    for key, miss in now.items():
        assert key in record, f"new {section} miss on {key}: {_describe(miss)}"
        for comp, err in miss.items():
            assert comp in record[key], f"{key}: new {section} component {comp} ({err:+.2f})"
            assert abs(err) <= abs(record[key][comp]) + 0.15, (
                f"{key}: {comp} worsened from {record[key][comp]:+.2f} to {err:+.2f}"
            )
    for key, miss in record.items():
        assert key in now, f"stale {section} entry: {key} now passes; rerun --write-misses"
        for comp in miss:
            assert comp in now[key], f"stale {section} entry: {key} {comp} now passes"


def test_quality_floor(current):
    assert gl.n_rows() - len(current["g3"]) >= FLOOR_G3_PASSES
    assert gl.curvature_passes() >= FLOOR_CURVATURE_PASSES
    spin_misses = [k for k, m in current["presets"].items() if "spin_pct" in m]
    assert not spin_misses, f"presets whose spin is off by more than 1 percent: {spin_misses}"
    amateur_pass = [c for c in data.AMATEUR_ANCHORS if f"amateur/{c}" not in current["presets"]]
    assert len(amateur_pass) >= FLOOR_AMATEUR_ANCHOR_PASSES


def test_g3_misses_never_include_launch():
    """Launch passes by construction (dynamic loft comes from launch)."""
    assert all("launch_deg" not in m for m in G3_MISSES.values())


@pytest.mark.parametrize("key", [f"{t}/{c}" for (t, c) in data.DYNAMIC_LOFT_DEG])
def test_default_dynamic_loft_matches_published(key):
    """The default dynamic loft, inverted from the table launch angle, lands
    within 1 deg of TrackMan's published dynamic loft (driver and 6 iron)."""
    tour, club = key.split("/")
    r = data.TOURS[tour][club]
    dl = launch_tools.derive_dyn_loft(r["launch_deg"], r["attack_deg"], club)
    assert abs(dl - data.DYNAMIC_LOFT_DEG[(tour, club)]) <= gl.DL_CHECK_DEG


@pytest.mark.parametrize(
    "key",
    [pytest.param(f"{t}/{c}", marks=_marks(PUBLISHED_MISSES, f"{t}/{c}", "spin loft"), id=f"{t}-{c}")
     for (t, c) in data.DYNAMIC_LOFT_DEG],
)
def test_spin_loft_at_published_dynamic_loft(key):
    """Spin loft at the published dynamic loft against the published spin loft.
    The LPGA driver misses by 2.3 deg (dynamic loft minus attack angle is 12.7
    against a published 15.0, unexplained on TrackMan's page; log, Anchor 1)."""
    tour, club = key.split("/")
    r = data.TOURS[tour][club]
    ln = launch.deliver(r["club_speed_mph"], r["attack_deg"], 0.0, 0.0, data.DYNAMIC_LOFT_DEG[(tour, club)], club)
    assert abs(ln.spin_loft_deg - data.SPIN_LOFT_DEG[(tour, club)]) <= gl.SL_CHECK_DEG + gl.SL_CHECK_SLACK


def test_tour_dyn_loft_table_matches_a_live_inversion():
    """data.TOUR_DYN_LOFT is a pasted copy of the inversion. A refit of
    LAUNCH_MODEL must regenerate it (calibrate_launch.py --write-tour-dyn-loft)."""
    assert set(data.TOUR_DYN_LOFT) == {(t, c) for t, c, _ in gl.rows()}
    for tour, club, r in gl.rows():
        live = launch_tools.derive_dyn_loft(r["launch_deg"], r["attack_deg"], club)
        assert abs(live - data.TOUR_DYN_LOFT[(tour, club)]) <= gl.TABLE_DL_TOL_DEG, f"{tour}/{club}"


def test_derive_dyn_loft_rejects_unreachable_launch():
    with pytest.raises(ValueError, match="not reachable"):
        launch_tools.derive_dyn_loft(80.0, 0.0)  # steeper than 65 deg of dynamic loft can launch
    with pytest.raises(ValueError, match="not reachable"):
        launch_tools.derive_dyn_loft(-5.0, 0.0)  # below what a 1 deg spin loft launches


# ---------------------------------------------------------------------------
# Fitted pieces
# ---------------------------------------------------------------------------


def test_smash_falls_with_spin_loft_and_holds_at_cap_and_floor():
    m = data.LAUNCH_MODEL
    vals = [launch.smash_of(sl) for sl in range(0, 76)]
    assert all(b <= a + 1e-12 for a, b in zip(vals, vals[1:]))
    assert vals[0] == m["smash_cap"] == 1.49  # capped at the largest published smash
    assert vals[12] == m["smash_cap"]  # the raw quadratic is still above the cap at SL 12
    assert vals[-1] == m["smash_floor"]  # floored beyond the fit
    raw45 = m["smash_a"] + m["smash_b"] * 45 + m["smash_c"] * 45 * 45
    assert m["smash_floor"] == pytest.approx(raw45, abs=1e-4)  # the fit's value at SL 45
    assert launch.smash_of(45.0) == pytest.approx(m["smash_floor"], abs=1e-4)
    assert launch.smash_of(30.0) > m["smash_floor"]


def test_k_of_is_linear_inside_and_flat_outside_the_fit_range():
    m = data.LAUNCH_MODEL
    lo, hi = m["k_sl_lo"], m["k_sl_hi"]
    assert launch.k_of(lo - 8.0) == launch.k_of(lo) == pytest.approx(m["k0"] + m["k1"] * lo)
    assert launch.k_of(hi + 20.0) == launch.k_of(hi) == pytest.approx(m["k0"] + m["k1"] * hi)
    mid = 0.5 * (lo + hi)
    assert launch.k_of(mid) == pytest.approx(0.5 * (launch.k_of(lo) + launch.k_of(hi)))


def test_k_of_driver_has_its_own_line_and_range():
    m = data.LAUNCH_MODEL
    lo, hi = m["k_sl_lo_driver"], m["k_sl_hi_driver"]
    assert (lo, hi) == (6.3, 23.2)  # the TrackMan 2010 chart's spin loft range
    assert launch.k_of(2.0, "driver") == launch.k_of(lo, "driver") == pytest.approx(m["k0_driver"] + m["k1_driver"] * lo)
    assert launch.k_of(40.0, "driver") == launch.k_of(hi, "driver")
    # Inside the chart range the driver is not held at the iron line's floor value
    assert launch.k_of(8.0, "driver") == pytest.approx(m["k0_driver"] + m["k1_driver"] * 8.0)
    assert launch.k_of(8.0, "driver") != launch.k_of(8.0, "7i") == launch.k_of(m["k_sl_lo"], "7i")
    # Every other club, and no club, share the iron line
    for club in (None, "3w", "hybrid", "7i", "pw"):
        assert launch.k_of(20.0, club) == pytest.approx(m["k0"] + m["k1"] * 20.0)


def test_face_share_is_between_the_two_claims():
    """Implied horizontal face share, model output and not a fit. The unverified
    claims are 85 driver and 75 6 iron (unattributed) or 87 and 81 (forum).
    Driver reads about 79 and 6 iron about 73 percent."""
    for tour in ("PGA", "LPGA"):
        for club, lo, hi in (("driver", 0.74, 0.88), ("6i", 0.66, 0.82)):
            a = data.TOURS[tour][club]["attack_deg"]
            share = launch_tools.horizontal_face_share(a, data.DYNAMIC_LOFT_DEG[(tour, club)], club)
            assert lo <= share <= hi
            assert share > 0.5  # face dominates start direction, as TrackMan says


def test_face_share_matches_launch_direction_slope():
    """Small face-to-path: launch direction is share * face + (1 - share) * path."""
    p = presets.preset("driver", "pga")
    share = launch_tools.horizontal_face_share(p["attack"], p["dyn_loft"], "driver")
    ln = launch.deliver(p["club_speed"], p["attack"], 0.0, 1.0, p["dyn_loft"], "driver")
    assert ln.launch_dir_deg == pytest.approx(share * 1.0, abs=0.01)


def test_spin_laws_by_club_class():
    """The driver has its own power law. The 3-wood and 5-wood take the iron law
    times spin_f_wood. Hybrids, irons, wedges and an unnamed club take the iron law."""
    m = data.LAUNCH_MODEL
    iron = launch.spin_of(140.0, 20.0, "7i")
    assert launch.spin_of(140.0, 20.0, "hybrid") == iron == launch.spin_of(140.0, 20.0)
    assert launch.spin_of(140.0, 20.0, "5w") == pytest.approx(m["spin_f_wood"] * iron)
    assert launch.spin_of(140.0, 20.0, "3w") == launch.spin_of(140.0, 20.0, "5w")
    assert launch.spin_of(140.0, 20.0, "driver") == pytest.approx(m["spin_a_driver"] * 140.0 * 20.0 ** m["spin_b_driver"])
    assert 0.0 < m["spin_f_wood"] < 1.0
    assert "spin_f_driver" not in m
    # Iron and wood spin is unchanged by the driver refit (task 004.3 chart)
    assert (m["spin_a"], m["spin_b"], m["spin_f_wood"]) == (0.778695, 1.30445, 0.878791)


def test_driver_spin_falls_almost_linearly_with_spin_loft():
    """The chart law is nearly linear in spin loft (exponent 1.04), unlike the
    iron law (1.30) that collapsed toward zero below its fitted floor."""
    m = data.LAUNCH_MODEL
    assert 0.95 <= m["spin_b_driver"] <= 1.15
    lo = launch.spin_of(170.0, 7.4, "driver")
    hi = launch.spin_of(170.0, 14.8, "driver")
    assert hi / lo == pytest.approx(2.0, rel=0.10)


# ---------------------------------------------------------------------------
# The TrackMan 2010 chart (TrackMan model output): 60 driver deliveries.
# ---------------------------------------------------------------------------


def _chart_deliveries():
    for row in data.TRACKMAN_CARRY_2010 + data.TRACKMAN_TOTAL_2010:
        club_speed, attack, ball, launch_deg, spin, _carry, _total, dyn_loft = row
        yield club_speed, attack, ball, launch_deg, spin, dyn_loft


def test_chart_has_sixty_rows_at_three_attack_angles():
    rows60 = list(_chart_deliveries())
    assert len(rows60) == 60
    assert {r[1] for r in rows60} == {-5, 0, 5}
    assert {r[0] for r in rows60} == set(range(75, 121, 5))
    assert min(r[5] - r[1] for r in rows60) == pytest.approx(6.3)


def test_driver_reproduces_the_chart_launch_and_spin():
    """In-sample: launch within 0.4 deg, spin within 2.5 percent, ball speed
    within 3 percent, at every attack angle and speed."""
    for club_speed, attack, ball, launch_deg, spin, dyn_loft in _chart_deliveries():
        ln = launch.deliver(float(club_speed), float(attack), 0.0, 0.0, dyn_loft, "driver")
        where = f"{club_speed} mph, attack {attack}"
        assert abs(ln.launch_deg - launch_deg) <= 0.4, where
        assert abs(ln.spin_rpm / spin - 1.0) <= 0.025, where
        assert abs(ln.ball_speed_mph / ball - 1.0) <= 0.03, where


def test_driver_spin_falls_as_attack_angle_rises_at_fixed_loft_below_the_iron_floor():
    """The case that prompted the refit: PGA driver loft, attack angle up to
    +10, spin loft down to 3.4. Spin falls smoothly and stays above 1,000 rpm
    down to the chart's lowest spin loft."""
    p = presets.preset("driver", "pga")
    spins = [launch.deliver(p["club_speed"], a, 0.0, 0.0, p["dyn_loft"], "driver", spin_trim=p["spin_trim"]).spin_rpm
             for a in (-6.0, 0.0, 3.0, 6.0, 10.0)]
    assert all(b < a for a, b in zip(spins, spins[1:]))
    assert spins[3] > 1150.0  # +6 deg attack, spin loft 6.7, with the PGA trim: the old iron law gave 1,086 rpm
    assert spins[4] > 0.0
    raw = launch.deliver(p["club_speed"], 6.0, 0.0, 0.0, p["dyn_loft"], "driver").spin_rpm
    assert raw > 1500.0  # untrimmed, at the chart's own spin loft 6.7 (115 mph, +5 row: 1,681 rpm)


def test_driver_at_equal_spin_loft_is_no_longer_under_the_chart():
    """Old iron-law driver spin ran 20 to 37 percent under the chart at equal
    spin loft. Now within 2.5 percent, checked here at the five 100 mph rows."""
    for row in _chart_deliveries():
        club_speed, attack, ball, launch_deg, spin, dyn_loft = row
        if club_speed != 100:
            continue
        ln = launch.deliver(float(club_speed), float(attack), 0.0, 0.0, dyn_loft, "driver")
        assert ln.spin_rpm >= 0.975 * spin


def test_pga_driver_global_model_needs_a_trim_and_lpga_does_not():
    """With no trim the PGA driver reads well over its table (Tour strike
    offsets the chart law does not carry) and the LPGA driver is within 10
    percent. The preset trim restores the PGA driver (ADR 0004)."""
    pga = gl.g3_row("PGA", "driver")
    lpga = gl.g3_row("LPGA", "driver")
    assert pga.spin_err_frac > 0.25
    assert abs(lpga.spin_err_frac) <= 0.10
    assert 0.6 <= presets.preset("driver", "pga")["spin_trim"] <= 0.85


# ---------------------------------------------------------------------------
# Curvature calibration against the eight Anchor 5(b) examples. IN-SAMPLE: the
# eight examples are the fitting data for axis_c, so these pass by design. They
# show the fit works and guard the mapping students see, and they say nothing
# about clubs and face-to-path values TrackMan did not publish.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tour,club,f2p,pub",
    [pytest.param(*e, id=f"{e[0]}-{e[1]}-{e[2]:+.0f}") for e in data.CURVATURE_EXAMPLES],
)
def test_curvature_example(tour, club, f2p, pub):
    _ln, f = gl.curvature_example(tour, club, f2p)
    assert abs(f.curve_yd - pub) <= gl.curve_tol(pub), (
        f"{tour} {club} f2p {f2p:+.0f}: curve {f.curve_yd:+.1f} yd against published {pub:+.0f}"
    )
    assert (f.curve_yd > 0) == (pub > 0)


# ---------------------------------------------------------------------------
# Input contract (data.DOMAIN)
# ---------------------------------------------------------------------------

_GOOD = dict(club_speed_mph=92.0, attack_deg=-3.0, path_deg=0.0, face_deg=0.0, dyn_loft_deg=20.0)


def _deliver(club=None, **changes):
    kw = dict(_GOOD, **changes)
    trim = kw.pop("spin_trim", 1.0)
    return launch.deliver(kw["club_speed_mph"], kw["attack_deg"], kw["path_deg"], kw["face_deg"], kw["dyn_loft_deg"],
                          club, spin_trim=trim)


@pytest.mark.parametrize("name", list(_GOOD))
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_deliver_rejects_non_finite_input(name, bad):
    with pytest.raises(ValueError, match=name):
        _deliver(**{name: bad})


@pytest.mark.parametrize(
    "name,value",
    [("club_speed_mph", 39.9), ("club_speed_mph", 140.1), ("attack_deg", -10.1), ("attack_deg", 10.1),
     ("path_deg", -15.1), ("path_deg", 15.1), ("face_deg", -15.1), ("face_deg", 15.1),
     ("dyn_loft_deg", -0.1), ("dyn_loft_deg", 65.1)],
)
def test_deliver_rejects_input_outside_the_domain(name, value):
    with pytest.raises(ValueError, match=name):
        _deliver(**{name: value})


@pytest.mark.parametrize("name", list(_GOOD))
def test_deliver_accepts_every_domain_edge(name):
    lo, hi = data.DOMAIN[name]
    for value in (lo, hi):
        kw = {name: value}
        if name == "dyn_loft_deg" and value - _GOOD["attack_deg"] < 1.0:
            continue
        if name == "attack_deg" and _GOOD["dyn_loft_deg"] - value < 1.0:
            continue
        ln = _deliver(**kw)
        assert math.isfinite(ln.spin_axis_deg) and ln.ball_speed_mph > 0.0


def test_deliver_rejects_spin_loft_under_one_degree():
    with pytest.raises(ValueError, match="dyn_loft_deg - attack_deg"):
        _deliver(attack_deg=5.0, dyn_loft_deg=5.9)
    _deliver(attack_deg=5.0, dyn_loft_deg=6.0)  # 1 deg is allowed


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan"), float("inf")])
def test_deliver_rejects_bad_spin_trim(bad):
    with pytest.raises(ValueError, match="spin_trim"):
        _deliver(spin_trim=bad)


def test_deliver_rejects_unknown_club_and_accepts_every_known_one():
    with pytest.raises(ValueError, match="club"):
        _deliver(club="2i")
    with pytest.raises(ValueError, match="club"):
        _deliver(club="Driver")
    _deliver(club=None)
    for club in data.PGA:
        _deliver(club=club)


def test_deliver_params_and_trim_are_keyword_only():
    with pytest.raises(TypeError):
        launch.deliver(92.0, -3.0, 0.0, 0.0, 20.0, "7i", None)
    with pytest.raises(TypeError):
        launch.deliver(92.0, -3.0, 0.0, 0.0, 20.0, "7i", None, 1.2)
    launch.deliver(92.0, -3.0, 0.0, 0.0, 20.0, "7i", params=None, spin_trim=1.2)


def test_outputs_carry_no_negative_zero():
    for path, face in ((0.0, 0.0), (-0.0, -0.0), (0.0, -0.0), (-0.0, 0.0)):
        ln = launch.deliver(92.0, 0.0, path, face, 20.0, "7i")
        for field in dataclasses.fields(ln):
            value = getattr(ln, field.name)
            assert math.copysign(1.0, value) == 1.0 or value != 0.0, f"{field.name} is -0.0"
    assert math.copysign(1.0, launch.swing_path(-0.0, -0.0, 49.0)) == 1.0


@pytest.mark.parametrize("attack", [0.0, 5.0, 9.0])
@pytest.mark.parametrize("f2p", [-5.0, 5.0])
def test_smallest_spin_loft_with_face_to_path(attack, f2p):
    """Dynamic loft = attack + 1: the D-plane normal lies close to horizontal, the
    axis tilt is large, and nothing ties or divides by zero."""
    ln = launch.deliver(90.0, attack, 0.0, f2p, attack + 1.0, "7i")
    mirrored = launch.deliver(90.0, attack, 0.0, -f2p, attack + 1.0, "7i")
    assert math.copysign(1.0, ln.spin_axis_deg) == math.copysign(1.0, f2p)
    assert 60.0 < abs(ln.spin_axis_deg) < 100.0
    assert mirrored.spin_axis_deg == pytest.approx(-ln.spin_axis_deg, abs=1e-9)
    assert ln.spin_loft_deg == pytest.approx(math.hypot(1.0, f2p), rel=0.02)
    f = flight.simulate(ln.ball_speed_mph, ln.launch_deg, ln.launch_dir_deg, ln.spin_rpm, ln.spin_axis_deg)
    assert f.carry_yd > 0.0


def test_dplane_normal_tie_breaks_toward_positive_ninety():
    """Exact tie: the D-plane normal is vertical, so it has no component
    along the right axis. Both orientations give +90, with no sign flip."""
    d = (1.0, 0.0, 0.0)
    for n in ((0.0, 1.0, 0.0), (0.0, -1.0, 0.0)):  # d x n is (0, 0, +1) or (0, 0, -1)
        assert launch.dplane_tilt_deg(d, n) == pytest.approx(90.0, abs=1e-9)


def test_swing_path_validates_plane_and_finiteness():
    for bad in (20.0, 80.0, 10.0, 90.0, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="plane_deg"):
            launch.swing_path(0.0, -3.0, bad)
    launch.swing_path(0.0, -3.0, 20.5)
    launch.swing_path(0.0, -3.0, 79.5)
    with pytest.raises(ValueError, match="swing_dir_deg"):
        launch.swing_path(float("nan"), -3.0, 49.0)
    with pytest.raises(ValueError, match="attack_deg"):
        launch.swing_path(0.0, float("inf"), 49.0)


def test_scale_speed_validates_speed():
    p = presets.preset("7i", "pga")
    for bad in (39.9, 140.1, float("nan"), float("inf"), -5.0):
        with pytest.raises(ValueError, match="club_speed"):
            presets.scale_speed(p, bad)
    assert presets.scale_speed(p, 40.0)["club_speed"] == 40.0
    assert presets.scale_speed(p, 140.0)["club_speed"] == 140.0


# ---------------------------------------------------------------------------
# G4 physics sanity
# ---------------------------------------------------------------------------


def _shot(p, path=0.0, face=0.0, attack=None, dyn_loft=None, club_speed=None):
    ln = launch.deliver(
        p["club_speed"] if club_speed is None else club_speed,
        p["attack"] if attack is None else attack,
        path,
        face,
        p["dyn_loft"] if dyn_loft is None else dyn_loft,
        p["club"],
        spin_trim=p["spin_trim"],
    )
    return ln, gl.fly(ln)


PLAYER_CLUBS = [(pl, c) for pl in presets.PLAYERS for c in ("driver", "5i", "7i", "pw")]


@pytest.mark.parametrize("player,club", PLAYER_CLUBS)
@pytest.mark.parametrize("path", [-6.0, -2.0, 0.0, 3.0, 8.0])
def test_face_equals_path_gives_no_curve(player, club, path):
    ln, f = _shot(presets.preset(club, player), path=path, face=path)
    assert abs(f.curve_yd) < 0.5
    assert abs(ln.spin_axis_deg) < 1e-6
    assert ln.launch_dir_deg == pytest.approx(path, abs=1e-6)


@pytest.mark.parametrize("player,club", PLAYER_CLUBS)
def test_mirrored_deliveries_mirror_the_flight(player, club):
    p = presets.preset(club, player)
    for path, face in ((3.0, -1.0), (-2.0, 4.0), (5.0, 2.0)):
        a_ln, a_f = _shot(p, path=path, face=face)
        b_ln, b_f = _shot(p, path=-path, face=-face)
        assert b_ln.launch_dir_deg == pytest.approx(-a_ln.launch_dir_deg, abs=1e-9)
        assert b_ln.spin_axis_deg == pytest.approx(-a_ln.spin_axis_deg, abs=1e-9)
        assert b_ln.launch_deg == pytest.approx(a_ln.launch_deg, abs=1e-9)
        assert b_ln.spin_rpm == pytest.approx(a_ln.spin_rpm, rel=1e-9)
        assert b_ln.ball_speed_mph == pytest.approx(a_ln.ball_speed_mph, rel=1e-9)
        assert b_f.curve_yd == pytest.approx(-a_f.curve_yd, abs=1e-6)
        assert b_f.carry_yd == pytest.approx(a_f.carry_yd, abs=1e-6)


@pytest.mark.parametrize("player,club", PLAYER_CLUBS)
def test_curve_rises_with_face_to_path(player, club):
    p = presets.preset(club, player)
    f2ps = [0.0, 1.0, 2.0, 3.0, 5.0, 7.0, 9.0]
    right = [_shot(p, path=0.0, face=x)[1].curve_yd for x in f2ps]
    left = [_shot(p, path=0.0, face=-x)[1].curve_yd for x in f2ps]
    assert all(b > a for a, b in zip(right, right[1:]))
    assert all(b < a for a, b in zip(left, left[1:]))
    # Same face-to-path made with the path instead of the face
    via_path = [_shot(p, path=-x, face=0.0)[1].curve_yd for x in f2ps]
    assert all(b > a for a, b in zip(via_path, via_path[1:]))


@pytest.mark.parametrize("player", presets.PLAYERS)
@pytest.mark.parametrize("f2p", [2.0, 5.0, -2.0, -5.0])
def test_same_face_to_path_curves_driver_more_than_irons(player, f2p):
    curve = {c: abs(_shot(presets.preset(c, player), path=0.0, face=f2p)[1].curve_yd) for c in ("driver", "6i", "pw")}
    assert curve["driver"] > curve["6i"] > curve["pw"]


def test_curve_falls_as_spin_loft_rises():
    """Design doc G4: curve falls as spin loft rises. Same delivery, more
    dynamic loft."""
    p = presets.preset("7i", "pga")
    curves = [abs(_shot(p, face=4.0, dyn_loft=dl)[1].curve_yd) for dl in (18.0, 21.0, 24.0, 27.0, 30.0)]
    assert all(b < a for a, b in zip(curves, curves[1:]))


@pytest.mark.parametrize("player,club", [("pga", "driver"), ("pga", "7i"), ("amateur", "6i"), ("lpga", "pw")])
def test_higher_club_speed_carries_farther(player, club):
    p = presets.preset(club, player)
    speeds = [p["club_speed"] * s for s in (0.80, 0.90, 1.00, 1.10)]
    carries = [_shot(presets.scale_speed(p, v))[1].carry_yd for v in speeds]
    assert all(b > a + 3.0 for a, b in zip(carries, carries[1:]))


@pytest.mark.parametrize("player", ["pga", "lpga", "amateur"])
def test_driver_steeper_attack_lowers_launch_and_raises_spin(player):
    p = presets.preset("driver", player)
    aoas = [4.0, 2.0, 0.0, -2.0, -4.0, -6.0]
    lns = [launch.deliver(p["club_speed"], a, 0.0, 0.0, p["dyn_loft"], "driver") for a in aoas]
    launches = [ln.launch_deg for ln in lns]
    spins = [ln.spin_rpm for ln in lns]
    assert all(b < a for a, b in zip(launches, launches[1:]))
    assert all(b > a for a, b in zip(spins, spins[1:]))


def test_more_dynamic_loft_raises_launch_and_spin_and_lowers_ball_speed():
    p = presets.preset("7i", "pga")
    lns = [launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, dl, "7i") for dl in (18.0, 21.0, 24.0, 27.0)]
    assert all(b.launch_deg > a.launch_deg for a, b in zip(lns, lns[1:]))
    assert all(b.spin_rpm > a.spin_rpm for a, b in zip(lns, lns[1:]))
    assert all(b.ball_speed_mph < a.ball_speed_mph for a, b in zip(lns, lns[1:]))


def test_swing_path_moves_right_as_attack_gets_steeper():
    """Anchor 5(c): with swing direction held, hitting down moves path right.
    Forum formula CP = HSP - AA * tan(90 - VSP)."""
    paths = [launch.swing_path(-2.0, aoa, 49.0) for aoa in (4.0, 2.0, 0.0, -2.0, -4.0, -6.0)]
    assert all(b > a for a, b in zip(paths, paths[1:]))
    assert launch.swing_path(-2.0, 0.0, 49.0) == -2.0
    assert launch.swing_path(0.0, -4.0, 49.0) == pytest.approx(0.869 * 4.0, abs=0.01)  # 1 / tan(49 deg) = 0.869
    assert launch.swing_path(0.0, -4.0) == launch.swing_path(0.0, -4.0, data.SWING_PLANE_DEG)
    # A flatter plane gives attack angle more pull on path
    assert launch.swing_path(0.0, -4.0, 40.0) > launch.swing_path(0.0, -4.0, 55.0)


def test_dplane_tilt_is_close_to_the_small_angle_spin_axis():
    """The exact D-plane normal tilt is close to atan2(face-to-path, spin loft).
    It differs by cos(dynamic loft) on the face-to-path term (about 3 percent at
    20 deg of loft), because a lofted face tilts less sideways per degree."""
    tilt = launch.dplane_tilt_deg(launch.club_direction(0.0, -3.0), launch.face_normal(4.0, 20.0))
    assert tilt == pytest.approx(math.degrees(math.atan2(4.0, 23.0)), rel=0.04)
    flat = launch.dplane_tilt_deg(launch.club_direction(2.0, 0.0), launch.face_normal(2.0, 15.0))
    assert flat == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Golfer sanity cases: right-handed, PGA 7-iron preset. Full shot naming
# comes with the classifier in the next task.
# ---------------------------------------------------------------------------

P7 = presets.preset("7i", "pga")


def test_golfer_dead_straight():
    ln, f = _shot(P7)
    assert abs(ln.launch_dir_deg) < 0.5
    assert abs(f.curve_yd) < 0.5


def test_golfer_push_draw_finishes_on_line():
    """Face +2, path +5: starts right, curves left, finishes near the target line."""
    ln, f = _shot(P7, path=5.0, face=2.0)
    assert ln.launch_dir_deg > 0.0
    assert f.curve_yd < 0.0
    assert abs(f.side_yd) <= 6.0


def test_golfer_face_and_path_both_left_starts_left_no_curve():
    ln, f = _shot(P7, path=-3.0, face=-3.0)
    assert ln.launch_dir_deg == pytest.approx(-3.0, abs=0.3)
    assert abs(f.curve_yd) < 0.5


def test_golfer_push_slice():
    """Face +4, path -3: starts right, curves right."""
    ln, f = _shot(P7, path=-3.0, face=4.0)
    assert ln.launch_dir_deg > 0.0
    assert f.curve_yd > 10.0


def test_golfer_pull_hook():
    """Face -4, path +2: starts left, curves left."""
    ln, f = _shot(P7, path=2.0, face=-4.0)
    assert ln.launch_dir_deg < 0.0
    assert f.curve_yd < -8.0


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------


def test_club_ladder_is_the_data_ladder():
    assert presets.CLUBS == tuple(data.PGA)
    assert presets.CLUBS == ("driver", "3w", "5w", "hybrid", "3i", "4i", "5i", "6i", "7i", "8i", "9i", "pw")


def test_amateur_anchors_match_the_log():
    d = presets.preset("driver", "amateur")
    assert (d["club_speed"], d["attack"], d["dyn_loft"]) == (94.0, -1.8, 15.1)  # Combine, average golfer (14.5)
    assert not d["modeled"]
    s6 = presets.preset("6i", "amateur")
    assert (s6["club_speed"], s6["attack"], s6["dyn_loft"]) == (80.0, -3.2, 22.4)  # Optimizer defaults
    pw = presets.preset("pw", "amateur")
    assert (pw["club_speed"], pw["attack"], pw["dyn_loft"]) == (72.0, -3.9, 36.7)
    assert s6["modeled"] and pw["modeled"] and "Optimizer" in s6["source"]


def test_amateur_ladder_is_ordered_and_modeled():
    ps = [presets.preset(c, "amateur") for c in presets.CLUBS]
    speeds = [p["club_speed"] for p in ps]
    assert all(b < a for a, b in zip(speeds, speeds[1:]))
    assert all(p["modeled"] for p in ps[1:])
    # Every club sits between the driver and the PW on speed, attack angle and loft
    assert all(72.0 <= p["club_speed"] <= 94.0 and -3.9 <= p["attack"] <= -1.8 and 15.1 <= p["dyn_loft"] <= 36.7
               for p in ps)


def test_amateur_dynamic_loft_never_falls_from_driver_through_pw():
    """Loft is non-decreasing driver through PW and rising at every step from the
    hybrid on. Recorded exception: the 3-wood shares the driver's loft (15.1).
    The PGA shape has the driver loft (12.7) above the 3-wood (12.4), so the
    interpolation position clamps to 0 and the 3-wood sits on the driver."""
    dls = {c: presets.preset(c, "amateur")["dyn_loft"] for c in presets.CLUBS}
    ordered = [dls[c] for c in presets.CLUBS]
    assert all(b >= a for a, b in zip(ordered, ordered[1:]))
    assert dls["3w"] == dls["driver"] < dls["5w"]
    tail = [dls[c] for c in presets.CLUBS[3:]]
    assert all(b > a for a, b in zip(tail, tail[1:]))


def test_amateur_slower_than_pga_on_every_club():
    for c in presets.CLUBS:
        assert presets.preset(c, "amateur")["club_speed"] < presets.preset(c, "pga")["club_speed"]


@pytest.mark.parametrize("player,tour", [("pga", "PGA"), ("lpga", "LPGA")])
def test_tour_presets_come_from_the_tables(player, tour):
    for club, r in data.TOURS[tour].items():
        p = presets.preset(club, player)
        assert p["club_speed"] == r["club_speed_mph"]
        assert p["attack"] == r["attack_deg"]
        assert p["dyn_loft"] == data.TOUR_DYN_LOFT[(tour, club)]
        assert p["path"] == 0.0 and p["face"] == 0.0
        assert not p["modeled"]


def test_lpga_three_iron_falls_back_to_four_iron():
    p = presets.preset("3i", "lpga")
    q = presets.preset("4i", "lpga")
    assert p["club"] == "4i"
    assert "no 3-iron" in p["note"]
    assert (p["club_speed"], p["attack"], p["dyn_loft"]) == (q["club_speed"], q["attack"], q["dyn_loft"])
    assert presets.preset("3i", "pga")["note"] == ""


def test_scale_speed_changes_only_speed():
    p = presets.preset("7i", "pga")
    q = presets.scale_speed(p, 80.0)
    assert q["club_speed"] == 80.0
    assert p["club_speed"] == 92.0
    assert {k: v for k, v in q.items() if k != "club_speed"} == {k: v for k, v in p.items() if k != "club_speed"}


def test_unknown_inputs_raise():
    with pytest.raises(ValueError):
        presets.preset("driver", "senior")
    with pytest.raises(ValueError):
        presets.preset("2i", "pga")


def test_every_preset_flies():
    """Every club and player produces a finite, landing shot."""
    for pl in presets.PLAYERS:
        for c in presets.CLUBS:
            _, f = _shot(presets.preset(c, pl))
            assert 60.0 < f.carry_yd < 330.0
            assert math.isclose(f.curve_yd, 0.0, abs_tol=0.5)


# ---------------------------------------------------------------------------
# Spin trim: a preset-level multiplier on spin only (MODELED).
# ---------------------------------------------------------------------------


def test_spin_trim_multiplies_spin_only():
    p = presets.preset("7i", "pga")
    args = (p["club_speed"], p["attack"], 2.0, 4.0, p["dyn_loft"], "7i")
    a = launch.deliver(*args)
    b = launch.deliver(*args, spin_trim=1.25)
    assert b.spin_rpm == pytest.approx(1.25 * a.spin_rpm, rel=1e-12)
    assert (b.ball_speed_mph, b.launch_deg, b.launch_dir_deg, b.spin_axis_deg, b.spin_loft_deg) == (
        a.ball_speed_mph, a.launch_deg, a.launch_dir_deg, a.spin_axis_deg, a.spin_loft_deg)


@pytest.mark.parametrize(
    "player,club",
    [pytest.param(p, c, marks=_marks(PRESET_MISSES, f"{p}/{c}", "preset"), id=f"{p}-{c}") for p, c in gl.preset_keys()],
)
def test_preset_reproduces_its_published_row(player, club):
    """Spin within 1 percent for every preset (the trim makes it so). Launch
    within 1 deg and ball speed within 2 percent: for the amateur anchors here,
    and for a Tour preset as the G3 row's own numbers (recorded once, under
    "g3", so the LPGA 8 iron ball speed miss is not listed twice)."""
    err_launch, err_spin, err_ball = gl.preset_errors(player, club)
    assert abs(err_spin) <= gl.PRESET_TOL["spin_pct"]
    if player == "amateur":
        assert abs(err_launch) <= gl.PRESET_TOL["launch_deg"]
        assert abs(err_ball) <= gl.PRESET_TOL["ball_pct"]
    else:
        g3 = gl.g3_row("PGA" if player == "pga" else "LPGA", club)
        assert err_launch == pytest.approx(g3.launch_err_deg, abs=1e-3)
        assert err_ball == pytest.approx(100.0 * g3.ball_err_frac, abs=1e-3)


def test_trims_are_between_0p6_and_1p6():
    for player in presets.PLAYERS:
        for club in presets.CLUBS:
            trim = presets.preset(club, player)["spin_trim"]
            assert 0.6 <= trim <= 1.6, f"{player}/{club}: trim {trim:.3f}"


def test_scale_speed_keeps_the_trim():
    p = presets.preset("driver", "amateur")
    assert presets.scale_speed(p, 100.0)["spin_trim"] == p["spin_trim"]


def test_amateur_trim_interpolates_between_anchors():
    a = {c: presets.preset(c, "amateur")["spin_trim"] for c in presets.CLUBS}
    for c in ("3w", "5w", "hybrid", "3i", "4i", "5i"):
        assert min(a["driver"], a["6i"]) <= a[c] <= max(a["driver"], a["6i"])
    for c in ("7i", "8i", "9i"):
        assert min(a["6i"], a["pw"]) <= a[c] <= max(a["6i"], a["pw"])


def test_lpga_three_iron_trim_follows_the_four_iron():
    assert presets.preset("3i", "lpga")["spin_trim"] == presets.preset("4i", "lpga")["spin_trim"]


# ---------------------------------------------------------------------------
# Golden vectors for the JS parity test (tests/golden_launch.json)
# ---------------------------------------------------------------------------


def test_golden_vectors_match_the_model():
    """The file the JS port tests against. Regenerate with
    `calibrate_launch.py --write-golden` after any model or preset change."""
    with open(gl.GOLDEN_PATH) as fh:
        recorded = json.load(fh)
    assert recorded["dt"] == gl.GOLDEN_DT
    cases = gl.golden_cases()
    assert [c["id"] for c in recorded["cases"]] == [c[0] for c in cases]
    assert 36 <= len(cases) <= 44 and len({c[0] for c in cases}) == len(cases)
    for rec, case in zip(recorded["cases"], cases):
        live = gl.golden_entry(*case)
        assert rec["args"] == live["args"], rec["id"]
        assert rec["kwargs"] == live["kwargs"], rec["id"]
        assert rec["launch"] == pytest.approx(live["launch"], rel=1e-9, abs=1e-9), rec["id"]
        assert rec["flight"] == pytest.approx(live["flight"], rel=1e-9, abs=1e-9), rec["id"]
