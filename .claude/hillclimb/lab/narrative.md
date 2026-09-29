| round | change | test | train | load ms | input p95 ms | kept |
|---|---|---|---|---|---|---|
| 0 | baseline | 0.469 | 0.448 | 234 | 15.9 | |
| 1 | first-screen budget per mode | 0.609 | 0.604 | 207 | 15.7 | yes |
| 2 | tracer sideways widened ~2x + disclosure note | 0.495 | 0.576 | 212 | 16.2 | reverted |

Best so far: v1 (test 0.609). v2 made curves readable on train (c2 0.39 -> 0.81) but the on-range disclosure note read as debug text, dropping polish (c8 0.73 -> 0.20) and defects (c5 0.30 -> 0.13); test fell outside noise, so it was reverted. Next: attack curve legibility with a true-scale feature instead of a distortion.
