# Peer Review

**Work reviewed:** How Far Do You Need to Hit It? (release 002, tee-shot club/distance, par 4s) — data.py, model.py, montecarlo.py, build_outputs.py, chart1-5.py, the caption, the article, the tool, /cite
**Author:** Claude, direction by Sunny
**Reviewer:** Claude (independent pass; code re-run from scratch, not re-read as a proof of correctness)
**Review type:** Full (logic, statistics, sourcing, presentation, code)
**Date:** 2026-07-12
**Turnaround commitment:** same day

---

## Context

**Business question this analysis addresses:** which club a golfer should hit off the tee, and how far a drive needs to travel, to keep a par-4 score at that golfer's own handicap-tier benchmark, once the approach shot the drive creates is priced in.

**What I reviewed:**
- [x] Logic and conclusions
- [x] Data sourcing and transformations
- [x] Code (data.py, model.py, montecarlo.py, build_outputs.py, chart1-5.py, tests)
- [x] Communication and presentation (caption, article, tool, /cite, home page)

I ran the test suite, re-derived the calibration and Monte Carlo checks from scratch rather than trusting the source log's numbers, and perturbed two calibration knobs in memory to test how far the headline numbers move under a declared sensitivity range. `data.py` was not edited; every perturbation ran in a live Python session and was reverted before exit.

---

## Method

1. Sampled ten numeric literals in `data.py` across anchors A, C, D, E, and F and traced each to `docs/sources/002_Source_Log.md`.
2. Re-ran the `LENGTH_MIX`-weighted expected-score check against `BENCHMARK_AGG` for all six published tiers.
3. Ran `pytest -v` and independently re-ran the Monte Carlo comparison at (0, 15, 30) x (340, 400, 460) yards with the same seed the test suite uses.
4. Scaled `MISHIT` and `TROUBLE_COST` to 0.5x and 1.5x their published starting values, one knob at a time, and recomputed the 400-yard cost lines for tiers 10/15/20 and the tier-10-at-360-yard headline number for each of the four scenarios.
5. Diffed `TOUR_DIST`/`TOUR_FAIRWAY`/`TOUR_ROUGH` in 002's `data.py` against 001's `data.py` line by line, and grepped both for `GOLFTEC`.
6. Read all five chart PNGs, the tool page, the article, and the caption for modeled-label coverage.
7. Re-derived every quoted number in the caption and article from `outputs/002_results.csv`, the chart scripts' own stdout, and direct model calls.

---

## Must Fix

*Issues that change the conclusion or produce a wrong output.*

None found.

---

## Should Fix

*Issues that weaken the conclusion or could mislead the audience.*

| # | Location | Issue | Evidence |
|---|---|---|---|
| 1 | `docs/sources/002_Tee_Shot_Caption.md` line 21; `site/tee-shot-distance/index.html` lines 254 and 274 | All three places claim the Monte Carlo harness "agrees with the analytic model within 0.002" strokes. The actual measured max gap, with the same seed, tiers, holes, and trial count the test suite uses, is 0.0021 strokes, not within 0.002. | `pytest -s tests/test_montecarlo.py` prints "max MC vs analytic gap: 0.0021 strokes"; an independent re-run outside the test suite (same seed 20260720) returned 0.002053903040251548. The test's own tolerance is 0.03, so nothing here threatens the finding, but the specific "within 0.002" claim is off by roughly 0.0001 strokes in three published places. |
| 2 | `site/index.html` lines 72-73, `site/cite/index.html` lines 67-68, `site/about/index.html`, `site/404.html`, `site/fairway-vs-rough/dashboard.html` (site-wide nav) | The primary nav's "Analyses" and "Tools" links still point to `fairway-vs-rough/index.html` and `fairway-vs-rough/dashboard.html` (release 001), not to the new `tee-shot-distance` pages. A visitor who lands on the home page and uses the top nav, instead of the hero button or the "latest analysis" card, cannot reach the 002 article or tool. `tee-shot-distance/index.html`'s own nav was updated correctly (its "Analyses" link is the current-page marker, "Tools" points to `tool.html`); the rest of the site was not. | `grep -rln "fairway-vs-rough/index.html\|fairway-vs-rough/dashboard.html" site/` returns `index.html`, `404.html`, `cite/index.html`, `about/index.html`, `fairway-vs-rough/dashboard.html`. |

