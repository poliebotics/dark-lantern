> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

# 1. What I understood the package claims

1. The package claims to contain one Groth16 proof for each of the 112 August session rows 600–711. (`README.md` line 11)
2. Each proof claims that the pinned integer diffusion evaluator processed the complete raw Bayer frame, derived the correct and owner-selected wrong conditionings, and publicly committed their residual sums and binding digests. (`README.md` line 14, `STATEMENT.md` line 18)
3. The package reports that all 112 rows had lower residual under the correct conditioning, with no ties, reversals, or nonzero clipping counts. (`README.md` line 11, `RESULTS.md` line 103)
4. The wrong row is selected by a five-offset rule anchored at row 600, with ten listed cases mirrored when the direct offset would leave the session. (`STATEMENT.md` line 163)
5. These are execution-binding claims, not proof of physical capture, liveness, realness, or untouched test-set generalization, and seven proof-target rows influenced integer calibration. (`CLAIM_BOUNDARY.md` line 15, `CLAIM_BOUNDARY.md` line 21)

Scope note: I performed read-only inspection and checksum checks only; I did not build software, execute the evaluator, or verify or generate proofs. The root `SHA256SUMS` ledger passes and covers all 2,703 other files.

# 2. The verification path

Set:

```bash
P=/path/to/zkdiff_august_20260907
```

First, check the publication ledger:

```bash
(cd "$P" &&
 sha256sum -c --quiet SHA256SUMS &&
 [ "$(grep -c . SHA256SUMS)" = "$(find . -type f ! -name SHA256SUMS | wc -l)" ] &&
 echo LEDGER_OK)
```

This is complete and passed. It is the authority for the redacted publication tree. (`VERIFY.md` line 29, `REDACTION.md` line 10)

## (a) Verify one proof

The package’s lightweight route is:

```bash
(cd "$P/tools/standalone_verifier" && cargo build --release --locked)

"$P/tools/standalone_verifier/target/release/zeebeam-standalone-verifier" \
  "$P/proofs/row_000600_groth16_proof.bin" \
  "$P/public_values/row_000600_public_values.bin" \
  0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027
```

Expected final output is `VERIFIED`, with its tampered-public-value and wrong-key controls rejected. (`VERIFY.md` line 47)

Package completeness: **No.** The proof, public values, verifier source, lockfile, and key are present, but the 209 locked Rust packages, compiled verifier, and Rust toolchain are not. The package explicitly requires either network access or an already populated Cargo cache. (`VERIFY.md` line 65, `tools/standalone_verifier/VENDORED.md` line 3)

That route verifies only the Groth16 equation under the supplied program key. To check the claimed field meanings and identities, the full verifier must also be built and run:

```bash
S="$P/source/armc-relation/script/target/release"

"$S/zkdiff-verify" --identity

"$S/zkdiff-verify" \
  --proof "$P/proofs/row_000600_groth16.bin" \
  --expect "$P/source/expected_identities_august.json" \
  --report /tmp/row_000600.verify.json
```

Package completeness: **No.** The source and expected identities are present, but the SP1/Rust toolchains, dependency cache, `protoc`, and embedded circuit material needed to build the executable are not. (`VERIFY.md` line 81)

## (b) Verify all 112

After building either verifier, first assert the count:

```bash
test "$(find "$P/proofs" -maxdepth 1 -name 'row_*_groth16.bin' | wc -l)" -eq 112
```

Then run the full acceptance verifier:

```bash
S="$P/source/armc-relation/script/target/release"

for p in "$P"/proofs/row_*_groth16.bin; do
  "$S/zkdiff-verify" \
    --proof "$p" \
    --expect "$P/source/expected_identities_august.json" \
    >/dev/null ||
    { echo "REFUSED $p"; exit 1; }
done

echo "every proof accepted"
```

This is the package’s documented loop. (`VERIFY.md` line 141)

Package completeness: **No**, for the same missing build dependencies. Also, the documented loop prints “every proof accepted” without itself asserting that exactly 112 files matched; the separate count above is necessary.

## (c) Rebuild the program and compare its identity

Required dependency fetches:

```bash
(cd "$P/source/armc-relation/script" &&
 CARGO_NET_OFFLINE=false cargo fetch --locked)

(cd "$P/source/armc-relation/program" &&
 CARGO_NET_OFFLINE=false cargo +succinct fetch --locked \
   --target riscv64im-succinct-zkvm-elf)
```

