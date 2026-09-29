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
 * The wide art uses the per-group zoom rects from camera.json. The mobile art
 * has none, so a crop is computed from the group's flights.
 *
 * Shots come in as {t, x, y, z, flightTime, carry, maxHeight, launchDir, ...}
 * with y already in the display frame (positive is right of the target line,
 * mirrored for a left-handed golfer by the page).
 */

const GROUP_VIEW_KEY = { driver: "driver", wood: "woods", long_iron: "long_iron", short_iron: "short_iron", wedge: "wedge" };
const ART_URL = {
  wide: new URL("../assets/img/004_range.png", import.meta.url).href,
  mobile: new URL("../assets/img/004_range_mobile.png", import.meta.url).href,
};
const ZOOM_MS = 650;
const START_DELAY_MS = 250;
const PULSE_MS = 800;

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const easeOutQuart = (p) => 1 - Math.pow(1 - p, 4);

export function createRange({ root, canvas, model, avoidEl }) {
  const ctx = canvas.getContext("2d");
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  const rootStyle = getComputedStyle(document.documentElement);
  const token = (name, fallback) => rootStyle.getPropertyValue(name).trim() || fallback;
  const COL = { ink: token("--ink", "#1C1B18"), card: token("--card", "#FBF7EE") };

  // ---- art -----------------------------------------------------------------
  function makeArt(key) {
    const c = model.camera[key];
    const art = { key, w: c.width, h: c.height, P: c.params, greens: c.greens, views: c.views || null, img: new Image(), ready: false, groupTop: {} };
    art.img.onload = () => {
      art.ready = true;
      loadingEl && loadingEl.classList.add("done");
      request();
    };
    art.img.src = ART_URL[key];
    return art;
  }
  const loadingEl = root.querySelector(".range-loading");
  const arts = { wide: makeArt("wide"), mobile: makeArt("mobile") };
  let art = arts.wide;

  function project(a, x, y, z) {
    const P = a.P;
    const xx = x < 0 ? 0 : x;
    const row = P.h + (P.r0 - P.h) / Math.pow(1 + xx / P.d0, P.p);
    const s = (row - P.h) / P.z_eff;
    const t = (P.r0 - row) / (P.r0 - P.h);
    return [P.u0 + (P.uh - P.u0) * t + y * s, row - z * s, s];
  }

  // ---- view (crop of the art) -----------------------------------------------
  let W = 300, H = 200, dpr = 1, k = 1;
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

  // ---- layout ----------------------------------------------------------------
  function layout() {
    const r = root.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return;
    W = r.width; H = r.height;
    dpr = Math.min(window.devicePixelRatio || 1, 3);
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    art = W / H < 1 ? arts.mobile : arts.wide;
    view = viewFor(art, group, W / H);
    viewAnim = null;
    request();
  }
  new ResizeObserver(layout).observe(root);

  // ---- shots -----------------------------------------------------------------
  let cur = null;        // shot on screen
  let committed = null;  // last committed shot
  let ghostShot = null;  // shot drawn dimmed
  let ghostOn = true;
  let mode = "settled";  // "playing" | "settled"
  let t0 = 0, speed = 1, landedAt = null;

  function prep(s) {
    const n = s.x.length;
    let ai = 0;
    for (let i = 1; i < n; i++) if (s.z[i] > s.z[ai]) ai = i;
    return { ...s, n, apexIdx: ai, key: null, pj: null, gr: null, guide: null };
  }

  function ensureProj(s) {
    if (s.key === art.key) return;
    s.key = art.key;
    s.pj = new Float32Array(2 * s.n);
    s.gr = new Float32Array(2 * s.n);
    for (let i = 0; i < s.n; i++) {
      const p = project(art, s.x[i], s.y[i], s.z[i]);
      s.pj[2 * i] = p[0]; s.pj[2 * i + 1] = p[1];
      const g = project(art, s.x[i], s.y[i], 0);
      s.gr[2 * i] = g[0]; s.gr[2 * i + 1] = g[1];
    }
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

  /** Draw a shot in full without animation and without touching the ghost. */
  function preview(shot) {
    cur = prep(shot);
    ghostShot = committed;
    mode = "settled";
    landedAt = null;
    request();
  }

  /** Make a shot the current one and fly it. The previous committed shot becomes the ghost. */
  function commit(shot, opts = {}) {
    cur = prep(shot);
    ghostShot = committed;
    committed = cur;
    if (opts.animate === false) settle(); else play();
  }

  function settle() { mode = "settled"; landedAt = null; request(); }

  function play() {
    if (!cur) return;
    if (reduce.matches) { settle(); return; }
    mode = "playing";
    t0 = performance.now() + START_DELAY_MS;
    landedAt = null;
    request();
  }

  // ---- drawing helpers -------------------------------------------------------
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

  let taken = [];
  const overlaps = (a, b) => a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;

  function roundRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function plate(text, ax, ay, dirs, fs, dark, pts) {
    ctx.font = `500 ${fs}px "IBM Plex Mono", ui-monospace, Menlo, monospace`;
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
    let best = null;
    for (const d of dirs) {
      const c = cands[d];
      const r = { x: clamp(c[0], 4, W - w - 4), y: clamp(c[1], 4, H - h - 4), w, h };
      const hitsLine = pts && pts.some((p) => p[0] > r.x - 4 && p[0] < r.x + w + 4 && p[1] > r.y - 4 && p[1] < r.y + h + 4);
      if (!hitsLine && !taken.some((t) => overlaps(r, t))) { best = r; break; }
      if (!best) best = r;
    }
    taken.push(best);
    roundRect(best.x, best.y, w, h, h / 2);
    if (dark) {
      ctx.fillStyle = "rgba(28,27,24,.74)";
      ctx.fill();
      ctx.fillStyle = "#F4EDE0";
    } else {
      ctx.fillStyle = "rgba(251,247,238,.96)";
      ctx.fill();
      ctx.lineWidth = 1;
      ctx.strokeStyle = COL.ink;
      ctx.stroke();
      ctx.fillStyle = COL.ink;
    }
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(text, best.x + w / 2, best.y + h / 2 + fs * 0.05);
  }

  /** Screen points along the shots, so the green plates can stay off the tracer. */
  function linePoints() {
    const out = [];
    for (const s of [cur, ghostOn ? ghostShot : null]) {
      if (!s) continue;
      ensureProj(s);
      for (let i = 0; i < s.n; i += 3) out.push([sx(s.pj[2 * i]), sy(s.pj[2 * i + 1])]);
    }
    return out;
  }

  function drawGreens(fs) {
    const pts = linePoints();
    for (const g of art.greens) {
      const x = sx(g.pixel[0]), y = sy(g.pixel[1]);
      if (x < 0 || x > W || y < 0 || y > H) continue;
      plate(`${g.yardage} yd`, x, y, ["above", "right", "left", "right2", "left2", "below"], fs, true, pts);
    }
  }

  const TRACER = { halo: "rgba(20,10,24,.30)", glowOuter: "rgba(255,138,61,.20)", glowInner: "rgba(255,170,90,.38)", core: "#FFF1DC" };

  function strokeTracer(lw) {
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.setLineDash([]);
    ctx.strokeStyle = TRACER.halo; ctx.lineWidth = lw * 2.6; ctx.stroke();
    ctx.strokeStyle = TRACER.glowOuter; ctx.lineWidth = lw * 3.6; ctx.stroke();
    ctx.strokeStyle = TRACER.glowInner; ctx.lineWidth = lw * 2.1; ctx.stroke();
    ctx.strokeStyle = TRACER.core; ctx.lineWidth = lw; ctx.stroke();
  }

  function ballDot(x, y, r, glow) {
    if (glow) {
      const g = ctx.createRadialGradient(x, y, 0, x, y, r * 3.2);
      g.addColorStop(0, "rgba(255,190,110,.75)");
      g.addColorStop(1, "rgba(255,150,70,0)");
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(x, y, r * 3.2, 0, Math.PI * 2); ctx.fill();
    }
    ctx.fillStyle = "#FFFDF6";
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
    ctx.lineWidth = 1.2;
    ctx.strokeStyle = "rgba(28,27,24,.55)";
    ctx.stroke();
  }

  function drawGhost(lw) {
    const s = ghostShot;
    ensureProj(s);
    trace(s, s.pj, s.flightTime);
    ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.setLineDash([]);
    ctx.strokeStyle = "rgba(20,10,24,.22)"; ctx.lineWidth = lw * 1.9; ctx.stroke();
    ctx.strokeStyle = "rgba(255,238,215,.42)"; ctx.lineWidth = lw * 0.8; ctx.stroke();
    const lx = sx(s.pj[2 * (s.n - 1)]), ly = sy(s.pj[2 * (s.n - 1) + 1]);
    const r = clamp(W / 190, 3, 7);
    ctx.beginPath(); ctx.ellipse(lx, ly, r * 1.6, r * 0.6, 0, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(255,238,215,.55)"; ctx.lineWidth = 1.5; ctx.stroke();
  }

  function drawShot(now, lw, fs) {
    const s = cur;
    ensureProj(s);
    let tt = s.flightTime;
    if (mode === "playing") {
      const p = ((now - t0) / 1000) * speed;
      tt = clamp(p, 0, s.flightTime);
      if (p >= s.flightTime && landedAt === null) landedAt = now;
    }
    const landed = tt >= s.flightTime;
    const apexShown = tt >= s.t[s.apexIdx];
    const settled = mode !== "playing";

    // start line guide
    ctx.beginPath();
    ctx.moveTo(sx(s.guide[0]), sy(s.guide[1]));
    for (let i = 1; i < s.guide.length / 2; i++) ctx.lineTo(sx(s.guide[2 * i]), sy(s.guide[2 * i + 1]));
    ctx.lineCap = "butt";
    ctx.setLineDash([lw * 2.6, lw * 2.6]);
    ctx.lineWidth = Math.max(1.5, lw * 0.55);
    ctx.strokeStyle = "rgba(255,255,255,.62)";
    ctx.stroke();
    ctx.setLineDash([]);

    // ground shadow
    trace(s, s.gr, tt);
    ctx.lineCap = "round"; ctx.lineJoin = "round";
    ctx.lineWidth = Math.max(1.5, lw * 0.9);
    ctx.strokeStyle = "rgba(10,8,14,.32)";
    ctx.stroke();

    // apex drop line and marker
    const ai = s.apexIdx;
    const au = sx(s.pj[2 * ai]), av = sy(s.pj[2 * ai + 1]);
    if (apexShown) {
      ctx.beginPath();
      ctx.moveTo(au, av);
      ctx.lineTo(sx(s.gr[2 * ai]), sy(s.gr[2 * ai + 1]));
      ctx.setLineDash([2, 4]);
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = "rgba(255,241,220,.7)";
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // tracer
    const head = trace(s, s.pj, tt);
    strokeTracer(lw);

    // landing marker
    const li = s.n - 1;
    const lx = sx(s.pj[2 * li]), ly = sy(s.pj[2 * li + 1]);
    const br = clamp(W / 150, 4, 9);
    if (landed) {
      const rx = br * 2.4, ry = rx * 0.38;
      ctx.beginPath(); ctx.ellipse(lx, ly, rx, ry, 0, 0, Math.PI * 2);
      ctx.lineWidth = 2; ctx.strokeStyle = "rgba(255,241,220,.95)"; ctx.stroke();
      if (landedAt !== null && !reduce.matches) {
        const pp = clamp((now - landedAt) / PULSE_MS, 0, 1);
        if (pp < 1) {
          ctx.beginPath(); ctx.ellipse(lx, ly, rx * (1 + easeOutQuart(pp) * 1.8), ry * (1 + easeOutQuart(pp) * 1.8), 0, 0, Math.PI * 2);
          ctx.lineWidth = 2; ctx.strokeStyle = `rgba(255,241,220,${0.8 * (1 - pp)})`; ctx.stroke();
        }
      }
    }

    // ball
    if (!landed) ballDot(head[0], head[1], br, true);
    else ballDot(lx, ly, br * 0.7, false);

    // apex ring and plates
    if (apexShown) {
      ctx.beginPath(); ctx.arc(au, av, br * 1.25, 0, Math.PI * 2);
      ctx.lineWidth = 2; ctx.strokeStyle = "rgba(255,241,220,.95)"; ctx.stroke();
      plate(`${Math.round(s.maxHeight)} yd high`, au, av, ["above", "right", "left", "below"], fs, false);
    }
    if (landed) plate(`${Math.round(s.carry)} yd carry`, lx, ly, ["below", "right", "left", "above"], fs, false);

    return settled && (landedAt === null || performance.now() - landedAt > PULSE_MS);
  }

  // ---- frame loop -------------------------------------------------------------
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
    if (art.ready) {
      ctx.drawImage(art.img, view.l, view.t, view.w, view.h, 0, 0, W, H);
      ctx.fillStyle = "rgba(14,9,26,.14)";
      ctx.fillRect(0, 0, W, H);
    } else {
      ctx.fillStyle = "#231B3A";
      ctx.fillRect(0, 0, W, H);
    }

    const lw = clamp(W / 240, 2.4, 6);
    const fs = clamp(W / 80, 10.5, 17);
    taken = [];
    if (avoidEl) {
      const rr = root.getBoundingClientRect();
      const ar = avoidEl.getBoundingClientRect();
      if (ar.width && ar.bottom > rr.top && ar.top < rr.bottom) taken.push({ x: ar.left - rr.left - 6, y: ar.top - rr.top - 6, w: ar.width + 12, h: ar.height + 12 });
    }
    if (art.ready) drawGreens(fs);
    if (ghostOn && ghostShot && ghostShot !== cur) drawGhost(lw);
    if (cur) {
      const done = drawShot(now, lw, fs);
      if (!done) busy = true;
      if (mode === "playing" && landedAt !== null && now - landedAt > PULSE_MS) mode = "settled";
    }
    if (busy) request();
  }

  // ---- public ----------------------------------------------------------------
  reduce.addEventListener && reduce.addEventListener("change", () => { if (reduce.matches) settle(); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(request);
  layout();

  return {
    preview,
    commit,
    replay: play,
    setGroup,
    clearGhost,
    setSpeed(n) { speed = n; },
    setGhost(on) { ghostOn = on; request(); },
    redraw: request,
    get artKey() { return art.key; },
  };
}
