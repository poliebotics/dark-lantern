#!/usr/bin/env bash
set -uo pipefail
. <box path redacted>
R="$ST/receipts"
PL=/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/zeebeam-r32-plonk-a2-20260823.service
date -u +%FT%TZ > "$R/runner_started_utc.txt"
# pre-launch PLONK snapshot
{ echo "utc=$(date -u +%FT%TZ)"; awk '/usage_usec/{print "plonk_usage_usec="$2}' "$PL/cpu.stat"; echo "plonk_mem=$(cat $PL/memory.current)"; echo "plonk_active=$(systemctl --user is-active zeebeam-r32-plonk-a2-20260823.service)"; } > "$R/plonk_before_runner.txt"
# overlap-guard dry run (same awk as the frozen runner)
if ps -eo args= | awk '
  /zeebeam-trained-r32-pose-ptq-v2/ && /--mode (core|groth16|plonk)/ { found=1 }
  /sp1.*prove/ && !/awk/ { found=1 }
  /gnark/ && !/awk/ { found=1 }
  END { exit found ? 0 : 1 }
'; then echo "DRYRUN: overlap guard WOULD trip" > "$R/overlap_dryrun.txt"; exit 4;
else echo "DRYRUN: overlap guard clear at $(date -u +%FT%TZ)" > "$R/overlap_dryrun.txt"; fi
awk '/^MemAvailable:/{print "memavailable_kib="$2}' /proc/meminfo >> "$R/overlap_dryrun.txt"
# results-path accommodation (declared): unit CWD is $HOME, --proof-out is relative
test ! -e <box path redacted> || { echo "<box path redacted> already exists; abort" ; exit 5; }
ln -s "$HR/results" <box path redacted>
echo "created <box path redacted> -> $HR/results at $(date -u +%FT%TZ)" > "$R/results_symlink_record.txt"
# launch monitor
<box path redacted> &
MON=$!
# coexistence bound for the gnark tail (frozen unit leaves GOMAXPROCS unset -> would
# default to 240 procs); manager env is captured by the unit at spawn. Declared in receipt.
systemctl --user set-environment GOMAXPROCS=8
echo "manager GOMAXPROCS=8 set at $(date -u +%FT%TZ)" > "$R/gomaxprocs_record.txt"
# frozen runner, exactly as handed off
cd "$HR"
chmod 755 tools/run_bosun-worker_groth16_bounded.sh
tools/run_bosun-worker_groth16_bounded.sh "$HR" > "$ST/logs/runner.log" 2>&1
RC=$?
systemctl --user unset-environment GOMAXPROCS
echo "manager GOMAXPROCS unset at $(date -u +%FT%TZ)" >> "$R/gomaxprocs_record.txt"
echo "runner_exit=$RC at $(date -u +%FT%TZ)" | tee "$R/runner_exit.txt"
# cleanup accommodation
rm -f <box path redacted>
echo "removed <box path redacted> at $(date -u +%FT%TZ)" >> "$R/results_symlink_record.txt"
# post-run PLONK snapshot
{ echo "utc=$(date -u +%FT%TZ)"; awk '/usage_usec/{print "plonk_usage_usec="$2}' "$PL/cpu.stat"; echo "plonk_mem=$(cat $PL/memory.current)"; echo "plonk_active=$(systemctl --user is-active zeebeam-r32-plonk-a2-20260823.service)"; } > "$R/plonk_after_runner.txt"
wait "$MON" 2>/dev/null
exit "$RC"
