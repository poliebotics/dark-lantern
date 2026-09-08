//! Integer kernels of the G1 fixed-point scheme, ported from `g1_integer/kernels.py`
//! (the scalar-loop `*_ref` functions there are the normative definitions).
//!
//! Conventions (README.md section 3 of the oracle):
//! * a tensor is a set of `i16` values with `f` fractional bits, real value `v * 2^-f`;
//! * `rshift_round(v, s) = (v + 2^(s-1)) >> s` with an arithmetic shift (round half up, also
//!   for negative `v`), `s == 0` is the identity;
//! * `round_div(a, b) = floor((2a + b) / (2b))` for `b > 0` (round half up);
//! * `clamp16` saturates to `[-32768, 32767]` and counts every saturation;
//! * `isqrt(m) = floor(sqrt(m))` by integer Newton iteration from a power-of-two overestimate.
//!
//! No floating point anywhere. All arithmetic is `i64` (accumulators, epilogues), `i128`/`u128`
//! only inside GroupNorm's per-group scalar (`X^2 // N`).
//!
//! Two rounding rules (Astra r3 contract on the G1 oracle): the *conversion* of inputs, weights,
//! constants and lookup tables is round-half-to-even and happens offline (`np.rint`); this crate
//! imports the frozen tables and constants from the blob and never regenerates a transcendental.
//! Every *runtime* shift and division rounds half toward +inf (`rshift_round`, `round_div`), and
//! `rshift_round` with `s <= 0` is an exact left shift.
//!
//! Saturation policy (G1 FINAL contract, README_FINAL.md section 3, Astra r4 item 1): the admitted
//! activation domain is the full int16 range `[-32768, 32767]`, both endpoints included. `clamp16`
//! saturates to that domain and counts every element that lay outside it before clipping, exactly
//! as the oracle's `kernels.clamp16` does (fixture: `C = noise = -32767` noises to `-39795`, which
//! clips to `-32768` and counts one event). Lookup-table activations additionally count every
//! indexed hit on a table entry that was itself clipped when the table was built (the oracle's
//! `lut_clipped_hit:<layer>`), using the per-table mask carried by the blob. Every integer input is
//! in domain by type; the oracle's conversion-time input clips (`input:C`, `input:noise`, `input:E`,
//! `input:coord`) happen before the integers exist and are recorded in the artifact manifests (all
//! zero), not observable here. A non-zero counter means the evaluation left the zero-clipping regime
//! covered by the reported validation (the computation stays the specified saturating one); the
//! caller publishes it.
//!
//! Proven bounds (Astra r3, derived from the weights and the domain, not observed on data):
//! * conv accumulators, over every partial sum: `<= 406,605,889,536` (int16 weights) and
//!   `<= 1,576,206,336` (int8 weights) for the width-16 constants; this crate recomputes the bound
//!   per layer as `32768 * max_o sum_k |Wq[o,k]|` ([`ConvLayer::finalize`]) and asserts it once per
//!   output element;
//! * the requantisation expression `acc * M + b' + 2^(S-1)` is `< 2^63` (checked per layer at parse
//!   in 128-bit arithmetic);
//! * GroupNorm: `n <= 32256` elements per group, `N < 2^60`, `X^2` up to 99 bits, the affine
//!   product `e * Mg < 2^55`; so `i64` with operands widened before multiplication suffices
//!   everywhere except the squared numerator, its division and the root, which use `i128`/`u128`;
//! * the residual sum `SSE <= 43008 * 65535^2 = 184,712,316,364,800 < 2^48`.
//!
//! Overflow policy: the crate is compiled with `overflow-checks = true`, so every ordinary `+`, `*`
//! panics on overflow (a hard failure). The single exception is the convolution inner loop, which
//! uses `wrapping_mul`/`wrapping_add` on purpose: with `i16` activations and `i16` (or `i8`)
//! weights the accumulator is bounded by `32767 * max_o sum_k |Wq[o,k]|` (`ConvLayer::acc_bound`,
//! at most 2^39 for the ARM-C constants) and can never reach `i64::MAX`, so wrapping arithmetic
//! is exact there; the bound is asserted once per output element instead of once per MAC.

use crate::tensor::Tensor;
use alloc::vec;
use alloc::vec::Vec;

/// Admitted activation domain: the full int16 range `[-32768, 32767]` (G1 FINAL contract).
pub const DOMAIN_MIN: i64 = -32768;
pub const DOMAIN_MAX: i64 = 32767;
/// Proven conv accumulator bounds for the width-16 constants (Astra r3), for reference and tests.
pub const ACC_BOUND_INT16_W16: i64 = 406_605_889_536;
pub const ACC_BOUND_INT8_W16: i64 = 1_576_206_336;
/// `43008 * 65535^2`: the residual-sum bound for 4 x 96 x 112 values in the admitted domain.
pub const SSE_BOUND_96X112: i64 = 184_712_316_364_800;

