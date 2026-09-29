"""Tests for ideals.py (task 004.4): ideal bands for the TrackMan-style tiles."""

import pytest

import os
import re

import chart
import data
import flight
import ideals
import launch
import presets

CASES = [(c, p) for p in presets.PLAYERS for c in presets.CLUBS]

# Metrics where the model's own ideal delivery falls outside its band. Recorded,
# not fudged. Strict: an entry that starts passing, or a new miss, fails. Empty:
# the driver's launch and spin bands span the TrackMan carry chart, the TrackMan
# total chart and PING, so the balanced-loft ideal driver sits inside them.
KNOWN_EXCEPTIONS = set()


def _metrics(club, player):
    """Model outputs at the ideal delivery, at the preset club speed."""
    p = presets.preset(club, player)["ideal"]
    ln, f = presets.fly(p)
    return {
        "club_speed": p["club_speed"], "attack_deg": p["attack"], "club_path_deg": p["path"], "face_deg": p["face"],
        "face_to_path_deg": ln.face_to_path_deg, "dyn_loft_deg": p["dyn_loft"], "spin_loft_deg": ln.spin_loft_deg,
        "ball_speed_mph": ln.ball_speed_mph, "smash": ln.smash, "launch_deg": ln.launch_deg,
        "launch_dir_deg": ln.launch_dir_deg, "spin_rpm": ln.spin_rpm, "spin_axis_deg": ln.spin_axis_deg,
        "max_height_yd": f.max_height_yd, "land_angle_deg": f.land_angle_deg, "carry_yd": f.carry_yd,
        "total_yd": flight.roll(f), "side_yd": f.side_yd, "curve_yd": f.curve_yd,
    }


def _inside(band, v):
    return (band["lo"] is None or v >= band["lo"] - 1e-9) and (band["hi"] is None or v <= band["hi"] + 1e-9)


def test_every_metric_has_a_band():
    b = ideals.ideal_bands("7i", "pga")
    assert set(b) == set(ideals.METRICS)
    assert len(ideals.METRICS) == 19
    for m, band in b.items():
        assert {"lo", "hi", "target", "source", "modeled"} <= set(band), m
        assert band["source"], m
        if band["lo"] is not None and band["hi"] is not None:
            assert band["lo"] <= band["target"] <= band["hi"], m


def test_exceptions_helper_matches_the_record():
    found = {(e["club"], e["player"], e["metric"]) for e in ideals.exceptions()}
    assert found == KNOWN_EXCEPTIONS


def test_ideal_preset_sits_inside_its_own_bands():
    misses = set()
    for club, player in CASES:
        bands = ideals.ideal_bands(club, player)
        for metric, v in _metrics(club, player).items():
            if not _inside(bands[metric], v):
                misses.add((club, player, metric))
    assert misses == KNOWN_EXCEPTIONS


