/*
 * The three secondary views under the range: top-down, side profile and the
 * impact diagram. All are inline SVG built here, drawn at the panel's real pixel
 * width (a ResizeObserver redraws on resize), so the text is always 12px or more.
 *
 * One plot style throughout: card background, muted grid, ink axes and labels in
 * mono. The current shot is clay, the ghost is a dashed muted line, the pinned
 * shot A (Compare mode) is denim. Colors come from classes in tool.css.
 *
 * Everything is in the display frame (positive is right of the target line, for
 * both hands), so a lefty draw curves right here as it does on the range.
 */
import { MINUS, DEG, fmt } from "./tiles.js";

const NS = "http://www.w3.org/2000/svg";
const RAD = Math.PI / 180;
const VERB = { draw: "draws", hook: "hooks", fade: "fades", slice: "slices", straight: "goes straight" };

function el(tag, attrs, cls) {
  const e = document.createElementNS(NS, tag);
  if (cls) e.setAttribute("class", cls);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  return e;
}
function add(parent, tag, attrs, cls) {
  const e = el(tag, attrs, cls);
  parent.appendChild(e);
  return e;
}
function label(parent, x, y, str, cls = "", anchor = "start") {
  const t = add(parent, "text", { x, y, "text-anchor": anchor }, "pv-text " + cls);
  t.textContent = str;
  return t;
}
const f1 = (v) => fmt(v, 1, true);
const pts = (list) => list.map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
const arcPath = (cx, cy, r, a0, a1, sweep) => {
  // angles in screen radians measured from the +x axis, y down
  const p0 = [cx + r * Math.cos(a0), cy + r * Math.sin(a0)];
  const p1 = [cx + r * Math.cos(a1), cy + r * Math.sin(a1)];
  return `M ${cx} ${cy} L ${p0[0].toFixed(1)} ${p0[1].toFixed(1)} A ${r} ${r} 0 0 ${sweep} ${p1[0].toFixed(1)} ${p1[1].toFixed(1)} Z`;
};
function arrowHead(parent, x, y, angle, size, cls) {
  // angle: direction the arrow points, screen radians (y down)
  const a1 = angle + Math.PI - 0.42, a2 = angle + Math.PI + 0.42;
  add(parent, "polygon", { points: pts([[x, y], [x + size * Math.cos(a1), y + size * Math.sin(a1)], [x + size * Math.cos(a2), y + size * Math.sin(a2)]]) }, cls);
}
const niceCeil = (v, step) => Math.max(step, Math.ceil(v / step) * step);

/** Points of a shot as [x, y, z] samples (every 3rd, plus the last). */
function samples(s) {
  const out = [];
  for (let i = 0; i < s.x.length; i += 3) out.push([s.x[i], s.y[i], s.z[i]]);
  const l = s.x.length - 1;
  if ((l % 3) !== 0) out.push([s.x[l], s.y[l], s.z[l]]);
  return out;
}

