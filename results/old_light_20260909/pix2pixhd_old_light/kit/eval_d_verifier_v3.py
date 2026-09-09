#!/usr/bin/env python3
"""Discriminator as a correspondence verifier, Old Light edition (adapted from the 6 September kit's eval_d_verifier_v2.py).

Every held-out frame of the given pairs directory is a target; its partner is another held-out frame of the SAME session under a
seeded derangement (no fixed point, bijection within the session); the map is written before any score and shared by every
discriminator scored on the same test set. Scores: mean over the three D scales of the mean final-layer output on cat(E, B), on the
512 centre crop and the full frame. Negatives: capture swap (partner's real capture with the true emission) and emission swap (partner's
emission with the true capture). Every target, partner and score is persisted for bootstrap CIs on the development machine.
The January 2025 discriminator (--d_path) ends each scale with a kernel-1 conv behind an unrecovered parameter-free module; both
reconstructions (--final_act none|lrelu) are scored, as the kit did, and reported as a comparison only.
  python3 eval_d_verifier_v3.py --name ol2024_b4 --pairs <pairs dir> --test test_A --results <dir> --ckpt <dir> [--gpu 0]
  python3 eval_d_verifier_v3.py --name d2025_none --d_path latest_net_D.pth --final_kernel 1 --final_act none ..."""
import argparse, hashlib, json, os, re, sys
import numpy as np, torch
from PIL import Image
sys.path.insert(0, os.getcwd())
from models import networks  # noqa: E402

def roc_auc_score(y, s):
    """Mann-Whitney AUROC (ties count half), identical in value to sklearn.metrics.roc_auc_score; sklearn is avoided because the
    box's Debian scikit-learn/pandas are built against numpy 1.x and fail to import beside the pip numpy 2.2.6."""
    y = np.asarray(y); s = np.asarray(s, dtype=float); pos = s[y == 1]; neg = s[y == 0]
    return float(((pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum()) / (len(pos) * len(neg)))

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True); ap.add_argument("--which_epoch", default="latest"); ap.add_argument("--gpu", type=int, default=0)
ap.add_argument("--pairs", required=True); ap.add_argument("--test", default="test", help="test | heldsession (the _A/_B suffix is added)")
ap.add_argument("--ckpt", required=True); ap.add_argument("--results", required=True); ap.add_argument("--d_path", default=None)
ap.add_argument("--final_kernel", type=int, default=4); ap.add_argument("--final_act", default="none", choices=["none", "lrelu"])
ap.add_argument("--seed", type=int, default=20260909); ap.add_argument("--map", default=None)
ap.add_argument("--meanprior", default=None, help="path of the mean training capture: the discriminator was trained with a 6-channel condition (emission + mean), so the D input has 9 channels")
ap.add_argument("--resize", default=None, help="WxH: resize emission and capture before scoring (a D trained on full frames at 1024 wide is scored at 1024 wide)")
a = ap.parse_args()
torch.manual_seed(0)
dev = torch.device(f"cuda:{a.gpu}")
NAME = re.compile(r"^(?P<s>[a-z0-9]+)_(?P<i>\d{6})\.png$")
A_DIR, B_DIR = os.path.join(a.pairs, a.test + "_A"), os.path.join(a.pairs, a.test + "_B")
names = sorted(n for n in os.listdir(A_DIR) if NAME.match(n) and os.path.exists(os.path.join(B_DIR, n)))
map_path = a.map or os.path.join(a.results, f"d_derangement_{a.test}.json")
os.makedirs(os.path.dirname(map_path), exist_ok=True)
if os.path.exists(map_path):
    M = json.load(open(map_path)); assert M["targets"] == names, "existing map covers another frame set"
else:
    rng = np.random.Generator(np.random.PCG64(a.seed)); by_s = {}
    for t in names: by_s.setdefault(t.split("_")[0], []).append(t)
    partners = {}
    for s, ts in by_s.items():
        if len(ts) < 2: continue
        while True:
            p = rng.permutation(len(ts))
            if not np.any(p == np.arange(len(ts))): break
        for i, t in enumerate(ts): partners[t] = ts[p[i]]
    M = dict(schema="oldlight-d-derangement/1", seed=a.seed, rng="numpy PCG64", test=a.test, n=len(partners), per_session={s: len(ts) for s, ts in by_s.items()}, targets=names, partners=partners,
             checks=dict(within_session=all(t.split("_")[0] == p.split("_")[0] for t, p in partners.items()), no_fixed_point=all(t != p for t, p in partners.items()), bijection=sorted(partners.values()) == sorted(partners)))
    assert all(M["checks"].values()); tmp = map_path + ".tmp"; json.dump(M, open(tmp, "w"), indent=1); os.replace(tmp, map_path)
