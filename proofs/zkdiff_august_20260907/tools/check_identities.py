#!/usr/bin/env python3
"""Cross-check every published statement against the frozen identities, the chain log, the receipts and PINS.json,
with the standard library only (no Rust, no network, no cryptographic verification of the proofs themselves).

For each row 600 to 711 it decodes public_values/row_XXXXXX_public_values.bin (tools/decode_zbdiff01.py) and requires:
  - the program identities (denoiser kind, constants, network-spec and preprocessing digests) equal source/expected_identities_august.json;
  - the session identities (id, row count, depth, S_0, S_N, authority manifest, chain-log BLAKE3, context, root) equal the same file;
  - the wrong row, offset and offset rule equal the declared offset rule computed here from the row number alone (STATEMENT.md section 7);
  - the raw-frame digest, both emission digests and both drand rounds equal the chain log's columns for rows r, u and r-1
    (source/vectors_relation/august/chain_log.csv), and equal the expected-identities row;
  - the normative noise BLAKE3, the two leaves and the expected residual sums equal the expected-identities row;
  - the statement's SHA-256, the raw proof's SHA-256 and the framed artifact's SHA-256 equal PINS.json batch.proofs[r] and the receipt;
  - R_correct, R_wrong, D, the outcome class and the clip count equal the receipt's;
  - the noise file's SHA-256 equals PINS.json noise_files[r].
What this does NOT do: verify a Groth16 proof. That needs the vendored standalone verifier or zkdiff-verify (VERIFY.md
sections 1 and 2) or the prebuilt binaries in capsule/. Exit 0 only if every check on every row passes.
usage: check_identities.py [PACKAGE_ROOT]   (default: the parent of this file's directory)"""
import csv, hashlib, io, json, os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(HERE)
sys.path.insert(0, os.path.join(P, "tools"))
import decode_zbdiff01  # noqa: E402

OFFSETS = [-2, 2, -15, 15, 30]
ROW_COUNT, ROW_START, ROW_END = 712, 600, 711

def rule(r):
    base = OFFSETS[(r - ROW_START) % 5]
    if 0 <= r + base < ROW_COUNT:
        return base, "direct", r + base
    return -base, "mirrored", r - base

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

