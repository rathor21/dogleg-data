# Peer Review

**Work reviewed:** Where to Aim at Augusta's 12th, Pin by Pin (release 003, Augusta National hole 12 aim-point piece) — `data.py`, `model.py`, `tour.py`, `optimizer.py`, `montecarlo.py`, `build_outputs.py`, `export.py`, `outputs/003_results.csv`, `outputs/003_moves.csv`, `VALIDATION_NOTES.md`, ADR 0001, ADR 0002, `docs/sources/003_Source_Log.md`, `docs/sources/003_Chapter_Numbers.md`, `site/augusta-12/index.html`, `site/augusta-12/tool.html` (labels and disclosures), `analysis/003-augusta-12/art/README.md`.
**Author:** Claude, direction by Sunny
**Reviewer:** Claude (independent pass, part of issue #17)
**Review type:** Full (spec compliance, model logic, validation gates, sourcing, numbers, facts, naming, copy)
**Date:** 2026-09-08
**Turnaround commitment:** same day

Scope note: `site/augusta-12/chapters.*`, `tool.html`'s interactive behavior, `launch/003-social/`, and the QA pass documented separately are another agent's concurrent work. This review does not touch or duplicate that ground; it reads those files for content only, and refers to `docs/plans/2026-09-08-003-qa-findings.md` for the browser/device QA once that agent lands it.

---

## Context

**Business question:** for each of five handicap tiers and three named pins on Augusta National's 12th, where should an amateur aim, and is that verdict trustworthy enough to publish under Dogleg Data's own gate standard.

**Method:** read issue #5 (spec), the completion plan, both ADRs, the full source log, `VALIDATION_NOTES.md`, `README.md`, the three core model modules, both output CSVs, the chapter-numbers ledger, the article and tool-page markup, and the art pipeline's README. Ran the full test suite read-only from `analysis/003-augusta-12` (`../002-tee-shot-distance/.venv/bin/python -m pytest -q`): **121 passed, 4 xfailed, 0 failed, 743.7s**. Cross-checked the four xfails' current reasons directly in `tests/test_montecarlo.py` rather than trusting `VALIDATION_NOTES.md`'s prose alone. Spot-checked over 20 numbers in the article against the CSVs and validation notes, using `003_Chapter_Numbers.md` as the ledger and then verifying the ledger itself against the underlying files.

---

## Spec compliance (issue #5's 22 user stories)

| # | Story | Status |
|---|---|---|
| 1 | Per-handicap aim verdict per pin | Met — `outputs/003_moves.csv`, article Chapters 2-4 and 8 |
| 2 | Verdict bundles club choice with line | Met — every verdict line states lateral yards and a club-language carry adjustment together |
| 3 | Scratch sees where pin-hunting is fine | Met — scratch reads "either works" at left/center, "bail" at Sunday, same as every other tier |
| 4 | Five shots, different aims/shapes, watched flying | Met — hero manifest, five curated arcs, medoid-of-class landings, disclosed selection rule |
| 5 | Hero legible at phone width | Deferred to the QA agent's findings doc; `hero_mobile_crop.png` (506×900) exists |
| 6 | LinkedIn native video lead post | Met (pending the QA pass) — `launch/003-social/out/hero.mp4`/`.webm` exist |
| 7 | Carousel, one card per chapter | Met — `card_01`…`card_09` PNGs plus `carousel.pdf` in `launch/003-social/out/` |
| 8 | Wind chapter with real mechanism | Met — Chapter 5, two named modeled multipliers, sensitivity ranges stated |
| 9 | 2019 final-round chapter, verified list | Met — Chapter 6, matches Anchor 4 exactly, Molinari hole-12/hole-15 correction carried through |
| 10 | Tour oval validated against scoring average and checked against 2019 distribution | **Met with deviation** — season-mean gate passes (ADR 0002's modern-era retarget); the 2019/2024 shape check the article discloses is incomplete relative to the current model state (see Must-Fix 1) and ADR 0002 itself is still unconfirmed |
| 11 | Every modeled assumption labeled with a sensitivity range | Met with deviation — `UP_AND_DOWN_PCT` has no stated numeric range anywhere (article's own table shows "-"); every other modeled constant has one and is swept by a dedicated test |
| 12 | Sandbox: drag aim, live score/water/strokes-lost | Met — `tool.html`'s embedded JS ports `model.score_components`-equivalent math client-side |
| 13 | Tier, club-distance, pin, wind controls | Met — carry slider stands in for club distance, functionally equivalent |
| 14 | Sandbox in 002's tools-tab pattern | Met — `tool.html` nav row lists the 002 calculator and the 001 dashboard tabs |
| 15 | Per-chapter share images | Met — `launch/003-social/out/card_*.png` |
| 16 | Hero art generated from Sunny's own geometry sketch | **Not met as specified, disclosed pivot** — the accepted `hero.png` (`r6_4`) was generated from a text prompt with no sketch reference at all; the model's camera was fitted to the art after the fact, the reverse of the story's stated intent. See "Naming and rights" and Open Items. |
| 17 | Scripted path to MP4 | Met — `launch/003-social/export.mjs`, `hero.mp4`/`hero_portrait.mp4` present |
| 18 | Deterministic settled state for QA/social capture | Met — `?settled=1` query param and `window.__phaseComplete` flag confirmed in `hero.js` |
| 19 | Static JSON, no server | Met — `site/augusta-12/data/` holds the three exported JSON files |
| 20 | Monte Carlo reproduces analytic model within tolerance | Met — amateur 0.0137, Tour 0.0121 stroke, both inside the 0.03 tolerance |
| 21 | 2D oval construction reusable for future analyses | Met by design — `oval_for_tier`/`region_at` are hole-agnostic primitives; not independently exercised by a second hole in this release |
| 22 | Degrades to settled state on slow hardware | Met — `hero.js` measures average frame time and falls back to the settled render |

**Out of scope:** the parametric closing chapter, full wind physics, other holes, DataGolf licensing, and X-thread strategy beyond reusing LinkedIn assets are all correctly absent. Launch copy and title were handled at copy time and read as finished prose, not placeholders (only the publish date is a marked placeholder — see Open Items).

---

## Model review

**Three-step oval chain.** `data.py`'s Rayleigh-inversion → `model.oval_for_tier`'s anisotropy split → hole-geometry placement is exactly the chain the source log's gate verdict describes, and every step's ANCHORED/MODELED status is stated in-line where the number is defined, not asserted after the fact. Tier 10's self-calibrating matched pair and the direct 150-175 yd Tour band (Anchor 7) are the strongest links; the 2:1-3.5:1 anisotropy ratio, carried over from a different distance band entirely, is rightly called the release's weakest anchor everywhere it appears.

**Putting curve (Anchor 8).** The fix from the invented `1.5 + 0.012*ft` floor to `putt_probabilities`'s anchored (p1,p2,p3) triple is a genuine, well-tested improvement, independent of whether the gates pass. Amateur three-putt-by-distance remains MODELED (Tour shape scaled by a modeled per-hole ratio) since no source publishes it directly — correctly disclosed.

**Creek band, short_fairway, and the pitch-over-water fix.** The rev-4/rev-5 sequence (finite creek band → short_fairway region → dunk-risk pricing on that region) is the strongest engineering in the package: each fix is diagnosed from a concrete defect (an infinite hazard, then a zero-risk pitch over water), each ships with its own sensitivity sweep, and each is shown not to flip the Sunday "bail" verdict. `PITCH_OVER_WATER_DUNK_PCT` and `SHORT_FAIRWAY_FALLOFF_YD` are both MODELED and anchorless (no source publishes a pitch-over-water dunk rate at any tier), both carry stated ranges, and both are swept by name in `tests/test_model.py`.

**Published-move vs. strict optimizer, the lay-up finding.** `optimizer.published_move` is a defensible, disclosed compromise: rather than silently publishing a 13-39-yard Sunday layup the strict search prefers, or silently suppressing that finding, the article states both numbers and the strokes between them, and flags every one of the five deepest cases as inside the 0.05 tossup band. `VALIDATION_NOTES.md`'s own "Sunday layup check" table is unusually candid that clamping the search to ±10 yd only costs 0.007-0.042 stroke versus the deeper layup — this is the right way to disclose a shallow-valley finding, and the article's prose ("still inside the tossup line... the direction is the finding") matches the data precisely.

**Flip set.** Only 4 of 150 sensitivity-corner combinations flip label, none of them Sunday, and the article's flip-set list matches `VALIDATION_NOTES.md`'s "Flip-set golden snapshot" combination-for-combination.

**MODELED constants without a swept range.** `UP_AND_DOWN_PCT` (Anchor 5, weakly sourced, WebSearch-only, direct fetch failed 403 on the underlying pages) has no stated sensitivity range and no sensitivity test anywhere in the suite, unlike `LONG_TROUBLE_UPDOWN_MULT`, `CREEK_WIDTH_YD`/`BANK_ROLLBACK_YD`, `SHORT_FAIRWAY_FALLOFF_YD`, and `PITCH_OVER_WATER_DUNK_PCT`, all of which are. It feeds every recovery leg in the model. A skeptical reader who reads the article's own Chapter 10 table (which correctly shows "-" for this row, rather than papering over the gap) will notice the omission. See Should-Fix 3.

---

## Validation gates

Per issue #5's own wording, the Tour oval "must reproduce the hole's published scoring average... and be checked against the 2019 distribution." ADR 0002 reads the first clause as the must-pass gate and the second as a check on it, not a second independent gate — a defensible reading, and one this review does not overturn.

**Season-mean gate: passes, plainly.** Analytic mean 3.1188 (rev 5's own current number), inside the modern-era band `[3.0586, 3.2051]` with room to spare; MC at n=500,000 agrees within 0.00035 stroke. The ADR 0002 retarget from the all-time 3.27-3.28 band to the modern-era mean is well-reasoned: Anchor 7's own Tour proximity data is drawn from 2016-2023, and every modern year on record scores below the all-time figure, so grading a 2016-2023-built oval against a 1934-2025 average compared two different eras of the same hole. This retarget is the correct call on the merits.

**Per-year shape checks: all four tested years currently fail, not two.** Live pytest confirms all four year-shape tests (`test_tour_gate_2019/2023/2024/2025_shape...`) are marked `xfail(strict=False)` and none passes. 2019 and 2023 are **structural** misses — their published means sit below this model's own achievable range at any `wind_frequency` in [0,1], not a "close but off" gap. 2024 and 2025 are genuine near-misses on the bogey bucket specifically (6.55pp and 3.27pp gaps against a 3.0pp tolerance); 2025 is a *new* regression introduced by the rev-4/rev-5 fixes — it was a clean pass as recently as the rev-3 calibration pass. This is a materially different picture from "2 of 4 years show a 6-point gap," which is what the article currently implies (see Must-Fix 1).

**Does the release clear the gate, plainly stated:** yes, on the must-pass season-mean gate, and no parameter was tuned to force that pass — the recovery-anchor hunt (Anchor 10) that closed it added two real published figures (Tour scrambling 58%, sand-save 50%) rather than moving an untethered constant. On the "checked against" shape comparison, the honest answer is that the model's outcome distribution runs more bogey-heavy than the published record in every year it can even be evaluated against, and two of four years cannot be evaluated at all under this model's current defaults. ADR 0002 is **still "proposed, pending Sunny's confirmation."** This release is not yet cleared to treat that retarget as settled.

---

## Numbers discipline (spot-checked against the CSVs and VALIDATION_NOTES.md)

| Claim | Article | Source | Match |
|---|---|---|---|
| Scratch oval | 18.7×6.2 yd | `oval_for_tier(0)` = 18.7153/6.2384 | Yes |
| 20-hcp oval | 33.6×11.2 yd | `oval_for_tier(20)` = 33.5729/11.1910 | Yes |
| Left, scratch, aim/delta | 3.9R/half-club long, 0.047 | CSV `0,left,False`: 3.938, 5.438, Δ0.0468 | Yes |
| Left, 20-hcp, aim/delta | 4R/same club, 0.014 | CSV `20,left,False`: 4.0, -2.0, Δ0.0140 | Yes |
| Center, 15-hcp, aim/delta | dead-on/half-club less, 0.006 | CSV `15,center,False`: 0.0, -4.0, Δ0.0060 | Yes |
| Sunday, 10-hcp full-shot vs. strict layup | 8L/1-club-less; strict 13.4 yd, edge 0.011 | `moves.csv` `10,sunday,False`: carry -9.938, Δ0.0928; strict carry -13.438, layup_edge 0.0107 | Yes |
| Sunday, 20-hcp layup edge | 26.9 yd, 0.032 strokes | strict carry -26.875, layup_edge 0.0317 | Yes |
| Sunday delta band | 0.073-0.093 strokes | min/max of the four listed deltas | Yes |
| 15-hcp Sunday oval, calm/wind | 28.1×9.4 → 36.5×12.2 yd | chapters cells `15\|sunday\|0/1` | Yes |
| 15-hcp Sunday delta, calm/wind | 0.082 → 0.057 | CSV Δ0.0817 → 0.0565 | Yes |
| Tour oval | 8.4×5.4 yd | `tour.tour_oval()` = 8.4412/5.4459 | Yes |
| Tour season mean | 3.1188 | `VALIDATION_NOTES.md`, rev 5 gate numbers | Yes |
| Modern-era band | 3.053-3.233, mean 3.132, sd 0.073 | `data.HOLE12_MODERN_AVG_BY_YEAR`, mean 3.1318/sd 0.0732 | Yes |
| All-time average | 3.27-3.28, spans 1934-2025 | Anchor 4, ADR 0002 | Yes |
| 2019 outcomes | 52/200/38/14 of 304, avg 3.053 | Anchor 4 | Yes |
| Bogey gap, 2024 | ≈6.6 points | rev 5 table, 6.55pp | Yes |
| Bogey gap, 2019 | ≈5.7 points | rev 4 table, 5.65pp (unchanged per rev 5 text) | Yes, but incomplete — see Must-Fix 1 |
| MC fidelity, amateur/Tour | 0.014 / 0.013 strokes | rev 5: 0.0137 / **0.0121** | Amateur exact; Tour rounds loosely (0.0121 nearest-rounds to 0.012, not 0.013) — Should-Fix 5 |
| Front-third depth | 10.5 yd (9-12) | `data.HOLE["front_third_depth_yd_range"]` | Yes |
| Anisotropy | 3.0 (2.0-3.5) | `data.ANISOTROPY` | Yes |
| Flip set | 3 named flips, Sunday never | `optimizer.flip_set()`, `VALIDATION_NOTES.md` golden snapshot | Yes |

No arithmetic or transcription mismatch found in this sample beyond the two items already flagged (Must-Fix 1, Should-Fix 5).

---

## Facts

**2019 chapter vs. Anchor 4:** players, clubs, outcomes, wind, and the Molinari hole-15 correction all match the source log exactly, including the specific correction (a second Molinari water ball, from a tree-deflected chip, belongs to the 15th, not the 12th) — this is exactly the kind of catch a source-hunt gate exists for, and it is carried through correctly rather than silently dropped.

**Hole geometry vs. Anchor 3:** yardage, bunker count/orientation, diagonal shoe-sole shape, and the Sunday depth offset are all stated as ANCHORED and match; green width/depth are correctly presented as disputed published ranges, never a single confident number.

**Wind vs. Anchor 6:** the article's framing (tee sheltered, green exposed, 2019's ~20 mph gusts) matches the narrative anchor; the carry penalty and dispersion inflation are correctly labeled modeled with ranges.

**Modern-era averages vs. Anchor 9:** all six per-year figures, the two-source/single-source split, and the mean/sd all match `data.py` and the source log exactly.

---

## Naming and rights

ADR 0001 compliance is clean: full nominative use throughout (title, slug `augusta-12`, social meta, article prose), matching Sunny's locked decision. No Augusta-owned photography or broadcast frame enters the pipeline at any of the six art rounds documented in `art/README.md` — every generated asset traces to nano-banana calls against either a code-rendered sketch, a generated environment plate, or a text prompt alone, never a real photograph. That said, **the README never states this as a single explicit sentence** ("no photo references were used"); it is true by inference from the process narrative across six rounds, which is adequate for this review but worth one explicit line for future audit clarity (Minor).

**Hero art vs. the model's own anchored geometry.** The accepted `hero.png` (`r6_4`) was, by the README's own account, generated from a text prompt alone with "no front bunker touching the creek" and only two bunkers total, against the model's ANCHORED three-bunker layout (one front, two back, Anchor 3). This is disclosed thoroughly in `art/README.md` but not mentioned anywhere in the site copy. It affects only the decorative hero illustration — the functional top-down chapter diagrams and the tool's map are code-rendered directly from `model.py`'s own geometry and are unaffected. Flagged for Sunny's sign-off below, not a should-fix on the analysis itself.

---

## Copy

Grepped the article and tool page for the house style rules: zero em dashes in reader-facing prose (one em dash found, but inside a `tool.html` JavaScript code comment, not copy); zero banned -ly adverbs; zero "not X, it's Y" constructions. The prose is consistently golfer-as-actor ("Bail. Aim 7 yards left...") rather than club- or model-as-actor. This is the cleanest copy pass of the three releases reviewed to date — no should-fix items on copy mechanics.

One documentation-hygiene item: `site/augusta-12/index.html`'s top-of-file HTML comment (lines 2-8) still describes the page as an unfilled scaffold with a placeholder title, awaiting a copy pass to "fill in the chapters and 'the move' sections." The page is fully built. This comment is stale and should be removed or updated before publish (Should-Fix 4).

---

## Cross-release consistency

The article makes no numeric claim about release 002; its own closing note says so explicitly ("None quotes release 002's numbers"). Confirmed by reading `analysis/002-tee-shot-distance/outputs/002_results.csv` and finding no overlapping figure. No cross-release check applies, and the article is correct to say so rather than silently skip the disclosure.

---

## Must Fix

*Issues that change the conclusion or produce a wrong output, or materially mislead the audience on a question the spec calls out by name.*

| # | Location | Issue | Suggested fix |
|---|---|---|---|
| 1 | `site/augusta-12/index.html`, Chapter 7 closing paragraph | Discloses the Tour shape-gate near-miss for only 2 of the 4 tested years (2019, 2024), both framed identically as "about six points high on the bogey bucket." The current model (confirmed by this review's own pytest run: 4 xfails, `test_tour_gate_2019/2023/2024/2025_shape...`) fails all four: 2019/2023 are **structural** misses (published mean unreachable at any wind_frequency, not merely "6 points high"), and 2025 is a *new* bogey-bucket near-miss (3.27pp gap) introduced by the rev-4/rev-5 fixes, having been a clean pass as recently as the rev-3 calibration pass. A skeptical reader — the exact audience issue #5's story 10 names — gets an incomplete and partly mischaracterized picture of the validation state. | Name all four tested years and their actual status (two structural, two near-miss) in the closing paragraph, or at minimum add 2025's regression and 2023's structural-miss status alongside 2019/2024. |

---

## Should Fix

*Issues that weaken the conclusion or could mislead the audience.*

| # | Location | Issue | Suggested fix |
|---|---|---|---|
| 1 | `tests/test_montecarlo.py`, lines 299-301 | Module comment states "2025's shape check is a plain pass and 2023's stays xfail," directly contradicted by the `xfail` decorator on `test_tour_gate_2025_shape_wind_frequency_calibrated_single_source` three tests below (added specifically because 2025 regressed to a near-miss). A future contributor or reviewer trusting the comment over the code would repeat this review's own initial misread. | Update the comment to match the current decorator state. |
| 2 | `analysis/003-augusta-12/data.py`, `UP_AND_DOWN_PCT` | No stated sensitivity range and no sensitivity test, unlike every other MODELED recovery constant in the file (`LONG_TROUBLE_UPDOWN_MULT`, `CREEK_WIDTH_YD`, `SHORT_FAIRWAY_FALLOFF_YD`, `PITCH_OVER_WATER_DUNK_PCT` all have both). It feeds every recovery leg. Story 11 asks for a range on every modeled assumption; the article's own table correctly shows "-" here rather than hiding the gap, but the gap itself should close. | Derive a defensible range (even a wide one) from the weakly-sourced WebSearch figures already in Anchor 5, and add a sensitivity test on the Sunday verdict the same way the other recovery constants are tested. |
| 3 | `site/augusta-12/index.html`, lines 2-8 | Top-of-file HTML comment describes the page as an unfilled scaffold awaiting a copy pass; the page is fully built with all ten chapters and "The move" section present. Stale documentation debt, not reader-visible but worth cleaning before publish. | Remove or update the comment. |
| 4 | Chapter 10's anchor table and `003_Chapter_Numbers.md` | "Monte Carlo fidelity... Tour surface within 0.013 strokes" rounds the actual 0.0121-stroke gap loosely (nearest-rounding gives 0.012). Still a true upper bound, but inconsistent with the amateur figure's exact rounding (0.0137→0.014) in the same sentence. | Change "0.013" to "0.012" for consistency, or state both to four decimals. |
| 5 | Chapter 4's closing paragraph | "Nothing extra for scratch or the 5-handicap" describes the 5-handicap's Sunday layup edge (0.0022 strokes) identically to scratch's exact 0.0, while the same sentence reports the 10/15/20-handicap figures to three decimals. | Either state 0.002 for the 5-handicap explicitly, or note both 0/5 as "under 0.003, effectively nothing" rather than treating a nonzero figure as identical to zero. |

---

## Minor / Optional

| # | Location | Suggestion |
|---|---|---|
| 1 | `analysis/003-augusta-12/art/README.md` | Add one explicit sentence confirming no photograph of the real hole was used as generation input at any round, for future audit clarity — currently true only by inference across six rounds of process narrative. |

---

## What's Working Well

1. The numbers discipline is the tightest of the three releases reviewed to date: every one of the 20-plus spot-checked figures traces exactly to `outputs/003_moves.csv`, `outputs/003_results.csv`, or `VALIDATION_NOTES.md`, via a purpose-built ledger (`003_Chapter_Numbers.md`) that names the exact cell for every number before the article ships it — a real ledger-then-verify workflow, not numbers typed from memory and checked after the fact.
2. The lay-up finding is disclosed with unusual honesty. Rather than silently publishing the strict optimizer's 13-to-39-yard Sunday layup, or silently suppressing it in favor of a tidier full-shot verdict, `optimizer.published_move` runs both searches and the article states the edge size per tier, including that it never clears the tossup line.
3. The rev-4/rev-5 region-geometry and pitch-over-water fixes are a model of self-correction under review: each was caught from a concrete, named defect (an infinite hazard, then a zero-risk pitch over water), each ships with its own sensitivity sweep, and each is shown, in the same commit, not to flip the piece's central finding.
4. ADR 0002's own addenda are candid about what did and did not close, including reopening a previously-passing year (2025) as a new near-miss rather than quietly leaving the stale "2 of 4" framing in place — the raw material for a correct disclosure exists in the repository even though the published copy has not yet caught up to it (Must-Fix 1).

---

## Overall Assessment

- [x] **Revisions required** — one must-fix item (Chapter 7's incomplete shape-gate disclosure); re-review of that paragraph only, not the full piece, once fixed.

Two decisions in this release are not this review's to make and are not "fixes" in the must-fix sense: ADR 0002's retarget is still unconfirmed by Sunny, and the hero art's front-bunker omission is a disclosed acceptance tradeoff, not a defect. Both are listed under Open Items and should be resolved before or alongside the must-fix item above.

---

## Open items for Sunny

1. **ADR 0002 confirmation.** The season-mean gate retarget (all-time 3.27-3.28 → modern-era 3.06-3.21) is well-reasoned on the merits but still carries "status: proposed, pending Sunny's confirmation." This is the largest outstanding methodology decision in the release.
2. **Shape-gate disclosure.** Once Must-Fix 1 is fixed in copy, decide whether four-of-four tested years failing the "checked against" shape comparison (two structurally, two on the bogey bucket) is acceptable to publish as a disclosed limitation, per ADR 0002's own framing, or whether it needs further model work first.
3. **Publish-date placeholder.** `article:published_time`/byline/JSON-LD all read 2026-09-14, explicitly marked a placeholder in three HTML comments. Needs a real ship date.
4. **Hero art acceptance.** The accepted painting (`r6_4`) was chosen after rejecting every geometry-first rendering, is generated from a text prompt with no sketch reference, and omits the anchored front bunker. This is the opposite of story 16's original intent ("art generated from my own geometry sketch... never contradicts where the model says the hazards sit") and was accepted as a deliberate trade for a painting that reads as the real hole rather than a diagram. Confirm this trade is still the right call now that it is written down plainly.
5. **The lay-up finding's presentation.** Confirm the "full-shot aim, strict optimum disclosed alongside it" framing (rather than either publishing the deeper layup or hiding it) is the right editorial choice for the Sunday pin at the higher tiers, where the gap grows to 0.032 stroke.
6. **QA findings.** Mobile legibility, console cleanliness, a throttled-device pass, and sandbox spot-checks are the other agent's concurrent work; see `docs/plans/2026-09-08-003-qa-findings.md` once it lands, rather than this document, for that state.

**Reviewer sign-off:** Claude — 2026-09-08
*(121/121 non-xfailed tests pass, 4 xfailed exactly as VALIDATION_NOTES.md and the live test file describe; 20+ sampled numbers traced to source; season-mean gate independently confirmed inside its band; four year-shape xfails independently confirmed in the test file, not just trusted from prose)*

---

## Addendum, 2026-09-08: must-fix resolved

Must-Fix 1 (chapter 7's shape-gate disclosure) is fixed in `site/augusta-12/index.html`: the paragraph now states that 2019 and 2023 sit below the model's calm-air floor and that 2024 and 2025 miss the bogey bucket by 6.6 and 3.3 points against a 3-point tolerance, with the ledger rows added to `docs/sources/003_Chapter_Numbers.md`. Should-Fix 4 (stale scaffold comment) and Should-Fix 5 (Tour fidelity rounding, now 0.012) are fixed; the stale test comment and the art README rights statement (Minor) are fixed. Should-Fix 3 (`UP_AND_DOWN_PCT` sensitivity range and sweep) is now resolved: `data.py` adds `UP_AND_DOWN_PCT_RANGE_MULT` (0.8x-1.2x per tier, capped at 0.95) and `up_and_down_pct_scaled`, two sensitivity tests land in `tests/test_montecarlo.py`, the site's method table and flip-set paragraph carry the range and the sweep's result, and `VALIDATION_NOTES.md`'s "UP_AND_DOWN_PCT sensitivity (peer review Should-Fix 3)" section records the swing table; no pin's label flips at any tier. Open items 1 to 5 remain Sunny's decisions and are listed in the pull request.

Verdict after addendum: cleared for publication once Sunny confirms ADR 0002, the hero art, and the publish date.

---

## Addendum, 2026-09-10: numbers re-derived after revs 6 and 7 (003.8/9)

Every number in `site/augusta-12/index.html` is re-derived against the mishit-mixture model (ADR 0003; rev 6's solid-strike-plus-mishit-tail split and widened bank, then rev 7's GIR-anchored core, skewed mishit tail, and retuned anisotropy default of 2.5:1). `docs/sources/003_Chapter_Numbers.md` is rebuilt from scratch against the current `outputs/003_results.csv`, `outputs/003_moves.csv`, and `outputs/003_chapters.json`; a throwaway extraction check confirms 169 of 169 real numeric tokens in the article's prose appear in the ledger (the extraction script's one apparent miss, "-5," is a regex artifact of "par-5" in Chapter 6's prose, not a number needing a source).

The owner's water-by-tier finding (a 20-handicap's water rate at the Sunday pin, calm, is lower than scratch's, 13.7% against 19.0%, because the 20's much wider miss pattern spreads past the creek band rather than concentrating in it) is disclosed in its own paragraph in Chapter 4, with the short-of-the-creek rate (`p_short`, a new field this pass exports) stated alongside every water-at-the-flag figure in Chapters 2, 3, 4, and 8 so the reader sees the 20's total short-side miss rate (51.1%) against scratch's (34.7%). The sandbox (`tool.html`) gains a fourth KPI card, "Short of the creek," and a disclosure sentence distinguishing it from "Finds the water."

One verdict label changed since the prior addendum's review: `(15, "sunday", wind)` now reads "either works" (delta 0.0493) rather than "bail," a genuine, disclosed erosion of the Sunday pin's sensitivity-rectangle robustness (three windy Sunday cells now flip inside the flip-set sweep, versus none before rev 6). The underlying finding is not reversed: calm air, and flip_set's own baseline settings, still call Sunday "bail" at every tier. Chapter 5 and Chapter 10's flip-set list are rewritten to state this outright rather than repeat the now-stale "Sunday never flips" claim.

## Addendum, 2026-09-10: prose pass (003.8/9), no numbers touched

`site/augusta-12/index.html` and `tool.html` go through a Sepia refactor and a Humanizer pass: reader-facing wording only, no figures changed. The pass trims the "'s own" overuse running through the copy, drops the Molinari hole-15 correction paragraph and other process narration (source-hunt, ADR, and chapter-cross-reference asides), and rewords the ADR 0002 validation-gate sentence into plain reader terms. Article body word count moves from 3,852 to 3,783 words (19-minute read); every remaining numeric token in the prose still traces to `docs/sources/003_Chapter_Numbers.md`, which drops the one ledger row for the deleted correction and otherwise keeps every number unchanged.