partners = M["partners"]; targets = sorted(partners)
print(f"map: {len(targets)} targets, sessions {M['per_session']}, checks {M['checks']}", flush=True)

netD = networks.define_D(9 if a.meanprior else 6, 64, 3, "instance", False, 3, True, gpu_ids=[a.gpu])
path = a.d_path or os.path.join(a.ckpt, a.name, f"{a.which_epoch}_net_D.pth")
state = torch.load(path, map_location="cpu")
if a.final_kernel == 1:
    import torch.nn as nn
    for s_idx in range(3):
        act = nn.LeakyReLU(0.2, True) if a.final_act == "lrelu" else nn.Identity()
        setattr(netD, f"scale{s_idx}_layer4", nn.Sequential(act, nn.Conv2d(512, 1, kernel_size=1)))
netD.load_state_dict(state); netD.eval(); netD.to(dev)
d_sha = hashlib.sha256(open(path, "rb").read()).hexdigest()

RS = tuple(int(x) for x in a.resize.split("x")) if a.resize else None
def load(d, n):
    img = Image.open(os.path.join(d, n)).convert("RGB")
    if RS: img = img.resize(RS, Image.LANCZOS)
    im = np.asarray(img, dtype=np.float32) / 127.5 - 1.0
    return torch.from_numpy(im).permute(2, 0, 1)
def centre(x):
    h, w = x.shape[-2:]; return x[..., h // 2 - 256: h // 2 + 256, w // 2 - 256: w // 2 + 256]
MEAN_T = None
if a.meanprior:
    _m = Image.open(a.meanprior).convert("RGB")
    if RS: _m = _m.resize(RS, Image.LANCZOS)
    MEAN_T = torch.from_numpy(np.asarray(_m, dtype=np.float32) / 127.5 - 1.0).permute(2, 0, 1)
def cond(E):
    if MEAN_T is None: return E
    M = MEAN_T if MEAN_T.shape[-2:] == E.shape[-2:] else centre(MEAN_T)
    return torch.cat([E, M], 0)
@torch.no_grad()
def score(E, B):
    E = cond(E)
    out = netD(torch.cat([E, B], 0).unsqueeze(0).to(dev))
    return float(np.mean([o[-1].mean().item() for o in out]))

rows = []
for i, t in enumerate(targets):
    p = partners[t]; E, B = load(A_DIR, t), load(B_DIR, t); B2 = load(B_DIR, p); E2 = load(A_DIR, p)
    r = dict(target=t, partner=p, session=t.split("_")[0])
    for mode, (e, b, b2, e2) in {"full": (E, B, B2, E2), "crop512": (centre(E), centre(B), centre(B2), centre(E2))}.items():
        r[mode] = dict(matched=score(e, b), capture_swap=score(e, b2), emission_swap=score(e2, b))
    rows.append(r)
    if i % 25 == 0: print(f"{i}/{len(targets)} scored", flush=True)
sessions = sorted({r["session"] for r in rows}); results = {}
for mode in ("full", "crop512"):
    for label, key in (("", "capture_swap"), ("_emission_swap", "emission_swap")):
        for s in sessions + ["pooled"]:
            sel = [r for r in rows if s == "pooled" or r["session"] == s]
            pos = [r[mode]["matched"] for r in sel]; neg = [r[mode][key] for r in sel]
            wins = sum(1 for m, q in zip(pos, neg) if m > q); ties = sum(1 for m, q in zip(pos, neg) if m == q)
            results[f"{mode}{label}:{s}"] = dict(n_pairs=len(sel), auroc_matched_vs_mismatched=float(roc_auc_score([1] * len(pos) + [0] * len(neg), pos + neg)), wins=wins, ties=ties,
                                                 paired_ordering=(wins + 0.5 * ties) / len(sel), matched_mean=float(np.mean(pos)), mismatched_mean=float(np.mean(neg)))
out = os.path.join(a.results, a.name, a.which_epoch + ("_held" if a.test == "heldsession" else "")); os.makedirs(out, exist_ok=True)
json.dump({"schema": "oldlight-d-verifier/1", "discriminator": path, "discriminator_sha256": d_sha, "final_kernel": a.final_kernel, "final_act": a.final_act, "resize": a.resize, "meanprior": a.meanprior, "test": a.test, "pairs": a.pairs,
           "map": map_path, "map_sha256": hashlib.sha256(open(map_path, "rb").read()).hexdigest(), "results": results, "per_pair": rows}, open(os.path.join(out, "d_verifier.json"), "w"), indent=1)
print("D-VERIFIER", a.name, a.test, json.dumps({k: round(v["auroc_matched_vs_mismatched"], 4) for k, v in results.items() if k.endswith(":pooled")}))
