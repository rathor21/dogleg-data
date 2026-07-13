# X Thread: How Far Do You Need to Hit It? (from the Dogleg Data account)

Ship: Wednesday July 22, the morning after the LinkedIn post. Article and tool go live Monday July 20; days between posts so they don't cannibalize each other's reach (001 mechanics kept).

**Posting notes:** No link until the final tweet. Attach images where marked; chart5_quote_card.png is the spare if a 5th image is wanted anywhere. A t.co link counts as 23 characters. Pin this thread after posting; quote the 001 thread once from it ("Analysis Nº 002 is live") so the old pin hands off.

Every number below re-derived from `analysis/002-tee-shot-distance/outputs/002_results.csv` and direct model calls on 2026-07-12. The 230 figure rounds from a 231.2-yard threshold, a convention disclosed in `Peer_Review_002_Tee_Shot.md`.

---

## Thread

**Tweet 1** (no image, no link)

How far do you need to hit it? Golf prices the tee shot in carry distance. The math prices it in strokes, and the strokes say you need less than you think. A 10-handicap can drive it 230 on a 360-yard par 4 and stay within a tenth of a stroke of their usual score on the hole:

**Tweet 2** [attach chart1_cost_line.png]

The model plays the whole hole. Dispersion sets the odds of fairway, rough, and trouble; the leftover yardage and lie set expected strokes to hole out. The cost line: the drive distance below which the hole costs you more than 0.1 strokes against your own handicap's number.

**Tweet 3** [attach chart2_flat_zone.png]

The cost line sits under every tier's average drive at every par-4 length from 300 to 480. A 15-handicap on a 400-yard hole: cost line 218, average drive 236. Scratch needs about 80 more yards than a 30-handicap (a modeled tier) to stay at their own number.

**Tweet 4** (no image)

The question that started this: what does a shorter drive with the same club cost? A 15-handicap driving 220 instead of their usual 236 on a 400-yard par 4 loses 0.09 strokes, all of it the longer approach. A shorter carry with the same club buys no fairways.

**Tweet 5** [attach chart4_club_map.png]

Clubbing down is where accuracy enters. For a 15-handicap on a 400-yard hole the 3-wood pays 0.15 strokes of longer approach and buys back 0.07 in tighter misses: net 0.08. The driver wins all 70 cells of the grid, never by more than 0.12. Hit the club you trust.

**Tweet 6** (no image)

What's modeled: the tier benchmark. It reproduces Shot Scope's published average par-4 scores at all six published handicap bands (max calibration gap 0.0001 strokes; Monte Carlo agrees within 0.003). The 30-handicap tier is a least-squares extrapolation, labeled on every chart.

**Tweet 7** (link goes here) [optional: attach chart5_quote_card.png]

Analysis Nº 002 from Dogleg Data. Enter a par 4, your handicap, and your typical drive; the model prices the tee shot: https://doglegdata.com/tee-shot-distance/tool.html

Sources: Shot Scope (via MyGolfSpy), @LouStagner / Arccos, Mark Broadie. Bring me the par 4 you argue about.

---

## Alt single post (for quote-posting the calculator, matches the caption's X version)

A 10-handicap can hit it 230 off the tee on a 360-yard par 4 and stay within a tenth of a stroke of their usual score.

The cost of a shorter drive is the approach it leaves, and it is smaller than you think.

Run your own hole: https://doglegdata.com/tee-shot-distance/tool.html
