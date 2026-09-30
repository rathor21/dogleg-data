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
import { createControls, radioGroup } from "./controls.js";
import { createViews } from "./views.js";
import { createWindows } from "./windows.js";
import { createCompare } from "./compare.js";
import { createPresenter } from "./present.js";
import { TILE_GROUPS, KEY_TILES, DEG, fmt, createTile, configureTiles } from "./tiles.js";

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

  // ---- secondary views --------------------------------------------------------------
  // One "on line" distance for the shot name, the Side tile and the top view: the model's own.
  const onLineYd = model.data.model.classify.on_line_yd;
  configureTiles({ onLineYd });
  const views = createViews({ root: $("#views"), onLineYd });
  // On a phone the three panels are tabs. Wider, all three show and the tabs are hidden.
  const viewTabs = [...document.querySelectorAll("#views .view-tab")];
  function selectView(name, focus) {
    for (const t of viewTabs) {
      const on = t.dataset.view === name;
      t.setAttribute("aria-selected", String(on));
      t.tabIndex = on ? 0 : -1;
      if (on && focus) t.focus();
    }
    for (const p of document.querySelectorAll("#views .vpanel")) p.dataset.active = String(p.dataset.view === name);
  }
  $(".view-tabs").addEventListener("click", (e) => { const t = e.target.closest(".view-tab"); if (t) selectView(t.dataset.view); });
  $(".view-tabs").addEventListener("keydown", (e) => {
    const i = viewTabs.findIndex((t) => t.getAttribute("aria-selected") === "true");
    const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
    if (step === undefined) return;
    e.preventDefault();
    selectView(viewTabs[(i + step + viewTabs.length) % viewTabs.length].dataset.view, true);
  });
  selectView("top");
  // The panels are tab panels only while the tabs show (a phone). Wider they are plain figures.
  const tabsShown = window.matchMedia("(max-width: 559px)");
  function applyTabRoles() {
    for (const p of document.querySelectorAll("#views .vpanel")) {
      if (tabsShown.matches) {
        p.setAttribute("role", "tabpanel");
        p.setAttribute("aria-labelledby", "tab-" + p.dataset.view);
      } else {
        p.removeAttribute("role");
        p.removeAttribute("aria-labelledby");
      }
    }
  }
  applyTabRoles();
  tabsShown.addEventListener("change", applyTabRoles);

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
  /** Speak a one-off message (a mode change) without waiting for a shot to change. */
  function announceMode(text) {
    clearTimeout(speechTimer);
    spoken = "";
    srLive.textContent = "";
    setTimeout(() => { srLive.textContent = text; }, 60);
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
    // Carry and total together: on the label, and after the name in the phone drawer's bar.
    const carryTotal = cl ? `${Math.round(f.carry)} yd carry · ${Math.round(c.s.total)} yd total` : "";
    $("#sl-carry").textContent = carryTotal;
    const sum = $("#swing-summary");
    sum.querySelector("b").textContent = name;
    sum.querySelector(".ct").textContent = carryTotal;
    sum.querySelector("span:not(.ct)").textContent = `Path ${fmt(state.path, 1, true)}${DEG} · Face ${fmt(state.face, 1, true)}${DEG}`;
    pendingSpeech = cl ? `${name}. Carries ${Math.round(f.carry)} yards, ${Math.round(c.s.total)} yards total, ${finish}. ${line}.` : "No carry. The ball goes into the ground.";
  }

  let urlTimer = 0;
  function writeUrl() {
    clearTimeout(urlTimer);
    urlTimer = setTimeout(() => {
      try { history.replaceState(null, "", store.buildUrl()); } catch (e) { /* sandboxed frame */ }
    }, 150);
  }

  // The ideals.json known_exceptions entry for this club, player and metric, if any.
  const exceptions = (model.data.ideals && model.data.ideals.known_exceptions) || [];
  function exceptionFor(metric) {
    return exceptions.find((e) => e.club === state.club && e.player === state.player && e.metric === metric) || null;
  }

  function render() {
    current = store.compute();
    Object.assign(state, current.norm); // keep what clampToDomain settled on
    controls.render();
    sliders.render(current, state.hand);
    for (const t of tiles) t.update(current.values[t.metric], current.bands[t.metric], state.hand, exceptionFor(t.metric));
    renderLabel(current);
    renderMode();
    renderAverageButtons();
    if (state.mode === "w") windows.render();
    if (state.mode === "c") compare.render(current);
    writeUrl();
    announceSoon();
  }

  function syncViews() {
    if (!current) return;
    views.update({
      shot: current.rangeShot,
      ghost: range.ghost,
      pinned: compare.pinned ? compare.pinned.rangeShot : null,
      values: current.values,
      classification: current.s.classification,
      hand: state.hand,
    });
  }

  // ---- modes: explore, 9 windows, compare ----------------------------------------------
  const MODE_HINT = {
    e: "Move the sliders and watch the ball flight.",
    w: "Nine 7-iron recipes. Tap one to load it and fly it.",
    c: "Pin a shot as A, change the swing, and read the difference.",
  };
  function renderMode() {
    modeRadio.set((b) => b.dataset.mode === state.mode);
    $("#windows").hidden = state.mode !== "w";
    $("#compare").hidden = state.mode !== "c";
    $("#mode-hint").textContent = MODE_HINT[state.mode];
    if (document.body.dataset.mode !== state.mode) {
      document.body.dataset.mode = state.mode; // tool.css budgets the first screen per mode
      scheduleFit(0);
    }
  }
  function setMode(m) {
    if (m === state.mode) return;
    if (state.mode === "w") { windows.stop(); store.selectWindow(null); }
    if (state.mode === "c") compare.reset();
    state.mode = m;
    // The windows are 7-iron recipes, so the club follows.
    if (m === "w" && state.club !== "7i") store.switchClub("7i");
    commitChange();
  }
  const modeRadio = radioGroup($("#mode-seg"), (b) => setMode(b.dataset.mode));

  let commitTimer = 0;
  function commitNow() {
    clearTimeout(commitTimer);
    commitTimer = 0;
    if (!current) return;
    range.commit(current.rangeShot);
    syncViews();
    announceNow();
  }
  function commitSoon(ms) {
    clearTimeout(commitTimer);
    commitTimer = setTimeout(commitNow, ms);
  }
  function liveChange() {
    render();
    range.preview(current.rangeShot);
    syncViews();
  }
  function commitChange() {
    clearTimeout(commitTimer);
    commitTimer = 0;
    render();
    range.setGroup(current.group);
    range.commit(current.rangeShot);
    syncViews();
    announceNow();
  }

  const windows = createWindows({
    model, store, range,
    hooks: {
      select(key) { windows.applyWindow(key); commitChange(); },
      startSequence() {
        clearTimeout(commitTimer);
        commitTimer = 0;
        // The windows are 7-iron shots: take the 7-iron and its camera view, even if another club was showing.
        store.switchClub("7i");
        range.setGroup(store.groupOf("7i"));
      },
      step() { render(); syncViews(); },
      endSequence() { render(); syncViews(); },
    },
  });
  const compare = createCompare({
    model, store, range,
    hooks: { pinRequest() { compare.pin(current); }, changed() { render(); syncViews(); } },
  });

  const sliders = createSliders({
    model, store,
    containers: { main: $("#sliders"), adv: $("#sliders-adv") },
    hooks: { live: liveChange, commitNow, commitSoon },
  });

  const changeClub = (id) => {
    store.switchClub(id);
    store.selectWindow(null); // a window is a 7-iron recipe
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
        if (state.mode === "w" && state.window) windows.applyWindow(state.window); // the same window, this player's recipe
        else store.applyBase(true);
        commitChange();
      },
      onHand(h) {
        if (h === state.hand) return;
        // Flip the hand and mirror the swing so the same shot shows from the other side.
        state.hand = h;
        state.path = round3(-state.path);
        state.face = round3(-state.face);
        range.clearGhost();
        compare.reset(); // a pinned shot belongs to the hand it was pinned with
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
  // Reset to ideal loads the ideal at the current club speed. The average button loads the
  // tour or amateur average and shows only where the two differ (the driver).
  for (const id of ["#reset-btn", "#reset-btn-2"]) {
    $(id).addEventListener("click", () => {
      store.selectWindow(null);
      store.loadIdeal();
      commitChange();
    });
  }
  for (const id of ["#avg-btn", "#avg-btn-2"]) {
    $(id).addEventListener("click", () => {
      store.selectWindow(null);
      store.loadAverage();
      commitChange();
    });
  }
  function renderAverageButtons() {
    const show = store.averageDiffers();
    const label = `${state.player === "amateur" ? "Amateur" : "Tour"} average`;
    for (const id of ["#avg-btn", "#avg-btn-2"]) {
      $(id).hidden = !show;
      $(id).textContent = label;
    }
  }
  $("#hit-btn").addEventListener("click", hit);
  $("#hit-btn-2").addEventListener("click", hit);
  $("#ghost-check").addEventListener("change", (e) => { range.setGhost(e.target.checked); syncViews(); });

  const copyStatus = $("#copy-status");
  let copyTimer = 0;
  const copyBtn = $("#copy-btn");
  copyBtn.addEventListener("click", async () => {
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
    // The status line is read aloud (and shown where there is room). On a phone the button itself says it.
    copyStatus.textContent = ok ? "Link copied" : "Copy failed";
    copyBtn.textContent = ok ? "Copied" : "Copy failed";
    clearTimeout(copyTimer);
    copyTimer = setTimeout(() => { copyStatus.textContent = ""; copyBtn.textContent = "Copy link"; }, 2500);
  });

  // ---- presentation mode -----------------------------------------------------------------
  const presenter = createPresenter({
    focusEl: "#hit-btn-2",
    returnEl: "#present-btn",
    onChange(on) {
      announceMode(on ? "Presentation mode on. Press Escape to exit." : "Presentation mode off.");
      applyDrawer();
      scheduleFit(0);
      range.redraw();
      views.redraw();
    },
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
    const open = !isDrawer() || drawerOpen || presenter.on;
    swing.dataset.open = String(open);
    toggle.setAttribute("aria-expanded", String(open));
    document.body.dataset.drawer = isDrawer() && drawerOpen && !presenter.on ? "open" : "closed";
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

  // ---- fit to the fold -----------------------------------------------------------------
  // The numbers a mode teaches with sit under the range: the key tiles, the nine
  // windows, the compare card. This measures how much room they need and gives the
  // rest to the range, so they end above the fixed bar instead of running under it.
  // If the range would get too short, body[data-fit="1"] trims detail (see tool.css).
  const rootStyle = document.body.style; // on body, so it beats the body[data-mode] fallbacks in tool.css
  const MAX_RANGE_ASPECT = 2.4;
  function fitFirstScreen() {
    const bs = document.body.dataset;
    if (presenter.on || shortLandscape.matches) {
      rootStyle.removeProperty("--reserve");
      rootStyle.removeProperty("--range-min");
      $("#views").style.marginTop = "";
      $(".win-note").style.marginTop = "";
      delete bs.fit;
      delete bs.tight;
      return;
    }
    // In 9 Windows the attribution note is a footnote: the block that must fit ends at the Fly all nine button.
    const target = state.mode === "w" ? $(".win-actions") : state.mode === "c" ? $("#compare") : $("#key-tiles");
    const cardPad = state.mode === "w" ? parseFloat(getComputedStyle($("#windows")).paddingBottom) || 0 : 0;
    const cs = getComputedStyle(document.documentElement);
    const rem = parseFloat(cs.fontSize) || 16;
    const drawerH = parseFloat(cs.getPropertyValue("--drawer-h")) || 0;
    const barH = parseFloat(getComputedStyle(document.body).paddingBottom) || 0; // drawer and the safe area
    const phone = window.innerWidth < 560;
    // The range never gets flatter than about 2.4 to 1: the picture's crop stops working past that.
    const aspectFloor = rangeRoot.getBoundingClientRect().width / MAX_RANGE_ASPECT;
    // Full detail keeps a 14 rem range on a phone (16 rem wider). Trimmed, a phone may go down to 11 rem.
    const floors = { 0: Math.max((phone ? 14 : 16) * rem, aspectFloor), 1: Math.max((phone ? 11 : 16) * rem, aspectFloor), 2: Math.max(9 * rem, aspectFloor) };
    const pad = 16;
    let reserve = null;
    let minRange = floors[0];
    // Levels: full, trimmed, and (phones only) trimmed with the range bar and page title out of the way.
    for (const level of phone ? ["0", "1", "2"] : ["0", "1"]) {
      bs.fit = level === "0" ? "0" : "1";
      if (level === "2") bs.tight = "1"; else delete bs.tight;
      minRange = floors[level];
      const tr = target.getBoundingClientRect(); // forces layout
      if (!tr.height) { reserve = null; break; }
      const rr = rangeRoot.getBoundingClientRect();
      const top = document.documentElement.getBoundingClientRect().top; // -scrollY, read in the same layout
      const fixed = tr.bottom + cardPad - top - rr.height; // everything above the range plus everything under it
      reserve = fixed + pad + (barH - drawerH);
      if (window.innerHeight - drawerH - reserve >= minRange) break;
    }
    const setVar = (name, px) => {
      if (px === null) rootStyle.removeProperty(name);
      else if (Math.abs(px - (parseFloat(rootStyle.getPropertyValue(name)) || 0)) > 0.5) rootStyle.setProperty(name, px.toFixed(1) + "px");
    };
    setVar("--reserve", reserve);
    setVar("--range-min", reserve === null ? null : minRange);
    // The layout ends at the fold: if the next section would show only its top edge above
    // the fixed bar, it starts below the fold instead. A section that shows more than a sliver stays put.
    const next = $("#views");
    next.style.marginTop = "0px";
    const visible = window.innerHeight - barH - (next.getBoundingClientRect().top);
    next.style.marginTop = visible > 0 && visible < 110 ? Math.ceil(visible + 8) + "px" : "";
    // The 9 Windows footnote never shows half a line above the bar: if it would be cut, it starts below the fold.
    const note = $(".win-note");
    note.style.marginTop = "";
    const nr = note.getBoundingClientRect();
    const fold = window.innerHeight - barH;
    if (state.mode === "w" && nr.height && nr.top < fold && nr.bottom > fold) note.style.marginTop = Math.ceil((parseFloat(getComputedStyle(note).marginTop) || 0) + fold - nr.top + 8) + "px";
  }
  // Debounced: a slider drag can change a tile's wrapping on every step, and the fit only needs to settle when it stops.
  let fitTimer = 0;
  function scheduleFit(delay = 90) {
    clearTimeout(fitTimer);
    fitTimer = setTimeout(() => requestAnimationFrame(fitFirstScreen), delay);
  }
  const fitObserver = new ResizeObserver(() => scheduleFit());
  for (const el of ["#key-tiles", "#windows", "#compare", ".page-head", ".modebar"]) {
    const node = $(el);
    if (node) fitObserver.observe(node);
  }
  window.addEventListener("resize", () => scheduleFit());
  narrow.addEventListener("change", () => scheduleFit(0));
  shortLandscape.addEventListener("change", () => scheduleFit(0));
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => scheduleFit(0));

  // ---- go ------------------------------------------------------------------------
  store.loadFromSearch(location.search, (key) => windows.applyWindow(key));
  render();
  range.setGroup(current.group);
  range.commit(current.rangeShot);
  syncViews();
  announceNow();
  window.__labReady = true;
}

main().catch((err) => {
  console.error(err);
  showError();
});
