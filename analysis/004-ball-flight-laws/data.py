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
# Anchor 1 and 2, SUPERSEDED 2019 rows (TrackMan PDFs dated 2019-01-04).
# Used ONLY to calibrate face-to-path curvature: TrackMan's worked examples on
# the Face to Path page use these carries (275, 183, 218, 152), not the 2023
# set (log, Anchor 5(b)). Nothing else in the codebase reads them. Same field
# order as FIELDS.
# ---------------------------------------------------------------------------

_SUPERSEDED_2019_ROWS = {
    ("PGA", "driver"): (113, -1.3, 167, 1.48, 10.9, 2686, 32, 38, 275),
    ("PGA", "6i"): (92, -4.1, 127, 1.38, 14.1, 6231, 30, 50, 183),
    ("LPGA", "driver"): (94, 3.0, 140, 1.48, 13.2, 2611, 25, 37, 218),
    ("LPGA", "6i"): (78, -2.3, 109, 1.41, 17.1, 5943, 25, 46, 152),
}
SUPERSEDED_2019 = {key: dict(zip(FIELDS, vals)) for key, vals in _SUPERSEDED_2019_ROWS.items()}

# ---------------------------------------------------------------------------
# Anchor 5(b) Source 1: TrackMan "What is Face to Path?" worked examples,
# centered contact. (tour, club, face-to-path deg, curvature yd). Curvature is
# signed here, positive right: "19 left" is -19. Each runs from the 2019 row
# of the same tour and club above (carry 275, 183, 218, 152).
# ---------------------------------------------------------------------------

CURVATURE_EXAMPLES = (
    ("PGA", "driver", -2.0, -19.0),
    ("PGA", "driver", 5.0, 44.0),
    ("PGA", "6i", 2.0, 8.0),
    ("PGA", "6i", -5.0, -20.0),
    ("LPGA", "driver", 2.0, 14.0),
    ("LPGA", "driver", -5.0, -32.0),
    ("LPGA", "6i", -2.0, -6.0),
    ("LPGA", "6i", 5.0, 14.0),
)

# ---------------------------------------------------------------------------
# Anchor 3: average amateur delivery anchors.
# Driver: TrackMan Combine, male, "Average golfer (14.5)" column (measured
# averages): club speed 94 mph, attack angle -1.8, dynamic loft 15.1. The same
# column gives launch 12.6 deg, spin loft 18.3 deg (which does not equal
# 15.1 - (-1.8) = 16.9, as with the Tour rows), spin 3275 rpm, smash 1.44.
# 6 iron and PW: TrackMan OPTIMIZER DEFAULTS for the average male golfer
# (Anchor 3 Source 2), model outputs and NOT measurements. Club speed 80 and
# 72 mph, attack angle -3.2 and -3.9, dynamic loft 22.4 and 36.7.
# ---------------------------------------------------------------------------

# Each anchor also carries the published row it should reproduce: ball speed,
# launch angle, spin rate and spin loft. Combine: 133, 12.6, 3275, 18.3.
# Optimizer 6 iron: 110, 16.9, 5956, 25.5. Optimizer PW: 86, 26.7, 8408, 40.6.
# They are held-out checks for the launch model and the targets of the preset
# spin trim, never fit targets.

AMATEUR_ANCHORS = {
    "driver": dict(club_speed_mph=94, attack_deg=-1.8, dyn_loft_deg=15.1, ball_speed_mph=133, launch_deg=12.6,
                   spin_rpm=3275, spin_loft_deg=18.3, source="TrackMan Combine, average golfer (14.5 HCP)"),
    "6i": dict(club_speed_mph=80, attack_deg=-3.2, dyn_loft_deg=22.4, ball_speed_mph=110, launch_deg=16.9,
               spin_rpm=5956, spin_loft_deg=25.5, source="TrackMan Optimizer default"),
    "pw": dict(club_speed_mph=72, attack_deg=-3.9, dyn_loft_deg=36.7, ball_speed_mph=86, launch_deg=26.7,
               spin_rpm=8408, spin_loft_deg=40.6, source="TrackMan Optimizer default"),
}

# Anchor 5(c) Source 2 and Anchor 3: swing plane of the Combine average golfer
# with a driver, 49.0 deg (TrackMan puts a driver between 45 and 50). Used only
# by launch.swing_path for the "hold swing direction" toggle.
SWING_PLANE_DEG = 49.0

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

