//! The conditioning hint: 12 XOF octave channels area-resized to 96x112 plus two coordinate channels, int16 Q14.
//!
//! Pipeline (train_lean.py `_load_E_uncached`, lines 142-153; src/data/xof_generation.py):
//! ```text
//! seed_c  = BLAKE3(b"TB:SEED:{R,G,B}:v8" || S_t)                      # derive_xof_seeds; S_t is the row's OWN state
//! stream  = BLAKE3(seed_c).xof(43110)                                   # expand_seed_to_octaves
//! grids   = stream sliced as 17x30, 34x60, 68x120, 135x240 uint8      # OCTAVE_SHAPES
//! oct_o   = float32(stack(R,G,B grids of octave o)) / 255.0            # xof_octaves_from_s_next, torch .float()/255.0
//! ups_o   = F.interpolate(oct_o[None], size=(96,112), mode="area")[0]  # line 152: same kernel as the frame
//! E       = cat(ups_0..ups_3)                                          # line 153: channel 3*o + c
//! cache/bf16/quant as for C, at 2^14 (g1_integer/int_ref.py:274)
//! hint    = cat(E (12), coord_grid (2))                                # train_lean.py:161-165, coord ch0 = x, ch1 = y
//! ```
//! The offset-0 convention (E_t from S_t, the v9 blocking loop) is the one established bit-exactly in
//! train_lean.py:38-52 and used by the trained model; the proved renderer uses the same S_t (join lib.rs:335).

use crate::b3xof::{self, octave_offset, GRID_H, GRID_W, NUM_OCTAVES, TOTAL_BYTES_PER_CHANNEL};
use crate::fp::{cache_quant, clamp16, round_div_half_even};
use crate::frame::{area_bins, inv255_table};
use crate::{HINT_CHANNELS, HINT_E_CHANNELS, OUT_H, OUT_W};

pub const F_HINT: u32 = 14;

/// The `h_o x w_o` uint8 grid of channel `c` (0 = R, 1 = G, 2 = B) and octave `o` inside the 129,330-byte
/// conditioning buffer returned by `b3xof::expand_all`.
pub fn octave_grid(cond: &[u8], c: usize, o: usize) -> &[u8] {
    let start = c * TOTAL_BYTES_PER_CHANNEL + octave_offset(o);
    &cond[start..start + GRID_H[o] * GRID_W[o]]
}

/// Pipeline-faithful area resize of one uint8 grid to 96x112 float32 means (sequential float32 accumulation,
/// row-major within the bin, then `/ kh / kw`), identical kernel semantics to `frame::reduce_torch_f32`.
pub fn resize_torch_f32(grid: &[u8], h: usize, w: usize) -> Vec<f32> {
    assert_eq!(grid.len(), h * w);
    let inv = inv255_table();
    let ybins = area_bins(h, OUT_H);
    let xbins = area_bins(w, OUT_W);
    let mut out = vec![0_f32; OUT_H * OUT_W];
    for (i, &(y0, y1)) in ybins.iter().enumerate() {
        for (j, &(x0, x1)) in xbins.iter().enumerate() {
            let mut acc = 0.0_f32;
            for y in y0..y1 {
                for x in x0..x1 {
                    acc += inv[grid[y * w + x] as usize];
                }
            }
            out[i * OUT_W + j] = acc / (y1 - y0) as f32 / (x1 - x0) as f32;
        }
    }
    out
}

/// Exact integer bin sums and counts of one grid on the torch bins.
pub fn resize_exact(grid: &[u8], h: usize, w: usize) -> (Vec<u32>, Vec<u32>) {
    let ybins = area_bins(h, OUT_H);
    let xbins = area_bins(w, OUT_W);
    let mut sums = vec![0_u32; OUT_H * OUT_W];
    let mut counts = vec![0_u32; OUT_H * OUT_W];
    for (i, &(y0, y1)) in ybins.iter().enumerate() {
        for (j, &(x0, x1)) in xbins.iter().enumerate() {
            let mut acc = 0_u32;
            for y in y0..y1 {
                for x in x0..x1 {
                    acc += grid[y * w + x] as u32;
                }
            }
            sums[i * OUT_W + j] = acc;
            counts[i * OUT_W + j] = ((y1 - y0) * (x1 - x0)) as u32;
        }
    }
    (sums, counts)
}

