/*
 * Data for the article figures and numbers (release 004, task 004.11).
 * Everything here reads the live model (flight.js, the same module the lab
 * runs) or the published rows in data/presets.json. Nothing is typed in from
 * a model run. The hand-entered sets are all published: TRACKMAN_EXAMPLES (eight
 * face-to-path curvature examples, Anchor 5b), TRACKMAN_TOTAL_2010 (the total-distance
 * half of the 2010 driver chart, Anchor 4 Source 1) and OPTIMIZER_DEFAULT_DRIVER
 * (TrackMan's current default for a 94 mph driver, Anchor 3 Source 2).
 */

export const CLUB_LABEL = { driver: "Driver", "3w": "3-wood", "5w": "5-wood", hybrid: "Hybrid", "3i": "3-iron", "4i": "4-iron", "5i": "5-iron", "6i": "6-iron", "7i": "7-iron", "8i": "8-iron", "9i": "9-iron", pw: "PW" };
export const PLAYER_LABEL = { pga: "PGA Tour", lpga: "LPGA Tour", amateur: "Average amateur" };

/** TrackMan, "What is Face to Path?" (2024-09-23). Positive curve is right. Carries quoted there are the 2019 set. */
export const TRACKMAN_EXAMPLES = [
  { tour: "pga", club: "driver", f2p: -2, curve: -19 },
  { tour: "pga", club: "driver", f2p: 5, curve: 44 },
  { tour: "pga", club: "6i", f2p: 2, curve: 8 },
  { tour: "pga", club: "6i", f2p: -5, curve: -20 },
  { tour: "lpga", club: "driver", f2p: 2, curve: 14 },
  { tour: "lpga", club: "driver", f2p: -5, curve: -32 },
  { tour: "lpga", club: "6i", f2p: -2, curve: -6 },
  { tour: "lpga", club: "6i", f2p: 5, curve: 14 },
];

/** TrackMan Driver Fitting Chart (2010), TOTAL Optimizer, launch and spin by club speed (rows) and attack angle (columns). */
export const TRACKMAN_TOTAL_2010 = {
  club_speed_mph: [75, 80, 85, 90, 95, 100, 105, 110, 115, 120],
  attack_deg: [-5, 0, 5],
  launch_deg: [[11.8, 13.0, 15.3], [10.1, 12.1, 14.8], [9.3, 11.7, 14.0], [8.5, 10.8, 13.8], [7.9, 10.5, 13.0], [7.2, 10.0, 12.4], [6.4, 9.1, 11.7], [5.6, 8.7, 11.1], [5.3, 8.0, 10.7], [4.5, 7.7, 10.3]],
  spin_rpm: [[3214, 2506, 1976], [3078, 2494, 2005], [3110, 2568, 1964], [3122, 2517, 2021], [3144, 2565, 1948], [3118, 2570, 1887], [3071, 2461, 1810], [3005, 2471, 1716], [3030, 2396, 1681], [2929, 2382, 1636]],
};

/** TrackMan's current Optimizer default for a 94 mph driver (attack 0): launch, spin. Anchor 3 Source 2. */
export const OPTIMIZER_DEFAULT_DRIVER = { clubSpeed: 94, launch: 13.6, spin: 2772 };

/** TrackMan's published Tour driver dynamic loft and spin loft (Anchor 1 supplement), PGA. */
export const PUBLISHED_PGA_DRIVER_LOFTS = { dynLoft: 12.8, spinLoft: 14.7 };

/** The same chart's TOTAL row for 115 mph at +5 attack: dynamic loft 11.7, spin 1,681 rpm, so spin loft 6.7. */
export const TOTAL_ROW_115_P5 = { dynLoft: 11.7, spin: 1681, attack: 5 };

function bracketIn(grid, x) {
  if (x <= grid[0]) return [0, 0, 0];
  if (x >= grid[grid.length - 1]) return [grid.length - 1, grid.length - 1, 0];
  let hi = 0;
  while (!(grid[hi] >= x)) hi++;
  return [hi - 1, hi, (x - grid[hi - 1]) / (grid[hi] - grid[hi - 1])];
}

