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
- `?chapter=N&step=M`: the contract this script is built against for the eight chapter cards, once `site/augusta-12`'s scrollytelling chapters (issue #13) land. Each chapter is expected to freeze to a settled figure sized for a 1080x1350 capture and set `window.__phaseComplete`.

## Chapter cards: stand-in until #13 lands

`cards.json` lists the real target: hero, `chapter=1` through `chapter=8`,
then `shot=5`. As of this script, `site/augusta-12`'s chapters section does
not exist yet (issue #13 is still open). The `?chapter=N&step=1` URLs just
render the ordinary hero animation, with nothing on the page matching a
chapter card container. For each chapter entry the script:

1. Navigates to the chapter URL and waits for `__phaseComplete`.
2. Looks for a chapter card element (`[data-social-card]`, `.capture-card`, `.chapter-card`, or `.chapter-figure`, in that order). `.capture-card` is the class `site/augusta-12/chapters.js` already builds for `?chapter=N&step=M` as of this writing, the others are fallback guesses in case that contract shifts before `index.html` wires the chapters section in.
3. If none of those exist, logs a note and falls back to that card's `standinUrl` in `cards.json` (`?settled=1&shot=N`, cycling `N` 1 through 5), capturing the ordinary hero-clip screenshot instead.

As of this writing `site/augusta-12/index.html` does not yet load
`chapters.js`/`chapters.css` or carry any `.chapter[data-chapter]` markup
(issue #13 in progress), so every chapter card still falls back to its
stand-in. Once the chapters section is wired into the page, re-run the
command with no changes needed. The manifest and card list this script
prints both state which cards used the stand-in.

## Other notes

- `hero` and `shot-5` cards use a plain page clip (`page.screenshot({ clip: {0,0,1080,1350} })`) instead of an element screenshot. The hero section's own rendered box is narrower than 1080px (it sits inside the article's max-width column) and shorter than 1350px.
- Chapter cards get captured as element screenshots, then scaled to the full 1080x1350 with ffmpeg if they come back at a different size. `chapters.css`'s `.capture-card` lays the card out at its own max-width (420px as of this writing) holding the right 4:5 aspect ratio rather than filling the viewport, so the raw element screenshot lands at that smaller native size. Scaling up after the fact means this script does not have to track that CSS value.
- `carousel.pdf` is built with a short inline Python snippet (Pillow, already on this machine) instead of a new dependency. `ffmpeg` has no clean multi-page PDF muxer for arbitrary PNGs. If Pillow is unavailable the script skips the PDF, logs why, and still leaves the individual card PNGs in place.
- Requires `ffmpeg` and `ffprobe` at `/opt/homebrew/bin/`, Chrome at `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`, and `npm install` run once at the repo root (installs `puppeteer-core` as a dev dependency, no Chromium download).
