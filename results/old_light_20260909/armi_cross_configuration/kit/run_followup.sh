#!/bin/bash
# run_followup.sh (BOSUN, 2026-09-09, second box): ARM-I trained across rigs, plus few-shot adaptation curves.
# Reads only the 96x112 caches the first box left on the filesystem (no archive download). Writes under the same new directory.
set -u
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
FS=${XCFG_FS:?set XCFG_FS to the working directory for caches, checkpoints, results and logs}; KIT=${XCFG_KIT:-$(cd "$(dirname "$0")/src" && pwd)}; LEAN=${XCFG_LEAN:?set XCFG_LEAN to the root of the 2026 preprocessed-row cache, the directory that contains 96x112/ (the loaders append the size)}
CACHE=$FS/cache; WC=$FS/cache_warped; UC=$FS/cache_unified; RUNS=$FS/runs; RES=$FS/results; LOG=$FS/logs/followup.log; cd "$KIT"
say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
say "followup start on $(hostname)"
S24SIX="20241219_044052,20241219_044529,20241219_050648,20241219_051150,20241219_051629,20241219_052040"
S23SEVEN="1680412337,1681945334,1682712156,1682013847,1682014432,1680410249,1680410569"   # ordered by size for the few-shot curve
BASE=$RUNS/armi_2026_s20260908/latest.pt
test -f "$BASE" || { say "base checkpoint missing"; exit 1; }
# 1. unified cache: 2023 sessions -> warped C (+Ei), everything else -> the raw cache (2026 C comes from cache_lean via fallback)
python3 - "$CACHE" "$WC" "$UC" <<'PY'
import os, sys, glob
cache, wc, uc = sys.argv[1:4]
n = 0
for d in sorted(glob.glob(os.path.join(cache, "96x112", "*"))):
    sid = os.path.basename(d); src = os.path.join(wc, "96x112", sid) if sid.startswith("16") else d
    out = os.path.join(uc, "96x112", sid); os.makedirs(out, exist_ok=True)
    for f in glob.glob(os.path.join(src, "*.npy")):
        o = os.path.join(out, os.path.basename(f))
        if not os.path.lexists(o): os.symlink(os.path.realpath(f), o); n += 1
print("unified cache:", n, "links")
PY
for sid in 1682718815 20241219_050046 d2; do echo "  $sid: C $(ls $UC/96x112/$sid | grep -c '^C_') Ei $(ls $UC/96x112/$sid | grep -c '^Ei_')"; done | tee -a "$LOG"
COMMON="--arch armc --base-ch 16 --out-size 96,112 --cond-drop 0.0 --from-scratch --no-base-ckpt --emission-image --bs 8 --accum 1 --prefetch 8 --old-root /nonexistent --c-cache-fallback $LEAN"
# 2. unified arms, two seeds, 24k steps, the published recipe; trailer and 050046 held out whole, 2026 eval blocks guarded as published
declare -A PID
for seed in 20260908 20260907; do
  name=armi_unified_s$seed; out=$RUNS/$name; mkdir -p "$out"
  CUDA_VISIBLE_DEVICES=0 nohup python3 train_xcfg.py $COMMON --sessions "d2,v10,august,$S24SIX,$S23SEVEN" --august-train-rows 600 --seed $seed \
    --monitor-sessions 20241219_050046,1682718815 --cache-dir "$UC" --max-steps 24000 --lr 2e-4 --warmup 200 --cosine-horizon 24000 --ckpt-every 1000 --eval-every 2000 \
    --out "$out" > "$out/train.log" 2>&1 &
  PID[$name]=$!; say "launched $name pid $!"
