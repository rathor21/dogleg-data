/*
 * State, shot computation and URL for the ball flight lab.
 *
 * State holds the delivery the way the sliders show it: target-line frame,
 * positive is right, for both hands. For a left-handed golfer the model runs
 * with path and face negated, and every lateral output is negated back for
 * display and for the drawn scene. The shot name comes from classify on the
 * right-handed-frame values, so a lefty draw still reads "Draw".
 */
import { METRICS, FT_PER_YD } from "./tiles.js";

export const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
export const round3 = (v) => Math.round(v * 1000) / 1000 + 0;
export const snap = (v, step) => round3(Math.round(v / step) * step);

const GROUP_DEFAULT_CLUB = { driver: "driver", wood: "3w", long_iron: "5i", short_iron: "7i", wedge: "pw" };
// URL key to state key. Short keys keep shared links readable.
const NUM_KEYS = { s: "clubSpeed", a: "attack", pa: "path", f: "face", l: "dynLoft" };
const MODES = ["e", "w", "c"]; // explore, 9 windows, compare
export const WINDOW_HEIGHTS = ["high", "mid", "low"];
export const WINDOW_SHAPES = ["draw", "straight", "fade"];
/** Window keys as windows.json spells them, in chart order: rows high to low, columns draw, straight, fade. */
export const WINDOW_KEYS = WINDOW_HEIGHTS.flatMap((h) => WINDOW_SHAPES.map((s) => `${h}_${s}`));

