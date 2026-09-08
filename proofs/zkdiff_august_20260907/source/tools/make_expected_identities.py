#!/usr/bin/env python3
"""Freeze the expected identities the acceptance verifier (zkdiff-verify, zkdiff-ceremony verify, zkdiff-batch prove)
enforces on every ZBDIFF01 statement of the August proof set (Astra r5 finding 3): the pinned program vkey and guest
ELF, the circuit verifier key, the constants / spec / preprocessing digests, the session identities, the declared offset rule and,
per row 600..711, the normative noise BLAKE3 (G1 FINAL august_inputs/manifest.json `noise_map`), the chain log's raw
BLAKE3, emission digests and drand rounds of r and u, the leaves (from the prepare manifest) and G1's expected int16
residual sums (the oracle comparison).

Sources, each hashed into the output so the record says what it was built from:
  --build-record   armc-relation/runs/build_record_<stamp>.txt of the asserting build (guest_elf_sha256, sp1_vkey,
                   embedded_groth16_vk_sha256, sp1_circuit_version)
  G1 manifest      ../g1_integer/final/august_inputs/manifest.json (noise_map, rows[r].expected_residual_sum_int, rule)
  chain log        vectors_relation/august/chain_log.csv (BLAKE3 must be 754e5716...)
  prepare manifest armc-relation/runs/batch_prepare_g2d_20260907/BATCH_MANIFEST.json (leaf_r, leaf_u per row; session)
  blob             blobs/final_int16/constants_int16.blob (constants_sha256)
  spec digests     adapter/src/lib.rs ARMC_INT_SPEC_SHA256_HEX and relation/src/spec.rs PREPROCESS_SPEC_SHA256_HEX
  session constants  script/src/session.rs SessionProfile::august (s_0, s_n, authority manifest, chain log BLAKE3, root)

usage: make_expected_identities.py --build-record PATH [--out expected_identities_august.json]
"""
import argparse, csv, hashlib, json, re, sys
from pathlib import Path

try:
    import blake3  # python package; falls back to the b3sum binary
except Exception:  # noqa: BLE001
    blake3 = None

G2 = Path(__file__).resolve().parent.parent
OFFSETS = [-2, 2, -15, 15, 30]
ROW_START, ROW_END, ROW_COUNT = 600, 711, 712


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def blake3_hex(data: bytes) -> str:
    if blake3 is not None:
        return blake3.blake3(data).hexdigest()
    import subprocess, tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(data)
    out = subprocess.run(["b3sum", "--no-names", f.name], check=True, capture_output=True, text=True).stdout.strip()
    Path(f.name).unlink()
    return out


def assignment(r):
    base = OFFSETS[(r - ROW_START) % 5]
    if 0 <= r + base < ROW_COUNT:
        return base, "direct", r + base
    return -base, "mirrored", r - base


