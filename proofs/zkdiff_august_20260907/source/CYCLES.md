---
version: 1.3
date: 2026-09-07
status: measured (execute-only, SP1 6.4.0, the development machine) for the pre-r4 kernels; ancillary numbers corrected per Astra r4 item 8; the kernel crate itself has since moved to the FINAL saturation contract (see the banner) and its parity record is FULL_GUEST.md
author: BOSUN
---

> **Superseded in part (2026-09-07, Astra r4, applied in G2-D).** The kernels measured here (v3, ELF `3fd902b3…`)
> used the symmetric domain `[-32767, 32767]` with `-32768` counted as a clip, and did not count indexed hits on
> clipped lookup-table entries. Both were changed to the G1 FINAL contract (`README_FINAL.md` section 3: full int16
> domain, every clamp counted, every masked-table hit counted, blob format v2 with a clipping mask per table, left
> shifts checked for representability, an attention multiplier for the width-12 specification) and the parity suite
> was re-pointed at the FINAL artifact (`oracle_final/`, checkpoint `c6955192…`) plus the 42 differential boundary
> fixtures of `g1_integer/final/fixtures/`. The instruction counts below are those of the pre-r4 kernels in the
> two-pass bench guest; the complete proof guest's count is in `FULL_GUEST.md`. `armc-eval-bench/` itself was not
> rebuilt. The `get_unchecked` optimisation (section 3.3, item 10.3) is deliberately NOT taken (Astra r4 item 10).

# G2-A: ARM-C integer denoiser in Rust, parity against the G1 oracle, SP1 instruction count

Scope: the G1 fixed-point scheme (`../g1_integer/README.md` section 3) ported to a `no_std` Rust
crate, proven byte-exact against the G1 test vectors, and executed (never proved) as a minimal
SP1 6.4.0 guest that evaluates the width-16 denoiser twice on row d2 1328 (own conditioning,
then the +2 conditioning) and commits the two residual sums. No network, no GitHub mutation, no
Lambda contact. Everything below is **[measured]** on the development machine unless marked **[derived]** (arithmetic
on measured numbers) or **[confirm]** (not measured here).

## 1. Result in one table

Headline (the tree's current kernels, ELF `3fd902b342ba07411cae719571af37033d544cafe20845db68f5e9e0e15230fa`;
the v2 ELF `a9bd26e51a075aba84a54d935cf4f6076093d76babbc7fde87f1b2efaed5fb39` gave the identical
counts in every region; all four residual sums exact, zero saturations, host-verified):

| scheme | pass_correct (instr) | pass_wrong (instr) | blob parse + input (instr) | two-pass guest total (instr) | instr / MAC, one pass [derived] | SP1 gas | host execute wall | peak RSS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **int16 weights** | **3,386,436,547** | 3,386,436,806 | 44,169,577 | **6,817,169,189** | **4.080781** | 6,545,542,054 | 101.9 s (execute call; full process wall 123.6 s) | 11.945 GB (11,665,088 KiB) |
| int8 weights | 3,386,439,739 | 3,386,437,797 | 44,169,573 | 6,817,173,308 | 4.080785 | 6,545,541,095 | 177.1 s (execute call; full process wall 237.9 s) | 12.162 GB (11,877,240 KiB) |

(v3 measurements from `logs/execute_int16_20260907T191457Z.{log,results}` and `logs/execute_int8_20260907T191943Z.{log,results}`;
an earlier revision of this table carried the v2 run's gas, time and RSS under the v3 label, corrected per Astra r4
item 8. GNU time reports KiB; the GB figures are decimal. Instructions per MAC for the complete two-pass guest
including the blob parse: 6,817,169,189 / 1,659,700,224 = 4.107470.)

First measurement, for the record (v1.0 kernels, ELF `133700ed831f7c267d0732a04426fd9eb1dbe705535260ab0904dac31fc6e5dd`):

| scheme | pass_correct (instr) | pass_wrong (instr) | blob parse + input (instr) | two-pass guest total (instr) | instr / MAC, one pass [derived] | SP1 gas | host execute wall | peak RSS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| int16 weights | 5,268,810,642 | 5,268,810,901 | 40,916,365 | 10,578,663,252 | 6.349 | 9,551,979,502 | 148.2 s | 12.67 GB |
| int8 weights | 5,268,813,834 | 5,268,811,892 | 40,916,361 | 10,578,667,371 | 6.349 | 9,551,984,308 | 199.9 s | 13.01 GB |

