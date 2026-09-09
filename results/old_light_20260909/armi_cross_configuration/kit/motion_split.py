#!/usr/bin/env python3
"""motion_split.py (BOSUN, 2026-09-09): does a person in the beam change the 2024 result? Rows of each 2024 session are split
by the data-look desk's leave-one-out change fraction of the beam (`temporal/model_outlier_frac_inside_per_frame` in
supporting/data_look/figures/2024/<sid>_stats.json; the desk's threshold of 4 percent of the beam marks person/motion
frames), and the frozen per-row scores (correct vs per-row wrong-mean) give AUROC and paired fraction per stratum with
1,000-resample row-bootstrap CIs. Usage: motion_split.py --results DIR --arm NAME [--threshold 0.04]"""
import argparse, glob, json, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from eval_xcfg import row_bootstrap
ap = argparse.ArgumentParser(); ap.add_argument("--results", required=True); ap.add_argument("--arm", required=True)
ap.add_argument("--stats-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "supporting", "data_look")); ap.add_argument("--threshold", type=float, default=0.04)
a = ap.parse_args()
cor, wm, frac = [], [], []
for f in sorted(glob.glob(os.path.join(a.stats_dir, "20241219_*_stats.json"))):   # the published directory holds both eras; the split is a 2024 result
    sid = os.path.basename(f).split("_stats")[0]
    raw = os.path.join(a.results, f"{a.arm}.raw_{sid}.npz")
    if not os.path.isfile(raw): continue
    z = np.load(raw); c = z["correct"]; W = np.stack([z[f"wrong_{o:+d}"] for o in (-2, 2, -15, 15, 30)], 1); w = np.nanmean(W, 1)
    per = json.load(open(f))["temporal"]["model_outlier_frac_inside_per_frame"]
    for i, r in enumerate(z["rows"]):
        cor.append(c[i]); wm.append(w[i]); frac.append(per[int(r)])
cor, wm, frac = np.array(cor), np.array(wm), np.array(frac)
out = {"arm": a.arm, "threshold": a.threshold, "metric": "leave-one-out gain/offset residual fraction of the beam (data-look desk)", "strata": {}}
print(f"| stratum (change fraction of the beam) | rows | AUROC | 95% CI | paired | 95% CI | mean delta |\n|---|---:|---:|---|---:|---|---:|")
for name, m in (("static, <= 4 %", frac <= a.threshold), ("person or motion, > 4 %", frac > a.threshold)):
    rb = row_bootstrap(cor[m], wm[m]); out["strata"][name] = {**rb, "mean_delta": float(np.mean(wm[m] - cor[m])), "mean_correct": float(np.mean(cor[m]))}
    print(f"| {name} | {m.sum()} | {rb['auroc']:.3f} | [{rb['auroc_ci95'][0]:.3f}, {rb['auroc_ci95'][1]:.3f}] | {rb['paired']:.3f} | [{rb['paired_ci95'][0]:.3f}, {rb['paired_ci95'][1]:.3f}] | {np.mean(wm[m]-cor[m]):.2e} |")
rk = lambda x: np.argsort(np.argsort(x)); out["spearman_change_vs_delta"] = float(np.corrcoef(rk(frac), rk(wm - cor))[0, 1])
print(f"Spearman(change fraction, delta) = {out['spearman_change_vs_delta']:.3f} over {cor.size} rows")
json.dump(out, open(os.path.join(a.results, f"{a.arm}.motion_split.json"), "w"), indent=1)
