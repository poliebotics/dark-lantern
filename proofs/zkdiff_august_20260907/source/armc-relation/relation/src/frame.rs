//! Whole-frame reduction: raw 4600x5320 uint8 Bayer bytes -> 4 x 96 x 112 int16 (Q12), exactly as the pipeline.
//!
//! Pipeline (train_lean.py `load_C`, lines 120-133, and precache.py 41):
//! ```text
//! x   = raw.reshape(4600, 5320)                                   # line 128
//! cfa = stack([x[0::2,0::2], x[0::2,1::2], x[1::2,0::2], x[1::2,1::2]])   # line 129: planes R, G1, G2, B
//! t   = float32(cfa) / 255.0                                       # line 132: float32 division
//! C   = F.interpolate(t[None], size=(96,112), mode="area")[0]      # line 133: adaptive_avg_pool2d, CPU
//! cache = float16(C); C_f32 = float32(cache); C_bf16 = bfloat16(C_f32); C_int = rint(C_bf16 * 2^12)
//! ```
//! `mode="area"` is `adaptive_avg_pool2d`: output bin i covers input rows `[floor(i*in/out), ceil((i+1)*in/out))`
//! (bins overlap by one row/column where the ratio is fractional: 2300/96 and 2660/112 give 24- or 25-wide bins),
//! and the CPU kernel accumulates the bin **sequentially in float32, row-major**, then divides by `kh` and then by
//! `kw`, both in float32. That semantics was pinned empirically on the development machine with torch 2.11.0: a random full-size frame
//! reproduces torch's output bit for bit (0 of 43,008 float32 mismatches), while the exact rational mean cast to
//! float32 differs in 39,094 positions (vectors_relation/gen_vectors.py, `torch_area_probe`). This module offers
//! both definitions:
//!
//! * `reduce_torch_f32` + `cache_quant`: the pipeline-faithful path (matches the G1 vectors' `C_int` exactly);
//! * `reduce_exact` + `quant_exact`: the clean rational statement `round_half_even(sum * 2^12 / (255 * count))`.
//!
//! Which one the statement uses is a design decision recorded in RELATION.md; the guest calls the torch path so
//! the proved integer inputs are the ones the network was validated on (G1 vectors), and publishes which.

use crate::fp::{cache_quant, clamp16, round_div_half_even};
use crate::{FRAME_CHANNELS, OUT_H, OUT_W, PLANE_H, PLANE_W, RAW_BYTES, RAW_W};

/// torch `adaptive_avg_pool2d` bins: `(start, end)` per output index, `start = floor(i*in/out)`,
/// `end = ceil((i+1)*in/out)`.
pub fn area_bins(n_in: usize, n_out: usize) -> Vec<(usize, usize)> {
    (0..n_out)
        .map(|i| ((i * n_in) / n_out, ((i + 1) * n_in).div_ceil(n_out)))
        .collect()
}

/// `float32(v) / 255.0f32` for every byte value, computed once (256 IEEE divisions instead of 6.1 million).
/// Each entry equals numpy's float32 `v / 255.0` element (correctly rounded division).
pub fn inv255_table() -> [f32; 256] {
    let mut t = [0_f32; 256];
    for (v, slot) in t.iter_mut().enumerate() {
        *slot = (v as f32) / 255.0_f32;
    }
    t
}

/// Index into the raw Bayer buffer of plane `p` element `(y, x)`: plane 0 = rows 0::2 cols 0::2 (R),
/// 1 = rows 0::2 cols 1::2 (G1), 2 = rows 1::2 cols 0::2 (G2), 3 = rows 1::2 cols 1::2 (B). Same order as
/// train_lean.py:129 and as the proved `pack_bayer_rggb` (preprocess_v1_candidate/src/lib.rs:65-95).
#[inline(always)]
pub fn raw_index(p: usize, y: usize, x: usize) -> usize {
    (2 * y + (p >> 1)) * RAW_W + 2 * x + (p & 1)
}

/// Pipeline-faithful reduction: the float32 area means, 4 x 96 x 112, channel-major, bit-exact to torch's CPU kernel.
pub fn reduce_torch_f32(raw: &[u8]) -> Vec<f32> {
    assert_eq!(raw.len(), RAW_BYTES, "raw frame must be exactly 24,472,000 bytes");
    let inv = inv255_table();
    let ybins = area_bins(PLANE_H, OUT_H);
    let xbins = area_bins(PLANE_W, OUT_W);
    let mut out = vec![0_f32; FRAME_CHANNELS * OUT_H * OUT_W];
    for p in 0..FRAME_CHANNELS {
        for (i, &(y0, y1)) in ybins.iter().enumerate() {
            for (j, &(x0, x1)) in xbins.iter().enumerate() {
                let mut acc = 0.0_f32;
                for y in y0..y1 {
                    let row = (2 * y + (p >> 1)) * RAW_W + (p & 1);
                    for x in x0..x1 {
                        acc += inv[raw[row + 2 * x] as usize];
                    }
                }
                let kh = (y1 - y0) as f32;
                let kw = (x1 - x0) as f32;
                out[(p * OUT_H + i) * OUT_W + j] = acc / kh / kw;
            }
        }
    }
    out
}

