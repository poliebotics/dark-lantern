> Public audit copy, 9 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md (in particular the owner correction of 9 September on the scene of the 2026 recordings).
> Paths are package-relative where the file is in this package (`dark-lantern/...` where it is elsewhere in the repository) and
> bracketed where it is not; line numbers are as at audit time and may have moved.

The positive numerical result reproduces. The report needs corrections before publication.

1. **PASS: reported calculations reproduce.** All **335 session/pooled result cells**, including bootstrap CIs and shuffle controls, reproduce from the score CSVs within floating-point precision. All **39,920 individual scores** reproduce from cached grids and partner maps, and all 106 report table lines regenerate correctly.

   The headline values are:

   | Era / grid | Pooled AUROC | Frame-bootstrap 95% CI | Paired wins |
   |---|---:|---:|---:|
   | April 2023 / 8 | 0.999859 | 0.999601–1 | 584/584 |
   | December 2024 / 16 | 0.998834 | 0.997877–0.999611 | 448/448 |

   Sources: 2023 results:2962 (`train_free_coupling_old_sessions/results/2023_results.json` line 2962), 2024 results:3072 (`train_free_coupling_old_sessions/results/2024_results.json` line 3072), report generator:47 (`train_free_coupling_old_sessions/code/write_report.py` line 47). Paired wins and AUROC measure different comparisons; neither should be presented as general “accuracy.”

2. **PASS: requested raw-pair recomputation.** I recomputed every one of the 64 raw pairs in each sampled session at grids 8 and 16, using saved quads and partners. All **1,536 matched/mismatched scores** across full-frame, crop and channel-swap variants reproduce exactly with the reference functions. An independent calculation using float64 cell sums and Pearson correlations gives identical AUROCs and wins.

   | Session | Grid | Crop AUROC | Crop wins | Full-frame AUROC |
   |---|---:|---:|---:|---:|
   | 1682013847 | 8 | 0.999023 | 64/64 | 0.735596 |
   | 1682013847 | 16 | 1.000000 | 64/64 | 0.775391 |
   | 20241219_044052 | 8 | 0.851807 | 61/64 | 0.537842 |
   | 20241219_044052 | 16 | 0.989502 | 64/64 | 0.561035 |

   Sources: 2023 grid 8:2858 (`train_free_coupling_old_sessions/results/2023_results.json` line 2858), 2023 grid 16:3568 (`train_free_coupling_old_sessions/results/2023_results.json` line 3568), 2024 grid 8:1838 (`train_free_coupling_old_sessions/results/2024_results.json` line 1838), 2024 grid 16:2890 (`train_free_coupling_old_sessions/results/2024_results.json` line 2890). Their bootstrap endpoints also reproduce.

3. **PASS: reference statistic and defensible adaptations.** `grid` and `corr` are identical to the reference at the parsed-code level. All **5,160 saved partner assignments** reproduce from seed 0 in the recorded grid/session order, with no self-pairs. The reference’s fixed-point repair can reuse a recording as several negatives; this is unchanged behaviour, not a one-to-one derangement. Reference:24 (`dark-lantern/results/train_free_coupling_20260906/scripts/coupling_stat.py` line 24), current implementation:32 (`train_free_coupling_old_sessions/code/coupling_lib.py` line 32).

   Channel handling agrees with the recorder sources. The 2023 clipping/rounding also matches an in-memory OpenCV PNG conversion on three checked emissions. The 180-degree orientation is a documented calibration decision. All 584 selected indices reproduce from the manifest-based selection rules, including the spaced samples and 195-frame trailer sample. 2023 recorder:111 (`truth_beam_2023_REDACTED.py (public: Truth Beam downloads, recovery/recorder-source/`):111), 2024 recorder:127 (`secure_record.py (github.com/poliebotics/TruthBeam-2024, commit bc8d2603`):127), selection:40 (`train_free_coupling_old_sessions/code/select_2023.py` line 40).

