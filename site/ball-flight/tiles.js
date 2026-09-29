/*
 * Metric metadata and tile rendering for the ball flight lab.
 *
 * METRICS is the one table for every number on the page: label, unit, decimals,
 * the words under the value, and (for the five inputs) the slider settings the
 * sliders read. A tile shows label, value, a direction word, a band bar with the
 * ideal band and a marker at the value, and a status line.
 *
 * Values the page passes in are in the display frame (positive is right of the
 * target line for both hands). Bands come from model.idealBands in the
 * right-handed frame, so a lateral metric's band is mirrored here for a
 * left-handed golfer. Every current lateral band is symmetric about zero, so the
 * mirror changes nothing today and stays right if a band stops being symmetric.
 */

export const MINUS = "−";
export const DEG = "°";

// The "on the line" distance for Side. The page sets it from the model's classify
// on_line_yd, so the tile, the shot name and the top view all agree.
let ON_LINE_YD = 0.05;
export function configureTiles({ onLineYd }) {
  if (Number.isFinite(onLineYd)) ON_LINE_YD = onLineYd;
}
const dirWord = (v) => (v > 0 ? "right" : "left");
const isZero = (v, tol) => Math.abs(v) < tol;

// words(rh, disp) returns the plain-language word under the value.
// rh is the right-handed-frame value (the frame the model runs in), disp is the
// value shown. Path, face and face to path read the same for both hands through
// rh: positive rh path is in-to-out, positive rh face is open.
//
// slider: {stateKey, step, dom, zero, advanced, label, hints(hand)}. stateKey is
// the key in the page state, dom the key in model.domain.
export const METRICS = {
  club_speed_mph: { label: "Club speed", unit: "mph", dec: 1,
    slider: { stateKey: "clubSpeed", step: 1, dom: "club_speed_mph", dec: 0 } },
  attack_deg: { label: "Attack angle", unit: DEG, dec: 1, signed: true,
    words: (rh) => (isZero(rh, 0.05) ? "level" : rh > 0 ? "hitting up" : "hitting down"),
    slider: { stateKey: "attack", step: 0.5, dom: "attack_deg", zero: true, hints: () => [MINUS + " down", "+ up"] } },
  path_deg: { label: "Club path", unit: DEG, dec: 1, signed: true, lateral: true,
    words: (rh) => (isZero(rh, 0.05) ? "square to target" : rh > 0 ? "in-to-out" : "out-to-in"),
    slider: { stateKey: "path", step: 0.5, dom: "path_deg", zero: true,
      hints: (h) => (h === "l" ? [MINUS + " in-to-out", "+ out-to-in"] : [MINUS + " out-to-in", "+ in-to-out"]) } },
  face_deg: { label: "Face angle", unit: DEG, dec: 1, signed: true, lateral: true,
    words: (rh) => (isZero(rh, 0.05) ? "square to target" : rh > 0 ? "open to target" : "closed to target"),
    slider: { stateKey: "face", step: 0.5, dom: "face_deg", zero: true, label: "Face angle (to target)",
      hints: (h) => (h === "l" ? [MINUS + " open", "+ closed"] : [MINUS + " closed", "+ open"]) } },
  face_to_path_deg: { label: "Face to path", unit: DEG, dec: 1, signed: true, lateral: true,
    words: (rh) => (isZero(rh, 0.05) ? "square to path" : rh > 0 ? "open to path" : "closed to path") },
  dyn_loft_deg: { label: "Dynamic loft", unit: DEG, dec: 1,
    slider: { stateKey: "dynLoft", step: 0.5, dom: "dyn_loft_deg", advanced: true } },
  spin_loft_deg: { label: "Spin loft", unit: DEG, dec: 1 },
  ball_speed_mph: { label: "Ball speed", unit: "mph", dec: 1 },
  smash: { label: "Smash factor", unit: "", dec: 2 },
  launch_deg: { label: "Launch angle", unit: DEG, dec: 1 },
  launch_dir_deg: { label: "Launch direction", unit: DEG, dec: 1, signed: true, lateral: true,
    words: (rh, d) => (isZero(d, 0.05) ? "on target line" : `starts ${dirWord(d)}`) },
  spin_rpm: { label: "Spin rate", unit: "rpm", dec: 0, grouped: true },
  spin_axis_deg: { label: "Spin axis", unit: DEG, dec: 1, signed: true, lateral: true,
    words: (rh, d) => (isZero(d, 0.05) ? "no side spin" : `tilts ${dirWord(d)}`) },
  max_height_yd: { label: "Height", unit: "yd", dec: 1 },
  land_angle_deg: { label: "Land angle", unit: DEG, dec: 1 },
  carry_yd: { label: "Carry", unit: "yd", dec: 0 },
  side_yd: { label: "Side", unit: "yd", dec: 1, signed: true, lateral: true,
    words: (rh, d) => (isZero(d, ON_LINE_YD) ? "on the line" : `${dirWord(d)} of target`) },
  curve_yd: { label: "Curve", unit: "yd", dec: 1, signed: true, lateral: true,
    words: (rh, d) => (isZero(d, 0.05) ? "no curve" : `curves ${dirWord(d)}`) },
  total_yd: { label: "Total", unit: "yd", dec: 0, noBand: true,
    words: () => "carry plus roll" },
};

