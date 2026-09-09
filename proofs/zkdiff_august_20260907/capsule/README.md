---
version: 1.3
date: 2026-09-09
status: the offline verification capsule: prebuilt static binaries and the exact inputs to verify all 112 proofs, and to recompute any row's statement from its raw frame, with no Rust toolchain, no Python and no network; tested in a fresh ubuntu:22.04 container with --network none
author: Cathal Ryan Hynes (author of record); drafted with BOSUN, the project's automated research assistant
---

# capsule/: verify every proof offline, with nothing installed

An outside agent asked for a way to check the proofs from the package alone, with no crates.io, no SP1 toolchain and no
network (`AUDIT_TRAIL.md` A1 Codex, the first outside reading). This directory is that way. It holds two statically linked x86_64 Linux
executables built from the published source, the pinned keys, the frozen expected identities, copies of the 112 proofs and
statements, and one script. Everything else in the package stays where it is; the capsule compares its copies with the
package's files when it sits inside it.

```
bash capsule/verify_offline.sh
```

Needs bash and coreutils only, about three and a half minutes on the rehearsal machine, and writes its reports under `$CAPSULE_OUT` (default
`/tmp/zkdiff_capsule_out`), so the capsule may be read-only. Exit 0 means: the capsule's own ledger verified; `zkdiff-verify`
embeds the pinned guest ELF `51b7bc35…75cc` and circuit key `4388a21c…e696`; all 112 framed proofs were accepted under the
pinned program key and every frozen identity (`STATEMENT.md` section 9); the 18 negative controls on row 600 behaved; the raw
356 + 752 byte form of row 600 was accepted; all 112 raw proofs were `VERIFIED` by the standalone verifier with both tamper
controls rejected each time. The script prints one line per row with `R_correct`, `R_wrong`, `D`, the class and the clip count,
which you can compare with `RESULTS.md` section 6.

In a fresh container, from the package root:

```
docker run --rm --network none -v "$PWD/capsule:/capsule:ro" -v /tmp/out:/out -e CAPSULE_OUT=/out ubuntu:22.04 bash /capsule/verify_offline.sh
```

## What is here

| file | what |
|---|---|
| `zkdiff-verify` | the package's acceptance verifier (`source/armc-relation/script/src/verify.rs`), statically linked (SHA-256 `8f74012f19b06ea733c6bf2944a9f2bcf705421781505c3a95dc3c2f8f39eed9`, 44,203,592 bytes); `--identity` prints the embedded ELF and circuit-key digests |
| `zeebeam-standalone-verifier` | the vendored ZeeBeam standalone verifier (`tools/standalone_verifier/`), statically linked (SHA-256 `f5995796f3dc265e78c5da7bace364eb35b904f2055e1e9843a5d4bd3be76d07`, 1,623,408 bytes): `sp1-verifier` 6.4.0 only, no ELF |
| `PROGRAM_VKEY.txt` | the pinned program verifying key `0x00f01894…a027` |
| `groth16_vk.bin` | the 492-byte SP1 Groth16 v6.1.0 circuit verifying key, SHA-256 `4388a21c…e696`; the same bytes are embedded in both binaries and the script checks the file against the pin |
| `expected_identities_august.json` | the frozen identities table, byte-identical to `source/expected_identities_august.json` (SHA-256 `182870aa06f11e246a76f8c94c5a1c40aed7b3ad4b3537420422f426dcd46eb2`); the file as frozen on 7 September 2026, which every receipt and acceptance report names, hashed `6822cdcefa9a8833460287a3bb619fa63d0f3755d46dccc7db5418b261d6d613` and differs only in the provenance paths of its `sources` block, redacted in the published copy (`REDACTION.md`) |
| `proofs/`, `public_values/` | copies of the 112 framed proofs, 112 raw proofs and 112 statements (the script compares them with `../proofs/` and `../public_values/`) |
| `verify_offline.sh` | the script described above |
| `BUILD_RECORD.txt`, `SOURCE_DIGESTS.txt` | the fail-closed build record of the rebuild that produced these binaries: `BUILD_REPRODUCED_OK`, ELF `51b7bc35…75cc`, vkey `0x00f01894…a027`, from a copy of this package's `source/` on 8 September 2026 (published with the development machine's paths and hostname redacted; both digests in `STATIC_LINK_RECORD.txt`) |
| `STATIC_LINK_RECORD.txt` | how the binaries were relinked statically, their digests and `file(1)` output |
| `THIRD_PARTY_CRATES_*.tsv`, `THIRD_PARTY_NOTICES.md` | the Rust crates statically linked into each binary, with their declared licences, and the notices for the crates, glibc and the copied circuit key |
| `reexecute/` | the re-execution capsule: the static `zkdiff-batch`, the raw frame and the oracle input arrays of row 600, and `reexecute_row.sh` (below) |
| `SHA256SUMS` | every file above; the script checks it first |

## Re-executing a row from its raw frame

`reexecute/reexecute_row.sh` recomputes a row's 752-byte statement from the raw frame, the chain log, the normative noise, the
constants blob and the frozen identities with the same `execute` mode of the batch driver the node used: the complete guest
program runs in the SP1 executor on the CPU (the pinned RISC-V ELF, executed but not proved), the host re-evaluates the relation
natively and requires the two statements to agree, and the script compares the result byte for byte with the published
`public_values/row_NNNNNN_public_values.bin`. It needs about 17 GB
of RAM and 4 to 7 minutes per row and no toolchain. Row 600's frame is shipped in `reexecute/`; the frames of all 112 rows
are on the data layer (`FRAMES.md`), so any row can be re-executed:

```
bash capsule/reexecute/reexecute_row.sh                                   # row 600, shipped frame
bash capsule/reexecute/reexecute_row.sh 684 --frames-dir /path/to/frames  # any row, a frame downloaded from the data layer
```

