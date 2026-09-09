#!/bin/bash
# Final production run. Preconditions checked by the operator: verify_2024.json shows 7 matches; verify_2023.json shows
# 0 bad and 0 missing (pull_2023.py finished). Threads: 3 stage-A processes x 4 threads = 12, under the 16-thread cap.
set -u
PKG=${COUPLING_PKG:-$(cd "$(dirname "$0")/.." && pwd)}; W=$PKG/code
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
LOG=$PKG/run_all.log
echo "$(date -u +%FT%TZ) run_all start" >> $LOG
# 2024: seven HDF5 sessions, three at a time
S2024="20241219_044052 20241219_044529 20241219_050046 20241219_050648 20241219_051150 20241219_051629 20241219_052040"
printf "%s\n" $S2024 | xargs -P 3 -I{} sh -c "python3 $W/stage_a_session.py 2024 {} ${HDF5_2024_DIR:-hdf5_2024}/{}/data.h5 >> $PKG/stage_a_2024.log 2>&1"
echo "$(date -u +%FT%TZ) stage A 2024 done" >> $LOG
# 2023: eight sessions (seven old + trailer), three at a time
for s in 1680410249 1680410569 1680412337 1681945334 1682013847 1682014432 1682712156; do echo "$s ${NPY_2023_DIR:-npy_2023}/old_truth_beams/$s"; done > /tmp/coupling_2023_list.txt
echo "1682718815 ${NPY_2023_DIR:-npy_2023}/truth_beam_poliepals_trailer/1682718815" >> /tmp/coupling_2023_list.txt
cat /tmp/coupling_2023_list.txt | xargs -P 3 -L 1 sh -c "python3 $W/stage_a_session.py 2023 \$0 \$1 >> $PKG/stage_a_2023.log 2>&1"
echo "$(date -u +%FT%TZ) stage A 2023 done" >> $LOG
python3 $W/stage_b_stats.py 2023 1680410249 1680410569 1680412337 1681945334 1682013847 1682014432 1682712156 1682718815 > $PKG/results/stage_b_2023.out 2>&1
python3 $W/stage_b_stats.py 2024 $S2024 > $PKG/results/stage_b_2024.out 2>&1
echo "$(date -u +%FT%TZ) stage B done" >> $LOG
python3 $W/make_figures.py 20241219_051150:2024 1680410249:2023 1682718815:2023 > $PKG/results/figures.out 2>&1
echo "$(date -u +%FT%TZ) figures done; RUN_ALL_DONE" >> $LOG
