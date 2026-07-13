# LinkedIn Post: Analysis Nº 002 (Sunny, personal profile)

Ship: Tuesday July 21, morning. Article and tool live Monday July 20; X thread follows Wednesday July 22.

**Carousel image order (5 images):** chart1_cost_line.png, chart2_flat_zone.png, chart3_decomposition.png, chart4_club_map.png, chart5_quote_card.png

**Posting notes:** Post from the personal profile. No link in the body; links go in the first comment, posted immediately after publishing. No hashtags in the body.

Every number re-derived from `analysis/002-tee-shot-distance/outputs/002_results.csv` and direct model calls on 2026-07-12. The 230 figure rounds from a 231.2-yard threshold, a convention disclosed in `Peer_Review_002_Tee_Shot.md`.

---

## Post

Two weeks ago I launched Dogleg Data. Analysis Nº 002 went live this morning, and it starts with the question every par 4 asks: how far do you need to hit it?

Golf culture prices the tee shot in carry distance. The math prices it in strokes, and the strokes say you need less than you think. A 10-handicap can hit it 230 off the tee on a 360-yard par 4 and stay within a tenth of a stroke of the score a typical 10-handicap posts there. That is 28 yards under the tier's own average drive.

The model plays the whole hole, because a 220-yard drive on a 400-yard par 4 looks fine until you price the 180-yard approach it creates. Tee shot dispersion sets the odds of fairway, rough, and trouble. The leftover yardage and lie set the expected strokes to hole out. The sum is an expected score for the hole, and the number worth remembering from chart 1 is the cost line: the drive distance where the hole starts costing more than a tenth of a stroke against your own number. It sits under every tier's average drive, at every par-4 length from 300 to 480 yards.

Two findings my data and product friends will want to poke at:

1. A shorter drive with the same club costs less than golfers think. A 15-handicap driving 220 instead of their usual 236 on a 400-yard hole loses 0.09 strokes, and every hundredth of it is the longer approach. Published accuracy numbers sit close to flat across handicaps; the club you swing sets the dispersion, not the carry you get from it.

2. The driver wins every cell of the club grid, all seven handicap tiers by all ten hole lengths, and it never wins by much. The 3-wood's worst case anywhere is 0.12 strokes. Hit the club you trust; the cost never tops an eighth of a stroke.

The methodology note, because that is the standard here: no published table of par-4 scores by hole length by handicap exists. So the benchmark is modeled, calibrated until the model reproduces Shot Scope's published par-4 averages at all six published handicap bands within 0.0001 strokes, with a Monte Carlo harness agreeing within 0.003. The 30-handicap tier is a least-squares extrapolation and carries a modeled label on every chart. Peer review ran before publish. It found no must-fix items this time, two should-fix items that are already resolved, and the notes publish with the analysis, same as last time.

The calculator takes a par 4, your handicap, and your typical drive, and prices your tee shot. Link in the first comment. Full model at Dogleg Data.

If you golf: bring me the par 4 you argue about. If you don't: the calibration method is the part worth poking.

---

## First comment (post immediately after publishing)

Analysis Nº 002, How Far Do You Need to Hit It?: https://doglegdata.com/tee-shot-distance/

The par-4 tee shot calculator (open in any browser, run your own hole): https://doglegdata.com/tee-shot-distance/tool.html

Analysis Nº 001, Fairway vs. Rough by Handicap, if you missed the launch: https://doglegdata.com/fairway-vs-rough/

Sources: Shot Scope performance data (driving distance, club distances, accuracy, and average par-4 scores by handicap band, via MyGolfSpy's published transcriptions) · Lou Stagner / Arccos Golf (tee shot targets, fairway geometry) · Mark Broadie, Golfmetrics (dispersion and proximity by skill group) · The 30-handicap tier and the length-resolved benchmark are modeled and labeled; full source log with URLs and retrieval dates in the repo.