Build and pin check:

```bash
(cd "$P/source/armc-relation" && ./build_reproducible.sh)

"$P/source/armc-relation/script/target/release/zkdiff-verify" --identity
```

The build must end with `BUILD_REPRODUCED_OK` and assert:

```text
ELF SHA-256:
51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc

SP1 vkey:
0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027
```

(`VERIFY.md` line 103, `VERIFY.md` line 115)

Package completeness: **No.** Rust 1.98, the succinct toolchain, SP1 6.4.0, locked crates, `protoc`, and other system tools must be obtained separately. The package states that the empty-cache network fetch was not rehearsed. (`VERIFY.md` line 109, `VERIFY.md` line 322)

The node runbook’s alternative `build` command is not valid on the publication tree: it checks `source/SHA256SUMS_G2D`, whose entries describe private/pre-redaction bytes and missing run artifacts. The redaction notice itself says those digests “do not validate the substituted files.” (`source/node_prep/G2D_NODE_RUNBOOK.sh` line 32, `REDACTION.md` line 10)

## (d) Reproduce row 600’s residual sums

After the build, the native execution command is:

```bash
S="$P/source/armc-relation/script"
FRAMES=/path/containing/the-August-raw-frames
OUT=/tmp/zkdiff_execute_600
BUILD_RECORD=$(ls -1t "$P"/source/armc-relation/runs/build_record_*.txt | head -1)

"$S/target/release/zkdiff-batch" execute \
  --chain-log "$P/source/vectors_relation/august/chain_log.csv" \
  --rows 600..600 \
  --frames-dir "$FRAMES" \
  --noise-dir "$P/source/noise_august" \
  --blob "$P/source/blobs/final_int16/constants_int16.blob" \
  --expect "$P/source/expected_identities_august.json" \
  --build-record "$BUILD_RECORD" \
  --out "$OUT"
```

The expected results are `R_correct=4435539299` and `R_wrong=11254163581`. (`source/node_prep/G2D_NODE_RUNBOOK.sh` line 54, `RESULTS.md` line 200)

Package completeness: **No.** The required 24,472,000-byte raw frame is deliberately absent. (`STATEMENT.md` line 82, `REDACTION.md` line 69)

The nominal independent Python calculation is:

```bash
(cd "$P/source" && python3 -B tools/python_oracle_rows.py 600)
```

That also cannot run: its required August input NPZ and data-layer vectors are absent, and it looks for a checkpoint under `oracle/ckpt/final`, while the published checkpoint is under `model/`. (`source/tools/python_oracle_rows.py` line 2, `source/tools/python_oracle_rows.py` line 18, `LARGE_FILES.md` line 26)

## (e) Reproduce a proof

After rebuilding, supplying the missing frame, and installing the GPU prover stack:

```bash
S="$P/source/armc-relation/script"
FRAMES=/path/containing/the-August-raw-frames
OUT=/tmp/zkdiff_prove_600
BUILD_RECORD=$(ls -1t "$P"/source/armc-relation/runs/build_record_*.txt | head -1)

"$S/target/release/zkdiff-batch" prove \
  --prover cuda \
  --device 0 \
  --cycle-limit 200000000000 \
  --chain-log "$P/source/vectors_relation/august/chain_log.csv" \
  --rows 600..600 \
  --frames-dir "$FRAMES" \
  --noise-dir "$P/source/noise_august" \
  --blob "$P/source/blobs/final_int16/constants_int16.blob" \
  --expect "$P/source/expected_identities_august.json" \
  --build-record "$BUILD_RECORD" \
  --out "$OUT"
```

This follows the published node runbook. (`source/node_prep/G2D_NODE_RUNBOOK.sh` line 71)

Package completeness: **No.** Missing items include the row’s raw frame, SP1/CUDA prover installation, Go toolchain, Groth16 circuit proving material, compatible GPU/node environment, and dependency caches. Some missing proving artifacts have hashes in `PINS.json`, but not their bytes. (`PINS.json` line 885)

The source fixes the proof nonce to zero, but I found no statement establishing that rerunning the prover must reproduce the exact published proof bytes rather than merely another valid proof. (`source/armc-relation/script/src/ceremony_core.rs` line 292)

# 3. Questions the package alone could not answer

Several requested concepts are defined well enough internally:

