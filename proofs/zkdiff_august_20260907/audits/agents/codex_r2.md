> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

# Outside-agent audit report

Method note: I only read files. I did not execute hashes, verifiers, builds, re-executions, or proofs.

## 1. What I understood the package claims

1. The package claims to contain one SP1 6.4.0 Groth16 proof for each of August rows 600–711, for 112 proofs total. (`README.md` lines 14–23)
2. Each proof binds a complete raw frame, its session-tree membership and predecessor chain state, two rendered conditionings, one normative noise tensor, and two executions of a pinned integer denoiser. (`STATEMENT.md` lines 18–36)
3. The published result is that all 112 proofs were accepted, all 112 differences `R_wrong - R_correct` were positive, and every clipping count was zero. (`RESULTS.md` lines 196–206, `RESULTS.md` line 324)
4. Rows 600–711 gave no gradient to weight training, but seven were used for quantisation calibration and four appeared in a training-time screen, so they are not an untouched test set. (`CLAIM_BOUNDARY.md` lines 23–34)
5. The proofs establish only the specified computation on committed bytes, not physical capture, illumination causality, realness, liveness, adversarial resistance, or unseen-session generalisation. (`CLAIM_BOUNDARY.md` lines 15–19)

## 2. The verification path

First set the package root and check its ledger:

```bash
P=the package root
(cd "$P" && sha256sum -c --quiet SHA256SUMS && echo LEDGER_OK)
```

Documented at `VERIFY.md` lines 41–56. I did not run it.

### a. Verify one proof

Full acceptance verification of row 600:

```bash
mkdir -p /tmp/zkdiff_one
"$P/capsule/zkdiff-verify" \
  --proof "$P/proofs/row_000600_groth16.bin" \
  --expect "$P/source/expected_identities_august.json" \
  --report /tmp/zkdiff_one/row_000600.verify.json
```

Independent Groth16-layer route using the raw proof:

```bash
"$P/capsule/zeebeam-standalone-verifier" \
  "$P/proofs/row_000600_groth16_proof.bin" \
  "$P/public_values/row_000600_public_values.bin" \
  0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027
```

Everything needed to execute these commands is present for x86-64 Linux: proof, statement, expected identities, program key, circuit verifying key, and two static binaries. The first route also checks all frozen statement identities; the second checks only Groth16 and two tamper controls. (`capsule/README.md` lines 16–26, `VERIFY.md` lines 64–98)

Limitation: both are shipped binaries. Without the rebuild below, the package alone does not independently establish that those binaries correspond to the supplied source.

### b. Verify all 112

```bash
CAPSULE_OUT=/tmp/zkdiff_capsule_out \
  bash "$P/capsule/verify_offline.sh"
```

The script checks its ledger, embedded ELF and circuit-key identities, all 112 framed proofs with the acceptance verifier, all 112 raw proofs with the standalone verifier, row-600 negative controls, and equality between capsule and root artifacts. (`capsule/verify_offline.sh` lines 20–92)

Everything needed is present on x86-64 Linux with Bash and coreutils. It needs a writable output directory but does not need Rust, Python, or a network. Again, this checks with prebuilt binaries rather than rebuilding them.

### c. Rebuild the program and compare its identity

The package’s one-command wrapper would be:

```bash
"$P/replicate/replicate.sh" \
  --from-local "$P" \
  --repo-only \
  --no-b3sum \
  --work /tmp/zkdiff_rebuild \
  build
```

With an already populated pinned toolchain and Cargo cache, the direct command is:

```bash
(cd "$P/source/armc-relation" && ./build_reproducible.sh)
```

Success must end with `BUILD_REPRODUCED_OK` and assert:

- ELF size: 396,200 bytes
- ELF SHA-256: `51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc`
- program vkey: `0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027`
- circuit-key SHA-256: `4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696`

(`source/armc-relation/build_reproducible.sh` lines 15–18, `source/armc-relation/build_reproducible.sh` lines 96–109)

The package does **not** contain everything needed under the stipulated no-network conditions. Missing are Rust 1.98.0, `cargo-prove`, the Succinct 1.94.0-dev toolchain, `protoc`, GNU build tools, the locked crates, and two patched Git dependencies. Their URLs and hashes are given, but their bytes are not bundled. (`VERIFY.md` lines 108–154)

### d. Reproduce one row’s residual sums

Row 600 is self-contained:

```bash
CAPSULE_OUT=/tmp/zkdiff_capsule_out \
  bash "$P/capsule/reexecute/reexecute_row.sh"
```

