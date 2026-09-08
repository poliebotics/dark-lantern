//! BLAKE3 compression-function accounting.
//!
//! The counter is a single process-global atomic, so a test that reads it must
//! hold the lock for its WHOLE body -- not merely around each measurement.
//! Holding it only around the measurement is not enough: hashing done between
//! measurements by a sibling test still bumps the shared counter. Both mistakes
//! were made while writing this file and both produced inflated counts.
#![cfg(feature = "count")]

use std::sync::{Mutex, MutexGuard, OnceLock};

use zeebeam_b3xof_relation as rel;
use zeebeam_b3xof_relation::blake3p::{self, counter};
use zeebeam_b3xof_relation::Mode;

/// Exclusive access to the process-global compression counter.
struct Session(#[allow(dead_code)] MutexGuard<'static, ()>);

impl Session {
    fn new() -> Self {
        static G: OnceLock<Mutex<()>> = OnceLock::new();
        // A poisoned lock only means another counting test already failed.
        let g = G
            .get_or_init(|| Mutex::new(()))
            .lock()
            .unwrap_or_else(|e| e.into_inner());
        Self(g)
    }

    fn count<T>(&self, f: impl FnOnce() -> T) -> (T, u64) {
        counter::reset();
        let out = f();
        (out, counter::get())
    }
}

#[test]
fn analytic_cost_matches_measured_cost_across_length_boundaries() {
    let sess = Session::new();
    let mut cases: Vec<(usize, usize)> = vec![
        (0, 32),
        (1, 32),
        (32, 32),
        (44, 32),
        (64, 32),
        (65, 32),
        (32, 43110),
        (1023, 32),
        (1024, 32),
        (1025, 32),
        (43110, 32),
        (129_330, 32),
        (1920 * 3, 32),
        (rel::TILE_BYTES, 32),
    ];
    // Every chunk count from 1 to 16, on and either side of the boundary.
    for k in 1..=16usize {
        cases.push((k * 1024 - 1, 32));
        cases.push((k * 1024, 32));
        cases.push((k * 1024 + 1, 32));
    }
    for (n_in, n_out) in cases {
        let input = vec![0xA5u8; n_in];
        let (_, measured) = sess.count(|| {
            let mut out = vec![0u8; n_out];
            blake3p::xof(&input, &mut out);
        });
        assert_eq!(
            measured,
            blake3p::compressions(n_in, n_out),
            "compression count mismatch in={n_in} out={n_out}"
        );
    }
}

#[test]
fn each_expansion_stage_costs_what_we_claim() {
    let sess = Session::new();
    let s = [0x5Au8; 32];

    let (seeds, m_seeds) = sess.count(|| rel::derive_seeds(&s));
    assert_eq!(m_seeds, rel::compressions_seeds(), "seed derivation");
    assert_eq!(m_seeds, 3, "three seeds, one compression each");

    let (_, m_xof) = sess.count(|| {
        let mut buf = vec![0u8; rel::TOTAL_BYTES_PER_CHANNEL];
        for c in 0..rel::CHANNELS {
            blake3p::xof(&seeds[c], &mut buf);
        }
    });
    assert_eq!(m_xof, rel::compressions_xof(), "XOF expansion");
    assert_eq!(
        m_xof,
        3 * 674,
        "43,110 bytes is 674 output blocks per channel"
    );

    let (cond, _) = sess.count(|| rel::expand_all(&s));
    let (leaves, m_leaf) = sess.count(|| rel::grid_row_leaves_from_cond(&cond));
    assert_eq!(m_leaf, rel::compressions_leaves(), "grid-row leaves");
    assert_eq!(leaves.len(), rel::GRID_LEAVES);

    let (_, m_tree) = sess.count(|| rel::merkle_root(&leaves));
    assert_eq!(
        m_tree,
        rel::compressions_merkle(rel::GRID_LEAVES),
        "Merkle tree"
    );
}

#[test]
fn whole_mode_costs_match_the_analytic_per_row_figure() {
    let sess = Session::new();
    let s = [0x5Au8; 32];
    for mode in [Mode::Seeds, Mode::Expand, Mode::Grids] {
        let w = rel::Witness {
            mode,
            states: vec![s],
            cell: (0, 0, 8, 8),
            open_chan: 0,
            open_oct: 0,
            open_row: 0,
            open_bytes: Vec::new(),
            open_path: Vec::new(),
            claim: Vec::new(),
        };
        let (out, measured) = sess.count(|| rel::evaluate(&w));
        out.expect("honest witness rejected");
        assert_eq!(
            measured,
            rel::compressions_per_row(mode),
            "mode {mode:?} compression count"
        );
    }
}

/// The headline cost numbers this experiment reports, each with its derivation
/// written out, pinned so a later edit cannot silently change them.
#[test]
fn published_cost_constants_are_stable() {
    // Three seed derivations: BLAKE3 over 12 + 32 = 44 bytes, one block each.
    assert_eq!(rel::compressions_seeds(), 3);
    // Three XOF expansions: 43,110 / 64 = 673.6 -> 674 output blocks each.
    assert_eq!(rel::compressions_xof(), 3 * 674);
    assert_eq!(rel::compressions_seeds() + rel::compressions_xof(), 2025);

    // 762 typed leaves. A leaf is BLAKE3 over 20 prefix bytes plus the grid row:
    //   octave 0:  20 +  30 =  50 bytes -> 1 block   x 17 rows
    //   octave 1:  20 +  60 =  80 bytes -> 2 blocks  x 34 rows
    //   octave 2:  20 + 120 = 140 bytes -> 3 blocks  x 68 rows
    //   octave 3:  20 + 240 = 260 bytes -> 5 blocks  x 135 rows
    // per channel 17 + 68 + 204 + 675 = 964, times 3 channels = 2,892.
    assert_eq!(rel::compressions_leaves(), 2_892);

    // Merkle over 762 leaves: 381+191+96+48+24+12+6+3+2+1 = 764 internal nodes,
    // each BLAKE3 over 13 + 64 = 77 bytes = 2 blocks.
    assert_eq!(rel::compressions_merkle(rel::GRID_LEAVES), 764 * 2);

    // The Grids statement, per row of chain_log.csv.
    assert_eq!(
        rel::compressions_per_row(Mode::Grids),
        2_025 + 2_892 + 1_528
    );
    assert_eq!(rel::compressions_per_row(Mode::Grids), 6_445);

    // The Expand statement additionally digests each 43,110-byte stream.
    assert_eq!(rel::compressions_per_row(Mode::Expand), 2_025 + 3 * 716);

    // A whole-tile BLAKE3 digest over 6,220,800 bytes.
    assert_eq!(blake3p::compressions(rel::TILE_BYTES, 32), 103_274);
}
