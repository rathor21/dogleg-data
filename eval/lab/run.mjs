#!/usr/bin/env node
/*
 * Eval runner for the Dogleg Data "Ball flight lab" (site/ball-flight/tool.html).
 *
 *   node eval/lab/run.mjs --variant baseline [--cases id1,id2] [--flow-dir .claude/hillclimb/lab]
 *                         [--reps 1] [--conc 4] [--perf-conc 1] [--cpu auto|N] [--redo] [--perf-only]
 *
 * Serves site/ itself (static server, gzip like the CDN would), then per case:
 *   pass 1 (screenshots + programmatic metrics): fresh incognito context, viewport, prefers-reduced-motion
 *          reduce, load, run actions, wait for settle, capture PNG + full-page JPEG, measure DOM metrics + axe.
 *   pass 2 (performance): fresh incognito context, motion ON, load_ms, input latency, transferred bytes.
 * CPU throttling in the perf pass: 4x for mobile:true viewports (phone, phone landscape, tablet), 1x for laptop and TV (override with --cpu N).
 * --perf-only re-measures only the perf fields of existing rows (atomic rewrite), leaving screenshots, DOM metrics and judge fields alone.
 * One row per case is appended to <flow>/<variant>/results.jsonl when both passes are done.
 * Failures go to errors.jsonl (never a zero row). Existing (prompt_id, rep) rows are skipped.
 *
 * The app under test (site/, analysis/) is read only.
 */
import http from "node:http";
import zlib from "node:zlib";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../..");
const SITE = path.join(ROOT, "site");
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const AXE = path.join(ROOT, "node_modules/axe-core/axe.min.js");
const CASE_TIMEOUT_MS = 60_000;

// ---------------------------------------------------------------- CLI
function parseArgs(argv) {
  const o = { variant: "baseline", reps: 1, conc: 4, perfConc: 1, cpu: null, perfOnly: false, flowDir: ".claude/hillclimb/lab", cases: null, redo: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === "--variant") o.variant = next();
    else if (a === "--reps") o.reps = Number(next());
    else if (a === "--cases") o.cases = next().split(",").map((s) => s.trim()).filter(Boolean);
    else if (a === "--flow-dir") o.flowDir = next();
    else if (a === "--conc") o.conc = Number(next());
    else if (a === "--perf-conc") o.perfConc = Number(next());
    else if (a === "--cpu") { const v = next(); o.cpu = v === "auto" ? null : Number(v); }
    else if (a === "--perf-only") o.perfOnly = true;
    else if (a === "--redo") o.redo = true;
    else if (a === "--help" || a === "-h") { console.log("see header of eval/lab/run.mjs"); process.exit(0); }
    else { console.error("unknown arg " + a); process.exit(2); }
  }
  return o;
}

// ---------------------------------------------------------------- static server
const MIME = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml",
  ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif",
  ".ico": "image/x-icon", ".woff2": "font/woff2", ".woff": "font/woff", ".txt": "text/plain; charset=utf-8", ".xml": "application/xml",
};
const COMPRESSIBLE = new Set([".html", ".js", ".mjs", ".css", ".json", ".svg", ".txt", ".xml"]);

function startServer() {
  const gz = new Map();
  const server = http.createServer((req, res) => {
    try {
      const u = new URL(req.url, "http://x");
      let rel = decodeURIComponent(u.pathname);
      if (rel.endsWith("/")) rel += "index.html";
      const file = path.normalize(path.join(SITE, rel));
      if (!file.startsWith(SITE + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
        res.writeHead(404, { "content-type": "text/plain" }); res.end("not found"); return;
      }
      const ext = path.extname(file).toLowerCase();
      const headers = { "content-type": MIME[ext] || "application/octet-stream", "cache-control": "no-store" };
      let body = fs.readFileSync(file);
      if (COMPRESSIBLE.has(ext) && /\bgzip\b/.test(req.headers["accept-encoding"] || "")) {
        const key = file + ":" + fs.statSync(file).mtimeMs;
        if (!gz.has(key)) gz.set(key, zlib.gzipSync(body, { level: 6 }));
        body = gz.get(key);
        headers["content-encoding"] = "gzip";
      }
      headers["content-length"] = body.length;
      res.writeHead(200, headers);
      res.end(req.method === "HEAD" ? undefined : body);
    } catch (e) {
      res.writeHead(500); res.end(String(e));
    }
  });
  return new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve({ server, port: server.address().port })));
}

