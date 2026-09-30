"""Tests for the face-to-loft coupling (task 004-physics, ADR 0004 addendum 3).

    dyn_loft_effective = dyn_loft_input + kappa(club) * (face - path),  kappa = cot(lie)

Closing the face to the path removes loft (a draw flies lower, with less spin and
more run), opening it adds loft (a fade flies higher, with more spin and less run).
A face equal to the path leaves the loft alone, so pure pulls and pure pushes stay
exact mirrors.
"""

import math

import pytest

import data
import flight
import launch
import presets

CASES = [(club, player) for player in presets.PLAYERS for club in presets.CLUBS]


def _fly(p, path, face, **kw):
    ln, f = presets.fly(p, path=path, face=face, **kw)
    return ln, f, flight.roll(f)


# ---------------------------------------------------------------------------
# kappa and the lie angles
# ---------------------------------------------------------------------------


def test_kappa_is_cot_of_the_lie_angle_for_every_club():
    assert set(data.KAPPA) == set(data.LIE_DEG) == set(data.PGA)
    for club, lie in data.LIE_DEG.items():
        assert data.KAPPA[club] == pytest.approx(1.0 / math.tan(math.radians(lie)), rel=1e-12)
        assert 0.45 < data.KAPPA[club] < 0.7  # cot(56 to 64 deg), below the 0.6 shaft-lean-free roll ceiling plus a margin


def test_lie_angles_follow_the_spec_sheets():
    """Anchor 8, Titleist custom options 2025 (irons, GT2 driver, fairway and hybrid rows)."""
    lie = data.LIE_DEG
    assert lie["driver"] == 58.5 and lie["3w"] == 56.5 and lie["5w"] == 57.5 and lie["hybrid"] == 57.0
    irons = [lie[c] for c in ("3i", "4i", "5i", "6i", "7i", "8i", "9i", "pw")]
    assert irons == [61.0, 61.5, 62.0, 62.5, 63.0, 63.5, 64.0, 64.0]
    kappas = [data.KAPPA[c] for c in ("3i", "4i", "5i", "6i", "7i", "8i", "9i", "pw")]
    assert kappas == sorted(kappas, reverse=True)  # longer clubs sit flatter and couple more
    assert data.KAPPA["driver"] > data.KAPPA["3i"] > data.KAPPA["pw"] - 1e-12


# ---------------------------------------------------------------------------
# deliver: the effective loft and the two loft fields
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("club", list(data.PGA))
def test_effective_loft_is_input_plus_kappa_times_face_to_path(club):
    ln = launch.deliver(95.0, -2.0, 3.0, -1.0, 25.0, club)
    assert ln.dyn_loft_input_deg == 25.0
    assert ln.dyn_loft_deg == pytest.approx(25.0 + data.KAPPA[club] * (-1.0 - 3.0))
    assert ln.face_to_path_deg == -4.0


def test_loft_is_unchanged_when_face_equals_path():
    for club in data.PGA:
        for x in (-6.0, 0.0, 4.0):
            ln = launch.deliver(95.0, -2.0, x, x, 25.0, club)
            assert ln.dyn_loft_deg == ln.dyn_loft_input_deg == 25.0


def test_an_unnamed_club_has_no_coupling():
    ln = launch.deliver(95.0, -2.0, 3.0, -1.0, 25.0)
    assert ln.dyn_loft_deg == ln.dyn_loft_input_deg == 25.0


def test_effective_loft_is_held_to_the_spin_loft_floor_and_the_domain():
    floor = data.DOMAIN["min_spin_loft_deg"]
    ln = launch.deliver(95.0, 6.0, 15.0, -15.0, 8.0, "driver")  # 8 - 0.61 * 30 would be negative
    assert ln.dyn_loft_deg == pytest.approx(6.0 + floor)
    top = launch.deliver(95.0, 0.0, -15.0, 15.0, 60.0, "pw")
    assert top.dyn_loft_deg == data.DOMAIN["dyn_loft_deg"][1]


def test_the_input_check_still_uses_the_input_loft():
    with pytest.raises(ValueError, match="dyn_loft_deg"):
        launch.deliver(95.0, 0.0, 0.0, 0.0, 70.0, "7i")
    with pytest.raises(ValueError, match="dyn_loft_deg - attack_deg"):
        launch.deliver(95.0, 5.0, 0.0, 0.0, 5.5, "7i")


def test_downstream_quantities_use_the_effective_loft():
    """A closed face gives the same launch and spin as a square face with the loft lowered by the coupling."""
    for club in ("driver", "7i"):
        closed = launch.deliver(95.0, -2.0, 0.0, -4.0, 25.0, club)
        eq = launch.deliver(95.0, -2.0, 0.0, -4.0, 25.0 - data.KAPPA[club] * 4.0, None)  # no coupling, loft pre-lowered
        # same effective loft: the spin loft and smash are equal, so are ball speed (class factors aside)
        assert closed.spin_loft_deg == pytest.approx(eq.spin_loft_deg, rel=1e-9)
        assert closed.smash == pytest.approx(eq.smash, rel=1e-9)
        assert closed.launch_deg < launch.deliver(95.0, -2.0, 0.0, 0.0, 25.0, club).launch_deg


# ---------------------------------------------------------------------------
# Draw against fade, pull hook against push slice, for every club and player
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("club,player", CASES)
def test_a_draw_flies_lower_with_less_spin_and_more_total_than_a_fade(club, player):
    p = presets.preset(club, player)
    ln_d, f_d, tot_d = _fly(p, path=4.0, face=0.0)  # face-to-path -4, a draw
    ln_f, f_f, tot_f = _fly(p, path=-4.0, face=0.0)  # face-to-path +4, a fade
    assert ln_d.dyn_loft_deg < ln_d.dyn_loft_input_deg < ln_f.dyn_loft_deg
    assert f_d.max_height_yd < f_f.max_height_yd
    assert ln_d.spin_rpm < ln_f.spin_rpm
    assert f_d.land_angle_deg < f_f.land_angle_deg
    assert tot_d > tot_f


