---
version: 1.3
date: 2026-09-09
status: the three results in shelf form with their plain-English statements and headline tables; every number copied from a named results file in this package, in the wording the second-model results audits approved
author: Cathal Ryan Hynes (author of record); drafted with BOSUN, the project's automated research assistant
---

# Results

Three results, three methods, one question: does a Truth Beam recording carry a measurable trace of the pattern projected
when it was taken? Each section gives the shelf lines and the plain-English paragraph in the wording that passed the
results audit (`AUDIT_TRAIL.md`), then the headline table and the file from which every number was copied. The full desk
reports, tables and caveats are `train_free_coupling_old_sessions/REPORT.md`, `pix2pixhd_old_light/REPORT.md` and
`armi_cross_configuration/REPORT.md`. Read everything under `CLAIM_BOUNDARY.md`: these are emission-recording
correspondence results within these recordings, nothing here is proved in zero knowledge, and the paired fraction and the
pooled AUROC are always quoted together.

Conventions. AUROC is the area under the ROC curve of matched against mismatched scores (0.5 chance, 1.0 perfect);
"paired" is the share of frames whose true pairing scored better than its alternative; brackets are 95 percent bootstrap
intervals over frames (1,000 resamples for the statistic and ARM-I, 5,000 for the pix2pixHD work), which condition on the
recorded scores and on fixed partners, geometry and models, ignore serial dependence between frames, and say nothing about
future recordings. A `[1.000, 1.000]` interval means every resample ordered every pair correctly, not certainty.

## 1. The train-free grid statistic on the old sessions (`train_free_coupling_old_sessions/`)

**Shelf.** No Training Required, archival repeat: with projected-region alignment, a fixed calculation preferred the correct
recording to one random same-session alternative in all 1,032 tested comparisons across 15 sessions, with no trained
model.

**Plain English.** We compared 584 April 2023 and 448 December 2024 projected patterns with their corresponding camera
recordings. After aligning the lit area, a fixed calculation preferred the correct recording over one randomly chosen
alternative from the same session in every tested comparison, using an 8x8 grid for April and 16x16 for December. No
training or model was involved. This shows frame-by-frame correspondence between the projected patterns and these
recordings. It does not measure image quality or establish liveness, realness, or proof of physical capture. Comparing the
whole camera image gave much weaker results, so alignment is an essential part of the finding.

**Headline table** (pooled AUROC with the frame-bootstrap interval, then paired wins; source
`train_free_coupling_old_sessions/results/<era>_results.json`, fields `grids.<g>.<variant>.pooled`):

| era | variant | grid 4 | grid 8 | grid 16 | grid 32 | grid 64 | pairs |
|---|---|---|---|---|---|---|---:|
| 2023 | whole frame | 0.6771 [0.666, 0.690]; 571/584 | 0.7232 [0.710, 0.739]; 560/584 | 0.7399 [0.725, 0.756]; 544/584 | 0.7440 [0.729, 0.762]; 548/584 | 0.7294 [0.715, 0.747]; 531/584 | 584 |
| 2023 | projected-region crop | 0.9328 [0.922, 0.944]; 583/584 | 0.9999 [1.000, 1.000]; 584/584 | 1.0000 [1.000, 1.000]; 584/584 | 1.0000 [1.000, 1.000]; 584/584 | 1.0000 [1.000, 1.000]; 584/584 | 584 |
| 2024 | whole frame | 0.5089 [0.501, 0.517]; 240/448 | 0.5308 [0.519, 0.545]; 273/448 | 0.5608 [0.542, 0.583]; 274/448 | 0.5665 [0.546, 0.586]; 267/448 | 0.5781 [0.556, 0.601]; 276/448 | 448 |
| 2024 | projected-region crop | 0.6373 [0.618, 0.659]; 346/448 | 0.8886 [0.872, 0.907]; 433/448 | 0.9988 [0.998, 1.000]; 448/448 | 1.0000 [1.000, 1.000]; 448/448 | 1.0000 [1.000, 1.000]; 448/448 | 448 |

