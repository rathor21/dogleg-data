#!/usr/bin/env node
/*
 * Social export pipeline for release 003 (issue #15).
 *
 * One command builds the LinkedIn assets from the article page's
 * deterministic settled-state hooks:
 *   - hero.webm / hero.mp4 / hero_portrait.mp4, a screen capture of the
 *     hero canvas's natural animation, transcoded to H.264.
 *   - card_NN_<name>.png, one 1080x1350 screenshot per entry in
 *     cards.json, plus carousel.pdf bundling them for LinkedIn's
 *     carousel-as-PDF upload path.
 *
 * Usage:
 *   node launch/003-social/export.mjs [--port 8946] [--out launch/003-social/out] [--url http://host:port]
 *
 * See README.md in this directory for the contract this script relies on.
 */

import { spawn, spawnSync } from "node:child_process";
import { mkdir, readFile, writeFile, readdir, stat, rename } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "..", "..");

const CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const FFMPEG = "/opt/homebrew/bin/ffmpeg";
const FFPROBE = "/opt/homebrew/bin/ffprobe";

function log(...args) {
  console.log("[social-export]", ...args);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function parseArgs(argv) {
  const opts = {
    port: 8946,
    out: path.join(__dirname, "out"),
    url: null,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--port") {
      opts.port = Number(argv[++i]);
    } else if (a === "--out") {
      opts.out = path.resolve(process.cwd(), argv[++i]);
    } else if (a === "--url") {
      opts.url = argv[++i].replace(/\/+$/, "");
    } else if (a === "--help" || a === "-h") {
      console.log(
        "Usage: node launch/003-social/export.mjs [--port 8946] [--out launch/003-social/out] [--url http://host:port]"
      );
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${a}`);
    }
  }
  return opts;
}

// ---------------------------------------------------------------
// Static server
// ---------------------------------------------------------------
async function waitForServer(url, timeoutMs = 15000) {
  const start = Date.now();
  let lastErr = null;
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url);
      // Any response at all means the server is answering requests.
      if (res.status) return;
    } catch (err) {
      lastErr = err;
    }
    await sleep(200);
  }
  throw new Error(
    `Static server did not respond at ${url} within ${timeoutMs}ms (${lastErr ? lastErr.message : "no response"})`
  );
}

async function startServer(port) {
  log(`starting static server: npx -y serve site -l ${port}`);
  const child = spawn("npx", ["-y", "serve", "site", "-l", String(port)], {
    cwd: REPO_ROOT,
    stdio: ["ignore", "pipe", "pipe"],
  });
  let out = "";
  child.stdout.on("data", (d) => { out += d.toString(); });
  child.stderr.on("data", (d) => { out += d.toString(); });
  child.on("exit", (code) => {
    if (code !== null && code !== 0) {
      console.error("[social-export] static server exited early:\n" + out);
    }
  });
  await waitForServer(`http://localhost:${port}/`);
  log("static server is up");
  return child;
}

function stopServer(child) {
  if (!child) return;
  log("stopping static server");
  child.kill("SIGTERM");
}

// ---------------------------------------------------------------
// Shared page helpers
// ---------------------------------------------------------------
async function waitForPhaseComplete(page, timeoutMs, label) {
  try {
    await page.waitForFunction(() => window.__phaseComplete === true, {
      timeout: timeoutMs,
    });
  } catch (err) {
    throw new Error(
      `Timed out after ${timeoutMs}ms waiting for window.__phaseComplete === true on ${label}`
    );
  }
}

// ---------------------------------------------------------------
// Hero video capture
// ---------------------------------------------------------------
async function captureHero(browser, baseUrl, outDir) {
  log("capturing hero animation (canvas.captureStream + MediaRecorder)");
  const page = await browser.newPage();
  // deviceScaleFactor 2: hero.js sizes the canvas backing store to
  // cssWidth * devicePixelRatio, so this doubles the captured source
  // resolution (the hero canvas renders at ~1132 CSS px wide inside the
  // article column, which was the whole source for the portrait crop
  // before -- at dpr 1 that gave a source narrower than the 1080px crop
  // width, hence the softening issue-#16 QA flagged). At dpr 2 the source
  // is ~2264px wide, comfortably above the 1920px floor the portrait cut
  // wants before its own 1080-wide crop.
  await page.setViewport({ width: 1600, height: 900, deviceScaleFactor: 2 });
  await page.goto(`${baseUrl}/augusta-12/`, { waitUntil: "networkidle0" });

  await page.waitForSelector("#hero-canvas");
  await page.waitForFunction(() => window.__heroState !== undefined, {
    timeout: 15000,
  });
  await page.waitForSelector("#hero-replay", { visible: true });

  // Arm the recorder before triggering a clean run, so the recording
  // starts before the first shot launches rather than mid-sequence.
  await page.evaluate(() => {
    const canvas = document.getElementById("hero-canvas");
    const stream = canvas.captureStream(30);
    let mimeType = "video/webm;codecs=vp9";
    if (!window.MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = "video/webm;codecs=vp8";
    }
    window.__chunks = [];
    window.__track = stream.getVideoTracks()[0];
    window.__rec = new MediaRecorder(stream, { mimeType });
    window.__rec.ondataavailable = (e) => {
      if (e.data && e.data.size) window.__chunks.push(e.data);
    };
    window.__rec.start(100);
    window.__recMime = mimeType;
  });

  await page.click("#hero-replay");

  await waitForPhaseComplete(page, 15000, "hero (/augusta-12/)");

  // The canvas stops repainting the instant the sequence settles, and in
  // headless Chrome that means the compositor stops producing new frames
  // for captureStream to grab -- requestFrame() alone is a no-op without a
  // real paint behind it. Force a harmless (zero-alpha, 1x1) draw each tick
  // so the settled composition holds on screen for a beat before the clip
  // ends, instead of the recording just stopping cold.
  await page.evaluate(
    () =>
      new Promise((resolve) => {
        const canvas = document.getElementById("hero-canvas");
        const ctx = canvas.getContext("2d");
        const track = window.__track;
        let elapsed = 0;
        const stepMs = 33;
        const holdMs = 1500;
        const timer = setInterval(() => {
          ctx.save();
          ctx.globalAlpha = 0;
          ctx.fillRect(0, 0, 1, 1);
          ctx.restore();
          if (typeof track.requestFrame === "function") track.requestFrame();
          elapsed += stepMs;
          if (elapsed >= holdMs) {
            clearInterval(timer);
            resolve();
          }
        }, stepMs);
      })
  );

  const dataUrl = await page.evaluate(
    () =>
      new Promise((resolve) => {
        window.__rec.onstop = () => {
          const blob = new Blob(window.__chunks, { type: window.__recMime });
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result);
          reader.readAsDataURL(blob);
        };
        window.__rec.stop();
      })
  );

  const base64 = dataUrl.slice(dataUrl.indexOf(",") + 1);
  const webmPath = path.join(outDir, "hero.webm");
  await writeFile(webmPath, Buffer.from(base64, "base64"));
  log(`wrote ${webmPath}`);
  await page.close();
  return webmPath;
}

// ---------------------------------------------------------------
// ffmpeg / ffprobe
// ---------------------------------------------------------------
function runFfmpeg(args, label) {
  const res = spawnSync(FFMPEG, args, { encoding: "utf8" });
  if (res.status !== 0) {
    throw new Error(`ffmpeg failed (${label}):\n${res.stderr}`);
  }
}

function ffprobeInfo(file) {
  const args = [
    "-v", "error",
    "-show_entries", "format=duration,format_name",
    "-show_entries", "stream=codec_name,pix_fmt,width,height,r_frame_rate,nb_frames",
    "-of", "json",
    file,
  ];
  const res = spawnSync(FFPROBE, args, { encoding: "utf8" });
  if (res.status !== 0) {
    throw new Error(`ffprobe failed on ${file}:\n${res.stderr}`);
  }
  const parsed = JSON.parse(res.stdout);
  const stream = (parsed.streams || []).find((s) => s.codec_name) || {};
  return {
    codec: stream.codec_name,
    pixFmt: stream.pix_fmt,
    width: stream.width,
    height: stream.height,
    frameRate: stream.r_frame_rate,
    frameCount: stream.nb_frames,
    duration: Number(parsed.format && parsed.format.duration),
    formatName: parsed.format && parsed.format.format_name,
  };
}

function transcodeHero(webmPath, outDir) {
  const mp4Path = path.join(outDir, "hero.mp4");
  const portraitPath = path.join(outDir, "hero_portrait.mp4");

  log("transcoding hero.mp4 (H.264, yuv420p, faststart)");
  runFfmpeg(
    [
      "-y", "-i", webmPath,
      "-vf", "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2",
      "-c:v", "libx264",
      "-pix_fmt", "yuv420p",
      "-crf", "20",
      "-movflags", "+faststart",
      mp4Path,
    ],
    "hero.mp4"
  );

  // 1600x900 source -> scale height to 1350 (x1.5 -> 2400 wide),
  // then crop the centered 1080 columns for a 4:5 portrait frame.
  log("transcoding hero_portrait.mp4 (1080x1350 center crop)");
  runFfmpeg(
    [
      "-y", "-i", webmPath,
      "-vf", "fps=30,scale=2400:1350,crop=1080:1350:660:0",
      "-c:v", "libx264",
      "-pix_fmt", "yuv420p",
      "-crf", "20",
      "-movflags", "+faststart",
      portraitPath,
    ],
    "hero_portrait.mp4"
  );

  const mp4Info = ffprobeInfo(mp4Path);
  const portraitInfo = ffprobeInfo(portraitPath);
  return { mp4Path, portraitPath, mp4Info, portraitInfo };
}

// ---------------------------------------------------------------
// Carousel
// ---------------------------------------------------------------
// Only chapters with a step-driven figure (chapters.js's own .step /
// data-figure contract) ever call buildCaptureCard, which is the one place
// that adds body.capture-mode -- chapter 6 (a plain prose chapter) and
// chapter 8 ("the move," a different, non-scrolly layout) never do. Before
// this check, page.$(".chapter-figure") for those two chapters silently
// matched *some other chapter's* inline figure (whichever renders first in
// document order on the un-captured page), and this script then force-
// resized that wrong image up to 1080x1350 and shipped it as if it were the
// requested chapter's card. Gating every fallback selector on capture-mode
// having actually engaged turns that into a clean "no element" result, so
// the caller falls back to the chapter's own standinUrl instead.
async function findCardElement(page, selectorList) {
  if (!selectorList) return null;
  const captured = await page.evaluate(() => document.body.classList.contains("capture-mode"));
  if (!captured) return null;
  const selectors = selectorList.split(",").map((s) => s.trim()).filter(Boolean);
  for (const sel of selectors) {
    const el = await page.$(sel);
    if (el) return el;
  }
  return null;
}

// As of issue #16, the chapter card contract lays the card out at its real
// 1080x1350 CSS px (chapters.css), so an element screenshot at
// deviceScaleFactor 1 already comes back at the exact target size -- no
// upscale needed, which is the fix for the soft type this pass found (the
// old 420px card was upscaled ~2.6x here, softening it). This stays as a
// safety net only: it no-ops when the size already matches, and only
// resizes (logging so a regression is visible) if some future change to
// chapters.css's own card width drifts from 1080x1350 again.
async function ensureCardDimensions(filePath, targetW, targetH) {
  const buf = await readFile(filePath);
  const dims = pngDimensions(buf);
  if (dims && dims.width === targetW && dims.height === targetH) return;
  log(
    `WARNING: ${path.basename(filePath)} came back at ${dims ? `${dims.width}x${dims.height}` : "an unreadable size"}, ` +
      `not the expected ${targetW}x${targetH} -- resizing rather than shipping a mismatched card. ` +
      `Check chapters.css's .capture-card width/aspect-ratio.`
  );
  const tmp = `${filePath}.resize.png`;
  runFfmpeg(
    ["-y", "-i", filePath, "-vf", `scale=${targetW}:${targetH}`, tmp],
    `resize ${path.basename(filePath)} to ${targetW}x${targetH}`
  );
  await rename(tmp, filePath);
}

async function captureCarousel(browser, baseUrl, outDir, cardsPath) {
  const cards = JSON.parse(await readFile(cardsPath, "utf8"));

  const results = [];
  let usedStandin = false;

  for (let i = 0; i < cards.length; i++) {
    const card = cards[i];
    const idx = String(i).padStart(2, "0");
    const fileName = `card_${idx}_${card.name}.png`;
    const filePath = path.join(outDir, fileName);

    // A fresh page per card avoids any state or memory build-up from the
    // previous card's animation bleeding into this one's timing.
    const page = await browser.newPage();
    await page.setViewport({ width: 1080, height: 1350, deviceScaleFactor: 1 });

    await page.goto(`${baseUrl}${card.url}`, { waitUntil: "networkidle0" });
    await waitForPhaseComplete(page, 20000, `card "${card.name}" (${card.url})`);

    let usingStandin = false;

    if (card.captureMode === "clip") {
      await page.screenshot({ path: filePath, clip: { x: 0, y: 0, width: 1080, height: 1350 } });
    } else {
      // element mode: chapter card container, sized for a 1080x1350 capture
      let el = await findCardElement(page, card.selector);
      if (!el && card.standinUrl) {
        usingStandin = true;
        usedStandin = true;
        log(
          `card "${card.name}": chapter section not present at ${card.url} yet, using stand-in ${card.standinUrl}`
        );
        await page.goto(`${baseUrl}${card.standinUrl}`, { waitUntil: "networkidle0" });
        await waitForPhaseComplete(page, 20000, `card "${card.name}" stand-in (${card.standinUrl})`);
        await page.screenshot({ path: filePath, clip: { x: 0, y: 0, width: 1080, height: 1350 } });
      } else if (!el) {
        throw new Error(
          `card "${card.name}" (${card.url}): no element matched selector "${card.selector}" and no stand-in URL is configured`
        );
      } else {
        await el.screenshot({ path: filePath });
        await ensureCardDimensions(filePath, 1080, 1350);
      }
    }

    await page.close();
    results.push({ name: card.name, url: card.url, file: filePath, standin: usingStandin });
  }

  return { results, usedStandin };
}

// ---------------------------------------------------------------
// Carousel PDF (LinkedIn document-carousel upload format)
// ---------------------------------------------------------------
function buildCarouselPdf(cardFiles, outDir) {
  const pdfPath = path.join(outDir, "carousel.pdf");
  const script = `
import sys
from PIL import Image

files = sys.argv[1:-1]
out = sys.argv[-1]
pages = []
for f in files:
    im = Image.open(f).convert("RGB")
    pages.append(im)
if not pages:
    raise SystemExit("no card images to bundle")
pages[0].save(out, save_all=True, append_images=pages[1:])
`;
  const res = spawnSync("python3", ["-c", script, ...cardFiles, pdfPath], {
    encoding: "utf8",
  });
  if (res.status !== 0) {
    log("carousel.pdf skipped: " + (res.stderr || res.error || "python3/Pillow unavailable"));
    return null;
  }
  log(`wrote ${pdfPath}`);
  return pdfPath;
}

// ---------------------------------------------------------------
// Manifest
// ---------------------------------------------------------------
function pngDimensions(buf) {
  // IHDR chunk: width and height are 4-byte big-endian ints starting at byte 16.
  if (buf.length < 24) return null;
  const width = buf.readUInt32BE(16);
  const height = buf.readUInt32BE(20);
  return { width, height };
}

async function printManifest(outDir) {
  const entries = await readdir(outDir);
  entries.sort();
  log("---- manifest ----");
  for (const name of entries) {
    const filePath = path.join(outDir, name);
    const s = await stat(filePath);
    if (s.isDirectory()) continue;
    const sizeKb = (s.size / 1024).toFixed(1);
    let extra = "";
    if (name.endsWith(".png")) {
      const buf = await readFile(filePath);
      const dims = pngDimensions(buf);
      if (dims) extra = ` (${dims.width}x${dims.height})`;
    } else if (name.endsWith(".mp4") || name.endsWith(".webm")) {
      try {
        const info = ffprobeInfo(filePath);
        extra = ` (${info.width}x${info.height}, ${info.duration ? info.duration.toFixed(2) + "s" : "?"}, ${info.codec || "?"}/${info.pixFmt || "?"})`;
      } catch {
        // best effort
      }
    }
    log(`  ${name}: ${sizeKb} KB${extra}`);
  }
  log("-------------------");
}

// ---------------------------------------------------------------
// Main
// ---------------------------------------------------------------
async function main() {
  const opts = parseArgs(process.argv.slice(2));
  await mkdir(opts.out, { recursive: true });

  let serverProc = null;
  let baseUrl = opts.url;
  if (!baseUrl) {
    serverProc = await startServer(opts.port);
    baseUrl = `http://localhost:${opts.port}`;
  } else {
    log(`using externally supplied server at ${baseUrl}`);
  }

  let browser = null;
  try {
    browser = await puppeteer.launch({
      executablePath: CHROME_PATH,
      headless: true,
      args: [
        "--autoplay-policy=no-user-gesture-required",
        "--window-size=1600,1350",
      ],
    });

    const webmPath = await captureHero(browser, baseUrl, opts.out);
    const { mp4Path, portraitPath, mp4Info, portraitInfo } = transcodeHero(webmPath, opts.out);

    log(`hero.mp4: ${mp4Info.width}x${mp4Info.height}, ${mp4Info.duration?.toFixed(2)}s, codec=${mp4Info.codec}, pix_fmt=${mp4Info.pixFmt}, container=${mp4Info.formatName}`);
    log(`hero_portrait.mp4: ${portraitInfo.width}x${portraitInfo.height}, ${portraitInfo.duration?.toFixed(2)}s, codec=${portraitInfo.codec}, pix_fmt=${portraitInfo.pixFmt}, container=${portraitInfo.formatName}`);

    if (mp4Info.codec !== "h264") throw new Error(`hero.mp4 codec is ${mp4Info.codec}, expected h264`);
    if (mp4Info.pixFmt !== "yuv420p") throw new Error(`hero.mp4 pix_fmt is ${mp4Info.pixFmt}, expected yuv420p`);
    if (!/mp4/.test(mp4Info.formatName || "")) throw new Error(`hero.mp4 container is ${mp4Info.formatName}, expected mp4`);
    if (portraitInfo.width !== 1080 || portraitInfo.height !== 1350) {
      throw new Error(`hero_portrait.mp4 is ${portraitInfo.width}x${portraitInfo.height}, expected 1080x1350`);
    }

    const cardsPath = path.join(__dirname, "cards.json");
    const { results, usedStandin } = await captureCarousel(browser, baseUrl, opts.out, cardsPath);

    const cardFiles = results.map((r) => r.file);
    buildCarouselPdf(cardFiles, opts.out);

    await printManifest(opts.out);

    log("---- carousel cards ----");
    results.forEach((r) => log(`  ${path.basename(r.file)} <- ${r.url}${r.standin ? " (stand-in: chapters section not present)" : ""}`));
    if (usedStandin) {
      log("NOTE: one or more chapter cards used the ?settled=1&shot=N stand-in. Expected for chapters 6 and 8 (a plain prose chapter and \"the move\" summary), neither of which has a step-driven figure to capture; unexpected for any other chapter.");
    }
    log("done.");
  } finally {
    if (browser) await browser.close();
    stopServer(serverProc);
  }
}

main().catch((err) => {
  console.error("[social-export] FAILED:", err.message || err);
  process.exit(1);
});
