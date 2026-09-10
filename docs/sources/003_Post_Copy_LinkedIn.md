# LinkedIn Posts: Analysis Nº 003 (Sunny, personal profile)

Ship date: not set. The article's own build comment flags the publish date as a placeholder until Sunny sets it (`site/augusta-12/index.html`, line 4), so this plan uses relative spacing: Day 1 ships with the article and tool live, Day 3 and Day 5 follow at the same weekday slot Day 1 used. Two-day gaps, wider than the one-day gap 001 and 002 kept between their LinkedIn and X posts, since all three posts here land on the same platform and the same audience, and need more room so one does not eat the next one's reach.

**Assets used:** `hero_portrait.mp4` (Day 1), `carousel.pdf` trimmed to 9 pages (Day 3, see card order below), a new screen recording of the aim sandbox not produced by the launch kit (Day 5). Source: `launch/003-social/README.md`.

**Posting notes that hold across all three posts:** personal profile, like 002. Links go in the first comment, never the body; a link in the body caps a LinkedIn post's reach. No hashtags, matching the 002 convention. No tags: `@HackItOutGolf`, `@LouStagner`, `@4golfonline`, and `@GregChalmersPGA` earned their credit on 002 because their podcast question started that piece. This release did not come from them, so their handles stay off it, and no other repo doc names a handle that fits.

Every fact and number below traces to `site/augusta-12/index.html` (the article), `analysis/003-augusta-12/outputs/003_moves.csv`, `docs/sources/003-scoping/viz-trends.md`, `launch/003-social/README.md`, or `docs/adr/0001-name-augusta-in-003.md`. Full ledger at the end. Copy voice matches 002 (plain golfer language, first person, Sunny as founder); the humanizer pass and the house rules check both ran on this file.

---

## Posting plan

**Day 1, native video: `hero_portrait.mp4`, 1080x1350 (4:5), link in the first comment.**

Lead with the animation despite what the algorithm rewards right now. `docs/sources/003-scoping/viz-trends.md` §3 reports that document carousels now out-reach video on LinkedIn by a wide margin (about 1,387 impressions per carousel against 703 for a single image and 589 for text-only, per the Closely tracking cited there), and that video "went from king to commoner" through 2025. Post the video first anyway: the animation is the only asset that shows the model in motion before a reader has read a word, and it is the piece Sunny wants leading regardless of the reach math. The carousel two days later picks up the format the algorithm favors now and gives the piece a second run for anyone who scrolled past the video.

Spec: MP4, H.264, well under LinkedIn's 200 MB cap. Keep the cut under a minute; the same research finds video under 60 seconds in 4:5 draws the most comments. About 80 to 85 percent of LinkedIn video plays muted, so burn in captions and open on a frame that reads with the sound off: a title card over the settled hero scene, on screen for the first two seconds, before the tee shots start flying. Something short and legible works, for example "4 shots. Same hole. One hour." Caption under 1,300 characters, see Post 1 below. Post late morning on a weekday, the slot 002 used.

**Day 3, document carousel: `carousel.pdf`, trimmed to 9 pages, link in the first comment.**

The launch kit's pipeline produces 10 cards (`card_00_hero.png` through `card_09_shot-5.png`, bundled into `carousel.pdf`). The viz-trends research flags 6 to 9 slides as the length that avoids what it calls "carousel fatigue," so drop the closing `shot-5` card and post the hero cover plus the eight chapter cards: nine pages, the top of that range.

Card order (matches `cards.json` in the launch kit):
1. Hero (settled scene, cover card)
2. Chapter 1, the question, all five handicap tiers
3. Chapter 2, the left pin
4. Chapter 3, the center pin
5. Chapter 4, the Sunday pin, the real sucker pin
6. Chapter 5, wind
7. Chapter 6, the 2019 final round (uses the hero-clip stand-in by design, per the README, not a missing capture)
8. Chapter 7, the model checked against the hole's scoring record
9. Chapter 8, the move, the full table (also a stand-in by design)

Caption under 900 characters, see Post 2 below. Late morning, same weekday slot as Day 1.

**Day 5, tool-first post: a fresh screen recording of the sandbox, link in the first comment.**

This asset is not in the launch kit; capture it fresh at `doglegdata.com/augusta-12/tool.html`, dragging the aim point through a full run. Cut it vertical, 1080x1350, under a minute, the same spec as Day 1's video. The sandbox's own interface already prints the tier, pin, and score numbers on screen as the aim point moves, so the caption requirement here is a two-second title card at the open, for example "Drag the pin. Watch the strokes," rather than a full burned-in caption track. Caption under 800 characters, built around one sandbox result a reader can reproduce step for step, see Post 3 below. Late morning, same weekday slot.

---

## Post 1 (Day 1, native video)

### Three hook options

**Cautionary Tale**
Koepka, Poulter, Molinari, and Finau put four balls in Rae's Creek within about an hour at the 2019 Masters. I ran that hole through a tee-shot model to see which of them the numbers would have forgiven.

**The Unexpected**
The 12th at Augusta National has three pins. I expected the middle one to punish mid-handicappers. The model found a different pin does the damage, and it costs every tier about the same.

**Achievement with Constraint**
Four Masters contenders found the same creek within an hour in 2019. Five simulated tee shots and a full handicap sweep later, the model says two of the hole's three pins are safe to attack at every level.

The Cautionary Tale hook leads the full post below: the 2019 Sunday is the strongest opening beat Sunny wants, and it sets up the animation and the verdict in one move.

### Full post (1,207 characters)

Koepka, Poulter, Molinari, and Finau put four balls in Rae's Creek within about an hour at the 2019 Masters. Koepka's 9-iron drifted right and rolled back off the bank. Poulter's 8-iron came up short. Molinari caught the same bank. Finau found the water outright. All four made double bogey.

