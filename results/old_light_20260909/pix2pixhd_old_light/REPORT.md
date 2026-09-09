---
version: 1.0
date: 2026-09-09
status: exploratory results, complete for the night's runs; Astra results audit r1 (PUBLISHABLE WITH FIXES) applied; published copy
author: BOSUN for Cathal Ryan Hynes (the pix2pixHD training desk)
---

> Published copy of the desk report of 9 September 2026, as audited (`../AUDIT_TRAIL.md`). Every table and number is the
> desk's; the operational sentences are replaced and the machine paths read as package locators, as `../REDACTION.md` records.
> Paths are relative to this directory; `../` reaches the package root; `dark-lantern/...` names a file elsewhere in the
> Dark Lantern repository; `armi/`, `coupling/`, `oldlight/` and `supporting/data_look/*.png` name objects of the data-layer
> bundle (`../LARGE_FILES.md`). Read under `../CLAIM_BOUNDARY.md`.

# Old Light: pix2pixHD on the December 2024 and April 2023 Truth Beam recordings

The task of 9 September 2026: train pix2pixHD models on the old Truth Beam recordings on a rented GPU and evaluate them honestly. Two tracks, labelled throughout: **2024** (the seven December 2024 HDF5 sessions, 448 pairs) and **2023** (the eight April 2023 NumPy sessions, 3,399 pairs). Every model is scored on frames excluded from its weight training: the last tenth of every training session (the in-session tails) and one whole held-out session per track (2024: `20241219_050046`, the January 2025 run's own holdout; 2023: the trailer session `1682718815`). **These are exploratory results, not an untouched final test**: the held-out scores informed development during the night (the crop model's tail and 050046 results prompted abandoning the 1024-crop attempt and changing recipe; the full-frame model's epoch-25 tail images and fidelity prompted stopping it and adding the mean-scene prior; the geometry check sampled frames of 050046), and the reported variants were chosen with that knowledge. Intervals are 95 percent frame bootstraps (5,000 resamples) that resample frames with their existing mismatches; they omit temporal dependence, shared partners, negative-draw variation and model or grid selection, and one session per era cannot establish uncertainty across sessions. The rented machine was terminated after the runs; the desk's run log stays on-box.

## Headline

**Positive, exploratory, and honestly framed.** Six static pix2pixHD runs were attempted tonight on one A100 (one abandoned at epoch 9), five evaluated; the two that matter are below, the rest are in the tables.

1. **The light is in the data, before any model.** The train-free grid-coupling statistic separates a recording from the recording of another frame of the same session at AUROC 1.000 [1.000, 1.000] on the held-out 2024 session 050046 (64/64 paired wins; grid 64) and 0.951 [0.942, 0.959] on the held-out 2023 trailer session (776/777; grid 16), once the emission channels are read in the physically matched order. A [1.000, 1.000] interval reflects perfect ordering in these sampled scores, not certainty about future performance.

2. **2024 track, the shelf piece: `ol2024_mean`** (a neural model given an average training scene). pix2pixHD fed the emission plus the mean training capture, whole frames at 1024x576, 100 epochs on 342 pairs. On session 050046, excluded from weight training, its generated recording is closer to the real one than the recording generated from another frame in **64/64 frames** (colour residual pooled AUROC 0.962 [0.936, 0.984]; tails 42/42); its own discriminator ranks the true pair above a capture swap at AUROC 0.934 [0.891, 0.969] (60/64) and above an emission swap at 0.944 [0.909, 0.976] (64/64). PSNR 22.36 dB / SSIM 0.720 against the sampled training-mean baseline 23.63 / 0.792 (the mean of the first 200 sorted training captures, four of the six training sessions; the prior handed to the model averages all 342, and an exact supplied-prior-copy comparison was not run). The generator carries emission-specific changes while overall fidelity remains below that sampled baseline; motion-related error and model error were not separated. The contact sheets show the bookshelf, the shelves, the dinosaur and the projected pattern; the participant is a ghost, because the emission cannot say where he stands.

3. **2023 track: the coupling statistic leads, the discriminator supports.** Without any model, the colour-grid check favoured the true pairing in 776 of 777 two-choice comparisons on the trailer session, excluded from weight training (grid 16 AUROC 0.951 [0.942, 0.959]). Supporting it, the discriminator of `ol2023_b4` (the 6 September crop recipe, 2,358 pairs) ranks the true pair above a capture swap on that session at AUROC 0.992 [0.990, 0.995] (775/777) and above an emission swap at 0.993 [0.991, 0.996] (777/777); its generator wins 658/777 paired comparisons in colour (pooled AUROC 0.614 [0.604, 0.624]). Its renders carry the pattern but not the scene. The full-frame 2023 model without a prior (`ol2023_full`, 20 epochs) has the weaker discriminator (0.646 [0.619, 0.673]) and fewer generator paired wins (597/777), though a higher pooled colour-residual AUROC (0.697 [0.678, 0.716]); a 2023 mean-prior run did not fit the night and is the first follow-up.

4. **What failed, kept for the record.** The crop recipe on 342 pairs (`ol2024_b4`) learned no scene and scored at chance on the held-out session; the same recipe on 2,358 pairs worked. Whole frames alone (`ol2024_full`, stopped at 57 epochs) recovered the correspondence (D 0.948 [0.914, 0.979], G 57/64 on 050046) but not the scene; the mean-scene prior gave both.

5. **Comparison row.** The January 2025 pix2pixHD release remains an artefact-only release with no performance claim, and its discriminator is not evaluated in this package. Tonight's 2024 models were trained without session 050046 and their discriminators score 0.93 to 0.95 on it.

## Where to look

- `oldlight/records/results/<track>/<run>/latest/contact_sheet.png` (tails) and `.../latest_held/contact_sheet.png` (the whole held-out session), true colour, on the data layer; the top halves of the two shelf sheets are in this directory under `results/`.
- `oldlight/records/thumbs/pairs/` on the data layer: what the prepared training pairs look like for each era.
- The contact sheets, strips and thumbnails show a masked participant in a recognisable indoor setting (the bookshelf room); they are not anonymised.

## Shelf verdict

**2024:** Given an average training scene, the neural model favoured the correct light pattern in all 64 two-choice comparisons from one session excluded from training.

**2023:** Without model training, a colour-grid check favoured the correct pairing in 776 of 777 two-choice comparisons from one trailer session.

The old Truth Beam recordings retain a measurable link between projected light and the camera image. In December's recordings, a neural model supplied with an average training scene favoured the matching light pattern in all 64 comparisons against one randomly chosen wrong pattern per recording. In April's trailer, a simple colour-grid check favoured the true pairing in 776 of 777 comparisons. These exploratory results cover one session per era excluded from training; evaluation results informed development and the choice of reported variants. They measure emission-recording correspondence within these recordings and do not establish realness, liveness, capture verification or forgery detection.

Shelf material on those terms: the two lines above, with the pictures (`ol2024_mean` on 050046: the supplied bookshelf scene with changing illumination and an inaccurate participant; for 2023 the emission and real columns of the held-session sheet), and this paragraph beside them.

## Results, 2024 track (December 2024, seven sessions, 448 pairs)

### The train-free statistic: correspondence in the data before any model

Grid-cell colour correlation between an emission and its own recording against the recording of another frame of the same session under one seeded shuffle per grid (seed 0; not a strict derangement, a partner can recur), emission channels in the physically matched order (`kit/channel_check.py`: the stored emission order is the reverse of the stored recording order in both eras); `kit/coupling_stat.py` is the 6 September kit's predeclared statistic. AUROC with 95 percent frame-bootstrap interval, paired wins in brackets; a [1.000, 1.000] interval reflects perfect ordering in these sampled scores, not certainty about future performance.

| held-out set | grid 8 | grid 16 | grid 32 | grid 64 |
|---|---|---|---|---|
| tails (42) | 0.857 [0.804, 0.918] (42/42) | 0.993 [0.976, 1.000] (42/42) | 0.999 [0.997, 1.000] (42/42) | 1.000 [1.000, 1.000] (42/42) |
| held-out 050046 (64) | 0.857 [0.810, 0.907] (63/64) | 0.982 [0.958, 0.999] (64/64) | 0.999 [0.997, 1.000] (64/64) | 1.000 [1.000, 1.000] (64/64) |

In the as-stored channel order the same statistic reads 0.952 [0.915, 0.984] at grid 32 on the tails (`coupling_test.json`), which is why the channel check mattered.

### Fidelity of the generated recordings (PSNR dB / SSIM, 95 percent intervals)

Compared at each model's own output scale; PSNR at a lower resolution is not comparable with PSNR at a higher one. Fidelity is a check that nothing is broken and a statement of scale, not the claim. The training-mean baseline is a deterministic sample of up to 200 training captures (the session's own for the tails; for a whole held-out session a global sample: 2024 the first 200 sorted training captures, four of the six training sessions; 2023 200 evenly strided), a valid constant baseline but not the exact image handed to the mean-prior model, whose prior averages all 342 training captures; an exact supplied-prior-copy comparison was not run. Observation, not explanation: the generators carry emission-specific changes while overall fidelity remains below the sampled training-mean baseline; motion-related error and model error were not separated.

