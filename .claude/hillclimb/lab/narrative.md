| round | change | test | train | load ms | input p95 ms | small targets |
|---|---|---|---|---|---|---|
| 0 | baseline | 0.469 | 0.448 | 234 | 15.9 | 14.8 |
| 1 | first-screen budget per mode (chrome trimmed, range capped, tiles/recipe/compare above the fold) | 0.609 | 0.604 | 207 | 15.7 | 17.6 |

Best so far: v1 (test +0.14, CI +0.04 to +0.25). The first screen now holds what each teaching mode needs. Remaining weak claims: c5 layout defects 0.30, c2 flight legibility 0.50 (phone range got shorter), c7 teaching fit 0.45.
