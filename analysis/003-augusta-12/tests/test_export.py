"""Tests for the export seam (issue #10): outputs/003_sandbox_grids.json
and outputs/003_manifest.json.

A session-scoped fixture runs export.main() once and hands every test the
same in-memory JSON plus the raw bytes written to disk, so the ~3-second
export cost (see export.py's module docstring on the vectorized grid
builder) is paid once for the whole file, not once per test.

Three groups of checks:

  1. Sandbox grids: bilinear round-trip against model.expected_score and
     against export.score_and_region_probs (the slow, obviously-correct
     per-aim-point mirror), optimum blocks matching outputs/003_results.csv
     exactly, and interpolation sanity (a midpoint lies between its
     corners).

  2. Manifest: every shot's landing reclassifies to its recorded region,
     every outcome_class matches the spec's designated bucket for that
     shot, the recorded seed reproduces the landing, the five tee
     positions are distinct and inside the tee box, landmarks_px matches
     art/sketch_coords.json, and the camera block matches art/sketch.py's
     own module constants.

  3. export.main() determinism: running it again reproduces the same
     bytes.
"""
import json
import os

import numpy as np
import pytest

import data
import model
import art.sketch as sketch
import export

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The spec's designated outcome bucket for each of the five curated shots
# (see export.SHOT_SPECS' docstring / the issue's shot list). "short_sided"
# reads as valid wherever the spec says "or short-sided".
DESIGNATED_OUTCOME_CLASSES = {
    "pin_hunter": {"short_sided", "bunker", "water"},
    "safe_center": {"green"},
    "draw": {"green"},
    "fade": {"bunker", "short_sided"},
    "under_clubbed": {"water"},
}


@pytest.fixture(scope="session")
def exported():
    export.main()
    with open(export.GRIDS_PATH, "rb") as f:
        grids_bytes = f.read()
    with open(export.MANIFEST_PATH, "rb") as f:
        manifest_bytes = f.read()
    return {
        "grids": json.loads(grids_bytes),
        "manifest": json.loads(manifest_bytes),
        "grids_bytes": grids_bytes,
        "manifest_bytes": manifest_bytes,
    }


# ---------------------------------------------------------------------------
# Sandbox grids
# ---------------------------------------------------------------------------

ROUND_TRIP_COMBOS = [(15, "sunday", False), (10, "center", True)]


def test_grid_builder_matches_expected_score_unrounded():
    """export.build_grid_for_combo's vectorized values match
    model.expected_score exactly (to 1e-6) at every 5th node in each axis,
    before the 4-decimal rounding the JSON file applies for storage."""
    for tier, pin, wind in ROUND_TRIP_COMBOS:
        score, p_water, _p_green = export.build_grid_for_combo(tier, pin, wind)
        pin_x, pin_y = data.PINS[pin]["x"], data.PINS[pin]["y"]
        for ci in range(0, len(export.CARRY_AXIS), 5):
            for li in range(0, len(export.LATERAL_AXIS), 5):
                carry = export.CARRY_AXIS[ci]
                lateral = export.LATERAL_AXIS[li]
                aim = (pin_x + lateral, pin_y + carry)
                exact = model.expected_score(tier, pin, aim, wind=wind)
                assert abs(float(score[ci, li]) - exact) < 1e-6, (tier, pin, wind, carry, lateral)

                sigma_d, sigma_l, mean_shift_y = export._oval_and_mean_shift(tier, wind)
                _s, pw, _pg = export.score_and_region_probs(sigma_d, sigma_l, tier, pin, aim, mean_shift_y)
                assert abs(float(p_water[ci, li]) - pw) < 1e-6, (tier, pin, wind, carry, lateral)


