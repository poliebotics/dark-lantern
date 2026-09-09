---
version: 1.2
date: 2026-09-09
status: what the data-layer bundle carries, directory by directory, and which ledger covers what; the object counts and byte totals of the payload directories are rendered from the staged bundle
author: Cathal Ryan Hynes (author of record); drafted with BOSUN, the project's automated research assistant
---

# The data-layer bundle

The large objects of this publication are served from the data layer (bucket `truthbeam`, prefix
`results/old_light_20260909/v1/`, `https://data.truthbeam.com/results/old_light_20260909/v1/`) because of their size or
their number: the checkpoints, the per-row score arrays, the pix2pixHD run records with every contact sheet, strip and
thumbnail, the cached grids of the statistic, the data-look atlas. Nothing a reader needs to check a number in
`RESULTS.md` is there: every results file the numbers were copied from is in this directory. The bundle carries copies of
this package's front matter under `repository_package_front_matter/` for convenience.

## Directories

| directory | objects | bytes | what |
|---|---:|---:|---|
| `armi/checkpoints/` | 67 | 191,937,233 | the fourteen ARM-I and ARM-C checkpoints (`latest.pt`, documented derivatives) with each run's training log, evaluation logs and loss history |
| `armi/evidence/` | 1 | 1,914,836 | the cropped copy of the public d2 preview frame 1300 (`PINS.json` `evidence`) |
| `armi/logs/` | 29 | 69,034 | the run logs of the two rented machines (precache, arms, aligned variant, trajectory, controls, follow-up, adaptation, channel-order diagnostic, download and verification) |
| `armi/per_row_scores/` | 220 | 33,662,404 | every per-row score array the ARM-I evaluations wrote, the aligned-variant, control, trajectory and adaptation arrays included, and the example arrays the contact sheets were drawn from |
| `coupling/cache/` | 22 | 269,507,332 | the statistic desk's cached grids per session (`<session>.npz`; `<session>.export75.npz` for the exporter-geometry variant), from which every score reproduces with the partner maps in `train_free_coupling_old_sessions/results/` |
| `coupling/previews/` | 165 | 44,682,520 | per-session previews of the projected-region detection (recording with the fitted quad, temporal standard-deviation map, warped crop, emission at the chosen orientation) and the geometry-development overlays |
| `oldlight/ci_summary.json` | 1 | 53,826 | a copy of the interval summary the pix2pixHD tables were rendered from |
| `oldlight/kit_inputs/` | 4 | 6,140,197 | the 2023 URL list, digest list and manifest copies against which the pix2pixHD kit verified its downloads |
| `oldlight/records/` | 349 | 317,840,443 | the pix2pixHD run records as pulled from the rented machine: every metrics, verifier, coupling and partner-map JSON, every contact sheet, top-half sheet and strip, the interim epoch-25 sheets, the mean training capture handed to the mean-prior model, the thumbnails, the split records, the pix2pixHD options, loss logs and epoch markers, and the training, evaluation, preparation and bootstrap logs |
| `supporting/data_look/` | 2 | 2,746,322 | the alignment atlas and the by-era overlay of the data-look desk |
| `repository_package_front_matter/` | 13 | | byte-identical copies of this package's front matter and ledgers (`README.md`, `RESULTS.md`, `CLAIM_BOUNDARY.md`, `AUDIT_TRAIL.md`, `HASHES.md`, `FAQ.md`, `LARGE_FILES.md`, `PINS.json`, `SHA256SUMS`, `MODES`, `LICENSE`, `REDACTION.md`, `REDACTION_LEDGER.tsv`), covered by this package's `SHA256SUMS` |
| `README.md`, `SHA256SUMS`, `_control/` | 5 | | the bundle's own README, the root copy of the control ledger, and the three controls |

The payload directories above hold 860 objects and 868,554,147 bytes; the complete object count and byte total, the front-matter copies included, are in the bundle's `_control/RELEASE.json` and in the root `README.md` paragraph.

## Which ledger covers what