# MODELED, fitted by `calibrate.py --fit` (variant quad7) to all 23 PGA and
# LPGA rows. rms of the G2-normalized residuals: carry 0.81, height 0.95, land
# angle 1.24, overall 1.02 (1.0 sits on the gate). Constraints hold on S in
# [0.05, 0.50] and Re in [0.5, 2.3]. CD at Re 1.5: 0.26 at S = 0.15, 0.31 at
# S = 0.30. CL: 0.23 at S = 0.15, 0.34 at S = 0.30. Spin decay stays at the
# published Anchor 7 value (SPIN_DECAY_COEF, 2.0e-5, Smits and Smith); no "k"
# key means quad_model uses it.
#
# Evidence for the choice (`calibrate.py --compare`, reproducible). Each variant
# fit on all rows, on PGA only and on LPGA only:
#   variant                    params  G2  teach  all rms  PGA>LPGA  LPGA>PGA  held mean
#   quad7 (shipped, k 2.0e-5)     7     6    12    1.016    0.989     1.298     1.143
#   A: quad7 + fitted k           8     7    12    0.987    0.958     1.245     1.102
#   B: logistic low-Re + k        8     8    14    1.040    1.521     1.236     1.378
# A's held-out gain is within noise, and its fitted k pinned at the 6.0e-5 upper
# bound of its range (3x the published value), so it is not shipped. B does not
# transfer from PGA to LPGA. The spin axis curvature check (3w vs 6i at 10 deg)
# reads 3w 12.1 yd and 6i 14.0 yd for quad7, the wrong order against TrackMan's
# examples, and is no better in A or B.
QUAD = {
    "d0": 0.19877,
    "d1": 0.52450,
    "d2": -0.50182,
    "d3": -0.09224,  # per unit of Re/1e5 above the pivot: drag falls as the ball speeds up
    "l0": 0.05635,
    "l1": 1.36147,
    "l2": -1.34813,
}

# ---------------------------------------------------------------------------
# Bounce and roll. Gaps section, item 8: no source read covers it; the Tour
# table gives landing angle but no roll-out. Everything below is MODELED, with
# no fitting claim. See flight.roll for the form.
# ---------------------------------------------------------------------------

ROLL_K = 8.5  # MODELED, yd per (mph of landing speed) at zero landing angle
ROLL_COS_POWER = 10  # MODELED; retuned at 004.2 for the quadratic fit's landing speeds and angles
ROLL_MAX_YD = 40.0  # MODELED bound

