---
version: 3.3
date: 2026-09-09
status: settled-ML-result; v4-claim-draft-audited-PASS; broader-interpretations-not-audited
author: Cathal Ryan Hynes (author of record); drafted with BOSUN, the project's automated research assistant
---

# Same Difference: uncropped ARM-C row conditioning across all eight seeds

> **SETTLED.** All eight seeds were re-evaluated at the declared horizon (step 12000,
> `latest.pt`, verified per result file) under the frozen evaluator, and the claim passed a
> four-round hostile Sol audit at ultra effort (v1 BLOCK -> v4 **PASS**, 2026-08-31). The
> audited claim text, evidence, attestation, independent recompute, full training histories
> and all four audit transcripts live in
> `experiments/nocrop_v2_20260830/audit_20260831/` on the ZeeBeam NFS and in
> `scratch/zeebeam_audits/nocrop8seed_20260831/` on bosun-desk. The v2 mixed-checkpoint table this
> replaces is preserved in the Log and in the as-audited bundle copies.

## 1. Seed-wise result (settled)

Pooled Mann-Whitney AUROC of correct-row conditioning against the mean of five wrong-row
offsets, the within-row paired fraction, and the mean wrong-minus-correct margin with its
contiguous-block bootstrap 95% CI. Every run trained from scratch (every history opens at
step 50 with loss ~0.987, the untrained denoising level) to the declared 12000 steps.
Evaluator sha256 `0bcfa7a7...`; every statistic independently recomputed from the raw
per-row scores by fresh code with 16/16 agreement (`INDEPENDENT_RECOMPUTE.json`).

| seed | step | AUROC d2 | AUROC v10 | paired d2/v10 | delta d2 (mean [95% CI]) | delta v10 (mean [95% CI]) |
|---|---|---|---|---|---|---|
| 20260825(base) | 12000 | 1.0 (exact) | 1.0 (exact) | 1.0000/1.0000 | 2.806e-03 [2.798e-03,2.813e-03] | 2.798e-03 [2.782e-03,2.814e-03] |
| base_seed0828_boxA | 12000 | 1.0 (exact) | 1.0 (exact) | 1.0000/1.0000 | 2.761e-03 [2.751e-03,2.771e-03] | 2.777e-03 [2.762e-03,2.790e-03] |
| base_seed0829_boxA | 12000 | 1.0 (exact) | 1.0 (exact) | 1.0000/1.0000 | 2.501e-03 [2.495e-03,2.507e-03] | 2.525e-03 [2.511e-03,2.537e-03] |
| base_seed0830_boxA | 12000 | 0.9999930555555555 | 0.999208 | 1.0000/1.0000 | 8.711e-04 [8.535e-04,8.899e-04] | 8.177e-04 [7.964e-04,8.390e-04] |
| base_seed0831_boxB | 12000 | 1.0 (exact) | 1.0 (exact) | 1.0000/1.0000 | 1.799e-03 [1.788e-03,1.810e-03] | 1.806e-03 [1.791e-03,1.821e-03] |
| base_seed0832_boxB | 12000 | 1.0 (exact) | 1.0 (exact) | 1.0000/1.0000 | 1.194e-03 [1.176e-03,1.214e-03] | 1.190e-03 [1.171e-03,1.211e-03] |
| base_seed26 | 12000 | 1.0 (exact) | 1.0 (exact) | 1.0000/1.0000 | 1.803e-03 [1.793e-03,1.814e-03] | 1.784e-03 [1.769e-03,1.798e-03] |
| base_seed27_boxA | 12000 | 1.0 (exact) | 0.999988 | 1.0000/1.0000 | 1.057e-03 [1.041e-03,1.074e-03] | 1.038e-03 [1.020e-03,1.057e-03] |

AUROC >= 0.9992 in all 16 session x seed cells; exactly 1.0 in 13 of 16 (stored values for
the rest: seed0830 d2 0.9999930555555555, seed0830 v10 0.999208, seed27 v10 0.999988).
Paired fraction 1.0000 in 16/16. The apparent "bimodal convergence" of v2 was an evaluation
artifact of mixed checkpoints: the two seeds that sat near 0.52 at step 10000 (seed27,
seed0832) reach >= 0.999988 at the declared step 12000. The transition is sharp in the final
2000 steps; no failed-convergence claim survives.

## 2. Paired fraction and pooled AUROC must be reported together

