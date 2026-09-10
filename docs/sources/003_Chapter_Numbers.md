# 003 Chapter Numbers -- number-by-number source ledger (issue #13)

Rebuilt from scratch for 003.8/9 after the mishit-mixture revs (rev 6, ADR
0003; rev 7, the GIR-anchored core and skewed mishit tail, ADR 0003's dated
addendum). Every number quoted in `site/augusta-12/index.html`'s chapters,
"The move," and "Method and sources" sections, with the exact source row it
traces to. Row keys for `outputs/003_moves.csv`, `outputs/003_results.csv`,
and `outputs/003_chapters.json` are `(tier, pin, wind)`; `wind` is
`False`/`0` unless stated. Percentages in the article are rounded to one
decimal from the chapters export's own four-decimal figures; stroke deltas
are rounded to three decimals, matching the CSV's own rounding.

## Chapter 1 -- The question

| Number in prose | Source |
|---|---|
| 155-yard shot | `data.TEE_SHOT_YD`, Anchor 3 |
| Scratch oval ≈18.3 × 7.3 yd | `model.oval_for_tier(0)` = (18.3166, 7.3267); `003_chapters.json` cell `0\|left\|0`.`sigma_d_calm_yd`/`sigma_l_calm_yd` |
| 20-handicap oval ≈32.9 × 13.1 yd | `model.oval_for_tier(20)` = (32.8505, 13.1402); cell `20\|left\|0`.`sigma_d_calm_yd`/`sigma_l_calm_yd` |
| "almost double" | derived, 32.8505/18.3166 = 1.79, 13.1402/7.3267 = 1.79 |
| Mishit rate 6.3% (scratch) to 31.3% (20-handicap) | `data.MISHIT_PCT` = `{0: 0.0625, 5: 0.10, 10: 0.15, 15: 0.225, 20: 0.3125}` |
| Mishit rate sensitivity range, 0.5x-1.5x multiplier | `data.MISHIT_PCT_SENSITIVITY_MULT_RANGE` = (0.5, 1.5) |
| Mishit short-distance fraction 25%, range 20% to 30% | `data.MISHIT_SHORT_FRAC` = 0.25; `data.MISHIT_SHORT_FRAC_RANGE` = (0.20, 0.30) |
| Mixture solved to reproduce each tier's own GIR rate at its own anchor distance | `data.solid_strike_sigma_iso_ft`; `docs/adr/0003-003-mishit-mixture.md`'s rev 7 addendum ("The fix") |
| 15/20-handicap ovals modeled | `data.py` module docstring / `data.SOURCES["SIGMA_ISO_FT"]` ("modeled/interpolated for 15/20") |
| Anisotropy 2.5-to-1, range 2:1 to 3.5:1 | `data.ANISOTROPY` = `{"ratio": 2.5, "range": (2.0, 3.5)}` |

## Chapter 2 -- Left pin

All rows: `outputs/003_moves.csv` `(tier, "left", False)`; water/short/green percentages: `outputs/003_chapters.json` cells `{tier}|left|0`.

| Tier | Aim (lat, carry) | Delta | Water pin→aim | Short pin | Green pin→aim |
|---|---|---|---|---|---|
| 0 | 4.0, 6.0 → "4.0 right, half a club long" | 0.0448 → 0.045 | 0.1151→0.1033 → 11.5%→10.3% | 0.1123 → 11.2% | 0.3085→0.4096 → 30.9%→41.0% |
| 10 | 3.812, 5.812 → "3.8 right, half a club long" | 0.0271 → 0.027 | 0.1239→0.1151 → 12.4%→11.5% | 0.2111 → 21.1% | 0.2319→0.2879 → 23.2%→28.8% |
| 15 | 5.5, 5.75 → "5.5 right, half a club long" | 0.0178 → 0.018 | 0.1196→0.1286 → 12.0%→12.9% | 0.262 → 26.2% | 0.2052→0.2722 → 20.5%→27.2% |
| 20 | 3.875, 9.812 → "3.9 right, one club long" | 0.0239 → 0.024 | 0.1273→0.1179 → 12.7%→11.8% | 0.3218 → 32.2% | 0.1662→0.214 → 16.6%→21.4% |

