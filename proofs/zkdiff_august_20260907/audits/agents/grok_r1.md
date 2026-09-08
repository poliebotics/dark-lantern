> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

# Agent audit of the zkdiff August publication package

This report is from reading the tree at `the package root` only. Nothing was modified, built, proved, or fetched. Hashes below are quoted from the package; they were not recomputed.

---

## 1. What I understood the package claims, in five plain sentences, and where each claim is stated (file and line)

1. **For each of the 112 August session rows 600–711, one SP1 6.4.0 Groth16 proof attests that a frozen integer diffusion denoiser, run twice on the same whole-frame noised input (own emission vs a declared wrong-row emission), produced the published residual sums `R_correct`, `R_wrong` and `D = R_wrong - R_correct`, with every binding digest and the clip count, and with no pixels in the 752-byte statement.**  
   *Stated:* `README.md` lines 8 and 14–24; restated as the governing claim in `CLAIM_BOUNDARY.md` lines 15–16: “Each proof establishes execution binding of an integer diffusion evaluator adapted from the frozen ARM-C protocol…”; technical layout in `STATEMENT.md` lines 16–41 and 208–214.

2. **All 112 proofs were verified and accepted under frozen identities; every signed outcome is positive, none is zero or negative, and no row has a nonzero clip count.**  
   *Stated:* `README.md` line 11: “112 proofs, one per row 600 to 711, every one verified and accepted under the frozen identities: 112 positive, 0 zero and 0 negative signed outcomes; 0 rows with a nonzero clip count.” Same sentence in `RESULTS.md` lines 189–190 and 315.

3. **The proofs establish only that specified integer computation on committed bytes; they establish nothing about cameras, scenes, realness, liveness, illumination causality, adversarial resistance, or another session, and they do not reproduce an eight-seed result, a five-offset aggregate, or a full diffusion trajectory.**  
   *Stated:* `CLAIM_BOUNDARY.md` lines 18–19 (verbatim, governing every other file per lines 10–13); short form in `README.md` lines 63–68 and `VERIFY.md` lines 312–319.

4. **August rows 600–711 were held out from weight training; seven of those rows (and fourteen August conditioning identities) entered quantisation calibration, so they are not an untouched test set; the d2/v10 evaluation blocks are development validation because they were used to pick the proof model.**  
   *Stated:* `CLAIM_BOUNDARY.md` lines 17 and 21–32; `RESULTS.md` lines 12–14 and 47–50; trainer numbers in `RESULTS.md` lines 34–41.

5. **A verifier need not trust the prover: the program verifying key is a pin, the circuit key is embedded in `sp1-verifier` 6.4.0, the guest ELF can be rebuilt from published source and asserted against that pin, and each statement is accepted only if it matches `source/expected_identities_august.json`.**  
   *Stated:* `VERIFY.md` lines 10–16 and 81–86; pin values in `README.md` lines 50–52 and `PINS.json` lines 5–12; acceptance layers in `STATEMENT.md` lines 192–204.

---

## 2. The verification path

Every command below is copied from the package. `VERIFY.md` lines 18–20 require setting `P` to the package root and never `cd`-ing between steps. The text names `P=/absolute/path/to/zkdiff_august_20260907` (`VERIFY.md` line 23); this tree is not named that.

### (a) Verify one proof

**Ledger first** (`VERIFY.md` lines 29–41):

```
(cd "$P" && sha256sum -c --quiet SHA256SUMS && [ "$(grep -c . SHA256SUMS)" = "$(find . -type f ! -name SHA256SUMS | wc -l)" ] && echo LEDGER_OK)
(cd "$P" && sha256sum -c --quiet LARGE_FILES_SHA256SUMS && echo LARGE_FILES_OK)
```

Package gives `SHA256SUMS` and `LARGE_FILES_SHA256SUMS`. The second ledger is for data-layer files that “are needed only for the oracle parity tests of section 6 and the regeneration of section 7, never for verifying a proof” (`VERIFY.md` lines 42–43). Those files are **not in this directory** (`LARGE_FILES.md` lines 10–16; no `source/oracle_final/` or `oracle/rows/` here).

**Standalone Groth16 check** (`VERIFY.md` lines 57–63):

