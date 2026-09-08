#!/usr/bin/env python3
"""Python oracle for the August proof rows the guest is executed on: G1's int_ref.py (IntBackend, forward_program)
on the FINAL checkpoint, run on the exported inputs, with the declared two-part offset rule.

For each row r: C_int, noise_int, Ct_int and E_correct come from oracle/final/august_inputs/row_r.npz, fetched from the data layer (LARGE_FILES.md; the
normative inputs; E_correct = rint(E_bf16[r] 2^14)). The wrong hint E_wrong is the same file's `E_wrong` when G1 had
the row (rows >= 600), otherwise (a training row below 600, e.g. 598 for r = 600, 587 for r = 602) it is derived by
gen_vectors.py's torch path from the chain-log state S_u (`E_int_from_s_hex`), i.e. the Python (torch) side of the
relation's hint derivation, never the Rust side. Positive control first: d2 1328 must give 8764459045 / 22311372969.

Output: source/runs/python_oracle_rows_<stamp>.json (the runs/ directory beside tools/) with residual sums per row and condition, plus the input
hashes, so the guest's public R_correct / R_wrong can be compared number for number.
usage: python_oracle_rows.py 600 601 602 603
"""
import hashlib, json, os, sys, time
from pathlib import Path

G2 = Path(__file__).resolve().parent.parent
G1 = G2.parent / "g1_integer"
if not G1.is_dir() and (G2.parent / "oracle" / "final").is_dir():
    G1 = G2.parent / "oracle"          # published layout: the oracle ships under oracle/ (Astra r6 finding 8)
os.environ.setdefault("OMP_NUM_THREADS", "8")
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
# the FINAL checkpoint environment of g1_integer/final/run_final.sh
_CK = G1 / "ckpt/final" if (G1 / "ckpt/final").is_dir() else G2.parent / "model"   # published layout: the checkpoint ships under model/ (agent audits r1)
os.environ["G1_CKPT"] = str(_CK / "g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pt")
os.environ["G1_REF_JSON"] = str(_CK / "g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pubproto_eval.json")
os.environ["G1_RAW_DIR"] = str(_CK / "g0e_armc_b16_96x112_cd0_aug_s20260908_24k" if (G1 / "ckpt/final").is_dir() else _CK / "pubproto_raw")
os.environ["G1_OUT"] = str(G1 / "final")
sys.path.insert(0, str(G1))
sys.path.insert(0, str(G2 / "vectors_relation"))
import numpy as np  # noqa: E402
import torch  # noqa: E402
torch.set_num_threads(int(os.environ["OMP_NUM_THREADS"]))
import int_ref  # noqa: E402
from int_ref import ITensor, QuantModel, forward_program, F_CT, F_HINT  # noqa: E402

OFFSETS = [-2, 2, -15, 15, 30]
ROWS_TOTAL = 712


def rule(r):
    base = OFFSETS[(r - 600) % 5]
    if 0 <= r + base < ROWS_TOTAL:
        return base, "direct"
    return -base, "mirrored"


def h16(a):
    return hashlib.sha256(np.ascontiguousarray(a.astype("<i2")).tobytes()).hexdigest()


def chain_rows():
    import csv
    rows = {}
    with open(G2 / "vectors_relation/august/chain_log.csv") as f:
        for rec in csv.DictReader(l for l in f if not l.startswith("#")):
            rows[int(rec["t"])] = rec
    return rows


