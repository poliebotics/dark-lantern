#!/usr/bin/env python3
"""Regenerate the 112 normative noise tensors from their rule and compare them with the published bytes and pins.

The rule (STATEMENT.md section 8; oracle/final/README_FINAL.md section 5): for proof row r in 600..711 the noise is
randn_cuda_emul(seed=20260823, call_index=r-600): Philox4x32-10 with the Random123/cuRAND constants, key (20260823, 0),
counter (r-600, 0, e, 0) for element e of the flattened (4, 96, 112) tensor, Box-Muller lane x in float32 with numpy
float32 log and sin, then noise_int = rint(sample * 2^12) with ties to even, clamped to int16, written little-endian.
The functions below are copied from oracle/common.py (philox4x32_10, box_muller_x, randn_cuda_emul) so that this tool
needs numpy only (no torch). The exported bytes in source/noise_august/ are the normative ones; this tool shows that they
follow the stated rule. It compares each regenerated tensor with the file's bytes, with PINS.json noise_files[r].sha256
and, when the `blake3` module is installed, with the BLAKE3 digest the statements publish.
usage: regen_noise.py [PACKAGE_ROOT] [--rows 600..711]"""
import hashlib, json, os, sys
sys.dont_write_bytecode = True
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
P = os.path.abspath(args[0]) if args else os.path.dirname(HERE)
rows = (600, 711)
if "--rows" in sys.argv:
    a, b = sys.argv[sys.argv.index("--rows") + 1].split("..")
    rows = (int(a), int(b))
try:
    import blake3
except ImportError:
    blake3 = None

TH, TW = 96, 112
SEED = 20260823
_M0, _M1 = np.uint64(0xD2511F53), np.uint64(0xCD9E8D57)
_W0, _W1 = np.uint32(0x9E3779B9), np.uint32(0xBB67AE85)
_MASK32 = np.uint64(0xFFFFFFFF)

def philox4x32_10(c0, c1, c2, c3, k0, k1):
    """Random123 / cuRAND Philox4x32-10 (oracle/common.py)."""
    c0 = np.asarray(c0, dtype=np.uint32); c1 = np.asarray(c1, dtype=np.uint32)
    c2 = np.asarray(c2, dtype=np.uint32); c3 = np.asarray(c3, dtype=np.uint32)
    k0 = np.uint32(k0); k1 = np.uint32(k1)
    with np.errstate(over="ignore"):
        for rnd in range(10):
            if rnd > 0:
                k0 = np.uint32((int(k0) + int(_W0)) & 0xFFFFFFFF)
                k1 = np.uint32((int(k1) + int(_W1)) & 0xFFFFFFFF)
            p0 = _M0 * c0.astype(np.uint64)
            p1 = _M1 * c2.astype(np.uint64)
            hi0 = (p0 >> np.uint64(32)).astype(np.uint32); lo0 = (p0 & _MASK32).astype(np.uint32)
            hi1 = (p1 >> np.uint64(32)).astype(np.uint32); lo1 = (p1 & _MASK32).astype(np.uint32)
            c0, c1, c2, c3 = (hi1 ^ c1 ^ k0), lo1, (hi0 ^ c3 ^ k1), lo0
    return c0, c1, c2, c3

def philox_self_test():
    kats = [((0, 0, 0, 0), (0, 0), (0x6627e8d5, 0xe169c58d, 0xbc57ac4c, 0x9b00dbd8)),
            ((0xffffffff,) * 4, (0xffffffff,) * 2, (0x408f276d, 0x41c83b0e, 0xa20bc7c6, 0x6d5451fd)),
            ((0x243f6a88, 0x85a308d3, 0x13198a2e, 0x03707344), (0xa4093822, 0x299f31d0), (0xd16cfe09, 0x94fdcceb, 0x5001e420, 0x24126ea1))]
    return all(tuple(int(v) for v in philox4x32_10(*ctr, *key)) == want for ctr, key, want in kats)

_INV = np.float32(2.3283064e-10)
_INV_2PI = np.float32(2.3283064e-10) * np.float32(6.2831855)

