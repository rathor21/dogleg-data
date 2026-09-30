"""Tests for loft-follows-attack (task 004-physics, ADR 0004 addendum 4).

Off the ground, hitting up adds loft (data.LOFT_PER_ATTACK, MODELED, 1.4 degrees per
degree): spin loft and spin rise, smash falls and the shot flies shorter. The
independent-slider path (fixed loft, moving attack) stays and behaves as before.
"""

import pytest

import chart
import data
import flight
import presets

IRONS = ("3i", "4i", "5i", "6i", "7i", "8i", "9i", "pw")
FOLLOWERS = data.LOFT_FOLLOWS_ATTACK_CLUBS


def _walk(club, player, attacks, follows=True):
    p = presets.preset(club, player)
    out = []
    for a in attacks:
        kwargs = {"attack": a}
        if follows:
            kwargs["dyn_loft"] = presets.loft_for_attack(club, player, a)
        ln, f = presets.fly(p, **kwargs)
        out.append((f.carry_yd, flight.roll(f), ln.smash, ln.spin_rpm, ln.launch_deg))
    return out


# ---------------------------------------------------------------------------
# The rule
# ---------------------------------------------------------------------------


def test_constants():
    assert data.LOFT_PER_ATTACK == 1.4
    assert set(data.LOFT_FOLLOWS_ATTACK_CLUBS) == set(data.PGA) - {"driver"}
    assert data.DRIVER_NATURAL_SLOPE == 1.0


@pytest.mark.parametrize("player", presets.PLAYERS)
@pytest.mark.parametrize("club", FOLLOWERS)
def test_loft_is_the_preset_loft_at_the_preset_attack_and_moves_1_4_per_degree(club, player):
    p = presets.preset(club, player)
    assert presets.loft_for_attack(club, player, p["attack"]) == pytest.approx(p["dyn_loft"])
    a = p["attack"] + 2.0
    assert presets.loft_for_attack(club, player, a) - p["dyn_loft"] == pytest.approx(2.0 * 1.4)
    a = p["attack"] - 1.5
    assert presets.loft_for_attack(club, player, a) - p["dyn_loft"] == pytest.approx(-1.5 * 1.4)


@pytest.mark.parametrize("player", presets.PLAYERS)
def test_the_driver_keeps_the_chart_rule(player):
    p = presets.preset("driver", player)
    for a in (-4.0, 0.0, 3.0, 5.0, 8.0):
        assert presets.loft_for_attack("driver", player, a) == pytest.approx(
            chart.optimal_loft(p["club_speed"], a).dyn_loft_deg)


@pytest.mark.parametrize("player", presets.PLAYERS)
@pytest.mark.parametrize("club", presets.CLUBS)
def test_every_result_is_a_loft_deliver_accepts(club, player):
    lo, hi = data.DOMAIN["attack_deg"]
    for a in (lo, -6.0, 0.0, 6.0, hi):
        dl = presets.loft_for_attack(club, player, a)
        assert dl - a >= data.DOMAIN["min_spin_loft_deg"] - 1e-12
        assert dl <= data.DOMAIN["dyn_loft_deg"][1]
        presets.fly(presets.preset(club, player), attack=a, dyn_loft=dl)  # deliver does not raise


def test_bad_inputs_raise():
    for bad in (float("nan"), float("inf"), 10.5, -10.5):
        with pytest.raises(ValueError, match="attack"):
            presets.loft_for_attack("7i", "pga", bad)
    with pytest.raises(ValueError, match="club"):
        presets.loft_for_attack("2i", "pga", 0.0)
    with pytest.raises(ValueError, match="player"):
        presets.loft_for_attack("7i", "scratch", 0.0)


def test_presets_and_ideals_are_untouched():
    """They sit at the preset attack, where the rule returns the preset loft."""
    for player in presets.PLAYERS:
        for club in FOLLOWERS:
            p = presets.preset(club, player)
            assert p["ideal"]["dyn_loft"] == p["dyn_loft"] and p["ideal"]["attack"] == p["attack"]


