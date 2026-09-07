# C-NC8 evidence bundle v2 — after Sol v2 (BLOCK 4; REVISE 1,2,3,6,9)

v1 as audited is preserved in EVIDENCE_v1_asaudited.md. Changes here: F4 rebuilt around
data-borne provenance (Sol correctly caught that run_seeds*.sh are EVALUATION runners, and
that v1 misnamed the withdrawn table's weak seeds); F2 now reports both falsify executions
with the variability disclosed in the claim itself; F3 paths and pending fields fixed; F6/F9
wording adopted INSIDE CLAIM_DRAFT.md (v3), not merely promised here.

## F1 — statistics independence DISCHARGED; residue declared
INDEPENDENT_RECOMPUTE.json + independent_stats.py (shas in ATTESTATION.json): fresh
numpy-only recompute of every statistic from raw/. 16/16 cells agree (<1e-12 AUROC/paired,
<1e-9 delta); 0 dead bootstrap replicates; effective n nominal (13,600 rows all finite).
Residue, declared in the claim: model forwards, loaders and q_sample remain the trainer's
code path.

## F2 — falsification bound, deterministic, honestly reported
Two sha-bound executions on identical checkpoint bytes (03dd6caf...) agree exactly (T1a
20/20, T1b 20/20, TRUE 60/60, DERANGED 37/60 = 0.6167): falsify_rerun_shabound_020953.log
and falsify_rerun3_shabound_030937.log. Determinism across processes therefore HOLDS on
fixed bytes; the earlier GPU-nondeterminism conjecture (Sol v2 rightly called it unproved)
is WITHDRAWN. The original run (falsify_215906.log, DERANGED 32/60 = 0.5333) recorded no
checkpoint hash and is retained as an unbound observation, most plausibly a different
latest.pt snapshot. CLAIM_DRAFT v3 reports all three executions with exactly this framing.

## F3 — bindings fixed
ATTESTATION.json (current file; its sha changes as bindings accrete and as-audited snapshots are preserved): full NFS paths for both falsify logs with their shas;
rerun no longer PENDING; independent_stats.py sha added; provenance_histories.json bound;
the audited v1 evidence text preserved and sha-bound.

## F4 — training provenance, data-borne
- FULL history.jsonl files for ALL 8 runs are now IN THIS BUNDLE under histories/, each verified byte-identical to the sha256 recorded in provenance_histories.json; hash them yourself. Additionally provenance_histories.json summarises (first/last-line PREFIXES, 200 chars; the full files above are the binding record), for ALL 8 runs, history.jsonl file
  sha256 + first line + last line. Every first line is step 50 with loss ~0.987, the
  untrained denoising level, which is direct evidence of from-scratch starts; every last
  line is step 12000 with the final eval, which is finality at the declared horizon.
- CORRECTION (Sol v2 was right): run_seeds.sh (55ec01fb...) and run_seeds2.sh are
  EVALUATION runners. No training-launcher script is claimed; training provenance rests on
  the histories above and the checkpoint-recorded args the evaluator prints (crop_id
  UNCROPPED*, out_size 768,896).
- CORRECTION (Sol v2 was right): the withdrawn table's weak seeds were seed27_boxA
  (0.5192/0.5155) and seed0832_boxB (0.5286/0.5227), both evaluated at step 10000
  (primary record: docs/research/zeebeam_nocrop_diffusion_8seed_20260830.md, section 1
  withdrawal note). CLAIM_DRAFT v1's "seed26, seed27" was wrong and is fixed in v3.
- Held-out structure: trainer SESSIONS table (train_armc_xof.py 04c83743...): d2 train
  (0,1238)(1758,2736)(3256,4234)(4754,5992), eval (1298,1698)(2796,3196)(4294,4694);
  v10 train (0,1050)(1420,2285)(2655,3743), eval (1110,1360)(2345,2595); >=60-row buffers;
  august train-only.
- 50k from-scratch rerun: live on [public address redacted] (runs/armc_uncropped_50k_seed20260832,
  --max-steps 50000, at ~step 11400 on 2026-08-31), same frozen evaluator on landing.

## F6 / F9 — adopted in the claim text itself
CLAIM_DRAFT.md v3 prints full-precision AUROCs ("exactly 1.0 in 13 of 16; >= 0.9992 in all
16"), and describes the bootstrap as "sub-blocked toward a 40-row target (v10 uses 41/42-row
chunks)".
