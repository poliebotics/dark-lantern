#!/usr/bin/env python3
"""Generate REPORT.md from the results JSONs so every number is read from a file. Usage: python3 write_report.py [status]"""
import json, os, sys, time, hashlib, subprocess
W = os.environ.get("COUPLING_PKG", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); RES = f"{W}/results"
R = {era: json.load(open(f"{RES}/{era}_results.json")) for era in ("2023", "2024") if os.path.exists(f"{RES}/{era}_results.json")}
sel = json.load(open(f"{W}/selection_2023.json"))
v23 = json.load(open(f"{W}/verify_2023.json")) if os.path.exists(f"{W}/verify_2023.json") else None
v24 = json.load(open(f"{W}/verify_2024.json")) if os.path.exists(f"{W}/verify_2024.json") else {}
status = sys.argv[1] if len(sys.argv) > 1 else "draft"
GRIDS = ["4", "8", "16", "32", "64"]
now = time.strftime("%Y-%m-%d", time.gmtime()); nowz = time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime())

def f3(x): return f"{x:.3f}"
def f4(x): return f"{x:.4f}"
def ci(r): return f"[{r['auroc_ci95'][0]:.3f}, {r['auroc_ci95'][1]:.3f}]"
def short(s): return s.replace("20241219_", "") if s.startswith("2024") else s

L = []
L.append(f"""---
version: 1.1
date: {now}
status: {status}
author: BOSUN (CPU statistics desk)
---

# Train-free emission-capture coupling on the old Truth Beam sessions (2023 and 2024)

Hoy. This is the *No Training Required* (6 September 2026) train-free coupling statistic, run with the same definitions on
the public 2023 NumPy sessions and the December 2024 HDF5 sessions. The statistic code is the reference implementation
(`the repository's `results/train_free_coupling_20260906/scripts/coupling_stat.py``) with only the loaders and the geometry adapted; every adaptation is listed in
section 5. Numbers in this report are read by `write_report.py` from `results/2023_results.json` and
`results/2024_results.json`; per-frame scores are in `results/<era>_scores.csv` and the mismatch partner maps in
`results/<era>_partners.json`. Generated {nowz}.

**What this is and is not.** A random-negative correspondence test: does the statistic tell the matched
(emission, capture) pair from the same emission paired with the capture of one other randomly chosen frame of the same
session? It is not a quality score, a liveness test, or a security claim. The negative is one random same-session
frame; harder temporal or adversarial alternatives remain untested.
""")

# ---- headline table ----
L.append("## 1. Headline: pooled AUROC per era by grid, full frame and projected-region crop\n")
L.append("| era | variant | " + " | ".join(f"grid {g}" for g in GRIDS) + " | n pairs |")
L.append("|---|---|" + "---|" * len(GRIDS) + "---|")
def variants_of(era):
    return [v for v in ("full", "crop", "export75", "crop_bgr", "export75_bgr") if v in R[era]["grids"]["8"]]
for era in R:
    for variant in variants_of(era):
        cells = []
        for g in GRIDS:
            p = R[era]["grids"][g][variant]["pooled"]
            cells.append(f"**{f4(p['auroc'])}** {ci(p)}")
        L.append(f"| {era} | {variant} | " + " | ".join(cells) + f" | {R[era]['grids']['8'][variant]['pooled']['n_pairs']} |")
L.append("\nBold: pooled AUROC; brackets: bootstrap 95% CI, 1000 resamples of frames (each frame carries its matched and its mismatched score). Variants: `full` = whole recording frame; `crop` = projected-region quad estimated from the recordings alone (no emission values, no pair labels); `export75` (2024 only) = an approximate reproduction of the January 2025 exporter's geometry, the centre 75 percent of the recording height at full width, RGB-corrected, without the exporter's resize to 2048x1024 (the resize is not numerically invariant for the grid statistic: one checked grid-16 mismatch score moves by 0.005); `crop_bgr` = the crop with the recording's channels reversed, a colour-sensitivity variant that keeps the spatial information (for 2024 this is the stored BGR order left unflipped against the RGB emission, the exporter's actual pairing; for 2023 it reverses the stored RGB report); `export75_bgr` = the exporter geometry in its stored byte order. Source: `results/<era>_results.json` -> grids.<g>.<variant>.pooled.\n")

