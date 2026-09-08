#!/usr/bin/env bash
# replicate.sh: one-pull replication of the zkdiff August proof package (Dark Lantern proofs/zkdiff_august_20260907).
#
# Every download is checked against a SHA-256 pinned in this file or in the package's own ledgers before anything runs;
# every step prints what it checked; the first mismatch exits non-zero. Idempotent: rerun after a failure and it resumes.
#
#   replicate.sh [options] fetch                 the repository package and the data-layer objects, every byte hash-checked
#   replicate.sh [options] quick                 Groth16 verification of all 112 proofs with the vendored standalone verifier (host Rust only)
#   replicate.sh [options] build                 pinned SP1 6.4.0 toolchain, then the reproducible rebuild: ELF, size and vkey asserted
#   replicate.sh [options] verify                acceptance verification of all 112 proofs with the package's own zkdiff-verify (implies build)
#   replicate.sh [options] execute ROW           one August row through the complete guest on the CPU; the frame is --frame PATH, or row 600's
#                                                frame shipped in capsule/reexecute/, or the published frame fetched from the data layer (FRAMES.md);
#                                                if no frame can be had: the frame-independent legs of that row, then the guest on the synthetic session
#   replicate.sh [options] synthetic             the complete guest, 14.4 G instructions, on the shipped synthetic session (no frame needed)
#   replicate.sh [options] parity                the Rust integer kernels against the Python oracle's vectors (cargo test; the data-layer files)
#   replicate.sh [options] prove ROW             one fresh Groth16 proof of an August row on a CUDA GPU (--device; the frame as for execute)
#   replicate.sh [options] all                   fetch, build, verify, quick, execute (or synthetic), parity, and prove when a GPU and a frame are present
#   replicate.sh [options] toolchain [rust|sp1|gpu]   install the pinned toolchains only (gpu implies sp1 implies rust)
#
# options:
#   --work DIR             working directory (default: $ZKDIFF_WORK or ./zkdiff_replicate)
#   --from-local PATH      take the repository package from a local copy (the package directory or a Dark Lantern checkout) instead of GitHub
#   --data-from-local DIR  take the data-layer objects from a local copy of the prefix instead of https://data.truthbeam.com
#   --ref REF              git ref of poliebotics/dark-lantern to fetch (default: main; a commit hash pins the tree)
#   --repo-only            fetch: skip the data-layer objects (they serve only parity and the oracle regeneration)
#   --frame PATH           the row's raw sensor frame (24,472,000 bytes; its BLAKE3 must equal the chain log's) for execute and prove; without it
#                          the script uses the shipped frame of row 600 or fetches the row's published frame from the data layer (FRAMES.md)
#   --device N             CUDA device for prove (default 0)
#   --no-prove             all: never prove, even with a GPU
#   --jobs N               cargo build jobs (default: cargo's)
#   --no-b3sum             do not install b3sum (the independent BLAKE3 check of the noise files and chain log is then skipped)
#   --refetch              fetch: discard a present package copy and fetch again
set -euo pipefail

# ---------------------------------------------------------------------------------------------------------------------
# Pins. Every one of these is also in the package (PINS.json, VERIFY.md, source/node_prep/) and the two copies must agree.
# ---------------------------------------------------------------------------------------------------------------------
readonly PACKAGE_REL="proofs/zkdiff_august_20260907"
readonly REPO_URL_DEFAULT="https://github.com/poliebotics/dark-lantern"
readonly DATA_BASE_DEFAULT="https://data.truthbeam.com/results/zkdiff_august_20260907/v1"
readonly DATA_PREFIX="results/zkdiff_august_20260907/v1/"
readonly ROW_FIRST=600 ROW_LAST=711
# the program
readonly PIN_ELF_SHA="51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc"
readonly PIN_ELF_BYTES="396200"
readonly PIN_VKEY="0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027"
readonly PIN_GROTH16_VK_SHA="4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696"   # sp1-verifier 6.4.0 = circuits/groth16/v6.1.0
readonly PIN_CIRCUIT_VERSION="v6.1.0"
readonly PIN_CONSTANTS_SHA="73310ddab603cab5588d05e9ac4deb7e56466a6fae4bbf89244c32f2bd1a8b92"
readonly PIN_CONSTANTS_BYTES="3476866"
readonly PIN_EXPECTED_IDENTITIES_SHA="182870aa06f11e246a76f8c94c5a1c40aed7b3ad4b3537420422f426dcd46eb2"
readonly PIN_CHAIN_LOG_SHA="5d9af297ae37119df15412f516a4543ee9f54b6aa66186abe478512fe9a1ff48"
readonly PIN_CHAIN_LOG_BLAKE3="754e5716e65a065e5ad3146131609a1fd12e8310d966fb6bf2d3de6c568e7f8b"
# the vendored ZeeBeam standalone verifier (tools/standalone_verifier, byte for byte from poliebotics/zeebeam ef686b33…48bd)
readonly PIN_SV_CARGO_TOML="07c3da3e187769e9734087a3c21fc18dc38144b756765641b580d1f13b6f2a71"
readonly PIN_SV_CARGO_LOCK="78fa1a2b85ac671f7e881ff4e4e9bfd84d1cec8d7cdabc52f1ff03aebffc19c1"
readonly PIN_SV_MAIN_RS="052f7a69dd66029659ea6acbb76a01cf902b6751ee43dedce150467b4cbf638a"
# host toolchain
readonly RUSTUP_VERSION="1.29.1"
readonly RUSTUP_INIT_URL="https://static.rust-lang.org/rustup/archive/${RUSTUP_VERSION}/x86_64-unknown-linux-gnu/rustup-init"
readonly PIN_RUSTUP_INIT_SHA="dda7234360b7f578ca8b0ddcb80145646fa61a67c1720a5abc7051b35c9fcb71"
readonly HOST_RUST="1.98.0"
readonly PIN_RUSTC_VERSION="rustc 1.98.0 (88d9e12ae 2026-08-18)"
readonly PIN_CARGO_VERSION="cargo 1.98.0 (797e8a9bc 2026-08-05)"
readonly B3SUM_VERSION="1.8.7"
# SP1 6.4.0 guest toolchain (the exact bytes the node and the development machine built with)
readonly CARGO_PROVE_URL="https://github.com/succinctlabs/sp1/releases/download/v6.4.0/cargo_prove_v6.4.0_linux_amd64.tar.gz"
readonly PIN_CARGO_PROVE_TARBALL_SHA="8ad88ebd4d970f0b9b7561f9b5899242f01c7da6d04ec4bd5d09f4cf044a541b"
readonly PIN_CARGO_PROVE_TARBALL_BYTES="21210386"
readonly PIN_CARGO_PROVE_SHA="d8835f80b386d5025420d6b09e73ad825b822ac143e8ed09312b2e08018ff106"
readonly PIN_CARGO_PROVE_VERSION="cargo-prove sp1 (f66b4bf 2026-08-12T14:40:11.709680161Z)"
readonly SUCCINCT_TOOLCHAIN_URL="https://github.com/succinctlabs/rust/releases/download/succinct-1.94.0-64bit/rust-toolchain-x86_64-unknown-linux-gnu.tar.gz"
readonly PIN_SUCCINCT_TARBALL_SHA="12c94435d41bfe4e20131bbcce40b35abd32270ad792befc653af4e3fabc192f"
readonly PIN_SUCCINCT_TARBALL_BYTES="384963362"
readonly PIN_SUCCINCT_RELEASE="1.94.0-dev"
readonly PIN_SUCCINCT_LLVM="21.1.8"
readonly SUCCINCT_DIR_NAME="succinct-1.94.0-64bit"
readonly PROTOC_URL="https://github.com/protocolbuffers/protobuf/releases/download/v21.12/protoc-21.12-linux-x86_64.zip"
readonly PIN_PROTOC_ZIP_SHA="3a4c1e5f2516c639d3079b1586e703fc7bcfa2136d58bda24d1d54f949c315e8"
readonly PIN_PROTOC_ZIP_BYTES="1585982"
readonly PIN_PROTOC_VERSION="libprotoc 3.21.12"
# GPU proving: the server binary and the Groth16 v6.1.0 circuit cache
readonly SP1_GPU_SERVER_URL="https://github.com/succinctlabs/sp1/releases/download/v6.4.0/sp1_gpu_server_v6.4.0_x86_64.tar.gz"
readonly PIN_SP1_GPU_SERVER_TARBALL_SHA="2946b0b46026b8689181eb05561ed0be2798114196893d5ef38e46f93c14c596"
readonly PIN_SP1_GPU_SERVER_TARBALL_BYTES="133469274"
readonly PIN_SP1_GPU_SERVER_SHA="f68b85dc3cff776a613df897ba6e7f8592d08482330b4165d46a8ee87aafd97c"
readonly PIN_SP1_GPU_SERVER_BYTES="250950472"
readonly CIRCUITS_URL="https://sp1-circuits.s3-us-east-2.amazonaws.com/v6.1.0-groth16.tar.gz"
readonly CIRCUITS_TARBALL_BYTES="6211807514"    # size only; the seven extracted files are pinned below and the tarball's own digest is recorded
readonly PIN_CIRCUITS="\
4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696  groth16_vk.bin
ee2ac8e094712a87ec3b0dc50ed39704aa90ee066ce4c5bf6160d54f04014c94  groth16_witness.json
d5e777120d9f675aefcc8c0c8786d4043acb8e063646e60818564b44fb2ec457  Groth16Verifier.sol
48e1db5baca3b102242ebd88280b3689a088076688146cd0d98876f5dacb76d0  SP1VerifierGroth16.sol
1fb0b3d5f59c45b8f41973b111604aba2402db3c8e887074300ab8d164def92b  constraints.json
d6a66be2702206e2b1a20bebf7096142864feac9e399a309e5e6e00353264cbc  groth16_circuit.bin
c3760e0e3b58487f8704680d5b3ad32a9fbca9f3cb0749d69055c4f1271ca167  groth16_pk.bin"
readonly CYCLE_LIMIT="200000000000"
readonly UA="zkdiff-replicate/1.0 (curl; https://github.com/poliebotics/dark-lantern)"

# ---------------------------------------------------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------------------------------------------------
WORK="${ZKDIFF_WORK:-$PWD/zkdiff_replicate}"
REPO_URL="${ZKDIFF_REPO_URL:-$REPO_URL_DEFAULT}"
DATA_BASE="${ZKDIFF_BASE_URL:-$DATA_BASE_DEFAULT}"
REF="${ZKDIFF_REF:-main}"
FROM_LOCAL=""; DATA_FROM_LOCAL=""; REPO_ONLY=0; FRAME=""; DEVICE=0; NO_PROVE=0; NO_B3SUM=0; REFETCH=0
CMD=""; ARG1=""
while [ $# -gt 0 ]; do
  case "$1" in
    --work) WORK=$2; shift 2;;
    --from-local) FROM_LOCAL=$2; shift 2;;
    --data-from-local) DATA_FROM_LOCAL=$2; shift 2;;
    --ref) REF=$2; shift 2;;
    --repo-only) REPO_ONLY=1; shift;;
    --frame) FRAME=$2; shift 2;;
    --device) DEVICE=$2; shift 2;;
    --no-prove) NO_PROVE=1; shift;;
    --jobs) export CARGO_BUILD_JOBS=$2; shift 2;;
    --no-b3sum) NO_B3SUM=1; shift;;
    --refetch) REFETCH=1; shift;;
    -h|--help) sed -n '2,32p' "$0"; exit 0;;
    --*) echo "unknown option $1" >&2; exit 2;;
    *) if [ -z "$CMD" ]; then CMD=$1; elif [ -z "$ARG1" ]; then ARG1=$1; else echo "unexpected argument $1" >&2; exit 2; fi; shift;;
  esac