The "crop" is the projector-lit quadrilateral found from the recordings alone (the temporal standard deviation of each
session's frames marks the lit region; one perspective transform per session, no emission values and no pair labels
enter it), the orientation (0 or 180 degrees) chosen on four matched frames per session that also enter the evaluation;
excluding every comparison that touches one of those frames leaves 522 of 522 April grid-8 wins and 394 of 394 December
grid-16 wins. A seeded label shuffle sits at chance in every cell (0.469 to 0.535; a 1,000-permutation null band 0.461 to
0.541), which checks the scoring machinery and nothing upstream of it. At grid 16 the lowest December session is 044052 at
0.9895; the December grid-32 pooled value 0.99996 rounds to 1.0000. The negative is one random same-session frame (the
reference construction of the 6 September package, seed 0; a recording can serve as the negative for more than one frame);
harder temporal or adversarial negatives are untested. The whole-frame numbers are above chance but measure the statistic
through a misregistration and are not shelf material on their own. This extends the same statistic to older recordings
and is not a directly comparable improvement over the 6 September d2/v10 result (0.756 at grid 8, 902 of 975 paired),
because the recordings and the alignment handling differ. Sources: `results/2023_results.json`, `results/2024_results.json`
(every cell), `results/<era>_scores.csv` (every matched and mismatched score), `results/<era>_partners.json` (every
negative), `geometry/<session>.geometry.json` (every quad); the second-model audit reproduced all 335 result cells and all
39,920 scores (`AUDIT_TRAIL.md`).

## 2. pix2pixHD trained on the old recordings (`pix2pixhd_old_light/`)

**Shelf.** 2024: Given an average training scene, the neural model favoured the correct light pattern in all 64 two-choice
comparisons from one session excluded from training. 2023: Without model training, a colour-grid check favoured the correct
pairing in 776 of 777 two-choice comparisons from one trailer session.

**Plain English.** The old Truth Beam recordings retain a measurable link between projected light and the camera image. In
December's recordings, a neural model supplied with an average training scene favoured the matching light pattern in all
64 comparisons against one randomly chosen wrong pattern per recording. In April's trailer, a simple colour-grid check
favoured the true pairing in 776 of 777 comparisons. These exploratory results cover one session per era excluded from
training; evaluation results informed development and the choice of reported variants. They measure emission-recording
correspondence within these recordings and do not establish realness, liveness, capture verification or forgery detection.

**Headline table, the whole held-out session per era** (source `pix2pixhd_old_light/ci_summary.json`, computed by
`kit/ci_summary.py` from the per-frame JSON under `results/`; 95 percent frame bootstraps, 5,000 resamples):

| track and held-out session | test | result |
|---|---|---|
| 2024, `20241219_050046` (64 pairs) | train-free grid statistic, emission channels in the physically matched order, grid 16 / grid 64 (`results/2024/coupling_heldsession_rbswap.json`) | 0.982 [0.958, 0.999], 64/64; 1.000 [1.000, 1.000], 64/64 |
| 2024 | `ol2024_mean` generator as verifier, colour residual (`results/2024/ol2024_mean/latest_held/g_verifier_color.json`) | paired 64/64 = 1.000 [1.000, 1.000], pooled AUROC 0.962 [0.936, 0.984] |
| 2024 | `ol2024_mean` own discriminator, capture swap / emission swap, full frame (`results/2024/ol2024_mean/latest_held/d_verifier.json`) | 0.934 [0.891, 0.969] (60/64); 0.944 [0.909, 0.976] (64/64) |
| 2024 | `ol2024_mean` fidelity at 1024x576 against the sampled training-mean baseline (`results/2024/ol2024_mean/latest_held/metrics.json`, `results/2024/baselines_heldsession_1024x576/metrics.json`) | PSNR 22.36 [22.08, 22.63] dB, SSIM 0.720 [0.713, 0.728]; baseline 23.63 [23.38, 23.84], 0.792 [0.786, 0.798] |
| 2023, `1682718815` (777 pairs) | train-free grid statistic, emission channels in the physically matched order, grid 8 / grid 16 (`results/2023/coupling_heldsession_rbswap.json`) | 0.928 [0.917, 0.938], 777/777; 0.951 [0.942, 0.959], 776/777 |
| 2023 | `ol2023_b4` own discriminator, capture swap / emission swap, full frame (`results/2023/ol2023_b4/latest_held/d_verifier.json`) | 0.992 [0.990, 0.995] (775/777); 0.993 [0.991, 0.996] (777/777) |
| 2023 | `ol2023_b4` generator as verifier, colour residual (`results/2023/ol2023_b4/latest_held/g_verifier_color.json`) | paired 658/777 = 0.847 [0.821, 0.871], pooled AUROC 0.614 [0.604, 0.624] |

