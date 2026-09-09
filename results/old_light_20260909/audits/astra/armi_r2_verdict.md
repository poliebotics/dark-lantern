> Public audit copy, 9 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md (in particular the owner correction of 9 September on the scene of the 2026 recordings).
> Paths are package-relative where the file is in this package (`dark-lantern/...` where it is elsewhere in the repository) and
> bracketed where it is not; line numbers are as at audit time and may have moved.

**The numbers reproduce. Publication still needs corrections to interpretation and disclosure.** This was read-only: I recomputed saved scores and intervals, inspected training evidence, and changed no files.

1. **PASS: unified and few-shot numbers, including bootstrap CIs, reproduce.** Independent calculations checked 31 model/session cells across 22 JSONs: **1,317 numerical comparisons, zero mismatches**. This covered AUROC with ties, paired fractions, margins, secondary comparisons, row and block bootstraps, and applicable session-cluster intervals. Sources: metric implementation (`armi_cross_configuration/kit/src/eval_xcfg.py` line 35), bootstrap implementation (`armi_cross_configuration/kit/src/eval_xcfg.py` line 66).

   Unified results, with reproduced 95% row-bootstrap intervals:

   | Evaluation set | Seed 20260908 AUROC [CI] | Seed 20260907 AUROC [CI] | Paired, respectively |
   |---|---|---|---|
   | d2, 1,200 rows | 1.000 [1,1] | 1.000 [1,1] | 1.000 / 1.000 |
   | v10, 500 | 1.000 [1,1] | 1.000 [1,1] | 1.000 / 1.000 |
   | August, 112 | 1.000 [1,1] | 1.000 [1,1] | 1.000 / 1.000 |
   | 050046, 64 | .787842 [.740222,.839362] | .726318 [.685284,.778833] | 1.000 / 1.000 |
   | Aligned trailer, 777 | 1.000 [1,1] | 1.000 [1,1] | 1.000 / 1.000 |
   | Raw trailer, 777 | .471707 [.452384,.491176] | .488582 [.479050,.498840] | .435006 / .474903 |

   These match the unified table (`armi_cross_configuration/SUMMARY_TABLES_unified.md` line 7) and raw-layout results (`armi_cross_configuration/REPORT.md` line 163). **“Stays at chance” needs correction:** both raw-trailer AUROC intervals lie below .5. Say “no positive correspondence under the raw layout.”

   Every few-shot curve point reproduces:

   | k | 050046 AUROC [CI] | d2 retention AUROC / paired | Aligned trailer AUROC [CI] | d2 retention AUROC / paired |
   |---|---|---|---|---|
   | 0 | .638916 [.616455,.674823] | 1 / 1 | .575067 [.569768,.581402] | 1 / 1 |
   | 1 | .948242 [.908441,.980225] | .998868 / 1 | .999783 [.999404,1] | .801704 / .948333 |
   | 2 | .942383 [.902820,.975592] | .998980 / 1 | 1 [1,1] | .787492 / .956667 |
   | 4 | .944092 [.903564,.977295] | .998676 / 1 | 1 [1,1] | .782429 / .952500 |
   | 6 / 7 | .944092 [.903320,.977057] | .998398 / 1 | 1 [1,1] | .791549 / .955000 |

   Target-session paired fractions are 1.000 throughout, except the aligned-trailer k=0 baseline, .881596. All retention and paired CIs also reproduce. Sources: few-shot results (`armi_cross_configuration/REPORT.md` line 173), figure inputs (`armi_cross_configuration/kit/make_figures.py` line 177).

   These intervals condition on the recorded scores and fixed training/calibration. They do not measure uncertainty across future sessions, adaptation-session choices or homographies. Perfect empirical intervals `[1,1]` do not establish certain future performance.