done
[ -n "$CMD" ] || { sed -n '2,32p' "$0"; exit 2; }

WORK=$(mkdir -p "$WORK" && cd "$WORK" && pwd)
DL="$WORK/downloads"; REPO="$WORK/repo"; PKG="$REPO/$PACKAGE_REL"; DATA="$WORK/data"; OUT="$WORK/out"
mkdir -p "$DL" "$DATA" "$OUT"
export CARGO_HOME="${CARGO_HOME:-$HOME/.cargo}" RUSTUP_HOME="${RUSTUP_HOME:-$HOME/.rustup}"
export PATH="$CARGO_HOME/bin:$HOME/.sp1/bin:$HOME/.local/bin:$PATH" LC_ALL=C
unset RUSTFLAGS CARGO_ENCODED_RUSTFLAGS RUSTUP_TOOLCHAIN || true
LOGFILE="$OUT/replicate.log"
exec > >(tee -a "$LOGFILE") 2>&1
trap 'sleep 0.3' EXIT    # let tee drain

# ---------------------------------------------------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------------------------------------------------
say()  { printf '%s\n' "$*"; }
ts()   { date -u +%Y-%m-%dT%H:%M:%SZ; }
step() { say ""; say "[$(ts)] ==> $*"; }
ok()   { say "[$(ts)]  ok  $*"; }
note() { say "[$(ts)]  ..  $*"; }
warn() { say "[$(ts)] WARN $*"; }
fail() { say "[$(ts)] FAIL $*"; say "[$(ts)] replicate.sh: stopped (log: $LOGFILE)"; exit 1; }
sha()  { sha256sum "$1" | cut -c1-64; }
need_cmd() { command -v "$1" >/dev/null 2>&1 || fail "missing command: $1 ($2)"; }
elapsed() { local s=$1; local e; e=$(( $(date +%s) - s )); printf '%dm%02ds' $((e/60)) $((e%60)); }
have_gpu() { command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; }

# S/BLOB/EXPECT/CHAIN/NOISE point into the package once it is present
set_paths() {
  S="$PKG/source/armc-relation/script"
  ELF="$PKG/source/armc-relation/program/target/elf-compilation/riscv64im-succinct-zkvm-elf/release/zkdiff-guest"
  BLOB="$PKG/source/blobs/final_int16/constants_int16.blob"
  EXPECT="$PKG/source/expected_identities_august.json"
  CHAIN="$PKG/source/vectors_relation/august/chain_log.csv"
  NOISE="$PKG/source/noise_august"
}
set_paths

fetch_pinned() { # url dest sha256 [bytes]
  local url=$1 dest=$2 want=$3 bytes=${4:-}
  if [ -f "$dest" ] && [ "$(sha "$dest")" = "$want" ]; then ok "present, sha256 $want: $dest"; return 0; fi
  need_cmd curl "apt-get install curl"
  note "download $url"
  mkdir -p "$(dirname "$dest")"
  curl -fsSL --retry 5 --retry-all-errors -A "$UA" -o "$dest.part" "$url" || fail "download failed: $url"
  local got; got=$(sha "$dest.part")
  [ "$got" = "$want" ] || { rm -f "$dest.part"; fail "sha256 of $url is $got, the pin says $want"; }
  if [ -n "$bytes" ]; then [ "$(stat -c %s "$dest.part")" = "$bytes" ] || { rm -f "$dest.part"; fail "size of $url is $(stat -c %s "$dest.part"), the pin says $bytes"; }; fi
  mv -f "$dest.part" "$dest"
  ok "downloaded, sha256 $got${bytes:+, $bytes bytes}: $dest"
}

environment_summary() {
  step "environment"
  say "  date        $(ts)"
  say "  os          $(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME" || uname -s)  kernel $(uname -rm)  glibc $(ldd --version 2>/dev/null | head -1 | awk '{print $NF}')"
  say "  cpu/mem     $(nproc) threads, $(awk '/MemTotal/{printf "%.0f GiB", $2/1048576}' /proc/meminfo) RAM, $(awk '/MemAvailable/{printf "%.0f GiB", $2/1048576}' /proc/meminfo) available"
  say "  disk        $(df -h "$WORK" | awk 'NR==2{print $4" free on "$6}')"
  say "  container   $([ -f /.dockerenv ] && echo yes || echo no)   user uid $(id -u)   HOME $HOME"
  if have_gpu; then say "  gpu         $(nvidia-smi -L | tr '\n' ';')"; else say "  gpu         none visible (nvidia-smi absent or no device)"; fi
  say "  work        $WORK"
  say "  log         $LOGFILE"
}

# ---------------------------------------------------------------------------------------------------------------------
# Toolchains: rust (rustup + 1.98.0 + b3sum), sp1 (cargo-prove, succinct toolchain, protoc), gpu (sp1-gpu-server, circuits)
# ---------------------------------------------------------------------------------------------------------------------
ensure_rust() {
  step "toolchain: host Rust $HOST_RUST"
  need_cmd curl "apt-get install curl"; need_cmd cc "apt-get install build-essential"; need_cmd python3 "apt-get install python3"
  need_cmd tar "coreutils"; need_cmd git "apt-get install git"
  if ! command -v rustup >/dev/null 2>&1; then
    fetch_pinned "$RUSTUP_INIT_URL" "$DL/rustup-init" "$PIN_RUSTUP_INIT_SHA"
    chmod +x "$DL/rustup-init"
    "$DL/rustup-init" -y -q --profile minimal --default-toolchain none --no-modify-path >/dev/null || fail "rustup-init failed"
    command -v rustup >/dev/null 2>&1 || fail "rustup-init ran but rustup is not on PATH ($CARGO_HOME/bin)"
    ok "rustup $(rustup --version 2>/dev/null | head -1 | awk '{print $2}') installed in $CARGO_HOME and $RUSTUP_HOME (pinned installer)"
  else
    ok "rustup present: $(rustup --version 2>/dev/null | head -1)"
  fi
  rustup toolchain install "$HOST_RUST" --profile minimal >/dev/null 2>&1 || rustup toolchain install "$HOST_RUST" --profile minimal
  rustup default "$HOST_RUST" >/dev/null 2>&1
  local rv cv
  rv=$(rustc +"$HOST_RUST" -V); cv=$(cargo +"$HOST_RUST" -V)
  [ "$rv" = "$PIN_RUSTC_VERSION" ] || fail "rustc is '$rv', the pin says '$PIN_RUSTC_VERSION'"
  [ "$cv" = "$PIN_CARGO_VERSION" ] || fail "cargo is '$cv', the pin says '$PIN_CARGO_VERSION'"
  ok "$rv; $cv (rustup-verified channel download)"
  if [ "$NO_B3SUM" = 0 ]; then
    if command -v b3sum >/dev/null 2>&1; then
      ok "b3sum present: $(b3sum --version)"
    else
      note "installing b3sum $B3SUM_VERSION from crates.io (independent BLAKE3 tool for the noise files and chain log)"
      if cargo +"$HOST_RUST" install -q b3sum --version "$B3SUM_VERSION" --locked >/dev/null 2>&1; then ok "b3sum $(b3sum --version)"; else warn "b3sum did not install; the independent BLAKE3 check is skipped (the package's own code still checks the noise digests in execute)"; fi
    fi
  fi
}

