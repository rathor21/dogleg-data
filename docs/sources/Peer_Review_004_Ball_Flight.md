# Peer Review

**Work reviewed:** Face, Path, and the Ball Flight Laws, in Numbers, and the Ball flight lab (release 004, issues #19 to #31): `analysis/004-ball-flight-laws/` (`flight.py`, `launch.py`, `launch_tools.py`, `calibrate.py`, `calibrate_launch.py`, `gates.py`, `gates_launch.py`, `classify.py`, `windows.py`, `ideals.py`, `presets.py`, `export.py`, `tests/`), ADR 0004, `docs/sources/004_Source_Log.md`, `docs/sources/004_Caption.md`, `analysis/004-ball-flight-laws/art/README.md`, `site/ball-flight/` (page, lab, JS port, data JSON, tests).
**Author:** Claude, direction by Sunny
**Reviewer:** Claude (per-task review passes plus a final read, part of issue #31)
**Review type:** Full (sources, model, gates, JS parity, numbers, art, copy)
**Date:** 2026-09-29

---

## Context

**Question:** can a golf instructor move club path, face angle, attack angle, club speed and dynamic loft, watch a tracer fly over a range, and trust that the shot name and every number on screen follow published data, with each modeled number labeled.

**Method:** read the design spec (`docs/plans/2026-09-28-004-ball-flight-laws-design.md`), the source log, ADR 0004, both known-miss files, the art README and the article ledger. Ran the full suite from `analysis/004-ball-flight-laws`, the JS parity harness and the article drift test on the final tree.

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | 544 passed, 38 xfailed, 0 failed (582 collected) |
| `node site/ball-flight/tests/parity.mjs` | PARITY OK: 40 golden cases, 560 classify vectors, 9 windows, 16,783 checks, 0 failed |
| `node site/ball-flight/tests/article-numbers.mjs` | ok, 98 numbers match (two ledger keys unused, tm-ratio-pga and tm-ratio-lpga) |
| `export.py` rerun | `site/ball-flight/data/*.json` byte-identical, art published as `.jpg` |

The 38 xfails break down as 17 (G2 original tolerance) + 11 (G2 teaching tolerance) + 6 (G3 Tour rows) + 2 (amateur preset rows) + 1 (spin loft at the published LPGA driver loft) + 1 (short-shot curve order). Every one is a recorded miss. `test_no_new_or_worse_misses` and the strict xfail ratchet fail a new miss or a recorded component that grows by more than 0.15.

---

## Review rounds (from git history, `c825bc9..HEAD`)

| Task | Commit | What the review pass found and fixed |
|---|---|---|
| 004.1 | b7276e5 | Source log for G1. Seven anchors, each with a verdict. |
| 004 | 77eb88e | Design spec. Sunny picked round 1 art r1_5. |
| 004.2 | 728421f, fad9be2, af456a2, d6023a7 | Flight model fitted to both Tour tables. Three variants compared on held-out data, quad7 with the published spin decay shipped. |
| 004.2 review | da9bd84 | Variants moved out of `flight.py`, input contract added, gate scoring moved to `gates.py`, ratchet added on the known-miss record. |
| 004.6 | 735eecc, 2dc2baf | Round 2 art from r1_8 and a pinhole fit (superseded), then the fitted 2.5D art camera with per-group views. |
| 004.3 | 8406778, a92d213, 8bc178e, 1da750e | Delivery-to-launch model, G3 and G4, ADR 0004. Club-class spin factor for woods, per-preset spin trim, axis scale refit, then the driver recalibrated to the TrackMan 2010 chart. |
| 004.3 review | 756a0f2 | Input domain enforced (`data.DOMAIN`), keyword-only API, `gates_launch.py`, ratchet on live floors, golden vectors for the JS port. |
| 004.4 | 6ac19cc, b900769 | Finish-aware shot names, nine windows, ideal bands, site data export. |
| 004.4 review | 5319ce7 | Portable classifier, one JSON vocabulary, `SCHEMA.md`. |
| 004.5 | 894b7ad | `flight.js` port with a Python parity test. |
| 004.5 review | fa1f059 | Module-relative data path, defensive copies, `metricValue`, ideals fixture. |
| 004.7-8 | 381fa8c | Tool shell, tiles, URL state, range tracer. |
| 004.7-8 review | 5e0d46b | Partial links, accessibility, touch targets, landscape drawer, art loading, module split. |
| 004.9 | 09d342b | Top, side and impact views, 9 Windows, Compare, presentation mode. |
| 004.9 review | 8a0b302 | Camera on sequences, ghost in views, presentation sizing, deltas, accessibility. |
| 004.11 | 11cf858, 43f8a21 | Article draft with live figures, then a refresh for the calibrated driver model with accuracy and prose fixes. |
| 004.12 | 230e759, da11062 | Art published as JPEG, nav, home, sitemap, `llms.txt` and cite wiring, this document. |

---

## Validation gates

**G1, sources.** Passed with recorded gaps. Anchors 1 and 2 (TrackMan PGA and LPGA Tour tables) and Anchor 4 for the driver (TrackMan 2010, PING 2019) are ANCHORED. Anchor 3 (amateur) is PARTIAL: the driver has a measured Combine column, the 6-iron and PW are TrackMan Optimizer defaults (model output), every other amateur club is MODELED. Anchor 5 (ball flight laws) is PARTIAL: TrackMan's definitions, the launch direction geometry and eight worked curvature examples are logged. The start direction shares, D-plane equations and a per-degree curve law have no primary text. Anchor 6 (Tiger's nine windows) is ANCHORED for the concept and NOT FOUND for numbers, so the windows carry the `modeled` badge and no Tiger attribution. Anchor 7 (aerodynamics) is PARTIAL: Nathan's workbook and the spin decay law are read, the Smits and Smith equations are not. Pages that refused a fetch (MyGolfSpy, Golf Digest, GolfWRX, TrackMan help center, ResearchGate and others) were not worked around.

**G2, flight.** The original tolerance (carry 3 percent, height 3 yd, land angle 2 degrees) fails: quad7 passes 6 of 23 rows. ADR 0004 retargets G2 to the teaching tolerance (5 percent, 4 yd, 3 degrees), which quad7 passes on 12 of 23 rows. Rms by component, in units of the original tolerance: carry 0.81, height 0.95, land angle 1.24. The original tolerance stays as a reported metric.

**G3, launch.** Launch passes on all 23 rows by construction, because dynamic loft is inverted from launch. Spin and ball speed are the working tests, and 17 of 23 rows pass all three. Every Tour and anchored amateur preset reproduces its published spin within 1 percent through its spin trim.

**G4, physics.** Passes: face equal to path gives zero curve, mirrored inputs mirror the flight, curve rises with face-to-path, and the five golfer cases (straight, push draw, both left, push slice, pull hook) hold in `test_launch.py`. One flight-model check is a recorded xfail: at the same spin axis a 6-iron curves more than a 3-wood (14.0 against 12.1 yd), the wrong order against TrackMan's examples (15 against 11 yd). The scale on the spin axis absorbs it in the delivery model.

---

## Model decisions and rejected alternatives

| Decision | Choice | Rejected | Why |
|---|---|---|---|
| Flight model | quad7: quadratic lift and drag, 7 coefficients fitted to all 23 rows, shared by every club and both tours | Nathan's power law forms | Fitted to the Tour rows with the Reynolds branch on, Nathan passes 0 of 23 rows (rms 5.4). Holding Cd0 flat passes 3 of 23 (rms 1.3) and needs a 2.3x lift multiplier. Nathan's workbook stays reproducible in `baselines.py`, and the port matches his default shot at 259.0 yd against 259.3. |
| Spin decay | Published rate, k = 2.0e-5 SI (Smits and Smith) | Variant A: decay fitted with quad7 | The fitted k landed on the 6.0e-5 bound of its search range, three times the published value, for a held-out gain of 0.04 that sits inside the noise. |
| Drag shape | quad7 | Variant B: logistic low-Re drag plus fitted k | B passes the most rows (8 of 23 and 14 teaching) and transfers worst from PGA to LPGA (1.521 against 0.989). |
| Driver launch and spin | Own k line and spin law (1.3352 x ball speed x SL^1.0410) fitted to the TrackMan 2010 chart and the two published driver rows | The iron k line and spin law | They extrapolated below spin loft 12.7: at +6 attack the model read 1,086 rpm and ran 23 percent under the chart. Against the 60 chart rows the new law gives launch rms 0.22 degrees, spin rms 0.76 percent, ball speed rms 0.77 percent (in-sample). |
| Preset spin | Per-preset `spin_trim` (35 trims, all inside 0.6 to 1.6) | A per-club or per-tour factor in the model | Keeps the model free of per-club terms. The trim holds where each group strikes the face, and the model supplies only the response to delivery changes. |
| Curvature | Spin axis scale c linear in spin loft, c = 1.2177 - 0.008835 SL | Constant c = 1.046 | Worst error of the eight TrackMan examples falls from 0.64 to 0.39 of tolerance. |
| Start direction shares | Follow from the fitted k and lofts: 82.7 percent (PGA driver), 72.9 (PGA 6-iron) | The 85/75 and 87/81 figures as inputs | Neither pair traces to a TrackMan text. The article states this. |

---

## Known misses

Read from `tests/g2_known_misses.json`, `tests/g3_known_misses.json` and ADR 0004.

**G2, misses the teaching tolerance (11 rows):** PGA driver land angle +3.4 deg; PGA 3-wood height +4.6 yd; PGA 5-wood height +5.1; PGA hybrid height +5.1 and land angle -3.0; PGA 3-iron land angle -3.7; PGA 4-iron -4.2; PGA 5-iron -4.1; PGA 6-iron height +4.5; PGA PW carry -8.5 yd; LPGA 3-wood height -4.2 yd and land angle -4.4; LPGA 5-iron land angle -3.4.

**G2, misses only the original tolerance (6 rows):** PGA 7-iron carry -5.6 yd, PGA 9-iron land angle -2.5, LPGA driver carry -7.3, LPGA hybrid height +3.6, LPGA 4-iron carry -6.6, LPGA PW height -3.6 and land angle -2.0. Two patterns: the PGA 3-wood, 5-wood, hybrid and 6-iron run 4.5 to 5.1 yd high, and the PGA 3 to 5 irons land 3.7 to 4.2 degrees shallower than the table. One shared coefficient set cannot match both tours and every club.

**G3, misses (6 Tour rows plus one published check):** PGA driver spin +35.0 percent (model 3,436 rpm, table 2,545); PGA 5-wood spin -11.9; LPGA 3-wood spin +30.2; LPGA 5-wood spin -10.7; LPGA hybrid spin +12.2; LPGA 8-iron ball speed -2.3 percent. At the published LPGA driver dynamic loft the spin loft reads 12.7 against 15.0 (-2.3 degrees, unexplained in the log). The PGA driver miss is the model's own TrackMan-2010 output against a Tour average that spins about 26 percent less. Above-center strikes would do that and the log cannot confirm it.

**Preset rows that miss launch or ball speed:** amateur driver ball speed +2.78 percent and amateur 6-iron launch -1.28 degrees.

**Curvature:** all eight TrackMan examples sit inside the larger of 20 percent and 3 yd, worst at 0.39 of tolerance, rms 0.28. The model runs 2 to 8 percent short of the carries those examples quote, and it is symmetric where the published driver examples are not (9.5 against 8.8 yd per degree).

**Extrapolation:** driver spin below spin loft 6.3 (attack above about +6 at Tour loft) has no supporting row. The lab allows +10, where the PGA preset reads about 470 rpm.

---

## Art camera decision

The accepted range painting (r1_8, edited, 1376x768 wide and 768x1376 portrait, both generated with nano-banana) is not perspective-consistent. A pinhole fit from the poles, center line and ball anchor (RMS 1.06 px wide, 1.81 px portrait) squeezes 50 to 300 yd into about 20 px, because the stripe edges converge toward a vanishing row near 340 to 390 while the poles say 301. Commit 2dc2baf replaces it with a fitted 2.5D mapping: the ground row curve follows the painting's own greens, and `z_eff` sets the vertical scale. The wide image needs one zoom rectangle per club group, since no single `z_eff` fits both the driver arc and the wedge. The pinhole fit stays in `art/` as the documented baseline. The image resolution limit (nano-banana returns 1376x768 for 16:9 whatever the prompt asks) is recorded in the art README. The published files hold JPEG data and now carry the `.jpg` extension.

---

## JS parity evidence

`node site/ball-flight/tests/parity.mjs`, final tree:

| Category | Checks | Failed | Max deviation |
|---|---|---|---|
| deliver | 320 | 0 | 7.88e-9 |
| flight | 360 | 0 | 8.10e-7 |
| classify (cases) | 237 | 0 | 7.44e-8 |
| trajectory | 2,948 | 0 | 6.05e-7 |
| classify (vectors) | 3,360 | 0 | none |
| windows | 207 | 0 | 5.03e-7 |
| presets | 612 | 0 | 6.23e-4 |
| ideal bands | 4,536 | 0 | 7.22e-6 |
| ideal bands (fixture) | 3,347 | 0 | 4.94e-6 |
| metricValue | 251 | 0 | 2.80e-6 |
| invalid input, domain edges, clampToDomain, helpers, copies, loadModel | 65, 12, 507, 6, 9, 6 | 0 | 3.49e-6 (loadModel) |

Total 16,783 checks, 0 failed. `shot()` averages 0.087 ms over 2,000 PGA driver runs against a 2 ms budget. The presets row deviates by 6.23e-4 on `amateur.4i.carry_yd`, inside the 0.05 the harness allows for preset flight values.

---

## Numbers discipline

Every model number in the article prose sits in a `data-num` span that `article.js` fills from the live model through `article-numbers.js`. `tests/article-numbers.mjs` fails when a fallback drifts from the model. It passes on 98 numbers. Published numbers (TrackMan, PING) are plain text and their ledger is `docs/sources/004_Caption.md`. Model numbers carry the `modeled` badge in each figure caption and at first use in each chapter.

---

## Copy

Prose went through the house rules (no em dashes, no -ly adverbs, no "not X, it's Y"). The article discloses the model share of start direction (83 percent driver, 73 percent 6-iron) beside the 85/75 and 87/81 figures it could not trace, and names TrackMan and PING pages for every published number.

---

## Open items for Sunny

1. **Accept ADR 0004.** Status is proposed. It retargets G2 to the teaching tolerance and ships the misses above as documented xfails. Merging the PR is the acceptance.
2. **Preset launch trim.** Decide whether the three current misses need a trim like the spin trim: the amateur 6-iron launch miss (-1.28 degrees) and the two ball-speed misses (amateur driver +2.78 percent, LPGA 8-iron -2.3 percent).
3. **Tuxen paper unread.** "TRACKMAN Ball Flight Laws" (Anchor 5a) has not been read by a human. It may change the start direction shares and the D-plane equations. The article states shares from the model, and a table in the paper could move them.
4. **TaylorMade video unwatched.** The nine-windows concept rests on the Tiger and TaylorMade 2021 material, which was cited from text and never watched. The window recipes are model output and carry no Tiger attribution.
5. **Justin Kraft credit.** The article holds a comment where the credit goes. It stays out until Justin consents. Issue #29 (his private preview) stays open.
6. **Publish date.** The page and metadata read September 29, 2026. Change both if the release date moves.
7. **Real-device and Safari testing.** Browser QA ran in Chrome under emulation. Safari, an iPhone and an iPad at the range still need a pass, including touch on the tracer, the 9 Windows tap and the landscape drawer.
8. **Hero art rights.** Range art is generated, with no photographic reference. Confirm you accept it as the page image.

**Reviewer sign-off:** Claude, 2026-09-29. Tests, parity and the article drift test pass on the final tree. Sunny's decisions above stand before publish.
