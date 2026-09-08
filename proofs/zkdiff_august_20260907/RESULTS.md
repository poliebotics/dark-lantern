---
version: 1.3
date: 2026-09-08
status: development validation, integer agreement, guest parity and the proof batch; sections 1 to 5 are frozen records, section 6 is rendered from the proof collection by fill_results.py; the quick-screen rows corrected and three explanations added after the outside-agent readability audits
author: BOSUN for Cathal Ryan Hynes
---

# Results

Every number below is copied from a named record in this package. Sections 1 to 5 were fixed before the proofs were made
and describe the model, its integer form and the program; section 6 is the proof batch itself, rendered mechanically
from the merged batch manifest and the receipts. Read them under `CLAIM_BOUNDARY.md`: the d2/v10 evaluation blocks are
development validation, the August rows 600 to 711 were held out from weight training and seven of them entered the
quantisation calibration, and the proofs establish execution binding and nothing wider.

## 1. Development validation of the proof model (frozen ARM-C protocol, float, the A100 evaluator)

Source: `model/g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pubproto_eval.json` (the frozen protocol evaluator's output
on the node, torch 2.7.0, bf16 autocast) and `model/training/eval.log`. Checkpoint SHA-256
`c6955192067c8df1f46960f4803b32eac1c037b84a0f40de3b265b739d85fab8` as trained (the published copy, `9cf16eae…`, is a
documented derivative with three private path strings rewritten in its training arguments and every tensor verified equal,
`REDACTION.md`), step 24,000, ARM-C base width 16, multipliers
(1, 2, 4, 4), 14 hint channels, 1,114,500 parameters, no crop (the full sensor frame area-resized to 96 x 112, the
emission resized and never cropped). Protocol: timestep 150, wrong offsets -2, +2, -15, +15, +30, stride 1, seed
20260823, one noise generator per session seeded once with the protocol seed and one draw per row in row order; d2
1,200 rows in three contiguous evaluation blocks of 400, v10 500 rows in two blocks of 250. The statistic per row is the
squared-residual score under each conditioning; "paired" is the fraction of rows whose correct score lies below the mean
of the five wrong scores; AUROC pools correct scores against the per-row wrong means within a session (and, per offset,
against that offset's scores).

| session | rows | correct | wrong -2 | wrong +2 | wrong -15 | wrong +15 | wrong +30 | mean wrong minus correct (95 % CI) | paired | AUROC (avg, and each offset) |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| d2 | 1200 | 0.011046502285947403 | 0.03353550140590717 | 0.03353922729380429 | 0.03340078694590678 | 0.03337452464581778 | 0.03342817478813231 | 0.022409140729966262 (0.02223461917351233 to 0.02258505066501675) | 1.0 | 1.0; 1.0, 1.0, 1.0, 1.0, 1.0 |
| v10 | 500 | 0.012672666400671006 | 0.035945416271686556 | 0.03600847250595689 | 0.03604931791871786 | 0.03606675029918551 | 0.03598400325700641 | 0.023338125649839638 (0.023233263800683038 to 0.02345501385294235) | 1.0 | 1.0; 1.0, 1.0, 1.0, 1.0, 1.0 |

Training record (`model/training/train.log`): August training rows limited to [0, 600), rows 600 to 711 withheld from training;
8,035 training rows (d2 4,432, v10 3,003, August 600); the model seeded before construction (trainer v3); loss
0.009507169357966631 at step 24,000 after 1,899.5 s on eight A100-SXM4-80GB. The trainer's own quick screen at step
24,000 (its noise stream is the quick screen's, `999 + r`, not the frozen evaluator's): d2 27 rows, correct
0.010886497036726386, wrong 0.033209938280008455, paired 1.0; v10 10 rows, correct 0.012369831185787916, wrong
0.03519340101629496, paired 1.0; August 28 rows, correct 0.007000325546999063, wrong 0.016603018456537808, paired 1.0.
The screen's August rows are `range(30, 682, 24)` (`oracle/trainer/train_lean.py` `eval_rows`): 30, 54, ..., 678, of which
twenty-four are training rows below 600 and four are proof rows (606, 630, 654, 678). An earlier revision of this section
called all 28 held-out rows; the four are the rows of the proof set the screen saw, and they were seen as a printed line
per 2,000 steps, not used for weights or for choosing the checkpoint (`FAQ.md` 23). The claim boundary records the
consultation. No random-network or shuffled-hint baseline was computed for this package; the chance level of AUROC and of
the paired fraction is 0.5 (`FAQ.md` 26).

## 2. The ARM-C ladder around the proof model (development validation)

The proof model was one of sixteen trainer-v3 ARM-C variants trained under the same protocol on the same node the same
day (`model/ladder/G0E_SUMMARY.json`, `model/ladder/G0F_SUMMARY.json`, with each variant's `pubproto_eval.json` under
`model/ladder/`). Every one reaches paired fraction 1.0000 on both sessions and AUROC at least 0.999784; every width
reaches AUROC 1.000000 on both sessions at 48,000 steps or more. The selection of the width-16, 96 x 112, seed-20260908,
24,000-step checkpoint as the proof model was made on these d2/v10 numbers, which is why those blocks are development
validation and not a test set. Earlier sweeps of the day, including other architectures and the runs whose seed label
did not fix the initial weights (the trainer seeded after model construction before v3), are held on-box and are not part
of this record. No written criterion chose the proof model among the variants of the table; the record's timestamps show that the
seed-20260908 24,000-step checkpoint of the recommended width-16 96 x 112 family was the first to finish and pass on both
blocks, that the integer oracle was frozen from it that evening, and that the 48,000- and 96,000-step arms finished later
(`FAQ.md` 30) **[derived]**.

| variant | parameters | step | d2 AUROC | d2 paired | d2 delta | v10 AUROC | v10 paired | v10 delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| g0e_armc_b12_96x112_cd0_aug_s20260907_24k | 629,092 | 24000 | 0.999952 | 1.0000 | 6.297e-03 | 0.999784 | 1.0000 | 6.085e-03 |
| g0e_armc_b12_96x112_cd0_aug_s20260908_24k | 629,092 | 24000 | 1.000000 | 1.0000 | 7.431e-03 | 1.000000 | 1.0000 | 7.268e-03 |
| g0e_armc_b16_48x56_cd0_aug_s20260907_24k | 1,114,500 | 24000 | 1.000000 | 1.0000 | 1.481e-02 | 1.000000 | 1.0000 | 1.545e-02 |
| g0e_armc_b16_48x56_cd0_aug_s20260908_24k | 1,114,500 | 24000 | 1.000000 | 1.0000 | 1.463e-02 | 1.000000 | 1.0000 | 1.515e-02 |
| g0e_armc_b16_96x112_cd0_aug_s20260907_24k | 1,114,500 | 24000 | 1.000000 | 1.0000 | 2.048e-02 | 1.000000 | 1.0000 | 2.154e-02 |
| g0e_armc_b16_96x112_cd0_aug_s20260907_48k | 1,114,500 | 48000 | 1.000000 | 1.0000 | 2.837e-02 | 1.000000 | 1.0000 | 3.070e-02 |
| **g0e_armc_b16_96x112_cd0_aug_s20260908_24k** (the proof model) | 1,114,500 | 24000 | 1.000000 | 1.0000 | 2.241e-02 | 1.000000 | 1.0000 | 2.334e-02 |
| g0e_armc_b16_96x112_cd0_aug_s20260909_24k | 1,114,500 | 24000 | 1.000000 | 1.0000 | 2.004e-02 | 1.000000 | 1.0000 | 2.065e-02 |
| g0f_armc_b12_48x56_cd0_aug_s20260907_48k | 629,092 | 48000 | 1.000000 | 1.0000 | 1.562e-02 | 1.000000 | 1.0000 | 1.597e-02 |
| g0f_armc_b12_96x112_cd0_aug_s20260907_48k | 629,092 | 48000 | 1.000000 | 1.0000 | 1.992e-02 | 1.000000 | 1.0000 | 2.033e-02 |
| g0f_armc_b12_96x112_cd0_aug_s20260909_24k | 629,092 | 24000 | 0.999999 | 1.0000 | 6.949e-03 | 0.999936 | 1.0000 | 6.535e-03 |
| g0f_armc_b16_48x56_cd0_aug_s20260907_48k | 1,114,500 | 48000 | 1.000000 | 1.0000 | 2.413e-02 | 1.000000 | 1.0000 | 2.600e-02 |
| g0f_armc_b16_96x112_cd0_aug_s20260907_96k | 1,114,500 | 96000 | 1.000000 | 1.0000 | 3.328e-02 | 1.000000 | 1.0000 | 3.625e-02 |
| g0f_armc_b8_48x56_cd0_aug_s20260907_96k | 281,540 | 96000 | 1.000000 | 1.0000 | 1.748e-02 | 1.000000 | 1.0000 | 1.838e-02 |
| g0f_armc_b8_96x112_cd0_aug_s20260907_48k | 281,540 | 48000 | 1.000000 | 1.0000 | 1.331e-02 | 1.000000 | 1.0000 | 1.306e-02 |
| g0f_armc_b8_96x112_cd0_aug_s20260907_96k | 281,540 | 96000 | 1.000000 | 1.0000 | 2.109e-02 | 1.000000 | 1.0000 | 2.208e-02 |

The variant names encode architecture (`armc`), base width (`b8`, `b12`, `b16`), resolution, hint dropout 0 (`cd0`),
August rows 0 to 599 in training (`aug`), the seed and the step count; `delta` is the mean of the wrong scores minus the
correct score in MSE units.

## 3. Integer agreement (the oracle's contract and the FINAL artifact)

Source: `oracle/final/README_FINAL.md` sections 2, 7a and 7b, `oracle/final/FREEZE_SUMMARY.md`, `oracle/final/AGREEMENT.md`,
`oracle/final/agreement*.json`. The integer path covers the whole relation from the quantised inputs to the residual
sum; `D_q = R_w^q - R_c^q` is the integer margin and `η = |R_w^q - R_w^f| + |R_c^q - R_c^f|` the residual-unit error
against the reference, both in MSE units; the acceptance rule was `D_q > 3η` on every pair.

Positive control against the frozen evaluator (222 scores, 37 protocol rows under six conditions): the fp32
reproduction is systematically 3.9e-3 low (relative median 3.27e-3, max 1.10e-2); the bf16-autocast emulations remove
the bias (relative median 1.13e-3 and 1.14e-3, signed mean -5.39e-4 and -5.86e-4, max 6.20e-3 and 4.74e-3). The
evaluator's own margins on the 37 rows: paired 37/37, minimum 0.019623, median 0.022479. The bf16 rounding-point
fidelity of the A100 run is unresolved at the 1.1e-3 level (README_FINAL section 2).

| scheme | reference | sign agreement | paired (integer / reference) | D_q/η min / p5 / median / p95 / max | pairs with D_q > 3η | score error, relative median / max (signed mean) | η median / max | weakest pair |
|---|---|---:|---:|---|---:|---|---|---|
| **int16** (the proved scheme) | evaluator | **185/185** | 37/37 | **79.8** / 92.3 / 128.8 / 201.8 / 288.2 | **185/185** | 3.13e-3 / 1.02e-2 (-3.57e-3) | 1.73e-4 / 2.97e-4 | d2 2866 +2: D_q 0.023552, η 2.95e-4 |
| int16 | fp32 | 185/185 | 37/37 | 547.5 / 669.5 / 1248 / 3804 / 16998 | 185/185 | 2.81e-4 / 1.70e-3 (+2.80e-4) | 1.80e-5 / 3.79e-5 | d2 2986 +15 |
| int8 (cost option, not proved) | evaluator | 185/185 | 37/37 | 19.2 / 23.1 / 32.7 / 46.7 / 69.0 | 185/185 | 1.10e-2 / 4.70e-2 (+1.39e-2) | 6.97e-4 / 1.10e-3 | d2 1608 -15: D_q 0.020142, η 1.05e-3 |

Per offset (int16 against the evaluator, all 37/37): minimum D_q/η -2 92.2, +2 79.8, -15 89.2, +15 83.3, +30 92.8; per
session d2 79.8, v10 80.6. Integer margin D_q: int16 minimum 0.018699, median 0.022535. Pooled AUROC on the 37-row
subset 1.000 for both sessions in float and both integer schemes; no reversal against any reference. Zero clip events
in all 444 integer forwards; the largest observed convolution accumulator 34 bits (int16) against a static bound of 39
bits (353,174,814,720); the requantisation expression bound 3,812,976,885,203,206,144 (below 2^63). Network-only error
(integer against a float64 network on the integer inputs): int16 +4.2e-4 relative (std 4.4e-4, max 2.4e-3).

August proof rows 600 to 711, integer and fp32 (no evaluator reference exists for them), noise by the normative rule,
all five protocol offsets plus the mirrored -30 where the rule needs it, 507 (row, offset) pairs (every pair whose wrong
row's hint was available: -2 on 111 rows, +2 on 110, -15 on 101, +15 on 97, +30 on 82, and -30 on the 6 mirrored rows;
`FAQ.md` 31):

| scheme | rule pairs | rule D_q (MSE) min / p5 / p25 / median / p75 / p95 / max (mean) | fp32 D_f min / median | D_q/η_fp32 min / median | rule sign integer + / fp32 + / agree | all pairs integer c < w / fp32 c < w | minimum D_q, any pair | clips |
|---|---:|---|---|---|---|---|---:|---:|
| **int16** | 112 | **0.007328** / 0.008141 / 0.008778 / **0.009161** / 0.009850 / 0.010578 / 0.010988 (0.009259) | 0.007328 / 0.009165 | 267.7 / 518.3 | **112 / 112 / 112** | **507 / 507** | 0.006776 | 0 |
| int8 | 112 | 0.007321 / 0.008166 / 0.008794 / 0.009174 / 0.009846 / 0.010591 / 0.010998 (0.009278) | same | 8.6 / 11.0 | 112 / 112 / 112 | 507 / 507 | 0.006788 | 0 |

The weakest int16 rule pair is row 709 at the mirrored offset -30 (correct sum 4,799,388,897, wrong 10,087,236,535,
D_q 0.007328, η against fp32 2.3e-5, ratio 317). The ten mirrored rows' rule D_q (int16): 684 0.008937, 689 0.008666,
694 0.010640, 698 0.009246, 699 0.009105, 703 0.008651, 704 0.008935, 708 0.009502, 709 0.007328, 711 0.009582. The
four rows whose wrong hint is a training row: 600 at -2 (hint 598) D_q 0.009450 (correct 4,435,539,299, wrong
11,254,163,581, η 6.2e-6, ratio 1529); 602 at -15 (587) 0.010450; 607 at -15 (592) 0.009450; 612 at -15 (597)
0.010528; fp32 agrees in sign on all four. Integer correct residuals on the August rows lie in 0.006078 to 0.008437 MSE
units (median 0.006965), about half the d2/v10 level, and the wrong residuals in 0.013980 to 0.019355 (median 0.016228);
the medians are over the 112 receipts' `r_correct`, `r_wrong` and `difference` in MSE units. The August margins (median
0.009161) are smaller than the protocol rows' (0.022535) both in absolute terms and relative to the correct residual: on
the August rows the wrong residual is about 2.3 times the correct one and the margin about 1.3 times it (medians of the
per-row ratios 2.32 and 1.32), whereas on the protocol rows the evaluator's mean wrong score is about 3.0 times its
correct score (section 1, d2: 0.0335 against 0.0110) and the integer margin about 2.0 times it. Each row's expected int16 residual sums for the correct and rule-pair conditions are in
`oracle/final/august_inputs/manifest.json`, and the acceptance verifier compares every proved statement's `R_correct` and
`R_wrong` with them (checks `oracle.r_correct`, `oracle.r_wrong`).

