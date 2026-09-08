#!/bin/bash
# Fail-closed reproducible build of the zkdiff guest ELF and the four host binaries (G2-D; Astra r5 finding 5 applied).
# Exits non-zero unless: cargo itself exits 0 (its status is preserved, nothing is `|| true`d), the lockfiles are
# byte-identical before and after the build, exactly one guest ELF exists and was (re)built during this run, every host
# binary was (re)built during this run, the ELF's size / SHA-256 / SP1 vkey equal the pins below, and no machine path is
# embedded. Records beside the log: the exact command, features and environment, the installed compiler identities, the
# lock and source hashes (LC_ALL=C collation, so the development machine and the node produce the same list digest), the prover server and
# circuit identities when present on the box, the embedded circuit verifier key, the four host binary hashes and the
# asserted ELF / vkey. The complete cargo output is kept in runs/build_log_<stamp>.txt. Nothing is deleted: the guest
# rebuild is forced by touching its entry point (sp1-build reruns on source mtime) and proven by the ELF's mtime being
# later than the run's start; the host binaries likewise.
#   usage: build_reproducible.sh [--pin]     (--pin: print the observed values as new pins instead of asserting)
#   env:   CUDA=1 adds --features cuda (node build); the development machine builds without it.
set -euo pipefail
readonly EXPECT_ELF_SHA="51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc"
readonly EXPECT_VKEY="0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027"
readonly EXPECT_ELF_BYTES="396200"
readonly EXPECT_GROTH16_VK_SHA="4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696"   # sp1-verifier 6.4.0 = circuits/groth16/v6.1.0
PIN_MODE=0; [ "${1:-}" = "--pin" ] && PIN_MODE=1
R=$(cd "$(dirname "$0")" && pwd)                       # armc-relation/
G2=$(cd "$R/.." && pwd)                                # g2_guest/
S=$R/script
export CARGO_NET_OFFLINE=true PATH="$HOME/.sp1/bin:$PATH" LC_ALL=C
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
REC=$R/runs/build_record_$STAMP.txt
LOG=$R/runs/build_log_$STAMP.txt
mkdir -p "$R/runs"
START=$(mktemp "$R/runs/.build_start_XXXXXX")
trap 'rm -f "$START"' EXIT
FEAT=""; [ "${CUDA:-0}" = "1" ] && FEAT="--features cuda"
BINS="zkdiff-execute zkdiff-ceremony zkdiff-batch zkdiff-verify"
BIN_ARGS=""; for b in $BINS; do BIN_ARGS="$BIN_ARGS --bin $b"; done
fail() { echo "BUILD_FAILED: $1"; exit "$2"; }
{
echo "driver=$0 driver_sha256=$(sha256sum "$0" | cut -c1-64)"
echo "date_utc=$STAMP host=$(hostname) kernel=$(uname -srm) glibc=$(ldd --version 2>/dev/null | head -1)"
echo "cargo_config=$R/.cargo/config.toml ($(grep -v '^#' "$R/.cargo/config.toml" | tr -d '\n' | tr -s ' '))"
echo "== command"
echo "cd $S && touch ../program/src/main.rs && cargo build --release --offline --locked $FEAT$BIN_ARGS"
echo "== environment"
echo "CUDA=${CUDA:-0} features=${FEAT:-<none>} CARGO_NET_OFFLINE=$CARGO_NET_OFFLINE LC_ALL=$LC_ALL RUSTFLAGS=${RUSTFLAGS:-<unset>} CARGO_HOME=${CARGO_HOME:-$HOME/.cargo} CARGO_BUILD_JOBS=${CARGO_BUILD_JOBS:-<default>} SP1_CIRCUIT_VERSION_env=${SP1_CIRCUIT_VERSION:-<unset>}"
echo "guest remap: --remap-path-prefix \$CARGO_HOME=/cargo and $G2=/g2 (script/build.rs); guest --locked"
echo "== toolchains"
rustc -vV | sed 's/^/host: /'; cargo -V | sed 's/^/host: /'
rustc +succinct -vV | sed 's/^/succinct: /'
if cargo prove --version >/dev/null 2>&1; then cargo prove --version | sed 's/^/cargo-prove: /'; else echo "cargo-prove: (not on PATH)"; fi
echo "cargo_prove_sha256=$(sha256sum "$HOME/.sp1/bin/cargo-prove" | cut -c1-64)"
[ -f "$HOME/.sp1/rust-toolchain-x86_64-unknown-linux-gnu.tar.gz" ] && echo "succinct_toolchain_tarball_sha256=$(sha256sum "$HOME/.sp1/rust-toolchain-x86_64-unknown-linux-gnu.tar.gz" | cut -c1-64)"
echo "== prover server and circuit artefacts (when present on this box)"
if [ -x "$HOME/.sp1/bin/sp1-gpu-server" ]; then
  echo "sp1_gpu_server_sha256=$(sha256sum "$HOME/.sp1/bin/sp1-gpu-server" | cut -c1-64) bytes=$(stat -c%s "$HOME/.sp1/bin/sp1-gpu-server")"
  echo "sp1_gpu_server_version=$(CUDA_VISIBLE_DEVICES="" timeout 20 "$HOME/.sp1/bin/sp1-gpu-server" --version 2>&1 | tr '\n' ' ')"
else
  echo "sp1_gpu_server=absent"
fi
for cdir in "$HOME"/.sp1/circuits/groth16/*/; do
  [ -d "$cdir" ] || continue
  echo "circuit_dir=$cdir complete=$([ -f "$cdir/.complete" ] && echo yes || echo no)"
  [ -f "$cdir/groth16_vk.bin" ] && echo "circuit_groth16_vk_sha256=$(sha256sum "$cdir/groth16_vk.bin" | cut -c1-64) bytes=$(stat -c%s "$cdir/groth16_vk.bin")"
  for f in groth16_pk.bin groth16_circuit.bin constraints.json groth16_witness.json; do [ -f "$cdir/$f" ] && echo "circuit_file=$f bytes=$(stat -c%s "$cdir/$f") mtime=$(stat -c%y "$cdir/$f")"; done
done
echo "== lockfiles before"
LOCK_BEFORE=$( (sha256sum "$R/program/Cargo.lock" "$S/Cargo.lock" "$R/Cargo.lock" "$G2/armc-int/Cargo.lock") ); echo "$LOCK_BEFORE"
echo "== frozen source digests (every first-party file the guest and hosts are built from; LC_ALL=C sort)"
(cd "$G2" && find armc-relation/adapter armc-relation/relation armc-relation/b3xof armc-relation/program armc-relation/script armc-int \
   -type f \( -name '*.rs' -o -name 'Cargo.toml' -o -name 'Cargo.lock' -o -name 'rust-toolchain' \) -not -path '*/target/*' -print0 \
 | LC_ALL=C sort -z | xargs -0 sha256sum; sha256sum armc-relation/Cargo.toml armc-relation/Cargo.lock armc-relation/rust-toolchain armc-relation/.cargo/config.toml armc-relation/build_reproducible.sh) | tee "$R/runs/SOURCE_DIGESTS_$STAMP.txt" | sha256sum | sed 's/^/source_digest_list_sha256=/'
echo "source_digest_list=$R/runs/SOURCE_DIGESTS_$STAMP.txt entries=$(wc -l < "$R/runs/SOURCE_DIGESTS_$STAMP.txt")"
echo "== build"
cd "$S"
touch ../program/src/main.rs                            # force the guest rebuild from source (sp1-build reruns on mtime)
set +e
# shellcheck disable=SC2086
/usr/bin/time -f "build wall=%e s maxrss=%M KiB" cargo build --release --offline --locked $FEAT $BIN_ARGS > "$LOG" 2>&1
CARGO_RC=$?
set -e
echo "cargo_exit=$CARGO_RC full_log=$LOG"
grep -E "error\[|^error|Finished|build wall|warning: zkdiff-script@" "$LOG" || echo "(no headline lines in the cargo log)"
[ "$CARGO_RC" -eq 0 ] || fail "cargo build exited $CARGO_RC (full output in $LOG)" 8
mapfile -t ELFS < <(find ../program/target/elf-compilation -type f -name zkdiff-guest)
[ "${#ELFS[@]}" -eq 1 ] || fail "expected exactly one guest ELF, found ${#ELFS[@]}" 2
E="${ELFS[0]}"
[ "$E" -nt "$START" ] || fail "the guest ELF was not rebuilt during this run" 7
for b in $BINS; do
  [ -f "target/release/$b" ] || fail "host binary $b was not produced" 9
  [ "target/release/$b" -nt "$START" ] || fail "host binary $b was not rebuilt during this run (stale binary)" 9
done
SHA=$(sha256sum "$E" | cut -c1-64); SIZE=$(stat -c%s "$E"); HOME_PATHS=$(strings "$E" | grep -c '/home/' || true)
VKEY_OUT=$(./target/release/zkdiff-ceremony vkey 2>/dev/null) || fail "zkdiff-ceremony vkey exited $?" 10
VKEY=$(echo "$VKEY_OUT" | grep -E '^sp1_vkey=' | sed 's/^sp1_vkey=//')
[ -n "$VKEY" ] || fail "zkdiff-ceremony vkey printed no key" 10
IDENT=$(./target/release/zkdiff-verify --identity 2>/dev/null) || fail "zkdiff-verify --identity exited $?" 11
VER_ELF_SHA=$(echo "$IDENT" | grep -o '"guest_elf_sha256": "[0-9a-f]*"' | cut -d'"' -f4)
GROTH16_VK_SHA=$(echo "$IDENT" | grep -o '"groth16_vk_sha256": "[0-9a-f]*"' | cut -d'"' -f4)
CIRCUIT_VERSION=$(echo "$IDENT" | grep -o '"sp1_circuit_version": "[^"]*"' | cut -d'"' -f4)
echo "elf=$E"; echo "guest_elf_bytes=$SIZE guest_elf_sha256=$SHA"; echo "home_paths_in_elf=$HOME_PATHS"; echo "sp1_vkey=$VKEY"
echo "sp1_circuit_version=$CIRCUIT_VERSION embedded_groth16_vk_sha256=$GROTH16_VK_SHA verifier_sees_elf_sha256=$VER_ELF_SHA"
[ "$VER_ELF_SHA" = "$SHA" ] || fail "zkdiff-verify embeds ELF $VER_ELF_SHA but the file is $SHA" 12
[ "$GROTH16_VK_SHA" = "$EXPECT_GROTH16_VK_SHA" ] || fail "embedded circuit verifier key $GROTH16_VK_SHA != expected $EXPECT_GROTH16_VK_SHA" 13
for b in $BINS; do echo "host_$b=$(sha256sum target/release/$b | cut -c1-64) bytes=$(stat -c%s target/release/$b) glibc_max=$(objdump -T target/release/$b 2>/dev/null | grep -o 'GLIBC_[0-9.]*' | sort -Vu | tail -1)"; done
echo "== lockfiles after"
LOCK_AFTER=$( (sha256sum "$R/program/Cargo.lock" "$S/Cargo.lock" "$R/Cargo.lock" "$G2/armc-int/Cargo.lock") ); echo "$LOCK_AFTER"
[ "$LOCK_BEFORE" = "$LOCK_AFTER" ] || fail "a lockfile changed during the build" 6
if [ "$PIN_MODE" = "1" ]; then echo "PINS: EXPECT_ELF_SHA=$SHA EXPECT_VKEY=$VKEY EXPECT_ELF_BYTES=$SIZE"; exit 0; fi
[ "$SIZE" = "$EXPECT_ELF_BYTES" ] || fail "ELF size $SIZE != expected $EXPECT_ELF_BYTES" 3
[ "$SHA" = "$EXPECT_ELF_SHA" ] || fail "ELF sha256 $SHA != expected $EXPECT_ELF_SHA" 3
[ "$VKEY" = "$EXPECT_VKEY" ] || fail "vkey $VKEY != expected $EXPECT_VKEY" 4
[ "$HOME_PATHS" = "0" ] || fail "$HOME_PATHS machine paths embedded in the ELF" 5
echo "BUILD_REPRODUCED_OK sha256=$SHA vkey=$VKEY bytes=$SIZE groth16_vk_sha256=$GROTH16_VK_SHA circuit=$CIRCUIT_VERSION"
} 2>&1 | tee "$REC"
grep -q "BUILD_REPRODUCED_OK\|^PINS:" "$REC"
