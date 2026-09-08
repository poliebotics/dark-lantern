//! Truth Beam v8 projector-pattern expansion, as an in-circuit relation.
//!
//! The protocol expansion, all of it BLAKE3 and integer arithmetic:
//!
//! ```text
//! S_t (32 bytes, published in chain_log.csv as S_t_hex)
//!   -> seed_c = BLAKE3(b"TB:SEED:{R,G,B}:v8" || S_t)                    (32 bytes each)
//!   -> stream_c = BLAKE3(seed_c).xof(43110)
//!   -> sliced into four octave grids 17x30, 34x60, 68x120, 135x240
//!   -> fixed-point bilinear upsample to 1920x1080, octave o weighted >>o,
//!      +128, clipped to [0,255]
//! ```
//!
//! Nothing here is floating point and nothing here is geometric. Binding this
//! expansion says *nothing whatever* about where the pattern landed in a scene
//! or how a camera was aligned to it; see README.md.

#![no_std]

extern crate alloc;

pub mod blake3p;

use alloc::vec;
use alloc::vec::Vec;

// ------------------------------------------------------------------ constants

pub const TILE_W: usize = 1920;
pub const TILE_H: usize = 1080;
pub const NUM_OCTAVES: usize = 4;
pub const GRID_H: [usize; NUM_OCTAVES] = [17, 34, 68, 135];
pub const GRID_W: [usize; NUM_OCTAVES] = [30, 60, 120, 240];
pub const OCTAVE_BYTES: [usize; NUM_OCTAVES] = [17 * 30, 34 * 60, 68 * 120, 135 * 240];
pub const TOTAL_BYTES_PER_CHANNEL: usize = 43110;
pub const CHANNELS: usize = 3;
/// The full conditioning payload a verifier would otherwise have to be shown.
pub const CONDITIONING_BYTES: usize = TOTAL_BYTES_PER_CHANNEL * CHANNELS; // 129_330
pub const TILE_BYTES: usize = TILE_W * TILE_H * CHANNELS; // 6_220_800
/// Grid rows per channel: 17 + 34 + 68 + 135.
pub const GRID_ROWS_PER_CHANNEL: usize = 254;
pub const GRID_LEAVES: usize = GRID_ROWS_PER_CHANNEL * CHANNELS; // 762

pub const SEED_TAGS: [&[u8]; CHANNELS] = [b"TB:SEED:R:v8", b"TB:SEED:G:v8", b"TB:SEED:B:v8"];

/// Domain separation for this experiment's commitments. These are *ours*, not
/// the recording protocol's: the protocol publishes S_t and a whole-tile BLAKE3
/// digest, and we add a Merkle commitment over the octave grids so that a
/// verifier can be shown one grid row instead of all 129,330 bytes.
pub const DOM_LEAF: &[u8] = b"TB:ZK:GRIDROW:v1";
pub const DOM_NODE: &[u8] = b"TB:ZK:NODE:v1";
pub const DOM_ROW: &[u8] = b"TB:ZK:ROW:v1";
pub const DOM_STATES: &[u8] = b"TB:ZK:STATES:v1";

const SB: u32 = 16;
const SS: i64 = 1 << SB;
const MASK: i64 = SS - 1;

// -------------------------------------------------------------- octave slicing

/// Byte offset of octave `o` inside a 43,110-byte channel stream.
pub const fn octave_offset(o: usize) -> usize {
    let mut off = 0;
    let mut i = 0;
    while i < o {
        off += OCTAVE_BYTES[i];
        i += 1;
    }
    off
}

// ------------------------------------------------------------------ expansion

pub type Digest = [u8; 32];

/// `seed_c = BLAKE3(tag_c || S_t)` for c in {R,G,B}.
pub fn derive_seeds(s: &[u8; 32]) -> [Digest; CHANNELS] {
    let mut out = [[0u8; 32]; CHANNELS];
    for c in 0..CHANNELS {
        out[c] = blake3p::hash2(SEED_TAGS[c], s);
    }
    out
}

/// `stream_c = BLAKE3(seed_c).xof(43110)`.
pub fn expand_stream(seed: &Digest, out: &mut [u8; TOTAL_BYTES_PER_CHANNEL]) {
    blake3p::xof(seed, out);
}

/// The three 43,110-byte channel streams for a chain state.
pub fn expand_all(s: &[u8; 32]) -> Vec<u8> {
    let seeds = derive_seeds(s);
    let mut buf = vec![0u8; CONDITIONING_BYTES];
    for c in 0..CHANNELS {
        blake3p::xof(
            &seeds[c],
            &mut buf[c * TOTAL_BYTES_PER_CHANNEL..(c + 1) * TOTAL_BYTES_PER_CHANNEL],
        );
    }
    buf
}

// -------------------------------------------------------- grid-row commitment

/// The 20-byte typed prefix that a grid-row leaf commits under.
pub const LEAF_PREFIX_BYTES: usize = 20;

