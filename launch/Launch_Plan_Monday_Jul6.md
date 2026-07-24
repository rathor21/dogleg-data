# Dogleg Data — Monday Launch Plan (July 6, 2026)

Site reviewed and verified July 3. Decision made July 3: skip the holiday-weekend window, launch everything Monday. Final post copy lives in `Fairway_vs_Rough_Post/Post_Copy_LinkedIn.md` and `Post_Copy_X.md`, dashboard links now filled in.

## Site review verdict: ready

Checked live on production July 3.

| Check | Result |
|---|---|
| Pages resolve: /, /fairway-vs-rough/, /fairway-vs-rough/dashboard, /cite/, /about/, percentages-card.pdf | All live, correct titles, OG images, canonical URLs |
| Buttondown | Account live at buttondown.com/DoglegData; form action on both signup forms matches. One test left for you (below) |
| Numbers, re-derived from `Fairway_vs_Rough_Data.csv` | Card PDF, article, charts, and both posts agree: 75/23/17/12 at 150 yds; severity ladder 8/17/29 (light ×0.5, deep ×1.7); anecdote break-even 7.5 yds at the 160-yd ball, matching chart 2's panel |
| Peer review | Signed off July 1 (`Peer_Review_Rebrand_Addendum.md`); 7.5-vs-8 wording already documented there as a disclosed minor, direction conservative |
| 404 page, sitemap, robots.txt, llms.txt | Present |

Two open items, neither a blocker:

1. **Analytics beacon is still commented out on all five pages.** Without it you get zero launch-day traffic data. Fix before Monday: Cloudflare dashboard → Analytics & Logs → Web Analytics → Add site (doglegdata.com), copy the token, replace `YOUR_TOKEN_HERE` and remove the comment markers on all five HTML files, then `npx wrangler deploy`.
2. Homepage nav has no Cite link (the footer covers it). Cosmetic; fix whenever.

## Before Monday (30-45 minutes, this weekend)

- [ ] **Test the signup end to end with your own email.** Confirm the Buttondown welcome email arrives and carries the link to https://doglegdata.com/assets/percentages-card.pdf. This is the one untested piece of the funnel.
- [ ] Analytics token in, beacon uncommented on all five pages, redeployed (item 1 above)
- [ ] @DoglegData on X: bio, banner, avatar per `brand/bios_and_handles.md`; DMs open
- [ ] LinkedIn headline updated: "Founder, Dogleg Data | Golf analytics from 1B+ real shots"
- [ ] Warm list finished in `launch/Warm_List.csv`, one personal note per name
- [ ] Open the dashboard on your phone once; drag the sliders
- [ ] Block two 2-hour reply windows on Monday's calendar

## Monday run of show

**8:30 AM — LinkedIn** (personal profile)
- Post the main text from `Post_Copy_LinkedIn.md`
- Carousel, 5 images in this order: chart1_handicap_breakeven, chart2_severity_scramble, chart4_tenyard_gap, chart5_landing_pattern, chart3_montecarlo_gir
- No link and no hashtags in the body. First comment immediately after publishing: the dashboard link + sources block from the same file
- Send the LinkedIn half of the warm-list DMs
- Reply to every comment for 2 hours

**3:30 PM — X** (@DoglegData)
- 9-tweet thread from `Post_Copy_X.md`, images at the marked tweets, link only in tweet 9
- Pin the thread
- Send the X half of the warm-list DMs
- Second 2-hour reply window

Holding the thread to Tuesday 9 AM instead gives it its own news cycle and matches the original spacing rule; same-day works if you want one launch day. Either way, keep the two posts at least 6 hours apart.

## After Monday

The rest of the sequence is unchanged from `Launch_Day_Kit.md`, shifted to the new anchor: lead magnet post ~Jul 9, r/golf ~Jul 10, crossover post Jul 13, Product Hunt Jul 14, peer-review post Jul 15, Golfwell pitch once four posts are live. Reply-with-a-chart bank in `Content_Queue.md` covers the comment threads.
