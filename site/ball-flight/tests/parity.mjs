// Parity test: site/ball-flight/flight.js against the Python model.
//
//   node site/ball-flight/tests/parity.mjs
//
// Loads the JSON that export.py writes to site/ball-flight/data from disk,
// replays every case in golden.json through the JS port, and compares:
//   deliver outputs        1e-6 relative or 1e-6 absolute, whichever is looser
//   flight summaries       0.01 yd, 0.01 deg, 0.01 mph, 0.001 s
//   trajectory samples     0.01 yd (x, y, z), 1e-6 (t)
//   classify outputs       exact (finish_yd within 0.01 yd when it comes from a simulated flight)
// It also checks that invalid inputs throw, that the preset and ideal band
// data recompute from the model, and prints the mean time of one shot().
// Exit code 0 when everything passes, 1 otherwise.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createModel, loadModel, ValueError, RuntimeError, METRIC_FIELDS } from "../flight.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const DATA = join(HERE, "..", "data");
const load = (name) => JSON.parse(readFileSync(join(DATA, name + ".json"), "utf8"));

const json = {};
for (const n of ["model", "presets", "ideals", "windows", "camera"]) json[n] = load(n);
const golden = load("golden");
const model = createModel(json);

// ---------------------------------------------------------------------------
// Bookkeeping
// ---------------------------------------------------------------------------

const cats = new Map();
const failures = [];

function cat(name) {
  if (!cats.has(name)) cats.set(name, { checks: 0, fails: 0, maxDev: 0, maxWhere: "" });
  return cats.get(name);
}

function fail(name, where, msg) {
  cat(name).fails++;
  failures.push(`[${name}] ${where}: ${msg}`);
}

/** Compare numbers with an absolute tolerance, or the looser of 1e-6 relative and absolute. */
function near(name, where, actual, expected, tol, relative = false) {
  const c = cat(name);
  c.checks++;
  const dev = Math.abs(actual - expected);
  const limit = relative ? Math.max(tol, tol * Math.abs(expected)) : tol;
  if (!(dev <= limit)) {
    fail(name, where, `got ${actual}, expected ${expected}, deviation ${dev} > ${limit}`);
    return;
  }
  const scaled = relative ? dev / Math.max(1, Math.abs(expected)) : dev;
  if (scaled > c.maxDev) {
    c.maxDev = scaled;
    c.maxWhere = where;
  }
}

function exact(name, where, actual, expected) {
  cat(name).checks++;
  if (actual !== expected) fail(name, where, `got ${JSON.stringify(actual)}, expected ${JSON.stringify(expected)}`);
}

function throwsWith(name, where, fn, needle, cls = ValueError) {
  cat(name).checks++;
  try {
    fn();
  } catch (e) {
    if (!(e instanceof cls) || !e.message.includes(needle)) {
      fail(name, where, `threw ${e && e.name} "${e && e.message}", expected ${cls.name} naming "${needle}"`);
    }
    return;
  }
  fail(name, where, `did not throw, expected ${cls.name} naming "${needle}"`);
}

function doesNotThrow(name, where, fn) {
  cat(name).checks++;
  try {
    fn();
  } catch (e) {
    fail(name, where, `threw "${e.message}"`);
  }
}

// ---------------------------------------------------------------------------
// Schema adapter: golden.json and windows keys (Python snake_case) to JS fields.
// ---------------------------------------------------------------------------

const LAUNCH_KEYS = {
  ball_speed_mph: "ballSpeedMph", smash: "smash", launch_deg: "launchDeg", launch_dir_deg: "launchDirDeg",
  spin_rpm: "spinRpm", spin_axis_deg: "spinAxisDeg", spin_loft_deg: "spinLoftDeg", face_to_path_deg: "faceToPathDeg",
};
const FLIGHT_KEYS = {
  carry_yd: ["carry", 0.01], side_yd: ["side", 0.01], curve_yd: ["curve", 0.01],
  max_height_yd: ["maxHeight", 0.01], apex_x_yd: ["apexX", 0.01], land_angle_deg: ["landAngle", 0.01],
  flight_time_s: ["flightTime", 0.001], land_speed_mph: ["landSpeed", 0.01], total_yd: ["total", 0.01],
};

