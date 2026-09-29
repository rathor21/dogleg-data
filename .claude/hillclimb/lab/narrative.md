| round | change | test | train | load ms | input p95 ms | kept |
|---|---|---|---|---|---|---|
| 0 | baseline | 0.469 | 0.448 | 234 | 15.9 | |
| 1 | first-screen budget per mode | 0.609 | 0.604 | 207 | 15.7 | yes |
| 2 | tracer sideways widened ~2x + disclosure note | 0.495 | 0.576 | 212 | 16.2 | reverted |
| 3 | top-down shot map inset on the range | 0.599 | 0.677 | 243 | 17.4 | pending (flat on test) |

Best so far: v1 (test 0.609). v3's shot map made curve direction readable (test c2 0.67 -> 0.79) but pulled focus from the shot (test c6 0.67 -> 0.29), netting flat. Round 4 keeps the map and makes it subordinate.
