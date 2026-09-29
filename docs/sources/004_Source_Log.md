# Release 004 — Verification Gate Source Log

**Release:** Ball flight laws instructor tool. Sliders for club path, face angle, attack angle, club speed and dynamic loft drive a physics model; a tracer flies over a driving range; TrackMan-style tiles show each number against an ideal band for the club and player type (PGA Tour, LPGA Tour, average amateur); a nine-windows mode shows low, mid and high against draw, straight and fade.
**Purpose:** Standing rule, same as 002 and 003. No number enters the 004 codebase unless it traces to a row in this log. The physics model will be calibrated against these rows, so provenance outranks coverage.
**Hunt date:** 2026-09-28
**Hunter:** Claude (WebSearch, WebFetch, and raw page, PDF and image reads through curl into a scratch folder)

Every value below was read from a page, PDF or image fetched during this session. Each source line names how it was read:

- **RAW:** page HTML or PDF text layer read as published.
- **IMAGE:** a chart that exists only as a picture. It was opened and transcribed by eye, then checked as stated.
- **SUMMARIZED:** WebFetch returns a model summary of the page, not its text. Numbers read this way are marked and need a second read before they feed a calibration fit.
- **SNIPPET:** a number that appeared only in a WebSearch result blurb. Snippet numbers are never logged as values. They appear only as named leads.

Pages that refused a fetch (HTTP 403, Cloudflare or bot challenge, empty body) were not worked around: MyGolfSpy, Golf Digest, GolfWRX, the TrackMan help center, the TrackMan Japan blog (raw), Yumpu, Purdue's ISEA repository, ResearchGate and Scribd. Where one of these holds a needed number, the anchor says so.

## Gate summary

| Anchor | Topic | Verdict |
|---|---|---|
| 1 | TrackMan PGA Tour averages per club | ANCHORED |
| 2 | TrackMan LPGA Tour averages per club | ANCHORED |
| 3 | Average amateur by club | PARTIAL (driver only at handicap resolution; 6-iron and PW only as TrackMan Optimizer defaults) |
| 4 | Driver optimal launch and spin | ANCHORED for the driver (TrackMan 2010 and PING 2019 charts); NOT FOUND for irons |
| 5 | Ball flight law relationships | PARTIAL |
| 6 | Tiger Woods nine windows | ANCHORED for the concept; NOT FOUND for any numbers |
| 7 | Aerodynamic coefficients | PARTIAL (one complete working model and a spin decay law; the Smits and Smith equations were not read) |

---

## Anchor 1 — TrackMan PGA Tour averages per club

**Status: PUBLISHED as a full table, but only as an image on TrackMan's own page. The table below is a transcription. The version we use is the 2023 dataset, published on the TrackMan blog on 2024-05-02, and it is still the current one on TrackMan's pages as of the hunt date.**

