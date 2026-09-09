#!/usr/bin/env python3
"""Stage A: per-session loading, emission-blind geometry, and grid caching.
Usage: python3 stage_a_session.py <era> <session> <source> [--nofig]
  era 2023: source = session directory with emissions/ and reports/ (npy pairs, selected sample already on disk)
  era 2024: source = data.h5 (verified copy)
Writes $COUPLING_CACHE/<session>.npz (default coupling_cache/) with, per frame: E grids at each g for orientation 0 and 180,
R_full grids, R_crop grids; plus geometry.json and preview PNGs (std map, quad overlay, crop, emission) for the contact sheet.
"""
import sys, os, json, time
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coupling_lib import *

era, session, source = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = os.environ.get("COUPLING_CACHE", "coupling_cache"); os.makedirs(OUT, exist_ok=True)
PREV = os.environ.get("COUPLING_PREVIEWS", "coupling_previews"); os.makedirs(PREV, exist_ok=True)
t0 = time.time()

def log(m):
    print(time.strftime("%H:%M:%SZ", time.gmtime()), session, m, flush=True)

# ---- frame iteration ----
if era == "2023":
    pairs = list_2023_session(source)
    idxs = [p[0] for p in pairs]
    n = len(pairs)
    def load_pair(k):
        i, ep, rp = pairs[k]
        return load_2023_emission(ep), load_2023_report(rp)
    DS = 4; OUT_WH = (1920, 1200)
    src_files = {"emissions": [os.path.basename(p[1]) for p in pairs], "reports": [os.path.basename(p[2]) for p in pairs]}
else:
    import h5py
    hf = h5py.File(source, "r")
    n = hf["emissions"].shape[0]; idxs = list(range(n))
    def load_pair(k):
        return np.array(hf["emissions"][k]), load_2024_recording(np.array(hf["recordings"][k]))
    DS = 8; OUT_WH = (1920, 1080)
    src_files = {"h5": os.path.abspath(source), "attrs": {k: (v.item() if hasattr(v, "item") else str(v)) for k, v in hf.attrs.items()}}
log(f"{n} pairs; era {era}")

# ---- pass 1: working-scale stack for the temporal std map ----
small = []
for k in range(n):
    _, R = load_pair(k)
    h, w, _ = R.shape
    small.append(cv2.resize(R, (w // DS, h // DS), interpolation=cv2.INTER_AREA).astype(np.float32))
small = np.stack(small)
std_map = small.std(axis=0).mean(axis=2)
mean_map = small.mean(axis=0)
quad_w, comp, diag = projected_quad_from_std(std_map)
quad_full = (quad_w + 0.5) * DS - 0.5  # pixel-centre convention back to full resolution
Hf, Wf = h, w
diag.update({"downsample": DS, "recording_wh": [Wf, Hf], "quad_full_xy_TL_TR_BR_BL": quad_full.tolist(),
             "quad_area_frac_of_frame": float(cv2.contourArea(quad_full.astype(np.float32)) / (Wf * Hf)),
             "std_in_quad_mean": None, "std_out_quad_mean": None})
qmask = np.zeros(std_map.shape, np.uint8); cv2.fillConvexPoly(qmask, np.round(quad_w).astype(np.int32), 1)
diag["std_in_quad_mean"] = float(std_map[qmask == 1].mean()); diag["std_out_quad_mean"] = float(std_map[qmask == 0].mean())
log(f"quad (full px) {np.round(quad_full).astype(int).tolist()} area frac {diag['quad_area_frac_of_frame']:.3f} std in/out {diag['std_in_quad_mean']:.1f}/{diag['std_out_quad_mean']:.1f} method {diag['method']}")
del small

# ---- pass 2: grids ----
cache = {f"E{o}_{g}": np.zeros((n, g, g, 3), np.float32) for o in (0, 180) for g in GRIDS}
cache.update({f"Rfull_{g}": np.zeros((n, g, g, 3), np.float32) for g in GRIDS})
cache.update({f"Rcrop_{g}": np.zeros((n, g, g, 3), np.float32) for g in GRIDS})
chan = np.zeros((3, 3)); Emean = np.zeros((n, 3)); Rmean_full = np.zeros((n, 3)); Rmean_crop = np.zeros((n, 3))
keep = {}
for k in range(n):
    E, R = load_pair(k)
    crop = warp_quad(R, quad_full, OUT_WH)
    for g in GRIDS:
        cache[f"E0_{g}"][k] = grid(E, g); cache[f"E180_{g}"][k] = grid(orient(E, 180), g)
        cache[f"Rfull_{g}"][k] = grid(R, g); cache[f"Rcrop_{g}"][k] = grid(crop, g)
    Emean[k] = E.reshape(-1, 3).mean(axis=0); Rmean_full[k] = R.reshape(-1, 3).mean(axis=0); Rmean_crop[k] = crop.reshape(-1, 3).mean(axis=0)
    if k in (0, min(3, n - 1), n // 2):
        keep[k] = (E, R, crop)
np.savez_compressed(f"{OUT}/{session}.npz", idxs=np.array(idxs), **cache)
geom = {"era": era, "session": session, "n_pairs": n, "indices": idxs, "source": src_files, "crop_out_wh": OUT_WH, "geometry": diag,
        "emission_mean_rgb_per_frame": Emean.round(2).tolist(), "recording_mean_rgb_full": Rmean_full.round(2).tolist(),
        "recording_mean_rgb_crop": Rmean_crop.round(2).tolist(), "elapsed_s": round(time.time() - t0, 1)}
json.dump(geom, open(f"{OUT}/{session}.geometry.json", "w"), indent=1)

# ---- previews ----
if "--nofig" not in sys.argv:
    s8 = np.clip(std_map / max(np.percentile(std_map, 99.5), 1e-6) * 255, 0, 255).astype(np.uint8)
    over = cv2.cvtColor(s8, cv2.COLOR_GRAY2BGR)
    cv2.polylines(over, [np.round(quad_w).astype(np.int32)], True, (0, 0, 255), 2)
    cv2.imwrite(f"{PREV}/{session}_stdmap_quad.png", over)
    for k, (E, R, crop) in keep.items():
        Rs = cv2.resize(R, (Wf // DS, Hf // DS), interpolation=cv2.INTER_AREA)
        Rs = cv2.cvtColor(Rs, cv2.COLOR_RGB2BGR)
        cv2.polylines(Rs, [np.round(quad_w).astype(np.int32)], True, (0, 0, 255), 2)
        cv2.imwrite(f"{PREV}/{session}_f{k:03d}_recording_quad.png", Rs)
        cv2.imwrite(f"{PREV}/{session}_f{k:03d}_crop.png", cv2.cvtColor(cv2.resize(crop, (480, int(480 * OUT_WH[1] / OUT_WH[0]))), cv2.COLOR_RGB2BGR))
        cv2.imwrite(f"{PREV}/{session}_f{k:03d}_emission.png", cv2.cvtColor(cv2.resize(E, (480, int(480 * E.shape[0] / E.shape[1]))), cv2.COLOR_RGB2BGR))
log(f"done in {time.time()-t0:.1f}s -> {OUT}/{session}.npz")
