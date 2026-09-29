"""Gate-verified anchors for release 004 (ball flight laws instructor tool), flight model.

EVERY numeric literal in this file comes from docs/sources/004_Source_Log.md.
Anchor numbers (1, 2, 5, 7 and the Gaps section) cite that log. Values marked
MODELED are assumptions or fits built on published anchors; each carries a
comment saying what was assumed. Nothing here was typed from memory.

Units: the published tables are in mph, degrees, rpm and yards, and stay that
way here. flight.py converts to SI internally.

Where an anchor did not resolve at the resolution this release needs (dynamic
loft for clubs other than driver and 6 iron, club path and face angle by
club, bounce and roll), this file says so next to the value rather than
presenting an interpretive choice as if it were sourced.
"""

from math import pi

# ---------------------------------------------------------------------------
# Unit conversions. Exact by definition, not sourced measurements.
# ---------------------------------------------------------------------------

MPH_TO_MS = 0.44704
YD_TO_M = 0.9144
RPM_TO_RADS = 2.0 * pi / 60.0
G = 9.80665  # standard gravity, m/s^2 (exact by definition)

# ---------------------------------------------------------------------------
# Anchor 1: TrackMan PGA Tour averages per club, 2023 dataset (USED).
# Source 1 blog page 2024-05-02, cross-checked cell for cell against the
# media kit image (Source 2). Yards. Older 2019 set is SUPERSEDED and does not
# appear here (log: "no row from the older table should enter the codebase").
#
# Fields: club_speed_mph, attack_deg, ball_speed_mph, smash, launch_deg,
#         spin_rpm, max_height_yd, land_angle_deg, carry_yd.
# Smash is stored as published. Speeds are integers, so smash does not always
# equal ball speed over club speed (log, Gaps: calibrate on the speeds).
# ---------------------------------------------------------------------------

FIELDS = (
    "club_speed_mph",
    "attack_deg",
    "ball_speed_mph",
    "smash",
    "launch_deg",
    "spin_rpm",
    "max_height_yd",
    "land_angle_deg",
    "carry_yd",
)

_PGA_ROWS = {
    "driver": (115, -0.9, 171, 1.49, 10.4, 2545, 35, 39, 282),
    "3w": (110, -2.3, 162, 1.47, 9.3, 3663, 32, 44, 249),
    "5w": (106, -2.5, 156, 1.47, 9.7, 4322, 33, 48, 236),
    "hybrid": (102, -2.4, 149, 1.47, 10.2, 4587, 31, 49, 231),  # "Hybrid (15-18 deg)"
    "3i": (100, -2.5, 145, 1.46, 10.3, 4404, 30, 48, 218),
    "4i": (98, -2.9, 140, 1.44, 10.8, 4782, 31, 49, 209),
    "5i": (96, -3.4, 135, 1.41, 11.9, 5280, 33, 50, 199),
    "6i": (94, -3.7, 130, 1.39, 14.0, 6204, 32, 50, 188),
    "7i": (92, -3.9, 123, 1.34, 16.1, 7124, 34, 51, 176),
    "8i": (89, -4.2, 118, 1.33, 17.8, 8078, 33, 51, 164),
    "9i": (87, -4.3, 112, 1.29, 20.0, 8793, 32, 52, 152),
    "pw": (84, -4.7, 104, 1.24, 23.7, 9316, 32, 52, 142),
}

# ---------------------------------------------------------------------------
# Anchor 2: TrackMan LPGA Tour averages per club, 2023 dataset (USED).
# The 2023 LPGA table has no 3-iron row (it has a hybrid and a 4-iron).
# The LPGA driver attack angle is positive (+2.8); every other LPGA club is
# negative. Do not force one attack-angle rule across clubs and tours.
# The published smash column differs from ball/club speed by up to 0.03 on
# some rows (LPGA 6 iron: 111/80 = 1.39 against 1.41). Use as published.
# ---------------------------------------------------------------------------

_LPGA_ROWS = {
    "driver": (96, 2.8, 143, 1.49, 12.6, 2506, 26, 36, 223),
    "3w": (92, -0.8, 135, 1.47, 11.6, 2595, 25, 38, 200),
    "5w": (90, -1.6, 130, 1.46, 12.3, 4320, 25, 43, 189),
    "hybrid": (87, -1.9, 125, 1.44, 13.9, 4504, 25, 45, 178),  # "Hybrid (15-18 deg)"
    "4i": (82, -1.7, 118, 1.43, 13.9, 4608, 25, 43, 175),
    "5i": (81, -2.0, 114, 1.42, 14.6, 4966, 25, 45, 166),
    "6i": (80, -2.3, 111, 1.41, 16.7, 5904, 25, 46, 155),
    "7i": (78, -2.5, 106, 1.38, 18.5, 6630, 26, 47, 143),
    "8i": (76, -2.8, 102, 1.36, 20.8, 7413, 27, 47, 133),
    "9i": (74, -3.2, 95, 1.30, 23.5, 7605, 27, 48, 123),
    "pw": (72, -3.2, 88, 1.25, 25.2, 8465, 27, 48, 111),
}


