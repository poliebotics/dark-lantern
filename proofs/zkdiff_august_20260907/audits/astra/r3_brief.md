> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

# Astra brief r3: audit of the G1 integer reference (BOSUN, 2026-09-07)

Read-only audit. Your round-2 verdict (astra_r2/ASTRA_VERDICT_zkdiff_r2.md) set the G1 criteria: residual-unit error with D_q > 3*eta on the chosen pair, int16 weights as the first baseline, exact GroupNorm and table specifications, the exact noise stream, overflow bounds, byte-exact oracle/guest parity. G1 is now written and run. Audit it before the Rust port (Rust implementation in progress) relies on it.

Files, all under (on-box) oracle/:
- README.md (scheme, GroupNorm spec, op table, results, positive control, open items, log)
- AGREEMENT.md, agreement.json, agreement_int16.json, agreement_int8.json (185 pairs = 37 rows x 5 offsets)
- positive_control.py, positive_control.json, float_repro.py, float_repro.json (per-row reproduction of the frozen evaluator's scores in ckpt/pubproto_raw.npz_{d2,v10}.npz, with CUDA Philox emulation and bf16 autocast rounding points)
- common.py (noise emulation), kernels.py (scalar-loop references and vectorised kernels), int_ref.py (the integer forward), agreement.py
- constants_int16.json, constants_int8.json (quantised weights, scales, LUTs, time-embedding constants)
- vectors/ (row d2 1328: inputs, all 188 layer outputs, constants, LUTs, residual sums, sha256 per array)
- ckpt/armc_b16_96x112_s20260907_step12000.pt (the checkpoint; sha in README)
Model source: ../src/phase_g/diffusion_diagnostic_model.py with the ArmCUNet wrapper in ../src/train_lean.py; evaluator ../src/lean_pubproto_eval.py.

Reported results: positive control against the frozen evaluator within 9.84e-3 relative (fp32) and 5.09e-3 (bf16 emulation) on all 222 scores, every row at its own stream position; int16: sign agreement 185/185, paired 37/37, D_q/eta min 16.13 (vs evaluator) and 120.2 (vs fp32), all 185 pass D_q > 3 eta, no saturation; int8: min 8.92 (vs evaluator), 6.31 (vs fp32), all pass.

Questions:
1. Is the fixed-point scheme sound and completely specified for a byte-exact Rust port (every rounding rule, every bound, LUT domains, GroupNorm statistics and Newton iteration, softmax scaling, bilinear and pooling)? Name any place where the spec and the code could diverge or where a port could legitimately differ.
2. Are the overflow bounds proven or merely observed? Which accumulations need a formal bound before the guest drops per-MAC checks for a plain i64 accumulate?
3. Is the positive control adequate as evidence that the oracle reproduces the frozen evaluator (Philox emulation, bf16 rounding points, stream positions), and is the D_q/eta restatement against the evaluator computed correctly (definition of eta with the reference's bf16 path)?
4. Does anything here weaken or strengthen the choice of int16 first and int8 as the cost option?
5. What must change when the final checkpoint arrives (the candidate family trains width 12 and 16 at 24k-48k steps with hint dropout off and August rows included): recalibration procedure, re-verification, what carries over?
6. Any error in the numbers or the claim boundary as written in README.md?

Answer with numbered findings, each with a verdict and file/line, then one line: VERDICT: ACCEPT / REVISE / REJECT with the single most important change.
