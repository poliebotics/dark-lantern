#!/usr/bin/env python3
"""Does an emission-informed homography beat the emission-blind quad? Split the session's frames into a fit half (odd
positions) and an evaluation half (even positions). On the fit half, refine the 8 quad coordinates by Nelder-Mead to
maximise the mean grid-16 matched statistic (working scale, 1/4 recording). On the evaluation half, compute the grid-8,
16 and 32 AUROC (one seeded same-half mismatch) at full resolution with (a) the emission-blind quad from stage A and
(b) the refined quad. Usage: python3 refine_check.py <era> <session> <source>. Writes results/refine_check_<session>.json."""
import sys, os, json, time, random
import numpy as np, cv2
from scipy.optimize import minimize
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coupling_lib import *
era, session, source = sys.argv[1:4]
PKG = os.environ.get("COUPLING_PKG", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); RES = os.path.join(PKG, "results")
geom = json.load(open(f"{PKG}/geometry/{session}.geometry.json"))
quad0 = np.array(geom["geometry"]["quad_full_xy_TL_TR_BR_BL"], dtype=np.float64)
OUT_WH = tuple(geom["crop_out_wh"])
res_b = json.load(open(f"{RES}/{era}_results.json"))
orientation = res_b["sessions"][session]["orientation"]["chosen"]
t0 = time.time()
if era == "2023":
    pairs = list_2023_session(source)
    n = len(pairs)
    def load_pair(k):
        i, ep, rp = pairs[k]; return load_2023_emission(ep), load_2023_report(rp)
else:
    import h5py
    hf = h5py.File(source, "r"); n = hf["emissions"].shape[0]
    def load_pair(k):
        return np.array(hf["emissions"][k]), load_2024_recording(np.array(hf["recordings"][k]))
fit_idx = list(range(1, n, 2)); eval_idx = list(range(0, n, 2))
DS = 4
E_fit_g16, R_fit_small = [], []
for k in fit_idx:
    E, R = load_pair(k)
    E_fit_g16.append(grid(orient(E, orientation), 16))
    R_fit_small.append(cv2.resize(R, (R.shape[1] // DS, R.shape[0] // DS), interpolation=cv2.INTER_AREA))
small_wh = (OUT_WH[0] // DS, OUT_WH[1] // DS)

def objective(q):
    qq = q.reshape(4, 2) / DS
    vals = []
    for e16, Rs in zip(E_fit_g16, R_fit_small):
        crop = warp_quad(Rs, qq, small_wh)
        vals.append(corr(e16, grid(crop, 16)))
    return -float(np.mean(vals))

f0 = -objective(quad0.ravel())
opt = minimize(objective, quad0.ravel(), method="Nelder-Mead", options={"xatol": 0.5, "fatol": 1e-4, "maxiter": 1500, "maxfev": 1500, "initial_simplex": None})
quad1 = opt.x.reshape(4, 2)
f1 = -opt.fun
shift = np.linalg.norm(quad1 - quad0, axis=1)
print(f"{session}: fit frames {len(fit_idx)}; mean grid-16 matched corr blind {f0:.4f} -> refined {f1:.4f}; corner shifts (full px) {np.round(shift, 1).tolist()}; nfev {opt.nfev}; {time.time()-t0:.0f}s", flush=True)

# evaluation half at full resolution, same partners for both quads
random.seed(0)
names = [f"{session}_{k:06d}" for k in eval_idx]
shuffled = names[:]; random.shuffle(shuffled)
partners = [m if m != nm else shuffled[(i + 1) % len(shuffled)] for i, (nm, m) in enumerate(zip(names, shuffled))]
pos = {nm: i for i, nm in enumerate(names)}
G = (8, 16, 32)
Eg = {g: [] for g in G}; Rg = {"blind": {g: [] for g in G}, "refined": {g: [] for g in G}}
for k in eval_idx:
    E, R = load_pair(k); Eo = orient(E, orientation)
    for g in G:
        Eg[g].append(grid(Eo, g))
    cb = warp_quad(R, quad0, OUT_WH); cr = warp_quad(R, quad1, OUT_WH)
    for g in G:
        Rg["blind"][g].append(grid(cb, g)); Rg["refined"][g].append(grid(cr, g))
out = {"session": session, "era": era, "n": n, "fit_frames": fit_idx, "eval_frames": eval_idx, "orientation": orientation,
       "quad_blind": quad0.tolist(), "quad_refined": quad1.tolist(), "corner_shift_px": shift.tolist(),
       "fit_mean_corr16_blind": f0, "fit_mean_corr16_refined": f1, "nelder_mead_nfev": int(opt.nfev), "eval": {}}
for variant in ("blind", "refined"):
    out["eval"][variant] = {}
    for g in G:
        matched = [corr(Eg[g][i], Rg[variant][g][i]) for i in range(len(eval_idx))]
        mism = [corr(Eg[g][i], Rg[variant][g][pos[p]]) for i, p in enumerate(partners)]
        r = {"auroc": auroc(matched, mism), "wins": int(sum(a > b for a, b in zip(matched, mism))), "n": len(matched), "matched_mean": float(np.mean(matched))}
        r.update(bootstrap_ci(matched, mism)); out["eval"][variant][str(g)] = r
        print(f"  eval {variant:8s} grid {g:2d}: AUROC {r['auroc']:.4f} {r['auroc_ci95']} wins {r['wins']}/{r['n']} matched mean {r['matched_mean']:.4f}", flush=True)
out["elapsed_s"] = round(time.time() - t0, 1)
json.dump(out, open(f"{RES}/refine_check_{session}.json", "w"), indent=1)
print("written", f"{RES}/refine_check_{session}.json")