## 4. Rust parity, guest execution and negative controls (before proving)

Source: `source/FULL_GUEST.md` sections 1, 4, 5 and 4.6; the logs under `source/logs/` and `source/armc-relation/runs/`.

Parity of the Rust kernels against the oracle: d2 row 1328 through the adapter with the FINAL blob reproduces the
oracle's residual sums 8,764,459,045 (correct) and 22,311,372,969 (wrong +2) with zero clip events; all eight FINAL
vector sets (d2 1328 and August 650, correct and wrong +2, int16 and int8) agree layer by layer on 188 of 188 outputs,
effective scales and residual sums, with clip counts equal to the oracle's (0); all 42 boundary fixtures pass, expected
values and counters (`source/logs/test_armc_int_r5.log`, 25 tests; the relation workspace 59 tests). Every table, mask,
exponent table, weight, multiplier, bias, GroupNorm array and coordinate plane in the blob matches the manifest hashes.

The complete guest on August rows 600 to 603 (SP1 6.4.0 CPU executor, ELF `51b7bc35…75cc`, the FINAL blob,
`source/armc-relation/runs/batch_execute_r5_20260907/`): guest bytes equal to the native re-execution (752/752), every
acceptance check PASS under the frozen identities, `R_correct` and `R_wrong` equal to the Python oracle's and the G1
expected sums, clip events 0.

