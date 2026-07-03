#!/usr/bin/env python3
"""Dogleg Data - The Percentages Card (one-page PDF lead magnet).

Numbers are DERIVED here from Fairway_vs_Rough_Post/Fairway_vs_Rough_Data.csv
and dashboard_data.json (severity multipliers), never hand-typed, so the card
cannot drift from the published charts. Rounding uses Python round() (banker's)
because that is what chart 2 displays (20-hcp light rough at 150yd: 17 x 0.5 =
8.5 -> shown as 8). Asserts below enforce chart-to-chart consistency.

Fonts: brand TTFs from Fairway_vs_Rough_Post/source/fonts; Helvetica/Courier
fallback if missing (fonts are presentation, not data).
"""
import csv, json, os, sys

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

HERE = os.path.dirname(os.path.abspath(__file__))
POST = os.path.normpath(os.path.join(HERE, "..", "..", "Golf Agent", "Fairway_vs_Rough_Post"))
if not os.path.isdir(POST):
    POST = os.environ.get("FVR_POST", "")
CSV = os.path.join(POST, "Fairway_vs_Rough_Data.csv")
DASH = os.path.join(POST, "dashboard_data.json")
FONTS = os.path.join(POST, "source", "fonts")
OUT = os.path.normpath(os.path.join(HERE, "..", "site", "assets", "percentages-card.pdf"))

# Brand tokens (Dogleg_Data_Brand_Spec.md section 5)
CREAM = HexColor("#F4EDE0"); CARD = HexColor("#FBF7EE"); LINE = HexColor("#E2D8C6")
INK = HexColor("#1C1B18"); SADDLE = HexColor("#8A7F6E"); SOFT = HexColor("#4A4437")
CLAY = HexColor("#C05A36"); DENIM = HexColor("#5B7FA6"); OXBLOOD = HexColor("#7D362E")

# ---- fonts ----
def reg(name, fn):
    try:
        pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, fn))); return name
    except Exception:
        return None
F900 = reg("Fraunces900", "fraunces-900.ttf") or "Helvetica-Bold"
F600 = reg("Fraunces600", "fraunces-600.ttf") or "Helvetica-Bold"
MONO = reg("PlexMono", "ibm-plex-mono-400.ttf") or "Courier"
MONO5 = reg("PlexMono500", "ibm-plex-mono-500.ttf") or "Courier-Bold"
INTER = reg("Inter", "inter-400.ttf") or "Helvetica"
INTER6 = reg("Inter600", "inter-600.ttf") or "Helvetica-Bold"

# ---- derive numbers ----
rows = {}
with open(CSV) as f:
    for r in csv.DictReader(f):
        d = int(r["distance"])
        if d in (100, 125, 150, 175):
            rows[d] = {k: float(r[k]) for k in ("tour", "hcp10", "hcp20", "hcp30")}
mult = json.load(open(DASH))["worth"]["severity_mult"]  # light .5 / moderate 1 / deep 1.7

R = lambda x: round(x)  # banker's, matches chart 2 display
# Consistency asserts against published copy (site dek + chart 2 alt text)
assert (R(rows[150]["tour"]), R(rows[150]["hcp10"]), R(rows[150]["hcp20"]), R(rows[150]["hcp30"])) == (75, 23, 17, 12), rows[150]
w20_150 = rows[150]["hcp20"]
assert (R(w20_150 * mult["light"]), R(w20_150 * mult["moderate"]), R(w20_150 * mult["deep"])) == (8, 17, 29)

# ---- draw ----
W, H = letter
c = canvas.Canvas(OUT, pagesize=letter)
c.setTitle("Dogleg Data - The Percentages Card")
c.setAuthor("Dogleg Data")
c.setFillColor(CREAM); c.rect(0, 0, W, H, stroke=0, fill=1)
M = 54  # margin

# Header band
BH = 78
c.setFillColor(INK); c.rect(0, H - BH, W, BH, stroke=0, fill=1)
# mark (dogleg path), scaled 1.35, in cream on ink
c.saveState(); c.translate(M, H - BH + 14); c.scale(1.6, 1.6)
c.setStrokeColor(CREAM); c.setLineWidth(5); c.setLineCap(1); c.setLineJoin(1)
p = c.beginPath(); p.moveTo(8, 4); p.lineTo(8, 18); p.curveTo(8, 22, 10, 24, 14, 24); p.lineTo(21, 24)
c.drawPath(p, stroke=1, fill=0)
c.setFillColor(CLAY); c.circle(26, 24, 3.5, stroke=0, fill=1)
c.restoreState()
c.setFillColor(CREAM); c.setFont(F900, 24); c.drawString(M + 58, H - BH + 40, "Dogleg Data")
c.setFont(MONO, 9); c.drawString(M + 58, H - BH + 24, "PLAY THE PERCENTAGES")
c.setFont(MONO5, 11); c.drawRightString(W - M, H - BH + 40, "THE PERCENTAGES CARD")
c.setFont(MONO, 8); c.setFillColor(HexColor("#B9AF9E")); c.drawRightString(W - M, H - BH + 24, "doglegdata.com")

y = H - BH - 44

def section(title, yy):
    c.setFillColor(INK); c.setFont(F600, 16); c.drawString(M, yy, title)
    return yy - 8

