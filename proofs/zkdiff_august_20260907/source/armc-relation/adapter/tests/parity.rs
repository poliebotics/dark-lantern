//! Parity of the adapter (relation-derived inputs -> armc-int network -> residual sum) against the G1 oracle.
//!
//! Inputs come from the relation's own vector set (`vectors_relation/d2`: the cached `C_int`, the protocol noise, the
//! torch-path `E_int` of rows 1328 and 1330, all sha256-pinned to the G1 manifests by `relation/tests/vectors.rs`),
//! go through the relation's `forward_noise` and `hint14`, and the adapter's `predict` must reproduce G1's residual
//! sums exactly: with the step-12000 blob (`blobs/int16`) 12,775,807,457 / 15,569,339,266, with the FINAL blob
//! (`blobs/final_int16`) 8,764,459,045 / 22,311,372,969. The FINAL oracle exports (`oracle_final/`) add the August
//! row 650 pair and a layer-by-layer comparison of every one of the 188 layer outputs.

use armc_int::loader::{load_constants, load_oracle, OracleSet};
use armc_int::model::{evaluate, Hook};
use armc_int::Tensor;
use armc_relation::hint::hint14;
use armc_relation::net::Denoiser;
use armc_relation::noise::{forward_noise, residual_sum};
use std::path::PathBuf;
use zkdiff_armc_adapter::ArmcIntDenoiser;

fn g2() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..").join("..")
}

fn i16s(path: &PathBuf) -> Vec<i16> {
    let b = std::fs::read(path).unwrap_or_else(|e| panic!("read {}: {e}", path.display()));
    b.chunks_exact(2).map(|c| i16::from_le_bytes([c[0], c[1]])).collect()
}

fn blob(rel: &str) -> Vec<u8> {
    let p = g2().join(rel);
    std::fs::read(&p).unwrap_or_else(|e| panic!("constants blob {} missing: {e} (build it with armc-blob first)", p.display()))
}

fn d2_inputs() -> (Vec<i16>, Vec<i16>, Vec<i16>, Vec<i16>) {
    let d = g2().join("vectors_relation").join("d2");
    let c = i16s(&d.join("row_001328_C_q12_cache.bin"));
    let n = i16s(&d.join("row_001328_noise_q12.bin"));
    let e_r = i16s(&d.join("row_001328_E_q14_torchpath.bin"));
    let e_u = i16s(&d.join("row_001330_E_q14_torchpath.bin"));
    let (ct, sat) = forward_noise(&c, &n).unwrap();
    assert_eq!(sat, 0);
    (ct, n, e_r, e_u)
}

fn two_arms(net: &ArmcIntDenoiser, ct: &[i16], noise: &[i16], e_r: &[i16], e_u: &[i16]) -> (u64, u64) {
    let (eps_r, clips_r) = net.predict(ct, &hint14(e_r)).expect("predict r");
    let (eps_u, clips_u) = net.predict(ct, &hint14(e_u)).expect("predict u");
    assert_eq!((clips_r, clips_u), (0, 0), "no clipping event on the reference rows");
    (residual_sum(&eps_r, noise).unwrap(), residual_sum(&eps_u, noise).unwrap())
}

#[test]
fn d2_row_1328_with_the_step12000_blob_reproduces_g1s_residual_sums() {
    let net = ArmcIntDenoiser::from_blob(&blob("blobs/int16/constants_int16.blob")).expect("blob");
    assert_eq!(net.kind(), 1);
    let (ct, n, e_r, e_u) = d2_inputs();
    let (r_c, r_w) = two_arms(&net, &ct, &n, &e_r, &e_u);
    assert_eq!(r_c, 12_775_807_457, "R_correct (step-12000 constants)");
    assert_eq!(r_w, 15_569_339_266, "R_wrong +2 (step-12000 constants)");
    println!("step12000 blob sha256 {} : R_correct {r_c} R_wrong {r_w}", armc_relation::header::hex(&net.constants_sha256()));
}

#[test]
fn d2_row_1328_with_the_final_blob_reproduces_g1s_residual_sums() {
    let net = ArmcIntDenoiser::from_blob(&blob("blobs/final_int16/constants_int16.blob")).expect("blob");
    let (ct, n, e_r, e_u) = d2_inputs();
    let (r_c, r_w) = two_arms(&net, &ct, &n, &e_r, &e_u);
    assert_eq!(r_c, 8_764_459_045, "R_correct (FINAL constants, g1_integer/final/vectors)");
    assert_eq!(r_w, 22_311_372_969, "R_wrong +2 (FINAL constants)");
    println!("final blob sha256 {} : R_correct {r_c} R_wrong {r_w}", armc_relation::header::hex(&net.constants_sha256()));
}

struct Compare<'a> {
    oracle: &'a OracleSet,
    seen: usize,
    mismatches: Vec<String>,
}

