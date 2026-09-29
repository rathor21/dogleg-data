# 004 Caption -- number-by-number ledger (issue #30, task 004.11)

Every number in `site/ball-flight/index.html` (the article at `/ball-flight/`), with its source. First written 2026-09-29 at commit 5e0d46b. Refreshed 2026-09-29 against commit 8a0b302, which includes 1da750e (driver launch and spin calibrated to the TrackMan 2010 chart, ADR 0004 decision 3c, and c linear in spin loft, decision 4). Refreshed again 2026-09-29 against commit 2c9244e, which holds the flight and roll recalibration to the 2010 chart (ADR 0004 addendum 1), the hit-up driver ideal (addendum 2) and the three-source launch and spin bands. That refresh moved 26 fallbacks, removed `pga-drv-gap` and `pga-drv-gap-pct` (the PGA driver carry miss is gone), and added the driver keys in Chapter 3 and Chapter 4.

Three kinds of number appear in the article:

1. **Modeled, computed live by flight.js.** Each sits in `<span data-num="key">fallback</span>`. `site/ball-flight/article.js` overwrites the fallback with the value from `site/ball-flight/article-numbers.js` when the page loads, so the prose matches the figures and the lab. The fallback is the value at the time of writing (the "Value now" column below). `node site/ball-flight/tests/article-numbers.mjs` compares every fallback with a fresh computation and exits non-zero on drift. Rerun it after any refit or `export.py` run and paste the new values into the HTML. A few keys derive from published numbers (`tm-ratio*`, `am-def-gap`, `ch-*`) and cannot drift with a refit.
2. **Published.** Plain text, traced to an anchor in `docs/sources/004_Source_Log.md`.
3. **Fit and gate results.** Plain text in "Method and limits", traced to `docs/adr/0004-ball-flight-model.md`. These change only when the fit changes.

Every model figure and table cell is computed live from the same functions (`model.shot`, `model.preset`, `model.idealBands`, `model.trackmanCarry2010`, `model.ping2019`, `model.windows`). The hand-entered numbers in `article-data.js` are all published: TrackMan's eight curvature examples (Anchor 5b), the TOTAL-optimizer half of the 2010 driver chart (Anchor 4 Source 1, parsed from the log table), TrackMan's current Optimizer default for a 94 mph driver (Anchor 3 Source 2: 13.6 degrees, 2,772 rpm), and TrackMan's published PGA driver dynamic loft and spin loft (Anchor 1 supplement: 12.8 and 14.7).

Model delivery for each shot is the preset for that club and player (`model.preset(club, player)`) with the overrides named below. "Tour" means the PGA Tour preset unless a row says LPGA. Signs: right is positive, degrees and yards as in the lab. Where the article prints a model-derived dynamic loft or spin loft it says so and puts TrackMan's published value beside it.

## Inputs stated in the prose (chosen by the article, not computed)

| Number | Where | Source |
|---|---|---|
| 4 degrees of face or path | Chapter 1, Figure 1 | Chosen test size. Face rows: face +-4, path 0. Path rows: path +-4, face 0 |
| 1 degree | Chapter 1 (the share) | The share is launch direction at face +1, path 0, divided by 1, a slope. At 4 degrees the ratio (3.31 over 4) is 82.8 percent, within 0.1 point |
| 2 degrees of face-to-path | Chapter 2 | Chosen test size, path 0, face +2 |
| 115 mph, attack -6 to +10, 4 degrees steeper | Chapter 3 | Chosen test range at the PGA driver preset (TrackMan 2023 PGA table, Anchor 1) |
| Attack -5 and +5 at 115 mph | Chapter 3, `ch-*` and `md-*` | The 2010 chart's own attack range at the PGA driver's club speed. 115 mph is a chart row |
| 92 mph, 7-iron | Chapter 5 | PGA Tour 7-iron preset (`windows.json` `club`, Anchor 1) |
| path -4 and -2, face 0, amateur driver | Chapter 6 | Chosen example. The deep link is `/ball-flight/tool.html?c=driver&p=amateur&s=94&a=-1.8&l=15.1&pa=-4&f=0`, keys from `state.js` (`c`, `p`, `s`, `a`, `l`, `pa`, `f`). The lab opens the driver on the ideal delivery, so the link names the average delivery's speed, attack and loft (Combine average golfer, Anchor 3 Source 1: 94 mph, -1.8, 15.1). The URL carries no spin trim, so the lab uses the ideal's 1.0, and `coachingExample` in `article-data.js` uses the same 1.0. With the amateur preset's own trim (0.946) the same example reads 23 and 12 yd of curve and 20 yd of finish |

## Modeled numbers, computed live

### Chapter 1

