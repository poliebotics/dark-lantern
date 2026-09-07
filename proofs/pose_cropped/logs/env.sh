export ST=<box path redacted>
export HR="$ST/zeebeam-trained-r32-pose-ptq-v2-sp1-v1"
export PATH="$ST/toolchain/cargo-prove-bin:$ST/toolchain/go/bin:<box path redacted>"
export CARGO_BUILD_JOBS=32
unset RUSTFLAGS CARGO_ENCODED_RUSTFLAGS
export CARGO_HOME=<machine path redacted>
export BINDGEN_EXTRA_CLANG_ARGS="-isystem /usr/lib/gcc/x86_64-linux-gnu/13/include"