The batch driver refuses a frame whose BLAKE3 differs from the chain log's before it runs anything. `reexecute/row_000600.npz`
is the Python oracle's input record for row 600 (`C_int`, `noise_int`, `Ct_int`, `E_correct`, `E_wrong`); the same file for
every row is on the data layer under `oracle/final/august_inputs/`, and with those in place `source/tools/python_oracle_rows.py`
recomputes the residual sums in Python (`VERIFY.md` section 7). Both routes agree with the proofs (see the rehearsal table).

## What the capsule establishes, and what it does not

After `verify_offline.sh`: each of the 112 proofs verifies under the pinned program key with SP1's v6.1.0 Groth16 circuit, and
its statement carries exactly the frozen identities and the published residual sums; the standalone route agrees on the Groth16
layer. After `reexecute_row.sh` on a row: the published residual sums of that row are what the pinned guest program, and the native
evaluation beside it, compute on that frame. Neither says anything about a camera, a scene, realness, liveness or generalisation (`CLAIM_BOUNDARY.md`). The
capsule does not rebuild the guest from source; `VERIFY.md` section 2 and `replicate/` do, and the build record here is the
record of one such rebuild. Trusting the capsule's `zkdiff-verify` means trusting that the binary embeds what its record
says; a reader who does not want to trust a shipped binary rebuilds it (`replicate/replicate.sh build`), which reproduces the
pinned ELF and key from the published source, and then runs the same checks.

## How the binaries were built

A copy of this package's `source/` was rebuilt with the fail-closed driver `build_reproducible.sh` (Rust 1.98.0, cargo-prove
sp1 6.4.0 with the succinct 1.94.0-dev toolchain, offline, `--locked`), which asserted the pinned ELF, key and circuit key
(`BUILD_RECORD.txt`). The host build ran under `RUSTFLAGS=--remap-path-prefix=<cargo home>=/cargo
--remap-path-prefix=<source copy>=/src`, so no dependency carries a machine path in its panic-location or debug strings (the
guest ELF has its own remap in `script/build.rs` and reproduced the pin under these flags). In the same target directory the
host binaries were then relinked with `cargo rustc --release --offline --locked --bin <name> -- -C target-feature=+crt-static
-C strip=symbols`, which applies the static-linking flag to the final crate only, so the embedded guest ELF and every
dependency are the driver's build; the standalone verifier was built the same way from a copy of `tools/standalone_verifier/`.
The result is a static-pie executable with glibc 2.43 objects linked in (Ubuntu 26.04; the dynamically linked host binaries of
the same build reference symbols up to `GLIBC_2.39`) and symbols stripped (`STATIC_LINK_RECORD.txt`); `strings` finds no home,
corpus or staging path in any of the three. `zkdiff-verify --identity` prints the digest of the ELF it embeds and of itself;
`PINS.json` `capsule` pins all three binaries. Third-party terms: `THIRD_PARTY_NOTICES.md` here and the repository's root
`THIRD_PARTY_NOTICES.md` and `licenses/`.

## Rehearsal (8 September 2026)

The binaries were built twice that day: an afternoon build relinked at the final crate only, and, after the privacy sweep found
the development machine's paths inside them, the evening rebuild under a path remap that this capsule ships (`STATIC_LINK_RECORD.txt`).
Both were rehearsed; the rows below are the evening rebuild's, the afternoon's numbers in brackets where they differ.

| where | what | result |
|---|---|---|
| the development machine (Ubuntu 26.04) | `verify_offline.sh` inside the package | 112/112 accepted, 112/112 standalone VERIFIED, 18 controls behaved, copies equal the package's; 2 min 52 s (3 min 25 s) |
| a fresh `ubuntu:22.04` container (glibc 2.35, no cargo, python3, rustc or curl), `--network none`, uid 1000, capsule mounted read-only | `verify_offline.sh` | the same counts, 2 min 38 s (3 min 25 s) |
| the development machine | `reexecute_row.sh` (row 600, shipped frame) | `R_correct` 4,435,539,299, `R_wrong` 11,254,163,581, `D` +6,818,624,282, 14,400,363,198 instructions, statement byte-identical; 3 min 27 s (3 min 52 s) |
| the same container, `--network none`, the package mounted read-only | `reexecute_row.sh` (row 600) | the same numbers, statement byte-identical; 3 min 24 s (3 min 45 s) |
| the development machine | `reexecute_row.sh 684 --frames-dir` (a frame from the published set, the mirrored row) | offset -30 mirrored, wrong row 654; `R_correct` 4,587,519,841, `R_wrong` 11,036,216,072, `D` +6,448,696,231, 14,400,373,541 instructions (the node's count); statement byte-identical; 3 min 28 s (3 min 50 s) |
| the development machine, Python 3.14, torch 2.11.0, numpy 2.3.5 | `source/tools/python_oracle_rows.py 600 684` with the data-layer `august_inputs/*.npz` placed | 600: 4,435,539,299 / 11,254,163,581; 684: 4,587,519,841 / 11,036,216,072; equal to the statements; 11 s |

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-08 | BOSUN | First version: offline verification and re-execution capsule, after the outside-agent readability audits (the first reading, A1) and the principal's publication decision. |
| 1.1 | 2026-09-08 | BOSUN | The binaries rebuilt under a path remap (the privacy sweep, Astra round 7) and re-pinned; the re-execution described as the guest in the SP1 executor; glibc 2.43; timings; the expected identities' two digests; the notices completed. |
| 1.2 | 2026-09-08 | BOSUN | Third outside reading: the first reading named as such (it is not Astra round 7). |
| 1.3 | 2026-09-09 | BOSUN | authorship line, 9 September 2026. |
