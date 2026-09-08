//! Parity of the Rust integer network against the G1 FINAL oracle artifact
//! (`g1_integer/final/vectors`, checkpoint `c6955192…5fab8`, exported to `g2_guest/oracle_final/` by
//! `tools/export_oracle.py`), byte for byte, plus the artifact-specific pins Astra r4 asked for: the
//! FINAL residual sums, hashes, effective scale map, inherited-scale names, accumulator and
//! requantisation maxima, GroupNorm bounds, lookup-table set and clipping masks.
//!
//! Two modes per vector set:
//! * chained: the Rust forward runs on its own outputs; every one of the 188 layer outputs and the
//!   residual sum must equal the oracle's (the first mismatching layer and index are reported);
//! * isolated: after comparing, each layer output is replaced by the oracle's tensor, so every
//!   kernel is exercised on the oracle's exact inputs and a mismatch localises to one kernel.
//!
//! `ARMC_ORACLE_DIR` selects another export root (the superseded step-12000 artifact under
//! `g2_guest/oracle/` still passes the manifest-driven tests; the FINAL pins then fail by design).

use armc_int::blob::Constants;
use armc_int::kernels as k;
use armc_int::loader::{i16_le_bytes, i64_le_bytes, load_constants, load_oracle, sha256_hex, OracleSet};
use armc_int::model::{evaluate, Hook, Net};
use armc_int::Tensor;
use std::collections::BTreeMap;
use std::path::PathBuf;

/// Oracle export root: `ARMC_ORACLE_DIR` if set, else `g2_guest/oracle_final/` (the FINAL artifact).
fn oracle_dir(set: &str) -> PathBuf {
    match std::env::var_os("ARMC_ORACLE_DIR") {
        Some(root) => PathBuf::from(root).join(set),
        None => PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..").join("oracle_final").join(set),
    }
}

pub const FINAL_CHECKPOINT_SHA256: &str = "c6955192067c8df1f46960f4803b32eac1c037b84a0f40de3b265b739d85fab8";

/// README_FINAL.md section 6: residual sums of the FINAL artifact.
const FINAL_RESIDUALS: [(&str, i64); 8] = [
    ("int16_d2_1328_correct", 8_764_459_045),
    ("int16_d2_1328_wrong_p2", 22_311_372_969),
    ("int16_august_650_correct", 5_317_378_656),
    ("int16_august_650_wrong_p2", 12_127_686_594),
    ("int8_d2_1328_correct", 9_006_417_833),
    ("int8_d2_1328_wrong_p2", 22_578_064_838),
    ("int8_august_650_correct", 5_661_729_244),
    ("int8_august_650_wrong_p2", 12_505_149_149),
];

struct Mismatch {
    name: String,
    detail: String,
}

/// Compares every layer with the oracle; optionally substitutes the oracle tensor.
struct Compare<'a> {
    oracle: &'a OracleSet,
    substitute: bool,
    seen: usize,
    mismatches: Vec<Mismatch>,
}

impl<'a> Hook for Compare<'a> {
    fn layer(&mut self, name: &str, t: Tensor) -> Tensor {
        self.seen += 1;
        let r = match self.oracle.layers.get(name) {
            Some(r) => r,
            None => {
                self.mismatches.push(Mismatch { name: name.to_string(), detail: "layer not in the oracle export".into() });
                return t;
            }
        };
        if r.shape() != t.shape() || r.f != t.f {
            self.mismatches.push(Mismatch {
                name: name.to_string(),
                detail: format!("shape/f: oracle {:?} f={} rust {:?} f={}", r.shape(), r.f, t.shape(), t.f),
            });
        } else if let Some(i) = r.v.iter().zip(&t.v).position(|(a, b)| a != b) {
            let n_bad = r.v.iter().zip(&t.v).filter(|(a, b)| a != b).count();
            let (c, rem) = (i / (t.h * t.w), i % (t.h * t.w));
            let (y, x) = (rem / t.w, rem % t.w);
            self.mismatches.push(Mismatch {
                name: name.to_string(),
                detail: format!("first mismatch at flat index {i} (c={c}, y={y}, x={x}): oracle {} rust {}; {n_bad} of {} values differ", r.v[i], t.v[i], t.v.len()),
            });
        }
        if self.substitute {
            r.clone()
        } else {
            t
        }
    }
}

fn constants_set(scheme: &str) -> String {
    format!("{scheme}_d2_1328_correct")
}

