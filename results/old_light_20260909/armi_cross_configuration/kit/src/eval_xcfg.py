#!/usr/bin/env python3
"""eval_xcfg.py (BOSUN, 2026-09-09): the published lean evaluator's statistic (lean_pubproto_eval.py, verbatim in its
rules) generalised to any session in train_xcfg.py's table, for the ARM-I cross-configuration test.

Frozen rules kept exactly: t = 150; the frame grid from the checkpoint's out_size; one noise generator per session seeded with
EVAL_SEED, one draw per row in row order, shared across all conditions of that row; bf16 autocast; the residual is the mean
squared error between predicted and true noise; the five wrong offsets [-2, +2, -15, +15, +30], each skipped when it falls
outside the session (never imputed); the per-row wrong statistic is the mean over the available offsets; pooled AUROC is the
Mann-Whitney P(wrong > correct) with average-rank ties; paired fraction is P(correct < wrong-mean); the delta CI is the block
bootstrap over contiguous eval blocks sub-blocked to 40 rows, 1000 resamples, seeded EVAL_SEED.

Added for the unseen configurations (labelled as such in the output): (a) row-level bootstrap CIs (1000 resamples, seeded)
for AUROC and paired fraction, since a 64-row session yields too few 40-row blocks; (b) the single-wrong rule used for the
zkdiff proof rows, offset = OFFSETS[row mod 5] mirrored when it leaves the session, as a secondary statistic; (c) a pairing
check for the old sessions, the residual under the emission one row before and one row after (shift -1 and +1), which
guards against an index misalignment in the archived pairing; (d) per-era pooling with row and session-cluster bootstraps.
Eval rows: d2/v10 their eval blocks; august rows 600..711 (held out from training by --august-train-rows 600, same session);
old sessions every row. No realness, liveness or capture claim: this measures emission-recording correspondence."""
import argparse, hashlib, importlib.util, json, os, sys, time
import numpy as np
import torch
sys.dont_write_bytecode = True

OFFSETS = [-2, 2, -15, 15, 30]
T_VAL, EVAL_SEED, SUB_TARGET, N_BOOT = 150, 20260823, 40, 1000


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


def block_bootstrap_ci(values, block_lengths, n_boot=N_BOOT, alpha=0.05, seed=EVAL_SEED):
    rng = np.random.RandomState(seed); b = [0]
    for L in block_lengths: b.append(b[-1] + L)
    blocks = [values[b[i]:b[i + 1]] for i in range(len(block_lengths))]
    boot = np.zeros(n_boot)
    for i in range(n_boot):
        idx = rng.randint(0, len(blocks), size=len(blocks))
        boot[i] = np.concatenate([blocks[j] for j in idx]).mean()
    return float(np.nanmean(values)), float(np.nanquantile(boot, alpha / 2)), float(np.nanquantile(boot, 1 - alpha / 2))


def row_bootstrap(correct, wrong, n_boot=N_BOOT, alpha=0.05, seed=EVAL_SEED):
    """Row-level bootstrap of the pooled AUROC and the paired fraction: rows resampled with replacement, both arrays
    together (the pairing is kept), 1000 resamples. Returns dict with point estimates and percentile CIs."""
    rng = np.random.RandomState(seed); n = correct.size
    au = np.zeros(n_boot); pf = np.zeros(n_boot)
    for i in range(n_boot):
        idx = rng.randint(0, n, size=n)
        au[i] = auroc_pooled(correct[idx], wrong[idx]); pf[i] = float(np.mean(correct[idx] < wrong[idx]))
    return {"auroc": auroc_pooled(correct, wrong), "auroc_ci95": [float(np.quantile(au, alpha / 2)), float(np.quantile(au, 1 - alpha / 2))],
            "paired": float(np.mean(correct < wrong)), "paired_ci95": [float(np.quantile(pf, alpha / 2)), float(np.quantile(pf, 1 - alpha / 2))],
            "n": int(n), "resamples": n_boot, "rule": "row bootstrap, rows resampled with replacement, seed EVAL_SEED"}


