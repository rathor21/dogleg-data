/* Figure 1: start direction from 4 degrees of face or 4 degrees of path, driver and 7-iron. */
import { startDirection } from "./article-data.js";
import { svg, html, sgn, MINUS, scaleLin, ticks, tokens, mountResponsive, roundedBar, tip, centerOf, fillTable, legendItem } from "./article-svg.js";

export function drawStart(fig, model) {
  const T = tokens();
  const data = startDirection(model);
  const plot = fig.querySelector(".fig-plot");
  const legend = fig.querySelector("[data-legend]");
  legend.replaceChildren(legendItem("bar", T.clay, "Face changed, path 0"), legendItem("bar", T.blue, "Path changed, face 0"));

  const rowLabel = (r) => `${r.input === "face" ? "Face" : "Path"} ${sgn(r.value, 0)}°`;
  const side = (d) => (d < 0 ? "left" : "right");

  fillTable(fig.querySelector(".fig-table"),
    ["Club", "Change (deg)", "Start direction (deg)", "Yards off line at 200 yd"],
    data.flatMap((c) => c.rows.map((r) => [c.label, rowLabel(r), sgn(r.deg, 2), sgn(r.yd200, 1)])),
    "Start direction is the model's launch direction, right positive. Yards off line uses 200 yd times the tangent of that angle, TrackMan's launch direction geometry.");

  mountResponsive(plot, (w) => {
    const narrow = w < 480;
    const labelW = narrow ? 68 : 84;
    const left = labelW, right = 8;
    const x = scaleLin(-5, 5, left, w - right);
    const barH = 16, pitch = 27, titleH = 26, axisH = 24, gap = 10;
    const panelH = titleH + 4 * pitch + axisH;
    const H = data.length * panelH + (data.length - 1) * gap + 22;
    const root = svg("svg", { width: w, height: H, viewBox: `0 0 ${w} ${H}`, role: "group", "aria-labelledby": "fig1-t fig1-d" });
    root.append(svg("title", { id: "fig1-t" }, "Start direction from face and path changes"),
      svg("desc", { id: "fig1-d" }, `Horizontal bars for the Tour driver and 6-iron. Four degrees of face moves the driver's start line ${Math.abs(data[0].rows[1].deg).toFixed(1)} degrees. Four degrees of path moves it ${Math.abs(data[0].rows[3].deg).toFixed(1)} degrees. The data table lists each value.`));

    data.forEach((c, pi) => {
      const y0 = pi * (panelH + gap);
      const g = svg("g", { transform: `translate(0 ${y0})` });
      g.append(svg("text", { x: 0, y: 14, fill: T.ink, "font-family": T.sans, "font-size": 13, "font-weight": 600 }, c.label));
      g.append(svg("text", { x: w - 2, y: 14, "text-anchor": "end", fill: T.soft, "font-family": T.mono, "font-size": 11 }, "PGA Tour preset"));
      const top = titleH;
      for (const t of ticks(-4, 4, 2)) {
        g.append(svg("line", { x1: x(t), x2: x(t), y1: top - 4, y2: top + 4 * pitch, stroke: t === 0 ? T.soft : T.line, "stroke-width": 1 }));
        g.append(svg("text", { x: x(t), y: top + 4 * pitch + 15, "text-anchor": "middle", fill: T.soft, "font-family": T.mono, "font-size": 11 }, t === 0 ? "0" : sgn(t, 0)));
      }
      c.rows.forEach((r, i) => {
        const cy = top + i * pitch;
        const color = r.input === "face" ? T.clay : T.blue;
        const by = cy + (pitch - barH) / 2 - 1;
        const label = `${c.label}, ${rowLabel(r)}: starts ${Math.abs(r.deg).toFixed(1)} degrees ${side(r.deg)}, ${Math.abs(r.yd200).toFixed(1)} yards ${side(r.deg)} of line at 200 yards`;
        const row = svg("g", { class: "hit", tabindex: 0, role: "img", "aria-label": label });
        row.append(svg("rect", { x: 0, y: cy, width: w, height: pitch, fill: "transparent" }));
        row.append(svg("text", { x: 0, y: by + barH - 3, fill: T.soft, "font-family": T.mono, "font-size": 11.5 }, rowLabel(r)));
        row.append(svg("path", { d: roundedBar(x(0), x(r.deg), by, barH, 4), fill: color, class: "mark" }));
        const dir = r.deg >= 0 ? 1 : -1;
        row.append(svg("text", { x: x(r.deg) + dir * 7, y: by + barH - 3, "text-anchor": dir > 0 ? "start" : "end", fill: T.ink, "font-family": T.mono, "font-size": 12, "font-weight": 500 }, `${sgn(r.deg, 1)}°`));
        const show = (cx, cyy) => tip.show({
          heading: `${c.label}, ${rowLabel(r)}`,
          rows: [{ key: color, value: `${Math.abs(r.deg).toFixed(1)}° ${side(r.deg)}`, label: "start direction" },
            { value: `${Math.abs(r.yd200).toFixed(1)} yd ${side(r.deg)}`, label: "off line at 200 yd" }],
        }, cx, cyy);
        row.addEventListener("pointermove", (e) => show(e.clientX, e.clientY));
        row.addEventListener("pointerleave", () => tip.hide());
        row.addEventListener("focus", () => { const [a, b] = centerOf(row); show(a, b); });
        row.addEventListener("blur", () => tip.hide());
        g.append(row);
      });
      root.append(g);
    });
    root.append(svg("text", { x: x(0), y: H - 4, "text-anchor": "middle", fill: T.soft, "font-family": T.mono, "font-size": 11 }, `degrees from target (left ${MINUS}, right +)`));
    plot.replaceChildren(root);
  });
}