fn run_set(set: &str, substitute: bool) -> (i64, u32) {
    let scheme = set.split('_').next().unwrap();
    let k = load_constants(&oracle_dir(&constants_set(scheme)));
    let o = load_oracle(&oracle_dir(set));
    let mut hook = Compare { oracle: &o, substitute, seen: 0, mismatches: Vec::new() };
    let (r, sat) = evaluate(&k, &o.c_int, &o.noise_int, &o.e_int, &mut hook);
    let mode = if substitute { "isolated" } else { "chained" };
    println!("[{set} {mode}] layers seen {} (oracle has {}), residual {} (oracle {}), clip events {sat}", hook.seen, o.layers.len(), r, o.residual_sum_int);
    for m in &hook.mismatches {
        println!("  MISMATCH {}: {}", m.name, m.detail);
    }
    assert_eq!(hook.seen, o.layers.len(), "every oracle layer must be produced exactly once");
    assert!(hook.mismatches.is_empty(), "{} layer(s) differ from the oracle in {set} ({mode}); first: {} ({})", hook.mismatches.len(), hook.mismatches[0].name, hook.mismatches[0].detail);
    assert_eq!(r, o.residual_sum_int, "residual sum ({set}, {mode})");
    // the oracle's clip_events dict is empty for every FINAL set: no clamp, no input clip, no clipped-table hit
    let oracle_clips: u64 = o.index.manifest.clip_events.values().sum();
    assert_eq!(sat as u64, oracle_clips, "clip events ({set}, {mode}) must equal the oracle's count");
    (r, sat)
}

const ALL_SETS: [&str; 8] = [
    "int16_d2_1328_correct",
    "int16_d2_1328_wrong_p2",
    "int16_august_650_correct",
    "int16_august_650_wrong_p2",
    "int8_d2_1328_correct",
    "int8_d2_1328_wrong_p2",
    "int8_august_650_correct",
    "int8_august_650_wrong_p2",
];

#[test]
fn parity_chained_all_sets() {
    for set in ALL_SETS {
        if oracle_dir(set).join("index.json").is_file() {
            run_set(set, false);
        } else {
            println!("[{set}] not exported in this root, skipped");
        }
    }
    // the d2 1328 pair must exist in any root
    assert!(oracle_dir("int16_d2_1328_correct").join("index.json").is_file());
}

#[test]
fn kernels_isolated_all_sets() {
    for set in ALL_SETS {
        if oracle_dir(set).join("index.json").is_file() {
            run_set(set, true);
        }
    }
}

