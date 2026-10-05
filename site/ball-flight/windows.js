/*
 * 9 Windows mode. Nine recipes for the 7-iron (three heights by three shapes)
 * from model.windows (windows.json). Tapping a window loads its delivery into
 * the sliders and flies it. "Fly all nine" plays them in order and leaves every
 * tracer on the range.
 *
 * windows.json is right-handed. For a left-handed golfer the recipe's path and
 * face are negated (the page's target-line convention) and the columns swap
 * sides, so a lefty draw sits on the right, where it curves.
 */
import { WINDOW_KEYS, WINDOW_HEIGHTS, WINDOW_SHAPES } from "./state.js";
import { METRICS, DEG, fmt, loftNote, FT_PER_YD } from "./tiles.js";

const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
export const windowName = (key) => {
  const [h, s] = key.split("_");
  return `${cap(h)} ${s}`;
};

export function createWindows({ model, store, range, hooks }) {
  const { state } = store;
  const $ = (s) => document.querySelector(s);
  const root = $("#windows");
  const grid = $("#win-grid");
  const recipe = $("#win-recipe");
  const clubNote = $("#win-club-note");
  const flyBtn = $("#fly-all");
  const buttons = {};
  let running = false;

  const rec = (key, player = state.player) => model.windows.players[player][key];

  /** A window's delivery in the display frame for the current hand. */
  function delivery(key, hand = state.hand, player = state.player) {
    const w = rec(key, player);
    const sign = hand === "l" ? -1 : 1;
    const d = w.delivery;
    return {
      club: "7i",
      clubSpeed: d.club_speed_mph,
      attack: d.attack_deg,
      path: sign * d.path_deg + 0,
      face: sign * d.face_deg + 0,
      dynLoft: d.dyn_loft_deg,
      spinTrim: w.spin_trim,
      lie: 0, // a recipe is a center strike at the address lie
      strikeToe: 0,
      strikeUp: 0,
    };
  }

  function applyWindow(key) {
    store.switchClub("7i");
    Object.assign(state, delivery(key));
    store.syncLoftOffset(); // the recipe's loft is the starting point for following attack
    store.syncSwingDir(); // and its path and attack are the held swing direction
    store.selectWindow(key);
  }

  // ---- grid ------------------------------------------------------------------------
  // Each button is described by its row and column header, and the arrow keys move
  // between windows in the order they are drawn (so a lefty's grid moves the way it looks).
  function build() {
    grid.innerHTML = "";
    grid.appendChild(Object.assign(document.createElement("span"), { className: "win-corner", "aria-hidden": "true" }));
    for (const shape of WINDOW_SHAPES) {
      const h = document.createElement("span");
      h.className = "win-colhead";
      h.id = `win-ch-${shape}`;
      h.dataset.shape = shape;
      h.style.gridRow = 1;
      h.textContent = cap(shape);
      grid.appendChild(h);
    }
    WINDOW_HEIGHTS.forEach((height, r) => {
      const rh = document.createElement("span");
      rh.className = "win-rowhead";
      rh.id = `win-rh-${height}`;
      rh.style.gridRow = r + 2;
      rh.textContent = cap(height);
      grid.appendChild(rh);
      WINDOW_SHAPES.forEach((shape) => {
        const key = `${height}_${shape}`;
        const b = document.createElement("button");
        b.type = "button";
        b.className = "win-btn";
        b.dataset.key = key;
        b.dataset.shape = shape;
        b.dataset.height = height;
        b.style.gridRow = r + 2;
        b.tabIndex = -1;
        b.setAttribute("aria-pressed", "false");
        b.setAttribute("aria-describedby", `win-rh-${height} win-ch-${shape}`);
        b.innerHTML = `<span class="wb-n" aria-hidden="true">${WINDOW_KEYS.indexOf(key) + 1}</span><span class="wb-name">${windowName(key)}</span><span class="wb-peak"></span>`;
        b.addEventListener("click", () => { if (!running) hooks.select(key); });
        grid.appendChild(b);
        buttons[key] = b;
      });
    });
    grid.addEventListener("keydown", onGridKey);
    flyBtn.addEventListener("click", () => (running ? stop() : flyAll()));
  }

  /** Visual [row, column] of a button: columns swap for a lefty. */
  function cell(key) {
    const [height, shape] = key.split("_");
    const order = state.hand === "l" ? [...WINDOW_SHAPES].reverse() : WINDOW_SHAPES;
    return [WINDOW_HEIGHTS.indexOf(height), order.indexOf(shape)];
  }
  function keyAt(row, col) {
    const order = state.hand === "l" ? [...WINDOW_SHAPES].reverse() : WINDOW_SHAPES;
    return `${WINDOW_HEIGHTS[row]}_${order[col]}`;
  }
  function onGridKey(e) {
    const btn = e.target.closest(".win-btn");
    if (!btn) return;
    const d = { ArrowLeft: [0, -1], ArrowRight: [0, 1], ArrowUp: [-1, 0], ArrowDown: [1, 0] }[e.key];
    if (!d) return;
    e.preventDefault();
    const [r, c] = cell(btn.dataset.key);
    const nr = Math.min(2, Math.max(0, r + d[0])), nc = Math.min(2, Math.max(0, c + d[1]));
    const next = buttons[keyAt(nr, nc)];
    setTabStop(next.dataset.key);
    next.focus();
  }
  /** One tab stop for the whole grid: the selected window, or the first one. */
  function setTabStop(key) {
    for (const [k, b] of Object.entries(buttons)) b.tabIndex = k === key ? 0 : -1;
  }

  /** Put the columns in chart order for the hand: a lefty's draw is on the right. */
  function layoutColumns() {
    const order = state.hand === "l" ? [...WINDOW_SHAPES].reverse() : WINDOW_SHAPES;
    const cols = { draw: 0, straight: 0, fade: 0 };
    order.forEach((s, i) => { cols[s] = i + 2; }); // grid column 1 is the row label
    for (const h of grid.querySelectorAll(".win-colhead")) h.style.gridColumn = cols[h.dataset.shape];
    for (const b of Object.values(buttons)) b.style.gridColumn = cols[b.dataset.shape];
  }

  function render() {
    layoutColumns();
    const isSeven = state.club === "7i";
    clubNote.textContent = isSeven
      ? "" // the mode hint already says these are 7-iron recipes
      : "The windows are 7-iron recipes. Tap a window to switch back to the 7-iron.";
    for (const key of WINDOW_KEYS) {
      const w = rec(key);
      buttons[key].querySelector(".wb-peak").textContent = `${Math.round(w.flight.max_height_yd * FT_PER_YD)} ft high`;
      buttons[key].setAttribute("aria-pressed", String(state.window === key));
    }
    if (!grid.contains(document.activeElement)) setTabStop(state.window || keyAt(0, 0));
    // recipe
    if (!state.window) {
      recipe.innerHTML = '<p class="win-empty">Tap a window to load its recipe into the sliders and fly it.</p>';
      return;
    }
    const w = rec(state.window);
    const d = delivery(state.window);
    const sign = state.hand === "l" ? -1 : 1;
    const words = (metric, rhVal) => (METRICS[metric].words ? METRICS[metric].words(rhVal, sign * rhVal) : "");
    const rows = [
      ["Path", `${fmt(d.path, 1, true)}${DEG}`, words("path_deg", w.delivery.path_deg)],
      ["Face", `${fmt(d.face, 1, true)}${DEG}`, words("face_deg", w.delivery.face_deg)],
      ["Attack", `${fmt(d.attack, 1, true)}${DEG}`, words("attack_deg", w.delivery.attack_deg)],
      ["Peak height", `${Math.round(w.flight.max_height_yd * FT_PER_YD)} ft`, ""], // peak defines high, mid and low, so it stays in the first four rows a small screen keeps
      ["Dynamic loft", `${fmt(w.launch.dyn_loft_deg, 1)}${DEG}`, loftNote(w.launch.dyn_loft_deg, { input: w.launch.dyn_loft_input_deg, faceToPathRh: w.launch.face_to_path_deg })],
      ["Launch", `${fmt(w.launch.launch_deg, 1)}${DEG}`, ""],
      ["Spin", `${fmt(w.launch.spin_rpm, 0, false, true)} rpm`, ""],
      ["Shot", w.classification.name, w.classification.finish_text.replace(/left|right/, (m) => (state.hand === "l" ? (m === "left" ? "right" : "left") : m))],
    ];
    const off = Math.abs(state.path - d.path) > 0.06 || Math.abs(state.face - d.face) > 0.06 || Math.abs(state.attack - d.attack) > 0.06
      || Math.abs(state.dynLoft - d.dynLoft) > 0.06 || Math.abs(state.clubSpeed - d.clubSpeed) > 0.6;
    recipe.innerHTML = `<h3>${windowName(state.window)} <span class="win-adj">${off ? "sliders moved off the recipe" : "sliders match the recipe"}</span></h3>`
      + `<dl class="win-dl">${rows.map(([k, v, note]) => `<div><dt>${k}</dt><dd>${v}${note ? `<small>${note}</small>` : ""}</dd></div>`).join("")}</dl>`;
  }

  // ---- fly all nine --------------------------------------------------------------------
  function flyAll() {
    // Each shot is computed from its own copy of the state, so the sliders stay put until it flies.
    const items = WINDOW_KEYS.map((key) => {
      const c = store.compute({ ...state, ...delivery(key), club: "7i" });
      return { shot: c.rangeShot, label: String(WINDOW_KEYS.indexOf(key) + 1), name: windowName(key), key };
    });
    running = true;
    flyBtn.setAttribute("aria-pressed", "true");
    hooks.startSequence();
    range.playSequence(items, {
      speed: 2.5,
      onStep(i, item) {
        applyWindow(item.key);
        hooks.step();
      },
      onEnd(cancelled) {
        running = false;
        flyBtn.setAttribute("aria-pressed", "false");
        hooks.endSequence(cancelled);
      },
    });
  }

  function stop() {
    if (running) range.cancelSequence();
  }

  build();
  return { render, applyWindow, delivery, stop, flyAll, get running() { return running; } };
}
