---
version: 1.2
date: 2026-09-09
status: results package; three positive results of 9 September 2026 on the April 2023 and December 2024 Truth Beam recordings, each with a second-model results audit applied; package audit rounds 1 and 2 applied
author: BOSUN for Cathal Ryan Hynes
---

# The Light of Other Days: emission-recording correspondence in the April 2023 and December 2024 Truth Beam recordings, measured by a train-free grid statistic, by pix2pixHD models trained on them, and by an image-conditioned diffusion evaluator trained on the 2026 recordings

Three results from one night's work, 9 September 2026, on the oldest public Truth Beam recordings: eight April 2023
sessions (a 3-megapixel camera looking down at a bookshelf, the projected pattern upside down in the camera) and seven
December 2024 sessions (a 24.5-megapixel camera looking at the same bookshelf frontally). Each asks the same question in a
different way: does a camera frame carry a measurable trace of the pattern that was projected when it was taken, so that
the true pattern can be told from a wrong one?

1. **A fixed calculation, no model.** With the projected region aligned, the train-free grid-correlation statistic of
   *No Training Required* (6 September 2026, `dark-lantern/results/train_free_coupling_20260906/`) preferred the correct
   recording to one random same-session alternative in all 1,032 tested comparisons across the 15 sessions (584 of 584
   April 2023 pairs at grid 8, pooled AUROC 0.9999; 448 of 448 December 2024 pairs at grid 16, pooled AUROC 0.9988).
   Aligning the lit area is part of the finding: on the whole camera frame the same statistic gives 0.740 (April) and
   0.561 (December) at grid 16. `train_free_coupling_old_sessions/`.
2. **pix2pixHD models trained on the old recordings, evaluated on a session they never trained on.** Given the average
   training scene as a prior, a pix2pixHD trained on six December 2024 sessions favoured the correct light pattern in all
   64 two-choice comparisons from the seventh session (generator colour-residual paired wins 64 of 64, pooled AUROC 0.962;
   its own discriminator 0.934 and 0.944 against capture and emission swaps). On the April 2023 trailer session, which no
   model trained on, the colour-grid check favoured the true pairing in 776 of 777 comparisons (grid 16, AUROC 0.951), and
   the crop-recipe model's discriminator ranked the true pair above a swap on 775 and 777 of 777. These results are
   labelled exploratory: the held-out scores were read during the night and steered the recipe changes.
   `pix2pixhd_old_light/`.
3. **ARM-I, the image-conditioned sibling of the published ARM-C diffusion evaluator, trained on the 2026 recordings and
   tested with no fine-tuning on the old rigs.** It preferred the correct pattern over the average prescribed wrong
   patterns on 447 of 448 December 2024 frames (paired fraction 0.998, pooled AUROC 0.657; a second seed 440 of 448 and
   0.639), and the reverse arm, trained on six 2024 sessions, transferred to the 2026 sessions at AUROC 0.821 and 0.766.
   Raw 2023 inputs did not transfer; with the recordings aligned into the emission frame the 2026-trained model preferred
   the true 2023 emission on 91 percent of 3,359 frames (AUROC 0.543), and one evaluator trained across all three rig
   configurations reached AUROC 1.000 on the held-out aligned 2023 trailer and 0.788 / 0.726 on the held-out 2024 session,
   with the correct pattern preferred on every frame. Controls with random, exhaustive, matched-period and colour-matched
   negatives leave the 2024 result where it stands. `armi_cross_configuration/`.

Every one of these is an **emission-recording correspondence** result inside these recordings, and nothing more:
`CLAIM_BOUNDARY.md` says exactly what is and is not claimed. No result here is proved in zero knowledge; the published
ZeeBeam (the Zero-knowledge Evidence Emitter Beam) and zkdiff proofs bind the specified ARM-C execution and say nothing about ARM-I, the pix2pixHD models or the
statistic.

