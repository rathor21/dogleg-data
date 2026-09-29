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

# MODELED, fitted by `calibrate.py --fit-chart` (variant quad7, published spin
# decay) to BOTH the 23 tour rows (carry, height and land angle, each in units of
# the G2 tolerance) and the 60 rows of the TrackMan 2010 Driver Fitting Chart
# (TRACKMAN_CARRY_2010 and TRACKMAN_TOTAL_2010, "TrackMan 2010 chart (TrackMan
# model output)": carry only, in units of 3 percent), each row flown from its
# own ball speed, launch and spin with no axis. Weights: each set is divided by
# the square root of its residual count (tour 69, chart 60) and the chart set is
# then weighted 2.0 (CHART_WEIGHT in calibrate.py). Chart weight 2.0 is the
# smallest step on the grid 1, 1.5, 2, 3, 4 that puts every chart row within 3
# percent (worst 2.8); at 1.0 the worst chart row is 3.85 percent off and at 1.5
# it is 3.4, and at 3 and 4 the tour teaching passes fall to 10 and 7. Constraints hold on S in
# [0.05, 0.50] and Re in [0.5, 2.3]. Why refit: the fit to the tour rows alone
# under-carried high-launch, low-spin drives and left the driver flat across
# attack angle (chart carry error -1.6, -4.0 and -6.4 percent at attack -5, 0
# and +5; 115 mph +5 gave 278 against 295).
#
# Result (dt 0.01): tour rows G2 6 of 23, teaching 15 of 23 (was 6 and 12), rms
# of the normalized residuals carry 1.06, height 0.74, land angle 1.61, overall
# 1.19 (was 1.02). Chart: rms 0.42, all 60 rows within 3 percent (worst 2.8),
# mean carry error +1.2, -0.1 and -1.4 percent at attack -5, 0 and +5. Carry gain
# from attack -5 to +5 at 115 mph: 21.8 yd on the carry rows against the chart's
# 29 (was 14.4), 16.4 against 24 on the total rows (was 8.5); the model still
# gives about 70 percent of the chart's gain. The cost falls on the tour rows:
# PGA PW carry -11.7 yd (was -8.5) and PGA 3 to 5 iron land angles 5.2 to 5.7
# degrees shallow (were 3.7 to 4.2).
#
# Held-out comparison (`calibrate.py --compare-chart`, dt 0.05, chart weight 2).
# Each variant fit on both sets, on the tour rows only (scored on the chart) and
# on the chart rows only (scored on the tour rows). cub adds l3 S^3 to the lift,
# exp adds l3 exp(-S / 0.05), logi swaps the drag speed term for a logistic rise
# below a fitted Re (width 0.15 fixed):
#   variant  params  tour rms  chart rms  G2  teach  worst chart %  tour>chart  chart>tour
#   quad7      7      1.192     0.419      6    15        2.8          1.523       2.245
#   cub        8      1.187     0.428      6    15        2.8          1.597       2.338
#   exp        8      1.233     0.431      6    12        2.7          1.904       2.461
#   logi       8      1.048     0.386      7    16        3.3          1.298       2.250
# quad7 already puts every chart row inside 3 percent, and the extra term buys
# nothing in cub and exp. logi fits both sets a little better in sample but
# leaves one chart row outside the gate (3.3 percent) and has an extra fitted
# parameter, and the held-out scores move with the start point (the fits have a
# flat d2 / l2 valley), so quad7 ships. The chart only spans S 0.05 to 0.14, so
# chart-only fits are unconstrained above that and score 2.2 to 2.5 on the tour
# rows for every variant.
QUAD = {
    "d0": 0.16554,
    "d1": 0.72226,
    "d2": -0.57345,
    "d3": -0.02957,  # per unit of Re/1e5 above the pivot: drag falls slightly as the ball speeds up
    "l0": 0.05793,
    "l1": 1.28987,
    "l2": -1.21142,
}

