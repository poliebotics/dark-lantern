---
version: 1.3
date: 2026-09-09
status: relation side built and vector-tested on the development machine; network integrated (armc-int adapter, G2-D, see FULL_GUEST.md); August proof set prepared under the two-part offset rule; Astra r5 finding 1 applied (direct and mirrored offsets validated together, -30 admitted only as a mirror; ELF re-pinned in FULL_GUEST.md)
author: Cathal Ryan Hynes (author of record); drafted with BOSUN, the project's automated research assistant
---

> **Amended by G2-D (2026-09-07 evening), see `../FULL_GUEST.md` for the complete guest.** Four things in this
> document are superseded there: (1) public byte 11 is no longer reserved zero but the **offset-rule flag** (0 direct,
> 1 mirrored; section 1.1); (2) the witness has a tenth item, the one-byte offset-rule flag, and the guest reads the
> armc-int constants blob as an eleventh private input (section 1.2); (3) the network is no longer stubbed: the
> `zkdiff-armc-adapter` crate (`adapter/`) implements `net::Denoiser` over `armc_int::Constants` (kind 1), so
> sections 6 and 7's "stub" statements describe the state before integration; (4) public bytes 749..752, formerly
> reserved zero, carry the **clip-event flag and count** (G1 FINAL saturation contract, Astra r4): the noising leg no
> longer refuses a saturating witness (section 1.3 leg 11, section 6) but counts it, the network's clamps and
> masked-table hits are counted too, and the total is published (flag at 749, u16 LE at 750..752, saturating). The ELF,
> vkey and instruction counts of the complete guest are in FULL_GUEST.md; the stub ELF `4a0c8616…` and its 7.23 G
> count remain the record of the legs alone.
>
> **Amended again after Astra r5 (2026-09-07, night).** (5) The offset check of leg 1 validates direct and mirrored
> offsets TOGETHER (`statement::check_offset_rule`): under the direct flag `d` must lie in `{-2, 2, -15, 15, 30}`; under
> the mirror flag `-d` must lie in that set AND the direct wrong row `r - d` must lie outside `[0, row_count)`; in both
> cases `u = r + d` must lie inside. So `-30` is admitted exactly for the mirrored rows (684, 689, 694, 699, 704, 709 of
> the August set), where the shipped r4 guest had refused it before reaching the flag. The exact modulo assignment
> anchored at row 600 is `rule::august_assignment` and is enforced by the acceptance verifier (`script/src/accept.rs`,
> `zkdiff-verify`) on the public triple and byte 11, never by the guest, which does not know the batch to which it belongs.
> `PublicOutput::parse` applies the same admissibility check to the public fields. Section 1, 1.1, 1.2, 1.3 leg 1,
> 5 and 7 below are updated in place; the pins are in FULL_GUEST.md v1.2.

# ARM-C relation: the two-evaluation diffusion statement, everything except the network

Scope of this crate set (`g2_guest/armc-relation/`): the whole-frame reduction, the XOF hints, the integer forward
noising, the two-row statement, the session binding (frame hash, chain advance, drand beacons, both pattern renders,
both leaf openings), the public layout, the SP1 6.4.0 guest skeleton, and the host tooling (execute, ceremony, batch).
The integer network kernels are the sibling crate `g2_guest/armc-int/` and enter only through the `net::Denoiser`
trait; a stub stands in until its adapter lands (section 6). Every number below is tagged **[measured]** (read from a
test, log or file on the development machine), **[derived]** (arithmetic on measured numbers) or **[pending]** (needs data from the node).

Companion files: `../vectors_relation/` (reference vectors with `MANIFEST.json`, README there), `b3xof/PROVENANCE.md`
(the copied proved crate), `runs/` (logs of the execute, vkey and batch-prepare runs of 7 September).

## 1. The statement

For a pinned session (context digest and ordered-session root), a proved row `r` and a declared wrong row
`u = r + d`, where either the direct flag is set and `d` lies in the protocol's offset set `{-2, +2, -15, +15, +30}`,
or the mirror flag is set, `-d` lies in that set and the direct wrong row `r - d` lies outside the session (so
`d in {+2, -2, +15, -15, -30}` is admissible only as a mirror, `-30` only when `r + 30` leaves the session), the guest:

1. hashes the complete raw frame of row `r` and re-derives its chain advance `S_{r+1}`;
2. verifies the quicknet beacons of rows `r` and `r-1` (signature under the compiled-in quicknet key, randomness
   `SHA-256(sig)` equal to the chain-log value each advance consumed) and re-derives `S_r` from row `r-1`'s record;
3. regenerates both emission patterns from `S_r` and `S_u` (XOF, four-octave integer render), digests them, and requires
   row `u`'s digest to equal its witnessed leaf field (row `r`'s digest goes into its leaf);
4. opens both leaves to the same committed ordered-session root under the session context;
5. derives the integer inputs from the frame and the two XOF streams (section 3), forward-noises the frame at t = 150
   with the pinned noise tensor, evaluates the pinned integer denoiser once under each conditioning with the same `C_t`
   and the same noise target;
6. publishes `R_correct`, `R_wrong`, `D = R_wrong - R_correct`, its sign and the common denominator, together with
   every binding digest.

Claim: execution binding only, in the Astra verdict's words (`ASTRA_VERDICT_zkdiff_r1.md`, "The statement that must be
proved"; r2 finding 7). The statement says nothing about physical capture, realness, liveness or generalisation.

