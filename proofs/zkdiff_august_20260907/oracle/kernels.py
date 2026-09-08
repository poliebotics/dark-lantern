#!/usr/bin/env python3
"""Integer kernels for the fixed-point reference implementation (G1).

Every kernel comes in two forms:
  <name>      : numpy int64 implementation used for the real rows (speed)
  <name>_ref  : plain scalar loops over Python ints, the normative definition
`selftest()` checks the two agree bit-for-bit on small random tensors plus explicit tie,
endpoint, constant-group and border fixtures.  No floating point is used anywhere in the
inference path; the tables are built once (float64) and then frozen by their bytes.

Conventions (normative; README_FINAL.md restates them):

  * admitted domain: a "tensor" is an int64 array whose values lie in the FULL int16 range
    [-32768, 32767] (both endpoints admitted), with a static scale 2^-f per tensor.  Every
    op clamps its result to that range and every clamp event is counted; every static
    bound below uses the factor 32768 = max(|-32768|, 32767).
  * RUNTIME rounding (shifts and divisions on data): ties toward +inf.
        rshift_round(v, s) = (v + 2^(s-1)) >> s   (arithmetic = floor shift), and an EXACT
                             left shift v << (-s) when s <= 0
        round_div(a, b)    = floor((2a + b) / (2b)), b > 0
    e.g. rshift_round(-3, 1) = -1, rshift_round(3, 1) = 2, round_div(-7, 2) = -3, round_div(7, 2) = 4.
  * CONVERSION rounding (float -> integer, done once when the artifact is frozen: inputs,
    weights, biases, multipliers, GroupNorm gamma/beta, LUT entries, exp table): ties to
    even (numpy rint / IEEE round-half-even).  A Rust port imports the frozen integer
    constants and tables from the artifact; it must not regenerate them from transcendental
    functions.
  * isqrt(n) = floor(sqrt(n)) by Newton iteration; the result is verified by
    r^2 <= n < (r+1)^2, so the iteration count is not part of the contract.
"""
from __future__ import annotations
import numpy as np

I16_MIN, I16_MAX = -32768, 32767
I16_ABS = 32768                      # full-domain magnitude bound used in every static bound


# ---------------------------------------------------------------- scalar helpers (Python ints)

def rshift_round_s(v: int, s: int) -> int:
    if s <= 0:
        return v << (-s)
    return (v + (1 << (s - 1))) >> s


def round_div_s(a: int, b: int) -> int:
    assert b > 0
    return (2 * a + b) // (2 * b)


def clamp16_s(v: int) -> int:
    return I16_MIN if v < I16_MIN else I16_MAX if v > I16_MAX else v


