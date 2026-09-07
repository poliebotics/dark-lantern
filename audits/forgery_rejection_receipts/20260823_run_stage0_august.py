#!/usr/bin/env python3
"""Stage-0 forgery rejection on the August 2026 300 s training take (proof 5, empirical half).

For each sampled development row r: C_fake = F-A-v1(C_{r-2}, E_{r-2}, E_r) at native resolution
(published Stage-0 protocol, SOURCE_LAG = 2), reduced to the Phase G input. The published Phase G
verifier (safe-loaded, bf16 path, t=150, K=1, one shared noise tensor per row) scores:
  real_correct  (C_r,    E_r)        real_shuffled (C_r,    E_far)
  fake_correct  (C_fake, E_r)        fake_shuffled (C_fake, E_far)
  fake_source   (C_fake, E_{r-2})    fake_uncond   (C_fake, zero E)
E_far is a deterministic far row (r + 356 mod 712, always >= 60 rows away). Development take only.
"""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, sys, time
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

VERIFIER_SRC = Path("<machine path redacted>")
sys.path.insert(0, str(VERIFIER_SRC))
from phase_g.diffusion_diagnostic_model import DiffusionDiagnosticUNet, build_diffusion_constants, q_sample  # noqa: E402
from phase_f.editor_controlnet import EditorControlNet  # noqa: E402

TAKE = Path("[machine path redacted]")
FORBIDDEN = "live_120s_verification_001"
W, H = 5320, 4600
CROP_Y0, CROP_Y1, CROP_X0, CROP_X1 = 0, 1704, 155, 2433
TH, TW = 768, 1024
EXPECTED_VERIFIER = "b9d93050bfeb1a5cdbf620c38210f3ab6c6fd7af1f61eb45cc17ac269341f055"
EXPECTED_FORGER = "2bf156d07b1ddf72ec53dab500cc0df2344596edd40890f904a60901217ad92e"
SOURCE_LAG = 2
FAR = 356


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def die(msg):
    raise SystemExit(f"FAIL: {msg}")


def load_C_native(row):
    raw = np.frombuffer((TAKE / "Recordings" / f"frame_{row:06d}.raw").read_bytes(), dtype=np.uint8)
    if raw.size != W * H:
        die("raw size")
    r2 = raw.reshape(H, W)
    cfa = np.stack([r2[0::2, 0::2], r2[0::2, 1::2], r2[1::2, 0::2], r2[1::2, 1::2]], 0)
    return torch.from_numpy(cfa.astype(np.float32) / 255.0)  # (4, 2300, 2660)


def load_E_native(row):
    im = Image.open(TAKE / "derived" / "Emissions" / f"tile_{row:06d}.png").convert("RGB")
    if im.size != (1920, 1080):
        die("emission size")
    return torch.from_numpy(np.asarray(im).astype(np.float32) / 255.0).permute(2, 0, 1).contiguous()


def to_phase_g_C(C_native):
    return F.interpolate(C_native[:, CROP_Y0:CROP_Y1, CROP_X0:CROP_X1].unsqueeze(0), size=(TH, TW), mode="area").squeeze(0)


def to_phase_g_E(E_native):
    return F.interpolate(E_native.unsqueeze(0), size=(TH, TW), mode="area").squeeze(0)


def load_verifier(path, dev):
    if sha(path) != EXPECTED_VERIFIER:
        die("verifier hash")
    ck = torch.load(path, map_location="cpu", weights_only=True)
    args = ck["args"]; mults = tuple(args.get("mults", (1, 2, 4, 4)))
    attn = tuple(i == len(mults) - 1 for i in range(len(mults)))
    m = DiffusionDiagnosticUNet(in_ch=4, base_ch=args.get("base_ch", 96), channel_mults=mults, attn_at=attn, cond_drop_prob=0.0, hint_in_ch=11)
    m.load_state_dict(ck["model"], strict=True)
    return m.to(dev, dtype=torch.bfloat16).eval()


