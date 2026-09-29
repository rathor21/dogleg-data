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
# update), parameters as written in the workbook.
#   Re in units of 1e5.
#   Cd0 = CdL for Re <= ReLow; linear from CdL to CdH between ReLow and ReHigh;
#   CdH for Re >= ReHigh.
#   CD = Cd0 + CdS * S ;  CL = ClAmp * S^0.4 ;  S = R * omega / v.
# ---------------------------------------------------------------------------

CD_LOW_RE = 1.9451114  # CdL
CD_HIGH_RE = 0.13248  # CdH
CD_SPIN_SLOPE = 0.2087217  # CdS
CL_AMP = 0.2294096  # ClAmp
CL_EXPONENT = 0.4
RE_LOW = 0.5  # ReLow, units of 1e5
RE_HIGH = 1.0  # ReHigh, units of 1e5
RE_UNIT = 1.0e5

# MODELED switch. True reproduces Nathan's Re-dependent Cd0 exactly (checked
# against his workbook: 160 mph, 11 deg, 3000 rpm, 70 F, sea level gives
# 259.0 yd and 4.97 s here against 259.3 yd and 4.99 s in the sheet). False
# holds Cd0 at CdH for every Re, so CD = 0.13248 + 0.2087 * S at all speeds.
# The Tour tables cannot be met with the branch on. Below about 81 mph Cd0
# climbs linearly toward CdL = 1.945 (it is about 1.1 at 60 mph), so every
# iron loses its speed near the end of the flight, lands at 60 to 70 degrees
# and comes up 30 to 40 yd short whatever two global multipliers are used
# (calibrate.py --nathan-re: best rms 5.4 in units of the G2 tolerances,
# against 1.3 with the branch off). Anchor 7 Source 2 reports Bearman and
# Harvey's CD and CL as independent of Re over 126,000 to 238,000, and Source
# 3 reports spin-down as independent of Re for 1.0e5 to 2.5e5. Nothing read
# supports a drag climb of that size. A ball at 60 mph has Re near 75,000.
RE_DEPENDENT_DRAG = False

# Anchor 7, Source 1: the sheet computes Re = 123,638 at 100 mph for the
# default ball and air. Used below only to back out an air viscosity.
RE_AT_100MPH_DATUM = 123638.0
RE_DATUM_SPEED_MPH = 100.0

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
# Global aero multipliers. MODELED: at most two, shared by every club and both
# tours (task rule: no per-club fudge factors). Fit by calibrate.py by least
# squares on normalized carry, max height and land angle errors over all PGA
# and LPGA rows. 1.0 means Nathan's coefficients as published.
# ---------------------------------------------------------------------------

# Fit by `calibrate.py --fit` (RE_DEPENDENT_DRAG = False, dt = 0.02 for the fit,
# checked at 0.01). rms of the G2-normalized residuals (1.0 = on the gate):
# carry 1.26, height 0.93, land angle 1.57. The two-parameter point-mass model
# passes G2 on only a few rows: it runs long on driver height (about +5 yd),
# short on PGA wedge carry (-16 yd for PW), and shallow on landing angle for
# the long PGA clubs (-4 to -6 deg). A four-parameter fit (free Cd0, CdS,
# lift, lift exponent) only reaches rms 1.21, so the misses are not a
# two-multiplier limitation alone. See tests/test_flight.py for the row list.
LIFT_MULT = 2.309  # on CL. MODELED, fitted.
DRAG_MULT = 1.721  # on CD. MODELED, fitted.

# ---------------------------------------------------------------------------
# Bounce and roll. Gaps section, item 8: no source read covers it; the Tour
# table gives landing angle but no roll-out. Everything below is MODELED, with
# no fitting claim. See flight.roll for the form.
# ---------------------------------------------------------------------------

ROLL_K = 2.6  # MODELED, yd per (mph of landing speed) at zero landing angle
ROLL_COS_POWER = 6  # MODELED
ROLL_MAX_YD = 40.0  # MODELED bound
