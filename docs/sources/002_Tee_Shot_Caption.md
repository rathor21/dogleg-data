# 002 — How Far Do You Need to Hit It? (Caption)

Ship date: 2026-07-20 · Numbers re-derived from `analysis/002-tee-shot-distance/outputs/002_results.csv` on 2026-07-12. Every figure below traces to the model and the source log; modeled steps named in the disclosure paragraph.

## Long-form caption

This one started with a podcast. Hack It Out Golf's Saturday Morning Golf Stat (Jul 3, 2026) asked: "How far do you need to hit it—in the fairway—to break even on a strokes gained against your handicap peers?" Crossfield, Stagner, and Chalmers ran it for scratch and a 10-index. This analysis runs it at every handicap, and prices the miss odds instead of conditioning on the fairway.

Golf culture prices the tee shot in carry distance. The math prices it in strokes, and the strokes say you need less than you think. A 10-handicap can hit it 230 off the tee on a 360-yard par 4 and stay within a tenth of a stroke of the score a typical 10-handicap posts there. That is 28 yards under the tier's own average drive.

The model behind that number plays the whole hole, which was the point of building it. A 220-yard drive on a 400-yard par 4 looks fine until you price the 180-yard approach it creates, so the model prices it: tee shot dispersion sets the odds of fairway, rough, and trouble, the leftover yardage and lie set the expected strokes to hole out, and the sum is an expected score for the hole. Strokes gained zero means you played the hole like your handicap says you should. We call the interesting number the cost line: the drive distance below which the hole starts costing you more than 0.1 strokes against your own number.

Chart 1 is the headline. The cost line sits well under every tier's average drive, at every par-4 length from 300 to 480. Scratch needs about 80 more yards than a 30-handicap to stay at their own number, and each tier carries real headroom: a 15-handicap's cost line on a 400-yard hole is 218 yards against a 236-yard average drive.

Chart 2 shows why the headroom exists. Expected score falls as drives get longer, then goes flat. Past the cost line the curve buys you almost nothing: the shaded zone in each panel marks every drive distance that keeps the hole within a tenth of a stroke of your number. Your average drive already lives inside it.

Chart 3 answers the question that started this analysis. When a 15-handicap drives 220 instead of their usual 236 on a 400-yard par 4, the cost is 0.09 strokes, and every hundredth of it is the longer approach. A shorter drive with the same club buys no fairways; the published accuracy numbers are close to flat across handicaps, and the club you swing sets the dispersion regardless of how far it carries. Accuracy enters when the club changes: the 3-wood pays 0.15 strokes of approach cost and buys back 0.07 of it in tighter misses, for a net cost of 0.08.

Chart 4 generalizes that trade. The driver wins every cell of the grid, all seven handicap tiers by all ten hole lengths, and it never wins by much. The worst case anywhere for the 3-wood is 0.12 strokes. Hit the club you trust; the cost never tops an eighth of a stroke.

Chart 6 prices the exception. The 3-wood or a 5/7-wood earns the tee once your driver donates an extra OB about every 26 holes (a 15-handicap at 400 yards; 23 to 40 across tiers, OB modeled at 2 strokes). Irons never earn it on a straight par 4: a 4-iron costs 0.23, a 7-iron 0.39.

The verdicts, plainly: hit driver on most par 4s; the 3-wood is a 0.04-to-0.09-stroke luxury on open holes; irons off the tee are donations; and the bailout club pays only past the OB threshold above.

Chart 5 is the number to remember: 230.

**What is modeled.** The tier benchmark is the model's own expected score at each tier's average drive, calibrated so the model reproduces Shot Scope's published average par-4 scores at all six published handicap bands (max calibration gap 0.0001 strokes; a Monte Carlo harness agrees with the analytic model within 0.003 strokes). No published table of par-4 score by hole length by handicap exists, so length resolution is modeled and labeled. The 30-handicap tier extrapolates by least squares across the six published bands. Lateral dispersion inverts Shot Scope's published fairway-hit rates through Stagner's published 36-yard fairway. Mishit rates and trouble costs are modeled calibration knobs with declared ranges. The OB cost behind the bailout threshold is modeled at 2.0 strokes (stroke and distance), sensitivity 1.5 to 2.5. Every chart carries the labels.

**Sources.** Hack It Out Golf, "SMS: 400 Yard Hole, Drive Length for 0SG, Scratch and 10" (the prompt; credited and tagged on launch). Shot Scope performance data (driving distance, club distances, accuracy, and average par-4 scores by handicap band, via MyGolfSpy's published transcriptions), Lou Stagner / Arccos (tee shot targets, fairway geometry), Mark Broadie (Golfmetrics, dispersion and proximity by skill group). Full source log with URLs and retrieval dates published in the repo.

**Run your own hole.** Enter a par 4, your handicap, and your typical drive: doglegdata.com/tee-shot-distance/tool.html

## X version (launch thread, quote card on T1, chart 6 on T2)

T1 (248 chars):

.@HackItOutGolf asked: how far do you need to hit it to break even against your handicap peers?

I built the model. A 10-handicap needs 230 on a 360-yard par 4. 28 yards UNDER the tier's average drive.

h/t @LouStagner @4golfonline @GregChalmersPGA

T2 (247 chars):

The full answer, at every handicap, with the approach shot priced in. Plus the one that surprised me: the 3-wood only pays off if your driver donates an extra OB every 26 holes.

Article + free calculator: https://doglegdata.com/tee-shot-distance/

## X alternates

Day-2 standalone (chart 1 as image, 230 chars):

Drive length for zero strokes gained, 400-yard par 4:

Scratch: 256
10-handicap: 237
15-handicap: 218
20-handicap: 209

Every one sits under that tier's average drive. The number you need is shorter than the number you're chasing.

Alternative launch (link in reply, 277 chars):

I ran @HackItOutGolf's 0SG question at every handicap. Four verdicts:

1. Driver wins every tier, every length
2. The 3-wood is a 0.04-0.09 stroke luxury
3. Irons off the tee donate 0.2-0.4
4. Bench the driver once it costs an extra OB every 26 holes

Model + calculator, free:
