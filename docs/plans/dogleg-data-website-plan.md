# Dogleg Data Website — Implementation Plan

Goal: launch-ready static website for Dogleg Data with the Fairway vs. Rough analysis as post #1, the interactive dashboard integrated, brand images placed, and SEO in place.

## Constraints and context

- Static HTML/CSS, no build step, no frameworks. Chart.js via CDN only inside the dashboard page (already built).
- Design system: `.impeccable.md` in project root is law. The canonical reference implementation is `site/fairway-vs-rough/dashboard.html` (already fully branded). Match its tokens, header pattern, and detailing exactly.
- Voice: stop-slop rules apply to all copy (no em dashes, no -ly adverbs, no "not X, it's Y", active voice, no hype words). Every data claim keeps its source. Every modeled number keeps its "modeled" label.
- Canonical domain placeholder: `https://doglegdata.com` (not yet registered; flagged for Sunny before deploy).
- Working directory: `/Users/sunny/Documents/Claude/Projects/Golf Analytics` (git repo, main branch).

## Assets already in place (do not regenerate)

- `site/assets/img/chart1..5*.png` — five branded charts
- `site/assets/brand/mark.svg` — dogleg mark (ink stroke, clay dot), inline-able
- `site/assets/brand/favicon.svg` — mark on ink circle, cream stroke
- `site/assets/brand/apple-touch-icon.png`, `avatar-512.png`, `avatar-square.jpg`
- `site/assets/brand/og-banner.jpg` — 1024×537 cream banner (badge + tagline + hole diagram)
- `site/assets/brand/mascot-run.png` — running dachshund, transparent background, 344×175
- `site/fairway-vs-rough/dashboard.html` — self-contained interactive dashboard, already branded

## Site map

```
site/
  index.html                     Home
  fairway-vs-rough/index.html    Post #1 (the launch analysis)
  fairway-vs-rough/dashboard.html  Interactive dashboard (exists)
  about/index.html               About / method
  404.html                       Not-found page (mascot moment)
  assets/css/site.css            Shared design system
  assets/img/, assets/brand/     (exist)
  robots.txt, sitemap.xml, llms.txt
```

All internal links relative so the site works from file:// and any host.

---

## Task 1 — Design system CSS + Home page

**Files:** `site/assets/css/site.css`, `site/index.html`

Build the shared stylesheet from the dashboard's CSS variables and patterns (copy the `:root` tokens verbatim from `.impeccable.md`). Include: base/reset, header/nav pattern (mark + FRAUNCES-900 wordmark + mono tagline chip + nav links), footer pattern (double-rule top, mascot image right, boilerplate, social links, mono source-line style copyright), cards, buttons (pill, clay), figure/source-line styles, "modeled" badge (dashed oxblood pill, mono 10px), responsive breakpoints (760px), :focus-visible, prefers-reduced-motion.

