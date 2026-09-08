//! Relation side of the ZeeBeam two-evaluation diffusion statement (G2-B), everything except the
//! integer network kernels, which arrive through the [`net::Denoiser`] trait.
//!
//! Legs, in the order the guest runs them (statement.rs `evaluate`):
//!
//! 1. constants: the network's constants/spec digests and this crate's preprocessing spec digest;
//! 2. drand: quicknet BLS verification of the row's own beacon, `SHA-256(sig_r) == v_r`;
//! 3. raw frame: `BLAKE3(raw_r)`, the v9 chain advance to `S_{r+1}`;
//! 4. previous row: `sig_{r-1}` verified, `advance(S_{r-1}, ...) == S_r` (row 0 refused);
//! 5. emission r: XOF of `S_r`, four-octave render, digest kept for the leaf;
//! 6. emission u: XOF of `S_u`, render, digest must equal the witnessed leaf field;
//! 7. membership: `leaf_r` (with the recomputed `S_{r+1}` and emission digest) and `leaf_u` both open to the
//!    committed ordered-session root under the session context;
//! 8. inputs: whole-frame reduction of `raw_r` to the 4x96x112 int16 C, the two 14-channel hints from the two XOF
//!    streams, the pinned noise, `C_t` by integer forward noising at t = 150;
//! 9. two network evaluations, residual sums against the same noise, their difference;
//! 10. the public statement bytes.
//!
//! Every numeric rule is stated in RELATION.md with the pipeline line it reproduces; every module carries the
//! reference it was tested against.

pub mod beacon;
pub mod emission;
pub mod fp;
pub mod frame;
pub mod header;
pub mod hint;
pub mod membership;
pub mod net;
pub mod noise;
pub mod rule;
pub mod spec;
pub mod statement;

pub use zeebeam_b3xof_relation as b3xof;

/// One error type for the whole relation: a static message, so a guest panic prints exactly which leg failed.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct RelationError(pub &'static str);

impl RelationError {
    pub const fn message(self) -> &'static str {
        self.0
    }
}

impl core::fmt::Display for RelationError {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        f.write_str(self.0)
    }
}

impl std::error::Error for RelationError {}

pub type Result<T> = core::result::Result<T, RelationError>;

/// Frame grid the network consumes (`--out-size 96,112`, train_lean.py:272/279).
pub const OUT_H: usize = 96;
pub const OUT_W: usize = 112;
/// Sensor frame geometry (train_lean.py:126-128).
pub const RAW_H: usize = 4600;
pub const RAW_W: usize = 5320;
pub const RAW_BYTES: usize = RAW_H * RAW_W; // 24_472_000
pub const PLANE_H: usize = RAW_H / 2; // 2300
pub const PLANE_W: usize = RAW_W / 2; // 2660
pub const FRAME_CHANNELS: usize = 4;
pub const HINT_E_CHANNELS: usize = 12;
pub const HINT_CHANNELS: usize = 14;
pub const FRAME_ELEMS: usize = FRAME_CHANNELS * OUT_H * OUT_W; // 43_008