/** Bilinear lookup in the TOTAL chart, clamped to its range. Returns {launch, spin}. */
export function trackmanTotal2010(clubSpeed, attack) {
  const T = TRACKMAN_TOTAL_2010;
  const [r0, r1, fr] = bracketIn(T.club_speed_mph, clubSpeed);
  const [c0, c1, fc] = bracketIn(T.attack_deg, attack);
  const at = (tb) => (tb[r0][c0] * (1 - fc) + tb[r0][c1] * fc) * (1 - fr) + (tb[r1][c0] * (1 - fc) + tb[r1][c1] * fc) * fr;
  return { launch: at(T.launch_deg), spin: at(T.spin_rpm) };
}

/** One shot from a preset with overrides (club, player, {attack, path, face, clubSpeed, dynLoft}). */
export function shotAt(model, club, player, over = {}) {
  return model.shot({ ...model.preset(club, player), ...over });
}

const at200 = (deg) => 200 * Math.tan((deg * Math.PI) / 180);

/** Chapter 1. Start direction for face +-4 at path 0 and path +-4 at face 0. */
export function startDirection(model) {
  const out = [];
  for (const club of ["driver", "6i"]) {
    const rows = [];
    for (const [input, sign] of [["face", -1], ["face", 1], ["path", -1], ["path", 1]]) {
      const s = shotAt(model, club, "pga", { [input]: 4 * sign, [input === "face" ? "path" : "face"]: 0 });
      const deg = s.launch.launchDirDeg;
      rows.push({ input, value: 4 * sign, deg, yd200: at200(deg) });
    }
    out.push({ club, label: CLUB_LABEL[club], rows });
  }
  return out;
}

/** The face's share of start direction, per degree, from face +1 at path 0. Percent. */
export function faceShare(model, club, player = "pga") {
  return shotAt(model, club, player, { face: 1, path: 0 }).launch.launchDirDeg * 100;
}

/** Chapter 2. Curve against face-to-path at path 0, PGA presets for three clubs and LPGA for two. */
export function curveLines(model) {
  const defs = [
    { id: "pga-driver", club: "driver", player: "pga", label: "Driver", dash: false },
    { id: "pga-6i", club: "6i", player: "pga", label: "6-iron", dash: false },
    { id: "pga-pw", club: "pw", player: "pga", label: "PW", dash: false },
    { id: "lpga-driver", club: "driver", player: "lpga", label: "LPGA driver", dash: true },
    { id: "lpga-6i", club: "6i", player: "lpga", label: "LPGA 6-iron", dash: true },
  ];
  return defs.map((d) => {
    const pts = [];
    for (let f = -6; f <= 6.0001; f += 0.5) {
      const s = shotAt(model, d.club, d.player, { face: f, path: 0 });
      pts.push({ f2p: f, curve: s.flight.curve });
    }
    return { ...d, pts };
  });
}

export function curveAt(model, club, player, f2p) {
  return shotAt(model, club, player, { face: f2p, path: 0 }).flight.curve;
}

/** Example dots with the live preset line's value at the same face-to-path. */
export function exampleCheck(model) {
  return TRACKMAN_EXAMPLES.map((e) => {
    const m = curveAt(model, e.club, e.tour, e.f2p);
    return { ...e, model: m, miss: m - e.curve, pct: ((m - e.curve) / Math.abs(e.curve)) * 100 };
  });
}

/**
 * TrackMan's published driver-to-6-iron curvature ratio, from the eight examples.
 * Per tour: the mean yards of curve per degree of face-to-path for the driver over the same for the 6-iron.
 */
export function publishedRatio() {
  const perDeg = (tour, club) => {
    const r = TRACKMAN_EXAMPLES.filter((e) => e.tour === tour && e.club === club);
    return r.reduce((a, e) => a + Math.abs(e.curve) / Math.abs(e.f2p), 0) / r.length;
  };
  const pga = perDeg("pga", "driver") / perDeg("pga", "6i");
  const lpga = perDeg("lpga", "driver") / perDeg("lpga", "6i");
  return { pga, lpga };
}

