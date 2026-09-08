#!/usr/bin/env python3
"""Reference vectors for the ARM-C relation crate (g2_guest/armc-relation), G2-B.

Everything here is computed with the *pipeline's own* code paths (torch `F.interpolate(mode="area")`,
numpy float16 casts, torch bfloat16 casts, the truthbeam BLAKE3 XOF and CPU renderer) or with exact
integer / rational arithmetic, and every array is written as raw little-endian bytes with its sha256 in
MANIFEST.json. The Rust crate must reproduce every byte; nothing here is tuned to the Rust code.

Sources (read-only, cited by line in RELATION.md):
  precache.py:41-42            cache = load_C / _load_E_uncached -> float16 npy
  train_lean.py:120-133        load_C: raw 4600x5320 uint8 -> RGGB planes -> /255 float32 -> area (TH,TW)
  train_lean.py:142-153        _load_E_uncached: xof octaves -> area (TH,TW) each -> cat (12,TH,TW)
  lean_pubproto_eval.py:16-17  OFFSETS, T_VAL, EVAL_SEED
  lean_pubproto_eval.py:122-137 one generator per session, C -> bf16, Ct = q_sample(...).to(bf16), E -> bf16
  src/data/xof_generation.py   derive_xof_seeds / expand_seed_to_octaves / xof_octaves_from_hex
  g1_integer/README.md s.3     C_int = round(C_bf16 2^12), E_int = round(E_bf16 2^14), noise_int, Ct rule, SA/SO
  g1_integer/common.py         randn_cuda_emul (protocol noise), protocol_row_index
  proofs_20260902 membership/src/lib.rs 140-412, final_relation/chain/session_tree.py  (tree construction)
  truthbeam/code/recording/protocol/tile_cpu.py  (CPU renderer, emission digest oracle)

Usage: OMP_NUM_THREADS=8 python3 gen_vectors.py            (writes into this directory)
"""
from __future__ import annotations
import csv, hashlib, json, os, struct, sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from blake3 import blake3

torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "8")))

HERE = Path(__file__).resolve().parent
DEMO = HERE.parent.parent                       # scratch/zk_diffusion_demo_20260907
G1 = DEMO / "g1_integer"
SRC = DEMO / "src"
BUNDLE = Path("[zeebeam repository clone]/bundle/proofs_20260902")
AUGUST_CHAIN_LOG = BUNDLE / "final_relation/chain/chain_log.csv"
D2_CHAIN_LOG = Path("[truthbeam verification run]/d2/chain_log.csv")
TILE_CPU = BUNDLE.parent.parent.parent / "truthbeam/code/recording/protocol"

sys.path.insert(0, str(G1)); sys.path.insert(0, str(SRC))
import common                                   # g1_integer/common.py (module-level constants only)
from data.xof_generation import xof_octaves_from_hex, derive_xof_seeds, expand_seed_to_octaves  # noqa: E402

TH, TW = 96, 112
RAW_H, RAW_W = 4600, 5320
F_CT, F_HINT, F_EPS = 12, 14, 12
SA_INT, SO_INT, NOISE_P = 63540, 16053, 16      # g1_integer/README.md s.3, constants_int16.json
OFFSETS = [-2, 2, -15, 15, 30]                  # lean_pubproto_eval.py:16
T_VAL = 150
DENOM = 4 * TH * TW * (1 << (2 * F_EPS))       # 43008 * 2^24 = 721554505728 (= G1 residual_scale)

MANIFEST = {"files": {}, "notes": {}}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write(rel: str, data: bytes, **meta):
    p = HERE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    MANIFEST["files"][rel] = {"bytes": len(data), "sha256": sha256_bytes(data), **meta}
    return MANIFEST["files"][rel]["sha256"]


def write_i16(rel, a, **meta):
    a = np.asarray(a)
    assert a.min() >= -32768 and a.max() <= 32767, rel
    return write(rel, np.ascontiguousarray(a.astype("<i2")).tobytes(), dtype="int16_le", shape=list(a.shape), **meta)


def write_u32(rel, a, **meta):
    return write(rel, np.ascontiguousarray(np.asarray(a).astype("<u4")).tobytes(), dtype="uint32_le", shape=list(np.asarray(a).shape), **meta)


def write_f32(rel, a, **meta):
    return write(rel, np.ascontiguousarray(np.asarray(a).astype("<f4")).tobytes(), dtype="float32_le", shape=list(np.asarray(a).shape), **meta)


def write_json(rel, obj):
    data = (json.dumps(obj, indent=1, sort_keys=False) + "\n").encode()
    return write(rel, data, kind="json")


# --------------------------------------------------------------------------- shared PRNG (Python == Rust)
GOLDEN = np.uint64(0x9E3779B97F4A7C15)


def splitmix64_stream(seed: int, n_u64: int) -> np.ndarray:
    """Output i (0-based) = mix(seed + (i+1)*GOLDEN), all mod 2^64 (splitmix64 with a closed-form state)."""
    i = np.arange(1, n_u64 + 1, dtype=np.uint64)
    z = np.uint64(seed) + i * GOLDEN
    z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    return z ^ (z >> np.uint64(31))


