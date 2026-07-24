"""Copy the five 002 charts into the site tree.

Full-size renders go to site/assets/img/002_*.png; 1280x720 cite renders go
to site/assets/cite/002_*_1280x720.png. Chart scripts must have been run
(normal and CITE_EXPORT=1) first; this script re-runs them to be safe, then
copies. Idempotent.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, "..", "..", "site"))
IMG = os.path.join(SITE, "assets", "img")
CITE = os.path.join(SITE, "assets", "cite")

CHARTS = [
    ("chart1.py", "chart1_cost_line"),
    ("chart2.py", "chart2_flat_zone"),
    ("chart3.py", "chart3_decomposition"),
    ("chart4.py", "chart4_club_map"),
    ("chart5.py", "chart5_quote_card"),
    ("chart6.py", "chart6_bailout"),
]

env = dict(os.environ, CITE_EXPORT="1")
for script, _ in CHARTS:
    subprocess.run([sys.executable, os.path.join(HERE, script)], check=True, cwd=HERE,
                   env=env, capture_output=True)

for _, name in CHARTS:
    src = os.path.join(HERE, "outputs", f"{name}.png")
    cite_src = os.path.join(HERE, "outputs", "cite", f"{name}_1280x720.png")
    shutil.copyfile(src, os.path.join(IMG, f"002_{name}.png"))
    shutil.copyfile(cite_src, os.path.join(CITE, f"002_{name}_1280x720.png"))
    print("copied", name)
