#!/usr/bin/env python3
"""Pre-downsample C (whole sensor frame, area-resized) and E (12 XOF octave channels, area-resized) for every training and evaluation
row at one or more target sizes, using train_lean.py's own loaders so the cached tensors are exactly what the trainer would compute.
Writes <cache>/<TH>x<TW>/<sid>/{C,E}_<r>.npy as float16. Multi-process over rows. Idempotent (skips existing files)."""
import argparse, importlib.util, os, sys
from concurrent.futures import ThreadPoolExecutor   # I/O-bound; threads avoid forking torch state
import numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--trainer", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "train_lean.py"))
ap.add_argument("--cache-dir", required=True)
ap.add_argument("--sizes", default="96,112;48,56", help="semicolon-separated TH,TW list")
ap.add_argument("--sessions", default="d2,v10")
ap.add_argument("--workers", type=int, default=32)
ap.add_argument("--eval-only", action="store_true")
ap.add_argument("--local-root", default="", help="smoke tests: remap session dirs onto this root (sessions/<sid>)")
a = ap.parse_args()
spec = importlib.util.spec_from_file_location("lean", a.trainer); M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
if a.local_root:
    import pathlib
    for sid in list(M.SESSIONS):
        cand = pathlib.Path(a.local_root) / "sessions" / sid
        if cand.is_dir(): M.SESSIONS[sid]["dir"] = cand
        else: del M.SESSIONS[sid]
M.resolve_raw_layout()
sizes = [tuple(int(v) for v in s.split(",")) for s in a.sizes.split(";")]
sess = a.sessions.split(",")
rows = []
for sid in sess:
    S = M.SESSIONS[sid]
    if not a.eval_only:
        for lo, hi in S["train"]: rows += [(sid, r) for r in range(lo, hi)]
    for lo, hi in S["eval_blocks"]: rows += [(sid, r) for r in range(lo, hi)]
    # wrong-row offsets used by the protocol evaluator reach up to 30 rows outside the eval blocks
    for lo, hi in S["eval_blocks"]: rows += [(sid, r) for r in list(range(max(0, lo - 30), lo)) + list(range(hi, min(S["rows_total"], hi + 30)))]
rows = sorted(set(rows))
def work(item):
    sid, r = item; done = 0
    for (TH, TW) in [CUR_SIZE]:
        d = os.path.join(a.cache_dir, f"{TH}x{TW}", sid); os.makedirs(d, exist_ok=True)
        pc, pe = os.path.join(d, f"C_{r:06d}.npy"), os.path.join(d, f"E_{r:06d}.npy")
        if not os.path.isfile(pc): np.save(pc, M.load_C(sid, r).numpy().astype(np.float16)); done += 1
        if not os.path.isfile(pe): np.save(pe, M._load_E_uncached(sid, r).numpy().astype(np.float16)); done += 1
    return done
print(f"precache: {len(rows)} rows x {len(sizes)} sizes -> {a.cache_dir}", flush=True)
import torch; torch.set_num_threads(max(1, os.cpu_count() // 2))
n = 0
for CUR_SIZE in sizes:
    M.TH, M.TW = CUR_SIZE; M.CACHE_DIR = None
    with ThreadPoolExecutor(a.workers) as ex:
        for i, d in enumerate(ex.map(work, rows)):
            n += d
            if i % 500 == 0: print(f"  size {CUR_SIZE}: {i}/{len(rows)} rows, {n} files written", flush=True)
print(f"precache done: {n} files written")
