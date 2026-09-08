#!/usr/bin/env python3
"""Write $G1_OUT/FREEZE_SUMMARY.md from the JSON outputs of a freeze_artifact.sh run: the headline
numbers a reader needs before opening AGREEMENT.md (positive control, weakest pairs against the
evaluator, clip events, bounds, August rule-pair D_q distribution, artifact hashes)."""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from common import CKPT, OUT, RAW_DIR, REF_JSON


def main():
    ag = json.load(open(OUT / "agreement.json"))
    pc = json.load(open(OUT / "positive_control.json"))
    fr = json.load(open(OUT / "float_repro.json"))
    sha = hashlib.sha256(open(CKPT, "rb").read()).hexdigest()
    md = [f"# FREEZE SUMMARY: {CKPT.name}", "",
          f"- checkpoint sha256 `{sha}` (verified against `{REF_JSON.name}`), step {fr['checkpoint_step']}; evaluator raw scores from `{RAW_DIR}`",
          f"- generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} on {fr['env']['torch']=} {fr['env']['numpy']=}".replace("fr['env']['torch']=", "torch ").replace("fr['env']['numpy']=", "numpy "),
          "", "## Positive control against the frozen evaluator (222 scores)", "", "| variant | rel median | rel max | signed mean (std) |", "|---|---|---|---|"]
    for v in ("fp32", "bf16em", "bf16em_v2"):
        s = pc["summary"]["overall"][v]
        md.append(f"| {v} | {s['rel_median']:.2e} | {s['rel_max']:.2e} | {s['rel_signed_mean']:+.2e} ({s['rel_signed_std']:.2e}) |")
    cl = pc["emulation_variant_closer_to_evaluator"]
    md += ["", f"Closer emulation variant: **{cl['variant']}**. Evaluator on the 37 rows: paired {pc['reference_on_37_rows']['paired_rows']}/{pc['reference_on_37_rows']['rows']}, margin min {pc['reference_on_37_rows']['margin_min']:.6f}.", "",
           "## Integer vs evaluator (185 pairs)", "", "| scheme | sign agree | paired | D_q/eta min / median / max | pass 3eta | score err rel median / max (signed) | eta median | weakest pair | clips | conv acc bound | requant bound |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for scheme, s in ag["schemes"].items():
        a = s.get("vs_eval") or s["vs_fp32"]; sa = a["sign_agreement"]; de = a["D_q_over_eta"]; se = a["score_error_vs_ref"]; w = de["worst_pairs"][0]; g = s["static_bounds_global"]
        md.append(f"| {scheme} | {sa['agree']}/{sa['total']} | {a['paired_mean_of_wrong']['int_rows_correct_lower']}/{a['paired_mean_of_wrong']['rows']} | {de['min']:.2f} / {de['p50']:.2f} / {de['max']:.2f} | {de['pairs_pass_3eta']}/{a['n_pairs']} | "
                  f"{se['rel']['median']:.2e} / {se['rel']['max']:.2e} ({se['rel']['signed_mean']:+.2e}) | {a['eta_mse']['p50']:.2e} | {w['sid']} {w['row']} {w['offset']:+d} (D_q {w['D_q']:.6f}, eta {w['eta']:.2e}) | "
                  f"{sum(s['clip_events'].values())} | {g['conv_acc_bound_max']:,} | {g['conv_requant_expr_max']:,} |")
    md += ["", "## August proof rows 600-711 (rule offset, integer int16 and fp32; no evaluator)", ""]
    for scheme, a in ag.get("august", {}).items():
        dq = a["rule_D_q_mse"]; rs = a["rule_sign"]
        md += [f"- `{scheme}`: rule pairs available {a['rule_pairs_available']}/{a['n_rows']} (missing wrong-hint rows: {[u['row'] for u in a['rule_pairs_unavailable']]}); "
               f"D_q min {dq['min']:.6f}, p5 {dq['p5']:.6f}, median {dq['p50']:.6f}, max {dq['max']:.6f}; integer correct<wrong {rs['int_positive']}/{rs['n']}, fp32 {rs['fp32_positive']}/{rs['n']}; "
               f"negative integer rows {rs['negative_rows_int'] or 'none'}; all-offset pairs int c<w {a['all_offsets']['int_correct_lt_wrong']}/{a['all_offsets']['pairs']}; clips {sum(a['clip_events'].values())}"]
    calib = json.load(open(OUT / "agreement_int16.json"))["calib_rows"]
    aug_t = [r for s_, r in calib if s_ == "august"]; aug_ids = sorted({x for r in aug_t for x in (r, r + 15)})
    md += ["", "## Calibration disclosure", "",
           f"The fixed-point scales were calibrated on {len(calib)} rows x 2 conditionings (own E and E of row+15): protocol rows "
           + ", ".join(f"{s_} {r}" for s_, r in calib if s_ != "august") + f" and August targets {aug_t}, i.e. {len(aug_t)} raw August targets and "
           f"{len(aug_ids)} August conditioning identities {aug_ids}. August rows 600-711 were held out from weight training (august_train_rows 600) but were "
           "NOT untouched by calibration; they must not be described as an untouched test set. The proof set remains the complete 112 rows.", ""]
    md += ["", "## Artifact files", ""]
    for p in sorted(OUT.iterdir()):
        if p.is_file():
            md.append(f"- `{p.name}` sha256 `{hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]}...`")
    for sub in ("vectors", "august_inputs"):
        d = OUT / sub
        if d.exists():
            files = sorted(d.iterdir()); md.append(f"- `{sub}/`: {len(files)} files")
    Path(OUT / "FREEZE_SUMMARY.md").write_text("\n".join(md) + "\n")
    print(f"wrote {OUT / 'FREEZE_SUMMARY.md'}")


if __name__ == "__main__":
    main()
