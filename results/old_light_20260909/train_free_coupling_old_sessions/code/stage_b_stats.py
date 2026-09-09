#!/usr/bin/env python3
"""Stage B: the statistic over the cached grids. Usage: python3 stage_b_stats.py <era> <session> [<session> ...]
Mismatch partners follow the reference construction (random.seed(0); one shuffle per grid per session, sessions in the
given order) and are shared by the full-frame and cropped variants of the same grid. Orientation per session is decided
on the first min(4, n) frames at grid 8 on the cropped variant (both values recorded). Writes results/<era>_results.json,
results/<era>_scores.csv (per frame, per grid, per variant: matched and mismatched scores and partner index),
results/<era>_partners.json.
"""
import sys, os, json, csv
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coupling_lib import *

era = sys.argv[1]; sessions = sys.argv[2:]
CACHE = os.environ.get("COUPLING_CACHE", "coupling_cache")
PKG = os.environ.get("COUPLING_PKG", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); GEOM = os.path.join(PKG, "geometry")
RES = os.path.join(PKG, "results"); os.makedirs(RES, exist_ok=True)

data, names_by_session, geom = {}, {}, {}
for s in sessions:
    z = np.load(f"{CACHE}/{s}.npz")
    data[s] = {k: z[k] for k in z.files}
    if os.path.exists(f"{CACHE}/{s}.export75.npz"):
        z2 = np.load(f"{CACHE}/{s}.export75.npz")
        assert len(z2["idxs"]) == len(z["idxs"]), "export75 cache frame count differs"
        data[s].update({k: z2[k] for k in z2.files if k.startswith("Rexport75_")})
    geom[s] = json.load(open(f"{GEOM}/{s}.geometry.json"))
    names_by_session[s] = [f"{s}_{int(i):06d}" for i in z["idxs"]]

partners = mismatch_partners(names_by_session)  # partners[g][s] = list of partner names
pos = {s: {n: i for i, n in enumerate(ns)} for s, ns in names_by_session.items()}

# orientation decision (calibration frames, grid 8, crop)
orientation = {}
for s in sessions:
    k = min(4, len(names_by_session[s]))
    c = {o: float(np.mean([corr(data[s][f"E{o}_8"][i], data[s]["Rcrop_8"][i]) for i in range(k)])) for o in (0, 180)}
    orientation[s] = {"chosen": 0 if c[0] >= c[180] else 180, "calib_frames": k, "corr_grid8_crop": c}

def channel_matrix(s, g=16):
    o = orientation[s]["chosen"]; E = data[s][f"E{o}_{g}"]; R = data[s]["Rcrop_{}".format(g)]
    M = np.zeros((3, 3))
    for i in range(len(E)):
        for a in range(3):
            for b in range(3):
                M[a, b] += np.corrcoef(E[i][..., a].ravel(), R[i][..., b].ravel())[0, 1]
    return (M / len(E)).round(4).tolist()

def cell_corr_map(s, g=16, variant="crop"):
    """Per-cell correlation over frames between the emission cell value and the recording cell value (mean of channels);
    a diagnostic of alignment, positive across the whole grid when the crop is right. Uses matched frames only."""
    o = orientation[s]["chosen"]; E = data[s][f"E{o}_{g}"]; R = data[s][f"R{variant}_{g}"]
    if len(E) < 4:
        return None
    m = np.zeros((g, g))
    for c in range(3):
        e = E[..., c]; r = R[..., c]
        e = e - e.mean(axis=0); r = r - r.mean(axis=0)
        m += (e * r).sum(axis=0) / (np.sqrt((e * e).sum(axis=0) * (r * r).sum(axis=0)) + 1e-9)
    return (m / 3)

diag_maps = {}
for s in sessions:
    diag_maps[f"{s}_crop"] = cell_corr_map(s, 16, "crop"); diag_maps[f"{s}_full"] = cell_corr_map(s, 16, "full")
np.savez(f"{RES}/{era}_cellcorr_maps.npz", **{k: v for k, v in diag_maps.items() if v is not None})

