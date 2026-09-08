---
version: 2.5
date: 2026-09-07
status: FINAL G1 artifact for g0e_armc_b16_96x112_cd0_aug_s20260908_24k; Rust parity PASSED after this note was frozen (source/FULL_GUEST.md section 4, RESULTS.md section 4); regenerable by one command; published copy, see the banner below the title
author: BOSUN
---

# G1 FINAL: integer execution contract and artifact for the proof model

> **Published copy (8 September 2026).** This note was frozen on 7 September 2026 in the private tree, where the oracle lived under
> `g1_integer/` and the trainer under `src/`. In this publication the oracle is `oracle/` (this file is `oracle/final/README_FINAL.md`),
> the trainer is `oracle/trainer/`, the checkpoint and its evaluator outputs are `model/` (`ckpt/final/` below reads as `model/`), the
> d2, v10 and August cached rows, the vector arrays and the August input arrays (`august_inputs/row_NNNNNN.npz`,
> `rows_august/.../C_*.npy`) are on the data layer (`LARGE_FILES.md`; published by the principal's decision of 8 September 2026,
> `REDACTION.md`). Rust parity, open in
> section 9 when this was written, passed the same evening (`source/FULL_GUEST.md` sections 4.1 to 4.4; `RESULTS.md` section 4). The
> offset-rule label `standard` of the original reads `direct` here, the name the guest, the verifier and the receipts use. The
> ratio sentence of section 7 is corrected as marked. Nothing else was changed in the copy.

Checkpoint `ckpt/final/g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pt`, sha256
`c6955192067c8df1f46960f4803b32eac1c037b84a0f40de3b265b739d85fab8` (verified against
`g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pubproto_eval.json`), step 24000. Trainer args recorded
in the checkpoint: `arch armc`, `base_ch 16`, `mults ''` (default (1,2,4,4)), `out_size 96,112`,
`seed 20260908`, `sessions d2,v10,august`, `cond_drop 0.0`, `august_train_rows 600`,
`crop_id UNCROPPED_FULL_FRAME_20260825`, 1,114,500 parameters. The saved CUDA RNG state decodes to
seed 20260908, offset 192000 = 24000 steps x 2 draws x 4, which confirms both the per-call Philox
increment used by the noise emulation and that hint dropout drew nothing (cond_drop 0). Same
operator graph as the superseded step-12000 artifact (`../README.md`); weights, calibration, scale
map, constants, bounds, vectors and every measurement are regenerated here.

Evaluator outputs beside the checkpoint: the summary JSON (d2 correct 0.011047, wrong ~0.03340,
paired 1.0, AUROC 1.0; v10 correct 0.012673, wrong ~0.03600, paired 1.0, AUROC 1.0) and the per-row
arrays `ckpt/final/g0e_armc_b16_96x112_cd0_aug_s20260908_24k/pubproto_raw.npz_{d2,v10}.npz`.

## 0. Regenerating the whole artifact for another checkpoint (one command)

    cd "$P/oracle"          # P = the package root (VERIFY.md); the private tree kept the oracle under g1_integer/
    ./freeze_artifact.sh <ckpt.pt> <pubproto_eval.json> <raw_npz_dir> <out_dir>

Runs, in order and without hand steps: kernels self-test and float64-mirror check (`selfcheck`),
fp32 and bf16-emulated protocol scores for the 37 rows and the 112 August rows plus the per-row
positive control (`float`), the four agreement studies in parallel (`agreement`), byte-exact vectors
and `constants_{int16,int8}.json` (`vectors`), `agreement.json` + `AGREEMENT.md` (`report`), the
August guest inputs (`august`) and `FREEZE_SUMMARY.md` (`summary`). About 25 minutes on the development machine, CPU
only, `OMP_NUM_THREADS=16`, no bytecode under `src/`. A single stage can be rerun by naming it as the
fifth argument; the vector rows are the optional sixth (`d2:1328,august:650` by default). The
per-row noise, calibration set (every fifth protocol row, indices 0,5,...,30, plus August rows
600,616,...,696), scale-map derivation and bounds are all recomputed from the given checkpoint, so a
later proof model (the 48k or 96k arms) is frozen by pointing the command at it.

## 1. Environment pin and reference files

| item | value | source |
|---|---|---|
| node that trained and evaluated | 8x NVIDIA A100-SXM4-80GB, `torch 2.7.0` | `../node_results/G0.log:2` printed by `../bootstrap_node.sh:6`; `../launch_g0_20260907T1616Z.log:35` |
| the development machine (this artifact) | torch 2.11.0+cu130 (CPU only), numpy 2.3.5, Python 3.14.4 | `constants_int16.json -> env` |
| evaluator | `../src/lean_pubproto_eval.py` (t 150, offsets [-2,+2,-15,+15,+30], seed 20260823, one generator per session walked in row order, bf16 autocast) | lines 16-17, 115-137 |
| trainer, model | `../src/train_lean.py` (ArmCUNet 156-165, eval_rows 176-183, construction 341-343, strict load 347, diffusion constants 368), `../src/phase_g/diffusion_diagnostic_model.py` (forward 262-312) | see `../README.md` section 2 for the full citation table; unchanged |
| cache | float16 on disk (`../src/precache.py:41-42`), loaded float32 (`train_lean.py:123,139`), cast to bf16 by the evaluator (lines 125, 130, 136) | reproduced exactly in `common.load_*_bf16` |

## 2. Positive control against the frozen evaluator (before any integer number)