### 1.1 Public output `ZBDIFF01` (752 bytes, little-endian unless stated; `statement.rs` `PublicOutput`)

| offset | bytes | field | how constrained |
|---:|---:|---|---|
| 0 | 8 | magic `ZBDIFF01` | fixed |
| 8 | 1 | ABI = 1 | fixed |
| 9 | 1 | protocol = 9 (TB-v0.9) | fixed |
| 10 | 1 | denoiser kind (0 stub, 1 armc-int) | from the network implementation; a stub proof is labelled as such |
| 11 | 1 | offset-rule flag: 0 direct, 1 mirrored (G2-D; was reserved 0) | witness item 10; direct: `d` in the set; mirrored: `-d` in the set and `r - d` outside `[0, row_count)` (Astra r5: both validated together in `check_offset_rule`; `-30` only here) |
| 12 | 4 | public length = 752 | |
| 16 | 4 | row `r` | header; `1 <= r < row_count` |
| 20 | 4 | row `u` | `u = r + d`, `0 <= u < row_count`, equals the witnessed leaf's row |
| 24 | 4 | declared offset `d` (i32) | direct: `d` in `{-2,2,-15,15,30}`; mirrored: `-d` in that set; `u = r + d` inside; the exact August assignment `rule::august_assignment(r)` is checked by the acceptance verifier from `r`, `u`, `d` and byte 11 |
| 28 | 4 | row count | session context |
| 32 | 2 | tree depth | minimal for the row count |
| 34 | 2 | session id length; 36..164 session id, zero padded to 128 | session context |
| 164 | 128 | `S_0`, `S_N`, authority-manifest SHA-256, chain-log BLAKE3 | inputs to the context digest |
| 292 | 32 | context digest | recomputed |
| 324 | 32 | ordered-session root (wrapped) | both leaves open to it |
| 356 | 64 | `leaf_r`, `leaf_u` | recomputed |
| 420 | 32 | `BLAKE3(raw_r)` | recomputed from the frame |
| 452 | 64 | emission digests of `r` and `u` | recomputed by the render |
| 516 | 16 | previous and own drand rounds (u64 BE) | both signatures verified |
| 532 | 32 | drand leg digest `BLAKE3("ZBDIFF:DRAND:v1\0" ‖ round_{r-1} ‖ v_{r-1} ‖ round_r ‖ v_r ‖ quicknet chain hash)` | recomputed |
| 564 | 96 | constants SHA-256, spec SHA-256 (network), preprocessing spec SHA-256 (this crate, `spec.rs`, pinned `025de070…f4a5`) | compiled constants |
| 660 | 32 | noise BLAKE3 | recomputed from the witness |
| 692 | 4+8+8+4 | timestep 150, SA 63540, SO 16053, shift 16, F_CT 12, F_HINT 14, F_EPS 12 | fixed |
| 716 | 8+8+8+8 | `R_correct`, `R_wrong` (u64), `D` (i64), denominator `43008 · 2^24 = 721,554,505,728` | outputs |
| 748 | 1 | sign (1 if `D > 0`) | derived |
| 749 | 1+2 | (G2-D) clip flag (1 iff the count is nonzero), clip-event count u16 LE saturating at 65535: noising clamps + both network passes' clamps and masked-table hits | recomputed; the noising leg no longer refuses |

The proved relation kept `S_t`, the raw digest and the emission digests private and published only the root. This
statement publishes the raw and emission digests and both leaves because the August `chain_log.csv` is public and
carries them (`bayer_blake3_hex`, `emission_live_pixel_blake3_hex`); the task asked for them in the layout.

### 1.2 Private witness (ten `read_vec` items, in order; `statement.rs` `Witness`)

| # | item | bytes | content |
|---|---|---:|---|
| 1 | `header_r` | 120 | `ZBROWW01`: row `r`, `S_r`, meta (28), drand round, drand value (join lib.rs 96-161, copied to `header.rs`) |
| 2 | `membership` | 184 + id + 32·depth | `ZBOSM001`: session context, committed root, siblings of row `r` (membership lib.rs 169-265, copied to `membership.rs`) |
| 3 | `raw_r` | 24,472,000 | the row's raw Bayer frame |
| 4 | `sig_r` | 48 | quicknet signature of row `r`'s round |
| 5 | `previous` | 188 | `ZBDPRV01`: `S_{r-1}`, `BLAKE3(raw_{r-1})`, meta, round, value, signature of row `r-1` |
| 6 | `leaf_u` | 208 | `ZBDLFU01`: row `u`'s leaf fields (`S_u`, raw digest, meta, round, value, `S_{u+1}`, emission digest) |
| 7 | `siblings_u` | 32·depth | row `u`'s path |
| 8 | `noise` | 86,016 | int16 LE Q12, 4x96x112 |
| 9 | `offset` | 4 | i32 LE `d` |
| 10 | `offset_rule` | 1 | (G2-D) 0 direct, 1 mirrored; an empty item reads as direct; validated together with item 9 (`check_offset_rule`) |

The guest reads one further private input after these ten: the armc-int constants blob (3,476,866 bytes for the
FINAL int16 constants in blob format v2 with the clipping masks; an earlier revision of this note recorded 3,411,318 bytes,
the size before the masks were added, corrected in the published copy on 8 September 2026), whose SHA-256 is the public `constants_sha256` (offset 564); it is not part of `Witness`
because `evaluate` takes the network as a trait object (FULL_GUEST.md section 2).

