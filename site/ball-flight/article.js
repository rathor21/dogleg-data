/*
 * Article bootstrap for /ball-flight/ (release 004). Loads the live model from
 * flight.js, writes every data-num span from article-numbers.js, and draws the
 * five figures and the preset table. If the model fails to load, the prose
 * keeps the fallback numbers written in the HTML and each figure shows a note.
 */
import { loadModel } from "./flight.js";
import { computeNumbers } from "./article-numbers.js";
import { drawStart } from "./fig-start.js";
import { drawCurve } from "./fig-curve.js";
import { drawAttack } from "./fig-attack.js";
import { drawDriver } from "./fig-driver.js";
import { drawWindows } from "./fig-windows.js";
import { drawPresets } from "./fig-presets.js";

const FIGS = { start: drawStart, curve: drawCurve, attack: drawAttack, driver: drawDriver, windows: drawWindows, presets: drawPresets };

function failed(err) {
  console.error("Ball flight article: model failed to load", err);
  for (const fig of document.querySelectorAll("figure[data-fig]")) {
    const host = fig.querySelector(".fig-plot, .tbl-wrap");
    if (host) host.textContent = "The live figure could not load. The numbers in the text are the values at the time of writing.";
  }
}

async function main() {
  const model = await loadModel();
  const nums = new Map(computeNumbers(model).map((n) => [n.key, n.text]));
  for (const el of document.querySelectorAll("[data-num]")) {
    const v = nums.get(el.dataset.num);
    if (v === undefined) console.warn("Unknown data-num key", el.dataset.num);
    else el.textContent = v;
  }
  for (const fig of document.querySelectorAll("figure[data-fig]")) {
    const draw = FIGS[fig.dataset.fig];
    if (draw) draw(fig, model);
  }
  document.documentElement.dataset.figuresReady = "true";
}

main().catch(failed);
