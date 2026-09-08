#!/usr/bin/env bash
# verify_offline.sh: verify all 112 zkdiff August proofs with the prebuilt static binaries in this directory.
# Needs bash and coreutils (sha256sum, cmp, grep, cut, tail, wc). No Rust, no Python, no network, no other file.
# Reports are written under $CAPSULE_OUT (default /tmp/zkdiff_capsule_out), so the capsule itself may be read-only.
# Exit 0 only if the capsule ledger verifies, the binaries carry the pinned identities, all 112 proofs are accepted by
# zkdiff-verify, all 112 raw proofs are VERIFIED by the standalone verifier and the row-600 controls behave.
set -euo pipefail
C=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
OUT=${CAPSULE_OUT:-/tmp/zkdiff_capsule_out}
mkdir -p "$OUT/reports"
readonly PIN_ELF_SHA="51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc"
readonly PIN_GROTH16_VK_SHA="4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696"
readonly PIN_EXPECTED_SHA="182870aa06f11e246a76f8c94c5a1c40aed7b3ad4b3537420422f426dcd46eb2"
readonly PIN_VKEY="0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027"
say() { printf '%s\n' "$*"; }
fail() { say "FAIL: $*"; say "OFFLINE VERIFICATION FAILED"; exit 1; }
sha() { sha256sum "$1" | cut -c1-64; }
say "zkdiff August proofs, offline verification capsule: $C"
say "outputs: $OUT"
# 0. the capsule's own ledger
(cd "$C" && sha256sum -c --quiet SHA256SUMS) || fail "a capsule file differs from capsule/SHA256SUMS"
say "[0] capsule ledger: $(grep -c . "$C/SHA256SUMS") files present and matching"
[ "$(tr -d ' \n' < "$C/PROGRAM_VKEY.txt")" = "$PIN_VKEY" ] || fail "PROGRAM_VKEY.txt is not the pinned program key"
[ "$(sha "$C/expected_identities_august.json")" = "$PIN_EXPECTED_SHA" ] || fail "expected_identities_august.json is not the frozen file"
[ "$(sha "$C/groth16_vk.bin")" = "$PIN_GROTH16_VK_SHA" ] || fail "groth16_vk.bin is not the pinned circuit key"
say "[0] pins: program key $PIN_VKEY; expected identities sha256 $PIN_EXPECTED_SHA; circuit key sha256 $PIN_GROTH16_VK_SHA"
# 1. the verifier's own identity: the embedded guest ELF and circuit key
"$C/zkdiff-verify" --identity > "$OUT/identity.json" 2>&1 || fail "zkdiff-verify --identity did not run (is this an x86_64 Linux machine?)"
grep -q "\"guest_elf_sha256\": \"$PIN_ELF_SHA\"" "$OUT/identity.json" || fail "zkdiff-verify embeds another guest ELF"
grep -q "\"groth16_vk_sha256\": \"$PIN_GROTH16_VK_SHA\"" "$OUT/identity.json" || fail "zkdiff-verify embeds another circuit key"
grep -q '"sp1_circuit_version": "v6.1.0"' "$OUT/identity.json" || fail "zkdiff-verify is not circuit v6.1.0"
say "[1] zkdiff-verify identity: guest ELF sha256 $PIN_ELF_SHA, circuit v6.1.0, circuit key sha256 $PIN_GROTH16_VK_SHA, vk root $(grep -o '"vk_root": "[0-9a-f]*"' "$OUT/identity.json" | cut -d'"' -f4)"
# 2. acceptance verification of every framed proof (Groth16 under the pinned keys, then every frozen identity)
n=0; ok=0
say "[2] zkdiff-verify --expect on every framed proof"
say "     row    u   d  rule         R_correct       R_wrong             D class    clips  result"
for f in "$C"/proofs/row_*_groth16.bin; do
  n=$((n+1)); b=$(basename "$f" _groth16.bin)
  if "$C/zkdiff-verify" --proof "$f" --expect "$C/expected_identities_august.json" --report "$OUT/reports/$b.verify.json" > "$OUT/reports/$b.stdout" 2>&1 \
     && grep -q '^verified_and_accepted=true$' "$OUT/reports/$b.stdout"; then
    ok=$((ok+1)); res=ACCEPTED
  else
    res=REFUSED
  fi
  rep="$OUT/reports/$b.verify.json"
  g() { grep -o "\"$1\": [^,}]*" "$rep" | head -1 | sed 's/^[^:]*: //; s/"//g'; }
  printf '    %4s %4s %3s  %-9s %13s %13s %13s %-9s %4s  %s\n' "$(g row)" "$(g wrong_row)" "$(g offset)" "$(g offset_rule)" "$(g r_correct)" "$(g r_wrong)" "$(g difference)" "$(g outcome_class)" "$(g clip_events)" "$res"
