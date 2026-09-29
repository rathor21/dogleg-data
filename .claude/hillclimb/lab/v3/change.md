Add a top-down shot map inset in a corner of the range canvas so draws, fades and hooks read from directly behind the ball.

## Behavior (single root cause)
From directly behind the ball the fitted range camera compresses sideways motion, so a draw or fade paints as a near-vertical line. Train c2 on v1 was 0.39. Evidence (v1 judge reasons, train): phone-lefty-hook "a narrow near-vertical line ... the left-hander's start side and right curve cannot be told"; tabletp-lefty-draw "a near-vertical line that barely leaves the target line"; laptop-fade-driver-lpga "rises almost vertically on the target line, so the slight left start and right drift cannot be told"; tabletp-slice-to-draw and laptop-compare-slice-draw "rise in a narrow overlapping band"; phoneland-flyall "nine tracers pile into one narrow vertical bundle".

## The v2 lesson
Widening the sideways offset about 2x with the caption "sideways widened for clarity" lifted train c2 to 0.81, but the judges read the caption as debug text. Train c8 fell 0.73 to 0.20 and c5 0.30 to 0.13 (v2 reasons: "The 'sideways widened' caption looks like leftover debug text", "A stray 'sideways widened' caption sits on the range"). Curve legibility needs a designed feature, not a distortion of the picture or a disclaimer. v3 leaves the range projection and the painted-green plates exactly as in v1.

## Change (site/ball-flight: range.js, tool.css)
- range.js draws a "SHOT MAP" panel on the range canvas after the plates: rounded translucent dark panel (brand ink at 78%), 1px cream edge, mono type, distance rungs (25, 50 or 100 yd steps), the target line, the faint dashed start line, the live tracer (warm, animates with the flight), the ghost shot (dim, hidden in Compare), pinned A (cool blue), Fly all nine paths (warm, thinner), landing dots, "A" and "B" letters in Compare, and window numbers at each path's widest point on panels wide enough to hold them.
- Sideways axis is stretched on the panel face and labeled as scale, not as a caption: the bottom corners read "15 yd L" and "15 yd R" (compact "6 L" and "6 R" on narrow panels). The half-width steps through 6, 10, 15, 20, 30, 40, 50, 65, 80, 100, 130, 160, 200 yd to fit the widest shot.
- Layout: bottom-right by default; moves to bottom-left or top-right when the tracer or the shot label would touch it, and stays put until that happens. Present mode uses bottom-left (the key tiles own the right edge). Height is 46% of the range (min 124 px, max 360 px times the Present font scale), width 0.8 of that, capped at 36% of the range width. Type is 12 px minimum and scales with the Present font scale (15 px at 1080p, 30 px at 4K). It is skipped on canvases under 230x170 px. The panel is added to the plate avoidance list so yardage and carry plates route around it.
- Data comes from the existing flight x/y arrays in the display frame, so lefty mirroring matches the range. tool.css gains six --map-* tokens read by range.js.
- The separate Top view panel below the range is unchanged.

## Expected effect by claim
c2 up most (the target: curve side and start side readable on phone, tablet and laptop; Compare A/B and Fly all nine gain a second view). c8 and c5 flat or up: the panel uses the same tokens, radius and mono type as the plates, no caption, and nothing overlaps (plates and greens yardage avoid it). c6 flat: the panel is quiet and small next to the shot label. c1, c3, c4, c7 flat.

## Risks
- The panel covers about 30% of the range width on phones (100 x 140 px on a 354 px canvas). A very wide slice or push can move the tracer under the default corner, and the panel then jumps to another corner for that shot.
- Judges may count the panel as clutter (c6) or read the stretched axis as a distortion. The L/R scale labels are the mitigation.
- Fly all nine on a phone shows the nine paths as a lens with no numbers (panel too narrow); the numbers appear from laptop width up and can crowd near the landing point.
- Input p95 rose about 1 to 3 ms in the scratch run (16.1 to 20.4 ms on 6 train cases, tabletp-slice-to-draw worst); drawing is one panel with under 5 paths per frame.