`float_repro.json` / `positive_control.json` (`positive_control.log`). 222 scores = 37 rows x
(correct + 5 offsets), protocol stream, each row at its evaluator stream position (asserted per row).

| scope | variant | n | abs max | abs median | rel max | rel median | rel signed mean (std) |
|---|---|---|---|---|---|---|---|
| overall | fp32 | 222 | 2.14e-4 | 9.66e-5 | 1.10e-2 | 3.27e-3 | -3.85e-3 (2.02e-3) |
| overall | bf16em (bilinear bf16) | 222 | 2.09e-4 | 3.07e-5 | 6.20e-3 | **1.13e-3** | -5.39e-4 (1.50e-3) |
| overall | bf16em_v2 (bilinear fp32) | 222 | 1.60e-4 | 3.17e-5 | 4.74e-3 | **1.14e-3** | -5.86e-4 (1.50e-3) |
| d2 | fp32 / bf16em / v2 | 162 | 1.96e-4 / 2.09e-4 / 1.60e-4 | 9.61e-5 / 2.90e-5 / 3.12e-5 | 1.10e-2 / 6.20e-3 / 4.74e-3 | 3.29e-3 / 1.11e-3 / 1.15e-3 | -3.87e-3 / -5.01e-4 / -5.66e-4 |
| v10 | fp32 / bf16em / v2 | 60 | 2.14e-4 / 1.01e-4 / 1.54e-4 | 1.02e-4 / 3.38e-5 / 3.24e-5 | 9.32e-3 / 3.12e-3 / 4.44e-3 | 3.24e-3 / 1.19e-3 / 1.09e-3 | -3.80e-3 / -6.40e-4 / -6.40e-4 |
| correct | fp32 / bf16em / v2 | 37 | 1.21e-4 / 4.25e-5 / 4.91e-5 | 8.42e-5 / 1.04e-5 / 1.67e-5 | 1.10e-2 / 4.09e-3 / 3.76e-3 | 7.59e-3 / 8.78e-4 / 1.54e-3 | -7.57e-3 / -1.76e-4 / -4.59e-4 |
| offset -2 | fp32 / bf16em / v2 | 37 | 1.76e-4 / 1.20e-4 / 1.24e-4 | 9.28e-5 / 3.78e-5 / 3.61e-5 | 4.85e-3 / 3.53e-3 / 3.66e-3 | 2.54e-3 / 1.14e-3 / 1.11e-3 | -2.78e-3 / -1.85e-4 / -3.06e-4 |
| offset +2 | fp32 / bf16em / v2 | 37 | 2.14e-4 / 2.09e-4 / 1.60e-4 | 1.07e-4 / 3.38e-5 / 3.73e-5 | 5.72e-3 / 6.20e-3 / 4.74e-3 | 3.09e-3 / 8.92e-4 / 1.13e-3 | -3.26e-3 / -1.03e-3 / -8.87e-4 |
| offset -15 | fp32 / bf16em / v2 | 37 | 1.77e-4 / 1.01e-4 / 9.50e-5 | 1.08e-4 / 3.08e-5 / 2.99e-5 | 5.20e-3 / 3.04e-3 / 2.86e-3 | 3.14e-3 / 9.88e-4 / 8.34e-4 | -3.23e-3 / -5.88e-4 / -3.48e-4 |
| offset +15 | fp32 / bf16em / v2 | 37 | 1.73e-4 / 1.15e-4 / 1.54e-4 | 1.13e-4 / 5.15e-5 / 5.21e-5 | 5.54e-3 / 3.24e-3 / 4.44e-3 | 3.61e-3 / 1.47e-3 / 1.41e-3 | -3.27e-3 / -8.98e-4 / -8.18e-4 |
| offset +30 | fp32 / bf16em / v2 | 37 | 1.89e-4 / 1.05e-4 / 1.38e-4 | 1.01e-4 / 3.65e-5 / 4.34e-5 | 5.37e-3 / 2.94e-3 / 3.70e-3 | 2.90e-3 / 1.12e-3 / 1.12e-3 | -3.01e-3 / -3.57e-4 / -6.98e-4 |

The evaluator's own scores on these 37 rows: paired 37/37, margin (mean wrong minus correct) min
0.019623, median 0.022479. The fp32 reproduction is systematically 3.9e-3 low (7.6e-3 on the correct
condition), the bf16 emulations remove the bias (-5e-4) and leave an unbiased 1.5e-3 scatter.

**Astra r3 item 8 (bilinear promotion), tested and unresolved.** In PyTorch's CUDA autocast policy
`upsample_bilinear2d` is on the fp32 list, so the up-path interpolation in the A100 run may have
produced fp32 (making the following concat fp32); variant 1 keeps it in bf16, variant 2 promotes it.
Against the evaluator the two are indistinguishable at this resolution (rel median 1.13e-3 vs
1.14e-3, signed mean -5.4e-4 vs -5.9e-4; variant 2 has the smaller maximum, 4.7e-3 vs 6.2e-3). The
residual 1.5e-3 scatter is therefore not explained by this choice; it sits at the level of bf16 GEMM
accumulation order, cuDNN bias fusion, the bf16 GELU/SiLU kernels and the `__sincosf` noise
transform on torch 2.7.0 / A100, possible contributors that were not separately isolated or reproduced by the CPU reference. Both variants are carried
in the report; the exact rounding-point fidelity of the A100 run remains unverified.

## 3. The execution contract (Astra r3 items 1, 2, 3, 5, 10)

