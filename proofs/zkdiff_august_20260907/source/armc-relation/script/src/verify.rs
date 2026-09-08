//! `zkdiff-verify`: the acceptance verifier (Astra r5 finding 3). Cold, standalone, CPU only: it never derives a key
//! from an ELF and never runs SP1 setup. It takes the proof, the public bytes, the PINNED program vkey and the pinned
//! circuit verifier key (the expected-identities JSON), and fails closed on any expected-identity mismatch.
//!
//! usage:
//!   zkdiff-verify --proof ARTIFACT.bin --expect EXPECTED.json [--report OUT.json] [--controls]
//!       ARTIFACT.bin is the exact `row_XXXXXX_groth16.bin` (bincode SP1ProofWithPublicValues) the ceremony wrote
//!   zkdiff-verify --proof-bytes P.bin --public V.bin --expect EXPECTED.json [--report OUT.json] [--controls]
//!       the raw `SP1ProofWithPublicValues::bytes()` output (4-byte circuit-key prefix + encoded proof) and the 752 bytes
//!   zkdiff-verify --groth16-only --proof ARTIFACT.bin --vkey 0x... [--report OUT.json] [--controls]
//!       the Groth16 layer alone, for any SP1 6.4.0 Groth16 artifact (machinery check; no ZBDIFF acceptance)
//!   zkdiff-verify --identity [--with-vkey]
//!       prints the circuit version, the embedded circuit verifier key digest, the vk root and the embedded guest ELF
//!
//! `--controls` runs the proof-level negative controls of Astra r5 finding 10 against the given proof: relation-level
//! mutations of representative public fields (kind, offset-rule flag, u, offset, constants digest, noise BLAKE3,
//! R_correct, clip count), of the proof bytes and of the program vkey, each of which the Groth16 verifier must reject,
//! and policy-level mutations of the expected identities (constants digest, noise table, session root, row table)
//! under which the proof still verifies but acceptance must fail at the named check. Every control is recorded with
//! its mutation, expected failure stage, actual error and the sha256 of the mutated artefact.
//!
//! Exit status: 0 only if the proof is accepted (and, with --controls, every control behaved as expected).
#![recursion_limit = "512"]
#![allow(dead_code)]

mod accept;
mod ceremony_core;
mod witness;

use std::path::{Path, PathBuf};

use accept::{accept, groth16_rejection_controls, policy_rejection_controls, Control, Expected};
use ceremony_core::{load_exact, sha256_hex};
use sp1_sdk::{include_elf, Elf, SP1Proof, SP1_CIRCUIT_VERSION};

const ZKDIFF_ELF: Elf = include_elf!("zkdiff-guest");

fn usage() -> ! {
    eprintln!(
        "usage:\n  zkdiff-verify --proof ARTIFACT.bin --expect EXPECTED.json [--report OUT.json] [--controls]\n  zkdiff-verify --proof-bytes P.bin --public V.bin --expect EXPECTED.json [--report OUT.json] [--controls]\n  zkdiff-verify --groth16-only --proof ARTIFACT.bin --vkey 0x... [--report OUT.json] [--controls]\n  zkdiff-verify --identity [--with-vkey]"
    );
    std::process::exit(2);
}

/// Load an exact ceremony artifact and return (proof bytes as the verifier wants them, public bytes, sp1_version, sha256 of the artifact).
fn load_artifact(path: &Path) -> Result<(Vec<u8>, Vec<u8>, String, String, u64), String> {
    let (proof, bytes, digest) = load_exact(path)?;
    if !matches!(&proof.proof, SP1Proof::Groth16(_)) {
        return Err("artifact is not a Groth16 proof".into());
    }
    Ok((proof.bytes(), proof.public_values.to_vec(), proof.sp1_version.clone(), digest, bytes))
}

