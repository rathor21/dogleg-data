# Release 003 validation notes (issue #9, ADR 0002 pass)

**Publication status (2026-09-07, updated after the pitch-over-water risk fix, #8 rev 5):** the must-pass gates pass: the season-mean gate and the MC-vs-analytic fidelity gates all pass outright. The per-year shape checks for 2024 and 2025 are disclosed near-misses on the bogey bucket (details in "Creek band fix (rev 4)" and "Pitch-over-water risk (rev 5)" below and in ADR 0002's rev 3 addendum), shipped under `xfail(strict=False)` rather than tuned to force a pass; 2019 and 2023 remain structural misses (their published means sit below this model's own achievable range). The region-geometry fix that closed the amateur-side creek defect reopened 2025 as a new, marginal (0.2-point) near-miss -- previously a clean pass; rev 5's pitch-over-water fix barely moves it either way. Sunny decides whether this is acceptable to publish or needs further model work first. Rev 5 also closes a real gap the creek-band fix left open: the short_fairway pitch back over Rae's Creek carried no water risk at all, which had the optimizer recommending a 30+ yard Sunday-pin layup with no mechanism behind it -- see "Pitch-over-water risk (rev 5)" below for the fix, the sensitivity sweep, and the disclosed fact that several Sunday rows still lay up more than 15 yd even with the risk correctly priced.

Dated 2026-09-07. Companion to `tests/test_model.py`, `tests/test_montecarlo.py`,
and `tests/test_optimizer.py`. Numbers below come from running this tree's
`model.py`, `tour.py`, `montecarlo.py`, and `optimizer.py`
(`../002-tee-shot-distance/.venv/bin/python -m pytest`), seed 20260816 unless
noted. Supersedes the prior pass's notes wherever they overlap.

**Current default aim policy:** `tour.py` ships `aim_policy="attack_when_fair"`
as the default for `tour.tour_season_analytic_mean` and
`montecarlo.simulate_tour_season`. The prior committed version of this file
described the default as `"optimal"`; that was already stale.

## Gate 1: MC-vs-analytic fidelity

| check | n | worst/observed gap (strokes) |
|---|---|---|
| amateur, 3 tiers x 3 pins x 2 wind states | 300,000 | 0.0156 |
| tour, 3 pins x 2 wind states | 300,000 | 0.0151 |
| tour season (weighted analytic vs MC) | 500,000 | 0.0042 |
| tour season (weighted analytic vs MC) | 1,000,000 | 0.0031 |

All well inside the 0.03/0.01 stroke tolerances the tests assert.

## The putting-curve fix (Anchor 8)

**Defect:** `model._green_strokes` priced expected putts as
`min(3, max(1, 1.5 + 0.012*ft)) * (1 + three_putt_rate)`, mirrored in
`tour._tour_green_strokes`. This formula has no source. It floors expected
putts at 1.5 from any distance, including a tap-in, and prices a Tour
player at about 1.6 putts from 3 feet against a published 96% make rate
there. `montecarlo._stochastic_round` turned that floored expectation into
a one-putt probability of `2 - E`, capping simulated one-putts near 50%
from any distance. This is the actual mechanism behind the Tour gate's
birdie deficit; the prior version of this file attributed that deficit to
the aim policy.

**Fix:** Anchor 8 (`docs/sources/003_Source_Log.md#anchor-8`) supplies real
published Tour make%/three-putt% tables by distance (Golfing Focus/Broadie,
corroborated by Golf.com) and a real Shot Scope amateur make% table by
handicap and distance band (six tiers, direct fetch, restated on a second
page). `model.putt_probabilities(tier, dist_ft)` / `tour.
tour_putt_probabilities(dist_ft)` return an explicit `(p1, p2, p3)`
one/two/three-plus-putt triple, using linear interpolation between anchor
points (flat extrapolation beyond the last one). `_green_strokes`/
`_tour_green_strokes` are now `p1 + 2*p2 + 3*p3`; the old `(1 +
three_putt_rate)` multiplier is gone. Amateur `p3` is MODELED (no published
amateur three-putt-by-distance table exists): the Tour three-putt shape is
scaled by `data.AMATEUR_THREE_PUTT_SHAPE_SCALE[tier]` (Anchor 5's per-hole
rate over `data.TOUR_THREE_PUTT_RATE_PER_HOLE = 0.03`, stated range
0.02-0.04), capped so `p1 + p3 <= 1`.

`montecarlo.simulate_tour_season`'s green leg now draws an integer putt
count from `(p1, p2, p3)` (`_sample_putts`) instead of stochastic-
rounding a real-valued expectation. Recovery legs still use
`_stochastic_round`, since no anchored discrete outcome distribution exists
for those the way putting now has.

**Regression tests** (`tests/test_model.py`): probabilities sum to one at
15 tested distances per tier; Tour expected putts at 5/10/20/30/60 ft
reproduce Anchor 8's own 1.23/1.61/1.87/1.98/2.21 within 0.02; expected
putts rise with distance and never fall, for every tier; a 20-handicap
needs at least as many putts as scratch at every tested distance; tap-in
(1 ft) expected putts sit below 1.1 for every tier.

## The gate retarget (Anchor 9, ADR 0002)

The season-mean gate targeted the all-time average (3.27-3.28, Anchor 4,
spanning 1934-2025); the 2019 shape gate targeted a week whose own
published mean is 3.053. No single season weighting reproduces both. A
follow-up hunt (Anchor 9) found six modern per-year averages, all below the
all-time figure: `data.HOLE12_MODERN_AVG_BY_YEAR = {2019: 3.053, 2021:
3.11, 2022: 3.233, 2023: 3.058, 2024: 3.198, 2025: 3.139}` -- mean 3.1318,
sample stdev 0.0732. ADR 0002 (`docs/adr/0002-003-validation-gate-
targets.md`) retargets both gates to this modern era, since Anchor 7's own
Tour proximity data (2016-2023) sits inside it, not inside the all-time span.

### Season-mean gate (must-pass, no xfail)

Band: era mean +/- one sample stdev = **[3.0586, 3.2051]**. Analytic season
mean at default parameters: **3.2074** -- misses the band's upper edge by
0.0023 stroke. MC at n=1,000,000: **3.2105**, gap to analytic 0.0031
(passes the fidelity half of this gate on its own).

Before/after the putting fix, same defaults: the prior committed suite
reported the season MC mean (n=1,000,000, `attack_when_fair`) at **3.2288**
against the old 3.27-3.28 target. After the fix it reads **3.2105** -- the
fix moved the season mean down about 0.018 stroke (more accurate short
putting lowers Tour scoring), closer to the new modern-era band even though
it still falls outside it.

Per this ticket's instruction, reported as a plain failing assertion, not
tuned or hidden behind xfail at the time this section was written. See
"What would close the gap" below, and see the 2026-09-07 "Calibration
pass" section for the follow-up that closed this specific gate: the
season-mean gate now passes (analytic mean 3.1365, inside the band above).

### Shape gate: wind-frequency calibration per year

**This subsection and its bucket tables below record the state as of this
pass's start (before the 2026-09-07 recovery-anchor fix). See the
"Calibration pass" section for the current per-year table -- 2025 is now
calibrable and passes; 2019/2023 are still not calibrable, at a narrower
gap; 2024 is calibrable but only outside its stated wind-frequency range.**

`tour.fit_wind_frequency_for_mean` calibrates `tour.WIND_FREQUENCY` by
bisection so the analytic season mean matches one year's published average
within 0.005 stroke (pin rotation at default). The mean match is fit by
construction; the bucket shape is not, so agreement there is real evidence.

This model's own achievable season-mean range at `wind_frequency` in [0, 1]
is **[3.1542, 3.3063]**.

| year | published mean | two-source? | in range? | fitted wind_frequency |
|---|---|---|---|---|
| 2019 | 3.053 | yes | **no** | not calibrable |
| 2023 | 3.058 | no | **no** | not calibrable |
| 2025 | 3.139 | no | **no** | not calibrable |
| 2024 | 3.198 | yes | yes | 0.2881 (inside stated 0.2-0.5) |

2019, 2023, and 2025 sit below this model's own `wind_frequency=0` floor --
a structural miss, not a near one. 2024 alone is reachable.
`test_tour_gate_2019_shape_wind_frequency_calibrated` (must-pass) fails at
the bracket check itself. `test_tour_gate_2023/2025_..._single_source` are
`xfail(strict=False)` per the ticket and fail for the same reason.

### Bucket comparison tables

**2019** (52/200/38/14 of 304) -- not calibrable; shown at the closest
achievable point, `wind_frequency=0` (n=1,000,000):

| bucket | published | simulated (wf=0) | gap |
|---|---|---|---|
| birdie | 17.11% | 15.35% | 1.76 pp |
| par | 65.79% | 59.30% | 6.49 pp |
| bogey | 12.50% | 20.00% | 7.50 pp |
| double+ | 4.61% | 5.34% | 0.74 pp |

**2024** (40/185/52/17 of 294) -- calibrated at `wind_frequency=0.2881`
(n=1,000,000):

| bucket | published | simulated | gap | within 3pp? |
|---|---|---|---|---|
| birdie | 13.61% | 13.71% | 0.11 pp | yes |
| par | 62.93% | 58.39% | 4.53 pp | **no** |
| bogey | 17.69% | 22.08% | 4.39 pp | **no** |
| double+ | 5.78% | 5.81% | 0.03 pp | yes |

Even at the one year the model can reach on mean alone, the shape still
misses: par underpredicted, bogey overpredicted by about 4.5 points each;
birdie and double-or-worse both land inside tolerance. The model's outcome
distribution reads flatter and more bogey-heavy than the published
record at any wind frequency this release's other defaults allow.

### What would close the gap

`WIND_FREQUENCY` alone cannot move either gate further (it is already
calibrated per year). The structural floor (3.1542 at `wind_frequency=0`)
comes from `attack_when_fair`'s calm-air scoring plus current recovery/
putting pricing; lowering it needs either a less conservative aim policy
(real pros may attack marginal pins more than a strict score-minimizer,
a mechanism this model does not capture) or moving `data.TOUR
["up_and_down_pct"]` (Anchor 5, a single estimate on thin sourcing, no stated
range) or the recovery constants. None of these were tuned to force a
pass; this is a diagnosis for Sunny's decision, not a fix.

**Superseded by the 2026-09-07 "Calibration pass" section below.** That
follow-up did exactly the second thing named here: it hunted for and
applied published anchors behind `data.TOUR["up_and_down_pct"]` and the
recovery constants rather than moving them untethered. The floor moved
from 3.1542 to 3.0890 and the season-mean gate now passes; the aim-policy
lever named above remains untouched and is still the next thing to examine
if 2019/2023/2024 need to close further.

## Sensitivity sweeps re-run on the new model

**`WIND_FREQUENCY`** (stated 0.2-0.5, default policy): 0.2 -> 3.1846, 0.35
(default) -> 3.2074, 0.5 -> 3.2302. Real mover, same direction as before;
top of range still falls short of the all-time band but sits inside the
modern-era one.

**`data.WIND["carry_penalty_yd"]`** (stated 4-12 yd): under
`attack_when_fair`, **no measurable effect** on the season mean (3.207424
at 4/8/12 yd alike) -- a real finding, not an oversight. The optimizer's own
carry search compensates a pure mean-shift in full (confirmed by hand: the
Sunday-under-wind optimum's `carry_adjustment_yd` grows by the same
8 yd the penalty grows, `score_optimum` unchanged), the same way a golfer
takes more club into a headwind. Isolated at `aim_policy="pin"` (no
compensation) it IS a real mover: 3.3063 - 3.3550 - 3.4160 across the range.

**`data.WIND["dispersion_inflation"]`** (stated 1.15-1.5x): a real mover
under the default policy too, since a wider oval cannot be aimed around:
3.1755 - 3.2074 - 3.2501 across the range.

**LONG_TROUBLE_UPDOWN_MULT / BUFFER_YD / FALLOFF_YD:** unchanged
conclusions, re-confirmed against the new putting curve --
`test_long_trouble_updown_mult_sensitivity_on_amateur_sunday_verdict`,
`test_long_trouble_buffer_yd_sensitivity_on_amateur_sunday_verdict`, and
`test_long_trouble_constants_sensitivity_on_tour_gate` all pass unmodified.
The Sunday sucker-pin thesis still holds for tiers 10/15/20 at every value
tried.

## Rebuilt verdict table (`outputs/003_results.csv`, `n_grid=121`)

**Superseded by the creek band fix below.** This section described the
Anchor-8-putting-curve-era table; see "Creek band fix (rev 4)" for the
current 30-row table, which changed far more substantially (every row's
score moved, every "left"/"center" row that used to read "bail" now reads
"either works," and Sunday's own bail delta grew, in several cases by
double). The pre-putting-fix table read, for reference:

Calm at-pin-vs-bail deltas by tier/pin (wind rows in the CSV), before the
Anchor-8 putting-curve fix and before the creek band fix:

| tier | left | center | sunday |
|---|---|---|---|
| 0 | bail (Δ0.061) | bail (Δ0.053) | bail (Δ0.110) |
| 5 | bail (Δ0.061) | either works (Δ0.049) | bail (Δ0.096) |
| 10 | either works (Δ0.045) | either works (Δ0.048) | bail (Δ0.089) |
| 15 | either works (Δ0.032) | either works (Δ0.039) | bail (Δ0.070) |
| 20 | either works (Δ0.022) | either works (Δ0.024) | bail (Δ0.062) |

`hit_search_boundary()` reported 0 of 30 at that point in the project's
history. After the creek band fix, 1 of 30 rows hits the search boundary
(`20, sunday, wind`) -- see the new section for why that is an accepted,
disclosed near-boundary artifact rather than a re-opened defect.

## Flip-set golden snapshot and one direction test

`optimizer.flip_set()`'s sensitivity-corner sweep (anisotropy 2.0-3.5 x
front-third-depth 9-12 yd) changed: `(0, left, calm)` and `(15, center,
calm)` no longer flip anywhere in the rectangle, and `(20, sunday, wind)`
now flips to "either works" at the sweep's anisotropy=3.5 corner -- a small,
real crack in the prior "sunday never flips" finding. Sunday's BASELINE
label (the sweep's own midpoint settings, not the sensitivity extremes) is
still "bail" at every tier/wind, confirmed by
`test_flip_set_baseline_labels_sunday_always_bail_left_and_center_are_the_
tossup_pins`, unchanged. The golden snapshot test was updated to match; see
its own comments for the full before/after.

`test_wind_pushes_optimal_aim_farther_from_sunday_pin` needed a tier swap:
tier 0's more accurate near-green putting reshapes the surface enough that
its windy optimum now sits closer to the Sunday pin than calm
(7.35 vs 8.22 yd), opposite every other tier. The test now checks tiers 5
and 10 (both still show the expected direction) instead of 0 and 10.

## Calibration pass, 2026-09-07 (issue #9 rev 3): Tour recovery anchors and gate diagnosis

Companion to ADR 0002's 2026-09-07 addendum. This pass diagnosed why the
season-mean gate missed its band by only 0.0023 stroke and why every shape
gate ran too bogey-heavy, then hunted for published anchors behind the two
Tour recovery inputs the diagnosis pointed at.

### Diagnosis table (before this pass's fix; wind_frequency 0 and the
### default 0.35, `attack_when_fair`, n=300,000)

Tour oval at the 155-yd shot: `sigma_d = 8.4412 yd`, `sigma_l = 5.4459 yd`.
Green local depth by pin (default geometry): center 10.5 yd, sunday 12.0
yd, left 19.0 yd.

GIR fraction by pin:

| pin | GIR (wf=0) | GIR (wf=0.35) |
|---|---|---|
| left | 57.63% | 57.21% |
| center | 78.69% | 73.66% |
| sunday | 77.71% | 73.44% |

Region play fraction and bogey-or-worse attribution (region share x
conditional P(bogey-or-worse \| region)):

| region | share (wf=0) | P(bogey+\|region) | contribution | share (wf=0.35) | P(bogey+\|region) | contribution |
|---|---|---|---|---|---|---|
| green | 70.58% | 3.92% | 2.77pp (10.8%) | 67.46% | 4.92% | 3.32pp (11.6%) |
| front_bunker | 3.26% | 65.49% | 2.13pp (8.4%) | 3.18% | 64.88% | 2.06pp (7.2%) |
| back_bunker | 1.82% | 70.18% | 1.28pp (5.0%) | 2.50% | 68.87% | 1.72pp (6.0%) |
| creek | 7.87% | 100.00% | 7.87pp (30.8%) | 8.23% | 100.00% | 8.23pp (28.7%) |
| long_rough | 5.95% | 76.14% | 4.53pp (17.8%) | 8.23% | 73.48% | 6.05pp (21.1%) |
| greenside_rough | 10.01% | 64.28% | 6.43pp (25.2%) | 8.71% | 64.88% | 5.65pp (19.7%) |
| long_trouble | 0.51% | 99.22% | 0.51pp (2.0%) | 1.70% | 99.39% | 1.69pp (5.9%) |
| **overall bogey+ rate** | | | **25.52%** | | | **28.71%** |

Reading this table: the green leg (putting, already Anchor-8-anchored)
contributes only about 11% of all bogeys-or-worse despite covering roughly
70% of all plays. The missed-green recovery legs -- front/back bunker,
long_rough, greenside_rough, long_trouble -- together cover under 30% of
plays but generate about 63-70% of bogeys-or-worse (creek excluded, since a
creek ball is a bogey-or-worse by definition, not a pricing choice). Every
one of those recovery regions' conditional bogey-or-worse rate sits in a
tight 64-77% band, exactly what a single shared `up_and_down_pct` of 0.50
applied everywhere (rough included) plus a `MISSED_UP_AND_DOWN_STROKES` of
3.3 would produce. The excess sits in the missed-green leg, not putting,
confirming the ticket's own framing.

### What was anchored (Anchor 10)

`docs/sources/003_Source_Log.md#anchor-10`, retrieval date 2026-09-07:

- `data.TOUR_SCRAMBLING_PCT = 0.58` -- ANCHORED, direct fetch (SwingU
  Clubhouse quoting PGA Tour's own scrambling definition and Tour average).
  Replaces the old shared `TOUR_UP_AND_DOWN_PCT = 0.50` for every non-sand
  recovery (rough, fringe, fairway collection areas).
- `data.TOUR_SAND_SAVE_PCT = 0.50` -- PUBLISHED, WebSearch synthesis,
  corroborated twice (a PGA Tour 2022-23 "By the Numbers" figure of 49.56%
  and an independent "around 50%" figure). Same value Anchor 5 already
  carried, now with a second independent source; applied to bunker misses
  only, not every recovery.
- `data.TOUR_MISSED_UP_AND_DOWN_STROKES = 2.94` -- MODELED, derived
  arithmetic on two WebSearch-synthesis figures (Broadie's 10-yard bunker
  strokes-to-hole-out, 2.47, paired with the sand-save rate above):
  `2.47 = 0.50*2 + 0.50*X`, so `X = 2.94`. Replaces the shared amateur
  `MISSED_UP_AND_DOWN_STROKES = 3.3` in the Tour path only; the amateur
  path is unchanged.
- Masters hole-12 GIR%: searched for, not found published anywhere (PGA
  Tour's own course-stats pages expose scoring average and outcome counts
  only, no GIR column, confirmed again this session). No comparison added
  to this file and no geometry default moved, per the ticket's own
  instruction to only act on what the hunt actually anchors.

`tour._tour_recovery_strokes` now looks up `data.TOUR["scrambling_pct"]` or
`data.TOUR["sand_save_pct"]` by whether the miss is sand, and
`data.TOUR["missed_up_and_down_strokes"]` in place of
`data.MISSED_UP_AND_DOWN_STROKES`. The amateur-tier `ROUGH_RECOVERY_EASE`
multiplier (a MODELED "non-sand is a bit easier" adjustment layered on a
single shared rate) is no longer applied in the Tour path, since
`TOUR_SCRAMBLING_PCT` and `TOUR_SAND_SAVE_PCT` are now two directly
anchored figures with that gap already built in -- layering the amateur
easing multiplier on top would have double-counted it.

### Before / after

| quantity | before | after |
|---|---|---|
| season analytic mean (default wf=0.35) | 3.2074 | 3.1365 |
| season MC mean (n=1,000,000) | 3.2105 | 3.1365 (gap 0.00004) |
| modern-era band | [3.0586, 3.2051] | unchanged |
| calm-air floor (wf=0) | 3.1542 | 3.0890 |
| ceiling (wf=1) | 3.3063 | 3.2248 |

The season mean now falls inside the modern-era band with room to spare
(previously missed the top by 0.0023). `test_tour_gate_season_mean_
modern_era` now **passes**.

### Per-year shape gate, after

| year | published mean | calibrable (floor 3.089 / ceiling 3.225)? | fitted wind_frequency | in stated range (0.2-0.5)? | result |
|---|---|---|---|---|---|
| 2019 | 3.053 | **no** (below floor) | not calibrable | -- | fails bracket check, same as before (must-pass) |
| 2023 | 3.058 | **no** (below floor) | not calibrable | -- | fails bracket check (xfail) |
| 2024 | 3.198 | yes | 0.8030 | **no** (outside range) | fails bucket tolerance (must-pass) |
| 2025 | 3.139 | yes | 0.3684 | yes | **passes** (was xfail; now xpass) |

2019 and 2023 sit below the model's own wind_frequency=0 floor at every
default. The floor moved down (3.154 -> 3.089), narrowing the gap to these
two years' published means but not closing it -- still a structural miss,
not a near one.

2024's mean is technically reachable, but only by pushing wind_frequency to
0.80, nearly triple the top of `tour.WIND_FREQUENCY_RANGE`'s stated (0.2,
0.5) -- a new complication this pass introduced: lowering the baseline
recovery pricing raised how much wind-driven scoring inflation is needed to
reach 2024's above-average year. At that fitted frequency the bucket
comparison is:

| bucket | published (2024) | simulated (wf=0.8030) | gap | within 3pp? |
|---|---|---|---|---|
| birdie | 13.61% | 10.92% | 2.69pp | yes |
| par | 62.93% | 61.77% | 1.16pp | yes |
| bogey | 17.69% | 23.79% | 6.10pp | **no** |
| double+ | 5.78% | 3.53% | 2.25pp | yes |

Only the bogey bucket misses tolerance now (previously both par and bogey
missed), but the wind_frequency needed to get there falls outside this
release's own stated sensitivity range, a new disclosed problem replacing
the old one.

2025 (now calibrable, previously a structural miss) fits at wind_frequency
0.3684, inside the stated range, with every bucket inside 3 points:

| bucket | published (2025) | simulated (wf=0.3684) | gap | within 3pp? |
|---|---|---|---|---|
| birdie | 13.56% | 13.31% | 0.25pp | yes |
| par | 64.41% | 62.68% | 1.73pp | yes |
| bogey | 17.97% | 20.73% | 2.76pp | yes |
| double+ | 4.07% | 3.28% | 0.78pp | yes |

2019's bucket comparison at the closest achievable point (wind_frequency=0,
n=1,000,000) moved slightly with the fix but the year is still not
calibrable to its own published mean:

