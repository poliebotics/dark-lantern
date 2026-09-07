---
version: 1.2
date: 2026-09-06
status: public results package; retrospective, previously inspected frames; registered controls frozen before scoring
author: BOSUN for Cathal Ryan Hynes
---

# No Training Required: emission-capture grid correlation on the held-out tails of two Truth Beam sessions, reproduced from public frames with registered controls

On the 975 previously inspected tail frames from sessions d2 and v10, all five evaluated train-free grid-correlation
statistics scored matched emission–capture pairs above their recorded same-session random mismatches in aggregate; their
observed pooled AUROCs ranged from 0.683 to 0.756.

That sentence restates the result recorded on 6 September 2026 on a rented box (`box_record/coupling_stat.json`). This package
reproduces it from the public frames and adds two controls that were registered before any new score was produced. It is a
retrospective analysis of frames that had already been inspected in the earlier work; it is not a preregistered experiment, it
creates no fresh holdout, and it trains nothing.

## The statistic

For a pair (emission E, capture B) at 2048x1152, each image is reduced to a g x g grid of per-cell mean colours, standardised per
channel (mean removed, divided by the standard deviation plus 1e-6), and the statistic is the mean over the three channels of the
Pearson correlation between the two grids (`scripts/coupling_stat.py`, which preserves the box statistic implementation; the as-run script's SHA-256 is in `results/REGISTRATION.json`).
Grids 4, 8, 16, 32 and 64 are all reported. This is conventional image processing; the point is what it measures on these frames,
not the method.

## The frames

The contiguous final ten percent of each public session (`https://data.truthbeam.com/sessions/<s>/`), d2 frames 5392 to 5991 (600)
and v10 frames 3368 to 3742 (375), fetched from the gateway and rebuilt into pairs with the recorded rule (emission 1920x1080 to
2048x1152 bicubic; camera preview 5320x4600 cropped to rows 350 to 3342 and resampled to 2048x1152 with Lanczos). `PAIRS_MANIFEST.json`
records the SHA-256 of every fetched file, every pair file and every decoded pixel array (975 pairs; Pillow 12.1.1, numpy 2.3.5).

## Reproduction

Running the unchanged box script on the rebuilt pairs reproduced every recorded metric within 1e-06 and every strict-win
count exactly: 15 of 15 comparisons (`results/REPRODUCTION.json`, `results/coupling_stat_repro.json`).

## Registered control 1: repeated random mismatch

Five independent within-session derangements (numpy PCG64, seeds 2026090601, 2026090602, 2026090603, 2026090604, 2026090605; permutations
with a fixed point rejected), persisted before scoring (`results/maps/random_seed*.json`) and used unchanged for every grid. Per
session, grid and seed: AUROC with ties counted one half, and paired ordering (wins plus half the ties over the comparisons).
Registered pass rule: both metrics at least 0.60 in all 50 combinations. **Result: PASS, 0 failures of 50.**
Over the five seeds, AUROC ranged 0.671 to 0.767 and paired ordering 0.792 to 0.955.

| grid | session | pairs | AUROC over five seeds | paired ordering over five seeds |
|---|---|---:|---|---|
| 4x4 | d2 | 600 | 0.679 to 0.689 | 0.912 to 0.937 |
| 4x4 | v10 | 375 | 0.671 to 0.684 | 0.888 to 0.901 |
| 8x8 | d2 | 600 | 0.760 to 0.767 | 0.940 to 0.955 |
| 8x8 | v10 | 375 | 0.734 to 0.748 | 0.928 to 0.944 |
| 16x16 | d2 | 600 | 0.723 to 0.729 | 0.858 to 0.893 |
| 16x16 | v10 | 375 | 0.702 to 0.726 | 0.843 to 0.904 |
| 32x32 | d2 | 600 | 0.694 to 0.711 | 0.803 to 0.832 |
| 32x32 | v10 | 375 | 0.692 to 0.717 | 0.824 to 0.853 |
| 64x64 | d2 | 600 | 0.685 to 0.703 | 0.792 to 0.817 |
| 64x64 | v10 | 375 | 0.687 to 0.713 | 0.821 to 0.840 |

## Registered control 2: hard negatives (separately registered)

Four partner families chosen from emissions only, same session, self excluded, lexicographic tie-break: the previous frame, the next
frame (no wrap; 599 and 374 comparisons), the nearest other emission by mean-RGB distance, and the nearest other emission by
standardised 32x32 pattern similarity (975 comparisons; not necessarily derangements). Registered pass rule: both metrics at least
0.60 for every grid, session and family. **Result: PASS, 0 failures of 40.** AUROC ranged 0.633 to 0.769 and paired
ordering 0.757 to 0.995 (the weakest family is the pattern-similar emission, as expected).

| family | session | comparisons | AUROC over the five grids | paired ordering over the five grids |
|---|---|---:|---|---|
| previous frame | d2 | 599 | 0.689 to 0.765 | 0.838 to 0.990 |
| previous frame | v10 | 374 | 0.666 to 0.723 | 0.880 to 0.989 |
| next frame | d2 | 599 | 0.687 to 0.769 | 0.853 to 0.988 |
| next frame | v10 | 374 | 0.667 to 0.722 | 0.869 to 0.995 |
| nearest other emission by mean-RGB distance | d2 | 600 | 0.687 to 0.767 | 0.807 to 0.955 |
| nearest other emission by mean-RGB distance | v10 | 375 | 0.682 to 0.736 | 0.819 to 0.909 |
| nearest other emission by 32x32 pattern similarity | d2 | 600 | 0.661 to 0.727 | 0.757 to 0.912 |
| nearest other emission by 32x32 pattern similarity | v10 | 375 | 0.633 to 0.684 | 0.763 to 0.877 |

Every target and partner identity, both scores, their difference, and the win and tie flags are in `results/scores/` (one file per
map, grid and session); contiguous 30-frame and 60-frame block summaries, shorter terminal blocks retained, are in
`results/N7_RAW_v1_results.json` under `blocks`. Of the 1,485 thirty-frame blocks, 27 have AUROC below 0.60 (minimum 0.546); of
the 765 sixty-frame blocks, 5 do (minimum 0.565); no block's paired ordering falls below 0.60. These are descriptive variation within
the registered session-level floors, and they bound how broadly the word robust may be read.

## What this does and does not show

It shows framewise emission–capture correspondence in the held-out tails of two sessions the earlier models were trained on, measured
by a fixed statistic that learned nothing, and it holds in aggregate under the five recorded random maps and the four hard-negative
families (robustness means exactly that observed aggregate behaviour and no more). The 8x8 grid has the highest AUROC, but it was
selected after comparing five grids on these same tails, so it is not a validated optimum. This package does not clear the existing
learned-model package; the mismatch orientation throughout is corr(E_target, B_partner), with partners selected from emissions only,
so the hard families compare a target's emission against captures associated with nearby or similar emissions; they are not a
capture-anchored emission-substitution experiment. Nothing
here establishes generalisation to unseen sessions, liveness, resistance to an adversary who chooses the emission or capture,
or current-emission specificity of any generative model. Serial frames are dependent, so no confidence interval treating frames
as independent is given; the block summaries show the variation instead. The floors are engineering effect-size floors on
inspected data, not significance tests or security thresholds.

## Protocol details and deviations, stated exactly

Random maps: for each seed and session, a fresh PCG64 generator is initialised with that seed, the sorted session names are
permuted, and complete permutations are rejected until none contains a fixed point (the sessions do not use independently seeded
streams). Hard families: the mean-RGB feature is the float32 mean over the prepared 2048x1152 pixels with float64 Euclidean
distances between means; under exact integer sums 14 of the 975 nearest choices would differ (ten d2, four v10), and the recorded
maps are kept as scored rather than adjusted after inspection; the pattern feature is the frozen 32x32 cell construction with
per-channel standardisation, flattened and standardised again, compared by dot product divided by 3072; ties did not occur, the
lexicographic rule is in the code. Chronology (UTC, 6 September 2026): registration written 18:12:21, the reproduction run
scored 18:12:51, the nine maps persisted 18:13:30, endpoint score files written through 18:13:35: every map preceded the endpoint
scoring, but the reproduction scoring preceded the maps, so the common text's rule that complete maps be frozen before any new
score was met for the endpoints and not literally for the reproduction. `results/REGISTRATION.json` pinned the statistic source, the
box record, the pairs manifest, the grids, the seeds and the floor; it did not hash-bind the extension source, the full
registration text, the hard-feature arithmetic or the complete environment, so the as-run hashes in `SCRIPTS_AS_RUN.json` and the
local timestamps are the provenance for those, written after the fact and dated as such. The runner has no attempt isolation (a
rerun would write the same paths) and a nonfinite value stops the run without persisting the current file's partial rows; neither
condition arose. The script header's phrase applied verbatim is therefore too strong; the registration was applied as described
here.

## Contents and verification

`scripts/fetch_heldout2.sh` fetches the frames; `scripts/n7_prep_pairs.py` rebuilds the pairs and writes `PAIRS_MANIFEST.json`;
`scripts/n7_extension.py` freezes `results/REGISTRATION.json`, runs the box script for the reproduction, persists the maps, scores
every map at every grid and writes `results/N7_RAW_v1_results.json`. `scripts/n7_package.py` assembled this package and generated
this README from those files. The shipped scripts and the two results records have the workspace's absolute paths reduced to
package-relative form (the box script's two default paths included), so their hashes differ from the files as run;
`SCRIPTS_AS_RUN.json` records the as-run hashes and `SHA256SUMS` the shipped bytes. The shipped `n7_package.py` is historical
source that expects the working-directory layout. `SHA256SUMS` covers every other package file.

## Log

- 1.2 (2026-09-06, BOSUN) — title given its paper form; no other change.
- 1.1 (2026-09-06, BOSUN) — after Astra's audit (HOLD on wording, provenance and packaging): protocol details and deviations
  stated, block-level variation reported, claims bounded, learned-package hold retained, shipped paths reduced with the as-run hashes
  distinguished.
- 1.0 (2026-09-06, BOSUN) — built from GPT-6 Astra's N7-RAW-v1 registration of the same day; reproduction and both
  registered endpoints passed on the first and only run.