#[test]
fn final_artifact_pins() {
    // this test is specific to the FINAL artifact and fails, by design, on any other export root
    let o = load_oracle(&oracle_dir("int16_d2_1328_correct"));
    assert_eq!(o.index.manifest.checkpoint_sha256, FINAL_CHECKPOINT_SHA256, "not the FINAL checkpoint");
    for (set, expect) in FINAL_RESIDUALS {
        let o = load_oracle(&oracle_dir(set));
        assert_eq!(o.index.manifest.checkpoint_sha256, FINAL_CHECKPOINT_SHA256, "{set}: checkpoint");
        assert_eq!(o.residual_sum_int, expect, "{set}: manifest residual differs from README_FINAL section 6");
        let (r, sat) = run_set(set, false);
        assert_eq!(r, expect, "{set}: Rust residual");
        assert_eq!(sat, 0, "{set}: clip events");
    }
    // effective scale map: the 15 inherited names and the histogram of README_FINAL section 3
    let m = &o.index.manifest;
    let inherited: Vec<&String> = m.scale_source.iter().filter(|(_, s)| s.as_str() == "inherited").map(|(n, _)| n).collect();
    let expect_inherited = ["down_attns.3.attn", "hint_up.0", "hint_up.1", "hint_up.2", "hint_up.3", "mid_attn.attn", "pool.0", "pool.1", "pool.2", "pool.3", "up.0", "up.1", "up.2", "up.3", "up_attns.0.attn"];
    assert_eq!(inherited.iter().map(|s| s.as_str()).collect::<Vec<_>>(), expect_inherited.to_vec(), "inherited-scale tensors");
    assert_eq!(m.ftab.len(), 188, "188 tensors in the effective scale map");
    let mut hist: BTreeMap<u32, u32> = BTreeMap::new();
    for f in m.ftab.values() {
        *hist.entry(*f).or_default() += 1;
    }
    let expect_hist: BTreeMap<u32, u32> = [(7, 1), (8, 1), (9, 22), (10, 26), (11, 89), (12, 38), (13, 6), (14, 5)].into_iter().collect();
    assert_eq!(hist, expect_hist, "effective scale histogram (int16)");
    assert_eq!(m.ftab["ups.3.1.conv1"], 7, "the f = 7 tensor");
    assert_eq!(m.ftab["hint"], 14);
    assert_eq!(m.ftab["out_conv"], 12);
    // every executed layer scale equals the published map (the Compare hook checked f per layer above)
    for (name, l) in &m.layers {
        assert_eq!(l.f, m.ftab[name], "{name}: layer f vs scale map");
    }
    // static bounds recomputed from the authenticated constants
    for (scheme, acc_max, requant_max) in [("int16", 353_174_814_720_i64, 3_812_976_885_203_206_144_i128), ("int8", 1_368_850_432, 22_661_745_809_484_953)] {
        let dir = oracle_dir(&constants_set(scheme));
        let kk = load_constants(&dir);
        let o = load_oracle(&dir);
        let worst = kk.convs.iter().map(|l| l.acc_bound).max().unwrap();
        assert_eq!(worst, acc_max, "{scheme}: max conv accumulator bound (README_FINAL section 4)");
        let requant = kk
            .convs
            .iter()
            .map(|l| (l.acc_bound as i128) * (*l.m.iter().max().unwrap() as i128) + l.bp.iter().map(|b| (*b as i128).abs()).max().unwrap() + (1i128 << (l.shift - 1)))
            .max()
            .unwrap();
        assert_eq!(requant, requant_max, "{scheme}: max requantisation expression");
        assert!(requant < (1i128 << 63));
        let g = &o.index.manifest.static_bounds["global"];
        assert_eq!(g["conv_acc_bound_max"].as_i64().unwrap(), acc_max);
        assert_eq!(g["conv_requant_expr_max"].as_i64().unwrap() as i128, requant_max);
        assert_eq!(g["gn_n_max"].as_u64().unwrap(), 32256);
        assert_eq!(g["gn_N_bits_max"].as_u64().unwrap(), 60);
        assert_eq!(g["gn_X2_bits_max"].as_u64().unwrap(), 99);
        assert_eq!(g["gn_affine_bits_max"].as_u64().unwrap(), 50);
        assert_eq!(g["sse_bound"].as_i64().unwrap(), k::SSE_BOUND_96X112);
        assert_eq!(g["noising_acc_bound"].as_i64().unwrap(), (kk.sa + kk.so) * 32768);
        // the shift range of README_FINAL section 3
        let (s_min, s_max) = kk.convs.iter().fold((u32::MAX, 0), |(a, b), l| (a.min(l.shift), b.max(l.shift)));
        if scheme == "int16" {
            assert!((s_min, s_max) == (38, 43), "int16 S in [38, 43], got {s_min}..{s_max}");
        } else {
            assert!((s_min, s_max) == (30, 35), "int8 S in [30, 35], got {s_min}..{s_max}");
        }
    }
    // the lookup-table set of the FINAL checkpoint and its clipped-entry counts
    let kk = load_constants(&oracle_dir("int16_d2_1328_correct"));
    let mut luts: Vec<(u8, u32, u32, u32)> = kk.luts.iter().map(|l| (l.kind, l.f_in, l.f_out, k::lut_mask_popcount(&l.mask))).collect();
    luts.sort();
    let expect = vec![(0u8, 9u32, 9u32, 0u32), (0, 9, 10, 16384), (0, 10, 10, 0), (0, 10, 11, 16384), (0, 11, 11, 0), (0, 11, 12, 16378), (0, 12, 12, 0), (1, 11, 11, 0)];
    assert_eq!(luts, expect, "(kind, f_in, f_out, clipped entries)");
    for l in &kk.luts {
        let kind = if l.kind == 0 { "silu" } else { "gelu" };
        let le = &m.luts[&format!("{kind}:{}->{}", l.f_in, l.f_out)];
        assert_eq!(le.clipped_entries, Some(k::lut_mask_popcount(&l.mask) as usize), "{kind} {}->{} clipped entries", l.f_in, l.f_out);
    }
}