- “Held out” means excluded from weight updates, not untouched: 28 August rows were consulted during quick screening, and seven target rows influenced calibration. (`RESULTS.md` line 34)
- The wrong-row formula and all ten mirrors are explicit. (`STATEMENT.md` line 163)
- The normative noise is 86,016 exported int16 Q12 values; the bytes are private witness input while their digest is public. (`STATEMENT.md` line 178)
- The integer contract specifies rounding, saturation, tensor formats, and clipping; int16 is presented as the fidelity baseline, while int8 is a potential cost option with larger numerical errors. (`oracle/final/README_FINAL.md` line 84, `RESULTS.md` line 90)
- In the result tables, positive `D = R_wrong − R_correct` means the correct conditioning has the lower squared residual; “good” is only established against the package’s internal acceptance condition, not as physical-world validity or generalization. (`STATEMENT.md` line 206, `RESULTS.md` line 77)

The remaining unanswered questions are:

1. What exactly do the dataset names `d2` and `v10` mean, who captured or published them, and what are their licenses and complete train/evaluation splits? Expected in `README.md`, `RESULTS.md`, or a dataset README; the package says only that they are “public Truth Beam sessions.” (`REDACTION.md` line 77)

2. What physical capture setup produced the August session, who controlled it, and what independently ties the committed raw bytes to the claimed projector-camera session on 22 August? Expected in the authority manifest or an August dataset README; both the raw frames and authority-manifest contents are absent.

3. What does “ARM-C” expand to, which exact protocol/version was adapted, and what changed in this implementation? Expected in `README.md` or `source/armc-relation/RELATION.md`.

4. What semantic specifications correspond to `abi_version=1`, `protocol_version=9`, and `TB-v0.9`? Their numeric values and byte positions are given, but no versioned specification or registry is included. (`STATEMENT.md` line 51)

5. What are the plain-language trust roles of `session_id`, `S0`, `SN`, `authority_manifest_sha256`, `chain_log_blake3`, `context`, `wrapped_root`, raw and emission leaves, and endpoint digests? The layout and comparison rules are present, but the underlying authority model and some terminology are not. Expected in `STATEMENT.md` or a glossary. (`STATEMENT.md` line 61)

6. What exact file and contents have the published `authority_manifest_sha256`? Only its digest is available, so the claimed authority assertions cannot be inspected. Expected beside `source/vectors_relation/august/chain_log.csv` or in `receipts/`.

7. How can an offline reader authenticate the drand/Quicknet rounds? The package calls this an “out-of-band check” and supplies no schedule authority or independently verifiable source. (`VERIFY.md` line 197)

8. For every hash in `PINS.json`, what is the algorithm, canonical serialization, and package-relative target? Most keys identify these, but the three `model.pubproto_raw` values are unlabeled bare hex values, and the noise paths omit the actual `source/` prefix. (`PINS.json` line 80, `PINS.json` line 914)

9. Who is the “owner” or coordinator who selected the wrong-row rule, why were these five offsets chosen, and why is row 600 the modulo anchor? The arithmetic is exact, but the selection rationale and authority are absent. Expected in `STATEMENT.md` or the calibration record.

10. Why was seed `20260823` and the stated Philox/Box–Muller mapping chosen, when was it fixed, and why are the noise values private witness data rather than public input? Expected in the noise-generation provenance. (`STATEMENT.md` line 178)

11. Why were those seven August calibration rows and the own/+15 pair selected, and what quantitative effect did consulting them have on the reported 112-row result? The disclosure states what happened but does not evaluate the resulting selection bias. (`CLAIM_BOUNDARY.md` line 21)

12. Why was the acceptance rule `Dq > 3η` chosen, was it fixed before examining the target results, and how were percentiles, intervals, ties, and uncertainty calculated? Expected in `RESULTS.md` or a statistical-methods note.

13. Why was int16 ultimately proved instead of int8? Fidelity comparisons are supplied, but no measured proof-cost comparison for int8 is provided despite calling it a “cost option.” (`RESULTS.md` line 90)

14. What were the Astra auditors’ complete prompts, evidence, findings, and reasoning? Only short verdict lines and author-written change summaries are published; the “full verdict texts remain on-box.” (`AUDIT_TRAIL.md` line 10)

15. Was the final r6-revised package audited again? The last published verdict remains `REVISE`, so I cannot tell whether an auditor approved the exact final bytes. (`AUDIT_TRAIL.md` line 96)