/** Slider metrics in the order the sliders appear. */
export const SLIDER_METRICS = ["club_speed_mph", "attack_deg", "path_deg", "face_deg", "dyn_loft_deg"];

export const TILE_GROUPS = [
  { id: "club", name: "Club", note: "What you set with the sliders, plus face to path and spin loft.",
    items: ["club_speed_mph", "attack_deg", "path_deg", "face_deg", "face_to_path_deg", "dyn_loft_deg", "spin_loft_deg"] },
  { id: "ball", name: "Ball", note: "Dogleg Data model output.",
    items: ["ball_speed_mph", "smash", "launch_deg", "launch_dir_deg", "spin_rpm", "spin_axis_deg"] },
  { id: "flight", name: "Flight", note: "Dogleg Data model output.",
    items: ["max_height_yd", "land_angle_deg", "carry_yd", "side_yd", "curve_yd", "total_yd"] },
];

// The six tiles beside the range. The phone shows the four that are not extra:
// start line, curve, carry, height.
export const KEY_TILES = [
  { metric: "face_to_path_deg", extra: true },
  { metric: "launch_dir_deg" },
  { metric: "spin_axis_deg", extra: true },
  { metric: "curve_yd" },
  { metric: "carry_yd" },
  { metric: "max_height_yd" },
];

export function fmt(v, dec, signed, grouped) {
  let s = Math.abs(v).toFixed(dec);
  if (Number(s) === 0) return (0).toFixed(dec);
  if (grouped) s = Number(s).toLocaleString("en-US", { maximumFractionDigits: dec });
  if (v < 0) return MINUS + s;
  return (signed ? "+" : "") + s;
}

/** The band in the display frame: a lateral band is mirrored for a left-handed golfer. */
export function displayBand(metric, band, hand) {
  if (!band) return null;
  if (hand === "l" && METRICS[metric].lateral) {
    return { ...band, lo: band.hi === null ? null : -band.hi, hi: band.lo === null ? null : -band.lo };
  }
  return band;
}

/** Geometry of the band bar: percent positions for the band and the marker. */
export function barGeometry(band, value) {
  const { lo, hi, target } = band;
  let a, b;
  if (lo !== null && hi !== null) {
    const w = hi - lo || 1;
    a = lo - 0.9 * w;
    b = hi + 0.9 * w;
  } else if (lo !== null) {
    const w = 2 * Math.abs(target - lo) || 1;
    a = lo - w;
    b = lo + 3 * w;
  } else {
    const w = 2 * Math.abs(hi - target) || 1;
    a = hi - 3 * w;
    b = hi + w;
  }
  const pct = (x) => ((x - a) / (b - a)) * 100;
  const bandL = lo === null ? 0 : pct(lo);
  const bandR = hi === null ? 100 : pct(hi);
  const raw = pct(value);
  const val = Math.min(100, Math.max(0, raw));
  return { bandL, bandR, val, edge: raw < 0 || raw > 100 };
}

export function statusOf(band, value) {
  const eps = 1e-9;
  if (band.lo !== null && value < band.lo - eps) return "below";
  if (band.hi !== null && value > band.hi + eps) return "above";
  return "in";
}

const unitText = (m) => (m.unit === DEG ? DEG : m.unit ? " " + m.unit : "");

/** The band as {lead, range}: "ideal" and the unbreakable range, so a note wraps after "ideal" or not at all. */
function idealParts(m, band) {
  const f = (x) => fmt(x, m.dec, m.signed, m.grouped);
  const u = unitText(m);
  if (band.lo !== null && band.hi !== null) return { lead: "ideal", range: `${f(band.lo)} to ${f(band.hi)}${u}` };
  if (band.lo !== null) return { lead: "ideal", range: `${f(band.lo)}${u} or more` };
  return { lead: "ideal", range: `up to ${f(band.hi)}${u}` };
}
function idealText(m, band) {
  const p = idealParts(m, band);
  return `${p.lead} ${p.range}`;
}

/** Source strings from ideals.json read like data. Clean them for display. */
export function humanize(text, hasDetail) {
  let t = String(text || "")
    .replace(/\+-/g, "±")
    .replace(/^MODELED:/, "Modeled:")
    .replace(/\(MODELED margin\)/g, "(modeled margin)");
  if (hasDetail) t = t.replace(/\s*\(values in detail\)/, "");
  return t;
}

