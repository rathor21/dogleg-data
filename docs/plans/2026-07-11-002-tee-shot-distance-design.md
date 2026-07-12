# Release 002 — How Far Do You Need to Hit It? (Design Spec)

Date: 2026-07-11 · Status: approved by Sunny (decisions confirmed in session) · Author: Claude, direction by Sunny
Ship date: Monday, July 20, 2026 · Cadence context: pipeline moves to one flagship every two weeks (see pipeline doc rev 3)

---

## The question

Which club should you hit off the tee (driver, wood/hybrid, or iron) at every handicap, answered through one finding: the minimum drive distance that keeps your score at your tier's benchmark on a given par 4. Sunny's theory under test: a 10-to-20 handicap needs less distance than golf culture claims. The model prices in the approach shot the drive creates, so a 220-yard drive on a 400-yard hole gets charged for the 180-yard second shot it leaves.

One-line hook: "You don't need to hit it as far as you think. Here's the number, at your handicap."

## Decisions locked in session (2026-07-11)

1. **Pipeline slot:** this piece is the new 002, framed as tee-shot club choice. The shot-shape piece moves to 003. Full reorder lives in the pipeline doc.
2. **Baseline:** own-tier. Strokes gained zero means you played the hole like a typical golfer at your handicap. The finding reads "the distance below which driving is what costs you strokes against your peers."
3. **Second shot:** full-hole expected strokes. One number per (tier, hole length, drive distance), no double counting. A decomposition chart shows where the cost moves, but the threshold comes from the full-hole model.
4. **Model:** analytic core, Monte Carlo as a peer-review validation harness only.
5. **Tool scope at launch:** par 4s, three inputs (hole length, handicap, typical drive distance).
6. **Ship date:** July 20, 2026, holding the biweekly cadence from the July 6 launch.

## Gate outcome addendum (2026-07-11, post source hunt)

The verification gate ran and `docs/sources/002_Source_Log.md` is the record. Three outcomes bind the build:

1. **Gate decision: CLUB VERDICT.** Shot Scope publishes the club ladder at handicap resolution (anchor C). The club framing stands.
2. **Benchmark decision: calibration path.** No published (band x length) par-4 scoring table exists. The benchmark becomes the calibrated model evaluated at tier-typical driving, with its level pinned to Shot Scope's published aggregate par-4 score per band (anchor E): the model's expected score, averaged over a stated par-4 length mix, must reproduce each tier's published aggregate. The length-resolved benchmark is MODELED (calibrated to a published aggregate) and labeled that way everywhere.
3. **Threshold redefinition: the cost line.** With a calibrated benchmark, the strict SG = 0 crossing is degenerate: the benchmark is the model at tier-average driving, so the crossing sits at the tier's average drive by construction. The headline metric is therefore the cost line: the drive distance below which expected score exceeds the tier benchmark by more than 0.10 strokes (one shot per ten rounds). The API keeps the same shape with an explicit `margin` parameter (default 0.10); charts may also show a 0.25 line. The strokes-gained readout in the tool (benchmark minus expected score at your drive) is unchanged. Both spec edge cases (always at benchmark, never at benchmark) apply to the margin-adjusted line.

Data-source bindings from the log: driver means use Shot Scope P-Avg (internal consistency with the anchor C club ladder), with the Arccos discrepancy disclosed as a sensitivity check; lateral dispersion per band is derived in code by inverting Shot Scope's fairway-hit percentages through Stagner's published 36-yard fairway geometry, cross-checked against Broadie 2008 angular dispersion; distance-sd fraction is MODELED with a stated sensitivity range; amateur strokes-to-holeout curves are constructed from Broadie 2011 tour curves scaled by anchor D/E ratios and are MODELED; Shot Scope penalty % vs Arccos trouble rate are reconciled as a MODELED trouble parameter with both published values quoted.

## The model

Analytic chain, per handicap tier:

1. **Tee shot.** Club selection sets a carry distribution: mean and dispersion by tier, from published distance tables. Clubs map to distance bands per tier (a 15's driver band differs from a 5's).
2. **Lie probabilities.** Dispersion feeds fairway, rough, and penalty odds. Reuses the 001 Fairway vs. Rough machinery and anchors.
3. **Approach and hole-out.** Leftover yardage plus lie feeds an expected-strokes-to-hole-out curve per tier, built from published anchors and interpolated between them. Interpolation carries the modeled label.
4. **Expected hole score.** Sum of tee shot and expected strokes from the resulting position, integrated over the dispersion distribution.
5. **The threshold.** Expected hole score as a function of drive distance crosses the tier's benchmark score for a hole of that length at one point. That crossing is the neutral distance. Longer drives show as strokes gained, shorter as strokes lost. Edge case: on short holes the curve may sit at or under the benchmark across the whole plausible distance range. The model reports "no threshold" there and the tool's verdict says any reasonable drive keeps you at benchmark.

