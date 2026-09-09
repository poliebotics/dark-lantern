---
version: 1.2
date: 2026-09-09
status: the public-layout runbook: what regenerates from the files in this directory, what needs the data-layer bundle, what needs the public recordings and a GPU, and how each script finds its inputs in the published layout
author: BOSUN for Cathal Ryan Hynes
---

# Reproducing the tables and figures, and re-running the work

**Read this first.** Two different things can be reproduced, and the instructions below keep them apart. **Regeneration from
the saved scores** rebuilds every numerical table and every score plot of this package (the AUROC bars, residual histograms,
monitor curves, trajectory and few-shot curves) from the per-row and per-frame scores the desks saved; it needs this directory
and, for the plots and the ARM-I controls, the data-layer bundle; it needs no model and no GPU. The contact sheets are a separate
matter: the ARM-I sheets redraw from the example arrays on the data layer and the statistic's sheet from its previews (section 2),
but the pix2pixHD contact sheets, strips and thumbnails (`pix2pixhd_old_light/kit/contact_sheet.py`) need the per-frame generated
images, which are not published, so the sheets on the data layer are the desk's and regenerate only after retraining (section 3).
**Fresh inference** re-scores the recordings with the models: for ARM-I the fourteen checkpoints are published as documented
derivatives on the data layer and the evaluator runs on a GPU; for the pix2pixHD work the checkpoints are not published, so
fresh inference means retraining from the public recordings with the kit. The statistic needs no model in either sense: a
re-run from the public recordings recomputes every score.

Conventions. `PKG` is this directory. The scripts were run on the rented machines and the development machine with their own
paths; the published copies resolve their inputs relative to the package layout or from the environment variables named
below (`REDACTION.md`, "Files adapted to the published layout"; every change is a path assignment and is in
`REDACTION_LEDGER.tsv`). Python 3.10 or later with numpy; matplotlib and OpenCV for the figures; h5py for the 2024 HDF5
files; PyTorch for anything that touches a checkpoint. Run the regeneration steps on a copy of the package when a script
writes into it (the coupling scripts write `results/` and `figures/` in place).

## 1. From this directory alone (no bundle, no model)

ARM-I tables (`SUMMARY_TABLES.md` and `SUMMARY_TABLES_unified.md` were rendered from these lines; `SUMMARY.json` is rewritten):

```
cd "$PKG"
python3 armi_cross_configuration/kit/summarize.py --results armi_cross_configuration/results
```

pix2pixHD interval summary and tables (`ci_summary.json` is the desk's copy with the four held `results/2024/d2025_*` groups removed,
73 interval groups). The regenerated file carries the same 73 groups with the same point values (`n`, `auroc`, `paired_wins`, the rates,
the means); its interval bounds differ from the desk's for the groups the directory walk visits after the held groups' former position
(34 of the 73 at the staging check, by at most 0.024 on an AUROC or paired-rate bound and 0.026 dB on a PSNR bound), because one seeded
generator serves every group in walk order and the desk's walk included the four held groups:

```
python3 pix2pixhd_old_light/kit/ci_summary.py pix2pixhd_old_light > ci_summary_regen.json
python3 pix2pixhd_old_light/kit/summarise.py pix2pixhd_old_light ci_summary_regen.json
```

The statistic's report text (`write_report.py` reads `results/*.json`, `selection_2023.json`, `verify_2023.json` and
`verify_2024.json` and writes `REPORT.md` in the package directory: run it on a copy):

```
cp -r train_free_coupling_old_sessions /tmp/coupling_copy && python3 /tmp/coupling_copy/code/write_report.py complete
```

## 2. With the data-layer bundle (`LARGE_FILES.md` has the fetch-and-verify sequence)

Place the bundle beside the package, or set the variables below to wherever you put it. `BUNDLE` is the fetched prefix.

ARM-I figures and controls need the per-row score arrays and the loss histories:

```
cp "$BUNDLE"/armi/per_row_scores/*.npz armi_cross_configuration/results/
for a in "$BUNDLE"/armi/checkpoints/*/; do n=$(basename "$a"); mkdir -p armi_cross_configuration/runs/$n; cp "$a"/history.jsonl armi_cross_configuration/runs/$n/; done
python3 armi_cross_configuration/kit/make_figures.py --results armi_cross_configuration/results --arm armi_2026_s20260908 --out figures_regen
python3 armi_cross_configuration/kit/make_figures.py --results armi_cross_configuration/results --arm fewshot --out figures_regen
python3 armi_cross_configuration/kit/perlin_bins.py --results armi_cross_configuration/results --arm armi_2026_s20260908
python3 armi_cross_configuration/kit/motion_split.py --results armi_cross_configuration/results --arm armi_2026_s20260908
```

