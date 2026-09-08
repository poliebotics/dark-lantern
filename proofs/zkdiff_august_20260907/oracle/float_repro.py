#!/usr/bin/env python3
"""G1 positive control: rebuild the ARM-C lean denoiser on the CPU and reproduce the
frozen-protocol per-row scores for the 37 evaluation rows (and, with --august, the
held-out August rows 600-711 under the G1 noise convention).

Float variants computed for every score:
  fp32      : the model run in plain float32 on the protocol inputs (C and E rounded to
              bf16 as the evaluator does, C_t formed in fp32 then rounded to bf16).
  bf16em    : the CUDA bf16-autocast rounding points applied explicitly (conv/linear/bmm
              outputs and residual adds rounded to bf16, GroupNorm and softmax in fp32),
              with the up-path bilinear interpolation kept in bf16 (variant 1).
  bf16em_v2 : as bf16em but with upsample_bilinear2d promoted to fp32, as the CUDA autocast
              fp32 list does (PyTorch autocast_mode.cpp, upsample_* entries); the following
              concat is then fp32 by type promotion.  Astra r3 item 8: which of the two the
              A100 environment executed is decided empirically in positive_control.py.
Output: $G1_OUT/float_repro.json.
"""
from __future__ import annotations
import argparse, hashlib, json, math, time
import numpy as np
import torch
import torch.nn.functional as F
from common import (CKPT, OFFSETS, OUT, REF_JSON, SESSIONS, T_VAL, TH, TW, august_offsets, august_rows, build_model, env_summary,
                    eval_rows, load_C_bf16, load_E_bf16, make_Ct, philox_self_test, protocol_noise,
                    protocol_row_index, quick_eval_noise, randn_cuda_emul, read_trainlog_eval, row_available, score)

torch.set_num_threads(16)


# ---------------------------------------------------------------- CUDA-autocast emulation

def bf(x):
    return x.to(torch.bfloat16)


def conv_ac(m, x):
    """autocast conv2d: operands rounded to bf16, fp32 accumulation, output rounded to bf16."""
    y = F.conv2d(bf(x).float(), bf(m.weight).float(), None if m.bias is None else bf(m.bias).float(),
                 m.stride, m.padding)
    return bf(y)


def linear_ac(m, x):
    return bf(F.linear(bf(x).float(), bf(m.weight).float(), None if m.bias is None else bf(m.bias).float()))


def gn_ac(m, x):
    """autocast group_norm: input cast to fp32, output fp32 (CUDA autocast fp32 list)."""
    return F.group_norm(x.float(), m.num_groups, m.weight, m.bias, m.eps)


def linspace_bf16_cuda(start, end, steps):
    """torch.linspace in bf16 as the CUDA kernel computes it: step in bf16, two-sided formula."""
    s = torch.tensor(start, dtype=torch.bfloat16); e = torch.tensor(end, dtype=torch.bfloat16)
    step = (e - s) / (steps - 1)
    halfway = steps // 2
    out = torch.empty(steps, dtype=torch.bfloat16)
    for i in range(steps):
        out[i] = (s + step * i) if i < halfway else (e - step * (steps - i - 1))
    return out


def coord_grid_bf16_cuda(h, w):
    y = linspace_bf16_cuda(-1.0, 1.0, h)
    x = linspace_bf16_cuda(-1.0, 1.0, w)
    yy, xx = torch.meshgrid(y, x, indexing="ij")
    return torch.stack([xx, yy], dim=0)


def resblock_em(blk, x, t_emb):
    h = conv_ac(blk.conv1, F.silu(gn_ac(blk.norm1, x)))
    tp = linear_ac(blk.t_proj, F.silu(t_emb))                 # bf16 (1, C)
    h = bf(h.float() + tp.float().unsqueeze(-1).unsqueeze(-1))
    h = conv_ac(blk.conv2, F.silu(gn_ac(blk.norm2, h)))
    sk = conv_ac(blk.skip, x) if isinstance(blk.skip, torch.nn.Conv2d) else x
    return bf(h.float() + sk.float())


