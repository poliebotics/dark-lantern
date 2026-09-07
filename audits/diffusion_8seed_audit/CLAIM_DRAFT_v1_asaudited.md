# CLAIM C-NC8 (draft, pre-audit) — uncropped ARM-C diffusion, 8-seed conditioning separation

Eight independently seeded, from-scratch ARM-C uncropped diffusion models (out_size 768x896,
full sensor frame area-resized, NO crop) were trained to the declared horizon max_steps=12000
and ALL evaluated at their final checkpoint (latest.pt; checkpoint_step=12000 verified in every
result JSON) under the frozen evaluator (bin/armc_pubproto_eval.py, sha256
0bcfa7a7701e5dbf7e0a68264157a34f998542ccca33f07e9ad6753d3bd6d245): published-protocol
statistics (offsets [-2,+2,-15,+15,+30], t=150, one-stream per-session noise generator seeded
20260823 with one draw per row in row order, pooled Mann-Whitney AUROC with average-rank ties,
contiguous-block bootstrap sub-blocked to 40, paired fraction), preprocessing ARM-C's own
(deliberately NOT the ARM-A cropped evaluator).

Result, seed-wise (never pooled): d2 (n=1200) AUROC 1.0000 in 8/8 seeds; v10 (n=500) AUROC
1.0000 in 7/8 seeds and 0.9992 in 1/8 (seed0830); paired fraction 1.0000 in all 16 session x
seed cells. Mean wrong-minus-correct margins with 95% block-bootstrap CIs are recorded per seed
in out/*.json (delta_wrong_mean). Saturated statistics are quoted only alongside those margins.

Falsification harness (bin/falsify_eval.py) passed before this table was assembled:
duplicate-condition bit-identity 20/20; deranged correct-assignment collapses 1.0000 -> 0.5333.

History this table corrects: an earlier 6-of-8 table mixed checkpoints (6 at step 10000, 2 at
12000) and was WITHDRAWN; both apparent failures (seed26, seed27) reached 1.0000 at the declared
step 12000. The transition is sharp in the final 2000 steps.

Declared limitations: (1) the discriminated signal may include any frame-synchronous cue
correlated with row alignment; label/time aliasing is not excluded by this design, and a flat
per-offset profile rules out only smooth drift; (2) models are budget-limited at 12000 steps
(a 50000-step from-scratch rerun, seed 20260832, is in flight and gets this same evaluator);
(3) this is conditioning-discrimination on the August development take's held-out sessions
d2/v10, not realness, liveness, or held-out-take generalisation (the sealed 288-row take stays
sealed); (4) training data is owner-trusted.
