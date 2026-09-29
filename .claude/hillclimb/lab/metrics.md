# Ball flight lab: metrics

30 cases (`eval/lab/cases.json`), each a teaching moment on one device: phone portrait 390x844, phone landscape 844x390, iPad 1024x768 and 768x1024, laptop 1440x900, TV 1920x1080, and one 4K TV. Modes covered: Explore, 9 Windows, Compare, Present. Split: random, stratified by viewport class (`tags[0]`), seed 20260929, 18 train and 12 test (`_state.json`).

The headline is `design`. The rest are guardrails and diagnostics.

## Judge metrics (a subagent grades one screenshot per case against `eval/lab/rubric.md`)

| id | label | what it means | better |
|----|-------|---------------|--------|
| design | Design | Mean of the eight binary claims below, averaged over judge reps and then over cases. 1.0 means every claim passes on every case. | higher |
| c1 | Readable | Shot name and where it finishes are readable at this viewport without zooming, at the distance the device implies. | higher |
| c2 | Flight | The ball flight is clearly visible and its curve direction (left, right, straight) can be told. | higher |
| c3 | Numbers | The numbers the scenario's teaching point needs are visible without scrolling. | higher |
| c4 | Controls | The controls the scenario needs are visible or one obvious, labeled tap away. | higher |
| c5 | No defects | No overlap, clipping, covered elements, broken layout or placeholder areas. | higher |
| c6 | Hierarchy | One clear focal point: the shot and its name first, the rest subordinate, no clutter. | higher |
| c7 | Teach fit | A coach could use this exact screen for the scenario without explaining the interface. | higher |
| c8 | Polish | Type, spacing, alignment and color look consistent and finished. | higher |

Each claim is a mean over judge reps (0 to 1 per case). Judge noise: run at least two reps and read the inter-rep agreement that `merge.mjs` prints. The judge sees the PNG and the scenario text only, never the programmatic numbers. `all_pass` (derived, not in the metric list) is 1 when a case's design equals 1.

## Programmatic metrics (measured in Chrome by `eval/lab/run.mjs`, screenshot pass with prefers-reduced-motion: reduce)

| id | label | definition | better |
|----|-------|------------|--------|
| console_errors | Console errs | Count of console errors, uncaught page errors, failed requests and HTTP 4xx/5xx responses during load and the case's actions. Third-party font requests count. | lower |
| overflow_x | Overflow X | 1 when the page scrolls sideways (max of documentElement and body scrollWidth is larger than clientWidth), else 0. | lower |
| min_font_px | Min font px | Smallest computed font-size among text nodes that are rendered, at least 2 px across, inside the viewport and not covered or clipped (checked with elementFromPoint at the text's center). Text drawn on the range canvas is not measured. | higher |
| small_targets | Small targets | Count of rendered, non-inert interactive elements on the whole page (links outside running text, buttons, inputs, selects, summary, role radio/tab/button) whose hit box is under 44x44 CSS px on mobile viewports (phone, phone landscape, tablet) and under 24x24 elsewhere. A checkbox counts with its label. The first ten offenders are in `meta.small_target_samples`. | lower |
| axe_serious | Axe serious | Number of axe-core rules violated with impact serious or critical (rules, not nodes), run on the final screen. Details in `meta.axe_serious`. | lower |
| above_fold_ok | Above fold | 1 when both the shot label and the range canvas intersect the viewport, measured before the first scrollTo action (or after all actions when there is no scroll). Fractions are in `meta.label_in_view` and `meta.canvas_in_view`. Not in the metric list, kept in the row. | higher |

## Performance metrics (separate pass, motion on, fresh incognito context, cache off)

| id | label | definition | better |
|----|-------|------------|--------|
| load_ms | Load ms | Milliseconds from navigation start until the shot label first has text (a MutationObserver installed before any script runs). | lower |
| input_p50_ms, input_p95_ms | Input p95 ms | 20 synthetic `input` events on the face slider, values spread between -6 and +6 degrees, 70 ms apart, after the opening flight has finished. Each sample runs from dispatch to the second animation frame after it (double rAF), so the floor on a 60 Hz display is about 17 to 33 ms. p50 and p95 over the 20 samples. | lower |
| js_kb | JS KB | Transferred (gzip) bytes of scripts, from CDP `encodedDataLength`. The local server gzips text files as the CDN does. | lower |
| total_kb | Total KB | Transferred bytes of everything, including the range art and Google Fonts. Kept in the row, not in the metric list. | lower |
| latency_s | Load | `load_ms / 1000`, shown as the perf column in the report. | lower |

Perf caveats: the perf pass runs one page at a time (`--perf-conc 1`) so timings do not fight each other. Numbers come from a headless Chrome on the developer's Mac with no CPU throttling unless `--cpu N` is passed. Compare variants, not absolute values. Input latency is dominated by the double-rAF floor; a regression shows as p95 well above 33 ms.

## Guardrails for the hillclimb

`goal.hold` lists `console_errors`, `overflow_x`, `axe_serious`, `input_p95_ms` and `load_ms`: a variant that raises `design` while making any of them worse does not count as a win.

## Files

- `baseline/results.jsonl`: one row per case. `grade` holds every number. After `merge.mjs`, `grade` also holds `design`, `c1`..`c8`, `all_pass`, and `explanation` holds the judge's reason per claim from rep 0.
- `baseline/shots/<id>.png`: viewport screenshot the judge sees. `<id>_full.jpg`: full page, JPEG q70 (gitignored).
- `baseline/errors.jsonl`: failed attempts with a class (`timeout`, `app_error`, `action_failed`, `perf_failed`, `shots_failed`).
- `traces/<id>_rep0.json`: user turn (scenario and focus, screenshot) and assistant turn (rendered shot label and key tiles as text).
- `calibration/null_blank.png`, `calibration/bad_hidden_label.png`: images the judge must fail, to check the grader is not lenient.
