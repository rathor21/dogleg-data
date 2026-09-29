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

## Round 2 and camera fit

### Pick change

Sunny first picked r1_5, then switched to **r1_8** (sunset dusk, bay frame, white painted center line). Everything built on r1_5 stays in `candidates/` under the `r2_r1_5_` prefix (portrait tries, cleanup edits, its own contact sheet) and in `prompts/` as `r2_r1_5_*.txt`. Nothing was deleted.

### Final images

| File | Size | Source |
|---|---|---|
| `range_final.png` | 1376x768 (16:9) | `candidates/r2_w_edit_b.png`, a nano-banana edit of r1_8 |
| `range_final_mobile.png` | 768x1376 (9:16) | `candidates/r2_m_edit.png`, a nano-banana edit of r1_8 |

Contact sheet of all round 2 candidates: `candidates/r2_contact.png`.

**Recommended wide image: `r2_w_edit_b`.** It is r1_8 with two changes (prompt in `prompts/r2_wide_edit_b.txt`): the metal-railed bay dividers shrink to low corner panels (they now stop below row 580 instead of row 440), and two more greens step back along the range (a large green right of the line, a small one on the line). The sunset, the trees, the floodlights, the center line and the mat stay as in r1_8. The faithful version is `r2_w_upscale.png`.

Other round 2 candidates and why they lost:

- `r2_w_upscale`: the "upscale" edit returned r1_8 at the same 1376x768 size, unchanged to the eye. It is the fallback if the edit look is unwanted.
- `r2_w_edit_a`: merged the left green with a new one into a wide double-flag oval. Rejected.
- `r2_m_gen_a`, `r2_m_gen_b`: text-to-image portraits. They look good but drift from r1_8 (different sky, a clean tee mat, no orange band). Rejected for not matching the pick.

**Resolution limit.** The nanobanana extension (both the default model and `gemini-3-pro-image-preview`) returns 1376x768 for 16:9 and 768x1376 for 9:16 whatever the prompt asks. It has no size or aspect option. The upscale edit, the pro-model regeneration and the edits all came back at that size, so no higher resolution version exists. No resampled or code-drawn version was made. 1376 px is enough for a page column of about 700 css px on 2x screens.

**Portrait.** Made with nano-banana (`prompts/r2_mobile_edit.txt`, an edit of r1_8 asked to recompose to 9:16 with the sky extended to 45 percent of the frame). It kept the sunset band, the white center line, the striped fairway and the greens. It dropped the bay dividers, which suits a phone. No crop was needed.

### Camera model

Full formula, with the rotation order, is in the docstring of `fit_camera.py`. The JS should reimplement it as written.

World frame (yards): origin at the ball, x downrange along the target line, y lateral (positive to the right seen from behind the golfer), z up.

```
fwd   = ( cos(pitch) cos(yaw),  cos(pitch) sin(yaw), -sin(pitch) )
r0    = (-sin(yaw),             cos(yaw),             0          )
u0    = ( sin(pitch) cos(yaw),  sin(pitch) sin(yaw),  cos(pitch) )
right =  r0 cos(roll) + u0 sin(roll)
up    = -r0 sin(roll) + u0 cos(roll)

d  = P - C                       C = cam_pos = [-3, 0, 1.8]
Xc = d . right,  Yc = d . up,  Zc = d . fwd     (Zc is depth, must be > 0)
u  = cx + f * Xc / Zc
v  = cy - f * Yc / Zc            (v is the image row, growing downward)
```

Positive yaw turns the camera toward +y (right). Positive pitch tilts the camera down. Positive roll lifts the image's right edge. Angles in the JSON are degrees. To place a pixel on the ground: `ray = fwd + ((u-cx)/f) right - ((v-cy)/f) up`, `t = -zc/ray.z`, `P = C + t*ray` (valid below the horizon).

### Assumptions

- Camera height 1.8 yd, camera 3 yd behind the ball (x = -3), on the target line (y = 0).
- Principal point at the image center, square pixels, no lens distortion, flat ground.
- No ball is painted, so the ball anchor is the mat center on the white line: (689, 712) wide, (386, 1290) portrait. **The focal length f is set by this anchor**, because f trades against the fixed 3 yd offset. Moving the anchor 20 px moves f by about 5 percent.
- Floodlight poles are vertical, equal in height and in a straight row on each side.
- Mowing stripes are parallel to the target line with constant width.

### What was measured

`landmarks_final.json` and `landmarks_final_mobile.json` hold pixel coordinates read from zoomed, gamma-brightened crops: the center line at 11 to 12 rows, base and lamp of 6 poles per side (wide) or 3 to 4 per side (portrait), the ball anchor, greens (center and left/right edges) and 3 stripe edges (wide only). The horizon (vanishing row) is not measured on its own. The pole rows give it: (pole base row - horizon) is proportional to pole pixel height, and the left and right rows agree (301 and 302 in the wide image, 550 and 551 in the portrait).

### Fit results