pins = json.load(open(os.path.join(P, "PINS.json")))
exp = json.load(open(os.path.join(P, "source", "expected_identities_august.json")))
raw = open(os.path.join(P, "source", "vectors_relation", "august", "chain_log.csv"), encoding="utf-8").read().splitlines()
chain = list(csv.DictReader(io.StringIO("\n".join(raw[1:]))))          # line 1 is a comment naming the session start
assert len(chain) == ROW_COUNT, f"chain log has {len(chain)} rows"
sess, prog = exp["session"], pins["program"]
batch = (pins.get("batch") or {}).get("proofs") or {}
failures, rows_ok = [], 0
print(f"{'row':>4} {'u':>4} {'d':>4} {'rule':<8} {'R_correct':>13} {'R_wrong':>13} {'D':>13} {'class':<8} clips  round_r    round_r-1  result")
for r in range(ROW_START, ROW_END + 1):
    pad = f"{r:06d}"
    pv_path = os.path.join(P, "public_values", f"row_{pad}_public_values.bin")
    pv = open(pv_path, "rb").read()
    d = decode_zbdiff01.decode(pv)
    e = exp["rows"][str(r)]
    rec = json.load(open(os.path.join(P, "receipts", f"row_{pad}_receipt.json")))
    bad = []
    def eq(name, got, want):
        if got != want:
            bad.append(f"{name}: statement {got!r} != {want!r}")
    if d["framing_problems"]:
        bad.append(f"framing: {d['framing_problems']}")
    # program and session identities
    eq("denoiser_kind", d["denoiser_kind"], exp["denoiser_kind"])
    for k in ("constants_sha256", "spec_sha256", "preprocess_spec_sha256"):
        eq(k, d[k], exp[k])
    eq("session_id", d["session_id"], sess["session_id"]); eq("row_count", d["row_count"], sess["row_count"]); eq("tree_depth", d["tree_depth"], sess["tree_depth"])
    for k in ("s_0", "s_n", "authority_manifest_sha256", "chain_log_blake3", "context_digest", "ordered_session_root"):
        eq(k, d[k], sess[k])
    # the declared offset rule, from the row number alone
    off, kind, u = rule(r)
    eq("row", d["row"], r); eq("offset", d["offset"], off); eq("offset_rule", d["offset_rule"], kind); eq("wrong_row", d["wrong_row"], u)
    eq("expected offset", e["offset"], off); eq("expected offset_rule", e["offset_rule"], kind); eq("expected wrong_row", e["wrong_row"], u)
    # the chain log: rows r, u and r-1
    cr, cu, cp = chain[r], chain[u], chain[r - 1]
    eq("raw_blake3 (chain log row r)", d["raw_blake3"], cr["bayer_blake3_hex"])
    eq("emission_blake3_r (chain log row r)", d["emission_blake3_r"], cr["emission_live_pixel_blake3_hex"])
    eq("emission_blake3_u (chain log row u)", d["emission_blake3_u"], cu["emission_live_pixel_blake3_hex"])
    eq("own_drand_round (chain log row r)", d["own_drand_round"], int(cr["drand_round_number"]))
    eq("prev_drand_round (chain log row r-1)", d["prev_drand_round"], int(cp["drand_round_number"]))
    # the expected-identities row
    for k in ("noise_blake3", "raw_blake3", "emission_blake3_r", "emission_blake3_u", "leaf_r", "leaf_u"):
        eq(f"{k} (expected identities)", d[k], e[k])
    eq("own_drand_round (expected identities)", d["own_drand_round"], e["own_drand_round"]); eq("prev_drand_round (expected identities)", d["prev_drand_round"], e["prev_drand_round"])
    eq("R_correct (oracle table)", d["r_correct"], e["expected_residual_int16"]["correct"]); eq("R_wrong (oracle table)", d["r_wrong"], e["expected_residual_int16"]["wrong"])
    # the receipt
    for k, rk in (("r_correct", "r_correct"), ("r_wrong", "r_wrong"), ("difference", "difference"), ("outcome_class", "outcome_class"), ("clip_events", "clip_events")):
        eq(f"{k} (receipt)", d[k], rec[rk])
    pv_sha = hashlib.sha256(pv).hexdigest()
    eq("public values sha256 (receipt)", pv_sha, rec["public_values_sha256"])
    raw_sha = sha(os.path.join(P, "proofs", f"row_{pad}_groth16_proof.bin"))
    framed_sha = sha(os.path.join(P, "proofs", f"row_{pad}_groth16.bin"))
    eq("raw proof sha256 (receipt)", raw_sha, rec["proof_raw_bytes_sha256"]); eq("framed proof sha256 (receipt)", framed_sha, rec["proof_sha256"])
    if str(r) in batch:
        b = batch[str(r)]
        eq("public values sha256 (PINS batch)", pv_sha, b["public_values_sha256"]); eq("raw proof sha256 (PINS batch)", raw_sha, b["raw_sha256"])
        eq("framed proof sha256 (PINS batch)", framed_sha, b["framed_sha256"]); eq("outcome (PINS batch)", d["outcome_class"], b["outcome"])
    else:
        bad.append("PINS.json carries no batch entry for this row")
    nf = pins["noise_files"][str(r)]
    noise_path = os.path.join(P, "source", nf["file"].split("source/", 1)[-1])          # PINS paths are package-relative (source/noise_august/...)
    eq("noise file sha256 (PINS noise_files)", sha(noise_path), nf["sha256"]); eq("noise BLAKE3 (PINS noise_files)", d["noise_blake3"], nf["blake3"])
    if bad:
        failures.append((r, bad))
    else:
        rows_ok += 1
    print(f"{d['row']:>4} {d['wrong_row']:>4} {d['offset']:>+4} {d['offset_rule']:<8} {d['r_correct']:>13} {d['r_wrong']:>13} {d['difference']:>+13} {d['outcome_class']:<8} {d['clip_events']:>5}  {d['own_drand_round']}  {d['prev_drand_round']}  {'OK' if not bad else 'MISMATCH'}")
    for m in bad:
        print(f"      {m}")
same_round = sum(1 for r in range(ROW_START, ROW_END + 1) if chain[r]["drand_round_number"] == chain[r - 1]["drand_round_number"])
print(f"\n{rows_ok}/{ROW_END - ROW_START + 1} statements agree with the frozen identities, the chain log, the receipts and PINS.json on every field checked here;"
      f" {same_round} of them carry the same drand round for rows r and r-1 (the chain log's rounds are non-decreasing: {all(int(chain[i]['drand_round_number']) >= int(chain[i-1]['drand_round_number']) for i in range(1, ROW_COUNT))}).")
print("This check does not verify a Groth16 proof; VERIFY.md sections 1, 2 and 2a do.")
sys.exit(1 if failures else 0)
