# 003 completion plan

Date: 2026-09-07 · Branch: `analysis-003-augusta-12` · Orchestrator: Fable, Sonnet subagents per task.

## State at start

Closed: #6 (Tour proximity anchor), #7 (amateur oval core), #8 (optimizer and verdicts), #9 (Monte Carlo and gates). Open: #10 through #17. Uncommitted: `analysis/003-augusta-12/art/` (the #11 stencil pipeline, README claims registration PASS) and `docs/agents/` (skill setup docs referenced by CLAUDE.md). Three Twitter-named JPEGs at the repo root predate 003 (July 3) and stay out of every commit.

Test suite: 76 passed, 2 xfailed (the two Tour gates), 3.5 minutes under `analysis/002-tee-shot-distance/.venv/bin/python`.

## Review findings that change the plan

1. **Putting model defect.** `model._green_strokes` prices putts as `max(1, 1.5 + 0.012 * ft) * (1 + three_putt_rate)`. That floors expected putts at 1.5 from a tap-in and prices a 3-footer at about 1.6 putts for a Tour player. Published Tour putts-per-distance sits near 1.04 at 3 ft and 1.6 at 10 ft. The Monte Carlo's stochastic rounding turns the expectation into a one-putt probability, so the floor caps Tour birdies near 50 percent even from inside 3 ft. This is the mechanism behind the gate's birdie deficit (about 10 percent simulated vs 17.1 percent in 2019), which VALIDATION_NOTES attributes to aim policy. Fix: anchor a putts-by-distance curve per tier (Tour and amateur) from published sources, replace the shape, mirror in `tour.py`, and let the MC discretize with a one-putt and three-putt probability instead of two-outcome rounding.

2. **The two Tour gates contradict each other as written.** The season-mean gate targets the all-time average (3.27 to 3.28). The 2019 shape gate targets a week whose own published mean is 3.053 (Anchor 4). No single season weighting reproduces both. The 2019 shape test must run under a weighting calibrated to the 2019 mean (one disclosed parameter, wind frequency, fit to a published anchor), then compare the four bucket fractions. The season-mean gate compares a 2016-2023 proximity oval against a 1934-2025 average; a hunt for per-year hole-12 averages decides whether a modern-era window is the honest target. Recorded as ADR 0002 once the hunt lands.

3. **Hero art fails on sight.** `art/hero.png` passes the landmark registration script and still reads as a flat green wedge pasted over a backdrop: the composited green rises above the plate's tree line, the fairway corridor is a hard-edged triangle, the creek is a blue stripe. Cause: the sketch camera's horizon sits near the top of the frame while the generated environment plate puts its horizon mid-frame. Fix: regenerate the plate with a horizon matching the sketch camera, feather the fairway into the plate's own grass, shade the green and creek banks so they read as relief. The registration gate stays; a visual gate joins it (the orchestrator views the result).

4. **VALIDATION_NOTES.md is stale.** It documents `aim_policy="optimal"` as the default; the committed `tour.py` defaults to `attack_when_fair` with a season mean of 3.250. The notes get rewritten in the model-fix task.

5. **Creek region has no floor** (found while curating manifest landings). `model.region_at` classified every non-bunker miss short of the green as creek, however far short. The typical water landing for a 15-handicap sat 27 yards short of the Sunday pin, which is fairway on the real hole. Fix: a finite creek-plus-bank band (MODELED widths with ranges) and a new short-of-creek fairway region priced as a pitch over water. Regenerates the verdict CSV, grids, and manifest.

## Progress log

- Anchors 8, 9, 10 appended to the source log (putting curves, modern-era hole-12 averages, Tour scrambling).
- Hero art accepted at commit 5a139bc, #11 closed: code-rendered ground over a generated tree band.
- Model: anchored putting curve, Tour recovery anchors, gate retargeting per ADR 0002 (proposed). Season-mean gate passes at 3.1365 inside [3.0586, 3.2051]; 2019 and 2024 shape checks are disclosed near-misses on the bogey bucket (5.7 and 6.1 points high at a 3-point tolerance); 2025 passes.
- Export seam committed (#10), manifest landings on the medoid of their outcome class.

- Creek band and pitch-over-water risk priced (revs 4 and 5); left and center "either works" at every tier, Sunday "bail" everywhere; published moves use the full-shot window with the lay-up disclosed as a tossup (`outputs/003_moves.csv`).
- Site: hero page (#12), chapters and The move (#13), sandbox (#14), social export (#15), site integration (nav, home, sitemap, llms.txt), QA pass (#16, all pass).
- Art, 2026-09-07 to 08: Sunny rejected every geometry-first rendering. Final: nano-banana painting of Golden Bell from a text prompt (`art/hero_candidates/r6_4.png`), camera fitted to the art as a thin-plate spline with a homography backbone (`art/camera_tps.json`), arcs drawn as screen-space tracers between projected endpoints.

## Tasks, in order

| # | Task | Ticket | Depends on |
|---|------|--------|------------|
| A | Anchor hunt: putts-by-distance (Tour, amateur by handicap) and per-year Masters hole-12 scoring averages 2015-2025; append Anchors 8 and 9 to `docs/sources/003_Source_Log.md` | #9 follow-up | none |
| B | Hero art rework in `art/` (plate horizon, fairway feathering, relief shading), commit the pipeline | #11 | none |
| C | Model fix: anchored putting curve, MC three-outcome putting, gate reframing per finding 2, ADR 0002, rebuild `outputs/003_results.csv`, refresh golden snapshots, rewrite VALIDATION_NOTES | #9 | A |
| D | Export seam: `build_outputs.py` emits sandbox grids JSON and the animation manifest; equality tests | #10 | C |
| E | Hero animation page `site/augusta-12/index.html` (hero section only, settled-state hook) | #12 | B, D |
| F | Scrollytelling chapters and The move section on the same page | #13 | C, E |
| G | Aim sandbox `site/augusta-12/tool.html` joining the tools tab row | #14 | D |
| H | Social export script: Puppeteer capture to WebM, ffmpeg to MP4, carousel PNGs | #15 | F |
| I | Mobile and QA pass with findings doc | #16 | E, F, G |
| J | Peer review doc, cross-release check, sitemap/nav/llms.txt, PR | #17 | all |

Each task: implementer subagent, spec review, quality review, commit. Publication to main waits for Sunny; the PR is the deliverable.
