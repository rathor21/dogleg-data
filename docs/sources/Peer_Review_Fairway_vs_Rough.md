# Peer Review

**Work reviewed:** Fairway vs. Rough, by Handicap (post package — chart1-5, caption, worth_by_distance CSV)
**Author:** Sunny
**Reviewer:** Claude (independent pass, code and data re-derived from scratch rather than re-reading the original code)
**Review type:** Full (logic, statistics, presentation — code review not requested)
**Date:** 2026-07-01
**Turnaround commitment:** same day

---

## Context

**Business question this analysis addresses:**
Should a golfer, segmented by handicap, play a rough ball or a fairway ball in a scramble, and how far does "stay in the fairway" advice actually hold up by skill level.

**What I reviewed:**
- [x] Logic and conclusions
- [x] Data sourcing and transformations
- [ ] Code (SQL / Python / notebook) — out of scope per requested review scope, though three bugs surfaced anyway while re-deriving numbers and building the dashboard
- [x] Communication and presentation

Audience for this delivery: the Golfwell podcast, Dr. Luke Benoit, the golf community on X, and the data/analytics community on LinkedIn — a technical audience that will poke at edge cases, which raised the bar on this pass relative to a typical internal review.

---

## Must Fix

*Issues that change the conclusion or produce a wrong output. Resolved before this delivery.*

| # | Location | Issue | Resolution |
|---|---|---|---|
| 1 | `model.py`, `amateur_worth_table()` | The 30-index "fairway worth" curve was built by doubling a single noisy bin-to-bin delta (`worth[20] - worth[15]`) from the published Stagner table. Real bin-level noise in the source table got doubled along with it, producing a sign-flip artifact: the 30-handicap worth number went positive at 210-220yd after already going negative at 200yd, then negative again at 230+. That's a method artifact, not a golf finding, and it also drove a wrong headline number (150yd, 30-handicap: 9 yards). | Refit using ordinary least squares across all five published handicap points (0/5/10/15/20) per distance bin, then extrapolated the fitted line to 25/30. Direction changes in the resulting curve dropped from 13 to 5 (the residual 5 reflect real noise already present in the published 0-20 data, not the extrapolation method). The 150yd, 30-handicap number moved from 9 to 12 yards. |
| 2 | `montecarlo.py`, `make_curve()` | The dispersion-by-handicap extrapolation used the fitted quadratic's own instantaneous derivative at hcp=13 as the growth rate for hcp>13. For the width (left-right) dispersion curve specifically, that derivative was negative (-0.11 yd/hcp), so simulated shot dispersion *shrank* from hcp 13 to 30 instead of growing. Verified impact: at several distances (e.g. 130yd, rough/moderate) the simulation showed a 30-handicap hitting greens at a higher rate than a 20-handicap — backwards, and exactly the kind of thing a sharp reviewer checks first. | Extrapolation now uses the secant slope over the last measured interval (hcp 8→13), which is guaranteed non-negative since every real anchor pair shows dispersion increasing. Re-ran a full sweep (60-250yd, all lie/severity combinations, 20 vs 30-handicap): zero inversions remain, down from a systematic pattern before the fix. |
| 3 | `model.py`, `tour_worth()` | Found while building the dashboard, but it affects every existing deliverable: `tour_worth()` computed the tour worth curve only at `TOUR_DIST`'s own sparse, unevenly-spaced points (10yd steps below 100yd, 20yd steps above), and `tour_worth_at()` linearly interpolated those. Chart 1 never called this function — it does its own direct fine-grid computation — so chart 1 and the caption both correctly say "150yd = 75yd worth." But chart 2, the CSV export, and this new dashboard all call `tour_worth_at()`, which returned 76.67yd at the same distance. Same claim, two different numbers, depending on which chart you looked at (max discrepancy across the range: 2.33yd, at 146yd). This is exactly the kind of inconsistency a technical audience cross-referencing chart 1 against chart 2 would catch immediately. | `tour_worth()` now computes on a dense 1-yard grid using the same direct method chart 1 already uses, instead of interpolating sparse pre-computed values. Verified `tour_worth_at(150)` now returns exactly 75.0, matching chart 1 and the caption. Chart 2, the CSV, and the dashboard data were all regenerated. |

---

## Should Fix

*Issues that weaken the conclusion or could mislead the audience. Resolved before this delivery.*