// ---------------------------------------------------------------- scalar helpers

/// `(v + 2^(s-1)) >> s` (arithmetic shift, round half toward +inf) for `s > 0`; for `s <= 0` the
/// exact left shift `v << -s` (the oracle's `rshift_round_s`, which is exact in Python's unbounded
/// integers). The left shift is checked to be representable: the result shifted back must give `v`
/// (Astra r4 item 6: `rshift_round(32767, -62)` must not silently go negative), and `-s < 63`.
#[inline(always)]
pub fn rshift_round(v: i64, s: i32) -> i64 {
    if s <= 0 {
        let k = (-s) as u32;
        assert!(k < 63, "left shift amount out of range");
        let r = v << k;
        assert!(r >> k == v, "left shift is not representable in i64");
        r
    } else {
        assert!(s < 64, "right shift amount out of range");
        (v + (1i64 << (s - 1))) >> s
    }
}

/// `floor((2a + b) / (2b))`, `b > 0`.
#[inline(always)]
pub fn round_div(a: i64, b: i64) -> i64 {
    debug_assert!(b > 0);
    (2 * a + b).div_euclid(2 * b)
}

/// Saturate to the admitted domain `[-32768, 32767]`, counting in `sat` every value that lay outside
/// it (the oracle's `clamp16` with a counter).
#[inline(always)]
pub fn clamp16(v: i64, sat: &mut u32) -> i16 {
    if v < DOMAIN_MIN {
        *sat += 1;
        DOMAIN_MIN as i16
    } else if v > DOMAIN_MAX {
        *sat += 1;
        DOMAIN_MAX as i16
    } else {
        v as i16
    }
}

/// Change fractional bits: exact left shift when `f_to > f_from`, round-half-up right shift
/// otherwise (the oracle's `rescale`).
#[inline(always)]
pub fn rescale(v: i64, f_from: u32, f_to: u32) -> i64 {
    rshift_round(v, f_from as i32 - f_to as i32)
}

/// `floor(sqrt(n))` by Newton iteration (the oracle's `isqrt_s`): start at the power of two
/// `2^ceil(bitlen(n)/2)` (an overestimate), iterate `x <- (x + n / x) >> 1` while it decreases.
/// The result is checked against `x^2 <= n < (x+1)^2`, so the iteration count is irrelevant to
/// the value.
pub fn isqrt_u128(n: u128) -> u128 {
    if n < 2 {
        return n;
    }
    let bit_length = 128 - n.leading_zeros();
    let mut x: u128 = 1u128 << ((bit_length + 1) / 2);
    loop {
        let y = (x + n / x) >> 1;
        if y >= x {
            break;
        }
        x = y;
    }
    assert!(x * x <= n && n < (x + 1) * (x + 1), "isqrt postcondition");
    x
}

// ---------------------------------------------------------------- convolution

/// One convolution layer's quantised constants (per-output-channel requantisation).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ConvLayer {
    pub name: alloc::string::String,
    pub out_ch: usize,
    pub in_ch: usize,
    pub kh: usize,
    pub kw: usize,
    pub stride: usize,
    pub pad: usize,
    pub f_in: u32,
    pub f_out: u32,
    /// Requantisation shift `S`.
    pub shift: u32,
    /// Weights `Wq[o, c, ky, kx]`, row-major, values within `[-qmax, qmax]`.
    pub w: Vec<i16>,
    /// Multipliers `M_o`.
    pub m: Vec<i64>,
    /// Pre-shift biases `b'_o`.
    pub bp: Vec<i64>,
    /// `32768 * max_o sum_k |Wq[o, k]|`: static bound on `|acc|` over every partial sum, derived
    /// from the weights for the full `i16` input range (Astra r3: 406,605,889,536 for the int16
    /// width-16 constants, 1,576,206,336 for int8).
    pub acc_bound: i64,
}

