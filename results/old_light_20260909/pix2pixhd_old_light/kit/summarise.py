#!/usr/bin/env python3
"""Print the Old Light numbers as markdown tables from the pulled box_results and ci_summary.json (the development machine side).
Usage: python3 summarise.py <box_results dir> <ci_summary.json>"""
import json, os, sys
R, CI = sys.argv[1], json.load(open(sys.argv[2]))


def ci(key, sub):
    v = CI.get(key, {}).get(sub)
    if not v: return "n/a"
    if "auroc" in v: return f"{v['auroc']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}] (n={v['n']}, wins {v['paired_wins']}/{v['n']})"
    return f"{v['mean']:.2f} [{v['ci95'][0]:.2f}, {v['ci95'][1]:.2f}]"


for track in ("2024", "2023"):
    root = os.path.join(R, "results", track)
    if not os.path.isdir(root): continue
    runs = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and not d.startswith(("baselines", "d2025")))
    print(f"\n## Track {track}\n")
    for TS, sub in (("tails (last tenth of every training session)", "latest"), ("whole held-out session", "latest_held")):
        bts = "test" if sub == "latest" else "heldsession"
        print(f"### {TS}\n")
        print("| model / baseline | PSNR dB [95% CI] | SSIM [95% CI] | G-verifier residual corr AUROC [CI] | G full corr AUROC | D capture-swap AUROC full [CI] | D emission-swap AUROC full [CI] | D capture-swap crop512 |")
        print("|---|---|---|---|---|---|---|---|")
        for run in runs:
            k = f"results/{track}/{run}/{sub}"
            print(f"| {run} | {ci(k + '/fidelity', 'psnr')} | {ci(k + '/fidelity', 'ssim')} | {ci(k + '/g_verifier', 'residual_corr')} | {ci(k + '/g_verifier', 'full_corr')} | {ci(k + '/d_verifier', 'full_capture_swap')} | {ci(k + '/d_verifier', 'full_emission_swap')} | {ci(k + '/d_verifier', 'crop512_capture_swap')} |")
        for b in ("emission", "prev_real", "mean_train"):
            k = f"results/{track}/baselines_{bts}/baseline_{b}"
            print(f"| baseline: {b} | {ci(k, 'psnr')} | {ci(k, 'ssim')} | | | | | |")
        if track == "2024":
            for act in ("none", "lrelu"):
                k = f"results/{track}/d2025_{act}/{sub}/d_verifier"
                if k in CI: print(f"| Jan 2025 D, final act {act} (comparison only) | | | | | {ci(k, 'full_capture_swap')} | {ci(k, 'full_emission_swap')} | {ci(k, 'crop512_capture_swap')} |")
        ck = f"results/{track}/coupling_{bts}"
        if ck in CI:
            print(f"\nTrain-free coupling statistic, matched vs within-session mismatched AUROC [95% CI]: " + "; ".join(f"grid {g}: {ci(ck, g)}" for g in ("4", "8", "16", "32", "64")))
        print()