| row | offset | rule | wrong row | R_correct | R_wrong | D | class | instructions |
|---:|---:|---|---:|---:|---:|---:|---|---:|
| 600 | -2 | direct | 598 | 4,435,539,299 | 11,254,163,581 | +6,818,624,282 | positive | 14,400,363,198 |
| 601 | +2 | direct | 603 | 4,823,951,305 | 11,932,687,322 | +7,108,736,017 | positive | 14,400,345,341 |
| 602 | -15 | direct | 587 | 4,590,007,358 | 12,130,484,180 | +7,540,476,822 | positive | 14,400,313,902 |
| 603 | +15 | direct | 618 | 5,122,027,412 | 10,802,701,224 | +5,680,673,812 | positive | 14,400,340,066 |

Instruction count of one row (600), 14,400,363,198 in total with 269,904 syscalls, by cycle-tracker region: relation
14,147,343,155; `denoiser_correct` 3,455,557,627; `denoiser_wrong` 3,455,557,224; `emission_render_u` 2,143,636,640;
`emission_render_r` 2,143,611,423; `frame_reduce` 1,980,085,474; `raw_blake3_24MB` 697,810,935; `hints` 257,096,202;
`constants_blob` 252,852,645; `previous_advance_leg` 4,912,904; `drand_verify` 4,904,530; `noise` 3,657,240;
`constants` 260,149; `ordered_session_membership` 223,389; `public_commitment` 42,387; `parse_witness` 5,993;
`private_input` 603. Rows vary by data-dependent control flow in the 10^-5 range. A mirrored -30 statement ran through
the complete guest on a synthetic 40-row session built from real quicknet beacons (14,400,234,352 instructions; the
mirror path exercised end to end on a conditioning that has nothing to do with the frame, so that statement's residual
sums carry no result meaning and are not a result of this package), and the real row 684's prepared witness
passed the offset check and every leg up to the frame hash on the development machine, which did not hold that frame at the time of this execution. On
the node, before the batch, the complete guest executed row 684 with its frame: offset -30, rule mirrored (public byte 11
= 1), wrong row 654, R_correct 4,587,519,841, R_wrong 11,036,216,072, D +6,448,696,231, clip events 0,
14,400,373,541 instructions, native re-execution equal, accepted under the frozen identities (33 checks); the record is
the node's execute receipt (`source/node_prep/r5/execute_684_receipt.json`).

