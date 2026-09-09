---
version: 1.2
date: 2026-09-09
status: the questions a reader of this package is likely to ask, answered from its files; where the answer is a decision of the principal that has not been taken, the entry says so
author: BOSUN for Cathal Ryan Hynes
---

# Questions a reader will ask, and the answers the package gives

**1. What, in one sentence, was shown?** That the April 2023 and December 2024 Truth Beam recordings carry a measurable,
frame-by-frame trace of the pattern that was projected when each frame was taken, measured three ways: by a fixed
statistic with no model (every one of 1,032 comparisons), by pix2pixHD models trained on the recordings (64 of 64 on the
held-out December session), and by a diffusion evaluator trained on the 2026 recordings (447 of 448 December frames with no
fine-tuning, pooled AUROC 0.657). `RESULTS.md`.

**2. What is not shown?** That any recording is real, live or physically captured; that a forgery would be detected; that
any method survives an adversary; that anything transfers to a third scene. `CLAIM_BOUNDARY.md`.

**3. Is any of this proved in zero knowledge?** No. The ZeeBeam and zkdiff proofs concern the ARM-C evaluator on the 2026
August session. ARM-I is a sibling with a different conditioning input and no proof; the pix2pixHD models and the
statistic have none either. `CLAIM_BOUNDARY.md`, third paragraph.

**4. How can a model prefer the true pattern on 447 of 448 frames and have a pooled AUROC of only 0.657?** Because the two
numbers ask different questions. The paired fraction compares each frame with itself: under the true pattern the
residual is lower than under the wrong ones on almost every frame. The pooled AUROC pools all correct residuals against all
wrong-mean residuals across frames, and on the 2024 rig the residual level varies from frame to frame (the participant
moves through the beam, the pattern period varies) by more than the 6 percent margin between true and wrong, which drags
the pooled figure toward 0.5. In-distribution the margin is about 200 percent and both numbers are 1.000. The report shows
the two histograms (`armi_cross_configuration/figures/residual_hist_armi_2026_s20260908.png`). Both numbers are always
quoted together. `armi_cross_configuration/REPORT.md`, the forward-transfer section.

**5. Why did the raw 2023 recordings give chance for ARM-I when the same statistic gave 1.000 for the grid method?** The
grid statistic aligned the projected region first (its "crop"); ARM-I's published posture is the whole frame with no
crop and no alignment, and the 2023 camera saw the pattern upside down, with a 14 percent keystone, through a different
sensor and colour pipeline, with a smoother pattern family. When the 2023 recordings were warped into the emission frame
with the per-session homographies, the 2026-trained ARM-I preferred the true 2023 emission on 91 percent of frames (AUROC 0.543), and a
model trained across all three rigs on the aligned inputs reached 1.000 on the held-out trailer. The raw null is a limit
of zero-shot transfer under a change of recorded geometry, and is published as such. `armi_cross_configuration/REPORT.md`,
the 2023 and variant (b) sections.

**6. Are the homographies a leak?** They were fitted by the data-look desk from the target sessions' own emission and
recording pairs (8 to 25 frames per 2023 session, all 64 per 2024 session), so they are a retrospective calibration and
the reports say so. Removing the fitted frames from the evaluation does not change the conclusions (752 of 752 on the
trailer without its 25 calibration rows; 2,981 of 3,280 on aligned 2023 without the 79 fitted frames), but a geometry
fitted on the target and applied to every remaining frame is a benefit those checks do not bound. The grid statistic's
crop uses recordings alone (no emission values, no pair labels) and one transform per session; its orientation choice uses
four matched frames per session, and excluding those leaves 522 of 522 and 394 of 394. `CLAIM_BOUNDARY.md`, fourth
paragraph.

**7. Were the held-out sessions used in training?** No weights were trained on them; the training logs and split records
show it and both ARM-I audits and the pix2pixHD audit checked it (`AUDIT_TRAIL.md`). Three qualifications are disclosed:
ARM-I monitored small samples of the held-out sessions during training (printed every 2,000 steps, no gradient, no
checkpoint selection); the pix2pixHD held-out scores were read during the night and steered the recipe changes, which is
why those results are labelled exploratory; and the 2026 evaluation blocks are development validation, scored repeatedly
by the programme.

