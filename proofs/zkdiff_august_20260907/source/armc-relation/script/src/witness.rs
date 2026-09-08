//! Shared witness loading and oracle checks for the host binaries (execute, ceremony, batch).
//!
//! A witness directory holds the private items as files, in the layout gen_vectors.py and `zkdiff-batch prepare`
//! write:
//!   header_r.bin  membership_r_zbosm001.bin  sig_r.bin  prev_zbdprv01.bin  leaf_u_zbdlfu01.bin  siblings_u.bin
//!   noise_q12.bin  offset.bin  [offset_rule.bin]
//! the raw frame comes from `--raw PATH` or `--raw synthetic:a` (the PRNG frame the vectors are built on), and the
//! armc-int constants blob from `--blob PATH`. The guest reads the ten witness items and then the blob.
//!
//! The oracle is the native re-execution of the same `evaluate` with the same adapter (a zkVM/native divergence
//! check), plus, when `--expected PATH` names the Python oracle's 752 bytes (gen_vectors.py, stub network), the
//! independent byte comparison of every field the network does not determine.

use std::path::{Path, PathBuf};

use armc_relation::net::Denoiser;
use armc_relation::spec::preprocess_spec_sha256;
use armc_relation::statement::{evaluate, PublicOutput, Witness, OFFSET_RULE_DIRECT, PUBLIC_BYTES};
use sp1_sdk::SP1Stdin;
use zkdiff_armc_adapter::ArmcIntDenoiser;

pub fn arg(args: &[String], flag: &str) -> Option<String> {
    args.iter().position(|a| a == flag).and_then(|i| args.get(i + 1).cloned())
}

pub fn hex(b: &[u8]) -> String {
    b.iter().map(|x| format!("{x:02x}")).collect()
}

fn splitmix64_at(seed: u64, i: u64) -> u64 {
    let mut z = seed.wrapping_add((i + 1).wrapping_mul(0x9E37_79B9_7F4A_7C15));
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^ (z >> 31)
}

/// The synthetic frames of gen_vectors.py (`synthetic:a`, `synthetic:b`), regenerated rather than stored.
pub fn synthetic_frame(kind: char) -> Vec<u8> {
    let seed = match kind {
        'a' => 0xA5A5_0001,
        'b' => 0xA5A5_0002,
        _ => panic!("unknown synthetic frame"),
    };
    let n = armc_relation::RAW_BYTES;
    let mut b = Vec::with_capacity(n + 8);
    let mut i = 0_u64;
    while b.len() < n {
        b.extend_from_slice(&splitmix64_at(seed, i).to_le_bytes());
        i += 1;
    }
    b.truncate(n);
    if kind == 'b' {
        for y in 0..armc_relation::RAW_H {
            for x in 0..armc_relation::RAW_W {
                let v = &mut b[y * armc_relation::RAW_W + x];
                if x < 1000 {
                    *v = u8::from(*v == 255);
                } else if x < 2000 {
                    *v &= 3;
                }
            }
        }
    }
    b
}

pub fn load_raw(spec: &str) -> Vec<u8> {
    match spec {
        "synthetic:a" => synthetic_frame('a'),
        "synthetic:b" => synthetic_frame('b'),
        path => std::fs::read(path).unwrap_or_else(|e| panic!("cannot read raw frame {path}: {e}")),
    }
}

/// The constants blob and the adapter built from it (hash checked to parse before anything runs).
pub struct Network {
    pub blob: Vec<u8>,
    pub net: ArmcIntDenoiser,
}

impl Network {
    pub fn load(path: &Path) -> Network {
        let blob = std::fs::read(path).unwrap_or_else(|e| panic!("cannot read constants blob {}: {e}", path.display()));
        let net = ArmcIntDenoiser::from_blob(&blob).unwrap_or_else(|e| panic!("constants blob {} rejected: {e}", path.display()));
        Network { blob, net }
    }
    pub fn blob_sha256_hex(&self) -> String {
        hex(&self.net.constants_sha256())
    }
    pub fn spec_sha256_hex(&self) -> String {
        hex(&self.net.spec_sha256())
    }
}

pub struct Built {
    pub witness: Witness,
    pub stdin: SP1Stdin,
    pub row: u32,
    pub expected_python: Option<Vec<u8>>,
}

/// The guest's input order: the ten witness items, then the blob.
pub fn stdin_of(w: &Witness, blob: &[u8]) -> SP1Stdin {
    let mut stdin = SP1Stdin::new();
    for item in [&w.header, &w.membership, &w.raw, &w.signature, &w.previous, &w.leaf_u, &w.siblings_u, &w.noise, &w.offset, &w.offset_rule] {
        stdin.write_vec(item.clone());
    }
    stdin.write_vec(blob.to_vec());
    stdin
}

