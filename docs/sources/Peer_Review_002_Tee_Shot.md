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

---

## Resolution record (2026-07-12, post-review)

- **Should-fix 1 (MC precision claim): FIXED.** Caption and article now say "within 0.003 strokes," a bound the reproducible 0.0021 max gap clears with headroom.
- **Should-fix 2 (site nav): FIXED.** "Analyses" in the primary nav now points at the 002 article on the home, about, cite, 404, and 001-article pages. The Tools hub keeps its URL and gains a link to the 002 calculator; the calculator remains linked from the hero, the home card, the article, and the /cite page.
- **Minor 1 (TROUBLE_COST insensitivity): noted, no change.** Structural to the own-tier cost-line metric; recorded here as the methodology note the review asked for.
- **Minor 2 (inline modeled flag): FIXED for the "80 more yards" sentence** in the article ("a modeled tier" inline). The "230" sentence rests on the published tier 10 band; its benchmark-is-modeled disclosure stands in the adjacent chart caption and the disclosure paragraph.

---

## Rev 2 addendum review (2026-07-12: Hack It Out framing, verdicts, bailout threshold)

Scope: the 7-iron club rung, the bailout-threshold model and chart 6, the reframed article/caption copy, and the launch thread. Method: every number that entered rev 2 copy was re-derived from the model in one script; all twelve checks passed.