(`--arm` takes any arm with an `eval.json`; `perlin_bins.py` reads `kit/perlin/` and `motion_split.py` reads
`../../supporting/data_look/` by default; both accept `--params-dir` and `--stats-dir`.)

The statistic's figures need the preview images, and a recomputation of every score from the cached grids needs the cache:

```
COUPLING_PREVIEWS="$BUNDLE/coupling/previews" python3 train_free_coupling_old_sessions/code/make_figures.py 20241219_051150:2024 1680410249:2023 1682718815:2023
COUPLING_CACHE="$BUNDLE/coupling/cache" python3 train_free_coupling_old_sessions/code/stage_b_stats.py 2024 20241219_044052 20241219_044529 20241219_050046 20241219_050648 20241219_051150 20241219_051629 20241219_052040
COUPLING_CACHE="$BUNDLE/coupling/cache" python3 train_free_coupling_old_sessions/code/stage_b_stats.py 2023 1680410249 1680410569 1680412337 1681945334 1682013847 1682014432 1682712156 1682718815
```

(`stage_b_stats.py` rewrites `results/<era>_results.json`, `<era>_scores.csv` and `<era>_partners.json`; the per-session
geometry it reads is `geometry/<session>.geometry.json` in the package; `COUPLING_PKG` overrides the package directory.)

Loading an ARM-I checkpoint (the trainer's classes are in `kit/src/`; the subshell leaves the caller in `PKG`):

```
( cd armi_cross_configuration/kit/src && python3 -c "import torch; ck = torch.load('$BUNDLE/armi/checkpoints/armi_2026_s20260908/latest.pt', map_location='cpu', weights_only=False); print(ck['step'], len(ck['model']), ck['args']['seed'])" )
```

## 3. From the public recordings (a full re-run)

Every recording is on the data layer (`README.md`, primer). The kits fetch and verify them against the archives' own
manifests before anything is computed.

**ARM-I** (one A100-class GPU; about 31 minutes for the four arms of the first run). The steps run in this order: `run_arms.sh`
waits for the download marker and for the last line of the 2026 precache log, and aborts after an hour without them.

```
export XCFG_FS=/path/to/work XCFG_DATA=/path/to/archives XCFG_LEAN=/path/to/cache_lean XCFG_ROOT=/path/to/2026_sessions
mkdir -p "$XCFG_FS/logs"
bash armi_cross_configuration/kit/download.sh "$XCFG_DATA" "$PKG/armi_cross_configuration/kit/downloads.tsv"     # 6,817 files, verified by SHA-256; writes $XCFG_DATA/.verified
python3 armi_cross_configuration/kit/src/precache_xcfg.py --cache-dir "$XCFG_FS/cache" --c-cache-fallback "$XCFG_LEAN" --sessions d2,v10,august --workers 24 > "$XCFG_FS/logs/precache_2026.log" 2>&1   # the 2026 emission images (10,147 rows); the log's last line is the marker run_arms.sh waits for
bash armi_cross_configuration/kit/run_arms.sh                                                            # the old-session precache, the self-test, the four arms, the evaluations
bash armi_cross_configuration/kit/run_warped.sh; bash armi_cross_configuration/kit/run_trajectory.sh     # variant (b), the trajectory
bash armi_cross_configuration/kit/run_followup.sh; bash armi_cross_configuration/kit/run_fewshot.sh; bash armi_cross_configuration/kit/run_controls.sh
```

`XCFG_LEAN` is the root of the 2026 preprocessed-row cache the published zkdiff package's trainer builds (`dark-lantern/proofs/zkdiff_august_20260907/oracle/trainer/precache.py`
over the public d2, v10 and August rows), the directory that contains `96x112/`: the loaders append the size themselves (`kit/src/train_xcfg.py`,
`_cache_path` and the fallback). `XCFG_ROOT` holds the 2026 sessions' emission tiles at `truthbeam/sessions/<s>/derived/Emissions/` and
`august_dev_712/derived/Emissions/` as the trainer expects; the 2026 precache reads them once and writes the `Ei_*.npy` rows into
`$XCFG_FS/cache/96x112/<session>/`, taking each row's `C_*.npy` from `XCFG_LEAN` rather than rewriting it. `run_warped.sh` reads the
homographies from `kit/H/` and `run_controls.sh` the Perlin parameters from `kit/perlin/`, beside `kit/src/` (`XCFG_H` and `XCFG_PERLIN`
override); `download.sh` takes the list and the log by any path and makes them absolute before it changes directory.

