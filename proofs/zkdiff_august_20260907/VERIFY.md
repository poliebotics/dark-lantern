---
version: 1.7
date: 2026-09-08
status: how to verify one proof and all of them, with nothing installed (the capsule), with Rust, or with the SP1 toolchain, with or without the network (the offline build kit); decode a statement, rebuild the program and its key, check every pinned identity, recompute a row from its published frame; verification routes rehearsed on 8 September 2026 (section 9, replicate/TEST_LOG.md, capsule/README.md); unrehearsed routes are identified below
author: BOSUN for Cathal Ryan Hynes
---

# Verifying the zkdiff August proofs

Everything a verifier needs is in this directory or in `PINS.json`: the proofs (`proofs/`), the public statements
(`public_values/`), the receipts (`receipts/`), the frozen source of the program and its verifier (`source/`), the frozen
expected identities (`source/expected_identities_august.json`), the constants blob (`source/blobs/final_int16/`), the
normative noise (`source/noise_august/`), the chain log (`source/vectors_relation/august/chain_log.csv`) and the vendored
standalone verifier (`tools/standalone_verifier/`). Nothing here requires trusting the prover: the program's verifying key
is a pin, the circuit's verifier key is embedded in the published `sp1-verifier` 6.4.0 crate, and the program is rebuilt
from source and asserted against the pin.

The publication is two-part: this repository package, and the data-layer bundle at
`https://data.truthbeam.com/results/zkdiff_august_20260907/v1/` holding the frames, the large arrays, the node's collection and
the offline build kit (`README.md`, `LARGE_FILES.md`, `FRAMES.md`). Every object there is named by path and SHA-256, most in
this package (`LARGE_FILES_SHA256SUMS`, `FRAMES.md`, `PINS.json`) and the node's collection and the bundle's README only in the
bundle's `_control/MANIFEST.jsonl`; the bundle's controls are `_control/MANIFEST.jsonl`, `_control/SHA256SUMS` and `_control/RELEASE.json`, and the Dark
Lantern root `README.md` fixes their digests in the commit that adds this package. The capsule, the standalone verifier and the
identity and noise checks need nothing from the bundle; the offline rebuild kit, the re-execution of rows other than 600, the
tests with the export sets and the oracle regeneration say what they fetch.

Three ways in, by what you have installed. With nothing but bash and coreutils: the offline capsule, section 2a
(`capsule/verify_offline.sh`: static x86-64 Linux binaries, no network, about three and a half minutes on the rehearsal machine;
`capsule/reexecute/reexecute_row.sh` recomputes a row from its raw frame). With a Rust toolchain: the standalone verifier,
section 1. With the SP1 toolchain: the full route, sections 2 and 5, which rebuilds the program from source and asserts the
pins; with no network at all, the same rebuild from the offline build kit on the data layer, section 2b. One command runs the
whole ladder from an empty machine, downloading and hash-checking every toolchain it needs: `replicate/replicate.sh all --no-prove`
(`replicate/README.md`; rehearsed end to end in a fresh Ubuntu 22.04 container, `replicate/TEST_LOG.md`). Without any
binary, `tools/check_identities.py` (Python, standard library) compares every statement's fields with the frozen
identities, the chain log and the receipts, and `tools/regen_noise.py` (numpy) regenerates the normative noise from its rule;
neither verifies a proof.

Every command below is anchored to `P`, the absolute path of this directory (wherever your copy sits; the name in the
repository is `proofs/zkdiff_august_20260907`), and runs from any working directory; set it first and never `cd` into a
subdirectory between steps (a relative path such as `proofs/row_000600_groth16.bin` is relative to `P`, not to wherever the
previous step left you):

```
P=/absolute/path/to/zkdiff_august_20260907   # a renamed or relocated copy works the same (FAQ 60)
```

Tags: **[confirm]** marks a step that has not been rehearsed on this package's exact bytes. After the rehearsals of 8 September
2026 two remain, each tagged where it stands: the regeneration of the August export sets with the exporter (section 6) and the
complete oracle regeneration with the August rows placed (section 7). The GPU prove path, the third open step of the earlier
revision, was rehearsed that evening from the package alone on a freshly rented A100-SXM4-40GB machine (section 9). The dependency fetch
from an empty cargo home, the one open step of the earlier revision, was rehearsed by the replication kit in a fresh container
(`replicate/TEST_LOG.md`), which corrected two commands of section 2 as noted there, and the rebuild with no network at all was
rehearsed from the offline build kit (section 2b).

## 0. Check the ledger first

```
(cd "$P" && sha256sum -c --quiet SHA256SUMS && echo LEDGER_OK)
(cd "$P" && find . -type f ! -name SHA256SUMS ! -path '*/target/*' ! -path './source/armc-relation/runs/build_record_*' ! -path './source/armc-relation/runs/build_log_*' ! -path './source/armc-relation/runs/SOURCE_DIGESTS_*' ! -path './source/armc-relation/runs/.build_start_*' \
   | sed 's|^\./||' | LC_ALL=C sort | LC_ALL=C comm -23 - <(LC_ALL=C sort <(cut -c67- SHA256SUMS) <(cut -c67- LARGE_FILES_SHA256SUMS)) | grep . && echo UNLISTED_FILES || echo NO_UNLISTED_FILES)
```

Every line of the first command must say OK, and the second must print `NO_UNLISTED_FILES`, before anything else is trusted.
The second command lists any file that neither ledger names; it allows the files a rebuild leaves under `target/` and in
`source/armc-relation/runs/`, and it allows the data-layer files whether or not they have been placed, because they are
listed in the second ledger:

```
(cd "$P" && sha256sum -c --quiet LARGE_FILES_SHA256SUMS && echo LARGE_FILES_OK)
```

The data-layer files are needed only for the oracle parity tests of section 6 and the regeneration of section 7, never for
verifying a proof. The data-layer prefix `results/zkdiff_august_20260907/v1/` (served at `https://data.truthbeam.com/`) holds
them under `repository_package_large_files/` at the same relative paths; `replicate/replicate.sh fetch` downloads and checks
them. The raw frames of the proof rows are on the same prefix under `frames/`, listed with their digests in `FRAMES.md`; keep
downloaded frames outside this directory (they are not package files), as section 2a and `capsule/README.md` describe.

## 1. Verify a proof with the standalone verifier (no SP1 toolchain)

The Groth16 layer of every proof here is the SP1 6.4.0 Groth16 wrap, circuit v6.1.0, the same layer the ZeeBeam release
verifies with its standalone verifier (`sp1-verifier` 6.4.0 plus `sha2`, 209 locked packages). That verifier is vendored
here, byte for byte, from github.com/poliebotics/zeebeam at commit `ef686b337bf70016b30d713d9948928ac56c88bd` (the
ZeeBeam 1.0.0 release commit; `tools/standalone_verifier/VENDORED.md` and `PINS.json` `standalone_verifier` carry the
three file digests, and `git show ef686b337bf70016b30d713d9948928ac56c88bd:bundle/proofs_20260902/verifier/standalone_verifier/Cargo.lock | sha256sum`
in a clone of that repository reproduces the lockfile digest). No external clone is needed. It takes the raw proof, the
public bytes and the program's verifying key and knows nothing about the statement's layout:

