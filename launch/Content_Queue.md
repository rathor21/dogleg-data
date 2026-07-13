# Content Queue — drafted, review before posting

Voice check applied: no em dashes, no filler adverbs, active voice, sources named, modeled labeled. Every number below already exists in the published charts; nothing new is claimed.

## Post 3 (X): the 240-yard crossover — Mon Jul 13

> Strangest finding in the fairway-vs-rough data, and it needed no modeling at all.
>
> In @LouStagner's published Arccos data, a 20-handicap's rough ball at 240 to 250 yards out scores BETTER than a fairway ball at the same distance. A 15-handicap crosses the same line at 250.
>
> Past that range neither ball reaches the green, and the rough ball rolls out farther with less spin.
>
> I tried to confirm it a second way with the simulation. It didn't reproduce, and the writeup says so: the sim only tracks one shot's landing spot, and a few yards of bias drowns in high-handicap dispersion. This finding rests on the real scoring data alone.
>
> Full analysis: doglegdata.com/fairway-vs-rough/

Attach: chart or quote card. Tag Stagner (source credit rule).

## Post 4 (LinkedIn, Sunny): what peer review caught — Wed Jul 15

> Before publishing Dogleg Data's first analysis, I ran it through the same review I'd give a work deliverable. The review caught three bugs. All three would have shipped a wrong number to readers.
>
> Bug 1: the extrapolation for 30-handicaps doubled a single noisy gap between two published data points, which manufactured a sign-flip that looked like a golf finding and put the headline number at 9 yards. A least-squares refit across all five published handicap points moved it to 12.
>
> Bug 2: the dispersion curve borrowed a fitted quadratic's slope to extend past the data, and that slope was negative. Simulated 30-handicaps hit more greens than 20-handicaps, a result any golfer would laugh at. The fix used the slope between the last two real anchors; every inversion disappeared.
>
> Bug 3: two functions computed the same tour number on different grids, so one chart said the fairway is worth 75 yards where another said 76.67. Readers cross-referencing charts would have caught it in minutes. Both now compute on the same 1-yard grid.
>
> The habit I'm keeping: publish what broke, every analysis. An error I catch is content. An error a reader catches is damage.
>
> The analysis, the interactive model, and the review notes: doglegdata.com. Full model at Dogleg Data.

## Post 5 (X): single-chart remix, chart 5 landing patterns — ~Jul 17

> Same target, 150 yards out. Where the ball lands, by handicap.
>
> One chart, four dispersion patterns, GOLFTEC-calibrated. The 25 and 30 tiers are modeled and labeled, because the fitting data runs out at 20.
>
> The reason "aim at the flag" means something different at a 20-handicap than on tour is this picture.
>
> Run your own pattern: doglegdata.com/fairway-vs-rough/dashboard.html

## 002 launch week (article live Mon Jul 20)

Full post copy in `docs/sources/002_Post_Copy_LinkedIn.md` and `docs/sources/002_Post_Copy_X.md`. Numbers re-derived from `002_results.csv` and direct model calls on 2026-07-12.

| When | What |
|---|---|
| Mon Jul 20 | Article and calculator live (already staged and peer-reviewed). Quote-post the calculator from @DoglegData using the alt single post |
| Tue Jul 21 AM | LinkedIn 002 post (Sunny) + first comment with links |
| Wed Jul 22 | X thread, pin it; quote the 001 thread once so the old pin hands off |
| Thu-Fri Jul 23-24 | Reply windows. Answer questions with the calculator link where the question is someone's own hole |

## Post 6 (X): single-chart remix, chart 2 flat zone — ~Fri Jul 24

> Every drive distance inside the shaded zone keeps the hole within a tenth of a stroke of your usual score.
>
> Your average drive already lives inside it. That is the finding: the flat zone is wide, and you are standing in it.
>
> The 30-handicap tier is modeled and labeled; the rest is calibrated to Shot Scope's published par-4 scores.
>
> Check your zone: doglegdata.com/tee-shot-distance/tool.html

Attach: chart2_flat_zone.png.

## Post 7 (X): the number to remember — ~Mon Jul 27

> 230.
>
> A 10-handicap who drives it 230 on a 360-yard par 4 stays within a tenth of a stroke of the score a typical 10-handicap posts there. That is 28 yards under the tier's own average drive.
>
> The gap between what you think the hole demands and what it charges is the whole analysis.
>
> Run your own hole: doglegdata.com/tee-shot-distance/tool.html

Attach: chart5_quote_card.png. The "28 yards under" phrasing matches the published caption exactly; it comes from the unrounded 231.2-yard threshold against the 259-yard tier average (259 − 231.2 = 27.8). Do not restate the average as a bare 259 next to the rounded 230, or readers will compute 29 and flag the mismatch.

## Post 8 (LinkedIn, Sunny): the calibration story — ~Wed Jul 29

> How do you benchmark a golf model when the table you need does not exist?
>
> No one publishes par-4 scores by hole length by handicap. For Dogleg Data's second analysis I needed exactly that, so the model calibrates its own benchmark: its expected scores, averaged across a par-4 length mix, must reproduce Shot Scope's published average par-4 scores at all six published handicap bands. Final calibration gap: 0.0001 strokes. A Monte Carlo harness agrees with the analytic model within 0.003.
>
> The parts that stay modeled stay labeled: the 30-handicap tier, the length resolution, the mishit and trouble knobs. Readers trust labeled numbers more, not less.
>
> The analysis and the calculator: doglegdata.com. Full model at Dogleg Data.

## Scramble Reads template (recurring, first real submission)

> Scramble read from @[submitter]:
> [Distance A] in the fairway vs [distance B] in [light/moderate/deep] rough, [handicap] handicaps.
>
> The model says: break-even is [N] yards. You had [M]. Play the [fairway/rough] ball.
>
> [Chart-2-style graphic]
>
> Bring me yours. Real distances, real lies. I'll run it through the model.

Production notes: 30 minutes each. Credit the submitter by handle. If week 1 has no submissions, run a televised or famous scramble decision instead (growth plan week 6 fallback, pulled forward).

## Reply-with-a-chart bank (48-hour rule)

Standing pairings so replies take minutes, not drafting sessions:
- "lay up vs go for it" arguments → chart 1 + break-even explorer link
- "always punch out of rough" → chart 2 severity grid
- "amateurs should play like pros" → chart 5 landing patterns
- GIR stats quoted as decision proof → chart 4 + the honesty note (single-shot GIR undersells a good lie decision; strokes-to-hole-out prices in the easier miss)
- distance-vs-accuracy debates past 240 → the crossover finding, Stagner credited
