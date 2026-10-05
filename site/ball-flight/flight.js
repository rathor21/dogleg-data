/*
 * Ball flight model for release 004, browser port of the Python package in
 * analysis/004-ball-flight-laws. One ES module, no dependencies, no build step.
 *
 * Every constant comes from the JSON that export.py writes to
 * site/ball-flight/data (model.json, presets.json, ideals.json, windows.json,
 * camera.json), so a Python refit plus `python export.py` flows through with
 * no edit here. Nothing in this file is a fitted number.
 *
 * Right-handed frame only. A lefty display is a mirror done by the page.
 *
 * Python source of each function
 * ------------------------------
 *   flight.py    simulate()             -> model.simulate      (deriv and rk4 inlined, MAX_FLIGHT_S, V_FLOOR_MS)
 *                _lift_dir_launch()     -> liftDirLaunch
 *                roll()                 -> model.roll          (uses landSpin, the spin state at the landing step)
 *   launch.py    deliver()              -> model.deliver       (face-to-loft coupling: effectiveLoft, couplingKappa)
 *                effective_loft(), coupling_kappa() -> effectiveLoft, couplingKappa
 *   presets.py   loft_for_attack()      -> model.loftForAttack (loft follows attack angle, MODELED)
 *                check_delivery()       -> checkDelivery
 *                _check_range()         -> checkRange
 *                check_club()           -> checkClub
 *                club_direction()       -> clubDirection
 *                face_normal()          -> faceNormal
 *                blend()                -> blend
 *                _angle_between()       -> angleBetween
 *                dplane_tilt_deg()      -> dplaneTiltDeg
 *                launch_vector()        -> model.launchVector
 *                k_of, smash_of, spin_of, axis_scale
 *                                       -> kOf, smashOf, spinOf, axisScale (the driver has its own k line
 *                                          and spin law; k_of and spin_of take the club)
 *                swing_path()           -> model.swingPath
 *                swing_direction()      -> model.swingDirection
 *                swing_plane_for()      -> model.swingPlaneFor
 *                tilt_about_target_line(), bulge_roll(), gear_effect(), smash_strike_factor()
 *                                       -> internal helpers of deliver (gearEffect is exported)
 *                _no_negative_zero()    -> noNegZero
 *   classify.py  classify()             -> model.classify (with startOf, shapeOf, nameOf, finishText)
 *   presets.py   preset(), scale_speed()-> model.preset, model.scaleSpeed (values read from presets.json)
 *                ideal_delivery()       -> model.idealDelivery (the driver's ideal is computed here from
 *                                          presets.json driver_ideal and optimalLoft)
 *   chart.py     optimal_loft()         -> model.optimalLoft   (dynamic loft midway between the TrackMan 2010
 *                                          CARRY and TOTAL optimizer grids)
 *   ideals.py    ideal_bands()          -> model.idealBands
 *                _bracket, _bilinear, trackman_carry_2010, trackman_total_2010, ping_2019
 *                                       -> bracket, bilinear, trackmanCarry2010, trackmanTotal2010, ping2019
 *   (new)        clampToDomain, shot, metricValue, METRIC_FIELDS, loadModel, createModel
 *
 * Field name mapping (Python snake_case -> JS camelCase)
 * ------------------------------------------------------
 * deliver() returns a Launch object:
 *   ball_speed_mph ballSpeedMph, smash smash, launch_deg launchDeg,
 *   launch_dir_deg launchDirDeg, spin_rpm spinRpm, spin_axis_deg spinAxisDeg,
 *   spin_loft_deg spinLoftDeg, face_to_path_deg faceToPathDeg,
 *   dyn_loft_input_deg dynLoftInputDeg (the delivery's loft, face square to the path),
 *   dyn_loft_deg dynLoftDeg (the EFFECTIVE loft after the face-to-loft coupling, roll and lie,
 *   the loft TrackMan would measure; metricValue("dyn_loft_deg") reads this one),
 *   face_input_deg faceInputDeg (the delivery's face), face_deg faceDeg (the EFFECTIVE face at
 *   the impact point after bulge and the lie tilt; metricValue("face_deg") reads this one),
 *   gear_side_rpm gearSideRpm, gear_back_rpm gearBackRpm (spin the strike's gear effect added).
 * simulate() returns a Flight object:
 *   t, x, y, z (Float64Array, x/y/z in yards, y positive right),
 *   carry_yd carry, side_yd side, curve_yd curve, max_height_yd maxHeight,
 *   apex_x_yd apexX, land_angle_deg landAngle, flight_time_s flightTime,
 *   land_speed_mph landSpeed, land_spin_rpm landSpin, launch_dir_deg launchDir.
 * classify() returns:
 *   start, shape, name, worked_back workedBack, finish_yd finishYd,
 *   finish_text finishText.
 * A delivery object (input to shot and clampToDomain, output of preset) is:
 *   clubSpeed, attack, path, face, dynLoft, club, spinTrim, and optionally lie (lie change at
 *   impact, degrees, positive toe up), strikeToe (mm toward the toe) and strikeUp (mm above the
 *   face center), each 0 when absent.
 * preset() also returns source, modeled, note, atPreset (the launch and
 * flight summaries exactly as export.py wrote them, in Python snake_case) and
 * ideal: the ideal delivery at the preset club speed, {clubSpeed, attack, dynLoft,
 * path, face, spinTrim, club, label, source, modeled, speedClamped, atIdeal}. For
 * every club but the driver it repeats the preset. For the driver it is attack
 * +5 with the balanced TrackMan 2010 chart loft and spin trim 1.0.
 * idealDelivery(club, player, clubSpeed) gives the ideal at another club speed
 * (the driver's loft moves with speed). optimalLoft(clubSpeed, attack) returns
 * {dynLoft, carryLoft, totalLoft, extrapolated, speedClamped}, dynLoft being the
 * mean of the carry-chart and total-chart lofts.
 * shot() returns {delivery, launch, flight, total, classification}, where
 * total is total_yd (carry plus roll) and classification is null when the
 * carry is zero or less (classify() would throw).
 * idealBands() returns {metric: band} with the JSON metric keys (club_speed_mph,
 * attack_deg, path_deg, ...) and band fields lo, hi, target, source_id, source,
 * modeled, published, detail, the shape of ideals.json plus the resolved source
 * text. source_id, source, modeled and published are static and are read from
 * ideals.json, lo, hi and target are recomputed for the current club speed and
 * attack angle.
 *
 * Deliberate deviations from Python
 * ---------------------------------
 * - Only the shipped quadratic aero model exists here. Python's pluggable Aero
 *   (baselines and fit variants) is calibration tooling and is not ported.
 * - `params` overrides are not ported. The model comes from model.json.
 * - The lateral series y and the landing side are normalized to +0 where Python
 *   would leave -0.0 (a UI would print "-0").
 * - Errors are ValueError and RuntimeError, both subclasses of Error, carrying
 *   the same argument names and wording as Python.
 *
 * - Band source text is static (ideals.json `sources`, looked up by source_id).
 *   Python's ideal_bands() embeds the driver's optimizer numbers in the source
 *   string, here they live in band.detail only.
 *
 * Where the JSON keys are read
 * ----------------------------
 * The preset row, band metadata and source lookups are mapped in the SCHEMA
 * block at the top of createModel. model.json constants are read into named
 * constants right below it. createModel checks every key it needs up front and
 * throws a ValueError naming the first one that is missing, so a schema rename
 * fails at load and not in the middle of a shot.
 *
 * Copies: shot() copies the delivery, preset() deep-copies atPreset, every
 * driver band gets its own detail object and model.domain is a frozen deep
 * copy, so a caller that edits a result cannot change the model.
 */

// ---------------------------------------------------------------------------
// Errors and small helpers
// ---------------------------------------------------------------------------

export class ValueError extends Error {
  constructor(message) {
    super(message);
    this.name = "ValueError";
  }
}

export class RuntimeError extends Error {
  constructor(message) {
    super(message);
    this.name = "RuntimeError";
  }
}

const RAD = Math.PI / 180.0; // math.radians(x) is x * (pi / 180)
const DEG = 180.0 / Math.PI; // math.degrees(x) is x * (180 / pi)

const isFiniteNumber = (v) => typeof v === "number" && Number.isFinite(v);

/** Python repr of a number, string or None, for error messages. */
function pyRepr(v) {
  if (v === null || v === undefined) return "None";
  if (typeof v === "string") return `'${v}'`;
  if (typeof v === "number") {
    if (Number.isNaN(v)) return "nan";
    if (v === Infinity) return "inf";
    if (v === -Infinity) return "-inf";
    return Number.isInteger(v) ? `${v}.0` : String(v);
  }
  return String(v);
}

