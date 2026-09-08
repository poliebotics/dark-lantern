//! The preprocessing specification the statement commits to: a canonical JSON string compiled into the guest and
//! hashed in circuit (the proved relation's `PREPROCESS_SPEC_SHA256` pattern, join/src/lib.rs 66-71 and 297-302).
//! Change one character here and the published digest changes; the pinned constant below is asserted by a test.

use sha2::{Digest, Sha256};

pub const PREPROCESS_SPEC_CANONICAL_JSON: &str = concat!(
    "{\"id\":\"ZBDIFF_PREPROCESS_V1\",",
    "\"frame\":{\"raw\":\"uint8 4600x5320 row-major RGGB\",\"planes\":\"[y0::2,x0::2],[y0::2,x1::2],[y1::2,x0::2],[y1::2,x1::2]\",",
    "\"value\":\"float32(v)/255.0f32\",\"area\":\"adaptive_avg_pool2d bins [floor(i*in/out),ceil((i+1)*in/out)), ",
    "sequential float32 accumulation row-major within the bin, then /kh then /kw in float32\",",
    "\"out\":\"4x96x112\",\"cache\":\"float16 RNE -> float32 -> bfloat16 RNE\",\"quant\":\"clamp16(rint_half_even(x*2^12))\"},",
    "\"hint\":{\"seeds\":\"BLAKE3(TB:SEED:{R,G,B}:v8 || S_t)\",\"stream\":\"BLAKE3(seed).xof(43110)\",",
    "\"grids\":\"17x30,34x60,68x120,135x240 uint8\",\"value\":\"float32(v)/255.0f32\",\"area\":\"same kernel, each grid to 96x112\",",
    "\"channels\":\"3*octave+{R,G,B}\",\"cache\":\"float16 RNE -> float32 -> bfloat16 RNE\",\"quant\":\"clamp16(rint_half_even(x*2^14))\",",
    "\"coords\":\"ch12 = rint_half_even((-16384*(W-1)+32768*j)/(W-1)), ch13 = same over i with H\",\"state\":\"S_t of the row itself (v9 blocking loop)\"},",
    "\"noising\":{\"t\":150,\"SA\":63540,\"SO\":16053,\"shift\":16,\"rule\":\"clamp16((SA*C+SO*noise+2^15)>>16)\",\"noise\":\"int16 Q12 witness, BLAKE3 published\"},",
    "\"residual\":{\"rule\":\"sum((eps-noise)^2) exact\",\"denominator\":721554505728,\"D\":\"R_wrong-R_correct\"},",
    "\"offsets\":[-2,2,-15,15,30],\"emission\":\"tile_cpu.gen_channel_v2 semantics, BLAKE3 of interleaved RGB 1080x1920\"}"
);

/// SHA-256 of `PREPROCESS_SPEC_CANONICAL_JSON`, pinned; `spec_digest_is_pinned` fails if the text drifts.
pub const PREPROCESS_SPEC_SHA256_HEX: &str = "025de070985434fefaea547745e18983ffd21c50ec66e3126bcfffc8af58f4a5";

pub fn preprocess_spec_sha256() -> [u8; 32] {
    Sha256::digest(PREPROCESS_SPEC_CANONICAL_JSON.as_bytes()).into()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn spec_digest_is_pinned() {
        let actual = crate::header::hex(&preprocess_spec_sha256());
        assert_eq!(actual, PREPROCESS_SPEC_SHA256_HEX, "PREPROCESS_SPEC_CANONICAL_JSON changed; its digest is now {actual}");
        // the text must be one line of valid-looking JSON with the constants the code uses
        assert!(PREPROCESS_SPEC_CANONICAL_JSON.contains("\"SA\":63540"));
        assert!(PREPROCESS_SPEC_CANONICAL_JSON.contains("\"offsets\":[-2,2,-15,15,30]"));
        assert!(!PREPROCESS_SPEC_CANONICAL_JSON.contains('\n'));
    }
}