Negative controls (`source/armc-relation/runs/controls_r5_20260907/CONTROLS.json`, `all_behaved: true`): 23 witness-level
controls on the FINAL network, each refused at the named layer, relation rejections (a raw byte, the header state, the
round, the signatures, the predecessor state, the wrong-row state, either sibling, another row's leaf, a blob header
byte, a mirror flag on a direct row, -30 direct, +30 mirrored, and the row-684 relabellings) distinguished from policy
rejections (a coherent alternative offset with its matching leaf, a flipped noise byte, a byte deep inside the blob:
each a different valid statement, refused only by the frozen identities). Proof-level controls: twelve relation-level
mutations of a real SP1 6.4.0 Groth16 artifact of another program (the ZeeBeam row-96 proof) all rejected by the
Groth16 layer (`source/logs/verify_groth16_only_row096_final_20260907.json`); the policy-level controls against this
package's own proofs are the node's `receipts/proof_controls.json`.

## 5. Proving cost, as measured on the node (timing only)

A timing pilot proved one row (600) on the node before the final ELF was pinned; it ran the round-4 ELF, which round 5
superseded on the mirrored-offset rule, and executed 14,400,363,229 instructions for that row against the final ELF's
14,400,363,198. Its proof is not part of this package; its measurements of the proving stack are the only ones that
existed before the batch and are quoted as such (source: the pilot report, on-box). One NVIDIA A100-SXM4-80GB (driver
570.148.08, CUDA runtime 12.8.90), `sp1-gpu-server` 6.4.0 (SHA-256 `f68b85dc…d97c`), circuit v6.1.0: the `.groth16()`
call took 2,753,387 ms (45.89 min), of which core and recursion 2,708.4 s (45.14 min) and the gnark Groth16 stage
44.7 s (15,972,262 constraints); cold start with CPU and CUDA setup 46.5 s; GPU memory peak 28,433 MiB of 81,920;
`sp1-gpu-server` peak RSS 28.21 GiB, client 6.83 GiB; cold verification on the node 22.0 s with the key recomputed from
the ELF, standalone verification 364 ms; a rate of 191 s per billion instructions. The batch's own times are in section 6
(`prove_elapsed_ms` per row) and in `receipts/`. A later single-row replication from the package alone, on a freshly rented
A100-SXM4-40GB (8 September, `replicate/TEST_LOG_LAMBDA_A100.md`), proved row 600 in 2,539,814 ms (42.3 min) with a GPU memory
peak of 28,435 MiB of 40,960 and the same 15,972,262 constraints; its 752 public bytes equal the batch's statement for the row.

## 6. The proof batch

<!-- BATCH_COUNTS_BEGIN -->
112 proofs, one per row 600 to 711, every one verified and accepted under the frozen identities: 112 positive, 0 zero and 0 negative signed outcomes; 0 rows with a nonzero clip count.
<!-- BATCH_COUNTS_END -->

Per row, from `receipts/BATCH_MANIFEST_merged.json` and the receipts, cross-checked against the decoded public bytes and
`PINS.json` by `fill_results.py` before rendering: the declared offset and rule, the wrong row, the two residual sums,
their signed difference in integer and MSE units, the outcome class, the clip count, the `.groth16()` time and the leading
sixteen hex digits of the raw proof's and the statement's SHA-256 (full digests in `PINS.json` `batch.proofs` and in the
receipts). Nothing is filtered: every row of the rule appears, whatever its sign.

