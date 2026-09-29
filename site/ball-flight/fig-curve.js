/* Figure 2: curve against face-to-path for three clubs, with TrackMan's eight published examples as dots. */
import { curveLines, exampleCheck, CLUB_LABEL } from "./article-data.js";
import { svg, sgn, MINUS, scaleLin, ticks, tokens, mountResponsive, tip, centerOf, fillTable, legendItem } from "./article-svg.js";

export function drawCurve(fig, model) {
  const T = tokens();
  const lines = curveLines(model);
  const ex = exampleCheck(model);
  const color = { driver: T.ink, "6i": T.clay, pw: T.blue };
  const plot = fig.querySelector(".fig-plot");
  fig.querySelector("[data-legend]").replaceChildren(
    legendItem("line", T.ink, "Driver"), legendItem("line", T.clay, "6-iron"), legendItem("line", T.blue, "PW"),
    legendItem("line", T.soft, "PGA Tour preset"), legendItem("dash", T.soft, "LPGA Tour preset"),
    legendItem("dot", T.soft, "TrackMan example, PGA"), legendItem("ring", T.soft, "TrackMan example, LPGA"));

  const fs = lines[0].pts.map((p) => p.f2p);
  fillTable(fig.querySelector(".fig-table"),
    ["Face-to-path (deg)", ...lines.map((l) => `${l.player === "lpga" ? "LPGA " : "PGA "}${CLUB_LABEL[l.club]} curve (yd)`)],
    fs.map((f, i) => [sgn(f, 1), ...lines.map((l) => sgn(l.pts[i].curve, 1))]),
    "Curve in yards, right positive, at path 0. TrackMan's published examples: " +
      ex.map((e) => `${e.tour.toUpperCase()} ${CLUB_LABEL[e.club]} at ${sgn(e.f2p, 0)} degrees, ${Math.abs(e.curve)} yd ${e.curve < 0 ? "left" : "right"} (preset line ${sgn(e.model, 1)})`).join("; ") + ".");

  mountResponsive(plot, (w) => {
    const narrow = w < 480;
    const m = { l: 40, r: narrow ? 46 : 60, t: 28, b: 40 };
    const H = narrow ? 300 : 360;
    const x = scaleLin(-6, 6, m.l, w - m.r);
    const y = scaleLin(55, -55, m.t, H - m.b);
    const root = svg("svg", { width: w, height: H, viewBox: `0 0 ${w} ${H}`, role: "group", "aria-labelledby": "fig2-t fig2-d" });
    root.append(svg("title", { id: "fig2-t" }, "Curve against face-to-path for the driver, 6-iron and wedge"),
      svg("desc", { id: "fig2-d" }, "Line chart from minus 6 to plus 6 degrees of face-to-path. The driver curves most, up to about 50 yards at 6 degrees. The 6-iron reaches about 30 yards and the wedge about 9. Dots mark TrackMan's eight published examples. The data table lists every value."));

    for (const t of ticks(-50, 50, 25)) {
      root.append(svg("line", { x1: m.l, x2: w - m.r, y1: y(t), y2: y(t), stroke: t === 0 ? T.soft : T.line, "stroke-width": 1 }));
      root.append(svg("text", { x: m.l - 6, y: y(t) + 4, "text-anchor": "end", fill: T.soft, "font-family": T.mono, "font-size": 11 }, t === 0 ? "0" : sgn(t, 0)));
    }
    for (const t of ticks(-6, 6, 2)) {
      root.append(svg("line", { x1: x(t), x2: x(t), y1: m.t, y2: H - m.b, stroke: t === 0 ? T.soft : T.line, "stroke-width": 1 }));
      root.append(svg("text", { x: x(t), y: H - m.b + 16, "text-anchor": "middle", fill: T.soft, "font-family": T.mono, "font-size": 11 }, t === 0 ? "0" : sgn(t, 0)));
    }
    root.append(svg("text", { x: m.l, y: H - 6, fill: T.soft, "font-family": T.mono, "font-size": 11 }, "face-to-path, degrees (face minus path)"));
    root.append(svg("text", { x: m.l + 4, y: m.t - 12, fill: T.soft, "font-family": T.mono, "font-size": 11 }, `curve, yd (left ${MINUS}, right +)`));

    // Lines. LPGA first so the PGA lines sit on top.
    const drawn = [...lines].sort((a, b) => (a.player === "lpga" ? -1 : 1) - (b.player === "lpga" ? -1 : 1));
    for (const l of drawn) {
      const d = l.pts.map((p, i) => `${i ? "L" : "M"}${x(p.f2p).toFixed(1)} ${y(p.curve).toFixed(1)}`).join("");
      root.append(svg("path", { d, fill: "none", stroke: color[l.club], "stroke-width": l.dash ? 1.5 : 2, "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-dasharray": l.dash ? "5 4" : null, "pointer-events": "none" }));
    }
    // Direct labels on the PGA lines, at the right end.
    for (const l of lines.filter((q) => q.player === "pga")) {
      const p = l.pts[l.pts.length - 1];
      root.append(svg("text", { x: x(p.f2p) + 6, y: y(p.curve) + 4, fill: T.ink, "font-family": T.sans, "font-size": 12, "font-weight": 500 }, l.label));
    }

    // Crosshair layer.
    const cross = svg("g", { "pointer-events": "none" });
    const vline = svg("line", { y1: m.t, y2: H - m.b, stroke: T.ink, "stroke-width": 1, "stroke-dasharray": "2 3" });
    const dots = lines.map((l) => svg("circle", { r: 4, fill: color[l.club], stroke: T.card, "stroke-width": 2 }));
    cross.append(vline, ...dots);
    cross.setAttribute("visibility", "hidden");
    let idx = null;
    const setIdx = (i, cx, cy) => {
      idx = Math.max(0, Math.min(fs.length - 1, i));
      const f = fs[idx];
      vline.setAttribute("x1", x(f)); vline.setAttribute("x2", x(f));
      lines.forEach((l, k) => { dots[k].setAttribute("cx", x(f)); dots[k].setAttribute("cy", y(l.pts[idx].curve)); });
      cross.setAttribute("visibility", "visible");
      tip.show({
        heading: `Face-to-path ${sgn(f, 1)}°`,
        rows: lines.map((l) => ({ key: color[l.club], dash: l.dash, value: `${Math.abs(l.pts[idx].curve).toFixed(1)} yd ${l.pts[idx].curve < 0 ? "left" : l.pts[idx].curve > 0 ? "right" : ""}`.trim(), label: l.player === "lpga" ? l.label : `PGA ${l.label}` })),
      }, cx, cy);
    };
    const hideAll = () => { cross.setAttribute("visibility", "hidden"); tip.hide(); };
    const overlay = svg("rect", { x: m.l, y: m.t, width: w - m.l - m.r, height: H - m.t - m.b, fill: "transparent", tabindex: 0, role: "group",
      "aria-label": "Curve by face-to-path. Use the left and right arrow keys to move along the axis and read each line." });
    overlay.addEventListener("pointermove", (e) => {
      const r = overlay.getBoundingClientRect();
      const f = -6 + ((e.clientX - r.left) / r.width) * 12;
      setIdx(Math.round((f + 6) / 0.5), e.clientX, e.clientY);
    });
    overlay.addEventListener("pointerleave", hideAll);
    overlay.addEventListener("blur", hideAll);
    overlay.addEventListener("focus", () => { const [a, b] = centerOf(overlay); setIdx(idx === null ? 12 : idx, a, b); });
    overlay.addEventListener("keydown", (e) => {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      e.preventDefault();
      const [a, b] = centerOf(overlay);
      setIdx((idx === null ? 12 : idx) + (e.key === "ArrowRight" ? 1 : -1), a, b);
    });
    root.append(overlay, cross);

    // TrackMan's eight examples, on top of the overlay so they take their own hover.
    for (const e of ex) {
      const c = color[e.club];
      const label = `TrackMan example: ${e.tour.toUpperCase()} ${CLUB_LABEL[e.club]}, face-to-path ${sgn(e.f2p, 0)} degrees, ${Math.abs(e.curve)} yards ${e.curve < 0 ? "left" : "right"}. Preset line reads ${sgn(e.model, 1)} yards.`;
      const g = svg("g", { class: "hit", tabindex: 0, role: "img", "aria-label": label });
      g.append(svg("circle", { cx: x(e.f2p), cy: y(e.curve), r: 14, fill: "transparent" }));
      g.append(e.tour === "pga"
        ? svg("circle", { cx: x(e.f2p), cy: y(e.curve), r: 5, fill: c, stroke: T.card, "stroke-width": 2, class: "mark" })
        : svg("circle", { cx: x(e.f2p), cy: y(e.curve), r: 5, fill: T.card, stroke: c, "stroke-width": 2, class: "mark" }));
      const show = (cx, cy) => { cross.setAttribute("visibility", "hidden"); tip.show({
        heading: `TrackMan example, ${e.tour.toUpperCase()} ${CLUB_LABEL[e.club]}`,
        rows: [{ value: `${Math.abs(e.curve)} yd ${e.curve < 0 ? "left" : "right"}`, label: `published at ${sgn(e.f2p, 0)}° face-to-path` },
          { value: `${Math.abs(e.model).toFixed(1)} yd ${e.model < 0 ? "left" : "right"}`, label: "model preset line" }],
      }, cx, cy); };
      g.addEventListener("pointermove", (ev) => { ev.stopPropagation(); show(ev.clientX, ev.clientY); });
      g.addEventListener("pointerleave", () => tip.hide());
      g.addEventListener("focus", () => { const [a, b] = centerOf(g); show(a, b); });
      g.addEventListener("blur", () => tip.hide());
      root.append(g);
    }
    plot.replaceChildren(root);
  });
}