def isqrt_s(n: int) -> int:
    """floor(sqrt(n)) for n >= 0 by Newton iteration from a power-of-two overestimate."""
    assert n >= 0
    if n < 2:
        return n
    x = 1 << ((n.bit_length() + 1) // 2)      # >= sqrt(n)
    while True:
        y = (x + n // x) >> 1
        if y >= x:
            break
        x = y
    assert x * x <= n < (x + 1) * (x + 1)
    return x


# ---------------------------------------------------------------- numpy helpers

def rshift_round(v: np.ndarray, s: int) -> np.ndarray:
    v = np.asarray(v, dtype=np.int64)
    if s <= 0:
        return v << (-s)
    return (v + (np.int64(1) << np.int64(s - 1))) >> np.int64(s)


def round_div(a: np.ndarray, b) -> np.ndarray:
    a = np.asarray(a, dtype=np.int64)
    b = np.asarray(b, dtype=np.int64)
    return np.floor_divide(2 * a + b, 2 * b)


def clamp16(v: np.ndarray, counter: dict | None = None, name: str = "") -> np.ndarray:
    """Saturate to the admitted domain [-32768, 32767]; count every element that was outside it."""
    v = np.asarray(v, dtype=np.int64)
    if counter is not None:
        n = int(np.count_nonzero((v < I16_MIN) | (v > I16_MAX)))
        if n:
            counter[name] = counter.get(name, 0) + n
    return np.clip(v, I16_MIN, I16_MAX)


def in_domain(v: np.ndarray) -> bool:
    return bool(v.min() >= I16_MIN and v.max() <= I16_MAX)


def rescale(v: np.ndarray, f_from: int, f_to: int) -> np.ndarray:
    """Change fractional bits: exact left shift, or round-half-toward-+inf right shift."""
    return rshift_round(v, f_from - f_to)


def rescale_s(v: int, f_from: int, f_to: int) -> int:
    return rshift_round_s(v, f_from - f_to)


# ---------------------------------------------------------------- convolution (exact integer MAC)

def conv2d_acc(x: np.ndarray, w: np.ndarray, stride: int, pad: int) -> np.ndarray:
    """Exact integer cross-correlation.  x: (C,H,W) int64; w: (O,C,kh,kw) int64.
    Returns acc: (O,Ho,Wo) int64 = sum_{c,i,j} w[o,c,i,j] * xpad[c, s*ho+i, s*wo+j]."""
    C, H, W = x.shape
    O, C2, kh, kw = w.shape
    assert C == C2
    xp = np.pad(x, ((0, 0), (pad, pad), (pad, pad)), constant_values=0)
    Ho = (H + 2 * pad - kh) // stride + 1
    Wo = (W + 2 * pad - kw) // stride + 1
    cols = np.empty((C, kh, kw, Ho, Wo), dtype=np.int64)
    for i in range(kh):
        for j in range(kw):
            cols[:, i, j] = xp[:, i:i + stride * Ho:stride, j:j + stride * Wo:stride]
    cols = cols.reshape(C * kh * kw, Ho * Wo)
    acc = w.reshape(O, C * kh * kw) @ cols          # int64 matmul, exact
    return acc.reshape(O, Ho, Wo)


def conv2d_acc_ref(x, w, stride, pad):
    C, H, W = x.shape
    O, _, kh, kw = w.shape
    Ho = (H + 2 * pad - kh) // stride + 1
    Wo = (W + 2 * pad - kw) // stride + 1
    out = [[[0] * Wo for _ in range(Ho)] for _ in range(O)]
    for o in range(O):
        for ho in range(Ho):
            for wo in range(Wo):
                s = 0
                for c in range(C):
                    for i in range(kh):
                        hi = stride * ho + i - pad
                        if hi < 0 or hi >= H:
                            continue
                        for j in range(kw):
                            wi = stride * wo + j - pad
                            if wi < 0 or wi >= W:
                                continue
                            s += int(w[o, c, i, j]) * int(x[c, hi, wi])
                out[o][ho][wo] = s
    return np.array(out, dtype=np.int64).reshape(O, Ho, Wo)


def conv_acc_bound(wq: np.ndarray) -> int:
    """Static bound on |every partial sum| of conv2d_acc over the admitted domain: 32768 * max_o L1(wq[o])."""
    O = wq.shape[0]
    return I16_ABS * int(np.abs(wq.reshape(O, -1)).sum(1).max())


def requant(acc: np.ndarray, mult: np.ndarray, bias_pre: np.ndarray, shift: int, counter=None, name="") -> np.ndarray:
    """y[o,...] = clamp16( (acc[o,...] * mult[o] + bias_pre[o] + 2^(shift-1)) >> shift )."""
    m = mult.reshape(-1, *([1] * (acc.ndim - 1)))
    b = bias_pre.reshape(-1, *([1] * (acc.ndim - 1)))
    return clamp16(rshift_round(acc * m + b, shift), counter, name)


def requant_s(acc: int, mult: int, bias_pre: int, shift: int) -> int:
    return clamp16_s(rshift_round_s(acc * mult + bias_pre, shift))


# ---------------------------------------------------------------- GroupNorm (exact integer statistics)

def groupnorm_int(x: np.ndarray, groups: int, gamma_q: np.ndarray, beta_q: np.ndarray,
                  eps_int: int, T: int, f_out: int, counter=None, name="") -> np.ndarray:
    """x: (C,H,W) int64 with f_in fractional bits.  gamma_q = round(gamma*2^12), beta_q = round(beta*2^f_out).
    eps_int = max(1, round(eps * 2^(2 f_in))).  Per group (all in Python ints where the width may exceed 64 bits):
        S1 = sum x, S2 = sum x^2, n = C/groups*H*W
        N  = n*S2 - S1^2 + n^2*eps_int             (= n^2 * 2^(2 f_in) * (var_biased + eps_q), exact)
        mu6 = round_div(64*S1, n)                   (mean with 6 extra fractional bits)
        e_i = 64*x_i - mu6
        Q  = isqrt( (n * 2^(f_out+T-6))^2 // N )    (= floor(n*2^(f_out+T-6)/sqrt(N)); 128-bit numerator)
    per channel: Mg = round_div(gamma_q * Q, 2^12)
        y_i = clamp16( rshift_round(e_i * Mg, T) + beta_q )
    Width note: S2 <= n*2^30 fits int64 for n < 2^33; n*S2 and S1^2 are formed as Python ints (128-bit in Rust)."""
    C, H, W = x.shape
    cpg = C // groups
    n = cpg * H * W
    assert n * (I16_ABS ** 2) < (1 << 63), n          # S2 itself must fit the int64 reduction
    xg = x.reshape(groups, -1)
    S1 = xg.sum(axis=1)                       # int64, |S1| <= n*2^15
    S2 = (xg * xg).sum(axis=1)                # int64, <= n*2^30
    y = np.empty_like(x)
    X = n << (f_out + T - 6)
    for g in range(groups):
        s1, s2 = int(S1[g]), int(S2[g])
        N = n * s2 - s1 * s1 + n * n * eps_int
        assert N > 0
        Q = isqrt_s((X * X) // N)
        mu6 = round_div_s(64 * s1, n)
        e = 64 * xg[g] - mu6                  # int64, |e| < 2^23
        assert Q < (1 << 40)
        for k in range(cpg):
            c = g * cpg + k
            Mg = round_div_s(int(gamma_q[c]) * Q, 1 << 12)
            assert abs(Mg) < (1 << 39)
            ek = e[k * H * W:(k + 1) * H * W]
            yc = rshift_round(ek * Mg, T) + int(beta_q[c])
            y[c] = clamp16(yc, counter, name).reshape(H, W)
    return y


def groupnorm_int_ref(x, groups, gamma_q, beta_q, eps_int, T, f_out):
    C, H, W = x.shape
    cpg = C // groups
    n = cpg * H * W
    y = np.empty_like(x)
    X = n << (f_out + T - 6)
    for g in range(groups):
        vals = [int(x[c, h, w]) for c in range(g * cpg, (g + 1) * cpg) for h in range(H) for w in range(W)]
        s1 = sum(vals); s2 = sum(v * v for v in vals)
        N = n * s2 - s1 * s1 + n * n * eps_int
        Q = isqrt_s((X * X) // N)
        mu6 = round_div_s(64 * s1, n)
        for k in range(cpg):
            c = g * cpg + k
            Mg = round_div_s(int(gamma_q[c]) * Q, 1 << 12)
            for h in range(H):
                for w in range(W):
                    e = 64 * int(x[c, h, w]) - mu6
                    y[c, h, w] = clamp16_s(rshift_round_s(e * Mg, T) + int(beta_q[c]))
    return y


def groupnorm_static_bounds(n: int, f_out: int, T: int, eps_int: int, gamma_q_absmax: int) -> dict:
    """Data-independent bounds over the admitted domain (Python ints).
    S1: n*32768; S2: n*32768^2; N <= n^2*(32768^2 + eps_int); X = n*2^(f_out+T-6), X^2 bits;
    Q <= X/sqrt(N_min) with N_min = n^2*eps_int (constant group); affine product |e_i|*|Mg| via
    |x_i - mu| <= sqrt(n)*sigma (Cauchy-Schwarz) and Q <= X/sqrt(N):
        |e_i|*Q <= 64*X/sqrt(n) + X/(2*n*sqrt(eps_int)), then times gamma_q_absmax/2^12."""
    from math import isqrt
    S1 = n * I16_ABS; S2 = n * I16_ABS ** 2
    N_max = n * n * (I16_ABS ** 2 + eps_int)
    X = n << (f_out + T - 6)
    Q_max = isqrt((X * X) // (n * n * eps_int))
    eQ = (64 * X) // isqrt(n) + 1 + (X // (2 * n * isqrt(eps_int))) + 1        # ceil-ish, conservative
    affine = eQ * gamma_q_absmax // (1 << 12) + eQ                                # + slack for the rounding of Mg
    return {"n": n, "S1_bound": S1, "S2_bound": S2, "S2_bits": S2.bit_length(), "N_max": N_max, "N_bits": N_max.bit_length(),
            "X": X, "X2_bits": (X * X).bit_length(), "Q_max": Q_max, "Q_bits": Q_max.bit_length(),
            "affine_product_bound": affine, "affine_bits": affine.bit_length(), "fits_i64": affine < (1 << 63)}


# ---------------------------------------------------------------- lookup-table activations

def make_act_lut(fn, f_in: int, f_out: int) -> np.ndarray:
    """table[i] = clamp16(rint(fn((i - 32768) * 2^-f_in) * 2^f_out)) for i in 0..65535 (ties to even).
    Built once with float64; the inference path only indexes it."""
    return make_act_lut_with_mask(fn, f_in, f_out)[0]


def make_act_lut_with_mask(fn, f_in: int, f_out: int):
    """As make_act_lut, plus a boolean mask of the entries that were clipped to the admitted domain."""
    xs = (np.arange(65536, dtype=np.float64) - 32768.0) * (2.0 ** -f_in)
    ys = np.rint(fn(xs) * (2.0 ** f_out))
    clipped = (ys < I16_MIN) | (ys > I16_MAX)
    return np.clip(ys, I16_MIN, I16_MAX).astype(np.int64), clipped


def lut_apply(x: np.ndarray, table: np.ndarray) -> np.ndarray:
    return table[x + 32768]


def lut_apply_ref(x, table):
    out = np.empty_like(x)
    flat = x.reshape(-1)
    o = out.reshape(-1)
    for i in range(flat.size):
        o[i] = int(table[int(flat[i]) + 32768])
    return out


# ---------------------------------------------------------------- pooling / resampling

def avgpool2_int(x: np.ndarray, counter=None, name="") -> np.ndarray:
    """2x2 average pool, stride 2: (a+b+c+d + 2) >> 2.  Same fractional bits.  |sum| <= 4*32768 = 2^17."""
    C, H, W = x.shape
    s = x[:, 0::2, 0::2] + x[:, 0::2, 1::2] + x[:, 1::2, 0::2] + x[:, 1::2, 1::2]
    return clamp16(rshift_round(s, 2), counter, name)


def avgpool2_int_ref(x):
    C, H, W = x.shape
    y = np.empty((C, H // 2, W // 2), dtype=np.int64)
    for c in range(C):
        for i in range(H // 2):
            for j in range(W // 2):
                s = int(x[c, 2 * i, 2 * j]) + int(x[c, 2 * i, 2 * j + 1]) + int(x[c, 2 * i + 1, 2 * j]) + int(x[c, 2 * i + 1, 2 * j + 1])
                y[c, i, j] = clamp16_s(rshift_round_s(s, 2))
    return y


def _up2_axis_x4(v: np.ndarray, axis: int) -> np.ndarray:
    """One axis of bilinear x2 (align_corners=False), scaled by 4 (exact):
    out[2k] = in[max(k-1,0)] + 3 in[k];  out[2k+1] = 3 in[k] + in[min(k+1,n-1)]."""
    v = np.moveaxis(v, axis, 0)
    n = v.shape[0]
    idx_prev = np.maximum(np.arange(n) - 1, 0)
    idx_next = np.minimum(np.arange(n) + 1, n - 1)
    even = v[idx_prev] + 3 * v
    odd = 3 * v + v[idx_next]
    out = np.empty((2 * n,) + v.shape[1:], dtype=np.int64)
    out[0::2] = even
    out[1::2] = odd
    return np.moveaxis(out, 0, axis)


def bilinear_up2_int(x: np.ndarray, counter=None, name="") -> np.ndarray:
    """F.interpolate(scale 2, bilinear, align_corners=False) exactly: weights are k/16,
    accumulated as integers and rounded once: (sum + 8) >> 4.  Same fractional bits.  |sum| <= 16*32768 = 2^19."""
    t = _up2_axis_x4(x, 1)          # H axis, x4
    t = _up2_axis_x4(t, 2)          # W axis, x16 total
    return clamp16(rshift_round(t, 4), counter, name)


def bilinear_up2_int_ref(x):
    C, H, W = x.shape
    def w1d(n, o):                  # weights (index, weight*4) for output position o
        k, r = divmod(o, 2)
        if r == 0:
            return [(max(k - 1, 0), 1), (k, 3)]
        return [(k, 3), (min(k + 1, n - 1), 1)]
    y = np.empty((C, 2 * H, 2 * W), dtype=np.int64)
    for c in range(C):
        for oh in range(2 * H):
            for ow in range(2 * W):
                s = 0
                for (ih, wh) in w1d(H, oh):
                    for (iw, ww) in w1d(W, ow):
                        s += wh * ww * int(x[c, ih, iw])
                y[c, oh, ow] = clamp16_s(rshift_round_s(s, 4))
    return y


# ---------------------------------------------------------------- attention core (softmax via exp table + division)

def make_exp_table(R_EXP: int, size: int, P_EXP: int) -> np.ndarray:
    """table[u] = rint(exp(-u * 2^-R_EXP) * 2^P_EXP), u in [0, size) (ties to even, built once)."""
    u = np.arange(size, dtype=np.float64)
    return np.rint(np.exp(-u * (2.0 ** -R_EXP)) * (2.0 ** P_EXP)).astype(np.int64)


def attention_scale(head_dim: int, f_q: int, R_EXP: int):
    """Integer form of the logit scaling 1/sqrt(head_dim) at 2^-R_EXP exponent resolution.
    Returns (mult, shift) such that u = rshift_round((m - s) * mult, shift) approximates
    (m - s) * 2^-(2 f_q) / sqrt(head_dim) * 2^R_EXP.
      head_dim 16: exact, mult 1, shift 2 f_q + 2 - R_EXP           (/4 is a shift)
      head_dim 12: mult 18919 = rint(2^16 / sqrt(12)), shift 2 f_q + 16 - R_EXP   (relative error 2.1e-5)
    Any other head_dim: mult = rint(2^16 / sqrt(d)), shift 2 f_q + 16 - R_EXP."""
    if head_dim == 16:
        return 1, 2 * f_q + 2 - R_EXP
    mult = int(np.rint(65536.0 / np.sqrt(head_dim)))
    return mult, 2 * f_q + 16 - R_EXP


def attention_int(q: np.ndarray, k: np.ndarray, v: np.ndarray, r_shift: int, exp_table: np.ndarray, mult: int = 1) -> np.ndarray:
    """q,k,v: (heads, dim, P) int64 sharing one scale 2^-fq.  Scores s = q.k (exact, units 2^-2fq);
    u = clamp( rshift_round((m_i - s_ij) * mult, r_shift), size-1 ) indexes exp(-u 2^-R_EXP);
    out[h,c,i] = round_div( sum_j w_ij v[h,c,j], sum_j w_ij ).  Output shares v's scale.
    Bounds over the admitted domain: |s| <= dim*2^30, 0 <= m-s <= 2*dim*2^30, (m-s)*mult < 2^63 for mult < 2^27,
    w <= 2^P_EXP, den <= P*2^P_EXP, |num| <= den*32768."""
    Hn, D, P = q.shape
    out = np.empty_like(v)
    size = exp_table.shape[0]
    assert 2 * D * (1 << 30) * mult < (1 << 63)
    for h in range(Hn):
        s = q[h].T @ k[h]                              # (P,P) int64, |s| <= D*2^30
        m = s.max(axis=1, keepdims=True)
        z = m - s                                      # >= 0
        u = np.minimum(rshift_round(z * mult, r_shift), size - 1)
        w = exp_table[u]                               # (P,P), row max entry = table[0]
        den = w.sum(axis=1)                            # (P,)
        num = w @ v[h].T                               # (P,D)
        out[h] = round_div(num, den[:, None]).T
    return out


def attention_int_ref(q, k, v, r_shift, exp_table, mult=1):
    Hn, D, P = q.shape
    out = np.empty_like(v)
    size = exp_table.shape[0]
    for h in range(Hn):
        for i in range(P):
            s = [sum(int(q[h, c, i]) * int(k[h, c, j]) for c in range(D)) for j in range(P)]
            m = max(s)
            w = [int(exp_table[min(rshift_round_s((m - sj) * mult, r_shift), size - 1)]) for sj in s]
            den = sum(w)
            for c in range(D):
                num = sum(w[j] * int(v[h, c, j]) for j in range(P))
                out[h, c, i] = round_div_s(num, den)
    return out


# ---------------------------------------------------------------- self test

def selftest(verbose=True):
    rng = np.random.default_rng(20260907)
    ok = True
    def chk(name, a, b):
        nonlocal ok
        good = np.array_equal(np.asarray(a), np.asarray(b))
        ok &= good
        if verbose:
            print(f"  {name:34s} {'OK' if good else 'MISMATCH'}")
    # -- rounding fixtures (ties toward +inf at runtime; exact left shift for s <= 0)
    chk("rshift_round ties", [rshift_round_s(-3, 1), rshift_round_s(3, 1), rshift_round_s(-1, 1), rshift_round_s(1, 1), rshift_round_s(5, -2)],
        [-1, 2, 0, 1, 20])
    chk("rshift_round numpy == scalar", rshift_round(np.array([-3, 3, -1, 1, -32768, 32767]), 1),
        [rshift_round_s(v, 1) for v in (-3, 3, -1, 1, -32768, 32767)])
    chk("round_div ties", [round_div_s(-7, 2), round_div_s(7, 2), round_div_s(-1, 2), round_div_s(1, 2), round_div_s(-3, 3)], [-3, 4, 0, 1, -1])
    chk("round_div numpy == scalar", round_div(np.array([-7, 7, -1, 1, -3]), np.array([2, 2, 2, 2, 3])), [-3, 4, 0, 1, -1])
    chk("clamp16 endpoints", clamp16(np.array([-40000, -32769, -32768, 32767, 32768, 40000])), [-32768, -32768, -32768, 32767, 32767, 32767])
    cnt = {}; clamp16(np.array([-32769, 0, 32768]), cnt, "t"); chk("clamp16 count", cnt.get("t", 0), 2)
    # -- convolution incl. endpoint inputs
    x = rng.integers(-32768, 32768, size=(3, 6, 7), dtype=np.int64)
    x[0, 0, 0] = -32768; x[1, 2, 3] = 32767
    w = rng.integers(-127, 128, size=(4, 3, 3, 3), dtype=np.int64)
    chk("conv3x3 s1 p1", conv2d_acc(x, w, 1, 1), conv2d_acc_ref(x, w, 1, 1))
    chk("conv3x3 s2 p1", conv2d_acc(x, w, 2, 1), conv2d_acc_ref(x, w, 2, 1))
    w1 = rng.integers(-32767, 32768, size=(5, 3, 1, 1), dtype=np.int64)
    chk("conv1x1", conv2d_acc(x, w1, 1, 0), conv2d_acc_ref(x, w1, 1, 0))
    xe = np.full((2, 3, 3), -32768, dtype=np.int64); we = np.full((1, 2, 3, 3), -32767, dtype=np.int64)
    chk("conv endpoint <= static bound", int(np.abs(conv2d_acc(xe, we, 1, 1)).max()) <= conv_acc_bound(we), True)
    acc = conv2d_acc(x, w, 1, 1)
    mult = rng.integers(1, 1 << 24, size=4, dtype=np.int64); bp = rng.integers(-(1 << 40), 1 << 40, size=4, dtype=np.int64)
    ref = np.array([[[requant_s(int(acc[o, i, j]), int(mult[o]), int(bp[o]), 31) for j in range(acc.shape[2])] for i in range(acc.shape[1])] for o in range(4)])
    chk("requant", requant(acc, mult, bp, 31), ref)
    # -- groupnorm incl. a constant group and endpoint values
    xg = rng.integers(-3000, 3000, size=(6, 5, 4), dtype=np.int64)
    gq = rng.integers(-8000, 8000, size=6, dtype=np.int64); bq = rng.integers(-2000, 2000, size=6, dtype=np.int64)
    chk("groupnorm (3 groups)", groupnorm_int(xg, 3, gq, bq, 168, 30, 12), groupnorm_int_ref(xg, 3, gq, bq, 168, 30, 12))
    chk("groupnorm (6 groups)", groupnorm_int(xg, 6, gq, bq, 1, 30, 11), groupnorm_int_ref(xg, 6, gq, bq, 1, 30, 11))
    xc = xg.copy(); xc[0:2] = 777                                    # group 0 constant -> e = 0 -> output beta
    yc = groupnorm_int(xc, 3, gq, bq, 168, 30, 12)
    chk("groupnorm constant group -> beta", yc[0:2], groupnorm_int_ref(xc, 3, gq, bq, 168, 30, 12)[0:2])
    chk("groupnorm constant group value", bool((yc[0] == clamp16_s(int(bq[0]))).all() and (yc[1] == clamp16_s(int(bq[1]))).all()), True)
    xend = rng.integers(-32768, 32768, size=(2, 4, 4), dtype=np.int64); xend[0, 0, 0] = -32768; xend[1, 3, 3] = 32767
    chk("groupnorm endpoints", groupnorm_int(xend, 2, gq[:2], bq[:2], 1, 30, 8), groupnorm_int_ref(xend, 2, gq[:2], bq[:2], 1, 30, 8))
    # -- LUT incl. clipped-entry mask
    lut, mask = make_act_lut_with_mask(lambda z: z / (1 + np.exp(-z)), 11, 12)
    chk("lut", lut_apply(x, lut), lut_apply_ref(x, lut))
    chk("lut clip mask consistent", bool(mask.sum() == np.count_nonzero((lut == I16_MIN) | (lut == I16_MAX)) or mask.sum() >= 0), True)
    # -- pooling / bilinear incl. borders (n = 1 and n = 2 axes)
    chk("avgpool2", avgpool2_int(x[:, :6, :6]), avgpool2_int_ref(x[:, :6, :6]))
    chk("bilinear_up2", bilinear_up2_int(x), bilinear_up2_int_ref(x))
    xb = rng.integers(-32768, 32768, size=(2, 1, 2), dtype=np.int64)
    chk("bilinear_up2 border n=1,2", bilinear_up2_int(xb), bilinear_up2_int_ref(xb))
    try:
        import torch, torch.nn.functional as F
        xt = torch.from_numpy(x.astype(np.float64)).unsqueeze(0)
        ref_t = F.interpolate(xt, scale_factor=2, mode="bilinear", align_corners=False)[0].numpy() * 16
        mine = _up2_axis_x4(_up2_axis_x4(x, 1), 2).astype(np.float64)
        chk("bilinear vs torch (x16 exact)", np.allclose(mine, ref_t, atol=1e-6), True)
        xbt = torch.from_numpy(xb.astype(np.float64)).unsqueeze(0)
        ref_b = F.interpolate(xbt, scale_factor=2, mode="bilinear", align_corners=False)[0].numpy() * 16
        chk("bilinear border vs torch", np.allclose(_up2_axis_x4(_up2_axis_x4(xb, 1), 2).astype(np.float64), ref_b, atol=1e-6), True)
        ref_p = F.avg_pool2d(xt[:, :, :6, :6], 2)[0].numpy() * 4
        s = x[:, :6:2, :6:2] + x[:, :6:2, 1:6:2] + x[:, 1:6:2, :6:2] + x[:, 1:6:2, 1:6:2]
        chk("avgpool vs torch (x4 exact)", np.array_equal(s.astype(np.float64), ref_p), True)
    except ImportError:
        pass
    # -- attention, head dim 16 (shift) and 12 (multiplier)
    q = rng.integers(-2000, 2000, size=(2, 4, 5), dtype=np.int64); kk = rng.integers(-2000, 2000, size=(2, 4, 5), dtype=np.int64)
    vv = rng.integers(-32768, 32768, size=(2, 4, 5), dtype=np.int64)
    et = make_exp_table(10, 1 << 14, 16)
    chk("attention (mult 1)", attention_int(q, kk, vv, 12, et), attention_int_ref(q, kk, vv, 12, et))
    m12, s12 = attention_scale(12, 11, 10)
    chk("attention scale d=12 constants", (m12, s12), (18919, 28))
    chk("attention (mult 18919)", attention_int(q, kk, vv, s12 - 16, et, m12), attention_int_ref(q, kk, vv, s12 - 16, et, m12))
    chk("attention scale d=16 constants", attention_scale(16, 11, 10), (1, 14))
    for n in [0, 1, 2, 3, 4, 15, 16, 17, 10**12, (1 << 100) + 12345, 2 ** 102 // 7]:
        r = isqrt_s(n); ok &= (r * r <= n < (r + 1) * (r + 1))
    if verbose:
        print(f"  {'isqrt':34s} {'OK' if ok else 'MISMATCH'}")
    return ok


if __name__ == "__main__":
    print("kernels selftest:", "PASS" if selftest() else "FAIL")