**Source 1 (primary, USED):** TrackMan, ["New PGA & LPGA Tour Averages"](https://www.trackman.com/blog/introducing-updated-tour-averages). Page date 2024-05-02 (the page's own date tag). Retrieved 2026-09-28. Read: RAW for the text, IMAGE for the table ([PGA image](https://a.storyblok.com/f/117513/1920x883/6aefae601d/pga_tour-averages_trackman_blog.jpg), headed "PGA TOUR AVERAGES YARDS/METERS 2023"). The page text states: male data comes from more than 40 events and more than 200 players across PGA TOUR and DP World Tour events, with most from the PGA TOUR; averages combine competition and range shots; a process removes non-driver shots from the driver data, leaving fewer than 0.5 percent; official stat holes point in opposite directions to reduce wind effects. The page says the new figures show players hitting driver further, with more ball speed and less spin than the previous set.

**Source 2 (primary, cross-check):** TrackMan Media Kit, [Tour averages](https://www.trackman.media/tour-averages), file ["PGA yards tour average.jpg"](https://images.squarespace-cdn.com/content/v1/63c7e373ff4f92106ce379ce/f40560fd-a473-4f2b-9f8e-194355fb188a/PGA+yards+tour+average.jpg). Retrieved 2026-09-28. Read: IMAGE. This is a separate file from Source 1. Every cell matches Source 1 cell for cell. It labels the hybrid "Hybrid 15-18°". Smash factor equals ball speed over club speed to within rounding on every row (integer speeds in the table cause gaps of up to 0.01).

**Source 3 (older version, SUPERSEDED, logged for comparison):** TrackMan "PGA TOUR AVERAGES" PDF hosted at [teeituprva.com](https://teeituprva.com/wp-content/uploads/2019/03/PGA-AVERAGES-INTERACTIVE.pdf). The PDF metadata gives a creation date of 2019-01-04. TrackMan's 2024 page links a picture ([trackman_tour_avg.jpg](https://a.storyblok.com/f/117513/1080x1384/c4ab5f6f1c/trackman_tour_avg.jpg)) under the words "what's changed compared to the last Tour Averages", and that picture shows the same numbers as this PDF. Retrieved 2026-09-28. Read: RAW (PDF text layer), cross-checked against the picture by eye. The PDF footer says altitude and weather were not taken into account.

### PGA Tour, TrackMan 2023 dataset (USED). Yards.

| Club | Club speed (mph) | Attack angle (deg) | Ball speed (mph) | Smash factor | Launch angle (deg) | Spin rate (rpm) | Max height (yd) | Land angle (deg) | Carry (yd) |
|---|---|---|---|---|---|---|---|---|---|
| Driver | 115 | -0.9 | 171 | 1.49 | 10.4 | 2545 | 35 | 39 | 282 |
| 3-wood | 110 | -2.3 | 162 | 1.47 | 9.3 | 3663 | 32 | 44 | 249 |
| 5-wood | 106 | -2.5 | 156 | 1.47 | 9.7 | 4322 | 33 | 48 | 236 |
| Hybrid (15-18°) | 102 | -2.4 | 149 | 1.47 | 10.2 | 4587 | 31 | 49 | 231 |
| 3 Iron | 100 | -2.5 | 145 | 1.46 | 10.3 | 4404 | 30 | 48 | 218 |
| 4 Iron | 98 | -2.9 | 140 | 1.44 | 10.8 | 4782 | 31 | 49 | 209 |
| 5 Iron | 96 | -3.4 | 135 | 1.41 | 11.9 | 5280 | 33 | 50 | 199 |
| 6 Iron | 94 | -3.7 | 130 | 1.39 | 14.0 | 6204 | 32 | 50 | 188 |
| 7 Iron | 92 | -3.9 | 123 | 1.34 | 16.1 | 7124 | 34 | 51 | 176 |
| 8 Iron | 89 | -4.2 | 118 | 1.33 | 17.8 | 8078 | 33 | 51 | 164 |
| 9 Iron | 87 | -4.3 | 112 | 1.29 | 20.0 | 8793 | 32 | 52 | 152 |
| PW | 84 | -4.7 | 104 | 1.24 | 23.7 | 9316 | 32 | 52 | 142 |

Metric columns printed in the Source 1 image (max height / carry, meters): Driver 32 / 258; 3-wood 29 / 228; 5-wood 30 / 216; Hybrid 28 / 211; 3 Iron 27 / 199; 4 Iron 28 / 192; 5 Iron 30 / 182; 6 Iron 29 / 172; 7 Iron 31 / 161; 8 Iron 30 / 150; 9 Iron 29 / 139; PW 29 / 130.

### PGA Tour, previous TrackMan set (SUPERSEDED, PDF dated 2019-01-04). Yards.

| Club | Club speed (mph) | Attack angle (deg) | Ball speed (mph) | Smash factor | Launch angle (deg) | Spin rate (rpm) | Max height (yd) | Land angle (deg) | Carry (yd) |
|---|---|---|---|---|---|---|---|---|---|
| Driver | 113 | -1.3 | 167 | 1.48 | 10.9 | 2686 | 32 | 38 | 275 |
| 3-wood | 107 | -2.9 | 158 | 1.48 | 9.2 | 3655 | 30 | 43 | 243 |
| 5-wood | 103 | -3.3 | 152 | 1.47 | 9.4 | 4350 | 31 | 47 | 230 |
| Hybrid (15-18°) | 100 | -3.5 | 146 | 1.46 | 10.2 | 4437 | 29 | 47 | 225 |
| 3 Iron | 98 | -3.1 | 142 | 1.45 | 10.4 | 4630 | 27 | 46 | 212 |
| 4 Iron | 96 | -3.4 | 137 | 1.43 | 11.0 | 4836 | 28 | 48 | 203 |
| 5 Iron | 94 | -3.7 | 132 | 1.41 | 12.1 | 5361 | 31 | 49 | 194 |
| 6 Iron | 92 | -4.1 | 127 | 1.38 | 14.1 | 6231 | 30 | 50 | 183 |
| 7 Iron | 90 | -4.3 | 120 | 1.33 | 16.3 | 7097 | 32 | 50 | 172 |
| 8 Iron | 87 | -4.5 | 115 | 1.32 | 18.1 | 7998 | 31 | 50 | 160 |
| 9 Iron | 85 | -4.7 | 109 | 1.28 | 20.4 | 8647 | 30 | 51 | 148 |
| PW | 83 | -5.0 | 102 | 1.23 | 24.2 | 9304 | 29 | 52 | 136 |

**Which set we use:** the 2023 set (Source 1, confirmed by Source 2). The older set has slower driver club and ball speed, higher driver spin, a steeper driver attack angle and shorter carry, which is the trend TrackMan describes on its 2024 page. Mixing the two would corrupt a calibration, so no row from the older table should enter the codebase.

**Other Tour parameters TrackMan publishes.** Only two clubs, driver and 6 iron, and only on the per-parameter TrackMan blog pages. Read RAW on 2026-09-28.

| Parameter (page) | PGA driver | PGA 6 iron | LPGA driver | LPGA 6 iron |
|---|---|---|---|---|
| Dynamic loft, deg ([What is Dynamic Loft](https://www.trackman.com/blog/golf/dynamic-loft)) | 12.8 | 20.2 | 15.5 | 23.6 |
| Spin loft, deg ([What is Spin Loft](https://www.trackman.com/blog/golf/spin-loft)) | 14.7 | 24.3 | 15.0 | 25.9 |

Club path and face angle are not published as Tour averages. The [Club Path](https://www.trackman.com/blog/golf/club-path) and [Face Angle](https://www.trackman.com/blog/what-is-face-angle) pages list no Tour figures and say TrackMan's standard assumption for each is zero for all clubs. Dynamic loft for clubs other than driver and 6 iron is also unpublished. Cross-check on the two rows above: PGA 6 iron dynamic loft minus attack angle is 20.2 - (-3.7) = 23.9, against a published spin loft of 24.3. PGA driver gives 12.8 - (-0.9) = 13.7 against 14.7. LPGA driver gives 15.5 - 2.8 = 12.7 against 15.0. TrackMan states spin loft is close to dynamic loft minus attack angle and departs from it as face-to-path grows. The LPGA driver gap of 2.3 degrees is wider than the other rows and is not explained on the page.

**Verdict: ANCHORED.** Every requested column is published for driver, 3-wood, 5-wood, hybrid, 3-iron through 9-iron and PW, in a primary TrackMan table confirmed by a second TrackMan file. Caveats for the model: the source is an image, so the log is a transcription; values are integers or one-decimal averages of pooled Tour shots, not per-player distributions; club path, face angle and most dynamic loft values are not published.

---

## Anchor 2 — TrackMan LPGA Tour averages per club

**Status: PUBLISHED as a full table in the same image set as Anchor 1. Same page, same date, same "use the 2023 set" decision.**

**Source 1 (primary, USED):** the same [TrackMan blog page](https://www.trackman.com/blog/introducing-updated-tour-averages) (2024-05-02), image headed "LPGA TOUR AVERAGES YARDS/METERS 2023" ([image](https://a.storyblok.com/f/117513/1920x883/9617e89ecd/lpga_tour-averages_trackman_blog.jpg)). Retrieved 2026-09-28. Read: IMAGE. Female data comes from more than 30 events and more than 150 players at LPGA and Ladies European Tour events, with most from the LPGA.

**Source 2 (primary, cross-check):** TrackMan Media Kit file ["LPGA yards tour average.jpg"](https://images.squarespace-cdn.com/content/v1/63c7e373ff4f92106ce379ce/a6360f88-5046-4625-b6aa-30164ccc3981/LPGA+yards+tour+average.jpg). Retrieved 2026-09-28. Read: IMAGE. Every cell matches Source 1.

**Source 3 (older version, SUPERSEDED):** TrackMan "LPGA TOUR AVERAGES" PDF at [teeituprva.com](https://teeituprva.com/wp-content/uploads/2019/03/LPGA-AVERAGES-INTERACTIVE.pdf), PDF metadata creation date 2019-01-04. Read: RAW (text layer).

The 2023 LPGA table has no 3-iron row. It has a hybrid and a 4-iron. The older table has a 7-wood and no hybrid.

### LPGA Tour, TrackMan 2023 dataset (USED). Yards.

| Club | Club speed (mph) | Attack angle (deg) | Ball speed (mph) | Smash factor | Launch angle (deg) | Spin rate (rpm) | Max height (yd) | Land angle (deg) | Carry (yd) |
|---|---|---|---|---|---|---|---|---|---|
| Driver | 96 | 2.8 | 143 | 1.49 | 12.6 | 2506 | 26 | 36 | 223 |
| 3-wood | 92 | -0.8 | 135 | 1.47 | 11.6 | 2595 | 25 | 38 | 200 |
| 5-wood | 90 | -1.6 | 130 | 1.46 | 12.3 | 4320 | 25 | 43 | 189 |
| Hybrid (15-18°) | 87 | -1.9 | 125 | 1.44 | 13.9 | 4504 | 25 | 45 | 178 |
| 4 Iron | 82 | -1.7 | 118 | 1.43 | 13.9 | 4608 | 25 | 43 | 175 |
| 5 Iron | 81 | -2.0 | 114 | 1.42 | 14.6 | 4966 | 25 | 45 | 166 |
| 6 Iron | 80 | -2.3 | 111 | 1.41 | 16.7 | 5904 | 25 | 46 | 155 |
| 7 Iron | 78 | -2.5 | 106 | 1.38 | 18.5 | 6630 | 26 | 47 | 143 |
| 8 Iron | 76 | -2.8 | 102 | 1.36 | 20.8 | 7413 | 27 | 47 | 133 |
| 9 Iron | 74 | -3.2 | 95 | 1.30 | 23.5 | 7605 | 27 | 48 | 123 |
| PW | 72 | -3.2 | 88 | 1.25 | 25.2 | 8465 | 27 | 48 | 111 |

Metric columns printed in the Source 1 image (max height / carry, meters): Driver 24 / 204; 3-wood 23 / 183; 5-wood 23 / 173; Hybrid 23 / 163; 4 Iron 23 / 160; 5 Iron 23 / 152; 6 Iron 23 / 142; 7 Iron 24 / 131; 8 Iron 25 / 122; 9 Iron 25 / 112; PW 25 / 101.

Smash factor differs from ball speed over club speed by up to 0.03 on some rows (the LPGA 6 iron gives 111/80 = 1.39 against a published 1.41). The published club and ball speeds are integers, and rounding explains gaps of this size. Use the published smash column as published and the speed columns as published, and do not rebuild one from the other.

### LPGA Tour, previous TrackMan set (SUPERSEDED, PDF dated 2019-01-04). Yards.

| Club | Club speed (mph) | Attack angle (deg) | Ball speed (mph) | Smash factor | Launch angle (deg) | Spin rate (rpm) | Max height (yd) | Land angle (deg) | Carry (yd) |
|---|---|---|---|---|---|---|---|---|---|
| Driver | 94 | 3.0 | 140 | 1.48 | 13.2 | 2611 | 25 | 37 | 218 |
| 3-wood | 90 | -0.9 | 132 | 1.48 | 11.2 | 2704 | 23 | 39 | 195 |
| 5-wood | 88 | -1.8 | 128 | 1.47 | 12.1 | 4501 | 26 | 43 | 185 |
| 7-wood | 85 | -3.0 | 123 | 1.46 | 12.7 | 4693 | 25 | 46 | 174 |
| 4 Iron | 80 | -1.7 | 116 | 1.45 | 14.3 | 4801 | 24 | 43 | 169 |
| 5 Iron | 79 | -1.9 | 112 | 1.43 | 14.8 | 5081 | 23 | 45 | 161 |
| 6 Iron | 78 | -2.3 | 109 | 1.41 | 17.1 | 5943 | 25 | 46 | 152 |
| 7 Iron | 76 | -2.3 | 104 | 1.38 | 19.0 | 6699 | 26 | 47 | 141 |
| 8 Iron | 74 | -3.1 | 100 | 1.33 | 20.8 | 7494 | 25 | 47 | 130 |
| 9 Iron | 72 | -3.1 | 93 | 1.32 | 23.9 | 7589 | 26 | 47 | 119 |
| PW | 70 | -2.8 | 86 | 1.28 | 25.7 | 8403 | 23 | 48 | 107 |

**Which set we use:** the 2023 set. The LPGA driver attack angle is positive (+2.8 in 2023, +3.0 before) and every other LPGA club is negative or near zero. Any model that forces one shared attack-angle rule across clubs and tours will miss this. Dynamic loft and spin loft for driver and 6 iron are in the Anchor 1 supplement table.

**Verdict: ANCHORED.** Same caveats as Anchor 1: image transcription, pooled averages, no club path or face angle.

---

## Anchor 3 — Average amateur by club

**Status: TrackMan publishes amateur numbers by handicap band, for the DRIVER only, on its own blog. TrackMan gives 6-iron and pitching wedge "average male golfer" values only as Optimizer default assumptions, and those are model outputs, not measurements. No primary source found publishes a full per-club amateur table. Secondary sources give a few irons, with definitions that stay unclear.**

**Source 1 (primary, driver by handicap):** TrackMan "Trackman Combine Averages" blocks, repeated on TrackMan's per-parameter pages, all dated 2024-09-23 on the page unless noted. Retrieved 2026-09-28. Read: RAW (page HTML converted to text).
[Club Speed](https://www.trackman.com/blog/golf/what-is-club-speed), [Ball Speed](https://www.trackman.com/blog/ball-speed), [Smash Factor](https://www.trackman.com/blog/smash-factor), [Attack Angle](https://www.trackman.com/blog/attack-angle), [Launch Angle](https://www.trackman.com/blog/golf/launch-angle), [Spin Rate](https://www.trackman.com/blog/spin-rate), [Dynamic Loft](https://www.trackman.com/blog/golf/dynamic-loft), [Spin Loft](https://www.trackman.com/blog/golf/spin-loft), [Swing Plane](https://www.trackman.com/blog/what-is-swing-plane) (page date 2024-05-01). The pages do not state sample size, date range or launch monitor generation for the Combine data.

### TrackMan Combine, male amateur, driver

| Metric | Scratch or better | 5 HCP | 10 HCP | Average golfer (14.5) | Bogey golfer |
|---|---|---|---|---|---|
| Club speed (mph) | 110 | 101 | 95 | 94 | 92 |
| Ball speed (mph) | 161 | 147 | 138 | 133 | 131 |
| Smash factor | 1.49 | 1.45 | 1.45 | 1.44 | 1.43 |
| Attack angle (deg) | -0.9 | -1.1 | -1.2 | -1.8 | -2.1 |
| Launch angle (deg) | 11.2 | 11.2 | 11.9 | 12.6 | 12.1 |
| Dynamic loft (deg) | 13.0 | 13.2 | 14.1 | 15.1 | 14.3 |
| Spin loft (deg) | 14.8 | 15.8 | 17.3 | 18.3 | 18.2 |
| Spin rate (rpm) | 2896 | 2987 | 3192 | 3275 | 3127 |
| Swing plane (deg) | 48.1 | 48.5 | 48.9 | 49.0 | 49.4 |

### TrackMan Combine, female amateur, driver

| Metric | Scratch or better | 5 HCP | 10 HCP | 15 HCP |
|---|---|---|---|---|
| Club speed (mph) | 90 | 87 | 83 | 79 |
| Ball speed (mph) | 131 | 125 | 119 | 111 |
| Smash factor | 1.46 | 1.45 | 1.44 | 1.41 |
| Attack angle (deg) | -0.9 | -1.8 | -1.7 | -2.3 |
| Launch angle (deg) | 12.7 | 12.0 | 12.4 | 13.6 |
| Dynamic loft (deg) | 14.8 | 14.4 | 15.0 | 16.5 |
| Spin loft (deg) | 17.1 | 18.4 | 18.6 | 20.1 |
| Spin rate (rpm) | 2831 | 3027 | 3207 | 3287 |
| Swing plane (deg) | 46.8 | 47.2 | 48.4 | 47.6 |

Note on internal consistency. The published smash factor is not the ratio of the published mean speeds. For the 14.5 handicap the ratio is 133 / 94 = 1.415 against a published 1.44. For scratch it is 161 / 110 = 1.464 against 1.49. The likelier cause is that TrackMan averaged per-shot smash factors, but the pages do not say. Do not derive one column from the other in the amateur presets.

**Source 2 (primary, "standard assumption" defaults, NOT measured amateur data):** the same per-parameter pages state TrackMan Optimizer defaults for the average male golfer, used whenever a value is not entered. Read: RAW.

| Parameter | Driver (club speed 94 mph, attack angle 0, optimized carry) | 6 iron (club speed 80 mph, mid trajectory) | PW (club speed 72 mph, mid trajectory) |
|---|---|---|---|
| Ball speed (mph) | 137 | 110 | 86 |
| Launch angle (deg) | 13.6 | 16.9 | 26.7 |
| Spin rate (rpm) | 2772 | 5956 | 8408 |
| Dynamic loft (deg) | 15.6 | 22.4 | 36.7 |
| Spin loft (deg) | 15.6 | 25.5 | 40.6 |
| Attack angle (deg) | 0 | -3.2 | -3.9 |

These are what TrackMan's optimizer says a golfer at that club speed should produce, not what amateurs hit. The Combine driver row for the average golfer (spin 3275, launch 12.6, ball speed 133) sits away from the Optimizer driver row (spin 2772, launch 13.6, ball speed 137). Source 3's "optimal" column (ball speed 140.1, launch 14.7, spin 2300) does not equal the Optimizer default either, so the two come from different optimizer runs and should not be mixed.

**Source 3 (primary, older, driver only):** TrackMan (Japan blog), ["Performance of the Average Male Amateur Golfer"](https://blog.trackmangolf.jp/performance-of-the-average-male-amateur/), published 2014-08-02. Read: SUMMARIZED (the raw page returned a bot challenge, so only the WebFetch summary was available). The summary listed, for the average male amateur with a driver, actual against optimal: ball speed 132.6 against 140.1 mph; launch 12.6 against 14.7 deg; spin 3275 against 2300 rpm; carry 204 against 228 yd; landing angle 34.8 against 34.1 deg; total 226 against 255 yd; club speed 93.4 mph. The summary also gave an "average total distance" of 214 yd, which disagrees with the 226 in the table. Treat this source as a pointer only. Its 3275 rpm and 12.6 deg equal the current Combine average-golfer values, so the pages draw on the same dataset, and the current pages are the ones to cite.

**Source 4 (secondary, TrackMan-sourced, driver speed by skill):** Golf.com, ["Here's how fast golfers swing their driver based on handicap"](https://golf.com/instruction/how-fast-swing-driver-based-handicap/), 2021-02-03, credited to TrackMan data. Read: SUMMARIZED. Ranges only: Tour "upwards of 110 mph", scratch "around 106", high single digits "hover around 97", average "about 93"; overall mean 93.4 mph with more than 40 percent between 91 and 100 mph. These disagree with the Combine page (scratch 110, 10 HCP 95). **Primary is the TrackMan Combine page.**

**Source 5 (secondary, Arccos, per club, definitions unclear):** Arccos, ["Know Your Club Distances With Arccos Caddie Smart Distance"](https://www.arccosgolf.com/blogs/community/arccos-caddie-smart-distances-provide-rapid-golf-game-improvement), dated 2020-04-24, 6+ million shots. Read: SUMMARIZED. Labels as returned by the summary: 5 iron, scratch mean 194 / median 176 yd, 20 handicap mean 187 / median 152; 7 iron, scratch 170 / 159, 10 handicap 165 / 148, 20 handicap 162 / 140; PW, scratch 126 / 122, 10 handicap 119 / 114, 20 handicap 112 / 104; driver 0-5 handicap 243, 16-20 handicap 209. The page's own definition of "mean" against "median" and whether the values are carry or total distance were not confirmed. Do not use as carry.

**Source 6 (secondary, Shot Scope via a retailer, one club):** MG Golf, ["New Shot Scope data shows the average golfer carries a 5-iron 174 yards"](https://mggolf.com/blogs/the-fairway-report-golf-news-tips/new-shot-scope-data-shows-the-average-golfer-carries-a-5-iron-174-yards-see-how-you-compare-by-handicap), 2026-08-08, citing Shot Scope data reported by Golf Monthly. Read: SUMMARIZED. 5-iron carry: scratch 200, 5 HCP 183, 10 HCP 187, 15 HCP 169, 25 HCP 143, overall 174 yd. The 5 and 10 handicap values run in the wrong order, so a transcription or data problem exists upstream. The same retailer's [distance chart](https://mggolf.com/blogs/the-fairway-report-golf-news-tips/golf-club-carry-distance) (2026-08-27) lists a full bag for 5, 15 and 25 handicaps, but its own text says only the driver row is Shot Scope P-Avg data and the rest are "rounded full-bag planning estimates". **REJECTED as an anchor.**

**Source 7 (secondary, Shot Scope, driver only):** Shot Scope, ["Reduce your Handicap – 15hcp Law of Averages"](https://shotscope.com/blog/practice-green/game-improvement/reduce-your-handicap-15hcp/). Read: RAW. The text says the 15 handicap hits 34 yd longer than a 20 handicap and 22 yd shorter than a 10 handicap, and, in the same paragraph, that "a 25 handicapper has a Performance-Average driver distance of 238 yards" on a page about the 15 handicap. The handicap label on the 238 figure conflicts with the rest of the page (the MG Golf chart above assigns 238 to the 15 handicap). Performance Average is Shot Scope's on-course figure with outliers removed and includes roll. Not a carry number.

**Not read:** MyGolfSpy's iron distance chart and driver optimal chart (HTTP 403 and Cloudflare challenge). If MyGolfSpy holds a per-club, per-handicap table, it needs a human with a browser.

**Verdict: PARTIAL.** ANCHORED at handicap resolution for the driver (male and female, five and four bands, nine metrics). MODELED for every other club. TrackMan gives 6 iron and PW only as optimizer defaults for a 94 mph driver golfer. Nothing found gives a measured amateur 7-iron table from a primary source. The model must build amateur irons by scaling from the driver row using the published Tour club ladder (Anchor 1), and label the result modeled.

---

## Anchor 4 — Driver optimization: optimal launch and spin by club speed and attack angle

**Status: TWO complete numeric charts exist. TrackMan's Driver Fitting Chart (2010) gives optimal ball speed, launch, spin and dynamic loft by club speed and attack angle. PING's Optimal Launch & Spin Chart (2019) gives optimal launch and spin by ball speed and attack angle. The two disagree by a few degrees of launch and a few hundred rpm. No numeric optimum for irons was found.**

**Source 1 (primary, TrackMan, dated 2010):** TrackMan "Driver Fitting Chart" PDF, four pages, footer "www.trackman.dk", PDF metadata creation date 2010-02-10, hosted at [wishongolf.com](https://wishongolf.com/wp-content/uploads/2012/07/TrackMan-Driver-Optimization_2010.pdf) (a fitter's site, not TrackMan). Retrieved 2026-09-28. Read: RAW (PDF text layer). Two charts: "CARRY Optimizer" (optimizes carry) and "TOTAL Optimizer" (optimizes total distance). Attack angles tabulated: -5, 0 and +5 degrees. Club speeds 75 to 120 mph in 5 mph steps. The PDF gives no ball model, air conditions or launch monitor generation, and it predates the 2023 Tour dataset by 13 years.

### TrackMan CARRY Optimizer (2010)

| Club speed (mph) | Attack angle (deg) | Ball speed (mph) | Launch angle (deg) | Spin rate (rpm) | Carry (yd) | Total (yd) | Dynamic loft (deg) |
|---|---|---|---|---|---|---|---|
| 75 | -5 | 104 | 14.6 | 3722 | 143 | 166 | 18.2 |
| 75 | 0 | 107 | 16.3 | 3121 | 154 | 178 | 19.2 |
| 75 | 5 | 108 | 19.2 | 2720 | 164 | 187 | 21.8 |
| 80 | -5 | 113 | 12.9 | 3652 | 160 | 176 | 16.2 |
| 80 | 0 | 115 | 15.5 | 3179 | 171 | 187 | 18.3 |
| 80 | 5 | 116 | 18.0 | 2648 | 181 | 197 | 20.3 |
| 85 | -5 | 121 | 11.9 | 3669 | 175 | 199 | 15.0 |
| 85 | 0 | 123 | 14.5 | 3164 | 187 | 211 | 17.1 |
| 85 | 5 | 124 | 17.0 | 2596 | 197 | 223 | 19.1 |
| 90 | -5 | 129 | 11.1 | 3689 | 191 | 215 | 14.0 |
| 90 | 0 | 131 | 13.4 | 3093 | 203 | 228 | 15.8 |
| 90 | 5 | 132 | 16.4 | 2633 | 214 | 239 | 18.5 |
| 95 | -5 | 137 | 9.9 | 3626 | 207 | 243 | 12.6 |
| 95 | 0 | 138 | 12.7 | 3114 | 219 | 244 | 15.0 |
| 95 | 5 | 140 | 15.7 | 2595 | 231 | 256 | 17.6 |
| 100 | -5 | 144 | 9.6 | 3722 | 222 | 244 | 12.2 |
| 100 | 0 | 146 | 12.1 | 3118 | 235 | 272 | 14.3 |
| 100 | 5 | 148 | 14.9 | 2538 | 247 | 272 | 16.7 |
| 105 | -5 | 152 | 8.7 | 3675 | 237 | 260 | 11.1 |
| 105 | 0 | 154 | 11.2 | 3038 | 251 | 275 | 13.2 |
| 105 | 5 | 155 | 14.5 | 2563 | 263 | 288 | 16.2 |
| 110 | -5 | 160 | 7.7 | 3570 | 252 | 275 | 9.9 |
| 110 | 0 | 162 | 10.5 | 2970 | 266 | 291 | 12.3 |
| 110 | 5 | 163 | 13.7 | 2435 | 279 | 305 | 15.2 |
| 115 | -5 | 168 | 7.0 | 3548 | 266 | 290 | 9.2 |
| 115 | 0 | 170 | 9.8 | 2919 | 281 | 306 | 11.6 |
| 115 | 5 | 171 | 13.0 | 2358 | 295 | 321 | 14.4 |
| 120 | -5 | 176 | 6.1 | 3433 | 281 | 305 | 8.1 |
| 120 | 0 | 178 | 9.3 | 2890 | 296 | 321 | 11.0 |
| 120 | 5 | 179 | 12.6 | 2343 | 310 | 350 | 14.0 |

In the CARRY table, total distance at attack angle 0 reads 244 yd at 95 mph, 272 yd at 100 mph and 275 yd at 105 mph. A 28 yard jump followed by a 3 yard step looks like a printing error in the source. Values are logged as printed.

### TrackMan TOTAL Optimizer (2010)

| Club speed (mph) | Attack angle (deg) | Ball speed (mph) | Launch angle (deg) | Spin rate (rpm) | Carry (yd) | Total (yd) | Dynamic loft (deg) |
|---|---|---|---|---|---|---|---|
| 75 | -5 | 107 | 11.8 | 3214 | 140 | 182 | 14.9 |
| 75 | 0 | 109 | 13.0 | 2506 | 147 | 195 | 15.3 |
| 75 | 5 | 111 | 15.3 | 1976 | 156 | 206 | 17.1 |
| 80 | -5 | 115 | 10.1 | 3078 | 154 | 188 | 12.8 |
| 80 | 0 | 117 | 12.1 | 2494 | 163 | 199 | 14.3 |
| 80 | 5 | 118 | 14.8 | 2005 | 174 | 209 | 16.5 |
| 85 | -5 | 123 | 9.3 | 3110 | 169 | 215 | 11.9 |
| 85 | 0 | 125 | 11.7 | 2568 | 180 | 228 | 13.8 |
| 85 | 5 | 126 | 14.0 | 1964 | 189 | 241 | 15.6 |
| 90 | -5 | 131 | 8.5 | 3122 | 185 | 231 | 11.0 |
| 90 | 0 | 132 | 10.8 | 2517 | 196 | 245 | 12.8 |
| 90 | 5 | 134 | 13.8 | 2021 | 207 | 259 | 15.3 |
| 95 | -5 | 138 | 7.9 | 3144 | 201 | 247 | 10.2 |
| 95 | 0 | 140 | 10.5 | 2565 | 213 | 262 | 12.3 |
| 95 | 5 | 141 | 13.0 | 1948 | 223 | 276 | 14.4 |
| 100 | -5 | 146 | 7.2 | 3118 | 216 | 262 | 9.3 |
| 100 | 0 | 148 | 10.0 | 2570 | 230 | 278 | 11.7 |
| 100 | 5 | 149 | 12.4 | 1887 | 239 | 293 | 13.7 |
| 105 | -5 | 154 | 6.4 | 3071 | 231 | 278 | 8.4 |
| 105 | 0 | 156 | 9.1 | 2461 | 243 | 294 | 10.7 |
| 105 | 5 | 157 | 11.7 | 1810 | 254 | 309 | 12.9 |
| 110 | -5 | 162 | 5.6 | 3005 | 245 | 293 | 7.5 |
| 110 | 0 | 163 | 8.7 | 2471 | 260 | 310 | 10.2 |
| 110 | 5 | 165 | 11.1 | 1716 | 268 | 326 | 12.2 |
| 115 | -5 | 170 | 5.3 | 3030 | 261 | 307 | 7.1 |
| 115 | 0 | 171 | 8.0 | 2396 | 274 | 325 | 9.5 |
| 115 | 5 | 172 | 10.7 | 1681 | 285 | 342 | 11.7 |
| 120 | -5 | 178 | 4.5 | 2929 | 273 | 322 | 6.2 |
| 120 | 0 | 179 | 7.7 | 2382 | 290 | 340 | 9.0 |
| 120 | 5 | 180 | 10.3 | 1636 | 300 | 358 | 11.3 |

**Source 2 (primary, PING, dated 2019):** PING "Optimal Launch & Spin Chart", one-page PDF, PDF title "Optimal_Launch_Spin_Chart_Update_10_30_19", creation date 2019-10-30, hosted at [pgamagazine.com](https://pgamagazine.com/wp-content/media/2021/02/Optimal-Launch-Spin-Chart-1.pdf) (a mirror uploaded in 2021-02). Retrieved 2026-09-28. Read: RAW for the text layer and IMAGE (rendered page) to confirm the cell grid. PING's own pages did not return it: the [Proving Grounds article URL](https://ca.ping.com/en-ca/blogs/proving-grounds/optimal-launch-and-spin) now shows the podcast index, and the Golf Digest write-up returned HTTP 403. The chart rows are driver ball speed (mph) and the columns are angle of attack (deg). Each cell holds a launch angle and a spin rate. Notes printed on the chart: launch within 1 degree and spin within 300 rpm of the cell counts as near optimal; for ball speed above 155 mph on firm or windy fairways, lower launch by 0.5 to 1 degree and spin by 150 to 250 rpm, and on soft fairways raise both by the same amounts; for ball speed below 125 mph, adjust launch by 1.5 to 3 degrees and spin by 250 to 400 rpm in the same directions; angle of attack values assume a radar monitor that tracks the clubhead center, and a camera-based monitor reads about 2 degrees higher (a +4 camera reading maps to the +2 column). The colored legend maps colors to carry bands (125 to 325 yd) and prints no per-cell carry. Cell format below: launch deg / spin rpm.

### PING Optimal Launch & Spin Chart (2019). Launch (deg) / spin (rpm).

| Ball speed (mph) | AoA -10 | AoA -8 | AoA -6 | AoA -4 | AoA -2 | AoA 0 | AoA +2 | AoA +4 | AoA +6 | AoA +8 | AoA +10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 180 | 3.6 / 3450 | 4.9 / 3250 | 6.2 / 3050 | 7.5 / 2850 | 9.0 / 2700 | 10.4 / 2550 | 11.9 / 2400 | 13.3 / 2200 | 14.8 / 2050 | 16.4 / 1950 | 17.9 / 1800 |
| 170 | 4.3 / 3500 | 5.7 / 3300 | 6.9 / 3100 | 8.2 / 2900 | 9.6 / 2750 | 11.0 / 2550 | 12.4 / 2400 | 13.9 / 2250 | 15.3 / 2100 | 16.8 / 1950 | 18.2 / 1800 |
| 160 | 5.2 / 3500 | 6.5 / 3300 | 7.7 / 3100 | 9.0 / 2950 | 10.3 / 2750 | 11.7 / 2600 | 13.0 / 2400 | 14.4 / 2300 | 15.9 / 2100 | 17.3 / 1950 | 18.7 / 1800 |
| 150 | 6.2 / 3500 | 7.4 / 3350 | 8.6 / 3150 | 9.8 / 2950 | 11.1 / 2750 | 12.4 / 2600 | 13.7 / 2450 | 15.1 / 2300 | 16.4 / 2150 | 17.9 / 2000 | 19.3 / 1850 |
| 140 | 7.3 / 3550 | 8.3 / 3300 | 9.5 / 3150 | 10.7 / 2950 | 12.0 / 2800 | 13.2 / 2600 | 14.5 / 2450 | 15.8 / 2300 | 17.2 / 2150 | 18.5 / 2000 | 19.9 / 1850 |
| 130 | 8.4 / 3500 | 9.4 / 3300 | 10.6 / 3150 | 11.7 / 2950 | 12.8 / 2750 | 14.1 / 2600 | 15.3 / 2450 | 16.6 / 2300 | 17.9 / 2150 | 19.2 / 2000 | 20.6 / 1850 |
| 120 | 9.6 / 3450 | 10.6 / 3250 | 11.6 / 3100 | 12.7 / 2900 | 13.8 / 2750 | 15.0 / 2600 | 16.2 / 2450 | 17.4 / 2300 | 18.7 / 2150 | 19.9 / 2000 | 21.2 / 1850 |
| 110 | 10.9 / 3400 | 11.8 / 3200 | 12.7 / 3000 | 13.9 / 2850 | 14.9 / 2700 | 15.9 / 2550 | 17.1 / 2400 | 18.2 / 2250 | 19.5 / 2100 | 20.7 / 1950 | 21.9 / 1850 |
| 100 | 11.9 / 3250 | 12.9 / 3100 | 13.9 / 2950 | 14.9 / 2800 | 15.9 / 2600 | 16.9 / 2450 | 18.0 / 2300 | 19.1 / 2150 | 20.3 / 2050 | 21.4 / 1900 | 22.6 / 1750 |
| 90 | 12.7 / 3050 | 13.9 / 2950 | 15.0 / 2800 | 15.9 / 2650 | 16.9 / 2500 | 18.0 / 2350 | 19.0 / 2200 | 20.0 / 2100 | 21.1 / 1950 | 22.2 / 1850 | 23.3 / 1700 |
| 80 | 13.8 / 2800 | 14.5 / 2650 | 15.8 / 2600 | 16.9 / 2450 | 17.8 / 2350 | 18.8 / 2200 | 19.9 / 2100 | 20.8 / 1950 | 21.8 / 1800 | 22.9 / 1700 | 24.0 / 1600 |

An AI-generated encyclopedia page about this chart ([Grokipedia](https://grokipedia.com/page/PING_Optimal_Launch_and_Spin_Chart), fetched) quotes example cells such as "160 mph, +5 degrees, 15.1 deg, 2179 rpm". The PING chart has no +5 column and its 160 mph, +4 and +6 cells read 14.4 / 2300 and 15.9 / 2100. **Grokipedia's figures are wrong and were not used.**

**Source 3 (secondary, fitter parameter bands):** Golf.com, ["Optimal Trackman numbers to hit farther drives, based on swing speed"](https://golf.com/gear/swing-speed-optimal-trackman-numbers-to-hit-your-drives-farther/), 2020-07-02, credited to True Spec Golf "Launch Monitor Preferred Parameters". Read: SUMMARIZED. Bands by swing speed, as returned: Very Fast (105+ mph) launch 10 to 16 deg, spin 1750 to 2300 rpm, peak height 100 to 120 ft, descent angle 34 to 38 deg; Fast (97 to 104) 12 to 16, 2000 to 2500, 87 to 100 ft, 33 to 37; Average (84 to 96) 13 to 16, 2400 to 2700, 70 to 86 ft, 32 to 36; Slow (72 to 83) 14 to 19, 2600 to 2900, 58 to 70 ft, 31 to 35; Ladies (under 72) 14 to 19, 2600 to 2900, 45 to 58 ft, 27 to 31. Ranges only, from a fitting company, no attack angle. Useful as a band width guide, not as an anchor.

**Where the two primary charts overlap** (attack angle 0, values read from the tables above):

| Ball speed | TrackMan CARRY (launch / spin) | TrackMan TOTAL (launch / spin) | PING (launch / spin) |
|---|---|---|---|
| about 130 mph | 13.4 / 3093 (ball 131) | 10.8 / 2517 (ball 132) | 14.1 / 2600 (ball 130) |
| about 160 mph | 10.5 / 2970 (ball 162) | 8.7 / 2471 (ball 163) | 11.7 / 2600 (ball 160) |
| about 170 mph | 9.8 / 2919 (ball 170) | 8.0 / 2396 (ball 171) | 11.0 / 2550 (ball 170) |

PING's launch angle runs 0.7 to 1.2 degrees above TrackMan's carry optimum and 3.0 to 3.3 degrees above TrackMan's total-distance optimum. PING's spin runs 370 to 490 rpm below TrackMan's carry optimum and 80 to 150 rpm above TrackMan's total optimum. For scale, the 2023 PGA driver row (Anchor 1: ball speed 171, attack angle -0.9, launch 10.4, spin 2545) falls between PING's 170 mph cells for attack angles of -2 and 0 (9.6 / 2750 and 11.0 / 2550).

**Iron and wedge optima.** TrackMan publishes no optimal launch, spin or descent-angle table for irons. Its Optimizer is described on the [Shot Optimizer](https://www.trackman.com/blog/golf/trackman-shot-optimizer) (2015-12-23, Tom Stickney II) and [Optimizer](https://www.trackman.com/blog/golf/unlock-your-full-potential-with-trackman-optimizer) (2025-10-10) pages as comparing a shot to ideal benchmarks, and neither page prints the benchmark values. The only iron-relevant Optimizer numbers are the 6-iron and PW defaults in Anchor 3, Source 2. PING's [fitting page](https://ca.ping.com/en-us/fitting/our-process/driver-fitting) prints no numeric launch, spin or angle-of-attack guidance.

**Verdict: ANCHORED** for the driver, in two independent primary charts (TrackMan 2010, PING 2019) that agree on the shape of the relationship and differ in level. **NOT FOUND** for irons: the model must derive iron ideal bands from the Tour table (Anchor 1, LPGA in Anchor 2) and label them modeled. The 2010 chart is old, PING's states its own tolerance (plus or minus 1 degree launch, 300 rpm spin), and the ideal band drawn on a driver tile should use that width, not a single value.

---

## Anchor 5 — Ball flight law relationships

**Status: Definitions are PUBLISHED by TrackMan in plain text. The face-versus-path start direction shares (about 85 percent driver, 75 percent irons) are NOT confirmed in any primary text read this session and two secondary versions disagree. Curvature is PUBLISHED as worked examples, not as a per-degree formula. The attack-angle to path coupling is PUBLISHED in words by TrackMan and as a formula only on a forum.**

### (a) Start direction: face against path

**Source 1 (primary, qualitative):** TrackMan, ["What is Face Angle?"](https://www.trackman.com/blog/what-is-face-angle) (2024-09-23). Read: RAW. Face angle is the most important number for start direction, and the ball launches close to the direction the face points at impact. TrackMan's [Club Path](https://www.trackman.com/blog/golf/club-path) page says path is part of what determines starting direction. TrackMan's ["The true impact factors"](https://www.trackman.com/blog/golf/trackman-talks-the-true-impact-factors) (2025-05-01) says face angle is the main contributor to launch direction. No percentage appears on any of these three pages.

**Source 2 (primary, geometry only):** TrackMan, ["What is Launch Direction?"](https://www.trackman.com/blog/what-is-launch-direction) (2022-02-17). Read: RAW. Launch direction is the horizontal start angle of the ball relative to the target line, positive right. Offline distance by launch direction: at 100 yd, 1 deg left is 1.7 yd, 3 deg left is 5.2 yd, 2 deg right is 3.4 yd, 4 deg right is 7.0 yd; at 200 yd, 1 deg left is 3.5 yd, 3 deg left is 10.5 yd, 2 deg right is 7.0 yd, 4 deg right is 14.0 yd; at 300 yd, 1 deg left is 5.2 yd, 3 deg left is 15.7 yd, 2 deg right is 10.5 yd, 4 deg right is 20.9 yd. TrackMan's standard assumption is zero. One Master's quote on the page says to keep launch direction within plus or minus 2 degrees.

**Source 3 (secondary, no TrackMan attribution):** PGA Academy Australia, ["Starting Line - Path or Face?"](https://pgaacademy.com.au/trackman/starting-line-path-or-face/), 2014-07-22. Read: SUMMARIZED. Says the face controls 75 percent of the start line for a 6 iron and about 85 percent for a driver. The page does not credit TrackMan for those figures.

**Source 4 (secondary, forum, TrackMan cited by the poster):** Golf Simulator Forum, [thread "Experiment: Rough calculation of clubface using launch direction and club path"](https://golfsimulatorforum.com/forum/foresight-sports/345478-experiment-rough-calculation-of-clubface-using-launch-direction-and-club-path), post by "dinospumoni", 2021-10-14. Read: SUMMARIZED. The poster says "trackman academy" assigns 87 percent of launch direction to face angle and 13 percent to path for a driver, and 81 percent and 19 percent for a 6 iron or pitching wedge, with the formula "Club Face Angle*.87 + Club Path*.13 = Launch Direction". No URL or date for the TrackMan material.

**Source 5 (secondary, forum, image only):** Brian Manzella Golf forum, ["NEW (Launch Direction Dictated by...) CHART from TrackMan Conference"](https://forum.brianmanzellagolf.com/threads/new-launch-direction-dictated-by-chart-from-trackman-conference.15009/), posted 2011-03-11. Read: SUMMARIZED. The chart is an image with no text values. Replies mention 85 percent driver, 75 percent irons, 65 percent lob wedge as conversational estimates, not as chart readings.

**Not readable:** the primary document that should hold the shares is Fredrik Tuxen's "TRACKMAN Ball Flight Laws" (TrackMan CTO, 25 pages, 2013-03-26 per its [Yumpu listing](https://www.yumpu.com/en/document/view/11652756/trackman-ball-flight-laws)). The listing showed a table of contents (club and ball collision, ball launch direction, launch angle, D-plane, spin axis, gear effect) and returned no text to the fetch tool. A human should open it and copy the launch direction weighting table.

**Conflict to carry forward:** the shares in circulation are 85 / 75 (PGA Academy, unattributed), 87 / 81 for driver and 6-iron-or-wedge (forum, attributed to TrackMan Academy) and 65 for a lob wedge (forum chatter). The design doc's "about 0.85 for driver and 0.75 for wedges" matches the first set for irons and does not match the 81 percent figure for wedges. None is verified.

### (b) Curvature per degree of face-to-path and spin axis

**Source 1 (primary):** TrackMan, ["What is Face to Path?"](https://www.trackman.com/blog/face-to-path) (2024-09-23). Read: RAW. Face to path is face angle minus club path. With centered contact the ball curves toward the face angle and away from the path. TrackMan's worked examples (centered contact):

| Shot | Face-to-path (deg) | Curvature (yd) |
|---|---|---|
| PGA Tour driver, 275 yd carry | -2 | 19 left |
| PGA Tour driver, 275 yd carry | 5 | 44 right |
| PGA Tour 6 iron, 183 yd carry | 2 | 8 right |
| PGA Tour 6 iron, 183 yd carry | -5 | 20 left |
| LPGA driver, 218 yd carry | 2 | 14 right |
| LPGA driver, 218 yd carry | -5 | 32 left |
| LPGA 6 iron, 152 yd carry | -2 | 6 left |
| LPGA 6 iron, 152 yd carry | 5 | 14 right |

Arithmetic on the table, for orientation only (derived here, not published): the ratio of curvature to face-to-path runs about 9.5 yd per degree (PGA driver, left) and 8.8 (right), 4.0 (PGA 6 iron), 7.0 and 6.4 (LPGA driver), 3.0 and 2.8 (LPGA 6 iron). The same face-to-path bends a longer club more, and the values are not symmetric for left and right on the driver. The carry figures in these examples (275, 183, 218, 152) are the 2019-set carries, not the 2023 set, so the page's examples are one dataset behind the Tour table we use.

**Source 2 (primary):** TrackMan, ["What is Spin Axis?"](https://www.trackman.com/blog/spin-axis) (2024-09-23). Read: RAW. Positive spin axis curves the ball right, negative left. A spin axis between -2 and 2 counts as straight. Examples: for an optimized 150 yd shot, 2 deg of spin axis is about 2.2 yd of curvature and 10 deg is about 11 yd; for an optimized 200 yd shot, 2 deg is about 3 yd and 10 deg is about 15 yd. In outdoor mode TrackMan reads the spin axis from the first 30 yards of ball flight; in indoor mode it computes it from spin loft and face to path. The page states no formula from face-to-path to spin axis.

**Source 3 (primary, coach quote on TrackMan's page):** the Face to Path page carries a quote from John Parkinson that 1 deg of face-to-path at 300 yd gives 12 yd of curve. It is a coach's estimate, not a TrackMan table.

### (c) Attack angle, swing direction and club path

**Source 1 (primary, definitions):** TrackMan, ["What is Swing Direction?"](https://www.trackman.com/blog/what-is-swing-direction) (2016-11-20) and ["What is Swing Plane?"](https://www.trackman.com/blog/what-is-swing-plane) (2024-05-01). Read: RAW. Swing direction is the horizontal direction of the plane the club head follows from about knee high to knee high on the downswing. Club path is the horizontal direction at one instant, maximum compression. Swing plane is the vertical angle of that plane. TrackMan puts a driver between 45 and 50 degrees. A coach quote on the Swing Direction page puts the swing direction for arrow-straight iron shots at about -2.5 degrees. TrackMan's ["The true impact factors"](https://www.trackman.com/blog/golf/trackman-talks-the-true-impact-factors) lists five inputs a player controls (swing plane, swing direction, club speed, face angle, 3D low point) and calls club path and attack angle combinations of them. On that page swing direction is a key component of club path, and swing plane and 3D low point shape attack angle. The Combine average swing planes are in the Anchor 3 tables (48.1 to 49.4 deg male, 46.8 to 48.4 deg female).

**Source 2 (forum formula, NOT TrackMan):** Brian Manzella Golf forum, ["Clubhead Direction - AoA and Club Path"](https://forum.brianmanzellagolf.com/threads/clubhead-direction-aoa-and-club-path.15209/), poster "cwdlaw223", 2011-04-12. Read: SUMMARIZED. Formula as posted: CP = HSP - [AA x tan(90 - VSP)], with CP club path, HSP horizontal swing plane (swing direction), AA angle of attack and VSP vertical swing plane. In a companion [thread](https://forum.brianmanzellagolf.com/threads/club-path-and-attack-angle-trackman.14822/) the summary found no formula from TrackMan staff, only the statement that VSP, HSP and attack angle combine to give path, and participants noting TrackMan does not define a "true path". Sign check on the posted formula: a negative attack angle (hitting down) raises path (moves it right for a right-hander), which agrees with the instructor rule the design doc names. Derived here, not published: for a 49 degree vertical swing plane (the Combine average driver plane), 1 / tan(49 deg) is about 0.87, so each degree of downward attack angle would add about 0.87 degree to path at fixed swing direction. Treat as geometry the model owns, with the forum as the only text citation.

**Source 3 (primary, measurement offsets that matter for calibration):** TrackMan, ["Understanding Club Data in Golf"](https://www.trackman.com/blog/club-data-definitions) (2017-08-21). Read: RAW. TrackMan reports club speed, attack angle and club path at the geometric center of the club head, near the center of gravity, using pre-impact data at maximum compression. For a driver the center-face path differs from the center-of-gravity path by about 3 degrees (center face more outside-in) and the center-face attack angle is about 1 degree higher. For a standard driver a 10 mm toe impact makes the face angle 2 degrees more open at the impact point, and a 10 mm low impact makes dynamic loft 2 degrees lower. For a driver with a spin loft of 10 to 15 degrees, attack angle at ball separation is 4 to 6 degrees steeper than at first touch.

### (d) Spin loft and the D-plane

**Source 1 (primary):** TrackMan, ["What is Spin Loft?"](https://www.trackman.com/blog/golf/spin-loft) (2024-09-23). Read: RAW. Spin loft is the 3D angle between the club head's movement (attack angle and path) and the club face orientation (dynamic loft and face angle). Dynamic loft minus attack angle approximates it, and the approximation drifts as face-to-path grows. Higher spin loft gives higher spin rate and lower smash factor, all else equal. The [Dynamic Loft](https://www.trackman.com/blog/golf/dynamic-loft) page defines dynamic loft as the vertical face orientation at the impact point at maximum compression. Numeric Tour values are in the Anchor 1 supplement.

**D-plane:** TrackMan's Club Data Definitions page names the D-plane as the concept that links Face Angle, Dynamic Loft, Club Path and Attack Angle to ball flight and gives no equation. The equation and the D-plane definition sit in the Tuxen document that could not be read (see (a)). **NOT FOUND in a readable primary source.**

### (e) Landing angle and peak height guidance for irons

TrackMan's ["What is Apex Height?"](https://www.trackman.com/blog/apex-height) (2024-06-28) says the difference in apex height between driver and PW in the Tour averages is only 3 yd (35 and 32 in the 2023 table). It gives no target height. TrackMan's [Carry](https://www.trackman.com/blog/what-is-carry) page defines carry and prints the Tour driver carries. No page found publishes a recommended landing angle or peak height for irons beyond the Tour table columns. A dedicated landing angle page does not exist on TrackMan's site (404 on the probes tried).

**Verdict: PARTIAL.** ANCHORED: TrackMan's plain-language definitions; the launch direction geometry (Source 2 of (a)); face-to-path curvature as eight worked examples and spin axis curvature as four; the measurement offsets. NOT FOUND in a primary text: the start direction shares by club, the D-plane equations, a per-degree curvature law, and target landing angle or peak height for irons. The attack-angle to path relation exists as one forum formula and as TrackMan's qualitative statement.

---

## Anchor 6 — Tiger Woods nine windows

**Status: The concept is PUBLISHED by TaylorMade with Tiger Woods himself. No launch monitor numbers for any window were found.**

**Source 1 (primary for the concept):** TaylorMade Golf, ["Tiger Woods' Nine Windows"](https://www.youtube.com/watch?v=q0mj9Adz0Jw), YouTube video, published 2021-09-21, 539 seconds. Retrieved 2026-09-28. Read: RAW (video page metadata and description). The description says Woods made the Nine Windows drill part of his routine years ago and calls it an example of the control a golfer can have with an iron. It adds that he outlines the objective of the drill and then walks the channel's @trottiegolf through each shot, using his P·7TW irons. The description text reads "High, low, draw, cut". The video itself (its audio and picture) was not watched, so the exact wording Woods uses and any numbers shown on screen are unknown.

**Source 2 (secondary, no windows numbers):** ESPN, ["How Tiger Woods tests a golf ball: 'He's a human launch monitor'"](https://www.espn.com/golf/story/_/id/28685129/how-tiger-woods-tests-golf-ball-human-launch-monitor), Tom VanHaaren, 2020-02-13. Read: SUMMARIZED. Says Woods checks launch angle and spin on 5 and 10 yard shots and shapes shots on purpose, and states no launch monitor values for shot shapes.

**Source 3 (secondary, title only):** Rotary Swing, ["Day 9: How to Use Tiger's Drill to Master the 9 Ball Flights"](https://rotaryswing.com/golf-instruction/golf-ball-striking-how-to/drill-for-how-to-work-the-golf-ball). Read: SUMMARIZED. Refers to Tiger's "9 Shots" drill in a video title, gives no origin source and no numbers. A GolfWRX article titled "Tiger Woods breaks down his famous 'Nine Window' warm-up drill" appeared in search results and returned HTTP 403, so its content was not read.

**The 3 by 3 layout.** The description names height (high, low) and shape (draw, cut) and the title says nine. The read text does not spell out the three heights and three shapes. The design doc's low, mid, high against draw, straight, fade grid is the standard reading of the drill and rests on the title plus general knowledge, not on a passage read this session.

**Launch monitor numbers.** A search blurb attributed some Tiger TrackMan averages to a Rotary Swing page. That page was not fetched and the values are not logged. No source found publishes launch angle, spin or peak height for any of the nine windows.

**Verdict: ANCHORED for the concept and its name (TaylorMade and Tiger Woods, 2021). NOT FOUND for numbers.** The nine-window recipes in the tool are model output, must carry the `modeled` badge, and must not be attributed to Tiger.

---

## Anchor 7 — Aerodynamic coefficients for a golf ball

**Status: One complete, current, published working model exists (lift and drag as functions of spin factor and Reynolds number, plus a spin decay law). It is a spreadsheet by Alan Nathan (University of Illinois) that uses Washington State University measurements and a fit to seven clubs. The classic papers (Bearman and Harvey 1976, Smits and Smith 1994) are reached only through secondary summaries. The three available characterizations disagree with each other on lift and drag at the same spin factor.**

Definitions used across the sources: spin factor S = R x omega / v (ball radius times spin rate over speed); Reynolds number Re; lift coefficient CL; drag coefficient CD. Ball radius in the spin decay paper: 0.02134 m (mass 0.04593 kg).

**Source 1 (working model, current):** Alan M. Nathan, ["Trajectory Calculator: Golf Version"](https://baseball.physics.illinois.edu/trajectory-calculator-golf.html), page updated 2025-02-15. Spreadsheets [imperial](https://baseball.physics.illinois.edu/TrajectoryCalculatorGolf-v2.xlsx) and [metric](https://baseball.physics.illinois.edu/TrajectoryCalculatorGolf-v2m.xlsx). Retrieved 2026-09-28. Read: RAW (the workbooks were fetched and their cell formulas, labels and in-sheet notes read; nothing was executed). The page says the drag and lift come from Lyu et al. ("The Aerodynamics of Golf Balls in Still Air", [Proceedings 2(6):238](https://www.mdpi.com/2504-3900/2/6/238), from WSU measurements) and from Peter Dewhurst's *The Science of the Perfect Swing*, pp. 34 to 35. The workbook's own notes say the drag on S comes from Dewhurst p. 34, the sheet is a "Beta Version For Golf", dated 2023-11-29, with a minor update on 2025-02-14, and the parameters were "optimized for 7 clubs, driver through 5-iron". The page adds that the coefficients are an overall average over several ball types, and that dimple design changes them.

Model as written in the workbook:

- Re is in units of 1e5 (the sheet computes Re at 100 mph as 123,638 for the default ball and air).
- Cd0 = CdL for Re at or below ReLow; Cd0 = CdL + (CdH - CdL) x (Re - ReLow) / (ReHigh - ReLow) between ReLow and ReHigh; Cd0 = CdH for Re at or above ReHigh.
- CD = Cd0 + CdS x S.
- CL = ClAmp x S^0.4.
- Parameter values in the workbook: CdL 1.9451114, CdH 0.1324800, CdS 0.2087217, ClAmp 0.2294096, ReLow 0.5, ReHigh 1.0. With the sheet's Re scale, Re = 1.0 falls at about 81 mph and Re = 0.5 at about 40 mph, so for ball speeds above about 81 mph CD = 0.13248 + 0.20872 x S.
- Default ball: mass 1.62 oz, circumference 5.277 in.
- Spin decay: time constant tau = R / (2.0e-5 x v), spin = initial spin x exp(-t / tau). The imperial sheet gives tau = 14.9 s at 160 mph. The formula matches Smits and Smith's 2.0e-5 coefficient in Source 3.

Values this model returns (computed here from the published parameters, not read from a table), Re above 1e5: at S = 0.075, CD 0.148, CL 0.081; at S = 0.10, CD 0.153, CL 0.091; at S = 0.15, CD 0.164, CL 0.107; at S = 0.20, CD 0.174, CL 0.121; at S = 0.30, CD 0.195, CL 0.142; at S = 0.45, CD 0.226, CL 0.167.

Two flags. (1) The workbook's separate "Cd-Cl" sheet also holds an unlabeled column of 1.99 x S - 3.255 x S^2, which gives 0.225 at S = 0.15 and peaks near 0.304 at S = 0.30. It is not the CL the trajectory sheet uses (that one is 0.107 at S = 0.15). Its source is not stated. (2) The metric workbook computes tau with the ball radius in feet and speed in meters per second, and reads 48.9 s at 71.52 m/s; the imperial workbook, with matching units, reads 14.9 s at 160 mph (the same speed). The imperial one agrees with Source 3's stated 23.8 s at 100 mph. Use the imperial parametrization or fix the units.

**Source 2 (measured ranges, secondary summary of Bearman and Harvey 1976 and Smits and Smith 1994):** J. M. Pallis and R. D. Mehta, ["Aerodynamics and hydrodynamics in sports"](https://people.stfx.ca/smackenz/courses/HK474/Labs/Jump%20Float%20Lab/Pallis%20and%20Mehta%20%20Aerodynamics%20and%20hydrodynamics%20in%20sports.pdf). Retrieved 2026-09-28. Read: RAW (PDF text). Bearman and Harvey (1976, *Aeronautical Quarterly*) tested a large spinning model over a wide range of Re and S. They found CL rose with S at every step, from about 0.08 to 0.25, and CD began to rise for S above 0.1, from about 0.27 to 0.32. The trends did not depend on Reynolds number for 126,000 to 238,000. Smits and Smith (1994, *Science and Golf II*, pp. 340 to 347) measured 40,000 to 250,000 Re and S from 0.04 to 1.4, agreed in general terms with Bearman and Harvey, saw a second drop in CD above Re 200,000 and suggested compressibility as the cause. Their measured spin decay is in Source 3. The full set of Smits and Smith equations was not in any source read this session. A search blurb described a functional form with named constants; the values did not survive a check against the ranges above (its power-law lift would give about 0.006 at S = 0.15), and the blurb is a snippet, so it is not logged.

**Source 3 (spin decay, published law):** Alan M. Nathan, ["The Effect of Spin-Down on the Flight of a Baseball"](https://baseball.physics.illinois.edu/spindown.pdf), 2008-07-14, quoting Smits and Smith (1994) and Tavares, Shannon and Melvin (1998, *Science and Golf III*, pp. 464 to 472). Retrieved 2026-09-28. Read: RAW (PDF text, page image checked). Smits and Smith's golf ball data (mass 0.04593 kg, radius 0.02134 m) show spin-down rate times R squared over v squared is close to linear in S, and independent of Reynolds number for Re from 1.0e5 to 2.5e5. Their law, as printed: d(omega)/dt = -2.0e-5 x (v squared / R squared) x S. The paper says "v in mph" next to the equation and, in a footnote, that the number is 2.0e-5 if v is in m/s. The paper's own worked result, a time constant of 23.8 s at 100 mph, reproduces only with SI units (R / (2.0e-5 x v) = 23.9 s for R = 0.02134 m and v = 44.7 m/s). Use SI. Tavares' radar-based coefficient of moment is CM about 0.012 x S, which the paper converts to 2.5e-5 (time constant 18.9 s at 100 mph).

**Source 4 (modern statement of the fitted form):** W. McNally, J. Lambeth and D. Brekke (Dunlop Sports Americas), ["Combining Physics and Deep Learning Models to Simulate the Flight of a Golf Ball"](https://openaccess.thecvf.com/content/CVPR2023W/CVSports/papers/McNally_Combining_Physics_and_Deep_Learning_Models_To_Simulate_the_Flight_CVPRW_2023_paper.pdf) (CVPR 2023 Workshops). Retrieved 2026-09-28. Read: RAW (PDF text). Dataset: 90,233 shots from a TrackMan 3e (81,209 train, 9,024 validation), robot and player tests. Their baseline model (from Ferguson, McNally and McPhee) writes CL = p1 + p2 S + p3 S^2, CD = p4 + p5 S + p6 S^2 and a moment coefficient CM = p7 S, with S = R ||omega|| / ||v||. The paper does not print the fitted p values. Its network output limits CL and CD to 0 to 0.5 and CM to 0 to 0.02, "based on values observed in previous work". Best validation landing error: 5.60 yd for their model, 6.95 yd for the quadratic baseline. The value to this project is the confirmed functional form and the size of the residual a quadratic form leaves against TrackMan data.

**Source 5 (CFD cross-check at one spin factor):** J. Crabill, F. Witherden and A. Jameson, ["High-Order Computational Fluid Dynamics Simulations of a Spinning Golf Ball"](https://arxiv.org/pdf/1806.00378) (arXiv 1806.00378, *Sports Engineering*). Retrieved 2026-09-28. Read: RAW (PDF text). They read Bearman and Harvey's data as CD about 0.28 and CL about 0.18 at S = 0.15 (CL about 0.16 at S = 0.13, a spinning-to-static drag rise of 5 percent). Their own LES gives CD 0.2469 static and 0.256 spinning at S = 0.15, at a Reynolds number of about 150,000. Kensrud's thesis ([Illinois copy](https://baseball.physics.illinois.edu/kensrudthesis.pdf), 2010) reports the drag crisis for a no-spin golf ball starting near Re 70,000 with a minimum drag of 0.17, and notes Bearman and Harvey's dimpled ball minimum of 0.23.

**Disagreement to carry forward.** At S = 0.15 and high Re, the three characterizations read: Nathan's model CD 0.164, CL 0.107; Bearman and Harvey as read by Crabill CD about 0.28, CL about 0.18; the unlabeled quadratic on Nathan's Cd-Cl sheet CL 0.225. CD differs by 70 percent and CL by a factor of two. The model's coefficients will be a calibration target against the Tour carry column, not a lookup.

**Spin factor range the model must cover.** Derived here from the Anchor 1, 2 and 3 rows, launch ball speed and launch spin with R = 0.02134 m: PGA driver 0.074, LPGA driver 0.088, average amateur driver 0.123, PGA 7 iron 0.29, PGA PW 0.448, LPGA PW 0.481. Nathan's fit covers driver through 5 iron (S from 0.07 to 0.2 at launch, by the arithmetic above). Bearman and Harvey's data end at S = 0.3. Only Smits and Smith reach S = 1.4. Wedge shots sit in the region the best-supported model was not fit to.

**TrackMan, Rapsodo and FlightScope notes.** No technical note publishing CL or CD was found for any of the three in the search. Rapsodo publishes a comparison of its ball flight algorithm against TrackMan and Foresight and was not read for coefficients.

**Verdict: PARTIAL.** ANCHORED: one complete parametric model with published constants (Source 1), a spin decay law (Source 3), the quadratic functional form and the data scale from an independent TrackMan-fitted study (Source 4), and measured ranges from the two classic papers by secondary quote (Sources 2 and 5). NOT VERIFIED: the Smits and Smith lift and drag equations and constants, Lyu et al.'s own fits (the MDPI page returned HTTP 403), and Dewhurst's parametrization (a book, not read).

---

## Gaps and what the model must assume

**Confirmed gaps.**

1. **Amateur irons.** No primary source gives measured amateur club speed, ball speed, launch, spin or carry for any iron. TrackMan's driver-only Combine table and its 6-iron and PW optimizer defaults are all there is. Amateur iron rows must be scaled from the driver row and the Tour club ladder and carry the `modeled` badge. One sanity check available: the Optimizer defaults give a 94 mph golfer's 6-iron club speed as 80 mph, which is 85 percent of the driver, against 82 percent for PGA Tour (94 / 115) and 83 percent for LPGA (80 / 96).
2. **Ideal bands for irons.** No published optimal launch, spin, landing angle or peak height for irons. Use the Tour tables as the "ideal" for Tour presets and the modeled scaling for amateurs, with band widths taken from PING's stated tolerance for the driver (plus or minus 1 degree launch, 300 rpm spin) only where they apply to the driver.
3. **Start direction shares by club.** Unverified (Anchor 5a). The model can carry 0.85 for the driver and 0.75 for irons as stated assumptions, with 0.87 and 0.81 as the second published set and 0.65 for a lob wedge as unattributed chatter. A human should read Tuxen's "TRACKMAN Ball Flight Laws" and replace the assumption.
4. **Curvature law.** Published only as eight face-to-path examples and four spin-axis examples. The spin axis from face-to-path and spin loft is model output and can be checked against the eight examples.
5. **Nine windows.** No numbers exist. Model output only.
6. **Aerodynamics.** Nathan's fit is the only complete set, is fit to driver through 5 iron, and disagrees with Bearman and Harvey's numbers by a wide margin at S = 0.15. The Smits and Smith equations are unread. The wedge S range (0.45 and up) is outside the best-supported fit.
7. **Club path and face angle by club.** TrackMan does not publish Tour or amateur averages for either. The ideal tile for those two must come from shot-shape targets, not from a table.
8. **Bounce and roll.** No source read here covers it. TrackMan's Tour table gives landing angle but no roll-out. Total-distance numbers stay `modeled`.

**Assumptions the model must state.**

- Air is standard sea level unless the tool says otherwise. The Tour tables note that altitude and weather were not taken into account, and the 2010 optimizer charts give no conditions.
- TrackMan reports club speed, attack angle and path at the center of gravity or geometric center. Camera-based monitors (and PING's chart, when the reader uses one) read attack angle about 2 degrees higher. Say which convention the sliders follow.
- The 2023 Tour set is current on TrackMan pages as of 2026-09-28. Older sets (2019-01) are logged for comparison only.
- Published smash factor does not equal published ball speed over club speed on some rows (LPGA up to 0.03, amateur average golfer 1.44 against 1.415). Calibrate on speeds and treat the smash column as a check, or the reverse, and say which.
- Ball: mass 0.04593 kg (1.620 oz) and diameter 0.04267 m (1.680 in), the USGA Rules of Golf equipment standards (ball weight limit and minimum diameter). Anchor 7 quotes the same mass and a radius of 0.02134 m, which agrees with half the diameter. Added 2026-09-28 for task 004.2.
- Nathan's workbook was re-read at task 004.2 (cell values and formulas, nothing executed) and confirms CdL 1.9451114, CdH 0.13248, CdS 0.2087217, ClAmp 0.2294096, ReLow 0.5, ReHigh 1, air density 1.1944 kg/m^3 at 70 F and 50 percent humidity, and Re 123,638 at 100 mph. Its default shot (160 mph, 11 deg, 3000 rpm) lands at 259.3 yd after 4.99 s with an apex near 19.7 yd. The Re-dependent drag branch (CdL 1.945 at 40 mph rising to CdH at 81 mph) makes every Tour iron row unreachable, and the flight model turns it off (see data.py, RE_DEPENDENT_DRAG).
- Tour tables are pooled averages of competition and range shots. The model reproduces an average shot, not a distribution, so dispersion needs its own source.

**Discrepancies logged, not resolved.**

- PGA Tour 2019 to 2023: driver club speed 113 to 115, ball speed 167 to 171, spin 2686 to 2545, launch 10.9 to 10.4, attack angle -1.3 to -0.9, carry 275 to 282.
- Tour examples on TrackMan's face-to-path page use 2019 carries; the Tour table we use is 2023.
- LPGA driver dynamic loft minus attack angle (12.7) against published spin loft (15.0).
- TrackMan Combine driver speeds by handicap against the Golf.com 2021 ranges.
- Shot Scope 238 yd driver label (15 or 25 handicap) inside one page.
- MG Golf 5-iron carry, 5 handicap 183 against 10 handicap 187.
- Nathan's spin decay equation "v in mph" note against its SI-consistent number; the metric workbook's radius unit.
- Optimal driver launch and spin: TrackMan 2010 carry and total charts against PING 2019 (Anchor 4).
- Aerodynamic coefficients at S = 0.15 across three sources (Anchor 7).

**Leads that need a human with a normal browser.**

- Tuxen, "TRACKMAN Ball Flight Laws" (Yumpu listing above). Wanted: launch direction weighting by club, D-plane equations.
- MyGolfSpy iron distance chart and driver optimal launch and spin chart.
- Lyu et al., Proceedings 2(6):238 (MDPI), for the fitted coefficients; Smits and Smith 1994 for their equations.
- The TaylorMade video for whatever Tiger says about heights and shapes.
- The PING Proving Grounds "Unlocking Distance: Launch Conditions and Angle of Attack" page, to confirm the 2019 chart against PING's own site.
