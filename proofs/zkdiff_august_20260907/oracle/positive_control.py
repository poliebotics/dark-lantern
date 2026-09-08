#!/usr/bin/env python3
"""Positive control against the frozen evaluator's per-row raw scores.

Reference: $G1_RAW_DIR/pubproto_raw.npz_{d2,v10}.npz, written by lean_pubproto_eval.py:154-155 on
the A100 (bf16 autocast): arrays `rows`, `block_lengths`, `correct`, `wrong_-2`, `wrong_+2`,
`wrong_-15`, `wrong_+15`, `wrong_+30`, one entry per eval row in the evaluator's row order.

Ours: $G1_OUT/float_repro.json, the fp32 and the two bf16-autocast-emulation variants of the
protocol scores for the 37 rows, computed with the same session noise stream (one CUDA-Philox
generator per session seeded 20260823, each row at its own stream position; common.protocol_noise).

Writes $G1_OUT/positive_control.json (every (row, condition) triple with deviations, max and median
absolute and relative deviation per session and per offset, and which emulation variant is closer)
and fills the per-row `reference` and `abs_diff_*` fields of float_repro.json.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from common import OFFSETS, OUT, RAW_DIR, protocol_row_index

CONDS = ["correct"] + [f"wrong_{o:+d}" for o in OFFSETS]
VARIANTS = ("fp32", "bf16em", "bf16em_v2")


def load_reference():
    ref = {}
    for sid in ("d2", "v10"):
        p = RAW_DIR / f"pubproto_raw.npz_{sid}.npz"
        z = np.load(p)
        rows = [int(r) for r in z["rows"]]
        ref[sid] = {"index": {r: i for i, r in enumerate(rows)}, "arrays": {c: z[c] for c in CONDS},
                    "n": len(rows), "blocks": [int(b) for b in z["block_lengths"]], "path": str(p)}
    return ref


def reference_score(ref, sid, r, cond):
    i = ref[sid]["index"][r]
    assert i == protocol_row_index(sid, r), (sid, r, i)      # the evaluator's row order = our stream position
    return float(ref[sid]["arrays"][cond][i])


def agg(sub):
    out = {}
    for var in VARIANTS:
        a = np.array([s[f"{var}_abs"] for s in sub]); rl = np.array([s[f"{var}_rel"] for s in sub])
        out[var] = {"n": len(sub), "abs_max": float(a.max()), "abs_median": float(np.median(a)),
                    "rel_max": float(np.abs(rl).max()), "rel_median": float(np.median(np.abs(rl))),
                    "rel_signed_mean": float(rl.mean()), "rel_signed_std": float(rl.std())}
    return out


def main():
    fr_path = OUT / "float_repro.json"
    fr = json.load(open(fr_path))
    ref = load_reference()
    recs = []
    for x in fr["rows"]:
        sid, r = x["sid"], x["row"]
        for cond, v in x["pubproto"].items():
            R = reference_score(ref, sid, r, cond)
            v["reference"] = R
            for var in VARIANTS:
                v[f"abs_diff_{var}"] = abs(v[var] - R)
            rec = {"sid": sid, "row": r, "stream_index": x["protocol_noise_index"], "cond": cond,
                   "offset": 0 if cond == "correct" else int(cond.split("_")[1]), "ref": R}
            for var in VARIANTS:
                rec[var] = v[var]; rec[f"{var}_abs"] = abs(v[var] - R); rec[f"{var}_rel"] = (v[var] - R) / R
            recs.append(rec)
    summary = {"overall": agg(recs),
               "by_session": {sid: agg([s for s in recs if s["sid"] == sid]) for sid in ("d2", "v10")},
               "by_offset": {("correct" if o == 0 else f"{o:+d}"): agg([s for s in recs if s["offset"] == o]) for o in [0] + OFFSETS},
               "by_session_and_offset": {f"{sid}/{'correct' if o == 0 else f'{o:+d}'}": agg([s for s in recs if s["sid"] == sid and s["offset"] == o])
                                         for sid in ("d2", "v10") for o in [0] + OFFSETS}}
    ref_rows = {}
    for x in fr["rows"]:
        sid, r = x["sid"], x["row"]
        c = reference_score(ref, sid, r, "correct")
        w = [reference_score(ref, sid, r, k) for k in CONDS[1:] if k in x["pubproto"]]
        ref_rows[f"{sid}/{r}"] = {"correct": c, "wrong": w, "paired": bool(c < np.mean(w)), "margin": float(np.mean(w) - c)}
    ov = summary["overall"]
    closer = min(("bf16em", "bf16em_v2"), key=lambda v: ov[v]["rel_median"])
    out = {"reference_files": {sid: ref[sid]["path"] for sid in ref}, "reference_rows_per_session": {sid: ref[sid]["n"] for sid in ref},
           "reference_block_lengths": {sid: ref[sid]["blocks"] for sid in ref}, "ours": str(fr_path), "checkpoint_sha256": fr["checkpoint_sha256"],
           "noise_rule": fr["noise_rule"], "variants": fr["variants"],
           "emulation_variant_closer_to_evaluator": {"variant": closer, "rel_median": {v: ov[v]["rel_median"] for v in ("bf16em", "bf16em_v2")},
                                                     "rel_signed_mean": {v: ov[v]["rel_signed_mean"] for v in ("bf16em", "bf16em_v2")},
                                                     "rel_signed_std": {v: ov[v]["rel_signed_std"] for v in ("bf16em", "bf16em_v2")}},
           "summary": summary,
           "reference_on_37_rows": {"paired_rows": int(sum(v["paired"] for v in ref_rows.values())), "rows": len(ref_rows),
                                    "margin_min": float(min(v["margin"] for v in ref_rows.values())),
                                    "margin_median": float(np.median([v["margin"] for v in ref_rows.values()]))},
           "records": recs}
    json.dump(out, open(OUT / "positive_control.json", "w"), indent=1)
    fr["reference_per_row_raw_scores"] = {"available_locally": True, "local_paths": {sid: ref[sid]["path"] for sid in ref},
                                          "note": "per-row reference filled by positive_control.py; comparison summary in positive_control.json"}
    json.dump(fr, open(fr_path, "w"), indent=1)
    print(f"{'scope':16s} {'var':10s} {'n':>4s} {'abs max':>10s} {'abs median':>10s} {'rel max':>9s} {'rel median':>10s} {'signed mean':>11s} {'std':>9s}")
    for scope, d in [("overall", summary["overall"])] + [(f"session {k}", v) for k, v in summary["by_session"].items()] + [(f"offset {k}", v) for k, v in summary["by_offset"].items()]:
        for var in VARIANTS:
            s = d[var]
            print(f"{scope:16s} {var:10s} {s['n']:4d} {s['abs_max']:10.2e} {s['abs_median']:10.2e} {s['rel_max']:9.2e} {s['rel_median']:10.2e} {s['rel_signed_mean']:+11.2e} {s['rel_signed_std']:9.2e}")
    r37 = out["reference_on_37_rows"]
    print(f"reference on the 37 rows: paired {r37['paired_rows']}/{r37['rows']}, margin min {r37['margin_min']:.6f} median {r37['margin_median']:.6f}")
    print(f"emulation variant closer to the evaluator: {closer}  {out['emulation_variant_closer_to_evaluator']}")
    print(f"wrote {OUT/'positive_control.json'} and filled {fr_path} reference fields")


if __name__ == "__main__":
    main()
