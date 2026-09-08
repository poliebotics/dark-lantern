//! Batch driver for the declared proof set: one proof per held-out August row r in 600..711, every outcome
//! published including zero and negative differences, the declared wrong-row offset chosen by the declared rule of
//! 7 September 2026 (two parts; `armc_relation::rule`):
//!
//!   base   = OFFSETS[(r - 600) mod 5],  OFFSETS = [-2, +2, -15, +15, +30]
//!   offset = base                      if 0 <= r + base < 712        (offset_rule = direct)
//!          = -base                     otherwise                      (offset_rule = mirrored; the ten rows
//!            684, 689, 694, 699, 704, 709 (+30), 698, 703, 708 (+15) and 711 (+2) mirror to -30, -15, -2)
//!
//! `r`, `u`, `d` and the offset_rule flag (public byte 11) are public; the guest validates direct and mirrored offsets
//! together (`statement::check_offset_rule`), and the acceptance verifier (`accept.rs`, `zkdiff-verify`) enforces the
//! exact assignment above plus every other expected identity on every statement.
//!
//! For every row the driver rebuilds the session tree from the chain log, assembles the ten-item witness (header,
//! membership path of r, raw frame, beacon signature, previous record, wrong-row leaf and path, noise, offset,
//! offset_rule), checks every frame-independent leg natively (`prepare`), and then either executes the guest for the
//! instruction count and public bytes (`execute`) or runs the Groth16 ceremony with the tamper controls and the
//! acceptance verifier (`prove`). `controls` runs the negative controls of Astra r5 finding 10 (witness-level on the
//! final network natively; proof-level against a given artifact).
//!
//! Receipts (Astra r5 finding 9): one `row_XXXXXX/receipt.json` per row with the exact public bytes and their hash,
//! every decoded identity, both residuals, the signed difference and its outcome class, clip flag and count, the
//! proof bytes and hashes, ELF / vkey / circuit identity, the oracle comparison and every verification result, the
//! attempt identifier and the retained history of earlier attempts on the same row, every input hash, the exact
//! command, the build record and the expected-identities file. `BATCH_MANIFEST.json` is rewritten durably after every
//! row (recoverable progress) and carries `complete = true` only when every required row of this process is proved
//! AND accepted; the merger (`tools/merge_batch_manifests.py`) requires all 112 rows so.
//!
//! usage:
//!   zkdiff-batch prepare|execute|prove|controls --chain-log PATH --out DIR --blob PATH [--expect EXPECTED.json]
//!       [--rows 600..711] [--frames-dir DIR] [--noise-dir DIR] [--session-json PATH] [--build-record PATH]
//!       [--prover cpu|cuda] [--device N] [--cycle-limit N] [--frames-name frame_{r:06d}.raw] [--noise-name noise_{r:06d}.i16]
//!       [--row R] [--proof ARTIFACT.bin]            (controls: the row to mutate, default 600; the proof for proof-level controls)
//!
//! `--device N` (cuda) maps to `ProverClient::builder().cuda().with_device_id(N)`; run one process per GPU with
//! disjoint `--rows` ranges and separate `--out` directories, then merge the manifests. `prove` REQUIRES `--expect`.
//! Rows whose frame or noise file is absent are recorded as `pending_frame` / `pending_noise` after their
//! frame-independent checks. The `--cycle-limit` is enforced by the CPU executor and prover only; the pinned
//! `sp1-cuda` client does not forward it (Astra r5 finding 8), so it is recorded as requested metadata.
#![recursion_limit = "512"]
#![allow(dead_code)]

mod accept;
mod ceremony_core;
mod session;
mod witness;

use std::path::{Path, PathBuf};
use std::time::Instant;

use accept::{accept_public, Expected};
use armc_relation::net::Denoiser;
use armc_relation::rule::{self, AUGUST_RULE_ROW_END_INCLUSIVE, AUGUST_RULE_ROW_START, RULE_TEXT};
use armc_relation::statement::{evaluate, PublicOutput, Witness, OFFSETS, OFFSET_RULE_DIRECT, OFFSET_RULE_MIRRORED};
use ceremony_core::{sha256_hex, utc_stamp, write_json_durable, DEFAULT_CYCLE_LIMIT};
use session::{Session, SessionProfile};
use sp1_sdk::{
    blocking::{Prover, ProverClient},
    include_elf, Elf, HashableKey, ProvingKey, SP1_CIRCUIT_VERSION,
};

const ZKDIFF_ELF: Elf = include_elf!("zkdiff-guest");
const MANIFEST_SCHEMA: &str = "zbdiff-batch/v3";
const RECEIPT_SCHEMA: &str = "zbdiff-row-receipt/v3";

/// The declared rule, as constants (the definition lives in `armc_relation::rule`).
pub const RULE_ROW_START: u32 = AUGUST_RULE_ROW_START;
pub const RULE_ROW_END_INCLUSIVE: u32 = AUGUST_RULE_ROW_END_INCLUSIVE;

fn usage() -> ! {
    eprintln!(
        "usage: zkdiff-batch prepare|execute|prove|controls --chain-log PATH --out DIR --blob PATH [--expect EXPECTED.json] [--rows 600..711] [--frames-dir DIR] [--noise-dir DIR] [--session-json PATH] [--build-record PATH] [--prover cpu|cuda] [--device N] [--cycle-limit N] [--frames-name frame_{{r:06d}}.raw] [--noise-name noise_{{r:06d}}.i16] [--row R] [--proof ARTIFACT.bin]"
    );
    std::process::exit(2);
}

fn parse_rows(spec: &str) -> (u32, u32) {
    let (a, b) = spec.split_once("..").unwrap_or_else(|| usage());
    (a.parse().unwrap_or_else(|_| usage()), b.parse().unwrap_or_else(|_| usage()))
}

fn file_name(pattern: &str, r: u32) -> String {
    pattern.replace("{r:06d}", &format!("{r:06}"))
}

fn hostname() -> String {
    std::fs::read_to_string("/proc/sys/kernel/hostname").map(|s| s.trim().to_string()).unwrap_or_default()
}

fn self_sha256() -> String {
    std::fs::read("/proc/self/exe").map(|b| sha256_hex(&b)).unwrap_or_default()
}

fn file_identity(path: &Path) -> serde_json::Value {
    match std::fs::read(path) {
        Ok(b) => serde_json::json!({"path": path.display().to_string(), "bytes": b.len(), "sha256": sha256_hex(&b)}),
        Err(e) => serde_json::json!({"path": path.display().to_string(), "error": e.to_string()}),
    }
}

