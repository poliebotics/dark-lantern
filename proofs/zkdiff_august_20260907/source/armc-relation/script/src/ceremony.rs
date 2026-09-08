//! The proving ceremony host for ONE witness, the proved script/src/ceremony.rs adapted to the diffusion statement
//! (machinery in ceremony_core.rs). Not run on the development machine for proving: proving is a Lambda-box job behind the release step,
//! the development machine has no Go for the gnark wrap (feature `groth16`) and no attached GPU for `cuda`.
//!
//! usage:
//!   ceremony prove  --witness-dir DIR --raw PATH --blob PATH --out DIR [--expect EXPECTED.json] [--prover cpu|cuda] [--device N] [--cycle-limit N] [--expected PATH]
//!   ceremony verify --proof PATH --expect EXPECTED.json [--elf PATH] [--report OUT.json]
//!   ceremony export --proof PATH --out DIR
//!   ceremony vkey [--elf PATH]
//!
//! `verify` (Astra r5 finding 3): the SDK verification runs under the vkey derived from the embedded ELF (or `--elf`),
//! and that vkey MUST equal the pinned `sp1_vkey` of the expected identities, otherwise the command fails before
//! verifying anything; the three SDK tamper controls follow, then the acceptance verifier (`accept.rs`) checks every
//! expected identity on the public bytes. Success is printed only when every layer passes. The standalone path with
//! no SP1 setup at all is `zkdiff-verify`.
//!
//! `--device N` (cuda only) maps to `ProverClient::builder().cuda().with_device_id(N)`: the SDK defaults to CUDA
//! device 0 and overwrites CUDA_VISIBLE_DEVICES for the gpu server, so this flag is the only way to pick the GPU.
#![recursion_limit = "512"]
#![allow(dead_code)]

mod accept;
mod ceremony_core;
mod witness;

use std::fs;
use std::path::{Path, PathBuf};
use std::time::Instant;

use accept::Expected;
use ceremony_core::{load_exact, prove_built, sha256_hex, verify_original_and_tamper, write_json_durable, DEFAULT_CYCLE_LIMIT};
use sp1_sdk::{
    blocking::{Prover, ProverClient},
    include_elf, Elf, HashableKey, ProvingKey, SP1Proof, SP1_CIRCUIT_VERSION,
};

use armc_relation::statement::PUBLIC_BYTES;

const ZKDIFF_ELF: Elf = include_elf!("zkdiff-guest");

fn usage() -> ! {
    eprintln!(
        "usage:\n  ceremony prove  --witness-dir DIR --raw PATH --blob PATH --out DIR [--expect EXPECTED.json] [--prover cpu|cuda] [--device N] [--cycle-limit N] [--expected PATH]\n  ceremony verify --proof PATH --expect EXPECTED.json [--elf PATH] [--report OUT.json]\n  ceremony export --proof PATH --out DIR\n  ceremony vkey [--elf PATH]"
    );
    std::process::exit(2);
}

#[allow(clippy::too_many_arguments)]
fn run_prove<P: Prover>(client: &P, prover_name: &str, dir: &Path, raw: &str, blob: &Path, expected_python: Option<PathBuf>, expected: Option<&Expected>, out_dir: &Path, cycle_limit: u64) -> Result<(), String> {
    let network = witness::Network::load(blob);
    let built = witness::build(dir, raw, expected_python, &network);
    let setup_started = Instant::now();
    let proving_key = client.setup(ZKDIFF_ELF).map_err(|e| format!("SP1 setup failed: {e}"))?;
    let setup_ms = setup_started.elapsed().as_millis();
    println!("mode=ceremony_groth16");
    println!("prover={prover_name}");
    println!("row={}", built.row);
    println!("sp1_circuit_version={SP1_CIRCUIT_VERSION}");
    println!("groth16_vk_sha256={}", accept::embedded_groth16_vk_sha256());
    println!("cycle_limit_requested={cycle_limit}");
    println!("raw_bytes={} raw_sha256={}", built.witness.raw.len(), sha256_hex(&built.witness.raw));
    println!("constants_blob={} constants_blob_bytes={} constants_sha256={} spec_sha256={}", blob.display(), network.blob.len(), network.blob_sha256_hex(), network.spec_sha256_hex());
    println!("guest_elf_bytes={} guest_elf_sha256={}", ZKDIFF_ELF.len(), sha256_hex(&ZKDIFF_ELF));
    println!("sp1_vkey={}", proving_key.verifying_key().bytes32());
    println!("expected_identities={}", expected.map(|e| format!("{} sha256 {}", e.path, e.sha256)).unwrap_or_else(|| "none (acceptance not run; the receipt says so)".into()));
    println!("setup_elapsed_ms={setup_ms}");
    fs::create_dir_all(out_dir).map_err(|e| format!("cannot create {}: {e}", out_dir.display()))?;
    let record = prove_built(client, ZKDIFF_ELF, &proving_key, setup_ms, &built, &network, out_dir, cycle_limit, expected)?;
    let manifest = record.manifest(prover_name);
    write_json_durable(&out_dir.join(format!("row_{:06}_manifest.json", built.row)), &manifest)?;
    println!("oracle={} checked={} circuit_derived=0", record.oracle_mode, record.public.len());
    for n in &record.oracle_notes {
        println!("oracle_note={n}");
    }
    println!("public_values_bytes={}", record.public.len());
    println!("public_values_sha256={}", sha256_hex(&record.public));
    println!("outcome_class={}", record.outcome_class);
    println!("prove_elapsed_ms={}", record.prove_ms);
    println!("verify_and_tamper_elapsed_ms={}", record.verify_ms);
    println!("acceptance_elapsed_ms={} accepted={}", record.accept_ms, record.acceptance.as_ref().map(|a| a["accepted"].to_string()).unwrap_or_else(|| "not_run".into()));
    println!("host_peak_rss_kib={:?}", record.host_peak_rss_kib);
    println!("proof_output={}", out_dir.join(&record.proof_file).display());
    println!("proof_bytes={} proof_sha256={}", record.proof_bytes, record.proof_sha256);
    println!("proof_raw_bytes={} proof_raw_sha256={}", record.proof_raw_bytes, record.proof_raw_sha256);
    println!("verified_proof=true");
    println!("proof_generated=true");
    Ok(())
}

