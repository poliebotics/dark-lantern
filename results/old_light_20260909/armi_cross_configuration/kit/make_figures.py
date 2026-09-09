#!/usr/bin/env python3
"""make_figures.py (BOSUN, 2026-09-09): figures for the ARM-I cross-configuration report from the pulled results.
  auroc_bars_<arm>.png      per-session pooled AUROC with row-bootstrap 95% CI whiskers, grouped by era (2026 / 2024 / 2023)
  residual_hist_<arm>.png   per-era histograms of the correct residual vs the per-row wrong-mean residual
  contact_sheet_<arm>.png   C (RGGB planes shown as RGB), E-correct and E-wrong for a few rows per era, as the model sees them
Palette: the dataviz reference instance, validated (eras: blue #2a78d6, aqua #1baf7a, yellow #eda100; conditions: blue, orange #eb6834).
Usage: make_figures.py --results DIR --arm NAME --out DIR
"""
import argparse, glob, json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ERA_COL = {"2026": "#2a78d6", "2024": "#1baf7a", "2023": "#eda100"}
COND_COL = {"correct": "#2a78d6", "wrong": "#eb6834"}
TXT, TXT2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
ORDER_2026 = ["d2", "v10", "august"]


def style(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID); ax.spines[s].set_linewidth(1)
    ax.tick_params(colors=TXT2, labelsize=9, length=0)
    ax.yaxis.grid(True, color=GRID, linewidth=1); ax.set_axisbelow(True)


def short(sid):
    if sid.startswith("20241219_"): return sid[9:]
    return sid


def auroc_bars(res, arm, out):
    sess = res["sessions"]
    order = [s for s in ORDER_2026 if s in sess] + sorted([s for s, c in sess.items() if c["era"] == "2024"]) + sorted([s for s, c in sess.items() if c["era"] == "2023"])
    vals = [sess[s]["auroc"]["correct_vs_wrong_avg"] for s in order]
    lo = [sess[s]["row_bootstrap"]["auroc_ci95"][0] for s in order]; hi = [sess[s]["row_bootstrap"]["auroc_ci95"][1] for s in order]
    eras = [sess[s]["era"] for s in order]; ns = [sess[s]["n_rows"] for s in order]
    fig, ax = plt.subplots(figsize=(max(7, 0.62 * len(order) + 2.5), 4.8), dpi=160); fig.patch.set_facecolor(SURF); style(ax)
    x = np.arange(len(order))
    for i, s in enumerate(order):
        ax.bar(x[i], vals[i], width=0.62, color=ERA_COL[eras[i]], edgecolor="none", zorder=3)
        ax.plot([x[i], x[i]], [lo[i], hi[i]], color=TXT, linewidth=1.2, zorder=4)
        ax.text(x[i], min(1.02, hi[i] + 0.012), f"{vals[i]:.3f}" if vals[i] < 0.9995 else "1.000", ha="center", va="bottom", fontsize=7.5, color=TXT)
    ax.axhline(0.5, color=TXT2, linewidth=1, zorder=2)
    ax.text(len(order) - 0.5, 0.505, "chance 0.5", ha="right", va="bottom", fontsize=8, color=TXT2)
    ax.set_xticks(x); ax.set_xticklabels([f"{short(s)}\nn={n}" for s, n in zip(order, ns)], fontsize=7.5, color=TXT2)
    ax.set_ylim(0.4, 1.06); ax.set_yticks([0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]); ax.set_ylabel("pooled AUROC, correct vs wrong-mean residual", color=TXT2, fontsize=9)
    ax.set_title(f"ARM-I ({arm}): pooled AUROC per session\nwhiskers: 95% row-bootstrap CI (1,000 resamples); bars coloured by era", fontsize=10, color=TXT, loc="left")
    from matplotlib.patches import Patch
    labels = {"2026": "2026 Truth Beam (trained configuration)", "2024": "December 2024 (unseen rig)", "2023": "April 2023 (unseen rig)"}
    tr = res.get("train_args", {}).get("sessions") or ""
    if tr.startswith("20241219"):
        labels = {"2026": "2026 Truth Beam (unseen configuration)", "2024": "December 2024 (trained; 050046 held out)", "2023": "April 2023 (unseen rig)"}
    elif "20241219" in tr and "1680412337" in tr:
        labels = {"2026": "2026 Truth Beam (trained; eval blocks held out)", "2024": "December 2024 (trained; 050046 held out)", "2023": "April 2023 aligned (trained; trailer held out)"}
    ax.legend(handles=[Patch(color=ERA_COL[e], label=labels[e]) for e in ("2026", "2024", "2023") if e in eras], loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, fontsize=8, frameon=False, labelcolor=TXT2)
    fig.tight_layout(); fig.savefig(out, facecolor=SURF, bbox_inches="tight"); plt.close(fig)


