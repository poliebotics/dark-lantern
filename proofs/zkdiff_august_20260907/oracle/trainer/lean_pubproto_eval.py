#!/usr/bin/env python3
"""ARM-C published-protocol evaluator (no-crop line).

Statistics are the published protocol verbatim (same five wrong offsets, pooled
Mann-Whitney AUROC with average-rank ties, block bootstrap CI over contiguous eval
blocks sub-blocked to 40, paired fraction). PREPROCESSING is ARM-C's own: the full
sensor frame area-resized to the checkpoint's recorded out_size, emission resized not
cropped. It deliberately does NOT reuse the ARM-A evaluator, which applies
CROP=(0,1704,155,2433) and would silently mis-protocol these models.
"""
import argparse, hashlib, importlib.util, json, os, sys
import numpy as np
import torch
sys.dont_write_bytecode = True

OFFSETS = [-2, 2, -15, 15, 30]
T_VAL, EVAL_SEED, SUB_TARGET = 150, 20260823, 40

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 22), b""): h.update(c)
    return h.hexdigest()

def auroc_pooled(correct, wrong):
    """P(wrong_err > correct_err); average-rank ties, as the published protocol."""
    x = np.concatenate([wrong, correct])
    y = np.concatenate([np.ones(wrong.size), np.zeros(correct.size)])
    o = np.argsort(x, kind="mergesort"); r = np.empty(x.size); xs = x[o]; i = 0
    while i < xs.size:
        j = i
        while j + 1 < xs.size and xs[j + 1] == xs[i]: j += 1
        r[o[i:j + 1]] = (i + j + 2) / 2.0; i = j + 1
    return float((r[y == 1].sum() - wrong.size * (wrong.size + 1) / 2) / (wrong.size * correct.size))

def sub_block(bl, target):
    out = []
    for L in bl:
        n = max(1, round(L / target)); base, rem = divmod(L, n)
        out += [base + (1 if i < rem else 0) for i in range(n)]
    return out