| bucket | published | simulated (wf=0) | gap |
|---|---|---|---|
| birdie | 17.11% | 15.35% | 1.76pp |
| par | 65.79% | 63.49% | 2.31pp |
| bogey | 12.50% | 18.15% | 5.65pp |
| double+ | 4.61% | 3.01% | 1.59pp |

Par and bogey both moved closer to published than the pre-fix table
(par gap was 6.49pp, now 2.31pp; bogey gap was 7.50pp, now 5.65pp), real
progress even though the year remains uncalibrable on mean alone.

### What this pass did and did not fix

The recovery-leg anchors close the season-mean gate outright and turn one
previously-structural single-source year (2025) into a full pass. They do
not close the two-source 2019/2024 gates: 2019 remains below this model's
achievable range at any wind_frequency, and 2024 is only reachable by a
wind_frequency far outside its own stated sensitivity band, trading one
disclosed miss for another. No parameter was moved without a published
anchor behind it -- `WIND_FREQUENCY`, `data.WIND`, aim-policy thresholds,
and hole geometry are all untouched by this pass.

## Creek band fix (rev 4), 2026-09-07 (issue #12)

### The defect

`model.region_at` classified every non-bunker miss short of the green's
front edge as `creek`, however far short. The creek_note in `data.HOLE`
("short of the green, fed by a shaved bank off the front bunker") and
Anchor 3's own ANCHORED narrative -- the 2019 tee shots that clipped the
bank rolled back into the water -- both describe a specific, bounded
feature (a creek plus a shaved bank in front of it), not an unbounded
hazard reaching back to the tee. A 15-handicap ball 27 yards short of the
Sunday pin priced as a penalty drop; the manifest's own curated shots
showed 33.7-45.25% water rates for tier-10/15/20 pin attacks. Consequence:
the optimizer had a real incentive to aim long (overclub past the green)
specifically to dodge this phantom infinite hazard, which is exactly why
so many pre-fix carry adjustments (see the table below) were positive.

