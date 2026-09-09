#!/usr/bin/env python3
"""precache_xcfg.py (BOSUN, 2026-09-09): pre-downsample the ARM-I inputs with train_xcfg.py's own loaders so the cached
tensors are exactly what the trainer and evaluator compute: C (whole frame, 4 RGGB planes, area-resized) and Ei (the rendered
emission image, RGB, area-resized). Writes <cache>/<TH>x<TW>/<sid>/{C,Ei}_<r>.npy as float16. For the 2026 sessions C is taken
from the read-only published cache (--c-cache-fallback) when present and only Ei is written; nothing is written outside --cache-dir.
Idempotent. Rows: 2026 train + eval blocks +/- 30 (as the published precache) plus all August rows; old sessions: every row."""
import argparse, importlib.util, os, sys, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
ap = argparse.ArgumentParser()
ap.add_argument("--trainer", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "train_xcfg.py"))
ap.add_argument("--cache-dir", required=True)
ap.add_argument("--c-cache-fallback", default="")
ap.add_argument("--old-root", default="")
ap.add_argument("--sizes", default="96,112")
ap.add_argument("--sessions", required=True, help="comma list")
ap.add_argument("--workers", type=int, default=24)
ap.add_argument("--local-root", default="", help="tests: remap 2026 session dirs (sessions/<sid>, august_dev_712)")
ap.add_argument("--limit", type=int, default=0, help="tests: first N rows per session")
a = ap.parse_args()
spec = importlib.util.spec_from_file_location("xcfg", a.trainer); M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
M.EMISSION_IMAGE = True
if a.c_cache_fallback: M.C_CACHE_FALLBACK = a.c_cache_fallback
if a.old_root:
    from pathlib import Path
    M.OLD_ROOT = Path(a.old_root)
    for sid in M.SESSIONS_2024: M.SESSIONS[sid]["file"] = M.OLD_ROOT / "2024" / f"{sid}.h5"
    for sid in M.SESSIONS_2023: M.SESSIONS[sid]["dir"] = M.OLD_ROOT / "2023" / sid
sess = a.sessions.split(",")
for sid in list(M.SESSIONS):
    if sid not in sess: del M.SESSIONS[sid]
if a.local_root:
    from pathlib import Path
    LR = Path(a.local_root); remap = {"d2": LR / "sessions/d2", "v10": LR / "sessions/v10", "august": LR / "august_dev_712"}
    for sid in M.SESSIONS:
        if sid in remap and remap[sid].is_dir(): M.SESSIONS[sid]["dir"] = remap[sid]
M.resolve_raw_layout()
sizes = [tuple(int(v) for v in s.split(",")) for s in a.sizes.split(";")]
rows = []
for sid in sess:
    S = M.SESSIONS[sid]
    if S.get("kind", "tb2026") == "tb2026":
        if sid == "august":
            rows += [(sid, r) for r in range(0, S["rows_total"])]
        else:
            for lo, hi in S["train"]: rows += [(sid, r) for r in range(lo, hi)]
            for lo, hi in S["eval_blocks"]: rows += [(sid, r) for r in range(lo, hi)]
            for lo, hi in S["eval_blocks"]: rows += [(sid, r) for r in list(range(max(0, lo - 30), lo)) + list(range(hi, min(S["rows_total"], hi + 30)))]
    else:
        rows += [(sid, r) for r in range(S["rows_total"])]
    if a.limit:
        rows = [x for x in rows if x[0] != sid] + [x for x in rows if x[0] == sid][:a.limit]
rows = sorted(set(rows))
def work(item):
    sid, r = item; done = 0
    TH, TW = CUR
    d = os.path.join(a.cache_dir, f"{TH}x{TW}", sid); os.makedirs(d, exist_ok=True)
    pc, pe = os.path.join(d, f"C_{r:06d}.npy"), os.path.join(d, f"Ei_{r:06d}.npy")
    kind = M.SESSIONS[sid].get("kind", "tb2026")
    have_fallback = kind == "tb2026" and a.c_cache_fallback and os.path.isfile(os.path.join(a.c_cache_fallback, f"{TH}x{TW}", sid, f"C_{r:06d}.npy"))
    if not os.path.isfile(pc) and not have_fallback:
        t = M.load_C(sid, r).numpy().astype(np.float16); tmp = pc + ".tmp"; np.save(tmp, t); os.replace(tmp + ".npy" if not tmp.endswith(".npy") else tmp, pc); done += 1
    if not os.path.isfile(pe):
        t = M._load_Ei_uncached(sid, r).numpy().astype(np.float16); tmp = pe + ".tmp"; np.save(tmp, t); os.replace(tmp + ".npy" if not tmp.endswith(".npy") else tmp, pe); done += 1
    return done
print(f"precache_xcfg: {len(rows)} rows x {len(sizes)} sizes -> {a.cache_dir} (sessions {sess})", flush=True)
import torch; torch.set_num_threads(2)
n = 0; t0 = time.time()
for CUR in sizes:
    M.TH, M.TW = CUR; M.CACHE_DIR = None
    with ThreadPoolExecutor(a.workers) as ex:
        for i, d in enumerate(ex.map(work, rows)):
            n += d
            if i % 500 == 0: print(f"  size {CUR}: {i}/{len(rows)} rows, {n} files written, {time.time()-t0:.0f}s", flush=True)
print(f"precache_xcfg done: {n} files written in {time.time()-t0:.0f}s")