**8. Why is the December 2024 track of the pix2pixHD work so small?** Seven sessions of 64 pairs exist, 342 pairs trained,
and one session of 64 pairs was excluded as the holdout. The intervals are wide and the whole-session result rests on one session; the 2023
track is seven times larger. `pix2pixhd_old_light/REPORT.md`, caveats.

**9. What does "an average training scene" mean?** The `ol2024_mean` model received, beside the emission, the mean of the
342 training captures as three extra input channels (a six-channel input), so it did not have to learn the fixed
background from crops of a translation-invariant pattern. The crop recipe without it (`ol2024_b4`) learned no scene on 342
pairs; the whole-frame recipe without it recovered the correspondence but not the scene. The prior is the training
captures' mean only. `pix2pixhd_old_light/REPORT.md`, Models.

**10. Why is the pix2pixHD generators' image fidelity below a constant baseline, and is that a problem?** PSNR and SSIM
of the generated recordings sit below the sampled training-mean capture; the generators carry emission-specific changes
while overall fidelity stays below that baseline, and the report does not explain the deficit (motion error and model
error were not separated; the baseline is a 200-capture sample, not the exact prior the model was given). Fidelity is a
check that nothing is broken and a statement of scale, not the claim; the correspondence tests are the claim.

**11. Why is the January 2025 pix2pixHD discriminator not evaluated here?** That release remains an artefact-only release
with no performance claim, and this package does not evaluate it; the pix2pixHD report as published carries no comparison rows
for it (`REDACTION.md`). The pix2pixHD models of this package were trained on 9 September 2026 with the seventh 2024 session
excluded, the same session the January run excluded.

**12. Where are the checkpoints?** The fourteen ARM-I and ARM-C checkpoints (four arms, two unified models, eight
adaptations; 13.7 MB each) are on the data layer under `armi/checkpoints/<arm>/latest.pt` as documented derivatives of the
as-trained files (`REDACTION.md`; both digests in `PINS.json`). The pix2pixHD checkpoints remain on the persistent
filesystem of the rented environment and are not published; their options, loss logs and epoch markers are under
`pix2pixhd_old_light/records/`. **What this means for reproduction:** every numerical table and score plot regenerates from the
saved scores without any model, and the ARM-I and statistic contact sheets redraw from the bundle's example arrays and previews
(`REPRODUCE.md`, sections 1 and 2); the pix2pixHD contact sheets need the per-frame generated images, which are not published, so
the published sheets are the desk's; fresh inference, re-scoring recordings with the models, is possible for
ARM-I with the published checkpoints and for pix2pixHD only by retraining (`REPRODUCE.md`, section 3).

**13. Can the evaluation be re-run?** `REPRODUCE.md` is the runbook. **Two scopes, kept apart:** regenerating the numerical tables and
score plots from the saved scores needs this directory and the bundle and no model; fresh inference needs the checkpoints, which are
published for ARM-I and not for pix2pixHD. For ARM-I a full re-run works from the public data and the kit: `kit/download.sh`
fetches and verifies the archives from `kit/downloads.tsv`, `kit/src/precache_xcfg.py` builds the 96 x 112 inputs,
`kit/src/eval_xcfg.py` scores a checkpoint with the frozen statistic, `kit/src/eval_controls.py` runs the controls; the run
scripts take their directories from the environment variables `REPRODUCE.md` names. For the statistic,
`train_free_coupling_old_sessions/code/run_all.sh` is the production run over the public files (stage A per session, stage B
statistics, figures), and `code/stage_b_stats.py` recomputes every score from the bundle's cached grids. For pix2pixHD,
`pix2pixhd_old_light/kit/box_bootstrap.sh` fetches and verifies the data (the 2023 URL and digest lists it reads come from the
bundle's `oldlight/kit_inputs/` and are placed in the kit directory first), clones NVIDIA/pix2pixHD's default branch unless the
checkout already exists, applies the kit's patches and records the HEAD it used (the run's was `14b3b3c7fff413086e3b58df52096f16b6891172`,
in the bundle's `oldlight/records/logs/pix2pixHD_commit.txt`); it does not pin the checkout, so `REPRODUCE.md` clones and checks
that commit out before running it; `train_oldlight.sh` trains and `run_evals.sh` evaluates. Without the checkpoints the pix2pixHD evaluation
reproduces only from a retrained model, and GAN training is not bit-reproducible, so re-evaluated numbers will differ from the
published ones, which stand on the saved scores. Every numerical table and score plot regenerates from the shipped results files with the
kits' summary and figure scripts; the pix2pixHD contact sheets are the exception `REPRODUCE.md` states.

**14. Where do the numbers in `RESULTS.md` come from?** Each entry names its file. The desks' reports were generated or
copied from the results files (the statistic's report by `write_report.py` from the results JSON; the pix2pixHD tables by
the report assembler from `ci_summary.json`; the ARM-I numbers through `summarize.py` and `perlin_bins.py` from the
evaluation JSON), and each results audit reproduced them from the per-frame or per-row scores (`AUDIT_TRAIL.md`).

**15. What do the pictures show, and who is in them?** A masked participant in a recognisable indoor setting: the
bookshelf room for 2023 and 2024, CittaDel's wheelhouse (the principal's vessel) for the 2026 rows of the ARM-I contact sheets. The participant
wears a full face covering; no unobscured face appears. The images are not anonymised; identity may be inferred from
clothing, movement or context. `README.md`, "What the pictures show".