impl ConvLayer {
    /// Recompute `acc_bound` from the weights (`32768 * max_o sum_k |Wq[o,k]|`) and check the static
    /// requantisation bound `acc_bound * max(M) + max|b'| + 2^(S-1) < 2^63` in 128-bit arithmetic
    /// (the oracle's static assertion, `int_ref.py` line 312, with the full-range factor).
    pub fn finalize(&mut self) -> Result<(), &'static str> {
        let per_out = self.in_ch * self.kh * self.kw;
        if self.w.len() != self.out_ch * per_out || self.m.len() != self.out_ch || self.bp.len() != self.out_ch {
            return Err("conv layer array sizes");
        }
        let mut worst: i64 = 0;
        for o in 0..self.out_ch {
            let s: i64 = self.w[o * per_out..(o + 1) * per_out].iter().map(|&v| (v as i64).abs()).sum();
            worst = worst.max(s);
        }
        self.acc_bound = 32768 * worst;
        if self.shift == 0 || self.shift > 62 {
            return Err("conv shift out of range");
        }
        let m_max = self.m.iter().copied().max().unwrap_or(0);
        if self.m.iter().any(|&m| m < 0) {
            return Err("negative multiplier");
        }
        let bp_max = self.bp.iter().map(|&b| (b as i128).abs()).max().unwrap_or(0);
        let total = (self.acc_bound as i128) * (m_max as i128) + bp_max + (1i128 << (self.shift - 1));
        if total >= (1i128 << 63) {
            return Err("conv requantisation static bound exceeded");
        }
        Ok(())
    }

    pub fn out_shape(&self, h: usize, w: usize) -> (usize, usize) {
        ((h + 2 * self.pad - self.kh) / self.stride + 1, (w + 2 * self.pad - self.kw) / self.stride + 1)
    }
}

/// Zero-padded copy `(C, H+2, W+2)` of a `(C, H, W)` plane set (pad 1 on every side), so the
/// 3x3 kernels need no border cases. Costs one copy of the input per convolution layer, i.e.
/// `2 / (9 * out_ch)` instructions per MAC, and keeps the inner loop uniform.
fn pad1(x: &[i16], c: usize, h: usize, w: usize) -> Vec<i16> {
    let (hp, wp) = (h + 2, w + 2);
    let mut xp = vec![0i16; c * hp * wp];
    for ci in 0..c {
        for y in 0..h {
            let src = &x[(ci * h + y) * w..(ci * h + y + 1) * w];
            let base = (ci * hp + y + 1) * wp + 1;
            xp[base..base + w].copy_from_slice(src);
        }
    }
    xp
}

/// Register-blocked 3x3 accumulation for `B` adjacent output columns of one output row and one
/// output channel, stride `S` (1 or 2), on the zero-padded input; `SPAN = S * (B - 1) + 3` is the
/// number of input columns read per kernel row (a const parameter so the row is viewed as a
/// fixed-size array and every tap index is a compile-time in-bounds constant). `wo` holds this
/// output channel's `in_ch * 9` weights. Every product is `i16 x i16` widened to `i64` before the
/// multiply; the sum is bounded by `ConvLayer::acc_bound`, so wrapping arithmetic is exact (see
/// the module doc). The `B` accumulators live in registers for the whole `in_ch * 9` reduction.
#[inline(always)]
fn conv3x3_block<const B: usize, const S: usize, const SPAN: usize>(xp: &[i16], in_ch: usize, hp: usize, wp: usize, oy: usize, ox: usize, wo: &[i16]) -> [i64; B] {
    debug_assert_eq!(SPAN, S * (B - 1) + 3);
    let mut acc = [0i64; B];
    let mut plane = 0usize;
    let row0 = (S * oy) * wp + S * ox;
    for ci in 0..in_ch {
        let wk: &[i16; 9] = wo[ci * 9..ci * 9 + 9].try_into().unwrap();
        let mut off = plane + row0;
        for ky in 0..3 {
            let r: &[i16; SPAN] = xp[off..off + SPAN].try_into().unwrap();
            let (w0, w1, w2) = (wk[ky * 3] as i64, wk[ky * 3 + 1] as i64, wk[ky * 3 + 2] as i64);
            for j in 0..B {
                acc[j] = acc[j]
                    .wrapping_add(w0.wrapping_mul(r[S * j] as i64))
                    .wrapping_add(w1.wrapping_mul(r[S * j + 1] as i64))
                    .wrapping_add(w2.wrapping_mul(r[S * j + 2] as i64));
            }
            off += wp;
        }
        plane += hp * wp;
    }
    acc
}

/// Requantise `B` accumulators of one output channel into `out` (one bound check per element).
#[inline(always)]
fn requant_block<const B: usize>(acc: &[i64; B], m: i64, bp: i64, half: i64, shift: u32, bound: i64, name: &str, out: &mut [i16], sat: &mut u32) {
    for j in 0..B {
        let a = acc[j];
        assert!(a >= -bound && a <= bound, "conv {name}: accumulator outside the static bound");
        // bounded by the static check acc_bound * max(M) + max|b'| + 2^(S-1) < 2^63, so wrapping is exact
        let v = a.wrapping_mul(m).wrapping_add(bp).wrapping_add(half) >> shift;
        out[j] = clamp16(v, sat);
    }
}

