/*
 * Small SVG and DOM helpers shared by the article figures (release 004).
 * Vanilla, no dependencies. Figures draw at the pixel width of their
 * container and redraw when it changes, so type stays at its CSS size on a
 * 375 px phone and on a wide desktop.
 */

export const NS = "http://www.w3.org/2000/svg";
export const MINUS = "−";

/** Create an SVG element. Kids can be nodes, strings or arrays of them. */
export function svg(tag, attrs = {}, ...kids) {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v !== null && v !== undefined) n.setAttribute(k, String(v));
  for (const c of kids.flat()) if (c !== null && c !== undefined) n.append(c);
  return n;
}

/** Create an HTML element. Same kids rule. Text goes in as text, never as markup. */
export function html(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined) continue;
    if (k === "class") n.className = v;
    else n.setAttribute(k, String(v));
  }
  for (const c of kids.flat()) if (c !== null && c !== undefined) n.append(c);
  return n;
}

/** Signed number with a true minus sign. Zero prints without a sign. */
export function sgn(v, dp = 1) {
  const r = Number(Math.abs(v).toFixed(dp));
  return (r === 0 ? "" : v < 0 ? MINUS : "+") + r.toFixed(dp);
}

export const grp = (v) => Math.round(v).toLocaleString("en-US");

export const scaleLin = (d0, d1, r0, r1) => (v) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);

/** Nice tick list from lo to hi in steps of `step`. */
export function ticks(lo, hi, step) {
  const out = [];
  for (let v = Math.ceil(lo / step - 1e-9) * step; v <= hi + 1e-9; v += step) out.push(Math.abs(v) < 1e-9 ? 0 : v);
  return out;
}

/** Design tokens read from the page's CSS custom properties (site.css). */
export function tokens() {
  const cs = getComputedStyle(document.documentElement);
  const g = (n) => cs.getPropertyValue(n).trim();
  return {
    card: g("--card"), line: g("--line"), ink: g("--ink"), soft: g("--ink-soft"), muted: g("--muted"),
    clay: g("--clay"), clayText: g("--clay-text"), blue: g("--blue"), blueText: g("--blue-text"), maroon: g("--maroon"),
    mono: g("--mono"), sans: g("--sans"),
  };
}

/** Draw into `container` at its pixel width, and again whenever that width changes. */
export function mountResponsive(container, draw) {
  let last = 0;
  const run = () => {
    const w = Math.floor(container.clientWidth);
    if (w < 120 || w === last) return;
    last = w;
    draw(w);
  };
  if (typeof ResizeObserver === "function") new ResizeObserver(run).observe(container);
  else window.addEventListener("resize", run);
  run();
}

/** Bar with a 4 px rounded data end and a square baseline end. Works left or right of the baseline. */
export function roundedBar(x0, x1, y, h, r = 4) {
  const dir = x1 >= x0 ? 1 : -1;
  const len = Math.abs(x1 - x0);
  const rr = Math.min(r, len, h / 2);
  const e = x1;
  const sweep = dir > 0 ? 1 : 0;
  return `M${x0} ${y}H${e - dir * rr}A${rr} ${rr} 0 0 ${sweep} ${e} ${y + rr}V${y + h - rr}A${rr} ${rr} 0 0 ${sweep} ${e - dir * rr} ${y + h}H${x0}Z`;
}

/* ---------- tooltip: one shared element, filled with text nodes only ---------- */

let tipEl = null;
function tipNode() {
  if (!tipEl) {
    tipEl = html("div", { class: "fig-tip", role: "presentation" });
    tipEl.hidden = true;
    document.body.append(tipEl);
  }
  return tipEl;
}

export const tip = {
  /** rows: [{key?: color, dash?: boolean, label, value}] and an optional heading. Position in client coordinates. */
  show({ heading, rows }, clientX, clientY) {
    const el = tipNode();
    el.replaceChildren();
    if (heading) el.append(html("div", { class: "tip-head" }, heading));
    for (const r of rows) {
      const line = html("div", { class: "tip-row" });
      if (r.key) {
        const sw = svg("svg", { class: "tip-key", width: 16, height: 8, viewBox: "0 0 16 8", "aria-hidden": "true" },
          svg("line", { x1: 0, x2: 16, y1: 4, y2: 4, stroke: r.key, "stroke-width": 2, "stroke-dasharray": r.dash ? "4 3" : null }));
        line.append(sw);
      }
      line.append(html("span", { class: "tip-val" }, r.value), html("span", { class: "tip-lab" }, r.label));
      el.append(line);
    }
    el.hidden = false;
    const pad = 12;
    const w = el.offsetWidth, h = el.offsetHeight;
    let x = clientX + pad, y = clientY + pad;
    if (x + w > window.innerWidth - 8) x = clientX - w - pad;
    if (x < 8) x = 8;
    if (y + h > window.innerHeight - 8) y = clientY - h - pad;
    if (y < 8) y = 8;
    el.style.left = `${x}px`;
    el.style.top = `${y}px`;
  },
  hide() {
    if (tipEl) tipEl.hidden = true;
  },
};

/** Client position of the middle of an element, for keyboard focus tooltips. */
export function centerOf(node) {
  const r = node.getBoundingClientRect();
  return [r.left + r.width / 2, r.top + r.height / 2];
}

/** Fill a <details class="fig-table"> body with a table. rows are arrays of strings or nodes. */
export function fillTable(details, headers, rows, note) {
  const body = details.querySelector(".fig-table-body");
  const table = html("table", { class: "data" },
    html("thead", {}, html("tr", {}, headers.map((h, i) => html("th", { scope: "col", class: i === 0 ? "l" : "r" }, h)))),
    html("tbody", {}, rows.map((r) => html("tr", {}, r.map((c, i) => html(i === 0 ? "th" : "td", i === 0 ? { scope: "row", class: "l" } : { class: "r" }, c))))),
  );
  body.replaceChildren(html("div", { class: "tbl-wrap" }, table));
  if (note) body.append(html("p", { class: "tbl-note" }, note));
}

/** A legend key: a short line or a marker beside text. kind: line | dash | dot | ring | square | diamond | bar */
export function legendItem(kind, color, text) {
  const s = svg("svg", { width: 22, height: 12, viewBox: "0 0 22 12", "aria-hidden": "true" });
  if (kind === "line" || kind === "dash" || kind === "dotted") {
    s.append(svg("line", { x1: 1, x2: 21, y1: 6, y2: 6, stroke: color, "stroke-width": 2, "stroke-linecap": "round", "stroke-dasharray": kind === "dash" ? "5 3" : kind === "dotted" ? "1 3" : null }));
  } else if (kind === "dot") s.append(svg("circle", { cx: 11, cy: 6, r: 4.5, fill: color }));
  else if (kind === "ring") s.append(svg("circle", { cx: 11, cy: 6, r: 4, fill: "none", stroke: color, "stroke-width": 2 }));
  else if (kind === "square") s.append(svg("rect", { x: 7, y: 2, width: 8, height: 8, fill: color }));
  else if (kind === "diamond") s.append(svg("path", { d: "M11 1L16 6L11 11L6 6Z", fill: color }));
  else if (kind === "bar") s.append(svg("rect", { x: 1, y: 3, width: 20, height: 6, rx: 3, fill: color }));
  return html("span", { class: "legend-item" }, s, html("span", {}, text));
}
