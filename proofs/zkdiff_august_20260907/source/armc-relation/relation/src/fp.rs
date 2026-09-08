//! Rounding and float-format primitives, all specified exactly.
//!
//! Two families live here. Integer rounding for the fixed-point statement (`round_div_half_even`, `rshift_round`,
//! `clamp16`, G1's rules). IEEE conversions for the pipeline-faithful input path: the training/eval pipeline stores
//! the reduced tensors as float16 (precache.py:41-42), reloads them as float32 (train_lean.py:123/139) and casts
//! them to bfloat16 (lean_pubproto_eval.py:125/130) before G1 quantises with `rint(x * 2^f)` (int_ref.py:266/274).
//! `f32_to_f16_bits` is IEEE-754 round-to-nearest-even including the subnormal range (numpy `astype(float16)`);
//! `f32_to_bf16_bits` is round-to-nearest-even on the bit pattern (torch `c10::BFloat16::round_to_nearest_even`).
//! Both are tested against 8,192 numpy/torch vectors including injected exact ties (vectors_relation/conv/).

/// `round(num / den)` with ties to even, for `den > 0` and any sign of `num` (Python `round(Fraction(num, den))`).
pub fn round_div_half_even(num: i128, den: i128) -> i128 {
    debug_assert!(den > 0);
    let q = num.div_euclid(den);
    let r = num.rem_euclid(den); // 0 <= r < den
    let twice = 2 * r;
    if twice > den || (twice == den && (q & 1) == 1) {
        q + 1
    } else {
        q
    }
}

/// G1 `rshift_round(v, s) = (v + 2^(s-1)) >> s` with an arithmetic (floor) shift: round half toward +inf.
pub fn rshift_round(v: i64, s: u32) -> i64 {
    debug_assert!(s > 0 && s < 63);
    (v + (1_i64 << (s - 1))) >> s
}

/// Saturate to int16.
pub fn clamp16(v: i64) -> i16 {
    v.clamp(-32768, 32767) as i16
}

/// Saturate to int16 and report whether saturation happened.
pub fn clamp16_counted(v: i64, saturations: &mut u32) -> i16 {
    if v < -32768 || v > 32767 {
        *saturations += 1;
    }
    clamp16(v)
}

/// IEEE-754 binary32 -> binary16, round to nearest, ties to even. Subnormal results are rounded on the
/// 2^-24 grid; NaN becomes a quiet NaN; overflow becomes infinity.
pub fn f32_to_f16_bits(x: f32) -> u16 {
    let bits = x.to_bits();
    let sign = ((bits >> 16) & 0x8000) as u16;
    let exp = ((bits >> 23) & 0xff) as i32;
    let mant = bits & 0x007f_ffff;
    if exp == 0xff {
        // inf or nan
        return sign | 0x7c00 | if mant != 0 { 0x0200 } else { 0 };
    }
    let e = exp - 127 + 15; // binary16 biased exponent of the same value
    if e >= 0x1f {
        return sign | 0x7c00;
    }
    if e <= 0 {
        // binary16 subnormal (or zero): value = M * 2^-24 with M = (1.mant) * 2^(exp-127+24)
        if exp == 0 {
            return sign; // binary32 zero or subnormal: far below the binary16 grid
        }
        let m = mant | 0x0080_0000; // 24-bit significand
        let shift = (14 - e) as u32; // M = m >> shift, shift >= 14
        if shift > 24 {
            return sign; // below half of the smallest subnormal
        }
        let q = m >> shift;
        let rem = m & ((1_u32 << shift) - 1);
        let half = 1_u32 << (shift - 1);
        let q = if rem > half || (rem == half && (q & 1) == 1) { q + 1 } else { q };
        return sign | q as u16; // q == 0x400 is the smallest normal, which this encoding gives naturally
    }
    let q = mant >> 13;
    let rem = mant & 0x1fff;
    let mut r = ((e as u32) << 10) | q;
    if rem > 0x1000 || (rem == 0x1000 && (q & 1) == 1) {
        r += 1; // may carry into the exponent; e == 30 with carry gives 0x7c00 = inf, which is correct
    }
    sign | r as u16
}

/// binary16 -> binary32, exact.
pub fn f16_bits_to_f32(h: u16) -> f32 {
    let sign = ((h & 0x8000) as u32) << 16;
    let exp = ((h >> 10) & 0x1f) as u32;
    let mant = (h & 0x03ff) as u32;
    let bits = if exp == 0 {
        if mant == 0 {
            sign
        } else {
            // subnormal: value = mant * 2^-24; normalise
            let mut m = mant;
            let mut e: i32 = 127 - 15 + 1; // exponent of a normal with the same leading bit position
            while m & 0x0400 == 0 {
                m <<= 1;
                e -= 1;
            }
            sign | ((e as u32) << 23) | ((m & 0x03ff) << 13)
        }
    } else if exp == 0x1f {
        sign | 0x7f80_0000 | (mant << 13)
    } else {
        sign | ((exp + 127 - 15) << 23) | (mant << 13)
    };
    f32::from_bits(bits)
}

