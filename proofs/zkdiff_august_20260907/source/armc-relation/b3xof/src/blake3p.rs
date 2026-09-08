//! Portable BLAKE3, written for a zkVM guest: `no_std`, no dependencies, no
//! SIMD, no `unsafe`. Follows the BLAKE3 reference implementation exactly
//! (7 rounds, 8 G-functions per round, the documented message permutation, and
//! the chunk / parent / root output flags).
//!
//! Why hand-rolled rather than the `blake3` crate: SP1 v6.4.0 exposes no BLAKE3
//! precompile, so BLAKE3 is compiled to RISC-V either way. Writing it out lets
//! us count compression-function calls exactly and keeps the guest free of
//! `cfg(target_arch)` SIMD paths. It is cross-checked bit-for-bit against the
//! upstream `blake3` crate and against Python `blake3` in the host tests.

pub const OUT_LEN: usize = 32;
pub const BLOCK_LEN: usize = 64;
pub const CHUNK_LEN: usize = 1024;

const CHUNK_START: u32 = 1 << 0;
const CHUNK_END: u32 = 1 << 1;
const PARENT: u32 = 1 << 2;
const ROOT: u32 = 1 << 3;

const IV: [u32; 8] = [
    0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A, 0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19,
];

const MSG_PERMUTATION: [usize; 16] = [2, 6, 3, 10, 7, 0, 4, 13, 1, 11, 12, 5, 9, 14, 15, 8];

/// Number of compression-function calls, for cost accounting. Only compiled
/// when the `count` feature is on, so the guest pays nothing for it.
#[cfg(feature = "count")]
pub mod counter {
    use core::sync::atomic::{AtomicU64, Ordering};
    static N: AtomicU64 = AtomicU64::new(0);
    pub fn bump() {
        N.fetch_add(1, Ordering::Relaxed);
    }
    pub fn reset() {
        N.store(0, Ordering::Relaxed);
    }
    pub fn get() -> u64 {
        N.load(Ordering::Relaxed)
    }
}

#[inline(always)]
#[allow(clippy::too_many_arguments)]
fn g(state: &mut [u32; 16], a: usize, b: usize, c: usize, d: usize, mx: u32, my: u32) {
    state[a] = state[a].wrapping_add(state[b]).wrapping_add(mx);
    state[d] = (state[d] ^ state[a]).rotate_right(16);
    state[c] = state[c].wrapping_add(state[d]);
    state[b] = (state[b] ^ state[c]).rotate_right(12);
    state[a] = state[a].wrapping_add(state[b]).wrapping_add(my);
    state[d] = (state[d] ^ state[a]).rotate_right(8);
    state[c] = state[c].wrapping_add(state[d]);
    state[b] = (state[b] ^ state[c]).rotate_right(7);
}

#[inline(always)]
fn round(state: &mut [u32; 16], m: &[u32; 16]) {
    g(state, 0, 4, 8, 12, m[0], m[1]);
    g(state, 1, 5, 9, 13, m[2], m[3]);
    g(state, 2, 6, 10, 14, m[4], m[5]);
    g(state, 3, 7, 11, 15, m[6], m[7]);
    g(state, 0, 5, 10, 15, m[8], m[9]);
    g(state, 1, 6, 11, 12, m[10], m[11]);
    g(state, 2, 7, 8, 13, m[12], m[13]);
    g(state, 3, 4, 9, 14, m[14], m[15]);
}

#[inline(always)]
fn permute(m: &mut [u32; 16]) {
    let mut p = [0u32; 16];
    let mut i = 0;
    while i < 16 {
        p[i] = m[MSG_PERMUTATION[i]];
        i += 1;
    }
    *m = p;
}

#[inline(always)]
fn words_from_block(block: &[u8; BLOCK_LEN]) -> [u32; 16] {
    let mut w = [0u32; 16];
    let mut i = 0;
    while i < 16 {
        w[i] = u32::from_le_bytes([
            block[4 * i],
            block[4 * i + 1],
            block[4 * i + 2],
            block[4 * i + 3],
        ]);
        i += 1;
    }
    w
}

/// The BLAKE3 compression function. Returns the full 16-word output state with
/// the reference implementation's final feed-forward already applied, so
/// `out[0..8]` is the chaining value and all 16 words are the root output block.
fn compress(
    cv: &[u32; 8],
    block_words: &[u32; 16],
    counter: u64,
    block_len: u32,
    flags: u32,
) -> [u32; 16] {
    #[cfg(feature = "count")]
    counter::bump();
    let mut state = [
        cv[0],
        cv[1],
        cv[2],
        cv[3],
        cv[4],
        cv[5],
        cv[6],
        cv[7],
        IV[0],
        IV[1],
        IV[2],
        IV[3],
        counter as u32,
        (counter >> 32) as u32,
        block_len,
        flags,
    ];
    let mut block = *block_words;
    let mut r = 0;
    while r < 6 {
        round(&mut state, &block);
        permute(&mut block);
        r += 1;
    }
    round(&mut state, &block);
    let mut i = 0;
    while i < 8 {
        state[i] ^= state[i + 8];
        state[i + 8] ^= cv[i];
        i += 1;
    }
    state
}