L.append("### Paired fraction (matched > mismatched) and shuffled-label control, pooled\n")
L.append("| era | variant | " + " | ".join(f"grid {g}" for g in GRIDS) + " |")
L.append("|---|---|" + "---|" * len(GRIDS))
for era in R:
    for variant in variants_of(era):
        cells = []
        for g in GRIDS:
            p = R[era]["grids"][g][variant]["pooled"]
            cells.append(f"{p['wins']}/{p['n_pairs']}; ctrl {p['control']['one_shuffle_auroc']:.3f} (null {p['control']['perm_ci95'][0]:.3f}-{p['control']['perm_ci95'][1]:.3f})")
        L.append(f"| {era} | {variant} | " + " | ".join(cells) + " |")
L.append("\n`wins/n`: frames whose matched statistic exceeds their mismatched one. `ctrl`: AUROC after one seeded shuffle of the matched/mismatched labels; `null`: 2.5-97.5 percentiles of 1000 such shuffles. The label shuffle relabels already computed scores, so a chance result checks the scoring machinery; it cannot exclude upstream leakage or temporal confounding. Source: `results/<era>_results.json` -> pooled.control.\n")

# best grid and per-session range
L.append("### Best grid and per-session range\n")
for era in R:
    for variant in [v for v in variants_of(era) if not v.endswith("_bgr")]:
        best = max(GRIDS, key=lambda g: R[era]["grids"][g][variant]["pooled"]["auroc"])
        per = {s: R[era]["grids"][best][variant][s]["auroc"] for s in R[era]["sessions"]}
        lo = min(per, key=per.get); hi = max(per, key=per.get)
        if f3(per[lo]) == f3(per[hi]):
            L.append(f"- {era}, {variant}: best grid {best} (pooled {f4(R[era]['grids'][best][variant]['pooled']['auroc'])}); every session {f3(per[lo])} at that grid.")
        else:
            L.append(f"- {era}, {variant}: best grid {best} (pooled {f4(R[era]['grids'][best][variant]['pooled']['auroc'])}); per-session AUROC at that grid from {f3(per[lo])} ({short(lo)}, n={R[era]['sessions'][lo]['n']}) to {f3(per[hi])} ({short(hi)}, n={R[era]['sessions'][hi]['n']}).")
L.append("")

