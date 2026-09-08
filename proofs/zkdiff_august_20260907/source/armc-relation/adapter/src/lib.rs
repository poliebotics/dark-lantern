//! The real network behind `armc_relation::net::Denoiser`: the `armc-int` integer ARM-C denoiser (G1 fixed-point
//! scheme, int16 weights), parameterised by a constants blob that arrives as a private input and is identified in
//! the public statement by its SHA-256 (`constants_sha256`) together with the digest of the arithmetic
//! specification below (`spec_sha256`). `kind()` is 1, so a statement carrying this adapter can never be confused
//! with the stub's.
//!
//! What the adapter checks, and refuses on failure (every refusal is a static `RelationError`):
//! * the blob parses (`armc_int::blob::Constants::parse`, which runs the static bound checks of every layer);
//! * the blob's geometry and fixed-point constants equal the relation's compiled ones: 96 x 112, `F_CT = 12`,
//!   `F_HINT = 14`, `F_EPS = 12`, `SA = 63540`, `SO = 16053`, noise shift 16, int16 weights (`qmax = 32767`);
//! * the two coordinate planes the relation derives (`hint::coord_int`, hint channels 12 and 13) equal the blob's
//!   coordinate planes byte for byte, so the network is evaluated on exactly the 14-channel hint the relation built;
//! * every clipping event of the forward pass is counted and returned to the relation, which publishes the total
//!   (every clamp outside the admitted int16 domain and every indexed hit on a clipped lookup-table entry, the G1
//!   FINAL contract; the G1 record shows zero events over every row it evaluated, so a nonzero public count marks an
//!   evaluation outside the zero-clipping regime covered by the reported validation, published rather than hidden or
//!   refused: the proof remains valid for the specified saturating computation, and 65535 means at least 65535).
//!
//! The same-noise-both-arms property is the relation's: `statement::evaluate` computes `C_t` once, calls `predict`
//! twice (hint of row r, hint of row u) and forms both residual sums against the one noise witness whose BLAKE3 is
//! public. The adapter is stateless across the two calls.

use armc_int::blob::Constants;
use armc_int::model::{Net, NoHook};
use armc_int::Tensor;
use armc_relation::net::{Denoiser, KIND_ARMC_INT};
use armc_relation::noise::{F_CT, F_EPS, NOISE_SHIFT, SA_INT, SO_INT};
use armc_relation::{RelationError, Result, FRAME_CHANNELS, FRAME_ELEMS, HINT_CHANNELS, HINT_E_CHANNELS, OUT_H, OUT_W};
use sha2::{Digest, Sha256};

