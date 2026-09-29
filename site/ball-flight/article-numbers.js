/*
 * Every model number the article prose states, computed from the live model.
 * article.js writes each value into its <span data-num="key"> so the text can
 * never drift from the figures or the lab. The HTML carries the value at the
 * time of writing as fallback text, and tests/article-numbers.mjs fails when
 * a fallback no longer matches this file's output.
 *
 * Each entry: key, what it is, how it is computed, and a function that
 * returns the formatted string. docs/sources/004_Caption.md lists them all.
 */
import {
  faceShare, startDirection, shotAt, exampleCheck, attackSweep, couplingShot,
  driverWindows, nineWindows, coachingExample, presetTable,
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
  put("share-drv", "Face share of start direction, Tour driver", "launch direction at face +1, path 0, over 1 degree", shDrv.toFixed(0));
  put("share-6i", "Face share of start direction, Tour 6-iron", "same, 6-iron", sh6.toFixed(0));
  put("share-gap-drv", "Points under the circulating 85 percent driver share", "85 minus share-drv", (85 - shDrv).toFixed(0));
  put("share-gap-6i", "Points under the circulating 75 percent iron share", "75 minus share-6i", (75 - sh6).toFixed(0));
  put("sd-drv-face4", "Start direction, Tour driver, face +4 at path 0 (degrees)", "launch_dir", abs1(drv[1].deg));
  put("sd-drv-path4", "Start direction, Tour driver, path +4 at face 0 (degrees)", "launch_dir", abs1(drv[3].deg));

  // Chapter 2
  const c2 = (club) => shotAt(model, club, "pga", { face: 2, path: 0 });
  const cd = c2("driver").flight.curve, c6 = c2("6i").flight.curve, cp = c2("pw").flight.curve;
  put("curve2-drv", "Curve, Tour driver, face-to-path +2 (yd)", "flight.curve", abs1(cd));
  put("curve2-6i", "Curve, Tour 6-iron, face-to-path +2 (yd)", "flight.curve", abs1(c6));
  put("curve2-pw", "Curve, Tour PW, face-to-path +2 (yd)", "flight.curve", abs1(cp));
  put("ratio-drv-pw", "Driver curve over PW curve at the same face-to-path", "curve2-drv / curve2-pw", (cd / cp).toFixed(1));
  put("ratio-drv-6i", "Driver curve over 6-iron curve at the same face-to-path", "curve2-drv / curve2-6i", (cd / c6).toFixed(1));
  put("sl-drv", "Spin loft, Tour driver preset (degrees)", "launch.spinLoftDeg", shotAt(model, "driver", "pga").launch.spinLoftDeg.toFixed(1));
  put("sl-pw", "Spin loft, Tour PW preset (degrees)", "launch.spinLoftDeg", shotAt(model, "pw", "pga").launch.spinLoftDeg.toFixed(0));
  const ex = exampleCheck(model);
  put("ex-miss", "Largest gap between a preset line and a TrackMan example (yd)", "max |model - published| over the eight examples", Math.max(...ex.map((e) => Math.abs(e.miss))).toFixed(1));

  // Chapter 3
  const sw = attackSweep(model);
  const lo = sw.rows[0], hi = sw.rows[sw.rows.length - 1];
  put("atk-loft", "Tour driver dynamic loft held fixed (degrees)", "preset dynLoft", sw.dynLoft.toFixed(1));
  put("atk-launch-dn", "Launch at attack angle -6 (degrees)", "launch.launchDeg", lo.launch.toFixed(1));
  put("atk-launch-up", "Launch at attack angle +6 (degrees)", "launch.launchDeg", hi.launch.toFixed(1));
  put("atk-spin-dn", "Spin at attack angle -6 (rpm)", "launch.spinRpm", grp(lo.spin));
  put("atk-spin-up", "Spin at attack angle +6 (rpm)", "launch.spinRpm", grp(hi.spin));
  put("atk-sl-dn", "Spin loft at attack angle -6 (degrees)", "launch.spinLoftDeg", lo.spinLoft.toFixed(1));
  put("atk-sl-up", "Spin loft at attack angle +6 (degrees)", "launch.spinLoftDeg", hi.spinLoft.toFixed(1));
  put("sl-floor", "Lowest spin loft in the launch fit (degrees)", "model.json launch_model.k_sl_lo", sw.floor.toFixed(1));
  const cp2 = couplingShot(model);
  put("plane", "Swing plane, Combine average driver (degrees)", "model.json swing_plane_default_deg", cp2.plane.toFixed(0));
  put("per-deg", "Path added per degree of down attack (degrees)", "tan(90 - plane)", cp2.perDegree.toFixed(2));
  put("couple-path", "Path after steepening by 4 degrees, swing direction held (degrees right)", "swingPath", abs1(cp2.path));
  put("couple-curve", "Curve of that shot with the face square (yd left)", "flight.curve", Math.abs(cp2.shot.flight.curve).toFixed(0));
  put("couple-start", "Start direction of that shot (degrees)", "launch.launchDirDeg", Math.abs(cp2.shot.launch.launchDirDeg).toFixed(1));
  put("couple-launch", "Launch of that shot (degrees)", "launch.launchDeg", cp2.shot.launch.launchDeg.toFixed(1));
  put("couple-spin", "Spin of that shot (rpm)", "launch.spinRpm", grp(cp2.shot.launch.spinRpm));

  // Chapter 4
  const dw = driverWindows(model);
  const [pg, lp, am] = dw;
  put("lpga-tm-launch", "TrackMan 2010 optimum launch at the LPGA driver speed and attack angle (degrees)", "trackmanCarry2010(96, 2.8)", lp.tm.launch_deg.toFixed(1));
  put("lpga-ping-launch", "PING 2019 optimum launch at the LPGA driver ball speed and attack angle (degrees)", "ping2019(ball speed, 2.8)", lp.ping.launch_deg.toFixed(1));
  put("lpga-gap-lo", "LPGA average launch under the nearer optimizer (degrees)", "min(tm, ping) - 12.6", (Math.min(lp.tm.launch_deg, lp.ping.launch_deg) - lp.avg.launch).toFixed(1));
  put("lpga-gap-hi", "LPGA average launch under the farther optimizer (degrees)", "max(tm, ping) - 12.6", (Math.max(lp.tm.launch_deg, lp.ping.launch_deg) - lp.avg.launch).toFixed(1));
  put("lpga-tm-spin", "TrackMan 2010 optimum spin, LPGA driver (rpm)", "trackmanCarry2010", grp(lp.tm.spin_rpm));
  put("lpga-ping-spin", "PING 2019 optimum spin, LPGA driver (rpm)", "ping2019", grp(lp.ping.spin_rpm));
  put("pga-tm-launch", "TrackMan 2010 optimum launch, PGA driver (degrees)", "trackmanCarry2010(115, -0.9)", pg.tm.launch_deg.toFixed(1));
  put("pga-ping-launch", "PING 2019 optimum launch, PGA driver (degrees)", "ping2019", pg.ping.launch_deg.toFixed(1));
  put("am-tm-launch", "TrackMan 2010 optimum launch, amateur driver (degrees)", "trackmanCarry2010(94, -1.8)", am.tm.launch_deg.toFixed(1));
  put("am-ping-launch", "PING 2019 optimum launch, amateur driver (degrees)", "ping2019", am.ping.launch_deg.toFixed(1));
  put("am-ping-spin", "PING 2019 optimum spin, amateur driver (rpm)", "ping2019", grp(am.ping.spin_rpm));
  put("am-tm-spin", "TrackMan 2010 optimum spin, amateur driver (rpm)", "trackmanCarry2010", grp(am.tm.spin_rpm));
  put("am-spin-gap", "Amateur driver average spin over the PING 2019 optimum (rpm)", "3,275 minus ping2019 spin", grp(am.avg.spin - am.ping.spin_rpm));
  const pt = presetTable(model);
  const amDrv = pt.rows.find((r) => r.club === "driver" && r.player === "amateur").cells;
  put("am-carry", "Amateur driver carry (yd)", "flight.carry at the amateur preset", Math.round(amDrv.find((c) => c.id === "carry_yd").value).toFixed(0));

  // Chapter 5
  const nw = Object.fromEntries(nineWindows(model).map((n) => [n.key, n]));
  const dl = (k) => nw[k].delivery, fl = (k) => nw[k].shot.flight;
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
  put("w-draw-path", "Mid draw: club path (degrees right)", "windows.json recipe", abs1(dl("mid_draw").path));
  put("w-draw-face", "Mid draw: face angle (degrees right)", "windows.json recipe", abs1(dl("mid_draw").face));
  put("w-draw-curve", "Mid draw: curve (yd left)", "flight.curve", Math.abs(fl("mid_draw").curve).toFixed(0));

  const tg = model.windows.targets;
  put("t-low", "Low window peak height as percent of the standard shot", "windows.json targets.heights.low x 100", (tg.heights.low * 100).toFixed(0));
  put("t-high", "High window peak height as percent of the standard shot", "windows.json targets.heights.high x 100", (tg.heights.high * 100).toFixed(0));
  put("t-curve", "Draw and fade bend as percent of carry", "windows.json targets.curve_frac.fade x 100", (tg.curve_frac.fade * 100).toFixed(0));
  put("w-draw-f2p", "Mid draw: face-to-path (degrees)", "recipe face minus path", signed1(dl("mid_draw").face - dl("mid_draw").path));

  // Chapter 6
  const ce = coachingExample(model);
  put("cx-name", "Shot name, amateur driver, path -4, face 0", "classification.name, lower case", ce.a.classification.name.toLowerCase());
  put("cx-curve", "Curve of that shot (yd right)", "flight.curve", Math.abs(ce.a.flight.curve).toFixed(0));
  put("cx-finish", "Where it finishes (yd right)", "flight.side", Math.abs(ce.a.flight.side).toFixed(0));
  put("cx-curve2", "Curve with the path moved to -2 (yd right)", "flight.curve", Math.abs(ce.b.flight.curve).toFixed(0));
  return out;
}
export { signed1 };