def test_non_driver_bands_follow_the_stated_widths():
    b = ideals.ideal_bands("7i", "pga")
    m = _metrics("7i", "pga")
    assert (b["club_path_deg"]["lo"], b["club_path_deg"]["hi"]) == (-2.0, 2.0)
    assert (b["face_deg"]["lo"], b["face_deg"]["hi"]) == (-1.0, 1.0)
    assert (b["face_to_path_deg"]["lo"], b["face_to_path_deg"]["hi"]) == (-1.5, 1.5)
    assert (b["launch_dir_deg"]["lo"], b["launch_dir_deg"]["hi"]) == (-2.0, 2.0)
    assert (b["spin_axis_deg"]["lo"], b["spin_axis_deg"]["hi"]) == (-2.0, 2.0)
    assert b["launch_deg"]["hi"] - b["launch_deg"]["lo"] == pytest.approx(3.0)
    assert b["launch_deg"]["target"] == pytest.approx(m["launch_deg"])
    assert b["spin_rpm"]["lo"] == pytest.approx(0.9 * m["spin_rpm"])
    assert b["spin_rpm"]["hi"] == pytest.approx(1.1 * m["spin_rpm"])
    assert b["max_height_yd"]["hi"] - b["max_height_yd"]["lo"] == pytest.approx(6.0)
    assert b["land_angle_deg"]["lo"] == pytest.approx(m["land_angle_deg"] - 3.0) and b["land_angle_deg"]["hi"] is None
    assert b["smash"]["lo"] == pytest.approx(m["smash"] - 0.03) and b["smash"]["hi"] is None
    assert b["attack_deg"]["hi"] - b["attack_deg"]["lo"] == pytest.approx(3.0)
    assert b["dyn_loft_deg"]["hi"] - b["dyn_loft_deg"]["lo"] == pytest.approx(4.0)
    assert b["spin_loft_deg"]["hi"] - b["spin_loft_deg"]["lo"] == pytest.approx(4.0)
    assert b["side_yd"]["hi"] == pytest.approx(0.05 * m["carry_yd"])
    assert b["curve_yd"]["hi"] == pytest.approx(0.04 * m["carry_yd"])
    assert b["carry_yd"]["hi"] == pytest.approx(1.03 * m["carry_yd"])
    assert b["ball_speed_mph"]["lo"] == pytest.approx(0.97 * m["ball_speed_mph"])


def test_sourced_and_modeled_flags():
    b = ideals.ideal_bands("7i", "pga")
    assert b["launch_dir_deg"]["modeled"] is False and "What is Launch Direction?" in b["launch_dir_deg"]["source"]
    assert b["spin_axis_deg"]["modeled"] is False and "What is Spin Axis?" in b["spin_axis_deg"]["source"]
    assert all(band["modeled"] for m, band in b.items() if m not in ("launch_dir_deg", "spin_axis_deg"))


def test_published_values_are_recorded_where_they_exist():
    b = ideals.ideal_bands("7i", "pga")
    assert b["launch_deg"]["published"] == data.PGA["7i"]["launch_deg"]
    assert b["carry_yd"]["published"] == 176 and b["spin_rpm"]["published"] == 7124
    assert "published" not in b["dyn_loft_deg"]  # only the driver and 6 iron are published
    assert ideals.ideal_bands("6i", "pga")["dyn_loft_deg"]["published"] == 20.2
    assert ideals.ideal_bands("driver", "lpga")["spin_loft_deg"]["published"] == 15.0
    assert ideals.ideal_bands("driver", "amateur")["spin_rpm"]["published"] == 3275
    assert "published" not in ideals.ideal_bands("7i", "amateur")["spin_rpm"]
    assert ideals.ideal_bands("3i", "lpga")["carry_yd"]["published"] == data.LPGA["4i"]["carry_yd"]  # 4 iron stands in


def test_club_speed_scales_ball_speed_and_carry_only():
    base = ideals.ideal_bands("7i", "pga")
    slow = ideals.ideal_bands("7i", "pga", club_speed=80.0)
    assert slow["ball_speed_mph"]["target"] == pytest.approx(base["ball_speed_mph"]["target"] * 80.0 / 92.0)
    assert slow["carry_yd"]["target"] < base["carry_yd"]["target"]
    assert slow["side_yd"]["hi"] == pytest.approx(0.05 * slow["carry_yd"]["target"])
    for m in ("launch_deg", "spin_rpm", "max_height_yd", "dyn_loft_deg", "smash", "club_speed"):
        assert slow[m] == base[m], m


def test_club_speed_outside_the_domain_raises():
    with pytest.raises(ValueError):
        ideals.ideal_bands("7i", "pga", club_speed=10.0)


def test_explicit_preset_speed_and_attack_match_the_defaults():
    """The default club speed is the preset's and the default attack is the ideal's
    (+4 for the driver, the preset's for every other club)."""
    for club in ("driver", "7i"):
        p = presets.preset(club, "pga")
        assert (ideals.ideal_bands(club, "pga", p["club_speed"], p["ideal"]["attack"])
                == ideals.ideal_bands(club, "pga"))


