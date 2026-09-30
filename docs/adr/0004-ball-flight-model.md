# ADR 0004: Release 004 ball flight model, its calibration, and the gate tolerances it ships with

Date: 2026-09-29 · Status: accepted (by merge of PR #32, 2026-09-29) · Decider: Sunny

## Context

Release 004 (issue #19) turns a club delivery (club speed, attack angle, club path, face angle, dynamic loft) into a flown shot. The design doc (docs/plans/2026-09-28-004-ball-flight-laws-design.md) sets three gates. G2 checks the flight model against the TrackMan 2023 Tour tables: carry within 3 percent, max height within 3 yd, land angle within 2 degrees. G3 checks the delivery-to-launch model: launch within 1 degree, spin within 10 percent, ball speed within 2 percent. G4 checks physics sanity: symmetry, monotonicity and five golfer cases.

The source log (docs/sources/004_Source_Log.md) fixes what the models can be fitted to. It holds 23 Tour rows (PGA 12, LPGA 11), dynamic loft and spin loft for four of them (driver and 6 iron), and eight worked face-to-path curvature examples. It records gaps: no primary text for the start direction shares (Anchor 5a), no D-plane equations or per-degree curvature law (5b, 5d), no measured amateur irons (Anchor 3), and no Tour club path or face angle. Every model number that is not in the log is labeled MODELED in data.py.

Task 004.2 built the flight model and task 004.3 built the delivery model. They share one calibration set and one list of misses, so this ADR records both.

## Decision

**1. Flight model: quadratic coefficients (quad7) with the published spin decay.**
`flight.py` integrates a point mass with gravity, drag and Magnus lift by RK4 at dt 0.01 s. Lift and drag follow the quadratic family of Anchor 7 Source 4 (McNally, Lambeth and Brekke): CL = l0 + l1 S + l2 S^2 and CD = d0 + d1 S + d2 S^2 + d3 (Re - 1.5), with S = R omega / v. The seven coefficients are MODELED. `calibrate.py --fit` fits them once to all 23 rows, shared by every club and both tours, with no per-club factors. Spin decays at the published rate, k = 2.0e-5 in SI (Anchor 7 Source 3, Smits and Smith). Air is standard sea level.

Nathan's workbook (Anchor 7 Source 1) is the baseline and stays reproducible in `baselines.py` and `calibrate.py --nathan`. The port reproduces his default shot at 259.0 yd and 4.97 s against 259.3 yd and 4.99 s in the sheet. Fitted to the Tour rows, his published forms fail. With the Reynolds branch on (`data.NATHAN["re_branch"]`), Cd0 climbs toward 1.945 below 81 mph, every iron dives at 60 to 70 degrees and the best two-multiplier fit passes 0 of 23 rows (rms 5.4 in units of the G2 tolerances). Holding Cd0 flat (`data.NATHAN_FLAT_FIT`) gives rms 1.3 and 3 of 23 rows, with a lift multiplier of 2.3.

Held-out evidence for quad7, from `calibrate.py --compare` (also in the data.py comments):

| Variant | Params | G2 rows passed | Teaching rows passed | rms, all rows | Fit on PGA, scored on LPGA | Fit on LPGA, scored on PGA |
|---|---|---|---|---|---|---|
| quad7 (shipped) | 7 | 6 | 12 | 1.016 | 0.989 | 1.298 |
| A: quad7 plus fitted decay k | 8 | 7 | 12 | 0.987 | 0.958 | 1.245 |
| B: logistic low-Re drag plus k | 8 | 8 | 14 | 1.040 | 1.521 | 1.236 |

A gains 0.04 on the held-out mean, which is inside the noise, and its fitted k landed on the 6.0e-5 bound of its search range, three times the published value. Shipping it would replace a published constant with a fitted one for no measurable transfer. B passes the most rows (8 and 14) and transfers worst from PGA to LPGA. quad7 stays. Its rms by component is carry 0.81, height 0.95, land angle 1.24 (1.0 sits on the gate).

**2. G2 retargets to the teaching tolerance.**
No shared coefficient set passes the original G2 on every row: quad7 passes 6 of 23. The gate for release 004 becomes carry within 5 percent, height within 4 yd and land angle within 3 degrees, which quad7 passes on 12 of 23 rows. The original tolerance stays as a reported metric. Both lists are recorded in `tests/g2_known_misses.json`, each row is xfail(strict=False) with its size, and `test_no_new_or_worse_misses` fails if a new row misses or a recorded component grows by more than 0.15.

Rows that still miss the teaching tolerance (model minus table):

| Row | Miss |
|---|---|
| PGA driver | land angle +3.4 deg |
| PGA 3-wood | height +4.6 yd |
| PGA 5-wood | height +5.1 yd |
| PGA hybrid | height +5.1 yd, land angle -3.0 deg |
| PGA 3 iron | land angle -3.7 deg |
| PGA 4 iron | land angle -4.2 deg |
| PGA 5 iron | land angle -4.1 deg |
| PGA 6 iron | height +4.5 yd |
| PGA PW | carry -8.5 yd |
| LPGA 3-wood | height -4.2 yd, land angle -4.4 deg |
| LPGA 5 iron | land angle -3.4 deg |

Six more rows miss only the original G2 tolerance: PGA 7 iron (carry -5.6 yd, land angle -2.0), PGA 9 iron (land angle -2.5), LPGA driver (carry -7.3), LPGA hybrid (height +3.6), LPGA 4 iron (carry -6.6) and LPGA PW (height -3.6, land angle -2.0). Two patterns stand out. The PGA 3-wood, 5-wood, hybrid and 6 iron come out 4.5 to 5.1 yd too high, and the PGA 3 to 5 iron land 3.7 to 4.2 degrees shallower than the table. One coefficient set that fits both tours and every club cannot match both, and per-club factors would break the rule that the model has no per-club terms. The tables are pooled averages of range and competition shots with integer speeds, so a residual of this size sits near the data's own noise.

**3. Delivery model (`launch.py`).** All of it is MODELED and fitted by `calibrate_launch.py --fit`.

- Geometry. Club direction d comes from path and attack angle. The face normal n comes from face angle (azimuth) and dynamic loft (elevation). Spin loft is the 3D angle between them. It equals dynamic loft minus attack angle when path and face are zero.
- Launch vector. u = normalize((1 - k) d + k n) with k linear in spin loft and held flat outside the range it was fitted on. The driver has its own line (spin loft 6.3 to 23.2, decision 3c). Every other club uses the line fitted to the four published triples (12.7 to 25.9). Launch angle and launch direction both come from u. The plane of d and n is the D-plane.
- Fit of k. The exact k per published (dynamic loft, attack angle, launch) triple is 0.824 (PGA driver), 0.738 (PGA 6 iron), 0.771 (LPGA driver) and 0.730 (LPGA 6 iron). The line fitted to those four is k = 0.8643 - 0.005170 SL, with launch residuals of -0.42, +0.07, +0.35 and 0.00 degrees. It stays the line for hybrids, woods, irons and wedges and was not refit. The driver line replaced it for the driver in decision 3c.
- Default dynamic loft. `launch_tools.derive_dyn_loft` inverts the launch model so the tour attack angle and that loft reproduce the table's launch at path 0 and face 0. For the four published rows the inverted loft sits within 0.9 degrees of TrackMan's (PGA driver 12.7 against 12.8, PGA 6 iron 20.1 against 20.2, LPGA driver 14.6 against 15.5, LPGA 6 iron 23.6 against 23.6). The result for every Tour row is stored in `data.TOUR_DYN_LOFT` (printed by `calibrate_launch.py --write-tour-dyn-loft`), and a test checks the table against a live inversion to 0.05 degrees. Other clubs have no published loft, so their derived loft is MODELED. It runs from 12.4 (PGA 3-wood) to 35.3 degrees (LPGA PW).
- Smash. smash = 1.5688 - 0.005394 SL - 0.0000820 SL^2, capped at 1.49 (the largest published smash). It is monotone decreasing from 0 to 45 degrees of spin loft. It is fitted to ball speed over club speed on all 23 rows, because the gate tests ball speed. The printed smash column differs from that ratio by up to 0.03 (log, Anchor 2). A fit to the printed column misses ball speed on 3 rows and the ratio fit misses 1 (LPGA 8 iron, -2.3 percent). No extra smash penalty for face-to-path was added, since the 3D spin loft already falls as face-to-path grows. The driver uses the same smash law: against the 60 chart rows of decision 3c it leaves ball speed within 1.4 percent.
- Spin, irons and woods. spin = f x 0.7787 x ball speed x SL^1.3045, where f is 0.8788 for the 3-wood and 5-wood and 1 for hybrids, irons and wedges. The three numbers come from a soft-L1 fit on relative error across all 23 rows (rms 9.5 percent), made in task 004.3 before the driver had its own law, and they are unchanged. There is no per-tour factor. The table's spin ladder is not one smooth curve: the PGA driver spins 1,100 rpm below the 3-wood at the same spin loft. The wood factor is modest in reason: fairway woods are low-CG heads and give less spin per degree of spin loft than an iron. The published evidence that strike location moves spin loft, and so spin, is Anchor 5(c) Source 3: a 10 mm low strike makes a driver's dynamic loft 2 degrees lower. The log holds no spin-by-strike-height data, so the size of the factor is a fit and not a measurement.
- Spin, driver. spin = 1.3352 x ball speed x SL^1.0410, fitted to the TrackMan 2010 chart and the published driver rows (decision 3c). It replaced the earlier driver factor on the iron law (0.6461).
- Spin axis. The D-plane normal tilts by about atan2(face-to-path, vertical spin loft). The shipped axis is that tilt times c = 1.2177 - 0.008835 SL, held to spin lofts 12.4 to 26.9 (decision 4).

G3 result. Launch passes on all 23 rows because dynamic loft is derived from launch, so launch checks the inversion and the fit of k, and the published-loft rows above test it as a separate check. Spin and ball speed are the working tests, and 17 of 23 rows pass all three. The misses, all recorded in `tests/g3_known_misses.json`:

| Row | Miss |
|---|---|
| PGA driver | spin +35.0 percent (model 3,436 rpm, table 2,545) |
| PGA 5-wood | spin -11.9 percent |
| LPGA 3-wood | spin +30.2 percent |
| LPGA 5-wood | spin -10.7 percent |
| LPGA hybrid | spin +12.2 percent |
| LPGA 8 iron | ball speed -2.3 percent |
| LPGA driver, published spin loft | spin loft at the published dynamic loft is 12.7 against 15.0 (-2.3 degrees) |

Spin for the driver and woods, global model with no trim (model against table, rpm):

| Row | Model | Table | Error |
|---|---|---|---|
| PGA driver | 3,436 | 2,545 | +35.0 percent |
| PGA 3-wood | 3,690 | 3,663 | +0.7 percent |
| PGA 5-wood | 3,807 | 4,322 | -11.9 percent |
| PGA hybrid | 4,355 | 4,587 | -5.1 percent |
| LPGA driver | 2,492 | 2,506 | -0.5 percent |
| LPGA 3-wood | 3,378 | 2,595 | +30.2 percent |
| LPGA 5-wood | 3,859 | 4,320 | -10.7 percent |
| LPGA hybrid | 5,052 | 4,504 | +12.2 percent |

The driver law comes from TrackMan's own model output and has no strike offset, so the two Tour drivers separate. The LPGA driver lands within 0.5 percent. The PGA driver sits 35 percent over its table, which says the PGA Tour average driver spins about 26 percent less than TrackMan's model gives for the same delivery (trim 0.741). Above-center strikes would do that and the log cannot confirm it. The refit reverses an earlier trade, in which a shared driver factor put the PGA driver in band and the LPGA driver 24.5 percent under. The LPGA 3-wood misses at +30.2 percent because the table's LPGA 3-wood spin (2,595) sits with the driver and far below the LPGA 5-wood (4,320), and the 3-wood and 5-wood share one factor. The PGA driver spin loft, taken at the published dynamic loft of 12.8, lands 1.0 degree from the published value, on the line, and the LPGA driver's is 2.3 degrees under (12.7 against 15.0, unexplained in the log). Held out and never fitted: the TrackMan Optimizer 6 iron reads launch 15.6 against 16.9 degrees and PW reads 26.1 against 26.7, and the Combine average driver reads launch 12.3 against 12.6 and spin 3,463 against 3,275 rpm (+5.7 percent, before any trim).

**3a. Spin trim per preset (`presets.py`).** The global model above stays as fitted, and G3 tests it with no trim. Each preset also carries `spin_trim`, a MODELED multiplier that `launch.deliver(..., spin_trim=)` applies to spin and nothing else. For a Tour row the trim is table spin over model spin at the preset delivery (path 0, face 0, derived dynamic loft). The amateur driver takes the Combine average-golfer spin (3,275 rpm) and the amateur 6 iron and PW take the Optimizer default spin (5,956 and 8,408 rpm), each over model spin. Other amateur clubs interpolate the trim between the anchored clubs by club speed. LPGA 3 iron uses the 4 iron's trim. The trim stands for where on the face each player group strikes the ball, which the published averages include and the model does not. It stays fixed as students move the sliders, so the model supplies only the response to delivery changes, and `scale_speed` keeps it.

Trims (published spin over model spin; 1.00 means the global model already matches):

| Club | PGA | LPGA | Amateur |
|---|---|---|---|
| driver | 0.741 | 1.005 | 0.946 |
| 3-wood | 0.993 | 0.768 | 0.961 |
| 5-wood | 1.135 | 1.120 | 0.973 |
| hybrid | 1.053 | 0.891 | 0.986 |
| 3 iron | 1.010 | 0.985 (4 iron) | 0.992 |
| 4 iron | 1.020 | 0.985 | 0.998 |
| 5 iron | 0.989 | 0.987 | 1.004 |
| 6 iron | 0.974 | 0.989 | 1.011 |
| 7 iron | 0.980 | 1.020 | 1.005 |
| 8 iron | 1.037 | 1.035 | 0.998 |
| 9 iron | 1.041 | 0.964 | 0.992 |
| PW | 0.982 | 1.041 | 0.985 |

The driver refit of decision 3c moved only the driver trims and the amateur trims that interpolate from the driver. Before it they read PGA driver 0.930, LPGA driver 1.324, amateur driver 1.191 and amateur 3-wood, 5-wood, hybrid, 3 iron, 4 iron, 5 iron 1.148, 1.114, 1.079, 1.062, 1.045, 1.028. All 35 trims fall inside 0.6 to 1.6, the bound the tests enforce. Irons and wedges sit within 0.96 to 1.04 for the Tours and within 0.98 to 1.01 for the amateur. Trims far from 1 mark where the global model is weakest: the PGA driver (0.741), LPGA 3-wood (0.768), the PGA and LPGA 5-wood (1.14, 1.12) and the PGA hybrid (1.05). Those are the rows where the table's spin does not follow the club ladder or, for the PGA driver, the Tour average sits well under TrackMan's own model output.

With the trim every Tour and anchored amateur preset reproduces its published spin to within 1 percent. Launch and ball speed come from the global model and still miss on two amateur preset rows, recorded in `tests/g3_known_misses.json` under `presets`: amateur driver ball speed +2.8 percent and amateur 6 iron launch -1.28 degrees (the Optimizer 6 iron loft against a model that reads launch low there). The Tour presets' launch and ball speed are their G3 rows' numbers, so the LPGA 8 iron ball speed miss (-2.3 percent) is recorded once, under `g3`. The amateur driver launch now reads 12.3 against the Combine's 12.6 (it read 11.4 before the driver refit).

**3c. Driver calibrated to the TrackMan 2010 chart.** The iron spin law and k line extrapolated below their fitted spin loft floor of 12.7. At PGA driver loft and +6 degrees of attack (spin loft 7.4) the model gave 1,086 rpm, and at equal spin loft it ran 23 percent under TrackMan's 2010 chart on average (14 to 33 percent under, launch 1.0 degree low on average, worst 2.3, over the 30 CARRY rows). Every positive attack angle at Tour loft sits below that floor, and the tool lets students go to +10.

Calibration data: the 60 rows of TrackMan's 2010 Driver Fitting Chart (Anchor 4 Source 1), the 30 CARRY optimizer rows in `data.TRACKMAN_CARRY_2010` and the 30 TOTAL optimizer rows in `data.TRACKMAN_TOTAL_2010` (parsed from the log table by script), labeled "TrackMan 2010 chart (TrackMan model output)". Each row is TrackMan's own launch-model output for a driver delivery (club speed 75 to 120 mph, attack angle -5, 0 and +5, dynamic loft, launch, spin), whatever the optimizer objective, so it is valid calibration data for driver launch and spin. Spin loft runs 6.3 to 23.2 degrees. The chart is 2010 vintage, uses the radar attack angle convention, and carries no strike-location offset. It is model output and not measurement.

Fit, driver only, iron laws and woods unchanged:

- k. The exact k of the chart rows is about 0.85 at every spin loft (rms 0.003 around a line). The driver line is a weighted least-squares fit through the 60 chart rows and the two published driver triples, each published triple weighted as 15 chart rows (`PUBLISHED_DRIVER_K_WEIGHT`, MODELED). At weight 1 the chart wins and the LPGA driver's inverted loft leaves the published 15.5 by 1.1 degrees, over the 1 degree check. At 15 both checks hold. The line is k = 0.8251 + 0.000433 SL over the chart's range 6.3 to 23.2. Launch against the chart: rms 0.22 degrees, worst 0.30. Launch against the published triples: +0.10 (PGA driver) and +0.76 (LPGA driver) degrees.
- Spin. A power law in spin loft with its own coefficient and exponent, 1.3352 x ball speed x SL^1.0410, soft-L1 on relative error over the 60 chart rows and the PGA and LPGA driver rows. The exponent is near 1, so driver spin falls in near proportion to spin loft, where the iron law (exponent 1.30) fell toward zero. Two parameters replace the earlier driver factor.

Result against all 60 chart rows, through `deliver` at path 0 and face 0 with the model's own ball speed (error is model minus chart; mean, then largest absolute):

| Group | Rows | Launch, deg | Spin, percent | Ball speed, percent |
|---|---|---|---|---|
| Attack -5 | 20 | -0.22, 0.30 | +0.52, 1.19 | +0.72, 1.19 |
| Attack 0 | 20 | -0.22, 0.28 | +0.18, 1.31 | +0.70, 1.34 |
| Attack +5 | 20 | -0.20, 0.27 | +0.49, 1.65 | +0.41, 1.21 |
| 75 mph | 6 | -0.22, 0.27 | +0.30, 1.19 | +0.73, 1.05 |
| 90 mph | 6 | -0.20, 0.25 | +0.74, 1.52 | +0.60, 1.34 |
| 105 mph | 6 | -0.22, 0.28 | +0.31, 0.81 | +0.66, 1.14 |
| 120 mph | 6 | -0.17, 0.24 | +0.00, 1.31 | +0.20, 1.19 |
| All | 60 | rms 0.22 | rms 0.76 | rms 0.77 |

The other club speeds (80, 85, 95, 100, 110 and 115 mph) fall between these rows, with launch worst 0.30, spin worst 1.65 and ball speed worst 1.42 percent. There is no drift with speed or attack angle. This is in-sample.

PGA driver at the preset (115 mph, dynamic loft 12.7, trim 0.741), across attack angle. The old model is the iron law with its driver factor and the old preset trim (0.930):

| Attack, deg | Spin loft | Launch | Spin, new | Spin, new with trim 1 | Spin, old |
|---|---|---|---|---|---|
| -6 | 18.7 | 9.6 | 3,448 | 4,656 | 3,684 |
| 0 | 12.7 | 10.5 | 2,381 | 3,214 | 2,349 |
| +3 | 9.7 | 11.0 | 1,801 | 2,432 | 1,696 |
| +6 | 6.7 | 11.5 | 1,224 | 1,653 | 1,086 |
| +10 | 2.7 | 12.2 | 474 | 640 | 392 |

With dynamic loft raised with attack angle (spin loft held at 12.7) spin holds at 2,545 by construction and launch runs 5.3, 11.3, 14.3, 17.3 and 21.3 degrees at attack -6, 0, +3, +6 and +10. At +6 the untrimmed spin (1,653) sits on the chart's own 115 mph row at the same spin loft (attack +5, dynamic loft 11.7: 1,681 rpm). The trimmed 1,224 is lower because the trim holds the Tour strike offset fixed as attack angle changes. That is an assumption the data cannot check. At +10 the spin loft (2.7) is below the chart's lowest (6.3), where k is held flat and spin follows the near-linear law toward zero, and no row supports that end.

Effects on the presets: the PGA driver preset still reproduces 10.4 degrees and 2,545 rpm and sits inside its ideal launch band (8.3 to 11.4) and spin band (2,439 to 3,232). The amateur driver preset reads launch 12.3 (band 10.9 to 13.4) and spin 3,275 (band 2,565 to 3,500). The LPGA driver preset's launch (12.6) sits below its ideal band (13.2 to 15.8) as before, since the preset launch is the table value.

**3b. Input domain and port surface.** `launch.deliver(club_speed_mph, attack_deg, path_deg, face_deg, dyn_loft_deg, club=None, *, params=None, spin_trim=1.0)` raises ValueError, naming the argument, for a non-finite value, a value outside `data.DOMAIN`, dynamic loft minus attack angle under 1 degree, a `spin_trim` that is not positive, or a club that is neither None nor a key of `data.PGA`. `data.DOMAIN` is a MODELED design choice that the tool's sliders clamp to: club speed 40 to 140 mph, attack angle -10 to +10, path -15 to +15, face -15 to +15, dynamic loft 0 to 65 degrees, and a minimum vertical spin loft of 1 degree (the fits have no data below spin loft 6.3 for the driver and 12.7 for every other club, and the D-plane normal is undefined at zero). `swing_path` accepts a plane angle between 20 and 80 degrees, ends excluded, and `presets.scale_speed` a speed inside the club speed range. Smash holds at a floor, the fit's own value at spin loft 45 (1.160), because the quadratic keeps falling past the last fitted row. The D-plane normal is oriented without a tie: an exact tie on the horizontal axis breaks toward +90 degrees. Outputs never carry a negative zero.

`launch.py` holds only what the JS port needs: `deliver`, its helpers, `swing_path` and `Launch`. The inversion, the face share and other fitting helpers live in `launch_tools.py`. Gate scoring lives in `gates_launch.py` with no scipy, and `tests/golden_launch.json` (40 deliveries with `deliver` outputs and flight summaries at dt 0.01) is the vector file the parity test will read. Its regeneration command is `calibrate_launch.py --write-golden`. The known-miss record uses strict xfails, detects stale entries in all three sections (`g3`, `published`, `presets`), and ratchets on live floors (17 of 23 G3 rows, 8 of 8 curvature examples, every preset's spin, and the amateur PW), the same way the flight tests do. `--write-misses` refuses a worse result unless `--force` is given.

**4. Curvature calibration and the flight model's over-curve.**
The face-to-path to curve mapping is what students see, so it follows TrackMan's eight examples (Anchor 5b) and not the flight model's own curve per degree of spin axis. `flight.py` gives a 6 iron more curve than a 3-wood at the same axis (13.9 against 12.8 yd at 10 degrees, the LPGA 6 iron and 3-wood Tour rows), the wrong order against TrackMan's 11 and 15 yd, and `test_flight.py` records that as an xfail. That over-curve of short irons per degree of axis is a known limit of the flight model. The scale c on the spin axis absorbs it.

Each example runs from the 2019 row of the same tour and club, path 0 and face equal to face-to-path, with the loft inverted from that row's launch. Those rows are SUPERSEDED in the log and sit in `data.SUPERSEDED_2019` for this purpose only, because TrackMan's examples quote 2019 carries (PGA driver 275, PGA 6 iron 183, LPGA driver 218, LPGA 6 iron 152). Each example also takes a spin trim from its own 2019 row (2019 spin over model spin at path 0 and face 0), held fixed as the face opens, the same way a preset's trim works. The fit gives c(SL) = 1.2177 - 0.008835 SL, held to spin lofts 12.4 to 26.9 (the examples' own range), which is 1.11 at spin loft 12.4 and 0.98 at 26.9. Results against the published curvature (positive is right):

| Example | Model | Published | Error |
|---|---|---|---|
| PGA driver, -2 | -17.8 yd | -19 | +6 percent |
| PGA driver, +5 | +42.0 | +44 | -5 percent |
| PGA 6 iron, +2 | +8.8 | +8 | +11 percent (0.8 yd) |
| PGA 6 iron, -5 | -21.5 | -20 | -8 percent |
| LPGA driver, +2 | +14.5 | +14 | +3 percent |
| LPGA driver, -5 | -33.4 | -32 | -4 percent |
| LPGA 6 iron, -2 | -5.3 | -6 | +12 percent (0.7 yd) |
| LPGA 6 iron, +5 | +12.8 | +14 | -8 percent |

All eight sit inside the larger of 20 percent and 3 yd, the worst at 0.39 of its tolerance (rms 0.28). The D-plane tilt supplies most of the driver-to-iron ordering, because a lofted club has less tilt per degree of face-to-path. Two forms fit. A constant c = 1.046 leaves the worst error at 0.64 of tolerance and 2.6 yd (the PGA 6 iron at -5, 22.6 yd against 20), with the driver fine. The linear form cuts the worst error to 0.39 and 1.5 yd and the driver errors to 1.2 and 2.0 yd, at the cost of one parameter, so it ships. The slope is small: c moves 0.13 across the whole range. It also trims the 6 iron's over-curve. The 2023 PGA 6 iron preset (carry 186) curves 9.8 yd at face-to-path +2 and 23.8 at -5, against TrackMan's 8 and 20 on the 2019 row (carry 183), where the constant gave 10.2 and 24.8. The model carries in these examples run 2 to 8 percent under the quoted carries (the PGA driver flies 251 to 263 yd against 275, the LPGA driver 198 to 209 against 218), so c also carries a share of that gap. The published driver examples are asymmetric (9.5 yd per degree left, 8.8 right), and the model is symmetric. The linear c was in use before the spin trims and was dropped when they went in. The driver refit put it back because the driver law changed the examples' spin, and a slope now fits better than the constant.

**5. Start direction shares stay unverified.**
The model does not take the 85 / 75 (PGA Academy, unattributed) or 87 / 81 (forum, attributed to TrackMan Academy) shares as inputs. The horizontal face share follows from the fitted k and the lofts: k cos(L) / ((1 - k) cos(A) + k cos(L)). It reads 82.7 percent for the PGA driver, 82.5 for the LPGA driver (with the driver's own k line), 72.9 for the PGA 6 iron and 71.3 for the LPGA 6 iron, falling to about 69 percent at the PW. That is 2 points under the 85 claim for the driver and 2 under the 75 claim for a 6 iron, and lower than the 87 and 81 claims. The comparison checks plausibility and cannot favor either set. A human should read Tuxen's "TRACKMAN Ball Flight Laws" (log, Anchor 5a) and refit k if its table differs.

**6. Amateur presets, and the MODELED irons.**
The driver comes from the TrackMan Combine "Average golfer (14.5)" column, which is measured: club speed 94, attack angle -1.8, dynamic loft 15.1. The 6 iron (80 mph, -3.2, 22.4) and PW (72 mph, -3.9, 36.7) are TrackMan Optimizer defaults, which are model outputs and not measurements, and the preset flags them as such. Every other club is MODELED. Club speed, attack angle and dynamic loft interpolate between the two nearest anchored clubs, placed by where the PGA Tour value for that club falls between the PGA values of the anchor clubs, so the PGA shape guides the ladder. The position is held to the range 0 to 1, so no club leaves the span of its two anchors. That clamp has one visible effect: the PGA driver's derived loft (12.7) sits above its 3-wood (12.4), so the amateur 3-wood takes the driver's loft (15.1), and amateur loft is non-decreasing from the driver through the PW and rising at every step from the 5-wood (15.4) on. That is the recorded exception, and a test checks it.

One deviation from the brief. Scaling PGA club speed by 94 / 115 for the other clubs puts the amateur 5 iron (78.5 mph) below the anchored 6 iron (80) and the 9 iron (71.1) below the anchored PW (72). Interpolating speed the same way as the other two quantities keeps the ladder in order and hits the anchors. LPGA has no 3 iron, so `preset("3i", "lpga")` returns the 4 iron and says so in its `note` and `club` fields.

## Consequences

- G2 for release 004 is the teaching tolerance. The 11 rows above, and the six that miss only the original tolerance, ship as documented xfails. Any UI number for those rows is a model output and can sit outside the table by the sizes listed.
- Every ideal preset reproduces its published spin to within 1 percent through its spin trim, so the PGA and LPGA driver presets do not light their own spin tiles. The trims for the PGA driver (0.741), LPGA 3-wood (0.768) and the 5-woods (1.14, 1.12) are the farthest from 1, and they mark where the global model is weakest. A slider move away from a preset uses the global model's response to spin loft, scaled by that fixed trim. A user who picks a preset and then changes dynamic loft by a few degrees sees the model's slope, and a preset with a trim far from 1 inherits any error in that slope. The amateur trims come from one Combine average and two Optimizer defaults, and the other amateur trims interpolate between them, so they are MODELED.
- Curvature follows TrackMan's published examples within 13 percent (or 3 yd) for both tours on the driver and 6 iron, with c linear in spin loft. Curvature for the other clubs is extrapolation through spin loft and the flight model, with no published check. The 10-degree spin axis examples in `test_flight.py` remain a separate check on the flight model.
- Driver spin below spin loft 6.3 (attack angle above about +6 at Tour loft) is extrapolation past the TrackMan 2010 chart. The tool lets students reach +10, where spin loft is 2.7 at the PGA preset and spin about 470 rpm. No row supports that end.
- The launch model has no test against a published start direction share. The golfer cases test signs, the face = path identity and symmetry, none of which depend on the share.
- Every value in `data.LAUNCH_MODEL` is regenerated by `calibrate_launch.py --fit` and pasted by hand. `--write-misses` regenerates `tests/g3_known_misses.json`. `--fit` refits every parameter in order (iron k line, smash, iron and wood spin, then the driver k line and spin law, then c), and c depends on all of them, so a change to any needs the whole fit rerun. A refit also needs `--write-tour-dyn-loft` pasted, then `--write-misses`, `--write-golden`, `export.py` and the JS parity test.
- Open items for Sunny: accept the G2 retarget, decide whether the three rows that miss launch or ball speed (amateur 6 iron launch at -1.28 degrees, amateur driver ball speed at +2.78 percent, LPGA 8 iron ball speed at -2.3 percent) need a trim like the spin trim, and decide whether a human reading of Tuxen's document (start direction shares, D-plane equations) is worth doing before the article states a share.

## Addendum (2026-09-29, branch 004-copy-pass): flight and roll recalibrated to the TrackMan 2010 chart

**Problem.** The owner found that the driver did not reward hitting up. Fed the 2010 chart's own launch conditions (`data.TRACKMAN_CARRY_2010` and `data.TRACKMAN_TOTAL_2010`, 60 rows, labeled "TrackMan 2010 chart (TrackMan model output)"), the flight model under-carried the high-launch, low-spin rows. At 115 mph the chart's carry rises 266, 281, 295 yd across attack angle -5, 0 and +5. The model gave 264, 272, 278 (the +5 row 278 against 295). Chart carry errors averaged -1.6, -4.0 and -6.4 percent at attack -5, 0 and +5, and the roll model (tuned to landing angle alone) missed chart totals by 17 yd rms. The delivery model was not at fault: it reproduces the chart's launch to 0.3 degrees and its spin to 1.7 percent (decision 3c). The aero fit had seen the 23 Tour rows, which hold one driver each.

**Decision 1: refit quad7 on both sets.** The seven coefficients keep their form and the published spin decay (k = 2.0e-5). `calibrate.py --fit-chart` fits the 23 Tour rows (carry, height and land angle, each in units of its G2 tolerance) and the 60 chart rows (carry only, in units of 3 percent), each flown from its own ball speed, launch and spin with no axis. Each set is divided by the square root of its residual count, then the chart set gets weight 2.0. The physical constraints are unchanged (CD and CL positive, CL non-decreasing and at most 0.40, CD 0.15 to 0.45, on S 0.05 to 0.50 and Re 0.5e5 to 2.3e5). Weight 2.0 is the smallest on the grid 1, 1.5, 2, 3, 4 that puts all 60 chart rows within 3 percent:

| Chart weight | Tour rms | Chart rms | Worst chart row | Tour G2 passes | Tour teaching passes |
|---|---|---|---|---|---|
| 0 (before) | 1.016 | 1.52 | 7.9 percent | 6 | 12 |
| 1 | 1.10 | 0.60 | 3.9 percent | 5 | 12 |
| 1.5 | 1.13 | 0.52 | 3.4 percent | 6 | 14 |
| **2 (shipped)** | **1.19** | **0.42** | **2.8 percent** | **6** | **15** |
| 3 | 1.31 | 0.31 | 2.0 percent | 6 | 10 |
| 4 | 1.41 | 0.23 | 1.7 percent | 3 | 7 |

New coefficients: d0 0.16554, d1 0.72226, d2 -0.57345, d3 -0.02957, l0 0.05793, l1 1.28987, l2 -1.21142 (before: 0.19877, 0.52450, -0.50182, -0.09224, 0.05635, 1.36147, -1.34813). CD at Re 1.5 reads 0.216, 0.261, 0.331 at S 0.075, 0.15, 0.30, and CL reads 0.148, 0.224, 0.336.

**Variants.** The linear form fits both sets, so the variants stay evidence. `calibrate.py --compare-chart` fits each on both sets, on the Tour rows alone (scored on the chart) and on the chart alone (scored on the Tour rows):

| Variant | Params | Tour rms | Chart rms | Worst chart row | Tour G2 | Tour teaching | Tour fit scored on chart | Chart fit scored on Tour |
|---|---|---|---|---|---|---|---|---|
| quad7 (shipped) | 7 | 1.192 | 0.419 | 2.8 percent | 6 | 15 | 1.523 | 2.245 |
| plus l3 S^3 lift | 8 | 1.187 | 0.428 | 2.8 percent | 6 | 15 | 1.597 | 2.338 |
| plus low-S lift term | 8 | 1.233 | 0.431 | 2.7 percent | 6 | 12 | 1.904 | 2.461 |
| logistic low-Re drag | 8 | 1.048 | 0.386 | 3.3 percent | 7 | 16 | 1.298 | 2.250 |

The extra lift terms buy nothing. The logistic drag fits both sets a little better in sample but leaves one chart row outside 3 percent, adds a parameter, and its held-out ranking flips with the start point (the objective has a flat valley in d2 and l2, so a held-out score moves by up to 0.7 with the start). A chart-only fit scores 2.2 to 2.5 on the Tour rows for every variant, since the chart spans S 0.05 to 0.14 and leaves the wedge range free. quad7 ships.

**Result against the chart** (model minus chart, from the chart's own launch conditions, dt 0.01). Carry error by attack angle, mean and worst, before and after:

| Attack | Before, mean | Before, worst | After, mean | After, worst |
|---|---|---|---|---|
| -5 | -1.6 percent | 3.0 percent | +1.2 percent | 2.8 percent |
| 0 | -4.0 percent | 5.3 percent | -0.1 percent | 1.2 percent |
| +5 | -6.4 percent | 7.8 percent | -1.4 percent | 2.6 percent |

Carry gain from attack -5 to +5, model against chart (yd):

| Chart | Speed | Carry, before | Carry, after | Carry, chart | Total, before | Total, after | Total, chart |
|---|---|---|---|---|---|---|---|
| Carry rows | 90 | 11.4 | 16.5 | 23 | -2.0 | 17.3 | 24 |
| Carry rows | 105 | 12.8 | 19.3 | 26 | 0.0 | 20.8 | 28 |
| Carry rows | 115 | 14.4 | 21.8 | 29 | 5.5 | 25.3 | 31 |
| Total rows | 90 | 12.7 | 18.3 | 22 | 12.7 | 24.3 | 28 |
| Total rows | 105 | 11.1 | 18.1 | 23 | 11.1 | 32.6 | 31 |
| Total rows | 115 | 8.5 | 16.4 | 24 | 8.5 | 36.6 | 35 |

The model now rewards hitting up. It gives 68 to 83 percent of the chart's carry gain across the six cases and 72 to 105 percent of its total gain. The remaining carry shortfall (7 to 8 yd across the 10 degree swing at 115 mph) is the price of holding the Tour rows: weight 4 would close it to 26 yd against 29 and cost the Tour teaching passes 8 of 15.

Chart carry error and total error by club speed and attack angle after the refit (model minus chart, yd; carry error first, total error second, with the roll of decision 2):

| Speed | Carry rows, -5 | Carry rows, 0 | Carry rows, +5 | Total rows, -5 | Total rows, 0 | Total rows, +5 |
|---|---|---|---|---|---|---|
| 75 | +1.0 / +5.4 | -0.6 / +4.7 | -4.1 / +0.3 | +2.7 / +1.8 | +0.1 / +2.8 | -0.4 / +4.8 |
| 80 | +1.1 / +13.8 | -0.8 / +10.6 | -4.7 / +7.8 | +1.2 / +13.6 | +0.2 / +15.4 | -2.9 / +15.6 |
| 85 | +2.1 / +5.8 | -0.6 / +2.5 | -4.1 / -1.2 | +2.9 / +1.8 | +1.8 / +0.9 | -1.5 / +1.3 |
| 90 | +2.3 / +4.4 | -0.7 / +2.0 | -4.2 / -2.3 | +3.3 / +1.1 | -1.0 / -1.1 | -0.3 / -2.6 |
| 95 | +1.3 / -8.0 | -2.6 / -1.1 | -4.6 / -3.2 | +2.0 / -2.1 | +0.6 / -3.8 | -2.8 / -3.4 |
| 100 | +0.6 / +2.0 | -2.4 / -14.5 | -4.2 / -2.8 | +3.1 / -1.8 | +0.8 / -4.8 | -2.3 / -2.8 |
| 105 | +0.8 / +0.9 | -2.8 / -1.4 | -5.9 / -6.3 | +3.4 / -2.3 | +2.5 / -3.1 | -1.5 / -0.6 |
| 110 | +0.6 / +1.6 | -2.0 / -1.6 | -5.7 / -5.5 | +4.2 / -1.5 | +0.4 / -6.5 | +0.2 / +1.2 |
| 115 | +1.6 / +0.7 | -1.5 / -1.3 | -5.6 / -4.9 | +5.5 / -2.0 | +1.7 / -4.9 | -2.1 / -0.4 |
| 120 | +1.2 / +1.5 | -0.9 / -1.7 | -4.5 / -19.2 | +7.6 / -0.7 | +2.7 / -5.3 | -0.4 / +0.1 |

The largest total misses sit on three groups of rows: the 80 mph rows (+8 to +16), the carry rows at 100 mph and attack 0 (-14.5, the row the source log flags as a likely printing error) and the 120 mph, attack +5 carry row (-19, a chart roll of 40 yd against 24 on its neighbors). Seven rows miss the 5 percent total gate and are recorded as strict xfails. Total error across the 60 rows is 0.0 yd mean and 6.0 rms, against -10.7 and 17.3 before.

**Decision 2: roll refit to the chart's total minus carry.** `calibrate.py --fit-roll` fits three numbers on all 60 rows (both charts), flown from each row's launch conditions with the shipped aero, soft-L1 with a 5 yd scale because two totals are suspect:

roll = k x landing speed x cos(landing angle)^p x (2,500 / max(landing spin, 500 rpm))^q, capped at 80 yd

k 1.2962, p 4.3428, q 0.5594. The residual is 6.2 yd rms on rolls of 16 to 58 yd (largest 18.5). The old form, k = 8.5 and p = 10 on landing angle alone, had no way to separate the carry rows (roll near 24 yd) from the total rows (42 to 58 yd) because both land between 27 and 47 degrees. With q fixed at 0 the fit reads 8.3 yd rms. Landing spin separates them, and it is also what stops a wedge rolling like a driver, since a Tour PW lands with about 8,200 rpm. `Flight` gained `land_spin_rpm` (the spin state at the landing step). The reference 2,500 rpm, the 500 rpm floor and the 80 yd cap are MODELED constants and are not fitted. The chart holds drivers only, so irons and wedges are extrapolation, checked by eye. Roll at the Tour rows, model (yd): PGA driver 30.5, 5 iron 11.6, 7 iron 7.1, 9 iron 5.8, PW 5.4, LPGA driver 36.2, LPGA PW 7.1. Landing speeds (mph): PGA driver 63.5, 7 iron 54.2, PW 54.6. The roll stays MODELED and now rests on TrackMan's model output, not on a measured roll-out.

**Tour rows after the refit.** G2 (original tolerance) 6 of 23, teaching 15 of 23 (before 6 and 12). The PGA driver now passes G2 (283.7 yd carry against 282, height 35.2 against 35, land angle 39.5 against 39), and the LPGA driver passes as well. Rows that got worse: PGA PW carry -11.7 yd (was -8.5), PGA 7, 8 and 9 iron carry -7.6, -7.7 and -7.5 yd (the 7 iron was -5.6, and the 8 and 9 iron carry passed G2 before, so the 8 iron is a new G2 miss), the PGA 3 to 5 iron land angles -5.3, -5.7 and -5.2 degrees (were -3.7, -4.2, -4.1), the LPGA 3-wood land angle -6.2 (was -4.4), and the LPGA 5-wood and hybrid carry +6.6 and +8.1 (5-wood is a new G2 miss). Rows that came back inside the teaching tolerance: PGA driver, 3-wood and 6 iron. The updated record is in `tests/g2_known_misses.json`, written with `calibrate.py --write-misses --force` because the refit trades Tour rows against the chart (the tool refuses a worse record without `--force`): 17 G2 misses, 8 teaching misses, 0 chart carry misses, 7 chart total misses. Every entry is a strict xfail and the guard test fails on a new, worse or stale entry. The floors moved with the evidence: teaching passes at least 15, overall Tour rms at most 1.20, chart rms at most 0.45.

**Curvature examples (Anchor 5b), a check and not a fit target.** With the launch model untouched (c = 1.2177 - 0.008835 SL) all eight still pass the larger of 20 percent and 3 yd: PGA driver -2 gives -18.5 yd against -19, +5 gives +43.3 against +44, PGA 6 iron +2 gives +8.6 against +8, -5 gives -20.9 against -20, LPGA driver +2 gives +15.4 against +14, -5 gives -35.1 against -32, LPGA 6 iron -2 gives -5.2 against -6, +5 gives +12.7 against +14. The worst error is 0.49 of its tolerance (LPGA driver at -5, 3.1 yd over against 6.4) and the rms is 0.32, against 0.39 and 0.28 before. `calibrate_launch.py --fit` would refit c to 1.0724 - 0.002338 SL and bring the worst error to 0.34 of its tolerance (rms 0.27), but that changes every spin axis the tool shows, so the addendum leaves c alone and names the option.

**G3 and golfer cases.** G3 does not run the flight model, so it is unchanged: 17 of 23 rows pass launch, spin and ball speed, with the recorded misses above. The five golfer cases on the PGA 7 iron preset (path, face) keep their signs and symmetry. Flown carry, curve and total after the refit, with the old values in brackets:

| Case | Carry | Curve | Total |
|---|---|---|---|
| Straight (0, 0) | 171.7 (173.8) | 0.0 (0.0) | 178.5 (180.0) |
| Push draw (+5, +2) | 171.1 (173.3) | -10.9 (-11.3) | 178.0 (179.8) |
| Left, left (-3, -3) | 171.4 (173.6) | 0.0 (0.0) | 178.3 (179.8) |
| Push slice (-3, +4) | 166.1 (168.5) | +24.2 (+25.1) | 173.3 (175.9) |
| Pull hook (+2, -4) | 167.3 (169.6) | -21.1 (-21.9) | 174.3 (176.7) |

Iron carry falls about 2 yd and curve about 4 percent, inside the model's own residuals against the Tour table (PGA 7 iron carry 168.4 against 176 published, at path 0 and face 0 with the derived loft).

**Consequences.**
- The tool's driver now gains carry with attack angle: 68 to 83 percent of the chart's carry gain and 72 to 105 percent of its total gain. The remaining shortfall in carry gain is recorded above and can shrink only if Tour teaching passes fall.
- The Tour fit got worse in places (PGA PW carry, PGA 3 to 5 iron landing angles). Any UI number for those rows can sit outside the table by the sizes listed here.
- The roll needs landing spin. `flight.js`, `model.json` (`roll` gains `spin_power`, `spin_ref_rpm`, `spin_floor_rpm`) and `golden.json` (`land_spin_rpm` in each flight summary) change with it. `export.py` and its tests carry the new fields, but the export to `site/` and the JS port are separate steps: until they run, `tests/test_export.py::test_disk_copy_matches_a_fresh_build` and `tests/test_js_parity.py::test_ideals_fixture_is_current` fail because the committed site data and the ideal band fixture came from the old flight model.
- `tests/golden_launch.json` is regenerated (`calibrate_launch.py --write-golden`) and holds `land_spin_rpm` beside the other flight fields.
- Open items for Sunny: decide whether to refit c (the option above), and whether a carry gain near 75 percent of the chart's is enough for the article or the chart weight should rise toward 3 at the cost of Tour teaching passes.

## Addendum 2 (2026-09-29): the driver's ideal is the TrackMan 2010 chart delivery, +5 attack, balanced loft

**Decision.** The driver's ideal delivery was the Tour average (PGA attack -0.9), and its attack band was the preset plus or minus 1.5 degrees, so the tool told students that the ideal driver hits down. TrackMan's 2010 chart says carry rises with attack angle at every club speed from 75 to 120 mph (at 115 mph, 266, 281 and 295 yd at attack -5, 0 and +5), and the flight model now reproduces that chart (addendum 1). The owner wants hitting up to give the most carry and the most total distance. `data.DRIVER_IDEAL` (MODELED, chart evidence in the `data.py` comment) sets the driver ideal to the chart's top attack angle, +5, with a band of +2 to +5, path 0, face 0 and spin trim 1.0 (the chart's own strike and the basis the model is calibrated to). Dynamic loft is `chart.optimal_loft(club speed, attack)`: the mean of the TrackMan 2010 CARRY chart's and TOTAL chart's optimal dynamic loft, each bilinear over club speed (75 to 120 mph, clamped) and attack angle (-5, 0, +5), with attack beyond -5 and +5 extended along the edge slope and flagged. It also returns the two components (`carry_loft_deg`, `total_loft_deg`). Every other club keeps its preset and its downward-attack band (attack hi at most +0.7).

**Why balanced.** A first version took the loft from the carry chart alone, at attack +4. It beat the Tour-average delivery in carry for all three players, and it lost total for the LPGA (256.0 yd against 263.2): the LPGA average already hits up (+2.8), launches at 12.6 degrees and lands at 35.6 degrees, so it rolls 36 yd, and the carry optimizer's delivery lands at 40.5 degrees and rolls 26 yd. The chart's total rows want about 2 degrees less loft and 700 to 800 rpm less spin than its carry rows at the same attack angle. The balanced loft splits that difference, and at +5 it beats the average in carry and total for all three players, so the strict test has no xfail.

**Bands.** Driver `attack_deg` is 2 to 5, target 5. `dyn_loft_deg` is the balanced loft at the current club speed and attack, plus or minus 1.5. `ball_speed_mph`, `carry_yd` and the new `total_yd` (carry plus roll, plus or minus 3 percent) come from the model at the ideal delivery at the current club speed. Spin loft, smash, peak height and landing angle follow the ideal delivery at the preset speed. Launch and spin bands span three sources, the TrackMan carry chart, the TrackMan total chart and PING, and bands default to the ideal attack angle, so the lookups match the ideal delivery (see the launch and spin bands paragraph below). `presets.preset()["ideal"]` and `presets.ideal_delivery(club, player, club_speed)` carry the delivery.

**Ideal against the Tour-average delivery**, same club speed, model output:

| Player | Speed | Average: attack, loft | Carry, total | Ideal: attack, loft (carry, total loft) | Carry, total | Gain: carry, total |
|---|---|---|---|---|---|---|
| PGA | 115 | -0.9, 12.7 | 282.1, 312.9 | +5, 13.05 (14.40, 11.70) | 287.3, 327.6 | +5.2, +14.8 |
| LPGA | 96 | +2.8, 14.6 | 227.0, 263.2 | +5, 15.84 (17.42, 14.26) | 229.9, 266.6 | +2.9, +3.4 |
| Amateur | 94 | -1.8, 15.1 | 212.7, 238.3 | +5, 16.18 (17.78, 14.58) | 223.8, 260.2 | +11.1, +21.9 |

**Launch and spin bands, and the exceptions that went away.** With the ideal loft between the carry and total optimizers, the ideal driver first launched 0.3 to 0.6 degrees below the lower edge of a launch band built from the carry chart and PING, because the total chart wants a lower launch than either. The launch and spin bands now take the TrackMan 2010 TOTAL chart as a third source: the band is the lowest of the three minus 1 degree (200 rpm for spin) to the highest plus 1 degree (200 rpm), the target is the mean of the three, all three values sit in `detail` and the source text names them, evaluated at the current club speed and attack angle (PING at the ideal delivery's ball speed). The ideal driver now sits inside every band for all three players, `ideals.exceptions()` is empty and the test that the ideal sits inside all its bands holds again. Bands at each player's ideal (model launch and spin against the band, sources carry / total / PING):

| Player | Launch | Launch band (target) | Sources | Spin | Spin band (target) | Sources |
|---|---|---|---|---|---|---|
| PGA | 11.7 | 9.7 to 15.5 (12.7) | 13.0 / 10.7 / 14.5 | 2,006 | 1,481 to 2,558 (2,069) | 2,358 / 1,681 / 2,168 |
| LPGA | 14.0 | 11.9 to 17.3 (14.9) | 15.5 / 12.9 / 16.3 | 2,283 | 1,736 to 2,784 (2,248) | 2,584 / 1,936 / 2,225 |
| Amateur | 14.3 | 12.2 to 17.5 (15.2) | 15.8 / 13.2 / 16.5 | 2,308 | 1,763 to 2,803 (2,263) | 2,603 / 1,963 / 2,225 |

The wider band is the price: the launch band now spans 5.8, 5.4 and 5.3 degrees, against about 3.5 with two sources, and a launch that suits the carry optimizer sits inside it as well as one that suits the total optimizer.

**Roll cap (pre-merge review).** The roll fit saw only drivers at 75 to 120 mph, and its form grew unchecked at slow club speeds: the driver ideal at 40 mph carried 46 yd and rolled 72 (total 118), at 60 mph 107 and 164, and a 7 iron at 40 mph 41 and 79. `flight.roll` now also caps roll at `ROLL_CAP_FRAC * carry`, with `ROLL_CAP_FRAC` = 0.3592 (MODELED): 1.1 times the largest (total - carry) / carry on the 60 rows of TrackMan's two 2010 charts, 0.3265 at the 75 mph, attack 0 row of the total chart (carry 147, total 195). The cap binds on no chart row (the model's largest ratio there is 0.355), no Tour row, and no preset or ideal delivery at its own club speed, so the ideal against average results above do not move. It binds only for slow swings: the PGA driver ideal at 40 mph now carries 46.4 yd and totals 63.1 (was 118.0), at 60 mph 107.2 and 145.7 (was 164.4), at 75 mph 161.4 and 199.7 (unchanged), and the PGA 7 iron at 40 mph carries 41.2 and totals 56.0 (was 79.7), at 60 mph 96.9 and 121.8 and at 75 mph 137.9 and 151.3 (both unchanged). The cap is exported in `model.json` (`roll.cap_frac`) and ported to `flight.js`.

## Addendum 3 (2026-09-29, branch 004-physics): face-to-loft coupling through the lie angle

**Problem.** The launch model treated face angle and dynamic loft as independent inputs, so it was mirror symmetric: a draw and a fade, a hook and a slice, gave the same carry, height, spin and total to the last digit. The physics audit (`docs/sources/004_Physics_Research.md`, topics 1 and 2) says otherwise. The shaft leans at the lie angle, so rotating the head about it to close the face also delofts the club and opening it adds loft, cot(lie) degrees of loft per degree of face rotation. TrackMan says an open or closed face to path changes dynamic loft (Dynamic Loft page) and prints no coefficient. Its draw against fade example (Stickney, 2016, one driver) shows a draw at 10.5 degrees of dynamic loft and 2,643 rpm running about 20 yd past a fade at 15.0 degrees and 3,768 rpm.

**Decision.** `launch.deliver` computes an effective dynamic loft and uses it for spin loft, launch, spin and the D-plane tilt:

dyn_loft_effective = dyn_loft_input + kappa(club) x (face - path), kappa = cot(lie angle)

The input loft is the loft with the face square to the path (the slider). The effective loft is what TrackMan would measure, and `Launch` returns both (`dyn_loft_input_deg` and `dyn_loft_deg`). The tile and band for dynamic loft read the effective loft (`metricValue("dyn_loft_deg")`). The effective loft is held to at least attack plus 1 degree (the spin loft floor) and at most 65 degrees. A club that is not named has kappa 0. MODELED: the reading is a rotation of the head about the shaft with no shaft lean and no yaw of the whole club, which is the upper end of what the geometry allows (a pure yaw gives 0 and adding shaft lean raises it), and no source measured where real golfers sit. The lie angles are the manufacturers' static standard lies at address (Anchor 8 of the source log, Titleist custom options 2025 with PING G430 pages as a cross-check, retrieved 2026-09-29), not the dynamic lie at impact.

| Club | Lie, deg | kappa | Club | Lie, deg | kappa |
|---|---|---|---|---|---|
| Driver | 58.5 | 0.613 | 6 iron | 62.5 | 0.521 |
| 3-wood | 56.5 | 0.662 | 7 iron | 63.0 | 0.510 |
| 5-wood | 57.5 | 0.637 | 8 iron | 63.5 | 0.499 |
| Hybrid | 57.0 | 0.649 | 9 iron | 64.0 | 0.488 |
| 3 iron | 61.0 | 0.554 | PW | 64.0 | 0.488 |
| 4 iron | 61.5 | 0.543 | | | |
| 5 iron | 62.0 | 0.532 | | | |

`data.LIE_DEG` and `data.KAPPA` hold them and `model.json` exports them (`coupling`). PING's pages read 0.5 to 1.5 degrees flatter for woods and irons, which moves kappa by about 0.01 to 0.03.

**Check against TrackMan's example, not a fit.** The 4.5 degree loft gap needs a face-to-path swing of 4.5 / 0.613 = 7.3 degrees, plus and minus 3.7. Flying the PGA driver preset (115 mph, attack -0.9) at spin trim 1.0 (the chart's own strike, the basis the model is calibrated to) with an input loft of 12.75:

| | TrackMan draw | Model draw | TrackMan fade | Model fade | TrackMan gap | Model gap |
|---|---|---|---|---|---|---|
| Dynamic loft, deg | 10.5 | 10.5 | 15.0 | 15.0 | 4.5 | 4.5 (by construction) |
| Spin, rpm | 2,643 | 3,032 | 3,768 | 4,096 | 1,125 | 1,065 |
| Peak height, ft | 63.6 | 93.0 | 105.6 | 145.7 | 42.0 | 52.8 |
| Landing angle, deg | 28.8 | 37.6 | 42.9 | 48.4 | 14.1 | 10.8 |
| Carry, yd | 245.7 | 271.3 | 240.8 | 262.6 | draw +4.9 | draw +8.7 |
| Run, yd | | 29.7 | | 11.6 | draw about +20 | draw +18.1 |

Every difference has TrackMan's sign. The spin gap sits 5 percent under, the run-out gap matches, the landing angle gap is 3 degrees short and the height gap is 11 ft long. The absolute levels differ because the model driver is a Tour driver at 115 mph and TrackMan's is one R15 at an unstated speed. `tests/test_coupling.py::test_trackman_draw_fade_example` records these bounds. Where the previous model gave both shots the same run, the coupling supplies most of the 20 yd. The example does not say how much of the real gap came from face-to-path, so a smaller kappa would fit some rows better, and the model claims no more than direction and rough size.

**Recalibration of the axis scale c (the eight Anchor 5(b) examples, coupling on).** With the coupling on, the examples' spin lofts and carries move (a closed face flies longer and curves more, an open one shorter and less), and the shipped line c = 1.2177 - 0.008835 SL no longer fits: the least-squares refit of a line leaves the PGA 6 iron at -5 outside its tolerance (1.07). TrackMan's examples curve about the same per degree either way, and the coupled model is asymmetric, so a fit that minimizes the largest normalized error replaces the sum of squares. It gives one constant, c = 0.9986 (`axis_c1` is 0), worst error 0.90 of tolerance, rms 0.56, all eight inside. c near 1 also agrees with Tuxen's rules of thumb (axis 4 times face-to-path for a driver, 2 times for a 6 iron). Curvature (positive is right) with the 2019 rows' own spin trims:

| Example | F2P | Model carry | Model curve | Published | Error, yd | Fraction of tolerance |
|---|---|---|---|---|---|---|
| PGA driver | -2 | 272 | -17.2 | -19 | +1.8 | 0.47 |
| PGA driver | +5 | 258 | +38.8 | +44 | -5.2 | 0.59 |
| PGA 6 iron | +2 | 177 | +8.2 | +8 | +0.2 | 0.07 |
| PGA 6 iron | -5 | 183 | -23.6 | -20 | -3.6 | 0.90 |
| LPGA driver | +2 | 220 | +13.8 | +14 | -0.2 | 0.07 |
| LPGA driver | -5 | 194 | -28.7 | -32 | +3.3 | 0.52 |
| LPGA 6 iron | -2 | 148 | -5.6 | -6 | +0.4 | 0.13 |
| LPGA 6 iron | +5 | 138 | +11.3 | +14 | -2.7 | 0.90 |

The table is the model's own line at each example's F2P. The 2023 presets, which the article compares with TrackMan, curve 5.9 yd off the PGA 6 iron example at -5 (29 percent of its 20 yd), a wider gap than before the coupling (4.7 yd, 15 percent).

**What moved.** With face = path (no face-to-path), nothing moves: G3 (17 of 23), the presets, their spin trims, the ideal deliveries and bands, the golden fixtures for such deliveries and every known-miss record are unchanged (`--write-misses` reports no change). Things that changed: the curvature examples, the golfer cases, the nine windows (recipes keep the same targets and solve to different path, face and loft: draws fly lower and carry and total more than fades) and the golden vectors with a face-to-path. `golden_launch.json` is regenerated, and `golden.json`, `model.json` (`coupling`), `presets.json`, `windows.json` and `SCHEMA.md` are exported. `flight.js` ports `effectiveLoft` and `couplingKappa`, `deliver` returns `dynLoftInputDeg` and `dynLoftDeg`, and `METRIC_FIELDS.dyn_loft_deg` now points at the effective loft (`dyn_loft_input_deg` at the slider).

**Draw against fade, hook against slice, PGA (yd, rpm).** Draw is path +4 and face 0 (face-to-path -4), fade path -4 and face 0 (+4), pull hook path -2 and face -6 (-4), push slice path +2 and face +6 (+4). Straight is path 0, face 0.

| Club | Shot | Effective loft | Carry | Peak height | Spin | Total | Landing angle |
|---|---|---|---|---|---|---|---|
| Driver | Straight | 12.7 | 282.1 | 34.8 | 2,545 | 312.9 | 39.3 |
| Driver | Draw | 10.2 | 266.8 | 23.7 | 2,217 | 321.9 | 30.3 |
| Driver | Fade | 15.1 | 273.3 | 42.0 | 3,071 | 292.8 | 44.2 |
| Driver | Pull hook | 10.2 | 262.1 | 23.7 | 2,217 | 317.2 | 30.3 |
| Driver | Push slice | 15.1 | 268.5 | 42.0 | 3,071 | 288.1 | 44.2 |
| 7 iron | Straight | 23.4 | 171.7 | 36.6 | 7,124 | 178.5 | 49.1 |
| 7 iron | Draw | 21.3 | 176.5 | 34.2 | 6,619 | 184.6 | 47.4 |
| 7 iron | Fade | 25.4 | 164.4 | 37.4 | 7,782 | 170.5 | 50.0 |
| 7 iron | Pull hook | 21.3 | 174.2 | 34.2 | 6,619 | 182.3 | 47.4 |
| 7 iron | Push slice | 25.4 | 162.5 | 37.4 | 7,782 | 168.6 | 50.0 |

The PGA driver draw totals 29.1 yd more than the fade with 6.5 yd less carry (the delofted ball flies flat and runs), and the 7 iron draw carries 12.1 yd more and totals 14.1 more. The tests hold for all 12 clubs and 3 players: the draw carries a lower peak height and lands flatter, spins less and totals more than the fade, and the pull hook totals more than the push slice.

The five golfer cases on the PGA 7 iron preset, carry, curve, total (before the coupling in brackets): straight 171.7, 0.0, 178.5 (same); push draw (+5, +2) 175.9, -12.1, 183.7 (171.1, -10.9, 178.0); left, left (-3, -3) 171.4, 0.0, 178.3 (same); push slice (-3, +4) 157.1, +19.7, 162.8 (166.1, +24.2, 173.3); pull hook (+2, -4) 175.4, -25.3, 184.5 (167.3, -21.1, 174.3). Names and signs hold (Straight, Draw, Pull, Slice, Pull hook). The open face's added loft pulls the push slice case's start line in, from 1.997 to 1.955 degrees right, still inside TrackMan's 2 degree line, so it reads Slice as before (`test_classify.py` records the boundary).

**The honest limit.** Pure pulls and pure pushes at equal face-to-path stay equal in the model. Path 4 with face 4 and path -4 with face -4 have face-to-path 0, no loft change, and mirror to the last digit (`test_pure_pulls_and_pushes_stay_equal`). The coupling is about the difference between face and path, so it separates draws from fades and hooks from slices and cannot separate a pull from a push. The physics agrees on the carry (a straight pull and a straight push are mirror images in the D-plane, research file topic 1), and a TrackMan Master says a controlled draw and fade go the same distance while the real gap comes from the impact conditions that usually produce them. Anything that separates a pull from a push (a strike-location control, a dynamic lie) is out of scope here.

**Consequences.**
- The tool's draw and fade, and hook and slice, no longer share a distance, and the sizes rest on a MODELED kappa at the top of the geometric range. The slider `dyn_loft_deg` is the loft with the face square to the path and the loft tile shows the effective loft, which reads differently from the slider whenever face-to-path is not 0.
- On a closed driver face the curve grows to a peak and then falls: PGA driver, path 0, curve of -9.3, -27.0, -40.0, -43.7 and -45.0 yd at face-to-path -1, -3, -5, -6 and -7 degrees (the peak), then -44.0, -41.1, -36.6, -25.0 and -9.6 yd at -8, -9, -10, -12 and -15 as the axis passes 37 degrees and carry falls from 225 to 78 yd. The open side keeps rising (+41.8 yd at +5, +85.0 at +15, axis 32 degrees). The monotone-curve test is limited to 5 degrees.
- The spin axis scale c is now one constant near 1, and the earlier statement that c falls from 1.11 to 0.98 with spin loft (decision 4) no longer holds. The 2023 preset lines against TrackMan's examples show a worst gap of 29 percent (5.9 yd), so the article's statement of that gap needs the new number.

## Addendum 4 (2026-09-29, branch 004-physics): loft follows attack angle for irons, wedges, hybrids and fairway woods

**Problem.** The attack angle and dynamic loft sliders were independent. Hitting up at a fixed loft cut spin loft, so an iron gained carry, lost spin and gained smash. That contradicts the owner's claim, which the evidence supports for full swings: hitting up with an iron adds loft, loses compression and flies shorter. The Foresight 7 iron chart (Anchor 9) drops 21.7 yd at 100 mph and 13.9 yd at 90 mph going from attack -6 to +2, is near flat at 70 to 80 mph, and reverses at 60 mph. The cause is the loft that comes with the attack angle, not the upward motion alone (docs/sources/004_Physics_Research.md, topic 13).

**Decision.** `presets.loft_for_attack(club, player, attack)` gives the input dynamic loft when the loft follows the attack angle:

dyn_loft = preset dyn_loft + LOFT_PER_ATTACK x (attack - preset attack), LOFT_PER_ATTACK = 1.4

for the hybrid, both fairway woods, every iron and the PW (`data.LOFT_FOLLOWS_ATTACK_CLUBS`). MODELED. The result is held to at least attack + 1 degree (the spin loft floor) and at most 65 degrees, so `deliver` always accepts it, and it returns the preset loft at the preset attack. Evidence for 1.4 (`data.py` comment): a floor of 1.0 from arc geometry and TrackMan's rule that dynamic loft is static loft plus attack angle plus a shaft adjustment (Anchor 11), and Suzuki et al. 2021 (Anchor 10), whose within-player driver slopes are 0.85 for 42 professionals and 1.23 for 25 amateurs; the Foresight chart (Anchor 9) gives 1.25 to 1.73 from launch across head speeds (median about 1.4) and about 1.5 from spin. No source measures the slope for wedges, hybrids or fairway woods, so 1.4 there extends the 7 iron result. The range is 1.0 (pure arc) to about 1.5. The driver keeps the chart's optimal loft rule (`chart.optimal_loft` at the preset club speed, addendum 2), and `loft_for_attack("driver", ...)` returns it. `data.DRIVER_NATURAL_SLOPE` = 1.0 (the arc value, Suzuki's amateurs at 1.23 and professionals at 0.85 bracket it) is exported for the page's information only. The independent-slider path (fixed loft, moving attack angle) stays and behaves as before. Presets, their ideal deliveries and every band are unchanged: they sit at the preset attack, where the rule returns the preset loft. Non-driver attack bands stay downward. The slope is limited below the preset attack (the next paragraph).

**What it does.** Each degree of upward attack adds 0.4 degree of spin loft (loft rises 1.4, attack 1.0), about 115 rpm of spin and a loss of about 0.004 of smash for a Tour 7 iron, and launch rises about 1.3 degrees, so carry and total fall. Carry and total change per degree of attack from the preset attack to +3, coupling on (yd per degree, carry / total; preset attack in brackets):

| Club | PGA | LPGA | Amateur |
|---|---|---|---|
| 3-wood | -1.93 / -3.86 (-2.3) | +2.03 / -3.11 (-0.8) | -0.16 / -2.77 (-2.5) |
| 5-wood | -2.46 / -3.77 (-2.5) | -1.08 / -2.82 (-1.6) | -0.02 / -2.64 (-2.6) |
| Hybrid | -2.33 / -3.55 (-2.4) | -1.19 / -2.62 (-1.9) | -0.55 / -2.52 (-2.5) |
| 3 iron | -1.96 / -3.38 (-2.5) | -0.78 / -2.39 (-1.7) | -0.46 / -2.46 (-2.6) |
| 4 iron | -2.10 / -3.23 (-2.9) | -0.78 / -2.39 (-1.7) | -0.64 / -2.37 (-2.8) |
| 5 iron | -2.20 / -3.03 (-3.4) | -0.99 / -2.30 (-2.0) | -0.97 / -2.26 (-3.0) |
| 6 iron | -2.25 / -2.77 (-3.7) | -1.38 / -2.21 (-2.3) | -1.30 / -2.15 (-3.2) |
| 7 iron | -2.15 / -2.54 (-3.9) | -1.39 / -2.03 (-2.5) | -1.39 / -2.01 (-3.3) |
| 8 iron | -1.86 / -2.20 (-4.2) | -1.33 / -1.84 (-2.8) | -1.31 / -1.87 (-3.5) |
| 9 iron | -1.68 / -1.98 (-4.3) | -1.31 / -1.77 (-3.2) | -1.27 / -1.75 (-3.6) |
| PW | -1.54 / -1.81 (-4.7) | -1.13 / -1.55 (-3.2) | -1.17 / -1.58 (-3.9) |

Total falls for every club and player. Carry falls for every iron for the PGA and LPGA (the tests hold it for all eight irons, six sample attacks each) and for the PGA woods and hybrid. For slow players the long clubs sit near their carry peak, so carry is flat or rises a little from the preset (the LPGA 3-wood, +2.0 yd per degree, and the amateur 3-wood and 5-wood, about 0), and total still falls. The amateur 7 iron carry peaks at attack -5.5 (142.5 yd, flat from -6.5 to -4.5) over a scan from -8 to +6 and falls from 0 to +3 (before the steep-attack floor below it peaked at -6.5). The tests now hold carry over the whole -10 to +10 range and the launch at 3 degrees or more; the statement above that carry falls for every iron of every player holds from the preset attack up.

**Check against the Foresight chart** (a check, not a fit): the PGA 7 iron scaled to 90 mph loses 1.82 yd of carry per degree from attack -6 to +2 (171.2 yd to 156.7), against the chart's 1.7 (183.4 to 169.5 at 90 mph). The chart's absolute carry runs higher (its club and method are unknown, and the model's Tour 7 iron sits at spin loft 27 where its launch and spin fits stop at 26). The slope, not the absolute carry, is the transferable result. At 60 to 80 mph the chart's carry is flat or reversed, where the model still falls, about 1.4 yd per degree for the amateur 7 iron against about 0.5 in the chart at 80 mph. Foresight's slow-swing rows reward the higher descent angle a neutral or positive attack gives, which the model captures only in part.

**PGA 7 iron (92 mph, preset attack -3.9) and PGA 5-wood (106 mph, preset attack -2.5), coupling on, straight shots, carry / total in yd:**

| Attack | 7 iron loft | 7 iron carry / total | 7 iron smash, spin | 5-wood loft | 5-wood carry / total | 5-wood smash, spin |
|---|---|---|---|---|---|---|
| -6 | 20.4 | 174.8 / 183.2 | 1.369, 6,880 | 8.1 | 238.6 / 266.9 | 1.476, 3,850 |
| -3 | 24.6 | 170.1 / 176.4 | 1.357, 7,228 | 12.3 | 242.1 / 257.7 | 1.467, 4,254 |
| preset | 23.4 | 171.7 / 178.5 | 1.361, 7,124 | 13.0 | 241.7 / 256.1 | 1.465, 4,322 |
| 0 | 28.8 | 163.9 / 169.0 | 1.345, 7,573 | 16.5 | 237.4 / 247.3 | 1.457, 4,663 |
| +3 | 33.0 | 156.8 / 161.0 | 1.333, 7,914 | 20.7 | 228.2 / 235.3 | 1.447, 5,074 |

(The preset row sits between -6 and -3 for the 7 iron, at -3.9, and between -3 and 0 for the 5-wood, at -2.5.) The 5-wood's carry peaks near -3 (242.1) because delofting it a long way at -6 leaves 8 degrees of loft, launch 5.2 degrees and a low flight. Its total peaks at -6, where the low launch runs out.

**Consequences.**
- The lab has two ways to move attack angle: the independent slider (loft fixed, so hitting up cuts spin loft) and loft-follows-attack (`loft_for_attack`, hitting up adds loft). The tool chooses, and the choice is a teaching claim: with loft following, hitting up shortens an iron.
- The 1.4 slope is MODELED from one manufacturer chart with an unknown method plus the arc floor. The wedge, hybrid and fairway wood values are extension, and a slope of 1.0 gives carry changes of about -0.6 yd per degree for the PGA 7 iron.
- `model.json` carries `coupling.loft_per_attack`, `loft_per_attack_clubs` and `driver_natural_slope`, `flight.js` has `loftForAttack`, and `golden.json` carries 252 test vectors.

**Steep attack: the followed loft is floored (pre-merge review).** Run on below the preset attack, the 1.4 slope has evidence from -6 to +2 only, and it hit a cliff: the PGA 3-wood at -9 flew 213 yd with a 6 yd apex, at -10 it delivered 1.6 degrees of loft and launched at -0.7 degrees (carry 0), and the PGA 5-wood, hybrid, 3 iron and 4 iron and the amateur woods reached launches of 0 to 2 degrees at -9 to -10. A golfer can only lean the shaft so far. Below the preset attack the loft taken off now follows the 1.4 slope exactly for the first 3 degrees of deloft (`data.LOFT_FOLLOW_DELOFT_LINEAR`) and then rolls off to a limit of 5 degrees below the preset loft (`LOFT_FOLLOW_DELOFT_MAX`), with an exponential whose value and slope are continuous at the join, so there is no kink: loft change = 3 + 2 x (1 - exp(-(d - 3) / 2)) for a raw deloft d over 3 (MODELED, both numbers are design choices). Three degrees is the deloft the Foresight chart itself reaches for the 7 iron at attack -6 against a preset of -3.9, and 5 degrees is about the shaft lean coaches quote for an iron (a search snippet, not used as a value). The alternatives, a hard floor at max(preset loft - 5, attack + 8), would put a slope kink at 3.6 degrees below the preset attack, and the exponential keeps the loft rising with attack everywhere with steps that change by under 0.25 degree per half degree. Above the preset the slope runs on (nothing above +2 has evidence). `launch.clamp_loft` is the one clamp on an effective loft, and it now floors the loft at max(attack + 1, `DOMAIN["min_effective_loft_deg"]` = 1.0): a 3-wood at attack -10, path -8 and face -15 had delivered -3.0 degrees.

PGA carry / total (yd) after the fix, with the loft, launch and apex behind them, at attack -10 to -6 (preset attack and loft in the row heading):

| Club | -10 | -9 | -8 | -7 | -6 |
|---|---|---|---|---|---|
| 3-wood (-2.3, 12.4) | 240 / 262 (L 7.4, 3.5 deg, 23 yd) | 243 / 268 (7.5, 3.9, 23) | 246 / 274 (7.6, 4.2, 22) | 248 / 279 (7.7, 4.6, 22) | 251 / 283 (8.1, 5.1, 22) |
| 5-wood (-2.5, 13.0) | 226 / 243 (8.1, 4.0, 24) | 229 / 249 (8.1, 4.3, 24) | 233 / 254 (8.2, 4.7, 24) | 236 / 259 (8.4, 5.1, 24) | 239 / 262 (8.8, 5.7, 25) |
| Hybrid (-2.4, 13.7) | 213 / 230 (8.8, 4.4, 23) | 217 / 235 (8.8, 4.8, 23) | 220 / 240 (8.9, 5.1, 23) | 223 / 244 (9.1, 5.6, 23) | 226 / 248 (9.4, 6.1, 24) |
| 3 iron (-2.5, 13.9) | 208 / 228 (8.9, 4.5, 21) | 212 / 233 (9.0, 4.9, 21) | 215 / 237 (9.1, 5.3, 21) | 217 / 242 (9.3, 5.7, 21) | 220 / 245 (9.7, 6.3, 22) |

Across every club and player and attack -10 to +10 the launch stays at or above 3.5 degrees (the PGA 3-wood at -10), the apex at or above 10 yd (the LPGA 3-wood) and the carry above 88 yd (the amateur PW at +10, where the followed loft is 57 degrees), and the tests hold launch at least 3 degrees, apex at least 8 yd and carry over 50 yd. Carry now falls from the preset attack to +10 for every iron of every player, except that the 3 and 4 iron sit near their carry peak and gain under a yard in the first 2 to 3 degrees above the preset (recorded in the test). Below the preset, carry still slips a little as the attack steepens, because the limited deloft leaves spin loft growing (the PGA 3-wood loses 11 yd from -6 to -10), and total falls with it.
