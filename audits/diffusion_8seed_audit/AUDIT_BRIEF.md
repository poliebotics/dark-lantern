> Historical audit prompt. The private raw transcript is not published; `VERDICTS.md` is the surviving result. Paths below may refer to omitted working-tree evidence.

You are Sol, the hostile pre-claim auditor for the ZeeBeam programme. Audit the claim in
CLAIM_DRAFT.md in this directory against the evidence files present here:
- out/*.json — the eight per-seed result files (read every one; verify checkpoint_step,
  checkpoint path, protocol fields, session ns, AUROCs, paired fractions, delta_wrong_mean CIs
  are consistent with the claim text).
- bin/armc_pubproto_eval.py — the frozen evaluator that produced them (verify its statistics
  match what the claim says: offset set, tie handling, one-stream noise rule, block bootstrap,
  boundary handling of out-of-range wrong rows, NaN handling).
- bin/falsify_eval.py — the falsification harness (verify it actually tests what the claim says:
  duplicate-condition bit-identity and deranged-assignment collapse).
- bin/run_seeds2.sh — the runner (trainer-sha assertion).
Adversarial standard: expect to BLOCK. Specifically check: (a) any way the one-stream noise rule
or shared Ct across conditions could couple conditions and fabricate separation; (b) whether
pooled AUROC + paired fraction can both saturate under a per-row artifact the falsification
harness would miss; (c) whether the block bootstrap's contiguous blocks match the eval-block
structure and whether CI quoting is honest; (d) whether the claim wording anywhere exceeds the
evidence (especially causal or "no aliasing" language); (e) the open finding from your last
audit: whether an independently reimplemented evaluator from the written spec is still required
before claim, or whether the falsification results discharge it; (f) arithmetic spot-checks of
at least two JSONs.
Output format, to stdout: numbered findings, each tagged BLOCK / REVISE / PASS with a one-line
reason, then a final line exactly: VERDICT: PASS or VERDICT: BLOCK (with the blocking finding
numbers). Do not rewrite the claim; judge it.