// ---------------------------------------------------------------- helpers
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const pct = (arr, p) => {
  const s = [...arr].sort((a, b) => a - b);
  if (!s.length) return NaN;
  const i = (s.length - 1) * p, lo = Math.floor(i), hi = Math.ceil(i);
  return s[lo] + (s[hi] - s[lo]) * (i - lo);
};
const r1 = (v) => Math.round(v * 10) / 10;
const r2 = (v) => Math.round(v * 100) / 100;

class CaseError extends Error {
  constructor(cls, msg) { super(msg); this.cls = cls; }
}
async function withTimeout(promise, ms, label, onTimeout) {
  let t;
  const timeout = new Promise((_, rej) => { t = setTimeout(async () => { try { await onTimeout?.(); } catch {} rej(new CaseError("timeout", `${label} exceeded ${ms / 1000}s`)); }, ms); });
  try { return await Promise.race([promise, timeout]); } finally { clearTimeout(t); }
}

async function openPage(browser, c, { reduced, cpu }) {
  const ctx = await browser.createBrowserContext(); // incognito, no shared cache or storage
  const page = await ctx.newPage();
  const v = c.viewport;
  await page.setViewport({ width: v.w, height: v.h, deviceScaleFactor: v.dpr, isMobile: !!v.mobile, hasTouch: !!v.mobile });
  await page.emulateMediaFeatures([{ name: "prefers-reduced-motion", value: reduced ? "reduce" : "no-preference" }]);
  if (cpu && cpu > 1) {
    const cdp = await page.createCDPSession();
    await cdp.send("Emulation.setCPUThrottlingRate", { rate: cpu });
  }
  return { ctx, page };
}

/** Install a MutationObserver before any script runs so load_ms is the first moment the shot label has text. */
const INSTALL_LABEL_CLOCK = () => {
  window.__labShotAt = null;
  const check = () => {
    const e = document.getElementById("sl-name");
    if (e && e.textContent.trim()) { window.__labShotAt = performance.now(); return true; }
    return false;
  };
  new MutationObserver((_, o) => { if (check()) o.disconnect(); }).observe(document, { subtree: true, childList: true, characterData: true });
};

async function waitReady(page, timeout = 30_000) {
  await page.waitForFunction(() => {
    const e = document.getElementById("sl-name");
    return window.__labReady === true && e && e.textContent.trim().length > 0;
  }, { timeout });
  const failed = await page.evaluate(() => { const e = document.getElementById("app-error"); return e && !e.hidden; });
  if (failed) throw new CaseError("app_error", "The app shows its own load error (#app-error).");
}

