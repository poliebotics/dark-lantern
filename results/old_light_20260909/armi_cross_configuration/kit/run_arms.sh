#!/bin/bash
# run_arms.sh (BOSUN, 2026-09-09): the ARM-I cross-configuration run on ONE A100. Waits for the verified downloads and the
# 2026 image-E precache, precaches the old sessions, runs the on-box self-test, then trains four arms concurrently on the one GPU
# with the published G0e recipe (width 16, 96x112, cond_drop 0, 24k steps, bs 8, lr 2e-4, warmup 200, cosine 24k, OMP 4), and
# evaluates each arm with eval_xcfg.py as soon as its training ends. Everything under the new FS directory only.
set -u
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
FS=${XCFG_FS:?set XCFG_FS to the working directory for caches, checkpoints, results and logs}; DATA=${XCFG_DATA:?set XCFG_DATA to the directory holding the downloaded 2024 and 2023 archives}; KIT=${XCFG_KIT:-$(cd "$(dirname "$0")/src" && pwd)}
CACHE=$FS/cache; LEAN=${XCFG_LEAN:?set XCFG_LEAN to the root of the 2026 preprocessed-row cache, the directory that contains 96x112/ (the loaders append the size)}; RUNS=$FS/runs; RES=$FS/results; LOG=$FS/logs/run_arms.log
mkdir -p "$RUNS" "$RES"; cd "$KIT"
say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
say "run_arms start on $(hostname)"
# 1. wait for the verified downloads (download.sh touches .verified) and the 2026 precache
for i in $(seq 1 240); do [ -f "$DATA/.verified" ] && break; sleep 15; done
[ -f "$DATA/.verified" ] || { say "downloads not verified after 60 min"; exit 1; }
say "downloads verified"
for i in $(seq 1 240); do grep -q "precache_xcfg done" "$FS/logs/precache_2026.log" 2>/dev/null && break; sleep 15; done
grep -q "precache_xcfg done" "$FS/logs/precache_2026.log" || { say "2026 precache not done after 60 min"; exit 1; }
say "2026 precache done: $(tail -1 $FS/logs/precache_2026.log)"
# 2. precache the old sessions (C and Ei for every row)
OLD24="20241219_044052,20241219_044529,20241219_050046,20241219_050648,20241219_051150,20241219_051629,20241219_052040"
OLD23="1680410249,1680410569,1680412337,1681945334,1682013847,1682014432,1682712156,1682718815"
OMP_NUM_THREADS=2 python3 precache_xcfg.py --cache-dir "$CACHE" --old-root "$DATA" --sessions "$OLD24,$OLD23" --workers 24 > "$FS/logs/precache_old.log" 2>&1 || { say "old precache failed"; tail -5 "$FS/logs/precache_old.log" | tee -a "$LOG"; exit 1; }
say "old precache done: $(tail -1 $FS/logs/precache_old.log)"
for d in "$CACHE"/96x112/*/; do echo "  $(basename $d): C $(ls $d | grep -c '^C_') Ei $(ls $d | grep -c '^Ei_')"; done | tee -a "$LOG"
# 3. self-test: 30 GPU steps with old-session monitors, then the evaluator on 6 rows of three sessions
ST=$RUNS/selftest; rm -rf "$ST"
python3 train_xcfg.py --arch armc --base-ch 16 --out-size 96,112 --seed 1 --cond-drop 0.0 --from-scratch --no-base-ckpt --emission-image \
  --sessions d2,v10,august --august-train-rows 600 --monitor-sessions 20241219_050046,1682718815 --old-root "$DATA" --cache-dir "$CACHE" --c-cache-fallback "$LEAN" \
  --out "$ST" --max-steps 30 --bs 8 --accum 1 --lr 2e-4 --warmup 5 --cosine-horizon 30 --ckpt-every 30 --eval-every 30 --prefetch 8 > "$ST.log" 2>&1 \
  && python3 eval_xcfg.py --ckpt "$ST/latest.pt" --cache-dir "$CACHE" --c-cache-fallback "$LEAN" --old-root "$DATA" --sessions d2,20241219_050046,1682718815 --limit 6 --pairing-check \
  --out "$ST/eval.json" --save-raw "$ST/raw" >> "$ST.log" 2>&1 || { say "SELF-TEST FAILED"; tail -20 "$ST.log" | tee -a "$LOG"; exit 1; }
say "self-test passed: $(grep -o '"eras".*' $ST.log | tail -1 | cut -c1-200)"
# 4. the arms (all on GPU 0, concurrently)
SIX24="20241219_044052,20241219_044529,20241219_050648,20241219_051150,20241219_051629,20241219_052040"
COMMON="--arch armc --base-ch 16 --out-size 96,112 --cond-drop 0.0 --from-scratch --no-base-ckpt --max-steps 24000 --bs 8 --accum 1 --lr 2e-4 --warmup 200 --cosine-horizon 24000 --ckpt-every 1000 --eval-every 2000 --prefetch 8"
declare -A CMD
CMD[armi_2026_s20260908]="$COMMON --emission-image --sessions d2,v10,august --august-train-rows 600 --seed 20260908 --monitor-sessions 20241219_050046,1682718815 --old-root $DATA --cache-dir $CACHE --c-cache-fallback $LEAN"
CMD[armi_2026_s20260907]="$COMMON --emission-image --sessions d2,v10,august --august-train-rows 600 --seed 20260907 --monitor-sessions 20241219_050046,1682718815 --old-root $DATA --cache-dir $CACHE --c-cache-fallback $LEAN"
CMD[armi_2024six_s20260908]="$COMMON --emission-image --sessions $SIX24 --seed 20260908 --monitor-sessions 20241219_050046,1682718815,d2 --old-root $DATA --cache-dir $CACHE --c-cache-fallback $LEAN"
CMD[armc_2026_s20260908_ctl]="$COMMON --sessions d2,v10,august --august-train-rows 600 --seed 20260908 --cache-dir $LEAN"
declare -A PID
for name in armi_2026_s20260908 armi_2026_s20260907 armi_2024six_s20260908 armc_2026_s20260908_ctl; do
  out=$RUNS/$name; mkdir -p "$out"
  CUDA_VISIBLE_DEVICES=0 nohup python3 train_xcfg.py ${CMD[$name]} --out "$out" > "$out/train.log" 2>&1 &
  PID[$name]=$!; say "launched $name pid ${PID[$name]}"
done
# 5. evaluate each arm as soon as it ends
eval_arm() {
  local name=$1 out=$RUNS/$1 extra=""
  case "$name" in
    armc_*) CUDA_VISIBLE_DEVICES=0 python3 eval_xcfg.py --ckpt "$out/latest.pt" --cache-dir "$LEAN" --sessions d2,v10 --out "$RES/$name.eval.json" --save-raw "$RES/$name.raw" > "$out/eval.log" 2>&1
            CUDA_VISIBLE_DEVICES=0 python3 lean_pubproto_eval.py --ckpt "$out/latest.pt" --trainer train_xcfg.py --cache-dir "$LEAN" --out "$RES/$name.pubproto_eval.json" --save-raw "$RES/$name.pubproto_raw" > "$out/pubproto_eval.log" 2>&1 ;;
    armi_2026_s20260908) extra="--dump-examples $RES/examples_$name.npz --n-examples 4" ;&
    *) CUDA_VISIBLE_DEVICES=0 python3 eval_xcfg.py --ckpt "$out/latest.pt" --cache-dir "$CACHE" --c-cache-fallback "$LEAN" --old-root "$DATA" --pairing-check $extra --out "$RES/$name.eval.json" --save-raw "$RES/$name.raw" > "$out/eval.log" 2>&1 ;;
  esac
  say "eval done $name: $(tail -1 $out/eval.log | cut -c1-300)"
}
remaining=("${!PID[@]}")
while [ ${#remaining[@]} -gt 0 ]; do
  still=()
  for name in "${remaining[@]}"; do
    if kill -0 "${PID[$name]}" 2>/dev/null; then still+=("$name"); else
      say "training ended $name (exit $(wait ${PID[$name]} 2>/dev/null; echo $?)): $(grep -h "^{'step'" $RUNS/$name/train.log | tail -1 | cut -c1-120)"
      [ -f "$RUNS/$name/latest.pt" ] && eval_arm "$name" &
    fi
  done
  remaining=("${still[@]}"); sleep 60
done
wait
say "ALL ARMS TRAINED AND EVALUATED"; ls -la "$RES" | tee -a "$LOG"; touch "$RES/.done"
