#!/usr/bin/env python3
"""Bootstrap confidence intervals over the per-frame rows pulled from the box (the development machine side).
AUROC CIs: frames resampled with replacement (matched and its paired mismatch travel together), 5,000 resamples, percentile 2.5/97.5.
Mean CIs for PSNR/SSIM: the same frame bootstrap. Usage: python3 ci_summary.py <box_results dir> > ci_summary.json"""
import json, os, sys
import numpy as np

R = sys.argv[1]; B = 5000; rng = np.random.default_rng(20260909)


def auroc(pos, neg):
    pos = np.asarray(pos, float); neg = np.asarray(neg, float)
    return float(((pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum()) / (len(pos) * len(neg)))


def boot_auroc(pos, neg):
    """pooled AUROC (all matched against all mismatched scores) and the paired win rate (frame by frame, ties half), each with a
    frame-bootstrap 95 percent interval; the paired rate is the per-frame question and is not diluted by between-frame differences"""
    pos = np.asarray(pos, float); neg = np.asarray(neg, float); n = len(pos); vals = []; wins = []
    w = (pos > neg).astype(float) + 0.5 * (pos == neg)
    for _ in range(B):
        idx = rng.integers(0, n, n); vals.append(auroc(pos[idx], neg[idx])); wins.append(w[idx].mean())
    return {"n": n, "auroc": auroc(pos, neg), "ci95": [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))], "paired_wins": int((pos > neg).sum()),
            "paired_win_rate": float(w.mean()), "paired_win_ci95": [float(np.percentile(wins, 2.5)), float(np.percentile(wins, 97.5))]}


def boot_mean(x):
    x = np.asarray(x, float); n = len(x); vals = [x[rng.integers(0, n, n)].mean() for _ in range(B)]
    return {"n": n, "mean": float(x.mean()), "ci95": [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]}


out = {}
for root, dirs, files in os.walk(R):
    rel = os.path.relpath(root, R)
    if "d_verifier.json" in files:
        d = json.load(open(os.path.join(root, "d_verifier.json"))); rows = d["per_pair"]
        out[f"{rel}/d_verifier"] = {f"{mode}_{neg}": boot_auroc([r[mode]["matched"] for r in rows], [r[mode][neg] for r in rows]) for mode in ("full", "crop512") for neg in ("capture_swap", "emission_swap")} | {"discriminator": d["discriminator"], "final_act": d.get("final_act")}
    for gf, tag in (("g_verifier.json", "g_verifier"), ("g_verifier_color.json", "g_verifier_color")):
        if gf in files:
            g = json.load(open(os.path.join(root, gf))); rows = [r for r in g["per_frame"] if r["partner"]]
            out[f"{rel}/{tag}"] = {f"{view}_{m}": boot_auroc([r[view][f"{m}_matched"] for r in rows], [r[view][f"{m}_mismatched"] for r in rows]) for view in ("full", "residual") for m in ("corr", "psnr")}
    if "metrics.json" in files:
        m = json.load(open(os.path.join(root, "metrics.json")))
        if "per_frame" in m and isinstance(m["per_frame"], dict):   # eval_p2p: {session: [(name, psnr, ssim), ...]}
            rows = [r for rs in m["per_frame"].values() for r in rs]
            out[f"{rel}/fidelity"] = {"psnr": boot_mean([r[1] for r in rows]), "ssim": boot_mean([r[2] for r in rows])}
        elif "per_frame" in m:                                        # baselines: rows with emission/prev_real/mean_train tuples
            for k in ("emission", "prev_real", "mean_train"):
                vals = [r[k] for r in m["per_frame"] if r.get(k)]
                if vals: out[f"{rel}/baseline_{k}"] = {"psnr": boot_mean([v[0] for v in vals]), "ssim": boot_mean([v[1] for v in vals])}
    for f in files:
        if f.startswith("coupling_") and f.endswith(".json"):
            c = json.load(open(os.path.join(root, f)))
            out[f"{rel}/{f[:-5]}"] = {g: boot_auroc([r["matched"] for r in pf], [r["mismatched"] for r in pf]) for g, pf in c["per_frame"].items() if pf}
json.dump(out, sys.stdout, indent=1)
