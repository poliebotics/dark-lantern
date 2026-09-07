---
version: 1.2
date: 2026-09-06
status: public extract of a development-data arithmetic fixture; revalidated 6 September 2026
author: BOSUN for Cathal Ryan Hynes
---

# Two Proofs, One Commitment: conditional micro-PLONK proofs of a frozen discriminator margin and a fixed-noise residual inequality over one committed tensor collection (23 August 2026, revalidated 6 September 2026)

Two verified PLONK proofs establish knowledge of the same committed 224-byte collection of derived 4×4 camera and emission tensors satisfying a frozen bilinear aggregate-score inequality and a frozen, fixed-noise t=150 conditional epsilon-residual aggregate inequality.

This is a development-data arithmetic fixture. Its relevance is implementation feasibility for frozen conditional computation
over shared hidden inputs inside a zero-knowledge proof. It does not prove raw-row membership, preprocessing, the full
diffusion sampler, the Phase G model, or any joined drand, BLAKE3 or Zcash statement. The rows are development data and the
tiny models were fitted on the same 712-row take; nothing here is held-out empirical evidence, and nothing here establishes
pose, liveness, identity, physical causation, sensor origin or reality. The margin ≥ 1 test is an arithmetic fixture predicate,
not a calibrated security threshold. The recorded row lineage and preprocessing checks are host-side replay evidence; the
circuits bind the supplied derived tensors through their shared commitment. Public identities and scores are disclosed in the
bundled JSON (`proof_receipt.public.json`, `discriminator/public.json`, `diffusion/public.json`, `MARGINS.json`); zero knowledge
hides the tensors and the commitment nonce, not the public signals. The tensor commitment is hiding only while its fresh private
nonce remains secret; this package makes no claim of everlasting secrecy. The runner requested operating-system entropy for that
nonce, but the entropy source was not independently witnessed, and differing proof bytes alone do not establish entropy quality.

## What is proved, exactly

Both proofs share one Poseidon commitment (`7062591557685344070810353090511299431417575682301226554859736612782971088205`), one
model tag and one context value. The hidden inputs are two 4x4x4 camera tensors, two 3x4x4 emission tensors and a 128-bit
nonce. The discriminator circuit exposes four bilinear arm scores and requires the aggregate difference `(tt + uu) - (tu + ut)`
to be at least one. The diffusion circuit exposes four epsilon-residuals for one fixed timestep and fixed in-circuit noise and
requires the aggregate `crossed - matched` residual difference to be at least one. Curve BN254, PLONK via snarkjs 0.7.6,
circuits compiled with Circom 2.2.3 at default optimisation, ceremony file `powersOfTau28_hez_final_15.ptau` (SHA-256 in
`PINS.json`).

## The limitation that must travel with the result

Each aggregate passes while one of its two directions fails. Recomputed from the public signals (`MARGINS.json`):

| predicate | first direction | second direction | aggregate |
|---|---:|---:|---:|
| discriminator, matched score minus crossed score | tt - tu = -374,704 | uu - ut = +468,684 | +93,980 |
| diffusion, crossed residual minus matched residual | tu - tt = -49,565,405,256 | ut - uu = +493,497,184,430 | +443,931,779,174 |

So neither proof shows that both cameras prefer their own emissions. Camera t's comparison favours the wrong emission under
both predicates; the aggregate passes because camera u's margin is larger. This is the controlled counterexample the programme
recorded on 24 August, not a successful two-sided verifier. The historical development-control table in the original note
(seven offsets, one shuffled fit per lane) is methodology, not an independent result, and is not restated here as evidence.

## Revalidation of 6 September 2026 (`CHECKS.json`)

All four retained proofs (original and repeat per circuit) verify against the retained verification keys; the repeated public
signals are identical and the proof bytes differ; the public signals equal the receipt in the declared order; both retained
malformed proofs and both retained tampered-public files reject; all 20 single-public-field mutations (9 discriminator, 11
diffusion; each value plus one modulo the field) reject; both proofs carry the same commitment, model tag and context; the
aggregates recompute to the public values; a synthetic zero-margin witness (all-zero tensors, nonce 0, the receipt context, the
fixed diffusion noise unchanged) is rejected by each circuit at its positivity constraint (`ZERO_MARGIN_TESTS.json`); the
retained positive witness-check logs report only the original witnesses' correctness; the receipt, training-result and
build-manifest hashes match the record; every receipt artefact matches its recorded size and SHA-256. No proof was regenerated
and no source recordings, private inputs or witnesses were read during revalidation.

## Contents and verification

`discriminator/` and `diffusion/`: circuit source, verification key, proof and public signals (original and repeat), the
retained malformed proof and tampered-public file, R1CS, symbol map, wasm with its witness generator, retained build and
verification logs. `proof_receipt.public.json`, `proof_build_manifest.json` and `training_result.json` are the 23 August records
with the build workspace's absolute paths reduced to relative form (`PINS.json` records the rule); the historical paths and
hashes inside those records describe the original source artefacts, while `SHA256SUMS` describes the shipped bytes (the
historical `build/<lane>/...` paths are not package paths). The two proving keys and the ceremony file are pinned by SHA-256 in
`PINS.json` and not shipped; verification needs only the verification keys, public signals and proofs. `verify.sh` checks the
manifest, the snarkjs version, the pinned keys, the four proofs, the four negative artefacts (a proof-rejection reason is
required), all 20 mutations, the shared public values, the margins and, where node can run the shipped wasm, the two synthetic
zero-margin rejections; run it from this directory as `SNARKJS=/path/to/node_modules/.bin/snarkjs bash verify.sh`. `SHA256SUMS`
covers every other package file.

## Log

- 1.2 (2026-09-06, BOSUN) — title given its paper form; no other change.
- 1.1 (2026-09-06, BOSUN) — after Astra's audit of the first extract: registered sentence restored verbatim; fixture, lineage,
  nonce-hiding and entropy limitations stated; four negative artefacts named; synthetic zero-margin witness tests added and
  recorded; complete check record shipped; path-reduction and manifest wording corrected; verifier hardened.
- 1.0 (2026-09-06, BOSUN) — extract built after GPT-6 Astra's review of the held negatives (N5-EXTRACT-v1): a genuine
  narrow positive, with the failed direction disclosed; the diffusion-verifier scientific claim stays held.