| Key (`data-num`) | Number in prose | Value now | Computed as |
|---|---|---|---|
| `share-drv` | Face share of start direction, Tour driver (percent) | 83 | launch direction at face +1, path 0, over 1 degree |
| `share-6i` | Face share of start direction, Tour 6-iron (percent) | 73 | same, 6-iron |
| `gap-drv-85` | Points under the circulating 85 percent driver share | 2 | 85 minus share-drv (unrounded) |
| `gap-drv-87` | Points under the circulating 87 percent driver share | 4 | 87 minus share-drv (unrounded) |
| `gap-6i-75` | Points under the circulating 75 percent iron share | 2 | 75 minus share-6i (unrounded) |
| `gap-6i-81` | Points under the circulating 81 percent iron share | 8 | 81 minus share-6i (unrounded) |
| `sd-drv-face4` | Start direction, Tour driver, face +4 at path 0 (degrees) | 3.3 | launch.launchDirDeg |
| `sd-drv-path4` | Start direction, Tour driver, path +4 at face 0 (degrees) | 0.7 | launch.launchDirDeg |

### Chapter 2

| Key (`data-num`) | Number in prose | Value now | Computed as |
|---|---|---|---|
| `curve2-drv` | Curve, Tour driver, face-to-path +2 (yd) | 20.1 | flight.curve |
| `curve2-6i` | Curve, Tour 6-iron, face-to-path +2 (yd) | 9.5 | flight.curve |
| `curve2-pw` | Curve, Tour PW, face-to-path +2 (yd) | 2.8 | flight.curve |
| `ratio-drv-pw` | Model: driver curve over PW curve at the same face-to-path (extrapolated) | 7.3 | curve2-drv / curve2-pw |
| `ratio-drv-6i` | Model: driver curve over 6-iron curve at the same face-to-path | 2.1 | curve2-drv / curve2-6i |
| `tm-ratio` | TrackMan published: driver curve per degree over 6-iron curve per degree, both tours | 2.3 | published; mean of the two examples per club, per tour (PGA and LPGA agree to 1 decimal) |
| `tm-ratio-pga` | TrackMan published ratio, PGA examples | 2.3 | published; 9.15 / 4.0 yd per degree |
| `tm-ratio-lpga` | TrackMan published ratio, LPGA examples | 2.3 | published; 6.7 / 2.9 yd per degree |
| `sl-drv` | Spin loft, Tour driver preset (degrees, model-derived) | 13.6 | launch.spinLoftDeg |
| `sl-pw` | Spin loft, Tour PW preset (degrees, model-derived) | 39 | launch.spinLoftDeg |
| `ex-miss-yd` | Largest gap between a preset line and a TrackMan example (yd) | 4.7 | max |model - published| over the eight examples |
| `ex-miss-yd-pct` | That gap as percent of the example's published curve | 15 | |miss| / |published| |
| `ex-pct-max` | Largest percent gap between a preset line and an example | 19 | max |miss| / |published| |
| `ex-pct-yd` | That gap in yards | 1.5 | |miss| of that example |

### Chapter 3

| Key (`data-num`) | Number in prose | Value now | Computed as |
|---|---|---|---|
| `atk-loft` | Tour driver dynamic loft held fixed (degrees, model-derived) | 12.7 | preset dynLoft |
| `atk-launch-dn` | Launch at attack angle -6 (degrees) | 9.6 | launch.launchDeg |
| `atk-launch-up` | Launch at attack angle +6 (degrees) | 11.5 | launch.launchDeg |
| `atk-spin-dn` | Spin at attack angle -6, with the preset spin trim (rpm) | 3,448 | launch.spinRpm |
| `atk-spin-up` | Spin at attack angle +6, with the preset spin trim (rpm) | 1,224 | launch.spinRpm |
| `atk-spin-up-nt` | Spin at attack angle +6, no trim (rpm) | 1,653 | launch.spinRpm with spinTrim 1 |
| `atk-sl-dn` | Spin loft at attack angle -6 (degrees) | 18.7 | launch.spinLoftDeg |
| `atk-sl-up` | Spin loft at attack angle +6 (degrees) | 6.7 | launch.spinLoftDeg |
| `atk-last-in` | Highest whole attack angle still inside the chart's spin loft range | +6 | last row with spin loft >= k_sl_lo_driver |
| `atk10-sl` | Spin loft at attack angle +10 (degrees) | 2.7 | launch.spinLoftDeg |
| `atk10-spin` | Spin at attack angle +10, with the trim (rpm) | 474 | launch.spinRpm |
| `sl-floor` | Lowest spin loft in the driver's calibration (degrees) | 6.3 | model.json launch_model.k_sl_lo_driver |
| `sl-ceil` | Highest spin loft in the driver's calibration (degrees) | 23.2 | model.json launch_model.k_sl_hi_driver |
| `trim` | PGA driver spin trim | 0.74 | presets.json spin_trim |
| `trim-pct` | Percent the Tour average spins under the model for the same delivery | 26 | (1 - trim) x 100 |
| `plane` | Swing plane, Combine average driver (degrees) | 49 | model.json swing_plane_default_deg |
| `per-deg` | Path added per degree of down attack (degrees) | 0.87 | tan(90 - plane) |
| `couple-path` | Path after steepening by 4 degrees, swing direction held (degrees right) | 3.5 | swingPath |
| `couple-curve` | Curve of that shot with the face square (yd left) | 29 | flight.curve |
| `couple-start` | Start direction of that shot (degrees) | 0.6 | launch.launchDirDeg |
| `couple-launch` | Launch of that shot (degrees) | 9.8 | launch.launchDeg |
| `couple-spin` | Spin of that shot (rpm) | 3,316 | launch.spinRpm |

