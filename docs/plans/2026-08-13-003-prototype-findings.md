# 003 Prototype Findings: The Spectacle Test

Date: 2026-08-13 · Origin: `/prototype` detour against `2026-08-13-003-prototype-handoff.md` · Status: throwaway code deleted, this file and the two PNGs are the surviving artifacts.

## Revision history

The prototype went through two compositions in one session.

**Rev 1, particle rain.** A top-down stylized hole 12 with 10,000 gaussian-sampled shot dots streaming in per handicap tier, color-coded by outcome. Sunny watched it render live in the browser pane and rejected it on sight before any further polish. The core problem: dots carry no shape information. A dispersion cloud shows where shots land. It says nothing about how the ball got there, and a top-down view flattens the one thing golf broadcast graphics rely on for drama, the arc. The result read as a scatter chart wearing a golf costume.

**Rev 2, shot arcs.** Five curated shots (pin-hunter, safe center, draw, fade, an under-clubbed ball that finds Rae's Creek) fly from tee to green as animated arcs in an elevated three-quarter perspective, staggered so the eye follows one flight at a time. This is the version scored below.

## Verdict: fixable

Rev 2 is a real improvement on the mechanism Sunny rejected, and it is not yet the thing that stops a scroll on its own.

**Composition.** The three-quarter view behind the tee reads as a golf hole on first look: tee box in the foreground, Rae's Creek crossing the fairway, three bunkers, the shallow green running diagonal front-left to back-right, three pins. The converging fairway edges sell depth without needing a real 3D engine, the whole thing is 2D perspective math (see Tech below). Where it falls short: the five arcs all launch from the tee, which is correct golf, so the composition is a tight fan of near-parallel lines rather than a wide spread. It reads as "five shots down one hole," which is accurate, but a wider stance, more visual separation between the arcs' launch angles, or a slight camera pull-back would make the fan itself more of a shape and less of a sheaf.

**Motion.** The stagger works. Launching one shot every 0.9 to 1.1 seconds gives a reader's eye time to track a single ball before the next one starts, rather than five things happening at once. The parabolic arc plus a sine-based bend for the draw and fade gives each shot a distinct silhouette even before it lands. What is missing is a sense of impact: the ball stops and a marker appears, full stop. A small squash-and-settle on landing, or a one-frame dust or splash puff at the outcome, would sell the moment better than a flat marker swap.

**Color.** Every trail carries its eventual outcome's color starting at launch, so the color story is legible while the ball is still in the air. This came from a real bug: the first pass colored every trail the same ink tone and left the landing marker as the only colored element, so a viewer had to wait for each shot to finish before learning anything from color. Outcome colors reuse the brand's fixed palette (ink, clay, blue, oxblood), which holds up, though bunker (clay) and short-sided (oxblood) sit close enough in hue that they blend at a glance. Worth a harder look before this goes further: pull short-sided toward a higher-contrast value. A different hue alone does not carry enough separation.

**Net:** the mechanism is sound and cheap to run (see frame rate below), the reading order works, and the outcome color-coding lands. It needs a second pass on landing impact and on widening the arc fan before it is the thing that makes someone stop scrolling. The verdict is fixable.

## Perspective choice

Built: an elevated three-quarter view from behind the tee, looking down the fairway, the same camera logic broadcast tracer graphics use. Chosen over a side profile (camera parallel to the fairway, hole receding left-to-right or right-to-left) because the three-quarter view sells both lateral spread (draw vs. fade vs. pin-hunter) and depth (short vs. full carry) in one frame, where a side profile would compress the lateral spread into almost nothing. The side profile was not built. If the three-quarter view stalls on the widen-the-fan problem above, the side profile is the fallback worth prototyping next; it trades depth legibility for lateral clarity and might read better at phone width, where the three-quarter view's fan has the least room to spread.

## Tech and performance

Canvas 2D, no WebGL, no SVG. The tech ladder in the charter assumed particle count would be the bottleneck; it was not, at any point in this session.

- **Rev 1 (10,000 dots):** stable 120 fps on this machine's display (which refreshes at 120Hz; the number is a ceiling, not a measurement of headroom). 10,000 shots streamed and rendered in under a second. Canvas 2D never came close to choking, so WebGL was never touched and SVG was never tried.
- **Rev 2 (5 arcs plus a subtle landing scatter, about 180 decorative dots total):** also a stable 120 fps, expected since it draws far less per frame than rev 1 did.
- **CPU throttling:** not tested. The tool stack available in this session (Chrome DevTools Protocol screenshot flows and the browser preview pane) did not expose a CPU throttling control, and adding one sat outside the scope of a one-day prototype. 10,000 unoptimized dots already ran at the display ceiling, so a throttled mobile CPU is not expected to bottleneck rev 2's much lighter draw call count. That is still an assumption, not a measurement, and it needs a real test (a physical mid-tier phone, or `--cpu-throttling-rate` through a proper Lighthouse/DevTools run) before the real build ships.

**An engineering finding, separate from the design one:** headless screenshot tools that advance virtual time (`chrome --headless --screenshot --virtual-time-budget=`) do not advance a `requestAnimationFrame`-driven animation in step with the requested budget. Two captures taken seconds apart with different budgets landed on the same near-zero animation frame. The fix was adding a `?settled=1` query parameter that skips straight to the animation's resting state, and a `window.__phaseComplete` flag a real browser automation tool (Puppeteer, driving the actual installed Chrome) can poll for. Both evidence screenshots in this findings file were captured that way. If the real build ever needs automated visual regression tests or scripted social-video capture, build the "jump to a known state" hook in from day one instead of discovering the need under deadline.

## Capture pipeline

`canvas.captureStream(30)` plus `MediaRecorder` works end to end. The visible canvas is itself a composite (three offscreen layers, a base hole drawn once, accumulated shot trails, and a per-frame overlay, flattened into one visible canvas every frame via `drawImage`), and `captureStream` on that single composited canvas captures the full picture. No separate compositing step is needed for the capture itself.

- Codec negotiated: `video/webm;codecs=vp9` (first supported candidate in this Chrome build; `vp8` and a bare `video/mp4` were offered as fallbacks and went unused).
- A 2-second test recording of rev 2 produced a 67KB WebM blob. The same test against rev 1's much busier 10,000-dot frame produced a 528KB blob, a useful data point on how much scene complexity costs in output size, beyond render time.
- **Caveat for LinkedIn:** LinkedIn wants native MP4/H.264. Chrome's `MediaRecorder` did not offer `video/mp4` as a working candidate here; it produced WebM. The real pipeline needs a transcode step (`ffmpeg -i capture.webm capture.mp4`) between the browser capture and the upload. That step is cheap and well understood. Do not assume the browser hands over a LinkedIn-ready file on its own.

## What should change in the chapter design or the sandbox

1. **Widen the arc fan.** All five shots share a tee, which is correct golf, but the resulting close bundle of trails is the single biggest thing standing between "fixable" and "stunning." Worth testing: staggering the tee position shot to shot (different players use different spots on a real tee box), or pulling the camera back so the fan has more room to spread before it reaches the green.
2. **Give landings weight.** A marker swap is not an impact. Even a two-frame squash or a small radial puff at outcome time would sell the moment of contact far better than the current instant swap.
3. **Separate bunker from short-sided by more than hue.** Same fix as the tier-color note in the brand spec: don't rely on hue alone when two hues sit close in value. Add a value or shape difference on top of the dashed-and-starred convention the brand already uses for modeled data.
4. **Build the "jump to a resting state" hook into the real piece from the start.** It is what made reliable, scripted screenshots possible here, and the real build will want the same thing for QA and for any automated social-video export.
5. **Test on a real throttled or low-end device before assuming Canvas 2D headroom holds on mobile.** Nothing in this session measured that; the 10,000-dot stress test speaks to desktop headroom, mobile stays untested.
6. **The side-profile camera is worth a half-day spike**, to see whether it reads better than the three-quarter view at phone width, where the current composition's lateral spread has the least room to work with.

## Evidence

- Desktop, 1440×900, settled state (all five shots landed, scroll-driven sixth ball not yet engaged): [`assets/003-proto-desktop.png`](assets/003-proto-desktop.png)
- Phone width, 375×812, same settled state: [`assets/003-proto-mobile.png`](assets/003-proto-mobile.png)

Both captures use the `?settled=1` deterministic state described above rather than an arbitrary mid-animation frame, so what's in the PNG is the same resting composition a reader would see a few seconds after the hero loads, before they've scrolled.
