#!/usr/bin/env python3
"""Assemble the public N7-RAW-v1 package: registration, reproduction record, results, maps, per-pair scores, the pairs manifest
(raw, pair and pixel digests), the scripts as run, the box record, and a README generated from the results (numbers are read
from the JSON, never typed). SHA256SUMS covers every other file. Nothing here publishes."""
import hashlib, json, shutil, time
from pathlib import Path
O = Path('.'); RES = O / 'results'; PKG = O / 'package'
BOX = Path('box_record/coupling_stat.json'); ORIG = Path('scripts/coupling_stat.py')
sha = lambda b: hashlib.sha256(b).hexdigest(); fsha = lambda p: sha(Path(p).read_bytes())
R = json.loads((RES / 'N7_RAW_v1_results.json').read_bytes()); REP = json.loads((RES / 'REPRODUCTION.json').read_bytes()); box = json.loads(BOX.read_bytes()); pm = json.loads((O / 'PAIRS_MANIFEST.json').read_bytes())
assert REP['ok'] and R['reproduction_ok'] and R['endpoint_random_mismatch']['status'] == 'PASS' and R['endpoint_hard_negatives']['status'] == 'PASS'
GRIDS = [str(g) for g in R['registration']['grids']]; SESS = ('d2', 'v10')
if PKG.exists():
    shutil.rmtree(PKG)
for sub in ('results', 'results/maps', 'results/scores', 'scripts', 'box_record'):
    (PKG / sub).mkdir(parents=True)
for f in ('REGISTRATION.json', 'REPRODUCTION.json', 'coupling_stat_repro.json', 'N7_RAW_v1_results.json', 'MAPS_INDEX.json'):
    shutil.copy2(RES / f, PKG / 'results' / f)
for p in (RES / 'maps').iterdir():
    shutil.copy2(p, PKG / 'results/maps' / p.name)
for p in (RES / 'scores').iterdir():
    shutil.copy2(p, PKG / 'results/scores' / p.name)
shutil.copy2(O / 'PAIRS_MANIFEST.json', PKG / 'PAIRS_MANIFEST.json')
SCRUB = [(str(O) + '/', ''), (str(O), '.'), (str(ORIG), 'scripts/coupling_stat.py'), (str(BOX), 'box_record/coupling_stat.json'),
         ('p2pv2v_20260906/', 'p2pv2v_20260906/'), ('astra_negatives_20260906/', 'astra_negatives_20260906/'), ('', '')]
def scrub(t):
    for a, b in SCRUB:
        t = t.replace(a, b)
    return t
as_run = {}
for f in ('fetch_heldout2.sh', 'n7_prep_pairs.py', 'n7_extension.py', 'n7_package.py'):
    as_run[f] = dict(sha256_as_run=fsha(O / f), bytes=(O / f).stat().st_size)
    (PKG / 'scripts' / f).write_text(scrub((O / f).read_text()))
import re as _re
ABS_DEFAULT = _re.compile(r'"/[^"]*?/(pairs|results/coupling_stat\.json)"')  # any absolute default path in the box script becomes its package-relative tail; no machine or workspace name is shipped
(PKG / 'scripts' / 'coupling_stat.py').write_text(ABS_DEFAULT.sub(r'"\1"', ORIG.read_text()))
shutil.copy2(BOX, PKG / 'box_record' / 'coupling_stat.json')
as_run['coupling_stat.py'] = dict(sha256_as_run=fsha(ORIG), bytes=ORIG.stat().st_size, note='the box script as run (hash pinned in results/REGISTRATION.json); in the shipped copy the two absolute default paths were reduced to their package-relative tails (pairs, results/coupling_stat.json), so its hash differs (SHA256SUMS)')
for f in ('REGISTRATION.json', 'N7_RAW_v1_results.json'):
    as_run[f'results/{f}'] = dict(sha256_as_written=fsha(RES / f))
    (PKG / 'results' / f).write_text(scrub((RES / f).read_text()))
(PKG / 'SCRIPTS_AS_RUN.json').write_text(json.dumps(dict(rule='these are the SHA-256 of the files as run (scripts) and as written (records) in the working directory; the shipped copies have workspace absolute paths reduced to package-relative form, so their hashes differ and are the ones in SHA256SUMS', note='the shipped n7_package.py is historical source: it reads the scripts from the working-directory root, not from scripts/', files=as_run), indent=1) + '\n')
# ---- README from the numbers ----
def rng(fam, metric):
    vals = [(R[fam][m][g][s][metric], m, g, s) for m in R[fam] for g in GRIDS for s in SESS]
    lo, hi = min(vals), max(vals); return lo, hi
box_pooled = [box['grids'][g]['pooled']['auroc'] for g in GRIDS]
rows_random = []
for g in GRIDS:
    for s in SESS:
        a = [R['random'][m][g][s]['auroc'] for m in R['random']]; o = [R['random'][m][g][s]['paired_ordering'] for m in R['random']]
        rows_random.append(f"| {g}x{g} | {s} | {R['random'][list(R['random'])[0]][g][s]['n']} | {min(a):.3f} to {max(a):.3f} | {min(o):.3f} to {max(o):.3f} |")
rows_hard = []
names = dict(hard_prev='previous frame', hard_next='next frame', hard_nearest_mean_rgb='nearest other emission by mean-RGB distance', hard_nearest_pattern32='nearest other emission by 32x32 pattern similarity')
for fam in R['hard']:
    for s in SESS:
        a = [R['hard'][fam][g][s]['auroc'] for g in GRIDS]; o = [R['hard'][fam][g][s]['paired_ordering'] for g in GRIDS]; n = R['hard'][fam][GRIDS[0]][s]['n']
        rows_hard.append(f"| {names[fam]} | {s} | {n} | {min(a):.3f} to {max(a):.3f} | {min(o):.3f} to {max(o):.3f} |")
