> Historical audit prompt. The private raw transcript is not published; `VERDICTS.md` is the surviving result. Paths below may refer to omitted working-tree evidence.

You are Sol, re-auditing claim C-NC8 for the third time. Your v1 verdict is in
sol_audit_raw.log, v2 in sol_audit_v2_raw.log (BLOCK on finding 4 only, REVISE 1,2,3,6,9).
The v3 bundle in this directory responds: CLAIM_DRAFT.md is now v3 (full-precision AUROCs,
all three falsification executions with the unbound original demoted and determinism shown
by two agreeing sha-bound runs, corrected withdrawn-table history naming seed27_boxA and
seed0832_boxB, sub-blocked-toward-40 wording, data-borne from-scratch provenance);
EVIDENCE.md is v2 (F4 rebuilt: provenance_histories.json carries per-run history.jsonl
sha256 + first/last lines — every run opens at step 50 with loss ~0.987, the untrained
denoising level, and closes at step 12000; the run_seeds*.sh misattribution is corrected:
they are evaluation runners and no training-launcher script is claimed); ATTESTATION.json
binds everything including falsify run 3 (falsify_rerun3_shabound_030937.log, local copy
present). As-audited v1 copies are preserved (CLAIM_DRAFT_v1_asaudited.md,
EVIDENCE_v1_asaudited.md). Judge each of your prior findings as discharged, discharged with
declared residue, or still blocking; verify the corrected claim text against the artifacts;
check the falsification determinism reasoning. Output: numbered findings tagged
BLOCK / REVISE / PASS, then exactly one final line: VERDICT: PASS or VERDICT: BLOCK (numbers).