function compareLaunch(catName, id, ln, exp) {
  for (const [k, js] of Object.entries(LAUNCH_KEYS)) near(catName, `${id}.${k}`, ln[js], exp[k], 1e-6, true);
}

function compareFlight(catName, id, f, exp) {
  for (const [k, [js, tol]] of Object.entries(FLIGHT_KEYS)) near(catName, `${id}.${k}`, f[js], exp[k], tol);
}

function compareClassification(catName, id, got, exp, finishTol) {
  exact(catName, `${id}.start`, got.start, exp.start);
  exact(catName, `${id}.shape`, got.shape, exp.shape);
  exact(catName, `${id}.name`, got.name, exp.name);
  exact(catName, `${id}.worked_back`, got.workedBack, exp.worked_back);
  exact(catName, `${id}.finish_text`, got.finishText, exp.finish_text);
  if (finishTol === 0) exact(catName, `${id}.finish_yd`, got.finishYd, exp.finish_yd);
  else near(catName, `${id}.finish_yd`, got.finishYd, exp.finish_yd, finishTol);
}

/** A golden delivery record as the delivery object shot() takes. */
const fromGolden = (d) => ({ clubSpeed: d.club_speed_mph, attack: d.attack_deg, path: d.path_deg, face: d.face_deg,
  dynLoft: d.dyn_loft_deg, club: d.club, spinTrim: d.spin_trim });

/** deliver, simulate, roll and classify from a golden or window delivery record. */
function run(d, club, spinTrim, dt) {
  const ln = model.deliver(d.club_speed_mph, d.attack_deg, d.path_deg, d.face_deg, d.dyn_loft_deg, club, { spinTrim });
  const f = model.simulate(ln.ballSpeedMph, ln.launchDeg, ln.launchDirDeg, ln.spinRpm, ln.spinAxisDeg, dt ? { dt } : undefined);
  f.total = model.roll(f);
  // classify() rejects a carry of zero or less. The golden fixture has null there.
  const cls = f.carry > 0 ? model.classify(ln.launchDirDeg, ln.spinAxisDeg, f.curve, f.side, f.carry) : null;
  return { ln, f, cls };
}

// ---------------------------------------------------------------------------
// 1. golden cases: deliver, flight, trajectory, classify
// ---------------------------------------------------------------------------

for (const c of golden.cases) {
  const { ln, f, cls } = run(c.delivery, c.delivery.club, c.delivery.spin_trim, golden.dt);
  compareLaunch("deliver", c.id, ln, c.launch);
  compareFlight("flight", c.id, f, c.flight);
  near("flight", `${c.id}.land_spin_rpm`, f.landSpin, c.flight.land_spin_rpm, 0.5);
  if (c.classification === null) {
    exact("classify (cases)", `${c.id} null classification`, cls, null);
    throwsWith("classify (cases)", `${c.id} carry <= 0`, () => model.classify(ln.launchDirDeg, ln.spinAxisDeg, f.curve, f.side, f.carry), "carry_yd");
    exact("classify (cases)", `${c.id} shot() classification`, model.shot(fromGolden(c.delivery)).classification, null);
  } else {
    compareClassification("classify (cases)", c.id, cls, c.classification, 0.01);
  }
  if (c.trajectory) {
    const tr = c.trajectory;
    exact("trajectory", `${c.id}.length`, f.t.length - 1, tr.indices[tr.indices.length - 1]);
    tr.indices.forEach((i, j) => {
      near("trajectory", `${c.id}.t[${i}]`, f.t[i], tr.t[j], 1e-6, true);
      near("trajectory", `${c.id}.x[${i}]`, f.x[i], tr.x[j], 0.01);
      near("trajectory", `${c.id}.y[${i}]`, f.y[i], tr.y[j], 0.01);
      near("trajectory", `${c.id}.z[${i}]`, f.z[i], tr.z[j], 0.01);
    });
  }
}