# ---------------------------------------------------------------------------
# Bounce and roll. Gaps section, item 8: no source read covers roll. The Tour
# table gives landing angle but no roll-out. MODELED, but anchored since task
# 004-copy-pass to TrackMan's own model output: `calibrate.py --fit-roll` fits
# total minus carry on the 60 rows of the TrackMan 2010 chart (carry optimizer
# and total optimizer rows, "TrackMan 2010 chart (TrackMan model output)"),
# each row flown from its own launch conditions with the shipped aero. Soft-L1
# with a 5 yd scale, since the log flags two totals at 100 mph as likely printing
# errors. Form, in flight.roll:
#   roll = k v cos(land angle)^p (ref / max(land spin, floor))^q
# Fit: k 1.296, p 4.34, q 0.559; rms 6.2 yd on rolls of 16 to 58 yd, largest 18.5
# yd. The two charts sit at different landing angles and spins, and TrackMan's
# roll is about 24 yd on the carry optimizer rows and 42 to 58 yd on the total
# optimizer rows. Landing angle alone could not separate them (rms 8.3 yd with
# q = 0). Landing spin is what stops a wedge rolling like a driver: a Tour PW
# lands with about 8,000 rpm and rolls about 6 yd. The chart holds drivers only,
# so irons and wedges are extrapolation, checked by eye, not fitted.
# ---------------------------------------------------------------------------

ROLL_K = 1.2962  # MODELED, fitted to the chart
ROLL_COS_POWER = 4.3428  # MODELED, fitted to the chart
ROLL_SPIN_POWER = 0.5594  # MODELED, fitted to the chart
ROLL_SPIN_REF_RPM = 2500.0  # MODELED reference (about the chart's median landing spin), not fitted
ROLL_SPIN_FLOOR_RPM = 500.0  # MODELED, keeps a zero-spin shot finite
ROLL_MAX_YD = 80.0  # MODELED safety bound, not fitted (the chart rolls reach 58 yd)
# Roll cap, added at the pre-merge review. The roll fit saw only 75 to 120 mph driver
# rows, and the form k v cos^p (ref / spin)^q grows unchecked at slow club speeds:
# the driver ideal at 40 mph carried 46 yd and rolled 72. TrackMan's own model output
# bounds the ratio. Across the 60 rows of both 2010 charts (TRACKMAN_CARRY_2010 and
# TRACKMAN_TOTAL_2010, "TrackMan 2010 chart (TrackMan model output)") the largest
# (total - carry) / carry is 0.3265, the 75 mph, attack 0 row of the total chart
# (carry 147, total 195). The cap is that ratio times 1.1: roll <= ROLL_CAP_FRAC *
# carry. MODELED; the 1.1 margin is a design choice. It does not bind on any chart
# row (the model's largest chart ratio is 0.355) or on any Tour row, preset or ideal
# delivery at its own club speed, so it changes nothing inside the fit; it binds
# only when a slow swing rolls out. tests/test_flight.py checks both.
ROLL_CAP_FRAC = 0.3592  # MODELED, 1.1 x 0.3265