2. **PASS on control arithmetic; FIX on the spatial-majority interpretation.** Independently reconstructed negatives and bootstraps reproduced **96 control cells, four motion strata and 12 Perlin bins: 8,268 numerical comparisons, zero mismatches**. Correct and prescribed-wrong residuals are bit-for-bit identical to the original evaluation.

   | Control | Main-seed AUROC [CI] | Main-seed paired [CI] | Second-seed AUROC / paired |
   |---|---|---|---|
   | Prescribed offsets | .657 [.646,.669] | .998 [.993,1] | .639 / .982 |
   | Random negatives | .658 [.647,.670] | .998 [.993,1] | .639 / .980 |
   | Mean of all 63 | .658 [.648,.670] | 1 [1,1] | .640 / .984 |
   | Nearest mean Perlin period | .653 [.641,.667] | .973 [.958,.987] | .635 / .913 |
   | Shuffled correct emission | .544 [.537,.551] | .772 [.732,.810] | .507 / .565 |
   | Colour-matched wrong emission | .649 [.638,.661] | .984 [.973,.996] | .629 / .940 |

   All stored per-session and second-seed intervals reproduce too. Exhaustive pooled AUROC is **.654752 / .636194**; **306/448 and 190/448** beat every alternative, respectively **68.3% and 42.4%**. Those identification counts must remain distinct from beating the average wrong residual. No CIs were supplied or claimed for these exhaustive pooled/count statistics. Sources: control results (`armi_cross_configuration/results/armi_2026_s20260908.controls2024.json` line 748), negative reconstruction (`armi_cross_configuration/kit/src/eval_controls.py` line 85).

   The controls substantially answer the offset-rule objection. Frequency and colour conclusions need narrower wording: the period control matches the nearest **RGB-average period**, with mean gap .883 pixels and maximum 16.024, rather than identical per-channel frequencies. Colour matching adjusts per-channel mean/std, followed by clipping; it does not match the complete colour distribution. Sources: period matching (`armi_cross_configuration/kit/src/eval_controls.py` line 57), colour transformation (`armi_cross_configuration/kit/src/eval_controls.py` line 77).

   **The shuffled result does not establish “mainly spatial correspondence with a secondary colour component.”** Main-seed residuals are correct .04056396, shuffled .04121688, wrong .04300350. The shuffle penalty is **26.8% of the original mean gap**, and only **5.2% for the second seed**. These ratios are descriptive, not causal shares; paired .772 measures prevalence, not contribution. Shuffling also changes spatial frequency and produces unfamiliar inputs. Replace the conclusion with: **“The model shows sensitivity to spatial arrangement, and preference survives the tested colour controls; these experiments do not partition spatial and colour contributions.”** Interpretation requiring replacement (`armi_cross_configuration/REPORT.md` line 194).

   Motion results reproduce: static **.669 [.656,.686], paired 1.000**, versus motion **.705 [.683,.734], paired .993**; second seed **.646/.987** versus **.682/.973**. Say “preference persists in both observed strata with similar margins.” An observational change-fraction split does not establish that motion has no effect. The Perlin bins and **1,285/1,792** cross-bin comparisons also reproduce. Sources: motion calculation (`armi_cross_configuration/kit/motion_split.py` line 19), Perlin calculation (`armi_cross_configuration/kit/perlin_bins.py` line 21).

3. **PASS on weight exclusion; FIX the completeness of monitoring disclosure; QUALIFIED PASS on calibration.** Both unified runs contain exactly **11,001 eligible training rows**, with zero from 050046 or the trailer. All eight adaptations exclude their target session and independently initialize from the same 2026 checkpoint. All ten final checkpoint hashes match evaluation metadata. Evidence comprises generated row-list definitions, logged counts and checkpoint arguments; no standalone training-row manifest was saved. Sources: unified counts (`armi/checkpoints/armi_unified_s20260908/train.log` line 2), row-list construction (`armi_cross_configuration/kit/src/train_xcfg.py` line 341), adaptation assignments (`armi_cross_configuration/kit/run_fewshot.sh` line 29).

   Unified monitoring included **10 rows from 050046, 11 trailer rows, 27 d2 evaluation rows, 10 v10 evaluation rows and 11 August held-out rows**, every 2,000 steps. The August rows were 604, 606, 620, 630, 636, 652, 654, 668, 678, 684 and 700. REPORT:154 (`armi_cross_configuration/REPORT.md` line 154) names only the old target monitors explicitly; add the 2026 subsets. Sources: monitor construction (`armi_cross_configuration/kit/src/train_xcfg.py` line 349), observed monitor (`armi/checkpoints/armi_unified_s20260908/train.log` line 45).

   There is no early-stopping or best-checkpoint selection path: runs reach fixed 24,000/2,000-step endpoints, and checkpoint saving precedes monitoring. Adaptation itself monitors no held-out target or d2 rows, although its inherited base had monitored the targets. No-gradient evaluation and separate noise generators preserve the training state. Training and checkpoint loop (`armi_cross_configuration/kit/src/train_xcfg.py` line 654).

   The trailer homography used **25 trailer pairs**, corresponding to evaluation rows **0,32,…,768**. Removing them leaves **752/752 paired successes and AUROC 1.000 for both unified seeds**. Few-shot k=1 becomes **.999777 [.999383,1]**, paired 752/752; k=2/4/7 remain perfect. Also removing calibration-row emissions from the remaining negative averages leaves those conclusions unchanged. Sources: fitted source indices (`supporting/data_look/1682718815_stats.json` line 6), source-to-row mapping (`armi_cross_configuration/kit/src/train_xcfg.py` line 151).

   **Direct inclusion of calibration rows does not explain the perfect result. The benefit from target-fitted geometry remains unbounded by this check**, because the same homography transforms every remaining frame. Describe the trailer as excluded from weight training, with alignment calibrated on 25 trailer pairs. Independent calibration and a complete content-duplicate audit remain absent.

