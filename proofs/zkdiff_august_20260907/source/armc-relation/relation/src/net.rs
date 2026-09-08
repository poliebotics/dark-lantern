//! The network boundary. The integer ARM-C kernels are a sibling crate (`g2_guest/armc-int`, in progress); the
//! relation reaches them only through [`Denoiser`], so the guest, the host oracle and the tests run today with
//! [`StubDenoiser`] and switch to the real network by one adapter (see RELATION.md "Stubbed").
//!
//! Contract: `predict(C_t, hint)` takes the noised frame (4 x 96 x 112 int16 Q12) and the 14-channel hint
//! (14 x 96 x 112 int16 Q14, channels 0..12 the XOF octaves, 12..14 the coordinates) and returns the predicted
//! noise eps (4 x 96 x 112 int16 Q12) together with the number of clipping events the network counted (every
//! clamp outside the admitted int16 domain and every indexed hit on a clipped lookup-table entry, the G1 FINAL
//! contract); the relation adds the noising leg's own count and publishes the total (public bytes 749..752). The
//! relation computes the residual sums itself, so the same noise target is used for both arms by construction. The two digests identify the executed integer function: the constants blob
//! (weights, per-channel multipliers, biases, GroupNorm constants, tables) and the arithmetic specification.

use crate::{Result, FRAME_ELEMS, HINT_CHANNELS, OUT_H, OUT_W};
use sha2::{Digest, Sha256};

pub trait Denoiser {
    /// 0 = stub, 1 = armc-int; published in the statement so a stub run can never pass as a network run.
    fn kind(&self) -> u8;
    /// SHA-256 of the integer constants blob (weights, scales, tables, folded time embedding).
    fn constants_sha256(&self) -> [u8; 32];
    /// SHA-256 of the arithmetic specification (formats, rounding rules, table formulas, layer order).
    fn spec_sha256(&self) -> [u8; 32];
    /// `(eps, clip_events)`: eps = f(C_t, hint, t = 150), int16 Q12, 4 x 96 x 112; clip_events as counted by the
    /// implementation (0 for the stub).
    fn predict(&self, ct: &[i16], hint: &[i16]) -> Result<(Vec<i16>, u32)>;
}

pub const KIND_STUB: u8 = 0;
pub const KIND_ARMC_INT: u8 = 1;

/// A deterministic placeholder that is NOT a network: `eps[c] = clamp16(C_t[c] - (hint[3c] >> 4))`, so the two arms
/// differ through the hint and the whole relation can be executed and oracle-checked end to end.
pub struct StubDenoiser;

pub const STUB_CONSTANTS_TAG: &[u8] = b"ARMC-RELATION-STUB-DENOISER-V0";
pub const STUB_SPEC_TAG: &[u8] = b"ARMC-RELATION-STUB-SPEC-V0";

impl Denoiser for StubDenoiser {
    fn kind(&self) -> u8 {
        KIND_STUB
    }
    fn constants_sha256(&self) -> [u8; 32] {
        Sha256::digest(STUB_CONSTANTS_TAG).into()
    }
    fn spec_sha256(&self) -> [u8; 32] {
        Sha256::digest(STUB_SPEC_TAG).into()
    }
    fn predict(&self, ct: &[i16], hint: &[i16]) -> Result<(Vec<i16>, u32)> {
        if ct.len() != FRAME_ELEMS || hint.len() != HINT_CHANNELS * OUT_H * OUT_W {
            return Err(crate::RelationError("stub denoiser: input shapes differ from 4x96x112 / 14x96x112"));
        }
        let plane = OUT_H * OUT_W;
        let mut eps = Vec::with_capacity(FRAME_ELEMS);
        for c in 0..4 {
            for k in 0..plane {
                let h = hint[3 * c * plane + k] as i64;
                eps.push(crate::fp::clamp16(ct[c * plane + k] as i64 - (h >> 4)));
            }
        }
        Ok((eps, 0))
    }
}

/// Adapter shape for the sibling crate once it lands (kept as documentation, not compiled): implement `Denoiser`
/// for a struct holding `armc_int::blob::Constants`, return `KIND_ARMC_INT`, hash the blob bytes for
/// `constants_sha256`, hash its canonical spec JSON for `spec_sha256`, and call its forward in `predict`.
pub const ARMC_INT_ADAPTER_NOTE: &str = "armc-int adapter: implement Denoiser over armc_int::blob::Constants; kind = 1";

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn stub_is_deterministic_and_hint_sensitive() {
        let ct = vec![1000_i16; FRAME_ELEMS];
        let mut hint = vec![0_i16; HINT_CHANNELS * OUT_H * OUT_W];
        let (a, clips) = StubDenoiser.predict(&ct, &hint).unwrap();
        assert!(a.iter().all(|&v| v == 1000));
        assert_eq!(clips, 0);
        hint[0] = 160; // channel 0 (octave 0, R), first pixel: 160 >> 4 = 10
        let (b, _) = StubDenoiser.predict(&ct, &hint).unwrap();
        assert_eq!(b[0], 990);
        assert_eq!(b[1], 1000);
        hint[3 * OUT_H * OUT_W] = -17; // channel 3 (octave 1, R) feeds eps channel 1; -17 >> 4 = -2 (floor)
        let (c, _) = StubDenoiser.predict(&ct, &hint).unwrap();
        assert_eq!(c[OUT_H * OUT_W], 1002);
        assert_eq!(StubDenoiser.kind(), KIND_STUB);
        assert_ne!(StubDenoiser.constants_sha256(), StubDenoiser.spec_sha256());
    }
}
