//! Proving-ceremony machinery shared by `zkdiff-ceremony` and `zkdiff-batch`, copied from the proved
//! script/src/ceremony.rs (rust/row_binding_join_membership_sp1_candidate): the `.groth16()` request with the
//! returned mode asserted, verification, the tamper controls (each recorded with the SDK's actual error text), the
//! acceptance verifier against the frozen expected identities (Astra r5 finding 3), and exact, durable on-disk
//! artifacts (proof, raw proof bytes, public bytes, manifest: every one written to a temp file, fsynced, renamed, the
//! directory fsynced; Astra r5 finding 9). Not run on the development machine for proving (no Go for the gnark wrap, no GPU); the Lambda
//! box runs it behind the release step.

use std::fs::{self, File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Write};
use std::os::unix::fs::OpenOptionsExt;
use std::path::Path;
use std::time::Instant;

use bincode::Options;
use sha2::{Digest, Sha256};
use sp1_sdk::{
    blocking::{ProveRequest, Prover},
    Elf, HashableKey, ProvingKey, SP1Proof, SP1ProofWithPublicValues, SP1PublicValues, SP1_CIRCUIT_VERSION,
};

use crate::accept::{self, Expected};
use crate::witness::{self, Built, Network};
use armc_relation::statement::{PublicOutput, PUBLIC_BYTES};

/// Astra's G1 launch gate is 200 G instructions; the limit is a ceiling, not a target. NOTE (Astra r5 finding 8): the
/// pinned `sp1-cuda` 6.4.0 client does not forward this limit to the GPU server, so under `--prover cuda` it is
/// requested metadata, not an enforced bound; the executor path (`execute`) and the CPU prover do enforce it.
pub const DEFAULT_CYCLE_LIMIT: u64 = 200_000_000_000;
pub const MAX_PROOF_BYTES: u64 = 64 * 1024 * 1024;
/// A byte of R_correct (public offset 716..724): the control flips the published result itself.
pub const TAMPER_PUBLIC_BYTE: usize = 716;
pub const TAMPER_GROTH16_PROOF_BYTE: usize = 96;

pub fn sha256_hex(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

pub fn peak_rss_kib() -> Option<u64> {
    let status = fs::read_to_string("/proc/self/status").ok()?;
    status.lines().find(|l| l.starts_with("VmHWM:")).and_then(|l| l.split_whitespace().nth(1)).and_then(|v| v.parse().ok())
}

pub fn utc_stamp() -> String {
    let secs = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0);
    // civil date from the epoch (proleptic Gregorian), no external crate
    let days = secs / 86_400;
    let (h, m, s) = ((secs % 86_400) / 3600, (secs % 3600) / 60, secs % 60);
    let z = days as i64 + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z.rem_euclid(146_097);
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let mo = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = if mo <= 2 { y + 1 } else { y };
    format!("{y:04}{mo:02}{d:02}T{h:02}{m:02}{s:02}Z")
}

/// Write `bytes` durably: temp file in the same directory, fsync, rename over `path`, fsync the directory.
pub fn write_durable(path: &Path, bytes: &[u8]) -> Result<(), String> {
    let parent = path.parent().filter(|p| !p.as_os_str().is_empty()).unwrap_or(Path::new("."));
    fs::create_dir_all(parent).map_err(|e| format!("cannot create {}: {e}", parent.display()))?;
    let pending = path.with_extension(format!("{}.pending", path.extension().and_then(|e| e.to_str()).unwrap_or("tmp")));
    let _ = fs::remove_file(&pending);
    let mut f = OpenOptions::new().write(true).create_new(true).mode(0o600).open(&pending).map_err(|e| format!("cannot create {}: {e}", pending.display()))?;
    f.write_all(bytes).map_err(|e| format!("cannot write {}: {e}", pending.display()))?;
    f.sync_all().map_err(|e| format!("cannot fsync {}: {e}", pending.display()))?;
    drop(f);
    fs::rename(&pending, path).map_err(|e| format!("cannot commit {}: {e}", path.display()))?;
    File::open(parent).and_then(|d| d.sync_all()).map_err(|e| format!("cannot fsync directory {}: {e}", parent.display()))?;
    Ok(())
}