I built an aim-point model for the 12th at Augusta: one dispersion oval per handicap tier, priced against the creek, the bank, and the bunkers. Analysis Nº 003 is live: five simulated tee shots, from a 10-handicap's draw to a 20-handicap's under-clubbed ball, landing on the green, in the bunker, short-sided, and in the creek.

Two of the hole's three pins are safe to attack at every tier. The back-right Sunday pin, the one closest to the water, isn't. Every tier's verdict is the same: bail. It costs scratch the most, 0.095 strokes, and a 20-handicap the least, 0.053. The water rate runs backward from what I expected: scratch's flag water rate, 19.0%, is the highest of any tier. A 20-handicap's, 13.7%, is the lowest.

Watch the animation, then drag your own aim point in the sandbox. Your tier, your pin, your wind.

Full model at Dogleg Data, link in the first comment. Which pin would you have attacked?

### First comment

Analysis Nº 003, Where to Aim at Augusta's 12th, Pin by Pin: https://doglegdata.com/augusta-12/

The aim sandbox, drag your own tier, pin, and wind: https://doglegdata.com/augusta-12/tool.html

---

## Post 2 (Day 3, carousel)

### Caption (738 characters)

The 12th at Augusta National plays 155 yards over Rae's Creek. Three pins guard the green. Two are safe to attack at every handicap. One isn't.

This carousel walks the model behind Analysis Nº 003, pin by pin: the dispersion ovals at every tier, the left pin's built-in margin, the center pin I expected to punish mid-handicaps and didn't, the back-right Sunday pin that costs every tier close to the same amount, and what an 8-yard wind penalty does to the bail call.

One card checks the model against the hole's own scoring record. Six modern seasons average 3.132 strokes. The model's Tour season average lands at 3.114.

The full aim, in yards and clubs, for every pin and tier: full model at Dogleg Data, link in the first comment.

### First comment

Analysis Nº 003, Where to Aim at Augusta's 12th, Pin by Pin: https://doglegdata.com/augusta-12/

---

## Post 3 (Day 5, the tool)

### Caption (590 characters)

Set the sandbox to a 15-handicap, the Sunday pin, calm air. Drag the aim point 7.8 yards left of the flag and about one club short of it.

The model's verdict: bail, worth 0.070 strokes. Water risk at the flag runs 15.9 percent. Bailing left drops it to 14.7 percent.

That's the back-right corner of Augusta's 12th, the pin closest to Rae's Creek. Every handicap tier bails here in calm air. The sandbox shows how far to bail and what it costs for your tier, and what wind does to the call.

Run your own pin and wind: full model at Dogleg Data, link in the first comment. What's your aim?

### First comment

The aim sandbox: https://doglegdata.com/augusta-12/tool.html

The full article, Where to Aim at Augusta's 12th, Pin by Pin: https://doglegdata.com/augusta-12/

---

## Alt text

**Video (`hero_portrait.mp4`, Day 1 and Day 5's sandbox recording):** Animated illustration of five simulated tee shots on Augusta National's 12th hole, landing in the green, a bunker, Rae's Creek, and short-sided of the pin. (Reused from the hero canvas `aria-label`, `site/augusta-12/index.html`.)

**Carousel cover (`card_00_hero.png`):** Stylized elevated three-quarter view of Augusta National's 12th hole, five simulated tee shots arcing toward the green across Rae's Creek, colored by outcome. (Reused from the `og:image:alt`, `site/augusta-12/index.html`.)

---

## Numbers used, and where each comes from

- 155 yards over Rae's Creek: `site/augusta-12/index.html`, dek and meta description.
- The 2019 final round, four players, about an hour: Koepka's 9-iron drifted right and rolled back off the bank; Poulter's 8-iron came up short; Molinari caught the same bank and rolled back; Finau found the water; all four made double bogey. Wind gusted to about 20 mph. `site/augusta-12/index.html`, Chapter 6.
- 2019 hole scoring average 3.053, 52 birdies, 200 pars, 38 bogeys, 14 doubles-or-worse, across 304 plays: Chapter 6.
- Two of the hole's three pins are safe to attack at every tier: Chapter 1, the dek.
- Sunday pin verdicts, calm air: scratch bails 7.1 yards left, worth 0.095 strokes; 10-handicap bails 7.0 yards left, worth 0.078; 15-handicap bails 7.8 yards left, worth 0.070; 20-handicap bails 8.0 yards left, worth 0.053: Chapter 4, and `analysis/003-augusta-12/outputs/003_moves.csv` rows tier 0/10/15/20, pin=sunday, wind=False.
- Sunday pin water rate at the flag: scratch 19.0% (highest of any tier), 20-handicap 13.7% (lowest): Chapter 4.
- 15-handicap Sunday pin water rate, calm: 15.9% at the flag, 14.7% at the published aim: Chapter 4, and `003_moves.csv` row tier=15, pin=sunday, wind=False.
- 15-handicap Sunday pin in wind: the bail signal crosses the tossup line at 0.049 strokes, reading as "either works": Chapter 5.
- Tour oval at the 155-yard shot: 8.4 by 5.4 yards; the model's Tour season average, 3.1142 (rounded to 3.114 in copy); six modern seasons average 3.132: Chapter 7.
- Carousel and video specs (10 cards at 1080x1350, MP4/H.264, hero at `deviceScaleFactor: 2`): `launch/003-social/README.md`.
- Carousel reach research (about 1,387 impressions per carousel against 703 for an image post and 589 for text-only; the 6-to-9-slide ideal length; video under 60 seconds in 4:5 drawing the most comments; 80 to 85 percent of LinkedIn video watched muted; captions adding 21 to 29 percent engagement): `docs/sources/003-scoping/viz-trends.md`, §3.
