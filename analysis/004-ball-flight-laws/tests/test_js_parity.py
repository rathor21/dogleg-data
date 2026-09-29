"""Runs the JS port's parity test (site/ball-flight/tests/parity.mjs) under node.

The node script loads the JSON that export.py wrote to site/ball-flight/data,
replays every golden case through site/ball-flight/flight.js and compares it
with the Python output. Skipped when node is not installed. Regenerate the
JSON with `python export.py` after any model change, or this fails. The ideal
band fixture site/ball-flight/tests/ideals_fixture.json comes from
dump_ideals_fixture.py and is checked for staleness here too.
"""

import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
TESTS_DIR = os.path.join(REPO, "site", "ball-flight", "tests")
SCRIPT = os.path.join(TESTS_DIR, "parity.mjs")
FIXTURE = os.path.join(TESTS_DIR, "ideals_fixture.json")
DUMP = os.path.join(TESTS_DIR, "dump_ideals_fixture.py")
NODE_FALLBACKS = ("/usr/local/bin/node", "/opt/homebrew/bin/node")


def _node():
    node = shutil.which("node")
    if node is None:
        node = next((p for p in NODE_FALLBACKS if os.path.exists(p)), None)
    return node


def test_ideals_fixture_is_current(tmp_path):
    out = tmp_path / "ideals_fixture.json"
    subprocess.run([sys.executable, DUMP, str(out)], cwd=REPO, check=True, capture_output=True, timeout=120)
    with open(FIXTURE, "rb") as fh:
        committed = fh.read()
    assert out.read_bytes() == committed, (
        "site/ball-flight/tests/ideals_fixture.json is stale, regenerate it with "
        "analysis/004-ball-flight-laws/.venv/bin/python site/ball-flight/tests/dump_ideals_fixture.py"
    )


def test_js_matches_python():
    node = _node()
    if node is None:
        pytest.skip("node is not installed, so site/ball-flight/tests/parity.mjs cannot run")
    proc = subprocess.run([node, SCRIPT], cwd=REPO, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, f"JS parity test failed:\n{proc.stdout}\n{proc.stderr}"
    assert "PARITY OK" in proc.stdout