/** The text behind a tile's i button: band, source, and for driver launch and spin the live source values. */
export function sourceText(metric, band, exception) {
  const m = METRICS[metric];
  let text = `Ideal band, ${idealText(m, band).replace(/^ideal /, "")}. ${humanize(band.source, !!band.detail)}`;
  if (band.detail && band.detail.trackman_carry_2010 && band.detail.ping_2019) {
    const key = metric === "launch_deg" ? "launch_deg" : "spin_rpm";
    const f = (x) => fmt(x, m.dec, false, m.grouped) + unitText(m);
    const i = band.detail.inputs;
    text += ` Right now: TrackMan 2010 ${f(band.detail.trackman_carry_2010[key])}, PING 2019 ${f(band.detail.ping_2019[key])}`
      + ` (${Math.round(i.club_speed_mph)} mph club speed, ${i.ball_speed_mph.toFixed(1)} mph ball speed, ${fmt(i.attack_deg, 1, true)}${DEG} attack).`;
  }
  if (band.modeled && !/modeled/i.test(text)) text += " This band is modeled.";
  if (exception && exception.note) text += " " + exception.note;
  return text;
}

/**
 * Build one tile. prefix keeps element ids unique when the same metric shows
 * twice on the page. Returns {el, metric, update(entry, band, hand, exception)}.
 */
export function createTile(metric, prefix, extraClass) {
  const m = METRICS[metric];
  const id = `${prefix}-${metric}`;
  const el = document.createElement("div");
  el.className = "tile" + (extraClass ? " " + extraClass : "");
  el.setAttribute("role", "group");
  el.dataset.metric = metric;
  el.innerHTML = `
    <div class="tile-top">
      <span class="tile-label">${m.label}</span>
      <button type="button" class="tile-info" aria-expanded="false" aria-controls="${id}-src" aria-label="About the ${m.label.toLowerCase()} band"><span aria-hidden="true">i</span></button>
    </div>
    <span class="badge-modeled" hidden>modeled</span>
    <div class="tile-val"><span class="v"></span><span class="u${m.unit === DEG ? " deg" : ""}">${m.unit}</span></div>
    <div class="tile-word"></div>
    <div class="bar" aria-hidden="true"><i class="band"></i><i class="mark"></i></div>
    <div class="tile-cap"><span class="status"></span><span class="ideal"><span class="il"></span> <span class="nw"></span></span></div>
    <p class="tile-src" id="${id}-src" hidden></p>`;
  const $ = (s) => el.querySelector(s);
  const vEl = $(".v");
  const wordEl = $(".tile-word");
  const bar = $(".bar");
  const bandEl = $(".band");
  const markEl = $(".mark");
  const statusEl = $(".status");
  let lastIdeal = "";
  const idealLead = $(".ideal .il");
  const idealRange = $(".ideal .nw");
  const capEl = $(".tile-cap");
  const srcEl = $(".tile-src");
  const badge = $(".badge-modeled");
  const info = $(".tile-info");

  info.addEventListener("click", () => {
    const open = info.getAttribute("aria-expanded") === "true";
    info.setAttribute("aria-expanded", String(!open));
    srcEl.hidden = open;
  });

  return {
    el,
    metric,
    update(entry, rawBand, hand, exception) {
      const value = entry.disp;
      vEl.textContent = fmt(value, m.dec, m.signed, m.grouped);
      wordEl.textContent = m.words ? m.words(entry.rh, entry.disp) : "";
      const band = m.noBand ? null : displayBand(metric, rawBand, hand);
      if (!band) {
        el.classList.remove("in", "out");
        bar.hidden = true;
        capEl.hidden = true;
        badge.hidden = false;
        el.setAttribute("aria-label", `${m.label} ${vEl.textContent} ${m.unit}, modeled`);
        srcEl.textContent = "Total is the carry plus a roll that the Dogleg Data model estimates from the landing angle and speed. It is a modeled number.";
        info.title = srcEl.textContent;
        return;
      }
      const st = statusOf(band, value);
      el.classList.remove("in", "out");
      el.classList.add(st === "in" ? "in" : "out");
      const g = barGeometry(band, value);
      bandEl.style.left = g.bandL + "%";
      bandEl.style.width = Math.max(0, g.bandR - g.bandL) + "%";
      markEl.style.left = g.val + "%";
      markEl.classList.toggle("edge", g.edge);
      const statusText = st === "in" ? "In band" : st === "above" ? "Above band" : "Below band";
      statusEl.textContent = (st === "in" ? "✓ " : st === "above" ? "▲ " : "▼ ") + statusText;
      // The band moves only when the club, player, speed or attack changes, so most drag steps skip this.
      const ip = idealParts(m, band);
      const ideal = ip.lead + " " + ip.range;
      if (ideal !== lastIdeal) {
        lastIdeal = ideal;
        idealLead.textContent = ip.lead;
        idealRange.textContent = ip.range;
        bar.title = ideal; // the key tiles drop the note, the bar keeps it
      }
      badge.hidden = !band.modeled;
      srcEl.textContent = sourceText(metric, band, exception);
      info.title = srcEl.textContent;
      // Screen readers get the value and the status together.
      el.setAttribute("aria-label", `${m.label} ${vEl.textContent} ${m.unit}, ${statusText.toLowerCase()}`);
    },
  };
}
