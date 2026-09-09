#!/usr/bin/env python3
"""Extra 2024 geometry requested by the coordinator (5090 desk, 2026-09-09): the January 2025 exporter's recording crop,
the centre 75 percent of the recording height at full width (4600 -> rows 575..4024, all 5320 columns). The exporter then
resized to 2048x1024 (LANCZOS) and kept the HDF5's stored BGR byte order; for the grid statistic the resize is immaterial
(cells are averaged) and the byte order is applied at stage B by reversing the cached grid channels. Grids here are
computed on the RGB-corrected recording. Usage: python3 stage_a_extra_2024.py <session> <data.h5>
Writes $COUPLING_CACHE/<session>.export75.npz (default coupling_cache/) (Rexport75_<g> arrays aligned with the main cache's frames)."""
import sys, os, json, time
import numpy as np, h5py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coupling_lib import *
session, source = sys.argv[1], sys.argv[2]
OUT = os.environ.get("COUPLING_CACHE", "coupling_cache")
hf = h5py.File(source, "r"); n = hf["recordings"].shape[0]
H = hf["recordings"].shape[1]; ch = int(round(0.75 * H)); top = (H - ch) // 2
cache = {f"Rexport75_{g}": np.zeros((n, g, g, 3), np.float32) for g in GRIDS}
t0 = time.time()
for k in range(n):
    R = load_2024_recording(np.array(hf["recordings"][k, top:top + ch]))
    for g in GRIDS:
        cache[f"Rexport75_{g}"][k] = grid(R, g)
np.savez_compressed(f"{OUT}/{session}.export75.npz", idxs=np.arange(n), crop_rows=np.array([top, top + ch]), **cache)
print(time.strftime("%H:%M:%SZ", time.gmtime()), session, f"export75 rows {top}..{top+ch-1} of {H}, {n} frames, {time.time()-t0:.0f}s", flush=True)
