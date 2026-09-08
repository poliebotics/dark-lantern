---
version: 1.5
date: 2026-09-08
status: every question the three outside-agent readability audits of 8 September 2026 raised that the package can answer, answered from the package's files, with the questions that only the principal can settle marked as such
author: BOSUN for Cathal Ryan Hynes
---

# Questions an outside reader asked, and the answers the package gives

Three outside agents (a Claude model, a Codex model and a Grok model) read a copy of this package on 8 September 2026 with
no other context and listed what they could not answer (`AUDIT_TRAIL.md`, the outside agents' first reading; their reports
are `audits/agents/*_r1.md`); the same evening they read the augmented package a second time (`*_r2.md`), and the section
"The second reading" below answers what remained. The questions are merged where they overlapped and grouped as they
grouped them. Each answer names the file that carries it.
Where the answer is a decision of the principal that has not been taken, the entry says **not decided at publication** and gives
the current position; the same evening the principal decided to publish the raw frames, the August tensors and the audit
texts, and the entries below state the result. Terms are defined in `GLOSSARY.md`; every published hash is explained in
`HASHES.md`.

## Hashes and identities

**1. What is the `vk root` printed in every acceptance report?** `sp1_verifier::VK_ROOT_BYTES` of the `sp1-verifier` 6.4.0
crate: the root of the Merkle tree of SP1's own recursion verifying keys for that release, a constant of the verifier, which
the Groth16 verifier requires the proof's committed root to equal. It is how a proof made with another SP1 release is
refused. It is not a pin of this package's program; the program's pin is the vkey `0x00f01894…a027`. `PINS.json`
`program.vk_root`, `HASHES.md`, `receipts/README.md`.

**2. What is the authority manifest whose SHA-256 `740d752d…d783` sits at offset 228, and where are its bytes?** It is the
recorder's session manifest, a file of the ZeeBeam recording of 22 August 2026. Its digest is one of the inputs of the
context digest; the guest carries it into the context and does not recompute it, exactly as the ZeeBeam release does, and the
ZeeBeam release likewise publishes the digest and not the file ("The authority-manifest preimage is not bundled; only its
digest is", ZeeBeam manuscript v3.20). Publishing the manifest is a decision for the ZeeBeam release, not this package:
**not decided at publication**. `GLOSSARY.md`, `HASHES.md`.

**3. How were `S_0` and `S_N` chosen or derived?** `S_0` is the seed the recorder chose for the session; how it was chosen is
not in this package and is not needed to verify a proof (the guest binds its bytes through the context digest). `S_N` is the
chain state after the 712th advance; the last advance of the chain log yields it (`source/vectors_relation/README.md`), and the
relation tests reproduce all 711 advances. `GLOSSARY.md`, `HASHES.md`.

**4. How exactly are the context digest, the leaves, the nodes, the padding and the wrapped root computed, and how is the
chain advanced?** Byte for byte in `HASHES.md` (sections "The session and the chain"), taken from
`source/armc-relation/relation/src/membership.rs` and `source/armc-relation/b3xof/src/lib.rs`.

**5. What are the fields of the 28-byte `meta`?** Big-endian: row index (u32), camera device timestamp in nanoseconds (u64),
capture wall-clock timestamp in nanoseconds (u64), a u32 that reads 64000 on all 712 rows, and the ASCII tag `RG08`. The first
three equal the chain log's `t`, `aravis_device_timestamp_ns` and `capture_wall_ns` on every row (checked when this file
was written). The meaning of the constant 64000 is not stated in any record in the package **[confirm]**; `RG08` names the
8-bit RGGB pixel format. `GLOSSARY.md`.

