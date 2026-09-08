# Replication image for the zkdiff August proof package (Dark Lantern proofs/zkdiff_august_20260907).
#
#   docker build -t zkdiff-replicate .                         # CPU image: Ubuntu 22.04 + the pinned Rust 1.98.0 / SP1 6.4.0 toolchain
#   docker run --rm -v "$PWD/work:/work" zkdiff-replicate      # = replicate.sh verify: fetch, ledger, rebuild the guest, verify 112 proofs
#   docker run --rm -v "$PWD/work:/work" zkdiff-replicate replicate.sh all --no-prove
#
# GPU (prove): build on a CUDA 12 runtime base and pass the GPUs through (needs the NVIDIA Container Toolkit on the host):
#   docker build -t zkdiff-replicate-cuda --build-arg BASE=nvidia/cuda:12.8.1-runtime-ubuntu22.04 .
#   docker run --rm --gpus all -v "$PWD/work:/work" -v /path/to/frames:/frames:ro zkdiff-replicate-cuda \
#       replicate.sh prove 600 --device 0 --frame /frames/frame_000600.raw
# The frame: --frame PATH, or row 600's frame shipped in the package's capsule/reexecute/, or the row's published frame fetched from the
# data layer (FRAMES.md); a 24 GB GPU is below the observed peak (about 28.5 GiB), so prove wants an A100-class card.
#
# The toolchain lives in the image under /home/replicator (uid 1000 by default; --build-arg UID=$(id -u) to match your user so the
# files written to the /work volume are yours). Nothing in this image is a secret or a credential. Every download is hash-pinned by
# replicate.sh itself; the apt packages come from Ubuntu's signed archive.
ARG BASE=ubuntu:22.04
FROM ${BASE} AS base
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git build-essential pkg-config time binutils python3 xz-utils \
    && rm -rf /var/lib/apt/lists/*
ARG UID=1000
RUN useradd -m -u ${UID} -s /bin/bash replicator && mkdir -p /work && chown replicator:replicator /work
COPY replicate.sh /usr/local/bin/replicate.sh
RUN chmod 0755 /usr/local/bin/replicate.sh
USER replicator
ENV HOME=/home/replicator \
    PATH=/home/replicator/.cargo/bin:/home/replicator/.sp1/bin:/home/replicator/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    ZKDIFF_WORK=/work
WORKDIR /work

FROM base AS toolchain
# rustup 1.29.1 (pinned installer), Rust 1.98.0, cargo-prove sp1 f66b4bf, the succinct 1.94.0-dev guest toolchain, protoc 21.12, b3sum:
# the same steps replicate.sh runs on a bare machine, so the image and the script cannot drift apart.
RUN replicate.sh --work /tmp/toolchain toolchain sp1 && rm -rf /tmp/toolchain
CMD ["replicate.sh", "verify"]
