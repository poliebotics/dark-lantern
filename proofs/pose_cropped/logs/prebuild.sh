#!/usr/bin/env bash
set -euo pipefail
. <box path redacted>
cd "$HR"
echo "=== fmt check ==="
cargo fmt --all -- --check
echo "=== model/native/relation tests ==="
nice -n 10 cargo test --release --locked \
  -p zeebeam-trained-r32-pose-ptq-v2-model \
  -p zeebeam-trained-r32-pose-ptq-v2-native \
  -p zeebeam-trained-r32-pose-ptq-v2-relation
echo "=== script tests ==="
nice -n 10 cargo test --release --locked -p zeebeam-trained-r32-pose-ptq-v2-script
echo "=== zk-wrap host build ==="
nice -n 10 cargo build --release --locked -p zeebeam-trained-r32-pose-ptq-v2-script --features zk-wrap
echo "=== native parity ==="
nice -n 10 cargo run --release --locked -p zeebeam-trained-r32-pose-ptq-v2-native \
  --bin parity -- frozen/r32_pose_training_calibrated_ptq.bin \
  fixtures/pose_evaluation_r32_parity_v2.bin
echo "=== host binary hash ==="
sha256sum target/release/zeebeam-trained-r32-pose-ptq-v2
stat -c 'host_bytes=%s' target/release/zeebeam-trained-r32-pose-ptq-v2
echo "PREBUILD_ALL_OK"
