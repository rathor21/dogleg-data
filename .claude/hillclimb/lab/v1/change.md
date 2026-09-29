Budget the first screen: compact the header and cap the range height so the mode's numbers and controls sit above the fold.

## Behavior (single root cause)
The page chrome (logo row, h1, a 2 to 3 line intro paragraph, a row of six cross-tool pills, the mode bar) takes 285 to 370 px, and the range then takes its full width-driven height (aspect 1376:768, or 0.62 tall on phones). Everything a scenario teaches with (the six key tiles, the 9 Windows grid and recipe, the Compare table, on a phone the tiles and hand/club setup) is laid out after the range in the same column, so it lands below the fold or under the phone drawer. The judge then fails c3 (numbers visible), c4 (controls reachable), c7 (teaching fit), and c6/c5 pick up the crowding, cut-off nav pill and a label card that covers the tracer.

## Evidence (train, judge reasons verbatim)
- laptop-launch-spin-numbers c3: "Launch angle and spin rate values are absent, since the tile row shows only its labels Face to path, Launch direction and Spin axis at the bottom edge with no in-band signal."
- laptop-fade-driver-lpga c3: "the face-to-path value is not visible since the tile row is cut off with only its label showing."
- laptop-hook-first-screen c3: "the face-to-path value is not visible since its tile shows only the label at the bottom edge."
- laptop-compare-slice-draw c3/c4: "The A/B/difference table is not on screen, since the Compare two shots panel shows only its heading at the bottom edge." / "No Pin this shot button is visible because the Compare two shots panel sits below the fold with only its heading showing."
- tabletl-window-low-fade c3/c4: "the 9 Windows grid begins at the bottom edge with only its heading visible." / "The nine window buttons that the coach must tap are below the fold with only a 9 Windows heading peeking in."
- tabletp-slice-to-draw c3: "the Compare two shots panel is cut off after its Re-pin and Clear buttons."
- phone-wedge-fade c6: "The Dogleg Data header, page title and two tab rows outweigh the small Fade label at the bottom."
- phone-window-high-draw c4: "The nine-window grid is not on screen and no visible handle points to it"; c3: "attack angle and loft are absent."
- phoneland-driver-draw c3/c4/c6: "path and face values are not on screen", "The path and face sliders sit below the visible area", "The logo, title, two tab rows and a tall slider panel take most of the 390 px height."
- phoneland-flyall c4: "The window grid needed to tap or match windows is not visible and sits below the fold."
- phone c5 (wedge-fade, default-7i, window): "The Tee shot calcu chip is cut off at the right edge" (the nav pill row that this change moves).
- tabletp-lefty-draw c6: "The large logo, three-line intro and two rows of nav pills take the top third."
Screens: baseline/shots/<id>.png for each id above. Best contrast: tv-present-driver-draw and tv-present-slice-amateur (0.94), where Present mode drops the chrome and the tiles and label fill the screen, and tabletp-attack-down-driver (0.75), where the range is at the top and the open drawer holds the controls.

## Count and cost
15 of 18 train cases lose c3 and/or c4 to this (all except the 3 TV present cases that pass, tv-present-compare partly). Sum of c3 + c4 + c7 failures on train, minus the TV present cases: c3 fails 14, c4 fails 11 (plus 4 half), c7 fails 13. About 38 claim points of 144 (0.26 of the design score), with c6/c5 adding roughly 6 more points of the same cause (chrome outweighing the shot, cut-off nav pill).

## Change (site/ball-flight: tool.css, ui.js, windows.js)
- Intro paragraph removed (mode hint carries the instruction), h1 smaller, header and tab spacing tightened at all sizes.
- Range gets max-height = 100dvh - drawer - a per-layout reserve (--reserve, --range-min), larger reserve in 9 Windows and Compare (ui.js sets body[data-mode]). Presenting mode is unchanged (max-height none).
- Phones and tablet portrait: the cross-tool nav pills move under the lab (no more clipped pill); phone range is 1:1, shot label compact under it, key tiles show all six in 3 columns without bars, Windows recipe (path, face, attack, loft) sits above a compact grid, Compare and Windows hide the redundant range bar, Hit stays in the drawer.
- Phone landscape: sliders side panel starts beside the mode bar and uses a 36 px thumb so path and face fit; nav moves down.
- 901 to 1199 wide: all six key tiles show (3 columns) instead of hiding face to path and spin axis.
- Shot label max width 42% of the range so it no longer covers the tracer or the A/B pills.
- 9 Windows buttons use a grid (badge beside the name, not on top of it); the club note is empty when the club is already the 7-iron; Compare card puts actions and status on one row with tighter table rows.

## Expected effect by claim
c3 up most (tiles, windows recipe, compare table, path and face now on screen at laptop, tablet, phone landscape, phone). c4 up (windows grid and compare controls on screen, sliders in landscape). c7 follows c3/c4. c6 and c5 up (no cut-off pill, label off the tracer, chrome smaller). c2 slightly up from wider ranges. c1 and c8 flat. Rough target: design +0.10 to +0.15 on phone, tablet and laptop, TV flat.

## Possible regressions
- Phone Compare and Windows: range is as short as 14rem (about 2:1); a 48 yd high tracer clips at the canvas top (also clipped in baseline).
- Phone Explore: range now 1:1 instead of tall, so the far end of the tracer is shorter; range bar drops Hit again (drawer has Hit).
- Laptop height under 800: range floors at 16rem and becomes a wide strip.
- Hand (Left) still has no on-screen indicator on phone and tablet portrait (not addressed, separate cause).
- Lefty and drawer-open cases (phone-lefty-hook, tabletp-attack-down-driver) are layout-identical to baseline apart from chrome.
Verified: parity.mjs OK, console errors 0, overflow_x 0, axe serious 0, input p95 14 to 18 ms (baseline about 15 to 18), load 122 to 252 ms on the 8 scratch cases and TV present unchanged.