// ---------------------------------------------------------------- actions
function parseSet(spec) {
  const json = spec.replace(/([{,]\s*)([A-Za-z_]\w*)\s*:/g, '$1"$2":');
  return JSON.parse(json);
}
const rafs = (page, n = 2) => page.evaluate((k) => new Promise((res) => { const step = (i) => (i <= 0 ? res() : requestAnimationFrame(() => step(i - 1))); step(k); }), n);

async function runAction(page, action, ctx) {
  const [name, ...rest] = action.split(":");
  const arg = rest.join(":");
  if (name === "pin") {
    const ok = await page.evaluate(() => { const b = document.getElementById("pin-btn"); if (!b) return false; b.click(); return true; });
    if (!ok) throw new CaseError("action_failed", "pin: #pin-btn not found");
  } else if (name === "set") {
    const vals = parseSet(arg);
    const ids = { clubSpeed: "sl-clubSpeed", attack: "sl-attack", path: "sl-path", face: "sl-face", dynLoft: "sl-dynLoft" };
    const res = await page.evaluate((vals, ids) => {
      const miss = [];
      for (const [k, v] of Object.entries(vals)) {
        const el = document.getElementById(ids[k]);
        if (!el) { miss.push(k); continue; }
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
        setter.call(el, String(v));
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
      }
      return miss;
    }, vals, ids);
    if (res.length) throw new CaseError("action_failed", "set: no slider for " + res.join(","));
  } else if (name === "flyAll") {
    const ok = await page.evaluate(() => { const b = document.getElementById("fly-all"); if (!b) return false; b.click(); return true; });
    if (!ok) throw new CaseError("action_failed", "flyAll: #fly-all not found");
    await sleep(150);
    await page.waitForFunction(() => document.getElementById("fly-all").getAttribute("aria-pressed") === "false", { timeout: 40_000 });
  } else if (name === "present") {
    // el.click() has no user activation, so fullscreen is refused and the app falls back to its class-only layout.
    await page.evaluate(() => document.getElementById("present-btn").click());
    await page.waitForFunction(() => document.body.classList.contains("presenting"), { timeout: 5000 });
    await sleep(700);
  } else if (name === "openDrawer") {
    await page.evaluate(() => { const t = document.getElementById("swing-toggle"); if (t && t.getAttribute("aria-expanded") === "false") t.click(); });
    await sleep(500);
  } else if (name === "tab") {
    await page.evaluate((v) => { const t = document.getElementById("tab-" + v); if (t) t.click(); }, arg);
  } else if (name === "scrollTo") {
    if (ctx.beforeScroll) { await ctx.beforeScroll(); ctx.beforeScroll = null; }
    const ok = await page.evaluate((sel) => { const e = document.querySelector(sel); if (!e) return false; e.scrollIntoView({ block: "start", behavior: "instant" }); return true; }, arg);
    if (!ok) throw new CaseError("action_failed", "scrollTo: no element " + arg);
    await sleep(300);
  } else {
    throw new CaseError("action_failed", "unknown action " + action);
  }
  await rafs(page, 3);
  await sleep(name === "set" || name === "pin" ? 350 : 120);
}

// ---------------------------------------------------------------- in-page metrics
const MEASURE = ({ mobile }) => {
  const vw = window.innerWidth, vh = window.innerHeight;
  const vis = (el) => {
    try { return el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true }); } catch { return true; }
  };
  const inView = (r) => r.right > 0 && r.bottom > 0 && r.left < vw && r.top < vh;

  // smallest computed font size among visible text nodes inside the viewport
  let minFont = Infinity, minSample = "";
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const rng = document.createRange();
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const txt = n.nodeValue.trim();
    if (!txt) continue;
    const el = n.parentElement;
    if (!el || /^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE)$/.test(el.tagName)) continue;
    if (!vis(el)) continue;
    rng.selectNodeContents(n);
    const r = rng.getBoundingClientRect();
    if (r.width < 2 || r.height < 2 || !inView(r)) continue;
    const cx = Math.min(Math.max((Math.max(r.left, 0) + Math.min(r.right, vw)) / 2, 0), vw - 1);
    const cy = Math.min(Math.max((Math.max(r.top, 0) + Math.min(r.bottom, vh)) / 2, 0), vh - 1);
    const hit = document.elementFromPoint(cx, cy);
    const cs = getComputedStyle(el);
    if (cs.pointerEvents !== "none" && hit && !(hit === el || el.contains(hit) || hit.contains(el))) continue; // covered or clipped
    const fs = parseFloat(cs.fontSize);
    if (!(fs > 0)) continue;
    if (fs < minFont) { minFont = fs; minSample = txt.slice(0, 40); }
  }

  // small interactive targets (whole page, rendered, not inert)
  const thr = mobile ? 44 : 24;
  const sel = 'a[href],button,input:not([type=hidden]),select,textarea,summary,[role=radio],[role=tab],[role=button],[tabindex]:not([tabindex="-1"])';
  let small = 0, total = 0;
  const samples = [];
  for (const el of document.querySelectorAll(sel)) {
    if (!vis(el) || el.closest("[inert]") || el.closest("[hidden]")) continue;
    let r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    if (r.right <= 0 || r.bottom <= 0) continue; // skip link parked off screen
    const cs = getComputedStyle(el);
    if (el.tagName === "A" && cs.display === "inline") continue; // inline text links are exempt
    if ((el.type === "checkbox" || el.type === "radio") && el.labels && el.labels[0]) {
      const l = el.labels[0].getBoundingClientRect();
      r = { width: Math.max(r.width, l.width), height: Math.max(r.height, l.height) };
    }
    total++;
    if (r.width < thr || r.height < thr) {
      small++;
      if (samples.length < 10) {
        const name = (el.getAttribute("aria-label") || el.textContent || el.id || el.tagName).replace(/\s+/g, " ").trim().slice(0, 28);
        samples.push(`${el.tagName.toLowerCase()}${el.id ? "#" + el.id : ""} "${name}" ${Math.round(r.width)}x${Math.round(r.height)}`);
      }
    }
  }

  const de = document.documentElement;
  const overflowX = Math.max(de.scrollWidth, document.body.scrollWidth) > de.clientWidth ? 1 : 0;
  return { minFont: Number.isFinite(minFont) ? minFont : null, minSample, small, total, samples, overflowX, scrollW: Math.max(de.scrollWidth, document.body.scrollWidth), clientW: de.clientWidth };
};

