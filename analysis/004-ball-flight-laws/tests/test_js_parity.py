"""Runs the JS port's parity test (site/ball-flight/tests/parity.mjs) under node.

The node script loads the JSON that export.py wrote to site/ball-flight/data,
replays every golden case through site/ball-flight/flight.js and compares it
with the Python output. Skipped when node is not installed. Regenerate the
JSON with `python export.py` after any model change, or this fails.
"""

import os
import shutil
import subprocess

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
SCRIPT = os.path.join(REPO, "site", "ball-flight", "tests", "parity.mjs")


def _node():
    node = shutil.which("node")
    if node is None and os.path.exists("/usr/local/bin/node"):
        node = "/usr/local/bin/node"
    return node


def test_js_matches_python():
    node = _node()
    if node is None:
        pytest.skip("node is not installed, so site/ball-flight/tests/parity.mjs cannot run")
    proc = subprocess.run([node, SCRIPT], cwd=REPO, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, f"JS parity test failed:\n{proc.stdout}\n{proc.stderr}"
    assert "PARITY OK" in proc.stdout
