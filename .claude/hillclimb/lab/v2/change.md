Widen the tracer's sideways offset about 2x in the range projection so curve and start side read at every distance (display only, model numbers untouched).

## Behavior (single root cause)
The range art is a fitted real-perspective camera seen from behind the ball. A 7 yd curve over a 175 yd carry spans only a few dozen art pixels, so every tracer paints as one near-vertical line hugging the dashed target line. The judge cannot tell start side or curve direction (c2), Compare's A and B ride the same band, Fly all nine piles into one bundle with the number badges on top (c5, c6), and the lefty and window scenarios cannot show the mirrored curve (c7).

## Evidence (train, judge reasons verbatim, v1)
- laptop-fade-driver-lpga c2: "The tracer is bright and thick but rises almost vertically on the target line, so the slight left start and right drift cannot be told from the picture."
- tabletp-lefty-draw c2: "The tracer is a near-vertical line that barely leaves the target line, so the left start and right curve of a lefty draw cannot be told from the picture."
- phone-window-high-draw c2: "The tracer is a thin near-vertical line that runs off the top of the picture, so curve direction and start side are not clear."
- tabletl-window-low-fade c2: "it rises almost vertically with a faint dashed companion, so the left start and right curve are hard to tell."
- phone-lefty-hook c2: "The tracer is a narrow near-vertical line with a faint dashed companion, so the left-hander's start side and right curve cannot be told."
- tabletp-slice-to-draw c2 and laptop-compare-slice-draw c2 and tv-present-compare c2: "rise almost on top of each other in a narrow band" / "in a narrow overlapping band so each one's start side and curve are hard to read" / "Three overlapping tracers ... rise in a narrow band".
- phoneland-flyall c2: "The nine tracers pile into one narrow vertical bundle at the center of the range, so each window's direction cannot be told." c5: "Numbered circles 1, 3, 4, 5 and 8 crowd and overlap the tracer bundle".
- Half credit only: phone-wedge-fade, phoneland-driver-draw, tv-present-driver-draw, tv4k-present-hook (c2 0.5, "reads as nearly straight" / "a thick bright tracer ... bends left").

## Count
c2 loses about 11.5 of 18 points on train (13 of 18 cases below 1; 9 at 0). c2 is now the lowest-but-one claim (.50) and the only one that fails in every viewport class including TV. Runner-up causes are smaller or split: c5 (12.5 points, but four unrelated sources: laptop tile wrap, bottom bar over content, label collisions, badge overlap) and c4 (unlabeled chevron, about 6 points on phone and tablet). Related follow-on points (c5 flyall, c6 flyall, c7 lefty and compare) add about 3 more to this cause.

## Change (site/ball-flight/range.js only)
project() now maps the sideways offset through lat(y) = 2.4 y / (1 + |y|/35): about 2x for ordinary curves, monotonic, odd, saturating (max about 84 yd drawn) so a big slice stays in frame. Tracer, ground shadow, start-line guide, landing rings and plates all go through project(), so they stay consistent. Left and right, ordering of shots (A versus B, the nine windows) and the vertical projection are unchanged. Carry, side and curve text and every tile come from the model and are unchanged. Cost: the landing spot is no longer at the painted green's true lateral yardage (art is an illustration per the rubric).

## Expected effect by claim
c2 up most: about +0.3 to +0.4 of the 11.5 lost points recoverable on curved shots (draw, fade, hook, lefty, windows, compare), Fly all nine spreads (c2, c5, c6 on that case). c7 up slightly on lefty, compare and windows. Others flat. Design mean ceiling about +0.04 to +0.06 on all 30 cases. That is at or inside the noise floor (about 0.045 held-out), so a rise may not be distinguishable from noise even if it is real. Straight shots and TV present cases with a real curve (driver draw, hook) were already at 0.5 and should move to 1.

## Possible regressions
- A lateral yardage is drawn about 2x wide, so a shot that finishes 3 yd right no longer lands 3 yd from the line at painted-green scale; a coach reading the painted greens against yardage would see exaggeration. Text stays exact.
- tabletp-slice-to-draw: the A carry plate still sits under the shot label card (same defect as v1, not new).
- Fly all nine: tracers now span a wider band, so a few numbered badges sit farther out on the range.
Verified: parity.mjs OK, scratch render of 8 train cases (phone, phone landscape, tablet, laptop, TV present compare) with console errors 0, axe serious 0, small_targets unchanged (26 to 39 on touch, 0 on laptop and TV), input p95 16 to 18 ms, load 126 to 250 ms.