pub fn leaf_prefix(chan: usize, oct: usize, row: usize) -> [u8; LEAF_PREFIX_BYTES] {
    let mut p = [0u8; LEAF_PREFIX_BYTES];
    p[..DOM_LEAF.len()].copy_from_slice(DOM_LEAF);
    p[16] = chan as u8;
    p[17] = oct as u8;
    p[18] = (row & 0xFF) as u8;
    p[19] = ((row >> 8) & 0xFF) as u8;
    p
}

/// `leaf = BLAKE3(DOM_LEAF || chan || oct || row_lo || row_hi || row_bytes)`.
///
/// Leaf order is channel-major, then octave, then grid row: 3 x 254 = 762.
/// A typed opening therefore names (channel, octave, grid row) and reveals only
/// that row -- 30 to 240 bytes instead of 129,330.
pub fn grid_row_leaves_from_cond(cond: &[u8]) -> Vec<Digest> {
    assert_eq!(cond.len(), CONDITIONING_BYTES, "conditioning length");
    let mut leaves = Vec::with_capacity(GRID_LEAVES);
    for c in 0..CHANNELS {
        let base = c * TOTAL_BYTES_PER_CHANNEL;
        let mut pos = base;
        for (o, &gw) in GRID_W.iter().enumerate() {
            for r in 0..GRID_H[o] {
                leaves.push(blake3p::hash2(&leaf_prefix(c, o, r), &cond[pos..pos + gw]));
                pos += gw;
            }
        }
        debug_assert_eq!(pos, base + TOTAL_BYTES_PER_CHANNEL);
    }
    leaves
}

/// Convenience wrapper that expands first. Callers that also need the
/// conditioning bytes should expand once and use `grid_row_leaves_from_cond`.
pub fn grid_row_leaves(s: &[u8; 32]) -> Vec<Digest> {
    grid_row_leaves_from_cond(&expand_all(s))
}

/// Leaf index for a typed (channel, octave, grid row) address.
pub fn leaf_index(chan: usize, oct: usize, row: usize) -> usize {
    let mut idx = chan * GRID_ROWS_PER_CHANNEL;
    for o in 0..oct {
        idx += GRID_H[o];
    }
    idx + row
}

fn node(l: &Digest, r: &Digest) -> Digest {
    let mut h = blake3p::Hasher::new();
    h.update(DOM_NODE);
    h.update(l);
    h.update(r);
    h.finalize()
}

/// Binary Merkle root; an odd node at any level is paired with itself.
pub fn merkle_root(leaves: &[Digest]) -> Digest {
    assert!(!leaves.is_empty(), "merkle over zero leaves");
    let mut level: Vec<Digest> = leaves.to_vec();
    while level.len() > 1 {
        let mut next = Vec::with_capacity(level.len().div_ceil(2));
        let mut i = 0;
        while i < level.len() {
            let l = level[i];
            let r = if i + 1 < level.len() {
                level[i + 1]
            } else {
                level[i]
            };
            next.push(node(&l, &r));
            i += 2;
        }
        level = next;
    }
    level[0]
}

pub fn merkle_path(leaves: &[Digest], index: usize) -> Vec<Digest> {
    let mut path = Vec::new();
    let mut level: Vec<Digest> = leaves.to_vec();
    let mut idx = index;
    while level.len() > 1 {
        let sib = idx ^ 1;
        path.push(if sib < level.len() {
            level[sib]
        } else {
            level[idx]
        });
        let mut next = Vec::with_capacity(level.len().div_ceil(2));
        let mut i = 0;
        while i < level.len() {
            let l = level[i];
            let r = if i + 1 < level.len() {
                level[i + 1]
            } else {
                level[i]
            };
            next.push(node(&l, &r));
            i += 2;
        }
        level = next;
        idx /= 2;
    }
    path
}

/// Recompute a root from a leaf and its sibling path.
pub fn merkle_verify(leaf: &Digest, index: usize, path: &[Digest]) -> Digest {
    let mut acc = *leaf;
    let mut idx = index;
    for sib in path {
        acc = if idx % 2 == 0 {
            node(&acc, sib)
        } else {
            node(sib, &acc)
        };
        idx /= 2;
    }
    acc
}

// ------------------------------------------------------- v9 chain transition

/// The v9 per-row chain-advance domain tag, from
/// `recording/protocol/session_schema.py:204`.
pub const ROW_DOMAIN_TAG: &[u8] = b"TB:ROW:v9";
/// Capture-meta struct width, `META_STRUCT = ">IQQI4s"`.
pub const META_BYTES: usize = 28;

