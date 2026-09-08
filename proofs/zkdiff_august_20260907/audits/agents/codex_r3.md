> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

# 1. What I understood the package claims

1. The package claims to contain 112 SP1 Groth16 proofs, one for each August row 600–711, all accepted under frozen identities. (`README.md` line 10)
2. Each proof binds a complete raw frame, session membership and predecessor state, two rendered conditionings, one normative noise tensor, and two executions of a pinned integer denoiser at timestep 150. (`STATEMENT.md` line 18)
3. The reported result is that all 112 differences `R_wrong - R_correct` are positive and all clipping counts are zero. (`RESULTS.md` line 200)
4. Rows 600–711 supplied no weight-training gradient, but seven entered quantisation calibration and four appeared in a training-time screen, so this is not an untouched test set. (`CLAIM_BOUNDARY.md` line 21)
5. The proofs establish only the specified computation on committed bytes, not physical capture, illumination causality, realness, liveness, adversarial resistance, or unseen-session generalisation. (`CLAIM_BOUNDARY.md` line 15)

# 2. The verification path

I only inspected these commands; I did not execute hashes, verifiers, builds, re-executions, or proofs.

First, on a writable or read-only copy:

```bash
P=the package root
(cd "$P" && sha256sum -c --quiet SHA256SUMS && echo LEDGER_OK)
```

This is the package’s initial integrity check. (`VERIFY.md` line 46)

## a. Verify one proof

Full acceptance verification of row 600:

```bash
mkdir -p /tmp/zkdiff_one
"$P/capsule/zkdiff-verify" \
  --proof "$P/proofs/row_000600_groth16.bin" \
  --expect "$P/source/expected_identities_august.json" \
  --report /tmp/zkdiff_one/row_000600.verify.json
```

Independent Groth16-layer check:

```bash
"$P/capsule/zeebeam-standalone-verifier" \
  "$P/proofs/row_000600_groth16_proof.bin" \
  "$P/public_values/row_000600_public_values.bin" \
  0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027
```

Availability: **YES**, on x86-64 Linux. The proof, public values, program key, circuit verifying key, expected identities, and two static verifiers are present. The first route checks the frozen statement identities; the second checks only Groth16 and its tamper controls. (`capsule/README.md` line 16)

Caveat: both are shipped binaries. Their connection to the supplied source remains dependent on the unavailable rebuild described below.

## b. Verify all 112

```bash
CAPSULE_OUT=/tmp/zkdiff_capsule_out \
  bash "$P/capsule/verify_offline.sh"
```

Availability: **YES**, with Bash and coreutils on x86-64 Linux. The directory contains 112 framed proofs, 112 raw proofs, 112 public statements, and the frozen identities. The script checks both verifiers, counts exactly 112, runs row-600 controls, and compares the capsule copies with the root copies. (`capsule/verify_offline.sh` line 20)

## c. Rebuild the program and compare its identity

The package’s wrapper is:

```bash
"$P/replicate/replicate.sh" \
  --from-local "$P" \
  --repo-only \
  --no-b3sum \
  --work /tmp/zkdiff_rebuild \
  build
```

With all dependencies already cached, the direct command is:

```bash
(cd "$P/source/armc-relation" && ./build_reproducible.sh)
```

Success must end with `BUILD_REPRODUCED_OK` and assert:

- ELF size `396200`
- ELF SHA-256 `51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc`
- program vkey `0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027`
- circuit-key SHA-256 `4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696`

(`source/armc-relation/build_reproducible.sh` line 15, `source/armc-relation/build_reproducible.sh` line 96)

Availability: **NO under the stipulated conditions**. Missing are Rust 1.98.0, `cargo-prove`, the Succinct guest toolchain, `protoc`, build tools, the locked crate sources, and the two patched Git dependencies. Their URLs and hashes are documented, but their bytes are absent. The supposedly offline `build_kit/`, including its essential `BUILD_KIT.md`, exists only on the external data layer and is not in this directory. (`VERIFY.md` line 113, `VERIFY.md` line 215)

## d. Reproduce one row’s residual sums

