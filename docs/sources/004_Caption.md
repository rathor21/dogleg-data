# 004 Caption -- number-by-number ledger (issue #30, task 004.11)

Every number in `site/ball-flight/index.html` (the article at `/ball-flight/`), with its source. Written 2026-09-29 against the model in `site/ball-flight/flight.js` and `site/ball-flight/data/*.json` at commit 5e0d46b plus the 004.11 files.

Three kinds of number appear in the article:

1. **Modeled, computed live by flight.js.** Each sits in `<span data-num="key">fallback</span>`. `site/ball-flight/article.js` overwrites the fallback with the value from `site/ball-flight/article-numbers.js` when the page loads, so the prose matches the figures and the lab. The fallback is the value at the time of writing (the "Value now" column below). `node site/ball-flight/tests/article-numbers.mjs` compares every fallback with a fresh computation and exits non-zero on drift. Rerun it after any refit or `export.py` run and paste the new values into the HTML.
2. **Published.** Plain text, traced to an anchor in `docs/sources/004_Source_Log.md`.
3. **Fit and gate results.** Plain text in "Method and limits", traced to `docs/adr/0004-ball-flight-model.md`. These change only when the fit changes.

Every model figure and table cell is computed live from the same functions (`model.shot`, `model.preset`, `model.idealBands`, `model.trackmanCarry2010`, `model.ping2019`, `model.windows`). Nothing in a figure is typed in except TrackMan's eight published curvature examples (Chapter 2, Anchor 5b).

Model delivery for each shot is the preset for that club and player (`model.preset(club, player)`) with the overrides named below. "Tour" means the PGA Tour preset unless a row says LPGA. Signs: right is positive, degrees and yards as in the lab.

## Inputs stated in the prose (chosen by the article, not computed)

| Number | Where | Source |
|---|---|---|
| 4 degrees of face or path | Chapter 1, Figure 1 | Chosen test size. Face rows: face +-4, path 0. Path rows: path +-4, face 0 |
| 1 degree | Chapter 1 (the share) | The share is launch direction at face +1, path 0, divided by 1. Measured at 1 degree so it is a slope, not a 4-degree average (at 4 degrees the driver reads 78.3 percent) |
| 2 degrees of face-to-path | Chapter 2 | Chosen test size, path 0, face +2 |
| -6 to +6 degrees of attack angle, 4 degrees steeper | Chapter 3 | Chosen test range |
| 92 mph, 7-iron | Chapter 5 | PGA Tour 7-iron preset (`windows.json` `club`, TrackMan 2023 PGA table, Anchor 1) |
| path -4 and -2, face 0, amateur driver | Chapter 6 | Chosen example. The deep link is `/ball-flight/tool.html?c=driver&p=amateur&pa=-4&f=0`, keys from `state.js` (`c`, `p`, `pa`, `f`) |

## Modeled numbers, computed live

### Chapter 1

| Key (`data-num`) | Number in prose | Value now | Computed as |
|---|---|---|---|
| `share-drv` | Face share of start direction, Tour driver | 79 | launch direction at face +1, path 0, over 1 degree |
| `share-6i` | Face share of start direction, Tour 6-iron | 73 | same, 6-iron |
| `share-gap-drv` | Points under the circulating 85 percent driver share | 6 | 85 minus share-drv |
| `share-gap-6i` | Points under the circulating 75 percent iron share | 2 | 75 minus share-6i |
| `sd-drv-face4` | Start direction, Tour driver, face +4 at path 0 (degrees) | 3.1 | launch_dir |
| `sd-drv-path4` | Start direction, Tour driver, path +4 at face 0 (degrees) | 0.9 | launch_dir |

### Chapter 2

| Key (`data-num`) | Number in prose | Value now | Computed as |
|---|---|---|---|
| `curve2-drv` | Curve, Tour driver, face-to-path +2 (yd) | 18.0 | flight.curve |
| `curve2-6i` | Curve, Tour 6-iron, face-to-path +2 (yd) | 10.4 | flight.curve |
| `curve2-pw` | Curve, Tour PW, face-to-path +2 (yd) | 3.1 | flight.curve |
| `ratio-drv-pw` | Driver curve over PW curve at the same face-to-path | 5.8 | curve2-drv / curve2-pw |
| `ratio-drv-6i` | Driver curve over 6-iron curve at the same face-to-path | 1.7 | curve2-drv / curve2-6i |
| `sl-drv` | Spin loft, Tour driver preset (degrees) | 14.3 | launch.spinLoftDeg |
| `sl-pw` | Spin loft, Tour PW preset (degrees) | 39 | launch.spinLoftDeg |
| `ex-miss` | Largest gap between a preset line and a TrackMan example (yd) | 5.4 | max |model - published| over the eight examples |

### Chapter 3

