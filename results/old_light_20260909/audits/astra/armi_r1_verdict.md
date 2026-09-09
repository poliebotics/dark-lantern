> Public audit copy, 9 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md (in particular the owner correction of 9 September on the scene of the 2026 recordings).
> Paths are package-relative where the file is in this package (`dark-lantern/...` where it is elsewhere in the repository) and
> bracketed where it is not; line numbers are as at audit time and may have moved.

**The positive result survives the audit. The arithmetic checks out; publication needs corrections to the claims and provenance.** No files were changed.

1. **PASS: the reported numerical results reproduce.** Independent AUROC calculation, with half-credit for ties, reproduced 108 session cells, 17 era pools and 12 Perlin bins: **2,444 numerical comparisons, zero mismatches**. This included the stated 1,000-resample row, session-cluster and block-margin bootstraps using seed 20260823. `SUMMARY_TABLES.md` regenerates exactly from the verified JSONs. The checkpoint-trajectory point estimates also reproduce. Sources: bootstrap implementation (`armi_cross_configuration/kit/src/eval_xcfg.py` line 55), aggregation (`armi_cross_configuration/kit/src/eval_xcfg.py` line 231), trajectory table (`armi_cross_configuration/REPORT.md` line 136).

   Both ARM-I seeds reproduce AUROC **1.000**, paired **1.000**, and bootstrap intervals **[1,1]** on d2, v10 and the 112 August held-out rows. The ARM-C control reproduces the same on d2/v10. The reported block-margin intervals also match. REPORT:59 (`armi_cross_configuration/REPORT.md` line 59).

   December 2024, main seed; brackets are reproduced 95% row-bootstrap intervals:

   | Session | AUROC [CI] | Correct-lower count; paired [CI] |
   |---|---|---|
   | 044052 | .651 [.629, .689] | 64/64; 1.000 [1,1] |
   | 044529 | .644 [.621, .681] | 64/64; 1.000 [1,1] |
   | 050046 | .639 [.616, .675] | 64/64; 1.000 [1,1] |
   | 050648 | .684 [.655, .727] | 64/64; 1.000 [1,1] |
   | 051150 | .686 [.662, .729] | 64/64; 1.000 [1,1] |
   | 051629 | .702 [.673, .749] | 63/64; .984 [.953, 1] |
   | 052040 | .687 [.664, .728] | 64/64; 1.000 [1,1] |
   | **Pooled** | **.657 [.646, .669]** | **447/448; .998 [.993, 1]** |
   | Second seed, pooled | .639 [.628, .651] | 440/448; .982 [.969, .993] |

   The pooled session-cluster AUROC intervals reproduce as **[.644,.679]** and **[.626,.658]**. All seven second-seed session estimates and intervals also match. SUMMARY_TABLES:10 (`armi_cross_configuration/SUMMARY_TABLES.md` line 10), second seed:41 (`armi_cross_configuration/SUMMARY_TABLES.md` line 41).

   Reverse and aligned results reproduce:

   | Cell | AUROC [row CI] | Paired [row CI] |
   |---|---|---|
   | Reverse, held-out 050046 | .951 [.911,.985] | 1.000 [1,1] |
   | Reverse, d2 | .821 [.811,.831] | .994 [.990,.998] |
   | Reverse, v10 | .766 [.752,.784] | .992 [.984,.998] |
   | Reverse, pooled 2026 | .687 [.679,.696] | .994 [.990,.997] |
   | Main seed, raw 2023 | .500 [.498,.502] | .505 [.489,.523] |
   | Main seed, aligned 2024 | .508 [.505,.511] | .634 [.589,.679] |
   | Main seed, aligned 2023 | .543 [.541,.545] | .909 [.899,.919] |
   | Second seed, aligned 2024 | .509 [.506,.514] | .636 [.589,.683] |
   | Second seed, aligned 2023 | .553 [.551,.556] | .937 [.929,.946] |
   | Reverse, aligned 2024 | .537 [.532,.544] | .754 [.712,.795] |
   | Reverse, aligned 2023 | .532 [.531,.534] | .761 [.745,.775] |

   Reverse transfer succeeds on **1,689/1,700** frames. Main aligned 2023 succeeds on **3,054/3,359**, with session-cluster AUROC interval **[.535,.569]**. Sources: reverse table (`armi_cross_configuration/REPORT.md` line 109), aligned table (`armi_cross_configuration/REPORT.md` line 123).

   Perlin bins also reproduce:

   | Display period; rows | Main AUROC [CI] | Main paired [CI] | Second-seed AUROC [CI] |
   |---|---|---|---|
   | 40–60; 97 | .634 [.621,.659] | 1.000 [1,1] | .632 [.617,.658] |
   | 60–80; 143 | .642 [.625,.663] | .993 [.979,1] | .625 [.607,.648] |
   | 80–110; 157 | .666 [.649,.690] | 1.000 [1,1] | .644 [.626,.667] |
   | 110–200; 51 | .735 [.695,.799] | 1.000 [1,1] | .722 [.679,.790] |

   Second-seed paired values are 1.000, .958, .987 and 1.000; their intervals reproduce. Spearman correlations are **.359869** and **.210580**. Perlin calculation (`armi_cross_configuration/kit/perlin_bins.py` line 17).

   **Qualification:** these intervals describe resampling the recorded scores. They do not include training uncertainty or establish performance on new rigs. Perfect paired intervals `[1,1]` arise automatically when every observed row succeeds.