// ---------------------------------------------------------------------------
// 2. classify vectors, exact
// ---------------------------------------------------------------------------

golden.classify_vectors.forEach((v, i) => {
  const [dir, axis, curve, side, carry] = v.args;
  compareClassification("classify (vectors)", `vector ${i} ${JSON.stringify(v.args)}`,
    model.classify(dir, axis, curve, side, carry), v.result, 0);
});

// ---------------------------------------------------------------------------
// 3. nine windows (PGA 7 iron)
// ---------------------------------------------------------------------------

for (const [key, w] of Object.entries(golden.windows_pga_7i)) {
  const { ln, f, cls } = run(w.delivery, w.club, w.spin_trim);
  compareLaunch("windows", `${key}.launch`, ln, w.launch);
  compareFlight("windows", `${key}.flight`, f, w.flight);
  compareClassification("windows", `${key}.classification`, cls, w.classification, 0.01);
}

// ---------------------------------------------------------------------------
// 4. presets.json: every at_preset summary recomputes from the preset row
// ---------------------------------------------------------------------------

for (const p of json.presets.players.map((x) => x.id)) {
  for (const club of json.presets.clubs.map((x) => x.id)) {
    const pr = model.preset(club, p);
    const ln = model.deliver(pr.clubSpeed, pr.attack, pr.path, pr.face, pr.dynLoft, pr.club, { spinTrim: pr.spinTrim });
    const fl = model.simulate(ln.ballSpeedMph, ln.launchDeg, ln.launchDirDeg, ln.spinRpm, ln.spinAxisDeg);
    fl.total = model.roll(fl);
    // The preset row is rounded to 6 significant digits, so allow 1e-4 relative on the launch side.
    for (const [k, js] of Object.entries(LAUNCH_KEYS)) near("presets", `${p}.${club}.${k}`, ln[js], pr.atPreset.launch[k], 1e-4, true);
    for (const [k, [js]] of Object.entries(FLIGHT_KEYS)) near("presets", `${p}.${club}.${k}`, fl[js], pr.atPreset.flight[k], 0.05);
  }
}

// 4b. ideal deliveries: presets.json ideal recomputes, idealDelivery agrees, optimalLoft vectors

