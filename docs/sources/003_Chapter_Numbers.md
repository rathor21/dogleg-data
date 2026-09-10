# 003 Chapter Numbers -- number-by-number source ledger (issue #13)

Every number quoted in `site/augusta-12/index.html`'s chapters, "The move," and
"Method and sources" sections, with the exact source row it traces to. Row
keys for `outputs/003_moves.csv` and `outputs/003_chapters.json` are
`(tier, pin, wind)`; `wind` is `False`/`0` unless stated. Percentages in the
article are rounded to one decimal from the chapters export's own
four-decimal figures; stroke deltas are rounded to three decimals, matching
the CSV's own rounding.

## Chapter 1 -- The question

| Number in prose | Source |
|---|---|
| 155-yard shot | `data.TEE_SHOT_YD`, Anchor 3 |
| Scratch oval ≈18.7 × 6.2 yd | `model.oval_for_tier(0)`; `003_chapters.json` cells `0\|left\|0`.`sigma_d_calm_yd`/`sigma_l_calm_yd` (18.7153/6.2384) |
| 20-handicap oval ≈33.6 × 11.2 yd | `model.oval_for_tier(20)`; cells `20\|left\|0`.`sigma_d_calm_yd`/`sigma_l_calm_yd` (33.5729/11.1910) |
| "nearly double" | derived, 33.5729/18.7153 = 1.79, 11.1910/6.2384 = 1.79 |
| 15/20-handicap ovals modeled | `data.py` module docstring / `data.SOURCES["SIGMA_ISO_FT"]` ("modeled/interpolated for 15/20") |
| Anisotropy 3-to-1, range 2:1 to 3.5:1 | `data.ANISOTROPY` |

## Chapter 2 -- Left pin

All rows: `outputs/003_moves.csv` `(tier, "left", False)`; water/green percentages: `outputs/003_chapters.json` cells `{tier}|left|0`.

| Tier | Aim (lat, carry) | Delta | Water pin→aim | Green pin→aim |
|---|---|---|---|---|
| 0 | 3.938, 5.438 → "3.9 right, half club long" | 0.0468 → 0.047 | 0.0778→0.0597 → 7.8%→6.0% | 0.3452→0.4494 → 34.5%→44.9% |
| 10 | 4.5, 2.812 → "4.5 right, half club long" | 0.0310 → 0.031 | 0.0653→0.0684 → 6.5%→6.8% | 0.2437→0.3133 → 24.4%→31.3% |
| 15 | 3.5, 2.75 → "3.5 right, half club long" | 0.0226 → 0.023 | 0.0711→0.0664 → 7.1%→6.6% | 0.2113→0.2572 → 21.1%→25.7% |
| 20 | 4.0, -2.0 → "4 right, same club" | 0.0140 → 0.014 | 0.0677→0.0661 → 6.8%→6.6% | 0.1814→0.2106 → 18.1%→21.1% |

Club-language convention (used throughout): |carry| ≤ 2 yd → "same club"; 2–6 yd → "half a club"; 6–10 yd → "one club." Sign: positive carry = long/more club; negative = short/less club. Lateral sign: positive = right (Sunday side) of the pin; negative = left, per `data.py`'s "positive = right / Sunday side" convention.

## Chapter 3 -- Center pin

All rows: `outputs/003_moves.csv` `(tier, "center", False)`; percentages: cells `{tier}|center|0`.

| Tier | Aim (lat, carry) | Delta | Water pin→aim | Green pin→aim |
|---|---|---|---|---|
| 0 | -1.438, 1.0 → "1.4 left, same club" | 0.0127 → 0.013 | 0.0797→0.0696 → 8.0%→7.0% | 0.4763→0.4780 → 47.6%→47.8% |
| 10 | -1.375, 0.5 → "1.4 left, same club" | 0.0147 → 0.015 | 0.0758→0.0558 → 7.6%→5.6% | 0.3412→0.3391 → 34.1%→33.9% |
| 15 | 0.0, -4.0 → "dead on the line, half club less" | 0.0060 → 0.006 | 0.0783→0.0823 → 7.8%→8.2% | 0.2809→0.2774 → 28.1%→27.7% |
| 20 | -1.0, -1.0 → "1 left, same club" | 0.0021 → 0.002 | 0.0677→0.0619 → 6.8%→6.2% | 0.2216→0.2323 → 22.2%→23.2% |

Front-third depth "≈10.5 yd (range 9 to 12)": `data.HOLE["front_third_depth_yd_range"]` = (9.0, 12.0), midpoint 10.5; also `003_chapters.json` `modeled` block, entry `front_third_depth_yd`.

## Chapter 4 -- Sunday pin

Full-shot rows: `outputs/003_moves.csv` `(tier, "sunday", False)`; percentages: cells `{tier}|sunday|0`. Strict-optimum layup figures: same CSV rows, `strict_carry_adjustment_yd` and `layup_edge_strokes` columns.