#[test]
fn table_and_constant_hashes_match_the_manifest() {
    for scheme in ["int16", "int8"] {
        let dir = oracle_dir(&constants_set(scheme));
        let k = load_constants(&dir);
        let o = load_oracle(&dir);
        let m = &o.index.manifest;
        for l in &k.luts {
            let kind = if l.kind == 0 { "silu" } else { "gelu" };
            let key = format!("{kind}:{}->{}", l.f_in, l.f_out);
            assert_eq!(sha256_hex(&i16_le_bytes(&l.table)), m.luts[&key].sha256_int16_le, "{scheme} lut {key}");
            let mask_entry = &o.index.arrays[&format!("MASK:{kind}:{}:{}", l.f_in, l.f_out)];
            assert_eq!(sha256_hex(&l.mask), mask_entry.sha256, "{scheme} mask {key}");
            // a masked entry sits at a domain endpoint (the parser also enforces this)
            for i in 0..65536 {
                if k::lut_mask_bit(&l.mask, i) {
                    assert!(l.table[i] == i16::MIN || l.table[i] == i16::MAX, "{key}: masked entry {i} = {}", l.table[i]);
                }
            }
        }
        assert_eq!(k.luts.len(), m.luts.len());
        let exp64: Vec<i64> = k.exp_table.iter().map(|&v| v as i64).collect();
        assert_eq!(sha256_hex(&i64_le_bytes(&exp64)), m.exp_table.sha256_int64_le, "{scheme} exp table");
        assert_eq!(k.exp_table[0], 1u32 << k.p_exp, "EXP[0] = 2^P_EXP");
        for c in &k.convs {
            let ce = &m.constants[&c.name];
            // weights are hashed in their int16-widened form by the manifest for both schemes
            let w_entry = &o.index.arrays[&format!("W:{}", c.name)];
            let expected_w = w_entry.sha256_int16_le.clone().unwrap_or_else(|| w_entry.sha256.clone());
            assert_eq!(sha256_hex(&i16_le_bytes(&c.w)), expected_w, "{scheme} W {}", c.name);
            assert_eq!(sha256_hex(&i64_le_bytes(&c.m)), o.index.arrays[&format!("M:{}", c.name)].sha256);
            assert_eq!(sha256_hex(&i64_le_bytes(&c.bp)), o.index.arrays[&format!("BP:{}", c.name)].sha256);
            assert_eq!(ce.shift, Some(c.shift));
        }
        assert_eq!(sha256_hex(&i16_le_bytes(&k.coord)), m.inputs["coord_int"].sha256_int16_le.clone().unwrap(), "{scheme} coord");
        assert_eq!(k.sa, 63540);
        assert_eq!(k.so, 16053);
        // the documented silu 11->11 and EXP hashes (README section 3, unchanged between artifacts)
        let l = k.luts.iter().find(|l| l.kind == 0 && l.f_in == 11 && l.f_out == 11).expect("silu 11->11");
        assert_eq!(sha256_hex(&i16_le_bytes(&l.table)), "dddc859491a7ad82bad38e0403ffa14a08c1baeface3ad4532f99e3eed920601");
        assert_eq!(sha256_hex(&i64_le_bytes(&exp64)), "e1978b8be2bd826ec3b939556d34dc9d6e1b9be6f1668e5f3b70ddbc52a5a706");
    }
}

#[test]
fn blob_round_trip_and_constants_identical_across_conditions() {
    for scheme in ["int16", "int8"] {
        let a = load_constants(&oracle_dir(&format!("{scheme}_d2_1328_correct")));
        let b = load_constants(&oracle_dir(&format!("{scheme}_d2_1328_wrong_p2")));
        assert!(a == b, "{scheme}: constants differ between correct and wrong_p2 exports");
        if oracle_dir(&format!("{scheme}_august_650_correct")).join("index.json").is_file() {
            let c = load_constants(&oracle_dir(&format!("{scheme}_august_650_correct")));
            assert!(a == c, "{scheme}: constants differ between d2 and august exports");
        }
        let bytes = a.to_bytes();
        let back = Constants::parse(&bytes).expect("parse");
        assert!(back == a, "{scheme}: blob round trip");
        println!("{scheme}: blob {} bytes, sha256 {}", bytes.len(), sha256_hex(&bytes));
        assert!(Constants::parse(&bytes[..bytes.len() - 1]).is_err());
        assert!(Constants::parse(&bytes[..100]).is_err());
        // a version-1 blob (no masks) is rejected
        let mut v1 = bytes.clone();
        v1[8..12].copy_from_slice(&1u32.to_le_bytes());
        assert!(Constants::parse(&v1).is_err());
        // a fractional-bit field outside 0..=15 is rejected (representability of the left shifts)
        let mut bad = a.clone();
        bad.f_ct = 16;
        assert!(Constants::parse(&bad.to_bytes()).is_err(), "F_CT = 16 must be refused");
        let mut bad = a.clone();
        bad.convs[0].f_out = 62;
        assert!(Constants::parse(&bad.to_bytes()).is_err(), "conv f_out = 62 must be refused");
        // a mask bit on a non-endpoint entry is rejected
        let mut bad = a.clone();
        let i = 32768usize; // x = 0 -> silu(0) = 0, never clipped
        let mut lut = bad.luts[0].clone();
        lut.mask[i >> 3] |= 1 << (i & 7);
        bad.luts[0] = lut;
        assert!(Constants::parse(&bad.to_bytes()).is_err(), "mask on a non-endpoint entry must be refused");
    }
}