#[inline(always)]
fn first8(words: &[u32; 16]) -> [u32; 8] {
    [
        words[0], words[1], words[2], words[3], words[4], words[5], words[6], words[7],
    ]
}

/// A finalised node that can emit an unbounded root output stream (the XOF).
#[derive(Clone, Copy)]
pub struct Output {
    input_cv: [u32; 8],
    block_words: [u32; 16],
    block_len: u32,
    counter: u64,
    flags: u32,
}

impl Output {
    fn chaining_value(&self) -> [u32; 8] {
        first8(&compress(
            &self.input_cv,
            &self.block_words,
            self.counter,
            self.block_len,
            self.flags,
        ))
    }

    /// Fill `out` with the root output stream. Each 64 bytes costs exactly one
    /// compression call.
    pub fn root_output_bytes(&self, out: &mut [u8]) {
        let mut block_counter: u64 = 0;
        let mut off = 0usize;
        while off < out.len() {
            let words = compress(
                &self.input_cv,
                &self.block_words,
                block_counter,
                self.block_len,
                self.flags | ROOT,
            );
            let take = core::cmp::min(BLOCK_LEN, out.len() - off);
            let mut i = 0;
            while i < take {
                out[off + i] = words[i / 4].to_le_bytes()[i % 4];
                i += 1;
            }
            off += take;
            block_counter += 1;
        }
    }
}

#[derive(Clone, Copy)]
struct ChunkState {
    cv: [u32; 8],
    counter: u64,
    block: [u8; BLOCK_LEN],
    block_len: u8,
    blocks_compressed: u8,
    flags: u32,
}

impl ChunkState {
    const fn new(counter: u64, flags: u32) -> Self {
        Self {
            cv: IV,
            counter,
            block: [0; BLOCK_LEN],
            block_len: 0,
            blocks_compressed: 0,
            flags,
        }
    }

    fn len(&self) -> usize {
        BLOCK_LEN * self.blocks_compressed as usize + self.block_len as usize
    }

    fn start_flag(&self) -> u32 {
        if self.blocks_compressed == 0 {
            CHUNK_START
        } else {
            0
        }
    }

    fn update(&mut self, mut input: &[u8]) {
        while !input.is_empty() {
            if self.block_len as usize == BLOCK_LEN {
                let words = words_from_block(&self.block);
                self.cv = first8(&compress(
                    &self.cv,
                    &words,
                    self.counter,
                    BLOCK_LEN as u32,
                    self.flags | self.start_flag(),
                ));
                self.blocks_compressed += 1;
                self.block = [0; BLOCK_LEN];
                self.block_len = 0;
            }
            let want = BLOCK_LEN - self.block_len as usize;
            let take = core::cmp::min(want, input.len());
            self.block[self.block_len as usize..self.block_len as usize + take]
                .copy_from_slice(&input[..take]);
            self.block_len += take as u8;
            input = &input[take..];
        }
    }

    fn output(&self) -> Output {
        Output {
            input_cv: self.cv,
            block_words: words_from_block(&self.block),
            block_len: self.block_len as u32,
            counter: self.counter,
            flags: self.flags | self.start_flag() | CHUNK_END,
        }
    }
}

fn parent_output(left: &[u32; 8], right: &[u32; 8], flags: u32) -> Output {
    let mut block = [0u8; BLOCK_LEN];
    let mut i = 0;
    while i < 8 {
        block[4 * i..4 * i + 4].copy_from_slice(&left[i].to_le_bytes());
        block[32 + 4 * i..32 + 4 * i + 4].copy_from_slice(&right[i].to_le_bytes());
        i += 1;
    }
    Output {
        input_cv: IV,
        block_words: words_from_block(&block),
        block_len: BLOCK_LEN as u32,
        counter: 0,
        flags: flags | PARENT,
    }
}

/// Incremental BLAKE3 hasher. Depth 54 covers any input up to 2^54 chunks.
pub struct Hasher {
    chunk: ChunkState,
    stack: [[u32; 8]; 54],
    stack_len: usize,
    flags: u32,
}

impl Default for Hasher {
    fn default() -> Self {
        Self::new()
    }
}

impl Hasher {
    pub const fn new() -> Self {
        Self {
            chunk: ChunkState::new(0, 0),
            stack: [[0u32; 8]; 54],
            stack_len: 0,
            flags: 0,
        }
    }

    fn push(&mut self, cv: [u32; 8]) {
        self.stack[self.stack_len] = cv;
        self.stack_len += 1;
    }

