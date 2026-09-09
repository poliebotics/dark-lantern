---
version: 1.1
updated: 2026-09-09
status: active
author: Cathal Ryan Hynes (author of record); drafted with BOSUN, the project's automated research assistant
---

# Test log: replicate.sh CPU path in a fresh ubuntu:22.04 container on the development machine

> Published copy of the release desk's test record (8 September 2026). Paths such as `release_pkg/...` and `g2_guest/...` are the
> development machine's private staging tree at the time of the test (its absolute paths are redacted); in the published package
> the same files are the package root, `source/` and the data layer. The raw frame named here was not yet published at the time of
> the test; the frames of all 112 proof rows are published since that evening (`../FRAMES.md`), row 600's in `../capsule/reexecute/`.

What is under test: `release_pkg/replicate/replicate.sh` and `release_pkg/replicate/Dockerfile`, the one-pull replication of the
zkdiff August proof package. Host: the development machine (32 threads, 91 GiB RAM, Docker 29.1.3, no NVIDIA container runtime). Container:
`zkdiff-replicate:base`, the Dockerfile's `base` stage (ubuntu:22.04 plus `ca-certificates curl git build-essential pkg-config
time binutils python3 xz-utils`, user `replicator` uid 1000), run as uid 1000 with empty cargo, rustup and sp1 homes on a bind
mount. Network allowed for the toolchain downloads. The package came from the local staging copy
(`--from-local /pkg/zkdiff_august_20260907`, a read-only mount of `release_pkg/dark-lantern/proofs/zkdiff_august_20260907`)
and the data-layer objects from the local bundle (`--data-from-local /pkg/data`, a read-only mount of
`release_pkg/r2_bundle/publish_package`), because nothing is public yet. The row-600 raw frame was mounted read-only from the
private tree (`g2_guest/frames_august/frame_000600.raw`, 24,472,000 bytes, sha256 `5c8e7856…211c`) so `execute 600` could run
the complete guest on a real August row; the frame stayed on the development machine. Runner scripts: `run_cpu_test.sh` (run 1),
`run_cpu_test2.sh` (run 2 onward). Full logs: `cpu_test_<run>.log` beside this file; the script's own log is
`work_<run>/.../out/replicate.log`. GPU path: **[untested here]** (no GPU in the container; the development machine's 5090 is not a proving target
for this package and Docker has no nvidia runtime).

## Run 1 (15:34Z to 15:36Z): FAILED at build, two defects found

Command: `run_cpu_test.sh run1 all --no-prove` (HOME overridden to `/work/home` on the mount).

| step | result | time |
|---|---|---|
| fetch (local copy, ledger, pins) | PASS: SHA256SUMS 2703 entries all matching, no unlisted file; every pin agrees between the script, PINS.json and the frozen files | 1 s |
| fetch (data layer, local bundle) | PASS: controls consistent (3356 objects, 348,367,700 bytes); 2500 large files placed and matching LARGE_FILES_SHA256SUMS | 4 s |
| toolchain rust | rustup-init printed `error: $HOME differs from euid-obtained home directory` three times, then installed anyway; Rust 1.98.0 and b3sum 1.8.7 installed and pin-checked | 19 s |
| toolchain sp1 | PASS: cargo-prove (tarball 8ad88ebd…, binary d8835f80…), succinct toolchain (12c94435…, 384,963,362 bytes), `cargo +succinct` resolved to the pinned cargo through the symlink, protoc 21.12 (3a4c1e5f…) | 29 s |
| cargo fetch | completed | 12 s |
| build | **FAIL**: `build_reproducible.sh` exit 8, cargo 101: sp1-build's `cargo metadata` on the guest (`sp1-build-6.4.0/src/build.rs:91`) ran offline and could not download `r-efi v5.3.0` | 17 s |

Defects and fixes:

1. `cargo +succinct fetch --locked --target riscv64im-succinct-zkvm-elf` (the command VERIFY.md section 2 gives) is not enough
   for the offline guest build: sp1-build runs `cargo metadata` without a platform filter before it builds, and metadata
   resolves every platform's dependencies from the lockfile, so the Windows/UEFI leaves (`r-efi`) must be in the cargo home too.
   Fix: fetch the guest lockfile without `--target`. VERIFY.md's `[confirm]` on the empty-cargo-home fetch is thereby answered:
   the documented command needs the `--target` dropped (reported to the package owner; VERIFY.md is not edited here).
2. The test harness overrode `HOME` to a directory that is not the container user's passwd home; rustup-init treats that as a
   sudo mistake and complains. Not a defect of the script on a real machine, but the script now exports `CARGO_HOME` and
   `RUSTUP_HOME` explicitly and fails closed if rustup-init does not leave a working `rustup`. Run 2 mounts the work
   directory at the user's real home instead.
3. Progress bars from `curl --progress-bar` filled the log with carriage returns; downloads are now silent (`-sS`) and
   reported by size and digest when they land.

## Run 2 (15:37Z to 15:38Z): FAILED at build, one defect found

Command: `run_cpu_test2.sh run2 all --no-prove` (home mounted at `/home/replicator`; no HOME override). Fetch, pins, data
layer and both toolchains passed as in run 1, without the rustup complaint; `cargo +succinct` resolved to the pinned cargo. The
guest ELF built (`zkdiff-guest built at 2026-09-08 15:38:38` in the cargo log), so defect 1 is fixed. Then:

| step | result | time |
|---|---|---|
| build | **FAIL**: cargo 101 in the build script of `sp1-core-executor-runner v6.4.0`: its nested `cargo metadata`, run offline, could not resolve `wasip3` (required by `getrandom 0.4.2`, locked by `uuid 1.23.1`) | 28 s |

Defect and fix:

4. `sp1-core-executor-runner 6.4.0` builds SP1's helper executor binary through a nested `cargo metadata` and `cargo build`
   inside the registry copies of itself and of `sp1-core-executor-runner-binary`, each resolved from the `Cargo.lock` shipped
   in the crate. Those shipped locks name crates the outer `script/Cargo.lock` does not (`wasip3`, `r-efi`), so after a plain
   `cargo fetch --locked` in `script/` the offline build has no source for them. The development machine and the node never
   saw this because their cargo homes were warm. Fix: `replicate.sh` now runs `cargo fetch --locked` inside both registry
   copies after the outer fetch. Because the nested trees resolve from lockfiles shipped inside crates whose checksums the
   outer lockfile pins, the helper binary's dependency set is pinned too (uuid 1.23.1, getrandom 0.4.2, sp1-* 6.4.0), which is
   worth stating in VERIFY.md alongside the `--target` correction from run 1.

## Run 3 (15:43Z to 15:52Z): CPU path PASSED through execute; parity classifier fixed in two short re-runs

Command: `run_cpu_test2.sh run3 all --no-prove`, fresh work directory (log of this pass: `cpu_test_run3_all_pass1.log`; the
script's reports: `run3_out/`). Container environment as printed by the script: Ubuntu 22.04.5, glibc 2.35, 32 threads,
92 GiB RAM (69 GiB available), no GPU, uid 1000, HOME `/home/replicator`.

| step | result | time |
|---|---|---|
| fetch (local copy) | PASS: SHA256SUMS 2703 entries all matching, no unlisted file; every pin agrees (vkey `0x00f01894…a027`, ELF `51b7bc35…75cc` 396,200 B, circuit key `4388a21c…e696`, constants `73310dda…8b92` 3,476,866 B, expected identities `6822cdce…d613`, chain log `5d9af297…ff48` / BLAKE3 `754e5716…7f8b`; batch complete over 112 rows, 112 positive) | 1 s |
| fetch (data layer, local bundle) | PASS: controls consistent (3356 objects, 348,367,700 bytes, RELEASE.json staged 2026-09-08T15:18:30Z); 2500 large files placed and matching | 4 s |
| toolchain rust + sp1 | PASS: rustup 1.29.1 (pinned installer), rustc/cargo 1.98.0, b3sum 1.8.7; cargo-prove `d8835f80…`; succinct toolchain tarball `12c94435…` linked as `succinct` (rustc 1.94.0-dev, LLVM 21.1.8), `cargo +succinct` resolving to the pinned cargo, target and bundled ld.lld present; protoc 3.21.12 | 27 s |
| cargo fetch | PASS: four lockfiles plus the two nested runner trees (352 and 342 locked packages), all `--locked` | 8 s |
| build | **PASS**: `BUILD_REPRODUCED_OK sha256=51b7bc35…75cc vkey=0x00f01894…a027 bytes=396200 groth16_vk_sha256=4388a21c…e696 circuit=v6.1.0`; cargo wall 98.9 s, max RSS 3.1 GiB; record `build_record_20260908T154406Z.txt` | 1m54s |
| verify | **PASS**: 112/112 accepted, 35/35 checks each, 112 positive; every statement equals its receipt and its PINS.json entry; 18 controls on row 600 behaved (relation and policy layers); raw 356 + 752 byte form accepted; 112 noise files match PINS.json by sha256; b3sum: chain log and 112 noise BLAKE3 digests match the expected identities | 33 s |
| quick | **PASS**: standalone verifier built from the vendored sources (pins matched), 112/112 VERIFIED with both tamper controls rejected. This answers VERIFY.md section 1's `[confirm]`: the published ZeeBeam standalone verifier accepts ZBDIFF01 proofs | 2m02s (build included) |
| execute 600, prepare | PASS: `prepared_native`, offset -2 direct, wrong row 598; beacons verified and bound, chain advance and both emission renders reproduce the chain log, noise BLAKE3 equals the frozen table; native statement accepted (33 checks): R_correct 4,435,539,299, R_wrong 11,254,163,581, D +6,818,624,282 | 13 s |
| execute 600, complete guest | **PASS**: status executed, 14,400,363,198 instructions, 269,904 syscalls, oracle native_reexecution, host peak RSS 14.8 GiB (time -v 15,482,904 KiB), wall 3:15.56; public values sha256 `26b5b2d3…e01b` equals the published receipt; the 752 bytes are byte-identical to `public_values/row_000600_public_values.bin` | 3m16s |
| parity | classifier defect (numbered in the Summary); after the fix, re-run in the same work directory: armc-int 24 passed, 1 held; armc-relation 57 passed, 2 held; total 81 passed, 3 held, 0 failed: **PASS** | 15 s first pass (compile included), 4 s re-run |

Defects and fixes:

5. The HELD classifier matched only the adapter tests' `oracle_final/{set} missing` assertion; armc-int's `final_artifact_pins`
   stops on the held set with the loader's `read …/int16_august_650_correct/index.json: No such file or directory`. The
   classifier now treats any test whose failure names a held August oracle set or a raw frame together with a missing-file
   message as HELD. Everything else still fails the step.
6. A shadowed name in the same classifier (`held` used for both the function and the per-suite list) raised
   `TypeError: 'list' object is not callable` on the first re-run; renamed.

Note on the published tree: `runs/batch_prepare_g2d_20260907/row_000684/witness` is present in the package as staged this
afternoon (the ledger grew from 2694 to 2703 entries while this was being written), so the relation test that reads it
passes; VERIFY.md section 6's `[confirm]` on the test suites is answered by the counts above: 81 tests pass on the published
tree, and exactly three stop on the held August oracle sets.

## Run 4 (15:55Z to 16:06Z): clean end-to-end CPU path PASSED, exit 0, 10m43s

Command: `run_cpu_test2.sh run4 all --no-prove`, fresh work directory, the final script (log: `cpu_test_run4.log`; the
script's own log and reports: `work_run4/zkdiff/out/`). Every step passed first time:

| step | wall | result |
|---|---|---|
| fetch (package + data layer) | 4 s | 2703 ledger entries OK; pins agree; controls consistent; 2500 large files matching |
| toolchain rust + sp1 | 47 s | rustup 1.29.1, Rust 1.98.0, b3sum 1.8.7, cargo-prove `d8835f80…`, succinct 1.94.0-dev / LLVM 21.1.8, protoc 3.21.12, all at their pins |
| cargo fetch | 31 s | four lockfiles + nested runner trees (352 and 342 packages), `--locked` |
| build | 2m44s (cargo wall 136.96 s, max RSS 3,034,208 KiB) | `BUILD_REPRODUCED_OK sha256=51b7bc35…75cc vkey=0x00f01894…a027 bytes=396200 groth16_vk_sha256=4388a21c…e696 circuit=v6.1.0`; record `build_record_20260908T155606Z.txt` |
| verify | 33 s | 112/112 accepted (35/35 checks), 18 controls behaved, raw form accepted, noise sha256 and BLAKE3 and chain-log BLAKE3 confirmed |
| quick | 2m04s | 112/112 VERIFIED with the vendored standalone verifier |
| execute 600 prepare | 13 s | `prepared_native`, 33 checks, R_correct 4,435,539,299 / R_wrong 11,254,163,581 / D +6,818,624,282 |
| execute 600 complete guest | 3m43s (time -v 3:42.19, max RSS 15,563,380 KiB) | 14,400,363,198 instructions, public bytes identical to `public_values/row_000600_public_values.bin` |
| parity | 22 s | 81 passed, 3 HELD (`final_artifact_pins`, `final_blob_through_the_adapter_reproduces_the_final_exports`, `final_vectors_layer_by_layer_parity_d2_1328_and_august_650`), 0 failed |
| prove | skipped | `--no-prove`; no GPU in the container in any case |

Git fetch path (on the development machine, not in the container): a local repository holding the package under `proofs/` plus a root
`SHA256SUMS` in the Dark Lantern form (`./proofs/...` paths) was fetched with `ZKDIFF_REPO_URL=file://…` by branch (`--ref
main`) and by commit hash; the sparse cone checkout, the package ledger, the pins and the root-ledger cross-check (2704
entries under the package path) all passed. A defect found on the way: the root-ledger grep did not accept the `./` prefix
the real repository uses; fixed (defect 7). The GitHub URL itself cannot be exercised until item 032 is pushed.

## Dockerfile, full image (16:06Z to 16:08Z): built and smoke-tested, then removed for disk

`docker build --force-rm -t zkdiff-replicate:toolchain .` (log: `docker_build_toolchain.log`) built the `toolchain` stage on
top of `base`: `RUN replicate.sh --work /tmp/toolchain toolchain sp1` installed rustup 1.29.1, Rust 1.98.0, b3sum 1.8.7,
cargo-prove, the succinct toolchain and protoc at their pins inside the image (image `814902b2d7df`, 3.95 GB, about two
minutes). Smoke test: `docker run --rm zkdiff-replicate:toolchain replicate.sh --work /tmp/w toolchain sp1` re-checked every
installed component against its pin (all `ok`, exit 0). The image was then removed (`docker rmi`) because the development machine's root
filesystem had reached 6.3 GB free; the Dockerfile's `verify` default command was not run from the image (it would fetch from
GitHub, which holds nothing yet) and a `--from-local` run inside the image would have duplicated the 4 GB build tree of run 4.

## No-frame branch (16:06Z to 16:12Z): `execute 601` without `--frame`, then `synthetic`

Command: `run_cpu_test3.sh run4 execute 601` (run 4's work tree, no frame mounted). Row 601: `zkdiff-batch prepare` ended
`pending_frame` with offset +2 direct, wrong row 603, and printed the native legs: beacons 31521690 verify and bind, both
patterns render to the chain log's digests, leaf_r and leaf_u open to the committed root, noise BLAKE3 equals the frozen
table; the script then said plainly that the frame-dependent legs stop there. The synthetic session ran the pinned guest end to
end: `verified_public_values=true`, `oracle=native_reexecution+python_oracle_binding_fields checked=651`, row 5 against wrong
row 7, 14,394,768,752 instructions, host elapsed 274 s (time -v wall 4:56.92, max RSS 15,917,792 KiB).

Defect 8: the script's own check of the executor's ELF line was anchored at line start (`^guest_elf_sha256=`), but
`zkdiff-execute` prints `guest_elf_bytes=… guest_elf_sha256=…` on one line, so a correct run was reported as "embeds another
ELF" and the step failed. Fixed (unanchored match, and the line is now printed).

Re-run (16:12Z to 16:16Z, `run_cpu_test3.sh run4 execute 601`, same work tree, exit 0): row 601 `pending_frame` with the same
native legs; `SYNTHETIC PASS in 3m32s`: `guest_elf_bytes=396200 guest_elf_sha256=51b7bc35…75cc`, 14,394,768,752 instructions,
269,904 syscalls, host elapsed 197.8 s (time -v wall 3:31.98, max RSS 15,498,840 KiB), statement row 5 wrong 7 offset +2,
R_correct 1,177,770,051,859, R_wrong 1,178,180,351,083, D +410,299,224.

## Summary

- CPU path: **PASS end to end** in a fresh Ubuntu 22.04 container with empty cargo, rustup and sp1 homes (run 4, 10m43s;
  fetch 4 s, toolchains 47 s, cargo fetch 31 s, build 2m44s, verify 33 s, quick 2m04s, execute 600 3m56s, parity 22 s), plus
  the no-frame branch (prepare `pending_frame` and the synthetic session, 3m32s), the git fetch path by branch and by commit
  hash against a local repository, and the Dockerfile's full image (built, pinned toolchain re-checked, removed for disk).
- Eight defects were found and fixed in the script on the way (numbered above). Two of them are facts about the package's own
  build that VERIFY.md should carry: the guest fetch must not be target-filtered (sp1-build's `cargo metadata` resolves every
  platform), and SP1's nested runner build needs `cargo fetch --locked` inside the registry copies of
  `sp1-core-executor-runner-6.4.0` and `sp1-core-executor-runner-binary-6.4.0` before an offline build from a fresh cargo home.
  VERIFY.md's `[confirm]` tags on the standalone-verifier route, the empty-cargo-home fetch and the test suites on the published
  tree are answered by these runs.
- GPU path (`prove`, `toolchain gpu`): **[untested here]**. It follows `source/node_prep/G2D_NODE_RUNBOOK.sh` (the commands the
  batch ran) and pins `sp1-gpu-server` and the seven circuit files by sha256, but this wrapper has not been executed on a GPU;
  the circuit tarball's own digest is recorded, not pinned (only its size, 6,211,807,514 bytes, was read from the bucket).
- What a fresh machine could not do at the time of the test: execute or prove a real August row without that row's raw frame, or
  run the August half of the oracle parity (the frames and the August tensors were published the same evening, `../FRAMES.md`,
  `../LARGE_FILES.md`; the kit now takes the shipped or published frame itself and reports absent data-layer files as absent).
- Disk: the test tree is 6.9 GB (run 4's work tree, the run 3 reports, the logs and the runner scripts); the run 1 to 3 work
  trees, the local git fixture, the hash-probe downloads and both Docker images were removed. the development machine's root was at 12 GB free at
  the end.

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.1 | 2026-09-09 | BOSUN | authorship line, 9 September 2026. |
| 1.0 | 2026-09-08 | BOSUN | Runs 3 and 4, the git path, the image build and the no-frame branch recorded; CPU path passes; eight defects fixed; GPU path untested here. |
| 0.1 | 2026-09-08 | BOSUN | Run 1 recorded; run 2 launched with the fixes. |
