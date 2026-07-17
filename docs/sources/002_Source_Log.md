# Release 002 — Verification Gate Source Log

**Release:** How Far Do You Need to Hit It? (tee-shot club/distance threshold, par 4s)
**Purpose:** Standing rule — no chart and no data value enters the 002 codebase until every number it depends on traces to a row in this log.
**Hunt date:** 2026-07-11
**Hunter:** Claude (web search + page fetch, no numbers taken from memory or training data)

Every value below was read from a page or PDF actually fetched during this session. Where a table was rendered as an image that automated text extraction could not read, that is stated plainly and the row is marked FAILED (with whatever qualitative content survived).

---

## Anchor A — Driving distance by handicap band

**Status: PUBLISHED (secondary transcription), handicap-band resolution 0/5/10/15/20/25.**

**Source:** MyGolfSpy, ["Driver Distance Chart (2026 Update): How Far Golfers Hit It By Handicap"](https://mygolfspy.com/news-opinion/driver-distance-chart-2026-update-how-far-golfers-hit-it-by-handicap/), Brittany Olizarowicz, Apr 10, 2026. Article states the numbers come from Shot Scope's own dataset ("With new data released from Shot Scope..."). Retrieved 2026-07-11.

*Note on sourcing chain:* the primary Shot Scope blog pages (`shotscope.com/blog/practice-green/stats-and-data/distribution-of-driving-distances-2022/`, `shotscope.com/blog/stats/2021-average-driving-distances/`) and the practical-golf.com writeup of the same Shot Scope dataset were all fetched directly. In every case the handicap-by-distance table is rendered as a chart image; text extraction returned no numeric table (see FAILED note below). The MyGolfSpy table below is the only place these Shot Scope numbers were readable as text. Treated as PUBLISHED-via-secondary-transcription, not primary-page-read.

| Handicap | Driver Distance (P-Avg, yd) |
|---|---|
| 0 | 285 |
| 5 | 261 |
| 10 | 259 |
| 15 | 236 |
| 20 | 225 |
| 25 | 204 |

Driver dispersion/accuracy context, same page, same handicap bands:

| Handicap | Fairway Hit % | Left Miss % | Right Miss % | Penalty % |
|---|---|---|---|---|
| 0 | 48 | 25 | 25 | 1 |
| 5 | 49 | 23 | 24 | 1 |
| 10 | 49 | 24 | 25 | 2 |
| 15 | 47 | 23 | 26 | 2 |
| 20 | 46 | 25 | 25 | 3 |
| 25 | 47 | 19 | 28 | 3 |

**Cross-check (different bands, independent database):** MyGolfSpy, ["6 Insights from the Arccos Driver Distance Report"](https://mygolfspy.com/news-opinion/6-insights-from-the-arccos-driver-distance-report/), Tony Covey, May 7, 2025, summarizing Arccos's 2025 annual report (6.5M+ driver shots, 4M rounds, 2024 data). Retrieved 2026-07-11.

| Handicap band | Avg. driving distance (yd) | Fairway hit % |
|---|---|---|
| 0–4.9 | 250.0 | 49.3% |
| 10–14.9 | 224.7 | 45.3% |
| 30+ | 184.9 | 40.6% |

The two databases do not use the same bands and do not agree exactly (e.g., Shot Scope's 0-hcp = 285yd vs. Arccos's 0–4.9 band = 250.0yd — a large gap, most likely driven by different sampling/filtering methodology between the two trackers, not by transcription error on our part; both numbers are quoted exactly as published). Flagging the disagreement rather than picking one silently. Model tasks should decide which database anchors the primary curve and disclose the other as a sensitivity check.

**FAILED:** `shotscope.com/blog/practice-green/stats-and-data/distribution-of-driving-distances-2022/`, `shotscope.com/blog/stats/2021-average-driving-distances/`, and `practical-golf.com/shotscope-handicap-data` were all fetched directly (2026-07-11). All three reference a "driving distance by handicap" chart, but in every case the table is a chart image; text extraction returned no numbers, only the surrounding prose confirming the chart exists.

**Tier 30 extrapolation:** neither database publishes a clean "30-handicap" point (Shot Scope's table stops at 25; Arccos's lowest band is an aggregate "30+"). Tier 30 must be extrapolated — MODELED, per spec.

---

## Anchor B — Driver lateral dispersion by handicap

**Status: PUBLISHED at multiple resolutions, no single clean yards-of-dispersion-by-handicap-index table found.**

**Source 1 (same page as Anchor A):** Shot Scope driver accuracy table above (fairway/left-miss/right-miss/penalty % by handicap 0/5/10/15/20/25). This is the most directly usable published dispersion proxy at full handicap-band resolution.

**Source 2:** Broadie, Mark (2008), ["Assessing Golfer Performance Using Golfmetrics,"](https://www.columbia.edu/~mnb2/broadie/Assets/broadie_wscg_v_200804.pdf) Chapter 34 in *Science and Golf V*, WSCG 2008. Retrieved 2026-07-11. **Note on method:** WebFetch's HTML/text converter could not render this PDF's embedded-font text (returned "compressed/garbled content" on three separate attempts, including a mirror at `business.columbia.edu`). The PDF was fetched as binary and its text was extracted locally with PyPDF2 (Python), which worked cleanly. Table 1 ("Putting, sand game and long tee shot results"):

| Group (18-hole score range) | 75th-pctile long tee distance, d₀.₇₅ (yd) | Std dev of direction, σ(α) (deg) |
|---|---|---|
| Pro (64–79) | 297 | 4.0 |
| Am1 (70–83) | 248 | 5.4 |
| Am2 (84–97) | 237 | 6.4 |
| Am3 (97–120) | 216 | 8.1 |

σ(α) is angular dispersion (degrees off the start-target line), which converts to lateral yards as a function of distance (e.g., a 4° error is 21 yd off-line at 300 yd). This is a genuine published driver/long-tee-shot dispersion anchor, but it is stratified by **18-hole score range** (Am1/Am2/Am3), not by USGA Handicap Index band (0/5/10/15/20/25) — mapping score ranges onto index bands for the model is a MODELED assumption that must be flagged wherever used.

**Source 3:** Lou Stagner, ["Tee Shot Targets," Newsletter #13](https://newsletter.loustagnergolf.com/p/newsletter-13-tee-shot-targets), May 12, 2023 (Arccos database). Retrieved 2026-07-11 — full text loaded without a paywall. Describes a hypothetical 36-yard-wide fairway and Arccos on-course dispersion data by handicap index, with one fully worked numeric example for "straight hitting" 5-index players: aiming dead-center of the fairway lands 62.6% of drives in the fairway (15.9% specifically on the left 10 yards); shifting the target 15 yards left drops overall fairway-hit to 51.9% while only raising left-side-of-fairway frequency to 19.1%. The newsletter states the pattern qualitatively for other indices (10- and 15-index golfers drift right as handicap rises) but does not publish a numeric dispersion-in-yards table for every index in the accessible text.

**FAILED (partial):** Lou Stagner, [Newsletter #47, "How Far Should You Hit Your Driver"](https://newsletter.loustagnergolf.com/p/how-far-should-you-hit-your-driver) — text confirms "the chart below shows the median distance with driver by handicap index" but the chart is an image; no numbers extracted.

**001 reuse (fallback, per spec):** `data.py` in `/Users/sunny/Documents/Claude/Projects/Golf Agent/Fairway_vs_Rough_Post/source/` — GOLFTEC 7-iron fitting data (n>10,000 swings), published via GOLF.com (Keith Clearwater, GOLFTEC, 2022): `GOLFTEC_WIDTH_YD = {0: 12.0, 8: 20.0, 13: 21.0}`, `GOLFTEC_DEPTH_YD = {0: 12.0, 8: 18.7, 13: 30.0}`. Already cited and used in 001's `montecarlo.py` (quadratic fit through the three anchors, secant-slope extrapolation beyond hcp 13 — the peer-review-fixed version). **Flag carried over honestly:** this is 7-iron approach-shot dispersion, not driver/tee-shot dispersion. It was an acceptable proxy for 001's approach-shot model; reusing it for a driver-off-the-tee model in 002 is a bigger stretch and should be disclosed as such, or replaced by the Shot Scope driver accuracy % table (Source 1 above), which is a real driver-specific published anchor.

---

## Anchor C — Club distances relative to driver, by handicap

**Status: PUBLISHED, handicap-band resolution (0/5/10/15/20/25 for driver/wood/irons; 0/5/15/25 for hybrids). Gate condition satisfied.**

All four sources are MyGolfSpy articles that state their numbers come from Shot Scope's performance-tracking database (male golfers). Retrieved 2026-07-11.

- ["How Far Should You Be Hitting Each Club?"](https://mygolfspy.com/news-opinion/how-far-should-you-be-hitting-each-club-distance-data-you-should-know/), Jan 7, 2025 — Driver, 3 Wood, 4–9 iron, PW/GW/SW/LW.
- ["How Far Should You Hit Each Iron? (2026 Data)"](https://mygolfspy.com/news-opinion/instruction/how-far-should-you-hit-each-iron-complete-iron-distance-chart-for-every-handicap/), Oct 14, 2025 — 4–9 iron restated; values match the January 2025 article exactly at every handicap band, a useful cross-consistency check.
- ["Hybrid Distance Chart: What's Average For Your Handicap?"](https://mygolfspy.com/news-opinion/hybrid-distance-chart-whats-average-for-your-handicap/), May 28, 2025 — 2H/3H/4H/5H, "Average" and "P-avg" (mishit-filtered) distance, but only published at 0/5/15/25 (10 and 20-handicap hybrid data not included in this piece).

| Handicap | Driver | 3-Wood | 2H (avg/P-avg) | 3H (avg/P-avg) | 4H (avg/P-avg) | 5H (avg/P-avg) | 4i | 5i | 6i | 7i | 8i | 9i | PW | GW | SW | LW |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 285 | 261 | 205/230 | 197/219 | 186/209 | 171/193 | 223 | 200 | 185 | 178 | 166 | 155 | 141 | 126 | 105 | 86 |
| 5 | 261 | 234 | 189/215 | 181/207 | 174/199 | 162/184 | 201 | 183 | 172 | 164 | 153 | 139 | 126 | 109 | 86 | 71 |
| 10 | 259 | 227 | — | — | — | — | 199 | 187 | 171 | 161 | 150 | 140 | 127 | 110 | 98 | 79 |
| 15 | 236 | 215 | 163/204 | 166/195 | 155/188 | 143/175 | 186 | 169 | 162 | 154 | 146 | 136 | 121 | 104 | 84 | 75 |
| 20 | 225 | 195 | — | — | — | — | 169 | 162 | 151 | 146 | 138 | 129 | 108 | 94 | 85 | 78 |
| 25 | 204 | 178 | 134/168 | 132/161 | 121/149 | 113/140 | 151 | 143 | 137 | 132 | 122 | 108 | 90 | 79 | 80 | 49 |

**Gate check:** the design spec's gate condition — "confirm Shot Scope publishes club-off-tee splits at handicap resolution" — is satisfied. Driver, 3-wood, and the full iron set are published at all six target bands (0/5/10/15/20/25); hybrid is published at four of six bands, close enough to interpolate rather than extrapolate for 10/20. This directly resolves the pre-approved reframe decision (see Gate Decision below).

---

## Anchor D — Expected strokes to hole out by distance and lie, amateurs

**Status: PUBLISHED at a related but not identical metric (proximity/FRL and % on green, not literal strokes-to-holeout), stratified by 18-hole score group rather than handicap-index band.**

**Source:** Broadie, Mark (2008), *Assessing Golfer Performance Using Golfmetrics* — same PDF as Anchor B, same extraction method (PyPDF2, since WebFetch could not render the text). Table 2 ("Short game and long game results"), using the Am1 (score 70–83) / Am2 (84–97) / Am3 (97–120) / Pro1 / Pro2 groups defined in the paper:

| Group | 20–60yd: % on green, fairway | 20–60yd: % on green, rough | 20–60yd: median FRL %, fairway | 20–60yd: median FRL %, rough | 100–150yd: % on green, fairway | 100–150yd: % on green, rough | 100–150yd: median FRL %, fairway | 100–150yd: median FRL %, rough |
|---|---|---|---|---|---|---|---|---|
| Pro1 (64–71) | 96 | 87 | 7.3 | 12.9 | 85 | 63 | 5.4 | 11.1 |
| Pro2 (72–79) | 95 | 80 | 9.4 | 15.3 | 77 | 46 | 5.8 | 12.8 |
| Am1 (70–83) | 93 | 86 | 13.8 | 15.4 | 63 | 53 | 8.7 | 10.4 |
| Am2 (84–97) | 81 | 72 | 16.9 | 21.0 | 46 | 34 | 12.0 | 13.5 |
| Am3 (97–120) | 75 | 64 | 20.3 | 25.6 | 25 | 25 | 17.3 | 18.4 |

Median FRL (fractional remaining length) is the median of (distance-to-hole-after-shot ÷ distance-to-hole-before-shot), expressed as a percent — a proximity/quality measure, not a literal "expected strokes to hole out" number. It is the closest published, distance-and-lie-stratified, amateur-skill-tiered table actually found. Two honesty flags for model tasks: (1) it is stratified by 18-hole score range, not USGA Handicap Index — same mapping caveat as Anchor B; (2) it measures proximity/FRL, not strokes; converting it into an expected-strokes curve is a MODELED step, not a direct read of the source.

**Tour/scratch end of the curve:** already sourced and in the codebase from 001 — Broadie (2011), ShotLink Table 9 (`TOUR_DIST`/`TOUR_FAIRWAY`/`TOUR_ROUGH` in `data.py`). Reused wholesale per spec, no re-pull needed.

**FAILED:** Shot Scope's strokes-gained ebook, fetched directly at `https://shotscope.com/ebook/Strokes_Gained.pdf` (2.4MB PDF, retrieved 2026-07-11). WebFetch's text extraction returned only PDF structural/binary noise, no readable tables. Not re-attempted with the local PyPDF2 workaround in this pass because the Broadie result above already gives a usable, better-documented amateur anchor; flagging this as an open follow-up if the model tasks need a second, independent amateur strokes-gained source.

---

## Anchor E — Average par-4 score by hole length by handicap (own-tier benchmark)

**Status: PUBLISHED at handicap-band resolution, aggregate across hole lengths only. FAILED at (band × length) resolution. Fallback calibration path is in play — see Benchmark Decision.**

**Primary target attempted:** Lou Stagner, ["Birds and Doubles by Hole Length," Newsletter #56](https://newsletter.loustagnergolf.com/p/birds-and-doubles-by-hole-length), Apr 26, 2024 (Arccos database). Retrieved 2026-07-11. This newsletter is explicitly scoped to **5-index players only** ("The data below is ONLY for five index players... I'll run the numbers for other skill levels soon — and post those on twitter"), so even at best it would not have given the multi-tier table the model needs. Worse, on this visit the article's data table rendered behind a "Subscribe to keep reading" metered wall after the initial scroll — the qualitative prose loaded (confirming 5-index golfers are more likely to make double-bogey-or-worse than birdie on most hole lengths, and that on 325–349yd par 4s a 5-index makes double-or-worse "once out of every ten times") but the actual birdie%/double%-by-length table (an embedded chart image) never became readable. No email was entered to get past the wall, per the instruction never to submit forms reached this way. **FAILED** at the resolution needed.

**Fallback used:** MyGolfSpy, ["What Is The Average Par-4 Score For Your Handicap?"](https://mygolfspy.com/news-opinion/what-is-the-average-par-4-score-for-your-handicap/), Jan 3, 2025, citing Shot Scope ("We asked Shot Scope for some data regarding the average par-4 score for their users"). Retrieved 2026-07-11.

| Handicap | Avg. Par-4 Score | Fairway Hit % | GIR % | Avg. Putts per GIR |
|---|---|---|---|---|
| 0 | 4.2 | 50% | 52% | 1.85 |
| 5 | 4.5 | 48% | 44% | 1.95 |
| 10 | 4.8 | 45% | 36% | 2.05 |
| 15 | 5.1 | 43% | 27% | 2.10 |
| 20 | 5.4 | 47% | 15% | 2.18 |
| 25 | 5.9 | 46% | 9% | 2.18 |

This is a real published own-tier benchmark, at all six target handicap bands — but it is a single aggregate number per tier across all par-4 lengths on record, not broken out by hole length. This is exactly the fallback scenario the design spec anticipated: *"if only aggregate exists, benchmark becomes model-calibrated and the log says so."* It does.

---

## Anchor F — Fairway-width and penalty-frequency context

**Status: 001's landing model does not contain an explicit fairway-width or tee-shot-penalty-frequency assumption. New published anchors were found in this hunt that are better suited to a tee-shot model than what 001 reused.**

**What 001 actually assumed — read directly from source, not from memory:** `/Users/sunny/Documents/Claude/Projects/Golf Agent/Fairway_vs_Rough_Post/source/data.py` and `montecarlo.py` (read-only reference, outside this repo). Confirmed by direct read and by `grep -i "fairway.*width\|width.*fairway\|FAIRWAY_WIDTH\|yards wide"` across every `.py` file in that source directory: **there is no fairway-width-in-yards variable anywhere in 001.** 001's "landing model" is:

1. A Monte Carlo **approach-shot** dispersion model (`montecarlo.py`), radial miss from a green center, calibrated to the GOLFTEC 7-iron width/depth anchors described in Anchor B above (0/8/13-handicap), quadratic-fit below hcp 13 and secant-slope-extrapolated above it (the peer-review-fixed version, see `Peer_Review_Fairway_vs_Rough.md` Must-Fix #2).
2. A three-tier `ROUGH_SEVERITY` multiplier (`data.py`): light 0.5x, moderate 1.0x, deep 1.7x — anchored to the USGA/R&A "Golfer Model" simulation (R22-13, Nov 2021) and cross-checked against a June 2025 Golf Digest field test.

Neither of these is a fairway-width or a tee-shot-penalty-rate assumption; 001's model starts from a known lie (fairway or rough) and asks how good the *next* shot is, it never modeled where the tee shot itself lands relative to a fairway edge. For 002's tee-shot model, this gap needs new anchors, found here:

**New published anchors found this session:**

- Lou Stagner, [Newsletter #13, "Tee Shot Targets"](https://newsletter.loustagnergolf.com/p/newsletter-13-tee-shot-targets) (see Anchor B, Source 3, full text quoted there). Explicitly states the analysis uses "a hypothetical fairway that is a relatively generous 36 yards wide. This is wider than the typical fairway," built from real Arccos on-course driver dispersion data, filtered to shots within ±20 yards of the golfer's own median distance (to exclude tops/duffs/bombs). This is the only concrete fairway-width number found anywhere in this hunt, published, with a stated methodology.
- Shot Scope driver accuracy table (Anchor A): Penalty % by handicap 0/5/10/15/20/25 = 1/1/2/2/3/3%.
- Arccos 2025 Driving Distance Report, via MyGolfSpy "6 Insights" (Anchor A, Source 2): 30+ handicap golfers hit "1 in 4 drives into some kind of trouble" (punch-out/drop/worse) — 25%, stated as 1.5x the low-handicap (0–4.9) rate (≈16.7% implied). 10–14.9-handicap golfers are "over 50% more likely... to hit their drive into a penalty area than low handicappers" and hit "nearly 1 in 5" (≈19%) tee shots into trouble, ~30% more than low-handicap players.

**Flag:** Shot Scope's "penalty %" (1–3%, strict penalty strokes) and Arccos's "trouble rate" (~17–25%, includes punch-outs and recovery shots, a much broader category) measure different things and are not directly comparable. Both are quoted exactly as published; reconciling them into one penalty-frequency curve for the model is a MODELED decision, not a data fact.

---

## Gate decision

**CLUB VERDICT.**

The pre-approved reframe trigger was "if anchor C fails at handicap resolution." It did not fail. Anchor C returned driver, 3-wood, and the full 4–9 iron ladder at all six target handicap bands (0/5/10/15/20/25), sourced to Shot Scope's own performance-tracking database and cross-consistent between two independently published MyGolfSpy articles pulling from the same underlying dataset eight months apart. Hybrid distances are published at four of the six bands (0/5/15/25), which is close enough to interpolate the missing two rather than extrapolate beyond a published range — a materially smaller modeling step than the reframe was designed to avoid. Given a real, at-resolution club-distance ladder exists, the release keeps its "club verdict" framing (driver vs. wood/hybrid vs. iron off the tee) rather than falling back to abstract distance-band labels.

---

## Benchmark decision

**Fallback calibration path is in play.** Anchor E produced a real external benchmark at handicap-band resolution (Shot Scope's average par-4 score, fairway%, GIR%, and putts-per-GIR by handicap, via MyGolfSpy), but that benchmark is a single aggregate number per tier across every par-4 length in Shot Scope's sample — it is not broken out by (handicap band × hole length). The Stagner/Arccos source that could have supplied length-resolved scoring (Newsletter #56) is scoped to one handicap tier only and its table was inaccessible behind a metered subscription wall on this visit.

Per the design spec's own fallback ("if only aggregate exists, benchmark becomes model-calibrated"), the model tasks should treat the Anchor E aggregate table as a **calibration target**, not a per-length ground truth: derive hole-length sensitivity from the expected-strokes-to-holeout mechanics (Anchor D, Broadie tour and amateur data) applied across the tee-shot and approach-shot chain, then calibrate that curve so its output — averaged across whatever hole-length mix the model assumes for a tier's home course — reproduces the tier's published aggregate par-4 score above. Every chart and caption built on the length-resolved benchmark must label it MODELED (calibrated to a published aggregate), not PUBLISHED at that resolution.

---

## Calibration (Task 7)

Before calibration, `HOLEOUT_SCALE` sat at 1.0 for every tier and the `LENGTH_MIX`-weighted model average missed the published aggregate at every published tier, worse at the harder tiers:

| Tier | Model (pre) | Published | Gap (pre) |
|---|---|---|---|
| 0 | 4.1535 | 4.2000 | -0.0465 |
| 5 | 4.4311 | 4.5000 | -0.0689 |
| 10 | 4.6301 | 4.8000 | -0.1699 |
| 15 | 4.8928 | 5.1000 | -0.2072 |
| 20 | 5.1695 | 5.4000 | -0.2305 |
| 25 | 5.3628 | 5.9000 | -0.5372 |

Tier 10 already breached the 0.15-stroke tolerance and every tier past it opened wider, so `HOLEOUT_SCALE` moved off 1.0. `expected_score` turns out to be exactly affine in `HOLEOUT_SCALE[tier]`: `strokes_to_holeout` rescales the anchor table linearly, and the trouble-cost term added on top is a flat per-tier constant that does not touch the scale. That linearity let a two-point secant per published tier solve the exact scale that zeroes its aggregate gap, no iteration needed. `MISHIT` and `TROUBLE_COST` stayed at their documented starting values; scale alone closed every published tier's gap to under 0.0001 strokes, well inside the ranges those two knobs are allowed.

Final knob values:

| Tier | HOLEOUT_SCALE | MISHIT | TROUBLE_COST |
|---|---|---|---|
| 0 | 1.0151 | 0.01 | 0.55 |
| 5 | 1.0206 | 0.02 | 0.60 |
| 10 | 1.0481 | 0.03 | 0.65 |
| 15 | 1.0547 | 0.05 | 0.70 |
| 20 | 1.0568 | 0.07 | 0.75 |
| 25 | 1.1267 | 0.09 | 0.80 |
| 30 (modeled) | 1.1210 | 0.11 | 0.85 |

Tier 30's `HOLEOUT_SCALE` is the least-squares line across the six calibrated published scales above, evaluated at 30, matching the standing tier-30 rule used everywhere else in `data.py`. `MISHIT[30]` and `TROUBLE_COST[30]` were untouched by this task; they already sat on the same LSQ-style extrapolation from the prior release.

After calibration, every published tier lands within 0.0001 strokes of its target:

| Tier | Model (post) | Published | Gap (post) |
|---|---|---|---|
| 0 | 4.1999 | 4.2000 | -0.0001 |
| 5 | 4.4999 | 4.5000 | -0.0001 |
| 10 | 4.8000 | 4.8000 | +0.0000 |
| 15 | 5.1000 | 5.1000 | -0.0000 |
| 20 | 5.3999 | 5.4000 | -0.0001 |
| 25 | 5.9001 | 5.9000 | +0.0001 |

Max gap after calibration: 0.0001 strokes (tier 25), against a 0.15-stroke tolerance.

The mid-handicap and high-handicap tiers needed the biggest scale moves because the pre-calibration holeout construction under-weighted how much worse a bogey golfer's short game gets relative to a scratch player's, so nudging `HOLEOUT_SCALE` up (never past 1.13, well inside the declared [0.8, 1.6] range) closed each tier's gap without touching any published anchor. Tier 25 needed the largest single move because its published aggregate (5.9) sat furthest from what the uncalibrated tour-to-scratch offset chain alone produced (5.36), a 0.54-stroke starting gap versus 0.05-0.23 strokes at the other five published tiers.

One test needed updating alongside this change: `test_holeout_hits_anchors_exactly` in `tests/test_model.py` compared `strokes_to_holeout()` (which applies `HOLEOUT_SCALE`) against the raw, unscaled `E_HOLEOUT` anchor value. That comparison only held while `HOLEOUT_SCALE` was uniformly 1.0; `model.py`'s docstring for `strokes_to_holeout` already flagged this as temporary ("this factor is 1.0 for all tiers today and may be calibrated in Task 7"). The test now compares against `s * data.HOLEOUT_SCALE[tier]`, preserving the same exact-match rigor at the new scale. The golden pin `test_expected_score_golden_pin` also moved, from 4.991488064215653 to 5.204051925307641, because `HOLEOUT_SCALE[15]` moved off 1.0; both changes are noted in the test file comments and travel with this commit.

Recalibrated headline numbers:

- `neutral_distance(400, 10)["threshold"]` = 236.6 yd; `benchmark_score(400, 10)` = 4.899
- `neutral_distance(400, 15)["threshold"]` = 217.8 yd; `benchmark_score(400, 15)` = 5.204
- `neutral_distance(400, 20)["threshold"]` = 209.2 yd; `benchmark_score(400, 20)` = 5.516
- `club_verdict(360, 20)["best"]` = driver (scores: driver 5.306, wood 5.347, hybrid 5.430, iron 5.460)

---

## Origin episode (added 2026-07-12)

**Source:** Hack It Out Golf podcast, Saturday Morning Golf Stat, ["SMS - 400 Yard Hole, Drive Length for 0SG, Scratch and 10"](https://www.hackitoutgolf.com/sms-400-yard-hole-drive-length-for-0sg-scratch-and-10/), released Jul 3, 2026. Retrieved 2026-07-12 (episode page; Apple Podcasts URL returned HTTP 500 on this visit). Hosts: Mark Crossfield (@4golfonline), Lou Stagner (@LouStagner), Greg Chalmers (@GregChalmersPGA); show account @HackItOutGolf (x.com/HackItOutGolf, retrieved 2026-07-12). Episode data source per show notes: Arccos Golf.

Show notes quote, verbatim: "How far do you need to hit it—in the fairway—to break even on a strokes gained against your handicap peers?" The show-notes page publishes no numeric answers and no transcript; the in-audio numbers are NOT recorded here and must not be quoted or paraphrased without listening (standing rule). Framing difference to disclose wherever the episode is credited: the episode's question conditions on the drive finding the fairway; the 002 model prices fairway/rough/trouble odds instead of conditioning on fairway.

## Bailout threshold constant (added 2026-07-12)

`OB_COST = 2.0` strokes per out-of-bounds drive (stroke and distance). MODELED: the standard strokes-gained rule of thumb for a stroke-and-distance penalty off the tee; no per-handicap published table used. Sensitivity range 1.5 to 2.5, carried in the peer-review addendum. Threshold formula: excess OB probability p* = (E_alt − E_driver) / OB_COST.