const ABOVE_FOLD = () => {
  const vw = window.innerWidth, vh = window.innerHeight;
  const frac = (el) => {
    if (!el) return 0;
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return 0;
    const w = Math.max(0, Math.min(r.right, vw) - Math.max(r.left, 0));
    const h = Math.max(0, Math.min(r.bottom, vh) - Math.max(r.top, 0));
    return (w * h) / (r.width * r.height);
  };
  const label = frac(document.getElementById("shot-label"));
  const canvas = frac(document.getElementById("range-canvas"));
  return { label, canvas, ok: label > 0 && canvas > 0 };
};

const RENDERED_STATE = () => {
  const t = (s, r = document) => { const e = r.querySelector(s); return e ? e.textContent.replace(/\s+/g, " ").trim() : ""; };
  const label = [t("#sl-name"), t("#sl-finish"), t("#sl-line")].filter(Boolean).join(" | ");
  const tiles = [...document.querySelectorAll("#key-tiles .tile")].map((e) => {
    const parts = [t(".tile-label", e), (t(".v", e) + " " + t(".u", e)).trim(), t(".tile-word", e)].filter(Boolean);
    return parts.join(" ");
  }).filter(Boolean).join("; ");
  const mode = document.querySelector('#mode-seg [aria-checked="true"]');
  return { label, tiles, mode: mode ? mode.textContent.trim() : "", url: location.search };
};