def prng_bytes(seed: int, n: int) -> np.ndarray:
    words = splitmix64_stream(seed, (n + 7) // 8)
    return words.astype("<u8").view(np.uint8)[:n].copy()


def synthetic_frame(kind: str) -> np.ndarray:
    """Two full-size raw Bayer frames. 'a': uniform random bytes. 'b': three vertical regions so that the
    reduced means exercise float16 subnormals (x < 1000: byte==255 -> 1 else 0), small values (1000 <= x < 2000:
    byte & 3) and the full range (elsewhere)."""
    seed = {"a": 0xA5A50001, "b": 0xA5A50002}[kind]
    b = prng_bytes(seed, RAW_H * RAW_W).reshape(RAW_H, RAW_W)
    if kind == "a":
        return b
    x = np.arange(RAW_W)[None, :]
    out = b.copy()
    out = np.where(x < 1000, (b == 255).astype(np.uint8), out)
    out = np.where((x >= 1000) & (x < 2000), b & 3, out)
    return out.astype(np.uint8)


# --------------------------------------------------------------------------- pipeline pieces
def rggb_planes(raw: np.ndarray) -> np.ndarray:
    """train_lean.py:128-129."""
    x = raw.reshape(RAW_H, RAW_W)
    return np.stack([x[0::2, 0::2], x[0::2, 1::2], x[1::2, 0::2], x[1::2, 1::2]], 0)


def area_f32(t: np.ndarray) -> np.ndarray:
    """train_lean.py:133 / 152: F.interpolate(mode='area') on a float32 (C,H,W) tensor, CPU."""
    assert t.dtype == np.float32
    return F.interpolate(torch.from_numpy(t).unsqueeze(0), size=(TH, TW), mode="area").squeeze(0).numpy()


def cache_and_bf16(area_out: np.ndarray) -> torch.Tensor:
    """precache.py:41-42 (float16 cache), train_lean.py:123/139 (float32 load), lean_pubproto_eval.py:125/130 (bf16)."""
    return torch.from_numpy(area_out.astype(np.float16).astype(np.float32)).to(torch.bfloat16)


def quant(bf: torch.Tensor, f: int) -> np.ndarray:
    """g1_integer/int_ref.py:266/274: clip(rint(x_bf16 * 2^f))."""
    return np.clip(np.rint(bf.float().numpy().astype(np.float64) * 2.0 ** f), -32768, 32767).astype(np.int64)


def area_bins(n_in: int, n_out: int):
    """torch adaptive_avg_pool2d bins: start=floor(i*in/out), end=ceil((i+1)*in/out)."""
    return [((i * n_in) // n_out, -((-(i + 1) * n_in) // n_out)) for i in range(n_out)]


def exact_sums(planes: np.ndarray):
    """Exact integer bin sums and counts on the torch bins."""
    C, H, W = planes.shape
    yb, xb = area_bins(H, TH), area_bins(W, TW)
    sums = np.zeros((C, TH, TW), np.int64); cnt = np.zeros((TH, TW), np.int64)
    p = planes.astype(np.int64)
    for i, (y0, y1) in enumerate(yb):
        for j, (x0, x1) in enumerate(xb):
            blk = p[:, y0:y1, x0:x1]
            sums[:, i, j] = blk.reshape(C, -1).sum(1); cnt[i, j] = (y1 - y0) * (x1 - x0)
    return sums, cnt


def round_half_even_div(num: int, den: int) -> int:
    return round(Fraction(num, den))            # Python round() on Fraction is round-half-even


def exact_quant(sums, cnt, f):
    """q = round_half_even(sum * 2^f / (255 * count)), the clean rational statement input."""
    out = np.zeros(sums.shape, np.int64)
    C = sums.shape[0]
    for c in range(C):
        for i in range(TH):
            for j in range(TW):
                out[c, i, j] = round_half_even_div(int(sums[c, i, j]) << f, 255 * int(cnt[i, j]))
    return out


def rshift_round(v, s):
    return (v + (1 << (s - 1))) >> s


def ct_int(c_int, noise_int):
    """g1_integer/README.md s.3: C_t = clamp16(rshift_round(SA*C + SO*noise, 16))."""
    return np.clip(rshift_round(SA_INT * c_int + SO_INT * noise_int, NOISE_P), -32768, 32767)


def coord_int():
    """diffusion_diagnostic_model.py coord_grid (ch0 = x over width, ch1 = y over height), rint(. * 2^14)
    from the exact rational linspace value; equal to G1's float64 rint (checked in this script)."""
    out = np.zeros((2, TH, TW), np.int64)
    for j in range(TW):
        out[0, :, j] = round_half_even_div(-16384 * (TW - 1) + 32768 * j, TW - 1)
    for i in range(TH):
        out[1, i, :] = round_half_even_div(-16384 * (TH - 1) + 32768 * i, TH - 1)
    return out


def E_int_from_s_hex(s_hex: str):
    """train_lean.py:151-153 then the cache/bf16/quant path. Returns (E_int (12,TH,TW), E_area_f32 (12,TH,TW))."""
    octs = xof_octaves_from_hex(s_hex)
    ups = [F.interpolate(o.unsqueeze(0), size=(TH, TW), mode="area").squeeze(0) for o in octs]
    E = torch.cat(ups, dim=0).contiguous().numpy()
    return quant(cache_and_bf16(E), F_HINT), E


def C_int_from_raw(raw: np.ndarray):
    planes = rggb_planes(raw)
    t = planes.astype(np.float32) / 255.0                      # train_lean.py:132 (float32 / python float -> float32)
    assert t.dtype == np.float32
    area = area_f32(t)
    return quant(cache_and_bf16(area), F_CT), area, planes


# --------------------------------------------------------------------------- renderer oracle (tile_cpu.py)
sys.path.insert(0, str(TILE_CPU))
import tile_cpu  # noqa: E402  (imports tile_params from the same directory)


def emission_digest(s_hex: str) -> str:
    """BLAKE3 of the interleaved 1080x1920 RGB tile rendered from S_t (v9 blocking loop: E_t = gen(xof(S_t)))."""
    seeds = derive_xof_seeds(bytes.fromhex(s_hex))
    chans = [tile_cpu.gen_channel_v2(s) for s in seeds]
    rgb = np.stack(chans, axis=-1)
    assert rgb.shape == (1080, 1920, 3) and rgb.dtype == np.uint8
    return blake3(rgb.tobytes()).hexdigest()


# --------------------------------------------------------------------------- ordered-session tree (membership lib.rs)
CONTEXT_DOMAIN = b"ZEEBEAM_ORDERED_SESSION_CONTEXT_V1\0"
ROW_DOMAIN = b"ZEEBEAM_ORDERED_SESSION_ROW_V1\0"
NODE_DOMAIN = b"ZEEBEAM_ORDERED_SESSION_NODE_V1\0"
ROOT_DOMAIN = b"ZEEBEAM_ORDERED_SESSION_ROOT_V1\0"
PADDING_DOMAIN = b"ZEEBEAM_ORDERED_SESSION_PADDING_V1\0"   # session_tree.py:30 (golden padding leaves)


def H(domain, parts):
    h = blake3(); h.update(domain)
    for p in parts:
        h.update(len(p).to_bytes(4, "big")); h.update(p)
    return h.digest()


def tree_depth_for_count(n):
    d, r = 0, n - 1
    while r:
        d += 1; r >>= 1
    return d


def context_digest(session_id: bytes, rows: int, s0: bytes, sn: bytes, manifest: bytes, chainlog: bytes) -> bytes:
    return H(CONTEXT_DOMAIN, [b"TB-v0.9", session_id, rows.to_bytes(4, "big"), b"\x01", s0, sn, manifest, chainlog])


def leaf_hash(ctx, t, s_t, raw_b3, meta, rnd, val, s_next, em_b3):
    return H(ROW_DOMAIN, [ctx, t.to_bytes(4, "big"), s_t, raw_b3, meta, rnd.to_bytes(8, "big"), val, s_next, em_b3])


def build_tree(leaves, ctx, rows, depth):
    width = 1 << depth
    layer = list(leaves) + [H(PADDING_DOMAIN, [ctx, rows.to_bytes(4, "big"), i.to_bytes(4, "big")]) for i in range(len(leaves), width)]
    layers = [layer]
    for level in range(1, depth + 1):
        layer = [H(NODE_DOMAIN, [ctx, level.to_bytes(2, "big"), p.to_bytes(4, "big"), layer[2 * p], layer[2 * p + 1]]) for p in range(len(layer) // 2)]
        layers.append(layer)
    assert len(layer) == 1
    return layers, layer[0]


def siblings(layers, index, depth):
    out, pos = [], index
    for level in range(depth):
        out.append(layers[level][pos ^ 1]); pos //= 2
    return out


def wrapped_root(ctx, rows, depth, internal):
    return H(ROOT_DOMAIN, [ctx, rows.to_bytes(4, "big"), depth.to_bytes(2, "big"), internal])


def advance_chain(s_t, bayer, meta, rnd, val):
    """b3xof relation lib.rs 252-271 (TB:ROW:v9, BE length prefixes)."""
    h = blake3(); h.update(b"TB:ROW:v9"); h.update(s_t)
    for part in (bayer, meta, rnd.to_bytes(8, "big"), val):
        h.update(len(part).to_bytes(4, "big")); h.update(part)
    return h.digest()


# --------------------------------------------------------------------------- statement encoders (mirror of statement.rs)
def encode_zbosm001(session_id: bytes, rows: int, depth: int, s0, sn, manifest, chainlog, root, sibs) -> bytes:
    """membership/src/lib.rs 231-264 (ZBOSM001)."""
    total = 184 + len(session_id) + 32 * len(sibs)
    b = bytearray(b"ZBOSM001"); b += bytes([1, 9, 1, 0]); b += struct.pack("<I", total)
    b += struct.pack("<HHI", len(session_id), depth, rows); b += s0 + sn + manifest + chainlog + root + session_id
    for s in sibs:
        b += s
    assert len(b) == total
    return bytes(b)


def encode_header(t: int, s_t: bytes, meta: bytes, rnd: int, val: bytes) -> bytes:
    """join/src/lib.rs 145-160 (ZBROWW01, 120 bytes)."""
    b = bytearray(b"ZBROWW01"); b += bytes([1, 9, 0, 0]); b += struct.pack("<I", t); b += s_t + meta
    b += struct.pack("<Q", rnd); b += val; b += bytes(4)
    assert len(b) == 120
    return bytes(b)


def encode_prev(s_prev, raw_prev, meta_prev, rnd_prev, val_prev, sig_prev) -> bytes:
    b = bytearray(b"ZBDPRV01") + s_prev + raw_prev + meta_prev + struct.pack("<Q", rnd_prev) + val_prev + sig_prev
    assert len(b) == 8 + 32 + 32 + 28 + 8 + 32 + 48
    return bytes(b)


def encode_leaf_u(u, s_u, raw_u, meta_u, rnd_u, val_u, s_next_u, em_u) -> bytes:
    b = bytearray(b"ZBDLFU01") + struct.pack("<I", u) + s_u + raw_u + meta_u + struct.pack("<Q", rnd_u) + val_u + s_next_u + em_u
    assert len(b) == 208
    return bytes(b)


QUICKNET_CHAIN_HASH = bytes.fromhex("52db9ba70e0cc0f6eaf7803dd07447a1f5477735fd3f661792ba94600c84e971")


def drand_leg_digest(rnd_prev, val_prev, rnd_own, val_own) -> bytes:
    h = blake3(); h.update(b"ZBDIFF:DRAND:v1\0")
    h.update(rnd_prev.to_bytes(8, "big")); h.update(val_prev); h.update(rnd_own.to_bytes(8, "big")); h.update(val_own)
    h.update(QUICKNET_CHAIN_HASH)
    return h.digest()


PUBLIC_BYTES = 752


def encode_public(*, denoiser_kind, r, u, d, rows, depth, session_id, s0, sn, manifest, chainlog, ctx, root, leaf_r, leaf_u,
                  raw_b3, em_r, em_u, rnd_prev, rnd_own, drand_digest, constants_sha, spec_sha, pre_sha, noise_b3,
                  r_correct, r_wrong) -> bytes:
    D = r_wrong - r_correct
    b = bytearray(b"ZBDIFF01"); b += bytes([1, 9, denoiser_kind, 0]); b += struct.pack("<I", PUBLIC_BYTES)
    b += struct.pack("<IIiIHH", r, u, d, rows, depth, len(session_id)); b += session_id + bytes(128 - len(session_id))
    b += s0 + sn + manifest + chainlog + ctx + root + leaf_r + leaf_u + raw_b3 + em_r + em_u
    b += rnd_prev.to_bytes(8, "big") + rnd_own.to_bytes(8, "big") + drand_digest
    b += constants_sha + spec_sha + pre_sha + noise_b3
    b += struct.pack("<Iqq", T_VAL, SA_INT, SO_INT) + bytes([NOISE_P, F_CT, F_HINT, F_EPS])
    b += struct.pack("<QQqQ", r_correct, r_wrong, D, DENOM) + bytes([1 if D > 0 else 0]) + bytes(3)
    assert len(b) == PUBLIC_BYTES, len(b)
    return bytes(b)


def stub_predict(ct: np.ndarray, hint: np.ndarray) -> np.ndarray:
    """The relation crate's StubDenoiser: eps[c] = clamp16(ct[c] - (hint[3c] >> 4)) (arithmetic shift). NOT a network."""
    eps = np.zeros_like(ct)
    for c in range(4):
        eps[c] = np.clip(ct[c].astype(np.int64) - (hint[3 * c].astype(np.int64) >> 4), -32768, 32767)
    return eps


def residual(eps, noise):
    d = eps.astype(np.int64) - noise.astype(np.int64)
    return int((d * d).sum())


STUB_CONSTANTS_SHA = hashlib.sha256(b"ARMC-RELATION-STUB-DENOISER-V0").digest()
STUB_SPEC_SHA = hashlib.sha256(b"ARMC-RELATION-STUB-SPEC-V0").digest()


# --------------------------------------------------------------------------- sections
def section_conversions():
    """float32 -> float16 (numpy) and float32 -> bfloat16 (torch) round-to-nearest-even vectors, incl. f16 subnormals."""
    rng = np.random.default_rng(20260907)
    n = 8192
    # log-uniform magnitudes from 1e-9 to 4, half of them negative, plus exact specials
    mag = np.exp(rng.uniform(np.log(1e-9), np.log(4.0), n)).astype(np.float32)
    sign = np.where(rng.integers(0, 2, n) == 1, -1.0, 1.0).astype(np.float32)
    x = (mag * sign).astype(np.float32)
    # ties: values whose f32 mantissa sits exactly on a f16 / bf16 half-way point
    bits = x.view(np.uint32).copy()
    bits[:1024] = (bits[:1024] & np.uint32(0xFFFFE000)) | np.uint32(0x1000)        # exact f16 tie (bit 12 set, below zero)
    bits[1024:2048] = (bits[1024:2048] & np.uint32(0xFFFF0000)) | np.uint32(0x8000)  # exact bf16 tie
    x = bits.view(np.float32)
    x[-4:] = [0.0, -0.0, 1.0, 5.960464477539063e-08]                               # zero, -zero, one, f16 min subnormal
    f16 = x.astype(np.float16).view(np.uint16)
    bf16 = torch.from_numpy(x.copy()).to(torch.bfloat16).view(torch.int16).numpy().view(np.uint16)
    back = x.astype(np.float16).astype(np.float32)
    q12 = np.clip(np.rint(torch.from_numpy(back.copy()).to(torch.bfloat16).float().numpy().astype(np.float64) * 4096.0), -32768, 32767).astype(np.int64)
    write("conv/f32_in.bin", x.astype("<f4").tobytes(), dtype="float32_le", shape=[n])
    write("conv/f16_bits.bin", f16.astype("<u2").tobytes(), dtype="uint16_le", shape=[n])
    write("conv/bf16_bits.bin", bf16.astype("<u2").tobytes(), dtype="uint16_le", shape=[n])
    write("conv/f16_back_f32.bin", back.astype("<f4").tobytes(), dtype="float32_le", shape=[n])
    write_i16("conv/cache_q12.bin", q12, note="rint(bf16(f16(x)) * 2^12) clipped, the cache path quantisation")
    MANIFEST["notes"]["conv"] = "numpy astype(float16) and torch .to(bfloat16) are both round-to-nearest-even; ties injected at [0,1024) (f16) and [1024,2048) (bf16)"


def section_synthetic():
    for kind in ("a", "b"):
        raw = synthetic_frame(kind)
        sha = sha256_bytes(raw.tobytes())
        MANIFEST["notes"][f"synthetic_frame_{kind}"] = {"seed_hex": hex({"a": 0xA5A50001, "b": 0xA5A50002}[kind]), "bytes": int(raw.size), "sha256": sha,
                                                          "generator": "splitmix64 closed form: out_i = mix(seed + (i+1)*0x9E3779B97F4A7C15), bytes = LE words; frame b: x<1000 -> (byte==255), 1000<=x<2000 -> byte&3"}
        c_int, area, planes = C_int_from_raw(raw)
        sums, cnt = exact_sums(planes)
        q_exact = exact_quant(sums, cnt, F_CT)
        # float64 exact mean -> f32 (a third definition, recorded so the RELATION doc can quote the mismatch count)
        h2 = (sums / (255.0 * cnt)).astype(np.float32)
        write_f32(f"synthetic/frame_{kind}_area_f32.bin", area, note="F.interpolate(mode='area') output on RGGB/255 float32, 4x96x112")
        write_i16(f"synthetic/frame_{kind}_c_q12_torchpath.bin", c_int, note="rint(bf16(f16(area)) * 2^12): the pipeline's C_int")
        write_u32(f"synthetic/frame_{kind}_sums.bin", sums, note="exact integer bin sums (4x96x112)")
        write_u32(f"synthetic/frame_{kind}_counts.bin", cnt, note="bin element counts (96x112)")
        write_i16(f"synthetic/frame_{kind}_c_q12_exact.bin", q_exact, note="round_half_even(sum * 2^12 / (255*count))")
        MANIFEST["notes"][f"synthetic_frame_{kind}_stats"] = {
            "torchpath_vs_exact_q12_mismatch": int((c_int != q_exact).sum()),
            "area_f32_vs_exact_mean_f32_bit_mismatch": int((area.view(np.uint32) != h2.view(np.uint32)).sum()),
            "distinct_bin_counts": sorted(set(cnt.reshape(-1).tolist())),
            "f16_subnormal_means": int(((area > 0) & (area < 6.103515625e-05)).sum()),
            "zero_means": int((area == 0).sum()),
        }
    write_json("synthetic/area_bins.json", {"y_2300_to_96": area_bins(2300, TH), "x_2660_to_112": area_bins(2660, TW),
                                            "octave_y": {str(h): area_bins(h, TH) for h in (17, 34, 68, 135)},
                                            "octave_x": {str(w): area_bins(w, TW) for w in (30, 60, 120, 240)}})


def load_chain(path: Path):
    lines = [l for l in path.read_text().splitlines() if not l.startswith("#")]
    return list(csv.DictReader(lines))


def section_d2():
    rows = load_chain(D2_CHAIN_LOG)
    st = {int(r["t"]): r["S_t_hex"] for r in rows}
    man_c = json.load(open(G1 / "vectors/vectors_int16_correct.json"))
    man_w = json.load(open(G1 / "vectors/vectors_int16_wrong_p2.json"))
    out = {"chain_log_sha256": sha256_bytes(D2_CHAIN_LOG.read_bytes()), "rows": {}}
    for row, man in ((1328, man_c), (1330, man_w)):
        e_int, e_area = E_int_from_s_hex(st[row])
        h = write_i16(f"d2/row_{row:06d}_E_q14_torchpath.bin", e_int, note="E_int: 12 octave channels area-resized, cache/bf16 path, rint(*2^14)")
        write_f32(f"d2/row_{row:06d}_E_area_f32.bin", e_area)
        assert h == man["inputs"]["E_int"]["sha256_int16_le"], (row, h)
        # exact-rational E for the record
        octs = [expand_seed_to_octaves(s) for s in derive_xof_seeds(bytes.fromhex(st[row]))]
        e_exact = np.zeros((12, TH, TW), np.int64)
        for o in range(4):
            grid = np.stack([octs[c][o] for c in range(3)], 0)
            sums, cnt = exact_sums(grid)
            e_exact[3 * o:3 * o + 3] = exact_quant(sums, cnt, F_HINT)
        write_i16(f"d2/row_{row:06d}_E_q14_exact.bin", e_exact)
        out["rows"][str(row)] = {"S_t_hex": st[row], "E_int_sha256_g1": man["inputs"]["E_int"]["sha256_int16_le"],
                                 "torchpath_vs_exact_q14_mismatch": int((e_int != e_exact).sum())}
    # C, noise, Ct, hint for row 1328 (protocol noise index 30) from the cached tensors and the G1 noise emulation
    Cb = common.load_C_bf16("d2", 1328)
    c_int = quant(Cb.reshape(4, TH, TW), F_CT)
    noise = common.protocol_noise("d2", 1328).numpy().reshape(4, TH, TW)
    n_int = np.clip(np.rint(noise.astype(np.float64) * 2.0 ** F_EPS), -32768, 32767).astype(np.int64)
    ct = ct_int(c_int, n_int)
    e_int, _ = E_int_from_s_hex(st[1328])
    coord = coord_int()
    hint = np.concatenate([e_int, coord], 0)
    hc = write_i16("d2/row_001328_C_q12_cache.bin", c_int, note="C_int from the node's float16 cache -> bf16 -> rint(*2^12)")
    hn = write_i16("d2/row_001328_noise_q12.bin", n_int, note="protocol noise (session generator seed 20260823, index 30) via g1 randn_cuda_emul, rint(*2^12)")
    ht = write_i16("d2/row_001328_Ct_q12.bin", ct)
    hh = write_i16("d2/row_001328_hint14_q14.bin", hint, note="cat(E_int, coord_int): the 14-channel hint the network consumes")
    hco = write_i16("d2/coord_q14.bin", coord, note="channel 0 = x (width), channel 1 = y (height); rint(linspace(-1,1) * 2^14)")
    g1 = man_c["inputs"]
    assert hc == g1["C_int"]["sha256_int16_le"] and hn == g1["noise_int"]["sha256_int16_le"] and ht == g1["Ct_int"]["sha256_int16_le"]
    assert hco == g1["coord_int"]["sha256_int16_le"] and hh == man_c["layers"]["hint"]["sha256_int16_le"]
    out["g1_manifest_sha256"] = {k: sha256_bytes((G1 / "vectors" / k).read_bytes()) for k in ("vectors_int16_correct.json", "vectors_int16_wrong_p2.json")}
    out["row_1328_inputs_match_g1"] = True
    out["residual_sums_g1_int16"] = {"correct_1328": man_c["residual_sum_int"], "wrong_1330": man_w["residual_sum_int"]}
    write_json("d2/d2_rows.json", out)


AUG_SESSION_ID = b"ZEEBEAM_MAINNET_BLOCKING_TRAINING_300S_20260822_001"
AUG_ROWS, AUG_DEPTH = 712, 10
AUG_S0 = bytes.fromhex("74e3a131e1aaadd98e18c5f2a5f28ffaf59b8cd738e10216586efa2a893f384c")
AUG_SN = bytes.fromhex("aeea9f4d6a55ebecd900eae187ea70dce05696551f96ae976c9a5243b3a4398e")
AUG_MANIFEST = bytes.fromhex("740d752d27b70cb63c9501a470562a52616f4a445a7a9c0fb300844f61c7d783")
AUG_CHAINLOG = bytes.fromhex("754e5716e65a065e5ad3146131609a1fd12e8310d966fb6bf2d3de6c568e7f8b")
# frozen row-96 constants, native/src/lib.rs (positive control for the tree builder)
F_CONTEXT = "f5eba65f4a3604bee08207b4af571b97813cbd4dd3f919c110f6c5125ab21ee0"
F_LEAF96 = "2e4e76aa9bfece295ce728ad12e37d1cc40fddfd190fa6012116cb88969f4f8b"
F_INTERNAL = "1d43309ef9a0e2fc6dba98846134280b98cda01840d2204dc41100d5038d3b37"
F_ROOT = "38a484b8793f3afadaf8fc5ba1c04d47e08cdbb4c07a39da09fb4149499a6572"


def august_tree():
    raw = AUGUST_CHAIN_LOG.read_bytes()
    assert blake3(raw).hexdigest() == AUG_CHAINLOG.hex()
    rows = load_chain(AUGUST_CHAIN_LOG)
    assert len(rows) == AUG_ROWS and rows[0]["S_t_hex"] == AUG_S0.hex()
    ctx = context_digest(AUG_SESSION_ID, AUG_ROWS, AUG_S0, AUG_SN, AUG_MANIFEST, AUG_CHAINLOG)
    assert ctx.hex() == F_CONTEXT
    leaves = []
    for i, r in enumerate(rows):
        s_next = bytes.fromhex(rows[i + 1]["S_t_hex"]) if i + 1 < AUG_ROWS else AUG_SN
        leaves.append(leaf_hash(ctx, i, bytes.fromhex(r["S_t_hex"]), bytes.fromhex(r["bayer_blake3_hex"]), bytes.fromhex(r["meta_hex"]),
                                int(r["drand_round_number"]), bytes.fromhex(r["drand_round_value_hex"]), s_next, bytes.fromhex(r["emission_live_pixel_blake3_hex"])))
    assert leaves[96].hex() == F_LEAF96
    layers, internal = build_tree(leaves, ctx, AUG_ROWS, AUG_DEPTH)
    assert internal.hex() == F_INTERNAL
    root = wrapped_root(ctx, AUG_ROWS, AUG_DEPTH, internal)
    assert root.hex() == F_ROOT
    return raw, rows, ctx, leaves, layers, root


def section_august():
    raw, rows, ctx, leaves, layers, root = august_tree()
    write("august/chain_log.csv", raw, note="the August session chain log, blake3 754e5716... (frozen CHAIN_LOG constant)")
    # the whole-log chain walk as a Python fact: every advance reproduces the next S_t
    ok = 0
    for i in range(AUG_ROWS - 1):
        r = rows[i]
        s_next = advance_chain(bytes.fromhex(r["S_t_hex"]), bytes.fromhex(r["bayer_blake3_hex"]), bytes.fromhex(r["meta_hex"]), int(r["drand_round_number"]), bytes.fromhex(r["drand_round_value_hex"]))
        ok += s_next.hex() == rows[i + 1]["S_t_hex"]
    last = rows[-1]
    s_n = advance_chain(bytes.fromhex(last["S_t_hex"]), bytes.fromhex(last["bayer_blake3_hex"]), bytes.fromhex(last["meta_hex"]), int(last["drand_round_number"]), bytes.fromhex(last["drand_round_value_hex"]))
    MANIFEST["notes"]["august_chain_walk"] = {"advances_reproduced": ok, "of": AUG_ROWS - 1, "final_advance_equals_S_N": s_n == AUG_SN}
    proof_row = 600
    wanted = sorted({proof_row, proof_row - 1} | {proof_row + d for d in OFFSETS})
    out = {"session": {"id": AUG_SESSION_ID.decode(), "rows": AUG_ROWS, "depth": AUG_DEPTH, "s_0": AUG_S0.hex(), "s_n": AUG_SN.hex(),
                       "authority_manifest_sha256": AUG_MANIFEST.hex(), "chain_log_blake3": AUG_CHAINLOG.hex(), "context": ctx.hex(), "ordered_session_root": root.hex(),
                       "frozen_row96_constants_reproduced": True},
           "proof_row": proof_row, "offsets": OFFSETS, "rows": {}}
    for t in wanted:
        r = rows[t]
        s_next = rows[t + 1]["S_t_hex"] if t + 1 < AUG_ROWS else AUG_SN.hex()
        em = emission_digest(r["S_t_hex"])
        assert em == r["emission_live_pixel_blake3_hex"], (t, em)          # Python renderer oracle == chain log
        e_int, _ = E_int_from_s_hex(r["S_t_hex"])
        he = write_i16(f"august/row_{t:06d}_E_q14_torchpath.bin", e_int)
        out["rows"][str(t)] = {"t": t, "s_t": r["S_t_hex"], "raw_blake3": r["bayer_blake3_hex"], "emission_blake3": r["emission_live_pixel_blake3_hex"],
                               "emission_blake3_reproduced_by_tile_cpu": True, "meta": r["meta_hex"], "drand_round": int(r["drand_round_number"]),
                               "drand_value": r["drand_round_value_hex"], "drand_signature": r["drand_signature_hex"], "s_next": s_next,
                               "leaf": leaves[t].hex(), "siblings": [s.hex() for s in siblings(layers, t, AUG_DEPTH)], "E_q14_sha256": he,
                               "raw_frame": f"[pending: [frames directory]/frame_{t:06d}.raw, 24,472,000 bytes, blake3 must equal raw_blake3]"}
    # the parts of row 600's public statement that the chain log already fixes (everything but the network outputs)
    r, p = rows[proof_row], rows[proof_row - 1]
    out["row_600_public_partial"] = {
        "leaf_r": leaves[proof_row].hex(), "raw_blake3_r": r["bayer_blake3_hex"], "emission_blake3_r": r["emission_live_pixel_blake3_hex"],
        "prev_drand_round": int(p["drand_round_number"]), "own_drand_round": int(r["drand_round_number"]),
        "drand_leg_digest": drand_leg_digest(int(p["drand_round_number"]), bytes.fromhex(p["drand_round_value_hex"]), int(r["drand_round_number"]), bytes.fromhex(r["drand_round_value_hex"])).hex(),
        "leaf_u_by_offset": {str(d): leaves[proof_row + d].hex() for d in OFFSETS},
        "emission_blake3_u_by_offset": {str(d): rows[proof_row + d]["emission_live_pixel_blake3_hex"] for d in OFFSETS},
    }
    write_json("august/august_rows.json", out)
    # ZBOSM001 / ZBROWW01 / ZBDPRV01 / ZBDLFU01 byte witnesses for r=600, u=602 (everything but raw_r and noise)
    sib = siblings(layers, proof_row, AUG_DEPTH)
    write("august/row_000600_membership_zbosm001.bin", encode_zbosm001(AUG_SESSION_ID, AUG_ROWS, AUG_DEPTH, AUG_S0, AUG_SN, AUG_MANIFEST, AUG_CHAINLOG, root, sib))
    write("august/row_000600_header_zbroww01.bin", encode_header(proof_row, bytes.fromhex(r["S_t_hex"]), bytes.fromhex(r["meta_hex"]), int(r["drand_round_number"]), bytes.fromhex(r["drand_round_value_hex"])))
    write("august/row_000600_sig_r.bin", bytes.fromhex(r["drand_signature_hex"]))
    write("august/row_000600_prev_zbdprv01.bin", encode_prev(bytes.fromhex(p["S_t_hex"]), bytes.fromhex(p["bayer_blake3_hex"]), bytes.fromhex(p["meta_hex"]), int(p["drand_round_number"]), bytes.fromhex(p["drand_round_value_hex"]), bytes.fromhex(p["drand_signature_hex"])))
    for d in OFFSETS:
        u = proof_row + d; ru = rows[u]
        s_next_u = bytes.fromhex(rows[u + 1]["S_t_hex"]) if u + 1 < AUG_ROWS else AUG_SN
        write(f"august/row_000600_offset_{d:+d}_leaf_u_zbdlfu01.bin", encode_leaf_u(u, bytes.fromhex(ru["S_t_hex"]), bytes.fromhex(ru["bayer_blake3_hex"]), bytes.fromhex(ru["meta_hex"]), int(ru["drand_round_number"]), bytes.fromhex(ru["drand_round_value_hex"]), s_next_u, bytes.fromhex(ru["emission_live_pixel_blake3_hex"])))
        write(f"august/row_000600_offset_{d:+d}_siblings_u.bin", b"".join(siblings(layers, u, AUG_DEPTH)))


def section_e2e():
    """A fully synthetic 16-row session whose row 5 frame is synthetic frame 'a', with REAL quicknet beacons borrowed
    from August rows 595..610 (a beacon signature is independent of the session), so the complete relation can be
    executed end to end with the stub denoiser and the public bytes compared against this independent computation."""
    raw_a = synthetic_frame("a")
    raw_b3 = blake3(raw_a.tobytes()).digest()
    aug = load_chain(AUGUST_CHAIN_LOG)
    n_rows, depth = 16, tree_depth_for_count(16)
    sid = b"ZBDIFF_SYNTHETIC_E2E_001"
    s0 = blake3(b"ZBDIFF synthetic S_0").digest()
    manifest = hashlib.sha256(b"ZBDIFF synthetic authority manifest").digest()
    chainlog = blake3(b"ZBDIFF synthetic chain log bytes").digest()
    r_proof, d = 5, 2
    u = r_proof + d
    recs = []
    s_t = s0
    for t in range(n_rows):
        a = aug[595 + t]
        bayer = raw_b3 if t == r_proof else blake3(f"ZBDIFF synthetic raw row {t}".encode()).digest()
        meta = struct.pack(">IQQI4s", t, 0, 0, 0, b"RG08")
        rnd, val, sig = int(a["drand_round_number"]), bytes.fromhex(a["drand_round_value_hex"]), bytes.fromhex(a["drand_signature_hex"])
        em = bytes.fromhex(emission_digest(s_t.hex()))
        s_next = advance_chain(s_t, bayer, meta, rnd, val)
        recs.append({"t": t, "s_t": s_t, "bayer": bayer, "meta": meta, "rnd": rnd, "val": val, "sig": sig, "em": em, "s_next": s_next})
        s_t = s_next
    sn = s_t
    ctx = context_digest(sid, n_rows, s0, sn, manifest, chainlog)
    leaves = [leaf_hash(ctx, x["t"], x["s_t"], x["bayer"], x["meta"], x["rnd"], x["val"], x["s_next"], x["em"]) for x in recs]
    layers, internal = build_tree(leaves, ctx, n_rows, depth)
    root = wrapped_root(ctx, n_rows, depth, internal)
    R, P, U = recs[r_proof], recs[r_proof - 1], recs[u]
    # inputs to the network
    c_int, _, _ = C_int_from_raw(raw_a)
    noise_words = prng_bytes(0x0E2E0001, 4 * TH * TW * 2).view("<u2").astype(np.int64)
    n_int = ((noise_words & 0x7FFF) - 16384).reshape(4, TH, TW)
    ct = ct_int(c_int, n_int)
    coord = coord_int()
    hint_r = np.concatenate([E_int_from_s_hex(R["s_t"].hex())[0], coord], 0)
    hint_u = np.concatenate([E_int_from_s_hex(U["s_t"].hex())[0], coord], 0)
    r_c = residual(stub_predict(ct, hint_r), n_int)
    r_w = residual(stub_predict(ct, hint_u), n_int)
    noise_bytes = np.ascontiguousarray(n_int.astype("<i2")).tobytes()
    pre_sha = bytes(32)  # filled by the Rust side: PREPROCESS_SPEC_SHA256 is a compiled constant; the test patches it in
    public = encode_public(denoiser_kind=0, r=r_proof, u=u, d=d, rows=n_rows, depth=depth, session_id=sid, s0=s0, sn=sn, manifest=manifest, chainlog=chainlog,
                           ctx=ctx, root=root, leaf_r=leaves[r_proof], leaf_u=leaves[u], raw_b3=raw_b3, em_r=R["em"], em_u=U["em"],
                           rnd_prev=P["rnd"], rnd_own=R["rnd"], drand_digest=drand_leg_digest(P["rnd"], P["val"], R["rnd"], R["val"]),
                           constants_sha=STUB_CONSTANTS_SHA, spec_sha=STUB_SPEC_SHA, pre_sha=pre_sha, noise_b3=blake3(noise_bytes).digest(),
                           r_correct=r_c, r_wrong=r_w)
    write("e2e/header_r.bin", encode_header(r_proof, R["s_t"], R["meta"], R["rnd"], R["val"]))
    write("e2e/membership_r_zbosm001.bin", encode_zbosm001(sid, n_rows, depth, s0, sn, manifest, chainlog, root, siblings(layers, r_proof, depth)))
    write("e2e/sig_r.bin", R["sig"])
    write("e2e/prev_zbdprv01.bin", encode_prev(P["s_t"], P["bayer"], P["meta"], P["rnd"], P["val"], P["sig"]))
    write("e2e/leaf_u_zbdlfu01.bin", encode_leaf_u(u, U["s_t"], U["bayer"], U["meta"], U["rnd"], U["val"], U["s_next"], U["em"]))
    write("e2e/siblings_u.bin", b"".join(siblings(layers, u, depth)))
    write("e2e/noise_q12.bin", noise_bytes, dtype="int16_le", shape=[4, TH, TW])
    write("e2e/offset.bin", struct.pack("<i", d))
    write("e2e/expected_public_zbdiff01.bin", public, note="bytes 628..660 (preprocess spec sha) are zero here; the Rust test substitutes its compiled constant before comparing")
    write_i16("e2e/C_q12.bin", c_int); write_i16("e2e/Ct_q12.bin", ct); write_i16("e2e/hint_r_q14.bin", hint_r); write_i16("e2e/hint_u_q14.bin", hint_u)
    write_json("e2e/e2e.json", {"session_id": sid.decode(), "rows": n_rows, "depth": depth, "r": r_proof, "u": u, "offset": d,
                                 "raw_frame": "synthetic frame a (regenerate from the PRNG; sha256 in notes.synthetic_frame_a)",
                                 "raw_blake3": raw_b3.hex(), "context": ctx.hex(), "root": root.hex(), "leaf_r": leaves[r_proof].hex(), "leaf_u": leaves[u].hex(),
                                 "emission_r": R["em"].hex(), "emission_u": U["em"].hex(), "beacons_borrowed_from_august_rows": [595, 595 + n_rows - 1],
                                 "prev_round": P["rnd"], "own_round": R["rnd"], "R_correct_stub": r_c, "R_wrong_stub": r_w, "D_stub": r_w - r_c,
                                 "denoiser": "StubDenoiser (kind 0): eps[c] = clamp16(Ct[c] - (hint[3c] >> 4)); the network is NOT exercised here"})


def main():
    section_conversions()
    section_synthetic()
    section_d2()
    section_august()
    section_e2e()
    MANIFEST["environment"] = {"torch": torch.__version__, "numpy": np.__version__, "python": sys.version.split()[0],
                               "torch_threads": torch.get_num_threads()}
    MANIFEST["sources"] = {
        "d2_chain_log": {"path": str(D2_CHAIN_LOG), "sha256": sha256_bytes(D2_CHAIN_LOG.read_bytes())},
        "august_chain_log": {"path": str(AUGUST_CHAIN_LOG), "blake3": AUG_CHAINLOG.hex()},
        "g1_cache_C_001328": {"path": str(G1 / "rows[preprocessed-row cache]/d2/C_001328.npy"), "sha256": sha256_bytes((G1 / "rows[preprocessed-row cache]/d2/C_001328.npy").read_bytes())},
        "tile_cpu": {"path": str(TILE_CPU / "tile_cpu.py"), "sha256": sha256_bytes((TILE_CPU / "tile_cpu.py").read_bytes())},
        "xof_generation": {"path": str(SRC / "data/xof_generation.py"), "sha256": sha256_bytes((SRC / "data/xof_generation.py").read_bytes())},
    }
    (HERE / "MANIFEST.json").write_text(json.dumps(MANIFEST, indent=1) + "\n")
    print(json.dumps(MANIFEST["notes"], indent=1))
    print(f"wrote {len(MANIFEST['files'])} files")


if __name__ == "__main__":
    main()