/** Bilinear lookup of one grid of a driver chart in ideals.json ("carry_yd", "total_yd"), clamped to the chart's range. */
export function chartYd(model, chart, field, clubSpeed, attack) {
  const T = model.data.ideals.driver[chart];
  const [r0, r1, fr] = bracketIn(T.club_speed_mph, clubSpeed);
  const [c0, c1, fc] = bracketIn(T.attack_deg, attack);
  const g = T[field];
  return (g[r0][c0] * (1 - fc) + g[r0][c1] * fc) * (1 - fr) + (g[r1][c0] * (1 - fc) + g[r1][c1] * fc) * fr;
}

/**
 * Chapter 3. Tour driver, attack angle -6 to +10, two ways. The fixed-loft rows hold dynamic loft at the preset.
 * Spin is shown with the preset's spin trim (the lab's number) and with no trim (the TrackMan chart's own basis).
 * The `fol` rows let loft follow attack: dynamic loft is model.optimalLoft (midway between the TrackMan 2010 carry
 * and total optimizers at this club speed), spin trim is the driver ideal's (1.0, the chart's own strike). A fixed-loft
 * row is extrapolated when its spin loft leaves the range the driver law was calibrated on (launch_model
 * k_sl_lo_driver to k_sl_hi_driver, the TrackMan 2010 chart's 6.3 to 23.2 degrees). A `fol` row is extrapolated
 * on that test too, and when the chart's loft is extended past its own attack range of -5 to +5.
 */
export function attackSweep(model) {
  const p = model.preset("driver", "pga");
  const lo = model.data.model.launch_model.k_sl_lo_driver;
  const hi = model.data.model.launch_model.k_sl_hi_driver;
  const idealTrim = model.data.presets.driver_ideal.spin_trim;
  const rows = [];
  for (let a = -6; a <= 10; a += 1) {
    const s = model.shot({ ...p, attack: a });
    const u = model.shot({ ...p, attack: a, spinTrim: 1 });
    const ol = model.optimalLoft(p.clubSpeed, a);
    const f = model.shot({ ...p, attack: a, dynLoft: ol.dynLoft, spinTrim: idealTrim });
    const row = {
      attack: a,
      launch: s.launch.launchDeg,
      spin: s.launch.spinRpm,
      spinUntrimmed: u.launch.spinRpm,
      spinLoft: s.launch.spinLoftDeg,
      carry: s.flight.carry,
      carryUntrimmed: u.flight.carry,
      extrapolated: s.launch.spinLoftDeg < lo || s.launch.spinLoftDeg > hi,
      fol: {
        loft: ol.dynLoft,
        launch: f.launch.launchDeg,
        spin: f.launch.spinRpm,
        spinLoft: f.launch.spinLoftDeg,
        carry: f.flight.carry,
        total: f.total,
        extrapolated: ol.extrapolated || f.launch.spinLoftDeg < lo || f.launch.spinLoftDeg > hi,
      },
      tm: null,
      tmCarry: null,
      ping: null,
    };
    if (a >= -5 && a <= 5) {
      const [l, sp] = model.trackmanCarry2010(p.clubSpeed, a);
      row.tm = { launch: l, spin: sp };
      row.tmCarry = chartYd(model, "trackman_carry_2010", "carry_yd", p.clubSpeed, a);
    }
    const [pl, ps] = model.ping2019(s.launch.ballSpeedMph, a);
    row.ping = { launch: pl, spin: ps };
    rows.push(row);
  }
  return { dynLoft: p.dynLoft, spinTrim: p.spinTrim, followTrim: idealTrim, clubSpeed: p.clubSpeed, floor: lo, ceil: hi, rows, tour: model.data.presets.published.pga.driver };
}

/**
 * Chapter 3. What TrackMan's 2010 chart and the model each gain in carry and total from attack -5 to +5
 * at one club speed (default the PGA driver's 115 mph). The chart's own carry and total come from its carry
 * rows (and its total-distance rows, `tt`). The model gain flies each row's own ball speed, launch and spin
 * with no axis, the way the calibration does (ADR 0004 addendum 1), so it isolates the flight and roll.
 */