Club-language convention (used throughout): |carry| ≤ 2 yd → "same club"; 2–6 yd → "half a club"; 6–10 yd → "one club." Sign: positive carry = long/more club; negative = short/less club. Lateral sign: positive = right (Sunday side) of the pin; negative = left, per `data.py`'s "positive = right / Sunday side" convention. "Smallest edge of any tier at this pin" (15-handicap, 0.018) and "ticking back up" (20-handicap, 0.024): compared against the full four-delta set above (0.045, 0.027, 0.018, 0.024).

## Chapter 3 -- Center pin

All rows: `outputs/003_moves.csv` `(tier, "center", False)`; percentages: cells `{tier}|center|0`.

| Tier | Aim (lat, carry) | Delta | Water pin→aim | Short pin | Green pin→aim |
|---|---|---|---|---|---|
| 0 | -1.0, 4.0 → "1.0 left, half a club long" | 0.0243 → 0.024 | 0.1406→0.1081 → 14.1%→10.8% | 0.1423 → 14.2% | 0.4554→0.4619 → 45.5%→46.2% |
| 10 | -1.0, 4.0 → "1.0 left, half a club long" | 0.0129 → 0.013 | 0.1368→0.124 → 13.7%→12.4% | 0.2381 → 23.8% | 0.3222→0.3266 → 32.2%→32.7% |
| 15 | -2.0, 4.0 → "2.0 left, half a club long" | 0.0121 → 0.012 | 0.1258→0.1203 → 12.6%→12.0% | 0.2917 → 29.2% | 0.2758→0.2811 → 27.6%→28.1% |
| 20 | -0.938, 8.0 → "0.9 left, one club long" | 0.0177 → 0.018 | 0.1308→0.116 → 13.1%→11.6% | 0.3508 → 35.1% | 0.2084→0.233 → 20.8%→23.3% |

"The closest thing to a pure tossup on the whole hole" / "the smallest edge this piece finds anywhere" (15-handicap, 0.012): the minimum delta among every calm, narrated (tier, pin) cell in Chapters 2-4 (left 0.045/0.027/0.018/0.024; center 0.024/0.013/0.012/0.018; sunday 0.095/0.078/0.070/0.053). Front-third depth "≈10.5 yd (range 9 to 12)": `data.HOLE["front_third_depth_yd_range"]` = (9.0, 12.0), midpoint 10.5; also `003_chapters.json` `modeled` block, entry `front_third_depth_yd`.

## Chapter 4 -- Sunday pin

Full-shot rows: `outputs/003_moves.csv` `(tier, "sunday", False)`; percentages: cells `{tier}|sunday|0`. Strict-optimum layup figures: same CSV rows, `strict_carry_adjustment_yd` and `layup_edge_strokes` columns.

| Tier | Aim (lat, carry) | Delta | Water pin→aim | Short pin | Green pin→aim | Strict layup carry | Layup edge |
|---|---|---|---|---|---|---|---|
| 0 | -7.062, -4.75 → "7.1 left, half a club less" | 0.0948 → 0.095 | 0.1904→0.1471 → 19.0%→14.7% | 0.1565 → 15.7% | 0.342→0.4576 → 34.2%→45.8% | -4.75 (no edge) | 0.0 |
| 5 (band only, not a named step) | -7.0, -6.5 | 0.0851 | -- | -- | -- | -6.5 (no edge) | 0.0 |
| 10 | -7.0, -9.188 → "7.0 left, one club less" | 0.0777 → 0.078 | 0.1595→0.1505 → 16.0%→15.0% | 0.2573 → 25.7% | 0.2681→0.3199 → 26.8%→32.0% | -9.188 (no edge) | 0.0 |
| 15 | -7.75, -9.625 → "7.8 left, one club less" | 0.0696 → 0.070 | 0.1591→0.1467 → 15.9%→14.7% | 0.3048 → 30.5% | 0.2137→0.2779 → 21.4%→27.8% | -9.875 (no edge) | 0.0 |
| 20 | -8.0, -9.938 → "8.0 left, one club less" | 0.0529 → 0.053 | 0.137→0.1301 → 13.7%→13.0% | 0.3737 → 37.4% | 0.1765→0.2152 → 17.6%→21.5% | -11.5 | 0.002 |