| predictor | tails (42) PSNR | tails (42) SSIM | held-out 050046 (64) PSNR | held-out 050046 (64) SSIM |
|---|---|---|---|---|
| **ol2024_mean** (full frame + mean-scene prior, 1024x576) | 22.44 [22.07, 22.82] | 0.720 [0.708, 0.731] | 22.36 [22.08, 22.63] | 0.720 [0.713, 0.728] |
| **ol2024_full** (full frame, 1024x576, stopped at 57 epochs) | 19.07 [18.90, 19.25] | 0.463 [0.456, 0.471] | 19.04 [18.88, 19.20] | 0.467 [0.462, 0.472] |
| **ol2024_b4** (512 random crops, 2048x1152 output) | 16.81 [16.69, 16.93] | 0.455 [0.451, 0.459] | 16.77 [16.64, 16.90] | 0.458 [0.455, 0.461] |
| baseline at 1024 wide: training-mean capture | 23.64 [23.46, 23.81] | 0.792 [0.785, 0.799] | 23.63 [23.38, 23.84] | 0.792 [0.786, 0.798] |
| baseline at 1024 wide: previous real capture | 21.05 [20.77, 21.31] | 0.692 [0.677, 0.707] | 21.09 [20.80, 21.38] | 0.692 [0.681, 0.703] |
| baseline at 1024 wide: the emission itself | 8.58 [8.55, 8.62] | 0.238 [0.226, 0.250] | 8.55 [8.50, 8.59] | 0.239 [0.229, 0.249] |
| baseline at the pair resolution: training-mean capture | 23.58 [23.40, 23.75] | 0.828 [0.824, 0.833] | 23.57 [23.32, 23.80] | 0.828 [0.824, 0.832] |
| baseline at the pair resolution: previous real capture | 20.99 [20.72, 21.25] | 0.737 [0.727, 0.748] | 21.03 [20.74, 21.31] | 0.738 [0.730, 0.746] |
| baseline at the pair resolution: the emission itself | 8.58 [8.55, 8.61] | 0.351 [0.343, 0.359] | 8.54 [8.50, 8.59] | 0.352 [0.344, 0.360] |