export function chartGains(model, clubSpeed = 115) {
  const I = model.data.ideals.driver;
  const out = {};
  for (const [id, chart] of [["cr", "trackman_carry_2010"], ["tt", "trackman_total_2010"]]) {
    const T = I[chart];
    const i = T.club_speed_mph.indexOf(clubSpeed);
    const flown = [0, 2].map((j) => {
      const f = model.simulate(T.ball_speed_mph[i][j], T.launch_deg[i][j], 0.0, T.spin_rpm[i][j], 0.0);
      return { carry: f.carry, total: model.roll(f) };
    });
    out[id] = {
      chartCarryDn: T.carry_yd[i][0], chartCarryUp: T.carry_yd[i][2],
      chartTotalDn: T.total_yd[i][0], chartTotalUp: T.total_yd[i][2],
      modelCarryGain: flown[1].carry - flown[0].carry, modelTotalGain: flown[1].total - flown[0].total,
    };
    out[id].chartCarryGain = out[id].chartCarryUp - out[id].chartCarryDn;
    out[id].chartTotalGain = out[id].chartTotalUp - out[id].chartTotalDn;
  }
  return out;
}

/**
 * Chapter 3. The lab's driver ideal against the average delivery for each player, at that player's own club speed.
 * The average is model.preset (the published Tour or Combine row). The ideal is model.idealDelivery.
 */
export function driverIdeals(model) {
  return ["pga", "lpga", "amateur"].map((pl) => {
    const avg = model.preset("driver", pl);
    const ideal = model.idealDelivery("driver", pl);
    const a = model.shot(avg), i = model.shot(ideal);
    return { player: pl, label: PLAYER_LABEL[pl], avg: { ...avg, carry: a.flight.carry, total: a.total }, ideal: { ...ideal, carry: i.flight.carry, total: i.total } };
  });
}

/** Chapter 3 coupling. Steepen the Tour driver by 4 degrees with the swing direction and face held. */
export function couplingShot(model, steeper = 4) {
  const p = model.preset("driver", "pga");
  const plane = model.data.model.swing_plane_default_deg;
  const swingDir = p.path + p.attack * Math.tan((90 - plane) * Math.PI / 180) * 1; // path at the preset attack
  const path0 = model.swingPath(swingDir, p.attack, plane);
  const attack = p.attack - steeper;
  const path = model.swingPath(swingDir, attack, plane);
  const s = model.shot({ ...p, attack, path });
  return { plane, perDegree: Math.tan((90 - plane) * Math.PI / 180), pathShift: path - path0, path, shot: s };
}

/**
 * Chapter 4. Driver launch and spin, each group's published average against TrackMan's 2010 carry chart,
 * PING's 2019 chart and TrackMan's 2010 total-distance chart. Chart lookups use the group's published club
 * speed (TrackMan), published ball speed (PING) and published attack angle. The band is the lab's rule
 * (the lowest and highest of the three sources, widened by the ideals.json margins) applied to those lookups.
 */
export function driverWindows(model) {
  const tol = model.data.ideals.tolerances;
  return ["pga", "lpga", "amateur"].map((pl) => {
    const pub = model.data.presets.published[pl].driver;
    const [tl, ts] = model.trackmanCarry2010(pub.club_speed_mph, pub.attack_deg);
    const [pl2, ps] = model.ping2019(pub.ball_speed_mph, pub.attack_deg);
    const tot = trackmanTotal2010(pub.club_speed_mph, pub.attack_deg);
    const ml = tol.driver_launch_margin_deg, ms = tol.driver_spin_margin_rpm;
    return {
      player: pl,
      label: PLAYER_LABEL[pl],
      clubSpeed: pub.club_speed_mph,
      ballSpeed: pub.ball_speed_mph,
      attack: pub.attack_deg,
      tm: { launch_deg: tl, spin_rpm: ts },
      ping: { launch_deg: pl2, spin_rpm: ps },
      total: { launch_deg: tot.launch, spin_rpm: tot.spin },
      avg: { launch: pub.launch_deg, spin: pub.spin_rpm },
      band: { launch: [Math.min(tl, pl2, tot.launch) - ml, Math.max(tl, pl2, tot.launch) + ml], spin: [Math.min(ts, ps, tot.spin) - ms, Math.max(ts, ps, tot.spin) + ms] },
      source: pub.source || "TrackMan 2023 Tour table",
    };
  });
}

