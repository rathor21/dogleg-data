# 003 hero art: stencil/texture-composite architecture (issue #11)

Status: **registration PASSES (15/15), round four.** `hero.png` and `hero_mobile_crop.png` are accepted assets. Round four replaced every generated ground texture with a direct, procedural render (`render_ground.py`) after round three's composited ground failed on sight despite passing registration -- see "Round four" below for what changed and why, and "Round three" and "Round two" above it for the two rounds of texture-through-masks compositing that preceded it. This whole stencil approach supersedes the first architecture (asking nano-banana to respect pixel geometry directly via image-to-image), which failed registration on all 7 candidates -- see "First architecture" below for that record, kept for reference.

## The pivot

Round one asked nano-banana to *generate* geometry-correct art directly (image-to-image against a flat-fill sketch). It couldn't: loose prompts drew a beautiful but geometrically wrong hole, literal "preserve this shape" prompts produced a double-exposure of the sketch pasted over a separately-imagined background. Full writeup of that failure is preserved below.

Round two stopped asking the generator to respect geometry at all. Geometry is now a **stencil**: masks.py rasterizes the model's own regions as alpha masks, nano-banana generates texture and environment with no composition constraints, and Pillow composites textures through the masks at the exact camera coordinates. nano-banana never has to get geometry right; Python enforces it by construction, which is why registration now passes trivially rather than approximately.

## Pipeline

1. **`sketch.py`** (unchanged from round one) -- the model's geometry (`data.py`/`model.py`) projected into the elevated three-quarter camera. Still used as the registration reference and by every downstream script.
2. **`masks.py`** -- reuses `sketch.build_scene()`/`make_projector()` (same functions, same camera, zero new geometry) to rasterize anti-aliased alpha masks into `masks/`: `green`, `creek`, `bunker_front`, `bunker_back_0`, `bunker_back_1`, `bunkers` (union), `fairway` (mown corridor + tee box), `bank` (shaved-bank halo strips, bunker footprint subtracted), `playfield` (union of all of the above), `environment` (`1 - playfield`, where the plate shows through unclipped).
3. **nano-banana generations** (`gen-image.py`, `gemini-2.5-flash-image`), five calls, none of them geometry-constrained:
   - `environment_plate.png` -- the backdrop: trees, azaleas, sky, open grass. The prompt explicitly says no water/bunkers/green/bridge, since environment is supposed to be everywhere *outside* the hole. It mostly complied; stray bunkers it left in are clone-stamped out in `composite.py` (`patch_stray_bunkers`, tuned to the current plate image). Regenerated once since (round three, below) to fix a horizon mismatch with the sketch's camera.
   - `tiles/tile_grass.png`, `tile_water.png`, `tile_sand.png`, `tile_rough.png` -- four close-up seamless-ish textures, one per the ticket's named region type. No composition, no camera, just texture.