// ---------------------------------------------------------------- pass 1: screenshots and DOM metrics
async function passShots(browser, c, port, shotDir, variant) {
  const { ctx, page } = await openPage(browser, c, { reduced: true });
  const errors = [];
  const errLog = [];
  const note = (kind, msg) => { errors.push(kind); if (errLog.length < 8) errLog.push(kind + ": " + String(msg).slice(0, 200)); };
  page.on("console", (m) => { if (m.type() === "error") note("console", m.text()); });
  page.on("pageerror", (e) => note("pageerror", e.message));
  page.on("requestfailed", (r) => note("requestfailed", r.url() + " " + (r.failure()?.errorText || "")));
  page.on("response", (r) => { if (r.status() >= 400) note("http" + r.status(), r.url()); });
  const t0 = Date.now();
  try {
    return await withTimeout((async () => {
      await page.goto(`http://127.0.0.1:${port}/ball-flight/tool.html?${c.url}`, { waitUntil: "networkidle2", timeout: 45_000 });
      await waitReady(page);
      await page.evaluate(() => document.fonts && document.fonts.ready);
      await rafs(page, 3);
      await sleep(400);
      const actx = { aboveFold: null };
      actx.beforeScroll = async () => { actx.aboveFold = await page.evaluate(ABOVE_FOLD); };
      for (const a of c.actions || []) await runAction(page, a, actx);
      if (!actx.aboveFold) actx.aboveFold = await page.evaluate(ABOVE_FOLD);
      // settle: network idle after any lazy art, then two frames
      try { await page.waitForNetworkIdle({ idleTime: 400, timeout: 8000 }); } catch {}
      await rafs(page, 3);
      await sleep(300);
      const scrollY = await page.evaluate(() => window.scrollY);

      const png = path.join(shotDir, `${c.id}.png`);
      await page.screenshot({ path: png, type: "png" });
      const state = await page.evaluate(RENDERED_STATE);
      const m = await page.evaluate(MEASURE, { mobile: !!c.viewport.mobile });

      let fullOk = true;
      try {
        await page.screenshot({ path: path.join(shotDir, `${c.id}_full.jpg`), type: "jpeg", quality: 70, fullPage: true });
      } catch (e) { fullOk = false; }

      await page.addScriptTag({ path: AXE });
      const axe = await page.evaluate(async () => {
        const r = await window.axe.run(document, { resultTypes: ["violations"] });
        return r.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length }));
      });
      const serious = axe.filter((v) => v.impact === "serious" || v.impact === "critical");

      return {
        state,
        grade: {
          console_errors: errors.length,
          overflow_x: m.overflowX,
          min_font_px: m.minFont === null ? null : r2(m.minFont),
          small_targets: m.small,
          axe_serious: serious.length, // violated rules with impact serious or critical, see metrics.md
          above_fold_ok: actx.aboveFold.ok ? 1 : 0,
        },
        meta: {
          console_error_samples: errLog,
          min_font_sample: m.minSample,
          small_target_samples: m.samples,
          interactive_total: m.total,
          scroll_w: m.scrollW,
          client_w: m.clientW,
          label_in_view: r2(actx.aboveFold.label),
          canvas_in_view: r2(actx.aboveFold.canvas),
          axe_serious: serious,
          scroll_y: scrollY,
          full_page_ok: fullOk,
          shot_s: r1((Date.now() - t0) / 1000),
        },
      };
    })(), CASE_TIMEOUT_MS, "screenshot pass", () => ctx.close());
  } finally {
    try { await ctx.close(); } catch {}
  }
}

// ---------------------------------------------------------------- pass 2: performance
const cpuFor = (c, o) => (o.cpu && o.cpu > 0 ? o.cpu : c.viewport.mobile ? 4 : 1);