/** Chapter 4 table. Published value where one exists, modeled otherwise. */
export function presetTable(model) {
  const cols = [
    { id: "club_speed_mph", label: "Club speed (mph)", dp: 0, from: (s) => s.delivery.clubSpeed },
    { id: "launch_deg", label: "Launch (deg)", dp: 1, from: (s) => s.launch.launchDeg },
    { id: "spin_rpm", label: "Spin (rpm)", dp: 0, from: (s) => s.launch.spinRpm },
    { id: "max_height_yd", label: "Height (yd)", dp: 0, from: (s) => s.flight.maxHeight },
    { id: "land_angle_deg", label: "Land angle (deg)", dp: 0, from: (s) => s.flight.landAngle },
    { id: "carry_yd", label: "Carry (yd)", dp: 0, from: (s) => s.flight.carry },
  ];
  const rows = [];
  for (const club of ["driver", "6i", "pw"]) {
    for (const player of ["pga", "lpga", "amateur"]) {
      const p = model.preset(club, player);
      const s = model.shot(p);
      const pub = model.data.presets.published[player][club] || {};
      const isDefault = typeof pub.source === "string" && /Optimizer default/i.test(pub.source);
      const cells = cols.map((c) => {
        const has = pub[c.id] !== undefined;
        const value = has ? pub[c.id] : c.from(s);
        const kind = !has ? "modeled" : isDefault ? "default" : "published";
        return { id: c.id, value, dp: c.dp, kind };
      });
      rows.push({ club, player, label: `${CLUB_LABEL[club]}, ${PLAYER_LABEL[player]}`, cells, source: pub.source || "TrackMan 2023 Tour table" });
    }
  }
  return { cols, rows };
}

const NINE = [
  ["high", "draw"], ["high", "straight"], ["high", "fade"],
  ["mid", "draw"], ["mid", "straight"], ["mid", "fade"],
  ["low", "draw"], ["low", "straight"], ["low", "fade"],
];

/** Chapter 5. The nine 7-iron recipes for the PGA Tour preset, flown live. */
export function nineWindows(model) {
  const w = model.windows.players.pga;
  return NINE.map(([height, shape]) => {
    const r = w[`${height}_${shape}`];
    const d = r.delivery;
    const s = model.shot({ clubSpeed: d.club_speed_mph, attack: d.attack_deg, path: d.path_deg, face: d.face_deg, dynLoft: d.dyn_loft_deg, club: r.club, spinTrim: r.spin_trim });
    return { key: `${height}_${shape}`, height, shape, label: `${height[0].toUpperCase()}${height.slice(1)} ${shape}`, delivery: { clubSpeed: d.club_speed_mph, attack: d.attack_deg, path: d.path_deg, face: d.face_deg, dynLoft: d.dyn_loft_deg }, shot: s };
  });
}

/**
 * Chapter 6 example: the amateur driver's average delivery (94 mph, -1.8 attack, loft 15.1), face square,
 * path 4 and then 2 degrees left. The spin trim is the lab's ideal trim, 1.0, because the article's deep link
 * carries speed, attack, path, face and loft and no trim, so the lab opens with the driver ideal's trim.
 */
export function coachingExample(model) {
  const trim = model.idealDelivery("driver", "amateur").spinTrim;
  const a = shotAt(model, "driver", "amateur", { path: -4, face: 0, spinTrim: trim });
  const b = shotAt(model, "driver", "amateur", { path: -2, face: 0, spinTrim: trim });
  return { a, b };
}

/**
 * Method and limits. Club speeds at which the lab's driver ideal gives less total distance than the average delivery.
 * Both are flown at the same club speed (the average is the preset with its club speed changed, the ideal is
 * model.idealDelivery at that speed), scanned over the lab's whole club speed range in 5 mph steps. Returns the lowest
 * and highest such speed for each Tour player, or null when the ideal never loses total.
 */
export function idealTotalReversal(model) {
  const [lo, hi] = model.domain.club_speed_mph;
  const out = {};
  for (const pl of ["pga", "lpga"]) {
    const p = model.preset("driver", pl);
    const hits = [];
    for (let s = Math.ceil(lo / 5) * 5; s <= hi; s += 5) {
      const a = model.shot(model.scaleSpeed(p, s));
      const i = model.shot(model.idealDelivery("driver", pl, s));
      if (i.total < a.total) hits.push(s);
    }
    out[pl] = hits.length ? { lo: hits[0], hi: hits[hits.length - 1] } : null;
  }
  return out;
}