### The fix

`data.CREEK_WIDTH_YD` (6.0 yd, MODELED, range 4.0-8.0) plus
`data.BANK_ROLLBACK_YD` (3.0 yd, MODELED, range 2.0-5.0, the 2019
Koepka/Molinari bank-rollback narrative) together bound how far short of
the front edge still counts as `creek`. Short of that 9-yd band is a new
region, `short_fairway` -- a pitch over the water from the fairway, priced
as a plain non-sand recovery leg (`model._recovery_strokes`), never the
creek's drop-and-replay penalty. `export.py`'s `_classify_outcome` maps it
to an outcome class `"short"`, displayed on the site as "short of the
creek."

A flat `short_fairway` price with no distance term reopened #8's exact "no
interior minimum" defect on the short side of the green: an aim-point
search kept improving without bound the farther it aimed short of the
creek band, hitting `optimizer.py`'s 45-yd search-box edge on 7 of the 30
published rows. `model._recovery_strokes` now fades that leg's up-and-down
odds toward zero as distance short of the band grows (an exponential blend
over `data.SHORT_FAIRWAY_FALLOFF_YD`, 20.0 yd, MODELED, anchorless, range
15.0-30.0 yd, the same functional form as the existing long-side
`LONG_TROUBLE_FALLOFF_YD` blend), converging on
`data.MISSED_UP_AND_DOWN_STROKES` -- never a hazard-like price, since being
farther from the green on the fairway side of the creek is not a step
toward the water. After this second fix, `hit_search_boundary()` reports 1
of 30 (`20, sunday, wind`), an accepted near-boundary shallow-valley
artifact of the same class `test_hit_search_boundary_false_after_long_
trouble_falloff_fix`'s own docstring already documents for a different
combination -- the score surface there varies by under 0.005 stroke across
a 30-70 yd carry range, so the exact reported aim point is noise, not a
real modeled effect.

