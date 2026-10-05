# Dogleg Data — Domain Glossary

Canonical vocabulary for the analyses. Terms here are binding across releases; if a draft uses a word to mean something else, the draft is wrong.

## Cost line

The drive distance below which a golfer's expected score on a hole exceeds their handicap tier's benchmark by more than 0.10 strokes (one shot per ten rounds). The headline metric of release 002. Not a strokes-gained-zero crossing: under the own-tier baseline that crossing degenerates to the tier average by construction.

## Tier benchmark

The calibrated model's expected score for a handicap tier at that tier's typical play, pinned to Shot Scope's published aggregate scoring per band. Length-resolved values are MODELED and labeled as such.

## Dispersion oval

The two-dimensional distribution of where a golfer's shots at a single target finish: distance error (long/short) and line error (left/right) together. The unit of analysis for release 003. A dispersion oval belongs to a golfer-club pair, never to a single swing.

## Aim point

The spot a golfer should aim at, chosen to minimize expected score given their dispersion oval and the hole's architecture. Two-dimensional: a line component (where to aim laterally) and a club component (how far to carry). Release 003's verdict is an aim point per handicap tier per pin position.

## Sucker pin

A pin position whose direct line puts a meaningful share of the dispersion oval into a hazard or short-sided lie, so that aiming at it raises expected score for the tier in question. Whether a pin is a sucker pin depends on the oval: the same pin can be fair for a scratch golfer and a sucker pin for a 15.

## Short-sided

A miss that finishes on the same side as the pin, leaving little green between the ball and the hole. Priced in the model through the recovery leg, never treated as merely "a missed green."

## Ball flight laws

The short list of cause and effect instructors teach: the face sets the start line, face-to-path sets the curve, attack angle changes launch and spin and moves the path. The subject of release 004. The article puts a weight on each rule and the lab lets a student move the inputs.

## Face-to-path

Face angle minus club path, in degrees, right positive. The ball curves toward the face and away from the path, so a positive value curves a right-hander's shot right. The same face-to-path bends a driver farther than a wedge, because the tilt of the spin axis falls as spin loft rises. Zero face-to-path gives no curve.

## Spin loft

The 3D angle between the club head's direction of travel (attack angle and path) and the face normal (dynamic loft and face angle). Dynamic loft minus attack angle approximates it and drifts as face-to-path grows. Higher spin loft gives more spin and lower smash factor. Not the same as the club's static loft.

## Spin axis

The tilt of the ball's spin axis from horizontal, in degrees, positive curving right. The model takes it from the D-plane, the plane through the club's travel direction and the face normal. A spin axis within 2 degrees of zero counts as straight.

## Window

One of the nine trajectories of the nine-windows drill: low, mid or high height crossed with draw, straight or fade. A window's recipe (path, face, attack angle, dynamic loft) is MODELED output. The drill is Tiger Woods's. The numbers are not his.

## Swing direction

The horizontal direction of the plane the club head swings on, in degrees, right positive. Club path is the swing direction minus the attack angle times the tangent of 90 minus the vertical swing plane: a vertical change in the attack angle tilts the arc and shifts the path. The lab's "path follows attack angle" switch holds the swing direction while the attack angle moves. The swing plane is a per-club number, anchored at the driver and the 6 iron and MODELED elsewhere.

## Lie at impact

The change in the club's lie angle at impact from its address lie, in degrees, positive toe up. A rotation of the head about the target line: toe up opens the face by about the tangent of the loft per degree and toe down closes it. Geometry, not a fitted number. The lab's face angle tile shows the face after the lie tilt, the slider the face before it.

## Strike location

Where the ball meets the face, in millimeters from the face center, toward the toe and upward. It drives the gear effect, the bulge and roll of a wood face, and the ball speed loss. A preset is a center strike, and its spin trim stands for its player group's typical strike, so the lab's strike sliders are offsets from that strike.

## Gear effect

The spin an off-center strike adds because the head turns about its center of gravity and friction turns the ball the other way. Horizontal: a toe strike adds draw spin and a heel strike fade spin, on every club. Vertical: a strike above center takes backspin off a driver or fairway wood, below center adds it. The added spin is a vector sum with the D-plane spin, so the spin rate and the spin axis both move.
