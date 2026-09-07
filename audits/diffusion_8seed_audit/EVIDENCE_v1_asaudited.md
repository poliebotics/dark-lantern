# C-NC8 evidence bundle — response to the 2026-08-31 Sol BLOCK (findings 1-4, 6, 8, 9)

Assembled 2026-08-31 by BOSUN. Everything below is present in this directory or at the
named NFS path; every artifact is sha-bound in ATTESTATION.json.

## F1 (independent evaluation) — statistics half DISCHARGED, forwards half declared open
`independent_stats.py` + `INDEPENDENT_RECOMPUTE.json` (sha in ATTESTATION.json): a fresh
numpy-only implementation of ranks, Mann-Whitney AUROC, per-offset AUROCs, paired fraction,
delta means and the contiguous-block bootstrap, sharing no code with the evaluator, recomputed
every statistic from the raw per-row npz scores. Result: 16/16 session x seed cells match the
evaluator (AUROC and paired to <1e-12, delta to <1e-9); 0 dead bootstrap replicates; effective
n equals nominal n everywhere (no NaNs in any cell, answering F8's concern for THIS data;
the recompute reports effective counts explicitly). Full-precision AUROCs: exactly 1.0 in
13/16 cells; seed0830 d2 = 0.999993055555556, seed0830 v10 = 0.999208, seed27 v10 = 0.999988.
STILL SHARED with the training stack: the model forwards and data loaders that PRODUCED the
raw scores (trainer's load_C/load_E/q_sample). Discharging that would require a from-spec
loader + forward reimplementation; declared, not done.

## F2 (falsification binding) — DISCHARGED, with a disclosed nondeterminism note
Original execution log recovered: `falsify_215906.log` (T1a 20/20 bit-identical, T1b 20/20,
TRUE paired 60/60 = 1.0000, DERANGED (+613) 32/60 = 0.5333). Sha-bound rerun 2026-08-31:
`falsify_rerun_shabound_020953.log` — header binds falsifier bec430f4..., evaluator
0bcfa7a7..., trainer 04c83743..., checkpoint 03dd6caf... (base run latest.pt). Rerun: T1a
20/20, T1b 20/20, TRUE 60/60 = 1.0000, DERANGED 37/60 = 0.6167.
DISCLOSED: the deranged fraction differs across processes (0.5333 vs 0.6167) on the same
checkpoint. GPU forwards (bf16 autocast, cudnn) are not bit-stable run-to-run; deranged
comparisons sit near chance where tiny float differences flip individual pairs. The
falsification invariant is TRUE = 1.0000 plus collapse toward chance under derangement, and
both runs satisfy it. T1a/T1b bit-identity holds within-process and is claimed only
within-process.

## F3 (bindings) — DISCHARGED
`ATTESTATION.json`: evaluator/trainer/falsifier shas, all 8 result-JSON shas, all 16 raw-npz
shas, checkpoint paths + checkpoint shas + steps, recompute sha. The evaluator did not write
its own sha into the result JSONs (F3's specific gripe): true, unfixable retroactively without
regenerating results; the attestation binds them externally, and future evaluator runs will
record it inline.

## F4 (provenance of training claims) — EVIDENCE
- Finality: `history.jsonl` final line records step 12000 for ALL 8 runs under
  [machine path redacted]*/ (verified 2026-08-31; the eight
  final-step eval summaries are quoted in the ledger).
- From-scratch: launch scripts bin/run_seeds.sh + bin/run_seeds2.sh pass --from-scratch;
  checkpoint-recorded args (read by the evaluator from the ckpt, printed in result JSONs as
  crop_id UNCROPPED*, out_size 768,896) and the falsify header (base_ch=96 hint=14).
- Held-out status: trainer SESSIONS table (train_armc_xof.py, sha 04c83743...): d2 train
  blocks (0,1238)(1758,2736)(3256,4234)(4754,5992) vs eval blocks (1298,1698)(2796,3196)
  (4294,4694) = 3x400=1200 rows; v10 train (0,1050)(1420,2285)(2655,3743) vs eval
  (1110,1360)(2345,2595) = 2x250=500 rows; >=60-row buffers between train and eval blocks;
  august is train-only, no eval blocks.
- Withdrawn 10k table: ledger trail in scratch/tasks/TODO.md (2026-08-30 entries) and
  docs/research/zeebeam_nocrop_diffusion_8seed_20260830.md v2.0 (table withdrawn, reason:
  mixed checkpoints, both weak seeds were at step 10000).
- 50k run: live from-scratch process on [public address redacted]
  (runs/armc_uncropped_50k_seed20260832, --max-steps 50000), lands ~1 Sep, gets this same
  frozen evaluator.

## F6 / wording — ADOPTED
The claim table quotes full-precision AUROCs. Committed wording: "AUROC >= 0.9992 in all 16
session x seed cells; exactly 1.0 in 13 of 16." No 0.99999x value is ever printed as 1.0000.

## F9 (sub-block wording) — ADOPTED
"Sub-blocked toward a 40-row target" (v10 uses 41/42-row chunks); the recompute implements
and reports the same partition (assertion that sub-blocks cover all rows exactly).
