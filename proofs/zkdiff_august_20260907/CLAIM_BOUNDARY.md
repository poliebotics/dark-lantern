---
version: 1.1
date: 2026-09-08
status: the claim boundary of this package, fixed before the proofs were made; the three quoted paragraphs are verbatim; the disclosure's quick-screen sentence corrected and the external referents pointed to the glossary
author: BOSUN for Cathal Ryan Hynes
---

# Claim boundary

The three paragraphs below are the boundary of what this package claims. They were written by the programme's second-model
auditor (GPT-6 Astra, round 5, finding 11) after it had read the complete guest, the oracle and the calibration record, and
they are reproduced verbatim from `source/FULL_GUEST.md` section 11.1. Every other document in this directory is read
under them, and a sentence elsewhere that seems to say more than they do is to be read as saying no more.

> We publish one independently verified Groth16 proof for each August target row 600–711, including every signed outcome and any clipping. Each proof establishes execution binding of an integer diffusion evaluator adapted from the frozen ARM-C protocol: whole-frame preprocessing of a committed raw frame, authenticated conditioning from the declared row states, and two evaluations at timestep 150 sharing one noisy frame and one hash-bound normative noise target. The comparison uses the published single-offset rule, including its boundary mirrors.
>
> Model weights were trained on August rows 0–599 plus the d2/v10 training blocks. August rows 600–711 were held out from weight training; quantisation calibration used seven targets from this set and their own/+15 hints, listed in the release manifest. The repeatedly consulted d2/v10 evaluation blocks are development validation.
>
> These proofs establish the specified integer computations and bindings. They establish no physical-capture, realness, liveness, illumination-causality, adversarial-resistance or unseen-session-generalisation claim. They do not reproduce the original published checkpoint, five-offset aggregate, eight-seed AUROC or full diffusion sampling. Noise generation remains external provenance; the proof binds the normative bytes and computes forward noising.

## The calibration disclosure, in full

The fixed-point scales of the integer network were calibrated on fifteen rows, each under two conditionings (its own
emission and the emission of the row fifteen places later): protocol rows d2 1328, 1528, 2866, 3066, 4404, 4604 and
v10 1260, 2495, and August targets 600, 616, 632, 648, 664, 680 and 696. Seven raw August targets and fourteen August
conditioning identities (600, 615, 616, 631, 632, 647, 648, 663, 664, 679, 680, 695, 696, 711) therefore influenced the
integer scales. August rows 600 to 711 were held out from weight training (`august_train_rows 600` in the trainer
arguments recorded in the checkpoint); four of them (606, 630, 654 and 678) were among the 28 August rows the trainer's own
quick screen scored during training, the other 24 screen rows being training rows below 600 (`RESULTS.md` section 1,
`FAQ.md` 23; an earlier revision of this paragraph said the screen consulted the held-out rows without naming them); they were
not untouched by calibration and must not be described as an untouched test set. The proof set remains the complete 112
rows, disclosed as such. The "release manifest" the second paragraph names is `PINS.json` (`model.calibration_rows`) and
`oracle/final/constants_int16.json` (`calib_rows`, `calib_maxabs`). Sources: `oracle/final/README_FINAL.md` section 7b,
`oracle/final/FREEZE_SUMMARY.md` "Calibration disclosure", `source/FULL_GUEST.md` section 11.1.

## Where this boundary comes from

It is the ZeeBeam manuscript's boundary applied to a new learned component. The manuscript's Section 3.4 states that a
proof establishes execution binding, that the published outputs are exactly what the pinned functions produce on the
bytes whose hashes sit in the committed chain, and that any physical reading needs assumptions no proof supplies; its
Section 8.3 states that a reader may disregard a learned component's semantic label while retaining the execution claim.
The programme's engineering review of this demonstration (round 1) fixed the publishable sentence as "this establishes
execution binding" and listed what may not be claimed: proof of physical capture, illumination causality, realness,
liveness, adversarial resistance, unseen-take generalisation, or a complete diffusion sampling trajectory; round 2 added
that the new model does not inherit the eight-seed AUROC and that the d2/v10 blocks, excluded from training but used
repeatedly for candidate selection, are development validation. The proofs also do not authenticate the raw frame's
origin in a camera, do not bind the noise tensor to any random-number generator (its bytes are normative and hash-bound),
and say nothing about the sealed 288-row verification take, which this work never touched. The external referents of the
three paragraphs (the eight-seed AUROC, the five-offset aggregate, the original published checkpoint, the coupling packet,
the sealed take) are defined in `GLOSSARY.md` and `FAQ.md` 20.

## Sources

`source/FULL_GUEST.md` section 11.1 (the verbatim paragraphs and the calibration preamble); `oracle/final/README_FINAL.md`
sections 6 and 7b; `AUDIT_TRAIL.md` (rounds 1, 2 and 5); the ZeeBeam manuscript *ZeeBeam: The Zero-Knowledge Beam* v3.20,
Sections 3.4 and 8.3 (github.com/poliebotics/zeebeam, `paper/zeebeam.md`).

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-07 | BOSUN | First version, drafted before the proof batch; the quoted paragraphs are Astra round 5 finding 11 verbatim. |
| 1.1 | 2026-09-08 | BOSUN | Agent audits round 1: the quick screen's rows named (four proof rows, not the whole held-out set); external referents pointed to the glossary. The quoted paragraphs are unchanged. |