async function passPerf(browser, c, port, cpu) {
  const { ctx, page } = await openPage(browser, c, { reduced: false, cpu });
  try {
    return await withTimeout((async () => {
      const cdp = await page.createCDPSession();
      await cdp.send("Network.enable");
      await cdp.send("Network.setCacheDisabled", { cacheDisabled: true });
      const types = new Map();
      let js = 0, total = 0;
      cdp.on("Network.responseReceived", (e) => types.set(e.requestId, e.type));
      cdp.on("Network.loadingFinished", (e) => {
        const t = types.get(e.requestId);
        total += e.encodedDataLength || 0;
        if (t === "Script") js += e.encodedDataLength || 0;
      });
      await page.evaluateOnNewDocument(INSTALL_LABEL_CLOCK);
      await page.goto(`http://127.0.0.1:${port}/ball-flight/tool.html?${c.url}`, { waitUntil: "networkidle2", timeout: 45_000 });
      await waitReady(page);
      const loadMs = await page.evaluate(() => window.__labShotAt);
      if (loadMs == null) throw new CaseError("perf_failed", "shot label clock never fired");
      // Let the opening flight finish so the inputs do not compete with it, then idle.
      await sleep(4500);
      const has = await page.evaluate(() => !!document.getElementById("sl-face"));
      if (!has) throw new CaseError("perf_failed", "#sl-face not found");
      // Per sample, one dispatch and three timestamps from the same t0:
      //   sync   = dispatchEvent returned (the synchronous handler and render work, no frame quantization)
      //   single = first requestAnimationFrame callback after the dispatch
      //   double = second requestAnimationFrame callback (the frame that shows the result)
      // A random gap between samples varies the frame phase so the single-rAF number is not locked to one phase.
      const times = await page.evaluate(async () => {
        const el = document.getElementById("sl-face");
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
        const out = [];
        const raf = () => new Promise((res) => requestAnimationFrame(res));
        const wait = (ms) => new Promise((r) => setTimeout(r, ms));
        const lo = Number(el.min), hi = Number(el.max);
        for (let i = 0; i < 20; i++) {
          const v = ((i * 7) % 13) - 6; // a deterministic spread of faces between -6 and +6
          const val = Math.max(lo, Math.min(hi, v));
          const t0 = performance.now();
          setter.call(el, String(val));
          el.dispatchEvent(new Event("input", { bubbles: true }));
          const sync = performance.now() - t0;
          await raf();
          const single = performance.now() - t0;
          await raf();
          const dbl = performance.now() - t0;
          out.push({ sync, single, dbl });
          await wait(60 + ((i * 37) % 23));
        }
        return out;
      });
      await sleep(300);
      return {
        load_ms: Math.round(loadMs),
        input_p50_ms: r1(pct(times.map((t) => t.single), 0.5)),
        input_p95_ms: r1(pct(times.map((t) => t.single), 0.95)),
        input_frame_p95_ms: r1(pct(times.map((t) => t.dbl), 0.95)),
        input_sync_p50_ms: r1(pct(times.map((t) => t.sync), 0.5)),
        input_sync_p95_ms: r1(pct(times.map((t) => t.sync), 0.95)),
        js_kb: r1(js / 1024),
        total_kb: r1(total / 1024),
      };
    })(), CASE_TIMEOUT_MS, "perf pass", () => ctx.close());
  } finally {
    try { await ctx.close(); } catch {}
  }
}

// ---------------------------------------------------------------- pool
async function pool(items, n, fn) {
  let i = 0;
  const worker = async () => { for (;;) { const k = i++; if (k >= items.length) return; await fn(items[k], k); } };
  await Promise.all(Array.from({ length: Math.max(1, n) }, worker));
}

const readJsonl = (p) => (fs.existsSync(p) ? fs.readFileSync(p, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l)) : []);