### Does the generated recording identify its own emission? (generator as verifier)

The real recording is held fixed and another generated image is substituted: for every held-out frame t, corr(G(E_t) − M, B_t − M) is compared with corr(G(E_s) − M, B_t − M), s another held-out frame of the same session drawn independently with seed 20260909 (self excluded, partner reuse possible), M the sampled mean training capture. Paired wins ask, frame by frame, whether the recording generated from the true emission is the closer one; the pooled AUROC also mixes in how similar frames are to each other overall, so read the paired rate first (the kit's own instruction). The colour view averages the three channel correlations, which matters because these emission patterns vary in hue far more than in luminance; the grayscale view is the kit's.

| model | view | tails (42): paired wins, pooled AUROC | held-out 050046 (64): paired wins, pooled AUROC |
|---|---|---|---|
| **ol2024_mean** | colour residual | 42/42 = 1.000 [1.000, 1.000], 0.936 [0.899, 0.971] | 64/64 = 1.000 [1.000, 1.000], 0.962 [0.936, 0.984] |
| **ol2024_mean** | grayscale residual | 42/42 = 1.000 [1.000, 1.000], 0.848 [0.808, 0.898] | 64/64 = 1.000 [1.000, 1.000], 0.888 [0.853, 0.927] |
| **ol2024_full** | colour residual | 37/42 = 0.881 [0.786, 0.976], 0.870 [0.799, 0.934] | 57/64 = 0.891 [0.812, 0.953], 0.802 [0.741, 0.864] |
| **ol2024_full** | grayscale residual | 37/42 = 0.881 [0.786, 0.976], 0.849 [0.774, 0.921] | 56/64 = 0.875 [0.797, 0.953], 0.763 [0.699, 0.832] |
| **ol2024_b4** | colour residual | 28/42 = 0.667 [0.524, 0.810], 0.583 [0.498, 0.675] | n/a |
| **ol2024_b4** | grayscale residual | 17/42 = 0.405 [0.262, 0.548], 0.453 [0.362, 0.539] | 17/64 = 0.266 [0.156, 0.375], 0.341 [0.273, 0.404] |

### Does the trained discriminator recognise a matched pair? (discriminator as verifier)

The run's own discriminator scores the real pair D(E_t, B_t) against a capture swap D(E_t, B_s) (true emission, another frame's recording) and an emission swap D(E_s, B_t) (another frame's emission, true recording); the score is the mean of the final prediction maps over the three scales; the partner s comes from a PCG64-seeded within-session bijection without self-matches, recorded before scoring and shared by every discriminator on that set (`d_derangement_*.json`); full frame at the model's scale, and the 512 centre crop. On the held-out sessions the saved draws contain almost no adjacent-frame swaps (2 of 64 in 2024, 1 of 777 in 2023; median index separations 22 and 243), so hard temporal negatives are untested there; the seven-frame 2024 tails contain 17 adjacent swaps of 42 (median separation 2), the 2023 tails 9 of 262 (median 21).

| discriminator | negative | tails (42) AUROC (paired wins) | held-out 050046 (64) AUROC (paired wins) |
|---|---|---|---|
| **ol2024_mean** own D | capture swap, full frame | 0.962 [0.925, 0.992] (42/42) | 0.934 [0.891, 0.969] (60/64) |
| **ol2024_mean** own D | emission swap, full frame | 0.963 [0.925, 0.992] (42/42) | 0.944 [0.909, 0.976] (64/64) |
| **ol2024_mean** own D | capture swap, 512 centre crop | 0.905 [0.836, 0.965] (39/42) | 0.865 [0.801, 0.921] (56/64) |
| **ol2024_full** own D | capture swap, full frame | 0.968 [0.933, 0.993] (41/42) | 0.948 [0.914, 0.979] (63/64) |
| **ol2024_full** own D | emission swap, full frame | 0.944 [0.897, 0.986] (42/42) | 0.951 [0.922, 0.977] (64/64) |
| **ol2024_full** own D | capture swap, 512 centre crop | 0.848 [0.756, 0.926] (34/42) | 0.826 [0.748, 0.897] (55/64) |
| **ol2024_b4** own D | capture swap, full frame | 0.566 [0.488, 0.653] (24/42) | 0.553 [0.460, 0.642] (35/64) |
| **ol2024_b4** own D | emission swap, full frame | 0.582 [0.486, 0.676] (24/42) | 0.550 [0.480, 0.619] (34/64) |
| **ol2024_b4** own D | capture swap, 512 centre crop | 0.706 [0.586, 0.815] (25/42) | 0.618 [0.509, 0.722] (39/64) |

## Results, 2023 track (April 2023, eight sessions, 3,399 pairs)

The coupling statistic leads this track: it needs no model and it is the cleanest result here. The discriminator rows are supporting evidence.

### The train-free statistic: correspondence in the data before any model

Grid-cell colour correlation between an emission and its own recording against the recording of another frame of the same session under one seeded shuffle per grid (seed 0; not a strict derangement, a partner can recur), emission channels in the physically matched order (`kit/channel_check.py`: the stored emission order is the reverse of the stored recording order in both eras); `kit/coupling_stat.py` is the 6 September kit's predeclared statistic. AUROC with 95 percent frame-bootstrap interval, paired wins in brackets; a [1.000, 1.000] interval reflects perfect ordering in these sampled scores, not certainty about future performance.

| held-out set | grid 8 | grid 16 | grid 32 | grid 64 |
|---|---|---|---|---|
| tails (262 paired / 264) | 0.919 [0.899, 0.937] (262/262) | 0.920 [0.900, 0.939] (259/262) | 0.910 [0.888, 0.931] (258/262) | 0.897 [0.875, 0.918] (260/262) |
| held-out 1682718815 (777) | 0.928 [0.917, 0.938] (777/777) | 0.951 [0.942, 0.959] (776/777) | 0.944 [0.935, 0.954] (770/777) | 0.944 [0.935, 0.953] (773/777) |

In the as-stored channel order the same statistic reads 0.639 [0.610, 0.668] at grid 32 on the tails (`coupling_test.json`), which is why the channel check mattered.

### Fidelity of the generated recordings (PSNR dB / SSIM, 95 percent intervals)

Compared at each model's own output scale; PSNR at a lower resolution is not comparable with PSNR at a higher one. Fidelity is a check that nothing is broken and a statement of scale, not the claim. The training-mean baseline is a deterministic sample of up to 200 training captures (the session's own for the tails; for a whole held-out session a global sample: 2024 the first 200 sorted training captures, four of the six training sessions; 2023 200 evenly strided), a valid constant baseline but not the exact image handed to the mean-prior model, whose prior averages all 342 training captures; an exact supplied-prior-copy comparison was not run. Observation, not explanation: the generators carry emission-specific changes while overall fidelity remains below the sampled training-mean baseline; motion-related error and model error were not separated.