---

## Minor / Optional

*Suggestions for clarity or future improvement. Author's discretion.*

| # | Location | Suggestion |
|---|---|---|
| 1 | `data.py`, `TROUBLE_COST` | The cost-line metric is nearly insensitive to `TROUBLE_COST` (see the sensitivity table below: under 0.001 yards of movement at 0.5x/1.5x). The reason is structural, not a bug: `TROUBLE_COST` adds a near-flat cost across every drive distance because trouble probability depends on lateral dispersion, not carry, and the benchmark is the same model evaluated at the tier's own average drive, so the shift cancels between the curve and the benchmark it is measured against. Worth a line in the methodology so a future reader doesn't mistake the flat sensitivity for the knob being unimportant to the underlying strokes total; it moves `expected_score(400, 15)` from 5.204 to 5.257 at 1.5x, a real change, just one the cost-line metric specifically does not see. |
| 2 | Caption and article, first mentions of the "80 more yards" and "230" headline claims | Both numbers rest partly on tier 30, which is modeled (least-squares extrapolation, no published band). The nearby chart carries the modeled label correctly (chart 1's legend marks "30-handicap (modeled)" with a dashed line), and the piece's closing disclosure paragraph names tier 30 as modeled, but the sentence making the claim itself carries no inline flag. Low stakes since the chart sitting next to the sentence is labeled and the disclosure paragraph is unambiguous, but a reader who screenshots just the sentence loses the flag. |

---

## Sensitivity analysis

Scaled `MISHIT` (all tiers) and `TROUBLE_COST` (all tiers) to 0.5x and 1.5x their calibrated starting values, one knob at a time, in a live session against the unmodified `data.py` on disk. Verified the mechanism was not a no-op before trusting the results: `expected_score(400, 15)` moved from 5.204051925307641 (baseline) to 5.256799055294922 (`TROUBLE_COST` x1.5) and 5.15130479532036 (`TROUBLE_COST` x0.5), and `neutral_distance` thresholds moved measurably under `MISHIT` scaling (see deltas below).

| Scenario | Cost line, tier 10, 400 yd | Cost line, tier 15, 400 yd | Cost line, tier 20, 400 yd | Cost line, tier 10, 360 yd | Headline (rounded to nearest 5) |
|---|---|---|---|---|---|
| Baseline | 236.6 | 217.8 | 209.2 | 231.2 | 230 |
| MISHIT x0.5 | 236.7 | 218.0 | 209.5 | 231.3 | 230 |
| MISHIT x1.5 | 236.5 | 217.5 | 208.9 | 231.1 | 230 |
| TROUBLE_COST x0.5 | 236.6 | 217.8 | 209.2 | 231.2 | 230 |
| TROUBLE_COST x1.5 | 236.6 | 217.8 | 209.2 | 231.2 | 230 |

Max spread across all four scenarios, per metric: tier 10 at 400 yd, 0.2 yd; tier 15 at 400 yd (the "218" number), 0.4 yd; tier 20 at 400 yd (the "209" number), 0.6 yd; tier 10 at 360 yd (the "230" headline), 0.2 yd.

**Range rule:** the design spec's rule triggers a caption range if any headline number moves more than 15 yards across the sensitivity sweep. The largest movement measured here is 0.6 yards, at tier 20. **The rule does not trigger.** The caption and quote card can keep their point values as written. This holds specifically for `MISHIT` and `TROUBLE_COST` at the declared (0.5, 1.5) multiplicative range; it says nothing about `sd_dist_frac`, the loft-tightening factor, or the tour-to-scratch offset, none of which this review was scoped to perturb.

---

## Calibration record

Re-ran the `LENGTH_MIX`-weighted `expected_score` against `BENCHMARK_AGG` for all six published tiers, independent of the source log:

| Tier | Model | Published | Gap |
|---|---|---|---|
| 0 | 4.1999 | 4.2000 | -0.0001 |
| 5 | 4.4999 | 4.5000 | -0.0001 |
| 10 | 4.8000 | 4.8000 | +0.0000 |
| 15 | 5.1000 | 5.1000 | -0.0000 |
| 20 | 5.3999 | 5.4000 | -0.0001 |
| 25 | 5.9001 | 5.9000 | +0.0001 |

Max gap: 0.0001 strokes, at tier 25. This matches the source log's Calibration section exactly, row for row.

---

## Monte Carlo agreement

`pytest -v` passed all 44 tests. Independently re-ran the comparison at (0, 15, 30) x (340, 400, 460) with the test suite's seed (20260720):

| Tier | Hole | Monte Carlo | Analytic | Gap |
|---|---|---|---|---|
| 0 | 340 | 4.0707 | 4.0713 | 0.0006 |
| 0 | 400 | 4.2939 | 4.2938 | 0.0001 |
| 0 | 460 | 4.5276 | 4.5266 | 0.0010 |
| 15 | 340 | 4.9396 | 4.9408 | 0.0012 |
| 15 | 400 | 5.2038 | 5.2041 | 0.0002 |
| 15 | 460 | 5.5889 | 5.5869 | 0.0021 |
| 30 | 340 | 5.9751 | 5.9763 | 0.0012 |
| 30 | 400 | 6.4019 | 6.4006 | 0.0014 |
| 30 | 460 | 6.8853 | 6.8862 | 0.0009 |

Max gap: 0.0021 strokes, at tier 15, 460 yd, well inside the test's 0.03 tolerance. This is the number behind Should-Fix #1: the published "within 0.002" claim should read 0.0021, or round up to a safer "within 0.003."

---

## Source log audit

Sampled ten numeric literals in `data.py`, spread across anchors A, C, D, E, and F, and traced each to `docs/sources/002_Source_Log.md`:

| Literal | `data.py` location | Anchor | Traced to |
|---|---|---|---|
| 285 (driver mean, 0-hcp) | `_DRIVER_MEAN_PUB[0]` | A | Anchor A table, MyGolfSpy, retrieved 2026-07-11 |
| 0.48 (fairway-hit %, 0-hcp) | `_FAIRWAY_HIT_PUB[0]` | A | Anchor A table, same source |
| 261 (3-wood mean, 0-hcp, used in `_WOOD_RATIO`) | wood-ratio comment block | C | Anchor C table row hcp 0 |
| 219 (3H P-avg, 0-hcp, used in `_HYBRID_RATIO`) | hybrid-ratio comment block | C | Anchor C table row hcp 0, "197/219" column |
| 151 (4-iron, 25-hcp, used in `_IRON_RATIO`) | iron-ratio comment block | C | Anchor C table row hcp 25 |
| 18 (`fairway_half_width`) | `GEOMETRY` | F | Stagner Newsletter #13, half of the published 36-yard fairway |
| 2.18 (`TOUR_FAIRWAY[0]`) | `TOUR_FAIRWAY` | D | Broadie 2011 ShotLink Table 9, reused from 001 per the log's note |
| 4.8 (`BENCHMARK_AGG[10]`) | `_BENCHMARK_AGG_PUB` | E | Anchor E table, MyGolfSpy, retrieved 2026-07-11 |
| 0.36 (`_GIR_PCT_PUB[10]`) | `_GIR_PCT_PUB` | E | Anchor E table, GIR % column |
| 2.05 (`_PUTTS_PER_GIR_PUB[10]`) | `_PUTTS_PER_GIR_PUB` | E | Anchor E table, putts-per-GIR column |

All ten traced cleanly. No untraceable literal found in this sample. Calibration knobs (`MISHIT`, `TROUBLE_COST`, `HOLEOUT_SCALE`) and pure modeling choices (`GEOMETRY["rough_band"]`, `LENGTH_MIX`, `LEFTOVER_FLOOR_YD`, `_LOFT_TIGHTEN`, `_TOUR_TO_SCRATCH_OFFSET`) carry no source URL by design; each one is commented MODELED with a stated sensitivity range instead, which is what the spec asks for.

---

## Cross-release consistency

`TOUR_DIST`, `TOUR_FAIRWAY`, and `TOUR_ROUGH` in 002's `data.py` (lines 219-221) match `/Users/sunny/Documents/Claude/Projects/Golf Agent/Fairway_vs_Rough_Post/source/data.py` (lines 11-13) exactly, value for value; the only difference between the files is whitespace. `grep -rn GOLFTEC` across 002's source finds nothing: the source log lists GOLFTEC as a documented fallback option for driver dispersion, but the model uses the Shot Scope fairway-hit-percentage inversion instead (source 1 under Anchor B), so GOLFTEC is not a number 002 actually shares with 001. That is a legitimate choice already disclosed in the log, not a gap.

---

## Chart-to-copy consistency

Re-derived every quoted number from `outputs/002_results.csv`, the chart scripts' stdout, and direct model calls:

| Claim | Caption / article | Recomputed | Match |
|---|---|---|---|
| 10-hcp, 360-yd cost line | 230 | `chart5.py`: threshold 231.2, rounds to 230; CSV row `10,360,4.744,0.1,231.2` | Yes |
| Headroom, 360-yd leftover | 130 yd in | 360 - 230 = 130 | Yes |
| Gap vs tier average | 28 yards under | `chart5.py`: gap 27.8, rounds to 28 | Yes |
| 15-hcp, 400-yd cost line | 218 | `neutral_distance(400, 15)["threshold"]` = 217.7557 | Yes |
| 20-hcp, 400-yd cost line | 209 | `neutral_distance(400, 20)["threshold"]` = 209.1685 | Yes |
| Headroom figures | 24 / 22 / 18 / 16 | `chart2.py` stdout: 24.2, 22.4, 18.2, 15.8 | Yes |
| Scratch-vs-30 gap | about 80 | tier-0 cost line 256.1 minus tier-30 cost line 178.3 at 400 yd = 77.8, rounds to 80 | Yes |
| 220-drive decomposition delta | 0.09 | Chart 3 panel A, 220-yd drive bar reads +0.09 | Yes |
| Wood approach / buyback / net | 0.15 / 0.07 / 0.08 | Chart 3 panel B: 3-wood approach +0.15, actual net +0.08, buyback = 0.15 - 0.08 = 0.07 | Yes |
| Club map worst case | 0.12 | Chart 4, scratch row, 480-yd column, bolded 0.12 | Yes |
| 25-hcp, 320-yd 3-wood cost | 0.02 (article body) | Chart 4, 25-hcp row, 320-yd column = 0.02 | Yes |

No mismatches found.

---

## Labeling audit

Chart 1 marks tier 30 with a dashed line and "(modeled)" in the legend. Chart 4 marks the "30 hcp (modeled)" row. Charts 1 through 5 each carry a subtitle or footer stating the benchmark is modeled and calibrated to published Shot Scope aggregates. The tool's tier dropdown labels tier 30 "30-hcp (modeled)" in the data it renders, and its footer names every modeled step (tier 30's extrapolation, the length-resolved benchmark, and the lateral-dispersion smoothing) by name. The /cite page repeats the modeled-benchmark disclosure and instructs users to keep the "modeled" labels visible when they reuse a chart. The one gap is Minor #2 above: the specific sentences carrying the "80" and "230" numbers don't carry an inline flag, though the chart beside each one does.

