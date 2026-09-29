"""Build a labeled contact sheet (2 columns) from a glob of candidate images.

Usage: contact_sheet.py "candidates/r1_[0-9].png" candidates/r1_contact.jpg
"""
import glob
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

THUMB_W = 800
COLS = 2
GAP = 12


def natural_key(path):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", path)]


def load_font(size):
    for p in ("/System/Library/Fonts/Helvetica.ttc",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    pattern, out = sys.argv[1], sys.argv[2]
    paths = sorted(glob.glob(pattern), key=natural_key)
    if not paths:
        sys.exit(f"no files match {pattern}")
    thumbs = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        h = round(im.height * THUMB_W / im.width)
        thumbs.append((os.path.splitext(os.path.basename(p))[0],
                       im.resize((THUMB_W, h), Image.LANCZOS)))
    rows = -(-len(thumbs) // COLS)
    row_h = max(t.height for _, t in thumbs)
    sheet = Image.new("RGB", (COLS * THUMB_W + (COLS + 1) * GAP,
                              rows * row_h + (rows + 1) * GAP), (20, 20, 20))
    draw = ImageDraw.Draw(sheet)
    font = load_font(34)
    for i, (label, t) in enumerate(thumbs):
        x = GAP + (i % COLS) * (THUMB_W + GAP)
        y = GAP + (i // COLS) * (row_h + GAP)
        sheet.paste(t, (x, y))
        box = draw.textbbox((x + 14, y + 10), label, font=font)
        draw.rectangle((box[0] - 8, box[1] - 6, box[2] + 8, box[3] + 6), fill=(0, 0, 0))
        draw.text((x + 14, y + 10), label, font=font, fill=(255, 255, 255))
    sheet.convert("RGB").save(out, quality=82)
    print(f"wrote {out} ({sheet.width}x{sheet.height}, {len(thumbs)} images)")


if __name__ == "__main__":
    main()