| predictor | tails (262 paired / 264) PSNR | tails (262 paired / 264) SSIM | held-out 1682718815 (777) PSNR | held-out 1682718815 (777) SSIM |
|---|---|---|---|---|
| **ol2023_full** (full frame, 1024x640) | 17.74 [17.66, 17.82] | 0.411 [0.409, 0.413] | 17.61 [17.58, 17.63] | 0.404 [0.404, 0.405] |
| **ol2023_b4** (512 random crops, 1792x1120 output) | 17.58 [17.47, 17.70] | 0.461 [0.458, 0.464] | 17.21 [17.18, 17.24] | 0.449 [0.448, 0.449] |
| baseline at 1024 wide: training-mean capture | 22.73 [22.59, 22.87] | 0.795 [0.793, 0.797] | 21.93 [21.89, 21.97] | 0.700 [0.699, 0.700] |
| baseline at 1024 wide: previous real capture | 20.65 [20.52, 20.78] | 0.728 [0.725, 0.730] | 20.26 [20.22, 20.29] | 0.715 [0.714, 0.716] |
| baseline at 1024 wide: the emission itself | 7.49 [7.46, 7.51] | 0.235 [0.234, 0.237] | 7.59 [7.58, 7.60] | 0.244 [0.243, 0.244] |
| baseline at the pair resolution: training-mean capture | 22.69 [22.55, 22.82] | 0.803 [0.801, 0.805] | 21.87 [21.83, 21.91] | 0.724 [0.724, 0.725] |
| baseline at the pair resolution: previous real capture | 20.60 [20.47, 20.73] | 0.728 [0.726, 0.730] | 20.21 [20.18, 20.25] | 0.717 [0.716, 0.718] |
| baseline at the pair resolution: the emission itself | 7.48 [7.46, 7.51] | 0.277 [0.275, 0.278] | 7.59 [7.58, 7.59] | 0.287 [0.287, 0.288] |

### Does the generated recording identify its own emission? (generator as verifier)

