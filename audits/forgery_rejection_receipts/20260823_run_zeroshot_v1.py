#!/usr/bin/env python3
"""Phase G verifier, zero-shot, on the August 2026 ZeeBeam 300 s training take.

Reads ONLY stage/live_300s_training_001 (712 development rows). Never touches the
120 s verification take. Uses the published model_final.pt and the exact Phase G
input contract (pack, crop, /255, area resize, 11-ch hint, cosine schedule, seeded
shared noise, bf16 forward, float32 MSE). Scoring protocol is the paper's, thinned:
timesteps (150, 300, 500), K noise draws, wrong-emission offsets inside the take,
an unconditioned arm, pooled tie-aware AUROC, block bootstrap over contiguous blocks.
"""
from __future__ import annotations
import argparse, hashlib, json, math, sys, time
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

VERIFIER_SRC = Path("<machine path redacted>")
sys.path.insert(0, str(VERIFIER_SRC))
from phase_g.diffusion_diagnostic_model import (  # noqa: E402
    DiffusionDiagnosticUNet, build_diffusion_constants, q_sample)


def block_bootstrap_ci(values, block_lengths, n_boot=1000, alpha=0.05, seed=0):
    """Verbatim logic of eval_diffusion_diagnostic.block_bootstrap_ci (inlined: that module imports cv2)."""
    rng = np.random.RandomState(seed)
    b = [0]
    for L in block_lengths:
        b.append(b[-1] + L)
    blocks = [values[b[i]:b[i + 1]] for i in range(len(block_lengths))]
    boot = np.zeros(n_boot)
    for i in range(n_boot):
        idx = rng.randint(0, len(blocks), size=len(blocks))
        cat = np.concatenate([blocks[j] for j in idx])
        boot[i] = cat.mean()
    return float(np.nanmean(values)), float(np.nanquantile(boot, alpha / 2)), float(np.nanquantile(boot, 1 - alpha / 2))


def auroc_pooled(correct_mse, wrong_mse):
    """Verbatim logic of eval_diffusion_diagnostic.auroc_pooled: pooled Mann-Whitney on -MSE, average-rank ties."""
    c = -np.asarray(correct_mse).ravel(); w = -np.asarray(wrong_mse).ravel()
    c = c[np.isfinite(c)]; w = w[np.isfinite(w)]
    if c.size == 0 or w.size == 0:
        return float("nan")
    n1, n2 = c.size, w.size
    s = np.concatenate([c, w]); order = np.argsort(s, kind="stable"); ss = s[order]
    ranks_sorted = np.empty(len(s)); i = 0
    while i < len(ss):
        j = i
        while j + 1 < len(ss) and ss[j + 1] == ss[i]:
            j += 1
        ranks_sorted[i:j + 1] = (i + j) / 2.0 + 1.0; i = j + 1
    ranks = np.empty_like(ranks_sorted); ranks[order] = ranks_sorted
    U = ranks[:n1].sum() - n1 * (n1 + 1) / 2
    return float(U / (n1 * n2))

# ---- Phase G LOCKED contract (diffusion_diagnostic_dataset.py:47-55) ----
W, H = 5320, 4600
CROP_Y0, CROP_Y1, CROP_X0, CROP_X1 = 0, 1704, 155, 2433
TH, TW = 768, 1024
TAKE = Path("[machine path redacted]")
FORBIDDEN = "live_120s_verification_001"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_C(row: int) -> torch.Tensor:
    raw = np.frombuffer((TAKE / "Recordings" / f"frame_{row:06d}.raw").read_bytes(), dtype=np.uint8)
    assert raw.size == W * H
    r2 = raw.reshape(H, W)
    cfa = np.stack([r2[0::2, 0::2], r2[0::2, 1::2], r2[1::2, 0::2], r2[1::2, 1::2]], 0)  # R,G1,G2,B
    t = torch.from_numpy(cfa.astype(np.float32) / 255.0)
    t = t[:, CROP_Y0:CROP_Y1, CROP_X0:CROP_X1]
    return F.interpolate(t.unsqueeze(0), size=(TH, TW), mode="area").squeeze(0)


def load_E(row: int) -> torch.Tensor:
    im = Image.open(TAKE / "derived" / "Emissions" / f"tile_{row:06d}.png").convert("RGB")
    assert im.size == (1920, 1080)
    t = torch.from_numpy(np.asarray(im).astype(np.float32) / 255.0).permute(2, 0, 1).contiguous()
    return F.interpolate(t.unsqueeze(0), size=(TH, TW), mode="area").squeeze(0)