export function createStore(model) {
  const clubById = Object.fromEntries(model.clubs.map((c) => [c.id, c]));
  const playerIds = model.players.map((p) => p.id);
  // loftFollows and loftOffset are the driver's "loft follows attack angle" switch and the
  // manual loft the golfer added on top of the chart loft. Other clubs ignore both.
  const state = { club: "7i", player: "pga", hand: "r", clubSpeed: 0, attack: 0, path: 0, face: 0, dynLoft: 0, spinTrim: 1, mode: "e", window: null, loftFollows: true, loftOffset: 0, loftOffsetIsMine: false };
  const lastClubInGroup = { ...GROUP_DEFAULT_CLUB };

  const groupOf = (club = state.club) => clubById[club].group;

  const isDriver = (st = state) => st.club === "driver";
  const [LOFT_LO, LOFT_HI] = model.domain.dyn_loft_deg;
  /**
   * The loft the switch follows for this attack angle. The driver: the TrackMan chart's
   * optimal loft at the current club speed. Every other club: model.loftForAttack (the preset
   * loft plus the model's degrees of loft per degree of attack). Returns {dynLoft, extrapolated, speedClamped}.
   */
  const chartLoft = (st = state) => {
    if (isDriver(st)) return model.optimalLoft(st.clubSpeed, st.attack);
    return { dynLoft: model.loftForAttack(st.club, st.player, clamp(st.attack, ...model.domain.attack_deg)), extrapolated: false, speedClamped: false };
  };

  /** Driver: remember how far the loft sits from the chart loft, so following keeps that offset. */
  function syncLoftOffset(fromSlider = false) {
    state.loftOffset = round3(state.dynLoft - chartLoft().dynLoft);
    // Only an offset the golfer set on the loft slider is "theirs". One that comes from a loaded
    // average or a link is just how that delivery sits against the chart, and the note says so.
    state.loftOffsetIsMine = fromSlider && Math.abs(state.loftOffset) >= 0.05;
  }

  /** Driver with the switch on: loft is the chart loft for this speed and attack, plus the golfer's own offset. */
  function followLoft() {
    if (!state.loftFollows) return;
    state.dynLoft = round3(clamp(chartLoft().dynLoft + state.loftOffset, LOFT_LO, LOFT_HI));
  }

  /** Call after a slider moves. The loft slider sets the offset. Attack and club speed pull the loft along. */
  function afterSliderChange(key) {
    if (key === "dynLoft") syncLoftOffset(true);
    else if (key === "attack" || key === "clubSpeed") followLoft();
  }

  /** Turning it on returns the loft to the chart loft for this speed and attack. Turning it off leaves the loft where it is. */
  function setLoftFollows(on) {
    state.loftFollows = !!on;
    if (on) {
      state.loftOffset = 0;
      state.loftOffsetIsMine = false;
      followLoft();
    }
  }

  /**
   * Load the ideal delivery (model.idealDelivery) at the preset club speed, as
   * "Reset to ideal" always has. The driver's ideal hits up, with loft from the chart.
   * Every other club is its preset. Path and face go to the ideal too, and the loft
   * switch goes back on.
   */
  function loadIdeal() {
    const d = applyBase(false); // idealDelivery(club, player) at the preset club speed, path and face included
    state.loftFollows = true;
    return d;
  }

  /**
   * The default for a club and player, at the preset club speed: the ideal. Used on
   * first load and on a club or player change. Path and face stay when keepLateral.
   */
  function applyBase(keepLateral) {
    const d = model.idealDelivery(state.club, state.player);
    state.clubSpeed = d.clubSpeed;
    state.attack = d.attack;
    state.dynLoft = d.dynLoft;
    state.spinTrim = d.spinTrim;
    state.loftOffset = 0;
    state.loftOffsetIsMine = false;
    if (!keepLateral) {
      state.path = d.path + 0;
      state.face = d.face + 0;
    }
    return d;
  }

  /** Does the tour or amateur average differ from the ideal? True for the driver. */
  function averageDiffers() {
    const p = model.preset(state.club, state.player);
    const d = model.idealDelivery(state.club, state.player);
    const far = (a, b, tol) => Math.abs(a - b) > tol;
    return far(p.attack, d.attack, 0.05) || far(p.dynLoft, d.dynLoft, 0.05) || far(p.spinTrim, d.spinTrim, 0.001) || far(p.clubSpeed, d.clubSpeed, 0.05);
  }

  /** Load the preset (the tour or amateur average) as it is, at its own club speed. */
  function loadAverage() {
    applyPreset(false);
    state.loftFollows = true;
    syncLoftOffset(); // the average's loft sits where it sits; following moves it from there
  }

  /** Set club speed, attack, loft and spin trim from the preset. Path and face too unless keepLateral. */
  function applyPreset(keepLateral) {
    const p = model.preset(state.club, state.player);
    state.clubSpeed = p.clubSpeed;
    state.attack = p.attack;
    state.dynLoft = p.dynLoft;
    state.spinTrim = p.spinTrim;
    if (!keepLateral) {
      state.path = p.path + 0;
      state.face = p.face + 0;
    }
    return p;
  }

  /** The one way to change club: sets the club, remembers it for its group, and loads its preset (path and face stay). */
  function switchClub(id) {
    state.club = id;
    lastClubInGroup[groupOf(id)] = id;
    applyBase(true);
  }

  /** The one writer of state.window (a window key, or null for none). */
  function selectWindow(key) {
    state.window = key;
  }

  /** What a pinned shot needs to remember about the setup, read through the store. */
  function snapshot() {
    return { club: state.club, player: state.player, hand: state.hand };
  }

  /**
   * Pure parse of a query string into the keys that are present and usable.
   * A missing key, an empty value (?s=) and a non-number are all "missing".
   */
  function parseQuery(search) {
    const q = new URLSearchParams(search);
    const get = (k) => {
      const v = q.get(k);
      return v === null || v.trim() === "" ? null : v.trim();
    };
    const out = { nums: {} };
    const club = (get("c") || "").toLowerCase();
    if (clubById[club]) out.club = club;
    const player = (get("p") || "").toLowerCase();
    if (playerIds.includes(player)) out.player = player;
    const hand = (get("h") || "").toLowerCase();
    if (hand === "l" || hand === "left") out.hand = "l";
    else if (hand === "r" || hand === "right") out.hand = "r";
    const mode = (get("m") || "").toLowerCase();
    if (MODES.includes(mode)) out.mode = mode;
    const win = (get("w") || "").toLowerCase().replace(/-/g, "_");
    if (WINDOW_KEYS.includes(win)) out.window = win;
    const lf = (get("lf") || "").toLowerCase();
    if (lf === "1" || lf === "0") out.loftFollows = lf === "1";
    for (const [k, key] of Object.entries(NUM_KEYS)) {
      const raw = get(k);
      if (raw === null) continue;
      const v = Number(raw);
      if (Number.isFinite(v)) out.nums[key] = v;
    }
    return out;
  }

  /**
   * Load state from a query string. Anything missing falls back to the preset
   * for the club and player. In 9 Windows mode the club is the 7-iron and a
   * selected window is applied (afterPreset) before the numbers in the URL, so
   * a recipe you had adjusted comes back adjusted.
   */
  function loadFromSearch(search, afterPreset) {
    const p = parseQuery(search);
    if (p.club) state.club = p.club;
    if (p.player) state.player = p.player;
    if (p.hand) state.hand = p.hand;
    state.mode = p.mode || "e";
    if (state.mode === "w") state.club = "7i";
    applyBase(false);
    if (p.loftFollows !== undefined) state.loftFollows = p.loftFollows;
    selectWindow(state.mode === "w" && p.window ? p.window : null);
    if (state.window && afterPreset) afterPreset(state.window);
    Object.assign(state, p.nums);
    // A link that names speed or attack but no loft gets the followed loft for them.
    if (p.nums.dynLoft === undefined && state.loftFollows && !state.window) state.dynLoft = round3(clamp(chartLoft().dynLoft, LOFT_LO, LOFT_HI));
    syncLoftOffset();
    lastClubInGroup[groupOf()] = state.club;
  }

  /** The share URL for a state, built synchronously (path and query, no origin). */
  function buildUrl(st = state) {
    const r2 = (v) => String(Math.round(v * 100) / 100 + 0);
    const q = new URLSearchParams({
      c: st.club, p: st.player, h: st.hand, m: st.mode,
      s: r2(st.clubSpeed), a: r2(st.attack), pa: r2(st.path), f: r2(st.face), l: r2(st.dynLoft),
    });
    q.set("lf", st.loftFollows ? "1" : "0");
    if (st.mode === "w" && st.window) q.set("w", st.window.replace(/_/g, "-"));
    return location.pathname + "?" + q.toString();
  }

  /**
   * Pure: run the model for a state. Nothing here writes to the state.
   * Returns {norm, s, bands, values, rangeShot, group}. norm is the state's
   * delivery after clampToDomain (the caller decides whether to keep it).
   */
  function compute(st = state) {
    const sign = st.hand === "l" ? -1 : 1;
    const d = model.clampToDomain({
      clubSpeed: st.clubSpeed, attack: st.attack, path: sign * st.path, face: sign * st.face,
      dynLoft: st.dynLoft, club: st.club, spinTrim: st.spinTrim,
    });
    const norm = {
      clubSpeed: round3(d.clubSpeed),
      attack: round3(d.attack),
      dynLoft: round3(d.dynLoft),
      path: round3(sign * d.path),
      face: round3(sign * d.face),
    };
    const s = model.shot(d);
    let bands = model.idealBands(st.club, st.player, d.clubSpeed, d.attack);

    const values = {};
    for (const m of Object.keys(METRICS)) {
      const rh = model.metricValue(m, s);
      values[m] = { rh, disp: METRICS[m].lateral ? sign * rh + 0 : rh };
    }
    // Height is shown in feet. The model works in yards, so convert the value and its band here.
    const ft = (v) => (v === null ? null : v * FT_PER_YD);
    values.max_height_yd = { rh: ft(values.max_height_yd.rh), disp: ft(values.max_height_yd.disp) };
    const hb = bands.max_height_yd;
    if (hb) bands = { ...bands, max_height_yd: { ...hb, lo: ft(hb.lo), hi: ft(hb.hi), target: ft(hb.target) } };
    // The Dynamic loft tile shows the effective loft. These let it say how the face moved it off the slider's loft.
    values.dyn_loft_deg.input = s.launch.dynLoftInputDeg;
    values.dyn_loft_deg.faceToPathRh = s.launch.faceToPathDeg;
    const f = s.flight;
    const n = f.x.length;
    const y = new Float64Array(n);
    for (let i = 0; i < n; i++) y[i] = sign * f.y[i] + 0;
    const rangeShot = {
      t: f.t, x: f.x, y, z: f.z, flightTime: f.flightTime, carry: f.carry, total: s.total, maxHeight: f.maxHeight,
      launchDir: sign * s.launch.launchDirDeg,
    };
    return { norm, s, bands, values, rangeShot, group: groupOf(st.club) };
  }

  return { state, lastClubInGroup, clubById, groupOf, applyPreset, applyBase, syncLoftOffset, loadIdeal, loadAverage, averageDiffers, afterSliderChange, setLoftFollows, followLoft, chartLoft, switchClub, selectWindow, snapshot, parseQuery, loadFromSearch, buildUrl, compute };
}
