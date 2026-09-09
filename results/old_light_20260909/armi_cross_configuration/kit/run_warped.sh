#!/bin/bash
# run_warped.sh: variant (b), alignment-normalised C for the old sessions (recording warped by H into the emission frame),
# then the frozen evaluator on the three ARM-I arms with that cache. Waits for the main results marker.
set -u
export OMP_NUM_THREADS=4
FS=${XCFG_FS:?set XCFG_FS to the working directory for caches, checkpoints, results and logs}; DATA=${XCFG_DATA:?set XCFG_DATA to the directory holding the downloaded 2024 and 2023 archives}; KIT=${XCFG_KIT:-$(cd "$(dirname "$0")/src" && pwd)}; CACHE=$FS/cache; WC=$FS/cache_warped; LEAN=${XCFG_LEAN:?set XCFG_LEAN to the root of the 2026 preprocessed-row cache, the directory that contains 96x112/ (the loaders append the size)}
RES=$FS/results; LOG=$FS/logs/warped.log; cd "$KIT"
say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
for i in $(seq 1 360); do [ -f "$RES/.done" ] && break; sleep 20; done
OLD="20241219_044052,20241219_044529,20241219_050046,20241219_050648,20241219_051150,20241219_051629,20241219_052040,1680410249,1680410569,1680412337,1681945334,1682013847,1682014432,1682712156,1682718815"
say "warped precache start"
OMP_NUM_THREADS=2 python3 precache_warped.py --src-cache "$CACHE" --dst-cache "$WC" --h-dir "${XCFG_H:-$(dirname "$KIT")/H}" --old-root "$DATA" --sessions "$OLD" --workers 16 > "$FS/logs/precache_warped.log" 2>&1 || { say "warped precache FAILED"; tail -5 "$FS/logs/precache_warped.log"; exit 1; }
say "warped precache done: $(tail -1 $FS/logs/precache_warped.log)"
for ARM in armi_2026_s20260908 armi_2026_s20260907 armi_2024six_s20260908; do
  CUDA_VISIBLE_DEVICES=0 python3 eval_xcfg.py --ckpt "$FS/runs/$ARM/latest.pt" --cache-dir "$WC" --c-cache-fallback "$LEAN" --old-root "$DATA" --sessions "$OLD" --pairing-check \
    $( [ "$ARM" = armi_2026_s20260908 ] && echo "--dump-examples $RES/examples_warped_$ARM.npz --n-examples 3" ) \
    --out "$RES/$ARM.warped.eval.json" --save-raw "$RES/$ARM.warped.raw" > "$FS/logs/warped_eval_$ARM.log" 2>&1 || say "warped eval failed for $ARM"
  say "warped eval done $ARM: $(tail -1 $FS/logs/warped_eval_$ARM.log | cut -c1-250)"
done
say "WARPED DONE"; touch "$RES/.warped_done"