The real recording is held fixed and another generated image is substituted: for every held-out frame t, corr(G(E_t) − M, B_t − M) is compared with corr(G(E_s) − M, B_t − M), s another held-out frame of the same session drawn independently with seed 20260909 (self excluded, partner reuse possible), M the sampled mean training capture. Paired wins ask, frame by frame, whether the recording generated from the true emission is the closer one; the pooled AUROC also mixes in how similar frames are to each other overall, so read the paired rate first (the kit's own instruction). The colour view averages the three channel correlations, which matters because these emission patterns vary in hue far more than in luminance; the grayscale view is the kit's.

| model | view | tails (262 paired / 264): paired wins, pooled AUROC | held-out 1682718815 (777): paired wins, pooled AUROC |
|---|---|---|---|
| **ol2023_full** | colour residual | 192/262 = 0.733 [0.679, 0.786], 0.655 [0.625, 0.686] | 597/777 = 0.768 [0.739, 0.798], 0.697 [0.678, 0.716] |
| **ol2023_full** | grayscale residual | 149/262 = 0.569 [0.508, 0.626], 0.542 [0.514, 0.571] | 471/777 = 0.606 [0.571, 0.641], 0.566 [0.549, 0.584] |
| **ol2023_b4** | colour residual | 226/262 = 0.863 [0.821, 0.901], 0.585 [0.573, 0.599] | 658/777 = 0.847 [0.821, 0.871], 0.614 [0.604, 0.624] |
| **ol2023_b4** | grayscale residual | 200/262 = 0.763 [0.710, 0.813], 0.551 [0.541, 0.563] | 555/777 = 0.714 [0.682, 0.745], 0.558 [0.550, 0.567] |

### Does the trained discriminator recognise a matched pair? (discriminator as verifier)

The run's own discriminator scores the real pair D(E_t, B_t) against a capture swap D(E_t, B_s) (true emission, another frame's recording) and an emission swap D(E_s, B_t) (another frame's emission, true recording); the score is the mean of the final prediction maps over the three scales; the partner s comes from a PCG64-seeded within-session bijection without self-matches, recorded before scoring and shared by every discriminator on that set (`d_derangement_*.json`); full frame at the model's scale, and the 512 centre crop. On the held-out sessions the saved draws contain almost no adjacent-frame swaps (2 of 64 in 2024, 1 of 777 in 2023; median index separations 22 and 243), so hard temporal negatives are untested there; the seven-frame 2024 tails contain 17 adjacent swaps of 42 (median separation 2), the 2023 tails 9 of 262 (median 21).

| discriminator | negative | tails (262 paired / 264) AUROC (paired wins) | held-out 1682718815 (777) AUROC (paired wins) |
|---|---|---|---|
| **ol2023_full** own D | capture swap, full frame | 0.616 [0.578, 0.653] (164/262) | 0.646 [0.619, 0.673] (508/777) |
| **ol2023_full** own D | emission swap, full frame | 0.613 [0.597, 0.631] (228/262) | 0.644 [0.630, 0.658] (622/777) |
| **ol2023_full** own D | capture swap, 512 centre crop | 0.550 [0.499, 0.602] (145/262) | 0.563 [0.534, 0.593] (442/777) |
| **ol2023_b4** own D | capture swap, full frame | 0.855 [0.831, 0.878] (256/262) | 0.992 [0.990, 0.995] (775/777) |
| **ol2023_b4** own D | emission swap, full frame | 0.853 [0.832, 0.877] (262/262) | 0.993 [0.991, 0.996] (777/777) |
| **ol2023_b4** own D | capture swap, 512 centre crop | 0.892 [0.864, 0.917] (232/262) | 0.931 [0.919, 0.942] (725/777) |

## Data

**2024 track.** The seven physical projector-camera sessions of 19 December 2024. Six are the public unanchored archive `r2:truthbeam/archive/2024/truth_beam_20241219_unanchored/v1/` (sessions 044052, 044529, 050648, 051150, 051629, 052040; `dummy_run` true, chain stored locally, no RSK submission); the seventh is the anchored companion `20241219_050046` (`r2:truthbeam/pinata/20241219_050046_TB.h5`, `dummy_run` false, final RSK transaction recorded). Each HDF5 holds `emissions` (64, 1080, 1920, 3) uint8, `recordings` (64, 4600, 5320, 3) uint8 and `hashes` (64, 32). All seven files verified by SHA-256 against `_control/MANIFEST.jsonl` and the RELEASE.json payload hash on the box (`oldlight/records/logs/bootstrap.log`). 448 pairs.

**2023 track.** The eight April 2023 NumPy sessions: seven in `archive/2023/old_truth_beams/v1/` (1680410249, 1680410569, 1680412337, 1681945334, 1682013847, 1682014432, 1682712156) and the PoliePals trailer session `1682718815` in `archive/2023/truth_beam_poliepals_trailer/v1/`. Emissions are 1024x1024x3 float arrays on a 0..255 scale (one float64 file per session, the rest float32), reports 1536x2048x3 uint8. Pairs are matched on the six-digit index prefix; 1682013847 and 1682014432 each have one emission without a report, dropped. 6,800 arrays verified by SHA-256 against the two manifests. 3,399 pairs. Recorder facts on record (an internal programme note, not published): Daheng Galaxy camera through gxipy, fixed 16,660 microsecond exposure, emission shown fullscreen at 1920x1200; the camera model is not on record.

## Geometry (decided from the data, `RUN_LOG.md` (on-box) 01:34Z to 01:40Z)

The choice of crop and orientation was made with the train-free grid-coupling statistic under the four axis orientations and the bright region of the mean luminance (`kit/orient_check2.py`), before any pair was built.

- 2024: the projected rectangle occupies x 320..4888, y 664..3360 of the 5320x4600 frame in every session; identity orientation is the only one with positive coupling (+0.033 to +0.043 at grids 16 to 64; the other orientations within 0.006 of zero). Crop (x0, y0, x1, y1) = (220, 660, 5020, 3360), 4800x2700, exactly 16:9, Lanczos to 2048x1152. The emission (1920x1080) goes bicubic to 2048x1152, the 6 September kit's convention. Recorded in `records/SPLIT_2024.json`.
- 2023: the projection occupies x 96..1824, y 272..1368 of the 2048x1536 report (16:10, as the projector's 1920x1200 output). The camera was mounted inverted relative to the projector: rot180 is the only orientation with positive coupling (+0.103 / +0.095 / +0.088 / +0.082 at grids 8 to 64; others within 0.009). Crop (64, 248, 1856, 1368), 1792x1120, exactly 16:10, rotated 180 degrees so the scene reads upright and the emission maps onto it without a flip; no rescale of the report. The square emission is resized bicubic to 1792x1120, which reproduces the recorder's fullscreen stretch; values are clipped and cast to uint8 without rescaling. `records/SPLIT_2023.json`.

## Holdouts

Trained once per configuration, scored twice: the holdouts are excluded from weight training, and they are not an untouched final test (see the disclosure below the table). From every training session the contiguous last tenth of the frames by index is held out (the in-session tails, the 6 September kit's split), and one whole session is held out entirely: for 2024 `20241219_050046`, the session the January 2025 run also held out (so the two are comparable; an internal programme note, not published), and for 2023 `1682718815`, the trailer, the last session by timestamp.

| track | train pairs | in-session tails | whole held-out session |
|---|---|---|---|
| 2024 | 342 (six sessions x frames 0..56) | 42 (six x frames 57..63) | 64 (050046) |
| 2023 | 2,358 | 264 | 777 (1682718815) |

**Adaptive reuse, disclosed.** The held-out scores were read during the night and steered it: the 2024 crop model's tail and 050046 results (03:35Z) prompted abandoning the 1024-crop attempt and changing to full frames; the full-frame model's epoch-25 tail images and fidelity (04:43Z) prompted stopping it and adding the mean-scene prior; the orientation and crop check (01:37Z) sampled three frames of 050046 among its twelve. Split records and preparation code give disjoint counts (342/42/64 and 2,358/264/777) and the mean prior is built from the 342 training captures only, so "excluded from weight training" holds; "untouched final test" does not, and the results are labelled exploratory throughout. Six runs were attempted and five evaluated: `ol2024_hires` (1024 crops) was abandoned after nine epochs; `ol2024_full` was stopped after 57 epochs and evaluated from its epoch-56 `latest` checkpoint.

## Models

Two recipes per track, both static pix2pixHD, trained once each and tested on the same held-out frames.

**Crop recipe (`ol2024_b4`, `ol2023_b4`).** The 6 September kit's `tb_base_b4`: 512 random crops, batch 4. On this data it fails in a way at which the 6 September runs' fidelity numbers already hinted: a network trained on random crops of a translation-invariant noise emission has no positional cue, so it cannot learn the position-dependent scene and renders a blotchy texture (contact sheets under `results/<track>/ol*_b4/`). Reported for the record and as the comparison the kit invites.

**Full-frame recipe (`ol2024_full`, `ol2023_full`).** The January 2025 run's idea (`resize_or_crop none`) at half width so it fits the 40 GB card without fp16: `--resize_or_crop scale_width --loadSize 1024`, batch 2, whole frames of 1024x576 (2024) and 1024x640 (2023) every step, so border cues let the network learn the fixed background while the emission drives the pattern. Evaluated at the same 1024-wide scale, with the baselines and the trained discriminator scored at that scale too.

Common to both: NVIDIA/pix2pixHD at commit 14b3b3c7 with the kit's modern-PyTorch patches plus `math.gcd` for `fractions.gcd`; netG local, ngf 32, n_downsample_global 4, n_blocks_global 9, one local enhancer; multiscale discriminator num_D 3, n_layers_D 3, ndf 64; label_nc 0 (RGB emission input), no instance maps, no flips (fixed geometry), 512 random crops, batch 4, GAN + feature-matching + VGG losses, Adam 0.0002, first epoch with the global generator frozen. Epoch counts were set from the training-set sizes: `ol2024_b4` 160 + 40 decay epochs (86 iterations each, about 68k samples), `ol2023_b4` 24 + 6 (590 each, about 71k samples), `ol2024_full` 80 + 20 (171 each), `ol2023_full` 16 + 4 (1,179 each). Full options in `records/checkpoints/<run>/opt.txt`, losses in `loss_log.txt`. Environment: one A100-SXM4-40GB, torch 2.7.0+cu126, torchvision 0.22.0, numpy 2.2.6, Python 3.10.12 (`RUN_LOG.md` (on-box) 01:33Z).

## Evaluation protocol

All numbers are on held-out frames excluded from weight training (the adaptive reuse of the holdouts is disclosed under Holdouts); the 95 percent intervals are frame bootstraps (5,000 resamples, matched and its paired mismatch travelling together; `kit/ci_summary.py`).

1. **Fidelity**: PSNR and SSIM of the generated recording against the real one at the model's output resolution (`kit/eval_p2p.py`, the kit's, verbatim), beside three trivial predictors at the same resolution (`kit/eval_baselines.py`): the emission itself, the previous held-out real capture, and a sampled training-mean capture: the mean of up to 200 training captures, the session's own for the tails and, for a whole held-out session, a global sample (2024: the first 200 sorted training captures, four of the six training sessions; 2023: 200 evenly strided across all training captures). That constant is a valid baseline but not the exact image handed to `ol2024_mean`, whose prior averages all 342 training captures.
2. **Generator as verifier** (`kit/eval_g_verifier.py`): does the generated capture identify its own emission? The real recording is held fixed and another *generated* image is substituted: for every held-out frame t, corr(G(E_t) − M, B_t − M) is compared with corr(G(E_s) − M, B_t − M), where s is another held-out frame of the same session drawn independently with seed 20260909 (self excluded; a partner may recur: 40 distinct partners among the 64 frames of 050046, 487 among the 777 of the trailer) and M is the mean training capture (the session's own where it has training captures, otherwise the mean of the first 200 sorted training captures). The residual view subtracts M; the full view does not. The kit's view is grayscale; the colour view added tonight averages the three channel correlations, at 512x288 (2024) and 512x320 (2023). Paired wins and pooled AUROC.
3. **Discriminator as verifier** (`kit/eval_d_verifier_v3.py`, the kit's corrected v2 approach): the run's own trained D scores the real pair D(E_t, B_t) against a capture swap D(E_t, B_s) and an emission swap D(E_s, B_t); the score is the mean of the final prediction maps over the three scales; the partner map is a PCG64-seeded within-session bijection without self-matches, recorded before scoring and shared by every discriminator on that set; full frame at the model's scale and the 512 centre crop. The saved draws are mostly distant frames: on the held-out sessions only 2 of 64 (2024) and 1 of 777 (2023) swaps are adjacent frames, with median index separations 22 and 243, so hard temporal negatives are untested there; the seven-frame tails happen to contain many (17 of 42 adjacent swaps in 2024, median separation 2; 9 of 262 in 2023, median 21). The January 2025 pix2pixHD release is not evaluated in this package; it remains an artefact-only release with no performance claim.
4. **Train-free coupling statistic** (`kit/coupling_stat.py`, the kit's predeclared statistic): the emission and the capture are each reduced to a g x g grid of mean colours, standardised per channel over the grid (no training-mean subtraction), and correlated channel by channel; matched against the capture of another frame of the same session under one seeded shuffle per grid (seed 0; the shuffle's self-match repair can repeat a partner, so it is not a strict derangement: 62 distinct partners among 64 on 050046, 776 among 777 on the trailer at grid 16), grids 4 to 64, no learning involved.
5. **Renders**: contact sheets of emission | real recording | generated recording for evenly strided held-out frames, one per test set per run.

## Caveats, stated plainly

- **Adaptive reuse of the holdouts.** The held-out scores were read during the night and steered the recipe changes and the choice of reported variants (details under Holdouts). Excluded from weight training: yes. Untouched final test: no. Every result here is exploratory.

- **Tiny corpus on the 2024 track.** 342 training pairs; 42 tail frames and one 64-frame session for testing. The intervals are wide and the whole-session result rests on one session. The 2023 track is seven times larger and its intervals are correspondingly tighter.
- **In-session tails versus a whole held-out session.** The tails come from sessions the model trained on (same scene, same participant position range); the whole held-out session is the stronger generalisation test, qualified by the disclosed adaptive evaluation (its scores were read during the night and steered the recipe changes), and is reported beside them everywhere.
- **No realness, liveness or verification claim.** These are physical projector-camera captures of a masked participant, evaluated for emission-to-recording correspondence and image fidelity. Nothing here tests forgery, replay or an adversary; a discriminator that ranks a matched pair above a within-session swap is not a verifier of anything beyond that swap.
- **Execution on physical captures.** All frames are the original recordings; nothing was re-captured or simulated. Pairs were rebuilt from the archives with the crops, rotation and channel handling stated above; the residual keystone of the 2023 rig (about -14 percent vertical, per the data-look desk) is left to the network.
- **Fidelity is not the claim, and its deficit is not explained.** The generators carry emission-specific changes while their overall fidelity stays below the sampled training-mean baseline; motion-related error and model error were not separated (no person mask, static-region or controlled-motion analysis was run). The baseline is a deterministic 200-capture sample, not the exact prior handed to `ol2024_mean`; an exact supplied-prior-copy comparison was not run. Read the correspondence tests for the claim and the fidelity table for scale.
- **Hard temporal negatives untested.** The saved discriminator draws on the held-out sessions contain almost no adjacent-frame swaps (2 of 64 in 2024, 1 of 777 in 2023; median index separations 22 and 243). The bijective within-session swaps balance emissions and captures between classes, so bookshelf, session identity or capture alone cannot explain the pooled separation, but transfer to other scenes and pair-specific shortcuts involving motion and time are not excluded.
- **Intervals.** Frame bootstraps that resample frames with their existing mismatches; they omit temporal dependence, shared partners, negative-draw variation and model or grid selection. A [1.000, 1.000] interval reflects perfect ordering in these sampled scores, not certainty about future performance. One session per era cannot establish uncertainty across sessions.
- **Stopped and abandoned runs.** `ol2024_hires` (1024 crops) was abandoned after nine epochs; `ol2024_full` was stopped at 57 of 100 epochs and evaluated from its epoch-56 latest checkpoint; `ol2023_full` finished its 20 epochs before the 06:45Z cutoff. Six attempted, five evaluated.
- **What is published.** The results, records, logs, contact sheets and kit are published in this package and on the data layer; the checkpoints and the per-frame generated outputs remain on the persistent filesystem of the rented environment and are not published.

## Box, cost, provenance

One `gpu_1x_a100_sxm4` (A100-SXM4-40GB, 30 vCPU, 216 GiB) in us-east-1 with the persistent filesystem mounted: launched 01:01:08Z, terminate accepted 06:57:58Z, fleet listing empty at 06:59:48Z. About 5.95 hours at USD 1.99 per hour: about **USD 11.8** compute before VAT (Lambda bills to the minute). No 8x box had capacity in us-east-1 all night. Storage: only the new directory `oldlight_20260909` was added to the filesystem (checkpoints of five runs, about 6 GB, and per-frame outputs); nothing else there was read for writing, modified or deleted.

Data provenance: the public archives at `https://data.truthbeam.com` (`archive/2024/truth_beam_20241219_unanchored/v1/`, `pinata/20241219_050046_TB.h5`, `archive/2023/old_truth_beams/v1/`, `archive/2023/truth_beam_poliepals_trailer/v1/`), every file verified by SHA-256 against the archive manifests on the box before use (`oldlight/records/logs/bootstrap.log`). Code: NVIDIA/pix2pixHD commit 14b3b3c7fff413086e3b58df52096f16b6891172 plus the patches in `kit/box_bootstrap.sh`; the 6 September kit (its statistic is published as `dark-lantern/results/train_free_coupling_20260906/scripts/coupling_stat.py`); tonight's kit `kit/` (as-run hashes in `KIT_SHA256SUMS_as_run.txt`; the package ledger covers the published bytes). Environment: torch 2.7.0+cu126, torchvision 0.22.0+cu126, numpy 2.2.6, h5py 3.16.0, scikit-image 0.25.2, Python 3.10.12, driver 570.148.08.

## Audit note

Every number in the tables above was generated by the desk's report assembler (on-box) from `ci_summary.json`, which `kit/ci_summary.py` computes from the per-frame JSON files pulled from the box (`results/<track>/...`); the model-free figures were checked against the box logs at the time (`RUN_LOG.md` (on-box) 02:03Z, 02:51Z). The kit scripts were reused verbatim (`kit/eval_p2p.py`) or parametrised without changing the statistics (`kit/eval_baselines.py`, `kit/eval_g_verifier.py`, `kit/coupling_stat.py`, `kit/eval_d_verifier_v3.py` from the kit's v2; `roc_auc_score` replaced by an arithmetically identical Mann-Whitney AUROC). New tonight: the mean-prior dataset (`kit/meanprior_dataset.py`), the colour view of the generator verifier, the channel-order option of the coupling statistic, the orientation and channel checks. Open items: a 2023 mean-prior run; a second seed per configuration; hard negatives (adjacent frames) for the discriminator test; block-aware intervals for serial frames; a homography-warped pairing using the data-look desk's per-session H.

## Log

- 0.1 (2026-09-09, BOSUN) — assembled at the end of the Lambda run; every table generated from `ci_summary.json`; awaits the principal's reading. Not for release.
- 1.0 (2026-09-09, BOSUN) — Astra results audit r1 (`../audits/astra/oldlight_r1_verdict.md`, PUBLISHABLE WITH FIXES) applied with no new training: adaptive reuse of the holdouts disclosed and the results labelled exploratory; the generator test described exactly (another generated image is substituted, the real recording held fixed; seeded draw with partner reuse); capture swap and emission swap defined; the baseline identity corrected (200-capture sample, not the supplied prior) and the causal explanation of the fidelity deficit replaced by an observation; the near-absence of adjacent-frame negatives stated; the 2023 section led by the coupling statistic with the discriminator supporting; the claim that `ol2023_full` was weaker on every test corrected (higher pooled colour-residual AUROC, fewer paired wins); Astra's two shelf lines and paragraph adopted; the coupling draw no longer called a derangement; gallery rebuilt (mean model, channel-corrected coupling, colour versus grayscale labels, resolution-matched baselines, a comparison number since removed from the published copy). The 0.937 in the earlier desk reply was 0.936. Not for release.
- published copy (2026-09-09, BOSUN): paths and the desk's operational sentences redacted as `../REDACTION.md` records; every table and number unchanged. The two comparison rows and the caveat on the January 2025 discriminator are not published; that release remains an artefact-only release with no performance claim.