Kernels and rounding rules are normative in `../kernels.py` (module docstring), the program in
`../int_ref.py` (`forward_program`); constants, scale map, rounding, domain and bounds are exported
in `constants_int16.json`, `constants_int8.json` and every `vectors/*.json` manifest.

**One effective scale map (item 1).** `scale_map` in the constants and manifests is recorded from an
executed trace and locked; execution asserts every tensor's f against it. 188 tensors: 171 from
calibration (`f = clip(floor(log2(32768 / (2 * maxabs))), 0, 15)` over 15 calibration rows x
(own E, E of row+15)), 2 fixed (`hint` 14, `out_conv` 12; inputs `C`, `C_t`, `noise` 12), 15
inherited (their input's f, by construction): `hint_up.0-3`, `pool.0-3`, `up.0-3`,
`down_attns.3.attn`, `mid_attn.attn`, `up_attns.0.attn`. Effective histogram for this checkpoint:
`{7:1, 8:1, 9:22, 10:26, 11:89, 12:38, 13:6, 14:5}` (the f=7 tensor is `ups.3.1.conv1`, calibration
max 71.3). The calibration-candidate table is still exported as `calibration_candidates_ftab` but is
not the contract.

**Two rounding rules (item 2).** Conversion, once at freeze time (inputs C, noise, E and
coordinates; weights, biases, multipliers, gamma/beta; LUT and exp-table entries): ties to even
(`numpy.rint`). Runtime, on data: `rshift_round(v, s) = (v + 2^(s-1)) >> s` with an arithmetic
(floor) shift, an exact left shift `v << -s` when `s <= 0`, and `round_div(a, b) = floor((2a+b)/(2b))`
for `b > 0`: ties toward +inf on signed values (fixtures: `rshift_round(-3,1) = -1`, `(3,1) = 2`,
`round_div(-7,2) = -3`, `(7,2) = 4`). A Rust port imports the frozen integer constants and tables
from the artifact; it must not regenerate them from transcendental functions.

**Saturation contract (normative; Astra r4 items 1-2).** The admitted domain of every tensor value
is the full int16 range [-32768, 32767], both endpoints included, at every input, every op output and
every export; every static bound uses the factor 32768. `clamp16(v)` returns -32768 for every
`v < -32768` and 32767 for every `v > 32767`, and each such element is one clip event. Worked
example (noising, admitted inputs `C = noise = -32767`): `acc = (63540 + 16053) * (-32767) =
-2608023831`, `rshift_round(acc, 16) = -39795`, `clamp16 -> -32768`, one clip event counted under
`C_t`; the positive twin gives +39795 -> 32767. A port that returns -32767 there disagrees with the
oracle. Every clipping event is counted, under a name, in the same pass that produces the value:
input quantisation (`input:C`, `input:noise`, `input:E`, `input:coord`, elements outside the domain
after ties-to-even rounding), the `C_t` clamp, every op output (convolution requantisation,
GroupNorm affine, add, concat, avg-pool, bilinear), and every activation-table lookup whose index
carries mask 1 (`lut_clipped_hit:<layer>`; e.g. input 32767 into the `silu 11->12` table returns
32767 and counts one hit). Three tables have clipped entries by construction (`silu 11->12`: 16378
of 65536, `silu 10->11`: 16384, `silu 9->10`: 16384, all in the upper half of the input domain);
the masks are exported as arrays (`LUTMASK:kind:f_in:f_out`, uint8, sha256 in the manifests and in
`constants_*.json`), and `EXP_TABLE_CLIP_MASK` is exported all-zero because the exp table is an int64
table in [0, 2^20] to which no clamp applies (the index clamp to 32767 is not a clip event). The
total clip count is part of the relation's output: it is **0** in every run of this artifact (222 +
502 + 5 integer forwards), and a proof must carry the count it observed rather than assume zero.

**Noising.** `C_int = rint(C_bf16 2^12)`, `noise_int = rint(noise 2^12)` (the target), `E_int =
rint(E_bf16 2^14)`, coordinates `rint(linspace(-1,1,n) 2^14)`; `C_t = clamp16((63540 C_int + 16053
noise_int + 2^15) >> 16)` with `63540 = rint(0.9695360064506531 2^16)`, `16053 =
rint(0.24494898319244385 2^16)` from the trainer's float32 `sqrt_alphas_cum[150]`,
`sqrt_one_minus_alphas_cum[150]`.

**Convolution.** Per output channel `s_c = max_k |W[c,k]| / qmax` (qmax 32767 int16, 127 int8),
`Wq = rint(W/s_c)`; `acc = sum_k Wq[c,k] x[k]` exact; `y = clamp16(rshift_round(acc M_c + b'_c, S))`,
`M_c = rint(s_c 2^(f_out-f_in+S))`, `b'_c = rint(bias_c 2^(f_out+S))`, `S` per layer so that `max M_c`
has `min(24, 62 - bitlen(32768 max_c L1(Wq[c])))` bits. This checkpoint: int16 S in [38, 43],
multipliers 23-24 bits; int8 S in [30, 35], 24 bits. The t=150 term `t_proj.weight @ silu(t_emb) +
t_proj.bias` is folded into every ResBlock conv1 bias before quantisation (float64, once).

