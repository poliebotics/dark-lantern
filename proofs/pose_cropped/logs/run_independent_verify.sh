#!/usr/bin/env bash
set -uo pipefail
. <box path redacted>
OUT="$ST/receipts/independent_verify"; mkdir -p "$OUT"
V=[machine path redacted]
ELF="$HR/target/elf-compilation/riscv64im-succinct-zkvm-elf/release/zeebeam-trained-r32-pose-ptq-v2-program"
P="$HR/results/pose_join_groth16.proof.bin"
sha256sum "$V" "$ELF" "$P" > "$OUT/inputs_sha256.txt"
echo "== clean verify =="        | tee    "$OUT/verify.log"
nice -n 19 "$V" "$ELF" "$P"      2>&1 | tee -a "$OUT/verify.log"; echo "clean_exit=$?"   | tee -a "$OUT/verify.log"
echo "== tamper publics =="      | tee -a "$OUT/verify.log"
nice -n 19 "$V" "$ELF" "$P" --tamper publics 2>&1 | tee -a "$OUT/verify.log"; echo "tamper_publics_exit=$?" | tee -a "$OUT/verify.log"
echo "== tamper proof =="        | tee -a "$OUT/verify.log"
nice -n 19 "$V" "$ELF" "$P" --tamper proof   2>&1 | tee -a "$OUT/verify.log"; echo "tamper_proof_exit=$?"   | tee -a "$OUT/verify.log"
grep -m1 'program_vkey' "$OUT/verify.log" | sed 's/.*: //' > "$OUT/vkey.txt"
cat "$OUT/vkey.txt"