Row `u`'s raw frame is never needed: its leaf commits it. The previous-row record is an explicit witness rather than a
parse of the anchored August CSV prefix (august.rs `verify_previous_advance`, lines 340-367), so the same leg serves any
session whose beacon signatures are known.

### 1.3 Relation, leg by leg (`statement.rs` `evaluate`, the order the guest runs)

| # | leg | cycle-tracker label | reuse |
|---|---|---|---|
| 1 | parse the ten items; `r >= 1`, `r < n`; `check_offset_rule(r, n, d, flag)`: direct `d` in the set, or mirrored `-d` in the set with `r - d` outside `[0, n)`; `0 <= u = r + d < n`; `leaf_u.row == u`, `meta_{r-1}` names `r-1` | `parse_witness` | header and `ZBOSM001` parsers copied; offset rule new (Astra r5) |
| 2 | digests: preprocessing spec (`spec.rs`), network constants and spec (`Denoiser`) | `constants` | PREPROCESS_SPEC pattern of join lib.rs 66-71, 297-302 |
| 3 | `verify_quicknet_beacon(round_r, sig_r)`, `SHA-256(sig_r) == v_r` | `drand_verify` | join lib.rs 251-283, copied to `beacon.rs` |
| 4 | `BLAKE3(raw_r)`; `S_{r+1} = advance_chain(S_r, BLAKE3(raw_r), meta_r, round_r, v_r)` | `raw_blake3_24MB` | b3xof `blake3p::hash`, `advance_chain` |
| 5 | verify and bind `sig_{r-1}`; `advance_chain(S_{r-1}, …) == S_r`; row 0 refused | `previous_advance_leg` | august.rs logic with explicit witnesses |
| 6 | `expand_all(S_r)`, render 1080 rows, streaming BLAKE3 | `emission_render_r` | join lib.rs 334-350 (`emission.rs`) |
| 7 | the same for `S_u`; digest must equal `leaf_u.emission_blake3` | `emission_render_u` | |
| 8 | `leaf_r = H(ROW, …, S_{r+1}, emission_r)`, `leaf_u` from the witness; both open to the root | `ordered_session_membership` | membership lib.rs 341-412 |
| 9 | whole-frame reduction to `C_int` | `frame_reduce` | new (`frame.rs`) |
| 10 | `E_int` for both streams, coordinates, 14-channel hints | `hints` | new (`hint.rs`), XOF from b3xof |
| 11 | `BLAKE3(noise)`, `C_t = clamp16((SA·C + SO·noise + 2^15) >> 16)`; saturations counted into the public clip count (G2-D; formerly refused) | `noise` | new (`noise.rs`) |
| 12 | `eps_r = f(C_t, hint_r)`, `R_correct = Σ(eps_r - noise)^2` | `denoiser_correct` | trait |
| 13 | `eps_u = f(C_t, hint_u)`, `R_wrong` | `denoiser_wrong` | trait |
| 14 | encode and commit | `public_commitment` (guest) | |

The guest (`program/src/main.rs`) reads the items, calls `evaluate` with the network implementation and commits the
bytes; the host oracle calls the same `evaluate` natively, so a zkVM/native divergence is detectable, as in the b3xof
relation. Every check fails closed with a static message (`RelationError`), and `tests/vectors.rs`
`end_to_end_negative_controls_fail_closed` exercises nine of them on the synthetic session.

## 2. Preprocessing semantics, exactly, with the pipeline lines

### 2.1 The frame (`frame.rs`)

Pipeline: `train_lean.py` `load_C`, lines 120-133, then the cache and the evaluator.

```text
x   = raw.reshape(4600, 5320)                                              # 128
cfa = stack([x[0::2,0::2], x[0::2,1::2], x[1::2,0::2], x[1::2,1::2]])     # 129   planes R, G1, G2, B
t   = float32(cfa) / 255.0                                                 # 132   float32 division
C   = F.interpolate(t[None], size=(96,112), mode="area")[0]                # 133   adaptive_avg_pool2d, CPU
cache = float16(C)                                                          # precache.py 41
C_f32 = float32(cache); C_bf16 = bfloat16(C_f32)                            # train_lean.py 123; lean_pubproto_eval.py 125
C_int = clip(rint(C_bf16 * 2^12), int16)                                    # g1_integer/int_ref.py 266
```