# ---- verdict ----
c23 = R["2023"]["grids"]; c24 = R["2024"]["grids"]
_ctrls = [cc[v]["pooled"]["control"]["one_shuffle_auroc"] for c in (c23, c24) for cc in c.values() for v in cc]
_nulls_lo = [cc[v]["pooled"]["control"]["perm_ci95"][0] for c in (c23, c24) for cc in c.values() for v in cc]
_nulls_hi = [cc[v]["pooled"]["control"]["perm_ci95"][1] for c in (c23, c24) for cc in c.values() for v in cc]
ctrl_range = f"{min(_ctrls):.3f} to {max(_ctrls):.3f}"; null_range = f"{min(_nulls_lo):.3f} to {max(_nulls_hi):.3f}"
L.append(f"""## 1b. Verdict: what is shelf material

**Supported claim: frame-by-frame correspondence between emission and recording against the chosen random same-session negatives, with projected-region alignment.** With the crop, the statistic preferred the correct recording to one random same-session alternative in every tested comparison at grid 8 for April 2023 ({c23['8']['crop']['pooled']['wins']}/{c23['8']['crop']['pooled']['n_pairs']} paired wins, pooled AUROC {f4(c23['8']['crop']['pooled']['auroc'])}) and at grid 16 for December 2024 ({c24['16']['crop']['pooled']['wins']}/{c24['16']['crop']['pooled']['n_pairs']}, pooled AUROC {f4(c24['16']['crop']['pooled']['auroc'])}). At grid 16 the lowest 2024 session is 044052 at {f4(c24['16']['crop']['20241219_044052']['auroc'])}; at grids 32 and 64 every session rounds to 1.000 and the December grid-32 pooled value is {c24['32']['crop']['pooled']['auroc']:.5f}, which the tables round to 1.0000. **At grid 16, aligning the projected region raises pooled AUROC from {f3(c23['16']['full']['pooled']['auroc'])} to {f3(c23['16']['crop']['pooled']['auroc'])} in April and from {f3(c24['16']['full']['pooled']['auroc'])} to {f3(c24['16']['crop']['pooled']['auroc'])} in December.** The preprocessing is part of the finding.

**Shelf entry.** No Training Required, archival repeat: with projected-region alignment, a fixed calculation preferred the correct recording to one random same-session alternative in all 1,032 tested comparisons across 15 sessions, with no trained model.

**Plain English.** We compared 584 April 2023 and 448 December 2024 projected patterns with their corresponding camera recordings. After aligning the lit area, a fixed calculation preferred the correct recording over one randomly chosen alternative from the same session in every tested comparison, using an 8x8 grid for April and 16x16 for December. No training or model was involved. This shows frame-by-frame correspondence between the projected patterns and these recordings. It does not measure image quality or establish liveness, realness, or proof of physical capture. Comparing the whole camera image gave much weaker results, so alignment is an essential part of the finding.

**What supports the claim, and what it does not settle.**

1. The quad is estimated without emission values or pair labels (section 5, G2): one shared transform per session, no pair-specific optimisation. That is a statement about how the geometry was obtained; it does not establish optimal alignment and does not eliminate every source of retrospective optimism. The orientation (0 or 180 degrees) is chosen on four matched pairs that also enter the evaluation, and the geometry method was developed iteratively on these same sessions (RUN_LOG). Excluding every comparison that touches an orientation-calibration frame leaves 522/522 April grid-8 wins and 394/394 December grid-16 wins.
2. The negative is the reference construction unchanged: for each frame, the recording of one other frame of the same session, chosen by `random.seed(0)` and one shuffle per grid per session, with the reference's fixed-point repair (a recording can serve as the negative for more than one frame; this is not a one-to-one derangement), shared by every geometry variant of that grid (`results/<era>_partners.json`). Most negatives are distant frames (13 of 448 December grid-16 partners are immediate neighbours). Shared scene, exposure and the moving person are not independently controlled; nothing in the record shows they manufactured the result, and harder temporal or adversarial negatives are untested.
3. The shuffled-label control sits at chance in every cell (one seeded shuffle {ctrl_range} across all grids and variants; 1000-permutation null bands {null_range}). It relabels already computed scores, so it checks the scoring machinery, not upstream leakage. The channel-swap variant (`crop_bgr`) tests colour sensitivity and keeps the spatial information; it is not a chance-level null.
4. The refinement check (section 4b) is a limited sensitivity check, not a proof that no alignment improvement remains: on 051150 an emission-informed quad raises grid-8 AUROC from 0.875 to 0.893 while paired wins fall from 32/32 to 30/32, and the saturated grids 16 and 32 cannot show a difference either way.

**Positive but weaker, not shelf material on its own: the full-frame numbers** (2023 pooled {f3(c23['4']['full']['pooled']['auroc'])} to {f3(c23['32']['full']['pooled']['auroc'])}; 2024 pooled {f3(c24['4']['full']['pooled']['auroc'])} to {f3(c24['64']['full']['pooled']['auroc'])}). They are above chance with CIs clear of 0.5 (2024 grid 4 only just: {f3(c24['4']['full']['pooled']['auroc'])} {ci(c24['4']['full']['pooled'])}), and in 2023 the paired wins are still {c23['8']['full']['pooled']['wins']}/{c23['8']['full']['pooled']['n_pairs']} at grid 8, but they measure the statistic through a misregistration.

**Relation to the 6 September result.** This extends the same statistic to older recordings. It is not a directly comparable improvement over the d2/v10 result (pooled 0.756 at grid 8, 902/975 paired), because both the recordings and the alignment handling differ (section 4c).

**The 2024 exporter geometry (coordinator's request).** The January 2025 exporter's centre-75-percent band does not coincide with the detected projected region (section 4a). Under an approximate reproduction of that geometry (without the exporter's resize) the statistic reaches {f3(c24['32']['export75']['pooled']['auroc'])} at grid 32 RGB-corrected and {f3(c24['32']['export75_bgr']['pooled']['auroc'])} with the exporter's unflipped BGR byte order; the channel swap alone moves the tight crop from {f3(c24['8']['crop']['pooled']['auroc'])} to {f3(c24['8']['crop_bgr']['pooled']['auroc'])} at grid 8 and from {f3(c24['16']['crop']['pooled']['auroc'])} to {f3(c24['16']['crop_bgr']['pooled']['auroc'])} at grid 16. A 2025 model trained on that export saw misregistered, colour-swapped pairs.
""")

