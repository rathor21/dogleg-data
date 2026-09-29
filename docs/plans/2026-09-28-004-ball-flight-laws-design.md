# 004: Ball Flight Laws instructor tool (design)

Date: 2026-09-28 · Status: approved by Sunny · Author: Claude, direction by Sunny

## Context

Sunny wants an interactive teaching tool on Dogleg Data that shows how club path, face angle, and attack angle produce ball flight. Justin Kraft is the first user: he will use it with students, on a phone or iPad at the range and on a laptop or TV in the studio. Students move sliders and watch a TopTracer/GSPro-style tracer fly over a painted driving range. The tracer shows launch, apex, curve, and carry, and a label names the shot (push draw, pull hook, straight fade). A TrackMan-style tile panel shows every number against the ideal band for the chosen club and player. A Tiger Woods "9 windows" mode shows the nine trajectories and the delivery recipe for each.

Sunny's decisions (2026-09-28):
- Ships as **Release 004**: analysis package, short article, and the tool page. Same shape as 002 and 003.
- Player presets: **PGA Tour, LPGA Tour, average amateur**, plus a **club speed slider** that overrides the preset.
- Layout gets **equal weight on phone/iPad and laptop/TV**.

What exploration found:
- The repo has no ball-flight physics in Python or JS. The 003 hero (`site/augusta-12/hero.js:368 arcPoint`) draws a hand-tuned parabola. The flight model gets written from scratch.
- The original pipeline planned a ball-flight piece prompted by the GolfWell episode with Kraft and Benoit (`docs/plans/2026-07-03-analysis-pipeline-design.md:52-68`). It lists TrackMan tour averages and curvature per degree of spin axis as anchors. Benoit's study archive stays off limits without his permission.
- The slot `analysis/004-*` is free. The pipeline doc's 004 ("0 vs 10 vs 20") moves to 005.

## Architecture

One physics engine written twice. A Python reference handles calibration and tests. A JS ES module is the version the page runs. Golden test vectors hold the two in parity, the same Python-to-JS pattern 003 used for `sandboxLookup`.

```
sliders ─► launch.js (delivery → launch) ─► flight.js (3D RK4 ODE) ─► classify.js (shot name)
                                                   │
                         range.js (tracer on fitted art) · views.js (top/side/impact) · tiles.js
```

### Physics model (analysis/004-ball-flight-laws/)

**Delivery inputs:** club, player type, club speed, attack angle, club path, face angle, dynamic loft (advanced slider; defaults per club), and a handedness toggle. Right-handed is the default; lefty mirrors the sign.

**Delivery to launch (`launch.py`)**, D-plane approximations fitted to the published tables:
- Spin loft = dynamic loft − attack angle (the vertical part), combined with face-to-path for the 3D angle.
- Vertical launch = AoA + k_v(club) × (dynamic loft − AoA).
- Horizontal launch = path + k_h(club) × (face − path). k_h runs about 0.85 for driver and 0.75 for wedges, per TrackMan's face-dominance guidance. Fitted per club.
- Ball speed = club speed × smash(spin loft). Smash falls as spin loft rises, fitted across the TrackMan club ladder.
- Spin rate is proportional to ball speed × spin loft, with the coefficient fitted per club class.
- Spin axis tilt = atan2(face − path, dynamic loft − AoA) × a fitted factor. This produces the teaching point that 1° of face-to-path curves a driver more than a wedge.
- Optional "hold swing direction" toggle: path = swing direction − AoA / tan(plane angle). With it on, hitting down pushes path right. This is the attack-angle-to-path coupling instructors teach.

**Flight (`flight.py`):** 3D point-mass ODE with RK4 at dt 0.01 s. Drag and lift coefficients depend on the spin factor S = rω/v, spin decays over the flight, air is standard sea level. Bounce and roll use a simple empirical model keyed to landing angle and speed, and every total-distance number carries the `modeled` badge. The flight takes about 700 steps, cheap enough to rerun on every slider input.

**Shot naming (`classify.py`):** 3 × 3 grid of start line (pull / straight / push) × curve (hook-draw / straight / fade-slice).
- Start threshold: ±1.5° launch direction.
- Curve is scaled to carry: under 2% of carry is straight, 2 to 6% is draw or fade, over 6% is hook or slice.
- Names read like a golfer would say them: "Push draw", "Pull hook", "Straight fade", "Straight". A secondary line gives the finish ("finishes 4 yd right").
- Thresholds live in `data.py` and the methods note, so Justin can argue with them.

**Ideals:**
- Irons and wedges: TrackMan's descent-angle and peak-height targets per club, plus the tour table's launch and spin.
- Driver: optimal launch and spin as a function of club speed and attack angle (TrackMan optimizer charts, Ping fitting charts if public). The ideal band moves as the speed slider moves.

**Nine windows (`windows.py`):** low / mid / high × draw / straight / fade for a 7-iron. A small solver finds the delivery (path, face, AoA, dynamic loft) that hits each window's target peak height and curve. The recipes are model output and carry the `modeled` badge. We do not claim they are Tiger's measured numbers unless a primary source publishes them.