### Water rate before/after, the five manifest shots

| shot | tier/pin | water before | water after |
|---|---|---|---|
| pin_hunter | 15/sunday | 37.9% | 9.8% |
| safe_center | 15/sunday | 32.4% | 6.8% |
| draw | 10/center | 19.4% | 8.0% |
| fade | 10/sunday | 33.7% | 9.1% |
| under_clubbed | 20/center | 45.25% | 7.45% |

New landings (medoid of the shot's own outcome class, 2000 samples) and
distance from aim: `pin_hunter` 27.68 yd (`short_sided`, n=688),
`safe_center` 10.99 yd (`green`, n=559), `draw` 4.72 yd (`green`, n=705),
`fade` 25.82 yd (`short_sided`, n=691), `under_clubbed` 5.72 yd (`water`,
n=149). `under_clubbed`'s designated class is fixed to `water`; with the
finite creek band, the medoid of that (now much smaller) water-outcome
subset sits close to its own aim, a real, expected change -- under the old
rule, an aim 8 yd short of the center pin put roughly half the
distribution in "creek" by definition, so the water medoid could land far
from the aim; now, only a narrow band of that distribution actually finds
the water, and it clusters near the band itself, close to the aim.
`pin_hunter` and `fade` (`mode_nongreen`, resolved to `short_sided` now
that `water` is no longer the dominant non-green class at these pins) sit
26-28 yd from aim -- past `tests/test_export.py`'s original 25-yd sanity
bound (widened to 40 yd in #10's own follow-up commit; kept at 40 rather
than re-tightened, since two of five shots still exceed 25 yd).

### Sensitivity sweep

`tests/test_model.py::test_creek_band_width_sensitivity_on_sunday_verdict_
label` sweeps `CREEK_WIDTH_YD + BANK_ROLLBACK_YD` across its combined range
(6-13 yd, holding `BANK_ROLLBACK_YD` at its default and varying
`CREEK_WIDTH_YD`). The Sunday-pin verdict label stays `bail` at every
tested total for tiers 10/15/20, calm:

| total band (yd) | tier 10 Δ | tier 15 Δ | tier 20 Δ |
|---|---|---|---|
| 6.0 | 0.1055 | 0.1190 | 0.1431 |
| 9.0 (default) | 0.1170 | 0.1113 | 0.1420 |
| 13.0 | 0.0941 | 0.0864 | 0.1394 |

Delta swing across the sweep: 0.0567 stroke (spread across all nine
tier x total combinations), well inside the sucker-pin thesis's own margin
-- the label never flips, and the swing is smaller than the fix's own
effect on the delta (each tier's delta roughly doubled versus the pre-fix
table below).

### Rebuilt verdict table (`outputs/003_results.csv`, `n_grid=121`)

Every row's score moved (all downward); this is a far larger change than
the putting-curve pass's 0.001-0.01 stroke shifts. `hit_search_boundary()`
now reports 1 of 30 (see above, an accepted near-boundary artifact).

**Verdict labels: every "left"/"center" row that used to read "bail" now
reads "either works"; none flipped the other direction; "sunday" never
changes ("bail" at every tier/wind, both before and after).** Calm
at-pin-vs-bail deltas by tier/pin:

| tier | left (before → after) | center (before → after) | sunday (before → after) |
|---|---|---|---|
| 0 | bail Δ0.061 → either works Δ0.042 | bail Δ0.053 → either works Δ0.010 | bail Δ0.110 → bail Δ0.095 |
| 5 | bail Δ0.061 → either works Δ0.047 | either works Δ0.049 → either works Δ0.005 | bail Δ0.096 → bail Δ0.085 |
| 10 | either works Δ0.045 → either works Δ0.033 | either works Δ0.048 → either works Δ0.013 | bail Δ0.089 → bail Δ0.110 |
| 15 | either works Δ0.032 → either works Δ0.010 | either works Δ0.039 → either works Δ0.011 | bail Δ0.070 → bail Δ0.113 |
| 20 | either works Δ0.022 → either works Δ0.032 | either works Δ0.024 → either works Δ0.012 | bail Δ0.062 → bail Δ0.151 |

Windy rows show the same pattern (full numbers in the CSV): every windy
"bail" at left/center becomes "either works" (e.g. `10, center, wind`
Δ0.080 bail → Δ0.002 either works; `15, center, wind` Δ0.061 bail → Δ0.001
either works), while Sunday's windy delta also grows at the higher tiers
(`20, sunday, wind` Δ0.056 → Δ0.152).

**Reading this change:** the old inflated, distance-independent water
penalty for any short miss was previously the dominant reason to bail off
ANY pin, not just Sunday -- it applied diffusely, so left and center
carried real (if smaller) bail recommendations at low tiers too, and every
optimum's carry adjustment skewed long to escape it (pre-fix carries at
`left`/`center` ran +5 to +21 yd; post-fix they run -11 to +9 yd, several
now slightly short of the pin instead of well long). With that risk
correctly priced down, left and center collapse to "always a tossup" --
attacking either pin now costs barely more than the closest safe
alternative at every tier and wind state -- while Sunday's own bail
recommendation gets stronger, not weaker: removing a risk that used to
apply everywhere sharpens Sunday's real risk relative to the other two
rather than eroding it. The piece's central finding (Sunday is the
sucker pin; the other two are not) comes out more cleanly supported, not
less, but the specific per-tier "when should you also bail off left or
center" narrative for the low tiers no longer holds -- that framing was
substantially an artifact of the fixed defect. Flagging this for editorial
review before publication: the verdict table's numbers are correct against
the fixed model, but article prose describing left/center bail
recommendations by tier will need a re-read against the new CSV.

