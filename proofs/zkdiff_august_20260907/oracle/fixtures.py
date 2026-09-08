#!/usr/bin/env python3
"""Differential boundary fixtures for the Rust port, generated from the SCALAR Python oracle
(kernels.py: rshift_round_s, round_div_s, clamp16_s, isqrt_s and the *_ref kernels), each
cross-checked against the numpy kernels before it is written.

One file per fixture in $G1_OUT/fixtures/: <name>.json with `kernel`, `params`, `inputs`,
`expected` and `counters` (clip events exactly as the oracle counts them: one per element
outside [-32768, 32767] before clamping, one per LUT lookup whose index carries mask 1).
Arrays are inline lists when small; large arrays live in <name>.npz and the JSON carries their
sha256 (little-endian int16 / int64, uint8 for masks, float32 never used here).
fixtures/manifest.json lists every file with its sha256 and the used shifts/divisors it covers.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np
import kernels as K
from common import CKPT, OUT, TH, TW
from int_ref import EXP_SIZE, F_CT, F_EPS, F_HINT, GN_GAMMA_BITS, GN_T, NOISE_P, P_EXP, R_EXP

FIX = OUT / "fixtures"
INLINE_MAX = 20000


# ---------------------------------------------------------------- helpers

def sha(a, dt):
    return hashlib.sha256(np.ascontiguousarray(np.asarray(a).astype(dt)).tobytes()).hexdigest()


def clamp_count_s(v):
    """Scalar oracle clamp with its counter: returns (clamped, 1 if v was outside the admitted domain else 0)."""
    return K.clamp16_s(v), (1 if (v < K.I16_MIN or v > K.I16_MAX) else 0)


class Fixture:
    def __init__(self, name, kernel, params, notes=""):
        self.d = {"fixture": name, "kernel": kernel, "params": params, "notes": notes, "inputs": {}, "expected": {}, "counters": {}}
        self.big = {}
    def inp(self, k, a, dt="<i8"):
        self._put("inputs", k, a, dt)
    def exp(self, k, a, dt="<i8"):
        self._put("expected", k, a, dt)
    def _put(self, sect, k, a, dt):
        a = np.asarray(a)
        if a.size > INLINE_MAX:
            self.big[k] = a.astype(dt if dt != "u1" else np.uint8)
            self.d[sect][k] = {"npz_key": k, "shape": list(a.shape), "dtype": dt, "sha256": sha(a, dt if dt != "u1" else np.uint8)}
        else:
            self.d[sect][k] = a.tolist() if a.ndim else (int(a) if np.issubdtype(a.dtype, np.integer) else a.item())
    def counter(self, k, v):
        self.d["counters"][k] = int(v)
    def write(self):
        FIX.mkdir(parents=True, exist_ok=True)
        if self.big:
            np.savez_compressed(FIX / f"{self.d['fixture']}.npz", **self.big)
            self.d["npz"] = f"{self.d['fixture']}.npz"
        json.dump(self.d, open(FIX / f"{self.d['fixture']}.json", "w"), indent=1)
        return self.d["fixture"]


def used_constants():
    """Shifts, divisors and LUT keys actually used by the frozen artifact (both schemes)."""
    shifts, divisors, luts, attn = set(), set(), {}, {}
    for scheme in ("int16", "int8"):
        c = json.load(open(OUT / f"constants_{scheme}.json"))
        for name, L in c["layers"].items():
            if L["kind"] == "conv":
                shifts.add(L["shift"])
            elif L["kind"] == "groupnorm":
                pass
            elif L.get("kind") == "attention":
                shifts.add(L["r_shift"]); attn[name] = L
            elif L["kind"] == "lut":
                luts[name] = L
        for name, g in c["static_bounds"]["groupnorm"].items():
            divisors.add(g["n"])
    shifts |= {2, 4, NOISE_P, GN_T}
    divisors |= {1 << GN_GAMMA_BITS}
    return sorted(shifts), sorted(divisors), luts, attn


# ---------------------------------------------------------------- fixtures

def fx_rounding(shifts, divisors):
    names = []
    f = Fixture("rounding_shifts_ties", "rshift_round", {"shifts": shifts, "rule": "(v + 2^(s-1)) >> s, arithmetic shift; ties toward +inf"},
                "signed ties and their neighbours at every used shift; plus small rescale shifts 1..8")
    cases_in, cases_s, cases_out = [], [], []
    for s in sorted(set(shifts) | set(range(1, 9))):
        half = 1 << (s - 1)
        vals = [0, 1, -1, half, half - 1, half + 1, -half, -half - 1, -half + 1, 3 * half, -3 * half, 5 * (1 << s) + half, -(5 * (1 << s) + half),
                32767, -32768, (1 << 40) + half, -((1 << 40) + half)]
        for v in vals:
            cases_in.append(v); cases_s.append(s); cases_out.append(K.rshift_round_s(v, s))
    f.inp("v", cases_in); f.inp("s", cases_s); f.exp("rshift_round", cases_out)
    assert all(int(K.rshift_round(np.array([v]), s)[0]) == o for v, s, o in zip(cases_in, cases_s, cases_out))
    names.append(f.write())

    f = Fixture("rounding_shifts_zero_negative", "rshift_round", {"rule": "s <= 0 is an EXACT left shift v << -s (no rounding)"},
                "zero and negative shifts; the artifact only up-shifts int16 values by at most 15 bits (rescale), so v << -s fits i64")
    cases = [(v, s) for s in (0, -1, -3, -7, -15) for v in (0, 1, -1, 3, -3, 32767, -32768, 12345, -12345)]
    f.inp("v", [v for v, _ in cases]); f.inp("s", [s for _, s in cases]); f.exp("rshift_round", [K.rshift_round_s(v, s) for v, s in cases])
    names.append(f.write())

    f = Fixture("rounding_divisors_ties", "round_div", {"divisors": divisors, "rule": "floor((2a + b) / (2b)), b > 0; ties toward +inf"},
                "every GroupNorm group size n (mean divisor), 2^12 (gamma multiplier), and odd divisors as attention denominators can be")
    cases_a, cases_b, cases_out = [], [], []
    for d in sorted(set(divisors) | {3, 5, (1 << P_EXP) + 1, 168 * (1 << P_EXP) - 1}):
        hd = d // 2
        vals = [0, d, -d, hd, -hd, hd + 1, hd - 1, -hd - 1, -hd + 1, 3 * hd, -3 * hd, 7 * d + hd, -(7 * d + hd), d - 1, -(d - 1), 1, -1]
        if d % 2 == 1:
            vals += [hd, hd + 1, -hd, -hd - 1]
        for a in vals:
            cases_a.append(a); cases_b.append(d); cases_out.append(K.round_div_s(a, d))
    f.inp("a", cases_a); f.inp("b", cases_b); f.exp("round_div", cases_out)
    assert all(int(K.round_div(np.array([a]), np.array([b]))[0]) == o for a, b, o in zip(cases_a, cases_b, cases_out))
    names.append(f.write())
    return names


def fx_domain():
    f = Fixture("domain_endpoints_clamp16", "clamp16", {"domain": [K.I16_MIN, K.I16_MAX]},
                "both endpoints admitted; values outside saturate and each is one clip event")
    v = [-(1 << 40), -39795, -32769, -32768, -32767, -1, 0, 1, 32766, 32767, 32768, 39795, 1 << 40]
    out, cnt = zip(*[clamp_count_s(x) for x in v])
    f.inp("v", v); f.exp("clamp16", list(out)); f.exp("clip_flag", list(cnt)); f.counter("clip_events", sum(cnt))
    ctr = {}; K.clamp16(np.array(v), ctr, "t"); assert ctr.get("t", 0) == sum(cnt)
    return [f.write()]


def fx_noising(SA, SO):
    f = Fixture("noising_saturation", "noise_Ct", {"SA_INT": SA, "SO_INT": SO, "P": NOISE_P, "f": F_CT,
                                                   "rule": "C_t = clamp16(rshift_round(SA*C + SO*noise, P)); one clip event per saturated element"},
                "C = noise = -32767 gives -39795 before clipping and -32768 after (Astra r4 item 1); positive twin; endpoints; interior")
    pairs = [(-32767, -32767), (32767, 32767), (-32768, -32768), (32767, -32768), (-32768, 32767), (0, -32768), (0, 32767), (-32768, 0), (32767, 0),
             (4096, 0), (0, 4096), (-1, 1), (1, -1), (0, 0), (-32767, 32767), (20000, 20000), (-20000, -20000), (30000, 12000)]
    C = [c for c, _ in pairs]; N = [n for _, n in pairs]
    acc = [SA * c + SO * n for c, n in pairs]; pre = [K.rshift_round_s(a, NOISE_P) for a in acc]
    out, cnt = zip(*[clamp_count_s(p) for p in pre])
    f.inp("C_int", C); f.inp("noise_int", N); f.exp("acc", acc); f.exp("pre_clip", pre); f.exp("Ct_int", list(out)); f.exp("clip_flag", list(cnt))
    f.counter("clip_events_C_t", sum(cnt))
    assert pre[0] == -39795 and out[0] == -32768 and pre[1] == 39795 and out[1] == 32767
    ctr = {}; got = K.clamp16(K.rshift_round(np.array(acc), NOISE_P), ctr, "C_t"); assert got.tolist() == list(out) and ctr["C_t"] == sum(cnt)
    return [f.write()]


def requant_scalar(acc, M, bp, S):
    """Scalar requant with counting: returns (out array, clip count)."""
    O = acc.shape[0]; out = np.empty_like(acc); n = 0
    for o in range(O):
        for idx in np.ndindex(acc.shape[1:]):
            pre = K.rshift_round_s(int(acc[(o,) + idx]) * int(M[o]) + int(bp[o]), S)
            v, c = clamp_count_s(pre); out[(o,) + idx] = v; n += c
    return out, n


def fx_conv(shifts):
    names = []
    rng = np.random.default_rng(20260907)
    # a) impulses at corners/edges, stride 1 and 2, width 20 (> 8 columns) and a stride-2 tail with odd width
    w = np.arange(1, 10, dtype=np.int64).reshape(1, 1, 3, 3)
    for stride, W_ in ((1, 20), (2, 20), (2, 21)):
        f = Fixture(f"conv3x3_impulses_s{stride}_w{W_}", "conv2d_acc", {"stride": stride, "pad": 1, "w_shape": [1, 1, 3, 3], "x_shape": [1, 5, W_]},
                    "single impulses at the four corners and four edge midpoints; kernel taps 1..9 so each output reveals which tap it saw; output width > 8 columns")
        pos = [(0, 0), (0, W_ - 1), (4, 0), (4, W_ - 1), (0, W_ // 2), (4, W_ // 2), (2, 0), (2, W_ - 1)]
        xs, accs = [], []
        for (i, j) in pos:
            x = np.zeros((1, 5, W_), dtype=np.int64); x[0, i, j] = 1
            acc = K.conv2d_acc_ref(x, w, stride, 1); assert np.array_equal(acc, K.conv2d_acc(x, w, stride, 1))
            xs.append(x); accs.append(acc)
        f.inp("w", w); f.inp("impulse_positions", pos); f.inp("x", np.stack(xs)); f.exp("acc", np.stack(accs))
        names.append(f.write())
    # b) saturation through requant, both signs, at the artifact's smallest and largest CONVOLUTION shifts and a small shift
    conv_shifts = [x for x in shifts if x >= 30]
    for S in (min(conv_shifts), max(conv_shifts), 8):
        f = Fixture(f"conv_requant_saturation_S{S}", "conv2d_acc+requant", {"stride": 1, "pad": 1, "S": S, "rule": "y = clamp16(rshift_round(acc*M + bp, S)); count per saturated element"},
                    "endpoint inputs with saturating weights and multipliers: positive and negative saturation, plus an interior channel that does not saturate; S 30 and 43 bracket the artifact's convolution shifts (int8 30-35, int16 38-43), S 8 is a small-shift case")
        x = np.full((2, 4, 12), 32767, dtype=np.int64); x[1] = -32768; x[0, 1, 5] = -32768; x[1, 2, 7] = 32767
        wq = np.zeros((3, 2, 3, 3), dtype=np.int64); wq[0, 0] = 32767; wq[1, 0] = -32767; wq[2, 0, 1, 1] = 1; wq[2, 1, 1, 1] = -1
        acc = K.conv2d_acc_ref(x, wq, 1, 1); assert np.array_equal(acc, K.conv2d_acc(x, wq, 1, 1))
        if S >= 40:      # at the artifact's large shifts the bound-respecting multiplier cannot saturate by itself: saturate through the pre-shift bias
            M = np.array([1 << 23, 1 << 23, 1 << 12], dtype=np.int64); bp = np.array([1 << 62, -(1 << 62), 3 << (S - 2)], dtype=np.int64)
        else:
            M = np.array([1 << 23, 1 << 23, 1 << 12], dtype=np.int64); bp = np.array([1 << (S - 1), -(1 << (S - 1)), 3 << (S - 2)], dtype=np.int64)
        assert K.conv_acc_bound(wq) * int(M.max()) + int(np.abs(bp).max()) + (1 << (S - 1)) < (1 << 63)
        y, n = requant_scalar(acc, M, bp, S)
        assert n > 0, f"saturation fixture S={S} did not saturate"
        ctr = {}; yn = K.requant(acc, M, bp, S, ctr, "c"); assert np.array_equal(y, yn) and ctr.get("c", 0) == n
        f.inp("x", x); f.inp("wq", wq); f.inp("M", M); f.inp("bp", bp); f.exp("acc", acc); f.exp("y", y); f.counter("clip_events", n)
        f.exp("clip_events_positive", int(sum(1 for o in range(3) for idx in np.ndindex(acc.shape[1:]) if K.rshift_round_s(int(acc[(o,)+idx]) * int(M[o]) + int(bp[o]), S) > K.I16_MAX)))
        f.exp("clip_events_negative", int(sum(1 for o in range(3) for idx in np.ndindex(acc.shape[1:]) if K.rshift_round_s(int(acc[(o,)+idx]) * int(M[o]) + int(bp[o]), S) < K.I16_MIN)))
        names.append(f.write())
    # c) random wide cases, int8 and int16 weights, stride 1 and 2, with requant at a used shift
    for scheme, qmax in (("int16", 32767), ("int8", 127)):
        for stride in (1, 2):
            f = Fixture(f"conv3x3_random_{scheme}_s{stride}_w24", "conv2d_acc+requant", {"stride": stride, "pad": 1, "S": 38 if scheme == "int16" else 30, "qmax": qmax},
                        "random int16 activations over the full domain, random weights, output width 24 (stride 1) or 12 (stride 2)")
            x = rng.integers(-32768, 32768, size=(3, 6, 24), dtype=np.int64); x[0, 0, 0] = -32768; x[2, 5, 23] = 32767
            wq = rng.integers(-qmax, qmax + 1, size=(4, 3, 3, 3), dtype=np.int64)
            acc = K.conv2d_acc_ref(x, wq, stride, 1); assert np.array_equal(acc, K.conv2d_acc(x, wq, stride, 1))
            S = 38 if scheme == "int16" else 30
            M = rng.integers(1 << 22, 1 << 23, size=4, dtype=np.int64); bp = rng.integers(-(1 << 45), 1 << 45, size=4, dtype=np.int64)
            assert K.conv_acc_bound(wq) * int(M.max()) + int(np.abs(bp).max()) + (1 << (S - 1)) < (1 << 63)
            y, n = requant_scalar(acc, M, bp, S)
            ctr = {}; yn = K.requant(acc, M, bp, S, ctr, "c"); assert np.array_equal(y, yn) and ctr.get("c", 0) == n
            f.inp("x", x); f.inp("wq", wq); f.inp("M", M); f.inp("bp", bp); f.exp("acc", acc); f.exp("y", y); f.counter("clip_events", n)
            f.exp("acc_bound_static", K.conv_acc_bound(wq)); f.exp("acc_absmax_observed", int(np.abs(acc).max()))
            names.append(f.write())
    return names


def rescale_add_scalar(a, fa, b, fb, fo):
    fm = max(fa, fb); out = []; n = 0
    for x, y in zip(a, b):
        s = K.rescale_s(int(x), fa, fm) + K.rescale_s(int(y), fb, fm)
        v, c = clamp_count_s(K.rescale_s(s, fm, fo)); out.append(v); n += c
    return out, n


def fx_add_cat():
    names = []
    f = Fixture("add_saturation_rescale", "add", {"rule": "align both operands to max(f) by exact left shift, add, rescale once to f_out (ties toward +inf), clamp16, count"},
                "positive and negative saturation, endpoint operands, ties in the final rescale, and interior values")
    a = [32767, -32768, 32767, -32768, 20000, -20000, 1, -1, 0, 32767, -32768, 3, -3, 16383, -16384]
    b = [32767, -32768, -32768, 32767, 20000, -20000, 1, -1, 0, 0, 0, 1, -1, 1, -1]
    for fa, fb, fo in ((11, 12, 11), (12, 12, 12), (12, 11, 13), (9, 12, 10)):
        out, n = rescale_add_scalar(a, fa, b, fb, fo)
        f.inp(f"a_f{fa}_b_f{fb}_fo{fo}", {"a": a, "b": b}); f.exp(f"y_f{fa}_b_f{fb}_fo{fo}", out); f.counter(f"clip_events_f{fa}_b_f{fb}_fo{fo}", n)
        fm = max(fa, fb); s = K.rescale(np.array(a), fa, fm) + K.rescale(np.array(b), fb, fm); ctr = {}
        yn = K.clamp16(K.rescale(s, fm, fo), ctr, "t"); assert yn.tolist() == out and ctr.get("t", 0) == n
    names.append(f.write())
    f = Fixture("concat_saturation_rescale", "cat", {"rule": "each half rescaled to f_out (exact left shift or rounded right shift), clamp16, count; concat along channels"},
                "first half up-shifted (can saturate), second half down-shifted (ties); channel order preserved")
    a = np.array([[32767, -32768], [16384, -16385], [1, -1]], dtype=np.int64); b = np.array([[3, -3], [1, -1], [32767, -32768]], dtype=np.int64)
    fa, fb, fo = 11, 13, 12
    outa, na = zip(*[clamp_count_s(K.rescale_s(int(v), fa, fo)) for v in a.reshape(-1)]); outb, nb = zip(*[clamp_count_s(K.rescale_s(int(v), fb, fo)) for v in b.reshape(-1)])
    y = np.concatenate([np.array(outa).reshape(a.shape), np.array(outb).reshape(b.shape)], 0)
    f.inp("a", a); f.inp("b", b); f.inp("f", {"a": fa, "b": fb, "out": fo}); f.exp("y", y); f.counter("clip_events", sum(na) + sum(nb))
    ctr = {}; yn = np.concatenate([K.clamp16(K.rescale(a, fa, fo), ctr, "t"), K.clamp16(K.rescale(b, fb, fo), ctr, "t")], 0); assert np.array_equal(yn, y) and ctr.get("t", 0) == sum(na) + sum(nb)
    names.append(f.write())
    return names


def gn_scalar_count(x, groups, gamma_q, beta_q, eps_int, T, f_out):
    """groupnorm_int_ref plus the clip counter (pre-clamp values recomputed with the same scalar formulas)."""
    C, H, W = x.shape; cpg = C // groups; n = cpg * H * W; X = n << (f_out + T - 6); cnt = 0; y = np.empty_like(x); Qs = []
    for g in range(groups):
        vals = [int(x[c, h, w]) for c in range(g * cpg, (g + 1) * cpg) for h in range(H) for w in range(W)]
        s1 = sum(vals); s2 = sum(v * v for v in vals); N = n * s2 - s1 * s1 + n * n * eps_int
        Q = K.isqrt_s((X * X) // N); mu6 = K.round_div_s(64 * s1, n); Qs.append(Q)
        for k in range(cpg):
            c = g * cpg + k; Mg = K.round_div_s(int(gamma_q[c]) * Q, 1 << 12)
            for h in range(H):
                for w in range(W):
                    pre = K.rshift_round_s((64 * int(x[c, h, w]) - mu6) * Mg, T) + int(beta_q[c])
                    v, cc = clamp_count_s(pre); y[c, h, w] = v; cnt += cc
    return y, cnt, Qs


def fx_groupnorm():
    names = []
    rng = np.random.default_rng(7)
    def run(name, x, groups, gamma_q, beta_q, eps_int, f_out, notes):
        f = Fixture(name, "groupnorm_int", {"groups": groups, "eps_int": eps_int, "T": GN_T, "f_out": f_out, "gamma_bits": GN_GAMMA_BITS,
                                            "n": (x.shape[0] // groups) * x.shape[1] * x.shape[2]}, notes)
        y, cnt, Qs = gn_scalar_count(x, groups, gamma_q, beta_q, eps_int, GN_T, f_out)
        yr = K.groupnorm_int_ref(x, groups, gamma_q, beta_q, eps_int, GN_T, f_out); assert np.array_equal(y, yr)
        ctr = {}; yn = K.groupnorm_int(x, groups, gamma_q, beta_q, eps_int, GN_T, f_out, ctr, "g"); assert np.array_equal(y, yn) and ctr.get("g", 0) == cnt
        f.inp("x", x, "<i2"); f.inp("gamma_q", gamma_q); f.inp("beta_q", beta_q); f.exp("y", y, "<i2"); f.exp("Q_per_group", Qs); f.counter("clip_events", cnt)
        names.append(f.write())
    gq = np.array([4096, -4096, 8191, 1, 2048, -3000], dtype=np.int64); bq = np.array([100, -100, 0, 32000, -32000, 7], dtype=np.int64)
    x = rng.integers(-3000, 3000, size=(6, 5, 4), dtype=np.int64); x[0:2] = 777
    run("groupnorm_constant_group", x, 3, gq, bq, 168, 12, "group 0 (channels 0,1) constant: e = 0, output = beta_q exactly; groups 1,2 random")
    x2 = x.copy(); x2[0, 0, 0] = 778
    run("groupnorm_nearly_constant_group", x2, 3, gq, bq, 168, 12, "group 0 constant except one element +1: N = n*1 - 1 + n^2 eps; the deviating element is amplified by Q")
    x3 = rng.integers(-32768, 32768, size=(2, 6, 7), dtype=np.int64); x3[0, 0, 0] = -32768; x3[1, 5, 6] = 32767
    run("groupnorm_endpoints_n84", x3, 1, gq[:2], bq[:2], 1, 11, "one group of 2 channels x 6 x 7 (n = 84, the smallest group size in the artifact) over the full domain, eps_int = 1")
    xb = np.empty((3, TH, TW), dtype=np.int64); flat = xb.reshape(-1); flat[: flat.size // 2] = -32768; flat[flat.size // 2:] = 32767
    run("groupnorm_balanced_endpoints_n32256", xb, 1, np.array([4096, -4096, 32767], dtype=np.int64), np.array([0, 0, 0], dtype=np.int64), 168, 9,
        "maximum group size n = 32256 (3 channels x 96 x 112), half -32768 half 32767: S2 = n*2^30 (45 bits), N near 2^60, X^2 99 bits, gamma_q 32767 saturates")
    xs = rng.integers(-32768, 32768, size=(2, 8, 8), dtype=np.int64)
    run("groupnorm_saturation_both_signs", xs, 2, np.array([32767, -32767], dtype=np.int64), np.array([32767, -32768], dtype=np.int64), 1, 15,
        "max |gamma_q| with f_out 15: outputs saturate on both sides; every saturated element counted")
    run("groupnorm_zero_gamma", xs, 2, np.array([0, 0], dtype=np.int64), np.array([5, -5], dtype=np.int64), 168, 12, "gamma_q = 0: output = beta_q regardless of the statistics")
    return names


def fx_isqrt():
    f = Fixture("isqrt_perfect_squares", "isqrt", {"rule": "floor(sqrt(n)); Newton from 2^ceil(bits/2), stop at first non-decrease; verified by r^2 <= n < (r+1)^2"},
                "perfect squares and +-1 around them up to 2^102, plus the GroupNorm-shaped case X^2 // N")
    ks = [0, 1, 2, 3, 7, 8, 255, 256, 65535, 65536, (1 << 32) - 1, 1 << 32, (1 << 40) + 12345, 1 << 49, (1 << 51) - 1]
    ns = []
    for k in ks:
        ns += [k * k, k * k + 1, max(k * k - 1, 0)]
    ns += [2, 3, 5, 10 ** 12, (1 << 100) + 12345, (1 << 102) // 7]
    exp = [K.isqrt_s(n) for n in ns]
    f.inp("n", [str(n) for n in ns]); f.exp("isqrt", [str(v) for v in exp]); f.d["notes"] += "; values are decimal strings (exceed 64 bits)"
    return [f.write()]


def fx_pool_bilinear():
    names = []
    f = Fixture("avgpool2_ties", "avgpool2_int", {"rule": "(a+b+c+d + 2) >> 2; ties toward +inf; same f"}, "2x2 sums of +-2, +-6 (ties), +-1, +-3, endpoints")
    quads = [(1, 1, 0, 0), (-1, -1, 0, 0), (3, 3, 0, 0), (-3, -3, 0, 0), (1, 0, 0, 0), (-1, 0, 0, 0), (2, 1, 0, 0), (-2, -1, 0, 0),
             (32767, 32767, 32767, 32767), (-32768, -32768, -32768, -32768), (32767, -32768, 32767, -32768), (32767, 32767, 32767, 32766)]
    x = np.zeros((1, 2, 2 * len(quads)), dtype=np.int64)
    for i, (a, b, c, d) in enumerate(quads):
        x[0, 0, 2 * i] = a; x[0, 0, 2 * i + 1] = b; x[0, 1, 2 * i] = c; x[0, 1, 2 * i + 1] = d
    y = K.avgpool2_int_ref(x); assert np.array_equal(y, K.avgpool2_int(x))
    f.inp("x", x); f.exp("y", y); f.counter("clip_events", 0)
    names.append(f.write())
    for shape, vals, note in (((1, 1, 1), [[[5]]], "1x1 input: all four outputs equal the input"),
                              ((1, 2, 2), [[[1, 0], [0, 0]]], "2x2 input with one 1: sums 9,3,1 over 16 -> one final rounding"),
                              ((1, 2, 3), [[[-1, 0, 1], [0, 0, 0]]], "signed neighbours: negative sums round toward +inf after +8"),
                              ((2, 3, 3), [[[32767, -32768, 32767], [-32768, 32767, -32768], [32767, -32768, 32767]], [[-32768] * 3, [32767] * 3, [-32768] * 3]], "endpoint checkerboard: 16-weighted sums stay within i64 and outputs within int16")):
        f = Fixture(f"bilinear_up2_border_{shape[1]}x{shape[2]}", "bilinear_up2_int", {"rule": "per axis out[2k] = in[max(k-1,0)] + 3 in[k], out[2k+1] = 3 in[k] + in[min(k+1,n-1)] (x4 each axis), then (sum + 8) >> 4 once", "in_shape": list(shape)}, note)
        x = np.array(vals, dtype=np.int64).reshape(shape)
        y = K.bilinear_up2_int_ref(x); assert np.array_equal(y, K.bilinear_up2_int(x))
        f.inp("x", x); f.exp("y", y); f.exp("sum_x16", K._up2_axis_x4(K._up2_axis_x4(x, 1), 2)); f.counter("clip_events", 0)
        names.append(f.write())
    return names


def fx_luts(luts):
    names = []
    import torch, torch.nn.functional as F
    idx = np.arange(-32768, 32768, dtype=np.int64)
    for key, L in sorted(luts.items()):
        _, kind, fio = key.split(":"); fi, fo = (int(v) for v in fio.split("->"))
        fn = (lambda z: z / (1.0 + np.exp(-z))) if kind == "silu" else (lambda z: F.gelu(torch.from_numpy(np.ascontiguousarray(z))).numpy())
        table, mask = K.make_act_lut_with_mask(fn, fi, fo)
        assert sha(table, "<i2") == L["table_sha256_int16_le"] and sha(mask, np.uint8) == L["mask_sha256_uint8"], key
        f = Fixture(f"lut_all_indices_{kind}_{fi}_{fo}", "lut_apply", {"kind": kind, "f_in": fi, "f_out": fo, "index": "x_int16 + 32768",
                                                                       "table_sha256_int16_le": L["table_sha256_int16_le"], "mask_sha256_uint8": L["mask_sha256_uint8"]},
                    "every int16 input once: expected output is the table itself; expected clip events = number of indexed entries with mask 1 (all of them here)")
        y = K.lut_apply_ref(idx, table); assert np.array_equal(y, table) and np.array_equal(y, K.lut_apply(idx, table))
        f.inp("x", idx, "<i2"); f.inp("table", table, "<i2"); f.inp("mask", mask, "u1"); f.exp("y", y, "<i2")
        f.counter("lut_clipped_hits", int(mask.sum())); f.exp("clipped_entries", int(mask.sum()))
        f.exp("first_clipped_index_int16", int(idx[mask][0]) if mask.any() else None); f.exp("hit_for_input_32767", int(mask[-1]))
        names.append(f.write())
    return names


def fx_attention(attn):
    names = []
    et = K.make_exp_table(R_EXP, EXP_SIZE, P_EXP)
    def run(name, q, k, v, f_q, notes):
        mult, r_shift = K.attention_scale(q.shape[1], f_q, R_EXP)
        f = Fixture(name, "attention_int", {"heads": q.shape[0], "head_dim": q.shape[1], "tokens": q.shape[2], "f_qkv": f_q, "mult": mult, "r_shift": r_shift,
                                            "R_EXP": R_EXP, "EXP_SIZE": EXP_SIZE, "P_EXP": P_EXP, "exp_table_sha256_int64_le": sha(et, "<i8")}, notes)
        y = K.attention_int_ref(q, k, v, r_shift, et, mult); assert np.array_equal(y, K.attention_int(q, k, v, r_shift, et, mult))
        # expose the intermediates of head 0 for debugging
        s = q[0].T @ k[0]; m = s.max(axis=1, keepdims=True); u = np.minimum(K.rshift_round((m - s) * mult, r_shift), EXP_SIZE - 1); w = et[u]
        f.inp("q", q); f.inp("k", k); f.inp("v", v); f.exp("out", y); f.exp("head0_scores", s); f.exp("head0_u", u); f.exp("head0_weights", w); f.exp("head0_den", w.sum(axis=1))
        f.counter("clip_events", 0)
        names.append(f.write())
    D = 16
    q = np.zeros((1, D, 5), dtype=np.int64); k = np.zeros((1, D, 5), dtype=np.int64)
    v = np.array([[[-32768, 32767, -1, 1, 0]] * D], dtype=np.int64)
    run("attention_equal_scores", q, k, v, 11, "q = 0: all scores equal, every weight 2^20, output = round_div(sum v, 5) with negative numerators")
    q2 = np.zeros((1, D, 3), dtype=np.int64); q2[0, 0, :] = 8192
    k2 = np.zeros((1, D, 3), dtype=np.int64); k2[0, 0, 0] = 32767; k2[0, 0, 1] = -32767; k2[0, 0, 2] = 32767 - 1
    v2 = np.array([[[1000, -1000, 500]] * D], dtype=np.int64)
    run("attention_exponent_clamp_boundary", q2, k2, v2, 11, "f_q 11 -> r_shift 14: key 1 has m - s = 2*8192*32767 = 536870912 -> u = 32768 clamped to 32767 (weight 0); key 2 sits one unit below the max score")
    rng = np.random.default_rng(3)
    q3 = rng.integers(-2000, 2000, size=(2, D, 7), dtype=np.int64); k3 = rng.integers(-2000, 2000, size=(2, D, 7), dtype=np.int64)
    v3 = rng.integers(-32768, 32768, size=(2, D, 7), dtype=np.int64)
    run("attention_signed_weighted_average", q3, k3, v3, 12, "two heads, f_q 12 -> r_shift 16, random signed values over the full domain: signed numerators, ties toward +inf in round_div")
    q4 = np.zeros((1, 12, 4), dtype=np.int64); q4[0, 0] = 700; k4 = np.zeros((1, 12, 4), dtype=np.int64); k4[0, 0] = [3000, -3000, 0, 1500]
    v4 = np.array([[[-5, 5, 10, -10]] * 12], dtype=np.int64)
    run("attention_head_dim12_multiplier", q4, k4, v4, 11, "width-12 specification: mult 18919, r_shift 2*11+16-10 = 28; not used by the b16 artifact")
    return names


def fx_sse():
    names = []
    f = Fixture("sse_endpoints", "score_int", {"rule": "sum (eps_int - noise_int)^2 over 4x96x112, exact; f = 12", "elements": 4 * TH * TW}, "both endpoint combinations and a half/half mix")
    n = 4 * TH * TW
    e1 = np.full((4, TH, TW), -32768, dtype=np.int64); n1 = np.full((4, TH, TW), 32767, dtype=np.int64)
    e2 = np.full((4, TH, TW), 32767, dtype=np.int64); n2 = np.full((4, TH, TW), -32768, dtype=np.int64)
    e3 = e1.copy(); e3.reshape(-1)[n // 2:] = 32767; n3 = n1.copy(); n3.reshape(-1)[n // 2:] = -32768
    exp = []
    for e, nn in ((e1, n1), (e2, n2), (e3, n3), (e1, e1)):
        s = sum(int(a - b) ** 2 for a, b in zip(e.reshape(-1)[:64], nn.reshape(-1)[:64]))    # scalar on a prefix ...
        full = int(((e - nn) * (e - nn)).sum()); exp.append(full)
        assert s == int(((e.reshape(-1)[:64] - nn.reshape(-1)[:64]) ** 2).sum())
    from int_ref import IntBackend, ITensor
    assert IntBackend.score_int(ITensor(e1, F_EPS), n1) == exp[0] == 4 * TH * TW * 65535 ** 2 == 184712316364800
    f.inp("cases", ["eps=-32768,noise=32767", "eps=32767,noise=-32768", "half/half", "eps=noise=-32768"]); f.exp("sse", [str(v) for v in exp])
    f.exp("sse_bound", str(4 * TH * TW * 65535 ** 2)); f.d["notes"] += "; values are decimal strings"
    names.append(f.write())
    return names


def main():
    shifts, divisors, luts, attn = used_constants()
    SA = json.load(open(OUT / "constants_int16.json"))["noising"]["SA_INT"]; SO = json.load(open(OUT / "constants_int16.json"))["noising"]["SO_INT"]
    FIX.mkdir(parents=True, exist_ok=True)
    for old in FIX.glob("*"):
        old.unlink()
    names = []
    names += fx_rounding(shifts, divisors); names += fx_domain(); names += fx_noising(SA, SO); names += fx_conv(shifts); names += fx_add_cat()
    names += fx_groupnorm(); names += fx_isqrt(); names += fx_pool_bilinear(); names += fx_luts(luts); names += fx_attention(attn); names += fx_sse()
    files = {}
    for p in sorted(FIX.iterdir()):
        if p.name != "manifest.json":
            files[p.name] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    manifest = {"artifact": "G1 FINAL differential boundary fixtures (scalar oracle)", "checkpoint": str(CKPT),
                "checkpoint_sha256": hashlib.sha256(open(CKPT, "rb").read()).hexdigest(),
                "oracle": "kernels.py scalar helpers and *_ref kernels; every expected value also verified equal to the numpy kernels",
                "counters": "clip_events = elements outside [-32768, 32767] before clamping (one per element); lut_clipped_hits = lookups whose index has mask 1",
                "used_shifts": shifts, "used_divisors": divisors, "noising": {"SA_INT": SA, "SO_INT": SO, "P": NOISE_P},
                "fixtures": names, "files": files}
    json.dump(manifest, open(FIX / "manifest.json", "w"), indent=1)
    print(f"wrote {len(names)} fixtures ({len(files)} files) to {FIX}; shifts {shifts}; divisors {divisors}")


if __name__ == "__main__":
    main()