`mode="area"` is `adaptive_avg_pool2d`: output bin `i` covers input indices `[floor(i·in/out), ceil((i+1)·in/out))`.
For 2300 -> 96 and 2660 -> 112 the bins are 24 or 25 wide and neighbouring bins overlap by one row or column
(`area_bins`; bin sizes 576, 600, 625 **[measured]**). The CPU kernel accumulates each bin **sequentially in float32,
row-major within the bin**, then divides by `kh` and then by `kw`, both in float32. This was pinned empirically, not
recalled: on a random full-size frame the emulation reproduces torch 2.11.0's output bit for bit (0 of 43,008
mismatches), whereas the exact rational mean cast to float32 differs in 39,094 positions (`gen_vectors.py`, notes
`synthetic_frame_*_stats`) **[measured]**. The Rust `reduce_torch_f32` follows that order with a 256-entry
`float32(v)/255` table (each entry is the correctly rounded IEEE quotient, as numpy's) and IEEE `f32` adds and
divisions, which the SP1 target executes in software (compiler-rt soft-float, IEEE round-to-nearest-even), so the guest
reproduces the CPU kernel exactly. The cache path `cache_quant` is `f32 -> binary16 (RNE, subnormals included) -> f32 ->
bfloat16 (RNE on bits) -> round_ties_even(x · 2^12) -> clamp16` (`fp.rs`), tested on 8,192 numpy/torch vectors with
injected exact ties, and on frame b, whose dark band produces 7,313 binary16-subnormal means and 751 zero means
**[measured]**.

The rational alternative `round_half_even(sum · 2^12 / (255 · count))` is implemented too (`reduce_exact`,
`quant_exact`) and tested against a `fractions.Fraction` reference, but it is a *different function*: it differs from
the pipeline's `C_int` in 39,077 (frame a) and 24,962 (frame b) of 43,008 positions **[measured]**, because bfloat16
keeps 8 significant bits (a spacing of 16 Q12 units in `[0.5, 1)`). The guest uses the pipeline path, so the integer
inputs are the ones the G1 reference validated (the G1 `C_int` hash of d2 row 1328 is reproduced from the cache, and
`E_int` of rows 1328 and 1330 from the chain log; section 5). Design decision recorded: exactness to the trained
pipeline over arithmetic elegance; the cost is soft-float in the guest (section 4).

### 2.2 The hint (`hint.rs`)

Pipeline: `train_lean.py` `_load_E_uncached`, lines 142-153; `src/data/xof_generation.py`; `ArmCUNet._build_hint`,
lines 161-165; `diffusion_diagnostic_model.py` `coord_grid` (channel 0 = x over the width, channel 1 = y over the
height, g1_integer/README.md s.2).

```text
seed_c  = BLAKE3(b"TB:SEED:{R,G,B}:v8" || S_r)               # derive_xof_seeds; S_r is the row's OWN state (offset 0,
stream  = BLAKE3(seed_c).xof(43110)                            #   train_lean.py 38-52, the v9 blocking loop)
grids   = 17x30, 34x60, 68x120, 135x240 uint8 per channel     # expand_seed_to_octaves
oct_o   = float32(stack(R,G,B)) / 255.0                       # xof_octaves_from_s_next
ups_o   = F.interpolate(oct_o[None], (96,112), "area")[0]     # 152: same kernel; octaves 0-2 upsample (bins of 1-2), 3 downsamples
E       = cat(ups_0..3)                                       # 153: channel 3*o + c
E_int   = clip(rint(bfloat16(float32(float16(E))) * 2^14))    # cache, bf16, int_ref.py 274
coord   = rint(linspace(-1,1,n) * 2^14)                       # exact rational -1 + 2k/(n-1); no ties for n = 96, 112
hint    = cat(E_int (12), coord (2))                          # 14 x 96 x 112 int16 Q14
```

### 2.3 Noising and residual (`noise.rs`)

`SA = round(sqrt(alphas_cum[150]) · 2^16) = 63540`, `SO = round(sqrt(1 - alphas_cum[150]) · 2^16) = 16053` from the
trainer's float32 constants (`vectors_int16_correct.json` `noising`; `diffusion_diagnostic_model.py` 317-339, cosine
schedule); `C_t = clamp16((SA·C_int + SO·noise_int + 2^15) >> 16)`; `R = Σ (eps - noise_int)^2` exact in u64 (< 2^48);
MSE units `R / (43008 · 2^24)`. The noise tensor is a witness pinned by BLAKE3; its correspondence to the evaluator's
CUDA Philox stream (one generator per session seeded 20260823, one draw per row in row order,
`lean_pubproto_eval.py` 122-126) is an off-circuit provenance fact, as the verdict says. For the d2 row 1328 the G1
emulation (`g1_integer/common.py` `randn_cuda_emul`, index 30) reproduces G1's `noise_int` and `Ct_int` hashes
**[measured]**. For the August rows the protocol has no noise branch (the evaluator walks d2/v10 blocks only), so the
August noise: `../vectors_relation/august/noise_proposal/` held a labelled proposal (the same emulated stream, seed 20260823,
draw index `r - 600`); it was adopted as the normative August noise rule (`oracle/final/README_FINAL.md` section 5), and the
published copy of that set is `noise_august/` (the `noise_proposal/` duplicate is omitted, `REDACTION.md`).

## 3. What is reused from the proved tree (paths, read-only; copied, never edited)

Root: `[zeebeam repository clone]/bundle/proofs_20260902/source/`.