ensure_sp1() {
  ensure_rust
  step "toolchain: SP1 6.4.0 (cargo-prove, succinct guest toolchain, protoc)"
  need_cmd /usr/bin/time "apt-get install time (GNU time; the build driver records wall time and RSS with it)"
  need_cmd objdump "apt-get install binutils"; need_cmd strings "apt-get install binutils"
  mkdir -p "$HOME/.sp1/bin" "$HOME/.sp1/toolchains" "$HOME/.local/bin"
  # cargo-prove
  if [ -x "$HOME/.sp1/bin/cargo-prove" ] && [ "$(sha "$HOME/.sp1/bin/cargo-prove")" = "$PIN_CARGO_PROVE_SHA" ]; then
    ok "cargo-prove present, sha256 $PIN_CARGO_PROVE_SHA"
  else
    fetch_pinned "$CARGO_PROVE_URL" "$DL/cargo_prove_v6.4.0_linux_amd64.tar.gz" "$PIN_CARGO_PROVE_TARBALL_SHA" "$PIN_CARGO_PROVE_TARBALL_BYTES"
    local t; t=$(mktemp -d "$DL/cargo_prove.XXXXXX")
    tar -xzf "$DL/cargo_prove_v6.4.0_linux_amd64.tar.gz" -C "$t"
    [ -f "$t/cargo-prove" ] || fail "the cargo-prove tarball carries no cargo-prove at its root"
    [ "$(sha "$t/cargo-prove")" = "$PIN_CARGO_PROVE_SHA" ] || fail "extracted cargo-prove sha256 $(sha "$t/cargo-prove") != pin $PIN_CARGO_PROVE_SHA"
    install -m 0755 "$t/cargo-prove" "$HOME/.sp1/bin/cargo-prove"; rm -rf "$t"
    ok "cargo-prove installed, sha256 $PIN_CARGO_PROVE_SHA"
  fi
  local cpv; cpv=$(cargo prove --version 2>/dev/null | head -1 || true)
  [ "$cpv" = "$PIN_CARGO_PROVE_VERSION" ] || fail "cargo prove --version says '$cpv', the pin says '$PIN_CARGO_PROVE_VERSION'"
  ok "$cpv"
  # succinct toolchain: the tarball is kept where sp1up keeps it, because the build driver records its digest
  local tb="$HOME/.sp1/rust-toolchain-x86_64-unknown-linux-gnu.tar.gz" tdir="$HOME/.sp1/toolchains/$SUCCINCT_DIR_NAME"
  fetch_pinned "$SUCCINCT_TOOLCHAIN_URL" "$tb" "$PIN_SUCCINCT_TARBALL_SHA" "$PIN_SUCCINCT_TARBALL_BYTES"
  local relink=0
  if rustc +succinct -vV >/dev/null 2>&1; then
    local rel llvm
    rel=$(rustc +succinct -vV | awk '/^release:/{print $2}'); llvm=$(rustc +succinct -vV | awk '/^LLVM version:/{print $3}')
    if [ "$rel" = "$PIN_SUCCINCT_RELEASE" ] && [ "$llvm" = "$PIN_SUCCINCT_LLVM" ]; then ok "rustup toolchain 'succinct' present: rustc $rel, LLVM $llvm"; else warn "an existing 'succinct' toolchain is rustc $rel / LLVM $llvm, not $PIN_SUCCINCT_RELEASE / $PIN_SUCCINCT_LLVM; relinking to the pinned tarball"; relink=1; fi
  else
    relink=1
  fi
  if [ "$relink" = 1 ]; then
    if [ ! -x "$tdir/bin/rustc" ]; then
      note "extracting the succinct toolchain to $tdir"
      mkdir -p "$tdir"; tar -xzf "$tb" -C "$tdir"
    fi
    rustup toolchain uninstall succinct >/dev/null 2>&1 || true
    rustup toolchain link succinct "$tdir"
    local rel llvm
    rel=$(rustc +succinct -vV | awk '/^release:/{print $2}'); llvm=$(rustc +succinct -vV | awk '/^LLVM version:/{print $3}')
    [ "$rel" = "$PIN_SUCCINCT_RELEASE" ] && [ "$llvm" = "$PIN_SUCCINCT_LLVM" ] || fail "linked succinct toolchain is rustc $rel / LLVM $llvm"
    ok "rustup toolchain 'succinct' linked to $tdir: rustc $rel, LLVM $llvm"
  fi
  local sysroot; sysroot=$(rustc +succinct --print sysroot)
  [ -d "$sysroot/lib/rustlib/riscv64im-succinct-zkvm-elf" ] || fail "the succinct toolchain carries no riscv64im-succinct-zkvm-elf target"
  [ -x "$sysroot/lib/rustlib/x86_64-unknown-linux-gnu/bin/gcc-ld/ld.lld" ] || fail "the succinct toolchain carries no bundled ld.lld"
  # the guest toolchain ships rustc only; give it the pinned host cargo so the guest build needs no rustup fallback toolchain
  if ! cargo +succinct -V >/dev/null 2>&1 || [ "$(cargo +succinct -V 2>/dev/null)" != "$PIN_CARGO_VERSION" ]; then
    ln -sfn "$(rustc +"$HOST_RUST" --print sysroot)/bin/cargo" "$sysroot/bin/cargo"
  fi
  [ "$(cargo +succinct -V 2>/dev/null)" = "$PIN_CARGO_VERSION" ] || fail "cargo +succinct is '$(cargo +succinct -V 2>&1 | head -1)', expected the pinned $PIN_CARGO_VERSION"
  ok "cargo +succinct resolves to $PIN_CARGO_VERSION; target riscv64im-succinct-zkvm-elf and bundled ld.lld present"
  # protoc (the sp1-prover-types build script runs it)
  if [ "$(protoc --version 2>/dev/null || true)" = "$PIN_PROTOC_VERSION" ]; then
    ok "protoc present: $PIN_PROTOC_VERSION ($(command -v protoc))"
  else
    fetch_pinned "$PROTOC_URL" "$DL/protoc-21.12-linux-x86_64.zip" "$PIN_PROTOC_ZIP_SHA" "$PIN_PROTOC_ZIP_BYTES"
    python3 - "$DL/protoc-21.12-linux-x86_64.zip" "$HOME/.local" <<'PY' || fail "protoc did not extract"
import sys, zipfile, os, stat
z, dest = zipfile.ZipFile(sys.argv[1]), sys.argv[2]
for n in z.namelist():
    if n.startswith("bin/") or n.startswith("include/"):
        z.extract(n, dest)
p = os.path.join(dest, "bin", "protoc"); os.chmod(p, os.stat(p).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
PY
    [ "$(protoc --version)" = "$PIN_PROTOC_VERSION" ] || fail "protoc --version says '$(protoc --version)'"
    ok "protoc installed to $HOME/.local/bin: $PIN_PROTOC_VERSION"
  fi
  export PROTOC; PROTOC=$(command -v protoc)
}

ensure_gpu() {
  ensure_sp1
  step "toolchain: CUDA prover (sp1-gpu-server 6.4.0, Groth16 circuit cache $PIN_CIRCUIT_VERSION)"
  have_gpu || fail "nvidia-smi shows no device; the prove step needs a CUDA GPU (about 28.5 GiB of VRAM was the observed peak)"
  if ldconfig -p 2>/dev/null | grep -q 'libcudart\.so\.12'; then
    ok "libcudart.so.12 on the library path (sp1-gpu-server links it)"
  elif [ -e /usr/local/cuda/lib64/libcudart.so.12 ]; then
    export LD_LIBRARY_PATH="/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"; ok "libcudart.so.12 found under /usr/local/cuda/lib64 (added to LD_LIBRARY_PATH)"
  else
    fail "libcudart.so.12 not found; install the CUDA 12 runtime (the node ran driver 570.148.08 with CUDA runtime 12.8.90)"
  fi
  if [ -x "$HOME/.sp1/bin/sp1-gpu-server" ] && [ "$(sha "$HOME/.sp1/bin/sp1-gpu-server")" = "$PIN_SP1_GPU_SERVER_SHA" ]; then
    ok "sp1-gpu-server present, sha256 $PIN_SP1_GPU_SERVER_SHA"
  else
    fetch_pinned "$SP1_GPU_SERVER_URL" "$DL/sp1_gpu_server_v6.4.0_x86_64.tar.gz" "$PIN_SP1_GPU_SERVER_TARBALL_SHA" "$PIN_SP1_GPU_SERVER_TARBALL_BYTES"
    local t; t=$(mktemp -d "$DL/sp1_gpu_server.XXXXXX")
    tar -xzf "$DL/sp1_gpu_server_v6.4.0_x86_64.tar.gz" -C "$t"
    local bin; bin=$(find "$t" -type f -name 'sp1-gpu-server*' | head -1)
    [ -n "$bin" ] || fail "the sp1-gpu-server tarball carries no sp1-gpu-server binary"
    [ "$(sha "$bin")" = "$PIN_SP1_GPU_SERVER_SHA" ] || fail "extracted sp1-gpu-server sha256 $(sha "$bin") != pin $PIN_SP1_GPU_SERVER_SHA"
    [ "$(stat -c %s "$bin")" = "$PIN_SP1_GPU_SERVER_BYTES" ] || fail "extracted sp1-gpu-server is $(stat -c %s "$bin") bytes, the pin says $PIN_SP1_GPU_SERVER_BYTES"
    install -m 0755 "$bin" "$HOME/.sp1/bin/sp1-gpu-server"; rm -rf "$t"
    ok "sp1-gpu-server installed, sha256 $PIN_SP1_GPU_SERVER_SHA"
  fi
  local sv; sv=$(CUDA_VISIBLE_DEVICES="" timeout 20 "$HOME/.sp1/bin/sp1-gpu-server" --version 2>&1 | tr -d '\r' | tail -1 || true)
  case "$sv" in *6.4.0*) ok "sp1-gpu-server --version: $sv";; *) fail "sp1-gpu-server --version says '$sv', expected 6.4.0";; esac
  local cdir="$HOME/.sp1/circuits/groth16/$PIN_CIRCUIT_VERSION"
  if [ -f "$cdir/.complete" ] && (cd "$cdir" && echo "$PIN_CIRCUITS" | sha256sum -c --quiet - >/dev/null 2>&1); then
    ok "Groth16 circuit cache present and pinned: $cdir (7 files)"
  else
    note "the Groth16 $PIN_CIRCUIT_VERSION circuit cache is absent or incomplete; fetching $CIRCUITS_URL ($CIRCUITS_TARBALL_BYTES bytes, about 5.8 GiB)"
    mkdir -p "$cdir"
    local tgz="$DL/v6.1.0-groth16.tar.gz"
    if [ ! -f "$tgz" ] || [ "$(stat -c %s "$tgz")" != "$CIRCUITS_TARBALL_BYTES" ]; then
      curl -fsSL --retry 5 --retry-all-errors -C - -A "$UA" -o "$tgz" "$CIRCUITS_URL" || fail "circuit download failed"
    fi
    [ "$(stat -c %s "$tgz")" = "$CIRCUITS_TARBALL_BYTES" ] || fail "circuit tarball is $(stat -c %s "$tgz") bytes, expected $CIRCUITS_TARBALL_BYTES"
    note "circuit tarball sha256 $(sha "$tgz") (recorded; the seven files inside are the pinned identities)"
    local t; t=$(mktemp -d "$DL/circuits.XXXXXX")
    tar -xzf "$tgz" -C "$t"
    local f p
    while read -r _ f; do
      p=$(find "$t" -type f -name "$f" | head -1); [ -n "$p" ] || fail "circuit tarball carries no $f"
      mv -f "$p" "$cdir/$f"
    done <<<"$PIN_CIRCUITS"
    rm -rf "$t"
    (cd "$cdir" && echo "$PIN_CIRCUITS" | sha256sum -c --quiet -) || fail "a circuit file differs from its pin"
    : > "$cdir/.complete"
    ok "Groth16 circuit cache installed and pinned: $cdir; tarball kept at $tgz"
  fi
}

# ---------------------------------------------------------------------------------------------------------------------
# fetch: the repository package and the data-layer objects
# ---------------------------------------------------------------------------------------------------------------------
check_ledger() {
  step "package ledger"
  [ -f "$PKG/SHA256SUMS" ] || fail "no SHA256SUMS in $PKG"
  (cd "$PKG" && sha256sum -c --quiet SHA256SUMS) || fail "a package file differs from SHA256SUMS"
  local entries unlisted
  entries=$(grep -c . "$PKG/SHA256SUMS")
  unlisted=$(cd "$PKG" && find . -type f ! -name SHA256SUMS ! -path '*/target/*' ! -path './source/armc-relation/runs/build_record_*' \
      ! -path './source/armc-relation/runs/build_log_*' ! -path './source/armc-relation/runs/SOURCE_DIGESTS_*' ! -path './source/armc-relation/runs/.build_start_*' \
      | sed 's|^\./||' | LC_ALL=C sort | LC_ALL=C comm -23 - <(LC_ALL=C sort <(cut -c67- SHA256SUMS) <(cut -c67- LARGE_FILES_SHA256SUMS)))
  if [ -n "$unlisted" ]; then say "$unlisted" | head -20; fail "$(say "$unlisted" | wc -l) file(s) in the package that no ledger lists"; fi
  ok "SHA256SUMS: $entries entries, every listed file present and matching, no unlisted file (build outputs and data-layer files excepted)"
  if [ -f "$REPO/SHA256SUMS" ]; then
    # the Dark Lantern root ledger lists paths as ./proofs/...; accept that form and the bare one
    local n; n=$(grep -c -E "  (\./)?$PACKAGE_REL/" "$REPO/SHA256SUMS" || true)
    if [ "$n" -gt 0 ]; then
      (cd "$PKG" && grep -E "  (\./)?$PACKAGE_REL/" "$REPO/SHA256SUMS" | sed -E "s#  (\./)?$PACKAGE_REL/#  #" | sha256sum -c --quiet -) || fail "the repository's root SHA256SUMS disagrees with the package files"
      ok "root SHA256SUMS of the repository: $n entries under $PACKAGE_REL/ all match"
    else
      note "the repository's root SHA256SUMS has no entries for $PACKAGE_REL/ (a tree staged before the package was committed?)"
    fi
  fi
}