// ---------------------------------------------------------------- --perf-only
// Re-measure the perf pass for cases that already have a row and patch only the perf fields.
// Every write re-reads results.jsonl and rewrites it atomically, so a concurrent merge.mjs is not clobbered.
const PERF_GRADE_KEYS = ["load_ms", "input_p50_ms", "input_p95_ms", "input_frame_p95_ms", "input_sync_p50_ms", "input_sync_p95_ms", "js_kb", "total_kb"];
async function perfOnly(o, cases, resultsPath, errorsPath) {
  const have = new Set(readJsonl(resultsPath).map((r) => r.prompt_id));
  const todo = cases.filter((c) => have.has(c.id));
  console.log(`perf-only ${o.variant}: ${todo.length} cases with existing rows`);
  if (!todo.length) return;
  const { server, port } = await startServer();
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: true,
    args: ["--hide-scrollbars", "--force-color-profile=srgb", "--font-render-hinting=none", "--no-first-run", "--no-default-browser-check", "--disable-search-engine-choice-screen"],
  });
  const wall0 = Date.now();
  let n = 0, nfail = 0;
  try {
    await pool(todo, o.perfConc, async (c) => {
      const t = Date.now();
      try {
        const cpu = cpuFor(c, o);
        const perf = await passPerf(browser, c, port, cpu);
        for (const [k, v] of Object.entries(perf)) if (!Number.isFinite(v)) throw new CaseError("bad_metric", `${c.id}: ${k} is ${v}`);
        const rows = readJsonl(resultsPath);
        const row = rows.find((r) => r.prompt_id === c.id && r.rep === 0);
        for (const k of PERF_GRADE_KEYS) row.grade[k] = perf[k];
        row.latency_s = r2(perf.load_ms / 1000);
        row.meta = { ...row.meta, cpu_throttle: cpu };
        const tmp = resultsPath + ".tmp";
        fs.writeFileSync(tmp, rows.map((r) => JSON.stringify(r)).join("\n") + "\n");
        fs.renameSync(tmp, resultsPath);
        console.log(`[perf ${++n}/${todo.length}] ${c.id} cpu=${cpu}x ${((Date.now() - t) / 1000).toFixed(1)}s load=${perf.load_ms}ms p50=${perf.input_p50_ms} p95=${perf.input_p95_ms} sync95=${perf.input_sync_p95_ms} frame95=${perf.input_frame_p95_ms}`);
      } catch (e) {
        ++n; ++nfail;
        fs.appendFileSync(errorsPath, JSON.stringify({ prompt_id: c.id, rep: 0, class: e.cls || "perf_failed", message: String(e.message).slice(0, 500), ts: new Date().toISOString() }) + "\n");
        console.log(`  ERROR ${c.id}: ${e.cls || "perf_failed"}: ${String(e.message).slice(0, 160)}`);
      }
    });
  } finally {
    await browser.close();
    server.close();
  }
  console.log(`perf-only done in ${((Date.now() - wall0) / 1000).toFixed(0)}s, ${nfail} failed`);
  if (nfail) process.exitCode = 1;
}