```
(cd "$P/tools/standalone_verifier" && cargo build --release --locked)
"$P/tools/standalone_verifier/target/release/zeebeam-standalone-verifier" \
    "$P/proofs/row_000600_groth16_proof.bin" \
    "$P/public_values/row_000600_public_values.bin" \
    0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027
```

Present: raw 356-byte proof, 752-byte public values, vendored verifier sources and lockfile (`tools/standalone_verifier/`, `VENDORED.md`). Expected output: `tamper_public_byte_87_rejected=true`, `wrong_vkey_rejected=true`, `VERIFIED` (`VERIFY.md` lines 67–68).

Missing for an agent with this package alone and no network:

- A Rust toolchain (“rehearsed with 1.98.0”, `VERIFY.md` line 65). Not in the tree.
- The 209 locked crates. Only `Cargo.lock` is vendored. `VERIFY.md` lines 25–27 and 65–66: first build needs “either the network or a cargo home that already holds the 209 locked crates”; a fetch from an empty cargo home “was not rehearsed” and is tagged **[confirm]**.
- A prebuilt `zeebeam-standalone-verifier` binary. Not shipped.

**Full acceptance check** (`VERIFY.md` lines 104–129), after toolchain install and `./build_reproducible.sh`:

```
S="$P/source/armc-relation/script/target/release"
"$S/zkdiff-verify" --identity
"$S/zkdiff-verify" --proof "$P/proofs/row_000600_groth16.bin" --expect "$P/source/expected_identities_august.json" --report /tmp/row_000600.verify.json
```

Present: framed proof `proofs/row_000600_groth16.bin`, `source/expected_identities_august.json`, guest/host source, node receipt `receipts/row_000600_verify.json`.

Missing: SP1 6.4.0 (`sp1up --version v6.4.0`), succinct rustc, `protoc` and protobuf includes, GNU time, binutils (`VERIFY.md` lines 89–99); cargo registry contents (workspace is `offline = true`, `VERIFY.md` lines 103–110); rebuilt `zkdiff-verify` binary (build outputs “omitted”, `REDACTION.md` line 79).

This route **does** check statement identities; the standalone route “does not check the statement's identities … and it says nothing about which program the key belongs to” (`VERIFY.md` lines 78–79).

### (b) Verify all 112

Standalone (`VERIFY.md` lines 70–75):

```
for r in "$P"/proofs/row_*_groth16_proof.bin; do
  b=$(basename "$r" _groth16_proof.bin)
  "$P/tools/standalone_verifier/target/release/zeebeam-standalone-verifier" "$r" "$P/public_values/${b}_public_values.bin" \
      0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027 | grep -q '^VERIFIED$' || { echo "REJECTED $r"; exit 1; }
done && echo "standalone: 112 VERIFIED"
```

Full (`VERIFY.md` lines 143–146):

```
for p in "$P"/proofs/row_*_groth16.bin; do
  "$S/zkdiff-verify" --proof "$p" --expect "$P/source/expected_identities_august.json" > /dev/null || { echo "REFUSED $p"; exit 1; }
done && echo "every proof accepted"
```

Present: 112 framed proofs, 112 raw proofs, 112 public-value pairs, 112 receipts and node verify reports, 112 `independent_verify` reports.

Same toolchain/crate gap as (a). Negative controls: `"$S/zkdiff-verify" ... --controls` (`VERIFY.md` lines 154–158); record `receipts/proof_controls.json` is present.

### (c) Rebuild the program and compare its identity to the pinned one

```
(cd "$P/source/armc-relation/script" && CARGO_NET_OFFLINE=false cargo fetch --locked)
(cd "$P/source/armc-relation/program" && CARGO_NET_OFFLINE=false cargo +succinct fetch --locked --target riscv64im-succinct-zkvm-elf)
(cd "$P/source/armc-relation" && ./build_reproducible.sh)
```

(`VERIFY.md` lines 106–116.) Driver asserts ELF 396,200 bytes, SHA-256 `51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc`, vkey `0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027` (`VERIFY.md` lines 119–123; pins in `PINS.json` lines 7–9). Last line must be `BUILD_REPRODUCED_OK`.

