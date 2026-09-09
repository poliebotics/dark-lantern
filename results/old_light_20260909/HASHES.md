---
version: 1.1
date: 2026-09-09
status: what every published digest is a digest of, and where to recompute it
author: BOSUN for Cathal Ryan Hynes
---

# What every hash is a hash of

All digests in this package are SHA-256 over whole files unless a line says otherwise. Values abbreviated in prose are
complete in `PINS.json` and in the ledgers.

## The ledgers

| hash | of | recompute |
|---|---|---|
| `SHA256SUMS` (the package ledger) | every other file in this directory, in `sha256sum` form, LC_ALL=C order; the ledger's own SHA-256 is what the Dark Lantern root `README.md` pins for this package | `sha256sum -c SHA256SUMS`; `sha256sum SHA256SUMS` |
| `MODES` | the list of executable files (the shell scripts); every other file is mode 0644; listed in `SHA256SUMS` | `find -perm /111` against the list |
| the bundle's `_control/MANIFEST.jsonl`, `_control/SHA256SUMS`, `_control/RELEASE.json` | every object the data-layer prefix `results/old_light_20260909/v1/` serves except the controls themselves: relative path, size, SHA-256, object key and content type per line; the `sha256sum -c` form; the release record. Their own digests are fixed in the Dark Lantern root `README.md` by the commit that adds this package | fetch and `sha256sum`; compare with the root `README.md` |
| `armi_cross_configuration/KIT_SHA256SUMS_as_run.txt`, `pix2pixhd_old_light/KIT_SHA256SUMS_as_run.txt` | the desks' own digest lists over the kit and record files **as run** (private bytes, machine paths included); the published kit files differ from them where `REDACTION_LEDGER.tsv` records a substitution, so these lists do not validate the published bytes; `SHA256SUMS` does | for the record; `REDACTION_LEDGER.tsv` pairs each as-run digest with its published digest |
| `REDACTION_LEDGER.tsv` | every published file whose bytes differ from the desk's original, with the private and the published digest and the reason | `sha256sum` on the published file; the private digest is checkable only by a holder of the originals |

## The results

| hash | of | recompute |
|---|---|---|
| `PINS.json` `results.armi[]`, `results.coupling[]`, `results.oldlight[]` | the published results files (evaluation JSON, controls, motion split, Perlin bins, summary tables; the statistic's results JSON, score CSVs, partner maps, geometry files, refinement and exporter checks; the pix2pixHD metrics, verifier, coupling and partner-map JSON and `ci_summary.json`); redacted copies where a path string was replaced (`REDACTION_LEDGER.tsv`), otherwise byte-identical to the desks' files | `sha256sum`; a redacted copy's private digest is in the ledger |
| `checkpoint_sha256` in every `armi_cross_configuration/results/<arm>*.eval.json`, and the truncated digests in `SUMMARY_TABLES.md` | the **as-trained** ARM-I and ARM-C checkpoints (`latest.pt`) on the rented machine, the files the evaluator scored | `PINS.json` `checkpoints[].as_trained_sha256`; the as-trained bytes are not published |
| `PINS.json` `checkpoints[].published_sha256` | the published checkpoint derivatives on the data layer (`armi/checkpoints/<arm>/latest.pt`): the as-trained file with the machine-path strings in its recorded training arguments replaced, every model tensor, the optimiser state, the RNG states, the step, the sampler and every other argument verified equal (`REDACTION.md`) | `sha256sum` after fetching |
| `PINS.json` `figures[]` | every PNG under the three `figures/` directories and the two contact-sheet halves | `sha256sum`; the plots regenerate with the kits' figure scripts from the results files, the ARM-I and statistic contact sheets from the bundle's example arrays and previews; the two pix2pixHD sheet halves need the per-frame generated images, which are not published (`REPRODUCE.md`) |
| `PINS.json` `audits[]` | the published audit copies (`audits/astra/*.md`) | `sha256sum` |

## The data

| hash | of | recompute |
|---|---|---|
| the archives' `_control/MANIFEST.jsonl` and `_control/SHA256SUMS` at `https://data.truthbeam.com/archive/2023/old_truth_beams/v1/`, `.../archive/2023/truth_beam_poliepals_trailer/v1/`, `.../archive/2024/truth_beam_20241219_unanchored/v1/` | every 2023 NumPy file and every 2024 HDF5 file the desks used; the desks verified every downloaded byte against them (`train_free_coupling_old_sessions/verify_2023.json`, `verify_2024.json`; the ARM-I `kit/downloads.tsv` carries the 6,817 URLs with their manifest digests; the pix2pixHD `kit/sha_2024.txt` and the bundle's `oldlight/kit_inputs/sha_2023.txt` the same) | fetch and `sha256sum -c`; `train_free_coupling_old_sessions/CONTROL_INPUTS.md` lists the control files' own digests |
| `f4792a200cffcb70471a03c6ee6212737cefd4b71630ed5e72f654f445b8496a` | `pinata/20241219_050046_TB.h5`, the anchored December 2024 session (5,096,765,440 bytes), the payload hash its `RELEASE.json` records | `sha256sum` after fetching |
| `32dd9572c96275ab15601cfbb3d135722b13e60a627b02f119514a96f87d648b` | `sessions/d2/derived/Recordings_previews/frame_001300.png`, the public d2 camera preview the owner correction of 9 September was verified against (`AUDIT_TRAIL.md`); a cropped copy is on the data layer under `armi/evidence/` (`PINS.json` `evidence`) | `sha256sum` after fetching |
| `hashes` datasets and `attrs` in the 2024 HDF5 files, quoted in `pix2pixhd_old_light/records/SPLIT_2024.json` (`initial_blockhash`, `final_hash`) | the recorder's BLAKE3 chain over the recordings (`h[i] = blake3(h[i-1] || recordings[i])`), as the archive's `HDF5_VALIDATION.json` describes | h5py and blake3 over the fetched file |
| the file-name digests of the 2023 archives (`emissions/{index}_{hash}.npy`, `reports/{index}_{hash}.npy`) | the recorder's BLAKE3 of each array's bytes, cross-checked against the chain log by the ARM-I loader and the data-look desk | blake3 over the fetched file |

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-09 | BOSUN | First version. |
| 1.1 | 2026-09-09 | BOSUN | Package audit round 2 applied: the figures row says which PNGs regenerate from the results files and which need the bundle or the withheld generated images. |
