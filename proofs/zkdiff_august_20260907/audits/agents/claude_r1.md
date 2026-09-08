> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

# Outside-agent readability audit of `zkdiff_agent_audit_pkg` ("A Tale of Two Conditionings")

Auditor: an outside AI agent (Claude), working only by reading the supplied package.
Method: every top-level document read in full; the engineering records (`source/armc-relation/RELATION.md`,
`source/FULL_GUEST.md`, `oracle/final/README_FINAL.md`, `AGREEMENT.md`, `FREEZE_SUMMARY.md`), the verifier sources
(`accept.rs`, `verify.rs`, `rule.rs`, `statement.rs` excerpts, `spec.rs`, `adapter/src/lib.rs`, `program/src/main.rs`,
`build_reproducible.sh`, `G2D_NODE_RUNBOOK.sh`), the receipts for rows 600 and 684, the merged manifest, `PINS.json`,
`expected_identities_august.json`, the chain log, the model logs and the decoder read or searched. Nothing was
executed: no build, no proof, no hash computed. Where I say a file "is present" I checked existence and byte size only;
where I say a number "matches" I compared text against text. Line numbers are those of the package files.

---

## 1. What I understood the package claims

1. For each of the 112 August rows 600 to 711 there is one SP1 6.4.0 Groth16 proof (356-byte raw proof, 752-byte public
   statement) that an integer diffusion denoiser "adapted from the frozen ARM-C protocol and run in exact fixed point,
   produced the published residual sums on the whole sensor frame of that row" under the row's own emission and under a
   declared wrong row's emission (`README.md:14-24`; `STATEMENT.md:16-41`).
2. Each proof binds its inputs rather than trusting the prover: the raw frame is hashed in circuit and opened to the
   committed session tree, the chain state is re-derived from an authenticated predecessor under verified drand quicknet
   beacons, both emission patterns are re-rendered from chain states, the noise tensor is bound by its BLAKE3 and the
   network constants by their SHA-256 (`README.md:17-22`; `STATEMENT.md:21-36` and `108-123`).
3. All 112 proofs verified and were accepted under the frozen identities, every signed difference `D = R_wrong - R_correct`
   is positive, no row has a nonzero clip count, and `D` in MSE units runs from 0.007328 to 0.010988 with median 0.009161
   (`README.md:11`; `RESULTS.md:190` and `315`).
4. The claim is execution binding only: "They establish no physical-capture, realness, liveness, illumination-causality,
   adversarial-resistance or unseen-session-generalisation claim" (`CLAIM_BOUNDARY.md:19`; `README.md:63-68`).
5. Rows 600 to 711 were held out from weight training but seven of them entered quantisation calibration, the d2/v10
   evaluation blocks are development validation on which the proof model was selected, and the proof model reached
   AUROC 1.0 and paired fraction 1.0 on those blocks (`CLAIM_BOUNDARY.md:17` and `23-32`; `RESULTS.md:29-32` and `45-50`).

---

## 2. The verification path

Notation: `P` is the package root, as `VERIFY.md:23` asks (`P=/absolute/path/to/zkdiff_august_20260907`).

### (a) Verify one proof (row 600)

| # | step | command or action | source | package gives everything? |
|---|---|---|---|---|
| a1 | check the ledger | `(cd "$P" && sha256sum -c --quiet SHA256SUMS && [ "$(grep -c . SHA256SUMS)" = "$(find . -type f ! -name SHA256SUMS \| wc -l)" ] && echo LEDGER_OK)` | `VERIFY.md:32` | Yes. `SHA256SUMS` has 2,703 entries; all 2,703 paths exist and no file outside the ledger exists (checked by listing, not by hashing). |
| a2 | decode the statement | `python3 "$P/tools/decode_zbdiff01.py" "$P/public_values/row_000600_public_values.bin"` | `VERIFY.md:163`; layout `STATEMENT.md:49-76` | Yes. Standard library only (`tools/decode_zbdiff01.py:12`). Expected fields: row 600, wrong_row 598, offset -2, direct, `r_correct` 4435539299, `r_wrong` 11254163581 (`RESULTS.md:202`; `receipts/row_000600_receipt.json` `decoded`). |
| a3 | Groth16 layer with the vendored standalone verifier | `(cd "$P/tools/standalone_verifier" && cargo build --release --locked)` then `"$P/tools/standalone_verifier/target/release/zeebeam-standalone-verifier" "$P/proofs/row_000600_groth16_proof.bin" "$P/public_values/row_000600_public_values.bin" 0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027` | `VERIFY.md:58-62`; expected last lines `tamper_public_byte_87_rejected=true`, `wrong_vkey_rejected=true`, `VERIFIED` (`VERIFY.md:67`; `src/main.rs:35-38`) | Source, `Cargo.toml`, `Cargo.lock` (209 packages, `sp1-verifier 6.4.0`) and the key are in the package. Missing: a Rust toolchain and either the network or a cargo home holding the 209 crates (`VERIFY.md:65-66`). No URL or hash for `rustup`/`cargo` is given. |
| a4 | full acceptance (identities) | build first (see (c)), then `S="$P/source/armc-relation/script/target/release"; "$S/zkdiff-verify" --proof "$P/proofs/row_000600_groth16.bin" --expect "$P/source/expected_identities_august.json" --report /tmp/row_000600.verify.json`; raw form `"$S/zkdiff-verify" --proof-bytes "$P/proofs/row_000600_groth16_proof.bin" --public "$P/public_values/row_000600_public_values.bin" --expect "$P/source/expected_identities_august.json"` | `VERIFY.md:127-138`; checks listed `STATEMENT.md:194-204`, implemented `source/armc-relation/script/src/accept.rs:7-24` and `198-340` | The verifier source, the frozen table (`expected_identities_august.json`, 119,375 bytes as pinned) and the report format are present. Missing: the SP1 6.4.0 toolchain (`zkdiff-verify` embeds the guest ELF, `verify.rs:36`, so it cannot be built without `cargo-prove`), `protoc`, GNU time, binutils and the network for the first `cargo fetch` (`VERIFY.md:89-113`; the fetch from an empty cargo home is the one step marked **[confirm]**, `VERIFY.md:111-113`). |
| a5 | compare | the report's `statement` object against `RESULTS.md:202` and `receipts/row_000600_receipt.json` (`acceptance.checks`, all PASS); the node's own report is `receipts/row_000600_verify.json`, the development machine's `receipts/independent_verify/row_000600.verify.json` | `VERIFY.md:133-134`, `149-150` | Yes. |
| a6 | optional proof-level negative controls | `"$S/zkdiff-verify" --proof "$P/proofs/row_000600_groth16.bin" --expect "$P/source/expected_identities_august.json" --controls --report /tmp/controls.json` | `VERIFY.md:155-158`; node record `receipts/proof_controls.json` | Yes, given a4. |