**Validation harness (peer review, not publication):** a Monte Carlo simulation over the same distributions must reproduce the analytic curves within tolerance, and the model must reproduce each tier's published scoring benchmark when fed that tier's average drive distance. Both checks are must-pass gates in the peer review document.

## Data and the verification gate

**Published anchors (re-pull before any chart, log URLs and retrieval dates):**

- Shot Scope benchmark tables: club performance off the tee, driving distance by handicap band, approach and short-game benchmarks at bands 0/5/10/15/20/25.
- Stagner/Arccos: driving distance and dispersion by handicap; approach tables where published.
- Broadie 2011 (ShotLink amateur tables): expected strokes by distance and lie, tour and amateur context.
- GOLFTEC dispersion data, as used in 001.
- The 001 source log, reused wholesale for lie values.

**Modeled (labeled in every chart, caption, and table):**

- Tier-resolution expected-strokes curves between published distance points.
- Any tier or club split Shot Scope does not publish, extrapolated by least-squares across all published bands, never a single last delta.

**Gate:** confirm Shot Scope publishes club-off-tee splits at handicap resolution. If the club-level amateur hunt fails, the piece reframes from "club verdict" to "distance threshold" and clubs become labeled distance bands. The reframe decision happens at the gate, before charts.

## Charts (five)

1. **The headline.** Minimum neutral drive distance vs hole length, one curve per tier. The chart that carries the release.
2. **The flat zone.** Expected strokes vs drive distance on a 400-yard par 4, per tier, showing where each curve flattens. The "you don't need to bomb it" picture.
3. **The decomposition.** As drive distance drops, where the cost moves: the tee shot itself vs the longer approach it creates. Sunny's 220/180 example rendered.
4. **The club verdict map.** Hole length by tier, best tee club in each cell.
5. **The quote card.** The single most counterintuitive threshold that survives verification, e.g. what a 15 needs on a 380-yard hole.

All five: matplotlib PNGs, house style, badge and source line, published-vs-modeled labels.

## The tool

Par-4 calculator, self-contained page matching the fairway-vs-rough dashboard pattern (same palette, header, tabs, Chart.js from CDN, no build step).

**Inputs:** hole length (280 to 500 yards), handicap (0 to 30), typical drive distance (140 to 320 yards). Values outside ranges clamp.

**Outputs:**

- Expected strokes on the hole vs your tier benchmark (the strokes-gained number).
- The neutral distance threshold for that hole at your handicap.
- The full expected-strokes curve across drive distances with your position marked.
- A club-shaped verdict line ("at your distances, the wood gives up nothing here").

**Implementation:** the Python model exports precomputed curve tables into the page's JS. No runtime model, no server. The page renders correct output for the full clamped input grid.

## Testing

- **Model unit tests:** expected-strokes curves decrease as leftover distance drops; rough costs more than fairway at equal distance, every tier; each tier's curve reproduces its published scoring benchmark at tier-average inputs.
- **Cross-release check:** every number shared with 001 matches 001 exactly, or the caption states the discrepancy.
- **Monte Carlo harness:** simulated scores match analytic curves within stated tolerance, documented in peer review.
- **Tool check:** rendered outputs match the Python model on a fixed test grid of (hole length, handicap, drive distance) triples.

## Deliverables (standing rules apply)

Five PNG charts, long-form caption plus X alt version, the dashboard page, peer review document before anything publishes, /cite exports.

## Risks

- **Question-type repetition.** 001 and 002 both live in tee/approach decision territory. Accepted for launch momentum: machinery reuse is what makes a biweekly slot feasible. The pipeline doc states this.
- **Nine-day build.** The verification gate is the schedule risk. Mitigation: the gate runs first, and the reframe path (distance bands instead of club verdicts) is pre-approved above.
- **Modeled amateur curves.** Tier-resolution interpolation is the largest modeled surface. Defense: aggressive labeling, published-anchor documentation, sensitivity analysis in peer review.
- **DECADE/Fawcett overlap.** Tee-club logic overlaps course-management products. Differentiation: handicap-specific inputs, free access, shown work. Cite Fawcett where tour logic matches.