Present: source under `source/armc-relation/` and `source/armc-int/`, lockfiles, `build_reproducible.sh`, rust-toolchain files, expected identities, constants blob.

Missing:

- Network for an empty cargo home (**[confirm]**, `VERIFY.md` lines 111–113, 346–347).
- SP1 6.4.0 and succinct target; compare `sha256sum ~/.sp1/bin/cargo-prove` to `PINS.json` `reproducible_build.guest_toolchain.cargo_prove_sha256` = `d8835f80…ff106` and tarball `12c94435…192f` (`PINS.json` lines 787–793). Those binaries are not in the package.
- Guest ELF is “not shipped” (`PINS.json` line 6).
- Frozen source-digest lists were “computed over the private bytes” (`PINS.json` line 775; `REDACTION.md` lines 14–18). Two comment-only substitutions change `ceremony.rs` and `ceremony_core.rs`; the package says the compiler ignores comments and the ELF pin is the check (`VERIFY.md` lines 216–217). An agent cannot validate those historical digest lists against the published files.

### (d) Reproduce one row's residual sums

The **numbers** for every row are in the package: `oracle/final/august_inputs/manifest.json` (e.g. row 600 int16 correct `4435539299`, `wrong_-2` `11254163581`, lines 1119–1128), copied into `source/expected_identities_august.json` lines 105–109, `RESULTS.md` line 202, and receipts. The acceptance verifier compares proved `R_correct`/`R_wrong` to that table (`STATEMENT.md` lines 201–203). That is a table lookup, not a recomputation.

To **recompute** a row, the package's own tools need the integer inputs `C_int`, `noise_int`, `Ct_int`, `E_correct`, `E_wrong` and the frozen scale map:

- `source/tools/python_oracle_rows.py` lines 88–90: `np.load(G1 / f"final/august_inputs/row_{r:06d}.npz")`. Those 112 npz files are **held** (`REDACTION.md` lines 81–83: `g1_integer/final/august_inputs`, 112 files, “August camera-derived tensors, held for clearance”). This tree has only `oracle/final/august_inputs/manifest.json` and `coord_int.npy`.
- Recalibrating from public rows is stated not to reproduce the frozen map: “a run on the public rows alone recalibrates on 8 rows and yields a different one” (`VERIFY.md` lines 274–279). Consumers “load, never recompute” the frozen constants (`VERIFY.md` lines 279–282).
- Re-deriving `C_int` from the raw Bayer frame needs the 24,472,000-byte frame. “Raw sensor frames are never published” (`REDACTION.md` line 71). Guest execute uses `FRAMES=${FRAMES:-"$P/frames/raw"}` (updated example) (`source/node_prep/G2D_NODE_RUNBOOK.sh` line 24), a path that is not in this package.
- Prepared witnesses under `source/armc-relation/runs/batch_prepare_r5_20260907/row_000600/witness/` have header, membership, noise, offset, previous, leaf, siblings, signature — **not** `raw_r`. Receipts withhold `witness/` (1,017 files, `receipts/README.md` lines 77–78).

A **d2** residual (row 1328: 8,764,459,045 / 22,311,372,969) can be aimed at via `oracle/final/vectors/vectors_int16_d2_1328_*.json` plus the data-layer `.npz` (`LARGE_FILES.md` line 32) or `source/blobs/final_int16/C_int_d2_row1328_*.i16`. Those data-layer arrays are not in this directory. August 650 has `E_int` and `noise_int` blobs but **no** `C_int` blob.

**Verdict for (d):** the package gives the expected sums and a checker that matches them; it does not give the August camera tensors or frames needed to reproduce them.

### (e) Reproduce a proof

The batch command actually used (`source/node_prep/r5/g2g_batch/launch_gpu.sh` lines 37–38):

```
./target/release/zkdiff-batch prove --prover cuda --device "$N" --cycle-limit $CYCLE_LIMIT \
  --chain-log "$CHAIN" --rows "$A..$B" --frames-dir "$FRAMES" --noise-dir "$NOISE" --blob "$BLOB" --expect "$EXPECT" --build-record "$BUILD_RECORD" --out "$out"
```

with `FRAMES="$P/frames/raw"` (updated example) (line 18). One-row form: `G2D_NODE_RUNBOOK.sh prove-one N R` (lines 71–80).

