#!/usr/bin/env python3
"""Guest-ready integer inputs for the August proof set (rows 600-711, one proof each).

Rule (coordinator, 2026-09-07): wrong offset = [-2, +2, -15, +15, +30][(r - 600) mod 5].

Normative noise derivation for August (no frozen evaluator ran on August):
    noise_f32[r] = randn_cuda_emul(seed=20260823, call_index=r-600)      (common.py)
  i.e. Philox4x32-10 with key (20260823, 0), counter (r-600, 0, element_index, 0), Box-Muller
  lane x = sqrt(-2 ln u) sin(v) in float32; then noise_int = rint(noise_f32 * 2^12) (ties to even),
  clamped to int16.  The exported noise_int bytes are the normative target and noising input.

Per row r the npz holds (all int16 little-endian unless stated):
  C_int        rint(C_bf16 * 2^12)            (4,96,112)   the cached fp16 frame reduction, bf16-rounded as the evaluator does
  noise_int    normative target, Q12          (4,96,112)
  noise_f32    the float32 stream it came from (4,96,112) float32, informative
  Ct_int       clamp16((SA*C_int + SO*noise_int + 2^15) >> 16), SA=63540, SO=16053   (4,96,112)
  E_correct    rint(E_bf16[r] * 2^14)         (12,96,112)
  E_wrong      rint(E_bf16[r + offset] * 2^14) (12,96,112)  absent when that row is not on this box
  coord_int    rint(coord_grid * 2^14)        (2,96,112)   shared hint channels 12-13
Output: $G1_OUT/august_inputs/row_NNNNNN.npz + manifest.json (sha256 of every array's bytes).
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import blake3
import numpy as np
import torch
from common import CKPT, EVAL_SEED, OFFSETS, OUT, TH, TW, august_rows, env_summary, import_trainer, load_C_bf16, load_E_bf16, protocol_noise, protocol_row_index, row_available, rule_pair
from int_ref import DOMAIN, F_CT, F_EPS, F_HINT, NOISE_P, ROUNDING, IntBackend, coord_grid_f64


NOISE_RULE = ("NORMATIVE August noise. For row r in 600..711 the noise tensor is randn_cuda_emul(seed=20260823, call_index=r-600) "
              "(common.py): Philox4x32-10 (Random123/cuRAND constants M0=0xD2511F53, M1=0xCD9E8D57, W0=0x9E3779B9, W1=0xBB67AE85, 10 rounds) "
              "with key (20260823, 0) and, for element e in 0..43007 of the flattened (4,96,112) tensor, counter (r-600, 0, e, 0); of the four output "
              "words (x, y, z, w) the sample is Box-Muller lane x in float32: u = x*2^-32 + 2^-33, v = y*(2^-32*2pi) + 2^-33*2pi, "
              "sample = sqrt(-2 ln u) * sin(v) (numpy float32 log/sin); noise_int = rint(sample * 2^12) with ties to even, clamped to int16. "
              "The guest takes noise_int as its witness item `noise` (86,016 bytes, int16 LE Q12, 4x96x112) and publishes BLAKE3(noise) in the public "
              "output (RELATION.md section 1.1, offset 660); it derives C_t = clamp16((63540*C_int + 16053*noise_int + 2^15) >> 16) in-circuit from the "
              "committed frame's reduction and that noise (noise.rs), so C_t is not supplied and no C_t hash is published; the constants blob is bound by "
              "SHA-256 (offset 564). The exported Ct_int is the oracle's expected value of that derivation. The float32 stream (noise_f32) is reference only.")


def h(a, dt):
    return hashlib.sha256(np.ascontiguousarray(a.astype(dt)).tobytes()).hexdigest()


def main():
    outdir = OUT / "august_inputs"; outdir.mkdir(parents=True, exist_ok=True)
    M = import_trainer(); dc = M.build_diffusion_constants(1000, torch.device("cpu"), torch.float32)
    B = IntBackend({"conv": {}, "gn": {}}, {}, "int16"); B.set_noising_constants(dc)
    coord = B.hint_coord
    np.save(outdir / "coord_int.npy", coord.astype(np.int16))
    # expected residual sums from the agreement runs, when present
    expected = {}
    for scheme in ("int16", "int8"):
        p = OUT / f"agreement_{scheme}_august.json"
        if p.exists():
            for x in json.load(open(p))["rows"]:
                expected.setdefault(x["row"], {})[scheme] = {k: v["R_int"] for k, v in x["conds"].items()}
    rows = {}
    clip_total = {}
    for sid, r in august_rows():
        o, rw, rule_kind, nominal = rule_pair(r)
        noise = protocol_noise(sid, r)
        B.sat = {}
        inp = B.int_inputs(load_C_bf16(sid, r), noise, load_E_bf16(sid, r))
        arrays = {"C_int": inp["C_int"].astype(np.int16), "noise_int": inp["noise_int"].astype(np.int16),
                  "noise_f32": noise.numpy().reshape(4, TH, TW).astype(np.float32), "Ct_int": inp["Ct"].v.astype(np.int16),
                  "E_correct": inp["E_int"].astype(np.int16)}
        wrong_available = row_available(sid, rw)
        if wrong_available:
            arrays["E_wrong"] = B.quant_E(load_E_bf16(sid, rw)).astype(np.int16)
        np.savez_compressed(outdir / f"row_{r:06d}.npz", **arrays)
        for k, v in B.sat.items():
            clip_total[k] = clip_total.get(k, 0) + v
        noise_bytes = np.ascontiguousarray(arrays["noise_int"].astype("<i2")).tobytes()
        assert len(noise_bytes) == 86016
        rec = {"row": r, "noise_call_index": protocol_row_index(sid, r), "nominal_offset": nominal, "rule_offset": o, "offset_rule": rule_kind,
               "wrong_row": rw, "wrong_available": wrong_available, "file": f"row_{r:06d}.npz", "clip_events": dict(B.sat),
               "noise_int_blake3": blake3.blake3(noise_bytes).hexdigest(),
               "sha256": {k: (h(v, "<f4") if k == "noise_f32" else h(v, "<i2")) for k, v in arrays.items()}}
        if r in expected:
            rec["expected_residual_sum_int"] = {sch: {"correct": d.get("correct"), f"wrong_{o:+d}": d.get(f"wrong_{o:+d}")} for sch, d in expected[r].items()}
        rows[str(r)] = rec
    manifest = {"artifact": "G1 FINAL August proof-set inputs", "checkpoint": str(CKPT), "checkpoint_sha256": hashlib.sha256(open(CKPT, "rb").read()).hexdigest(),
                "env": env_summary(), "rule": "nominal wrong offset = [-2,+2,-15,+15,+30][(r-600) mod 5]; boundary clause: if r+offset >= 712 use -offset (offset_rule = mirrored); one proof per row 600..711",
                "mirrored_rows": [int(k) for k, v in rows.items() if v["offset_rule"] == "mirrored"], "normative_noise_rule": NOISE_RULE,
                "noise_derivation": {"normative": "noise_int bytes in each row file", "construction": "randn_cuda_emul(seed=20260823, call_index=r-600): Philox4x32-10 key (20260823,0), counter (r-600, 0, element_index, 0), Box-Muller lane x in float32; noise_int = rint(noise_f32 * 2^12) ties-to-even, clamp int16",
                                     "seed": EVAL_SEED, "call_index": "r - 600", "cuda_correspondence": "approximate (Philox words exact; float32 transform uses libm log/sin)"},
                "fixed_point": {"F_CT": F_CT, "F_HINT": F_HINT, "F_EPS": F_EPS, "NOISE_P": NOISE_P, "SA_INT": B.SA_INT, "SO_INT": B.SO_INT},
                "rounding": ROUNDING, "domain": DOMAIN, "coord_int": {"file": "coord_int.npy", "shape": [2, TH, TW], "f": F_HINT, "sha256_int16_le": h(coord, "<i2")},
                "hint_layout": "hint = concat(E (12 ch, f=14), coord_int (2 ch: x then y, f=14)) -> 14 channels",
                "noise_map": {"columns": ["row", "file", "npz_key", "call_index", "bytes", "blake3", "sha256"],
                              "note": "normative per-row noise: BLAKE3 over the 86,016 little-endian int16 bytes of noise_int (witness item `noise`, public offset 660 in ZBDIFF01); sha256 is the file-integrity hash of the same bytes",
                              "rows": [[v["row"], v["file"], "noise_int", v["noise_call_index"], 86016, v["noise_int_blake3"], v["sha256"]["noise_int"]] for v in rows.values()]},
                "clip_events_total": clip_total, "rows": rows}
    json.dump(manifest, open(outdir / "manifest.json", "w"), indent=1)
    n_un = sum(1 for v in rows.values() if not v["wrong_available"])
    print(f"wrote {len(rows)} row files to {outdir} ({n_un} rows without a local wrong hint: {[v['row'] for v in rows.values() if not v['wrong_available']]}); clip events {clip_total}")


if __name__ == "__main__":
    main()
