// Drift check for the article. Loads the model from data/, computes every
// number in article-numbers.js and compares it with the fallback text inside
// each <span data-num="key"> in index.html. Exit code 1 on any mismatch or on
// a key that is missing from either side.
//   node site/ball-flight/tests/article-numbers.mjs
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, "..");
const { createModel } = await import(path.join(root, "flight.js"));
const { computeNumbers } = await import(path.join(root, "article-numbers.js"));

const json = {};
for (const n of ["model", "presets", "ideals", "windows", "camera"]) {
  json[n] = JSON.parse(fs.readFileSync(path.join(root, "data", `${n}.json`), "utf8"));
}
const nums = computeNumbers(createModel(json));
const html = fs.readFileSync(path.join(root, "index.html"), "utf8").replace(/<!--[\s\S]*?-->/g, "");
const found = [...html.matchAll(/<span data-num="([^"]+)">([^<]*)<\/span>/g)];
let bad = 0;
const used = new Set();
for (const [, key, text] of found) {
  used.add(key);
  const n = nums.find((x) => x.key === key);
  if (!n) { console.log(`no such key: ${key}`); bad++; continue; }
  if (n.text !== text) { console.log(`drift ${key}: html "${text}" model "${n.text}"`); bad++; }
}
for (const n of nums) if (!used.has(n.key)) console.log(`unused (ok): ${n.key}`);
console.log(bad ? `${bad} problem(s)` : `ok, ${found.length} numbers match`);
process.exit(bad ? 1 : 0);