`VERIFY.md` line 348: “proving was not rehearsed and is not part of verification.”

Missing:

- Raw frames (held).
- NVIDIA A100, CUDA, `sp1-gpu-server` 6.4.0 (hash `f68b85dc…d97c` in `PINS.json` lines 886–888; binary not shipped).
- Groth16 proving key `groth16_pk.bin` (hash `c3760e0e…a167` in `PINS.json` line 896; file not shipped).
- Go, “needed only to prove, through the `groth16` feature” (`VERIFY.md` lines 100–101).
- CUDA-enabled `zkdiff-batch` (`CUDA=1` in the node build, `build_reproducible.sh` line 13).
- Per-row witnesses including `raw_r` (withheld).

Noise, chain log, blob, and expected identities **are** present. That is not enough to prove.

---

## 3. Every question I could not answer from the package alone

1. **What is the authority manifest whose SHA-256 is `740d752d…d783`?** Expected in `PINS.json` / `STATEMENT.md` (session table). The digest is pinned; the bytes are not here.

2. **What are `S_0` and `S_N` besides 32-byte hex pins?** They are “inputs to the context digest” (`STATEMENT.md` line 63). How the chain is initialised, and what “authority” means, is not defined in this package.

3. **What is the file hashed as the preprocessing / network spec, beyond the compiled JSON strings?** Digests are pinned (`PINS.json` lines 23–26). The JSON lives in `spec.rs` and `adapter/src/lib.rs`. Why those particular English phrases are the spec, and how they relate to a ZeeBeam original, is not here (the manuscript is cited, not shipped: `CLAIM_BOUNDARY.md` lines 50–52).

4. **What is Groth16 `vk root` `002f850ee998974d6cc00e50cd0814b098c05bfade466d28573240d057f25352` in `receipts/row_000600_receipt.json` line 13?** It is not a named pin in `PINS.json` `program`.

5. **What are `groth16_witness.json`, `Groth16Verifier.sol`, `SP1VerifierGroth16.sol`, `constraints.json`, `groth16_circuit.bin`, `groth16_pk.bin` as used on the proving node?** Hashes are in `PINS.json` lines 889–896, sourced from on-box `pilot/node_runs/pilot_600/{server_identity,circuit_identity}.txt`, which is not in the package.

6. **What is `cargo-prove` commit `f66b4bf` as a tarball an agent can fetch without the web?** Only a SHA-256 of `~/.sp1/bin/cargo-prove` and of a toolchain tarball (`PINS.json` lines 791–793).

7. **What is `driver_sha256_private` `911baa0c…3ac8` (`PINS.json` line 760)?** It is labelled private; the published driver may differ.

8. **How do I verify historical `SOURCE_DIGESTS_*.txt` against this tree?** They “were computed over the private bytes and therefore do not validate the substituted files” (`REDACTION.md` lines 14–16).

9. **What does each public-output field mean, in full?** `STATEMENT.md` section 2 names them. Still unanswered from the package alone: expansion of `TB-v0.9`; what “wrapped” means for the ordered-session root; why row 600’s `prev_drand_round` and `own_drand_round` are both `31521690` (`expected_identities_august.json` lines 101–102) while `STATEMENT.md` line 25 speaks of “two verified drand quicknet beacons”; semantic content of `meta` (28 bytes); how `terminal_committed` is set (`membership.rs` line 34).

10. **Where do datasets d2 and v10 come from?** Trainer table (`oracle/trainer/train_lean.py` lines 72–80): d2 has 5,992 rows under `truthbeam/sessions/d2`, v10 3,743 under `truthbeam/sessions/v10`, with named train/eval blocks. `REDACTION.md` line 77: “The d2 and v10 tensors derive from the public Truth Beam sessions.” What was recorded, when, with what camera/projector, and why those names, is not stated. The sessions themselves are not in this package.

11. **Where does the August session physically come from beyond “projector-camera session recorded on 22 August 2026”?** `README.md` line 14; session id `ZEEBEAM_MAINNET_BLOCKING_TRAINING_300S_20260822_001`; chain-log comment `# session_iso_utc=2026-08-22T03:09:45.544477+00:00`. Sensor model, lens, projector, site, and what “MAINNET_BLOCKING_TRAINING_300S” means are not given. Frames are held.

