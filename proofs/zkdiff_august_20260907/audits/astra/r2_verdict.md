> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

1. **PROCEED: switch to ARM-C; retain width 16 as the working baseline.** Its individual-offset AUROCs also exceed 0.9988, so the result survives beyond averaging wrong conditions. Retire zk2 and ZkUNet for this demo. Use the already-running smaller candidates if their **actual integer exports** meet per-session AUROC **and paired fraction ≥0.95**, preserve the selected pair’s margin, and reduce measured guest cost. Do not choose from float AUROC and mean margin alone. Width 16 is the fallback, not a width that must be fixed now. ARM-C results (on-box: `model/ladder/armc_b16_96x112_s20260907/pubproto_eval.json` line 75), round-1 thresholds (on-box: `ASTRA_VERDICT_zkdiff_r1.md` line 128).

2. **REVISE: preserve both statistics and tighten their descriptions.** The paired statistic tests \(R_{c,i}<\operatorname{mean}_o R_{w,i,o}\). The headline pooled AUROC compares correct residuals across rows with those **per-row wrong means**, separately within each session. Consistent small within-row improvements can coexist with heavily overlapping pooled distributions; ZkUNet demonstrates exactly that. Report both, plus per-offset success counts and margin distributions. Paired 1.000 does not establish that all 8,500 individual comparisons succeeded.

   “Ignores the hint” overstates zk2’s evidence, particularly its 0.765/0.792 paired result at 48×56. “Too thin for quantisation” remains unmeasured. ZkUNet’s correct residual means are 0.03799/0.04043, giving relative margins approximately 0.95%/0.82%. Statistic implementation (`oracle/trainer/lean_pubproto_eval.py` line 139), zk2 results (on-box: `model/ladder/zk2_b16_48x56_s20260907_qat/pubproto_eval.json` line 75), ZkUNet results (on-box: `model/ladder/zk_b16_96x112_s20260907/pubproto_eval.json` line 75).

3. **REVISE: G1 needs residual-unit error and exact guest parity.** Keep ≥99% sign agreement as an initial screen. On 37 rows × five offsets, it permits one reversal, and these are correlated comparisons. Report counts by session and offset and explain every reversal. Sign agreement alone does not preserve pooled AUROC.

   For the selected pair, express integer and reference residuals in common units and define
   \[
   D_q=R_w^q-R_c^q,\qquad
   \eta=|R_w^q-R_w^f|+|R_c^q-R_c^f|.
   \]
   Require **\(D_q>3\eta\)**. This guarantees \(|D_q-D_f|\le\eta\) for that measured pair. Include preprocessing, noising, target quantisation and every network approximation in the comparison. Prediction-tensor MSE is not the relevant error measure. Separately require **byte-exact integer-oracle/Rust agreement**, including residual sums. The 30% mean margin supplies no minimum-pair bound; the local JSONs lack those tails. Residual computation (`oracle/trainer/lean_pubproto_eval.py` line 125), 37-row selection (`oracle/trainer/train_lean.py` line 176), round-1 parity requirement (on-box: `ASTRA_VERDICT_zkdiff_r1.md` line 116).