This directory's `SHA256SUMS` covers every file in this directory and nothing outside it. The objects under the bundle's
`repository_package_front_matter/` are byte-identical copies of files in this directory and are covered by `SHA256SUMS`
at their package paths. Every other object of the bundle, and the bundle's own `README.md`, is covered only by the bundle's
`_control/MANIFEST.jsonl` (one JSON line per object: relative path, size, SHA-256, object key, content type) and its
`sha256sum -c` form `_control/SHA256SUMS` (a copy sits at the bundle root). The SHA-256 digests of the manifest, of
`_control/SHA256SUMS` and of `_control/RELEASE.json`, the object count and the byte total are frozen before upload and
published in the Dark Lantern repository's root `README.md`, in the provenance paragraph for this package; check a downloaded
manifest against that digest before trusting it. `PINS.json` in this directory carries the published digest of every
checkpoint derivative and of the evidence crop, so those objects are also pinned from here.

## Fetching and verifying the bundle

The digests of the three controls, the object count and the byte total are published in the Dark Lantern root `README.md`, in
the provenance paragraph for this package; compare them before trusting anything else. `PKG` is this directory.

```
P=https://data.truthbeam.com/results/old_light_20260909/v1
mkdir -p bundle && cd bundle
for f in _control/MANIFEST.jsonl _control/SHA256SUMS _control/RELEASE.json README.md SHA256SUMS; do curl -fsSL --create-dirs -o "$f" "$P/$f"; done
sha256sum _control/MANIFEST.jsonl _control/SHA256SUMS _control/RELEASE.json    # must equal the three digests in the root README paragraph
cmp SHA256SUMS _control/SHA256SUMS && echo ROOT_COPY_OK
python3 - <<'PY'
import json, subprocess
rows = [json.loads(l) for l in open("_control/MANIFEST.jsonl")]
print(len(rows), "objects,", sum(r["size"] for r in rows), "bytes")          # must equal the count and total in the root README paragraph
for r in rows:
    subprocess.run(["curl", "-fsSL", "--create-dirs", "-o", r["relative_path"], "https://data.truthbeam.com/" + r["object_key"]], check=True)
PY
sha256sum -c --quiet _control/SHA256SUMS && echo BUNDLE_OK                      # every object, by SHA-256
cmp repository_package_front_matter/SHA256SUMS "$PKG/SHA256SUMS" && echo PACKAGE_MATCH   # the bundle belongs to this package
```

Placement for regeneration (`REPRODUCE.md`, section 2): the per-row score arrays go beside the evaluation JSON
(`cp bundle/armi/per_row_scores/*.npz "$PKG/armi_cross_configuration/results/"`), each run's `history.jsonl` under
`"$PKG/armi_cross_configuration/runs/<arm>/"`, and the statistic's previews and cached grids are named to the scripts by
`COUPLING_PREVIEWS` and `COUPLING_CACHE`. Everything else in the bundle is read where it lies.

## The checkpoints

`armi/checkpoints/<arm>/latest.pt` are documented derivatives of the as-trained files: the machine-path strings in the
recorded training arguments (`args.out`, `args.ckpt`, `args.cache_dir`, `args.old_root`, `args.c_cache_fallback` and, for
the adaptations, `args.init_from`) are replaced by the placeholders of `REDACTION.md`; every model tensor, the optimiser
state, the RNG states, the step, the sampler and every other argument were verified equal to the as-trained file before the
derivative was written (`REDACTION_LEDGER.tsv`, `PINS.json` `checkpoints`). The evaluation JSON's `checkpoint_sha256` names
the as-trained digest; `PINS.json` pairs it with the published one. Loading them needs the trainer's model classes
(`armi_cross_configuration/kit/src/train_xcfg.py`, `phase_g/`) and PyTorch with `weights_only=False`, since the checkpoint
carries the RNG states and the argument record beside the tensors.

## What the images show

The contact sheets, strips and thumbnails under `oldlight/records/`, the previews under `coupling/previews/`, the evidence
crop under `armi/evidence/` and the atlas under `supporting/data_look/` depict a masked participant in a recognisable indoor
setting (the bookshelf room; the evidence crop, CittaDel's wheelhouse). The participant wears a full face covering; no
unobscured face appears. These materials are not anonymised; identity may be inferred from clothing, movement or context.

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-09 | BOSUN | First version; the directory table is rendered by the staging script from the bundle. |
| 1.1 | 2026-09-09 | BOSUN | Package audit round 1 applied: the copyable fetch, verification and placement sequence. |
| 1.2 | 2026-09-09 | BOSUN | authorship line, 9 September 2026. |