### Data anchors (`docs/sources/004_Source_Log.md`, numbered, with URLs and retrieval dates)

1. TrackMan PGA Tour averages per club (club speed, AoA, ball speed, smash, launch, spin, max height, land angle, carry).
2. TrackMan LPGA Tour averages per club.
3. Average amateur by club. TrackMan publishes amateur and handicap-band numbers; the gate confirms what exists. If a club is missing, the gap gets filled by scaling from the nearest published club and labeled modeled.
4. TrackMan driver optimizer (optimal launch and spin by club speed and AoA) and Ping launch/spin fitting charts. If Ping has no public chart, the source log says so and TrackMan stands alone.
5. TrackMan curvature per degree of spin axis, and face/path start-direction percentages.
6. Tiger's nine-window drill: the primary video or article, cited for the concept only.

### Gate (runs before any UI work)

- **G1 sources:** every anchor above verified at its primary page and logged. Numbers stay provisional until the log exists (standing rule from 002).
- **G2 flight:** given each table's published launch conditions, the model reproduces carry within ±3%, max height within ±3 yd, and land angle within ±2°. It must pass for PGA and LPGA, driver through PW.
- **G3 launch:** given each table's delivery, the model reproduces launch angle within ±1°, spin within ±10%, and ball speed within ±2%.
- **G4 physics sanity:**
  - Face = path gives zero curve.
  - Mirrored inputs give mirrored flights.
  - Curve rises with face-to-path and falls as spin loft rises.
  - Hitting down with the swing direction held moves path right.
  - The golfer sanity cases in Verification below all pass.
- Misses get documented as ADR 0004 (flight model and calibration tolerances), the way ADR 0002 handled 003's gate.

## Visual design

Load `/frontend-design` for the tool UI and `dataviz` for the article figures. Tokens and fonts come from `site/assets/css/site.css`, the source of truth over `.impeccable.md`.

**Range view (hero of the tool):**
- A nano-banana painting of a driving range seen from behind the tee: yardage flags at 50 to 300 yd and target greens, TopTracer mood.
- Green is allowed in this release (Sunny, 2026-09-28), both in the range art and in the UI. Offer daylight and floodlit-dusk candidates; Sunny picks at the contact sheet.
- Follow the 003 art rule (memory: hero art must look real): generate from scratch with a descriptive prompt, pick by looks, show Sunny a contact sheet of 6 to 8 candidates, then fit the camera to the painting. The fit is a homography or affine from painted flag positions, reusing the approach in `analysis/003-augusta-12/art/fit_shapes.py` and `fit_camera.py`.
- Generate a portrait crop for phones, as 003 did with `hero_mobile_crop.png`.

**Tracer rendering (`range.js`):**
- Canvas 2D over the art: a glowing clay tracer with a fading trail, an apex marker labeled with height, a landing marker labeled with carry, and a start-line guide.
- The previous shot stays as a dimmed ghost for comparison.
- Borrow patterns from `site/augusta-12/hero.js`: `readColors` (160), the offscreen trail layers and `strokeTrailSegment` (462), `drawBall` (479), the rAF `tick` (702), the settled render for `prefers-reduced-motion` (851), and `debounce` (950).
- Flight plays in real time with a 2× option. It replays on slider release and draws a live preview line while dragging.

**Secondary views**, as tabs on phone and a row on desktop:
- Top-down curve plot with the start line.
- Side profile with launch angle, apex, and land angle.
- Impact diagram: top view with path arrow, face line, and face-to-path wedge; side view with AoA and dynamic loft. This is the D-plane picture instructors draw on whiteboards.

**TrackMan-style tiles:**
- Tiles: club speed, attack angle, club path, face angle, face to path, dynamic loft, spin loft, ball speed, smash, launch angle, launch direction, spin rate, spin axis, height, land angle, carry, side, curve, total.
- Each tile shows the ideal band. In-band values render in green, out-of-band in clay (green allowed for 004 by Sunny, 2026-09-28).
- Dogleg branding only. TrackMan gets named as a data source, and its UI or logo is never copied.

**Controls:**
- Selectors: club (wedge, short iron, long iron, fairway wood, driver, with a specific club inside each group) and player (PGA / LPGA / Amateur).
- Sliders: speed, path, face, AoA, and dynamic loft behind an "advanced" disclosure.
- Each slider gets ± steppers at 0.5° and keyboard arrows, with thumbs big enough for thumbs.
- Slider CSS and wiring follow `site/augusta-12/tool.html` (`.controls`, `.control`, `.val`, `populateControls` at 550, a single `render()` at 614).

**Modes:**
- **Explore:** sliders.
- **Ideal:** snaps to the preset for club and player.
- **9 Windows:** a 3 × 3 button grid laid out like the window chart. Tapping one animates it and shows its recipe.
- **Compare:** pin a shot, keep adjusting, see both.

**Instructor extras:**
- The URL query string holds the full state, so Justin can text a student a setup.
- A fullscreen presentation mode for a TV.
- "Reset to ideal" button.