- Cost lines at 400 yd as quoted in the stacked post: 256.1 / 236.6 / 217.8 / 209.2 for 0/10/15/20, rounding to the quoted 256/237/218/209.
- Quote-card claims: 231.2 at 360/10 (quoted as 230, floor rounding consistent with the chart script), 27.8 yards under the 259 tier average (quoted 28).
- Bailout thresholds: one extra OB every 26 driver holes (15-hcp) and every 23 (20-hcp); tier range 23 to 40, as the caption states. Sensitivity: thresholds scale inversely with OB_COST; at the declared 1.5-to-2.5 range the 15-hcp figure runs 20 to 34 holes. The copy quotes the 2.0-stroke point value with the modeled label; acceptable, range recorded here.
- Club costs at 400/15: wood 0.076 (dek's "0.08-stroke luxury"), 4-iron 0.226 (quoted 0.23), 7-iron 0.394 (quoted 0.39); wood range across tiers at 400 is 0.051 to 0.088, matching the corrected "0.05 to 0.09" (an earlier "0.04 to 0.09" draft was caught and fixed pre-publication).
- Origin honesty: the article and caption quote only the episode's published show-notes question, disclose the fairway-conditioning difference, and no in-audio claim is paraphrased. Chart 6 carries the OB_COST modeled label.
- Test suite after rev 2: 47 passed.

**Rev 2 verdict: cleared for publication, no must-fix items.**

---

## Rev 3 addendum review (2026-07-13: golfer-as-actor sweep, backup-club calculator, trouble cross-check)

Scope: the copy sweep replacing club-as-actor phrasing (donates / owes / keeps its job / earns) with golfer-as-actor sentences across article, captions, chart 6, and tool; the calculator's backup-club comparison (club select + real backup distance mapped onto the curves via distance ÷ dist_ratio, OB break-even and per-club lie mix shown); the unified tools tabs with the calculator first; and the Fawcett/DECADE passage. Checks:

- Copy: zero remaining hits for the swept phrases across site and captions; the quoted Hack It Out question keeps its verbatim em dashes (quote, exempt).
- Backup math, independently verified in-browser and against the Python model at 400/15/220/wood: driver 5.291, backup-equivalent axis point 219.1, backup 5.379, delta 0.09, break-even 4.4% excess OB, one extra OB per 23 driver holes, 1.6 rounds at 14 driver holes a round.
- Lie mixes shown in the tool sum to 1 exactly (rough stored as residual, matching the model's convention) and the driver trouble rate (14.3-15.3% across tiers) sits inside the published Arccos band (17-25%) and above Shot Scope's strict penalty rates (1-3%); guarded by test_driver_trouble_rate_in_published_band.
- Suite: 48 passed after all rev 3 commits.

**Rev 3 verdict: cleared for publication, no must-fix items.**

---

## Rev 4 addendum review (2026-07-24: fairway-width variable, tool width slider, article width section, July 24 dates)

**Scope:** everything added since rev 3 — the `fairway_width` parameter threaded through `model.py`/`montecarlo.py`, `score_components` and its client-side JS mirror, the tool's fairway-width slider and label clarity pass, the article's "Squeeze the fairway and the answer holds" section, and the July 24 date move — plus a full whole-release regression sweep before launch (suite, rebuild determinism, nav, copy rules, cross-release Broadie curves, tier-30 labeling, reading time).

### Method

1. Ran `pytest -q` (55 tests), then wiped `outputs/` and rebuilt everything from scratch (`build_outputs.py`, all six `chart*.py` with `CITE_EXPORT=1`, `export_site_assets.py`) and diffed the working tree for drift.
2. Re-derived the width math directly against `model.py`, independent of the source log's own table: the width-25 delta and cost-line shift at (400, 15), the `score_components` decomposition identity at three randomly chosen (tier, club, width) triples, and a fresh Monte Carlo run at width 27 with a seed the suite does not use.
3. Re-derived every number in the article's width section from live model calls, then swept `club_verdict(400, t, fairway_width=W)` across all seven tiers at W in (20, 36, 50), plus spot checks at 320 and 480 yards at W=20, watching for any club other than driver winning.
4. Read the tool's embedded JS (`lieProbs`, `scoreAt`, `scoreAtInterp`, `costLineAtWidth`) line by line against `model._lie_probs`/`model.score_components`/`model.neutral_distance` to confirm the client-side math is a faithful port, and checked the width slider's min/max/step and the modeled-badge logic.
5. Grepped `site/` and `docs/sources/` for stray "July 20"/"2026-07-20", club-as-actor phrasing, em/en dashes, and -ly adverbs in the new copy.
6. Diffed `TOUR_DIST`/`TOUR_FAIRWAY`/`TOUR_ROUGH` against 001's `data.py` again and confirmed the primary nav still points at the 002 pages site-wide (regression check on rev 1's should-fix #2).
7. Recounted the article's rendered word count and checked it against the byline's stated reading time.

---

### Must Fix

*Issues that change the conclusion or produce a wrong output.*

None found. The `club_verdict` sweep found zero flips off driver across all seven tiers, three widths (20/36/50) at 400 yards, and the 320/480-yard spot checks at width 20 — the article's "holds at every width the calculator lets you set, from 20 to 50 yards" claim stands.

---

### Should Fix

*Issues that weaken the conclusion or could mislead the audience.*

| # | Location | Issue | Evidence |
|---|---|---|---|
| 1 | `site/tee-shot-distance/index.html` line 236 | The width section states "0.080 for a 15[-handicap]." The true value, computed directly from `model.expected_score`, is 0.0794621888302176 strokes, which rounds to 0.079 at three decimal places, not 0.080. The source log's own width-delta table (added this rev) lists the intermediate value as 0.0795 to four places; rounding that already-rounded 4-place figure a second time produces 0.080, a double-rounding error. The 10-handicap (0.076) and 20-handicap (0.083) figures in the same sentence are correct under either method, so only the 15-handicap figure is affected. | `expected_score(400,15,fairway_width=25) - expected_score(400,15)` = 0.0794621888302176; `Decimal(d).quantize(Decimal('0.001'))` = 0.079. Low stakes: the sentence's own headline framing ("about 0.08 strokes more") is accurate either way, and the error is 0.001 strokes on a number never used downstream. |
| 2 | `docs/sources/002_Post_Copy_LinkedIn.md` line 3; `docs/sources/002_Post_Copy_X.md` line 3 | Both scheduling notes still say the article and tool "live Monday July 20," with ship dates of "Tuesday July 21" and "Wednesday July 22." The actual ship date, confirmed everywhere else (byline, meta, JSON-LD, homepage card, sitemap, caption, pipeline doc), is July 24. These are not the peer-review doc's history — they are live scheduling instructions for the still-upcoming LinkedIn and X posts, and using them as written would post "went live this morning" framing on the wrong calendar day. | `grep -n "July 20\|July 21\|July 22" docs/sources/002_Post_Copy_LinkedIn.md docs/sources/002_Post_Copy_X.md` returns both line-3 hits; no other stray "July 20"/"2026-07-20" found anywhere else in `site/` or `docs/sources/` outside this review doc's own history sections. |

---

### Minor / Optional

*Suggestions for clarity or future improvement. Author's discretion.*

| # | Location | Suggestion |
|---|---|---|
| 1 | `site/tee-shot-distance/tool.html` line 475 | The Chart.js dataset label `DATA.tiers[tier] + ' — expected score, driver'` uses an em dash, visible in the chart legend. Pre-existing since the tool page's original commit (`8d3e72a`), not touched by rev 3's golfer-as-actor/dash sweep or this rev. Very low visibility (a legend fragment, not prose) but technically outside the house style now enforced elsewhere. |
| 2 | `site/tee-shot-distance/index.html` line 236 | Same pattern as rev 1's Minor #2: only the closing "gets back about 0.05 strokes" clause carries the inline `modeled` badge, even though every non-36-yd number in the paragraph (0.076/0.080/0.083, 218→232, the 13-17 yd range) is equally modeled geometry per the source log's new width entry. The section header, the adjacent tool's width-badge logic, and the paragraph below ("Width is a second-order lever...") all disclose the modeling, so a reader who screenshots just the numeric sentence loses the flag, same low-stakes gap as before. |

---

### Width math verification

| Check | Expected (task) | Computed | Match |
|---|---|---|---|
| `expected_score(400,15,fw=25) - expected_score(400,15)` | ≈ +0.080 | +0.0794621888302176 | Yes (rounds to 0.079, see Should-Fix 1) |
| `neutral_distance(400,15,fw=25)["threshold"]` | ≈ 232.0 | 232.0446134534514 | Yes |
| `score_components` decomposition, 3 random (tier, club, width) triples | agrees to 1e-9 | tier=10/wood/W=31.8: diff -8.9e-16; tier=0/seven_iron/W=22.8: diff +1.8e-15; tier=0/seven_iron/W=26.4: diff +8.9e-16 | Yes, all at float-precision noise floor |
| `simulate_hole` vs analytic at width 27 | agrees within 0.03 | seed 20260720 (suite's own): gap 0.0011; independent seed 999, n=200,000: gap 0.0011 | Yes |

Also independently reproduced the suite's own `test_decomposition_reproduces_expected_score` and `test_montecarlo_matches_at_nondefault_width` logic outside pytest, not just trusting green output.

---

### Article width-section number audit

| Claim | Article text | Recomputed | Match |
|---|---|---|---|
| 10-hcp cost at W=25 vs 36, 400 yd | 0.076 | 0.07623973591721445 | Yes |
| 15-hcp cost at W=25 vs 36, 400 yd | 0.080 | 0.0794621888302176 | **No — rounds to 0.079** (Should-Fix 1) |
| 20-hcp cost at W=25 vs 36, 400 yd | 0.083 | 0.08253247154492804 | Yes |
| 15-hcp cost line, 218 → 232 | 218 → 232 | `neutral_distance` threshold 217.7557 → 232.0446 | Yes |
| Cost-line jump, 15-hcp | 14-yard jump | 232.0446 - 217.7557 = 14.29 | Yes |
| 10/20-hcp cost-line shift range | 13-17 yd | tier 10: 16.89 yd; tier 20: 12.96 yd | Yes, both inside range |
| Widen to 45, golfer gets back | ~0.05 strokes | tier 10: -0.0519; tier 15: -0.0542; tier 20: -0.0564 | Yes, all round to "about 0.05" |
| Driver verdict holds 20-50 yd, all tiers, 400 yd | holds | 7 tiers x {20,36,50} = 21 cells, all driver | Yes, no flips |
| Driver verdict spot check, 320/480 yd, W=20 | holds | 7 tiers x 2 holes = 14 cells, all driver | Yes, no flips |

---

### Rebuild determinism

```
rm -rf outputs && python build_outputs.py && for i in 1 2 3 4 5 6; do CITE_EXPORT=1 python chart$i.py; done && python export_site_assets.py
git status --short -- site analysis docs
```

Produced no output — a full from-scratch rebuild reproduces every chart PNG, cite variant, and embedded tool blob byte-for-byte against what is committed. No drift.

---

### Tool integrity

- Embed tests (`test_build_outputs_writes_valid_tool_json`, `test_blob_decomposition_matches_model`, `test_tool_page_embeds_current_tool_data`) pass as part of the 55.
- Width slider: `min="20" max="50" step="1" value="36"` — 25 is directly reachable.
- Main slider label: "Your driver distance," hint "The driver's own carry plus roll."
- Backup slider label: "Your `<span id="ts-backup-club-label">`... distance," populated per club by `DATA.clubs[club].label` in `render()`; hint "That club's own distance, not your driver's."
- Never-rescales note present: "Every distance here is the named club's own. The model never rescales what you type" (line 173), plus a second width-specific note appended at render time: "The benchmark and dashed line stay pinned to the 36 yd default width, so a narrower fairway shows up here as strokes lost against a fixed goalpost, not a moved one."
- Modeled badges: width label shows `<span class="badge-modeled">modeled</span>` whenever `width !== 36`; tier label shows it whenever `DATA.modeled.includes(tier)` (tier 30 only); both confirmed by reading the JS, not just assuming from the blob.
- Client-side `lieProbs`/`scoreAt`/`costLineAtWidth` are a line-for-line port of `model._lie_probs`/`score_components`/`neutral_distance`; the JS comments say so explicitly and the math checks out against the Python side.

---

### Dates

| Location | Value | Status |
|---|---|---|
| Article `article:published_time` meta | 2026-07-24 | OK |
| Article JSON-LD `datePublished` | 2026-07-24 | OK |
| Article byline | "July 24, 2026" | OK |
| Homepage card | "July 24, 2026" | OK |
| Sitemap, `tee-shot-distance/` | lastmod 2026-07-24 | OK |
| Sitemap, `tee-shot-distance/tool.html` | lastmod 2026-07-24 | OK (two entries, as expected) |
| Caption ship line | "Ship date: 2026-07-24" | OK |
| Pipeline doc, 002 row | "Jul 24, 2026 (slipped from Jul 20)" | OK, explicitly notes the slip |
| `site/` (whole tree) | grep for "July 20"/"2026-07-20" | Clean, zero hits |
| `docs/sources/` (whole tree) | grep for "July 20"/"2026-07-20" | Two stray hits, both in social scheduling docs (Should-Fix 2); peer-review doc's own history mentions are the accepted exception and were excluded |

---

### Copy rules regression

- Club-as-actor phrases (donates, owes, keeps its job, earns the, wants the): zero hits across `site/` and the 002 caption/post-copy docs.
- -ly adverbs in the new width section (article paragraphs + heading): zero.
- Em/en dashes outside the quoted podcast question: one pre-existing hit, a Chart.js legend string in `tool.html` (Minor 1). `site/assets/css/site.css` and `fairway-vs-rough/dashboard.html` also contain dashes but are shared/001 assets outside this release's copy, and the CSS hits are code comments, not reader-facing prose.

---

### Cross-release and labeling spot checks

- `TOUR_DIST`/`TOUR_FAIRWAY`/`TOUR_ROUGH` in 002's `data.py` still match `Fairway_vs_Rough_Post/source/data.py` value-for-value (whitespace only difference), unchanged since rev 1.
- Primary nav "Analyses"/"Tools" links still point at the 002 article/tool on `index.html`, `about/index.html`, `404.html`, `cite/index.html`, and `fairway-vs-rough/index.html` — rev 1's should-fix #2 has not regressed.
- Modeled badges present: tool width label at non-36 widths (confirmed in JS), the article width section (Minor 2 notes partial coverage), chart 6's figcaption, and tier 30 everywhere in the tool (tier dropdown label and the benchmark line itself, via `DATA.modeled`).

---

### Reading time

Full rendered word count inside `<article>...</article>` (headings, paragraphs, figcaptions, tables, the sources definition list — everything a reader can see), computed by stripping HTML tags and tokenizing: 2,286 words. 2286 / 230 = 9.94, rounds to 10. Byline reads "10 min read." Match. (For reference, this rev bumped the byline from 8 to 10 minutes alongside the ~178-word width section; the 8-minute figure at rev 3 was already slightly under this same counting method — 2,105 words there would round to 9 — but that predates this review's scope and does not affect the current, correctly-rounded 10.)

---

### Suite

`pytest -q`: 55 passed (up from 48 at rev 3; the width variable adds 5 new tests in `tests/test_width.py` plus 2 more in `tests/test_outputs.py` covering the blob decomposition and embed).

---

**Rev 4 verdict: cleared for publication.** No must-fix items; two should-fix items (the article's "0.080" rounding on the 15-handicap width delta, and stale "July 20" scheduling dates in the LinkedIn/X post-copy docs) are both cosmetic — neither touches the model, the data, the driver-verdict conclusion, or any live site page — but both are worth a quick fix before or immediately after the post-copy docs get used to actually schedule the launch posts.

**Reviewer sign-off:** Claude — 2026-07-24
*(55/55 tests pass; full rebuild reproduces the committed `site`/`analysis`/`docs` trees byte-for-byte with zero diff; width math independently re-derived against `model.py` and matches within float precision; driver verdict swept across 7 tiers x 3 widths x 3 hole lengths with zero flips; Broadie tour curves still match 001 exactly; nav regression from rev 1's should-fix #2 holds)*
