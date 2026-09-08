//! SP1 guest for the ZeeBeam two-evaluation diffusion statement (ZBDIFF01) with the real integer network.
//!
//! Private inputs, in order (`read_vec` each): the ten witness items of statement.rs (nine items plus the one-byte
//! offset-rule flag), then the armc-int constants blob. The blob is hashed (SHA-256, published as `constants_sha256`
//! at public offset 564), parsed and checked against the relation's compiled constants by
//! `zkdiff_armc_adapter::ArmcIntDenoiser::from_blob`; the relation then runs every leg through
//! `armc_relation::statement::evaluate` (the same function the host oracle runs natively) and the 752 public bytes
//! are committed with `denoiser_kind = 1`.

#![no_main]
sp1_zkvm::entrypoint!(main);

use armc_relation::net::Denoiser;
use armc_relation::statement::{evaluate, Witness};
use zkdiff_armc_adapter::ArmcIntDenoiser;

pub fn main() {
    println!("cycle-tracker-report-start: private_input");
    let witness = Witness {
        header: sp1_zkvm::io::read_vec(),
        membership: sp1_zkvm::io::read_vec(),
        raw: sp1_zkvm::io::read_vec(),
        signature: sp1_zkvm::io::read_vec(),
        previous: sp1_zkvm::io::read_vec(),
        leaf_u: sp1_zkvm::io::read_vec(),
        siblings_u: sp1_zkvm::io::read_vec(),
        noise: sp1_zkvm::io::read_vec(),
        offset: sp1_zkvm::io::read_vec(),
        offset_rule: sp1_zkvm::io::read_vec(),
    };
    let blob = sp1_zkvm::io::read_vec();
    println!("cycle-tracker-report-end: private_input");

    println!("cycle-tracker-report-start: constants_blob");
    let net = ArmcIntDenoiser::from_blob(&blob).unwrap_or_else(|error| panic!("constants blob rejected: {error}"));
    drop(blob);
    println!("cycle-tracker-report-end: constants_blob");
    println!("denoiser_kind={}", net.kind());

    println!("cycle-tracker-report-start: zbdiff_relation");
    let public = evaluate(&witness, &net).unwrap_or_else(|error| panic!("diffusion relation rejected: {error}"));
    println!("cycle-tracker-report-end: zbdiff_relation");

    println!("cycle-tracker-report-start: public_commitment");
    sp1_zkvm::io::commit_slice(&public);
    println!("cycle-tracker-report-end: public_commitment");
}
