/*
 * Compare mode. "Pin this shot" freezes the current shot as A (drawn in a second
 * color on the range and the views). The live shot is B. The table shows A, B and
 * the change from A to B for the numbers an instructor talks about.
 *
 * Values are the display frame (positive is right for both hands). A pinned shot
 * is tied to the hand it was pinned with, so flipping the hand clears it.
 */
import { METRICS, fmt } from "./tiles.js";

const ROWS = ["carry_yd", "max_height_yd", "curve_yd", "side_yd", "launch_deg", "spin_rpm"];
// On a short screen the table keeps carry, curve, side and the shot name, so it fits above the fold.
const MORE = new Set(["max_height_yd", "launch_deg", "spin_rpm"]);

export function createCompare({ model, store, range, hooks }) {
  const $ = (s) => document.querySelector(s);
  const pinBtn = $("#pin-btn");
  const clearBtn = $("#clear-pin-btn");
  const status = $("#pin-status");
  const table = $("#cmp-body");
  let pinned = null;

  const clubName = (id) => model.clubs.find((c) => c.id === id).name;
  const playerName = (id) => model.players.find((p) => p.id === id).name;

  function pin(current) {
    const setup = store.snapshot();
    pinned = {
      hand: setup.hand,
      title: `${clubName(setup.club)}, ${playerName(setup.player)}`,
      name: current.s.classification ? current.s.classification.name : "No carry",
      values: Object.fromEntries(ROWS.map((m) => [m, current.values[m].disp])),
      rangeShot: current.rangeShot,
    };
    range.setPinned(pinned.rangeShot, "A");
    range.setLiveTag("B");
    hooks.changed();
  }

  function clear() {
    if (!pinned) return;
    pinned = null;
    range.setPinned(null);
    range.setLiveTag("");
    hooks.changed();
  }

  /** Leaving Compare mode drops the pin and the "B" tag. */
  function reset() {
    pinned = null;
    range.setPinned(null);
    range.setLiveTag("");
  }

  function render(current) {
    clearBtn.disabled = !pinned;
    pinBtn.textContent = pinned ? "Re-pin this shot as A" : "Pin this shot";
    // The table is always there, so pinning a shot fills the A column and the layout does not jump.
    // Before a pin it shows the shot as B, with A and the change left empty.
    table.closest("table").hidden = false;
    const bName = current.s.classification ? current.s.classification.name : "No carry";
    status.textContent = pinned
      ? `A is pinned: ${pinned.title}. Keep adjusting for B.`
      : "No shot pinned yet. Set up a shot, then pin it as A.";
    const rows = ROWS.map((m) => {
      const M = METRICS[m];
      const dec = M.dec;
      const unit = M.unit === "°" ? "°" : M.unit ? " " + M.unit : "";
      const b = Number(current.values[m].disp.toFixed(dec));
      const cls = MORE.has(m) ? ' class="cmp-more"' : "";
      if (!pinned) {
        return `<tr${cls}><th scope="row">${M.label}</th><td></td><td>${fmt(b, dec, M.signed, M.grouped)}${unit}</td><td></td></tr>`;
      }
      // The difference comes from the numbers as shown, so the table always adds up.
      const a = Number(pinned.values[m].toFixed(dec));
      const d = Number((b - a).toFixed(dec));
      const same = d === 0;
      return `<tr${cls}><th scope="row">${M.label}</th><td>${fmt(a, dec, M.signed, M.grouped)}${unit}</td><td>${fmt(b, dec, M.signed, M.grouped)}${unit}</td>`
        + `<td class="cmp-d${same ? " zero" : ""}">${same ? "same" : fmt(d, dec, true, M.grouped) + unit}</td></tr>`;
    });
    rows.push(pinned
      ? `<tr><th scope="row">Shot</th><td>${pinned.name}</td><td>${bName}</td><td class="cmp-d${pinned.name === bName ? " zero" : ""}">${pinned.name === bName ? "same" : "changed"}</td></tr>`
      : `<tr><th scope="row">Shot</th><td></td><td>${bName}</td><td></td></tr>`);
    table.innerHTML = rows.join("");
  }

  pinBtn.addEventListener("click", () => hooks.pinRequest());
  clearBtn.addEventListener("click", clear);
  return { pin, clear, reset, render, get pinned() { return pinned; } };
}
