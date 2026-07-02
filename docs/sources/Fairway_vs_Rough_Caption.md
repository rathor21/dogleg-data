# Fairway vs. Rough, by Handicap: Post Package (v2)

**Interactive companion:** `Fairway_vs_Rough_Dashboard.html`, a self-contained page (open it in any browser, no install needed) with three tools: a break-even explorer, the Monte Carlo GIR% simulator, and a scramble decision calculator you can run your own numbers through. Worth linking directly for the LinkedIn/data-community audience and anyone on the Golfwell side who wants to poke at the model themselves.

**Images (5 total):**
1. `chart1_handicap_breakeven.png`: hero chart, distance-equivalency plus the "why" mechanism panel
2. `chart2_severity_scramble.png`: rough-severity grid plus your real scramble decision
3. `chart4_tenyard_gap.png`: the realistic 10-yard scramble gap, with an honest caveat about what it leaves out
4. `chart5_landing_pattern.png`: plain-language illustration of what the simulation is doing
5. `chart3_montecarlo_gir.png`: same-distance GIR comparison (optional, most redundant with #3/#4 if you need to cut to 3-4 images)

**If you need to cut to 3 images for a single post:** use 1, 2, and 5 (landing pattern). Save 3 and 4 for a follow-up or a carousel/thread. Chart 3 (same-distance GIR) is the one most easily dropped since chart 4 covers similar ground with a more realistic setup.

---

## Caption (long version)

Fairway or rough. Which ball do you play in a scramble?

Golf course wisdom says stay in the fairway, even 25 yards back. I ran the real data by handicap. The old advice is right, but only for one group of golfers, and it's not the group asking the question.

At a 150-yard approach, the fairway is worth 75 yards to a tour pro. That means a rough ball has to be 75 yards closer to tie a pro's fairway ball at 150. It peaks even higher, around 80 yards, for a shot from 140 out. The "stay in the fairway" rule was built around exactly this kind of number.

For the rest of us, that same fairway is worth a lot less. At 150 yards, it's worth 23 yards to a 10-handicap, 17 to a 20, and 12 to a 30.

I assumed going in that amateur shots are too erratic for lie to matter much. The actual explanation lives in the shape of a pro's scoring curve, not the amateur's. A tour pro's rough penalty is close to the same everywhere on the course, usually 0.16 to 0.25 strokes. But between 60 and 140 yards, a pro's score barely changes with distance. They're basically as good from 90 as they are from 60. So a small, constant penalty gets divided by an almost-flat scoring curve, and the yardage needed to cancel it out balloons to 75 or 80 yards. Amateurs never get that flat stretch. Every extra yard costs them more score, at every distance. So the same size penalty gets canceled out by a lot fewer yards.

I need to walk back part of that confound check. I first compared cut heights: tour rough at regular events runs about 2 inches, amateur municipal rough runs 1.75 to 2.5, and I concluded they overlap. But height is a weak stand-in for how punishing rough plays, and the agronomy backs that up. At Oak Hill's 2023 PGA Championship, the rough measured about 2.75 inches, in the same range as a municipal course, and it still wrecked shots, because the grass stood upright and the blades ran wide. Superintendents don't get that effect by letting rough grow taller. Oakmont's crew builds it through fertilizer programs that thicken the turf stand over months, a variable no height number captures. Shinnecock adds a second category entirely: about 125 acres of native fescue, sedge, and bluestem outside the primary rough, closer to knee-high than 2 inches, where a ball is often lost rather than found.

So here's the honest version. I can't rule out that U.S. Open-style rough plays harder than anything in this dataset, and the height comparison I ran doesn't settle that question. What I can say is that Broadie's numbers come from regular-season Tour events, not majors, and regular Tour rough, thick as it is, isn't grown in with that same density program. The 75 to 80 yard number was never built from U.S. Open rough. The confound doesn't touch the headline claim, but it's a fair flag on anything I'd build for a major-specific version of this. It also means chart 2's "deep rough" column, which I'd anchored to a general thick-rough field test, undersells true U.S. Open native rough. I relabeled it so it doesn't imply otherwise.

You also had a hunch about amateur wedge distances, that there's a point where a comfortable partial wedge turns into a full swing and consistency drops off. There's real data on this, and it mostly holds up. Stagner's Arccos database tracks proximity as a percentage of starting distance, by handicap, fairway shots only. Every group I checked (0, 10, and 20 handicap) has the same shape: proximity control gets better as you approach a sweet spot around 115 to 135 yards, then gets worse again past it. It's not a cliff, and it's not one-directional: shots inside 100 yards are relatively less accurate too, so the real shape is a U, not a drop-off. What does scale hard with handicap is how much worse things get on the far side of that sweet spot. A scratch player's relative proximity roughly doubles between the sweet spot and 220 yards. A 20-handicap's more than doubles again on top of that. Chart 1's third panel plots this next to the tour explanation, so you can see both mechanisms side by side.

Rough type changes the math too. For a 20-handicap at 150 yards, the fairway is worth 8 yards in light rough, 17 in moderate rough, and 29 in a thick primary cut. That last number is still a muni-course "deep rough," not true U.S. Open native fescue, which this model doesn't have enough data to size. Same player, same distance, different call depending on what the rough looks like.

I hit this exact spot in a scramble last weekend. My ball sat in light rough, 35 yards closer than my partner's fairway ball. Two of my partners wanted the fairway ball. The model says an 8-yard edge was enough for a 20-handicap in light rough. I had 35. It wasn't close, and chart 2 walks through the math.

One more real finding, and this one needed no modeling at all: in Lou Stagner's published Arccos data, a 20-handicap's rough ball at 240 to 250 yards scores BETTER than a fairway ball at the same distance, and a 15-handicap crosses the same line at 250. Past that range, neither ball is reaching the green, and the rough ball is rolling out farther with less spin. I tried to confirm this a second way, by adding a distance-dependent bias to the Monte Carlo model. It didn't reproduce the effect. That simulation only tracks where one shot lands, and at higher-handicap dispersion levels a few yards of bias gets buried in the noise. So this finding rests on the real scoring data alone, not on the simulation. I'd rather tell you that than paper over it.

You asked a sharper version of the scramble question too: what if the gap is a realistic 10 yards, not 35? Chart 4 answers it directly, fairway at 125 against rough at 115, across handicaps and rough types. And it comes with a real catch: measured as "did this one shot find the green," 10 yards of rough almost never fully closes the gap on the fairway ball. But that's an incomplete way to keep score. A rough shot that misses from 10 yards closer usually leaves an easier up-and-down than a fairway shot that misses from farther out, and the real strokes-to-hole-out data already prices that in (that's why a 20-handicap's true break-even in light rough is 8 yards, not more). The single-shot simulation and the full scoring data are answering two different questions, and chart 4 says so directly rather than picking whichever number sounds better.

Chart 5 turns the same idea into a picture instead of a percentage. Two greens, same shot pattern, only the lie changes. Dots that land inside the green are solid, the rest are faded. It's the same 20-handicap, 150-yard example from chart 3, drawn out so you can see the shot pattern instead of reading a number.

Sources: PGA TOUR numbers come from Broadie's 2011 ShotLink study, Table 9, over 8 million shots. Amateur break-even numbers come from Lou Stagner and Arccos Golf, roughly 1 billion shots, published directly (10-index and 20-index are real published values; 30-index is my extrapolation across their full published 0-to-20 range, and it's labeled as such on the chart). Amateur proximity-by-distance numbers come from a separate Stagner/Arccos newsletter, also real, also unmodeled. Rough-severity scaling comes from a 2021 USGA/R&A rough-difficulty simulation, checked against a 2025 Golf Digest field test and against public rough-height figures for regular Tour events, municipal courses, and U.S. Open setups. The dispersion simulation is calibrated to real GOLFTEC swing data but stretched well past its measured range to cover higher handicaps, and the tour dispersion figure specifically assumes pros are 25% tighter than a scratch amateur, a judgment call, not a cited number. I've marked the dispersion simulation as the most heavily modeled piece of the set.