def box_muller_x(x_u32, y_u32):
    u = x_u32.astype(np.float32) * _INV + _INV / np.float32(2)
    v = y_u32.astype(np.float32) * _INV_2PI + _INV_2PI / np.float32(2)
    s = np.sqrt(np.float32(-2) * np.log(u)).astype(np.float32)
    return (np.sin(v).astype(np.float32) * s).astype(np.float32)

def _box_muller_y(x_u32, y_u32):
    u = x_u32.astype(np.float32) * _INV + _INV / np.float32(2)
    v = y_u32.astype(np.float32) * _INV_2PI + _INV_2PI / np.float32(2)
    s = np.sqrt(np.float32(-2) * np.log(u)).astype(np.float32)
    return (np.cos(v).astype(np.float32) * s).astype(np.float32)

def randn_cuda_emul(seed, call_index, numel=4 * TH * TW, sms=108, max_threads_per_sm=2048):
    """torch.randn(numel, device='cuda', generator=g) emulated, g seeded with `seed` and advanced by `call_index` calls of this size."""
    block = 256
    grid = (numel + block - 1) // block
    grid = min(grid, sms * (max_threads_per_sm // block))
    stride = grid * block
    unroll = 4
    counter_offset = ((numel - 1) // (stride * unroll) + 1) * unroll
    base_ctr = (call_index * counter_offset) // 4
    assert (call_index * counter_offset) % 4 == 0
    k0, k1 = seed & 0xFFFFFFFF, (seed >> 32) & 0xFFFFFFFF
    out = np.empty(numel, dtype=np.float32)
    idx = np.arange(stride, dtype=np.uint32)
    rounded = ((numel - 1) // (stride * unroll) + 1) * stride * unroll
    it = 0
    for lin0 in range(0, rounded, stride * unroll):
        c0 = np.full(stride, (base_ctr + it) & 0xFFFFFFFF, dtype=np.uint32)
        c1 = np.full(stride, ((base_ctr + it) >> 32) & 0xFFFFFFFF, dtype=np.uint32)
        x0, x1, x2, x3 = philox4x32_10(c0, c1, idx, np.zeros(stride, np.uint32), k0, k1)
        lanes = [box_muller_x(x0, x1), None, box_muller_x(x2, x3), None]
        if numel > lin0 + stride:
            lanes[1], lanes[3] = _box_muller_y(x0, x1), _box_muller_y(x2, x3)
        for ii in range(unroll):
            li = lin0 + idx.astype(np.int64) + stride * ii
            m = li < numel
            if not m.any():
                continue
            out[li[m]] = lanes[ii][m]
        it += 1
    return out

def noise_int_bytes(r):
    sample = randn_cuda_emul(SEED, r - 600)
    q = np.rint(sample.astype(np.float64) * 4096.0)          # rint is ties-to-even
    return np.clip(q, -32768, 32767).astype("<i2").tobytes()

if not philox_self_test():
    print("Philox known-answer self-test FAILED"); sys.exit(1)
print("Philox4x32-10 known-answer self-test: OK (three Random123 vectors)")
pins = json.load(open(os.path.join(P, "PINS.json")))
exp = json.load(open(os.path.join(P, "source", "expected_identities_august.json")))
ok = bad = 0
for r in range(rows[0], rows[1] + 1):
    want = pins["noise_files"][str(r)]
    path = os.path.join(P, "source", want["file"].split("source/", 1)[-1])
    regen = noise_int_bytes(r)
    published = open(path, "rb").read()
    s = hashlib.sha256(regen).hexdigest()
    b3 = blake3.blake3(regen).hexdigest() if blake3 else None
    good = regen == published and s == want["sha256"] and (b3 is None or b3 == want["blake3"] == exp["rows"][str(r)]["noise_blake3"])
    ok += good; bad += not good
    print(f"row {r}: call_index {r-600:>3}  regenerated == published bytes: {regen == published}  sha256 == PINS: {s == want['sha256']}"
          + (f"  BLAKE3 == statement: {b3 == want['blake3']}" if b3 else "  (blake3 module absent: BLAKE3 not compared)") + ("" if good else "  MISMATCH"))
print(f"{ok} rows regenerated from the rule and equal to the published normative bytes; {bad} mismatches" + ("" if blake3 else "; install the blake3 module for the BLAKE3 comparison, or trust sha256 against PINS.json"))
sys.exit(1 if bad else 0)