Row 600 is self-contained:

```bash
CAPSULE_OUT=/tmp/zkdiff_capsule_out \
  bash "$P/capsule/reexecute/reexecute_row.sh"
```

Availability: **YES**, on x86-64 Linux with roughly 17 GB RAM. The static batch driver, row-600 raw frame, chain log, normative noise, constants blob, expected identities, and published statement are present. The script runs the guest in the SP1 CPU executor, compares it with native host evaluation, and requires all 752 output bytes to equal the published statement. (`capsule/reexecute/reexecute_row.sh` line 30)

This does not provide an independent Python-oracle calculation: that route requires missing d2 vectors, cached rows, and August `.npz` files from the data layer. (`FAQ.md` line 397)

For rows 601–711, the command exists, but the corresponding frame is missing from this directory:

```bash
bash "$P/capsule/reexecute/reexecute_row.sh" 684 \
  --frames-dir /path/to/frames
```

## e. Reproduce a proof

For row 600:

```bash
"$P/replicate/replicate.sh" \
  --from-local "$P" \
  --repo-only \
  --no-b3sum \
  --work /tmp/zkdiff_reprove \
  --frame "$P/capsule/reexecute/frame_000600.raw" \
  --device 0 \
  prove 600
```

Availability: **NO under the stipulated conditions**. The row-600 frame, witnesses, program vkey, verification key, source, and hashes are present, but these are missing:

- an A100-class CUDA GPU with about 28.5 GiB available VRAM;
- `sp1-gpu-server` 6.4.0;
- both Rust toolchains, `cargo-prove`, `protoc`, and dependency sources;
- the Groth16 proving material, especially `groth16_pk.bin`, `groth16_circuit.bin`, `constraints.json`, and `groth16_witness.json`.

Only `groth16_vk.bin` is bundled. The absent files’ hashes and download locations are documented. (`replicate/replicate.sh` line 914, `VERIFY.md` line 135)

# 3. Questions I could not answer from the package alone

Several requested subjects are answered well:

- All 752 public-output bytes are mapped and constrained. (`STATEMENT.md` line 69)
- `HASHES.md` identifies every published hash class, although some preimages are absent. (`HASHES.md` line 8)
- The result tables define residuals, `D`, MSE units, paired fraction, AUROC, clipping, proving time, and digest columns. (`RESULTS.md` line 24, `RESULTS.md` line 206)
- The complete direct/mirrored rule and all ten mirrored rows are stated. (`STATEMENT.md` line 189)
- The noise is a Philox-derived Q12 tensor; it is a witness because its CUDA correspondence uses approximate transcendental emulation, while the exported bytes are normative. (`STATEMENT.md` line 209)
- The calibration disclosure and exact seven August rows are explicit. (`CLAIM_BOUNDARY.md` line 21)
- The integer contract is documented, and int16 was chosen as the predeclared fidelity baseline, giving a minimum margin/error ratio of about 80 versus 19 for int8. (`FAQ.md` line 243)
- BOSUN is identified as a Claude-family automated research assistant with no publication authority. (`GLOSSARY.md` line 241)

The remaining unanswered questions are:

1. **Are the claimed data-layer objects actually present and authentic now?** The directory says they are “served from the data layer,” but contains neither `frames/`, `build_kit/`, nor the 4,664 large files. The authoritative `_control` digest is itself said to live in an external repository README. I expected a local control manifest in `FRAMES.md` or `LARGE_FILES.md`. (`LARGE_FILES.md` line 10)

2. **What are the bytes and complete contents of the authority manifest?** Its SHA-256 is identified, but it is explicitly “not published” and “not recomputable from the package.” I expected it beside the session material. (`HASHES.md` line 36)

3. **How was `S_0` generated, by whom, and from what entropy?** The only answer is “the seed the recorder chose.” I expected this in the authority manifest or protocol record. (`FAQ.md` line 35)

4. **What does the constant `64000` in every `meta` record mean?** The glossary explicitly says its meaning “is not stated.” (`GLOSSARY.md` line 71)

