/*
 * Ball flight lab: state, controls, tiles, URL and the range wiring.
 *
 * State holds the delivery the way the sliders show it: target-line frame,
 * positive is right, for both hands. For a left-handed golfer the model runs
 * with path and face negated, and every lateral output is negated back for
 * display and for the drawn scene. The shot name comes from classify on the
 * right-handed-frame values, so a lefty draw still reads "Draw".
 */
import * as F from "./flight.js";
import { createRange } from "./range.js";
import { METRICS, TILE_GROUPS, KEY_TILES, MINUS, fmt, createTile } from "./tiles.js";

const $ = (s, r = document) => r.querySelector(s);
const el = (tag, cls, html) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
};

const GROUP_LABEL = { wedge: "Wedges" };
const PLAYER_LABEL = { amateur: "Amateur" };
const GROUP_DEFAULT_CLUB = { driver: "driver", wood: "3w", long_iron: "5i", short_iron: "7i", wedge: "pw" };
const DEG = "°";

const SLIDERS = [
  { key: "clubSpeed", metric: "club_speed_mph", label: "Club speed", unit: " mph", step: 1, dec: 0, dom: "club_speed_mph" },
  { key: "attack", metric: "attack_deg", label: "Attack angle", unit: DEG, step: 0.5, dec: 1, signed: true, dom: "attack_deg", zero: true,
    hints: () => [MINUS + " down", "+ up"] },
  { key: "path", metric: "path_deg", label: "Club path", unit: DEG, step: 0.5, dec: 1, signed: true, dom: "path_deg", zero: true,
    hints: (h) => (h === "l" ? [MINUS + " in-to-out", "+ out-to-in"] : [MINUS + " out-to-in", "+ in-to-out"]) },
  { key: "face", metric: "face_deg", label: "Face angle (to target)", unit: DEG, step: 0.5, dec: 1, signed: true, dom: "face_deg", zero: true,
    hints: (h) => (h === "l" ? [MINUS + " open", "+ closed"] : [MINUS + " closed", "+ open"]) },
  { key: "dynLoft", metric: "dyn_loft_deg", label: "Dynamic loft", unit: DEG, step: 0.5, dec: 1, dom: "dyn_loft_deg", advanced: true },
];

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const round3 = (v) => Math.round(v * 1000) / 1000 + 0;
const snap = (v, step) => round3(Math.round(v / step) * step);
const swapLR = (t) => t.replace(/left|right/g, (m) => (m === "left" ? "right" : "left"));
const dirOf = (v) => (v > 0 ? "right" : "left");

