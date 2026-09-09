#!/bin/bash
# Old Light evaluation driver for one run: bash run_evals.sh <run> <track> <g_size e.g. 512x288> [gpu]
# Generates on the tail test set and the whole held-out session (eval_p2p.py from the kit), then G verifier, baselines, D verifier,
# coupling statistic and contact sheets for both. Results under $FS/results/<track>/...
set -uo pipefail
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
K=${OL_KIT:-$(cd "$(dirname "$0")" && pwd)}; L=${OL_LOCAL:?set OL_LOCAL to a local work area for the raw downloads, the pairs and the pix2pixHD checkout}; FS=${OL_FS:?set OL_FS to the output directory for checkpoints, results and logs}
run=$1; track=$2; gsize=$3; gpu=${4:-0}; mode=${5:-crop}
if [ $mode = full ] || [ $mode = mean ]; then GEN="--resize_or_crop scale_width --loadSize 1024"; if [ $track = 2024 ]; then SZ=1024x576; else SZ=1024x640; fi; BSZ="--size $SZ"; DRS="--resize $SZ"; BSUF="_$SZ"; else GEN=""; BSZ=""; DRS=""; BSUF=""; fi
if [ $mode = mean ]; then export P2P_MEANPRIOR=1; MP="--meanprior $L/pairs$track/mean_train_B.png"; else MP=""; fi
P=$L/pairs$track; PH=$L/pairs${track}_held; R=$FS/results/$track; CK=$FS/checkpoints
mkdir -p $R $PH $FS/logs
if [ $track = 2024 ]; then SHEET="--swap_rb_b"; else SHEET="--swap_rb_a"; fi   # true-colour display: 2024 recordings are stored BGR; 2023 emissions were displayed BGR
# the held-session dataroot: the same training dirs, test_* = the whole held-out session
for d in train_A train_B; do [ -e $PH/$d ] || ln -s $P/$d $PH/$d; done
[ -e $PH/test_A ] || ln -s $P/heldsession_A $PH/test_A; [ -e $PH/test_B ] || ln -s $P/heldsession_B $PH/test_B
cd $L/pix2pixHD; cp -f $K/eval_p2p.py $K/eval_d_verifier_v3.py .
log=$FS/logs/eval_${run}.log; echo "== $(date -u +%T) eval $run ($track) gpu $gpu" | tee -a $log
P2P_CKPT=$CK P2P_RESULTS=$R P2P_DATAROOT=$P P2P_GPU=$gpu P2P_METRIC_PROCS=8 python3 eval_p2p.py --name $run --which_epoch latest $GEN >> $log 2>&1; echo "eval_p2p tails rc=$?" | tee -a $log
P2P_CKPT=$CK P2P_RESULTS=$R P2P_DATAROOT=$PH P2P_GPU=$gpu P2P_METRIC_PROCS=8 P2P_OUT_SUFFIX=_held python3 eval_p2p.py --name $run --which_epoch latest $GEN >> $log 2>&1; echo "eval_p2p held rc=$?" | tee -a $log
for t in latest latest_held; do
  if [ $t = latest ]; then TA=$P/test_A; TB=$P/test_B; TS=test; else TA=$P/heldsession_A; TB=$P/heldsession_B; TS=heldsession; fi
  python3 $K/eval_g_verifier.py --fake $R/$run/$t/fake --real $TB --train_b $P/train_B --out $R/$run/$t/g_verifier.json --size $gsize >> $log 2>&1; echo "g_verifier $t rc=$?" | tee -a $log
  python3 $K/eval_g_verifier.py --fake $R/$run/$t/fake --real $TB --train_b $P/train_B --out $R/$run/$t/g_verifier.json --size $gsize --color >> $log 2>&1; echo "g_verifier colour $t rc=$?" | tee -a $log
  python3 eval_d_verifier_v3.py --name $run --pairs $P --test $TS --ckpt $CK --results $R --gpu $gpu $DRS $MP >> $log 2>&1; echo "d_verifier $t rc=$?" | tee -a $log
  [ -f $R/baselines_$TS$BSUF/metrics.json ] || { python3 $K/eval_baselines.py --test_a $TA --test_b $TB --train_b $P/train_B --out $R/baselines_$TS$BSUF/metrics.json $BSZ >> $log 2>&1; echo "baselines $TS$BSUF rc=$?" | tee -a $log; }
  [ -f $R/coupling_$TS.json ] || { python3 $K/coupling_stat.py --test_a $TA --test_b $TB --out $R/coupling_$TS.json >> $log 2>&1; echo "coupling $TS rc=$?" | tee -a $log; }
  [ -f $R/coupling_${TS}_rbswap.json ] || { python3 $K/coupling_stat.py --test_a $TA --test_b $TB --out $R/coupling_${TS}_rbswap.json --swap_emission_rb >> $log 2>&1; echo "coupling rbswap $TS rc=$?" | tee -a $log; }
  python3 $K/contact_sheet.py --test_a $TA --test_b $TB --fake $R/$run/$t/fake --out $R/$run/$t/contact_sheet.png --rows 8 $SHEET --title "Old Light $track, run $run, $TS held-out: emission | real | generated (true colour)" >> $log 2>&1; echo "sheet $t rc=$?" | tee -a $log
done
echo "== $(date -u +%T) eval $run done" | tee -a $log
