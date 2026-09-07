#!/bin/bash
# Re-verifies the N5 extract with an independent snarkjs 0.7.6 (npm i snarkjs@0.7.6; then SNARKJS=/path/to/node_modules/.bin/snarkjs bash verify.sh)
# from this directory. Requires bash, node, python3, sha256sum. Checks: manifest, snarkjs version, pinned verification keys, the four
# proofs, the four retained negative artefacts (rejection reason required), all 20 single-public-field mutations, shared public values,
# aggregate and directional margins, and (when node can run the shipped wasm) the two synthetic zero-margin witness rejections.
set -uo pipefail
SNARKJS=${SNARKJS:-snarkjs}; fail=0
say() { echo "$*"; }
step() { if eval "$2"; then say "ok   $1"; else say "FAIL $1"; fail=1; fi; }
step "SHA256SUMS covers every other file and matches" 'sha256sum -c --quiet SHA256SUMS && [ "$(grep -c . SHA256SUMS)" = "$(find . -type f ! -name SHA256SUMS | wc -l)" ]'
step "snarkjs is 0.7.6" '[ "$($SNARKJS --version 2>/dev/null | head -1)" = "snarkjs@0.7.6" ]'
step "discriminator verification key pinned" '[ "$(sha256sum discriminator/verification_key.json | cut -c1-64)" = "5b92d8c79e633dbb96415ba43ad7f9d72f16f79b1822a6baf88ce4605b3aeae4" ]'
step "diffusion verification key pinned" '[ "$(sha256sum diffusion/verification_key.json | cut -c1-64)" = "eecab416dabfe3f2e5f05ce0378c07c714a9d067b169c557c63167516aae9940" ]'
verify_ok() { $SNARKJS plonk verify "$1" "$2" "$3" 2>&1 | grep -q "OK!"; }
verify_rejects() { out=$($SNARKJS plonk verify "$1" "$2" "$3" 2>&1); ! echo "$out" | grep -q "OK!" && echo "$out" | grep -Eq "Invalid Proof|not valid"; }
for lane in discriminator diffusion; do
  step "$lane original proof verifies" "verify_ok $lane/verification_key.json $lane/public.json $lane/proof.json"
  step "$lane repeat proof verifies" "verify_ok $lane/verification_key.json $lane/public_repeat.json $lane/proof_repeat.json"
  step "$lane repeated public signals identical" "cmp -s $lane/public.json $lane/public_repeat.json"
  step "$lane retained malformed proof rejects with a proof error" "verify_rejects $lane/verification_key.json $lane/public.json $lane/proof_tampered.json"
  step "$lane retained tampered public rejects with a proof error" "verify_rejects $lane/verification_key.json $lane/public_tampered.json $lane/proof.json"
done
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
python3 - "$TMP" <<'PY'
import json, sys
P = 21888242871839275222246405745257275088548364400416034343698204186575808495617; tmp = sys.argv[1]
for lane in ('discriminator', 'diffusion'):
    pub = json.load(open(f'{lane}/public.json'))
    for i in range(len(pub)):
        m = list(pub); m[i] = str((int(m[i]) + 1) % P); json.dump(m, open(f'{tmp}/{lane}_mut_{i}.json', 'w'))
PY
for lane in discriminator diffusion; do
  n=$(python3 -c "import json;print(len(json.load(open('$lane/public.json'))))"); rej=0
  for ((i=0;i<n;i++)); do verify_rejects $lane/verification_key.json $TMP/${lane}_mut_$i.json $lane/proof.json && rej=$((rej+1)); done
  step "$lane: all $n single-public-field mutations reject ($rej/$n)" "[ $rej = $n ]"
done
step "shared commitment, model tag and context agree across both proofs; aggregates and directional margins recompute" 'python3 - <<'"'"'PY'"'"'
import json
r = json.load(open("proof_receipt.public.json")); D = {k: int(v) for k, v in zip(r["discriminator"]["public_signal_order"], json.load(open("discriminator/public.json")))}
F = {k: int(v) for k, v in zip(r["diffusion"]["public_signal_order"], json.load(open("diffusion/public.json")))}
assert all(D[k] == F[k] for k in ("commitment", "model_tag", "context"))
assert D["score_tt"] + D["score_uu"] - D["score_tu"] - D["score_ut"] == D["delta"] > 0 and D["passed"] == 1
assert (F["residual_tu"] + F["residual_ut"]) - (F["residual_tt"] + F["residual_uu"]) == F["margin"] > 0 and F["passed"] == 1
assert F["residual_tt"] + F["residual_uu"] == F["matched_residual"] and F["residual_tu"] + F["residual_ut"] == F["crossed_residual"]
m = json.load(open("MARGINS.json"))
assert m["discriminator"]["first_direction_tt_minus_tu"] == D["score_tt"] - D["score_tu"] < 0 and m["diffusion"]["first_direction_tu_minus_tt"] == F["residual_tu"] - F["residual_tt"] < 0
print("   directional:", "disc tt-tu", D["score_tt"] - D["score_tu"], "uu-ut", D["score_uu"] - D["score_ut"], "| diff tu-tt", F["residual_tu"] - F["residual_tt"], "ut-uu", F["residual_ut"] - F["residual_uu"])
PY'
if command -v node >/dev/null && [ -f discriminator/generate_witness.js ]; then
  for lane in discriminator diffusion; do
    ctx=$(python3 -c "import json;print(json.load(open('proof_receipt.public.json'))['$lane']['public_signals']['context'])")
    python3 -c "import json;z=[['0']*16 for _ in range(4)];e=[['0']*16 for _ in range(3)];json.dump(dict(context='$ctx',nonce='0',cameraT=z,cameraU=z,emissionT=e,emissionU=e),open('$TMP/${lane}_zero.json','w'))"
    step "$lane synthetic zero-margin witness rejects (Assert Failed)" "! node $lane/generate_witness.js $lane/$lane.wasm $TMP/${lane}_zero.json $TMP/${lane}_zero.wtns >/dev/null 2>$TMP/${lane}_zero.err && grep -q 'Assert Failed' $TMP/${lane}_zero.err"
  done
else
  say "skip synthetic zero-margin witness tests (node or generate_witness.js unavailable)"
fi
[ $fail = 0 ] && say "ALL CHECKS PASSED" || say "SOME CHECKS FAILED"; exit $fail
