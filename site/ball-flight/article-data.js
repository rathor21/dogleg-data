/*
 * Data for the article figures and numbers (release 004, task 004.11).
 * Everything here reads the live model (flight.js, the same module the lab
 * runs) or the published rows in data/presets.json. Nothing is typed in from
 * a model run. The one hand-entered set is TRACKMAN_EXAMPLES, TrackMan's eight
 * published face-to-path curvature examples (source log, Anchor 5b).
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

/** One shot from a preset with overrides (club, player, {attack, path, face, clubSpeed, dynLoft}). */
export function shotAt(model, club, player, over = {}) {
  return model.shot({ ...model.preset(club, player), ...over });
}

const at200 = (deg) => 200 * Math.tan((deg * Math.PI) / 180);

/** Chapter 1. Start direction for face +-4 at path 0 and path +-4 at face 0. */
export function startDirection(model) {
  const out = [];
  for (const club of ["driver", "7i"]) {
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
    return { ...e, model: m, miss: m - e.curve };
  });
}

/** Chapter 3. Tour driver, dynamic loft held at the preset, attack angle -6 to +6. */
export function attackSweep(model) {
  const p = model.preset("driver", "pga");
  const floor = model.data.model.launch_model.k_sl_lo;
  const rows = [];
  for (let a = -6; a <= 6; a += 1) {
    const s = model.shot({ ...p, attack: a });
    const row = {
      attack: a,
      launch: s.launch.launchDeg,
      spin: s.launch.spinRpm,
      spinLoft: s.launch.spinLoftDeg,
      carry: s.flight.carry,
      extrapolated: s.launch.spinLoftDeg < floor,
      tm: null,
      ping: null,
    };
    if (a >= -5 && a <= 5) {
      const [l, sp] = model.trackmanCarry2010(p.clubSpeed, a);
      row.tm = { launch: l, spin: sp };
    }
    const [pl, ps] = model.ping2019(s.launch.ballSpeedMph, a);
    row.ping = { launch: pl, spin: ps };
    rows.push(row);
  }
  return { dynLoft: p.dynLoft, clubSpeed: p.clubSpeed, floor, rows, tour: model.data.presets.published.pga.driver };
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

/** Chapter 4. Driver launch and spin against the two optimizers, per player group. */
export function driverWindows(model) {
  return ["pga", "lpga", "amateur"].map((pl) => {
    const b = model.idealBands("driver", pl);
    const d = b.launch_deg.detail;
    const pub = model.data.presets.published[pl].driver;
    const p = model.preset("driver", pl);
    return {
      player: pl,
      label: PLAYER_LABEL[pl],
      clubSpeed: p.clubSpeed,
      attack: p.attack,
      ballSpeed: d.inputs.ball_speed_mph,
      tm: d.trackman_carry_2010,
      ping: d.ping_2019,
      avg: { launch: pub.launch_deg, spin: pub.spin_rpm },
      band: { launch: [b.launch_deg.lo, b.launch_deg.hi], spin: [b.spin_rpm.lo, b.spin_rpm.hi] },
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

/** Chapter 6 example: amateur driver, face square, path 4 and then 2 degrees left. */
export function coachingExample(model) {
  const a = shotAt(model, "driver", "amateur", { path: -4, face: 0 });
  const b = shotAt(model, "driver", "amateur", { path: -2, face: 0 });
  return { a, b };
}
