---
version: 1.2
updated: 2026-09-08
status: active
author: BOSUN for Cathal Ryan Hynes
---

# Replicate the zkdiff August proofs yourself

Hoy. BOSUN here. This directory is the one-pull path through `proofs/zkdiff_august_20260907/`: one script and one Dockerfile
that fetch the package, check every byte against its ledgers, verify all 112 proofs, rebuild the proved program to its pinned
ELF and key, run the guest on the CPU, and, on a GPU with the right input, make a fresh proof. Nothing here asks for a login or
a favour. Every download is checked against a SHA-256 pinned in `replicate.sh` or in the package's own `SHA256SUMS`,
`LARGE_FILES_SHA256SUMS` and `PINS.json` before it is used, every step prints what it checked, and the first mismatch exits
non-zero. The claim these proofs make, and the claim they do not, is `../CLAIM_BOUNDARY.md`; nothing below widens it.

## The ladder, shortest first

| rung | command | what it establishes | needs | about how long |
|---|---|---|---|---|
| ledger | `replicate.sh fetch` | the package you hold is the package: every `SHA256SUMS` entry matches and no file is unlisted; every pin in this script agrees with `PINS.json`, the expected identities, the constants blob and the chain log; the data-layer objects match `LARGE_FILES_SHA256SUMS` and the prefix's own `_control/` ledgers | curl, git, python3 | under a minute plus the 633,286,043 bytes of data-layer files (`LARGE_FILES.md`), plus any raw frame downloaded |
| quick | `replicate.sh quick` | each of the 112 Groth16 proofs verifies under the pinned program key `0x00f01894…a027` with the circuit key embedded in `sp1-verifier` 6.4.0, and rejects a flipped public byte and a wrong key; this is the seconds-per-proof check that needs only the raw proof, the 752 public bytes and the key | stable Rust only (installed for you) | 2 to 3 minutes to build the verifier, then well under a second per proof |
| build | `replicate.sh build` | the published source is the proved program: the pinned SP1 6.4.0 toolchain rebuilds the guest from `source/` with the locked dependencies and the driver asserts ELF sha256 `51b7bc35…75cc`, 396,200 bytes, vkey `0x00f01894…a027` (derived from the rebuilt ELF), embedded circuit key `4388a21c…e696` (v6.1.0) | the toolchain downloads below | rehearsal numbers in the table further down |
| verify | `replicate.sh verify` | all 112 proofs are accepted by the package's own `zkdiff-verify`: Groth16 under the pinned key and circuit, then every frozen identity (program, constants, spec and preprocessing digests, session, rule, the row's normative noise BLAKE3, chain-log digests, drand rounds, leaves, expected residual sums); a 112-line table, the negative controls on row 600, the raw 356 + 752 byte form, and the noise files and chain log by sha256 and BLAKE3 | build | a minute or two |
| execute | `replicate.sh execute ROW [--frame PATH]` | with the row's raw frame: the complete guest re-executes on the CPU and its 752 public bytes are byte-identical to the published statement (`R_correct`, `R_wrong`, `D`, every digest). The frame is `--frame PATH`, else the frame of row 600 shipped in `capsule/reexecute/`, else the row's published frame fetched from the data layer and checked against `FRAMES.md`; if none can be had, the frame-independent legs of that row run natively (beacons verified and bound, chain advance and both emission renders reproduce the chain log, noise BLAKE3 equals the frozen table), then the complete guest runs on the shipped synthetic session | build; a frame (shipped for row 600, published for every row) | 6 to 7 minutes and 15 to 17 GB of RAM for one row; about 4 minutes for the synthetic session |
| parity | `replicate.sh parity` | the Rust integer kernels and the relation agree with the Python oracle's exported vectors layer by layer (`cargo test` in `armc-int` and `armc-relation`); with the data-layer files placed every test passes (25 and 59); a test whose data-layer file is not in place is reported as ABSENT, not failed, and everything else must pass | the data-layer files | a few minutes |
| prove | `replicate.sh prove ROW --device N [--frame PATH]` | the whole pipeline: a fresh Groth16 proof of the row on your GPU, accepted cold under the pinned identities, with public bytes identical to the published statement (the proof bytes differ, Groth16 is randomised); the frame as for `execute` | a CUDA GPU, the 5.8 GiB circuit cache, the row's frame (shipped for row 600, published for every row) | 46 minutes on one A100-SXM4-80GB in the timing pilot; 61 to 67 minutes per row when eight shared the node |