**GroupNorm.** Groups: largest of 32,16,8,4,2,1 dividing C (16->16, 32->32, 48->16, 64->32,
96->32, 128->32); biased variance; `n = C/G * H * W` (<= 32256). With `x` at `f_in`:
`S1 = sum x`, `S2 = sum x^2`; `N = n S2 - S1^2 + n^2 eps_int`, `eps_int = max(1, rint(1e-5
2^(2 f_in)))` = 1, 1, 3, 10, 42, 168 for f_in 7..12 (the exact identity `N = n^2 2^(2 f_in) (var +
eps_q)` holds for the quantised `eps_q = eps_int 2^(-2 f_in)`); `mu6 = round_div(64 S1, n)`;
`e_i = 64 x_i - mu6`; `Q = isqrt((n 2^(f_out+24))^2 // N)` (T = 30); `Mg_c = round_div(gamma_q[c] Q,
2^12)` with `gamma_q = rint(gamma 2^12)`; `y_i = clamp16(rshift_round(e_i Mg_c, 30) + beta_q[c])`,
`beta_q = rint(beta 2^f_out)`. `isqrt(m)`: Newton from `x0 = 2^ceil(bitlen(m)/2)`, `x <- (x + m//x)
>> 1` while decreasing; the result is the floor root, verified by `x^2 <= m < (x+1)^2`, so the
iteration count is not part of the contract. `n S2`, `S1^2`, `N`, `X^2 // N` are formed in
unbounded Python integers here and need 128-bit integers in Rust.

**Activations.** One 65536-entry int16 table per (kind, f_in, f_out), `table[i] =
clamp16(rint(act((i-32768) 2^-f_in) 2^f_out))`, index `x + 32768`; GELU exact erf form. Eight
tables for this checkpoint (`gelu 11->11`; `silu 9->9, 9->10, 10->10, 10->11, 11->11, 11->12,
12->12`), bytes frozen by sha256 in the manifests.

**Attention.** `q, k, v` share the qkv conv's f (11, 12, 11); scores `s_ij = sum_c q_ic k_jc`
exact; the logit scale `1/sqrt(head_dim)` is `(mult, shift)` from `kernels.attention_scale`: for
head_dim 16 `mult 1, shift 2 f_q + 2 - 10` (exact: /4 is a shift), so `u = min(rshift_round(m_i -
s_ij, shift), 32767)`, `w = EXP[u]`, `EXP[u] = rint(exp(-u/2^10) 2^20)` (32768 entries, zero beyond
u = 15.2 x 1024, `EXP[0] = 2^20` so the denominator is positive), `out_ic = round_div(sum_j w_ij
v_jc, sum_j w_ij)` at the qkv scale.

**Width 12 (item 10, specification only; not exercised).** Four heads over 48 channels give
head_dim 12; the kernel then uses `mult = 18919 = rint(2^16 / sqrt(12))`, `shift = 2 f_q + 16 - 10`
(relative error 2.1e-5 in the logit scale, i.e. below the 2^-10 exponent resolution), verified
against the scalar reference in `kernels.selftest`. The final 36-channel concat at 96x112 has four
GroupNorm groups of 9 channels, `n = 96768`: `S2 <= n 2^30` still fits i64 (2^46.6) but `n S2`,
`S1^2` and `N` reach 2^63.5 and must be 128-bit; the bounds table must be regenerated for that
width (`static_bounds` does this from the traced shapes). Recalibration follows the same command.

**Pooling, resampling, residuals, score.** `avg_pool2d(2)`: `clamp16(rshift_round(a+b+c+d, 2))`;
bilinear x2 (align_corners=False): per axis `out[2k] = in[max(k-1,0)] + 3 in[k]`, `out[2k+1] = 3
in[k] + in[min(k+1,n-1)]`, both axes then `clamp16(rshift_round(sum, 4))` (verified against
`F.interpolate` / `F.avg_pool2d` exactly, borders included); add and concat align to `max(f_a,
f_b)` by exact left shift and round once to the output scale; the residual sum `R = sum (eps_int -
noise_int)^2` is exact (< 2^48), MSE units `R / (43008 2^24)`; the paired statistic is the exact
comparison `5 R_c < sum_o R_w,o`.

## 4. Static bounds bound to the frozen constants (item 5)

Computed by `IntBackend.static_bounds` from the authenticated quantised weights, the traced shapes
and the admitted domain (factor 32768), Python integers throughout; exported under `static_bounds`
in the constants and manifests, per layer and globally. For this checkpoint:

| quantity | int16 weights | int8 weights | note |
|---|---|---|---|
| convolution accumulator, max over layers of `32768 x max_c L1(Wq[c])` (bounds every partial sum) | **353,174,814,720** (39 bits) | **1,368,850,432** (31 bits) | i64 |
| requantisation expression `acc_bound x M_max + max\|b'\| + 2^(S-1)`, max over layers | **3,812,976,885,203,206,144** (62 bits, < 2^63) | 22,661,745,809,484,953 (55 bits) | i64 |
| GroupNorm `n` max / `S2 <= n 32768^2` / `N <= n^2 (32768^2 + eps_int)` | 32256 / 45 bits / **60 bits** | same | S2 i64; `n S2`, `S1^2`, `N` in 128-bit |
| GroupNorm `X = n 2^(f_out+24)`, `X^2` | **99 bits** | same | u128 for `X^2 // N` and its isqrt |
| GroupNorm affine `\|e_i\| x \|Mg_c\|` via Cauchy-Schwarz (`\|x_i - mu\| <= sqrt(n) sigma`) and `Q <= X/sqrt(N)` | **< 2^50** | same | i64 |
| attention: `\|s\| <= 16 x 2^30` (34 bits), `den <= 168 x 2^20`, `2 num + den` | 44 bits | same | i64 |
| noising `(63540 + 16053) x 32768` | 2,608,103,424 (32 bits) | same | i64 |
| add/concat sum `2 x 32768 x 2^15`; avg-pool `4 x 32768`; bilinear `16 x 32768` | 2^31; 2^17; 2^19 | same | i64 |
| SSE `43008 x 65535^2`; paired sum `5 x SSE` | **184,712,316,364,800**; 923,561,581,824,000 | same | i64 |