MAC count per pass: 829,850,112 (0.82985 G, `../g1_integer/constants_int16.json` `op_count`,
attention QK^T and AV included). Instructions per MAC for the whole two-pass guest including
the blob parse: 6,817,169,189 / 1,659,700,224 = **4.107470** [derived] (v1.0: 6.374); per pass
3,386,436,547 / 829,850,112 = 4.080781. The instruction counts are deterministic; wall times varied, and their causes were not
separately measured.

Every guest committed exactly the oracle's residual sums (int16: 12775807457 correct,
15569339266 wrong +2; int8: 12951859214 and 15757745232), zero saturation events, and the host
verified them against the native `armc-int` evaluation and the oracle manifests
(`verified_public_values=true`, `paired_correct_lt_wrong=true`). Syscalls: 0.

For scale: the G2 plan (`../g2_scoping/SP1_GUEST_PLAN.md` section 6) estimated 27.2 G for two
passes plus legs at the 12.8 instr/MAC bench rate and 123.3 G at the 70.7 r32 rate; the measured
denoiser-only figure is 6.82 G (10.58 G with the first kernels). At the fleet's measured A100 rate
of 182 to 230 s per G instructions (plan section 6), the two-pass denoiser alone would be 21 to 26
minutes of proving [derived, extrapolation, not measured].

## 2. Parity (deliverable 2): PASS

`cargo test --release --offline` in `armc-int/`, 15 tests, all pass (0.3 s):

