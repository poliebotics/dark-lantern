#!/usr/bin/env python3
"""eval_controls.py (BOSUN, 2026-09-09): the simple-baseline and shortcut controls Astra asked for, on the December 2024
sessions, for a saved ARM-I checkpoint. Same frozen rules as eval_xcfg.py (t = 150, one noise generator per session seeded
EVAL_SEED with one draw per row in row order, bf16, MSE residual), so the correct residuals are the ones already reported.
For every row the residual is scored under EVERY other emission of the session (exhaustive, 63 negatives), from which:
  prescribed   the published five offsets, per-row mean of the available ones (must reproduce eval_xcfg.py)
  random       five random within-session negatives per row (seeded), per-row mean
  exhaustive   all 63 negatives: pooled AUROC of correct vs all wrong, per-row mean, and the fraction beating every negative
  matched      the negative whose Perlin period (mean over RGB of 1/scale, from the chain) is closest to the correct row's
plus two shortcut negatives that need their own forward passes:
  shuffled     the correct emission with its 96x112 pixels spatially permuted (seeded per row): same colour statistics, no structure
  colourmatch  the prescribed +2 (or -2) wrong emission with its per-channel mean and std matched to the correct emission's
Row-bootstrap CIs (1,000 resamples) for AUROC and paired fraction throughout."""
import argparse, glob, hashlib, importlib.util, json, os, sys, time
import numpy as np, torch
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_xcfg import auroc_pooled, row_bootstrap, OFFSETS, T_VAL, EVAL_SEED

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True); ap.add_argument("--trainer", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "train_xcfg.py"))
    ap.add_argument("--cache-dir", required=True); ap.add_argument("--c-cache-fallback", default=""); ap.add_argument("--old-root", default="/nonexistent")
    ap.add_argument("--sessions", default="20241219_044052,20241219_044529,20241219_050046,20241219_050648,20241219_051150,20241219_051629,20241219_052040")
    ap.add_argument("--perlin-dir", required=True); ap.add_argument("--out", required=True); ap.add_argument("--save-raw", required=True)
    ap.add_argument("--n-random", type=int, default=5); ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    ck = torch.load(a.ckpt, map_location="cpu", weights_only=False); args = ck.get("args", {})
    TH, TW = (int(v) for v in str(args.get("out_size", "96,112")).split(","))
    spec = importlib.util.spec_from_file_location("xcfg", a.trainer); M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
    M.TH, M.TW = TH, TW; M.CACHE_DIR = a.cache_dir; M.EMISSION_IMAGE = True
    if a.c_cache_fallback: M.C_CACHE_FALLBACK = a.c_cache_fallback
    from pathlib import Path
    M.OLD_ROOT = Path(a.old_root)
    for sid in M.SESSIONS_2024: M.SESSIONS[sid]["file"] = M.OLD_ROOT / "2024" / f"{sid}.h5"
    for sid in M.SESSIONS_2023: M.SESSIONS[sid]["dir"] = M.OLD_ROOT / "2023" / sid
    sess = a.sessions.split(",")
    for sid in list(M.SESSIONS):
        if sid not in sess: del M.SESSIONS[sid]
    M.resolve_raw_layout()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    dc = M.build_diffusion_constants(1000, dev, torch.float32)
    base_ch = int(ck["model"]["in_conv.weight"].shape[0]); hint_in = int(ck["model"]["hint_encoder.s0.0.weight"].shape[1]); assert hint_in == 5
    model = M.ArmIUNet(in_ch=4, base_ch=base_ch, channel_mults=(1, 2, 4, 4), attn_at=(False, False, False, True), cond_drop_prob=0.2, hint_in_ch=5).to(dev)
    model.load_state_dict(ck["model"], strict=True); model.eval()
    res = {"checkpoint": a.ckpt, "checkpoint_step": ck.get("step"), "sessions": {}, "pooled": {},
           "rules": {"noise": "one generator per session, manual_seed(EVAL_SEED), one draw per row in row order (as eval_xcfg.py)", "t": T_VAL,
                     "random": f"{a.n_random} within-session negatives per row, numpy RandomState(EVAL_SEED + row) choice without replacement, per-row mean",
                     "matched": "the other row of the session with the closest Perlin period (mean over RGB of 1/scale; ties -> lower row)",
                     "shuffled": "the correct emission with its TH*TW pixel positions permuted by numpy RandomState(EVAL_SEED + 1000 + row), same permutation on all three channels",
                     "colourmatch": "the prescribed +2 wrong emission (-2 at the end), per channel rescaled to the correct emission's mean and std, clipped to [0,1]"}}
    pooled = {k: [] for k in ("correct", "prescribed", "random", "exhaustive_mean", "matched", "shuffled", "colourmatch")}
    pooled_all_wrong = []; beats_all = []; beats_single = []
    for sid in sess:
        S = M.SESSIONS[sid]; total = S["rows_total"]; rows = list(range(total))[: (a.limit or total)]
        per = json.load(open(os.path.join(a.perlin_dir, f"perlin_params_{sid}.json")))
        period = {fr["frame"]: float(np.mean([1.0 / s for s in fr["scales_rgb"]])) for fr in per["frames"]}
        E = {r: M.load_E(sid, r) for r in range(total)}
        R = np.full((len(rows), total), np.nan); cor = np.full(len(rows), np.nan); shuf = np.full(len(rows), np.nan); cmatch = np.full(len(rows), np.nan)
        gen = torch.Generator(device=dev); gen.manual_seed(EVAL_SEED); t0 = time.time()
        with torch.no_grad():
            for i, r in enumerate(rows):
                C = M.load_C(sid, r).to(dev, torch.bfloat16)
                noise = torch.randn(1, 4, TH, TW, device=dev, generator=gen)
                tt = torch.full((1,), T_VAL, device=dev, dtype=torch.long)
                Ct = M.q_sample(C.float().unsqueeze(0), tt, dc, noise).to(torch.bfloat16)
                def score(Et):
                    with torch.autocast(dev, dtype=torch.bfloat16, enabled=True):
                        e = model(Ct, Et.to(dev, torch.bfloat16).unsqueeze(0), tt)
                    return float((e.float() - noise).pow(2).mean())
                cor[i] = score(E[r])
                for rw in range(total):
                    if rw != r: R[i, rw] = score(E[rw])
                rng = np.random.RandomState(EVAL_SEED + 1000 + r); perm = torch.from_numpy(rng.permutation(TH * TW))
                Es = E[r].reshape(3, -1)[:, perm].reshape(3, TH, TW)
                shuf[i] = score(Es)
                rw2 = r + 2 if r + 2 < total else r - 2
                Ew = E[rw2].clone(); Ec = E[r]
                for ch in range(3):
                    mw, sw = Ew[ch].mean(), Ew[ch].std(); mc, sc = Ec[ch].mean(), Ec[ch].std()
                    Ew[ch] = ((Ew[ch] - mw) / (sw + 1e-6)) * sc + mc
                cmatch[i] = score(Ew.clamp(0, 1))
                if i % 16 == 0: print(f"  {sid} {i}/{len(rows)} {time.time()-t0:.0f}s", flush=True)
        # derived negatives
        presc = np.array([np.nanmean([R[i, r + o] for o in OFFSETS if 0 <= r + o < total]) for i, r in enumerate(rows)])
        rnd = np.array([np.mean(R[i, np.random.RandomState(EVAL_SEED + r).choice([x for x in range(total) if x != r], a.n_random, replace=False)]) for i, r in enumerate(rows)])
        exh_mean = np.nanmean(R, 1)
        matched_rows = [min((x for x in range(total) if x != r), key=lambda x: (abs(period[x] - period[r]), x)) for r in rows]
        matched = np.array([R[i, mr] for i, mr in enumerate(matched_rows)])
        def _single(i, r):
            o = OFFSETS[r % 5]; rw = r + o if 0 <= r + o < total else r - o
            return R[i, rw] if 0 <= rw < total else np.nan
        single = np.array([_single(i, r) for i, r in enumerate(rows)])
        all_wrong = R[~np.isnan(R)]
        cell = {"n_rows": len(rows),
                "prescribed_offsets": row_bootstrap(cor, presc), "random_negatives": row_bootstrap(cor, rnd),
                "exhaustive_mean_of_63": row_bootstrap(cor, exh_mean),
                "exhaustive_pooled_auroc_correct_vs_all_wrong": auroc_pooled(cor, all_wrong),
                "fraction_beating_every_negative": float(np.mean(np.nanmin(R, 1) > cor)),
                "fraction_beating_single_selected_wrong": float(np.nanmean(single > cor)),
                "matched_period_negative": row_bootstrap(cor, matched), "matched_period_gap_px_mean": float(np.mean([abs(period[mr] - period[r]) for r, mr in zip(rows, matched_rows)])),
                "shuffled_correct": row_bootstrap(cor, shuf), "colour_matched_wrong": row_bootstrap(cor, cmatch),
                "means": {"correct": float(cor.mean()), "prescribed": float(presc.mean()), "random": float(rnd.mean()), "exhaustive": float(exh_mean.mean()), "matched": float(matched.mean()), "shuffled": float(shuf.mean()), "colourmatch": float(cmatch.mean())}}
        res["sessions"][sid] = cell
        for k, v in (("correct", cor), ("prescribed", presc), ("random", rnd), ("exhaustive_mean", exh_mean), ("matched", matched), ("shuffled", shuf), ("colourmatch", cmatch)): pooled[k].append(v)
        pooled_all_wrong.append(all_wrong); beats_all.append(np.nanmin(R, 1) > cor); beats_single.append(single > cor)
        np.savez(f"{a.save_raw}_{sid}.npz", rows=np.array(rows), R=R, correct=cor, shuffled=shuf, colourmatch=cmatch, matched_rows=np.array(matched_rows), period=np.array([period[r] for r in rows]))
        print(json.dumps({sid: {k: (round(cell[k]["auroc"], 3), round(cell[k]["paired"], 3)) for k in ("prescribed_offsets", "random_negatives", "exhaustive_mean_of_63", "matched_period_negative", "shuffled_correct", "colour_matched_wrong")}}), flush=True)
    cor = np.concatenate(pooled["correct"])
    res["pooled"] = {k: row_bootstrap(cor, np.concatenate(pooled[k])) for k in ("prescribed", "random", "exhaustive_mean", "matched", "shuffled", "colourmatch")}
    res["pooled"]["exhaustive_pooled_auroc_correct_vs_all_wrong"] = auroc_pooled(cor, np.concatenate(pooled_all_wrong))
    res["pooled"]["n_rows"] = int(cor.size); res["pooled"]["beats_every_negative"] = int(np.concatenate(beats_all).sum()); res["pooled"]["beats_single_selected_wrong"] = int(np.concatenate(beats_single).sum())
    json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps({"pooled": {k: (round(v["auroc"], 3), round(v["paired"], 3)) if isinstance(v, dict) else v for k, v in res["pooled"].items()}}))

if __name__ == "__main__":
    main()
