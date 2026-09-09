---
version: 1.3
date: 2026-09-09
status: the four second-model results audits of 9 September 2026 (two rounds on ARM-I, one on the statistic, one on the pix2pixHD work), their verdict lines verbatim, what each reproduced and what changed after each, the owner correction of the same day, the texts in audits/, and the package audit's three rounds with their dispositions
author: BOSUN for Cathal Ryan Hynes
---

# Audit trail

Each of the three results was audited by the programme's second model, GPT-6 Astra through `codex exec` (model
`gpt-6-astra`, ultra reasoning effort), reading the desk's report, code and results files on the development machine,
read-only, before this package was built. The brief the desk gave and the verdict returned are published in `audits/astra/`
with on-box paths trimmed to package paths and the release desk's private instructions redacted (`audits/README.md`). The
verdict lines below are verbatim. These are model reviews, not independent validation: each audit recomputed the reported
numbers from the saved per-frame or per-row scores and read the code, and none re-ran a training or a fresh inference.

| round | time (UTC) | subject | verdict line |
|---|---|---|---|
| ARM-I r1 | 04:29 | the first ARM-I report (four arms, three diagnostics, the aligned variant, the Perlin sweep) | "VERDICT: PUBLISHABLE WITH FIXES, replace “never saw” and “untouched” with an explicit disclosure of target-session monitoring and calibration." |
| ARM-I r2 | 05:33 | the follow-up (unified three-rig model, few-shot adaptation, the controls) and the round-1 fixes | "VERDICT: PUBLISHABLE WITH FIXES, replace the unsupported “mainly spatial, secondary colour” conclusion with a statement that the controls demonstrate spatial sensitivity without quantifying contribution shares." |
| statistic r1 | 05:34 | the train-free grid statistic on the 2023 and 2024 sessions | "VERDICT: PUBLISHABLE WITH FIXES — replace the claim that crop blindness and refinement rule out inflation with the supported claim of correspondence against the chosen random same-session negatives." |
| pix2pixHD r1 | 08:06 | the Old Light pix2pixHD runs on both tracks | "VERDICT: PUBLISHABLE WITH FIXES. Most important change: disclose adaptive reuse of the holdouts and label the results exploratory." |

## What each round reproduced

**ARM-I r1** (`audits/astra/armi_r1_verdict.md`): 2,444 numerical comparisons with zero mismatches (108 session cells, 17
era pools, 12 Perlin bins, the 1,000-resample row, session-cluster and block-margin bootstraps with seed 20260823, the
trajectory points); the two evaluators' scores on the control checkpoint bit-for-bit identical; the 1,296-parameter
difference between ARM-I and ARM-C exactly the nine removed hint channels; the training logs showing zero gradient rows
from the old sessions; the homographies confirmed as fitted from the target sessions' own pairs, with the aligned 2023
result recomputed without the 79 fitted frames (2,981 of 3,280, paired 0.909, AUROC 0.543).

**ARM-I r2** (`audits/astra/armi_r2_verdict.md`): 1,317 unified and few-shot comparisons and 8,268 control comparisons with
zero mismatches; exactly 11,001 eligible training rows in both unified runs with zero from the held-out sessions; every
adaptation independently initialised from the same 2026 checkpoint and excluding its target; the complete monitoring
inventory (10 rows of 050046, 11 trailer rows, 27 d2, 10 v10 and 11 August rows every 2,000 steps, no gradient, no
checkpoint selection); the trailer result recomputed without the 25 calibration rows (752 of 752, AUROC 1.000 for both
seeds); the identification counts (306 of 448 and 190 of 448 beating every alternative) kept distinct from the paired
fraction.

**statistic r1** (`audits/astra/coupling_r1_verdict.md`): all 335 session and pooled result cells, bootstrap intervals and
shuffle controls reproduced from the score CSVs; all 39,920 scores from the cached grids and partner maps; every one of the
64 raw pairs of one 2023 and one 2024 session recomputed from the saved quads and partners at grids 8 and 16 (1,536
scores, exact); all 5,160 partner assignments from seed 0; channel handling agreed with both recorder sources; the quad
estimator confirmed to receive recordings alone.

**pix2pixHD r1** (`audits/astra/oldlight_r1_verdict.md`): the six held-session results (paired wins, pooled AUROC and
intervals) and all 77 interval summary groups reproduced from the saved per-frame scores; all 396 listed hashes verified;
the split records and preparation code giving disjoint train, tail and held-out counts (342 / 42 / 64 and 2,358 / 264 /
777) and the mean prior built from the 342 training captures only; the discriminator partner maps confirmed as
within-session bijections without self-matches.

