# 002 — How Far Do You Need to Hit It?

Analysis package for Dogleg Data release 002. Spec:
docs/plans/2026-07-11-002-tee-shot-distance-design.md

## Order of operations
1. `docs/sources/002_Source_Log.md` is the verification gate. `data.py`
   values come from that log only.
2. `pytest` from this directory runs all model and consistency tests.
3. `python build_outputs.py` writes `outputs/002_results.csv` and
   `outputs/tool_data.json`.
4. `python chart1.py` .. `python chart5.py` write PNGs to `outputs/`
   (site copies happen in the site tasks).

## Modeling stance
Own-tier baseline: strokes gained 0 = you played the hole like a typical
golfer at your handicap. Full-hole expected strokes, drive dispersion ->
lie odds -> approach expected strokes to hole-out. Tier 30 and all
between-anchor interpolation are MODELED and labeled.

## Environment
Use the package venv: `.venv/bin/python -m pytest`. Create it with
`/opt/homebrew/bin/python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