# ---------------------------------------------------------------------------
# Delivery-to-launch model (task 004.3, gate G3). Every number is MODELED: a
# fit made by `calibrate_launch.py --fit` to the published tables above. Forms
# are in launch.py; ADR 0004 records the choices.
#
#   k(SL) = k0 + k1 * clamp(SL, k_sl_lo, k_sl_hi)   weight of the face normal
#       Fitted to the four published (dynamic loft, attack angle, launch)
#       triples: PGA and LPGA driver and 6 iron. Exact k per row is 0.824,
#       0.738 (PGA driver, 6i), 0.771, 0.730 (LPGA driver, 6i). The line leaves
#       launch residuals of -0.42, +0.07, +0.35 and 0.00 deg. The clamp bounds
#       are the spin lofts of those rows (dynamic loft minus attack angle:
#       12.7 to 25.9). Outside that range k stays flat rather than
#       extrapolating a line fitted through four points.
#   smash(SL) = min(smash_a + smash_b SL + smash_c SL^2, smash_cap)
#       Fitted to ball speed over club speed on all 23 rows against the derived
#       spin loft (rms 1.0 percent of ball speed, largest miss 2.3 percent).
#       Monotone decreasing over SL 0 to 45. The cap is the largest published
#       smash (1.49), so a low spin loft cannot buy speed no Tour row shows.
#       smash_floor is the fit's own value at SL 45 (1.56883 - 0.00539408 * 45
#       - 0.0000819501 * 45^2 = 1.16015), about where the fitted rows end (PGA PW
#       38.5). The quadratic keeps falling past that, and no row supports
#       extrapolating it, so smash holds at the floor for larger spin loft.
#   spin = class_factor * spin_a * ball_speed_mph * SL^spin_b
#       class_factor is spin_f_driver for the driver, spin_f_wood for the 3-wood
#       and 5-wood, and 1 for hybrids, irons and wedges. a, b, f_driver and
#       f_wood are fitted together, soft-L1 loss on relative error, all 23 rows
#       (rms 9.5 percent). MODELED, no per-tour factor.
#       Rationale, kept modest: tour players strike the driver above center,
#       and vertical gear effect cuts spin, and fairway woods are low-CG heads.
#       Both give less spin per degree of spin loft than an iron. The published
#       evidence that strike location moves spin loft, and so spin, is
#       Anchor 5(c) Source 3: a 10 mm low strike makes a driver's dynamic loft
#       2 degrees lower. The log holds no spin-by-strike-height data, so the
#       size of each factor is a fit and not a measurement. Without the factors
#       the PGA driver read 3777 rpm against 2545 (+48 percent).
#       Result: PGA driver +7.6 percent, LPGA driver -24.5 percent. One factor
#       cannot serve both: their derived spin lofts are 14.3 and 12.3 (the LPGA
#       driver's dynamic loft minus attack angle is 12.7 against a published
#       15.0), and at the published 15.0 the same factor would give 2460 rpm
#       against 2506. Other rows that miss 10 percent: PGA 5w -11.9, LPGA 3w
#       +30.2, LPGA 5w -10.7, LPGA hybrid +12.2.
#   spin_axis = axis_c * atan2(face-to-path, vertical spin loft)   (D-plane normal tilt)
#       axis_c is one constant, fitted with the spin trims below applied, so
#       the eight Anchor 5(b) face-to-path examples reproduce their curvature
#       through flight.simulate (largest miss 13 percent, or 1.5 yd on the PGA
#       6 iron; all inside max(20 percent, 3 yd)). It absorbs the flight
#       model's own curvature per degree of axis. Each example takes a spin
#       trim from its own 2019 row: 2019 spin over model spin at path 0 and
#       face 0, held fixed as the face opens. Before trims, a constant c fit
#       only while the driver had no spin factor (0.968), and the driver
#       factor forced a slope (1.68 - 0.0283 SL).
#
# Spin trim (MODELED, presets.py, not stored here). Each preset carries
# spin_trim = published spin / model spin at the preset delivery (path 0,
# face 0), passed to launch.deliver(spin_trim=) as a multiplier on spin_rpm.
# It stands for where on the face each player group strikes the ball, which
# the published averages include and the model does not. It stays fixed as
# sliders move. The global model above and its G3 test are unchanged: G3 runs
# with trim 1. Amateur anchors take their spin from AMATEUR_ANCHORS (Combine
# 3275, Optimizer 5956 and 8408); amateur clubs between them interpolate the
# trim by club speed. Trims far from 1 mark where the global model is weakest.
# ---------------------------------------------------------------------------

LAUNCH_MODEL = {
    "k0": 0.864266,
    "k1": -0.00516972,
    "k_sl_lo": 12.7,
    "k_sl_hi": 25.9,
    "smash_a": 1.56883,
    "smash_b": -0.00539408,
    "smash_c": -8.19501e-05,
    "smash_cap": 1.49,
    "smash_floor": 1.16015,
    "spin_a": 0.778695,
    "spin_b": 1.30445,
    "spin_f_driver": 0.646101,
    "spin_f_wood": 0.878791,
    "axis_c": 1.0739,
}

# ---------------------------------------------------------------------------
# Default dynamic loft per Tour row (deg). MODELED: for each row, the dynamic
# loft that makes the launch model (LAUNCH_MODEL) reproduce the table's launch
# angle at the table's attack angle, path 0 and face 0. Found by bisection in
# launch_tools.derive_dyn_loft and printed by `calibrate_launch.py
# --write-tour-dyn-loft`. Only the driver and 6 iron loft are published (see
# DYNAMIC_LOFT_DEG); the inversion lands within 0.6 deg of them. A test checks
# this table still matches a live inversion within 0.05 deg, so a refit of
# LAUNCH_MODEL needs the table regenerated.
# ---------------------------------------------------------------------------

