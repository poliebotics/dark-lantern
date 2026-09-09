#!/usr/bin/env python3
"""Orientation and crop check before pair building: grid-8 coupling correlation (the kit's train-free statistic) between the emission,
resized to the crop's size under each of four orientations (identity, flip left-right, flip top-bottom, rotate 180), and the camera crop,
averaged over sample frames. The right orientation should stand out; a flat profile means the crop or the assumption is wrong.
  python3 orient_check.py 2024 x0,y0,x1,y1 ;  python3 orient_check.py 2023 x0,y0,x1,y1"""
import os, sys, re, numpy as np
from pathlib import Path
from PIL import Image
track, crop = sys.argv[1], tuple(int(x) for x in sys.argv[2].split(","))
RAW = Path(os.environ.get("OL_LOCAL", "oldlight_local")) / f"raw{track}"
G = 8
def grid(a):
    h, w, _ = a.shape; a = a[: (h // G) * G, : (w // G) * G].astype(np.float32)
    c = a.reshape(G, h // G, G, w // G, 3).mean(axis=(1, 3)); c -= c.mean(axis=(0, 1), keepdims=True); return c / (c.std(axis=(0, 1), keepdims=True) + 1e-6)
def corr(x, y): return float(np.mean([np.corrcoef(x[..., k].ravel(), y[..., k].ravel())[0, 1] for k in range(3)]))
ORIENT = {"identity": lambda im: im, "flip_lr": lambda im: im.transpose(Image.FLIP_LEFT_RIGHT), "flip_tb": lambda im: im.transpose(Image.FLIP_TOP_BOTTOM), "rot180": lambda im: im.transpose(Image.ROTATE_180)}
size = (crop[2] - crop[0], crop[3] - crop[1]); samples = []
if track == "2024":
    import h5py
    for f in sorted(RAW.glob("*.h5"))[:4]:
        with h5py.File(f, "r") as h:
            for i in (5, 30, 55): samples.append((f.stem, i, Image.fromarray(h["emissions"][i]), Image.fromarray(h["recordings"][i]).crop(crop)))
else:
    IDX = re.compile(r"^(\d{6})_")
    for s in sorted(p for p in RAW.iterdir() if p.is_dir())[:5]:
        em = {IDX.match(p.name).group(1): p for p in (s / "emissions").glob("*.npy")}; rp = {IDX.match(p.name).group(1): p for p in (s / "reports").glob("*.npy")}
        common = sorted(set(em) & set(rp))
        for k in (common[len(common) // 4], common[len(common) // 2], common[3 * len(common) // 4]):
            e = np.load(em[k]); e8 = np.clip(e / 255.0 * 255.0, 0, 255).astype(np.uint8)
            samples.append((s.name, int(k), Image.fromarray(e8), Image.fromarray(np.load(rp[k])).crop(crop)))
res = {o: [] for o in ORIENT}; mism = []
for j, (s, i, E, B) in enumerate(samples):
    gB = grid(np.asarray(B))
    for o, fn in ORIENT.items(): res[o].append(corr(grid(np.asarray(fn(E).resize(size, Image.BICUBIC))), gB))
    other = samples[(j + 1) % len(samples)][2]; mism.append(corr(grid(np.asarray(other.resize(size, Image.BICUBIC))), gB))
print(f"track {track} crop {crop} size {size} frames {len(samples)}")
for o in ORIENT: print(f"  {o:9s} mean corr {np.mean(res[o]):+.4f}  per-frame {' '.join(f'{v:+.2f}' for v in res[o])}")
print(f"  mismatch  mean corr {np.mean(mism):+.4f} (another sample's emission, identity)")