Chapter 3, the driver and hitting up. The `ch-*` keys are published TrackMan chart values read from `data/ideals.json` (they cannot drift with a refit). The `md-*`, `fx-*`, `av-*` and `id-*` keys are model output.

| Key (`data-num`) | Number in prose | Value now | Computed as |
|---|---|---|---|
| `ch-carry-dn` | TrackMan 2010 carry chart carry at 115 mph, attack -5 (yd) | 266 | published; `driver.trackman_carry_2010.carry_yd`, 115 mph row (Anchor 4 Source 1) |
| `ch-carry-up` | Same, attack +5 (yd) | 295 | published; same |
| `ch-carry-gain` | Carry gained from attack -5 to +5 on that chart (yd) | 29 | published; ch-carry-up minus ch-carry-dn |
| `ch-total-gain` | Total distance gained on the carry chart's rows (yd) | 31 | published; `total_yd` of the carry rows, 290 to 321 |
| `ch-total-gain-tt` | Total distance gained on the total-distance chart's rows (yd) | 35 | published; `driver.trackman_total_2010.total_yd`, 307 to 342 |
| `md-carry-gain` | Model carry gained from attack -5 to +5 when flown from the carry chart's own ball speed, launch and spin, axis 0 (yd) | 22 | `model.simulate` at each row; ADR 0004 addendum 1 (21.8) |
| `md-total-gain` | Model total gained the same way (yd) | 25 | carry plus `model.roll`; ADR 0004 addendum 1 (25.3) |
| `fx-peak-carry` | Tour driver with loft held at the preset: highest carry from attack -6 to +10, spin trim on (yd) | 285 | `flight.carry` |
| `fx-peak-atk` | Attack angle of that highest carry (degrees) | +1 | argmax over the sweep (285.0 at +1, 284.7 at +2) |
| `fx-carry-p5` | Same line, carry at attack +5 (yd) | 281 | `flight.carry` |
| `fx-carry-p10` | Same line, carry at attack +10 (yd) | 266 | `flight.carry` |
| `id-atk` | Lab driver ideal attack angle (degrees) | +5 | `presets.json` `driver_ideal.attack_deg` |
| `id-pga-loft` | PGA driver ideal dynamic loft (degrees) | 13.1 | `model.idealDelivery`: mean of the TrackMan 2010 carry and total optimizer lofts at 115 mph, +5 (14.40 and 11.70, ADR 0004 addendum 2: 13.05) |
| `av-pga-carry` | PGA driver, average (preset) delivery, carry (yd) | 282 | `flight.carry` at `model.preset` |
| `av-pga-total` | Same, total (yd) | 313 | carry plus `model.roll` |
| `id-pga-carry` | PGA driver at the lab ideal, carry (yd) | 287 | `flight.carry` at `model.idealDelivery` |
| `id-pga-total` | Same, total (yd) | 328 | carry plus `model.roll` |
| `av-lpga-carry` | LPGA driver, average delivery, carry (yd) | 227 | as above, 96 mph |
| `av-lpga-total` | Same, total (yd) | 263 | as above |
| `id-lpga-carry` | LPGA driver at the lab ideal, carry (yd) | 230 | as above |
| `id-lpga-total` | Same, total (yd) | 267 | as above |
| `av-am-carry` | Average amateur driver, average delivery, carry (yd) | 213 | as above, 94 mph |
| `av-am-total` | Same, total (yd) | 238 | as above |
| `id-am-carry` | Average amateur driver at the lab ideal, carry (yd) | 224 | as above |
| `id-am-total` | Same, total (yd) | 260 | as above |
| `id-pga-carry-tt` | PGA driver ideal carry if the Tour spin trim (0.741) is kept (yd) | 283 | `flight.carry` at `model.idealDelivery` with the preset's `spinTrim`. Total in that case reads 347 yd, which the article does not print |
| `id-pga-gain-tt` | That carry over the average delivery's (yd) | 1 | 283.3 minus 282.1 |