# ---------------------------------------------------------------------------
# Delivery-to-launch model (task 004.3, gate G3). Every number is MODELED: a
# fit made by `calibrate_launch.py --fit` to the published tables above. Forms
# are in launch.py; ADR 0004 records the choices.
#
# Irons, hybrids and woods (fitted first, and unchanged by the driver refit):
#
#   k(SL) = k0 + k1 * clamp(SL, k_sl_lo, k_sl_hi)   weight of the face normal
#       Fitted to the four published (dynamic loft, attack angle, launch)
#       triples: PGA and LPGA driver and 6 iron. Exact k per row is 0.824,
#       0.738 (PGA driver, 6i), 0.771, 0.730 (LPGA driver, 6i). The line leaves
#       launch residuals of -0.42, +0.07, +0.35 and 0.00 deg. The clamp bounds
#       are the spin lofts of those rows (dynamic loft minus attack angle:
#       12.7 to 25.9). Outside that range k stays flat rather than
#       extrapolating a line fitted through four points. Every club except the
#       driver uses this line.
#   smash(SL) = min(smash_a + smash_b SL + smash_c SL^2, smash_cap)
#       Fitted to ball speed over club speed on all 23 rows against the derived
#       spin loft (rms 1.0 percent of ball speed, largest miss 2.3 percent).
#       Monotone decreasing over SL 0 to 45. The cap is the largest published
#       smash (1.49), so a low spin loft cannot buy speed no Tour row shows.
#       smash_floor is the fit's own value at SL 45 (1.56883 - 0.00539408 * 45
#       - 0.0000819501 * 45^2 = 1.16015), about where the fitted rows end (PGA PW
#       38.5). The quadratic keeps falling past that, and no row supports
#       extrapolating it, so smash holds at the floor for larger spin loft. The
#       driver uses this law too: against the 60 chart rows it leaves ball
#       speed within 1.4 percent.
#   spin = factor * spin_a * ball_speed_mph * SL^spin_b   (not the driver)
#       factor is spin_f_wood for the 3-wood and 5-wood and 1 for hybrids,
#       irons and wedges. a, b and f_wood come from the 23-row soft-L1 fit on
#       relative error made in task 004.3 (with a driver factor that the
#       driver law below replaced), and are unchanged. MODELED, no per-tour
#       factor. Rationale for the wood factor, kept modest: fairway woods are
#       low-CG heads and give less spin per degree of spin loft than an iron.
#       The published evidence that strike location moves spin loft, and so
#       spin, is Anchor 5(c) Source 3: a 10 mm low strike makes a driver's
#       dynamic loft 2 degrees lower. The log holds no spin-by-strike-height
#       data, so the size of the factor is a fit and not a measurement. Rows
#       that miss 10 percent: PGA 5w -11.9, LPGA 3w +30.2, LPGA 5w -10.7, LPGA
#       hybrid +12.2.
#
# Driver (fitted second, task 004.3 chart refit). Calibration evidence: the 60
# rows of the TrackMan 2010 Driver Fitting Chart above (TRACKMAN_CARRY_2010 and
# TRACKMAN_TOTAL_2010, "TrackMan 2010 chart (TrackMan model output)": club speed
# 75 to 120, attack angle -5, 0 and +5, spin loft 6.3 to 23.2), plus the PGA and
# LPGA published driver rows. The iron laws above extrapolated badly there:
# below spin loft 12.7 they held k and let spin fall to 1086 rpm at PGA driver
# loft and +6 deg attack, and at equal spin loft ran 20 to 37 percent under the
# chart.
#
#   k_driver(SL) = k0_driver + k1_driver * clamp(SL, k_sl_lo_driver, k_sl_hi_driver)
#       Weighted line through the exact k of the 60 chart rows (about 0.85 at
#       every spin loft, rms 0.003 around a line) and the two published driver
#       triples (0.824 PGA, 0.771 LPGA), each published triple weighted as 15
#       chart rows (calibrate_launch.PUBLISHED_DRIVER_K_WEIGHT, MODELED): at
#       weight 1 the LPGA driver's inverted loft leaves the published 15.5 by
#       1.1 deg, over the 1 deg check. Result: chart launch rms 0.22 deg, worst
#       0.30. The range is the chart's spin loft range, 6.3 to 23.2.
#   spin_driver = spin_a_driver * ball_speed_mph * SL^spin_b_driver
#       Soft-L1 on relative error over the 60 chart rows and the PGA and LPGA
#       driver rows. The chart law is almost linear in spin loft (exponent
#       1.04) with 0.76 percent rms and 1.7 percent worst error on the chart
#       (delivered end to end with the model's own ball speed). The Tour rows
#       carry strike-location offsets the chart does not: at its own inverted
#       spin loft the law puts the PGA driver 35 percent over its table
#       (trim 0.74) and the LPGA driver within 0.5 percent. Presets restore
#       published spin through the spin trim below.
#
#   spin_axis = (axis_c0 + axis_c1 * SL) * atan2(face-to-path, vertical spin loft)
#       (D-plane normal tilt), SL held to axis_sl_lo..axis_sl_hi, the spin
#       lofts of the eight examples (12.4 to 26.9). Fitted so the eight
#       Anchor 5(b) face-to-path examples reproduce their curvature through
#       flight.simulate (worst miss 0.39 of tolerance, 1.5 yd on the PGA 6
#       iron). It absorbs the flight model's own curvature per degree of axis.
#       Each example takes a spin trim from its own 2019 row: 2019 spin over
#       model spin at path 0 and face 0, held fixed as the face opens. A
#       constant c (1.046) fits all eight too, with a worst miss of 0.64 of
#       tolerance and 2.6 yd on the PGA 6 iron at -5. The slope (c falls from
#       1.11 at spin loft 12.4 to 0.98 at 26.9) cuts both and is the shipped
#       form.
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
    "k0_driver": 0.825055,
    "k1_driver": 0.000432686,
    "k_sl_lo_driver": 6.3,
    "k_sl_hi_driver": 23.2,
    "smash_a": 1.56883,
    "smash_b": -0.00539408,
    "smash_c": -8.19501e-05,
    "smash_cap": 1.49,
    "smash_floor": 1.16015,
    "spin_a": 0.778695,
    "spin_b": 1.30445,
    "spin_f_wood": 0.878791,
    "spin_a_driver": 1.33518,
    "spin_b_driver": 1.04096,
    "axis_c0": 1.21767,
    "axis_c1": -0.00883498,
    "axis_sl_lo": 12.4304,
    "axis_sl_hi": 26.8865,
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
    ("PGA", "driver"): 12.685,
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
    ("LPGA", "driver"): 14.596,
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
#   on_target_frac: a ball that finishes within this fraction of its carry of
#       the target line counts as on target. MODELED design choice, an
#       instructor can adjust it. It decides whether a ball that starts on one
#       side and curves back the other way was "worked back" (a Draw that
#       starts right, a Fade that starts left) or missed (Push draw, Pull
#       fade, Push hook, Pull slice). 4 percent of a 170 yd carry is 6.8 yd.
#   on_line_yd: a finish inside this many yards of the target line reads
#       "finishes on line" in the finish text. MODELED design choice.
# ---------------------------------------------------------------------------