Observed maxima in the runs sit well inside: largest conv accumulator 34 bits (int16) / 26 bits
(int8). Consequence for the guest: i64 accumulation with operands widened before multiplication is
sufficient everywhere; u128 (or i128) is needed only for GroupNorm's `n S2 - S1^2`, `X^2 // N` and
the integer square root.

## 5. Noise (item 7) and the normative August noise rule

The Philox4x32-10 words are exact (three Random123 known-answer vectors; stream positions verified
per row against the evaluator's row order and the RNG offsets of both checkpoints). The float32
Box-Muller transform uses libm `log`/`sin`, cuRAND uses `logf`/`__sincosf`: the correspondence to
the GPU's samples is approximate (about 1e-6 per sample; Astra measured that a 4.77e-7 perturbation
flips two Q12 target integers on d2/1328). Therefore the **exported bytes are normative**: every
vector manifest and every August input file carries `noise_int` (Q12, ties-to-even, the target and
the noising input) together with the `noise_f32` stream it was rounded from, both hashed. A proof
binds those bytes; nothing re-derives them from CUDA.

**Normative August noise (binding, coordinator 2026-09-07).** For proof row `r` in 600..711 the
noise tensor is `randn_cuda_emul(seed=20260823, call_index=r-600)` (`common.py`): Philox4x32-10
with the Random123/cuRAND constants (multipliers `0xD2511F53`, `0xCD9E8D57`; key bumps
`0x9E3779B9`, `0xBB67AE85`; 10 rounds), key `(20260823, 0)`, and for element `e` in 0..43007 of the
flattened `(4, 96, 112)` tensor (channel-major, then row, then column) the counter
`(r - 600, 0, e, 0)`; of the four output words `(x, y, z, w)` the sample is Box-Muller lane x in
float32: `u = x * 2^-32 + 2^-33`, `v = y * (2^-32 * 2pi) + 2^-33 * 2pi` (float32 constants
`2.3283064e-10` and `2.3283064e-10 * 6.2831855`), `sample = sqrt(-2 ln u) * sin(v)`, computed with
numpy float32 `log`/`sin`; then `noise_int = rint(sample * 2^12)` with ties to even, clamped to
int16. `C_t_int = clamp16((63540 * C_int + 16053 * noise_int + 2^15) >> 16)`. The guest takes
`noise_int` as its witness item `noise` (86,016 bytes, int16 little-endian Q12, 4x96x112; exactly
the `noise_int` array of `august_inputs/row_NNNNNN.npz`) and publishes `BLAKE3(noise)` in its public
output (RELATION.md section 1.1, offset 660); it derives `C_t` in-circuit from the committed frame's
whole-frame reduction and that noise (`noise.rs`, RELATION.md 2.3), so `C_t` is not supplied and no
`C_t` hash is published; the constants blob is bound by SHA-256 (offset 564). The exported `Ct_int`
is the oracle's expected value of that derivation, for checking the guest. The per-row mapping row ->
noise file -> call index -> BLAKE3 (with the sha256 file-integrity hash) is the `noise_map` table in
`august_inputs/manifest.json`, which the acceptance verifier checks row by row. The `noise_f32`
array is exported for reference only. August rows
are not in the frozen evaluator's d2/v10 streams; this rule is the definition for them, and the same
rule applied to the blocks of d2/v10 reproduces the evaluator's stream positions (section 2).

## 6. Test vectors (`vectors/`) and August guest inputs (`august_inputs/`)

`vectors/vectors_{int16,int8}_{d2_1328,august_650}_{correct,wrong_p2}.{npz,json}`: inputs
(`IN:C_int`, `IN:noise_int`, `IN:noise_f32`, `IN:Ct_int`, `IN:E_int`, `IN:coord_int`), all 188
layer outputs (`T:<name>`, int16, with `f` and `scale_source`), quantised weights (`W:` int16 or
int8), `M:`/`BP:` (int64), GroupNorm `GQ:`/`BQ:`, `LUT:kind:f_in:f_out`, `EXP_TABLE`; the manifest
gives every array's sha256, the scale map, rounding rules, domain, bounds, clip events and the
residual sum. A port is byte-exact when every `T:` hash and the residual sum match.

| scheme | row | condition | residual sum (int) | MSE |
|---|---|---|---|---|
| int16 | d2 1328 (stream 30) | correct | 8764459045 | 0.012147 |
| int16 | d2 1328 | wrong +2 (row 1330) | 22311372969 | 0.030921 |
| int16 | august 650 (index 50) | correct | 5317378656 | 0.007369 |
| int16 | august 650 | wrong +2 (row 652) | 12127686594 | 0.016808 |
| int8 | d2 1328 | correct | 9006417833 | 0.012482 |
| int8 | d2 1328 | wrong +2 | 22578064838 | 0.031291 |
| int8 | august 650 | correct | 5661729244 | 0.007847 |
| int8 | august 650 | wrong +2 | 12505149149 | 0.017331 |