# ---------------------------------------------------------------------------
# What it does to the shot
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("player", ["pga", "lpga"])
@pytest.mark.parametrize("club", IRONS)
def test_hitting_up_shortens_tour_irons_from_the_preset_attack_to_plus_3(club, player):
    p = presets.preset(club, player)
    attacks = [p["attack"] + (3.0 - p["attack"]) * i / 5 for i in range(6)]
    rows = _walk(club, player, attacks)
    carry, total = [r[0] for r in rows], [r[1] for r in rows]
    assert all(b < a for a, b in zip(carry, carry[1:])), (club, player, carry)
    assert all(b < a for a, b in zip(total, total[1:])), (club, player, total)


@pytest.mark.parametrize("player", presets.PLAYERS)
@pytest.mark.parametrize("club", FOLLOWERS)
def test_total_falls_and_smash_falls_and_spin_rises_with_attack(club, player):
    attacks = [-8.0, -6.0, -4.0, -2.0, 0.0, 2.0, 4.0]
    rows = _walk(club, player, attacks)
    # Total falls from the preset attack up. Far below it a slow player's delofted wood or hybrid
    # launches too low and loses total from the other side (the 3-wood peaks between -6 and -4).
    p = presets.preset(club, player)
    up = _walk(club, player, [p["attack"] + i * (4.0 - p["attack"]) / 6 for i in range(7)])
    assert all(b[1] < a[1] for a, b in zip(up, up[1:])), "total"
    assert all(b[2] < a[2] for a, b in zip(rows, rows[1:])), "smash"
    assert all(b[3] > a[3] for a, b in zip(rows, rows[1:])), "spin"
    assert all(b[4] > a[4] for a, b in zip(rows, rows[1:])), "launch"


def test_the_amateur_7_iron_carry_curve_peaks_at_or_below_zero_attack():
    attacks = [a / 2.0 for a in range(-16, 13)]  # -8 to +6
    carry = [r[0] for r in _walk("7i", "amateur", attacks)]
    peak = attacks[carry.index(max(carry))]
    assert peak <= 0.0
    assert carry[attacks.index(0.0)] > carry[attacks.index(3.0)]


def test_the_pga_7_iron_slope_matches_the_foresight_chart_at_90_mph():
    """Foresight 7 iron chart (Anchor 9): 183.4 yd at attack -6 and 169.5 at +2 at 90 mph head
    speed, -1.7 yd per degree. Within 1 yd per degree."""
    p = presets.scale_speed(presets.preset("7i", "pga"), 90.0)
    carry = {}
    for a in (-6.0, 2.0):
        _, f = presets.fly(p, attack=a, dyn_loft=presets.loft_for_attack("7i", "pga", a))
        carry[a] = f.carry_yd
    slope = (carry[2.0] - carry[-6.0]) / 8.0
    assert slope == pytest.approx(-1.7, abs=1.0)
    assert slope < 0.0


# ---------------------------------------------------------------------------
# The independent path stays
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("club", IRONS)
def test_the_independent_sliders_still_raise_carry_with_attack_at_fixed_loft(club):
    """Coupling off: loft held at the preset, attack moving. Hitting up cuts spin loft, so carry
    and smash rise. This path is unchanged."""
    p = presets.preset(club, "pga")
    rows = _walk(club, "pga", [-6.0, -3.0, 0.0, 3.0], follows=False)
    assert all(b[0] > a[0] for a, b in zip(rows, rows[1:]))
    assert all(b[2] > a[2] for a, b in zip(rows, rows[1:]))
    assert all(b[3] < a[3] for a, b in zip(rows, rows[1:]))
    ln, f = presets.fly(p)  # the preset itself is the same call as before
    assert f.carry_yd == pytest.approx(presets.fly(p, attack=p["attack"], dyn_loft=p["dyn_loft"])[1].carry_yd)


def test_the_two_paths_agree_at_the_preset_attack():
    for club in FOLLOWERS:
        p = presets.preset(club, "pga")
        a = _walk(club, "pga", [p["attack"]], follows=True)[0]
        b = _walk(club, "pga", [p["attack"]], follows=False)[0]
        assert a == pytest.approx(b, rel=1e-12)