#[test]
fn noising_and_hint_match_the_exported_inputs() {
    for set in ["int16_d2_1328_correct", "int16_d2_1328_wrong_p2", "int8_d2_1328_correct", "int16_august_650_correct"] {
        if !oracle_dir(set).join("index.json").is_file() {
            continue;
        }
        let dir = oracle_dir(set);
        let k = load_constants(&oracle_dir(&constants_set(set.split('_').next().unwrap())));
        let o = load_oracle(&dir);
        let mut sat = 0u32;
        let ct = k::noise_ct(&o.c_int, &o.noise_int, k.sa, k.so, k.noise_p, &mut sat);
        assert_eq!(ct, o.ct_int, "{set}: C_t");
        assert_eq!(sat, 0);
        let e = Tensor::new(12, k.h, k.w, k.f_hint, o.e_int.clone());
        let mut hook = armc_int::model::NoHook;
        let mut net = Net::new(&k, &mut hook);
        let hint = net.build_hint(&e);
        assert_eq!(hint, o.layers["hint"], "{set}: hint");
        if set == "int16_d2_1328_correct" {
            assert!(sha256_hex(&i16_le_bytes(&o.c_int)).starts_with("9baf878a"));
            assert!(sha256_hex(&i16_le_bytes(&o.noise_int)).starts_with("37198a3d"));
            assert!(sha256_hex(&i16_le_bytes(&o.ct_int)).starts_with("4050eb3f"));
            assert!(sha256_hex(&i16_le_bytes(&o.e_int)).starts_with("26f2fedf"));
        }
    }
}

// ---------------------------------------------------------------- saturation semantics (Astra r4 items 1, 2)

#[test]
fn full_int16_domain_is_admitted_and_every_clip_is_counted() {
    let mut sat = 0u32;
    assert_eq!(k::clamp16(-32768, &mut sat), -32768);
    assert_eq!(k::clamp16(32767, &mut sat), 32767);
    assert_eq!(sat, 0, "endpoints are in domain and uncounted");
    assert_eq!(k::clamp16(-32769, &mut sat), -32768);
    assert_eq!(k::clamp16(32768, &mut sat), 32767);
    assert_eq!(k::clamp16(-40000, &mut sat), -32768);
    assert_eq!(sat, 3);
    // Astra's counterexample: C = noise = -32767 noises to -39795 before clipping; Python gives -32768 and counts one
    let mut sat = 0u32;
    let ct = k::noise_ct(&[-32767], &[-32767], 63540, 16053, 16, &mut sat);
    assert_eq!(k::rshift_round(63540 * -32767 + 16053 * -32767, 16), -39795);
    assert_eq!(ct, vec![-32768]);
    assert_eq!(sat, 1);
    // both endpoints noised together stay in domain
    let mut sat = 0u32;
    let ct = k::noise_ct(&[-32768, 32767, -32768, 32767], &[-32768, 32767, 32767, -32768], 63540, 16053, 16, &mut sat);
    assert_eq!(ct, vec![-32768, 32767, -23744, 23743]); // the noising_saturation fixture: (-32768, 32767) -> -23744, (32767, -32768) -> 23743
    assert_eq!(sat, 2);
}