# ---------------------------------------------------------------------------
# Driver optimizer lookups
# ---------------------------------------------------------------------------


def test_trackman_grid_points_read_back_exactly():
    for row in data.TRACKMAN_CARRY_2010:
        assert ideals.trackman_carry_2010(row[0], row[1]) == pytest.approx((row[3], row[4]))
    for row in data.TRACKMAN_TOTAL_2010:
        assert ideals.trackman_total_2010(row[0], row[1]) == pytest.approx((row[3], row[4]))
    assert ideals.trackman_total_2010(115, 5) == pytest.approx((10.7, 1681))
    assert ideals.trackman_carry_2010(115, 0) == pytest.approx((9.8, 2919))


def test_ping_grid_points_read_back_exactly():
    for bs, cells in data.PING_2019.items():
        for aoa, cell in zip(data.PING_2019_AOA_DEG, cells):
            assert ideals.ping_2019(bs, aoa) == pytest.approx(cell)
    assert ideals.ping_2019(170, -2) == pytest.approx((9.6, 2750))


def test_optimizer_lookups_interpolate_and_clamp():
    lo, hi = ideals.trackman_carry_2010(112.5, 0)
    assert lo == pytest.approx(0.5 * (10.5 + 9.8)) and hi == pytest.approx(0.5 * (2970 + 2919))
    assert ideals.trackman_carry_2010(115, 2.5) == pytest.approx((0.5 * (9.8 + 13.0), 0.5 * (2919 + 2358)))
    assert ideals.trackman_carry_2010(200, 20) == ideals.trackman_carry_2010(120, 5)  # clamped to the table
    assert ideals.trackman_carry_2010(10, -20) == ideals.trackman_carry_2010(75, -5)
    assert ideals.ping_2019(400, 50) == ideals.ping_2019(180, 10)
    assert ideals.ping_2019(10, -50) == ideals.ping_2019(80, -10)


def test_driver_bands_span_all_three_sources_with_the_margin():
    for player in presets.PLAYERS:
        b = ideals.ideal_bands("driver", player)
        d = b["launch_deg"]["detail"]
        srcs = [d["trackman_carry_2010"], d["trackman_total_2010"], d["ping_2019"]]
        assert b["launch_deg"]["lo"] == pytest.approx(min(s["launch_deg"] for s in srcs) - 1.0)
        assert b["launch_deg"]["hi"] == pytest.approx(max(s["launch_deg"] for s in srcs) + 1.0)
        assert b["launch_deg"]["target"] == pytest.approx(sum(s["launch_deg"] for s in srcs) / 3.0)
        assert b["spin_rpm"]["lo"] == pytest.approx(min(s["spin_rpm"] for s in srcs) - 200.0)
        assert b["spin_rpm"]["hi"] == pytest.approx(max(s["spin_rpm"] for s in srcs) + 200.0)
        assert "TrackMan" in b["launch_deg"]["source"] and "PING" in b["launch_deg"]["source"]


def test_driver_bands_follow_speed_and_attack():
    base = ideals.ideal_bands("driver", "pga", attack=0.0)
    higher = ideals.ideal_bands("driver", "pga", attack=3.0)
    assert higher["launch_deg"]["target"] > base["launch_deg"]["target"]  # more attack, more optimal launch
    assert higher["spin_rpm"]["target"] < base["spin_rpm"]["target"]
    assert higher["dyn_loft_deg"]["target"] > base["dyn_loft_deg"]["target"]  # the chart pairs more loft with more attack
    assert higher["attack_deg"] == base["attack_deg"]  # the attack band is fixed at +2 to +5
    base = ideals.ideal_bands("driver", "pga")
    slow = ideals.ideal_bands("driver", "pga", club_speed=90.0)
    assert slow["launch_deg"]["target"] > base["launch_deg"]["target"]  # slower swings want more launch


