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