/// Every decoded identity of a public statement, for the receipt.
fn decoded_json(p: &PublicOutput) -> serde_json::Value {
    let h = armc_relation::header::hex;
    serde_json::json!({
        "denoiser_kind": p.denoiser_kind,
        "offset_rule": if p.offset_rule == OFFSET_RULE_MIRRORED { "mirrored" } else { "direct" },
        "public_offset_rule_byte": p.offset_rule,
        "row": p.row_r, "wrong_row": p.row_u, "offset": p.offset,
        "row_count": p.row_count, "tree_depth": p.tree_depth,
        "session_id": String::from_utf8_lossy(&p.session_id),
        "s_0": h(&p.s_0), "s_n": h(&p.s_n), "authority_manifest_sha256": h(&p.authority_manifest_sha256), "chain_log_blake3": h(&p.chain_log_blake3),
        "context_digest": h(&p.context_digest), "ordered_session_root": h(&p.ordered_session_root),
        "leaf_r": h(&p.leaf_r), "leaf_u": h(&p.leaf_u),
        "raw_blake3": h(&p.raw_blake3_r), "emission_blake3_r": h(&p.emission_blake3_r), "emission_blake3_u": h(&p.emission_blake3_u),
        "prev_drand_round": p.prev_drand_round, "own_drand_round": p.own_drand_round, "drand_leg_digest": h(&p.drand_leg_digest),
        "constants_sha256": h(&p.constants_sha256), "spec_sha256": h(&p.spec_sha256), "preprocess_spec_sha256": h(&p.preprocess_spec_sha256),
        "noise_blake3": h(&p.noise_blake3),
        "r_correct": p.r_correct, "r_wrong": p.r_wrong, "difference": p.difference(),
        "difference_sign_positive": p.difference() > 0, "outcome_class": accept::outcome_class(p.difference()),
        "clip_flag": u8::from(p.clip_events != 0), "clip_events": p.clip_events, "clip_events_saturated": p.clip_events == u16::MAX,
    })
}

/// The retained history of earlier attempts on a row: read the existing receipt (if any) and keep its summary.
fn previous_attempts(receipt_path: &Path) -> Vec<serde_json::Value> {
    let Ok(text) = std::fs::read_to_string(receipt_path) else { return Vec::new() };
    let Ok(old) = serde_json::from_str::<serde_json::Value>(&text) else {
        return vec![serde_json::json!({"attempt_id": "unparseable earlier receipt", "receipt_sha256": sha256_hex(text.as_bytes())})];
    };
    let mut attempts: Vec<serde_json::Value> = old["attempts"].as_array().cloned().unwrap_or_default();
    attempts.push(serde_json::json!({
        "attempt_id": old["attempt_id"], "attempt_started_utc": old["attempt_started_utc"], "status": old["status"], "error": old["error"],
        "elapsed_ms": old["elapsed_ms"], "public_values_sha256": old["public_values_sha256"], "proof_sha256": old["proof_sha256"],
        "outcome_class": old["outcome_class"], "receipt_sha256": sha256_hex(text.as_bytes()),
    }));
    attempts
}

struct Common {
    mode: String,
    args: Vec<String>,
    attempt_id: String,
    started_utc: String,
    build_record: Option<serde_json::Value>,
    expected: Option<Expected>,
    elf_sha256: String,
}