async function main() {
  const loadingEl = $("#app-loading");
  const errorEl = $("#app-error");
  const app = $("#app");

  let model;
  try {
    model = await F.loadModel(new URL("./data/", import.meta.url).href);
  } catch (err) {
    console.error(err);
    loadingEl.hidden = true;
    errorEl.hidden = false;
    return;
  }
  loadingEl.hidden = true;
  app.hidden = false;

  const clubById = Object.fromEntries(model.clubs.map((c) => [c.id, c]));
  const metricValue = model.metricValue || F.metricValue;

  // ---- state -------------------------------------------------------------------
  const state = { club: "7i", player: "pga", hand: "r", clubSpeed: 0, attack: 0, path: 0, face: 0, dynLoft: 0, spinTrim: 1 };
  const lastClubInGroup = { ...GROUP_DEFAULT_CLUB };

  function applyPreset(keepLateral) {
    const p = model.preset(state.club, state.player);
    state.clubSpeed = p.clubSpeed;
    state.attack = p.attack;
    state.dynLoft = p.dynLoft;
    state.spinTrim = p.spinTrim;
    if (!keepLateral) { state.path = p.path + 0; state.face = p.face + 0; }
    return p;
  }

  function readUrl() {
    const q = new URLSearchParams(location.search);
    const club = q.get("c");
    const player = q.get("p");
    if (club && clubById[club]) state.club = club;
    if (player && model.players.some((p) => p.id === player)) state.player = player;
    const hand = q.get("h");
    if (hand === "l" || hand === "r") state.hand = hand;
    applyPreset(false);
    const num = (k) => {
      if (!q.has(k)) return null;
      const v = Number(q.get(k));
      return Number.isFinite(v) ? v : null;
    };
    const map = { s: "clubSpeed", a: "attack", pa: "path", f: "face", l: "dynLoft" };
    for (const [k, key] of Object.entries(map)) {
      const v = num(k);
      if (v !== null) state[key] = v;
    }
    // Clamp what the URL gave (compute() also runs clampToDomain on every shot).
    lastClubInGroup[clubById[state.club].group] = state.club;
  }

  let urlTimer = 0;
  function writeUrl() {
    clearTimeout(urlTimer);
    urlTimer = setTimeout(() => {
      const r2 = (v) => String(Math.round(v * 100) / 100 + 0);
      const q = new URLSearchParams({
        c: state.club, p: state.player, h: state.hand,
        s: r2(state.clubSpeed), a: r2(state.attack), pa: r2(state.path), f: r2(state.face), l: r2(state.dynLoft),
      });
      try { history.replaceState(null, "", location.pathname + "?" + q.toString()); } catch (e) { /* file:// or sandbox */ }
    }, 150);
  }

  // ---- compute -----------------------------------------------------------------
  function compute() {
    const sign = state.hand === "l" ? -1 : 1;
    const d = model.clampToDomain({
      clubSpeed: state.clubSpeed, attack: state.attack, path: sign * state.path, face: sign * state.face,
      dynLoft: state.dynLoft, club: state.club, spinTrim: state.spinTrim,
    });
    state.clubSpeed = round3(d.clubSpeed);
    state.attack = round3(d.attack);
    state.dynLoft = round3(d.dynLoft);
    state.path = round3(sign * d.path);
    state.face = round3(sign * d.face);
    const s = model.shot(d);
    const bands = model.idealBands(state.club, state.player, d.clubSpeed, d.attack);

    const values = {};
    for (const m of Object.keys(METRICS)) {
      const rh = metricValue(m, s);
      values[m] = { rh, disp: METRICS[m].lateral ? sign * rh + 0 : rh };
    }
    const f = s.flight;
    const n = f.x.length;
    const y = new Float64Array(n);
    for (let i = 0; i < n; i++) y[i] = sign * f.y[i] + 0;
    const rangeShot = {
      t: f.t, x: f.x, y, z: f.z, flightTime: f.flightTime, carry: f.carry, maxHeight: f.maxHeight,
      launchDir: sign * s.launch.launchDirDeg,
    };
    return { s, bands, values, rangeShot, sign };
  }

  // ---- range ---------------------------------------------------------------------
  const rangeRoot = $("#range");
  const range = createRange({ root: rangeRoot, canvas: $("#range-canvas"), model, avoidEl: $("#shot-label") });

  // ---- radio groups ---------------------------------------------------------------
  function radioGroup(container, onPick) {
    const items = () => [...container.querySelectorAll('[role="radio"]')];
    container.addEventListener("click", (e) => {
      const b = e.target.closest('[role="radio"]');
      if (b && container.contains(b)) onPick(b);
    });
    container.addEventListener("keydown", (e) => {
      const keys = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };
      if (!(e.key in keys)) return;
      const list = items();
      const i = list.indexOf(document.activeElement);
      if (i < 0) return;
      e.preventDefault();
      const next = list[(i + keys[e.key] + list.length) % list.length];
      next.focus();
      onPick(next);
    });
    return {
      set(pred) {
        for (const b of items()) {
          const on = pred(b);
          b.setAttribute("aria-checked", String(on));
          b.tabIndex = on ? 0 : -1;
        }
      },
    };
  }

  // ---- club and player controls ---------------------------------------------------
  const groupChips = $("#group-chips");
  const clubChips = $("#club-chips");
  const playerSeg = $("#player-seg");
  const handSeg = $("#hand-seg");
  const speedSeg = $("#speed-seg");

  groupChips.innerHTML = model.groups
    .map((g) => `<button type="button" class="chip" role="radio" aria-checked="false" data-group="${g.id}">${GROUP_LABEL[g.id] || g.name}</button>`)
    .join("");
  playerSeg.innerHTML = model.players
    .map((p) => `<button type="button" role="radio" aria-checked="false" data-player="${p.id}" title="${p.name}">${PLAYER_LABEL[p.id] || p.name}</button>`)
    .join("");

  const groupRadio = radioGroup(groupChips, (b) => {
    const g = b.dataset.group;
    if (g === clubById[state.club].group) return;
    changeClub(lastClubInGroup[g]);
  });
  const clubRadio = radioGroup(clubChips, (b) => changeClub(b.dataset.club));
  const playerRadio = radioGroup(playerSeg, (b) => {
    if (b.dataset.player === state.player) return;
    state.player = b.dataset.player;
    applyPreset(true);
    commitChange();
  });
  const handRadio = radioGroup(handSeg, (b) => {
    const h = b.dataset.hand;
    if (h === state.hand) return;
    // Flip the hand and mirror the swing so the same shot shows from the other side.
    state.hand = h;
    state.path = round3(-state.path);
    state.face = round3(-state.face);
    range.clearGhost();
    commitChange();
  });
  const speedRadio = radioGroup(speedSeg, (b) => {
    range.setSpeed(Number(b.dataset.speed));
    speedRadio.set((x) => x === b);
    range.replay();
  });

  speedRadio.set((b) => b.dataset.speed === "1");

  function changeClub(id) {
    state.club = id;
    lastClubInGroup[clubById[id].group] = id;
    applyPreset(true);
    commitChange();
  }

  function renderClubControls() {
    const g = clubById[state.club].group;
    groupRadio.set((b) => b.dataset.group === g);
    const clubs = model.clubs.filter((c) => c.group === g);
    clubChips.innerHTML = clubs.length > 1
      ? clubs.map((c) => `<button type="button" class="chip" role="radio" aria-checked="false" data-club="${c.id}">${c.name}</button>`).join("")
      : "";
    clubRadio.set((b) => b.dataset.club === state.club);
    playerRadio.set((b) => b.dataset.player === state.player);
    handRadio.set((b) => b.dataset.hand === state.hand);
    const note = model.preset(state.club, state.player).note;
    const noteEl = $("#preset-note");
    noteEl.hidden = !note;
    noteEl.textContent = note || "";
  }

  // ---- sliders --------------------------------------------------------------------
  const sliderEls = {};
  function buildSlider(cfg, container) {
    const id = "sl-" + cfg.key;
    const [lo, hi] = model.domain[cfg.dom];
    const wrap = el("div", "slider");
    const unitWord = cfg.unit === DEG ? " degrees" : " mph";
    wrap.innerHTML = `
      <div class="slider-head"><label for="${id}">${cfg.label}</label><output for="${id}" id="${id}-out"></output></div>
      <div class="slider-row">
        <button type="button" class="step" data-dir="-1" aria-label="Decrease ${cfg.label.toLowerCase()} by ${cfg.step}${unitWord}"><span aria-hidden="true">${MINUS}</span></button>
        <div class="track-wrap">
          <span class="track-base"></span><span class="band-hint"></span>${cfg.zero ? '<span class="zero-tick"></span>' : ""}
          <input type="range" id="${id}" min="${lo}" max="${hi}" step="any" value="0">
        </div>
        <button type="button" class="step" data-dir="1" aria-label="Increase ${cfg.label.toLowerCase()} by ${cfg.step}${unitWord}"><span aria-hidden="true">+</span></button>
      </div>
      ${cfg.hints ? '<div class="slider-hint"><span class="hl"></span><span class="hr"></span></div>' : ""}`;
    container.appendChild(wrap);
    const input = $("input", wrap);
    const out = $("output", wrap);
    const band = $(".band-hint", wrap);
    const zero = $(".zero-tick", wrap);
    if (zero) zero.style.left = `calc(1.375rem + ${(0 - lo) / (hi - lo)} * (100% - 2.75rem))`;
    const api = { cfg, input, out, band, wrap, lo, hi };
    sliderEls[cfg.key] = api;

    const setValue = (v, how) => {
      v = clamp(snap(v, cfg.step), lo, hi);
      if (v === state[cfg.key]) return;
      state[cfg.key] = v;
      liveChange();
      if (how === "commit") commitNow();
      else if (how === "soon") commitSoon(380);
    };
    const nudge = (dir) => {
      const cur = state[cfg.key];
      const q = cur / cfg.step;
      let v;
      if (dir > 0) v = (Math.floor(q + 1e-9) + 1) * cfg.step;
      else v = (Math.ceil(q - 1e-9) - 1) * cfg.step;
      v = clamp(round3(v), lo, hi);
      if (v === cur) return;
      state[cfg.key] = v;
      liveChange();
      commitSoon(380);
    };

    input.addEventListener("input", () => {
      const v = clamp(snap(parseFloat(input.value), cfg.step), lo, hi);
      if (v !== state[cfg.key]) { state[cfg.key] = v; liveChange(); }
    });
    input.addEventListener("change", commitNow);
    input.addEventListener("keydown", (e) => {
      const steps = { ArrowRight: 1, ArrowUp: 1, ArrowLeft: -1, ArrowDown: -1, PageUp: 5, PageDown: -5 };
      if (e.key in steps) {
        e.preventDefault();
        const n = steps[e.key] * (e.shiftKey ? 5 : 1);
        for (let i = 0; i < Math.abs(n); i++) nudge(Math.sign(n));
      } else if (e.key === "Home" || e.key === "End") {
        e.preventDefault();
        setValue(e.key === "Home" ? lo : hi, "soon");
      }
    });

    // Steppers: click, or hold to repeat.
    for (const btn of wrap.querySelectorAll(".step")) {
      const dir = Number(btn.dataset.dir);
      let hold = 0, rep = 0;
      const stop = () => { clearTimeout(hold); clearInterval(rep); };
      btn.addEventListener("pointerdown", (e) => {
        if (e.button !== undefined && e.button !== 0) return;
        nudge(dir);
        hold = setTimeout(() => { rep = setInterval(() => nudge(dir), 70); }, 420);
      });
      for (const ev of ["pointerup", "pointerleave", "pointercancel"]) btn.addEventListener(ev, stop);
      // Keyboard activation (Enter and Space fire click with no pointerdown).
      btn.addEventListener("click", (e) => { if (e.detail === 0) nudge(dir); });
      btn.addEventListener("contextmenu", (e) => e.preventDefault());
    }
    return api;
  }

  const slidersMain = $("#sliders");
  const slidersAdv = $("#sliders-adv");
  for (const cfg of SLIDERS) buildSlider(cfg, cfg.advanced ? slidersAdv : slidersMain);

  function renderSliders(c) {
    for (const cfg of SLIDERS) {
      const api = sliderEls[cfg.key];
      const v = state[cfg.key];
      if (document.activeElement !== api.input || Math.abs(parseFloat(api.input.value) - v) > 1e-6) api.input.value = v;
      const entry = c.values[cfg.metric];
      const text = fmt(v, cfg.dec, cfg.signed) + (cfg.unit === DEG ? DEG : cfg.unit);
      const word = METRICS[cfg.metric].words ? METRICS[cfg.metric].words(entry.rh, entry.disp) : "";
      api.out.innerHTML = `${text}${word ? `<span class="w">${word}</span>` : ""}`;
      api.input.setAttribute("aria-valuetext", `${text}${word ? ", " + word : ""}`);
      const b = c.bands[cfg.metric];
      if (b) {
        const span = api.hi - api.lo;
        const l = b.lo === null ? api.lo : b.lo;
        const h = b.hi === null ? api.hi : b.hi;
        api.band.style.setProperty("--p1", clamp((l - api.lo) / span, 0, 1));
        api.band.style.setProperty("--p2", clamp((h - api.lo) / span, 0, 1));
        api.band.hidden = false;
      }
      if (cfg.hints) {
        const [a, z] = cfg.hints(state.hand);
        $(".hl", api.wrap).textContent = a;
        $(".hr", api.wrap).textContent = z;
      }
    }
  }

  // ---- tiles ----------------------------------------------------------------------
  const tiles = [];
  const keyHost = $("#key-tiles");
  for (const k of KEY_TILES) {
    const t = createTile(k.metric, "k", k.extra ? "key-extra" : "");
    keyHost.appendChild(t.el);
    tiles.push(t);
  }
  const groupHost = $("#tile-groups");
  for (const g of TILE_GROUPS) {
    const sec = el("section", "tile-group");
    sec.innerHTML = `<h3>${g.name}<small>${g.note}</small></h3>`;
    const grid = el("div", "tile-grid");
    for (const m of g.items) {
      const t = createTile(m, "a", "");
      grid.appendChild(t.el);
      tiles.push(t);
    }
    sec.appendChild(grid);
    groupHost.appendChild(sec);
  }

  function renderTiles(c) {
    for (const t of tiles) t.update(c.values[t.metric], c.bands[t.metric], state.hand);
  }

  // ---- shot label -----------------------------------------------------------------
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
    $("#sl-name").textContent = name;
    $("#sl-finish").textContent = finish;
    $("#sl-line").textContent = cl ? `${start} · ${bend}` : "Raise dynamic loft or attack angle";
    $("#swing-summary").innerHTML = `<b></b><span>Path ${fmt(state.path, 1, true)}${DEG} \u00B7 Face ${fmt(state.face, 1, true)}${DEG}</span>`;
    $("#swing-summary b").textContent = name;
    $("#range-canvas").setAttribute("aria-label",
      cl ? `Range view. ${name}, carries ${Math.round(f.carry)} yards, ${finish}.` : "Range view. The ball goes into the ground.");
  }

  // ---- render and change flow -------------------------------------------------------
  let current = null;
  function render() {
    current = compute();
    renderClubControls();
    renderSliders(current);
    renderTiles(current);
    renderLabel(current);
    writeUrl();
  }
  function liveChange() {
    render();
    range.preview(current.rangeShot);
  }
  let commitTimer = 0;
  function commitNow() {
    clearTimeout(commitTimer);
    if (!current) return;
    range.commit(current.rangeShot);
  }
  function commitSoon(ms) {
    clearTimeout(commitTimer);
    commitTimer = setTimeout(commitNow, ms);
  }
  function commitChange() {
    render();
    range.setGroup(clubById[state.club].group);
    range.commit(current.rangeShot);
  }

  // ---- reset, hit, copy ------------------------------------------------------------
  for (const id of ["#reset-btn", "#reset-btn-2"]) {
    $(id).addEventListener("click", () => {
      applyPreset(false);
      commitChange();
    });
  }
  const hit = () => range.replay();
  $("#hit-btn").addEventListener("click", hit);
  $("#hit-btn-2").addEventListener("click", (e) => { e.stopPropagation(); hit(); });
  $("#ghost-check").addEventListener("change", (e) => range.setGhost(e.target.checked));

  const copyStatus = $("#copy-status");
  let copyTimer = 0;
  $("#copy-btn").addEventListener("click", async () => {
    writeUrl();
    await new Promise((r) => setTimeout(r, 200));
    const url = location.href;
    let ok = false;
    try { await navigator.clipboard.writeText(url); ok = true; } catch (e) {
      const ta = el("textarea");
      ta.value = url; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select();
      try { ok = document.execCommand("copy"); } catch (e2) { ok = false; }
      ta.remove();
    }
    copyStatus.textContent = ok ? "Link copied" : "Copy failed";
    clearTimeout(copyTimer);
    copyTimer = setTimeout(() => { copyStatus.textContent = ""; }, 2500);
  });

  // ---- drawer (single column layouts) ----------------------------------------------
  const swing = $("#swing");
  const toggle = $("#swing-toggle");
  const body = $("#swing-body");
  const mq = window.matchMedia("(max-width: 900px)");
  let drawerOpen = false;
  function applyDrawer() {
    const open = !mq.matches || drawerOpen;
    swing.dataset.open = String(open);
    toggle.setAttribute("aria-expanded", String(open));
    body.inert = !open;
    document.documentElement.style.setProperty("--drawer-h", mq.matches ? "64px" : "0px");
  }
  toggle.addEventListener("click", () => {
    if (!mq.matches) return;
    drawerOpen = !drawerOpen;
    applyDrawer();
    if (drawerOpen) {
      // Bring the range to the top of the screen so the drawer does not hide it.
      const top = rangeRoot.getBoundingClientRect().top + window.scrollY - 8;
      window.scrollTo({ top: Math.max(0, top), behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    }
  });
  mq.addEventListener("change", applyDrawer);
  applyDrawer();

  // ---- go ------------------------------------------------------------------------
  readUrl();
  render();
  range.setGroup(clubById[state.club].group);
  range.commit(current.rangeShot);
}

main().catch((err) => {
  console.error(err);
  $("#app-loading").hidden = true;
  $("#app-error").hidden = false;
});