/// The v9 chain advance, length-prefixed exactly as `compute_chain_row` does:
///
/// ```text
/// S_{t+1} = BLAKE3( b"TB:ROW:v9" || S_t
///                   || len32(bayer_hash)        || bayer_hash        (32 B)
///                   || len32(meta_bytes)        || meta_bytes        (28 B)
///                   || len32(drand_round_be8)   || drand_round_be8   ( 8 B)
///                   || len32(drand_round_value) || drand_round_value (32 B) )
/// ```
///
/// Every length prefix is 4-byte BIG-endian, and the drand round number is
/// 8-byte big-endian. MEASURED to reproduce every advance of august_dev_712
/// (711/711) and d2 (5991/5991). It does NOT reproduce v10, which carries two
/// extra `ai_payload_*` columns and is not re-walkable under this rule; see
/// README.md.
pub fn advance_chain(
    s_t: &[u8; 32],
    bayer_hash: &[u8; 32],
    meta: &[u8; META_BYTES],
    drand_round: u64,
    drand_value: &[u8; 32],
) -> Digest {
    let mut h = blake3p::Hasher::new();
    h.update(ROW_DOMAIN_TAG);
    h.update(s_t);
    h.update(&(32u32.to_be_bytes()));
    h.update(bayer_hash);
    h.update(&((META_BYTES as u32).to_be_bytes()));
    h.update(meta);
    h.update(&(8u32.to_be_bytes()));
    h.update(&drand_round.to_be_bytes());
    h.update(&(32u32.to_be_bytes()));
    h.update(drand_value);
    h.finalize()
}

/// Compressions for one v9 advance: 9 + 32 + 4+32 + 4+28 + 4+8 + 4+32 = 157
/// bytes, so three 64-byte blocks.
pub fn compressions_advance() -> u64 {
    blake3p::compressions(
        ROW_DOMAIN_TAG.len() + 32 + 4 + 32 + 4 + META_BYTES + 4 + 8 + 4 + 32,
        32,
    )
}

/// Per-row commitment binding a chain state to its grid-set root.
pub fn row_commit(s: &[u8; 32], grid_root: &Digest) -> Digest {
    let mut h = blake3p::Hasher::new();
    h.update(DOM_ROW);
    h.update(s);
    h.update(grid_root);
    h.finalize()
}

// ---------------------------------------------------------------- render maths

/// Bilinear tap tables for one axis of one octave, computed by exact integer
/// stepping so the guest performs two divisions per axis rather than one per
/// output sample. `i0[k]`, `i1[k]` are grid indices and `f[k]` the 16-bit
/// fraction, exactly `floor(k * (g-1) * 65536 / (n-1))` split into whole and
/// fractional parts, matching `tile_cpu._tables`.
pub struct Taps {
    pub i0: Vec<u16>,
    pub i1: Vec<u16>,
    pub f: Vec<i64>,
}

pub fn taps(grid: usize, out: usize) -> Taps {
    let num = ((grid - 1) as i64) * SS;
    let den = core::cmp::max(out as i64 - 1, 1);
    let q_step = num / den;
    let r_step = num % den;
    let mut i0 = Vec::with_capacity(out);
    let mut i1 = Vec::with_capacity(out);
    let mut f = Vec::with_capacity(out);
    let mut q: i64 = 0;
    let mut r: i64 = 0;
    for _ in 0..out {
        let idx = q >> SB;
        i0.push(idx as u16);
        i1.push(core::cmp::min(idx + 1, grid as i64 - 1) as u16);
        f.push(q & MASK);
        q += q_step;
        r += r_step;
        if r >= den {
            q += 1;
            r -= den;
        }
    }
    Taps { i0, i1, f }
}

pub struct RenderTables {
    pub x: Vec<Taps>,
    pub y: Vec<Taps>,
}

impl RenderTables {
    pub fn new() -> Self {
        Self {
            x: (0..NUM_OCTAVES).map(|o| taps(GRID_W[o], TILE_W)).collect(),
            y: (0..NUM_OCTAVES).map(|o| taps(GRID_H[o], TILE_H)).collect(),
        }
    }
}

impl Default for RenderTables {
    fn default() -> Self {
        Self::new()
    }
}

/// One output row of one channel, over the x-range `[x0, x0+w)`.
/// Bit-exact to `tile_cpu.gen_channel_v2`: int32 horizontal accumulation,
/// int64 vertical, `>>16`, octave weight `>>o`, `+128`, clip.
#[allow(clippy::needless_range_loop)]
pub fn render_row(
    stream: &[u8],
    tables: &RenderTables,
    y: usize,
    x0: usize,
    w: usize,
    out: &mut [u8],
) {
    // OPTIMISED_I32_RENDER: identical integer semantics, 32-bit operands.
    // SP1 targets RV32IM, so every i64 multiply above was emulated. Ranges:
    //   g in [-128,127]; |top|,|bot| <= 128<<16 = 8_388_608 (fits i32)
    //   top*(SS-fy) needs 40 bits, so only that product widens to i64
    //   |v| <= 8_388_608, |acc| <= ~1.6e7 (both fit i32)
    let mut acc = vec![0i32; w];
    for o in 0..NUM_OCTAVES {
        let gw = GRID_W[o];
        let goff = octave_offset(o);
        let ty = &tables.y[o];
        let tx = &tables.x[o];
        let iy = ty.i0[y] as usize;
        let iyn = ty.i1[y] as usize;
        let fy = ty.f[y] as i32;
        let ss = SS as i32;
        let _ss_minus_fy = ss - fy;
        let rt = goff + iy * gw;
        let rb = goff + iyn * gw;
        let row_t = &stream[rt..rt + gw];
        let row_b = &stream[rb..rb + gw];
        for k in 0..w {
            let x = x0 + k;
            let ix = tx.i0[x] as usize;
            let ixn = tx.i1[x] as usize;
            let fx = tx.f[x] as i32;
            let _ss_minus_fx = ss - fx;
            // OPTIMISED_LERP_V2: exact integer identities, fewer multiplies.
            //   a*(S-f) + b*f  ==  a*S + (b-a)*f          (exact, no shift)
            //   (top*S + (bot-top)*fy) >> 16 == top + (((bot-top)*fy) >> 16)
            // because top*S is an exact multiple of S = 1<<16 and >> is floor.
            // Six multiplies per pixel-octave become two, one of them widening.
            let g_tl = row_t[ix] as i32 - 128;
            let g_tr = row_t[ixn] as i32 - 128;
            let g_bl = row_b[ix] as i32 - 128;
            let g_br = row_b[ixn] as i32 - 128;
            let top = (g_tl << 16) + (g_tr - g_tl) * fx;
            let bot = (g_bl << 16) + (g_br - g_bl) * fx;
            let v = top + ((((bot - top) as i64) * (fy as i64)) >> 16) as i32;
            if o == 0 {
                acc[k] = v;
            } else {
                acc[k] += v >> o;
            }
        }
    }
    for k in 0..w {
        let p = (acc[k] >> 16) + 128;
        out[k] = if p < 0 {
            0
        } else if p > 255 {
            255
        } else {
            p as u8
        };
    }
}

