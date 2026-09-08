#!/usr/bin/env python3
"""Export a G1 vector artifact (npz + json manifest per set) to the raw little-endian layout armc-int's `loader`
reads: `<out>/<scheme>_<sid>_<row>_<tag>/index.json` + one `.bin` per array.

Handles both artifacts:
  * FINAL (g1_integer/final/vectors, authoritative): files `vectors_<scheme>_<sid>_<row>_<tag>.{npz,json}`, manifest
    key `scale_map` (the one effective map), native int8 weights in the int8 scheme, a float32 noise record
    (`IN:noise_f32`, exported as f32 with its `sha256_f32_le` checked), attention entries without `f_in`;
  * superseded step-12000 (g1_integer/vectors): files `vectors_<scheme>_<tag>.{npz,json}`, manifest key `ftab`.
The manifest is stored verbatim under `manifest`; `arrays` lists dtype, shape, file and sha256 of every exported array,
each checked against the manifest's hash where it carries one (layers, inputs, weights, multipliers, biases, GroupNorm
constants, tables, exp table).

Clipping masks (Astra r4 item 2): for every table in the manifest the mask of entries that were clipped to the admitted
domain is computed with the oracle's own `g1_integer/kernels.make_act_lut_with_mask` (kind, f_in, f_out), the table it
returns is required to equal the artifact's table byte for byte, the popcount is required to equal the manifest's
`clipped_entries` when present, and the mask is exported as `MASK:<kind>:<f_in>:<f_out>` (u8 bitset, 8192 bytes, LSB
first) with its sha256 in `arrays`. If the artifact itself carries a `MASK:` array it must agree.

usage: export_oracle.py [--src DIR] [--out DIR]     (defaults: g1_integer/final/vectors -> g2_guest/oracle_final)
"""
import argparse, hashlib, json, re, sys
from pathlib import Path
import numpy as np

G2 = Path(__file__).resolve().parent.parent
G1 = G2.parent / "g1_integer"
if not G1.is_dir() and (G2.parent / "oracle" / "final").is_dir():
    G1 = G2.parent / "oracle"          # published layout: the oracle ships under oracle/ (Astra r6 finding 8)
sys.path.insert(0, str(G1))
import kernels as K  # noqa: E402  (the oracle's kernels; make_act_lut_with_mask)
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--src", default=str(G1 / "final" / "vectors"))
ap.add_argument("--out", default=str(G2 / "oracle_final"))
args = ap.parse_args()
SRC, OUT = Path(args.src), Path(args.out)