### (b) Verify all 112

| # | step | command | source | complete? |
|---|---|---|---|---|
| b1 | Groth16 layer, all rows | `for r in "$P"/proofs/row_*_groth16_proof.bin; do b=$(basename "$r" _groth16_proof.bin); "$P/tools/standalone_verifier/target/release/zeebeam-standalone-verifier" "$r" "$P/public_values/${b}_public_values.bin" 0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027 \| grep -q '^VERIFIED$' \|\| { echo "REJECTED $r"; exit 1; }; done && echo "standalone: 112 VERIFIED"` | `VERIFY.md:71-75` | Yes, given a3. 112 raw proofs (356 bytes each) and 112 statements (752 bytes each) are on disk. |
| b2 | acceptance, all rows | `for p in "$P"/proofs/row_*_groth16.bin; do "$S/zkdiff-verify" --proof "$p" --expect "$P/source/expected_identities_august.json" > /dev/null \|\| { echo "REFUSED $p"; exit 1; }; done && echo "every proof accepted"` | `VERIFY.md:144-147` | Yes, given a4. The 112 framed artifacts are on disk at 2,444/2,445/2,446/2,447 bytes (1/12/59/40 files), matching `PINS.json` `batch.framed_proof_bytes_histogram` and `RESULTS.md:315`. |
| b3 | cross-check the rendered table | each row of `RESULTS.md:202-313` against `receipts/row_XXXXXX_receipt.json` and `PINS.json` `batch.proofs` (full digests) | `RESULTS.md:193-197` | Yes, but by hand or by a script the reader writes; `fill_results.py`, named as the renderer, is not in the package. |

### (c) Rebuild the program and compare its identity to the pinned one

| # | step | command | source | complete? |
|---|---|---|---|---|
| c1 | install the toolchain | Rust 1.98.0 via rustup (`source/armc-relation/rust-toolchain` pins `channel = "1.98.0"`); `sp1up --version v6.4.0` (installs `cargo-prove sp1 (f66b4bf 2026-08-12)` and succinct `rustc 1.94.0-dev`); `protobuf-compiler`, `libprotobuf-dev`, `time`, binutils | `VERIFY.md:89-101` | Partly. Hashes to compare are given (`PINS.json:793-797`: `cargo_prove_sha256 d8835f80…`, `succinct_toolchain_tarball_sha256 12c94435…`), but no download location for `sp1up` or the tarball, and nothing in the package can be used offline. |
| c2 | fetch the locked crates once | `(cd "$P/source/armc-relation/script" && CARGO_NET_OFFLINE=false cargo fetch --locked)` and `(cd "$P/source/armc-relation/program" && CARGO_NET_OFFLINE=false cargo +succinct fetch --locked --target riscv64im-succinct-zkvm-elf)` | `VERIFY.md:107-108`; the workspace forces `offline = true` (`source/armc-relation/.cargo/config.toml`) | Needs the network; explicitly "not rehearsed on the release machine" **[confirm]** (`VERIFY.md:111-113`). Also needs the two git patches (`bls12_381` fork, `program/Cargo.toml` via `[patch.crates-io]` in `script/Cargo.toml:41-42`). |
| c3 | build and assert | `(cd "$P/source/armc-relation" && ./build_reproducible.sh)`; last line must be `BUILD_REPRODUCED_OK` | `VERIFY.md:116-124`; pins hard-coded at `build_reproducible.sh:15-18` (ELF sha256 `51b7bc35…75cc`, 396,200 bytes, vkey `0x00f01894…a027`, circuit key `4388a21c…e696`); asserts at lines 105-109 | Yes given c1 and c2. Note the ELF itself is not shipped (`PINS.json:6`: "rebuilt by … build_reproducible.sh; not shipped"), so the only way to hold the pinned program is to rebuild it. `--pin` prints observed values without asserting (`build_reproducible.sh:12`). |
| c4 | compare identities | `"$S/zkdiff-verify" --identity` must print `sp1_circuit_version v6.1.0`, `groth16_vk_sha256 4388a21c…`, `guest_elf_sha256 51b7bc35…`; compare with `PINS.json:7-12`, `source/expected_identities_august.json:4-8`, the node build record `source/node_prep/r5/build_record_20260907T215855Z.txt` and the launch identity file `receipts/gpu0_inputs_identity_launch.txt` (ELF, blob, chain log, expected identities, build record) | `VERIFY.md:127-133`; `verify.rs:72-89` | Yes. The prover's own three reproductions (two machines, two absolute paths) are recorded (`FULL_GUEST.md:218-223`; `PINS.json:803-824`). |
| c5 | check the source digests | `source/node_prep/r5/SOURCE_DIGESTS_20260907T215855Z.txt` and `source/armc-relation/runs/SOURCE_DIGESTS_*.txt` | `REDACTION.md:13-16` | Not checkable against the published bytes: the lists "were computed over the private bytes and therefore do not validate the substituted files" (two comment-only substitutions in `ceremony.rs`, `ceremony_core.rs`). The rebuild is the check. |

