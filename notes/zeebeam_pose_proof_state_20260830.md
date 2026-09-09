---
version: 1.3
date: 2026-09-09
status: historical-cropped-proof-state
author: Cathal Ryan Hynes (author of record); drafted with BOSUN, the project's automated research assistant
---

# Proof of Pose: what exists, what it proves, and what it does not

Written because the principal asked, on 2026-08-30, whether we are still doing proof of pose. We
are, and most of it is already done. This note states the artifact, its exact claim
ceiling and the filed errata that bounds its tamper claim. A section that recorded a withdrawn line of
my own work is held from the public record (section 5).

## 1. The artifact exists

`[machine path redacted]`,
2,184 bytes, sha256 `762f91c0016f5746769292c2f9045ca491ace3c0c7920bcfa585cd191a7ac53e`,
frozen 2026-08-24 at about 16:05 UTC as PROOF 4. It is one SP1 6.4.0 Groth16
zero-knowledge proof. Guest ELF sha256
`9c5f53522c588024c3c20068f49958e31fa0192d7647e9443f75dc25e8487525`, 236,760 bytes,
reproduced on the box from locked source. Frozen model blob
`c1f16af543f1140dc98944c0343955603fc38f25519784a33c8ff7c34f468d68`, 13,312 bytes,
hash-asserted inside the guest.

The guest takes a private preprocessed camera tensor `uint8[4,256,256]` and sixteen private
emission leaf sibling hashes, recomputes the camera leaves to produce the public typed pair
root, performs an exact 8x8 ties-to-even reduction (this is where "r32" comes from: 256/8 =
32), runs the frozen integer model, and commits 490 public bytes including the typed context
digest, the typed pair root, eleven integer logits, the first-max verdict, the saturation
count, and the model and reduction bindings.

Frozen exemplar is development row 52 of the August take. Public typed pair root
`efd35d054df639c3b07acff6ebab5d2ebec59a85ed0dcde5c0e99aa95006d395`, verdict class 1,
saturation count 0.

## 2. The claim ceiling, verbatim from the handoff

"A verified proof establishes knowledge of private, already-preprocessed camera pixels and
emission leaf hashes consistent with the public typed pair root, plus the exact frozen
model's logits and verdict over those camera pixels. It does not establish raw sensor
origin, preprocessing correctness, row or session membership, capture time, chronology,
physical pose ground truth, or liveness. The model verdict is evidence about committed
pixels, not proof of physical reality."

So it is a proof of computational integrity over committed pixels. It is not a proof that a
human held a pose. The name "proof of pose" is a convenient label and it overstates the
relation if quoted without this paragraph.

## 3. Two things that must travel with any presentation

The frozen exemplar row 52 is one of the four rows, out of 116 evaluation rows, where the
model verdict (class 1) DISAGREES with the BOSUN-authored cue assignment (class 0). The
narrative says to state this everywhere, and it is right to: the proof binds the verdict
whatever the verdict is, and no reader may be allowed to assume verdict equals label. This
also explains the "112/116" figure that has been circulating. It is model-versus-annotation
agreement on the evaluation rows, not a classifier accuracy in the ordinary sense.

`ERRATA.md`, filed 2026-08-24 at 18:40Z, materially bounds the tamper claim. The single-bit
flip that was REJECTED was a flip of the final byte of the extracted on-chain proof, in
memory. Single-bit flips of the proof FILE were measured ACCEPTED, exit 0, on the same
verifier binary, because the shipped envelope carries a second hex blob at offsets 991..1640
that verification never consumes. Any tamper-evidence sentence must carry that scope.

The underlying science has a one-subject, one-room, one-rig, one-occurrence-per-cue
confound. That bounds the scientific claim, not the cryptographic one.

## 4. The classifier's own declared ceiling

`camera_pose_resolution_ladder_candidate.py` declares, in source, `reality_claim: False`,
`proof: False`, `blind_pose_truth: False`, `verification_result: False`,
`cue_aware_annotation: True`, and
`single_take_subject_room_camera_time_background_confound: True`. Its docstring calls it a
single-take development diagnostic. The eleven classes are human body poses: neutral,
superman, letter_y, letter_m, letter_c, letter_a, letter_t, letter_x, hands_up, point_left,
point_right.

What would raise this from proof-of-computation toward something closer to proof-of-pose is
a blind, multi-subject, multi-room, multi-rig evaluation set. That is a capture problem, not
a cryptography problem, and no amount of proving work substitutes for it.

## 5. Held by publication edit

This section recorded a withdrawn line of BOSUN's own work (a discriminator experiment declared void, not evidence). It
is held from the public record under the publication rule of 6 September 2026 (positive, patent-supporting results only;
see the 1.1 Log entry). The artifact, claim ceiling, errata and limits in sections 1 to 4 are unaffected. One sourced fact
from the held section is kept: `configs/preprocess_v1.candidate.json` gives `camera_crop` x0=782, y0=340, 1024x1024
applied to the packed CFA plane 2660x2300, 17.1 percent of that area.

## 6. The no-crop DIFFUSION line, which is sound, is unaffected

The progress report formerly here is superseded by `zeebeam_nocrop_diffusion_8seed_20260830.md` v3.0: all eight seeds were evaluated at step 12,000. It is an ML conditioning result, not a proof, realness, or liveness claim.

## Log

- 1.3 (2026-09-09, BOSUN) — authorship line, 9 September 2026.
- 1.2 (2026-09-06, BOSUN) — title given its paper form; no other change.
- 1.1 (2026-09-06, BOSUN) — publication edit for the Dark Lantern record under the 6 September rule (GPT-6 Astra's
  audit of the ninth tree): section 5, a withdrawn discriminator line of BOSUN's (void, not evidence), is held from the
  public record and replaced by a notice; the introduction adjusted; the sourced crop-geometry fact retained. Sections
  1 to 4 and 6 unchanged.
- 1.0 (2026-08-30, BOSUN) — first issue. Written in response to the principal's question. Facts
  read from the artifacts and source named above rather than from memory; the pose proof
  sha, guest ELF sha, model blob sha, claim-ceiling text and errata scope are quoted from
  `RECEIPT_NARRATIVE.md` and `ERRATA.md` in `proofs/pose_verdict_20260824/`.