#[test]
fn lut_hits_on_clipped_entries_are_counted() {
    let k = load_constants(&oracle_dir("int16_d2_1328_correct"));
    let l = k.luts.iter().find(|l| l.kind == 0 && l.f_in == 11 && l.f_out == 12).expect("silu 11->12");
    assert_eq!(k::lut_mask_popcount(&l.mask), 16378);
    // input 32767 (index 65535) lands on a clipped entry: value 32767, one counted hit (Astra r4 item 2)
    let x = Tensor::new(1, 1, 1, 11, vec![32767]);
    let mut sat = 0u32;
    let y = k::lut_apply(&x, &l.table, &l.mask, 12, &mut sat);
    assert_eq!(y.v, vec![32767]);
    assert_eq!(sat, 1);
    // every index once: the hit count equals the mask popcount, and unmasked entries count nothing
    let all: Vec<i16> = (0..65536).map(|i| (i as i32 - 32768) as i16).collect();
    let x = Tensor::new(1, 256, 256, 11, all);
    let mut sat = 0u32;
    let y = k::lut_apply(&x, &l.table, &l.mask, 12, &mut sat);
    assert_eq!(sat, 16378);
    assert_eq!(y.v.as_slice(), l.table.as_slice());
    for l in &k.luts {
        let mut sat = 0u32;
        k::lut_apply(&x, &l.table, &l.mask, l.f_out, &mut sat);
        assert_eq!(sat, k::lut_mask_popcount(&l.mask), "lut {} {}->{}", l.kind, l.f_in, l.f_out);
    }
}

#[test]
fn left_shifts_are_checked_for_representability() {
    assert_eq!(k::rshift_round(5, -2), 20);
    assert_eq!(k::rshift_round(-5, -3), -40);
    assert_eq!(k::rshift_round(-32768, -15), -(1i64 << 30));
    assert_eq!(k::rshift_round(32767, -47), 32767i64 << 47);
    let r = std::panic::catch_unwind(|| k::rshift_round(32767, -62));
    assert!(r.is_err(), "rshift_round(32767, -62) must refuse instead of going negative");
    let r = std::panic::catch_unwind(|| k::rshift_round(1, -63));
    assert!(r.is_err());
    let r = std::panic::catch_unwind(|| k::rshift_round(-1, -63));
    assert!(r.is_err());
}

// ---------------------------------------------------------------- kernel self tests (no oracle)

struct Lcg(u64);
impl Lcg {
    fn next(&mut self) -> u64 {
        self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        self.0 >> 11
    }
    fn i16(&mut self, bound: i64) -> i16 {
        let r = (self.next() % (2 * bound as u64 + 1)) as i64 - bound;
        r as i16
    }
}

fn conv_via_generic(x: &Tensor, l: &k::ConvLayer) -> Vec<i64> {
    let (ho, wo) = l.out_shape(x.h, x.w);
    let per_out = l.in_ch * l.kh * l.kw;
    let mut all = Vec::with_capacity(l.out_ch * ho * wo);
    for o in 0..l.out_ch {
        let mut acc = vec![0i64; ho * wo];
        k::conv_generic_plane(&x.v, l.in_ch, x.h, x.w, l.kh, l.kw, l.stride, l.pad, &l.w[o * per_out..(o + 1) * per_out], &mut acc);
        all.extend(acc);
    }
    all
}