def attn_em(m, x):
    b, c, h, w = x.shape
    qkv = conv_ac(m.qkv, gn_ac(m.norm, x))
    q, k, v = qkv.chunk(3, dim=1)
    hd = c // m.n_heads
    q = q.reshape(b, m.n_heads, hd, h * w); k = k.reshape(b, m.n_heads, hd, h * w); v = v.reshape(b, m.n_heads, hd, h * w)
    a = bf(torch.einsum("bhci,bhcj->bhij", q.float(), k.float()))       # bmm in bf16 -> bf16
    a = bf(a.float() / math.sqrt(hd))
    a = a.float().softmax(dim=-1)                                        # fp32
    out = bf(torch.einsum("bhij,bhcj->bhci", bf(a).float(), v.float()))  # operands cast to bf16
    out = out.reshape(b, c, h, w)
    return bf(x.float() + conv_ac(m.proj, out).float())


@torch.no_grad()
def forward_cuda_bf16_emul(model, Ct_bf16, E_bf16, tt, bilinear_fp32=False):
    """DiffusionDiagnosticUNet.forward (diffusion_diagnostic_model.py:262-312) with the CUDA
    autocast rounding points made explicit.  bilinear_fp32=True promotes the up-path
    F.interpolate to fp32 (autocast fp32 list), which also makes the concat fp32."""
    coord = coord_grid_bf16_cuda(TH, TW).unsqueeze(0)
    hint = torch.cat([E_bf16, coord], dim=1)                     # ArmCUNet._build_hint, train_lean.py:161-165
    feats = []
    h = hint
    for s in (model.hint_encoder.s0, model.hint_encoder.s1, model.hint_encoder.s2, model.hint_encoder.s3):
        h = F.gelu(gn_ac(s[1], conv_ac(s[0], h)))                # conv -> bf16, GN -> fp32, GELU fp32
        feats.append(h)
    half = model.t_emb.dim // 2
    t = tt.to(torch.float32)
    freqs = torch.exp(-math.log(10000) * torch.arange(half, dtype=torch.float32) / half)
    ang = t.unsqueeze(-1) * freqs
    emb = torch.cat([torch.sin(ang), torch.cos(ang)], dim=-1)
    t_emb = linear_ac(model.t_emb.mlp[2], F.gelu(linear_ac(model.t_emb.mlp[0], emb)))
    x = conv_ac(model.in_conv, Ct_bf16)
    skips = []
    for i, (blocks, attn) in enumerate(zip(model.downs, model.down_attns)):
        for blk in blocks:
            x = resblock_em(blk, x, t_emb)
        if not isinstance(attn, torch.nn.Identity):
            x = attn_em(attn, x)
        h_i = feats[i]
        if h_i.shape[-2:] != x.shape[-2:]:
            h_i = F.interpolate(h_i, size=x.shape[-2:], mode="bilinear", align_corners=False)  # fp32 features
        x = bf(x.float() + conv_ac(model.adapters[i].conv, h_i).float())
        skips.append(x)
        x = F.avg_pool2d(x, 2)                                    # bf16 in, bf16 out
    x = resblock_em(model.mid_a, x, t_emb)
    x = attn_em(model.mid_attn, x)
    x = resblock_em(model.mid_b, x, t_emb)
    for blocks, attn, skip in zip(model.ups, model.up_attns, reversed(skips)):
        if bilinear_fp32:
            x = F.interpolate(x.float(), size=skip.shape[-2:], mode="bilinear", align_corners=False)   # fp32 out
            x = torch.cat([x, skip.float()], dim=1)                                                      # fp32 by promotion
        else:
            x = F.interpolate(x, size=skip.shape[-2:], mode="bilinear", align_corners=False)           # bf16
            x = torch.cat([x, skip], dim=1)
        for blk in blocks:
            x = resblock_em(blk, x, t_emb)
        if not isinstance(attn, torch.nn.Identity):
            x = attn_em(attn, x)
    return conv_ac(model.out_conv, F.silu(gn_ac(model.out_norm, x)))


# ---------------------------------------------------------------- scoring

VARIANTS = ("fp32", "bf16em", "bf16em_v2")


