# Release 003 validation notes (issue #9)

Companion to `tests/test_montecarlo.py`. Numbers below come from running
`montecarlo.py`, `optimizer.py`, and `tour.py` against the current tree
(`../002-tee-shot-distance/.venv/bin/python -m pytest`), seed 20260816
unless noted. Updated for the integration-fix pass (issues #8/#9 builder
reports, three fixes below); the original #9 sweep is superseded where it
overlaps.

## MC-vs-analytic fidelity (Gate 1)

Both harnesses reproduce their analytic surface comfortably inside a 0.03
stroke tolerance, the same discipline 002 used (002's own published gap:
0.0021, "within 0.003"). This release's model prices discrete hazard
boundaries (creek edge, bunkers, short-siding) that 002's smooth
anchor-table interpolation never had to cross, so the achieved gaps sit
wider than 002's but still comfortably inside tolerance:

| check | n | worst gap (strokes) |
|---|---|---|
| amateur, 3 tiers x 3 pins x 2 wind states | 300,000 | 0.0198 |
| tour, 3 pins x 2 wind states | 300,000 | 0.0147 |
| tour season (weighted analytic vs MC) | 500,000 | ~0.007 |

Still holds after FIX 1 (model.py's long_trouble distance falloff) and
FIX 3 (the Tour season sim's aim policy): both fixes changed pricing/aim
logic that `montecarlo.py`'s per-sample loop mirrors directly (the falloff
fix required threading `overshoot_yd` into `simulate_tour_season`'s inline
`long_trouble` branch, which the pre-fix code did not price at all), so the
MC-vs-analytic check is not a coincidence -- it is confirming the same
pricing formula runs on both paths.

## FIX 1: model.py's long_trouble distance falloff

**Defect (found by #8):** `long_trouble` pricing (misses that clear the back
bunkers by `LONG_TROUBLE_BUFFER_YD` or more) was a flat discount
(`LONG_TROUBLE_UPDOWN_MULT`) with no distance term, so expected score kept
improving without bound the farther an aim point carried past the green.
#8's optimizer search, capped at a stated 25-yd carry budget as a
workaround, still flagged 11 of 30 published verdicts as
`hit_search_boundary()=True` (bounded best-within-budget, not a converged
interior optimum) -- confirmed by hand out to a 150-yd carry adjustment
with no sign of a real optimum.

**Fix:** `model._recovery_strokes`'s trouble branch now takes `overshoot_yd`
(yards carried past the long_trouble boundary, computed per-pin and
per-lateral-position by `model._long_trouble_overshoot_yd`, since the
green's front/back edges are diagonal) and blends the leg's price from the
existing buffer-edge price toward `_creek_strokes`'s hazard-like price (the
same drop-and-replay-plus-recovery cost already charged for finding the
creek, itself built from Anchor-5 figures already in this file) as an
exponential approach:

```
blend = 1 - exp(-overshoot_yd / LONG_TROUBLE_FALLOFF_YD)
price = buffer_edge_price * (1 - blend) + hazard_like_price * blend
```

`LONG_TROUBLE_FALLOFF_YD = 15.0` yd is MODELED and anchorless (no source in
the log gives a decay distance for how quickly a deep miss in the
azalea-lined ledge gets worse) -- **stated sensitivity range (10.0, 25.0)
yd**. The two prices it blends between are both already Anchor-5-anchored;
only the decay length itself is a new invented number.

**Regression test:** `tests/test_model.py::
test_long_trouble_falloff_gives_every_tier_and_pin_an_interior_minimum`
checks expected score at +15 yd and +40 yd of carry past every pin, for
every tier -- +40 yd is never better than +15 yd anywhere in the 5-tier x
3-pin grid (30 combinations), confirming the interior minimum the pre-fix
model lacked.

**Consequence for the optimizer:** with a real interior minimum, the
optimizer's search box no longer needs to be an artificially tight cap
against an unbounded asymptote. `optimizer.DEFAULT_CARRY_RANGE_YD` moved
from 25 to **45 yd** (the front-left pin's worst case under wind, tier 20,
has its true argmin around 38 yd of carry; 45 yd leaves real margin past
that). Re-running `build_outputs.py`'s full sweep at the published
`VERDICT_N_GRID=121` resolution: **`hit_search_boundary()` now reports 0 of
30 rows** (down from 11), confirmed live and checked by
`tests/test_optimizer.py::test_hit_search_boundary_false_after_long_
trouble_falloff_fix` against the specific combination #8 flagged by hand.

## FIX 2: tossup verdict label

Added the 002 tossup convention (`site/tee-shot-distance/tool.html`'s
sandbox band: `|delta| <= 0.05` strokes reads "Either club works here") to
`optimizer.verdict_label`: `|delta| <= TOSSUP_THRESHOLD_STROKES` (0.05,
unchanged) now labels **"either works"** instead of collapsing into
"attack." "Bail" is unchanged (`delta > threshold`); "attack" is kept for
API completeness (`delta < -threshold`, which `optimize_aim`'s own search
never actually produces, since it always evaluates the pin as a candidate).

Re-labeling the full verdict table (`outputs/003_results.csv`, `n_grid=121`,
after FIX 1's falloff) surfaces a real, non-empty flip-set for the first
time (`optimizer.flip_set()`, corner sweep of anisotropy 2.0-3.5 x
front-third depth 9-12 yd): the "left" and "sunday" pins stay "bail" at
every tier and wind state, no flips anywhere in the sensitivity rectangle
(deltas 0.06-0.32 strokes, a wide margin). The "center" pin is the one
genuinely close to the tossup line: baseline flips to "either works" at
5/10/15-handicap calm and 20-handicap in both wind states (deltas 0.02-0.05
strokes), and every one of those flips to "bail" at the sensitivity
rectangle's narrow-depth corner (9 yd). Scratch calm is "bail" at baseline
(delta 0.054) and flips the other way, to "either works," at the wide-depth
corner (12 yd). Frozen as the new golden snapshot in
`tests/test_optimizer.py::test_flip_set_runs_and_matches_golden_snapshot`.

**Narrative gradient after FIX 1 + FIX 2, before the left-pin reposition
(superseded below):** the model did not confirm a "left lenient, center
tier-dependent, Sunday always a trap" three-way split -- left read as a
firm bail at every tier, on a par with Sunday. See "Left-pin reposition"
below for why and what changed.

## Left-pin reposition (this pass)

**Defect:** the coordinator flagged that the verdict table above contradicts
the release's locked pin cast (issue #5, "Pins: three, escalating" -- left
scoped as the welcoming/accessible pin). `data.PINS["left"]` placed the pin
at `front_frac=0.15`, a MODELED placement tucked against the green's front
edge (hugging the creek), which bailed harder than Sunday at every tier --
the model's honest finding given that placement, but the placement itself
failed the locked decision it was meant to implement.

**Fix:** Anchor 3 is qualitatively ANCHORED as "shallower on the right,
deeper on the left" (`docs/sources/003_Source_Log.md#anchor-3`) -- the
green's own roomier lobe sits on the left, so the accessible pin belongs
mid-depth on that lobe, not tucked against the front edge. `data.PINS
["left"]` repositioned:

| field | old (front pin) | new (mid-depth) | reasoning |
|---|---|---|---|
| `x` | -6.0 | **-10.0** | MODELED, moved further into the green's wide/deep left section (Anchor 3); plausible range -13.0 to -7.0, stays inside the green's published half-width |
| `y` | 147.5 | **148.0** | MODELED, chosen to sit near the shared green boundary's own local midpoint at x=-10 under the default geometry (front edge ~134.5, back edge ~161.0, midpoint ~147.75) |
| `front_frac` / `back_frac` | 0.15 / 0.85 | **0.5 / 0.5** | MODELED mid-depth placement; plausible sensitivity range 0.45-0.55 |
| `local_depth_yd_range` | (12.0, 16.0) | **(16.0, 22.0)** | MODELED, widened to represent the anchored "deeper on the left" claim as a roomier local pocket than a front-edge placement would have (narrower than the green's full published depth range, 20-33 yd, since this is a local pocket around one pin) |

Anchor 3's own diagonal-slope hook ("Sunday sits roughly 15 yd deeper than
a front-left pin") is a claim about a generic front-left reference
position, not necessarily wherever the named "left" pin sits -- decoupled
into a new `data._FRONT_LEFT_SLOPE_REFERENCE_X/Y` pair (values unchanged
from the retired front placement) so repositioning `PINS["left"]` cannot
quietly drag the green's ANCHORED diagonal front-edge slope
(`model._FRONT_EDGE_SLOPE_YD_PER_YD`) along with it. Sunday's own `y`
still derives from this same reference plus the ANCHORED +15 yd offset, so
Sunday's placement and the shared green geometry are completely unchanged
by this fix.

**Result:** at the pin's own position, attacking it now *beats* the
center-of-green bailout at every tier (e.g. tier 20: at-pin 4.2406 vs.
center-aim 4.2737, a −0.033-stroke edge to attacking) -- the opposite of
the pre-fix placement, where at-pin always lost to the bailout. Symmetric
`front_frac`/`back_frac` also means neither a short nor a long miss reads
as short-sided at this pin anymore (`model.region_at`), the same behavior
"center" already has; enforced by
`tests/test_model.py::test_left_pin_mid_depth_placement_is_never_short_sided`.

### Re-labeled verdict table (`outputs/003_results.csv`, `n_grid=121`, after the reposition)

| tier | left | center | sunday |
|---|---|---|---|
| 0 | bail (Δ0.061) | bail (Δ0.054) | bail (Δ0.114) |
| 5 | bail (Δ0.061) | either works (Δ0.050) | bail (Δ0.102) |
| 10 | either works (Δ0.050) | either works (Δ0.049) | bail (Δ0.099) |
| 15 | either works (Δ0.038) | either works (Δ0.040) | bail (Δ0.084) |
| 20 | either works (Δ0.029) | either works (Δ0.022) | bail (Δ0.075) |

(calm; wind rows in `outputs/003_results.csv`.) `hit_search_boundary()`
still reports **0 of 30 rows** after the reposition.

**Narrative gradient (final, this pass):** the honest read is not a clean
three-way split ("left lenient, center tier-dependent, Sunday a trap") --
it is closer to a two-way split. Left and center now read very similarly
to each other: both sit close to the tossup line, tipping between "bail"
and "either works" by tier, wind, and (per the flip-set sensitivity sweep)
exactly how the green's front-third depth is modeled, rather than one
being clearly softer than the other at every tier. Sunday is decisively
the outlier: bail at every tier and wind state (delta 0.06-0.14), never
approaching the tossup band, the trap the scoping expected. Re-labeling
`optimizer.flip_set()`'s golden snapshot after the reposition surfaces 9
flips (up from 5), split between "left" and "center" almost evenly, and
none at "sunday" -- see `tests/test_optimizer.py`'s updated golden
snapshot for the full sensitivity picture.

## FIX 3: Tour season sim aim policy

**Near miss (from #9):** the season Monte Carlo overshot the published
3.27-3.28 all-time scoring average at **3.443 strokes**, aiming every Tour
shot straight at the flag at every pin, including "sunday" (this release's
own sucker pin). The orchestrator's hypothesis: real Tour play does not aim
dead at every flag; playing away from a dangerous pin is baseline
course-management doctrine, the same logic #8's amateur optimizer already
applies.

**Fix:** `tour.tour_optimal_aim(pin, wind)` calls
`optimizer.optimize_aim_tour` (a Tour-tier sibling of `optimize_aim`,
factored out from a shared `optimizer._search_aim` so both surfaces run the
identical two-stage search) once per (pin, wind) state and caches the
result (`tour._TOUR_AIM_CACHE`, 6 states total, cleared by
`tour.clear_tour_aim_cache()` for tests that monkeypatch pricing constants).
`tour.tour_aim_point(pin, wind, aim_policy)` resolves "optimal" (new
default), "pin" (pre-fix behavior, kept for comparison), or "center"
(always the center-of-green bailout). Both `tour.tour_season_analytic_mean`
and `montecarlo.simulate_tour_season` now default to `aim_policy="optimal"`
-- the latter also needed its inline per-sample `long_trouble` pricing
branch updated to compute `overshoot_yd` (FIX 1), which it had been
skipping entirely before this pass.

**Result:** `tour.tour_season_analytic_mean()` (all other defaults
unchanged) drops from 3.443 to **3.203** strokes; MC at `n=1,000,000`
(seed 20260816) gives **3.209**. Against the 3.27-3.28 target, this cuts the
miss roughly in half (0.16-stroke overshoot -> ~0.06-0.07-stroke
undershoot) but flips its direction rather than landing inside the band.
`tests/test_montecarlo.py::test_aim_policy_optimal_reduces_season_gate_
overshoot_vs_pin` locks in the direction of this improvement as a
regression guard.

### Sensitivity sweep, season analytic mean, post-FIX-3 (`aim_policy="optimal"` unless noted)

| parameter | range checked | mean at range endpoints | verdict |
|---|---|---|---|
| `TOUR_ANISOTROPY.ratio` | 1.5 - 1.6 (stated) | 3.4415 - 3.4394 (checked at `aim_policy="pin"`, cheap) | still negligible (<0.003) |
| `LONG_TROUBLE_UPDOWN_MULT` | 0.4 - 0.7 (stated) | 3.4418 - ~3.4414 (`aim_policy="pin"`) | still negligible (<0.001) |
| `LONG_TROUBLE_BUFFER_YD` | 2 - 20 yd (swept) | 3.4435 - 3.4406 (`aim_policy="pin"`) | still negligible (<0.003) |
| `LONG_TROUBLE_FALLOFF_YD` (new, FIX 1) | 10 - 25 yd (stated) | 3.4417 - 3.4415 (`aim_policy="pin"`) | negligible (<0.001) |
| `WIND_FREQUENCY` | 0.2 - 0.5 (stated) | 3.172 - 3.235 (`aim_policy="optimal"`) | real mover, same direction as before, but **even the top of the stated range still undershoots** (3.235 < 3.27) |
| `data.WIND["carry_penalty_yd"]` | 4 - 12 yd (stated) | 3.379 - 3.513 (`aim_policy="pin"`, isolating the pricing effect) | **real mover, not swept before this pass** |
| `data.WIND["dispersion_inflation"]` | 1.15 - 1.5x (stated) | 3.422 - 3.461 (`aim_policy="pin"`) | **real mover, not swept before this pass** |

Compound check: `WIND_FREQUENCY` and both `data.WIND` severity constants at
the top of their stated ranges simultaneously (`carry_penalty_yd=12`,
`dispersion_inflation=1.5`), with `WIND_FREQUENCY` swept, `aim_policy=
"optimal"`:

| `WIND_FREQUENCY` (with WIND severity maxed) | season mean |
|---|---|
| 0.35 (unchanged default) | 3.2497 |
| 0.40 | 3.2661 |
| 0.415 | 3.2712 |
| 0.42 | 3.2729 |
| 0.43 | 3.2763 |
| 0.44 | 3.2797 |
| 0.45 | 3.2831 |
| 0.50 (top of range) | 3.3001 |

**This compound combination does reach 3.27-3.28** (roughly `WIND_FREQUENCY`
in [0.415, 0.44] with both WIND severity constants at the top of their own
stated ranges) -- every individual value stays inside its own disclosed
range. This release does **not** adopt it as the default. Reaching the
target this way requires simultaneously tuning three independently-MODELED
constants (season wind frequency, per-round carry penalty, per-round
dispersion inflation) to a narrow joint region whose only justification is
that it makes the gate assertion pass -- there is no independent evidence
(no additional anchor, no separate reasoning) pointing at that specific
combination over any other point in the same three-dimensional box. That is
the same kind of forcing this release already declined to do when the
pre-fix miss required moving a single constant outside its stated range;
staying inside three ranges at once by construction is not meaningfully
more honest, just harder to see. `TOUR_UP_AND_DOWN_PCT` still has no stated
range at all (Anchor 5's single weakly-sourced point estimate) and is left
at 0.50.

**Conclusion:** FIX 3's aim-policy change is a real, substantial, structural
improvement (roughly halves the gate's miss and is the correct mechanism
per the orchestrator's own diagnosis), but the season gate remains a
disclosed near miss on this release's own default parameters.
`test_tour_gate_scoring_average` and `test_tour_gate_2019_distribution_
shape` ship as failing, clearly-labeled gates with the new numbers and this
diagnosis chain in their assertion messages, not a silently retuned pass.

### A new distributional finding: the "optimal" aim policy suppresses birdies

The 2019-shape gate's failure mode changed character, not just magnitude.
Pre-fix (`aim_policy="pin"`), the miss was "too many bogeys/doubles, too
few pars/birdies" -- consistent with a season mean that ran too high.
Post-fix (`aim_policy="optimal"`), the season mean runs slightly *low*, but
the birdie bucket is now the single largest per-bucket gap (simulated 9.8%
vs. published 17.1%, a 7.3-point gap against a 3-point tolerance) --
bigger, not smaller, than pre-fix. Bogeys are still over-represented too
(19.4% vs. 12.5%). Read together, this suggests the model's fully
expected-score-minimizing aim policy is more conservative than how the real
Tour field plays this hole in practice: a strict score-minimizer bails off
every meaningfully dangerous pin every time, which suppresses the
close-range look-at-birdie chances real pros create by sometimes attacking
anyway (leaderboard pressure, must-make situations, a hot week, TV
moments) -- a mechanism this release's model does not attempt to capture.
Worth flagging for the article/#9's narrative chapter if the Tour
validation chapter references "how pros actually play this hole": the
model's aim policy is a lower bound on aggression, not a behavioral
prediction.

## LONG_TROUBLE sensitivity pass on amateur verdicts

The #7 review flagged `LONG_TROUBLE_UPDOWN_MULT` (0.4-0.7) and
`LONG_TROUBLE_BUFFER_YD` (no stated range; swept 2-20 yd here) as anchorless.
Checked against the release's core amateur thesis metric -- the Sunday
sucker-pin delta (`expected_score(tier, "sunday", at_pin) -
expected_score(tier, "sunday", center_aim)`) for tiers 10/15/20:

| constant | range | delta range (tier 15) | verdict |
|---|---|---|---|
| `LONG_TROUBLE_UPDOWN_MULT` | 0.4 - 0.7 | 0.0768 - 0.0795 strokes | sucker-pin thesis holds at every value; delta swings <0.003 stroke |
| `LONG_TROUBLE_BUFFER_YD` | 2 - 20 yd | 0.0777 - 0.0822 strokes | sucker-pin thesis holds at every value; delta swings <0.005 stroke |

Both constants are robust: the amateur verdicts this release publishes do
not depend on their exact anchorless value within the stated/swept ranges.
Enforced going forward by `test_long_trouble_updown_mult_sensitivity_on_
amateur_sunday_verdict` and `test_long_trouble_buffer_yd_sensitivity_on_
amateur_sunday_verdict` in `tests/test_montecarlo.py`. Re-confirmed after
FIX 1 added `LONG_TROUBLE_FALLOFF_YD` alongside these two (both existing
tests still pass unmodified against the falloff-aware pricing).