```
(cd "$P/tools/standalone_verifier" && cargo build --release --locked)
"$P/tools/standalone_verifier/target/release/zeebeam-standalone-verifier" \
    "$P/proofs/row_000600_groth16_proof.bin" \
    "$P/public_values/row_000600_public_values.bin" \
    0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027
```

Requirements: a stable Rust toolchain with `cargo` (rehearsed with 1.98.0) and, for the first build, either the network
or a cargo home that already holds the 209 locked crates (`cargo build --release --locked --offline` then). Expected
output ends with `tamper_public_byte_87_rejected=true`, `wrong_vkey_rejected=true` and `VERIFIED` (exit 0): the proof
verifies under the pinned key, and the same proof is rejected with one flipped public byte and with a wrong key. All rows:

```
n=0; for r in "$P"/proofs/row_*_groth16_proof.bin; do
  b=$(basename "$r" _groth16_proof.bin); n=$((n+1))
  "$P/tools/standalone_verifier/target/release/zeebeam-standalone-verifier" "$r" "$P/public_values/${b}_public_values.bin" \
      0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027 | grep -q '^VERIFIED$' || { echo "REJECTED $r"; exit 1; }
done && [ "$n" -eq 112 ] && echo "standalone: $n VERIFIED"
```

What this route establishes is that each proof verifies under the pinned program key; it does not check the statement's
identities (section 2 or 2a does), and it says nothing about which program the key belongs to (section 5 does). In
particular a relabelled statement on one of the eight policy-only rows (697, 702, 707, 710, 698, 703, 708 and 711; `STATEMENT.md` section 7) passes this route and is
refused only by the acceptance verifier. Confirmed on all 112 proofs by the capsule (section 2a) and by the replication kit.

## 2. Verify with the package's own acceptance verifier (full check)

`zkdiff-verify` verifies the Groth16 proof under the pinned program key and the embedded circuit key and then refuses
any statement whose identities differ from the frozen expected identities: program, constants, spec and preprocessing
digests, session, the declared offset rule, the row's normative noise BLAKE3, the chain log's raw and emission digests, the drand
rounds, the leaves, and the oracle's expected residual sums (`STATEMENT.md` section 9). Building it needs the SP1 6.4.0
toolchain because the host binaries embed the guest ELF.

Requirements, complete:

- A C compiler and linker and `pkg-config` (`build-essential pkg-config` on Debian and Ubuntu: `cc`, `ld`): several crates
  compile C sources in their build scripts and the linker produces the host binaries; the replication kit and the build kit list
  the same packages.
- Rust 1.98.0 through rustup (the `rust-toolchain` files pin it; rustup installs it on first use).
- SP1 6.4.0 through `sp1up --version v6.4.0`, which installs `cargo-prove sp1 (f66b4bf 2026-08-12)` and the succinct Rust
  toolchain (`rustc 1.94.0-dev`, LLVM 21.1.8); compare `sha256sum ~/.sp1/bin/cargo-prove` and the toolchain tarball with
  `PINS.json` `reproducible_build.guest_toolchain`. `~/.sp1/bin` must be on `PATH` (the build driver adds it).
- `protoc`, the Protocol Buffers compiler, with the standard protobuf includes (`google/protobuf/*.proto`): the build
  script of the `sp1-prover-types` 6.4.0 dependency runs it. On Debian and Ubuntu: `protobuf-compiler` and
  `libprotobuf-dev`; rehearsed with libprotoc 3.21.12 and `/usr/include/google/protobuf`.
- GNU time at `/usr/bin/time` (package `time`) and binutils (`strings`, `objdump`): the build driver measures the build
  with the former and reads the ELF and the host binaries' glibc requirements with the latter. `sha256sum` (coreutils).
- Go is not needed to build, verify or prove as the batch proved: the node built with `--features cuda` alone
  (`source/node_prep/r5/build_record_20260907T215855Z.txt`) and the Groth16 wrapping runs inside `sp1-gpu-server`; the
  `groth16` feature of the host crate, which would need Go, is enabled by nothing here (an earlier draft of
  `source/armc-relation/RELATION.md` named `groth16,cuda` and Go, corrected in the published copy).

Where the toolchain comes from, and the digest of every download (the same pins `replicate/replicate.sh` carries and
checks; `PINS.json` `reproducible_build.guest_toolchain` and `prover_node`):