12. **What is `crop_id UNCROPPED_FULL_FRAME_20260825` (`oracle/final/README_FINAL.md` line 15)?** Named, not defined.

13. **What does “held out” mean here, exactly, for every use of the August rows?** Weight training: held out (`CLAIM_BOUNDARY.md` line 17; `august_train_rows 600`). Quantisation calibration: seven targets used (`CLAIM_BOUNDARY.md` lines 23–29). Trainer quick screen: “Those 28 August rows were consulted as a screen during training and not for weights” (`RESULTS.md` lines 39–41). Proof set: all 112. The package says they “must not be described as an untouched test set.” It does not say which 28 of 112 were the screen, or how that consultation could have affected training choices.

14. **Are the d2/v10 evaluation blocks in the training set?** `CLAIM_BOUNDARY.md` line 43: “the d2/v10 blocks, excluded from training but used repeatedly for candidate selection, are development validation.” Trainer train ranges in `train_lean.py` lines 75–79 sit beside those eval blocks. Whether any eval row leaked into the 8,035 training rows (`RESULTS.md` line 35: “d2 4,432, v10 3,003, August 600”) is not shown as an arithmetic check in the package.

15. **What do the results-table numbers mean, and are they “good”?** Meanings of paired, AUROC, delta, `D_q`, `η`, `D_q > 3η` are defined (`RESULTS.md` lines 24–27; `oracle/final/AGREEMENT.md` lines 6–7). Whether AUROC 1.0 / paired 1.0 is surprising, trivial, or overfit is not judged except by calling d2/v10 “development validation.” For August, the package reports all 112 signs positive and median `D` 0.009161 MSE (`RESULTS.md` line 315) and that August margins are smaller than protocol-row margins (`RESULTS.md` lines 117–122). It does not state a pass/fail threshold for August other than matching the oracle table and publishing the sign.

16. **How is 507 (row, offset) pairs obtained?** `RESULTS.md` line 104: “all five protocol offsets plus the mirrored -30 where the rule needs it, 507 (row, offset) pairs.” 112×5 = 560. The package does not show the subtraction that yields 507.

17. **How does the wrong-row offset rule work, including mirrors?** The rule text is complete (`STATEMENT.md` lines 165–167; `rule.rs` lines 5–9, 36). Remaining gaps: why the offset set is specifically `{-2,+2,-15,+15,+30}`; why modulo 5 anchored at 600; why a mirror is `-base` rather than another in-set offset; why four proofs (600, 602, 607, 612) take a **training-row** hint (`STATEMENT.md` lines 169–170) if the scientific story is held-out evaluation. Generic vs policy split is stated (`STATEMENT.md` lines 171–176). `common.py` `rule_pair` (lines 64–72) only tests `r + o >= 712`, not `r + o < 0`; Rust `assignment` tests both bounds (`rule.rs` lines 63–66). For August rows ≥ 600 this coincides; the discrepancy is not explained.

18. **What is the noise, and why is it a witness?** Construction is fully specified (`STATEMENT.md` section 8; `README_FINAL.md` section 5). Why a witness rather than in-circuit generation: “Noise generation remains external provenance; the proof binds the normative bytes” (`CLAIM_BOUNDARY.md` line 19); “The correspondence to a CUDA generator is approximate and is not what the proof binds” (`STATEMENT.md` lines 186–187). Why the proof does not bind the Philox generator itself is not further justified. Why seed `20260823` and call index `r-600` is not motivated beyond matching a protocol convention.

19. **What does the calibration disclosure mean for interpreting the 112 proofs?** The 15×2 rows and the seven August targets are listed (`CLAIM_BOUNDARY.md` lines 23–29). How much the integer scales moved because of those seven rows, versus the eight protocol rows, is not quantified except by the rehearsal histogram with vs without August (`VERIFY.md` lines 277–279). Whether a proof row that was a calibration target is a weaker claim is left to the reader.