pub fn build(dir: &Path, raw_spec: &str, expected: Option<PathBuf>, network: &Network) -> Built {
    let read = |name: &str| std::fs::read(dir.join(name)).unwrap_or_else(|e| panic!("cannot read {}: {e}", dir.join(name).display()));
    let offset_rule = if dir.join("offset_rule.bin").is_file() { read("offset_rule.bin") } else { vec![OFFSET_RULE_DIRECT] };
    let witness = Witness {
        header: read("header_r.bin"),
        membership: read("membership_r_zbosm001.bin"),
        raw: load_raw(raw_spec),
        signature: read("sig_r.bin"),
        previous: read("prev_zbdprv01.bin"),
        leaf_u: read("leaf_u_zbdlfu01.bin"),
        siblings_u: read("siblings_u.bin"),
        noise: read("noise_q12.bin"),
        offset: read("offset.bin"),
        offset_rule,
    };
    let row = u32::from_le_bytes(witness.header[12..16].try_into().expect("header row index"));
    let stdin = stdin_of(&witness, &network.blob);
    let expected_python = expected.map(|p| {
        let mut bytes = std::fs::read(&p).unwrap_or_else(|e| panic!("cannot read expected public bytes {}: {e}", p.display()));
        assert_eq!(bytes.len(), PUBLIC_BYTES, "expected public bytes must be 752 bytes");
        // gen_vectors.py leaves the preprocessing spec digest zero; the compiled constant is the guest's
        if bytes[628..660].iter().all(|&b| b == 0) {
            bytes[628..660].copy_from_slice(&preprocess_spec_sha256());
        }
        bytes
    });
    Built { witness, stdin, row, expected_python }
}

pub struct OracleReport {
    pub mode: String,
    pub bytes_checked: usize,
    pub notes: Vec<String>,
}

/// Public byte ranges the network determines: kind (10), constants and spec digests (564..628), the residual
/// tail (716..752). Everything else is the binding relation and must equal an independent computation.
fn network_determined(i: usize) -> bool {
    i == 10 || (564..628).contains(&i) || (716..752).contains(&i)
}
// (749..752, the clip flag and count, lie inside the residual tail range above)

/// The guest's committed bytes must equal the native re-execution with the same adapter, and (binding fields) the
/// Python oracle when supplied.
pub fn check(actual: &[u8], built: &Built, network: &Network) -> Result<OracleReport, String> {
    if actual.len() != PUBLIC_BYTES {
        return Err(format!("public value length {} differs from {PUBLIC_BYTES}", actual.len()));
    }
    let native = evaluate(&built.witness, &network.net).map_err(|e| format!("native evaluation rejects the witness: {e}"))?;
    if native != actual {
        let i = native.iter().zip(actual.iter()).position(|(a, b)| a != b).unwrap_or(0);
        return Err(format!("guest public values differ from the native re-execution at byte {i}"));
    }
    let mut mode = "native_reexecution".to_string();
    let mut notes = Vec::new();
    let mut checked = PUBLIC_BYTES;
    if let Some(expected) = &built.expected_python {
        let binding: Vec<usize> = (0..PUBLIC_BYTES).filter(|&i| !network_determined(i)).collect();
        if let Some(&i) = binding.iter().find(|&&i| expected[i] != actual[i]) {
            return Err(format!("guest public values differ from the Python oracle at binding byte {i}: guest {} oracle {}", hex(&actual[i..(i + 16).min(PUBLIC_BYTES)]), hex(&expected[i..(i + 16).min(PUBLIC_BYTES)])));
        }
        checked = binding.len();
        mode = "native_reexecution+python_oracle_binding_fields".into();
        notes.push(format!("python oracle (gen_vectors.py, stub network) agrees on all {} binding bytes; the {} network-determined bytes (kind, constants/spec digests, residual tail) are checked by the native re-execution only", binding.len(), PUBLIC_BYTES - binding.len()));
    }
    let p = PublicOutput::parse(actual).map_err(|e| e.to_string())?;
    if p.denoiser_kind != network.net.kind() || p.constants_sha256 != network.net.constants_sha256() || p.spec_sha256 != network.net.spec_sha256() {
        return Err("public network identity differs from the host's adapter".into());
    }
    notes.push(format!(
        "row {} wrong {} offset {} offset_rule {} kind {} constants_sha256 {} R_correct {} R_wrong {} D {} sign {} clip_events {}",
        p.row_r,
        p.row_u,
        p.offset,
        p.offset_rule,
        p.denoiser_kind,
        hex(&p.constants_sha256),
        p.r_correct,
        p.r_wrong,
        p.difference(),
        u8::from(p.difference() > 0),
        p.clip_events
    ));
    Ok(OracleReport { mode, bytes_checked: checked, notes })
}
