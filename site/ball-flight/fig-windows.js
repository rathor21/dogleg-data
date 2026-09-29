/* Figure 5: the model's nine 7-iron recipes as small multiples, side profile above and top-down below. */
import { nineWindows } from "./article-data.js";
import { svg, html, sgn, grp, tokens, mountResponsive, fillTable, legendItem } from "./article-svg.js";

export function drawWindows(fig, model) {
  const T = tokens();
  const W = nineWindows(model);
  const plot = fig.querySelector(".fig-plot");
  fig.querySelector("[data-legend]").replaceChildren(
    legendItem("dot", T.clay, "Apex"), legendItem("ring", T.ink, "Landing"), legendItem("dash", T.soft, "Target line"));

  fillTable(fig.querySelector(".fig-table"),
    ["Window", "Path (deg)", "Face (deg)", "Face-to-path (deg)", "Attack angle (deg)", "Dynamic loft (deg)", "Launch (deg)", "Spin (rpm)", "Carry (yd)", "Peak height (yd)", "Curve (yd)", "Model's name"],
    W.map((n) => {
      const d = n.delivery, s = n.shot;
      return [n.label, sgn(d.path, 1), sgn(d.face, 1), sgn(d.face - d.path, 1), sgn(d.attack, 1), d.dynLoft.toFixed(1), s.launch.launchDeg.toFixed(1), grp(s.launch.spinRpm), s.flight.carry.toFixed(0), s.flight.maxHeight.toFixed(0), sgn(s.flight.curve, 1), s.classification.name];
    }),
    "Tour 7-iron at 92 mph, PGA Tour preset. Dogleg Data model output. Tiger Woods did not publish these numbers.");

  // Geometry in yards, drawn in a fixed 200 by 216 box and scaled by CSS.
  const XMAX = 200, SIDE_H = 100, VS = 2, LS = 5, LAT = 8;
  const topBase = SIDE_H + 14 + LAT * LS;
  const VB_H = SIDE_H + 14 + 2 * LAT * LS;

  mountResponsive(plot, (w) => {
    const grid = html("div", { class: "win-grid" });
    W.forEach((n) => {
      const f = n.shot.flight;
      const step = 4;
      const side = [], top = [];
      for (let i = 0; i < f.x.length; i += step) {
        side.push(`${f.x[i].toFixed(1)} ${(SIDE_H - f.z[i] * VS).toFixed(1)}`);
        top.push(`${f.x[i].toFixed(1)} ${(topBase + f.y[i] * LS).toFixed(1)}`);
      }
      const last = f.x.length - 1;
      side.push(`${f.x[last].toFixed(1)} ${(SIDE_H - f.z[last] * VS).toFixed(1)}`);
      top.push(`${f.x[last].toFixed(1)} ${(topBase + f.y[last] * LS).toFixed(1)}`);
      let apexI = 0;
      for (let i = 0; i < f.z.length; i++) if (f.z[i] > f.z[apexI]) apexI = i;
      const name = `${n.label}: ${f.carry.toFixed(0)} yards carry, ${f.maxHeight.toFixed(0)} yards high, ${Math.abs(f.curve).toFixed(0)} yards of ${f.curve < 0 ? "draw" : f.curve > 0 ? "fade" : "curve"}`;
      const s = svg("svg", { viewBox: `-4 -6 ${XMAX + 12} ${VB_H + 12}`, role: "img", "aria-label": name, preserveAspectRatio: "xMidYMid meet" });
      // side profile
      s.append(svg("line", { x1: 0, x2: XMAX, y1: SIDE_H, y2: SIDE_H, stroke: T.soft, "stroke-width": 1, "vector-effect": "non-scaling-stroke" }));
      s.append(svg("polyline", { points: side.join(" "), fill: "none", stroke: T.ink, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round", "vector-effect": "non-scaling-stroke" }));
      s.append(svg("circle", { cx: f.x[apexI], cy: SIDE_H - f.z[apexI] * VS, r: 3.6, fill: T.clay }));
      s.append(svg("circle", { cx: f.x[last], cy: SIDE_H, r: 3.4, fill: T.card, stroke: T.ink, "stroke-width": 1.6, "vector-effect": "non-scaling-stroke" }));
      // top-down
      s.append(svg("line", { x1: 0, x2: XMAX, y1: topBase, y2: topBase, stroke: T.soft, "stroke-width": 1, "stroke-dasharray": "4 3", "vector-effect": "non-scaling-stroke" }));
      s.append(svg("polyline", { points: top.join(" "), fill: "none", stroke: T.ink, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round", "vector-effect": "non-scaling-stroke" }));
      s.append(svg("circle", { cx: f.x[last], cy: topBase + f.y[last] * LS, r: 3.4, fill: T.card, stroke: T.ink, "stroke-width": 1.6, "vector-effect": "non-scaling-stroke" }));
      const d = n.delivery;
      grid.append(html("div", { class: "win" }, s,
        html("div", { class: "win-name" }, n.label),
        html("div", { class: "win-nums" }, `${f.carry.toFixed(0)} yd, ${f.maxHeight.toFixed(0)} high`),
        html("div", { class: "win-recipe" }, `Path ${sgn(d.path, 1)} · Face ${sgn(d.face, 1)} · AoA ${sgn(d.attack, 1)} · Loft ${d.dynLoft.toFixed(1)}`)));
    });
    plot.replaceChildren(grid);
  });
}
