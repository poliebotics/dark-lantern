//! `armc-int`: bit-exact integer inference of the ARM-C lean denoiser in the G1 fixed-point
//! scheme (`scratch/zk_diffusion_demo_20260907/g1_integer/`, the Python oracle), written for the
//! SP1 guest: `no_std` + `alloc`, plain `i64` integer arithmetic, no floating point.
//!
//! Modules:
//! * [`kernels`]: conv 3x3 / 1x1 (and generic), requantisation, GroupNorm, LUT activations,
//!   bilinear x2, average pool, add, concat, attention, forward noising, residual sum;
//! * [`blob`]: the constants blob (quantised weights, multipliers, GroupNorm constants, LUTs,
//!   exp table, coordinates, scheme constants), a compact binary format with a parser;
//! * [`model`]: the ARM-C network program parameterised by the blob (any base width);
//! * [`loader`] (feature `std`): reads the G1 oracle export (`g2_guest/oracle/<set>/`) into a
//!   [`blob::Constants`] and an [`loader::OracleSet`], and writes blobs.

#![cfg_attr(not(feature = "std"), no_std)]

extern crate alloc;

pub mod blob;
pub mod kernels;
pub mod model;
pub mod tensor;

#[cfg(feature = "std")]
pub mod loader;

pub use blob::Constants;
pub use tensor::Tensor;
