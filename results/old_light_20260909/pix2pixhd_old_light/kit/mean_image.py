#!/usr/bin/env python3
"""Mean of all training captures at the pair resolution -> <pairs>/mean_train_B.png (and a copy in the held-session dataroot).
  python3 mean_image.py <pairs dir> [procs]"""
import os, sys, numpy as np
from multiprocessing import Pool
from PIL import Image
P = sys.argv[1]; procs = int(sys.argv[2]) if len(sys.argv) > 2 else 8
files = sorted(os.listdir(f"{P}/train_B"))
def part(chunk):
    acc = None
    for f in chunk:
        x = np.asarray(Image.open(f"{P}/train_B/{f}").convert("RGB"), dtype=np.float64); acc = x if acc is None else acc + x
    return acc, len(chunk)
chunks = [files[i::procs] for i in range(procs)]
with Pool(procs) as pool: parts = pool.map(part, chunks)
acc = sum(p[0] for p in parts if p[0] is not None); n = sum(p[1] for p in parts)
img = Image.fromarray(np.clip(acc / n, 0, 255).astype(np.uint8)); img.save(f"{P}/mean_train_B.png", compress_level=1)
held = P + "_held"
if os.path.isdir(held): img.save(f"{held}/mean_train_B.png", compress_level=1)
print(P, "mean of", n, "training captures", img.size)