| this crate | source | what |
|---|---|---|
| `b3xof/` (verbatim, sha256 in `b3xof/PROVENANCE.md`) | `deps/BOSUN/scratch/zeebeam_lambda_artifacts_20260824/reviews/post_hold_followup_closure_20260825T0446Z/b3xof_experiment_snapshot/source/sp1/relation/` | pure-Rust BLAKE3 and XOF, seeds, `expand_all`, octave layout, `RenderTables`, `render_row_rgb`, `advance_chain` |
| `relation/src/header.rs` | `rust/row_binding_join_sp1_candidate/join/src/lib.rs` 55-58, 96-161 | `ZBROWW01` header |
| `relation/src/beacon.rs` | same file, 31-47, 248-283 | quicknet constants and `verify_quicknet_beacon` |
| `relation/src/emission.rs` | same file, 338-350 | streaming render and digest |
| `relation/src/membership.rs` | `rust/row_binding_join_membership_sp1_candidate/membership/src/lib.rs` 23-28, 40-43, 103-265, 267-412 | `ZBOSM001`, domains, context, leaf, node, wrapped root, path walk; generalised to leaf fields from a struct; plus a host-side tree builder with the golden padding rule of `final_relation/chain/session_tree.py` 12-14, 87-89 |
| previous-row leg (in `statement.rs`) | `membership/src/august.rs` 328-367 | same checks, explicit witnesses instead of the CSV prefix |
| `program/Cargo.toml`, `script/build.rs`, `script/Cargo.toml` | `…membership_sp1_candidate/{program/Cargo.toml, script/build.rs, script/Cargo.toml}` | `sp1-zkvm = "=6.4.0"`, `lto = "thin"`, `overflow-checks = true`, the two sp1-patches forks, `--remap-path-prefix` + `--locked` guest build, `groth16`/`cuda` features |
| `program/Cargo.lock`, `script/Cargo.lock` (seeded, then minimally updated) | the proved `program/Cargo.lock`, `script/Cargo.lock` | every `sp1-*` crate at 6.4.0 (21 in the host, 3 in the guest), bls12_381 fork at `9e4e2ae4`, sha2 fork at `0b1945ee` in the guest **[measured, `grep` of the locks]**; without the seed the offline resolver picked sp1 6.6.0 for the sub-crates |
| `script/src/ceremony_core.rs`, `ceremony.rs` | `…/script/src/ceremony.rs` | `.groth16()` request, mode and version asserted, verify, three tamper controls, exact artifacts, manifest |
| `script/src/execute.rs` | `…/script/src/main.rs` | execute-only host with cycle regions and oracle compare |
| unused by design | `join` r32 scorer, pose leg, typed root, `zcash.rs`, `memo.rs`, `verify_august_anchor`, `preprocess_v1_candidate` | dropped per the verdict (no new Zcash transaction, no pose, no r32) |

Uncropped-mean template: `uncropped_halfup_mean` (uncr64 relation lib.rs 160) uses the non-overlapping partition
`ys[i] = i·in/out` and half-up rounding, which is not the pipeline's function; it was read as the loop template only.

## 4. Built and measured on the development machine

| item | value |
|---|---|
| host toolchain | rustc 1.98.0, cargo 1.98.0 (`rust-toolchain` pins 1.98.0) |
| guest toolchain | `succinct` (rustc 1.94.0-dev), target `riscv64im-succinct-zkvm-elf`, sp1-build 6.4.0, offline (`CARGO_NET_OFFLINE=true`) **[measured]** |
| guest ELF | `program/target/elf-compilation/riscv64im-succinct-zkvm-elf/release/zkdiff-guest`, 490,120 bytes, sha256 `4a0c8616f36920d4e154678411c56b549423fdb9069743b09bd63fa0cfc45f3f` **[measured]** |
| vkey | `0x00982b7bd707f5efa9d03bda4585db0b320bb8dbe962a87350a480944878eaab` (`zkdiff-ceremony vkey`, `runs/vkey_20260907.log`) **[measured]** |
| `cargo test --release --offline` | 46 tests, all pass: 21 unit, 13 vector (`tests/vectors.rs`), 12 in the copied b3xof crate **[measured]** |
| execute of the synthetic e2e witness | see `runs/execute_e2e_synthetic_20260907.log`; numbers in section 4.1 |
| batch prepare, August rows 600..711 | `runs/batch_prepare_20260907/BATCH_MANIFEST.json`; section 7 |

### 4.1 Instruction count of the relation legs (stub network)

`zkdiff-execute --witness-dir ../vectors_relation/e2e --raw synthetic:a --expected …/expected_public_zbdiff01.bin`
(`runs/execute_e2e_synthetic_20260907.log`, the development machine, SP1 6.4.0 CPU executor) **[measured]**:

| quantity | value |
|---|---:|
| total instructions | 7,233,062,881 |
| syscalls | 269,904 |
| host wall time | 225.0 s |
| oracle | `native_reexecution+python_oracle`, 752 bytes checked, 0 circuit-derived (the guest's public bytes equal gen_vectors.py's independent computation) |

| cycle region | instructions | note |
|---|---:|---|
| `emission_render_r` | 2,143,613,548 | the proved row's render cost 2,141,120,868 |
| `emission_render_u` | 2,143,615,648 | second pattern |
| `frame_reduce` | 1,974,597,155 | soft-float area means of 6.1 M raw pixels, 323 instructions per pixel; the price of the pipeline-exact path (section 2.1) |
| `raw_blake3_24MB` | 697,810,934 | the proved row: 702,715,828 |
| `hints` | 257,106,344 | two XOF expansions, 24 octave resizes, coordinates |
| `previous_advance_leg` | 4,912,895 | one BLS verification + advance |
| `drand_verify` | 4,904,523 | the proved row: 4,904,590 |
| `noise` | 3,657,237 | BLAKE3 of 86 KB, forward noising |
| `denoiser_correct`, `denoiser_wrong` | 1,280,400, 1,280,396 | the stub; the real network replaces these two lines |
| `ordered_session_membership` | 119,902 | two leaves, two paths |
| `constants`, `public_commitment`, `parse_witness`, `private_input` | 85,997, 42,387, 4,342, 551 | |

So the relation legs cost 7.23 G instructions before the network **[measured]**, against the plan's 5.03 G estimate
for the retained legs plus 0.2 G for the reduction: the difference is the soft-float frame reduction (1.97 G instead of
0.2 G). At the proved fleet's median 182 s per G instruction on one A100-SXM4-40GB that is about 22 minutes of proving
per row for the legs alone **[derived]**, before the network's two passes (30 to 118 G at the r32 rate for width 16,
plan section 6). The reduction's lever, if it matters, is an exact integer emulation of the float32 accumulation (the
per-step rounding depends only on the running sum's exponent), which would replace the soft-float adds; the rounding
rule itself is not negotiable without leaving the pipeline's function.

