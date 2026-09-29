#!/usr/bin/env node
/*
 * Merge judge_rep*.jsonl into results.jsonl and print a per-variant summary.
 *
 *   node eval/lab/merge.mjs [--flow-dir .claude/hillclimb/lab] [--variant baseline|v1|...]  (default: every variant dir)
 *
 * Per case the row's grade gains: design (mean over judge reps of each rep's mean of eight passes),
 * c1..c8 (mean over reps), all_pass (1 when design == 1). row.explanation gets {c1..c8: reason from rep 0},
 * row.judge_model is set. The merge is idempotent: it reads judge files fresh each run.
 * results.jsonl is rewritten atomically (temp file + rename).
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../..");
const CLAIMS = ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"];
const JUDGE_MODEL = "claude-sonnet-5-5 (Claude Code subagent)";
const PERF = ["console_errors", "overflow_x", "min_font_px", "small_targets", "axe_serious", "above_fold_ok", "load_ms", "input_p50_ms", "input_p95_ms", "input_frame_p95_ms", "input_sync_p50_ms", "input_sync_p95_ms", "js_kb", "total_kb"];

const args = process.argv.slice(2);
const opt = (name, dflt) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : dflt; };
const flow = path.resolve(ROOT, opt("--flow-dir", ".claude/hillclimb/lab"));
const only = opt("--variant", null);

const readJsonl = (p, warn) => {
  if (!fs.existsSync(p)) return [];
  const out = [];
  fs.readFileSync(p, "utf8").split("\n").forEach((l, i) => {
    if (!l.trim()) return;
    try { out.push(JSON.parse(l)); } catch { warn?.(`${path.basename(p)} line ${i + 1}: invalid JSON, skipped`); }
  });
  return out;
};
const mean = (xs) => (xs.length ? xs.reduce((s, x) => s + x, 0) / xs.length : NaN);
const sd = (xs) => { const m = mean(xs); return Math.sqrt(mean(xs.map((x) => (x - m) ** 2))); };

// seeded PRNG so the CI is reproducible
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
function bootCI(xs, iters = 4000, seed = 20260929) {
  if (xs.length < 2) return [NaN, NaN];
  const r = rng(seed), ms = [];
  for (let b = 0; b < iters; b++) { let s = 0; for (let i = 0; i < xs.length; i++) s += xs[Math.floor(r() * xs.length)]; ms.push(s / xs.length); }
  ms.sort((a, b) => a - b);
  return [ms[Math.floor(0.025 * iters)], ms[Math.ceil(0.975 * iters) - 1]];
}
const f = (v, d = 3) => (Number.isFinite(v) ? v.toFixed(d) : "n/a");

function validClaims(line) {
  if (!line || typeof line.claims !== "object" || line.claims === null) return false;
  return CLAIMS.every((c) => line.claims[c] && (line.claims[c].pass === 0 || line.claims[c].pass === 1));
}

function mergeVariant(variant) {
  const dir = path.join(flow, variant);
  const resPath = path.join(dir, "results.jsonl");
  const rows = readJsonl(resPath);
  if (!rows.length) { console.log(`${variant}: no results.jsonl rows`); return null; }
  const warnings = [];
  const judgeFiles = fs.readdirSync(dir).filter((n) => /^judge_rep\d+\.jsonl$/.test(n)).sort((a, b) => Number(a.match(/\d+/)) - Number(b.match(/\d+/)));
  // byCase[id][rep] = judge line (last valid line wins)
  const byCase = {};
  for (const jf of judgeFiles) {
    const k = Number(jf.match(/\d+/)[0]);
    for (const line of readJsonl(path.join(dir, jf), (w) => warnings.push(`${jf}: ${w}`))) {
      if (!validClaims(line)) { warnings.push(`${jf}: ${line?.prompt_id}: malformed claims, skipped`); continue; }
      (byCase[line.prompt_id] ||= {})[k] = line;
    }
  }
  let judged = 0;
  for (const row of rows) {
    const reps = byCase[row.prompt_id];
    if (!reps) continue;
    const ks = Object.keys(reps).map(Number).sort((a, b) => a - b);
    const per = ks.map((k) => reps[k]);
    const g = { ...row.grade };
    for (const c of CLAIMS) g[c] = mean(per.map((l) => l.claims[c].pass));
    g.design = mean(per.map((l) => mean(CLAIMS.map((c) => l.claims[c].pass))));
    g.all_pass = g.design === 1 ? 1 : 0;
    row.grade = g;
    const first = reps[ks[0]];
    row.explanation = Object.fromEntries(CLAIMS.map((c) => [c, String(first.claims[c].reason || "")]));
    row.judge_model = JUDGE_MODEL;
    row.judge_reps = ks.length;
    judged++;
  }
  const tmp = resPath + ".tmp";
  fs.writeFileSync(tmp, rows.map((r) => JSON.stringify(r)).join("\n") + "\n");
  fs.renameSync(tmp, resPath);

  // ---- summary
  console.log(`\n=== ${variant}: ${rows.length} cases, ${judged} judged, ${judgeFiles.length} judge rep file(s) ===`);
  for (const w of warnings.slice(0, 10)) console.log("  warning: " + w);
  const scored = rows.filter((r) => Number.isFinite(r.grade.design));
  if (scored.length) {
    const ds = scored.map((r) => r.grade.design);
    const [lo, hi] = bootCI(ds);
    console.log(`design  mean ${f(mean(ds))}  95% CI [${f(lo)}, ${f(hi)}] (bootstrap over ${ds.length} cases)  all_pass ${scored.filter((r) => r.grade.all_pass === 1).length}/${scored.length}`);
    console.log("claims  " + CLAIMS.map((c) => `${c} ${f(mean(scored.map((r) => r.grade[c])), 2)}`).join("  "));
    const strata = {};
    for (const r of scored) (strata[r.tags[0]] ||= []).push(r.grade.design);
    console.log("by viewport class  " + Object.entries(strata).map(([k, v]) => `${k} ${f(mean(v), 2)} (n=${v.length})`).join("  "));
    // inter-rep agreement over claim grades where rep0 and rep1 both exist
    let same = 0, tot = 0;
    for (const reps of Object.values(byCase)) {
      if (!reps[0] || !reps[1]) continue;
      for (const c of CLAIMS) { tot++; if (reps[0].claims[c].pass === reps[1].claims[c].pass) same++; }
    }
    console.log(tot ? `judge inter-rep agreement (rep0 vs rep1): ${f(same / tot, 3)} (${same}/${tot} claim grades identical)` : "judge inter-rep agreement: n/a (fewer than two reps)");
  } else {
    console.log("design  not judged yet");
  }
  const pm = PERF.map((k) => {
    const xs = rows.map((r) => r.grade[k]).filter(Number.isFinite);
    return `${k} ${f(mean(xs), k === "min_font_px" || k.startsWith("input") || k.endsWith("_kb") ? 1 : 2)}`;
  });
  console.log("programmatic means  " + pm.join("  "));
  return { variant, rows };
}

const variants = fs.readdirSync(flow, { withFileTypes: true })
  .filter((e) => e.isDirectory() && /^(baseline|v\d+)$/.test(e.name) && (!only || e.name === only))
  .map((e) => e.name)
  .sort((a, b) => (a === "baseline" ? -1 : b === "baseline" ? 1 : Number(a.slice(1)) - Number(b.slice(1))));
if (!variants.length) { console.error("no variant directories found in " + flow); process.exit(1); }
for (const v of variants) mergeVariant(v);