The ideal-against-average numbers match ADR 0004 addendum 2 (PGA 287.3 and 327.6 against 282.1 and 312.9, LPGA 229.9 and 266.6 against 227.0 and 263.2, amateur 223.8 and 260.2 against 212.7 and 238.3). "The LPGA gains least because its average already hits up" is the LPGA preset's published attack, +2.8 (Anchor 2), and the gains above (+2.9 carry, +3.4 total against +5.2 and +14.8, and +11.1 and +21.9). "That is the tee-it-higher, ball-forward move" is the brief's own description of raising loft with attack, not a model output.

### Chapter 4

| Key (`data-num`) | Number in prose | Value now | Computed as |
|---|---|---|---|
| `pga-tm-launch` | TrackMan 2010 carry chart launch, PGA driver (degrees) | 9.3 | trackmanCarry2010(115, -0.9), interpolated between published cells |
| `pga-ping-launch` | PING 2019 launch, PGA driver at 171 mph ball speed (degrees) | 10.3 | ping2019(171, -0.9), interpolated |
| `lpga-tm-launch` | TrackMan 2010 carry chart launch, LPGA driver (degrees) | 14.2 | trackmanCarry2010(96, 2.8), interpolated |
| `lpga-ping-launch` | PING 2019 launch, LPGA driver at 143 mph ball speed (degrees) | 14.8 | ping2019(143, 2.8), interpolated |
| `lpga-total-launch` | TrackMan 2010 total-distance chart launch, LPGA driver (degrees) | 11.8 | bilinear lookup in the published TOTAL chart (96 mph, +2.8) |
| `lpga-gap-lo` | LPGA average launch under the nearer of the carry chart and PING (degrees) | 1.6 | min(tm, ping) - 12.6 |
| `lpga-gap-hi` | LPGA average launch under the farther of the carry chart and PING (degrees) | 2.2 | max(tm, ping) - 12.6 |
| `pga-total-launch` | TrackMan 2010 total-distance chart launch, PGA driver (degrees) | 7.5 | bilinear lookup in the published TOTAL chart (115 mph, -0.9) |
| `lpga-total-gap` | LPGA average launch over the total-distance chart's (degrees) | 0.8 | 12.6 minus lpga-total-launch (unrounded). The LPGA average sits 1.6 to 2.2 under the carry chart and PING and 0.8 over the total chart, inside the three-source band |
| `band-w-lo` | Narrowest lab driver launch band across the three players, at each player's ideal (degrees wide) | 5.3 | `model.idealBands` hi minus lo, `launch_deg` (ADR 0004 addendum 2: 5.8, 5.4, 5.3) |
| `band-w-hi` | Widest of the three (degrees wide) | 5.8 | same |
| `am-tm-spin` | TrackMan 2010 carry chart spin, amateur driver (rpm) | 3,300 | trackmanCarry2010(94, -1.8), interpolated |
| `am-ping-spin` | PING 2019 spin, amateur driver at 133 mph ball speed (rpm) | 2,749 | ping2019(133, -1.8), interpolated |
| `am-ping-gap` | Amateur average spin over PING's (rpm) | 527 | 3,275 minus ping2019 spin |
| `am-def-gap` | Amateur average spin over TrackMan's current Optimizer default (rpm, to the nearest 50) | 500 | published: 3,275 minus 2,772 |

### Chapter 5

