#!/usr/bin/env python3
"""Decode a ZBDIFF01 public statement (752 bytes) into named fields. Standard library only.

usage: decode_zbdiff01.py FILE          FILE holds the 752 raw bytes (row_XXXXXX_public_values.bin) or their hex (.hex)
       decode_zbdiff01.py --hex HEXSTRING

Layout (source/armc-relation/RELATION.md section 1.1 as amended by FULL_GUEST.md section 2.2): little-endian unless stated.
Exit status 0 when the fixed fields parse (magic, ABI, protocol, length, fixed noising constants, D = R_wrong - R_correct,
sign byte consistent, clip flag consistent); 1 otherwise. The decoder checks framing only; acceptance against the frozen
identities is zkdiff-verify's job (VERIFY.md).
"""
import json, struct, sys

def decode(b: bytes) -> dict:
    if len(b) != 752:
        raise ValueError(f"expected 752 bytes, got {len(b)}")
    u32 = lambda o: struct.unpack_from("<I", b, o)[0]
    i32 = lambda o: struct.unpack_from("<i", b, o)[0]
    u64 = lambda o: struct.unpack_from("<Q", b, o)[0]
    i64 = lambda o: struct.unpack_from("<q", b, o)[0]
    u16 = lambda o: struct.unpack_from("<H", b, o)[0]
    hx = lambda o, n: b[o:o + n].hex()
    problems = []
    magic = b[0:8]
    if magic != b"ZBDIFF01": problems.append(f"magic {magic!r}")
    if b[8] != 1: problems.append(f"ABI {b[8]}")
    if b[9] != 9: problems.append(f"protocol {b[9]}")
    if u32(12) != 752: problems.append(f"public length {u32(12)}")
    sid_len = u16(34)
    sid = b[36:36 + sid_len].decode("ascii", "replace")
    if any(b[36 + sid_len:164]): problems.append("session id padding not zero")
    r, u, d, n = u32(16), u32(20), i32(24), u32(28)
    if u != (r + d) & 0xFFFFFFFF: problems.append(f"u {u} != r + d {r + d}")
    rc, rw, D, den = u64(716), u64(724), i64(732), u64(740)
    if D != rw - rc: problems.append(f"D {D} != R_wrong - R_correct {rw - rc}")
    if den != 721554505728: problems.append(f"denominator {den}")
    sign = b[748]
    if sign != (1 if D > 0 else 0): problems.append(f"sign byte {sign} inconsistent with D {D}")
    clip_flag, clip_events = b[749], u16(750)
    if clip_flag != (1 if clip_events else 0): problems.append(f"clip flag {clip_flag} inconsistent with count {clip_events}")
    fixed = dict(timestep=u32(692), SA=u64(696), SO=u64(704), shift=b[712], F_CT=b[713], F_HINT=b[714], F_EPS=b[715])
    exp = dict(timestep=150, SA=63540, SO=16053, shift=16, F_CT=12, F_HINT=14, F_EPS=12)
    for k, v in exp.items():
        if fixed[k] != v: problems.append(f"{k} {fixed[k]} != {v}")
    return {
        "magic": magic.decode("ascii", "replace"), "abi": b[8], "protocol": b[9],
        "denoiser_kind": b[10], "offset_rule": {0: "direct", 1: "mirrored"}.get(b[11], f"unknown({b[11]})"),
        "public_length": u32(12), "row": r, "wrong_row": u, "offset": d, "row_count": n, "tree_depth": u16(32),
        "session_id": sid,
        "s_0": hx(164, 32), "s_n": hx(196, 32), "authority_manifest_sha256": hx(228, 32), "chain_log_blake3": hx(260, 32),
        "context_digest": hx(292, 32), "ordered_session_root": hx(324, 32), "leaf_r": hx(356, 32), "leaf_u": hx(388, 32),
        "raw_blake3": hx(420, 32), "emission_blake3_r": hx(452, 32), "emission_blake3_u": hx(484, 32),
        "prev_drand_round": struct.unpack_from(">Q", b, 516)[0], "own_drand_round": struct.unpack_from(">Q", b, 524)[0],
        "drand_leg_digest": hx(532, 32), "constants_sha256": hx(564, 32), "spec_sha256": hx(596, 32),
        "preprocess_spec_sha256": hx(628, 32), "noise_blake3": hx(660, 32), "fixed": fixed,
        "r_correct": rc, "r_wrong": rw, "difference": D, "denominator": den,
        "difference_mse_units": D / den, "sign_positive": sign == 1,
        "outcome_class": "positive" if D > 0 else ("zero" if D == 0 else "negative"),
        "clip_flag": clip_flag, "clip_events": clip_events, "clip_events_saturated": clip_events == 65535,
        "framing_problems": problems,
    }

def main():
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(2)
    if a[0] == "--hex":
        raw = bytes.fromhex(a[1].strip())
    else:
        data = open(a[0], "rb").read()
        raw = bytes.fromhex(data.decode().strip()) if a[0].endswith(".hex") or len(data) != 752 else data
    out = decode(raw)
    print(json.dumps(out, indent=1))
    sys.exit(1 if out["framing_problems"] else 0)

if __name__ == "__main__":
    main()