/// Interleaved RGB for one output row over `[x0, x0+w)`.
pub fn render_row_rgb(
    cond: &[u8],
    tables: &RenderTables,
    y: usize,
    x0: usize,
    w: usize,
    out: &mut [u8],
) {
    let mut chan = vec![0u8; w];
    for c in 0..CHANNELS {
        let stream = &cond[c * TOTAL_BYTES_PER_CHANNEL..(c + 1) * TOTAL_BYTES_PER_CHANNEL];
        render_row(stream, tables, y, x0, w, &mut chan);
        for k in 0..w {
            out[k * CHANNELS + c] = chan[k];
        }
    }
}

// ----------------------------------------------------------------- statement

pub const WITNESS_MAGIC: &[u8; 8] = b"TBZKW3V2";
pub const PUBLIC_MAGIC: &[u8; 8] = b"TBZKB3V1";
pub const HEADER_BYTES: usize = 16;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
#[repr(u8)]
pub enum Mode {
    /// Seed derivation only: 3 BLAKE3 compressions. Cost calibration.
    Seeds = 0,
    /// Full XOF expansion, committed as three per-channel stream digests.
    Expand = 1,
    /// Expansion plus the 762-leaf Merkle root over the octave grid rows.
    Grids = 2,
    /// Grids plus an exact integer render of one tile cell, published verbatim.
    Cell = 3,
    /// Grids plus the whole-tile BLAKE3 digest, comparable to chain_log's
    /// `emission_live_pixel_blake3_hex`.
    Tile = 4,
    /// Many rows amortised into one statement.
    Batch = 5,
    /// A typed grid-row opening checked against a Merkle path.
    Open = 6,
    /// The v9 chain advance alone: S_t + row evidence -> S_{t+1}.
    Advance = 7,
    /// The FULL same-row relation: raw Bayer bytes -> BLAKE3(C_t) matching the
    /// committed digest, the v9 advance to S_{t+1}, and the expansion of S_t
    /// through to the exact 1080x1920 emission digest. One statement, one row.
    Row = 8,
}

impl Mode {
    pub fn from_u8(v: u8) -> Option<Self> {
        Some(match v {
            0 => Mode::Seeds,
            1 => Mode::Expand,
            2 => Mode::Grids,
            3 => Mode::Cell,
            4 => Mode::Tile,
            5 => Mode::Batch,
            6 => Mode::Open,
            7 => Mode::Advance,
            8 => Mode::Row,
            _ => return None,
        })
    }
}

/// What a `Row`-mode statement must reproduce. Each field is a value already
/// published in `chain_log.csv`, so a verifier holding only the public log can
/// check the public values without being shown any pixel.
pub struct RowEvidence {
    pub bayer_hash: [u8; 32],
    pub meta: [u8; META_BYTES],
    pub drand_round: u64,
    pub drand_value: [u8; 32],
    /// Optional raw Bayer frame. When present the guest hashes it and requires
    /// the digest to equal `bayer_hash`, which binds the capture side too.
    pub bayer_raw: Vec<u8>,
    /// Render and digest the whole 1920x1080 emission when set.
    pub want_tile: bool,
}

/// Maximum published cell, so the public journal stays small.
pub const MAX_CELL: usize = 8;

/// Fixed witness header width. Everything positional, so the guest's parse is
/// a handful of loads and cannot be confused by a truncated tail.
pub const WITNESS_HEADER_BYTES: usize = 160;