| | Wide | Portrait |
|---|---|---|
| f (px) | 723.8 | 1302.4 |
| pitch (down) | 6.59 deg | 6.16 deg |
| yaw | -0.05 deg | -0.08 deg |
| roll | -0.18 deg | -0.03 deg |
| horizon row | 300.4 | 547.5 |
| residual, center line, poles, ball (RMS) | 1.06 px | 1.81 px |
| pole row lateral offsets | -12.5 / +13.4 yd | -9.8 / +10.7 yd |
| pole height | 3.5 yd | 2.8 yd |
| stripe width | 4.0 yd (pinned to the lower search limit, residual 66 px) | not fitted |

The center line is vertical at the image center, so yaw and roll come out near zero as expected. Pole rows on both sides fit within 1 to 2.5 px.

**The stripes do not fit.** The stripe edges and the center line's width taper converge toward a vanishing row of about 340 to 390 in the wide image, while the pole rows and tree base line say 301. The painting is not perspective-consistent between its ground texture and its poles. The fit therefore uses the poles, center line and ball for the camera, and solves stripe width and offset in a second step with the camera held fixed. Treat the stripe width (4.0 yd, at the search limit) as unreliable. The portrait has low-contrast stripes and none were fitted.

### Painted greens back-projected to z = 0 (z_c = 1.8 yd)

| Wide | x (yd) | y (yd) |
|---|---|---|
| A, left near | 10.3 | -3.9 |
| B, right near | 7.6 | +4.6 |
| C, left mid | 29.5 | -3.2 |
| D, right mid | 20.0 | +3.5 |
| E, center far | 101.8 | +0.2 |

| Portrait | x (yd) | y (yd) |
|---|---|---|
| H, left mid | 25.2 | -2.8 |
| J, right near | 18.5 | +3.0 |
| E, center far | 67.7 | 0.0 |

Edges are in `camera_final*.json` (`left_edge_yd`, `right_edge_yd`).

### Concern: the painting is small next to real yardages

With a 1.8 yd eye height the painting reads as a short, narrow field: greens land between 8 and 100 yd and the pole rows sit 25 yd apart. The image was drawn as if from a raised deck (pole base row to lamp is about twice the eye-to-ground gap). Consequences for the page:

- The painted greens cannot serve as labeled yardage targets at their back-projected positions (10 yd, 20 yd and so on). Label them by order or skip them.
- The whole 50 to 300 yd ground range squeezes into a band about 20 px tall just under the horizon (wide: 50 yd at row 325, 100 yd at 313, 300 yd at 305, horizon 300). A ball landing at 250 yd draws at row 306, inside the dark tree band, above the painted fairway edge (row 312 to 316).
- Raising z_c fixes some of this: `python fit_camera.py landmarks_final.json out.json 4.5` (the third argument is z_c). Sweep on the wide image:

| z_c (yd) | f | pitch | greens A, B, C, D, E (yd) | stripe residual |
|---|---|---|---|---|
| 1.8 | 724 | 6.6 deg | 10, 8, 30, 20, 102 | 66 px |
| 4.5 | 352 | 13.3 deg | 13, 10, 37, 25, 129 | 11 px |
| 9.0 | 248 | 18.6 deg | 19, 14, 55, 38, 191 | 10 px |

  The stripe residual drops at higher z_c, but f falls to a very wide lens (about 126 deg field of view at 4.5), so the geometry is not physical either. The spec's z_c = 1.8 is what ships in `camera_final*.json`.

### QA overlays

`range_final_fit_overlay.png` and `range_final_mobile_fit_overlay.png` (made by `overlay_fit.py`) draw the 50 to 300 yd ground lines (yellow, y from -30 to +30), the center line (magenta), y = +-10 and +-20 lines (cyan), the back-projected greens (red circle at the painted pixel, white cross at the projected ground point), the horizon (orange), a straight driver tracer with apex 35 yd at x = 165 (white), and the same with a 25 yd draw toward -y (green), both ending at x = 280.

- The 300 yd line sits below the horizon in both images (wide 304.8 vs 300.4, portrait 555.4 vs 547.5).
- The driver tracer stays inside the frame. Its highest pixel is row 68 of 768 (wide) and row 131 of 1376 (portrait). The highest point on screen is near the ball, not at the 165 yd apex: a ball 15 yd downrange and 6 yd up is 18 yd from a camera at 1.8 yd, so it climbs high in the image. The true apex projects at row 152 (wide). The page can keep the full 35 yd apex without scaling.
- The tracer's far end lands next to the horizon row, so the flight reads as a tall arc that returns to the center of the frame, like a view from behind the golfer.
- The mowing stripes do not follow the projected lines. They are shallower than the perspective the poles imply, as noted above.

### Files

- `landmarks_final.json`, `landmarks_final_mobile.json`: measured pixels.
- `fit_camera.py`: numpy-only Levenberg-Marquardt fit and the projection functions. Usage: `python fit_camera.py landmarks.json camera.json [z_c]`.
- `overlay_fit.py`: overlay renderer.
- `camera_final.json`, `camera_final_mobile.json`: fitted cameras, with `greens`, `assumptions` and the fit residuals.