### (d) Reproduce one row's residual sums

| # | route | what it needs | present? |
|---|---|---|---|
| d1 | an August proof row (600): recompute `C_int` from the raw frame, `hint` from the chain-log states, `C_t` from the normative noise, run the int16 network, sum | the raw frame `frame_000600.raw` (24,472,000 bytes) or the exported `C_int`/`Ct_int` | **No.** "Raw sensor frames are never published" and the August `C_int`, `Ct_int`, cached rows, vector sets and export sets "are held pending the principal's separate clearance" (`REDACTION.md:71-75`, `81-94`). Only two of the three inputs are derivable: the hint from `S_t` in `source/vectors_relation/august/chain_log.csv` and the noise from `source/noise_august/noise_000600.i16` (or from the rule via `oracle/common.py:226 randn_cuda_emul`). |
| d2 | the Python oracle on August rows | `source/tools/python_oracle_rows.py` | No: "its August inputs are held regardless" (`REDACTION.md:52`), and the frozen scale map cannot be recomputed without the held rows (a public-rows run "recalibrates on 8 rows and yields a different one", `VERIFY.md:274-281`). |
| d3 | the nearest self-contained check: d2 row 1328 through the Rust adapter with the FINAL blob | `(cd "$P/source/armc-relation" && cargo test --release --offline …)`; the test `d2_row_1328_with_the_final_blob_reproduces_g1s_residual_sums` expects 8,764,459,045 and 22,311,372,969 | Yes: `source/vectors_relation/d2/` carries `row_001328_C_q12_cache.bin`, `row_001328_noise_q12.bin`, `row_001328_Ct_q12.bin`, `row_001328_hint14_q14.bin`, and the blob is present (3,476,866 bytes). But this is a development row, not one of the 112 proved rows (`FULL_GUEST.md:232-235`; `VERIFY.md:230-249`). |
| d4 | the layer-by-layer parity tests on the FINAL export sets | `source/oracle_final/` (data layer) or regeneration from `oracle/final/vectors/*.npz` (data layer) | Not in this copy: all 2,500 data-layer files are absent, and the August halves are held anyway (`VERIFY.md:230-236`; `LARGE_FILES.md:26-39`). |
| d5 | what the acceptance verifier compares instead | `oracle.r_correct` / `oracle.r_wrong` against `expected_residual_int16` in the frozen table, sourced from `oracle/final/august_inputs/manifest.json` `rows[600].expected_residual_sum_int.int16` | Present (`accept.rs:324-330`; `source/expected_identities_august.json` row 600; `manifest.json:1100-1125`). It is the prover's own oracle, so this is a consistency check, not an independent reproduction. |

Conclusion for (d): for any of the 112 proved rows the residual sums cannot be reproduced from the package; the
package states this plainly and it is a deliberate hold, not an omission of instructions.

### (e) Reproduce a proof