20. **What is the integer contract, and why int16?** The contract is `oracle/final/README_FINAL.md` section 3 (rounding, domain, kernels, bounds). Why int16: “int16 weights became the first fidelity baseline” (`AUDIT_TRAIL.md` line 48); “int8 remains a cost option … int16 is the fidelity baseline” (`README_FINAL.md` lines 336, 400). Why not int32, or float-in-circuit, is not argued. Why Q12/Q14/Q12 for C/hint/eps is given as compiled constants, not derived in prose from a bit-budget.

21. **What did the audits find, in full?** Verdict **lines** are verbatim in `AUDIT_TRAIL.md` lines 22–28. “The full verdict texts were not included in the reviewed revision” (`AUDIT_TRAIL.md` lines 13–14). Findings 1–15 of round 6 are only visible as dispositions, not as the auditor’s original text. Round-6 files `astra_r6/ASTRA_VERDICT_package_r6.md` etc. are not here. “These are model reviews, not independent validation” (`AUDIT_TRAIL.md` line 16).

22. **What does the patent mention mean?** `README.md` lines 90–91: “The matter of this package is the subject of an Irish patent application filed on 6 September 2026; it is an application, not a grant, and publication of these proofs grants no licence under it.” No application number, title, claims, or office reference.

23. **Who is BOSUN?** `README.md` line 84: “Drafted, built, proved and verified with BOSUN, the project's automated research assistant, under the principal's direction.” `REDACTION.md` line 12: “the assistant's box identity `BOSUN` reads `BOSUN`.” Whether BOSUN is a model, a harness, a human-operated agent, or a named product is not stated. Who “the coordinator” is (`README_FINAL.md` line 215: “coordinator 2026-09-07”) is not stated.

24. **Who is Cathal Ryan Hynes / PolieBotics beyond “Principal”?** Named (`README.md` line 84). No further identity in the package.

25. **What is ARM-C?** Used as architecture name (`DiffusionDiagnosticUNet` / `ArmCUNet`, `STATEMENT.md` line 151). The acronym is never expanded. Relation to any prior ARM-C paper is not in the tree.

26. **What is ZeeBeam, the ZeeBeam release, and the ZeeBeam manuscript *ZeeBeam: The Zero-Knowledge Beam* v3.20?** Cited (`CLAIM_BOUNDARY.md` lines 36–39, 50–52; `VERIFY.md` lines 48–53, 191–195). The manuscript and the ZeeBeam repo are not in this package. An agent is told not to use the web.

27. **What is Dark Lantern?** Licence name and “repository” (`README.md` line 92; `LARGE_FILES.md` lines 22–24). The `LICENSE` file is **not in this directory** (not in `SHA256SUMS`). Licence text is therefore unread.

28. **What is the data layer `truthbeam` / prefix `results/zkdiff_august_20260907/v1/`?** `LARGE_FILES.md` lines 10–12. How to obtain it without the web is not specified. `_control/MANIFEST.jsonl` “whose SHA-256 digests are fixed at publication in the Dark Lantern repository's root `README.md`” (`LARGE_FILES.md` lines 22–24) — that root README is not here.

29. **What is `fill_results.py` / `tools_release/` / `stage_package.py` / `evidence_allowlist.py`?** Named as the staging/rendering machinery (`README.md` line 101; `receipts/README.md` line 4). Not in this package.

30. **What is G0 / G1 / G2-A / G2-D / G3 / G0E / G0F as a glossary?** Used throughout. `AUDIT_TRAIL.md` lines 31–36 defines the four gates in passing. No glossary.

31. **What is SP1, Groth16, AUROC, CFA, Bayer, GELU, SiLU, Philox, Box-Muller, drand, quicknet, gnark, as this package uses them?** Some (Philox, Box-Muller, quicknet pairing) are specified in code/docs. SP1, Groth16, AUROC, CFA are used without definition. Bayer is “raw Bayer frame” of 4600×5320 (`STATEMENT.md` lines 91, 131).

32. **What is the “eight-seed AUROC” that is not reproduced?** `CLAIM_BOUNDARY.md` line 19. The original figure is not in the package.

33. **What is the “sealed 288-row verification take, which this work never touched”?** `CLAIM_BOUNDARY.md` line 46. Not defined here.

34. **What is “the development machine”?** Development machine (`FULL_GUEST.md` line 4; `PINS.json` line 805). Hardware beyond glibc 2.39 host binaries is not fully specified in the top-level docs.