pub fn write_json_durable(path: &Path, value: &serde_json::Value) -> Result<(), String> {
    write_durable(path, serde_json::to_string_pretty(value).map_err(|e| e.to_string())?.as_bytes())
}

pub fn save_exact(proof: &SP1ProofWithPublicValues, output: &Path) -> Result<(u64, String), String> {
    let parent = output.parent().ok_or("output has no parent")?;
    fs::create_dir_all(parent).map_err(|e| format!("cannot create {}: {e}", parent.display()))?;
    let pending = output.with_extension("pending");
    let _ = fs::remove_file(&pending);
    let file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(&pending)
        .map_err(|e| format!("cannot create {}: {e}", pending.display()))?;
    let mut writer = BufWriter::new(file);
    bincode::DefaultOptions::new()
        .with_fixint_encoding()
        .reject_trailing_bytes()
        .serialize_into(&mut writer, proof)
        .map_err(|e| format!("cannot serialize proof: {e}"))?;
    writer.flush().map_err(|e| format!("cannot flush proof: {e}"))?;
    writer.get_ref().sync_all().map_err(|e| format!("cannot fsync proof: {e}"))?;
    drop(writer);
    let bytes = fs::read(&pending).map_err(|e| format!("cannot re-read proof: {e}"))?;
    if bytes.len() as u64 > MAX_PROOF_BYTES {
        return Err("proof artifact exceeds the size limit".into());
    }
    fs::rename(&pending, output).map_err(|e| format!("cannot commit proof: {e}"))?;
    File::open(parent).and_then(|d| d.sync_all()).map_err(|e| format!("cannot fsync directory: {e}"))?;
    Ok((bytes.len() as u64, sha256_hex(&bytes)))
}

pub fn load_exact(path: &Path) -> Result<(SP1ProofWithPublicValues, u64, String), String> {
    let bytes = fs::read(path).map_err(|e| format!("cannot read {}: {e}", path.display()))?;
    if bytes.len() as u64 > MAX_PROOF_BYTES {
        return Err("proof artifact exceeds the size limit".into());
    }
    let digest = sha256_hex(&bytes);
    let mut reader = BufReader::new(&bytes[..]);
    let proof: SP1ProofWithPublicValues = bincode::DefaultOptions::new()
        .with_fixint_encoding()
        .with_limit(bytes.len() as u64)
        .reject_trailing_bytes()
        .deserialize_from(&mut reader)
        .map_err(|e| format!("proof framing is not exact: {e}"))?;
    let mut trailing = [0u8; 1];
    if reader.read(&mut trailing).map_err(|e| format!("cannot test framing: {e}"))? != 0 {
        return Err("proof framing has trailing bytes".into());
    }
    Ok((proof, bytes.len() as u64, digest))
}

pub fn mutate_groth16_proof_byte(proof: &mut SP1ProofWithPublicValues) -> Result<(), String> {
    let SP1Proof::Groth16(groth16) = &mut proof.proof else {
        return Err("proof is not Groth16".into());
    };
    let mut encoded = groth16.encoded_proof.as_bytes().to_vec();
    if encoded.len() <= TAMPER_GROTH16_PROOF_BYTE {
        return Err("encoded proof too short to tamper".into());
    }
    let c = encoded[TAMPER_GROTH16_PROOF_BYTE];
    encoded[TAMPER_GROTH16_PROOF_BYTE] = if c == b'0' { b'1' } else { b'0' };
    groth16.encoded_proof = String::from_utf8(encoded).map_err(|_| "tampered proof is not UTF-8")?;
    Ok(())
}

