---
version: 1.5
date: 2026-09-09
status: every term and acronym used in the prose of this package, defined for a reader with no context; added after the outside-agent readability audits (AUDIT_TRAIL.md, the first reading, A1)
author: Cathal Ryan Hynes (author of record); drafted with BOSUN, the project's automated research assistant
---

# Glossary

Terms are grouped, then alphabetical inside each group. A term in `code` is a field or identifier as it appears in the files.
Where a definition rests on a file in this package the file is named; where the referent is outside the package (the
ZeeBeam manuscript, the Dark Lantern repository, the programme's earlier results) that is said, and `FAQ.md` says what the
package can and cannot tell you about it.

## The recording and the protocol

**ARM-C.** The third training arm (arm C; "ARM" is a label, not an acronym) of the ZeeBeam programme's conditional-diffusion
study: a conditional denoising U-Net whose input is the whole sensor frame reduced to a small grid and whose conditioning is
the projected pattern reduced to the same grid, with no crop. Arm A used a cropped frame (crop `(0,1704,155,2433)` in the
programme's evaluator) and is not used here; the trainer's class for arm C is `ArmCUNet`, wrapping `DiffusionDiagnosticUNet`
(`oracle/trainer/train_lean.py`, `oracle/trainer/phase_g/diffusion_diagnostic_model.py`). The **frozen ARM-C protocol** is
the fixed evaluation recipe of that study: timestep 150, wrong-row offsets {-2, +2, -15, +15, +30}, evaluation seed 20260823,
one noise draw per row in row order, pooled AUROC and paired fraction as the statistics (`oracle/trainer/lean_pubproto_eval.py`).
The published eight-seed ARM-C result of 30 August 2026 is an external referent (Dark Lantern repository,
`notes/zeebeam_nocrop_diffusion_8seed_20260830.md`); this package neither reproduces nor inherits it (`CLAIM_BOUNDARY.md`).

**august_dev_712, the August session, the August take.** The 712-row recording of 22 August 2026 that the session
identifier (defined further down) names: the programme's August development recording. Rows 0 to 599 trained the model; rows 600 to 711 are the
proof rows. It is distinct from the **sealed 288-row verification take**, a separate recording the programme sealed for a
one-look verification, which this work never touched (`CLAIM_BOUNDARY.md`).

**Bayer frame, raw frame, CFA.** One photograph as the camera delivers it: 4,600 rows by 5,320 columns of 8-bit values,
24,472,000 bytes, in the sensor's colour-filter-array (CFA) order `RGGB`: each 2 x 2 block carries one red, two green and one
blue sample. The four **CFA planes** are the four sub-grids (R, G1, G2, B), each 2,300 x 2,660. The raw frames of the proof
rows 600 to 711 are published (`FRAMES.md`, which also says what they show); their BLAKE3 digests are in the chain log and in
every statement.

**Blocking loop.** The capture loop in which the pattern for row t+1 cannot be generated until frame t has been captured and
hashed, because the chain state `S_{t+1}` folds in `BLAKE3(raw_t)`. The session identifier's `BLOCKING` names it
(`oracle/trainer/train_lean.py` line 46 calls these "BLOCKING-loop sessions").

**Chain state `S_t`, `S_0`, `S_N`, chain advance.** A 32-byte value per row. `S_0` is the session seed the recorder chose
(how it was chosen is not in this package; its value is a pin). `S_{t+1} = BLAKE3("TB:ROW:v9" || S_t || len || BLAKE3(raw_t)
|| len || meta_t || len || round_t || len || value_t)` with 4-byte big-endian length prefixes (`HASHES.md`;
`source/armc-relation/b3xof/src/lib.rs` `advance_chain`). `S_N` is the state after the last advance (N = 712); the last
advance of the chain log yields it (`source/vectors_relation/README.md`).

**Chain log.** `source/vectors_relation/august/chain_log.csv`: one line per row (after a first comment line naming the
session start), with the state `S_t`, the frame's BLAKE3, capture identifiers and timestamps, the emission's BLAKE3, the 28-byte
`meta`, the drand round, value and signature, and `drand_staleness_ms`. Its BLAKE3 is a session identity in every statement.

**drand, quicknet, round, beacon value.** drand is a public randomness beacon run by the League of Entropy; **quicknet** is
its chain that publishes a BLS signature every 3 seconds, numbered by round (chain hash `52db9ba7…e971`, public key in
`source/armc-relation/relation/src/beacon.rs` and `PINS.json` `drand`). The **beacon value** of a round is the SHA-256 of its
signature. The guest verifies the signatures of rows r and r-1 under the compiled-in key and requires each value to be the
SHA-256 of its signature. Most consecutive rows carry the same round (`STATEMENT.md` section 1a).

**`drand_staleness_ms`.** A column of the chain log: the recorder's own measure, in milliseconds, of how old the beacon
was when the row was captured (1,363 to 10,799 ms over the session, median 6,100 ms). It is informational: the guest does
not read it and nothing in the proofs binds it (`STATEMENT.md` section 1a; `FAQ.md`).

**Emission, emission pattern, `E_t`.** The RGB image the projector shows for row t, derived from `S_t` alone: three seeds
`BLAKE3("TB:SEED:{R,G,B}:v8" || S_t)`, each expanded by the BLAKE3 XOF to 43,110 bytes, sliced into four **octave** grids
(17 x 30, 34 x 60, 68 x 120, 135 x 240) and rendered by fixed-point bilinear upsampling to 1,920 x 1,080 with the octave o
weighted by `>> o`. Its BLAKE3 over the interleaved RGB bytes is the row's **emission digest**. The guest re-renders the
patterns of rows r and u from their states and requires the digests to match (`STATEMENT.md` sections 1 and 4).

**Hint.** The network's conditioning tensor: the twelve XOF octave channels of a state (three colours by four octaves) reduced
to 96 x 112 and quantised to Q14, plus two coordinate channels: fourteen int16 channels (`STATEMENT.md` section 5).

**`meta`, meta record.** The 28-byte capture record folded into each chain advance and each leaf: big-endian row index
(4 bytes), camera device timestamp in nanoseconds (8), capture wall-clock timestamp in nanoseconds (8), a 4-byte field that
reads 64000 on every row of this session (its meaning is not stated in the package's records **[confirm]**), and the 4-byte
ASCII tag `RG08` (the 8-bit RGGB pixel format). The first three fields equal the chain log's `t`, `aravis_device_timestamp_ns`
and `capture_wall_ns` on all 712 rows (`FAQ.md`).

**Row.** One capture step of the session: one frame, one chain state, one emission pattern, one chain-log line, one leaf.
Rows are about 400 ms apart (median 400.05 ms, `PINS.json` `drand`).

**Session identifier.** `ZEEBEAM_MAINNET_BLOCKING_TRAINING_300S_20260822_001`, the recorder's label for the August
session, bound into every statement as bytes. Read as the recorder named it: the ZeeBeam programme, anchored to Zcash
mainnet, blocking loop, a training (development) recording, a 300-second target, recorded on 22 August 2026, first session
of the day. Only the bytes are proved; the reading is the programme's, not a proved fact.

**Session tree, leaf, ordered-session root, context digest, wrapped root.** A BLAKE3 Merkle tree of depth 10 over the 712
leaves, one per row, `leaf_t = H(ROW, [context, u32be(t), S_t, BLAKE3(raw_t), meta_t, u64be(round_t), value_t, S_{t+1},
BLAKE3(E_t)])`, with domain-separated padding leaves for indices 712 to 1023. The **context digest** hashes the session
identity (`TB-v0.9`, identifier, row count, the terminal flag, `S_0`, `S_N`, the authority-manifest digest, the chain-log
BLAKE3). The **wrapped root** is the internal root hashed once more with the context, row count and depth; it is the
`ordered_session_root` of every statement. Exact byte constructions: `HASHES.md`.

**Authority manifest.** The recorder's session manifest, a file of the ZeeBeam recording whose SHA-256 (`740d752d…d783`)
is one of the context inputs. Only its digest is published, here as in the ZeeBeam release; the guest carries the digest into
the context and does not recompute it (`FAQ.md`).

**TB-v0.9, protocol 9.** The Truth Beam capture protocol revision the session followed (ZeeBeam manuscript section 4), encoded
as the byte 9 in the statement and the private headers, and as the string `TB-v0.9` inside the context digest. "TB" is Truth
Beam, the programme's mark.

**Truth Beam, ZeeBeam, Dark Lantern, PolieBotics.** PolieBotics is the principal's company. Truth Beam is the
projector-camera capture system and its mark. ZeeBeam is the capture-and-proof system and the public release
(github.com/poliebotics/zeebeam, manuscript *ZeeBeam: The Zero-Knowledge Beam* v3.20) whose relation these proofs extend
with a learned component. Dark Lantern is the wider privacy and zero-knowledge research programme and the public repository
this package is published in (github.com/poliebotics/dark-lantern); its `LICENSE` is copied here.

**XOF.** Extendable-output function: BLAKE3 run as a stream that can emit any number of bytes from one seed. The emission
patterns and hints are XOF expansions of the row's state.

## The model, the oracle and the integer contract

**AUROC.** Area under the receiver-operating curve, here the pooled Mann-Whitney probability that a wrong-conditioning
score exceeds a correct-conditioning score across the rows of a session, average ranks for ties. 1.0 is perfect separation,
0.5 is chance (`oracle/trainer/lean_pubproto_eval.py`).

**Calibration, calibration rows.** The fixed-point conversion needs, per tensor, the number of fractional bits at which the
tensor's values are represented; those scales were chosen by running the float model on fifteen rows (eight protocol rows
of d2 and v10, seven August rows) under two conditionings each and recording the largest magnitudes. The seven August rows
are proof rows, which is why the August set is not an untouched test set (`CLAIM_BOUNDARY.md`).

**Constants blob, `ARMCINT1 v2`.** One byte string holding everything the integer network needs besides its inputs: int16
weights, per-channel multipliers, folded biases, GroupNorm parameters, the activation tables with their clipping masks, the
attention exponent table, the coordinate planes and the scale table (layout: `source/armc-int/src/blob.rs`). Its SHA-256 is
in every statement (`constants_sha256`); the guest hashes the blob in circuit.

**d2, v10.** Two earlier Truth Beam sessions recorded with the same kind of rig (d2: 5,992 rows; v10: 3,743 rows), the
programme's public development sessions. Their training blocks trained the model; their **evaluation blocks** (d2: rows
1298 to 1697, 2796 to 3195, 4294 to 4693; v10: 1110 to 1359, 2345 to 2594) were scored repeatedly to compare candidates,
which makes them **development validation** rather than a test set (`RESULTS.md` sections 1 and 2; block bounds in
`oracle/trainer/train_lean.py`). The package ships their cached 96 x 112 reductions and emission rows on the data layer, not
their frames; the frames are public in the Truth Beam session bundles `https://data.truthbeam.com/sessions/d2/` (Truth Beam protocol v9, recorded 2026-04-25T02:08:30Z, 5,992 frames) and
`https://data.truthbeam.com/sessions/v10/` (protocol v10, recorded 2026-04-25T05:10:42Z, 3,743 frames), where row N is
`Recordings/frame_{N:06d}.raw` (`FAQ.md` 17).

**Development validation.** Data excluded from weight training but consulted while choosing the model. Its scores describe
the selected model on data that influenced the selection; they are not an estimate of performance on unseen data.

**Held out, untouched.** "Held out from weight training" means the rows contributed no gradient. The August rows 600 to 711
were held out in that sense and are still not **untouched**: the trainer's quick screen scored four proof rows, 606, 630, 654
and 678, among 28 August rows (the other 24 are training rows), and quantisation calibration used seven proof rows
(`CLAIM_BOUNDARY.md`; `FAQ.md` 23 lists the 28).

**Integer contract, int16 contract.** The exact fixed-point arithmetic of the network's evaluation: int16 weights and
activations, exact 64-bit accumulation, per-layer requantisation with a stated rounding rule, integer GroupNorm, table
look-ups for the activations, integer attention, saturation to the int16 range with every saturation counted
(`oracle/final/README_FINAL.md` section 3; `STATEMENT.md` section 6). The Python oracle, the Rust kernels and the guest all
implement it and were checked byte for byte against each other.

**GroupNorm.** Group normalisation, a layer that normalises groups of channels by their mean and variance; here computed in
integers with a floor integer square root.

**LUT, masked-table hit.** The GELU and SiLU activations are evaluated by 65,536-entry look-up tables indexed by the int16
input. Entries whose exact value fell outside the int16 range were clipped when the table was built and flagged in a
**clipping mask**; an input that lands on a flagged entry is a **masked-table hit** and is counted as a clipping event
(`source/armc-int/src/blob.rs`; `oracle/final/README_FINAL.md` section 3).

**MSE units, denominator.** Residual sums are integers; dividing by `43008 · 2^24 = 721,554,505,728` (43,008 output values,
each squared difference of two Q12 numbers carrying 24 fractional bits) expresses them as a mean squared error in the float
model's units (`STATEMENT.md` section 5).

**Normative noise.** The Gaussian noise tensor added to the reduced frame before the network sees it. For each proof row it
is defined by a stated Philox-based rule (`STATEMENT.md` section 8) and exported as 86,016 bytes; those bytes are the
definition ("normative"), and the proof binds them by BLAKE3. `tools/regen_noise.py` regenerates them from the rule.

**Oracle, Python oracle, G1 artifact.** The independent Python implementation of the integer contract
(`oracle/int_ref.py`, `oracle/kernels.py`) and the frozen artifact it produced (`oracle/final/`: constants, vectors,
agreement studies, the expected residual sums per row). "Oracle" here means reference implementation, not a random oracle.

**Paired fraction.** The fraction of rows whose correct-conditioning score is below the mean of the wrong-conditioning
scores. 1.0 means every row separated; 0.5 is chance.

**PTQ, QAT.** Post-training quantisation (converting a trained float model to integers afterwards, which is what was done
here, with calibration) and quantisation-aware training (training with the quantisation in the loop, which was not done
for the proof model; an earlier candidate family carried a `_qat` label, `AUDIT_TRAIL.md` round 2).

**Q12, Q14, `F_CT`, `F_HINT`, `F_EPS`.** Fixed-point formats: Qn means an integer whose value is the integer divided by
2^n. The reduced frame and the noise are Q12 (`F_CT` = 12), the hint is Q14 (`F_HINT` = 14), the network's output is Q12
(`F_EPS` = 12). These three fractional-bit counts are fixed fields of the statement (`STATEMENT.md` section 2).

**Residual, `R_correct`, `R_wrong`, `D`.** The network predicts the noise that was added; the residual is the sum over the
43,008 output values of the squared difference between the prediction and the noise. `R_correct` is the residual under the
row's own emission, `R_wrong` under the declared wrong row's, `D = R_wrong - R_correct`; positive `D` means the correct
conditioning predicted the noise better.

**Timestep 150, `SA`, `SO`.** The diffusion schedule position at which the frame is noised: `C_t = SA · C + SO · noise` with
`SA = 63540/2^16` and `SO = 16053/2^16`, the cosine schedule's `sqrt(alpha_cum)` and `sqrt(1 - alpha_cum)` at step 150 of the
trainer's schedule, fixed in the statement.

**Whole-frame reduction, zero crop.** The four CFA planes area-averaged to 96 x 112 each (4 x 96 x 112 values), the whole
sensor frame entering the average; no region is cropped away. The exact float path the trainer used is reproduced in
software floating point inside the guest (`STATEMENT.md` section 5).

## The proof system

**Acceptance verifier, `zkdiff-verify`, expected identities.** The package's own verifier: it verifies the Groth16 proof under
the pinned program key and circuit key and then refuses any statement whose fields differ from the frozen table
`source/expected_identities_august.json` (program, session, rule, per-row digests and expected residual sums)
(`STATEMENT.md` section 9). A prebuilt static copy is in `capsule/`.

**Circuit key, Groth16 verifying key, `groth16_vk.bin`.** The 492-byte verifying key of SP1's Groth16 wrapping circuit,
release v6.1.0, embedded in the `sp1-verifier` 6.4.0 crate and shipped as `capsule/groth16_vk.bin`; SHA-256 `4388a21c…e696`.
It is the same for every SP1 6.4.0 Groth16 proof of any program.

**Framed artifact, raw proof, public values, statement.** The SP1 SDK writes each proof as a bincode-framed artifact
(`proofs/row_XXXXXX_groth16.bin`, 2,444 to 2,447 bytes) that carries the 356-byte **raw Groth16 proof**
(`proofs/row_XXXXXX_groth16_proof.bin`) and the 752-byte **public values**, the **statement** the proof is about
(`public_values/row_XXXXXX_public_values.bin`). Receipts call the framed artifact the "proof" (`proof_sha256`) and the raw
proof `proof_raw_bytes`.

**Groth16.** A pairing-based zero-knowledge proof system producing constant-size proofs (here 356 bytes over the BN254
curve) that verify in milliseconds. SP1 wraps its zkVM proof in a Groth16 proof so a verifier needs only the small proof, the
statement and two keys.

**Guest, guest ELF, host.** The **guest** is the program that runs inside the zkVM (`source/armc-relation/program/`), compiled
to a RISC-V **ELF** (396,200 bytes, SHA-256 `51b7bc35…75cc`) that the reproducible build recreates; the **hosts** are the
ordinary programs that drive it (`zkdiff-execute`, `zkdiff-ceremony`, `zkdiff-batch`, `zkdiff-verify`).

**Program verifying key, vkey, `sp1_vkey`.** The 32-byte identity of the guest program under SP1
(`0x00f01894…a027`), derived from the ELF by the SP1 SDK; the proof verifies only under the key of the program that produced
it. The **vk root** (`002f850e…5352`) is a different constant: the root of SP1 6.4.0's own recursion-key tree, embedded in
the verifier crate (`HASHES.md`).

**Relation, leg, witness, public output.** The **relation** is the set of checks the guest performs (`STATEMENT.md` section
4, fourteen **legs**); the **witness** is the private input (the frame, the beacon signatures, the tree paths, the noise, the
offset, the blob); the **public output** is the 752-byte statement to which the proof commits.

**SP1, zkVM, `sp1-verifier`, `cargo-prove`, succinct toolchain, `sp1-gpu-server`.** SP1 (Succinct) is the zero-knowledge
virtual machine: a RISC-V executor whose execution is proved. Release 6.4.0 of its SDK, prover and `sp1-verifier` crate were
used; `cargo-prove` is its build tool, the **succinct toolchain** its Rust compiler for the RISC-V target, and
`sp1-gpu-server` the CUDA prover process. Download sources and digests: `VERIFY.md` section 2.

**Statement bytes, `ZBDIFF01`.** The 752-byte public output, magic `ZBDIFF01`, laid out in `STATEMENT.md` section 2 and
decoded by `tools/decode_zbdiff01.py`.

## The rule, the batch and the audits

**Coordinator, operator, owner, principal.** Two parties. **Principal** and **owner** both mean Cathal Ryan Hynes, who
set the rules (the wrong-row rule and the proof-set rule) and gives every release order. **Coordinator** and **operator**
both mean BOSUN, the assistant, in two of its sessions: the desk session that relayed the principal's decisions to the
parallel working sessions on 7 September 2026 and fixed engineering conventions such as the noise rule, and the session
that ran the builds, the node and the verifications. The published copies call the principal's wrong-row rule the
**declared offset rule**; where a copied record still says "the owner's rule" or "run by the operator", that is what it means.

**BOSUN.** The project's automated research assistant: a Claude-family large language model running the project's desk
(so the ZeeBeam manuscript's acknowledgement describes it). It drafted the text and code of this package under the
principal's direction and ran the machines; it is not a person, holds no authority, and every publication step is the
principal's own action. The alias rule of the Dark Lantern record replaces its machine identity with `BOSUN` in copied files.

**GPT-6 Astra, `codex exec`, round, finding.** The second model that audited the work: GPT-6 Astra run through the
`codex exec` command line at ultra reasoning effort. Each **round** returned a verdict line and numbered **findings**;
`AUDIT_TRAIL.md` lists the rounds, the verdict lines verbatim and the findings' subjects.

**G0, G1, G2, G2-A, G2-D, G3, G0E, G0F.** The gates of the plan (`AUDIT_TRAIL.md`): G0 a learning and feasibility screen
(the training sweeps; G0E and G0F name the two sweeps whose variants are in `model/ladder/`), G1 the integer oracle, G2 the
guest and the proofs (G2-A the integer kernel crate, G2-D the complete guest, G2-G the batch), G3 audit and release.

**The development machine; the node.** The development machine is a laptop-class x86_64 workstation (16 cores and 32 threads;
128 GB of unified memory, of which about 91 GiB is visible to the operating system, the rest being reserved for the integrated
graphics; an NVIDIA RTX 5090 laptop GPU with 24 GB that was not a proving target; Ubuntu 26.04, glibc 2.43) on which the oracle, the Rust code and the builds were made and every proof was re-verified; copied
records name it as such, and its host label in build records reads `development-workstation`. The **node** is the rented
Lambda instance with eight NVIDIA A100-SXM4-80GB GPUs (glibc 2.35) that trained the model and made the proofs; its address
and login are redacted and its host label in the receipts reads `prover-node`.

**The preprocessed-row cache (the Lambda cache).** The node's cache of preprocessed rows, from which the four training-row
hints of the rule pairs were copied (`oracle/final/README_FINAL.md` section 7b); the cached rows the oracle scores are
published under `oracle/rows/d2/`, `oracle/rows/v10/` and `oracle/rows_august/august/` on the data layer (`LARGE_FILES.md`);
copied records that name the cache read `[preprocessed-row cache]`.

**Mirrored offset, direct offset, offset rule, wrong row.** The **wrong row** `u` is the row whose emission is used as the
wrong conditioning. The rule assigns a base offset from {-2, +2, -15, +15, +30} by `(r - 600) mod 5`; the offset is
**direct** when `r + base` lies inside the session and **mirrored** (`-base`) when it would not (ten rows). Public byte 11
carries the flag (`STATEMENT.md` section 7). "standard", the name the oracle's records used for direct, reads `direct` in
this publication (`REDACTION.md`).

**Negative control, relation rejection, policy rejection.** A deliberately mutated input that must be refused. A
**relation rejection** is refused by the guest itself (the mutated witness does not satisfy the relation); a **policy
rejection** is a coherent different statement the relation accepts and only the acceptance verifier's frozen identities
refuse (`RESULTS.md` section 4; `receipts/proof_controls.json`).

**Receipt, ceremony manifest, batch manifest, strict merge.** The prover's per-row record (`receipts/row_XXXXXX_receipt.json`),
the SDK-level record of the same proof (`row_XXXXXX_manifest.json`), the per-process record of fourteen rows
(`gpuN_BATCH_MANIFEST.json`) and their merge into one record that refuses unless all 112 rows are proved and accepted
(`BATCH_MANIFEST_merged.json`). `receipts/README.md` explains the fields.

**Data layer, gateway, prefix.** The programme's public object store (bucket `truthbeam`, served at `data.truthbeam.com`),
where the large files of this package live under `results/zkdiff_august_20260907/v1/` (`LARGE_FILES.md`).

**Evidence allowlist, withheld, on-box.** The release tooling's positive list of what may leave the node's proof collection
for publication; everything else is **withheld** and stays **on-box** (on the development machine), pinned by digest in
`receipts/SHA256SUMS_RUNS` (`receipts/README.md`).

## Terms of art, briefly

**ABI.** Application binary interface: here the fixed byte layouts the guest and its verifiers agree on, the 752-byte `ZBDIFF01`
statement (`STATEMENT.md` section 2) and the order of the ten `read_vec` witness items followed by the constants blob.

**Aravis, GenICam.** GenICam is the industry standard for programming machine-vision cameras; Aravis is the open-source GenICam
and GigE Vision library through which the recorder drove the camera. The chain log's `aravis_device_timestamp_ns` is the camera's
own clock read through it.

**BLS12-381.** The pairing-friendly elliptic curve of drand quicknet's BLS signatures; the guest verifies the two beacon signatures
on it with the `bls12_381` crate it links.

**BN254.** The pairing-friendly curve (also called alt_bn128) over which SP1's Groth16 wrapper proof is made and verified; the
356-byte raw proof is a Groth16 proof on this curve.

**bincode.** The Rust binary serialisation format the SP1 SDK uses to frame a proof together with its public values
(`proofs/row_XXXXXX_groth16.bin`; "Framed artifact" above).

**ELF.** Executable and Linkable Format, the binary format of the compiled guest program: the RISC-V `zkdiff-guest`, 396,200 bytes,
whose SHA-256 is the program pin ("Guest, guest ELF, host" above).

**Random123, Philox.** Random123 is a family of counter-based random number generators; Philox4x32-10 is the member that CUDA's
normal sampler uses and that the normative noise rule reproduces exactly (`STATEMENT.md` section 8; "Normative noise" above).

**Release desk; transmit items 032 and 033.** The release desk is the operator's staging of this publication on the development
machine (the tools named in `REDACTION.md` and `receipts/README.md`). A transmit item is one staged publication action, fired
by the principal from his own shell after review: item 032 is the commit that adds this package to the Dark Lantern repository,
item 033 the upload of the data-layer bundle. Copied briefs and verdicts refer to them by number.

**SDK.** SP1's software development kit, the `sp1-sdk` crate the host programs link to execute the guest, produce and wrap proofs
and write the framed artifact; distinct from `sp1-verifier`, the small crate that checks a Groth16 proof and statement.

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-08 | BOSUN | First version, after the outside-agent readability audits (the first reading, A1). |
| 1.1 | 2026-09-08 | BOSUN | Privacy sweep and second reading: the frames are published (what they show is in FRAMES.md); the quick-screen rows stated as four proof rows among 28; the machines named by role; the cache entry; the mark; the declared offset rule. |
| 1.2 | 2026-09-08 | BOSUN | Third outside reading: short entries for ABI, Aravis and GenICam, BLS12-381, BN254, bincode, ELF, Random123 and Philox, SDK. |
| 1.3 | 2026-09-08 | BOSUN | Third outside reading: the development machine's memory and GPU stated; the release desk and the transmit items defined. |
| 1.4 | 2026-09-09 | BOSUN | Revision 1.1: the d2 and v10 entry names the public session bundles. |
| 1.5 | 2026-09-09 | BOSUN | authorship line, 9 September 2026. |
