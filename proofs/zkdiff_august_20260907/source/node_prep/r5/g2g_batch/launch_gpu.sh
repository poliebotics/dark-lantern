#!/bin/bash
# G2-G: one detached prover on GPU N over rows A..B (zkdiff-batch prove --prover cuda --device N, re-pinned r5 tree), with the
# pilot's sidecars: nvidia-smi 30 s sampler and the per-session host RSS sampler. Launch this script itself detached
# (setsid nohup bash launch_gpu.sh N A B >> .../launch_gpuN.log 2>&1 < /dev/null &) so the prover pipeline owns its session.
# TAG names the attempt (launch, relaunch1, ...). On a relaunch the existing BATCH_MANIFEST.json is copied aside first: the
# driver rewrites it for the new --rows range, and the copy keeps the earlier rows' entries for the merge. Nothing is deleted.
set -o pipefail
export PATH="$HOME/.cargo/bin:$HOME/.sp1/bin:$HOME/.local/go/bin:$PATH" LC_ALL=C
export RUST_LOG="${RUST_LOG:-info}"
N=${1:?gpu}; A=${2:?first row}; B=${3:?last row}; TAG=${TAG:-launch}
G2=source
S=$G2/armc-relation/script
ELF=$G2/armc-relation/program/target/elf-compilation/riscv64im-succinct-zkvm-elf/release/zkdiff-guest
BLOB=$G2/blobs/final_int16/constants_int16.blob
NOISE=$G2/noise_august
CHAIN=$G2/vectors_relation/august/chain_log.csv
EXPECT=$G2/expected_identities_august.json
FRAMES=[frames directory]
RUNS=$HOME/prove_prep/runs/zbdiff_r5_g2_guest_r5
D=$HOME/prove_prep/g2g_batch
CYCLE_LIMIT=200000000000
BUILD_RECORD=$(ls -1t "$G2"/armc-relation/runs/build_record_*.txt | head -1)
out=$RUNS/gpu$N; mkdir -p "$out"; cd "$S" || exit 9
ts() { date -u +%FT%T.%3NZ; }
SID=$(ps -o sid= -p $$ | tr -d ' ')
echo "$TAG gpu=$N rows=$A..$B start=$(ts) pid=$$ sid=$SID build_record=$BUILD_RECORD RUST_LOG=$RUST_LOG" | tee -a "$out/launch_times.txt"
if [ -f "$out/BATCH_MANIFEST.json" ]; then
  cp -p "$out/BATCH_MANIFEST.json" "$out/BATCH_MANIFEST_before_$TAG.json"
  echo "kept the earlier manifest as BATCH_MANIFEST_before_$TAG.json" | tee -a "$out/launch_times.txt"
fi
pgrep -f "[s]ys_sidecar.sh" > /dev/null || { setsid nohup bash "$D/sys_sidecar.sh" >> "$RUNS/sys_sidecar.out" 2>&1 < /dev/null & echo "sys sidecar started pid $!" | tee -a "$out/launch_times.txt"; }
nvidia-smi -i "$N" --query-gpu=index,uuid,name,driver_version,memory.total,pci.bus_id --format=csv > "$out/gpu_identity.csv" 2>&1
sha256sum ./target/release/zkdiff-batch "$ELF" "$BLOB" "$CHAIN" "$EXPECT" "$BUILD_RECORD" > "$out/inputs_identity_$TAG.txt" 2>&1
setsid nohup nvidia-smi -i "$N" --query-gpu=timestamp,memory.used,memory.total,utilization.gpu,power.draw,temperature.gpu --format=csv -l 30 >> "$out/gpu_mem.csv" 2>&1 < /dev/null &
echo $! > "$out/nvidia_smi_sidecar.pid"
echo "prover exec $(ts) $TAG rows $A..$B" | tee -a "$out/launch_times.txt"
/usr/bin/time -v ./target/release/zkdiff-batch prove --prover cuda --device "$N" --cycle-limit $CYCLE_LIMIT \
  --chain-log "$CHAIN" --rows "$A..$B" --frames-dir "$FRAMES" --noise-dir "$NOISE" --blob "$BLOB" --expect "$EXPECT" --build-record "$BUILD_RECORD" --out "$out" \
  2>> "$out/prove.stderr" < /dev/null | while IFS= read -r line; do printf "%s %s\n" "$(date -u +%FT%T.%3NZ)" "$line"; done >> "$out/prove.stdout" &
PIPE=$!
sleep 5
BPID=""
for p in $(pgrep -x zkdiff-batch); do tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null | grep -q -- "--device $N " && BPID=$p; done
echo "zkdiff-batch pid=$BPID sid=$SID pipeline_pid=$PIPE" | tee -a "$out/launch_times.txt"
if [ -n "$BPID" ]; then
  setsid nohup bash "$D/sidecar_rss.sh" "$out" "$N" "$BPID" "$SID" >> "$out/rss_sidecar.log" 2>&1 < /dev/null &
  echo "rss sidecar pid $!" | tee -a "$out/launch_times.txt"
fi
wait $PIPE; rc=$?
echo "prover pipeline exit=$rc end=$(ts) $TAG (time -v 'Exit status' or 'terminated by signal' in prove.stderr)" | tee -a "$out/launch_times.txt"
echo "stdout: proved=$(grep -c 'status=proved' "$out/prove.stdout") failed=$(grep -c 'status=failed' "$out/prove.stdout"); $(grep -E ' complete=' "$out/prove.stdout" | tail -1 | cut -c1-200)" | tee -a "$out/launch_times.txt"
kill "$(cat "$out/nvidia_smi_sidecar.pid")" 2>/dev/null
echo "$TAG gpu=$N done $(ts)" | tee -a "$out/launch_times.txt"
