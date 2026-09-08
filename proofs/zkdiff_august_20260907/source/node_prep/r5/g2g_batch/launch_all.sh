#!/bin/bash
# G2-G: eight detached provers, one per GPU, 14 contiguous rows each (600-613, 614-627, ..., 698-711), started 90 s apart.
# Run detached itself (setsid nohup bash launch_all.sh >> launch_all.log 2>&1 < /dev/null &). Records the GPUs at launch,
# /tmp state before, 60 s after the first launch (does the second server rewrite the native runner?) and after the last.
RUNS=$HOME/prove_prep/runs/zbdiff_r5_g2_guest_r5; mkdir -p "$RUNS"
D=$HOME/prove_prep/g2g_batch
ts() { date -u +%FT%T.%3NZ; }
tmpstate() { { echo "== $(ts) $1"; ls -la /tmp/sp1-* 2>&1; stat -c '%y %s %n' /tmp/sp1-native-runner-bin-* 2>&1; pgrep -a -x sp1-gpu-server | cut -c1-120; pgrep -c -f '[s]p1-native-runner-bin'; } >> "$RUNS/tmp_state.log"; }
echo "launch_all start $(ts)" | tee -a "$RUNS/launch_schedule.txt"
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv > "$RUNS/gpus_at_launch.csv"
tmpstate "before any launch"
pgrep -f "[s]ys_sidecar.sh" > /dev/null || { setsid nohup bash "$D/sys_sidecar.sh" >> "$RUNS/sys_sidecar.out" 2>&1 < /dev/null & echo "sys sidecar pid $!" | tee -a "$RUNS/launch_schedule.txt"; }
i=0
for range in 600:613 614:627 628:641 642:655 656:669 670:683 684:697 698:711; do
  a=${range%:*}; b=${range#*:}
  TAG=launch setsid nohup bash "$D/launch_gpu.sh" $i $a $b >> "$RUNS/launch_gpu$i.log" 2>&1 < /dev/null &
  echo "$(ts) gpu $i rows $a..$b launcher pid $!" | tee -a "$RUNS/launch_schedule.txt"
  if [ $i -eq 0 ]; then sleep 60; tmpstate "60 s after gpu 0 launch"; sleep 30
  elif [ $i -eq 1 ]; then sleep 60; tmpstate "60 s after gpu 1 launch"; sleep 30
  elif [ $i -lt 7 ]; then sleep 90; fi
  i=$((i+1))
done
sleep 60; tmpstate "60 s after gpu 7 launch"
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv >> "$RUNS/tmp_state.log"
echo "launch_all end $(ts)" | tee -a "$RUNS/launch_schedule.txt"