35. **Why do eight prover processes exit through “the observed GPU-server shutdown exception” (`RESULTS.md` line 321; `receipts/README.md` lines 86–88)?** Stderr is withheld. The package says manifests were complete first. The panic itself cannot be inspected.

36. **What is `NODE_PROVE_READY.md`?** Listed as a companion in `FULL_GUEST.md` line 27. Not in this tree.

37. **How does `python_oracle_rows.py` find the checkpoint in the published layout?** It sets `G1_CKPT` to `oracle/ckpt/final/g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pt` (lines 25–27). The checkpoint in this package is `model/g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pt`. `VERIFY.md` section 7 uses the `model/` path. The tool’s default published path does not resolve.

38. **Are the four August `oracle/final/vectors/*.json` usable without the held `.npz`?** JSON manifests are here; arrays are held (`REDACTION.md` lines 84–85). Layer-by-layer parity for August 650 cannot be rerun.

39. **What is `noise_proposal/` and why was it omitted?** “byte-identical duplicate of `source/noise_august/`” (`REDACTION.md` line 77). `MANIFEST.json` of that comparison is not here.

40. **What does protocol code 9 / ABI 1 encode historically?** Fixed fields (`STATEMENT.md` lines 52–53). Why 9, why 1: not stated.

41. **Is the standalone verifier’s comment about public-value length (1,085 or 1,101 bytes, `tools/standalone_verifier/src/main.rs` lines 6–7) compatible with this package’s 752-byte statements?** The same file says “the proof binds whatever bytes are supplied.” Whether byte 87 (the tamper test) is a meaningful field in `ZBDIFF01` is not discussed (in this layout byte 87 sits inside the session-id padding region per `STATEMENT.md` lines 62–63).

42. **How can an agent check that a drand signature is “the one the relay published”?** `VERIFY.md` lines 195–198: “the public quicknet schedule … is the out-of-band check that a round's signature is the one the relay published, which no proof can do for you.” That schedule is not in the package; checking it needs the network, which this audit forbids.

43. **What is `b3xof` provenance beyond a copy path?** `source/armc-relation/b3xof/PROVENANCE.md` points at a private ZeeBeam snapshot path. The proved original is not here.

44. **Why int16 rather than the int8 scheme that also passed `D_q > 3η`?** See item 20. Cost vs fidelity is named, not quantified as proving-time or constraint-count in this package (int8 is “not proved”, `RESULTS.md` line 94).

45. **What is “the original published checkpoint” that these proofs do not reproduce?** `CLAIM_BOUNDARY.md` line 19. Not identified.

---

## 4. Obstacles ranked by severity

**1. Held inputs that the package’s own reproduction paths require.** Raw frames never published; August `C_int` / `E_*` / `Ct_int` held (`REDACTION.md` lines 69–77). Residual reproduction and proving are blocked by design. Witness `raw_r` is absent even from the shipped prepare directories.

**2. Verification builds assume the network and a preinstalled SP1 stack.** `VERIFY.md` is explicit: empty cargo home needs the network and was not rehearsed; SP1 6.4.0, `protoc`, GNU time, binutils are requirements. No prebuilt verifier, no `vendor/` crate directory, no guest ELF. An agent confined to this directory cannot execute (a), (b), or (c).

**3. Steps that assume knowledge not in the package.** ZeeBeam manuscript Sections 3.4 and 8.3 (`CLAIM_BOUNDARY.md` lines 36–39); Dark Lantern `LICENSE`; data-layer fetch; on-box Astra verdict files; `~/.sp1/circuits/groth16/v6.1.0/`; node path `[private corpus path]/...`; “public quicknet schedule.” `FULL_GUEST.md` still says “never proved” and “[pending node]” (line 4) in a package that contains 112 proofs.

**4. Inconsistencies between files.**

