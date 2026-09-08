#!/bin/bash
# G2-G: one STATUS header and one line per GPU group: prover alive (pid), proved+accepted / failed receipts, verified
# reports ok / bad, manifest required / done / finished / complete, outcome counts, the last row line of prove.stdout.
RUNS=$HOME/prove_prep/runs/zbdiff_r5_g2_guest_r5
echo "STATUS ts=$(date -u +%FT%TZ) load=$(cut -d' ' -f1-3 /proc/loadavg) used_mib=$(free -m | awk '/^Mem:/{print $3}') zkdiff_procs=$(pgrep -c -x zkdiff-batch) servers=$(pgrep -c -x sp1-gpu-server) runners=$(pgrep -c -f '[s]p1-native-runner-bin')"
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tr '\n' ';'; echo
for i in 0 1 2 3 4 5 6 7; do
  out=$RUNS/gpu$i; [ -d "$out" ] || { echo "GPU $i: no dir"; continue; }
  alive=no; for p in $(pgrep -x zkdiff-batch); do tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null | grep -q -- "--device $i " && alive=$p; done
  python3 - "$out" "$i" "$alive" <<'PY'
import json, sys, glob
out, i, alive = sys.argv[1], sys.argv[2], sys.argv[3]
proved = failed = other = 0; ok = bad = 0; rows_proved = []; rows_failed = []
for r in sorted(glob.glob(out + "/row_*/receipt.json")):
    try:
        j = json.load(open(r))
    except Exception:
        other += 1; continue
    s = j.get("status")
    if s == "proved" and (j.get("acceptance") or {}).get("accepted"):
        proved += 1; rows_proved.append(j["row"])
    elif s == "failed":
        failed += 1; rows_failed.append(j["row"])
    else:
        other += 1
for v in glob.glob(out + "/row_*/row_*_groth16.verify.json"):
    try:
        o = json.load(open(v)).get("ok")
    except Exception:
        o = None
    if o: ok += 1
    else: bad += 1
m = {}
try:
    m = json.load(open(out + "/BATCH_MANIFEST.json"))
except Exception:
    pass
last = ""
try:
    last = [l for l in open(out + "/prove.stdout") if " row=" in l or "cuda_setup" in l or "starting proof" in l][-1].strip()[:170]
except Exception:
    pass
print(f"GPU {i}: alive={alive} proved_accepted={proved} failed={failed} other={other} verified_ok={ok} verified_bad={bad} manifest_required={m.get('rows_required')} done_ok={m.get('rows_done_ok')} finished={m.get('finished')} complete={m.get('complete')} outcomes={m.get('outcome_counts')} rows_proved={rows_proved} rows_failed={rows_failed} last='{last}'")
PY
done
