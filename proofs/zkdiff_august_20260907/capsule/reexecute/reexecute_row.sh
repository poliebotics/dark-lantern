#!/usr/bin/env bash
# reexecute_row.sh: recompute one proof row's 752-byte statement from its raw sensor frame with the prebuilt static
# zkdiff-batch, whose `execute` mode runs the complete guest program in the SP1 executor on the CPU (the pinned RISC-V ELF,
# executed but not proved), checks the guest's statement against the host's own native re-evaluation, and compares the result
# byte for byte with the published statement.
# Needs bash, coreutils, about 17 GB of RAM and about 4 to 7 minutes per row. No Rust, no Python, no network.
#
#   reexecute_row.sh                      row 600, with the frame shipped in this directory
#   reexecute_row.sh ROW --frames-dir DIR any row 600..711, with DIR holding frame_ROW.raw (24,472,000 bytes) as downloaded from
#                                         the data layer (results/zkdiff_august_20260907/v1/frames/); FRAMES.md lists their digests
# The package root is two directories up when this sits at capsule/reexecute/; set ZKDIFF_PKG otherwise. Outputs go under
# $CAPSULE_OUT (default /tmp/zkdiff_capsule_out), so this directory may be read-only. The batch driver refuses a frame whose
# BLAKE3 differs from the chain log's before anything else runs.
set -euo pipefail
H=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
P=${ZKDIFF_PKG:-$(cd "$H/../.." && pwd)}
ROW=600; FRAMES_DIR="$H"
while [ $# -gt 0 ]; do
  case "$1" in
    --frames-dir) FRAMES_DIR=$2; shift 2;;
    -h|--help) sed -n '2,12p' "$0"; exit 0;;
    *) ROW=$1; shift;;
  esac
done
[[ "$ROW" =~ ^[0-9]+$ ]] && [ "$ROW" -ge 600 ] && [ "$ROW" -le 711 ] || { echo "ROW must be 600..711"; exit 2; }
PAD=$(printf %06d "$ROW")
OUT=${CAPSULE_OUT:-/tmp/zkdiff_capsule_out}/execute_${PAD}_$(date -u +%Y%m%dT%H%M%SZ)
say() { printf '%s\n' "$*"; }
fail() { say "FAIL: $*"; say "RE-EXECUTION FAILED"; exit 1; }
[ -f "$P/source/vectors_relation/august/chain_log.csv" ] || fail "no package at $P (set ZKDIFF_PKG to the package root)"
(cd "$H" && sha256sum -c --quiet SHA256SUMS) || fail "a file of this directory differs from its ledger"
FRAME="$FRAMES_DIR/frame_${PAD}.raw"
[ -f "$FRAME" ] || fail "no frame at $FRAME (download it from the data layer, FRAMES.md, or pass --frames-dir)"
[ "$(stat -c %s "$FRAME")" = 24472000 ] || fail "$FRAME is $(stat -c %s "$FRAME") bytes; a raw frame is 24,472,000 bytes"
say "[0] ledger of $H: $(grep -c . "$H/SHA256SUMS") files present and matching; frame $FRAME, $(stat -c %s "$FRAME") bytes, sha256 $(sha256sum "$FRAME" | cut -c1-64)"
mkdir -p "$OUT/frames"
cp "$FRAME" "$OUT/frames/frame_${PAD}.raw"
say "[1] zkdiff-batch execute, row $ROW; output $OUT"
if ! "$H/zkdiff-batch" execute --chain-log "$P/source/vectors_relation/august/chain_log.csv" --rows "$ROW..$ROW" --frames-dir "$OUT/frames" \
     --noise-dir "$P/source/noise_august" --blob "$P/source/blobs/final_int16/constants_int16.blob" \
     --expect "$P/source/expected_identities_august.json" --build-record "$H/BUILD_RECORD.txt" --out "$OUT" > "$OUT/stdout" 2> "$OUT/stderr"; then
  tail -5 "$OUT/stderr"; fail "zkdiff-batch execute did not succeed (see $OUT/stderr)"
fi
grep -q "^row=$ROW .*status=executed" "$OUT/stdout" || { tail -3 "$OUT/stdout"; fail "row $ROW did not reach status=executed"; }
rec="$OUT/row_$PAD/receipt.json"
g() { grep -o "\"$1\": [^,}]*" "$rec" | head -1 | sed 's/^[^:]*: //; s/"//g'; }
say "[1] executed: offset $(g offset) ($(g offset_rule)), wrong row $(g wrong_row); R_correct $(g r_correct)  R_wrong $(g r_wrong)  D $(g difference) ($(g outcome_class))  clip events $(g clip_events)  instructions $(g total_instruction_count)  oracle_mode $(g oracle_mode)  accepted $(g accepted)"
cmp "$OUT/row_$PAD/public_values.bin" "$P/public_values/row_${PAD}_public_values.bin" || fail "the recomputed 752 public bytes differ from public_values/row_${PAD}_public_values.bin"
say "[2] the recomputed 752-byte statement is byte-identical to the published public_values/row_${PAD}_public_values.bin (sha256 $(sha256sum "$OUT/row_$PAD/public_values.bin" | cut -c1-64))"
say "RE-EXECUTION PASSED: the published residual sums of row $ROW are what the pinned integer network computes on this frame; reports in $OUT"
