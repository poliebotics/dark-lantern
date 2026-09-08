#!/bin/bash
# SHA256SUMS_G2D: every file of the transfer PAYLOAD the node needs for the August batch (sources rebuilt there, data used
# as is), so the node checks the bundle with `sha256sum -c SHA256SUMS_G2D` before building (Astra r5 finding 6: the list
# names exactly what is transferred, so a plain `sha256sum -c` passes or fails on the payload alone; nothing under
# target/ is listed). the development machine's build artefacts (reference ELF and host binaries) go into REFERENCE_PINS_G2D.txt beside it,
# for the record only: the node rebuilds them and the driver asserts the pins. Run from anywhere; writes into g2_guest/.
set -euo pipefail
cd "$(dirname "$0")/.."
export LC_ALL=C
{
  find armc-relation/adapter armc-relation/relation armc-relation/b3xof armc-relation/program armc-relation/script armc-int \
       -type f \( -name '*.rs' -o -name 'Cargo.toml' -o -name 'Cargo.lock' -o -name 'rust-toolchain' -o -name '*.md' -o -name '*.json' \) -not -path '*/target/*' -print0
  printf '%s\0' armc-relation/Cargo.toml armc-relation/Cargo.lock armc-relation/rust-toolchain armc-relation/RELATION.md armc-relation/.cargo/config.toml armc-relation/build_reproducible.sh FULL_GUEST.md CYCLES.md
  find fixtures_final -type f -print0
  find tools -type f -print0
  find node_prep -maxdepth 1 -type f -name 'G2D_NODE_RUNBOOK.sh' -print0
  printf '%s\0' blobs/final_int16/constants_int16.blob vectors_relation/august/chain_log.csv vectors_relation/august/august_rows.json
  find vectors_relation/synthetic_mirror40 -type f -print0
  find noise_august -type f -print0
  find armc-relation/runs -maxdepth 1 -type f \( -name 'build_record_*.txt' -o -name 'build_log_*.txt' -o -name 'SOURCE_DIGESTS_*.txt' \) -print0
  find armc-relation/runs/batch_prepare_g2d_20260907 -type f -print0
  [ -f expected_identities_august.json ] && printf '%s\0' expected_identities_august.json
} | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS_G2D
{
  echo "# the development machine build artefacts, for the record; the node rebuilds them and build_reproducible.sh asserts the ELF/vkey pins"
  ELF=armc-relation/program/target/elf-compilation/riscv64im-succinct-zkvm-elf/release/zkdiff-guest
  [ -f "$ELF" ] && sha256sum "$ELF" && echo "guest_elf_bytes=$(stat -c%s "$ELF")"
  for b in zkdiff-execute zkdiff-ceremony zkdiff-batch zkdiff-verify; do
    f=armc-relation/script/target/release/$b
    [ -f "$f" ] && echo "$(sha256sum "$f")  bytes=$(stat -c%s "$f") glibc_max=$(objdump -T "$f" 2>/dev/null | grep -o 'GLIBC_[0-9.]*' | sort -Vu | tail -1)"
  done
  echo "generated_utc=$(date -u +%Y%m%dT%H%M%SZ) host=$(hostname)"
} > REFERENCE_PINS_G2D.txt
echo "SHA256SUMS_G2D: $(wc -l < SHA256SUMS_G2D) files; REFERENCE_PINS_G2D.txt written"
