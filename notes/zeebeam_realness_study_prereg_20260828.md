---
version: 1.3
date: 2026-09-09
status: historical-frozen-preregistration; premise-corrected
author: Cathal Ryan Hynes (author of record); drafted with BOSUN, the project's automated research assistant (desk)
---

Execution deviated from this preregistration; the final realness study is exploratory (`zeebeam_realness_results_20260901.md`).

# Before We Looked: the ZeeBeam realness discriminator preregistration

Frozen BEFORE any outcome is inspected, per ULTRA_AUDIT_4 finding D1 and the owner-confirmed
framing (an August framing note, since withdrawn and not published in this tree). The claim this study measures: a
frozen neural-physical discriminator separates genuine time-chained ZeeBeam captures from
adaptive forgeries, with a reported error rate that is the strength of the evidence. This
document is the contract; results that deviate from it are exploratory, not confirmatory.

## Why this is not the conditioning result

The earlier record called the conditioning result AUROC 1.0; the final 144-value fixture gives 72/72 paired comparisons and pooled AUROC 0.9983. That result is `correct_vs_wrong_pattern` on a real frame: a CONDITIONING
discriminator. It does not test genuine-vs-forged imagery and supplies no realness FPR/FNR.
This study measures the different quantity.

## Discriminator (frozen before scoring)

- Input: a captured (or forged) time-chained sequence and its chain log (states, patterns).
- Physical feature vector, declared now, computed per frame and pooled over the sequence:
  (1) optical/sensor consistency of the frame under its declared emission `E_t = render(XOF(S_t))`;
  (2) frame-to-frame temporal coherence of that consistency along the chain;
  (3) cross-correlation of the frame's neural-physical statistics against a held-out bank of
  KNOWN-REAL captures. The scorer weights are frozen and hashed before any negative is scored.
- Aggregation: sequence-level score = declared pooling (median of per-frame consistency minus
  the wrong-arm mean), one number per sequence. No per-sequence tuning.

## Classes

- **Positive (genuine):** held-out real time-chained sequences. No-rig first pass uses the
  existing 22 Aug takes, held out by contiguous whole-subsequence blocks (never frames from a
  scored block leaking into the bank). LIMITATION, stated: one subject, one rig, one occasion,
  so the no-rig ROC is PRELIMINARY; the definitive corpus (R1, rig) needs multiple independent
  takes for whole-take holdout.
- **Negative (adaptive forgery), box-generated, attacker knows the published protocol and
  chooses patterns.** Declared attack classes, each scored separately:
  1. naive per-frame synthesis to the pattern (no temporal model);
  2. temporally-coherent generative sequence conditioned on the previous FORGED frame;
  3. replay/splice of real frames under mismatched patterns;
  4. optimise-against-the-scorer white-box attempt (the scorer is public in the release).

## Protocol (frozen)

- Holdout unit: whole contiguous subsequence (never single frames).
- Seeds: >= 3 independent model/eval seeds and >= 3 forger seeds; report all.
- Metric: sequence-level ROC and AUROC with a sequence-CLUSTERED bootstrap CI; FPR and FNR at
  a threshold frozen in this document (Youden-J on a declared calibration split disjoint from
  test); reported per attack class AND pooled.
- Reproducibility: raw per-sequence scores published; scorer + generators + environment + seeds
  in the stranger-verifiable release so a hostile reviewer recomputes the ROC from the frames.

## What the no-rig version can and cannot claim

- CAN: a preliminary, multi-seed, whole-subsequence real-vs-adaptive-forgery ROC on the
  existing take, with box-generated attacks across the four classes; honest error rates with
  the one-occasion limitation stated.
- CANNOT: whole-TAKE holdout across independent occasions, subject/session generalisation, or
  any "definitive" realness claim. Those need the R1 rig corpus.

## Execution (box, no rig)

1. Build and hash the frozen scorer from the released feature vector.
2. Build the four forgery generators on the idle GPUs; hash each.
3. Score positives + all negatives; emit raw scores, ROC/AUROC/CI, FPR/FNR by class.
4. Second-model audit the pipeline for leakage (bank/test disjoint, no per-sequence tuning) BEFORE
   reading the ROC.

## Log
- 1.3 (2026-09-09, BOSUN) — authorship line, 9 September 2026.
- 1.2 (2026-09-06, BOSUN) — title given its paper form; no other change.
- 1.1, 2026-09-06, BOSUN. Publication edit under the 6 September rule: the reference to the withdrawn August framing
  note replaced by a plain mention; content otherwise unchanged.
- 1.0, 2026-08-28, BOSUN. Frozen at the desk on the owner's order to do all non-rig work
  that improves the paper. Related: [[zeebeam-publishability]], realness framing doc,
  ULTRA_AUDIT_4_REFRAMED.
