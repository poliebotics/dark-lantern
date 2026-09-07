#!/usr/bin/env bash
# Samples pose unit + PLONK cgroups every 15 s until the pose unit disappears.
ST=<box path redacted>
OUT="$ST/receipts/pose_unit_monitor.csv"
PL=/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/zeebeam-r32-plonk-a2-20260823.service
echo "utc,unit,unit_active,pose_mem_current,pose_mem_peak,pose_swap,plonk_usage_usec,plonk_mem,host_memavailable_kib" >> "$OUT"
# wait up to 30 min for the unit to appear
for i in $(seq 1 1800); do
  U=$(systemctl --user list-units --all 'bosun-zeebeam-pose-groth16-*' --no-legend 2>/dev/null | awk '{print $1}' | grep -m1 service || true)
  test -n "$U" && break; sleep 1
done
test -n "$U" || { echo "no pose unit appeared" >> "$OUT"; exit 1; }
CG="/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/$U"
while systemctl --user is-active --quiet "$U"; do
  echo "$(date -u +%FT%TZ),$U,active,$(cat $CG/memory.current 2>/dev/null),$(cat $CG/memory.peak 2>/dev/null),$(cat $CG/memory.swap.current 2>/dev/null),$(awk '/usage_usec/{print $2}' $PL/cpu.stat 2>/dev/null),$(cat $PL/memory.current 2>/dev/null),$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)" >> "$OUT"
  sleep 15
done
echo "$(date -u +%FT%TZ),$U,exited,,,,$(awk '/usage_usec/{print $2}' $PL/cpu.stat 2>/dev/null),$(cat $PL/memory.current 2>/dev/null),$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)" >> "$OUT"