Delta band "0.053 to 0.095 strokes": min/max of all five tiers' deltas (0.0948, 0.0851, 0.0777, 0.0696, 0.0529). "Scratch pays the most; a 20-handicap pays the least": same five deltas, ranked by tier. Layup-edge finding ("agrees with the published aim through the 15-handicap, edges 0.002 strokes deeper for a 20"): `layup_edge_strokes` column, tiers 0/5/10/15/20, sunday, calm (0.0, 0.0, 0.0, 0.0, 0.002).

### Owner's-finding paragraph (water rate by tier at the flag)

| Number | Source |
|---|---|
| Scratch 19.0% water at the flag, sunday, calm | cell `0\|sunday\|0`.`p_water_at_pin` = 0.1904 |
| 20-handicap 13.7% water at the flag, sunday, calm | cell `20\|sunday\|0`.`p_water_at_pin` = 0.137 |
| Creek band 10 to 24 yd short of the Sunday pin | derived from `data.CREEK_WIDTH_YD` + `data.BANK_ROLLBACK_YD` (14.0 yd band) positioned against the Sunday pin's own front-edge offset in `model._front_edge_yd`/`model.region_at` |
| Scratch 15.7% short of the creek, sunday, calm | cell `0\|sunday\|0`.`p_short_at_pin` = 0.1565 |
| 20-handicap 37.4% short of the creek, sunday, calm | cell `20\|sunday\|0`.`p_short_at_pin` = 0.3737 |
| 20-handicap total short-side 51.1% (13.7% + 37.4%) | derived, 0.137 + 0.3737 = 0.5107 |
| Scratch total short-side 34.7% (19.0% + 15.7%) | derived, 0.1904 + 0.1565 = 0.3469 |

## Chapter 5 -- Wind

| Number | Source |
|---|---|
| 15-handicap, Sunday, calm oval 27.5 × 11.0 yd | `003_chapters.json` cell `15\|sunday\|0`.`sigma_d_calm_yd`/`sigma_l_calm_yd` (27.4749/10.99) |
| Calm delta 0.070 | `outputs/003_moves.csv` `(15, "sunday", False)`.`delta_vs_at_pin_strokes` = 0.0696 |
| Windy oval 35.7 × 14.3 yd | cell `15\|sunday\|1`.`sigma_d_yd`/`sigma_l_yd` (35.7174/14.287) |
| Windy delta 0.049, label "either works" | `outputs/003_moves.csv` `(15, "sunday", True)`.`delta_vs_at_pin_strokes` = 0.0493, `verdict_label` = "either works" |
| Tossup threshold 0.05 | `optimizer.TOSSUP_THRESHOLD_STROKES` |
| Scratch left, wind: delta 0.059, label "bail" | `outputs/003_moves.csv` `(0, "left", True)`.`delta_vs_at_pin_strokes` = 0.0586, `verdict_label` = "bail" |
| Scratch center, wind: delta 0.053, label "bail" | `outputs/003_moves.csv` `(0, "center", True)`.`delta_vs_at_pin_strokes` = 0.0526, `verdict_label` = "bail" |
| Every tier 5-handicap and up stays "either works" at left/center in wind | `outputs/003_moves.csv`, `(5/10/15/20, "left"/"center", True)` rows, `verdict_label` column |
| Three windy Sunday cells read as a tossup at some sensitivity settings | `tests/test_optimizer.py::test_flip_set_runs_and_matches_golden_snapshot`, keys `(10, "sunday", True)`, `(15, "sunday", True)`, `(20, "sunday", True)` |
| Wind carry penalty 8 yd, range 4–12 | `data.WIND["carry_penalty_yd"]`/`["carry_penalty_range_yd"]` |
| Wind dispersion inflation 1.3x, range 1.15–1.5x | `data.WIND["dispersion_inflation"]`/`["dispersion_inflation_range"]` |
| ~20 mph gusts, 2019 final round | `docs/sources/003_Source_Log.md#anchor-6`, narrative anchor |

## Chapter 6 -- April 14, 2019

