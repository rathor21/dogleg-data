#!/usr/bin/env node
/*
 * Produce the two grader sanity screenshots under .claude/hillclimb/lab/calibration/:
 *   null_blank.png         a blank cream page at 1440x900 (no app at all)
 *   bad_hidden_label.png   the laptop-straight-7i case with the shot label and key tiles hidden by injected CSS
 * The judge must fail these (design near 0 for the blank page, c1 and c3 failing for the hidden label).
 */
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../..");
const SITE = path.join(ROOT, "site");
const OUT = path.join(ROOT, ".claude/hillclimb/lab/calibration");
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml", ".jpg": "image/jpeg", ".png": "image/png" };

fs.mkdirSync(OUT, { recursive: true });
const c = JSON.parse(fs.readFileSync(path.join(HERE, "cases.json"), "utf8")).find((x) => x.id === "laptop-straight-7i");
const server = http.createServer((req, res) => {
  const f = path.normalize(path.join(SITE, decodeURIComponent(new URL(req.url, "http://x").pathname)));
  if (!f.startsWith(SITE + path.sep) || !fs.existsSync(f) || !fs.statSync(f).isFile()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { "content-type": MIME[path.extname(f)] || "application/octet-stream" });
  res.end(fs.readFileSync(f));
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const port = server.address().port;
const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ["--hide-scrollbars", "--force-color-profile=srgb"] });
try {
  let ctx = await browser.createBrowserContext();
  let page = await ctx.newPage();
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
  await page.setContent('<!doctype html><html><body style="margin:0;background:#F4EDE0"></body></html>');
  await page.screenshot({ path: path.join(OUT, "null_blank.png"), type: "png" });
  await ctx.close();

  ctx = await browser.createBrowserContext();
  page = await ctx.newPage();
  await page.setViewport({ width: c.viewport.w, height: c.viewport.h, deviceScaleFactor: c.viewport.dpr });
  await page.emulateMediaFeatures([{ name: "prefers-reduced-motion", value: "reduce" }]);
  await page.goto(`http://127.0.0.1:${port}/ball-flight/tool.html?${c.url}`, { waitUntil: "networkidle2" });
  await page.waitForFunction(() => window.__labReady === true && document.getElementById("sl-name").textContent.trim());
  await page.addStyleTag({ content: "#shot-label,#key-tiles{display:none !important}" });
  await new Promise((r) => setTimeout(r, 600));
  await page.screenshot({ path: path.join(OUT, "bad_hidden_label.png"), type: "png" });
  await ctx.close();
} finally {
  await browser.close();
  server.close();
}
console.log("wrote", fs.readdirSync(OUT).join(", "));
