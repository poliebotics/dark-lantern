//! The activation tensor: `i16` values in `(C, H, W)` row-major order with `f` fractional bits.

use alloc::vec::Vec;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Tensor {
    pub c: usize,
    pub h: usize,
    pub w: usize,
    /// Fractional bits: real value `v * 2^-f`.
    pub f: u32,
    pub v: Vec<i16>,
}

impl Tensor {
    pub fn new(c: usize, h: usize, w: usize, f: u32, v: Vec<i16>) -> Self {
        assert_eq!(v.len(), c * h * w, "tensor size");
        Tensor { c, h, w, f, v }
    }

    pub fn len(&self) -> usize {
        self.v.len()
    }

    pub fn is_empty(&self) -> bool {
        self.v.is_empty()
    }

    pub fn shape(&self) -> (usize, usize, usize) {
        (self.c, self.h, self.w)
    }

    /// Little-endian bytes of the values (the byte string the oracle hashes).
    pub fn to_le_bytes(&self) -> Vec<u8> {
        let mut out = Vec::with_capacity(self.v.len() * 2);
        for &x in &self.v {
            out.extend_from_slice(&x.to_le_bytes());
        }
        out
    }

    pub fn from_le_bytes(c: usize, h: usize, w: usize, f: u32, bytes: &[u8]) -> Self {
        assert_eq!(bytes.len(), 2 * c * h * w, "tensor byte length");
        let v = bytes.chunks_exact(2).map(|b| i16::from_le_bytes([b[0], b[1]])).collect();
        Tensor { c, h, w, f, v }
    }
}
