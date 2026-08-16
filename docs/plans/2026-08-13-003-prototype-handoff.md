# 003 Prototype Handoff: The Spectacle Test

Date: 2026-08-13 · Origin: grilling session for release 003 · Bridge: open a fresh session, run /prototype against this file. Throwaway from day one. Keep the answer, delete the code.

## The one question

Does the hero scene stop a scroll, at desktop full-bleed and at phone width?

Everything else is a sub-finding. If the hero scene does not stun with fake data, the real build never starts.

## Rev 2 (2026-08-13, mid-prototype): composition pivot

Sunny watched composition rev 1 (10,000-shot particle rain, top-down) render live and rejected it on sight. Rev 2 replaces it: five aggregated shot arcs flying tee to green in a perspective view (elevated three-quarter behind the tee, or a side-ish profile), each arc a curated representative with its own aim and shot shape (pin-hunter at the Sunday pin, center-green safe aim, draw, fade, under-clubbed ball into the creek), launches staggered so the eye follows one at a time. Landing scatter or ghost trails allowed as garnish under the arcs. The 10,000-run simulation engine still powers the analysis; the rendering shows curated representatives, never the raw cloud. The frontend-design and data:create-viz skills govern the visual build.

## What 003 is (context from the grilling)

Release 003 is an animation-led scrollytelling piece: where to aim, and what to club, on the 12th at Augusta National, one verdict per handicap tier per pin. Amateur tiers scratch/10/15/20 plus a Tour oval validated against published Masters hole-12 scoring. Three pins escalating left, center, Sunday right. Wind as a MODELED scenario multiplier. Aim sandbox tool after the story. LinkedIn leads with native video of the animation. Full nominative Augusta use per ADR 0001; no Augusta-owned imagery, own stylized rendering.

Glossary terms (CONTEXT.md is canonical): dispersion oval, aim point, sucker pin, short-sided.

## What to build

- One throwaway page. Whatever tooling is fastest; no build system for its own sake.
- Stylized rendering of hole 12 from memory-level geometry: tee box, Rae's Creek crossing the front, one front bunker, two back bunkers, the shallow green running diagonal front-left to back-right, three pin dots. Accuracy does not matter yet; beauty does. Brand style per `.impeccable.md` and `Dogleg_Data_Brand_Spec.md`.
- Fake but plausible ovals per tier. Suggested shapes: distance sd from ~8 yd (scratch) to ~16 yd (20-hcp), lateral sd from ~6 yd to ~12 yd, long-short error wider than left-right. Exact numbers are placeholders; the source hunt replaces them later.
- The shot rain: shots arc or fall onto the scene and accumulate as dots. Color code the outcomes: green, bunker, water, short-sided miss. Target 10,000 shots streaming in without jank.
- Tech ladder, in order: Canvas 2D first (expected winner), WebGL if Canvas chokes on particle count, SVG tried long enough to rule out. Record frame rates at each rung.
- One scroll-driven beat, whichever is cheaper to fake: the oval morphing across handicap tiers, or the aim point dragging with the oval following. Enough to feel the scroll choreography, no more.
- Capture check: confirm a clean MP4 or GIF export path exists (canvas.captureStream + MediaRecorder, or screen capture). LinkedIn needs native video; this must fall out of the page.

## What to bring back

Write findings to `docs/plans/2026-08-13-003-prototype-findings.md` in the repo, then delete the prototype code. The findings file carries:

1. The verdict: stunning, fixable, or dead. One desktop capture and one phone-width screenshot as evidence (commit them next to the findings file).
2. Chosen tech, particle budget, and frame rate on desktop and a throttled mobile profile.
3. The capture pipeline that worked.
4. Anything the prototype taught that should change the chapter design or the sandbox.

## Constraints

- One day of effort, scoped by the charter above. The choreography test was considered and rejected: prototyping all chapters is half the real build wearing a prototype's name tag.
- Fake data throughout. No source hunting, no model code, no reuse of 002 internals.
- Reference reading if needed: `docs/sources/003-scoping/viz-trends.md` (formats and delivery), `docs/sources/003-scoping/data-sources.md` (why no real trajectory data exists anywhere, which is why the simulation is the piece).