| # | Location | Issue | Resolution |
|---|---|---|---|
| 1 | `montecarlo.py`, `dispersion_yd()` | Tour dispersion is set to 75% of scratch-amateur dispersion. The code comment implied this came from "ShotLink proximity data," but there's no specific citation behind the 25% figure anywhere in the source set used for this analysis — it's a plausible judgment call, not a sourced number. | Comment corrected to say plainly it's an assumption. Disclosed in chart3 and chart4 footers and in the caption's Sources paragraph, so it's not silently presented as data. |
| 2 | `chart2.py` | The severity heatmap listed a "30-hcp" row with no flag, while chart 1's 30-hcp line is clearly dashed and labeled "(modeled)." Inconsistent treatment of the same extrapolated tier across the two most-viewed charts. | Relabeled the row "30-hcp*" with a footnote clarifying it's extrapolated beyond Stagner's published 0-20 range. |
| 3 | Caption, confound paragraph (resolved earlier in this working session, noted here for completeness) | Original rough-severity confound check compared cut height only, which is a weak proxy for how punishing rough plays (density, blade width, and grow-in practice matter more, per Oak Hill/Oakmont/Shinnecock agronomy). | Rewritten to lead with density/thickness rather than height, and chart 2's "deep rough (U.S. Open style)" label was corrected to "(thick primary cut)" since the modeled multiplier was never sized to true U.S. Open native rough. |

---

## Minor / Optional

*Suggestions for clarity or future improvement. Author's discretion — not changed for this delivery.*

| # | Location | Suggestion |
|---|---|---|
| 1 | Caption, long-range crossover paragraph | "a 15-handicap crosses the same line at 250" implies more precision than the data supports — the published table is binned every 10 yards, and the actual crossover falls somewhere in the 240-250 window, not exactly at 250. Low stakes given the direction of the finding is solid, but a precise reader could flag the wording. |
| 2 | Monte Carlo charts (3/4/5) | No uncertainty band shown. Sampling error is small at these trial counts (n=30k-80k, roughly 0.1-0.3pp), so it's not misleading, but the real uncertainty (from the extrapolated high-handicap dispersion curve) is unquantified and only disclosed qualitatively ("most heavily modeled"). A shaded sensitivity range for the 25/30-handicap bars would be a stronger version of this for a technical audience, if there's a next iteration. |
| 3 | `montecarlo.py`, `width_curve` | The fitted quadratic has its vertex at hcp≈12.1, so there's a ~0.05-yard dip between hcp 12.1 and 13, inside the *interpolated* (not extrapolated) region. This is an artifact of fitting an exact curve through only 3 anchor points. Magnitude is below any real measurement precision and isn't visible in any chart — flagging for completeness, not asking for a fix. |
| 4 | `model.py`, `amateur_worth_table()` | Computes a 25-index column that isn't used in any chart or the caption. Harmless dead code; worth removing or wiring up if a 25-index tier is ever added to the visuals. |

---

## What's Working Well

1. Every headline number in the caption survived an independent from-scratch recomputation. I rebuilt the tour worth curve and the 10/20/30-handicap worth numbers directly from `TOUR_DIST`/`TOUR_FAIRWAY`/`TOUR_ROUGH`/`AM_TIE` without touching `model.py`, and matched the caption's claims to the exact yard: 150yd tour worth = 75, peak at 140yd = 80, 10-handicap = 23, 20-handicap = 17. The rough-penalty range (0.16-0.25 strokes) and the "basically as good from 90 as from 60" claim (2.70 vs 2.77 strokes) checked out the same way.
2. The published-vs-modeled line is drawn honestly throughout, not just in one disclaimer paragraph. Every chart footer separates hard data (Broadie, Stagner) from simulation, and the long-range rough-beats-fairway crossover was explicitly flagged as something the Monte Carlo model could *not* reproduce, rather than being quietly smoothed over or dropped. That's the right instinct for an audience that includes a working golf-analytics researcher.

---

## Overall Assessment

- [x] **Approved with minor revisions** — three must-fix items were found and resolved during this review cycle (see above); should-fix items are also resolved. Minor items are noted for awareness and left at the author's discretion.

**Reviewer sign-off:** Claude — 2026-07-01
*(must-fix items #1, #2, and #3 confirmed resolved: re-ran the full inversion sweep, the extrapolation-smoothness check, and a chart1-vs-chart2 cross-consistency check on the tour number after each fix, all clean)*

---

## Changes Made (Summary)

1. Fixed the 30-index amateur worth extrapolation (least-squares fit across all 5 published points instead of doubling one noisy delta). 150yd/30-handicap number: 9 → 12 yards.
2. Fixed the Monte Carlo width-dispersion extrapolation (secant slope instead of local derivative). Eliminated a systematic inversion where 30-handicap GIR% could exceed 20-handicap GIR% at the same distance.
3. Fixed `tour_worth()` to compute on a dense grid instead of interpolating sparse pre-computed points, resolving a chart1-vs-chart2 inconsistency on the tour number (150yd: 76.67 → 75.0, now matching chart 1 and the caption everywhere it's used).
4. Disclosed the unsourced "tour = 75% of scratch dispersion" assumption in chart footers, the caption, and the code comment.
5. Flagged chart 2's 30-hcp row as extrapolated, matching chart 1's treatment.
6. Regenerated all five charts, the CSV export, and the new interactive dashboard's data with the fixed model; updated the caption's affected numbers and added a transparency note describing what the peer review caught.