fn run_verify<P: Prover>(client: &P, path: &Path, elf_path: Option<&Path>, exp: &Expected, report: Option<&Path>) -> Result<(), String> {
    let elf: Elf = match elf_path {
        Some(p) => Elf::from(fs::read(p).map_err(|e| format!("cannot read ELF {}: {e}", p.display()))?),
        None => ZKDIFF_ELF,
    };
    let (proof, bytes, digest) = load_exact(path)?;
    if !matches!(&proof.proof, SP1Proof::Groth16(_)) {
        return Err("loaded proof is not Groth16".into());
    }
    if proof.sp1_version != SP1_CIRCUIT_VERSION || proof.sp1_version != exp.str("sp1_circuit_version") {
        return Err(format!("loaded proof uses circuit version {}, this host {SP1_CIRCUIT_VERSION}, expected {}", proof.sp1_version, exp.str("sp1_circuit_version")));
    }
    let elf_sha256 = sha256_hex(&elf);
    if elf_sha256 != exp.str("guest_elf_sha256") {
        return Err(format!("the ELF at hand ({elf_sha256}) is not the pinned guest ({}); the key is never derived from an unpinned ELF", exp.str("guest_elf_sha256")));
    }
    let proving_key = client.setup(elf).map_err(|e| format!("SP1 setup failed: {e}"))?;
    let vkey = proving_key.verifying_key().bytes32();
    if vkey != exp.vkey() {
        return Err(format!("derived vkey {vkey} differs from the pinned {}", exp.vkey()));
    }
    let t = Instant::now();
    let sdk_controls = verify_original_and_tamper(client, &proof, proving_key.verifying_key())?;
    let sdk_ms = t.elapsed().as_millis();
    let public = proof.public_values.to_vec();
    if public.len() != PUBLIC_BYTES {
        return Err("public value length differs".into());
    }
    let raw = proof.bytes();
    let a = accept::accept(&raw, &public, exp);
    let rep = serde_json::json!({
        "mode": "cold_verify_groth16",
        "artifact": path.display().to_string(), "artifact_bytes": bytes, "artifact_sha256": digest,
        "sp1_vkey": vkey, "guest_elf_sha256": elf_sha256, "sp1_circuit_version": proof.sp1_version,
        "groth16_vk_sha256": accept::embedded_groth16_vk_sha256(),
        "expected_identities": exp.path, "expected_identities_sha256": exp.sha256,
        "proof_raw_bytes": raw.len(), "proof_raw_sha256": sha256_hex(&raw),
        "public_values_sha256": sha256_hex(&public), "public_values_hex": witness::hex(&public),
        "sdk_verify_and_tamper_elapsed_ms": sdk_ms, "sdk_tamper_controls": sdk_controls,
        "acceptance": a.json(),
        "verified_and_accepted": a.ok(),
    });
    if let Some(p) = report {
        write_json_durable(p, &rep)?;
    }
    println!("{}", serde_json::to_string_pretty(&rep).unwrap());
    if !a.ok() {
        return Err(format!("proof verifies but the statement is not the expected one: {}", a.failed.unwrap_or_default()));
    }
    let decoded = a.decoded.unwrap();
    println!(
        "statement: row {} wrong {} offset {} rule {} kind {} R_correct {} R_wrong {} D {} outcome {} clip_events {}",
        decoded.row_r,
        decoded.row_u,
        decoded.offset,
        decoded.offset_rule,
        decoded.denoiser_kind,
        decoded.r_correct,
        decoded.r_wrong,
        decoded.difference(),
        a.outcome_class.unwrap_or("?"),
        decoded.clip_events
    );
    println!("verified_and_accepted=true");
    Ok(())
}

