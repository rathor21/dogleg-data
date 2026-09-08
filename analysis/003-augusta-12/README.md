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
up-and-down rates, penalty strokes). Each constant names its source anchor
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
short of that band is `short_fairway`, a pitch over the water priced as a
recovery leg, not a penalty drop. `score_for_oval` integrates a truncated
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
across the anisotropy and green-depth sensitivity ranges.

**montecarlo.py** is a peer-review harness, not a published number source.
It samples from the exact same distributions the analytic model integrates
and prices each sample through the same region and stroke formulas, so
agreement between the two is a check on the grid integration, not
independent evidence. A season-length Tour simulation also checks the
model against the hole's published scoring history.

**build_outputs.py** runs the optimizer across every tier, pin, and wind
combination and writes `outputs/003_results.csv`, the single table every
published number in the article must match exactly. It then calls
`export.main()` to build the browser-facing export seam.

**export.py** builds two JSON files from the CSV and the model: a sandbox
grid the browser interpolates for any aim point with no server round trip,
and an animation manifest that supplies the hero animation's camera,
geometry, and five curated shot arcs. Its grid builder mirrors
`model.score_for_oval`'s math with numpy broadcasting instead of Python
loops, so building all 30 tier/pin/wind grids takes seconds; a slower,
line-by-line mirror of the same formulas lives alongside it and the test
suite checks the two against each other and against `model.expected_score`
directly.

**export_site_assets.py** copies the two export.py outputs into
`site/augusta-12/data/` and the hero art into `site/assets/img/`.

**art/sketch.py** builds the geometry sketch that stands in for camera
registration: every hazard boundary comes from `model.py`'s own functions,
with a handful of art-only constants (tee box footprint; creek width now
reads `data.CREEK_WIDTH_YD` directly rather than carrying its own figure)
and the pixel-space camera projection documented in its module docstring.
`export.py`'s manifest reads this projection's constants directly so the
site's JavaScript can reproduce it.

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
constants needed to reproduce `art/sketch.py`'s projection in JavaScript,
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
