#!/bin/bash
# PUBLISHED COPY (8 September 2026): this runbook drove the node on 7 and 8 September 2026 and is kept as the record of what ran.
# On the published tree the `build` step's bundle check reads source/SHA256SUMS_G2D, which lists the private pre-substitution
# bytes (REDACTION.md), so that step is historical here; the published rebuild route is VERIFY.md section 2
# (armc-relation/build_reproducible.sh). The `prove` step's 20 s stagger was superseded by the 90 s schedule of
# node_prep/r5/g2g_batch/launch_all.sh, which the batch actually used (receipts/launch_schedule.txt).
# G2-D node runbook for the August proof set (112 rows, 8 GPUs), Astra r5 revision. Every step below is run ON THE NODE
# ([node user]@[node]) by the operator after the release step. The tree root is the directory this runbook lives in
# (node_prep/..), so a copy under .../g2_guest_r5/ drives that tree and never the superseded one. Paths mirror the development machine's.
#
# usage on the node:   bash G2D_NODE_RUNBOOK.sh build            # after the rsync: verify the payload, rebuild, reproduce the pins
#                      bash G2D_NODE_RUNBOOK.sh execute R        # execute (no proof) one row R on the CPU: parity, count, acceptance
#                      bash G2D_NODE_RUNBOOK.sh controls [R] [PROOF]   # negative controls (witness-level on row R; proof-level on PROOF)
#                      bash G2D_NODE_RUNBOOK.sh prove-one N R    # ONE detached proof of row R on GPU N (the pilot), with a basic sidecar
#                      bash G2D_NODE_RUNBOOK.sh prove            # eight detached provers, one per GPU, 14 rows each
#                      bash G2D_NODE_RUNBOOK.sh status           # progress of the provers (rows done / required, complete flags)
#                      bash G2D_NODE_RUNBOOK.sh verify           # cold, standalone acceptance of EVERY proof (fails on the first refusal)
#                      bash G2D_NODE_RUNBOOK.sh merge            # verify, then the strict merge (all 112 rows accepted, or it refuses)
# Every failure propagates: set -euo pipefail, explicit `|| exit 1` inside loops, no pipeline continues after a refusal.
set -euo pipefail
export PATH="$HOME/.cargo/bin:$HOME/.sp1/bin:$HOME/.local/go/bin:$PATH" LC_ALL=C
G2=$(cd "$(dirname "$0")/.." && pwd)
S=$G2/armc-relation/script
ELF=$G2/armc-relation/program/target/elf-compilation/riscv64im-succinct-zkvm-elf/release/zkdiff-guest
BLOB=$G2/blobs/final_int16/constants_int16.blob
NOISE=$G2/noise_august
CHAIN=$G2/vectors_relation/august/chain_log.csv
EXPECT=$G2/expected_identities_august.json
FRAMES=${FRAMES:-[frames directory]}
RUNS=${RUNS:-$HOME/prove_prep/runs/zbdiff_r5_$(basename "$G2")}
CYCLE_LIMIT=200000000000     # requested; not forwarded by the pinned sp1-cuda client (Astra r5 finding 8), the executor enforces it
BUILD_RECORD=""              # set by `build` (the asserting record) and re-read by the later steps
latest_build_record() { ls -1t "$G2"/armc-relation/runs/build_record_*.txt 2>/dev/null | head -1; }
pin() { python3 -c "import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])" "$EXPECT" "$1"; }
need() { [ -e "$1" ] || { echo "MISSING: $1"; exit 1; }; }
case "${1:-}" in
  build)
    cd "$G2"
    need SHA256SUMS_G2D; need "$EXPECT"
    # the payload list names exactly what was transferred (no target/ artefacts), so a plain check passes or fails on the payload
    sha256sum -c SHA256SUMS_G2D --quiet && echo "bundle hashes OK ($(wc -l < SHA256SUMS_G2D) files)" || { echo "BUNDLE HASH MISMATCH: STOP"; exit 1; }
    echo "$(pin constants_sha256)  $BLOB" | sha256sum -c - || { echo "BLOB PIN MISMATCH: STOP"; exit 1; }
    # the fail-closed driver: offline (armc-relation/.cargo/config.toml), --locked, cargo status preserved, lockfiles compared
    # before/after, fresh ELF and host binaries asserted, ELF size / sha256 / vkey / circuit key asserted against the pins,
    # every identity recorded in armc-relation/runs/build_record_<stamp>.txt with the full cargo log beside it
    CUDA=1 nice -n 10 "$G2/armc-relation/build_reproducible.sh" || { echo "BUILD DID NOT REPRODUCE THE PINS: STOP"; exit 1; }
    BUILD_RECORD=$(latest_build_record)
    grep -q "BUILD_REPRODUCED_OK" "$BUILD_RECORD" || { echo "no BUILD_REPRODUCED_OK in $BUILD_RECORD: STOP"; exit 1; }
    "$S/target/release/zkdiff-ceremony" vkey | tee /tmp/g2d_vkey.txt
    grep -q "sp1_vkey=$(pin sp1_vkey)" /tmp/g2d_vkey.txt && echo "VKEY OK" || { echo "VKEY DIFFERS FROM THE PIN: STOP"; exit 1; }
    "$S/target/release/zkdiff-verify" --identity | tee /tmp/g2d_identity.json
    grep -q "\"groth16_vk_sha256\": \"$(pin groth16_vk_sha256)\"" /tmp/g2d_identity.json || { echo "EMBEDDED CIRCUIT KEY DIFFERS FROM THE PIN: STOP"; exit 1; }
    grep -q "\"guest_elf_sha256\": \"$(pin guest_elf_sha256)\"" /tmp/g2d_identity.json || { echo "VERIFIER EMBEDS ANOTHER ELF: STOP"; exit 1; }
    CIRC=$HOME/.sp1/circuits/groth16/$(python3 -c "import json;print(json.load(open('$EXPECT'))['sp1_circuit_version'])")/groth16_vk.bin
    need "$CIRC"
    echo "$(pin groth16_vk_sha256)  $CIRC" | sha256sum -c - || { echo "INSTALLED CIRCUIT KEY DIFFERS FROM THE EMBEDDED ONE: STOP"; exit 1; }
    echo "BUILD STEP OK: record $BUILD_RECORD"
    ;;
  execute)
    R=${2:?row}; BUILD_RECORD=$(latest_build_record); need "$BUILD_RECORD"
    mkdir -p "$RUNS/execute_$R" && cd "$S"
    # expected for row 600 with the r5 ELF: the FULL_GUEST.md section 5 count, R_correct 4435539299, R_wrong 11254163581,
    # clip_events 0, oracle_mode native_reexecution, acceptance accepted=true (about 6.5 min, 17 GB RSS on the node)
    /usr/bin/time -v ./target/release/zkdiff-batch execute --chain-log "$CHAIN" --rows "$R..$R" --frames-dir "$FRAMES" --noise-dir "$NOISE" --blob "$BLOB" \
        --expect "$EXPECT" --build-record "$BUILD_RECORD" --out "$RUNS/execute_$R" 2> "$RUNS/execute_$R/stderr.log" | tee "$RUNS/execute_$R/stdout.log" | grep -E "^(mode|guest_elf|constants_blob|row=|batch_manifest|complete)"
    grep -E "Maximum resident|Elapsed \(wall" "$RUNS/execute_$R/stderr.log"
    grep -q "^row=$R .*status=executed" "$RUNS/execute_$R/stdout.log" || { echo "EXECUTE OF ROW $R DID NOT SUCCEED: STOP"; exit 1; }
    python3 -c "import json,sys; r=json.load(open(sys.argv[1])); assert r['acceptance']['accepted'] is True, r['acceptance'].get('failed_check'); print('acceptance OK', r['outcome_class'], r['total_instruction_count'])" "$RUNS/execute_$R/row_$(printf %06d "$R")/receipt.json"
    ;;
  controls)
    R=${2:-600}; PROOF=${3:-}; mkdir -p "$RUNS/controls_$R" && cd "$S"
    ARGS=(controls --row "$R" --chain-log "$CHAIN" --frames-dir "$FRAMES" --noise-dir "$NOISE" --blob "$BLOB" --expect "$EXPECT" --out "$RUNS/controls_$R")
    [ -n "$PROOF" ] && ARGS+=(--proof "$PROOF")
    ./target/release/zkdiff-batch "${ARGS[@]}" | tee "$RUNS/controls_$R/stdout.log" || { echo "A CONTROL DID NOT BEHAVE: see $RUNS/controls_$R/CONTROLS.json"; exit 1; }
    ;;
  prove-one)
    N=${2:?gpu}; R=${3:?row}; BUILD_RECORD=$(latest_build_record); need "$BUILD_RECORD"
    out="$RUNS/pilot_${R}_gpu$N"; mkdir -p "$out" && cd "$S"
    nvidia-smi -i "$N" --query-gpu=index,uuid,name,driver_version,memory.total --format=csv | tee "$out/gpu_identity.csv"
    setsid nohup nvidia-smi -i "$N" --query-gpu=timestamp,memory.used,memory.total,utilization.gpu,power.draw --format=csv -l 5 > "$out/gpu_mem_5s.csv" 2>&1 < /dev/null &
    echo $! > "$out/nvidia_smi_sidecar.pid"
    setsid nohup /usr/bin/time -v ./target/release/zkdiff-batch prove --prover cuda --device "$N" --cycle-limit $CYCLE_LIMIT \
        --chain-log "$CHAIN" --rows "$R..$R" --frames-dir "$FRAMES" --noise-dir "$NOISE" --blob "$BLOB" --expect "$EXPECT" --build-record "$BUILD_RECORD" --out "$out" \
        > "$out/prove.stdout" 2> "$out/prove.stderr" < /dev/null &
    echo "pilot row $R on gpu $N pid $! out $out (instrumented pilot script: pilot/node_records/prove_step4.sh pattern)"
    ;;
  prove)
    BUILD_RECORD=$(latest_build_record); need "$BUILD_RECORD"
    # one process per GPU, 14 rows each, detached from the ssh session (setsid nohup), nvidia-smi sidecar per GPU; stagger the
    # starts (the eight share CPU, RAM, storage and the server installation; Astra r5 finding 7)
    mkdir -p "$RUNS" && cd "$S"
    nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv | tee "$RUNS/gpus_at_launch.csv"
    i=0
    for range in 600..613 614..627 628..641 642..655 656..669 670..683 684..697 698..711; do
      out="$RUNS/gpu$i"; mkdir -p "$out"
      setsid nohup nvidia-smi -i $i --query-gpu=timestamp,memory.used,utilization.gpu --format=csv -l 30 > "$out/gpu_mem.csv" 2>&1 < /dev/null &
      setsid nohup /usr/bin/time -v ./target/release/zkdiff-batch prove --prover cuda --device $i --cycle-limit $CYCLE_LIMIT \
        --chain-log "$CHAIN" --rows "$range" --frames-dir "$FRAMES" --noise-dir "$NOISE" --blob "$BLOB" --expect "$EXPECT" --build-record "$BUILD_RECORD" --out "$out" \
        > "$out/prove.stdout" 2> "$out/prove.stderr" < /dev/null &
      echo "gpu $i rows $range pid $! out $out"
      i=$((i+1))
      sleep 20
    done
    ;;
  status)
    for i in 0 1 2 3 4 5 6 7; do
      out="$RUNS/gpu$i"; [ -f "$out/prove.stdout" ] || continue
      echo "== gpu $i: $(grep -c 'status=proved' "$out/prove.stdout" || true) proved, $(grep -c 'status=failed' "$out/prove.stdout" || true) failed; last: $(grep -E '^row=' "$out/prove.stdout" | tail -1)"
      [ -f "$out/BATCH_MANIFEST.json" ] && python3 -c "import json,sys; m=json.load(open(sys.argv[1])); print('   manifest: rows_done_ok', m['rows_done_ok'], '/', m['rows_required'], 'complete', m['complete'], 'outcomes', m['outcome_counts'], 'written', m['written_utc'])" "$out/BATCH_MANIFEST.json"
      grep -E "panicked|CEREMONY FAILED|error" "$out/prove.stderr" | tail -2 || true
    done
    ;;
  verify)
    cd "$S"; n=0
    find "$RUNS" -path '*/row_*/row_*_groth16.bin' -print0 | LC_ALL=C sort -z | while IFS= read -r -d '' p; do
      ./target/release/zkdiff-verify --proof "$p" --expect "$EXPECT" --report "${p%.bin}.verify.json" > /dev/null 2>&1 || { echo "VERIFY REFUSED $p"; exit 1; }
      echo "accepted $p"
    done || exit 1
    # proof-level controls once, against the first proof
    first=$(find "$RUNS" -path '*/row_*/row_*_groth16.bin' -print0 | LC_ALL=C sort -z | head -z -n1 | tr -d '\0')
    [ -n "$first" ] || { echo "NO PROOFS UNDER $RUNS"; exit 1; }
    ./target/release/zkdiff-verify --proof "$first" --expect "$EXPECT" --controls --report "$RUNS/proof_controls.json" > /dev/null || { echo "PROOF-LEVEL CONTROLS DID NOT BEHAVE: see $RUNS/proof_controls.json"; exit 1; }
    echo "VERIFY STEP OK"
    ;;
  merge)
    bash "$0" verify || exit 1
    cd "$S" && python3 "$G2/tools/merge_batch_manifests.py" "$RUNS/BATCH_MANIFEST.json" "$RUNS"/gpu*/BATCH_MANIFEST.json || { echo "MERGE REFUSED: the collection is not the complete accepted set"; exit 1; }
    cd "$RUNS" && find . -type f \( -name '*.bin' -o -name '*.json' -o -name '*.hex' -o -name '*.log' -o -name '*.csv' -o -name 'prove.*' \) -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS_RUNS
    echo "MERGE STEP OK; pull back to the development machine:  rsync -az [node user]@NODE:$RUNS/ $G2/proofs_$(date -u +%Y%m%d)/  then sha256sum -c SHA256SUMS_RUNS and zkdiff-verify each proof on the development machine"
    ;;
  *) echo "usage: $0 build|execute R|controls [R] [PROOF]|prove-one N R|prove|status|verify|merge"; exit 2;;
esac
