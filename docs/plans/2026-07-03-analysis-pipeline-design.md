# Dogleg Data — Flagship Analysis Pipeline (002–007)

Date: 2026-07-03 · Status: approved by Sunny (order confirmed in session) · Author: Claude, direction by Sunny

Purpose: the ranked release pipeline for the six flagship analyses after Fairway vs. Rough (001). Order is the release order. Slot 002 carries the strongest idea because launch-window traction compounds; every later slot has a stated reason beyond raw strength. This document supersedes the growth plan's penciled "flyer lie / spin variance" as Analysis 002 (moved to the bench, reason below). Everything else in the growth plan and launch strategy stands.

Cadence: one flagship per month (growth plan sustainable floor). Every release is a full flagship: five charts, a dashboard module, a long-form caption plus X alt version, and a peer review document before anything publishes.

---

## Ranking criteria

Order was set by four tests, applied in this priority:

1. **Traction potential.** Does it start or settle an argument golfers already have? Arguments travel; tables don't.
2. **Non-repetition.** No two adjacent releases share a question type. 001 was a tee/approach decision model, so 002 cannot be one.
3. **Strategic payload.** Does the release open a door beyond the post (collab pitch, citation window, new audience)?
4. **Data availability.** Published anchors must exist before the idea earns a slot. Ideas that fail the source hunt drop to the bench, not to a lower slot.

Seasonality breaks ties: decision pieces land in playing season, diagnosis and planning pieces land in the off-season.

---

## The pipeline

| # | Release | Window | Question type | One-line hook |
|---|---|---|---|---|
| 002 | What separates a 0 from a 10 from a 20 from a 30 | Aug 2026 | Diagnosis | Same course, four golfers: where the strokes go |
| 003 | The 3-putt zone | Sep 2026 | Putting decision | The distance where lag beats charge, by handicap |
| 004 | Go for it or lay up? | Oct 2026 | Tee/approach decision | Par-5 math at your handicap, not Rory's |
| 005 | What "being a 15" actually means | Nov 2026 | Statistics | You beat your handicap once in five rounds. That's the system working |
| 006 | Practice ROI: where your next stroke is cheapest | Dec 2026 | Synthesis | The improvement map built from 002–005 |
| 007 | The free aim-point model | Jan 2027 | Strategy | DECADE-style aim points at amateur dispersion, free, sources shown |

---

## Per-release scope

### 002 — What separates a 0 from a 10 from a 20 from a 30 (Aug)

**Question.** Where do the strokes actually go between handicap tiers: driving, approach, short game, or putting? Settles "drive for show, putt for dough" with a strokes-gained decomposition at four tiers.

**Why this slot.** Strongest traction candidate that does not repeat 001's question. Introduces a second dataset in release two, which reads as range rather than a one-trick model. It is also the permissionless collab pitch the launch strategy names (marketing-ideas #52): an analysis built entirely on Shot Scope's published benchmarks, credited and tagged, is both content and the future partnership opener. The citation-pitch window (growth plan weeks 10–11) opens with two flagships live.

**Data.** PUBLISHED: Shot Scope publishes performance benchmarks at six handicap bands: 0, 5, 10, 15, 20, 25 (per their benchmark feature pages and strokes-gained ebook). Broadie 2011 ShotLink Table 9 anchors the tour-side context. MODELED: no 30 band exists in Shot Scope's public data; the 30 column extrapolates by least-squares across all six published bands (never a single last delta) and carries the modeled label in every chart, caption, and table where it appears. **Verification gate:** before any chart, pull the current Shot Scope benchmark tables, confirm the six tiers and the specific stats published per tier, and log exact page URLs and retrieval dates. If published tiers changed, re-scope before modeling.