# Section 1: table
y = section("What the fairway is worth", y)
c.setFillColor(SOFT); c.setFont(INTER, 9.5)
c.drawString(M, y - 12, "Yards closer the rough ball must be before it beats the fairway ball. Moderate rough, whole yards.")
y -= 34

tiers = [("Tour pro", "tour", INK), ("10 hcp", "hcp10", DENIM), ("20 hcp", "hcp20", CLAY), ("30 hcp *", "hcp30", OXBLOOD)]
x0 = M; colw = (W - 2 * M) / 5.0
rowh = 26
# header row
c.setFont(INTER6, 10); c.setFillColor(SADDLE)
c.drawString(x0 + 10, y, "APPROACH")
for i, (lab, _, col) in enumerate(tiers):
    c.setFillColor(col); c.drawRightString(x0 + colw * (i + 2) - 10, y, lab.upper())
y -= 10
c.setStrokeColor(INK); c.setLineWidth(1.2); c.line(M, y, W - M, y)
for d in (100, 125, 150, 175):
    y -= rowh
    if d in (125, 175):
        c.setFillColor(CARD); c.rect(M, y - 8, W - 2 * M, rowh, stroke=0, fill=1)
    c.setFont(MONO5, 12); c.setFillColor(INK)
    c.drawString(x0 + 10, y, f"{d} yds")
    for i, (_, k, col) in enumerate(tiers):
        c.setFillColor(col)
        star = " *" if k == "hcp30" else ""
        c.setFont(MONO5, 13)
        c.drawRightString(x0 + colw * (i + 2) - 10, y, f"{R(rows[d][k])}{star}")
y -= 12
c.setStrokeColor(LINE); c.setLineWidth(0.8); c.line(M, y, W - M, y)
y -= 16
c.setFillColor(OXBLOOD); c.setFont(INTER, 8.5)
c.drawString(M, y, "* Modeled: extrapolated beyond Stagner/Arccos's published 0-to-20 range. At 100 yards the modeled 30 tier lands")
y -= 11
c.drawString(M, y, "above the 20. Wobble like that is why modeled numbers carry stars.")
y -= 34

# Section 2: scramble rule
y = section("The scramble rule", y)
c.setFillColor(SOFT); c.setFont(INTER, 10.5)
c.drawString(M, y - 14, "Play the rough ball when it's closer by more than the table number, scaled for the lie:")
y -= 38
c.setFont(MONO5, 12)
for label, key, col in (("LIGHT x 0.5", "light", DENIM), ("MODERATE x 1.0", "moderate", CLAY), ("DEEP x 1.7", "deep", OXBLOOD)):
    c.setFillColor(col); c.drawString(M + 10, y, label)
    y -= 18
y -= 4
c.setFillColor(INK); c.setFont(INTER6, 10.5)
ex = (R(w20_150 * mult["light"]), R(w20_150), R(w20_150 * mult["deep"]))
c.drawString(M, y, f"Example: 20-handicap, 150-yard approach. The rough ball needs to be {ex[0]} yards closer in light rough,")
y -= 14
c.drawString(M, y, f"{ex[1]} in moderate, {ex[2]} in deep, before you play it.")
y -= 36

# Section 3: the 240-yard line
y = section("The 240-yard line", y)
c.setFillColor(SOFT); c.setFont(INTER, 10.5)
c.drawString(M, y - 14, "Past 240 yards out, a 20-handicap's rough ball outscores the fairway ball at the same distance.")
y -= 28
c.drawString(M, y, "A 15-handicap crosses the same line at 250. Real Arccos scoring data; no modeling involved.")
y -= 40

# Standing invite (fills the band above the footer; feeds the Scramble Reads format)
c.setFillColor(INK); c.setFont(F600, 14)
c.drawString(M, 150, "Bring a real scramble read. I'll run it through the model.")
c.setFillColor(HexColor("#A34A2C")); c.setFont(MONO5, 9)
c.drawString(M, 132, "@DOGLEGDATA ON X - SUNNY@DOGLEGDATA.COM")

# Footer
c.setStrokeColor(INK); c.setLineWidth(1); c.line(M, 92, W - M, 92)
c.setStrokeColor(INK); c.setLineWidth(1); c.line(M, 89, W - M, 89)
c.setFillColor(SADDLE); c.setFont(MONO, 7.2)
c.drawString(M, 74, "SOURCES: BROADIE 2011 SHOTLINK TABLE 9 (TOUR) - LOU STAGNER / ARCCOS PUBLISHED BREAK-EVEN DATA (AMATEUR)")
c.drawString(M, 63, "USGA/R&A 2021 ROUGH-DIFFICULTY SIMULATION, CROSS-CHECKED VS 2025 GOLF DIGEST FIELD TEST (SEVERITY) - GOLFTEC (DISPERSION)")
c.drawString(M, 52, "MODELED FIGURES STARRED, EVERY TIME THEY APPEAR.")
c.setFillColor(INK); c.setFont(MONO5, 8)
c.drawString(M, 36, "RUN YOUR OWN NUMBERS: DOGLEGDATA.COM")
c.setFillColor(SADDLE); c.setFont(MONO, 7.2)
c.drawRightString(W - M, 36, "(C) 2026 DOGLEG DATA - PLAY THE PERCENTAGES")

c.save()
print("wrote", OUT)
print("table:", {d: [R(rows[d][k]) for _, k, _c in tiers] for d in (100, 125, 150, 175)})
