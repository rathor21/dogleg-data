| round | change | per-round test | blind tournament test | kept |
|---|---|---|---|---|
| 0 | baseline | 0.469 | 0.547 | |
| 1 | first-screen budget per mode | 0.609 | 0.682 | yes |
| 2 | tracer sideways widened ~2x + disclosure note | 0.495 | not re-judged | reverted |
| 3 | top-down shot map inset | 0.599 | 0.693 | reverted (tie with v1) |
| 4 | shot map made quieter | 0.474 | not re-judged | reverted |
| 5 | tiles and key numbers fit to the fold, one-line notes | not per-round judged | 0.740 | yes |

**Recommended change.** Ship v1 + v5 (commits 194c0df and 9ba178b on analysis-004-hillclimb): the first screen now holds what each teaching mode needs, and the tile row fits the fold with no cut or wrapped notes.

**Versus baseline.** Blind tournament on the 12 held-out test scenarios, same two judges for every variant: baseline 0.547 -> v5 0.740 (+0.193, 95% CI +0.10 to +0.28); v5 beats v1 by +0.057 (CI +0.01 to +0.12). Guardrails held: 0 console errors, 0 overflow, 0 serious axe, input p95 16.4 ms (15.9 at baseline), median load 243 ms (252), JS 53 KB (52).

**Why trust this.** Judge calibration passed (blank page 0/8; hidden label failed the right claims). A no-change control re-judge of v1 showed session-to-session judge drift of about 0.05 on the design mean (c6 hierarchy swung 0.70 -> 0.37 on identical images), larger than one-round effects; so the final call uses one blind, shuffled tournament where every variant meets the same judges. Tournament inter-rep agreement 0.857.

**What else was tried.** Curve legibility from behind the ball (c2) was attacked three ways: widening the tracer (v2) read as debug text once disclosed; a shot map inset (v3) raised c2 (0.71 -> 0.88 in the tournament) but tied v1 overall because it cost hierarchy; a quieter map (v4) lost more. Next ideas: v5 plus a refined shot map (it is the only c2 lever that worked), tap targets on touch (small_targets rose 14.8 -> 17.5 with v1), and a tighter c6 rubric definition to cut judge drift.
