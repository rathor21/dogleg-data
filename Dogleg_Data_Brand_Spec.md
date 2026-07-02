# Dogleg Data — Brand Specification

Date: 2026-07-01 · Status: awaiting Sunny's sign-off · Author: Claude, direction by Sunny

## 1. Positioning

Dogleg Data runs golf's conventional wisdom through real data, at every handicap. The tour has ShotLink and Data Golf. Betting has RickRunGood. The 8-to-30 handicap playing a $40 muni has hand-me-down advice built from tour numbers. Dogleg Data serves that golfer with peer-reviewed, source-cited analysis that says plainly what is measured and what is modeled.

Vision: become the analysis golf podcasters and YouTubers cite when the question is "what do the numbers say for a normal golfer," and from there earn collaborations with a major golf brand or content creator.

Audience, in order: golf X/Twitter, the LinkedIn data community, golf podcasters and YouTubers (Golfwell, Dr. Luke Benoit), golf brands.

## 2. Name and tagline

**Dogleg Data.** A dogleg is the hole that punishes the straight line — the whole brand is "the obvious play isn't always the right one, here's the math." Alliteration aids podcast recall. Adjacent "Dogleg" marks exist (Swiss apparel, a brewery, a putter maker); none are analytics content, and the compound "Dogleg Data" is unclaimed and searchable.

**Tagline: "Play the percentages."**

## 3. Aesthetic direction

Malbon-inspired: vintage country club meets streetwear. Retro-leisure over lab-report. Badge and mascot energy, flat screen-print surfaces, cream paper, leather-goods tones. The data credibility lives in the details (mono numbers, source lines, modeled-data flags), while the shell reads like a brand you'd wear.

## 4. Logo system

- **The mark:** a dogleg-right hole drawn as one thick rounded stroke from tee to bend to a baked-clay dot at the green. Reads as both a hole diagram and a chart line ending in a data point.
- **Primary badge:** circular patch, ink field, cream mark, "DOGLEG DATA" curved along the top ring, "PLAY THE PERCENTAGES" along the bottom, double ring border. No EST dates.
- **Avatar:** mark alone on ink circle. Must read at 44px.
- **Mascot:** the dogleg dachshund — body bent 90° like the hole shape, bucket hat, retro-cartoon linework. Merch, stickers, watermarks, empty states.
- **Chart badge:** compact ink strip with mark, wordmark, and mono source line, stamped on every published chart. Charts travel farther than profiles.

Badge, mascot, and banner art generated in Gemini per `Gemini_Image_Prompts.md`; geometry, lockups, exports, and chart badge assembled here from those images. Wordmark type is always set in real fonts, never image-generated.

## 5. Color

Charts sit on cream paper, not white — instantly recognizable in a feed of white-background stats charts. No green, no yellow, anywhere.

| Role | Name | Hex | Use |
|---|---|---|---|
| Paper | Range ball cream | #F4EDE0 | Chart/dashboard backgrounds, badge linework |
| Primary | Ink | #1C1B18 | Wordmark, tour data, primary text |
| Accent | Baked clay | #C05A36 | 20-hcp data, highlights, the mark's dot |
| Cool | Faded denim | #5B7FA6 | 10-hcp data, secondary accents |
| Deep | Oxblood | #7D362E | 30-hcp data (dashed + labeled modeled) |
| Muted | Saddle | #8A7F6E | Secondary text, axis labels, source lines |
| Line | Warm grid | #E2D8C6 | Gridlines and hairlines on cream |

Fixed tier mapping everywhere: tour = ink, 10 = denim, 20 = clay, 30 = oxblood. Blue/orange axis keeps tiers separable for colorblind readers; the 30 tier is additionally dashed and starred as modeled, so color is never the only signal.

## 6. Typography

- **Headlines / wordmark:** Fraunces (600, 900) — soft retro serif, 70s clubhouse warmth
- **Numbers, axes, source lines:** IBM Plex Mono (mono digits align in tables)
- **Body:** Inter

All free via Google Fonts. Charts: TTFs registered with matplotlib; DejaVu Sans is the documented fallback if font install fails (fonts are presentation, not data).

## 7. Voice

1. Show the work. Every claim names its source (Broadie 2011 Table 9, Stagner/Arccos, GOLFTEC, USGA/R&A). Every modeled number is labeled modeled, in every chart, every time it appears.
2. Talk to the 15-handicap, quote the tour data. Second person over abstraction.
3. Admit what broke. Peer-review findings get published, not buried. This is the signature move.
4. Invite the reader in: "bring me your scramble read."
5. Stop-slop discipline: no em dashes, no filler adverbs, active voice, no "not X, it's Y" reversals, varied sentence rhythm, no hype vocabulary ("game-changer," "unlock").

## 8. Social architecture (hybrid)

- **X:** brand account. Handle preference order: @DoglegData, @DoglegDataGolf, @dogleg_data (verify at signup). Posts in brand voice, first person singular.
- **LinkedIn:** Sunny posts personally; headline includes "Founder, Dogleg Data." Brand travels via the chart badge and a plug line ("Full model at Dogleg Data").
- Bios, banner, and pinned-post copy delivered in the brand kit.

## 9. Asset inventory

Brand kit → `Golf Analytics/brand/`:
1. `Dogleg_Data_Brand_Guide.md` (this spec, expanded with usage rules)
2. `logo/` — mark, primary lockup, avatar, chart badge (SVG + PNG)
3. `banner_x.png` (1500×500), `banner_linkedin.png` (1584×396)
4. `bios_and_handles.md`
5. `content_growth_plan.md`

Post refresh → `Fairway_vs_Rough_Post/`:
6. `source/style.py` rebranded (only file edited in source/); charts 1–5, CSV, dashboard data regenerated
7. Dashboard HTML re-skinned (typography, palette, header with mark; data untouched)
8. `Post_Copy_LinkedIn.md` + `Post_Copy_X.md` (platform-tuned, all sourced claims intact)
9. Updated peer review addendum covering the rebrand pass

## 10. Verification standard (unchanged from project rules)

Headline numbers re-derived independently after regeneration (150yd: 75.0 / 23.0 / 17.0 / 11.8→"12"; peak 80 at 140yd). Chart-to-chart consistency re-checked. Peer-review addendum with must-fix/should-fix/minor and sign-off before anything is called publishable.

## 11. Out of scope (this round)

Website, merch, paid design tools, trademark filing (worth a search before real money is spent on the name), video/motion assets.
