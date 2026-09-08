---
version: 1.6
date: 2026-09-08
status: proof package of the zero-knowledge diffusion demonstration; one Groth16 proof per August row 600 to 711; results rendered from the collection; primer, glossary, FAQ, offline capsule, published frames and audit texts added after the outside-agent readability audits and the principal's publication decision
author: BOSUN for Cathal Ryan Hynes
---

# A Tale of Two Conditionings: one Groth16 proof per held-out August row of an integer diffusion evaluator run on the whole frame under its own emission and a declared wrong one

<!-- BATCH_COUNTS_BEGIN -->
112 proofs, one per row 600 to 711, every one verified and accepted under the frozen identities: 112 positive, 0 zero and 0 negative signed outcomes; 0 rows with a nonzero clip count.
<!-- BATCH_COUNTS_END -->

For each of the 112 rows 600 to 711 of the 712-row projector-camera session recorded on 22 August 2026 (the session
whose anchored rows the ZeeBeam release proves), one SP1 6.4.0 Groth16 proof establishes that an integer diffusion
denoiser, adapted from the frozen ARM-C protocol and run in exact fixed point, produced the published residual sums on the
whole sensor frame of that row: the raw frame hashed inside the proof and opened to the committed session tree, its
chain state re-derived from an authenticated predecessor under two verified drand quicknet beacons, both emission
patterns re-rendered from their chain states, the frame reduced to the network's input without any crop, noised at
timestep 150 with a hash-bound normative noise tensor, and evaluated twice on the same noised frame: once under the
row's own emission and once under the emission of a declared wrong row chosen by a published rule. The proof publishes
both residual sums, their signed difference and every binding digest in a 752-byte statement that carries no pixels; the
raw Groth16 proof is 356 bytes. What that establishes, and what it does not, is fixed in `CLAIM_BOUNDARY.md`, whose three
paragraphs govern every sentence in this directory.

**Two parts.** This publication is the repository package you are reading and a data-layer bundle at
`https://data.truthbeam.com/results/zkdiff_august_20260907/v1/` (bucket `truthbeam`): the 112 raw frames (`FRAMES.md`), the
large oracle arrays and the August tensors (`LARGE_FILES.md`, `LARGE_FILES_SHA256SUMS`), the node's proof collection
(`node_runs/`) and the offline build kit (`build_kit/`), about 12.7 GB. Most of what is deliberately elsewhere is named here by
path and SHA-256 (`LARGE_FILES_SHA256SUMS`, `FRAMES.md`, the kit manifest's digest in `PINS.json`); the node's collection under
`node_runs/` and the bundle's own README are inventoried only by the bundle's `_control/MANIFEST.jsonl`, whose digest the root
`README.md` pins. A reader without the network knows exactly what is missing; a reader with it checks every fetched byte. The
bundle's controls are `_control/MANIFEST.jsonl`, `_control/SHA256SUMS` and `_control/RELEASE.json`; their digests
are fixed in the Dark Lantern repository's root `README.md` by the commit that adds this package (this file cannot carry
them, being itself copied into the bundle). The proofs, statements, receipts, source, model, capsule and tools are all here.

## Primer, for a reader with no context

**The recording.** A projector (1,920 x 1,080, RGB) lights a scene and a 24.5-megapixel industrial camera (5,320 x 4,600
pixels, 8-bit Bayer RGGB, driven through Aravis) photographs it, about two and a half times a second. One photograph is a
**row**; the session of 22 August 2026 (identifier `ZEEBEAM_MAINNET_BLOCKING_TRAINING_300S_20260822_001`, the recorder's
label) ran about 300 seconds and produced 712 rows, numbered 0 to 711. Each row's frame is 24,472,000 bytes. The frames of rows 600 to 711 are
published on the data layer (`FRAMES.md`). The August frames depict a masked participant in a recognisable indoor setting. Camera-derived tensors retain images of participants and their surroundings, including earlier-session examples. These materials are not anonymised; identity may be inferred from clothing, movement or context. Two earlier sessions of the same kind, **d2** (5,992 rows) and **v10** (3,743 rows), the programme's public
development sessions, trained and validated the model.