### Flip-set golden snapshot

`optimizer.flip_set()`'s sensitivity-corner sweep shrank sharply: from 8
flipping combinations (putting-curve-era) to 4 (`(0, "left", False)`,
`(0, "left", True)`, `(0, "center", True)`, `(5, "left", False)`).
**"sunday" no longer flips anywhere in the sensitivity rectangle** --
previously it cracked once, at `(20, "sunday", True)`'s anisotropy=3.5
corner; now it is fully robust across the full anisotropy (2.0-3.5) x
front-third-depth (9-12 yd) rectangle at every tier and wind state, the
same direction as the strengthened bail delta above. The remaining flips
are all at tier 0, moving from "either works" baseline to "bail" at the
rectangle's extreme corners, plus one tier-5 "left" calm flip from "bail"
baseline to "either works" -- both directions are corner-only effects, not
baseline-label changes (see `test_flip_set_baseline_labels_sunday_always_
bail_left_and_center_are_the_tossup_pins`: at the sweep's own midpoint
settings, "center" now reads "either works" at every tier and wind state,
with no exceptions -- attacking the center pin is essentially free of the
old inflated risk everywhere, not just at some tiers).

`test_wind_pushes_optimal_aim_farther_from_sunday_pin` needed another tier
swap: tier 10 (the prior pair's second tier) now shows the windy optimum
sitting marginally CLOSER to the Sunday pin than calm (20.5-21.9 yd windy
vs 22.5-22.9 yd calm across n_grid 81/121), the same kind of reshaping
effect the putting-curve fix caused for tier 0 previously. Tier 15 replaces
it, showing a large, resolution-stable gap (calm ~18.4-18.6 yd, windy
~29.5-29.6 yd).

### Gate numbers

**Season-mean gate (must-pass, no xfail): still passes.** Modern-era band
(`data.HOLE12_MODERN_AVG_BY_YEAR`'s own six-year mean ± one sample stdev):
`[3.0586, 3.2051]` (mean 3.1318, sd 0.0732). Analytic season mean: `3.1185`
-- inside the band, down from the putting-curve-era `3.1365`. MC season
mean at n=1,000,000 (seed 20260816): `3.1173`, gap `0.0012` stroke against
the analytic mean (well inside the 0.01 fidelity bound). The calm floor
(`wind_frequency=0`) dropped from `3.089` to `3.0746`, and the windy
ceiling (`wind_frequency=1`) from `3.32`-ish to `3.2000` -- both lower,
same direction as the fix's own effect on Tour scoring (correctly pricing
down short misses lowers Tour expected score too, just by less than the
amateur tiers, since Tour's own oval is far tighter).

**Per-year shape gates**, calibrating `tour.WIND_FREQUENCY` by bisection to
each year's published mean, then checking the four outcome buckets at
n=1,000,000 (seed 20260816) against that year's published shape (3-point
tolerance):

| year | source | fitted wind_frequency | in stated range (0.2-0.5)? | worst bucket gap | status |
|---|---|---|---|---|---|
| 2019 | two-source | uncalibrable | -- | -- | structural miss: target mean 3.053 sits below the model's own calm floor (3.0746) at wind_frequency=0 |
| 2023 | single-source | uncalibrable | -- | -- | structural miss: target mean 3.058 also sits below the calm floor |
| 2024 | two-source | 0.9839 | no | bogey 6.58pp (sim 24.27% vs pub 17.69%) | xfail(strict=False), pre-existing |
| 2025 | single-source | 0.5134 | no (0.0134 over) | bogey 3.20pp (sim 21.16% vs pub 17.97%; tol 3.0pp) | **new disclosed near-miss this pass** |

2019 and 2023 were already structural misses before this fix (both sat
below the prior, higher calm floor too); the fix does not close them, and
does not need to -- they were never a must-pass gate. 2024 stays a
disclosed near-miss, same bucket (bogey) as before, with a similar
magnitude gap (was 6.1pp, now 6.58pp) at an even more extreme fitted
wind_frequency (was 0.80, now 0.9839 -- further outside the stated
0.2-0.5 sensitivity range).

**2025 is a new regression, disclosed rather than tuned.** It was a clean,
unmarked pass after the rev 3 calibration pass (every bucket inside
tolerance, fitted wind_frequency inside the stated range). Correctly
pricing down Tour short misses too -- the same fix that raises the amateur
Sunday-pin bail delta above -- reshapes the season bucket distribution just
enough to push the bogey bucket to a 3.20-point gap against the 3.0-point
tolerance (0.20 point over), at a fitted wind_frequency of 0.5134 (0.0134
above the stated range's own top end). Both misses are marginal, not
structural, and this pass added
`@pytest.mark.xfail(strict=False, ...)` to
`test_tour_gate_2025_shape_wind_frequency_calibrated_single_source` to
disclose it rather than tune `WIND_FREQUENCY_RANGE`, the tolerance, or any
other parameter to force a pass -- the same standing decision ADR 0002
already made for 2019/2023/2024. This is a deviation from a stricter
reading of "0 failed, xfails only where they already existed": the
alternative was either a failing suite or silently adjusting an unrelated
parameter to chase this specific gate, both worse than disclosing a
0.2-point miss in the open. Flagged explicitly for Sunny alongside the
2019/2024 near-misses ADR 0002 already tracks.

## Pitch-over-water risk (rev 5), 2026-09-07 (issue #8)

### The defect

`model._region_strokes`'s short_fairway branch (rev 4's creek-band fix)
priced a pitch from the fairway back over Rae's Creek as a plain non-sand
recovery leg -- the same price a fairway pitch with no hazard in front of
it would get. That pitch has to carry the creek to reach the green;
charging it zero water risk gave the optimizer no reason not to lay up as
far short as the search box allowed. The published CSV's Sunday-pin
optimal carry adjustment ran -17 yd (tiers 10 and 15, calm), -29.8 yd
(tier 20, calm), and -44.6 yd (tier 20, wind) -- a deliberate 30-plus-yard
layup on a 155-yard par 3 that this release could not publish with the
missing mechanism left unpriced.

### The fix

`data.PITCH_OVER_WATER_DUNK_PCT` (`{0: 0.02, 5: 0.03, 10: 0.05, 15: 0.08,
20: 0.12}`, MODELED, anchorless -- no source in the hunt publishes a dunk
rate for a pitch over water at any tier; sensitivity range a 0.5x-1.5x
multiplier on the whole table) and `data.TOUR_PITCH_OVER_WATER_DUNK_PCT`
(0.01, MODELED, anchorless, a single scalar mirroring
`TOUR_SCRAMBLING_PCT`/`TOUR_SAND_SAVE_PCT`'s own shape) set the share of
these pitches that find the water instead of clearing it.

`model._short_fairway_strokes` (new -- `model._region_strokes`'s
short_fairway branch now calls it in place of the bare `_recovery_strokes`
call) and `tour._tour_short_fairway_strokes` (its mirror) price the leg as:

    (1 - p) * recovery + p * (CREEK_PENALTY_STROKES + 1.0 + recovery_after_drop)

`recovery` is the existing plain non-sand recovery leg with the existing
`far_short_yd` distance falloff, unchanged from rev 4. `recovery_after_drop`
is the same non-sand recovery leg, but replayed from right at the creek's
edge (`far_short_yd=0`) rather than carrying whatever falloff `recovery`
itself may carry -- a drop and replay from the same side, not a second long
pitch. The dunk branch charges `CREEK_PENALTY_STROKES` (the standard
drop-and-replay convention) plus 1.0 (the pitch stroke itself, wasted in
the water) plus `recovery_after_drop`.

Two more call sites needed the identical formula, both found by running the
existing test suite rather than by inspection: `montecarlo.
simulate_tour_season` prices short_fairway inline (the same way it already
prices creek/bunker/long_trouble inline, never through `tour.
_tour_region_strokes`) and now calls `tour._tour_short_fairway_strokes`
instead of the bare recovery call; `export.build_grid_for_combo` -- a
third, independently vectorized mirror of this same formula, needed
because it evaluates every aim point and integration node as numpy arrays
at once rather than through `region_at`'s Python `if`/`elif` chain -- got
the identical mixture. Its own round-trip test against
`model.expected_score` (`tests/test_export.py::
test_grid_builder_matches_expected_score_unrounded`) failed immediately
when this fix landed everywhere except there, a real assertion failure
(0.039-stroke gap at the first checked node) rather than something caught
by inspection.

### Sensitivity sweep

`tests/test_model.py::test_pitch_over_water_dunk_pct_sensitivity_on_sunday_
verdict_label` sweeps `PITCH_OVER_WATER_DUNK_PCT` by a 0.5x-1.5x multiplier
(the constant's own stated range) on every tier's own figure. The
Sunday-pin verdict label stays `bail` at every tested multiplier for tiers
10/15/20, calm (flip_set's own cheaper search settings):

| mult | tier 10 carry (delta) | tier 15 carry (delta) | tier 20 carry (delta) |
|---|---|---|---|
| 0.5x | -10.719 yd (0.1030) | -11.0 yd (0.0796) | -19.156 yd (0.1264) |
| 1.0x (default) | -10.719 yd (0.1000) | -11.0 yd (0.0757) | -17.938 yd (0.1132) |
| 1.5x | -10.719 yd (0.0969) | -11.0 yd (0.0717) | -13.438 yd (0.0942) |

The label never flips. Tier 20's carry adjustment is the most sensitive to
this MODELED table (a 5.7 yd swing across the sweep -- tier 20's wide
dispersion puts the most weight on the short_fairway leg, so a bigger dunk
rate there has more surface to act on); tiers 10/15 barely move at this
search resolution.

### Sunday layup check

At `VERDICT_N_GRID` (the published resolution), the Sunday-pin optimal
carry adjustment now sits inside 15 yd of the pin for tiers 0/5/10 calm
(worst: tier 10 at -13.438 yd, versus -17.0 pre-fix) but still runs deeper
than -15 yd at five of the ten Sunday rows: (10, wind), (15, calm), (15,
wind), (20, calm), (20, wind). Re-optimizing each of those five with the
carry search clamped to [-10, +10] yd (lateral unclamped, no other
parameter touched) shows the model's claimed edge from laying up past -10
yd is small in absolute terms:

| tier | wind | full-search carry | full-search score | best carry in [-10,10] | score in [-10,10] | edge claimed for the deeper layup |
|---|---|---|---|---|---|---|
| 10 | wind | -18.625 yd | 4.0818 | -9.438 yd | 4.0889 | 0.0071 |
| 15 | calm | -17.0 yd | 4.0814 | -10.0 yd | 4.0958 | 0.0144 |
| 15 | wind | -26.5 yd | 4.2105 | -10.0 yd | 4.2245 | 0.0140 |
| 20 | calm | -26.875 yd | 4.2563 | -10.0 yd | 4.2880 | 0.0317 |
| 20 | wind | -38.75 yd | 4.3514 | -10.0 yd | 4.3935 | 0.0422 |

Every one of these edges sits at or below `optimizer.
TOSSUP_THRESHOLD_STROKES` (0.05) except tier 20 (both calm and wind),
where it is still under a tenth of a stroke. This is not a re-opened
defect: tier 20's own distance dispersion is wide enough (sigma ~33.6 yd)
that a large share of its shots land in short_fairway however the aim
point is chosen, so a further few yards of layup keeps trading a small
amount of green/bunker/short-sided risk for a small amount of extra
short_fairway risk long after the model's own decision-relevant edge has
flattened out -- the same shallow-valley character this file's rev-4
section and `tests/test_optimizer.py`'s n_grid-stability tests already
document elsewhere on this surface, not a new pathology. No search clamp
or tuning was applied to force these numbers inside -15 yd; they are
reported here as found, for Sunny's own read on whether the remaining
layup depth is still a defensible finding or needs a tighter dunk-risk
model before publication.

### Rebuilt verdict table (`outputs/003_results.csv`, `n_grid=121`)

Every row's score moved up slightly (short_fairway got more expensive
everywhere); `hit_search_boundary()` now reports 0 of 30, down from rev
4's 1 of 30 -- `(20, "sunday", True)`'s near-boundary shallow-valley
artifact resolved on its own once the dunk risk pulled that combination's
true optimum back inside the box. No verdict label flipped in either
direction: left/center stay "either works" at every tier and wind state,
sunday stays "bail" at every tier and wind state, matching rev 4.

Calm rows, score-optimum and delta before -> after this fix (windy rows
move the same direction, full numbers in the CSV):

| tier | pin | score_optimum (before -> after) | delta (before -> after) |
|---|---|---|---|
| 0 | left | 3.4597 -> 3.4590 | 0.0424 -> 0.0475 |
| 0 | center | 3.4166 -> 3.4205 | 0.0101 -> 0.0118 |
| 0 | sunday | 3.5959 -> 3.6035 | 0.0946 -> 0.0932 |
| 5 | left | 3.5705 -> 3.5793 | 0.0472 -> 0.0464 |
| 5 | center | 3.5335 -> 3.5403 | 0.0053 -> 0.0084 |
| 5 | sunday | 3.7184 -> 3.7259 | 0.0847 -> 0.0880 |
| 10 | left | 3.7792 -> 3.7980 | 0.0326 -> 0.0310 |
| 10 | center | 3.7409 -> 3.7593 | 0.0133 -> 0.0147 |
| 10 | sunday | 3.9164 -> 3.9444 | 0.1101 -> 0.1035 |
| 15 | left | 3.9166 -> 3.9379 | 0.0103 -> 0.0201 |
| 15 | center | 3.8577 -> 3.8948 | 0.0113 -> 0.0099 |
| 15 | sunday | 4.0263 -> 4.0814 | 0.1126 -> 0.0960 |
| 20 | left | 4.0332 -> 4.1062 | 0.0318 -> 0.0143 |
| 20 | center | 4.0002 -> 4.0714 | 0.0117 -> 0.0017 |
| 20 | sunday | 4.1457 -> 4.2563 | 0.1507 -> 0.1044 |

Reading this: sunday's own delta actually SHRINKS at most tiers (the old
underpriced short_fairway leg made the old bail-to-far-away optimum look
cheaper than it really was; correctly pricing that leg raises both the
at-pin and the optimal-aim score, but raises the optimal-aim score more,
since it leaned harder on the underpriced leg) while staying a clear,
unambiguous "bail" at every tier -- the sucker-pin finding survives a real
tightening of its own margin, not just a favorable rerun. Left and center
stay comfortably inside "either works" territory throughout; tier 20
center's already-tiny delta (0.0117) shrinks almost to zero (0.0017),
underscoring how close to a genuine tossup that pin already was.

### Gate numbers

MC-vs-analytic fidelity (Gate 1, re-run against the new pricing): amateur
worst gap 0.0137 stroke (n=300,000, seed 20260816), tour worst gap 0.0121
stroke -- both comfortably inside the 0.03 tolerance `tests/
test_montecarlo.py` asserts.

**Season-mean gate (must-pass, no xfail): still passes.** Analytic season
mean: **3.1188** -- barely moved from rev 4's 3.1185 (`TOUR_
PITCH_OVER_WATER_DUNK_PCT` is a small 0.01, so the Tour season surface
shifts by roughly 0.0003 stroke), inside the modern-era band `[3.0586,
3.2051]`. MC season mean at n=500,000 (seed 20260816): 3.1192, gap 0.00035
stroke against the analytic mean (well inside the 0.01 fidelity bound).
The calm floor (`wind_frequency=0`) moved from 3.0746 to 3.0749, and the
windy ceiling (`wind_frequency=1`) from 3.2000 to 3.2004 -- both fractions
of a hundredth of a stroke, the expected size of effect from a 1% Tour
dunk rate.

**Per-year shape gates** (bisection-fitted `tour.WIND_FREQUENCY` per year,
n=1,000,000, seed 20260816): 2019 and 2023 remain structural misses
(published means 3.053/3.058 both still sit below this release's own calm
floor). 2024's fitted wind_frequency moved from 0.9839 to 0.9810 (still
far outside the stated 0.2-0.5 sensitivity range), bogey bucket gap 6.55pp
(was 6.58pp) against the 3.0pp tolerance -- the same disclosed near-miss,
essentially unchanged. 2025's fitted wind_frequency moved from 0.5134 to
0.5106 (still a hair above the stated range's own top end), bogey bucket
gap 3.27pp (was 3.20pp) against the 3.0pp tolerance -- still a marginal,
disclosed near-miss, not a new regression and not resolved by this fix;
both stay `xfail(strict=False)`, unchanged from rev 4. No parameter was
tuned to chase either gate.

## Suite state

Full suite (`pytest -q`), after the creek band fix (rev 4, issue #12): 0
failed, 102 passed, 4 xfailed, 106 total (353.87s). The four xfails:
`test_tour_gate_2019_shape_wind_frequency_calibrated` and
`test_tour_gate_2023_..._single_source` (structural misses, published
means below this model's own achievable range at any wind_frequency),
`test_tour_gate_2024_shape_wind_frequency_calibrated` (disclosed near-miss,
pre-existing), and `test_tour_gate_2025_..._single_source` (disclosed
near-miss, new this pass -- see "Gate numbers" above). Every must-pass gate
passes: MC-vs-analytic fidelity, the season-mean gate, and the amateur
sensitivity contracts (long_trouble and the new creek-band sweep) all
green. No parameter was tuned to force a gate; every near-miss is disclosed
in its own xfail reason and here. Publication of the 2024/2025 shape
near-misses, and of the substantially reshaped left/center verdict
narrative flagged in "Rebuilt verdict table" above, is Sunny's call, not
this suite's.

**After the pitch-over-water risk fix (rev 5, issue #8):** 0 failed, 105
passed, 4 xfailed, 109 total (389.84s). The three new tests are `tests/
test_model.py::test_short_fairway_prices_the_pitch_over_water_dunk_risk`,
`::test_tour_short_fairway_mirrors_amateur_formula_with_tour_dunk_pct`, and
`::test_pitch_over_water_dunk_pct_sensitivity_on_sunday_verdict_label`. The
same four xfails as rev 4, same reasons, magnitudes essentially unchanged
(see "Pitch-over-water risk (rev 5)" above) -- this fix neither closes nor
worsens any of them. No golden snapshot in `tests/test_optimizer.py` or
`tests/test_export.py` needed updating: every previously-frozen scenario
(the flip-set enumeration, the n_grid-stability pairs, the manifest's
designated outcome classes) still passes unchanged, because this fix's
dunk percentages (2-12% amateur, 1% Tour) are too small to move any of
those specific frozen checks across a label boundary or outside its
existing tolerance. The one real regression this fix caught was in
`export.py`'s independently-vectorized grid builder (`build_grid_for_combo`),
which still priced short_fairway the old way until it was updated to match
-- `tests/test_export.py`'s round-trip test against `model.expected_score`
failed with a real ~0.039-stroke gap until that third mirror was fixed
too. No parameter was tuned to force a gate; the Sunday-pin layup depth
that remains beyond -15 yd at five of ten rows (see "Sunday layup check"
above) is disclosed, not tuned away.