def _table(rows):
    return {club: dict(zip(FIELDS, vals)) for club, vals in rows.items()}


PGA = _table(_PGA_ROWS)
LPGA = _table(_LPGA_ROWS)
TOURS = {"PGA": PGA, "LPGA": LPGA}

# ---------------------------------------------------------------------------
# Anchor 1 supplement: TrackMan publishes dynamic loft and spin loft (deg) for
# the driver and 6 iron only. Every other club is unpublished (log: "Dynamic
# loft for clubs other than driver and 6 iron is also unpublished").
# The published spin loft is close to, but not equal to, dynamic loft minus
# attack angle: PGA 6i 20.2 - (-3.7) = 23.9 vs 24.3; PGA driver 13.7 vs 14.7;
# LPGA driver 12.7 vs 15.0 (unexplained on TrackMan's page).
# ---------------------------------------------------------------------------

DYNAMIC_LOFT_DEG = {
    ("PGA", "driver"): 12.8,
    ("PGA", "6i"): 20.2,
    ("LPGA", "driver"): 15.5,
    ("LPGA", "6i"): 23.6,
}
SPIN_LOFT_DEG = {
    ("PGA", "driver"): 14.7,
    ("PGA", "6i"): 24.3,
    ("LPGA", "driver"): 15.0,
    ("LPGA", "6i"): 25.9,
}

# ---------------------------------------------------------------------------
# Ball. Gaps section of the log, "Ball" entry: USGA Rules of Golf equipment
# standards, ball weight limit 1.620 oz (45.93 g) and minimum diameter
# 1.680 in (42.67 mm). Anchor 7 quotes the same mass (0.04593 kg) and a radius
# of 0.02134 m for the spin decay data, which agrees with D/2.
# ---------------------------------------------------------------------------

BALL_MASS_KG = 0.04593
BALL_DIAMETER_M = 0.04267
BALL_RADIUS_M = BALL_DIAMETER_M / 2.0  # 0.021335 m; Anchor 7 quotes 0.02134 m

# ---------------------------------------------------------------------------
# Anchor 7, Source 1: Alan Nathan's Trajectory Calculator, Golf Version (2025-02-15
# update), parameters as written in the workbook (re-read at task 004.2).
#   Re in units of 1e5.
#   Cd0 = CdL for Re <= ReLow; linear from CdL to CdH between ReLow and ReHigh;
#   CdH for Re >= ReHigh.
#   CD = Cd0 + CdS * S ;  CL = ClAmp * S^0.4 ;  S = R * omega / v.
# NATHAN is the published set: multipliers 1.0 and the Re branch on. Checked
# against the workbook: 160 mph, 11 deg, 3000 rpm, 70 F, sea level gives
# 259.0 yd and 4.97 s here against 259.3 yd and 4.99 s in the sheet.
# ---------------------------------------------------------------------------

RE_UNIT = 1.0e5

NATHAN = {
    "cd_low_re": 1.9451114,  # CdL
    "cd_high_re": 0.13248,  # CdH
    "cd_spin": 0.2087217,  # CdS
    "cl_amp": 0.2294096,  # ClAmp
    "cl_exp": 0.4,
    "re_low": 0.5,  # ReLow, units of 1e5
    "re_high": 1.0,  # ReHigh, units of 1e5
    "re_branch": True,  # MODELED switch: False holds Cd0 at CdH for every Re
    "lift_mult": 1.0,  # MODELED multipliers, 1.0 = as published
    "drag_mult": 1.0,
}

# Anchor 7, Source 1: the sheet computes Re = 123,638 at 100 mph for the
# default ball and air. Used below only to back out an air viscosity.
RE_AT_100MPH_DATUM = 123638.0
RE_DATUM_SPEED_MPH = 100.0

# MODELED baseline, kept reproducible behind `calibrate.py --nathan` and
# `--nathan-re`. Two global multipliers on Nathan's forms, fitted to the Tour
# tables. With the Re branch on (`--nathan-re`) the best fit passes 0 of 23 G2
# rows (rms 5.4 in units of the G2 tolerances): below about 81 mph Cd0 climbs
# toward 1.945, every iron dives to 60 to 70 degrees and lands 30 to 40 yd
# short. Anchor 7 Sources 2 and 3 report CD, CL and spin-down as independent
# of Re over the tested range, so `--nathan` holds Cd0 flat at CdH and refits.
# That gives rms 1.3 and passes 3 of 23 rows, with a 2.3x lift multiplier.
NATHAN_FLAT_FIT = dict(NATHAN, re_branch=False, lift_mult=2.309, drag_mult=1.721)