def load_model(ckpt: Path, device):
    ck = torch.load(ckpt, map_location="cpu", weights_only=False)
    state = ck["model"] if "model" in ck else ck
    args = ck.get("args", {})
    base_ch = args.get("base_ch", 96); mults = tuple(args.get("mults", (1, 2, 4, 4)))
    attn_at = args.get("attn_at")
    attn_at = tuple(bool(x) for x in attn_at) if attn_at is not None else tuple(i == len(mults) - 1 for i in range(len(mults)))
    m = DiffusionDiagnosticUNet(in_ch=4, base_ch=base_ch, channel_mults=mults, attn_at=attn_at,
                                cond_drop_prob=0.0, hint_in_ch=11)
    missing, unexp = m.load_state_dict(state, strict=True), None
    n = sum(p.numel() for p in m.parameters())
    return m.to(device).eval(), n, {"base_ch": base_ch, "mults": mults, "attn_at": attn_at}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="model_final.pt")
    ap.add_argument("--stride", type=int, default=6)
    ap.add_argument("--inset", type=int, default=30)
    ap.add_argument("--K", type=int, default=2)
    ap.add_argument("--timesteps", type=int, nargs="+", default=[150, 300, 500])
    ap.add_argument("--offsets", type=int, nargs="+", default=[-2, 2, -15, 15, 30])
    ap.add_argument("--block", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20260823)
    ap.add_argument("--out", default="zeroshot_result.json")
    a = ap.parse_args()
    assert FORBIDDEN not in str(TAKE)
    dev = torch.device("cuda")
    n_rows = len(list((TAKE / "Recordings").glob("frame_*.raw")))
    assert n_rows == 712, n_rows
    rows = list(range(a.inset, n_rows - a.inset, a.stride))
    model, n_params, cfg = load_model(Path(a.ckpt), dev)
    dc = build_diffusion_constants(1000, dev, torch.float32)
    T = len(a.timesteps)
    conds = ["correct"] + [f"wrong_{o:+d}" for o in a.offsets] + ["uncond"]
    per_row = []
    t0 = time.time()
    for i, r in enumerate(rows):
        C = load_C(r).to(dev)
        torch.manual_seed(a.seed + r)
        noise = torch.randn(T, a.K, 4, TH, TW, device=dev)  # shared across conditions
        Es = {"correct": load_E(r).to(dev)}
        for o in a.offsets:
            Es[f"wrong_{o:+d}"] = load_E(r + o).to(dev)
        scores = {c: np.zeros((T, a.K)) for c in conds}
        with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
            for ti, t in enumerate(a.timesteps):
                tt = torch.full((1,), t, device=dev, dtype=torch.long)
                for k in range(a.K):
                    Ct = q_sample(C.unsqueeze(0), tt, dc, noise[ti, k].unsqueeze(0)).to(torch.bfloat16)
                    for c in conds:
                        if c == "uncond":
                            eps = model(Ct, Es["correct"].unsqueeze(0), tt, force_uncond=True)
                        else:
                            eps = model(Ct, Es[c].unsqueeze(0), tt)
                        scores[c][ti, k] = (eps.float() - noise[ti, k].unsqueeze(0)).pow(2).mean().item()
        per_row.append({"row": r, "block": r // a.block, **{c: scores[c].tolist() for c in conds}})
        if i % 10 == 0:
            el = time.time() - t0
            print(f"[{i+1}/{len(rows)}] row {r} correct={scores['correct'].mean():.6f} "
                  f"wrong+2={scores['wrong_+2'].mean():.6f} uncond={scores['uncond'].mean():.6f} "
                  f"{el:.0f}s", flush=True)

    # ---- summary ----
    def arr(c, ti=None):
        if ti is None:
            return np.array([np.mean(p[c]) for p in per_row])
        return np.array([np.mean(p[c][ti]) for p in per_row])
    blocks = sorted(set(p["block"] for p in per_row))
    block_lengths = [sum(1 for p in per_row if p["block"] == b) for b in blocks]
    summary = {"n_rows": len(rows), "rows_first_last": [rows[0], rows[-1]], "stride": a.stride,
               "timesteps": a.timesteps, "K": a.K, "offsets": a.offsets, "blocks": block_lengths,
               "conditions": {}, "per_timestep": {}, "auroc": {}}
    correct = arr("correct")
    wrongs = np.stack([arr(f"wrong_{o:+d}") for o in a.offsets], 1)
    for c in conds:
        summary["conditions"][c] = float(arr(c).mean())
    d = wrongs.mean(1) - correct
    m, lo, hi = block_bootstrap_ci(d, block_lengths)
    summary["delta_wrong_mean"] = {"mean": m, "ci95": [lo, hi]}
    du = arr("uncond") - correct
    m, lo, hi = block_bootstrap_ci(du, block_lengths)
    summary["delta_uncond_mean"] = {"mean": m, "ci95": [lo, hi]}
    summary["auroc"]["correct_vs_wrong_avg"] = auroc_pooled(correct, wrongs.mean(1))
    for j, o in enumerate(a.offsets):
        summary["auroc"][f"correct_vs_wrong_{o:+d}"] = auroc_pooled(correct, wrongs[:, j])
    summary["auroc"]["correct_vs_uncond"] = auroc_pooled(correct, arr("uncond"))
    summary["paired_frac_correct_lt_wrong_avg"] = float((correct < wrongs.mean(1)).mean())
    for ti, t in enumerate(a.timesteps):
        c_t = arr("correct", ti); w_t = np.stack([arr(f"wrong_{o:+d}", ti) for o in a.offsets], 1).mean(1)
        summary["per_timestep"][str(t)] = {"correct": float(c_t.mean()), "wrong": float(w_t.mean()),
                                           "delta": float((w_t - c_t).mean()),
                                           "auroc": auroc_pooled(c_t, w_t)}
    summary["elapsed_s"] = time.time() - t0
    summary["model"] = {"ckpt_sha256": sha256(Path(a.ckpt)), "n_params": n_params, **{k: list(v) if isinstance(v, tuple) else v for k, v in cfg.items()}}
    summary["take"] = str(TAKE)
    summary["script_sha256"] = sha256(Path(__file__))
    summary["torch"] = torch.__version__
    summary["device"] = torch.cuda.get_device_name(0)
    json.dump({"summary": summary, "per_row": per_row}, open(a.out, "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