**The statistic** (CPU):

```
export HDF5_2024_DIR=/path/to/hdf5   # <session>/data.h5 for the six unanchored sessions and 20241219_050046
export NPY_2023_DIR=/path/to/npy     # old_truth_beams/<session>/{emissions,reports}/ and truth_beam_poliepals_trailer/1682718815/
python3 train_free_coupling_old_sessions/code/select_2023.py         # needs the archives' _control/MANIFEST.jsonl under control/{old_truth_beams,trailer}/ (CONTROL_INPUTS.md)
bash train_free_coupling_old_sessions/code/run_all.sh                # stage A per session, stage B per era, the figures
```

**pix2pixHD** (one A100-class GPU; about six hours for the five evaluated runs). The bootstrap reads the 2023 URL and digest lists
from the kit directory, and they travel in the bundle (`oldlight/kit_inputs/`; the 2024 lists are in the kit), so place them first;
it skips the clone when `$OL_LOCAL/pix2pixHD` exists and patches whatever is checked out there, so clone and check out the desk's
commit before running it:

```
export OL_LOCAL=/path/to/work OL_FS=/path/to/outputs
cp "$BUNDLE"/oldlight/kit_inputs/urls_2023.txt "$BUNDLE"/oldlight/kit_inputs/sha_2023.txt pix2pixhd_old_light/kit/     # on a copy of the package; OL_KIT may name another kit directory
mkdir -p "$OL_LOCAL" && git clone -q https://github.com/NVIDIA/pix2pixHD.git "$OL_LOCAL/pix2pixHD" && git -C "$OL_LOCAL/pix2pixHD" checkout 14b3b3c7fff413086e3b58df52096f16b6891172   # the commit the desk used (the bundle's oldlight/records/logs/pix2pixHD_commit.txt)
bash pix2pixhd_old_light/kit/box_bootstrap.sh                        # downloads and verifies the archives, applies the kit's patches to the checkout, records its HEAD
python3 pix2pixhd_old_light/kit/prep_2024.py --crop 220,660,5020,3360 --size 2048x1152
python3 pix2pixhd_old_light/kit/prep_2023.py --crop 64,248,1856,1368 --size 1792x1120 --rot180
python3 pix2pixhd_old_light/kit/install_meanprior.py
bash pix2pixhd_old_light/kit/train_oldlight.sh ol2024_b4 2024 160 40 --save_epoch_freq 25      # and the other runs as the report's Models section states
bash pix2pixhd_old_light/kit/run_evals.sh ol2024_mean 2024 512x288 0 mean
```

The bootstrap records the HEAD it patched in `$OL_FS/logs/pix2pixHD_commit.txt`; the desk's run cloned the default branch and
recorded that HEAD, which is why the checkout above pins the commit before the patches. The report's
Models section gives every run's recipe and epoch counts; `run_evals.sh <run> <track> <g_size> [gpu] [crop|full|mean]` scores
the tails and the held-out session. Retraining reproduces the recipe, not the weights: GAN training is not bit-reproducible
across machines, so re-evaluated numbers will differ from the published ones, which is why the published numbers stand on
the saved scores under `results/`.

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-09 | BOSUN | First version, after the package audit's readability finding. |
| 1.1 | 2026-09-09 | BOSUN | Package audit round 2 applied: the ARM-I steps run in order (the download list by absolute path, the 2026 precache step and its log marker, `XCFG_LEAN` as the cache root, the homographies and Perlin parameters found beside the kit); the pix2pixHD kit inputs placed from the bundle and the checkout pinned before the bootstrap; the saved-score scope limited to the numerical tables and score plots, the contact sheets distinguished; the interval summary described with its 73 groups. |
| 1.2 | 2026-09-09 | BOSUN | Package audit round 3 applied: the checkpoint-loading command runs in a subshell, so the caller stays in `PKG` for the blocks that follow. |
