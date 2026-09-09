#!/bin/bash
# run_controls.sh: Astra's simple-baseline and shortcut controls on the 2024 sessions for the two 2026-trained ARM-I seeds (saved inputs, forward passes only).
set -u; export OMP_NUM_THREADS=4
FS=${XCFG_FS:?set XCFG_FS to the working directory for caches, checkpoints, results and logs}; KIT=${XCFG_KIT:-$(cd "$(dirname "$0")/src" && pwd)}; LEAN=${XCFG_LEAN:?set XCFG_LEAN to the root of the 2026 preprocessed-row cache, the directory that contains 96x112/ (the loaders append the size)}; RES=$FS/results; LOG=$FS/logs/controls.log; cd "$KIT"
say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
for ARM in armi_2026_s20260908 armi_2026_s20260907; do
  say "controls start $ARM"
  CUDA_VISIBLE_DEVICES=0 python3 eval_controls.py --ckpt "$FS/runs/$ARM/latest.pt" --cache-dir "$FS/cache" --c-cache-fallback "$LEAN" --perlin-dir "${XCFG_PERLIN:-$(dirname "$KIT")/perlin}" \
    --out "$RES/$ARM.controls2024.json" --save-raw "$RES/$ARM.controls2024" > "$FS/logs/controls_$ARM.log" 2>&1 || say "controls failed $ARM"
  say "controls done $ARM: $(tail -1 $FS/logs/controls_$ARM.log | cut -c1-400)"
done
say "CONTROLS DONE"; touch "$RES/.controls_done"