TOUR_DYN_LOFT = {
    ("PGA", "driver"): 13.378,
    ("PGA", "3w"): 12.396,
    ("PGA", "5w"): 13.039,
    ("PGA", "hybrid"): 13.707,
    ("PGA", "3i"): 13.893,
    ("PGA", "4i"): 14.793,
    ("PGA", "5i"): 16.666,
    ("PGA", "6i"): 20.092,
    ("PGA", "7i"): 23.354,
    ("PGA", "8i"): 25.749,
    ("PGA", "9i"): 28.738,
    ("PGA", "pw"): 33.813,
    ("LPGA", "driver"): 15.060,
    ("LPGA", "3w"): 15.022,
    ("LPGA", "5w"): 16.385,
    ("LPGA", "hybrid"): 18.925,
    ("LPGA", "4i"): 18.820,
    ("LPGA", "5i"): 20.058,
    ("LPGA", "6i"): 23.603,
    ("LPGA", "7i"): 26.102,
    ("LPGA", "8i"): 29.299,
    ("LPGA", "9i"): 33.048,
    ("LPGA", "pw"): 35.313,
}

# ---------------------------------------------------------------------------
# Model domain (task 004.3 review). MODELED design choice, not sourced: the
# ranges launch.deliver accepts and the tool's sliders clamp to. Wide enough
# for every preset and worked example (club speed 72 to 115, attack angle -4.9
# to +3.0, dynamic loft up to 36.7) with room for a slider to move. Each range
# is (low, high) inclusive. The spin loft floor keeps dynamic loft minus attack
# angle at 1 degree or more: the fit has no data below spin loft 12 and the
# D-plane normal is undefined when spin loft is zero. swing_plane_deg is the
# open interval swing_path accepts.
# ---------------------------------------------------------------------------

DOMAIN = {
    "club_speed_mph": (40.0, 140.0),
    "attack_deg": (-10.0, 10.0),
    "path_deg": (-15.0, 15.0),
    "face_deg": (-15.0, 15.0),
    "dyn_loft_deg": (0.0, 65.0),
    "min_spin_loft_deg": 1.0,
    "swing_plane_deg": (20.0, 80.0),
}

# ---------------------------------------------------------------------------
# Shot classifier (task 004.4). classify.py reads these.
#   start_straight_deg: launch direction inside +-2 deg counts as a straight
#       start. Anchor 5(a) Source 2, TrackMan "What is Launch Direction?"
#       (2022-02-17): a Master's quote on the page says to keep launch
#       direction within plus or minus 2 degrees. SOURCED (a coach quote on
#       TrackMan's page, not a TrackMan-defined class boundary).
#   axis_straight_deg: spin axis between -2 and 2 counts as straight. Anchor
#       5(b) Source 2, TrackMan "What is Spin Axis?" (2024-09-23). SOURCED.
#   curve_hook_frac: curve over carry above which a curving ball reads as a
#       hook or slice instead of a draw or fade. MODELED design choice, an
#       instructor can adjust it. Reasoning from the Anchor 5(b) Source 1
#       worked examples: a PGA driver with face-to-path +5 curves 44 yd on a
#       275 yd carry (16 percent), which reads as a slice; a PGA 6 iron with
#       face-to-path +2 curves 8 yd on 183 (4.4 percent), which reads as a
#       fade. 8 percent sits between them.
# ---------------------------------------------------------------------------

CLASSIFY = {
    "start_straight_deg": 2.0,
    "axis_straight_deg": 2.0,
    "curve_hook_frac": 0.08,
}

# ---------------------------------------------------------------------------
# Nine windows (task 004.4). Every number is MODELED: Anchor 6 (TaylorMade,
# "Tiger Woods' Nine Windows", 2021) anchors the concept and the name only.
# The source log holds no launch, spin or height for any window, so the
# recipes are model output, carry the modeled badge and are never attributed
# to Tiger Woods.
#   height_mult: peak height as a multiple of the preset's modeled peak height
#       (mid is the preset itself). MODELED.
#   curve_frac: draw and fade curvature as a fraction of the window's own
#       carry, draw negative. MODELED.
#   side_tol_yd: every window must finish this close to the target line. MODELED.
#   attack_per_loft: attack angle change per degree of the height lever h,
#       with dynamic loft = preset dynamic loft + h. MODELED: a lower shot
#       comes from a ball played further back, which delofts and steepens the
#       blow together; a higher shot comes from a ball further forward, which
#       adds loft and shallows the blow.
# ---------------------------------------------------------------------------