4. **PASS for crop blindness; FIX the claimed implication.** The quad estimator receives recordings alone and applies one shared transform per session. It performs no pair-specific optimization using matched labels. Orientation, however, is selected using four matched pairs that also enter evaluation; geometry development was iterative on these sessions. Crop construction:42 (`train_free_coupling_old_sessions/code/stage_a_session.py` line 42), orientation:32 (`train_free_coupling_old_sessions/code/stage_b_stats.py` line 32), development log:34 ([the desk's run log, on-box] line 34).

   Replace “cannot inflate” and “misalignment can only lower” with the precise statement that **the quad is estimated without emission values or pair labels**. Blinding does not establish optimal alignment or eliminate every source of retrospective optimism. Reassuringly, excluding every comparison touching an orientation-calibration frame preserves 522/522 April grid-8 wins and 394/394 December grid-16 wins.

5. **FIX: the refinement conclusion exceeds the evidence.** December session 051150 improves at grid 8 from **0.875 to 0.892578 AUROC**, while paired wins fall from 32/32 to 30/32. Unchanged AUROC at already saturated grids 16/32 cannot establish that no alignment improvement remains. REPORT:182 (`train_free_coupling_old_sessions/REPORT.md` line 182).

   There is also a resolution mismatch: refinement fits a 480×270 crop but evaluates at 1920×1080, and grid truncation retains different fractions of the image. My raw check found that refinement improves the held half’s correlation at fitting resolution, **0.1325→0.2333**, while worsening even the fit half at full resolution, **0.1866→0.1712**. Therefore the log’s “overfits its half” explanation is unsupported. Describe this as a limited sensitivity check. refine_check.py:31 (`train_free_coupling_old_sessions/code/refine_check.py` line 31), RUN_LOG:52 ([the desk's run log, on-box] line 52).

6. **QUALIFIED PASS: controls support the narrow correspondence claim.** Label shuffles relabel already-computed scores. Their chance results check the scoring machinery, but cannot exclude upstream leakage or temporal confounding. The channel swap tests colour sensitivity and retains substantial spatial information; it is not a chance-level null. Controls:236 (`train_free_coupling_old_sessions/code/coupling_lib.py` line 236), channel swap:82 (`train_free_coupling_old_sessions/code/stage_b_stats.py` line 82).

   Random negatives mostly come from distant frames: only **13/448** December grid-16 negatives are immediate neighbours. Shared scene, exposure and a moving person are not independently controlled. Uniform channel offsets/gains are removed by correlation, but spatial changes and nonlinear responses remain possible influences. No evidence establishes that these manufactured the result. Replace “the easiest negative there is” with “one random same-session negative”; harder temporal or adversarial alternatives remain untested. The report otherwise states the random-negative scope explicitly. REPORT:17 (`train_free_coupling_old_sessions/REPORT.md` line 17).

   Serial dependence is disclosed, but the CI explanation needs correction. These intervals condition on fixed partners, geometry and orientation, and ignore session clustering and shared recordings. A ten-pair crop interval of **[1,1]** reflects bootstrap saturation, not certainty about future recordings. Bootstrap:220 (`train_free_coupling_old_sessions/code/coupling_lib.py` line 220), REPORT:227 (`train_free_coupling_old_sessions/REPORT.md` line 227).

7. **FIX: remaining factual and documentation errors.**

   - “Every session ≥0.999” is false: December 044052 at grid 16 is **0.989502**. December grid 32’s pooled **1.0000 is rounded**, from 0.999955. REPORT:62 (`train_free_coupling_old_sessions/REPORT.md` line 62), 2024 results:4124 (`train_free_coupling_old_sessions/results/2024_results.json` line 4124).
   - In 2023, `crop_bgr` deliberately reverses stored **RGB** recordings; “stored BGR left unflipped” applies only to December. REPORT:35 (`train_free_coupling_old_sessions/REPORT.md` line 35).
   - `export75` reproduces the crop geometry but omits the exporter’s resize. The resize is not numerically invariant: one checked grid-16 mismatch score changes by 0.00458. Label this an approximate geometry variant. stage_a_extra_2024.py:4 (`train_free_coupling_old_sessions/code/stage_a_extra_2024.py` line 4).
   - Update the stale Otsu description, the stated minimum cell size from 30×17 to **30×16**, and the audit note incorrectly listing refinement as unperformed. Library:17 (`train_free_coupling_old_sessions/code/coupling_lib.py` line 17), REPORT:199 (`train_free_coupling_old_sessions/REPORT.md` line 199), REPORT:237 (`train_free_coupling_old_sessions/REPORT.md` line 237).

8. **PUBLISHABLE framing after those corrections.** This extends the same statistic to older recordings. It is not a directly comparable improvement over d2/v10’s **0.756 at grid 8**, because both recordings and alignment differ. The earlier paired count at that grid is **902/975**. Morning report:16 (`dark-lantern/results/train_free_coupling_20260906/README.md (and its box_record/coupling_stat.json`):16).

   The alignment gap deserves its own sentence: **At grid 16, aligning the projected region raises pooled AUROC from 0.740 to 1.000 in April and from 0.561 to 0.999 in December.** This makes the preprocessing contribution explicit. REPORT:26 (`train_free_coupling_old_sessions/REPORT.md` line 26).

   **Shelf entry:** No Training Required, archival repeat: with projected-region alignment, a fixed calculation preferred the correct recording to one random same-session alternative in all 1,032 tested comparisons across 15 sessions, with no trained model.

   **Plain-English paragraph:** We compared 584 April 2023 and 448 December 2024 projected patterns with their corresponding camera recordings. After aligning the lit area, a fixed calculation preferred the correct recording over one randomly chosen alternative from the same session in every tested comparison, using an 8×8 grid for April and 16×16 for December. No training or model was involved. This shows frame-by-frame correspondence between the projected patterns and these recordings. It does not measure image quality or establish liveness, realness, or proof of physical capture. Comparing the whole camera image gave much weaker results, so alignment is an essential part of the finding.

VERDICT: PUBLISHABLE WITH FIXES — replace the claim that crop blindness and refinement rule out inflation with the supported claim of correspondence against the chosen random same-session negatives.