pub struct Witness {
    pub mode: Mode,
    pub states: Vec<[u8; 32]>,
    /// Cell mode: (x0, y0, w, h).
    pub cell: (u32, u32, u32, u32),
    /// Open mode: leaf address and the claimed grid-row bytes.
    pub open_chan: u32,
    pub open_oct: u32,
    pub open_row: u32,
    pub open_bytes: Vec<u8>,
    pub open_path: Vec<Digest>,
    /// Advance and Row modes: the published per-row evidence.
    pub evidence: RowEvidence,
    /// Claimed values the guest must reproduce exactly, or abort.
    pub claim: Vec<u8>,
}

fn rd_u32(b: &[u8], o: usize) -> u32 {
    u32::from_le_bytes([b[o], b[o + 1], b[o + 2], b[o + 3]])
}

fn rd_u64(b: &[u8], o: usize) -> u64 {
    let mut w = [0u8; 8];
    w.copy_from_slice(&b[o..o + 8]);
    u64::from_le_bytes(w)
}

impl Witness {
    /// Layout. Scalars are little endian ON THE WIRE; the big-endian encoding
    /// the protocol hashes is applied inside `advance_chain`.
    /// ```text
    ///   0..8    magic "TBZKW3V2"
    ///   8       mode
    ///   9       flags: bit0 = render and digest the whole tile
    ///  10..12   n_rows u16
    ///  12..16   claim_len u32
    ///  16..32   cell x0,y0,w,h  (u32 x4)
    ///  32..44   open chan,oct,row (u32 x3)
    ///  44..48   n_path u32
    ///  48..52   open_bytes_len u32
    ///  52..56   bayer_raw_len u32
    ///  56..64   drand_round u64
    ///  64..96   bayer_hash
    ///  96..128  drand_value
    /// 128..156  meta (28 bytes, verbatim protocol struct)
    /// 156..160  reserved, must be zero
    /// 160..     n_rows*32 states, claim, open_bytes, path, bayer_raw
    /// ```
    pub fn parse(b: &[u8]) -> Result<Self, &'static str> {
        if b.len() < WITNESS_HEADER_BYTES {
            return Err("witness shorter than header");
        }
        if &b[0..8] != WITNESS_MAGIC {
            return Err("witness magic mismatch");
        }
        let mode = Mode::from_u8(b[8]).ok_or("unknown mode")?;
        let flags = b[9];
        if flags & !0x01 != 0 {
            return Err("unknown witness flag bits");
        }
        let n_rows = u16::from_le_bytes([b[10], b[11]]) as usize;
        if n_rows == 0 {
            return Err("zero rows");
        }
        let claim_len = rd_u32(b, 12) as usize;
        let cell = (rd_u32(b, 16), rd_u32(b, 20), rd_u32(b, 24), rd_u32(b, 28));
        let open_chan = rd_u32(b, 32);
        let open_oct = rd_u32(b, 36);
        let open_row = rd_u32(b, 40);
        let n_path = rd_u32(b, 44) as usize;
        let open_len = rd_u32(b, 48) as usize;
        let bayer_len = rd_u32(b, 52) as usize;
        let drand_round = rd_u64(b, 56);
        let mut bayer_hash = [0u8; 32];
        bayer_hash.copy_from_slice(&b[64..96]);
        let mut drand_value = [0u8; 32];
        drand_value.copy_from_slice(&b[96..128]);
        let mut meta = [0u8; META_BYTES];
        meta.copy_from_slice(&b[128..128 + META_BYTES]);
        if b[156..160] != [0u8; 4] {
            return Err("reserved header bytes set");
        }

        let mut off = WITNESS_HEADER_BYTES;
        let need = n_rows * 32 + claim_len + open_len + n_path * 32 + bayer_len;
        if b.len() != off + need {
            return Err("witness length does not match declared fields");
        }
        let mut states = Vec::with_capacity(n_rows);
        for _ in 0..n_rows {
            let mut s = [0u8; 32];
            s.copy_from_slice(&b[off..off + 32]);
            states.push(s);
            off += 32;
        }
        let claim = b[off..off + claim_len].to_vec();
        off += claim_len;
        let open_bytes = b[off..off + open_len].to_vec();
        off += open_len;
        let mut open_path = Vec::with_capacity(n_path);
        for _ in 0..n_path {
            let mut d = [0u8; 32];
            d.copy_from_slice(&b[off..off + 32]);
            open_path.push(d);
            off += 32;
        }
        let bayer_raw = b[off..off + bayer_len].to_vec();
        Ok(Self {
            mode,
            states,
            cell,
            open_chan,
            open_oct,
            open_row,
            open_bytes,
            open_path,
            evidence: RowEvidence {
                bayer_hash,
                meta,
                drand_round,
                drand_value,
                bayer_raw,
                want_tile: flags & 0x01 != 0,
            },
            claim,
        })
    }
}

/// Public-values builder. Header is magic, mode, reserved, n_rows, payload_len.
pub struct PublicBuilder {
    pub bytes: Vec<u8>,
}