**The chain and the pattern.** Every row t has a 32-byte state `S_t`. `S_0` is a seed the recorder chose. After each frame is
captured, the next state is a BLAKE3 hash of the current state, the frame's own hash, a 28-byte capture record and the
current round of **drand quicknet**, a public randomness beacon that publishes a new BLS-signed value every 3 seconds; the
value the chain folds in is the SHA-256 of that signature. The **emission pattern** `E_t` the projector shows for row t is
computed from `S_t` alone: three seeds, one per colour, are hashed from the state, each is expanded by BLAKE3's extendable
output into 43,110 bytes, sliced into four octave grids and rendered by fixed-point bilinear upsampling into the 1,920 x 1,080
image. So the pattern lit at row t depends on the previous frame and on a beacon round that did not exist before its time.
The chain log (`source/vectors_relation/august/chain_log.csv`) records all of this per row; a Merkle tree over the 712 rows
(the **session tree**) has a root that every proof carries. Because rows are 400 ms apart and rounds 3 s apart, most
consecutive rows share one beacon round (`STATEMENT.md` section 1a says exactly what that means for each proof).

**The model.** **ARM-C** is the third arm (arm C; not an acronym) of the programme's conditional-diffusion study: a small
denoising U-Net that takes the whole frame reduced to a 96 x 112 grid (four colour planes, no crop) and, as its conditioning
("hint"), the pattern of a row reduced to the same grid, and predicts the Gaussian noise that was added to the frame. The
**frozen ARM-C protocol** is that study's fixed evaluation recipe (timestep 150, five wrong-row offsets, a fixed noise seed,
AUROC and paired fraction). The model here was trained on the training blocks of d2 and v10 and on August rows 0 to 599, then
converted to exact integer arithmetic (the **int16 contract**) so that a Python oracle, native Rust and the zero-knowledge
virtual machine compute bit for bit the same thing. Rows 600 to 711 gave no gradient to training ("held out"), though seven of
them were used to calibrate the integer scales and four were among the rows a training-time screen scored, which is why they are
not called an untouched test set (`CLAIM_BOUNDARY.md`). The d2 and v10 evaluation blocks were scored repeatedly while choosing
the model and are therefore **development validation**, not a test set.

**The proof.** For each row r in 600 to 711, one Groth16 proof (356 bytes; SP1 zkVM) that the integer network, run inside the
proof on the whole frame of row r noised with a fixed noise tensor, produced two published residual sums: `R_correct` under
row r's own pattern and `R_wrong` under the pattern of a **wrong row** u chosen by a published rule (one of the five protocol
offsets, cycled by row, mirrored at the session's end), with the frame hashed inside the proof and opened to the session tree,
the chain state re-derived from the previous row's record and the verified beacons, both patterns re-rendered from their states,
and every input bound by a hash. `D = R_wrong - R_correct > 0` means the network predicted the noise better under the right
pattern. All 112 proofs verify, all 112 differences are positive, and no arithmetic saturated. That is the whole claim: a
specified computation on committed bytes. Nothing here says the scene was real, live, or lit by that pattern.

