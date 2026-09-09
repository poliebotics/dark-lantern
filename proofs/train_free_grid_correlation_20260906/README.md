---
version: 1.3
date: 2026-09-09
status: public engineering demonstration on public data; retrospective; CPU-generated PLONK proofs
author: BOSUN for Cathal Ryan Hynes
---

# Exact Change: Sixteen Cells, One Threshold: two PLONK proofs of an exact train-free emission–capture correlation bound over committed 4×4 cell-sum grids

On two disclosed public-data examples, CPU-generated PLONK proofs verified that the mean-channel Pearson correlation of Poseidon-committed 4×4 RGB cell-sum grids exceeded 1/8 for the matched capture–emission pair and remained below 1/8 for the same capture with its fixed recorded mismatch.

This is an engineering demonstration of a zero-knowledge proof-system implementation of the train-free grid statistic from the
train-free coupling package (held-out tails of the public Truth Beam sessions d2 and v10). It is retrospective: the two examples
were chosen by a fixed rule (the lexicographically first target of each session in the recorded seed-2026090601 mismatch map,
the mismatch emission being the one whose recorded edge ends at that capture), and the threshold τ = 1/8 was chosen after
inspecting those two values. It makes no calibration or generalisation claim, says nothing about the other 973 pairs, and
establishes neither physical authenticity nor liveness. The commitments were made tonight, not at recording time. The proof
starts at the committed integer grids: decoding the PNGs and summing the cells is host-side replay evidence (`scripts/reference.py`
and the separate `scripts/independent_check.py`), not in-circuit computation. The data are public and the nonces are disclosed,
so this demonstrates the proof system, not confidentiality.

## The relation

Each image (2048×1152 RGB) is reduced to a 4×4 grid of exact integer cell sums per channel (48 values of at most 26 bits; equal
cell areas, so the channel correlation of the sums equals that of the cell means). For each channel, with n = 16,
C = n·Σxy − Σx·Σy, Vx = n·Σx² − (Σx)², Vy = n·Σy² − (Σy)². The circuit certifies, for each of the six channel comparisons, a sign
b and a quotient q = ⌊S·|ρ|⌋ with S = 65536 through the bounded-slack inequalities q²·Vx·Vy ≤ S²C² < (q+1)²·Vx·Vy, requires every
variance to be nonzero, sums the signed quotients Q per comparison and outputs z = 196608 + Q. The guards z_matched ≥ 221187 and
z_mismatch ≤ 221180 certify the mathematical mean correlation above and below 1/8 respectively, allowing for the rounding error
|Q/(3S) − mean ρ| < 1/S. Three Poseidon(11) commitments bind the capture grid, the matched emission grid and the recorded
mismatch grid to the manifest digest (as two 128-bit public inputs), a 128-bit nonce, the count 48 and a domain-separated role tag;
the same capture grid feeds both comparisons. Circom 2.2.3, snarkjs 0.7.6 PLONK on BN254, 11,811 R1CS constraints, 23,212 PLONK
constraints, the pinned power-15 ceremony file; setup 1.9 s, proving about 9.7 s per example and verification about 0.4 s on the
laptop CPU.

| example | capture and matched emission | recorded mismatch emission | signed q (R, G, B) matched | signed q mismatch | z_matched | z_mismatch | exact mean ρ matched / mismatch |
|---|---|---|---|---|---:|---:|---|
| d2 | `d2_005392.png` | `d2_005980.png` | 4591, 28516, 13043 | 34294, -5297, -9068 | 242758 | 216537 | 0.234737 / 0.101364 |
| v10 | `v10_003368.png` | `v10_003697.png` | -12955, 10764, 30572 | 27399, -29075, -12306 | 224989 | 182626 | 0.144353 / -0.071119 |

Both proofs verify and their public outputs equal the expected values (`RESULTS.json`). The float32 program of the train-free
package gives 0.234756 and 0.101338 for d2 and 0.144328 and -0.071107 for v10 on the
corresponding pairs; the exact-sum values differ from it by less than 3e-5 and every threshold decision agrees. The relation proves
the exact-sum statistic, not the float32 program bit for bit.

## Controls (13 of 13 behaved as required; `CONTROLS.json` records the layer at which each fails)

The recorded donor substituted into the matched role, the two emissions exchanged, the matched emission complemented (sign flip)
and a quotient witness moved by ±1 all fail at witness construction (a circuit assertion); constant-zero grids fail before the
circuit (no inverse of a zero variance) and inside it (v·v⁻¹ = 1); a grid value changed under recomputed commitments yields a proof
that verifies against its own public signals and is rejected against the pinned ones; every one of the seven public signals mutated
by one is rejected by the verifier; the v10 proof is rejected against the d2 public signals; synthetic identical and complementary
grids verify at the exact endpoints z = 393216 and z = 0.

## Contents and verification

`SPEC_FREEZE.json` (frozen before any circuit work), `EXAMPLES.json` (grids and reference arithmetic), `MANIFEST.json` and its
halves in the public signals, `ROOTS.json` (commitments and nonces pinned before proving), `RESULTS.json`, `CONTROLS.json` (first run)
and `CONTROLS_DETAIL.json` (rerun of the witness-layer controls with each assertion's template and circuit line), `RECEIPT.json`
(toolchain hashes, constraint counts, timings with peak memory measured on labelled reruns, the fresh source-to-build comparison
showing the recompiled R1CS and wasm byte-identical to the shipped ones), the circuit source, `logs/` (compile and re-prove logs),
and under `build/` the R1CS, symbol file, wasm witness generator, proving key, verification key, both proofs, public signals and
witness inputs. `fixtures/` holds the six source PNGs (public data from the train-free package's rebuilt pairs), the recorded
seed-2026090601 mismatch map and the pairs manifest, so the package replays without any other tree.

To verify the proofs alone: `snarkjs plonk verify build/verification_key.json build/d2_main_public.json build/d2_main_proof.json`
(and likewise for v10). To replay everything from the package root with an independent snarkjs 0.7.6 (python3 with numpy and
Pillow, node): `SNARKJS="/path/to/node_modules/.bin/snarkjs" python3 scripts/independent_check.py`. It checks the fixture PNGs'
file and decoded-RGB digests against the pairs manifest, recomputes every grid with a separate code path and compares it and its
canonical digest with the frozen openings and the witness inputs, recomputes the signed quotients and z values, reconstructs the
three commitments from the disclosed nonces and grids through the shipped witness generator and compares them with `ROOTS.json`
and the public signals, and verifies both proofs. A checker that compared only aggregate scores could not tell grids shifted by a
constant per value apart, so the grids and digests themselves are compared. Every shipped text file has the build workspace's
absolute paths reduced to package-relative form; `RECEIPT.json` records the SHA-256 of the scripts as run. `SHA256SUMS` covers
every other file.

## Log

- 1.3 (2026-09-09, BOSUN) — title revision, 9 September 2026.
- 1.2 (2026-09-06, BOSUN) — title given its paper form; no other change.
- 1.1 (2026-09-06, BOSUN) — after Astra's audit (HOLD H1–H3): the checker now verifies source digests, grids and commitments
  against the frozen openings from the package root; fixtures shipped; toolchain hashes, rerun peak memory, build logs, the fresh
  compile comparison and the controls' assertion locations added to the receipt.
- 1.0 (2026-09-06, BOSUN) — built on GPT-6 Astra's A′ specification of the same evening; both proofs and all controls
  behaved on the first run.
