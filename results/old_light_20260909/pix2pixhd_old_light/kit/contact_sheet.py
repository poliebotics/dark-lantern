#!/usr/bin/env python3
"""Contact sheet of held-out triples: emission | real recording | generated recording, one row per frame, evenly strided.
  python3 contact_sheet.py --test_a <dir> --test_b <dir> --fake <dir> --out sheet.png [--rows 8] [--width 640] [--title "..."]"""
import argparse, os
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser(); ap.add_argument("--test_a", required=True); ap.add_argument("--test_b", required=True); ap.add_argument("--fake", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--rows", type=int, default=8); ap.add_argument("--width", type=int, default=640); ap.add_argument("--title", default=""); ap.add_argument("--names", default=None, help="comma list of frame names to use instead of the stride")
ap.add_argument("--swap_rb_a", action="store_true", help="show the emission with its channel order reversed (2023: displayed BGR)"); ap.add_argument("--swap_rb_b", action="store_true", help="show real and generated recordings with channels reversed (2024: stored BGR)")
a = ap.parse_args()
names = sorted(f for f in os.listdir(a.fake) if f.endswith(".png") and os.path.exists(os.path.join(a.test_b, f)))
if a.names: names = a.names.split(",")
else:
    step = max(1, len(names) // a.rows); names = names[::step][: a.rows]
w = a.width; sample = Image.open(os.path.join(a.test_b, names[0])); h = round(w * sample.size[1] / sample.size[0]); pad = 6; head = 44 if a.title else 0; label = 22
sheet = Image.new("RGB", (3 * w + 4 * pad, head + len(names) * (h + label + pad) + pad), (18, 18, 18)); d = ImageDraw.Draw(sheet)
if a.title: d.text((pad, 12), a.title, fill=(230, 230, 230))
for r, n in enumerate(names):
    y = head + pad + r * (h + label + pad)
    for c, (dirname, cap) in enumerate(((a.test_a, "emission (projector input)"), (a.test_b, "real camera recording"), (a.fake, "pix2pixHD generated recording"))):
        im = Image.open(os.path.join(dirname, n)).convert("RGB").resize((w, h), Image.LANCZOS); x = pad + c * (w + pad)
        if (c == 0 and a.swap_rb_a) or (c > 0 and a.swap_rb_b): im = Image.fromarray(__import__("numpy").asarray(im)[..., ::-1].copy())
        sheet.paste(im, (x, y + label)); d.text((x, y + 4), f"{cap}  {n}" if c == 1 else cap, fill=(200, 200, 200))
sheet.save(a.out, optimize=True); print("sheet", a.out, sheet.size, len(names), "rows")
