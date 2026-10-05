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
/** Heights show in feet. The model and the data stay in yards. */
export const FT_PER_YD = 3;
export const DEG = "°";

// The "on the line" distance for Side. The page sets it from the model's classify
// on_line_yd, so the tile, the shot name and the top view all agree.
let ON_LINE_YD = 0.05;
export function configureTiles({ onLineYd }) {
  if (Number.isFinite(onLineYd)) ON_LINE_YD = onLineYd;
}
const dirWord = (v) => (v > 0 ? "right" : "left");

/** "face 3.0° closed to path takes 1.5° off", or "adds 1.8°", when the face has moved the effective loft off the slider's. */
export function loftNote(effective, entry) {
  if (!entry || entry.input === undefined) return "";
  const delta = effective - entry.input;
  if (Math.abs(delta) < 0.05) return "";
  const f2p = entry.faceToPathRh;
  const rel = f2p < 0 ? "closed" : "open";
  return `face ${Math.abs(f2p).toFixed(1)}\u00B0 ${rel} to path ${delta < 0 ? "takes" : "adds"} ${Math.abs(delta).toFixed(1)}\u00B0${delta < 0 ? " off" : ""}`;
}
const isZero = (v, tol) => Math.abs(v) < tol;

/** "lie 3.0° toe up opens 1.3°", "heel strike bulge closes 2.5°", or both, when the lie or the strike moved the face off the slider's. */
export function faceNote(effective, entry) {
  if (!entry || entry.input === undefined) return "";
  const delta = effective - entry.input;
  if (Math.abs(delta) < 0.05) return "";
  const causes = [];
  if (Math.abs(entry.lie || 0) >= 0.05) causes.push(`lie ${Math.abs(entry.lie).toFixed(1)}\u00B0 toe ${entry.lie > 0 ? "up" : "down"}`);
  if (Math.abs(entry.strikeToe || 0) >= 0.5) causes.push(`${entry.strikeToe > 0 ? "toe" : "heel"} strike bulge`);
  const open = delta > 0 ? (entry.hand === "l" ? "closes" : "opens") : (entry.hand === "l" ? "opens" : "closes");
  return `${causes.join(" and ") || "lie and strike"} ${open} ${Math.abs(delta).toFixed(1)}\u00B0`;
}

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
  // The tile shows the EFFECTIVE face at the impact point (what TrackMan would measure). The slider sets the
  // face before the lie tilt and the bulge of an off-center strike move it.
  face_deg: { label: "Face angle", unit: DEG, dec: 1, signed: true, lateral: true,
    words: (rh, d, e) => faceNote(d, e) || (isZero(rh, 0.05) ? "square to target" : rh > 0 ? "open to target" : "closed to target"),
    slider: { stateKey: "face", step: 0.5, dom: "face_deg", zero: true, label: "Face angle (to target)",
      hints: (h) => (h === "l" ? [MINUS + " open", "+ closed"] : [MINUS + " closed", "+ open"]) } },
  face_to_path_deg: { label: "Face to path", unit: DEG, dec: 1, signed: true, lateral: true,
    words: (rh) => (isZero(rh, 0.05) ? "square to path" : rh > 0 ? "open to path" : "closed to path") },
  // The tile shows the EFFECTIVE loft (what TrackMan would measure). The slider sets the loft with the face
  // square to the path, and closing or opening the face against the path moves the effective loft off it.
  dyn_loft_deg: { label: "Dynamic loft", unit: DEG, dec: 1,
    words: (rh, d, e) => loftNote(d, e),
    slider: { stateKey: "dynLoft", step: 0.5, dom: "dyn_loft_deg", advanced: true, label: "Dynamic loft (face square to path)" } },
  // Lie at impact and strike location (advanced sliders). The toe is the toe for both hands, so none is lateral.
  lie_deg: { label: "Lie at impact", unit: DEG, dec: 1, signed: true,
    words: (rh) => (isZero(rh, 0.05) ? "as addressed" : rh > 0 ? "toe up, opens the face" : "toe down, closes the face"),
    noBandText: "The change of lie at impact from the club's address lie, positive toe up. A toe-up (flat) lie opens the face by about the tangent of the loft per degree and a toe-down (upright) lie closes it, so a wedge moves most and a driver least. Geometry, no ideal band: 0 is the address lie.",
    slider: { stateKey: "lie", step: 0.5, dom: "lie_deg", zero: true, advanced: true, label: "Lie at impact",
      hints: () => [MINUS + " toe down", "+ toe up"] } },
  strike_toe_mm: { label: "Strike, heel to toe", unit: "mm", dec: 0, signed: true,
    words: (rh) => (isZero(rh, 0.5) ? "center of the face" : rh > 0 ? "toward the toe, draw spin" : "toward the heel, fade spin"),
    noBandText: "Where the ball met the face, mm from center toward the toe. Gear effect: a toe strike adds draw spin and a heel strike fade spin (about 0.47 rpm per mm per mph of ball speed, from TrackMan's published examples). On a driver or fairway wood the bulge of the face also opens the face at a toe strike and closes it at a heel strike, 2 degrees per 10 mm. Any strike off center costs ball speed. Modeled; 0 is the player group's own typical strike.",
    slider: { stateKey: "strikeToe", step: 1, dom: "strike_toe_mm", zero: true, advanced: true, label: "Strike, heel to toe",
      hints: () => [MINUS + " heel", "+ toe"] } },
  strike_up_mm: { label: "Strike, high or low", unit: "mm", dec: 0, signed: true,
    words: (rh) => (isZero(rh, 0.5) ? "center of the face" : rh > 0 ? "above center, less spin" : "below center, more spin"),
    noBandText: "Where the ball met the face, mm above center. On a driver or fairway wood the roll of the face adds loft above center (2 degrees per 10 mm) and the vertical gear effect takes backspin off, so a high strike launches higher with less spin; a low strike does the reverse. Irons and hybrids have a flat face and their center of gravity near it, so only the ball speed loss applies. Modeled; 0 is the player group's own typical strike.",
    slider: { stateKey: "strikeUp", step: 1, dom: "strike_up_mm", zero: true, advanced: true, label: "Strike, high or low",
      hints: () => [MINUS + " low", "+ high"] } },
  spin_loft_deg: { label: "Spin loft", unit: DEG, dec: 1 },
  ball_speed_mph: { label: "Ball speed", unit: "mph", dec: 1 },
  smash: { label: "Smash factor", unit: "", dec: 2 },
  launch_deg: { label: "Launch angle", unit: DEG, dec: 1 },
  launch_dir_deg: { label: "Launch direction", unit: DEG, dec: 1, signed: true, lateral: true,
    words: (rh, d) => (isZero(d, 0.05) ? "on target line" : `starts ${dirWord(d)}`) },
  spin_rpm: { label: "Spin rate", unit: "rpm", dec: 0, grouped: true },
  spin_axis_deg: { label: "Spin axis", unit: DEG, dec: 1, signed: true, lateral: true,
    words: (rh, d) => (isZero(d, 0.05) ? "no side spin" : `tilts ${dirWord(d)}`) },
  gear_side_rpm: { label: "Gear effect, side", unit: "rpm", dec: 0, signed: true, lateral: true, grouped: true,
    words: (rh, d) => (isZero(d, 0.5) ? "center strike" : `${d > 0 ? "fade" : "draw"} spin from the strike`),
    noBandText: "Sidespin the horizontal gear effect added for a heel or toe strike, positive curving right. It is added as a vector to the spin the D-plane gives, so the spin rate and the spin axis both move. Modeled on TrackMan's published gear-effect examples." },
  gear_back_rpm: { label: "Gear effect, back", unit: "rpm", dec: 0, signed: true, grouped: true,
    words: (rh) => (isZero(rh, 0.5) ? "center strike" : rh > 0 ? "more backspin, low strike" : "less backspin, high strike"),
    noBandText: "Backspin the vertical gear effect added for a strike above or below center on a driver or fairway wood, negative above center. Irons and hybrids get none. Modeled, 1.75 times the horizontal gear effect for the same offset." },
  max_height_yd: { label: "Height", unit: "ft", dec: 0 }, // value and band are converted to feet by state.compute
  land_angle_deg: { label: "Land angle", unit: DEG, dec: 1 },
  carry_yd: { label: "Carry", unit: "yd", dec: 0 },
  side_yd: { label: "Side", unit: "yd", dec: 1, signed: true, lateral: true,
    words: (rh, d) => (isZero(d, ON_LINE_YD) ? "on the line" : `${dirWord(d)} of target`) },
  curve_yd: { label: "Curve", unit: "yd", dec: 1, signed: true, lateral: true,
    words: (rh, d) => (isZero(d, 0.05) ? "no curve" : `curves ${dirWord(d)}`) },
  total_yd: { label: "Total", unit: "yd", dec: 0,
    words: () => "carry plus roll" },
};

