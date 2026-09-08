//! The hand-rolled portable BLAKE3 must agree with the upstream `blake3` crate
//! bit-for-bit, including the XOF at the exact lengths this protocol uses. If
//! these tests pass, the in-circuit hash is the real BLAKE3.

use zeebeam_b3xof_relation as rel;

#[test]
fn digests_match_upstream_across_length_boundaries() {
    let mut lens: Vec<usize> = vec![
        0, 1, 31, 32, 33, 63, 64, 65, 100, 127, 128, 1023, 1024, 1025, 2047, 2048, 2049, 4096,
        43110, 129_330,
    ];
    // A few awkward lengths around chunk boundaries.
    for k in 1..=8 {
        lens.push(k * 1024 - 1);
        lens.push(k * 1024);
        lens.push(k * 1024 + 1);
    }
    for n in lens {
        let input: Vec<u8> = (0..n).map(|i| (i * 31 + 7) as u8).collect();
        let ours = rel::blake3p::hash(&input);
        let theirs = blake3::hash(&input);
        assert_eq!(
            ours.as_slice(),
            theirs.as_bytes(),
            "32-byte digest mismatch at len {n}"
        );
    }
}

#[test]
fn xof_matches_upstream_at_protocol_lengths() {
    for n_in in [0usize, 1, 32, 44, 64, 65, 1024, 1025] {
        for n_out in [1usize, 32, 63, 64, 65, 128, 43110] {
            let input: Vec<u8> = (0..n_in).map(|i| (i * 17 + 3) as u8).collect();
            let mut ours = vec![0u8; n_out];
            rel::blake3p::xof(&input, &mut ours);
            let mut theirs = vec![0u8; n_out];
            let mut h = blake3::Hasher::new();
            h.update(&input);
            h.finalize_xof().fill(&mut theirs);
            assert_eq!(ours, theirs, "xof mismatch in={n_in} out={n_out}");
        }
    }
}

#[test]
fn seed_derivation_matches_the_published_formula() {
    // Exactly xof_generation.derive_xof_seeds: blake3(tag || S).digest()
    let s = [0x11u8; 32];
    let ours = rel::derive_seeds(&s);
    for (c, tag) in rel::SEED_TAGS.iter().enumerate() {
        let mut h = blake3::Hasher::new();
        h.update(tag);
        h.update(&s);
        assert_eq!(ours[c].as_slice(), h.finalize().as_bytes(), "channel {c}");
    }
}

#[test]
fn expansion_matches_the_published_formula() {
    // Exactly xof_generation.expand_seed_to_octaves: blake3(seed).digest(43110)
    let s = [0x22u8; 32];
    let cond = rel::expand_all(&s);
    assert_eq!(cond.len(), rel::CONDITIONING_BYTES);
    let seeds = rel::derive_seeds(&s);
    for c in 0..rel::CHANNELS {
        let mut want = vec![0u8; rel::TOTAL_BYTES_PER_CHANNEL];
        let mut h = blake3::Hasher::new();
        h.update(&seeds[c]);
        h.finalize_xof().fill(&mut want);
        let got = &cond[c * rel::TOTAL_BYTES_PER_CHANNEL..(c + 1) * rel::TOTAL_BYTES_PER_CHANNEL];
        assert_eq!(got, want.as_slice(), "channel {c} stream");
    }
}

/// A whole tile rendered through the streaming row path must have the BLAKE3
/// digest that chain_log.csv publishes as `emission_live_pixel_blake3_hex`.
/// The expected value here is the measured one for august_dev_712 row 0.
#[test]
fn august_row0_tile_digest_matches_the_published_commitment() {
    let s = hex_lit("74e3a131e1aaadd98e18c5f2a5f28ffaf59b8cd738e10216586efa2a893f384c");
    let cond = rel::expand_all(&s);
    let tables = rel::RenderTables::new();
    let mut h = blake3::Hasher::new();
    let mut row = vec![0u8; rel::TILE_W * rel::CHANNELS];
    for y in 0..rel::TILE_H {
        rel::render_row_rgb(&cond, &tables, y, 0, rel::TILE_W, &mut row);
        h.update(&row);
    }
    assert_eq!(
        h.finalize().to_hex().as_str(),
        "94ea977fcc33e904c96915a8f3158e92ccc594ae26b7d1e1ca1ccd1ea3be3db6",
        "rendered tile digest does not match chain_log emission_live_pixel_blake3_hex"
    );
}

/// A partial render over an arbitrary rectangle must produce exactly the bytes
/// the full-row render produces there. This is what makes a cell opening sound.
#[test]
fn cell_render_agrees_with_full_row_render() {
    let s = hex_lit("74e3a131e1aaadd98e18c5f2a5f28ffaf59b8cd738e10216586efa2a893f384c");
    let cond = rel::expand_all(&s);
    let tables = rel::RenderTables::new();
    for (x0, y0) in [(0usize, 0usize), (7, 3), (960, 540), (1912, 1072)] {
        let mut full = vec![0u8; rel::TILE_W * rel::CHANNELS];
        let mut cell = vec![0u8; 8 * rel::CHANNELS];
        for dy in 0..8 {
            rel::render_row_rgb(&cond, &tables, y0 + dy, 0, rel::TILE_W, &mut full);
            rel::render_row_rgb(&cond, &tables, y0 + dy, x0, 8, &mut cell);
            let want = &full[x0 * rel::CHANNELS..(x0 + 8) * rel::CHANNELS];
            assert_eq!(cell.as_slice(), want, "cell ({x0},{y0}) row {dy}");
        }
    }
}

#[test]
fn open_mode_accepts_an_honest_path_for_every_octave() {
    let s = [0x33u8; 32];
    let cond = rel::expand_all(&s);
    let leaves = rel::grid_row_leaves_from_cond(&cond);
    let root = rel::merkle_root(&leaves);
    for (c, o, r) in [
        (0usize, 0usize, 0usize),
        (1, 1, 33),
        (2, 2, 67),
        (0, 3, 134),
    ] {
        let idx = rel::leaf_index(c, o, r);
        let gw = rel::GRID_W[o];
        let pos = c * rel::TOTAL_BYTES_PER_CHANNEL + rel::octave_offset(o) + r * gw;
        let bytes = &cond[pos..pos + gw];
        let leaf = rel::blake3p::hash2(&rel::leaf_prefix(c, o, r), bytes);
        assert_eq!(leaf, leaves[idx], "leaf ({c},{o},{r})");
        let path = rel::merkle_path(&leaves, idx);
        assert_eq!(rel::merkle_verify(&leaf, idx, &path), root);
    }
}

fn hex_lit(h: &str) -> [u8; 32] {
    let mut out = [0u8; 32];
    for i in 0..32 {
        out[i] = u8::from_str_radix(&h[2 * i..2 * i + 2], 16).unwrap();
    }
    out
}
