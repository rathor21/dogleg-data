# Peer Review Addendum — Dogleg Data Rebrand Pass

**Scope:** rebrand of the Fairway vs. Rough package (charts 1-5, dashboard, new platform copy) to the Dogleg Data identity. Numeric model untouched by design; this pass verifies that claim and reviews the new presentation and copy.
**Reviewer:** Claude (orchestrator pass, independent of the subagents that produced the assets)
**Date:** 2026-07-01

## Verification of the "zero numeric drift" claim

1. `Fairway_vs_Rough_Data.csv` diffed against a pre-rebrand copy after every regeneration: identical, every time.
2. Dashboard embedded DATA blob: SHA-256 identical before and after the re-skin.
3. Headline numbers re-derived from `data.py` raw arrays with independent code (not `model.py`): tour worth 75.0 at 150, 80.0 at 140. Rough penalty range 0.16-0.25. The 90-vs-60 claim: 2.77 vs 2.70 strokes. All match the caption.
4. `data.py`, `model.py`, `montecarlo.py`, `build_data.py`, `dashboard_data_gen.py` untouched (chart and style files only).

## Must fix — found and resolved this pass

| # | Location | Issue | Resolution |
|---|---|---|---|
| 1 | chart2 scramble panel | Displayed "needed 8 yd ... margin +28 yd", implying 35−8=28. Underlying values are 7.5 and 27.5 (break-even at the partner ball's 160 yd); integer rounding made consistent math read as an arithmetic error. | Both lines now show one decimal (7.5 / +27.5) and name the 160 yd distance. Post copy aligned to the same numbers. |
| 2 | chart2 verdict text | Rendered in green (#3f7d5c); the brand palette bans green. | Verdict and margin now darkened denim (#46628A), contrast-checked on cream. |
| 3 | chart4 vs dashboard | Light rough was an off-palette sky blue (#8fb8d9) in chart4 and #D0906B in the dashboard; fairway was ink in charts 3/4/5 but denim in the dashboard. Same categories, two palettes. | Canonical lie palette applied everywhere: fairway #5B7FA6, light #D0906B, moderate #C05A36, deep #7D362E. |

## Should fix — found and resolved this pass

| # | Location | Issue | Resolution |
|---|---|---|---|
| 1 | chart 1-5 text | Em dashes and banned adverbs ("actually" in two titles, "clearly", "just") violated brand voice rules. | Reworded, text-only edits; no numbers or sources touched. |
| 2 | chart5 illustration | Literal green-grass rendering conflicted with the no-green brand rule. | Redrawn as a vintage yardage-book diagram: cream tones, ink-outlined green, clay flag. |

## Minor / noted, not changed

1. chart5 header shows 11% / 6% from its drawn 260-shot sample; chart3's 60k-trial run gives 9.2% / 6.2% for the same setup. The chart labels its sample size, and the caption calls chart5 an illustration of chart3's example. Pre-existing, disclosed, left alone.
2. chart2 grid cells round to integers (light-rough 20-hcp exact value 8.5, shown as 8). The scramble panel now shows exact decimals; the grid stays integer for readability. Direction is conservative.
3. Fonts: Fraunces/Inter/IBM Plex Mono installed and registered for matplotlib with per-glyph DejaVu fallback for arrows and ≈ symbols. If the pipeline runs on a machine without `source/fonts/`, charts fall back to DejaVu Sans; presentation only.
4. The caption file (`Fairway_vs_Rough_Caption.md`) still says "an 8-yard edge was enough." The published post copy now says 7.5 at 160. Both trace to the same model; if the caption file gets published anywhere verbatim, align it then.

## Copy checks

Stop-slop sweep of both post files: no em dashes, no banned adverbs, no reversal constructions, no hype vocabulary. Every statistic traced to the caption/model: 75, 80 peak, 23/17/12 (30 labeled modeled), 8/17/29 severity ladder, 7.5/35 scramble, 240-250 crossover, 0.16-0.25, 2.70/2.77, 76.67 disclosure. Tweet lengths re-counted after edits; longest is 272 chars with the t.co link counted at 23.

## Sign-off

- [x] **Approved.** Three must-fix and two should-fix items resolved during this pass; minors noted for awareness. The package is publishable under the Dogleg Data identity once the Gemini logo art is dropped in (charts carry a text-and-geometry badge that does not depend on it).

Reviewer: Claude — 2026-07-01
