#!/usr/bin/env python3
"""Orientation and crop check, second pass: (1) the bright projected region's bounding box from the mean luminance of sample recordings
(downsampled 8x, threshold at a fraction of the 99th percentile); (2) coupling correlation for the four orientations at grids 8, 16, 32, 64.
  python3 orient_check2.py 2024 x0,y0,x1,y1 ;  python3 orient_check2.py 2023 x0,y0,x1,y1"""
import os, sys, re, numpy as np
from pathlib import Path
from PIL import Image
track, crop = sys.argv[1], tuple(int(x) for x in sys.argv[2].split(","))
RAW = Path(os.environ.get("OL_LOCAL", "oldlight_local")) / f"raw{track}"
def grid(a, G):
    h, w, _ = a.shape; a = a[: (h // G) * G, : (w // G) * G].astype(np.float32)
    c = a.reshape(G, h // G, G, w // G, 3).mean(axis=(1, 3)); c -= c.mean(axis=(0, 1), keepdims=True); return c / (c.std(axis=(0, 1), keepdims=True) + 1e-6)
def corr(x, y): return float(np.mean([np.corrcoef(x[..., k].ravel(), y[..., k].ravel())[0, 1] for k in range(3)]))
ORIENT = {"identity": lambda im: im, "flip_lr": lambda im: im.transpose(Image.FLIP_LEFT_RIGHT), "flip_tb": lambda im: im.transpose(Image.FLIP_TOP_BOTTOM), "rot180": lambda im: im.transpose(Image.ROTATE_180)}
samples = []
if track == "2024":
    import h5py
    for f in sorted(RAW.glob("*.h5"))[:4]:
        with h5py.File(f, "r") as h:
            for i in (5, 30, 55): samples.append((f.stem, i, Image.fromarray(h["emissions"][i]), Image.fromarray(h["recordings"][i])))
else:
    IDX = re.compile(r"^(\d{6})_")
    for s in sorted(p for p in RAW.iterdir() if p.is_dir())[:5]:
        em = {IDX.match(p.name).group(1): p for p in (s / "emissions").glob("*.npy")}; rp = {IDX.match(p.name).group(1): p for p in (s / "reports").glob("*.npy")}
        common = sorted(set(em) & set(rp))
        for k in (common[len(common) // 4], common[len(common) // 2], common[3 * len(common) // 4]):
            samples.append((s.name, int(k), Image.fromarray(np.clip(np.load(em[k]), 0, 255).astype(np.uint8)), Image.fromarray(np.load(rp[k]))))
# (1) bright-region bounding box
lum = np.mean([np.asarray(B.convert("L").resize((B.size[0] // 8, B.size[1] // 8), Image.BOX), dtype=np.float32) for _, _, _, B in samples], axis=0)
for frac in (0.25, 0.35, 0.5):
    thr = frac * np.percentile(lum, 99); ys, xs = np.where(lum > thr)
    print(f"bright region (>{frac:.2f} x p99={np.percentile(lum, 99):.1f}): x {xs.min()*8}..{(xs.max()+1)*8}  y {ys.min()*8}..{(ys.max()+1)*8}  (full-res px)")
# (2) orientation profile at several grids
size = (crop[2] - crop[0], crop[3] - crop[1]); print(f"track {track} crop {crop} size {size} frames {len(samples)}")
for G in (8, 16, 32, 64):
    res = {o: [] for o in ORIENT}; mism = []
    for j, (s, i, E, B) in enumerate(samples):
        gB = grid(np.asarray(B.crop(crop)), G)
        for o, fn in ORIENT.items(): res[o].append(corr(grid(np.asarray(fn(E).resize(size, Image.BICUBIC)), G), gB))
        mism.append(corr(grid(np.asarray(samples[(j + 1) % len(samples)][2].resize(size, Image.BICUBIC)), G), gB))
    print(f"  grid {G:2d}: " + "  ".join(f"{o} {np.mean(res[o]):+.4f}" for o in ORIENT) + f"  | mismatch {np.mean(mism):+.4f}")
