#!/usr/bin/env python3
"""precache_warped.py (BOSUN, 2026-09-09): variant (b) of the cross-configuration test, the alignment-normalised input.
For every row of the old sessions the full-resolution recording is warped into the displayed-emission frame with the
per-session homography H (displayed-emission px -> recording px, fitted by the data-look desk, supporting/data_look/),
then re-mosaiced onto the RGGB grid and area-resized to the frame grid exactly as the raw variant, and written as C_<r>.npy
into a separate cache root; Ei_<r>.npy are symlinked from the main cache. Bilinear sampling with torch grid_sample; pixel
centres at integer coordinates; samples falling outside the recording are zero (none do: every mapped rectangle lies inside
its frame per the alignment table). No model, no training: an input geometry normalisation for a fair second test."""
import argparse, importlib.util, os, sys, time
from concurrent.futures import ThreadPoolExecutor
import numpy as np, torch, torch.nn.functional as F
ap = argparse.ArgumentParser()
ap.add_argument("--trainer", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "train_xcfg.py"))
ap.add_argument("--src-cache", required=True); ap.add_argument("--dst-cache", required=True); ap.add_argument("--h-dir", required=True)
ap.add_argument("--old-root", required=True); ap.add_argument("--sessions", required=True); ap.add_argument("--workers", type=int, default=16)
ap.add_argument("--size", default="96,112"); ap.add_argument("--limit", type=int, default=0)
a = ap.parse_args()
spec = importlib.util.spec_from_file_location("xcfg", a.trainer); M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
from pathlib import Path
M.OLD_ROOT = Path(a.old_root)
for sid in M.SESSIONS_2024: M.SESSIONS[sid]["file"] = M.OLD_ROOT / "2024" / f"{sid}.h5"
for sid in M.SESSIONS_2023: M.SESSIONS[sid]["dir"] = M.OLD_ROOT / "2023" / sid
sess = a.sessions.split(",")
for sid in list(M.SESSIONS):
    if sid not in sess: del M.SESSIONS[sid]
M.resolve_raw_layout()
TH, TW = (int(v) for v in a.size.split(","))
M.TH, M.TW = TH, TW
DISP = {"h5_2024": (1080, 1920), "npy_2023": (1200, 1920)}   # displayed-emission frame (H, W)
torch.set_num_threads(2)

def grid_for(H, out_hw, in_hw):
    """Sampling grid (1, oh, ow, 2) in grid_sample's normalised coordinates: for each emission pixel centre (u, v) the recording
    location H (u, v, 1), pixel centres at integer coordinates (align_corners=True convention: -1 <-> pixel 0, +1 <-> pixel W-1)."""
    oh, ow = out_hw; ih, iw = in_hw
    u, v = np.meshgrid(np.arange(ow, dtype=np.float64), np.arange(oh, dtype=np.float64))
    P = np.stack([u.ravel(), v.ravel(), np.ones(u.size)], 0)
    Q = H @ P; x = Q[0] / Q[2]; y = Q[1] / Q[2]
    gx = 2.0 * x / (iw - 1) - 1.0; gy = 2.0 * y / (ih - 1) - 1.0
    return torch.from_numpy(np.stack([gx, gy], -1).reshape(1, oh, ow, 2).astype(np.float32))

GRIDS = {}
def warp(img_u8_hwc, sid):
    kind = M.SESSIONS[sid]["kind"]
    if sid not in GRIDS:
        H = np.load(os.path.join(a.h_dir, f"{sid}_H_full.npy")).astype(np.float64)
        GRIDS[sid] = grid_for(H, DISP[kind], img_u8_hwc.shape[:2])
    t = torch.from_numpy(img_u8_hwc.astype(np.float32)).permute(2, 0, 1).unsqueeze(0)   # (1,3,H,W)
    out = F.grid_sample(t, GRIDS[sid], mode="bilinear", padding_mode="zeros", align_corners=True)
    return out.squeeze(0).permute(1, 2, 0).numpy()   # (oh, ow, 3) float in 0..255 units

def work(item):
    sid, r = item
    d = os.path.join(a.dst_cache, f"{TH}x{TW}", sid); os.makedirs(d, exist_ok=True)
    pc, pe = os.path.join(d, f"C_{r:06d}.npy"), os.path.join(d, f"Ei_{r:06d}.npy")
    if not os.path.islink(pe) and not os.path.exists(pe):
        src = os.path.join(a.src_cache, f"{TH}x{TW}", sid, f"Ei_{r:06d}.npy")
        os.symlink(src, pe)
    if os.path.isfile(pc): return 0
    S = M.SESSIONS[sid]
    if S["kind"] == "h5_2024":
        img = M._h5_read(S["file"], "recordings", r); order = "BGR"
    else:
        img = np.load(M._OLD[sid][r][2]); order = "RGB"
    w = np.clip(warp(img, sid), 0, 255)
    planes = M._planes_from_rgb_image(w, order)        # float planes /255 (the function divides by 255)
    C = M._area(planes).numpy().astype(np.float16)
    tmp = pc + ".tmp.npy"; np.save(tmp, C); os.replace(tmp, pc)
    return 1
rows = [(sid, r) for sid in sess for r in range(M.SESSIONS[sid]["rows_total"])]
if a.limit: rows = [x for sid in sess for x in [(sid, r) for r in range(min(a.limit, M.SESSIONS[sid]["rows_total"]))]]
print(f"precache_warped: {len(rows)} rows -> {a.dst_cache}", flush=True)
t0 = time.time(); n = 0
with ThreadPoolExecutor(a.workers) as ex:
    for i, d in enumerate(ex.map(work, rows)):
        n += d
        if i % 400 == 0: print(f"  {i}/{len(rows)} {n} written {time.time()-t0:.0f}s", flush=True)
print(f"precache_warped done: {n} written in {time.time()-t0:.0f}s")