5. **What exact equipment and capture settings produced the August data?** Dimensions, Bayer format, Aravis, and general equipment classes are stated, but camera model, lens, exposure, gain, projector calibration, timing/synchronisation, and the authority manifest are absent. I expected these in `FRAMES.md` or recording documentation.

6. **Were the frames physically captured as described, live, and illuminated by the claimed pattern?** The package deliberately excludes all such claims, so this cannot be answered from the proofs. (`CLAIM_BOUNDARY.md` line 19)

7. **When and where were d2 and v10 recorded, what did they depict, and where are their raw frames?** Their sizes and block divisions are given, but their dates and frame locations are explicitly “not decided at publication.” (`FAQ.md` line 113)

8. **Can the model training and selection search be reproduced?** No: the raw d2/v10 data, August training frames 0–599, and earlier sweeps are absent or held on-box; `train_lean.py` retains `[private corpus path]`. (`RESULTS.md` line 49, `oracle/trainer/train_lean.py` line 66)

9. **Do the compiled quicknet key and recorded signatures actually match the public drand relay?** The package calls this an out-of-band network check that “no proof can do for you”; the required web check is unavailable here. (`VERIFY.md` line 328)

10. **Are the August results good against a meaningful null?** The package candidly supplies no random-network or shuffled-hint baseline and no confidence interval for the 112 August margins. It gives chance levels for AUROC and paired fraction, but that does not settle practical significance. (`FAQ.md` line 169)

11. **Why are the August margins roughly half the d2/v10 margins?** The package says, “Reported, not explained.” (`FAQ.md` line 175)

12. **What written criterion selected the 24,000-step seed-20260908 checkpoint over variants with larger margins?** Only a chronology-derived explanation is supplied; “No written criterion” exists. (`RESULTS.md` line 49)

13. **Would excluding the seven August calibration rows change any proved residual or sign?** This counterfactual was not measured. (`FAQ.md` line 156)

14. **Why were these five offsets chosen and cycled modulo five?** The mechanics and effect are complete, but “no further rationale is recorded.” (`FAQ.md` line 203)

15. **What caused the unresolved approximately `1.1e-3` bf16 fidelity discrepancy?** Its scope is explained, but its cause and the torch version used when the node cache was made remain unresolved. (`RESULTS.md` line 93, `source/armc-relation/RELATION.md` line 404)

16. **Does full oracle regeneration reproduce the current published tree?** The August exporter and complete oracle regeneration remain tagged `[confirm]`, and the required arrays are absent. (`VERIFY.md` line 393, `VERIFY.md` line 552)

17. **What caused the slower batch proving time and the eight cleanup failures?** CPU/memory contention is labelled only an interpretation; shard counts were not logged, and the diagnostic stderr files remain withheld. (`RESULTS.md` line 331)

18. **What caused the single 533.8 ms frame gap?** The package says the cause is not recorded. (`FAQ.md` line 412)

19. **What did the unpublished privacy audit contain, and what was “Astra round 9”?** Round 7’s full text is withheld, while `REDACTION.md`, `FAQ.md`, `HASHES.md`, and the `AUDIT_TRAIL.md` log cite a round 9 that is absent from the audit table and from `audits/astra/`. (`AUDIT_TRAIL.md` line 25, `REDACTION.md` line 23)

20. **Was the final post-round-9 package audited as a whole?** The package says the revision applying the preceding rounds “has not itself been re-read.” (`AUDIT_TRAIL.md` line 208)

21. **What patent was filed?** The package supplies only “Patent filing date: 6 September 2026” and the licence’s non-assertion for permitted non-commercial use; it gives no title, application number, jurisdiction, applicant, claims, or technical scope. (`README.md` line 157, `LICENSE` line 63)

22. **Can the package front matter, pins, redaction, and result tables be regenerated exactly?** `fill_results.py`, `stage_package.py`, `make_pins.py`, and `evidence_allowlist.py` are not included. (`FAQ.md` line 296)