## What changed after each round

**After ARM-I r1** (report v1.2): "never saw" and "untouched" replaced by the disclosure that the target sessions were
excluded from weight training and that selected rows were monitored; the paired fraction defined exactly (the fraction of
frames whose correct-emission error is below the average prescribed wrong-emission error, not identification accuracy);
the margin arithmetic separated (absolute margin about one tenth, relative margin about thirty-threefold smaller on the
2024 rig); "equals exactly" replaced by "matched AUROC and paired fraction, with similar margins"; the control's 2 percent
margin drift called unexplained; the trajectory stated as observed; raw 2023 called consistent with chance and its recovery
under alignment stated with AUROC 0.543 beside paired 0.909; the homographies called a retrospective calibration from the
target sessions' own pairs with the leave-fitted-pairs-out numbers; the 2023 emission called an emission-image
approximation; the Perlin-period result called an observational association; the follow-up run the audit asked for (the
unified model, the adaptation curve, the controls) was run on a second machine and appended.

**After ARM-I r2** (report v1.3): the "mainly spatial, secondary colour" conclusion replaced by the supported statement
(sensitivity to spatial arrangement; preference surviving the tested colour controls; no partition of contributions); the
complete monitoring inventory for the unified runs; "stays at chance" for the raw trailer replaced by "no positive
correspondence under the raw layout" (both intervals lie below 0.5); the surviving round-1 contradictions removed; the
one-session claim restricted to the tested seed, the first adaptation sessions and the two targets; "three recorded rig
configurations" for "three cameras"; the identification counts kept distinct; the kit manifest regenerated after the
trainer changed; Astra's three shelf entries and plain paragraph adopted as the report's own.

**The owner correction of 9 September** (report v1.4): both ARM-I rounds, and the desk's own caveat, had stated that one
bookshelf appears in all three eras, on the strength of the data-look desk's reading of the 2026 contact sheet. The
principal stated that the 2026 sessions were recorded in a different room, aboard CittaDel, in her wheelhouse, and the desk
verified it against the public d2 camera preview frame 1300 (`https://data.truthbeam.com/sessions/d2/derived/Recordings_previews/frame_001300.png`,
SHA-256 `32dd9572c96275ab15601cfbb3d135722b13e60a627b02f119514a96f87d648b`), which shows a wheel, a row of blind-covered
windows, a bench and the masked participant, and no bookshelf: the horizontal bands the data-look desk read as shelving are
the wheelhouse windows, their blinds, the sills and the bench edge. The 2026 to 2024 and 2024 to 2026 zero-shot transfers
are therefore cross-scene as well as cross-camera, cross-resolution and cross-pattern-family; the 2023 to 2024 pair shares
a room; no third-scene test exists. Every other caveat was kept. The audit texts in `audits/` carry the superseded
same-bookshelf sentences as written at the time; this correction supersedes them.

**After statistic r1** (report v1.1): the claim that crop blindness and the refinement check rule out inflation replaced by
the supported claim of correspondence against the chosen random same-session negatives; the refinement conclusion corrected
(051150 grid 8 from 0.875 to 0.893 with paired wins 32 of 32 to 30 of 32; fit and evaluation at different resolutions; a
limited sensitivity check); "easiest negative" wording replaced; the controls described as checks on the scoring machinery;
the bootstrap intervals described as conditional on fixed partners, geometry and orientation; "every session at least
0.999" corrected (044052 at grid 16 is 0.9895; the December grid-32 pooled 0.99996 rounds to 1.0000); `crop_bgr` described
correctly for 2023; `export75` labelled an approximate geometry variant; the partner construction described as the
reference's repaired shuffle rather than a one-to-one derangement; the 2026 d2/v10 comparison framed as not directly
comparable (0.756 at grid 8, 902 of 975 paired); the alignment-gap sentence, shelf entry and plain-English paragraph adopted
from the audit as the report's own. No new computation.

**After pix2pixHD r1** (report v1.0): the adaptive reuse of the holdouts disclosed and every result labelled exploratory;
the generator test described exactly (another generated image is substituted, the real recording held fixed; seeded draw
with partner reuse); capture swap and emission swap defined; the baseline identity corrected (a 200-capture sample, not the
supplied prior) and the causal explanation of the fidelity deficit replaced by an observation; the near-absence of
adjacent-frame negatives stated; the 2023 section led by the coupling statistic with the discriminator supporting; the claim
that the whole-frame 2023 model was weaker on every test corrected; Astra's two shelf lines and paragraph adopted. The
desk's private gallery, which the audit found defective, is not published.

## The package audit