fn main() {
    sp1_sdk::utils::setup_logger();
    let args: Vec<String> = std::env::args().skip(1).collect();
    let Some(mode) = args.first().cloned() else { usage() };
    if !["prepare", "execute", "prove", "controls"].contains(&mode.as_str()) {
        usage();
    }
    let chain_log = PathBuf::from(witness::arg(&args, "--chain-log").unwrap_or_else(|| usage()));
    let out_dir = PathBuf::from(witness::arg(&args, "--out").unwrap_or_else(|| usage()));
    let blob_path = PathBuf::from(witness::arg(&args, "--blob").unwrap_or_else(|| usage()));
    let (row_start, row_end) = parse_rows(&witness::arg(&args, "--rows").unwrap_or_else(|| format!("{RULE_ROW_START}..{RULE_ROW_END_INCLUSIVE}")));
    let frames_dir = witness::arg(&args, "--frames-dir").map(PathBuf::from);
    let noise_dir = witness::arg(&args, "--noise-dir").map(PathBuf::from);
    let frames_name = witness::arg(&args, "--frames-name").unwrap_or_else(|| "frame_{r:06d}.raw".into());
    let noise_name = witness::arg(&args, "--noise-name").unwrap_or_else(|| "noise_{r:06d}.i16".into());
    let prover = witness::arg(&args, "--prover").unwrap_or_else(|| "cpu".into());
    let device: u32 = witness::arg(&args, "--device").map(|v| v.parse().expect("cuda device id")).unwrap_or(0);
    let cycle_limit: u64 = witness::arg(&args, "--cycle-limit").map(|v| v.parse().expect("cycle limit")).unwrap_or(DEFAULT_CYCLE_LIMIT);
    let profile = match witness::arg(&args, "--session-json") {
        Some(p) => SessionProfile::from_json(Path::new(&p)).unwrap_or_else(|e| panic!("session profile: {e}")),
        None => SessionProfile::august(),
    };
    let expected = witness::arg(&args, "--expect").map(|p| Expected::load(Path::new(&p)).unwrap_or_else(|e| panic!("{e}")));
    if mode == "prove" && expected.is_none() {
        panic!("prove requires --expect EXPECTED.json: a proof is accepted only against the frozen identities");
    }
    let build_record = witness::arg(&args, "--build-record").map(|p| file_identity(Path::new(&p)));
    let common = Common {
        mode: mode.clone(),
        args: std::env::args().collect(),
        attempt_id: format!("{}-{}-{}", utc_stamp(), hostname(), std::process::id()),
        started_utc: utc_stamp(),
        build_record,
        expected,
        elf_sha256: sha256_hex(&ZKDIFF_ELF),
    };

    let started = Instant::now();
    let network = witness::Network::load(&blob_path);
    let log_bytes = std::fs::read(&chain_log).unwrap_or_else(|e| panic!("cannot read chain log: {e}"));
    let session = Session::load(profile, &log_bytes).unwrap_or_else(|e| panic!("session: {e}"));
    std::fs::create_dir_all(&out_dir).expect("out dir");
    println!("mode={mode} attempt_id={} session={} rows={row_start}..{row_end} rule=\"{RULE_TEXT}\"", common.attempt_id, session.profile.name);
    println!("guest_elf_bytes={} guest_elf_sha256={} sp1_circuit_version={SP1_CIRCUIT_VERSION} groth16_vk_sha256={}", ZKDIFF_ELF.len(), common.elf_sha256, accept::embedded_groth16_vk_sha256());
    println!("constants_blob={} constants_blob_bytes={} constants_sha256={} spec_sha256={}", blob_path.display(), network.blob.len(), network.blob_sha256_hex(), network.spec_sha256_hex());
    println!("ordered_session_root={}", armc_relation::header::hex(&session.root));
    println!("expected_identities={}", common.expected.as_ref().map(|e| format!("{} sha256 {}", e.path, e.sha256)).unwrap_or_else(|| "none".into()));
    if let Some(exp) = &common.expected {
        // the frozen identities must describe THIS build and THIS blob, or nothing this process produces can be accepted
        assert_eq!(exp.str("guest_elf_sha256"), common.elf_sha256, "expected guest_elf_sha256 differs from the embedded ELF");
        assert_eq!(exp.str("constants_sha256"), network.blob_sha256_hex(), "expected constants_sha256 differs from --blob");
        assert_eq!(exp.str("spec_sha256"), network.spec_sha256_hex(), "expected spec_sha256 differs from the adapter's");
        assert_eq!(exp.str("groth16_vk_sha256"), accept::embedded_groth16_vk_sha256(), "expected circuit key differs from the embedded sp1-verifier key");
        assert_eq!(exp.str("sp1_circuit_version"), SP1_CIRCUIT_VERSION, "expected circuit version differs from this host's");
        assert_eq!(exp.json["session"]["ordered_session_root"].as_str().unwrap_or(""), armc_relation::header::hex(&session.root), "expected session root differs from the rebuilt tree");
    }
    if prover == "cuda" {
        println!("cuda_device_id={device}");
    }

    if mode == "controls" {
        let row: u32 = witness::arg(&args, "--row").map(|v| v.parse().expect("row")).unwrap_or(600);
        let proof = witness::arg(&args, "--proof").map(PathBuf::from);
        let ok = run_controls(&common, &session, &network, &blob_path, &out_dir, row, frames_dir.as_deref(), noise_dir.as_deref(), &frames_name, &noise_name, proof.as_deref());
        std::process::exit(if ok { 0 } else { 1 });
    }

    let client = ProverClient::builder().cpu().build();
    #[cfg(feature = "cuda")]
    let cuda_client = if prover == "cuda" { Some(ProverClient::builder().cuda().with_device_id(device).build()) } else { None };
    #[cfg(not(feature = "cuda"))]
    if prover == "cuda" {
        panic!("built without the cuda feature");
    }
    // one setup per batch process (about 22 s on the proved row); the key is the same for every row
    let (proving_key, setup_ms, vkey) = if mode == "prove" {
        let t = Instant::now();
        let pk = client.setup(ZKDIFF_ELF).expect("SP1 setup");
        let vk = pk.verifying_key().bytes32();
        println!("sp1_vkey={vk} setup_elapsed_ms={}", t.elapsed().as_millis());
        if let Some(exp) = &common.expected {
            assert_eq!(exp.vkey(), vk, "expected sp1_vkey differs from the key derived from the embedded ELF");
        }
        (Some(pk), t.elapsed().as_millis(), Some(vk))
    } else {
        (None, 0, None)
    };
    #[cfg(feature = "cuda")]
    let cuda_key = match (&cuda_client, mode.as_str()) {
        (Some(c), "prove") => {
            let t = Instant::now();
            let k = c.setup(ZKDIFF_ELF).expect("SP1 cuda setup");
            let vk = k.verifying_key().bytes32();
            if let Some(cpu_vk) = &vkey {
                assert_eq!(&vk, cpu_vk, "cuda and cpu verifying keys differ");
            }
            println!("cuda_setup_elapsed_ms={}", t.elapsed().as_millis());
            Some(k)
        }
        _ => None,
    };

    let mut entries = Vec::new();
    let mut counts: std::collections::BTreeMap<String, u32> = Default::default();
    let mut outcome_counts: std::collections::BTreeMap<String, u32> = Default::default();
    let mut mirrored_rows: Vec<u32> = Vec::new();
    let mut failed_attempts_retained = 0_u64;
    // `--rows` only bounds the rows this process handles; the offset rule is anchored at RULE_ROW_START for every
    // process, so eight processes with disjoint ranges assign exactly the same offsets as one process would.
    let rule_start = if session.profile.name == "august_dev_712" { RULE_ROW_START } else { row_start };
    let required: Vec<u32> = (row_start..=row_end).collect();
    let prover_name = if prover == "cuda" { format!("local_cuda_explicit_device{device}") } else { "local_cpu_explicit".to_string() };
    let manifest_path = out_dir.join("BATCH_MANIFEST.json");
    let write_manifest = |entries: &Vec<serde_json::Value>, counts: &std::collections::BTreeMap<String, u32>, outcome_counts: &std::collections::BTreeMap<String, u32>, mirrored_rows: &Vec<u32>, failed_attempts_retained: u64, finished: bool| {
        let done_ok = entries.iter().filter(|e| if mode == "prove" { e["status"] == "proved" && e["acceptance"]["accepted"] == true } else { e["status"] == "executed" || e["status"] == "prepared_native" }).count();
        let complete = mode == "prove" && finished && done_ok == required.len() && entries.len() == required.len();
        let manifest = serde_json::json!({
            "schema": MANIFEST_SCHEMA,
            "mode": mode,
            "attempt_id": common.attempt_id,
            "started_utc": common.started_utc,
            "written_utc": utc_stamp(),
            "host": hostname(),
            "command": common.args,
            "binary_sha256": self_sha256(),
            "build_record": common.build_record,
            "expected_identities": common.expected.as_ref().map(|e| serde_json::json!({"path": e.path, "sha256": e.sha256})),
            "progress_note": "rewritten durably after every row; `complete` is true only when every required row is proved and accepted by the acceptance verifier",
            "rule": {
                "text": RULE_TEXT,
                "row_start": rule_start,
                "rows_processed": format!("{row_start}..{row_end}"),
                "offsets": OFFSETS,
                "offset_formula": "base = OFFSETS[(r - row_start) mod 5]; offset = base if 0 <= r + base < row_count else -base (offset_rule = mirrored)",
                "public_check": "r (16..20), u (20..24), d (24..28) and the offset_rule byte (11) are public; the guest validates direct and mirrored offsets together (-30 only under the mirror flag and only when r + 30 leaves the session); the acceptance verifier enforces the exact assignment",
                "mirrored_rows_in_this_run": mirrored_rows,
                "rule_constants_row_start": RULE_ROW_START,
                "rule_constants_row_end_inclusive": RULE_ROW_END_INCLUSIVE,
            },
            "session": {
                "name": session.profile.name,
                "session_id": String::from_utf8_lossy(&session.profile.session_id),
                "row_count": session.profile.row_count,
                "chain_log": chain_log.display().to_string(),
                "chain_log_blake3": armc_relation::header::hex(&session.profile.chain_log_blake3),
                "context_digest": armc_relation::header::hex(&session.context),
                "ordered_session_root": armc_relation::header::hex(&session.root),
            },
            "guest_elf_bytes": ZKDIFF_ELF.len(),
            "guest_elf_sha256": common.elf_sha256,
            "sp1_vkey": vkey,
            "sp1_circuit_version": SP1_CIRCUIT_VERSION,
            "groth16_vk_sha256": accept::embedded_groth16_vk_sha256(),
            "prover": prover,
            "prover_name": prover_name,
            "cuda_device_id": if prover == "cuda" { Some(device) } else { None },
            "cycle_limit_requested": cycle_limit,
            "cycle_limit_note": "enforced by the CPU executor/prover only; not forwarded by the pinned sp1-cuda client (Astra r5 finding 8)",
            "denoiser": {
                "kind": network.net.kind(),
                "name": "armc-int int16 (zkdiff-armc-adapter over armc_int::Constants)",
                "constants_blob": blob_path.display().to_string(),
                "constants_blob_bytes": network.blob.len(),
                "constants_sha256": network.blob_sha256_hex(),
                "spec_sha256": network.spec_sha256_hex(),
            },
            "noise": {
                "dir": noise_dir.as_ref().map(|p| p.display().to_string()),
                "file_pattern": noise_name,
                "rule": "normative noise_int bytes exported from g1_integer/final/august_inputs (G1 FINAL, README_FINAL.md section 5); per-row sha256 and BLAKE3 in the receipts, BLAKE3 public at offset 660 and checked against the frozen table by the acceptance verifier",
            },
            "frames": { "dir": frames_dir.as_ref().map(|p| p.display().to_string()), "file_pattern": frames_name },
            "preprocess_spec_sha256": armc_relation::header::hex(&armc_relation::spec::preprocess_spec_sha256()),
            "required_rows": required,
            "rows_required": required.len(),
            "rows_recorded": entries.len(),
            "rows_done_ok": done_ok,
            "complete": complete,
            "finished": finished,
            "status_counts": counts,
            "outcome_counts": outcome_counts,
            "failed_attempts_retained": failed_attempts_retained,
            "rows": entries,
            "elapsed_ms": started.elapsed().as_millis(),
        });
        write_json_durable(&manifest_path, &manifest).expect("manifest");
    };
    write_manifest(&entries, &counts, &outcome_counts, &mirrored_rows, failed_attempts_retained, false);

    for r in row_start..=row_end {
        if r < rule_start {
            panic!("row {r} lies before the rule's first row {rule_start}");
        }
        let base = rule::base_offset(r, rule_start).expect("row >= rule start");
        let row_dir = out_dir.join(format!("row_{r:06}"));
        let witness_dir = row_dir.join("witness");
        let receipt_path = row_dir.join("receipt.json");
        let attempts = previous_attempts(&receipt_path);
        // earlier attempts that ended in failure (a pending_frame attempt is not a failure, it is an unfinished row)
        failed_attempts_retained += attempts.iter().filter(|a| a["status"] == "failed" || a["status"] == "unknown" || a["status"].is_null()).count() as u64;
        let t_row = Instant::now();
        let mut entry = serde_json::json!({
            "schema": RECEIPT_SCHEMA, "row": r, "base_offset": base, "status": "unknown",
            "attempt_id": common.attempt_id, "attempt_started_utc": utc_stamp(), "attempts": attempts,
            "mode": mode, "host": hostname(), "command": common.args, "binary_sha256": self_sha256(),
            "build_record": common.build_record, "expected_identities": common.expected.as_ref().map(|e| serde_json::json!({"path": e.path, "sha256": e.sha256})),
            "guest_elf_sha256": common.elf_sha256, "guest_elf_bytes": ZKDIFF_ELF.len(), "sp1_circuit_version": SP1_CIRCUIT_VERSION, "groth16_vk_sha256": accept::embedded_groth16_vk_sha256(),
            "constants_sha256": network.blob_sha256_hex(), "spec_sha256": network.spec_sha256_hex(), "chain_log_blake3": armc_relation::header::hex(&session.profile.chain_log_blake3),
        });
        let mut status = String::new();
        let mut notes: Vec<String> = Vec::new();

        let Some(a) = rule::assignment(r, rule_start, session.profile.row_count) else {
            // neither the direct nor the mirrored wrong row is inside the session (cannot happen for 600..711 with
            // 712 rows; kept so the driver fails closed on another session)
            entry["status"] = serde_json::json!("out_of_range_by_rule");
            entry["offset"] = serde_json::json!(base);
            entry["notes"] = serde_json::json!([format!("neither r + base nor r - base lies inside 0..{}", session.profile.row_count)]);
            entry["elapsed_ms"] = serde_json::json!(t_row.elapsed().as_millis());
            std::fs::create_dir_all(&row_dir).expect("row dir");
            write_json_durable(&receipt_path, &entry).expect("receipt");
            println!("row={r} base={base:+} status=out_of_range_by_rule");
            *counts.entry("out_of_range_by_rule".into()).or_default() += 1;
            entries.push(entry);
            write_manifest(&entries, &counts, &outcome_counts, &mirrored_rows, failed_attempts_retained, false);
            continue;
        };
        let (d, mirrored, u) = (a.offset, a.mirrored, a.wrong_row);
        entry["offset"] = serde_json::json!(d);
        entry["wrong_row"] = serde_json::json!(u);
        entry["offset_rule"] = serde_json::json!(if mirrored { "mirrored" } else { "direct" });
        if mirrored {
            mirrored_rows.push(r);
            notes.push(format!("offset mirrored: r + base = {} lies outside 0..{}, so offset = {d:+}", r as i64 + base as i64, session.profile.row_count));
        }

        let outcome: Result<(), String> = (|| {
            let prep = session.prepare_checks(r, d)?;
            notes.extend(prep);
            let frame_path = frames_dir.as_ref().map(|dir| dir.join(file_name(&frames_name, r)));
            let noise_path = noise_dir.as_ref().map(|dir| dir.join(file_name(&noise_name, r)));
            let raw = match &frame_path {
                Some(p) if p.is_file() => std::fs::read(p).map_err(|e| e.to_string())?,
                _ => Vec::new(),
            };
            let noise = match &noise_path {
                Some(p) if p.is_file() => std::fs::read(p).map_err(|e| e.to_string())?,
                _ => Vec::new(),
            };
            let w = session.assemble(r, d, mirrored, raw, noise)?;
            Session::write_witness_files(&witness_dir, &w)?;
            entry["witness_dir"] = serde_json::json!(witness_dir.display().to_string());
            entry["frame"] = serde_json::json!(frame_path.as_ref().map(|p| p.display().to_string()));
            entry["noise"] = serde_json::json!(noise_path.as_ref().map(|p| p.display().to_string()));
            entry["leaf_r"] = serde_json::json!(armc_relation::header::hex(&session.leaves[r as usize]));
            entry["leaf_u"] = serde_json::json!(armc_relation::header::hex(&session.leaves[u as usize]));
            entry["raw_blake3_expected"] = serde_json::json!(armc_relation::header::hex(&session.log.rows[r as usize].bayer_blake3));
            if !w.noise.is_empty() {
                entry["noise_sha256"] = serde_json::json!(sha256_hex(&w.noise));
                entry["noise_blake3"] = serde_json::json!(armc_relation::header::hex(&armc_relation::b3xof::blake3p::hash(&w.noise)));
                if let Some(exp) = &common.expected {
                    // the noise file at hand must be the frozen normative one BEFORE anything is executed or proved
                    let want = exp.row(r).and_then(|row| row["noise_blake3"].as_str()).ok_or_else(|| format!("expected identities carry no noise BLAKE3 for row {r}"))?;
                    let have = armc_relation::header::hex(&armc_relation::b3xof::blake3p::hash(&w.noise));
                    if want != have {
                        return Err(format!("noise file {} has BLAKE3 {have}, the frozen normative table says {want}", noise_path.as_ref().map(|p| p.display().to_string()).unwrap_or_default()));
                    }
                    notes.push("noise BLAKE3 equals the frozen normative table entry".into());
                }
            }
            if w.raw.is_empty() {
                status = "pending_frame".into();
                return Ok(());
            }
            if armc_relation::b3xof::blake3p::hash(&w.raw) != session.log.rows[r as usize].bayer_blake3 {
                return Err("frame BLAKE3 differs from the chain log's bayer digest".into());
            }
            entry["raw_sha256"] = serde_json::json!(sha256_hex(&w.raw));
            entry["raw_blake3"] = serde_json::json!(armc_relation::header::hex(&armc_relation::b3xof::blake3p::hash(&w.raw)));
            if w.noise.is_empty() {
                status = "pending_noise".into();
                return Ok(());
            }
            let decode = |entry: &mut serde_json::Value, public: &[u8], p: &PublicOutput| {
                entry["public_values_hex"] = serde_json::json!(witness::hex(public));
                entry["public_values_sha256"] = serde_json::json!(sha256_hex(public));
                entry["public_values_bytes"] = serde_json::json!(public.len());
                entry["decoded"] = decoded_json(p);
                entry["r_correct"] = serde_json::json!(p.r_correct);
                entry["r_wrong"] = serde_json::json!(p.r_wrong);
                entry["difference"] = serde_json::json!(p.difference());
                entry["difference_sign_positive"] = serde_json::json!(p.difference() > 0);
                entry["outcome_class"] = serde_json::json!(accept::outcome_class(p.difference()));
                entry["denoiser_kind"] = serde_json::json!(p.denoiser_kind);
                entry["public_offset_rule_byte"] = serde_json::json!(p.offset_rule);
                entry["clip_flag"] = serde_json::json!(u8::from(p.clip_events != 0));
                entry["clip_events"] = serde_json::json!(p.clip_events);
                entry["constants_sha256"] = serde_json::json!(armc_relation::header::hex(&p.constants_sha256));
                entry["public_noise_blake3"] = serde_json::json!(armc_relation::header::hex(&p.noise_blake3));
            };
            if mode == "prepare" {
                let public = evaluate(&w, &network.net).map_err(|e| e.to_string())?;
                let p = PublicOutput::parse(&public).map_err(|e| e.to_string())?;
                ceremony_core::write_durable(&row_dir.join("native_public_values.hex"), format!("{}\n", witness::hex(&public)).as_bytes())?;
                decode(&mut entry, &public, &p);
                if let Some(exp) = &common.expected {
                    let acc = accept_public(&public, exp);
                    entry["acceptance"] = acc.json();
                    if !acc.ok() {
                        return Err(format!("native statement is not the expected one: {}", acc.failed.unwrap_or_default()));
                    }
                }
                status = "prepared_native".into();
                return Ok(());
            }
            let built = witness::Built { stdin: witness::stdin_of(&w, &network.blob), row: r, witness: w, expected_python: None };
            if mode == "execute" {
                let (output, report) = client.execute(ZKDIFF_ELF, built.stdin.clone()).run().map_err(|e| format!("SP1 execute failed: {e}"))?;
                let public = output.as_slice().to_vec();
                let oracle = witness::check(&public, &built, &network)?;
                let p = PublicOutput::parse(&public).map_err(|e| e.to_string())?;
                ceremony_core::write_durable(&row_dir.join("public_values.hex"), format!("{}\n", witness::hex(&public)).as_bytes())?;
                ceremony_core::write_durable(&row_dir.join("public_values.bin"), &public)?;
                decode(&mut entry, &public, &p);
                entry["total_instruction_count"] = serde_json::json!(report.total_instruction_count());
                entry["total_syscall_count"] = serde_json::json!(report.total_syscall_count());
                let mut regions: Vec<(String, u64)> = report.cycle_tracker.iter().map(|(k, v)| (k.clone(), *v)).collect();
                regions.sort_by(|a, b| b.1.cmp(&a.1));
                entry["cycle_regions"] = serde_json::json!(regions);
                entry["oracle_mode"] = serde_json::json!(oracle.mode);
                entry["host_peak_rss_kib"] = serde_json::json!(ceremony_core::peak_rss_kib());
                notes.extend(oracle.notes);
                if let Some(exp) = &common.expected {
                    let acc = accept_public(&public, exp);
                    entry["acceptance"] = acc.json();
                    if !acc.ok() {
                        return Err(format!("executed statement is not the expected one: {}", acc.failed.unwrap_or_default()));
                    }
                }
                status = "executed".into();
                return Ok(());
            }
            // prove
            let pk = proving_key.as_ref().unwrap();
            let exp = common.expected.as_ref();
            let record = {
                #[cfg(feature = "cuda")]
                {
                    match (&cuda_client, &cuda_key) {
                        (Some(c), Some(ck)) => ceremony_core::prove_built(c, ZKDIFF_ELF, ck, setup_ms, &built, &network, &row_dir, cycle_limit, exp)?,
                        _ => ceremony_core::prove_built(&client, ZKDIFF_ELF, pk, setup_ms, &built, &network, &row_dir, cycle_limit, exp)?,
                    }
                }
                #[cfg(not(feature = "cuda"))]
                {
                    ceremony_core::prove_built(&client, ZKDIFF_ELF, pk, setup_ms, &built, &network, &row_dir, cycle_limit, exp)?
                }
            };
            let manifest = record.manifest(&prover_name);
            write_json_durable(&row_dir.join("manifest.json"), &manifest)?;
            decode(&mut entry, &record.public, &record.decoded);
            entry["proof_file"] = serde_json::json!(row_dir.join(&record.proof_file).display().to_string());
            entry["proof_bytes"] = serde_json::json!(record.proof_bytes);
            entry["proof_sha256"] = serde_json::json!(record.proof_sha256);
            entry["proof_raw_bytes_file"] = serde_json::json!(row_dir.join(&record.proof_raw_file).display().to_string());
            entry["proof_raw_bytes"] = serde_json::json!(record.proof_raw_bytes);
            entry["proof_raw_bytes_sha256"] = serde_json::json!(record.proof_raw_sha256);
            entry["public_values_file"] = serde_json::json!(row_dir.join(&record.public_file).display().to_string());
            entry["sp1_vkey"] = serde_json::json!(record.vkey);
            entry["sp1_version"] = serde_json::json!(record.sp1_version);
            entry["prover"] = serde_json::json!(prover_name);
            entry["cycle_limit_requested"] = serde_json::json!(cycle_limit);
            entry["setup_elapsed_ms"] = serde_json::json!(record.setup_ms);
            entry["prove_elapsed_ms"] = serde_json::json!(record.prove_ms);
            entry["verify_and_tamper_elapsed_ms"] = serde_json::json!(record.verify_ms);
            entry["acceptance_elapsed_ms"] = serde_json::json!(record.accept_ms);
            entry["host_peak_rss_kib"] = serde_json::json!(record.host_peak_rss_kib);
            entry["oracle_mode"] = serde_json::json!(record.oracle_mode);
            entry["verification"] = serde_json::json!({
                "sdk_verify": true, "sdk_tamper_controls": record.sdk_tamper_controls,
                "acceptance_verifier": "accept::accept (standalone sp1-verifier under the pinned program vkey and circuit key, then every expected identity)",
            });
            entry["acceptance"] = record.acceptance.clone().unwrap_or(serde_json::json!({"accepted": false, "failed_check": "acceptance not run"}));
            notes.extend(record.oracle_notes);
            status = "proved".into();
            Ok(())
        })();
        if let Err(e) = outcome {
            status = "failed".into();
            entry["error"] = serde_json::json!(e);
        }
        entry["status"] = serde_json::json!(status);
        entry["notes"] = serde_json::json!(notes);
        entry["elapsed_ms"] = serde_json::json!(t_row.elapsed().as_millis());
        std::fs::create_dir_all(&row_dir).expect("row dir");
        write_json_durable(&receipt_path, &entry).expect("receipt");
        println!(
            "row={r} offset={d:+} rule={} wrong={u} status={status} outcome={} elapsed_ms={}",
            if mirrored { "mirrored" } else { "direct" },
            entry["outcome_class"].as_str().unwrap_or("n/a"),
            t_row.elapsed().as_millis()
        );
        *counts.entry(status.clone()).or_default() += 1;
        if let Some(c) = entry["outcome_class"].as_str() {
            *outcome_counts.entry(c.to_string()).or_default() += 1;
        }
        entries.push(entry);
        write_manifest(&entries, &counts, &outcome_counts, &mirrored_rows, failed_attempts_retained, false);
    }
    write_manifest(&entries, &counts, &outcome_counts, &mirrored_rows, failed_attempts_retained, true);
    println!("batch_manifest={}", manifest_path.display());
    let manifest: serde_json::Value = serde_json::from_str(&std::fs::read_to_string(&manifest_path).unwrap()).unwrap();
    println!("complete={} rows_done_ok={} rows_required={} status_counts={} outcome_counts={}", manifest["complete"], manifest["rows_done_ok"], manifest["rows_required"], manifest["status_counts"], manifest["outcome_counts"]);
}