/// The arithmetic specification of the executed integer function, canonical one-line JSON, compiled in and hashed
/// into the statement. It states what `armc-int` does (g1_integer/final/README_FINAL.md section 3 as ported, the
/// full int16 domain admitted and every clip counted, Astra r4). Change one character and the published digest
/// changes; `spec_digest_is_pinned` fails if the text drifts.
pub const ARMC_INT_SPEC_CANONICAL_JSON: &str = concat!(
    "{\"id\":\"ARMC_INT_SPEC_V2\",\"crate\":\"armc-int 0.1.0 (g2_guest/armc-int, blob ARMCINT1 v2)\",",
    "\"program\":\"DiffusionDiagnosticUNet/ArmCUNet: hint=cat(E 12ch Q14, coord 2ch Q14); hint encoder 4x(conv3x3 s2, GroupNorm, GELU); ",
    "in_conv; 4 levels x 2 ResBlocks (GN-SiLU-conv3x3 (+folded t=150 bias), GN-SiLU-conv3x3, +skip or 1x1 skip conv), attention at level 3, ",
    "hint feature bilinear x2 + 1x1 adapter added, avg_pool2d(2); mid ResBlock-Attention-ResBlock; 4 up levels (bilinear x2, concat skip, 2 ResBlocks, attention at the first); ",
    "GN-SiLU-conv3x3 to 4 channels Q12\",",
    "\"formats\":{\"activations\":\"int16 with per-tensor fractional bits f from the blob (conv, GroupNorm, activation, add, concat outputs) ",
    "or inherited from the input (avg pool, bilinear, attention core)\",\"weights\":\"per-output-channel int16, |Wq|<=qmax=32767\",\"accumulators\":\"i64, wrapping in the conv inner loop under the asserted bound 32768*max_o sum_k|Wq[o,k]|\"},",
    "\"rounding\":{\"conversion\":\"offline, ties to even (numpy rint): inputs, weights, multipliers, biases, gamma/beta, LUT and exp-table entries; the blob carries the frozen integers\",",
    "\"runtime_shift\":\"rshift_round(v,s)=(v+2^(s-1))>>s arithmetic shift for s>0, exact left shift for s<=0\",\"runtime_division\":\"round_div(a,b)=floor((2a+b)/(2b)), b>0\"},",
    "\"domain\":{\"admitted\":[-32768,32767],\"note\":\"full int16 domain (G1 FINAL); every element outside it is clamped and counted once; every indexed hit on a clipped lookup-table entry (blob mask) is counted once; the total is published, not refused\"},",
    "\"conv\":\"acc=sum Wq*x exact; y=clamp16(rshift_round(acc*M_c+b'_c,S)); requant expression checked <2^63 per layer at parse\",",
    "\"groupnorm\":\"S1,S2 exact; N=n*S2-S1^2+n^2*eps_int; mu6=round_div(64*S1,n); e=64*x-mu6; Q=isqrt((n*2^(f_out+24))^2//N) (T=30, 128-bit); Mg=round_div(gamma_q*Q,2^12); y=clamp16(rshift_round(e*Mg,30)+beta_q)\",",
    "\"activation\":\"65536-entry int16 table per (kind,f_in,f_out) from the blob with its 65536-bit clip mask, index x+32768\",",
    "\"attention\":\"4 heads; s_ij=sum q k exact; u=min(rshift_round((m_i-s_ij)*mult, r_shift),32767) with mult 1 and r_shift 2f+2-10 for head_dim 16; w=EXP[u] (32768 entries, 2^20 scale, from the blob); out=clamp16(round_div(sum w v, sum w)) at the qkv scale\",",
    "\"avgpool2\":\"clamp16(rshift_round(a+b+c+d,2))\",\"bilinear_up2\":\"align_corners=False: out[2k]=in[max(k-1,0)]+3in[k], out[2k+1]=3in[k]+in[min(k+1,n-1)] per axis, then clamp16(rshift_round(sum,4))\",",
    "\"add_cat\":\"align to max(f_a,f_b) by exact left shift, add or concatenate, one rshift_round to f_out, clamp16\",",
    "\"noising_expected\":{\"F_CT\":12,\"F_HINT\":14,\"F_EPS\":12,\"SA\":63540,\"SO\":16053,\"shift\":16},",
    "\"representability\":\"every fractional-bit field of the blob lies in 0..=15 and every left shift is checked to round-trip\",",
    "\"blob\":\"ARMCINT1 v2 (armc_int::blob: weights, multipliers, folded biases, GroupNorm parameters, tables and masks, exp table, coordinates, scale table), SHA-256 of the exact bytes published as constants_sha256\",",
    "\"coordinates\":\"hint channels 12,13 as derived by the relation must equal the blob's coordinate planes\"}"
);

/// SHA-256 of `ARMC_INT_SPEC_CANONICAL_JSON`, pinned (hex).
pub const ARMC_INT_SPEC_SHA256_HEX: &str = "02872ec23ab5a503fa1a6b450d90511f83a59afb36457cacb161e1277b22073b";

pub fn armc_int_spec_sha256() -> [u8; 32] {
    Sha256::digest(ARMC_INT_SPEC_CANONICAL_JSON.as_bytes()).into()
}

/// The armc-int network as a `Denoiser`.
pub struct ArmcIntDenoiser {
    constants: Constants,
    blob_sha256: [u8; 32],
    blob_len: usize,
}

