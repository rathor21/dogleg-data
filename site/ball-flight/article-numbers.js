/*
 * Every model number the article prose states, computed from the live model.
 * article.js writes each value into its <span data-num="key"> so the text
 * can match the figures and the lab. The HTML carries the value at the time of
 * writing as fallback text, and tests/article-numbers.mjs fails when a fallback
 * no longer matches this file's output.
 *
 * Each entry: key, what it is, how it is computed, and the formatted text.
 * docs/sources/004_Caption.md lists them all. A few entries are derived from
 * published numbers (marked "published" in `how`) and cannot drift with a refit.
 */
import {
  faceShare, startDirection, shotAt, exampleCheck, publishedRatio, attackSweep, couplingShot,
  driverWindows, nineWindows, coachingExample, TRACKMAN_TOTAL_2010, OPTIMIZER_DEFAULT_DRIVER,
} from "./article-data.js";

const MINUS = "−";
const grp = (v) => Math.round(v).toLocaleString("en-US");
const abs1 = (v) => Math.abs(v).toFixed(1);
const signed1 = (v) => `${v < 0 ? MINUS : "+"}${Math.abs(v).toFixed(1)}`;

/** Returns [{key, label, how, text}] for a built model. */
export function computeNumbers(model) {
  const out = [];
  const put = (key, label, how, text) => out.push({ key, label, how, text });

  // Chapter 1
  const sd = startDirection(model);
  const drv = sd[0].rows;
  const shDrv = faceShare(model, "driver");
  const sh6 = faceShare(model, "6i");
  put("share-drv", "Face share of start direction, Tour driver (percent)", "launch direction at face +1, path 0, over 1 degree", shDrv.toFixed(0));
  put("share-6i", "Face share of start direction, Tour 6-iron (percent)", "same, 6-iron", sh6.toFixed(0));
  put("gap-drv-85", "Points under the circulating 85 percent driver share", "85 minus share-drv (unrounded)", (85 - shDrv).toFixed(0));
  put("gap-drv-87", "Points under the circulating 87 percent driver share", "87 minus share-drv (unrounded)", (87 - shDrv).toFixed(0));
  put("gap-6i-75", "Points under the circulating 75 percent iron share", "75 minus share-6i (unrounded)", (75 - sh6).toFixed(0));
  put("gap-6i-81", "Points under the circulating 81 percent iron share", "81 minus share-6i (unrounded)", (81 - sh6).toFixed(0));
  put("sd-drv-face4", "Start direction, Tour driver, face +4 at path 0 (degrees)", "launch.launchDirDeg", abs1(drv[1].deg));
  put("sd-drv-path4", "Start direction, Tour driver, path +4 at face 0 (degrees)", "launch.launchDirDeg", abs1(drv[3].deg));

  // Chapter 2
  const c2 = (club) => shotAt(model, club, "pga", { face: 2, path: 0 });
  const cd = c2("driver").flight.curve, c6 = c2("6i").flight.curve, cp = c2("pw").flight.curve;
  put("curve2-drv", "Curve, Tour driver, face-to-path +2 (yd)", "flight.curve", abs1(cd));
  put("curve2-6i", "Curve, Tour 6-iron, face-to-path +2 (yd)", "flight.curve", abs1(c6));
  put("curve2-pw", "Curve, Tour PW, face-to-path +2 (yd)", "flight.curve", abs1(cp));
  put("ratio-drv-pw", "Model: driver curve over PW curve at the same face-to-path (extrapolated)", "curve2-drv / curve2-pw", (cd / cp).toFixed(1));
  put("ratio-drv-6i", "Model: driver curve over 6-iron curve at the same face-to-path", "curve2-drv / curve2-6i", (cd / c6).toFixed(1));
  const pr = publishedRatio();
  put("tm-ratio", "TrackMan published: driver curve per degree over 6-iron curve per degree, both tours", "published; mean of the two examples per club, per tour (PGA and LPGA agree to 1 decimal)", ((pr.pga + pr.lpga) / 2).toFixed(1));
  put("tm-ratio-pga", "TrackMan published ratio, PGA examples", "published; 9.15 / 4.0 yd per degree", pr.pga.toFixed(1));
  put("tm-ratio-lpga", "TrackMan published ratio, LPGA examples", "published; 6.7 / 2.9 yd per degree", pr.lpga.toFixed(1));
  const sl = (club) => shotAt(model, club, "pga").launch.spinLoftDeg;
  put("sl-drv", "Spin loft, Tour driver preset (degrees, model-derived)", "launch.spinLoftDeg", sl("driver").toFixed(1));
  put("sl-pw", "Spin loft, Tour PW preset (degrees, model-derived)", "launch.spinLoftDeg", sl("pw").toFixed(0));
  const ex = exampleCheck(model);
  const worstYd = ex.reduce((a, e) => (Math.abs(e.miss) > Math.abs(a.miss) ? e : a));
  const worstPct = ex.reduce((a, e) => (Math.abs(e.pct) > Math.abs(a.pct) ? e : a));
  put("ex-miss-yd", "Largest gap between a preset line and a TrackMan example (yd)", "max |model - published| over the eight examples", Math.abs(worstYd.miss).toFixed(1));
  put("ex-miss-yd-pct", "That gap as percent of the example's published curve", "|miss| / |published|", Math.abs(worstYd.pct).toFixed(0));
  put("ex-pct-max", "Largest percent gap between a preset line and an example", "max |miss| / |published|", Math.abs(worstPct.pct).toFixed(0));
  put("ex-pct-yd", "That gap in yards", "|miss| of that example", Math.abs(worstPct.miss).toFixed(1));

  // Chapter 3
  const sw = attackSweep(model);
  const at = (a) => sw.rows.find((r) => r.attack === a);
  const lo = at(-6), hi = at(6), top = at(10);
  const lastIn = [...sw.rows].reverse().find((r) => !r.extrapolated);
  put("atk-loft", "Tour driver dynamic loft held fixed (degrees, model-derived)", "preset dynLoft", sw.dynLoft.toFixed(1));
  put("atk-launch-dn", "Launch at attack angle -6 (degrees)", "launch.launchDeg", lo.launch.toFixed(1));
  put("atk-launch-up", "Launch at attack angle +6 (degrees)", "launch.launchDeg", hi.launch.toFixed(1));
  put("atk-spin-dn", "Spin at attack angle -6, with the preset spin trim (rpm)", "launch.spinRpm", grp(lo.spin));
  put("atk-spin-up", "Spin at attack angle +6, with the preset spin trim (rpm)", "launch.spinRpm", grp(hi.spin));
  put("atk-spin-up-nt", "Spin at attack angle +6, no trim (rpm)", "launch.spinRpm with spinTrim 1", grp(hi.spinUntrimmed));
  put("atk-sl-dn", "Spin loft at attack angle -6 (degrees)", "launch.spinLoftDeg", lo.spinLoft.toFixed(1));
  put("atk-sl-up", "Spin loft at attack angle +6 (degrees)", "launch.spinLoftDeg", hi.spinLoft.toFixed(1));
  put("atk-last-in", "Highest whole attack angle still inside the chart's spin loft range", "last row with spin loft >= k_sl_lo_driver", `+${lastIn.attack}`);
  put("atk10-sl", "Spin loft at attack angle +10 (degrees)", "launch.spinLoftDeg", top.spinLoft.toFixed(1));
  put("atk10-spin", "Spin at attack angle +10, with the trim (rpm)", "launch.spinRpm", grp(top.spin));
  put("sl-floor", "Lowest spin loft in the driver's calibration (degrees)", "model.json launch_model.k_sl_lo_driver", sw.floor.toFixed(1));
  put("sl-ceil", "Highest spin loft in the driver's calibration (degrees)", "model.json launch_model.k_sl_hi_driver", sw.ceil.toFixed(1));
  put("trim", "PGA driver spin trim", "presets.json spin_trim", sw.spinTrim.toFixed(2));
  put("trim-pct", "Percent the Tour average spins under the model for the same delivery", "(1 - trim) x 100", ((1 - sw.spinTrim) * 100).toFixed(0));
  const cp2 = couplingShot(model);
  put("plane", "Swing plane, Combine average driver (degrees)", "model.json swing_plane_default_deg", cp2.plane.toFixed(0));
  put("per-deg", "Path added per degree of down attack (degrees)", "tan(90 - plane)", cp2.perDegree.toFixed(2));
  put("couple-path", "Path after steepening by 4 degrees, swing direction held (degrees right)", "swingPath", abs1(cp2.path));
  put("couple-curve", "Curve of that shot with the face square (yd left)", "flight.curve", Math.abs(cp2.shot.flight.curve).toFixed(0));
  put("couple-start", "Start direction of that shot (degrees)", "launch.launchDirDeg", Math.abs(cp2.shot.launch.launchDirDeg).toFixed(1));
  put("couple-launch", "Launch of that shot (degrees)", "launch.launchDeg", cp2.shot.launch.launchDeg.toFixed(1));
  put("couple-spin", "Spin of that shot (rpm)", "launch.spinRpm", grp(cp2.shot.launch.spinRpm));

  // Chapter 4
  const [pg, lp, am] = driverWindows(model);
  put("pga-tm-launch", "TrackMan 2010 carry chart launch, PGA driver (degrees)", "trackmanCarry2010(115, -0.9), interpolated between published cells", pg.tm.launch_deg.toFixed(1));
  put("pga-ping-launch", "PING 2019 launch, PGA driver at 171 mph ball speed (degrees)", "ping2019(171, -0.9), interpolated", pg.ping.launch_deg.toFixed(1));
  put("lpga-tm-launch", "TrackMan 2010 carry chart launch, LPGA driver (degrees)", "trackmanCarry2010(96, 2.8), interpolated", lp.tm.launch_deg.toFixed(1));
  put("lpga-ping-launch", "PING 2019 launch, LPGA driver at 143 mph ball speed (degrees)", "ping2019(143, 2.8), interpolated", lp.ping.launch_deg.toFixed(1));
  put("lpga-total-launch", "TrackMan 2010 total-distance chart launch, LPGA driver (degrees)", "bilinear lookup in the published TOTAL chart (96 mph, +2.8)", lp.total.launch_deg.toFixed(1));
  put("lpga-gap-lo", "LPGA average launch under the nearer of the carry chart and PING (degrees)", "min(tm, ping) - 12.6", (Math.min(lp.tm.launch_deg, lp.ping.launch_deg) - lp.avg.launch).toFixed(1));
  put("lpga-gap-hi", "LPGA average launch under the farther of the carry chart and PING (degrees)", "max(tm, ping) - 12.6", (Math.max(lp.tm.launch_deg, lp.ping.launch_deg) - lp.avg.launch).toFixed(1));
  put("am-tm-spin", "TrackMan 2010 carry chart spin, amateur driver (rpm)", "trackmanCarry2010(94, -1.8), interpolated", grp(am.tm.spin_rpm));
  put("am-ping-spin", "PING 2019 spin, amateur driver at 133 mph ball speed (rpm)", "ping2019(133, -1.8), interpolated", grp(am.ping.spin_rpm));
  put("am-ping-gap", "Amateur average spin over PING's (rpm)", "3,275 minus ping2019 spin", grp(am.avg.spin - am.ping.spin_rpm));
  put("am-def-gap", "Amateur average spin over TrackMan's current Optimizer default (rpm, to the nearest 50)", "published: 3,275 minus 2,772", grp(Math.round((am.avg.spin - OPTIMIZER_DEFAULT_DRIVER.spin) / 50) * 50));

  // Chapter 5
  const nw = Object.fromEntries(nineWindows(model).map((n) => [n.key, n]));
  const dl = (k) => nw[k].delivery, fl = (k) => nw[k].shot.flight;
  const tg = model.windows.targets;
  put("w-apl", "Attack angle per degree of loft in the height lever", "windows.json targets.attack_per_loft", tg.attack_per_loft.toFixed(1));
  put("t-low", "Low window peak height as percent of the standard shot", "windows.json targets.heights.low x 100", (tg.heights.low * 100).toFixed(0));
  put("t-high", "High window peak height as percent of the standard shot", "windows.json targets.heights.high x 100", (tg.heights.high * 100).toFixed(0));
  put("t-curve", "Draw and fade bend as percent of carry", "windows.json targets.curve_frac.fade x 100", (tg.curve_frac.fade * 100).toFixed(0));
  put("w-low-loft", "Straight low: dynamic loft (degrees)", "windows.json recipe", dl("low_straight").dynLoft.toFixed(1));
  put("w-low-aoa", "Straight low: attack angle (degrees down)", "windows.json recipe", abs1(dl("low_straight").attack));
  put("w-low-carry", "Straight low: carry (yd)", "flight.carry", fl("low_straight").carry.toFixed(0));
  put("w-low-h", "Straight low: peak height (yd)", "flight.maxHeight", fl("low_straight").maxHeight.toFixed(0));
  put("w-mid-loft", "Straight mid: dynamic loft (degrees)", "windows.json recipe", dl("mid_straight").dynLoft.toFixed(1));
  put("w-mid-aoa", "Straight mid: attack angle (degrees down)", "windows.json recipe", abs1(dl("mid_straight").attack));
  put("w-mid-carry", "Straight mid: carry (yd)", "flight.carry", fl("mid_straight").carry.toFixed(0));
  put("w-mid-h", "Straight mid: peak height (yd)", "flight.maxHeight", fl("mid_straight").maxHeight.toFixed(0));
  put("w-high-loft", "Straight high: dynamic loft (degrees)", "windows.json recipe", dl("high_straight").dynLoft.toFixed(1));
  put("w-high-aoa", "Straight high: attack angle (degrees up)", "windows.json recipe", abs1(dl("high_straight").attack));
  put("w-high-carry", "Straight high: carry (yd)", "flight.carry", fl("high_straight").carry.toFixed(0));
  put("w-high-h", "Straight high: peak height (yd)", "flight.maxHeight", fl("high_straight").maxHeight.toFixed(0));
  const draws = ["low_draw", "mid_draw", "high_draw"];
  const rng = (f) => { const v = draws.map(f); return [Math.min(...v), Math.max(...v)]; };
  const [faceLo, faceHi] = rng((k) => dl(k).face);
  const [pathLo, pathHi] = rng((k) => dl(k).path);
  const [crvLo, crvHi] = rng((k) => Math.abs(fl(k).curve));
  put("w-face-lo", "Draw windows: smallest face angle (degrees right)", "windows.json recipes", faceLo.toFixed(1));
  put("w-face-hi", "Draw windows: largest face angle (degrees right)", "windows.json recipes", faceHi.toFixed(1));
  put("w-path-lo", "Draw windows: smallest path (degrees right)", "windows.json recipes", pathLo.toFixed(1));
  put("w-path-hi", "Draw windows: largest path (degrees right)", "windows.json recipes", pathHi.toFixed(1));
  put("w-curve-lo", "Draw windows: smallest curve (yd)", "flight.curve", crvLo.toFixed(1));
  put("w-curve-hi", "Draw windows: largest curve (yd)", "flight.curve", crvHi.toFixed(1));
  for (const h of ["low", "mid", "high"]) {
    put(`w-f2p-${h}`, `${h[0].toUpperCase()}${h.slice(1)} draw: face-to-path (degrees)`, "recipe face minus path", signed1(dl(`${h}_draw`).face - dl(`${h}_draw`).path));
  }

  // Chapter 6
  const ce = coachingExample(model);
  put("cx-name", "Shot name, amateur driver, path -4, face 0", "classification.name, lower case", ce.a.classification.name.toLowerCase());
  put("cx-curve", "Curve of that shot (yd right)", "flight.curve", Math.abs(ce.a.flight.curve).toFixed(0));
  put("cx-finish", "Where it finishes (yd right)", "flight.side", Math.abs(ce.a.flight.side).toFixed(0));
  put("cx-curve2", "Curve with the path moved to -2 (yd right)", "flight.curve", Math.abs(ce.b.flight.curve).toFixed(0));

  // Method and limits
  const pgaDrv = shotAt(model, "driver", "pga");
  const pubCarry = model.data.presets.published.pga.driver.carry_yd;
  put("pga-drv-carry", "PGA driver preset carry (yd)", "flight.carry at the preset", pgaDrv.flight.carry.toFixed(0));
  put("pga-drv-gap", "Published PGA driver carry minus the preset's (yd)", "282 - flight.carry", (pubCarry - pgaDrv.flight.carry).toFixed(0));
  put("pga-drv-gap-pct", "That gap in percent of the published carry", "gap / 282", (((pubCarry - pgaDrv.flight.carry) / pubCarry) * 100).toFixed(0));
  put("pga-drv-ball", "PGA driver preset ball speed (mph)", "launch.ballSpeedMph", pgaDrv.launch.ballSpeedMph.toFixed(1));
  const noTrim = model.shot({ ...model.preset("driver", "pga"), spinTrim: 1 });
  put("pga-drv-spin-nt", "PGA driver spin with no trim (rpm)", "launch.spinRpm with spinTrim 1", grp(noTrim.launch.spinRpm));
  const trims = [];
  for (const c of model.clubs) for (const p of model.players) trims.push(model.preset(c.id, p.id).spinTrim);
  put("trim-min", "Smallest preset spin trim", "min over all presets", Math.min(...trims).toFixed(2));
  put("trim-max", "Largest preset spin trim", "max over all presets", Math.max(...trims).toFixed(2));
  return out;
}
export { signed1, TRACKMAN_TOTAL_2010 };
