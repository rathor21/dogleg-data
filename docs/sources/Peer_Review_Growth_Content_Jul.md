# Peer Review

**Work reviewed:** Growth and content batch, 2026-07-12 — 002 launch posts (`002_Post_Copy_LinkedIn.md`, `002_Post_Copy_X.md`), Content Queue updates (Post 4 completion, 002 launch week, Posts 6-8, Post 5 voice fix), Outreach Pitches upgrade (anchor options, sequencing decision)
**Author:** Claude, direction by Sunny
**Reviewer:** Claude (numbers re-derived from source CSVs and direct model calls, not re-read from the drafts)
**Review type:** Numbers, sourcing, voice, platform mechanics
**Date:** 2026-07-12

---

## Method

1. Re-derived every number quoted in the new copy from `analysis/002-tee-shot-distance/outputs/002_results.csv`, `data.py`, and direct `model.expected_score` / `model.club_verdict` calls, and from `Fairway_vs_Rough_Post/Fairway_vs_Rough_Data.csv` for 001 numbers.
2. Counted every tweet programmatically with the t.co link normalized to 23 characters.
3. Swept all four content files for em dashes and filler adverbs in post bodies (headers keep the repo's title convention).
4. Cross-checked the 230/28/259 rounding convention against `Peer_Review_002_Tee_Shot.md`, which sanctions it.

## Must Fix

None shipped. One caught during drafting, recorded because the standing habit is publishing what broke:

| # | Location | Issue | Resolution |
|---|---|---|---|
| 1 | Content Queue, Post 7 draft | First draft restated the tier-10 average drive as a bare number beside the rounded 230 cost line. Any reader subtracting would get 29 and flag a mismatch with the published caption's "28 yards under" (which comes from the unrounded 231.2 threshold against the 259 average: 27.8, rounds to 28). | Post 7 now reuses the caption's exact sanctioned phrasing, and a production note under the post explains the trap so future copy avoids it. |

## Should Fix

None open.

## Minor / Optional

| # | Location | Note |
|---|---|---|
| 1 | Content Queue, Post 5 | "where the ball actually lands" carried a banned filler adverb from the original draft; removed. |
| 2 | Outreach sequencing | The recommended slip of the Golfwell pitch from Jul 16 to Jul 21 is a judgment call, not a data finding. The counter-case (a recent episode with a direct fairway-vs-rough moment) is documented in the file with instructions to ignore the slip. |
| 3 | X thread, tweet 7 | Tags Stagner only, naming Shot Scope/MyGolfSpy/Broadie without handles. This matches the 001 thread's convention. If the tag-every-source rule is read strictly, add @MyGolfSpy; left at author's discretion. |

## Verification record

| Claim in new copy | Recomputed | Match |
|---|---|---|
| 230 on a 360-yd par 4, tier 10 | CSV threshold 231.2, rounds to 230 (sanctioned in 002 review) | Yes |
| 28 yards under tier average | 259 − 231.2 = 27.8, rounds to 28 (sanctioned in 002 review) | Yes |
| Cost line 218 / average 236, tier 15 at 400 | CSV 217.8; `data.py` DRIVER[15] mean 236.0 | Yes |
| 220 vs 236 costs 0.09 | `expected_score` delta 0.0868 | Yes |
| 3-wood pays 0.15, buys back 0.07, net 0.08 (15 hcp, 400 yd) | `club_verdict` wood−driver = 0.0763; decomposition figures match caption | Yes |
| Driver wins all 70 cells, worst case 0.12 | 7 tiers × 10 lengths, all driver-best; max wood price 0.1203 at (0, 480) | Yes |
| Scratch needs about 80 more yards than tier 30 | 256.1 − 178.3 = 77.8 at 400 yd | Yes |
| Calibration 0.0001, Monte Carlo 0.003, six bands | Matches post-resolution caption and article (0.0021 measured, 0.003 published bound) | Yes |
| 75 / 23 / 17 / 12 at 150 yd (001, Posts 3-5 context) | CSV: 75.0 / 23.0 / 17.0 / 11.8 | Yes |
| 20-hcp crossover at 240-250 (Post 3) | CSV: hcp20 worth −1.0 at 240 | Yes |
| All 7 tweets ≤ 280 chars | 252-279, link normalized to 23 | Yes |

## Sign-off

- [x] **Approved** — one must-fix caught and resolved before delivery; minors at author's discretion.

**Reviewer sign-off:** Claude — 2026-07-12