## 5. Tests and what each one proves (all `[measured]`, `cargo test --release --offline`)

| test | reference | what passes |
|---|---|---|
| `fp::tests::*` | hand values | rounding rules, binary16/bfloat16 edge cases (ties, subnormals, overflow) |
| `float_conversions_match_numpy_and_torch_on_8192_vectors` | `conv/` (numpy `astype(float16)`, torch `.to(bfloat16)`) | 8,192 values, 2,048 of them exact ties: f16 bits, f16->f32, bf16 bits, `cache_quant` |
| `torch_area_bins_match_the_python_reference` | `synthetic/area_bins.json` | every bin of 2300->96, 2660->112 and the eight octave resizes |
| `synthetic_frame_{a,b}_…_reduces_bit_exactly` | torch `F.interpolate` output, numpy int64 sums, `Fraction` rounding | PRNG frame regenerated and sha256-checked; float32 means bit-exact; `C_int` torch path; exact sums, counts and rational `C_int`; mismatch counts equal the manifest's |
| `d2_rows_1328_and_1330_hints_match_the_g1_vectors` | local d2 chain log + G1 manifests | XOF -> octave means bit-exact per channel; `E_int` equals G1's `26f2fedf…` and `7ab0ee86…`; rational `E_int` |
| `d2_row_1328_coordinates_hint_noise_and_ct_match_g1` | G1 manifest hashes | coords `84184184…`, hint `b4e00b6a…`, `C_int` `9baf878a…`, noise `37198a3d…`, `C_t` `4050eb3f…` |
| `membership::tests::frozen_row96_constants_reproduce` | native/src/lib.rs constants | context `f5eba65f…`, leaf `2e4e76aa…`, internal root `1d43309e…`, wrapped root `38a484b8…` |
| `august_tree_builder_reproduces_the_frozen_siblings_and_root` | frozen row-96 siblings, `august_rows.json` | the host-side tree builder from all 712 leaves |
| `august_rows_render_open_and_advance` | August chain log rows 585, 598, 599, 600, 602, 615, 630 | renders equal `emission_live_pixel_blake3_hex`; `E_int` per row; leaves open; advances reproduce `S_{t+1}`; the row-600 byte witnesses parse and open for all five offsets |
| `august_chain_log_walks_end_to_end` | chain log BLAKE3 `754e5716…` | 712 of 712 advances (last one yields `S_N`) |
| `beacon::tests::*`, `august_rows_599_and_600_beacons_verify` | chain-log signatures | real quicknet BLS verification and binding for rows 0, 96, 599, 600, 602; wrong round, value and point rejected |
| `emission::tests::august_row_96_emission_digest_matches_the_chain_log` | chain log | the copied renderer on real data |
| `end_to_end_synthetic_statement_matches_the_python_oracle` | `e2e/expected_public_zbdiff01.bin` | the complete relation on a synthetic 16-row session with real beacons: all 752 public bytes equal an independent Python computation (stub network on both sides) |
| `end_to_end_negative_controls_fail_closed` | | one raw byte, zero offset, legal-but-mismatched offset, signature bit, wrong-row emission digest, wrong `S_u`, wrong `S_{r-1}`, wrong sibling, mirror flag on an in-range direct row, flag byte 2 all rejected with the expected message; absent flag reads as direct; a different noise gives a different valid statement |
| `rule::tests::all_112_august_assignments_follow_the_owner_rule` | the rule spelled out by hand | every row 600..711: base, direct/mirrored, `u`; the ten mirrored rows; the six `-30` rows; the guest's generic check admits exactly the rule's flag and refuses the flipped flag except on the eight policy-only rows (697, 702, 707, 710 flipped to mirrored; 698, 703, 708, 711 flipped to direct), which only the acceptance verifier refuses |
| `statement::tests::offsets_fail_closed`, `public_parse_enforces_the_offset_rule_on_the_public_fields` | | `-30` refused as direct, admitted as mirror exactly for `r + 30 >= n`; `+30` mirrored refused; `u != r + d` refused by the public parser |
| `synthetic_mirror40_session_admits_the_mirrored_minus_30_statement_and_refuses_its_relabellings` | a 40-row session built in Rust (real quicknet beacons of August rows 600..639, v9 advances, every emission rendered, golden padding tree) | row 39 (base +30, 69 outside) with `-30` mirrored EVALUATES (stub network) and parses; the same witness relabelled direct, as `+30` mirrored, with the mirror flag on row 20, and with `-15` mirrored (admissible generically, leaf mismatch) is refused with the named message; the witness is written to `vectors_relation/synthetic_mirror40/` for the complete-guest executor run (FULL_GUEST.md s.4.5) |
| `august_row_684_mirrored_minus_30_passes_the_offset_check_and_needs_only_its_frame` | the prepared row-684 witness | with a substitute frame the relation fails exactly at the membership leg, i.e. after the offset check; the direct and `+30` relabellings are refused before any frame is touched |
| `august_row_600_needs_only_the_raw_frame` | August witnesses | with a synthetic frame in place of `raw_600` the relation fails exactly at the membership leg (the documented pending item) |

Two separate tests remain separate, as the verdict asks: integer reference versus Rust is exact (above); float versus
integer is G1's report, not this crate's.

## 6. Stubbed