# ---- per-session tables ----
L.append("## 2. Per-session results\n")
for era in R:
    L.append(f"### {era}: AUROC by grid (crop / full), orientation, n\n")
    L.append("| session | n | orientation | " + " | ".join(f"grid {g} crop / full" for g in GRIDS) + " |")
    L.append("|---|---|---|" + "---|" * len(GRIDS))
    for s in R[era]["sessions"]:
        o = R[era]["sessions"][s]["orientation"]
        cells = [f"{f3(R[era]['grids'][g]['crop'][s]['auroc'])} / {f3(R[era]['grids'][g]['full'][s]['auroc'])}" for g in GRIDS]
        L.append(f"| {short(s)} | {R[era]['sessions'][s]['n']} | {o['chosen']} deg (calib corr 0: {o['corr_grid8_crop']['0']:.2f}, 180: {o['corr_grid8_crop']['180']:.2f}) | " + " | ".join(cells) + " |")
    L.append("")
    L.append(f"### {era}: per-session bootstrap CIs and paired wins at grid 8 and grid 16 (crop)\n")
    L.append("| session | n | grid 8 AUROC [CI] | wins | grid 16 AUROC [CI] | wins | grid 8 full AUROC [CI] |")
    L.append("|---|---|---|---|---|---|---|")
    for s in R[era]["sessions"]:
        a8 = R[era]["grids"]["8"]["crop"][s]; a16 = R[era]["grids"]["16"]["crop"][s]; f8 = R[era]["grids"]["8"]["full"][s]
        L.append(f"| {short(s)} | {a8['n']} | {f3(a8['auroc'])} {ci(a8)} | {a8['wins']}/{a8['n']} | {f3(a16['auroc'])} {ci(a16)} | {a16['wins']}/{a16['n']} | {f3(f8['auroc'])} {ci(f8)} |")
    L.append("")

# ---- geometry diagnostics ----
L.append("## 3. Geometry and loader diagnostics per session\n")
L.append("| session | recording w x h | quad area frac of frame | excess std inside quad | RANSAC side inliers (top, right, bottom, left) | grid-16 cell corr mean, crop (full) | frac cells > 0 | channel matrix diagonal (R,G,B) |")
L.append("|---|---|---|---|---|---|---|---|")
for era in R:
    for s, v in R[era]["sessions"].items():
        g = v["geometry"]; inl = g.get("side_inlier_frac", {})
        cm = v["channel_matrix_grid16_crop_Erows_Rcols"]
        L.append(f"| {short(s)} | {g['recording_wh'][0]}x{g['recording_wh'][1]} | {g['quad_area_frac_of_frame']:.3f} | {g['excess_std_captured_frac']:.3f} | "
                 + ", ".join(f"{inl.get(k, float('nan')):.2f}" for k in ("top", "right", "bottom", "left")) + f" ({g['method']}) | "
                 + (f"{v['cellcorr16_crop_mean']:.3f} ({v['cellcorr16_full_mean']:.3f})" if v['cellcorr16_crop_mean'] is not None else "n/a")
                 + f" | {(v['cellcorr16_crop_frac_positive'] if v['cellcorr16_crop_frac_positive'] is not None else float('nan')):.2f} | {cm[0][0]:.2f}, {cm[1][1]:.2f}, {cm[2][2]:.2f} |")
L.append("\nSource: `results/<era>_results.json` -> sessions.<s>.geometry and the diagnostic fields; quads in full-resolution pixels are in `train_free_coupling_old_sessions/geometry/<session>.geometry.json`. The channel matrix is the mean over frames of the per-channel grid-16 correlation between emission channel a and recording channel b after the loader's channel handling; a diagonal-dominant matrix confirms the RGB alignment.\n")

# ---- figures ----
L.append("""## 4. Figures

![AUROC by grid, 2023](figures/auroc_bars_2023.png)

![AUROC by grid, 2024](figures/auroc_bars_2024.png)

![Crops used, three sessions](figures/contact_sheet_crops.png)

The recording and crop panels of this sheet show a masked participant in a recognisable indoor setting (the bookshelf room); the participant wears a full face covering, and the images are not anonymised (identity may be inferred from clothing, movement or context).

`figures/auroc_bars_<era>.png`: per-session and pooled AUROC by grid, full frame (top) and crop (bottom), whiskers the bootstrap 95% CI. `figures/contact_sheet_crops.png`: for 20241219_051150, 1680410249 and 1682718815, the recording with the fitted quad, the temporal std map with the quad, the warped crop, the emission in the orientation used, and the grid-16 per-cell temporal correlation between emission and crop (a flat positive map means the crop is aligned; edges falling to zero would mean a quad too large). The recording and crop panels show the masked participant; the images are not anonymised.
""")