WINDOWS = {
    "club": "7i",
    "heights": {"low": 0.70, "mid": 1.00, "high": 1.25},
    "curve_frac": {"draw": -0.05, "straight": 0.0, "fade": 0.05},
    "side_tol_yd": 1.5,
    "attack_per_loft": 0.4,
}

# ---------------------------------------------------------------------------
# Ideal bands (task 004.4). ideals.py reads these.
# Delivery bands for a straight target shot. launch_dir and spin_axis: TrackMan
# plus or minus 2 deg (Anchors 5(a) and 5(b), see CLASSIFY). Everything else
# in IDEAL_TOL is a MODELED width chosen by design, not a source value.
# Driver launch and spin come from the two optimizer tables below, widened by
# a MODELED margin: one degree of launch and 200 rpm of spin on each side.
# PING's own printed tolerance is 1 deg launch and 300 rpm spin around a cell
# (Anchor 4 Source 2); the band here is [lowest source - margin, highest
# source + margin], so it already spans the two sources' disagreement.
# ---------------------------------------------------------------------------

IDEAL_TOL = {
    "path_deg": 2.0,
    "face_deg": 1.0,
    "face_to_path_deg": 1.5,
    "launch_dir_deg": 2.0,  # Anchor 5(a), TrackMan
    "spin_axis_deg": 2.0,  # Anchor 5(b), TrackMan
    "side_frac": 0.05,  # of carry
    "curve_frac": 0.04,  # of carry
    "launch_deg": 1.5,  # non-driver clubs
    "spin_frac": 0.10,  # non-driver clubs
    "max_height_yd": 3.0,
    "land_angle_below_deg": 3.0,  # lower edge only, upper edge open
    "attack_deg": 1.5,
    "dyn_loft_deg": 2.0,
    "spin_loft_deg": 2.0,
    "smash_below": 0.03,  # lower edge only, upper edge open
    "ball_speed_frac": 0.03,
    "carry_frac": 0.03,
    "club_speed_frac": 0.05,
    "driver_launch_margin_deg": 1.0,
    "driver_spin_margin_rpm": 200.0,
}

