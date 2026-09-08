#!/usr/bin/env python3
"""G1 agreement study: integer (fixed-point) residual sums against the frozen evaluator's per-row
scores (and the fp32 / bf16-emulated reproductions) for the 37 protocol rows x 5 wrong offsets, for
the int16 (first baseline) and int8 weight schemes; plus the held-out August rows 600-711, which are
ALL proof rows by rule (wrong offset = OFFSETS[(r-600) mod 5]; integer and fp32 only, no evaluator
exists for August).

Residual-unit metric (Astra r2 item 3): for each (row, offset)
    D_q  = R_w^q - R_c^q                      integer margin, common units (MSE = sum/(43008*2^24))
    eta  = |R_w^q - R_w^f| + |R_c^q - R_c^f|  total integer-vs-reference error of the pair
    pass = D_q > 3*eta                        guarantees |D_q - D_f| <= eta for that pair
References R^f: the evaluator's own per-row score (R_eval, primary), the fp32 reproduction, and the
two bf16-autocast emulations.  The integer path covers the whole relation: C and E quantisation,
integer forward noising, the integer network and the quantised noise target.

Usage:  agreement.py --scheme int16 [--sessions d2,v10|august]  -> $G1_OUT/agreement_<scheme>[_august].json
        agreement.py --report                                     -> $G1_OUT/agreement.json + AGREEMENT.md
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np
import torch
from common import (CKPT, OFFSETS, OUT, RAW_DIR, SESSIONS, TH, TW, august_offsets, august_rows, env_summary, eval_rows, load_C_bf16,
                    load_E_bf16, protocol_noise, protocol_row_index, row_available, rule_pair)

FLOAT_VARIANTS = ("fp32", "bf16em", "bf16em_v2")


def auroc_pooled(correct, wrong):
    """lean_pubproto_eval.py:25-34 verbatim semantics: P(wrong > correct), average-rank ties."""
    x = np.concatenate([wrong, correct]); y = np.concatenate([np.ones(wrong.size), np.zeros(correct.size)])
    o = np.argsort(x, kind="mergesort"); r = np.empty(x.size); xs = x[o]; i = 0
    while i < xs.size:
        j = i
        while j + 1 < xs.size and xs[j + 1] == xs[i]:
            j += 1
        r[o[i:j + 1]] = (i + j + 2) / 2.0; i = j + 1
    return float((r[y == 1].sum() - wrong.size * (wrong.size + 1) / 2) / (wrong.size * correct.size))


def run_scheme(scheme, sessions, out_path, supplement=False):
    """supplement=True: keep an existing output file and compute only the (row, condition) pairs it lacks."""
    from int_ref import QuantModel
    torch.set_num_threads(16)
    fr = json.load(open(OUT / "float_repro.json"))
    if sessions == "august":
        rows = august_rows(); frow = {(x["sid"], x["row"]): x for x in fr["august_rows"]}
    else:
        rows = eval_rows(); frow = {(x["sid"], x["row"]): x for x in fr["rows"]}
    assert all((s, r) in frow for s, r in rows), "float_repro.json lacks these rows (run float_repro.py [--august] first)"
    existing = json.load(open(out_path)) if (supplement and Path(out_path).exists()) else None
    ex_rows = {(x["sid"], x["row"]): x for x in existing["rows"]} if existing else {}
    qm = QuantModel(scheme)
    scale = qm.B.score_scale()
    t0 = time.time()
    recs = []
    n_new = 0
    for n, (sid, r) in enumerate(rows):
        noise = protocol_noise(sid, r)
        C = load_C_bf16(sid, r)
        offs = august_offsets(r) if sessions == "august" else OFFSETS
        conds = [("correct", r)] + [(f"wrong_{o:+d}", r + o) for o in offs if row_available(sid, r + o)]
        rec = ex_rows.get((sid, r)) or {"sid": sid, "row": r, "protocol_noise_index": protocol_row_index(sid, r), "conds": {}}
        for cname, rr in conds:
            if cname in rec["conds"]:
                continue
            n_new += 1
            E = load_E_bf16(sid, rr)
            eps, inp = qm.run_int(C, noise, E)
            R_int = qm.score_int(eps, inp["noise_int"])
            e64 = qm.run_f64_real(inp["Ct"].real(), inp["E_int"].astype(np.float64) * 2.0 ** -14)
            f = frow[(sid, r)]["pubproto"][cname]
            d = {"row_cond": rr, "R_int": R_int, "R_int_mse": R_int / scale}
            for v in FLOAT_VARIANTS:
                d[f"R_{v}"] = f[v]
            if f.get("reference") is not None:
                d["R_eval"] = f["reference"]
            d["R_f64_on_int_inputs"] = float(((e64 - inp["noise_int"].astype(np.float64) * 2.0 ** -12) ** 2).mean())
            rec["conds"][cname] = d
        recs.append(rec)
        c = rec["conds"]
        if (sessions != "august" or n % 8 == 0) and not existing:
            print(f"[{scheme} {sessions} {n+1:3d}/{len(rows)}] {sid} {r}: int correct {c['correct']['R_int_mse']:.6f} (fp32 {c['correct']['R_fp32']:.6f}) "
                  f"wrong mean {np.mean([v['R_int_mse'] for k, v in c.items() if k != 'correct']):.6f} ({len(c)-1} offsets)  clips {sum(qm.B.sat.values())}  ({time.time()-t0:.0f}s)", flush=True)
    if existing:
        assert existing["scale_map"] == qm.scale_map, "scale map changed since the original run; rerun without --supplement"
        out = dict(existing); out["rows"] = recs
        out["clip_events"] = {k: existing["clip_events"].get(k, 0) + v for k, v in {**existing["clip_events"], **qm.B.sat}.items()} if qm.B.sat else existing["clip_events"]
        out["acc_bits_observed"] = {k: max(existing["acc_bits_observed"].get(k, 0), v) for k, v in {**existing["acc_bits_observed"], **qm.B.bounds_obs}.items()}
        out["supplement"] = {"added_conditions": n_new, "elapsed_s": time.time() - t0}
    else:
        out = {"scheme": scheme, "sessions": sessions, "checkpoint": str(CKPT), "env": env_summary(), "n_rows": len(rows), "score_scale": scale,
               "calib_rows": qm.calib_rows, "scale_map": qm.scale_map, "scale_source": qm.scale_source, "scale_histogram": qm.scale_histogram(),
               "clip_events": dict(qm.B.sat), "acc_bits_observed": qm.B.bounds_obs, "constants": qm.B.constants_summary(),
               "static_bounds_global": qm.static_bounds["global"], "noising": qm.B.noising, "elapsed_s": time.time() - t0, "rows": recs}
    json.dump(out, open(out_path, "w"), indent=1)
    print(f"wrote {out_path} ({time.time()-t0:.0f}s, {n_new} new conditions)")


# ---------------------------------------------------------------- analysis

def analyse(data, ref_key):
    rows = [x for x in data["rows"] if all(ref_key in c for c in x["conds"].values())]
    scale = data["score_scale"]
    pairs, per_row = [], []
    for x in rows:
        c = x["conds"]["correct"]
        Rc_q, Rc_f = c["R_int_mse"], c[ref_key]
        wq, wf = [], []
        for o in OFFSETS:
            k = f"wrong_{o:+d}"
            if k not in x["conds"]:
                continue
            w = x["conds"][k]
            Rw_q, Rw_f = w["R_int_mse"], w[ref_key]
            D_q = Rw_q - Rc_q; D_f = Rw_f - Rc_f
            eta = abs(Rw_q - Rw_f) + abs(Rc_q - Rc_f)
            pairs.append({"sid": x["sid"], "row": x["row"], "offset": o, "Rc_q": Rc_q, "Rw_q": Rw_q, "Rc_f": Rc_f, "Rw_f": Rw_f,
                          "D_q": D_q, "D_f": D_f, "eta": eta, "ratio": D_q / eta if eta > 0 else float("inf"),
                          "D_q_int": w["R_int"] - c["R_int"], "sign_int": w["R_int"] > c["R_int"], "sign_f": Rw_f > Rc_f, "pass_3eta": D_q > 3 * eta})
            wq.append(w["R_int"]); wf.append(Rw_f)
        n_w = len(wq)
        per_row.append({"sid": x["sid"], "row": x["row"], "n_wrong": n_w, "int_paired": n_w * c["R_int"] < sum(wq), "f_paired": Rc_f < np.mean(wf),
                        "int_margin_mse": np.mean(wq) / scale - Rc_q, "f_margin_mse": float(np.mean(wf) - Rc_f),
                        "row_err": max(abs(x["conds"][k]["R_int_mse"] - x["conds"][k][ref_key]) for k in x["conds"]),
                        "Rc_q": Rc_q, "Rc_f": Rc_f, "wmean_q": np.mean(wq) / scale, "wmean_f": float(np.mean(wf))})
    ratios = np.array([p["ratio"] for p in pairs]); Dq = np.array([p["D_q"] for p in pairs]); eta = np.array([p["eta"] for p in pairs])
    agree = np.array([p["sign_int"] == p["sign_f"] for p in pairs])
    q = lambda a, ps: {f"p{int(p)}": float(np.percentile(a, p)) for p in ps}
    by = lambda key: {str(v): {"n": int(sum(1 for p in pairs if p[key] == v)),
                               "sign_agree": int(sum(1 for p in pairs if p[key] == v and p["sign_int"] == p["sign_f"])),
                               "int_correct_lt_wrong": int(sum(1 for p in pairs if p[key] == v and p["sign_int"])),
                               "pass_3eta": int(sum(1 for p in pairs if p[key] == v and p["pass_3eta"])),
                               "min_ratio": float(min(p["ratio"] for p in pairs if p[key] == v))}
                      for v in sorted({p[key] for p in pairs}, key=str)}
    auroc = {}
    for sid in sorted({p["sid"] for p in per_row}):
        rr = [p for p in per_row if p["sid"] == sid]
        auroc[sid] = {"n": len(rr), "int": auroc_pooled(np.array([p["Rc_q"] for p in rr]), np.array([p["wmean_q"] for p in rr])),
                      "float": auroc_pooled(np.array([p["Rc_f"] for p in rr]), np.array([p["wmean_f"] for p in rr])),
                      "int_paired_fraction": float(np.mean([p["int_paired"] for p in rr])), "float_paired_fraction": float(np.mean([p["f_paired"] for p in rr]))}
    row_err = np.array([p["row_err"] for p in per_row]); row_margin = np.array([p["int_margin_mse"] for p in per_row])
    rel = np.array([(x["conds"][k]["R_int_mse"] - x["conds"][k][ref_key]) / x["conds"][k][ref_key] for x in rows for k in x["conds"]])
    ab = np.array([abs(x["conds"][k]["R_int_mse"] - x["conds"][k][ref_key]) for x in rows for k in x["conds"]])
    return {"reference": ref_key, "n_rows": len(rows), "n_pairs": len(pairs),
            "sign_agreement": {"agree": int(agree.sum()), "total": len(pairs), "fraction": float(agree.mean()),
                               "int_correct_lt_wrong": int(sum(p["sign_int"] for p in pairs)), "float_correct_lt_wrong": int(sum(p["sign_f"] for p in pairs)),
                               "by_session": by("sid"), "by_offset": by("offset"), "reversals": [p for p in pairs if p["sign_int"] != p["sign_f"]]},
            "paired_mean_of_wrong": {"int_rows_correct_lower": int(sum(p["int_paired"] for p in per_row)), "float_rows_correct_lower": int(sum(p["f_paired"] for p in per_row)),
                                     "rows": len(per_row), "disagreements": [p for p in per_row if p["int_paired"] != p["f_paired"]]},
            "D_q_over_eta": {"min": float(ratios.min()), **q(ratios, [5, 25, 50, 75, 95]), "max": float(ratios.max()),
                             "pairs_pass_3eta": int(sum(p["pass_3eta"] for p in pairs)), "pairs_fail_3eta": [p for p in pairs if not p["pass_3eta"]],
                             "best_pairs": sorted(pairs, key=lambda p: -p["ratio"])[:10], "worst_pairs": sorted(pairs, key=lambda p: p["ratio"])[:10]},
            "integer_margin_mse": {"min": float(Dq.min()), **q(Dq, [5, 25, 50, 75, 95]), "max": float(Dq.max()), "mean": float(Dq.mean()),
                                   "min_int_units": int(min(p["D_q_int"] for p in pairs)), "max_int_units": int(max(p["D_q_int"] for p in pairs))},
            "eta_mse": {"min": float(eta.min()), **q(eta, [5, 25, 50, 75, 95]), "max": float(eta.max()), "mean": float(eta.mean())},
            "score_error_vs_ref": {"abs": {"min": float(ab.min()), "median": float(np.median(ab)), "max": float(ab.max())},
                                   "rel": {"min": float(np.abs(rel).min()), "median": float(np.median(np.abs(rel))), "max": float(np.abs(rel).max()),
                                           "signed_mean": float(rel.mean()), "signed_std": float(rel.std())}},
            "row_margin_gt_3x_row_error": {"count": int(np.sum(row_margin > 3 * row_err)), "rows": len(per_row), "min_margin_over_error": float(np.min(row_margin / row_err))},
            "auroc_subset": auroc}


def network_only_error(data):
    vals = np.array([(c["R_int_mse"] - c["R_f64_on_int_inputs"]) / c["R_f64_on_int_inputs"] for x in data["rows"] for c in x["conds"].values()])
    return {"n": int(vals.size), "signed_rel_mean": float(vals.mean()), "signed_rel_std": float(vals.std()), "abs_rel_max": float(np.abs(vals).max())}


def august_table(data):
    """Every August row: integer and fp32 residual sums at all available offsets, the rule pair marked, D_q distribution and signs."""
    rows = []
    for x in data["rows"]:
        c = x["conds"]["correct"]; ro, rw_rule, rule_kind, nominal = rule_pair(x["row"])
        offs = {}
        for k, w in x["conds"].items():
            if k == "correct":
                continue
            o = int(k.split("_")[1])
            D_q = w["R_int_mse"] - c["R_int_mse"]; D_f = w["R_fp32"] - c["R_fp32"]
            eta = abs(w["R_int_mse"] - w["R_fp32"]) + abs(c["R_int_mse"] - c["R_fp32"])
            offs[f"{o:+d}"] = {"row_cond": w["row_cond"], "Rw_int": w["R_int"], "Rw_q": w["R_int_mse"], "Rw_f": w["R_fp32"], "D_q": D_q, "D_f": D_f, "eta": eta,
                               "ratio": D_q / eta if eta > 0 else float("inf"), "D_q_int": w["R_int"] - c["R_int"], "sign_int": w["R_int"] > c["R_int"], "sign_f": D_f > 0}
        rule = offs.get(f"{ro:+d}")
        rows.append({"row": x["row"], "stream_index": x["protocol_noise_index"], "Rc_int": c["R_int"], "Rc_q": c["R_int_mse"], "Rc_f": c["R_fp32"],
                     "rule_offset": ro, "nominal_offset": nominal, "offset_rule": rule_kind, "rule_wrong_row": rw_rule, "rule_available": rule is not None, "rule": rule, "offsets": offs,
                     "n_offsets": sum(1 for o in OFFSETS if f"{o:+d}" in offs),
                     "min_D_q_all_offsets": min(v["D_q"] for v in offs.values()), "all_sign_int": all(v["sign_int"] for v in offs.values()),
                     "all_sign_f": all(v["sign_f"] for v in offs.values())})
    avail = [r for r in rows if r["rule_available"]]
    Dq = np.array([r["rule"]["D_q"] for r in avail]); Df = np.array([r["rule"]["D_f"] for r in avail]); ratio = np.array([r["rule"]["ratio"] for r in avail])
    q = lambda a, ps: {f"p{int(p)}": float(np.percentile(a, p)) for p in ps}
    allpairs = [(r["row"], o, v) for r in rows for o, v in r["offsets"].items()]
    return {"n_rows": len(rows), "rule": "nominal offset = [-2,+2,-15,+15,+30][(r-600) mod 5]; boundary clause: if r+offset >= 712 use -offset (mirrored); one proof per row",
            "mirrored_rows": [r["row"] for r in rows if r["offset_rule"] == "mirrored"],
            "rule_pairs_available": len(avail), "rule_pairs_unavailable": [{"row": r["row"], "rule_offset": r["rule_offset"], "wrong_row": r["rule_wrong_row"], "offset_rule": r["offset_rule"],
                                                                            "reason": "wrong-hint row is a training row (< 600) whose E is not on this box (it is on the Lambda cache)"} for r in rows if not r["rule_available"]],
            "rule_D_q_mse": {"min": float(Dq.min()), **q(Dq, [5, 25, 50, 75, 95]), "max": float(Dq.max()), "mean": float(Dq.mean())},
            "rule_D_f_mse": {"min": float(Df.min()), "median": float(np.median(Df)), "max": float(Df.max())},
            "rule_D_q_over_eta_fp32": {"min": float(ratio.min()), "median": float(np.median(ratio)), "max": float(ratio.max())},
            "rule_sign": {"int_positive": int(sum(r["rule"]["sign_int"] for r in avail)), "fp32_positive": int(sum(r["rule"]["sign_f"] for r in avail)),
                          "agreement": int(sum(r["rule"]["sign_int"] == r["rule"]["sign_f"] for r in avail)), "n": len(avail),
                          "negative_rows_int": [r["row"] for r in avail if not r["rule"]["sign_int"]], "negative_rows_fp32": [r["row"] for r in avail if not r["rule"]["sign_f"]]},
            "all_offsets": {"pairs": len(allpairs), "int_correct_lt_wrong": int(sum(1 for _, _, v in allpairs if v["sign_int"])), "fp32_correct_lt_wrong": int(sum(1 for _, _, v in allpairs if v["sign_f"])),
                            "sign_agreement": int(sum(1 for _, _, v in allpairs if v["sign_int"] == v["sign_f"])), "min_D_q": float(min(v["D_q"] for _, _, v in allpairs)),
                            "negative_pairs_int": [(rr, o) for rr, o, v in allpairs if not v["sign_int"]]},
            "weakest_rule_rows": sorted(avail, key=lambda r: r["rule"]["D_q"])[:5], "rows": rows}


# ---------------------------------------------------------------- report

def load_eval_reference():
    ref = {}
    for sid in ("d2", "v10"):
        p = RAW_DIR / f"pubproto_raw.npz_{sid}.npz"
        if not p.exists():
            return None
        z = np.load(p)
        ref[sid] = {"index": {int(r): i for i, r in enumerate(z["rows"])}, "arrays": {k: z[k] for k in ["correct"] + [f"wrong_{o:+d}" for o in OFFSETS]}}
    return ref


def attach_eval_reference(data, ref):
    for x in data["rows"]:
        if x["sid"] not in ref:
            continue
        i = ref[x["sid"]]["index"][x["row"]]
        assert i == x["protocol_noise_index"]
        for cname, c in x["conds"].items():
            c["R_eval"] = float(ref[x["sid"]]["arrays"][cname][i])


LABELS = {"R_eval": "frozen evaluator per-row scores (A100, torch 2.7.0, bf16 autocast): eta includes the evaluator's own bf16 path",
          "R_fp32": "fp32 protocol reproduction", "R_bf16em": "bf16-autocast emulation, bilinear in bf16 (variant 1)",
          "R_bf16em_v2": "bf16-autocast emulation, bilinear promoted to fp32 (variant 2)"}


def write_report(out_json, out_md):
    fr = json.load(open(OUT / "float_repro.json"))
    pc_path = OUT / "positive_control.json"
    pc = json.load(open(pc_path)) if pc_path.exists() else None
    ref_eval = load_eval_reference()
    report = {"checkpoint": fr["checkpoint"], "checkpoint_sha256": fr["checkpoint_sha256"], "env": fr.get("env"), "float_reference": {"file": str(OUT / "float_repro.json")}, "schemes": {}, "august": {}}
    md = [f"# G1 agreement: integer residual sums against the frozen evaluator ({Path(fr['checkpoint']).name}, sha256 {fr['checkpoint_sha256'][:12]})", "",
          "37 protocol rows (d2 27, v10 10) x 5 wrong offsets (-2, +2, -15, +15, +30) = 185 (row, offset) pairs, protocol noise (one Philox",
          "stream per session seeded 20260823, each row at its original stream position). Residuals: sum of squared differences between",
          "predicted eps and the noise target over 4x96x112 values; the integer path quantises C, E and the noise (Q12, ties to even), forms",
          "C_t by integer q_sample, runs the integer network and sums (eps_int - noise_int)^2 exactly; MSE units divide by 43008 * 2^24.",
          "Metric: D_q = R_w^q - R_c^q, eta = |R_w^q - R_w^f| + |R_c^q - R_c^f|, selection rule D_q > 3 eta.", ""]
    if pc:
        report["float_reference"]["positive_control_vs_frozen_evaluator"] = pc["summary"]; report["float_reference"]["emulation_variant_closer"] = pc["emulation_variant_closer_to_evaluator"]
        md += ["## Positive control against the frozen evaluator (per-row raw scores)", "",
               f"Reference arrays: `{pc['reference_files']['d2']}` and `..._v10.npz`. Our 37 rows sit at their evaluator stream positions (asserted per row).",
               f"Deviation of our protocol-stream scores from the evaluator's, over all {pc['summary']['overall']['fp32']['n']} (row, condition) scores:", "",
               "| scope | variant | n | abs max | abs median | rel max | rel median | rel signed mean (std) |", "|---|---|---|---|---|---|---|---|"]
        for scope, d in [("overall", pc["summary"]["overall"])] + [(f"session {k}", v) for k, v in pc["summary"]["by_session"].items()] + [(f"offset {k}", v) for k, v in pc["summary"]["by_offset"].items()]:
            for var in FLOAT_VARIANTS:
                v = d[var]
                md.append(f"| {scope} | {var} | {v['n']} | {v['abs_max']:.2e} | {v['abs_median']:.2e} | {v['rel_max']:.2e} | {v['rel_median']:.2e} | {v['rel_signed_mean']:+.2e} ({v['rel_signed_std']:.2e}) |")
        cl = pc["emulation_variant_closer_to_evaluator"]; r37 = pc["reference_on_37_rows"]
        md += ["", f"Emulation variant closer to the evaluator: **{cl['variant']}** (rel median {cl['rel_median']['bf16em']:.2e} vs {cl['rel_median']['bf16em_v2']:.2e}; signed mean "
               f"{cl['rel_signed_mean']['bf16em']:+.2e} vs {cl['rel_signed_mean']['bf16em_v2']:+.2e}).",
               f"The evaluator's own scores on these 37 rows: paired {r37['paired_rows']}/{r37['rows']}, margin (mean wrong minus correct) min {r37['margin_min']:.6f}, median {r37['margin_median']:.6f}.", ""]
    for scheme in ("int16", "int8"):
        p = OUT / f"agreement_{scheme}.json"
        if not p.exists():
            md += [f"## {scheme}: NOT RUN", ""]; continue
        data = json.load(open(p))
        if ref_eval:
            attach_eval_reference(data, ref_eval)
        refs = (["R_eval"] if ref_eval else []) + [f"R_{v}" for v in FLOAT_VARIANTS]
        res = {ref: analyse(data, ref) for ref in refs}
        neto = network_only_error(data)
        g = data["static_bounds_global"]
        report["schemes"][scheme] = {"clip_events": data["clip_events"], "acc_bits_observed_max": max(data["acc_bits_observed"].values()), "elapsed_s": data["elapsed_s"],
                                     "calib_rows": data["calib_rows"], "scale_histogram": data["scale_histogram"], "static_bounds_global": g, "network_only_error": neto,
                                     **{("vs_eval" if ref == "R_eval" else "vs_" + ref[2:]): res[ref] for ref in refs}}
        md += [f"## Scheme `{scheme}` (per-output-channel {scheme} weights, int16 activations)", "",
               f"Clip events over all 222 forwards (inputs, C_t, every op, LUT clipped hits): {sum(data['clip_events'].values())}" + (f" {data['clip_events']}" if data["clip_events"] else "") +
               f". Largest observed conv accumulator: {max(data['acc_bits_observed'].values())} bits against a static bound of {g['conv_acc_bound_max'].bit_length()} bits "
               f"({g['conv_acc_bound_max']:,}); requantisation expression bound {g['conv_requant_expr_max']:,} (< 2^63); GroupNorm n <= {g['gn_n_max']}, N < 2^{g['gn_N_bits_max']}, "
               f"X^2 <= {g['gn_X2_bits_max']} bits, affine product < 2^{g['gn_affine_bits_max']}; SSE <= {g['sse_bound']:,}. Effective scale histogram {data['scale_histogram']}. Runtime {data['elapsed_s']:.0f} s.", "",
               f"Network-only error (integer vs float64 network on the integer path's own inputs/target): signed rel mean {neto['signed_rel_mean']:+.2e}, std {neto['signed_rel_std']:.2e}, max |.| {neto['abs_rel_max']:.2e} over {neto['n']} scores.", ""]
        for ref in refs:
            a = res[ref]; sa = a["sign_agreement"]; pm = a["paired_mean_of_wrong"]; de = a["D_q_over_eta"]; im = a["integer_margin_mse"]; et = a["eta_mse"]; se = a["score_error_vs_ref"]
            md += [f"### vs {LABELS[ref]}", "",
                   f"- Sign agreement (correct < wrong, per pair): **{sa['agree']}/{sa['total']}**; integer says correct<wrong in {sa['int_correct_lt_wrong']}/{sa['total']}, reference in {sa['float_correct_lt_wrong']}/{sa['total']}.",
                   f"- Paired (correct < mean of wrong, exact integer comparison): integer {pm['int_rows_correct_lower']}/{pm['rows']} rows, reference {pm['float_rows_correct_lower']}/{pm['rows']}; disagreements {len(pm['disagreements'])}.",
                   f"- D_q/eta: min **{de['min']:.2f}**, p5 {de['p5']:.2f}, median {de['p50']:.2f}, p95 {de['p95']:.2f}, max {de['max']:.2f}; pairs with D_q > 3 eta: **{de['pairs_pass_3eta']}/{a['n_pairs']}**.",
                   f"- Integer margin D_q (MSE units): min {im['min']:.6f}, median {im['p50']:.6f}, max {im['max']:.6f} (integer units min {im['min_int_units']}, max {im['max_int_units']}).",
                   f"- eta (MSE units): min {et['min']:.2e}, median {et['p50']:.2e}, max {et['max']:.2e}.",
                   f"- Score error |R^q - R^f|: abs median {se['abs']['median']:.2e}, max {se['abs']['max']:.2e}; relative median {se['rel']['median']:.2e}, max {se['rel']['max']:.2e}; signed mean {se['rel']['signed_mean']:+.2e} (std {se['rel']['signed_std']:.2e}).",
                   f"- Rows with (mean-wrong minus correct) margin > 3x the row's max score error: {a['row_margin_gt_3x_row_error']['count']}/{a['row_margin_gt_3x_row_error']['rows']} (min margin/error {a['row_margin_gt_3x_row_error']['min_margin_over_error']:.2f}).", "",
                   "| session | pairs | sign agree | int c<w | pass 3eta | min D_q/eta |", "|---|---|---|---|---|---|"]
            for s, v in sa["by_session"].items():
                md.append(f"| {s} | {v['n']} | {v['sign_agree']} | {v['int_correct_lt_wrong']} | {v['pass_3eta']} | {v['min_ratio']:.2f} |")
            md += ["", "| offset | pairs | sign agree | int c<w | pass 3eta | min D_q/eta |", "|---|---|---|---|---|---|"]
            for s, v in sa["by_offset"].items():
                md.append(f"| {s} | {v['n']} | {v['sign_agree']} | {v['int_correct_lt_wrong']} | {v['pass_3eta']} | {v['min_ratio']:.2f} |")
            md += ["", "| session | n | AUROC int | AUROC ref | paired int | paired ref |", "|---|---|---|---|---|---|"]
            for s, v in a["auroc_subset"].items():
                md.append(f"| {s} | {v['n']} | {v['int']:.4f} | {v['float']:.4f} | {v['int_paired_fraction']:.3f} | {v['float_paired_fraction']:.3f} |")
            if sa["reversals"]:
                md += ["", "Reversals (integer and reference disagree on correct < wrong):", ""]
                for p_ in sa["reversals"]:
                    md.append(f"- {p_['sid']} row {p_['row']} offset {p_['offset']:+d}: Rc_q {p_['Rc_q']:.6f} Rw_q {p_['Rw_q']:.6f} (D_q {p_['D_q']:+.2e}); Rc_f {p_['Rc_f']:.6f} Rw_f {p_['Rw_f']:.6f} (D_f {p_['D_f']:+.2e}); eta {p_['eta']:.2e}: "
                              f"the reference margin is {abs(p_['D_f'])/p_['eta']:.2f} eta, inside the error band, so the pair is undecided rather than contradicted.")
            else:
                md += ["", "Reversals: none.", ""]
            if de["pairs_fail_3eta"]:
                md += ["", f"Pairs failing D_q > 3 eta ({len(de['pairs_fail_3eta'])}):", ""]
                for p_ in de["pairs_fail_3eta"]:
                    md.append(f"- {p_['sid']} row {p_['row']} offset {p_['offset']:+d}: D_q {p_['D_q']:.6f}, eta {p_['eta']:.2e}, ratio {p_['ratio']:.2f}")
            md += ["", "Ten strongest candidate pairs (largest D_q/eta):", "", "| session | row | offset | R_c^q | R_w^q | D_q | eta | D_q/eta |", "|---|---|---|---|---|---|---|---|"]
            for p_ in de["best_pairs"]:
                md.append(f"| {p_['sid']} | {p_['row']} | {p_['offset']:+d} | {p_['Rc_q']:.6f} | {p_['Rw_q']:.6f} | {p_['D_q']:.6f} | {p_['eta']:.2e} | {p_['ratio']:.1f} |")
            md += ["", "Five weakest pairs (smallest D_q/eta):", "", "| session | row | offset | R_c^q | R_w^q | D_q | eta | D_q/eta |", "|---|---|---|---|---|---|---|---|"]
            for p_ in de["worst_pairs"][:5]:
                md.append(f"| {p_['sid']} | {p_['row']} | {p_['offset']:+d} | {p_['Rc_q']:.6f} | {p_['Rw_q']:.6f} | {p_['D_q']:.6f} | {p_['eta']:.2e} | {p_['ratio']:.1f} |")
            md.append("")
        md += [f"### Per-row scores, `{scheme}` (MSE units; int = integer path, eval = frozen evaluator, f = fp32)", "",
               "| session | row | stream idx | R_c int | R_c eval | R_c f | mean R_w int | mean R_w eval | mean R_w f | int margin | eval margin | max err vs eval |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for x in data["rows"]:
            c = x["conds"]["correct"]; ws = [v for k, v in x["conds"].items() if k != "correct"]
            mi = np.mean([w["R_int_mse"] for w in ws]); mf = np.mean([w["R_fp32"] for w in ws])
            if ref_eval:
                me = np.mean([w["R_eval"] for w in ws]); ce = f"{c['R_eval']:.6f}"; mes = f"{me:.6f}"; eme = f"{me-c['R_eval']:.6f}"; erre = f"{max(abs(v['R_int_mse'] - v['R_eval']) for v in x['conds'].values()):.2e}"
            else:
                ce = mes = eme = erre = "n/a"
            md.append(f"| {x['sid']} | {x['row']} | {x['protocol_noise_index']} | {c['R_int_mse']:.6f} | {ce} | {c['R_fp32']:.6f} | {mi:.6f} | {mes} | {mf:.6f} | {mi-c['R_int_mse']:.6f} | {eme} | {erre} |")
        md.append("")
    # ---- August: every held-out row is a proof row (rule offset)
    for scheme in ("int16", "int8"):
        p = OUT / f"agreement_{scheme}_august.json"
        if not p.exists():
            continue
        data = json.load(open(p))
        at = august_table(data)
        report["august"][scheme] = dict(at); report["august"][scheme]["clip_events"] = data["clip_events"]
        rs = at["rule_sign"]; dq = at["rule_D_q_mse"]; ao = at["all_offsets"]
        md += [f"## August held-out rows 600-711 as proof rows, scheme `{scheme}` (integer and fp32 only; no evaluator reference exists)", "",
               f"Rule: {at['rule']}. Mirrored rows: {at['mirrored_rows']}. Noise (normative, README_FINAL.md section 5): Philox key 20260823, counter word 0 = r-600,",
               "Box-Muller lane x, Q12 ties-to-even; the exported noise_int bytes in final/august_inputs/ are what the guest consumes.",
               f"{at['n_rows']} rows; rule pair available on this box for {at['rule_pairs_available']} rows; {len(at['rule_pairs_unavailable'])} rows need a wrong-hint E from a training row (< 600) that is not on the development machine: "
               + ", ".join(f"{u['row']}({u['rule_offset']:+d}->{u['wrong_row']})" for u in at["rule_pairs_unavailable"]) + ".", "",
               f"Rule-pair D_q (MSE units): min **{dq['min']:.6f}**, p5 {dq['p5']:.6f}, median {dq['p50']:.6f}, p95 {dq['p95']:.6f}, max {dq['max']:.6f}, mean {dq['mean']:.6f}; "
               f"fp32 D_f min {at['rule_D_f_mse']['min']:.6f}, median {at['rule_D_f_mse']['median']:.6f}; D_q/eta_fp32 min {at['rule_D_q_over_eta_fp32']['min']:.1f}, median {at['rule_D_q_over_eta_fp32']['median']:.1f}.",
               f"Rule-pair sign: integer correct < wrong in **{rs['int_positive']}/{rs['n']}**, fp32 in {rs['fp32_positive']}/{rs['n']}, agreement {rs['agreement']}/{rs['n']}. "
               f"Negative integer rule pairs: {rs['negative_rows_int'] if rs['negative_rows_int'] else 'none'}; negative fp32 rule pairs: {rs['negative_rows_fp32'] if rs['negative_rows_fp32'] else 'none'}.",
               f"All available offsets: {ao['pairs']} pairs, integer correct < wrong in {ao['int_correct_lt_wrong']}, fp32 in {ao['fp32_correct_lt_wrong']}, sign agreement {ao['sign_agreement']}, min D_q {ao['min_D_q']:.6f}; negative integer pairs {ao['negative_pairs_int'] if ao['negative_pairs_int'] else 'none'}. "
               f"Clip events {sum(data['clip_events'].values())}" + (f" {data['clip_events']}" if data["clip_events"] else "") + ".", "",
               "Weakest rule pairs (smallest integer D_q):", "", "| row | rule offset | R_c int (sum) | R_w int (sum) | D_q (MSE) | D_f (MSE) | eta | D_q/eta |", "|---|---|---|---|---|---|---|---|"]
        for r in at["weakest_rule_rows"]:
            v = r["rule"]
            md.append(f"| {r['row']} | {r['rule_offset']:+d}{' (m)' if r['offset_rule']=='mirrored' else ''} | {r['Rc_int']} | {v['Rw_int']} | {v['D_q']:.6f} | {v['D_f']:.6f} | {v['eta']:.2e} | {v['ratio']:.1f} |")
        md += ["", f"### Every August row, `{scheme}` (integer residual sums are exact int; MSE = sum / (43008 * 2^24))", "",
               "| row | idx | rule offset (m = mirrored) | R_c int sum | R_c int MSE | R_c fp32 | R_w int sum (rule) | R_w fp32 (rule) | D_q rule | D_f rule | sign int/f | D_q -2 | D_q +2 | D_q -15 | D_q +15 | D_q +30 |",
               "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in at["rows"]:
            v = r["rule"]
            rule_cells = (f"{v['Rw_int']} | {v['Rw_f']:.6f} | {v['D_q']:+.6f} | {v['D_f']:+.6f} | {'+' if v['sign_int'] else '-'}/{'+' if v['sign_f'] else '-'}") if v else "pending E | n/a | n/a | n/a | n/a"
            cells = " | ".join((f"{r['offsets'][f'{o:+d}']['D_q']:+.6f}" if f"{o:+d}" in r["offsets"] else "n/a") for o in OFFSETS)
            md.append(f"| {r['row']} | {r['stream_index']} | {r['rule_offset']:+d}{' (m)' if r['offset_rule']=='mirrored' else ''} | {r['Rc_int']} | {r['Rc_q']:.6f} | {r['Rc_f']:.6f} | {rule_cells} | {cells} |")
        md.append("")
    md += ["## Log", "", "- 2.0 (2026-09-07, BOSUN) — FINAL artifact report generated by agreement.py --report (evaluator reference first; August rows added)."]
    json.dump(report, open(out_json, "w"), indent=1)
    Path(out_md).write_text("\n".join(md))
    print(f"wrote {out_json} and {out_md}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scheme", choices=["int16", "int8"])
    ap.add_argument("--sessions", default="d2,v10", choices=["d2,v10", "august"])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--supplement", action="store_true", help="compute only the (row, condition) pairs missing from an existing output file")
    a = ap.parse_args()
    if a.scheme:
        suffix = "_august" if a.sessions == "august" else ""
        run_scheme(a.scheme, a.sessions, OUT / f"agreement_{a.scheme}{suffix}.json", supplement=a.supplement)
    if a.report:
        write_report(OUT / "agreement.json", OUT / "AGREEMENT.md")


if __name__ == "__main__":
    main()