for (const p of json.presets.players.map((x) => x.id)) {
  for (const club of json.presets.clubs.map((x) => x.id)) {
    const pr = model.preset(club, p);
    const id = pr.ideal;
    const where = `${p}.${club}.ideal`;
    const ln = model.deliver(id.clubSpeed, id.attack, id.path, id.face, id.dynLoft, id.club, { spinTrim: id.spinTrim });
    const fl = model.simulate(ln.ballSpeedMph, ln.launchDeg, ln.launchDirDeg, ln.spinRpm, ln.spinAxisDeg);
    fl.total = model.roll(fl);
    for (const [k, js] of Object.entries(LAUNCH_KEYS)) near("ideal presets", `${where}.${k}`, ln[js], id.atIdeal.launch[k], 1e-4, true);
    for (const [k, [js]] of Object.entries(FLIGHT_KEYS)) near("ideal presets", `${where}.${k}`, fl[js], id.atIdeal.flight[k], 0.05);
    // idealDelivery at the preset speed is the same delivery, without the stale atIdeal
    const again = model.idealDelivery(club, p);
    for (const k of ["clubSpeed", "attack", "dynLoft", "path", "face", "spinTrim", "club", "label", "source", "modeled", "speedClamped"]) {
      if (typeof id[k] === "number") near("ideal presets", `${where}.${k} idealDelivery`, again[k], id[k], 1e-4, true);
      else exact("ideal presets", `${where}.${k} idealDelivery`, again[k], id[k]);
    }
    exact("ideal presets", `${where}.no atIdeal on idealDelivery`, again.atIdeal, undefined);
    if (club === "driver") {
      const ol = model.optimalLoft(pr.clubSpeed, json.presets.driver_ideal.attack_deg);
      near("ideal presets", `${where}.dynLoft is optimalLoft`, id.dynLoft, ol.dynLoft, 1e-4, true);
      exact("ideal presets", `${where}.attack`, id.attack, json.presets.driver_ideal.attack_deg);
      exact("ideal presets", `${where}.spinTrim`, id.spinTrim, json.presets.driver_ideal.spin_trim);
      exact("ideal presets", `${where}.label`, id.label, json.presets.driver_ideal.label);
    } else {
      near("ideal presets", `${where}.repeats the preset dynLoft`, id.dynLoft, pr.dynLoft, 1e-9, true);
      near("ideal presets", `${where}.repeats the preset attack`, id.attack, pr.attack, 1e-9, true);
    }
  }
}
// the driver's ideal loft follows club speed, every other club keeps its preset
{
  const a = model.idealDelivery("driver", "pga", 100);
  const b = model.idealDelivery("driver", "pga", 115);
  exact("ideal presets", "driver loft falls with speed", a.dynLoft > b.dynLoft, true);
  exact("ideal presets", "7i keeps its loft at another speed", model.idealDelivery("7i", "pga", 80).dynLoft, model.preset("7i", "pga").dynLoft);
  exact("ideal presets", "speed clamped flag", model.idealDelivery("driver", "pga", 60).speedClamped, true);
}
for (const v of golden.optimal_loft_vectors) {
  const [speed, attack] = v.args;
  const r = model.optimalLoft(speed, attack);
  near("optimalLoft", `(${speed}, ${attack})`, r.dynLoft, v.result.dyn_loft_deg, 1e-6, true);
  near("optimalLoft", `(${speed}, ${attack}) carry`, r.carryLoft, v.result.carry_loft_deg, 1e-6, true);
  near("optimalLoft", `(${speed}, ${attack}) total`, r.totalLoft, v.result.total_loft_deg, 1e-6, true);
  exact("optimalLoft", `(${speed}, ${attack}) extrapolated`, r.extrapolated, v.result.extrapolated);
  exact("optimalLoft", `(${speed}, ${attack}) speedClamped`, r.speedClamped, v.result.speed_clamped);
}

// ---------------------------------------------------------------------------
// 5. ideal bands at the preset delivery against ideals.json
// ---------------------------------------------------------------------------

for (const p of Object.keys(json.ideals.bands)) {
  for (const club of Object.keys(json.ideals.bands[p])) {
    const got = model.idealBands(club, p);
    const want = json.ideals.bands[p][club];
    for (const metric of json.ideals.metrics) {
      const where = `${p}.${club}.${metric}`;
      const g = got[metric];
      const w = want[metric];
      for (const side of ["lo", "hi", "target"]) {
        if (w[side] === null) exact("ideal bands", `${where}.${side}`, g[side], null);
        else near("ideal bands", `${where}.${side}`, g[side], w[side], 1e-4, true);
      }
      exact("ideal bands", `${where}.modeled`, g.modeled, w.modeled);
      exact("ideal bands", `${where}.published`, g.published, w.published);
      exact("ideal bands", `${where}.source_id`, g.source_id, w.source_id);
      exact("ideal bands", `${where}.source`, g.source, json.ideals.sources[w.source_id]);
    }
  }
}

// ---------------------------------------------------------------------------
// 6. invalid inputs throw, edges of the domain do not
// ---------------------------------------------------------------------------

const base = [92, -3.9, 0, 0, 23.354, "7i"];
const withArg = (i, v) => base.map((x, j) => (j === i ? v : x));
const DOM = json.model.domain;
const argNames = ["club_speed_mph", "attack_deg", "path_deg", "face_deg", "dyn_loft_deg"];