`replicate.sh all` runs fetch, build, verify, quick, execute (row 600 from its shipped frame), parity, and prove when a GPU is
present (row 600, the same frame).

## One pull

### A laptop or any Linux box, no GPU

```
git clone --depth 1 https://github.com/poliebotics/dark-lantern
cd dark-lantern/proofs/zkdiff_august_20260907/replicate
./replicate.sh all --no-prove
```

Debian or Ubuntu packages the script needs and will not install for you: `curl git build-essential pkg-config time binutils
python3`. Everything else it installs into your home with pinned digests: rustup 1.29.1 and Rust 1.98.0 into `~/.cargo` and
`~/.rustup`, cargo-prove and the succinct guest toolchain into `~/.sp1`, protoc 21.12 into `~/.local`, b3sum from crates.io.
Work lands in `./zkdiff_replicate/` (override with `--work DIR` or `ZKDIFF_WORK`); the log is `zkdiff_replicate/out/replicate.log`.
Memory: the build wants a few GB; the CPU execution of a row 15 to 17 GB; verification almost nothing. Disk: about 8 GB for
toolchains, crates and build outputs, plus 633,286,043 bytes of data-layer files (4,664 files, `LARGE_FILES.md`) and 24,472,000 bytes per downloaded raw frame.

### A fresh Lambda A100 box (Ubuntu 22.04)

```
sudo apt-get install -y curl git build-essential pkg-config time binutils python3
git clone --depth 1 https://github.com/poliebotics/dark-lantern
cd dark-lantern/proofs/zkdiff_august_20260907/replicate
./replicate.sh all --no-prove                                        # every CPU route, row 600 from its shipped frame
./replicate.sh prove 600 --device 0                                  # row 600 from its shipped frame; any other row fetches its published frame
```

`prove` installs `sp1-gpu-server` 6.4.0 (tarball sha256 `2946b0b4…c596`, binary `f68b85dc…d97c`) and the Groth16 v6.1.0
circuit cache (6,211,807,514-byte download, seven files pinned by sha256) into `~/.sp1`, rebuilds the host with the `cuda`
feature (the driver asserts the same ELF and key again), and runs one row detached from nothing: run it under `setsid nohup`
if your SSH session may drop. The pinned `sp1-cuda` client returned a nonzero status during cleanup after the manifest and receipt
were written in every observed run; the script judges the run by the receipt and by a cold `zkdiff-verify` of the fresh proof, not by the exit code.
The observed footprint per row: GPU memory peak about 28.5 GiB, `sp1-gpu-server` RSS about 28 GiB, client RSS about 7 GiB, so
an 80 GB A100 (the batch and the pilot) and a 40 GB A100 (the fresh-machine rehearsal below, peak 28,435 MiB of 40,960) have
room, and a 24 GB part (A10, consumer cards) is below the observed peak and is expected to fail **[untested]**.

### Docker

```
cd dark-lantern/proofs/zkdiff_august_20260907/replicate
docker build -t zkdiff-replicate .
docker run --rm -v "$PWD/work:/work" zkdiff-replicate                       # = replicate.sh verify (fetch, build, verify)
docker run --rm -v "$PWD/work:/work" zkdiff-replicate replicate.sh all --no-prove
```

The image is Ubuntu 22.04 with the apt packages above and the same pinned toolchain the script installs on a bare machine
(the Dockerfile calls `replicate.sh toolchain sp1`, so the two cannot drift apart). Build it with `--build-arg UID=$(id -u)` if
your user is not uid 1000, so the files in `work/` are yours. For `prove`, build on a CUDA runtime base and pass the GPUs
through (`--build-arg BASE=nvidia/cuda:12.8.1-runtime-ubuntu22.04`, `docker run --gpus all`, the NVIDIA Container Toolkit on the
host); the GPU path in Docker is documented, not rehearsed **[untested]**.

## Little local proofs: what each step lets you say

- After `quick`: "this program key and this circuit key verify these 112 proofs". That needs no ELF, no SP1 toolchain,
  no trust in the prover; only `sp1-verifier` 6.4.0's embedded verifying key and the raw proof and statement bytes.
- After `build`: "the source in this package compiles to the ELF whose key verifies those proofs". The rebuild is offline
  and `--locked`, the lockfiles are compared before and after, the ELF is hashed and its key derived by `zkdiff-ceremony`, and
  no machine path is embedded. Together with `quick`, that is the whole binding from published source to accepted proof.
- After `verify`: "every statement carries exactly the frozen identities" (the acceptance verifier refuses a coherent
  statement about another session, another noise tensor, another constants blob or another rule), and the per-row residual sums
  in `RESULTS.md`, the receipts and `PINS.json` are the values to which the proofs commit.
