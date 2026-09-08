//! Standalone verification of a ZeeBeam one-proof Groth16 artifact.
//!
//! usage: zeebeam-standalone-verifier <proof.bin> <public_values.bin> <sp1_vkey_hash_hex>
//!
//! proof.bin is the on-chain byte encoding (4-byte Groth16 vkey-hash prefix + encoded proof),
//! public_values.bin is the public statement (1,085 bytes for ceremony 1, 1,101 for the final
//! relation; the proof binds whatever bytes are supplied), and the SP1 vkey hash is the 0x-prefixed
//! 32-byte hash of the guest program's verification key. The Groth16 verifying key for SP1 6.4.0
//! (circuit v6.1.0) is embedded in the sp1-verifier crate. Nothing else is needed.
use sha2::{Digest, Sha256};
use sp1_verifier::{Groth16Verifier, GROTH16_VK_BYTES};

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.len() != 3 {
        eprintln!("usage: zeebeam-standalone-verifier <proof.bin> <public_values.bin> <sp1_vkey_hash_hex>");
        std::process::exit(2);
    }
    let proof = std::fs::read(&args[0]).expect("read proof");
    let public = std::fs::read(&args[1]).expect("read public values");
    let vkey = args[2].trim().to_string();
    println!("proof_bytes={} proof_sha256={:x}", proof.len(), Sha256::digest(&proof));
    println!("public_values_bytes={} public_values_sha256={:x}", public.len(), Sha256::digest(&public));
    println!("sp1_vkey_hash={vkey}");
    match Groth16Verifier::verify(&proof, &public, &vkey, *GROTH16_VK_BYTES) {
        Ok(()) => {
            // the same proof must reject a single flipped public byte and a wrong vkey
            let mut tampered = public.clone();
            tampered[87] ^= 1;
            let t1 = Groth16Verifier::verify(&proof, &tampered, &vkey, *GROTH16_VK_BYTES).is_err();
            let mut wrong = vkey.clone();
            let last = wrong.pop().unwrap();
            wrong.push(if last == '0' { '1' } else { '0' });
            let t2 = Groth16Verifier::verify(&proof, &public, &wrong, *GROTH16_VK_BYTES).is_err();
            println!("tamper_public_byte_87_rejected={t1}");
            println!("wrong_vkey_rejected={t2}");
            if t1 && t2 {
                println!("VERIFIED");
            } else {
                println!("VERIFIED_BUT_TAMPER_CONTROL_FAILED");
                std::process::exit(3);
            }
        }
        Err(e) => {
            println!("REJECTED: {e}");
            std::process::exit(1);
        }
    }
}