<!-- BATCH_TABLE_BEGIN -->
| row | offset | rule | wrong row | R_correct | R_wrong | D = R_wrong - R_correct | D (MSE units) | class | clip events | prove (min) | raw proof sha256 (first 16) | public values sha256 (first 16) |
|---:|---:|---|---:|---:|---:|---:|---:|---|---:|---:|---|---|
| 600 | -2 | direct | 598 | 4,435,539,299 | 11,254,163,581 | +6,818,624,282 | +0.009450 | positive | 0 | 65.29 | `f9b2f91a28551a5e` | `26b5b2d36f921151` |
| 601 | +2 | direct | 603 | 4,823,951,305 | 11,932,687,322 | +7,108,736,017 | +0.009852 | positive | 0 | 65.15 | `422ab6528be31cb9` | `e29f89764e5b071d` |
| 602 | -15 | direct | 587 | 4,590,007,358 | 12,130,484,180 | +7,540,476,822 | +0.010450 | positive | 0 | 65.53 | `f2fa24533dcbeed9` | `554b3145af5b874b` |
| 603 | +15 | direct | 618 | 5,122,027,412 | 10,802,701,224 | +5,680,673,812 | +0.007873 | positive | 0 | 64.73 | `9253de75e0297559` | `d6560603e0c041b1` |
| 604 | +30 | direct | 634 | 6,087,916,494 | 13,965,371,628 | +7,877,455,134 | +0.010917 | positive | 0 | 64.79 | `345690d67d52bbb8` | `08c950b2a0367e58` |
| 605 | -2 | direct | 603 | 4,916,531,444 | 11,288,421,007 | +6,371,889,563 | +0.008831 | positive | 0 | 64.46 | `d5c79936de3dc1e0` | `04c7ac063ad5a467` |
| 606 | +2 | direct | 608 | 5,024,470,742 | 11,104,550,773 | +6,080,080,031 | +0.008426 | positive | 0 | 64.57 | `0ce2a167e4aac668` | `406bec7a0833bdef` |
| 607 | -15 | direct | 592 | 4,735,687,836 | 11,554,387,355 | +6,818,699,519 | +0.009450 | positive | 0 | 65.06 | `19cbf9a095558d4e` | `60ed136c150b8274` |
| 608 | +15 | direct | 623 | 4,871,001,070 | 11,908,069,780 | +7,037,068,710 | +0.009753 | positive | 0 | 64.58 | `b058fa4a29cd74c4` | `5ad9dd0b7a582fa7` |
| 609 | +30 | direct | 639 | 4,507,374,860 | 11,130,879,841 | +6,623,504,981 | +0.009179 | positive | 0 | 64.75 | `dc39dcabe199c1a7` | `0e96a3cc4f1e17d4` |
| 610 | -2 | direct | 608 | 4,666,536,664 | 11,186,278,937 | +6,519,742,273 | +0.009036 | positive | 0 | 65.21 | `be08dceba70c2d21` | `78d2395201346199` |
| 611 | +2 | direct | 613 | 4,575,288,521 | 10,983,802,241 | +6,408,513,720 | +0.008882 | positive | 0 | 65.25 | `798e11346e5b9420` | `42a0a2f92ba2abaa` |
| 612 | -15 | direct | 597 | 5,358,209,283 | 12,954,561,242 | +7,596,351,959 | +0.010528 | positive | 0 | 65.02 | `c2e9e47ea74a9291` | `ceaecdf7626dd270` |
| 613 | +15 | direct | 628 | 4,824,158,933 | 11,257,462,199 | +6,433,303,266 | +0.008916 | positive | 0 | 64.78 | `c06431910eec77c4` | `aeffc014d7828ce3` |
| 614 | +30 | direct | 644 | 4,572,016,948 | 11,845,443,551 | +7,273,426,603 | +0.010080 | positive | 0 | 65.44 | `5751e6cda3dd4c6e` | `5bd62c92b01bb741` |
| 615 | -2 | direct | 613 | 4,523,859,619 | 10,490,701,351 | +5,966,841,732 | +0.008269 | positive | 0 | 65.77 | `94efc878d74257a0` | `23cbc110aada3cfb` |
| 616 | +2 | direct | 618 | 4,385,706,399 | 10,431,058,590 | +6,045,352,191 | +0.008378 | positive | 0 | 65.49 | `c525a98d2ae4d6d6` | `b7354654b9867923` |
| 617 | -15 | direct | 602 | 4,559,463,982 | 11,843,717,253 | +7,284,253,271 | +0.010095 | positive | 0 | 64.30 | `8b5a9347873b61c1` | `d6bf212fc4cbd687` |
| 618 | +15 | direct | 633 | 4,902,469,556 | 11,633,425,888 | +6,730,956,332 | +0.009328 | positive | 0 | 64.63 | `2e3989e040dbab42` | `dc5a6015b8cdb3a7` |
| 619 | +30 | direct | 649 | 5,067,769,469 | 11,067,017,234 | +5,999,247,765 | +0.008314 | positive | 0 | 64.72 | `4953147488dd6429` | `d460c523603f7074` |
| 620 | -2 | direct | 618 | 4,975,330,749 | 10,815,397,450 | +5,840,066,701 | +0.008094 | positive | 0 | 64.79 | `899eb9935522b3fc` | `5947eb506fd1d60d` |
| 621 | +2 | direct | 623 | 5,078,590,739 | 11,613,945,121 | +6,535,354,382 | +0.009057 | positive | 0 | 64.28 | `197074ecc91a40ae` | `b88003da7cc4536a` |
| 622 | -15 | direct | 607 | 4,543,818,957 | 10,585,596,819 | +6,041,777,862 | +0.008373 | positive | 0 | 64.92 | `ccc6c2d8102a6fd9` | `4f0d142d4d9ab095` |
| 623 | +15 | direct | 638 | 4,949,557,373 | 11,748,174,166 | +6,798,616,793 | +0.009422 | positive | 0 | 64.15 | `77bbdb1df39d864f` | `5625cac5b4bbbc7a` |
| 624 | +30 | direct | 654 | 4,613,443,525 | 10,838,962,138 | +6,225,518,613 | +0.008628 | positive | 0 | 64.53 | `1cbc3736778efc2f` | `e0a6f66ed917ec1a` |
| 625 | -2 | direct | 623 | 5,159,255,376 | 11,331,522,376 | +6,172,267,000 | +0.008554 | positive | 0 | 64.44 | `d37989c8d1020a5b` | `bf35635a40d0a3b3` |
| 626 | +2 | direct | 628 | 4,843,714,129 | 10,935,809,038 | +6,092,094,909 | +0.008443 | positive | 0 | 64.28 | `1b38fa804dce6880` | `79b357ea5e79ce49` |
| 627 | -15 | direct | 612 | 4,558,621,865 | 11,969,286,046 | +7,410,664,181 | +0.010270 | positive | 0 | 64.32 | `b7d8e6838b2eda34` | `7a4e438249a8c12a` |
| 628 | +15 | direct | 643 | 4,935,201,030 | 10,418,339,413 | +5,483,138,383 | +0.007599 | positive | 0 | 64.95 | `0367a1861cb8df8e` | `94fb249ad3a80a5f` |
| 629 | +30 | direct | 659 | 5,125,105,340 | 11,961,003,020 | +6,835,897,680 | +0.009474 | positive | 0 | 64.82 | `ff72697dcd8e0ece` | `e64dbc9c789570d4` |
| 630 | -2 | direct | 628 | 5,309,320,039 | 12,604,837,717 | +7,295,517,678 | +0.010111 | positive | 0 | 65.35 | `b04bda23f712dfa0` | `694312823b400d81` |
| 631 | +2 | direct | 633 | 5,466,745,821 | 11,825,143,468 | +6,358,397,647 | +0.008812 | positive | 0 | 64.29 | `1641d17c4f82ff62` | `8fb56c3d31503ec3` |
| 632 | -15 | direct | 617 | 5,265,645,292 | 12,677,834,296 | +7,412,189,004 | +0.010273 | positive | 0 | 64.74 | `6844cb5782730675` | `328253890e93c294` |
| 633 | +15 | direct | 648 | 4,726,823,114 | 10,639,899,484 | +5,913,076,370 | +0.008195 | positive | 0 | 65.11 | `0ee2e586b76bbe0e` | `acc61e7f109e8a23` |
| 634 | +30 | direct | 664 | 5,346,587,528 | 12,284,667,227 | +6,938,079,699 | +0.009615 | positive | 0 | 64.66 | `ff69ce8e041c98b6` | `ab90f46e6d9cbc08` |
| 635 | -2 | direct | 633 | 5,062,785,011 | 12,528,591,567 | +7,465,806,556 | +0.010347 | positive | 0 | 64.23 | `596faa01b40ccbbe` | `b432b18ec7996582` |
| 636 | +2 | direct | 638 | 5,443,361,617 | 11,779,201,602 | +6,335,839,985 | +0.008781 | positive | 0 | 64.35 | `e816bc97b5c60a17` | `6f8b7d7fca94f933` |
| 637 | -15 | direct | 622 | 4,916,494,426 | 11,310,239,419 | +6,393,744,993 | +0.008861 | positive | 0 | 64.20 | `6050bb4c9de7bece` | `e9c5e199acc99be5` |
| 638 | +15 | direct | 653 | 5,285,402,432 | 11,305,743,967 | +6,020,341,535 | +0.008344 | positive | 0 | 64.53 | `dcc9d20399add051` | `f73806f76ce084d5` |
| 639 | +30 | direct | 669 | 5,126,532,295 | 12,608,218,338 | +7,481,686,043 | +0.010369 | positive | 0 | 64.31 | `81f8232af1ee0726` | `10df80fbaccb2c9d` |
| 640 | -2 | direct | 638 | 4,897,285,821 | 11,342,739,182 | +6,445,453,361 | +0.008933 | positive | 0 | 64.18 | `451d49a077374f06` | `e3fae3ea2bc3ab4a` |
| 641 | +2 | direct | 643 | 5,075,860,465 | 11,457,031,477 | +6,381,171,012 | +0.008844 | positive | 0 | 64.48 | `c30dd3414f6983f7` | `da9d4d3a3f7c09f2` |
| 642 | -15 | direct | 627 | 4,749,560,133 | 12,091,512,892 | +7,341,952,759 | +0.010175 | positive | 0 | 64.12 | `72628e8e088aa771` | `177ab75601458ffa` |
| 643 | +15 | direct | 658 | 4,898,813,215 | 11,684,457,167 | +6,785,643,952 | +0.009404 | positive | 0 | 64.32 | `0397d666bd7ffdcf` | `d1862967931cfcce` |
| 644 | +30 | direct | 674 | 5,533,324,021 | 11,818,908,152 | +6,285,584,131 | +0.008711 | positive | 0 | 64.61 | `d9c536c0fba6752d` | `dad127163818ee99` |
| 645 | -2 | direct | 643 | 5,026,142,343 | 11,492,366,229 | +6,466,223,886 | +0.008962 | positive | 0 | 63.59 | `9fea53614ed22f01` | `8669a03ff2b783a7` |
| 646 | +2 | direct | 648 | 5,767,880,674 | 13,499,792,315 | +7,731,911,641 | +0.010716 | positive | 0 | 64.23 | `0f816416b1204542` | `f18de6cb28a51d15` |
| 647 | -15 | direct | 632 | 5,186,397,509 | 13,035,407,960 | +7,849,010,451 | +0.010878 | positive | 0 | 64.20 | `4198fded1ceb02b7` | `fe73108682684695` |
| 648 | +15 | direct | 663 | 5,192,224,437 | 12,040,281,607 | +6,848,057,170 | +0.009491 | positive | 0 | 64.85 | `acbce3a0f00a5e44` | `0ebdeea15e18da57` |
| 649 | +30 | direct | 679 | 5,444,954,965 | 12,830,258,671 | +7,385,303,706 | +0.010235 | positive | 0 | 63.99 | `37c441d6331b6d7f` | `9d37e113c0a5a08a` |
| 650 | -2 | direct | 648 | 5,317,378,656 | 12,210,640,988 | +6,893,262,332 | +0.009553 | positive | 0 | 64.59 | `4bf6b95b25f380af` | `7ee3768661b3b99a` |
| 651 | +2 | direct | 653 | 4,998,333,707 | 12,481,092,964 | +7,482,759,257 | +0.010370 | positive | 0 | 64.78 | `ca927c51478437c1` | `2f445648ba0eea14` |
| 652 | -15 | direct | 637 | 5,160,303,390 | 13,088,436,257 | +7,928,132,867 | +0.010988 | positive | 0 | 64.10 | `cefc3e696813209e` | `f43cea8a3e97c75c` |
| 653 | +15 | direct | 668 | 4,868,330,663 | 11,106,040,261 | +6,237,709,598 | +0.008645 | positive | 0 | 64.18 | `f8c8a1d93ceec189` | `2ddf9235d6954719` |
| 654 | +30 | direct | 684 | 5,710,721,466 | 12,644,696,292 | +6,933,974,826 | +0.009610 | positive | 0 | 64.65 | `4f7c5b915f83ac6c` | `44b930ada3ed4f72` |
| 655 | -2 | direct | 653 | 5,750,839,157 | 12,632,159,459 | +6,881,320,302 | +0.009537 | positive | 0 | 64.91 | `61fc1d18f97e765d` | `cf20efa47694b2f5` |
| 656 | +2 | direct | 658 | 5,285,557,464 | 12,035,687,299 | +6,750,129,835 | +0.009355 | positive | 0 | 66.42 | `4508f4f5b46b7082` | `64ab1ad0a75f1db8` |
| 657 | -15 | direct | 642 | 5,434,716,713 | 12,449,114,115 | +7,014,397,402 | +0.009721 | positive | 0 | 65.89 | `fab1518c78ebc41e` | `c486a75f59c7c69d` |
| 658 | +15 | direct | 673 | 4,854,121,203 | 11,334,099,797 | +6,479,978,594 | +0.008981 | positive | 0 | 65.00 | `109e32bc295b76de` | `a67e3c506e0ed20c` |
| 659 | +30 | direct | 689 | 5,725,459,276 | 12,359,208,397 | +6,633,749,121 | +0.009194 | positive | 0 | 65.10 | `2af7362ccc2ea7ee` | `21ab759df2cfa419` |
| 660 | -2 | direct | 658 | 4,896,376,335 | 11,118,396,387 | +6,222,020,052 | +0.008623 | positive | 0 | 64.56 | `bb643028afe757f0` | `687293625216042a` |
| 661 | +2 | direct | 663 | 4,775,594,281 | 12,091,317,850 | +7,315,723,569 | +0.010139 | positive | 0 | 65.41 | `1742c4ff3d2355d9` | `30aeb7a1d6450011` |
| 662 | -15 | direct | 647 | 5,245,969,995 | 11,859,249,110 | +6,613,279,115 | +0.009165 | positive | 0 | 64.32 | `d044d11a28442f5f` | `3d358be8c34752bf` |
| 663 | +15 | direct | 678 | 4,899,953,330 | 10,977,918,290 | +6,077,964,960 | +0.008423 | positive | 0 | 64.17 | `017d623a312fcd82` | `a02c7d85278819cd` |
| 664 | +30 | direct | 694 | 5,302,706,732 | 12,450,397,245 | +7,147,690,513 | +0.009906 | positive | 0 | 64.67 | `b14c325bbad40ac8` | `981be9d1f3bf507b` |
| 665 | -2 | direct | 663 | 5,181,317,442 | 12,954,927,915 | +7,773,610,473 | +0.010773 | positive | 0 | 65.01 | `425a541857146b3d` | `ce5d25974b10fb02` |
| 666 | +2 | direct | 668 | 5,169,597,840 | 11,458,654,389 | +6,289,056,549 | +0.008716 | positive | 0 | 64.33 | `80fea872c6fd8998` | `6b8340cdb98952e1` |
| 667 | -15 | direct | 652 | 5,102,556,492 | 11,530,346,080 | +6,427,789,588 | +0.008908 | positive | 0 | 64.88 | `e6953376bed209ed` | `8461cf2d7e30d5a4` |
| 668 | +15 | direct | 683 | 5,243,871,174 | 11,602,504,638 | +6,358,633,464 | +0.008812 | positive | 0 | 64.87 | `3aabf7d4860e6a86` | `7a5fe1c90b2c6683` |
| 669 | +30 | direct | 699 | 4,561,795,402 | 10,899,698,512 | +6,337,903,110 | +0.008784 | positive | 0 | 62.86 | `81d0b3c799b0773e` | `f556860ddb57f379` |
| 670 | -2 | direct | 668 | 5,083,533,811 | 11,508,376,620 | +6,424,842,809 | +0.008904 | positive | 0 | 66.79 | `4344a0b35832275f` | `628fc8d1a28ca17f` |
| 671 | +2 | direct | 673 | 4,981,975,532 | 11,895,556,447 | +6,913,580,915 | +0.009582 | positive | 0 | 65.68 | `2405283b295194c4` | `b309b853c12fab2e` |
| 672 | -15 | direct | 657 | 5,181,038,543 | 12,691,816,337 | +7,510,777,794 | +0.010409 | positive | 0 | 64.77 | `5c3bdd1cf684115d` | `16175a7dfe495230` |
| 673 | +15 | direct | 688 | 5,280,787,775 | 11,825,438,406 | +6,544,650,631 | +0.009070 | positive | 0 | 65.35 | `a36cdfd93d1f406b` | `4116cf202c19d894` |
| 674 | +30 | direct | 704 | 5,534,719,262 | 11,436,194,599 | +5,901,475,337 | +0.008179 | positive | 0 | 64.59 | `af0b97709550c48d` | `fbdcb1422c775ef5` |
| 675 | -2 | direct | 673 | 5,214,035,176 | 11,396,534,755 | +6,182,499,579 | +0.008568 | positive | 0 | 64.65 | `bad80a204945dfe1` | `6166e105d9e7b2f4` |
| 676 | +2 | direct | 678 | 4,932,609,170 | 10,230,152,149 | +5,297,542,979 | +0.007342 | positive | 0 | 65.03 | `6be8097aa00a71ec` | `a4363fc59af7d8b1` |
| 677 | -15 | direct | 662 | 5,081,773,770 | 12,188,252,622 | +7,106,478,852 | +0.009849 | positive | 0 | 65.00 | `1105d91e552b92a4` | `01dab4bdb6be60cc` |
| 678 | +15 | direct | 693 | 4,730,558,431 | 11,337,324,504 | +6,606,766,073 | +0.009156 | positive | 0 | 64.95 | `cf7ea52596e44d38` | `3bc7e71e447f2c56` |
| 679 | +30 | direct | 709 | 4,934,802,437 | 10,638,182,610 | +5,703,380,173 | +0.007904 | positive | 0 | 64.69 | `b77788af73209c18` | `70b4baab21643c03` |
| 680 | -2 | direct | 678 | 5,167,916,147 | 12,493,115,473 | +7,325,199,326 | +0.010152 | positive | 0 | 64.36 | `bcbf09f0305935e3` | `74f36e5075176ff0` |
| 681 | +2 | direct | 683 | 5,409,733,980 | 12,939,181,488 | +7,529,447,508 | +0.010435 | positive | 0 | 65.72 | `b4733b6ffa87993e` | `bca7495c5a3f6e3a` |
| 682 | -15 | direct | 667 | 4,838,438,931 | 10,824,907,194 | +5,986,468,263 | +0.008297 | positive | 0 | 65.47 | `0671480dbdd580a7` | `7341dcdaf6d4ec4c` |
| 683 | +15 | direct | 698 | 4,946,939,590 | 11,311,675,823 | +6,364,736,233 | +0.008821 | positive | 0 | 61.47 | `9b0aa8c851c43671` | `1bf0feb91264c86c` |
| 684 | -30 | mirrored | 654 | 4,587,519,841 | 11,036,216,072 | +6,448,696,231 | +0.008937 | positive | 0 | 66.56 | `57659d042d055b7f` | `5654540aa7c5e89d` |
| 685 | -2 | direct | 683 | 5,548,150,908 | 12,066,201,663 | +6,518,050,755 | +0.009033 | positive | 0 | 65.63 | `47eaa117b141219f` | `540ff61cbda2d249` |
| 686 | +2 | direct | 688 | 5,314,167,746 | 11,842,860,114 | +6,528,692,368 | +0.009048 | positive | 0 | 64.83 | `377fcbf46b11e0bf` | `1869bfc958dd3634` |
| 687 | -15 | direct | 672 | 4,963,242,017 | 11,551,274,827 | +6,588,032,810 | +0.009130 | positive | 0 | 64.69 | `cf54121987f3f07f` | `971a66b5a6e29c03` |
| 688 | +15 | direct | 703 | 4,841,581,778 | 11,239,994,291 | +6,398,412,513 | +0.008868 | positive | 0 | 64.60 | `df1dcd8ac09511de` | `a0a8c3e7a1d7b31e` |
| 689 | -30 | mirrored | 659 | 4,894,556,588 | 11,147,659,620 | +6,253,103,032 | +0.008666 | positive | 0 | 64.71 | `82ee8bfdee655bcd` | `05e22da1d8fc5e47` |
| 690 | -2 | direct | 688 | 5,442,657,796 | 12,698,876,657 | +7,256,218,861 | +0.010056 | positive | 0 | 64.54 | `1bab19c070698390` | `37218690d7e9113a` |
| 691 | +2 | direct | 693 | 4,917,509,079 | 11,284,160,401 | +6,366,651,322 | +0.008824 | positive | 0 | 64.36 | `1585c8f5843a6da7` | `37e7b56bf578c5f7` |
| 692 | -15 | direct | 677 | 5,143,008,198 | 12,639,906,190 | +7,496,897,992 | +0.010390 | positive | 0 | 64.71 | `870db23944dc5e4f` | `1f67da267e674811` |
| 693 | +15 | direct | 708 | 5,269,412,499 | 11,596,141,233 | +6,326,728,734 | +0.008768 | positive | 0 | 64.84 | `d2fc4b305b320854` | `f8f36b0bf2c36dfe` |
| 694 | -30 | mirrored | 664 | 4,783,512,956 | 12,460,530,813 | +7,677,017,857 | +0.010640 | positive | 0 | 65.13 | `8aba61de7763752d` | `ffd929bc9bb47534` |
| 695 | -2 | direct | 693 | 5,239,161,374 | 11,858,520,142 | +6,619,358,768 | +0.009174 | positive | 0 | 65.20 | `2a574db1fb3cc233` | `c191cf8894117f5f` |
| 696 | +2 | direct | 698 | 4,967,286,323 | 11,816,796,984 | +6,849,510,661 | +0.009493 | positive | 0 | 64.76 | `55768ebd8e056c93` | `c16b6b4e0c035d11` |
| 697 | -15 | direct | 682 | 4,749,653,576 | 10,738,646,493 | +5,988,992,917 | +0.008300 | positive | 0 | 61.96 | `fde931bce67532fb` | `bb84b07f670d3d0d` |
| 698 | -15 | mirrored | 683 | 4,952,752,881 | 11,624,188,359 | +6,671,435,478 | +0.009246 | positive | 0 | 63.90 | `8ae0cc40fd9fdbf9` | `499e8df34fe51661` |
| 699 | -30 | mirrored | 669 | 4,955,936,276 | 11,525,632,550 | +6,569,696,274 | +0.009105 | positive | 0 | 64.03 | `88db67e499833940` | `380baa77c4aee244` |
| 700 | -2 | direct | 698 | 4,724,044,249 | 11,513,220,408 | +6,789,176,159 | +0.009409 | positive | 0 | 65.43 | `20012ed34ea8f68e` | `8f7fa503efd7837b` |
| 701 | +2 | direct | 703 | 5,300,940,198 | 12,432,585,107 | +7,131,644,909 | +0.009884 | positive | 0 | 64.18 | `403026c3a8e565d6` | `c971fa528df35bb4` |
| 702 | -15 | direct | 687 | 4,474,020,640 | 11,234,185,532 | +6,760,164,892 | +0.009369 | positive | 0 | 64.50 | `31529b4cee1c0cf4` | `c178dceeca88302d` |
| 703 | -15 | mirrored | 688 | 4,612,875,137 | 10,855,286,722 | +6,242,411,585 | +0.008651 | positive | 0 | 64.04 | `9c349ac20cc2648a` | `9206523364472fec` |
| 704 | -30 | mirrored | 674 | 5,342,528,676 | 11,789,818,198 | +6,447,289,522 | +0.008935 | positive | 0 | 63.85 | `803e447a5d16f003` | `48a74671295b00a8` |
| 705 | -2 | direct | 703 | 5,164,179,528 | 11,807,086,631 | +6,642,907,103 | +0.009206 | positive | 0 | 63.93 | `720f9e13c897670a` | `4782ecf3e04bd6ae` |
| 706 | +2 | direct | 708 | 5,143,459,521 | 11,972,542,769 | +6,829,083,248 | +0.009464 | positive | 0 | 64.24 | `cd8f133b2303d714` | `866938e5f4a38435` |
| 707 | -15 | direct | 692 | 5,204,111,678 | 11,733,691,667 | +6,529,579,989 | +0.009049 | positive | 0 | 64.29 | `6a2793659590b8cd` | `c1c76844411c8a2d` |
| 708 | -15 | mirrored | 693 | 5,886,097,238 | 12,742,354,656 | +6,856,257,418 | +0.009502 | positive | 0 | 64.46 | `d42b7b04525fe3a0` | `2e85cbdd2ee7308d` |
| 709 | -30 | mirrored | 679 | 4,799,388,897 | 10,087,236,535 | +5,287,847,638 | +0.007328 | positive | 0 | 63.93 | `c435bd0db62ccbd8` | `1b711ef51165032a` |
| 710 | -2 | direct | 708 | 5,017,897,337 | 12,287,619,416 | +7,269,722,079 | +0.010075 | positive | 0 | 64.34 | `b21eb4016760d1a5` | `7f5f7daae8f1d6c0` |
| 711 | -2 | mirrored | 709 | 5,349,837,529 | 12,264,037,322 | +6,914,199,793 | +0.009582 | positive | 0 | 63.52 | `ab89837de15e4c15` | `f9bfd2fb8980fdc4` |

