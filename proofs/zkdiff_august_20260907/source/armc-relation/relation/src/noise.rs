//! Integer forward noising at t = 150 and the residual sum, G1's fixed-point rules (g1_integer/README.md s.3).
//!
//! ```text
//! q_sample (diffusion_diagnostic_model.py:317-339, cosine schedule s = 0.008, T = 1000, float32 constants):
//!   x_t = sqrt(alphas_cum[t]) * x_0 + sqrt(1 - alphas_cum[t]) * noise
//! integer form, P = 16 fractional bits for the two coefficients:
//!   SA = round(0.9695360064506531 * 2^16) = 63540,  SO = round(0.24494898319244385 * 2^16) = 16053
//!   C_t = clamp16( (SA * C_int + SO * noise_int + 2^15) >> 16 )         (arithmetic shift)
//!   R   = sum_j (eps_j - noise_j)^2   over the 4 x 96 x 112 int16 values, exact (< 2^48)
//!   MSE units: R / (43008 * 2^24)
//! ```
//! The two float32 coefficients are the trainer's `sqrt_alphas_cum[150]` and `sqrt_one_minus_alphas_cum[150]`
//! (vectors_int16_correct.json `noising`). The noise tensor is a witness pinned by its BLAKE3 digest; its
//! correspondence to the evaluator's CUDA Philox stream (one generator per session, seed 20260823, one draw per row
//! in row order, lean_pubproto_eval.py:122-126) is an off-circuit provenance fact, as the Astra verdict states.

use crate::fp::{clamp16_counted, rshift_round};
use crate::{RelationError, Result, FRAME_ELEMS};

pub const TIMESTEP: u32 = 150;
pub const F_CT: u32 = 12;
pub const F_EPS: u32 = 12;
pub const NOISE_SHIFT: u32 = 16;
pub const SA_INT: i64 = 63540;
pub const SO_INT: i64 = 16053;
/// `4 * 96 * 112 * 2^(2 * F_EPS)`: the denominator that turns a residual sum into the evaluator's MSE.
pub const RESIDUAL_DENOMINATOR: u64 = (FRAME_ELEMS as u64) << (2 * F_EPS); // 721_554_505_728
pub const NOISE_BYTES: usize = FRAME_ELEMS * 2;

/// `C_t` from `C_int` and `noise_int` (both int16 Q12), int16 Q12. Returns the saturation count as well: the
/// statement treats a saturation as a fact to publish, never as something to hide.
pub fn forward_noise(c_int: &[i16], noise_int: &[i16]) -> Result<(Vec<i16>, u32)> {
    if c_int.len() != FRAME_ELEMS || noise_int.len() != FRAME_ELEMS {
        return Err(RelationError("forward noising expects 4x96x112 int16 tensors"));
    }
    debug_assert!((SA_INT + SO_INT) * 32768 < (1_i64 << 62));
    let mut sat = 0_u32;
    let out = c_int
        .iter()
        .zip(noise_int.iter())
        .map(|(&c, &n)| clamp16_counted(rshift_round(SA_INT * c as i64 + SO_INT * n as i64, NOISE_SHIFT), &mut sat))
        .collect();
    Ok((out, sat))
}

/// `sum (eps - noise)^2`, exact in u64 (each term < 2^32, 43,008 terms, sum < 2^48).
pub fn residual_sum(eps: &[i16], noise_int: &[i16]) -> Result<u64> {
    if eps.len() != FRAME_ELEMS || noise_int.len() != FRAME_ELEMS {
        return Err(RelationError("residual expects 4x96x112 int16 tensors"));
    }
    let mut acc = 0_u64;
    for (&e, &n) in eps.iter().zip(noise_int.iter()) {
        let d = e as i64 - n as i64;
        acc += (d * d) as u64;
    }
    Ok(acc)
}

/// int16 little-endian bytes -> values.
pub fn i16_from_le(bytes: &[u8]) -> Result<Vec<i16>> {
    if bytes.len() % 2 != 0 {
        return Err(RelationError("int16 byte string has odd length"));
    }
    Ok(bytes.chunks_exact(2).map(|c| i16::from_le_bytes([c[0], c[1]])).collect())
}

/// values -> int16 little-endian bytes.
pub fn i16_to_le(values: &[i16]) -> Vec<u8> {
    values.iter().flat_map(|v| v.to_le_bytes()).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn constants_are_g1s() {
        assert_eq!(RESIDUAL_DENOMINATOR, 721_554_505_728);
        assert_eq!(((0.9695360064506531_f64 * 65536.0).round()) as i64, SA_INT);
        assert_eq!(((0.24494898319244385_f64 * 65536.0).round()) as i64, SO_INT);
    }

    #[test]
    fn noising_and_residual_small_cases() {
        let c = vec![4096_i16; FRAME_ELEMS]; // 1.0
        let n = vec![-4096_i16; FRAME_ELEMS]; // -1.0
        let (ct, sat) = forward_noise(&c, &n).unwrap();
        assert_eq!(sat, 0);
        // (63540 - 16053) * 4096 = 194_506_752; + 32768 >> 16 = 2968 (0.7246 in Q12)
        assert_eq!(ct[0], 2968);
        let eps = vec![0_i16; FRAME_ELEMS];
        assert_eq!(residual_sum(&eps, &n).unwrap(), FRAME_ELEMS as u64 * 4096 * 4096);
        let big = vec![32767_i16; FRAME_ELEMS];
        let (_, sat) = forward_noise(&big, &big).unwrap();
        assert_eq!(sat, FRAME_ELEMS as u32); // ((SA+SO) * 32767 + 2^15) >> 16 = 39795 saturates
    }
}
