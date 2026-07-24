# Dogleg Data — Flagship Analysis Pipeline (002–008)

Date: 2026-07-03 (rev 3, 2026-07-11: cadence moved to biweekly, new 002 inserted at Sunny's direction, everything renumbered) · Status: approved by Sunny (order confirmed in session) · Author: Claude, direction by Sunny

Purpose: the ranked release pipeline for the seven flagship analyses after Fairway vs. Rough (001). Order is the release order. This document supersedes the growth plan's penciled "flyer lie / spin variance" as Analysis 002 (moved to the bench, reason below) and the growth plan's one-per-month cadence. Everything else in the growth plan and launch strategy stands.

Cadence: one flagship every two weeks, set by Sunny on July 11 to build momentum off the July 6 launch. Machinery reuse between releases is what makes the pace feasible; any release that cannot pass its verification gate on the biweekly clock drops to the bench rather than shipping thin. Every release is a full flagship: five charts, a dashboard module, a long-form caption plus X alt version, and a peer review document before anything publishes.

---

## Ranking criteria

Order was set by four tests, applied in this priority:

1. **Traction potential.** Does it start or settle an argument golfers already have? Arguments travel; tables don't.
2. **Non-repetition.** Adjacent releases should not share a question type. One stated exception exists (002, below).
3. **Strategic payload.** Does the release open a door beyond the post (collab pitch, citation window, new audience)?
4. **Data availability.** Published anchors must exist before the idea earns a slot. Ideas that fail the source hunt drop to the bench, not to a lower slot.

The old seasonality tiebreaker (decision pieces in playing season, planning pieces in the off-season) no longer binds: the biweekly cadence lands the whole pipeline inside playing season, through mid-October.

**Why 002 is the tee-shot distance piece.** The prompt was Hack It Out Golf's Saturday Morning Golf Stat "SMS: 400 Yard Hole, Drive Length for 0SG, Scratch and 10" (Jul 3, 2026; Crossfield, Stagner, Chalmers), credited and tagged at launch. Sunny's call, July 11: lead the biweekly cadence with the club-off-the-tee question ("how far do you need to hit it for no strokes gained at your handicap, with the approach shot priced in"). It rides the launch window with the strongest argument-starter in the pool (distance culture vs what the math says), and it reuses 001's dispersion and lie machinery, which is what makes a nine-day build honest. This knowingly breaks the non-repetition rule (001 and 002 both live in tee/approach decision territory); the momentum trade is stated and accepted. The shot-shape piece moves to 003 with its citation logic intact. Full spec: [2026-07-11-002-tee-shot-distance-design.md](2026-07-11-002-tee-shot-distance-design.md).

---

## The pipeline

| # | Release | Window | Question type | One-line hook |
|---|---|---|---|---|
| 002 | How far do you need to hit it? | Jul 24, 2026 (slipped from Jul 20) | Tee-club decision | You don't need to hit it as far as you think. Here's the number, at your handicap |
| 003 | One shape, two shapes, or straight? | Aug 3, 2026 | Ball-flight strategy | Tour pros pick a side. Should you? |
| 004 | What separates a 0 from a 10 from a 20 from a 30 | Aug 17, 2026 | Diagnosis | Same course, four golfers: where the strokes go |
| 005 | Go for it or lay up? | Aug 31, 2026 | Tee/approach decision | Par-5 math at your handicap, not Rory's |
| 006 | The 3-putt zone | Sep 14, 2026 | Putting decision | The distance where lag beats charge, by handicap |
| 007 | What "being a 15" actually means | Sep 28, 2026 | Statistics | You beat your handicap once in five rounds. That's the system working |
| 008 | Practice ROI: where your next stroke is cheapest | Oct 12, 2026 | Synthesis | The improvement map built from 004–007 |

---

## Per-release scope

### 002 — How far do you need to hit it? (Jul 24, slipped from Jul 20)

**Question.** Which club should you hit off the tee (driver, wood/hybrid, or iron) at every handicap? Answered through the minimum drive distance that keeps expected score at the tier benchmark on a given par 4, with the approach shot the drive creates priced into a full-hole expected-strokes model. Own-tier baseline: strokes gained zero means you played the hole like a typical golfer at your handicap.

**Scope.** This release has its own approved design spec: [2026-07-11-002-tee-shot-distance-design.md](2026-07-11-002-tee-shot-distance-design.md). Summary: analytic expected-strokes model with Monte Carlo as a peer-review validation harness; five charts (neutral-distance headline curve, the flat zone, the tee/approach cost decomposition, the club verdict map, the quote card); a par-4 calculator tool with three inputs (hole length, handicap, typical drive distance).

**Data.** PUBLISHED: Shot Scope benchmarks (club off the tee, distance by band), Stagner/Arccos distance and dispersion by handicap, Broadie 2011 amateur tables, GOLFTEC dispersion, the 001 source log. MODELED: tier-resolution expected-strokes curves between published anchors, labeled. **Verification gate:** confirm Shot Scope publishes club-off-tee splits at handicap resolution; if not, the piece reframes from club verdicts to labeled distance bands. Gate runs first, per the spec.

**Why this slot.** See ranking criteria above. Absorbs the benched "driver vs 3-wood off the tee" idea.

### 003 — One shape, two shapes, or straight? (Aug 3)

**Question.** Should a golfer play one set shape, work it both ways, or aim to hit it straight? Is a player's left-right distribution unimodal or bimodal, what does that answer cost in strokes, and where should they aim given the answer? Tour data answers it for pros; simulation extrapolates it to amateurs.

**Origin.** GolfWell podcast, June 10, 2026: "Is Zero Path Actually Bad? Two Coaches Disagree" (Justin Kraft and Dr. Luke Benoit debating club path, face angle, and why so many tour pros draw the driver). No public transcript exists; listen to the episode before drafting and log the specific claims worth testing. The published post credits the episode as the prompt. This is the Benoit/GolfWell citation pitch in artifact form, per the launch strategy's reply-with-a-chart play; the 90-day goal (one podcast citation) runs through this release.

**Why this slot.** Was 002 in rev 2; displaced by Sunny's July 11 call to lead with the distance piece. The citation logic holds at 003: the biweekly cadence lands it August 3, still inside the episode's relevance window, and it introduces the tour-vs-amateur simulation machinery (Monte Carlo over face/path distributions) that later releases reuse.

**Data.** PUBLISHED (tour side): PGA Tour Tour Tracker launch data as analyzed in the Golf Analytics blog's "Ball Flights on PGA Tour" (spin-axis distributions; per-player fade/draw splits; driver vs non-driver shape rates); Trackman published tour averages and their draw-vs-fade distance analysis (curvature-per-degree-of-spin-axis relationship); Broadie 2011 for strokes-gained context. MODELED (amateur side): no published amateur shape-consistency data exists; amateur left-right distributions are simulated from face/path variance assumptions anchored to GOLFTEC published swing data and the dispersion anchors already used in 001, with sensitivity analysis on every assumption and the modeled label everywhere. The unimodal-vs-bimodal answer for amateurs is a modeled result and the caption says so plainly. **Verification gate:** re-pull the Tour Tracker analysis figures from the primary post and cross-check against Trackman's published averages before any chart; confirm what GOLFTEC actually publishes at handicap resolution; log URLs and retrieval dates.

**The Benoit study.** Benoit maintains an unpublished study archive (49 golfers, Foresight launch monitor, no-feedback shots) with an explicit "ask before you distribute" note. Do not touch it without permission. The right move: after the analysis is drafted on published data, write to him once — the episode prompted the analysis, here is the draft, and if his study data could test the amateur simulation he is welcome to co-verify or correct it. That is simultaneously the citation pitch, a data-goodwill play, and a possible future collab. If he declines or ignores it, the piece stands on published tour data plus labeled simulation.

**Charts (sketch).** 1: tour spin-axis distribution (the unimodal answer for pros, from published data). 2: one-shape vs two-shape players, per-player shape splits. 3: simulated amateur distributions by handicap tier (modeled, labeled): does a 20-handicap even have a shape? 4: the cost surface — strokes lost by strategy (one shape / both / straight) per tier. 5: aim consequences — where each strategy says to aim on a real hole. Dashboard: pick tier and strategy, see the distribution and the aim point.

**Distribution.** Post credits and tags the GolfWell episode, Kraft, and Benoit on day one. Quote-card number: whichever tour shape split survives verification (the Tour Tracker analysis suggests roughly half of tour drivers are fades; verify before quoting). Reply-with-chart standing order for any shape-debate thread.

**Risks.** The amateur half is the most simulation-heavy work the brand has shipped; the defense is aggressive labeling, published-anchor documentation, and sensitivity analysis in the peer review. Tour Tracker analysis is a third-party blog derivation of public data, not a primary league release; cite it as the analysis it is and cross-check against Trackman. Do not paraphrase specific podcast claims without listening first.

### 004 — What separates a 0 from a 10 from a 20 from a 30 (Aug 17)

**Question.** Where do the strokes actually go between handicap tiers: driving, approach, short game, or putting? Settles "drive for show, putt for dough" with a strokes-gained decomposition at four tiers.

**Why this slot.** Strongest traction candidate after the two decision pieces, and a clean question-type rotation (diagnosis after two decision releases). It is the permissionless collab pitch the launch strategy names (marketing-ideas #52): an analysis built entirely on Shot Scope's published benchmarks, credited and tagged, is both content and the future partnership opener. It lands with three flagships live behind it, right as the citation-pitch window opens.

**Data.** PUBLISHED: Shot Scope publishes performance benchmarks at six handicap bands: 0, 5, 10, 15, 20, 25 (per their benchmark feature pages and strokes-gained ebook). Broadie 2011 ShotLink Table 9 anchors the tour-side context. MODELED: no 30 band exists in Shot Scope's public data; the 30 column extrapolates by least-squares across all six published bands (never a single last delta) and carries the modeled label in every chart, caption, and table where it appears. **Verification gate:** before any chart, pull the current Shot Scope benchmark tables, confirm the six tiers and the specific stats published per tier, and log exact page URLs and retrieval dates. If published tiers changed, re-scope before modeling.

**Charts (sketch).** 1: stacked strokes-lost decomposition, four tiers side by side. 2: the approach gap isolated (Shot Scope's own published claim that fairways-hit barely separates tiers while approach play does; verify the exact figure at the gate). 3: short game and putting gaps. 4: tour vs amateur contrast (Broadie). 5: "your 10 strokes to the next tier" summary card. Dashboard module: pick two tiers, see the gap decomposition.

**Distribution.** Tag Shot Scope on every post using their data. The quote-card number is whichever single gap is most counterintuitive after verification. Reply-with-chart target: any "putting is everything" take from an account with reach.

**Risks.** Shot Scope could object to derived use of their published tables; mitigation is the growth plan's goodwill rule (credit, tag, link, quote rather than reproduce, ask when in doubt). The 30 tier is fully modeled; the labeling discipline is the defense.

### 005 — Go for it or lay up? (Aug 31)

**Question.** Par-5 second shots and driveable par-4s: when does going for it gain strokes at each handicap?

**Why this slot.** The strongest pure argument left in the pool, held three releases behind 002 because both live in tee/approach decision territory. By late August it reads as the model maturing (same machinery, new decision) rather than repetition, and it lands inside playing season. Reuses the 001/002 strokes-gained framework, which keeps a two-week build honest.

**Data.** PUBLISHED: Broadie 2011 Table 9; Stagner/Arccos distance and dispersion tables; GOLFTEC dispersion. MODELED: amateur go-for-it success rates by handicap (published data here is thin; expect heavy modeling, labeled). **Verification gate:** hunt for published amateur par-5 scoring by strategy before building; Stagner has posted par-5 material, confirm what exists at the time of build.

**Charts (sketch).** Break-even success rate by handicap; expected strokes go vs lay by distance-to-green; the lay-up distance question (does laying back to a full wedge help; tour data says mostly no, test at amateur dispersion); dispersion overlay on a real hole; decision card. Dashboard: distance, lie, handicap in; verdict out.

**Risks.** DECADE overlap; the differentiation is handicap-specific inputs, free access, and shown work. Cite Fawcett where the tour logic matches.

### 006 — The 3-putt zone (Sep 14)

**Question.** From what distance does trying to make it cost more than lagging, by handicap? Output is a decision rule: the lag line.

**Why this slot.** Rotates to the green after four long-game releases; the pipeline owes the putting surface a turn. Highly calculator-friendly, which feeds the dashboard's "run your own numbers" positioning, and the output is a rule that works on a practice carpet year-round. (The old November "indoor season" rationale died with the monthly cadence.)

**Data.** PUBLISHED: PGA Tour make rates by distance (public stats); Stagner/Arccos amateur make rates and 3-putt rates by handicap from his newsletter tables; Shot Scope putting benchmarks by band. MODELED: expected-putts curves between published distance points; any tier interpolation. **Verification gate:** confirm amateur make-rate tables exist by handicap tier at usable distance resolution. If amateur curves exist only for aggregate amateurs, the handicap split becomes modeled and labeled, or the analysis reframes as tour-vs-amateur.

**Charts (sketch).** Make-rate curves by tier; 3-putt probability by distance; the lag line per tier; expected strokes surface; a famous televised putt run through the model. Dashboard: enter distance and handicap, get make %, 3-putt %, and the verdict.

**Risks.** Putting data is the most published territory in golf; novelty must come from the decision rule, not the curves. If the lag line turns out flat across handicaps, that null result publishes as the finding (honesty is the brand).

### 007 — What "being a 15" actually means (Sep 28)

**Question.** Round-to-round variance by handicap: how often you shoot your number, the real distribution around it, expected best-of-20, and what one great round does and does not mean.

**Why this slot.** Question-type rotation again: statistics, not decisions. High viral ceiling ("you beat your handicap once every five rounds" is quote-card material, credited to Stagner), and it feeds every sandbagging argument on golf X. Needs no playing-season tie-in, so it can sit late in the run without cost.

**Data.** PUBLISHED: Stagner newsletter #97 ("What do golfers actually shoot") and #52 (scoring averages by course and slope); his published rules of thumb (beat your handicap roughly one round in five; scoring average roughly three over course handicap); USGA/WHS handicap system documentation. MODELED: full score distributions between published anchors. **Verification gate:** re-pull the newsletter tables and confirm exact figures before quoting; the one-in-five and three-over figures above are from search-result summaries and must be verified against the primary newsletters before any chart.

**Charts (sketch).** Score distribution by tier; probability of beating handicap by margin; expected best and worst of 20; "is your buddy a sandbagger" chart (odds of shooting X under); day-to-day identity chart (the range a 15 actually occupies). Dashboard: enter index, get your distribution.

**Risks.** Stagner owns this territory; the piece must credit him heavily and add the interactive model and decision framing he does not ship. Complementary, never adversarial.

### 008 — Practice ROI: where your next stroke is cheapest (Oct 12)

**Question.** Given the gaps measured in 004, 006, and 007, where does a golfer at each tier buy the next stroke with the least effort?

**Why this slot.** It synthesizes the pipeline's accumulated findings, so it cannot ship earlier. It converts three prior flagships into the most practically useful piece, and mid-October is when playing season winds down and improvement planning starts in the northern half of the audience. Strong email-list content (the "what to work on" card is a natural lead magnet refresh).

**Data.** PUBLISHED: the verified benchmark gaps from 004, 006, and 007 sources. MODELED: stroke-per-practice-hour assumptions have no published anchor; this release carries the highest modeled share in the pipeline after 003 and says so in the caption. If no defensible effort model survives peer review, the piece reframes as "the gap map" (where the strokes are, without effort claims), which stands on published data alone. **Verification gate:** the reframe decision is the gate; make it at peer review, not after.

**Charts (sketch).** Gap-size by category per tier; cost-per-stroke ranking (modeled, labeled); the "wrong practice" chart (time spent vs strokes available, if a published time-allocation survey exists; hunt for one); tier-jump roadmap; the plan card. Dashboard: your tier, your weakest category, the ranked plan.

**Risks.** The effort model is attackable; the reframe path is the mitigation and is decided by peer review, not by deadline pressure. Cross-release consistency matters most here: every number quoted from 004, 006, and 007 must match those releases exactly.

---

## The bench

Ideas that lost their slot, kept with reasons so re-ranking is easy:

- **The free aim-point model** (was slot 007 in rev 1). Release 003 now carries the core aiming logic (chart 5 and the dashboard's aim-point output), so a standalone aim-point flagship would repeat it too soon. It returns as a year-two candidate: the full calculator (hole presets, tier dispersion, penalty weighting) is the most product-shaped artifact on the bench.
- **Flyer lie / spin variance** (was penciled as 002 in the growth plan). Published amateur data on flyer-lie spin is thin; the data hunt has already slipped once. Note: the same GolfWell episode behind release 003 discusses the flyer lie myth, and Benoit has an Instagram post on it; if the Benoit contact from 003 warms up, this is the natural second conversation and the piece un-benches the day a source hunt succeeds.
- ~~**Driver vs 3-wood off the tee.**~~ Off the bench as of rev 3: absorbed into release 002, which generalizes it to driver vs wood/hybrid vs iron with the approach shot priced in.
- **Take one more club (under-clubbing tax).** Strong single chart, not a flagship. Feed to Scramble Reads or a mid-cycle single-chart post.
- **Punch-out vs hero shot (trouble recovery).** Extends the scramble framework; amateur recovery success rates are unpublished, so it needs the same data luck as flyer lies. Bench until sourced.
- **Wind/weather value by handicap.** No published amateur anchor found; would be nearly all modeled. Fails ranking test 4.

---

## Standing rules (apply to every release)

1. **Source hunt first.** Each flagship starts with its verification gate. No charts before the gate passes and sources are logged with URLs and retrieval dates.
2. **Published vs modeled discipline.** Per the project instructions: separation labeled in every chart, caption, and table, every time; extrapolation by least-squares across all published anchors; headline numbers independently re-derived from raw sources before delivery.
3. **Peer review before publication.** Must-fix / should-fix / minor with sign-off, every release. Publish what broke (the signature move).
4. **Cross-checks.** Where a release touches a prior release's numbers (008 especially), the numbers must agree across releases or the discrepancy is stated in the caption.
5. **Deliverables per release.** Five PNG charts (matplotlib, house style, badge and source line), long-form caption plus X alt version, dashboard module (Chart.js, self-contained), peer review document, /cite exports.
6. **Biweekly gate discipline.** A release that cannot pass its verification gate in time slips to the bench and the next release moves up; the cadence holds, the content flexes.

## Re-rank triggers

Review the order at each metrics check-in. Re-rank if:

- A verification gate fails (the release drops to the bench; the next slot moves up).
- Stagner, Shot Scope, or a coach with reach publishes substantially the same analysis (pivot the release to the interactive-model angle or swap slots).
- Benoit responds to the 003 contact with data or interest (the flyer-lie bench idea may jump the queue).
- A Scramble Reads submission or news moment makes a bench idea suddenly timely.
- Launch metrics show the dashboard outdrawing the posts (per the strategy doc's day-30 gate, tool-shaped releases move up).
- The biweekly pace proves unsustainable two releases in a row (revert to monthly at the next natural break and restate windows).

## Sources consulted for this plan

Release 002 data: Shot Scope benchmark and club-performance pages, [Shot Scope strokes gained](https://shotscope.com/us/discover/features/strokes-gained/), [Shot Scope strokes-gained ebook](https://shotscope.com/ebook/Strokes_Gained.pdf), Stagner/Arccos distance and dispersion tables, Broadie 2011, GOLFTEC dispersion, plus the 001 source log; full source plan in the [002 design spec](2026-07-11-002-tee-shot-distance-design.md). Release 003 origin and data: [GolfWell podcast, "Is Zero Path Actually Bad? Two Coaches Disagree" (Jun 10, 2026)](https://podcasts.apple.com/sg/podcast/is-zero-path-actually-bad-2-coaches-disagree/id1049039619?i=1000772076838), [Luke Benoit Golf study archive](https://www.lukebenoitgolf.com/support-for-shot-shape), [Golf Analytics: Ball Flights on PGA Tour](https://golfanalytics.wordpress.com/2024/10/20/ball-flights-on-pga-tour/), [Trackman: updated tour averages](https://www.trackman.com/blog/golf/introducing-updated-tour-averages), [Trackman: draw or fade to maximize distance](https://www.trackman.com/blog/golf/draw-or-fade-to-maximize-distance). Shot Scope benchmark tiers (0/5/10/15/20/25): links above plus [Bunkered: Shot Scope strokes gained benchmarking](https://www.bunkered.co.uk/gear/shot-scope-strokes-gained-benchmarking/). Scoring distributions: [Lou Stagner newsletter #97: What do golfers actually shoot](https://newsletter.loustagnergolf.com/p/what-do-golfers-actually-shoot), [newsletter #52: scoring averages by course and slope rating](https://newsletter.loustagnergolf.com/p/scoring-averages-by-course-and-slope-rating). Figures quoted from these sources in this plan are provisional until each release's verification gate re-pulls them; nothing here publishes externally without that check.
