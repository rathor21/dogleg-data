Make the shot map subordinate: smaller, lower contrast, no title, no distance labels, softer path with a bright landing dot.

## Behavior (single root cause)
v3 added a "SHOT MAP" inset that fixed curve legibility but pulled the eye off the shot and its name. Train evidence, v1 to v3: c2 0.39 to 0.92 (test 0.67 to 0.79), c6 0.72 to 0.44 (test 0.67 to 0.29). The v3 train judge reasons for c6 name the map as one of the competing items: "Five range overlays, an inset map, a toolbar row and six tiles crowd the screen", "six banded tiles and a slider panel with chips all compete with the Fade heading", "A dense tracer knot with badges, five range labels, an inset lens shape and a slider panel compete". The map was too heavy (78% dark panel, all-caps title, glowing paths, four label groups) for a secondary view.

## Change (site/ball-flight: range.js, tool.css)
- Footprint: height 31% of the range (v3 46%), min 88 px, max 236 px times the Present scale; width 0.8 of height, capped at 27% of the range width (v3 36%). About 65% of v3 in each dimension. Skipped under 78 px tall.
- Removed the "SHOT MAP" title and the distance rung labels (25, 50, 100). The rungs stay as faint unlabeled lines; the range plates carry yardage. Only the L and R scale labels remain, since they explain the stretched axis.
- Lower contrast: --map-bg .78 to .46, edge .26 to .14, grid .13 to .09, muted text .72 to .6, target line .6 to .34, start line .5 to .3.
- Paths: thinner (1.3 px, v3 1.7), no glow underlay, a softer warm tint (pinned A a soft blue) at about 86 to 90% alpha. The landing dot, the live head dot and the A and B letters keep the bright ball color and ring, so the outcome is the brightest thing on the map.
- Cost: the panel, rungs, L/R labels and target line render once into an offscreen canvas (keyed by size, scales, dpr, tokens) and blit per frame. Per frame work is the clip, the paths and the dots.
- Unchanged: corner logic and plate avoidance, lefty mirroring, Present scaling, Compare A/B, Fly all nine, the range projection, painted greens, flight.js, data and round 1 layout.

## Expected movement
c6 back toward v1 (train 0.44 toward 0.7; test 0.29 toward 0.5 or better). c2 held: the curve and start side stay readable on laptop, tablet, TV and phone portrait, at somewhat lower contrast, so a small slip (0.05 to 0.15) is possible. c5, c8 flat or up (fewer overlays, no caps title).

## Risks
- Phone portrait panel is about 85 x 120 px; the curve of a small draw or fade is a thin sliver and the judge may again call it unreadable. Fly all nine on phones stays a lens with no numbers.
- Softer path and grid may read as too faint on bright ranges.
- The judge may still count the map as an overlay; if c6 stays low the next step is to hide the map on phones or show it only after the shot lands.
- Scratch input p95 on 7 train cases: 15.9 to 19.0 ms (phoneland-flyall worst), laptop cases 16.0 and 16.5 ms; no console errors, no overflow, axe 0.