`august_inputs/row_NNNNNN.npz` for every row 600..711 (`august_inputs.py`): `C_int`, `noise_int`
(normative target and noising input), `noise_f32` (reference only), `Ct_int` (as the guest consumes
it), `E_correct`, `E_wrong` (the rule-pair hint, present when that row is on this box), plus the
shared `coord_int.npy`; `manifest.json` gives per row the nominal offset, the effective offset,
`offset_rule` (`direct` or `mirrored`), the wrong row, `wrong_available`, sha256 per array, and,
where the agreement run exists, the expected int16 and int8 residual sums for the correct and
rule-pair conditions; the header carries the normative noise rule verbatim.

**Proof-set rule (binding, coordinator 2026-09-07).** Every row 600..711 (held out from weight
training; see the calibration disclosure in 7b) is a proof row,
one proof each; the nominal wrong offset is `[-2, +2, -15, +15, +30][(r - 600) mod 5]`. Boundary
clause: when `r + offset >= 712` the mirrored offset `-offset` is used, which affects ten rows:
684, 689, 694, 699, 704, 709 (+30 -> -30), 698, 703, 708 (+15 -> -15), 711 (+2 -> -2); their
`E_wrong` is the mirrored pair's hint and the manifest marks `offset_rule = mirrored`. Four rows keep
the direct rule with a wrong hint from a training row below 600 (600 -> 598, 602 -> 587,
607 -> 592, 612 -> 597); those four E files were pulled from the Lambda cache into `rows_august/`
and the pairs are complete (`wrong_available: true` for all 112 rows). Every in-range protocol offset and the required -30 mirrors are
reported for every row.

### 6a. Differential boundary fixtures (`fixtures/`, Astra r4 item 4)

`fixtures.py` (stage `fixtures` of the freeze command) writes 42 fixtures from the SCALAR oracle
(`kernels.py` scalar helpers and `*_ref` kernels), each cross-checked against the numpy kernels
before writing: one `<name>.json` per fixture with `kernel`, `params`, `inputs`, `expected` and
`counters` (clip events exactly as the oracle counts them), arrays inline or in `<name>.npz` with
sha256; `fixtures/manifest.json` lists every file's sha256 and the used shifts
{2, 4, 14, 16, 30..35, 38..43} and divisors {84, 336, 672, 1344, 2688, 4096, 8064, 10752, 32256}.
Coverage: `rounding_shifts_ties` (signed ties and neighbours at every used shift plus 1..8),
`rounding_shifts_zero_negative` (exact left shifts), `rounding_divisors_ties` (every GroupNorm
group size, 2^12, odd attention-style denominators), `domain_endpoints_clamp16`,
`noising_saturation` (includes the -39795 -> -32768 case), `conv3x3_impulses_s{1,2}_w20` and
`_s2_w21` (corner and edge impulses with taps 1..9, output widths 20 / 10 / 11, stride-2 tail),
`conv_requant_saturation_S{30,43,8}` (positive and negative saturation with counters),
`conv3x3_random_{int16,int8}_s{1,2}_w24` (full-domain random inputs, output width 24 / 12),
`add_saturation_rescale` (four f combinations), `concat_saturation_rescale`,
`groupnorm_{constant_group, nearly_constant_group, endpoints_n84, balanced_endpoints_n32256,
saturation_both_signs, zero_gamma}` (n = 84 and the maximum n = 32256; per-group Q exposed),
`isqrt_perfect_squares` (k^2 and +-1 up to 2^102, decimal strings), `avgpool2_ties`,
`bilinear_up2_border_{1x1, 2x2, 2x3, 3x3}` (with the x16 sums before the single rounding),
`lut_all_indices_<kind>_<f_in>_<f_out>` (all eight tables: every index, table and mask, expected
hits = clipped entries, hit for input 32767 flagged), `attention_{equal_scores,
exponent_clamp_boundary, signed_weighted_average, head_dim12_multiplier}` (head-0 scores, u,
weights and denominators exposed), `sse_endpoints` (184712316364800 at the endpoints). Randomised
and full-network comparisons remain in `vectors/` and `august_inputs/`.

## 7. Results

### 7a. Protocol rows: integer against the frozen evaluator (37 rows x 5 offsets = 185 pairs)

`agreement.json`, `AGREEMENT.md` (`agreement_int16.json`, `agreement_int8.json`). `R^f` is the
evaluator's own per-row score (A100, torch 2.7.0, bf16 autocast), so `eta` includes the evaluator's
bf16 path; the fp32 reproduction and both bf16 emulations are reported alongside. The integer path
covers the whole relation from `(C, noise, E)` to the residual sum. Zero clip events in all 444
integer forwards (inputs, C_t, every op, LUT hits); largest observed conv accumulator 34 bits (int16)
and 25 bits (int8) against the static bounds of 39 and 31 bits.