16. What does “independently verified” mean here, and by whom? The provenance describes the proving node, development machine, project assistant, and model reviews, but not an independent organization or verifier. Expected in `README.md:89`.

17. What licensing information accompanies the 6 September 2026 filing notice? The package says only that an Irish patent application was filed on 6 September. (`README.md` line 92)

18. What are the exact license terms? `README.md` points to `LICENSE`, but that file is absent, leaving the named “Dark Lantern Research and Private Use Licence 1.2” unavailable for inspection. (`README.md` line 92)

19. Who or what is BOSUN beyond “the project’s automated research assistant”: model/version, operator, authority, degree of autonomy, and which text, code, checks, or signatures it produced? Expected in `README.md` or `AUDIT_TRAIL.md`. (`README.md` line 84)

20. Does the zero nonce make proving byte-deterministic across machines and runs, or is proof reproduction intended to mean only producing another accepted proof? Expected in the proving runbook or ceremony documentation.

21. What exactly is in the withheld raw frames, witness directories, oracle arrays, incident logs, and full audit records? Their hashes sometimes identify particular absent bytes, but hashes do not let a reader inspect or reproduce them. (`receipts/README.md` line 67, `LARGE_FILES.md` line 10)

# 4. Obstacles ranked by severity

| Rank | Severity | Obstacle and consequence |
|---:|---|---|
| 1 | Critical | The indispensable August raw frames are absent. This prevents native residual reproduction and proof generation, even though `README.md` calls the frame part of the witness. |
| 2 | Critical | Neither verifier is offline-runnable from package bytes: the “vendored” standalone verifier contains source and a lockfile, not the 209 dependencies or an executable. This contradicts the practical implication of “No external clone is needed.” (`VERIFY.md` line 47) |
| 3 | Critical | Proving additionally assumes SP1, CUDA, Go, circuit proving material, compatible hardware, and caches not in the package; some are represented only by hashes. |
| 4 | High | The advertised independent residual script cannot run against the public layout: required arrays are held back, and its checkpoint path does not resolve. |
| 5 | High | The node runbook checks `SHA256SUMS_G2D`, but that ledger describes private/pre-substitution bytes and missing run files; its `build` path therefore does not validate this publication tree. |
| 6 | High | Provenance checks ultimately lead outside the package: external ZeeBeam material, Quicknet/drand authenticity, authority-manifest contents, and dataset origins cannot be checked offline. |
| 7 | High | The missing `LICENSE`, unexplained licensing scope, abbreviated audit material, and undefined BOSUN identity prevent evaluation of legal status and claimed review independence. |
| 8 | Medium | Important glossary terms are unexplained: ARM-C, d2, v10, TB-v0.9, G1/G2-D, ZeeBeam/Truth Beam, owner/coordinator, and several session-binding fields. |
| 9 | Medium | Several paths and descriptions are inconsistent: `PINS.json` noise paths omit `source/`; actual launch scripts contain private absolute paths; and the standalone verifier comments describe 1,101-byte final public values while this statement is 752 bytes. (`tools/standalone_verifier/src/main.rs` line 5, `STATEMENT.md` line 43) |
| 10 | Medium | Historical documents remain beside final records and contain stale conclusions such as “never proved” or “Rust parity remains unverified,” whereas later results say those steps succeeded. Status banners help, but an agent must reconstruct chronology. |
| 11 | Low | The all-proof verification loops do not independently assert a 112-file count before printing success. |
| 12 | Low | Ambiguous wording such as “independently verified,” “vendored,” and “everything needed to verify” overstates what is available under package-only, offline conditions. (`VERIFY.md` line 10) |

# 5. Three things the package does well

1. The root checksum ledger is complete, count-checked, and internally consistent, so the exact publication bytes can be identified reliably.
2. The statement layout, integer arithmetic, owner-offset mirrors, noise commitment, acceptance rule, and claim boundary are unusually explicit.
3. It includes both wrapped and raw proof artifacts, public values, receipts, negative-control descriptions, expected identities, and candid disclosures about calibration and withheld data.

# 6. Verdict

**NO — the single most important fix is to ship a self-contained offline row-600 reproduction capsule containing its raw frame, required oracle inputs, verifier/prover dependencies and circuit assets, with one package-root script that verifies, re-executes, and reproves it.**