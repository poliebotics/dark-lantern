> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

# Astra brief r4: audit of the Rust integer kernels and the SP1 bench guest (BOSUN, 2026-09-07)

Read-only audit before proving. Round 3 (astra_r3/ASTRA_VERDICT_g1_r3.md) set the integer contract; the Rust port claims to implement it with byte-exact parity against the Python oracle and measures the SP1 cost. Files under (on-box) source/:
- armc-int/ (crate: src/kernels.rs, src/model.rs, tests/parity.rs, tools/export_oracle.py, armc-blob tool), CYCLES.md (v1.2), run_bench.sh, artifacts/ (ELF hashes, host binaries, result files), logs/, blobs/, oracle/ (exported vectors from g1_integer/vectors/).
- armc-eval-bench/{program,script}: SP1 6.4.0 guest (sp1-zkvm = 6.4.0) reading the constants blob and two conditionings, running two evaluations, committing two residual sums; host script executes (no proving) and prints total_instruction_count.
Oracle and contract: oracle/ (README.md, kernels.py, int_ref.py, vectors/, AGREEMENT.md) and the round-3 verdict.
Reported: 17 tests pass; all 188 layer outputs match on the four vector sets (int16/int8 x correct/wrong+2), chained and isolated; residual sums 12775807457 / 15569339266 / 12951859214 / 15757745232 exact; zero saturations; a mutation fixture proves the tester can fail. Executor: 3,386,436,547 instructions per pass, 6,817,169,189 for the two-pass guest, 4.081 instr/MAC vs 0.82985 GMAC/pass, peak RSS 11.5 GB, ~100 s wall on the development machine. Bounds reproduced from the constants: conv accumulator <= 406,605,889,536 (int16) / 1,576,206,336 (int8), GN n=32256, N 60 bits, X^2 99 bits, affine 55 bits, SSE <= 184,712,316,364,800; i64 everywhere except GroupNorm numerator/division/root in i128/u128. Effective scale map pinned by a test. Rounding rules split (offline ties-to-even, runtime ties toward +inf, exact left shift for s<=0). Admitted domain [-32767, 32767], every clipping event counted. int8 costs the same in this loop shape. A further ~12% via get_unchecked was deliberately not taken.

Questions:
1. Is the parity evidence sufficient for byte-exact equivalence with the oracle on arbitrary admitted inputs, or only on these four vectors? What additional fixtures (ties, endpoints, constant GroupNorm, borders, saturating inputs) must be added before the proofs, and can they be generated from the Python oracle without new theory?
2. Are the overflow bounds correctly derived from the constants and enforced (asserted) rather than assumed, so the unchecked i64 accumulate is sound for every admitted input, including adversarial ones inside the admitted domain?
3. Is the guest free of nondeterminism, host-trust leaks or unbound inputs (blob parsing, lengths, offsets, the two conditionings, the constants hash committed to public values)? What must the full relation guest add so that weights, scales, tables and arithmetic semantics are bound to public values (round-2 finding 7)?
4. Is the build reproducible in the sense the proved September tree required (pins, --locked, remap-path-prefix, offline resolution), and is anything missing for an auditable ELF and vkey?
5. Any error in CYCLES.md numbers or the extrapolation to A100 proving time (fleet 182-230 s per G instructions from the 4.15 G row proof)?
6. Is the get_unchecked optimisation worth taking before proving 112 rows (about 12% of 6.8 G), and under what invariant assertion would it be acceptable in a proof guest?

Answer with numbered findings, each with a verdict and file/line, then one line: VERDICT: ACCEPT / REVISE / REJECT with the single most important change before proving.