argNames.forEach((name, i) => {
  const [lo, hi] = DOM[name];
  for (const [label, v] of [["below", lo - 0.001], ["above", hi + 0.001], ["NaN", NaN], ["Infinity", Infinity], ["-Infinity", -Infinity]]) {
    // A dyn_loft below its minimum or an attack above the loft trips the spin loft floor message instead.
    throwsWith("invalid input", `${name} ${label}`, () => model.deliver(...withArg(i, v)), name);
  }
  doesNotThrow("domain edges", `${name} = ${lo}`, () => model.deliver(...withArg(i, lo)));
  doesNotThrow("domain edges", `${name} = ${hi}`, () => model.deliver(...withArg(i, hi)));
});
throwsWith("invalid input", "spin loft below floor", () => model.deliver(90, 5, 0, 0, 5.9, "7i"), "dyn_loft_deg - attack_deg");
doesNotThrow("domain edges", "spin loft at floor", () => model.deliver(90, 5, 0, 0, 6, "7i"));
for (const v of [0, -1, NaN, Infinity]) {
  throwsWith("invalid input", `spin_trim ${v}`, () => model.deliver(...base, { spinTrim: v }), "spin_trim");
}
throwsWith("invalid input", "club", () => model.deliver(92, -3.9, 0, 0, 23.354, "2i"), "club");
doesNotThrow("domain edges", "club null", () => model.deliver(92, -3.9, 0, 0, 23.354, null));

const flightArgs = [150, 12, 0, 3000, 0];
const flightNames = ["ball_speed_mph", "launch_deg", "launch_dir_deg", "spin_rpm", "spin_axis_deg"];
flightNames.forEach((name, i) => {
  for (const v of [NaN, Infinity, -Infinity]) {
    throwsWith("invalid input", `simulate ${name} ${v}`,
      () => model.simulate(...flightArgs.map((x, j) => (j === i ? v : x))), name);
  }
});
throwsWith("invalid input", "simulate ball speed 0", () => model.simulate(0, 12, 0, 3000, 0), "ball_speed_mph");
throwsWith("invalid input", "simulate ball speed -5", () => model.simulate(-5, 12, 0, 3000, 0), "ball_speed_mph");
throwsWith("invalid input", "simulate dt 0", () => model.simulate(150, 12, 0, 3000, 0, { dt: 0 }), "dt");
throwsWith("invalid input", "simulate dt NaN", () => model.simulate(150, 12, 0, 3000, 0, { dt: NaN }), "dt");
throwsWith("invalid input", "simulate never lands", () => model.simulate(1000, 89, 0, 0, 0), "did not land", RuntimeError);
throwsWith("invalid input", "scaleSpeed low", () => model.scaleSpeed(model.preset("7i", "pga"), 39.9), "club_speed");
throwsWith("invalid input", "scaleSpeed NaN", () => model.scaleSpeed(model.preset("7i", "pga"), NaN), "club_speed");
throwsWith("invalid input", "optimalLoft speed NaN", () => model.optimalLoft(NaN, 0), "club_speed");
throwsWith("invalid input", "optimalLoft attack Infinity", () => model.optimalLoft(100, Infinity), "attack");
throwsWith("invalid input", "idealDelivery speed low", () => model.idealDelivery("driver", "pga", 39.9), "club_speed");
throwsWith("invalid input", "idealDelivery NaN", () => model.idealDelivery("driver", "pga", NaN), "club_speed");
throwsWith("invalid input", "idealDelivery club", () => model.idealDelivery("2i", "pga", 100), "club");
throwsWith("invalid input", "preset player", () => model.preset("7i", "scratch"), "player");
throwsWith("invalid input", "preset club", () => model.preset("2i", "pga"), "club");
throwsWith("invalid input", "swingPath plane", () => model.swingPath(0, -3, 20), "plane_deg");
throwsWith("invalid input", "swingPath NaN", () => model.swingPath(NaN, -3), "swing_dir_deg");
throwsWith("invalid input", "classify NaN", () => model.classify(0, NaN, 0, 0, 200), "spin_axis_deg");
throwsWith("invalid input", "classify carry 0", () => model.classify(0, 0, 0, 0, 0), "carry_yd");

