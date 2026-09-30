# LinkedIn Posts: Analysis Nº 004 (Sunny, personal profile)

## Private message to Justin (NOT FOR POSTING)

Send this as a text. Nothing in it goes public.

> Justin, I built a lab where you set a student's face, path and attack angle, watch the ball fly, and text them a link to that same shot, and I'd like your read on it: https://doglegdata.com/ball-flight/tool.html

---

Analysis Nº 004 went live 2026-09-29: the article "Face, Path, and the Ball Flight Laws, in Numbers" at https://doglegdata.com/ball-flight/ and the Ball flight lab at https://doglegdata.com/ball-flight/tool.html. This copy was refreshed against the article and number ledger at commit 5d65911 (branch 004-physics). The model changed three times since the first draft: driver launch, spin and flight were recalibrated to TrackMan's 2010 chart and the driver ideal moved to +5 attack angle; face-to-path now changes loft through the lie angle; and irons gain loft as the attack angle rises, with a "Loft follows attack angle" switch on every club. The social ship date is Sunny's call. This plan keeps relative spacing: Day 1 ships once Sunny picks the date, and Days 3, 5 and 7 follow at the same weekday slot Day 1 used. Two-day gaps, as in 003, since all four posts land on the same platform and the same audience. The plan holds at four posts: the iron flip folds into Post 1 with the driver finding, and the draw-versus-fade finding is Post 2. The two rules and the slice example share Post 3.

**Assets to capture (none exist yet; the 004 release has no launch kit like 003's):**
- Day 1: a screen recording of the lab, vertical 1080x1350 (4:5), under a minute, in two parts. Part one: open the first deep link in the first comment (PGA driver on the ideal delivery), drag the attack angle from -5 to +5 with Loft follows attack angle on, then turn the switch off and drag again. Part two: open the 7-iron link, leave the switch on, and drag the attack angle from -3.9 to +3 while the carry readout falls. Read the on-screen carry against `004_Caption.md` before burning in any text, and burn in numbers from the ledger alone, for example "Tour 7-iron, -3.9 to +3 attack: carry 172 to 157 yd". Figure 3 (launch, spin and carry against attack angle, both loft lines) can run as a second image.
- Day 3: a screen recording of the draw-versus-fade comparison, 1080x1350, under a minute. Open the lab on the PGA driver, press Tour average, switch to Compare mode, pin a draw (path +4, face 0), then change the path to -4. Read the pinned and live carry and total off the screen against the ledger (draw 267 and 322, fade 273 and 293 yd) before burning in text. If Sunny wants a still, use the article's Chapter 2 numbers on a plain card.
- Day 5: a document carousel of six pages cut from the article's figures (the site's `/cite` page covers sized exports with credit). Cover card, Figure 1 (start direction from 4 degrees of face or path), a card that sets the model's 83 and 73 percent beside the 85/75 and 87/81 pairs in circulation, Figure 2 (curve against face-to-path with TrackMan's eight examples), a card for the 2.0 against 2.3 ratio, and a closing card with the slice example (21 yd of curve at path -4, 11 at path -2). If Sunny shoots a photo of Present mode on a TV, use it as a second image, with the consent of anyone in frame.
- Day 7: a screen recording of 9 Windows mode, "Fly all nine", 1080x1350, under a minute.

**Posting notes that hold across all four posts:** personal profile, like 002 and 003. Links go in the first comment, never the body. No hashtags. No tags, and no instructor is named in any public post; consent for that is pending. The nine-windows drill belongs to Tiger Woods. The recipes are Dogleg Data model output, and no post implies that Tiger published or used these numbers. Every model number in a post carries "in my model" or "the model" wording, and published numbers name TrackMan, PING or Foresight. The loft couplings (face-to-path through the lie angle, and attack angle for irons) are modeled assumptions, and Posts 1 and 2 name the geometry and the sources behind each and say what checks them.