/** Slider metrics in the order the sliders appear. */
export const SLIDER_METRICS = ["club_speed_mph", "attack_deg", "path_deg", "face_deg", "dyn_loft_deg", "lie_deg", "strike_toe_mm", "strike_up_mm"];

export const TILE_GROUPS = [
  { id: "club", name: "Club", note: "What you set with the sliders, plus face to path and spin loft.",
    items: ["club_speed_mph", "attack_deg", "path_deg", "face_deg", "face_to_path_deg", "dyn_loft_deg", "spin_loft_deg", "lie_deg", "strike_toe_mm", "strike_up_mm"] },
  { id: "ball", name: "Ball", note: "Dogleg Data model output.",
    items: ["ball_speed_mph", "smash", "launch_deg", "launch_dir_deg", "spin_rpm", "spin_axis_deg", "gear_side_rpm", "gear_back_rpm"] },
  { id: "flight", name: "Flight", note: "Dogleg Data model output.",
    items: ["max_height_yd", "land_angle_deg", "carry_yd", "side_yd", "curve_yd", "total_yd"] },
];

// The six tiles beside the range. Narrower layouts and the phone show the four that are not
// extra: curve, carry, total, height (the shot label already gives the start line).
export const KEY_TILES = [
  { metric: "face_to_path_deg", extra: true },
  { metric: "launch_dir_deg", extra: true },
  { metric: "curve_yd" },
  { metric: "carry_yd" },
  { metric: "total_yd" },
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
  let src = humanize(band.source, !!band.detail);
  // The band's own source text quotes yards. Say feet, like the tile.
  if (metric === "max_height_yd") src = src.replace(/(\d+(?:\.\d+)?) yd/g, (_m, n) => `${Math.round(Number(n) * FT_PER_YD)} ft`);
  let text = `Ideal band, ${idealText(m, band).replace(/^ideal /, "")}. ${src}`;
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
      wordEl.textContent = m.words ? m.words(entry.rh, entry.disp, entry) : "";
      const band = m.noBand || !rawBand ? null : displayBand(metric, rawBand, hand);
      if (!band) {
        el.classList.remove("in", "out");
        bar.hidden = true;
        capEl.hidden = true;
        badge.hidden = false;
        el.setAttribute("aria-label", `${m.label} ${vEl.textContent} ${m.unit}, modeled`);
        srcEl.textContent = m.noBandText || "Total is the carry plus a roll that the Dogleg Data model estimates from the landing angle and speed. It is a modeled number.";
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
