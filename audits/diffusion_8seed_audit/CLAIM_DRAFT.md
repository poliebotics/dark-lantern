# CLAIM C-NC8 v3 (pre-audit draft) — uncropped ARM-C diffusion, 8-seed conditioning separation

Eight independently seeded, from-scratch ARM-C uncropped diffusion models (out_size 768x896,
full sensor frame area-resized, NO crop) were trained to the declared horizon max_steps=12000
and ALL evaluated at their final checkpoint (latest.pt; checkpoint_step=12000 verified in every
result JSON) under the frozen evaluator (bin/armc_pubproto_eval.py, sha256
0bcfa7a7701e5dbf7e0a68264157a34f998542ccca33f07e9ad6753d3bd6d245): published-protocol
statistics (offsets [-2,+2,-15,+15,+30], t=150, one-stream per-session noise generator seeded
20260823 with one draw per row in row order, pooled Mann-Whitney AUROC with average-rank ties,
contiguous eval blocks sub-blocked toward a 40-row target — v10 uses 41/42-row chunks — 1000
bootstrap reps, paired fraction), preprocessing ARM-C's own (deliberately NOT the ARM-A
cropped evaluator).

Result, seed-wise, full precision (never pooled alone): on d2 (n=1200) AUROC is exactly 1.0
in 7/8 seeds and 0.9999930555555555 in seed0830; on v10 (n=500) exactly 1.0 in 6/8, with
seed0830 = 0.999208 and seed27 = 0.999988. AUROC >= 0.9992 in all 16 session x seed cells;
exactly 1.0 in 13 of 16. Paired fraction is 1.0000 in 16/16 cells. Mean wrong-minus-correct
margins with 95% block-bootstrap CIs are recorded per seed in out/*.json (delta_wrong_mean)
and independently recomputed in INDEPENDENT_RECOMPUTE.json (16/16 agreement, 0 dead
replicates, effective n nominal everywhere).

From-scratch and finality provenance (provenance_histories.json): every run's history.jsonl
opens at step 50 with loss ~0.987 (untrained denoising level) and closes at step 12000 with
the final eval; the file sha256 of each history is recorded.

Falsification (bin/falsify_eval.py, sha bec430f4...): two sha-bound executions on the same
checkpoint bytes (03dd6caf...) agree exactly: T1a and T1b duplicate-condition bit-identity
20/20 within-process, TRUE-conditioning paired fraction 60/60 = 1.0000, DERANGED (+613)
paired fraction 37/60 = 0.6167 in BOTH (falsify_rerun_shabound_020953.log,
falsify_rerun3_shabound_030937.log) — the harness is deterministic across processes on fixed
checkpoint bytes. The original execution (falsify_215906.log) recorded no checkpoint hash,
reported DERANGED 32/60 = 0.5333, and cannot be bound to these bytes; it is retained as an
unbound observation. All executions satisfy the falsification invariant: TRUE = 1.0000 with
collapse toward chance under derangement.

History this table corrects: an earlier table mixed checkpoints (six evaluated at step 10000,
two at 12000) against a declared 12000 horizon and was WITHDRAWN. The two seeds that appeared
weak in it, seed27_boxA (0.5192/0.5155) and seed0832_boxB (0.5286/0.5227), were both
evaluated at step 10000; at the declared step 12000 both reach >= 0.999988. The transition is
sharp in the final 2000 steps.

Declared limitations: (1) the discriminated signal may include any frame-synchronous cue
correlated with row alignment; label/time aliasing is not excluded by this design, and a flat
per-offset profile rules out only smooth drift; (2) models are budget-limited at 12000 steps
(a 50000-step from-scratch rerun, seed 20260832, is in flight and gets this same evaluator);
(3) this is conditioning-discrimination on the held-out eval blocks of sessions d2 and v10;
the august session is train-only and is absent from the reported held-out evaluation (its histories carry an in-training august diagnostic, which is not a held-out number), not realness, liveness, or held-out-take generalisation (the sealed 288-row take
stays sealed); (4) training data is owner-trusted; (5) the statistics are independently
recomputed, but score generation (model forwards, loaders, q_sample) remains the trainer's
code path; an evaluator fully reimplemented from the written spec has not been done.
