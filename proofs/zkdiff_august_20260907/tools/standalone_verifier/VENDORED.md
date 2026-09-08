# Vendored: the ZeeBeam standalone verifier

Byte-for-byte copy of `bundle/proofs_20260902/verifier/standalone_verifier/` from the public repository github.com/poliebotics/zeebeam at commit
`ef686b337bf70016b30d713d9948928ac56c88bd` (the ZeeBeam 1.0.0 release commit of 7 September 2026). `sp1-verifier` 6.4.0 plus `sha2`, 209 locked
packages; no SP1 SDK, no ELF, no prover. It verifies the Groth16 layer of a proof under a program verifying key and
checks two tamper controls (a flipped public byte, a wrong key); it knows nothing about the ZBDIFF01 statement layout.
Build and use: `VERIFY.md` section 1. Digests of the three files (SHA-256):

- `tools/standalone_verifier/Cargo.toml` `07c3da3e187769e9734087a3c21fc18dc38144b756765641b580d1f13b6f2a71`
- `tools/standalone_verifier/Cargo.lock` `78fa1a2b85ac671f7e881ff4e4e9bfd84d1cec8d7cdabc52f1ff03aebffc19c1`
- `tools/standalone_verifier/src/main.rs` `052f7a69dd66029659ea6acbb76a01cf902b6751ee43dedce150467b4cbf638a`

Check against the repository: `git -C zeebeam show ef686b337bf70016b30d713d9948928ac56c88bd:bundle/proofs_20260902/verifier/standalone_verifier/Cargo.lock | sha256sum`.