- After `execute` on a real row: "the published residual sums are what the integer network produces on this frame". Where no
  frame can be had you still get the frame-independent legs of the row natively and the complete guest on the synthetic session,
  which exercises the same 14.4 G-instruction program end to end against the native re-execution and the Python oracle.
- After `parity`: "the Rust kernels compute what the Python oracle computes" on the published vectors, layer by layer.
- After `prove`: "I made one of these proofs myself and it says the same thing".

## Honest limits

- **The raw frames of the proof rows are published** (`../FRAMES.md`, the data layer). Executing or proving a real August row
  needs its frame: pass `--frame PATH`, or let the script use the frame of row 600 shipped in `../capsule/reexecute/` or fetch the
  row's published frame and check its SHA-256 against `FRAMES.md`; the batch driver then checks its BLAKE3 against the chain log
  before anything runs. A GPU alone cannot prove an August row; a GPU and a frame can.
- **The August camera-derived tensors are published on the data layer** (`../LARGE_FILES.md`), so with the data-layer files
  placed every parity test passes (25 and 59). A test whose data-layer file has not been placed (`int16_august_650_*`,
  `int8_august_650_*`) is reported as ABSENT, not as passing. The offline build kit on the data layer (`build_kit/`) carries the
  vendored crates and the pinned toolchain downloads, so the rebuild can run with no network.
- **What remains external**: the Rust channel (rustup's signed manifests), the SP1 6.4.0 release assets on GitHub (cargo-prove
  and the guest toolchain, both pinned here by sha256), the Groth16 v6.1.0 circuit cache on Succinct's S3 bucket (the seven
  files pinned by sha256; the tarball itself is recorded, not pinned), protoc from the protobuf releases (pinned), and
  crates.io for the locked dependencies (each crate is checksummed by its lockfile entry). If any of these disappears, the
  script fails closed and says which.
- **One nested build inside SP1.** The host binaries embed a helper executor binary that `sp1-core-executor-runner` 6.4.0
  builds from a nested cargo tree inside the registry copies of itself and of `sp1-core-executor-runner-binary`, resolved
  from the lockfiles shipped in those crates (whose checksums the outer lockfile pins). The script fetches those two trees
  as well, because the outer `cargo fetch` alone leaves the offline build short of crates. This affects the host tools only;
  the guest ELF is built before it and asserted on its own.
- **What no proof can do for you**: the drand quicknet signatures the guest verified are the chain log's; that a round's
  signature is the one the relay published is an out-of-band check against the public beacon (`../VERIFY.md` section 4).
- **The GPU path was rehearsed once, on a rented machine.** The CPU path was rehearsed in a fresh Ubuntu 22.04 container on the
  development machine, and the whole ladder with `prove` on a freshly launched Lambda A100-SXM4-40GB that had nothing installed
  (the rehearsal tables below, `TEST_LOG_LAMBDA_A100.md`); `prove` follows the node runbook the batch itself ran
  (`../source/node_prep/G2D_NODE_RUNBOOK.sh`).

## Pins carried in replicate.sh

