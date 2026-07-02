# Dogleg Data — Gemini Image Generation Brief

Paste the context block into every prompt, then use the specific prompts below it. Generate 4+ variations per asset and pick; ask Gemini for "same design, minor variations" once you find a keeper.

---

## Context block (include with every prompt)

> Brand: "Dogleg Data," a golf analytics brand with a vintage country-club-meets-streetwear aesthetic, inspired by Malbon Golf's retro-leisure style. Flat vector illustration, screen-print texture acceptable, no gradients, no 3D, no photorealism, no drop shadows. Strict palette: cream #F4EDE0, soft ink black #1C1B18, baked clay orange #C05A36, faded denim blue #5B7FA6, oxblood #7D362E. Never use green or yellow. Clean edges suitable for conversion to a logo. White or transparent background.

---

## Prompt A — Primary badge logo

> A circular embroidered-patch-style golf logo badge. Center element: a single thick rounded line drawing the shape of a dogleg-right golf hole, starting at the bottom as a tee, bending 90 degrees at a smooth rounded corner, and ending at a small solid circle in baked clay orange (the green/data point). The line is cream on an ink-black badge. Around the ring, the words "DOGLEG DATA" curved along the top and "PLAY THE PERCENTAGES" curved along the bottom, in a clean monospaced or engraved style, cream color, with two small dot separators at 3 and 9 o'clock. Double thin ring border in cream. Vintage 1970s country club patch energy, flat vector, no gradients.

Variations to try: swap ring text bottom for "GOLF ANALYTICS"; try badge in cream with ink linework (inverted); try a subtle halftone texture.

## Prompt B — Mascot: the dogleg dachshund

> Character sheet for a retro cartoon mascot: a long dachshund whose elongated body bends in a smooth 90-degree curve, like a dogleg golf hole seen from above. The dog wears a small vintage golf bucket hat and carries a single golf club in its mouth. Style: 1960s-70s American cartoon advertising mascot, thick even outlines in soft black ink, flat fills only from this palette: baked clay orange body, cream accents, faded denim blue hat, oxblood collar. Friendly, confident, slightly smug expression. Three poses on one sheet: (1) body bent in the signature dogleg curve, (2) lining up a putt, (3) sitting proudly next to a golf flag. Flat vector, white background, no gradients, no 3D.

The bent-body pose is the one that matters — it should read as the brand mark's silhouette. If Gemini fights the 90-degree bend, ask for "top-down view of the dog walking a dogleg-shaped path."

## Prompt C — Simplified avatar mark

> A minimal flat logo mark on a solid ink-black circle: one thick cream rounded stroke forming a dogleg-right golf hole shape (vertical line from bottom, smooth 90-degree bend to the right, short horizontal line), ending in one solid baked clay orange dot. Nothing else. Perfectly balanced composition, generous margins, legible at 44 pixels. Flat vector.

This is the X/LinkedIn avatar. It must stay dead simple — reject any variation Gemini decorates.

## Prompt D — Social banners

X banner (1500×500):
> A wide horizontal banner, cream #F4EDE0 background with a subtle scorecard grid texture. Left third: the Dogleg Data badge logo. Center: the phrase "Play the percentages." in a bold retro serif, ink black. Right third: a minimal top-down illustration of a dogleg golf hole in faded denim blue and baked clay, drawn like a vintage yardage-book diagram with small monospaced yardage numbers. Flat vector, retro country club aesthetic, no gradients, no green, no yellow.

LinkedIn banner (1584×396): same prompt, but replace the badge with the dachshund mascot at small scale on the left, and add thin ink rule lines top and bottom like a scorecard.

## Prompt E — Sticker/watermark set (optional, for later)

> Sticker sheet: the dogleg dachshund mascot in five small poses (swinging a club, reading a yardage book, sitting in a bucket hat, celebrating with a flag, asleep on a golf bag), plus the circular badge logo, plus the words "worth 17 yards" in a retro serif inside a small banner ribbon. Flat vector, thick outlines, palette: cream, ink, baked clay, faded denim, oxblood. White background.

---

## What to avoid (add as needed)

No green, no yellow, no gradients, no 3D render, no photorealism, no neon, no golf ball with wings, no shield shapes, no crossed golf clubs, no script/cursive fonts, no "EST." dates.

## When you bring images back

Save whatever you pick into `Golf Analytics/brand/from_gemini/`. I will: extract/trace the geometry where needed, cut PNG exports at avatar (400×400), badge (1000×1000), and banner sizes, build the chart-corner badge from the approved mark, and match the charts' fonts and colors to the exact hexes above. Fonts stay my job (Fraunces for headlines, IBM Plex Mono for numbers, Inter for body) — don't let Gemini invent type, its logo text usually needs replacing anyway. If badge text comes out garbled, pick the version with the best shapes and I'll rebuild the text layer.