# Anchor 4 Source 1: TrackMan Driver Fitting Chart (2010), CARRY Optimizer.
# Rows: (club speed mph, attack angle deg, ball speed mph, launch deg, spin rpm,
# carry yd, total yd, dynamic loft deg). Club speed 75 to 120 in 5 mph steps,
# attack angle -5, 0, +5. Values as printed in the log. The log flags the total
# at 100 mph as a likely printing error; total is unused here.
TRACKMAN_CARRY_2010_FIELDS = (
    "club_speed_mph", "attack_deg", "ball_speed_mph", "launch_deg", "spin_rpm", "carry_yd", "total_yd", "dyn_loft_deg",
)
TRACKMAN_CARRY_2010 = (
    (75, -5, 104, 14.6, 3722, 143, 166, 18.2),
    (75, 0, 107, 16.3, 3121, 154, 178, 19.2),
    (75, 5, 108, 19.2, 2720, 164, 187, 21.8),
    (80, -5, 113, 12.9, 3652, 160, 176, 16.2),
    (80, 0, 115, 15.5, 3179, 171, 187, 18.3),
    (80, 5, 116, 18.0, 2648, 181, 197, 20.3),
    (85, -5, 121, 11.9, 3669, 175, 199, 15.0),
    (85, 0, 123, 14.5, 3164, 187, 211, 17.1),
    (85, 5, 124, 17.0, 2596, 197, 223, 19.1),
    (90, -5, 129, 11.1, 3689, 191, 215, 14.0),
    (90, 0, 131, 13.4, 3093, 203, 228, 15.8),
    (90, 5, 132, 16.4, 2633, 214, 239, 18.5),
    (95, -5, 137, 9.9, 3626, 207, 243, 12.6),
    (95, 0, 138, 12.7, 3114, 219, 244, 15.0),
    (95, 5, 140, 15.7, 2595, 231, 256, 17.6),
    (100, -5, 144, 9.6, 3722, 222, 244, 12.2),
    (100, 0, 146, 12.1, 3118, 235, 272, 14.3),
    (100, 5, 148, 14.9, 2538, 247, 272, 16.7),
    (105, -5, 152, 8.7, 3675, 237, 260, 11.1),
    (105, 0, 154, 11.2, 3038, 251, 275, 13.2),
    (105, 5, 155, 14.5, 2563, 263, 288, 16.2),
    (110, -5, 160, 7.7, 3570, 252, 275, 9.9),
    (110, 0, 162, 10.5, 2970, 266, 291, 12.3),
    (110, 5, 163, 13.7, 2435, 279, 305, 15.2),
    (115, -5, 168, 7.0, 3548, 266, 290, 9.2),
    (115, 0, 170, 9.8, 2919, 281, 306, 11.6),
    (115, 5, 171, 13.0, 2358, 295, 321, 14.4),
    (120, -5, 176, 6.1, 3433, 281, 305, 8.1),
    (120, 0, 178, 9.3, 2890, 296, 321, 11.0),
    (120, 5, 179, 12.6, 2343, 310, 350, 14.0),
)
# Anchor 4 Source 2: PING Optimal Launch & Spin Chart (2019). Rows are driver
# ball speed (mph, 80 to 180), columns are angle of attack (PING_2019_AOA_DEG,
# radar-monitor convention), cells are (launch deg, spin rpm).
PING_2019_AOA_DEG = (-10, -8, -6, -4, -2, 0, 2, 4, 6, 8, 10)
PING_2019 = {
    180: (
        (3.6, 3450), (4.9, 3250), (6.2, 3050), (7.5, 2850), (9.0, 2700), (10.4, 2550), (11.9, 2400), (13.3, 2200), (14.8, 2050), (16.4, 1950), (17.9, 1800),
    ),
    170: (
        (4.3, 3500), (5.7, 3300), (6.9, 3100), (8.2, 2900), (9.6, 2750), (11.0, 2550), (12.4, 2400), (13.9, 2250), (15.3, 2100), (16.8, 1950), (18.2, 1800),
    ),
    160: (
        (5.2, 3500), (6.5, 3300), (7.7, 3100), (9.0, 2950), (10.3, 2750), (11.7, 2600), (13.0, 2400), (14.4, 2300), (15.9, 2100), (17.3, 1950), (18.7, 1800),
    ),
    150: (
        (6.2, 3500), (7.4, 3350), (8.6, 3150), (9.8, 2950), (11.1, 2750), (12.4, 2600), (13.7, 2450), (15.1, 2300), (16.4, 2150), (17.9, 2000), (19.3, 1850),
    ),
    140: (
        (7.3, 3550), (8.3, 3300), (9.5, 3150), (10.7, 2950), (12.0, 2800), (13.2, 2600), (14.5, 2450), (15.8, 2300), (17.2, 2150), (18.5, 2000), (19.9, 1850),
    ),
    130: (
        (8.4, 3500), (9.4, 3300), (10.6, 3150), (11.7, 2950), (12.8, 2750), (14.1, 2600), (15.3, 2450), (16.6, 2300), (17.9, 2150), (19.2, 2000), (20.6, 1850),
    ),
    120: (
        (9.6, 3450), (10.6, 3250), (11.6, 3100), (12.7, 2900), (13.8, 2750), (15.0, 2600), (16.2, 2450), (17.4, 2300), (18.7, 2150), (19.9, 2000), (21.2, 1850),
    ),
    110: (
        (10.9, 3400), (11.8, 3200), (12.7, 3000), (13.9, 2850), (14.9, 2700), (15.9, 2550), (17.1, 2400), (18.2, 2250), (19.5, 2100), (20.7, 1950), (21.9, 1850),
    ),
    100: (
        (11.9, 3250), (12.9, 3100), (13.9, 2950), (14.9, 2800), (15.9, 2600), (16.9, 2450), (18.0, 2300), (19.1, 2150), (20.3, 2050), (21.4, 1900), (22.6, 1750),
    ),
    90: (
        (12.7, 3050), (13.9, 2950), (15.0, 2800), (15.9, 2650), (16.9, 2500), (18.0, 2350), (19.0, 2200), (20.0, 2100), (21.1, 1950), (22.2, 1850), (23.3, 1700),
    ),
    80: (
        (13.8, 2800), (14.5, 2650), (15.8, 2600), (16.9, 2450), (17.8, 2350), (18.8, 2200), (19.9, 2100), (20.8, 1950), (21.8, 1800), (22.9, 1700), (24.0, 1600),
    ),
}
