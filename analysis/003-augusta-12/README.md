# 003: Augusta 12 aim-point piece

Release 003 asks where an amateur golfer should aim an approach shot into
Augusta National's 12th hole, across five handicap tiers, three named pins,
and calm or windy conditions. The package builds an analytic expected-score
model from published proximity and short-game data, searches for the
optimal aim point at every tier/pin/wind combination, validates the model
against a Monte Carlo simulation and against PGA Tour scoring history, and
exports the result as a browser-facing sandbox and a hero animation for the
site.

## Modules

**data.py** holds every numeric input the model uses: proximity and
dispersion figures by handicap tier, the hole's geometry (pins, green
shape, bunkers, the creek), wind effects, and short-game pricing (putting,
up-and-down rates, penalty strokes, pitch-over-water dunk rates). Each constant names its source anchor
in `docs/sources/003_Source_Log.md` and states whether it is published
directly, computed from a published figure, or modeled with a disclosed
sensitivity range. Nothing in this file comes from memory or invention
without that label.

**model.py** turns a dispersion oval into an expected score. `oval_for_tier`
splits a tier's isotropic miss radius into distance and line axes using the
amateur anisotropy ratio. `region_at` classifies a landing point into an
outcome region (green, bunker, a finite creek band, the fairway short of
that band, rough, or the ledge behind the back bunkers) using the hole's
diagonal geometry. Rae's Creek is `data.CREEK_WIDTH_YD` plus
`data.BANK_ROLLBACK_YD` wide, not every yard of short miss back to the tee;
short of that band is `short_fairway`, a pitch that has to carry the creek
back onto the green. That pitch itself can miss into the water: `data.
PITCH_OVER_WATER_DUNK_PCT` sets the share of these pitches, by tier, that
find the creek instead of clearing it, priced as a mixture of the plain
recovery leg and a drop-and-replay penalty, not a flat recovery price with
no water risk at all. `score_for_oval` integrates a truncated
bivariate normal over those regions on a product grid, pricing each
region's outcome in expected strokes. `expected_score` is the public,
tier-and-wind-aware wrapper other modules call.

**tour.py** repeats the same construction for the PGA Tour tier, using its
own anisotropy ratio and proximity anchor, so the piece can show where the
pros play this hole against where an amateur should.