| Key (`data-num`) | Number in prose | Value now | Computed as |
|---|---|---|---|
| `w-apl` | Attack angle per degree of loft in the height lever | 0.4 | windows.json targets.attack_per_loft |
| `t-low` | Low window peak height as percent of the standard shot | 70 | windows.json targets.heights.low x 100 |
| `t-high` | High window peak height as percent of the standard shot | 125 | windows.json targets.heights.high x 100 |
| `t-curve` | Draw and fade bend as percent of carry | 5 | windows.json targets.curve_frac.fade x 100 |
| `w-low-loft` | Straight low: dynamic loft (degrees) | 15.3 | windows.json recipe |
| `w-low-aoa` | Straight low: attack angle (degrees down) | 7.1 | windows.json recipe |
| `w-low-carry` | Straight low: carry (yd) | 186 | flight.carry |
| `w-low-h` | Straight low: peak height (yd) | 26 | flight.maxHeight |
| `w-mid-loft` | Straight mid: dynamic loft (degrees) | 23.4 | windows.json recipe |
| `w-mid-aoa` | Straight mid: attack angle (degrees down) | 3.9 | windows.json recipe |
| `w-mid-carry` | Straight mid: carry (yd) | 172 | flight.carry |
| `w-mid-h` | Straight mid: peak height (yd) | 37 | flight.maxHeight |
| `w-high-loft` | Straight high: dynamic loft (degrees) | 34.4 | windows.json recipe |
| `w-high-aoa` | Straight high: attack angle (degrees up) | 0.5 | windows.json recipe |
| `w-high-carry` | Straight high: carry (yd) | 149 | flight.carry |
| `w-high-h` | Straight high: peak height (yd) | 46 | flight.maxHeight |
| `w-face-lo` | Draw windows: smallest face angle (degrees right) | 1.8 | windows.json recipes |
| `w-face-hi` | Draw windows: largest face angle (degrees right) | 2.4 | windows.json recipes |
| `w-path-lo` | Draw windows: smallest path (degrees right) | 4.3 | windows.json recipes |
| `w-path-hi` | Draw windows: largest path (degrees right) | 5.2 | windows.json recipes |
| `w-curve-lo` | Draw windows: smallest curve (yd) | 7.4 | flight.curve |
| `w-curve-hi` | Draw windows: largest curve (yd) | 9.3 | flight.curve |
| `w-f2p-low` | Low draw: face-to-path (degrees) | −2.0 | recipe face minus path |
| `w-f2p-mid` | Mid draw: face-to-path (degrees) | −2.4 | recipe face minus path |
| `w-f2p-high` | High draw: face-to-path (degrees) | −3.4 | recipe face minus path |

### Chapter 6

| Key (`data-num`) | Number in prose | Value now | Computed as |
|---|---|---|---|
| `cx-name` | Shot name, amateur driver, path -4, face 0 | slice | classification.name, lower case |
| `cx-curve` | Curve of that shot (yd right) | 24 | flight.curve |
| `cx-finish` | Where it finishes (yd right) | 21 | flight.side |
| `cx-curve2` | Curve with the path moved to -2 (yd right) | 12 | flight.curve |

### Method and limits

| Key (`data-num`) | Number in prose | Value now | Computed as |
|---|---|---|---|
| `pga-drv-carry` | PGA driver preset carry (yd) | 282 | flight.carry at the preset; published 282 |
| `pga-drv-ball` | PGA driver preset ball speed (mph) | 170.2 | launch.ballSpeedMph |
| `pga-drv-spin-nt` | PGA driver spin with no trim (rpm) | 3,436 | launch.spinRpm with spinTrim 1 |
| `trim-min` | Smallest preset spin trim | 0.74 | min over all presets |
| `trim-max` | Largest preset spin trim | 1.14 | max over all presets |

### Figure and table values

All computed live from the model or the published rows, none typed in except the published sets named above:

| Item | Computed as |
|---|---|
| Figure 1 bars and data table | `launch.launchDirDeg` of `model.shot` at the four deliveries per club (driver, 6-iron). Yards off line at 200 yd is `200 x tan(launch direction)`, TrackMan's launch direction geometry (Anchor 5a Source 2) |
| Figure 2 lines and data table | `flight.curve` of `model.shot` at face -6 to +6 in 0.5 steps, path 0, for PGA driver, 6-iron and PW and LPGA driver and 6-iron |
| Figure 2 dots | TrackMan's eight examples, published (Anchor 5b Source 1): PGA driver -2 = 19 yd left, +5 = 44 right; PGA 6-iron +2 = 8 right, -5 = 20 left; LPGA driver +2 = 14 right, -5 = 32 left; LPGA 6-iron -2 = 6 left, +5 = 14 right. The page quotes 2019 carries (275, 183, 218, 152) and the lines use the 2023 presets. Live gaps: `ex-miss-yd` and `ex-pct-max` above |
| Figure 3 | Model lines: `model.shot` for the PGA driver preset with `attack` -6 to +10, dynamic loft fixed, with the preset spin trim (0.741) and with `spinTrim: 1` (grey line). Loft-follows line (maroon): the same shot with dynamic loft `model.optimalLoft(115, attack).dynLoft` (mean of the TrackMan 2010 carry and total optimizer lofts) and the driver ideal's spin trim 1.0 (`presets.json` `driver_ideal.spin_trim`), dotted where the spin loft leaves 6.3 to 23.2 or the attack leaves the chart's -5 to +5. Carry panel: the same three lines' `flight.carry`, plus the TrackMan carry chart's `carry_yd` at 115 mph (266, 281, 295 at -5, 0, +5, published, drawn as dots at the chart's own carry-optimizer loft), and the Tour average dot at 282 yd, -0.9. Optimizer lines in the launch and spin panels: `model.trackmanCarry2010(115, attack)` (attack -5 to +5, the chart's range) and `model.ping2019(model ball speed, attack)`. Tour average dot: 10.4 degrees and 2,545 rpm at -0.9 (Anchor 1). Dotted segments and the shaded region: spin loft outside `launch_model.k_sl_lo_driver` to `k_sl_hi_driver` (6.3 to 23.2, the chart's range, ADR 0004 decision 3c) |
| Figure 3 prose, "1,681 rpm" | Published: TrackMan Driver Fitting Chart (2010), TOTAL Optimizer row, 115 mph, attack +5, dynamic loft 11.7, spin 1,681 (Anchor 4 Source 1). Spin loft 11.7 - 5 = 6.7. Also in ADR 0004 decision 3c |
| Figure 4 | Rows use the published club speed, ball speed and attack angle: PGA 115 mph, 171 mph, -0.9; LPGA 96, 143, +2.8; amateur 94, 133, -1.8 (Anchors 1, 2, 3). Averages: launch 10.4 / 12.6 / 12.6 deg, spin 2,545 / 2,506 / 3,275 rpm (published). Carry chart: `model.trackmanCarry2010(club speed, attack)`. PING: `model.ping2019(published ball speed, attack)`. Total-distance chart: bilinear lookup in `TRACKMAN_TOTAL_2010` (`article-data.js`). Band: the lowest to the highest of the carry chart, the total-distance chart and PING, widened by the `ideals.json` margins (1 degree, 200 rpm), the lab's rule since ADR 0004 addendum 2. The lab's own band uses the model's ball speed, so it can differ from the drawn band by a few tenths of a degree |
| Table 1 | Published values from `presets.json` `published` (TrackMan 2023 PGA and LPGA tables; Combine average golfer for the amateur driver: 94 mph, 12.6 deg, 3,275 rpm). Amateur 6-iron and PW club speed, launch and spin are TrackMan Optimizer defaults (80 / 16.9 / 5,956 and 72 / 26.7 / 8,408, Anchor 3 Source 2), tagged `default`. Every blank published cell is `model.shot` at the preset and tagged `modeled` |
| Figure 5 | Recipes from `windows.json` `players.pga`, flown again live with `model.shot` (club 7i, the recipe's spin trim). Curves are `flight.x`, `flight.y`, `flight.z` |
| Deep link example numbers | `cx-*` above |

## Published numbers stated in the prose

| Number | Source |
|---|---|
| 85 percent driver and 75 percent iron face share | PGA Academy Australia, "Starting Line - Path or Face?", 2014-07-22, no source named (Anchor 5a Source 3) |
| 87 percent and 81 percent | Golf Simulator Forum post, 2021-10-14, cites "trackman academy" without a link (Anchor 5a Source 4) |
| "TrackMan's own pages print no percentage" | Anchor 5a Source 1 (Face Angle, Club Path, True impact factors pages) |
| Tuxen paper unreadable | Anchor 5a "Not readable" |
| k fitted to launch angle data alone: four published triples plus the 60 chart rows | ADR 0004 decision 3 (Fit of k) and 3c (driver k) |
| 12.8 degrees dynamic loft, 14.7 degrees spin loft, PGA driver | TrackMan What is Dynamic Loft and What is Spin Loft (Anchor 1 supplement) |
| 2019 rows, carries 275, 183, 218, 152 yd; every example within 20 percent or 3 yd | Anchor 5b Source 1 (carries); ADR 0004 decision 4 (fit result; worst 12 percent, 0.39 of tolerance) |
| Published driver-to-6-iron ratio `tm-ratio` | Derived from the eight examples: PGA driver 19 yd at 2 deg and 44 at 5 (9.5 and 8.8 yd per degree, mean 9.15) against the 6-iron 8 at 2 and 20 at 5 (4.0 each); LPGA driver 14 at 2 and 32 at 5 (7.0, 6.4, mean 6.7) against 6 at 2 and 14 at 5 (3.0, 2.8, mean 2.9). Ratios 2.29 and 2.31. Pair by pair the range is 2.1 to 2.5 |
| TrackMan's 2010 chart spans 6.3 to 23.2 degrees of spin loft | ADR 0004 decision 3c (`launch_model.k_sl_lo_driver`, `k_sl_hi_driver`) |
| Tour average spins about 26 percent under TrackMan's model for the same delivery (trim 0.741), above-center strikes would explain it and the log cannot confirm it | ADR 0004 decision 3 and 3c; source log Gaps item 9 |
| 2011 forum formula, 0.87 degree per degree | Brian Manzella Golf forum, "Clubhead Direction - AoA and Club Path", 2011-04-12 (Anchor 5c Source 2). The 0.87 is `tan(90 - 49)`, derived in the source log |
| 49-degree swing plane | TrackMan Combine average golfer swing plane 49.0 (Anchor 3 Source 1), also `model.json` `swing_plane_default_deg` |
| TrackMan says path comes from swing direction, plane and attack angle, no equation | Anchor 5c Source 1 |
| PGA driver launch 10.4 degrees | TrackMan 2023 PGA table (Anchor 1) |
| LPGA driver launch 12.6 degrees, attack angle +2.8 | TrackMan 2023 LPGA table (Anchor 2) |
| Amateur driver launch 12.6 degrees, spin 3,275 rpm, ball speed 133 mph, "14.5-handicap" | TrackMan Combine, average golfer 14.5 handicap (Anchor 3 Source 1) |
| Optimizer default for a 94 mph driver: 13.6 degrees, 2,772 rpm | TrackMan Optimizer defaults on the parameter pages (Anchor 3 Source 2) |
| Charts dated 2010 (carry and total-distance, same PDF) and 2019 | Anchor 4 Sources 1 and 2 |
| The chart's carry at 115 mph, 266 at -5 and 295 at +5 (gain 29), total 290 to 321 on the carry rows (31) and 307 to 342 on the total rows (35) | Anchor 4 Source 1, read from `data/ideals.json` (`ch-*` keys) |
| The chart is TrackMan model output, 2010 vintage, radar attack angle convention, no strike offset | ADR 0004 decision 3c calibration data |
| PGA driver published carry 282 yd | TrackMan 2023 PGA table (Anchor 1) |
| Average amateur driver 94 mph, attack -1.8, dynamic loft 15.1 (the deep-link numbers) | TrackMan Combine average golfer (Anchor 3 Source 1) |
| 1 degree and 200 rpm band margin | `ideals.json` `tolerances` `driver_launch_margin_deg`, `driver_spin_margin_rpm` (design choice, modeled; PING states its own tolerance of 1 degree and 300 rpm, Anchor 4) |
| TaylorMade video, 2021, "Tiger Woods' Nine Windows"; description reads "High, low, draw, cut" and calls the drill an example of the control a golfer can have with an iron | Anchor 6 Source 1, read from the video page description. The video itself was not watched. The 3 by 3 grid is the standard reading of the drill (Anchor 6 "The 3 by 3 layout") |
| "I found no launch monitor numbers for any window" | Anchor 6 verdict, as far as the hunt reached |
| TrackMan reports club speed, attack angle and path at the center of the head; camera monitors read attack angle about 2 degrees higher; tables do not adjust for altitude or weather | Anchor 5c Source 3; Anchor 4 Source 2 (PING chart note); Anchor 1 Source 3 footer and the gaps list |
| Tour averages pool competition and range shots | Anchor 1 Source 1 |

## Fit and gate results in "Method and limits" (ADR 0004)

| Statement | Source |
|---|---|
| Point mass, RK4 at 0.01 s, standard sea-level air, quadratic lift and drag, seven coefficients fitted once to 23 Tour rows (PGA 12, LPGA 11) and the 60 chart rows, no per-club terms, published spin decay | ADR 0004 decision 1 and addendum 1, decision 1 (refit on both sets) |
| Driver launch line and spin law refit to the 60 rows of TrackMan's 2010 chart | ADR 0004 decision 3c |
| Original gate: carry 3 percent, height 3 yd, land angle 2 degrees, passed on 6 of 23 rows; teaching tolerance 5 percent, 4 yd, 3 degrees, passed on 15 (12 before the chart refit) | ADR 0004 decision 2; addendum 1 (Tour rows after the refit); `tests/g2_known_misses.json` (17 G2 misses, 8 teaching misses) |
| Chart weight twice the Tour set's, the smallest on the grid 1, 1.5, 2, 3, 4 that puts all 60 chart rows within 3 percent (worst 2.8 percent) | ADR 0004 addendum 1, decision 1 table |
| PGA 7, 8 and 9 iron carry 7.6, 7.7 and 7.5 yd short, PGA PW 11.7 short; PGA 3, 4 and 5 iron land 5.3, 5.7 and 5.2 degrees shallower (article: 7.5 to 7.7 short, 5.2 to 5.7 shallower); PGA 3-wood, 5-wood, hybrid and 6-iron 3.3, 3.6, 3.9 and 3.2 yd too high (article: 3.2 to 3.9) | ADR 0004 addendum 1 (Tour rows after the refit); `tests/g2_known_misses.json` |
| PGA driver preset carry 282 yd against 282 published, ball speed 170.2 mph against 171; the PGA driver passes G2 (283.7 carry against 282 when flown from the published row, land angle 39.5 against 39) | `pga-drv-*` keys above; ADR 0004 addendum 1; TrackMan 2023 PGA table (Anchor 1) |
| All 60 chart rows carry within 3 percent (worst 2.8 percent), in-sample. Seven chart totals miss the 5 percent gate: C80/-5, C80/+0, T80/-5, T80/+0, T80/+5 (five 80 mph rows), C100/+0 (-14.5 yd, the row the source log flags as a suspected printing error) and C120/+5 (-19.2 yd) | ADR 0004 addendum 1 (result against the chart); `tests/g2_known_misses.json` `chart` (empty) and `chart_total` (7) |
| Roll follows landing speed, landing angle and landing spin (k 1.2962, p 4.3428, q 0.5594, cap 80 yd), fitted to the chart's total minus carry on 60 driver rows, 6.2 yd rms on rolls of 16 to 58 yd; irons and wedges extrapolated; rests on TrackMan model output | ADR 0004 addendum 1, decision 2 |
| Driver ideal: attack +5, band +2 to +5, path 0, face 0, spin trim 1.0 (the chart's own strike), loft the mean of the TrackMan carry and total optimizer lofts; beats the average delivery in carry and total for all three players; with the Tour trim kept the PGA ideal carries 283.3 against 282.1 | ADR 0004 addendum 2; `id-pga-carry-tt` above. The trim-kept figure is computed live, not in the ADR |
| Chart covers 75 to 120 mph and attack -5 to +5; loft extends along the edge slope beyond, and is held at the edge beyond 120 mph | ADR 0004 addendum 2 (`optimalLoft`); `sliders.js` notes |
| Launch band 5.3 to 5.8 degrees wide at each player's ideal, from three sources | ADR 0004 addendum 2 (5.8, 5.4, 5.3); `band-w-*` above |
| 17 of 23 rows pass launch within 1 degree, spin within 10 percent, ball speed within 2 percent | ADR 0004 decision 3, G3 result |
| PGA driver spin 3,436 against 2,545 with no trim (+35.0 percent); LPGA 3-wood +30.2 percent | ADR 0004 decision 3 tables; `tests/g3_known_misses.json` |
| Against the 60 chart rows: launch within 0.30 degree, rms 0.22; spin rms 0.76 percent; ball speed rms 0.77 percent; in-sample | ADR 0004 decision 3c result table |
| Spin trims: PGA driver 0.741, LPGA 3-wood 0.768, 5-woods 1.135 and 1.120; range 0.741 to 1.135; presets within 1 percent of published spin | ADR 0004 decision 3a (`trim-min`, `trim-max` above are live) |
| Remaining preset misses: amateur driver ball speed +2.78 percent, amateur 6-iron launch -1.28 degrees, LPGA 8-iron ball speed -2.3 percent | ADR 0004 decision 3a; `tests/g3_known_misses.json` (`presets` and `g3`) |
| Amateur driver measured, 6-iron and PW Optimizer defaults, other clubs interpolated | ADR 0004 decision 6 |
| Flight model over-curves short irons per degree of axis: 6-iron 13.9 yd against 3-wood 12.8 at 10 degrees, TrackMan 11 and 15 | ADR 0004 decision 4 (`test_flight.py` xfail). Values refreshed after the chart refit by running `flight.simulate` on the LPGA 6-iron and 3-wood Tour rows at 10 degrees of axis (13.91, 12.84); the ADR still prints 14.0 and 12.1 |
| c linear in spin loft, 1.11 at 12.4 and 0.98 at 26.9; c absorbs part of the over-curve and of the 1 to 6 percent carry shortfall in the examples (seven of eight run under; the LPGA driver at +2 runs 0.7 percent over); driver examples asymmetric (9.5 yd per degree left, 8.8 right) | ADR 0004 decision 4 |
| Launch fit spans 12.7 to 25.9 degrees of spin loft for every club but the driver | ADR 0004 decision 3 (k line, spin law) |
| Driver range 6.3 to 23.2; at the Tour preset attack angles up to +6; the tool reaches +10 where spin loft is 2.7 and no row supports the result | ADR 0004 decision 3c and Consequences; source log Gaps item 9 |
| Nine-window height lever: `dyn_loft = preset + h`, `attack = preset + 0.4 h`; solver finds path, face and h | `windows.json` `height_lever` and `targets.attack_per_loft`; the 0.4 is a design choice, modeled |
| Total distance modeled: roll rule fitted to the chart, see the roll row above | ADR 0004 addendum 1, decision 2; source log gaps item 8 |
| Start-direction shares unverified | ADR 0004 decision 5; Anchor 5a |