impl PublicBuilder {
    pub fn new(mode: Mode, n_rows: u16) -> Self {
        let mut bytes = Vec::with_capacity(256);
        bytes.extend_from_slice(PUBLIC_MAGIC);
        bytes.push(mode as u8);
        bytes.push(0);
        bytes.extend_from_slice(&n_rows.to_le_bytes());
        bytes.extend_from_slice(&0u32.to_le_bytes()); // payload_len, patched below
        Self { bytes }
    }
    pub fn push(&mut self, b: &[u8]) {
        self.bytes.extend_from_slice(b);
    }
    pub fn push_u32(&mut self, v: u32) {
        self.bytes.extend_from_slice(&v.to_le_bytes());
    }
    pub fn finish(mut self) -> Vec<u8> {
        let n = (self.bytes.len() - HEADER_BYTES) as u32;
        self.bytes[12..16].copy_from_slice(&n.to_le_bytes());
        self.bytes
    }
}

/// Evaluate the relation. Returns the public values, or `Err` if the witness's
/// claimed values do not match the protocol-mandated ones. Both the guest and
/// the host native path call exactly this function, so a native/SP1 divergence
/// is detectable.
pub fn evaluate(w: &Witness) -> Result<Vec<u8>, &'static str> {
    let mut pb = PublicBuilder::new(w.mode, w.states.len() as u16);
    match w.mode {
        Mode::Seeds => {
            let s = &w.states[0];
            let seeds = derive_seeds(s);
            pb.push(s);
            for c in 0..CHANNELS {
                pb.push(&seeds[c]);
            }
        }
        Mode::Expand => {
            let s = &w.states[0];
            let seeds = derive_seeds(s);
            pb.push(s);
            let mut buf = vec![0u8; TOTAL_BYTES_PER_CHANNEL];
            for c in 0..CHANNELS {
                blake3p::xof(&seeds[c], &mut buf);
                pb.push(&blake3p::hash(&buf));
            }
        }
        Mode::Grids => {
            let s = &w.states[0];
            let root = merkle_root(&grid_row_leaves(s));
            pb.push(s);
            pb.push(&root);
        }
        Mode::Cell => {
            let s = &w.states[0];
            let (x0, y0, cw, ch) = w.cell;
            if cw as usize > MAX_CELL || ch as usize > MAX_CELL || cw == 0 || ch == 0 {
                return Err("cell size out of range");
            }
            if x0 as usize + cw as usize > TILE_W || y0 as usize + ch as usize > TILE_H {
                return Err("cell out of tile bounds");
            }
            let cond = expand_all(s);
            let root = merkle_root(&grid_row_leaves_from_cond(&cond));
            let tables = RenderTables::new();
            let mut cell = vec![0u8; (cw as usize) * (ch as usize) * CHANNELS];
            for r in 0..ch as usize {
                let dst = r * (cw as usize) * CHANNELS;
                render_row_rgb(
                    &cond,
                    &tables,
                    y0 as usize + r,
                    x0 as usize,
                    cw as usize,
                    &mut cell[dst..dst + (cw as usize) * CHANNELS],
                );
            }
            pb.push(s);
            pb.push(&root);
            pb.push_u32(x0);
            pb.push_u32(y0);
            pb.push_u32(cw);
            pb.push_u32(ch);
            pb.push(&cell);
        }
        Mode::Tile => {
            let s = &w.states[0];
            let cond = expand_all(s);
            let root = merkle_root(&grid_row_leaves_from_cond(&cond));
            let tables = RenderTables::new();
            let mut h = blake3p::Hasher::new();
            let mut row = vec![0u8; TILE_W * CHANNELS];
            for y in 0..TILE_H {
                render_row_rgb(&cond, &tables, y, 0, TILE_W, &mut row);
                h.update(&row);
            }
            let tile_digest = h.finalize();
            pb.push(s);
            pb.push(&root);
            pb.push(&tile_digest);
        }
        Mode::Batch => {
            // One statement over many rows. Public values are O(1) in the row
            // count: a commitment to the state list and a Merkle root over the
            // per-row commitments.
            let mut sh = blake3p::Hasher::new();
            sh.update(DOM_STATES);
            let mut row_commits = Vec::with_capacity(w.states.len());
            for s in &w.states {
                sh.update(s);
                let root = merkle_root(&grid_row_leaves(s));
                row_commits.push(row_commit(s, &root));
            }
            let states_commit = sh.finalize();
            let rows_root = merkle_root(&row_commits);
            pb.push(&states_commit);
            pb.push(&rows_root);
            pb.push(&w.states[0]);
            pb.push(&w.states[w.states.len() - 1]);
        }
        Mode::Open => {
            let s = &w.states[0];
            let chan = w.open_chan as usize;
            let oct = w.open_oct as usize;
            let row = w.open_row as usize;
            if chan >= CHANNELS || oct >= NUM_OCTAVES || row >= GRID_H[oct] {
                return Err("grid-row address out of range");
            }
            if w.open_bytes.len() != GRID_W[oct] {
                return Err("claimed grid row has the wrong length");
            }
            let leaves = grid_row_leaves(s);
            let root = merkle_root(&leaves);
            let idx = leaf_index(chan, oct, row);
            // The claimed row bytes must hash to the leaf the protocol mandates.
            let claimed_leaf = blake3p::hash2(&leaf_prefix(chan, oct, row), &w.open_bytes);
            if claimed_leaf != leaves[idx] {
                return Err("claimed grid-row bytes are not the protocol's");
            }
            // ...and the supplied path must open that leaf to that root.
            if merkle_verify(&claimed_leaf, idx, &w.open_path) != root {
                return Err("Merkle path does not open the claimed leaf to the root");
            }
            pb.push(s);
            pb.push(&root);
            pb.push_u32(chan as u32);
            pb.push_u32(oct as u32);
            pb.push_u32(row as u32);
            pb.push(&claimed_leaf);
            pb.push(&w.open_bytes);
        }
        Mode::Advance => {
            // S_t plus the published row evidence determines S_{t+1}.
            let s = &w.states[0];
            let e = &w.evidence;
            let s_next = advance_chain(s, &e.bayer_hash, &e.meta, e.drand_round, &e.drand_value);
            pb.push(s);
            pb.push(&s_next);
            pb.push(&e.bayer_hash);
            pb.push(&e.meta);
            pb.push(&e.drand_value);
            pb.push(&e.drand_round.to_be_bytes());
        }
        Mode::Row => {
            // The full same-row relation, in one statement:
            //   (a) raw Bayer bytes hash to the committed bayer digest,
            //   (b) that digest advances S_t to S_{t+1} under the v9 rule,
            //   (c) S_t expands to the mandated octave grids, and
            //   (d) those grids render to the exact 1080x1920 emission whose
            //       BLAKE3 digest chain_log publishes.
            let s = &w.states[0];
            let e = &w.evidence;

            // (a) Camera side. Only checkable when the frame is supplied.
            let bayer_bound = if e.bayer_raw.is_empty() {
                false
            } else {
                if blake3p::hash(&e.bayer_raw) != e.bayer_hash {
                    return Err("raw Bayer bytes do not hash to the committed digest");
                }
                true
            };

            // (b) Chain advance.
            let s_next = advance_chain(s, &e.bayer_hash, &e.meta, e.drand_round, &e.drand_value);

            // (c) Expansion and the grid commitment.
            let cond = expand_all(s);
            let root = merkle_root(&grid_row_leaves_from_cond(&cond));

            // (d) The exact 1080x1920 emission, streamed a row at a time so the
            // guest never holds the 6,220,800-byte frame.
            let tile_digest = if e.want_tile {
                let tables = RenderTables::new();
                let mut h = blake3p::Hasher::new();
                let mut row = vec![0u8; TILE_W * CHANNELS];
                for y in 0..TILE_H {
                    render_row_rgb(&cond, &tables, y, 0, TILE_W, &mut row);
                    h.update(&row);
                }
                h.finalize()
            } else {
                [0u8; 32]
            };

            pb.push(s);
            pb.push(&s_next);
            pb.push(&e.bayer_hash);
            pb.push(&root);
            pb.push(&tile_digest);
            pb.push_u32(u32::from(bayer_bound));
            pb.push_u32(u32::from(e.want_tile));
            pb.push_u32(e.bayer_raw.len() as u32);
        }
    }
    let public = pb.finish();
    // The witness carries the claim; the relation is only satisfied if the
    // protocol-mandated public values equal it exactly.
    if !w.claim.is_empty() && w.claim != public {
        return Err("claimed public values differ from the protocol's");
    }
    Ok(public)
}

