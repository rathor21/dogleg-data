/* Table 1: the preset rows for the driver, 6-iron and wedge, published values where they exist. */
import { presetTable } from "./article-data.js";
import { html, grp } from "./article-svg.js";

export function drawPresets(fig, model) {
  const T = presetTable(model);
  const fmt = (c) => (c.dp === 0 ? grp(c.value) : Number(c.value).toFixed(c.dp));
  const table = html("table", { class: "data presets" },
    html("thead", {}, html("tr", {}, [html("th", { scope: "col", class: "l" }, "Club and player"), ...T.cols.map((c) => html("th", { scope: "col", class: "r" }, c.label))])),
    html("tbody", {}, T.rows.map((r) => html("tr", { class: r.player === "pga" ? "group-start" : null },
      html("th", { scope: "row", class: "l" }, r.label),
      ...r.cells.map((c) => html("td", { class: "r" }, fmt(c),
        c.kind === "modeled" ? html("span", { class: "badge-modeled" }, "modeled") : c.kind === "default" ? html("span", { class: "badge-modeled" }, "default") : null))))));
  fig.querySelector(".tbl-wrap").replaceChildren(table);
}
