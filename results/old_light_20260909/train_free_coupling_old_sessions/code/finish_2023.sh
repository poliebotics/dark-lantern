#!/bin/bash
# Final 2023 pass once verify_2023.json shows 0 bad / 0 missing: stage A for all eight sessions (3 parallel, 4 threads
# each), stage B 2023, refinement check on the trailer, figures, report draft.
set -u
PKG=${COUPLING_PKG:-$(cd "$(dirname "$0")/.." && pwd)}; W=$PKG/code
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
LOG=$PKG/run_all.log
echo "$(date -u +%FT%TZ) finish_2023 start" >> $LOG
for s in 1680410249 1680410569 1680412337 1681945334 1682013847 1682014432 1682712156; do echo "$s ${NPY_2023_DIR:-npy_2023}/old_truth_beams/$s"; done > /tmp/coupling_2023_list.txt
echo "1682718815 ${NPY_2023_DIR:-npy_2023}/truth_beam_poliepals_trailer/1682718815" >> /tmp/coupling_2023_list.txt
: > $PKG/stage_a_2023.log
cat /tmp/coupling_2023_list.txt | xargs -P 3 -L 1 sh -c "python3 $W/stage_a_session.py 2023 \$0 \$1 >> $PKG/stage_a_2023.log 2>&1"
echo "$(date -u +%FT%TZ) stage A 2023 done" >> $LOG
python3 $W/stage_b_stats.py 2023 1680410249 1680410569 1680412337 1681945334 1682013847 1682014432 1682712156 1682718815 > $PKG/results/stage_b_2023.out 2>&1
echo "$(date -u +%FT%TZ) stage B 2023 done" >> $LOG
python3 $W/refine_check.py 2023 1682718815 ${NPY_2023_DIR:-npy_2023}/truth_beam_poliepals_trailer/1682718815 2>&1 | grep -v warpPerspective > $PKG/results/refine_check_1682718815.out
echo "$(date -u +%FT%TZ) refine check trailer done" >> $LOG
python3 $W/make_figures.py 20241219_051150:2024 1680410249:2023 1682718815:2023 > $PKG/results/figures.out 2>&1
python3 $W/write_report.py "complete" > $PKG/results/report.out 2>&1
echo "$(date -u +%FT%TZ) FINISH_2023_DONE" >> $LOG