4. **PROCEED with integerisation; use int16 weights as the first fidelity baseline.** Int8 preservation is plausible but **unmeasured**. Int16 reduces weight-rounding uncertainty without changing MAC count; it cannot repair activation clipping or inaccurate normalisation. Promote int8 or mixed precision when measured error and guest cost justify it. Integer nonlinear inference has precedent, but that establishes feasibility rather than ARM-C accuracy. Model operations (`oracle/trainer/phase_g/diffusion_diagnostic_model.py` line 90), [I-BERT paper](https://proceedings.mlr.press/v139/kim21d/kim21d.pdf).

   Specify a **fixed-point GroupNorm approximation with exact implementation parity**: groups, variance convention, epsilon, Newton initialisation/iterations and rounding. Freeze LUT domains and bytes, softmax scaling, signed rounding, pooling and bilinear interpolation with `align_corners=False`. Check bounds for variance sums, Newton products, requantisation products and residual sums. NumPy int64 alone supplies no overflow protection. Spatial operations (`oracle/trainer/phase_g/diffusion_diagnostic_model.py` line 292), [NumPy overflow documentation](https://numpy.org/doc/stable/user/basics.types.html#overflow-errors).

5. **REVISE: close three provenance gaps.** The 37-row quick screen uses `999+r`; the frozen evaluator uses a session stream seeded `20260823`. A G0 subset must retain each row’s original stream position, including skipped draws. Pin the noise bytes and actual BF16/autocast reference. Also, the cache stores FP16 before evaluation converts to BF16, so its claim of exact uncached tensors is too strong. Include that rounding path in reference validation. Quick-screen RNG (`oracle/trainer/train_lean.py` line 198), frozen RNG (`oracle/trainer/lean_pubproto_eval.py` line 119), cache conversion (`oracle/trainer/precache.py` line 41).

   Fresh model construction also precedes `manual_seed`. Current seed labels control subsequent training randomness but do not reproduce initial weights. Preserve the checkpoints, fix subsequent construction order, and disclose the limitation without requiring another sweep. Construction (`oracle/trainer/train_lean.py` line 327), late seeding (`oracle/trainer/train_lean.py` line 390).

6. **REVISE: the cost table omits attention products.** Parameter counts and convolution/linear subtotals reproduce. At 96×112 the three attention blocks have **168, 42 and 168 tokens**. Including QKᵀ and AV gives:

   | ARM-C candidate | GMAC/pass | Two-pass G instructions, **estimated at 71/MAC** |
   |---|---:|---:|
   | b8, 96×112 | 0.21379 | 30.36 |
   | b12, 96×112 | 0.47156 | 66.96 |
   | b16, 96×112 | 0.82991 | 117.85 |
   | b16, 48×56 | 0.20593 | 29.24 |
   | b16, 128×160 | 1.59357 | 226.29 |

   The correction is modest. Nonlinear work is plausibly secondary, but “negligible” remains unmeasured: b16/96×112 processes approximately 3.28 million GroupNorm elements and 3.26 million SiLU/GELU elements per pass. The 71 coefficient belongs to r32, and the table excludes the binding legs. Measure the **complete guest**, preserving round 1’s ≤200B-instruction/≤1-hour execution gate. The 128×160 candidate already exceeds that instruction estimate before extras. Attention products (`oracle/trainer/phase_g/diffusion_diagnostic_model.py` line 114), spatial schedule (`oracle/trainer/phase_g/diffusion_diagnostic_model.py` line 288), cost assumptions and launch gate (on-box: `ASTRA_VERDICT_zkdiff_r1.md` line 129).

7. **REVISE G2’s abbreviated specification: retain the complete input binding.** Hashing a frame and proving session membership does not connect a host-supplied thumbnail to that frame. The guest must derive whole-frame reduction, both XOF hints and forward noising; bind both conditioning rows and emission renders; enforce the declared nonzero offset; and use the same noisy frame and noise target twice. Bind integer weights, scales, tables and arithmetic semantics, then publish residual sums or their difference with the common denominator. Finish with independently verified Groth16 and tampered-input controls. Round-1 relation requirements (on-box: `ASTRA_VERDICT_zkdiff_r1.md` line 54), proof mode (on-box: `ASTRA_VERDICT_zkdiff_r1.md` line 106).

8. **PROCEED with the execution-binding description after verification.** Say **“integer diffusion evaluator adapted from the frozen ARM-C protocol”**, trained from scratch at the declared reduced resolution. State that one proof binds whole-frame preprocessing and two conditional evaluations at t=150, producing the published positive integer difference.

   Report float and integer empirical results separately, with actual datasets, arithmetic, checkpoint and selection procedure. The d2/v10 blocks remain excluded from training, but their repeated use for candidate selection makes them development validation. Disclose selected positive examples. Do not claim reproduction of the published checkpoint/eight-seed result, proof of the five-offset aggregate or AUROC, full diffusion sampling, physical capture, illumination causality, realness, liveness, adversarial resistance or unseen-session generalisation. The predecessor drand leg does not enlarge that boundary. Round-1 public claim (on-box: `ASTRA_VERDICT_zkdiff_r1.md` line 146), paper’s claim boundary (on-box: `zeebeam.md` line 568).

Read-only audit: checked sources and JSONs, reproduced architecture counts, and matched the staged checkpoint hash to G0. No completed G1 implementation/results were available locally; integer parity and SP1 execution remain unverified.

— BOSUN ⚓

**VERDICT: REVISE: retain ARM-C, but require end-to-end residual-error validation and byte-exact complete-guest parity at G1.**