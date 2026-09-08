//! drand quicknet beacon verification, copied from the proved join crate
//! (rust/row_binding_join_sp1_candidate/join/src/lib.rs lines 31-47 constants, 248-283 `verify_quicknet_beacon`).
//!
//! quicknet is `bls-unchained-g1-rfc9380`: `e(sig, G2) == e(H(sha256(round_be8)), pk)` with the RFC 9380
//! `BLS_SIG_BLS12381G1_XMD:SHA-256_SSWU_RO_NUL_` suite; the beacon randomness is `SHA-256(sig)`, which the caller
//! binds to the chain-log `drand_round_value` that `advance_chain` consumes. In the guest the `bls12_381`
//! sp1-patches fork routes the field arithmetic through the SP1 precompiles (4.9 M instructions per verification
//! as measured for the proved row); on the host it is plain Rust.

#[cfg(feature = "bls")]
use bls12_381::hash_to_curve::{ExpandMsgXmd, HashToCurve};
#[cfg(feature = "bls")]
use bls12_381::{pairing, G1Affine, G1Projective, G2Affine};
use sha2::{Digest as ShaDigest, Sha256};

use crate::{RelationError, Result};

/// drand quicknet chain hash (the network identifier every drand client pins).
pub const QUICKNET_CHAIN_HASH: [u8; 32] = [
    0x52, 0xdb, 0x9b, 0xa7, 0x0e, 0x0c, 0xc0, 0xf6, 0xea, 0xf7, 0x80, 0x3d, 0xd0, 0x74, 0x47, 0xa1, 0xf5, 0x47, 0x77, 0x35,
    0xfd, 0x3f, 0x66, 0x17, 0x92, 0xba, 0x94, 0x60, 0x0c, 0x84, 0xe9, 0x71,
];
pub const QUICKNET_DST: &[u8] = b"BLS_SIG_BLS12381G1_XMD:SHA-256_SSWU_RO_NUL_";
pub const QUICKNET_PUBLIC_KEY: [u8; 96] = [
    0x83, 0xcf, 0x0f, 0x28, 0x96, 0xad, 0xee, 0x7e, 0xb8, 0xb5, 0xf0, 0x1f, 0xca, 0xd3, 0x91, 0x22, 0x12, 0xc4, 0x37, 0xe0,
    0x07, 0x3e, 0x91, 0x1f, 0xb9, 0x00, 0x22, 0xd3, 0xe7, 0x60, 0x18, 0x3c, 0x8c, 0x4b, 0x45, 0x0b, 0x6a, 0x0a, 0x6c, 0x3a,
    0xc6, 0xa5, 0x77, 0x6a, 0x2d, 0x10, 0x64, 0x51, 0x0d, 0x1f, 0xec, 0x75, 0x8c, 0x92, 0x1c, 0xc2, 0x2b, 0x0e, 0x17, 0xe6,
    0x3a, 0xaf, 0x4b, 0xcb, 0x5e, 0xd6, 0x63, 0x04, 0xde, 0x9c, 0xf8, 0x09, 0xbd, 0x27, 0x4c, 0xa7, 0x3b, 0xab, 0x4a, 0xf5,
    0xa6, 0xe9, 0xc7, 0x6a, 0x4b, 0xc0, 0x9e, 0x76, 0xea, 0xe8, 0x99, 0x1e, 0xf5, 0xec, 0xe4, 0x5a,
];
pub const SIGNATURE_BYTES: usize = 48;

/// Verify a quicknet signature for `round` under the compiled-in public key and return `SHA-256(signature)`.
#[cfg(feature = "bls")]
pub fn verify_quicknet_beacon(round: u64, drand_signature: &[u8]) -> Result<[u8; 32]> {
    if drand_signature.len() != SIGNATURE_BYTES {
        return Err(RelationError("drand quicknet signature must be 48 bytes"));
    }
    let mut sig_bytes = [0_u8; 48];
    sig_bytes.copy_from_slice(drand_signature);
    let sig_point = G1Affine::from_compressed(&sig_bytes);
    if bool::from(sig_point.is_none()) {
        return Err(RelationError("drand signature is not a valid G1 point"));
    }
    let sig_point = sig_point.unwrap();
    if bool::from(sig_point.is_identity()) {
        return Err(RelationError("drand signature is the identity point"));
    }
    let pk_point = G2Affine::from_compressed(&QUICKNET_PUBLIC_KEY);
    if bool::from(pk_point.is_none()) {
        return Err(RelationError("quicknet public key is not a valid G2 point"));
    }
    let pk_point = pk_point.unwrap();
    if bool::from(pk_point.is_identity()) {
        return Err(RelationError("quicknet public key is the identity point"));
    }
    let beacon_message: [u8; 32] = Sha256::digest(round.to_be_bytes()).into();
    let hashed: G1Affine =
        <G1Projective as HashToCurve<ExpandMsgXmd<Sha256>>>::hash_to_curve([beacon_message.as_slice()], QUICKNET_DST).into();
    if pairing(&sig_point, &G2Affine::generator()) != pairing(&hashed, &pk_point) {
        return Err(RelationError("drand quicknet signature does not verify"));
    }
    Ok(Sha256::digest(drand_signature).into())
}

