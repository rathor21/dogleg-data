/*
 * Figure 3: Tour driver launch and spin against attack angle at fixed dynamic loft.
 * Spin is drawn with the preset's spin trim and without it. Both are dotted where the spin loft
 * leaves the range the driver law was calibrated on (TrackMan's 2010 chart, 6.3 to 23.2 degrees),
 * and that region is shaded and labeled "extrapolated".
 */
import { attackSweep } from "./article-data.js";
import { svg, html, sgn, grp, scaleLin, ticks, tokens, mountResponsive, tip, centerOf, fillTable, legendItem } from "./article-svg.js";

export function drawAttack(fig, model) {
  const T = tokens();
  const S = attackSweep(model);
  const rows = S.rows;
  const plot = fig.querySelector(".fig-plot");
  fig.querySelector("[data-legend]").replaceChildren(
    legendItem("line", T.ink, `Model, tour spin trim ${S.spinTrim.toFixed(2)}`),
    legendItem("line", T.muted, "Model, no trim"),
    legendItem("dotted", T.ink, "Dotted: extrapolated"),
    legendItem("square", T.blue, "TrackMan 2010 carry chart"),
    legendItem("diamond", T.clay, "PING 2019"),
    legendItem("ring", T.ink, "Tour average"));

  fillTable(fig.querySelector(".fig-table"),
    ["Attack angle (deg)", "Spin loft (deg)", "Model launch (deg)", "Model spin, trimmed (rpm)", "Model spin, no trim (rpm)", "TrackMan 2010 launch (deg)", "TrackMan 2010 spin (rpm)", "PING 2019 launch (deg)", "PING 2019 spin (rpm)", "Model carry (yd)"],
    rows.map((r) => [sgn(r.attack, 0), r.spinLoft.toFixed(1) + (r.extrapolated ? " *" : ""), r.launch.toFixed(1), grp(r.spin), grp(r.spinUntrimmed),
      r.tm ? r.tm.launch.toFixed(1) : "n/a", r.tm ? grp(r.tm.spin) : "n/a", r.ping.launch.toFixed(1), grp(r.ping.spin), r.carry.toFixed(0)]),
    `Dynamic loft ${S.dynLoft.toFixed(1)} degrees (model-derived) and club speed ${S.clubSpeed} mph throughout. * marks an extrapolated row: spin loft outside ${S.floor.toFixed(1)} to ${S.ceil.toFixed(1)} degrees, the range of TrackMan's 2010 chart. TrackMan's chart tabulates attack angles from -5 to +5, so its column is blank outside them. PING's lookup uses the model's ball speed at each row.`);

  const panels = [
    { id: "launch", title: "Launch angle, degrees", dom: [6, 20], ticks: [6, 8, 10, 12, 14, 16, 18, 20], series: [{ get: (r) => r.launch, color: T.ink, w: 2, main: true }],
      tm: (r) => r.tm && r.tm.launch, ping: (r) => r.ping.launch, avg: S.tour.launch_deg, fmt: (v) => v.toFixed(1), unit: "°" },
    { id: "spin", title: "Spin rate, rpm", dom: [0, 5000], ticks: [0, 1000, 2000, 3000, 4000, 5000], series: [{ get: (r) => r.spinUntrimmed, color: T.muted, w: 1.75, main: false }, { get: (r) => r.spin, color: T.ink, w: 2, main: true }],
      tm: (r) => r.tm && r.tm.spin, ping: (r) => r.ping.spin, avg: S.tour.spin_rpm, fmt: grp, unit: " rpm" },
  ];

  mountResponsive(plot, (w) => {
    const stacked = w < 640;
    const pw = stacked ? w : Math.floor((w - 24) / 2);
    const H = 250;
    const m = { l: 46, r: 34, t: 28, b: 34 };
    const wrap = html("div", { class: "fig-panels" });
    panels.forEach((P) => {
      const x = scaleLin(-6, 10, m.l, pw - m.r);
      const y = scaleLin(P.dom[1], P.dom[0], m.t, H - m.b);
      const root = svg("svg", { width: pw, height: H, viewBox: `0 0 ${pw} ${H}`, role: "group", "aria-labelledby": `fig3-${P.id}-t fig3-${P.id}-d` });
      const first = rows[0], last = rows[rows.length - 1];
      const at6 = rows.find((r) => r.attack === 6);
      root.append(svg("title", { id: `fig3-${P.id}-t` }, `Driver ${P.title.toLowerCase()} against attack angle`),
        svg("desc", { id: `fig3-${P.id}-d` }, P.id === "launch"
          ? `Model launch angle rises from ${first.launch.toFixed(1)} to ${last.launch.toFixed(1)} degrees as attack angle goes from minus 6 to plus 10 at fixed loft. The two optimizer charts are drawn for comparison. Values above plus 6 are extrapolated.`
          : `Model spin falls from ${grp(first.spin)} to ${grp(last.spin)} rpm with the tour spin trim, and from ${grp(first.spinUntrimmed)} to ${grp(last.spinUntrimmed)} rpm without it, as attack angle goes from minus 6 to plus 10 at fixed loft. At plus 6 the values are ${grp(at6.spin)} and ${grp(at6.spinUntrimmed)} rpm. Values above plus 6 are extrapolated.`));
      root.append(svg("text", { x: 2, y: 14, fill: T.ink, "font-family": T.sans, "font-size": 13, "font-weight": 600 }, P.title));
      // Extrapolated region.
      const lastIn = [...rows].reverse().find((r) => !r.extrapolated);
      const x0 = x(lastIn.attack + 0.5);
      root.append(svg("rect", { x: x0, y: m.t, width: x(10) - x0, height: H - m.t - m.b, fill: T.line, opacity: 0.45, "pointer-events": "none" }));
      root.append(svg("text", { x: (x0 + x(10)) / 2, y: m.t + 12, "text-anchor": "middle", fill: T.soft, "font-family": T.mono, "font-size": 11 }, "extrapolated"));
      for (const t of P.ticks) {
        root.append(svg("line", { x1: m.l, x2: pw - m.r, y1: y(t), y2: y(t), stroke: T.line, "stroke-width": 1 }));
        root.append(svg("text", { x: m.l - 6, y: y(t) + 4, "text-anchor": "end", fill: T.soft, "font-family": T.mono, "font-size": 11 }, P.id === "spin" ? grp(t) : String(t)));
      }
      for (const t of ticks(-6, 10, 2)) {
        root.append(svg("line", { x1: x(t), x2: x(t), y1: m.t, y2: H - m.b, stroke: t === 0 ? T.soft : "none", "stroke-width": 1 }));
        root.append(svg("text", { x: x(t), y: H - m.b + 16, "text-anchor": "middle", fill: T.soft, "font-family": T.mono, "font-size": 11 }, t === 0 ? "0" : sgn(t, 0)));
      }
      root.append(svg("text", { x: m.l, y: H - 4, fill: T.soft, "font-family": T.mono, "font-size": 11 }, `attack angle, degrees (down ${"−"}, up +)`));

      const path = (pick, from, to) => rows.filter((r) => r.attack >= from && r.attack <= to && pick(r) != null)
        .map((r, i) => `${i ? "L" : "M"}${x(r.attack).toFixed(1)} ${y(pick(r)).toFixed(1)}`).join("");
      root.append(svg("path", { d: path(P.tm, -5, 5), fill: "none", stroke: T.blue, "stroke-width": 1.5, "stroke-linejoin": "round", "pointer-events": "none" }));
      root.append(svg("path", { d: path(P.ping, -6, 10), fill: "none", stroke: T.clay, "stroke-width": 1.5, "stroke-linejoin": "round", "pointer-events": "none" }));
      for (const r of rows) {
        if (r.tm && r.attack % 5 === 0) root.append(svg("rect", { x: x(r.attack) - 4, y: y(P.tm(r)) - 4, width: 8, height: 8, fill: T.blue, stroke: T.card, "stroke-width": 2, "pointer-events": "none" }));
        if (r.attack % 2 === 0) root.append(svg("path", { d: `M${x(r.attack)} ${y(P.ping(r)) - 5}L${x(r.attack) + 5} ${y(P.ping(r))}L${x(r.attack)} ${y(P.ping(r)) + 5}L${x(r.attack) - 5} ${y(P.ping(r))}Z`, fill: T.clay, stroke: T.card, "stroke-width": 1.5, "pointer-events": "none" }));
      }
      // Model lines: solid where calibrated, dotted where extrapolated.
      for (const s of P.series) {
        root.append(svg("path", { d: path(s.get, -6, lastIn.attack), fill: "none", stroke: s.color, "stroke-width": s.w, "stroke-linecap": "round", "stroke-linejoin": "round", "pointer-events": "none" }));
        root.append(svg("path", { d: path(s.get, lastIn.attack, 10), fill: "none", stroke: s.color, "stroke-width": s.w, "stroke-linecap": "round", "stroke-dasharray": "1 4", "pointer-events": "none" }));
      }
      root.append(svg("circle", { cx: x(-0.9), cy: y(P.avg), r: 5, fill: T.card, stroke: T.ink, "stroke-width": 2, "pointer-events": "none" }));
      const main = P.series[P.series.length - 1];
      root.append(svg("text", { x: x(first.attack) + 2, y: y(main.get(first)) - 10, fill: T.ink, "font-family": T.mono, "font-size": 12, "font-weight": 500 }, P.fmt(main.get(first)) + (P.id === "launch" ? "°" : "")));
      root.append(svg("text", { x: x(last.attack) + 5, y: y(main.get(last)) + 4, fill: T.ink, "font-family": T.mono, "font-size": 12, "font-weight": 500 }, P.fmt(main.get(last)) + (P.id === "launch" ? "°" : "")));

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
        cdot.setAttribute("cx", x(r.attack)); cdot.setAttribute("cy", y(main.get(r)));
        cross.setAttribute("visibility", "visible");
        const ex = r.extrapolated ? " (extrapolated)" : "";
        const tr = [{ key: T.ink, dash: r.extrapolated, value: P.fmt(main.get(r)) + P.unit, label: `model${P.id === "spin" ? ", trimmed" : ""}, spin loft ${r.spinLoft.toFixed(1)}°${ex}` }];
        if (P.id === "spin") tr.push({ key: T.muted, dash: r.extrapolated, value: P.fmt(r.spinUntrimmed) + P.unit, label: `model, no trim${ex}` });
        if (P.tm(r) != null) tr.push({ key: T.blue, value: P.fmt(P.tm(r)) + P.unit, label: "TrackMan 2010" });
        tr.push({ key: T.clay, value: P.fmt(P.ping(r)) + P.unit, label: "PING 2019" });
        tip.show({ heading: `Attack angle ${sgn(r.attack, 0)}°`, rows: tr }, cx, cy);
      };
      const hide = () => { cross.setAttribute("visibility", "hidden"); tip.hide(); };
      const overlay = svg("rect", { x: m.l, y: m.t, width: pw - m.l - m.r, height: H - m.t - m.b, fill: "transparent", tabindex: 0, role: "group",
        "aria-label": `${P.title} by attack angle. Use the left and right arrow keys to step through the values.` });
      overlay.addEventListener("pointermove", (e) => {
        const r = overlay.getBoundingClientRect();
        setIdx(Math.round(((e.clientX - r.left) / r.width) * 16), e.clientX, e.clientY);
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