---

## What's Working Well

1. The calibration and Monte Carlo numbers in the source log are not just plausible, they are exactly reproducible. Re-running both from scratch, without reading the log's stated results first, landed on the same values to four decimal places for calibration and matched the test suite's own printed Monte Carlo gap precisely.
2. Every quoted chart number in the caption and article traces cleanly to a script's own computed output, not a hand-typed value. Chart 1's headline gap, chart 2's headroom figures, and chart 5's quote-card number are all computed inside the chart scripts themselves and printed to stdout, which is the right way to keep prose and pixels from drifting apart.
3. The headline numbers are genuinely robust. A 50% swing in either calibration knob, in either direction, moves the cost line by well under a yard. The design spec's own 15-yard range-disclosure rule gave this review a real bar to clear, and the model cleared it with room to spare.

---

## Overall Assessment

- [x] **Cleared for publication pending must-fix items** — there are no must-fix items, so this reads as clean; the two should-fix items (the "within 0.002" precision claim, and the site-wide nav still pointing at release 001) are worth fixing before or shortly after the July 20 ship date, but neither touches the model, the data, or the conclusion.

**Reviewer sign-off:** Claude — 2026-07-12
*(sensitivity range rule checked and does not trigger; calibration and Monte Carlo numbers independently reproduced; 44/44 tests pass; ten sampled data.py literals all trace to the source log; cross-release Broadie curves match 001 exactly)*