# Anchor 7, Source 3: spin decay d(omega)/dt = -2.0e-5 * (v^2 / R^2) * S in SI
# units, i.e. omega(t) = omega0 * exp(-t/tau) with tau = R / (2.0e-5 * v).
# Reproduces the paper's 23.8 s at 100 mph only in SI (log: "Use SI").
SPIN_DECAY_COEF = 2.0e-5

# ---------------------------------------------------------------------------
# Air. Gaps section, "Assumptions the model must state": air is standard sea
# level unless the tool says otherwise (the Tour tables say altitude and
# weather were not taken into account).
# MODELED standard condition: sea level, 70 F, density 1.194 kg/m^3.
# MODELED dynamic viscosity: backed out of the Anchor 7 datum (Re = 123,638 at
# 100 mph) with this density and the ball diameter above: mu = rho*v*D/Re.
# It is a derived number (about 1.84e-5 Pa s), not a sourced measurement. It
# only enters through Re, and Re only matters below about 81 mph.
# ---------------------------------------------------------------------------

AIR_DENSITY_KG_M3 = 1.194
AIR_VISCOSITY_PA_S = (
    AIR_DENSITY_KG_M3
    * (RE_DATUM_SPEED_MPH * MPH_TO_MS)
    * BALL_DIAMETER_M
    / RE_AT_100MPH_DATUM
)

# ---------------------------------------------------------------------------
# Quadratic family, Anchor 7 Source 4: McNally, Lambeth and Brekke (Dunlop, 2023,
# 90,233 TrackMan shots) write CL = p1 + p2 S + p3 S^2 and CD = p4 + p5 S +
# p6 S^2. The paper prints no fitted values, so every number below is MODELED:
# fitted here by calibrate.py to the Tour tables, shared by all clubs and both
# tours, no per-club factors.
#   CD = d0 + d1 S + d2 S^2 + d3 (Re/1e5 - RE_PIVOT)
#   CL = l0 + l1 S + l2 S^2
# The Re term is the one speed term the coordinator allowed on drag.
# ---------------------------------------------------------------------------

RE_PIVOT = 1.5  # MODELED, units of 1e5. Re/1e5 is 1.24 at 100 mph.

# Constraints the fit must respect (MODELED design choices, task 004.2):
# CD and CL positive and CL non-decreasing in S over [S_MIN, S_MAX]; CD inside
# [CD_BAND] and CL at most CL_MAX over the Re and S ranges a shot visits.
# S_MAX is 0.50, not 0.40, because Tour wedge launches sit at S = 0.45 to 0.48
# (Anchor 7 spin factor range), so 0.40 would leave the wedges unconstrained.
S_MIN = 0.05
S_MAX = 0.50
CD_BAND = (0.15, 0.45)
CL_MAX = 0.40
RE_RANGE = (0.5, 2.3)  # units of 1e5, about 40 to 185 mph

# MODELED, fitted by `calibrate.py --compare` (variant A) to all 23 PGA and LPGA
# rows: the 7 quadratic parameters plus the spin decay coefficient k. rms of
# the G2-normalized residuals: overall 0.99 (1.0 sits on the gate). Constraints
# hold on S in [0.05, 0.50] and Re in [0.5, 2.3]. CD at Re 1.5: 0.26 at
# S = 0.15, 0.31 at S = 0.30. CL: 0.23 at S = 0.15, 0.34 at S = 0.30.
# k is the coefficient in tau = R / (k v), SI. Anchor 7 logs 2.0e-5 (Smits and
# Smith) and 2.5e-5 (Tavares); k was free in [1.0e-5, 6.0e-5] and the fit sits
# on the UPPER BOUND, 3x the Smits and Smith value (spin time constant 8 s at
# 100 mph instead of 24 s). Read it as "the Tour tables want spin to fall
# faster than the logged laws", not as a measured decay rate. The comparison
# against the 7-parameter model and the logistic variant is in the 004.2
# report; the 7-parameter model at k = 2.0e-5 had held-out rms 1.14, this has
# 1.10.
QUAD = {
    "d0": 0.19710,
    "d1": 0.54852,
    "d2": -0.52694,
    "d3": -0.09160,  # per unit of Re/1e5 above the pivot: drag falls as the ball speeds up
    "l0": 0.06628,
    "l1": 1.37548,
    "l2": -1.41620,
    "k": 6.0e-5,  # MODELED, fitted, at the upper bound of its [1.0e-5, 6.0e-5] range
}

# ---------------------------------------------------------------------------
# Bounce and roll. Gaps section, item 8: no source read covers it; the Tour
# table gives landing angle but no roll-out. Everything below is MODELED, with
# no fitting claim. See flight.roll for the form.
# ---------------------------------------------------------------------------

ROLL_K = 8.5  # MODELED, yd per (mph of landing speed) at zero landing angle
ROLL_COS_POWER = 10  # MODELED; retuned at 004.2 for the quadratic fit's landing speeds and angles
ROLL_MAX_YD = 40.0  # MODELED bound