// ------------------------------------------------------------------ negative controls (Astra r5 finding 10)

struct WitnessControl {
    name: &'static str,
    layer: &'static str,
    mutation: String,
    expected_stage: String,
    witness: Result<(Witness, Option<Vec<u8>>), String>, // (witness, replacement blob)
}

/// Run one witness-level control natively with the final network: relation rejection (evaluate refuses, message
/// recorded), policy rejection (evaluate accepts a different statement, the acceptance verifier refuses at the
/// named check) or acceptance.
fn run_witness_control(c: &WitnessControl, network: &witness::Network, exp: Option<&Expected>) -> serde_json::Value {
    let (w, blob) = match &c.witness {
        Ok(x) => x,
        Err(e) => {
            return serde_json::json!({"control": c.name, "layer_expected": c.layer, "mutation": c.mutation, "expected_failure_stage": c.expected_stage, "actual": format!("control not runnable here: {e}"), "behaved_as_expected": null, "pending": true});
        }
    };
    let ident = serde_json::json!({
        "header_sha256": sha256_hex(&w.header), "membership_sha256": sha256_hex(&w.membership), "raw_sha256": sha256_hex(&w.raw), "signature_sha256": sha256_hex(&w.signature),
        "previous_sha256": sha256_hex(&w.previous), "leaf_u_sha256": sha256_hex(&w.leaf_u), "siblings_u_sha256": sha256_hex(&w.siblings_u), "noise_sha256": sha256_hex(&w.noise),
        "offset": i32::from_le_bytes(w.offset.clone().try_into().unwrap_or([0; 4])), "offset_rule": w.offset_rule, "blob_sha256": blob.as_ref().map(|b| sha256_hex(b)).unwrap_or_else(|| network.blob_sha256_hex()),
    });
    // the network for this control: the batch blob, or the mutated blob (which may itself be refused by the adapter)
    let evaluated = match blob {
        Some(b) => match zkdiff_armc_adapter::ArmcIntDenoiser::from_blob(b) {
            Ok(net) => evaluate(w, &net).map_err(|e| format!("relation: {}", e.message())),
            Err(e) => Err(format!("constants_blob (adapter parse): {}", e.message())),
        },
        None => evaluate(w, &network.net).map_err(|e| format!("relation: {}", e.message())),
    };
    match evaluated {
        Err(msg) => {
            let behaved = c.layer == "relation" || c.layer == "relation_or_policy" || (c.layer == "pending_frame" && msg.contains("does not open"));
            serde_json::json!({"control": c.name, "layer_expected": c.layer, "layer_actual": "relation", "mutation": c.mutation, "expected_failure_stage": c.expected_stage, "actual": msg, "behaved_as_expected": behaved, "mutated_artefact_identity": ident})
        }
        Ok(public) => {
            let p = PublicOutput::parse(&public).ok();
            let (acc_json, failed_at) = match exp {
                Some(e) => {
                    let a = accept_public(&public, e);
                    let f = a.checks.iter().find(|c| c.status == "FAIL").map(|c| c.name.clone());
                    (Some(a.json()), f)
                }
                None => (None, None),
            };
            let layer_actual = if failed_at.is_some() { "policy" } else { "accepted" };
            let behaved = match c.layer {
                "policy" | "relation_or_policy" => failed_at.is_some(),
                "accepted" => failed_at.is_none(),
                _ => false,
            };
            serde_json::json!({
                "control": c.name, "layer_expected": c.layer, "layer_actual": layer_actual, "mutation": c.mutation, "expected_failure_stage": c.expected_stage,
                "actual": format!("RELATION ACCEPTED a statement (public sha256 {}); acceptance verifier: {}", sha256_hex(&public), failed_at.clone().map(|f| format!("FAIL at {f}")).unwrap_or_else(|| if exp.is_some() { "PASS".into() } else { "not run (no --expect)".into() })),
                "public_values_sha256": sha256_hex(&public),
                "statement": p.map(|p| decoded_json(&p)),
                "acceptance": acc_json,
                "behaved_as_expected": behaved,
                "mutated_artefact_identity": ident,
            })
        }
    }
}