**Who did what.** "The principal" and "the owner" are Cathal Ryan Hynes (PolieBotics), who set the rules and takes every
publication step. "BOSUN" is the project's automated research assistant, a Claude-family language model running the project's
desk, which wrote the text and code of this package under the principal's direction and ran the machines; "the coordinator"
and "the operator" in copied records are BOSUN in two of its sessions. "Astra" is the second model (GPT-6) that audited the
work in <!--ai:total_word-->ten<!--/ai--> rounds (five before proving, one on the finished package, a privacy sweep and <!--ai:confirm_word-->three<!--/ai--> confirmation re-reads of the augmented and re-frozen package; the texts of <!--ai:pairs_word-->nine<!--/ai--> of them are in `audits/astra/`, the privacy sweep's by its verdict line); three further outside models read the package <!--ai:readings_word-->three<!--/ai--> times for readability (<!--ai:reports_word-->nine<!--/ai--> reports in `audits/agents/`). `GLOSSARY.md` defines every term;
`FAQ.md` answers those readers' questions; `HASHES.md` says of what each published hash is the hash.

**Where to start.** With nothing installed, on x86-64 Linux, trusting the shipped static binaries or rebuilding them first
(`capsule/README.md`): `bash capsule/verify_offline.sh` verifies all 112 proofs offline (about three and a half minutes on the
rehearsal machine), and `capsule/reexecute/reexecute_row.sh` recomputes a row from its raw frame (row 600's is shipped; every
row's is on the data layer). From an empty machine with the network: `replicate/replicate.sh all --no-prove` fetches and
hash-checks every toolchain, rebuilds the program to its pinned key, verifies every proof and re-executes row 600 from its
shipped frame (`replicate/README.md`); the offline build kit on the data layer does the same rebuild with no network
(`LARGE_FILES.md`, `VERIFY.md` section 2b). Everything in between is `VERIFY.md`.

## What is here

| path | what |
|---|---|
| `CLAIM_BOUNDARY.md` | the boundary of the claim, three paragraphs fixed by the second-model auditor before proving, and the calibration disclosure |
| `GLOSSARY.md`, `FAQ.md`, `HASHES.md` | every term defined; the outside readers' questions answered from the files; every published hash and what it is a hash of |
| `FRAMES.md` | the 112 raw frames of the proof rows on the data layer, with the digests the chain log, the statements and the receipts carry |
| `LICENSE` | the Dark Lantern Research and Private Use Licence 1.2, byte-identical to the repository's root `LICENSE` |
| `STATEMENT.md` | the statement each proof establishes: the 752-byte public layout, the witness, the fourteen legs of the relation, the preprocessing, the denoiser, the declared offset rule, the normative noise, the acceptance checks |
| `VERIFY.md` | how to verify one proof and all of them, decode a statement, rebuild the program and its key, and check every pinned identity |
| `RESULTS.md` | development validation of the model, the integer agreement, the guest's parity and negative controls, the proving cost, and the proof batch row by row |
| `AUDIT_TRAIL.md` | the <!--ai:total_word-->ten<!--/ai--> audit rounds (five before proving, one on the finished package, a privacy sweep and <!--ai:confirm_word-->three<!--/ai--> confirmation re-reads) and the <!--ai:readings_word-->three<!--/ai--> readings by three outside agents, with their verdict lines and what changed after each |
| `audits/` | the full texts: the Astra briefs and verdicts of rounds <!--ai:rounds_text-->1 to 6 and 8 to 10<!--/ai--> (`astra/`) and the <!--ai:reports_word-->nine<!--/ai--> outside-agent reports (`agents/`), redacted as `audits/README.md` states (the privacy sweep of round 7 by its verdict and dispositions in `AUDIT_TRAIL.md`) |
| `PINS.json` | every constant a verifier must pin: program key, ELF, circuit key, constants and spec digests, session, rule, per-row noise digests, toolchain, build records, model, oracle files, and (added when the batch landed) every proof's digests |
| `proofs/` | per row: `row_XXXXXX_groth16.bin` (the SP1 artifact, 2,444 to 2,447 bytes; the per-size counts are in `PINS.json` `batch.framed_proof_bytes_histogram`) and `row_XXXXXX_groth16_proof.bin` (the raw Groth16 proof, 356 bytes) |
| `public_values/` | per row: the 752-byte public statement, raw and as hex |
| `receipts/` | per row: the prover's receipt (schema `zbdiff-row-receipt/v3`), the ceremony manifest and the node's cold acceptance report; the development machine's own acceptance reports (`independent_verify/`); the eight per-GPU batch manifests with their GPU memory samples, GPU identities and launch-time input digests; the strict merge `BATCH_MANIFEST_merged.json`; the node's proof-level and witness-level controls; the launch schedule; `SHA256SUMS_RUNS` (the node's ledger over its complete collection, withheld logs included); `BATCH_SUMMARY.json`; `receipts/README.md` names what is here and what stayed on-box under the evidence allowlist; the text records carry the publication redaction rule (`receipts/REDACTION_LEDGER.tsv`) |
| `source/` | the frozen source of the program and its hosts (`armc-relation/`: relation, adapter, guest, hosts, build driver; `armc-int/`: the integer kernels; `tools/`), the frozen expected identities, the constants blob, the normative noise, the chain log and reference vectors, the boundary fixtures, the build records and source digest lists, the run records and test logs, the node runbook; `FULL_GUEST.md` and `armc-relation/RELATION.md` are the engineering records the statement was frozen from |
| `oracle/` | the Python integer oracle and its FINAL artifact (`oracle/final/`: the execution contract `README_FINAL.md`, `AGREEMENT.md`, `FREEZE_SUMMARY.md`, the constants, the agreement studies, the fixtures and the August input manifest), the oracle's Python and the trainer and evaluator sources it imports |
| `model/` | the proof model's checkpoint (13,701,907 bytes; a documented derivative of the as-trained file with three private path strings rewritten and every tensor verified equal, `REDACTION.md`), its frozen-protocol evaluator output and per-row raw scores, its training log, and the sixteen-variant ARM-C ladder's evaluator outputs |
| `tools/decode_zbdiff01.py` | a standard-library decoder of the 752-byte statement |
| `tools/check_identities.py`, `tools/regen_noise.py` | a standard-library cross-check of every statement against the frozen identities, the chain log, the receipts and the pins; a numpy regeneration of the 112 normative noise tensors from their rule |
| `capsule/` | the offline verification capsule: statically linked `zkdiff-verify` and standalone verifier, the pinned keys and identities, copies of the proofs and statements, `verify_offline.sh`; `capsule/reexecute/` recomputes any row's statement from its raw frame with the static batch driver (row 600's frame shipped) |
| `replicate/` | the one-pull replication kit: `replicate.sh` and a Dockerfile that fetch the package and the data layer, install the pinned toolchains with hash checks, rebuild the program, verify every proof, re-execute a row and, on an A100-class GPU, re-prove one; `TEST_LOG.md` is its clean-container rehearsal and `TEST_LOG_LAMBDA_A100.md` its end-to-end run, `prove` included, on a freshly launched A100-SXM4-40GB machine |
| `tools/standalone_verifier/` | the published ZeeBeam standalone verifier (`sp1-verifier` 6.4.0 plus `sha2`, lockfile included), vendored byte for byte from poliebotics/zeebeam at commit `ef686b33…48bd` (`VENDORED.md`, `PINS.json` `standalone_verifier`); verifies the Groth16 layer of any proof here under the pinned key |
| `LARGE_FILES.md`, `LARGE_FILES_SHA256SUMS` | the files that belong here by layout and are served from the data layer for size (the exported oracle arrays, the d2 vector sets, the cached rows), fixed by path and digest |
| `REDACTION.md`, `REDACTION_LEDGER.tsv` | what was substituted (the alias and redaction rule) or corrected in the copied records, every changed file with its private and published digests; what is published (the frames and the August tensors, since 8 September 2026) and what is not |
| `SHA256SUMS`, `MODES` | the digest of every other file in this directory (check it first); the files that are executable (every other file is mode 0644) |

## What is proved, in one paragraph

Under the pinned verifying key `0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027` (program ELF
`51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc`, 396,200 bytes, rebuilt byte for byte on two
machines and at two absolute paths) and the constants blob `73310ddab603cab5588d05e9ac4deb7e56466a6fae4bbf89244c32f2bd1a8b92`,
an accepting proof establishes that the published `R_correct`, `R_wrong` and `D = R_wrong - R_correct` are what the
frozen integer network produced on the whole-frame reduction of the frame whose BLAKE3 digest sits in the session tree at
the published row, noised with the noise whose BLAKE3 is published, under the row's own emission and under the declared
wrong row's, both re-derived from beacon-seeded chain states, with the published clip count. Each proof costs about
14.4 billion RISC-V instructions in the zkVM; the two network passes are 6.9 billion of them, the frame reduction 2.0
billion and the two pattern renders 4.3 billion (`RESULTS.md` section 4). Those counts were measured on five real rows
(600 to 603 on the development machine, 684 on the node); the batch itself did not count instructions per proof.

## What is not proved

The three paragraphs of `CLAIM_BOUNDARY.md` say it exactly. In short: execution binding of the specified integer
computation on committed bytes, and no claim about physical capture, realness, liveness, illumination causality,
adversarial resistance or generalisation to an unseen session; no reproduction of the eight-seed result, the five-offset
aggregate or a full diffusion trajectory; the noise tensor is bound by its bytes and not by any generator; the August
rows 600 to 711 were held out from weight training and seven of them entered the quantisation calibration; the d2 and
v10 evaluation blocks are development validation.

## Verify it

```
sha256sum -c --quiet SHA256SUMS && echo LEDGER_OK
python3 tools/decode_zbdiff01.py public_values/row_000600_public_values.bin
```

Then, with nothing installed, `bash capsule/verify_offline.sh` (`VERIFY.md` section 2a). Then `VERIFY.md`: the standalone
verifier route (the vendored ZeeBeam standalone verifier in `tools/standalone_verifier/` on the raw proof, the public bytes and
the key above) and the full route (`source/armc-relation/build_reproducible.sh`, which rebuilds the program and asserts the
pins, then `zkdiff-verify --proof proofs/row_XXXXXX_groth16.bin --expect source/expected_identities_august.json` for every row,
which accepts a statement only if every frozen identity matches), or all of it in one pull with `replicate/`.

## Provenance

Principal: Cathal Ryan Hynes (PolieBotics). Drafted, built, proved and verified with BOSUN, the project's automated
research assistant (a Claude-family language model running the project's desk), under the principal's direction; BOSUN
holds no authority and every publication step is the principal's. Second-model audits by GPT-6 Astra through `codex exec`:
five rounds on 7 September 2026 before proving, a sixth on 8 September on the finished package, and a privacy sweep and
<!--ai:confirm_word-->three<!--/ai--> confirmation re-reads of the augmented and re-frozen package the same evening; three outside agents read the package
<!--ai:readings_word-->three<!--/ai--> times for an outsider;
verdict lines in `AUDIT_TRAIL.md`, full texts in `audits/` (the privacy sweep by its verdict and dispositions); these are model
reviews, not independent validation. The model was trained and evaluated on a rented
eight-GPU A100 node, the integer oracle and the guest were built and executed on the development machine, and the proofs
were made on the same rented node, one process per GPU, each proof verified on the node cold against the frozen identities
and again on the development machine (`receipts/`). On 8 September 2026 the principal decided to publish the 112 raw frames
of the proof rows and the August camera-derived tensors (`FRAMES.md`, `LARGE_FILES.md`), so every residual sum can be
recomputed and every proof re-made by anyone; the calibration disclosure is unchanged. The August frames depict a masked participant in a recognisable indoor setting. Camera-derived tensors retain images of participants and their surroundings, including earlier-session examples. These materials are not anonymised; identity may be inferred from clothing, movement or context. Patent filing date:
6 September 2026. Licence: `LICENSE` (the Dark Lantern Research and Private Use Licence 1.2, the repository's): non-commercial
research, teaching, verification and private study; all other rights reserved; section 5 of the licence states what is granted
under any patent.

— BOSUN ⚓

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-07 | BOSUN | Drafted before the proof batch; the counts line and RESULTS.md section 6 are rendered by fill_results.py from the collection. |
| 1.1 | 2026-09-08 | BOSUN | Astra round 6 applied: framed artifact sizes stated as measured, receipts under the evidence allowlist, vendored standalone verifier, sixth audit round, instruction-count provenance. |
| 1.2 | 2026-09-08 | BOSUN | Agent audits round 1: primer, roles, where to start; glossary, FAQ, hashes, frames, licence, capsule, replication kit, audit texts and tools rows; the publication of the frames and tensors and the seventh round in the provenance. |
| 1.3 | 2026-09-08 | BOSUN | Privacy sweep (Astra round 7), confirmation re-read (round 8) and the agents' second reading: what the frames show; the declared offset rule; the redaction ledger, MODES and the checkpoint derivative in the table; the audit rounds restated; the patent notice reduced to the filing date; where to start corrected (platform, timing, the build kit). |
| 1.4 | 2026-09-08 | BOSUN | Section table: the replication kit's fresh-machine run named. |
| 1.5 | 2026-09-08 | BOSUN | Third outside reading: the two-part publication stated in one paragraph, with the bundle's controls and where their digests are fixed. |
| 1.6 | 2026-09-08 | BOSUN | Astra round 11: the audit inventory rendered from audits/ (inline markers); the two-part paragraph says which inventory sits only in the bundle's manifest. |
