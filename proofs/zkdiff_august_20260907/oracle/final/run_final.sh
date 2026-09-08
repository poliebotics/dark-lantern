#!/usr/bin/env bash
# Regenerate THIS artifact (g0e_armc_b16_96x112_cd0_aug_s20260908_24k) with the general one-command freeze.
# Usage: final/run_final.sh [stage]   (stage: all | selfcheck | float | agreement | vectors | report | august | summary)
set -euo pipefail
cd "$(dirname "$0")/.."
# Published layout (Astra r8 finding 5): the checkpoint, its evaluator summary and the raw scores ship under ../model/ rather
# than ckpt/final/; the private layout stays the first choice so the script runs unchanged where it was written. Regenerating
# THIS artifact writes into ./final, the published copy: run it on a copy of the package (VERIFY.md section 7; the run is not
# rehearsed on the published tree).
if [ -f ckpt/final/g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pt ]; then CK=ckpt/final; RAW=ckpt/final/g0e_armc_b16_96x112_cd0_aug_s20260908_24k
else CK=../model; RAW=../model/pubproto_raw; fi
exec ./freeze_artifact.sh \
  "$CK/g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pt" \
  "$CK/g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pubproto_eval.json" \
  "$RAW" \
  final "${1:-all}" "d2:1328,august:650"