CLASSIFY = {
    "start_straight_deg": 2.0,
    "axis_straight_deg": 2.0,
    "curve_hook_frac": 0.08,
    "on_target_frac": 0.04,
    "on_line_yd": 1.0,
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
#   solver_tol_yd: windows.solve_window raises unless peak height, curve and
#       side all land within this many yards of their targets. MODELED.
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
    "solver_tol_yd": 0.05,
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
    "total_frac": 0.03,  # total distance (carry plus roll), same width as carry
    "club_speed_frac": 0.05,
    "driver_launch_margin_deg": 1.0,
    "driver_spin_margin_rpm": 200.0,
}

# Driver ideal delivery (task 004-copy-pass). MODELED design choice, with chart
# evidence. The driver's "ideal" used to be the Tour average (PGA attack -0.9), and
# its attack band was preset +-1.5, so the ideal read negative. TrackMan's own
# 2010 Driver Fitting Chart (TRACKMAN_CARRY_2010 and TRACKMAN_TOTAL_2010, "TrackMan
# 2010 chart (TrackMan model output)") says the opposite: carry rises from attack
# -5 to 0 to +5 at every club speed from 75 to 120 mph in both charts (at 115 mph
# 266, 281, 295 yd on the carry rows and 261, 274, 285 on the total rows), and
# total rises with it at every speed on the total rows and on the carry rows
# except at 100 mph, where the log flags a likely printing error (0 and +5 both
# 272). +5 is the chart's top row and the owner wants hitting up to give the most
# carry and total, so the ideal attack is +5 and the band is +2 to +5 (the top
# edge is the chart's edge). Where +2 sits is a design choice: about two fifths of
# the way from the chart's 0 row to its +5 row. Loft is balanced between the two
# optimizers: chart.optimal_loft(club_speed, attack) is the mean of the CARRY
# chart's and the TOTAL chart's dynamic loft (the total chart wants about 2
# degrees less loft and 700 to 800 rpm less spin than the carry chart at the same
# attack). Carry-only loft cost the LPGA driver total distance against its own
# average (256.0 yd against 263.2), and the balanced loft at +5 beats the average
# in carry and total for all three players (ADR 0004, addendum 2). The chart is the
# calibration basis of the flight model (chart carry within 3 percent on all 60
# rows), so the ideal delivery takes spin trim 1.0, the chart's own strike, instead
# of a player group's trim. This applies to the driver only. Fairway woods,
# hybrids, irons and wedges keep their downward-attack presets and bands (attack
# preset +-1.5, so a tour or amateur value from -0.8 to -4.7).
DRIVER_IDEAL = {
    "attack_deg": 5.0,
    "attack_lo_deg": 2.0,
    "attack_hi_deg": 5.0,
    "dyn_loft_half_deg": 1.5,  # dynamic loft band half-width around the balanced loft
    "spin_trim": 1.0,
    "label": "TrackMan 2010 charts: loft between the carry and total optimizers",
}