This uses the shipped `frame_000600.raw`, static `zkdiff-batch`, chain log, normative noise, constants, and expected identities, then compares the complete 752-byte recomputed statement with the published one. (`capsule/reexecute/reexecute_row.sh` lines 28–48)

Everything needed for row 600 is present, assuming x86-64 Linux and about 17 GB RAM. It is native Rust re-execution, not proof generation and not an independently rebuilt executable.

For rows 601–711, the command exists but their frames are outside this directory:

```bash
bash "$P/capsule/reexecute/reexecute_row.sh" 684 \
  --frames-dir /path/to/frames
```

The missing item is `frame_000684.raw` or the corresponding frame for the chosen row. The 111 additional frames and per-row `.npz` inputs are only referenced on the data layer. (`capsule/README.md` lines 51–67)

### e. Reproduce a proof

For row 600, the prescribed command is:

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

The script would create a fresh randomized Groth16 proof, verify it cold, and require its public statement to equal the published statement. (`replicate/replicate.sh` lines 888–925)

The package does **not** provide everything needed. Missing are:

- an A100-class CUDA GPU, with observed peak about 28.5 GiB;
- `sp1-gpu-server` 6.4.0;
- the 6.2 GB circuit archive, notably `groth16_pk.bin`, `groth16_circuit.bin`, `constraints.json`, and `groth16_witness.json`;
- `cargo-prove`, both Rust toolchains, `protoc`, and locked dependency sources;
- network access or an offline cache containing those objects.

Only `groth16_vk.bin` is shipped. Moreover, the wrapper’s GPU path is explicitly “not rehearsed here.” (`replicate/README.md` lines 49–66, `replicate/README.md` lines 119–121)

## 3. Questions I could not answer from the package alone

The package does answer all public-output fields in `STATEMENT.md` lines 75–103, the exact direct/mirrored rule in `STATEMENT.md` lines 189–206, what the noise is and why it is a witness in `STATEMENT.md` lines 208–220, the calibration disclosure, the integer contract and int16 rationale, the audit findings, the limited meaning of the patent mention, and who BOSUN is. The remaining unanswered questions are:

1. What are the bytes and full contents of the authority manifest whose SHA-256 is `740d752d…d783`? I expected it beside the chain/session material; only its digest is published. (`FAQ.md` lines 26–31)

2. How was `S_0` generated, with what entropy source, and by whom specifically? The package only says it was “the seed the recorder chose.” (`FAQ.md` lines 33–36)

3. What does the constant `64000` in every 28-byte `meta` record mean? The package explicitly marks this unknown. (`FAQ.md` lines 42–46)

4. What scene was recorded, and what exact camera, projector, lens, exposure, gain, synchronisation, and calibration settings produced it? I expected this in the recording primer, authority manifest, or dataset documentation; only dimensions and general equipment classes are stated. (`FAQ.md` lines 104–109)

5. When and where were d2 and v10 recorded, what did their scenes contain, and where are their raw frames? Their row counts and train/evaluation blocks are given, but their dates and frame locations are explicitly absent. (`FAQ.md` lines 111–119)

6. Can the model training actually be reproduced? No: the raw August training frames 0–599, d2/v10 frames, and earlier candidate sweeps are absent or on-box. (`REDACTION.md` lines 96–101, `RESULTS.md` lines 49–59)

7. Was the referenced data-layer upload ever completed, and do its bytes match the listed hashes? The directory contains only row 600’s frame and `.npz`; FAQ says the prefix remains empty “Until the upload is released.” With no network, I cannot settle its present state. (`FAQ.md` lines 279–281)

8. Do the compiled quicknet key and recorded signatures actually correspond to the public drand quicknet relay? The package calls this an out-of-band network check that no proof supplies. (`VERIFY.md` lines 283–293)

9. Are the August results “good” against a meaningful null? There is no random-network or shuffled-hint baseline and no confidence interval for the 112 August margins; only chance levels for AUROC and paired fraction are stated. (`FAQ.md` lines 165–169)

10. Why are the August margins roughly half the d2/v10 margins? The package says this is “reported, not explained.” (`FAQ.md` line 171)

11. What criterion selected the 24,000-step seed-20260908 checkpoint over variants with larger margins? The chronology is reconstructed, but “no written criterion” exists. (`FAQ.md` lines 183–188)

12. Would excluding the seven August calibration rows change any proved residual or sign? This counterfactual was not measured. (`FAQ.md` lines 152–155)

13. Why were those five offsets chosen, why were they cycled modulo five, and why was mirroring preferred beyond retaining all rows? The mechanics are complete, but “no further rationale is recorded.” (`FAQ.md` lines 201–205)