def const_from(path, name):
    m = re.search(rf'{name}: &str = "([0-9a-f]{{64}})"', Path(path).read_text())
    if not m:
        sys.exit(f"cannot find {name} in {path}")
    return m.group(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-record", required=True)
    ap.add_argument("--out", default=str(G2 / "expected_identities_august.json"))
    ap.add_argument("--prepare-manifest", default=str(G2 / "armc-relation/runs/batch_prepare_g2d_20260907/BATCH_MANIFEST.json"))
    a = ap.parse_args()

    rec = Path(a.build_record).read_text()
    def rec_field(key):
        m = re.search(rf"{key}=(\S+)", rec)
        if not m:
            sys.exit(f"build record lacks {key}")
        return m.group(1)
    if "BUILD_REPRODUCED_OK" not in rec:
        sys.exit("the build record is not an asserting BUILD_REPRODUCED_OK record")
    elf_sha, elf_bytes, vkey = rec_field("guest_elf_sha256"), int(rec_field("guest_elf_bytes")), rec_field("sp1_vkey")
    groth16_vk_sha, circuit_version = rec_field("embedded_groth16_vk_sha256"), rec_field("sp1_circuit_version")

    g1_path = (G2.parent / "g1_integer" if (G2.parent / "g1_integer").is_dir() else G2.parent / "oracle") / "final/august_inputs/manifest.json"   # published layout (Astra r6 finding 8)
    g1 = json.loads(g1_path.read_text())
    noise_map = {row[0]: dict(zip(g1["noise_map"]["columns"], row)) for row in g1["noise_map"]["rows"]}
    assert len(noise_map) == 112, len(noise_map)

    chain_path = G2 / "vectors_relation/august/chain_log.csv"
    chain_bytes = chain_path.read_bytes()
    chain_blake3 = blake3_hex(chain_bytes)
    assert chain_blake3 == "754e5716e65a065e5ad3146131609a1fd12e8310d966fb6bf2d3de6c568e7f8b", chain_blake3
    rows = {}
    with open(chain_path) as f:
        for rec_ in csv.DictReader(l for l in f if not l.startswith("#")):
            rows[int(rec_["t"])] = rec_
    assert len(rows) == ROW_COUNT

    prep = json.loads(Path(a.prepare_manifest).read_text())
    prep_rows = {e["row"]: e for e in prep["rows"]}
    session = prep["session"]
    assert session["row_count"] == ROW_COUNT and session["chain_log_blake3"] == chain_blake3

    blob_path = G2 / "blobs/final_int16/constants_int16.blob"
    constants_sha = sha256_file(blob_path)
    spec_sha = const_from(G2 / "armc-relation/adapter/src/lib.rs", "ARMC_INT_SPEC_SHA256_HEX")
    pre_sha = const_from(G2 / "armc-relation/relation/src/spec.rs", "PREPROCESS_SPEC_SHA256_HEX")
    # the August session constants of script/src/session.rs SessionProfile::august (proved native oracle)
    sess_src = (G2 / "armc-relation/script/src/session.rs").read_text()
    def sess(name):
        m = re.search(rf'{name}: (?:Some\()?unhex32\("([0-9a-f]{{64}})"\)', sess_src)
        if not m:
            sys.exit(f"cannot find {name} in session.rs")
        return m.group(1)
    s_0, s_n, authority, expected_root = sess("s_0"), sess("s_n"), sess("authority_manifest_sha256"), sess("expected_root")
    assert expected_root == session["ordered_session_root"], (expected_root, session["ordered_session_root"])

    table = {}
    mirrored = []
    for r in range(ROW_START, ROW_END + 1):
        d, kind, u = assignment(r)
        g1r = g1["rows"][str(r)]
        assert g1r["rule_offset"] == d and g1r["wrong_row"] == u, (r, g1r["rule_offset"], d)
        nm = noise_map[r]
        assert nm["blake3"] == g1r["noise_int_blake3"] and nm["sha256"] == g1r["sha256"]["noise_int"]
        # the exported noise file must be the normative bytes
        nf = G2 / "noise_august" / f"noise_{r:06d}.i16"
        nb = nf.read_bytes()
        assert hashlib.sha256(nb).hexdigest() == nm["sha256"], r
        assert blake3_hex(nb) == nm["blake3"], r
        if kind == "mirrored":
            mirrored.append(r)
        pr = prep_rows.get(r, {})
        if pr:
            assert pr["offset"] == d and pr["wrong_row"] == u and pr["offset_rule"] == kind, (r, pr["offset"], pr["offset_rule"])
        er = g1r["expected_residual_sum_int"]["int16"]
        wrong_key = [k for k in er if k.startswith("wrong")]
        assert wrong_key == [f"wrong_{d:+d}".replace("+", "+") if d > 0 else f"wrong_{d}"] or len(wrong_key) == 1, (r, wrong_key)
        table[str(r)] = {
            "offset": d, "offset_rule": kind, "wrong_row": u,
            "noise_file": f"noise_august/noise_{r:06d}.i16", "noise_blake3": nm["blake3"], "noise_sha256": nm["sha256"], "noise_call_index": nm["call_index"],
            "raw_blake3": rows[r]["bayer_blake3_hex"],
            "emission_blake3_r": rows[r]["emission_live_pixel_blake3_hex"], "emission_blake3_u": rows[u]["emission_live_pixel_blake3_hex"],
            "own_drand_round": int(rows[r]["drand_round_number"]), "prev_drand_round": int(rows[r - 1]["drand_round_number"]),
            "leaf_r": pr.get("leaf_r"), "leaf_u": pr.get("leaf_u"),
            "expected_residual_int16": {"correct": er["correct"], "wrong": er[wrong_key[0]], "source": f"g1_integer/final/august_inputs/manifest.json rows[{r}].expected_residual_sum_int.int16.{wrong_key[0]}"},
        }
    assert mirrored == [684, 689, 694, 698, 699, 703, 704, 708, 709, 711], mirrored

    out = {
        "schema": "zbdiff-expected-identities/v1",
        "what": "frozen expected identities for the August proof set (rows 600..711): the acceptance verifier fails closed on any mismatch",
        "sp1_vkey": vkey, "guest_elf_sha256": elf_sha, "guest_elf_bytes": elf_bytes,
        "sp1_circuit_version": circuit_version, "groth16_vk_sha256": groth16_vk_sha,
        "denoiser_kind": 1, "constants_sha256": constants_sha, "constants_blob": "blobs/final_int16/constants_int16.blob",
        "spec_sha256": spec_sha, "preprocess_spec_sha256": pre_sha,
        "session": {
            "name": session["name"], "session_id": session["session_id"], "row_count": ROW_COUNT, "tree_depth": 10,
            "s_0": s_0, "s_n": s_n, "authority_manifest_sha256": authority, "chain_log_blake3": chain_blake3,
            "context_digest": session["context_digest"], "ordered_session_root": session["ordered_session_root"],
        },
        "rule": {
            "row_start": ROW_START, "row_end_inclusive": ROW_END, "offsets": OFFSETS, "mirrored_rows": mirrored,
            "text": prep["rule"]["text"],
        },
        "noising": {"timestep": 150, "SA": 63540, "SO": 16053, "shift": 16, "F_CT": 12, "F_HINT": 14, "F_EPS": 12, "denominator": 721554505728},
        "sources": {
            "build_record": {"path": str(Path(a.build_record).resolve()), "sha256": sha256_file(a.build_record)},
            "g1_manifest": {"path": str(g1_path), "sha256": sha256_file(g1_path), "checkpoint_sha256": g1["checkpoint_sha256"]},
            "chain_log": {"path": str(chain_path), "blake3": chain_blake3, "sha256": hashlib.sha256(chain_bytes).hexdigest()},
            "prepare_manifest": {"path": str(Path(a.prepare_manifest).resolve()), "sha256": sha256_file(a.prepare_manifest)},
            "constants_blob": {"path": str(blob_path), "sha256": constants_sha, "bytes": blob_path.stat().st_size},
            "noise_dir": {"path": str(G2 / "noise_august"), "files_checked": 112},
        },
        "rows": table,
    }
    text = json.dumps(out, indent=1, sort_keys=False) + "\n"
    Path(a.out).write_text(text)
    print(f"wrote {a.out} sha256 {hashlib.sha256(text.encode()).hexdigest()}: vkey {vkey} elf {elf_sha[:16]}... {elf_bytes} B, {len(table)} rows, mirrored {mirrored}")


if __name__ == "__main__":
    main()