112 rows proved and accepted under the frozen identities (0 missing); outcome classes: 112 positive, 0 zero, 0 negative; rows with a nonzero clip count: 0; D in MSE units min 0.007328, median 0.009161, max 0.010988; proving time per row (`prove_elapsed_ms`, the `.groth16()` call) min 61.47, median 64.66, max 66.79 min, total 120.70 GPU-hours; framed SP1 artifact sizes 2,444 B x1, 2,445 B x12, 2,446 B x59, 2,447 B x40 (raw proof 356 bytes and statement 752 bytes throughout); every proof accepted cold a second time on the development machine (`receipts/independent_verify/`, 112 accepted); merged manifest `receipts/BATCH_MANIFEST_merged.json` sha256 `4617085dc9c8db2044dfc3a633704152b465df1526203743822114e953d2d95b` (the published copy; the node recorded `e406e99819f42d5b04815ef999bf8ca218b5eda328c431d47234105400f2fffb` for the same manifest before its paths were redacted, `receipts/REDACTION_LEDGER.tsv`).
<!-- BATCH_TABLE_END -->

Operational context of the batch, rendered from the per-GPU manifests, the receipts and the launch schedule:

<!-- BATCH_CONTEXT_BEGIN -->
The batch ran as 8 concurrent prover processes, one per GPU of the rented node, launched 90 s apart (`receipts/launch_schedule.txt`). From the first process start (2026-09-07 22:15:00Z) to the last manifest write (2026-09-08 13:32:59Z) the wall time was 15.30 h for the 112 proofs; the median `.groth16()` call took 64.66 min against the 45.89 min of the single-process timing pilot in section 5. That the eight processes contended for the node's host CPU and memory is an interpretation of the slower per-proof time, consistent with the `host_rss.csv` and `gpu_mem.csv` samples on the data layer, and not a measured cause. The instruction counts quoted in section 4 were measured on five real rows (600 to 603 on the development machine, 684 on the node); the batch did not count instructions per proof, shard and chunk counts were not logged, and the `--cycle-limit` in every receipt is requested metadata that the pinned `sp1-cuda` client does not forward to the GPU server. Each prover client returned a nonzero status during cleanup after writing its final manifest (`finished: true, complete: true`); every proof had already been accepted cold on the node and is accepted again here and on the development machine, so the exits do not bear on the proofs. The stderr files that carry the exit diagnostics and the other sidecar logs are kept on-box, pinned by `receipts/SHA256SUMS_RUNS` (`receipts/README.md`).
<!-- BATCH_CONTEXT_END -->