/// 3x3, pad 1, stride 1 or 2: one output channel over the whole plane, blocks of 8, 4 then 1
/// columns (W = 112, 56, 28, 14, 7 at width 16: tails only at the small levels). One function per
/// stride because `SPAN` must be a literal const (no generic const expressions on stable Rust).
macro_rules! conv3x3_channel {
    ($name:ident, $s:literal, $span8:literal, $span4:literal, $span1:literal) => {
        #[inline(always)]
        fn $name(xp: &[i16], in_ch: usize, hp: usize, wp: usize, ho: usize, wo_: usize, wt: &[i16], m: i64, bp: i64, half: i64, shift: u32, bound: i64, name: &str, out: &mut [i16], sat: &mut u32) {
            for oy in 0..ho {
                let orow = &mut out[oy * wo_..(oy + 1) * wo_];
                let mut ox = 0;
                while ox + 8 <= wo_ {
                    let acc = conv3x3_block::<8, $s, $span8>(xp, in_ch, hp, wp, oy, ox, wt);
                    requant_block::<8>(&acc, m, bp, half, shift, bound, name, &mut orow[ox..ox + 8], sat);
                    ox += 8;
                }
                if ox + 4 <= wo_ {
                    let acc = conv3x3_block::<4, $s, $span4>(xp, in_ch, hp, wp, oy, ox, wt);
                    requant_block::<4>(&acc, m, bp, half, shift, bound, name, &mut orow[ox..ox + 4], sat);
                    ox += 4;
                }
                while ox < wo_ {
                    let acc = conv3x3_block::<1, $s, $span1>(xp, in_ch, hp, wp, oy, ox, wt);
                    requant_block::<1>(&acc, m, bp, half, shift, bound, name, &mut orow[ox..ox + 1], sat);
                    ox += 1;
                }
            }
        }
    };
}
conv3x3_channel!(conv3x3_channel_s1, 1, 10, 6, 3);
conv3x3_channel!(conv3x3_channel_s2, 2, 17, 9, 3);

/// Exact accumulator plane of one output channel, 1x1 kernel, stride 1, pad 0.
/// `wt` holds the `in_ch` weights of this output channel; `acc` (`hw`) must be zero.
fn conv1x1_plane(x: &[i16], in_ch: usize, hw: usize, wt: &[i16], acc: &mut [i64]) {
    let mut ci = 0;
    while ci + 4 <= in_ch {
        let (w0, w1, w2, w3) = (wt[ci] as i64, wt[ci + 1] as i64, wt[ci + 2] as i64, wt[ci + 3] as i64);
        let p0 = &x[ci * hw..(ci + 1) * hw];
        let p1 = &x[(ci + 1) * hw..(ci + 2) * hw];
        let p2 = &x[(ci + 2) * hw..(ci + 3) * hw];
        let p3 = &x[(ci + 3) * hw..(ci + 4) * hw];
        for ((((a, &v0), &v1), &v2), &v3) in acc.iter_mut().zip(p0).zip(p1).zip(p2).zip(p3) {
            *a = a
                .wrapping_add(w0.wrapping_mul(v0 as i64))
                .wrapping_add(w1.wrapping_mul(v1 as i64))
                .wrapping_add(w2.wrapping_mul(v2 as i64))
                .wrapping_add(w3.wrapping_mul(v3 as i64));
        }
        ci += 4;
    }
    while ci < in_ch {
        let w0 = wt[ci] as i64;
        let p0 = &x[ci * hw..(ci + 1) * hw];
        for (a, &v0) in acc.iter_mut().zip(p0) {
            *a = a.wrapping_add(w0.wrapping_mul(v0 as i64));
        }
        ci += 1;
    }
}

/// Generic exact accumulator plane (any kernel, stride, pad): the scalar definition
/// (`conv2d_acc_ref`). Used as the reference for the fast paths in the tests and as the fallback
/// for any geometry the fast paths do not cover.
pub fn conv_generic_plane(
    x: &[i16],
    in_ch: usize,
    h: usize,
    w: usize,
    kh: usize,
    kw: usize,
    stride: usize,
    pad: usize,
    wt: &[i16],
    acc: &mut [i64],
) {
    let ho = (h + 2 * pad - kh) / stride + 1;
    let wo = (w + 2 * pad - kw) / stride + 1;
    debug_assert_eq!(acc.len(), ho * wo);
    for oy in 0..ho {
        for ox in 0..wo {
            let mut s: i64 = 0;
            for ci in 0..in_ch {
                for ky in 0..kh {
                    let iy = (oy * stride + ky) as isize - pad as isize;
                    if iy < 0 || iy >= h as isize {
                        continue;
                    }
                    for kx in 0..kw {
                        let ix = (ox * stride + kx) as isize - pad as isize;
                        if ix < 0 || ix >= w as isize {
                            continue;
                        }
                        let wv = wt[(ci * kh + ky) * kw + kx] as i64;
                        let xv = x[(ci * h + iy as usize) * w + ix as usize] as i64;
                        s = s.wrapping_add(wv.wrapping_mul(xv));
                    }
                }
            }
            acc[oy * wo + ox] = s;
        }
    }
}