#[test]
fn fast_conv_paths_equal_the_generic_definition() {
    // widths chosen so the 8-column block, the 4-column block and the 1-column tail are all exercised, for
    // stride 1 (W = 8, 9, 12, 16, 17, 112) and stride 2 (W = 17, 20, 33): Astra r4 item 4 (eight-column case)
    let mut rng = Lcg(20260907);
    let cases: &[(usize, usize, usize, usize, usize, usize, usize)] = &[
        (3, 6, 7, 4, 3, 1, 1),
        (5, 2, 2, 3, 3, 1, 1),
        (7, 9, 5, 6, 3, 1, 1),
        (3, 4, 8, 2, 3, 1, 1),
        (3, 4, 9, 2, 3, 1, 1),
        (2, 5, 12, 3, 3, 1, 1),
        (4, 3, 16, 2, 3, 1, 1),
        (3, 3, 17, 2, 3, 1, 1),
        (2, 2, 112, 2, 3, 1, 1),
        (4, 6, 8, 5, 1, 1, 0),
        (6, 5, 5, 3, 1, 1, 0),
        (3, 6, 7, 4, 3, 2, 1),
        (14, 8, 6, 5, 3, 2, 1),
        (3, 5, 17, 2, 3, 2, 1),
        (3, 6, 20, 2, 3, 2, 1),
        (2, 7, 33, 2, 3, 2, 1),
    ];
    for &(c, h, w, o, kk, stride, pad) in cases {
        let x = Tensor::new(c, h, w, 11, (0..c * h * w).map(|_| rng.i16(32767)).collect());
        let wts: Vec<i16> = (0..o * c * kk * kk).map(|_| rng.i16(32767)).collect();
        let mut l = k::ConvLayer {
            name: format!("test_c{c}_h{h}_w{w}_o{o}_k{kk}_s{stride}"),
            out_ch: o,
            in_ch: c,
            kh: kk,
            kw: kk,
            stride,
            pad,
            f_in: 11,
            f_out: 11,
            shift: 40,
            w: wts,
            m: (0..o).map(|_| (rng.next() % (1 << 23)) as i64 + 1).collect(),
            bp: (0..o).map(|_| (rng.next() % (1 << 40)) as i64 - (1 << 39)).collect(),
            acc_bound: 0,
        };
        l.finalize().expect("finalize");
        let mut sat = 0u32;
        let y = k::conv2d(&x, &l, &mut sat);
        let acc = conv_via_generic(&x, &l);
        let (ho, wo) = l.out_shape(h, w);
        assert_eq!(y.shape(), (o, ho, wo));
        let mut sat2 = 0u32;
        for oc in 0..o {
            for p in 0..ho * wo {
                let a = acc[oc * ho * wo + p];
                let expect = k::clamp16(k::rshift_round(a * l.m[oc] + l.bp[oc], l.shift as i32), &mut sat2);
                assert_eq!(y.v[oc * ho * wo + p], expect, "{}: output {oc},{p}", l.name);
            }
        }
        assert_eq!(sat, sat2);
    }
}

#[test]
fn rounding_helpers_follow_python_semantics() {
    assert_eq!(k::rshift_round(-3, 1), -1);
    assert_eq!(k::rshift_round(-1, 1), 0);
    assert_eq!(k::rshift_round(-2, 1), -1);
    assert_eq!(k::rshift_round(1, 1), 1);
    assert_eq!(k::rshift_round(2, 2), 1);
    assert_eq!(k::rshift_round(-6, 2), -1);
    assert_eq!(k::rshift_round(-7, 2), -2);
    assert_eq!(k::rshift_round(5, 0), 5);
    assert_eq!(k::round_div(-3, 2), -1);
    assert_eq!(k::round_div(-1, 2), 0);
    assert_eq!(k::round_div(1, 2), 1);
    assert_eq!(k::round_div(-5, 3), -2);
    assert_eq!(k::round_div(7, 2), 4);
    assert_eq!(k::round_div(-7, 2), -3);
    assert_eq!(k::rescale(-5, 12, 10), -1);
    assert_eq!(k::rescale(-5, 10, 12), -20);
    for n in [0u128, 1, 2, 3, 4, 15, 16, 17, 1_000_000_000_000, (1u128 << 100) + 12345, (1u128 << 102) / 7, u64::MAX as u128] {
        let r = k::isqrt_u128(n);
        assert!(r * r <= n && n < (r + 1) * (r + 1), "isqrt {n}");
    }
}

#[test]
fn tester_detects_a_corrupted_constant() {
    let mut k = load_constants(&oracle_dir("int16_d2_1328_correct"));
    let o = load_oracle(&oracle_dir("int16_d2_1328_correct"));
    let idx = k.convs.iter().position(|l| l.name == "in_conv").expect("in_conv");
    k.convs[idx].w[0] = k.convs[idx].w[0].wrapping_add(1);
    k.convs[idx].finalize().unwrap();
    let mut hook = Compare { oracle: &o, substitute: false, seen: 0, mismatches: Vec::new() };
    let (r, _) = evaluate(&k, &o.c_int, &o.noise_int, &o.e_int, &mut hook);
    assert!(!hook.mismatches.is_empty(), "a corrupted weight went unnoticed");
    assert_eq!(hook.mismatches[0].name, "in_conv", "the first mismatch must be the corrupted layer");
    assert_ne!(r, o.residual_sum_int);
    println!("corrupted in_conv: {} layers differ, first {}: {}", hook.mismatches.len(), hook.mismatches[0].name, hook.mismatches[0].detail);
}