done
# 3. few-shot adaptation curves: warm start from the 2026-trained ARM-I, brief low-LR fine-tune on k sessions of the new rig only
fewshot() {  # tag cachedir sessions evalsessions
  local tag=$1 cdir=$2 sess=$3 evs=$4
  local out=$RUNS/fs_$tag; mkdir -p "$out"
  CUDA_VISIBLE_DEVICES=0 python3 train_xcfg.py $COMMON --sessions "$sess" --seed 20260908 --init-from "$BASE" --cache-dir "$cdir" \
     --max-steps 2000 --lr 5e-5 --warmup 50 --cosine-horizon 2000 --ckpt-every 1000 --eval-every 1000 --out "$out" > "$out/train.log" 2>&1 || { say "fewshot $tag training failed"; return; }
  CUDA_VISIBLE_DEVICES=0 python3 eval_xcfg.py --ckpt "$out/latest.pt" --cache-dir "$cdir" --c-cache-fallback "$LEAN" --old-root /nonexistent --sessions "$evs" --pairing-check \
     --out "$RES/fs_$tag.eval.json" --save-raw "$RES/fs_$tag.raw" > "$out/eval.log" 2>&1 || say "fewshot $tag eval failed"
  # 2026 retention on the d2 eval blocks, from the raw cache
  CUDA_VISIBLE_DEVICES=0 python3 eval_xcfg.py --ckpt "$out/latest.pt" --cache-dir "$CACHE" --c-cache-fallback "$LEAN" --old-root /nonexistent --sessions d2 \
     --out "$RES/fs_$tag.d2.eval.json" --save-raw "$RES/fs_$tag.d2raw" > "$out/eval_d2.log" 2>&1 || say "fewshot $tag d2 eval failed"
  say "fewshot $tag done: $(tail -1 $out/eval.log | cut -c1-200) | d2 $(tail -1 $out/eval_d2.log | cut -c1-120)"
}
(
  A=(20241219_044052 20241219_044529 20241219_050648 20241219_051150 20241219_051629 20241219_052040)
  for k in 1 2 4 6; do fewshot "2024_k$k" "$CACHE" "$(IFS=,; echo "${A[*]:0:$k}")" "20241219_050046"; done
  B=(1680412337 1681945334 1682712156 1682013847 1682014432 1680410249 1680410569)
  for k in 1 2 4 7; do fewshot "2023w_k$k" "$WC" "$(IFS=,; echo "${B[*]:0:$k}")" "1682718815"; done
  say "FEWSHOT DONE"; touch "$RES/.fewshot_done"
) > "$FS/logs/fewshot.out" 2>&1 &
# 4. evaluate the unified arms as they end: held-out 2026 blocks, 050046 raw, trailer warped (unified cache), plus trailer raw as a secondary line
for name in "${!PID[@]}"; do
  ( wait ${PID[$name]} 2>/dev/null; while kill -0 ${PID[$name]} 2>/dev/null; do sleep 30; done
    say "training ended $name: $(grep -h "^{'step'" $RUNS/$name/train.log | tail -1 | cut -c1-100)"
    CUDA_VISIBLE_DEVICES=0 python3 eval_xcfg.py --ckpt "$RUNS/$name/latest.pt" --cache-dir "$UC" --c-cache-fallback "$LEAN" --old-root /nonexistent \
       --sessions "d2,v10,august,20241219_050046,1682718815" --pairing-check --dump-examples "$RES/examples_$name.npz" --n-examples 3 \
       --out "$RES/$name.eval.json" --save-raw "$RES/$name.raw" > "$RUNS/$name/eval.log" 2>&1
    CUDA_VISIBLE_DEVICES=0 python3 eval_xcfg.py --ckpt "$RUNS/$name/latest.pt" --cache-dir "$CACHE" --c-cache-fallback "$LEAN" --old-root /nonexistent \
       --sessions "1682718815" --out "$RES/$name.trailer_raw.eval.json" --save-raw "$RES/$name.trailer_raw" > "$RUNS/$name/eval_raw.log" 2>&1
    say "eval done $name: $(tail -1 $RUNS/$name/eval.log | cut -c1-300)" ) &
done
wait
say "FOLLOWUP DONE"; touch "$RES/.followup_done"
