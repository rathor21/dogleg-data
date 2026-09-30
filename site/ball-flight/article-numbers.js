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
  driverWindows, nineWindows, coachingExample, chartGains, driverIdeals, idealTotalReversal, couplingDemo, drawFadeCheck, ironFlip, hookPeak, TRACKMAN_TOTAL_2010, OPTIMIZER_DEFAULT_DRIVER,
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
  put("ex-miss-yd", "Largest gap between a preset line and a TrackMan example (yd)", "max |model - published| over the eight examples", Math.abs(worstYd.miss).toFixed(1));
  put("ex-miss-yd-pct", "That gap as percent of the example's published curve", "|miss| / |published|", Math.abs(worstYd.pct).toFixed(0));

  // Chapter 2, loft from face-to-path
  const cpd = couplingDemo(model);
  const r0 = (v) => Math.round(v).toString();
  put("kappa-drv", "Loft added per degree of face-to-path, driver (cotangent of the 58.5 degree lie)", "model.couplingKappa", cpd.driver.kappa.toFixed(2));
  put("kappa-7i", "Same, 7-iron (63.0 degree lie)", "model.couplingKappa", cpd["7i"].kappa.toFixed(2));
  for (const [club, id] of [["driver", "drv"], ["7i", "7i"]]) {
    for (const [shot, k] of [["draw", "draw"], ["fade", "fade"], ["hook", "hook"], ["slice", "slice"]]) {
      if (club === "driver" && (shot === "hook" || shot === "slice")) continue;
      const name = `${club === "driver" ? "Tour driver" : "Tour 7-iron"} ${shot === "hook" ? "pull hook (path -2, face -6)" : shot === "slice" ? "push slice (path +2, face +6)" : shot === "draw" ? "draw (path +4, face 0)" : "fade (path -4, face 0)"}`;
      put(`cp-${id}-${k}-carry`, `${name}: carry (yd)`, "flight.carry", r0(cpd[club][shot].carry));
      put(`cp-${id}-${k}-total`, `${name}: total (yd)`, "carry plus model.roll", r0(cpd[club][shot].total));
    }
  }
  put("cp-drv-carry-gap", "Tour driver: fade carry over draw carry (yd)", "cp-drv-fade-carry minus cp-drv-draw-carry (unrounded)", (cpd.driver.fade.carry - cpd.driver.draw.carry).toFixed(1));
  put("cp-drv-total-gap", "Tour driver: draw total over fade total (yd)", "cp-drv-draw-total minus cp-drv-fade-total (unrounded)", (cpd.driver.draw.total - cpd.driver.fade.total).toFixed(1));
  const hp = hookPeak(model);
  put("hook-peak-f2p", "Face-to-path at which a closed Tour driver face curves the ball most, path 0 (degrees)", "hookPeak: scan of face -15 to -1 in half degrees", `${hp.f2p < 0 ? MINUS : "+"}${Math.abs(hp.f2p).toFixed(0)}`);
  put("hook-peak-yd", "That largest curve (yd)", "flight.curve at the peak", hp.curve.toFixed(0));
  put("t1-draw-carry", "Tour driver draw (path +4, face 0) at the chart's strike, spin trim 1.0: carry (yd)", "flight.carry with spinTrim 1", r0(hp.drawCarry));
  put("t1-fade-carry", "Same, fade (path -4): carry (yd)", "flight.carry with spinTrim 1", r0(hp.fadeCarry));
  const dfc = drawFadeCheck(model);
  put("df-spin-gap", "Model check: spin of the fade over the draw when the loft gap is TrackMan's 4.5 degrees (rpm)", "drawFadeCheck; TrackMan's gap is 1,125", grp(dfc.spinGap));
  put("df-run-gap", "Model check: run-out of the draw over the fade (yd)", "drawFadeCheck; TrackMan says about 20", dfc.runGap.toFixed(0));

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

  // Chapter 3, the iron flip
  const irf = ironFlip(model);
  put("ir-slope", "Loft added per degree of attack for irons, wedges, hybrids and fairway woods (MODELED)", "model.json coupling.loft_per_attack", irf.slope.toFixed(1));
  put("ir-atk-dn", "Tour 7-iron preset attack angle (degrees)", "model.preset", signed1(irf.attackDn));
  put("ir-loft-dn", "Tour 7-iron loft at the preset attack (degrees)", "model.loftForAttack", model.loftForAttack("7i", "pga", irf.attackDn).toFixed(1));
  put("ir-loft-up", "Tour 7-iron loft at attack +3 with loft following (degrees)", "model.loftForAttack", model.loftForAttack("7i", "pga", 3).toFixed(1));
  put("ir-carry-dn", "Tour 7-iron carry at the preset attack (yd)", "flight.carry", r0(irf.dn.flight.carry));
  put("ir-carry-up", "Tour 7-iron carry at attack +3, loft following (yd)", "flight.carry", r0(irf.up.flight.carry));
  put("ir-total-dn", "Tour 7-iron total at the preset attack (yd)", "carry plus model.roll", r0(irf.dn.total));
  put("ir-total-up", "Tour 7-iron total at attack +3, loft following (yd)", "carry plus model.roll", r0(irf.up.total));
  put("ir-carry-loss", "Carry lost from the preset attack to +3 (yd)", "ir-carry-dn minus ir-carry-up (unrounded)", r0(irf.dn.flight.carry - irf.up.flight.carry));
  put("ir-total-loss", "Total lost over the same change (yd)", "ir-total-dn minus ir-total-up (unrounded)", r0(irf.dn.total - irf.up.total));
  put("ir-model-slope", "Model: Tour 7-iron at 90 mph, carry lost per degree of attack from -6 to +2, loft following (yd)", "flight.carry at the two attack angles over 8", irf.modelSlope.toFixed(1));
  put("ir-chart-slope", "Foresight 7 iron chart at 90 mph: carry lost per degree from -6 to +2 (yd)", "published; (183.4 - 169.5) / 8", irf.chartSlope.toFixed(1));
  put("ir-am-peak", "Attack angle of the average amateur 7-iron's most carry, loft following (degrees)", "scan of -8 to +6 in half degrees", signed1(irf.amateurPeak.attack));

  // Chapter 3, the driver and hitting up
  const cg = chartGains(model);
  put("ch-carry-dn", "TrackMan 2010 carry chart carry at 115 mph, attack -5 (yd)", "published; ideals.json driver.trackman_carry_2010.carry_yd", grp(cg.cr.chartCarryDn));
  put("ch-carry-up", "TrackMan 2010 carry chart carry at 115 mph, attack +5 (yd)", "published; same", grp(cg.cr.chartCarryUp));
  put("ch-carry-gain", "TrackMan carry chart: carry gained from attack -5 to +5 at 115 mph (yd)", "published; ch-carry-up minus ch-carry-dn", grp(cg.cr.chartCarryGain));
  put("ch-total-gain", "TrackMan carry chart: total distance gained from attack -5 to +5 at 115 mph (yd)", "published; total_yd of the carry rows", grp(cg.cr.chartTotalGain));
  put("ch-total-gain-tt", "TrackMan total-distance chart: total distance gained from attack -5 to +5 at 115 mph (yd)", "published; total_yd of the total rows", grp(cg.tt.chartTotalGain));
  put("md-carry-gain", "Model flown from the carry chart's launch conditions: carry gained from attack -5 to +5 at 115 mph (yd)", "model.simulate at each row's ball speed, launch and spin, axis 0", grp(cg.cr.modelCarryGain));
  put("md-total-gain", "Same: total distance gained (yd)", "carry plus model.roll", grp(cg.cr.modelTotalGain));
  let fxPeak = sw.rows[0];
  for (const r of sw.rows) if (r.carry > fxPeak.carry) fxPeak = r;
  put("fx-peak-carry", "Tour driver, loft held at the preset: highest carry in the sweep (yd)", "flight.carry, spin trim on; max over attack -6 to +10", grp(fxPeak.carry));
  put("fx-peak-atk", "Attack angle of that highest carry (degrees)", "argmax of the same sweep", `+${fxPeak.attack}`);
  put("fx-carry-p5", "Tour driver, loft held: carry at attack +5 (yd)", "flight.carry, spin trim on", grp(at(5).carry));
  put("fx-carry-p10", "Tour driver, loft held: carry at attack +10 (yd)", "flight.carry, spin trim on", grp(top.carry));
  const di = Object.fromEntries(driverIdeals(model).map((d) => [d.player, d]));
  put("id-atk", "Lab driver ideal attack angle (degrees)", "presets.json driver_ideal.attack_deg", `+${model.data.presets.driver_ideal.attack_deg}`);
  put("id-pga-loft", "PGA driver ideal dynamic loft (degrees)", "model.idealDelivery: mean of the TrackMan carry and total optimizer lofts", di.pga.ideal.dynLoft.toFixed(1));
  for (const pl of ["pga", "lpga", "amateur"]) {
    const k = pl === "amateur" ? "am" : pl;
    put(`av-${k}-carry`, `${di[pl].label} driver, average delivery: carry (yd)`, "flight.carry at model.preset", grp(di[pl].avg.carry));
    put(`av-${k}-total`, `${di[pl].label} driver, average delivery: total (yd)`, "carry plus model.roll at model.preset", grp(di[pl].avg.total));
    put(`id-${k}-carry`, `${di[pl].label} driver, lab ideal: carry (yd)`, "flight.carry at model.idealDelivery", grp(di[pl].ideal.carry));
    put(`id-${k}-total`, `${di[pl].label} driver, lab ideal: total (yd)`, "carry plus model.roll at model.idealDelivery", grp(di[pl].ideal.total));
  }

  const pgaKeep = model.shot({ ...di.pga.ideal, spinTrim: di.pga.avg.spinTrim });
  put("id-pga-carry-tt", "PGA driver ideal carry if the Tour spin trim is kept (yd)", "flight.carry at model.idealDelivery with the preset's spin trim", grp(pgaKeep.flight.carry));
  put("id-pga-gain-tt", "That carry over the average delivery's (yd)", "carry with the Tour trim minus av-pga-carry (unrounded)", grp(pgaKeep.flight.carry - di.pga.avg.carry));
  const rv = idealTotalReversal(model);
  put("slow-pga-lo", "Lowest club speed at which the PGA driver ideal gives less total than the average delivery (mph)", "5 mph scan of the lab's club speed range, ideal at that speed against the preset at that speed", String(rv.pga.lo));
  put("slow-pga-hi", "Highest such club speed, PGA (mph)", "same scan", String(rv.pga.hi));
  put("slow-lpga-lo", "Lowest club speed at which the LPGA driver ideal gives less total than the average delivery (mph)", "same scan", String(rv.lpga.lo));
  put("slow-lpga-hi", "Highest such club speed, LPGA (mph)", "same scan", String(rv.lpga.hi));

  // Chapter 4
  const [pg, lp, am] = driverWindows(model);
  put("pga-tm-launch", "TrackMan 2010 carry chart launch, PGA driver (degrees)", "trackmanCarry2010(115, -0.9), interpolated between published cells", pg.tm.launch_deg.toFixed(1));
  put("pga-ping-launch", "PING 2019 launch, PGA driver at 171 mph ball speed (degrees)", "ping2019(171, -0.9), interpolated", pg.ping.launch_deg.toFixed(1));
  put("lpga-tm-launch", "TrackMan 2010 carry chart launch, LPGA driver (degrees)", "trackmanCarry2010(96, 2.8), interpolated", lp.tm.launch_deg.toFixed(1));
  put("lpga-ping-launch", "PING 2019 launch, LPGA driver at 143 mph ball speed (degrees)", "ping2019(143, 2.8), interpolated", lp.ping.launch_deg.toFixed(1));
  put("lpga-total-launch", "TrackMan 2010 total-distance chart launch, LPGA driver (degrees)", "bilinear lookup in the published TOTAL chart (96 mph, +2.8)", lp.total.launch_deg.toFixed(1));
  put("lpga-gap-lo", "LPGA average launch under the nearer of the carry chart and PING (degrees)", "min(tm, ping) - 12.6", (Math.min(lp.tm.launch_deg, lp.ping.launch_deg) - lp.avg.launch).toFixed(1));
  put("lpga-gap-hi", "LPGA average launch under the farther of the carry chart and PING (degrees)", "max(tm, ping) - 12.6", (Math.max(lp.tm.launch_deg, lp.ping.launch_deg) - lp.avg.launch).toFixed(1));
  put("pga-total-launch", "TrackMan 2010 total-distance chart launch, PGA driver (degrees)", "bilinear lookup in the published TOTAL chart (115 mph, -0.9)", pg.total.launch_deg.toFixed(1));
  put("lpga-total-gap", "LPGA average launch over the total-distance chart's (degrees)", "12.6 - lpga-total-launch (unrounded)", (lp.avg.launch - lp.total.launch_deg).toFixed(1));
  const wid = ["pga", "lpga", "amateur"].map((pl) => { const b = model.idealBands("driver", pl).launch_deg; return b.hi - b.lo; });
  put("band-w-lo", "Narrowest lab driver launch band across the three players, at each player's ideal (degrees wide)", "idealBands hi - lo, launch_deg", Math.min(...wid).toFixed(1));
  put("band-w-hi", "Widest lab driver launch band across the three players (degrees wide)", "idealBands hi - lo, launch_deg", Math.max(...wid).toFixed(1));
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
  put("cx-spin", "Spin of the amateur example shot at the lab's spin trim of 1.0 (rpm)", "launch.spinRpm of the example; the published amateur average is 3,275", grp(ce.a.launch.spinRpm));

  // Method and limits
  const pgaDrv = shotAt(model, "driver", "pga");
  put("pga-drv-carry", "PGA driver preset carry (yd)", "flight.carry at the preset; published 282", pgaDrv.flight.carry.toFixed(0));
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