2. **PASS WITH QUALIFICATION: the floating statistic and architectural change match; the proof statistic must remain distinct.** The evaluator preserves timestep 150, shared noisy frame and noise target across conditions, MSE residuals, offsets `[-2,+2,-15,+15,+30]`, omission of invalid offsets, and averaging of the available wrong residuals. On the control checkpoint, the two evaluators’ correct scores and every individual-offset score are **bit-for-bit identical**. eval_xcfg:198 (`armi_cross_configuration/kit/src/eval_xcfg.py` line 198), published evaluator:119 (`dark-lantern/proofs/zkdiff_august_20260907/oracle/trainer/lean_pubproto_eval.py` line 119).

   The package’s proof instead uses **one wrong emission**, selected by `OFFSETS[(r−600)%5]`, mirrored at the August boundary. The secondary `r%5` implementation is equivalent for August and an adapted convention elsewhere. ARM-I’s floating scores are not the package’s fixed-point proved execution. STATEMENT:195 (`dark-lantern/proofs/zkdiff_august_20260907/STATEMENT.md` line 195).

   The neural architecture changes only the hint input, from 14 to 5 channels. The **1,296-parameter reduction** is exactly nine removed input channels × sixteen filters × 3×3. The trainer additionally introduces loaders, cache handling and monitors; its optimization, sampler and schedule remain unchanged. All four final checkpoint hashes match their evaluation metadata. trainer classes (`armi_cross_configuration/kit/src/train_xcfg.py` line 299), launch recipe (`armi_cross_configuration/kit/run_arms.sh` line 36), kit hashes (`armi_cross_configuration/KIT_SHA256SUMS_as_run.txt` line 1).