| Key (`data-num`) | Number in prose | Value now | Computed as |
|---|---|---|---|
| `atk-loft` | Tour driver dynamic loft held fixed (degrees) | 13.4 | preset dynLoft |
| `atk-launch-dn` | Launch at attack angle -6 (degrees) | 8.8 | launch.launchDeg |
| `atk-launch-up` | Launch at attack angle +6 (degrees) | 11.9 | launch.launchDeg |
| `atk-spin-dn` | Spin at attack angle -6 (rpm) | 3,684 | launch.spinRpm |
| `atk-spin-up` | Spin at attack angle +6 (rpm) | 1,086 | launch.spinRpm |
| `atk-sl-dn` | Spin loft at attack angle -6 (degrees) | 19.4 | launch.spinLoftDeg |
| `atk-sl-up` | Spin loft at attack angle +6 (degrees) | 7.4 | launch.spinLoftDeg |
| `sl-floor` | Lowest spin loft in the launch fit (degrees) | 12.7 | model.json launch_model.k_sl_lo |
| `plane` | Swing plane, Combine average driver (degrees) | 49 | model.json swing_plane_default_deg |
| `per-deg` | Path added per degree of down attack (degrees) | 0.87 | tan(90 - plane) |
| `couple-path` | Path after steepening by 4 degrees, swing direction held (degrees right) | 3.5 | swingPath |
| `couple-curve` | Curve of that shot with the face square (yd left) | 28 | flight.curve |
| `couple-start` | Start direction of that shot (degrees) | 0.8 | launch.launchDirDeg |
| `couple-launch` | Launch of that shot (degrees) | 9.2 | launch.launchDeg |
| `couple-spin` | Spin of that shot (rpm) | 3,508 | launch.spinRpm |

### Chapter 4

| Key (`data-num`) | Number in prose | Value now | Computed as |
|---|---|---|---|
| `lpga-tm-launch` | TrackMan 2010 optimum launch at the LPGA driver speed and attack angle (degrees) | 14.2 | trackmanCarry2010(96, 2.8) |
| `lpga-ping-launch` | PING 2019 optimum launch at the LPGA driver ball speed and attack angle (degrees) | 14.8 | ping2019(ball speed, 2.8) |
| `lpga-gap-lo` | LPGA average launch under the nearer optimizer (degrees) | 1.6 | min(tm, ping) - 12.6 |
| `lpga-gap-hi` | LPGA average launch under the farther optimizer (degrees) | 2.2 | max(tm, ping) - 12.6 |
| `lpga-tm-spin` | TrackMan 2010 optimum spin, LPGA driver (rpm) | 2,817 | trackmanCarry2010 |
| `lpga-ping-spin` | PING 2019 optimum spin, LPGA driver (rpm) | 2,390 | ping2019 |
| `pga-tm-launch` | TrackMan 2010 optimum launch, PGA driver (degrees) | 9.3 | trackmanCarry2010(115, -0.9) |
| `pga-ping-launch` | PING 2019 optimum launch, PGA driver (degrees) | 10.4 | ping2019 |
| `am-tm-launch` | TrackMan 2010 optimum launch, amateur driver (degrees) | 11.9 | trackmanCarry2010(94, -1.8) |
| `am-ping-launch` | PING 2019 optimum launch, amateur driver (degrees) | 12.4 | ping2019 |
| `am-ping-spin` | PING 2019 optimum spin, amateur driver (rpm) | 2,765 | ping2019 |
| `am-tm-spin` | TrackMan 2010 optimum spin, amateur driver (rpm) | 3,300 | trackmanCarry2010 |
| `am-spin-gap` | Amateur driver average spin over the PING 2019 optimum (rpm) | 510 | 3,275 minus ping2019 spin |
| `am-carry` | Amateur driver carry (yd) | 203 | flight.carry at the amateur preset |

### Chapter 5