**16. The audits said the same bookshelf appears in all three eras. The report says otherwise. Which is right?** The
report. Both ARM-I audits repeated the desk's caveat, which rested on the data-look desk's misreading of the 2026 contact
sheet; the principal corrected it on 9 September and the desk verified the correction against the public d2 preview frame
1300. The audit texts are published as written at the time; `AUDIT_TRAIL.md` records the supersession.

**17. What is a "desk", and who is "the coordinator"?** BOSUN, the project's automated research assistant, ran the night's
work in several concurrent sessions, each called a desk in the reports (the ARM-I desk, the CPU statistics desk, the
pix2pixHD training desk, the data-look desk, a desk that checked the older discriminator, the release desk). The
coordinator is BOSUN's coordinating session, which set the follow-up runs. `README.md`, "Who did what".

**18. What was redacted, and what is held?** Machine paths, hostnames, provider instance identifiers and the operator's
handle in every copied text record; the operational sentences of the reports (spend caps, launch bookkeeping, internal
notices); the comparison rows on the January 2025 discriminator, which this package does not evaluate. Held: the desks' run logs and the second model's raw transcripts (they
quote the operator's private instructions), the desk's private gallery, the data-look desk's per-session contact and diagnostic sheets and gain maps, the pix2pixHD checkpoints and
per-frame generated outputs. `REDACTION.md`, `RESULTS.md` last section.

**19. Is the whole-frame statistic result (0.74 and 0.58) a failure?** It is positive but weaker, with intervals clear of
0.5, and it measures the statistic through a misregistration; the report calls it not shelf material on its own. The
alignment gap (0.740 to 1.000 in April, 0.561 to 0.999 in December at grid 16) is stated as part of the finding.

**20. How does this relate to the 6 September train-free result on d2 and v10?** It extends the same statistic, with the
same definitions and the same negative construction, to older recordings; it is not a directly comparable improvement over
the d2/v10 result (0.756 at grid 8, 902 of 975 paired), because the recordings and the alignment handling differ (a fixed
16:9 band then, a per-session projected-region quad now). `train_free_coupling_old_sessions/REPORT.md`, section 4c.

**21. Under what licence?** The Dark Lantern Research and Private Use Licence 1.2 (`LICENSE`, the repository's): non-commercial
research, teaching, verification and private study with attribution; redistribution of the materials, commercial use and
derived weights reserved. The recordings themselves are published by the Truth Beam project under its own terms at
`https://data.truthbeam.com`. Patent filing date: 6 September 2026.

**22. What was not run before publication.** A third-scene held-out test, a second seed per pix2pixHD configuration, a 2023
mean-prior run and hard temporal negatives for the discriminators are listed as open in the reports' audit notes; the principal
chose to publish the results as they stand, and those items remain open.

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-09 | BOSUN | First version. |
| 1.1 | 2026-09-09 | BOSUN | Package audit round 1 applied: AUROC beside every paired count (items 1 and 5), the January 2025 entry reduced to the artefact-only fact (items 11 and 18), the two reproduction scopes stated (items 12 and 13), the pix2pixHD bootstrap described as it is (clones the default branch, records HEAD). |
| 1.2 | 2026-09-09 | BOSUN | Package audit round 2 applied: the saved-score promise limited to the numerical tables and score plots, the contact sheets distinguished (items 12 and 13); the pix2pixHD bootstrap's inputs and checkout order stated (item 13). |