**optimizer.py** searches the aim plane around each pin for the lateral
offset and carry adjustment that minimizes `model.expected_score`, at an
elevated integration resolution for verdict-grade numbers. `verdict_label`
turns the gap between the optimal aim and aiming straight at the pin into
"attack," "bail," or "either works," using a threshold set above the
model's own truncation noise. `flip_set` checks which verdicts change
across the anisotropy and green-depth sensitivity ranges. `published_move`
(issue #13) runs the same search a second time with the carry axis clamped
to `PUBLISHED_CARRY_RANGE_YD` (10 yd, the "full shot" window a golfer
reaches by picking a club and swinging normally), alongside the ordinary
unclamped search, and reports the strokes the unclamped ("strict") optimum
claims to save over the clamped one as `layup_edge_strokes` (floored at
zero; the two independent searches are not exhaustive and can disagree by
search noise on this surface's known shallow-valley stretches). The
Sunday-pin verdicts in `outputs/003_results.csv` sometimes want a deeper
layup than a single club change explains; `published_move` is how the
article discloses that gap instead of silently publishing the layup.

**montecarlo.py** is a peer-review harness, not a published number source.
It samples from the exact same distributions the analytic model integrates
and prices each sample through the same region and stroke formulas, so
agreement between the two is a check on the grid integration, not
independent evidence. A season-length Tour simulation also checks the
model against the hole's published scoring history.

**build_outputs.py** runs the optimizer across every tier, pin, and wind
combination and writes `outputs/003_results.csv`, the single table every
published number in the article must match exactly. It also runs
`optimizer.published_move` across the same grid and writes
`outputs/003_moves.csv` (issue #13), the "full shot" aim the chapters and
"The move" section actually quote, alongside the strict optimum and the
layup edge between them. It then calls `export.main()` to build the
browser-facing export seam.

**export.py** builds three JSON files from the two CSVs and the model: a
sandbox grid the browser interpolates for any aim point with no server
round trip, an animation manifest that supplies the hero animation's
camera, geometry, and five curated shot arcs, and a small chapters blob
(`outputs/003_chapters.json`, issue #13, well under 60 KB) that carries
per tier/pin/wind dispersion sigmas, the published and strict aims, and
water/green probabilities at both the pin and the published aim, for the
scrollytelling chapters' own top-down figures. The grid builder mirrors
`model.score_for_oval`'s math with numpy broadcasting instead of Python
loops, so building all 30 tier/pin/wind grids takes seconds; a slower,
line-by-line mirror of the same formulas lives alongside it and the test
suite checks the two against each other and against `model.expected_score`
directly.

**export_site_assets.py** copies the two export.py outputs into
`site/augusta-12/data/` and the hero art into `site/assets/img/`.

**art/sketch.py** builds the model's own yard-space geometry (every hazard
boundary comes straight from `model.py`'s functions, plus a handful of
art-only constants such as the tee box footprint) that `export.py`'s
`geometry_yd` block and the accepted hero art both trace back to. It no
longer supplies the manifest's pixel camera: through round five, its own
piecewise projection stood in for a camera fit to the art, but nano-banana
art fit to that stylized camera kept reading as a diagram, not Golden
Bell. Round six (issue #11) inverted the relationship: `art/fit_tps.py`
fits a thin-plate spline (TPS) camera to the accepted painted art
(`art/hero.png`, a nano-banana repaint with no sketch reference at all),
mapping model yards to that art's own pixels at a set of hand-picked and
detected correspondences, registering each of them exactly by
construction. `art/camera_tps.json` is the committed result (control
points, target pixels, RBF weights, affine terms, the mobile crop offset,
and the trusted depth limit); `export.py`'s `camera_block()` reads it
directly, and `landmarks_px` in the manifest is that same fitted
correspondence list, not a sketch.py coordinate dump. See
`art/README.md`'s "Round six, integration" section for the fit, the
residual tables, and why `r6_4` won over `r6_3`.

## Build sequence

```
python3 build_outputs.py          # writes outputs/003_results.csv, then calls export.main()
python3 export_site_assets.py     # copies the two JSON files and the hero art into site/
```

Run `pytest` from this directory to check the full suite, or `pytest
tests/test_export.py` for just the export seam (session-scoped, under ten
seconds).

## Schemas at a glance

**`outputs/003_sandbox_grids.json`** (`dogleg-003-sandbox-grids/1`): a
1-yard grid of lateral offset (-20 to 20) by carry adjustment (-20 to 45),
one cell per tier/pin/wind combination. Each cell carries `score` and
`p_water` grids (expected strokes and creek probability at every node,
4 decimals), an `optimum` block copied exactly from the results CSV, and
the tier's modeled constants with their sensitivity ranges.
`export.sandbox_lookup` bilinearly interpolates between the four nodes
surrounding an arbitrary aim point; the browser implements the identical
formula against the same file.

**`outputs/003_manifest.json`** (`dogleg-003-manifest/1`): the camera
block needed to reproduce `art/camera_tps.json`'s thin-plate-spline fit in
JavaScript (control points, target pixels, RBF weights, affine terms,
mobile crop offset, trusted depth limit -- see `art/README.md`, round six),
the hole's geometry in model yards, five curated shot arcs (aim, tee,
landing, and outcome), and a 1,000-point scatter per shot's own scenario
for the animation's background cloud. Each shot's landing is the medoid of
its outcome class, not a random member of it: `export.py` draws 2,000
seeded samples at the shot's own tier, pin, wind, and aim, classifies each
one, then keeps the landing nearest the centroid of the class the shot is
meant to show. `safe_center` and `draw` are pinned to the `green` class and
`under_clubbed` to `water`; `pin_hunter` and `fade` have no fixed class,
since aiming at a pin can miss several ways, so their class is whichever
non-green outcome came up most often among that shot's own samples. The
manifest records the seed, sample count, in-class count, sample index,
class frequencies, and a `selection_rule` string, so the pick is
reproducible and disclosed rather than asserted.

**`outputs/003_chapters.json`** (`dogleg-003-chapters/1`, issue #13): the
scrollytelling chapters' own data contract, one cell per tier/pin/wind
combination keyed the same way as the sandbox grids. Each cell carries the
dispersion oval (`sigma_d_yd`/`sigma_l_yd`, wind-inflated where applicable,
plus the calm-air values for comparison), the published full-shot `aim`
and the unclamped `strict_aim` (lateral offset, carry adjustment, and
score), the at-pin and center-aim scores and delta already in
`outputs/003_moves.csv`, the layup edge and its tossup flag, and
`p_water`/`p_green` computed at both the pin and the published aim via
`export.score_and_region_probs`. The file also carries `geometry_yd`
(identical to the manifest's own block), `pins`, `wind`, and the same
`modeled` sensitivity-range list `build_sandbox_grids` exports, so the
chapters page never needs to cross-reference the manifest or the sandbox
grids for its own top-down figures. Kept well under a 60 KB budget
(~26 KB as of this pass); `export.main()` warns if a future change pushes
it over.