| # | step | command | source | present? |
|---|---|---|---|---|
| e1 | build with proving features on a GPU box | `CUDA=1 build_reproducible.sh` (adds `--features cuda`); Groth16 wrap needs `--features groth16` ("Go >= 1.24", `script/Cargo.toml:9-13`) | `build_reproducible.sh:13,30`; `FULL_GUEST.md:479-484`; `RELATION.md:389-391` | Source yes; `sp1-gpu-server` 6.4.0 (hash `f68b85dc…`, `PINS.json:887`) and the v6.1.0 Groth16 circuit files (hashes `PINS.json:889-897`; `groth16_pk.bin` 5,862,173,061 bytes per the node build record) have no download source in the package. |
| e2 | prove one row | `./target/release/zkdiff-batch prove --prover cuda --device N --cycle-limit 200000000000 --chain-log "$CHAIN" --rows R..R --frames-dir "$FRAMES" --noise-dir "$NOISE" --blob "$BLOB" --expect "$EXPECT" --build-record "$BUILD_RECORD" --out "$out"` | `source/node_prep/G2D_NODE_RUNBOOK.sh` (`prove-one`, `prove`); exact command as run in `receipts/row_000600_receipt.json` `command` | **No.** `--frames-dir` must hold `frame_000600.raw`, which is held (d1). Everything else (chain log, noise, blob, expected identities, build record) is present. |
| e3 | cost | about 46 min alone or 61 to 67 min with eight concurrent processes on one A100-SXM4-80GB | `RESULTS.md:176-185`, `315`, `321` | Information only. |

Conclusion for (e): not possible from the package; `VERIFY.md:348` says so ("proving was not rehearsed and is not part
of verification"). Whether a re-proof would be byte-identical to the shipped proof ("proof nonce zero",
`FULL_GUEST.md:503`) is not stated.

---

## 3. Questions I could not answer from the package alone

Hashes and identities

1. What is the `vk root 002f850ee998974d6cc00e50cd0814b098c05bfade466d28573240d057f25352` printed in every acceptance
   report (`receipts/row_000600_receipt.json:12`)? It is `sp1_verifier::VK_ROOT_BYTES` (`accept.rs:176-178`) but no
   document says what it commits to or why it matters. Expected in `STATEMENT.md` section 9 or `VERIFY.md` section 2.
2. What is the "authority manifest" whose SHA-256 `740d752d…d783` sits at offset 164 (`STATEMENT.md:63`)? Neither the
   document nor its origin is described anywhere. Expected in `STATEMENT.md` section 2 or `VERIFY.md` section 4.
3. How was `S_0` (`74e3a131…384c`) chosen or derived, and what is `S_N` beyond "the last advance yields `S_N`"?
   Expected in `STATEMENT.md` section 2.
4. How exactly are the context digest, the leaves, the nodes, the padding and the "wrapped" root computed? `STATEMENT.md:64-66`
   says only "recomputed" and writes the leaf as `H(ROW, ..., S_{r+1}, emission_r)` (line 117). The actual definition,
   `H(ROW, [context, u32be(row), s_t, raw_blake3, meta, u64be(round), value, s_next, emission_blake3])` with domain strings
   `ZEEBEAM_ORDERED_SESSION_{CONTEXT,ROW,NODE,ROOT,PADDING}_V1\0`, exists only in `source/armc-relation/relation/src/membership.rs:25-28,193,218,244,307-312`.
5. What are the fields of the 28-byte `meta`? `header.rs:7` gives the struct format `">IQQI4s"` with `meta[0..4] BE == row index`;
   the two `Q`s, the second `I` and the `4s` (e.g. `…0000fa0052473038`) are unexplained. Expected in `STATEMENT.md` section 3.
6. What is the exact `advance_chain` construction (`ROW_DOMAIN_TAG`, field ordering)? Only in `source/armc-relation/b3xof/src/lib.rs:252-264`.
   Expected in `STATEMENT.md` section 4 leg 4.
7. What does the receipt control `sdk.wrong_vkey` mean by "verifying key preprocessed commitment rotated:
   0x007fb8c7…"? Expected in `receipts/README.md`.
8. Where can `cargo-prove` (`d8835f80…`), the succinct toolchain tarball (`12c94435…`), `sp1-gpu-server` (`f68b85dc…`)
   and the v6.1.0 circuit files be obtained so that the hashes in `PINS.json:793-797,887-897` can be checked? No URL.
   Expected in `VERIFY.md` section 2.
9. What is in the node's `SHA256SUMS_RUNS` beyond the shipped files, and how would a reader ever use the digests of
   withheld files (`receipts/README.md:6-7,67-84`)? Expected in `receipts/README.md`.

Public-output fields

10. What is protocol "TB-v0.9" (byte 9 = 9, `STATEMENT.md:53`, `header.rs:6,16`)? Never expanded.
11. What do `MAINNET`, `BLOCKING`, `TRAINING`, `300S` mean in the session id `ZEEBEAM_MAINNET_BLOCKING_TRAINING_300S_20260822_001`?
    Expected in `README.md` or `STATEMENT.md` section 2.
12. Why do rows `r-1` and `r` carry the same drand round for most rows? Row 600's statement has `prev_drand_round` =
    `own_drand_round` = 31521690 (`receipts/row_000600_receipt.json` `decoded`); the chain log shows rows 598 to 601 all at
    31521690, only 66 distinct rounds across 712 rows, and a `drand_staleness_ms` column of 5.7 to 7.8 s that is never
    mentioned. `STATEMENT.md:24-26` says the guest "verifies the drand quicknet BLS signatures of rows r and r-1", which for
    646 of the 711 consecutive pairs is the same signature twice. Is round monotonicity checked? What is the relation
    between rows (about 400 ms apart by `capture_wall_ns`) and beacon rounds (3 s)? Expected in `STATEMENT.md` section 1
    item 2 and `VERIFY.md` section 4.
