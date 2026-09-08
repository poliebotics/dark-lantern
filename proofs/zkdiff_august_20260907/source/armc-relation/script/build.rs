use sp1_build::{build_program_with_args, BuildArgs};

/// Path-independent guest build, copied from the proved host's build.rs
/// (rust/row_binding_join_membership_sp1_candidate/script/build.rs): remap the cargo home (registry and git
/// checkouts) and the source-tree root so panic locations and debug strings carry no machine-specific paths, so
/// two machines with the same sources, lockfile and toolchain produce byte-identical ELFs and the same
/// verification key. The root here is `g2_guest/` (script -> armc-relation -> g2_guest), which contains every
/// first-party crate the guest embeds (program, relation, b3xof, adapter and the sibling `armc-int`); remapping
/// only `armc-relation/` left three `armc-int` source paths in the ELF (G2-D build log).
fn main() {
    let cargo_home = std::env::var("CARGO_HOME")
        .ok()
        .or_else(|| std::env::var("HOME").ok().map(|h| format!("{h}/.cargo")))
        .expect("CARGO_HOME or HOME");
    let manifest = std::env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR");
    let root = std::path::Path::new(&manifest)
        .ancestors()
        .nth(2)
        .expect("g2_guest root")
        .to_string_lossy()
        .to_string();
    // Astra r5, node reproduction: cargo hashes path dependencies that lie outside the guest's workspace root
    // (relation, adapter, b3xof, armc-int) by ABSOLUTE path into `-C metadata`, so the mangled symbol names in
    // .symtab/.strtab depend on where the tree sits (the development machine's g2_guest vs the node's g2_guest_r5 gave the same vkey and
    // the same loaded segments but a different file hash). The loaded program never needs the symbol table: strip it,
    // so the ELF bytes depend only on sources, lockfiles and toolchain.
    let args = BuildArgs {
        rustflags: vec![
            format!("--remap-path-prefix={cargo_home}=/cargo"),
            format!("--remap-path-prefix={root}=/g2"),
            "-Cstrip=symbols".to_string(),
        ],
        locked: true,
        ..Default::default()
    };
    build_program_with_args("../program", args)
}
