# LinkedIn Post: Analysis Nº 002 (Sunny, personal profile)

Ship: Friday July 24, late morning, the day the article and tool go live. The X thread follows Saturday July 25 morning so the two posts do not split each other's reach (001 mechanics kept).

**Carousel image order (6 images):** 002_chart1_cost_line.png, 002_chart2_flat_zone.png, 002_chart3_decomposition.png, 002_chart4_club_map.png, 002_chart6_bailout.png, 002_chart5_quote_card.png

**Posting notes:** Post from the personal profile. No link in the body; links go in the first comment, posted right after publishing. No hashtags. Tag the Hack It Out Golf company page in the credit line if LinkedIn offers one; host tags ride on the X thread, which is the reply-with-a-chart channel.

Numbers re-derived from `analysis/002-tee-shot-distance/outputs/002_results.csv` and direct model calls, 2026-07-24. The 230 rounds from a 231.2-yard threshold, disclosed in `Peer_Review_002_Tee_Shot.md`. Rev 4 peer review cleared publication 2026-07-24.

---

## Primary post (strategy breakdown)

Two weeks ago the Hack It Out Golf podcast asked a question I could not put down: how far do you need to hit it, in the fairway, to break even against your handicap peers?

I built the model to answer it at every handicap. Analysis Nº 002 went live this morning.

The headline: a 10-handicap needs 230 yards off the tee on a 360-yard par 4 to stay within a tenth of a stroke of a typical 10-handicap score. That is 28 yards under the tier's average drive.

Three arguments golfers have on every tee box, priced in strokes:

1️⃣ The cost line sits under your average drive
↳ At every handicap and every par-4 length from 300 to 480 yards, the drive distance where the hole starts costing you more than 0.1 strokes sits below your tier's average. The distance you have is closer to enough than the distance the ads sell you.

2️⃣ The 3-wood is insurance, and insurance has a price
↳ On an open hole it runs 0.05 to 0.09 strokes behind the driver. It pays on one condition: you lose an extra ball to OB with the driver about once every two rounds, on drives the wood would have kept in play. Count your last ten rounds before you buy the safe play.

3️⃣ The approach shot is the whole bill
↳ Drive 220 instead of your usual 236 on a 400-yard hole as a 15-handicap and it costs 0.09 strokes, every hundredth of it from the longer second shot. The model plays the full hole, so the 180 yards in gets priced with the drive that created it.

The methodology note, because that is the standard here: no published table of par-4 scores by hole length by handicap exists, so the benchmark is modeled, calibrated until the model reproduces Shot Scope's published par-4 averages at all six published bands within 0.0001 strokes, with a Monte Carlo harness agreeing within 0.003. The 30-handicap tier is a least-squares extrapolation and carries a modeled label on every chart. Peer review ran four times before publish and the notes ship with the analysis.

The calculator is free: your par 4, your handicap, your driver at its own distance, a backup club at its own distance, your fairway width. It returns the verdict, including how often the driver has to find OB before the backup wins.

The question came from Mark Crossfield, Lou Stagner, and Greg Chalmers at Hack It Out Golf. Thank you for the nerd snipe.

Full model at Dogleg Data; link in the first comment. Which number should I run next?

---

## Alternate post (personal story)

The podcast episode was ten minutes long. It cost me two weeks.

Hack It Out Golf ran a Saturday stat segment in early July: how far do you need to hit it, in the fairway, to break even against your handicap peers? They ran it for scratch and a 10-index.

I wanted the whole answer. Every handicap, every par-4 length, and the part that nagged at me: the second shot. A 220-yard drive on a 400-yard hole looks harmless until you stand over the 180-yard approach it left you.

So I built a model that plays the full hole. Dispersion sets the odds of fairway, rough, and trouble. The leftover yardage sets the expected strokes to hole out. The sum is the score your drive bought.

The bill for that 220-yard drive: 0.09 strokes, all of it at the approach. And the distance where a 400-yard hole starts costing a 15-handicap real strokes came out to 218 yards, against a 236-yard average drive.

Analysis Nº 002 went live this morning, with a free calculator that runs your hole, your handicap, your driver, and your backup club.

Full model at Dogleg Data; link in the first comment. What piece of golf advice should get tested against real data next?

---

## First comment (post right after publishing, either version)

Analysis Nº 002, 230 Yards Is Enough: https://doglegdata.com/tee-shot-distance/

The tee shot calculator (run your own hole, backup club and fairway width included): https://doglegdata.com/tee-shot-distance/tool.html

The episode that started it: Hack It Out Golf, "SMS: 400 Yard Hole, Drive Length for 0SG, Scratch and 10" (Jul 3): https://www.hackitoutgolf.com/sms-400-yard-hole-drive-length-for-0sg-scratch-and-10/

Analysis Nº 001, Fairway vs. Rough by Handicap: https://doglegdata.com/fairway-vs-rough/

Sources: Shot Scope performance data (via MyGolfSpy's published transcriptions) · Lou Stagner / Arccos Golf · Mark Broadie, Golfmetrics · Modeled figures labeled on every chart; full source log with URLs and retrieval dates in the repo.