/** Python format spec :g for the short values used in messages. */
function pyG(v) {
  return String(Number(v.toPrecision(6)));
}

const noNegZero = (x) => x + 0.0; // -0 + 0 is +0

const clone = (o) => JSON.parse(JSON.stringify(o)); // the model data is plain JSON

function deepFreeze(o) {
  if (o !== null && typeof o === "object" && !Object.isFrozen(o)) {
    Object.freeze(o);
    for (const v of Object.values(o)) deepFreeze(v);
  }
  return o;
}

/**
 * Metric name to the path of its value in a shot() result. Covers every name in
 * ideals.json `metrics` plus the other flight fields and spin_trim. Frozen.
 */
export const METRIC_FIELDS = deepFreeze({
  club_speed_mph: ["delivery", "clubSpeed"],
  attack_deg: ["delivery", "attack"],
  path_deg: ["delivery", "path"],
  face_input_deg: ["delivery", "face"], // the slider: face before bulge and the lie tilt
  face_deg: ["launch", "faceDeg"], // the EFFECTIVE face at the impact point, what TrackMan would measure
  dyn_loft_input_deg: ["delivery", "dynLoft"], // the slider: loft with the face square to the path
  dyn_loft_deg: ["launch", "dynLoftDeg"], // the EFFECTIVE loft, what TrackMan would measure
  spin_trim: ["delivery", "spinTrim"],
  lie_deg: ["delivery", "lie"],
  strike_toe_mm: ["delivery", "strikeToe"],
  strike_up_mm: ["delivery", "strikeUp"],
  gear_side_rpm: ["launch", "gearSideRpm"],
  gear_back_rpm: ["launch", "gearBackRpm"],
  face_to_path_deg: ["launch", "faceToPathDeg"],
  spin_loft_deg: ["launch", "spinLoftDeg"],
  ball_speed_mph: ["launch", "ballSpeedMph"],
  smash: ["launch", "smash"],
  launch_deg: ["launch", "launchDeg"],
  launch_dir_deg: ["launch", "launchDirDeg"],
  spin_rpm: ["launch", "spinRpm"],
  spin_axis_deg: ["launch", "spinAxisDeg"],
  max_height_yd: ["flight", "maxHeight"],
  apex_x_yd: ["flight", "apexX"],
  land_angle_deg: ["flight", "landAngle"],
  flight_time_s: ["flight", "flightTime"],
  land_speed_mph: ["flight", "landSpeed"],
  carry_yd: ["flight", "carry"],
  side_yd: ["flight", "side"],
  curve_yd: ["flight", "curve"],
  total_yd: ["total"],
});

/** Throw a ValueError naming the first dotted path that is missing from obj. */
function requireKeys(obj, paths) {
  for (const path of paths) {
    let cur = obj;
    for (const part of path.split(".")) {
      if (cur === null || typeof cur !== "object" || cur[part] === undefined) {
        throw new ValueError(`model data is missing ${path}`);
      }
      cur = cur[part];
    }
  }
}

const REQUIRED_KEYS = [
  ...["units.mph_to_ms", "units.yd_to_m", "units.rpm_to_rads", "units.g", "ball.mass_kg", "ball.diameter_m",
    "ball.radius_m", "air.density_kg_m3", "air.viscosity_pa_s", "aero.re_pivot", "aero.re_unit",
    "aero.spin_decay_coef", ...["d0", "d1", "d2", "d3", "l0", "l1", "l2"].map((k) => "aero.quad." + k),
    "flight.dt", "flight.max_flight_s", "flight.v_floor_ms", "roll.k", "roll.cos_power", "roll.spin_power",
    "roll.spin_ref_rpm", "roll.spin_floor_rpm", "roll.max_yd", "roll.cap_frac",
    ...["k0", "k1", "k_sl_lo", "k_sl_hi", "k0_driver", "k1_driver", "k_sl_lo_driver", "k_sl_hi_driver", "smash_a",
      "smash_b", "smash_c", "smash_cap", "smash_floor", "spin_a", "spin_b", "spin_f_wood", "spin_a_driver",
      "spin_b_driver", "axis_c0", "axis_c1", "axis_sl_lo", "axis_sl_hi"].map((k) => "launch_model." + k),
    "coupling.kappa", "coupling.loft_per_attack", "coupling.loft_follow_deloft_linear",
    "coupling.loft_follow_deloft_max", "coupling.driver_natural_slope",
    ...["gear_h_rpm_per_mm_mph", "gear_v_ratio", "gear_v_clubs", "gear_backspin_floor_frac", "bulge_deg_per_mm",
      "roll_deg_per_mm", "bulge_roll_clubs", "smash_loss_per_mm2"].map((k) => "strike." + k),
    "spin_class", ...["club_speed_mph", "attack_deg", "path_deg", "face_deg", "dyn_loft_deg", "swing_plane_deg",
      "min_spin_loft_deg", "lie_deg", "strike_toe_mm", "strike_up_mm"].map((k) => "domain." + k),
    ...["start_straight_deg", "axis_straight_deg", "curve_hook_frac", "on_target_frac", "on_line_yd"].map(
      (k) => "classify." + k),
    "swing_plane_default_deg", "swing_plane_by_club"].map((k) => "model." + k),
  "presets.clubs", "presets.players", "presets.presets", "presets.driver_ideal",
  "ideals.tolerances", "ideals.bands", "ideals.sources", "ideals.metrics", "ideals.driver.trackman_carry_2010",
  "ideals.driver.ping_2019", "ideals.driver.trackman_total_2010", "ideals.driver.default_attack_deg",
];

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
}

// ---------------------------------------------------------------------------
// Vector helpers (launch.py, plain arrays: these run once per delivery)
// ---------------------------------------------------------------------------

const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];
const norm = (a) => Math.sqrt(dot(a, a));
const unit = (a) => {
  const n = norm(a);
  return [a[0] / n, a[1] / n, a[2] / n];
};

/** Angle between two vectors in degrees, from atan2 of |a x b| and a . b. */
function angleBetween(a, b) {
  return Math.atan2(norm(cross(a, b)), dot(a, b)) * DEG;
}

function clubDirection(pathDeg, attackDeg) {
  const p = pathDeg * RAD;
  const a = attackDeg * RAD;
  return [Math.cos(a) * Math.cos(p), Math.cos(a) * Math.sin(p), Math.sin(a)];
}

function faceNormal(faceDeg, dynLoftDeg) {
  const f = faceDeg * RAD;
  const l = dynLoftDeg * RAD;
  return [Math.cos(l) * Math.cos(f), Math.cos(l) * Math.sin(f), Math.sin(l)];
}

/**
 * launch.py tilt_about_target_line: rotate a face normal about the target line (x) for a lie
 * change of lieDeg, positive toe up. A right-handed golfer's toe points to -y, so toe up is a
 * rotation by -lieDeg about +x: it turns a square face open (+y).
 */
function tiltAboutTargetLine(n, lieDeg) {
  const t = -lieDeg * RAD;
  const c = Math.cos(t);
  const s = Math.sin(t);
  return [n[0], n[1] * c - n[2] * s, n[1] * s + n[2] * c];
}

/** launch.py normal_angles: [face angle deg, loft deg] of a face normal. */
function normalAngles(n) {
  return [Math.atan2(n[1], n[0]) * DEG, Math.atan2(n[2], Math.sqrt(n[0] * n[0] + n[1] * n[1])) * DEG];
}

/** Unit vector along (1 - k) d + k n. */
function blend(d, n, k) {
  return unit([
    (1.0 - k) * d[0] + k * n[0],
    (1.0 - k) * d[1] + k * n[1],
    (1.0 - k) * d[2] + k * n[2],
  ]);
}

/**
 * Tilt of the D-plane normal about the launch direction, degrees, positive
 * curves right. d is the club direction and n the face normal.
 */
function dplaneTiltDeg(d, n) {
  const m = cross(d, n);
  if (norm(m) < 1e-9) return 0.0;
  const u = unit([d[0] + n[0], d[1] + n[1], d[2] + n[2]]);
  const right = unit(cross([0.0, 0.0, 1.0], u));
  const up = cross(u, right);
  let mRight = dot(m, right);
  let mUp = dot(m, up);
  // Orient the normal to the backspin side, breaking an exact tie toward +90.
  if (mRight < 0.0 || (mRight === 0.0 && mUp > 0.0)) {
    mRight = -mRight;
    mUp = -mUp;
  }
  return Math.atan2(-mUp, mRight) * DEG;
}

/** flight.py _lift_dir_launch: lift direction for a spin axis tilted about the velocity vector. */
function liftDirLaunch(vhat, spinAxisDeg) {
  const n = cross(vhat, [0.0, 0.0, 1.0]);
  let a0;
  if (Math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2]) < 1e-12) {
    a0 = [0.0, -1.0, 0.0]; // vertical launch: pick "right" continuously (y is left)
  } else {
    a0 = unit(n);
  }
  const l0 = cross(a0, vhat);
  const th = spinAxisDeg * RAD;
  const c = Math.cos(th);
  const s = Math.sin(th);
  return [c * l0[0] + s * a0[0], c * l0[1] + s * a0[1], c * l0[2] + s * a0[2]];
}

// ---------------------------------------------------------------------------
// Scratch storage for trajectories, reused across simulate() calls. The
// result arrays are copies (slice), so callers own what they get.
// ---------------------------------------------------------------------------

let scratchCap = 2048;
let sT = new Float64Array(scratchCap);
let sX = new Float64Array(scratchCap);
let sY = new Float64Array(scratchCap);
let sZ = new Float64Array(scratchCap);

function growScratch() {
  const cap = scratchCap * 2;
  const grow = (old) => {
    const bigger = new Float64Array(cap);
    bigger.set(old);
    return bigger;
  };
  sT = grow(sT);
  sX = grow(sX);
  sY = grow(sY);
  sZ = grow(sZ);
  scratchCap = cap;
}

// ---------------------------------------------------------------------------
// Model
// ---------------------------------------------------------------------------

/**
 * Build a Model from the parsed JSON objects
 * {model, presets, ideals, windows, camera}. windows and camera are only
 * carried through for the page, the maths never reads them.
 */
