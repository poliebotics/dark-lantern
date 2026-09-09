#!/usr/bin/env python3
"""Trivial-predictor baselines on a held-out set (Old Light edition of the kit script), PSNR/SSIM at the pair resolution:
  emission    the emission frame as the predicted capture;  prev_real  the previous held-out real capture (by index) as the prediction;
  mean_train  the session's mean training capture, or, for a whole held-out session, the mean over all training captures (recorded).
  python3 eval_baselines.py --test_a <dir> --test_b <dir> --train_b <dir> --out <metrics.json>"""
import argparse, json, os, re
from multiprocessing import Pool
import numpy as np
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

ap = argparse.ArgumentParser()
ap.add_argument("--test_a", required=True); ap.add_argument("--test_b", required=True); ap.add_argument("--train_b", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--procs", type=int, default=16); ap.add_argument("--mean_samples", type=int, default=200)
ap.add_argument("--size", default=None, help="WxH: resize real and predictions to this size before scoring (the full-frame models output 1024 wide)")
a = ap.parse_args()
NAME = re.compile(r"^(?P<s>[a-z0-9]+)_(?P<i>\d{6})\.png$")
names = sorted(n for n in os.listdir(a.test_b) if NAME.match(n)); test_set = set(names)


SIZE = tuple(int(x) for x in a.size.split("x")) if a.size else None


def load(p, size=None):
    im = Image.open(p).convert("RGB"); size = size or SIZE
    if size and im.size != size: im = im.resize(size, Image.LANCZOS)
    return np.array(im)
def prev_name(n):
    m = NAME.match(n); c = f"{m.group('s')}_{int(m.group('i')) - 1:06d}.png"; return c if c in test_set else None
def metrics(real, pred): return float(peak_signal_noise_ratio(real, pred, data_range=255)), float(structural_similarity(real, pred, channel_axis=2, data_range=255))


train_files = sorted(os.listdir(a.train_b)); MEANS = {}; MEAN_SRC = {}
def mean_of(files):
    step = max(1, len(files) // a.mean_samples); acc = None; n = 0
    for f in files[::step][:a.mean_samples]:
        x = load(os.path.join(a.train_b, f)).astype(np.float64); acc = x if acc is None else acc + x; n += 1
    return np.clip(acc / n, 0, 255).astype(np.uint8), n
for s in sorted({n.split("_")[0] for n in names}):
    own = [f for f in train_files if f.startswith(s + "_")]
    MEANS[s], k = mean_of(own if own else train_files); MEAN_SRC[s] = (f"session mean of {k} training captures" if own else f"no training captures of this session: global mean of {k} training captures")


def work(n):
    real = load(os.path.join(a.test_b, n)); size = (real.shape[1], real.shape[0]); out = {"name": n, "session": n.split("_")[0]}
    out["emission"] = metrics(real, load(os.path.join(a.test_a, n), size)); p = prev_name(n)
    out["prev_real"] = metrics(real, load(os.path.join(a.test_b, p), size)) if p else None
    out["mean_train"] = metrics(real, MEANS[out["session"]]); return out


def summarise(rows, key):
    summ = {}
    for s in sorted({r["session"] for r in rows}) + ["all"]:
        vals = [r[key] for r in rows if (s == "all" or r["session"] == s) and r[key] is not None]
        if vals:
            ps, ss = np.array([v[0] for v in vals]), np.array([v[1] for v in vals])
            summ[s] = {"frames": len(vals), "psnr_mean": float(ps.mean()), "psnr_median": float(np.median(ps)), "ssim_mean": float(ss.mean()), "ssim_median": float(np.median(ss))}
    return summ


if __name__ == "__main__":
    with Pool(a.procs) as pool: rows = pool.map(work, names, chunksize=2)
    summary = {k: summarise(rows, k) for k in ("emission", "prev_real", "mean_train")}
    summary["note"] = {"size": a.size or "native", "emission": "emission frame as the prediction", "prev_real": "previous held-out real capture as the prediction (frames without a held-out predecessor skipped)", "mean_train": MEAN_SRC, "frames": len(names)}
    os.makedirs(os.path.dirname(a.out), exist_ok=True); json.dump({"schema": "oldlight-baselines/1", "summary": summary, "per_frame": rows}, open(a.out, "w"), indent=1)
    print("BASELINES", a.out, json.dumps({k: {s: {m: round(v[m], 3) for m in ("psnr_mean", "ssim_mean")} for s, v in summary[k].items()} for k in ("emission", "prev_real", "mean_train")}))