Home page sections:
1. **Hero:** display headline in Fraunces 900 (about testing golf's conventional wisdom with real data for normal golfers), subhead naming the audience (8-to-30 handicap), two CTAs: "Read the first analysis" (clay pill → post) and "Run your own numbers" (outline → dashboard). Include the mark large as decorative element. No stock imagery.
2. **Latest analysis card:** chart1 thumbnail, title "Fairway vs. Rough, by Handicap", date 2026-07-02, 2-sentence dek (fairway worth 75 yards to a pro at 150, 17 to a 20-handicap), "Read the analysis" link.
3. **Method strip:** three short items: Sources named (Broadie 2011, Stagner/Arccos, USGA/R&A, GOLFTEC); Modeled numbers labeled, every chart, every time; Peer review published, including what broke.
4. **Scramble Reads invite:** "Bring a real scramble read. I'll run it through the model." with link to X @DoglegData.
5. **Footer** per shared pattern.

Copy rules: headline/dek copy must come from the source documents' claims (75/23/17/12 at 150 yards; "modeled" label on the 30). Nothing invented. Tagline "Play the percentages." appears in header chip and hero.

Before writing markup, invoke the `frontend-design` skill; run all copy through `stop-slop` discipline. Commit when done.

**Acceptance:** opens from file://, zero console errors, matches dashboard aesthetic side by side, no green/yellow anywhere, all links resolve (dashboard, post, about may be stubs but hrefs correct), WCAG AA contrast, works at 375px and 1280px.

## Task 2 — Post page + About page + dashboard nav hook

**Files:** `site/fairway-vs-rough/index.html`, `site/about/index.html`, edit `site/fairway-vs-rough/dashboard.html` (header only)

Post page: full article adapting the long caption (source: `Fairway_vs_Rough_Caption.md` text, provided in prompt) into a web essay. Structure:
- Article header: kicker "ANALYSIS Nº 001" (mono), H1 "Fairway vs. Rough, by Handicap", dek, byline "Sunny · Founder, Dogleg Data", date 2026-07-02, reading time.
- Body with all 5 charts as `<figure>` with captions and mono source lines; "modeled" badges where the 30-handicap or dispersion sim appears; alt text states each chart's finding.
- Big dashboard CTA card mid-article and at end ("Run your own numbers", links to `dashboard.html`).
- "What peer review caught" section (the three bugs) styled as a distinct feature block — this is the brand's signature move, give it visual weight.
- Sources section listing all sources with the modeled/measured distinction.
- Closer: the scramble-read invite.
- Preserve every number and caveat exactly as the source copy states them (75/80 peak/23/17/12; 8/17/29 severity; 240-250 crossover; 7.5-yard break-even in the anecdote at 160; three peer-review bugs). Edit for web reading (shorter paragraphs, subheads), never for math.

About page: positioning paragraph, method/verification standard, Sunny bio (from bios file text in prompt), social links, boilerplate paragraph. Short page, same shell.

Dashboard: add a small "← Dogleg Data" home link into its existing header without touching any data, script, or chart code.

Invoke `frontend-design` and apply `stop-slop`. Commit when done.

**Acceptance:** all five charts render, sources intact, no altered numbers (spot-check against source text), nav round-trips home ↔ post ↔ dashboard ↔ about, works at 375px.

## Task 3 — SEO layer

**Files:** edit all four HTML pages; create `robots.txt`, `sitemap.xml`, `llms.txt`, `404.html`

- Per-page: unique `<title>` (≤60 chars) and meta description (≤155 chars), canonical URL (`https://doglegdata.com/...`), OG + Twitter Card meta (og:image → `/assets/brand/og-banner.jpg`, summary_large_image), favicon links (favicon.svg + apple-touch-icon.png), lang, theme-color #F4EDE0.
- JSON-LD: home = WebSite + Organization (logo avatar-512.png, sameAs X/LinkedIn); post = Article (author Person Sunny, image chart1, datePublished 2026-07-02); about = AboutPage + Person; dashboard = WebApplication.
- `sitemap.xml` (4 URLs), `robots.txt` (allow all, sitemap ref, explicitly allow GPTBot/ClaudeBot/PerplexityBot), `llms.txt` per spec (site summary + page list with one-line descriptions).
- `404.html`: mascot-run.png, short line in brand voice, link home.
- Verify heading hierarchy (one H1 per page) and image alt text; fix if missing.

Commit when done.

**Acceptance:** JSON-LD parses (validate with python json against extracted blocks), every page has unique title/description/canonical/OG, sitemap URLs match real files.

## Task 4 — Polish pass

Invoke the `polish` skill. Cross-page sweep: spacing rhythm, alignment, consistent header/footer across all pages including dashboard, hover/focus states, typography scale consistency, mobile at 375px, dead link check (`grep` all hrefs/srcs against files on disk), copy pass for stop-slop violations (grep for " — ", "ly " adverb spot-check, banned words). Fix everything found. Commit.

**Acceptance:** link check script passes, no visual inconsistencies between pages, no slop patterns in rendered copy.

---

## Review protocol

After each task: spec-compliance reviewer subagent, then code-quality reviewer subagent (both Sonnet, per prompts in the subagent-driven-development skill). Controller (Fable) does final browser verification with the preview server and screenshots after Task 4.