check_pins() {
  step "pins: this script against PINS.json, the expected identities and the frozen files"
  python3 - "$PKG" "$PIN_ELF_SHA" "$PIN_ELF_BYTES" "$PIN_VKEY" "$PIN_GROTH16_VK_SHA" "$PIN_CIRCUIT_VERSION" "$PIN_CONSTANTS_SHA" "$PIN_CONSTANTS_BYTES" "$PIN_EXPECTED_IDENTITIES_SHA" "$PIN_CHAIN_LOG_SHA" "$PIN_CHAIN_LOG_BLAKE3" "$PIN_SV_CARGO_TOML" "$PIN_SV_CARGO_LOCK" "$PIN_SV_MAIN_RS" <<'PY' || fail "a pin disagrees between this script and the package"
import json, sys, hashlib, os
pkg, elf_sha, elf_bytes, vkey, g16, circ, const_sha, const_bytes, exp_sha, chain_sha, chain_b3, sv_toml, sv_lock, sv_main = sys.argv[1:]
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()
bad = []
def eq(what, got, want):
    if str(got) != str(want): bad.append(f"{what}: package says {got}, this script pins {want}")
P = json.load(open(f"{pkg}/PINS.json")); prog = P["program"]
eq("PINS.json program.guest_elf_sha256", prog["guest_elf_sha256"], elf_sha)
eq("PINS.json program.guest_elf_bytes", prog["guest_elf_bytes"], elf_bytes)
eq("PINS.json program.sp1_vkey", prog["sp1_vkey"], vkey)
eq("PINS.json program.groth16_vk_sha256", prog["groth16_vk_sha256"], g16)
eq("PINS.json program.sp1_circuit_version", prog["sp1_circuit_version"], circ)
eq("PINS.json program.sp1_version", prog["sp1_version"], "6.4.0")
eq("PINS.json program.constants_sha256", prog["constants_sha256"], const_sha)
eq("PINS.json program.constants_blob_bytes", prog["constants_blob_bytes"], const_bytes)
eq("PINS.json program.public_statement_bytes", prog["public_statement_bytes"], 752)
eq("PINS.json program.raw_groth16_proof_bytes", prog["raw_groth16_proof_bytes"], 356)
eq("PINS.json chain_log.sha256", P["chain_log"]["sha256"], chain_sha)
eq("PINS.json chain_log.blake3", P["chain_log"]["blake3"], chain_b3)
eq("PINS.json prover_node.groth16_circuit_files_v6_1_0.groth16_vk.bin", P["prover_node"]["groth16_circuit_files_v6_1_0"]["groth16_vk.bin"], g16)
eq("PINS.json reproducible_build.guest_toolchain.cargo_prove_sha256", P["reproducible_build"]["guest_toolchain"]["cargo_prove_sha256"], "d8835f80b386d5025420d6b09e73ad825b822ac143e8ed09312b2e08018ff106")
eq("PINS.json reproducible_build.guest_toolchain.succinct_toolchain_tarball_sha256", P["reproducible_build"]["guest_toolchain"]["succinct_toolchain_tarball_sha256"], "12c94435d41bfe4e20131bbcce40b35abd32270ad792befc653af4e3fabc192f")
eq("PINS.json prover_node.sp1_gpu_server_sha256", P["prover_node"]["sp1_gpu_server_sha256"], "f68b85dc3cff776a613df897ba6e7f8592d08482330b4165d46a8ee87aafd97c")
E = json.load(open(f"{pkg}/source/expected_identities_august.json"))
eq("expected_identities sp1_vkey", E["sp1_vkey"], vkey); eq("expected_identities guest_elf_sha256", E["guest_elf_sha256"], elf_sha)
eq("expected_identities groth16_vk_sha256", E["groth16_vk_sha256"], g16); eq("expected_identities constants_sha256", E["constants_sha256"], const_sha)
eq("expected_identities sp1_circuit_version", E["sp1_circuit_version"], circ)
eq("sha256(source/expected_identities_august.json)", sha(f"{pkg}/source/expected_identities_august.json"), exp_sha)
eq("sha256(constants_int16.blob)", sha(f"{pkg}/source/blobs/final_int16/constants_int16.blob"), const_sha)
eq("size(constants_int16.blob)", os.path.getsize(f"{pkg}/source/blobs/final_int16/constants_int16.blob"), const_bytes)
eq("sha256(chain_log.csv)", sha(f"{pkg}/source/vectors_relation/august/chain_log.csv"), chain_sha)
eq("sha256(tools/standalone_verifier/Cargo.toml)", sha(f"{pkg}/tools/standalone_verifier/Cargo.toml"), sv_toml)
eq("sha256(tools/standalone_verifier/Cargo.lock)", sha(f"{pkg}/tools/standalone_verifier/Cargo.lock"), sv_lock)
eq("sha256(tools/standalone_verifier/src/main.rs)", sha(f"{pkg}/tools/standalone_verifier/src/main.rs"), sv_main)
n_noise = len(P["noise_files"]); n_rows = len(E["rows"])
if n_noise != 112 or n_rows != 112: bad.append(f"expected 112 noise files and 112 expected rows, found {n_noise} and {n_rows}")
b = P.get("batch", {})
if not (b.get("complete") is True and b.get("rows") == 112 and len(b.get("proofs", {})) == 112): bad.append("PINS.json batch section is not a complete 112-row batch")
for w in bad: print("   MISMATCH " + w)
if bad: sys.exit(1)
print(f"   program vkey {vkey}")
print(f"   guest ELF sha256 {elf_sha} ({elf_bytes} bytes), circuit {circ}, circuit key sha256 {g16}")
print(f"   constants blob sha256 {const_sha} ({const_bytes} bytes); expected identities sha256 {exp_sha}")
print(f"   chain log sha256 {chain_sha}, BLAKE3 {chain_b3}; 112 noise files, 112 expected rows, batch complete over 112 rows")
print(f"   outcome counts recorded in PINS.json: {b.get('outcome_counts')}")
PY
  ok "every pin agrees between this script, PINS.json and the frozen files"
}

fetch_repo() {
  step "fetch: repository package $PACKAGE_REL"
  if [ "$REFETCH" = 1 ] && [ -d "$REPO" ]; then note "--refetch: discarding $REPO"; rm -rf "$REPO"; fi
  if [ -f "$PKG/PINS.json" ]; then
    ok "package present at $PKG$([ -d "$REPO/.git" ] && echo " (git $(git -C "$REPO" rev-parse --short HEAD 2>/dev/null))")"
  elif [ -n "$FROM_LOCAL" ]; then
    local src="$FROM_LOCAL"
    [ -d "$src" ] || fail "--from-local $src is not a directory"
    mkdir -p "$REPO/proofs"
    if [ -f "$src/PINS.json" ]; then
      cp -a "$src" "$PKG"
      for f in README.md SHA256SUMS LICENSE; do [ -f "$src/../../$f" ] && cp -a "$src/../../$f" "$REPO/$f"; done
    elif [ -f "$src/$PACKAGE_REL/PINS.json" ]; then
      cp -a "$src/$PACKAGE_REL" "$PKG"
      for f in README.md SHA256SUMS LICENSE; do [ -f "$src/$f" ] && cp -a "$src/$f" "$REPO/$f"; done
    else
      fail "--from-local $src holds neither the package (PINS.json) nor a Dark Lantern checkout ($PACKAGE_REL/PINS.json)"
    fi
    ok "copied from the local tree $src (no network)"
  else
    need_cmd git "apt-get install git"
    note "sparse clone of $REPO_URL at $REF, only $PACKAGE_REL and the root files (blobs filtered)"
    rm -rf "$REPO"; mkdir -p "$REPO"
    git -C "$REPO" init -q
    git -C "$REPO" remote add origin "$REPO_URL"
    git -C "$REPO" sparse-checkout init --cone
    git -C "$REPO" sparse-checkout set "$PACKAGE_REL"
    git -C "$REPO" fetch -q --depth 1 --filter=blob:none origin "$REF" || fail "git fetch of $REF from $REPO_URL failed"
    git -C "$REPO" -c advice.detachedHead=false checkout -q FETCH_HEAD
    [ -f "$PKG/PINS.json" ] || fail "the tree at $REF carries no $PACKAGE_REL/PINS.json"
    ok "commit $(git -C "$REPO" rev-parse HEAD) ($(git -C "$REPO" log -1 --format=%cd --date=iso-strict)), $(git -C "$REPO" log -1 --format=%s | cut -c1-90)"
  fi
  check_ledger
  check_pins
  readme_digests
}

readme_digests() {
  # the repository's root README fixes the data-layer control digests and the package ledger digest; report what it says
  [ -f "$REPO/README.md" ] || { note "no repository root README.md here (a package-only copy); the data-layer control digests are not cross-checked against it"; return 0; }
  python3 - "$REPO/README.md" "$PKG/SHA256SUMS" "$DATA" <<'PY' || fail "a digest published in the repository's root README.md disagrees with the bytes here"
import re, sys, hashlib, os
readme, ledger, data = sys.argv[1:]
t = open(readme, encoding="utf-8", errors="replace").read()
paras = [p for p in t.split("\n\n") if "zkdiff_august_20260907" in p and "MANIFEST.jsonl" in p]
if not paras:
    print("   root README.md carries no provenance paragraph for this package yet (unpublished or pre-publication tree)"); sys.exit(0)
p = paras[0]
def grab(label):
    m = re.search(re.escape(label) + r"[^`]*\(`?(?:SHA-256 `)?([0-9a-f]{64})`", p)
    return m.group(1) if m else None
want = {"SHA256SUMS(package)": grab("`SHA256SUMS`"), "_control/MANIFEST.jsonl": grab("`_control/MANIFEST.jsonl`"),
        "_control/SHA256SUMS": grab("`_control/SHA256SUMS`"), "_control/RELEASE.json": grab("`_control/RELEASE.json`")}
def sha(path):
    h = hashlib.sha256(); h.update(open(path, "rb").read()); return h.hexdigest()
bad = 0
got = sha(ledger)
if want["SHA256SUMS(package)"]:
    print(f"   README: package SHA256SUMS digest {want['SHA256SUMS(package)']} -> {'matches' if got == want['SHA256SUMS(package)'] else 'DIFFERS from ' + got}")
    bad += got != want["SHA256SUMS(package)"]
for k in ("_control/MANIFEST.jsonl", "_control/SHA256SUMS", "_control/RELEASE.json"):
    f = os.path.join(data, k)
    if want[k] and os.path.exists(f):
        g = sha(f); print(f"   README: {k} digest {want[k]} -> {'matches the fetched object' if g == want[k] else 'DIFFERS from the fetched object ' + g}"); bad += g != want[k]
    elif want[k]:
        print(f"   README: {k} digest {want[k]} (object not fetched yet; checked after fetch)")
sys.exit(1 if bad else 0)
PY
}

