#!/bin/bash
# G2-G host sidecar for one prover (the pilot's rss_sidecar.sh, keyed by pid and session): every 30 s while the zkdiff-batch
# pid lives, every process of its session (client, sp1-gpu-server, native runner) with RSS/VmHWM/VSZ/%CPU, the session RSS
# sum and system used memory (host_rss.csv, host_procs.log), and per-process VRAM on that GPU (gpu_procs.csv). Appends.
out=$1; N=$2; BPID=$3; SID=$4
[ -f "$out/host_rss.csv" ] || echo "ts_utc,proc,pid,ppid,rss_kib,vmhwm_kib,vsz_kib,pcpu,etimes,sys_used_mib,sum_rss_kib_session" > "$out/host_rss.csv"
echo "rss sidecar start $(date -u +%FT%TZ) gpu=$N bpid=$BPID sid=$SID"
while [ -d "/proc/$BPID" ]; do
  ts=$(date -u +%FT%TZ); used=$(free -m | awk '/^Mem:/{print $3}')
  echo "== $ts sid=$SID" >> "$out/host_procs.log"
  ps -o pid,ppid,sid,rss,vsz,pcpu,etimes,comm,args --sid "$SID" 2>/dev/null | cut -c1-200 >> "$out/host_procs.log"
  sum=0
  for p in $(ps -o pid= --sid "$SID" 2>/dev/null); do
    name=$(cat /proc/$p/comm 2>/dev/null) || continue
    case "$name" in bash|time|sleep|cut|ps|awk|cat|tr|free|df|nvidia-smi|top|sed|date|grep|tee|du) continue;; esac
    read -r rss vsz pcpu et ppid <<< "$(ps -o rss=,vsz=,pcpu=,etimes=,ppid= -p $p 2>/dev/null)"
    hwm=$(awk '/^VmHWM/{print $2}' /proc/$p/status 2>/dev/null)
    sum=$((sum + ${rss:-0}))
    echo "$ts,$name,$p,$ppid,$rss,$hwm,$vsz,$pcpu,$et,$used," >> "$out/host_rss.csv"
  done
  echo "$ts,SESSION_SUM,,,,,,,,$used,$sum" >> "$out/host_rss.csv"
  nvidia-smi -i "$N" --query-compute-apps=timestamp,pid,process_name,used_memory --format=csv,noheader >> "$out/gpu_procs.csv" 2>&1
  sleep 30
done
echo "rss sidecar end $(date -u +%FT%TZ) (zkdiff-batch $BPID gone)"