Unchanged from prior revs (no model-dependent numbers). The prose pass at 003.8/9 drops the Molinari hole-15 correction paragraph (the second, tree-deflected water ball, previously sourced to Anchor 4's "Discrepancy caught and resolved" paragraph) as process narration; the four hole-12 water balls stay.

| Fact | Source |
|---|---|
| Koepka (9-iron, drifted right, bank, rolled back), Poulter (8-iron, didn't carry), Molinari (tee shot into the bank, rolled back), Finau (water), all double bogey | `docs/sources/003_Source_Log.md#anchor-4` |
| ~20 mph gusts | Anchor 6 / Anchor 4 (PGATOUR.com retrospective) |
| 2019 scoring average 3.053 | `data.HOLE12_MODERN_AVG_BY_YEAR[2019]`, Anchor 4/Anchor 9 |
| 52 birdies / 200 pars / 38 bogeys / 14 double-or-worse of 304 | `data.HOLE12_OUTCOMES_BY_YEAR[2019]`, Anchor 4 |

## Chapter 7 -- Does the model know this hole?

| Number | Source |
|---|---|
| Tour oval 8.4 × 5.4 yd at the 155-yd shot | `tour.tour_oval()` = (8.4412, 5.4459); unchanged this pass (Tour tier decoupled from the amateur retune, its own pro anisotropy ratio); Anchor 7 |
| Model Tour season mean 3.1142 | `tour.tour_season_analytic_mean()` = 3.114220...; `VALIDATION_NOTES.md`, "GIR-anchored core and skewed mishit tail (rev 7)" → "Gate numbers" |
| Modern-era band 3.053–3.233, mean 3.132, sd ≈0.073 | `data.HOLE12_MODERN_AVG_BY_YEAR` (six years), Anchor 9; unchanged (published data, not model-dependent) |
| All-time scoring average 3.27–3.28 | `data.HOLE12_ALLTIME_AVG_RANGE`, Anchor 4 |
| 2016-2023 Tour proximity data underlying the oval | Anchor 7 |
| Bar chart years 2019, 2021, 2022, 2023, 2024, 2025 (2020 not played, no usable figure) | `data.HOLE12_MODERN_AVG_BY_YEAR`, Anchor 9 |
| All-time average spans 1934-2025 | ADR 0002 ("The all-time figure spans 1934-2025") |
| "~90-year average" | derived, 2025-1934 = 91, rounded |
| Anchor 1's 125-149 yard proximity band | `docs/sources/003_Source_Log.md#anchor-1` |
| Anchor 7's 150-175 yard Tour proximity band | `docs/sources/003_Source_Log.md#anchor-7` |
| Broadie, Science and Golf V, 2008 | `docs/sources/003_Source_Log.md#anchor-2` (citation year) |
| 300,000-run Monte Carlo harness | `VALIDATION_NOTES.md`, "Gate 1: MC-vs-analytic fidelity" table |
| Bogey bucket gap ≈5.7 points, 2019 | `VALIDATION_NOTES.md`, "Creek band fix (rev 4)" → 2019 bucket table; unchanged this pass, Tour surface did not move |
| Bogey bucket gap ≈3.3 points, 2025 | `VALIDATION_NOTES.md`, "Pitch-over-water risk (rev 5)" → per-year shape gates; unchanged this pass |
| 2019 and 2023 published averages 3.053 and 3.058 below the calm-air floor | `data.HOLE12_MODERN_AVG_BY_YEAR` (Anchor 9); `VALIDATION_NOTES.md` per-year table (structural misses); unchanged this pass |
| Bogey bucket gap ≈6.6 points, 2024 | `VALIDATION_NOTES.md`, "Pitch-over-water risk (rev 5)" → "Per-year shape gates"; unchanged this pass |

## Chapter 8 -- The move

Restates Chapters 2, 3, and 4's own numbers verbatim, plus the short-of-the-creek figure alongside each water-at-the-flag number; see those sections above for the row-by-row source. No new figures introduced.

## Chapter 9 -- Try your own aim

No quoted numbers (CTA card only).

## Chapter 10 -- Method and sources

| Number | Source |
|---|---|
| Anisotropy 2.5, range 2.0–3.5 | `data.ANISOTROPY` |
| Mishit-tail rate 6.3% to 31.3% by tier, range 0.5x–1.5x | `data.MISHIT_PCT`, `data.MISHIT_PCT_SENSITIVITY_MULT_RANGE` |
| Mishit-tail short-distance fraction 25%, range 20%–30% | `data.MISHIT_SHORT_FRAC`, `data.MISHIT_SHORT_FRAC_RANGE` |
| Green width 25.5 yd (midpoint), range 16–35 | `data.HOLE["green_width_yd_range"]`; unchanged this pass |
| Green depth 26.5 yd (midpoint), range 20–33 | `data.HOLE["green_depth_yd_range"]`; unchanged this pass |
| Front-third depth 10.5 yd (midpoint), range 9–12 | `data.HOLE["front_third_depth_yd_range"]`; unchanged this pass |
| Creek width + bank rollback 14.0 yd, range 9–20 | `data.CREEK_WIDTH_YD` (6.0, range 4–8) + `data.BANK_ROLLBACK_YD` (8.0, range 5–12) = 14.0, range 9–20 |
| Wind carry penalty 8 yd, range 4–12 | `data.WIND` (as above); unchanged this pass |
| Wind dispersion inflation 1.3x, range 1.15–1.5x | `data.WIND` (as above); unchanged this pass |
| Up-and-down rate 30% to 54% by tier, sensitivity range 0.8x to 1.2x | `data.UP_AND_DOWN_PCT` (0.30 at tier 20 to 0.54 at tier 0); `data.UP_AND_DOWN_PCT_RANGE_MULT`; unchanged this pass |
| Up-and-down sweep flips no pin's label at any tier | `tests/test_montecarlo.py::test_up_and_down_pct_sensitivity_on_amateur_verdicts`; unchanged this pass (independent of the mishit mixture) |
| Pitch-over-water dunk rate 2% to 12% by tier | `data.PITCH_OVER_WATER_DUNK_PCT` (0.02 at tier 0 to 0.12 at tier 20); unchanged this pass |
| Flip set: Sunday reads "bail" at the sweep's own baseline everywhere | `optimizer.flip_set()`; `tests/test_optimizer.py::test_flip_set_baseline_labels_sunday_always_bail_left_and_center_are_the_tossup_pins` |
| Flip set golden snapshot, 7 cells | `tests/test_optimizer.py::test_flip_set_runs_and_matches_golden_snapshot`; keys `(0,"left",False)`, `(0,"center",True)`, `(5,"left",False)`, `(5,"left",True)`, `(10,"sunday",True)`, `(15,"sunday",True)`, `(20,"sunday",True)` |
| Scratch left pin: baseline "bail", flips to "either works" at anisotropy 2.0/front-third 12.0 | same test, `flipped_at` for key `(0,"left",False)` |
| Scratch center pin: baseline "bail" (wind), flips to "either works" at anisotropy 3.5/front-third 12.0 | same test, `flipped_at` for key `(0,"center",True)` |
| 5-handicap left pin: baseline "either works", flips to "bail" at anisotropy 3.5 (front-third 9.0 calm; 9.0 and 12.0 in wind) | same test, `flipped_at` for keys `(5,"left",False)`/`(5,"left",True)` |
| Sunday windy flips: tier 10 at anisotropy 2.0/front-third 12.0; tier 15 at all three of (2.0,12.0)/(3.5,9.0)/(3.5,12.0); tier 20 at (3.5,9.0)/(3.5,12.0) | same test, `flipped_at` for keys `(10,"sunday",True)`, `(15,"sunday",True)`, `(20,"sunday",True)` |
| Broadie's own published ratio 3-to-1; this release's default 2.5-to-1 | `docs/adr/0003-003-mishit-mixture.md`'s rev 7 addendum ("Chosen values": `ANISOTROPY["ratio"]` 3.0 -> 2.5) |
| MC fidelity: amateur 0.012, Tour 0.011, tolerance 0.03 | `VALIDATION_NOTES.md`, "GIR-anchored core and skewed mishit tail (rev 7)" → "Gate numbers" ("amateur worst gap 0.0115 stroke, Tour worst gap 0.0107 stroke") |

## Reading time and word count

Article body (chapters through method and sources, excluding the dek and
byline): 3,783 words (down from 3,852 after the 003.8/9 Sepia and Humanizer
prose pass, which trims the "'s own" overuse throughout, drops the
Molinari hole-15 correction paragraph and other process narration, and
otherwise reworks wording only, no figures touched). At 200 words/minute
(002's own convention), that rounds up to 19 minutes, the figure the
byline states.