| scheme | reference | sign agreement | paired (int / ref) | D_q / eta min / p5 / median / p95 / max | pairs D_q > 3 eta | score error rel. median / max (signed mean) | eta median / max | weakest pair |
|---|---|---|---|---|---|---|---|---|
| **int16** | **evaluator** | **185 / 185** | 37 / 37 | **79.8** / 92.3 / 128.8 / 201.8 / 288.2 | **185 / 185** | 3.13e-3 / 1.02e-2 (-3.57e-3) | 1.73e-4 / 2.97e-4 | d2 2866 +2: D_q 0.023552, eta 2.95e-4 |
| int16 | fp32 | 185 / 185 | 37 / 37 | 547.5 / 669.5 / 1248 / 3804 / 16998 | 185 / 185 | 2.81e-4 / 1.70e-3 (+2.80e-4) | 1.80e-5 / 3.79e-5 | d2 2986 +15: D_q 0.018927, eta 3.46e-5 |
| int16 | bf16em (v1) | 185 / 185 | 37 / 37 | 84.1 / 101.6 / 147.0 / 238.5 / 424.1 | 185 / 185 | 2.59e-3 / 9.18e-3 (-3.04e-3) | 1.51e-4 / 2.64e-4 | d2 2826 -15 |
| int16 | bf16em_v2 | 185 / 185 | 37 / 37 | 84.8 / 96.7 / 148.6 / 270.9 / 536.5 | 185 / 185 | 2.61e-3 / 9.20e-3 (-2.99e-3) | 1.50e-4 / 2.54e-4 | d2 1528 -15 |
| int8 | evaluator | 185 / 185 | 37 / 37 | 19.2 / 23.1 / 32.7 / 46.7 / 69.0 | 185 / 185 | 1.10e-2 / 4.70e-2 (+1.39e-2) | 6.97e-4 / 1.10e-3 | d2 1608 -15: D_q 0.020142, eta 1.05e-3 |
| int8 | fp32 | 185 / 185 | 37 / 37 | 17.0 / 19.1 / 25.5 / 34.0 / 41.2 | 185 / 185 | 1.43e-2 / 5.75e-2 (+1.79e-2) | 8.90e-4 / 1.24e-3 | d2 1608 -2 |

Per offset (int16 vs evaluator, all 37/37 sign-agreeing and passing): min D_q/eta -2 92.2, +2 79.8,
-15 89.2, +15 83.3, +30 92.8; per session d2 79.8, v10 80.6. int8 vs evaluator per offset: -15 19.2,
-2 19.6, +15 21.4, +2 21.6, +30 21.2. Integer margin D_q (MSE units): int16 min 0.018699, median
0.022535, int8 min 0.018682, median 0.022599. Pooled AUROC (correct vs per-row wrong mean) on the
37-row subset 1.000 for d2 and v10 in float and both integer schemes; paired fraction 1.000. No
reversals against any reference. Rows whose margin exceeds three times the row's largest score
error: 37/37 in both schemes.

Network-only error (integer vs float64 network on the integer path's own inputs and target): int16
+4.2e-4 relative (std 4.4e-4, max 2.4e-3); int8 +1.80e-2 (std 1.0e-2, max 5.8e-2). The margins of
this checkpoint are about five times those of the step-12000 model (D_q min 0.0187 against 0.0032)
while `eta` against the evaluator is unchanged (median 1.7e-4), which is why the weakest int16 pair
moved from 16.1 to 79.8 times `eta`. int8's error grew (its inflation is now 1.4-1.8 % of the
smaller correct residual); it still passes every pair with a minimum of 19.2 and stays the cost
option, int16 the fidelity baseline.

### 7b. August proof rows 600-711 (integer int16 and fp32; no evaluator reference)

`agreement_int16_august.json`, `agreement_int8_august.json`, tables for every row in `AGREEMENT.md`.
112 rows, noise by the normative rule of section 5, all five protocol offsets plus the mirrored -30
where the rule needs it: 507 (row, offset) pairs on this box. The rule pair is complete for all
**112 rows** (ten boundary rows by the mirrored offset; the four training-row hints 598, 587, 592,
597 pulled from the Lambda cache).

| scheme | rule pairs | rule D_q (MSE) min / p5 / p25 / median / p75 / p95 / max (mean) | fp32 D_f min / median | D_q / eta_fp32 min / median | rule sign int+ / fp32+ / agree | all pairs int c<w / fp32 c<w | min D_q any pair | clips |
|---|---|---|---|---|---|---|---|---|
| **int16** | 112 | **0.007328** / 0.008141 / 0.008778 / **0.009161** / 0.009850 / 0.010578 / 0.010988 (0.009259) | 0.007328 / 0.009165 | 267.7 / 518.3 | **112 / 112 / 112** | **507 / 507** | 0.006776 | 0 |
| int8 | 112 | 0.007321 / 0.008166 / 0.008794 / 0.009174 / 0.009846 / 0.010591 / 0.010998 (0.009278) | same | 8.6 / 11.0 | 112 / 112 / 112 | 507 / 507 | 0.006788 | 0 |

**Calibration disclosure (Astra r5, finding 11).** The fixed-point scales of this artifact were
calibrated on 15 rows x 2 conditionings (own E and E of row+15): protocol rows d2 1328, 1528, 2866,
3066, 4404, 4604 and v10 1260, 2495, and August targets 600, 616, 632, 648, 664, 680, 696, that is
seven raw August targets and fourteen August conditioning identities (600, 615, 616, 631, 632, 647,
648, 663, 664, 679, 680, 695, 696, 711). August rows 600-711 were held out from weight training
(`august_train_rows 600`) but were not untouched by calibration: those seven targets and fourteen
hints influenced the integer scales (`constants_*.json -> calib_rows`, `calib_maxabs`). They must not
be described as an untouched test set; the proof set remains the complete 112 rows, disclosed as
such.

