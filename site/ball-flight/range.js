/*
 * Range renderer for the ball flight lab.
 *
 * One canvas draws the painted range art and the shot over it. The art camera
 * (data/camera.json, wide and mobile) projects yards to art pixels:
 *   row(x) = h + (r0 - h) / (1 + x/d0)^p          (x clamped to >= 0)
 *   s(x)   = (row(x) - h) / z_eff                 px per yard for y and z
 *   t(x)   = (r0 - row(x)) / (r0 - h)
 *   u      = u0 + (uh - u0) * t(x) + y * s(x)
 *   v      = row(x) - z * s(x)
 * The view is a crop of the art (a rect in art pixels) scaled to the canvas.
 * The wide art uses the per-group zoom rects from camera.json. The mobile art has
 * none, so a crop is computed from the group's flights.
 *
 * Only the art for the current container shape loads (wide for landscape, mobile
 * for portrait). If it fails to load, the tracer still draws on a plain dusk
 * background and the overlay says so.
 *
 * Shots come in as {t, x, y, z, flightTime, carry, maxHeight, launchDir} with y
 * already in the display frame (positive is right of the target line, mirrored
 * for a left-handed golfer by the page). Colors come from CSS custom properties
 * on :root (see tool.css), so the palette lives in one place.
 */

const GROUP_VIEW_KEY = { driver: "driver", wood: "woods", long_iron: "long_iron", short_iron: "short_iron", wedge: "wedge" };
const ART_URL = {
  wide: new URL("../assets/img/004_range.jpg", import.meta.url).href,
  mobile: new URL("../assets/img/004_range_mobile.jpg", import.meta.url).href,
};
const ZOOM_MS = 650;
const START_DELAY_MS = 250;
const PULSE_MS = 800;
const MIN_FONT_PX = 12;

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const easeOutQuart = (p) => 1 - Math.pow(1 - p, 4);