/// BLAKE3 compressions for the three seed derivations of one row.
pub fn compressions_seeds() -> u64 {
    CHANNELS as u64 * blake3p::compressions(SEED_TAGS[0].len() + 32, 32)
}

/// BLAKE3 compressions for the three 43,110-byte XOF expansions of one row.
pub fn compressions_xof() -> u64 {
    CHANNELS as u64 * blake3p::compressions(32, TOTAL_BYTES_PER_CHANNEL)
}

/// BLAKE3 compressions for the 762 typed grid-row leaves of one row.
pub fn compressions_leaves() -> u64 {
    let mut leaf = 0u64;
    for _c in 0..CHANNELS {
        for (o, &gw) in GRID_W.iter().enumerate() {
            leaf += GRID_H[o] as u64 * blake3p::compressions(LEAF_PREFIX_BYTES + gw, 32);
        }
    }
    leaf
}

/// BLAKE3 compressions for the Merkle tree over `n` leaves (odd node duplicated).
pub fn compressions_merkle(n_leaves: usize) -> u64 {
    let mut nodes = 0u64;
    let mut n = n_leaves;
    while n > 1 {
        n = n.div_ceil(2);
        nodes += n as u64;
    }
    // Each internal node is BLAKE3 over 13 + 32 + 32 = 77 bytes: two blocks.
    nodes * blake3p::compressions(DOM_NODE.len() + 64, 32)
}

/// Cost of the full same-row relation, broken out by which legs are included.
/// `bayer_len` is 0 when the raw frame is not supplied.
pub fn compressions_row(bayer_len: usize, want_tile: bool) -> u64 {
    let mut n = compressions_seeds()
        + compressions_xof()
        + compressions_leaves()
        + compressions_merkle(GRID_LEAVES)
        + compressions_advance();
    if bayer_len > 0 {
        n += blake3p::compressions(bayer_len, 32);
    }
    if want_tile {
        n += blake3p::compressions(TILE_BYTES, 32);
    }
    n
}