**Charts (sketch).** 1: stacked strokes-lost decomposition, four tiers side by side. 2: the approach gap isolated (Shot Scope's own published claim that fairways-hit barely separates tiers while approach play does; verify the exact figure at the gate). 3: short game and putting gaps. 4: tour vs amateur contrast (Broadie). 5: "your 10 strokes to the next tier" summary card. Dashboard module: pick two tiers, see the gap decomposition.

**Distribution.** Tag Shot Scope on every post using their data. The quote-card number is whichever single gap is most counterintuitive after verification. Reply-with-chart target: any "putting is everything" take from an account with reach.

**Risks.** Shot Scope could object to derived use of their published tables; mitigation is the growth plan's goodwill rule (credit, tag, link, quote rather than reproduce, ask when in doubt). The 30 tier is fully modeled; the labeling discipline is the defense.

### 003 — The 3-putt zone (Sep)

**Question.** From what distance does trying to make it cost more than lagging, by handicap? Output is a decision rule: the lag line.

**Why this slot.** First green-side flagship; rotates question type after a diagnosis piece. September is still playing season, and the output is a rule a golfer uses Saturday. Highly calculator-friendly, which feeds the dashboard's "run your own numbers" positioning.

**Data.** PUBLISHED: PGA Tour make rates by distance (public stats); Stagner/Arccos amateur make rates and 3-putt rates by handicap from his newsletter tables; Shot Scope putting benchmarks by band. MODELED: expected-putts curves between published distance points; any tier interpolation. **Verification gate:** confirm amateur make-rate tables exist by handicap tier at usable distance resolution. If amateur curves exist only for aggregate amateurs, the handicap split becomes modeled and labeled, or the analysis reframes as tour-vs-amateur.

**Charts (sketch).** Make-rate curves by tier; 3-putt probability by distance; the lag line per tier; expected strokes surface; a famous televised putt run through the model. Dashboard: enter distance and handicap, get make %, 3-putt %, and the verdict.

**Risks.** Putting data is the most published territory in golf; novelty must come from the decision rule, not the curves. If the lag line turns out flat across handicaps, that null result publishes as the finding (honesty is the brand).

### 004 — Go for it or lay up? (Oct)

**Question.** Par-5 second shots and driveable par-4s: when does going for it gain strokes at each handicap?

**Why this slot.** The strongest pure argument in the pool, held back two releases because it shares tee/approach decision DNA with 001. By October it reads as the model maturing (same machinery, new decision) rather than repetition. Reuses the 001 strokes-gained framework, which keeps a month's build honest.

**Data.** PUBLISHED: Broadie 2011 Table 9; Stagner/Arccos distance and dispersion tables; GOLFTEC dispersion. MODELED: amateur go-for-it success rates by handicap (published data here is thin; expect heavy modeling, labeled). **Verification gate:** hunt for published amateur par-5 scoring by strategy before building; Stagner has posted par-5 material, confirm what exists at the time of build.

**Charts (sketch).** Break-even success rate by handicap; expected strokes go vs lay by distance-to-green; the lay-up distance question (does laying back to a full wedge help; tour data says mostly no, test at amateur dispersion); dispersion overlay on a real hole; decision card. Dashboard: distance, lie, handicap in; verdict out.

**Risks.** DECADE overlap; the differentiation is handicap-specific inputs, free access, and shown work. Cite Fawcett where the tour logic matches.

### 005 — What "being a 15" actually means (Nov)

**Question.** Round-to-round variance by handicap: how often you shoot your number, the real distribution around it, expected best-of-20, and what one great round does and does not mean.

**Why this slot.** Off-season slot for a piece that needs no playing season. High viral ceiling ("you beat your handicap once every five rounds" is quote-card material, credited to Stagner). Different question type again: statistics, not decisions. Feeds every sandbagging argument on golf X.

**Data.** PUBLISHED: Stagner newsletter #97 ("What do golfers actually shoot") and #52 (scoring averages by course and slope); his published rules of thumb (beat your handicap roughly one round in five; scoring average roughly three over course handicap); USGA/WHS handicap system documentation. MODELED: full score distributions between published anchors. **Verification gate:** re-pull the newsletter tables and confirm exact figures before quoting; the one-in-five and three-over figures above are from search-result summaries and must be verified against the primary newsletters before any chart.

**Charts (sketch).** Score distribution by tier; probability of beating handicap by margin; expected best and worst of 20; "is your buddy a sandbagger" chart (odds of shooting X under); day-to-day identity chart (the range a 15 actually occupies). Dashboard: enter index, get your distribution.

**Risks.** Stagner owns this territory; the piece must credit him heavily and add the interactive model and decision framing he does not ship. Complementary, never adversarial.

### 006 — Practice ROI: where your next stroke is cheapest (Dec)

**Question.** Given the gaps measured in 002–005, where does a golfer at each tier buy the next stroke with the least effort?

**Why this slot.** December is improvement-planning season. It is deliberately late: it synthesizes the three prior flagships, so it cannot ship earlier, and it converts the pipeline's accumulated findings into the most practically useful piece. Strong email-list content (the "what to work on this winter" card is a natural lead magnet refresh).

**Data.** PUBLISHED: the verified benchmark gaps from 002, 003, and 005 sources. MODELED: stroke-per-practice-hour assumptions have no published anchor; this release carries the highest modeled share in the pipeline and says so in the caption. If no defensible effort model survives peer review, the piece reframes as "the gap map" (where the strokes are, without effort claims), which stands on published data alone. **Verification gate:** the reframe decision is the gate; make it at peer review, not after.

**Charts (sketch).** Gap-size by category per tier; cost-per-stroke ranking (modeled, labeled); the "wrong practice" chart (time spent vs strokes available, if a published time-allocation survey exists; hunt for one); tier-jump roadmap; winter plan card. Dashboard: your tier, your weakest category, the ranked plan.

**Risks.** The effort model is attackable; the reframe path is the mitigation and is decided by peer review, not by deadline pressure.

### 007 — The free aim-point model (Jan)

**Question.** Where should you aim, off the tee and into greens, given amateur dispersion at your handicap? New season, new strategy piece.

**Why this slot.** Opens year two with the most product-like flagship: an aim-point calculator is the strongest "run your own numbers" artifact yet and the clearest free-DECADE positioning. January golfers plan; a strategy overhaul piece fits. Absorbs the driver-vs-3-wood chart (the bench notes why it is not its own flagship).

**Data.** PUBLISHED: GOLFTEC dispersion data; Stagner/Arccos dispersion and distance tables; Broadie for tour aim logic. MODELED: dispersion ellipses between published handicap anchors; penalty-weighted aim shifts. **Verification gate:** confirm GOLFTEC dispersion is published at handicap resolution, not only as aggregate amateur; the model's tiers inherit whatever resolution survives the hunt.

**Charts (sketch).** Dispersion ellipse by tier; aim-shift vs trouble map on a real hole; driver vs 3-wood at every tier (the absorbed chart); expected strokes by aim point; the one-rule summary. Dashboard: hole layout presets, your tier, the aim point.

**Risks.** Closest to DECADE's paid territory; same mitigation as 004. Highest build complexity in the pipeline; January follows the two most reusable builds (006 reuses 002–005; 007 gets the full month).

---

## The bench

Ideas that lost their slot, kept with reasons so re-ranking is easy:

- **Flyer lie / spin variance** (was penciled as 002 in the growth plan). Published amateur data on flyer-lie spin is thin; the data hunt has already slipped once. It returns to the pipeline the day a source hunt succeeds. Cutting it from 002 is this document's one override of the growth plan.
- **Driver vs 3-wood off the tee.** Real question, but its core (fairway value by handicap) is 001's finding re-angled. Runs as chart 3 of release 007 instead of six weeks of flagship.
- **Take one more club (under-clubbing tax).** Strong single chart, not a flagship. Feed to Scramble Reads or a mid-cycle single-chart post.
- **Go-for-it variants (punch-out vs hero shot).** Extends the scramble framework; amateur recovery success rates are unpublished, so it needs the same data luck as flyer lies. Bench until sourced.
- **Wind/weather value by handicap.** No published amateur anchor found; would be nearly all modeled. Fails ranking test 4.

---

## Standing rules (apply to every release)

1. **Source hunt first.** Each flagship starts with its verification gate. No charts before the gate passes and sources are logged with URLs and retrieval dates.
2. **Published vs modeled discipline.** Per the project instructions: separation labeled in every chart, caption, and table, every time; extrapolation by least-squares across all published anchors; headline numbers independently re-derived from raw sources before delivery.
3. **Peer review before publication.** Must-fix / should-fix / minor with sign-off, every release. Publish what broke (the signature move).
4. **Cross-checks.** Where a release touches a prior release's numbers (006 especially), the numbers must agree across releases or the discrepancy is stated in the caption.
5. **Deliverables per release.** Five PNG charts (matplotlib, navy/teal/amber/red on white, badge and source line), long-form caption plus X alt version, dashboard module (Chart.js, self-contained), peer review document, /cite exports.

## Re-rank triggers

Review the order at each monthly metrics Sunday. Re-rank if:

- A verification gate fails (the release drops to the bench; the next slot moves up).
- Stagner or Shot Scope publishes substantially the same analysis (pivot the release to the interactive-model angle or swap slots).
- A Scramble Reads submission or news moment makes a bench idea suddenly timely.
- Launch metrics show the dashboard outdrawing the posts (per the strategy doc's day-30 gate, tool-shaped releases like 007 move up).

## Sources consulted for this plan

Shot Scope benchmark tiers (0/5/10/15/20/25): [Shot Scope strokes gained](https://shotscope.com/us/discover/features/strokes-gained/), [Shot Scope strokes-gained ebook](https://shotscope.com/ebook/Strokes_Gained.pdf), [Bunkered: Shot Scope strokes gained benchmarking](https://www.bunkered.co.uk/gear/shot-scope-strokes-gained-benchmarking/). Scoring distributions: [Lou Stagner newsletter #97: What do golfers actually shoot](https://newsletter.loustagnergolf.com/p/what-do-golfers-actually-shoot), [newsletter #52: scoring averages by course and slope rating](https://newsletter.loustagnergolf.com/p/scoring-averages-by-course-and-slope-rating). Figures quoted from these sources in this plan are provisional until each release's verification gate re-pulls them; nothing here publishes externally without that check.