| component | URL | SHA-256 |
|---|---|---|
| rustup-init 1.29.1 (x86_64 Linux), then `rustup toolchain install 1.98.0` | `https://static.rust-lang.org/rustup/archive/1.29.1/x86_64-unknown-linux-gnu/rustup-init` | `dda7234360b7f578ca8b0ddcb80145646fa61a67c1720a5abc7051b35c9fcb71` |
| cargo-prove 6.4.0 tarball (21,210,386 bytes); the `cargo-prove` binary inside | `https://github.com/succinctlabs/sp1/releases/download/v6.4.0/cargo_prove_v6.4.0_linux_amd64.tar.gz` | tarball `8ad88ebd4d970f0b9b7561f9b5899242f01c7da6d04ec4bd5d09f4cf044a541b`; binary `d8835f80b386d5025420d6b09e73ad825b822ac143e8ed09312b2e08018ff106` (`cargo-prove sp1 (f66b4bf 2026-08-12T14:40:11.709680161Z)`) |
| succinct guest toolchain tarball (384,963,362 bytes; rustc 1.94.0-dev, LLVM 21.1.8), linked as the rustup toolchain `succinct` | `https://github.com/succinctlabs/rust/releases/download/succinct-1.94.0-64bit/rust-toolchain-x86_64-unknown-linux-gnu.tar.gz` | `12c94435d41bfe4e20131bbcce40b35abd32270ad792befc653af4e3fabc192f` |
| protoc 21.12 (1,585,982 bytes; or the distribution's `protobuf-compiler` and `libprotobuf-dev`) | `https://github.com/protocolbuffers/protobuf/releases/download/v21.12/protoc-21.12-linux-x86_64.zip` | `3a4c1e5f2516c639d3079b1586e703fc7bcfa2136d58bda24d1d54f949c315e8` |
| sp1-gpu-server 6.4.0 tarball (133,469,274 bytes; proving only); the binary inside (250,950,472 bytes) | `https://github.com/succinctlabs/sp1/releases/download/v6.4.0/sp1_gpu_server_v6.4.0_x86_64.tar.gz` | tarball `2946b0b46026b8689181eb05561ed0be2798114196893d5ef38e46f93c14c596`; binary `f68b85dc3cff776a613df897ba6e7f8592d08482330b4165d46a8ee87aafd97c` |
| Groth16 v6.1.0 circuit files (proving only; the tarball is 6,211,807,514 bytes and is recorded by size, its seven files by digest) | `https://sp1-circuits.s3-us-east-2.amazonaws.com/v6.1.0-groth16.tar.gz` | `groth16_vk.bin` `4388a21c…e696`, `groth16_witness.json` `ee2ac8e0…4c94`, `Groth16Verifier.sol` `d5e77712…c457`, `SP1VerifierGroth16.sol` `48e1db5b…76d0`, `constraints.json` `1fb0b3d5…f92b`, `groth16_circuit.bin` `d6a66be2…4cbc`, `groth16_pk.bin` `c3760e0e…a167` (full digests in `PINS.json` `prover_node.groth16_circuit_files_v6_1_0`) |
| the locked crates | crates.io and the two git patches named in the lockfiles (`bls12_381` sp1-patches fork); each crate is checksummed by its lockfile entry | the four lockfile digests in `PINS.json` `reproducible_build.lockfiles` |

`sp1up --version v6.4.0` installs the first three of the SP1 items and is what the development machine and the node used;
the URLs let a reader fetch and check the same bytes without it. The prove path needs an A100-class GPU: the observed
memory peak of about 28.5 GiB exceeds a 24 GB card (`replicate/README.md`).

The workspace's `.cargo/config.toml` sets `offline = true`, so the locked dependencies must be present in the cargo home
first. From a machine that has never built SP1, fetch them once with the network. Two facts the replication kit's rehearsal
established (`replicate/TEST_LOG.md`) shape the commands: the guest fetch must NOT be narrowed with `--target`, because
`sp1-build` runs `cargo metadata` without a platform filter before building and the offline build then lacks crates such as
`r-efi`; and `sp1-core-executor-runner` 6.4.0 builds a helper binary from lockfiles shipped inside its own crate, which need
their own fetch in the registry copies or the offline build stops at `wasip3`:

```
(cd "$P/source/armc-relation/script" && CARGO_NET_OFFLINE=false cargo fetch --locked)
(cd "$P/source/armc-relation/program" && CARGO_NET_OFFLINE=false cargo +succinct fetch --locked)
(cd "$P/source/armc-relation" && CARGO_NET_OFFLINE=false cargo fetch --locked)
(cd "$P/source/armc-int" && CARGO_NET_OFFLINE=false cargo fetch --locked)
for c in sp1-core-executor-runner-6.4.0 sp1-core-executor-runner-binary-6.4.0; do
  (cd "$(ls -d "${CARGO_HOME:-$HOME/.cargo}"/registry/src/*/$c | head -1)" && CARGO_NET_OFFLINE=false cargo fetch --locked)
done
```

Rehearsed from an empty cargo home in a fresh Ubuntu 22.04 container on 8 September 2026 by `replicate/replicate.sh`
(`replicate/TEST_LOG.md`, runs 3 and 4), and offline against a populated cargo home on the development machine (section 9).
Then build and assert the pins in one step:

```
(cd "$P/source/armc-relation" && ./build_reproducible.sh)
```

The driver exits non-zero unless cargo succeeds, the lockfiles are unchanged, exactly one guest ELF and the four host
binaries were freshly built, and the ELF is 396,200 bytes with SHA-256
`51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc` and verifying key
`0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027`; its last line is then `BUILD_REPRODUCED_OK`. Its
record lands in `$P/source/armc-relation/runs/build_record_<stamp>.txt`. On the release machine a cold build of the
published tree (fresh `target/`, 16 jobs) took 77 s of cargo wall time and 3.2 GB of peak memory. Then:

```
S="$P/source/armc-relation/script/target/release"
"$S/zkdiff-verify" --identity
"$S/zkdiff-verify" --proof "$P/proofs/row_000600_groth16.bin" --expect "$P/source/expected_identities_august.json" --report /tmp/row_000600.verify.json
```

`--identity` prints `sp1_circuit_version v6.1.0`, `groth16_vk_sha256 4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696`
and `guest_elf_sha256 51b7bc35…75cc`. The verification exits 0 and its report says `accepted: true` with every check
PASS; the decoded statement in the report must equal the row's line in `RESULTS.md` and its `receipts/row_000600_receipt.json`.
The raw form takes the 356-byte proof and the 752 public bytes:

```
"$S/zkdiff-verify" --proof-bytes "$P/proofs/row_000600_groth16_proof.bin" --public "$P/public_values/row_000600_public_values.bin" --expect "$P/source/expected_identities_august.json"
```

All rows:

```
n=0; for p in "$P"/proofs/row_*_groth16.bin; do
  n=$((n+1)); "$S/zkdiff-verify" --proof "$p" --expect "$P/source/expected_identities_august.json" > /dev/null || { echo "REFUSED $p"; exit 1; }
done && [ "$n" -eq 112 ] && echo "every proof accepted ($n)"
```

Expected: `every proof accepted (112)`. The node's own cold acceptance reports are `receipts/row_XXXXXX_verify.json`
and the development machine's are `receipts/independent_verify/row_XXXXXX.verify.json`. The proof-level negative controls
(mutated public fields, proof bytes and program key, each rejected by the Groth16 verifier; mutated expected identities,
each refused at the named acceptance check while the proof still verifies):

```
"$S/zkdiff-verify" --proof "$P/proofs/row_000600_groth16.bin" --expect "$P/source/expected_identities_august.json" --controls --report /tmp/controls.json
```

Exit 0 means every control behaved; `receipts/proof_controls.json` is the node's record of the same run.

## 2b. Rebuild with no network: the offline build kit

The data-layer prefix carries `build_kit/` (`LARGE_FILES.md`; its own `BUILD_KIT.md` is the procedure): the vendored crates of
every lockfile under `source/` and `tools/standalone_verifier/` (674 crates.io crates and the two `sp1-patches` git crates,
`crates/vendor.tar.gz`, laid out in cargo-home shape so the guest's path remap gives the same strings and the ELF reproduces
byte for byte; `crates/offline_cargo_home.sh` extracts them into a `CARGO_HOME`, verifies every file against
`crates/VENDOR_SHA256SUMS` and writes the directory-source `config.toml`), the six pinned toolchain downloads by their upstream
names (rustup-init 1.29.1, the Rust 1.98.0 standalone tarball, cargo-prove 6.4.0, the succinct guest toolchain, protoc 21.12,
sp1-gpu-server 6.4.0; the digests of the table in section 2) and the seven Groth16 v6.1.0 circuit files with the record of the
tarball they came from (`circuits/groth16/v6.1.0/CIRCUIT_TARBALL.txt`: tarball SHA-256
`18beebb6cd0cc9b4d4a240ee4f49511da6c2a7e51724bad4232de538a9147810`, 6,211,807,514 bytes). Every kit file is listed with its
SHA-256 in `build_kit/KIT_MANIFEST.json` (26 files, 9,279,782,724 bytes with the circuit files; manifest SHA-256 `6fe432a725e2b81fe8e8815e38200571c9e7393250b17b4bf67182c6b631db46`, also in `PINS.json` `build_kit`).
From a bare x86-64 Linux box holding only the operating-system packages of the requirements list, the kit installs Rust 1.98.0
from the standalone tarball, rustup offline (`rustup-init --default-toolchain none`, then `rustup toolchain link`), the succinct
toolchain, cargo-prove and protoc, lays out the cargo home, and then section 2's `build_reproducible.sh` runs unchanged with
`--offline --locked`.
The six toolchain downloads are shipped as released upstream; the executables inside them keep their upstream build
environments' path strings (`/home/runner/.cargo/…`, `/build/…`: those projects' CI paths, not this programme's). The path-remap
assurance concerns the package's own rebuilt binaries and the capsule's (`build_kit/BUILD_KIT.md` section 7).

Rehearsed on 8 September 2026, four times (`build_kit/offline_build_test/OFFLINE_BUILD_TEST.md`, `docker.log`, `build_record_20260908T200732Z.txt`
and the 54-entry source inventory it names, `SOURCE_DIGESTS_20260908T200732Z.txt`; the fourth run against this revision's frozen
sources, inventory sha256 `24efb517…4a9d`):
a fresh `ubuntu:22.04` container with `build-essential pkg-config time binutils xz-utils unzip ca-certificates file` and nothing
else (no git, curl or python), started with `--network none`, uid 1000, the kit and a copy of this package's `source/`,
`tools/standalone_verifier/`, `proofs/` and `public_values/` mounted read-only: the kit's procedure ran end to end in 160 s, 164 s,
187 s and 189 s (four runs) and `build_reproducible.sh` ended `BUILD_REPRODUCED_OK sha256=51b7bc35…75cc vkey=0x00f01894…a027
bytes=396200 groth16_vk_sha256=4388a21c…e696 circuit=v6.1.0` each time (cargo wall 104.7 s, 108.3 s, 123.0 s and 125.7 s, peak about 3.1 GiB); `zkdiff-verify --identity` printed the
pinned identities; the standalone verifier built offline in 15 s and printed `VERIFIED` for row 600; `zkdiff-verify --proof-bytes`
accepted row 600 under the frozen identities with 35 of 35 checks PASS. The same layout had first reproduced the ELF on the
development machine with a scratch `CARGO_HOME`. The kit is third-party material under its own licences (`BUILD_KIT.md` section
7); the `sp1-gpu-server`, `cargo-prove` and succinct toolchain tarballs carry no licence file and are redistributed as Succinct
released them **[confirm]**.

## 2a. Verify with nothing installed: the offline capsule

`capsule/` holds `zkdiff-verify` and the standalone verifier as statically linked x86_64 Linux executables built from this
package's source (the fail-closed rebuild record is `capsule/BUILD_RECORD.txt`; the relink, `capsule/STATIC_LINK_RECORD.txt`),
the pinned program key, the pinned circuit key file, the frozen expected identities and copies of the 112 proofs and
statements. One script runs both routes of sections 1 and 2 on all 112 proofs, the controls and the raw form, with bash and
coreutils only, no network and no other file:

```
bash "$P/capsule/verify_offline.sh"
```

Exit 0 means 112 of 112 accepted by `zkdiff-verify` under every frozen identity and 112 of 112 `VERIFIED` by the standalone
verifier; the script prints one line per row with the residual sums to compare with `RESULTS.md` section 6. Rehearsed on the
development machine and in a fresh `ubuntu:22.04` container with `--network none` and no Rust, Python or curl (about three and a
half minutes; `capsule/README.md`). A reader who does not want to trust a shipped binary rebuilds it (section 2 or
`replicate/replicate.sh build`), which reproduces the pinned ELF and key from the published source, and runs the same checks.

`capsule/reexecute/` carries the static batch driver, the raw frame and the oracle inputs of row 600, and a script that
recomputes a row's 752-byte statement from its raw frame (the complete guest program run in the SP1 executor on the CPU,
executed but not proved, and checked against the host's native re-evaluation; about 17 GB of RAM, 4 to 7 minutes) and compares
it with the published one; with a frame downloaded from the data layer (`FRAMES.md`) it does so for any row:

```
bash "$P/capsule/reexecute/reexecute_row.sh"                                     # row 600, the shipped frame
bash "$P/capsule/reexecute/reexecute_row.sh" 684 --frames-dir /path/to/frames    # any row 600..711
```

Rehearsed for row 600 on the development machine and in the same container, and for the mirrored row 684 from the published
frame set (section 9). The batch driver refuses a frame whose BLAKE3 differs from the chain log's before it runs anything.

## 3. Read a statement

```
python3 "$P/tools/decode_zbdiff01.py" "$P/public_values/row_000600_public_values.bin"
```

Standard library only; prints the fields of `STATEMENT.md` section 2 as JSON and exits 0 when the framing is consistent
(magic, ABI, protocol, length, fixed noising constants, `D = R_wrong - R_correct`, sign, clip flag). The fields that
matter: `row`, `wrong_row`, `offset`, `offset_rule`, `r_correct`, `r_wrong`, `difference`, `outcome_class`,
`clip_events`, `noise_blake3`, `raw_blake3`, `constants_sha256`. Compare them with the receipt's `decoded` object and
with the row's line in `RESULTS.md`; the acceptance verifier of section 2 makes the same comparison against the frozen
table, so the decoder is for reading, not for acceptance. To make every such comparison at once, for all 112 statements,
against the frozen identities, the chain log (rows r, u and r-1), the receipts and `PINS.json`, with the rule recomputed from
the row number:

```
python3 "$P/tools/check_identities.py" "$P"
```

Standard library only; exit 0 only if every field of every statement agrees (rehearsed: 112 of 112). It verifies no proof; it
is the identity half of section 2 for a reader without a binary.

## 4. Check the pinned identities by hand

```
sha256sum "$P/source/expected_identities_august.json"          # 182870aa06f11e246a76f8c94c5a1c40aed7b3ad4b3537420422f426dcd46eb2 (the published copy; the receipts name the frozen file's 6822cdce…d613, which differs only in the redacted paths of its sources block, HASHES.md)
sha256sum "$P/source/blobs/final_int16/constants_int16.blob"   # 73310ddab603cab5588d05e9ac4deb7e56466a6fae4bbf89244c32f2bd1a8b92 (3,476,866 bytes)
b3sum --no-names "$P/source/vectors_relation/august/chain_log.csv"   # 754e5716e65a065e5ad3146131609a1fd12e8310d966fb6bf2d3de6c568e7f8b
b3sum --no-names "$P/source/noise_august/noise_000600.i16"           # bd4d83ec376a69908df28372878c50f8458ce328a068eea158ef2b30767f41ad
```

Without `b3sum`, the Python `blake3` module gives the same digests (rehearsed with blake3 1.0.8):

```
python3 -c 'import blake3, sys; print(blake3.blake3(open(sys.argv[1], "rb").read()).hexdigest())' "$P/source/vectors_relation/august/chain_log.csv"
python3 -c 'import blake3, sys; print(blake3.blake3(open(sys.argv[1], "rb").read()).hexdigest())' "$P/source/noise_august/noise_000600.i16"
```

The per-row noise digests for all 112 rows are `PINS.json` `noise_files` and `source/expected_identities_august.json`
`rows[r].noise_blake3`; the statement's byte 660 to 691 must equal the row's entry, and the acceptance verifier enforces
it. That the published noise bytes follow their stated rule (`STATEMENT.md` section 8) is checked by regenerating them:

```
python3 "$P/tools/regen_noise.py" "$P"
```

numpy only (the `blake3` module optional); it re-derives all 112 tensors from the Philox rule, compares the bytes with
`source/noise_august/`, the SHA-256 with `PINS.json` and, with the module, the BLAKE3 with the statements (rehearsed: 112 of
112 equal, under a second). The chain log is byte-identical to the ZeeBeam release's `bundle/proofs_20260902/final_relation/chain/chain_log.csv`
(SHA-256 `5d9af297ae37119df15412f516a4543ee9f54b6aa66186abe478512fe9a1ff48`), and the session identities in every
statement (id `ZEEBEAM_MAINNET_BLOCKING_TRAINING_300S_20260822_001`, 712 rows, depth 10, `S_0` `74e3a131…384c`, `S_N`
`aeea9f4d…398e`, authority manifest `740d752d…d783`, chain-log BLAKE3 `754e5716…7f8b`, context `f5eba65f…1ee0`, root
`38a484b8…6572`) equal the ZeeBeam release's `PINS_final.json` session record. Each statement's two drand rounds are the
chain log's rounds for rows `r-1` and `r`; the chain log carries the beacon signatures the guest verified, and the public
quicknet schedule (chain `52db9ba70e0cc0f6eaf7803dd07447a1f5477735fd3f661792ba94600c84e971`) is the out-of-band check
that a round's signature is the one the relay published, which no proof can do for you: the public relay serves a round as
`https://api.drand.sh/<chain hash>/public/<round>` (round, randomness, signature) and the chain's public key as
`https://api.drand.sh/<chain hash>/info`; compare the signature with the chain log's `drand_signature_hex` and the key with
`PINS.json` `drand.quicknet_public_key_hex` (not exercised from this package: it needs the network). Most consecutive rows
share a round; `STATEMENT.md` section 1a says what the two verified beacons are and are not. The digests the statements
publish for the raw frame and both emissions are the chain log's `bayer_blake3_hex` and `emission_live_pixel_blake3_hex`
columns for rows `r` and `u`, the rounds its `drand_round_number` column and the verified signatures its
`drand_signature_hex` column (the file's first line is a comment naming the session's start time; the header is its
second line); the frames of the proof rows 600 to 711 are published (`FRAMES.md`, which also says what they show).

## 5. Rebuild the program and its key

Section 2's `build_reproducible.sh` is the rebuild. What it fixes and records is in `PINS.json` `reproducible_build`:
the four lockfiles (unchanged before and after), the frozen source digest list, the host and guest compiler identities,
`--locked`, the inherited offline configuration, the two `--remap-path-prefix` flags and `-Cstrip=symbols` (the symbol
table is never loaded by the zkVM; stripping it made the file hash independent of the tree's absolute path). The pin was
reproduced byte for byte on the development machine, in a copy of the sources at another absolute path
(`source/logs/probe_build_other_absolute_path_20260907.log`), on the rented node before the batch
(`source/node_prep/r5/build_record_20260907T215855Z.txt`, the record every batch manifest and receipt names, with its
source digest list beside it and the summary `node_build_r5_summary.txt`), and twice more on 8 September 2026 from
copies of this published tree (section 9). To see the values a build produces without asserting them, run the driver
with `--pin`. Two comment-only substitutions in `source/armc-relation/script/src/ceremony.rs` and `ceremony_core.rs`
(`REDACTION.md`) make the published source digest list differ from the private one in those two lines; the compiler
ignores comments and the driver asserts the ELF, so the rebuild is the check.

## 6. Oracle parity: the Rust kernels against the Python oracle

The Rust integer network was accepted against the Python oracle's exported vectors before anything was proved
(`RESULTS.md` section 4). To rerun those tests, place the data-layer files at the paths `LARGE_FILES.md` gives
(`source/oracle_final/` for the eight export sets, d2 and August; the August four were held in the earlier revision and are
published since 8 September 2026), then:

```
(cd "$P/source/armc-int" && cargo test --release --offline)
(cd "$P/source/armc-relation" && cargo test --release --offline --no-fail-fast)
```

What to expect with all eight export sets placed: `armc-int` 25 of 25 and `armc-relation` 59 of 59 pass (section 9). With the
d2 sets only, as the afternoon rehearsal ran: `armc-int` runs 25 tests, 24 pass and `final_artifact_pins` fails at
`oracle_final/int16_august_650_correct/index.json: No such file or directory`, because that test iterates over all eight
FINAL export sets; `armc-relation` runs 59 tests, 57 pass and the two adapter parity tests
`final_blob_through_the_adapter_reproduces_the_final_exports` and `final_vectors_layer_by_layer_parity_d2_1328_and_august_650`
fail with `oracle_final/int16_august_650_correct missing`, for the same reason. Everything else passes either way: the 42
boundary fixtures, the relation vectors, the synthetic sessions, the mirrored row 684's prepared witness
(`source/armc-relation/runs/batch_prepare_g2d_20260907/row_000684/witness/`, run against a synthetic frame), the `b3xof` crate
and the cross-checks. To see the two suites pass as a whole without the August sets, skip the three tests that need them:

```
(cd "$P/source/armc-int" && cargo test --release --offline -- --skip final_artifact_pins)
(cd "$P/source/armc-relation" && cargo test --release --offline -- --skip final_blob_through_the_adapter_reproduces_the_final_exports --skip final_vectors_layer_by_layer_parity_d2_1328_and_august_650)
```

Rehearsed: 24 passed, 0 failed, 1 filtered out, exit 0; 57 passed, 0 failed, 2 filtered out, exit 0. With the eight sets
present the suites ran complete as 25 and 59 passing tests, on 7 September (`source/logs/test_armc_int_r5.log`,
`source/logs/test_relation_r5_pass*.log`) and again on 8 September on the published tree (section 9). `ARMC_ORACLE_DIR` points the kernel
tests at another export root. The relation tests that would read `frames_august/frame_000600.raw` fall back to a
synthetic frame by design (`relation/tests/vectors.rs` `mirror40_frame`), so no frame is needed.

The four d2 export sets can be regenerated from the vector sets instead of fetched. The exporter needs Python 3 with
numpy and torch (torch only for the GELU reference; rehearsed with torch 2.11.0 and numpy 2.3.5) and the oracle's
`kernels.py`, which it finds under `oracle/` in this layout (`REDACTION.md`):

```
(cd "$P/source" && python3 -B tools/export_oracle.py --src "$P/oracle/final/vectors" --out /tmp/oracle_final_regen)
```

Rehearsed for the d2 sets: the four sets are produced (482 arrays each, 474 hashes checked against the manifests, 8 clipping
masks; the int8 pair's residual sums 9,006,417,833 and 22,578,064,838 as recorded in the manifests); every array file is
byte-identical to the data-layer copy under `source/oracle_final/`, and only `index.json` differs, in its recorded absolute
source paths and in the exporter's self-description fields, which the published export predates. The August vector sets are
on the data layer since 8 September 2026 and the same exporter regenerates their export sets **[confirm]**.

## 7. Regenerate the oracle from the checkpoint: what the public rows allow

`oracle/freeze_artifact.sh <ckpt.pt> <pubproto_eval.json> <raw_npz_dir> <out_dir> [stage]` is the one-command driver
that generated the G1 artifact (`oracle/final/README_FINAL.md` section 0). In this layout the checkpoint, the evaluator
summary and the raw scores are under `model/`, the trainer under `oracle/trainer/` (the oracle imports the model class
from `train_lean.py` there; `REDACTION.md` lists the import-path adaptation) and the cached rows the evaluator scored
are the data-layer files `oracle/rows/` (d2, v10) and `oracle/rows_august/` (the August emission rows). It needs Python 3
with torch and numpy on a CPU (rehearsed with torch 2.11.0, numpy 2.3.5, Python 3.14).

What the files allow. The frozen scale map in `oracle/final/constants_int16.json` was calibrated on 15 rows, 7 of them August
rows (`oracle/final/runlogs/selfcheck_int16.log`: `calibrated on 15 rows (7 august)`), and that calibration reads the August
camera-derived rows (`rows_august/.../C_*.npy`), which the earlier revision of this package held and which are on the data
layer since 8 September 2026 (`LARGE_FILES.md`). Without them the oracle cannot recompute that map: a run on the d2 and v10
rows alone recalibrates on 8 rows and yields a different one (rehearsed: `calibrated on 8 rows (0 august)`, scale histogram
`{7: 1, 8: 1, 9: 21, 10: 17, 11: 95, 12: 41, 13: 7, 14: 5}` against the frozen
`{7: 1, 8: 1, 9: 22, 10: 26, 11: 89, 12: 38, 13: 6, 14: 5}`). With them placed, `python_oracle_rows.py` (below) recalibrated on
the 15 rows, 7 August, and reproduced the residual sums of rows 600 and 684 (section 9). The frozen constants are loaded, never
recomputed, by every consumer in this package: the constants blob (`source/blobs/final_int16/constants_int16.blob`, hashed in
circuit and pinned), the Rust tests and the guest; `source/tools/export_oracle.py` checks the exported tables against the
artifact's manifests rather than regenerating them. The 185-pair and 507-pair agreement studies of `RESULTS.md` section 3 rest
on that frozen map; their records are the artifact's `agreement*.json`, `AGREEMENT.md` and `FREEZE_SUMMARY.md`, and with the
data-layer rows placed the whole artifact regenerates (`run_final.sh`, end of this section).

What a third party can run with the repository alone, and what it reproduces: the float positive control on the 37 protocol
rows (fp32 and the two bf16 emulations against the evaluator's per-row scores in `model/pubproto_raw/`), which needs only the
d2 and v10 rows and reproduces the d2 and v10 figures of `oracle/final/float_repro.json`; the kernel self-test and the integer
forward with `--no-august-calib`, a code-path check under an unfrozen map; and the differential boundary fixtures, which derive
from the scalar oracle and need no camera row. With the data-layer files placed, the Python oracle recomputes any proof row's
residual sums from the published input arrays (`oracle/final/august_inputs/row_NNNNNN.npz`: `C_int`, `noise_int`, `Ct_int`,
`E_correct`, `E_wrong`), independently of the Rust code:

```
(cd "$P/source" && python3 -B tools/python_oracle_rows.py 600 684)
```

Rehearsed on 8 September 2026 (torch 2.11.0, numpy 2.3.5, Python 3.14, 11 s): the positive control on d2 1328 reproduced,
then row 600 `R_correct` 4,435,539,299 and `R_wrong` 11,254,163,581, row 684 4,587,519,841 and 11,036,216,072, equal to the
statements; the script writes its record to `source/runs/python_oracle_rows_<stamp>.json`, so run it on a copy if you keep the
package ledger clean.

```
export G1_CKPT="$P/model/g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pt" \
       G1_REF_JSON="$P/model/g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pubproto_eval.json" \
       G1_RAW_DIR="$P/model/pubproto_raw" G1_OUT=/tmp/oracle_regen OMP_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1
mkdir -p "$G1_OUT"
(cd "$P/oracle" && python3 -B float_repro.py --out "$G1_OUT/float_repro.json")
(cd "$P/oracle" && python3 -B int_ref.py --scheme int16 --no-august-calib)
(cd "$P/oracle" && ./freeze_artifact.sh "$G1_CKPT" "$G1_REF_JSON" "$G1_RAW_DIR" "$G1_OUT/artifact" selfcheck)
```

Rehearsed: the float control ran in 8 s over `0 august rows`, giving d2 correct 0.010910 under the bf16 emulation
against the evaluator's 0.011047 and delta 0.022224 against 0.022409, v10 correct 0.012517 against 0.012673, paired
1.000 throughout, bf16 emulation against fp32 relative mean +3.3e-3, as `oracle/final/float_repro.json` records;
`int_ref.py --no-august-calib` passed the kernel self-test and the integer forward (score f64 0.012132, int 0.012149,
relative +1.4e-3, no clip events); `freeze_artifact.sh` detected the absent August rows, said so, ran `selfcheck` with
`--no-august-calib` and, asked for `agreement`, skipped it with the reason printed. The driver skips `agreement`,
`vectors`, `report`, `august` and `summary` whenever the August rows are absent. With the data-layer rows placed,
`oracle/final/run_final.sh` regenerates the whole artifact, about 25 minutes on the development machine (the run of 7
September that produced the published artifact; not repeated on the published tree **[confirm]**).

## 8. What the proof says, and what it does not

Under the pinned verifying key, ELF and constants, an accepting proof establishes that the published `R_correct`,
`R_wrong` and their difference are what the frozen integer denoiser produces on the whole-frame reduction of the raw
frame whose BLAKE3 digest is bound into the session tree at row `r`, noised with the noise whose BLAKE3 is published, under
the row's own emission and under the declared wrong row's emission, both re-derived from chain states that the verified
quicknet beacons seeded; and that the clip count is what that computation counted. It establishes nothing about a
camera, a scene, a person, realness, liveness, illumination causality, adversarial resistance or another session.
`CLAIM_BOUNDARY.md` is the complete statement of the boundary.

## 9. Rehearsal record (8 September 2026)

The following table records the commands and data available during the afternoon rehearsal of 8 September 2026 on the
development machine, against a copy of the published tree of that hour with the data-layer files placed at their
package-relative paths, after the round-6 audit asked for it; the evening tables record what was added and rehearsed later. A historical note on that copy: between it and the round-6 revision only this document,
the round-6 records (`REDACTION.md`, `AUDIT_TRAIL.md`, `PINS.json`, the ledger) and the row-684 witness directory the
rehearsal itself showed to be missing changed, and the proofs, statements, source, oracle and model were the same bytes. The privacy
sweep of the same evening (Astra round 7) then changed text files under `source/` and `oracle/` and the checkpoint under `model/`
(recorded paths redacted, the checkpoint a documented derivative: `REDACTION.md`, `REDACTION_LEDGER.tsv`); the proofs and
statements are unchanged since, and the ELF rebuilt from the redacted sources reproduced the pin (section 2b, second run). Environment:
Ubuntu 26.04, rustc and cargo 1.98.0, `cargo-prove sp1 (f66b4bf 2026-08-12)` with succinct rustc 1.94.0-dev, libprotoc
3.21.12, Python 3.14 with torch 2.11.0, numpy 2.3.5 and blake3 1.0.8; the cargo home already held every locked crate,
so every cargo step ran offline.

| step | outcome |
|---|---|
| 0 ledger, large files | every listed file verified, count equal; `LARGE_FILES_SHA256SUMS` verified over the 2,500 placed files |
| 1 standalone verifier | built in 13 s (`--locked --offline`); row 600 `VERIFIED` with `tamper_public_byte_87_rejected=true` and `wrong_vkey_rejected=true`; all 112 raw proofs `VERIFIED` in 2 min |
| 2 fetch | both `cargo fetch --locked --offline` resolved, so the lockfiles are complete against the cached registry; a fetch from an empty cargo home was not rehearsed (network) |
| 2 build | `BUILD_REPRODUCED_OK`: ELF 396,200 bytes `51b7bc35…75cc`, vkey `0x00f01894…a027`, embedded circuit key `4388a21c…e696`, no host path in the ELF; cargo wall 77 s at 16 jobs, peak 3.2 GB; a second cold build the same afternoon from a copy of `source/` alone gave the same values in 80 s |
| 2 verify | `--identity` as stated; row 600 accepted with every check PASS (report kept); the raw form accepted; all 112 proofs accepted in 26 s; `--controls` exit 0, every control behaved |
| 3 decoder | fields printed as JSON, exit 0 |
| 4 pins by hand | the two SHA-256 values as stated; `b3sum` is not installed on the release machine, so the two BLAKE3 values were taken with the Python `blake3` module and equal the pins |
| 6 tests | `armc-int` 24 of 25 pass, `armc-relation` 57 of 59 pass; the three failures read the August export sets, not yet on the data layer at that hour; with those three skipped, 24 and 57 pass and both suites exit 0 (the row-684 witness test had failed on the first copy for want of its witness directory, since added) |
| 6 exporter | four d2 sets regenerated from the vectors, array files byte-identical to the data-layer copies, `index.json` differing only in recorded source paths and exporter self-description |
| 7 oracle | float control reproduced (8 s); `int_ref.py --no-august-calib` self-test and forward passed with an unfrozen scale map, as section 7 states; `freeze_artifact.sh` announced the absent August rows, ran `selfcheck` and skipped `agreement` |

The evening of the same day, after the outside-agent readability audits (the first reading, A1) and the principal's decision to publish the
frames and the August tensors:

| step | outcome |
|---|---|
| 2a capsule, development machine | `verify_offline.sh`: 112/112 accepted by the static `zkdiff-verify`, 112/112 VERIFIED by the static standalone verifier, 18 controls behaved, raw form accepted, copies equal the package's (3 min 25 s) |
| 2a capsule, fresh `ubuntu:22.04` container, `--network none`, no Rust, Python or curl, uid 1000, read-only mount | the same counts (3 min 25 s) |
| 2a re-execution, row 600 (shipped frame), development machine and the same container | `R_correct` 4,435,539,299, `R_wrong` 11,254,163,581, `D` +6,818,624,282, 14,400,363,198 instructions, statement byte-identical (3 min 52 s; 3 min 45 s) |
| 2a re-execution, row 684 (mirrored -30) from the published frame set, development machine | offset -30 mirrored, wrong row 654; `R_correct` 4,587,519,841, `R_wrong` 11,036,216,072, `D` +6,448,696,231, 14,400,373,541 instructions (the node's count for the same row), statement byte-identical (3 min 50 s) |
| 3 identities | `tools/check_identities.py`: 112/112 statements agree with the frozen identities, the chain log, the receipts and `PINS.json` on every field; 103 share a round with the predecessor row |
| 4 noise rule | `tools/regen_noise.py`: 112/112 tensors regenerated from the rule equal the published bytes, the `PINS.json` SHA-256 and the statements' BLAKE3 (0.5 s) |
| 6 tests with all eight export sets placed (the August sets from the data-layer staging) | `armc-int` 25 passed, 0 failed; `armc-relation` 59 passed, 0 failed; both suites complete, no test skipped |
| 7 Python oracle with the data-layer files placed | `python_oracle_rows.py 600 684`: calibration on 15 rows (7 August); d2 1328 control 8,764,459,045 / 22,311,372,969; row 600 4,435,539,299 / 11,254,163,581; row 684 4,587,519,841 / 11,036,216,072 (11 s) |
| the one-pull kit | `replicate/replicate.sh all --no-prove` from an empty `ubuntu:22.04` container: fetch, toolchains, build reproducing the pins (2 min 44 s), verify 112/112, standalone 112/112, execute row 600 byte-identical, parity 81 passed and 3 absent (the August sets were not yet on the data layer at that hour); `replicate/TEST_LOG.md` |

Later the same evening, after the privacy sweep (Astra round 7) asked for the capsule binaries to be rebuilt with every dependency
under a path remap, and the confirmation re-read (round 8) and the outside agents' second reading were applied:

| step | outcome |
|---|---|
| 2a capsule, remapped static rebuild, development machine | `verify_offline.sh` on the three rebuilt binaries: 112/112 accepted by `zkdiff-verify`, 112/112 VERIFIED by the standalone verifier, 18 controls behaved, raw form accepted, copies equal the package's (2 min 52 s) |
| 2a re-execution, row 600 (shipped frame), development machine | `R_correct` 4,435,539,299, `R_wrong` 11,254,163,581, `D` +6,818,624,282, 14,400,363,198 instructions, statement byte-identical (3 min 27 s) |
| 2a re-execution, row 684 (mirrored -30) from the published frame set, development machine | offset -30 mirrored, wrong row 654; `R_correct` 4,587,519,841, `R_wrong` 11,036,216,072, `D` +6,448,696,231, 14,400,373,541 instructions, statement byte-identical (3 min 28 s) |
| 2a capsule, remapped static rebuild, fresh `ubuntu:22.04` container, `--network none`, no Rust, Python or curl, uid 1000, read-only mount | `verify_offline.sh`: the same counts, 18 controls (2 min 38 s) |
| 2a re-execution, row 600 (shipped frame), the same container, `--network none`, the package mounted read-only | the same numbers, statement byte-identical (3 min 24 s) |
| 2b offline build kit, fresh `ubuntu:22.04` container, `--network none` | `BUILD_REPRODUCED_OK`, ELF `51b7bc35…75cc`, vkey `0x00f01894…a027`, cargo wall 104.7 s, 108.3 s, 123.0 s and 125.7 s over four runs, the fourth against this revision's frozen sources (inventory `24efb517…4a9d`, shipped); standalone verifier built offline, row 600 `VERIFIED`; `zkdiff-verify` accepted row 600, 35 of 35 checks (160 s, 164 s, 187 s and 189 s in all; `build_kit/offline_build_test/`) |

Later still, the same evening, the one-pull kit was run on a machine that had none of this installed: a freshly launched Lambda
`gpu_1x_a100_sxm4` instance (Ubuntu 22.04.5, kernel 6.8.0-60-generic, glibc 2.35, 30 threads, 216 GiB RAM, one NVIDIA
A100-SXM4-40GB, driver 570.148.08; no Rust, SP1 or protoc), against a local copy of the package as staged at 16:50Z that day
(3,092 ledger entries; every pin the run checked is a pin of this revision, and the proofs, source, ELF, noise, chain log,
constants and frames are the same bytes; what changed after that hour is the redacted copies, the capsule rebuild, the build
kit, the audit texts and the papers). `replicate.sh all --repo-only --from-local … --frame …` ran end to end in 62m26s. The
earlier timing pilot and the batch ran on 80 GB cards (`RESULTS.md` sections 5 and 6). The full log, redacted by the same rule
as every other copied record, and the run's small artefacts are `replicate/TEST_LOG_LAMBDA_A100.md` and
`replicate/lambda_a100_20260908/`.

| step | outcome |
|---|---|
| fetch (local copy), ledger and pins | 3,092 entries present and matching, no unlisted file; every pin agrees between the script, `PINS.json` and the frozen files (2 s) |
| toolchains | rustup 1.29.1, rustc and cargo 1.98.0, `cargo-prove sp1 (f66b4bf 2026-08-12)`, the succinct toolchain (rustc 1.94.0-dev, LLVM 21.1.8), protoc 21.12 and b3sum 1.8.7, each download at its pinned sha256 (27 s) |
| build (CPU features) | `BUILD_REPRODUCED_OK`: ELF `51b7bc35…75cc`, 396,200 bytes, vkey `0x00f01894…a027`, circuit key `4388a21c…e696` (2m34s) |
| verify | 112/112 accepted by `zkdiff-verify` under the pinned key, circuit and constants; controls behaved; 112 noise files match `PINS.json` (0m52s) |
| quick | 112/112 `VERIFIED` by the standalone verifier, both tamper controls rejected per proof (3m25s) |
| execute row 600 (the row's frame, passed with `--frame`) | `R_correct` 4,435,539,299, `R_wrong` 11,254,163,581, `D` +6,818,624,282; 14,400,363,198 instructions, 269,904 syscalls, max RSS 17,447,080 kB; 33 acceptance checks PASS; 752 public bytes byte-identical to the published statement (6m59s, the frame-independent legs included) |
| CUDA prover install and rebuild | `sp1-gpu-server` 6.4.0 (tarball `2946b0b4…c596`, binary `f68b85dc…d97c`); the Groth16 v6.1.0 circuit cache fetched (6,211,807,514 bytes, tarball `18beebb6…7810`, its seven files at their pinned identities); the rebuild with the `cuda` feature reproduced the same ELF and key (1m23s) |
| prove row 600 on device 0 | a fresh Groth16 proof, 2,446 bytes wrapped (356 raw), sha256 `a381b80b…8be`; `prove_elapsed_ms` 2,539,814 (42.3 min), setup 1,249 ms, 15,972,262 constraints; GPU memory peak 28,435 MiB of 40,960, `zkdiff-batch` max RSS 7,353,628 kB; verified and accepted cold under the pinned identities, all 35 checks; its 752 public bytes byte-identical to the published statement, the proof bytes differing as Groth16 proofs are randomised; the pinned `sp1-cuda` client exited 134 from its destructor panic after the manifest and receipt were written, as in every observed run (`FAQ.md` 61) (43m06s) |

Limitations, plainly: proving is not part of verification; it was rehearsed once from the package alone, on the rented
A100-SXM4-40GB above (row 600, 43 min), and remains a route for a reader with such a card (`replicate/README.md`); the full oracle
regeneration with the August rows placed and the export of the August sets were not repeated on the published tree **[confirm]**.

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-07 | BOSUN | First version, drafted before the proof batch; routes 1, 2 (fetch step), 6 and 7 carry [confirm] tags as stated. |
| 1.1 | 2026-09-08 | BOSUN | Astra round 6 (findings 6, 7, 8): every command anchored to the package root `P`; the complete requirements (protoc and its includes, GNU time, binutils, the blake3 alternative); the standalone verifier vendored at a pinned commit; the oracle regeneration claim narrowed to the public rows and the driver's behaviour without the held rows stated; every route rehearsed on a copy of the published tree and recorded in section 9. |
| 1.2 | 2026-09-08 | BOSUN | Agent audits round 1 and the principal's publication decision: the three routes by what is installed; the offline capsule (2a) and the re-execution of any row from its published frame; toolchain download sources and digests; the corrected fetch commands and the empty-cargo-home rehearsal (replicate/); count assertions; the ledger check that tolerates build outputs and data-layer files; identities and noise-rule tools; the drand out-of-band check named; sections 6 and 7 on the published August sets; the evening rehearsals. |
| 1.3 | 2026-09-08 | BOSUN | Astra rounds 7 and 8 and the agents' second reading: the offline build kit (2b) and its network-less rehearsal; the three remaining [confirm] steps named where they stand; the C compiler, linker and pkg-config in the requirements; Go stated one way; the re-execution described as the guest in the SP1 executor; the frames' publication; the expected identities' published digest; the rehearsal record's wording and the round-8 capsule rows. |
| 1.4 | 2026-09-08 | BOSUN | The fresh-machine replication on a rented Lambda A100-SXM4-40GB (8 September, 17:05Z to 18:07Z) added to section 9 with its log and artefacts under `replicate/`; the GPU prove path no longer carries [confirm]; two [confirm] steps remain (sections 6 and 7). |
| 1.5 | 2026-09-08 | BOSUN | Astra round 9: the offline kit re-run against this revision's frozen sources (second run, its source inventory shipped); the kit's file count, bytes and manifest digest; the upstream binaries' path strings stated; the afternoon-rehearsal note made historical (source, oracle and model changed in the privacy sweep). |
| 1.6 | 2026-09-08 | BOSUN | Astra round 10 and the third outside reading: the two-part publication stated up front; a renamed copy noted at P=; the eight policy-only rows; the first outside reading named as such; the offline kit test's fourth run (two host-source comment lines changed by the release-step wording; the third run had used an incompletely adapted staging copy) recorded in 2b and section 9. |
| 1.7 | 2026-09-08 | BOSUN | Astra round 11: which inventory sits only in the bundle's manifest; the kit manifest digest refreshed after the write-up's size correction. |
