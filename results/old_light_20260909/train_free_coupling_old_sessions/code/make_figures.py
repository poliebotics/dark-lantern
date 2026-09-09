#!/usr/bin/env python3
"""Figures for REPORT.md.
  figures/auroc_bars_2023.png, figures/auroc_bars_2024.png: per-session AUROC by grid, two panels (full frame, crop),
      bootstrap 95 percent CI whiskers, hairline at 0.5; grids as an ordinal single-hue ramp (dataviz reference palette,
      steps 250-650, validated with scripts/validate_palette.js --ordinal).
  figures/contact_sheet_crops.png: the crop used, on three sessions: recording with the quad, temporal std map with the
      quad, the warped crop, the oriented emission, and the grid-16 per-cell temporal correlation map (crop).
"""
import json, os, sys, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import cv2

W = os.environ.get("COUPLING_PKG", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); RES = f"{W}/results"; FIG = f"{W}/figures"; os.makedirs(FIG, exist_ok=True)
PREV = os.environ.get("COUPLING_PREVIEWS", "coupling_previews")
RAMP = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]  # ordinal blue, steps 250..650
INK, INK2, MUTED, GRID, BASE, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
GRIDS = ["4", "8", "16", "32", "64"]
plt.rcParams.update({"font.family": "sans-serif", "font.size": 9, "axes.edgecolor": BASE, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF})


def short(s):
    return s.replace("20241219_", "") if s.startswith("2024") else s


def bars(era):
    r = json.load(open(f"{RES}/{era}_results.json"))
    sessions = list(r["sessions"].keys()) + ["pooled"]
    ns = {s: r["sessions"][s]["n"] for s in r["sessions"]}
    panels = [("full", "Full recording frame"), ("crop", "Projected-region crop (emission-blind quad)")]
    if "export75" in r["grids"]["8"]:
        panels.append(("export75", "January 2025 exporter geometry: centre 75% of height, full width (RGB-corrected)"))
    fig, axes = plt.subplots(len(panels), 1, figsize=(max(9, 1.05 * len(sessions) + 2), 3.2 * len(panels)), sharex=True)
    for ax, (variant, title) in zip(axes, panels):
        x = np.arange(len(sessions)); wbar = 0.15
        for gi, g in enumerate(GRIDS):
            vals = [r["grids"][g][variant][s]["auroc"] for s in sessions]
            lo = [r["grids"][g][variant][s]["auroc_ci95"][0] for s in sessions]; hi = [r["grids"][g][variant][s]["auroc_ci95"][1] for s in sessions]
            xs = x + (gi - 2) * (wbar + 0.012)
            ax.bar(xs, vals, width=wbar, color=RAMP[gi], edgecolor=SURF, linewidth=0.8, label=f"grid {g}")
            ax.errorbar(xs, vals, yerr=[np.array(vals) - np.array(lo), np.array(hi) - np.array(vals)], fmt="none", ecolor=INK2, elinewidth=0.8, capsize=0)
        ax.axhline(0.5, color=MUTED, linewidth=1, zorder=0)
        ax.set_ylim(0, 1.02); ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0]); ax.yaxis.grid(True, color=GRID, linewidth=0.8); ax.set_axisbelow(True)
        ax.set_ylabel("AUROC"); ax.set_title(title, loc="left", color=INK, fontsize=10)
        ax.axvline(len(sessions) - 1.5, color=BASE, linewidth=0.8)
    axes[-1].set_xticks(np.arange(len(sessions))); axes[-1].set_xticklabels([f"{short(s)}\n(n={ns[s]})" if s != "pooled" else f"pooled\n(n={r['grids']['8']['crop']['pooled']['n_pairs']})" for s in sessions], fontsize=8)
    axes[0].legend(handles=[Patch(color=RAMP[i], label=f"grid {g}") for i, g in enumerate(GRIDS)], ncol=5, frameon=False, loc="lower right", bbox_to_anchor=(1, 1.0), fontsize=8)
    fig.suptitle(f"Train-free coupling statistic, {era} Truth Beam sessions\nAUROC of matched vs one random same-session mismatch; whiskers: bootstrap 95% CI (1000 frame resamples); line: 0.5",
                 x=0.01, ha="left", fontsize=9, color=INK2, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.96)); out = f"{FIG}/auroc_bars_{era}.png"; fig.savefig(out, dpi=160); plt.close(fig)
    print("wrote", out)


def contact(sessions_eras):
    maps = {}
    for era in ("2023", "2024"):
        p = f"{RES}/{era}_cellcorr_maps.npz"
        if os.path.exists(p):
            z = np.load(p); maps.update({k: z[k] for k in z.files})
    fig, axes = plt.subplots(len(sessions_eras), 5, figsize=(15, 2.9 * len(sessions_eras)))
    for row, (s, era) in enumerate(sessions_eras):
        g = json.load(open(f"{W}/geometry/{s}.geometry.json"))
        r = json.load(open(f"{RES}/{era}_results.json"))["sessions"][s]
        k = min(3, g["n_pairs"] - 1)
        panels = [(cv2.cvtColor(cv2.imread(f"{PREV}/{s}_f{k:03d}_recording_quad.png"), cv2.COLOR_BGR2RGB), f"{short(s)}: recording, frame {k}, quad"),
                  (cv2.cvtColor(cv2.imread(f"{PREV}/{s}_stdmap_quad.png"), cv2.COLOR_BGR2RGB), "temporal std map, fitted quad"),
                  (cv2.cvtColor(cv2.imread(f"{PREV}/{s}_f{k:03d}_crop.png"), cv2.COLOR_BGR2RGB), "warped crop (projected region)"),
                  (cv2.cvtColor(cv2.imread(f"{PREV}/{s}_f{k:03d}_emission.png"), cv2.COLOR_BGR2RGB), f"emission, orientation {r['orientation']['chosen']} deg")]
        for col, (im, title) in enumerate(panels):
            ax = axes[row, col]
            if col == 0 and era == "2024":
                Hh, Ww = im.shape[:2]; top = int(round(Hh * (0.125))); bot = int(round(Hh * 0.875))
                cv2.rectangle(im, (0, top), (Ww - 1, bot), (237, 161, 0), 2)
                title = f"{short(s)}: frame {k}, quad (red), 75% band (yellow)"
            if col == 3 and r["orientation"]["chosen"] == 180:
                im = im[::-1, ::-1]
            ax.imshow(im); ax.set_title(title, fontsize=8.5, loc="left", color=INK); ax.axis("off")
        ax = axes[row, 4]; m = maps.get(f"{s}_crop")
        if m is not None:
            imh = ax.imshow(m, cmap="Blues", vmin=0, vmax=max(0.3, float(np.percentile(m, 99))))
            ax.set_title(f"grid-16 per-cell temporal corr (crop), mean {m.mean():.2f}", fontsize=8.5, loc="left", color=INK)
            cb = fig.colorbar(imh, ax=ax, fraction=0.046, pad=0.02); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=7, color=INK2)
        ax.set_xticks([]); ax.set_yticks([])
    fig.tight_layout(); out = f"{FIG}/contact_sheet_crops.png"; fig.savefig(out, dpi=130); plt.close(fig); print("wrote", out)


if __name__ == "__main__":
    for era in ("2023", "2024"):
        if os.path.exists(f"{RES}/{era}_results.json"):
            bars(era)
    sel = [tuple(a.split(":")) for a in sys.argv[1:]] or [("20241219_051150", "2024"), ("1680410249", "2023"), ("1682718815", "2023")]
    contact(sel)