The 2024 track is 342 training pairs from six sessions (frames 0 to 56 of each), 42 in-session tail frames (57 to 63) and
the whole seventh session; the 2023 track 2,358 training pairs, 264 tails and the whole trailer. "Excluded from weight
training" holds for every held-out frame (split records `records/SPLIT_2024.json`, `records/SPLIT_2023.json`; the mean
prior is built from the 342 training captures only); "untouched final test" does not, because the held-out scores were
read during the night and steered the recipe changes, which is why every result is labelled exploratory. The fidelity of
the generated recordings stays below the sampled training-mean baseline while the generators carry emission-specific
changes; motion-related error and model error were not separated. The crop-recipe model on the 342 December pairs
(`ol2024_b4`) learned no scene and scored at chance on the held-out session; the same recipe on 2,358 April pairs worked;
the whole-frame December model without a prior (`ol2024_full`, stopped at 57 epochs) recovered the correspondence
(discriminator 0.948, generator 57 of 64) but not the scene; the mean-scene prior gave both. The saved discriminator draws
on the held-out sessions contain almost no adjacent-frame swaps (2 of 64 and 1 of 777), so hard temporal negatives are
untested there. Full tables: `pix2pixhd_old_light/REPORT.md`.

## 3. ARM-I, the image-conditioned diffusion evaluator across rig configurations (`armi_cross_configuration/`)

**Shelf.** Zero-shot 2026 to 2024: 447 of 448 frames favour their own pattern over the average prescribed wrong patterns,
paired 0.998, pooled AUROC 0.657; second seed 0.982 / 0.639. Targets excluded from weight training; selected rows
monitored. Unified three-rig ARM-I: AUROC 1.000 on the 2026 evaluation rows and the aligned trailer; 0.788 / 0.726 on
050046, paired 1.000 throughout. Targets excluded from weight training; evaluation subsets monitored; trailer alignment
calibrated on 25 trailer pairs. One-session adaptation: in the tested single-seed runs, 64 adaptation pairs yield held-out
2024 AUROC 0.948; 777 aligned adaptation pairs yield trailer AUROC 0.9998, paired 1.000 both. Trailer calibration is
target-fitted; d2 retention 0.9989 / 0.8017.