def load_forger(path, dev):
    if sha(path) != EXPECTED_FORGER:
        die("forger hash")
    with torch.serialization.safe_globals([pathlib.PosixPath]):
        ck = torch.load(path, map_location="cpu", weights_only=True)
    args = ck.get("args", {})
    m = EditorControlNet(init_mode="scratch", hint_use_source=(args.get("hint_mode", "v1_5_treatment") == "v1_5_treatment"))
    m.load_state_dict(ck["editor"], strict=True)
    m = m.to(dev, dtype=torch.bfloat16).eval()
    for p in m.parameters():
        p.requires_grad = False
    return m, int(ck.get("step", -1)), sum(p.numel() for p in m.parameters())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verifier", default="../phase_g_zeroshot_20260823/model_final.pt")
    ap.add_argument("--forger", default="f_a_v1_step_00100000.pt")
    ap.add_argument("--stride", type=int, default=8)
    ap.add_argument("--inset", type=int, default=32)
    ap.add_argument("--t", type=int, default=150)
    ap.add_argument("--seed", type=int, default=20260823)
    ap.add_argument("--out", default="stage0_august.json")
    ap.add_argument("--save-fakes", action="store_true")
    a = ap.parse_args()
    if sys.flags.optimize != 0 or FORBIDDEN in str(TAKE):
        die("runtime")
    n_rows = len(list((TAKE / "Recordings").glob("frame_*.raw")))
    if n_rows != 712:
        die("row count")
    dev = torch.device("cuda")
    ver = load_verifier(Path(a.verifier), dev)
    forger, fstep, fparams = load_forger(Path(a.forger), dev)
    dc = build_diffusion_constants(1000, dev, torch.float32)
    rows = list(range(a.inset, n_rows - a.inset, a.stride))
    conds = ["real_correct", "real_shuffled", "fake_correct", "fake_shuffled", "fake_source", "fake_uncond"]
    out_rows = []
    t0 = time.time()
    fake_stats = []
    for i, r in enumerate(rows):
        far = (r + FAR) % n_rows
        C_real_n = load_C_native(r)
        C_src_n = load_C_native(r - SOURCE_LAG)
        E_src_n = load_E_native(r - SOURCE_LAG)
        E_tgt_n = load_E_native(r)
        with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
            C_fake_n = forger(C_src_n.to(dev, torch.bfloat16).unsqueeze(0), E_src_n.to(dev, torch.bfloat16).unsqueeze(0),
                              E_tgt_n.to(dev, torch.bfloat16).unsqueeze(0)).squeeze(0).float().cpu()
        fake_stats.append({"row": r, "fake_minus_source_mae": float((C_fake_n - C_src_n).abs().mean()),
                           "fake_minus_real_mae": float((C_fake_n - C_real_n).abs().mean()),
                           "real_minus_source_mae": float((C_real_n - C_src_n).abs().mean())})
        if a.save_fakes:
            np.save(f"fake_{r:06d}.npy", (C_fake_n.clamp(0, 1) * 255).round().to(torch.uint8).numpy())
        C_real = to_phase_g_C(C_real_n).to(dev, torch.bfloat16)
        C_fake = to_phase_g_C(C_fake_n).to(dev, torch.bfloat16)
        E_t = to_phase_g_E(E_tgt_n).to(dev, torch.bfloat16)
        E_s = to_phase_g_E(E_src_n).to(dev, torch.bfloat16)
        E_far = to_phase_g_E(load_E_native(far)).to(dev, torch.bfloat16)
        torch.manual_seed(a.seed + r)
        noise = torch.randn(1, 4, TH, TW, device=dev)
        tt = torch.full((1,), a.t, device=dev, dtype=torch.long)
        sc = {}
        with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
            for name, C, E, unc in [("real_correct", C_real, E_t, False), ("real_shuffled", C_real, E_far, False),
                                    ("fake_correct", C_fake, E_t, False), ("fake_shuffled", C_fake, E_far, False),
                                    ("fake_source", C_fake, E_s, False), ("fake_uncond", C_fake, E_t, True)]:
                Ct = q_sample(C.float().unsqueeze(0), tt, dc, noise).to(torch.bfloat16)
                eps = ver(Ct, E.unsqueeze(0), tt, force_uncond=unc)
                sc[name] = float((eps.float() - noise).pow(2).mean())
        out_rows.append({"row": r, "source_row": r - SOURCE_LAG, "far_row": far, **sc})
        if i % 10 == 0:
            print(f"[{i+1}/{len(rows)}] row {r} real_c={sc['real_correct']:.6f} fake_c={sc['fake_correct']:.6f} fake_sh={sc['fake_shuffled']:.6f} {time.time()-t0:.0f}s", flush=True)

    def arr(c):
        return np.array([o[c] for o in out_rows])

    def auroc(pos, neg):  # pooled Mann-Whitney on -MSE, average ranks; positive = first arg
        c = -pos; w = -neg; n1, n2 = c.size, w.size
        s = np.concatenate([c, w]); order = np.argsort(s, kind="stable"); ss = s[order]
        rs = np.empty(len(s)); i = 0
        while i < len(ss):
            j = i
            while j + 1 < len(ss) and ss[j + 1] == ss[i]:
                j += 1
            rs[i:j + 1] = (i + j) / 2.0 + 1.0; i = j + 1
        ranks = np.empty_like(rs); ranks[order] = rs
        return float((ranks[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n2))

    summary = {
        "label": "Stage-0 forgery rejection on the August 300 s take, F-A v1 step 100k, Phase G verifier zero-shot, t=150, K=1",
        "n_rows": len(rows), "rows_first_last": [rows[0], rows[-1]], "stride": a.stride, "inset": a.inset, "source_lag": SOURCE_LAG, "far": FAR,
        "means": {c: float(arr(c).mean()) for c in conds},
        "auroc": {"real_correct_vs_fake_correct": auroc(arr("real_correct"), arr("fake_correct")),
                  "real_correct_vs_real_shuffled": auroc(arr("real_correct"), arr("real_shuffled")),
                  "fake_correct_vs_fake_shuffled": auroc(arr("fake_correct"), arr("fake_shuffled")),
                  "fake_correct_vs_fake_source": auroc(arr("fake_correct"), arr("fake_source")),
                  "fake_correct_vs_fake_uncond": auroc(arr("fake_correct"), arr("fake_uncond"))},
        "paired_frac_real_lt_fake": float((arr("real_correct") < arr("fake_correct")).mean()),
        "fake_pixel_stats_mean": {k: float(np.mean([f[k] for f in fake_stats])) for k in fake_stats[0] if k != "row"},
        "verifier_sha256": EXPECTED_VERIFIER, "forger_sha256": EXPECTED_FORGER, "forger_step": fstep, "forger_params": fparams,
        "checkpoint_load_mode": "weights_only=True (forger: pathlib.PosixPath allowlisted), strict state_dict, bf16",
        "take": str(TAKE), "seed": a.seed, "t": a.t, "script_sha256": sha(Path(__file__)), "elapsed_s": time.time() - t0,
        "torch": torch.__version__, "device": torch.cuda.get_device_name(0),
    }
    json.dump({"summary": summary, "per_row": out_rows, "fake_stats": fake_stats}, open(a.out, "w"), indent=1, allow_nan=False)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