done
[ "$n" -eq 112 ] || fail "expected 112 framed proofs, found $n"
[ "$ok" -eq 112 ] || fail "$ok of $n proofs accepted"
say "[2] $ok/$n proofs accepted under the frozen identities"
# 3. the negative controls on row 600 and the raw (356 + 752 byte) form
"$C/zkdiff-verify" --proof "$C/proofs/row_000600_groth16.bin" --expect "$C/expected_identities_august.json" --controls --report "$OUT/controls_000600.json" > "$OUT/controls_000600.stdout" 2>&1 \
  || fail "a control did not behave (see $OUT/controls_000600.json)"
grep -q '"controls_all_behaved": true' "$OUT/controls_000600.json" || fail "controls_all_behaved is not true"
say "[3] controls on row 600: $(grep -o '"control": "[^"]*"' "$OUT/controls_000600.json" | wc -l) mutations, every one rejected or refused at its expected layer"
"$C/zkdiff-verify" --proof-bytes "$C/proofs/row_000600_groth16_proof.bin" --public "$C/public_values/row_000600_public_values.bin" --expect "$C/expected_identities_august.json" > "$OUT/raw_000600.stdout" 2>&1 \
  || fail "the raw form of row 600 (356-byte proof + 752-byte statement) was refused"
say "[3] raw form of row 600 (356-byte proof + 752-byte statement): accepted"
# 4. the standalone verifier (sp1-verifier 6.4.0 only, no ELF): Groth16 under the pinned program key, two tamper controls each
m=0; ok2=0
for f in "$C"/proofs/row_*_groth16_proof.bin; do
  m=$((m+1)); b=$(basename "$f" _groth16_proof.bin)
  if "$C/zeebeam-standalone-verifier" "$f" "$C/public_values/${b}_public_values.bin" "$PIN_VKEY" > "$OUT/reports/$b.standalone.txt" 2>&1 \
     && tail -1 "$OUT/reports/$b.standalone.txt" | grep -q '^VERIFIED$' \
     && grep -q '^tamper_public_byte_87_rejected=true$' "$OUT/reports/$b.standalone.txt" \
     && grep -q '^wrong_vkey_rejected=true$' "$OUT/reports/$b.standalone.txt"; then
    ok2=$((ok2+1))
  else
    say "    REJECTED $b (standalone)"
  fi
done
[ "$m" -eq 112 ] || fail "expected 112 raw proofs, found $m"
[ "$ok2" -eq 112 ] || fail "$ok2 of $m raw proofs VERIFIED by the standalone verifier"
say "[4] standalone verifier: $ok2/$m raw proofs VERIFIED under $PIN_VKEY, both tamper controls rejected each time"
# 5. when the capsule sits inside the package, its copies must equal the package's files
if [ -d "$C/../proofs" ] && [ -d "$C/../public_values" ]; then
  d=0
  for f in "$C"/proofs/*.bin; do cmp -s "$f" "$C/../proofs/$(basename "$f")" || d=$((d+1)); done
  for f in "$C"/public_values/*.bin; do cmp -s "$f" "$C/../public_values/$(basename "$f")" || d=$((d+1)); done
  cmp -s "$C/expected_identities_august.json" "$C/../source/expected_identities_august.json" || d=$((d+1))
  [ "$d" -eq 0 ] || fail "$d capsule files differ from the package's copies"
  say "[5] the capsule's proofs, statements and expected identities are byte-identical to the package's"
else
  say "[5] capsule used on its own (no ../proofs): the package comparison is skipped"
fi
if [ -d "$C/reexecute" ]; then
  say "[6] reexecute/ is present: $C/reexecute/reexecute_row.sh recomputes row 600's statement from the shipped raw frame, and any other row from a frame downloaded from the data layer (FRAMES.md); about 4 to 7 minutes and 17 GB of RAM per row"
else
  say "[6] reexecute/ is absent from this copy; the raw frames are on the data layer (FRAMES.md) and the re-execution capsule is part of the published package"
fi
say "OFFLINE VERIFICATION PASSED: $ok/112 accepted by zkdiff-verify (Groth16 under the pinned program and circuit keys, then every frozen identity), $ok2/112 VERIFIED by the standalone verifier, controls behaved; reports in $OUT"