impl ArmcIntDenoiser {
    /// Hash and parse the constants blob, then check that it describes the network this statement is about.
    pub fn from_blob(blob: &[u8]) -> Result<Self> {
        let blob_sha256: [u8; 32] = Sha256::digest(blob).into();
        let k = Constants::parse(blob).map_err(|_| RelationError("armc-int constants blob rejected by the parser"))?;
        if k.h != OUT_H || k.w != OUT_W {
            return Err(RelationError("armc-int constants blob is not for a 96x112 grid"));
        }
        if k.qmax != 32767 {
            return Err(RelationError("armc-int constants blob does not carry int16 weights"));
        }
        if k.f_ct != F_CT || k.f_hint != armc_relation::hint::F_HINT || k.f_eps != F_EPS {
            return Err(RelationError("armc-int constants blob fixed-point formats differ from the relation's"));
        }
        if k.sa != SA_INT || k.so != SO_INT || k.noise_p != NOISE_SHIFT {
            return Err(RelationError("armc-int constants blob noising constants differ from the relation's"));
        }
        if k.coord.len() != 2 * OUT_H * OUT_W || k.coord != armc_relation::hint::coord_int() {
            return Err(RelationError("armc-int constants blob coordinate planes differ from the relation's hint coordinates"));
        }
        Ok(Self { constants: k, blob_sha256, blob_len: blob.len() })
    }

    pub fn constants(&self) -> &Constants {
        &self.constants
    }

    pub fn blob_len(&self) -> usize {
        self.blob_len
    }
}

impl Denoiser for ArmcIntDenoiser {
    fn kind(&self) -> u8 {
        KIND_ARMC_INT
    }

    fn constants_sha256(&self) -> [u8; 32] {
        self.blob_sha256
    }

    fn spec_sha256(&self) -> [u8; 32] {
        armc_int_spec_sha256()
    }

    fn predict(&self, ct: &[i16], hint: &[i16]) -> Result<(Vec<i16>, u32)> {
        let plane = OUT_H * OUT_W;
        if ct.len() != FRAME_ELEMS || hint.len() != HINT_CHANNELS * plane {
            return Err(RelationError("armc-int: input shapes differ from 4x96x112 / 14x96x112"));
        }
        let (e, coord) = hint.split_at(HINT_E_CHANNELS * plane);
        if coord != self.constants.coord.as_slice() {
            return Err(RelationError("armc-int: hint coordinate planes differ from the constants blob"));
        }
        // the already-noised frame goes straight into the network (never through the crate's own noising path)
        let ct_t = Tensor::new(FRAME_CHANNELS, OUT_H, OUT_W, F_CT, ct.to_vec());
        let e_t = Tensor::new(HINT_E_CHANNELS, OUT_H, OUT_W, self.constants.f_hint, e.to_vec());
        let mut hook = NoHook;
        let mut net = Net::new(&self.constants, &mut hook);
        let eps = net.forward(&ct_t, &e_t);
        if eps.c != FRAME_CHANNELS || eps.h != OUT_H || eps.w != OUT_W || eps.f != F_EPS {
            return Err(RelationError("armc-int: eps shape or scale differs from 4x96x112 Q12"));
        }
        Ok((eps.v, net.sat))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn spec_digest_is_pinned() {
        let actual = armc_relation::header::hex(&armc_int_spec_sha256());
        assert_eq!(actual, ARMC_INT_SPEC_SHA256_HEX, "ARMC_INT_SPEC_CANONICAL_JSON changed; its digest is now {actual}");
        assert!(!ARMC_INT_SPEC_CANONICAL_JSON.contains('\n'));
        assert!(ARMC_INT_SPEC_CANONICAL_JSON.contains("\"SA\":63540"));
    }

    #[test]
    fn garbage_blob_is_rejected() {
        assert!(ArmcIntDenoiser::from_blob(b"ARMCINT1 not a blob").is_err());
        assert!(ArmcIntDenoiser::from_blob(&[]).is_err());
    }
}
