#!/bin/bash
# Evaluations that need no trained model, run while training proceeds: baselines and the coupling statistic on both test sets of both
# tracks (CPU), and the January 2025 discriminator's two reconstructions on the 2024 test sets (GPU, light). Log: $FS/logs/pretrain_evals.log
set -uo pipefail
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
K=${OL_KIT:-$(cd "$(dirname "$0")" && pwd)}; L=${OL_LOCAL:?set OL_LOCAL to a local work area for the raw downloads, the pairs and the pix2pixHD checkout}; FS=${OL_FS:?set OL_FS to the output directory for checkpoints, results and logs}
for track in 2024 2023; do
  P=$L/pairs$track; R=$FS/results/$track; mkdir -p $R
  for TS in test heldsession; do
    python3 $K/eval_baselines.py --test_a $P/${TS}_A --test_b $P/${TS}_B --train_b $P/train_B --out $R/baselines_$TS/metrics.json --procs 8; echo "$(date -u +%T) baselines $track $TS rc=$?"
    python3 $K/coupling_stat.py --test_a $P/${TS}_A --test_b $P/${TS}_B --out $R/coupling_$TS.json --procs 8; echo "$(date -u +%T) coupling $track $TS rc=$?"
  done
done
cd $L/pix2pixHD; cp -f $K/eval_d_verifier_v3.py .
for act in none lrelu; do for TS in test heldsession; do
  python3 eval_d_verifier_v3.py --name d2025_$act --d_path $FS/init2025/latest_net_D.pth --final_kernel 1 --final_act $act --pairs $L/pairs2024 --test $TS --ckpt $FS/checkpoints --results $FS/results/2024 --gpu 0 2>&1 | tail -n 3; echo "$(date -u +%T) d2025_$act $TS rc=$?"
done; done
echo "$(date -u +%T) PRETRAIN EVALS DONE"
