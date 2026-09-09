#!/usr/bin/env python3
"""Channel-order check on the prepared pairs: mean correlation matrix between emission channel c and capture channel c' over grid-16 cells,
averaged over sample pairs. A diagonal-dominant matrix means the stored channel orders agree; a strong anti-diagonal (E0~B2, E2~B0) means one
side is BGR relative to the other.  python3 channel_check.py <pairs dir> [n]"""
import os, sys, numpy as np
from PIL import Image
P = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 40; G = 16
names = sorted(os.listdir(f"{P}/train_A")); names = names[:: max(1, len(names) // n)][:n]
def grid(a):
    h, w, _ = a.shape; a = a[: (h // G) * G, : (w // G) * G].astype(np.float32); c = a.reshape(G, h // G, G, w // G, 3).mean(axis=(1, 3))
    c -= c.mean(axis=(0, 1), keepdims=True); return c / (c.std(axis=(0, 1), keepdims=True) + 1e-6)
M = np.zeros((3, 3))
for nm in names:
    E = grid(np.asarray(Image.open(f"{P}/train_A/{nm}").convert("RGB"))); B = grid(np.asarray(Image.open(f"{P}/train_B/{nm}").convert("RGB")))
    for c in range(3):
        for d in range(3): M[c, d] += np.corrcoef(E[..., c].ravel(), B[..., d].ravel())[0, 1]
M /= len(names)
print(P, len(names), "pairs; rows = emission channel 0,1,2 as stored; cols = capture channel 0,1,2 as stored")
for c in range(3): print("  E%d: " % c + "  ".join(f"{M[c, d]:+.3f}" for d in range(3)))