/// Full convolution: exact integer accumulation then
/// `y = clamp16((acc * M_o + b'_o + 2^(S-1)) >> S)` per output channel.
pub fn conv2d(x: &Tensor, l: &ConvLayer, sat: &mut u32) -> Tensor {
    assert_eq!(x.c, l.in_ch, "conv {}: input channels", l.name);
    assert_eq!(x.f, l.f_in, "conv {}: input fractional bits", l.name);
    let (ho, wo) = l.out_shape(x.h, x.w);
    let per_out = l.in_ch * l.kh * l.kw;
    let mut out = vec![0i16; l.out_ch * ho * wo];
    let half = 1i64 << (l.shift - 1);
    let bound = l.acc_bound;
    let padded3 = l.kh == 3 && l.kw == 3 && l.pad == 1 && (l.stride == 1 || l.stride == 2);
    if padded3 {
        let xp = pad1(&x.v, x.c, x.h, x.w);
        let (hp, wp) = (x.h + 2, x.w + 2);
        for o in 0..l.out_ch {
            let wt = &l.w[o * per_out..(o + 1) * per_out];
            let dst = &mut out[o * ho * wo..(o + 1) * ho * wo];
            if l.stride == 1 {
                conv3x3_channel_s1(&xp, l.in_ch, hp, wp, ho, wo, wt, l.m[o], l.bp[o], half, l.shift, bound, &l.name, dst, sat);
            } else {
                conv3x3_channel_s2(&xp, l.in_ch, hp, wp, ho, wo, wt, l.m[o], l.bp[o], half, l.shift, bound, &l.name, dst, sat);
            }
        }
        return Tensor { c: l.out_ch, h: ho, w: wo, f: l.f_out, v: out };
    }
    let fast1 = l.kh == 1 && l.kw == 1 && l.stride == 1 && l.pad == 0;
    let mut acc = vec![0i64; ho * wo];
    for o in 0..l.out_ch {
        for a in acc.iter_mut() {
            *a = 0;
        }
        let wt = &l.w[o * per_out..(o + 1) * per_out];
        if fast1 {
            conv1x1_plane(&x.v, l.in_ch, x.h * x.w, wt, &mut acc);
        } else {
            conv_generic_plane(&x.v, l.in_ch, x.h, x.w, l.kh, l.kw, l.stride, l.pad, wt, &mut acc);
        }
        let (m, bp) = (l.m[o], l.bp[o]);
        for (y, &a) in out[o * ho * wo..(o + 1) * ho * wo].iter_mut().zip(acc.iter()) {
            // one bound check per output element instead of one per MAC
            assert!(a >= -bound && a <= bound, "conv {}: accumulator outside the static bound", l.name);
            // bounded by the static check acc_bound * max(M) + max|b'| + 2^(S-1) < 2^63, so wrapping is exact
            *y = clamp16(a.wrapping_mul(m).wrapping_add(bp).wrapping_add(half) >> l.shift, sat);
        }
    }
    Tensor { c: l.out_ch, h: ho, w: wo, f: l.f_out, v: out }
}

// ---------------------------------------------------------------- GroupNorm

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct GnLayer {
    pub name: alloc::string::String,
    pub channels: usize,
    pub groups: usize,
    /// `max(1, round(eps * 2^(2 f_in)))`.
    pub eps_int: i64,
    pub f_in: u32,
    pub f_out: u32,
    /// `round(gamma * 2^12)`.
    pub gamma_q: Vec<i64>,
    /// `round(beta * 2^f_out)`.
    pub beta_q: Vec<i64>,
}

