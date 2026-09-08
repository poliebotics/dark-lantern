//! Emission pattern render and digest, exactly the proved leg (join/src/lib.rs lines 338-350): the 1920x1080 RGB
//! tile of a chain state is rendered one interleaved row at a time with `render_row_rgb` and streamed into BLAKE3;
//! the digest is compared with the chain log's `emission_live_pixel_blake3_hex` through the session leaf.

use crate::b3xof::{self, blake3p, RenderTables};

/// Render the whole tile from a 129,330-byte conditioning buffer (`b3xof::expand_all(S_t)`) and return its
/// BLAKE3 digest. The tile itself is never materialised (5,760 bytes of row buffer).
pub fn render_tile_digest(cond: &[u8]) -> [u8; 32] {
    assert_eq!(cond.len(), b3xof::CONDITIONING_BYTES);
    let tables = RenderTables::new();
    let row_bytes = b3xof::TILE_W * b3xof::CHANNELS;
    let mut row = vec![0_u8; row_bytes];
    let mut hasher = blake3p::Hasher::new();
    for y in 0..b3xof::TILE_H {
        b3xof::render_row_rgb(cond, &tables, y, 0, b3xof::TILE_W, &mut row);
        hasher.update(&row);
    }
    hasher.finalize()
}

/// Convenience: state -> (conditioning stream, tile digest).
pub fn expand_and_digest(s_t: &[u8; 32]) -> (Vec<u8>, [u8; 32]) {
    let cond = b3xof::expand_all(s_t);
    let digest = render_tile_digest(&cond);
    (cond, digest)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::header::unhex32;

    #[test]
    fn august_row_96_emission_digest_matches_the_chain_log() {
        // chain_log.csv row 96: S_t_hex and emission_live_pixel_blake3_hex (also EMISSION_BLAKE3 in the proved
        // row_binding_join native oracle).
        let s_t = unhex32("9ebaec46e2e4924c1a628ce67c482f49ff48b4972c0619f972443888c881584e");
        let (_, digest) = expand_and_digest(&s_t);
        assert_eq!(digest, unhex32("5e4a0bc9f4790b843d91185736b916042f5cac794a5d8c31662a2cd601a4bfa8"));
    }
}
