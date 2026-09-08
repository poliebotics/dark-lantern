> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

# Outside-agent readability audit, round two: "A Tale of Two Conditionings" (`zkdiff_agent_audit_pkg`)

Auditor: an outside AI agent (Claude), reading only the files under the package directory. Method: every top-level
document read in full (`README.md`, `STATEMENT.md`, `CLAIM_BOUNDARY.md`, `VERIFY.md`, `RESULTS.md`, `GLOSSARY.md`,
`FAQ.md`, `HASHES.md`, `FRAMES.md`, `LARGE_FILES.md`, `REDACTION.md`, `AUDIT_TRAIL.md`, `LICENSE`), the capsule and
replication kit in full (`capsule/README.md`, `capsule/verify_offline.sh`, `capsule/reexecute/reexecute_row.sh`, the
build and relink records, `replicate/README.md`, `replicate/replicate.sh`, `replicate/TEST_LOG.md`, `replicate/Dockerfile`),
the three Python tools, the engineering records (`source/armc-relation/RELATION.md`, `source/FULL_GUEST.md`,
`oracle/final/README_FINAL.md`, `FREEZE_SUMMARY.md`), the verifier sources (`accept.rs`, `verify.rs`, `rule.rs`,
`statement.rs`, `spec.rs`, `beacon.rs`, `header.rs`, `membership.rs`, `build_reproducible.sh`), the row-600 receipt,
acceptance reports, manifests, controls, `PINS.json` and `expected_identities_august.json` by section, the chain-log
header, the three round-1 agent reports and the Astra round-6 verdict. Nothing was executed: no build, no proof, no hash
computed, no script run. "Present" means the file exists at that path and has the stated size or content where I read it;
"matches" means text compared with text. Line numbers are those of the package files as they stand.

---

## 1. What I understood the package claims

1. For each of the 112 rows 600 to 711 of the 712-row projector-camera session of 22 August 2026 there is one SP1 6.4.0
   Groth16 proof (356 raw bytes, 752-byte public statement) that an integer diffusion denoiser "adapted from the frozen
   ARM-C protocol and run in exact fixed point, produced the published residual sums on the whole sensor frame of that
   row" under the row's own emission and under the emission of a wrong row chosen by a published rule
   (`README.md:14-24`; `STATEMENT.md:18-41`).
2. Each proof binds its inputs rather than trusting the prover: the raw frame is hashed inside the proof and opened to the
   committed session tree, the chain state is re-derived from the previous row's record under verified drand quicknet
   signatures, both emission patterns are re-rendered from their chain states, the noise tensor is bound by its BLAKE3
   and the network constants by their SHA-256, and the statement "carries no pixels" (`README.md:17-23`;
   `STATEMENT.md:22-36`, `108-127`; `HASHES.md:16-57`).
3. All 112 proofs "verified and accepted under the frozen identities: 112 positive, 0 zero and 0 negative signed
   outcomes; 0 rows with a nonzero clip count", with `D` in MSE units from 0.007328 to 0.010988, median 0.009161
   (`README.md:11`; `RESULTS.md:199`, `324`).
4. The claim is execution binding only: the proofs "establish no physical-capture, realness, liveness,
   illumination-causality, adversarial-resistance or unseen-session-generalisation claim", do not reproduce the
   eight-seed result, the five-offset aggregate or a full diffusion trajectory, and the noise is bound by its bytes, not
   by a generator (`CLAIM_BOUNDARY.md:15-19`; `README.md:124-129`).
5. Rows 600 to 711 gave no gradient to training, but seven of them calibrated the integer scales and four were scored by
   a training-time screen, so they are "not an untouched test set"; the d2/v10 evaluation blocks on which the model was
   chosen are development validation; the program rebuilds byte for byte to the pinned ELF and key on two machines, and
   since 8 September 2026 the 112 raw frames and the August tensors are published so "every residual sum can be
   recomputed and every proof re-made by anyone" (`CLAIM_BOUNDARY.md:17`, `23-34`; `RESULTS.md:12-14`, `34-45`;
   `README.md:111-113`, `154-156`).

---

## 2. The verification path

