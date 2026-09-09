#!/usr/bin/env python3
"""Generator-as-verifier (Old Light edition of the 6 September kit script): does a generated capture identify its own emission?
For every held-out frame t with a generated capture fake_t, the similarity between fake_t and the real capture real_t is compared with
the similarity between fake_s and real_t, s a different held-out frame of the same session (seeded draw). AUROC and paired wins.
Views: FULL and RESIDUAL (a mean training capture subtracted: the session's own training mean where the session has training captures,
otherwise, for the whole held-out session, the mean over all training captures; which one is recorded per session).
Similarities: Pearson correlation and PSNR at 512x288 grey (2024) or 512x320 grey (2023). Per-frame rows persisted for CIs.
  python3 eval_g_verifier.py --fake <dir> --real <test_B dir> --train_b <train_B dir> --out <g_verifier.json> [--size 512x288]"""
import argparse, json, os, random
from multiprocessing import Pool
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--fake", required=True); ap.add_argument("--real", required=True); ap.add_argument("--train_b", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--color", action="store_true", help="per-channel RGB correlation averaged over channels instead of grayscale (the emission patterns vary in hue far more than in luminance); writes g_verifier_color.json")
ap.add_argument("--procs", type=int, default=16); ap.add_argument("--size", default="512x288"); ap.add_argument("--mean_samples", type=int, default=200); ap.add_argument("--seed", type=int, default=20260909)
a = ap.parse_args()
W, H = (int(x) for x in a.size.split("x"))
names = sorted(f for f in os.listdir(a.fake) if f.endswith(".png") and os.path.exists(os.path.join(a.real, f)))
sessions = sorted({n.split("_")[0] for n in names})


def gray(p):
    im = Image.open(p).convert("RGB").resize((W, H), Image.BOX)
    return np.asarray(im, dtype=np.float64) if a.color else np.asarray(im.convert("L"), dtype=np.float64)


def mean_of(files):
    step = max(1, len(files) // a.mean_samples); acc = None; n = 0
    for f in files[::step][:a.mean_samples]:
        x = gray(os.path.join(a.train_b, f)); acc = x if acc is None else acc + x; n += 1
    return acc / n, n


train_files = sorted(os.listdir(a.train_b)); MEANS = {}; MEAN_SRC = {}
for s in sessions:
    own = [f for f in train_files if f.startswith(s + "_")]
    if own: MEANS[s], k = mean_of(own); MEAN_SRC[s] = f"session mean of {k} training captures"
    else: MEANS[s], k = mean_of(train_files); MEAN_SRC[s] = f"no training captures of this session: global mean of {k} training captures"
rng = random.Random(a.seed); partner = {}
for s in sessions:
    ns = [n for n in names if n.startswith(s + "_")]
    for n in ns:
        others = [m for m in ns if m != n]; partner[n] = rng.choice(others) if others else None


def corr1(x, y):
    x = x - x.mean(); y = y - y.mean(); d = np.sqrt((x * x).sum() * (y * y).sum()); return float((x * y).sum() / d) if d > 0 else 0.0
def corr(x, y):
    return float(np.mean([corr1(x[..., c], y[..., c]) for c in range(3)])) if x.ndim == 3 else corr1(x, y)
def psnr(x, y):
    mse = float(((x - y) ** 2).mean()); return 99.0 if mse == 0 else float(10 * np.log10(255.0 ** 2 / mse))


def work(n):
    s = n.split("_")[0]; m = MEANS[s]
    real = gray(os.path.join(a.real, n)); fake = gray(os.path.join(a.fake, n)); other = gray(os.path.join(a.fake, partner[n])) if partner[n] else None
    out = {"name": n, "session": s, "partner": partner[n]}
    for view, (r, f, o) in {"full": (real, fake, other), "residual": (real - m, fake - m, None if other is None else other - m)}.items():
        out[view] = {"corr_matched": corr(f, r), "psnr_matched": psnr(f, r), "corr_mismatched": corr(o, r) if o is not None else None, "psnr_mismatched": psnr(o, r) if o is not None else None}
    return out


def auroc(pos, neg):
    pos = np.asarray(pos); neg = np.asarray(neg); gt = (pos[:, None] > neg[None, :]).sum(); eq = (pos[:, None] == neg[None, :]).sum()
    return float((gt + 0.5 * eq) / (len(pos) * len(neg)))


if __name__ == "__main__":
    with Pool(a.procs) as pool: rows = pool.map(work, names, chunksize=4)
    rows = [r for r in rows if r["partner"]]; results = {}
    for view in ("full", "residual"):
        for metric in ("corr", "psnr"):
            for s in sessions + ["all"]:
                sel = [r for r in rows if s == "all" or r["session"] == s]
                if not sel: continue
                pos = [r[view][f"{metric}_matched"] for r in sel]; neg = [r[view][f"{metric}_mismatched"] for r in sel]
                results[f"{view}_{metric}_{s}"] = {"n": len(sel), "auroc": auroc(pos, neg), "paired_win": float(np.mean([p > q for p, q in zip(pos, neg)])), "matched_mean": float(np.mean(pos)), "mismatched_mean": float(np.mean(neg))}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    if a.color: a.out = a.out.replace("g_verifier.json", "g_verifier_color.json")
    json.dump({"schema": "oldlight-g-verifier/1", "color": a.color, "fake": a.fake, "real": a.real, "frames": len(rows), "size": a.size, "seed": a.seed, "mean_source": MEAN_SRC, "results": results, "per_frame": rows}, open(a.out, "w"), indent=1)
    print("G-VERIFIER", a.out, json.dumps({k: {"auroc": round(v["auroc"], 4), "paired_win": round(v["paired_win"], 4), "n": v["n"]} for k, v in results.items() if k.endswith("_all")}))
