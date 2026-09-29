/* Figure 3: Tour driver launch and spin against attack angle at fixed dynamic loft, with the two optimizer charts. */
import { attackSweep } from "./article-data.js";
import { svg, html, sgn, grp, scaleLin, ticks, tokens, mountResponsive, tip, centerOf, fillTable, legendItem } from "./article-svg.js";

export function drawAttack(fig, model) {
  const T = tokens();
  const S = attackSweep(model);
  const rows = S.rows;
  const plot = fig.querySelector(".fig-plot");
  fig.querySelector("[data-legend]").replaceChildren(
    legendItem("line", T.ink, "Model, inside the fitted spin loft"),
    legendItem("dotted", T.ink, "Model, below the fit"),
    legendItem("square", T.blue, "TrackMan 2010, carry optimizer"),
    legendItem("diamond", T.clay, "PING 2019"),
    legendItem("ring", T.ink, "Tour average"));

  fillTable(fig.querySelector(".fig-table"),
    ["Attack angle (deg)", "Spin loft (deg)", "Model launch (deg)", "Model spin (rpm)", "TrackMan 2010 launch (deg)", "TrackMan 2010 spin (rpm)", "PING 2019 launch (deg)", "PING 2019 spin (rpm)", "Model carry (yd)"],
    rows.map((r) => [sgn(r.attack, 0), r.spinLoft.toFixed(1) + (r.extrapolated ? " *" : ""), r.launch.toFixed(1), grp(r.spin),
      r.tm ? r.tm.launch.toFixed(1) : "n/a", r.tm ? grp(r.tm.spin) : "n/a", r.ping.launch.toFixed(1), grp(r.ping.spin), r.carry.toFixed(0)]),
    `Dynamic loft ${S.dynLoft.toFixed(1)} degrees and club speed ${S.clubSpeed} mph throughout. * marks spin loft below ${S.floor.toFixed(1)} degrees, the lowest value in the launch fit. TrackMan's chart covers attack angles from -5 to +5. PING's chart lookup uses the model's ball speed at each row.`);

  const panels = [
    { id: "launch", title: "Launch angle, degrees", get: (r) => r.launch, tm: (r) => r.tm && r.tm.launch, ping: (r) => r.ping.launch, avg: S.tour.launch_deg, dom: [6, 16], ticks: [6, 8, 10, 12, 14, 16], fmt: (v) => v.toFixed(1), unit: "°" },
    { id: "spin", title: "Spin rate, rpm", get: (r) => r.spin, tm: (r) => r.tm && r.tm.spin, ping: (r) => r.ping.spin, avg: S.tour.spin_rpm, dom: [500, 4000], ticks: [1000, 2000, 3000, 4000], fmt: grp, unit: " rpm" },
  ];

  mountResponsive(plot, (w) => {
    const stacked = w < 640;
    const pw = stacked ? w : Math.floor((w - 24) / 2);
    const H = 236;
    const m = { l: stacked ? 44 : 44, r: 12, t: 26, b: 34 };
    const wrap = html("div", { class: "fig-panels" });
    const drawn = [];
    panels.forEach((P, pi) => {
      const x = scaleLin(-6, 6, m.l, pw - m.r);
      const y = scaleLin(P.dom[1], P.dom[0], m.t, H - m.b);
      const root = svg("svg", { width: pw, height: H, viewBox: `0 0 ${pw} ${H}`, role: "img", "aria-labelledby": `fig3-${P.id}-t fig3-${P.id}-d` });
      root.append(svg("title", { id: `fig3-${P.id}-t` }, `Driver ${P.title.toLowerCase()} against attack angle`),
        svg("desc", { id: `fig3-${P.id}-d` }, P.id === "launch"
          ? `Launch angle rises from ${rows[0].launch.toFixed(1)} to ${rows[rows.length - 1].launch.toFixed(1)} degrees as attack angle goes from minus 6 to plus 6 at fixed loft. Two optimizer charts are drawn for comparison.`
          : `Spin falls from ${grp(rows[0].spin)} to ${grp(rows[rows.length - 1].spin)} rpm as attack angle goes from minus 6 to plus 6 at fixed loft, and runs under both optimizer charts at positive attack angles.`));
      root.append(svg("text", { x: 2, y: 14, fill: T.ink, "font-family": T.sans, "font-size": 13, "font-weight": 600 }, P.title));
      for (const t of P.ticks) {
        root.append(svg("line", { x1: m.l, x2: pw - m.r, y1: y(t), y2: y(t), stroke: T.line, "stroke-width": 1 }));
        root.append(svg("text", { x: m.l - 6, y: y(t) + 4, "text-anchor": "end", fill: T.soft, "font-family": T.mono, "font-size": 11 }, P.id === "spin" ? grp(t) : String(t)));
      }
      for (const t of ticks(-6, 6, 2)) {
        root.append(svg("line", { x1: x(t), x2: x(t), y1: m.t, y2: H - m.b, stroke: t === 0 ? T.soft : "none", "stroke-width": 1 }));
        root.append(svg("text", { x: x(t), y: H - m.b + 16, "text-anchor": "middle", fill: T.soft, "font-family": T.mono, "font-size": 11 }, t === 0 ? "0" : sgn(t, 0)));
      }
      root.append(svg("text", { x: m.l, y: H - 4, fill: T.soft, "font-family": T.mono, "font-size": 11 }, "attack angle, degrees (down −, up +)"));

      const path = (pick, from, to) => rows.filter((r) => r.attack >= from && r.attack <= to && pick(r) != null)
        .map((r, i) => `${i ? "L" : "M"}${x(r.attack).toFixed(1)} ${y(pick(r)).toFixed(1)}`).join("");
      // Optimizer lines and markers.
      root.append(svg("path", { d: path(P.tm, -5, 5), fill: "none", stroke: T.blue, "stroke-width": 1.5, "stroke-linejoin": "round", "pointer-events": "none" }));
      root.append(svg("path", { d: path(P.ping, -6, 6), fill: "none", stroke: T.clay, "stroke-width": 1.5, "stroke-linejoin": "round", "pointer-events": "none" }));
      for (const r of rows) {
        if (r.tm && r.attack % 5 === 0) root.append(svg("rect", { x: x(r.attack) - 4, y: y(P.tm(r)) - 4, width: 8, height: 8, fill: T.blue, stroke: T.card, "stroke-width": 2, "pointer-events": "none" }));
        if (r.attack % 2 === 0) root.append(svg("path", { d: `M${x(r.attack)} ${y(P.ping(r)) - 5}L${x(r.attack) + 5} ${y(P.ping(r))}L${x(r.attack)} ${y(P.ping(r)) + 5}L${x(r.attack) - 5} ${y(P.ping(r))}Z`, fill: T.clay, stroke: T.card, "stroke-width": 1.5, "pointer-events": "none" }));
      }
      // Model line: solid inside the fit, dotted below its spin loft floor.
      const inside = rows.filter((r) => !r.extrapolated), outside = rows.filter((r) => r.extrapolated);
      const lastIn = inside[inside.length - 1];
      root.append(svg("path", { d: path(P.get, -6, lastIn.attack), fill: "none", stroke: T.ink, "stroke-width": 2, "stroke-linecap": "round", "stroke-linejoin": "round", "pointer-events": "none" }));
      if (outside.length) root.append(svg("path", { d: path(P.get, lastIn.attack, 6), fill: "none", stroke: T.ink, "stroke-width": 2, "stroke-linecap": "round", "stroke-dasharray": "1 4", "pointer-events": "none" }));
      // Tour average and end labels for the model line.
      root.append(svg("circle", { cx: x(-0.9), cy: y(P.avg), r: 5, fill: T.card, stroke: T.ink, "stroke-width": 2, "pointer-events": "none" }));
      const first = rows[0], last = rows[rows.length - 1];
      root.append(svg("text", { x: x(first.attack) + 2, y: y(P.get(first)) - 10, fill: T.ink, "font-family": T.mono, "font-size": 12, "font-weight": 500 }, P.fmt(P.get(first)) + (P.id === "launch" ? "°" : "")));
      root.append(svg("text", { x: x(last.attack) - 2, y: y(P.get(last)) + 18, "text-anchor": "end", fill: T.ink, "font-family": T.mono, "font-size": 12, "font-weight": 500 }, P.fmt(P.get(last)) + (P.id === "launch" ? "°" : "")));

      // Crosshair snapped to whole degrees of attack angle.
      const cross = svg("g", { "pointer-events": "none", visibility: "hidden" });
      const vline = svg("line", { y1: m.t, y2: H - m.b, stroke: T.ink, "stroke-width": 1, "stroke-dasharray": "2 3" });
      const cdot = svg("circle", { r: 4, fill: T.ink, stroke: T.card, "stroke-width": 2 });
      cross.append(vline, cdot);
      let idx = null;
      const setIdx = (i, cx, cy) => {
        idx = Math.max(0, Math.min(rows.length - 1, i));
        const r = rows[idx];
        vline.setAttribute("x1", x(r.attack)); vline.setAttribute("x2", x(r.attack));
        cdot.setAttribute("cx", x(r.attack)); cdot.setAttribute("cy", y(P.get(r)));
        cross.setAttribute("visibility", "visible");
        const tr = [{ key: T.ink, dash: r.extrapolated, value: P.fmt(P.get(r)) + P.unit, label: `model, spin loft ${r.spinLoft.toFixed(1)}°${r.extrapolated ? " (below the fit)" : ""}` }];
        if (P.tm(r) != null) tr.push({ key: T.blue, value: P.fmt(P.tm(r)) + P.unit, label: "TrackMan 2010" });
        tr.push({ key: T.clay, value: P.fmt(P.ping(r)) + P.unit, label: "PING 2019" });
        tip.show({ heading: `Attack angle ${sgn(r.attack, 0)}°`, rows: tr }, cx, cy);
      };
      const hide = () => { cross.setAttribute("visibility", "hidden"); tip.hide(); };
      const overlay = svg("rect", { x: m.l, y: m.t, width: pw - m.l - m.r, height: H - m.t - m.b, fill: "transparent", tabindex: 0, role: "group",
        "aria-label": `${P.title} by attack angle. Use the left and right arrow keys to step through the values.` });
      overlay.addEventListener("pointermove", (e) => {
        const r = overlay.getBoundingClientRect();
        setIdx(Math.round(((e.clientX - r.left) / r.width) * 12), e.clientX, e.clientY);
      });
      overlay.addEventListener("pointerleave", hide);
      overlay.addEventListener("blur", hide);
      overlay.addEventListener("focus", () => { const [a, b] = centerOf(overlay); setIdx(idx === null ? 6 : idx, a, b); });
      overlay.addEventListener("keydown", (e) => {
        if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
        e.preventDefault();
        const [a, b] = centerOf(overlay);
        setIdx((idx === null ? 6 : idx) + (e.key === "ArrowRight" ? 1 : -1), a, b);
      });
      root.append(overlay, cross);
      wrap.append(root);
    });
    wrap.style.display = "grid";
    wrap.style.gridTemplateColumns = stacked ? "1fr" : "1fr 1fr";
    wrap.style.gap = stacked ? "14px" : "24px";
    plot.replaceChildren(wrap);
  });
}
