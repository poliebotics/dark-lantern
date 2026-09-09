#!/usr/bin/env python3
"""summarize.py (BOSUN, 2026-09-09): markdown tables from the pulled eval JSONs (one per arm) for REPORT.md.
Usage: summarize.py --results DIR [--arms a,b,c]  -> prints markdown; also writes SUMMARY.json beside the results."""
import argparse, glob, json, os


def f3(x):
    return "n/a" if x is None else (f"{x:.4f}" if abs(x - round(x, 2)) > 5e-5 else f"{x:.3f}")


def ci(c):
    return "n/a" if not c else f"[{c[0]:.3f}, {c[1]:.3f}]"


def short(sid):
    return sid[9:] if sid.startswith("20241219_") else sid


def arm_tables(name, res):
    out = [f"### {name}\n", f"Checkpoint step {res['checkpoint_step']}, sha256 `{res['checkpoint_sha256'][:16]}...`, {res['conditioning']}, params {res['arch']['params']:,}; "
           f"trained on `{res['train_args'].get('sessions')}` (august rows < {res['train_args'].get('august_train_rows')}), seed {res['train_args'].get('seed')}, {res['train_args'].get('max_steps')} steps.\n"]
    out.append("| session | era | rows | AUROC (correct vs wrong-mean) | 95% CI (row bootstrap) | paired fraction | 95% CI | delta wrong-correct (relative) | single-wrong AUROC (mod-5 mirrored) | pairing check AUROC shift -1 / +1 |")
    out.append("|---|---|---:|---:|---|---:|---|---:|---:|---|")
    order = [s for s in ("d2", "v10", "august") if s in res["sessions"]] + sorted(s for s, c in res["sessions"].items() if c["era"] == "2024") + sorted(s for s, c in res["sessions"].items() if c["era"] == "2023")
    for sid in order:
        c = res["sessions"][sid]; rb = c["row_bootstrap"]; sw = c.get("secondary_single_wrong_mod5_mirrored") or {}; pc = c.get("pairing_check") or {}
        pcs = f"{pc['shift_-1']['auroc_correct_vs_shift']:.3f} / {pc['shift_+1']['auroc_correct_vs_shift']:.3f}" if pc else "n/a"
        out.append(f"| {short(sid)} | {c['era']} | {c['n_rows']} | {c['auroc']['correct_vs_wrong_avg']:.4f} | {ci(rb['auroc_ci95'])} | {c['paired_fraction_correct_lower']:.3f} | {ci(rb['paired_ci95'])} | "
                   f"{c['delta_wrong_mean']['mean']:.2e} ({100*c['delta_wrong_mean']['relative']:+.1f}%) | {f3(sw.get('auroc'))} | {pcs} |")
    out.append("")
    out.append("| era pool | sessions | rows | AUROC | 95% CI rows | 95% CI sessions (cluster) | paired | 95% CI | mean correct | mean wrong |")
    out.append("|---|---|---:|---:|---|---|---:|---|---:|---:|")
    for e in ("2026", "2024", "2023"):
        d = res["eras"].get(e)
        if not d: continue
        out.append(f"| {e} | {len(d['sessions'])} | {d['n_rows']} | {d['auroc']:.4f} | {ci(d['auroc_ci95_row_bootstrap'])} | {ci(d.get('auroc_ci95_session_cluster_bootstrap'))} | {d['paired']:.3f} | {ci(d['paired_ci95_row_bootstrap'])} | {d['mean_correct']:.4f} | {d['mean_wrong']:.4f} |")
    out.append("")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--results", required=True); ap.add_argument("--arms", default="")
    a = ap.parse_args()
    arms = a.arms.split(",") if a.arms else sorted(os.path.basename(f)[:-10] for f in glob.glob(os.path.join(a.results, "*.eval.json")))
    lines = []; summary = {}
    for name in arms:
        p = os.path.join(a.results, f"{name}.eval.json")
        if not os.path.isfile(p): lines.append(f"### {name}\n\n(no eval json)\n"); continue
        res = json.load(open(p)); lines += arm_tables(name, res)
        summary[name] = {"step": res["checkpoint_step"], "sha256": res["checkpoint_sha256"],
                         "sessions": {s: {"era": c["era"], "n": c["n_rows"], "auroc": c["auroc"]["correct_vs_wrong_avg"], "auroc_ci": c["row_bootstrap"]["auroc_ci95"],
                                          "paired": c["paired_fraction_correct_lower"], "delta": c["delta_wrong_mean"]["mean"], "delta_rel": c["delta_wrong_mean"]["relative"]} for s, c in res["sessions"].items()},
                         "eras": {e: {"n": d["n_rows"], "auroc": d["auroc"], "auroc_ci_rows": d["auroc_ci95_row_bootstrap"], "auroc_ci_cluster": d.get("auroc_ci95_session_cluster_bootstrap"), "paired": d["paired"]} for e, d in res["eras"].items()}}
    pp = os.path.join(a.results, "..", "pubproto_check.md")
    json.dump(summary, open(os.path.join(a.results, "SUMMARY.json"), "w"), indent=1)
    print("\n".join(lines))
