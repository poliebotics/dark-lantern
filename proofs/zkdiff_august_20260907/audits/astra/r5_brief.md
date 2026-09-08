> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

# Astra brief r5: audit of the complete zkdiff guest before proving (BOSUN, 2026-09-07)

Read-only audit. Rounds 1-4 are in (on-box) {ASTRA_VERDICT_zkdiff_r1.md, astra_r2/, astra_r3/, astra_r4/}. The complete guest is now built and executed (no proof yet). Judge whether it may be proven and, if so, what the receipts and the public description must carry.

Files under (on-box) source/:
- FULL_GUEST.md (result table, integration, pins, parity, instruction count, batch manifest, node runbook; section 5's run-2 breakdown may still be a placeholder)
- armc-relation/ : RELATION.md (statement, ZBDIFF01 public layout, legs, preprocessing citations), relation/src/*.rs (frame.rs, hint.rs, noise.rs, membership.rs, beacon.rs, emission.rs, statement.rs, net.rs, spec.rs), adapter/ (zkdiff-armc-adapter, kind 1), program/src/main.rs (the guest), script/ (zkdiff-execute, zkdiff-ceremony with Groth16 request and tamper controls, zkdiff-batch prepare|execute|prove), build_reproducible.sh, .cargo/config.toml, runs/ (batch_prepare_20260907, batch_execute_20260907, batch_execute_r4_20260907, SOURCE_DIGESTS_*), b3xof/ (proved crate copied verbatim, PROVENANCE.md)
- armc-int/ (kernels after r4: src/kernels.rs, model.rs, loader.rs, blob.rs; tests/parity.rs, tests/fixtures.rs), CYCLES.md
- vectors_relation/ (gen_vectors.py, MANIFEST.json), frames_august/frame_00060{0,1,2,3}.raw
Oracle: oracle/final/ (README_FINAL.md sections 3 and 5: saturation contract and normative noise rule; august_inputs/manifest; fixtures/).
Declared evaluation protocol: proof set = all 112 held-out August rows 600-711 (never trained on; training used August rows 0-599 plus d2/v10 training blocks), wrong offset = [-2,+2,-15,+15,+30][(r-600) mod 5] with the mirrored offset for the ten rows where r+offset >= 712, every outcome published with sign; noise bytes normative and hash-bound.
Reported: ELF 0f1fd5249d3e1e8c38b63ae96d6c6dbb9aa58957650be7170ea85ba7b265db9e (654,200 bytes), vkey 0x0009823f…8482 (full value in FULL_GUEST.md); parity PASS on d2 1328, on all eight FINAL layer-vector sets (188/188), on the 42 boundary fixtures, and guest = native = Python on August rows 600-603; ~14.25 G instructions per row; constants digest committed at public offset 564; clip events public; source digests and lock checks; node prepared (NODE_PROVE_READY.md).

Questions:
1. Does the guest bind what the statement claims: whole-frame reduction from the committed raw frame, both XOF hints derived from the chain state, the forward noising with hash-bound normative noise, both conditioning rows with identities and the permitted offset, the constants/spec digests, the session membership, the previous-row drand leg, and the same noisy frame and target in both passes? Any host-trust leak or unbound input left?
2. Is the public layout (ZBDIFF01, 752 bytes) sufficient and unambiguous for an independent verifier, and what must the verifier check beyond the Groth16 proof (vkey, digests, rule constants)?
3. Is the saturation and clip accounting consistent between guest, adapter and oracle after r4, and is the clip-events field correctly exposed and interpreted (a nonzero count must be disclosed, not hidden)?
4. Reproducibility: are the pins, lock checks, offline config, source digests and the node rebuild/assert procedure adequate for an auditable ELF and vkey? Anything that must be recorded before the first proof (e.g. toolchain identity, exact commands)?
5. The pilot-then-batch plan: one Groth16 proof of row 600 on one A100 first, then eight parallel provers; what must be measured and recorded from the pilot before the batch is sized (time, VRAM, host RSS, shards), and any risk in running eight sp1-gpu-server instances on one node?
6. Receipts and publication: what each per-row receipt and the batch manifest must contain, what negative controls must accompany the batch (tampered inputs, wrong offset, swapped hints, mutated public values), and the exact claim boundary wording for the public description (execution binding of an integer diffusion evaluator adapted from the frozen ARM-C protocol; no realness/liveness/causality; development-validation status of d2/v10; the August rows' held-out status and the training rows 0-599).
7. Any defect in FULL_GUEST.md's numbers or reasoning.

Answer with numbered findings, each with a verdict and file/line, then one line: VERDICT: PROVE / REVISE / STOP with the single most important change before the pilot proof.