| Tier | Aim (lat, carry) | Delta | Water pin→aim | Green pin→aim | Strict layup carry | Layup edge |
|---|---|---|---|---|---|---|
| 0 | -7.0, -8.0 → "7 left, one club less" | 0.0932 → 0.093 | 0.1287→0.0975 → 12.9%→9.8% | 0.3945→0.4600 → 39.5%→46.0% | -6.875 (inside window) | 0.0 |
| 5 (band only, not a named step) | -5.625, -9.812 | 0.0858 | -- | -- | -7.875 | 0.0022 |
| 10 | -7.938, -9.938 → "8 left, one club less" | 0.0928 → 0.093 | 0.1016→0.0841 → 10.2%→8.4% | 0.2751→0.3444 → 27.5%→34.4% | -13.438 → "13.4 yd" | 0.0107 → 0.011 |
| 15 | -5.0, -10.0 → "5 left, one club less" | 0.0817 → 0.082 | 0.0958→0.0750 → 9.6%→7.5% | 0.2381→0.2806 → 23.8%→28.1% | -17.0 → "17.0 yd" | 0.0144 → 0.014 |
| 20 | -5.562, -10.0 → "5.6 left, one club less" | 0.0727 → 0.073 | 0.0847→0.0806 → 8.5%→8.1% | 0.1801→0.2252 → 18.0%→22.5% | -26.875 → "26.9 yd" | 0.0317 → 0.032 |

Delta band "0.073 to 0.093 strokes": min/max of the four listed deltas (0.0727, 0.0932). Layup-edge gradient "nothing extra for scratch or the 5-handicap, 0.011 for a 10, 0.014 for a 15, 0.032 for a 20": `layup_edge_strokes` column, tiers 0/5/10/15/20, sunday, calm (0.0, 0.0022, 0.0107, 0.0144, 0.0317).

## Chapter 5 -- Wind

| Number | Source |
|---|---|
| 15-handicap, Sunday, calm oval 28.1 × 9.4 yd | `003_chapters.json` cell `15\|sunday\|0`.`sigma_d_calm_yd`/`sigma_l_calm_yd` (28.0729/9.3576) |
| Calm delta 0.082 | `outputs/003_moves.csv` `(15, "sunday", False)`.`delta_vs_at_pin_strokes` = 0.0817 |
| Windy oval 36.5 × 12.2 yd | cell `15\|sunday\|1`.`sigma_d_yd`/`sigma_l_yd` (36.4948/12.1649) |
| Windy delta 0.057 | `outputs/003_moves.csv` `(15, "sunday", True)`.`delta_vs_at_pin_strokes` = 0.0565 |
| Wind carry penalty 8 yd, range 4–12 | `data.WIND["carry_penalty_yd"]`/`["carry_penalty_range_yd"]` |
| Wind dispersion inflation 1.3x, range 1.15–1.5x | `data.WIND["dispersion_inflation"]`/`["dispersion_inflation_range"]` |
| Every left/center row reads "either works" in wind too | `outputs/003_moves.csv`, all `(tier, "left"/"center", True)` rows, `verdict_label` column |
| ~20 mph gusts, 2019 final round | `docs/sources/003_Source_Log.md#anchor-6`, narrative anchor |

## Chapter 6 -- April 14, 2019

