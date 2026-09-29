# Release 004 hero art: candidate paintings

Candidates for the driving-range view behind the ball-flight tracer. Full prompt text for each image lives in `prompts/`. Images live in `candidates/`. Rebuild the contact sheet with:

```
analysis/002-tee-shot-distance/.venv/bin/python contact_sheet.py "candidates/r1_[0-9].png" candidates/r1_contact.png
```

Generator: Nano Banana through the Gemini CLI (`/generate`, one image per call). Output size is 1376x768 (about 16:9).

## Round 1

`candidates/r0_test.png` is the earlier test image (golden hour, inside a hitting bay, painted flag numbers with "100" twice). It stays for reference and is not ranked.

### Prompts

Every prompt shares one core: a long straight range running to the horizon, the hitting position at bottom center, the target line down the middle, target greens with plain flagsticks (red or white flags, no numbers) at about 50, 100, 150, 200 and 250 yards, tree lines on both sides, sky in the top third, photorealistic, and explicit bans on people, text, numbers, letters, signs, logos, watermarks and airborne balls. The per-image differences:

| Image | Light | Camera | Framing |
|---|---|---|---|
| r1_1 | Midday sun, blue sky, cumulus | Head height behind a mat | Open |
| r1_2 | Midday sun, clear sky | Elevated, about 4 m | Open |
| r1_3 | Golden hour, sun behind camera | Head height behind a mat | Open |
| r1_4 | Golden hour, sun behind camera | Elevated, about 4 m | Open |
| r1_5 | Floodlit dusk, blue twilight | Head height behind a mat | Open |
| r1_6 | Floodlit night, navy sky | Elevated, about 4 m | Open |
| r1_7 | Late-morning sun, cirrus | Elevated, about 3 m | Subtle bay frame (low dividers at the bottom corners) |
| r1_8 | Sunset dusk, floodlights just on | Head height behind a mat | Bay frame (dividers at the bottom corners) |

### Ranking

Criteria in order: looks like a real and attractive range, straight target line with distinct greens at increasing distance, sky room for a tracer apex, and prompt compliance.

1. **r1_5** (floodlit dusk, head height). The most convincing TopTracer look. Floodlight poles give depth cues down both sides, the sky is deep blue with a faint horizon glow (a bright tracer will read well against it), and the sky fills the top 45%. One large green sits near the center line with a red flag, smaller greens and flags step back toward the horizon. The mat at the bottom has painted white alignment lines, which are shapes and not text. Weakness: the far greens sit off the center line, and about four greens are readable.
2. **r1_4** (golden hour, elevated). Clean and natural. The elevated view separates four greens at increasing distance, tall trees converge on a symmetric vanishing point, and mowing stripes give strong perspective lines for a camera fit. Sky takes the top third with warm cloud bands. Weakness: a wooden club rack and a ball basket sit beside the mat (objects, not people, easy to paint out or crop), and the greens are low contrast against the stripes.
3. **r1_2** (midday, elevated). The most symmetric of the set and the best geometry for a camera fit: greens stack on the center line, white flags mark the edges, and the stripes converge to a sharp vanishing point. Sky covers the top 45%. Weakness: the greens and flags are small, the look is closer to a drone shot than a hitting-bay view, and the front mat edge is the sole foreground detail at the bottom.
4. **r1_7** (late morning, subtle bay frame). Looks like a real photograph. Orange and white flags at the edges and red flags on the center line give useful distance cues, and the sky is generous. The two low dividers at the bottom corners frame the view without touching the sky or fairway. Weakness: the phone-photo tone is flatter than the others, and the dividers eat the bottom corners.
5. **r1_6** (night, elevated). A dramatic floodlit range, and a glowing tracer would show well on the dark sky. Three greens read at increasing distance. Weakness: greens sit right of center, the sky is empty (no horizon glow to anchor it), and the trees are near black, which limits cues for an art-camera fit.
6. **r1_3** (golden hour, head height). The lighting is the most photographic of the set, with wildflower rough and a warm sky. Weakness: the greens are off-center, the mat fills the bottom fifth of the frame with grime and a tee peg, and the horizon sits high, leaving less room to see the fairway shape.
7. **r1_1** (midday, head height). A pleasant real-looking range with two dark disc greens and several red flags. Weakness: the greens look like flat dark ovals, the mat looks worn, two greens read, and the distances are hard to separate at this low camera height.
8. **r1_8** (sunset dusk, bay frame). The sunset is the prettiest sky of the set. The metal-railed dividers cover both bottom corners and rise into the frame, so tracers would cross them. A white painted line runs down the fairway and mat (a useful target line, but a hard artifact), and the greens sit far off the center line. Weakness: the dark grass loses stripe detail, so the perspective lines a camera fit needs are faint.

Top three picks: r1_5, r1_4, r1_2. Five candidates passed, which clears the three-good threshold, so no round 2 was run.

### Compliance notes

- No people in any image.
- No legible text, numbers, logos or watermarks in any image. Flags are blank in all eight. r1_5 has white painted lines on the mat and r1_8 has a white painted center line, both are shapes.
- r1_4 includes a club rack and a ball basket. r1_5 and r1_8 show floodlight poles, which a tracer could pass behind. No airborne balls appear.
- Greens follow "increasing distance" in every image, but none of them sit at exact 50-yard steps, and several sit off the center line. The camera fit should use the flags as ground control points and measure their pixel positions, and should not trust the prompt yardages.

### Phone crops

A 9:16 crop from a 1376x768 image is 432x768 pixels. Cut around the center line (x from about 472 to 904) and the crop keeps the sky, the vanishing point and the near green in r1_2, r1_4 and r1_5. The crop drops the edge flags and most of the tree lines. r1_5 and r1_6 lose the floodlight poles that give the widescreen framing its depth. Scale the tracer to the cropped view instead of reusing the wide fit, and consider a second, phone-specific generation with a portrait aspect if the crop looks thin. At 432x768 the crop is below phone retina resolution, so plan an upscale pass or a native portrait render before shipping.