| test | what it checks | result |
|---|---|---|
| `parity_int16_correct_chained`, `parity_int16_wrong_p2_chained`, `parity_int8_correct_chained`, `parity_int8_wrong_p2_chained` | the Rust forward on its own outputs: all 188 `T:` layer outputs (shape, `f`, every value) equal the oracle's, and the residual sum equals `residual_sum_int` | **PASS, 188/188 layers, residual equal, 0 saturations, in all four sets** |
| `kernels_isolated_*` (four sets) | every layer recomputed on the oracle's own input tensors (the output is substituted by the oracle's after comparing), so each kernel is tested in isolation against the exported layer tensors | **PASS, 188/188 in all four sets** |
| `residual_sums_are_the_documented_ones` | the four manifests carry 12775807457 / 15569339266 / 12951859214 / 15757745232 | PASS |
| `blob_round_trip_and_constants_identical_across_conditions` | blob serialise/parse round trip; constants identical between the correct and wrong_p2 exports; truncated blobs rejected | PASS |
| `table_and_constant_hashes_match_the_manifest` | SHA-256 of every LUT, the exp table, every `W:`/`M:`/`BP:` array and the coordinate planes against the manifest (incl. the README's silu 11->11 and EXP hashes) | PASS |
| `noising_and_hint_match_the_exported_inputs` | integer `q_sample` reproduces `IN:Ct_int`; `hint = cat(E, coord)` reproduces `T:hint`; input hashes 9baf878a / 37198a3d / 4050eb3f / 26f2fedf | PASS |
| `fast_conv_paths_equal_the_generic_definition` | the 3x3 stride-1 and 1x1 fast paths against the scalar generic convolution on random data (borders, tails) | PASS |
| `rounding_helpers_follow_python_semantics` | `rshift_round`, `round_div`, `rescale`, `isqrt`, `clamp16` on signed cases against the Python definitions | PASS |
| `tester_detects_a_corrupted_constant` | fixture test of the tester: one weight of `in_conv` changed by one unit is reported as the first mismatching layer (index 242, oracle -49 vs -50) with 167 downstream layers differing | PASS |

There was no mismatch to report: the first run of the parity suite passed. The test prints, for
any mismatch, the layer name, the first differing flat index with (c, y, x), both values and the
count of differing values.

Oracle vectors used: `../g1_integer/vectors/vectors_{int16,int8}_{correct,wrong_p2}.{npz,json}`,
exported to raw little-endian arrays by `tools/export_oracle.py` into `oracle/<set>/` (464 arrays
per set; every exported array's SHA-256 was checked against the manifest hash at export time,
464/464 per set).

## 3. Where the instructions go

### 3.0 v1.0 kernels (int16 run, both passes; int8 identical to within 5,000)

Opcode counts from the executor report (`artifacts/results_int16_plain.txt`), per MAC over the
two passes (1,659,700,224 MACs) [derived]:

| opcode | count | per MAC | reading |
|---|---:|---:|---|
| ADD | 2,082,373,587 | 1.25 | the accumulate (1 per MAC) plus address arithmetic |
| MUL | 1,712,828,621 | 1.03 | the multiply (1 per MAC) plus requantisation multipliers |
| LH | 1,671,488,064 | 1.01 | one `i16` activation load per MAC |
| ADDI | 1,577,629,509 | 0.95 | pointer and counter increments |
| LD | 781,532,828 | 0.47 | `i64` accumulator loads (one per 3 MACs in the row loop) |
| BNE | 706,491,384 | 0.43 | loop branches |
| SD | 587,742,253 | 0.35 | accumulator stores |
| SUB, BLTU, SLL, BEQ, SLT, BGEU, MULHU, BGE, BLT | 1,285,107,484 | 0.77 | bounds and overflow checks, mostly in the per-output-element epilogue and per-row setup |
| all others | 173,469,522 | 0.10 | |
| total | 10,578,663,252 | 6.37 | |

The hot loop, from the guest ELF disassembly (`logs/elf_disasm.txt`, `kernels::conv2d`,
`0x7800e0d0..0x7800e104`), is 14 RISC-V instructions for three MACs (one output element of one
kernel row):

```
lh   s3, 0(s4)      ; x[ox-1]
ld   s11, 0(s0)     ; acc[ox]
lh   s9, 2(s4)      ; x[ox]
lh   s5, 4(s4)      ; x[ox+1]
mul  s3, s3, t6     ; * w0
add  s3, s3, s11
addi s4, s4, 2
mul  s9, s9, ra     ; * w1
mul  s5, s5, t5     ; * w2
add  s5, s9, s5
add  s3, s3, s5
sd   s3, 0(s0)
addi s0, s0, 8
bne  s0, a1, loop
```

That is 4.67 instr/MAC inside the loop; 3x3 stride-1 convolutions are 767,950,848 MACs per pass
(92.5 %), so the loop accounts for about 3.58 G of the 5.27 G per pass [derived].

### 3.1 Per-kernel breakdown of the v1.0 kernels (traced guest, int16, both passes) [measured]

A guest variant with the same kernels and one extra input byte opens a cycle-tracker region
around every kernel call (ELF `a7341998f1afc56332c9644419077ebca6e7ddb22d1e605fbb389bdb560df09e`;
its total, 10,579,419,341, exceeds the plain ELF's by 756,089 instructions, the cost of the 800
region markers). Regions accumulate over both passes; `logs/execute_int16_trace_20260907T190212Z.results`.

| kernel | instructions, two passes | share | per unit [derived] |
|---|---:|---:|---|
| conv3x3_s1 (52 layers, 767.95 M MACs per pass) | 7,825,470,626 | 74.3 % | 5.10 per MAC (loop 4.67 + row setup + requantisation) |
| conv3x3_s2 (4 hint-encoder layers, 13.16 M MACs per pass) | 1,526,128,692 | 14.5 % | **58.0 per MAC**: the generic scalar path with per-tap index tests; 1.6 % of the MACs at 14.5 % of the cost |
| conv1x1 (26 layers, 41.29 M MACs per pass) | 484,172,394 | 4.6 % | 5.86 per MAC |
| attention (3 blocks, 7.45 M MACs per pass incl. exp lookups and 10.7 k divisions) | 253,043,932 | 2.4 % | 17.0 per MAC |
| groupnorm (44 layers, 3.28 M elements per pass) | 218,630,176 | 2.1 % | 33.3 per element (two passes over the data plus the per-group u128 root) |
| add (34 layers) | 106,219,824 | 1.0 % | 12.1 per element (4.39 M elements per pass) |
| lut (41 layers, 3.26 M elements per pass) | 52,270,604 | 0.5 % | 8.0 per element |
| bilinear_up2 (8 layers) | 39,515,302 | 0.4 % | |
| cat (4 layers) | 23,536,424 | 0.2 % | |
| avgpool2 (4 layers) | 3,466,722 | 0.03 % | |
| outside the kernels (name lookups, `format!`, hint concat, noising, score) | about 6.0 M | 0.06 % | [derived: passes minus regions] |

The two items worth changing are visible: the strided 3x3 path (58 per MAC) and the accumulator
traffic of the stride-1 loop. Both are addressed by the v2 kernels measured in section 3.2.

### 3.2 v2 kernels: zero-padded input, register-blocked output-stationary 3x3 [measured]

`kernels.rs` v2 copies each conv input once into a zero-padded `(C, H+2, W+2)` buffer (about
`2 / (9 * out_ch)` instructions per MAC), then computes each output row in blocks of 8, 4 and 1
adjacent columns whose accumulators stay in registers across the whole `in_ch * 9` reduction
(`conv3x3_block::<B, S>`, stride 1 or 2 through one const parameter), and requantises each block
in place with wrapping arithmetic under the per-element bound assert. The stride-2 hint-encoder
convolutions use the same block with `S = 2`. The stride-1 block loop is 248 instructions for 72
MACs (3.44 per MAC: 39 `lh`, 72 `mul`, 72 `add`, the rest address arithmetic and residual slice
bounds checks); the stride-2 block 3.71; the 4-wide tail block 4.72 (`logs/elf_v2_disasm.txt`).

Traced v2 guest, int16, both passes (ELF `a9bd26e5…`, total 6,817,922,351, i.e. +753,162 for the
region markers; `logs/execute_int16_trace_20260907T191218Z.results`):

| kernel | instructions, two passes | share | per unit [derived] | v1.0 |
|---|---:|---:|---|---|
| conv3x3_s1 | 5,406,731,334 | 79.3 % | 3.52 per MAC | 5.10 |
| conv1x1 | 471,948,746 | 6.9 % | 5.72 per MAC | 5.86 |
| attention | 253,806,112 | 3.7 % | 17.0 per MAC | 17.0 |
| groupnorm | 218,646,336 | 3.2 % | 33.3 per element | 33.3 |
| add | 160,845,910 | 2.4 % | 18.3 per element (the general signed-shift `rescale` now branches per element; hoisting the shift decisions out of the loop is the obvious fix) | 12.1 |
| conv3x3_s2 | 116,642,962 | 1.7 % | **4.43 per MAC** | 58.0 |
| lut | 52,270,604 | 0.8 % | 8.0 per element | 8.0 |
| bilinear_up2 | 42,147,254 | 0.6 % | | |
| cat | 36,997,992 | 0.5 % | (same `rescale` effect as `add`) | |
| avgpool2 | 3,624,474 | 0.05 % | | |
| outside the kernels | about 10 M | 0.15 % | | |

Opcode mix of the plain v2 int16 run (`logs/execute_int16_20260907T190753Z.results`), per MAC
over both passes [derived]: ADD 1.22, MUL 1.01, LH 0.63 (input loads now shared across the block),
ADDI 0.35, LD 0.27, BGEU 0.19 (residual slice-bounds checks inside the block, about 15 per 72-MAC
iteration), BNE 0.09, SD 0.04. `mul` plus `add` (2.0 per MAC) are the floor for RV64IM, which has
no fused multiply-add and no vector unit; the remaining 2.1 per MAC of the pass is loads, address
arithmetic, bounds checks, requantisation and the non-conv kernels.

### 3.3 v3: const-span array view [measured, identical to v2]

v3 (the source now in the tree) views each padded input row segment as a fixed-size array
(`&[i16; SPAN]`, `SPAN = S*(B-1)+3` as a const parameter, one function per stride via a macro) so
every tap index is a compile-time in-bounds constant. Parity passes (17/17). Measured: 6,817,169,189
(int16), 6,817,173,308 (int8), traced regions identical to v2 to the instruction; LLVM had already
folded the per-tap checks. The 72-MAC block listing (`logs/elf_v3_disasm.txt`, loop `0x7801346c..0x78013848`) is 248 instructions,
of which 13 are panic jumps that a successful iteration skips, so the steady path executes **235 instructions per
72 MACs** (3.26 per MAC inside the block; the measured 3.52 per MAC for the layer class includes row setup,
tails and requantisation). The remaining overhead is the runtime slice checks on `wo[ci*9..ci*9+9]` and the three
`xp[off..off+SPAN]` rows, whose bounds depend on `off` and cannot be proven from `xp.len()` by the compiler, plus
stack reloads of loop invariants under register pressure. Removing them means `get_unchecked` under up-front
invariant asserts (`xp.len() == in_ch*hp*wp`, weight length `9*in_ch`, output length, `SPAN = S*(B-1)+3`, valid block
scheduling, `S*oy+2 < hp` and `S*ox+SPAN <= wp` for every block; Astra r4 item 10); deferred until correctness is
closed, then to be benchmarked before any pin is frozen. Not taken in G2-D.

Design choices that produced this rate, as the task asked: the inner loop is a plain
`wrapping_mul`/`wrapping_add` `i64` accumulate over a contiguous row (`windows(3)` so no per-MAC
bounds checks), weight-stationary per (output channel, input channel, kernel row); the
accumulator bound `32767 * max_o sum_k |Wq[o,k]|` (at most 2^39 here) is recomputed from the
weights at blob parse, the static requantisation bound `acc_bound * max M + max |b'| + 2^(S-1) <
2^63` is checked once per layer in 128-bit arithmetic, and `|acc| <= acc_bound` is asserted once
per output element. Everything outside the inner loop runs with `overflow-checks = true`
(the proved tree's profile), so any overflow is a hard failure.

## 4. int8 costs the same in this loop shape, and why

The int8 scheme changes the values of the weights (|Wq| <= 127, multipliers and shifts differ)
but not their storage or the arithmetic: the blob carries every weight as an `i16`, the kernel
loads it with `lh` and multiplies in `i64`, exactly as for int16. RV64IM has one `mul` and one
`add` regardless of operand width, so the instruction count is identical (the 4,119-instruction
difference across 10.6 G is data-dependent control flow in GroupNorm's Newton iteration and the
clamps). int8 would only pay off with a packed-weight kernel (two `i8` per 16-bit load, or four
per 32-bit load), or in proving cost if SP1 priced narrow multiplies differently, which it does
not by instruction. int16 is therefore the fidelity baseline at no extra guest cost (the G1
result: int16 margin/eta >= 120 versus int8 >= 6.3).

## 5. Memory

| quantity | value | source |
|---|---|---|
| executor peak RSS, int16 run | 12,674,400 kB (12.67 GB) | `/usr/bin/time -v`, `logs/execute_int16_20260907T185047Z.log` |
| executor peak RSS, int8 run | 13,005,720 kB (13.01 GB) | `logs/execute_int8_20260907T185413Z.log` |
| executor RSS during the passes | 10.3 to 10.8 GB, flat (not growing with instructions) | 15-second samples, `logs/rss_int16.txt` |
| executor `MEMORY_LIMIT` | default 24 GiB, not reached | `sp1-core-executor-6.4.0/src/opts.rs:51` |
| guest heap | not measured: the report's `touched_memory_addresses` is 0 in this execute mode | **[confirm]** |
| guest working set, by construction | blob 3.41 MB + inputs 0.69 MB in the reserved input region; per pass the layer outputs total 27.6 MB of `i16` if none were freed (embedded allocator frees, so the live set is a few MB); largest accumulator plane 86 KB; attention scratch 2.7 KB | [derived from shapes] **[confirm]** in a proving run |
| host process CPU | 423.75 s user, 9.73 s system, 256 % of one core, for 148.2 s of execution | `/usr/bin/time -v` |

the development machine had 91 GiB visible, 21 GiB free at launch (`free -g` in the run log). The executor ran at
71.4 M instructions per second here [derived].

## 6. Build hashes, versions, pins

| item | value |
|---|---|
| guest ELF, current source (headline) | sha256 `3fd902b342ba07411cae719571af37033d544cafe20845db68f5e9e0e15230fa`; copy at `artifacts/armc-eval-bench-program.v3.elf`; host `8419744110a871e3113e4e37857448e71bd2262e93ae09b51d6746a598968cc4` (`artifacts/armc-eval-bench-execute.v3`) |
| guest ELF v2 (identical counts) | sha256 `a9bd26e51a075aba84a54d935cf4f6076093d76babbc7fde87f1b2efaed5fb39` (`artifacts/armc-eval-bench-program.v2.elf`); host `2da286490953ec061323748fe4e523aab283fed9d847022cd1f50fec32d61f72` |
| guest ELF v1.0 (first measurement) | sha256 `133700ed831f7c267d0732a04426fd9eb1dbe705535260ab0904dac31fc6e5dd`, 291,000 bytes (`artifacts/armc-eval-bench-program.plain.elf`); host `3f03f074895f85e32afcf3ff07fe4ddf6b5f51f81aeee664c465dd8bb17600f1` (`artifacts/armc-eval-bench-execute.plain`); traced twin `a7341998f1afc56332c9644419077ebca6e7ddb22d1e605fbb389bdb560df09e` |
| results files | `artifacts/results_{int16,int8}_{plain,v2,v3}.txt`, `artifacts/results_int16_trace_{v1,v2,v3}.txt` (each names its ELF hash) |
| constants blob int16 | sha256 `55ff1f0c2b6269c69eedc9e3ffb3344db87d7050128385ea72be088d78eb19af`, 3,411,318 bytes (`blobs/int16/constants_int16.blob`) |
| constants blob int8 | sha256 `3c6fab2580eb556c1cf404274d7e5046ac32745d5eae30748e86bc7fbda97955`, 3,411,318 bytes (`blobs/int8/constants_int8.blob`) |
| inputs | C_int `9baf878a31ac8604c383b29b7cb3fadfc86c4edc419d911402c367876871626f`, noise_int `37198a3df5111736b49a68206895669aa64bccaeb567ab018967b3be3a07b112`, E_int row 1328 `26f2fedf7b7795bbff827915f65b6bb9d21de380be0aec10979f138ba0152de6`, E_int row 1330 `7ab0ee868f3c227b78d8e17f6fba8a5f2d14a2b8c9dd2cc70ca0a9029ff72484` (all 4/12 x 96 x 112 `i16` LE; the G1 manifests carry the same hashes) |
| public values (int16) | `e1597ff902000000 824301a003000000 00000000 ff7f0000` = 12775807457, 15569339266, 0 saturations, qmax 32767 |
| SP1 crates | `sp1-zkvm = "=6.4.0"`, `sp1-sdk = "=6.4.0"` (features `blocking`, `profiling`), `sp1-build = "=6.4.0"`; program lock 109 packages, script lock 516 packages, both seeded from the proved tree's locks and resolved `--offline`; no git sources |
| guest toolchain | `succinct` (rustc 1.94.0-dev), target `riscv64im-succinct-zkvm-elf`; `cargo-prove sp1 (f66b4bf 2026-08-12T14:40:11Z)` in `~/.sp1/bin` |
| host toolchain | `rust-toolchain` channel 1.98.0 (cargo 1.98.0, rustc 1.98.0) |
| guest profile | `lto = "thin"`, `overflow-checks = true` (as `row_binding_join_membership_sp1_candidate/program/Cargo.toml`) |
| guest build flags | sp1-build defaults plus `--remap-path-prefix=$CARGO_HOME=/cargo` and `--remap-path-prefix=<g2_guest>=/g2`, `--locked` (`armc-eval-bench/script/build.rs`, the proved tree's pattern) |
| oracle | `../g1_integer/vectors/` manifests, checkpoint sha256 `f7da7d5096436e675cd8b7b9bd3bd34fb83215589bf57e36cd8a61e048f733eb` |

Crates downloaded: none. Every dependency came from the local cargo registry cache
(`serde 1.0.229`, `serde_json 1.0.151`, `sha2 0.10.9` for the std-only loader and tests; the
guest depends on `sp1-zkvm` and core Rust only).

## 7. Exact commands (all run from the development machine, nothing outside `g2_guest/` written)

```
cd source
python3 tools/export_oracle.py                                   # npz -> oracle/<set>/*.bin + index.json, hashes checked
cd armc-int && cargo generate-lockfile --offline && cargo build --release --offline
cargo test --release --offline                                   # parity: 15 tests PASS
cd .. && ./armc-int/target/release/armc-blob oracle/int16_correct blobs/int16
./armc-int/target/release/armc-blob oracle/int16_wrong_p2 blobs/int16
./armc-int/target/release/armc-blob oracle/int8_correct blobs/int8
./armc-int/target/release/armc-blob oracle/int8_wrong_p2 blobs/int8
cp <proved tree>/program/Cargo.lock armc-eval-bench/program/ && cp <proved tree>/script/Cargo.lock armc-eval-bench/script/
(cd armc-eval-bench/program && cargo metadata --offline --format-version 1 > /dev/null)   # prune/complete the lock offline
(cd armc-eval-bench/script && cargo metadata --offline --format-version 1 > /dev/null)
cd armc-eval-bench/script && export PATH="$HOME/.sp1/bin:$PATH" && cargo build --release --locked --offline
cd ../.. && ./run_bench.sh int16 && ./run_bench.sh int8         # nice -n 10, RAYON/OMP threads 8, /usr/bin/time -v
./run_bench.sh int16 trace                                       # per-kernel cycle-tracker regions (guest input byte = 1)
```

`run_bench.sh` invokes `armc-eval-bench/script/target/release/armc-eval-bench-execute --blob
blobs/<s>/constants_<s>.blob --c blobs/<s>/C_int_d2_row1328_cond1328.i16 --noise
blobs/<s>/noise_int_d2_row1328_cond1328.i16 --e-correct blobs/<s>/E_int_d2_row1328_cond1328.i16
--e-wrong blobs/<s>/E_int_d2_row1328_cond1330.i16 --expect-correct N --expect-wrong N --out ...`.
Logs: `logs/execute_int16_20260907T185047Z.{log,results}`,
`logs/execute_int8_20260907T185413Z.{log,results}`, `logs/build_script.log`.

## 8. Files

```
g2_guest/
  armc-int/               no_std + alloc crate: kernels.rs (conv 3x3/1x1/generic, requant, GroupNorm,
                          LUT, bilinear x2, avgpool, add, cat, attention, noising, residual sum),
                          blob.rs (constants blob format + parser + static bound checks), model.rs
                          (the ARM-C program, any width, Hook for tracing/testing), loader.rs (std:
                          oracle export -> Constants/OracleSet), src/bin/armc_blob.rs, tests/parity.rs
  armc-eval-bench/program SP1 guest (sp1-zkvm =6.4.0): reads blob + C + noise + E_correct + E_wrong (+ trace byte),
                          two evaluations, commits 24 public bytes
  armc-eval-bench/script  host: build.rs (remap-path-prefix, --locked), src/main.rs (execute only, native + oracle check)
  tools/export_oracle.py  G1 npz -> raw arrays with hash cross-check
  oracle/                 the four exported vector sets (126 MB)
  blobs/                  constants blobs and raw inputs for both schemes
  artifacts/              the measured plain ELF, host binary and results files
  run_bench.sh            the exact executor invocation
  logs/                   build and execute logs, RSS samples, ELF disassembly
```

## 9. The port contract after Astra's r3 audit of the oracle (applied, tested)

The following changes implemented the round-3 review findings available on 7 September 2026.

1. **Effective scale map, not the declared `ftab`.** Convolutions, GroupNorms, activations, adds
   and concats take their output scale from their constants or the `ftab`; average pooling,
   bilinear upsampling and the attention core inherit their input scale. The kernels always did
   this (`avgpool2`, `bilinear_up2`, `attention` return the input's `f`); the parity hook compares
   the effective `f` of every layer, and the new test
   `effective_scale_map_differs_from_the_declared_ftab_exactly_where_astra_says` pins the seven
   width-16 names where declared and effective differ: `pool.2`, `pool.3`, `up.0`, `up.1` (declared
   12, effective 11), `down_attns.3.attn` (13 -> 11), `mid_attn.attn` (13 -> 12), `up_attns.0.attn`
   (12 -> 11). `model.rs` documents the rule. The FINAL scale map and revised vectors (width 16, 96x112, seed 20260908, 24k steps, `oracle/final/` in
   this package) required a new parity run, with no code change, using the commands below (written before that
   artifact existed; historical):
   `python3 tools/export_oracle.py --src <final vectors dir> --out oracle_final` then
   `ARMC_ORACLE_DIR=$PWD/oracle_final cargo test --release --offline` in `armc-int/`. As of this
   version `g1_integer/final/` does not exist; the current vectors remain valid for the current
   constants and are the vectors against which every number here was measured.
2. **Two rounding rules.** Conversion of inputs, weights, constants and LUTs is ties-to-even and
   happens offline (`np.rint`); the crate imports the frozen tables and never regenerates a
   transcendental (no `f32`/`f64` anywhere in `kernels.rs`, `blob.rs`, `model.rs`). Runtime shifts
   and divisions are ties toward +inf (`rshift_round`, `round_div`); `rshift_round(v, s)` with
   `s <= 0` is the exact left shift `v << -s` (signature changed to `i32`; tested).
3. **Saturation policy.** Admitted activation domain `[-32767, 32767]`; `-32768` is out of domain.
   `clamp16` saturates to that domain and counts every clipping event; the inputs `C_int`,
   `noise_int`, `E_int` are checked on entry (`count_out_of_domain`), the attention output goes
   through `clamp16`, and the blob parser rejects a LUT entry or coordinate equal to `-32768`. No
   current vector contains `-32768` (checked over every `T:` and `IN:` array of the four sets), so
   the numbers above are unchanged by this rule, and the guest's committed saturation count stays 0.
4. **Bounds are proven, not observed.** Documented in the `kernels.rs` module doc and checked by
   `proven_bounds_match_astra_r3`: conv accumulators over every partial sum `<= 406,605,889,536`
   (int16) and `<= 1,576,206,336` (int8), reproduced exactly from the blob as
   `32768 * max_o sum_k |Wq[o,k]|` (both at `ups.0.0.conv1`); the requantisation expression
   `< 2^63` (checked per layer at parse, 128-bit); GroupNorm `n <= 32256` (max is exactly 32256),
   `N < 2^60` (60 bits at most), `X^2` up to 99 bits, `Q` up to 34 bits, affine `e * Mg` up to 55
   bits, all derived from the constants and the domain; `SSE <= 43008 * 65535^2 =
   184,712,316,364,800 < 2^48`. Hence `i64` with operands widened before multiplication everywhere
   except GroupNorm's squared numerator, division and root, which use `i128`/`u128`; that is how
   the kernels are written.
5. **int8 buys nothing in this loop shape** (section 4); int16 stays the baseline.

## 10. Open items

1. Re-run parity on the FINAL checkpoint's vectors when `g1_integer/final/` lands (item 9.1).
2. Guest memory footprint under proving (page touches, shard count) is unmeasured **[confirm]**.
3. Cheap remaining cuts, unmeasured [estimate]: hoist the shift decisions out of the `add`/`cat`
   element loops (about 0.1 G of 6.8 G); block the 1x1 convolutions like the 3x3 (0.47 G at 5.7
   per MAC could approach 3.5); attention scores with register-blocked keys (0.25 G). None changes
   a rounding rule.
4. Not in this bench, by scope: blob hash pin in the guest, the drand / BLAKE3 / XOF legs, the
   whole-frame reduction, the two-row statement layout, any proof.

## 11. Audit note

Checked against source: every oracle rule was ported from `kernels.py` and `int_ref.py` and the
G1 README section 3, and every layer of four vector sets compares equal by value, for every kernel
version measured here (the parity suite ran and passed before each rebuild). The SP1 numbers are
read from the executor report printed by the host (`total_instruction_count`, cycle-tracker
regions, opcode counts, gas) and from `/usr/bin/time -v`; each run's ELF hash is in its results
file. The 0.82985 GMAC denominator is the oracle's op count. The A100 extrapolation reuses the
plan's measured per-G rate and is not a measurement of this guest. Astra's r3 bounds were
reproduced from the constants, not copied. Nothing was proved; no ELF left the development machine.

## Log

- 1.3 (2026-09-07, BOSUN, G2-D) — Astra r4 item 8 applied: v3 gas, execute time, wall and RSS corrected
  (the table had carried v2's), KiB/GB stated, 235-instruction steady path, the inconsistent "60 instructions,
  0.5 per MAC" remark removed; banner recording the post-r4 kernel changes and where their parity lives.
- 1.0 (2026-09-07 19:59 IST, BOSUN) — crate, parity suite (15 PASS), guest and host built
  offline against the proved tree's pins, int16 and int8 executed on the development machine, numbers recorded.
- 1.1 (2026-09-07 20:15 IST, BOSUN) — Astra r3 contract applied (effective scale map, two
  rounding rules, symmetric domain with counted clipping incl. inputs, proven bounds reproduced;
  17 tests PASS); per-kernel breakdown of v1.0; v2 kernels (padded, register-blocked 3x3, proper
  stride-2 path) measured: 6,817,169,189 for two passes, 4.081 instr/MAC; v3 build started.
- 1.2 (2026-09-07 20:25 IST, BOSUN) — v3 (const-span block) measured identical to v2 in every
  region; headline fixed at the current source's ELF `3fd902b3…`; residual block overhead
  explained from the disassembly; artifacts and results files listed.
