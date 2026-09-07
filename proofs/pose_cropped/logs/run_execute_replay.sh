#!/usr/bin/env bash
set -euo pipefail
. <box path redacted>
OUT="$ST/receipts/execute"
test ! -e "$OUT" || { echo "execute receipt dir exists"; exit 1; }
mkdir -p "$OUT"
BIN="$HR/target/release/zeebeam-trained-r32-pose-ptq-v2"
sha256sum "$BIN" > "$OUT/host_binary_sha256.txt"
systemd-run --user --quiet --wait --collect --pipe \
  --unit=pose-execute-replay-20260824 \
  --working-directory="$HR" \
  --property=MemoryMax=34359738368 \
  --property=MemorySwapMax=0 \
  --property=RuntimeMaxSec=1800 \
  --nice=5 \
  --setenv=RAYON_NUM_THREADS=8 \
  --setenv=MINIMAL_TRACE_CHUNK_THRESHOLD=8388608 \
  --setenv=TRACE_CHUNK_SLOTS=2 \
  /usr/bin/time -v -o "$OUT/time.txt" \
  "$BIN" --mode execute > "$OUT/stdout.log" 2> "$OUT/stderr.log"
req() { grep -Fqx -- "$1" "$OUT/stdout.log" || { echo "MISSING: $1"; exit 9; }; }
req "typed_root=efd35d054df639c3b07acff6ebab5d2ebec59a85ed0dcde5c0e99aa95006d395"
req "typed_context=9d99a1f294eb4e7d1d8b87e21498cf1b598354a9f79b130a227fe6621d794789"
req "predicted_class_id=1"
req "true_class_id_diagnostic_only=0"
req "saturation_count=0"
req "integer_logits_le_i16_csv=8403,8677,184,-1435,6346,-4488,-1564,2047,2253,413,583"
req "public_values_bytes=490"
req "total_instruction_count=16611240"
req "total_syscall_count=0"
req "verified_public_values=true"
req "proof_generated=false"
req "mode=execute_only"
echo "EXECUTE_REPLAY_ALL_EXPECTED_LINES_PRESENT"
grep -E 'span_cycles|host_elapsed_ms' "$OUT/stdout.log"