23. **Can the relation vectors be regenerated by their advertised command?** `source/vectors_relation/README.md` says `python3 gen_vectors.py`, but the script expects nonexistent `g1_integer/`, `[zeebeam repository clone]`, `[truthbeam verification run]`, and external renderer paths. (`source/vectors_relation/README.md` line 10, `source/vectors_relation/gen_vectors.py` line 35)

24. **What externally authenticates the root `SHA256SUMS`?** `HASHES.md` points to the absent Dark Lantern root README, so the local ledger checks internal consistency but has no trust anchor inside this directory. (`HASHES.md` line 84)

25. **What complete third-party licence set governs the package?** `LICENSE` refers to root `THIRD_PARTY_NOTICES.md`, `licenses/`, and `CITATION.cff`, none of which is present here; only a capsule-specific notice is bundled. (`FAQ.md` line 283)

26. **What would int8 proving cost, and would a 24 GB GPU work?** Int8 proving was not measured, while failure on a 24 GB card is explicitly untested. (`FAQ.md` line 251, `replicate/README.md` line 64)

# 4. Obstacles ranked by severity

1. **Critical — essential “package” material is external.** The offline build kit, 111 frames, all ordinary August row `.npz` inputs, d2/v10 vectors and caches, and Groth16 proving material are only referenced on a data layer. Under this audit’s package-only rule, those paths do not resolve.

2. **Critical — source-to-vkey identity cannot be independently rebuilt.** The static capsule can verify the proofs, but an isolated reader must trust its binaries and build records because the dependency sources and toolchains needed to recreate them are absent.

3. **High — proof reproduction is not self-contained.** The proving key, circuit cache, GPU server, toolchains, and suitable GPU are missing, despite the command and hashes being supplied.

4. **High — only row 600 can be recomputed from a real frame.** The package proves all 112 statements cryptographically, but checking the claimed computation against actual input bytes for the other 111 requires externally hosted frames.

5. **High — session provenance has non-recomputable or out-of-band components.** The authority-manifest preimage is absent, `S_0` provenance is unknown, and quicknet identity requires a network check.

6. **Medium — important scripts retain unresolved paths.** `gen_vectors.py` contains bracket placeholders and private-layout assumptions; receipts intentionally contain `[frames directory]` and other provenance paths that “resolve nowhere in this package.” (`receipts/README.md` line 131)

7. **Medium — audit and operational evidence is incomplete.** The privacy audit, prover stderr, pilot report, parts of the witness evidence, and release tooling are withheld; the final revision was not re-read.

8. **Medium — inconsistencies remain.**

   - The audit trail describes eight rounds, but several current files cite “Astra round 9” without an entry or audit text.
   - `source/vectors_relation/README.md` calls its synthetic input a “complete nine-item witness,” while the current statement requires ten `read_vec` items plus the constants blob. (`source/vectors_relation/README.md` line 21)
   - `LARGE_FILES.md` totals the external files at `633,286,043` bytes, while `replicate/README.md` says `633,315,259` bytes without explaining the 29,216-byte difference. (`LARGE_FILES.md` line 59, `replicate/README.md` line 21)

9. **Low — historical notes demand careful reconciliation.** Files such as `FULL_GUEST.md` retain stale “never proved” and `[pending node]` text under corrective banners. The banners are honest, but an agent must distinguish frozen history from current truth throughout.

10. **Low — the glossary is strong but not literally exhaustive.** ABI, BLS, BN254, SDK, ELF, bincode, GenICam, Aravis, Random123, and some SP1-specific terms are used without full standalone definitions.

# 5. Three things the package does well

1. It draws an exceptionally clear claim boundary and repeatedly distinguishes computation binding from physical-world claims.

2. It documents the complete statement layout, witness, fourteen relation legs, hash constructions, fixed-point formats, clipping semantics, and mirrored-offset cases with source references.

3. The offline capsule is genuinely useful: it bundles two verifiers, all 112 proofs and statements, frozen identities, negative controls, and a real row-600 frame with toolchain-free re-execution.

# 6. Verdict

**NO — the single most important fix is to bundle the complete data-layer payload, including `build_kit/`, all 112 frames, and all oracle inputs, inside the publication package rather than referring to external storage.**