13. Which quicknet public key is compiled in (`beacon.rs:24`), and is chain hash `52db9ba7…` the only out-of-band fact a
    verifier must hold? `VERIFY.md:196-198` names the chain; the key bytes are only in source.
14. What are `F_CT`, `F_HINT`, `F_EPS` (offset 692, `STATEMENT.md:73`)? Fractional bits, inferable from
    `README_FINAL.md:128-132`, but never named as such where the layout is given.
15. What is a "masked-table hit" counted into the clip count (`STATEMENT.md:76`)? Defined only in
    `oracle/final/README_FINAL.md:117-124`.
16. Why is the denominator `43008 · 2^24` (`STATEMENT.md:74`)? The decomposition (4 x 96 x 112 values, Q12 squared) is
    implied at `STATEMENT.md:147` but not stated.

Datasets and the recording

17. What are sessions d2 and v10 (what was recorded, when, how many rows, where the "public Truth Beam sessions" of
    `REDACTION.md:77` can be obtained)? Expected in `RESULTS.md` section 1.
18. Which row ranges are the d2/v10 "training blocks" as against the "three contiguous evaluation blocks of 400" and
    "two blocks of 250" (`RESULTS.md:23-24`)? The block boundaries are not given. Expected in `RESULTS.md` section 1.
19. What is the August session physically? "projector-camera session" (`README.md:14`) is the whole description. What
    was projected, what scene, what camera (the spec says `uint8 4600x5320 row-major RGGB`, `spec.rs:9`), what exposure?
    Expected in `README.md`.
20. What is an "emission pattern" and the "four-octave integer render" of "1080 rows" (`STATEMENT.md:27`, `115`)? The
    algorithm is in `b3xof` and `emission.rs`; its meaning (a projected pattern derived from the chain state) is never
    said. Expected in `STATEMENT.md` section 1 item 3.
21. What does "ARM-C" stand for, and where is "the frozen ARM-C protocol" published? The package uses it as a name
    (`STATEMENT.md:151`, `RESULTS.md:16`), the class is `ArmCUNet` (`oracle/trainer/train_lean.py:156`), and the protocol
    constants are in `oracle/trainer/lean_pubproto_eval.py:16-17`; ARM-A and ARM-B never appear. Expected in
    `RESULTS.md` section 1 or `STATEMENT.md` section 6.
22. What does "the session whose anchored rows the ZeeBeam release proves" (`README.md:15`) mean by "anchored"?
23. What are "the ZeeBeam release", "the eight-seed AUROC", "the five-offset aggregate", "the original published
    checkpoint", "the published coupling packet" and "the sealed 288-row verification take" (`CLAIM_BOUNDARY.md:19,43-46`;
    `REDACTION.md:74-75`)? All are external referents with no definition. Expected in `CLAIM_BOUNDARY.md`.
24. What is "the Lambda cache" from which four training-row hints were pulled (`README_FINAL.md:272-273`)?

"Held out"

25. The 28 August rows the trainer's quick screen consulted (`RESULTS.md:37-41`): which rows, and did that screen affect
    any decision (step count, seed, architecture)? `RESULTS.md:47-50` says selection used d2/v10 numbers; the screen's
    role is not stated. Expected in `CLAIM_BOUNDARY.md`.
26. Would the proved `R` values differ under a scale map calibrated without the seven August rows? `VERIFY.md:274-279`
    shows the map differs (`{…9: 21, 10: 17, 11: 95, 12: 41…}` against the frozen `{…9: 22, 10: 26, 11: 89, 12: 38…}`)
    but not the effect on residuals or signs. Expected in `CLAIM_BOUNDARY.md`.

Results tables

27. Are the numbers good? There is no null or baseline: no random-network or shuffled-hint distribution of `D`, no
    confidence interval on the 112 August margins, and no comparison with the "original published checkpoint". AUROC 1.0
    and paired 1.0 on 1,200 and 500 rows are perfect separations, but the reader must supply the chance level. Expected
    in `RESULTS.md` sections 1 and 3.
28. Why are the August margins about half the d2/v10 margins (`RESULTS.md:116-122`)? Reported, not explained.
29. Why `D_q > 3η` as the acceptance rule (`RESULTS.md:82`; `AUDIT_TRAIL.md:46-47`)? Stated as the rule, not motivated.
30. What does "the bf16 rounding-point fidelity of the A100 run is unresolved at the 1.1e-3 level" (`RESULTS.md:87-88`)
    imply for the claims? Expected in `RESULTS.md` section 3.
31. By what criterion was `g0e_armc_b16_96x112_cd0_aug_s20260908_24k` chosen over ladder variants with larger margins,
    for example `g0f_armc_b16_96x112_cd0_aug_s20260907_96k` (d2 delta 3.328e-02 against 2.241e-02, `RESULTS.md:62,68`)?
    "The selection … was made on these d2/v10 numbers" (`RESULTS.md:48-49`) does not say which number. Expected in
    `RESULTS.md` section 2.
32. What is the unit and meaning of the "prove (min)" column being 61 to 67 min against the pilot's 45.89 min? The
    contention explanation is labelled "an interpretation … not a measured cause" (`RESULTS.md:321`), which is honest,
    but the reader cannot resolve it.

