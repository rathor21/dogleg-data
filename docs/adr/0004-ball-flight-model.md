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
The face-to-path to curve mapping is what students see, so it follows TrackMan's eight examples (Anchor 5b) and not the flight model's own curve per degree of spin axis. `flight.py` gives a 6 iron more curve than a 3-wood at the same axis (14.0 against 12.1 yd at 10 degrees), the wrong order against TrackMan's 11 and 15 yd, and `test_flight.py` records that as an xfail. That over-curve of short irons per degree of axis is a known limit of the flight model. The scale c on the spin axis absorbs it.

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