/// Verify the proof with the SDK, then require that a flipped public byte, a flipped proof byte and a wrong
/// verification key are all rejected. Returns the three controls with the SDK's actual error text (Astra r5
/// finding 10 asks for mutation, expected stage and actual error on record).
pub fn verify_original_and_tamper<P: Prover>(client: &P, proof: &SP1ProofWithPublicValues, vkey: &sp1_sdk::SP1VerifyingKey) -> Result<Vec<serde_json::Value>, String> {
    client.verify(proof, vkey, None).map_err(|e| format!("proof does not verify: {e}"))?;
    let mut controls = Vec::new();
    let mut public_tampered = proof.clone();
    let mut bytes = public_tampered.public_values.to_vec();
    bytes[TAMPER_PUBLIC_BYTE] ^= 1;
    public_tampered.public_values = SP1PublicValues::from(&bytes);
    match client.verify(&public_tampered, vkey, None) {
        Ok(()) => return Err("a tampered public byte was accepted".into()),
        Err(e) => controls.push(serde_json::json!({"control": "sdk.public_byte_716", "layer": "relation", "mutation": format!("public byte {TAMPER_PUBLIC_BYTE} (R_correct) ^= 1"), "expected_failure_stage": "sdk verify (committed value digest differs)", "actual": format!("{e}"), "behaved_as_expected": true, "mutated_artefact_sha256": sha256_hex(&bytes)})),
    }
    let mut proof_tampered = proof.clone();
    mutate_groth16_proof_byte(&mut proof_tampered)?;
    match client.verify(&proof_tampered, vkey, None) {
        Ok(()) => return Err("a tampered proof byte was accepted".into()),
        Err(e) => controls.push(serde_json::json!({"control": "sdk.proof_nibble_96", "layer": "relation", "mutation": format!("groth16 encoded-proof hex nibble {TAMPER_GROTH16_PROOF_BYTE} flipped"), "expected_failure_stage": "sdk verify (pairing check fails)", "actual": format!("{e}"), "behaved_as_expected": true, "mutated_artefact_sha256": sha256_hex(proof_tampered.bytes().as_slice())})),
    }
    let mut wrong_vkey = vkey.clone();
    wrong_vkey.vk.preprocessed_commit.rotate_left(1);
    if wrong_vkey.bytes32() == vkey.bytes32() {
        return Err("wrong-verifying-key mutation did not change its hash".into());
    }
    match client.verify(proof, &wrong_vkey, None) {
        Ok(()) => return Err("a wrong verification key was accepted".into()),
        Err(e) => controls.push(serde_json::json!({"control": "sdk.wrong_vkey", "layer": "relation", "mutation": format!("verifying key preprocessed commitment rotated: {}", wrong_vkey.bytes32()), "expected_failure_stage": "sdk verify (vkey hash public input differs)", "actual": format!("{e}"), "behaved_as_expected": true, "mutated_artefact_sha256": sha256_hex(wrong_vkey.bytes32().as_bytes())})),
    }
    Ok(controls)
}

/// Everything a proof run produces, for receipts and manifests.
pub struct ProveRecord {
    pub row: u32,
    pub public: Vec<u8>,
    pub decoded: PublicOutput,
    pub sp1_version: String,
    pub vkey: String,
    pub groth16_vk_sha256: String,
    pub elf_sha256: String,
    pub elf_bytes: usize,
    pub raw_sha256: String,
    pub raw_blake3: String,
    pub constants_sha256: String,
    pub spec_sha256: String,
    pub noise_blake3: String,
    pub noise_sha256: String,
    pub proof_file: String,
    pub proof_bytes: u64,
    pub proof_sha256: String,
    pub proof_raw_file: String,
    pub proof_raw_bytes: usize,
    pub proof_raw_sha256: String,
    pub public_file: String,
    pub cycle_limit: u64,
    pub setup_ms: u128,
    pub prove_ms: u128,
    pub verify_ms: u128,
    pub accept_ms: u128,
    pub oracle_mode: String,
    pub oracle_notes: Vec<String>,
    pub sdk_tamper_controls: Vec<serde_json::Value>,
    pub acceptance: Option<serde_json::Value>,
    pub outcome_class: &'static str,
    pub host_peak_rss_kib: Option<u64>,
}