4. **`composite.py`** -- the compositor (bullets below describe round two's version; round three, further down, adds a horizon-aligning crop, per-mask feather radii, and several relief cues on top of this without changing the overall shape):
   - Loads the plate, patches stray bunkers, resizes to the 1600x900 mask canvas.
   - For each region, builds a **perspective-correct** texture layer: every output pixel is mapped back to model `(x_yd, y_yd)` through the exact camera (`y_yd_for_screen_y` inverts `sketch.screen_y_for`; `sketch.half_width_px_for` gives the lateral scale), then sampled from the tile modulo a repeat size in *yards*. This is the fix for the first pass's biggest tell: a texture tiled at a fixed pixel size looks like a flat sticker glued onto a receding silhouette, because the mask recedes in perspective but a flat tile doesn't. Mapping in yards makes mow-stripe frequency (and sand ripple frequency, etc.) increase toward the green exactly like the geometry already does.
   - Color-matches each tile toward the plate's own lighting (partial mean/contrast transfer from the plate's `environment`-masked region -- see `REGION_MEAN_STRENGTH`: grass regions transfer most of the way for coherence, water and sand transfer much less, so they keep their own hue instead of desaturating toward the green backdrop).
   - Composites each textured region onto the plate through its feathered mask, in sketch.py's own z-order: fairway/bank -> creek -> bunkers -> green.
   - Legibility touches: a crisp waterline along the creek's far (green-side) bank -- exactly `model._front_edge_yd`, sampled the same way `sketch.py` samples it, since a later ticket's flight-path arcs will terminate near this line; a soft shadow under the green's back edge; a light vignette.
   - Pin flags drawn at the exact same `project(x, y)` coordinates `sketch.py` uses, so pin geometry is pixel-exact by construction, not by generation luck.
   - Saves `hero.png` (1600x900) and `hero_mobile_crop.png` (a 9:16 center crop, `crop_w = round(900 * 9/16) = 506`, centered on the canvas -- the camera's own horizontal center by construction).
5. **`registration_qa.py`** (extended, not replaced) -- now accepts an explicit target (`python3 registration_qa.py hero.png`) in addition to its original `hero_candidates/*.png` sweep. Same 15-landmark color-threshold measurement as round one (3 pins, 9 creek-bank samples, 3 bunker centroids), 5%-of-image-width tolerance.

## Registration result

```
python3 registration_qa.py hero.png
-> 15/15 landmarks within 5.0% of image width -> overall PASS
```

Full numbers: `registration_report_hero.json`. Overlay for visual inspection: `hero_overlay.png` (the sketch blended at 40% opacity over `hero.png` -- every hazard boundary lines up because both are computed from the same `project()` call).

Three of the four per-landmark-type search windows needed tightening from round one's defaults once real geometry stopped being the limiting factor: pins sit as close as ~65px apart on this canvas and creek-bank samples ~50px apart, closer than the original 12%-of-width (~190px) window used to hunt for badly-drifted AI-generated geometry. A window that wide let a sample's search snap onto a neighboring landmark instead of its own. Tightened windows (`pin_win = 40`, `creek_win = 24`, `bunker_win = 55`) are specific to `registration_qa.py`'s own detection logic, not a change to any drawn geometry.

## Per-layer inventory

| Layer | Source | File(s) |
|---|---|---|
| Green mask | `model._front_edge_yd`/`_back_edge_yd`, `data.HOLE` width | `masks/green.png` |
| Creek mask | far bank = `model._front_edge_yd` exactly; near bank = far bank minus the art-only `CREEK_WIDTH_YD` from `sketch.py` | `masks/creek.png` |
| Bunker masks | `data.HOLE` x-ranges/depths, anchored to the front/back edge functions | `masks/bunker_front.png`, `bunker_back_0.png`, `bunker_back_1.png`, union `bunkers.png` |
| Fairway/bank masks | fairway corridor + tee box (`fairway.png`); shaved-bank halo strips minus bunker footprint (`bank.png`) | `masks/fairway.png`, `masks/bank.png` |
| Environment mask | `1 - playfield` | `masks/environment.png` |
| Environment plate | nano-banana, no hole features requested (three stray bunkers patched out anyway), horizon-aligned crop applied in `composite.py` -- see "Round three" | `environment_plate.png` (round three; `environment_plate_v1.png` was round two's, deleted in round four, see "Round four deliverables") |
| Grass texture (rounds two/three only -- round four renders the whole ground in code, see "Round four" below) | nano-banana, applied to both `green` (brighter/cooler tint, finer 2.5yd repeat) and `fairway` (duller tint, 4.5yd repeat) -- the ticket names one "mown grass" tile for both, differentiated here by Pillow tint/scale rather than a second generation | `tiles/tile_grass.png` |
| Water texture (rounds two/three only) | nano-banana, 5.5yd repeat, minimal color transfer to keep its blue-teal hue | `tiles/tile_water.png` |
| Sand texture (rounds two/three only) | nano-banana, 2yd repeat, minimal color transfer, warm/bright tint pushed further in Pillow | `tiles/tile_sand.png` |
| Rough/bank texture (rounds two/three only) | nano-banana, 3yd repeat, applied to the `bank` mask | `tiles/tile_rough.png` |

## Round three (2026-09-07): horizon-matched plate, feathered composite (issue #11)

Registration passing 15/15 didn't mean the picture worked. An orchestrator's visual review of round two's `hero.png` caught three problems the landmark-color-threshold check can't see, because it only checks that specific points land near specific colors, never whether the picture reads as one place:

1. **The green and both back bunkers rose above the plate's own tree line, into open sky.** A ground plane can never sit above the horizon, and this one did, by a lot.
2. **The fairway corridor was a hard-edged, uniformly-colored triangle** that read as a sticker pasted onto a backdrop that was already grass.
3. **The creek read as a flat blue stripe, the green as a flat parallelogram, bunkers as flat patches** -- no bank, no rim, no sense any of them were physical ground rather than a color fill.

### 1. The horizon mismatch, with numbers

`sketch.py`'s camera has its own horizon built in: `screen_y_for` is a 3-segment piecewise-linear depth budget that walks screen y from `GROUND_NEAR_PX` (862, the tee box's back edge) down to `HORIZON_PX` (150) as model distance runs out to `Y_MAX_YD` (200yd). `HORIZON_PX = 150` on a 900px-tall canvas is **16.7% down from the top** -- everything the stencil draws (green, bunkers, creek, fairway) is geometrically guaranteed to stay below that line, because `masks.py` uses this exact same projector.

Round two's `environment_plate.png` didn't know about that number. Its tree line sat with its base around row 430 of a 768px-tall image -- **56% down the frame**, not 17%. Below `HORIZON_PX`, the stencil was painting real geometry (the green complex reaches up to about screen y=240, well inside what should be "grass"); the plate, at that same screen height, was still rendering open sky. Hence a bright green shape floating above the tree line.

### 2. Regenerating the plate

New prompt (full text, four candidates generated, `gemini-2.5-flash-image`):

> A painterly-but-clean editorial illustration of open golf course parkland, elevated camera looking down over rolling mown grass from a high vantage point, in the style of Augusta National's back nine. The sky and a distant tree line of tall mature pines are confined ONLY to the top 15 percent of the frame -- a thin band of soft overcast sky and a low, distant tree line right at the very top edge. Everything below that -- fully 85 percent of the frame, from just below the top edge all the way to the bottom -- is rolling, gently undulating mown grass in muted greens, seen from above at a steep downward angle, filling the entire foreground and midground. Azalea bushes in pink and white are allowed in a thin band along the base of the tree line at the very top, not lower. Do NOT include: any water, creek, stream, or pond; any sand bunkers; any putting green; any flags or pins; any bridge; any path or cart trail; any people or equipment; any text, logos, or watermarks. Just a huge expanse of open grass beneath a thin strip of trees and sky at the top of frame. Confident brushwork, clean readable shapes, muted Masters color palette (soft greens, warm cream light), soft natural light. Aspect ratio 16:9.

All four candidates still drew 2-3 stray sand bunkers despite the explicit "do NOT include" line (same non-compliance round two hit once, for the same reason: an "Augusta National back nine" prompt pulls bunkers back in even when told not to). Candidate 4 won on tree-line placement: measuring where each candidate's grass clearly resumes below its tree/azalea band (color-sampled, not eyeballed) gave tree-line-base fractions of native height of 0.29, 0.11 (a false low -- its azalea band alone reads grass-green in that column, the actual base is much lower), 0.26, and **0.20** for candidates 1-4; visual inspection with a horizon guide line confirmed candidate 4's was the only one close to the 16.7% target with a clean-looking ground plane. Its native tree-line base measured row 190 of 768 (24.7%) -- closer than round two's 56% by a wide margin, but still not exact.

Rather than re-roll for a pixel-perfect match (a fifth call with no guarantee of landing closer), `composite.py`'s `load_aligned_plate` crops a fixed fraction of pure sky off the plate's top before resizing to the canvas (`PLATE_CROP_TOP_FRAC = 0.099`, i.e. 76 of the native 768px). Cropping sky-only rows shrinks the denominator the tree-line row is measured against without moving the tree line itself, which pushes its *effective* fraction down: `(190 - 76) / (768 - 76) = 0.165`, just under the 0.167 target -- "at or slightly above the horizon," per the brief. The crop is then centered horizontally to hold the plate's native 16:9 aspect (dropping ~85px off each side) so the final resize to the 1600x900 canvas is a uniform scale, not a stretch. `environment_plate.png` is candidate 4; the round-two plate is kept as `environment_plate_v1.png`. Candidate 4's three stray bunkers are clone-stamped out in `composite.py`'s `patch_stray_bunkers` (native-plate-coordinate boxes, same technique round two used for its one stray bunker, applied before the crop above).

### 3. Compositing changes

- **Fairway**: kept the corridor mask (didn't switch to a pure low-opacity overlay) but feathered its edge from round two's 2.5px radius out to 20px (a Gaussian's visible falloff runs 2-3x its radius, so this is roughly a 60-90px soft transition), raised `REGION_MEAN_STRENGTH["fairway"]` from 0.32 to 0.42 so its color pulls further toward the plate's own grass, and added a new `REGION_CONTRAST_SOFTEN` step (0.72x) that flattens the mow-stripe tile's own contrast before tinting -- round two's own "Honest assessment" (below) had already flagged this contrast gap as the fairway's weak point. `bank`'s edge widened similarly (14px radius, 0.34 mean strength). The tee box, unioned into the same `fairway` mask, gets the same wide feather rather than a separately-crisp edge -- the ticket allowed either, and splitting the mask wasn't worth the added complexity for this pass.
- **Green**: unchanged fine-grained texture, plus new relief cues -- a soft shadow just inside the green's back edge (kept from round two) *and* a matching one along its creek-side front edge (new), plus a thin lighter rim line traced along both edges (a mown-collar highlight).
- **Creek**: the crisp far waterline stays (a later ticket's flight-path arcs terminate on it), but its color changed from round two's pale low-alpha teal (`(35,58,63)` at 170/255 core alpha) to a deeper, higher-alpha blue (`(18,52,96)` at 235/255) -- see the registration regression below for why. Added a softer, darker near-bank shadow line on the fairway-side bank, and a `darken_creek_toward_banks` pass that erodes the creek mask (`ImageFilter.MinFilter`, ~15px) and darkens the textured water in the resulting edge band, so the channel reads as having two banks and some depth rather than one flat tint.
- **Bunkers**: added a thin dark rim shadow just inside each bunker's *far* edge (the side away from the camera -- for the front bunker that's `model._front_edge_yd`, i.e. the green's own front edge; for each back bunker it's the outer boundary away from the green), so each pocket reads as sunk rather than flush with the grass around it.
- **Pins**: unchanged -- still drawn at the exact `project(x, y)` sketch.py uses.

**A registration regression, and the fix.** The front bunker's x-range (-10 to 2yd) sits directly on the same curve as the creek's far bank and the green's front edge for part of its length -- by the model's own design, the front bunker occupies the front slice of the creek's depth budget rather than sitting beside it. The new bunker-rim-shadow and green-front-rim/shadow effects, drawn along that shared curve, painted over the crisp waterline wherever the three curves coincided. Reordering the draw calls (waterline last, so it always paints on top) fixed the visual overlap, but `registration_qa.py`'s `creek_far_bank:3` landmark (`x=-5yd`, deep inside the bunker's span, where no actual creek water is ever visible under any correct rendering) still failed: round two's pale, low-alpha waterline stroke blended against the bunker's warm, high-red sand read as sandy-brown, not blue, to the `is_blueish` predicate (`b > r+10, b > 70`). The deeper, higher-alpha blue above passes `is_blueish` against both the fairway and the bunker's sand tone (checked by hand against both backgrounds), which is why the waterline's color changed as part of this round rather than staying pixel-identical to round two.

### Registration result, round three

```
python3 registration_qa.py hero.png
-> 15/15 landmarks within 5.0% of image width -> overall PASS
```

`hero_overlay.png` and `registration_report_hero.json` regenerated against the new composite.

### What's still weak

Honest read, in order of severity: (1) the fairway corridor, after widening its feather and softening its contrast to stop reading as a sticker, is now subtle to the point of being hard to pick out in a quick glance at the full 1600x900 image -- it only clearly reads at roughly 2x zoom or closer. Round two's problem was too much edge; this may now be very slightly too little. (2) The bunkers' sand texture reads a bit pale/mottled rather than a clean warm gold, most visible on the two thin back-bunker slivers -- a pre-existing `tile_sand.png` characteristic, not something this round changed, but worth another look if bunkers get their own ticket. (3) The creek's added bank-darkening and near-bank shadow help, but the water body itself is still closer to "textured flat tint" than "water with visible depth" -- a fourth relief pass (e.g. a highlight streak or two along the near bank, echoing the far waterline) would go further than this round's darkening alone. None of these three rise to the level of the round-two problems this round set out to fix (all of which -- the horizon float, the sticker edge, and the total absence of relief cues -- are resolved), but none should be called "fixed" either.

### Round two's honest assessment (superseded by round three above, kept for record)

This reads as one illustration, not a collage, on the strength of three specific fixes over the first attempt at this same composite approach: (1) regenerating the environment plate with an explicit no-hazards prompt, since the first plate's own creek and bunkers competed with the stencil's; (2) mapping every texture through the model's actual camera in yards rather than tiling at a fixed pixel size, since a geometrically-correct silhouette filled with a flat-scale texture is the single biggest sticker tell; (3) letting water and sand keep most of their own hue instead of blending toward the backdrop's green-brown mood, which was washing them out gray. The remaining soft spot is the fairway's mow-stripe contrast, which is a bit bolder/more graphic than the plate's own grass rendering right at the mask boundary -- a real but minor seam, visible on close inspection (see `hero_overlay.png` or a full-resolution crop along the fairway edge) rather than at a glance. If this needs another pass, the fix is narrowing that contrast gap (soften `tile_grass.png`'s stripe darkness, or reduce `REGION_MEAN_STRENGTH["fairway"]`'s pull toward the plate less and lean on a stronger blur instead) rather than anything structural in the stencil approach itself.

(Round three, above, is exactly that "another pass" -- it also turned up two problems this assessment didn't anticipate, the horizon mismatch and the total lack of relief cues, which is why round three's own "what's still weak" section exists rather than declaring the picture finished.)

## Round four (2026-09-07): code-rendered ground over generated tree band (issue #11)

### Why: registration passing was not the same as the picture working

Round three passed 15/15 landmarks and still failed on sight. The orchestrator's verdict on round three's `hero.png`: the composited ground read as a blurred green-on-green smear with a faint triangle silhouette, the green was a small dark parallelogram with no presence, the bunkers were pale smudges, the creek a thin dark stripe. Two full rounds of the same fix pattern -- generate a texture tile, tile it through a mask, color-match it toward the plate -- had produced two rounds of the same failure mode at different intensities. The problem was not a parameter to tune; it was the premise that a small, geometrically-correct tile of nano-banana texture, resampled and blurred to hide its seams, would ever read as a painted ground plane rather than a processed photo of one.

### The strategy change

Nano-banana kept exactly one job: the strip above the horizon (sky, pine tree line, azalea beds), where round three had already shown it works -- "horizon now matches" was the one piece of positive feedback out of round three's verdict, and `environment_plate.png` plus `load_aligned_plate`'s horizon-crop math are untouched this round. Everything below the horizon is now rendered directly in code (`render_ground.py`), in the register of a clean editorial yardage-book illustration -- the same flat-but-confident style as the prototype's own accepted composition (`docs/plans/assets/003-proto-desktop.png`): solid base colors, crisp region edges, and a small number of explicit relief marks (rim lines, shadow bands, a waterline, bunker lips, rake lines) drawn with `ImageDraw` calls at exact projected coordinates, not sampled from a generated tile and blurred into place.

Geometry is untouched by this change. `render_ground.py` imports `sketch.build_scene()`/`make_projector()` and calls `masks.build_masks()` for every region boundary -- the same functions rounds two and three already used -- so nothing about where the green, creek, or bunkers sit moved by a single pixel; only how they are painted changed.

### What render_ground.py actually draws

- **Base turf.** A per-pixel inverse-camera lookup (`yd_grids`, the same technique round three's `perspective_texture` used for tile sampling, kept here for computing model `(x_yd, y_yd)` per screen pixel rather than for sampling an image) drives mow stripes: alternating +/-5% bands every 4 yards of depth, computed directly from `y_yd` rather than from a tiled texture. Beyond the fairway/tee mask (feathered 20px, per the brief), the same stripe pattern is recolored warmer and darker for rough. A quadratic falloff darkens the two bottom screen corners (not a full vignette), and independent per-pixel grain (sigma ~6, about 2.4% of 255) keeps the fill from reading flat.
- **Anti-aliasing the stripes, not just the fill.** The first pass at this drew stripes with a hard `floor(y_yd / stripe_width)` and got a wall of Moire banding near the green -- the camera's depth budget compresses so much yardage into so few screen rows near the horizon that a fixed-yard stripe period aliases into noise well before the literal horizon line. The fix (`row_resolution_fade`) measures the actual yards-per-screen-row at each row and fades the stripe contrast out once that resolution can no longer support the period, rather than fading on a fixed fraction of the camera's total depth range. This is the same fix applied to the green's finer 2-yard stripes and the bunkers' rake lines.
- **Tee box.** A separately-rasterized crisp rectangle (its own polygon, not unioned into the fairway blend) in a lighter tint, feathered 1.5px.
- **Rae's Creek.** Deep blue-green water color, computed per pixel from where it falls between the model's exact near/far bank curves (a triangular "center streak" weight, brightest at mid-channel) plus a small sinusoidal ripple. The far (green-side) bank is `model._front_edge_yd`, exactly, and a crisp 2px cream line traces it -- the near bank gets a softer, wider dark shadow line instead, so the channel reads as having two different kinds of edge rather than one flat tint on both sides.
- **Green.** The brightest surface, finer (2-yard) stripes, a fringe collar (a polygon expanded 1.5 yards past the green's own edges on every side, mask-subtracted so it never overlaps the putting surface itself), a thin light rim line, and soft shadow bands along the back edge and the screen-left edge (sketch.py's `x = -half_width` line, "left" by the same "positive x = right/Sunday side" convention the camera projection itself uses).
- **Bunkers.** Sand fill with a low-amplitude, high-frequency mottle (increased in frequency from an early attempt that read as one visible light-to-dark gradient across the whole bunker rather than fine grain), a darker lip line along each bunker's far edge, faint rake lines (same anti-alias treatment as the turf stripes, so they recede correctly at the green complex's distance rather than banding), and a boundary perturbed by a smooth, low-amplitude (1.6px) displacement field (`wobble_mask`) so the edge reads as drawn rather than a clean polygon.
- **Shaved-bank halo strips.** `masks.py`'s existing `bank` mask (bunker-surround halos, including the strip between the front bunker and the creek that the brief calls out as "in front of the green"), filled with a lighter, more yellow-green tone, feathered only 3px.

### Compositing: two layers, one soft seam

`composite.py` is now a small file. It loads the plate (unchanged patching and horizon-crop from round three), renders the ground, and blends them with one vertical ramp: pure plate above `sketch.HORIZON_PX`, pure ground from 40px below that down, linear in between. That 40px band is the only place the plate and the code-render ever mix; everything else is one or the other outright. Pins are drawn last, at the same exact projected coordinates every round has used, now slightly larger (50px stick, wider pennant) with a 1px dark outline so they hold up against the brighter green at phone width.

### Registration result

```
python3 registration_qa.py hero.png
-> 15/15 landmarks within 5.0% of image width -> overall PASS
```

No detector thresholds needed changing. The one landmark type at risk was `creek_far_bank` -- the far-bank stroke is now a thin cream line rather than a blue one, per the brief's art direction -- but the `creek_win = 24` search window still finds genuinely blue water pixels immediately adjacent to that line on every sample, so `is_blueish` keeps passing without modification. `hero_overlay.png` and `registration_report_hero.json` are regenerated against the new composite.

### What the plate still contributes, and what it lost

The plate contributes exactly the sky, the pine tree line, and the azalea beds along its base -- the top roughly 20% of the frame plus the 40px transition band. Its own ground (the sculpted, dark, blurred rendering round three's verdict discarded in spirit) is now discarded in fact: `render_ground.py` never reads a pixel of the plate's own grass, and nothing below the transition band comes from nano-banana at all.

### What is still weak, honestly

(1) The fairway corridor, after several contrast passes, reads clearly at the hole itself but stays subtle across the wider expanse of open rough -- the brief's "fairway but no sticker edge" is achieved, but a viewer scanning the far background rather than the hole might not immediately register where the corridor's outer edge sits. (2) The two back bunkers are still small, thin slivers at this camera distance -- a pre-existing framing fact from the model's own geometry (the green complex sits far from camera), not something this round's rendering approach can fix without moving geometry, which is out of scope. (3) The creek's reflective center streak and ripple read correctly as water up close but are subtle at a quick glance on the full 1600x900 canvas; a stronger streak would help but risks looking like a highlight rather than a reflection. None of these is the smear/no-presence/smudge failure this round set out to fix -- all three of those are resolved -- but none should be called perfect either.

### Round four deliverables

- [x] `render_ground.py` -- the code-rendered ground plane, imported by `composite.py`
- [x] `composite.py` -- rewritten to blend the plate (sky/trees only, via the horizon transition) with `render_ground`'s output, plus pins
- [x] `hero.png` -- 1600x900, round four
- [x] `hero_variant_b.png` -- same render with stronger stripe contrast and a warmer turf tone, for the orchestrator to choose between
- [x] `hero_mobile_crop.png` -- 506x900 (9:16) center crop
- [x] `hero_overlay.png` / `registration_report_hero.json` -- 15/15 PASS, no threshold changes
- [x] `environment_plate_v1.png` deleted (round two's plate, 1.58MB, unreferenced by any code -- `environment_plate.png`, round three's candidate, remains the plate in use)

## Deliverables

- [x] `hero.png` -- 1600x900 accepted hero art, round four (code-rendered ground, generated sky/tree band)
- [x] `hero_variant_b.png` -- round four's deliberate-difference variant (stronger stripes, warmer turf)
- [x] `hero_mobile_crop.png` -- 506x900 (9:16) center crop
- [x] `hero_overlay.png` -- sketch-over-hero registration overlay
- [x] `registration_report_hero.json` -- 15/15 PASS
- [x] `environment_plate.png` -- round three's horizon-matched plate, still the plate in use; `environment_plate_v1.png` (round two's) deleted round four, see above
- [x] This README: stencil architecture, prompts (`prompts/` has round one's; round two's and round three's plate/tile prompts are inline in `composite.py`'s git history and the "Round three" / "Round-two generation prompts" sections below), per-layer inventory

## Round-two generation prompts

**Environment plate** (`environment_plate.png`):
> A beautiful painterly editorial illustration of open golf course parkland, in the style of Augusta National's back nine. Rolling mown grass filling the foreground and midground, azaleas in pink and white blooming in beds along a tree line, tall mature pines forming a backdrop across the whole horizon, soft natural overcast sky above the treeline. Camera elevated, wide open grassy view. Do NOT include: any water, creek, stream, or pond; any sand bunkers; any putting green or flags; any bridge; any path or cart trail. Just open grass, azalea beds, pine trees, and sky -- a backdrop plate with no hole features at all. Style: painterly-but-clean editorial illustration suited to a data-journalism site header, confident brushwork, clean readable shapes, muted Masters color palette (soft greens, warm cream light). No text, no logos, no watermarks, no people, no animals, no equipment. Aspect ratio 16:9.

**Grass tile** (`tiles/tile_grass.png`):
> An extreme close-up, top-down texture of tightly mown golf course grass, Augusta National style vivid muted green, subtle linear mowing stripes running across the frame, even lighting, no shadows of objects, no people, no equipment, no text, no logos, tileable seamless texture, painterly-but-clean editorial illustration style.

**Water tile** (`tiles/tile_water.png`):
> An extreme close-up, top-down or gently angled texture of dark blue-green creek water with soft gentle ripples and a few subtle light reflections, calm slow-moving stream, no objects, no people, no boats, no text, no logos, tileable seamless texture, painterly-but-clean editorial illustration style, muted color palette.

**Sand tile** (`tiles/tile_sand.png`):
> An extreme close-up, top-down texture of pale warm golden bunker sand with faint rake lines, golf course sand trap texture, even lighting, no objects, no people, no rakes, no text, no logos, tileable seamless texture, painterly-but-clean editorial illustration style, muted color palette.

**Rough/bank tile** (`tiles/tile_rough.png`):
> An extreme close-up, top-down texture of slightly longer rough and bank grass beside a golf fairway, mown but less manicured than a putting green or fairway, muted green-gold blend with a little texture and variation, no objects, no people, no equipment, no text, no logos, tileable seamless texture, painterly-but-clean editorial illustration style.

---

## First architecture (superseded, kept for record)

Status: sketch pipeline complete and committed. Hero art generation attempted seven times across four prompt strategies. Every candidate failed the registration gate. Per issue #11's own failure clause and ADR 0001, this shipped the sketch pipeline plus a failure report and stopped -- see git history / `hero_candidates/` for the full record of that attempt, preserved below unedited.

### What's here

- `sketch.py` — renders `sketch.png` and `sketch_coords.json` straight from `data.py`/`model.py`'s own geometry.
- `sketch.png` / `sketch_coords.json` — the layout sketch and its landmark coordinates.
- `hero_candidates/` — all 7 round-one candidates, their overlays, and `registration_report.json`.
- `prompts/` — round one's exact prompt text per candidate.

### Generation attempts

Model: `gemini-2.5-flash-image`, via the wardrobe project's `scripts/gen-image.py`, `GEMINI_API_KEY` read from `wardrobe/.env`. Every call used `--ref sketch.png --aspect 16:9`. Output resolution: 1344x768 for every candidate.

| Candidate | Prompt strategy | Registration | Verdict |
|---|---|---|---|
| 1 editorial | Loose: "transform into art, keep every feature where the sketch places it," painterly editorial style | 1/15 landmarks in tolerance | Beautiful, but no tee box in frame, creek redrawn as a winding river, not the diagonal band |
| 2 retro flat | Same loose prompt, flat retro-poster style | 4/15 | Same failure mode: winding river, invented bridge, no tee box |
| 3 atmospheric | Same loose prompt, atmospheric golden-hour style | 2/15 | Same failure mode, plus 6 pin flags instead of 3 |
| 4 editorial strict | Literal "coloring book, do not change the shape" instructions | 11/15 | Highest registration score, and worthless: double-exposure defect |
| 5 retro flat strict | Same literal instructions, flat retro-poster style | 9/15 | Same double-exposure defect as candidate 4 |
| 6 composition-specific | Explicit tee-box/fairway/diagonal-creek/three-pin composition instructions | 0/15 | The best-looking single coherent image of the seven, and the furthest out of registration |
| 7 composition-diagonal | Candidate 6's prompt plus stronger asymmetry language | 7/15 | Regressed: fairway rendered as a sand-colored path, creek flattened, only 2 pins visible |

Full per-landmark offsets: `hero_candidates/registration_report.json`.

### Why every candidate failed

Two distinct failure modes: loose/composition-specific prompts produced coherent, often beautiful illustrations that redrew the creek's path and shifted the green complex's scale/position rather than locking to the sketch's pixel geometry. Literal "preserve this exact shape" prompts caused a double-exposure defect: the sketch's own flat-color shapes stayed visibly pasted over a separately imagined background. No middle ground between these two prompt families was found across four distinct wording strategies -- which is what motivated the architecture change to a Pillow-enforced stencil instead of asking the generator to respect geometry at all.