| Key (`data-num`) | Number in prose | Value now | Computed as |
|---|---|---|---|
| `w-low-loft` | Straight low: dynamic loft (degrees) | 15.3 | windows.json recipe |
| `w-low-aoa` | Straight low: attack angle (degrees down) | 7.1 | windows.json recipe |
| `w-low-carry` | Straight low: carry (yd) | 186 | flight.carry |
| `w-low-h` | Straight low: peak height (yd) | 27 | flight.maxHeight |
| `w-mid-loft` | Straight mid: dynamic loft (degrees) | 23.4 | windows.json recipe |
| `w-mid-aoa` | Straight mid: attack angle (degrees down) | 3.9 | windows.json recipe |
| `w-mid-carry` | Straight mid: carry (yd) | 174 | flight.carry |
| `w-mid-h` | Straight mid: peak height (yd) | 38 | flight.maxHeight |
| `w-high-loft` | Straight high: dynamic loft (degrees) | 34.6 | windows.json recipe |
| `w-high-aoa` | Straight high: attack angle (degrees up) | 0.6 | windows.json recipe |
| `w-high-carry` | Straight high: carry (yd) | 152 | flight.carry |
| `w-high-h` | Straight high: peak height (yd) | 48 | flight.maxHeight |
| `w-draw-path` | Mid draw: club path (degrees right) | 4.4 | windows.json recipe |
| `w-draw-face` | Mid draw: face angle (degrees right) | 2.3 | windows.json recipe |
| `w-draw-curve` | Mid draw: curve (yd left) | 9 | flight.curve |
| `t-low` | Low window peak height as percent of the standard shot | 70 | windows.json targets.heights.low x 100 |
| `t-high` | High window peak height as percent of the standard shot | 125 | windows.json targets.heights.high x 100 |
| `t-curve` | Draw and fade bend as percent of carry | 5 | windows.json targets.curve_frac.fade x 100 |
| `w-draw-f2p` | Mid draw: face-to-path (degrees) | −2.1 | recipe face minus path |

### Chapter 6

| Key (`data-num`) | Number in prose | Value now | Computed as |
|---|---|---|---|
| `cx-name` | Shot name, amateur driver, path -4, face 0 | slice | classification.name, lower case |
| `cx-curve` | Curve of that shot (yd right) | 22 | flight.curve |
| `cx-finish` | Where it finishes (yd right) | 19 | flight.side |
| `cx-curve2` | Curve with the path moved to -2 (yd right) | 11 | flight.curve |

### Figure and table values

All computed live, none typed in:

| Item | Computed as |
|---|---|
| Figure 1 bars and data table | `launch.launchDirDeg` of `model.shot` at the four deliveries per club (driver, 7-iron). Yards off line at 200 yd is `200 x tan(launch direction)`, TrackMan's launch direction geometry (Anchor 5a Source 2) |
| Figure 2 lines and data table | `flight.curve` of `model.shot` at face -6 to +6 in 0.5 steps, path 0, for PGA driver, 6-iron and PW and LPGA driver and 6-iron |
| Figure 2 dots | TrackMan's eight examples, published (Anchor 5b Source 1): PGA driver -2 = 19 yd left, +5 = 44 right; PGA 6-iron +2 = 8 right, -5 = 20 left; LPGA driver +2 = 14 right, -5 = 32 left; LPGA 6-iron -2 = 6 left, +5 = 14 right. The page quotes 2019 carries (275, 183, 218, 152) and the lines use the 2023 presets, so they differ a little by construction. Live gap: `ex-miss` above |
| Figure 3 | Model line: `model.shot` for the PGA driver preset with `attack` -6 to +6, dynamic loft fixed. Optimizer lines: `model.trackmanCarry2010(115, attack)` (attack -5 to +5, the chart's range) and `model.ping2019(model ball speed, attack)`. Tour average dot: 10.4 degrees and 2,545 rpm at -0.9 (Anchor 1). Dotted segment: spin loft below `launch_model.k_sl_lo` |
| Figure 4 | Rows: PGA 115 mph -0.9, LPGA 96 mph +2.8, amateur 94 mph -1.8 (Anchors 1, 2, 3). Averages: launch 10.4 / 12.6 / 12.6 deg, spin 2,545 / 2,506 / 3,275 rpm (published). Optimizer marks and the band: `model.idealBands("driver", player)` detail (TrackMan 2010 CARRY at club speed, PING 2019 at model ball speed, band = both charts widened by 1 degree and 200 rpm, `ideals.json` tolerances) |
| Table 1 | Published values from `presets.json` `published` (TrackMan 2023 PGA and LPGA tables; Combine average golfer for the amateur driver: 94 mph, 12.6 deg, 3,275 rpm). Amateur 6-iron and PW club speed, launch and spin are TrackMan Optimizer defaults (80 / 16.9 / 5,956 and 72 / 26.7 / 8,408, Anchor 3 Source 2), tagged `default`. Every blank published cell (amateur driver height, land angle and carry; every amateur 6-iron and PW height, land angle and carry) is `model.shot` at the preset and tagged `modeled` |
| Figure 5 | Recipes from `windows.json` `players.pga`, flown again live with `model.shot` (club 7i, the recipe's spin trim). Curves are `flight.x`, `flight.y`, `flight.z` |
| Deep link example numbers | `cx-*` above |

## Published numbers stated in the prose

| Number | Source |
|---|---|
| 85 percent driver and 75 percent iron face share | PGA Academy Australia, "Starting Line - Path or Face?", 2014-07-22, no source named (Anchor 5a Source 3) |
| 87 percent and 81 percent | Golf Simulator Forum post, 2021-10-14, cites "trackman academy" without a link (Anchor 5a Source 4) |
| "TrackMan's own pages print no percentage" | Anchor 5a Source 1 (Face Angle, Club Path, True impact factors pages) |
| Tuxen paper unreadable | Anchor 5a "Not readable" |
| Eight examples within `ex-miss` yards, no wedge example | Anchor 5b Source 1 lists eight examples, none for a wedge |
| 2011 forum formula, 0.87 degree per degree | Brian Manzella Golf forum, "Clubhead Direction - AoA and Club Path", 2011-04-12 (Anchor 5c Source 2). The 0.87 is `tan(90 - 49)`, derived in the source log |
| 49-degree swing plane | TrackMan Combine average golfer swing plane 49.0 (Anchor 3 Source 1), also `model.json` `swing_plane_default_deg` |
| TrackMan says path comes from swing direction, plane and attack angle, no equation | Anchor 5c Source 1 |
| PGA driver launch 10.4 degrees | TrackMan 2023 PGA table (Anchor 1) |
| LPGA driver launch 12.6 degrees, attack angle +2.8 | TrackMan 2023 LPGA table (Anchor 2) |
| Amateur driver launch 12.6 degrees, spin 3,275 rpm | TrackMan Combine, average golfer 14.5 handicap (Anchor 3 Source 1) |
| "14.5-handicap" | Same |
| Charts dated 2010 and 2019, TrackMan optimizes carry | Anchor 4 Sources 1 and 2 |
| 1 degree and 200 rpm band margin | `ideals.json` `tolerances` `driver_launch_margin_deg`, `driver_spin_margin_rpm` (design choice, modeled; PING states its own tolerance of 1 degree and 300 rpm, Anchor 4) |
| TaylorMade video, 2021, "Tiger Woods' Nine Windows"; description calls it an example of the control a golfer can have with an iron | Anchor 6 Source 1, read from the video page description. The video itself was not watched, and the low / mid / high by draw / straight / fade grid is the standard reading of the drill, not a passage read (Anchor 6 "The 3 by 3 layout") |
| "Nobody has published launch monitor numbers for any window" | Anchor 6 verdict, as far as the hunt reached |
| TrackMan reports club speed, attack angle and path at the center of the head; camera monitors read attack angle about 2 degrees higher; tables do not adjust for altitude or weather | Anchor 5c Source 3; Anchor 4 Source 2 (PING chart note); Anchor 1 Source 3 footer and the gaps list |
| Tour averages pool competition and range shots | Anchor 1 Source 1 |

## Fit and gate results in "Method and limits" (ADR 0004)

| Statement | Source |
|---|---|
| Point mass, RK4 at 0.01 s, standard sea-level air, quadratic lift and drag, seven coefficients fitted once to 23 rows (PGA 12, LPGA 11), no per-club terms, published spin decay | ADR 0004 decision 1 |
| Original gate: carry 3 percent, height 3 yd, land angle 2 degrees, passed on 6 of 23 rows; teaching tolerance 5 percent, 4 yd, 3 degrees, passed on 12 | ADR 0004 decision 2 (quad7 passes 6 of 23 rows on the original gate, 12 of 23 on the teaching tolerance) |
| PGA 3-wood, 5-wood, hybrid and 6-iron 4.5 to 5.1 yd too high; PGA 3-iron through 5-iron land 3.7 to 4.2 degrees shallower; PGA wedge carry 8.5 yd short | ADR 0004 known-misses table (3-wood +4.6, 5-wood +5.1, hybrid +5.1, 6-iron +4.5; 3, 4, 5 iron -3.7, -4.2, -4.1; PW -8.5) |
| 17 of 23 rows pass launch within 1 degree, spin within 10 percent, ball speed within 2 percent; LPGA driver spin -24.5 percent, LPGA 3-wood +30.2 percent before trim | ADR 0004 decision 3 |
| Spin trims 0.77 to 1.32 (LPGA driver 1.324, LPGA 3-wood 0.768), presets within 1 percent of published spin | ADR 0004 decision 3a |
| Amateur driver measured, 6-iron and PW Optimizer defaults, other clubs interpolated | ADR 0004 decision 6 |
| Curvature within 20 percent or 3 yd on eight examples in calibration; model carries 2 to 12 percent under quoted carries; driver examples asymmetric (9.5 yd per degree left, 8.8 right) | ADR 0004 decision 4. The 20 percent claim is the calibration against the 2019 rows. The live 2023 presets are within `ex-miss` yd of the dots |
| Launch fit spans 12.7 to 25.9 degrees of spin loft | ADR 0004 decision 3 (k held flat outside 12.7 to 25.9, the range of the four fitting points) |
| Roll is an empirical rule with no source, total distance modeled | ADR 0004 context and design doc; source log gaps item 8 |
| Start-direction shares unverified | ADR 0004 decision 5; Anchor 5a |
