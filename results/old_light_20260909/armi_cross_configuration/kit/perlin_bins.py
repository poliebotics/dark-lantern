#!/usr/bin/env python3
"""perlin_bins.py (BOSUN, 2026-09-09): the free spatial-frequency sweep inside 2024. Each 2024 frame's Perlin period is fixed
by its chain hash (data-look desk, supporting/data_look/stats/perlin_params_<sid>.json: per-channel scale in cycles per px;
period = 1/scale, 40 to 200 px). Rows are binned by the frame's mean period over its three channels and the frozen per-row
scores (correct vs per-row wrong-mean) give AUROC and paired fraction per bin, with 1,000-resample row bootstrap CIs.
Usage: perlin_bins.py --results DIR --arm NAME [--params-dir DIR]"""
import argparse, glob, json, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from eval_xcfg import auroc_pooled, row_bootstrap
ap = argparse.ArgumentParser(); ap.add_argument("--results", required=True); ap.add_argument("--arm", required=True)
ap.add_argument("--params-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "perlin")); ap.add_argument("--edges", default="40,60,80,110,200")
ap.add_argument("--suffix", default="raw")
a = ap.parse_args()
edges = [float(x) for x in a.edges.split(",")]
per, cor, wm, sids = [], [], [], []
for f in sorted(glob.glob(os.path.join(a.params_dir, "perlin_params_*.json"))):
    p = json.load(open(f)); sid = p["session"]
    raw = os.path.join(a.results, f"{a.arm}.{a.suffix}_{sid}.npz")
    if not os.path.isfile(raw): continue
    z = np.load(raw); c = z["correct"]; W = np.stack([z[f"wrong_{o:+d}"] for o in (-2, 2, -15, 15, 30)], 1); w = np.nanmean(W, 1)
    periods = {fr["frame"]: float(np.mean([1.0 / s for s in fr["scales_rgb"]])) for fr in p["frames"]}
    for i, r in enumerate(z["rows"]):
        if int(r) in periods and np.isfinite(c[i]) and np.isfinite(w[i]):
            per.append(periods[int(r)]); cor.append(c[i]); wm.append(w[i]); sids.append(sid)
per, cor, wm = np.array(per), np.array(cor), np.array(wm)
out = {"arm": a.arm, "n_rows": int(per.size), "period_definition": "mean over RGB of 1/scale (px on the 1920x1080 display); camera px = 2.40 x", "bins": []}
print(f"| period bin (display px) | rows | AUROC | 95% CI | paired | 95% CI | mean delta |")
print("|---|---:|---:|---|---:|---|---:|")
for lo, hi in zip(edges[:-1], edges[1:]):
    m = (per >= lo) & (per < hi)
    if m.sum() < 5: continue
    rb = row_bootstrap(cor[m], wm[m])
    out["bins"].append({"lo": lo, "hi": hi, "n": int(m.sum()), **rb, "mean_delta": float(np.mean(wm[m] - cor[m]))})
    print(f"| {lo:.0f} to {hi:.0f} | {m.sum()} | {rb['auroc']:.3f} | [{rb['auroc_ci95'][0]:.3f}, {rb['auroc_ci95'][1]:.3f}] | {rb['paired']:.3f} | [{rb['paired_ci95'][0]:.3f}, {rb['paired_ci95'][1]:.3f}] | {np.mean(wm[m]-cor[m]):.2e} |")
# Spearman rank correlation between period and per-row delta
d = wm - cor
rk = lambda x: np.argsort(np.argsort(x))
rho = float(np.corrcoef(rk(per), rk(d))[0, 1]) if per.size > 2 else float("nan")
out["spearman_period_vs_delta"] = rho
print(f"\nSpearman(period, wrong-correct delta) = {rho:.3f} over {per.size} rows")
json.dump(out, open(os.path.join(a.results, f"{a.arm}.perlin_bins.json"), "w"), indent=1)