@pytest.mark.parametrize("club,player", CASES)
def test_a_pull_hook_totals_more_than_a_push_slice(club, player):
    p = presets.preset(club, player)
    _, f_h, tot_h = _fly(p, path=-2.0, face=-6.0)  # pull hook, face-to-path -4
    _, f_s, tot_s = _fly(p, path=2.0, face=6.0)  # push slice, face-to-path +4
    assert tot_h > tot_s
    assert f_h.max_height_yd < f_s.max_height_yd


@pytest.mark.parametrize("club,player", CASES)
def test_pure_pulls_and_pushes_stay_equal(club, player):
    """Face = path: no face-to-path, no loft change, an exact mirror. The physics gives equal
    carry here too (research file, topic 1), the coupling does not separate them."""
    p = presets.preset(club, player)
    for x in (2.0, 4.0, 6.0):
        ln_l, f_l, tot_l = _fly(p, path=-x, face=-x)
        ln_r, f_r, tot_r = _fly(p, path=x, face=x)
        assert ln_l.dyn_loft_deg == ln_r.dyn_loft_deg == ln_l.dyn_loft_input_deg
        assert f_l.carry_yd == pytest.approx(f_r.carry_yd, abs=1e-6)
        assert f_l.max_height_yd == pytest.approx(f_r.max_height_yd, abs=1e-6)
        assert ln_l.spin_rpm == pytest.approx(ln_r.spin_rpm, rel=1e-12)
        assert tot_l == pytest.approx(tot_r, abs=1e-6)
        assert f_l.side_yd == pytest.approx(-f_r.side_yd, abs=1e-6)


@pytest.mark.parametrize("club,player", CASES)
def test_draw_and_fade_are_no_longer_mirrors(club, player):
    p = presets.preset(club, player)
    _, f_d, tot_d = _fly(p, path=4.0, face=0.0)
    _, f_f, tot_f = _fly(p, path=-4.0, face=0.0)
    assert abs(tot_d - tot_f) > 1.0


def test_the_pga_driver_and_7_iron_numbers():
    """Records the numbers the ADR quotes: PGA driver at 115 mph and PGA 7 iron at 92 mph, path and
    face split as stated, carry, height, spin and total."""
    drv = presets.preset("driver", "pga")
    _, f_d, tot_d = _fly(drv, path=4.0, face=0.0)
    _, f_f, tot_f = _fly(drv, path=-4.0, face=0.0)
    assert f_d.carry_yd < f_f.carry_yd  # a closed driver face carries less and runs much farther
    assert tot_d - tot_f > 20.0
    seven = presets.preset("7i", "pga")
    _, f7_d, tot7_d = _fly(seven, path=4.0, face=0.0)
    _, f7_f, tot7_f = _fly(seven, path=-4.0, face=0.0)
    assert f7_d.carry_yd > f7_f.carry_yd  # a closed iron face flies farther in carry too
    assert tot7_d - tot7_f > 10.0


# ---------------------------------------------------------------------------
# The TrackMan draw against fade example (a check, not a fit)
# ---------------------------------------------------------------------------


def test_trackman_draw_fade_example():
    """TrackMan blog (Stickney, 2016), one R15 driver: fade 15.0 deg dynamic loft, 3,768 rpm, 105.6 ft,
    42.9 deg landing, 240.8 yd carry; draw 10.5 deg, 2,643 rpm, 63.6 ft, 28.8 deg, 245.7 yd carry, and
    almost 20 yd more run. The 4.5 deg loft gap needs a face-to-path swing of 4.5 / kappa = 7.3 deg
    (plus and minus 3.7). The PGA driver at trim 1.0 (the chart's own strike) reproduces the direction of
    every difference and lands close to the sizes."""
    k = data.KAPPA["driver"]
    x = 4.5 / (2.0 * k)
    assert 2 * x == pytest.approx(7.34, abs=0.01)
    p = presets.preset("driver", "pga")
    common = dict(dyn_loft=12.75, spin_trim=1.0)
    ln_d, f_d, tot_d = _fly(p, path=x, face=0.0, **common)  # face-to-path -x
    ln_f, f_f, tot_f = _fly(p, path=-x, face=0.0, **common)
    assert ln_f.dyn_loft_deg - ln_d.dyn_loft_deg == pytest.approx(4.5, abs=0.01)
    assert (ln_d.dyn_loft_deg, ln_f.dyn_loft_deg) == pytest.approx((10.5, 15.0), abs=0.01)
    spin_gap = ln_f.spin_rpm - ln_d.spin_rpm
    assert 800.0 < spin_gap < 1400.0  # TrackMan 1,125
    height_gap_ft = 3.0 * (f_f.max_height_yd - f_d.max_height_yd)
    assert 30.0 < height_gap_ft < 70.0  # TrackMan 42
    land_gap = f_f.land_angle_deg - f_d.land_angle_deg
    assert 8.0 < land_gap < 18.0  # TrackMan 14.1
    run_gap = (tot_d - f_d.carry_yd) - (tot_f - f_f.carry_yd)
    assert 10.0 < run_gap < 30.0  # TrackMan "almost 20 yd"
    assert abs(f_d.carry_yd - f_f.carry_yd) < 12.0  # TrackMan: draw 4.9 yd farther in carry
