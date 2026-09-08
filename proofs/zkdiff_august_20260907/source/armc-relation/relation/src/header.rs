//! The private row header, `ZBROWW01`, copied from the proved join crate
//! (rust/row_binding_join_sp1_candidate/join/src/lib.rs lines 55-58 and 96-161) so the host tooling that already
//! produces these 120 bytes (session_tree.py output through witness.rs) keeps working unchanged.
//!
//! ```text
//!   0..8    magic "ZBROWW01"     8      abi 1        9  protocol 9 (TB-v0.9)     10..12 reserved 0
//!  12..16   row index u32 LE    16..48  S_t         48..76 meta (28 B, ">IQQI4s", meta[0..4] BE == row index)
//!  76..84   drand round u64 LE  84..116 drand value 116..120 reserved 0
//! ```

use crate::b3xof::META_BYTES;
use crate::{RelationError, Result};

pub const PRIVATE_MAGIC: &[u8; 8] = b"ZBROWW01";
pub const PRIVATE_ABI_VERSION: u8 = 1;
pub const PROTOCOL_V9_CODE: u8 = 9;
pub const PRIVATE_HEADER_BYTES: usize = 120;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RowWitnessHeader {
    pub row_index: u32,
    pub s_t: [u8; 32],
    pub meta: [u8; META_BYTES],
    pub drand_round: u64,
    pub drand_value: [u8; 32],
}

impl RowWitnessHeader {
    pub fn parse(bytes: &[u8]) -> Result<Self> {
        if bytes.len() != PRIVATE_HEADER_BYTES {
            return Err(RelationError("private header must be exactly 120 bytes"));
        }
        if &bytes[0..8] != PRIVATE_MAGIC {
            return Err(RelationError("private header magic differs"));
        }
        if bytes[8] != PRIVATE_ABI_VERSION {
            return Err(RelationError("private ABI version differs"));
        }
        if bytes[9] != PROTOCOL_V9_CODE {
            return Err(RelationError("private protocol code must be TB-v0.9"));
        }
        if bytes[10..12] != [0; 2] || bytes[116..120] != [0; 4] {
            return Err(RelationError("private reserved bytes must be zero"));
        }
        let row_index = u32::from_le_bytes(bytes[12..16].try_into().expect("fixed row index"));
        let mut s_t = [0_u8; 32];
        s_t.copy_from_slice(&bytes[16..48]);
        let mut meta = [0_u8; META_BYTES];
        meta.copy_from_slice(&bytes[48..76]);
        let drand_round = u64::from_le_bytes(bytes[76..84].try_into().expect("fixed drand round"));
        let mut drand_value = [0_u8; 32];
        drand_value.copy_from_slice(&bytes[84..116]);
        let meta_row = u32::from_be_bytes(meta[0..4].try_into().expect("fixed metadata row"));
        if meta_row != row_index {
            return Err(RelationError("metadata row index differs from private header"));
        }
        Ok(Self { row_index, s_t, meta, drand_round, drand_value })
    }

    pub fn encode(&self) -> Result<[u8; PRIVATE_HEADER_BYTES]> {
        let meta_row = u32::from_be_bytes(self.meta[0..4].try_into().expect("fixed metadata row"));
        if meta_row != self.row_index {
            return Err(RelationError("metadata row index differs from private header"));
        }
        let mut bytes = [0_u8; PRIVATE_HEADER_BYTES];
        bytes[0..8].copy_from_slice(PRIVATE_MAGIC);
        bytes[8] = PRIVATE_ABI_VERSION;
        bytes[9] = PROTOCOL_V9_CODE;
        bytes[12..16].copy_from_slice(&self.row_index.to_le_bytes());
        bytes[16..48].copy_from_slice(&self.s_t);
        bytes[48..76].copy_from_slice(&self.meta);
        bytes[76..84].copy_from_slice(&self.drand_round.to_le_bytes());
        bytes[84..116].copy_from_slice(&self.drand_value);
        Ok(bytes)
    }
}

/// Lowercase hex helper shared by tests and the host.
pub fn unhex(s: &str) -> Vec<u8> {
    let s = s.trim();
    assert!(s.len() % 2 == 0, "hex string of odd length");
    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).expect("hex")).collect()
}

pub fn unhex32(s: &str) -> [u8; 32] {
    unhex(s).try_into().expect("32-byte hex")
}

pub fn hex(b: &[u8]) -> String {
    b.iter().map(|x| format!("{x:02x}")).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn example() -> RowWitnessHeader {
        let mut meta = [0_u8; META_BYTES];
        meta[0..4].copy_from_slice(&96_u32.to_be_bytes());
        RowWitnessHeader { row_index: 96, s_t: [0x11; 32], meta, drand_round: 31_521_620, drand_value: [0x22; 32] }
    }

    #[test]
    fn round_trips_and_fails_closed() {
        let h = example();
        let e = h.encode().unwrap();
        assert_eq!(RowWitnessHeader::parse(&e).unwrap(), h);
        for i in [0_usize, 8, 9, 10, 116] {
            let mut c = e;
            c[i] ^= 1;
            assert!(RowWitnessHeader::parse(&c).is_err(), "byte {i}");
        }
        let mut wrong_row = e;
        wrong_row[12..16].copy_from_slice(&97_u32.to_le_bytes());
        assert!(RowWitnessHeader::parse(&wrong_row).is_err());
        assert!(RowWitnessHeader::parse(&e[..119]).is_err());
    }
}