/// `E_int`: 12 x 96 x 112 int16 Q14 by the pipeline-faithful path, channel `3*o + c`.
pub fn e_int_torchpath(cond: &[u8]) -> Vec<i16> {
    assert_eq!(cond.len(), b3xof::CONDITIONING_BYTES);
    let mut out = Vec::with_capacity(HINT_E_CHANNELS * OUT_H * OUT_W);
    for o in 0..NUM_OCTAVES {
        for c in 0..b3xof::CHANNELS {
            let means = resize_torch_f32(octave_grid(cond, c, o), GRID_H[o], GRID_W[o]);
            out.extend(means.iter().map(|&m| cache_quant(m, F_HINT)));
        }
    }
    out
}

/// `E_int` by the rational rule `round_half_even(sum * 2^14 / (255 * count))`.
pub fn e_int_exact(cond: &[u8]) -> Vec<i16> {
    assert_eq!(cond.len(), b3xof::CONDITIONING_BYTES);
    let mut out = Vec::with_capacity(HINT_E_CHANNELS * OUT_H * OUT_W);
    for o in 0..NUM_OCTAVES {
        for c in 0..b3xof::CHANNELS {
            let (sums, counts) = resize_exact(octave_grid(cond, c, o), GRID_H[o], GRID_W[o]);
            out.extend(sums.iter().zip(counts.iter()).map(|(&s, &n)| {
                clamp16(round_div_half_even((s as i128) << F_HINT, 255 * n as i128) as i64)
            }));
        }
    }
    out
}

/// The two coordinate channels, Q14: channel 0 = x = linspace(-1, 1, 112) along the width, channel 1 = y =
/// linspace(-1, 1, 96) along the height (diffusion_diagnostic_model.py `coord_grid`, cited in
/// g1_integer/README.md s.2), rounded half-even from the exact rational `-1 + 2k/(n-1)`. Equal to G1's
/// `rint(float64 linspace * 2^14)` (no exact ties exist for n = 96 or 112; checked in gen_vectors.py).
pub fn coord_int() -> Vec<i16> {
    let mut out = vec![0_i16; 2 * OUT_H * OUT_W];
    let q = |k: usize, n: usize| -> i16 {
        let num = -(1_i128 << F_HINT) * (n as i128 - 1) + (1_i128 << (F_HINT + 1)) * k as i128;
        clamp16(round_div_half_even(num, n as i128 - 1) as i64)
    };
    for i in 0..OUT_H {
        for j in 0..OUT_W {
            out[i * OUT_W + j] = q(j, OUT_W);
            out[OUT_H * OUT_W + i * OUT_W + j] = q(i, OUT_H);
        }
    }
    out
}

/// `hint = cat(E_int, coord_int)`: the 14 x 96 x 112 int16 Q14 tensor the network consumes.
pub fn hint14(e_int: &[i16]) -> Vec<i16> {
    assert_eq!(e_int.len(), HINT_E_CHANNELS * OUT_H * OUT_W);
    let mut out = Vec::with_capacity(HINT_CHANNELS * OUT_H * OUT_W);
    out.extend_from_slice(e_int);
    out.extend_from_slice(&coord_int());
    out
}

/// Everything the network needs from a chain state: the conditioning stream (kept for the render) and the hint.
pub fn hint_from_state(s_t: &[u8; 32]) -> (Vec<u8>, Vec<i16>) {
    let cond = b3xof::expand_all(s_t);
    let hint = hint14(&e_int_torchpath(&cond));
    (cond, hint)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn coordinates_are_symmetric_and_span_q14() {
        let c = coord_int();
        assert_eq!(c[0], -16384); // x = -1 at j = 0
        assert_eq!(c[OUT_W - 1], 16384); // x = +1 at j = 111 (exact)
        assert_eq!(c[OUT_H * OUT_W], -16384); // y = -1 at i = 0
        assert_eq!(c[2 * OUT_H * OUT_W - 1], 16384); // y = +1 at i = 95
        assert_eq!(c[OUT_W], -16384); // x channel is constant down a column
        assert_eq!(c[OUT_H * OUT_W + 1], -16384); // y channel is constant along a row
        // odd-symmetric: value at k equals minus the value at n-1-k
        for j in 0..OUT_W {
            assert_eq!(c[j] as i32, -(c[OUT_W - 1 - j] as i32), "x {j}");
        }
    }
}