**Plain English.** ARM-I scores agreement between a recording and a supplied projected pattern. Trained on the 2026
recordings, it preferred the correct pattern over the average prescribed wrong patterns on 447 of 448 December 2024
frames, with pooled AUROC 0.657; a second seed gave 440 of 448 and 0.639. Reverse transfer also worked, with 2026 session
AUROCs 0.821 and 0.766. Raw 2023 inputs did not transfer successfully. Training across all three recorded rig
configurations produced AUROC 1.000 on the 2026 evaluation rows and the aligned 2023 trailer, and 0.788 / 0.726 on the
held-out 2024 session. One adaptation session reached 0.948 on 2024 and 0.9998 on the aligned trailer, although the 2023
adaptation reduced d2 retention to 0.802. Target sessions were excluded from weight training, selected evaluation rows were
monitored, and the trailer alignment used 25 pairs from that trailer. Controls support correspondence under several
alternative negatives without establishing how much comes from spatial or colour information. These are
emission-recording correspondence results within this recorded corpus. The 2026 sessions were recorded aboard CittaDel, in her
wheelhouse, and the 2023 and 2024 sessions in front of the same bookshelf in another room, so the 2026 to
2024 and 2024 to 2026 transfers cross scene as well as camera, resolution and pattern family, while the 2023 to 2024 pair
shares a room; a scene-held-out test with a third scene still does not exist. They establish no realness, liveness or
physical-capture claim. The published ZK proofs bind the specified ARM-C execution only, and do not prove ARM-I.

**Headline table** (the frozen ARM-C statistic at the 24,000-step checkpoints; row bootstraps, 1,000 resamples, seed
20260823; sources `armi_cross_configuration/results/<arm>.eval.json` and the tables `SUMMARY_TABLES.md`,
`SUMMARY_TABLES_unified.md` rendered from them):

| model, trained on | tested on (excluded from weight training) | pooled AUROC [CI] | paired [CI] | margin, wrong minus correct | source |
|---|---|---|---|---|---|
| ARM-I seed 20260908, 2026 (d2, v10, August 0 to 599; 8,035 rows) | 2026 d2 / v10 evaluation blocks (1,200 / 500) | 1.000 / 1.000 | 1.000 / 1.000 | 2.24e-2 (+204 %) / 2.34e-2 (+185 %) | `results/armi_2026_s20260908.eval.json` |
| the same | the seven December 2024 sessions, raw whole frame (448) | 0.657 [0.646, 0.669] (session-cluster [0.644, 0.679]) | 0.998 [0.993, 1.000], 447 of 448 | +2.44e-3 (+6.01 %) | the same |
| ARM-I seed 20260907, 2026 | the seven December 2024 sessions (448) | 0.639 [0.628, 0.651] | 0.982 [0.969, 0.993], 440 of 448 | | `results/armi_2026_s20260907.eval.json` |
| ARM-I seed 20260908, 2026 | the eight April 2023 sessions, raw (3,359) | 0.500 [0.498, 0.502] | 0.505 [0.489, 0.523] | +0.0 % | `results/armi_2026_s20260908.eval.json` |
| the same | the eight April 2023 sessions, aligned into the emission frame (3,359) | 0.543 [0.541, 0.545] (cluster [0.535, 0.569]) | 0.909 [0.899, 0.919] | +1.5 % | `results/armi_2026_s20260908.warped.eval.json` |
| ARM-I seed 20260908, six 2024 sessions (384 rows) | 2024 session 050046, held out (64) | 0.951 [0.911, 0.985] | 1.000 [1.000, 1.000] | +7.20e-3 (+48 %) | `results/armi_2024six_s20260908.eval.json` |
| the same | 2026 d2 / v10 evaluation blocks | 0.821 [0.811, 0.831] / 0.766 [0.752, 0.784] | 0.994 [0.990, 0.998] / 0.992 [0.984, 0.998] | +11.9 % / +8.2 % | the same |
| ARM-C positive control, seed 20260908, 2026 | 2026 d2 / v10 | 1.000 / 1.000 | 1.000 / 1.000 | 2.29e-2 / 2.39e-2 | `results/armc_2026_s20260908_ctl.eval.json`, `.pubproto_eval.json` |
| unified ARM-I, seeds 20260908 / 20260907: 2026 blocks + six 2024 sessions (raw) + seven 2023 sessions (aligned), 11,001 rows | 2026 d2, v10, August 600 to 711 | 1.000 in every cell | 1.000 in every cell | 1.81e-2 / 1.51e-2 on d2 | `results/armi_unified_s2026090{8,7}.eval.json` |
| the same | 2024 session 050046, raw, held out (64) | 0.788 [0.740, 0.839] / 0.726 [0.685, 0.779] | 1.000 [1.000, 1.000] / 1.000 | +13.4 % / +9.5 % | the same |
| the same | 2023 trailer 1682718815, aligned, held out (777) | 1.000 [1.000, 1.000] / 1.000 | 1.000 / 1.000 | +419 % / +331 % | the same |
| one-session adaptation from the 2026 model (2,000 steps, seed 20260908) | 2024 session 050046 after one 2024 session (64 pairs); d2 retention | 0.948 [0.908, 0.980]; 0.9989 | 1.000; 1.000 | | `results/fs_2024_k1.eval.json`, `fs_2024_k1.d2.eval.json` |
| the same | the aligned trailer after one aligned 2023 session (777 pairs); d2 retention | 0.9998 [0.9994, 1.000]; 0.802 [0.790, 0.814] | 1.000; 0.948 | | `results/fs_2023w_k1.eval.json`, `fs_2023w_k1.d2.eval.json` |