Notation: `P` is the absolute path of the package root (`VERIFY.md:33-35`). The route that needs nothing installed is
x86_64 Linux only: the capsule binaries are "statically linked x86_64 Linux executables" (`VERIFY.md:207`) and
`verify_offline.sh:28` fails with "is this an x86_64 Linux machine?" elsewhere.

### (a) Verify one proof (row 600)

| # | step | command | source | complete? |
|---|---|---|---|---|
| a0 | ledger | `(cd "$P" && sha256sum -c --quiet SHA256SUMS && echo LEDGER_OK)` then the unlisted-files command of `VERIFY.md:45-46` | `VERIFY.md:41-53` | Yes. `SHA256SUMS` has 3,092 entries; by listing, every path exists (3,090 files plus the two nested `capsule/*/SHA256SUMS` ledgers that the `! -name SHA256SUMS` filter hides) and no file is unlisted. Not hashed by me. |
| a1 | the verifier's identity | `"$P/capsule/zkdiff-verify" --identity` | `capsule/README.md:38`; `verify_offline.sh:28-32` | Yes. Expected JSON: `guest_elf_sha256` `51b7bc35…75cc`, `groth16_vk_sha256` `4388a21c…e696`, `sp1_circuit_version` `v6.1.0`, `vk_root` `002f850e…5352` (`capsule/STATIC_LINK_RECORD.txt:13`). |
| a2 | full acceptance, framed artifact | `"$P/capsule/zkdiff-verify" --proof "$P/proofs/row_000600_groth16.bin" --expect "$P/source/expected_identities_august.json" --report /tmp/row_000600.verify.json` | `VERIFY.md:172-179` with the capsule binary in place of `$S/zkdiff-verify`; the 35 named checks are `accept.rs:7-24`, `198-367` | Yes. Stdout must end `verified_and_accepted=true` (`verify.rs:175`); the report's `acceptance.accepted` must be `true` and `version_check` `PASS` (`verify.rs:136-144`). Compare with `receipts/row_000600_receipt.json` `decoded` and `receipts/independent_verify/row_000600.verify.json`. |
| a3 | raw form | `"$P/capsule/zkdiff-verify" --proof-bytes "$P/proofs/row_000600_groth16_proof.bin" --public "$P/public_values/row_000600_public_values.bin" --expect "$P/source/expected_identities_august.json"` | `VERIFY.md:183`; `verify_offline.sh:57-59` | Yes. |
| a4 | Groth16 layer alone | `"$P/capsule/zeebeam-standalone-verifier" "$P/proofs/row_000600_groth16_proof.bin" "$P/public_values/row_000600_public_values.bin" 0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027` | `VERIFY.md:75-79`; `tools/standalone_verifier/src/main.rs:35-38` | Yes. Expected last lines `tamper_public_byte_87_rejected=true`, `wrong_vkey_rejected=true`, `VERIFIED`. |
| a5 | decode and compare | `python3 "$P/tools/decode_zbdiff01.py" "$P/public_values/row_000600_public_values.bin"` | `VERIFY.md:238-248`; layout `STATEMENT.md:75-102` | Yes (python3, standard library). Expected `row` 600, `wrong_row` 598, `offset` -2, `direct`, `r_correct` 4435539299, `r_wrong` 11254163581, `noise_blake3` `bd4d83ec…`, `raw_blake3` `9d4a0745…`; equal to `RESULTS.md:211`, the receipt's `decoded` block and `PINS.json` `batch.proofs.600`. |
| a6 | controls | `"$P/capsule/zkdiff-verify" --proof "$P/proofs/row_000600_groth16.bin" --expect "$P/source/expected_identities_august.json" --controls --report /tmp/controls.json` | `VERIFY.md:200-203`; `accept.rs:395-539` | Yes; the node's record is `receipts/proof_controls.json`, 18 controls (`capsule/README.md:24`). |

What a3/a4 trust: the shipped binaries, pinned by SHA-256 in `capsule/SHA256SUMS`, `PINS.json` `capsule.binaries`
(lines 1911-1925) and `capsule/STATIC_LINK_RECORD.txt:10-11`, with the rebuild and relink records beside them. A reader
who will not trust a shipped binary has the source route (`VERIFY.md` sections 1 and 2), which needs a Rust toolchain
and either the network or a populated cargo home: the crates are not vendored.