def residual_hist(res, raw_dir, arm, out):
    eras = ["2026", "2024", "2023"]
    data = {e: ([], []) for e in eras}
    for sid, c in res["sessions"].items():
        if sid == "august": continue
        f = os.path.join(raw_dir, os.path.basename(c["raw_scores"]))
        if not os.path.isfile(f): continue
        z = np.load(f); cor = z["correct"]; W = np.stack([z[f"wrong_{o:+d}"] for o in (-2, 2, -15, 15, 30)], 1); wm = np.nanmean(W, 1)
        fin = np.isfinite(cor) & np.isfinite(wm); data[c["era"]][0].append(cor[fin]); data[c["era"]][1].append(wm[fin])
    eras = [e for e in eras if data[e][0]]
    fig, axes = plt.subplots(1, len(eras), figsize=(4.2 * len(eras), 3.6), dpi=160, sharey=False); fig.patch.set_facecolor(SURF)
    axes = np.atleast_1d(axes)
    for ax, e in zip(axes, eras):
        style(ax); cor = np.concatenate(data[e][0]); wm = np.concatenate(data[e][1])
        lo = min(cor.min(), wm.min()); hi = max(cor.max(), wm.max()); bins = np.linspace(lo, hi, 41)
        ax.hist(wm, bins=bins, color=COND_COL["wrong"], alpha=0.8, label=f"wrong emission, per-row mean of 5 offsets (n={wm.size})", edgecolor=SURF, linewidth=0.6)
        ax.hist(cor, bins=bins, color=COND_COL["correct"], alpha=0.7, label=f"correct emission (n={cor.size})", edgecolor=SURF, linewidth=0.6)
        au = res["eras"].get(e, {}).get("auroc")
        ax.set_title(f"{e}: AUROC {au:.3f}" if au is not None else e, fontsize=10, color=TXT, loc="left")
        ax.set_xlabel("residual (mean squared noise-prediction error at t=150)", fontsize=8, color=TXT2); ax.set_ylabel("rows", fontsize=8, color=TXT2)
        ax.legend(fontsize=7, frameon=False, labelcolor=TXT2, loc="upper right")
    fig.suptitle(f"ARM-I ({arm}): residual under the correct vs a wrong emission, by era", fontsize=10, color=TXT, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(out, facecolor=SURF); plt.close(fig)


def to_rgb(C):
    """(4,H,W) RGGB planes in [0,1] -> (H,W,3) display image, per-image percentile stretch so a dark sensor frame is visible."""
    img = np.stack([C[0], 0.5 * (C[1] + C[2]), C[3]], -1)
    lo, hi = np.percentile(img, 1), np.percentile(img, 99.5)
    return np.clip((img - lo) / max(hi - lo, 1e-6), 0, 1)


def contact_sheet(ex_path, arm, out, per_session=1, pick=("d2", "v10", "august", "20241219_044052", "20241219_050046", "1680412337", "1682718815")):
    z = np.load(ex_path)
    keys = sorted({k.rsplit("/", 2)[0] + "/" + k.rsplit("/", 2)[1] for k in z.files})
    by_sid = {}
    for k in keys:
        sid, r = k.split("/"); by_sid.setdefault(sid, []).append(int(r))
    order = [s for s in ORDER_2026 if s in by_sid] + sorted([s for s in by_sid if s.startswith("2024")]) + sorted([s for s in by_sid if s not in ORDER_2026 and not s.startswith("2024")])
    if pick:
        order = [s for s in pick if s in by_sid]
    rows = [(s, r) for s in order for r in sorted(by_sid[s])[:per_session]]
    fig, axes = plt.subplots(len(rows), 3, figsize=(7.2, 2.15 * len(rows) + 0.5), dpi=150); fig.patch.set_facecolor(SURF)
    axes = np.atleast_2d(axes)
    for i, (s, r) in enumerate(rows):
        C = z[f"{s}/{r}/C"]; Ec = z[f"{s}/{r}/E_correct"]; Ew = z[f"{s}/{r}/E_wrong"]; rw = int(z[f"{s}/{r}/wrong_row"])
        era = "2026" if s in ORDER_2026 else ("2024" if s.startswith("2024") else "2023")
        for j, (img, title) in enumerate([(to_rgb(C), f"C  {era} {short(s)} row {r}"), (np.clip(Ec.transpose(1, 2, 0), 0, 1), f"E correct (row {r})"), (np.clip(Ew.transpose(1, 2, 0), 0, 1), f"E wrong (row {rw})")]):
            ax = axes[i, j]; ax.imshow(img, interpolation="nearest"); ax.set_title(title, fontsize=7.5, color=TXT, loc="left", pad=3); ax.axis("off")
    fig.suptitle(f"ARM-I inputs at the 96x112 frame grid ({arm})\ncamera frame C (RGGB planes shown as RGB, per-image stretch), the correct emission, a wrong emission of the same session", fontsize=8, color=TXT, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.55 / (2.15 * len(rows) + 0.5))); fig.savefig(out, facecolor=SURF); plt.close(fig)


