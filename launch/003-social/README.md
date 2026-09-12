# 003 social export

One command builds the LinkedIn assets for the Augusta 12 release from the
article page's deterministic settled-state hooks. No manual screen recording,
no manual cropping.

## Run it

From the repo root:

```
node launch/003-social/export.mjs
```

Options:

- `--port 8946`: port for the static server this script spawns (`npx serve site -l <port>`). Default 8946.
- `--out launch/003-social/out`: output directory. Default `launch/003-social/out` next to this script.
- `--url http://host:port`: point at a server you already have running (skips spawning and stopping one). The article page must be served at `<url>/augusta-12/`.

The script starts the static server itself, drives a real headless Chrome
through Puppeteer, writes every output, then shuts the server down. Nothing
about it needs `site/` deployed anywhere, it runs the same static files the
site ships.

## What it produces

In the output directory:

- `hero.webm`: raw capture of the hero canvas, VP9 (or VP8 if VP9 is unavailable).
- `hero.mp4`: the same clip transcoded to H.264, `yuv420p`, 30 fps, even dimensions, `-movflags +faststart`, CRF 20.
- `hero_portrait.mp4`: a 1080x1350 (4:5) portrait cut of the same clip, center-cropped from the 16:9 source.
- `card_00_hero.png` through `card_09_shot-5.png`: one 1080x1350 PNG per entry in `cards.json`.
- `carousel.pdf`: the card PNGs bundled into one PDF, page order matching the card numbers.

## LinkedIn specs this targets

- Feed video: MP4, H.264 video codec, well under LinkedIn's 200 MB cap (these clips run under 2 MB). 4:5 portrait (`hero_portrait.mp4`) is the pick for feed. The 16:9 cut (`hero.mp4`) covers anywhere landscape reads better.
- Document carousel: PDF, one page per card, 1080x1350 (4:5) pages. LinkedIn's carousel post type takes a PDF upload, not individual images, hence `carousel.pdf`.

## The hooks it relies on

- `?settled=1` on `/augusta-12/`: draws the hero in its final composition on the spot and sets `window.__phaseComplete = true` once drawn.
- `?shot=N` (1-5): same, but settled up to shot N. Used for `card_09_shot-5.png` and as the carousel's stand-in cards (see below).
- `window.__phaseComplete`: the script polls this after every navigation, 20 second timeout, before it takes a screenshot.
- The hero canvas is `#hero-canvas` inside `#hero-scene`. The replay control is `#hero-replay`.
- `canvas.captureStream(30)` plus `MediaRecorder` capture the hero animation. The recorder gets armed, then `#hero-replay` gets clicked so the recording starts before the first shot launches instead of mid-sequence. Headless Chrome stops compositing the canvas the instant it stops repainting, so once `__phaseComplete` flips true the script forces a harmless zero-alpha 1x1 redraw plus `track.requestFrame()` on a 33ms tick for 1.5 seconds. Without that, the recording stops cold with no hold on the settled frame.
- `?chapter=N&step=M`: `site/augusta-12`'s scrollytelling chapters (issue #13) landed and this is their deterministic capture hook. Each chapter with a step-driven figure freezes to a settled `.capture-card`, laid out at the real 1080x1350 CSS px `chapters.css` gives it (issue #16), and sets `window.__phaseComplete`.

## Chapter cards: six of eight capture for real, two use the stand-in by design

`cards.json` lists hero, `chapter=1` through `chapter=8`, then `shot=5`. For
each chapter entry the script:

1. Navigates to the chapter URL and waits for `__phaseComplete`.
2. Checks whether `chapters.js` actually engaged capture mode (`document.body.classList.contains("capture-mode")`, set only inside its own `buildCaptureCard`) before looking for a card element (`[data-social-card]`, `.capture-card`, `.chapter-card`, or `.chapter-figure`, in that order). Gating on capture-mode first matters: without it, a chapter with no step-driven figure still has *some* `.chapter-figure` in the page (whichever chapter's inline figure happens to render first in document order), and this script would screenshot and force-resize the wrong chapter's art instead of recognizing there was no card to capture.
3. If capture mode never engaged, logs a note and falls back to that card's `standinUrl` in `cards.json` (`?settled=1&shot=N`, cycling `N` 1 through 5), capturing the ordinary hero-clip screenshot instead.

Chapters 1 through 5 and 7 have a `.step`-driven figure and capture for
real. Chapters 6 (a plain prose chapter, the 2019 final-round writeup) and 8
("the move," a summary table, not a scrolly figure) have no step/figure to
capture and always use their stand-in -- that is the correct, expected
outcome for those two, not a sign anything is missing. The manifest and
card list this script prints both state which cards used the stand-in.

## Other notes

- `hero` and `shot-5` cards use a plain page clip (`page.screenshot({ clip: {0,0,1080,1350} })`) instead of an element screenshot. The hero section's own rendered box is narrower than 1080px (it sits inside the article's max-width column) and shorter than 1350px.
- Chapter cards get captured as element screenshots. `chapters.css`'s `.capture-card` lays the card out at the real 1080x1350 CSS px target (fixed `width`/`height`, not just an `aspect-ratio` a flex column could grow past under long caption text), so the raw element screenshot at `deviceScaleFactor: 1` already lands at the exact target size with no upscale needed -- upscaling a smaller card, which this pipeline did before issue #16, softened the type. `ensureCardDimensions` stays as a safety net: it no-ops when the size already matches and only resizes (with a loud warning) if a future `chapters.css` change drifts the card's own size away from 1080x1350.
- The hero capture runs at `deviceScaleFactor: 2` (issue #16), not 1: the hero canvas renders at its CSS width times device pixel ratio (`site/augusta-12/hero.js`), and at `dpr: 1` that canvas is only about 1132px wide, the whole source for `hero_portrait.mp4`'s 1080px-wide crop. At `dpr: 2` the source is about 2264px wide, comfortably above the 1080px crop target instead of being upscaled into it.
- `carousel.pdf` is built with a short inline Python snippet (Pillow, already on this machine) instead of a new dependency. `ffmpeg` has no clean multi-page PDF muxer for arbitrary PNGs. If Pillow is unavailable the script skips the PDF, logs why, and still leaves the individual card PNGs in place.
- Requires `ffmpeg` and `ffprobe` at `/opt/homebrew/bin/`, Chrome at `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`, and `npm install` run once at the repo root (installs `puppeteer-core` as a dev dependency, no Chromium download).