impl ProveRecord {
    pub fn manifest(&self, prover_name: &str) -> serde_json::Value {
        serde_json::json!({
            "schema": "zbdiff-ceremony/v2",
            "row": self.row,
            "wrong_row": self.decoded.row_u,
            "offset": self.decoded.offset,
            "offset_rule": if self.decoded.offset_rule == 1 { "mirrored" } else { "direct" },
            "denoiser_kind": self.decoded.denoiser_kind,
            "constants_sha256": self.constants_sha256,
            "spec_sha256": self.spec_sha256,
            "noise_blake3": self.noise_blake3,
            "noise_sha256": self.noise_sha256,
            "prover": prover_name,
            "sp1_version": self.sp1_version,
            "sp1_circuit_version_compiled": SP1_CIRCUIT_VERSION,
            "groth16_vk_sha256": self.groth16_vk_sha256,
            "guest_elf_sha256": self.elf_sha256,
            "guest_elf_bytes": self.elf_bytes,
            "sp1_vkey": self.vkey,
            "raw_frame_sha256": self.raw_sha256,
            "raw_frame_blake3": self.raw_blake3,
            "public_values_bytes": self.public.len(),
            "public_values_sha256": sha256_hex(&self.public),
            "public_values_hex": witness::hex(&self.public),
            "public_values_file": self.public_file,
            "r_correct": self.decoded.r_correct,
            "r_wrong": self.decoded.r_wrong,
            "difference": self.decoded.difference(),
            "difference_sign_positive": self.decoded.difference() > 0,
            "outcome_class": self.outcome_class,
            "clip_flag": u8::from(self.decoded.clip_events != 0),
            "clip_events": self.decoded.clip_events,
            "oracle_mode": self.oracle_mode,
            "oracle_notes": self.oracle_notes,
            "proof_file": self.proof_file,
            "proof_bytes": self.proof_bytes,
            "proof_sha256": self.proof_sha256,
            "proof_raw_bytes_file": self.proof_raw_file,
            "proof_raw_bytes": self.proof_raw_bytes,
            "proof_raw_bytes_sha256": self.proof_raw_sha256,
            "cycle_limit_requested": self.cycle_limit,
            "cycle_limit_note": "enforced by the CPU executor/prover; the pinned sp1-cuda 6.4.0 client does not forward it to the GPU server (Astra r5 finding 8)",
            "setup_elapsed_ms": self.setup_ms,
            "prove_elapsed_ms": self.prove_ms,
            "verify_and_tamper_elapsed_ms": self.verify_ms,
            "acceptance_elapsed_ms": self.accept_ms,
            "host_peak_rss_kib": self.host_peak_rss_kib,
            "host_peak_rss_note": "VmHWM of this client process only; the sp1-gpu-server and any executor runner are separate processes (sidecar)",
            "sdk_tamper_controls": self.sdk_tamper_controls,
            "acceptance": self.acceptance,
        })
    }
}