14. What causes the unresolved approximately `1.1e-3` bf16 fidelity difference? Its scope is explained, but its cause remains unresolved. (`RESULTS.md` lines 91–95)

15. Has the package in its present, post-round-7 and post-publication-decision form been re-audited? No; the package states it was not re-read by the second model. (`AUDIT_TRAIL.md` lines 148–154)

16. What exactly happened in the eight `sp1-cuda` destructor panics, and does the absent pilot report support all quoted timing details? The backtraces and pilot report remain on-box. (`receipts/README.md` lines 68–89, `RESULTS.md` lines 183–194)

17. [Question about the patent filing's details redacted; the package states the filing by date only (`README.md`, `LICENSE`).]

18. Can the publication front matter and tables be regenerated exactly? `fill_results.py`, `stage_package.py`, `make_pins.py`, and `evidence_allowlist.py` are not included. (`FAQ.md` lines 283–285)

19. Does the new `replicate.sh prove` wrapper work end to end on a GPU? It was not rehearsed. (`replicate/README.md` lines 119–121)

20. Which complete third-party licence texts govern the package? `LICENSE` points to root `THIRD_PARTY_NOTICES.md` and `licenses/`, neither of which exists here; only a capsule-specific notice is present. (`LICENSE` lines 58–65)

## 4. Obstacles ranked by severity

1. **Critical — source-to-proof identity cannot be checked offline.** The capsule can verify all proofs, but its binaries cannot be rebuilt from this directory because toolchains and dependency sources are external. Thus an isolated agent must trust the shipped verifier binaries and their build records.

2. **Critical — proof reproduction is not self-contained.** The proving key and circuit files, GPU server, build toolchains, dependencies, and GPU are absent. The package supplies hashes and download instructions, not the required bytes.

3. **High — most published inputs are not package files.** `LARGE_FILES.md` lists 4,664 external files, and 111 of the 112 raw frames are outside the directory. “Published on the data layer” is not equivalent to “available in this package alone.” (`LARGE_FILES.md` lines 8–17)

4. **High — contradictory current wording about publication status.** `FRAMES.md` says all frames were published, while active or supposedly corrected files still say:

   - “Raw frames are never published.” (`GLOSSARY.md` lines 32–35)
   - “needs the frame (held).” (`HASHES.md` lines 41–53)
   - “the frames themselves are not published.” (`VERIFY.md` lines 295–298)
   - “Raw frames are not published” and tensors are “held pending clearance.” (`replicate/README.md` lines 99–106)

5. **High — other inconsistencies survived the correction pass.**

   - The glossary says the quick screen scored 28 held-out rows, but the detailed account says only four proof rows and 24 training rows. (`GLOSSARY.md` lines 134–136, `FAQ.md` lines 144–150)
   - `VERIFY.md` says no `[confirm]` tags remain, but several remain. (`VERIFY.md` lines 37–39, `VERIFY.md` lines 356–360, `VERIFY.md` lines 471–473)
   - `RELATION.md` still calls it a “nine-item witness”; the current statement specifies ten `read_vec` items plus the constants blob. (`source/armc-relation/RELATION.md` lines 343–346, `STATEMENT.md` lines 108–125)

6. **Medium — unresolved and hard-coded paths.** Receipts and frozen identities contain acknowledged `/home/...` and `/lambda/...` provenance paths. More seriously, `source/vectors_relation/gen_vectors.py` retains private absolute paths, so it is not directly rerunnable in this layout. (`PINS.json` lines 34–37, `source/vectors_relation/gen_vectors.py` lines 37–45)

7. **Medium — important provenance remains external.** The authority-manifest preimage, public drand comparison, prior ZeeBeam manuscript/repository, raw training datasets, incident logs, and pilot record are unavailable.

8. **Low — the glossary is excellent but not literally exhaustive.** Technical acronyms such as ABI, BLS, SDK, and ELF are used without expansion, although their operational roles are usually explained.

## 5. Three things the package does well

1. It draws an unusually clear claim boundary and repeatedly distinguishes computation binding from physical-world claims.

2. The 752-byte statement, witness, fourteen relation legs, every major hash construction, fixed-point formats, residual denominator, wrong-row rule, and clipping semantics are documented concretely and linked to source.

3. The offline capsule is genuinely useful in design: it includes two verifier implementations, all 112 proofs and statements, negative controls, ledgers, pinned keys, and a row-600 native re-execution capsule.

## 6. Verdict

**NO — the single most important fix is to bundle a hash-pinned offline source-to-vkey build environment, including all locked crates and SP1 toolchains, so the shipped verifier and proved program can be independently rebuilt rather than trusted as binaries.**