impl<'a> Hook for Compare<'a> {
    fn layer(&mut self, name: &str, t: Tensor) -> Tensor {
        self.seen += 1;
        match self.oracle.layers.get(name) {
            None => self.mismatches.push(format!("{name}: not in the oracle export")),
            Some(r) => {
                if r.shape() != t.shape() || r.f != t.f {
                    self.mismatches.push(format!("{name}: shape/f oracle {:?} f={} rust {:?} f={}", r.shape(), r.f, t.shape(), t.f));
                } else if let Some(i) = r.v.iter().zip(&t.v).position(|(a, b)| a != b) {
                    let n_bad = r.v.iter().zip(&t.v).filter(|(a, b)| a != b).count();
                    self.mismatches.push(format!("{name}: first mismatch at {i}: oracle {} rust {}; {n_bad} of {} differ", r.v[i], t.v[i], t.v.len()));
                }
            }
        }
        t
    }
}

/// Every layer output and the residual sum of one FINAL export set, chained (the Rust forward on its own outputs).
fn final_set_parity(set: &str, expected_residual: i64) -> OracleSet {
    let dir = g2().join("oracle_final").join(set);
    assert!(dir.join("index.json").is_file(), "oracle_final/{set} missing (run tools/export_oracle_final.py)");
    let k = load_constants(&dir);
    let o = load_oracle(&dir);
    let mut hook = Compare { oracle: &o, seen: 0, mismatches: Vec::new() };
    let (r, sat) = evaluate(&k, &o.c_int, &o.noise_int, &o.e_int, &mut hook);
    for m in &hook.mismatches {
        println!("  MISMATCH {m}");
    }
    assert_eq!(hook.seen, o.layers.len(), "{set}: every oracle layer produced exactly once");
    assert!(hook.mismatches.is_empty(), "{set}: {} layer(s) differ", hook.mismatches.len());
    assert_eq!(r, o.residual_sum_int, "{set}: residual sum");
    assert_eq!(r, expected_residual, "{set}: documented residual sum (README_FINAL.md section 6)");
    assert_eq!(sat, 0, "{set}: saturations");
    println!("[{set}] {} layers equal, residual {r}", hook.seen);
    o
}

#[test]
fn final_vectors_layer_by_layer_parity_d2_1328_and_august_650() {
    final_set_parity("int16_d2_1328_correct", 8_764_459_045);
    final_set_parity("int16_d2_1328_wrong_p2", 22_311_372_969);
    final_set_parity("int16_august_650_correct", 5_317_378_656);
    final_set_parity("int16_august_650_wrong_p2", 12_127_686_594);
}

#[test]
fn final_blob_through_the_adapter_reproduces_the_final_exports() {
    let net = ArmcIntDenoiser::from_blob(&blob("blobs/final_int16/constants_int16.blob")).expect("blob");
    for (set, expected) in [("int16_d2_1328_correct", 8_764_459_045_u64), ("int16_d2_1328_wrong_p2", 22_311_372_969), ("int16_august_650_correct", 5_317_378_656), ("int16_august_650_wrong_p2", 12_127_686_594)] {
        let dir = g2().join("oracle_final").join(set);
        assert!(dir.join("index.json").is_file(), "oracle_final/{set} missing (run tools/export_oracle_final.py)");
        let o = load_oracle(&dir);
        // the export's C_t must equal the relation's forward noising of its C_int and noise_int
        let (ct, sat) = forward_noise(&o.c_int, &o.noise_int).unwrap();
        assert_eq!(sat, 0);
        assert_eq!(ct, o.ct_int, "{set}: C_t");
        let (eps, clips) = net.predict(&ct, &hint14(&o.e_int)).expect("predict");
        assert_eq!(clips, 0);
        let r = residual_sum(&eps, &o.noise_int).unwrap();
        assert_eq!(r, expected, "{set}: residual through the adapter");
        assert_eq!(r as i64, o.residual_sum_int);
    }
}

#[test]
fn adapter_refuses_foreign_coordinates_and_wrong_shapes() {
    let net = ArmcIntDenoiser::from_blob(&blob("blobs/int16/constants_int16.blob")).expect("blob");
    let (ct, _n, e_r, _e_u) = d2_inputs();
    let mut hint = hint14(&e_r);
    let plane = 96 * 112;
    hint[12 * plane] ^= 1;
    assert_eq!(net.predict(&ct, &hint).unwrap_err().message(), "armc-int: hint coordinate planes differ from the constants blob");
    assert!(net.predict(&ct[..100], &hint14(&e_r)).is_err());
    // -32768 is inside the admitted domain (G1 FINAL): the evaluation runs and reports its clip count
    let mut edge_ct = ct.clone();
    edge_ct[7] = i16::MIN;
    let (eps, _clips) = net.predict(&edge_ct, &hint14(&e_r)).expect("endpoint input is admitted");
    assert_eq!(eps.len(), ct.len());
    // a blob with one flipped byte in the header is rejected, one flipped weight byte still parses but hashes differently
    let mut b = blob("blobs/int16/constants_int16.blob");
    let h0 = ArmcIntDenoiser::from_blob(&b).unwrap().constants_sha256();
    b[0] ^= 1;
    assert!(ArmcIntDenoiser::from_blob(&b).is_err());
    b[0] ^= 1;
    let pos = b.len() / 2;
    b[pos] ^= 1;
    if let Ok(other) = ArmcIntDenoiser::from_blob(&b) {
        assert_ne!(other.constants_sha256(), h0);
    }
}