#[cfg(not(feature = "bls"))]
pub fn verify_quicknet_beacon(_round: u64, _drand_signature: &[u8]) -> Result<[u8; 32]> {
    Err(RelationError("built without the bls feature: the beacon leg is unavailable and no statement can be produced"))
}

/// Verify and bind: the randomness must be the value the chain advance consumed.
pub fn verify_and_bind(round: u64, signature: &[u8], expected_value: &[u8; 32]) -> Result<()> {
    let randomness = verify_quicknet_beacon(round, signature)?;
    if randomness != *expected_value {
        return Err(RelationError("drand randomness is not sha256 of the verified signature"));
    }
    Ok(())
}

/// The published drand leg digest: `BLAKE3("ZBDIFF:DRAND:v1\0" || round_{r-1} BE || value_{r-1} || round_r BE ||
/// value_r || QUICKNET_CHAIN_HASH)`. Both rounds were verified in circuit when this digest is published.
pub fn drand_leg_digest(prev_round: u64, prev_value: &[u8; 32], own_round: u64, own_value: &[u8; 32]) -> [u8; 32] {
    let mut h = crate::b3xof::blake3p::Hasher::new();
    h.update(b"ZBDIFF:DRAND:v1\0");
    h.update(&prev_round.to_be_bytes());
    h.update(prev_value);
    h.update(&own_round.to_be_bytes());
    h.update(own_value);
    h.update(&QUICKNET_CHAIN_HASH);
    h.finalize()
}

#[cfg(all(test, feature = "bls"))]
mod tests {
    use super::*;
    use crate::header::{unhex, unhex32};

    // August rows 96 and 0 (chain_log.csv columns drand_round_number, drand_signature_hex, drand_round_value_hex;
    // row 96's signature is also ROW96_SIGNATURE_HEX in the proved script/src/witness.rs).
    const ROW96_SIG: &str = "86efb9051b5f44e9c5e8e8e6ed30eff6a3ed1a3e11c91e42f6da0fa505db5e51385bda5892ae44ae40a5783a147d3322";
    const ROW96_VALUE: &str = "65775d2f4063482fe05f1889939b7822407b395deb6a94dfc4236ef80f10f313";
    const ROW0_SIG: &str = "b6986a890c9aee8c7d3d509e2605c480dbf83e5d3c97c1033d1e8220c02869f9422e7a5555389891c59fdd620dffc683";
    const ROW0_VALUE: &str = "ed8b01211651c0e95775aec902e4713d8befc617144490884a82829185b885c9";

    #[test]
    fn real_quicknet_beacons_verify_and_bind() {
        verify_and_bind(31_521_620, &unhex(ROW96_SIG), &unhex32(ROW96_VALUE)).unwrap();
        verify_and_bind(31_521_605, &unhex(ROW0_SIG), &unhex32(ROW0_VALUE)).unwrap();
    }

    #[test]
    fn wrong_round_wrong_value_and_bad_point_are_rejected() {
        assert!(verify_quicknet_beacon(31_521_621, &unhex(ROW96_SIG)).is_err());
        assert!(verify_and_bind(31_521_620, &unhex(ROW96_SIG), &unhex32(ROW0_VALUE)).is_err());
        assert!(verify_quicknet_beacon(31_521_620, &unhex(ROW96_SIG)[..47]).is_err());
        let mut bad = unhex(ROW96_SIG);
        bad[47] ^= 1;
        assert!(verify_quicknet_beacon(31_521_620, &bad).is_err());
    }
}
