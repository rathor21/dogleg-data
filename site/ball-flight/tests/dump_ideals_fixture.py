"""Writes site/ball-flight/tests/ideals_fixture.json: Python ideal_bands() output
at club speeds and attack angles other than the preset, for parity.mjs.

    analysis/004-ball-flight-laws/.venv/bin/python site/ball-flight/tests/dump_ideals_fixture.py

Each point is {club, player, club_speed_mph, attack_deg, bands}. bands maps the
exported metric name to {lo, hi, target, modeled, published?, detail?}. A null
club_speed_mph or attack_deg means "the preset value" (the function default).
Points cover interior values, clamped optimizer lookups (driver speed under 75
or over 120 mph, attack past +-5 for TrackMan and +-10 for PING, ball speed past
the PING grid) and the domain edges. `errors` lists inputs Python rejects (NaN is written as the string "NaN").
Full double precision, deterministic. An optional argument names another output
file (the pytest wrapper uses it to check the committed fixture is current).
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, "..", "..", "..", "analysis", "004-ball-flight-laws"))
sys.path.insert(0, PKG)

import export  # noqa: E402
import ideals  # noqa: E402

# (club, player, club speed or None, attack or None)
POINTS = [
    # driver, interior
    ("driver", "pga", 105.0, -2.0), ("driver", "pga", 110.5, 1.5), ("driver", "amateur", 88.0, -3.0),
    ("driver", "amateur", 100.0, 4.0), ("driver", "lpga", 85.0, 2.0), ("driver", "lpga", 96.0, None),
    ("driver", "pga", None, 3.0), ("driver", "pga", 120.0, -5.0),
    # driver, clamped: speed below and above the TrackMan grid, attack past both grids
    ("driver", "amateur", 60.0, -1.0), ("driver", "amateur", 45.0, -9.0), ("driver", "pga", 135.0, 0.0),
    ("driver", "pga", 140.0, 10.0), ("driver", "lpga", 70.0, -10.0), ("driver", "pga", 115.0, 8.0),
    ("driver", "pga", 40.0, -10.0),
    # non-driver, scaled speed and attack
    ("7i", "pga", 80.0, None), ("7i", "pga", 100.0, -6.0), ("7i", "amateur", 70.0, -2.0),
    ("7i", "lpga", 85.0, 3.0), ("pw", "amateur", 60.0, None), ("pw", "pga", 95.0, -8.0),
    ("5w", "lpga", 88.0, 1.0), ("3w", "pga", 120.0, -1.0), ("hybrid", "amateur", 75.0, -2.5),
    ("3i", "lpga", 90.0, None), ("3i", "pga", 40.0, -10.0), ("9i", "pga", 140.0, 10.0),
    ("6i", "amateur", 90.0, None), ("4i", "pga", None, None),
]
BAD = [
    ("7i", "pga", 39.9, None), ("7i", "pga", 140.1, None), ("driver", "pga", 100.0, 10.1),
    ("driver", "pga", 100.0, -10.1), ("7i", "pga", float("nan"), None), ("7i", "pga", None, float("nan")),
]


def _enc(v):
    """NaN is not JSON, so it is written as the string "NaN"."""
    return "NaN" if v is not None and v != v else v


def clean_band(b):
    out = {k: b[k] for k in ("lo", "hi", "target", "modeled") if k in b}
    if "published" in b:
        out["published"] = b["published"]
    if "detail" in b:
        out["detail"] = b["detail"]
    return out


def main():
    points = []
    for club, player, speed, aoa in POINTS:
        raw = ideals.ideal_bands(club, player, speed, aoa)
        bands = {export.METRIC_NAMES.get(m, m): clean_band(b) for m, b in raw.items()}
        points.append({"club": club, "player": player, "club_speed_mph": speed, "attack_deg": aoa, "bands": bands})
    errors = []
    for club, player, speed, aoa in BAD:
        try:
            ideals.ideal_bands(club, player, speed, aoa)
        except ValueError as e:
            errors.append({"club": club, "player": player, "club_speed_mph": _enc(speed), "attack_deg": _enc(aoa),
                           "message": str(e)})
        else:
            raise RuntimeError(f"expected ideal_bands to reject {(club, player, speed, aoa)}")
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "ideals_fixture.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"note": "Python ideal_bands() at non-preset club speeds and attack angles. Regenerate with "
                           "dump_ideals_fixture.py. null speed or attack means the preset value.",
                   "points": points, "errors": errors}, fh, sort_keys=True, allow_nan=False, indent=None,
                  separators=(",", ":"))
        fh.write("\n")
    print(f"wrote {path}: {len(points)} points, {len(errors)} errors")


if __name__ == "__main__":
    main()