fn main() {
    sp1_sdk::utils::setup_logger();
    let args: Vec<String> = std::env::args().skip(1).collect();
    let Some(command) = args.first() else { usage() };
    let prover = witness::arg(&args, "--prover").unwrap_or_else(|| "cpu".into());
    let result = match command.as_str() {
        "prove" => {
            let dir = PathBuf::from(witness::arg(&args, "--witness-dir").unwrap_or_else(|| usage()));
            let raw = witness::arg(&args, "--raw").unwrap_or_else(|| usage());
            let blob = PathBuf::from(witness::arg(&args, "--blob").unwrap_or_else(|| usage()));
            let out = PathBuf::from(witness::arg(&args, "--out").unwrap_or_else(|| usage()));
            let expected_python = witness::arg(&args, "--expected").map(PathBuf::from);
            let expected = witness::arg(&args, "--expect").map(|p| Expected::load(Path::new(&p)).unwrap_or_else(|e| panic!("{e}")));
            let cycle_limit = witness::arg(&args, "--cycle-limit").map(|v| v.parse().expect("cycle limit")).unwrap_or(DEFAULT_CYCLE_LIMIT);
            let device: u32 = witness::arg(&args, "--device").map(|v| v.parse().expect("cuda device id")).unwrap_or(0);
            match prover.as_str() {
                "cpu" => run_prove(&ProverClient::builder().cpu().build(), "local_cpu_explicit", &dir, &raw, &blob, expected_python, expected.as_ref(), &out, cycle_limit),
                #[cfg(feature = "cuda")]
                "cuda" => {
                    println!("cuda_device_id={device}");
                    run_prove(&ProverClient::builder().cuda().with_device_id(device).build(), &format!("local_cuda_explicit_device{device}"), &dir, &raw, &blob, expected_python, expected.as_ref(), &out, cycle_limit)
                }
                other => {
                    let _ = device;
                    Err(format!("unknown or unbuilt prover {other}"))
                }
            }
        }
        "vkey" => {
            let elf: Elf = match witness::arg(&args, "--elf") {
                Some(p) => Elf::from(fs::read(&p).expect("read ELF")),
                None => ZKDIFF_ELF,
            };
            let sha = sha256_hex(&elf);
            let len = elf.len();
            let client = ProverClient::builder().cpu().build();
            client
                .setup(elf)
                .map(|pk| {
                    println!("guest_elf_bytes={len} guest_elf_sha256={sha}");
                    println!("sp1_vkey={}", pk.verifying_key().bytes32());
                    println!("sp1_circuit_version={SP1_CIRCUIT_VERSION} groth16_vk_sha256={}", accept::embedded_groth16_vk_sha256());
                })
                .map_err(|e| format!("SP1 setup failed: {e}"))
        }
        "export" => {
            let proof = PathBuf::from(witness::arg(&args, "--proof").unwrap_or_else(|| usage()));
            let out = PathBuf::from(witness::arg(&args, "--out").unwrap_or_else(|| usage()));
            (|| -> Result<(), String> {
                let (p, _, digest) = load_exact(&proof)?;
                if !matches!(&p.proof, SP1Proof::Groth16(_)) {
                    return Err("not a Groth16 proof".into());
                }
                let stem = proof.file_stem().unwrap().to_string_lossy().to_string();
                let raw = p.bytes();
                let public = p.public_values.to_vec();
                fs::create_dir_all(&out).map_err(|e| e.to_string())?;
                ceremony_core::write_durable(&out.join(format!("{stem}_proof.bin")), &raw)?;
                ceremony_core::write_durable(&out.join(format!("{stem}_public_values.bin")), &public)?;
                println!("source_artifact_sha256={digest}");
                println!("raw_proof_bytes={} raw_proof_sha256={}", raw.len(), sha256_hex(&raw));
                println!("public_values_bytes={} public_values_sha256={}", public.len(), sha256_hex(&public));
                println!("sp1_version={}", p.sp1_version);
                Ok(())
            })()
        }
        "verify" => {
            let proof = PathBuf::from(witness::arg(&args, "--proof").unwrap_or_else(|| usage()));
            let elf = witness::arg(&args, "--elf").map(PathBuf::from);
            let report = witness::arg(&args, "--report").map(PathBuf::from);
            let exp = witness::arg(&args, "--expect").map(|p| Expected::load(Path::new(&p))).unwrap_or_else(|| Err("verify requires --expect EXPECTED.json (the pinned identities); no key is derived from an unpinned ELF".into()));
            match exp {
                Ok(exp) => run_verify(&ProverClient::builder().cpu().build(), &proof, elf.as_deref(), &exp, report.as_deref()),
                Err(e) => Err(e),
            }
        }
        _ => usage(),
    };
    if let Err(e) = result {
        eprintln!("CEREMONY FAILED: {e}");
        std::process::exit(1);
    }
}
