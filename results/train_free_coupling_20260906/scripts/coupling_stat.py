#!/usr/bin/env python3
"""Train-free optical coupling statistic on the held-out pairs (TB-Q2 in OPEN_QUESTIONS): does a predeclared analytic
statistic over (emission, capture) discriminate matched pairs from mismatched pairs (the capture of another held-out frame
of the same session) without any learned verifier? CPU only, all cores.

Statistic (predeclared here, before any result was looked at): for each pair, downsample the emission E and the capture B
to a grid of g x g cells (mean colour per cell), remove each image's per-channel mean and divide by its per-channel std,
then take the mean over channels of the Pearson correlation between the E grid and the B grid. Reported for g in
{4, 8, 16, 32, 64}. AUROC of matched vs mismatched, per session and pooled; also the fraction of frames whose matched
statistic exceeds their mismatched one (paired comparison). Writes results/coupling_stat.json.
"""
import json, os, random, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image
from sklearn.metrics import roc_auc_score

PAIRS = sys.argv[1] if len(sys.argv) > 1 else "pairs"
OUT = sys.argv[2] if len(sys.argv) > 2 else "results/coupling_stat.json"
GRIDS = (4, 8, 16, 32, 64)
random.seed(0)


def grid(img, g):
    a = np.asarray(img, dtype=np.float32)
    h, w, _ = a.shape
    a = a[: (h // g) * g, : (w // g) * g]
    cells = a.reshape(g, (h // g), g, (w // g), 3).mean(axis=(1, 3))  # g x g x 3
    cells = cells - cells.mean(axis=(0, 1), keepdims=True)
    cells = cells / (cells.std(axis=(0, 1), keepdims=True) + 1e-6)
    return cells


def load_grids(name):
    E = Image.open(os.path.join(PAIRS, "test_A", name)).convert("RGB")
    B = Image.open(os.path.join(PAIRS, "test_B", name)).convert("RGB")
    return name, {g: grid(E, g) for g in GRIDS}, {g: grid(B, g) for g in GRIDS}


def corr(a, b):
    return float(np.mean([np.corrcoef(a[..., c].ravel(), b[..., c].ravel())[0, 1] for c in range(3)]))


def main():
    names = sorted(os.listdir(os.path.join(PAIRS, "test_A")))
    with ProcessPoolExecutor(max_workers=min(200, os.cpu_count() or 8)) as ex:
        data = {n: (e, b) for n, e, b in ex.map(load_grids, names, chunksize=4)}
    by_session = {}
    for n in names:
        by_session.setdefault(n.split("_")[0], []).append(n)
    out = {"n_frames": len(names), "sessions": {s: len(v) for s, v in by_session.items()}, "grids": {}}
    for g in GRIDS:
        res = {}
        all_y, all_s, paired_wins, paired_n = [], [], 0, 0
        for s, ns in by_session.items():
            shuffled = ns[:]
            random.shuffle(shuffled)
            mism = [m if m != n else shuffled[(i + 1) % len(shuffled)] for i, (n, m) in enumerate(zip(ns, shuffled))]
            matched = [corr(data[n][0][g], data[n][1][g]) for n in ns]
            mismatched = [corr(data[n][0][g], data[m][1][g]) for n, m in zip(ns, mism)]
            y = [1] * len(ns) + [0] * len(ns); sc = matched + mismatched
            wins = sum(1 for a, b in zip(matched, mismatched) if a > b)
            res[s] = {"n": len(ns), "auroc": float(roc_auc_score(y, sc)), "matched_mean": float(np.mean(matched)),
                      "mismatched_mean": float(np.mean(mismatched)), "paired_matched_greater": wins / len(ns)}
            all_y += y; all_s += sc; paired_wins += wins; paired_n += len(ns)
        res["pooled"] = {"n_pairs": paired_n, "auroc": float(roc_auc_score(all_y, all_s)), "paired_matched_greater": paired_wins / paired_n}
        out["grids"][str(g)] = res
        print(f"grid {g:2d}: pooled AUROC {res['pooled']['auroc']:.4f}, paired wins {paired_wins}/{paired_n}; " + "; ".join(f"{s} AUROC {r['auroc']:.4f}" for s, r in res.items() if s != "pooled"), flush=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w"), indent=1)
    print("written", OUT)


if __name__ == "__main__":
    main()
