/* Figure 4: driver launch and spin, each group's published average against the two published optimizers. */
import { driverWindows } from "./article-data.js";
import { svg, sgn, grp, scaleLin, tokens, mountResponsive, tip, centerOf, fillTable, legendItem } from "./article-svg.js";

export function drawDriver(fig, model) {
  const T = tokens();
  const D = driverWindows(model);
  const plot = fig.querySelector(".fig-plot");
  fig.querySelector("[data-legend]").replaceChildren(
    legendItem("dot", T.ink, "Published average"),
    legendItem("square", T.blue, "TrackMan 2010 carry chart"),
    legendItem("ring", T.blue, "TrackMan 2010 total-distance chart"),
    legendItem("diamond", T.clay, "PING 2019"),
    legendItem("bar", T.line, "Lab ideal band"));

  fillTable(fig.querySelector(".fig-table"),
    ["Group", "Club speed (mph)", "Ball speed (mph)", "Attack angle (deg)", "Average launch (deg)", "Carry chart launch (deg)", "PING launch (deg)", "Total chart launch (deg)", "Average spin (rpm)", "Carry chart spin (rpm)", "PING spin (rpm)", "Total chart spin (rpm)"],
    D.map((d) => [d.label, d.clubSpeed.toFixed(0), d.ballSpeed.toFixed(0), sgn(d.attack, 1), d.avg.launch.toFixed(1), d.tm.launch_deg.toFixed(1), d.ping.launch_deg.toFixed(1), d.total.launch_deg.toFixed(1), grp(d.avg.spin), grp(d.tm.spin_rpm), grp(d.ping.spin_rpm), grp(d.total.spin_rpm)]),
    "Averages are TrackMan's 2023 Tour tables and the Combine average golfer (14.5 handicap), all published. Chart values interpolate between published cells at the group's published club speed (TrackMan charts), published ball speed (PING) and attack angle. The band is the carry chart and PING widened by 1 degree and 200 rpm.");

  const panels = [
    { id: "launch", title: "Launch angle, degrees", dom: [6, 16], step: 2, avg: (d) => d.avg.launch, tm: (d) => d.tm.launch_deg, total: (d) => d.total.launch_deg, ping: (d) => d.ping.launch_deg, band: (d) => d.band.launch, fmt: (v) => v.toFixed(1), tick: (v) => String(v) },
    { id: "spin", title: "Spin rate, rpm", dom: [2000, 3600], step: 400, avg: (d) => d.avg.spin, tm: (d) => d.tm.spin_rpm, total: (d) => d.total.spin_rpm, ping: (d) => d.ping.spin_rpm, band: (d) => d.band.spin, fmt: grp, tick: grp },
  ];

  mountResponsive(plot, (w) => {
    const left = 4, right = 12;
    const rowH = 62, titleH = 26, axisH = 26, gap = 8;
    const panelH = titleH + D.length * rowH + axisH;
    const H = panels.length * panelH + (panels.length - 1) * gap;
    const root = svg("svg", { width: w, height: H, viewBox: `0 0 ${w} ${H}`, role: "group", "aria-labelledby": "fig4-t fig4-d" });
    root.append(svg("title", { id: "fig4-t" }, "Driver launch and spin against the TrackMan 2010 and PING 2019 optimizers"),
      svg("desc", { id: "fig4-d" }, "Two dot strips, launch angle and spin rate, with one row each for the PGA Tour, LPGA Tour and average amateur. The LPGA Tour average launch sits below the carry chart and PING values and above the total-distance chart value. The data table lists every value."));

    panels.forEach((P, pi) => {
      const x = scaleLin(P.dom[0], P.dom[1], left + 8, w - right);
      const g = svg("g", { transform: `translate(0 ${pi * (panelH + gap)})` });
      g.append(svg("text", { x: left, y: 14, fill: T.ink, "font-family": T.sans, "font-size": 13, "font-weight": 600 }, P.title));
      const axisY = titleH + D.length * rowH;
      for (let t = P.dom[0]; t <= P.dom[1] + 1e-9; t += P.step) {
        g.append(svg("line", { x1: x(t), x2: x(t), y1: titleH - 2, y2: axisY, stroke: T.line, "stroke-width": 1 }));
        g.append(svg("text", { x: x(t), y: axisY + 15, "text-anchor": "middle", fill: T.soft, "font-family": T.mono, "font-size": 11 }, P.tick(t)));
      }
      D.forEach((d, i) => {
        const top = titleH + i * rowH;
        const cy = top + 34;
        const [bl, bh] = P.band(d);
        const label = `${d.label}, ${d.clubSpeed.toFixed(0)} mph, attack ${sgn(d.attack, 1)}°`;
        const unit = P.id === "launch" ? "°" : " rpm";
        const aria = `${label}: published average ${P.fmt(P.avg(d))}${unit}, TrackMan 2010 carry chart ${P.fmt(P.tm(d))}${unit}, total-distance chart ${P.fmt(P.total(d))}${unit}, PING 2019 ${P.fmt(P.ping(d))}${unit}.`;
        const row = svg("g", { class: "hit", tabindex: 0, role: "img", "aria-label": aria });
        row.append(svg("rect", { x: 0, y: top, width: w, height: rowH, fill: "transparent" }));
        row.append(svg("text", { x: left, y: top + 12, fill: T.soft, "font-family": T.mono, "font-size": 11.5 }, label));
        row.append(svg("rect", { x: x(bl), y: cy - 6, width: Math.max(2, x(bh) - x(bl)), height: 12, rx: 6, fill: T.line }));
        row.append(svg("rect", { x: x(P.tm(d)) - 5, y: cy - 16, width: 10, height: 10, fill: T.blue, stroke: T.card, "stroke-width": 2, class: "mark" }));
        row.append(svg("rect", { x: x(P.total(d)) - 4.5, y: cy - 15.5, width: 9, height: 9, fill: T.card, stroke: T.blue, "stroke-width": 2, class: "mark" }));
        const py = cy + 14;
        row.append(svg("path", { d: `M${x(P.ping(d))} ${py - 6}L${x(P.ping(d)) + 6} ${py}L${x(P.ping(d))} ${py + 6}L${x(P.ping(d)) - 6} ${py}Z`, fill: T.clay, stroke: T.card, "stroke-width": 1.5, class: "mark" }));
        row.append(svg("circle", { cx: x(P.avg(d)), cy, r: 6, fill: T.ink, stroke: T.card, "stroke-width": 2, class: "mark" }));
        // Value label for the published average, placed on the side with room.
        const ax = x(P.avg(d));
        const toRight = ax < w * 0.62;
        row.append(svg("text", { x: ax + (toRight ? 12 : -12), y: cy + 4, "text-anchor": toRight ? "start" : "end", fill: T.ink, "font-family": T.mono, "font-size": 12, "font-weight": 500 }, P.fmt(P.avg(d)) + (P.id === "launch" ? "°" : "")));
        const show = (cx, cyy) => tip.show({
          heading: label,
          rows: [{ key: T.ink, value: P.fmt(P.avg(d)) + unit, label: "published average" },
            { key: T.blue, value: P.fmt(P.tm(d)) + unit, label: "TrackMan 2010 carry chart" },
            { key: T.blue, dash: true, value: P.fmt(P.total(d)) + unit, label: "TrackMan 2010 total-distance chart" },
            { key: T.clay, value: P.fmt(P.ping(d)) + unit, label: "PING 2019" },
            { value: `${P.fmt(bl)} to ${P.fmt(bh)}${unit}`, label: "lab ideal band" }],
        }, cx, cyy);
        row.addEventListener("pointermove", (e) => show(e.clientX, e.clientY));
        row.addEventListener("pointerleave", () => tip.hide());
        row.addEventListener("focus", () => { const [a, b] = centerOf(row); show(a, b); });
        row.addEventListener("blur", () => tip.hide());
        g.append(row);
      });
      root.append(g);
    });
    plot.replaceChildren(root);
  });
}
