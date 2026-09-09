#!/bin/bash
# Old Light training: two static pix2pixHD runs concurrently on the one A100 (40 GB). Recipe = the 6 September kit's tb_base_b4
# (the best discriminator-verifier run of that night, 0.965 AUROC; paired G-verifier wins 957/975): netG local, ngf 32,
# n_downsample_global 4, n_blocks_global 9, n_local_enhancers 1, multiscale D num_D 3 n_layers_D 3 ndf 64, loadSize = full width,
# 512 random crops, batch 4, label_nc 0 (RGB emission input), no_instance, no_flip (fixed geometry), VGG + GAN-feature losses.
# Epoch counts are set from the training-set size so both runs see about 70k sample-iterations (the kit's 1024-crop run saw 70k):
#   bash train_oldlight.sh <run> <track> <niter> <niter_decay> --save_epoch_freq N [extra args]   (N must divide niter+niter_decay so the final epoch saves)
set -euo pipefail
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
L=${OL_LOCAL:?set OL_LOCAL to a local work area for the raw downloads, the pairs and the pix2pixHD checkout}; FS=${OL_FS:?set OL_FS to the output directory for checkpoints, results and logs}
run=$1; track=$2; niter=$3; decay=$4; shift 4
cd $L/pix2pixHD
mkdir -p $FS/checkpoints $FS/logs
setsid nohup python3 train.py --name $run --gpu_ids 0 --dataroot $L/pairs$track --checkpoints_dir $FS/checkpoints \
  --label_nc 0 --no_instance --no_flip --resize_or_crop crop --loadSize 2048 --fineSize 512 --netG local --ngf 32 \
  --n_downsample_global 4 --n_blocks_global 9 --n_local_enhancers 1 --num_D 3 --n_layers_D 3 --ndf 64 --batchSize 4 --nThreads 10 \
  --niter $niter --niter_decay $decay --niter_fix_global 1 --save_latest_freq 1000 --print_freq 100 --display_freq 1000000 "$@" \
  > $FS/logs/train_$run.log 2>&1 < /dev/null &
echo "$run on gpu 0 pid $! ($(date -u +%T)) niter $niter decay $decay"