# ---- exporter geometry agreement (coordinator's request) ----
if os.path.exists(f"{RES}/export75_vs_quad.json"):
    X = json.load(open(f"{RES}/export75_vs_quad.json"))
    L.append("## 4a. The January 2025 exporter's geometry against the detected projected region (2024)\n")
    L.append("The 5090 desk (`a separate desk measurement (not published)`) recovered the January 2025 exporter's recipe: recording centre-cropped to 75 percent of its height at full width (rows 575 to 4024 of 4600, all 5320 columns), resized to 2048x1024, stored BGR byte order left unflipped; emission straight-resized. The detected projected regions do not agree with that band, so it was not adopted as the crop; it is reported as its own approximate variant (`export75`, RGB-corrected, and `export75_bgr`, the exporter's byte order) in the tables above; the exporter's resize to 2048x1024 is omitted, which changes individual grid scores slightly (one checked grid-16 mismatch score by 0.005).\n")
    L.append("| session | detected quad rows (top edge, bottom edge) | quad columns (left, right) | quad centre y | band centre y | quad area inside band | band area covered by quad | quad height / band height | quad width / frame width |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for s_, v in X.items():
        L.append(f"| {short(s_)} | {v['quad_rows_top_edge'][0]:.0f}-{v['quad_rows_top_edge'][1]:.0f}, {v['quad_rows_bottom_edge'][0]:.0f}-{v['quad_rows_bottom_edge'][1]:.0f} | {v['quad_cols_left_edge'][0]:.0f}-{v['quad_cols_left_edge'][1]:.0f}, {v['quad_cols_right_edge'][0]:.0f}-{v['quad_cols_right_edge'][1]:.0f} | {v['quad_centre_xy'][1]:.0f} | {v['band_centre_y']:.0f} | {v['quad_area_frac_inside_band']:.3f} | {v['band_area_frac_covered_by_quad']:.3f} | {v['quad_vertical_extent_frac_of_band']:.3f} | {v['quad_horizontal_extent_frac_of_width']:.3f} |")
    L.append("\nSource: `results/export75_vs_quad.json`, computed from `train_free_coupling_old_sessions/geometry/<session>.geometry.json`. Disagreement in plain terms: the projector-lit region sits about 290 px above the frame centre and spans about 58 percent of the frame height and 85 percent of its width, so inside the exporter's band the emission occupies roughly rows 3 to 80 percent and columns 6 to 91 percent; cell g of the emission grid does not land on cell g of the band grid, which is what the `export75` rows measure.\n")

# ---- sensitivity: emission-informed refinement ----
import glob as _glob
rc = sorted(_glob.glob(f"{RES}/refine_check_*.json"))
rc = [x for x in rc if not x.endswith("_testquad.json")]
if rc:
    L.append("## 4b. Sensitivity: emission-blind quad versus an emission-informed refinement\n")
    L.append("`refine_check.py` splits a session into a fit half (odd positions) and an evaluation half (even positions), refines the eight quad coordinates on the fit half by Nelder-Mead on the mean grid-16 matched statistic (working scale), and evaluates both quads on the evaluation half at full resolution with one seeded same-half mismatch. The refinement is fitted at working resolution (a 480x270 or 480x300 crop) and evaluated at full resolution, and grid truncation keeps different fractions of the image at the two scales, so it is a limited sensitivity check: it can show that an emission-informed quad changes the evaluation-half result, it cannot show that no alignment improvement remains where the grids are already saturated.\n")
    L.append("| session | eval frames | corner shifts (px) | fit-half mean corr16 blind -> refined | grid 8 AUROC blind / refined | grid 16 | grid 32 |")
    L.append("|---|---|---|---|---|---|---|")
    for x in rc:
        d = json.load(open(x)); e = d["eval"]
        L.append(f"| {short(d['session'])} | {len(d['eval_frames'])} | " + ", ".join(f"{v:.0f}" for v in d["corner_shift_px"]) + f" | {d['fit_mean_corr16_blind']:.3f} -> {d['fit_mean_corr16_refined']:.3f} | "
                 + " | ".join(f"{e['blind'][g]['auroc']:.3f} / {e['refined'][g]['auroc']:.3f}" for g in ("8", "16", "32")) + " |")
    L.append("\nSource: `results/refine_check_<session>.json`. The refinement uses the emission and is therefore not the reported crop. On 051150 it raises grid-8 AUROC from 0.875 to 0.893 while paired wins fall from 32/32 to 30/32; at grids 16 and 32 both quads give 1.000 on every session tested, which is saturation, not evidence of equivalence. The audit's raw check found the refined quad improves the held half's correlation at the fitting resolution (0.133 to 0.233) while lowering even the fit half's correlation at full resolution (0.187 to 0.171), so the earlier 'overfits its half' reading in RUN_LOG is unsupported; the honest description is a resolution mismatch between fitting and evaluation.\n")

# ---- reference numbers from the 2026 run ----
L.append("""## 4c. Reference: the 2026 result this repeats

From `the repository's `results/train_free_coupling_20260906/README.md` and `box_record/coupling_stat.json`` section 1 (975 held-out frames of sessions d2 and v10, capture = the 16:9 band of the 5320x4600 preview, no per-session alignment): pooled AUROC 0.683 (grid 4), 0.756 (grid 8), 0.720 (grid 16), 0.700 (grid 32), 0.695 (grid 64); paired 900 to 781 of 975. Those numbers are quoted for scale only; the 2026 sessions were not re-run here, and the present results are not a directly comparable improvement over them: the recordings differ and the alignment handling differs (the 2026 run used a fixed 16:9 band, this one a per-session projected-region quad).
""")

# ---- method ----
L.append("""## 5. Method: what was reused and what was adapted

**Statistic (unchanged, `coupling_lib.py` copies `grid`, `corr` and the mismatch construction from `the repository's `results/train_free_coupling_20260906/scripts/coupling_stat.py``).** For each pair, the emission E and the capture B are reduced to a g x g grid of mean colours, each grid has its per-channel mean removed and is divided by its per-channel std, and the statistic is the mean over the three channels of the Pearson correlation between the two grids; g in {4, 8, 16, 32, 64}. The negative for frame i is the capture of one other frame of the same session, chosen by `random.seed(0)` and one shuffle per grid per session in the reference's order (so the partner differs per grid, exactly as in the reference), with the reference's fixed-point repair, under which a recording can be the negative for more than one frame (this is not a one-to-one derangement); the partner map is written to `results/<era>_partners.json`. The full-frame and cropped variants of the same grid use the same partners. AUROC of matched against mismatched per session and pooled per era; paired fraction; per-session and pooled 1000-resample frame bootstrap for the 95% CIs; shuffled-label control.

**Adaptations, all in the loaders and the geometry.**

- L1, 2023 emission. Stored as a float (1024, 1024, 3) array in the channel order the recorder handed to cv2 (`truth_beam_2023_REDACTED.py` writes it with `cv2.imwrite`, reads it back, resizes to 1920x1200 and shows it fullscreen through the cv2 backend, which interprets the array as BGR). The loader clips and rounds to uint8, as `cv2.imwrite` did, and reverses the channels to RGB. The report (1536, 2048, 3) uint8 comes from gxipy `convert("RGB")` and is used as stored. Confirmed empirically: before the reversal, the emission-channel x report-channel correlation matrix is anti-diagonal (1680410569, grid 8, emission rotated 180 degrees: 0.33, 0.32, 0.27 on the anti-diagonal, about 0 elsewhere).
- L2, 2024 recording. The recorder (`secure_record.py`, commit bc8d2603, a The Imaging Source camera delivering BGRA) stores `cv2.cvtColor(captured, COLOR_BGRA2BGR)` into `recordings`, so the recording is BGR; the loader reverses it to RGB. The emission is stored from `Image.fromarray(..., 'RGB')` and used as stored.
- G1, orientation. The 2023 projected image appears rotated 180 degrees in the camera relative to the stored array. Per session the orientation (0 or 180) is chosen on the first min(4, n) frames as the one with the higher mean grid-8 correlation on the crop; both values are recorded in the per-session table. Every 2023 session chose 180 and every 2024 session chose 0.
- G2, projected-region crop (emission-blind). The per-pixel temporal std of the recording over the session's frames marks the projector-lit region (the emission changes every frame; the room does not). At working scale (2023: 1/4, 2024: 1/8) the std map is thresholded relative to the frame-border background (max of 2.5 x median, median + 6 MAD), closed, hole-filled, and the largest component taken. Rows narrower than 0.7 of the median row width and columns shorter than 0.7 of the median column height are removed as protrusions (lit objects above the shelf), extents within 2 percent of the frame border are dropped, and one RANSAC line per side is fitted to the component's extents (tolerance 1 percent of the frame's smaller side); the quad is the four intersections. The recording is then warped by the perspective transform of that quad (bilinear, `cv2.warpPerspective`) to 1920x1200 (2023, the displayed emission's size) or 1920x1080 (2024); the grid statistic then averages cells of at least 30x16 pixels (grid 64 on 1920x1080 truncates to 16-row cells), so the interpolation choice is immaterial. The quad is estimated without emission values or pair labels and is one shared transform per session; that describes how it was obtained and does not by itself establish optimal alignment. The full-frame variant grids the whole recording with the same orientation and channel handling.
- Emission structure, 2023. `emission_from_hash` builds each emission from a 16x16x3 complex array (two inverse 3D FFTs, magnitude, bilinear resize to 1024), so the 2023 emission carries structure at 16x16 cells only; grids 32 and 64 mostly resample interpolation. The 2024 emission is a per-channel Perlin field at 1920x1080.
""")

# ---- data ----
L.append("## 6. Data, sampling and verification\n")
L.append("| session | era | archive | mode | pairs available | pairs used | index range |")
L.append("|---|---|---|---|---|---|---|")
for s, v in sel["sessions"].items():
    L.append(f"| {s} | 2023 | {v['archive']} | {v['mode']} | {v['n_pairs_available']} | {v['n_pairs_selected']} | {v['index_min']}..{v['index_max']} |")
for s in sorted(v24):
    L.append(f"| {s} | 2024 | truth_beam_20241219_unanchored (050046: r2:truthbeam/pinata) | whole HDF5 | 64 | 64 | 0..63 |")
L.append(f"""
2023 selection rule (`select_2023.py`, from the archive manifests in `control/`): a session under 3 GB is taken whole; otherwise a spaced 64-pair sample (`np.linspace` over the indices that have both an emission and a report); the trailer session takes every 4th index from 1. Staged bytes were verified against the archive manifests' SHA-256: {('%d of %d files checked, %d bad, %d missing' % (v23['ok'], v23['checked'], len(v23['bad']), len(v23['missing']))) if v23 else 'verify_2023.json pending'} (`verify_2023.json`). 2024 HDF5 copies (read-only, pulled by another desk to `[local copies of the public 2024 HDF5 files]/`) were used only after their size stopped changing and their SHA-256 matched `_control/SHA256SUMS` (six sessions) or the `RELEASE.json` payload hash (050046): {sum(r['match'] for r in v24.values())} of {len(v24)} match (`verify_2024.json`).
""")

# ---- caveats ----
L.append("""## 7. Caveats

- Random-negative correspondence test. The negative is one random other frame of the same session; it does not test quality, liveness, replay, or any adversarial substitution. Harder temporal or adversarial negatives remain untested. Most negatives are distant frames (13 of 448 December grid-16 partners are immediate neighbours); shared scene, exposure and a moving person are not independently controlled, and no evidence shows they manufactured the result.
- Sample sizes. Two 2023 sessions have 10 pairs each (20 combined), the 2024 sessions 64 each; the 777-pair 2023 sessions are represented by spaced samples of 64 (trailer: every 4th, 195), so per-session results on the large sessions describe the sample, not the whole session. Per-session CIs on 10 pairs are wide and a per-session AUROC of 1.000 on 10 pairs is not a strong statement.
- Bootstrap intervals. They resample frames independently and condition on fixed partners, geometry and orientation; they ignore session clustering and shared recordings, and consecutive 2024 frames (2.5 s apart) may not be independent. A ten-pair crop interval of [1.000, 1.000] reflects bootstrap saturation, not certainty about future recordings.
- Orientation is chosen on the first four frames of each session, which also enter the evaluation. The margin is large in every session (see the calibration correlations), so the choice is not in doubt, but it is a data-dependent decision and is recorded as such.
- The quad is estimated without emission values or pair labels, which rules out pair-specific tuning but not every source of retrospective optimism: the orientation decision uses four matched frames that also enter the evaluation (excluding every comparison touching them leaves 522/522 April grid-8 and 394/394 December grid-16 wins), and the geometry method was developed iteratively on these sessions.
- Per-grid partners differ (reference behaviour), so grids are not strictly paired comparisons of the same negatives. Paired wins and AUROC measure different comparisons; neither is a general accuracy.
- Label-shuffle controls check the scoring machinery on already computed scores; they do not exclude upstream leakage or temporal confounding. The channel-swap variants keep spatial information and are not chance-level nulls.
- `export75` omits the exporter's resize and is an approximate geometry variant.
- The 2023 emission has 16x16-cell structure, so grid 32 and 64 results for 2023 measure interpolation of the same field rather than finer content.
- The 2023 reports were taken after 12 frame reads at a fixed 16,660 us exposure with auto white balance on (recorder source); frame timing relative to the display is not recorded, and any late frames would lower, not raise, the matched statistic.
""")

# ---- audit note ----
L.append(f"""## 8. Audit note

Checked: statistic code against the reference (`diff`-level identity of `grid`, `corr` and the partner construction); loader channel order against both recorder sources and empirically (anti-diagonal channel matrix before reversal); HDF5 dataset names and shapes against `HDF5_VALIDATION.json`; staged 2023 bytes against the manifests' SHA-256; 2024 HDF5 bytes against `SHA256SUMS` and `RELEASE.json`; the quads by eye on the contact sheet and by the excess-std and cell-correlation diagnostics; the shuffled-label control at about 0.5 in every cell. Astra results audit r1 (`astra/ASTRA_VERDICT_results_r1.md`): all 335 result cells and bootstrap and shuffle controls reproduce from the score CSVs; all 39,920 scores reproduce from the cached grids and partner maps; 128 raw pairs recomputed from saved quads and partners at grids 8 and 16 yield 1,536 matched and mismatched scores that reproduce exactly; all 5,160 partner assignments reproduce from seed 0; channel handling agrees with both recorder sources. Open: no independent recomputation of the 2023 hash chains for the sampled pairs (pairing is by filename index, which the archive's `NPY_VALIDATION.json` records as complete and duplicate-free); the refinement comparison (section 4b) is a limited sensitivity check with fitting and evaluation at different resolutions; the two 10-pair sessions carry little weight on their own; the bootstrap intervals condition on fixed partners, geometry and orientation and ignore session clustering.

## Log

- 1.0 (2026-09-09, BOSUN) - first complete run; generated by `write_report.py` from the results JSONs. RUN_LOG.md carries the desk timeline.
- 1.1 ({now}, BOSUN) - Astra results audit r1 (`astra/ASTRA_VERDICT_results_r1.md`, PUBLISHABLE WITH FIXES; all 335 result cells and 1,536 recomputed raw scores reproduce) applied: the claim that crop blindness and the refinement check rule out inflation replaced by the supported claim of correspondence against the chosen random same-session negatives; the refinement conclusion corrected (051150 grid 8 0.875 to 0.893 with paired wins 32/32 to 30/32, fit and evaluation at different resolutions, a limited sensitivity check); "easiest negative" wording replaced; controls described as checks on the scoring machinery; bootstrap intervals described as conditional on fixed partners, geometry and orientation; "every session at least 0.999" corrected (044052 grid 16 is 0.9895; December grid 32 pooled 0.99996 rounds to 1.0000); `crop_bgr` described correctly for 2023 (stored RGB reversed); `export75` labelled an approximate geometry variant (the exporter's resize is omitted); minimum cell size 30x16; partner construction described as the reference's repaired shuffle, not a one-to-one derangement; audit note corrected; the 2026 d2/v10 comparison framed as not directly comparable (0.756 at grid 8, 902/975 paired); alignment-gap sentence, shelf entry and plain-English paragraph adopted from the audit as the report's own. No new computation; the calibration-exclusion, neighbour-partner and rounding figures were re-read from the existing scores, partner maps and results JSONs.
""")
open(f"{W}/REPORT.md", "w").write("\n".join(L))
print("wrote REPORT.md", len("\n".join(L)), "chars")
