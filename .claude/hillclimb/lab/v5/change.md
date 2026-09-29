Fit the tile and key-number block to the fold: measure what sits under the range, give the range the rest, shorten tile notes so none wraps or orphans a unit, and hide what would peek out behind the drawer.

## Behavior (single root cause)
The first screen was budgeted with fixed rem constants (--reserve) that never matched the real height of the tile row, the 9 Windows card or the Compare card, and the tile notes ("ideal 209 to 222 yd") were free text that wrapped in narrow tiles. So the last row landed half under the fixed bar or cut at the viewport edge, notes broke mid-range, and a required carry plate could settle under the shot card. On phones a second cause hid in the CSS: .card padding won over .swing padding, so the closed drawer was 99 px tall while the page reserved 64 px, and the last tile row sat under it.

## Evidence (train, v1, judge reasons verbatim)
Defect A, last tile or grid row cut at the fold or faded under the bottom bar (6 cases plus 2 borderline):
- phone-window-high-draw: "The bottom row of the window grid ('Low straight') is cut mid-text by the fixed bottom bar."
- phone-default-7i: "The bottom row of tiles (Curve, Carry, Height) is cut off by the fixed bottom bar with the fade overlapping their text area."
- tabletp-lefty-draw: "The bottom row of tiles (Curve, Carry, Height) is cut by the fixed bottom bar with the fade over the 'ideal' lines."
- laptop-fade-driver-lpga, laptop-hook-first-screen, laptop-launch-spin-numbers: "their text is cut at the bottom edge."
- borderline: tabletp-slice-to-draw (compare table faded under the bar), tabletl-window-low-fade (9 Windows grid at the bottom edge).
Defect B, tile notes that wrap mid-range or orphan a unit (4 cases): laptop x3 "the six narrow tiles wrap awkwardly ('ideal -1.5 to / +1.5°', 'ideal 209 to 222 / yd', 'DIRECTION')" and tabletp-lefty-draw (fade over the 'ideal' lines).
Defect C, strips of content behind the open drawer (2 cases): phone-lefty-hook "A clipped fragment of the shot card peeks out above the drawer at the top edge, so text is cut mid-glyph." tabletp-attack-down-driver "The tops of three tile cards peek out as thin slivers above the drawer."
Defect D, plate under the shot card (1 case): tabletp-slice-to-draw "The shot shape card covers the left half of the A carry label so only 'yd carry' and a faded '201' remain visible." (tv-present-compare pills on the tracers is not addressed.)
Not addressed: phoneland-flyall numbered circles overlapping the tracer bundle, tv-present-compare pills, and 5 c5 scores that the judge explained with "only the normal bottom edge of the viewport" (no concrete defect).
c5 was below 1 in 16 of 18 train cases. Defects A to D cover 9 of them (union of the cases above).
c6 cases that cite the same elements: phone-lefty-hook ("Four large slider rows outweigh the small range picture"), phoneland-flyall, laptop x3 at 0.5 (tile row and sliders competing).

## Change (site/ball-flight: tool.css, ui.js, tiles.js, compare.js, range.js)
- ui.js fitFirstScreen: measures the bottom of the mode's block (key tiles, 9 Windows card, Compare card) and sets --reserve on body so the block ends 16 px above the fixed bar. If the range would drop below its minimum, body[data-fit="1"] trims detail (tile status line, Compare rows for height, launch and spin, 9 Windows recipe words and notes, padding). The range never gets flatter than 2.4 to 1 (the art crop breaks past about 3 to 1). Debounced 90 ms so a slider drag pays nothing. If the next section would show only a sliver above the fold it moves below it.
- Key tiles keep label, value, direction word, bar and status. The ideal range moves to the bar tooltip and stays in full in Every number. Tile notes are "ideal" plus an unbreakable range, so a note can wrap only after "ideal". Every number tiles are 11.5 rem minimum. "on the target line" becomes "on target line" in the tile.
- Key tiles hide in 9 Windows and Compare at every width (before: only at 900 px and below), so no tile row half shows under those cards.
- Nav pills sit under the lab at every width (before: 900 px and below).
- Phone drawer: padding fix so the closed drawer is exactly --drawer-h (64 px). With the drawer open, the stage below the range is hidden so no strip peeks out.
- range.js placePlate: a required plate that cannot find a clear spot takes one that the tracer crosses before one under the shot label.
- Tile update no longer rebuilds the ideal note when the band is unchanged.

## Expected movement
c5 up (roughly 9 of the 16 sub-1 train cases lose their cause). c6 up slightly (nav pills gone from the first screen, no tiles under Compare and 9 Windows, no cut rows). c1 to c4, c7, c8 flat. Range height at laptop 900 in Compare and 9 Windows drops from 388 px to about 395 to 435 px at level 1 (same), on tablet landscape to about 260 px.

## Guardrails (train, 18 cases)
0 console errors, 0 overflow, 0 serious axe, above_fold_ok 1, min font 13.5 mean (12 px floor kept), small_targets 16.9 (v1 17.1), input p95 16.1 ms (v1 15.7), load 204 ms (v1 207). parity.mjs passes.

## Risks
- Tablet landscape (1024x768) 9 Windows and short laptops get a range near the floor (16 rem tall), and 9 Windows at level 1 drops launch, spin, peak height and shot name from the recipe.
- Compare at level 1 drops height, launch and spin rows; a scenario about launch or spin needs Explore.
- Key tiles no longer show the ideal range in words (bar and marker only). c3 for "ideal band" scenarios reads it from the bar.
- Presenting mode is untouched. Phone landscape is untouched (its layout has no first-screen tiles).
- The 90 ms debounce means a mode switch shows the old range height for a moment.