def cluster_bootstrap(groups, n_boot=N_BOOT, alpha=0.05, seed=EVAL_SEED):
    """Session-cluster bootstrap of the pooled AUROC: sessions resampled with replacement, all their rows pooled."""
    rng = np.random.RandomState(seed); k = len(groups)
    au = np.zeros(n_boot)
    for i in range(n_boot):
        idx = rng.randint(0, k, size=k)
        c = np.concatenate([groups[j][0] for j in idx]); w = np.concatenate([groups[j][1] for j in idx])
        au[i] = auroc_pooled(c, w)
    return [float(np.quantile(au, alpha / 2)), float(np.quantile(au, 1 - alpha / 2))]


def mirrored_offset(r, k, total):
    """The zkdiff proof-row rule: offset OFFSETS[k mod 5]; if it leaves the session, use the mirrored offset."""
    o = OFFSETS[k % 5]
    rw = r + o
    if rw < 0 or rw >= total:
        rw = r - o
    if rw < 0 or rw >= total:
        return None
    return rw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--trainer", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "train_xcfg.py"))
    ap.add_argument("--cache-dir", default="")
    ap.add_argument("--c-cache-fallback", default="")
    ap.add_argument("--old-root", default="")
    ap.add_argument("--local-root", default="")
    ap.add_argument("--sessions", default="", help="comma list; default all 2026 eval cells and every old session")
    ap.add_argument("--out", required=True)
    ap.add_argument("--save-raw", required=True, help="prefix for per-session npz of raw per-row scores")
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--pairing-check", action="store_true", help="old sessions: also score E at shift -1 and +1")
    ap.add_argument("--dump-examples", default="", help="npz path: C, E-correct, E-wrong(+2) for a few rows per session (contact sheet)")
    ap.add_argument("--n-examples", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0, help="tests: first N eval rows per session")
    a = ap.parse_args()

    ck = torch.load(a.ckpt, map_location="cpu", weights_only=False)
    args = ck.get("args", {})
    crop_id = str(args.get("crop_id", ""))
    if not crop_id.startswith("UNCROPPED"):
        raise SystemExit(f"REFUSING: checkpoint crop_id {crop_id!r} is not an uncropped run")
    out_size = str(args.get("out_size", "768,896")); TH, TW = (int(v) for v in out_size.split(","))
    emission_image = bool(args.get("emission_image", False))

    spec = importlib.util.spec_from_file_location("xcfg", a.trainer)
    M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
    M.TH, M.TW = TH, TW; M.CACHE_DIR = a.cache_dir or None; M.EMISSION_IMAGE = emission_image
    if a.c_cache_fallback: M.C_CACHE_FALLBACK = a.c_cache_fallback
    from pathlib import Path
    if a.old_root:
        M.OLD_ROOT = Path(a.old_root)
        for sid in M.SESSIONS_2024: M.SESSIONS[sid]["file"] = M.OLD_ROOT / "2024" / f"{sid}.h5"
        for sid in M.SESSIONS_2023: M.SESSIONS[sid]["dir"] = M.OLD_ROOT / "2023" / sid
    if a.sessions:
        sess = a.sessions.split(",")
    else:
        sess = ["d2", "v10", "august"] + (M.SESSIONS_2024 + M.SESSIONS_2023 if emission_image else [])
    for sid in list(M.SESSIONS):
        if sid not in sess: del M.SESSIONS[sid]
    if a.local_root:
        LR = Path(a.local_root); remap = {"d2": LR / "sessions/d2", "v10": LR / "sessions/v10", "august": LR / "august_dev_712"}
        for sid in M.SESSIONS:
            if sid in remap and remap[sid].is_dir(): M.SESSIONS[sid]["dir"] = remap[sid]
    M.resolve_raw_layout()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    dc = M.build_diffusion_constants(1000, dev, torch.float32)

    base_ch = int(ck["model"]["in_conv.weight"].shape[0])
    _m = args.get("mults") or (1, 2, 4, 4)
    mults = tuple(int(v) for v in _m.split(",")) if isinstance(_m, str) and _m else tuple(_m) if not isinstance(_m, str) else (1, 2, 4, 4)
    hint_in = int(ck["model"]["hint_encoder.s0.0.weight"].shape[1])
    if emission_image:
        assert hint_in == 5, hint_in
        model = M.ArmIUNet(in_ch=4, base_ch=base_ch, channel_mults=mults, attn_at=tuple(i == len(mults) - 1 for i in range(len(mults))), cond_drop_prob=0.2, hint_in_ch=5).to(dev)
    else:
        assert hint_in == 14, hint_in
        model = M.ArmCUNet(in_ch=4, base_ch=base_ch, channel_mults=mults, attn_at=tuple(i == len(mults) - 1 for i in range(len(mults))), cond_drop_prob=0.2, hint_in_ch=14).to(dev)
    model.load_state_dict(ck["model"], strict=True); model.eval()

    res = {"checkpoint": a.ckpt, "checkpoint_sha256": sha(a.ckpt), "checkpoint_step": ck.get("step"), "crop_id": crop_id, "out_size": out_size,
           "conditioning": "ARM-I: rendered emission image (3 ch) + coord (2)" if emission_image else "ARM-C: 12 XOF octave channels + coord (2)",
           "train_args": {k: args.get(k) for k in ("sessions", "august_train_rows", "seed", "max_steps", "cond_drop", "base_ch", "lr", "bs", "accum", "emission_image", "monitor_sessions")},
           "arch": {"kind": "armi" if emission_image else "armc", "base_ch": base_ch, "mults": list(mults), "hint_in_ch": hint_in, "params": int(sum(p.numel() for p in model.parameters()))},
           "preprocessing": {"C": "whole frame, no crop: 2026 the raw RGGB Bayer frame packed to 4 planes; 2024/2023 the stored demosaiced frame re-mosaiced onto the RGGB grid (R top-left, G top-right and bottom-left, B bottom-right of each 2x2 cell; 2024 recordings are stored BGR, 2023 reports RGB); planes /255, area-resized to out_size",
                             "E": "the rendered emission image as displayed, RGB in [0,1], area-resized to out_size (2026 tile PNG 1920x1080; 2024 HDF5 emissions 1920x1080 RGB; 2023 npy 1024x1024 float 0..255 stored BGR through OpenCV, reversed to RGB and clipped)"},
           "protocol": {"t": T_VAL, "offsets": OFFSETS, "stride": a.stride, "seed": EVAL_SEED, "sub_blocks": SUB_TARGET, "n_boot": N_BOOT,
                        "noise_rule": "one generator per session, manual_seed(EVAL_SEED), one draw per row in row order",
                        "primary": "pooled AUROC of correct residual vs per-row mean of the available wrong-offset residuals; paired fraction P(correct < wrong-mean)",
                        "secondary": "single wrong row, offset OFFSETS[row mod 5] mirrored at the session ends (the zkdiff proof-row rule)",
                        "claim_boundary": "emission-recording correspondence under a change of rig, camera, alignment and emission family; no realness, liveness or capture claim"},
           "sessions": {}, "eras": {}}

    raw_by_sid = {}
    examples = {}
    for sid in sess:
        if sid not in M.SESSIONS: continue
        S = M.SESSIONS[sid]; total = S["rows_total"]; kind = S.get("kind", "tb2026")
        if sid == "august":
            tr = int(args.get("august_train_rows", 712) or 712)
            blocks_def = [(tr, 712)] if tr < 712 else []
            cell_note = f"same session as training rows 0..{tr-1}; rows {tr}..711 unseen"
        elif kind == "tb2026":
            blocks_def = S["eval_blocks"]; cell_note = "published eval blocks (60-row guards), in-distribution sanity check"
        else:
            blocks_def = [(0, total)]; cell_note = f"unseen configuration ({S.get('era')}), every row"
        if not blocks_def:
            continue
        blocks, rows = [], []
        for (lo, hi) in blocks_def:
            rr = list(range(lo, hi, a.stride)); blocks.append(len(rr)); rows += rr
        if a.limit:
            rows = rows[:a.limit]; blocks = [len(rows)]
        keys = ["correct"] + [f"wrong_{o:+d}" for o in OFFSETS] + ["single_wrong"] + (["shift_-1", "shift_+1"] if (a.pairing_check and kind != "tb2026") else [])
        arrs = {k: np.full(len(rows), np.nan) for k in keys}
        single_rw = np.full(len(rows), -1, dtype=np.int64)
        gen = torch.Generator(device=dev); gen.manual_seed(EVAL_SEED)
        t0 = time.time()
        with torch.no_grad():
            for i, r in enumerate(rows):
                C = M.load_C(sid, r).to(dev, torch.bfloat16)
                noise = torch.randn(1, 4, TH, TW, device=dev, generator=gen)
                tt = torch.full((1,), T_VAL, device=dev, dtype=torch.long)
                Ct = M.q_sample(C.float().unsqueeze(0), tt, dc, noise).to(torch.bfloat16)
                Ec = M.load_E(sid, r)
                with torch.autocast(dev, dtype=torch.bfloat16, enabled=True):
                    e = model(Ct, Ec.to(dev, torch.bfloat16).unsqueeze(0), tt)
                arrs["correct"][i] = float((e.float() - noise).pow(2).mean())
                cache = {}
                def score(rw):
                    if rw in cache: return cache[rw]
                    with torch.autocast(dev, dtype=torch.bfloat16, enabled=True):
                        ew = model(Ct, M.load_E(sid, rw).to(dev, torch.bfloat16).unsqueeze(0), tt)
                    v = float((ew.float() - noise).pow(2).mean()); cache[rw] = v; return v
                for o in OFFSETS:
                    rw = r + o
                    if rw < 0 or rw >= total: continue
                    arrs[f"wrong_{o:+d}"][i] = score(rw)
                rw = mirrored_offset(r, r, total)   # offset by ROW number mod 5, mirrored at the session ends
                if rw is not None:
                    arrs["single_wrong"][i] = score(rw); single_rw[i] = rw
                if "shift_-1" in arrs:
                    if r - 1 >= 0: arrs["shift_-1"][i] = score(r - 1)
                    if r + 1 < total: arrs["shift_+1"][i] = score(r + 1)
                if a.dump_examples and i < a.n_examples:
                    rw2 = r + 2 if r + 2 < total else r - 2
                    examples[f"{sid}/{r}/C"] = C.float().cpu().numpy(); examples[f"{sid}/{r}/E_correct"] = Ec.numpy()
                    examples[f"{sid}/{r}/E_wrong"] = M.load_E(sid, rw2).numpy(); examples[f"{sid}/{r}/wrong_row"] = np.array(rw2)
                if i % 100 == 0: print(f"  {sid} {i}/{len(rows)} {time.time()-t0:.0f}s", flush=True)
        c = arrs["correct"]; W = np.stack([arrs[f"wrong_{o:+d}"] for o in OFFSETS], 1)
        wmean = np.nanmean(W, 1)
        eff = sub_block(blocks, SUB_TARGET)
        m, lo_, hi_ = block_bootstrap_ci(wmean - c, eff)
        fin = np.isfinite(c) & np.isfinite(wmean)
        rb = row_bootstrap(c[fin], wmean[fin])
        sw = arrs["single_wrong"]; fs = np.isfinite(c) & np.isfinite(sw)
        rbs = row_bootstrap(c[fs], sw[fs]) if fs.sum() > 1 else None
        cell = {"era": S.get("era"), "kind": kind, "note": cell_note, "n_rows": len(rows), "contiguous_eval_blocks": blocks, "blocks_used": eff,
                "conditions": {k: float(np.nanmean(v)) for k, v in arrs.items()},
                "delta_wrong_mean": {"mean": m, "ci95_block_bootstrap": [lo_, hi_], "relative": float(m / np.nanmean(c))},
                "paired_fraction_correct_lower": float(np.nanmean(c[fin] < wmean[fin])),
                "auroc": {"correct_vs_wrong_avg": auroc_pooled(c[fin], wmean[fin]),
                          **{f"correct_vs_wrong_{o:+d}": auroc_pooled(c[np.isfinite(arrs[f'wrong_{o:+d}'])], arrs[f"wrong_{o:+d}"][np.isfinite(arrs[f'wrong_{o:+d}'])])
                             for o in OFFSETS if np.isfinite(arrs[f'wrong_{o:+d}']).sum() > 1}},
                "row_bootstrap": rb,
                "secondary_single_wrong_mod5_mirrored": rbs,
                "raw_scores": f"{a.save_raw}_{sid}.npz"}
        if "shift_-1" in arrs:
            cell["pairing_check"] = {}
            for k in ("shift_-1", "shift_+1"):
                f2 = np.isfinite(c) & np.isfinite(arrs[k])
                cell["pairing_check"][k] = {"mean_residual": float(np.nanmean(arrs[k])), "auroc_correct_vs_shift": auroc_pooled(c[f2], arrs[k][f2]),
                                            "fraction_correct_lower": float(np.mean(c[f2] < arrs[k][f2]))}
            cell["pairing_check"]["reading"] = "the declared pairing is right when the correct residual sits below both one-row shifts"
        res["sessions"][sid] = cell
        raw_by_sid[sid] = (c[fin], wmean[fin], S.get("era"))
        np.savez(f"{a.save_raw}_{sid}.npz", rows=np.array(rows, dtype=np.int64), block_lengths=np.array(blocks, dtype=np.int64), single_wrong_row=single_rw, **arrs)
        print(json.dumps({sid: {"auroc": cell["auroc"]["correct_vs_wrong_avg"], "ci": rb["auroc_ci95"], "paired": cell["paired_fraction_correct_lower"], "delta": m, "n": len(rows)}}), flush=True)

    for era in ("2026", "2024", "2023"):
        groups = [(c, w) for sid, (c, w, e) in raw_by_sid.items() if e == era and sid != "august"]
        names = [sid for sid, (c, w, e) in raw_by_sid.items() if e == era and sid != "august"]
        if not groups: continue
        c = np.concatenate([g[0] for g in groups]); w = np.concatenate([g[1] for g in groups])
        rb = row_bootstrap(c, w)
        res["eras"][era] = {"sessions": names, "n_rows": int(c.size), "auroc": rb["auroc"], "auroc_ci95_row_bootstrap": rb["auroc_ci95"],
                            "auroc_ci95_session_cluster_bootstrap": cluster_bootstrap(groups) if len(groups) > 1 else None,
                            "paired": rb["paired"], "paired_ci95_row_bootstrap": rb["paired_ci95"],
                            "delta_wrong_mean": float(np.mean(w - c)), "mean_correct": float(np.mean(c)), "mean_wrong": float(np.mean(w)),
                            "note": "august (same session as training) excluded from the 2026 pool"}
    if a.dump_examples and examples:
        np.savez_compressed(a.dump_examples, **examples)
    with open(a.out, "w") as f: json.dump(res, f, indent=1)
    print(json.dumps({"eras": {e: {"auroc": d["auroc"], "ci": d["auroc_ci95_row_bootstrap"], "paired": d["paired"], "n": d["n_rows"]} for e, d in res["eras"].items()}}, indent=None))


if __name__ == "__main__":
    main()
