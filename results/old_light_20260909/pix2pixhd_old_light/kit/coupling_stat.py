#!/usr/bin/env python3
"""Train-free optical coupling statistic on a held-out set (Old Light edition of the kit script; statistic unchanged and predeclared):
for each pair, downsample the emission E and the capture B to a g x g grid of mean colours, standardise per channel, take the mean over
channels of the Pearson correlation between the grids. g in {4, 8, 16, 32, 64}. Mismatch: the capture of another held-out frame of the
same session under a seeded derangement (one per grid, as in the kit). AUROC per session and pooled, paired wins; per-frame values persisted.
  python3 coupling_stat.py --test_a <dir> --test_b <dir> --out <coupling_stat.json>"""
import argparse, json, os, random
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image

def roc_auc_score(y, s):
    """Mann-Whitney AUROC (ties count half), identical in value to sklearn.metrics.roc_auc_score; sklearn is avoided because the
    box's Debian scikit-learn/pandas are built against numpy 1.x and fail to import beside the pip numpy 2.2.6."""
    y = np.asarray(y); s = np.asarray(s, dtype=float); pos = s[y == 1]; neg = s[y == 0]
    return float(((pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum()) / (len(pos) * len(neg)))

ap = argparse.ArgumentParser(); ap.add_argument("--test_a", required=True); ap.add_argument("--test_b", required=True); ap.add_argument("--out", required=True); ap.add_argument("--procs", type=int, default=16)
ap.add_argument("--swap_emission_rb", action="store_true", help="reverse the emission channel order before correlating (the stored emission and capture orders are opposite in both eras; channel_check.py)")
a = ap.parse_args()
GRIDS = (4, 8, 16, 32, 64); random.seed(0)


def grid(img, g):
    x = np.asarray(img, dtype=np.float32); h, w, _ = x.shape; x = x[: (h // g) * g, : (w // g) * g]
    cells = x.reshape(g, h // g, g, w // g, 3).mean(axis=(1, 3)); cells = cells - cells.mean(axis=(0, 1), keepdims=True)
    return cells / (cells.std(axis=(0, 1), keepdims=True) + 1e-6)
def load_grids(name):
    E = Image.open(os.path.join(a.test_a, name)).convert("RGB"); B = Image.open(os.path.join(a.test_b, name)).convert("RGB")
    if a.swap_emission_rb: E = Image.fromarray(np.asarray(E)[..., ::-1].copy())
    return name, {g: grid(E, g) for g in GRIDS}, {g: grid(B, g) for g in GRIDS}
def corr(x, y): return float(np.mean([np.corrcoef(x[..., c].ravel(), y[..., c].ravel())[0, 1] for c in range(3)]))


def main():
    names = sorted(n for n in os.listdir(a.test_a) if n.endswith(".png") and os.path.exists(os.path.join(a.test_b, n)))
    with ProcessPoolExecutor(max_workers=a.procs) as ex: data = {n: (e, b) for n, e, b in ex.map(load_grids, names, chunksize=2)}
    by_session = {}
    for n in names: by_session.setdefault(n.split("_")[0], []).append(n)
    out = {"schema": "oldlight-coupling/1", "emission_channels_reversed": a.swap_emission_rb, "n_frames": len(names), "sessions": {s: len(v) for s, v in by_session.items()}, "grids": {}, "per_frame": {}}
    for g in GRIDS:
        res = {}; all_y, all_s, wins_all, n_all = [], [], 0, 0; pf = []
        for s, ns in by_session.items():
            if len(ns) < 2: continue
            shuffled = ns[:]; random.shuffle(shuffled)
            mism = [m if m != n else shuffled[(i + 1) % len(shuffled)] for i, (n, m) in enumerate(zip(ns, shuffled))]
            matched = [corr(data[n][0][g], data[n][1][g]) for n in ns]; mismatched = [corr(data[n][0][g], data[m][1][g]) for n, m in zip(ns, mism)]
            y = [1] * len(ns) + [0] * len(ns); sc = matched + mismatched; wins = sum(1 for p, q in zip(matched, mismatched) if p > q)
            res[s] = {"n": len(ns), "auroc": float(roc_auc_score(y, sc)), "matched_mean": float(np.mean(matched)), "mismatched_mean": float(np.mean(mismatched)), "paired_matched_greater": wins / len(ns)}
            all_y += y; all_s += sc; wins_all += wins; n_all += len(ns); pf += [{"name": n, "partner": m, "session": s, "matched": p, "mismatched": q} for n, m, p, q in zip(ns, mism, matched, mismatched)]
        res["pooled"] = {"n_pairs": n_all, "auroc": float(roc_auc_score(all_y, all_s)), "paired_matched_greater": wins_all / n_all}
        out["grids"][str(g)] = res; out["per_frame"][str(g)] = pf
        print(f"grid {g:2d}: pooled AUROC {res['pooled']['auroc']:.4f}, paired wins {wins_all}/{n_all}", flush=True)
    os.makedirs(os.path.dirname(a.out), exist_ok=True); json.dump(out, open(a.out, "w"), indent=1); print("written", a.out)


if __name__ == "__main__":
    main()