fn write_report(path: Option<&Path>, report: &serde_json::Value) {
    let text = serde_json::to_string_pretty(report).unwrap();
    println!("{text}");
    if let Some(p) = path {
        ceremony_core::write_durable(p, text.as_bytes()).unwrap_or_else(|e| {
            eprintln!("VERIFY FAILED: cannot write report: {e}");
            std::process::exit(1);
        });
    }
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.is_empty() {
        usage();
    }
    let flag = |f: &str| args.iter().any(|a| a == f);
    let report_path = witness::arg(&args, "--report").map(PathBuf::from);
    if flag("--identity") {
        let mut id = serde_json::json!({
            "sp1_circuit_version": SP1_CIRCUIT_VERSION,
            "groth16_vk_sha256": accept::embedded_groth16_vk_sha256(),
            "groth16_vk_bytes": accept::embedded_groth16_vk_bytes(),
            "vk_root": accept::vk_root_hex(),
            "guest_elf_sha256": sha256_hex(&ZKDIFF_ELF),
            "guest_elf_bytes": ZKDIFF_ELF.len(),
            "verifier_binary_sha256": std::fs::read("/proc/self/exe").map(|b| sha256_hex(&b)).unwrap_or_default(),
        });
        if flag("--with-vkey") {
            use sp1_sdk::{blocking::{Prover, ProverClient}, HashableKey, ProvingKey};
            let client = ProverClient::builder().cpu().build();
            let pk = client.setup(ZKDIFF_ELF).expect("SP1 setup");
            id["sp1_vkey"] = serde_json::json!(pk.verifying_key().bytes32());
        }
        write_report(report_path.as_deref(), &id);
        return;
    }
    let controls = flag("--controls");
    let result: Result<serde_json::Value, String> = (|| {
        if flag("--groth16-only") {
            let proof = PathBuf::from(witness::arg(&args, "--proof").unwrap_or_else(|| usage()));
            let vkey = witness::arg(&args, "--vkey").unwrap_or_else(|| usage());
            let (pb, public, version, artefact_sha, artefact_bytes) = load_artifact(&proof)?;
            let vk_sha = accept::embedded_groth16_vk_sha256();
            let verified = accept::verify_groth16_standalone(&pb, &public, &vkey, &vk_sha);
            let mut rep = serde_json::json!({
                "mode": "groth16_only", "artifact": proof.display().to_string(), "artifact_sha256": artefact_sha, "artifact_bytes": artefact_bytes,
                "artifact_sp1_version": version, "verifier_sp1_circuit_version": SP1_CIRCUIT_VERSION, "groth16_vk_sha256": vk_sha,
                "program_vkey": vkey, "proof_bytes": pb.len(), "proof_bytes_sha256": sha256_hex(&pb),
                "public_values_bytes": public.len(), "public_values_sha256": sha256_hex(&public),
                "verified": verified.is_ok(), "error": verified.as_ref().err(),
            });
            let mut ok = verified.is_ok() && version == SP1_CIRCUIT_VERSION;
            if controls {
                let cs = groth16_rejection_controls(&pb, &public, &vkey, &vk_sha);
                ok &= cs.iter().all(|c| c.behaved);
                rep["controls"] = serde_json::json!(cs.iter().map(Control::json).collect::<Vec<_>>());
                rep["controls_all_behaved"] = serde_json::json!(cs.iter().all(|c| c.behaved));
            }
            rep["ok"] = serde_json::json!(ok);
            return if ok { Ok(rep) } else { Err(serde_json::to_string_pretty(&rep).unwrap()) };
        }
        let exp = Expected::load(Path::new(&witness::arg(&args, "--expect").unwrap_or_else(|| usage())))?;
        let (pb, public, version, artefact, artefact_sha, artefact_bytes) = if let Some(p) = witness::arg(&args, "--proof-bytes") {
            let pb = std::fs::read(&p).map_err(|e| format!("cannot read {p}: {e}"))?;
            let v = witness::arg(&args, "--public").unwrap_or_else(|| usage());
            let public = std::fs::read(&v).map_err(|e| format!("cannot read {v}: {e}"))?;
            let sha = sha256_hex(&pb);
            let n = pb.len() as u64;
            (pb, public, String::from("(raw bytes: version not carried)"), format!("{p} + {v}"), sha, n)
        } else {
            let proof = PathBuf::from(witness::arg(&args, "--proof").unwrap_or_else(|| usage()));
            let (pb, public, version, sha, n) = load_artifact(&proof)?;
            (pb, public, version, proof.display().to_string(), sha, n)
        };
        let mut rep = serde_json::json!({
            "mode": "acceptance", "artifact": artefact, "artifact_sha256": artefact_sha, "artifact_bytes": artefact_bytes,
            "artifact_sp1_version": version, "verifier_sp1_circuit_version": SP1_CIRCUIT_VERSION, "expected_sp1_circuit_version": exp.str("sp1_circuit_version"),
            "expected_identities": exp.path, "expected_identities_sha256": exp.sha256,
            "program_vkey": exp.vkey(), "proof_bytes": pb.len(), "proof_bytes_sha256": sha256_hex(&pb),
            "public_values_bytes": public.len(), "public_values_sha256": sha256_hex(&public), "public_values_hex": witness::hex(&public),
        });
        let mut ok = true;
        if version != exp.str("sp1_circuit_version") && !version.starts_with("(raw") {
            rep["version_check"] = serde_json::json!(format!("FAIL: artifact {version} != expected {}", exp.str("sp1_circuit_version")));
            ok = false;
        } else if SP1_CIRCUIT_VERSION != exp.str("sp1_circuit_version") {
            rep["version_check"] = serde_json::json!(format!("FAIL: this verifier is {SP1_CIRCUIT_VERSION}, expected {}", exp.str("sp1_circuit_version")));
            ok = false;
        } else {
            rep["version_check"] = serde_json::json!("PASS");
        }
        let a = accept(&pb, &public, &exp);
        ok &= a.ok();
        rep["acceptance"] = a.json();
        if let Some(p) = &a.decoded {
            rep["statement"] = serde_json::json!({
                "row": p.row_r, "wrong_row": p.row_u, "offset": p.offset, "offset_rule": if p.offset_rule == 1 { "mirrored" } else { "direct" },
                "denoiser_kind": p.denoiser_kind, "r_correct": p.r_correct, "r_wrong": p.r_wrong, "difference": p.difference(),
                "outcome_class": a.outcome_class, "clip_events": p.clip_events, "noise_blake3": witness::hex(&p.noise_blake3),
                "raw_blake3": witness::hex(&p.raw_blake3_r), "constants_sha256": witness::hex(&p.constants_sha256),
            });
        }
        if controls {
            let mut cs = groth16_rejection_controls(&pb, &public, exp.vkey(), exp.str("groth16_vk_sha256"));
            cs.extend(policy_rejection_controls(&pb, &public, &exp));
            let all = cs.iter().all(|c| c.behaved);
            ok &= all;
            rep["controls"] = serde_json::json!(cs.iter().map(Control::json).collect::<Vec<_>>());
            rep["controls_all_behaved"] = serde_json::json!(all);
        }
        rep["ok"] = serde_json::json!(ok);
        if ok {
            Ok(rep)
        } else {
            Err(serde_json::to_string_pretty(&rep).unwrap())
        }
    })();
    match result {
        Ok(rep) => {
            write_report(report_path.as_deref(), &rep);
            println!("verified_and_accepted=true");
        }
        Err(text) => {
            // the report is written on failure too, with ok=false, so the failure is on record
            if let Ok(v) = serde_json::from_str::<serde_json::Value>(&text) {
                write_report(report_path.as_deref(), &v);
            } else {
                eprintln!("{text}");
            }
            eprintln!("VERIFY FAILED");
            println!("verified_and_accepted=false");
            std::process::exit(1);
        }
    }
}