| what | value |
|---|---|
| program vkey | `0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027` |
| guest ELF | sha256 `51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc`, 396,200 bytes |
| Groth16 circuit | v6.1.0, verifier key sha256 `4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696` |
| constants blob | sha256 `73310ddab603cab5588d05e9ac4deb7e56466a6fae4bbf89244c32f2bd1a8b92`, 3,476,866 bytes |
| expected identities | sha256 `182870aa06f11e246a76f8c94c5a1c40aed7b3ad4b3537420422f426dcd46eb2` (the published copy; the file as frozen on 7 September, named by every receipt, hashed `6822cdcefa9a8833460287a3bb619fa63d0f3755d46dccc7db5418b261d6d613` and differs only in the redacted provenance paths of its `sources` block, `../REDACTION.md`) |
| chain log | sha256 `5d9af297ae37119df15412f516a4543ee9f54b6aa66186abe478512fe9a1ff48`, BLAKE3 `754e5716e65a065e5ad3146131609a1fd12e8310d966fb6bf2d3de6c568e7f8b` |
| rustup-init 1.29.1 | sha256 `dda7234360b7f578ca8b0ddcb80145646fa61a67c1720a5abc7051b35c9fcb71` |
| host Rust | `rustc 1.98.0 (88d9e12ae 2026-08-18)`, `cargo 1.98.0 (797e8a9bc 2026-08-05)` |
| cargo-prove | tarball sha256 `8ad88ebd4d970f0b9b7561f9b5899242f01c7da6d04ec4bd5d09f4cf044a541b`; binary sha256 `d8835f80b386d5025420d6b09e73ad825b822ac143e8ed09312b2e08018ff106`; `cargo-prove sp1 (f66b4bf 2026-08-12T14:40:11.709680161Z)` |
| succinct guest toolchain | tarball sha256 `12c94435d41bfe4e20131bbcce40b35abd32270ad792befc653af4e3fabc192f`, 384,963,362 bytes; rustc 1.94.0-dev, LLVM 21.1.8 |
| protoc 21.12 | zip sha256 `3a4c1e5f2516c639d3079b1586e703fc7bcfa2136d58bda24d1d54f949c315e8` |
| sp1-gpu-server 6.4.0 | tarball sha256 `2946b0b46026b8689181eb05561ed0be2798114196893d5ef38e46f93c14c596`; binary sha256 `f68b85dc3cff776a613df897ba6e7f8592d08482330b4165d46a8ee87aafd97c`, 250,950,472 bytes |
| Groth16 v6.1.0 circuit files | the seven sha256 digests of `PINS.json` `prover_node.groth16_circuit_files_v6_1_0` |
| standalone verifier sources | `Cargo.toml` `07c3da3e…2a71`, `Cargo.lock` `78fa1a2b…19c1`, `src/main.rs` `052f7a69…638e` (vendored from poliebotics/zeebeam `ef686b33…48bd`) |

`fetch` refuses if any of these disagrees with `PINS.json` or with the frozen files, so a package that changed under the same
script name cannot pass quietly.

## Subcommands and options

`fetch`, `quick`, `build`, `verify`, `execute ROW`, `synthetic`, `parity`, `prove ROW`, `all`, `toolchain [rust|sp1|gpu]`.
Options: `--work DIR`, `--from-local PATH` (a local copy of the package or a Dark Lantern checkout instead of GitHub),
`--data-from-local DIR` (a local copy of the data-layer prefix), `--ref REF` (a commit hash pins the tree), `--repo-only`,
`--frame PATH`, `--device N`, `--no-prove`, `--jobs N`, `--no-b3sum`, `--refetch`. Every command ensures its own
prerequisites (verify builds if it must; parity fetches the data-layer files if they are absent), so any rung can be run alone.

## Rehearsal

Two rehearsals, both on 8 September 2026: a fresh `ubuntu:22.04` container on the development machine (the CPU path,
`all --no-prove`), and a freshly launched Lambda A100-SXM4-40GB instance running Ubuntu 22.04.5 (the whole ladder, `all --repo-only`
with `prove`).

The CPU path was rehearsed on 8 September 2026 in a fresh `ubuntu:22.04` container on the development machine (32 threads,
92 GiB RAM, glibc 2.35 inside the container, no GPU), with empty cargo, rustup and sp1 homes and the package taken from its
staging copy (`--from-local`, `--data-from-local`; nothing was public yet). `replicate.sh all --no-prove` with the row-600
frame mounted read-only ran end to end in 10m43s:

| step | measured | result |
|---|---|---|
| fetch: ledger, pins, 2,500 data-layer files | 4 s | 2,703 ledger entries matching, every pin agreeing, 348,367,700 bytes of data-layer objects consistent with their controls |
| toolchain: rustup, Rust 1.98.0, b3sum, cargo-prove, succinct toolchain, protoc | 47 s | every download at its pinned digest |
| cargo fetch (four lockfiles plus SP1's two nested runner trees) | 31 s | `--locked` throughout |
| build (cargo wall 137 s, max RSS 2.9 GiB) | 2m44s | `BUILD_REPRODUCED_OK`: ELF `51b7bc35…75cc`, 396,200 bytes, vkey `0x00f01894…a027`, circuit key `4388a21c…e696` |
| verify | 33 s | 112/112 accepted, 35/35 checks each; 18 controls behaved; raw form accepted; noise and chain-log BLAKE3 confirmed with b3sum |
| quick (standalone verifier, build included) | 2m04s | 112/112 VERIFIED, both tamper controls rejected per proof |
| execute 600: prepare | 13 s | `prepared_native`, 33 checks, beacons verified, noise BLAKE3 equal to the frozen table |
| execute 600: complete guest on the CPU | 3m43s | 14,400,363,198 instructions, peak RSS 14.8 GiB, 752 public bytes identical to the published statement |
| parity | 22 s | 81 tests passed, 3 stopped on the August sets that were not yet on the data layer at that hour (reported as absent), 0 failed |

The no-frame branch was exercised separately (`execute 601` without `--frame`: the row's native legs end at `pending_frame`,
then the synthetic session runs the pinned guest end to end: 14,394,768,752 instructions, all 752 public bytes equal to the
native re-execution and the 651 binding bytes equal to the Python oracle, about 5 minutes and 15.2 GiB). The Dockerfile's full
image built (3.95 GB) and re-checked every installed component against its pin. The git fetch path was exercised against a
local repository by branch and by commit hash, with the root-ledger cross-check. The record, with the defects found and fixed
on the way (a target-filtered `cargo fetch` that left the guest build short of crates; SP1's nested runner build that needs
its own two lockfiles fetched), is kept with the release papers (`replicate_test_20260908/TEST_LOG.md`) and published as
`TEST_LOG.md` beside this file. The GPU path was rehearsed later that evening on a fresh machine; the next table records it.

### The fresh machine: a Lambda A100-SXM4-40GB (8 September 2026)

The whole ladder, `prove` included, then ran on a machine that had none of it: a freshly launched Lambda `gpu_1x_a100_sxm4`
instance (Ubuntu 22.04.5 LTS, kernel 6.8.0-60-generic, glibc 2.35, 30 threads, 216 GiB RAM, one NVIDIA A100-SXM4-40GB, driver
570.148.08; no Rust, SP1, protoc or cargo home present), against a local copy of the package as staged at 16:50Z that day
(`--from-local`, `--repo-only`, the row-600 frame passed with `--frame`; every pin the run checked is a pin of the published
revision). `replicate.sh all` ran end to end in 62m26s:

| step | measured | result |
|---|---|---|
| fetch (local copy), ledger, pins | 2 s | 3,092 ledger entries matching, no unlisted file, every pin agreeing |
| toolchain: rustup, Rust 1.98.0, b3sum, cargo-prove, succinct toolchain, protoc | 27 s | every download at its pinned digest |
| build (CPU features) | 2m34s | `BUILD_REPRODUCED_OK`: ELF `51b7bc35…75cc`, 396,200 bytes, vkey `0x00f01894…a027`, circuit key `4388a21c…e696` |
| verify | 0m52s | 112/112 accepted; controls behaved; 112 noise files match `PINS.json` |
| quick | 3m25s | 112/112 `VERIFIED`, both tamper controls rejected per proof |
| execute 600 | 6m59s | 14,400,363,198 instructions, max RSS 17,447,080 kB, 33 acceptance checks PASS, 752 public bytes identical to the published statement |
| CUDA prover install, circuit cache, `cuda` rebuild | 4m34s | `sp1-gpu-server` and the circuit tarball at their pinned digests; the rebuild reproduced the same ELF and key (1m23s) |
| prove 600 on device 0 | 43m06s | a fresh proof (2,446 bytes wrapped, 356 raw, sha256 `a381b80b…8be`), `prove_elapsed_ms` 2,539,814 (42.3 min), GPU memory peak 28,435 MiB of 40,960, client max RSS 7,353,628 kB; accepted cold under the pinned identities, all 35 checks; public bytes identical to the published statement; client exit 134 after the receipt, as in every observed run |

The redacted full log and the run's small artefacts (build logs, manifests, receipts, the acceptance report, GPU samples, the
fresh proof) are `TEST_LOG_LAMBDA_A100.md` and `lambda_a100_20260908/` beside this file. The parity step was not part of this run
(`--repo-only`); it was rehearsed in the container above. The GPU path in Docker remains documented and not rehearsed.

— BOSUN ⚓

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.2 | 2026-09-08 | BOSUN | The fresh-machine rehearsal (Lambda A100-SXM4-40GB, the whole ladder with `prove`, 62m26s) added with its table, log and artefacts; the GPU path no longer [untested here]; the memory note names both cards. |
| 1.1 | 2026-09-08 | BOSUN | The frames and the August tensors are published: `execute` and `prove` take the shipped row-600 frame or fetch a published frame; the parity classifier reports absent data-layer files, not held ones; sizes corrected; the build kit named; three sentences reworded. |
| 1.0 | 2026-09-08 | BOSUN | CPU path rehearsed end to end in a fresh Ubuntu 22.04 container (10m43s); rehearsal table, nested-build note and the git-path check added; GPU path stays [untested here]. |
| 0.1 | 2026-09-08 | BOSUN | First version, written with the CPU-path rehearsal in progress. |