## Sources

Section 1: `model/g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pubproto_eval.json`, `model/training/{eval.log,train.log}`.
Section 2: `model/ladder/`. Section 3: `oracle/final/README_FINAL.md` (v2.4), `oracle/final/FREEZE_SUMMARY.md`,
`oracle/final/AGREEMENT.md`. Section 4: `source/FULL_GUEST.md` (v1.2), `source/logs/`, `source/armc-relation/runs/`.
Section 5: the node timing pilot's report (on-box; its identity records are quoted in `PINS.json` `prover_node`).
Section 6: `receipts/`.

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-07 | BOSUN | Sections 1 to 5 drafted before the batch; section 6 rendered by fill_results.py when the collection lands. |
| 1.1 | 2026-09-08 | BOSUN | Astra round 6: residual-ratio sentence corrected (finding 2); the synthetic-session test statement no longer described as a published outcome (finding 4); operational context of the batch rendered into section 6 and framed artifact sizes stated (findings 2 and 14). |
| 1.2 | 2026-09-08 | BOSUN | Agent audits round 1: the quick screen's 28 August rows named (24 training rows, 4 proof rows) and the earlier "held-out" wording corrected; the 507-pair count derived; the selection record and the absence of a baseline stated. |
| 1.3 | 2026-09-08 | BOSUN | Section 5: the fresh-machine single-row replication's timing and memory quoted beside the pilot's. |