// ---------------------------------------------------------------- main
async function main() {
  const o = parseArgs(process.argv.slice(2));
  const flow = path.resolve(ROOT, o.flowDir);
  const vdir = path.join(flow, o.variant);
  const shotDir = path.join(vdir, "shots");
  const traceDir = path.join(flow, "traces");
  const partDir = path.join(vdir, ".partial");
  for (const d of [shotDir, traceDir, partDir]) fs.mkdirSync(d, { recursive: true });
  const resultsPath = path.join(vdir, "results.jsonl");
  const errorsPath = path.join(vdir, "errors.jsonl");

  let cases = JSON.parse(fs.readFileSync(path.join(HERE, "cases.json"), "utf8"));
  if (o.cases) {
    const unknown = o.cases.filter((id) => !cases.some((c) => c.id === id));
    if (unknown.length) { console.error("unknown case ids: " + unknown.join(", ")); process.exit(2); }
    cases = cases.filter((c) => o.cases.includes(c.id));
  }
  if (o.perfOnly) return perfOnly(o, cases, resultsPath, errorsPath);
  const done = new Set(o.redo ? [] : readJsonl(resultsPath).map((r) => `${r.prompt_id}#${r.rep}`));
  const todo = cases.filter((c) => !done.has(`${c.id}#0`));
  console.log(`variant ${o.variant}: ${cases.length} cases, ${cases.length - todo.length} already done, ${todo.length} to run`);
  if (!todo.length) return;

  const { server, port } = await startServer();
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ["--hide-scrollbars", "--force-color-profile=srgb", "--font-render-hinting=none", "--no-first-run", "--no-default-browser-check", "--disable-search-engine-choice-screen"],
  });
  const wall0 = Date.now();
  const failed = new Set();
  const logErr = (c, cls, msg) => {
    fs.appendFileSync(errorsPath, JSON.stringify({ prompt_id: c.id, rep: 0, class: cls, message: String(msg).slice(0, 500), ts: new Date().toISOString() }) + "\n");
    failed.add(c.id);
    console.log(`  ERROR ${c.id}: ${cls}: ${String(msg).slice(0, 160)}`);
  };
  let n1 = 0;
  const partPath = (c) => path.join(partDir, `${c.id}.json`);

  try {
    // pass 1: screenshots, concurrency o.conc
    await pool(todo, o.conc, async (c) => {
      const t = Date.now();
      try {
        const r = await passShots(browser, c, port, shotDir, o.variant);
        fs.writeFileSync(partPath(c), JSON.stringify(r));
        console.log(`[shots ${++n1}/${todo.length}] ${c.id} ${((Date.now() - t) / 1000).toFixed(1)}s err=${r.grade.console_errors} minfont=${r.grade.min_font_px} small=${r.grade.small_targets} axe=${r.grade.axe_serious}`);
      } catch (e) {
        ++n1;
        logErr(c, e.cls || "shots_failed", e.message);
      }
    });

    // pass 2: performance, low concurrency so timings are not fighting each other
    let n2 = 0;
    const perfTodo = todo.filter((c) => !failed.has(c.id));
    await pool(perfTodo, o.perfConc, async (c) => {
      const t = Date.now();
      try {
        const cpu = cpuFor(c, o);
        const perf = await passPerf(browser, c, port, cpu);
        perf.cpu_throttle = cpu;
        const shots = JSON.parse(fs.readFileSync(partPath(c), "utf8"));
        writeRow(c, shots, perf);
        console.log(`[perf ${++n2}/${perfTodo.length}] ${c.id} ${((Date.now() - t) / 1000).toFixed(1)}s load=${perf.load_ms}ms p95=${perf.input_p95_ms}ms js=${perf.js_kb}KB`);
      } catch (e) {
        ++n2;
        logErr(c, e.cls || "perf_failed", e.message);
      }
    });
  } finally {
    await browser.close();
    server.close();
  }

  function writeRow(c, shots, perf) {
    const { cpu_throttle, ...perfFields } = perf;
    const grade = { ...shots.grade, ...perfFields };
    for (const [k, v] of Object.entries(grade)) {
      if (typeof v !== "number" || !Number.isFinite(v)) throw new CaseError("bad_metric", `${c.id}: metric ${k} is ${v}`);
    }
    const png = `${o.variant}/shots/${c.id}.png`;
    const alt = `Screenshot of the ball flight lab at ${c.viewport.w}x${c.viewport.h}: ${shots.state.label}`;
    const prompt = `${c.scenario}\nFocus: ${c.focus}`;
    const row = {
      prompt_id: c.id, rep: 0, prompt, tags: c.tags,
      attachments: [{ kind: "image", ref: png, alt }],
      grade, model: "none (static app)", latency_s: r2(perf.load_ms / 1000),
      meta: { viewport: c.viewport, url: c.url, actions: c.actions || [], cpu_throttle, ...shots.meta },
    };
    const trace = [
      { role: "user", content: prompt, attachments: [{ kind: "image", ref: png, alt }] },
      { role: "assistant", content: `Rendered state: ${shots.state.label} | ${shots.state.tiles}`, attachments: [{ kind: "image", ref: png, alt }] },
    ];
    fs.writeFileSync(path.join(traceDir, `${c.id}_rep0.json`), JSON.stringify(trace, null, 2));
    fs.appendFileSync(resultsPath, JSON.stringify(row) + "\n");
    fs.rmSync(partPath(c), { force: true });
  }

  const rows = readJsonl(resultsPath);
  console.log(`done in ${((Date.now() - wall0) / 1000).toFixed(0)}s: ${rows.length} rows in results.jsonl, ${failed.size} failed this run`);
  if (failed.size) process.exitCode = 1;
}

main().catch((e) => { console.error(e); process.exit(1); });