def test_sandbox_lookup_round_trip_against_stored_grid(exported):
    """sandbox_lookup at exact grid nodes (every 5th node per axis)
    reproduces model.expected_score within the file's own stated 4-decimal
    rounding, and p_water matches the score_and_region_probs helper
    integral at the same tolerance, for at least two (tier, pin, wind)
    combinations."""
    grids = exported["grids"]
    for tier, pin, wind in ROUND_TRIP_COMBOS:
        pin_x, pin_y = data.PINS[pin]["x"], data.PINS[pin]["y"]
        sigma_d, sigma_l, mean_shift_y = export._oval_and_mean_shift(tier, wind)
        for ci in range(0, len(export.CARRY_AXIS), 5):
            for li in range(0, len(export.LATERAL_AXIS), 5):
                carry = export.CARRY_AXIS[ci]
                lateral = export.LATERAL_AXIS[li]
                looked_up = export.sandbox_lookup(grids, tier, pin, wind, lateral, carry)

                aim = (pin_x + lateral, pin_y + carry)
                exact = model.expected_score(tier, pin, aim, wind=wind)
                assert abs(looked_up["score"] - exact) < 5e-5

                _s, pw, _pg = export.score_and_region_probs(sigma_d, sigma_l, tier, pin, aim, mean_shift_y)
                assert abs(looked_up["p_water"] - pw) < 5e-5


def test_optimum_blocks_match_results_csv_exactly(exported):
    grids = exported["grids"]
    results = export.load_results_csv()
    for (tier, pin, wind), row in results.items():
        cell = grids["cells"][f"{tier}|{pin}|{int(wind)}"]
        assert cell["optimum"]["lateral_offset_yd"] == pytest.approx(row["aim_lateral_offset_yd"], abs=1e-9)
        assert cell["optimum"]["carry_adjustment_yd"] == pytest.approx(row["aim_carry_adjustment_yd"], abs=1e-9)
        assert cell["optimum"]["score"] == pytest.approx(row["score_optimum"], abs=1e-9)
        assert cell["score_at_pin"] == pytest.approx(row["score_at_pin"], abs=1e-9)
        assert cell["score_center_aim"] == pytest.approx(row["score_center_aim"], abs=1e-9)
        assert cell["verdict_label"] == row["verdict_label"]


def test_bilinear_interpolation_midpoint_between_corners(exported):
    grids = exported["grids"]
    tier, pin, wind = 15, "sunday", False
    key = f"{tier}|{pin}|{int(wind)}"
    score_grid = grids["cells"][key]["score"]
    lateral_axis = grids["axes"]["lateral_offset_yd"]
    carry_axis = grids["axes"]["carry_adjustment_yd"]

    ci, li = 10, 10
    mid_lateral = (lateral_axis[li] + lateral_axis[li + 1]) / 2.0
    mid_carry = (carry_axis[ci] + carry_axis[ci + 1]) / 2.0
    looked_up = export.sandbox_lookup(grids, tier, pin, wind, mid_lateral, mid_carry)

    corners = [score_grid[ci][li], score_grid[ci][li + 1], score_grid[ci + 1][li], score_grid[ci + 1][li + 1]]
    assert min(corners) <= looked_up["score"] <= max(corners)


def test_sandbox_lookup_clamps_outside_axes(exported):
    grids = exported["grids"]
    inside = export.sandbox_lookup(grids, 15, "sunday", False, 20.0, 45.0)
    beyond = export.sandbox_lookup(grids, 15, "sunday", False, 999.0, 999.0)
    assert inside["score"] == pytest.approx(beyond["score"], abs=1e-9)


def test_grids_schema_and_size(exported):
    grids = exported["grids"]
    assert grids["schema"] == "dogleg-003-sandbox-grids/1"
    assert grids["tiers"] == list(data.TIERS)
    assert set(grids["pins"]) == set(data.PINS)
    assert grids["axes"]["lateral_offset_yd"][0] == -20.0
    assert grids["axes"]["lateral_offset_yd"][-1] == 20.0
    assert grids["axes"]["carry_adjustment_yd"][0] == -20.0
    assert grids["axes"]["carry_adjustment_yd"][-1] == 45.0
    assert len(grids["cells"]) == len(data.TIERS) * len(data.PINS) * 2
    size = os.path.getsize(export.GRIDS_PATH)
    assert size < 2_200_000, f"003_sandbox_grids.json grew to {size} bytes"


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def test_shot_landings_reclassify_to_recorded_region(exported):
    for shot in exported["manifest"]["shots"]:
        region, short_sided = model.region_at(shot["landing"]["x"], shot["landing"]["y"], shot["pin"])
        assert region == shot["region"]
        assert short_sided == shot["short_sided"]


def test_shot_outcome_classes_match_designated_buckets(exported):
    for shot in exported["manifest"]["shots"]:
        allowed = DESIGNATED_OUTCOME_CLASSES[shot["id"]]
        assert shot["outcome_class"] in allowed, (shot["id"], shot["outcome_class"], allowed)


