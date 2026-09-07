#!/usr/bin/env bash
set -euo pipefail

export LC_ALL=C
umask 077

STAGE="<box path redacted>"
BIN="$STAGE/bin/zeebeam-trained-r32-ptq-v2-zkwrap"
EXPECTED_ROOT="8ee3eefa1027cc02d955b65f06840fe624ce07077f8d52f7e9e9f4eb309043b2"
EXPECTED_SCORE="56835791"
CIRCUIT_VERSION="v6.1.0"
CIRCUIT_URL="https://sp1-circuits.s3-us-east-2.amazonaws.com/v6.1.0-groth16.tar.gz"
MIN_MEMORY_KIB=1500000000
MIN_DISK_BYTES=322122547200

SP1_ENV=(
  --setenv=RUST_MIN_STACK=33554432
  --setenv=RAYON_NUM_THREADS=224
  --setenv=MINIMAL_TRACE_CHUNK_THRESHOLD=8388608
  --setenv=TRACE_CHUNK_SLOTS=2
  --setenv=SP1_WORKER_NUM_SPLICING_WORKERS=1
  --setenv=SP1_WORKER_SPLICING_BUFFER_SIZE=1
  --setenv=SP1_WORKER_NUMBER_OF_SEND_SPLICE_WORKERS_PER_SPLICE=1
  --setenv=SP1_WORKER_SEND_SPLICE_INPUT_BUFFER_SIZE_PER_SPLICE=1
  --setenv=SP1_WORKER_GLOBAL_MEMORY_BUFFER_SIZE=1
  --setenv=SP1_WORKER_NUM_CORE_WORKERS=1
  --setenv=SP1_WORKER_CORE_BUFFER_SIZE=1
  --setenv=SP1_WORKER_NUM_SETUP_WORKERS=1
  --setenv=SP1_WORKER_SETUP_BUFFER_SIZE=1
  --setenv=SP1_WORKER_NORMALIZE_PROGRAM_CACHE_SIZE=1
  --setenv=SP1_WORKER_NUM_PREPARE_REDUCE_WORKERS=1
  --setenv=SP1_WORKER_PREPARE_REDUCE_BUFFER_SIZE=1
  --setenv=SP1_WORKER_NUM_RECURSION_EXECUTOR_WORKERS=1
  --setenv=SP1_WORKER_RECURSION_EXECUTOR_BUFFER_SIZE=1
  --setenv=SP1_WORKER_NUM_RECURSION_PROVER_WORKERS=1
  --setenv=SP1_WORKER_RECURSION_PROVER_BUFFER_SIZE=1
  --setenv=SP1_WORKER_NUM_DEFERRED_WORKERS=1
  --setenv=SP1_WORKER_DEFERRED_BUFFER_SIZE=1
  --setenv=SP1_WORKER_VERIFY_INTERMEDIATES=true
  --setenv=SP1_WORKER_MAX_REDUCE_ARITY=4
  --setenv=SP1_WORKER_MAX_COMPOSE_ARITY=4
  --setenv=GOMAXPROCS=64
  --setenv=RUST_LOG=info
  --setenv=SP1_GROTH16_CIRCUIT_PATH="$STAGE/runtime/groth16"
)

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

require_line() {
  local path="$1"
  local line="$2"
  grep -Fqx -- "$line" "$path" || die "$path omitted expected line: $line"
}

verify_stage() {
  cd "$STAGE"
  sha256sum -c SHA256SUMS
  test "$(uname -m)" = "x86_64" || die "stage host must be x86_64"
  command -v systemd-run >/dev/null || die "systemd-run is required for the hard cgroup cap"
  command -v timeout >/dev/null || die "timeout is required for the wall-time cap"
  command -v /usr/bin/time >/dev/null || die "/usr/bin/time is required for the receipt"
  command -v curl >/dev/null || die "curl is required for the pinned Groth16 circuit fetch"
  command -v python3 >/dev/null || die "python3 is required for safe circuit extraction"
  local memory_kib disk_bytes
  memory_kib="$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)"
  disk_bytes="$(df --output=avail -B1 "$STAGE" | tail -n 1 | tr -d ' ')"
  test "$memory_kib" -ge "$MIN_MEMORY_KIB" || die "less than the frozen 1.5e9 KiB host-memory floor"
  test "$disk_bytes" -ge "$MIN_DISK_BYTES" || die "less than the frozen 300 GiB free-disk floor"
  systemd-run --user --quiet --wait --collect --pipe \
    --unit=zeebeam-r32-stage-cgroup-check \
    --property=MemoryMax=1073741824 \
    --property=MemorySwapMax=0 \
    /bin/true
}

record_preflight() {
  test ! -e "$STAGE/receipts" || die "refusing to overwrite receipts"
  mkdir "$STAGE/receipts"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$STAGE/receipts/started_at_utc.txt"
  uname -a > "$STAGE/receipts/uname.txt"
  lscpu > "$STAGE/receipts/lscpu.txt"
  cp /proc/meminfo "$STAGE/receipts/meminfo_before.txt"
  df -B1 "$STAGE" > "$STAGE/receipts/df_before.txt"
  sha256sum "$STAGE/SHA256SUMS" > "$STAGE/receipts/stage_manifest_sha256.txt"
  "$BIN" --version > "$STAGE/receipts/host_binary_version.txt"
}