fetch_data() {
  step "fetch: data-layer objects ($DATA_BASE)"
  local ctrl="$DATA/_control"; mkdir -p "$ctrl"
  local f
  for f in README.md _control/MANIFEST.jsonl _control/SHA256SUMS _control/RELEASE.json; do
    if [ -n "$DATA_FROM_LOCAL" ]; then
      [ -f "$DATA_FROM_LOCAL/$f" ] || fail "--data-from-local $DATA_FROM_LOCAL has no $f"
      cp -f "$DATA_FROM_LOCAL/$f" "$DATA/$f"
    else
      curl -fsSL --retry 5 --retry-all-errors -A "$UA" -o "$DATA/$f.part" "$DATA_BASE/$f" || fail "cannot fetch $DATA_BASE/$f"
      mv -f "$DATA/$f.part" "$DATA/$f"
    fi
  done
  ok "controls fetched: MANIFEST.jsonl sha256 $(sha "$ctrl/MANIFEST.jsonl"), SHA256SUMS sha256 $(sha "$ctrl/SHA256SUMS"), RELEASE.json sha256 $(sha "$ctrl/RELEASE.json")"
  # the controls must agree with each other and with the repository package's LARGE_FILES_SHA256SUMS
  python3 - "$DATA" "$PKG" "$DATA_PREFIX" <<'PY' || fail "the data-layer controls disagree with each other or with LARGE_FILES_SHA256SUMS"
import json, sys, hashlib, os
data, pkg, prefix = sys.argv[1:]
man = [json.loads(l) for l in open(f"{data}/_control/MANIFEST.jsonl") if l.strip()]
rel = json.load(open(f"{data}/_control/RELEASE.json"))
sums = {}
for l in open(f"{data}/_control/SHA256SUMS"):
    l = l.rstrip("\n")
    if l: sums[l[66:]] = l[:64]
bad = []
for m in man:
    if m["object_key"] != prefix + m["relative_path"]: bad.append(f"object key {m['object_key']} is not {prefix}{m['relative_path']}")
    if sums.get(m["relative_path"]) != m["sha256"]: bad.append(f"_control/SHA256SUMS disagrees with MANIFEST.jsonl for {m['relative_path']}")
if len(sums) != len(man): bad.append(f"_control/SHA256SUMS has {len(sums)} lines, MANIFEST.jsonl {len(man)}")
if rel.get("objects") != len(man): bad.append(f"RELEASE.json objects {rel.get('objects')} != {len(man)} manifest lines")
if rel.get("bytes") != sum(m["size"] for m in man): bad.append("RELEASE.json bytes != manifest byte total")
if rel.get("prefix") != prefix: bad.append(f"RELEASE.json prefix {rel.get('prefix')} != {prefix}")
if rel.get("draft") is not False: bad.append(f"RELEASE.json draft is {rel.get('draft')}")
by_path = {m["relative_path"]: m for m in man}
large = [l.rstrip("\n") for l in open(f"{pkg}/LARGE_FILES_SHA256SUMS") if l.strip()]
missing = 0
for l in large:
    s, p = l[:64], l[66:]
    m = by_path.get("repository_package_large_files/" + p)
    if m is None: missing += 1
    elif m["sha256"] != s: bad.append(f"data layer serves {p} with sha256 {m['sha256']}, the repository ledger says {s}")
if missing: bad.append(f"{missing} of {len(large)} large files are not in the data-layer manifest")
# front-matter copies are a convenience; report, never fail
diff = 0
for m in man:
    if m["relative_path"].startswith("repository_package_front_matter/"):
        f = os.path.join(pkg, m["relative_path"].split("/", 1)[1])
        if os.path.exists(f):
            h = hashlib.sha256(open(f, "rb").read()).hexdigest()
            diff += h != m["sha256"]
for w in bad: print("   MISMATCH " + w)
print(f"   {len(man)} objects, {sum(m['size'] for m in man):,} bytes under {prefix}; RELEASE.json staged {rel.get('staged_utc')}; {len(large)} large files all listed with matching digests")
if diff: print(f"   note: {diff} front-matter copies on the data layer differ from the repository package (the repository is the document of record)")
sys.exit(1 if bad else 0)
PY
  ok "controls consistent; every large file the repository names is served with the same digest"
  readme_digests
  # the large files themselves, placed at their package-relative paths; only what is missing or wrong is fetched
  local want; want=$( (cd "$PKG" && sha256sum -c LARGE_FILES_SHA256SUMS 2>/dev/null || true) | grep -v ': OK$' | sed 's/: [A-Za-z ]*$//' || true)
  local total; total=$(grep -c . "$PKG/LARGE_FILES_SHA256SUMS")
  if [ -z "$want" ]; then
    ok "all $total data-layer files already present at their package paths and matching LARGE_FILES_SHA256SUMS"
  else
    local n; n=$(say "$want" | grep -c .)
    note "$n of $total data-layer files to place"
    if [ -n "$DATA_FROM_LOCAL" ]; then
      while IFS= read -r p; do mkdir -p "$PKG/$(dirname "$p")"; cp -f "$DATA_FROM_LOCAL/repository_package_large_files/$p" "$PKG/$p" || fail "no $p in $DATA_FROM_LOCAL"; done <<<"$want"
    else
      local cfg; cfg=$(mktemp "$DL/curl_cfg.XXXXXX")
      while IFS= read -r p; do mkdir -p "$PKG/$(dirname "$p")"; printf 'url = "%s/repository_package_large_files/%s"\noutput = "%s"\n' "$DATA_BASE" "$p" "$PKG/$p" >> "$cfg"; done <<<"$want"
      if curl --help all 2>/dev/null | grep -q -- '--parallel'; then
        curl -fsS -L --retry 5 --retry-all-errors --parallel --parallel-max 16 -A "$UA" -K "$cfg" || warn "curl reported a failure; the ledger check decides"
      else
        curl -fsS -L --retry 5 --retry-all-errors -A "$UA" -K "$cfg" || warn "curl reported a failure; the ledger check decides"
      fi
      rm -f "$cfg"
    fi
    (cd "$PKG" && sha256sum -c --quiet LARGE_FILES_SHA256SUMS) || fail "a data-layer file is missing or differs from LARGE_FILES_SHA256SUMS (rerun fetch; it fetches only what is wrong)"
    ok "all $total data-layer files present and matching LARGE_FILES_SHA256SUMS ($(du -sh "$PKG/source/oracle_final" "$PKG/oracle/rows" "$PKG/oracle/rows_august" "$PKG/oracle/final/vectors" 2>/dev/null | awk '{s=s$1" "} END{print s}'))"
  fi
}

ensure_repo() { [ -f "$PKG/PINS.json" ] && [ -f "$OUT/ledger.ok" ] || { fetch_repo; : > "$OUT/ledger.ok"; }; }
ensure_large() { (cd "$PKG" && sha256sum -c --quiet LARGE_FILES_SHA256SUMS >/dev/null 2>&1) || fetch_data; }

cmd_fetch() {
  fetch_repo; : > "$OUT/ledger.ok"
  if [ "$REPO_ONLY" = 1 ]; then note "--repo-only: data-layer objects not fetched (parity needs them; nothing else does)"; else fetch_data; fi
}

# ---------------------------------------------------------------------------------------------------------------------
# quick: the vendored standalone verifier (sp1-verifier 6.4.0, no SP1 SDK, no ELF) on all 112 raw proofs
# ---------------------------------------------------------------------------------------------------------------------
cmd_quick() {
  ensure_repo; ensure_rust
  step "quick: Groth16 verification of 112 proofs under the pinned program key with the vendored standalone verifier"
  local sv="$PKG/tools/standalone_verifier" bin
  [ "$(sha "$sv/Cargo.toml")" = "$PIN_SV_CARGO_TOML" ] && [ "$(sha "$sv/Cargo.lock")" = "$PIN_SV_CARGO_LOCK" ] && [ "$(sha "$sv/src/main.rs")" = "$PIN_SV_MAIN_RS" ] || fail "standalone verifier sources differ from the vendored pins"
  bin="$sv/target/release/zeebeam-standalone-verifier"
  if [ ! -x "$bin" ]; then
    local t0; t0=$(date +%s)
    note "building the standalone verifier (209 locked crates: sp1-verifier 6.4.0 and sha2)"
    (cd "$sv" && CARGO_NET_OFFLINE=false cargo +"$HOST_RUST" build --release --locked -q 2>&1 | grep -v '^warning' || true)
    [ -x "$bin" ] || fail "the standalone verifier did not build"
    ok "built in $(elapsed "$t0"): $bin"
  fi
  mkdir -p "$OUT/quick"
  local r pad rc=0 t0; t0=$(date +%s)
  for r in $(seq $ROW_FIRST $ROW_LAST); do
    pad=$(printf %06d "$r")
    "$bin" "$PKG/proofs/row_${pad}_groth16_proof.bin" "$PKG/public_values/row_${pad}_public_values.bin" "$PIN_VKEY" > "$OUT/quick/row_${pad}.txt" 2>&1 || rc=1
  done
  python3 - "$PKG" "$OUT/quick" "$ROW_FIRST" "$ROW_LAST" <<'PY' || rc=1
import sys, os, json, hashlib
pkg, out, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
sys.path.insert(0, f"{pkg}/tools"); import decode_zbdiff01 as D
print(f"   {'row':>4} {'u':>4} {'off':>4} {'rule':<8} {'R_correct':>13} {'R_wrong':>13} {'D':>13} {'class':<8} {'clips':>5}  {'raw proof sha256':<16}  {'result'}")
okn = 0
for r in range(a, b + 1):
    pad = f"{r:06d}"
    txt = open(f"{out}/row_{pad}.txt").read().splitlines()
    verified = bool(txt) and txt[-1] == "VERIFIED" and "tamper_public_byte_87_rejected=true" in txt and "wrong_vkey_rejected=true" in txt
    okn += verified
    pv = open(f"{pkg}/public_values/row_{pad}_public_values.bin", "rb").read()
    d = D.decode(pv)
    psha = hashlib.sha256(open(f"{pkg}/proofs/row_{pad}_groth16_proof.bin", "rb").read()).hexdigest()
    print(f"   {d['row']:>4} {d['wrong_row']:>4} {d['offset']:>+4} {d['offset_rule']:<8} {d['r_correct']:>13} {d['r_wrong']:>13} {d['difference']:>+13} {d['outcome_class']:<8} {d['clip_events']:>5}  {psha[:16]}  {'VERIFIED (2 tamper controls rejected)' if verified else 'REJECTED'}")
print(f"   {okn}/{b - a + 1} proofs verified under {open(f'{out}/row_{a:06d}.txt').read().split('sp1_vkey_hash=')[1].split()[0] if okn else 'the pinned key'}")
sys.exit(0 if okn == b - a + 1 else 1)
PY
  [ "$rc" = 0 ] || fail "QUICK: a proof did not verify with the standalone verifier"
  ok "QUICK PASS in $(elapsed "$t0"): 112/112 Groth16 proofs verify under $PIN_VKEY with the circuit key embedded in sp1-verifier 6.4.0; the statements' identities are checked by verify"
}