out = {"era": era, "sessions": {s: {"n": len(names_by_session[s]), "orientation": orientation[s], "geometry": geom[s]["geometry"], "source": geom[s]["source"],
                                    "channel_matrix_grid16_crop_Erows_Rcols": channel_matrix(s),
                                    "cellcorr16_crop_mean": (None if diag_maps[f"{s}_crop"] is None else float(diag_maps[f"{s}_crop"].mean())),
                                    "cellcorr16_crop_frac_positive": (None if diag_maps[f"{s}_crop"] is None else float((diag_maps[f"{s}_crop"] > 0).mean())),
                                    "cellcorr16_full_mean": (None if diag_maps[f"{s}_full"] is None else float(diag_maps[f"{s}_full"].mean()))} for s in sessions},
       "grids": {}}
VARIANTS = ["full", "crop", "crop_bgr"]
if all(f"Rexport75_{GRIDS[0]}" in data[s] for s in sessions):
    VARIANTS += ["export75", "export75_bgr"]
out["variants"] = {"full": "whole recording frame", "crop": "emission-blind projected-region quad, warped to the displayed emission aspect",
                   "crop_bgr": "control: the crop with the recording's channels reversed (stored byte order against the RGB emission)",
                   "export75": "January 2025 exporter geometry: centre 75 percent of the recording height at full width, RGB-corrected",
                   "export75_bgr": "January 2025 exporter geometry with its stored (BGR) byte order against the RGB emission, as that exporter paired them"}
def rgrid(s, variant, g):
    if variant == "full": return data[s][f"Rfull_{g}"]
    if variant == "crop": return data[s][f"Rcrop_{g}"]
    if variant == "crop_bgr": return data[s][f"Rcrop_{g}"][..., ::-1]
    if variant == "export75": return data[s][f"Rexport75_{g}"]
    if variant == "export75_bgr": return data[s][f"Rexport75_{g}"][..., ::-1]
    raise KeyError(variant)
rows = []
for g in GRIDS:
    out["grids"][str(g)] = {}
    for variant in VARIANTS:
        res = {}; all_m, all_mm = [], []
        for s in sessions:
            ns = names_by_session[s]; o = orientation[s]["chosen"]
            E = data[s][f"E{o}_{g}"]; R = rgrid(s, variant, g)
            matched = [corr(E[i], R[i]) for i in range(len(ns))]
            mism = [corr(E[i], R[pos[s][p]]) for i, p in enumerate(partners[g][s])]
            for i, (n, p, a, b) in enumerate(zip(ns, partners[g][s], matched, mism)):
                rows.append({"session": s, "frame": n, "grid": g, "variant": variant, "orientation": o, "matched": a, "mismatched": b, "partner": p})
            r = {"n": len(ns), "auroc": auroc(matched, mism), "paired_matched_greater": paired_frac(matched, mism), "wins": int(sum(a > b for a, b in zip(matched, mism))),
                 "matched_mean": float(np.mean(matched)), "mismatched_mean": float(np.mean(mism))}
            r.update(bootstrap_ci(matched, mism)); r["control"] = shuffled_label_control(matched, mism)
            res[s] = r; all_m += matched; all_mm += mism
        pooled = {"n_pairs": len(all_m), "auroc": auroc(all_m, all_mm), "paired_matched_greater": paired_frac(all_m, all_mm), "wins": int(sum(a > b for a, b in zip(all_m, all_mm))),
                  "matched_mean": float(np.mean(all_m)), "mismatched_mean": float(np.mean(all_mm))}
        pooled.update(bootstrap_ci(all_m, all_mm)); pooled["control"] = shuffled_label_control(all_m, all_mm)
        res["pooled"] = pooled
        out["grids"][str(g)][variant] = res
        print(f"{era} grid {g:2d} {variant:12s}: pooled AUROC {pooled['auroc']:.4f} [{pooled['auroc_ci95'][0]:.3f},{pooled['auroc_ci95'][1]:.3f}] paired {pooled['wins']}/{pooled['n_pairs']} "
              f"ctrl {pooled['control']['one_shuffle_auroc']:.3f}; " + "; ".join(f"{s} {r['auroc']:.3f}" for s, r in res.items() if s != "pooled"), flush=True)

json.dump(out, open(f"{RES}/{era}_results.json", "w"), indent=1)
json.dump({str(g): partners[g] for g in GRIDS}, open(f"{RES}/{era}_partners.json", "w"), indent=1)
with open(f"{RES}/{era}_scores.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("orientation:", {s: orientation[s] for s in sessions})
print("written", f"{RES}/{era}_results.json")