**6. What does the receipt control `sdk.wrong_vkey` mean by "verifying key preprocessed commitment rotated"?** The prover
built a wrong program key by rotating the verifying key's preprocessed commitment by one element and confirmed that the SDK
refuses the proof under it; the hash printed is that wrong key's `bytes32()`. `receipts/README.md`, `source/armc-relation/
script/src/ceremony_core.rs` `verify_original_and_tamper`.

**7. Where can `cargo-prove`, the succinct toolchain, `sp1-gpu-server` and the Groth16 v6.1.0 circuit files be obtained so
the pinned hashes can be checked?** `VERIFY.md` section 2 now carries the download URL, the SHA-256 and the size of each;
`replicate/replicate.sh` fetches and checks them. The Groth16 circuit files are needed only to prove.

**8. What is in the node's `SHA256SUMS_RUNS` beyond the shipped files, and how would a reader use the digests of withheld
files?** It lists every file of the node's collection, published or withheld. Every published file was checked against it
before it was copied (the count is in `receipts/README.md`); the withheld files' digests are a commitment that lets any later
publication of them be checked against the ledger published first. `receipts/README.md`.

**9. Are the three `model.pubproto_raw` values labelled, and are `PINS.json` paths consistent?** Yes now: `PINS.json`
`model.pubproto_raw` names the two files; every path in `PINS.json` is package-relative (`noise_files[r].file` reads
`source/noise_august/…`); the one file that keeps its frozen private paths is `source/expected_identities_august.json`, because
every receipt names its SHA-256, and `PINS.json` `path_conventions` says which base each file uses.

**10. Why do all 112 receipts say `sp1_version: v6.1.0` when the package says SP1 6.4.0?** Two different things. 6.4.0 is the
release of the SP1 SDK, prover and `sp1-verifier` crate; `v6.1.0` is the release of the Groth16 wrapping circuit those crates
embed, and the SDK writes that circuit-version string into every artifact as its `sp1_version`. `receipts/README.md`,
`PINS.json` `program.sp1_version_note`.

## The public statement

**11. What is protocol `TB-v0.9`, ABI 1, protocol byte 9?** The Truth Beam capture-protocol revision the session followed,
defined in the ZeeBeam manuscript section 4 and encoded as byte 9 in the statement and the private headers and as the string
`TB-v0.9` inside the context digest; ABI 1 is the version of this statement's byte layout. There is no registry beyond the
manuscript and the source; the guest checks both bytes as fixed values. `GLOSSARY.md`.

**12. What do `MAINNET`, `BLOCKING`, `TRAINING` and `300S` mean in the session identifier?** The recorder's label, read as:
ZeeBeam programme, anchored to Zcash mainnet, blocking capture loop, a training (development) recording, a 300-second target,
22 August 2026, first session of the day. The proof binds the bytes of the identifier; the reading is the programme's.
`GLOSSARY.md`.

**13. Why do rows r and r-1 usually carry the same drand round, what does the predecessor leg add, is monotonicity checked,
and what is `drand_staleness_ms`?** `STATEMENT.md` section 1a answers in full. In short: quicknet publishes one round every
3 s and rows are 400 ms apart, so 646 of the 711 consecutive pairs share a round (66 distinct rounds across 712 rows; 10
across the proof rows; row 600 carries 31521690 twice). For such a row the guest verifies one signature twice; the
predecessor leg still binds `S_r` to the previous row's record (its frame digest, meta, round and value) through the chain
advance, which is the leg's purpose. The guest checks no round monotonicity; the acceptance verifier pins both rounds of
every statement to the chain log, whose rounds are non-decreasing (`tools/check_identities.py` prints the check).
`drand_staleness_ms` is the recorder's own measure of the beacon's age at capture and is bound by nothing.

**14. Which quicknet public key is compiled in, and is the chain hash the only out-of-band fact?** The 96-byte key is in
`source/armc-relation/relation/src/beacon.rs` and `PINS.json` `drand.quicknet_public_key_hex`; the chain hash `52db9ba7…e971`
is in the drand leg digest. A verifier who trusts the compiled-in key trusts that it is quicknet's; comparing it with the
public chain information is the out-of-band step, and so is checking that a round's signature is the one the relay
published. Neither needs the prover; both need the network. `VERIFY.md` section 4.

**15. What are `F_CT`, `F_HINT`, `F_EPS`; what is a masked-table hit; why the denominator `43008 · 2^24`?** Fractional-bit
counts of the reduced frame (Q12), the hint (Q14) and the network output (Q12); an activation-table entry flagged as clipped
that an input lands on, counted as a clipping event; 43,008 output values each a squared difference of two Q12 numbers.
`STATEMENT.md` sections 2, 5 and 10; `GLOSSARY.md`.

## The recording and the datasets

**16. What is the August session physically?** A projector (1,920 x 1,080 RGB8) lights a scene; a 24.5-megapixel GenICam
industrial camera (5,320 x 4,600 BayerRG8, driven through Aravis) photographs it; the session ran about 300 s and produced
712 rows (ZeeBeam manuscript section 4; `README.md` primer). The 112 raw frames of proof rows 600 to 711 and their camera-derived
tensors are published; see `FRAMES.md`. The August frames depict a masked participant in a recognisable indoor setting. Camera-derived tensors retain images of participants and their surroundings, including earlier-session examples. These materials are not anonymised; identity may be inferred from clothing, movement or context.

**17. What are d2 and v10, what was recorded, when, how many rows, and where can they be obtained?** Two earlier Truth Beam
sessions recorded with the same kind of rig, the programme's public development sessions: d2 has 5,992 rows, v10 3,743
(`oracle/trainer/train_lean.py` `SESSIONS`). The package ships the cached 96 x 112 reductions and emission rows it used (on
the data layer, `LARGE_FILES.md`), not their frames, and does not carry the public location of those frames or their recording
dates: **not decided at publication** (the principal to add the reference). The frames of the August proof rows are published
(`FRAMES.md`). Training blocks: d2 rows 0 to 1237, 1758 to 2735,
3256 to 4233, 4754 to 5991 (4,432 rows); v10 rows 0 to 1049, 1420 to 2284, 2655 to 3742 (3,003 rows). Evaluation blocks:
d2 1298 to 1697, 2796 to 3195, 4294 to 4693 (1,200 rows); v10 1110 to 1359, 2345 to 2594 (500 rows). The blocks are
disjoint with 60-row gaps, and 4,432 + 3,003 + 600 August rows = 8,035, the trainer's count. `RESULTS.md` section 1.

**18. What is an emission pattern, and what is ARM-C?** `GLOSSARY.md` (both entries) and `README.md` primer.

**19. What does "the session whose anchored rows the ZeeBeam release proves" mean by "anchored"?** The ZeeBeam release
anchored a prefix of this session's chain (rows 1 to 259) in Zcash mainnet transactions and proved rows under its relation;
this package uses the same session and the same chain log and makes no use of the anchor. `GLOSSARY.md` (august_dev_712).

**20. What are "the eight-seed AUROC", "the five-offset aggregate", "the original published checkpoint", "the published
coupling packet" and "the sealed 288-row verification take"?** External referents, defined in `GLOSSARY.md` (ARM-C,
august_dev_712) and in short here: the programme's published ARM-C result of 30 August 2026 (eight training seeds, AUROC
1.0 on d2 and v10 at step 12,000; Dark Lantern `notes/zeebeam_nocrop_diffusion_8seed_20260830.md`); that result's statistic,
which pools the five wrong offsets; the checkpoint of that result; the Dark Lantern `proofs/coupling/` package, whose
preprocessed camera tensor was held, the precedent for the earlier revision's withholding of the August tensors; and a separate 288-row recording
sealed for one look, untouched by this work. None of them is reproduced or inherited by these proofs (`CLAIM_BOUNDARY.md`).

**21. What is "the Lambda cache"?** The node's cache of preprocessed rows (the preprocessed-row cache), from which the four
training-row hints of the rule pairs were copied; the cached rows the oracle scores are published on the data layer under
`oracle/rows/d2/`, `oracle/rows/v10/` and `oracle/rows_august/august/` (`LARGE_FILES.md`), and copied records that name the
cache read `[preprocessed-row cache]`. `GLOSSARY.md`.

**22. What is `crop_id UNCROPPED_FULL_FRAME_20260825`?** The trainer's label recording that no crop is applied (its default
argument in `oracle/trainer/train_lean.py`), kept in the checkpoint's recorded arguments so a cropped and an uncropped model
cannot be confused.

## "Held out"

**23. Which 28 August rows did the trainer's quick screen consult, and did the screen affect any decision?** The screen scored
`range(30, 682, 24)`: rows 30, 54, 78, 102, 126, 150, 174, 198, 222, 246, 270, 294, 318, 342, 366, 390, 414, 438, 462, 486,
510, 534, 558, 582, 606, 630, 654 and 678 (`oracle/trainer/train_lean.py` `eval_rows`). Twenty-four of them are training rows
below 600; four are proof rows: 606, 630, 654 and 678. The screen printed one line per 2,000 steps (`model/training/train.log`)
and was not used to choose the checkpoint: the selection was made on the d2/v10 evaluation blocks (`RESULTS.md` section 2).
Before this file was written, `RESULTS.md` section 1 and `CLAIM_BOUNDARY.md` described the 28 as held-out rows; both are
corrected.

**24. Would the proved residuals differ under a scale map calibrated without the seven August rows?** Not measured. The
rehearsal shows the scale histogram differs (`VERIFY.md` section 7); the effect on the residual sums and signs was not
computed. Since the August camera-derived rows are published (data layer, `LARGE_FILES.md`) anyone can compute it with the
oracle (`oracle/int_ref.py --no-august-calib` on the August inputs). This comparison has not been measured.

**25. What does "held out" mean here, exactly?** Excluded from weight training (no gradient). Four proof rows were among the
quick screen's rows (question 23), seven were calibration targets and fourteen identities entered the calibration through the
own/+15 pairing (`CLAIM_BOUNDARY.md`). Of the fourteen identities, twelve proof rows have one of them as their wrong row
(633, 634, 646, 647, 648, 649, 650, 661, 662, 665, 694, 709), and the fourteen are all proof rows themselves. So: not an
untouched test set, as the claim boundary says.

## The results

**26. Are the numbers good? Where is the null or baseline?** The package carries no random-network or shuffled-hint baseline
and no confidence interval on the 112 August margins; the chance level of AUROC and of the paired fraction is 0.5, and the
comparison the proofs make is between the row's own conditioning and a declared wrong one. `RESULTS.md` section 1 gives the
95 % confidence intervals of the d2 and v10 margins (block bootstrap over the evaluation blocks). A baseline study is not in
the record.

**27. Why are the August margins about half the d2/v10 margins?** Reported, not explained; no explanation is on record.

**28. Why `D_q > 3η`, and was it fixed before the target results?** η bounds the total error between the integer and the
reference scores of a pair, so `D_q > η` already guarantees the reference has the same sign; 3 is a safety factor. The rule
was set by the second-model audit's round 2 at 18:51 on 7 September, before the integer oracle produced its numbers (round 3
audited them at 19:41). `AUDIT_TRAIL.md`. Percentiles are sample percentiles over the pairs (`oracle/agreement.py`).

**29. What does the unresolved bf16 fidelity at 1.1e-3 imply?** It bounds how closely the oracle's emulation of the node's
bf16 arithmetic reproduces the float development-validation scores of `RESULTS.md` section 1; it does not touch the proofs,
which bind an exact integer computation, and the integer margins exceed the reference error by a factor of 80 or more
(`RESULTS.md` section 3).

**30. By what criterion was the 24,000-step seed-20260908 checkpoint chosen over variants with larger margins?** The record
shows, not a written criterion, but a sequence: round 1 recommended a dense width-16 network at 96 x 112, round 2 confirmed
ARM-C at that width; the seed-20260908 24,000-step checkpoint was the first of that family to finish and pass AUROC 1.0 and
paired 1.0 on both evaluation blocks, the integer oracle was frozen from it that evening, and the 48,000- and 96,000-step arms
finished later (`RESULTS.md` section 2 lists them; `oracle/final/README_FINAL.md` section 0 says a longer-trained checkpoint
may be swapped in later). No swap was made. The ordering is derived from the records' timestamps **[derived]**.

**31. How is the number 507 (row, offset) pairs obtained?** Every (row, offset) pair among the five protocol offsets whose
wrong row's hint was available, plus the six mirrored -30 rule pairs: -2 on 111 rows (row 601's wrong row 599 is a training
row with no hint), +2 on 110 (rows 710 and 711 leave the session), -15 on 101 (rows 600 to 614 point below 600; the four
training-row hints 587, 592, 597 and 598 were pulled), +15 on 97, +30 on 82, and -30 on the 6 rows the rule mirrors:
111 + 110 + 101 + 97 + 82 + 6 = 507 (`oracle/final/agreement_int16_august.json`).

**32. What is the meaning of the prove time column, 61 to 67 min against the pilot's 46?** The `.groth16()` call per row
with eight processes sharing the node; contention is an interpretation, not a measured cause (`RESULTS.md` section 6).

## The wrong-row rule

**33. Why these five offsets, why cycle by `(r - 600) mod 5`, and why mirror rather than skip?** The five offsets are the
frozen protocol's (`oracle/trainer/lean_pubproto_eval.py`). What is on record is the rule itself (`STATEMENT.md` section 7)
and its effect: one proof per row, each offset used on 22 or 23 rows, and the ten boundary rows kept in the set with the
same offset magnitude in the other direction rather than dropped. The principal set the rule; no further rationale is
recorded.

**34. Who are the owner, the principal, the coordinator and the operator?** Two parties: the principal (owner) is Cathal Ryan
Hynes; the coordinator and the operator are BOSUN, the assistant, in two of its sessions. `GLOSSARY.md`, `README.md`.

**35. Can a verifier who uses only the standalone route detect a relabelled statement on the eight policy-only rows (697,
702, 707 and 710, which a flipped flag would relabel as mirrored, and 698, 703, 708 and 711, relabelled as direct; `STATEMENT.md`
section 7)?** No: that route checks the Groth16 layer only. The acceptance verifier does (`rule.assignment`), and it now
needs no toolchain: the static `capsule/zkdiff-verify` (`VERIFY.md` section 2a). Without any binary, `tools/check_identities.py`
(standard library) recomputes the rule from the row number and compares every public field with the frozen table; it does
not verify the proof itself, so use both.

**36. Why do four proofs take a training-row hint (600, 602, 607, 612)?** Because the rule's offset points below row 600 for
them and the rule was applied without exception; the wrong hint is a conditioning identity, not training data for the frame
being scored, and the four are disclosed in `STATEMENT.md` section 7 and `RESULTS.md` section 3.

**37. `common.py` `rule_pair` tests only `r + o >= 712`, `rule.rs` tests both bounds.** On rows 600 to 711 with the five
offsets `r + o` is never negative (the smallest is 585), so the two agree on every row of this set; the Rust form is the
general one.

## The noise

**38. Who generated the 112 noise files, could the prover have chosen them, and can the bytes be checked against the
rule?** (See also 39.) They were generated by the oracle's `randn_cuda_emul` under the rule in `STATEMENT.md` section 8 and exported before
proving; `tools/regen_noise.py` regenerates all 112 from the rule with numpy alone and compares them with the published
bytes, their SHA-256 in `PINS.json` and their BLAKE3 in the statements (112 of 112 equal when this file was written). A
prover could not choose them without changing the published BLAKE3, which the acceptance verifier pins per row.

**39. Why does the August stream restart at call index 0, why seed 20260823, and why is the noise a witness rather than
derived in circuit?** The frozen evaluator has no noise stream for the August rows, so a rule had to be defined for them;
the rule reuses the protocol's evaluation seed and indexes by row so each row's noise can be regenerated alone
(`oracle/final/README_FINAL.md` section 5). The noise is a witness because the emulation's correspondence to the CUDA
generator is approximate (float32 `log` and `sin`), so the bytes are made normative and bound by BLAKE3 rather than
re-derived by an approximate generator in circuit (`STATEMENT.md` section 8).

## The integer contract

**40. Why integer arithmetic for the network when the frame reduction runs in software floating point?** The network is
evaluated three times by three implementations (Python oracle, native Rust, the zkVM) and must agree bit for bit; integer
arithmetic makes that agreement exact and cheap to prove, whereas float in a zkVM is software-emulated and slow. The
reduction is float because the trained pipeline's float path had to be reproduced bit for bit and it is a small part of the
work (2.0 of 14.4 billion instructions). `STATEMENT.md` section 5; `RESULTS.md` section 4.

**41. Why int16 rather than int8, when both pass the rule?** int16 was set as the fidelity baseline before the oracle ran
(`AUDIT_TRAIL.md` round 2); it passes with a margin of 80 against the reference error where int8 passes with 19
(`RESULTS.md` section 3). The proving cost of int8 was not measured.

**42. What is the byte layout of the constants blob?** `source/armc-int/src/blob.rs` (header comment); `GLOSSARY.md`.

## The audits

**43. What did the audits find, in full? Was the package re-audited after the round-6 REVISE?** The full texts are published:
`audits/astra/` holds <!--ai:pairs_word-->nine<!--/ai--> briefs and verdicts (rounds <!--ai:rounds_text-->1 to 6 and 8 to 10<!--/ai-->), `audits/agents/` the <!--ai:reports_word-->nine<!--/ai--> outside-agent reports of <!--ai:readings_word-->three<!--/ai--> readings, with on-box paths
trimmed to package paths (`audits/README.md`); `AUDIT_TRAIL.md` lists the subjects of the round-6 findings and the verdict
lines. After round 6 the revised package was read by the three outside agents (their first reading, whose findings this file
answers). The augmented package (frames, tensors, audit texts, capsule) was then read again on the evening of 8 September 2026:
by the second model twice, a privacy and embarrassment sweep of both payloads (round 7; verdict STOP until the private
infrastructure and desk disclosures it listed were removed from the shipped bytes, every disposition applied) and a
confirmation re-read of the round-6 dispositions (round 8; verdict REVISE, nineteen findings, applied), and by the three outside
agents a second time (`audits/agents/*_r2.md`); the re-frozen revisions were then read in rounds 9 and 10 (verdicts STOP on
remaining private text, applied) and by the three agents a third time (`audits/agents/*_r3.md`). `AUDIT_TRAIL.md` carries the
verdict lines and what changed; the revision that applies round 10 and the third reading has not itself been re-read.

**44. What is "GPT-6 Astra through `codex exec`"?** The second model used for the audits, run through the `codex exec`
command line at ultra reasoning effort, reading files only. `GLOSSARY.md`.

**45. What does "independently verified" mean in the claim boundary?** Verified by verifiers independent of the proving
process: cold on the node, again on the development machine, and now by any reader with the capsule. It does not mean an
independent organisation; the model audits are model reviews (`AUDIT_TRAIL.md`).

## Patent, licence, provenance, locations

**46. What licensing information accompanies the filing notice?** Patent filing date: 6 September 2026. What a reader may do
is what `LICENSE` grants; its section 5 states the position under any patent (no licence, and no assertion against the
permitted non-commercial uses).

**47. What are the licence terms?** `LICENSE`, copied byte for byte from the Dark Lantern repository's root: the Dark
Lantern Research and Private Use Licence 1.2. The `THIRD_PARTY_NOTICES.md`, `licenses/` and `CITATION.cff` it names are files
of the repository root, beside this package; a standalone copy of the package lacks them. The commit that adds this package
extends the root notices with rows for the capsule's three static executables (their crate licence lists and glibc) and the
second copy of `groth16_vk.bin`, and adds the licence texts those rows name; `capsule/THIRD_PARTY_NOTICES.md` carries the
same terms inside the package.

**48. Who or what is BOSUN, and what is Dark Lantern?** `GLOSSARY.md`; `README.md` Provenance.

**49. Where is the data layer?** Bucket `truthbeam`, served at `https://data.truthbeam.com/`, prefix
`results/zkdiff_august_20260907/v1/`; the objects and their controls are listed in `LARGE_FILES.md` and `FRAMES.md`, and
`replicate/replicate.sh fetch` downloads and checks them. The prefix is populated by the release that publishes this package (the data-layer upload precedes or accompanies the repository commit); the Dark Lantern root `README.md` provenance paragraph records the manifest digest, object count and byte total of what was uploaded, and `replicate/replicate.sh fetch` refuses a prefix whose controls disagree with this package's ledgers.

**50. Where are `fill_results.py`, `stage_package.py`, `make_pins.py` and `evidence_allowlist.py`?** In the release desk's
staging repository, not in the package; they generated `RESULTS.md` section 6, `REDACTION.md`, `LARGE_FILES.md`, `PINS.json`
and `receipts/`. Everything they produced is checkable without them; publishing them is **not decided at publication**.

**51. Does the zero proof nonce make re-proving byte-deterministic?** No. The nonce fixes the zkVM-level inputs; the Groth16
wrapping is randomised, so a fresh proof of the same row has different proof bytes and the same 752-byte statement
(`replicate/README.md`).

## Paths, copies and inconsistencies the audits listed

**52. `source/oracle_final/`, `oracle/rows/`, `oracle/rows_august/…/C_*.npy`.** On the data layer (`LARGE_FILES.md`), the
August sets and rows included since the principal's decision of 8 September 2026 (`REDACTION.md`).

**53. `oracle/ckpt/final/…pt`, `g1_integer/`, `../src`.** The private tree's layout; the published layout is `model/`,
`oracle/` and `oracle/trainer/`, and the copied scripts resolve the published locations (`REDACTION.md`;
`oracle/final/README_FINAL.md` banner).

**54. `NODE_PROVE_READY.md`.** Held: it names the node's address, login and filesystem layout; its toolchain facts are in
`VERIFY.md` section 2 and `PINS.json` (`REDACTION.md`).

**55. `frames_august/frame_000600.raw`; the August `row_*.npz`.** Published on 8 September 2026 by the principal's decision:
the 112 frames are on the data layer under `frames/` (`FRAMES.md`; row 600's is also shipped in `capsule/reexecute/`), and the
112 `row_NNNNNN.npz` oracle inputs are on the data layer under `oracle/final/august_inputs/` (`LARGE_FILES.md`; row 600's is
also in `capsule/reexecute/`). `capsule/reexecute/reexecute_row.sh` recomputes any row's statement from its frame
(`capsule/README.md`).

**56. `repository_package_large_files/`.** The directory under the data-layer prefix that holds the files of `LARGE_FILES.md`
at their package-relative paths.

**57. `RELATION.md` said 3,411,318 bytes, nine witness items and `--elf`; `README_FINAL.md` said Rust parity open, version
2.0 and a wrong ratio; `FULL_GUEST.md` said never proved and `[pending node]`; the runbook's bundle check and stagger;
`offset_rule` `standard` against `direct`; `statement.rs` said nine items; `FREEZE_SUMMARY.md` records a digest that is not
the published `AGREEMENT.md`'s.** All corrected in the published copies or explained: `REDACTION.md` lists every changed
copy with its private and published digests and the reason; the copies carry dated banners where their frozen text had been
overtaken. `standard` was the oracle's name for `direct` and reads `direct` everywhere now.

**58. The standalone verifier's comment names 1,085- and 1,101-byte statements and flips byte 87.** It is the ZeeBeam
release's generic tool, vendored unchanged: it verifies whatever public bytes it is given. Byte 87 of this 752-byte layout is
the first zero byte of the session-id padding; flipping any public byte changes the committed digest, so the rejection is
the expected one. `VERIFY.md` section 1.

**59. `G2D_NODE_RUNBOOK.sh build` checks `SHA256SUMS_G2D`, which does not validate the published tree; `prove` sleeps 20 s
where the batch used 90 s.** Both are stated in the runbook copy's banner; the published rebuild route is
`build_reproducible.sh` (`VERIFY.md` section 2) and the launch schedule the batch used is `receipts/launch_schedule.txt`.

**60. `VERIFY.md` names `zkdiff_august_20260907` as the directory.** `P` is the absolute path of your copy of the package,
wherever it sits; the name is the package's name in the repository.

**61. The eight prover clients returned a nonzero status during cleanup after writing complete manifests; can that be
inspected?** The stderr files are withheld (infrastructure diagnostics, pinned by digest in `receipts/SHA256SUMS_RUNS`); the
manifests were complete before the exits and every proof was accepted cold twice. `receipts/README.md`, `RESULTS.md` section 6.

**62. `noise_proposal/` and its comparison record.** Omitted as a byte-identical duplicate of `source/noise_august/`; the
comparison record is not shipped; `tools/regen_noise.py` reproduces the bytes from the rule, which is the stronger check.

**62a. Can a residual sum, and a proof, be recomputed now?** Yes. `capsule/reexecute/reexecute_row.sh ROW --frames-dir DIR`
recomputes any row's statement from its published frame with no toolchain (rehearsed for rows 600 and 684, `VERIFY.md`
section 9); `source/tools/python_oracle_rows.py` recomputes the residual sums in Python from the published
`oracle/final/august_inputs/row_NNNNNN.npz` (rehearsed for 600 and 684); `replicate/replicate.sh prove ROW --frame PATH`
re-proves a row on an A100-class GPU (rehearsed once, on a freshly rented A100-SXM4-40GB, 43 min for row 600; question 78).

**63. `b3xof/PROVENANCE.md` names a private path.** The crate is a verbatim copy of the ZeeBeam release's source bundle
(`bundle/proofs_20260902/source/deps/…/b3xof_experiment_snapshot/source/sp1/relation/` in github.com/poliebotics/zeebeam);
the five file digests it lists can be checked against that public repository.

**64. What did the augmented package add for an agent with no toolchain?** `capsule/` (static binaries, tested with no
network in a fresh Ubuntu 22.04 container, with the re-execution of any row from its frame), `tools/check_identities.py` and
`tools/regen_noise.py` (Python), `replicate/` (the one-pull route with pinned downloads, tested end to end from an empty
container), `GLOSSARY.md`, `HASHES.md`, `FRAMES.md`, this file, `LICENSE`, the published frames and August tensors on the data
layer, the audit texts in `audits/`, and, after the second reading, the offline build kit on the data layer (question 65).

## The second reading

**65. Can the proved program be rebuilt without the network?** Yes, from the offline build kit on the data layer
(`build_kit/`, `LARGE_FILES.md`, `VERIFY.md` section 2b): the vendored crates of every lockfile under `source/` and
`tools/standalone_verifier/`, laid out by the kit's script so the rebuild reproduces the pinned ELF byte for byte, the pinned
toolchain downloads (rustup-init 1.29.1, Rust 1.98.0, cargo-prove and the succinct guest toolchain of SP1 6.4.0, protoc 21.12,
sp1-gpu-server 6.4.0) and the seven Groth16 v6.1.0 circuit files, each with its SHA-256 in `build_kit/KIT_MANIFEST.json`
(digest in `PINS.json` `build_kit`). `build_kit/BUILD_KIT.md` gives the procedure; `build_kit/offline_build_test/` is the record
of the rebuild in a container with no network, which reproduced the pinned ELF and key. The OS packages (a C compiler and
linker, pkg-config, GNU time, binutils, xz-utils, unzip) still come from the operating system.

**66. Why are the data-layer `_control/` digests not in `PINS.json` or `LARGE_FILES.md`?** Because the bundle carries copies of
this package's front matter and ledgers, its manifest digest depends on this package's bytes; a package that pinned that digest
would change it. The digests are therefore published outside both payloads, in the Dark Lantern root `README.md` provenance
paragraph for this package, together with the object count and byte total. `LARGE_FILES.md`.

**67. What is the SHA-256 of the Groth16 v6.1.0 circuit tarball?** `18beebb6cd0cc9b4d4a240ee4f49511da6c2a7e51724bad4232de538a9147810`
(6,211,807,514 bytes; `build_kit/circuits/groth16/v6.1.0/CIRCUIT_TARBALL.txt` records the digest of the downloaded tarball and
of each member, which equal the seven pins in `PINS.json` `prover_node.groth16_circuit_files_v6_1_0`). The tarball itself is
not mirrored; its seven members are, under `build_kit/`.

**68. Where are the frames of the training rows 0 to 599, and do the four training-row hints need them?** Not published
(`FRAMES.md`). No: a hint is derived from the row's chain state alone (`GLOSSARY.md`, "Hint"), so the wrong hints of rows 600,
602, 607 and 612 (rows 598, 587, 592, 597) need no frame; the emission rows the oracle used for them are on the data layer
under `oracle/rows_august/august/` (`LARGE_FILES.md`).

**69. Does proving need Go?** No. The batch was built with `--features cuda` alone (`source/node_prep/r5/build_record_20260907T215855Z.txt`)
and the Groth16 wrapping runs inside `sp1-gpu-server`; `VERIFY.md` section 2 and `source/armc-relation/RELATION.md` (corrected
in the published copy) now say the same.

**70. How is the Python oracle run on row 600 with the package alone?** Copy `capsule/reexecute/row_000600.npz` to
`oracle/final/august_inputs/row_000600.npz`; the positive control at the start of `source/tools/python_oracle_rows.py` also
needs the d2 vector sets `oracle/final/vectors/vectors_int16_d2_1328_*.npz` and the cached d2 rows from the data layer, so the
Python route needs the data-layer files in any case (`VERIFY.md` section 7). The toolchain-free route for row 600 is
`capsule/reexecute/reexecute_row.sh`.

**71. Why do the receipts name an expected-identities digest (`6822cdce…`) that the shipped file does not hash to?** The
shipped `source/expected_identities_august.json` hashes to `182870aa…`: it differs from the file frozen on 7 September
2026 only in the provenance paths of its `sources` block, which the publication redaction replaced with package locators
(`REDACTION.md`; `PINS.json` `program.expected_identities_sha256_frozen` and `expected_identities_note`). Every identity the
verifier compares is equal in both, and an acceptance report written against the shipped file names the shipped digest. The
same holds for the checkpoint (`9cf16eae…` published, `c6955192…` as trained, three path strings apart) and for the node's
build record (`capsule/STATIC_LINK_RECORD.txt` gives both digests). The `sources.prepare_manifest` entry names a private
prepare run whose only published part is the row-684 witness directory; it is provenance, not a file to resolve.

**72. Why does one frame gap read 533.8 ms against a median of 400.05 ms?** `PINS.json` `drand.frame_spacing_ms_min_median_max`
records the spread; the cause of the single long gap is not recorded.

**73. Does `tools/check_identities.py` recompute the leaves and emission digests?** No: it compares every statement field with
the frozen table and the chain log; the recomputation lives in the Rust relation (its tests) and in the batch driver's native
re-execution, which `capsule/reexecute/reexecute_row.sh` runs for any row. A Python-only reader confirms consistency, not
derivation.

**74. Which of the capsule timings holds, "about two minutes" or 3 min 25 s?** The measured runs: about three and a half
minutes for `verify_offline.sh` on the rehearsal machine (2 min 52 s to 3 min 25 s across the recorded runs) and about the same in
a container; every earlier "about two minutes" is corrected. `capsule/README.md`.

**75. Which glibc is in the static binaries?** glibc 2.43 (Ubuntu 26.04), linked statically; the `GLIBC_2.39` in the build records
is the highest versioned symbol the dynamically linked host binaries of the same build reference. `capsule/STATIC_LINK_RECORD.txt`,
`capsule/THIRD_PARTY_NOTICES.md`.

**76. `OPEN_ITEMS`, named in an earlier capsule notice, resolves nowhere.** It was the release desk's own record and is not in the
package; the notice no longer refers to it. The root `THIRD_PARTY_NOTICES.md` rows it asked for are part of the commit that adds
this package (question 47).

**77. Why does `oracle/final/august_inputs/manifest.json` state the rule as "if r+offset >= 712 use -offset" without the lower
bound?** The oracle's record was written for rows 600 to 711, where `r + offset` is never negative (the smallest is 585), so the
one-sided text is exact for that set; `rule.rs` and `check_offset_rule` state both bounds and are the normative form (question 37).

**78. Has anyone re-proved a row from the package alone, on a machine that started with nothing?** Yes, once, on 8 September 2026:
a freshly launched Lambda A100-SXM4-40GB instance (Ubuntu 22.04.5; no Rust, SP1 or protoc installed) ran `replicate.sh all` against
a local copy of the package and the row-600 frame. The toolchains installed at their pinned digests, the build reproduced the pinned
ELF and key, all 112 proofs verified under both verifiers, row 600 re-executed to the identical statement on the CPU in 7 minutes and
was re-proved on the GPU in 42.3 minutes, and the fresh proof was accepted cold under the pinned identities. The proof bytes differ
from the batch's, as Groth16 proofs are randomised; the 752 public bytes are the same. `VERIFY.md` section 9,
`replicate/TEST_LOG_LAMBDA_A100.md`, and the run's artefacts under `replicate/lambda_a100_20260908/`.

## The third reading

**79. Why do the acceptance reports count 35 checks in verify mode and 33 in execute mode?** The two absent in execute mode are
`circuit.groth16_vk_sha256` and `groth16.verify`: an execution proves nothing, so there is no proof and no circuit key to check;
the other 33 checks (layout, identities, rule, digests, sums) are the same in both modes (`receipts/row_000600_verify.json`
against an execute-mode receipt such as `replicate/lambda_a100_20260908/execute_600/row_000600/receipt.json`).

**80. The frozen table's `sources` block gives `build_record.sha256` `f09c8dae…` and `g1_manifest.sha256` `3e69c6cd…`, but the
published files hash differently.** Those are the digests of the private bytes the table was frozen against on 7 September,
recorded before the copies' paths were redacted; `REDACTION_LEDGER.tsv` pairs each with its published digest (`ac451a7b…` for
`source/armc-relation/runs/build_record_20260907T214246Z.txt`, `95fcf7ec…` for `oracle/final/august_inputs/manifest.json`), and
`PINS.json` records the table's own as-frozen and published digests (question 71 covers `prepare_manifest`).

**81. What is the ZeeBeam row-96 artifact the twelve relation controls mutate, and where is it?** `bundle/proofs_20260902/row_096_groth16.bin`
in the public ZeeBeam repository (github.com/poliebotics/zeebeam), 2,779 bytes, SHA-256 `62f113eca2c59970b54890bc6857ac527ecfde94487b4fba7263c325db32f936`
(`source/logs/verify_groth16_only_row096_20260907.json` records the same bytes and digest).

**82. Can the checkpoint be retrained from the published material?** No. The checkpoint, the trainer and its log and the
evaluation-row caches (`oracle/rows/d2/`, `oracle/rows/v10/`, `oracle/rows_august/`) are published; the training-block caches and
the frames of rows 0 to 599 and of the d2 and v10 sessions are not, and no claim in this package rests on retraining.

**83. Why is Astra round 8 (18:01) dated before round 7 (18:08)?** The two ran concurrently on the same frozen bytes, the privacy
sweep (round 7) and the confirmation re-read of the round-6 dispositions (round 8); round 8's verdict landed first, neither saw the
other's findings, and both sets of dispositions were applied together in the revision that followed (`AUDIT_TRAIL.md`, "After
rounds 7 and 8 and the second reading").

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-08 | BOSUN | First version, answering the outside-agent readability audits (the first reading, A1). |
| 1.1 | 2026-09-08 | BOSUN | The frames' publication and what they show (16), the cache (21), the four training-row hints (31), the audits after round 6 (43), the patent notice (46), the root licence files (47), the data layer (49), the exit diagnostics (61); the second reading answered (65 to 77). |
| 1.2 | 2026-09-08 | BOSUN | The fresh-machine replication (question 78; 62a updated). |
| 1.3 | 2026-09-08 | BOSUN | Astra round 9: the pending-decision label reads 'not decided at publication' wherever it appears. |
| 1.4 | 2026-09-08 | BOSUN | Third outside reading: question 35 names the eight policy-only rows; questions 79 to 83 (check counts, the frozen table's provenance digests, the row-96 artifact, retraining, the order of rounds 7 and 8). |
| 1.5 | 2026-09-08 | BOSUN | Astra round 11: question 43 covers rounds 9 and 10 and the third reading; the audit inventory rendered from audits/. |