def act_fn(kind):
    if kind == "silu":
        return lambda z: z / (1.0 + np.exp(-z))
    return lambda z: F.gelu(torch.from_numpy(np.ascontiguousarray(z))).numpy()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def export(npz_path, json_path):
    z = np.load(npz_path)
    man = json.load(open(json_path))
    name = f"{man['scheme']}_{man['sid']}_{man['row']}_{'correct' if man['conditioning_row'] == man['row'] else 'wrong_p%d' % (man['conditioning_row'] - man['row'])}"
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    arrays, checked, notes = {}, 0, []
    for key in z.files:
        a = z[key]
        if a.dtype == np.int16:
            raw, dtype = np.ascontiguousarray(a.astype("<i2")).tobytes(), "i16"
        elif a.dtype == np.int8:
            raw, dtype = np.ascontiguousarray(a.astype("i1")).tobytes(), "i8"
        elif a.dtype == np.int64:
            raw, dtype = np.ascontiguousarray(a.astype("<i8")).tobytes(), "i64"
        elif a.dtype == np.float32:
            raw, dtype = np.ascontiguousarray(a.astype("<f4")).tobytes(), "f32"
        elif a.dtype == np.bool_ or a.dtype == np.uint8:
            raw, dtype = np.ascontiguousarray(a.astype("u1")).tobytes(), "u8"
        else:
            raise SystemExit(f"unexpected dtype {a.dtype} for {key}")
        h = sha(raw)
        fname = key.replace(":", "__") + ".bin"
        (d / fname).write_bytes(raw)
        arrays[key] = {"dtype": dtype, "shape": list(a.shape), "file": fname, "sha256": h}
        ref = None
        if key.startswith("T:"):
            ref = man["layers"][key[2:]]["sha256_int16_le"]
        elif key.startswith("IN:"):
            e = man["inputs"][key[3:]]
            ref = e.get("sha256_int16_le") or e.get("sha256_f32_le")
        elif key.startswith("W:"):
            ref = man["constants"][key[2:]].get("wq_sha256_int16_le")
            if a.dtype == np.int8:
                # the FINAL manifest hashes int8 weights widened to int16 (export_vectors h16); check that form
                h16 = sha(np.ascontiguousarray(a.astype("<i2")).tobytes())
                assert ref == h16, (name, key, "int8 weights: manifest hash is the int16-widened form", ref, h16)
                arrays[key]["sha256_int16_le"] = h16
                ref = h16; h = h16
        elif key.startswith("M:"):
            ref = man["constants"][key[2:]]["M_sha256_int64_le"]
        elif key.startswith("BP:"):
            ref = man["constants"][key[3:]]["bp_sha256_int64_le"]
        elif key.startswith("GQ:"):
            ref = man["constants"][key[3:]]["gamma_q_sha256_int64_le"]
        elif key.startswith("BQ:"):
            ref = man["constants"][key[3:]]["beta_q_sha256_int64_le"]
        elif key.startswith("LUT:"):
            _, kind, fi, fo = key.split(":")
            ref = man["luts"][f"{kind}:{fi}->{fo}"]["sha256_int16_le"]
        elif key == "EXP_TABLE":
            ref = man["exp_table"]["sha256_int64_le"]
        elif key == "EXP_TABLE_CLIP_MASK":
            ref = man["exp_table"].get("mask_sha256_uint8")
        elif key.startswith("LUTMASK:"):
            _, kind, fi, fo = key.split(":")
            ref = man["luts"][f"{kind}:{fi}->{fo}"].get("mask_sha256_uint8")
        if ref is not None:
            assert ref == h, (name, key, ref, h)
            checked += 1
    # clipping masks from the oracle's own table constructor
    for lut_key, le in man["luts"].items():
        kind, rest = lut_key.split(":")
        fi, fo = (int(x) for x in rest.split("->"))
        table, mask = K.make_act_lut_with_mask(act_fn(kind), fi, fo)
        art = z[f"LUT:{kind}:{fi}:{fo}"].astype(np.int64)
        assert np.array_equal(table, art), (name, lut_key, "regenerated table differs from the artifact's")
        if "clipped_entries" in le:
            assert int(mask.sum()) == le["clipped_entries"], (name, lut_key, int(mask.sum()), le["clipped_entries"])
        bits = np.packbits(mask.astype(np.uint8), bitorder="little")
        assert bits.shape == (8192,)
        mkey = f"MASK:{kind}:{fi}:{fo}"
        # the FINAL artifact carries the oracle's own mask as LUTMASK:<kind>:<f_in>:<f_out> (uint8, 1 = clipped), hashed
        # in the manifest (mask_array / mask_sha256_uint8): it must equal the regenerated mask, and is exported verbatim
        art_key = le.get("mask_array") or f"LUTMASK:{kind}:{fi}:{fo}"
        if art_key in z.files:
            art_mask = z[art_key].astype(np.uint8).reshape(-1)
            assert art_mask.shape == (65536,), (name, art_key, art_mask.shape)
            assert np.array_equal(art_mask.astype(bool), mask), (name, art_key, "artifact mask differs from the regenerated one")
            if le.get("mask_sha256_uint8"):
                assert sha(np.ascontiguousarray(art_mask).tobytes()) == le["mask_sha256_uint8"], (name, art_key, "mask hash")
            notes.append(f"{art_key}: artifact mask present, equal to the regenerated mask, hash checked")
        elif f"MASK:{kind}:{fi}:{fo}" in z.files:
            assert np.array_equal(np.packbits(z[mkey].astype(np.uint8).reshape(-1), bitorder="little"), bits), (name, mkey, "artifact mask differs")
        raw = bits.tobytes()
        fname = mkey.replace(":", "__") + ".bin"
        (d / fname).write_bytes(raw)
        arrays[mkey] = {"dtype": "u8", "shape": [8192], "file": fname, "sha256": sha(raw), "popcount": int(mask.sum()),
                        "construction": "g1_integer/kernels.make_act_lut_with_mask(kind, f_in, f_out): entries whose rint(act(x) 2^f_out) lay outside [-32768, 32767]; bitset LSB first"}
    index = {"manifest": man, "arrays": arrays,
             "export": {"tool": "g2_guest/tools/export_oracle.py", "source_npz": str(npz_path), "source_json": str(json_path),
                        "source_sha256": {"npz": sha(open(npz_path, "rb").read()), "json": sha(open(json_path, "rb").read())},
                        "hashes_checked_against_manifest": checked, "notes": notes,
                        "scale_table_key": "scale_map" if "scale_map" in man else "ftab"}}
    json.dump(index, open(d / "index.json", "w"), indent=1)
    print(f"{name}: {len(arrays)} arrays, {checked} hashes checked, masks {len(man['luts'])}, residual_sum_int {man['residual_sum_int']}, checkpoint {man['checkpoint_sha256'][:16]}, scale table {index['export']['scale_table_key']}")
    return name, man


sets = {}
for npz_path in sorted(SRC.glob("vectors_*.npz")):
    json_path = npz_path.with_suffix(".json")
    if not json_path.is_file():
        raise SystemExit(f"missing manifest for {npz_path}")
    name, man = export(npz_path, json_path)
    sets[name] = man
# consistency across sets of one scheme: constants identical, C/noise/Ct/coord identical within a row, E differs
by_scheme = {}
for name, man in sets.items():
    by_scheme.setdefault(man["scheme"], []).append((name, man))
for scheme, items in by_scheme.items():
    a = items[0][1]
    key = "scale_map" if "scale_map" in a else "ftab"
    same = all(m["constants"] == a["constants"] and m["luts"] == a["luts"] and m["exp_table"] == a["exp_table"] and m[key] == a[key] and m["noising"] == a["noising"] for _, m in items)
    print(f"{scheme}: constants/luts/exp/{key}/noising identical across {len(items)} sets: {same}")
    assert same
    rows = {}
    for n, m in items:
        rows.setdefault((m["sid"], m["row"]), []).append(m)
    for (sid, row), ms in rows.items():
        for k in ("C_int", "noise_int", "Ct_int", "coord_int"):
            assert len({m["inputs"][k]["sha256_int16_le"] for m in ms}) == 1, (sid, row, k)
        assert len({m["inputs"]["E_int"]["sha256_int16_le"] for m in ms}) == len(ms), (sid, row, "E_int must differ between conditions")
print("exported", len(sets), "sets to", OUT)
