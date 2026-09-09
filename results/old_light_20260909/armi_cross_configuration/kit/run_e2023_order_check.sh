#!/bin/bash
# run_e2023_order_check.sh: diagnostic, no training. The 2023 emission arrays were read as BGR (OpenCV) and reversed to RGB in the
# loader. This scores the main ARM-I model on the 2023 sessions with the emission channels in the STORED order instead, by
# building a second cache whose Ei files are the channel-reversed copies of the cached ones (reversal commutes with the area
# resize, so this is exactly the alternative convention). If the stored order separates and the reversed one does not, the
# recorder reading was wrong. Waits for results/.done. Output: results/armi_2026_s20260908.e2023stored.eval.json
set -u
export OMP_NUM_THREADS=4
FS=${XCFG_FS:?set XCFG_FS to the working directory for caches, checkpoints, results and logs}; DATA=${XCFG_DATA:?set XCFG_DATA to the directory holding the downloaded 2024 and 2023 archives}; KIT=${XCFG_KIT:-$(cd "$(dirname "$0")/src" && pwd)}; CACHE=$FS/cache; ALT=$FS/cache_e2023stored; LEAN=${XCFG_LEAN:?set XCFG_LEAN to the root of the 2026 preprocessed-row cache, the directory that contains 96x112/ (the loaders append the size)}
ARM=armi_2026_s20260908; RES=$FS/results; LOG=$FS/logs/e2023_order_check.log; cd "$KIT"
say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
for i in $(seq 1 360); do [ -f "$RES/.done" ] && break; sleep 20; done
[ -f "$RES/.done" ] || { say "main run not done after 2 h; abort"; exit 1; }
S23="1680410249 1680410569 1680412337 1681945334 1682013847 1682014432 1682712156 1682718815"
python3 - "$CACHE" "$ALT" $S23 <<'PY'
import sys, os, glob, numpy as np
src, dst, sids = sys.argv[1], sys.argv[2], sys.argv[3:]
n = 0
for sid in sids:
    d = os.path.join(dst, "96x112", sid); os.makedirs(d, exist_ok=True)
    for f in sorted(glob.glob(os.path.join(src, "96x112", sid, "*.npy"))):
        b = os.path.basename(f); o = os.path.join(d, b)
        if os.path.exists(o): continue
        if b.startswith("Ei_"):
            a = np.load(f); np.save(o, np.ascontiguousarray(a[::-1])); n += 1     # channel axis reversed: stored order
        else:
            os.symlink(f, o)
print("alt cache built:", n, "Ei files reversed")
PY
say "alt cache built"
CUDA_VISIBLE_DEVICES=0 python3 eval_xcfg.py --ckpt "$FS/runs/$ARM/latest.pt" --cache-dir "$ALT" --c-cache-fallback "$LEAN" --old-root "$DATA" --sessions "$(echo $S23 | tr ' ' ',')" \
  --out "$RES/$ARM.e2023stored.eval.json" --save-raw "$RES/$ARM.e2023stored.raw" > "$FS/logs/e2023_order_check_eval.log" 2>&1 || say "eval failed"
say "E2023 ORDER CHECK DONE: $(tail -1 $FS/logs/e2023_order_check_eval.log | cut -c1-300)"; touch "$RES/.e2023_done"
