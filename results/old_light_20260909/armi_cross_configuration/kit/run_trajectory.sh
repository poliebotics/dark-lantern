#!/bin/bash
# run_trajectory.sh: after the main run, score the intermediate checkpoints of the main ARM-I arm on the unseen sessions (exact
# protocol, every row) plus d2 at stride 10 as a coarse in-distribution reference, to show how cross-configuration separation
# moves with training. Waits for results/.done. Output: results/traj_<step>.eval.json
set -u
export OMP_NUM_THREADS=4
FS=${XCFG_FS:?set XCFG_FS to the working directory for caches, checkpoints, results and logs}; DATA=${XCFG_DATA:?set XCFG_DATA to the directory holding the downloaded 2024 and 2023 archives}; KIT=${XCFG_KIT:-$(cd "$(dirname "$0")/src" && pwd)}; CACHE=$FS/cache; LEAN=${XCFG_LEAN:?set XCFG_LEAN to the root of the 2026 preprocessed-row cache, the directory that contains 96x112/ (the loaders append the size)}
ARM=${1:-armi_2026_s20260908}; RUN=$FS/runs/$ARM; RES=$FS/results; LOG=$FS/logs/trajectory.log; cd "$KIT"
say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
for i in $(seq 1 360); do [ -f "$RES/.done" ] && break; sleep 20; done
[ -f "$RES/.done" ] || { say "main run not done after 2 h; abort"; exit 1; }
OLD="20241219_044052,20241219_044529,20241219_050046,20241219_050648,20241219_051150,20241219_051629,20241219_052040,1680410249,1680410569,1680412337,1681945334,1682013847,1682014432,1682712156,1682718815"
for ck in "$RUN"/step_*.pt; do
  step=$(basename "$ck" .pt | sed 's/step_0*//'); [ -f "$RES/traj_${ARM}_$step.eval.json" ] && continue
  say "trajectory eval $ARM step $step"
  CUDA_VISIBLE_DEVICES=0 python3 eval_xcfg.py --ckpt "$ck" --cache-dir "$CACHE" --c-cache-fallback "$LEAN" --old-root "$DATA" --sessions "d2,$OLD" --stride 1 \
     --out "$RES/traj_${ARM}_$step.eval.json" --save-raw "$RES/traj_${ARM}_$step.raw" > "$FS/logs/traj_${ARM}_$step.log" 2>&1 || say "trajectory eval failed at step $step"
done
say "TRAJECTORY DONE"; touch "$RES/.traj_done"