def test_driver_ideal_sits_inside_the_launch_and_spin_bands():
    """The ideal driver (balanced chart loft, trim 1) launches and spins inside the
    three-source bands for every player."""
    for player in presets.PLAYERS:
        b = ideals.ideal_bands("driver", player)
        m = _metrics("driver", player)
        assert _inside(b["spin_rpm"], m["spin_rpm"]), player
        assert _inside(b["launch_deg"], m["launch_deg"]), player


def test_driver_bands_list_all_three_sources():
    b = ideals.ideal_bands("driver", "pga")
    for metric in ("launch_deg", "spin_rpm"):
        assert set(b[metric]["detail"]) == {"trackman_carry_2010", "trackman_total_2010", "ping_2019", "inputs"}
        assert "Total Optimizer" in b[metric]["source"] and "Carry Optimizer" in b[metric]["source"]
        assert "PING" in b[metric]["source"]
    d = b["launch_deg"]["detail"]
    assert d["trackman_total_2010"]["launch_deg"] < d["trackman_carry_2010"]["launch_deg"]  # the total chart launches lower
    assert d["trackman_total_2010"]["spin_rpm"] < d["trackman_carry_2010"]["spin_rpm"]


def test_nan_and_out_of_range_attack_raise():
    for bad in (float("nan"), float("inf"), 11.0, -11.0):
        with pytest.raises(ValueError, match="attack"):
            ideals.ideal_bands("driver", "pga", attack=bad)
    for bad in (float("nan"), float("inf")):
        with pytest.raises(ValueError):
            ideals.ideal_bands("driver", "pga", club_speed=bad)


def test_optimizer_grids_are_public_and_shaped():
    g = ideals.optimizer_grids()
    tm, pg = g["trackman_carry_2010"], g["ping_2019"]
    assert (len(tm["club_speed_mph"]), len(tm["attack_deg"])) == (10, 3)
    assert (len(pg["ball_speed_mph"]), len(pg["attack_deg"])) == (11, 11)
    assert tm["club_speed_mph"] == sorted(tm["club_speed_mph"]) and pg["ball_speed_mph"] == sorted(pg["ball_speed_mph"])
    for key in ("ball_speed_mph", "launch_deg", "spin_rpm", "carry_yd", "dyn_loft_deg"):
        assert len(tm[key]) == 10 and all(len(row) == 3 for row in tm[key]), key
    assert tm["launch_deg"][8][1] == 9.8 and tm["spin_rpm"][8][1] == 2919  # 115 mph, AoA 0
    assert pg["launch_deg"][-1][5] == 10.4 and pg["spin_rpm"][-1][5] == 2550  # 180 mph, AoA 0
    for i, s in enumerate(tm["club_speed_mph"]):  # the grid reads back through the interpolator
        for j, a in enumerate(tm["attack_deg"]):
            assert ideals.trackman_carry_2010(s, a) == pytest.approx((tm["launch_deg"][i][j], tm["spin_rpm"][i][j]))


def test_presets_fly_matches_deliver_and_simulate_and_takes_overrides():
    import flight
    p = presets.preset("7i", "pga")
    ln, f = presets.fly(p)
    ref = launch.deliver(p["club_speed"], p["attack"], 0.0, 0.0, p["dyn_loft"], "7i", spin_trim=p["spin_trim"])
    assert ln == ref
    assert f.carry_yd == flight.simulate(ref.ball_speed_mph, ref.launch_deg, ref.launch_dir_deg, ref.spin_rpm,
                                         ref.spin_axis_deg).carry_yd
    ln2, f2 = presets.fly(p, path=5.0, face=2.0)
    assert ln2.launch_dir_deg > 2.0 and f2.curve_yd < 0.0
    assert p["path"] == 0.0  # the preset dict is not changed
    assert presets.fly(p, club_speed=80.0)[0].ball_speed_mph < ln.ball_speed_mph
    with pytest.raises(ValueError, match="unknown override"):
        presets.fly(p, loft=20.0)
    with pytest.raises(ValueError):
        presets.fly(p, path=99.0)  # deliver's domain check