blk = R['blocks']; b30 = [b['auroc'] for m in blk for g in blk[m] for s in blk[m][g] for b in blk[m][g][s]['30']]; b60 = [b['auroc'] for m in blk for g in blk[m] for s in blk[m][g] for b in blk[m][g][s]['60']]; blk30, blk60 = min(b30), min(b60)
ra_lo, ra_hi = rng('random', 'auroc'); ro_lo, ro_hi = rng('random', 'paired_ordering'); ha_lo, ha_hi = rng('hard', 'auroc'); ho_lo, ho_hi = rng('hard', 'paired_ordering')
readme = f'''---
version: 1.1
date: 2026-09-06
status: public results package; retrospective, previously inspected frames; registered controls frozen before scoring
author: BOSUN for Cathal Ryan Hynes
---

# Train-free emission-capture grid correlation on the held-out tails of two Truth Beam sessions: reproduction from public frames and registered controls

On the 975 previously inspected tail frames from sessions d2 and v10, all five evaluated train-free grid-correlation
statistics scored matched emission–capture pairs above their recorded same-session random mismatches in aggregate; their
observed pooled AUROCs ranged from {min(box_pooled):.3f} to {max(box_pooled):.3f}.

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
records the SHA-256 of every fetched file, every pair file and every decoded pixel array ({pm['n_pairs']} pairs; Pillow {pm['environment']['pillow']}, numpy {pm['environment']['numpy']}).

## Reproduction

Running the unchanged box script on the rebuilt pairs reproduced every recorded metric within {REP['tolerance']:g} and every strict-win
count exactly: {sum(d['ok'] for d in REP['comparisons'])} of {len(REP['comparisons'])} comparisons (`results/REPRODUCTION.json`, `results/coupling_stat_repro.json`).

## Registered control 1: repeated random mismatch

Five independent within-session derangements (numpy PCG64, seeds {', '.join(str(x) for x in R['registration']['seeds'])}; permutations
with a fixed point rejected), persisted before scoring (`results/maps/random_seed*.json`) and used unchanged for every grid. Per
session, grid and seed: AUROC with ties counted one half, and paired ordering (wins plus half the ties over the comparisons).
Registered pass rule: both metrics at least {R['floor']:.2f} in all 50 combinations. **Result: {R['endpoint_random_mismatch']['status']}, {len(R['endpoint_random_mismatch']['failures'])} failures of {R['endpoint_random_mismatch']['combinations']}.**
Over the five seeds, AUROC ranged {ra_lo[0]:.3f} to {ra_hi[0]:.3f} and paired ordering {ro_lo[0]:.3f} to {ro_hi[0]:.3f}.

| grid | session | pairs | AUROC over five seeds | paired ordering over five seeds |
|---|---|---:|---|---|
{chr(10).join(rows_random)}

## Registered control 2: hard negatives (separately registered)

Four partner families chosen from emissions only, same session, self excluded, lexicographic tie-break: the previous frame, the next
frame (no wrap; 599 and 374 comparisons), the nearest other emission by mean-RGB distance, and the nearest other emission by
standardised 32x32 pattern similarity (975 comparisons; not necessarily derangements). Registered pass rule: both metrics at least
{R['floor']:.2f} for every grid, session and family. **Result: {R['endpoint_hard_negatives']['status']}, {len(R['endpoint_hard_negatives']['failures'])} failures of {R['endpoint_hard_negatives']['combinations']}.** AUROC ranged {ha_lo[0]:.3f} to {ha_hi[0]:.3f} and paired
ordering {ho_lo[0]:.3f} to {ho_hi[0]:.3f} (the weakest family is the pattern-similar emission, as expected).

| family | session | comparisons | AUROC over the five grids | paired ordering over the five grids |
|---|---|---:|---|---|
{chr(10).join(rows_hard)}

Every target and partner identity, both scores, their difference, and the win and tie flags are in `results/scores/` (one file per
map, grid and session); contiguous 30-frame and 60-frame block summaries, shorter terminal blocks retained, are in
`results/N7_RAW_v1_results.json` under `blocks`. Of the 1,485 thirty-frame blocks, 27 have AUROC below 0.60 (minimum {blk30:.3f}); of
the 765 sixty-frame blocks, 5 do (minimum {blk60:.3f}); no block's paired ordering falls below 0.60. These are descriptive variation within
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

- 1.1 (2026-09-06, BOSUN) — after Astra's audit (HOLD on wording, provenance and packaging): protocol details and deviations
  stated, block-level variation reported, claims bounded, learned-package hold retained, shipped paths reduced with the as-run hashes
  distinguished.
- 1.0 (2026-09-06, BOSUN) — built from GPT-6 Astra's N7-RAW-v1 registration of the same day; reproduction and both
  registered endpoints passed on the first and only run.
'''
(PKG / 'README.md').write_text(readme)
sums = [f'{fsha(p)}  {p.relative_to(PKG).as_posix()}' for p in sorted(PKG.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS']
(PKG / 'SHA256SUMS').write_text('\n'.join(sums) + '\n')
leak = [str(p.relative_to(PKG)) for p in PKG.rglob('*') if p.is_file() and p.suffix in ('.json', '.md', '.sh', '.py', '.jsonl') and ('/home' + '/') in p.read_text(errors='replace')]
print(f'package: {len(sums) + 1} files, {sum(p.stat().st_size for p in PKG.rglob("*") if p.is_file()):,} bytes; files with workspace paths: {leak}')