The four training-row pairs (int16): row 600 at -2 (hint 598) D_q 0.009450 (correct sum
4435539299, wrong 11254163581, eta 6.2e-6, ratio 1529); row 602 at -15 (587) D_q 0.010450 (ratio
296); row 607 at -15 (592) D_q 0.009450 (ratio 526); row 612 at -15 (597) D_q 0.010528 (ratio 351);
fp32 agrees in sign on all four (D_f 0.009456, 0.010455, 0.009454, 0.010524). No negative difference
on any row at any offset, in either scheme or in fp32; there is nothing to record on that side. The
weakest int16 rule pair is row 709 at the mirrored offset -30 (correct sum 4799388897, wrong
10087236535, D_q 0.007328, eta vs fp32 2.3e-5, ratio 317); the weakest int16 margin over all 507
pairs is 0.006776. The ten mirrored rows' rule D_q (int16): 684 0.008937, 689
0.008666, 694 0.010640, 698 0.009246, 699 0.009105, 703 0.008651, 704 0.008935, 708 0.009502, 709
0.007328, 711 0.009582. Integer correct residuals on August lie in 0.006078..0.008437 (MSE units),
about half the d2/v10 level, and the wrong residuals in 0.013980..0.019355 (median 0.016228), so the August
margins (median 0.0091) are smaller than the protocol rows' (0.0225) both in absolute terms and relative to the
correct residual: on the August rows the wrong residual is about 2.3x the correct one and the margin about 1.3x it,
against about 3.0x and 2.0x on the protocol rows (corrected in the published copy, 8 September 2026; the original
read "of the same relative size (about 2.3x the correct residual)", which confused the two ratios; RESULTS.md section 3). Each row's expected int16 and int8 residual sums for
the correct and rule-pair conditions are written into `august_inputs/manifest.json` beside the input
hashes, so the guest batch driver can check its residuals against the oracle row by row.

## 8. Astra round-3 items, disposition

| item | disposition |
|---|---|
| 1 scale map | one effective map, locked and asserted at execution; manifests and vectors carry it; superseded artifact's discrepancy documented in `../README.md` |
| 2 rounding | conversion ties-to-even vs runtime ties-toward-+inf stated in kernels, constants, manifests and here; exact left shift for s <= 0; Rust imports frozen tables |
| 3 domain | full int16 admitted, `abs <= 32767` checks removed, factor 32768 in every bound; input clips, C_t clamp, op clamps and LUT clipped hits all counted (0 in all runs); clipped LUT entries enumerated |
| 4 fixtures | tie, endpoint, constant-group and border fixtures added to `kernels.selftest` (29 checks) |
| 5 bounds | `static_bounds` from constants and shapes, exported; table in section 4; i64 with widened operands, u128 only for GroupNorm's squared numerator/division/root |
| 7 noise | exported bytes normative; CUDA correspondence stated approximate; August derivation defined |
| 8 bf16 fidelity | environment pinned (torch 2.7.0, A100); bilinear-promotion variant implemented and measured: indistinguishable at 1.1e-3 median, unresolved |
| 10 width 12 | 1/sqrt(12) multiplier specified and self-tested; 128-bit variance intermediates stated; bounds regenerate from shapes |
| 11 final checkpoint | this artifact; everything recomputed; one command for the next swap |
| 12 wording | corrected in `../README.md` (0.51 %, indices 0,5,...,30, f_in 8..13 with quantised epsilon, about 40x, "closer to fp32 scores") |

## 9. Open

1. **Rust parity**: open when this note was frozen; closed the same evening. The Rust kernels and the complete guest reproduce
   the vectors, the 42 fixtures and the August rows 600 to 603 (`source/FULL_GUEST.md` sections 4.1 to 4.4, `RESULTS.md`
   section 4); the vectors and August inputs were the acceptance fixtures.
2. **bf16 rounding-point fidelity** of the A100 run (item 8) is unresolved at the 1.1e-3 level.
3. **August rule pairs: closed.** The four training-row hints (598, 587, 592, 597) arrived on the development machine
   and rows 600, 602, 607, 612 are complete; the proof set reads 112/112 with every rule pair
   positive in int16, int8 and fp32.
4. The proof model may be swapped for a longer-trained checkpoint; section 0 is the procedure.
5. int8 remains a cost option (measured, section 7); int16 is the fidelity baseline.

## Log

- 2.0 (2026-09-07, BOSUN) — FINAL artifact for the seed-20260908 24k checkpoint under the
  revised contract (Astra r3); results filled from `agreement.py --report` the same evening.
- 2.1 (2026-09-07, BOSUN) — coordinator's binding decisions folded in: the per-row Philox rule
  is the normative August noise (section 5, witness bytes exported per row), the proof set is all
  112 rows with the boundary clause (ten mirrored rows, section 6); the mirrored -30 condition was
  computed as a supplement to the August runs and the report, August inputs and summary regenerated.
- 2.2 (2026-09-07, BOSUN) — training-row hints 598, 587, 592, 597 pulled to the development machine; rows 600,
  602, 607, 612 completed by supplement (5 new conditions per scheme), August set 112/112; report,
  inputs, summary regenerated. No other change.
- 2.3 (2026-09-07, BOSUN) — Astra r4 oracle-side items: LUT clipping masks exported and
  authenticated (vectors regenerated, residual sums unchanged), normative saturation contract
  written out (section 3), 42 differential boundary fixtures with expected bytes and counters in
  `fixtures/` (section 6a), `fixtures` stage added to the freeze command.
- 2.4 (2026-09-07, BOSUN) — Astra r5 finding 11: section 5 corrected to the real guest (noise
  witness with public BLAKE3, C_t derived in-circuit, constants SHA-256), calibration disclosure
  added here (7b) and in FREEZE_SUMMARY.md, per-row noise BLAKE3 map added to the August manifest.
- 2.5 (2026-09-08, BOSUN): published copy: banner with the layout mapping and the data-layer inputs, Rust parity closed in
  the status line and section 9, the section 7 ratio sentence corrected, `standard` renamed `direct` (agent audits r1).
