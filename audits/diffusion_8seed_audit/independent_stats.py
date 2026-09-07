#!/usr/bin/env python3
"""INDEPENDENT recompute of the C-NC8 statistics from the raw per-row scores.

Shares no code with armc_pubproto_eval.py: ranks, AUROC, paired fraction, deltas and the
block bootstrap are implemented fresh here from the written protocol (offsets -2/+2/-15/+15/+30,
pooled Mann-Whitney AUROC with average-rank ties, contiguous eval blocks sub-blocked toward 40,
1000 bootstrap reps seeded 20260823, paired fraction correct<mean(wrong)). NaN discipline is
explicit: effective sample counts reported per condition, non-finite pairs dropped, bootstrap
replicates that lose all data counted and reported (Sol F8). Full-precision AUROCs reported so
rounded 0.99999x values are never presented as exact saturation (Sol F6).
"""
import glob, json, hashlib, os
import numpy as np

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
WRONG = ["wrong_-2", "wrong_+2", "wrong_-15", "wrong_+15", "wrong_+30"]
SEED, NBOOT, SUBTARGET = 20260823, 1000, 40

def avg_ranks(x):
    order = np.argsort(x, kind="stable")
    ranks = np.empty(len(x), dtype=np.float64)
    sx = x[order]
    i = 0
    while i < len(sx):
        j = i
        while j + 1 < len(sx) and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return ranks

def auroc(neg, pos):
    """P(pos > neg) with average-rank tie handling; neg=correct errs, pos=wrong errs."""
    neg = neg[np.isfinite(neg)]; pos = pos[np.isfinite(pos)]
    if len(neg) == 0 or len(pos) == 0:
        return float("nan"), 0, 0
    allv = np.concatenate([pos, neg])
    r = avg_ranks(allv)
    u = r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2.0
    return float(u / (len(pos) * len(neg))), len(neg), len(pos)

def sub_blocks(lengths, target):
    out = []
    for L in lengths:
        n = max(1, round(L / target))
        base, rem = divmod(L, n)
        out += [base + 1] * rem + [base] * (n - rem)
    return out

def block_bootstrap(values, lengths, seed=SEED, nboot=NBOOT):
    rng = np.random.RandomState(seed)
    edges = np.cumsum([0] + list(lengths))
    blocks = [values[edges[i]:edges[i + 1]] for i in range(len(lengths))]
    reps = np.full(nboot, np.nan)
    dead = 0
    for b in range(nboot):
        pick = rng.randint(0, len(blocks), size=len(blocks))
        cat = np.concatenate([blocks[k] for k in pick])
        fin = np.isfinite(cat)
        if fin.any():
            reps[b] = cat[fin].mean()
        else:
            dead += 1
    return (float(np.nanquantile(reps, 0.025)), float(np.nanquantile(reps, 0.975)), dead)

report = {"schema": "c-nc8-independent-recompute/v1", "bootstrap": {"reps": NBOOT, "seed": SEED, "sub_target": SUBTARGET}, "seeds": {}}
mismatch = 0
for jp in sorted(glob.glob(os.path.join(OUT, "*.json"))):
    ref = json.load(open(jp))
    name = os.path.basename(jp)[:-5]
    entry = {"result_json_sha256": hashlib.sha256(open(jp, "rb").read()).hexdigest(), "sessions": {}}
    for sid, rd in ref["sessions"].items():
        z = np.load(os.path.join(RAW, f"{name}_{sid}.npz"), allow_pickle=False)
        c = z["correct"].astype(np.float64)
        w = np.stack([z[k].astype(np.float64) for k in WRONG], 1)
        wmean = np.where(np.isfinite(w).any(1), np.nanmean(np.where(np.isfinite(w), w, np.nan), 1), np.nan)
        fin = np.isfinite(c) & np.isfinite(wmean)
        a_avg, n_neg, n_pos = auroc(c[fin], wmean[fin])
        per_off = {}
        for k in WRONG:
            wk = z[k].astype(np.float64)
            fk = np.isfinite(c) & np.isfinite(wk)
            a_k, nn, np_ = auroc(c[fk], wk[fk])
            per_off[k] = {"auroc": a_k, "n_pairs": int(fk.sum())}
        paired = float(np.mean(c[fin] < wmean[fin]))
        delta = wmean - c
        eff = sub_blocks([int(x) for x in z["block_lengths"]], SUBTARGET)
        assert sum(eff) == len(delta), "sub-block partition does not cover rows"
        lo, hi, dead = block_bootstrap(delta, eff)
        mine = {"auroc_avg_full_precision": a_avg, "paired_fraction": paired,
                "delta_mean": float(np.nanmean(delta)), "delta_ci95": [lo, hi],
                "dead_bootstrap_reps": dead, "n_rows": int(len(c)),
                "n_finite_pairs": int(fin.sum()), "per_offset": per_off,
                "exactly_saturated": bool(a_avg == 1.0)}
        ref_a = rd["auroc"]["correct_vs_wrong_avg"]; ref_p = rd["paired_fraction_correct_lower"]
        ref_d = rd["delta_wrong_mean"]["mean"]
        agree = {"auroc_matches_ref": bool(abs(a_avg - ref_a) < 1e-12),
                 "paired_matches_ref": bool(abs(paired - ref_p) < 1e-12),
                 "delta_matches_ref": bool(abs(mine["delta_mean"] - ref_d) < 1e-9),
                 "ref": {"auroc": ref_a, "paired": ref_p, "delta": ref_d}}
        if not (agree["auroc_matches_ref"] and agree["paired_matches_ref"] and agree["delta_matches_ref"]):
            mismatch += 1
        entry["sessions"][sid] = {"independent": mine, "agreement": agree}
        print(f"{name:44} {sid:3} auroc={a_avg:.15f} sat={a_avg==1.0} paired={paired:.6f} "
              f"n={fin.sum()}/{len(c)} ci=({lo:.3e},{hi:.3e}) dead={dead} "
              f"match={agree['auroc_matches_ref'] and agree['paired_matches_ref'] and agree['delta_matches_ref']}")
    report["seeds"][name] = entry
report["mismatched_cells"] = mismatch
op = os.path.join(os.path.dirname(os.path.abspath(__file__)), "INDEPENDENT_RECOMPUTE.json")
json.dump(report, open(op, "w"), indent=1, sort_keys=True)
print("mismatched cells:", mismatch)
print("wrote", op, hashlib.sha256(open(op, "rb").read()).hexdigest())