def block_bootstrap_ci(values, block_lengths, n_boot=1000, alpha=0.05, seed=EVAL_SEED):
    rng = np.random.RandomState(seed); b = [0]
    for L in block_lengths: b.append(b[-1] + L)
    blocks = [values[b[i]:b[i + 1]] for i in range(len(block_lengths))]
    boot = np.zeros(n_boot)
    for i in range(n_boot):
        idx = rng.randint(0, len(blocks), size=len(blocks))
        boot[i] = np.concatenate([blocks[j] for j in idx]).mean()
    return float(np.nanmean(values)), float(np.nanquantile(boot, alpha / 2)), float(np.nanquantile(boot, 1 - alpha / 2))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--trainer", default="train_lean.py", help="the lean trainer module: its loaders, session table and both model classes are bound")
    ap.add_argument("--cache-dir", default="", help="pre-downsampled cache root (same tensors as the raw loaders)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--save-raw", required=True)
    ap.add_argument("--stride", type=int, default=1)
    a = ap.parse_args()

    ck = torch.load(a.ckpt, map_location="cpu", weights_only=False)
    args = ck.get("args", {})
    crop_id = str(args.get("crop_id", ""))
    if not crop_id.startswith("UNCROPPED"):
        raise SystemExit(f"REFUSING: checkpoint crop_id {crop_id!r} is not an uncropped ARM-C run")
    out_size = str(args.get("out_size", "768,896"))
    TH, TW = (int(v) for v in out_size.split(","))

    # import the ARM-C trainer and bind ITS loaders / session table
    spec = importlib.util.spec_from_file_location("armc", a.trainer)
    M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
    M.TH, M.TW = TH, TW                    # the trainer sets these in main(); bind from the ckpt
    M.CACHE_DIR = a.cache_dir or None
    import pathlib as _pl
    _root = os.environ.get("ARMC_DATA_ROOT", "")
    if _root:
        for _sid, _s in M.SESSIONS.items():
            _s["dir"] = _pl.Path(_root) / _pl.Path(_s["dir"]).name
    M.resolve_raw_layout()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    dc = M.build_diffusion_constants(1000, dev, torch.float32)   # exactly as the trainer calls it

    # architecture from the WEIGHTS (args records None for these runs), never assumed
    base_ch = int(ck["model"]["stem.weight"].shape[0]) if "stem.weight" in ck["model"] else int(ck["model"]["in_conv.weight"].shape[0])
    _m = args.get("mults") or (1, 2, 4, 4)
    mults = tuple(int(v) for v in _m.split(",")) if isinstance(_m, str) and _m else tuple(_m) if not isinstance(_m, str) else (1, 2, 4, 4)
    arch = str(args.get("arch", "armc"))
    if "stem.weight" in ck["model"]:
        hint_in = int(ck["model"]["stem.weight"].shape[1]) - 4
    else:
        hk = "hint_encoder.s0.0.weight" if "hint_encoder.s0.0.weight" in ck["model"] else "hint_encoder.stages.0.0.weight"
        hint_in = int(ck["model"][hk].shape[1])   # hint width, from the weights
    if arch == "zk2":
        model = M.LeanDenoiser(in_ch=4, base_ch=base_ch, channel_mults=mults, cond_drop_prob=0.2, hint_in_ch=hint_in, qat=bool(args.get("qat", False))).to(dev)
    elif arch == "zk":
        model = M.ZkUNet(in_ch=4, base_ch=base_ch, channel_mults=mults, cond_drop_prob=0.2, hint_in_ch=hint_in).to(dev)
    else:
        model = M.ArmCUNet(in_ch=4, base_ch=base_ch, channel_mults=mults,
                                          attn_at=tuple(i == len(mults) - 1 for i in range(len(mults))),
                                          cond_drop_prob=0.2, hint_in_ch=hint_in).to(dev)
    model.load_state_dict(ck["model"], strict=True); model.eval()

    res = {"checkpoint": a.ckpt, "checkpoint_sha256": sha(a.ckpt), "checkpoint_step": ck.get("step"),
           "crop_id": crop_id, "out_size": out_size, "arch": {"kind": arch, "base_ch": base_ch, "mults": list(mults), "hint_in_ch": hint_in, "params": int(sum(p.numel() for p in model.parameters()))},
           "preprocessing": "ARM-C: NO crop; full sensor frame area-resized to out_size; emission resized not cropped",
           "protocol": {"t": T_VAL, "offsets": OFFSETS, "stride": a.stride, "seed": EVAL_SEED,
                        "sub_blocks": SUB_TARGET, "noise_rule": "one generator per session, manual_seed(EVAL_SEED), one draw per row in row order", "statistics": "published protocol statistics; one-stream scoring RNG seeded once per session with the protocol seed"},
           "sessions": {}}

    for sid in ("d2", "v10"):
        if sid not in M.SESSIONS: continue
        S = M.SESSIONS[sid]; total = S["rows_total"]
        blocks, rows = [], []
        for (lo, hi) in S["eval_blocks"]:
            rr = list(range(lo, hi, a.stride)); blocks.append(len(rr)); rows += rr
        arrs = {k: np.full(len(rows), np.nan) for k in ["correct"] + [f"wrong_{o:+d}" for o in OFFSETS]}
        # FROZEN PROTOCOL noise rule: ONE generator per session, seeded once with the
        # protocol seed, one draw per row in row order, shared across all conditions for
        # that row. (The trainer's quick_eval uses per-row 999+r; that is NOT this.)
        gen = torch.Generator(device=dev); gen.manual_seed(EVAL_SEED)
        with torch.no_grad():
            for i, r in enumerate(rows):
                C = M.load_C(sid, r).to(dev, torch.bfloat16)
                noise = torch.randn(1, 4, TH, TW, device=dev, generator=gen)
                tt = torch.full((1,), T_VAL, device=dev, dtype=torch.long)
                Ct = M.q_sample(C.float().unsqueeze(0), tt, dc, noise).to(torch.bfloat16)
                with torch.autocast(dev, dtype=torch.bfloat16, enabled=True):
                    e = model(Ct, M.load_E(sid, r).to(dev, torch.bfloat16).unsqueeze(0), tt)
                arrs["correct"][i] = float((e.float() - noise).pow(2).mean())
                for o in OFFSETS:
                    rw = r + o
                    if rw < 0 or rw >= total: continue      # boundary: absent, never imputed
                    with torch.autocast(dev, dtype=torch.bfloat16, enabled=True):
                        ew = model(Ct, M.load_E(sid, rw).to(dev, torch.bfloat16).unsqueeze(0), tt)
                    arrs[f"wrong_{o:+d}"][i] = float((ew.float() - noise).pow(2).mean())
                if i % 100 == 0: print(f"  {sid} {i}/{len(rows)}", flush=True)
        c = arrs["correct"]; W = np.stack([arrs[f"wrong_{o:+d}"] for o in OFFSETS], 1)
        wmean = np.nanmean(W, 1)
        eff = sub_block(blocks, SUB_TARGET)
        m, lo_, hi_ = block_bootstrap_ci(wmean - c, eff)
        fin = np.isfinite(c) & np.isfinite(wmean)
        res["sessions"][sid] = {
            "n_rows": len(rows), "contiguous_eval_blocks": blocks, "blocks_used": eff,
            "conditions": {k: float(np.nanmean(v)) for k, v in arrs.items()},
            "delta_wrong_mean": {"mean": m, "ci95": [lo_, hi_]},
            "paired_fraction_correct_lower": float(np.nanmean(c[fin] < wmean[fin])),
            "auroc": {"correct_vs_wrong_avg": auroc_pooled(c[fin], wmean[fin]),
                      **{f"correct_vs_wrong_{o:+d}": auroc_pooled(
                          c[np.isfinite(arrs[f'wrong_{o:+d}'])],
                          arrs[f"wrong_{o:+d}"][np.isfinite(arrs[f'wrong_{o:+d}'])]) for o in OFFSETS}},
            "raw_scores": f"{a.save_raw}_{sid}.npz"}
        np.savez(f"{a.save_raw}_{sid}.npz", rows=np.array(rows, dtype=np.int64),
                 block_lengths=np.array(blocks, dtype=np.int64), **arrs)
    with open(a.out, "w") as f: json.dump(res, f, indent=1)
    print(json.dumps({s: {"auroc": d["auroc"]["correct_vs_wrong_avg"],
                          "delta": d["delta_wrong_mean"]["mean"],
                          "paired": d["paired_fraction_correct_lower"], "n": d["n_rows"]}
                      for s, d in res["sessions"].items()}))

if __name__ == "__main__":
    main()