The wrong-row offset rule

33. Why these five offsets, why cycle them by `(r - 600) mod 5`, and why mirror at the boundary rather than skip? The
    rule is given verbatim (`STATEMENT.md:167`; `rule.rs:36`) as "the owner's two-part … rule … relayed by the coordinator"
    (`rule.rs:1`) with no rationale. Expected in `STATEMENT.md` section 7.
34. Who are "the owner", "the principal", "the coordinator" and "the operator" (`rule.rs:1`; `README_FINAL.md:215,265`;
    `REDACTION.md:13`; `AUDIT_TRAIL.md:14`), and are they the same person? Expected in `README.md` Provenance.
35. The mirrored cases themselves are fully specified (`STATEMENT.md:165-176`; `rule.rs:95-106`). Open: for the four
    "policy-only" rows 698, 703, 708, 711 the mirrored offset coincides with a protocol offset, so a relabelled statement is
    relation-valid and refused only by the acceptance verifier (`STATEMENT.md:174-176`). Does a verifier who uses only the
    standalone route (VERIFY section 1) have any defence against such a relabelling? Expected in `VERIFY.md` section 1.

The noise

36. Who generated the 112 normative noise files and could the prover have chosen them? They follow a stated rule
    (`randn_cuda_emul(seed=20260823, call_index=r-600)`, `STATEMENT.md:180-186`; `oracle/common.py:226`), but `VERIFY.md`
    gives no command to regenerate them and compare BLAKE3s with `PINS.json` `noise_files`, so the reader cannot confirm
    that the bytes follow the rule. Expected in `VERIFY.md` section 4.
37. Why does the August stream restart at call index 0 rather than continue a session stream, and why was the noise
    made a witness rather than derived in circuit? The second is answered ("its correspondence to a CUDA generator is
    approximate", `STATEMENT.md:186-187`; `README_FINAL.md:204-213`); the first is a "coordinator 2026-09-07" decision
    with no reason (`README_FINAL.md:215`).

The calibration disclosure

38. The disclosure itself is clear (`CLAIM_BOUNDARY.md:23-32`). Open: what "own/+15 hints" contributed for row 696, whose
    +15 partner is 711, and whether any of the fourteen conditioning identities is also a wrong row in the proof set
    (711 is, as row 709's wrong row is 679 and row 711's is 709; 615, 631, 647, 663, 679, 695 are wrong rows of 617, 633,
    649, 665, 681, 697 by the rule). Expected in `CLAIM_BOUNDARY.md`.

The integer contract

39. Why integer arithmetic for the network at all, when the frame reduction is executed in software floating point
    inside the same guest (`STATEMENT.md:136-137`)? Cost is implied by the instruction counts (`RESULTS.md:149-153`) but
    the design reason is not stated. Expected in `STATEMENT.md` section 6.
40. Why int16 rather than int8: answered as "int8 … stays the cost option, int16 the fidelity baseline"
    (`README_FINAL.md:334-336`; ratios 79.8 against 19.2 at `RESULTS.md:92-94`). Open: why the fidelity baseline was
    chosen for proving when both pass the rule. Expected in `RESULTS.md` section 3.
41. What is the byte layout of the constants blob `ARMCINT1 v2` (`adapter/src/lib.rs:36,53`)? Only in `source/armc-int/src/`.
    Expected in `STATEMENT.md` section 6.

The audits

42. What did the audits find? The verdict lines are verbatim (`AUDIT_TRAIL.md:20-27`) and the dispositions are
    summarised, but findings are cited by number throughout ("Astra round 6, finding 15", `STATEMENT.md:221`;
    "findings 6, 7, 8", `VERIFY.md:355`; "finding 13", `LARGE_FILES.md:46`) and only round 5's twelve have one-line
    names (`FULL_GUEST.md:576-589`). The verdict files "stay on-box" (`AUDIT_TRAIL.md:13-14`). Expected in `AUDIT_TRAIL.md`.
43. Was the package re-audited after the round-6 verdict "REVISE: exclude on-box incident material … before
    publication" (`AUDIT_TRAIL.md:27`)? `AUDIT_TRAIL.md:116-118` says any later re-read "is a matter of the Dark
    Lantern repository's publication history", so the shipped bytes were not audited by the second model.
44. What is "GPT-6 Astra through `codex exec`" and what did it see (it reviewed additional unpublished context, `AUDIT_TRAIL.md:14`)? Expected in `AUDIT_TRAIL.md`.

The patent and licence

45. What licensing information accompanies the 6 September 2026 filing notice? `README.md:90-91` says only
    "the subject of an Irish patent application filed on 6 September 2026; it is an application, not a grant, and
    publication of these proofs grants no licence under it." Expected in `README.md` Provenance.
46. What are the licence terms? `README.md:91-93` cites "the repository's `LICENSE` (Dark Lantern Research and Private
    Use Licence 1.2)"; there is no `LICENSE` file in the package.

BOSUN and the roles

47. Who or what is BOSUN? `README.md:84-85`: "BOSUN, the project's automated research assistant"; every document is
    authored "BOSUN for Cathal Ryan Hynes"; `REDACTION.md:12` says the alias rule replaced "the assistant's box identity
    `BOSUN`". What system it is, how it was supervised, and what "for" means in the authorship line are not stated.
    Expected in `README.md` Provenance.