@torch.no_grad()
def scores_for(model, dc, M, sid, r, noise, offsets, wrong_clamp=False):
    """Returns {cond: {variant: score}} for correct and the wrong offsets whose E row exists."""
    C = load_C_bf16(sid, r)
    Ct = make_Ct(C, noise, dc, M)                      # bf16 (1,4,H,W)
    tt = torch.full((1,), T_VAL, dtype=torch.long)
    total = SESSIONS[sid]["rows_total"]
    out = {}
    conds = [("correct", r)]
    for o in offsets:
        rw = r + o
        if wrong_clamp:
            rw = min(rw, total - 1)                      # train_lean.quick_eval, line 205
        elif not row_available(sid, rw):
            continue                                     # lean_pubproto_eval.py:134 (boundary: absent)
        conds.append((f"wrong_{o:+d}", rw))
    for name, rr in conds:
        E = load_E_bf16(sid, rr).unsqueeze(0)
        e32 = model(Ct.float(), E.float(), tt)
        e1 = forward_cuda_bf16_emul(model, Ct, E, tt, bilinear_fp32=False)
        e2 = forward_cuda_bf16_emul(model, Ct, E, tt, bilinear_fp32=True)
        out[name] = {"fp32": score(e32, noise), "bf16em": score(e1, noise), "bf16em_v2": score(e2, noise), "row_cond": rr}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT / "float_repro.json"))
    ap.add_argument("--august", action="store_true", help="also score the held-out August rows 600-711 (G1 noise convention)")
    ap.add_argument("--quick-control", action="store_true", help="superseded artifact only: compare with train.log quick_eval means (noise 999+r)")
    ap.add_argument("--noise-check", action="store_true", help="alternative noise streams on the d2 quick_eval rows (needs --quick-control)")
    a = ap.parse_args()
    t0 = time.time()
    assert philox_self_test(), "Philox4x32-10 known-answer test failed"
    model, dc, M, ck = build_model(CKPT)
    ref = json.load(open(REF_JSON))
    sha = hashlib.sha256(open(CKPT, "rb").read()).hexdigest()
    assert sha == ref["checkpoint_sha256"], (sha, ref["checkpoint_sha256"])
    rows = eval_rows()
    print(f"ckpt {CKPT.name} sha ok ({sha[:12]}), params {sum(p.numel() for p in model.parameters())}, {len(rows)} protocol rows", flush=True)

    per_row = []
    for n, (sid, r) in enumerate(rows):
        pp = scores_for(model, dc, M, sid, r, protocol_noise(sid, r), OFFSETS)
        rec = {"sid": sid, "row": r, "protocol_noise_index": protocol_row_index(sid, r),
               "pubproto": {k: {**{v: pp[k][v] for v in VARIANTS}, "row_cond": pp[k]["row_cond"], "reference": None} for k in pp}}
        if a.quick_control:
            qq = scores_for(model, dc, M, sid, r, quick_eval_noise(r), [2], wrong_clamp=True)
            rec["quick_eval"] = {k: {v: qq[k][v] for v in VARIANTS} for k in qq}
        per_row.append(rec)
        print(f"[{n+1:2d}/{len(rows)}] {sid} {r}: correct fp32 {pp['correct']['fp32']:.6f} em {pp['correct']['bf16em']:.6f} em2 {pp['correct']['bf16em_v2']:.6f} | "
              f"wrong mean fp32 {np.mean([v['fp32'] for k, v in pp.items() if k != 'correct']):.6f}  ({time.time()-t0:.0f}s)", flush=True)

    aug = []
    if a.august:
        for n, (sid, r) in enumerate(august_rows()):
            pp = scores_for(model, dc, M, sid, r, protocol_noise(sid, r), august_offsets(r))
            aug.append({"sid": sid, "row": r, "protocol_noise_index": protocol_row_index(sid, r),
                        "pubproto": {k: {**{v: pp[k][v] for v in VARIANTS}, "row_cond": pp[k]["row_cond"]} for k in pp}})
            if n % 16 == 0:
                print(f"[august {n+1:3d}/112] row {r}: correct fp32 {pp['correct']['fp32']:.6f} | wrong mean fp32 "
                      f"{np.mean([v['fp32'] for k, v in pp.items() if k != 'correct']):.6f} ({len(pp)-1} offsets)  ({time.time()-t0:.0f}s)", flush=True)

    # coarse: 37-row means vs the full-session reference means
    coarse = {}
    for sid in ("d2", "v10"):
        rs = [x for x in per_row if x["sid"] == sid]
        for var in VARIANTS:
            d = {}
            for cond in ["correct"] + [f"wrong_{o:+d}" for o in OFFSETS]:
                vals = [x["pubproto"][cond][var] for x in rs if cond in x["pubproto"]]
                d[cond] = {"mean_37rows": float(np.mean(vals)), "ref_mean_all_rows": ref["sessions"][sid]["conditions"][cond], "n": len(vals)}
            c = np.array([x["pubproto"]["correct"][var] for x in rs])
            wm = np.array([np.mean([x["pubproto"][f"wrong_{o:+d}"][var] for o in OFFSETS]) for x in rs])
            d["paired_fraction_correct_lower"] = float((c < wm).mean()); d["ref_paired_fraction"] = ref["sessions"][sid]["paired_fraction_correct_lower"]
            d["delta_wrong_mean"] = float((wm - c).mean()); d["ref_delta_wrong_mean"] = ref["sessions"][sid]["delta_wrong_mean"]["mean"]
            coarse[f"{sid}_{var}"] = d
    diffs = {v: np.array([(x["pubproto"][c][v] - x["pubproto"][c]["fp32"]) / x["pubproto"][c]["fp32"] for x in per_row for c in x["pubproto"]]) for v in VARIANTS[1:]}

    control = None
    if a.quick_control:
        ref_q = read_trainlog_eval(12000)
        if ref_q:
            control = {}
            for sid in ("d2", "v10"):
                rs = [x for x in per_row if x["sid"] == sid]
                for var in VARIANTS:
                    c = np.array([x["quick_eval"]["correct"][var] for x in rs]); w = np.array([x["quick_eval"]["wrong_+2"][var] for x in rs])
                    control[f"{sid}_{var}"] = {"n": len(rs), "correct": float(c.mean()), "wrong": float(w.mean()), "paired": float((c < w).mean()),
                                                "ref_correct": ref_q[sid]["correct"], "ref_wrong": ref_q[sid]["wrong"],
                                                "rel_dev_correct": float(c.mean() / ref_q[sid]["correct"] - 1), "rel_dev_wrong": float(w.mean() / ref_q[sid]["wrong"] - 1)}

    out = {"checkpoint": str(CKPT), "checkpoint_sha256": sha, "checkpoint_step": ck["step"], "reference_json": str(REF_JSON), "env": env_summary(),
           "reference_per_row_raw_scores": {"available_locally": None, "note": "filled by positive_control.py"},
           "noise_rule": "CUDA Philox4x32-10 emulation of torch.randn on the A100 (common.randn_cuda_emul); Philox KAT passed; float transform approximate",
           "variants": {"fp32": "float32 model on the evaluator's bf16 C_t and E", "bf16em": "CUDA autocast rounding points, up-path bilinear in bf16",
                        "bf16em_v2": "as bf16em with upsample_bilinear2d promoted to fp32 (autocast fp32 list) and fp32 concat"},
           "control_quick_eval_step12000": control, "coarse_pubproto_session_means": coarse,
           "emulation_minus_fp32_relative": {v: {"mean": float(d.mean()), "std": float(d.std()), "max_abs": float(np.abs(d).max())} for v, d in diffs.items()},
           "rows": per_row, "august_rows": aug, "elapsed_s": time.time() - t0}
    json.dump(out, open(a.out, "w"), indent=1)
    print("=== COARSE: pubproto 37-row means vs full-session reference means ===")
    for k, v in coarse.items():
        print(f"{k:16s} correct {v['correct']['mean_37rows']:.6f} (ref all rows {v['correct']['ref_mean_all_rows']:.6f})  delta {v['delta_wrong_mean']:.6f} (ref {v['ref_delta_wrong_mean']:.6f})  paired {v['paired_fraction_correct_lower']:.3f}")
    for v, d in out["emulation_minus_fp32_relative"].items():
        print(f"{v} vs fp32 relative: mean {d['mean']:+.3e} std {d['std']:.3e} max|.| {d['max_abs']:.3e}")
    if control:
        for k, v in control.items():
            print(f"quick control {k:16s} correct rel {v['rel_dev_correct']:+.2e} wrong rel {v['rel_dev_wrong']:+.2e}")
    print(f"wrote {a.out} in {time.time()-t0:.0f}s ({len(aug)} august rows)")


if __name__ == "__main__":
    main()