/// Analytic BLAKE3 compression cost of each mode, per row. Argued from the
/// structure of the expansion, and checked against the `count` feature in tests.
pub fn compressions_per_row(mode: Mode) -> u64 {
    let seeds = compressions_seeds();
    let xof = compressions_xof();
    let leaf = compressions_leaves();
    let nodes = compressions_merkle(GRID_LEAVES);
    match mode {
        Mode::Seeds => seeds,
        Mode::Expand => {
            seeds + xof + CHANNELS as u64 * blake3p::compressions(TOTAL_BYTES_PER_CHANNEL, 32)
        }
        Mode::Grids | Mode::Cell => seeds + xof + leaf + nodes,
        // Open recomputes the root and additionally checks a 10-node path plus
        // one extra leaf hash.
        Mode::Open => {
            seeds
                + xof
                + leaf
                + nodes
                + blake3p::compressions(LEAF_PREFIX_BYTES + GRID_W[NUM_OCTAVES - 1], 32)
                + 10 * blake3p::compressions(DOM_NODE.len() + 64, 32)
        }
        Mode::Tile => seeds + xof + leaf + nodes + blake3p::compressions(TILE_BYTES, 32),
        Mode::Advance => compressions_advance(),
        // Row mode's cost depends on whether the raw frame and the tile are
        // included; `compressions_row` takes those as arguments.
        Mode::Row => compressions_row(0, false),
        // Per row: the expansion plus one row_commit; the states commitment and
        // the rows Merkle root are amortised and counted separately.
        Mode::Batch => seeds + xof + leaf + nodes + blake3p::compressions(13 + 64, 32),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn octave_layout_is_the_published_one() {
        assert_eq!(OCTAVE_BYTES, [510, 2040, 8160, 32400]);
        assert_eq!(OCTAVE_BYTES.iter().sum::<usize>(), TOTAL_BYTES_PER_CHANNEL);
        assert_eq!(octave_offset(0), 0);
        assert_eq!(octave_offset(1), 510);
        assert_eq!(octave_offset(2), 2550);
        assert_eq!(octave_offset(3), 10710);
        assert_eq!(octave_offset(4), TOTAL_BYTES_PER_CHANNEL);
        assert_eq!(GRID_H.iter().sum::<usize>(), GRID_ROWS_PER_CHANNEL);
        assert_eq!(GRID_LEAVES, 762);
        assert_eq!(CONDITIONING_BYTES, 129_330);
        assert_eq!(TILE_BYTES, 6_220_800);
    }

    #[test]
    fn leaf_index_is_a_bijection_onto_the_leaf_order() {
        let mut seen = vec![false; GRID_LEAVES];
        let mut k = 0usize;
        for c in 0..CHANNELS {
            for o in 0..NUM_OCTAVES {
                for r in 0..GRID_H[o] {
                    let i = leaf_index(c, o, r);
                    assert_eq!(i, k, "leaf order mismatch at ({c},{o},{r})");
                    assert!(!seen[i]);
                    seen[i] = true;
                    k += 1;
                }
            }
        }
        assert_eq!(k, GRID_LEAVES);
        assert!(seen.iter().all(|b| *b));
    }

    #[test]
    fn taps_match_the_reference_table_construction() {
        // Independent recomputation with a division per sample.
        for o in 0..NUM_OCTAVES {
            for (grid, out) in [(GRID_W[o], TILE_W), (GRID_H[o], TILE_H)] {
                let t = taps(grid, out);
                let num = (grid as i64 - 1) * (1 << 16);
                let den = core::cmp::max(out as i64 - 1, 1);
                for k in 0..out {
                    let xs = (k as i64) * num / den;
                    assert_eq!(t.i0[k] as i64, xs >> 16, "i0 o={o} k={k}");
                    assert_eq!(t.f[k], xs & 0xFFFF, "f o={o} k={k}");
                    assert_eq!(
                        t.i1[k] as i64,
                        core::cmp::min((xs >> 16) + 1, grid as i64 - 1),
                        "i1 o={o} k={k}"
                    );
                }
            }
        }
    }

    #[test]
    fn merkle_paths_open_every_leaf() {
        let leaves: Vec<Digest> = (0..GRID_LEAVES)
            .map(|i| blake3p::hash(&(i as u32).to_le_bytes()))
            .collect();
        let root = merkle_root(&leaves);
        for i in [0usize, 1, 2, 380, 381, 760, 761] {
            let path = merkle_path(&leaves, i);
            assert_eq!(merkle_verify(&leaves[i], i, &path), root, "leaf {i}");
            // A wrong sibling must not open.
            if !path.is_empty() {
                let mut bad = path.clone();
                bad[0][0] ^= 1;
                assert_ne!(merkle_verify(&leaves[i], i, &bad), root, "tamper {i}");
            }
            // A wrong index must not open.
            assert_ne!(merkle_verify(&leaves[i], i ^ 1, &path), root, "index {i}");
        }
    }
}