48. What is "the Dark Lantern repository" / "the Dark Lantern record's convention" (`AUDIT_TRAIL.md:14,117`;
    `LARGE_FILES.md:23`)? Expected in `README.md`.
49. Where is the data layer? `LARGE_FILES.md:10-11` names "bucket `truthbeam`, prefix `results/zkdiff_august_20260907/v1/`,
    transmit item 033" and `VERIFY.md:44-45` a sub-prefix, with no host, URL or access method. Expected in `LARGE_FILES.md`.
50. Why do all 112 receipts say `"sp1_version": "v6.1.0"` when the package says SP1 6.4.0 everywhere (`PINS.json:10-11`)?
    `verify.rs:51,137` shows the field is the artifact's circuit-version string, but no document says so. Expected in
    `receipts/README.md`.

---

## 4. Obstacles, ranked by severity

Severity 1 (blocks a check the brief asks for)

1. **The proved computation's inputs are held.** Raw frames are "never published" and the August `C_int`/`Ct_int`
   tensors, cached rows, vector sets and export sets are "held pending the principal's separate clearance"
   (`REDACTION.md:71-94`). Consequently no proved row's residual sums can be recomputed and no proof can be re-made
   (section 2 (d), (e)); the `oracle.*` acceptance checks compare against the prover's own table. The package says this
   clearly, but an agent asked to "check every proof" ends at the Groth16 and identity layers.
2. **The toolchain is external and unsourced.** Both verification routes need a Rust toolchain and 209 (standalone) or
   more (full) crates fetched over the network; the full route additionally needs `sp1up`, `cargo-prove`, the succinct
   toolchain, `protoc` and its includes. The only step still marked **[confirm]** is exactly this fetch
   (`VERIFY.md:26-27,111-113`). Hashes of `cargo-prove` and the tarball are pinned (`PINS.json:793-797`) but no download
   location is given anywhere.
3. **The data-layer location is not in the package.** 2,500 files (331,123,075 bytes) that `VERIFY.md` sections 6 and 7
   depend on are named by bucket and prefix only (`LARGE_FILES.md:10-11`); none is present here and no host is named.

Severity 2 (misleads or stalls a careful reader)

4. **"Two verified beacons" are usually one.** Rows `r-1` and `r` share a drand round in 646 of 711 consecutive pairs
   (66 distinct rounds in 712 rows); row 600's statement carries 31521690 twice. Nothing in `STATEMENT.md`, `VERIFY.md`
   or `README.md` mentions this, nor the `drand_staleness_ms` column (5.7 to 7.8 s). An agent reading "verifies the drand
   quicknet BLS signatures of rows r and r-1" (`STATEMENT.md:24-25`) will form the wrong picture of what the beacon leg
   binds.
5. **Undefined vocabulary at load-bearing points**: ARM-C, d2, v10, TB-v0.9, emission pattern, Truth Beam, ZeeBeam,
   anchored, `MAINNET_BLOCKING_TRAINING_300S`, authority manifest, vk root, the `meta` fields, owner/principal/coordinator/
   operator, Dark Lantern, G0 to G3 (defined only at `AUDIT_TRAIL.md:31-34`). There is no glossary.
6. **Shipped engineering records contradict the frozen documents in places and are not marked as superseded at the
   contradicting line**:
   - `source/armc-relation/RELATION.md:114-115`: the constants blob is "3,411,318 bytes"; `STATEMENT.md:99`,
     `FULL_GUEST.md:38,385` and the file on disk say 3,476,866 (blob v2 with masks).
   - `RELATION.md:99`: "Private witness (nine `read_vec` items …)" while the table lists ten and `STATEMENT.md:84` says ten.
   - `RELATION.md:395`: `zkdiff-ceremony verify --proof … --elf …` while `FULL_GUEST.md:129` says `verify` "REQUIRES `--expect`".
   - `oracle/final/README_FINAL.md:1-6`: frontmatter "version: 2.0 … Rust parity open" while its Log runs to 2.4
     (lines 404-419), `STATEMENT.md:220` cites "README_FINAL.md v2.4", and Rust parity is recorded as passed in `FULL_GUEST.md`.
   - `README_FINAL.md:371-373`: August margins are "of the same relative size (about 2.3x the correct residual)" as the
     protocol rows'; `RESULTS.md:118-122` (corrected in audit round 6) says the wrong residual is 2.3x and the margin 1.3x
     the correct one on August rows against 3.0x and 2.0x on protocol rows. The two files disagree.
   - `README_FINAL.md:371`: wrong residuals "near 0.015..0.018"; `RESULTS.md:117`: "0.013980 to 0.019355 (median 0.016228)".
   - `FULL_GUEST.md:41,340`: row 684's complete run "[pending node]" while `receipts/row_000684_receipt.json` shows it
     proved and accepted; the reader must know that `RESULTS.md` and `receipts/` supersede every "[pending node]" tag.