def monitor_curves(hist_path, arm, out):
    """In-loop quick_eval trajectory (offset +2 only, per-row seeds, small row sets): paired fraction and delta per monitored
    session against the training step. A learning-curve view, not the frozen statistic."""
    steps, series = [], {}
    for l in open(hist_path):
        d = json.loads(l)
        if "eval" not in d: continue
        steps.append(d["step"])
        for sid, v in d["eval"].items():
            series.setdefault(sid, ([], []))[0].append(v["paired"]); series[sid][1].append(v["delta"])
    if not steps: return
    def col(sid):
        return ERA_COL["2026"] if sid in ORDER_2026 else (ERA_COL["2024"] if sid.startswith("2024") else ERA_COL["2023"])
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.6), dpi=160); fig.patch.set_facecolor(SURF)
    styles = {}
    for k, sid in enumerate(series):
        same_era = [t for t in series if col(t) == col(sid)]
        styles[sid] = ["-", "--", ":", "-."][same_era.index(sid) % 4]
    for ax, (idx, ylabel) in zip(axes, [(0, "paired fraction (correct residual lower), quick_eval"), (1, "delta = wrong - correct residual, quick_eval")]):
        style(ax)
        for sid, (pf, dl) in series.items():
            ax.plot(steps, [pf, dl][idx], color=col(sid), linestyle=styles[sid], linewidth=2, marker="o", markersize=4, label=f"{short(sid)} (n={len(pf) and 0 or 0})" if False else short(sid))
        ax.set_xlabel("training step", fontsize=8, color=TXT2); ax.set_ylabel(ylabel, fontsize=8, color=TXT2)
        if idx == 0: ax.axhline(0.5, color=TXT2, linewidth=1); ax.set_ylim(0.2, 1.05)
        else: ax.axhline(0.0, color=TXT2, linewidth=1)
    axes[0].legend(fontsize=7, frameon=False, labelcolor=TXT2, ncol=2, loc="lower right")
    fig.suptitle(f"{arm}: in-loop monitor of held-out and unseen sessions during training (quick_eval: offset +2, 10 to 35 rows; not the frozen statistic)", fontsize=9, color=TXT, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(out, facecolor=SURF); plt.close(fig)


def trajectory(results_dir, arm, out):
    """Frozen statistic at the saved checkpoints (steps 5k..20k and the final 24k): pooled AUROC and paired fraction per era."""
    pts = []
    for f in glob.glob(os.path.join(results_dir, f"traj_{arm}_*.eval.json")) + [os.path.join(results_dir, f"{arm}.eval.json")]:
        if not os.path.isfile(f): continue
        d = json.load(open(f)); pts.append((int(d["checkpoint_step"]), d))
    pts.sort()
    if len(pts) < 2: return
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.6), dpi=160); fig.patch.set_facecolor(SURF)
    for ax, key, ylabel in zip(axes, ("auroc", "paired"), ("pooled AUROC (frozen statistic)", "paired fraction (frozen statistic)")):
        style(ax)
        for era in ("2026", "2024", "2023"):
            xs = [st for st, d in pts if era in d["eras"] or (era == "2026" and "d2" in d["sessions"])]
            ys = []
            for st, d in pts:
                if era in d["eras"]: ys.append(d["eras"][era][key])
                elif era == "2026" and "d2" in d["sessions"]: ys.append(d["sessions"]["d2"]["auroc"]["correct_vs_wrong_avg"] if key == "auroc" else d["sessions"]["d2"]["paired_fraction_correct_lower"])
            if xs: ax.plot(xs, ys, color=ERA_COL[era], linewidth=2, marker="o", markersize=5, label={"2026": "2026 d2 eval blocks", "2024": "2024, 7 sessions (unseen rig)", "2023": "2023, 8 sessions (unseen rig)"}[era])
        ax.axhline(0.5, color=TXT2, linewidth=1); ax.set_ylim(0.4, 1.05); ax.set_xlabel("training step (checkpoint)", fontsize=8, color=TXT2); ax.set_ylabel(ylabel, fontsize=8, color=TXT2)
    axes[0].legend(fontsize=7, frameon=False, labelcolor=TXT2, loc="center right")
    fig.suptitle(f"{arm}: cross-configuration separation along training, every checkpoint scored with the frozen statistic", fontsize=9, color=TXT, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(out, facecolor=SURF); plt.close(fig)


def fewshot_curve(results_dir, out, base_2024=None, base_2023=None):
    """Few-shot adaptation: AUROC and paired fraction on the held-out session of the new rig against the number of that rig's
    sessions used for the brief fine-tune (k = 0 is the 2026-trained model as evaluated in the first run), with 95 % row-bootstrap
    whiskers, and the d2 retention of each fine-tuned model as a dotted line."""
    import re
    series = {}
    for f in glob.glob(os.path.join(results_dir, "fs_*.eval.json")):
        m = re.match(r"fs_(2024|2023w)_k(\d+)(\.d2)?\.eval\.json", os.path.basename(f))
        if not m: continue
        rig, k, isd2 = m.group(1), int(m.group(2)), bool(m.group(3))
        d = json.load(open(f)); sid = list(d["sessions"])[0]; c = d["sessions"][sid]
        series.setdefault(rig, {}).setdefault(k, {})["d2" if isd2 else "held"] = (c["auroc"]["correct_vs_wrong_avg"], c["row_bootstrap"]["auroc_ci95"], c["paired_fraction_correct_lower"], c["row_bootstrap"]["paired_ci95"])
    if base_2024: series.setdefault("2024", {}).setdefault(0, {})["held"] = base_2024
    if base_2023: series.setdefault("2023w", {}).setdefault(0, {})["held"] = base_2023
    if not series: return
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8), dpi=160); fig.patch.set_facecolor(SURF)
    lab = {"2024": "2024 rig, held-out 050046 (raw layout)", "2023w": "2023 rig, held-out trailer 1682718815 (aligned)"}
    for ax, idx, ylabel in zip(axes, (0, 2), ("AUROC on the held-out session", "paired fraction on the held-out session")):
        style(ax)
        for rig, col in (("2024", ERA_COL["2024"]), ("2023w", ERA_COL["2023"])):
            if rig not in series: continue
            ks = sorted(series[rig]); ys = [series[rig][k]["held"][idx] for k in ks if "held" in series[rig][k]]; ks2 = [k for k in ks if "held" in series[rig][k]]
            los = [series[rig][k]["held"][idx + 1][0] for k in ks2]; his = [series[rig][k]["held"][idx + 1][1] for k in ks2]
            ax.plot(ks2, ys, color=col, linewidth=2, marker="o", markersize=6, label=lab[rig], zorder=3)
            for k, lo, hi in zip(ks2, los, his): ax.plot([k, k], [lo, hi], color=TXT, linewidth=1, zorder=4)
            d2k = [k for k in ks if "d2" in series[rig][k]]
            if d2k and idx == 0: ax.plot(d2k, [series[rig][k]["d2"][0] for k in d2k], color=col, linewidth=1.5, linestyle=":", marker="s", markersize=4, label=lab[rig].split(",")[0] + ": d2 retention (2026)")
        ax.axhline(0.5, color=TXT2, linewidth=1); ax.set_ylim(0.4, 1.05); ax.set_xlabel("sessions of the new rig used for the brief fine-tune (k)", fontsize=8, color=TXT2); ax.set_ylabel(ylabel, fontsize=8, color=TXT2)
        ax.set_xticks([0, 1, 2, 4, 6, 7])
    axes[0].legend(fontsize=7, frameon=False, labelcolor=TXT2, loc="lower right")
    fig.suptitle("Few-shot adaptation from the 2026-trained ARM-I: 2,000 steps at lr 5e-5 on k sessions of the new rig; whiskers 95 % row bootstrap", fontsize=9, color=TXT, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(out, facecolor=SURF); plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--results", required=True); ap.add_argument("--arm", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--examples", default="")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    if a.arm == "fewshot":
        def base(arm, sid, warped=False):
            f = os.path.join(a.results, f"{arm}{'.warped' if warped else ''}.eval.json")
            if not os.path.isfile(f): return None
            c = json.load(open(f))["sessions"][sid]; return (c["auroc"]["correct_vs_wrong_avg"], c["row_bootstrap"]["auroc_ci95"], c["paired_fraction_correct_lower"], c["row_bootstrap"]["paired_ci95"])
        fewshot_curve(a.results, os.path.join(a.out, "fewshot_curve.png"), base("armi_2026_s20260908", "20241219_050046"), base("armi_2026_s20260908", "1682718815", warped=True))
        print("few-shot figure written"); raise SystemExit
    res = json.load(open(os.path.join(a.results, f"{a.arm}.eval.json")))
    auroc_bars(res, a.arm, os.path.join(a.out, f"auroc_bars_{a.arm}.png"))
    residual_hist(res, a.results, a.arm, os.path.join(a.out, f"residual_hist_{a.arm}.png"))
    ex = a.examples or (glob.glob(os.path.join(a.results, f"examples_{a.arm}.npz")) or [""])[0]
    if ex and os.path.isfile(ex):
        contact_sheet(ex, a.arm, os.path.join(a.out, f"contact_sheet_{a.arm}.png"))
    trajectory(a.results, a.arm, os.path.join(a.out, f"trajectory_{a.arm}.png"))
    wex = os.path.join(a.results, f"examples_warped_{a.arm}.npz")
    if os.path.isfile(wex):
        contact_sheet(wex, a.arm + " (variant b: recording warped into the emission frame by H)", os.path.join(a.out, f"contact_sheet_warped_{a.arm}.png"), pick=("20241219_044052", "20241219_050046", "1680412337", "1682718815"))
    hist = os.path.join(os.path.dirname(a.results.rstrip("/")), "runs", a.arm, "history.jsonl")
    if os.path.isfile(hist):
        monitor_curves(hist, a.arm, os.path.join(a.out, f"monitor_curves_{a.arm}.png"))
    print("figures written to", a.out)