/// One Groth16 proof of one witness: setup, prove, mode and version asserted, oracle check, SDK verify + tamper
/// controls, acceptance under the frozen expected identities (when given), exact durable artifacts on disk. `setup`
/// may be reused across rows by passing the proving key.
pub fn prove_built<P: Prover>(
    client: &P,
    elf: Elf,
    proving_key: &P::ProvingKey,
    setup_ms: u128,
    built: &Built,
    network: &Network,
    out_dir: &Path,
    cycle_limit: u64,
    expected: Option<&Expected>,
) -> Result<ProveRecord, String> {
    let vkey = proving_key.verifying_key().bytes32();
    if let Some(exp) = expected {
        if exp.vkey() != vkey {
            return Err(format!("the proving key's vkey {vkey} differs from the expected {}; refusing to prove a statement the acceptance verifier would reject", exp.vkey()));
        }
    }
    let prove_started = Instant::now();
    let proof = client
        .prove(proving_key, built.stdin.clone())
        .groth16()
        .cycle_limit(cycle_limit)
        .with_proof_nonce([0, 0, 0, 0])
        .run()
        .map_err(|e| format!("SP1 Groth16 proof failed: {e}"))?;
    let prove_ms = prove_started.elapsed().as_millis();
    if !matches!(&proof.proof, SP1Proof::Groth16(_)) {
        return Err("SP1 returned a non-Groth16 proof".into());
    }
    if proof.sp1_version != SP1_CIRCUIT_VERSION {
        return Err("SP1 returned a proof under a different circuit version".into());
    }
    let public = proof.public_values.to_vec();
    if public.len() != PUBLIC_BYTES {
        return Err("public value length differs".into());
    }
    let report = witness::check(&public, built, network)?;
    let verify_started = Instant::now();
    let sdk_tamper_controls = verify_original_and_tamper(client, &proof, proving_key.verifying_key())?;
    let verify_ms = verify_started.elapsed().as_millis();
    let decoded = PublicOutput::parse(&public).map_err(|e| e.to_string())?;
    let raw_proof = proof.bytes();
    // acceptance under the frozen identities: a proof of the wrong statement is a failed row, never a success
    let accept_started = Instant::now();
    let acceptance = match expected {
        Some(exp) => {
            let a = accept::accept(&raw_proof, &public, exp);
            let j = a.json();
            if !a.ok() {
                return Err(format!("proof verified but the statement is not the expected one: {}", a.failed.clone().unwrap_or_default()));
            }
            Some(j)
        }
        None => None,
    };
    let accept_ms = accept_started.elapsed().as_millis();
    let stem = format!("row_{:06}", built.row);
    let out = out_dir.join(format!("{stem}_groth16.bin"));
    let (proof_bytes, proof_sha256) = save_exact(&proof, &out)?;
    let raw_file = out_dir.join(format!("{stem}_proof_bytes.bin"));
    write_durable(&raw_file, &raw_proof)?;
    let public_file = out_dir.join(format!("{stem}_public_values.bin"));
    write_durable(&public_file, &public)?;
    write_durable(&out_dir.join(format!("{stem}_public_values.hex")), format!("{}\n", witness::hex(&public)).as_bytes())?;
    Ok(ProveRecord {
        row: built.row,
        outcome_class: accept::outcome_class(decoded.difference()),
        noise_blake3: witness::hex(&decoded.noise_blake3),
        noise_sha256: sha256_hex(&built.witness.noise),
        raw_blake3: witness::hex(&decoded.raw_blake3_r),
        decoded,
        sp1_version: proof.sp1_version.clone(),
        vkey,
        groth16_vk_sha256: accept::embedded_groth16_vk_sha256(),
        elf_sha256: sha256_hex(&elf),
        elf_bytes: elf.len(),
        raw_sha256: sha256_hex(&built.witness.raw),
        constants_sha256: network.blob_sha256_hex(),
        spec_sha256: network.spec_sha256_hex(),
        proof_file: out.file_name().unwrap().to_string_lossy().to_string(),
        proof_bytes,
        proof_sha256,
        proof_raw_file: raw_file.file_name().unwrap().to_string_lossy().to_string(),
        proof_raw_bytes: raw_proof.len(),
        proof_raw_sha256: sha256_hex(&raw_proof),
        public_file: public_file.file_name().unwrap().to_string_lossy().to_string(),
        public,
        cycle_limit,
        setup_ms,
        prove_ms,
        verify_ms,
        accept_ms,
        oracle_mode: report.mode,
        oracle_notes: report.notes,
        sdk_tamper_controls,
        acceptance,
        host_peak_rss_kib: peak_rss_kib(),
    })
}