7. **`"sp1_version": "v6.1.0"` in all 112 receipts** against "SP1 6.4.0" in every document. The field is the SDK's
   circuit-version string (`verify.rs:51`), but only the source says so.
8. **Three different path bases.** `PINS.json` `noise_files[*].file` is `noise_august/…` (relative to `source/`),
   `PINS.json:20` `constants_blob` is `source/blobs/…` (package-relative), `source/expected_identities_august.json:11`
   `constants_blob` is `blobs/…` (relative to the private `g2_guest`); receipts, manifests and the expected-identities
   `sources` block carry absolute private paths (`[private development path]`, `[private development path]`,
   `[private corpus path]`) that resolve nowhere.
9. **`LICENSE` is referenced (`README.md:91-92`) and absent.**
10. **Terminology drift**: `offset_rule` is `"standard"` in `oracle/final/august_inputs/manifest.json:1105` and `"direct"`
    everywhere else; the manifest's rule text "if r+offset >= 712 use -offset" (line 14) omits the `< 0` case that
    `rule.rs:7-8` and `check_offset_rule` handle; "outcome" (receipts) against "class" (`RESULTS.md`); "framed artifact",
    "bincode artifact", "the SP1 artifact" against "raw proof", "proof bytes", "`SP1ProofWithPublicValues::bytes()`".
11. **Audit findings cited by number without text** (round 6 findings 2, 4, 6, 7, 8, 13, 14, 15; rounds 1 to 4 only by
    disposition), and no re-audit of the shipped bytes after the round-6 REVISE (`AUDIT_TRAIL.md:27,116-118`).
12. **The vendored verifier describes another statement.** `tools/standalone_verifier/src/main.rs:6-7` says the public
    values are "1,085 bytes for ceremony 1, 1,101 for the final relation" and the tamper control flips byte 87 (line 29)
    with no explanation; `VERIFY.md:55` does say it "knows nothing about the statement's layout", but the reader meets the
    contradiction first in the tool.

Severity 3 (friction)

13. `STATEMENT.md` elides derivations ("H(ROW, ..., S_{r+1}, emission_r)", "recomputed", "wrapped"), so the exact
    statement can only be reconstructed from Rust.
14. No command regenerates the normative noise from its rule and compares the 112 BLAKE3s, although `oracle/common.py`
    carries `randn_cuda_emul` and `philox_self_test`.
15. `VERIFY.md:35-37`: the ledger count check must be run before the large files are placed; an agent placing them first
    gets a spurious failure.
16. `fill_results.py`, `tools_release/stage_package.py`, `make_pins.py`, `evidence_allowlist.py` are named as the
    generators of `RESULTS.md` section 6, `REDACTION.md`, `LARGE_FILES.md`, `PINS.json` and `receipts/` but are not in the package.
17. `RESULTS.md` section 5 quotes the timing pilot from a report that is "on-box" (`RESULTS.md:179,329`).

---

## 5. Three things the package does well

1. **Everything is pinned and the pins agree with the bytes.** `SHA256SUMS` lists 2,703 files, all present and none
   extra; sizes on disk match every stated size (framed proofs 2,444 to 2,447 bytes in the stated 1/12/59/40 split, raw
   proofs 356, statements 752, noise files 86,016, blob 3,476,866, checkpoint 13,678,347, expected identities 119,375,
   chain log 367,429); the same identities recur unchanged in `PINS.json`, `expected_identities_august.json`,
   `build_reproducible.sh:15-18`, the node build record, the launch identity files and every receipt.
2. **Acceptance is layered, named and fail-closed.** `zkdiff-verify` "never derives a key from an ELF it is handed"
   (`STATEMENT.md:204`), every check is recorded PASS/FAIL/SKIP with a detail string (`accept.rs:112-165`), the owner rule
   is one pure function shared by driver, verifier and a 112-row regression test (`rule.rs`), negative controls are split
   into relation and policy layers with the error text recorded, and the receipts carry the exact command, binary hash,
   build record and expected-identities hash of the run.
3. **The claim is scoped honestly and the process is on record.** `CLAIM_BOUNDARY.md` governs every sentence, the
   calibration disclosure is explicit ("must not be described as an untouched test set"), the "[confirm]", "[measured]",
   "[derived]", "[extrapolation]" and "[pending node]" tags are used consistently, the batch's operational context labels
   its own interpretation as unmeasured, the rehearsal table names the one unrehearsed step, and every document ends
   with a versioned Log.

---

## 6. Verdict

**YES WITH EFFORT** for checking the proofs, **NO** for recomputing what they prove: given a network-fetched Rust/SP1
toolchain, the two rehearsed routes let an agent verify all 112 Groth16 proofs under the pinned key and every frozen
identity, but the residual sums can only be compared with the prover's own oracle table because the frames and August
tensors are held, and the session, the emission, ARM-C, d2/v10, the roles and the fact that rows r-1 and r usually share
one drand round must be inferred from source. **Single most important fix:** add a one-page primer to `README.md` that
defines, in plain words, the recording (what was projected and captured, what a row is), the emission pattern, ARM-C and
the frozen protocol, d2 and v10, the four roles, every published hash including the authority manifest and vk root, and
states outright that most consecutive rows share a beacon round, so that the statement can be read without opening the
Rust.