/// Exact-statistics GroupNorm (`groupnorm_int_ref`), `T` extra bits for the normaliser (30).
pub fn groupnorm(x: &Tensor, l: &GnLayer, t: u32, sat: &mut u32) -> Tensor {
    assert_eq!(x.c, l.channels, "gn {}: channels", l.name);
    assert_eq!(x.f, l.f_in, "gn {}: input fractional bits", l.name);
    assert!(l.groups > 0 && x.c % l.groups == 0, "gn {}: groups", l.name);
    let cpg = x.c / l.groups;
    let hw = x.h * x.w;
    let n = (cpg * hw) as i64;
    // S2 <= n * 2^30 must fit i64 (the oracle asserts n * 32768^2 < 2^63)
    assert!((n as i128) * (1i128 << 30) < (1i128 << 62), "gn {}: group too large", l.name);
    let big_x: u128 = (n as u128) << (l.f_out + t - 6);
    let mut out = vec![0i16; x.v.len()];
    for g in 0..l.groups {
        let seg = &x.v[g * cpg * hw..(g + 1) * cpg * hw];
        let (mut s1, mut s2) = (0i64, 0i64);
        for &v in seg {
            let v = v as i64;
            s1 = s1.wrapping_add(v);
            s2 = s2.wrapping_add(v.wrapping_mul(v));
        }
        assert!(s2 >= 0 && s2 <= n * (1i64 << 30), "gn {}: S2 bound", l.name);
        let nn = n as i128;
        let big_n: i128 = nn * (s2 as i128) - (s1 as i128) * (s1 as i128) + nn * nn * (l.eps_int as i128);
        assert!(big_n > 0, "gn {}: N <= 0", l.name);
        let q = isqrt_u128((big_x * big_x) / (big_n as u128));
        assert!(q < (1u128 << 40), "gn {}: Q bound", l.name);
        let q = q as i64;
        let mu6 = round_div(64 * s1, n);
        for k in 0..cpg {
            let ch = g * cpg + k;
            let mg = round_div(l.gamma_q[ch] * q, 1i64 << 12);
            assert!(mg.abs() < (1i64 << 39), "gn {}: Mg bound", l.name);
            let beta = l.beta_q[ch];
            let src = &x.v[ch * hw..(ch + 1) * hw];
            let dst = &mut out[ch * hw..(ch + 1) * hw];
            for (y, &v) in dst.iter_mut().zip(src) {
                let e = 64 * (v as i64) - mu6;
                *y = clamp16(rshift_round(e * mg, t as i32) + beta, sat);
            }
        }
    }
    Tensor { c: x.c, h: x.h, w: x.w, f: l.f_out, v: out }
}

// ---------------------------------------------------------------- lookup-table activations

/// Bytes of a 65536-entry clipping mask stored as a bitset, LSB first (`mask[i] = bit i`).
pub const LUT_MASK_BYTES: usize = 65536 / 8;

/// `mask[i]`: was table entry `i` clipped to the admitted domain when the table was built?
#[inline(always)]
pub fn lut_mask_bit(mask: &[u8], i: usize) -> bool {
    (mask[i >> 3] >> (i & 7)) & 1 == 1
}

/// Number of set bits of a mask (the oracle's `clipped_entries`).
pub fn lut_mask_popcount(mask: &[u8]) -> u32 {
    mask.iter().map(|b| b.count_ones()).sum()
}

/// `y = table[x + 32768]`, the table being a 65536-entry `i16` LUT for one `(kind, f_in, f_out)`;
/// every indexed hit on a masked (clipped) entry counts one clipping event in `sat` (the oracle's
/// `lut_clipped_hit:<layer>`).
pub fn lut_apply(x: &Tensor, table: &[i16], mask: &[u8], f_out: u32, sat: &mut u32) -> Tensor {
    assert_eq!(table.len(), 65536, "lut size");
    assert_eq!(mask.len(), LUT_MASK_BYTES, "lut mask size");
    let table: &[i16; 65536] = table.try_into().expect("lut size");
    let mask: &[u8; LUT_MASK_BYTES] = mask.try_into().expect("lut mask size");
    let mut hits = 0u32;
    let v: Vec<i16> = x
        .v
        .iter()
        .map(|&xv| {
            let i = (xv as i32 + 32768) as usize;
            hits += ((mask[i >> 3] >> (i & 7)) & 1) as u32;
            table[i]
        })
        .collect();
    *sat += hits;
    Tensor { c: x.c, h: x.h, w: x.w, f: f_out, v }
}

// ---------------------------------------------------------------- pooling and resampling

/// 2x2 average pool, stride 2: `clamp16((a + b + c + d + 2) >> 2)`, same fractional bits.
pub fn avgpool2(x: &Tensor, sat: &mut u32) -> Tensor {
    assert!(x.h % 2 == 0 && x.w % 2 == 0, "avgpool2 needs even H and W");
    let (ho, wo) = (x.h / 2, x.w / 2);
    let mut out = vec![0i16; x.c * ho * wo];
    for c in 0..x.c {
        let plane = &x.v[c * x.h * x.w..(c + 1) * x.h * x.w];
        for oy in 0..ho {
            let r0 = &plane[(2 * oy) * x.w..(2 * oy + 1) * x.w];
            let r1 = &plane[(2 * oy + 1) * x.w..(2 * oy + 2) * x.w];
            let dst = &mut out[(c * ho + oy) * wo..(c * ho + oy + 1) * wo];
            for ox in 0..wo {
                let s = r0[2 * ox] as i64 + r0[2 * ox + 1] as i64 + r1[2 * ox] as i64 + r1[2 * ox + 1] as i64;
                dst[ox] = clamp16(rshift_round(s, 2), sat);
            }
        }
    }
    Tensor { c: x.c, h: ho, w: wo, f: x.f, v: out }
}