`net::StubDenoiser` (kind 0): `eps[c] = clamp16(C_t[c] - (hint[3c] >> 4))`, constants digest
`SHA-256("ARMC-RELATION-STUB-DENOISER-V0")`, spec digest `SHA-256("ARMC-RELATION-STUB-SPEC-V0")`. It is not a network;
it exists so the guest, the host oracle and the tests run end to end. The public byte at offset 10 is 0 for it, so no
stub proof can be read as a network proof.

Integration point: implement `net::Denoiser` for a struct holding the sibling's `armc_int::blob::Constants`
(`kind = 1`, `constants_sha256 = SHA-256(blob bytes)`, `spec_sha256 = SHA-256(canonical spec JSON)`, `predict` calling
its forward on `C_t` (int16 Q12) and the 14-channel hint (int16 Q14), returning eps int16 Q12), add the crate as a path
dependency of `program/` and `script/` (`../../armc-int`, `default-features = false` in the guest), and swap
`StubDenoiser` for it in `program/src/main.rs` and `script/src/witness.rs`. The G1 vectors for d2 rows 1328/1330 then
give the first exact end-to-end check: this crate's `C_t` and hints are byte-identical to G1's inputs (section 5), so the
residual sums must equal `12,775,807,457` (correct) and `15,569,339,266` (wrong +2) for the int16 scheme
(`g1_integer/vectors/vectors_int16_*.json`).

Not implemented, by decision: no in-circuit RNG for the noise (off-circuit provenance, per the verdict); no Zcash, memo,
pose or r32 legs; saturation in forward noising is a hard failure rather than a published counter (G1 saw none in 222
forwards).

## 7. The August proof set and the node-side data

Declared offset rule (7 September 2026), two parts: one proof per held-out August row `r` in
600..711, `base = [-2, +2, -15, +15, +30][(r - 600) mod 5]`, `offset = base` when `0 <= r + base < 712` (direct), else
`offset = -base` with the mirror flag (rows 684, 689, 694, 699, 704, 709 at +30 mirror to -30; 698, 703, 708 at +15 to
-15; 711 at +2 to -2), every outcome published. The rule is one pure function, `relation/src/rule.rs`
(`august_assignment`, `august_table`, `RULE_TEXT`), read by `zkdiff-batch` (assignment), by the acceptance verifier
(`accept.rs`, enforcement on `r`, `u`, `d`, byte 11 of every statement) and by the regression test over all 112 rows.
The guest checks only the generic admissibility (section 1); the exact assignment is policy, enforced at acceptance.

`zkdiff-batch prepare --chain-log ../vectors_relation/august/chain_log.csv --out runs/batch_prepare_20260907`
(`runs/batch_prepare_20260907.log`, `BATCH_MANIFEST.json`, 62.7 s on the development machine) **[measured]**:

| status | rows | meaning |
|---|---:|---|
| `pending_frame` | 102 | every frame-independent leg verified natively for the row: beacons `r` and `r-1` verify and bind, `advance(r-1) == S_r`, both patterns render to the chain log's digests, `leaf_r` (with the chain log's raw digest) and `leaf_u` open to the committed root; the witness items other than `raw_r` and `noise` are written under `row_XXXXXX/witness/`; only the frame is missing |
| `out_of_range_by_rule` | 10 | (historical, first run) `r + offset >= 712`: r = 684, 689, 694, 699, 704, 709 (+30), 698, 703, 708 (+15), 711 (+2). Resolved the same day by the declared rule's mirror clause: these ten rows take `-base` with the mirror flag (FULL_GUEST.md s.6); the G2-D and r5 prepare runs record them as `pending_frame` with `offset_rule: mirrored`, none out of range |
| `failed` | 0 | |

The manifest carries the rule text and constants, the session (id, row count, chain-log BLAKE3, context digest, root),
the guest ELF sha256, the preprocessing spec digest and, per row: offset, wrong row, `leaf_r`, `leaf_u`, the expected
raw digest, the witness directory and the notes. In `execute` and `prove` modes the same manifest gains the residual
sums, the difference and its sign, instruction counts or proof sha256, vkey and timings per row, plus one
`receipt.json` (and `manifest.json` for proofs) per row.

What must come from the Lambda node (`[private corpus path]/august_dev_712/`, read-only pulls, no writes there):

1. **The 112 raw frames** `Recordings/frame_{r:06d}.raw` for `r` in 600..711 (24,472,000 bytes each, 2.74 GB in
   total); each must hash (BLAKE3) to the chain log's `bayer_blake3_hex`, which the driver checks before executing.
   `frame_000600.raw` alone unblocks the first execute.
2. **Nothing else from the node for the binding legs**: the August `chain_log.csv` (BLAKE3 `754e5716…`) is on the development machine
   (proved bundle, copied to `../vectors_relation/august/chain_log.csv`) with every signature; the session tree is
   rebuilt from it and reproduces the frozen root; the per-row witnesses are already written under
   `runs/batch_prepare_20260907/row_XXXXXX/witness/`.
3. **The August noise rule** (section 2.3): the proposal set is generated and hashed; the proposal was adopted as the normative rule (`oracle/final/README_FINAL.md` section 5).
4. **The network**: the `armc-int` adapter and its constants blob (section 6); the batch manifest records
   `denoiser = StubDenoiser` until then.
5. For the per-row float control: the node's `pubproto_raw.npz_*.npz` were
   already pulled by G1 (g1_integer/README.md s.1a).