run_execute() {
  local out="$STAGE/results/execute"
  test ! -e "$out" || die "refusing to overwrite execute result"
  mkdir -p "$out"
  systemd-run --user --quiet --wait --collect --pipe \
    --unit=zeebeam-r32-execute-20260823 \
    --working-directory="$STAGE" \
    --property=MemoryMax=34359738368 \
    --property=MemorySwapMax=0 \
    --property=RuntimeMaxSec=1800 \
    --nice=5 \
    "${SP1_ENV[@]}" \
    /usr/bin/time -v -o "$out/time.txt" \
    "$BIN" --mode execute > "$out/stdout.log" 2> "$out/stderr.log"
  require_line "$out/stdout.log" "typed_root=$EXPECTED_ROOT"
  require_line "$out/stdout.log" "score_numerator=$EXPECTED_SCORE"
  require_line "$out/stdout.log" "score_denominator=4"
  require_line "$out/stdout.log" "public_values_bytes=344"
  require_line "$out/stdout.log" "total_instruction_count=203004795"
  require_line "$out/stdout.log" "verified_public_values=true"
  require_line "$out/stdout.log" "proof_generated=false"
}

run_proof() {
  local label="$1"
  local mode="$2"
  local memory_max="$3"
  local runtime_max="$4"
  local timeout_value="$5"
  local expected_mode_line="$6"
  local out="$STAGE/results/$label"
  local proof="$out/trained_r32_${label}.proof.bin"
  test ! -e "$out" || die "refusing to overwrite $label result"
  mkdir -p "$out"
  systemd-run --user --quiet --wait --collect --pipe \
    --unit="zeebeam-r32-${label}-a2-20260823" \
    --working-directory="$STAGE" \
    --property="MemoryMax=$memory_max" \
    --property=MemorySwapMax=0 \
    --property="RuntimeMaxSec=$runtime_max" \
    --property=TimeoutStopSec=300 \
    --property=KillMode=mixed \
    --nice=5 \
    "${SP1_ENV[@]}" \
    /usr/bin/timeout --signal=INT --kill-after=5m "$timeout_value" \
    /usr/bin/time -v -o "$out/time.txt" \
    "$BIN" --mode "$mode" --proof-out "$proof" \
    > "$out/stdout.log" 2> "$out/stderr.log"
  test -s "$proof" || die "$label proof file is absent or empty"
  require_line "$out/stdout.log" "typed_root=$EXPECTED_ROOT"
  require_line "$out/stdout.log" "score_numerator=$EXPECTED_SCORE"
  require_line "$out/stdout.log" "score_denominator=4"
  require_line "$out/stdout.log" "public_values_bytes=344"
  require_line "$out/stdout.log" "$expected_mode_line"
  require_line "$out/stdout.log" "verified_public_values=true"
  require_line "$out/stdout.log" "verified_proof=true"
  require_line "$out/stdout.log" "tampered_public_values_rejected_by_verifier=true"
  grep -Eq '^proof_file_bytes=[1-9][0-9]*$' "$out/stdout.log" || die "$label omitted proof bytes"
  sha256sum "$proof" > "$out/proof_sha256.txt"
}

prepare_groth16() {
  local runtime="$STAGE/runtime"
  local archive="$runtime/v6.1.0-groth16.tar.gz"
  local base="$runtime/groth16"
  local output="$base/$CIRCUIT_VERSION"
  mkdir -p "$base"
  if test -d "$output"; then
    test -f "$output/.complete" || die "existing Groth16 circuit directory is incomplete"
    (cd "$output" && sha256sum -c "$STAGE/CIRCUIT_SHA256SUMS")
    return
  fi
  test ! -e "$archive" || die "refusing an existing unverified circuit archive"
  curl --proto '=https' --tlsv1.2 --fail --location --retry 3 --remove-on-error \
    --output "$archive" "$CIRCUIT_URL"
  sha256sum "$archive" > "$runtime/groth16_archive_sha256.txt"
  python3 "$STAGE/prepare_groth16_circuits.py" \
    "$archive" "$STAGE/CIRCUIT_SHA256SUMS" "$output"
  (cd "$output" && sha256sum -c "$STAGE/CIRCUIT_SHA256SUMS")
}

freeze_receipts() {
  test -s "$STAGE/results/core/trained_r32_core.proof.bin" || die "core proof is absent"
  test -s "$STAGE/results/groth16/trained_r32_groth16.proof.bin" || die "Groth16 proof is absent"
  test ! -e "$STAGE/RUN_SHA256SUMS" || die "refusing to overwrite run manifest"
  cp /proc/meminfo "$STAGE/receipts/meminfo_after.txt"
  df -B1 "$STAGE" > "$STAGE/receipts/df_after.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$STAGE/receipts/completed_at_utc.txt"
  cd "$STAGE"
  find results receipts runtime -type f -print0 \
    | sort -z \
    | xargs -0 sha256sum > RUN_SHA256SUMS
  sha256sum -c RUN_SHA256SUMS
}

usage() {
  printf 'usage: %s {preflight|execute|core|prepare-groth16|groth16|freeze|all}\n' "$0" >&2
  exit 2
}

mode="${1:-}"
test "$#" -eq 1 || usage
case "$mode" in
  preflight)
    verify_stage
    ;;
  execute)
    verify_stage
    mkdir -p "$STAGE/results"
    run_execute
    ;;
  core)
    verify_stage
    mkdir -p "$STAGE/results"
    run_proof core core 512G 14400 4h mode=core_stark_proof
    ;;
  prepare-groth16)
    verify_stage
    prepare_groth16
    ;;
  groth16)
    verify_stage
    prepare_groth16
    mkdir -p "$STAGE/results"
    run_proof groth16 groth16 1200G 43200 12h mode=groth16_zk_snark
    ;;
  freeze)
    verify_stage
    freeze_receipts
    ;;
  all)
    verify_stage
    record_preflight
    mkdir "$STAGE/results"
    run_execute
    run_proof core core 512G 14400 4h mode=core_stark_proof
    prepare_groth16
    run_proof groth16 groth16 1200G 43200 12h mode=groth16_zk_snark
    freeze_receipts
    ;;
  *)
    usage
    ;;
esac
