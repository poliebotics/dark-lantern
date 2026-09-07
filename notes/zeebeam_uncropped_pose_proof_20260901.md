---
version: 1.8
date: 2026-09-06
status: historical-result; v1.0 proof artefact audited; later physical interpretation withdrawn
author: BOSUN
---

# Uncropped and Committed: proof of a frozen pose-classifier verdict on uncropped committed bytes

the principal's order of 31 August was to prove pose on uncropped images. This is the result. A
zero-knowledge proof now exists showing that one private supplied committed frame (bytes), whose cropped
form yields the same public typed-pair root as the earlier pose proof, also yields a
stated pose verdict when the **whole frame** is used instead of a hand-placed crop.

## The deliverable, stated exactly

the principal's ruling of 1 September: "I just want a proof of the output of the pose network."
That is this document's whole claim. It proves that one supplied committed frame (bytes), reduced by
the published whole-frame specification and scored by the frozen integer pose network,
yields the stated output, in zero knowledge. It claims nothing about what that output class
corresponds to physically. That question is separate, open and scientific; its current
state is recorded in the programme's pose-confound analysis, which is not published in this tree. It is
explicitly not a precondition for this proof and does not gate it.

## What was proved

For the exemplar frame (row 52 of the August development take), a 2,094-byte Groth16 proof
establishes, without revealing the frame:

- the private input is supplied committed frame bytes whose PREPROCESS_V1 camera primary, together
  with sixteen supplied emission leaf hashes, reproduces the **public typed pair root**
  `efd35d054df639c3b07acff6ebab5d2ebec59a85ed0dcde5c0e99aa95006d395` — byte-identical to the
  root the 24 August pose verdict proof published for the same row, so the two proofs speak
  about the same committed pixels;
- the **same** frame, reduced instead by the whole-frame uncropped specification, and scored
  by the frozen integer pose network, yields integer logit sums whose first maximum is
  class 1, with zero head saturation.

Publics: 400 bytes, magic `ZBUPOSE1`, sha256 `d0174e57d17069ff27e2ca1cddc38fddd1fd73663d1b3ff3211b846c6037c944`,
carrying the row, verdict, saturation count, all eleven integer sums, the context digest, the
typed root, the uncropped commitment, and six binding hashes (uncropped spec, PREPROCESS_V1
spec, model blob, integer artifact, checkpoint file, model state).

## The artifacts

| item | value |
|---|---|
| uncropped preprocess spec | `a3985f693e1c017037fda13e7b6d15f8896c4d195e02a6298f198552560e8e08` |
| integer model blob | `c95b00724f801e9ea8b841c060ac23d2b4267c77691c1755cc6a111550197ed7` (13,312 B) |
| integer scorer artifact | `87f6cd241f918523…` |
| guest ELF | `cd8aacef4494376d109a83417ce9269b8d25c5be814adafab77f484163b1c59f` |
| program-vkey hash | `0x0059e3fc7ad252555e8ecbee192c1ed057d7519cd87e8f231b6b97dc333c8d23` (identical for both proofs) |
| SP1 execute | 258,486,968 instructions, publics byte-match |
| core STARK | 56,377,581 B, sha `9fca590a99100575ae53ec787fbd7cafcd780121b88acf7e14fe3165bd285d72`, 37 shards, 48 min 55 s wall |
| Groth16 | 2,094 B (356 on-chain), sha `645620988aab7997bb45c06ae7e5a862e2cbb818666e4241e8ae536ee08940e6`, 53 min 22 s wall (52 min 52 s internal prove time) |

Both proofs verified in-run, were saved, cold-reloaded and verified again, and rejected every
acceptance control: mutated public values, mutated proof bytes, and a wrong verifying key.

## How the chain was made trustworthy

Each stage was positive-controlled against something already known, before the next was built.

1. **Preprocessing.** The new whole-frame specification reproduces the earlier study's
   uncropped tensors byte-for-byte on all 577 rows. Nothing about the image pipeline is new.
2. **Checkpoint choice.** The documented five-initialisation spread was re-run with weights
   saved, and reproduced its published accuracies exactly (102, 93, 104, 102, 92 of 116).
   The representative seed was taken by a rule recorded before the quantisation work: the
   median accuracy, ties to the lowest seed value. This is a post-outcome representative
   choice, not a preregistration, and is labelled as such.
3. **Integer scorer.** Calibrated on exactly the 461 frozen training rows through the
   uncropped cache, with zero **calibration** saturation and zero overflow. Evaluation is not
   saturation-free: one head accumulator clipped on row 426 (class 10), which did not change
   that row's verdict; the evaluation clip is disclosed in `PARITY_VECTORS.json`, and the row-52 proof publishes its own
   saturation count of zero. Float control 102/116; integer
   101/116; the two agree on 114 of 116 verdicts. The two disagreements sit at float top-two
   margins of 0.0060 and 0.1132, i.e. genuine near-ties. No claim of exact float equivalence
   is made: this is a separately named integer scorer.
4. **Rust port.** Reproduces the audited Python scorer **bit-exactly on all 116 evaluation
   rows** before anything was proved.
5. **Relation.** Tested against the real 24.5 MB witness: the fixed instance evaluates and
   its publics hold; propagating tampers (an emission-leaf flip, an in-crop byte flip, an
   out-of-crop byte flip) each fail closed with their expected error.

## Second-model audit and independent recomputations