export function createModel(json) {
  if (json === null || typeof json !== "object") throw new ValueError(`model data must be an object, got ${pyRepr(json)}`);
  requireKeys(json, REQUIRED_KEYS);
  // ===== SCHEMA: every JSON key the maths reads is named here =====
  const M = json.model;
  const PRE = json.presets;
  const IDL = json.ideals;

  const U = M.units;
  const BALL = M.ball;
  const AIR = M.air;
  const Q = M.aero.quad;
  const RE_PIVOT = M.aero.re_pivot;
  const RE_UNIT = M.aero.re_unit;
  const SPIN_DECAY = M.aero.spin_decay_coef;
  const FLIGHT = M.flight;
  const LM = M.launch_model;
  const SPIN_CLASS = M.spin_class;
  const DOMAIN = M.domain;
  const CLS = M.classify;
  const ROLL = M.roll;
  const KAPPA = M.coupling.kappa;
  const LOFT_PER_ATTACK = M.coupling.loft_per_attack;
  const DELOFT_LINEAR = M.coupling.loft_follow_deloft_linear;
  const DELOFT_MAX = M.coupling.loft_follow_deloft_max;
  const STRIKE = M.strike;
  const SWING_PLANE_BY_CLUB = M.swing_plane_by_club;
  const DRIVER_IDEAL = PRE.driver_ideal;
  const TOL = IDL.tolerances;
  const FROZEN_DOMAIN = deepFreeze(clone(DOMAIN)); // what model.domain exposes
  for (const metric of IDL.metrics) {
    if (!Object.prototype.hasOwnProperty.call(METRIC_FIELDS, metric)) {
      throw new ValueError(`metric ${pyRepr(metric)} in ideals.json has no entry in METRIC_FIELDS`);
    }
  }
  const CLUBS = PRE.clubs.map((c) => c.id);
  const PLAYERS = PRE.players.map((p) => p.id);
  const SWING_PLANE_DEFAULT = M.swing_plane_default_deg;

  const MAX_FLIGHT_S = FLIGHT.max_flight_s;
  const V_FLOOR_MS = FLIGHT.v_floor_ms;
  const DEFAULT_DT = FLIGHT.dt;
  const AIR_DENSITY = AIR.density_kg_m3;
  const AIR_VISCOSITY = AIR.viscosity_pa_s;
  const BALL_MASS = BALL.mass_kg;
  const BALL_DIAMETER = BALL.diameter_m;
  const BALL_RADIUS = BALL.radius_m;

  /** One preset row as a delivery object. The single place that maps presets.json keys. */
  function idealFromRow(i) {
    return {
      clubSpeed: i.club_speed_mph,
      attack: i.attack_deg,
      dynLoft: i.dyn_loft_deg,
      path: i.path_deg,
      face: i.face_deg,
      spinTrim: i.spin_trim,
      club: i.club,
      label: i.label,
      source: i.source,
      modeled: i.modeled,
      speedClamped: i.speed_clamped,
      atIdeal: clone(i.at_ideal),
    };
  }
  function presetFromRow(e) {
    return {
      clubSpeed: e.club_speed_mph,
      attack: e.attack_deg,
      dynLoft: e.dyn_loft_deg,
      path: e.path_deg,
      face: e.face_deg,
      spinTrim: e.spin_trim,
      club: e.club,
      source: e.source,
      modeled: e.modeled,
      note: e.note,
      atPreset: clone(e.at_preset),
      ideal: idealFromRow(e.ideal),
    };
  }
  const presetRow = (player, club) => PRE.presets[player][club];
  const bandMeta = (player, club, metric) => IDL.bands[player][club][metric]; // {source_id, modeled, published?}
  const bandSource = (sourceId) => IDL.sources[sourceId];
  // ===== end SCHEMA =====

  // flight.py _make_deriv constants
  const area = Math.PI * BALL_RADIUS * BALL_RADIUS;
  const kf = (0.5 * AIR_DENSITY * area) / BALL_MASS;
  const rePerV = (AIR_DENSITY * BALL_DIAMETER) / AIR_VISCOSITY / RE_UNIT;
  const G = U.g;
  const d0 = Q.d0, d1 = Q.d1, d2 = Q.d2, d3 = Q.d3;
  const l0 = Q.l0, l1 = Q.l1, l2 = Q.l2;

  // Preallocated RK4 state. Index 0..6 is x, y, z, vx, vy, vz, omega. Internal frame: y LEFT.
  const s = new Float64Array(7);
  const sn = new Float64Array(7);
  const tmp = new Float64Array(7);
  const k1 = new Float64Array(7);
  const k2 = new Float64Array(7);
  const k3 = new Float64Array(7);
  const k4 = new Float64Array(7);
  const oh = new Float64Array(3); // omega_hat, fixed in space at launch

  /** flight.py deriv: write d(state)/dt of `st` into `out`. */
  function deriv(st, out) {
    const vx = st[3], vy = st[4], vz = st[5], w = st[6];
    const v = Math.max(Math.sqrt(vx * vx + vy * vy + vz * vz), V_FLOOR_MS);
    const spin = (BALL_RADIUS * w) / v;
    const re = rePerV * v;
    const cd = d0 + d1 * spin + d2 * spin * spin + d3 * (re - RE_PIVOT);
    const cl = l0 + l1 * spin + l2 * spin * spin;
    const vhx = vx / v, vhy = vy / v, vhz = vz / v;
    // lift direction = unit(omega_hat x v_hat)
    let lx = oh[1] * vhz - oh[2] * vhy;
    let ly = oh[2] * vhx - oh[0] * vhz;
    let lz = oh[0] * vhy - oh[1] * vhx;
    const ln = Math.sqrt(lx * lx + ly * ly + lz * lz);
    lx /= ln;
    ly /= ln;
    lz /= ln;
    const ad = kf * cd * v; // drag: -ad * v_vec
    const al = kf * cl * v * v; // lift: al * L_hat
    out[0] = vx;
    out[1] = vy;
    out[2] = vz;
    out[3] = -ad * vx + al * lx;
    out[4] = -ad * vy + al * ly;
    out[5] = -ad * vz + al * lz - G;
    out[6] = (-SPIN_DECAY * v * w) / BALL_RADIUS;
  }

  /** flight.py _rk4: advance `s` by dt into `sn`. */
  function rk4(dt) {
    deriv(s, k1);
    for (let i = 0; i < 7; i++) tmp[i] = s[i] + 0.5 * dt * k1[i];
    deriv(tmp, k2);
    for (let i = 0; i < 7; i++) tmp[i] = s[i] + 0.5 * dt * k2[i];
    deriv(tmp, k3);
    for (let i = 0; i < 7; i++) tmp[i] = s[i] + dt * k3[i];
    deriv(tmp, k4);
    for (let i = 0; i < 7; i++) {
      sn[i] = s[i] + (dt / 6.0) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]);
    }
  }

  const M2YD = 1.0 / U.yd_to_m;

  /**
   * flight.py simulate. Angles in degrees, spin in rpm, output in yards.
   * launchDeg is the vertical launch angle, launchDir the horizontal start
   * direction (positive right), spinAxis positive curves the ball right.
   * Throws ValueError on a bad input and RuntimeError if the ball has not
   * landed after MAX_FLIGHT_S.
   */
  function simulate(ballSpeed, launchDeg, launchDir, spin, spinAxis, opts) {
    const dt = opts && opts.dt !== undefined ? opts.dt : DEFAULT_DT;
    const checks = [
      ["ball_speed_mph", ballSpeed],
      ["launch_deg", launchDeg],
      ["launch_dir_deg", launchDir],
      ["spin_rpm", spin],
      ["spin_axis_deg", spinAxis],
      ["dt", dt],
    ];
    for (let i = 0; i < checks.length; i++) {
      if (!isFiniteNumber(checks[i][1])) {
        throw new ValueError(`${checks[i][0]} must be finite, got ${pyRepr(checks[i][1])}`);
      }
    }
    if (ballSpeed <= 0.0) throw new ValueError(`ball_speed_mph must be > 0, got ${pyRepr(ballSpeed)}`);
    if (dt <= 0.0) throw new ValueError(`dt must be > 0, got ${pyRepr(dt)}`);

    const v0 = ballSpeed * U.mph_to_ms;
    const gam = launchDeg * RAD;
    const psi = launchDir * RAD;
    const vhat = [Math.cos(gam) * Math.cos(psi), -Math.cos(gam) * Math.sin(psi), Math.sin(gam)]; // y is left
    const lhat = liftDirLaunch(vhat, spinAxis);
    const omegaHat = cross(vhat, lhat); // for omega perp v: v x (omega x v) = omega
    oh[0] = omegaHat[0];
    oh[1] = omegaHat[1];
    oh[2] = omegaHat[2];
    const w0 = spin * U.rpm_to_rads;

    s[0] = 0.0;
    s[1] = 0.0;
    s[2] = 0.0;
    s[3] = v0 * vhat[0];
    s[4] = v0 * vhat[1];
    s[5] = v0 * vhat[2];
    s[6] = w0;

    let n = 1; // samples recorded, sample 0 is the launch point
    sT[0] = 0.0;
    sX[0] = 0.0;
    sY[0] = 0.0;
    sZ[0] = 0.0;
    let t = 0.0;
    const maxSteps = Math.trunc(MAX_FLIGHT_S / dt);
    let landed = false;
    let lvx = 0.0, lvy = 0.0, lvz = 0.0, lw = 0.0;
    for (let step = 0; step < maxSteps; step++) {
      rk4(dt);
      const tNew = t + dt;
      if (n >= scratchCap) growScratch();
      if (sn[2] < 0.0) {
        const f = s[2] / (s[2] - sn[2]); // linear interpolation to z = 0
        sT[n] = t + f * dt;
        sX[n] = (s[0] + f * (sn[0] - s[0])) * M2YD;
        sY[n] = -(s[1] + f * (sn[1] - s[1])) * M2YD + 0.0; // flip to positive right
        sZ[n] = 0.0;
        lvx = s[3] + f * (sn[3] - s[3]);
        lvy = s[4] + f * (sn[4] - s[4]);
        lvz = s[5] + f * (sn[5] - s[5]);
        lw = s[6] + f * (sn[6] - s[6]);
        n++;
        landed = true;
        break;
      }
      sT[n] = tNew;
      sX[n] = sn[0] * M2YD;
      sY[n] = -sn[1] * M2YD + 0.0;
      sZ[n] = sn[2] * M2YD;
      n++;
      for (let i = 0; i < 7; i++) s[i] = sn[i];
      t = tNew;
    }
    if (!landed) throw new RuntimeError(`ball did not land within ${pyRepr(MAX_FLIGHT_S)} s`);

    const vh = Math.hypot(lvx, lvy);
    const landAngle = Math.atan2(-lvz, vh) * DEG;
    const landSpeed = Math.sqrt(lvx * lvx + lvy * lvy + lvz * lvz) / U.mph_to_ms;
    let iApex = 0; // first maximum, like np.argmax
    let zMax = sZ[0];
    for (let i = 1; i < n; i++) {
      if (sZ[i] > zMax) {
        zMax = sZ[i];
        iApex = i;
      }
    }
    const carry = sX[n - 1];
    const side = sY[n - 1];
    return {
      t: sT.slice(0, n),
      x: sX.slice(0, n),
      y: sY.slice(0, n),
      z: sZ.slice(0, n),
      carry,
      side,
      maxHeight: zMax,
      apexX: sX[iApex],
      landAngle,
      flightTime: sT[n - 1],
      curve: side - carry * Math.tan(psi),
      landSpeed,
      landSpin: lw / U.rpm_to_rads,
      launchDir,
    };
  }

  /**
   * flight.py roll: total distance in yards, carry plus a modeled bounce and roll,
   * k v cos(land angle)^p (spin_ref / max(landing spin, spin_floor))^q, fitted to
   * TrackMan's 2010 chart totals, and capped at cap_frac * carry so a slow swing cannot roll farther
   * than TrackMan's own charts allow.
   */
  function roll(shotResult) {
    const c = Math.cos(shotResult.landAngle * RAD);
    const spin = Math.max(shotResult.landSpin, ROLL.spin_floor_rpm);
    let r = ROLL.k * shotResult.landSpeed * Math.pow(c, ROLL.cos_power)
      * Math.pow(ROLL.spin_ref_rpm / spin, ROLL.spin_power);
    r = Math.min(Math.max(r, 0.0), ROLL.max_yd, ROLL.cap_frac * Math.max(shotResult.carry, 0.0));
    return shotResult.carry + r;
  }

  // -------------------------------------------------------------------------
  // launch.py
  // -------------------------------------------------------------------------

  function spinClassOf(club) {
    return club === null || club === undefined ? undefined : SPIN_CLASS[club];
  }

  function kOf(sl, club) {
    if (spinClassOf(club) === "driver") {
      const sd = Math.min(Math.max(sl, LM.k_sl_lo_driver), LM.k_sl_hi_driver);
      return LM.k0_driver + LM.k1_driver * sd;
    }
    const sc = Math.min(Math.max(sl, LM.k_sl_lo), LM.k_sl_hi);
    return LM.k0 + LM.k1 * sc;
  }

  function smashOf(sl) {
    const sc = Math.max(sl, 0.0);
    const raw = LM.smash_a + LM.smash_b * sc + LM.smash_c * sc * sc;
    return Math.max(Math.min(raw, LM.smash_cap), LM.smash_floor);
  }

  function spinOf(ballSpeed, sl, club) {
    const s = Math.max(sl, 0.0);
    const cls = spinClassOf(club);
    if (cls === "driver") return LM.spin_a_driver * ballSpeed * Math.pow(s, LM.spin_b_driver);
    const factor = cls === undefined ? 1.0 : LM["spin_f_" + cls];
    return factor * LM.spin_a * ballSpeed * Math.pow(s, LM.spin_b);
  }

  function axisScale(sl) {
    const s = Math.min(Math.max(sl, LM.axis_sl_lo), LM.axis_sl_hi);
    return LM.axis_c0 + LM.axis_c1 * s;
  }

  function checkRange(name, value, key) {
    if (!isFiniteNumber(value)) throw new ValueError(`${name} must be finite, got ${pyRepr(value)}`);
    const lo = DOMAIN[key][0];
    const hi = DOMAIN[key][1];
    if (!(lo <= value && value <= hi)) {
      throw new ValueError(`${name} must be within ${pyG(lo)} to ${pyG(hi)}, got ${pyRepr(value)}`);
    }
  }

  function checkClub(club) {
    if (club !== null && club !== undefined && !CLUBS.includes(club)) {
      const tuple = "(" + CLUBS.map((c) => `'${c}'`).join(", ") + ")";
      throw new ValueError(`club must be None or one of ${tuple}, got ${pyRepr(club)}`);
    }
  }

  function checkDelivery(clubSpeed, attack, path, face, dynLoft, club, spinTrim, lie, strikeToe, strikeUp) {
    checkRange("club_speed_mph", clubSpeed, "club_speed_mph");
    checkRange("attack_deg", attack, "attack_deg");
    checkRange("path_deg", path, "path_deg");
    checkRange("face_deg", face, "face_deg");
    checkRange("dyn_loft_deg", dynLoft, "dyn_loft_deg");
    checkRange("lie_deg", lie, "lie_deg");
    checkRange("strike_toe_mm", strikeToe, "strike_toe_mm");
    checkRange("strike_up_mm", strikeUp, "strike_up_mm");
    const floor = DOMAIN.min_spin_loft_deg;
    if (dynLoft - attack < floor) {
      throw new ValueError(
        `dyn_loft_deg - attack_deg must be at least ${pyG(floor)} deg, got ${pyG(dynLoft - attack)}`
      );
    }
    if (!isFiniteNumber(spinTrim) || spinTrim <= 0.0) {
      throw new ValueError(`spin_trim must be finite and positive, got ${pyRepr(spinTrim)}`);
    }
    checkClub(club);
  }

  /** launch.py launch_vector: launch angle, launch direction and spin loft in degrees. No input checks, like Python. */
  /** launch.py coupling_kappa: loft change per degree of (face - path), cot(lie) for a named club, else 0. */
  function couplingKappa(club) {
    return club !== null && club !== undefined && Object.prototype.hasOwnProperty.call(KAPPA, club) ? KAPPA[club] : 0.0;
  }

  /**
   * launch.py clamp_loft: the one clamp on an effective dynamic loft. At least attack + the domain's
   * minimum spin loft and at least the domain's minimum effective loft (never a negative loft), at
   * most the domain's largest dynamic loft.
   */
  function clampLoft(dl, attack) {
    const low = Math.max(attack + DOMAIN.min_spin_loft_deg, DOMAIN.min_effective_loft_deg);
    return Math.min(Math.max(dl, low), DOMAIN.dyn_loft_deg[1]);
  }

  /** launch.py effective_loft: dynLoft + kappa(club) * (face - path), through clampLoft. */
  function effectiveLoft(dynLoft, path, face, attack, club) {
    return clampLoft(dynLoft + couplingKappa(club) * (face - path), attack);
  }

  function launchVector(path, attack, face, dynLoft, club) {
    const d = clubDirection(path, attack);
    const n = faceNormal(face, effectiveLoft(dynLoft, path, face, attack, club));
    const sl = angleBetween(d, n);
    const u = blend(d, n, kOf(sl, club));
    return {
      launchDeg: Math.atan2(u[2], Math.sqrt(u[0] * u[0] + u[1] * u[1])) * DEG,
      launchDirDeg: Math.atan2(u[1], u[0]) * DEG,
      spinLoftDeg: sl,
    };
  }

  /**
   * launch.py bulge_roll: [face change deg, loft change deg] at the impact point from a curved
   * face, for the clubs in strike.bulge_roll_clubs (driver and fairway woods), else 0.
   */
  function bulgeRoll(club, strikeToe, strikeUp) {
    if (club === null || club === undefined || !STRIKE.bulge_roll_clubs.includes(club)) return [0.0, 0.0];
    return [STRIKE.bulge_deg_per_mm * strikeToe, STRIKE.roll_deg_per_mm * strikeUp];
  }

  /**
   * launch.py impact_normal: the face normal at the impact point (effective loft, then bulge and
   * roll, then the lie tilt) as [n, face deg, loft deg]. With no lie change the angles are the
   * sums themselves, so a square face keeps its loft to the last digit.
   */
  function impactNormal(path, attack, face, dynLoft, club, lie, strikeToe, strikeUp) {
    const dlEff = effectiveLoft(dynLoft, path, face, attack, club);
    const [df, dl] = bulgeRoll(club, strikeToe, strikeUp);
    let faceAt = face + df;
    let loftAt = clampLoft(dlEff + dl, attack);
    let n = faceNormal(faceAt, loftAt);
    if (lie === 0.0) return [n, faceAt, loftAt];
    n = tiltAboutTargetLine(n, lie);
    [faceAt, loftAt] = normalAngles(n);
    return [n, faceAt, loftAt];
  }

  /** launch.py smash_strike_factor: 1 - strike.smash_loss_per_mm2 * (distance from the face center)^2. */
  function smashStrikeFactor(strikeToe, strikeUp) {
    return 1.0 - STRIKE.smash_loss_per_mm2 * (strikeToe * strikeToe + strikeUp * strikeUp);
  }

  /**
   * launch.py gear_effect: add the gear-effect spin of an off-center strike to the D-plane spin.
   * Returns {spinRpm, axisDeg, gearSideRpm, gearBackRpm}. Toe strikes add draw sidespin (left),
   * heel strikes fade sidespin; above center on a driver or fairway wood takes backspin off.
   */
  function gearEffect(spinRpm, axisDeg, ballSpeed, club, strikeToe, strikeUp) {
    const a = axisDeg * RAD;
    const back0 = spinRpm * Math.cos(a);
    const side0 = spinRpm * Math.sin(a);
    const gearSide = -STRIKE.gear_h_rpm_per_mm_mph * ballSpeed * strikeToe;
    let gearBack = 0.0;
    if (club !== null && club !== undefined && STRIKE.gear_v_clubs.includes(club)) {
      gearBack = -STRIKE.gear_v_ratio * STRIKE.gear_h_rpm_per_mm_mph * ballSpeed * strikeUp;
    }
    const back = Math.max(back0 + gearBack, STRIKE.gear_backspin_floor_frac * back0);
    const side = side0 + gearSide;
    return { spinRpm: Math.sqrt(back * back + side * side), axisDeg: Math.atan2(side, back) * DEG, gearSideRpm: gearSide, gearBackRpm: back - back0 };
  }

  /**
   * launch.py deliver. Club delivery to launch conditions. `club` picks the
   * driver line and spin law, the wood factor, or the iron laws, the coupling kappa, the bulge
   * and roll and the vertical gear effect. opts.spinTrim multiplies the D-plane spin and nothing
   * else; opts.lie (degrees, positive toe up), opts.strikeToe and opts.strikeUp (mm) default to 0.
   */
  function deliver(clubSpeed, attack, path, face, dynLoft, club, opts) {
    const spinTrim = opts && opts.spinTrim !== undefined ? opts.spinTrim : 1.0;
    const lie = opts && opts.lie !== undefined ? opts.lie : 0.0;
    const strikeToe = opts && opts.strikeToe !== undefined ? opts.strikeToe : 0.0;
    const strikeUp = opts && opts.strikeUp !== undefined ? opts.strikeUp : 0.0;
    checkDelivery(clubSpeed, attack, path, face, dynLoft, club, spinTrim, lie, strikeToe, strikeUp);
    const d = clubDirection(path, attack);
    const [n, faceEff, dlEff] = impactNormal(path, attack, face, dynLoft, club, lie, strikeToe, strikeUp);
    const sl = angleBetween(d, n);
    const u = blend(d, n, kOf(sl, club));
    const launchDeg = Math.atan2(u[2], Math.sqrt(u[0] * u[0] + u[1] * u[1])) * DEG;
    const launchDir = Math.atan2(u[1], u[0]) * DEG;
    const smash = smashOf(sl) * smashStrikeFactor(strikeToe, strikeUp);
    const ball = smash * clubSpeed;
    const spin0 = spinOf(ball, sl, club) * spinTrim;
    const axis0 = axisScale(sl) * dplaneTiltDeg(d, n);
    const g = gearEffect(spin0, axis0, ball, club, strikeToe, strikeUp);
    return {
      ballSpeedMph: noNegZero(ball),
      smash: noNegZero(smash),
      launchDeg: noNegZero(launchDeg),
      launchDirDeg: noNegZero(launchDir),
      spinRpm: noNegZero(g.spinRpm),
      spinAxisDeg: noNegZero(g.axisDeg),
      spinLoftDeg: noNegZero(sl),
      faceToPathDeg: noNegZero(faceEff - path),
      dynLoftInputDeg: noNegZero(dynLoft),
      dynLoftDeg: noNegZero(dlEff),
      faceInputDeg: noNegZero(face),
      faceDeg: noNegZero(faceEff),
      gearSideRpm: noNegZero(g.gearSideRpm),
      gearBackRpm: noNegZero(g.gearBackRpm),
    };
  }

  /** launch.py swing_plane_for: the vertical swing plane per club, the driver's default for null. */
  function swingPlaneFor(club) {
    if (club === null || club === undefined) return SWING_PLANE_DEFAULT;
    checkClub(club);
    return SWING_PLANE_BY_CLUB[club];
  }

  function checkArc(swingDir, attack, plane) {
    const pl = plane === undefined || plane === null ? SWING_PLANE_DEFAULT : plane;
    const items = [["swing_dir_deg", swingDir], ["attack_deg", attack], ["plane_deg", pl]];
    for (const [name, value] of items) {
      if (!isFiniteNumber(value)) throw new ValueError(`${name} must be finite, got ${pyRepr(value)}`);
    }
    const lo = DOMAIN.swing_plane_deg[0];
    const hi = DOMAIN.swing_plane_deg[1];
    if (!(lo < pl && pl < hi)) {
      throw new ValueError(`plane_deg must be between ${pyG(lo)} and ${pyG(hi)} (exclusive), got ${pyRepr(pl)}`);
    }
    return pl;
  }

  /** launch.py swing_path: club path with the swing direction held (forum formula, checked against Tuxen's examples). */
  function swingPath(swingDir, attack, plane) {
    const pl = checkArc(swingDir, attack, plane);
    return noNegZero(swingDir - attack * Math.tan((90.0 - pl) * RAD));
  }

  /** launch.py swing_direction: the swing direction that gives this path at this attack angle, the inverse of swingPath. */
  function swingDirection(path, attack, plane) {
    const pl = checkArc(path, attack, plane);
    return noNegZero(path + attack * Math.tan((90.0 - pl) * RAD));
  }

  /**
   * Clamp a delivery to the input domain so a slider can never trip deliver().
   * Returns a copy. Dynamic loft minus attack is held at or above the spin loft
   * floor by raising dynamic loft first, and lowering attack if loft tops out.
   */
  function clampToDomain(delivery) {
    const keys = [
      ["clubSpeed", "club_speed_mph"],
      ["attack", "attack_deg"],
      ["path", "path_deg"],
      ["face", "face_deg"],
      ["dynLoft", "dyn_loft_deg"],
    ];
    const out = { ...delivery };
    for (const [key, dom] of keys) {
      const v = out[key];
      if (!isFiniteNumber(v)) throw new ValueError(`${dom} must be finite, got ${pyRepr(v)}`);
      out[key] = Math.min(Math.max(v, DOMAIN[dom][0]), DOMAIN[dom][1]);
    }
    // The lie and strike inputs are optional: absent means 0, present is clamped like the rest.
    for (const [key, dom] of [["lie", "lie_deg"], ["strikeToe", "strike_toe_mm"], ["strikeUp", "strike_up_mm"]]) {
      const v = out[key] === undefined || out[key] === null ? 0.0 : out[key];
      if (!isFiniteNumber(v)) throw new ValueError(`${dom} must be finite, got ${pyRepr(v)}`);
      out[key] = Math.min(Math.max(v, DOMAIN[dom][0]), DOMAIN[dom][1]);
    }
    const floor = DOMAIN.min_spin_loft_deg;
    if (out.dynLoft - out.attack < floor) {
      out.dynLoft = Math.min(out.attack + floor, DOMAIN.dyn_loft_deg[1]);
      // Unreachable with the shipped domain (attack tops out at 10 and dynamic loft at 65, so
      // attack + floor always fits). Kept so a refit domain with a tighter loft range stays deliverable.
      if (out.dynLoft - out.attack < floor) out.attack = out.dynLoft - floor;
    }
    return out;
  }

  // -------------------------------------------------------------------------
  // classify.py
  // -------------------------------------------------------------------------

  const START_STRAIGHT_DEG = CLS.start_straight_deg;
  const AXIS_STRAIGHT_DEG = CLS.axis_straight_deg;
  const CURVE_HOOK_FRAC = CLS.curve_hook_frac;
  const ON_TARGET_FRAC = CLS.on_target_frac;
  const ON_LINE_YD = CLS.on_line_yd;

  const SHAPE_SIDE = { draw: "left", hook: "left", fade: "right", slice: "right" };
  const START_SIDE = { pull: "left", push: "right" };

  function startOf(launchDir) {
    if (launchDir < -START_STRAIGHT_DEG) return "pull";
    if (launchDir > START_STRAIGHT_DEG) return "push";
    return "straight";
  }

  function shapeOf(spinAxis, curve, carry) {
    if (Math.abs(spinAxis) <= AXIS_STRAIGHT_DEG) return "straight";
    // A curve of exactly zero takes the side of the spin axis.
    const left = curve < 0.0 || (curve === 0.0 && spinAxis < 0.0);
    const sharp = Math.abs(curve) > CURVE_HOOK_FRAC * carry;
    if (left) return sharp ? "hook" : "draw";
    return sharp ? "slice" : "fade";
  }

  function nameOf(start, shape, onTarget) {
    if (start === "straight") return [capitalize(shape), false];
    if (shape === "straight") return [capitalize(start), false];
    if (START_SIDE[start] !== SHAPE_SIDE[shape] && onTarget) return [capitalize(shape), true];
    return [`${capitalize(start)} ${shape}`, false];
  }

  function finishText(side) {
    if (Math.abs(side) < ON_LINE_YD) return "finishes on line";
    const dir = side > 0.0 ? "right" : "left";
    return `finishes ${Math.round(Math.abs(side))} yd ${dir}`;
  }

  /** classify.py classify: ball flight name from launch and flight numbers. Right-handed, positive is right. */
  function classify(launchDir, spinAxis, curve, side, carry) {
    for (const [name, v] of [["launch_dir_deg", launchDir], ["spin_axis_deg", spinAxis], ["curve_yd", curve],
      ["side_yd", side], ["carry_yd", carry]]) {
      if (!isFiniteNumber(v)) throw new ValueError(`${name} must be finite, got ${pyRepr(v)}`);
    }
    if (carry <= 0.0) throw new ValueError(`carry_yd must be > 0, got ${pyRepr(carry)}`);
    const start = startOf(launchDir);
    const shape = shapeOf(spinAxis, curve, carry);
    const onTarget = Math.abs(side) <= ON_TARGET_FRAC * carry;
    const [name, workedBack] = nameOf(start, shape, onTarget);
    return { start, shape, name, workedBack, finishYd: side, finishText: finishText(side) };
  }

  // -------------------------------------------------------------------------
  // presets.py (values come from presets.json)
  // -------------------------------------------------------------------------

  /** presets.preset: a club delivery per club and player. */
  function preset(club, player) {
    if (!PLAYERS.includes(player)) {
      throw new ValueError(`player must be one of (${PLAYERS.map((p) => `'${p}'`).join(", ")}), got ${pyRepr(player)}`);
    }
    if (!CLUBS.includes(club)) {
      throw new ValueError(`club must be one of (${CLUBS.map((c) => `'${c}'`).join(", ")}), got ${pyRepr(club)}`);
    }
    return presetFromRow(presetRow(player, club));
  }

  /** presets._check_speed: ValueError unless clubSpeed is finite and inside the domain. */
  function checkSpeed(clubSpeed) {
    const lo = DOMAIN.club_speed_mph[0];
    const hi = DOMAIN.club_speed_mph[1];
    if (!(isFiniteNumber(clubSpeed) && lo <= clubSpeed && clubSpeed <= hi)) {
      throw new ValueError(`club_speed must be within ${pyG(lo)} to ${pyG(hi)} mph, got ${pyRepr(clubSpeed)}`);
    }
  }

  /** presets.scale_speed: copy of a preset with only the club speed changed. The spin trim stays.
   *  The copy's `ideal` stays at the old club speed: call idealDelivery for the ideal at the new one. */
  function scaleSpeed(presetObj, clubSpeed) {
    checkSpeed(clubSpeed);
    return { ...presetObj, clubSpeed };
  }

  /**
   * presets.loft_for_attack: the input dynamic loft when the loft follows the attack angle (MODELED).
   * Hybrids, fairway woods, irons and wedges: preset dynLoft + coupling.loft_per_attack * (attack -
   * preset attack), so hitting up adds loft. Below the preset attack the loft taken off follows the slope
   * for the first 3 degrees and rolls off to at most 5 (followedChange). The driver: optimalLoft at the
   * preset club speed. Through clampLoft, so it is always a loft deliver() accepts.
   * Throws ValueError for an unknown club or player, or an attack outside the domain.
   */
  function loftForAttack(club, player, attack) {
    const p = preset(club, player);
    const loA = DOMAIN.attack_deg[0];
    const hiA = DOMAIN.attack_deg[1];
    if (!(isFiniteNumber(attack) && loA <= attack && attack <= hiA)) {
      throw new ValueError(`attack must be within ${pyG(loA)} to ${pyG(hiA)} deg, got ${pyRepr(attack)}`);
    }
    const dl = club === "driver"
      ? optimalLoft(p.clubSpeed, attack).dynLoft
      : p.dynLoft + followedChange(LOFT_PER_ATTACK * (attack - p.attack));
    return clampLoft(dl, attack);
  }

  /**
   * presets._followed_change: loft change for a raw change of m * (attack - preset attack). Upward it
   * is the raw change. Downward it follows the slope for the first DELOFT_LINEAR degrees of deloft,
   * then rolls off exponentially to DELOFT_MAX (value and slope continuous at the join).
   */
  function followedChange(raw) {
    if (raw >= 0.0) return raw;
    let deloft = -raw;
    if (deloft > DELOFT_LINEAR) {
      deloft = DELOFT_LINEAR + (DELOFT_MAX - DELOFT_LINEAR) * (1.0 - Math.exp(-(deloft - DELOFT_LINEAR) / (DELOFT_MAX - DELOFT_LINEAR)));
    }
    return -deloft;
  }

  /**
   * presets.ideal_delivery: the ideal delivery for a club and player at a club speed
   * (default the preset's). Same fields as preset().ideal. The driver's is the player's
   * club speed, attack driver_ideal.attack_deg, dynamic loft optimalLoft(speed, attack),
   * path 0, face 0, spin trim driver_ideal.spin_trim. Every other club repeats its preset
   * at that club speed. Throws ValueError for a speed outside the domain.
   */
  function idealDelivery(club, player, clubSpeed) {
    const p = preset(club, player);
    const speed = clubSpeed === undefined || clubSpeed === null ? p.clubSpeed : clubSpeed;
    checkSpeed(speed);
    const { atIdeal, ...base } = p.ideal; // atIdeal is only valid at the preset club speed
    if (club === "driver") {
      const ol = optimalLoft(speed, DRIVER_IDEAL.attack_deg);
      return { ...base, clubSpeed: speed, attack: DRIVER_IDEAL.attack_deg, dynLoft: ol.dynLoft, path: 0.0, face: 0.0,
        spinTrim: DRIVER_IDEAL.spin_trim, speedClamped: ol.speedClamped };
    }
    return { ...base, clubSpeed: speed, speedClamped: false };
  }

  // -------------------------------------------------------------------------
  // Convenience: deliver + simulate + roll + classify
  // -------------------------------------------------------------------------

  /**
   * One full shot from a delivery object {clubSpeed, attack, path, face,
   * dynLoft, club, spinTrim}. opts.dt overrides the step size. Returns
   * {delivery, launch, flight, total, classification}, classification null
   * when the carry is zero or less.
   */
  function shot(delivery, opts) {
    if (delivery === null || typeof delivery !== "object") {
      throw new ValueError(`delivery must be an object, got ${pyRepr(delivery)}`);
    }
    const launch = deliver(
      delivery.clubSpeed, delivery.attack, delivery.path, delivery.face, delivery.dynLoft, delivery.club,
      { spinTrim: delivery.spinTrim === undefined ? 1.0 : delivery.spinTrim, lie: delivery.lie, strikeToe: delivery.strikeToe, strikeUp: delivery.strikeUp }
    );
    const flight = simulate(launch.ballSpeedMph, launch.launchDeg, launch.launchDirDeg, launch.spinRpm, launch.spinAxisDeg, opts);
    const total = roll(flight);
    // classify() rejects a carry of zero or less (a ball driven into the ground), so the shot has no name.
    const classification = flight.carry > 0.0
      ? classify(launch.launchDirDeg, launch.spinAxisDeg, flight.curve, flight.side, flight.carry)
      : null;
    return { delivery: { ...delivery }, launch, flight, total, classification };
  }

  /**
   * Value of one metric (any key of METRIC_FIELDS, which covers model.metrics)
   * in a shot() result, for example metricValue("carry_yd", s) is s.flight.carry.
   */
  function metricValue(metric, shotResult) {
    const path = Object.prototype.hasOwnProperty.call(METRIC_FIELDS, metric) ? METRIC_FIELDS[metric] : undefined;
    if (path === undefined) {
      throw new ValueError(`metric must be one of (${Object.keys(METRIC_FIELDS).map((m) => `'${m}'`).join(", ")}), got ${pyRepr(metric)}`);
    }
    let cur = shotResult;
    for (const part of path) {
      if (cur === null || typeof cur !== "object") throw new ValueError(`shot result has no ${path.join(".")} for metric ${pyRepr(metric)}`);
      cur = cur[part];
    }
    return cur;
  }

  // -------------------------------------------------------------------------
  // ideals.py
  // -------------------------------------------------------------------------

  const TM = IDL.driver.trackman_carry_2010;
  const PG = IDL.driver.ping_2019;
  const TT = IDL.driver.trackman_total_2010;

  /** (lower index, upper index, fraction) of x in a sorted grid, clamped to its range. */
  function bracket(grid, x) {
    if (x <= grid[0]) return [0, 0, 0.0];
    if (x >= grid[grid.length - 1]) return [grid.length - 1, grid.length - 1, 0.0];
    let hi = 0;
    while (!(grid[hi] >= x)) hi++; // first grid value >= x, like Python's next(...)
    const lo = hi - 1;
    return [lo, hi, (x - grid[lo]) / (grid[hi] - grid[lo])];
  }

  /** Bilinear in both axes, clamped. Each table is [row][col]. Returns the interpolated value of each table. */
  function bilinear(rowGrid, colGrid, tables, row, col) {
    const [r0, r1, fr] = bracket(rowGrid, row);
    const [c0, c1, fc] = bracket(colGrid, col);
    return tables.map((tb) => {
      const top = tb[r0][c0] * (1 - fc) + tb[r0][c1] * fc;
      const bot = tb[r1][c0] * (1 - fc) + tb[r1][c1] * fc;
      return top * (1 - fr) + bot * fr;
    });
  }

  /** ideals.trackman_carry_2010: [launch deg, spin rpm] from the TrackMan 2010 CARRY Optimizer. */
  function trackmanCarry2010(clubSpeed, attack) {
    return bilinear(TM.club_speed_mph, TM.attack_deg, [TM.launch_deg, TM.spin_rpm], clubSpeed, attack);
  }

  /** ideals.trackman_total_2010: [launch deg, spin rpm] from the TrackMan 2010 TOTAL Optimizer. */
  function trackmanTotal2010(clubSpeed, attack) {
    return bilinear(TT.club_speed_mph, TT.attack_deg, [TT.launch_deg, TT.spin_rpm], clubSpeed, attack);
  }

  /** ideals.ping_2019: [launch deg, spin rpm] from the PING 2019 Optimal Launch & Spin chart. */
  function ping2019(ballSpeed, attack) {
    return bilinear(PG.ball_speed_mph, PG.attack_deg, [PG.launch_deg, PG.spin_rpm], ballSpeed, attack);
  }

  /**
   * chart._loft_at: [loft, extrapolated] from one chart's dynamic loft table: linear across the
   * two nearest club speeds (clamped) at each chart attack angle, then linear in attack angle,
   * extended along the edge slope beyond the first and last chart attack angles.
   */
  function loftAt(grid, clubSpeed, attack) {
    const aoas = grid.attack_deg;
    const [s0, s1, fs] = bracket(grid.club_speed_mph, clubSpeed);
    const loft = aoas.map((_a, j) => grid.dyn_loft_deg[s0][j] * (1 - fs) + grid.dyn_loft_deg[s1][j] * fs);
    const aLo = aoas[0], aMid = aoas[1], aHi = aoas[2];
    if (attack > aHi) return [loft[2] + ((loft[2] - loft[1]) / (aHi - aMid)) * (attack - aHi), true];
    if (attack < aLo) return [loft[0] + ((loft[1] - loft[0]) / (aMid - aLo)) * (attack - aLo), true];
    if (attack <= aMid) {
      const t = (attack - aLo) / (aMid - aLo);
      return [loft[0] * (1 - t) + loft[1] * t, false];
    }
    const t = (attack - aMid) / (aHi - aMid);
    return [loft[1] * (1 - t) + loft[2] * t, false];
  }

  /**
   * chart.optimal_loft: balanced dynamic loft, the mean of the TrackMan 2010 CARRY chart's and
   * TOTAL chart's optimal dynamic loft, each bilinear over club speed (clamped to 75 to 120 mph)
   * and attack angle (-5, 0, +5). Beyond -5 or +5 each loft extends along its edge slope and
   * `extrapolated` is true. Returns {dynLoft, carryLoft, totalLoft, extrapolated, speedClamped}.
   * Throws ValueError for a non-finite input.
   */
  function optimalLoft(clubSpeed, attack) {
    for (const [name, v] of [["club_speed_mph", clubSpeed], ["attack_deg", attack]]) {
      if (!isFiniteNumber(v)) throw new ValueError(`${name} must be finite, got ${pyRepr(v)}`);
    }
    const [carryLoft, extrapolated] = loftAt(TM, clubSpeed, attack);
    const [totalLoft] = loftAt(TT, clubSpeed, attack);
    const speeds = TM.club_speed_mph;
    const speedClamped = clubSpeed < speeds[0] || clubSpeed > speeds[speeds.length - 1];
    return { dynLoft: 0.5 * (carryLoft + totalLoft), carryLoft, totalLoft, extrapolated, speedClamped };
  }

  function fly(p) {
    const ln = deliver(p.clubSpeed, p.attack, p.path, p.face, p.dynLoft, p.club, { spinTrim: p.spinTrim });
    const f = simulate(ln.ballSpeedMph, ln.launchDeg, ln.launchDirDeg, ln.spinRpm, ln.spinAxisDeg);
    return [ln, f];
  }

  /**
   * ideals.ideal_bands: bands for the TrackMan-style tiles. clubSpeed scales
   * ball speed and carry (and moves the driver's optimizer lookups), attack
   * moves only the driver's optimizer lookups. lo, hi and target are computed
   * here. source_id, source, modeled and published are static per club and
   * player and are read from ideals.json (source text from its `sources`).
   */
  function idealBands(club, player, clubSpeed, attack) {
    const p = preset(club, player);
    const ideal0 = p.ideal; // at the preset club speed
    const [ln0, f0] = fly(ideal0);
    const speed = clubSpeed === undefined || clubSpeed === null ? p.clubSpeed : clubSpeed;
    const idealS = idealDelivery(club, player, speed); // throws ValueError outside the domain
    const [lnS, fS] = speed === p.clubSpeed ? [ln0, f0] : fly(idealS);
    const aoa = attack === undefined || attack === null ? ideal0.attack : attack;
    const loA = DOMAIN.attack_deg[0];
    const hiA = DOMAIN.attack_deg[1];
    if (!(isFiniteNumber(aoa) && loA <= aoa && aoa <= hiA)) {
      throw new ValueError(`attack must be within ${pyG(loA)} to ${pyG(hiA)} deg, got ${pyRepr(aoa)}`);
    }
    const carry = fS.carry;
    const total = roll(fS);
    const driver = club === "driver";

    const b = {};
    const put = (metric, lo, hi, target) => {
      const meta = bandMeta(player, club, metric);
      const out = { lo, hi, target, source_id: meta.source_id, source: bandSource(meta.source_id), modeled: meta.modeled };
      if (meta.published !== undefined) out.published = meta.published;
      b[metric] = out;
      return out;
    };
    const around = (metric, center, half) => put(metric, center - half, center + half, center);

    around("club_speed_mph", p.clubSpeed, TOL.club_speed_frac * p.clubSpeed);
    if (driver) put("attack_deg", DRIVER_IDEAL.attack_lo_deg, DRIVER_IDEAL.attack_hi_deg, DRIVER_IDEAL.attack_deg);
    else around("attack_deg", p.attack, TOL.attack_deg);
    around("path_deg", 0.0, TOL.path_deg);
    around("face_deg", 0.0, TOL.face_deg);
    around("face_to_path_deg", 0.0, TOL.face_to_path_deg);
    if (driver) around("dyn_loft_deg", optimalLoft(speed, aoa).dynLoft, DRIVER_IDEAL.dyn_loft_half_deg);
    else around("dyn_loft_deg", p.dynLoft, TOL.dyn_loft_deg);
    around("spin_loft_deg", ln0.spinLoftDeg, TOL.spin_loft_deg);
    around("ball_speed_mph", lnS.ballSpeedMph, TOL.ball_speed_frac * lnS.ballSpeedMph);
    put("smash", ln0.smash - TOL.smash_below, null, ln0.smash);
    around("launch_deg", ln0.launchDeg, TOL.launch_deg);
    around("launch_dir_deg", 0.0, TOL.launch_dir_deg);
    around("spin_rpm", ln0.spinRpm, TOL.spin_frac * ln0.spinRpm);
    around("spin_axis_deg", 0.0, TOL.spin_axis_deg);
    around("max_height_yd", f0.maxHeight, TOL.max_height_yd);
    put("land_angle_deg", f0.landAngle - TOL.land_angle_below_deg, null, f0.landAngle);
    around("carry_yd", carry, TOL.carry_frac * carry);
    around("total_yd", total, TOL.total_frac * total);
    around("side_yd", 0.0, TOL.side_frac * carry);
    around("curve_yd", 0.0, TOL.curve_frac * carry);

    if (driver) {
      const [tmLaunch, tmSpin] = trackmanCarry2010(speed, aoa);
      const [ttLaunch, ttSpin] = trackmanTotal2010(speed, aoa);
      const [pgLaunch, pgSpin] = ping2019(lnS.ballSpeedMph, aoa);
      const ml = TOL.driver_launch_margin_deg;
      const mr = TOL.driver_spin_margin_rpm;
      const launches = [tmLaunch, ttLaunch, pgLaunch];
      const spins = [tmSpin, ttSpin, pgSpin];
      // Each band gets its own detail object.
      const detail = () => ({
        trackman_carry_2010: { launch_deg: tmLaunch, spin_rpm: tmSpin },
        trackman_total_2010: { launch_deg: ttLaunch, spin_rpm: ttSpin },
        ping_2019: { launch_deg: pgLaunch, spin_rpm: pgSpin },
        inputs: { club_speed_mph: speed, ball_speed_mph: lnS.ballSpeedMph, attack_deg: aoa },
      });
      put("launch_deg", Math.min(...launches) - ml, Math.max(...launches) + ml,
        (launches[0] + launches[1] + launches[2]) / 3.0).detail = detail();
      put("spin_rpm", Math.min(...spins) - mr, Math.max(...spins) + mr,
        (spins[0] + spins[1] + spins[2]) / 3.0).detail = detail();
    }
    return b;
  }

  // -------------------------------------------------------------------------

  return {
    // Python-mirrored API
    deliver,
    simulate,
    roll,
    classify,
    launchVector,
    swingPath,
    swingDirection,
    swingPlaneFor,
    gearEffect,
    preset,
    scaleSpeed,
    couplingKappa,
    effectiveLoft,
    idealDelivery,
    loftForAttack,
    optimalLoft,
    idealBands,
    trackmanCarry2010,
    trackmanTotal2010,
    ping2019,
    // Convenience
    shot,
    clampToDomain,
    metricValue,
    // Data for the page
    domain: FROZEN_DOMAIN,
    clubs: PRE.clubs,
    groups: PRE.groups,
    players: PRE.players,
    metrics: IDL.metrics,
    windows: json.windows,
    camera: json.camera,
    data: json,
  };
}

/**
 * Fetch model.json, presets.json, ideals.json, windows.json and camera.json
 * from a data directory and build a Model. baseUrl is a URL or a string ending
 * in a slash (one without is given a slash). The default is the data folder next
 * to this module, so it works from any page that imports it. Throws RuntimeError
 * when a file cannot be fetched or parsed.
 */
export async function loadModel(baseUrl = new URL("data/", import.meta.url)) {
  const dir = baseUrl instanceof URL ? baseUrl.href : String(baseUrl);
  const base = dir.endsWith("/") ? dir : dir + "/";
  const names = ["model", "presets", "ideals", "windows", "camera"];
  const parts = await Promise.all(
    names.map(async (n) => {
      const url = base + n + ".json";
      let res;
      try {
        res = await fetch(url);
      } catch (e) {
        throw new RuntimeError(`could not load ${url}: ${e && e.message}`);
      }
      if (!res.ok) throw new RuntimeError(`could not load ${url}: HTTP ${res.status}`);
      try {
        return await res.json();
      } catch (e) {
        throw new RuntimeError(`could not parse ${url}: ${e && e.message}`);
      }
    })
  );
  const json = {};
  names.forEach((n, i) => {
    json[n] = parts[i];
  });
  return createModel(json);
}