/// binary32 -> bfloat16 bits, round to nearest even on the bit pattern (c10::BFloat16 semantics).
pub fn f32_to_bf16_bits(x: f32) -> u16 {
    let bits = x.to_bits();
    if x.is_nan() {
        return ((bits >> 16) | 0x0040) as u16;
    }
    let lsb = (bits >> 16) & 1;
    ((bits.wrapping_add(0x7fff + lsb)) >> 16) as u16
}

/// bfloat16 bits -> binary32, exact.
pub fn bf16_bits_to_f32(b: u16) -> f32 {
    f32::from_bits((b as u32) << 16)
}

/// The pipeline's quantisation of one area-mean value x: `clamp16(rint(bf16(f32(f16(x))) * 2^f))`
/// (precache float16 cache -> float32 -> bfloat16 -> G1 `np.rint` at scale 2^f). The product by 2^f is exact in
/// binary32 for the magnitudes here (|x| <= 1, f <= 14), and `round_ties_even` is numpy's `rint`.
pub fn cache_quant(x: f32, f: u32) -> i16 {
    let cached = f16_bits_to_f32(f32_to_f16_bits(x));
    let bf = bf16_bits_to_f32(f32_to_bf16_bits(cached));
    let scaled = bf * (1_u32 << f) as f32;
    let r = scaled.round_ties_even();
    clamp16(r as i64)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn half_even_division_matches_python_round_on_fractions() {
        assert_eq!(round_div_half_even(5, 2), 2); // 2.5 -> 2
        assert_eq!(round_div_half_even(7, 2), 4); // 3.5 -> 4
        assert_eq!(round_div_half_even(-5, 2), -2); // -2.5 -> -2
        assert_eq!(round_div_half_even(-7, 2), -4); // -3.5 -> -4
        assert_eq!(round_div_half_even(1, 3), 0);
        assert_eq!(round_div_half_even(2, 3), 1);
        assert_eq!(round_div_half_even(-1, 3), 0);
        assert_eq!(round_div_half_even(-2, 3), -1);
        assert_eq!(round_div_half_even(0, 7), 0);
    }

    #[test]
    fn g1_rshift_round_is_half_up_with_floor_shift() {
        assert_eq!(rshift_round(3, 1), 2); // 1.5 -> 2
        assert_eq!(rshift_round(1, 1), 1); // 0.5 -> 1
        assert_eq!(rshift_round(-1, 1), 0); // -0.5 -> 0
        assert_eq!(rshift_round(-3, 1), -1); // -1.5 -> -1
        assert_eq!(rshift_round(-4, 2), -1);
        assert_eq!(rshift_round(-5, 2), -1); // -1.25 -> -1
        assert_eq!(rshift_round(-7, 2), -2); // -1.75 -> -2
    }

    #[test]
    fn f16_round_trips_and_known_values() {
        assert_eq!(f32_to_f16_bits(1.0), 0x3c00);
        assert_eq!(f32_to_f16_bits(-2.0), 0xc000);
        assert_eq!(f32_to_f16_bits(0.0), 0x0000);
        assert_eq!(f32_to_f16_bits(-0.0), 0x8000);
        assert_eq!(f32_to_f16_bits(65504.0), 0x7bff);
        assert_eq!(f32_to_f16_bits(65520.0), 0x7c00); // rounds to inf
        assert_eq!(f32_to_f16_bits(5.960464477539063e-08), 0x0001); // smallest subnormal
        assert_eq!(f32_to_f16_bits(2.9802322387695312e-08), 0x0000); // exactly half of it: tie to even (0)
        assert_eq!(f32_to_f16_bits(8.940696716308594e-08), 0x0002); // 1.5 * smallest: tie to even (2)
        assert_eq!(f32_to_f16_bits(6.103515625e-05), 0x0400); // smallest normal
        for h in [0x0001_u16, 0x03ff, 0x0400, 0x3c00, 0x7bff, 0x8001, 0xbc00, 0x1234, 0x5678] {
            assert_eq!(f32_to_f16_bits(f16_bits_to_f32(h)), h, "{h:#06x}");
        }
        assert!(f16_bits_to_f32(0x7c00).is_infinite());
        assert!(f16_bits_to_f32(0x7e00).is_nan());
    }

    #[test]
    fn bf16_known_values() {
        assert_eq!(f32_to_bf16_bits(1.0), 0x3f80);
        assert_eq!(f32_to_bf16_bits(f32::from_bits(0x3f80_8000)), 0x3f80); // exact tie, even stays
        assert_eq!(f32_to_bf16_bits(f32::from_bits(0x3f81_8000)), 0x3f82); // exact tie, odd rounds up
        assert_eq!(f32_to_bf16_bits(f32::from_bits(0x3f80_8001)), 0x3f81);
        assert_eq!(bf16_bits_to_f32(0x3f80), 1.0);
    }
}
