//! Execute-only local host: runs the guest in the SP1 executor (no proof), prints the instruction count, the
//! syscall count and every cycle-tracker region, and checks the committed public bytes against the native
//! re-execution and, if given, the Python oracle's binding fields. Pattern: the proved script/src/main.rs.
//!
//! usage: zkdiff-execute --witness-dir DIR --raw PATH|synthetic:a --blob PATH [--expected PATH]
#![recursion_limit = "512"]
#![allow(dead_code)]

mod witness;

use std::path::PathBuf;
use std::time::Instant;

use sp1_sdk::{
    blocking::{Prover, ProverClient},
    include_elf, Elf,
};

const ZKDIFF_ELF: Elf = include_elf!("zkdiff-guest");

fn main() {
    sp1_sdk::utils::setup_logger();
    let args: Vec<String> = std::env::args().skip(1).collect();
    let usage = || -> ! {
        eprintln!("usage: zkdiff-execute --witness-dir DIR --raw PATH|synthetic:a --blob PATH [--expected PATH]");
        std::process::exit(2)
    };
    let dir = PathBuf::from(witness::arg(&args, "--witness-dir").unwrap_or_else(|| usage()));
    let blob = PathBuf::from(witness::arg(&args, "--blob").unwrap_or_else(|| usage()));
    let raw = witness::arg(&args, "--raw").unwrap_or_else(|| "synthetic:a".into());
    let expected = witness::arg(&args, "--expected").map(PathBuf::from);
    let network = witness::Network::load(&blob);
    let built = witness::build(&dir, &raw, expected, &network);

    println!("mode=execute_only");
    println!("prover=local_cpu_explicit");
    println!("row={}", built.row);
    println!("raw={raw}");
    println!("constants_blob={} constants_blob_bytes={} constants_sha256={} spec_sha256={}", blob.display(), network.blob.len(), network.blob_sha256_hex(), network.spec_sha256_hex());
    println!("guest_elf_bytes={} guest_elf_sha256={}", ZKDIFF_ELF.len(), witness::hex(&sha2::Sha256::digest(&*ZKDIFF_ELF)));

    let client = ProverClient::builder().cpu().build();
    let started = Instant::now();
    let (output, report) = client.execute(ZKDIFF_ELF, built.stdin.clone()).run().expect("SP1 execute failed");
    let actual = output.as_slice();
    match witness::check(actual, &built, &network) {
        Ok(oracle) => {
            println!("oracle={} checked={} circuit_derived=0", oracle.mode, oracle.bytes_checked);
            for n in &oracle.notes {
                println!("oracle_note={n}");
            }
            println!("public_values_hex={}", witness::hex(actual));
            println!("verified_public_values=true");
        }
        Err(e) => {
            eprintln!("MISMATCH: {e}");
            panic!("public values differ from the oracle");
        }
    }
    println!("public_values_bytes={}", actual.len());
    println!("total_instruction_count={}", report.total_instruction_count());
    println!("total_syscall_count={}", report.total_syscall_count());
    {
        let mut regions: Vec<_> = report.cycle_tracker.iter().collect();
        regions.sort_by(|a, b| b.1.cmp(a.1));
        for (name, cycles) in regions {
            println!("CYCLE_REGION {name} = {cycles}");
        }
    }
    println!("host_elapsed_ms={}", started.elapsed().as_millis());
    println!("proof_generated=false");
}

use sha2::Digest;