3. **FIX: input handling is largely sound, but “as displayed” and the alignment explanation overstate the evidence.** Index pairing, logged-pair selection, whole-frame remosaicing and area resizing match the implementation. The 2024 recorder directly establishes RGB emissions and BGR recordings. recorder:106 (`supporting/data_look/control/unanchored_2024/recorder_source/secure_record.py` line 106), pair parser (`armi_cross_configuration/kit/src/train_xcfg.py` line 127), camera loader (`armi_cross_configuration/kit/src/train_xcfg.py` line 198).

   For 2023, the surviving trailer source supports reversing stored emission channels to RGB. Applying that convention to earlier recorder revisions remains an inference. Furthermore, the actual display passed through an eight-bit PNG and a bilinear resize to 1920×1200; the loader directly downsamples the clipped floating array. Two local samples differed by about **0.20/255 mean absolute intensity** after reduction. Call this an emission-image approximation; its score impact was not measured. The raw-layout channel-order null does not settle channel sensitivity after alignment. display pipeline (`truth_beam_2023_REDACTED.py (public: Truth Beam downloads, recovery/recorder-source/`):108), emission loader (`armi_cross_configuration/kit/src/train_xcfg.py` line 264), earlier-version caveat ([the data-look desk's report, on-box] line 188).

   **The homographies were fitted from target-session emission/recording pairs**, including all 64 pairs in each 2024 session. “Externally estimated” means another desk, not independent calibration data. Encouragingly, excluding the 79 fitted pairs overlapping the 2023 evaluation leaves **2,981/3,280 successes, paired .909, AUROC .543**; the second seed retains **.937 paired, AUROC .553**. The calibrated recovery therefore survives removal of calibration rows. homography fitting ([the data-look desk's code, on-box]/run_session.py line 99), calibration sample counts ([the data-look desk's report, on-box] line 88).

   The measured 180° rotation is credible. The “one-third scale” explanation is misleading at the model input: native camera-pixel scales largely cancel during resizing. Representative normalized scales are approximately **92% horizontally and 114% vertically** relative to 2024, with both fields occupying about half the frame. Warping changes orientation, perspective, background and occupancy together. Say **“alignment improved correspondence”**; rotation-only and scale-only causes were not isolated. 2023 geometry (`supporting/data_look/1682718815_stats.json` line 596), 2024 geometry (`supporting/data_look/20241219_050046_stats.json` line 115), overstated interpretation (`armi_cross_configuration/REPORT.md` line 130).

4. **FIX: the headline can be honest and readable, but several sentences need replacement.** Define paired fraction as **the fraction whose correct-emission error is below the average prescribed wrong-emission error**. It is not identification accuracy among all candidate emissions. Keep pooled AUROC beside it.

   The margin figures are correct: **0.00244, or 6.01%**, for December 2024 versus **0.02268, or 198.08%**, for pooled d2/v10. The absolute margin is roughly one tenth; the relative percentages differ by roughly thirty-threefold. The report conflates these comparisons. REPORT:81 (`armi_cross_configuration/REPORT.md` line 81).

   Replace “equals exactly” with “matched AUROC and paired fraction, with similar margins.” Describe the control’s approximately 2% drift as unexplained, since its cause was not isolated. Replace “a longer run would not have changed the picture” with the observed trajectory. Describe raw 2023 as **consistent with chance**, and present its calibrated recovery with AUROC **.543**, not paired .909 alone. REPORT:64 (`armi_cross_configuration/REPORT.md` line 64), REPORT:144 (`armi_cross_configuration/REPORT.md` line 144).

   The stated claim boundary is sound: **the published proof binds ARM-C execution; ARM-I has no corresponding proof here. Neither establishes realness, liveness or physical capture.** Preserve that wording in public material. REPORT:164 (`armi_cross_configuration/REPORT.md` line 164), package claim boundary:15 (`dark-lantern/proofs/zkdiff_august_20260907/CLAIM_BOUNDARY.md` line 15).

5. **MIXED: sceptical questions have partial answers, with clearly identifiable gaps.**

   | Question | Evidence present | Evidence missing or correction needed |
   |---|---|---|
   | Were old targets used in training? | Training logs show zero gradient-training rows from the old monitor sessions; the final 24,000-step endpoint was fixed. | Forward training monitored 050046 and the 2023 trailer; reverse training also monitored d2. Replace “never saw” with “excluded from weight training.” No complete cross-era exact/near-duplicate audit is recorded. |
   | Does this transfer across scenes? | The same bookshelf is documented across 2023/2024; shelving also appears in the 2026 contact sheet. | No scene-held-out test. The claimed changes of room and lens are unsupported here; camera-model identity also remains unresolved. |
   | Could simple corpus cues explain it? | Holding the camera frame and noise fixed controls frame difficulty within each comparison. | No matched-colour, spatial-shuffle, motion-stratified or comparable simple baseline rules out coarse correspondence shortcuts. |
   | Does the offset rule inflate paired fraction? | Main 2024: **447/448** beat the wrong mean, **437/448** beat the single selected wrong, **418/448** beat every available tested wrong. Individual-offset paired fractions remain .974–.986. | Random, harder or exhaustive alternative negatives were not tested. |
   | Is the Perlin result a controlled frequency experiment? | The recorded period association and both seed results reproduce. | Binning uses the correct emission’s period; **1,285/1,792 negative comparisons cross bins**. Matched-frequency negatives and controlled scale changes are absent. State an observational association. |

   Sources: training counts (`armi/checkpoints/armi_2026_s20260908/train.log` line 2), monitor assignments (`armi_cross_configuration/kit/run_arms.sh` line 38), bookshelf provenance ([the data-look desk's report, on-box] line 147), unsupported room/lens assertion (`armi_cross_configuration/REPORT.md` line 115), offset scoring (`armi_cross_configuration/kit/src/eval_xcfg.py` line 216), Perlin binning (`armi_cross_configuration/kit/perlin_bins.py` line 21).

6. **PUBLISHABLE WITH FIXES: proposed public wording.** This supports a bounded correspondence result on these recordings. New training is unnecessary for that claim; broader scene, hardware or causal claims require the missing evidence above. The existing shelf recommendation should lose “equals exactly” and “never saw.” REPORT:194 (`armi_cross_configuration/REPORT.md` line 194).

   **Shelf entry:** “ARM-I, trained on 2026 recordings: 447/448 December 2024 frames favour their own projected pattern over the average prescribed wrong patterns, paired fraction 0.998 and pooled AUROC 0.657.”

   **Plain-English paragraph:** “Our image-conditioned diffusion evaluator, ARM-I, trained on 2026 recordings, gave the correct projected pattern a lower error than the average prescribed wrong patterns on 447 of 448 December 2024 frames: paired fraction 0.998. Its pooled AUROC was 0.657, where 0.5 means chance and 1 means perfect separation; a second training seed gave 440 of 448 and AUROC 0.639. The average error gap was about 6% of the correct-pattern error, versus roughly 200% in the 2026 checks. Transfer also worked in reverse, with session AUROCs of 0.821 and 0.766 and correct-pattern preference on 99.4% of 1,700 frames. Target sessions were excluded from weight training, although selected sessions were monitored during training. Raw 2023 recordings gave chance performance; retrospective alignment calibrated from target-session pairs raised paired preference to 0.909, with AUROC 0.543. These are correspondence results within this recorded corpus. The published zkdiff proofs bind ARM-C’s specified execution only; they do not prove ARM-I or establish realness, liveness or physical capture.”

VERDICT: PUBLISHABLE WITH FIXES, replace “never saw” and “untouched” with an explicit disclosure of target-session monitoring and calibration.
