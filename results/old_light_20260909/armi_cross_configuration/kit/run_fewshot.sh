#!/bin/bash
# run_followup.sh (BOSUN, 2026-09-09, second box): ARM-I trained across rigs, plus few-shot adaptation curves.
# Reads only the 96x112 caches the first box left on the filesystem (no archive download). Writes under the same new directory.
set -u
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
FS=${XCFG_FS:?set XCFG_FS to the working directory for caches, checkpoints, results and logs}; KIT=${XCFG_KIT:-$(cd "$(dirname "$0")/src" && pwd)}; LEAN=${XCFG_LEAN:?set XCFG_LEAN to the root of the 2026 preprocessed-row cache, the directory that contains 96x112/ (the loaders append the size)}
CACHE=$FS/cache; WC=$FS/cache_warped; UC=$FS/cache_unified; RUNS=$FS/runs; RES=$FS/results; LOG=$FS/logs/fewshot.log; cd "$KIT"
say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
say "fewshot chain start (re-run after the unbound-variable abort) on $(hostname)"
S24SIX="20241219_044052,20241219_044529,20241219_050648,20241219_051150,20241219_051629,20241219_052040"
S23SEVEN="1680412337,1681945334,1682712156,1682013847,1682014432,1680410249,1680410569"   # ordered by size for the few-shot curve
BASE=$RUNS/armi_2026_s20260908/latest.pt
test -f "$BASE" || { say "base checkpoint missing"; exit 1; }
S24SIX="20241219_044052,20241219_044529,20241219_050648,20241219_051150,20241219_051629,20241219_052040"
BASE=$RUNS/armi_2026_s20260908/latest.pt
COMMON="--arch armc --base-ch 16 --out-size 96,112 --cond-drop 0.0 --from-scratch --no-base-ckpt --emission-image --bs 8 --accum 1 --prefetch 8 --old-root /nonexistent --c-cache-fallback $LEAN"
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
A=(20241219_044052 20241219_044529 20241219_050648 20241219_051150 20241219_051629 20241219_052040)
  for k in 1 2 4 6; do fewshot "2024_k$k" "$CACHE" "$(IFS=,; echo "${A[*]:0:$k}")" "20241219_050046"; done
  B=(1680412337 1681945334 1682712156 1682013847 1682014432 1680410249 1680410569)
  for k in 1 2 4 7; do fewshot "2023w_k$k" "$WC" "$(IFS=,; echo "${B[*]:0:$k}")" "1682718815"; done
say "FEWSHOT DONE"; touch "$RES/.fewshot_done"