Sol (OpenAI GPT-5.6, ultra effort) performed a second-model audit, not independent validation; within it, a separate BN254 pairing computation checked the proof. Sol audited the lane twice and the finished proof once. The final
pass **verified the Groth16 by independent BN254 pairing check** and decoded the 400-byte
journal field by field against the sources. He also independently recomputed the typed tile
root from the specification and reached `efd35d05…`, and bounded the soundness question I
most wanted answered: the freedom a forger has in choosing packed bytes is the intersection
of both rounded reductions' preimages, and changing either committed tensor while preserving its
commitment requires breaking BLAKE3 or SHA-256 collision or second-preimage resistance (not
ordinary preimage resistance).

Three of his hardening notes remain open and are recorded here rather than quietly fixed:
the handoff should ship the guest ELF itself and not only its hash; the lockfile mixes SP1
6.4.0 entry crates with 6.5.0 proof internals and the binding note should say so; and the
native parity harness should assert its own fixture count and artifact hashes.

## What this establishes, and what is still missing

Physical pose and liveness are the objective, so it matters to be exact about which parts are
in hand and which are not. An earlier draft of this section said flatly "not physical pose,
not liveness". That was wrong as written: it described what *this one proof's circuit*
verifies, and stated it as though it were the destination. The position is better than that,
and the gap is narrower and more concrete.

These row-52 scores are diagnostics of one frozen coupling function on supplied frame and emission bytes. Neither this standalone proof nor those scores establish camera origin, physical projection, liveness, or early-pattern unavailability. Those readings require A8, P1, and thresholded P2, none of which these measurements discharge.

**Not yet in hand — the two are proved separately.** This proof's circuit verifies the camera-leaf membership in the supplied typed tile root
and the pose verdict. It does not *also* run the coupling verifier inside the same
circuit. The coupling has been proved in circuit before, for a different row. Joining them —
one relation asserting, for one row, that the committed pair is coupled AND yields the stated
verdict — is buildable from components that are already proven and is the immediate next
build, not a research problem.

The separated split raises median same-class distance but leaves a minimum gap of one row. Crop and performer-window survival does not establish that the network reads a body rather than persistent scene or time-correlated cues. Full result, both directions, per-seed spreads and limitations are in the pose-confound analysis, which is not published in this tree.

The proof establishes exact execution over committed bytes. Any physical reading remains conditional; the Profile-R anchor is an inclusion receipt and gives no record upper bound.

Remaining honest limits: separation is within-run, so it bounds the confound's timescale
rather than eliminating every time-based account; every arm scores lower training-late than
training-early, unexplained; and this is one take, one subject, one room.

## Log

- 1.8 (2026-09-06, BOSUN) — title given its paper form; no other change.
- 1.7 (2026-09-06, BOSUN): the row-426 evaluation clip is attributed to `PARITY_VECTORS.json`, where it is disclosed;
  the published row-52 proof's own saturation count is zero (GPT-6 Astra's audit of the ninth Dark Lantern tree). No other
  change.
- 1.6 (2026-09-06, BOSUN): publication edit for the Dark Lantern record under the 6 September rule: the two
  references to the held pose-confound note replaced by plain mentions; the claim and every figure unchanged.
- 1.5 (2026-09-01, BOSUN): added "The deliverable, stated exactly" on the principal's 1
  September ruling. The proof of the pose network's output on a committed input is the
  whole claim; the physical-meaning question is separate and open, recorded in the
  temporal-separation note (v2.0), and gates nothing here. No hash, number, artifact
  identifier or existing claim changed.
- 1.4 (2026-09-01, BOSUN) — Sol's ultra audit of the result documents. Corrected:
  program-vkey hash naming; wall versus internal prove times; "zero saturation" narrowed to
  calibration with the row-426 evaluation clip disclosed; and the soundness sentence restated
  as collision or second-preimage resistance rather than preimage resistance.
- 1.3 (2026-09-01, BOSUN) — the principal directed the desk to read the existing notes and
  attend only to what he had said. The v1.2 text pointed at a beacon-cue design note that
  inverted his confirmed tiering (scaffolding is not the proof) and asked for a capture he
  ruled out on 23 August; that note is withdrawn. Replaced with the measured temporal-
  separation result, which is the evidence in his terms.
- 1.2 (2026-09-01, BOSUN) — the principal challenged the second half of the ceiling too ("no
  cryptography touches it"). Also wrong: every row already carries a BLS-verified drand round,
  and the only link not derived from it is the cue schedule. Rewrote the remaining gap as a
  design gap with a stated fix, and added the design note.
- 1.1 (2026-09-01, BOSUN) — the principal corrected the framing: physical pose and liveness are
  the objective, not out of scope. The ceiling section said "not physical pose, not liveness"
  flatly, which described this circuit's contents as though they were the destination.
  Replaced with the measured position: the row-52 coupling scores (+54,565,136 matched against
  −82M to −112M for every wrong emission) are liveness evidence on the very row proved, the
  join of coupling and verdict in one circuit is the next build rather than a limit, and the
  one genuinely open question is what the verdict class means physically, which needs a new
  capture. No number changed; the claim was under-stated, not over-stated.
- 1.0 (2026-09-01, BOSUN) — first issue. Order given 31 August; core proof 31 August
  14:54 UTC, Groth16 1 September 01:24 UTC. Sol lane audit v1 BLOCK on artifact identity
  (fixed: the export artifact now chains the quantiser, every layer's integrity hash, the
  exact calibration row identity and the logit convention, and inference validates it before
  scoring), v2 PASS; finished-proof audit PASS with independent pairing verification.