Every fact and number below traces to `site/ball-flight/index.html` (the article), `docs/sources/004_Caption.md` (the article's number ledger), `docs/sources/004_Source_Log.md`, `docs/sources/004_Physics_Research.md`, or `docs/adr/0004-ball-flight-model.md`. Numbers are copied at the ledger's rounding. Full list at the end. The sepia and humanizer passes both ran on this file, and the house rules check ran by script.

---

## Posting plan

**Day 1, native video: the hit-up and iron flip recording, link in the first comment.**

Lead with the finding the lab was rebuilt around. The driver ideal hits up, and the "Loft follows attack angle" switch lets a viewer see the carry keep rising with it on and stop climbing with it off. The same switch turns a 7-iron's attack angle into lost carry. Both are one action a viewer can follow with the sound off. Spec matches 003's Day 1 video: MP4, H.264, 4:5, under 60 seconds, well under LinkedIn's 200 MB cap. The 003 research (`docs/sources/003-scoping/viz-trends.md` §3) reports that about 80 to 85 percent of LinkedIn video plays muted, so burn in two lines of text: "Driver: loft follows, carry keeps rising" and "7-iron: hit up, carry falls". Caption under 1,300 characters, see Post 1. Late morning on a weekday, the slot 002 and 003 used.

**Day 3, native video: draw versus fade, link in the first comment.**

The draw and fade example gives coaches a comparison they can run in the lab in three clicks. The post states the loft geometry, the check against TrackMan's own example, and the limit of the coupling. Caption under 1,300 characters, see Post 2. Same weekday slot as Day 1.

**Day 5, carousel: the two rules and the slice example, link in the first comment.**

The 003 research finds carousels out-reach video and single images on LinkedIn, so the face and curve numbers take the carousel format. Six pages sits inside the 6-to-9 range that research recommends. Caption under 1,300 characters, see Post 3. Same weekday slot.

**Day 7, nine windows: link in the first comment.**

Tiger Woods' name will draw readers to this post, so the caption credits the drill to him and labels the recipes as Dogleg Data model output. Caption under 1,300 characters, see Post 4. Same weekday slot.

The LPGA launch finding (Chapter 4) stays off LinkedIn and runs on X alone. It needs the total-distance and era caveats, and 1,300 characters cannot carry them next to the other findings.

---

## Post 1 (Day 1, native video)

### Three hook options

**Chart first**
TrackMan's 2010 driver chart gains 29 yards of carry from a -5 to a +5 attack angle at 115 mph, and the loft rises with it.

**Model first**
Hold a Tour driver's loft at 12.7 degrees in my model and hitting up stops paying near +1 degree of attack angle.

**Flip**
In my model hitting up gains a driver carry when the loft follows, and costs a Tour 7-iron 15 yards of carry from -3.9 to +3 attack angle.

The full post below opens with the chart's numbers, puts the limit on the ideal (the Tour spin trim) in the same post as the gain, and names the source and the weak point of the iron slope (one Foresight chart of unknown method), so a coach who checks the article finds the same caveats.

### Full post (1,296 characters)

TrackMan's 2010 driver chart lists 266 yards of carry at 115 mph with an attack angle of -5 degrees and 295 at +5, and the chart's optimal loft rises with the attack angle. Hold the loft still and the carry stops climbing: in my model a Tour driver at 12.7 degrees of loft carries 285 yards near +1 and 281 at +5.

I built the driver ideal in the Ball flight lab on that move: +5 attack angle, loft midway between the chart's carry and total optimizers. At 115 mph the model's PGA driver goes from 282 yards of carry and 313 total to 287 and 328. The ideal uses the chart's own strike in place of the Tour spin trim. Keep the trim and the PGA carry reads 283.

Irons run the other way. In my model each degree of upward attack adds 1.4 degrees of loft to an iron: 1.0 from swing-arc geometry and the rest from one Foresight 7-iron chart of unknown method. Take the Tour 7-iron from -3.9 degrees of attack to +3 and its carry falls from 172 yards to 157 and its total from 179 to 161. Foresight's chart at 90 mph loses 1.7 yards of carry per degree from -6 to +2, and the model, scaled to 90 mph, loses 1.8. A slope of 1.0 would cut the 7-iron's loss to about 0.6.

Turn the lab's Loft follows attack angle switch on and off to see both. Link in the first comment. Tell me the club you would flip.

### First comment

Analysis Nº 004, Face, Path, and the Ball Flight Laws, in Numbers: https://doglegdata.com/ball-flight/

The Ball flight lab, PGA driver on the ideal delivery: https://doglegdata.com/ball-flight/tool.html?c=driver&p=pga

The same lab with the Tour 7-iron, for the iron flip: https://doglegdata.com/ball-flight/tool.html?c=7i&p=pga

---

## Post 2 (Day 3, native video)

### Caption (1,294 characters)

In my model a Tour driver draw and its mirror-image fade differ in carry and total. With the path 4 degrees right and the face square, the draw carries 267 yards and totals 322. The fade carries 273 and totals 293.

The gap comes from loft. The shaft leans at the lie angle, so rolling the face closed takes loft off and rolling it open adds loft: 0.61 degree of loft per degree of face-to-path for the driver and 0.51 for the 7-iron, the cotangent of each lie angle. Less loft means less spin, a lower flight and more run-out. More loft balloons the ball and it lands short.

TrackMan's own draw-versus-fade example, one driver in a 2016 post, has a draw at 10.5 degrees of loft and 2,643 rpm running about 20 yards past a fade at 15.0 degrees and 3,768 rpm. Give the model that 4.5 degrees of loft gap and the fade spins 1,065 rpm more than the draw against TrackMan's 1,125, and the draw runs out 18 yards farther. That checks direction and rough size, and the coupling is not fitted to it.

The coupling stays a modeled assumption. I roll the head about the shaft with no shaft lean, the most the geometry allows, and I found no source that measured where golfers sit. A pure pull and a pure push stay equal in my model.

Link in the first comment. Tell me which shape you would test first.

### First comment

Analysis Nº 004, Face, Path, and the Ball Flight Laws, in Numbers: https://doglegdata.com/ball-flight/

The Ball flight lab, PGA driver: press Tour average, pin a draw (path +4, face 0), then change the path to -4: https://doglegdata.com/ball-flight/tool.html?c=driver&p=pga

---

## Post 3 (Day 5, carousel)

### Caption (1,170 characters)

Instructors teach two rules. The face sets the start line, and the gap between face and path sets the curve. I fitted a flight model to TrackMan's published Tour averages and its 2010 driver chart, and put a number on each rule.

In the model, 83 percent of a Tour driver's start direction comes from the face, and 73 percent of a 6-iron's. I could not trace the 85/75 or 87/81 pairs in circulation to a TrackMan text, so treat every share as an estimate. At 2 degrees of face-to-path the model bends a Tour driver 18.1 yards and a 6-iron 8.9, so the driver bends 2.0 times as far. TrackMan's own worked examples give 2.3.

Set a student's miss in the Ball flight lab. An average-amateur driver (94 mph, -1.8 degrees of attack, 15.1 degrees of loft) with the path at -4 degrees and the face square is a slice in my model: it starts on line, bends 21 yards and finishes 19 yards right. Pin the shot, move the path to -2, and the curve drops to 11 yards.

Copy the lab's address and text it, and the student opens the same shot on a phone. Coaches can switch to Present mode for a TV or projector. Link in the first comment. Tell me the first club and miss you would load.

### First comment

Analysis Nº 004, Face, Path, and the Ball Flight Laws, in Numbers: https://doglegdata.com/ball-flight/

The Ball flight lab, with the -4 path slice loaded: https://doglegdata.com/ball-flight/tool.html?c=driver&p=amateur&s=94&a=-1.8&l=15.1&pa=-4&f=0

---

## Post 4 (Day 7, nine windows)

### Caption (876 characters)

Tiger Woods' nine windows is a drill, and the standard reading of it is three heights crossed with three shapes. TaylorMade's 2021 video "Tiger Woods' Nine Windows" is where I got the concept. I found no launch monitor numbers for any of the nine, so I built recipes in my model for a Tour 7-iron at 92 mph.

The straight low window takes 15.3 degrees of dynamic loft and an attack angle 7.1 degrees down, and it carries 186 yards with a 26-yard peak. The straight high window takes 34.4 degrees and an attack angle 0.5 degree up, and it carries 149 yards with a 46-yard peak. Each draw adds a face 1.9 to 2.4 degrees right of target and a path 4.3 to 5.0 degrees right, and each fade mirrors it.

The drill is Tiger's. The recipes are Dogleg Data model output.

The lab's 9 Windows mode flies all nine. Link in the first comment. Tell me what you would change in the recipes.

### First comment

The Ball flight lab, 9 Windows mode is in the tab bar: https://doglegdata.com/ball-flight/tool.html

The full article, Face, Path, and the Ball Flight Laws, in Numbers: https://doglegdata.com/ball-flight/

---

## Numbers used, and where each comes from

Model numbers come from the live model through `site/ball-flight/article-numbers.js`, and the "Value now" column of `004_Caption.md` holds each value. Published numbers trace to the Source Log anchors named in the ledger.

- TrackMan 2010 carry chart at 115 mph: carry 266 yd at attack -5 and 295 at +5 (`ch-carry-dn`, `ch-carry-up`, gain 29 in `ch-carry-gain`), read from `data/ideals.json`; Source Log Anchor 4 Source 1. Published. Post 1, hook, X tweet 1. The chart's optimal dynamic loft rises with attack angle (9.2, 11.6, 14.4 degrees at -5, 0, +5 on the carry rows). Total distance gains 31 yd on the carry chart's rows (`ch-total-gain`) and 35 on the total-distance chart's (`ch-total-gain-tt`); the posts print the 31.
- Tour driver with loft held at the preset 12.7 degrees (`atk-loft`, model-derived): highest carry 285 yd (`fx-peak-carry`) near +1 (`fx-peak-atk`), 281 yd at +5 (`fx-carry-p5`), 266 yd at +10 (`fx-carry-p10`); the spin keeps falling as the attack angle rises. Chapter 3. Model. Post 1, X tweet 2.
- Driver ideal at the PGA preset's 115 mph: attack +5 (`id-atk`), loft midway between the chart's carry and total optimizers, with the chart's own strike in place of the Tour spin trim (spin trim 1.0). PGA driver at the ideal 287 yd carry and 328 total (`id-pga-carry`, `id-pga-total`) against 282 and 313 for the average delivery (`av-pga-carry`, `av-pga-total`). With the Tour trim kept, PGA ideal carry is 283 yd (`id-pga-carry-tt`), 1 yd over the average's 282. Chapter 3 and Method and limits, "Driver ideal". Model; ADR 0004 addendum 2. Post 1, X tweets 3 and 4.
- Irons and loft from attack angle: 1.4 degrees of loft per degree of attack (`ir-slope`), floor 1.0 from arc geometry (TrackMan's dynamic loft rule, Anchor 11; Suzuki 2021, Anchor 10), the extra 0.4 from one Foresight 7-iron chart (Anchor 9, read by eye from the chart image, method unknown). Tour 7-iron from attack -3.9 (`ir-atk-dn`) to +3 with the loft following: carry 172 to 157 yd (`ir-carry-dn`, `ir-carry-up`, loss 15), total 179 to 161 (`ir-total-dn`, `ir-total-up`, loss 18). Foresight chart at 90 mph loses 1.7 yd of carry per degree from -6 to +2 (`ir-chart-slope`, published); the model scaled to 90 mph loses 1.8 (`ir-model-slope`). A slope of 1.0 would cut the PGA 7-iron's loss to about 0.6 yd per degree (ADR 0004 addendum 4, Consequences, and the article's Chapter 3). Modeled. Post 1, X tweets 5 and 6, X single tweet.
- Face-to-path and loft: effective loft is input loft plus kappa times face-to-path, kappa the cotangent of the lie angle, 0.61 for the driver (`kappa-drv`) and 0.51 for the 7-iron (`kappa-7i`), from rolling the head about the shaft with no shaft lean, the top of the geometric range. Lie angles are the manufacturers' standard lies at address (Titleist 2025, PING G430 cross-check; Anchor 8). Modeled; no source measured the coefficient. ADR 0004 addendum 3; `004_Physics_Research.md` topic 1. Post 2, X follow-up tweet 3.
- Tour driver, path +4, face 0 (draw): carry 267, total 322 yd (`cp-drv-draw-carry`, `cp-drv-draw-total`). Mirror fade, path -4, face 0: carry 273, total 293 yd (`cp-drv-fade-carry`, `cp-drv-fade-total`). Chapter 2. Model. Post 2, X follow-up tweet 2.
- Tour 7-iron draw carry 176, total 185 (`cp-7i-draw-*`); fade 164 and 170 (`cp-7i-fade-*`); pull hook (path -2, face -6) 174 and 182 (`cp-7i-hook-*`); push slice (path +2, face +6) 163 and 169 (`cp-7i-slice-*`). Chapter 2. Model. X follow-up tweet 5.
- TrackMan's own draw-versus-fade example (Stickney, 2016; `004_Physics_Research.md` S3): draw 10.5 degrees of dynamic loft and 2,643 rpm, fade 15.0 degrees and 3,768 rpm, gap 4.5 degrees and 1,125 rpm, the draw about 20 yd farther in run-out. Published, one R15 driver at an unstated speed. Model check with the same 4.5 degrees of loft gap: fade spins 1,065 rpm more than the draw (`df-spin-gap`), the draw runs out 18 yd farther (`df-run-gap`). A check, not a fit. Post 2 and X follow-up tweet 4.
- A pure pull and a pure push (face-to-path 0) stay equal in the model; no primary source separates them; a TrackMan Master says a controlled draw and fade go the same distance (`004_Physics_Research.md` S16). Post 2, X follow-up tweet 5.
- Amateur driver, 94 mph, attack -1.8, dynamic loft 15.1 (TrackMan Combine average golfer, Anchor 3 Source 1), path -4, face 0: a slice, curve 21 yd (`cx-curve`), finishes 19 yd right (`cx-finish`). Path -2: curve 11 yd (`cx-curve2`). Chapter 6; deep link `/ball-flight/tool.html?c=driver&p=amateur&s=94&a=-1.8&l=15.1&pa=-4&f=0`. Model. Post 3, X tweet 7.
- Face share of start direction, Tour driver 83 percent (`share-drv`), Tour 6-iron 73 percent (`share-6i`). Chapter 1. Model. Post 3, X follow-up tweet 1.
- Circulating shares: 85 and 75 (PGA Academy Australia, 2014, no source named); 87 and 81 (Golf Simulator Forum, 2021, cites TrackMan Academy with no link). Source Log Anchor 5a Sources 3 and 4. Neither traced to a TrackMan text; the model's shares are unverified. Post 3.
- Curve at 2 degrees of face-to-path: Tour driver 18.1 yd (`curve2-drv`), Tour 6-iron 8.9 yd (`curve2-6i`). Ratio 2.0 (`ratio-drv-6i`). Chapter 2. Model. Post 3, X follow-up tweet 1.
- TrackMan's published driver-to-6-iron curve ratio, 2.3 (`tm-ratio`; PGA 2.29, LPGA 2.31, from the eight worked examples). Source Log Anchor 5b Source 1. Post 3, X follow-up tweet 1, X single tweets.
- LPGA Tour average driver: launch 12.6 degrees, attack angle +2.8 (TrackMan 2023 LPGA table, Anchor 2). TrackMan 2010 carry chart 14.2 degrees (`lpga-tm-launch`), PING 2019 chart 14.8 degrees (`lpga-ping-launch`), gap 1.6 to 2.2 degrees (`lpga-gap-lo`, `lpga-gap-hi`), total-distance chart 11.8 degrees (`lpga-total-launch`), LPGA average 0.8 degree over it (`lpga-total-gap`). Chapter 4. Interpolated chart lookups. X LPGA thread.
- Nine windows, Tour 7-iron at 92 mph: straight low 15.3 degrees of dynamic loft (`w-low-loft`), attack angle 7.1 degrees down (`w-low-aoa`), carry 186 yd (`w-low-carry`), peak 26 yd (`w-low-h`); straight high 34.4 degrees (`w-high-loft`), attack angle 0.5 degree up (`w-high-aoa`), carry 149 yd (`w-high-carry`), peak 46 yd (`w-high-h`). Draw face 1.9 to 2.4 degrees right (`w-face-lo`, `w-face-hi`), path 4.3 to 5.0 degrees right (`w-path-lo`, `w-path-hi`); each fade mirrors it. Chapter 5. Model recipes. Post 4.
- TaylorMade video, 2021, "Tiger Woods' Nine Windows", cited for the concept and nothing else. The video was not watched; the description was read. The 3 by 3 grid is the standard reading of the drill. Source Log Anchor 6 Source 1. Post 4.
- No launch monitor numbers found for any window: Source Log Anchor 6 verdict, as far as the search reached. Post 4 says "I found no", never "there are none".
- Interface facts (Explore, 9 Windows, Compare and Present modes; Pin this shot; Copy link; Tour average; the Loft follows attack angle switch, on by default and working for every club; the driver opens on the ideal delivery): `site/ball-flight/tool.html`, `sliders.js`, `state.js`, `present.js` (TV or projector layout), article Chapter 6 (the link holds the whole setup). Posts 1 to 4, the Justin text.

## Numbers that changed since the previous version of this file

Previous version value (ledger commit 3ca0f79), then the current ledger value (commit 5d65911).

- Curve at 2 degrees of face-to-path, Tour driver: 20.1 yd, now 18.1. Tour 6-iron: 9.5 yd, now 8.9.
- Driver to 6-iron curve ratio in the model: 2.1, now 2.0. TrackMan's 2.3 is unchanged, so "the model runs low" still holds.
- Amateur slice: curve 24 yd, now 21. Finish 21 yd right, now 19. Curve at path -2: 12 yd, now 11. The delivery (94 mph, -1.8 attack, 15.1 loft) and the deep link are unchanged; the closed face-to-path now adds loft, so the example's spin reads 4,006 rpm against the published average's 3,275.
- Draw windows: smallest face angle 1.8 degrees, now 1.9. Largest path 5.2 degrees, now 5.0. The straight-window recipes (low 15.3, 7.1, 186, 26; high 34.4, 0.5, 149, 46) are unchanged.
- Unchanged: 83 and 73 percent, 3.3 and 0.7 degrees, the 85/75 and 87/81 gaps, the published 2.3 ratio, the LPGA launch figures, and every driver hit-up number (266, 295, 285, 281, 266, 287, 328, 282, 313, 283, 31).
- Removed from Post 3: the earlier "start direction moves 3.3 and 0.7 degrees" sentence, to make room for the slice example after the two rules.
- New in this version: the lie-angle coupling (0.61 and 0.51; draw 267/322, fade 273/293; 7-iron draw 176/185, fade 164/170; pull hook 174/182, push slice 163/169; check 1,065 against 1,125 rpm and 18 against about 20 yd) and the iron flip (1.4 per degree; 172 to 157 yd carry, 179 to 161 total; 1.8 against 1.7 yd per degree).

## Numbers left out

- **Driver to wedge ratio, 7.0** (`ratio-drv-pw`). The wedge line is extrapolated; no published example covers a wedge. Post 3 uses the driver and 6-iron pair, which TrackMan's examples cover.
- **The 0.87 path formula and the 28-yard hook from a 4-degree steeper attack** (`per-deg`, `couple-curve`). The formula comes from a 2011 forum post, not TrackMan, and the result needs the swing-direction-held assumption spelled out. The article has the paragraph for it.
- **Average amateur spin about 500 rpm over TrackMan's Optimizer default** (`am-def-gap`), and the slice example's 4,006 rpm against 3,275 (`cx-spin`). Each compares a model output or a measured average with a TrackMan default, and a caption cannot carry that distinction.
- **The model's carry gain against the chart's**: flown from the chart's own launch conditions, the model gains 22 of the chart's 29 yd of carry and 25 of the 31 yd of total (`md-carry-gain`, `md-total-gain`). Post 1 says "in my model" and points to the article.
- **The LPGA and amateur ideal gains** (LPGA 227 and 263 to 230 and 267, amateur 213 and 238 to 224 and 260). Post 1 prints the PGA driver at 115 mph and nothing else.
- **Slower speeds** (`slow-pga-lo`, `slow-pga-hi`, `slow-lpga-lo`, `slow-lpga-hi`): the model gives the driver ideal less total than the average delivery at 90 to 100 mph for the PGA preset and 75 to 90 mph for the LPGA, and carry still gains. Post 1 scopes its numbers to 115 mph, and the article's Method and limits carries the caveat.
- **The average amateur 7-iron carries most at an attack angle of -6.5 degrees** (`ir-am-peak`), and the chart's flat carry at 60 to 80 mph. Both need the speed-dependence explained.
- **The lab's driver launch band, 5.3 to 5.8 degrees wide** (`band-w-lo`, `band-w-hi`). A design consequence of the three-source band, useful to a coach who reads the article.
- **Model misses in Method and limits** (17 of 23 rows passing launch, spin and ball speed; the seven chart totals off by more than 5 percent). They belong in Method and limits, and Post 1 points to the article for them. Quoting them without the gate definitions would misstate them.
- **Tiger's numbers.** None exist in the sources, and none appear.