export function createRange({ root, canvas, model, avoidEl }) {
  const ctx = canvas.getContext("2d");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  const rootStyle = getComputedStyle(document.documentElement);
  const token = (name, fallback) => rootStyle.getPropertyValue(name).trim() || fallback;
  const COL = {
    ink: token("--ink", "#1C1B18"),
    dusk: token("--dusk", "#231B3A"),
    dim: token("--range-dim", "rgba(14,9,26,.14)"),
    halo: token("--tracer-halo", "rgba(20,10,24,.30)"),
    glowOuter: token("--tracer-glow-outer", "rgba(255,138,61,.20)"),
    glowInner: token("--tracer-glow-inner", "rgba(255,170,90,.38)"),
    core: token("--tracer-core", "#FFF1DC"),
    pinHalo: token("--pin-halo", "rgba(10,18,34,.34)"),
    pinGlowOuter: token("--pin-glow-outer", "rgba(91,127,166,.30)"),
    pinGlowInner: token("--pin-glow-inner", "rgba(140,180,230,.45)"),
    pinCore: token("--pin-core", "#DCEBFF"),
    ghostHalo: token("--tracer-ghost-halo", "rgba(20,10,24,.22)"),
    ghost: token("--tracer-ghost", "rgba(255,238,215,.42)"),
    guide: token("--guide-line", "rgba(255,255,255,.62)"),
    shadow: token("--ground-shadow", "rgba(10,8,14,.32)"),
    ring: token("--tracer-ring", "rgba(255,241,220,.95)"),
    ball: token("--ball", "#FFFDF6"),
    plateBg: token("--plate-bg", "rgba(251,247,238,.96)"),
    plateInk: token("--plate-ink", "#1C1B18"),
    plateDarkBg: token("--plate-dark-bg", "rgba(28,27,24,.74)"),
    plateDarkInk: token("--plate-dark-ink", "#F4EDE0"),
    skyTop: token("--fallback-sky-top", "#2B2450"),
    skyLow: token("--fallback-sky-low", "#B4573A"),
    ground: token("--fallback-ground", "#26351F"),
  };

  const PAL = {
    warm: { halo: COL.halo, outer: COL.glowOuter, inner: COL.glowInner, core: COL.core },
    cool: { halo: COL.pinHalo, outer: COL.pinGlowOuter, inner: COL.pinGlowInner, core: COL.pinCore },
  };

  // ---- art (loaded on demand, one at a time) -------------------------------------
  const loadingEl = root.querySelector(".range-loading");
  function makeArt(key) {
    const c = model.camera[key];
    return { key, w: c.width, h: c.height, P: c.params, greens: c.greens, views: c.views || null, img: null, status: "idle", groupTop: {} };
  }
  const arts = { wide: makeArt("wide"), mobile: makeArt("mobile") };
  let art = arts.wide;

  function loadArt(a) {
    if (a.status !== "idle") return;
    a.status = "loading";
    a.img = new Image();
    a.img.onload = () => { a.status = "ready"; updateOverlay(); request(); };
    a.img.onerror = () => { a.status = "failed"; updateOverlay(); request(); };
    a.img.src = ART_URL[a.key];
  }

  /** The overlay text follows the active art: loading, gone when ready, an error when it failed. */
  function updateOverlay() {
    if (!loadingEl) return;
    const failed = art.status === "failed";
    loadingEl.classList.toggle("done", art.status === "ready");
    loadingEl.classList.toggle("failed", failed);
    loadingEl.setAttribute("aria-hidden", failed ? "false" : "true");
    if (failed) loadingEl.setAttribute("role", "status"); else loadingEl.removeAttribute("role");
    loadingEl.textContent = failed ? "The range picture did not load. The tracer still works." : "Loading the range…";
  }

  function project(a, x, y, z) {
    const P = a.P;
    const xx = x < 0 ? 0 : x;
    const row = P.h + (P.r0 - P.h) / Math.pow(1 + xx / P.d0, P.p);
    const s = (row - P.h) / P.z_eff;
    const t = (P.r0 - row) / (P.r0 - P.h);
    return [P.u0 + (P.uh - P.u0) * t + y * s, row - z * s, s];
  }

  // ---- view (crop of the art) ------------------------------------------------------
  let W = 300, H = 200, dpr = 1, k = 1;
  let uiScale = 1; // the page's root font size over 16px, so the canvas text grows on a TV
  let view = { l: 0, t: 0, w: 1376, h: 768 };
  let viewAnim = null;
  let group = "short_iron";

  function fitRect(a, r, A) {
    let { l, t, w, h } = r;
    const cx = l + w / 2, cy = t + h / 2;
    if (w / h < A) w = h * A; else h = w / A;
    if (w > a.w) { w = a.w; h = w / A; }
    if (h > a.h) { h = a.h; w = h * A; }
    l = clamp(cx - w / 2, 0, a.w - w);
    t = clamp(cy - h / 2, 0, a.h - h);
    return { l, t, w, h };
  }

  /** Smallest art row any flight in the group reaches (the highest point on screen). */
  function groupTopRow(a, g) {
    if (a.groupTop[g] !== undefined) return a.groupTop[g];
    let top = Infinity;
    for (const c of model.clubs) {
      if (c.group !== g) continue;
      for (const pl of model.players) {
        let s;
        try { s = model.shot(model.preset(c.id, pl.id)); } catch (e) { continue; }
        const f = s.flight;
        for (let i = 0; i < f.x.length; i += 4) {
          const v = project(a, f.x[i], 0, f.z[i])[1];
          if (v < top) top = v;
        }
      }
    }
    a.groupTop[g] = Number.isFinite(top) ? top : 300;
    return a.groupTop[g];
  }

  function viewFor(a, g, A) {
    if (a.key === "wide") {
      const v = a.views && a.views[GROUP_VIEW_KEY[g]];
      const r = v ? { l: v.rect[0], t: v.rect[1], w: v.rect[2] - v.rect[0], h: v.rect[3] - v.rect[1] } : { l: 0, t: 0, w: a.w, h: a.h };
      return fitRect(a, r, A);
    }
    const bottom = a.h - 28;
    const top = groupTopRow(a, g) - 55;
    let h = bottom - top;
    let w = h * A;
    if (w > a.w) { w = a.w; h = w / A; }
    if (h > bottom) { h = bottom; w = h * A; }
    return { l: clamp(a.P.u0 - w / 2, 0, a.w - w), t: bottom - h, w, h };
  }

  function setGroup(g) {
    if (g === group && !viewAnim) return;
    const changed = g !== group;
    group = g;
    const to = viewFor(art, group, W / H);
    if (changed) clearGhost();
    if (reduce.matches || !changed) { view = to; viewAnim = null; } else viewAnim = { from: { ...view }, to, t0: performance.now() };
    request();
  }

  // ---- size, DPR and cached rects ----------------------------------------------------
  let avoidRect = null; // label rect in canvas px, or null when it does not sit on the range

  function measureAvoid() {
    avoidRect = null;
    if (!avoidEl) return;
    const rr = root.getBoundingClientRect();
    const ar = avoidEl.getBoundingClientRect();
    if (!ar.width || ar.bottom <= rr.top || ar.top >= rr.bottom) return;
    const ox = rr.left + root.clientLeft, oy = rr.top + root.clientTop;
    avoidRect = { x: ar.left - ox - 6, y: ar.top - oy - 6, w: ar.width + 12, h: ar.height + 12 };
  }

  function applySize(w, h) {
    if (w < 2 || h < 2) return;
    W = w; H = h;
    dpr = Math.min(window.devicePixelRatio || 1, 3);
    uiScale = (parseFloat(getComputedStyle(document.documentElement).fontSize) || 16) / 16;
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    art = W / H < 1 ? arts.mobile : arts.wide;
    loadArt(art);
    updateOverlay();
    view = viewFor(art, group, W / H);
    viewAnim = null;
    layer = null;
    measureAvoid();
    request();
  }

  const ro = new ResizeObserver((entries) => {
    let sized = false;
    for (const e of entries) {
      if (e.target === root) { applySize(e.contentRect.width, e.contentRect.height); sized = true; }
    }
    if (!sized) { measureAvoid(); request(); }
  });
  ro.observe(root);
  if (avoidEl) ro.observe(avoidEl);

  // The device pixel ratio changes on zoom or when the window moves screens.
  let dprQuery = null;
  function watchDpr() {
    if (dprQuery) dprQuery.removeEventListener("change", onDpr);
    dprQuery = window.matchMedia(`(resolution: ${window.devicePixelRatio || 1}dppx)`);
    dprQuery.addEventListener("change", onDpr);
  }
  function onDpr() {
    applySize(W, H);
    watchDpr();
  }
  watchDpr();

  // ---- shots ---------------------------------------------------------------------------
  let cur = null;        // shot on screen
  let committed = null;  // last committed shot
  let ghostShot = null;  // shot drawn dimmed
  let ghostOn = true;
  let mode = "settled";  // "playing" | "settled"
  let t0 = 0, speed = 1, landedAt = null;
  let pinned = null;     // Compare mode: shot A, drawn in the cool palette
  let liveTag = "";      // Compare mode: "B", shown on the live shot's carry plate
  let collection = [];   // shots that stay drawn after they have flown (Fly all nine)
  let seq = null;        // a running sequence: {items, i, speed, onStep, onEnd}

  function prep(s) {
    const n = s.x.length;
    let ai = 0;
    for (let i = 1; i < n; i++) if (s.z[i] > s.z[ai]) ai = i;
    return { ...s, n, apexIdx: ai, topIdx: ai, key: null, pj: null, gr: null, guide: null };
  }

  function ensureProj(s) {
    if (s.key === art.key) return;
    s.key = art.key;
    s.pj = new Float32Array(2 * s.n);
    s.gr = new Float32Array(2 * s.n);
    let top = 0;
    for (let i = 0; i < s.n; i++) {
      const p = project(art, s.x[i], s.y[i], s.z[i]);
      s.pj[2 * i] = p[0]; s.pj[2 * i + 1] = p[1];
      if (p[1] < s.pj[2 * top + 1]) top = i;
      const g = project(art, s.x[i], s.y[i], 0);
      s.gr[2 * i] = g[0]; s.gr[2 * i + 1] = g[1];
    }
    s.topIdx = top; // the visually highest point of the tracer, which is not always the true apex
    const tan = Math.tan((s.launchDir * Math.PI) / 180);
    const m = 28;
    s.guide = new Float32Array(2 * (m + 1));
    for (let i = 0; i <= m; i++) {
      const x = (s.carry * i) / m;
      const p = project(art, x, x * tan, 0);
      s.guide[2 * i] = p[0]; s.guide[2 * i + 1] = p[1];
    }
  }

  function clearGhost() { committed = null; ghostShot = null; }

  /** Stop a running sequence and clear the shots it left on the range. */
  function cancelSequence() {
    const was = seq;
    seq = null;
    collection = [];
    if (was && was.onEnd) was.onEnd(true);
  }

  /** Draw a shot in full without animation and without touching the ghost. */
  function preview(shot) {
    cancelSequence();
    cur = prep(shot);
    ghostShot = committed;
    mode = "settled";
    landedAt = null;
    request();
  }

  /** Make a shot the current one and fly it. The previous committed shot becomes the ghost. */
  function commit(shot, opts = {}) {
    cancelSequence();
    cur = prep(shot);
    ghostShot = committed;
    committed = cur;
    if (opts.animate === false) settle(); else play();
  }

  function settle() { mode = "settled"; landedAt = null; request(); }

  /**
   * Fly a list of {shot, label} one after another. Each shot stays on the range
   * when it lands, so all of them show at once. The ghost is off while they show.
   * opts: speed (playback multiplier), onStep(i, item), onEnd(cancelled).
   */
  function playSequence(items, opts = {}) {
    cancelSequence();
    committed = null;
    ghostShot = null;
    seq = { items, i: -1, speed: opts.speed || 2.5, onStep: opts.onStep, onEnd: opts.onEnd };
    if (reduce.matches) {
      // Reduced motion: everything settled at once.
      collection = items.slice(0, -1).map((it) => Object.assign(prep(it.shot), { label: it.label }));
      const last = items[items.length - 1];
      cur = Object.assign(prep(last.shot), { label: last.label });
      mode = "settled";
      const done = seq;
      seq = null;
      if (done.onStep) done.onStep(items.length - 1, last);
      if (done.onEnd) done.onEnd(false);
      request();
      return;
    }
    seqNext();
  }

  function seqNext() {
    if (!seq) return;
    if (cur && seq.i >= 0) collection.push(cur);
    seq.i += 1;
    if (seq.i >= seq.items.length) {
      const done = seq;
      seq = null;
      // The last shot stays as the current one. Take it back off the collection.
      collection.pop();
      if (done.onEnd) done.onEnd(false);
      request();
      return;
    }
    const it = seq.items[seq.i];
    cur = Object.assign(prep(it.shot), { label: it.label });
    mode = "playing";
    t0 = performance.now() + 150;
    landedAt = null;
    if (seq.onStep) seq.onStep(seq.i, it);
    request();
  }

  const pulseMs = () => (seq ? 350 : PULSE_MS);

  function play() {
    if (!cur) return;
    if (seq) return;
    if (reduce.matches) { settle(); return; }
    mode = "playing";
    t0 = performance.now() + START_DELAY_MS;
    landedAt = null;
    request();
  }

  // ---- drawing helpers ---------------------------------------------------------------
  const sx = (u) => (u - view.l) * k;
  const sy = (v) => (v - view.t) * k;

  /** Largest index i with t[i] <= tt. */
  function indexAt(s, tt) {
    let lo = 0, hi = s.n - 1;
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (s.t[mid] <= tt) lo = mid; else hi = mid - 1;
    }
    return lo;
  }

  /** Path the series up to time tt. Returns the head in canvas px. */
  function trace(s, pts, tt) {
    const i = indexAt(s, tt);
    ctx.beginPath();
    ctx.moveTo(sx(pts[0]), sy(pts[1]));
    for (let j = 1; j <= i; j++) ctx.lineTo(sx(pts[2 * j]), sy(pts[2 * j + 1]));
    let hx = sx(pts[2 * i]), hy = sy(pts[2 * i + 1]);
    if (i < s.n - 1 && tt > s.t[i]) {
      const f = (tt - s.t[i]) / (s.t[i + 1] - s.t[i]);
      hx = sx(pts[2 * i] + f * (pts[2 * i + 2] - pts[2 * i]));
      hy = sy(pts[2 * i + 1] + f * (pts[2 * i + 3] - pts[2 * i + 1]));
      ctx.lineTo(hx, hy);
    }
    return [hx, hy];
  }

  function roundRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  // Plates are placed first (so the shot's plates get the best spots and the
  // green plates fill in around them) and drawn last, on top of the tracer.
  /** "176 carry \u00B7 185 total", with a tag such as "B" in Compare. Total is left off when the shot has none. */
  const carryText = (s, tag) => `${tag ? tag + " \u00B7 " : ""}${Math.round(s.carry)} carry${s.total !== undefined ? ` \u00B7 ${Math.round(s.total)} total` : ""}`;
  let taken = [];
  let linePts = [];
  const overlaps = (a, b) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
  const fontFor = (fs) => `500 ${fs}px "IBM Plex Mono", ui-monospace, Menlo, monospace`;

  /**
   * Find a spot for a plate near (ax, ay). A spot is free when it overlaps no
   * other plate and no tracer point. If none is free, a required plate takes its
   * first choice and an optional plate is skipped (returns null).
   */
  function placePlate(text, ax, ay, dirs, fs, required) {
    ctx.font = fontFor(fs);
    const w = ctx.measureText(text).width + fs * 1.1;
    const h = fs * 1.75;
    const gap = fs * 0.85;
    const cands = {
      above: [ax - w / 2, ay - gap - h],
      below: [ax - w / 2, ay + gap],
      right: [ax + gap, ay - h / 2],
      left: [ax - gap - w, ay - h / 2],
      right2: [ax + gap + 36, ay - h / 2],
      left2: [ax - gap - 36 - w, ay - h / 2],
    };
    const rects = dirs.map((d) => {
      const c = cands[d];
      return { x: clamp(c[0], 4, W - w - 4), y: clamp(c[1], 4, H - h - 4), w, h };
    });
    const blocked = (r) => taken.some((t) => overlaps(r, t));
    const crossed = (r) => linePts.some((p) => p[0] > r.x - 4 && p[0] < r.x + w + 4 && p[1] > r.y - 4 && p[1] < r.y + h + 4);
    // Best spot first (clear of plates and the tracer). A required plate then
    // settles for a spot clear of other plates that the tracer crosses, and
    // last for its first choice.
    let r = rects.find((c) => !blocked(c) && !crossed(c));
    // A required plate never settles under the shot label: it takes a spot the tracer crosses before one the label covers.
    const underLabel = (c) => !!avoidRect && overlaps(c, avoidRect);
    if (!r && required) r = rects.find((c) => !blocked(c)) || rects.find((c) => !underLabel(c)) || rects[0];
    if (!r) return null;
    taken.push(r);
    return { r, text, fs };
  }

  function drawPlate(p, dark) {
    const { r, text, fs } = p;
    roundRect(r.x, r.y, r.w, r.h, r.h / 2);
    ctx.font = fontFor(fs);
    if (dark) {
      ctx.fillStyle = COL.plateDarkBg;
      ctx.fill();
      ctx.fillStyle = COL.plateDarkInk;
    } else {
      ctx.fillStyle = COL.plateBg;
      ctx.fill();
      ctx.lineWidth = 1;
      ctx.strokeStyle = COL.ink;
      ctx.stroke();
      ctx.fillStyle = COL.plateInk;
    }
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(text, r.x + r.w / 2, r.y + r.h / 2 + fs * 0.05);
  }

  const ghostVisible = () => ghostOn && !!ghostShot && !seq && collection.length === 0;

  /** Screen points along the shots, so plates stay off the tracer. */
  function collectLinePts() {
    const out = [];
    for (const s of [cur, ghostVisible() ? ghostShot : null, pinned, ...collection]) {
      if (!s) continue;
      ensureProj(s);
      for (let i = 0; i < s.n; i += 3) out.push([sx(s.pj[2 * i]), sy(s.pj[2 * i + 1])]);
    }
    return out;
  }

  function strokeTracer(lw, pal = PAL.warm) {
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.setLineDash([]);
    ctx.strokeStyle = pal.halo; ctx.lineWidth = lw * 2.6; ctx.stroke();
    ctx.strokeStyle = pal.outer; ctx.lineWidth = lw * 3.6; ctx.stroke();
    ctx.strokeStyle = pal.inner; ctx.lineWidth = lw * 2.1; ctx.stroke();
    ctx.strokeStyle = pal.core; ctx.lineWidth = lw; ctx.stroke();
  }

  /** A shot drawn whole and at rest: the pinned shot A, and every shot of a sequence that has landed. */
  function drawResting(s, lw, pal) {
    ensureProj(s);
    trace(s, s.pj, s.flightTime);
    strokeTracer(lw * 0.85, pal);
    const lx = sx(s.pj[2 * (s.n - 1)]), ly = sy(s.pj[2 * (s.n - 1) + 1]);
    const br = clamp(W / 150, 4, 9 * uiScale);
    ctx.beginPath(); ctx.ellipse(lx, ly, br * 2.1, br * 0.8, 0, 0, Math.PI * 2);
    ctx.lineWidth = 2; ctx.strokeStyle = pal.core; ctx.stroke();
    ballDot(lx, ly, br * 0.6, false);
    return [lx, ly];
  }

  function ballDot(x, y, r, glow) {
    if (glow) {
      const g = ctx.createRadialGradient(x, y, 0, x, y, r * 3.2);
      g.addColorStop(0, COL.glowInner);
      g.addColorStop(1, "rgba(255,150,70,0)");
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(x, y, r * 3.2, 0, Math.PI * 2); ctx.fill();
    }
    ctx.fillStyle = COL.ball;
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
    ctx.lineWidth = 1.2;
    ctx.strokeStyle = COL.halo;
    ctx.stroke();
  }

  function drawGhost(lw) {
    const s = ghostShot;
    ensureProj(s);
    trace(s, s.pj, s.flightTime);
    ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.setLineDash([]);
    ctx.strokeStyle = COL.ghostHalo; ctx.lineWidth = lw * 1.9; ctx.stroke();
    ctx.strokeStyle = COL.ghost; ctx.lineWidth = lw * 0.8; ctx.stroke();
    const lx = sx(s.pj[2 * (s.n - 1)]), ly = sy(s.pj[2 * (s.n - 1) + 1]);
    const r = clamp(W / 190, 3, 7);
    ctx.beginPath(); ctx.ellipse(lx, ly, r * 1.6, r * 0.6, 0, 0, Math.PI * 2);
    ctx.strokeStyle = COL.ghost; ctx.lineWidth = 1.5; ctx.stroke();
  }

  // ---- the art layer, cached per view ----------------------------------------------------
  let layer = null; // {key, canvas}
  function drawArtDirect(g) {
    if (art.status === "ready") {
      g.drawImage(art.img, view.l, view.t, view.w, view.h, 0, 0, W, H);
      g.fillStyle = COL.dim;
      g.fillRect(0, 0, W, H);
      return;
    }
    // Fallback: a plain dusk sky over dark grass, split at the camera horizon.
    const horizon = clamp(sy(art.P.h), 0, H);
    const sky = g.createLinearGradient(0, 0, 0, horizon);
    sky.addColorStop(0, COL.skyTop);
    sky.addColorStop(1, COL.skyLow);
    g.fillStyle = sky;
    g.fillRect(0, 0, W, horizon);
    g.fillStyle = COL.ground;
    g.fillRect(0, horizon, W, H - horizon);
  }
  function drawArtLayer() {
    if (viewAnim) { drawArtDirect(ctx); return; } // the view moves every frame during a zoom
    const key = `${art.key}|${art.status}|${view.l}|${view.t}|${view.w}|${W}|${H}|${dpr}`;
    if (!layer || layer.key !== key) {
      const c = document.createElement("canvas");
      c.width = canvas.width;
      c.height = canvas.height;
      const g = c.getContext("2d");
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
      g.imageSmoothingQuality = "high";
      drawArtDirect(g);
      layer = { key, canvas: c };
    }
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.drawImage(layer.canvas, 0, 0);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  // ---- one shot ----------------------------------------------------------------------------
  function drawShot(now, lw, fs) {
    const s = cur;
    ensureProj(s);
    let tt = s.flightTime;
    if (mode === "playing") {
      const p = ((now - t0) / 1000) * (seq ? seq.speed : speed);
      tt = clamp(p, 0, s.flightTime);
      if (p >= s.flightTime && landedAt === null) landedAt = now;
    }
    const landed = tt >= s.flightTime;
    const ai = s.apexIdx, ti = s.topIdx;
    const topShown = tt >= Math.max(s.t[ai], s.t[ti]);
    const settled = mode !== "playing";

    // start line guide
    ctx.beginPath();
    ctx.moveTo(sx(s.guide[0]), sy(s.guide[1]));
    for (let i = 1; i < s.guide.length / 2; i++) ctx.lineTo(sx(s.guide[2 * i]), sy(s.guide[2 * i + 1]));
    ctx.lineCap = "butt";
    ctx.setLineDash([lw * 2.6, lw * 2.6]);
    ctx.lineWidth = Math.max(1.5, lw * 0.55);
    ctx.strokeStyle = COL.guide;
    ctx.stroke();
    ctx.setLineDash([]);

    // ground shadow
    trace(s, s.gr, tt);
    ctx.lineCap = "round"; ctx.lineJoin = "round";
    ctx.lineWidth = Math.max(1.5, lw * 0.9);
    ctx.strokeStyle = COL.shadow;
    ctx.stroke();

    // apex drop line
    const au = sx(s.pj[2 * ai]), av = sy(s.pj[2 * ai + 1]);
    const tu = sx(s.pj[2 * ti]), tv = sy(s.pj[2 * ti + 1]);
    if (topShown) {
      ctx.beginPath();
      ctx.moveTo(au, av);
      ctx.lineTo(sx(s.gr[2 * ai]), sy(s.gr[2 * ai + 1]));
      ctx.setLineDash([2, 4]);
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = COL.ring;
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // tracer
    const head = trace(s, s.pj, tt);
    strokeTracer(lw);

    // landing marker
    const li = s.n - 1;
    const lx = sx(s.pj[2 * li]), ly = sy(s.pj[2 * li + 1]);
    const br = clamp(W / 150, 4, 9 * uiScale);
    if (landed) {
      const rx = br * 2.4, ry = rx * 0.38;
      ctx.beginPath(); ctx.ellipse(lx, ly, rx, ry, 0, 0, Math.PI * 2);
      ctx.lineWidth = 2; ctx.strokeStyle = COL.ring; ctx.stroke();
      if (landedAt !== null && !reduce.matches) {
        const pp = clamp((now - landedAt) / pulseMs(), 0, 1);
        if (pp < 1) {
          const grow = 1 + easeOutQuart(pp) * 1.8;
          ctx.beginPath(); ctx.ellipse(lx, ly, rx * grow, ry * grow, 0, 0, Math.PI * 2);
          ctx.globalAlpha = 0.8 * (1 - pp);
          ctx.lineWidth = 2; ctx.strokeStyle = COL.ring; ctx.stroke();
          ctx.globalAlpha = 1;
        }
      }
    }

    // ball
    if (!landed) ballDot(head[0], head[1], br, true);
    else ballDot(lx, ly, br * 0.7, false);

    // apex ring at the true maximum height. When the visually highest tracer
    // point sits elsewhere, a thin connector joins the two.
    if (topShown) {
      ctx.beginPath(); ctx.arc(au, av, br * 1.25, 0, Math.PI * 2);
      ctx.lineWidth = 2; ctx.strokeStyle = COL.ring; ctx.stroke();
      if (Math.hypot(tu - au, tv - av) > br * 1.5) {
        ctx.beginPath(); ctx.moveTo(au, av); ctx.lineTo(tu, tv);
        ctx.lineWidth = 1; ctx.strokeStyle = COL.ring; ctx.stroke();
      }
    }

    // plates: placed as if everything were shown so nothing jumps when it appears
    const heightPlate = placePlate(`${Math.round(s.maxHeight * 3)} ft high`, tu, tv, ["above", "right", "left", "right2", "left2", "below"], fs, true);
    const carryPlate = placePlate(carryText(s, liveTag), lx, ly, ["below", "right", "left", "right2", "left2", "above"], fs, true);
    return { settled, landed, topShown, heightPlate, carryPlate };
  }

  // ---- frame loop --------------------------------------------------------------------------
  let raf = 0;
  function request() { if (!raf) raf = requestAnimationFrame(frame); }

  function frame(now) {
    raf = 0;
    let busy = false;
    if (viewAnim) {
      const p = clamp((now - viewAnim.t0) / ZOOM_MS, 0, 1);
      const e = easeOutQuart(p);
      const a = viewAnim.from, b = viewAnim.to;
      view = { l: a.l + (b.l - a.l) * e, t: a.t + (b.t - a.t) * e, w: a.w + (b.w - a.w) * e, h: a.h + (b.h - a.h) * e };
      if (p >= 1) { view = b; viewAnim = null; } else busy = true;
    }
    k = W / view.w;

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    ctx.imageSmoothingQuality = "high";
    drawArtLayer();

    const lw = clamp(W / 240, 2.4, 6 * uiScale);
    const fs = clamp(W / 80, MIN_FONT_PX, 17 * uiScale);
    taken = avoidRect ? [avoidRect] : [];
    linePts = collectLinePts();

    if (ghostVisible() && ghostShot !== cur) drawGhost(lw);
    const restingPlates = [];
    for (const s of collection) {
      const [lx, ly] = drawResting(s, lw, PAL.warm);
      if (s.label) restingPlates.push({ text: s.label, x: lx, y: ly, dirs: ["below", "right", "left", "above", "right2", "left2"], required: true });
    }
    if (pinned) {
      const [lx, ly] = drawResting(pinned, lw, PAL.cool);
      restingPlates.push({ text: carryText(pinned, pinned.tag || "A"), x: lx, y: ly, dirs: ["left", "above", "right", "below"], cool: true, required: true });
    }
    let shotState = null;
    if (cur) {
      shotState = drawShot(now, lw, fs);
      if (!shotState.settled || (landedAt !== null && now - landedAt <= pulseMs())) busy = true;
      if (mode === "playing" && landedAt !== null && now - landedAt > pulseMs()) {
        mode = "settled";
        if (seq) { seqNext(); busy = true; }
      }
    }
    // Resting plates place after the live shot's, before the greens.
    const placedResting = restingPlates.map((p) => ({ p: placePlate(p.text, p.x, p.y, p.dirs, fs, !!p.required), cool: p.cool })).filter((x) => x.p);

    // Plates go on top of the tracer. Shot plates were placed first, so the
    // green plates take what is left and skip a spot when none is free.
    if (art.greens) {
      for (const g of art.greens) {
        const x = sx(g.pixel[0]), y = sy(g.pixel[1]);
        if (x < 0 || x > W || y < 0 || y > H) continue;
        const p = placePlate(`${g.yardage} yd`, x, y, ["above", "right", "left", "right2", "left2", "below"], fs, false);
        if (p) drawPlate(p, true);
      }
    }
    for (const x of placedResting) drawPlate(x.p, false);
    if (shotState) {
      if (shotState.topShown && shotState.heightPlate) drawPlate(shotState.heightPlate, false);
      if (shotState.landed && shotState.carryPlate) drawPlate(shotState.carryPlate, false);
    }
    if (busy) request();
  }

  // ---- lifecycle ------------------------------------------------------------------------------
  if (reduce.addEventListener) reduce.addEventListener("change", () => { if (reduce.matches) settle(); });
  // A hidden tab pauses animation frames. Show the settled shot instead of a half flight on return.
  document.addEventListener("visibilitychange", () => { if (document.hidden && mode === "playing") settle(); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(request);

  return {
    preview,
    commit,
    replay: play,
    setGroup,
    clearGhost,
    setSpeed(n) { speed = n; },
    setGhost(on) { ghostOn = on; request(); },
    playSequence,
    cancelSequence,
    /** Compare mode: freeze a shot as A (or pass null to clear). */
    setPinned(shot, tag) { pinned = shot ? Object.assign(prep(shot), { tag }) : null; request(); },
    setLiveTag(text) { liveTag = text || ""; request(); },
    /** The dimmed shot, or null when none shows. Views draw it too. */
    get ghost() { return ghostVisible() ? ghostShot : null; },
    get sequencing() { return !!seq; },
    redraw() { uiScale = (parseFloat(getComputedStyle(document.documentElement).fontSize) || 16) / 16; request(); },
    get artKey() { return art.key; },
    get artStatus() { return art.status; },
  };
}
