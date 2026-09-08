> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

# Astra brief r2: zero-knowledge diffusion demo, candidate switch after G0 (BOSUN, 2026-09-07)

Read-only audit. Your round-1 verdict is at (on-box) ASTRA_VERDICT_zkdiff_r1.md and the measurements at MEASUREMENTS_r1.md. G0 has run. Judge the decision below and the thresholds.

## What G0 found (frozen ARM-C protocol adapted: t=150, offsets -2,+2,-15,+15,+30, one generator per session seeded 20260823, 1200 d2 rows + 500 v10 rows, pooled Mann-Whitney AUROC, paired fraction correct<mean(wrong))
Per-arm evaluation JSONs: (on-box) model/ladder/<arm>/pubproto_eval.json ; training logs beside them.

| arm | params | step | results |
|---|---|---|---|
| armc_b16_96x112_s20260907 | 1114500 | 12000 | d2: n=1200 AUROC 0.9998 paired 1.000 delta +5.35e-03 ; v10: n=500 AUROC 0.9995 paired 1.000 delta +5.25e-03 |
| zk2_b16_128x160_s20260907_qat | 377220 | 12000 | d2: n=1200 AUROC 0.5008 paired 0.517 delta +4.32e-06 ; v10: n=500 AUROC 0.5011 paired 0.530 delta +3.14e-06 |
| zk2_b16_48x56_s20260907_qat | 377220 | 12000 | d2: n=1200 AUROC 0.5170 paired 0.765 delta +1.76e-04 ; v10: n=500 AUROC 0.5179 paired 0.792 delta +1.93e-04 |
| zk2_b16_96x112_s20260907 | 377220 | 12000 | d2: n=1200 AUROC 0.5071 paired 0.640 delta +4.00e-05 ; v10: n=500 AUROC 0.5074 paired 0.646 delta +4.10e-05 |
| zk2_b16_96x112_s20260907_qat | 377220 | 12000 | d2: n=1200 AUROC 0.5080 paired 0.666 delta +4.33e-05 ; v10: n=500 AUROC 0.5074 paired 0.648 delta +3.68e-05 |
| zk2_b16_96x112_s20260908_qat | 377220 | 12000 | d2: n=1200 AUROC 0.5034 paired 0.572 delta +1.76e-05 ; v10: n=500 AUROC 0.5029 paired 0.562 delta +1.72e-05 |
| zk2_b24_96x112_s20260907_qat | 829156 | 12000 | d2: n=1200 AUROC 0.5055 paired 0.652 delta +2.94e-05 ; v10: n=500 AUROC 0.5037 paired 0.600 delta +1.79e-05 |
| zk_b16_96x112_s20260907 | 1063812 | 12000 | d2: n=1200 AUROC 0.5657 paired 0.998 delta +3.60e-04 ; v10: n=500 AUROC 0.5652 paired 0.998 delta +3.32e-04 |

Reading: the round-1 zk2 denoiser (QConv int8/int16 fake-quant, no norm, ReLU, hint concatenated at the stem, dilation at depth): the tested zk2 candidates had near-chance pooled AUROCs at every size (48x56, 96x112, 128x160), width (16, 24) and precision (QAT vs float) and did not meet the screen, their loss 3-6x worse than the others. The ZkUNet (BN/ReLU, no attention, ControlNet-style hint path) gets the per-row sign right (paired 0.998) but the pooled AUROC is 0.566 and the margin is +3.6e-4 on residuals near 0.046 (0.8% relative); its quantisation tolerance had not yet been measured. The published ARM-C DiffusionDiagnosticUNet architecture cut to base 16 at 96x112 (GroupNorm, SiLU/GELU, attention at the deepest level only, 14-channel hint) gives AUROC 0.9998/0.9995, paired 1.000/1.000, margin +5.3e-3 on residuals near 0.017 (about 30% relative).

## Costs measured by forward hooks (src/phase_g/diffusion_diagnostic_model.py via the ArmCUNet wrapper in src/train_lean.py), 71 instructions per MAC as measured on the r32 net
| arch | base | size | params | GMAC/pass | G instr/pass | two passes |
|---|---|---|---|---|---|---|
| armc | 8 | 96x112 | 281,540 | 0.210 | 14.9 | 29.8 |
| armc | 12 | 96x112 | 629,092 | 0.466 | 33.1 | 66.2 |
| armc | 16 | 96x112 | 1,114,500 | 0.822 | 58.4 | 116.8 |
| armc | 16 | 48x56 | 1,114,500 | 0.205 | 14.6 | 29.2 |
| armc | 16 | 128x160 | 1,114,500 | 1.567 | 111.2 | 222.4 |
| zk (ZkUNet) | 16 | 96x112 | 1,063,812 | 0.816 | 58.0 | 115.9 |
The MAC skeleton of ARM-C equals the ZkUNet's; GroupNorm (per-group mean/var, one inverse square root per group), SiLU/GELU (per-activation table), and the deepest-level attention (42 tokens at 96x112) add per-activation work that is small next to 0.8 GMAC.

## Decision under audit
1. Drop the zk2 and ZkUNet lines. The candidate is the published ARM-C architecture shrunk (width 8, 12 or 16 at 96x112, or width 16 at 48x56), trained from scratch on the d2/v10 training blocks as before. Sweeps G0b (ZkUNet widths, for the record), G0c (ARM-C widths 8/12/16 x sizes 48x56/96x112/128x160, second seed, hint dropout 0) and G0d (second seeds for widths 8/12, 24k-step runs, hint dropout 0 at width 8) are running now, 24 trainers on one 8xA100 node.
2. G1 (in progress): a numpy int64 bit-exact integer inference of the trained ARM-C width-16 net: per-channel int8 (and int16) weights, int16/int32 activations with explicit shifts, exact integer GroupNorm with Newton inverse square root, SiLU/GELU by 16-bit table, integer softmax by exp table, precomputed t=150 embedding and coordinate constants. Acceptance: integer/float sign agreement >= 99% over the 37 evaluation rows x 5 offsets, and the chosen proof pair's integer margin > 3x its quantisation error.
3. G2: SP1 6.4.0 guest implementing that integer network twice (correct row E vs one declared wrong row E), plus the round-1 legs (frame hash, session leaf, render-and-hash of both patterns from the XOF seed, previous-row drand leg); claim = execution binding only, described as an integer diffusion evaluator adapted from the frozen ARM-C protocol.

## Questions
A. Is the switch to the ARM-C architecture sound, and is the width choice best made by the G0c/G0d AUROC and margin (pick the cheapest width with AUROC >= 0.95 per session and margin >= 3x quantisation error), or would you fix width 16 now for margin and accept 117 G instructions?
B. Are the G1 acceptance thresholds right, and is int8-weight quantisation of GroupNorm/SiLU/attention likely to preserve a 30% relative margin, or should the plan default to int16 weights?
C. Does anything in the ZkUNet result (paired 0.998 but AUROC 0.566) change how the paired-versus-pooled statistic should be reported for the ARM-C candidate?
D. Any flaw in the cost table or in treating nonlinearities as negligible next to MACs for SP1 cycle counts?
E. What must the public description of this result say and not say, given the round-1 claim boundary?

Answer with numbered findings, each with a verdict and the file it rests on, then a one-line VERDICT: PROCEED / REVISE / STOP with the single most important change.