/// Bilinear x2 upsample, `align_corners=False`, exactly: per axis `out[2k] = in[max(k-1,0)] + 3 in[k]`,
/// `out[2k+1] = 3 in[k] + in[min(k+1,n-1)]` (x4 each axis), then `clamp16((sum + 8) >> 4)`.
pub fn bilinear_up2(x: &Tensor, sat: &mut u32) -> Tensor {
    let (h, w) = (x.h, x.w);
    let (h2, w2) = (2 * h, 2 * w);
    let mut out = vec![0i16; x.c * h2 * w2];
    // H axis into an i32 temporary (|t| <= 2^17)
    let mut t = vec![0i32; h2 * w];
    for c in 0..x.c {
        let plane = &x.v[c * h * w..(c + 1) * h * w];
        for k in 0..h {
            let prev = if k == 0 { 0 } else { k - 1 };
            let next = if k + 1 >= h { h - 1 } else { k + 1 };
            let (rp, rk, rn) = (&plane[prev * w..(prev + 1) * w], &plane[k * w..(k + 1) * w], &plane[next * w..(next + 1) * w]);
            let (te, to) = t.split_at_mut((2 * k + 1) * w);
            let te = &mut te[2 * k * w..];
            let to = &mut to[..w];
            for j in 0..w {
                te[j] = rp[j] as i32 + 3 * rk[j] as i32;
                to[j] = 3 * rk[j] as i32 + rn[j] as i32;
            }
        }
        // W axis then rounding (|u| <= 2^19)
        for oy in 0..h2 {
            let row = &t[oy * w..(oy + 1) * w];
            let dst = &mut out[(c * h2 + oy) * w2..(c * h2 + oy + 1) * w2];
            for j in 0..w {
                let prev = if j == 0 { 0 } else { j - 1 };
                let next = if j + 1 >= w { w - 1 } else { j + 1 };
                let even = row[prev] as i64 + 3 * row[j] as i64;
                let odd = 3 * row[j] as i64 + row[next] as i64;
                dst[2 * j] = clamp16(rshift_round(even, 4), sat);
                dst[2 * j + 1] = clamp16(rshift_round(odd, 4), sat);
            }
        }
    }
    Tensor { c: x.c, h: h2, w: w2, f: x.f, v: out }
}

// ---------------------------------------------------------------- residual add, concat

/// Both operands to `max(f_a, f_b)` by exact left shift, add, one rounding to `f_out`, clamp.
pub fn add(a: &Tensor, b: &Tensor, f_out: u32, sat: &mut u32) -> Tensor {
    assert!(a.c == b.c && a.h == b.h && a.w == b.w, "add: shapes");
    let fm = a.f.max(b.f);
    let v: Vec<i16> = a
        .v
        .iter()
        .zip(&b.v)
        .map(|(&av, &bv)| {
            let s = rescale(av as i64, a.f, fm) + rescale(bv as i64, b.f, fm);
            clamp16(rescale(s, fm, f_out), sat)
        })
        .collect();
    Tensor { c: a.c, h: a.h, w: a.w, f: f_out, v }
}

/// Channel concat `[a, b]`, each half rescaled to `f_out` and clamped.
pub fn cat(a: &Tensor, b: &Tensor, f_out: u32, sat: &mut u32) -> Tensor {
    assert!(a.h == b.h && a.w == b.w, "cat: spatial shapes");
    let mut v = Vec::with_capacity(a.v.len() + b.v.len());
    v.extend(a.v.iter().map(|&av| clamp16(rescale(av as i64, a.f, f_out), sat)));
    v.extend(b.v.iter().map(|&bv| clamp16(rescale(bv as i64, b.f, f_out), sat)));
    Tensor { c: a.c + b.c, h: a.h, w: a.w, f: f_out, v }
}

// ---------------------------------------------------------------- attention

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AttnLayer {
    pub name: alloc::string::String,
    /// Shared scale of q, k, v (the qkv conv's `f_out`).
    pub f_qkv: u32,
    /// Logit-scale multiplier: 1 for head_dim 16 (1/sqrt(16) is a shift), `rint(2^16 / sqrt(head_dim))` otherwise
    /// (`kernels.attention_scale`; 18919 for head_dim 12).
    pub mult: i64,
    /// `2 f_qkv + 2 - R_EXP` for mult 1; `2 f_qkv + 16 - R_EXP` otherwise.
    pub r_shift: u32,
    /// Tokens `H * W` this layer was calibrated for (informational; the kernel uses the input).
    pub tokens: usize,
}