At step 10000 two seeds showed paired 1.0000 with pooled AUROC ~0.52: a small but perfectly
consistent within-row margin swamped by row-to-row difficulty variation. That state is real
and instructive (neither statistic alone is honest), and it vanished by step 12000.

## Per-offset profile

Wrong-row offsets are -2, +2, -15, +15 and +30. Per-offset AUROCs are flat within each seed,
to the third decimal, at whatever level that seed reached.

The near-offset result shows that the frozen scorer separates matched from wrong-row conditioning even at ±2. It does not identify the source of that separation or exclude a frame-synchronous, pipeline, session, or time-correlated cue. This is conditioning discrimination, not realness or liveness.

XOF avalanche makes wrong-row patterns unrelated, but it does not identify what the scorer reads or exclude a frame-synchronous, pipeline, session or time-correlated cue. The measured result is conditioning discrimination only.

Stated carefully, because flatness alone is weak evidence: a flat profile is also what a
non-discriminating model produces, which is why the weak seeds are flat at 0.52. The
argument rests specifically on the strong seeds achieving 1.000 at ±2, not on flatness by
itself.

## Limitations

Uncropped ARM-C only; this note says nothing about the cropped ARM-A arms. Two sessions, D2
with 1200 evaluation rows and V10 with 500; the august session is train-only and absent from
the reported held-out evaluation. The evaluator applies the published statistics and the
frozen one-stream noise rule; its statistics were independently recomputed from the raw
scores, but score GENERATION (model forwards, loaders, q_sample) remains the trainer's code
path, and an evaluator fully reimplemented from the written spec has not been done. The
discriminated signal may include any frame-synchronous cue correlated with row alignment;
label/time aliasing is not excluded by this design. Models are budget-limited at 12000 steps
(see section 6). Training data is owner-trusted.

## 5. Evaluator falsification — three executions, deterministic, PASSES

Tests on the base run at step 12000 (`bin/falsify_eval.py`, sha `bec430f4...`): T1a (correct
condition scored first and last in one call) 20/20 bit-identical; T1b (same wrong condition
duplicated at two positions) 20/20 bit-identical; T3 (deranged conditioning, +613) collapses
the paired fraction from 1.0000 to ~0.6 against chance 0.5. Two sha-bound executions on the
same checkpoint bytes (`03dd6caf...`) agree EXACTLY (deranged 37/60 = 0.6167 twice), so the
harness is deterministic across processes on fixed bytes. The original execution recorded no
checkpoint hash, reported 32/60 = 0.5333, and is retained as an unbound observation. The
invariant is TRUE = 1.0000 plus collapse under derangement, satisfied in all three.

## 6. The 50,000-step run

At issue time a 50,000-step run was in flight; this note contains no terminal record and makes no long-horizon claim.

## Log

- 3.3 (2026-09-09, BOSUN) — authorship line, 9 September 2026.
- 3.2 (2026-09-09, BOSUN) — title revision, 9 September 2026.
- 3.1 (2026-09-06, BOSUN) — title given its paper form; no other change.
- 3.0 (2026-08-31, BOSUN) — SETTLED. Homogeneous re-evaluation of all eight seeds at
  the declared step 12000; Sol audit v1 BLOCK -> v2 BLOCK(4) -> v3 BLOCK(4) -> v4 PASS
  (ultra). Corrections credited to Sol along the way: the withdrawn table's weak seeds were
  seed27_boxA and seed0832_boxB (v2's prose was right, an interim claim draft said
  seed26 and was wrong); run_seeds*.sh are evaluation runners, so from-scratch provenance is
  data-borne (all eight histories open at step 50, loss ~0.987, full files sha-bound in the
  audit bundle); full-precision AUROCs quoted, 0.99999x never printed as 1.0000; falsify
  determinism resolved by two agreeing sha-bound runs, GPU-nondeterminism conjecture
  withdrawn. v2 section-1 table (mixed checkpoints) superseded.
- 2.0 (2026-08-30, BOSUN) — Sol returned BLOCK. Section 1's seed table WITHDRAWN for
  mixed checkpoints (six at step 10000, two at 12000, declared horizon 12000, both weak seeds
  in the 10000 group). The "6 of 8 convergence" headline and the claim that this line does not
  inherit the pose line's confound are both withdrawn: a frame-synchronous cue survives the
  flat per-offset argument exactly. Added section 5, the evaluator falsification tests, which
  pass, and section 6, the in-flight 50k run.
- 1.0 (2026-08-30, BOSUN) — first issue, all eight seeds under the corrected protocol.
  Held as draft pending Sol audit.
