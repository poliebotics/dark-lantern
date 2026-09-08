#!/usr/bin/env bash
# Freeze a complete G1 integer artifact for one checkpoint in a single command (no hand steps).
#
#   ./freeze_artifact.sh <ckpt.pt> <pubproto_eval.json> <raw_npz_dir> <out_dir> [stage] [vector_rows]
#
#   ckpt.pt            the checkpoint (ARM-C lean denoiser, width 16, 96x112)
#   pubproto_eval.json the frozen evaluator's summary for that checkpoint (checkpoint_sha256 is verified)
#   raw_npz_dir        directory holding its pubproto_raw.npz_d2.npz and pubproto_raw.npz_v10.npz
#   out_dir            where everything is written (created); safe to point at a fresh directory
#   stage              all (default) | selfcheck | float | agreement | vectors | fixtures | report | august | summary
#   vector_rows        rows for byte-exact vectors, default "d2:1328,august:650"
#
# Stages, in order (each stage's stdout is in <out_dir>/runlogs/):
#   selfcheck  kernels self-test, float64 mirror vs torch fp32, integer forward, effective scale map, bounds (int16 and int8)
#   float      fp32 + two bf16-autocast emulations for the 37 protocol rows and the 112 August rows; per-row positive control
#   agreement  integer residual sums, 37 rows x 5 offsets, int16 and int8, plus all August rows; four processes in parallel
#   vectors    byte-exact test vectors and constants_{int16,int8}.json (scale map, rounding, domain, bounds, op count, LUT clip masks)
#   fixtures   differential boundary fixtures from the scalar oracle (fixtures/, expected bytes and clip counters)
#   report     agreement.json + AGREEMENT.md (evaluator reference first, then fp32 and the emulations; August rule pairs)
#   august     august_inputs/ (guest-ready integer inputs for every August proof row, sha256 manifest)
#   summary    FREEZE_SUMMARY.md with the headline numbers (weakest pairs, control, clips, bounds, August D_q)
# CPU only; every python run uses OMP_NUM_THREADS=16 and writes no bytecode under src/.  About 25 minutes on the development machine.
set -euo pipefail
cd "$(dirname "$0")"
if [ $# -lt 4 ]; then sed -n '2,22p' "$0"; exit 2; fi
export OMP_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1
export G1_CKPT="$(readlink -f "$1")" G1_REF_JSON="$(readlink -f "$2")" G1_RAW_DIR="$(readlink -f "$3")"
mkdir -p "$4"; export G1_OUT="$(readlink -f "$4")"
stage="${5:-all}"; rows="${6:-d2:1328,august:650}"
mkdir -p "$G1_OUT/runlogs" "$G1_OUT/vectors"
log() { echo "[$(date -u +%H:%M:%SZ)] $*"; }
# Published layout (Astra r6 finding 8): the August camera-derived rows (rows_august/.../august/C_*.npy) are served from the
# data layer, not the repository (LARGE_FILES.md). When they are absent the calibration cannot include the seven August rows the
# frozen scale map used and the August stages cannot run: the driver then runs only selfcheck (with --no-august-calib), float
# (without --august) and fixtures, skips agreement, vectors, report, august and summary, and says so. Such a run is a code-path
# check on the public rows: it does not reproduce constants_int16.json, the vectors or the agreement studies, which are loaded,
# not recomputed, by the blob, the Rust tests and the guest. With the data-layer rows placed, every stage runs (VERIFY.md 7).
AUG_C="$PWD/rows_august/august/C_000600.npy"
if [ -f "$AUG_C" ]; then AUGUST=1; NOCALIB=""; AUGFLAG="--august"; else
  AUGUST=0; NOCALIB="--no-august-calib"; AUGFLAG=""; rows=$(echo "$rows" | tr "," "\n" | grep -v "^august:" | paste -sd,)
  log "NOTE: $AUG_C absent (the August camera rows are on the data layer, LARGE_FILES.md): stages agreement, vectors, report, august and summary are skipped; selfcheck runs with --no-august-calib and does not reproduce the frozen scale map"
fi
skip() { log "stage $1 skipped: needs the August camera rows (on the data layer, LARGE_FILES.md)"; }
run_stage() {
  case "$1" in
    selfcheck)
      python3 int_ref.py --scheme int16 $NOCALIB --layer-report > "$G1_OUT/runlogs/selfcheck_int16.log" 2>&1
      python3 int_ref.py --scheme int8 $NOCALIB > "$G1_OUT/runlogs/selfcheck_int8.log" 2>&1 ;;
    float)
      python3 float_repro.py $AUGFLAG > "$G1_OUT/runlogs/float_repro.log" 2>&1
      python3 positive_control.py > "$G1_OUT/runlogs/positive_control.log" 2>&1 ;;
    agreement) [ "$AUGUST" = 1 ] || { skip agreement; return; }
      python3 agreement.py --scheme int16 > "$G1_OUT/runlogs/agreement_int16.log" 2>&1 &
      python3 agreement.py --scheme int8 > "$G1_OUT/runlogs/agreement_int8.log" 2>&1 &
      python3 agreement.py --scheme int16 --sessions august > "$G1_OUT/runlogs/agreement_int16_august.log" 2>&1 &
      python3 agreement.py --scheme int8 --sessions august > "$G1_OUT/runlogs/agreement_int8_august.log" 2>&1 &
      wait ;;
    vectors) [ "$AUGUST" = 1 ] || { skip vectors; return; }
      python3 int_ref.py --scheme int16 --vectors "$G1_OUT/vectors" --vector-rows "$rows" --dump-constants "$G1_OUT/constants_int16.json" > "$G1_OUT/runlogs/vectors_int16.log" 2>&1
      python3 int_ref.py --scheme int8 --vectors "$G1_OUT/vectors" --vector-rows "$rows" --dump-constants "$G1_OUT/constants_int8.json" > "$G1_OUT/runlogs/vectors_int8.log" 2>&1 ;;
    report)  [ "$AUGUST" = 1 ] || { skip report; return; }; python3 agreement.py --report > "$G1_OUT/runlogs/report.log" 2>&1 ;;
    august)  [ "$AUGUST" = 1 ] || { skip august; return; }; python3 august_inputs.py > "$G1_OUT/runlogs/august_inputs.log" 2>&1 ;;
    fixtures) python3 fixtures.py > "$G1_OUT/runlogs/fixtures.log" 2>&1 ;;
    summary) [ "$AUGUST" = 1 ] || { skip summary; return; }; python3 freeze_summary.py > "$G1_OUT/runlogs/summary.log" 2>&1 ;;
    *) echo "unknown stage $1"; exit 2 ;;
  esac
  log "stage $1 done"
}
if [ "$stage" = all ]; then
  for s in selfcheck float agreement vectors fixtures report august summary; do run_stage "$s"; done
else
  run_stage "$stage"
fi
log "artifact in $G1_OUT"