# ---------------------------------------------------------------------------
# data.py against the source log
# ---------------------------------------------------------------------------

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "docs", "sources", "004_Source_Log.md")


def _log_section(lines, start, end):
    i = next(k for k, l in enumerate(lines) if l.startswith(start))
    j = next(k for k, l in enumerate(lines) if k > i and l.startswith(end))
    return lines[i:j]


@pytest.mark.skipif(not os.path.exists(LOG), reason="source log not in this checkout")
def test_optimizer_tables_match_the_source_log():
    with open(LOG, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    rows = []
    for l in _log_section(lines, "### TrackMan CARRY Optimizer", "In the CARRY table"):
        m = re.match(r"\| (\d+) \| (-?\d+) \| (\d+) \| ([\d.]+) \| (\d+) \| (\d+) \| (\d+) \| ([\d.]+) \|", l)
        if m:
            rows.append(tuple(float(x) if "." in x else int(x) for x in m.groups()))
    assert len(rows) == 30
    assert rows == list(data.TRACKMAN_CARRY_2010)
    ping = {}
    for l in _log_section(lines, "### PING Optimal", "An AI-generated"):
        m = re.match(r"\| (\d+) \|(.*)\|$", l)
        if m:
            cells = [c.strip() for c in m.group(2).split("|")]
            ping[int(m.group(1))] = tuple((float(c.split("/")[0]), int(c.split("/")[1])) for c in cells)
    assert len(ping) == 11 and all(len(v) == 11 for v in ping.values())
    assert ping == data.PING_2019


# ---------------------------------------------------------------------------
# Driver ideal (task 004-copy-pass): TrackMan 2010 chart delivery, attack +2 to +5
# ---------------------------------------------------------------------------


def test_driver_attack_band_is_plus_two_to_plus_five_and_no_other_club_reads_positive():
    for player in presets.PLAYERS:
        b = ideals.ideal_bands("driver", player)["attack_deg"]
        assert (b["lo"], b["hi"], b["target"]) == (2.0, 5.0, 5.0)
        assert "2010" in b["source"] and b["modeled"] is True
        for club in presets.CLUBS:
            if club == "driver":
                continue
            hi = ideals.ideal_bands(club, player)["attack_deg"]["hi"]
            assert hi <= 1.0, (club, player, hi)  # downward attack: the LPGA 3-wood is the highest, at +0.7


def test_driver_ideal_constants_are_the_stated_design_choice():
    d = data.DRIVER_IDEAL
    assert (d["attack_lo_deg"], d["attack_hi_deg"], d["attack_deg"]) == (2.0, 5.0, 5.0)
    assert d["spin_trim"] == 1.0 and d["dyn_loft_half_deg"] == 1.5
    assert d["label"] == "TrackMan 2010 charts: loft between the carry and total optimizers"


def _avg_and_ideal(player):
    p = presets.preset("driver", player)
    assert p["ideal"]["club_speed"] == p["club_speed"] and p["ideal"]["attack"] == 5.0 and p["ideal"]["spin_trim"] == 1.0
    assert (p["ideal"]["path"], p["ideal"]["face"]) == (0.0, 0.0)
    assert p["ideal"]["dyn_loft"] == pytest.approx(chart.optimal_loft(p["club_speed"], 5.0).dyn_loft_deg)
    assert p["ideal"]["label"] == "TrackMan 2010 charts: loft between the carry and total optimizers"
    return presets.fly(p)[1], presets.fly(p["ideal"])[1]


@pytest.mark.parametrize("player", presets.PLAYERS)
def test_driver_ideal_carry_beats_the_tour_average_delivery(player):
    f_avg, f_ideal = _avg_and_ideal(player)
    assert f_ideal.carry_yd > f_avg.carry_yd


@pytest.mark.parametrize("player", presets.PLAYERS)
def test_driver_ideal_total_beats_the_tour_average_delivery(player):
    """The balanced loft keeps total distance: the carry-only loft lost it for the
    LPGA (256.0 yd against 263.2), the balanced loft at +5 does not."""
    f_avg, f_ideal = _avg_and_ideal(player)
    assert flight.roll(f_ideal) > flight.roll(f_avg)


def test_every_other_ideal_is_the_preset():
    for player in presets.PLAYERS:
        for club in presets.CLUBS:
            if club == "driver":
                continue
            p = presets.preset(club, player)
            i = p["ideal"]
            assert (i["club_speed"], i["attack"], i["dyn_loft"], i["spin_trim"], i["club"]) == (
                p["club_speed"], p["attack"], p["dyn_loft"], p["spin_trim"], p["club"])


def test_ideal_delivery_follows_club_speed_and_validates():
    a = presets.ideal_delivery("driver", "pga", 100.0)
    b = presets.ideal_delivery("driver", "pga", 115.0)
    assert a["club_speed"] == 100.0 and a["dyn_loft"] > b["dyn_loft"]  # slower swings want more loft
    assert presets.ideal_delivery("driver", "pga") == presets.preset("driver", "pga")["ideal"]
    assert presets.ideal_delivery("7i", "pga", 80.0)["dyn_loft"] == presets.preset("7i", "pga")["dyn_loft"]
    assert presets.ideal_delivery("driver", "pga", 60.0)["speed_clamped"] is True
    with pytest.raises(ValueError, match="club_speed"):
        presets.ideal_delivery("driver", "pga", 39.0)
    with pytest.raises(ValueError, match="club_speed"):
        presets.ideal_delivery("driver", "pga", float("nan"))


@pytest.mark.parametrize("speed", [75, 85, 94, 96, 100, 110, 115, 120])
def test_model_carry_rises_from_attack_0_to_5_when_loft_follows_optimal_loft(speed):
    carries = []
    for attack in (0.0, 5.0):
        d = dict(presets.preset("driver", "pga")["ideal"], club_speed=float(speed), attack=attack,
                 dyn_loft=chart.optimal_loft(speed, attack).dyn_loft_deg)
        f = presets.fly(d)[1]
        carries.append((f.carry_yd, flight.roll(f)))
    assert carries[1][0] > carries[0][0] and carries[1][1] > carries[0][1]


def test_driver_bands_at_the_ideal_delivery():
    for player in presets.PLAYERS:
        p = presets.preset("driver", player)
        b = ideals.ideal_bands("driver", player)
        _, f = presets.fly(p["ideal"])
        assert b["carry_yd"]["target"] == pytest.approx(f.carry_yd)
        assert b["carry_yd"]["lo"] == pytest.approx(0.97 * f.carry_yd)
        assert b["total_yd"]["target"] == pytest.approx(flight.roll(f))
        assert b["total_yd"]["hi"] == pytest.approx(1.03 * flight.roll(f))
        want = chart.optimal_loft(p["club_speed"], 5.0).dyn_loft_deg
        assert (b["dyn_loft_deg"]["lo"], b["dyn_loft_deg"]["hi"]) == pytest.approx((want - 1.5, want + 1.5))
        assert "2010" in b["dyn_loft_deg"]["source"]
    slow = ideals.ideal_bands("driver", "pga", club_speed=100.0, attack=1.0)
    assert slow["dyn_loft_deg"]["target"] == pytest.approx(chart.optimal_loft(100.0, 1.0).dyn_loft_deg)
    assert slow["carry_yd"]["target"] < ideals.ideal_bands("driver", "pga")["carry_yd"]["target"]


def test_non_driver_bands_are_unchanged_in_meaning():
    p = presets.preset("7i", "pga")
    b = ideals.ideal_bands("7i", "pga")
    assert b["dyn_loft_deg"]["target"] == pytest.approx(p["dyn_loft"])
    assert b["attack_deg"]["target"] == p["attack"]


# ---------------------------------------------------------------------------
# chart.optimal_loft
# ---------------------------------------------------------------------------


def test_optimal_loft_reads_both_charts_at_their_grid_points():
    total = {(r[0], r[1]): r[7] for r in data.TRACKMAN_TOTAL_2010}
    for row in data.TRACKMAN_CARRY_2010:
        r = chart.optimal_loft(row[0], row[1])
        assert r.carry_loft_deg == pytest.approx(row[7])
        assert r.total_loft_deg == pytest.approx(total[(row[0], row[1])])
        assert r.dyn_loft_deg == pytest.approx(0.5 * (row[7] + total[(row[0], row[1])]))
        assert not r.extrapolated and not r.speed_clamped


def test_the_balanced_loft_sits_between_the_two_optimizers_and_below_the_carry_loft():
    for speed in (75, 94, 115, 120):
        for attack in (-5, 0, 5):
            r = chart.optimal_loft(speed, attack)
            assert r.total_loft_deg < r.dyn_loft_deg < r.carry_loft_deg


def test_optimal_loft_interpolates_bilinearly():
    r = chart.optimal_loft(112.5, 2.5)
    for table, got in ((data.TRACKMAN_CARRY_2010, r.carry_loft_deg), (data.TRACKMAN_TOTAL_2010, r.total_loft_deg)):
        corners = [row[7] for row in table if row[0] in (110, 115) and row[1] in (0, 5)]
        assert got == pytest.approx(sum(corners) / 4.0)
    assert r.dyn_loft_deg == pytest.approx(0.5 * (r.carry_loft_deg + r.total_loft_deg))
    assert chart.optimal_loft(115, 4.0).carry_loft_deg == pytest.approx(11.6 + 0.8 * (14.4 - 11.6))
    assert chart.optimal_loft(115, 4.0).total_loft_deg == pytest.approx(9.5 + 0.8 * (11.7 - 9.5))


def test_optimal_loft_clamps_speed_and_flags_it():
    for speed, edge in ((50.0, 75), (75.0, 75), (130.0, 120), (140.0, 120)):
        r = chart.optimal_loft(speed, 0.0)
        assert r.dyn_loft_deg == pytest.approx(chart.optimal_loft(edge, 0.0).dyn_loft_deg)
        assert r.speed_clamped is (speed not in (75.0,))


def test_optimal_loft_extrapolates_attack_with_the_edge_slope_and_flags_it():
    for field in ("dyn_loft_deg", "carry_loft_deg", "total_loft_deg"):
        at5, at0, atm5 = (getattr(chart.optimal_loft(105, a), field) for a in (5, 0, -5))
        up = chart.optimal_loft(105, 10.0)
        assert up.extrapolated and getattr(up, field) == pytest.approx(at5 + (at5 - at0))  # slope per degree, five degrees
        down = chart.optimal_loft(105, -10.0)
        assert down.extrapolated and getattr(down, field) == pytest.approx(atm5 - (at0 - atm5))
    assert not chart.optimal_loft(105, 5.0).extrapolated and not chart.optimal_loft(105, -5.0).extrapolated


def test_optimal_loft_rises_with_attack_and_falls_with_speed():
    for speed in range(75, 125, 5):
        lofts = [chart.optimal_loft(speed, a).dyn_loft_deg for a in (-5, 0, 5)]
        assert lofts == sorted(lofts)
    for attack in (-5, 0, 5):
        lofts = [chart.optimal_loft(s, attack).dyn_loft_deg for s in range(75, 125, 5)]
        assert lofts == sorted(lofts, reverse=True)


def test_optimal_loft_rejects_non_finite_input():
    for bad in (float("nan"), float("inf")):
        with pytest.raises(ValueError, match="club_speed"):
            chart.optimal_loft(bad, 0.0)
        with pytest.raises(ValueError, match="attack"):
            chart.optimal_loft(100.0, bad)