// ---------------------------------------------------------------------------
// 7. helpers the page leans on
// ---------------------------------------------------------------------------

// clampToDomain always yields a delivery that deliver() accepts.
let seed = 12345;
const rnd = () => ((seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296);
for (let i = 0; i < 500; i++) {
  const wild = { clubSpeed: rnd() * 300 - 80, attack: rnd() * 60 - 30, path: rnd() * 60 - 30, face: rnd() * 60 - 30,
    dynLoft: rnd() * 120 - 20, club: "7i", spinTrim: 1 };
  const c = model.clampToDomain(wild);
  doesNotThrow("clampToDomain", `sample ${i}`, () => model.shot(c));
}
{
  const inside = { clubSpeed: 92, attack: -3.9, path: 1, face: 2, dynLoft: 23.354, club: "7i", spinTrim: 0.98 };
  const c = model.clampToDomain(inside);
  for (const k of Object.keys(inside)) exact("clampToDomain", `identity ${k}`, c[k], inside[k]);
}
// scaleSpeed keeps the spin trim, swingPath matches the closed form.
{
  const pr = model.preset("driver", "pga");
  const sc = model.scaleSpeed(pr, 100);
  exact("helpers", "scaleSpeed clubSpeed", sc.clubSpeed, 100);
  exact("helpers", "scaleSpeed spinTrim", sc.spinTrim, pr.spinTrim);
  exact("helpers", "scaleSpeed leaves the input", pr.clubSpeed === 100, false);
  near("helpers", "swingPath", model.swingPath(1, -4), 1 - -4 * Math.tan((90 - json.model.swing_plane_default_deg) * Math.PI / 180), 1e-12);
  exact("helpers", "swingPath -0", Object.is(model.swingPath(0, 0), 0), true);
  const s = model.shot({ ...pr, spinTrim: pr.spinTrim });
  exact("helpers", "shot total >= carry", s.total >= s.flight.carry, true);
}

// ---------------------------------------------------------------------------
// 8. ideal bands at non-preset club speeds and attack angles (Python fixture)
// ---------------------------------------------------------------------------

const fixture = JSON.parse(readFileSync(join(HERE, "ideals_fixture.json"), "utf8"));
const fixNum = (v) => (v === null ? undefined : v === "NaN" ? NaN : v);
fixture.points.forEach((pt, i) => {
  const label = `${pt.club}.${pt.player}@${pt.club_speed_mph},${pt.attack_deg}`;
  const got = model.idealBands(pt.club, pt.player, fixNum(pt.club_speed_mph), fixNum(pt.attack_deg));
  exact("ideal bands (fixture)", `${label} metric list`, Object.keys(got).sort().join(","), Object.keys(pt.bands).sort().join(","));
  for (const [metric, w] of Object.entries(pt.bands)) {
    const g = got[metric];
    if (!g) {
      fail("ideal bands (fixture)", `${label}.${metric}`, "missing band");
      continue;
    }
    for (const side of ["lo", "hi", "target"]) {
      if (w[side] === null) exact("ideal bands (fixture)", `${label}.${metric}.${side}`, g[side], null);
      else near("ideal bands (fixture)", `${label}.${metric}.${side}`, g[side], w[side], 1e-4, true);
    }
    exact("ideal bands (fixture)", `${label}.${metric}.modeled`, g.modeled, w.modeled);
    exact("ideal bands (fixture)", `${label}.${metric}.published`, g.published, w.published);
    if (w.detail) {
      for (const src of ["trackman_carry_2010", "trackman_total_2010", "ping_2019"]) {
        for (const k of ["launch_deg", "spin_rpm"]) {
          near("ideal bands (fixture)", `${label}.${metric}.detail.${src}.${k}`, g.detail[src][k], w.detail[src][k], 1e-4, true);
        }
      }
      for (const k of Object.keys(w.detail.inputs)) {
        near("ideal bands (fixture)", `${label}.${metric}.detail.inputs.${k}`, g.detail.inputs[k], w.detail.inputs[k], 1e-4, true);
      }
    } else {
      exact("ideal bands (fixture)", `${label}.${metric}.detail`, g.detail, undefined);
    }
  }
});
for (const e of fixture.errors) {
  throwsWith("ideal bands (fixture)", `error ${e.club} ${e.player} ${e.club_speed_mph} ${e.attack_deg}`,
    () => model.idealBands(e.club, e.player, fixNum(e.club_speed_mph), fixNum(e.attack_deg)),
    e.message.startsWith("attack") ? "attack" : "club_speed");
}

// ---------------------------------------------------------------------------
// 9. metricValue and METRIC_FIELDS
// ---------------------------------------------------------------------------

for (const m of json.ideals.metrics) exact("metricValue", `${m} has a field`, Object.hasOwn(METRIC_FIELDS, m), true);
for (const id of ["preset_pga_driver", "golfer_push_slice", "curvature_lpga_6i_-2", "edge_slow_7i", "preset_amateur_pw"]) {
  const c = golden.cases.find((x) => x.id === id);
  const sh = model.shot(fromGolden(c.delivery), { dt: golden.dt });
  for (const m of [...json.ideals.metrics, "spin_trim", "apex_x_yd", "flight_time_s", "land_speed_mph", "total_yd"]) {
    const want = m in c.delivery ? c.delivery[m] : m in c.launch ? c.launch[m] : c.flight[m];
    exact("metricValue", `${id}.${m} defined in golden`, typeof want, "number");
    near("metricValue", `${id}.${m}`, model.metricValue(m, sh), want, 0.01);
  }
}
throwsWith("metricValue", "unknown metric", () => model.metricValue("nope", model.shot(model.preset("7i", "pga"))), "metric");
throwsWith("metricValue", "inherited key", () => model.metricValue("constructor", model.shot(model.preset("7i", "pga"))), "metric");
throwsWith("metricValue", "no shot", () => model.metricValue("carry_yd", undefined), "carry_yd");

// ---------------------------------------------------------------------------
// 10. copies and loading
// ---------------------------------------------------------------------------

{
  const d = { clubSpeed: 92, attack: -3.9, path: 0, face: 0, dynLoft: 23.354, club: "7i", spinTrim: 1 };
  const sh = model.shot(d);
  sh.delivery.clubSpeed = 1;
  exact("copies", "shot delivery is a copy", d.clubSpeed, 92);
  exact("copies", "shot delivery is not the input", sh.delivery === d, false);
  const p1 = model.preset("7i", "pga");
  p1.atPreset.launch.smash = -1;
  exact("copies", "atPreset is a deep copy", model.preset("7i", "pga").atPreset.launch.smash > 0, true);
  const b = model.idealBands("driver", "pga");
  exact("copies", "driver detail objects differ", b.launch_deg.detail === b.spin_rpm.detail, false);
  b.launch_deg.detail.inputs.attack_deg = 99;
  exact("copies", "detail edit does not leak", b.spin_rpm.detail.inputs.attack_deg === 99, false);
  exact("copies", "domain frozen", Object.isFrozen(model.domain) && Object.isFrozen(model.domain.attack_deg), true);
  exact("copies", "domain is not the data", model.domain === json.model.domain, false);
  throwsWith("copies", "domain write", () => { model.domain.attack_deg[0] = -50; }, "", TypeError);
  exact("copies", "domain still intact", model.domain.attack_deg[0], -10);
}
throwsWith("invalid input", "shot(undefined)", () => model.shot(undefined), "delivery");
throwsWith("invalid input", "shot(null)", () => model.shot(null), "delivery");
throwsWith("invalid input", "clampToDomain names the argument", () => model.clampToDomain({ clubSpeed: NaN, attack: 0, path: 0, face: 0, dynLoft: 20 }), "club_speed_mph");
throwsWith("invalid input", "createModel missing key", () => createModel({ ...json, model: { ...json.model, roll: {} } }), "model.roll.k");
throwsWith("invalid input", "createModel missing section", () => createModel({ model: json.model }), "presets.clubs");
throwsWith("invalid input", "createModel not an object", () => createModel(null), "object");

{
  // loadModel: a fetch shim that serves file: URLs from disk.
  const realFetch = globalThis.fetch;
  const seen = [];
  globalThis.fetch = async (u) => {
    seen.push(String(u));
    try {
      const body = readFileSync(fileURLToPath(String(u)), "utf8");
      return { ok: true, status: 200, json: async () => JSON.parse(body) };
    } catch {
      return { ok: false, status: 404, json: async () => ({}) };
    }
  };
  try {
    const m = await loadModel();
    exact("loadModel", "default base is data/ next to flight.js", seen.every((u) => u.endsWith("/site/ball-flight/data/" + u.split("/").pop())), true);
    near("loadModel", "default model runs", m.shot(m.preset("driver", "pga")).flight.carry, golden.cases[0].flight.carry_yd, 0.01);
    const m2 = await loadModel(pathToFileURL(DATA).href + "/");
    exact("loadModel", "string base with slash", typeof m2.shot, "function");
    seen.length = 0;
    await loadModel(pathToFileURL(DATA));
    exact("loadModel", "URL base without slash gets one", seen[0].includes("/data/model.json"), true);
    let err = null;
    try {
      await loadModel("file:///no/such/dir/");
    } catch (e) {
      err = e;
    }
    exact("loadModel", "missing files throw RuntimeError", err instanceof RuntimeError, true);
    globalThis.fetch = async () => { throw new TypeError("network down"); };
    err = null;
    try {
      await loadModel();
    } catch (e) {
      err = e;
    }
    exact("loadModel", "fetch failure throws RuntimeError", err instanceof RuntimeError && err.message.includes("network down"), true);
  } finally {
    globalThis.fetch = realFetch;
  }
}

// ---------------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------------

const pad = (s, n) => String(s).padEnd(n);
console.log(`${pad("category", 22)}${pad("checks", 9)}${pad("failed", 9)}max deviation`);
let totalChecks = 0;
let totalFails = 0;
for (const [name, c] of cats) {
  totalChecks += c.checks;
  totalFails += c.fails;
  const dev = c.maxDev > 0 ? `${c.maxDev.toExponential(2)} (${c.maxWhere})` : "-";
  console.log(`${pad(name, 22)}${pad(c.checks, 9)}${pad(c.fails, 9)}${dev}`);
}

const BUDGET_MS = 2;
// Timing: mean of one shot() (deliver, simulate, roll, classify) over a warm run.
{
  const pr = model.preset("driver", "pga");
  for (let i = 0; i < 300; i++) model.shot(pr);
  const N = 2000;
  const t0 = process.hrtime.bigint();
  for (let i = 0; i < N; i++) model.shot(pr);
  const ms = Number(process.hrtime.bigint() - t0) / 1e6 / N;
  console.log(`shot() mean over ${N} runs, PGA driver: ${ms.toFixed(3)} ms (budget ${BUDGET_MS} ms)`);
  if (!(ms < BUDGET_MS)) {
    totalFails++;
    failures.push(`[timing] shot() mean ${ms.toFixed(3)} ms exceeds the ${BUDGET_MS} ms budget`);
  }
}

console.log(`${golden.cases.length} golden cases, ${golden.classify_vectors.length} classify vectors, ` +
  `${Object.keys(golden.windows_pga_7i).length} windows, ${totalChecks} checks, ${totalFails} failed`);
if (failures.length || totalFails) {
  console.log("\nFailures (first 40):");
  for (const f of failures.slice(0, 40)) console.log("  " + f);
  process.exit(1);
}
console.log("PARITY OK");
