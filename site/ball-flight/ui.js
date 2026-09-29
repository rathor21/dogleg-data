/*
 * Ball flight lab: wires the model, the store, the controls, the tiles and the
 * range together. State and URL live in state.js, the sliders in sliders.js, the
 * club, player and hand controls in controls.js, tiles in tiles.js, the canvas in
 * range.js.
 */
import * as F from "./flight.js";
import { createRange } from "./range.js";
import { createStore, round3 } from "./state.js";
import { createSliders } from "./sliders.js";
import { createControls } from "./controls.js";
import { TILE_GROUPS, KEY_TILES, DEG, fmt, createTile } from "./tiles.js";

const $ = (s, r = document) => r.querySelector(s);
const swapLR = (t) => t.replace(/left|right/g, (m) => (m === "left" ? "right" : "left"));
const dirOf = (v) => (v > 0 ? "right" : "left");
const reduceMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function showError() {
  $("#app-loading").hidden = true;
  $("#app-error").hidden = false;
  $("#app").hidden = true;
}

async function main() {
  let model;
  try {
    model = await F.loadModel(new URL("./data/", import.meta.url).href);
  } catch (err) {
    console.error(err);
    showError();
    return;
  }
  $("#app-loading").hidden = true;
  $("#app-error").hidden = true;
  $("#app").hidden = false;

  const store = createStore(model);
  const { state } = store;

  // ---- range ---------------------------------------------------------------------
  const rangeRoot = $("#range");
  const range = createRange({ root: rangeRoot, canvas: $("#range-canvas"), model, avoidEl: $("#shot-label") });

  // ---- tiles ---------------------------------------------------------------------
  const tiles = [];
  const keyHost = $("#key-tiles");
  for (const k of KEY_TILES) {
    const t = createTile(k.metric, "k", k.extra ? "key-extra" : "");
    keyHost.appendChild(t.el);
    tiles.push(t);
  }
  const groupHost = $("#tile-groups");
  for (const g of TILE_GROUPS) {
    const sec = document.createElement("section");
    sec.className = "tile-group";
    sec.innerHTML = `<h3>${g.name}<small>${g.note}</small></h3>`;
    const grid = document.createElement("div");
    grid.className = "tile-grid";
    for (const m of g.items) {
      const t = createTile(m, "a", "");
      grid.appendChild(t.el);
      tiles.push(t);
    }
    sec.appendChild(grid);
    groupHost.appendChild(sec);
  }

  // ---- announcements ---------------------------------------------------------------
  // The visible shot label changes on every drag step, so it is not a live region.
  // A separate screen-reader node speaks once a change settles or is committed.
  const srLive = $("#sr-live");
  const canvas = $("#range-canvas");
  let spoken = "";
  let pendingSpeech = "";
  let speechTimer = 0;
  function announceNow() {
    clearTimeout(speechTimer);
    if (!pendingSpeech || pendingSpeech === spoken) return;
    spoken = pendingSpeech;
    srLive.textContent = spoken;
    canvas.setAttribute("aria-label", "Range view. " + spoken);
  }
  function announceSoon() {
    clearTimeout(speechTimer);
    speechTimer = setTimeout(announceNow, 700);
  }

  // ---- render and change flow ----------------------------------------------------------
  let current = null;

  function renderLabel(c) {
    const cl = c.s.classification;
    const f = c.s.flight;
    const dir = c.values.launch_dir_deg.disp;
    const curve = c.values.curve_yd.disp;
    let name, finish;
    if (cl) {
      name = cl.name;
      finish = state.hand === "l" ? swapLR(cl.finishText) : cl.finishText;
    } else {
      name = "No carry";
      finish = "The ball goes into the ground";
    }
    const start = Math.abs(dir) < 0.05 ? "Starts on the target line" : `Starts ${Math.abs(dir).toFixed(1)}${DEG} ${dirOf(dir)}`;
    const cv = Math.abs(curve);
    const bend = cv < 0.5 ? "no curve" : `curves ${cv < 10 ? cv.toFixed(1) : Math.round(cv)} yd ${dirOf(curve)}`;
    const line = cl ? `${start} · ${bend}` : "Raise dynamic loft or attack angle";
    $("#sl-name").textContent = name;
    $("#sl-finish").textContent = finish;
    $("#sl-line").textContent = line;
    const sum = $("#swing-summary");
    sum.querySelector("b").textContent = name;
    sum.querySelector("span").textContent = `Path ${fmt(state.path, 1, true)}${DEG} · Face ${fmt(state.face, 1, true)}${DEG}`;
    pendingSpeech = cl ? `${name}. Carries ${Math.round(f.carry)} yards, ${finish}. ${line}.` : "No carry. The ball goes into the ground.";
  }

  let urlTimer = 0;
  function writeUrl() {
    clearTimeout(urlTimer);
    urlTimer = setTimeout(() => {
      try { history.replaceState(null, "", store.buildUrl()); } catch (e) { /* sandboxed frame */ }
    }, 150);
  }

  function render() {
    current = store.compute();
    Object.assign(state, current.norm); // keep what clampToDomain settled on
    controls.render();
    sliders.render(current, state.hand);
    for (const t of tiles) t.update(current.values[t.metric], current.bands[t.metric], state.hand);
    renderLabel(current);
    writeUrl();
    announceSoon();
  }

  let commitTimer = 0;
  function commitNow() {
    clearTimeout(commitTimer);
    commitTimer = 0;
    if (!current) return;
    range.commit(current.rangeShot);
    announceNow();
  }
  function commitSoon(ms) {
    clearTimeout(commitTimer);
    commitTimer = setTimeout(commitNow, ms);
  }
  function liveChange() {
    render();
    range.preview(current.rangeShot);
  }
  function commitChange() {
    clearTimeout(commitTimer);
    commitTimer = 0;
    render();
    range.setGroup(current.group);
    range.commit(current.rangeShot);
    announceNow();
  }

  const sliders = createSliders({
    model, store,
    containers: { main: $("#sliders"), adv: $("#sliders-adv") },
    hooks: { live: liveChange, commitNow, commitSoon },
  });

  const changeClub = (id) => {
    state.club = id;
    store.lastClubInGroup[store.groupOf(id)] = id;
    store.applyPreset(true);
    commitChange();
  };
  const controls = createControls({
    model, store,
    hooks: {
      onGroup(g) { if (g !== store.groupOf()) changeClub(store.lastClubInGroup[g]); },
      onClub(id) { if (id !== state.club) changeClub(id); },
      onPlayer(id) {
        if (id === state.player) return;
        state.player = id;
        store.applyPreset(true);
        commitChange();
      },
      onHand(h) {
        if (h === state.hand) return;
        // Flip the hand and mirror the swing so the same shot shows from the other side.
        state.hand = h;
        state.path = round3(-state.path);
        state.face = round3(-state.face);
        range.clearGhost();
        commitChange();
      },
      onSpeed(n) { range.setSpeed(n); hit(); },
    },
  });

  // ---- reset, hit, copy ------------------------------------------------------------
  function hit() {
    // A slider change waiting to fly goes now, so Hit never replays a stale shot.
    if (commitTimer) commitNow(); else range.replay();
  }
  for (const id of ["#reset-btn", "#reset-btn-2"]) {
    $(id).addEventListener("click", () => {
      store.applyPreset(false);
      commitChange();
    });
  }
  $("#hit-btn").addEventListener("click", hit);
  $("#hit-btn-2").addEventListener("click", hit);
  $("#ghost-check").addEventListener("change", (e) => range.setGhost(e.target.checked));

  const copyStatus = $("#copy-status");
  let copyTimer = 0;
  $("#copy-btn").addEventListener("click", async () => {
    const url = new URL(store.buildUrl(), location.href).href;
    let ok = false;
    try {
      await navigator.clipboard.writeText(url);
      ok = true;
    } catch (e) {
      const ta = document.createElement("textarea");
      ta.value = url;
      ta.setAttribute("readonly", "");
      ta.style.cssText = "position:fixed;opacity:0";
      document.body.appendChild(ta);
      ta.select();
      try { ok = document.execCommand("copy"); } catch (e2) { ok = false; }
      ta.remove();
    }
    copyStatus.textContent = ok ? "Link copied" : "Copy failed";
    clearTimeout(copyTimer);
    copyTimer = setTimeout(() => { copyStatus.textContent = ""; }, 2500);
  });

  // ---- drawer ------------------------------------------------------------------------
  // Below 901px the swing controls sit in a bottom drawer, except on a short
  // landscape screen, where they stay a side panel so the range keeps its height.
  // The same two conditions are in tool.css.
  const swing = $("#swing");
  const toggle = $("#swing-toggle");
  const body = $("#swing-body");
  const narrow = window.matchMedia("(max-width: 900px)");
  const shortLandscape = window.matchMedia("(max-height: 500px) and (min-width: 560px)");
  const isDrawer = () => narrow.matches && !shortLandscape.matches;
  let drawerOpen = false;
  function applyDrawer() {
    const open = !isDrawer() || drawerOpen;
    swing.dataset.open = String(open);
    toggle.setAttribute("aria-expanded", String(open));
    body.inert = !open;
  }
  function setDrawer(open, refocus) {
    drawerOpen = open;
    applyDrawer();
    if (open) {
      // Bring the range to the top of the screen so the drawer does not hide it.
      const top = rangeRoot.getBoundingClientRect().top + window.scrollY - 8;
      window.scrollTo({ top: Math.max(0, top), behavior: reduceMotion() ? "auto" : "smooth" });
    } else if (refocus) {
      toggle.focus();
    }
  }
  toggle.addEventListener("click", () => setDrawer(!drawerOpen, false));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && isDrawer() && drawerOpen) {
      e.preventDefault();
      setDrawer(false, swing.contains(document.activeElement));
    }
  });
  narrow.addEventListener("change", applyDrawer);
  shortLandscape.addEventListener("change", applyDrawer);
  applyDrawer();

  // ---- go ------------------------------------------------------------------------
  store.loadFromSearch(location.search);
  render();
  range.setGroup(current.group);
  range.commit(current.rangeShot);
  announceNow();
  window.__labReady = true;
}

main().catch((err) => {
  console.error(err);
  showError();
});