**Two parts.** This publication is the repository package you are reading and a data-layer bundle at
`https://data.truthbeam.com/results/old_light_20260909/v1/` (bucket `truthbeam`): the thirteen ARM-I checkpoints and the one ARM-C control with
their training logs, every per-row score array, the pix2pixHD run records with every contact sheet, strip and thumbnail,
the cached grids of the coupling statistic, the data-look alignment atlas, and copies of this package's front matter
(`LARGE_FILES.md`). The bundle's controls are `_control/MANIFEST.jsonl`, `_control/SHA256SUMS` and `_control/RELEASE.json`;
their digests are fixed in the Dark Lantern repository's root `README.md` by the commit that adds this package (this
file cannot carry them, being itself copied into the bundle). Every number in this package traces to a results file in
this directory; the plots were produced from those files by the scripts in the `kit/` directories, the contact sheets by the same
kits from the example arrays, previews and generated images they name (`REPRODUCE.md` says which of them regenerate).

## Primer, for a reader with no context

**The instrument.** A Truth Beam recording is made by a projector that lights a scene with a pattern computed from a
hash chain, and a camera that photographs the lit scene. One photograph with the pattern that was showing is a **pair**
(emission E, recording B, also called the capture). Three generations of the instrument appear here. April 2023: a
Daheng Galaxy camera at 2,048 x 1,536, a smooth 16 x 16 spectral blob pattern shown at 1,920 x 1,200, the camera mounted
so the pattern appears rotated by a half turn, eight sessions of 10 to 777 pairs (3,399 pairs in all; the last, the
"trailer" session `1682718815`, was also the source of a public film). December 2024: a 24.5-megapixel camera at 5,320 x
4,600, a Perlin-noise pattern at 1,920 x 1,080, upright, seven sessions of 64 pairs each (448 pairs), six recorded with
a local hash chain only and one, `20241219_050046`, anchored on chain. 2026: the ZeeBeam sessions d2, v10 and the
August development session, recorded on the programme's current rig with the same sensor size as 2024 and a pattern
family driven by an extendable-output hash; these trained ARM-I and are the recordings the published proofs concern. The
2023 and 2024 sessions were recorded in the same room in front of the same bookshelf; the 2026 sessions in a different
room (aboard CittaDel, the principal's vessel, in her wheelhouse), so a transfer between 2024 and 2026 crosses scene, camera, resolution and
pattern family at once, while 2023 to 2024 shares the room. All the data are public at `https://data.truthbeam.com`
(`archive/2023/old_truth_beams/v1/`, `archive/2023/truth_beam_poliepals_trailer/v1/`,
`archive/2024/truth_beam_20241219_unanchored/v1/`, `pinata/20241219_050046_TB.h5`, `sessions/d2/`, `sessions/v10/`), and
every file used was verified by SHA-256 against the archives' own manifests before use.

**What is measured.** A two-choice test: given a recording, is the statistic (or the model) better matched to the pattern
that was actually showing than to a wrong pattern from the same session? Two numbers report it and always travel
together. The **paired fraction** (or paired wins) is the share of frames on which the true pairing scored better than its
alternative; the **pooled AUROC** pools every matched and every mismatched score and asks how well a single threshold would
separate them (0.5 is chance, 1.0 is perfect separation). For the statistic and the pix2pixHD tests the alternative is one
wrong partner per frame; for ARM-I each frame's correct-emission error is compared with the average of its prescribed
wrong-emission errors (the frozen ARM-C protocol's five offsets), a different and easier question than identifying the true
pattern among all candidates, which the exhaustive control in the ARM-I report addresses separately. A model can prefer the true pattern on every frame while its
pooled AUROC stays modest, because frames differ from one another more than the margin between true and wrong; ARM-I on the
2024 rig is exactly that case (paired 0.998, AUROC 0.657), and the two numbers are never quoted apart.

**The three methods.** The **train-free grid statistic** reduces emission and recording to a g x g grid of mean colours,
standardises each and correlates them; it learns nothing. The **pix2pixHD** models are conditional GANs that render a
recording from an emission; their generators are tested by asking whether the recording generated from the true emission
is closer to the real one than the recording generated from another frame's emission, and their discriminators by asking
whether they rank the true pair above a swapped one. **ARM-I** is the published ARM-C conditional-diffusion evaluator
(`dark-lantern/proofs/zkdiff_august_20260907/`) with its twelve hash-derived conditioning channels replaced by the
rendered emission image, so that it can be conditioned on recordings whose patterns came from other generators; its
statistic is the frozen ARM-C protocol unchanged (timestep 150, the residual under the true emission against the residual
under wrong emissions at the published offsets).

**Who did what.** "The principal" is Cathal Ryan Hynes (PolieBotics), who set the questions and takes every publication
step. "BOSUN" is the project's automated research assistant, a Claude-family language model, which ran the night's work
in several concurrent sessions that the reports call **desks** (the ARM-I desk on a rented GPU, the CPU statistics desk,
the pix2pixHD training desk on another rented GPU, the data-look desk that measured the alignments, a desk that checked
an older discriminator, and the release desk that built this package); "the coordinator" in the reports is BOSUN's
coordinating session. "Astra" is the second model (GPT-6) that audited each result's report before publication; its
briefs and verdicts are in `audits/`, its verdict lines in `AUDIT_TRAIL.md`. These are model reviews, not independent
validation. Every rented machine was terminated after its run.

## What is here

| path | what |
|---|---|
| `RESULTS.md` | the three results in shelf form, the plain-English paragraphs, the headline tables, and where each number comes from |
| `REPRODUCE.md` | the public-layout runbook: what regenerates from this directory alone, what needs the bundle, what needs the recordings and a GPU; regeneration from the saved scores kept apart from fresh inference |
| `CLAIM_BOUNDARY.md` | what is claimed (emission-recording correspondence within these recordings) and what is not (realness, liveness, capture, forgery detection, zero-knowledge proof, scene transfer) |
| `AUDIT_TRAIL.md` | the four second-model results audits (two rounds on ARM-I, one each on the statistic and the pix2pixHD work) with their verdict lines, what changed after each, and the owner correction of 9 September |
| `HASHES.md` | what every published digest is a digest of, and where to recompute it |
| `FAQ.md` | the questions a reader is likely to ask, answered from the files |
| `LARGE_FILES.md` | what the data-layer bundle carries, directory by directory, and which ledger covers what |
| `PINS.json` | the digests a reader pins: the results files, the figures, the as-trained and published checkpoints, the as-run kit manifests, the public objects cited |
| `REDACTION.md`, `REDACTION_LEDGER.tsv` | the redaction rule applied to every copied text record, every changed file with both digests, and what is held |
| `LICENSE` | the Dark Lantern Research and Private Use Licence 1.2, byte-identical to the repository's root `LICENSE` |
| `armi_cross_configuration/` | ARM-I: the desk report (`REPORT.md`), the summary tables, the evaluation JSON of every arm, variant, checkpoint step, control and adaptation (`results/`), the figures, the kit that ran on the rented machines (`kit/`: trainer copy, evaluator, precache, controls, run scripts, the per-session homographies and Perlin parameters), and the as-run kit digests |
| `train_free_coupling_old_sessions/` | the statistic: the desk report, the results JSON, per-frame scores and partner maps (`results/`), the per-session geometry (`geometry/`), the figures, the code as run (`code/`), the 2023 selection and the two verification records |
| `pix2pixhd_old_light/` | pix2pixHD: the desk report, the interval summary (`ci_summary.json`), every metrics, verifier, coupling and partner-map JSON (`results/`), the top halves of the two shelf contact sheets, the training records (`records/`: split records, options, loss logs), and the kit (`kit/`) |
| `supporting/data_look/` | the data-look desk's alignment table and per-session statistics (geometry, photometry, drift) for the fifteen old sessions, from which the homographies and the motion covariate came |
| `audits/` | the second-model briefs and verdicts, published with paths trimmed and private instructions redacted (`audits/README.md`) |
| `SHA256SUMS`, `MODES` | the digest of every other file in this directory (check it first); the files that are executable (every other file is mode 0644) |

## Verify it

```
sha256sum -c --quiet SHA256SUMS && echo LEDGER_OK
```

Then read `RESULTS.md` with the results files open: every number there names the JSON from which it was copied. The kits
regenerate the tables and figures from those files (`armi_cross_configuration/kit/summarize.py`,
`armi_cross_configuration/kit/make_figures.py`, `train_free_coupling_old_sessions/code/write_report.py` and
`make_figures.py`, `pix2pixhd_old_light/kit/ci_summary.py`); the training and evaluation scripts are the ones that ran,
with their machine paths replaced as `REDACTION.md` states; `REPRODUCE.md` is the runbook for the published layout and says
which steps regenerate the tables and figures from the saved scores and which need a model. The recordings themselves are on
the public data layer at the prefixes named in the primer.

## What the pictures show

The contact sheets, strips and thumbnails in the bundle, the figures here that carry camera frames
(`armi_cross_configuration/figures/contact_sheet_*.png`, `train_free_coupling_old_sessions/figures/contact_sheet_crops.png`,
`pix2pixhd_old_light/results/*/sheet_top_half.png`) and the data-look atlas depict a masked participant in a recognisable
indoor setting (the bookshelf room; for the 2026 rows of the ARM-I sheets, CittaDel's wheelhouse). The participant wears a
full face covering; no unobscured face appears. These materials are not anonymised; identity may be inferred from clothing,
movement or context. The data-look report noted that the same person moves through the beam in most sessions; the ARM-I
motion split shows the preference for the true pattern in both the static and the moving frames.

## Provenance

Principal: Cathal Ryan Hynes (PolieBotics). Drafted, built, trained and evaluated with BOSUN, the project's automated
research assistant (a Claude-family language model running the project's desks), under the principal's direction; BOSUN
holds no authority and every publication step is the principal's. Second-model results audits by GPT-6 Astra through
`codex exec`, one round each on the statistic and the pix2pixHD work and two rounds on ARM-I, all on 9 September 2026 and
all before this package was built; their fixes are applied in the reports as published here, and their verdict lines are
in `AUDIT_TRAIL.md`; these are model reviews, not independent validation. The ARM-I arms trained on two rented single-A100
machines (about 2.6 machine-hours in all); the pix2pixHD runs on one rented A100 for about six hours; the statistic on the
development machine's CPU. The data are the public Truth Beam archives named in the primer, every file verified against
their manifests before use. The images published here and in the bundle show a masked participant as the previous section
states. Patent filing date: 6 September 2026. Licence: `LICENSE` (the Dark Lantern Research and Private Use Licence 1.2,
the repository's): non-commercial research, teaching, verification and private study; all other rights reserved; section 5
of the licence states what is granted under any patent.

— BOSUN ⚓

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-09 | BOSUN | First version: the three results of the night of 9 September 2026 packaged after their results audits. |
| 1.1 | 2026-09-09 | BOSUN | Package audit round 1 (REVISE) applied: the checkpoint count (thirteen ARM-I plus one ARM-C control), the two-choice comparison distinguished from the average-of-prescribed-wrong-emissions comparison, `REPRODUCE.md` added, the principal's decisions of the same day (the ship named, the results published together). |
| 1.2 | 2026-09-09 | BOSUN | Package audit round 2 applied: the figure sentence says which figures regenerate from the results files; the held January 2025 measurements removed from the interval summary and the bundle's pretrain log (`REDACTION.md`). |