### (b) Verify all 112

| # | step | command | source | complete? |
|---|---|---|---|---|
| b1 | offline, both routes | `bash "$P/capsule/verify_offline.sh"` | `VERIFY.md:214-221`; `capsule/README.md:16-27` | Yes. The script checks the capsule ledger, the pins, the two embedded identities, runs `zkdiff-verify --expect` on all 112 framed proofs and asserts `n -eq 112` and `ok -eq 112` (`verify_offline.sh:49-50`), the 18 controls and the raw form on row 600, the standalone verifier on all 112 raw proofs with both tamper controls (`:62-75`), and byte-compares the capsule copies with `../proofs`, `../public_values` and `../source/expected_identities_august.json` (`:77-83`). It prints one line per row with `R_correct`, `R_wrong`, `D`, class and clips to compare with `RESULTS.md:211-322`. Rehearsed in a `--network none` `ubuntu:22.04` container, 3 min 25 s (`capsule/README.md:95-96`). |
| b2 | identities without a binary | `python3 "$P/tools/check_identities.py" "$P"` | `VERIFY.md:251-255`; `check_identities.py:1-17` | Yes (standard library). Every field of every statement against the frozen table, the chain log rows r, u, r-1, the receipt and `PINS.json`, with the rule recomputed from the row number; it verifies no proof. |
| b3 | noise rule | `python3 "$P/tools/regen_noise.py" "$P"` | `VERIFY.md:278-283` | Yes with numpy (`blake3` module optional). Regenerates the 112 tensors from the Philox rule and compares bytes, SHA-256 and BLAKE3. |
| b4 | source-built loops, optional | `VERIFY.md:88-93` (standalone) and `:189-191` (acceptance), both with `[ "$n" -eq 112 ]` | `VERIFY.md` | Yes given a Rust or SP1 toolchain and the network for the first fetch. |

### (c) Rebuild the program and compare its identity to the pinned one

| # | step | command | source | complete? |
|---|---|---|---|---|
| c1 | toolchain | Rust 1.98.0 via rustup-init 1.29.1 (URL and SHA-256 `dda72343…`), `cargo-prove` 6.4.0 tarball (`8ad88ebd…`, binary `d8835f80…`), succinct toolchain tarball (`12c94435…`, 384,963,362 bytes), protoc 21.12 (`3a4c1e5f…`), GNU time, binutils | `VERIFY.md:108-137`; `replicate.sh:56-79` | Pinned and sourced, not present: every item is a network download. `replicate.sh toolchain sp1` fetches and checks them (`replicate.sh:193-293`). The rustup channel itself rests on rustup's signatures, as `replicate/README.md:107-111` says. |
| c2 | crates | the five `cargo fetch --locked` commands of `VERIFY.md:147-154` (no `--target` on the guest fetch; the two nested `sp1-core-executor-runner*` trees fetched too) | `VERIFY.md:139-157`; `TEST_LOG.md:41-47`, `67-74` | Needs the network once; the lockfile digests are pinned (`PINS.json:832-837`). Rehearsed from an empty cargo home in a container (`TEST_LOG.md` runs 3 and 4). |
| c3 | build and assert | `(cd "$P/source/armc-relation" && ./build_reproducible.sh)`; last line `BUILD_REPRODUCED_OK sha256=51b7bc35…75cc vkey=0x00f01894…a027 bytes=396200 groth16_vk_sha256=4388a21c…e696 circuit=v6.1.0` | `VERIFY.md:161-169`; pins hard-coded at `build_reproducible.sh:15-18`, asserted at `:98-109` | Yes given c1 and c2. The ELF is "not shipped" (`PINS.json:6`); the rebuild is the only way to hold it. `--pin` prints without asserting (`:12`, `:104`). |
| c4 | compare | `"$P/source/armc-relation/script/target/release/zkdiff-verify" --identity` against `PINS.json` `program` (lines 5-33), `source/expected_identities_august.json:4-8`, `capsule/BUILD_RECORD.txt:51-54`, `source/node_prep/r5/build_record_20260907T215855Z.txt`, `receipts/gpu0_inputs_identity_launch.txt` | `VERIFY.md:172-178`, `300-313` | Yes. The same five values recur unchanged in every one of those files, in `replicate.sh:42-45`, `capsule/verify_offline.sh:11-14` and every receipt; I compared the strings. |
| c5 | one pull | `"$P/replicate/replicate.sh" --from-local "$P" --repo-only build` (my composition from `replicate.sh:19-30`, `434-447`) | `replicate/README.md:23`, `147-151` | Yes with the network for toolchains and crates; `--from-local` takes this directory, and the root-README cross-check is skipped with a note when no repository root is present (`replicate.sh:468`). |