    fn pop(&mut self) -> [u32; 8] {
        self.stack_len -= 1;
        self.stack[self.stack_len]
    }

    fn add_chunk_cv(&mut self, mut new_cv: [u32; 8], mut total_chunks: u64) {
        while total_chunks & 1 == 0 {
            let left = self.pop();
            new_cv = parent_output(&left, &new_cv, self.flags).chaining_value();
            total_chunks >>= 1;
        }
        self.push(new_cv);
    }

    pub fn update(&mut self, mut input: &[u8]) {
        while !input.is_empty() {
            if self.chunk.len() == CHUNK_LEN {
                let cv = self.chunk.output().chaining_value();
                let total = self.chunk.counter + 1;
                self.add_chunk_cv(cv, total);
                self.chunk = ChunkState::new(total, self.flags);
            }
            let want = CHUNK_LEN - self.chunk.len();
            let take = core::cmp::min(want, input.len());
            self.chunk.update(&input[..take]);
            input = &input[take..];
        }
    }

    pub fn finalize_output(&self) -> Output {
        let mut out = self.chunk.output();
        let mut remaining = self.stack_len;
        while remaining > 0 {
            remaining -= 1;
            out = parent_output(&self.stack[remaining], &out.chaining_value(), self.flags);
        }
        out
    }

    pub fn finalize(&self) -> [u8; OUT_LEN] {
        let mut d = [0u8; OUT_LEN];
        self.finalize_output().root_output_bytes(&mut d);
        d
    }

    pub fn finalize_xof(&self, out: &mut [u8]) {
        self.finalize_output().root_output_bytes(out);
    }
}

/// One-shot 32-byte digest.
pub fn hash(input: &[u8]) -> [u8; OUT_LEN] {
    let mut h = Hasher::new();
    h.update(input);
    h.finalize()
}

/// One-shot two-part 32-byte digest, avoids concatenating in the caller.
pub fn hash2(a: &[u8], b: &[u8]) -> [u8; OUT_LEN] {
    let mut h = Hasher::new();
    h.update(a);
    h.update(b);
    h.finalize()
}

/// One-shot XOF.
pub fn xof(input: &[u8], out: &mut [u8]) {
    let mut h = Hasher::new();
    h.update(input);
    h.finalize_xof(out);
}

/// Exact compression-function call count for `hash`/`xof` of a single input.
///
/// A message of `n` bytes occupies `chunks = max(1, ceil(n/1024))` chunks.
/// Every chunk costs `ceil(len/64)` (min 1) block compressions, except that the
/// final block of the final chunk is not compressed during absorption: it is
/// re-compressed once per 64 bytes of output as the root node. A tree of
/// `chunks` leaves costs `chunks - 1` parent compressions, and when `chunks > 1`
/// the last parent likewise becomes the root output node.
pub fn compressions(in_len: usize, out_len: usize) -> u64 {
    const BPC: u64 = (CHUNK_LEN / BLOCK_LEN) as u64; // 16 blocks per chunk
    let out_blocks = out_len.div_ceil(BLOCK_LEN).max(1) as u64;
    let chunks = in_len.div_ceil(CHUNK_LEN).max(1) as u64;
    // Length of the final chunk, and its block count (min 1).
    let last_len = if in_len == 0 {
        0
    } else {
        let r = in_len % CHUNK_LEN;
        if r == 0 {
            CHUNK_LEN
        } else {
            r
        }
    };
    let last_blocks = last_len.div_ceil(BLOCK_LEN).max(1) as u64;

    if chunks == 1 {
        // The chunk's final block is the root node: absorption only, then XOF.
        (last_blocks - 1) + out_blocks
    } else {
        // Every non-final chunk costs BPC (absorb + one chaining value).
        // The final chunk costs last_blocks (absorb + its chaining value).
        // There are chunks-1 parent nodes; chunks-2 of them yield a chaining
        // value, and the last is the root output node.
        BPC * (chunks - 1) + last_blocks + (chunks - 2) + out_blocks
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn compression_counts_are_self_consistent() {
        // 32 bytes in, 43110 out: one block, so the single absorbed block IS the
        // root node and every 64 output bytes is one compression.
        assert_eq!(compressions(32, 43110), 43110u64.div_ceil(64));
        assert_eq!(compressions(32, 43110), 674);
        // 44 bytes in, 32 out.
        assert_eq!(compressions(44, 32), 1);
        // 64 bytes in, 32 out: still one block.
        assert_eq!(compressions(64, 32), 1);
        // 65 bytes in: two blocks, first absorbed, second is root.
        assert_eq!(compressions(65, 32), 2);
        // One full chunk.
        assert_eq!(compressions(1024, 32), 16);
        // Two chunks, second holding one byte.
        assert_eq!(compressions(1025, 32), 18);
        // A full 1920x1080x3 tile.
        assert_eq!(compressions(1920 * 1080 * 3, 32), 103_274);
    }
}