4. **PARTIALLY FIXED: round-1 corrections are mostly faithful, with surviving contradictions.** The paired-fraction definition, margin arithmetic, emission approximation, same-bookshelf limitation and observational Perlin association are correctly incorporated. Sources: definition (`armi_cross_configuration/REPORT.md` line 68), margin arithmetic (`armi_cross_configuration/REPORT.md` line 83), emission approximation (`armi_cross_configuration/REPORT.md` line 34), scene limitation (`armi_cross_configuration/REPORT.md` line 225).

   The round-1 leave-fitted-pairs-out calculation independently reproduces: **2,981/3,280, AUROC .543146**, and second seed **3,074/3,280, AUROC .553250**. REPORT:132 (`armi_cross_configuration/REPORT.md` line 132).

   Required cleanup:

   - REPORT:221 (`armi_cross_configuration/REPORT.md` line 221) still calls 2023 null for every tested model and repeats “a third of the scale.” Both conflict with the corrections and follow-up.
   - REPORT:132 (`armi_cross_configuration/REPORT.md` line 132) labels the approximately 92%/114% normalized comparison “aligned”; those comparisons concern the raw layouts before warping.
   - REPORT:247 (`armi_cross_configuration/REPORT.md` line 247) still says no motion split was made and attributes control drift to GPU nondeterminism. The cause remains unexplained.
   - REPORT:178 (`armi_cross_configuration/REPORT.md` line 178) should say **d2 retention** and restrict “one session is enough” to the tested seed, first adaptation session and target. Overlapping intervals do not establish equivalence of session counts.
   - Use **three recorded rig configurations** at REPORT:152 (`armi_cross_configuration/REPORT.md` line 152); three distinct cameras are not established.
   - The provenance manifest is stale: `sha256sum -c` passes six entries but fails `train_xcfg.py`, whose current hash begins `3732bda7`, against recorded `903b9f4e`. Version the updated trainer and include follow-up scripts in the manifest. KIT_SHA256SUMS:1 (`armi_cross_configuration/KIT_SHA256SUMS_as_run.txt` line 1).

5. **PUBLISHABLE WITH FIXES: proposed publication wording.** These entries preserve the distinctions supported by the results (`armi_cross_configuration/REPORT.md` line 154) and the proof boundary (`dark-lantern/proofs/zkdiff_august_20260907/CLAIM_BOUNDARY.md` line 15).

   **Zero-shot 2026→2024:** 447/448 frames favour their own pattern over the average prescribed wrong patterns: paired .998, pooled AUROC .657; second seed .982/.639. Targets excluded from weight training; selected rows monitored.  
   **Unified three-rig ARM-I:** AUROC 1.000 on 2026 evaluation rows and the aligned trailer; .788/.726 on 050046, paired 1.000 throughout. Targets excluded from weight training; evaluation subsets monitored; trailer alignment calibrated on 25 trailer pairs.  
   **One-session adaptation:** In the tested single-seed runs, 64 adaptation pairs yield held-out 2024 AUROC .948; 777 aligned adaptation pairs yield trailer AUROC .9998, paired 1.000 both. Trailer calibration is target-fitted; d2 retention is .9989/.8017.

   **Plain-English paragraph:** ARM-I scores agreement between a recording and a supplied projected pattern. Trained on 2026 recordings, it preferred the correct pattern over the average prescribed wrong patterns on 447 of 448 December 2024 frames, with pooled AUROC .657; a second seed gave 440 of 448 and .639. Reverse transfer also worked, with 2026 session AUROCs .821 and .766. Raw 2023 inputs did not transfer successfully. Training across all three recorded rig configurations produced AUROC 1.000 on the 2026 evaluation rows and aligned 2023 trailer, and .788/.726 on the held-out 2024 session. One adaptation session reached .948 on 2024 and .9998 on the aligned trailer, although 2023 adaptation reduced d2 retention to .802. Target sessions were excluded from weight training, selected evaluation rows were monitored, and trailer alignment used 25 pairs from that trailer. Controls support correspondence under several alternative negatives without establishing how much comes from spatial or colour information. These are emission-recording correspondence results within a corpus sharing the same bookshelf; they establish no realness, liveness, physical-capture or scene-transfer claim. The published ZK proofs bind the specified ARM-C execution only, and do not prove ARM-I.

VERDICT: PUBLISHABLE WITH FIXES, replace the unsupported “mainly spatial, secondary colour” conclusion with a statement that the controls demonstrate spatial sensitivity without quantifying contribution shares.