The historical `SOURCE_DIGESTS_*.txt` lists cannot be checked against the published files (two comment-only
substitutions, `REDACTION.md:13-18`); the rebuild is the check, as `VERIFY.md:310-313` says.

### (d) Reproduce one row's residual sums

| # | route | command | source | complete? |
|---|---|---|---|---|
| d1 | row 600, native, offline | `bash "$P/capsule/reexecute/reexecute_row.sh"` | `VERIFY.md:228`; `capsule/README.md:51-67`; `reexecute_row.sh:37-48` | Yes: the static `zkdiff-batch`, `frame_000600.raw` (24,472,000 bytes, SHA-256 `5c8e7856…211c` equal to `FRAMES.md:27` and the receipt's `raw_sha256`), the chain log, the noise, the blob and the frozen table are all in the package. Needs x86_64 Linux, about 17 GB RAM, 4 to 7 minutes. The driver refuses a frame whose BLAKE3 differs from the chain log's, then `cmp`s the 752 recomputed bytes with `public_values/row_000600_public_values.bin`. Expected `R_correct` 4,435,539,299, `R_wrong` 11,254,163,581, `D` +6,818,624,282, 14,400,363,198 instructions. |
| d2 | any other row | download `results/zkdiff_august_20260907/v1/frames/frame_NNNNNN.raw` from `https://data.truthbeam.com/`, `sha256sum` it against `FRAMES.md`, then `bash "$P/capsule/reexecute/reexecute_row.sh" 684 --frames-dir /path/to/frames` | `FRAMES.md:10-23`; `VERIFY.md:229-233` | Everything but the frame is in the package; the frame needs the network and a live data layer (see question 1). Rehearsed by the authors for row 684 (`capsule/README.md:99`). |
| d3 | independent implementation (Python) | `(cd "$P/source" && python3 -B tools/python_oracle_rows.py 600 684)` | `VERIFY.md:394-400`; `python_oracle_rows.py:75-99` | Not from the package alone. The script reads `oracle/final/august_inputs/row_600.npz` (in the package only as `capsule/reexecute/row_000600.npz`, and nothing says to copy it into place), asserts the positive control on `oracle/final/vectors/vectors_int16_d2_1328_{correct,wrong_p2}.npz` (data layer), and `QuantModel("int16")` recalibrates on the August cached rows `oracle/rows_august/...` (data layer). Needs torch and numpy. Documented as "with the data-layer files placed" (`capsule/README.md:66-67`). |
| d4 | what the acceptance verifier compares instead | checks `oracle.r_correct`, `oracle.r_wrong` against `expected_residual_int16` from `oracle/final/august_inputs/manifest.json` | `accept.rs:323-330`; `STATEMENT.md:232-233` | Present; a table lookup against the prover's own oracle, not a recomputation. |

Conclusion for (d): one proved row, 600, can be recomputed natively from the package alone with no toolchain; every
other row needs one frame from the data layer; the Python second implementation needs the data layer in any case.

### (e) Reproduce a proof

| # | step | command | source | complete? |
|---|---|---|---|---|
| e1 | GPU stack | `replicate.sh toolchain gpu`: `sp1-gpu-server` 6.4.0 (URL, tarball `2946b0b4…`, binary `f68b85dc…`, 250,950,472 bytes) and the Groth16 v6.1.0 circuit tarball (6,211,807,514 bytes, size only; seven files pinned by SHA-256) into `~/.sp1` | `VERIFY.md:131-132`; `replicate.sh:80-95`, `295-345` | Pinned and sourced, not present; about 6.2 GB of downloads; needs a CUDA 12 runtime and a GPU with more than the observed 28.5 GiB peak (`replicate/README.md:64-66`). |
| e2 | prove | `"$P/replicate/replicate.sh" --from-local "$P" prove 600 --device 0 --frame "$P/capsule/reexecute/frame_000600.raw"` (my composition; the README's form is `./replicate.sh prove 600 --device 0 --frame /path/to/frame_000600.raw`, `replicate/README.md:56`) | `replicate.sh:891-926`; the node's own command is `receipts/row_000600_receipt.json` `command` | Everything but the GPU stack and the network is present for row 600. The script rebuilds with `CUDA=1` (`--features cuda`), runs `zkdiff-batch prove --prover cuda`, judges the run by the receipt and a cold `zkdiff-verify` (the pinned `sp1-cuda` client panics in a destructor after writing, `replicate/README.md:62-63`), and `cmp`s the fresh statement with the published one; the proof bytes will differ because Groth16 is randomised (`FAQ.md:287-289`). |
| e3 | what to expect | 45.9 min alone on one A100-SXM4-80GB, 61 to 67 min with eight sharing a node | `RESULTS.md:183-194`, `324` | Information only. |

Two gaps: the GPU wrapper "has not been executed on a GPU" (`replicate/README.md:119-121`, `TEST_LOG.md:173-175`), and
whether Go is needed is stated two ways (question 12 below).

---

## 3. Questions I could not answer from the package alone

1. **Is the data layer populated now?** `FAQ.md:279-281`: "Until the upload is released the prefix is empty."
   `FRAMES.md:12-15`: the frames "are served from the data layer"; `README.md:154-156`: "the principal decided to publish";
   `TEST_LOG.md:21`: "nothing was public yet"; `FRAMES.md:140`: "Staged 2026-09-08T16:37:42Z" (staged, not uploaded).
   Every route beyond row 600 depends on the answer. Expected in `FRAMES.md` or `REDACTION.md` "What is published", as a
   dated statement with the `_control/RELEASE.json` digest of the live prefix.
2. **Is the repository live, and at which commit?** `replicate.sh:37`, `105` clones `poliebotics/dark-lantern` at `main`;
   `TEST_LOG.md:131`: "The GitHub URL itself cannot be exercised until item 032 is pushed." Expected in `replicate/README.md`.
3. **Do the data layer's `_control/` manifests list the files added on 8 September?** `replicate.sh:533-540` fails if any
   `LARGE_FILES_SHA256SUMS` entry is "not in the data-layer manifest"; `LARGE_FILES.md` grew from 2,500 to 4,664 files
   (`VERIFY.md:445`; `LARGE_FILES.md:45`). Expected in `LARGE_FILES.md`.
4. **The authority manifest** whose SHA-256 `740d752d…d783` enters the context digest: bytes not published, "not decided at publication" (`FAQ.md:26-31`; `HASHES.md:36`).
5. **Where the d2 and v10 sessions can be obtained and when they were recorded**: "not decided at publication" (`FAQ.md:111-119`).
6. [Question about the patent filing's details redacted; the package states the filing by date only (`README.md`, `LICENSE`).]
7. **The staging tools** `fill_results.py`, `stage_package.py`, `make_pins.py`, `evidence_allowlist.py` that rendered
   `RESULTS.md` section 6, `REDACTION.md`, `LARGE_FILES.md`, `PINS.json` and `receipts/`: not shipped (`FAQ.md:283-285`).
8. **Would the residual sums or signs change under a scale map calibrated without the seven August rows?** "Not measured"
   (`FAQ.md:152-155`); the rehearsal shows only that the histogram differs (`VERIFY.md:374-377`). Expected in `CLAIM_BOUNDARY.md`.
9. **What is the fourth `meta` field, the u32 that "reads 64000 on every row"?** Marked `[confirm]` (`GLOSSARY.md:72`;
   `FAQ.md:45`). Expected in `STATEMENT.md` section 3.
10. **Has the package in this state been read again by the second model?** "has not been re-read by the second model, which
    is a publication decision" (`FAQ.md:258-260`; `AUDIT_TRAIL.md:150-153`).
11. **Whether the 288-row sealed take, the eight-seed AUROC, the original checkpoint and the coupling packet exist as
    stated**: external referents, defined only in words (`FAQ.md:127-133`; `GLOSSARY.md:24-25`, `28-30`).
12. **Does proving need Go?** `VERIFY.md:119-120`: Go "is needed only to prove, through the `groth16` feature, which nothing
    here enables"; the node built with `--features cuda` only (`source/node_prep/r5/build_record_20260907T215855Z.txt:5`)
    and produced Groth16 proofs, and `replicate.sh:661-667` does the same; but `RELATION.md:390-393` says
    "`cargo build --release --locked --features groth16,cuda`" and "Go >= 1.24". Expected in `VERIFY.md` section 2 or
    `replicate/README.md`.
13. **How to run the Python oracle on row 600 offline.** `capsule/reexecute/row_000600.npz` is shipped, but
    `python_oracle_rows.py:89` reads `oracle/final/august_inputs/row_000600.npz`, and lines 77-79 assert on
    `oracle/final/vectors/*.npz` (data layer); nothing says to copy the capsule file into place or that the positive control
    needs the data layer. Expected in `capsule/README.md` or `VERIFY.md` section 7.
14. **Why `expected_identities_august.json` `sources.g1_manifest.sha256` is `3e69c6cd…`** when the published
    `oracle/final/august_inputs/manifest.json` is `a3fb8947…` (`REDACTION.md:74`), and where
    `sources.prepare_manifest` (`batch_prepare_g2d_20260907/BATCH_MANIFEST.json`, named in `make_expected_identities.py:14`)
    is: only `row_000684/` exists under that directory. `PINS.json:36` says the file "is left byte for byte as frozen", which
    explains the first without naming it. Expected in `PINS.json` `path_conventions` or `REDACTION.md`.
15. **Whether the repository's root `THIRD_PARTY_NOTICES.md` gained the row for the capsule binaries.**
    `capsule/THIRD_PARTY_NOTICES.md:13-14`: "it must gain a row for these binaries before publication (an item for the
    principal, `OPEN_ITEMS`)". `OPEN_ITEMS` resolves nowhere.
16. **Where `CITATION.cff`, `THIRD_PARTY_NOTICES.md` and `licenses/` are**: `LICENSE:35-36`, `55-56`, `58-61` name them at the
    repository root; none is in the package.
17. **What the scene contained.** `README.md:32`: the frames "speak for themselves"; no description and no note on how to
    view a raw 4600 x 5320 RGGB frame is given. Expected in `FRAMES.md`.
18. **Why one frame gap is 533.8 ms** against a median of 400.05 ms (`PINS.json:79-83`). Expected in `STATEMENT.md` 1a.
19. **The timing pilot's report and the node identity records** quoted in `RESULTS.md` section 5 and `PINS.json:954` are
    "on-box".
20. **The withheld prover stderr** (destructor-panic backtraces) cannot be inspected; the package says why (`FAQ.md:331-333`).
21. **The `vk root` constant** can be checked only in the `sp1-verifier` 6.4.0 crate source (`HASHES.md:23`), which needs
    crates.io.
22. **Whether the two "about two minutes" figures** (`README.md:75`; `VERIFY.md:19`; `capsule/README.md:20`) or the measured
    3 min 25 s (`capsule/README.md:95-96`) is the expectation to plan by.

Items 4 to 7, 10, 19 and 20 are stated openly by the package as pending or withheld; they are listed for completeness.

---

## 4. Obstacles, ranked by severity

Severity 1 (sends an agent down the wrong path or leaves a rung of the ladder undeterminable)

1. **The package says both that the frames and tensors are published and that they are held.** `FRAMES.md`, `README.md:154-156`
   and `REDACTION.md:87-94` say published; but `VERIFY.md:298` still reads "the frames themselves are not published
   (`REDACTION.md`)", `HASHES.md:41` and `:53` "needs the frame (held)", `HASHES.md:66` "the August input and vector sets
   held", `GLOSSARY.md:35` "Raw frames are never published (`REDACTION.md`)", `FAQ.md:108-109` "the frames are held, so a
   reader cannot see it here", `replicate/README.md:101` "**Raw frames are not published** (programme rule)", `:104`
   "**The August camera-derived tensors are held pending clearance**", `replicate.sh:822`, `856`, `893`, `947` (the
   messages a user of the kit actually sees), `Dockerfile:11`, `TEST_LOG.md:12`, `176-177`. An agent reading `VERIFY.md`
   section 4 or the replication kit concludes that (d) and (e) are impossible while `capsule/reexecute/` makes (d) possible
   for row 600 today.
2. **The publication state itself is unknowable and self-contradictory** (questions 1 to 3): `FAQ.md:281` "Until the upload is released the prefix is empty" beside `FRAMES.md:12` "served from the data layer". Every step past row 600, and the
   kit's default GitHub fetch, hangs on it.

Severity 2 (misleads or stalls a careful reader)

3. **The glossary contradicts the claim boundary on the screen rows.** `GLOSSARY.md:134-136`: "the trainer's quick screen
   scored 28 of them during training"; `CLAIM_BOUNDARY.md:27-31`, `RESULTS.md:40-43` and `FAQ.md:144-150` say 24 of the 28
   are training rows and four are proof rows, and that the earlier "28 held-out rows" wording was corrected. The glossary
   carries the uncorrected version.
4. **The kit does not re-execute a real row unless told where the frame is.** `README.md:76-77`: `replicate.sh all --no-prove`
   "re-executes a row"; `replicate.sh:825-828`: without `--frame` it runs the synthetic session instead, and neither
   `execute` nor `prove` fetches a frame from the data layer's `frames/` or defaults to the shipped
   `capsule/reexecute/frame_000600.raw`. The one-pull claim is true of the synthetic session, not of an August row.
5. **`VERIFY.md` says no `[confirm]` tag remains, and three do.** `VERIFY.md:37-39`: "After the rehearsals of 8 September 2026
   none remains"; `VERIFY.md:360`, `420`, `473` still carry `**[confirm]**` (August export regeneration; the full oracle
   regeneration on the published tree).
6. **The "nothing installed" route is a trust-the-binary route on one platform.** Honest about it (`capsule/README.md:74-78`;
   `VERIFY.md:220-221`), but `README.md:74-75` "With nothing installed" omits "x86_64 Linux" and "trusting the shipped binary
   or rebuilding it"; the rebuild needs the network.
7. **Frozen records contradict the final state at the contradicting line, with only a banner to warn.** `RELATION.md:390-393`
   (`--features groth16,cuda`, Go) against the node record and `VERIFY.md:119-120`; `RELATION.md:213-214` sends the reader to
   `noise_proposal/`, which is omitted (`REDACTION.md:97-98`); `FULL_GUEST.md:4`, `48`, `340-348` "[pending node]" (banner at
   `:10-15` closes them); `FREEZE_SUMMARY.md:35-38` lists private digests of `AGREEMENT.md`, `README_FINAL.md` and
   `agreement.json` (`REDACTION.md:19-21` explains the two Markdown files, not `agreement.json`, whose published digest is
   `2926e0f1…`, `REDACTION.md:75`).
8. **Provenance pointers inside `expected_identities_august.json` resolve to private bytes or nowhere** (question 14): the
   G1 manifest digest is the pre-rename private one and the prepare manifest is not shipped. Every receipt pins this file by
   digest, so it cannot be edited; a line in `PINS.json` `path_conventions` naming these two facts would close it.
9. **Stale sizes and times.** `replicate/README.md:21`, `47`: "331 MB of data-layer files" against `LARGE_FILES.md:45`
   "4664 files, 633,315,259 bytes"; "about two minutes" against 3 min 25 s (item 22).
10. **Dangling references and an internal to-do in a published file.** `LICENSE` names `CITATION.cff`, `THIRD_PARTY_NOTICES.md`
    and `licenses/` (absent); `capsule/THIRD_PARTY_NOTICES.md:13-14` ends with a task for the principal and an unexplained
    `OPEN_ITEMS`.
11. **The oracle manifest's rule text omits the lower bound.** `oracle/final/august_inputs/manifest.json:14`: "if r+offset >=
    712 use -offset"; `rule.rs:6-8` and `check_offset_rule` handle both bounds. Harmless for rows 600 to 711 (smallest
    `r + o` is 585), as `FAQ.md:220-222` says of `common.py`, but the manifest text is not covered by that answer.