/// Softmax attention with the exp table (`attention_int_ref`). `qkv` is `(3C, H, W)` at `f_qkv`;
/// `heads` heads of dimension `C / heads`; scores `s_ij = sum_c q_ic k_jc` exactly;
/// `u_ij = min(rshift_round((m_i - s_ij) * mult, r_shift), size - 1)`, `w_ij = EXP[u_ij]`,
/// `out_ic = round_div(sum_j w_ij v_jc, sum_j w_ij)`. Output `(C, H, W)` at `f_qkv`.
pub fn attention(qkv: &Tensor, heads: usize, mult: i64, r_shift: u32, exp_table: &[u32], sat: &mut u32) -> Tensor {
    assert!(qkv.c % 3 == 0, "attention: qkv channels");
    let c = qkv.c / 3;
    assert!(c % heads == 0, "attention: heads");
    let d = c / heads;
    let p = qkv.h * qkv.w;
    let size = exp_table.len() as i64;
    assert!(size > 0);
    // bounds as in the oracle: |s| <= d * 2^30 < 2^62; (m - s) * mult < 2^63; 2 * P * 2^P_EXP * 2^15 + P * 2^P_EXP < 2^63
    let exp_max = exp_table.iter().copied().max().unwrap_or(0) as i128;
    assert!(mult >= 1, "attention: multiplier");
    assert!((d as i128) * (1i128 << 30) < (1i128 << 62));
    assert!(2 * (d as i128) * (1i128 << 30) * (mult as i128) < (1i128 << 63), "attention: scaled difference bound");
    assert!(2 * (p as i128) * exp_max * (1i128 << 15) + (p as i128) * exp_max < (1i128 << 63), "attention: num bound");
    let mut out = vec![0i16; c * p];
    let mut s = vec![0i64; p];
    let mut wts = vec![0i64; p];
    for hd in 0..heads {
        let q = &qkv.v[hd * d * p..(hd + 1) * d * p];
        let k = &qkv.v[(c + hd * d) * p..(c + (hd + 1) * d) * p];
        let v = &qkv.v[(2 * c + hd * d) * p..(2 * c + (hd + 1) * d) * p];
        for i in 0..p {
            for sv in s.iter_mut() {
                *sv = 0;
            }
            for ch in 0..d {
                let qv = q[ch * p + i] as i64;
                let krow = &k[ch * p..(ch + 1) * p];
                for (sv, &kv) in s.iter_mut().zip(krow) {
                    *sv += qv * kv as i64;
                }
            }
            let m = s.iter().copied().max().unwrap();
            let mut den: i64 = 0;
            for (wv, &sv) in wts.iter_mut().zip(s.iter()) {
                let u = rshift_round((m - sv) * mult, r_shift as i32).min(size - 1);
                let e = exp_table[u as usize] as i64;
                *wv = e;
                den += e;
            }
            assert!(den > 0, "attention: zero denominator");
            for ch in 0..d {
                let vrow = &v[ch * p..(ch + 1) * p];
                let mut num: i64 = 0;
                for (&wv, &vv) in wts.iter().zip(vrow) {
                    num += wv * vv as i64;
                }
                // a convex combination of in-domain values stays in domain; clamp16 enforces and counts
                out[(hd * d + ch) * p + i] = clamp16(round_div(num, den), sat);
            }
        }
    }
    Tensor { c, h: qkv.h, w: qkv.w, f: qkv.f, v: out }
}

// ---------------------------------------------------------------- inputs, noising, score

/// Integer `q_sample`: `C_t = clamp16(rshift_round(SA * C + SO * noise, P))` (C, noise and C_t
/// share the same fractional bits).
pub fn noise_ct(c_int: &[i16], noise_int: &[i16], sa: i64, so: i64, p: u32, sat: &mut u32) -> Vec<i16> {
    assert_eq!(c_int.len(), noise_int.len());
    assert!(((sa + so) as i128) * 32768 < (1i128 << 62), "noising bound");
    c_int
        .iter()
        .zip(noise_int)
        .map(|(&cv, &nv)| clamp16(rshift_round(sa * cv as i64 + so * nv as i64, p as i32), sat))
        .collect()
}

/// The score: `R = sum (eps - noise)^2`, exact in `i64` (`< 2^48` for 43008 values).
pub fn residual_sum(eps: &[i16], noise_int: &[i16]) -> i64 {
    assert_eq!(eps.len(), noise_int.len());
    let mut r: i64 = 0;
    for (&e, &n) in eps.iter().zip(noise_int) {
        let d = e as i64 - n as i64;
        r += d * d;
    }
    debug_assert!(r <= (eps.len() as i64) * 65535 * 65535);
    r
}
