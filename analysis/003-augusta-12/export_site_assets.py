"""Copy release 003's export seam and hero art into the site tree.

Copies outputs/003_sandbox_grids.json and outputs/003_manifest.json (built
by export.py) into site/augusta-12/data/, and art/hero.png / art/
hero_mobile_crop.png into site/assets/img/003_hero.png / 003_hero_mobile.png.
Creates site/augusta-12/data/ if it does not exist yet. Idempotent: re-run
any time after export.py to refresh the site copies.

Run order: build_outputs.py (CSV + calls export.main()), then this script.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, "..", "..", "site"))
DATA_DIR = os.path.join(SITE, "augusta-12", "data")
IMG_DIR = os.path.join(SITE, "assets", "img")

DATA_FILES = ["003_sandbox_grids.json", "003_manifest.json"]
IMAGE_COPIES = [
    ("hero.png", "003_hero.png"),
    ("hero_mobile_crop.png", "003_hero_mobile.png"),
]


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    for name in DATA_FILES:
        src = os.path.join(HERE, "outputs", name)
        dst = os.path.join(DATA_DIR, name)
        shutil.copyfile(src, dst)
        print("copied", name, "->", dst)

    for src_name, dst_name in IMAGE_COPIES:
        src = os.path.join(HERE, "art", src_name)
        dst = os.path.join(IMG_DIR, dst_name)
        shutil.copyfile(src, dst)
        print("copied", src_name, "->", dst)


if __name__ == "__main__":
    main()