Controls on the December 2024 zero-shot result (`results/armi_2026_s20260908.controls2024.json`; second seed in
`armi_2026_s20260907.controls2024.json`): random within-session negatives 0.658 / 0.998, the mean of all 63 other
emissions 0.658 / 1.000 (306 of 448 frames beat every one of their 63 alternatives; 190 of 448 for the second seed), the
nearest matched Perlin period 0.653 / 0.973, a colour-matched wrong emission 0.649 / 0.984, the correct emission with its
pixels shuffled 0.544 / 0.772; the 301 static frames and the 147 frames with a person or motion in the beam give 0.669 /
1.000 and 0.705 / 0.993 (`results/armi_2026_s20260908.motion_split.json`). The controls support correspondence under the
alternative negatives and show sensitivity to spatial arrangement without partitioning spatial and colour contributions.
The trajectory (`results/traj_armi_2026_s20260908_<step>.eval.json`) shows the 2024 pooled AUROC rising from 0.542 at step
5,000 to 0.659 at 15,000 and staying within 0.653 to 0.657 through 24,000 while 2023 stays consistent with chance under
the raw layout. The trailer homography was fitted on 25 trailer pairs; removing them leaves 752 of 752 paired successes and
AUROC 1.000 for both unified seeds, and the aligned 2023 result for the 2026-trained model survives the removal of the 79
fitted frames (2,981 of 3,280, paired 0.909, AUROC 0.543); the benefit of target-fitted geometry, which transforms every
remaining frame, is not bounded by those checks. The positive control's margin is about 2 percent larger than the published
7 September checkpoint of the same seed, a difference that was not isolated; its AUROC and paired fraction are identical.
Full tables, the Perlin-period association, the channel-order diagnostic and every caveat: `armi_cross_configuration/REPORT.md`.

## What is not in this package

The desks' run logs and the second model's raw transcripts stay on-box (they quote the operator's private instructions). The
January 2025 pix2pixHD release is not evaluated here; it remains an artefact-only release with no performance claim, and the
pix2pixHD report as published carries no comparison rows for it. The raw-2023 null of ARM-I is published as a limit of the
transfer result it belongs to, with the recovery under alignment and the unified result beside it.

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-09 | BOSUN | First version, from the three desk reports as audited (ARM-I v1.4, statistic v1.1, pix2pixHD v1.0). |
| 1.1 | 2026-09-09 | BOSUN | Package audit round 1 applied: the last section reduced to what is not here, with the January 2025 release stated by the artefact-only fact alone; the ship named. |
| 1.2 | 2026-09-09 | BOSUN | Package audit round 2 applied: the two train-free statistic rows of the pix2pixHD headline table cite `coupling_heldsession_rbswap.json`, the file from which the numbers come. |
| 1.3 | 2026-09-09 | BOSUN | authorship line, 9 September 2026. |