- `offset_rule`: `"direct"` in `STATEMENT.md` / `rule.rs` vs `"standard"` in `oracle/final/august_inputs/manifest.json` line 1105 and `oracle/common.py` line 68.
- `oracle/final/README_FINAL.md` line 4 status: “Rust parity open”; `FULL_GUEST.md` line 4: “parity PASS.”
- `FREEZE_SUMMARY.md` lines 35–36 records `AGREEMENT.md` sha256 `28d8764dea2e45f5...` (the **private** hash in `REDACTION.md` line 32); published file is `b70728c7…`.
- `VERIFY.md` line 23 path `zkdiff_august_20260907` vs this directory name.
- `G2D_NODE_RUNBOOK.sh` `prove` sleeps 20 s (line 97); actual launch schedule is 90 s (`receipts/launch_schedule.txt`; `RESULTS.md` line 321).
- `statement.rs` lines 4–5: “nine `read_vec` items”; the list then has ten, plus the blob as eleventh (`STATEMENT.md` lines 82–99).
- `PINS.json` `noise_files[].file` is `noise_august/noise_000600.i16` (line 80) while `noise_rule` (line 77) and `VERIFY.md` use `source/noise_august/`.
- `python_oracle_rows.py` checkpoint path vs `model/` (item 37 above).
- Standalone verifier comments describe ZeeBeam public-value sizes, not 752-byte `ZBDIFF01`.

**5. Paths that do not resolve in this tree.** `source/oracle_final/`; `oracle/rows/`; `oracle/rows_august/.../C_*.npy`; `oracle/ckpt/final/...pt`; `g1_integer/`; `../src`; `NODE_PROVE_READY.md`; `LICENSE`; `frames_august/frame_000600.raw`; data-layer `repository_package_large_files/`; Astra verdict paths; `tools_release/`.

**6. Undefined acronyms and missing glossary.** ARM-C, SP1, AUROC, TB-v0.9, G0/G1/G2/G3, G0E/G0F, CFA, BOSUN, the development machine, Dark Lantern, ZeeBeam, ARM-C “protocol,” “Truth Beam,” “quicknet,” “gnark.” No glossary file.

**7. Ambiguous wording.** “Held out” vs calibration vs quick screen vs proof set. “Independently verified” (`CLAIM_BOUNDARY.md` line 15) vs “model reviews, not independent validation” (`AUDIT_TRAIL.md` line 16). “Normative noise” vs “CUDA correspondence is approximate.” “Wrapped” root. “Development validation” as a warning that is easy to miss next to AUROC 1.0 tables. `README_FINAL.md` section 0 still tells the reader to change to the oracle directory.

**8. Ledger coverage traps.** `VERIFY.md` lines 35–36: after placing large files, the SHA256SUMS file-count check no longer matches. Large files are not here, so the count check as written can pass; an agent who later fetches them must remember the caveat. `SHA256SUMS_G2D` does not validate published substituted files.

---

## 5. Three things the package does well

1. **A pinned, layered claim boundary that is actually used.** `CLAIM_BOUNDARY.md` puts three auditor-written paragraphs above every other document, then expands calibration in full (rows listed, “must not be described as an untouched test set”). `STATEMENT.md` section 9 lists the nine acceptance layers in order. That is unusually honest about what a Groth16 wrap does and does not say.

2. **Verification instructions that were rehearsed on a copy of the published tree, with requirements and failures named.** `VERIFY.md` section 9 records commands, times, and the three tests that fail without held August exports. Paths are anchored to `P`. Tamper controls (flipped public byte, wrong key, mutated identities) are part of the happy-path instructions, not an appendix.

3. **The public statement is decodable without the prover.** `tools/decode_zbdiff01.py` is standard-library Python; `STATEMENT.md` section 2 is a byte-level table; per-row expected identities, noise BLAKE3s, chain-log digests, and residual sums are in JSON a reader can open. For row 600 an agent can read `R_correct = 4,435,539,299` from the table, the receipt, and the identities file and see they agree, even without running a verifier.

---

## 6. Verdict

**NO** — an agent with this package alone cannot follow and check all the proofs: Groth16 checking still needs a network (or a cargo cache this tree does not contain) and a Rust/SP1 toolchain; residual-sum reproduction and proof reproduction need held camera tensors and raw frames that the package itself says are absent.

**Single most important fix:** ship a prebuilt standalone verifier (or a `cargo vendor` of the 209 locked crates) **and** the August integer input tensors `oracle/final/august_inputs/row_*.npz`, so checking a proof and recomputing one row’s `R_correct`/`R_wrong` do not require crates.io, SP1, or uncleared frames.