Severity 3 (friction)

12. `STATEMENT.md:99` gives the 24 bytes at offset 692 as "4+8+8+4" for seven fields without saying which is which; the
    decoder (`decode_zbdiff01.py:41`) and `statement.rs:279-282` show u32, i64, i64, then four single bytes.
13. `check_identities.py` compares `leaf_r`, `leaf_u` and the emission digests with the frozen table and chain log
    (`:76-83`) but recomputes neither; the recomputation lives only in the Rust tests and the batch driver (`HASHES.md:37-42`),
    so a Python-only reader confirms consistency, not derivation.
14. The reading load: eighteen top-level documents plus a 630-line `FULL_GUEST.md` and a 433-line `RELATION.md`, with the
    rule "a sentence elsewhere that seems to say more than they do is to be read as saying no more" (`CLAIM_BOUNDARY.md:13`)
    the only precedence rule; the banners on the frozen copies help, but the reader still reconstructs the chronology.
15. `receipts/README.md:101` lists the ten files outside the node ledger with a trailing "…" instead of the ten names.

---

## 5. Three things the package does well

1. **The capsule closes the loop that round one said was open.** Two static verifiers, the static batch driver, row 600's
   frame and oracle inputs, one script that asserts both counts of 112, runs the 18 controls and the raw form, and
   byte-compares its copies with the package's; a second script that recomputes a proved row's statement from its raw frame
   and `cmp`s it with the published bytes; build and relink records with digests; a `--network none` container rehearsal
   with timings (`capsule/verify_offline.sh`; `capsule/reexecute/reexecute_row.sh`; `capsule/README.md:91-100`).