def main():
    rows = [int(x) for x in sys.argv[1:]] or [600, 601, 602, 603]
    t0 = time.time()
    qm = QuantModel("int16", verbose=True)
    B = qm.B
    out = {"checkpoint_sha256": hashlib.sha256(open(os.environ["G1_CKPT"], "rb").read()).hexdigest(), "scheme": "int16",
           "scale_map_sha256": hashlib.sha256(json.dumps(qm.scale_map, sort_keys=True).encode()).hexdigest(), "rows": {}}

    def run(Ct_int, E_int, noise_int):
        B.sat = {}
        eps = forward_program(B, ITensor(Ct_int.astype(np.int64), F_CT), ITensor(E_int.astype(np.int64), F_HINT))
        return int(B.score_int(eps, noise_int.astype(np.int64))), dict(B.sat)

    # positive control: the FINAL d2 1328 vectors
    for tag, expect in (("correct", 8764459045), ("wrong_p2", 22311372969)):
        z = np.load(G1 / f"final/vectors/vectors_int16_d2_1328_{tag}.npz")
        r_int, sat = run(z["IN:Ct_int"], z["IN:E_int"], z["IN:noise_int"])
        assert r_int == expect and not sat, (tag, r_int, expect, sat)
        print(f"positive control d2 1328 {tag}: {r_int} == {expect}, clips {sat}", flush=True)
    out["positive_control"] = {"d2_1328_correct": 8764459045, "d2_1328_wrong_p2": 22311372969, "status": "PASS"}

    chain = chain_rows()
    from gen_vectors import E_int_from_s_hex  # torch path of the relation's hint derivation (Python side)
    man = json.load(open(G1 / "final/august_inputs/manifest.json"))
    for r in rows:
        d, kind = rule(r)
        u = r + d
        z = np.load(G1 / f"final/august_inputs/row_{r:06d}.npz")
        rec = man["rows"][str(r)]
        C_int, noise_int, Ct_int, E_c = z["C_int"], z["noise_int"], z["Ct_int"], z["E_correct"]
        # the exported C_t must be the integer noising of the exported C and noise
        Ct_chk = B.noise_Ct(C_int.astype(np.int64), noise_int.astype(np.int64)).v
        assert np.array_equal(Ct_chk, Ct_int.astype(np.int64)), r
        if "E_wrong" in z.files and rec["wrong_row"] == u:
            E_w = z["E_wrong"]; e_src = f"g1 august_inputs E_wrong (row {u}, rint(E_bf16 2^14))"
        else:
            E_w, _ = E_int_from_s_hex(chain[u]["S_t_hex"]); e_src = f"gen_vectors.E_int_from_s_hex(S_{u}) torch path (row {u} not in the G1 cache)"
            bin_path = G2 / f"vectors_relation/august/row_{u:06d}_E_q14_torchpath.bin"
            if bin_path.is_file():
                assert bin_path.read_bytes() == np.ascontiguousarray(E_w.astype("<i2")).tobytes(), f"E_{u} differs from the vectors_relation file"
                e_src += " (equals vectors_relation/august/row_%06d_E_q14_torchpath.bin)" % u
        t1 = time.time()
        r_c, sat_c = run(Ct_int, E_c, noise_int)
        r_w, sat_w = run(Ct_int, E_w, noise_int)
        out["rows"][str(r)] = {"row": r, "offset": d, "offset_rule": kind, "wrong_row": u,
                               "R_correct": r_c, "R_wrong": r_w, "D": r_w - r_c, "sign_positive": r_w > r_c,
                               "clip_events_correct": sat_c, "clip_events_wrong": sat_w,
                               "inputs_sha256": {"C_int": h16(C_int), "noise_int": h16(noise_int), "Ct_int": h16(Ct_int), "E_correct": h16(E_c), "E_wrong": h16(E_w)},
                               "E_wrong_source": e_src, "g1_manifest_sha256": rec["sha256"], "elapsed_s": round(time.time() - t1, 1)}
        print(f"row {r} offset {d:+d} ({kind}) wrong {u}: R_correct {r_c} R_wrong {r_w} D {r_w - r_c} clips {sat_c} {sat_w}  E_wrong from {e_src}", flush=True)
    out["elapsed_s"] = round(time.time() - t0, 1)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    p = G2 / "runs" / f"python_oracle_rows_{stamp}.json"
    p.parent.mkdir(exist_ok=True)
    json.dump(out, open(p, "w"), indent=1)
    print("wrote", p)


if __name__ == "__main__":
    main()