The release desk assembled this package after the four rounds above, and the coordinator's second-model audit of its exact
bytes, the bundle and the two transmit items followed the same day (GPT-6 Astra, `codex exec`). Round 1 found integrity,
numerical copying, privacy and the transmit preparation PASS (all ten frozen digests matched; every ledger entry and manifest
object verified; the 123 result files, the interval summary, 268 retained table rows and the ARM-I summary tables preserve
their source numbers; no private path, hostname or handle in 1,211 files and 17,076 decompressed archive members) and returned
"VERDICT: REVISE — harden and re-freeze 037_SEND.sh before staging either item." Its five REVISE findings are applied in this
revision (1.1 of the touched documents): wording in the reports that still contradicted the applied fixes ("unseen",
"never-seen", "never saw" read "excluded from weight training"; the motion split, the shuffle penalty and the matched-period
control described as their evidence supports; the generalisation test qualified by the disclosed adaptive evaluation); three
count descriptions and the presentation of AUROC beside every paired count; the January 2025 entries reduced to the
artefact-only fact and the participant disclosure repeated beside every sheet that shows a person; the send helper hardened
(isolation from ambient Git and gh configuration, refusal on any URL rewrite, explicit host on every read-back, a successful
send with an unchanged remote classed as inspect); and readability (`REPRODUCE.md`, the fetch-and-verify sequence in
`LARGE_FILES.md`, the two reproduction scopes stated beside the instructions, the pix2pixHD bootstrap described as it is).
Round 2, on the revised bytes, found integrity, reconciliation and privacy PASS (all ten frozen digests matched; the 325 package
entries covering 326 files, the 874 manifest objects and the four ledger and control files reconciled; the whitespace-aware scan
covered 1,212 files, 891,909,404 bytes and 17,076 decompressed members with no private-identifier residue) and returned "VERDICT:
REVISE, remove the excluded January discriminator measurements from both payloads and re-freeze." Its seven REVISE findings are
applied in this revision (1.2 of the touched documents; `REPRODUCE.md` 1.1, `HASHES.md` 1.1): the four `results/2024/d2025_*`
interval groups removed from the published `ci_summary.json` and the corresponding lines of the bundle's `pretrain_evals.log`
replaced by one bracketed line (`REDACTION.md`); the send helper's URL-rewrite guard replaced by two explicit `git config
--get-regexp` queries that refuse on a match or on a query error (the earlier `-i` form was rejected by the installed Git and read
as no match); the statistic's report generator aligned with the published report (the two 2023 sessions' pair count, the audit's
raw-pair count, the participant disclosure beside the contact sheet); the ARM-I full-run instructions completed (the download list
by absolute path, the 2026 precache step and its log marker, `XCFG_LEAN` as the cache root, the homographies and Perlin parameters
found beside the kit); the pix2pixHD kit inputs placed from the bundle and the checkout pinned before the bootstrap; the saved-score
promise limited to the numerical tables and score plots with the contact sheets distinguished; and the two headline-table
citations corrected to `coupling_heldsession_rbswap.json`. Round 3, on those bytes, closed all seven round-2 items, found the base change to
the post-039 main and the transmit helpers PASS (11 seals matching; 325 repository entries and 874 bundle objects verified; 1,213 files and
17,076 decompressed members scanned with no private residue) and returned "VERDICT: REVISE, contain REPRODUCE.md:88’s directory change in a
subshell, then re-freeze.", applied in `REPRODUCE.md` 1.2 (the checkpoint-loading command runs in a subshell, so the runbook's blocks work in
order). The audit texts are the coordinator's record and are not published here.

## Sources

The verdict lines are the closing lines of `audits/astra/armi_r1_verdict.md`, `armi_r2_verdict.md`,
`coupling_r1_verdict.md` and `oldlight_r1_verdict.md`. The dispositions are the Log sections of the three reports
(`armi_cross_configuration/REPORT.md`, `train_free_coupling_old_sessions/REPORT.md`, `pix2pixhd_old_light/REPORT.md`) and
their audit-note sections. The owner correction is recorded in the ARM-I report's Log (1.4) and caveats.

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-09 | BOSUN | First version: the four results audits and the owner correction; the package audit pending. |
| 1.1 | 2026-09-09 | BOSUN | The package audit's round 1 recorded with its verdict line and the dispositions applied; the ship named in the owner correction. |
| 1.2 | 2026-09-09 | BOSUN | The package audit's round 2 recorded with its verdict line and the seven dispositions applied. |
| 1.3 | 2026-09-09 | BOSUN | The package audit's round 3 recorded with its verdict line and the one disposition applied. |