# ---------------------------------------------------------------------------------------------------------------------
# build: cargo fetch with the pinned lockfiles, then the package's fail-closed reproducible build
# ---------------------------------------------------------------------------------------------------------------------
cargo_fetch_all() {
  if [ -f "$OUT/cargo_fetch.v2.ok" ] && [ "$REFETCH" = 0 ]; then ok "crates already fetched (stamp $OUT/cargo_fetch.v2.ok)"; return 0; fi
  local t0; t0=$(date +%s)
  note "cargo fetch --locked for the four lockfiles (the workspace's .cargo/config.toml is offline; overridden for this step only)"
  (cd "$S" && CARGO_NET_OFFLINE=false cargo fetch --locked -q) || fail "cargo fetch failed for script/"
  # sp1-core-executor-runner 6.4.0 builds its helper binary through a nested `cargo metadata` + `cargo build` inside the registry
  # copies of itself and of sp1-core-executor-runner-binary, each resolved from the Cargo.lock shipped in the crate (so the
  # nested tree is pinned by the outer lockfile's checksum); those two locks name crates the outer lockfile does not, so they
  # are fetched here or the offline build stops at "no matching package named `wasip3`"
  local c d
  for c in sp1-core-executor-runner-6.4.0 sp1-core-executor-runner-binary-6.4.0; do
    d=$(ls -d "$CARGO_HOME"/registry/src/*/"$c" 2>/dev/null | head -1)
    [ -n "$d" ] && [ -f "$d/Cargo.lock" ] || fail "cargo fetch left no registry copy of $c with its shipped Cargo.lock under $CARGO_HOME/registry/src"
    (cd "$d" && CARGO_NET_OFFLINE=false cargo fetch --locked -q) || fail "cargo fetch failed for the nested $c tree"
    note "nested $c: $(grep -c '^\[\[package\]\]' "$d/Cargo.lock") locked packages fetched"
  done
  # no --target here: sp1-build runs `cargo metadata` on the guest before building it, and metadata resolves every platform's
  # dependencies from the lockfile (r-efi and friends), so a target-filtered fetch leaves the offline build short of crates
  (cd "$PKG/source/armc-relation/program" && CARGO_NET_OFFLINE=false cargo +succinct fetch --locked -q) || fail "cargo +succinct fetch failed for program/"
  (cd "$PKG/source/armc-relation" && CARGO_NET_OFFLINE=false cargo fetch --locked -q) || fail "cargo fetch failed for the armc-relation workspace"
  (cd "$PKG/source/armc-int" && CARGO_NET_OFFLINE=false cargo fetch --locked -q) || fail "cargo fetch failed for armc-int/"
  : > "$OUT/cargo_fetch.v2.ok"
  ok "crates fetched in $(elapsed "$t0") with every lockfile unchanged (--locked)"
}

run_build() { # $1 = 0|1 (CUDA feature)
  ensure_repo; ensure_sp1; cargo_fetch_all
  local cuda=$1 t0; t0=$(date +%s)
  step "build: reproducible rebuild of the guest ELF and the four host binaries (CUDA=$cuda)"
  note "driver: source/armc-relation/build_reproducible.sh (offline, --locked, lockfiles compared before and after, ELF size / sha256 / vkey / circuit key asserted)"
  local rec_before; rec_before=$(ls -1 "$PKG/source/armc-relation/runs"/build_record_*.txt 2>/dev/null | wc -l)
  if ! (cd "$PKG/source/armc-relation" && CUDA=$cuda bash ./build_reproducible.sh) > "$OUT/build_cuda$cuda.stdout" 2>&1; then
    tail -40 "$OUT/build_cuda$cuda.stdout"; fail "build_reproducible.sh did not reproduce the pins (full output: $OUT/build_cuda$cuda.stdout; cargo log in source/armc-relation/runs/)"
  fi
  grep -E 'build wall|guest_elf_bytes|sp1_vkey=|sp1_circuit_version|BUILD_REPRODUCED_OK' "$OUT/build_cuda$cuda.stdout" | sed 's/^/   /'
  local rec; rec=$(ls -1t "$PKG/source/armc-relation/runs"/build_record_*.txt | head -1)
  [ "$(ls -1 "$PKG/source/armc-relation/runs"/build_record_*.txt | wc -l)" -gt "$rec_before" ] || fail "no new build record was written"
  grep -q '^BUILD_REPRODUCED_OK' "$rec" || fail "no BUILD_REPRODUCED_OK in $rec"
  # independent re-check of what the driver asserted
  [ -f "$ELF" ] || fail "no guest ELF at $ELF"
  [ "$(sha "$ELF")" = "$PIN_ELF_SHA" ] || fail "guest ELF sha256 $(sha "$ELF") != $PIN_ELF_SHA"
  [ "$(stat -c %s "$ELF")" = "$PIN_ELF_BYTES" ] || fail "guest ELF is $(stat -c %s "$ELF") bytes, not $PIN_ELF_BYTES"
  grep -q "^sp1_vkey=$PIN_VKEY\$" "$rec" || fail "the build record's vkey is not $PIN_VKEY"
  local id; id=$("$S/target/release/zkdiff-verify" --identity)
  say "$id" | grep -q "\"groth16_vk_sha256\": \"$PIN_GROTH16_VK_SHA\"" || fail "zkdiff-verify embeds circuit key $(say "$id" | grep -o '"groth16_vk_sha256": "[0-9a-f]*"'), not $PIN_GROTH16_VK_SHA"
  say "$id" | grep -q "\"guest_elf_sha256\": \"$PIN_ELF_SHA\"" || fail "zkdiff-verify embeds another ELF"
  say "$id" | grep -q "\"sp1_circuit_version\": \"$PIN_CIRCUIT_VERSION\"" || fail "zkdiff-verify is not circuit $PIN_CIRCUIT_VERSION"
  echo "$cuda" > "$OUT/build.cuda"; : > "$OUT/build.ok"; echo "$rec" > "$OUT/build.record"
  ok "BUILD PASS in $(elapsed "$t0"): ELF sha256 $PIN_ELF_SHA, $PIN_ELF_BYTES bytes; vkey $PIN_VKEY (derived from the rebuilt ELF by zkdiff-ceremony); embedded circuit key $PIN_GROTH16_VK_SHA ($PIN_CIRCUIT_VERSION); record $rec"
}
cmd_build() { run_build "${CUDA:-0}"; }
ensure_built() { [ -x "$S/target/release/zkdiff-verify" ] && [ -f "$OUT/build.ok" ] || run_build "${CUDA:-0}"; }
ensure_built_cuda() { { [ -x "$S/target/release/zkdiff-batch" ] && [ -f "$OUT/build.ok" ] && [ "$(cat "$OUT/build.cuda" 2>/dev/null)" = 1 ]; } || run_build 1; }
build_record() { cat "$OUT/build.record" 2>/dev/null || ls -1t "$PKG/source/armc-relation/runs"/build_record_*.txt | head -1; }

# ---------------------------------------------------------------------------------------------------------------------
# verify: the package's acceptance verifier on all 112 proofs, the controls, the raw form, the noise and chain-log digests
# ---------------------------------------------------------------------------------------------------------------------
cmd_verify() {
  ensure_built
  local V="$S/target/release/zkdiff-verify" t0; t0=$(date +%s)
  step "verify: acceptance verification of 112 proofs (Groth16 under the pinned key and circuit, then every frozen identity)"
  mkdir -p "$OUT/verify"
  local r pad rc=0
  for r in $(seq $ROW_FIRST $ROW_LAST); do
    pad=$(printf %06d "$r")
    "$V" --proof "$PKG/proofs/row_${pad}_groth16.bin" --expect "$EXPECT" --report "$OUT/verify/row_${pad}.json" > "$OUT/verify/row_${pad}.stdout" 2>&1 || rc=1
  done
  python3 - "$PKG" "$OUT/verify" "$ROW_FIRST" "$ROW_LAST" <<'PY' || rc=1
import sys, os, json, hashlib
pkg, out, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
P = json.load(open(f"{pkg}/PINS.json")); batch = P["batch"]["proofs"]
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
print(f"   {'row':>4} {'u':>4} {'off':>4} {'rule':<8} {'R_correct':>13} {'R_wrong':>13} {'D':>13} {'class':<8} {'clips':>5} {'noise BLAKE3':<16} {'checks':>6}  result")
acc = 0; bad = []
classes = {"positive": 0, "zero": 0, "negative": 0}
for r in range(a, b + 1):
    pad = f"{r:06d}"; rp = f"{out}/row_{pad}.json"
    if not os.path.exists(rp): bad.append(f"row {r}: no report"); print(f"   {r:>4} no report"); continue
    rep = json.load(open(rp)); st = rep.get("statement", {}); ac = rep.get("acceptance", {})
    ok = rep.get("ok") is True and ac.get("accepted") is True and rep.get("version_check") == "PASS"
    checks = ac.get("checks", []); npass = sum(1 for c in checks if c.get("status") == "PASS")
    rec = json.load(open(f"{pkg}/receipts/row_{pad}_receipt.json"))
    pv_sha = sha(f"{pkg}/public_values/row_{pad}_public_values.bin"); raw_sha = sha(f"{pkg}/proofs/row_{pad}_groth16_proof.bin")
    pin = batch[str(r)]
    for what, got, want in (("framed proof sha256 vs PINS", rep.get("artifact_sha256"), pin["framed_sha256"]),
                            ("public values sha256 vs PINS", rep.get("public_values_sha256"), pin["public_values_sha256"]),
                            ("public values file vs PINS", pv_sha, pin["public_values_sha256"]),
                            ("raw proof file vs PINS", raw_sha, pin["raw_sha256"]),
                            ("public values vs receipt", rep.get("public_values_sha256"), rec["public_values_sha256"]),
                            ("R_correct vs receipt", st.get("r_correct"), rec["r_correct"]), ("R_wrong vs receipt", st.get("r_wrong"), rec["r_wrong"]),
                            ("D vs receipt", st.get("difference"), rec["difference"]), ("class vs receipt", st.get("outcome_class"), rec["outcome_class"]),
                            ("clip events vs receipt", st.get("clip_events"), rec["clip_events"]), ("class vs PINS", st.get("outcome_class"), pin["outcome"]),
                            ("row", st.get("row"), r)):
        if got != want: ok = False; bad.append(f"row {r}: {what}: {got} != {want}")
    if ok:
        acc += 1; classes[st["outcome_class"]] = classes.get(st["outcome_class"], 0) + 1
    print(f"   {r:>4} {st.get('wrong_row', ''):>4} {st.get('offset', 0):>+4} {str(st.get('offset_rule', '')):<8} {st.get('r_correct', ''):>13} {st.get('r_wrong', ''):>13} {st.get('difference', 0):>+13} {str(st.get('outcome_class', '')):<8} {st.get('clip_events', ''):>5} {str(st.get('noise_blake3', ''))[:16]:<16} {npass:>3}/{len(checks):<2}  {'ACCEPTED' if ok else 'REFUSED ' + str(ac.get('failed_check') or rep.get('version_check'))}")
for w in bad[:20]: print("   MISMATCH " + w)
print(f"   {acc}/{b - a + 1} accepted; outcome classes {classes}; every accepted statement equals its receipt and its PINS.json entry")
sys.exit(0 if acc == b - a + 1 and not bad else 1)
PY
  [ "$rc" = 0 ] || fail "VERIFY: a proof was refused or a statement disagrees with its receipt or PINS.json"
  # proof-level and policy-level negative controls on one row
  note "negative controls on row 600 (mutated public fields, proof bytes and program key must be rejected; mutated expected identities must be refused at the named check)"
  "$V" --proof "$PKG/proofs/row_000600_groth16.bin" --expect "$EXPECT" --controls --report "$OUT/verify/controls_000600.json" > "$OUT/verify/controls_000600.stdout" 2>&1 || fail "a control did not behave (see $OUT/verify/controls_000600.json)"
  python3 -c "
import json,sys; r=json.load(open(sys.argv[1])); cs=r['controls']; assert r['controls_all_behaved'] is True
print(f\"   {len(cs)} controls, all behaved: \" + ', '.join(sorted(set(c.get('layer', c.get('kind','')) for c in cs)) or ['see report']))" "$OUT/verify/controls_000600.json" || fail "controls report unreadable"
  # the raw form: 356-byte proof plus 752 public bytes, no framing
  "$V" --proof-bytes "$PKG/proofs/row_000600_groth16_proof.bin" --public "$PKG/public_values/row_000600_public_values.bin" --expect "$EXPECT" --report "$OUT/verify/raw_000600.json" > /dev/null 2>&1 || fail "the raw form of row 600 was refused"
  ok "raw form accepted: proofs/row_000600_groth16_proof.bin (356 bytes) + public_values/row_000600_public_values.bin (752 bytes)"
  # the shipped noise files and chain log against the pins, by sha256 (PINS.json) and, when b3sum is here, by BLAKE3 (expected identities)
  python3 - "$PKG" <<'PY' > "$OUT/verify/noise_sha256sums.txt"
import json, sys
P = json.load(open(f"{sys.argv[1]}/PINS.json"))
for r, v in sorted(P["noise_files"].items(), key=lambda kv: int(kv[0])): print(f"{v['sha256']}  {v['file'] if v['file'].startswith('source/') else 'source/' + v['file']}")   # PINS paths are package-relative since 8 Sep
PY
  (cd "$PKG" && sha256sum -c --quiet "$OUT/verify/noise_sha256sums.txt") || fail "a noise file differs from PINS.json noise_files"
  ok "112 noise files match PINS.json by sha256"
  if command -v b3sum >/dev/null 2>&1; then
    [ "$(b3sum --no-names "$CHAIN")" = "$PIN_CHAIN_LOG_BLAKE3" ] || fail "chain log BLAKE3 is $(b3sum --no-names "$CHAIN"), the pin says $PIN_CHAIN_LOG_BLAKE3"
    python3 - "$PKG" <<'PY' > "$OUT/verify/noise_b3sums.txt"
import json, sys
E = json.load(open(f"{sys.argv[1]}/source/expected_identities_august.json"))
for r, v in sorted(E["rows"].items(), key=lambda kv: int(kv[0])): print(f"{v['noise_blake3']}  source/noise_august/noise_{int(r):06d}.i16")
PY
    (cd "$PKG" && b3sum --check --quiet "$OUT/verify/noise_b3sums.txt") || fail "a noise file's BLAKE3 differs from the expected identities table"
    ok "b3sum: chain log BLAKE3 $PIN_CHAIN_LOG_BLAKE3 and 112 noise-file BLAKE3 digests match the frozen expected identities"
  else
    note "b3sum absent: BLAKE3 of the noise files is enforced inside the proofs and re-derived by execute; the independent tool check is skipped"
  fi
  ok "VERIFY PASS in $(elapsed "$t0"): 112/112 proofs accepted under vkey $PIN_VKEY, circuit $PIN_CIRCUIT_VERSION (key $PIN_GROTH16_VK_SHA), constants $PIN_CONSTANTS_SHA; controls behaved; reports in $OUT/verify/"
}

# ---------------------------------------------------------------------------------------------------------------------
# execute / synthetic / parity
# ---------------------------------------------------------------------------------------------------------------------
check_row() { [[ "$1" =~ ^[0-9]+$ ]] && [ "$1" -ge $ROW_FIRST ] && [ "$1" -le $ROW_LAST ] || fail "ROW must be an integer in $ROW_FIRST..$ROW_LAST"; }

ensure_frame() { # row; sets FRAME: --frame, else the shipped row-600 frame, else the published frame (data layer or --data-from-local), sha256-checked against FRAMES.md; returns 1 if none can be had
  local r=$1 pad; pad=$(printf %06d "$r")
  [ -n "$FRAME" ] && return 0
  if [ "$r" = 600 ] && [ -f "$PKG/capsule/reexecute/frame_000600.raw" ]; then
    FRAME="$PKG/capsule/reexecute/frame_000600.raw"; note "row 600: the frame shipped in capsule/reexecute/ is used"; return 0
  fi
  local want; want=$(grep -E "^\| $r \| " "$PKG/FRAMES.md" | awk -F'|' '{print $6}' | tr -d ' `')
  [ "${#want}" = 64 ] || { note "FRAMES.md carries no digest for row $r"; return 1; }
  local dest="$OUT/frames_dl/frame_$pad.raw"; mkdir -p "$OUT/frames_dl"
  if [ -f "$dest" ] && [ "$(sha "$dest")" = "$want" ]; then FRAME=$dest; ok "frame $pad present, sha256 $want"; return 0; fi
  if [ -n "$DATA_FROM_LOCAL" ]; then
    [ -f "$DATA_FROM_LOCAL/frames/frame_$pad.raw" ] || { note "--data-from-local $DATA_FROM_LOCAL has no frames/frame_$pad.raw"; return 1; }
    cp -f "$DATA_FROM_LOCAL/frames/frame_$pad.raw" "$dest"
    [ "$(sha "$dest")" = "$want" ] || fail "frames/frame_$pad.raw in $DATA_FROM_LOCAL hashes to $(sha "$dest"), FRAMES.md says $want"
  else
    fetch_pinned "$DATA_BASE/frames/frame_$pad.raw" "$dest" "$want" 24472000 || return 1
  fi
  FRAME=$dest
}

frames_dir_for() { # row; symlinks --frame into a frames dir with the name the batch driver expects; prints the dir
  local r=$1 pad; pad=$(printf %06d "$r")
  [ -f "$FRAME" ] || fail "--frame $FRAME is not a file"
  [ "$(stat -c %s "$FRAME")" = 24472000 ] || fail "--frame $FRAME is $(stat -c %s "$FRAME") bytes; a raw frame is 24,472,000 bytes"
  mkdir -p "$OUT/frames"; ln -sfn "$(cd "$(dirname "$FRAME")" && pwd)/$(basename "$FRAME")" "$OUT/frames/frame_${pad}.raw"
  printf '%s' "$OUT/frames"
}

cmd_synthetic() {
  ensure_built
  local t0; t0=$(date +%s)
  step "synthetic: the complete guest (the pinned ELF) in the SP1 executor on the shipped 16-row synthetic session, row 5 against wrong row 7"
  note "witness: source/vectors_relation/e2e (raw frame regenerated from its PRNG seed; real quicknet beacons borrowed from the August chain log); expected binding bytes from the Python oracle"
  mkdir -p "$OUT/synthetic"
  if ! /usr/bin/time -v "$S/target/release/zkdiff-execute" --witness-dir "$PKG/source/vectors_relation/e2e" --raw synthetic:a --blob "$BLOB" \
        --expected "$PKG/source/vectors_relation/e2e/expected_public_zbdiff01.bin" > "$OUT/synthetic/stdout" 2> "$OUT/synthetic/stderr"; then
    grep -E 'MISMATCH|panicked|rejected' "$OUT/synthetic/stderr" | head -5; fail "zkdiff-execute failed on the synthetic session (see $OUT/synthetic/)"
  fi
  grep -q '^verified_public_values=true' "$OUT/synthetic/stdout" || fail "the guest's public values differ from the native re-execution"
  grep -q '^oracle=native_reexecution+python_oracle_binding_fields checked=651' "$OUT/synthetic/stdout" || fail "the Python oracle's 651 binding bytes were not all checked"
  grep -q "guest_elf_sha256=$PIN_ELF_SHA" "$OUT/synthetic/stdout" || fail "zkdiff-execute embeds another ELF"
  grep -E '^(row=|guest_elf_bytes=|oracle=|total_instruction_count|total_syscall_count|host_elapsed_ms)' "$OUT/synthetic/stdout" | sed 's/^/   /'
  grep -E '^oracle_note=row' "$OUT/synthetic/stdout" | sed 's/^oracle_note=/   statement: /'
  grep -E 'Maximum resident|Elapsed \(wall' "$OUT/synthetic/stderr" | sed 's/^\s*/   /'
  ok "SYNTHETIC PASS in $(elapsed "$t0"): the pinned guest executed end to end on the CPU; every one of the 752 public bytes equals the native re-execution and the 651 binding bytes equal the Python oracle"
}

cmd_execute() {
  local r=${ARG1:-600}; check_row "$r"
  ensure_built
  local pad t0; pad=$(printf %06d "$r"); t0=$(date +%s)
  local B="$S/target/release/zkdiff-batch" rec; rec=$(build_record)
  step "execute: August row $r, frame-independent legs (chain log, beacons, tree, noise) natively"
  ensure_frame "$r" || note "no frame for row $r (none given, none shipped, none fetched): the frame-dependent legs stop and the synthetic session runs instead"
  local fd=""; [ -n "$FRAME" ] && fd=$(frames_dir_for "$r")
  rm -rf "$OUT/prepare_$r"; mkdir -p "$OUT/prepare_$r"
  "$B" prepare --chain-log "$CHAIN" --rows "$r..$r" --noise-dir "$NOISE" --blob "$BLOB" --expect "$EXPECT" --build-record "$rec" --out "$OUT/prepare_$r" ${fd:+--frames-dir "$fd"} > "$OUT/prepare_$r/stdout" 2> "$OUT/prepare_$r/stderr" || { tail -5 "$OUT/prepare_$r/stderr"; fail "zkdiff-batch prepare failed for row $r"; }
  python3 - "$OUT/prepare_$r/row_$pad/receipt.json" "$FRAME" <<'PY' || fail "prepare of row $r did not end as expected (see $OUT/prepare_$r/)"
import json, sys
rec = json.load(open(sys.argv[1])); frame = sys.argv[2]
print(f"   status={rec['status']} offset={rec['offset']:+d} rule={rec['offset_rule']} wrong_row={rec['wrong_row']} raw_blake3_expected={rec.get('raw_blake3_expected')}")
for n in rec.get("notes", []): print("   " + n)
if frame:
    assert rec["status"] == "prepared_native", rec["status"]; assert rec["acceptance"]["accepted"] is True, rec["acceptance"].get("failed_check")
    print(f"   native statement accepted ({sum(1 for c in rec['acceptance']['checks'] if c['status']=='PASS')} checks): R_correct {rec['r_correct']} R_wrong {rec['r_wrong']} D {rec['difference']:+d} ({rec['outcome_class']}), clip events {rec['clip_events']}")
else:
    assert rec["status"] == "pending_frame", rec["status"]
    print("   no frame for this row here, so the frame-dependent legs (frame hash, reduction, two evaluations) stop; the published frames are on the data layer (FRAMES.md)")
PY
  ok "row $r prepared: beacons verified and bound, chain advance and both emission renders reproduce the chain log, noise BLAKE3 equals the frozen table"
  if [ -z "$FRAME" ]; then
    note "no frame for row $r: running the complete guest on the shipped synthetic session instead"
    cmd_synthetic
    return 0
  fi
  step "execute: August row $r through the complete guest in the SP1 executor (about 14.4 G instructions, 6 to 7 minutes, 15 to 17 GB of RAM)"
  rm -rf "$OUT/execute_$r"; mkdir -p "$OUT/execute_$r"
  if ! /usr/bin/time -v "$B" execute --chain-log "$CHAIN" --rows "$r..$r" --frames-dir "$fd" --noise-dir "$NOISE" --blob "$BLOB" --expect "$EXPECT" --build-record "$rec" --out "$OUT/execute_$r" > "$OUT/execute_$r/stdout" 2> "$OUT/execute_$r/stderr"; then
    grep -E 'MISMATCH|panicked|rejected|differs' "$OUT/execute_$r/stderr" | head -5; fail "zkdiff-batch execute failed for row $r (see $OUT/execute_$r/)"
  fi
  grep -q "^row=$r .*status=executed" "$OUT/execute_$r/stdout" || fail "row $r did not reach status=executed"
  python3 - "$OUT/execute_$r/row_$pad/receipt.json" "$PKG/receipts/row_${pad}_receipt.json" <<'PY' || fail "the executed statement of row $r differs from the published receipt"
import json, sys
rec, pub = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
assert rec["acceptance"]["accepted"] is True, rec["acceptance"].get("failed_check")
for k in ("r_correct", "r_wrong", "difference", "outcome_class", "clip_events", "public_values_sha256"):
    assert rec[k] == pub[k], (k, rec[k], pub[k])
print(f"   R_correct {rec['r_correct']}  R_wrong {rec['r_wrong']}  D {rec['difference']:+d} ({rec['outcome_class']})  clip events {rec['clip_events']}")
print(f"   instructions {rec['total_instruction_count']:,}  syscalls {rec['total_syscall_count']:,}  oracle {rec['oracle_mode']}  host peak RSS {rec.get('host_peak_rss_kib', 0)/1048576:.1f} GiB")
print(f"   public values sha256 {rec['public_values_sha256']} == the published receipt's; acceptance {sum(1 for c in rec['acceptance']['checks'] if c['status']=='PASS')} checks PASS")
PY
  cmp -s "$OUT/execute_$r/row_$pad/public_values.bin" "$PKG/public_values/row_${pad}_public_values.bin" || fail "the executed 752 public bytes differ from public_values/row_${pad}_public_values.bin"
  grep -E 'Maximum resident|Elapsed \(wall' "$OUT/execute_$r/stderr" | sed 's/^\s*/   /'
  ok "EXECUTE PASS in $(elapsed "$t0"): row $r re-executed on the CPU; its 752 public bytes are byte-identical to the published statement the proof commits to"
}

cmd_parity() {
  ensure_repo; ensure_rust; ensure_large
  [ -f "$OUT/cargo_fetch.v2.ok" ] || { ensure_sp1; cargo_fetch_all; }
  local t0; t0=$(date +%s)
  step "parity: the Rust integer kernels and the relation against the Python oracle's vectors (cargo test, both workspaces)"
  note "a test that stops on a data-layer file that is not in place (an August oracle set) or on a raw frame is reported as ABSENT, not failed; every other test must pass (with the data-layer files placed, every test passes)"
  mkdir -p "$OUT/parity"
  (cd "$PKG/source/armc-int" && cargo test --release --offline --no-fail-fast) > "$OUT/parity/armc-int.log" 2>&1 || true
  (cd "$PKG/source/armc-relation" && cargo test --release --offline --no-fail-fast) > "$OUT/parity/armc-relation.log" 2>&1 || true
  python3 - "$OUT/parity/armc-int.log" "$OUT/parity/armc-relation.log" <<'PY' || fail "PARITY: a test failed for a reason other than an absent data-layer file (logs: $OUT/parity/)"
import re, sys
AUGUST_SET = re.compile(r"oracle_final/int(?:16|8)_august_")
ABSENT = re.compile(r"missing|No such file or directory")
def is_held(block):
    # an August oracle set that has not been placed from the data layer, or a raw frame: a test that stops on one of them is ABSENT, not failed
    return bool((AUGUST_SET.search(block) and ABSENT.search(block)) or ("frames_august/" in block and ABSENT.search(block)))
total_pass = total_fail = total_held = 0
for log in sys.argv[1:]:
    t = open(log, errors="replace").read()
    results = re.findall(r"^test (\S+) \.\.\. (ok|FAILED|ignored)$", t, re.M)
    blocks = {m.group(1): m.group(2) for m in re.finditer(r"^---- (\S+) stdout ----\n(.*?)(?=^---- \S+ stdout ----|^failures:|\Z)", t, re.M | re.S)}
    p = sum(1 for _, s in results if s == "ok"); held = []; failed = []
    for name, s in results:
        if s == "FAILED":
            (held if is_held(blocks.get(name, "")) else failed).append(name)
    compile_error = "error[E" in t or "could not compile" in t
    print(f"   {log.split('/')[-1]:<20} passed {p:>3}  absent {len(held):>2}  failed {len(failed):>2}" + ("  COMPILE ERROR" if compile_error else ""))
    for n in held: print(f"      ABSENT {n}  (stops on a data-layer file not placed here, or a raw frame; LARGE_FILES.md, FRAMES.md)")
    for n in failed:
        print(f"      FAILED {n}"); print("         " + (blocks.get(n, "").strip().splitlines() or ["?"])[-1][:160])
    total_pass += p; total_fail += len(failed) + int(compile_error); total_held += len(held)
print(f"   total: {total_pass} passed, {total_held} absent, {total_fail} failed")
sys.exit(1 if total_fail or total_pass == 0 else 0)
PY
  ok "PARITY PASS in $(elapsed "$t0"): every kernel, fixture, relation-vector and oracle test that has its data passes on the published tree; tests whose data-layer files are absent are reported, not silently skipped"
}

# ---------------------------------------------------------------------------------------------------------------------
# prove: one fresh Groth16 proof on a CUDA GPU, then cold acceptance and byte comparison with the published statement
# ---------------------------------------------------------------------------------------------------------------------
cmd_prove() {
  local r=${ARG1:-600}; check_row "$r"
  ensure_frame "$r" || fail "prove needs the row's raw frame: pass --frame PATH, or let the script fetch the published frame from the data layer (FRAMES.md; --data-from-local for a local copy)"
  ensure_gpu; ensure_built_cuda
  local pad t0 B rec fd; pad=$(printf %06d "$r"); t0=$(date +%s); B="$S/target/release/zkdiff-batch"; rec=$(build_record); fd=$(frames_dir_for "$r")
  step "prove: August row $r on CUDA device $DEVICE (the timing pilot took 45.9 min on one A100-SXM4-80GB alone; the batch 61 to 67 min with eight processes sharing a node; VRAM peak about 28.5 GiB)"
  local o="$OUT/prove_$r"; rm -rf "$o"; mkdir -p "$o"
  nvidia-smi -i "$DEVICE" --query-gpu=index,uuid,name,driver_version,memory.total,memory.used --format=csv | tee "$o/gpu_identity.csv" | sed 's/^/   /'
  nvidia-smi -i "$DEVICE" --query-gpu=timestamp,memory.used,memory.total,utilization.gpu --format=csv -l 30 > "$o/gpu_mem.csv" 2>&1 &
  local sidecar=$!
  set +e
  /usr/bin/time -v "$B" prove --prover cuda --device "$DEVICE" --cycle-limit "$CYCLE_LIMIT" --chain-log "$CHAIN" --rows "$r..$r" --frames-dir "$fd" --noise-dir "$NOISE" \
      --blob "$BLOB" --expect "$EXPECT" --build-record "$rec" --out "$o" > "$o/prove.stdout" 2> "$o/prove.stderr"
  local rc=$?
  set -e
  kill "$sidecar" 2>/dev/null || true
  [ "$rc" = 0 ] || note "zkdiff-batch exited $rc (the pinned sp1-cuda client panics in a destructor after the manifest is written; the receipt and the cold verification below decide)"
  grep -q "^row=$r .*status=proved" "$o/prove.stdout" || { tail -20 "$o/prove.stderr"; fail "row $r did not reach status=proved (see $o/)"; }
  local proof="$o/row_$pad/row_${pad}_groth16.bin" V="$S/target/release/zkdiff-verify"
  [ -f "$proof" ] || fail "no proof artifact at $proof"
  "$V" --proof "$proof" --expect "$EXPECT" --report "$o/row_${pad}.verify.json" > /dev/null 2>&1 || fail "the fresh proof of row $r was refused by the acceptance verifier"
  cmp -s "$o/row_$pad/row_${pad}_public_values.bin" "$PKG/public_values/row_${pad}_public_values.bin" || fail "the fresh statement differs from public_values/row_${pad}_public_values.bin"
  python3 - "$o/row_$pad/receipt.json" "$o/gpu_mem.csv" "$o/prove.stderr" <<'PY' || fail "the fresh receipt of row $r is not proved and accepted"
import json, sys, re
rec = json.load(open(sys.argv[1]))
assert rec["status"] == "proved" and rec["acceptance"]["accepted"] is True
print(f"   R_correct {rec['r_correct']}  R_wrong {rec['r_wrong']}  D {rec['difference']:+d} ({rec['outcome_class']})  clip events {rec['clip_events']}")
print(f"   prove_elapsed_ms {rec['prove_elapsed_ms']:,} = {rec['prove_elapsed_ms']/60000:.1f} min; setup_elapsed_ms {rec.get('setup_elapsed_ms')}; proof {rec['proof_bytes']} bytes (raw {rec['proof_raw_bytes']}); proof sha256 {rec['proof_sha256']}")
try:
    peak = max(int(l.split(",")[1].split()[0]) for l in open(sys.argv[2]) if re.match(r"\d{4}/", l)); print(f"   GPU memory peak (30 s samples) {peak} MiB")
except Exception: pass
for l in open(sys.argv[3], errors="replace"):
    if "Maximum resident" in l or "Elapsed (wall" in l: print("   " + l.strip())
PY
  ok "PROVE PASS in $(elapsed "$t0"): a fresh Groth16 proof of row $r verifies and is accepted cold under the pinned identities, and its 752 public bytes are byte-identical to the published statement (the proof bytes differ, as Groth16 proofs are randomised)"
}

# ---------------------------------------------------------------------------------------------------------------------
# toolchain / all
# ---------------------------------------------------------------------------------------------------------------------
cmd_toolchain() {
  case "${ARG1:-sp1}" in
    rust) ensure_rust;; sp1) ensure_sp1;; gpu) ensure_gpu;; *) fail "toolchain takes rust, sp1 or gpu";;
  esac
  ok "toolchain ready"
}

cmd_all() {
  local t0; t0=$(date +%s)
  cmd_fetch
  run_build "${CUDA:-0}"
  cmd_verify
  cmd_quick
  ARG1=${ARG1:-600}; cmd_execute
  if [ "$REPO_ONLY" = 1 ]; then note "parity skipped (--repo-only)"; else cmd_parity; fi
  if [ "$NO_PROVE" = 1 ]; then note "prove skipped (--no-prove)"
  elif ! ensure_frame "${ARG1:-600}"; then note "prove skipped: no frame for the row (none given, none shipped, none fetched)"
  elif ! have_gpu; then note "prove skipped: no CUDA GPU visible"
  else cmd_prove; fi
  ok "ALL DONE in $(elapsed "$t0"); log $LOGFILE"
}

environment_summary
case "$CMD" in
  fetch) cmd_fetch;;
  quick) cmd_quick;;
  build) cmd_build;;
  verify) cmd_verify;;
  execute) cmd_execute;;
  synthetic) cmd_synthetic;;
  parity) cmd_parity;;
  prove) cmd_prove;;
  all) cmd_all;;
  toolchain) cmd_toolchain;;
  *) say "unknown command: $CMD"; sed -n '2,32p' "$0"; exit 2;;
esac
