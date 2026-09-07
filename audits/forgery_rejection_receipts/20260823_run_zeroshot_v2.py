#!/usr/bin/env python3
"""Phase G verifier, zero-shot, on the August 2026 ZeeBeam 300 s training take. v2: exhaustive rows, boundary offsets absent rather than imputed, per-arm denominators reported.

Reads ONLY stage/live_300s_training_001 (712 development rows). Never touches the
120 s verification take. Uses the published model_final.pt and the exact Phase G
input contract (pack, crop, /255, area resize, 11-ch hint, cosine schedule, seeded
shared noise, bf16 forward, float32 MSE). The v2 defaults are the agreed exhaustive
712-row diagnostic at t=150 and K=1. Boundary-crossing wrong-emission offsets are
absent rather than imputed; the output reports an explicit denominator for every
arm, pooled tie-aware AUROC, and block bootstrap over contiguous blocks.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, stat, sys, time
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

VERIFIER_SRC = Path("<machine path redacted>")
MODEL_SOURCE = VERIFIER_SRC / "phase_g/diffusion_diagnostic_model.py"
EXPECTED_MODEL_SOURCE_SHA256 = "f1241c1e4b7d042397d314207a45becd24066d9ed672ec759fbc14fd9e0c3beb"
EXPECTED_CHECKPOINT_SHA256 = "b9d93050bfeb1a5cdbf620c38210f3ab6c6fd7af1f61eb45cc17ac269341f055"
EXPECTED_CHECKPOINT_BYTES = 477_531_127
PUBLISHED_CHECKPOINT_CID = "QmPthdv3CvW2dyRRYJ7Aqgvwc5qN5D2ujLRVr8e1wWMoAY"
EXPECTED_EXECUTION = {
    "stride": 1,
    "inset": 0,
    "K": 1,
    "timesteps": [150],
    "offsets": [-2, 2, -15, 15, 30],
    "block": 100,
    "seed": 20260823,
}
EXPECTED_ARM_DENOMINATORS = {
    "correct": 712,
    "wrong_-2": 710,
    "wrong_+2": 710,
    "wrong_-15": 697,
    "wrong_+15": 697,
    "wrong_+30": 682,
    "uncond": 712,
}
if not MODEL_SOURCE.is_file() or MODEL_SOURCE.is_symlink():
    raise RuntimeError("pinned Phase G model source must be a regular non-symlink file")
MODEL_SOURCE_SHA256 = hashlib.sha256(MODEL_SOURCE.read_bytes()).hexdigest()
if MODEL_SOURCE_SHA256 != EXPECTED_MODEL_SOURCE_SHA256:
    raise RuntimeError(
        f"Phase G model source hash mismatch: {MODEL_SOURCE_SHA256} != "
        f"{EXPECTED_MODEL_SOURCE_SHA256}"
    )
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
    # The checkpoint is externally sourced data.  Fail closed on tensor-only
    # deserialisation; never fall back to unrestricted pickle execution.
    fd = os.open(ckpt, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as checkpoint_file:
        checkpoint_stat = os.fstat(checkpoint_file.fileno())
        if not stat.S_ISREG(checkpoint_stat.st_mode):
            raise RuntimeError("checkpoint must be a regular non-symlink file")
        if checkpoint_stat.st_size != EXPECTED_CHECKPOINT_BYTES:
            raise RuntimeError(
                f"checkpoint size mismatch: {checkpoint_stat.st_size} != "
                f"{EXPECTED_CHECKPOINT_BYTES}"
            )
        checkpoint_hash = hashlib.sha256()
        for chunk in iter(lambda: checkpoint_file.read(1 << 20), b""):
            checkpoint_hash.update(chunk)
        checkpoint_sha256 = checkpoint_hash.hexdigest()
        if checkpoint_sha256 != EXPECTED_CHECKPOINT_SHA256:
            raise RuntimeError(
                f"checkpoint hash mismatch: {checkpoint_sha256} != "
                f"{EXPECTED_CHECKPOINT_SHA256}"
            )
        checkpoint_file.seek(0)
        ck = torch.load(checkpoint_file, map_location="cpu", weights_only=True)
    if not isinstance(ck, dict) or "model" not in ck:
        raise RuntimeError("checkpoint must contain a model state dictionary")
    state = ck["model"] if "model" in ck else ck
    args = ck.get("args", {})
    if not isinstance(args, dict):
        raise RuntimeError("checkpoint args must be a plain dictionary")
    base_ch = args.get("base_ch", 96); mults = tuple(args.get("mults", (1, 2, 4, 4)))
    attn_at = args.get("attn_at")
    attn_at = tuple(bool(x) for x in attn_at) if attn_at is not None else tuple(i == len(mults) - 1 for i in range(len(mults)))
    m = DiffusionDiagnosticUNet(in_ch=4, base_ch=base_ch, channel_mults=mults, attn_at=attn_at,
                                cond_drop_prob=0.0, hint_in_ch=11)
    missing, unexp = m.load_state_dict(state, strict=True), None
    n = sum(p.numel() for p in m.parameters())
    return m.to(device, dtype=torch.bfloat16).eval(), n, {
        "base_ch": base_ch,
        "mults": mults,
        "attn_at": attn_at,
        "parameter_dtype": "torch.bfloat16",
        "ckpt_sha256": checkpoint_sha256,
        "ckpt_bytes": checkpoint_stat.st_size,
        "published_ipfs_cid_v0": PUBLISHED_CHECKPOINT_CID,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="model_final.pt")
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--inset", type=int, default=0)
    ap.add_argument("--K", type=int, default=1)
    ap.add_argument("--timesteps", type=int, nargs="+", default=[150])
    ap.add_argument("--offsets", type=int, nargs="+", default=[-2, 2, -15, 15, 30])
    ap.add_argument("--block", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20260823)
    ap.add_argument("--out", default="zeroshot_result.json")
    a = ap.parse_args()
    observed_execution = {
        "stride": a.stride,
        "inset": a.inset,
        "K": a.K,
        "timesteps": a.timesteps,
        "offsets": a.offsets,
        "block": a.block,
        "seed": a.seed,
    }
    if observed_execution != EXPECTED_EXECUTION:
        raise RuntimeError(
            f"v2 execution contract mismatch: {observed_execution} != "
            f"{EXPECTED_EXECUTION}"
        )
    assert FORBIDDEN not in str(TAKE)
    dev = torch.device("cuda")
    n_rows = len(list((TAKE / "Recordings").glob("frame_*.raw")))
    assert n_rows == 712, n_rows
    rows = list(range(a.inset, n_rows - a.inset, a.stride)) if a.inset > 0 else list(range(0, n_rows, a.stride))
    if rows != list(range(712)):
        raise RuntimeError("v2 must evaluate every development row exactly once")
    model, n_params, cfg = load_model(Path(a.ckpt), dev)
    dc = build_diffusion_constants(1000, dev, torch.float32)
    T = len(a.timesteps)
    conds = ["correct"] + [f"wrong_{o:+d}" for o in a.offsets] + ["uncond"]
    per_row = []
    t0 = time.time()
    for i, r in enumerate(rows):
        C = load_C(r).to(dev, dtype=torch.bfloat16)
        torch.manual_seed(a.seed + r)
        noise = torch.randn(T, a.K, 4, TH, TW, device=dev)  # shared across conditions
        Es = {"correct": load_E(r).to(dev, dtype=torch.bfloat16)}
        for o in a.offsets:
            if 0 <= r + o < n_rows:
                Es[f"wrong_{o:+d}"] = load_E(r + o).to(dev, dtype=torch.bfloat16)
        scores = {c: np.full((T, a.K), np.nan) for c in conds}
        with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
            for ti, t in enumerate(a.timesteps):
                tt = torch.full((1,), t, device=dev, dtype=torch.long)
                for k in range(a.K):
                    Ct = q_sample(C.float().unsqueeze(0), tt, dc, noise[ti, k].unsqueeze(0)).to(torch.bfloat16)
                    for c in conds:
                        if c not in Es and c != "uncond":
                            continue  # offset leaves the take: arm absent for this row, never imputed
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
            return np.array([np.nanmean(p[c]) if np.isfinite(p[c]).any() else np.nan for p in per_row])
        return np.array([np.nanmean(p[c][ti]) if np.isfinite(p[c][ti]).any() else np.nan for p in per_row])
    blocks = sorted(set(p["block"] for p in per_row))
    block_lengths = [sum(1 for p in per_row if p["block"] == b) for b in blocks]
    summary = {"n_rows": len(rows), "rows_first_last": [rows[0], rows[-1]], "stride": a.stride,
               "timesteps": a.timesteps, "K": a.K, "offsets": a.offsets, "blocks": block_lengths,
               "conditions": {}, "per_timestep": {}, "auroc": {}}
    correct = arr("correct")
    wrongs = np.stack([arr(f"wrong_{o:+d}") for o in a.offsets], 1)
    summary["arm_denominators"] = {c: int(np.isfinite(arr(c)).sum()) for c in conds}
    if summary["arm_denominators"] != EXPECTED_ARM_DENOMINATORS:
        raise RuntimeError(
            f"arm denominator mismatch: {summary['arm_denominators']} != "
            f"{EXPECTED_ARM_DENOMINATORS}"
        )
    for c in conds:
        summary["conditions"][c] = float(np.nanmean(arr(c)))
    d = np.nanmean(wrongs, 1) - correct
    m, lo, hi = block_bootstrap_ci(d, block_lengths)
    summary["delta_wrong_mean"] = {"mean": m, "ci95": [lo, hi]}
    du = arr("uncond") - correct
    m, lo, hi = block_bootstrap_ci(du, block_lengths)
    summary["delta_uncond_mean"] = {"mean": m, "ci95": [lo, hi]}
    summary["auroc"]["correct_vs_wrong_avg"] = auroc_pooled(correct, np.nanmean(wrongs, 1))
    for j, o in enumerate(a.offsets):
        summary["auroc"][f"correct_vs_wrong_{o:+d}"] = auroc_pooled(correct, wrongs[:, j])
    summary["auroc"]["correct_vs_uncond"] = auroc_pooled(correct, arr("uncond"))
    summary["paired_frac_correct_lt_wrong_avg"] = float(np.nanmean(correct < np.nanmean(wrongs, 1)))
    for ti, t in enumerate(a.timesteps):
        c_t = arr("correct", ti); w_t = np.nanmean(np.stack([arr(f"wrong_{o:+d}", ti) for o in a.offsets], 1), 1)
        summary["per_timestep"][str(t)] = {"correct": float(c_t.mean()), "wrong": float(w_t.mean()),
                                           "delta": float(np.nanmean(w_t - c_t)),
                                           "auroc": auroc_pooled(c_t, w_t)}
    summary["elapsed_s"] = time.time() - t0
    summary["model"] = {
        "checkpoint_load_mode": "torch_weights_only_true_fail_closed",
        "model_source_path": str(MODEL_SOURCE),
        "model_source_sha256": MODEL_SOURCE_SHA256,
        "n_params": n_params,
        **{k: list(v) if isinstance(v, tuple) else v for k, v in cfg.items()},
    }
    summary["take"] = str(TAKE)
    summary["script_sha256"] = sha256(Path(__file__))
    summary["torch"] = torch.__version__
    summary["device"] = torch.cuda.get_device_name(0)
    summary["execution_contract"] = observed_execution
    summary["command_argv"] = sys.argv
    json.dump({"summary": summary, "per_row": per_row}, open(a.out, "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