| Fact | Source |
|---|---|
| Koepka (9-iron, drifted right, bank, rolled back), Poulter (8-iron, didn't carry), Molinari (tee shot into the bank, rolled back), Finau (water), all double bogey | `docs/sources/003_Source_Log.md#anchor-4` |
| Molinari's tree-deflected chip found water on the 15th, not the 12th | Anchor 4's "Discrepancy caught and resolved" paragraph |
| ~20 mph gusts | Anchor 6 / Anchor 4 (PGATOUR.com retrospective) |
| 2019 scoring average 3.053 | `data.HOLE12_MODERN_AVG_BY_YEAR[2019]`, Anchor 4/Anchor 9 |
| 52 birdies / 200 pars / 38 bogeys / 14 double-or-worse of 304 | `data.HOLE12_OUTCOMES_BY_YEAR[2019]`, Anchor 4 |

## Chapter 7 -- Does the model know this hole?

| Number | Source |
|---|---|
| Tour oval 8.4 × 5.4 yd at the 155-yd shot | `tour.tour_oval()` = (8.4412, 5.4459); Anchor 7 |
| Model Tour season mean 3.1188 | `tour.tour_season_analytic_mean()`; `VALIDATION_NOTES.md`, "Pitch-over-water risk (rev 5)" → "Gate numbers" (3.1188) |
| Modern-era band 3.053–3.233, mean 3.132, sd ≈0.073 | `data.HOLE12_MODERN_AVG_BY_YEAR` (six years), Anchor 9; `VALIDATION_NOTES.md` "The gate retarget (Anchor 9, ADR 0002)" (mean 3.1318, sd 0.0732) |
| All-time scoring average 3.27–3.28 | `data.HOLE12_ALLTIME_AVG_RANGE`, Anchor 4 |
| 2016-2023 Tour proximity data underlying the oval | Anchor 7 |
| Bar chart years 2019, 2021, 2022, 2023, 2024, 2025 (2020 not played, no usable figure) | `data.HOLE12_MODERN_AVG_BY_YEAR`, Anchor 9 |
| All-time average spans 1934-2025 | ADR 0002 ("The all-time figure spans 1934-2025") |
| "~90-year average" | derived, 2025-1934 = 91, rounded |
| Anchor 1's 125-149 yard proximity band | `docs/sources/003_Source_Log.md#anchor-1` |
| Anchor 7's 150-175 yard Tour proximity band | `docs/sources/003_Source_Log.md#anchor-7` |
| Broadie, Science and Golf V, 2008 | `docs/sources/003_Source_Log.md#anchor-2` (citation year) |
| 300,000-run Monte Carlo harness | `VALIDATION_NOTES.md`, "Pitch-over-water risk (rev 5)" → "Gate numbers" ("amateur worst gap 0.0137 stroke (n=300,000...)... tour worst gap 0.0121 stroke") |
| Bogey bucket gap ≈5.7 points, 2019 | `VALIDATION_NOTES.md`, "Creek band fix (rev 4)" → 2019 bucket table (bogey 18.15% sim vs 12.50% pub, gap 5.65pp) |
| Bogey bucket gap ≈3.3 points, 2025 | `VALIDATION_NOTES.md`, "Pitch-over-water risk (rev 5)" → per-year shape gates (2025 bogey gap 3.27pp) |
| 2019 and 2023 published averages 3.053 and 3.058 below the calm-air floor | `data.HOLE12_MODERN_AVG_BY_YEAR` (Anchor 9); `VALIDATION_NOTES.md` per-year table (structural misses) |
| Bogey bucket gap ≈6.6 points, 2024 | `VALIDATION_NOTES.md`, "Pitch-over-water risk (rev 5)" → "Per-year shape gates" (2024 bogey gap 6.55pp) |

## Chapter 8 -- The move

Restates Chapters 2, 3, and 4's own numbers verbatim; see those sections above for the row-by-row source. No new figures introduced.

## Chapter 9 -- Try your own aim

No quoted numbers (CTA card only).

## Chapter 10 -- Method and sources

| Number | Source |
|---|---|
| Anisotropy 3.0, range 2.0–3.5 | `data.ANISOTROPY` |
| Green width 25.5 yd (midpoint), range 16–35 | `data.HOLE["green_width_yd_range"]` |
| Green depth 26.5 yd (midpoint), range 20–33 | `data.HOLE["green_depth_yd_range"]` |
| Front-third depth 10.5 yd (midpoint), range 9–12 | `data.HOLE["front_third_depth_yd_range"]` |
| Creek width + bank rollback 9.0 yd, range 6–13 | `data.CREEK_WIDTH_YD` + `data.BANK_ROLLBACK_YD` = 9.0; `data.CREEK_WIDTH_YD_RANGE` (4–8) + `data.BANK_ROLLBACK_YD_RANGE` (2–5) = 6–13 |
| Wind carry penalty 8 yd, range 4–12 | `data.WIND` (as above) |
| Wind dispersion inflation 1.3x, range 1.15–1.5x | `data.WIND` (as above) |
| Up-and-down rate 30% to 54% by tier, sensitivity range 0.8x to 1.2x | `data.UP_AND_DOWN_PCT` (0.30 at tier 20 to 0.54 at tier 0); `data.UP_AND_DOWN_PCT_RANGE_MULT` |
| Up-and-down sweep flips no pin's label at any tier | `tests/test_montecarlo.py::test_up_and_down_pct_sensitivity_on_amateur_verdicts`; `VALIDATION_NOTES.md`, "UP_AND_DOWN_PCT sensitivity (peer review Should-Fix 3)" |
| Pitch-over-water dunk rate 2% to 12% by tier | `data.PITCH_OVER_WATER_DUNK_PCT` (0.02 at tier 0 to 0.12 at tier 20) |
| Flip set: Sunday never flips | `optimizer.flip_set()`; `tests/test_optimizer.py::test_flip_set_baseline_labels_sunday_always_bail_left_and_center_are_the_tossup_pins`; `VALIDATION_NOTES.md` "Flip-set golden snapshot" (rev 4, unchanged by rev 5) |
| Scratch left pin flips to bail at anisotropy 3.5 (both wind states) | `tests/test_optimizer.py::test_flip_set_runs_and_matches_golden_snapshot`, key `(0, "left", False/True)` |
| Scratch center pin flips to bail at anisotropy 2.0 under wind | same test, key `(0, "center", True)` |
| 5-handicap left pin flips bail→either-works at its calm corner | same test, key `(5, "left", False)` |
| MC fidelity: amateur 0.014, Tour 0.012, tolerance 0.03 | `VALIDATION_NOTES.md`, "Pitch-over-water risk (rev 5)" → "Gate numbers" ("amateur worst gap 0.0137 stroke ... tour worst gap 0.0121 stroke") |

## Reading time and word count

Article body (chapters through method and sources, excluding the dek and
byline): 3,099 words. At 200 words/minute (002's own convention), that
rounds up to 16 minutes, the figure the byline states.