def test_shot_landing_reproducible_from_recorded_seed(exported):
    """Regenerating from the recorded seed reproduces the landing exactly.

    Must draw the SAME-sized arrays export._draw_landing draws (its
    max_samples default, not just sample_index + 1 values): the rng is
    shared across the sequential ys-then-xs calls, so its state after
    drawing ys depends on how many elements that call requested, and only
    matches export.py's own draw when the array sizes match exactly.
    """
    for shot in exported["manifest"]["shots"]:
        tier, pin, wind = shot["tier"], shot["pin"], shot["wind"]
        aim = (shot["aim"]["x"], shot["aim"]["y"])
        rng = np.random.default_rng(shot["seed"])
        sigma_d, sigma_l = model.oval_for_tier(tier)
        mean_shift_y = 0.0
        if wind:
            mean_shift_y = -data.WIND["carry_penalty_yd"]
            sigma_d = sigma_d * data.WIND["dispersion_inflation"]
            sigma_l = sigma_l * data.WIND["dispersion_inflation"]
        mean_x, mean_y = aim[0], aim[1] + mean_shift_y
        ys = rng.normal(mean_y, sigma_d, export.SHOT_DRAW_MAX_SAMPLES)
        xs = rng.normal(mean_x, sigma_l, export.SHOT_DRAW_MAX_SAMPLES)
        i = shot["sample_index"]
        x, y = float(xs[i]), float(ys[i])
        assert x == pytest.approx(shot["landing"]["x"], abs=1e-3)
        assert y == pytest.approx(shot["landing"]["y"], abs=1e-3)


def test_tee_positions_distinct_and_inside_tee_box(exported):
    shots = exported["manifest"]["shots"]
    xs = [s["tee"]["x"] for s in shots]
    assert len(set(xs)) == len(xs) == 5
    for shot in shots:
        assert abs(shot["tee"]["x"]) <= sketch.TEE_BOX_HALF_WIDTH_YD
        assert sketch.TEE_BOX_BACK_YD <= shot["tee"]["y"] <= 0.0


def test_landmarks_px_matches_sketch_coords_json(exported):
    with open(os.path.join(HERE, "art", "sketch_coords.json")) as f:
        expected = json.load(f)
    assert exported["manifest"]["landmarks_px"] == expected


def test_camera_matches_sketch_module_constants(exported):
    camera = exported["manifest"]["camera"]
    assert camera["canvas"] == {"width": sketch.CANVAS_W, "height": sketch.CANVAS_H}
    assert camera["horizon_px"] == sketch.HORIZON_PX
    assert camera["y_min_yd"] == sketch.Y_MIN_YD
    assert camera["y_max_yd"] == sketch.Y_MAX_YD
    assert camera["ground_near_px"] == sketch.GROUND_NEAR_PX
    assert camera["tee_front_px"] == sketch.TEE_FRONT_PX
    assert camera["mid_px"] == sketch.MID_PX
    assert camera["gamma_x"] == sketch.GAMMA_X
    assert camera["near_half_width_px"] == sketch.NEAR_HALF_WIDTH_PX
    assert camera["far_half_width_px"] == sketch.FAR_HALF_WIDTH_PX
    assert camera["frame_half_width_yd"] == sketch.FRAME_HALF_WIDTH_YD

    _regions, landmarks = sketch.build_scene()
    assert camera["y_break_yd"] == landmarks["y_break_yd"]


def test_manifest_schema(exported):
    manifest = exported["manifest"]
    assert manifest["schema"] == "dogleg-003-manifest/1"
    assert len(manifest["shots"]) == 5
    assert set(manifest["region_codes"]) == {
        "green", "front_bunker", "back_bunker", "creek",
        "long_trouble", "long_rough", "greenside_rough",
    }
    for key, points in manifest["scatter"].items():
        assert len(points["points"]) == 1000
        for x, y, code in points["points"][:5]:
            assert isinstance(code, int)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_export_main_is_deterministic(exported):
    export.main()
    with open(export.GRIDS_PATH, "rb") as f:
        assert f.read() == exported["grids_bytes"]
    with open(export.MANIFEST_PATH, "rb") as f:
        assert f.read() == exported["manifest_bytes"]