Held-out status: the model in training excludes rows 600..711 (`--august-train-rows 600`, train_lean.py 261, 310-313);
whether the frozen checkpoint for the proof set was trained under that flag is a training-side fact to record in the
release, not something this crate can check.

## 8. Runbook

the development machine (no GPU, no Go): build, test, execute.

```
export CARGO_NET_OFFLINE=true PATH="$HOME/.sp1/bin:$PATH"
cd source/armc-relation
cargo test --release --offline                                   # 46 tests
cd script && cargo build --release --offline --locked --bin zkdiff-execute --bin zkdiff-ceremony --bin zkdiff-batch
./target/release/zkdiff-ceremony vkey                            # pins ELF sha256 and vkey
./target/release/zkdiff-execute --witness-dir ../../vectors_relation/e2e --raw synthetic:a --expected ../../vectors_relation/e2e/expected_public_zbdiff01.bin
./target/release/zkdiff-batch prepare --chain-log ../../vectors_relation/august/chain_log.csv --out ../runs/batch_prepare_20260907
# with frames and noise present:
./target/release/zkdiff-batch execute --chain-log ../../vectors_relation/august/chain_log.csv --frames-dir /path/to/Recordings --noise-dir ../../vectors_relation/august/noise_proposal --out ../runs/batch_execute
```

Lambda box: bootstrap (apt dependencies, rustup, `sp1up --version v6.4.0`), copy this tree with `vectors_relation/august/` and the frames,
`cargo build --release --locked --features cuda --bin zkdiff-ceremony --bin zkdiff-batch` (the batch was built with `--features cuda`
alone and needed no Go toolchain, `node_prep/r5/build_record_20260907T215855Z.txt`; an earlier draft of this paragraph named
`groth16,cuda` and Go >= 1.24), check `zkdiff-ceremony vkey` equals the development machine's pin, then
`setsid nohup ./target/release/zkdiff-batch prove --prover cuda --chain-log … --frames-dir … --noise-dir … --out … &`
with the `nvidia-smi` sidecar, detached from the ssh session. One receipt and manifest per
row, `BATCH_MANIFEST.json` at the end; `zkdiff-ceremony verify --proof … --expect …` cold-verifies any artifact (`--expect` is required since the Astra r5 revision;
`zkdiff-verify` is the standalone form, FULL_GUEST.md section 2.3; the `--elf` form of the first draft was corrected in the published copy).

## 9. Risks and open points

| item | state |
|---|---|
| torch version on the node when the cache was made | the cache for d2 row 1328 equals a recompute on the development machine (torch 2.11.0) bit for bit **[measured]**; the measured CPU area-kernel output matched the reference fixture, but the node's torch version is unrecorded **[confirm]** |
| soft-float cost in the guest | measured in section 4.1; if the frame reduction dominates, the 256-entry table and the bin loop are the levers, never the rounding rule |
| beacon cost | two BLS verifications per proof (the proved row paid 4.9 M instructions each with the sp1 forks) |
| `sp1-*` versions | pinned to 6.4.0 by the seeded locks; the first offline resolution had drifted to 6.6.0 sub-crates and was discarded |
| Groth16 wrap not rehearsed | the development machine has no Go; `ceremony_core.rs` is the proved code with the witness swapped; first run is on the box |
| the batch's out-of-range rows | superseded: the declared rule's mirror clause assigns `-base` with the mirror flag to the ten rows; after Astra r5 the guest admits `-30` exactly there (`check_offset_rule`), the 112 assignments are regression-tested, and the acceptance verifier enforces the exact assignment |

## 10. Audit note

Checked against source or output on the development machine: every pipeline line cited in section 2 (files under `../../src/`), the G1
manifests and cache files, the proved tree paths of section 3 (copied bytes hashed), the d2 chain log (two identical
copies, sha256 `d0f97ac9…`), the August chain log (BLAKE3 equals the frozen constant), the frozen row-96 constants, the
`tile_cpu.py` renderer (Python side of `gen_vectors.py`), torch's `area` kernel behaviour (empirical, section 2.1), the
lockfile versions. Not checked: the node's torch version; anything about the raw frames (none on the development machine); the Groth16
path end to end; the network (stubbed). Nothing was written outside `g2_guest/armc-relation/` and
`g2_guest/vectors_relation/`; the proved tree and `armc-int/` were read only.

## Log

- 1.0 (2026-09-07, BOSUN) — relation crate, vectors, guest and host skeletons, batch driver; tests green; execute
  and batch-prepare runs recorded.
- 1.1 (2026-09-07, BOSUN, G2-D) — banner and layout rows amended for the offset-rule flag (byte 11, witness
  item 10), the constants-blob input and the published clip count (bytes 749..752); network integration recorded in
  FULL_GUEST.md.
- 1.2 (2026-09-07, BOSUN, Astra r5 finding 1) — direct and mirrored offsets validated together
  (`check_offset_rule`; `-30` admitted only as a mirror and only when `r + 30` leaves the session; `+30` never a
  mirror; the public parser applies the same check and `u = r + d`); the rule as a pure function (`rule.rs`) shared by
  the batch driver, the acceptance verifier and the 112-row regression test; synthetic 40-row mirror session and the
  row-684 prepared-witness test added; sections 1, 1.1, 1.2, 1.3, 5, 7 and 9 updated; the eight policy-only rows
  named. Pins moved to FULL_GUEST.md v1.2.
- 1.3 (2026-09-09, BOSUN) — authorship line, 9 September 2026.