#[allow(clippy::too_many_arguments)]
fn run_controls(common: &Common, session: &Session, network: &witness::Network, blob_path: &Path, out_dir: &Path, row: u32, frames_dir: Option<&Path>, noise_dir: Option<&Path>, frames_name: &str, noise_name: &str, proof: Option<&Path>) -> bool {
    let exp = common.expected.as_ref();
    let n = session.profile.row_count;
    let load = |dir: Option<&Path>, pattern: &str, r: u32| -> Option<Vec<u8>> {
        let p = dir?.join(file_name(pattern, r));
        std::fs::read(p).ok()
    };
    let assemble = |r: u32| -> Result<Witness, String> {
        let a = rule::assignment(r, RULE_ROW_START, n).ok_or_else(|| format!("row {r} has no assignment"))?;
        let raw = load(frames_dir, frames_name, r).ok_or_else(|| format!("frame of row {r} is not on this box"))?;
        let noise = load(noise_dir, noise_name, r).ok_or_else(|| format!("noise of row {r} is not on this box"))?;
        session.assemble(r, a.offset, a.mirrored, raw, noise)
    };
    let base = assemble(row);
    let mut results: Vec<serde_json::Value> = Vec::new();
    let mut all_ok = true;
    let baseline = match &base {
        Ok(w) => {
            let c = WitnessControl { name: "baseline", layer: "accepted", mutation: "none (the rule's own statement for this row)".into(), expected_stage: "none".into(), witness: Ok((w.clone(), None)) };
            let r = run_witness_control(&c, network, exp);
            all_ok &= r["behaved_as_expected"] == true;
            results.push(r);
            Some(w.clone())
        }
        Err(e) => {
            results.push(serde_json::json!({"control": "baseline", "actual": format!("cannot assemble row {row}: {e}"), "behaved_as_expected": false}));
            all_ok = false;
            None
        }
    };
    if let Some(w) = &baseline {
        let a = rule::assignment(row, RULE_ROW_START, n).unwrap();
        let mut list: Vec<WitnessControl> = Vec::new();
        let mk = |name: &'static str, layer: &'static str, mutation: &str, stage: &str, f: &dyn Fn(&mut Witness)| {
            let mut t = w.clone();
            f(&mut t);
            WitnessControl { name, layer, mutation: mutation.into(), expected_stage: stage.into(), witness: Ok((t, None)) }
        };
        list.push(mk("raw.byte_12345", "relation", "raw frame byte 12345 ^= 1", "membership: proved row does not open to the committed ordered-session root", &|t| t.raw[12_345] ^= 1));
        list.push(mk("header.s_r_byte_16", "relation", "header S_r byte 16 ^= 1 (the row's own state)", "previous_advance_leg: previous row's advance does not produce the proved row's S_t", &|t| t.header[16] ^= 1));
        list.push(mk("header.drand_round_byte_76", "relation", "header drand round byte 76 ^= 1", "drand_verify: the beacon signature does not verify for that round", &|t| t.header[76] ^= 1));
        list.push(mk("beacon.sig_r_bit", "relation", "row r's quicknet signature byte 10 ^= 1", "drand_verify", &|t| t.signature[10] ^= 1));
        list.push(mk("predecessor.s_prev_byte_8", "relation", "previous record S_{r-1} byte 8 ^= 1", "previous_advance_leg: previous row's advance does not produce the proved row's S_t", &|t| t.previous[8] ^= 1));
        list.push(mk("predecessor.sig_prev_byte_140", "relation", "previous record signature byte 140 ^= 1", "previous_advance_leg: beacon r-1 does not verify", &|t| t.previous[140] ^= 1));
        list.push(mk("state.leaf_u_s_u_byte_12", "relation", "wrong-row leaf S_u byte 12 ^= 1", "emission_render_u: declared wrong row's pattern does not render to its leaf's emission digest", &|t| t.leaf_u[12] ^= 1));
        list.push(mk("membership.sibling_r_last_byte", "relation", "last byte of row r's sibling path ^= 1", "membership: proved row does not open to the committed ordered-session root", &|t| {
            let i = t.membership.len() - 1;
            t.membership[i] ^= 1
        }));
        list.push(mk("membership.sibling_u_byte_0", "relation", "wrong-row sibling path byte 0 ^= 1", "membership: declared wrong row does not open to the committed ordered-session root", &|t| t.siblings_u[0] ^= 1));
        // conditioning identity: another row's leaf under the same declared offset
        let other_u = if a.wrong_row + 1 < n { a.wrong_row + 1 } else { a.wrong_row - 1 };
        let other = session.assemble(row, if other_u > row { (other_u - row) as i32 } else { -((row - other_u) as i32) }, false, w.raw.clone(), w.noise.clone());
        list.push(WitnessControl {
            name: "conditioning.leaf_of_other_row",
            layer: "relation",
            mutation: format!("leaf_u and siblings_u replaced by row {other_u}'s, declared offset unchanged ({:+})", a.offset),
            expected_stage: "parse_witness: wrong-row leaf witness does not carry row r + offset".into(),
            witness: other.as_ref().map(|o| {
                let mut t = w.clone();
                t.leaf_u = o.leaf_u.clone();
                t.siblings_u = o.siblings_u.clone();
                (t, None)
            }).map_err(|e| e.clone()),
        });
        // a coherent alternative offset: legal for the generic relation, wrong under the declared rule
        let alt_d = if a.offset == 2 { -2 } else { 2 };
        let alt = session.assemble(row, alt_d, false, w.raw.clone(), w.noise.clone());
        list.push(WitnessControl {
            name: "conditioning.coherent_alternative_offset",
            layer: "policy",
            mutation: format!("offset {alt_d:+} (direct) with the matching leaf_u and siblings_u of row {}, instead of the rule's {:+}", row as i64 + alt_d as i64, a.offset),
            expected_stage: "acceptance verifier: rule.assignment (the relation itself accepts this coherent statement)".into(),
            witness: alt.map(|t| (t, None)),
        });
        list.push(mk("noise.byte_0", "policy", "noise witness byte 0 ^= 1", "acceptance verifier: row.noise_blake3 (the relation accepts a different valid statement with a different noise digest)", &|t| t.noise[0] ^= 1));
        // constants: a header byte (parser refuses) and a byte deep inside the weights (hash differs; parser may or may not refuse)
        let mut blob_hdr = network.blob.clone();
        blob_hdr[8] ^= 1;
        list.push(WitnessControl { name: "constants.blob_header_byte_8", layer: "relation", mutation: "constants blob byte 8 ^= 1".into(), expected_stage: "constants_blob: the adapter's parser refuses the blob".into(), witness: Ok((w.clone(), Some(blob_hdr))) });
        let mut blob_mid = network.blob.clone();
        let mid = blob_mid.len() / 2;
        blob_mid[mid] ^= 1;
        list.push(WitnessControl { name: "constants.blob_byte_mid", layer: "relation_or_policy", mutation: format!("constants blob byte {mid} ^= 1 (inside the weights region)"), expected_stage: "constants_blob parse (relation) or acceptance verifier program.constants_sha256 (policy): a different blob is a different statement".into(), witness: Ok((w.clone(), Some(blob_mid))) });
        // mirrors
        list.push(mk("mirror.flag_on_direct_row", "relation", &format!("offset_rule flag set to mirrored on row {row}, whose direct wrong row {} exists", a.wrong_row), "parse_witness: mirrored offset claimed although the direct wrong row lies inside the session", &|t| t.offset_rule = vec![OFFSET_RULE_MIRRORED]));
        list.push(mk("mirror.minus30_direct_on_this_row", "relation", "offset -30 with the direct flag", "parse_witness: declared offset must be a nonzero protocol offset (-30 is admitted only as a mirror)", &|t| {
            t.offset = (-30_i32).to_le_bytes().to_vec();
            t.offset_rule = vec![OFFSET_RULE_DIRECT]
        }));
        list.push(mk("mirror.plus30_mirrored_on_this_row", "relation", "offset +30 with the mirror flag (its base would be -30)", "parse_witness: mirrored offset must be the mirror of a protocol offset", &|t| {
            t.offset = 30_i32.to_le_bytes().to_vec();
            t.offset_rule = vec![OFFSET_RULE_MIRRORED]
        }));
        // the valid mirror: row 684 (-30, mirrored) with its frame if it is here, else a substitute frame (then the
        // relation must fail exactly at the membership leg, AFTER the offset check, and the control is pending)
        for (name, r684, d, flag, layer, stage) in [
            ("mirror.valid_row_684_minus30", 684_u32, -30_i32, OFFSET_RULE_MIRRORED, "accepted", "none: accepted by the relation and by the acceptance verifier"),
            ("mirror.invalid_row_684_minus30_direct", 684, -30, OFFSET_RULE_DIRECT, "relation", "parse_witness: declared offset must be a nonzero protocol offset"),
            ("mirror.invalid_row_684_plus30_mirrored", 684, 30, OFFSET_RULE_MIRRORED, "relation", "parse_witness: mirrored offset must be the mirror of a protocol offset"),
            ("mirror.invalid_row_684_plus30_direct", 684, 30, OFFSET_RULE_DIRECT, "relation", "parse_witness: declared wrong row is outside the committed session"),
            ("mirror.policy_only_row_698_minus15_direct", 698, -15, OFFSET_RULE_DIRECT, "policy", "acceptance verifier: rule.assignment (row 698's rule offset is the mirrored -15; a direct -15 claim is generically valid)"),
        ] {
            let frame = load(frames_dir, frames_name, r684);
            let noise = load(noise_dir, noise_name, r684).unwrap_or_else(|| w.noise.clone());
            let (raw, frame_note, layer_eff) = match frame {
                Some(f) => (f, "own frame".to_string(), layer),
                None => (witness::synthetic_frame('a'), "SUBSTITUTE frame (row's frame not on this box): the relation must fail at the membership leg, after the offset check; complete run pending the node".to_string(), if layer == "accepted" || layer == "policy" { "pending_frame" } else { layer }),
            };
            let wit = if (0..n as i64).contains(&(r684 as i64 + d as i64)) {
                session.assemble(r684, d, flag == OFFSET_RULE_MIRRORED, raw, noise).map(|mut t| {
                    t.offset = d.to_le_bytes().to_vec();
                    t.offset_rule = vec![flag];
                    (t, None)
                })
            } else {
                // u outside: assemble with the rule's own offset, then relabel (the guest refuses before reading leaf_u)
                let a684 = rule::assignment(r684, RULE_ROW_START, n).unwrap();
                session.assemble(r684, a684.offset, a684.mirrored, raw, noise).map(|mut t| {
                    t.offset = d.to_le_bytes().to_vec();
                    t.offset_rule = vec![flag];
                    (t, None)
                })
            };
            list.push(WitnessControl { name, layer: layer_eff, mutation: format!("row {r684}, offset {d:+}, flag {}, {frame_note}", if flag == OFFSET_RULE_MIRRORED { "mirrored" } else { "direct" }), expected_stage: stage.into(), witness: wit });
        }
        for c in &list {
            let r = run_witness_control(c, network, exp);
            if r["pending"] != true {
                all_ok &= r["behaved_as_expected"] == true;
            }
            println!("control={} layer_expected={} behaved={} actual={}", c.name, c.layer, r["behaved_as_expected"], r["actual"].as_str().unwrap_or("").chars().take(160).collect::<String>());
            results.push(r);
        }
    }
    // proof-level controls against a real artifact, when given
    let proof_controls = match (proof, exp) {
        (Some(p), Some(e)) => match ceremony_core::load_exact(p) {
            Ok((pr, bytes, digest)) => {
                let raw = pr.bytes();
                let public = pr.public_values.to_vec();
                let mut cs = accept::groth16_rejection_controls(&raw, &public, e.vkey(), e.str("groth16_vk_sha256"));
                cs.extend(accept::policy_rejection_controls(&raw, &public, e));
                let all = cs.iter().all(|c| c.behaved);
                all_ok &= all;
                let base_ok = accept::accept(&raw, &public, e);
                all_ok &= base_ok.ok();
                serde_json::json!({"artifact": p.display().to_string(), "artifact_bytes": bytes, "artifact_sha256": digest, "baseline_acceptance": base_ok.json(), "controls": cs.iter().map(accept::Control::json).collect::<Vec<_>>(), "all_behaved": all})
            }
            Err(e) => {
                all_ok = false;
                serde_json::json!({"artifact": p.display().to_string(), "error": e})
            }
        },
        (Some(p), None) => {
            all_ok = false;
            serde_json::json!({"artifact": p.display().to_string(), "error": "proof-level controls need --expect"})
        }
        (None, _) => serde_json::json!({"pending": true, "note": "no --proof given: proof-level controls run on the node against the pilot proof (zkdiff-verify --controls, or zkdiff-batch controls --proof)"}),
    };
    let report = serde_json::json!({
        "schema": "zbdiff-controls/v1",
        "attempt_id": common.attempt_id, "written_utc": utc_stamp(), "host": hostname(), "command": common.args, "binary_sha256": self_sha256(),
        "guest_elf_sha256": common.elf_sha256, "constants_blob": blob_path.display().to_string(), "constants_sha256": network.blob_sha256_hex(),
        "expected_identities": exp.map(|e| serde_json::json!({"path": e.path, "sha256": e.sha256})),
        "row": row,
        "layers": {"relation": "the guest's relation refuses the witness (message recorded)", "policy": "the relation accepts a coherent different statement; the acceptance verifier refuses it at the named check", "pending_frame": "the row's frame is not on this box; the relation fails at the membership leg after the offset check, the complete run is pending the node"},
        "witness_controls": results,
        "proof_controls": proof_controls,
        "all_behaved": all_ok,
    });
    std::fs::create_dir_all(out_dir).expect("out dir");
    write_json_durable(&out_dir.join("CONTROLS.json"), &report).expect("controls report");
    println!("controls_report={} all_behaved={all_ok}", out_dir.join("CONTROLS.json").display());
    all_ok
}