**Layout:**
- Landscape iPad and desktop: range view left, about 65% wide; controls and tiles right.
- Phone portrait: range view, then shot label and key tiles, then sliders in a sticky drawer.
- Test at 375, 768, 1024, and 1440+ wide.

## Article (short)

`site/ball-flight/index.html`, about six chapters:
1. Face sets the start line.
2. Face-to-path sets the curve.
3. Attack angle changes launch, spin, and path.
4. The ideal window by club (TrackMan table figures).
5. Tiger's nine windows.
6. How to use the tool with a student.

Prose goes through `sepia`/`humanizer`, following the global writing rules. Justin gets credited or quoted only with his consent. The Benoit data stays untouched.

## Files

New:
- `analysis/004-ball-flight-laws/` with `data.py`, `launch.py`, `flight.py`, `classify.py`, `windows.py`, `calibrate.py`, `export.py`, `tests/`, `requirements.txt`, and `art/` (prompts, candidates, fit script, camera JSON). The venv pattern comes from 002.
- `site/ball-flight/`: `index.html`, `tool.html`, `flight.js` (launch + flight + classify, one ES module shared by the article and the tool), `range.js`, `views.js`, `tool.css`, `data/presets.json`, `data/windows.json`, `data/camera.json`, `data/golden.json`.
- `site/assets/img/004_range.png` and `004_range_mobile.png`, copied in by `export_site_assets.py`, same pattern as 003.
- Docs:
  - `docs/plans/2026-09-28-004-ball-flight-laws-design.md` and `-plan.md`.
  - `docs/sources/004_Source_Log.md`, `004_Caption.md`, `Peer_Review_004_Ball_Flight.md`.
  - `docs/adr/0004-ball-flight-model.md`.
  - `CONTEXT.md` terms: face-to-path, spin loft, spin axis, window.

Edited:
- Tool tab rows (`nav.tabs`) in `site/augusta-12/tool.html`, `site/tee-shot-distance/tool.html`, and `site/fairway-vs-rough/dashboard.html`.
- Home cards in `site/index.html:95-140`.
- Nav "Analyses" and "Tools" links on every page.
- `site/sitemap.xml`, `site/llms.txt`.
- The pipeline doc's renumber note.

## Build order (GitHub issues 004.1 to 004.12, branch `analysis-004-ball-flight`)

| # | Task | Depends on |
|---|---|---|
| 1 | Design spec + source log; verify anchors (G1) | none |
| 2 | Python flight ODE + calibration to launch-condition tables (G2) | 1 |
| 3 | Delivery→launch model + fit (G3), sanity tests (G4), ADR 0004 | 2 |
| 4 | Shot classifier + nine-window solver + ideal bands; export JSON + golden vectors | 3 |
| 5 | `flight.js` port + node parity test run from pytest against `golden.json` | 4 |
| 6 | Range art: prompts, contact sheet to Sunny, pick, camera fit, mobile crop | none (runs parallel to 2 to 5) |
| 7 | Tool shell with `/frontend-design`: layout, controls, tiles, URL state | 5 |
| 8 | Range tracer renderer on fitted art + ghost + reduced motion | 6, 7 |
| 9 | Top/side/impact views, 9 Windows mode, Compare, presentation mode | 7 |
| 10 | Private preview for Justin (Cloudflare preview URL). Sunny sends it; collect feedback | 8, 9 |
| 11 | Article + figures, caption doc, peer review, prose pass | 4, 10 |
| 12 | Site wiring (tabs, home, sitemap, llms.txt), final QA, PR for Sunny to merge | 11 |

Execute with `superpowers:subagent-driven-development`, same as 003. Sunny merges the PR.

## Verification

- **pytest** (`analysis/004-ball-flight-laws/tests/`): G2/G3 tolerance tables for PGA and LPGA, G4 symmetry and monotonicity, classifier boundary cases, the nine windows each landing in their target cell, and JS parity (node evaluates `flight.js` on `golden.json`; outputs match within 0.1 yd and 0.1°).
- **Golfer sanity cases (RH, 7-iron, tour speed):**
  - Face 0 / path 0 gives "Straight".
  - Face +2 / path +5 gives "Push draw" and finishes near the target line.
  - Face −3 / path −3 gives "Pull".
  - Face +3 / path −3 gives "Push slice".
  - Face −4 / path +2 gives "Pull hook".
  - The same face-to-path curves the driver more than a wedge.
  - Higher speed carries farther; more AoA-down lowers the driver's launch and raises its spin.
- **Browser** (preview server `static-site` in `.claude/launch.json`):
  - Drive the sliders with `computer`/`form_input` and confirm the label, tiles, and tracer update.
  - Check the console is clean, the URL state round-trips, all nine windows animate, and reduced motion renders the settled state.
  - Screenshots at 375, 768, 1024, and 1440 wide go to Sunny.
- **Human check:** Sunny, then Justin, sanity-check the numbers and labels on the preview before anything goes public.