export function createViews({ root, onLineYd = 0.5 }) {
  const panels = {};
  for (const name of ["top", "side", "impact"]) {
    const host = root.querySelector(`[data-view="${name}"] .vbody`);
    const svg = add(host, "svg", { role: "img", "aria-label": "" }, "pv");
    panels[name] = { host, svg, W: 0, H: 0 };
  }
  let last = null;

  function size(p, ratio = 1.2) {
    p.W = Math.max(0, Math.floor(p.host.clientWidth));
    p.H = Math.round(Math.max(200, Math.min(440, p.W * ratio)));
    p.svg.setAttribute("width", p.W);
    p.svg.setAttribute("height", p.H);
    p.svg.setAttribute("viewBox", `0 0 ${p.W} ${p.H}`);
  }
  function clear(p) { p.svg.replaceChildren(); }

  // ---- top view ----------------------------------------------------------------
  function drawTop(p, c) {
    size(p); clear(p);
    const { W, H, svg } = p;
    if (W < 60) return;
    const shots = [c.shot, c.ghost, c.pinned].filter(Boolean);
    const ml = 38, mr = 14, mt = 26, mb = 34;
    const pw = W - ml - mr, ph = H - mt - mb;
    const carryMax = Math.max(...shots.map((s) => s.carry));
    const yStep = carryMax > 180 ? 100 : 50;
    const yMax = niceCeil(carryMax * 1.06, yStep);
    let latMax = 8;
    for (const s of shots) for (let i = 0; i < s.y.length; i += 5) latMax = Math.max(latMax, Math.abs(s.y[i]));
    const ky = ph / yMax;
    // Sideways is stretched by a whole number so bends read. The plot says so.
    const stretch = Math.max(1, Math.min(4, Math.floor((pw / 2 / (latMax * 1.25)) / ky)));
    const kx = ky * stretch;
    const cx = ml + pw / 2, y0 = mt + ph;
    const X = (lat) => cx + lat * kx;
    const Y = (d) => y0 - d * ky;
    const clipId = "pvclip-top";
    const defs = add(svg, "defs", {});
    add(add(defs, "clipPath", { id: clipId }), "rect", { x: ml, y: mt, width: pw, height: ph });

    add(svg, "rect", { x: ml, y: mt, width: pw, height: ph }, "pv-plot");
    // grid: distance rows, sideways columns
    for (let d = yStep; d <= yMax; d += yStep) {
      add(svg, "line", { x1: ml, x2: ml + pw, y1: Y(d), y2: Y(d) }, "pv-grid");
      label(svg, ml - 6, Y(d) + 4, String(d), "muted", "end");
    }
    label(svg, ml - 6, y0 + 4, "0", "muted", "end");
    const latStepChoices = [5, 10, 20, 25, 50];
    const latStep = latStepChoices.find((s) => s * kx >= 46) || 50;
    for (let m = latStep; m * kx < pw / 2; m += latStep) {
      for (const sgn of [-1, 1]) {
        add(svg, "line", { x1: X(sgn * m), x2: X(sgn * m), y1: mt, y2: y0 }, "pv-grid");
        // keep the tick text inside the panel
        if (Math.abs(X(sgn * m) - cx) < pw / 2 - 14) label(svg, X(sgn * m), y0 + 15, `${m}${sgn < 0 ? " L" : " R"}`, "muted", "middle");
      }
    }
    const g = add(svg, "g", { "clip-path": `url(#${clipId})` });
    // target line
    add(g, "line", { x1: cx, x2: cx, y1: y0, y2: mt }, "pv-target");

    const path = (s, cls) => add(g, "polyline", { points: pts(samples(s).map((q) => [X(q[1]), Y(q[0])])) }, cls);
    if (c.ghost) path(c.ghost, "pv-path ghost");
    if (c.pinned) path(c.pinned, "pv-path pin");
    // start line
    const tan = Math.tan(c.shot.launchDir * RAD);
    add(g, "line", { x1: X(0), y1: Y(0), x2: X(c.shot.carry * tan), y2: Y(c.shot.carry) }, "pv-start");
    path(c.shot, "pv-path");
    if (c.pinned) {
      const q = c.pinned;
      add(g, "circle", { cx: X(q.y[q.y.length - 1]), cy: Y(q.carry), r: 4.5 }, "pv-dot pin");
    }
    const lat = c.shot.y[c.shot.y.length - 1];
    const lx = X(lat), ly = Y(c.shot.carry);
    add(g, "circle", { cx: lx, cy: ly, r: 5.5 }, "pv-dot");
    // landing label: side distance, on the roomier side of the dot
    const sideTxt = Math.abs(lat) < onLineYd ? "on line" : `${Math.abs(lat).toFixed(0)} yd ${lat > 0 ? "right" : "left"}`;
    const onRight = lx < cx + pw * 0.15;
    label(svg, Math.max(ml + 4, Math.min(ml + pw - 4, onRight ? lx + 10 : lx - 10)), Math.max(mt + 14, ly + 4), sideTxt, "ink", onRight ? "start" : "end");
    // ball at the origin
    add(svg, "circle", { cx: X(0), cy: Y(0), r: 3.5 }, "pv-ball");
    label(svg, ml, 12, "yd downrange", "muted");
    const narrow = W < 300;
    label(svg, ml + pw, H - 4, stretch > 1 ? `${narrow ? "sideways" : "side distance"} ×${stretch}` : "sideways to scale", "muted", "end");
    if (!narrow) label(svg, ml, H - 4, "L ← → R", "muted");
    const sideWord = Math.abs(lat) < onLineYd ? "on the target line" : `${Math.abs(lat).toFixed(0)} yards ${lat > 0 ? "right" : "left"} of the target line`;
    svg.setAttribute("aria-label", `Top view. The ball carries ${Math.round(c.shot.carry)} yards and lands ${sideWord}.${stretch > 1 ? " Sideways distance is stretched " + stretch + " times." : ""}`);
  }

  // ---- side view -----------------------------------------------------------------
  function drawSide(p, c) {
    size(p, 0.86); clear(p);
    const { W, H, svg } = p;
    if (W < 60) return;
    const shots = [c.shot, c.ghost, c.pinned].filter(Boolean);
    const ml = 38, mr = 12, mb = 34;
    const pw = W - ml - mr;
    const carryMax = Math.max(...shots.map((s) => s.carry));
    const xStep = carryMax > 180 ? 100 : 50;
    const xMax = niceCeil(carryMax * 1.04, xStep);
    const hMax = Math.max(...shots.map((s) => s.maxHeight));
    const y0 = H - mb;
    // One scale for both axes, so the angles are true. The top 66px stay free for the readout.
    const readoutH = W < 300 ? 86 : 66;
    const k = Math.min(pw / xMax, (y0 - readoutH) / (hMax * 1.25 + 8));
    const X = (d) => ml + d * k;
    const Y = (h) => y0 - h * k;
    const plotTop = Math.max(6, Y(hMax * 1.25 + 8));
    add(svg, "rect", { x: ml, y: plotTop, width: pw, height: y0 - plotTop }, "pv-plot");
    for (let d = xStep; d <= xMax; d += xStep) {
      add(svg, "line", { x1: X(d), x2: X(d), y1: plotTop, y2: y0 }, "pv-grid");
      label(svg, X(d), y0 + 15, String(d), "muted", "middle");
    }
    label(svg, X(0), y0 + 15, "0", "muted", "middle");
    // Height reads in feet. The plot itself stays in yards on both axes, so the angles stay true.
    const hStepFt = hMax * 3 > 180 ? 100 : 50;
    for (let ft = hStepFt; Y(ft / 3) > plotTop + 6; ft += hStepFt) {
      add(svg, "line", { x1: ml, x2: ml + pw, y1: Y(ft / 3), y2: Y(ft / 3) }, "pv-grid");
      label(svg, ml - 6, Y(ft / 3) + 4, String(ft), "muted", "end");
    }
    label(svg, ml - 6, y0 + 4, "0", "muted", "end");
    add(svg, "line", { x1: ml, x2: ml + pw, y1: y0, y2: y0 }, "pv-target");
    label(svg, ml + pw, H - 4, "yd downrange", "muted", "end");
    label(svg, ml, plotTop - 2 < 12 ? 12 : plotTop - 2, "ft high", "muted");

    const path = (s, cls) => add(svg, "polyline", { points: pts(samples(s).map((q) => [X(q[0]), Y(q[2])])) }, cls);
    if (c.ghost) path(c.ghost, "pv-path ghost");
    if (c.pinned) path(c.pinned, "pv-path pin");
    const s = c.shot;
    const launch = c.values.launch_deg.disp;
    const land = c.values.land_angle_deg.disp;
    // launch wedge at the start, true angle
    const R = Math.min(64, pw * 0.22);
    add(svg, "path", { d: arcPath(X(0), y0, R, -launch * RAD, 0, 1) }, "pv-wedge");
    add(svg, "line", { x1: X(0), y1: y0, x2: X(0) + Math.cos(launch * RAD) * (R + 22), y2: y0 - Math.sin(launch * RAD) * (R + 22) }, "pv-start");
    path(s, "pv-path");
    // Every path drawn here, as screen points, so labels can keep clear of the lines.
    const linePts = [];
    for (const q of shots) for (const p3 of samples(q)) linePts.push([X(p3[0]), Y(p3[2])]);
    const isClear = (x, yb, txt, anchor) => {
      const w = txt.length * 7.3;
      const x0 = anchor === "end" ? x - w : anchor === "middle" ? x - w / 2 : x;
      return !linePts.some((q) => q[0] > x0 - 5 && q[0] < x0 + w + 5 && q[1] > yb - 15 && q[1] < yb + 5);
    };
    /** Put a label at the first candidate spot that does not sit on a path. Skipped if none is free. */
    const placeLabel = (txt, cands, cls) => {
      const c0 = cands.find(([x, yb, anchor]) => isClear(x, yb, txt, anchor));
      if (c0) label(svg, c0[0], c0[1], txt, cls, c0[2]);
    };
    placeLabel(`${launch.toFixed(0)}${DEG}`, [[X(0) + R + 4, y0 - 5, "start"], [X(0) + 8, y0 - 22, "start"], [X(0) + R + 4, y0 - 20, "start"]], "ink");
    // apex, at its true height
    let ai = 0;
    for (let i = 1; i < s.z.length; i++) if (s.z[i] > s.z[ai]) ai = i;
    add(svg, "line", { x1: X(s.x[ai]), x2: X(s.x[ai]), y1: Y(s.z[ai]), y2: y0 }, "pv-start");
    add(svg, "circle", { cx: X(s.x[ai]), cy: Y(s.z[ai]), r: 5 }, "pv-dot");
    placeLabel(`${Math.round(s.maxHeight * 3)} ft`, [[X(s.x[ai]), Y(s.z[ai]) - 10, "middle"], [X(s.x[ai]) - 10, Y(s.z[ai]) - 8, "end"], [X(s.x[ai]) + 10, Y(s.z[ai]) - 8, "start"]], "ink");
    // landing angle, true
    const lx = X(s.carry);
    const wr = 30;
    add(svg, "path", { d: arcPath(lx, y0, wr, Math.PI, Math.PI + land * RAD, 1) }, "pv-wedge");
    add(svg, "line", { x1: lx, y1: y0, x2: lx - Math.cos(land * RAD) * (wr + 26), y2: y0 - Math.sin(land * RAD) * (wr + 26) }, "pv-start");
    add(svg, "circle", { cx: lx, cy: y0, r: 4.5 }, "pv-dot");
    placeLabel(`${land.toFixed(0)}${DEG}`, [[lx - wr - 6, y0 - 5, "end"], [lx - wr - 6, y0 - 22, "end"], [lx + 8, y0 - 14, "start"]], "ink");
    // readout in the space above the plot, where the flat profile leaves room
    const rows = [["launch", `${launch.toFixed(1)}${DEG}`], ["land", `${land.toFixed(1)}${DEG}`], ["peak", `${Math.round(s.maxHeight * 3)} ft`], ["carry", `${Math.round(s.carry)} yd`]];
    const oneColumn = W < 300; // two columns of label and value do not fit a narrow panel
    rows.forEach(([k, val], i) => {
      const rx = oneColumn ? ml : ml + (i % 2) * (pw / 2), ry = oneColumn ? 26 + i * 15 : 30 + Math.floor(i / 2) * 20;
      label(svg, rx, ry, k, "muted");
      label(svg, rx + 52, ry, val, "ink strong");
    });
    svg.setAttribute("aria-label", `Side view. Launch angle ${launch.toFixed(1)} degrees, peak height ${Math.round(s.maxHeight * 3)} feet, lands at ${land.toFixed(1)} degrees after ${Math.round(s.carry)} yards.`);
  }

  // ---- impact diagram ---------------------------------------------------------------
  function drawImpact(p, c) {
    size(p); clear(p);
    const { W, H, svg } = p;
    if (W < 60) return;
    const v = c.values;
    const pathD = v.path_deg.disp, faceD = v.face_deg.disp;
    const f2pRh = v.face_to_path_deg.rh, f2pDisp = v.face_to_path_deg.disp;
    const half = H / 2;
    const L = Math.min(76, W * 0.3);

    // -- top view of the club head (upper half)
    const g1 = add(svg, "g", {});
    label(g1, 6, 14, "Top view", "muted");
    const cx = W / 2, cy = half * 0.74;
    add(g1, "line", { x1: cx, y1: cy + 14, x2: cx, y2: 22 }, "pv-target");
    arrowHead(g1, cx, 20, -Math.PI / 2, 8, "pv-head target");
    label(g1, cx + 10, 30, "target", "muted");
    const dir = (deg) => [Math.sin(deg * RAD), -Math.cos(deg * RAD)]; // screen vector, up is target
    const pd = dir(pathD), nd = dir(faceD);
    // wedge between the path direction and the face normal
    let wedgeTip = null;
    if (Math.abs(faceD - pathD) > 0.05) {
      const a0 = Math.atan2(pd[1], pd[0]), a1 = Math.atan2(nd[1], nd[0]);
      add(g1, "path", { d: arcPath(cx, cy, L * 0.98, a0, a1, faceD > pathD ? 1 : 0) }, "pv-wedge");
      const mid = (a0 + a1) / 2;
      wedgeTip = [cx + L * 0.98 * Math.cos(mid), cy + L * 0.98 * Math.sin(mid)];
    }
    // swing path arrow, through the ball
    add(g1, "line", { x1: cx - pd[0] * L, y1: cy - pd[1] * L, x2: cx + pd[0] * L, y2: cy + pd[1] * L }, "pv-arrow path");
    arrowHead(g1, cx + pd[0] * L, cy + pd[1] * L, Math.atan2(pd[1], pd[0]), 9, "pv-head path");
    // clubface: a thick line across the face normal, with the shaft toward the golfer
    const tdir = [Math.cos(faceD * RAD), Math.sin(faceD * RAD)]; // along the face
    const heel = c.hand === "l" ? 1 : -1;
    add(g1, "line", { x1: cx + tdir[0] * heel * 26, y1: cy + tdir[1] * heel * 26, x2: cx + tdir[0] * heel * 80, y2: cy + tdir[1] * heel * 80 }, "pv-shaft");
    add(g1, "line", { x1: cx - tdir[0] * 30, y1: cy - tdir[1] * 30, x2: cx + tdir[0] * 30, y2: cy + tdir[1] * 30 }, "pv-face");
    // The strike point along the face: the toe is away from the golfer. 30 px of half face stands for about 50 mm.
    const strikeToe = v.strike_toe_mm ? v.strike_toe_mm.disp : 0;
    const strikeUp = v.strike_up_mm ? v.strike_up_mm.disp : 0;
    const lie = v.lie_deg ? v.lie_deg.disp : 0;
    const struck = Math.abs(strikeToe) >= 0.5 || Math.abs(strikeUp) >= 0.5;
    if (struck) {
      const off = -heel * strikeToe * 0.6;
      add(g1, "circle", { cx: cx + tdir[0] * off, cy: cy + tdir[1] * off, r: 3.2 }, "pv-strike");
    }
    label(g1, cx + tdir[0] * heel * 80 + (heel > 0 ? -2 : 2), cy + tdir[1] * heel * 80 - 8, "golfer", "muted", heel > 0 ? "end" : "start");
    // face normal arrow
    add(g1, "line", { x1: cx, y1: cy, x2: cx + nd[0] * L * 0.92, y2: cy + nd[1] * L * 0.92 }, "pv-arrow face");
    arrowHead(g1, cx + nd[0] * L * 0.92, cy + nd[1] * L * 0.92, Math.atan2(nd[1], nd[0]), 8, "pv-head face");
    add(g1, "circle", { cx, cy, r: 4 }, "pv-ball");
    // Labels in a short key at the left, colored like the arrows, so they never collide.
    label(g1, 6, 34, `path ${f1(pathD)}${DEG}`, "ink strong");
    label(g1, 6, 50, `face ${f1(faceD)}${DEG}`, "clay strong");
    // Lie and strike, when set, in the same key.
    const extras = [];
    if (Math.abs(lie) >= 0.05) extras.push(`lie ${Math.abs(lie).toFixed(1)}${DEG} toe ${lie > 0 ? "up" : "down"}`);
    if (Math.abs(strikeToe) >= 0.5) extras.push(`${Math.abs(Math.round(strikeToe))} mm ${strikeToe > 0 ? "toe" : "heel"}`);
    if (Math.abs(strikeUp) >= 0.5) extras.push(`${Math.abs(Math.round(strikeUp))} mm ${strikeUp > 0 ? "high" : "low"}`);
    extras.forEach((t, i) => label(g1, 6, 66 + 14 * i, t, "muted"));
    const cl = c.classification;
    const closed = f2pRh < -0.05, open = f2pRh > 0.05;
    const rel = Math.abs(f2pRh) < 0.05 ? "square to path" : `${Math.abs(f2pDisp).toFixed(1)}${DEG} ${closed ? "closed" : "open"} to path`;
    // A shot with almost no face-to-path has no bend to name, so no verb.
    const verb = cl && Math.abs(f2pRh) >= 0.5 ? VERB[cl.shape] || "" : "";
    // The caption wraps to two lines on a narrow panel.
    const caption = `face ${rel}`;
    const arrow = verb ? `→ ${verb}` : "";
    if ((caption.length + arrow.length + 1) * 7.3 > W - 10 && arrow) {
      label(g1, W / 2, half - 20, caption, "ink strong", "middle");
      label(g1, W / 2, half - 6, arrow, "ink strong", "middle");
    } else {
      label(g1, W / 2, half - 6, arrow ? `${caption} ${arrow}` : caption, "ink strong", "middle");
    }
    // The wedge is named where it is, with a leader line for the small ones.
    if (wedgeTip) {
      const lxp = Math.min(W - 6, cx + 34), lyp = Math.max(46, wedgeTip[1] + 4);
      add(g1, "line", { x1: wedgeTip[0], y1: wedgeTip[1], x2: lxp - 3, y2: lyp - 4 }, "pv-leader");
      const full = `${Math.abs(f2pDisp).toFixed(1)}${DEG} ${closed ? "closed" : "open"}`;
      // On a narrow panel the word goes and the number stays.
      label(g1, lxp, lyp, (W - 6 - lxp) >= full.length * 7.3 ? full : `${Math.abs(f2pDisp).toFixed(1)}${DEG}`, "clay strong");
    }

    // -- side view of the club and ball (lower half)
    const g2 = add(svg, "g", {});
    add(g2, "line", { x1: 8, x2: W - 8, y1: half + 4, y2: half + 4 }, "pv-grid");
    label(g2, 6, half + 20, "Side view", "muted");
    const sx0 = W / 2, sy0 = half + (H - half) * 0.5;
    add(g2, "line", { x1: 12, x2: W - 12, y1: sy0, y2: sy0 }, "pv-target");
    const atk = v.attack_deg.disp, loft = v.dyn_loft_deg.disp, spinLoft = v.spin_loft_deg.disp;
    const R2 = Math.min(56, W * 0.22);
    // spin loft wedge: from the path direction to the face normal
    add(g2, "path", { d: arcPath(sx0, sy0, R2 * 0.85, -loft * RAD, -atk * RAD, 1) }, "pv-wedge");
    // attack: the club approaches from behind, along the path direction
    const pv = [Math.cos(atk * RAD), -Math.sin(atk * RAD)];
    add(g2, "line", { x1: sx0 - pv[0] * R2 * 1.5, y1: sy0 - pv[1] * R2 * 1.5, x2: sx0, y2: sy0 }, "pv-arrow path");
    arrowHead(g2, sx0, sy0, Math.atan2(pv[1], pv[0]), 9, "pv-head path");
    // The slider's loft (face square to the path) as a faint reference when the face has moved the effective loft off it.
    const inputLoft = v.dyn_loft_deg.input;
    const moved = inputLoft !== undefined && Math.abs(inputLoft - loft) > 0.05;
    if (moved) {
      const rd = [Math.sin(inputLoft * RAD), Math.cos(inputLoft * RAD)];
      add(g2, "line", { x1: sx0 - rd[0] * 38, y1: sy0 - rd[1] * 38, x2: sx0 + rd[0] * 30, y2: sy0 + rd[1] * 30 }, "pv-ref");
    }
    // face: tilted back by the effective dynamic loft
    const fd = [Math.sin(loft * RAD), Math.cos(loft * RAD)];
    add(g2, "line", { x1: sx0 - fd[0] * 38, y1: sy0 - fd[1] * 38, x2: sx0 + fd[0] * 30, y2: sy0 + fd[1] * 30 }, "pv-face");
    // The strike point up or down the face: 38 px of the upper half stands for about 30 mm.
    if (struck) {
      const offUp = -strikeUp * 1.1;
      add(g2, "circle", { cx: sx0 + fd[0] * offUp, cy: sy0 + fd[1] * offUp, r: 3.2 }, "pv-strike");
    }
    const nv = [Math.cos(loft * RAD), -Math.sin(loft * RAD)];
    add(g2, "line", { x1: sx0, y1: sy0, x2: sx0 + nv[0] * R2 * 1.05, y2: sy0 + nv[1] * R2 * 1.05 }, "pv-arrow face");
    arrowHead(g2, sx0 + nv[0] * R2 * 1.05, sy0 + nv[1] * R2 * 1.05, Math.atan2(nv[1], nv[0]), 8, "pv-head face");
    add(g2, "circle", { cx: sx0, cy: sy0, r: 4 }, "pv-ball");
    label(g2, 6, sy0 + 20, `attack ${f1(atk)}${DEG}`, "ink strong");
    label(g2, W - 6, sy0 + 20, `loft ${loft.toFixed(1)}${DEG}`, "clay strong", "end");
    if (moved) label(g2, W - 6, sy0 + 35, `set ${inputLoft.toFixed(1)}${DEG}`, "muted", "end");
    const slText = `spin loft ${spinLoft.toFixed(1)}${DEG}`, slNote = "(3D)";
    if ((slText.length + slNote.length + 1) * 7.3 > W - 10) {
      label(g2, W / 2, H - 20, slText, "ink strong", "middle");
      label(g2, W / 2, H - 6, slNote, "muted", "middle");
    } else {
      label(g2, W / 2, H - 6, `${slText} ${slNote}`, "ink strong", "middle");
    }
    const extraText = extras.length ? ` ${extras.map((t) => t.replace(DEG, " degrees")).join(", ")}.` : "";
    svg.setAttribute("aria-label", `Impact diagram. Club path ${f1(pathD)} degrees, face angle ${f1(faceD)} degrees, face ${rel}${verb ? ", so the ball " + verb : ""}. Attack angle ${f1(atk)} degrees, dynamic loft ${loft.toFixed(1)} degrees, spin loft ${spinLoft.toFixed(1)} degrees.${extraText}`);
  }

  function redraw() {
    if (!last) return;
    drawTop(panels.top, last);
    drawSide(panels.side, last);
    drawImpact(panels.impact, last);
  }

  const ro = new ResizeObserver(() => redraw());
  for (const name in panels) ro.observe(panels[name].host);

  /**
   * c: {shot (range shot, display frame), ghost, pinned (range shots or null),
   *     values, classification, hand}
   */
  function update(c) {
    last = c;
    redraw();
  }

  return { update, redraw };
}
