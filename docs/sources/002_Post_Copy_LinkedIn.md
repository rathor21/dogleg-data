# LinkedIn Post: Analysis Nº 002 (Sunny, personal profile)

Ship: Friday July 24, late morning, the day the article and tool go live. The X thread follows Saturday July 25 morning so the two posts do not split each other's reach (001 mechanics kept).

**Carousel image order (6 images):** 002_chart1_cost_line.png, 002_chart2_flat_zone.png, 002_chart3_decomposition.png, 002_chart4_club_map.png, 002_chart6_bailout.png, 002_chart5_quote_card.png

**Posting notes:** Post from the personal profile. No link in the body; links go in the first comment, posted right after publishing. No hashtags. Tag the Hack It Out Golf company page in the credit line if LinkedIn offers one; host tags ride on the X thread.

Numbers re-derived from `analysis/002-tee-shot-distance/outputs/002_results.csv` and direct model calls, 2026-07-24. The 230 rounds from a 231.2-yard threshold, disclosed in `Peer_Review_002_Tee_Shot.md`. Rev 4 peer review cleared publication 2026-07-24. Copy voice matches the published article (plain golfer language; the humanizer pass ran on both).

---

## Primary post (strategy breakdown)

Three weeks ago the Hack It Out Golf podcast asked a question I could not put down: how far do you need to hit it, in the fairway, to score like your handicap?

I built a model to answer it at every handicap. Analysis Nº 002 went live this morning.

The headline: 230 yards. That is all a 10-handicap needs off the tee on a 360-yard par 4 to score like a typical 10-handicap. It is also 28 yards under that group's average drive.

And the part that sold me on publishing: the hosts answered their own question on air with Arccos data. 230 for scratch, 200 for a 10-index, drive in the fairway. My model runs on Shot Scope data and never saw their numbers. Under the same setup it says 228 and 208. Two datasets, two methods, one answer.

Three arguments golfers have on every tee box, settled with numbers:

1️⃣ You are long enough
↳ At every handicap and every par-4 length from 300 to 480 yards, the distance where a hole starts costing you strokes sits below your group's average drive. The distance you already have is closer to enough than the ads admit.

2️⃣ The 3-wood is insurance, and insurance has a price
↳ On an open hole it costs you less than a tenth of a stroke next to the driver. It pays off in one situation: you lose a ball with the driver about once every two rounds, on drives the wood would keep in play. Count your last ten rounds before you buy the safe play.

3️⃣ The second shot is the whole bill
↳ Drive 220 instead of your usual 236 on a 400-yard hole and the cost is about a tenth of a stroke, all of it from the longer approach. The model plays the full hole, so the 180 yards in gets priced with the drive that created it.

The fine print, because that is the standard here: no published table of par-4 scores by hole length by handicap exists, so the benchmark is modeled and calibrated until it reproduces Shot Scope's published par-4 averages at every published handicap band. A separate simulation agrees with the model to a rounding error. Peer review ran four times before publish and the notes ship with the analysis.

The calculator is free. Your par 4, your handicap, your driver, your backup club, your fairway width. It tells you what to expect on the hole, how that compares with a typical golfer at your handicap, and whether driver or the backup is the play.

The question came from Mark Crossfield, Lou Stagner, and Greg Chalmers at Hack It Out Golf. Thank you for the nerd snipe.

Full model at Dogleg Data; link in the first comment. Which number should I run next?

---

## Alternate post (personal story)

The podcast episode was ten minutes long. It cost me three weeks.

Hack It Out Golf ran a Saturday stat segment in early July: how far do you need to hit it, in the fairway, to score like your handicap? They ran it for scratch and a 10-index.

I wanted the whole answer. Every handicap, every par-4 length, and the part that nagged at me: the second shot. A 220-yard drive on a 400-yard hole looks harmless until you stand over the 180-yard approach it left you.

So I built a model that plays the full hole. Where your drives tend to land sets the odds of fairway, rough, and trouble. The yardage left sets what the second shot and everything after it will cost. The sum is the score your drive bought.

The bill for that 220-yard drive came to about a tenth of a stroke, all of it at the approach. And the distance where that hole starts costing a 15-handicap real strokes came out to 218 yards, against a 236-yard average drive. When the hosts answered their own question on air, their numbers and mine landed within a few yards of each other, from different data.

Analysis Nº 002 went live this morning, with a free calculator that runs your hole, your handicap, your driver, and your backup club.

Full model at Dogleg Data; link in the first comment. What piece of golf advice should get tested against real data next?

---

## First comment (post right after publishing, either version)

Analysis Nº 002, 230 Yards Is Enough: https://doglegdata.com/tee-shot-distance/

The tee shot calculator (run your own hole, backup club and fairway width included): https://doglegdata.com/tee-shot-distance/tool.html

The episode that started it: Hack It Out Golf, "SMS: 400 Yard Hole, Drive Length for 0SG, Scratch and 10" (Jul 3): https://www.hackitoutgolf.com/sms-400-yard-hole-drive-length-for-0sg-scratch-and-10/

Analysis Nº 001, Fairway vs. Rough by Handicap: https://doglegdata.com/fairway-vs-rough/

Sources: Shot Scope performance data (via MyGolfSpy's published transcriptions) · Lou Stagner / Arccos Golf · Mark Broadie, Golfmetrics · Modeled figures labeled on every chart; full source log with URLs and retrieval dates in the repo.