2. **Every constant is pinned once and repeated identically wherever it is needed, in machine-readable form.** The ELF
   digest, vkey, circuit key, constants digest, expected-identities digest and chain-log digests are the same strings in
   `PINS.json`, `expected_identities_august.json`, `build_reproducible.sh:15-18`, `replicate.sh:42-51`,
   `capsule/verify_offline.sh:11-14`, `capsule/BUILD_RECORD.txt`, the node build record, the launch identity files and all
   112 receipts; row 600's frame digest is the same in `FRAMES.md`, the receipt, the chain log and `capsule/reexecute/SHA256SUMS`;
   `tools/check_identities.py` and `tools/regen_noise.py` let a Python-only reader confirm every statement's identities and
   the noise rule, and `HASHES.md` says of what each digest is a digest.
3. **The claim is scoped and the process is on the record.** `CLAIM_BOUNDARY.md` governs; the calibration and quick-screen
   disclosures name the rows; the acceptance verifier records 35 named checks with details and "never derives a key from an
   ELF it is handed"; the controls are split into relation and policy layers with the error text kept; the pending owner
   decisions are labelled as such in `FAQ.md`; the full audit texts, including the three round-one reports with verdict
   `NO`, are published verbatim in `audits/`.

---

## 6. Verdict

**YES WITH EFFORT.** With this package alone, on an x86_64 Linux box with about 17 GB of RAM and no network, an agent can
verify all 112 Groth16 proofs under the pinned key and every frozen identity, decode and cross-check every statement in
Python, regenerate the normative noise from its rule, and recompute row 600's residual sums from its raw frame; rebuilding
the program, recomputing any other row and re-proving are fully specified with pinned, sourced downloads but need the
network and a data layer whose live state the package itself leaves in doubt. **Single most important fix:** remove every
surviving "frames are not published / tensors are held" sentence (`VERIFY.md:298`, `HASHES.md:41`, `:53`, `:66`,
`GLOSSARY.md:35`, `FAQ.md:108-109`, `replicate/README.md:101-106`, `replicate.sh:822`, `:856`, `:893`, `:947`,
`Dockerfile:11`) and replace `FAQ.md:281` with one dated statement of what is live on the data layer and in the
repository, then let `replicate.sh execute` and `prove` take a frame from `frames/` on the data layer or default to
`capsule/reexecute/frame_000600.raw`, so that the kit's "re-executes a row" is true of a proved row.