I ran a peer review on this before sending it out, and built an interactive dashboard alongside it (linked below). Between the two, it caught three real bugs, not wording nits. The first: the 30-index extrapolation originally doubled a single noisy bin-to-bin difference from the published table, which produced a fake sign flip in the 30-handicap "worth" number around 200 yards, an artifact of the method, not a finding about golf. I refit it using all five published handicap points instead of two, which fixed the flip and moved the 150-yard, 30-handicap number from 9 to 12 yards. The second: the Monte Carlo dispersion model for high handicaps was, for a narrow band of distances, showing a 30-handicap hitting greens slightly MORE often than a 20-handicap, which is backwards and traced to an extrapolation formula that let shot dispersion shrink past 13-handicap instead of continuing to grow. The third turned up while wiring the dashboard to the same code chart 2 uses: the tour "worth" number at 150 yards came out as 75 in chart 1 but 76.67 in chart 2 and the CSV, same claim, two different answers, because chart 1 computed it on a fine grid and everything else linearly interpolated a handful of sparse points instead. All three are fixed now, everything downstream is regenerated, and chart 1's numbers changed slightly as a result. I'd rather you hear that from me than find it yourself.

Bring a real scramble read of your own. I'll run it through the model.

---

## Shorter alt version (X / character-constrained)

Golf wisdom says stay in the fairway, even 25 yards back. For a tour pro, that's right: the fairway is worth about 75 yards to them at 150 out.

For a 20-handicap, it's worth 17 yards. Past 240 yards, in Stagner's real Arccos data, it's worth less than nothing.

Distance beats lie for the rest of us. Full breakdown and a real scramble example inside.

---

## Notes for follow-up posts
- Natural part 2: the flyer-lie / spin-variance question. I don't have enough data to model it rigorously yet, so it stays out of this post rather than getting a hand-wavy treatment.
- Natural part 3: once your branding and handle are set, re-skin the charts (they're built on a plain navy/teal/amber/red palette on white, specifically so a template can be dropped on top) and repost.
- Chart 4's honesty note (GIR vs. strokes-to-hole-out) got a strong reaction in review. Worth its own short post if you want to go deeper on "why single-shot stats can undersell a good lie decision."