# Anchor 4 Source 1: TrackMan Driver Fitting Chart (2010), CARRY Optimizer.
# Label: "TrackMan 2010 chart (TrackMan model output)". These are TrackMan's own
# launch-model outputs for a driver delivery (club speed, attack angle, dynamic
# loft), so whatever the optimizer objective, each row is a valid launch and spin
# calibration point. Parsed from the log table by script.
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
# Anchor 4 Source 1, TOTAL Optimizer (2010), same fields, same label. Parsed
# from the log table (### TrackMan TOTAL Optimizer (2010)) by script, 30 rows.
# With the CARRY rows these give 60 driver deliveries at attack angle -5, 0 and
# +5 and club speed 75 to 120 mph. Spin loft (dynamic loft minus attack angle)
# runs 6.3 to 23.2 deg.
TRACKMAN_TOTAL_2010 = (
    (75, -5, 107, 11.8, 3214, 140, 182, 14.9),
    (75, 0, 109, 13.0, 2506, 147, 195, 15.3),
    (75, 5, 111, 15.3, 1976, 156, 206, 17.1),
    (80, -5, 115, 10.1, 3078, 154, 188, 12.8),
    (80, 0, 117, 12.1, 2494, 163, 199, 14.3),
    (80, 5, 118, 14.8, 2005, 174, 209, 16.5),
    (85, -5, 123, 9.3, 3110, 169, 215, 11.9),
    (85, 0, 125, 11.7, 2568, 180, 228, 13.8),
    (85, 5, 126, 14.0, 1964, 189, 241, 15.6),
    (90, -5, 131, 8.5, 3122, 185, 231, 11.0),
    (90, 0, 132, 10.8, 2517, 196, 245, 12.8),
    (90, 5, 134, 13.8, 2021, 207, 259, 15.3),
    (95, -5, 138, 7.9, 3144, 201, 247, 10.2),
    (95, 0, 140, 10.5, 2565, 213, 262, 12.3),
    (95, 5, 141, 13.0, 1948, 223, 276, 14.4),
    (100, -5, 146, 7.2, 3118, 216, 262, 9.3),
    (100, 0, 148, 10.0, 2570, 230, 278, 11.7),
    (100, 5, 149, 12.4, 1887, 239, 293, 13.7),
    (105, -5, 154, 6.4, 3071, 231, 278, 8.4),
    (105, 0, 156, 9.1, 2461, 243, 294, 10.7),
    (105, 5, 157, 11.7, 1810, 254, 309, 12.9),
    (110, -5, 162, 5.6, 3005, 245, 293, 7.5),
    (110, 0, 163, 8.7, 2471, 260, 310, 10.2),
    (110, 5, 165, 11.1, 1716, 268, 326, 12.2),
    (115, -5, 170, 5.3, 3030, 261, 307, 7.1),
    (115, 0, 171, 8.0, 2396, 274, 325, 9.5),
    (115, 5, 172, 10.7, 1681, 285, 342, 11.7),
    (120, -5, 178, 4.5, 2929, 273, 322, 6.2),
    (120, 0, 179, 7.7, 2382, 290, 340, 9.0),
    (120, 5, 180, 10.3, 1636, 300, 358, 11.3),
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