/// Exact integer bin sums (4 x 96 x 112, u32) and bin element counts (96 x 112, u32) on the torch bins.
pub fn reduce_exact(raw: &[u8]) -> (Vec<u32>, Vec<u32>) {
    assert_eq!(raw.len(), RAW_BYTES, "raw frame must be exactly 24,472,000 bytes");
    let ybins = area_bins(PLANE_H, OUT_H);
    let xbins = area_bins(PLANE_W, OUT_W);
    let mut sums = vec![0_u32; FRAME_CHANNELS * OUT_H * OUT_W];
    let mut counts = vec![0_u32; OUT_H * OUT_W];
    for (i, &(y0, y1)) in ybins.iter().enumerate() {
        for (j, &(x0, x1)) in xbins.iter().enumerate() {
            counts[i * OUT_W + j] = ((y1 - y0) * (x1 - x0)) as u32;
        }
    }
    for p in 0..FRAME_CHANNELS {
        for (i, &(y0, y1)) in ybins.iter().enumerate() {
            for (j, &(x0, x1)) in xbins.iter().enumerate() {
                let mut acc = 0_u32;
                for y in y0..y1 {
                    let row = (2 * y + (p >> 1)) * RAW_W + (p & 1);
                    for x in x0..x1 {
                        acc += raw[row + 2 * x] as u32;
                    }
                }
                sums[(p * OUT_H + i) * OUT_W + j] = acc;
            }
        }
    }
    (sums, counts)
}

/// The pipeline's `C_int`: `cache_quant` of every float32 area mean at Q12.
pub fn quant_torchpath(means: &[f32], f: u32) -> Vec<i16> {
    means.iter().map(|&m| cache_quant(m, f)).collect()
}

/// The rational statement input: `round_half_even(sum * 2^f / (255 * count))` per element.
pub fn quant_exact(sums: &[u32], counts: &[u32], f: u32) -> Vec<i16> {
    let per_channel = counts.len();
    sums.iter()
        .enumerate()
        .map(|(k, &s)| {
            let c = counts[k % per_channel] as i128;
            clamp16(round_div_half_even((s as i128) << f, 255 * c) as i64)
        })
        .collect()
}

/// `C_int` (Q12) from the raw frame by the pipeline-faithful path.
pub fn frame_c_int(raw: &[u8]) -> Vec<i16> {
    quant_torchpath(&reduce_torch_f32(raw), crate::noise::F_CT)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bins_are_torch_adaptive_bins() {
        let y = area_bins(2300, 96);
        assert_eq!(y[0], (0, 24));
        assert_eq!(y[1], (23, 48)); // floor(2300/96)=23, ceil(4600/96)=48: overlaps row 23 with bin 0
        assert_eq!(y[95], (2276, 2300));
        let x = area_bins(2660, 112);
        assert_eq!(x[0], (0, 24));
        assert_eq!(x[111], (2636, 2660));
        // upsampling bins have one or two elements
        let o = area_bins(17, 96);
        assert!(o.iter().all(|&(a, b)| b - a == 1 || b - a == 2));
        assert_eq!(o[0], (0, 1));
        assert_eq!(o[95], (16, 17));
        let xb = area_bins(2660, 112);
        let mut sizes = std::collections::BTreeSet::new();
        for &(a, b) in &area_bins(2300, 96) {
            for &(c, d) in &xb {
                sizes.insert((b - a) * (d - c));
            }
        }
        assert_eq!(sizes.into_iter().collect::<Vec<_>>(), vec![576, 600, 625]);
    }

    #[test]
    fn raw_index_is_the_rggb_split() {
        assert_eq!(raw_index(0, 0, 0), 0);
        assert_eq!(raw_index(1, 0, 0), 1);
        assert_eq!(raw_index(2, 0, 0), RAW_W);
        assert_eq!(raw_index(3, 0, 0), RAW_W + 1);
        assert_eq!(raw_index(0, 1, 1), 2 * RAW_W + 2);
    }
}
