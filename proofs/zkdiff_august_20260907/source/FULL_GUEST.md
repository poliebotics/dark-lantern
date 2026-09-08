---
version: 1.2
date: 2026-09-07
status: complete guest built reproducibly on the development machine AND on the node (different absolute paths, byte-identical ELF, one vkey), never proved; Astra r5 findings 1, 3, 4 (wording), 5, 6, 9, 10, 11, 12 applied; parity PASS on d2 1328 (both constant sets), on the eight FINAL layer sets, on the 42 FINAL boundary fixtures, on August rows 600-603 in the complete guest with the acceptance verifier, and on a synthetic mirrored -30 statement through the complete guest; row 684's complete run waits for its frame on the node [pending node]
author: BOSUN
---

# G2-D: the complete zkdiff guest (relation legs + armc-int network), parity, instruction count, node batch procedure

> **Status on 8 September 2026 (published copy).** This note was frozen on 7 September 2026, before the node ran, and its status
> line describes that evening ("never proved", "[pending node]"). Every `[pending node]` item below has since been closed: the node
> executed row 684 through the complete guest with its frame (`RESULTS.md` section 4; `node_prep/r5/execute_684_receipt.json`), all
> 112 rows were proved and accepted (`RESULTS.md` section 6; `receipts/`), and the proof-level controls ran on a real proof
> (`receipts/proof_controls.json`). `NODE_PROVE_READY.md`, named as a companion below, is held (`REDACTION.md`); the toolchain
> facts it carried are in `VERIFY.md` section 2 and `PINS.json`. Nothing else in the copy was changed for this banner.

Scope: the `armc-int` integer network (G2-A) wired into the relation guest (G2-B) through a `Denoiser` adapter, the two
declared rules of 7 September (the offset rule and the noise rule) encoded in the witness, the public layout and the batch manifest, the Astra round-4
revisions of the kernel crate (`astra_r4/ASTRA_VERDICT_g2a_r4.md`), the Astra round-5 revisions of the guest, hosts,
batch driver and runbook (`astra_r5/ASTRA_VERDICT_fullguest_r5.md`, section 11 below), the complete SP1 6.4.0 guest
built by a fail-closed reproducible driver on two machines and executed (never proved) on the development machine, and the procedure for
the Lambda node. Tags: **[measured]** read from a test, log or file on the development machine or in the node's build record; **[derived]**
arithmetic on measured numbers; **[extrapolation]** a rate applied to a count; **[confirm]** not verified here;
**[pending node]** needs data that exists only on the node. Nothing was proved, published or pushed. The node was
touched exactly twice: an rsync of this tree into a NEW directory `g2_guest_r5/` beside the pilot's tree, and the
CPU-only reproducible build there (section 3.2).

Companion files: `armc-relation/RELATION.md` v1.2 (the legs, the offset rule), `CYCLES.md` (the pre-r4 network bench),
`NODE_PROVE_READY.md` (the node), `armc-relation/adapter/` (the adapter crate), `armc-relation/build_reproducible.sh`
(the build driver), `armc-relation/script/src/accept.rs` (the acceptance verifier, shared by `zkdiff-verify`,
`zkdiff-ceremony verify` and `zkdiff-batch`), `expected_identities_august.json` (the frozen identities every proof is
accepted against), `tools/` (exporters, oracle, identity freezer, strict merger, checksum tool), `armc-relation/runs/`
(every log, build record and receipt named below), `noise_august/` (the normative noise), `blobs/final_int16/` (the
blob), `fixtures_final/` (the staged G1 boundary fixtures), `vectors_relation/synthetic_mirror40/` (the synthetic
mirrored -30 witness), `node_prep/G2D_NODE_RUNBOOK.sh` (the node runbook).

## 1. Result in one table

| item | value |
|---|---|
| guest ELF (r5, FINAL pin) | `armc-relation/program/target/elf-compilation/riscv64im-succinct-zkvm-elf/release/zkdiff-guest`, **396,200 bytes**, sha256 **`51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc`**, symbol table stripped, no host path inside; byte-identical from three independent builds at two absolute paths on two machines (section 3) **[measured]** |
| SP1 verifying key | **`0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027`**, identical on the development machine, in the the development machine path probe and on the node **[measured]** |
| circuit | `SP1_CIRCUIT_VERSION` `v6.1.0`; circuit verifier key sha256 `4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696` (492 bytes; the `sp1-verifier` 6.4.0 embedded key equals `~/.sp1/circuits/groth16/v6.1.0/groth16_vk.bin` on the development machine and on the node) **[measured]** |
| expected identities | `expected_identities_august.json`, sha256 `6822cdcefa9a8833460287a3bb619fa63d0f3755d46dccc7db5418b261d6d613`: vkey, ELF, circuit key, constants / spec / preprocessing digests, session, rule, and per row the normative noise BLAKE3, chain-log raw and emission digests, drand rounds, leaves and G1's expected int16 residuals (`tools/make_expected_identities.py`, section 2.5) **[measured]** |
| constants blob the guest was executed with | G1 FINAL int16 (`g1_integer/final/vectors`, checkpoint `c6955192067c8df1f46960f4803b32eac1c037b84a0f40de3b265b739d85fab8`, seed 20260908, 24k steps), blob format v2 with the clipping masks: `blobs/final_int16/constants_int16.blob`, **3,476,866 bytes**, sha256 **`73310ddab603cab5588d05e9ac4deb7e56466a6fae4bbf89244c32f2bd1a8b92`** **[measured]** |
| network spec digest (public offset 596) | `02872ec23ab5a503fa1a6b450d90511f83a59afb36457cacb161e1277b22073b` (`adapter/src/lib.rs` `ARMC_INT_SPEC_CANONICAL_JSON`, id `ARMC_INT_SPEC_V2`, unchanged) **[measured]** |
| preprocessing spec digest (offset 628) | `025de070985434fefaea547745e18983ffd21c50ec66e3126bcfffc8af58f4a5` (unchanged) |
| the mirrored -30 offset (Astra r5 finding 1) | direct and mirrored offsets validated together in the guest (`statement::check_offset_rule`): `-30` admitted only under the mirror flag and only when `r + 30` leaves the session; all 112 assignments regression-tested; a mirrored -30 statement EXECUTES through the complete guest on a synthetic 40-row session with a real frame (section 4.5); the real row 684 passes the offset check and every leg up to the frame hash on the development machine, complete run **[pending node]** |
| parity, d2 row 1328 (relation-derived `C_t` and hints -> adapter) | step-12000 blob `4fcd5dc3…`: **12,775,807,457 / 15,569,339,266 PASS**; FINAL blob `73310dda…`: **8,764,459,045 / 22,311,372,969 PASS**, 0 clip events (`adapter/tests/parity.rs`) **[measured]** |
| parity, FINAL vectors layer by layer | d2 1328 and August 650, correct and wrong +2, int16 and int8: 188/188 layer outputs, effective scales and residual sums equal in all eight sets, clip counts equal the oracle's (0) (`armc-int/tests/parity.rs`) **[measured]** |
| parity, the 42 FINAL boundary fixtures | all pass, expected values and counters (`armc-int/tests/fixtures.rs`, section 4.3) **[measured]** |
| parity, August rows 600-603 in the complete guest | R_correct / R_wrong of the executed r5 guest = native re-execution = Python oracle = G1's `expected_residual_sum_int` (acceptance check `oracle.*`) in all four rows; sign positive, clip events 0; every receipt `accepted: true` under the frozen identities (section 4.4) **[measured]** |
| total instructions, one August row | r5 ELF: **14,400,363,198** (row 600); rows 601-603 **14,400,345,341**, **14,400,313,902**, **14,400,340,066**; r4 ELF (Astra r5 finding 12): 14,400,363,229; 14,400,345,372; 14,400,313,933; 14,400,340,097 **[measured]** |
| host execute, one row on the development machine | about 3 to 4 min wall with two other executors running, peak RSS **15.97 GB (14.87 GiB)** (`host_peak_rss_kib` **15,592,988**, the client process only); r4 run: 15.93 GB / 14.84 GiB (15,556,208 KiB) **[measured]** |
| expected proving per row on one A100-40GB | 14.4 G instructions x 182 to 230 s per G instruction (the proved fleet's historical rate) = **43.7 to 55.2 min per row including the Groth16 wrap**; 112 rows on 8 GPUs, 14 each = **10.2 to 12.9 h wall** **[extrapolation, unmeasured]**; the pilot proof measures it (section 7.3) |
| tests | `armc-relation` workspace **59** pass (relation 25 unit + 15 vectors, b3xof 5 unit + 7 crosscheck, adapter 2 unit + 5 parity); `armc-int` **25** pass (12 parity + 13 fixtures); `script` 1 (the circuit-key pin); the r4 count was 54, not 59 as v1.1 said (Astra r5 finding 12) **[measured]** |
| negative controls | 23 witness-level controls on the final network natively, every one behaved as expected, relation and policy rejections distinguished (`runs/controls_r5_20260907/CONTROLS.json`); 12 proof-level rejection controls exercised on a real SP1 6.4.0 Groth16 artifact of another program (section 4.6) **[measured]** |

## 2. What was integrated

### 2.1 The adapter crate `armc-relation/adapter/` (`zkdiff-armc-adapter`)

`ArmcIntDenoiser::from_blob(bytes)` hashes the blob (SHA-256), parses it with `armc_int::blob::Constants::parse`
(static bound checks of every layer, representability of every fractional-bit field, mask consistency) and refuses it
unless: the grid is 96 x 112; the weights are int16 (`qmax = 32767`); `F_CT = 12`, `F_HINT = 14`, `F_EPS = 12`;
`SA = 63540`, `SO = 16053`, noise shift 16 (the relation's compiled noising constants); and the blob's two coordinate
planes equal `hint::coord_int()` byte for byte. `Denoiser::predict(ct, hint)` splits the 14-channel hint into the 12
XOF channels and the 2 coordinate channels, requires the coordinate channels to equal the blob's, feeds the
already-noised frame straight into `armc_int::model::Net::forward` (never through the crate's own noising path) and
returns `(eps, clip_events)`, the network's count of clamps outside the int16 domain and of indexed hits on clipped
lookup-table entries. `kind() = 1`, `constants_sha256() = SHA-256(blob)`, `spec_sha256() = SHA-256` of the canonical
spec JSON in `lib.rs`, which states the executed arithmetic (rounding rules, domain and clip policy, kernel formulas,
scale rule, attention multiplier rule, representability rule, blob format).

The same-noise-both-arms property is enforced where it always was, in `statement::evaluate`: one `C_t`, two `predict`
calls, both residual sums against the one noise witness whose BLAKE3 is public; the adapter holds no state between
the two calls.

### 2.2 Witness and public layout (relation crate, `statement.rs`)

Declared rule (a), the mirrored offsets, as amended after Astra r5: witness item 10 is a one-byte **offset-rule flag**
(`OFFSET_RULE_DIRECT = 0`, `OFFSET_RULE_MIRRORED = 1`; an empty item reads as direct). Public byte 11 carries the flag.
`check_offset_rule(r, row_count, d, flag)` validates the offset and the flag TOGETHER: under the direct flag `d` must
be a nonzero value of `{-2, +2, -15, +15, +30}`; under the mirror flag `-d` must lie in that set and the rule's direct
wrong row `r - d` must lie OUTSIDE `[0, row_count)`; in both cases `u = r + d` must lie inside. So `-30` is admitted
exactly where the declared offset rule needs it (rows 684, 689, 694, 699, 704, 709 of the August set, whose `r + 30` reaches
714..739), a mirror flag on a row whose direct wrong row exists is refused, `+30` is never a mirror, and `-30` is never
direct. The shipped r4 guest's `parse_offset` had refused `-30` before reading the flag (Astra r5 finding 1); it is
gone. `PublicOutput::parse` applies the same check to the public fields and requires `u = r + d`, so every parser of
the 752 bytes, the acceptance verifier included, refuses an inconsistent statement. The exact modulo assignment
anchored at row 600 is one pure function, `relation/src/rule.rs` (`august_assignment`), shared by the batch driver,
the acceptance verifier and the 112-row regression test; the guest does not enforce it, because the guest does not
know which batch it is in (RELATION.md section 1). Eight rows of the August set admit a coherent alternative flag
generically and are refused by the acceptance verifier alone: 697, 702, 707 and 710 flipped to mirrored, 698, 703,
708 and 711 flipped to direct (`rule.rs` test). Regression: every one of the 112 assignments against the rule written
out by hand, the ten mirrored rows, the six `-30` rows (`rule::tests`), the boundary cases of `check_offset_rule`
(`statement::tests`), a synthetic 40-row session whose row 39 carries `-30` mirrored and evaluates while each
relabelling is refused with the named message, and the real row-684 witness (`relation/tests/vectors.rs`, section 4.5).

The constants blob is an eleventh private input of the guest, read after the ten witness items; its SHA-256 is public
offset 564 (`constants_sha256`), so a verifier compares that field with the published blob's hash; the ELF itself is
checkpoint-independent.

Saturation (Astra r4 items 1, 2, 6; the G1 FINAL contract, `README_FINAL.md` section 3): public bytes 749..752,
formerly reserved zero, carry the **clip flag** (749, 1 iff nonzero) and the **clip-event count** (750..752, u16 LE,
saturating at 65535): the noising leg's clamps (it no longer refuses a saturating witness), plus both network passes'
clamps and masked-table hits. The evaluation proceeds and publishes the count. Wording after Astra r5 finding 4: a
nonzero count marks a statement **outside the zero-clipping regime covered by the reported validation**; the proof
remains valid for the specified saturating computation; every nonzero count is published; **65535 means "at least
65535"**; count zero covers the counted runtime sites (noising clamp, network clamps, masked-table hits), not the
off-circuit input conversion. The oracle's conversion-time input clips (`input:C`, `input:noise`, `input:E`,
`input:coord`) happen before the integers exist and are recorded in the artifact manifests (all zero); they cannot
be observed in the guest and are stated as such.

Declared rule (b), the noise: the noise tensor remains a witness whose BLAKE3 is public (offset 660); the guest does not
generate the noise tensor. The normative bytes are G1's `noise_int` from `g1_integer/final/august_inputs/row_NNNNNN.npz` (README_FINAL
s.5), exported by `tools/export_august_inputs.py` to `noise_august/noise_{r:06d}.i16` with every sha256 asserted
against G1's manifest (112/112) **[measured]**; byte-identical to the earlier proposal set in all 112 rows. After
Astra r5 finding 3 the mapping row -> normative BLAKE3 is ENFORCED, not merely recorded: the frozen table
(`expected_identities_august.json`, built from G1's `noise_map` and checked file by file) is what the acceptance
verifier compares the public digest with, and the batch driver refuses to execute or prove a row whose noise file's
BLAKE3 differs from the table entry.

### 2.3 Guest and hosts

`program/src/main.rs`: ten `read_vec` items, then the blob; region `constants_blob` around hash + parse + checks;
`evaluate` with the adapter; `commit_slice` of the 752 bytes; prints `denoiser_kind=1`.

`script/`: `witness.rs` builds the stdin as ten items + blob and checks the guest's bytes against a native
re-execution with the same adapter, then (when `--expected` names gen_vectors.py's stub-network bytes) compares the 651
binding bytes and skips the 101 network-determined ones (byte 10, 564..628, 716..752). Four binaries:

| binary | role |
|---|---|
| `zkdiff-execute` | execute-only host: instruction count, cycle regions, native re-execution check |
| `zkdiff-ceremony` | `prove` (one witness, `--expect` runs the acceptance verifier after the SDK verify and the tamper controls), `verify` (REQUIRES `--expect`; derives the key only from the pinned ELF, refuses any other, then SDK verify + three tamper controls + acceptance), `export`, `vkey` |
| `zkdiff-batch` | `prepare | execute | prove | controls` over the August rows (section 6); `prove` REQUIRES `--expect` |
| `zkdiff-verify` (new, Astra r5 finding 3) | the cold acceptance verifier: proof bytes, public bytes, the PINNED program vkey and the embedded circuit verifier key; no SP1 setup, no ELF needed; `--controls` runs the proof-level negative controls; `--identity` prints the circuit and ELF identities for the build record |

`zkdiff-ceremony prove` and `zkdiff-batch prove` take `--blob PATH`, `--device N` (mapped to
`ProverClient::builder().cuda().with_device_id(N)`, `sp1-sdk-6.4.0/src/blocking/cuda/builder.rs:58`) and `--expect`.
In `prove` mode the CUDA client and its proving key are created once per process, and the derived vkey must equal the
expected one before any row is proved. The requested `--cycle-limit` (default 200 G) is enforced by the CPU executor
and the CPU prover; the pinned `sp1-cuda` 6.4.0 client does not forward it to the GPU server (Astra r5 finding 8), so
under `--prover cuda` it is recorded as requested metadata (`cycle_limit_requested`, `cycle_limit_note`), and the
execution count is established beforehand by `execute`.

### 2.4 The kernel crate after Astra r4 (`armc-int`)

| item | change |
|---|---|
| 1 saturation | admitted domain `[-32768, 32767]`; `clamp16` counts every element outside it (the oracle's `kernels.clamp16`); the noising counterexample `C = noise = -32767 -> -39795 -> -32768`, one event, is a test and a fixture; `count_out_of_domain` removed (every int16 is in domain) |
| 2 LUT clipping | blob format v2 carries a 65536-bit mask per table; `lut_apply` counts every indexed hit on a masked entry; the parser refuses a mask bit on a non-endpoint entry; input 32767 on silu 11->12 counts one (test) |
| 3 transport | `tools/export_oracle.py` reads both artifacts (FINAL filenames with session/row, `scale_map`, native int8 weights exported as `i8`, the float32 noise record as `f32`, attention entries without `f_in`) and exports the artifact's `LUTMASK:` arrays after checking them against a regeneration with the oracle's `make_act_lut_with_mask` and against the manifest's `mask_sha256_uint8`; the loader accepts `ftab` or `scale_map`, `i8` arrays and the masks; the parity suite pins the FINAL artifact (section 4.2) |
| 4 binding | the blob (weights, multipliers, folded biases, GroupNorm parameters, tables and masks, exp table, coordinates, scale table) is hashed in the guest and published; every fractional-bit field must lie in 0..=15 at parse (`MAX_FRACTIONAL_BITS`) and every left shift in `rshift_round` is checked to round-trip (`rshift_round(32767, -62)` now refuses instead of going negative, tested); the adapter consumes the noised frame directly, checks the coordinates and returns the clip count for publication; row identities and offset with the mirrored flag are public |
| 5 build | `armc-relation/.cargo/config.toml` (`[net] offline = true`, inherited by sp1-build's `cargo metadata` and the guest build), `build_reproducible.sh` (section 3) |
| 6 CYCLES.md | v3 gas, execute time, wall and RSS corrected (they had been v2's), 235-instruction steady path, the "0.5 per MAC" remark removed, KiB/GB stated |
| 7 `get_unchecked` | not taken |
| 8 fixtures | the 42 G1 FINAL differential boundary fixtures staged by `tools/export_fixtures.py` and run as `armc-int/tests/fixtures.rs` (section 4.3); the attention multiplier of the width-12 specification (`mult`, `r_shift = 2f + 16 - 10`) added to the kernel, blob and model so that fixture runs too |
| r5 wording | `kernels.rs` and `adapter/src/lib.rs` now say "outside the zero-clipping regime covered by the reported validation" (Astra r5 finding 4); comments only, the arithmetic is unchanged |

### 2.5 The acceptance verifier (`script/src/accept.rs`; Astra r5 finding 3)

Beyond "the Groth16 proof verifies", a statement is accepted only if it carries the EXPECTED identities. The expected
identities are frozen once per build in `expected_identities_august.json` by `tools/make_expected_identities.py`
from named sources, each hashed into the file: the asserting build record (vkey, ELF, circuit version, embedded
circuit key), G1's `august_inputs/manifest.json` (`noise_map`, `expected_residual_sum_int`, the rule), the August
chain log (BLAKE3 `754e5716…`; raw digest, emission digests and drand rounds per row), the prepare manifest (leaf
hashes, session), the blob (constants digest), the compiled spec digests and the session constants of `session.rs`.
The verifier never derives a key from whichever ELF it is handed. Checks, in order, each recorded PASS / FAIL / SKIP
with a detail string, any FAIL an error:

1. `circuit.groth16_vk_sha256`: the embedded `sp1_verifier::GROTH16_VK_BYTES` hash equals the pin;
2. `groth16.verify`: `sp1_verifier::Groth16Verifier::verify(proof_bytes, public, pinned_vkey, GROTH16_VK_BYTES)`
   (checks the circuit-key prefix, the verifier's `VK_ROOT_BYTES`, exit code 0, the pairing);
3. `layout.*`: 752 bytes; `PublicOutput::parse` (magic, ABI, protocol, length, zero-padded session id, timestep 150,
   SA 63540, SO 16053, shift 16, F_CT 12, F_HINT 14, F_EPS 12, `D = R_wrong - R_correct`, denominator
   721,554,505,728, sign byte, clip flag and count consistent, offset rule admissible, `u = r + d`);
4. `program.*`: kind 1; constants, network-spec and preprocessing digests;
5. `session.*`: id, row count 712, tree depth 10, `S_0`, `S_N`, authority manifest, chain-log BLAKE3, context digest,
   ordered-session root;
6. `rule.*`: `600 <= r <= 711`; `(d, flag, u)` equal `rule::august_assignment(r)` exactly;
7. `row.*`: the normative noise BLAKE3 of row `r` (mandatory), the chain log's `raw_blake3`, both emission digests,
   both drand rounds, `leaf_r`, `leaf_u`, and the table's own offset / flag / wrong row;
8. `oracle.*`: `R_correct` and `R_wrong` equal G1's int16 expected residual sums for the row and its rule offset;
9. `outcome.class`: positive / zero / negative from the signed `D`, recorded, never filtered.

`zkdiff-verify --controls` adds the proof-level negative controls (section 4.6). The Groth16 layer of the verifier
was exercised on the development machine against a real SP1 6.4.0 Groth16 artifact of another program (the 2 September row-96 proof,
vkey `0x0092cba2…`): verified, and every one of the 12 relation-level mutations rejected
(`logs/verify_groth16_only_row096_final_20260907.json`) **[measured]**. A ZBDIFF proof does not exist yet, so the
acceptance layers 3-9 are exercised on the executed public bytes (`accept_public`) in every receipt of section 4.4 and
on the mutated statements of the witness-level controls.

## 3. Build, pins, reproducibility

### 3.1 Toolchain, driver, locks

| item | value |
|---|---|
| host toolchain | rustc 1.98.0 / cargo 1.98.0 (`rust-toolchain` pins 1.98.0), `CARGO_NET_OFFLINE=true` plus the inherited `.cargo/config.toml`, nothing downloaded, `LC_ALL=C` **[measured]** |
| guest toolchain | `succinct` rustc 1.94.0-dev (LLVM 21.1.8), target `riscv64im-succinct-zkvm-elf`; `cargo-prove sp1 (f66b4bf 2026-08-12)` sha256 `d8835f80b386d5025420d6b09e73ad825b822ac143e8ed09312b2e08018ff106`; succinct toolchain tarball sha256 `12c94435d41bfe4e20131bbcce40b35abd32270ad792befc653af4e3fabc192f` (identical on the node); sp1-build 6.4.0, `--locked`, `--remap-path-prefix` (cargo home -> `/cargo`, the `g2_guest` root -> `/g2`), **`-Cstrip=symbols`** (below) **[measured, `runs/build_record_*.txt`]** |
| driver (Astra r5 finding 5) | `armc-relation/build_reproducible.sh`: fail-closed, cargo's exit status preserved (no `|| true`), the complete cargo output kept in `runs/build_log_<stamp>.txt`, lockfiles compared before and after, exactly one guest ELF and all four host binaries required to be FRESH (mtime after the run start), ELF size / sha256 / vkey / embedded circuit key asserted, no host path in the ELF; records the exact command, features and environment, host and succinct compiler identities, cargo-prove and toolchain tarball hashes, `sp1-gpu-server` and `~/.sp1/circuits/groth16/*/` identities when present, the four host binary hashes with their maximum GLIBC symbol version, and the frozen source-digest list (`LC_ALL=C sort`, so the development machine and the node agree on its digest) **[measured]** |
| locks | `program/Cargo.lock` unchanged since G2-D (`eb391600…`); `script/Cargo.lock` gained exactly one dependency edge, `sp1-verifier` (already in the graph as sp1-sdk's dependency; `logs/script_Cargo.lock.before_r5` against the current lock differs by that one line); every `sp1-*` crate still 6.4.0; bls12_381 fork `9e4e2ae4`, sha2 fork `0b1945ee` in the guest; unchanged across every driver run **[measured]** |
| source digests | final list `runs/SOURCE_DIGESTS_20260907T214737Z.txt` (the development machine, after the host-only counter fix of section 6), list sha256 `235dd832f342c3cc1a8d5980a9c2b3121ca1762aa5327d5fac47ce53ddee81bd`; the list of the asserting build that froze the identities, `…T214246Z.txt`, sha256 `d86b75adcf6c50ef28f51531ccb0235ee2ac9ed0181cc2c40719f6c16cdc6735`, equals the node's (`g2_guest_r5/armc-relation/runs/SOURCE_DIGESTS_20260907T214346Z.txt`) **[measured]**. Astra r5 finding 5 cited the r4 list `T201642Z` (`224f8bc449ecd7874800ed2b53dfb7ba141e6c382d59edcb716ac8dabaaa771c`, 51 entries); the r5 lists succeed it (the driver and `rule.rs`, `accept.rs`, `verify.rs` are new entries; the driver's own hash changes with its pins) |
| host binaries (the development machine, GLIBC_2.39) | `zkdiff-execute` `66b46573b81e2fea87e5e8ffc5adf8923e1a7dc6adc35cc17665bd580f8f3d20`, `zkdiff-ceremony` `2d70f5aab6f58f6faaf44ebf17a87adf727a01cfde5c4f5a85f56782e5b6a5fe`, `zkdiff-batch` `919f49bbedaf6f0ff15e7bf06c268030d4eee0bbc20239442b3c8028a1356df7`, `zkdiff-verify` `ef69af4c4ea82d10f94bdae241294593dc700ae01884c196205d877acfe6d623` (record `T214737Z`); they will not run on the node (glibc 2.35), which rebuilds them with the same driver (`CUDA=1`) **[measured]** |
| earlier pins, for the record | stub ELF `4a0c8616…3f3f` (490,120 B, vkey `0x00982b7b…aab`); pre-r4 complete ELF `395d376e…3164` (650,864 B, vkey `0x000183bb…277d`); **r4 ELF `0f1fd5249d3e1e8c38b63ae96d6c6dbb9aa58957650be7170ea85ba7b265db9e` (654,200 B, vkey `0x0009823f93cda8d383aef36fb97d4537bce515f339383343e15044c2bff38482`), SUPERSEDED: its `parse_offset` refused the mirrored -30 (Astra r5 finding 1); the timing pilot on the node runs on it and is labelled so**; interim r5 ELF `d36a30f21fdc429a50af1b75405d40764da464b86c4be5b52053b4876f30d459` (654,752 B, vkey `0x00cb883e2e7e1473a6b2b74e3ce84cbc47583f238dc1ed12ab591609712e62b6`, symbols present), superseded the same night by the stripped build below after the node reproduced its vkey but not its file hash |

### 3.2 Two machines, two absolute paths, one ELF

The node's first r5 build (`g2_guest_r5/node_build_r5_attempt1_unstripped_FAILED_pin.log`, driver record
`T213345Z`-class, kept) reproduced every identity of the interim ELF except the file hash: same sources (source list
`99b440…` on both), same toolchain, same size 654,752, **same vkey `0x00cb883e…`**, ELF sha256 `ed08fa78…` on the node
against `d36a30f2…` on the development machine, zero host paths on both. Cause, established on the development machine: cargo hashes a path dependency that
lies OUTSIDE the guest's workspace root (`program/` is its own root; `relation`, `adapter`, `b3xof` and `armc-int` lie
outside it) by its ABSOLUTE path into `-C metadata`, so the mangled symbol names in `.symtab` / `.strtab` (5,528
symbols, 258 KB) depend on where the tree sits. The r4 cross-machine match had only ever been tested at identical
absolute paths (the node mirrored the development machine's `…/g2_guest`). The hash digits have a fixed length, so the section sizes and
every loaded byte were identical and the vkey agreed. Fix: `-Cstrip=symbols` in `script/build.rs` (the symbol table
is never loaded; `sp1-zkvm` 6.4.0 defines no `__SUCCINCT_TRAP_CONTEXT` symbol, the one symbol SP1's ELF decoder
looks for, so no zkVM semantics change; only the profiler's function attribution under `TRACE_FILE` loses names). The
vkey moved with the strip because the first `PT_LOAD` segment maps the ELF header, whose `e_shoff` / `e_shnum` enter
the memory image. Evidence, all **[measured]**:

| build | path | ELF sha256 | bytes | vkey | record |
|---|---|---|---|---|---|
| the development machine, pin mode | `source` | `51b7bc35…75cc` | 396,200 | `0x00f01894…a027` | `runs/build_record_20260907T213834Z.txt` |
| the development machine, probe copy of the sources at ANOTHER absolute path | `[alternate build root]/g2_guest_r5` | `51b7bc35…75cc` | 396,200 | `0x00f01894…a027` | `logs/probe_build_other_absolute_path_20260907.log` (copied from the tmpfs probe; quoted in the Log) |
| the development machine, asserting | `…/g2_guest` | `51b7bc35…75cc` | 396,200 | `0x00f01894…a027` | `runs/build_record_20260907T214246Z.txt` (the record the identities were frozen from), `…T214737Z.txt` (after the host-only counter fix) |
| node `prover-node`, asserting, `CUDA=1` | `source` | `51b7bc35…75cc` | 396,200 | `0x00f01894…a027` | `g2_guest_r5/armc-relation/runs/build_record_20260907T214346Z.txt`, `BUILD_REPRODUCED_OK`, cargo exit 0, build wall 19.4 s (warm target from the failed first attempt), host binaries `5b634e5e…` / `5c225f4a…` / `098ad91c…` / `a65bc03a…` (GLIBC_2.34), source list `d86b75ad…` |

## 4. Parity

### 4.1 d2 row 1328 (the G1 acceptance fixture) through the adapter

The relation crate reproduces G1's inputs for d2 row 1328 from the local d2 chain log and the node's float16 cache
(`vectors_relation/d2`, every file sha256-pinned to G1's manifests by `relation/tests/vectors.rs`): `C_int`
`9baf878a…`, noise `37198a3d…`, `C_t` `4050eb3f…`, `E_int` of rows 1328 (`26f2fedf…`) and 1330 (`7ab0ee86…`). The
adapter test `d2_row_1328_with_the_step12000_blob_reproduces_g1s_residual_sums` runs `forward_noise`, `hint14` and
`predict` twice on those bytes with the step-12000 blob and gets **12,775,807,457** and **15,569,339,266**
exactly; `…with_the_final_blob…` gets **8,764,459,045** and **22,311,372,969** with the FINAL blob, the numbers of
`g1_integer/final/README_FINAL.md` section 6, with zero clip events **[measured]**.

The d2 row cannot go through the *complete* guest: the development machine has no raw frame for any d2 row (only the cache) and the d2
chain log carries no drand signatures, so the frame and beacon legs have nothing to consume. The August rows and the
synthetic mirror session below exercise the complete guest end to end.

### 4.2 armc-int against the FINAL artifact

`tools/export_oracle.py` exports `g1_integer/final/vectors/*.npz` into `oracle_final/` (eight sets, 482 arrays each,
465 hashes checked per set, masks regenerated and checked against the artifact's `LUTMASK:` arrays and hashes) and the
superseded artifact into `oracle/` (four sets) **[measured]**. `cargo test --release --offline` in `armc-int/`, 25
tests, all pass (`logs/test_armc_int_r5.log`) **[measured]**:

| test | what passes |
|---|---|
| `parity_chained_all_sets`, `kernels_isolated_all_sets` | all eight FINAL sets: 188/188 layer outputs (values, shapes and effective `f`), residual sums, clip counts equal the oracle's (0) |
| `final_artifact_pins` | checkpoint `c6955192…`; the eight residual sums of README_FINAL s.6; the 15 inherited-scale names; the effective histogram `{7:1, 8:1, 9:22, 10:26, 11:89, 12:38, 13:6, 14:5}` with `ups.3.1.conv1` at f = 7; conv accumulator maxima **353,174,814,720** (int16) / **1,368,850,432** (int8) recomputed from the blob; requantisation maxima **3,812,976,885,203,206,144** / **22,661,745,809,484,953** recomputed; GroupNorm n 32256, N 60 bits, X^2 99 bits, affine 50 bits, SSE bound and noising bound from the manifest; shift ranges [38, 43] / [30, 35]; the eight lookup tables with clipped-entry counts 16378 / 16384 / 16384 / 0 equal to the mask popcounts |
| `table_and_constant_hashes_match_the_manifest` | every table, mask, exp table, weight (int16-widened form), multiplier, bias, GroupNorm array and the coordinates against the manifest hashes; the documented silu 11->11 and EXP hashes |
| `blob_round_trip_and_constants_identical_across_conditions` | v2 blob serialise/parse round trip; constants identical across the four sets of a scheme; truncated blob, v1 blob, `F_CT = 16`, a conv `f_out = 62` and a mask bit on a non-endpoint entry all refused |
| `noising_and_hint_match_the_exported_inputs` | integer `q_sample` reproduces `IN:Ct_int`, `hint = cat(E, coord)` reproduces `T:hint` |
| `full_int16_domain_is_admitted_and_every_clip_is_counted` | endpoints uncounted; the `-32767` counterexample gives `-32768` with one event; the four endpoint pairs |
| `lut_hits_on_clipped_entries_are_counted` | input 32767 on silu 11->12: value 32767, one hit; every index once: hits = popcount for every table |
| `left_shifts_are_checked_for_representability` | `rshift_round(32767, -62)`, `(±1, -63)` refuse; exact shifts up to 47 bits pass |
| `fast_conv_paths_equal_the_generic_definition` | the blocked 3x3 paths against the scalar definition at output widths 8, 9, 12, 16, 17, 112 (stride 1) and 17, 20, 33 (stride 2), 1x1 paths, random full-domain data |
| `rounding_helpers_follow_python_semantics`, `tester_detects_a_corrupted_constant` | as before |

### 4.3 The 42 FINAL differential boundary fixtures (`armc-int/tests/fixtures.rs`)

Staged by `tools/export_fixtures.py` into `fixtures_final/` (every JSON checked against the fixtures manifest, every
npz array against the hash the fixture declares). All 42 pass, expected values and counters **[measured]**:
`rounding_shifts_ties` (374 signed ties and neighbours at every used shift), `rounding_shifts_zero_negative`,
`rounding_divisors_ties` (237 cases at every GroupNorm divisor), `domain_endpoints_clamp16`, `noising_saturation`
(18 pairs incl. the `-39795 -> -32768` case, 3 events), `conv3x3_impulses_{s1_w20,s2_w20,s2_w21}` (generic and
blocked paths), `conv3x3_random_{int16,int8}_{s1,s2}_w24` (accumulators, static bound, requantised outputs, 62 events
on the int16 s2 case), `conv_requant_saturation_{S8,S30,S43}` (96 events each), `add_saturation_rescale` (four scale
combinations, 2/4/10/8 events), `concat_saturation_rescale` (4 events), six GroupNorm fixtures including the balanced
endpoints at n = 32256 and the both-signs saturation (119 events), `isqrt_perfect_squares` (51 values to 2^102),
`avgpool2_ties`, four bilinear border cases, eight `lut_all_indices_*` (every index, hits = popcount, the 32767 hit),
four attention fixtures (equal scores, exponent clamp at u = 32767, signed weighted averages over two heads, the
width-12 multiplier 18919 with r_shift 28) and `sse_endpoints` (184,712,316,364,800).

### 4.4 August rows 600-603, complete guest against the Python oracle and the frozen identities

Frames on the development machine: `frames_august/frame_00060{0,1,2,3}.raw` (24,472,000 bytes each; each BLAKE3 equals the chain log's
`bayer_blake3_hex`, checked by the driver before executing). Witnesses: assembled by `zkdiff-batch` from the chain log
(root `38a484b8…6572`). Noise: `noise_august/`, each file's BLAKE3 checked against the frozen table before executing.
Blob: FINAL int16 v2 `73310dda…`.

Python oracle: `tools/python_oracle_rows.py` builds G1's `QuantModel("int16")` on the FINAL checkpoint (calibration
recomputed, 15 rows), passes the positive control (d2 1328: 8,764,459,045 / 22,311,372,969), then runs
`forward_program` on G1's exported inputs for the rule offsets of rows 600-603
(`runs/python_oracle_rows_20260907T194614Z.json`); the same numbers are G1's `expected_residual_sum_int` in
`august_inputs/manifest.json`, which the acceptance verifier compares with the public `R_correct` / `R_wrong`
(checks `oracle.r_correct`, `oracle.r_wrong`).

Run 3, r5 ELF `51b7bc35…`, blob v2, `--expect expected_identities_august.json`
(`runs/batch_execute_r5_20260907/`, its `.log`; three executors shared the box) **[measured]**:

| row | offset | rule | wrong row | R_correct (guest = native = G1) | R_wrong (guest = native = G1) | D | class | clip | instructions | accepted |
|---:|---:|---|---:|---:|---:|---:|---|---:|---:|---|
| 600 | -2 | direct | 598 | 4,435,539,299 | 11,254,163,581 | +6,818,624,282 | positive | 0 | 14,400,363,198 | true |
| 601 | +2 | direct | 603 | 4,823,951,305 | 11,932,687,322 | +7,108,736,017 | positive | 0 | 14,400,345,341 | true |
| 602 | -15 | direct | 587 | 4,590,007,358 | 12,130,484,180 | +7,540,476,822 | positive | 0 | 14,400,313,902 | true |
| 603 | +15 | direct | 618 | 5,122,027,412 | 10,802,701,224 | +5,680,673,812 | positive | 0 | 14,400,340,066 | true |

Every row: guest bytes = native re-execution (752/752), every acceptance check PASS (layout, program, session, rule,
row identities including the normative noise BLAKE3 and the chain log's raw and emission digests, oracle residuals),
`D > 0`, kind 1, byte 11 = 0 (direct), clip events 0, peak RSS **15,592,988 KiB** (**15.97 GB /
14.87 GiB**) per executor **[measured]**. The receipts are schema `zbdiff-row-receipt/v3` (section 6) and each
carries the retained summary of the earlier attempt on the row (the unstripped interim ELF `d36a30f2…` of 21:26Z, the
same program; attempt id `20260907T212624Z-development-workstation-918327`). The r4 run 2 numbers of Astra r5 finding 12 are in
`runs/batch_execute_r4_20260907/`: 14,400,363,229; 14,400,345,372; 14,400,313,933; 14,400,340,097 instructions, peak
RSS 15,556,208 KiB = 15.93 GB = 14.84 GiB; the r5 guest executes 31 fewer instructions per row (the offset check
restructured, `parse_witness` 5,993 against 5,980). The independent Python check of the *binding* fields remains the synthetic
e2e run: 651/651 bytes equal gen_vectors.py's computation (`runs/execute_e2e_synthetic_r4_20260907.log`).

### 4.5 The mirrored -30 statement through the complete guest (Astra r5 finding 1)

Two runs, both with the r5 ELF `51b7bc35…` and the FINAL network, both **[measured]**:

**Synthetic 40-row session, row 39, -30 mirrored, complete guest, SUCCESS.** `relation/tests/vectors.rs`
(`build_mirror40`) builds a 40-row session from the relation's own primitives: real quicknet beacons borrowed from
August rows 600..639 (round, value, signature), arbitrary states advanced by the v9 rule, every emission rendered, the
golden padding tree, session id `ZBDIFF_SYNTHETIC_MIRROR40_001`, context `f4ce0dae…`, root `0592d4b7…`. Row 39 has
base `OFFSETS[39 mod 5] = +30`, whose direct wrong row 69 lies outside the 40 rows, so its offset is the mirror -30
with `u = 9`; row 39 commits the BLAKE3 of the real August frame 600 (`9d4a0745…`) and uses the normative noise of the
real -30 row 684 (`ea4ac2f6…`). The test evaluates the statement with the stub network, refuses each relabelling
(direct -30; +30 mirrored; the mirror flag on row 20; -15 mirrored, generically admissible, leaf mismatch) with the
named message, and writes the witness to `vectors_relation/synthetic_mirror40/` (`synthetic_mirror40.json` records
every hash). `zkdiff-execute --witness-dir vectors_relation/synthetic_mirror40 --raw frames_august/frame_000600.raw
--blob blobs/final_int16/constants_int16.blob` then runs the COMPLETE guest on it
(`runs/execute_synthetic_mirror40_r5_20260907.log`): `verified_public_values=true` (guest = native re-execution),
row 39, wrong 9, offset -30, byte 11 = 1, kind 1 (the synthetic conditioning has nothing to do with the frame, so the
statement's residual sums and sign are a mirror-path exercise and carry no result meaning; the log holds them),
clip events 0, **14,400,234,352** instructions, 4:06 (219.1 s host elapsed) wall, peak RSS 15,576,768 KiB. The acceptance verifier
would refuse this statement on `session.*` and `rule.range` (it is not the August session), which is exactly the
policy layer doing its job on a relation-valid statement.

**Real row 684, -30 mirrored, complete guest, the frame is on the node.** The prepared witness of row 684 (`runs/
batch_prepare_g2d_20260907/row_000684/witness/`: offset -30, flag mirrored, leaf of row 654) with a SUBSTITUTE frame
through the complete guest (`runs/execute_row684_substitute_frame_r5_20260907.log`): the guest passes `parse_witness`
(the offset check the r4 guest failed at), the beacon leg, the frame hash, the previous advance and both renders, and
fails exactly at the membership leg, `diffusion relation rejected: proved row does not open to the committed
ordered-session root` (1:55 wall, 12.1 GB RSS). The same is asserted natively by
`august_row_684_mirrored_minus_30_passes_the_offset_check_and_needs_only_its_frame`. The complete execute and the
proof of row 684 need `[frames directory]/frame_000684.raw` **[pending node]**;
`G2D_NODE_RUNBOOK.sh execute 684` is the command.

### 4.6 Negative controls (Astra r5 finding 10)

`zkdiff-batch controls --row 600 --expect …` runs, natively on the FINAL network, the rule's own statement of row 600
as baseline and 22 mutations, each recorded with mutation, expected failure stage, the actual message, the layer at
which it was refused and the identity (sha256) of every mutated item (`runs/controls_r5_20260907/CONTROLS.json`,
`all_behaved: true`) **[measured]**:

| layer | controls | actual |
|---|---|---|
| relation (the guest refuses) | raw byte 12345; header `S_r` byte; header drand round byte; row-r signature bit; predecessor `S_{r-1}` byte; predecessor signature byte; wrong-row `S_u` byte; sibling of r; sibling of u; another row's leaf under the same offset; blob header byte; mirror flag on the direct row 600; -30 direct on row 600; +30 mirrored on row 600; row 684 with -30 direct; row 684 with +30 mirrored; row 684 with +30 direct | `proved row does not open…`, `previous row's advance does not produce…`, `drand quicknet signature does not verify`, `drand signature is not a valid G1 point`, `declared wrong row's pattern does not render…`, `declared wrong row does not open…`, `wrong-row leaf witness does not carry row r + offset`, `armc-int constants blob rejected by the parser`, `mirrored offset claimed although the direct wrong row lies inside the session`, `declared offset must be a nonzero protocol offset`, `mirrored offset must be the mirror of a protocol offset`, `declared wrong row is outside the committed session` |
| policy (the relation ACCEPTS a coherent different statement; the acceptance verifier refuses it at the named check) | coherent alternative offset (+2 direct with the matching leaf of row 602, instead of the rule's -2): FAIL at `rule.assignment`; noise byte 0 flipped: FAIL at `row.noise_blake3`; a byte deep inside the blob flipped (parses, different digest): FAIL at `program.constants_sha256` | a different valid statement each time, refused only by the frozen identities |
| pending the node's frames | row 684 with -30 mirrored (the valid mirror) and row 698 with -15 direct (the policy-only case: generically valid, refused by `rule.assignment` alone) run with a substitute frame on the development machine and fail at the membership leg after the offset check; `G2D_NODE_RUNBOOK.sh controls 600` on the node reruns them with the real frames **[pending node]** | |

Proof-level controls (`zkdiff-verify --controls`, also `zkdiff-batch controls --proof`): relation-level mutations of
the public bytes (kind byte 10, flag byte 11, `u`, `d`, constants digest byte, noise BLAKE3 byte, `R_correct` byte,
clip count), of the proof bytes (a byte inside the Groth16 proof, the circuit-key prefix, truncation) and of the
program vkey, each of which the Groth16 verifier must reject; policy-level mutations of the expected identities
(constants digest, spec digest, session root, the row's noise BLAKE3, the row removed, the row's offset) under which
the proof still verifies and acceptance must fail at the named check. Exercised against the 2 September row-96
Groth16 artifact (another program, `--groth16-only`): all 12 relation-level controls rejected with the SDK-independent
error (`ProofVerificationFailed`, `NotOnCurve`, `Groth16VkeyHashMismatch`, `InvalidData`) **[measured]**; the
policy-level controls need a ZBDIFF proof and run on the node against the pilot proof (`G2D_NODE_RUNBOOK.sh verify`
runs them on the first proof) **[pending node]**. The three SDK tamper controls of the ceremony (public byte 716,
Groth16 nibble 96, wrong vkey) are retained and now record the SDK's actual error text in every receipt.

## 5. Instruction count of the complete guest

One August row (600), SP1 6.4.0 CPU executor on the development machine, r5 ELF `51b7bc35…`, blob v2 `73310dda…`
(`runs/batch_execute_r5_20260907/row_000600/receipt.json`) **[measured]**: total **14,400,363,198**, syscalls 269,904 (no
SHA-256 precompile on rv64). The region table of the r4 ELF (Astra-checked, finding 12) with the r5 values beside it:

| region | r4 instructions | r5 instructions | note |
|---|---:|---:|---|
| **total** | **14,400,363,229** | **14,400,363,198** | syscalls 269,904 in both |
| `zbdiff_relation` | 14,147,343,186 | 14,147,343,155 | everything inside `evaluate` |
| `denoiser_correct` | 3,455,557,627 | 3,455,557,627 | one network pass |
| `denoiser_wrong` | 3,455,557,224 | 3,455,557,224 | second pass |
| `emission_render_u` | 2,143,636,640 | 2,143,636,640 |  |
| `emission_render_r` | 2,143,611,423 | 2,143,611,423 |  |
| `frame_reduce` | 1,980,085,473 | 1,980,085,474 | soft-float area means (RELATION.md s.2.1), real frame |
| `raw_blake3_24MB` | 697,810,935 | 697,810,935 |  |
| `hints` | 257,096,202 | 257,096,202 |  |
| `constants_blob` | 252,852,645 | 252,852,645 | SHA-256 of 3,476,866 bytes + parse + mask checks; SHA-256 in software, section 8 |
| `previous_advance_leg` | 4,912,895 | 4,912,904 | one BLS verification + advance |
| `drand_verify` | 4,904,524 | 4,904,530 | one BLS verification |
| `noise` | 3,657,239 | 3,657,240 | BLAKE3 of 86 KB, forward noising, clip count |
| `constants` | 260,158 | 260,149 | digests |
| `ordered_session_membership` | 223,412 | 223,389 | two leaves, two paths |
| `public_commitment` | 42,387 | 42,387 |  |
| `parse_witness` | 5,980 | 5,993 | the offset check lives here |
| `private_input` | 603 | 603 |  |

Row 600 under the r4 ELF (Astra r5 finding 12): **6,911,114,851** instructions for the two network passes,
**252,852,645** for the blob region, **7,236,395,733** remaining (legs alone) **[derived from the r4 receipt]**; the
brief's expectation (7.2 G legs + 6.8 G network) holds. The per-row variation is data-dependent control flow
(GroupNorm's Newton iterations, clamps), in the 10^-5 range (rows 600-603 within 50,000 instructions of each other).
The synthetic e2e session with the r4 guest cost 14,394,768,783 (`runs/execute_e2e_synthetic_r4_20260907.log`); the
synthetic mirror40 session with the r5 guest 14,400,234,352 (section 4.5).

Host: about 3 to 4 min wall per row on the development machine's CPU executor with two other executors running, peak RSS 15.97 GB
(the client process's `VmHWM`; the node measured 17.3 GB for the same row, NODE_PROVE_READY / pilot log).

## 6. The batch driver, receipts and manifest (Astra r5 finding 9)

`zkdiff-batch prepare|execute|prove|controls --chain-log … --out … --blob … --expect expected_identities_august.json
[--build-record …] [--rows a..b] [--frames-dir …] [--noise-dir …] [--prover cuda --device N]`. The rule is
`relation/src/rule.rs`; `prove` REQUIRES `--expect`, refuses to start if the expected ELF, blob, spec, circuit key,
circuit version or session root differ from the process's own, and refuses to prove if the derived vkey differs from
the expected one. Before a row is executed or proved its noise file's BLAKE3 must equal the frozen table entry.

**Receipt** `row_XXXXXX/receipt.json`, schema `zbdiff-row-receipt/v3`: `attempt_id` (`<utc>-<host>-<pid>`),
`attempt_started_utc`, `attempts` (the retained summaries of every earlier receipt of the row: attempt id, status,
error, elapsed, public hash, proof hash, outcome), `status` (`prepared_native | executed | proved | pending_frame |
pending_noise | failed | out_of_range_by_rule`), the exact `public_values_hex` and `public_values_sha256`, `decoded`
(every identity of the statement: session, root, context, r, u, d, flag, kind, digests, noise BLAKE3, raw BLAKE3,
emission digests, rounds, leaves), `r_correct`, `r_wrong`, signed `difference`, `outcome_class`
(positive / zero / negative), `clip_flag`, `clip_events` (and whether saturated), `proof_file` / `proof_bytes` /
`proof_sha256` (the exact bincode artifact), `proof_raw_bytes_file` / `proof_raw_bytes_sha256` (the
`SP1ProofWithPublicValues::bytes()` the standalone verifier consumes), `public_values_file`, `sp1_vkey`, `sp1_version`,
`groth16_vk_sha256`, `guest_elf_sha256` / `guest_elf_bytes`, `constants_sha256`, `spec_sha256`, `chain_log_blake3`,
`raw_sha256` / `raw_blake3`, `noise_sha256` / `noise_blake3`, `oracle_mode` (native re-execution) and the acceptance
report (`accepted`, `failed_check`, every check), `verification` (SDK verify, the three SDK tamper controls with the
SDK's error text), `cycle_limit_requested`, timings (`setup_elapsed_ms`, `prove_elapsed_ms`,
`verify_and_tamper_elapsed_ms`, `acceptance_elapsed_ms`), `host_peak_rss_kib` (the client process only), the exact
`command`, `binary_sha256` (the running host binary), `build_record` (path and sha256) and `expected_identities`
(path and sha256). Execute mode adds `total_instruction_count`, `total_syscall_count`, `cycle_regions`.

**Manifest** `BATCH_MANIFEST.json`, schema `zbdiff-batch/v3`, rewritten DURABLY after every row (temp file, fsync,
rename, directory fsync) so a killed process leaves recoverable progress: `required_rows`, `rows_required`,
`rows_recorded`, `rows_done_ok`, `complete` (true only when `finished` and every required row is `proved` with
`acceptance.accepted`), `status_counts`, `outcome_counts`, `failed_attempts_retained`, the rule (text, constants,
mirrored rows of this run), the session, ELF / vkey / circuit identities, the denoiser, the noise rule, the command,
host, binary hash, build record and expected identities, and every row entry. `tools/merge_batch_manifests.py`
REFUSES a collection unless the inputs agree on ELF, vkey, circuit, blob, spec, session and rule, the union is exactly
the 112 rows 600..711 once each, every row is proved and accepted, and every receipt, proof artifact and public-values
file beside a manifest exists and hashes to what its entry says (stale collections refused); `--allow-incomplete`
writes a partial merge marked `complete: false` with the problems listed and still exits 1. Exercised on fabricated
incomplete, disagreeing and stale collections (section 10). Nothing is inherited from the first input on which the inputs
were not checked to agree.

**Durability, corrected (Astra r5 finding 9):** the proof artifact was always fsynced (`save_exact`); receipts,
manifests, public bytes, raw proof bytes, manifests of the ceremony and the controls report are now written by
`write_durable` (temp, fsync, rename, directory fsync) as well; `prove.stdout`, `prove.stderr` and the nvidia-smi
sidecars remain ordinary buffered files.

The August prepare with the r5 binary (`runs/batch_prepare_r5_20260907/`, 48 s): 112 rows, `prepared_native` 4
(600-603, each `accepted: true`), `pending_frame` 108, `failed` 0, `out_of_range_by_rule` 0, mirrored rows exactly
684, 689, 694, 698, 699, 703, 704, 708, 709, 711 **[measured]**.

## 7. On-node batch procedure (Astra r5 finding 6 applied; every step [confirm] until run)

Everything below is `node_prep/G2D_NODE_RUNBOOK.sh` (`build | execute R | controls [R] [PROOF] | prove-one N R | prove
| status | verify | merge`), `set -euo pipefail`, every loop terminated with `|| exit 1`, no pipeline continues after a
refusal. The tree root is the runbook's own parent directory, so the copy under `g2_guest_r5/` drives that tree.
Node facts (toolchain, circuit cache, gpu server) are NODE_PROVE_READY.md's and the pilot log's.

### 7.1 What to copy (the development machine -> node, the tree as a tree)

`tools/make_sha256sums_g2d.sh` writes `SHA256SUMS_G2D` over the transfer PAYLOAD only (sources, data, tools, docs,
build records; nothing under `target/`), so `sha256sum -c SHA256SUMS_G2D` passes or fails on the payload alone, and
`REFERENCE_PINS_G2D.txt` with the development machine's ELF and host binary hashes for the record. The rsync copies the tree with its
shape preserved (one source directory, `-a`), never a brace list of sub-paths:

```
SSH="ssh -o StrictHostKeyChecking=accept-new"; H=[node user]@[node address]
rsync -az --info=stats1 --exclude 'target/' --exclude 'frames_august/' --exclude 'pilot/' --exclude 'oracle/' \
  --exclude 'oracle_final/' --exclude 'artifacts/' --exclude 'august_inputs_i16/' --exclude 'armc-eval-bench/' --exclude 'logs/' \
  -e "$SSH" source/ \
  "$H:source/"
```

This is the command that was run (twice, incrementally; `node_prep/r5/rsync_pass*.log`). No frame leaves the development machine: the
frames live on the node at `[frames directory]/frame_{r:06d}.raw`.

### 7.2 Build on the node and reproduce the pins (`G2D_NODE_RUNBOOK.sh build`)

`sha256sum -c SHA256SUMS_G2D --quiet` (payload only), the blob pin, then `CUDA=1 nice -n 10
armc-relation/build_reproducible.sh` (offline, `--locked`, fail-closed as in section 3.1), then
`$S/target/release/zkdiff-ceremony vkey` against the pin, `zkdiff-verify --identity` against the pinned ELF and
circuit key, and the installed `~/.sp1/circuits/groth16/v6.1.0/groth16_vk.bin` against the embedded key. The
executable path is the script's `target/release` (the r4 runbook had invoked it from `$G2`). Done once by hand on
7 September at 21:43Z with the driver alone (section 3.2): `BUILD_REPRODUCED_OK`.

### 7.3 Execute one row, then ONE pilot proof (`execute 600`, `prove-one N 600`)

`execute 600` must show the section 5 count, R_correct 4,435,539,299, R_wrong 11,254,163,581, clip events 0,
`oracle_mode native_reexecution`, `accepted: true`; the step fails unless `status=executed` and the receipt's
acceptance is true. Then one complete Groth16 proof of row 600 on one free GPU, detached, with `--expect` and
`--build-record`: its `prove_elapsed_ms`, `host_peak_rss_kib` (client only), the sidecars and the standalone
acceptance are the first measured numbers for a 14.4 G-instruction proof. Instrumentation for Astra r5 finding 7
(cold start, CPU and CUDA setup, phases, shard counts, VRAM sampling method, server and executor memory, CPU,
`/tmp` and `/dev/shm`, GPU and driver identities) is the timing pilot's script (`pilot/node_records/prove_step4.sh`);
its measurement on the superseded r4 ELF stands as a measurement, its proof does not stand as a result. The batch is
sized from the pilot, never from the extrapolation of section 1.

### 7.4 Prove, eight rows in parallel, one per GPU (`prove`), after the release step

One process per GPU, ranges 600..613, 614..627, …, 698..711, `--expect`, `--build-record`, `setsid nohup`, an
nvidia-smi sidecar per GPU, starts staggered by 20 s (the eight share CPU, RAM, storage and the server installation).
Per process: CPU `setup` for the vkey (asserted against the expected), CUDA `setup` once, then per row: frame read and
BLAKE3 check, noise BLAKE3 against the table, `.groth16()` proof with proof nonce zero, `SP1Proof::Groth16` and
circuit version asserted, native re-execution of the public bytes, SDK verify plus the three SDK tamper controls,
the acceptance verifier under the frozen identities, exact durable artifacts (`row_XXXXXX_groth16.bin`,
`row_XXXXXX_proof_bytes.bin`, `row_XXXXXX_public_values.{bin,hex}`, `manifest.json`, `receipt.json`), the manifest
rewritten. A row whose proof verifies but whose statement is not the expected one is a `failed` row, never a success.
Expected per row 43.7 to 55.2 min on A100-40GB rates **[extrapolation]**, replaced by the pilot's measurement; a
partial run is resumed by restarting with the first unfinished row as `a` (the receipts retain the earlier attempts).

### 7.5 Verify and collect (`verify`, `merge`, then rsync back)

`verify`: `zkdiff-verify --proof … --expect …` on EVERY `row_*_groth16.bin` (cold, standalone; the step exits 1 on
the first refusal) and `--controls` on the first proof (the proof-level negative controls). `merge`: `verify`, then
the strict merger (all 112 rows accepted or it refuses), then `SHA256SUMS_RUNS`. Back on the development machine: `sha256sum -c
SHA256SUMS_RUNS`, `zkdiff-verify` on every proof with the development machine's binary, and the merged manifest is the record: every
outcome, sign and clip count included, nothing filtered.

## 8. Open items and risks

| item | state |
|---|---|
| row 684 (and the other five -30 rows) through the complete guest | passes the offset check and every leg up to the frame hash on the development machine; complete execute needs the frame on the node **[pending node]**; a mirrored -30 statement did run through the complete guest on the synthetic session (section 4.5) |
| proof-level policy controls | need a ZBDIFF proof: the node's `verify` step runs them on the first proof **[pending node]** |
| SHA-256 of the blob in software | about 253 M instructions (1.8 %) because the pinned sp1 sha2 fork gates its precompile on `target_arch = "riscv32"` and this guest is rv64; levers unchanged |
| host RSS about 16 GB per executor | eight concurrent provers each run the executor; `sp1-gpu-server` RSS and VRAM at 14.4 G instructions per row are the pilot's to measure **[confirm]** |
| glibc | the development machine's host binaries need glibc 2.39; the node rebuilt from source (section 3.2) |
| cycle limit under CUDA | requested, not enforced by the pinned client (Astra r5 finding 8); the execute step establishes the count first; an operational deadline is the operator's |
| GPU occupancy | the pilot occupies GPU 0; which GPUs, and when, was fixed at launch (`receipts/launch_schedule.txt`: eight processes, one per GPU, started 90 s apart) |
| d2 row through the complete guest | not possible on the development machine (no raw frame, no d2 signatures) |
| profiler function names | stripped with the symbol table; the cycle-tracker regions (printed markers) are unaffected |
| `EXP_TABLE_CLIP_MASK` | exported and hash-checked but not consumed: the manifest states the exp table is not an int16 tensor and the index clamp is not a clip event; the mask is all zero |
| conversion-time input clips | the oracle's `input:*` counters are conversion-time facts recorded in the artifact manifests (all zero), unobservable in the guest; stated in the spec JSON |
| G1's README_FINAL wording | Astra r5 finding 11 also asks G1 to correct a stale statement about `C_t` being supplied and both hashes being SHA-256; README_FINAL section 5 states that `C_t` is derived in-circuit and the noise digest is BLAKE3 |

## 9. Files added or changed (all under `g2_guest/`; `armc-eval-bench/`, `g1_integer/` and `pilot/` untouched)

```
armc-relation/relation/src/{rule.rs (new), statement.rs, lib.rs}        check_offset_rule, hardened PublicOutput::parse, the rule as a function
armc-relation/relation/tests/vectors.rs                                 synthetic mirror40 session, row-684 witness test
armc-relation/adapter/src/lib.rs, armc-int/src/kernels.rs               finding-4 wording (comments)
armc-relation/script/{Cargo.toml,Cargo.lock,build.rs}                   zkdiff-verify bin, sp1-verifier dependency, -Cstrip=symbols
armc-relation/script/src/{accept.rs (new), verify.rs (new), ceremony.rs, ceremony_core.rs, batch.rs, execute.rs}
armc-relation/build_reproducible.sh, armc-relation/RELATION.md (v1.2)
armc-relation/runs/{build_record_20260907T2124*..T2147*.txt, build_log_*.txt, SOURCE_DIGESTS_*.txt,
                    batch_prepare_r5_20260907(.log,/), batch_execute_r5_20260907(.log,/), controls_r5_20260907(.log,/),
                    execute_synthetic_mirror40_r5_20260907.log, execute_row684_substitute_frame_r5_20260907.log}
tools/{make_expected_identities.py (new), merge_batch_manifests.py (strict), make_sha256sums_g2d.sh (payload only)}
node_prep/{G2D_NODE_RUNBOOK.sh, r5/rsync_pass*.log}
vectors_relation/synthetic_mirror40/ (new), expected_identities_august.json (new), SHA256SUMS_G2D, REFERENCE_PINS_G2D.txt (new)
logs/{test_relation_r5_pass*.log, test_armc_int_r5.log, build_script_r5_pass*.log, verify_groth16_only_row096*.json, script_Cargo.lock.before_r5}
FULL_GUEST.md (v1.2)
```

## 10. Audit note

Checked by running on the development machine: every test count above (`cargo test --release --offline` in `armc-relation`, `armc-int`
and `script`); the driver five times (two pin-mode runs at the same path, one pin-mode run of a source copy at another
absolute path, two asserting runs), each record read back; `readelf` on the ELF (segments, sections, symbol table
present then absent); `sha256sum` of the circuit key on the development machine against the embedded key; `zkdiff-verify --identity`;
the Groth16 layer of the acceptance verifier and its 12 rejection controls on a real Groth16 artifact of another
program; the four-row execute with acceptance; the synthetic mirror40 execute; the row-684 substitute-frame execute;
the 112-row prepare; the 23 witness-level controls; the strict merger on fabricated incomplete, disagreeing and stale
collections; `make_expected_identities.py` against G1's manifest (every noise file's sha256 and BLAKE3, the rule
offsets and wrong rows, the residual keys). Read in source: `sp1-core-executor-6.4.0` `disassembler/elf.rs`
(`TRAP_CONTEXT_SYMBOL`, PT_LOAD handling), `sp1-verifier-6.4.0` (`Groth16Verifier::verify`, `GROTH16_VK_BYTES`,
`VK_ROOT_BYTES`), `sp1-sdk-6.4.0` (`SP1ProofWithPublicValues::bytes`, `verify_proof`), `sp1-zkvm-6.4.0` (no trap
symbol). On the node, exactly: the rsync into the new `g2_guest_r5/`, the driver run there (its record read back),
and nothing else; the pilot on GPU 0 was not touched. Not done: any proof; any GitHub or publication action; any edit
under `armc-eval-bench/`, `g1_integer/` or `pilot/`. Not verified: everything marked
[pending node] and [confirm]; the proving time.

## 11. Astra r5 applied (`astra_r5/ASTRA_VERDICT_fullguest_r5.md`)

| finding | verdict | where it is fixed |
|---|---|---|
| 1 mirrored -30 rejected | REVISE | `statement::check_offset_rule` validates direct and mirrored offsets together; `rule.rs` regression over all 112 assignments; synthetic mirror40 complete-guest run; row 684 to the frame hash on the development machine [pending node]; RELATION.md v1.2 sections 1, 1.1, 1.2, 1.3, 5, 7; ELF/vkey re-pinned (sections 1, 3) |
| 2 computation bound | ACCEPT | unchanged; the acceptance verifier now checks the expected public identities the acceptance was conditional on |
| 3 verifier acceptance checks | REVISE | `accept.rs`, `zkdiff-verify`, `zkdiff-ceremony verify --expect`, `zkdiff-batch prove --expect`; `expected_identities_august.json`; the normative noise mapping enforced at acceptance and before execution (section 2.5) |
| 4 saturation semantics | ACCEPT, wording | "outside the zero-clipping regime covered by the reported validation", every nonzero count published, 65535 means at least 65535, count zero covers the counted runtime sites (section 2.2; `kernels.rs`, `adapter/lib.rs`) |
| 5 driver not fail-closed | REVISE | `build_reproducible.sh`: cargo status preserved, full log kept, fresh ELF and host binaries asserted, environment / commands / compiler / server / circuit identities recorded, `LC_ALL=C`; the final source lists cited (section 3.1) |
| 6 transfer and runbook | REVISE | rsync of the tree as a tree; `SHA256SUMS_G2D` over the payload only (`make_sha256sums_g2d.sh`); `$S/target/release/zkdiff-ceremony`; `set -euo pipefail` and `|| exit 1` everywhere; `verify` and strict `merge` steps (section 7; `G2D_NODE_RUNBOOK.sh`) |
| 7 pilot instrumentation | ACCEPT plan, REVISE instrumentation | the timing pilot's script (`pilot/node_records/prove_step4.sh`); this tree records `host_peak_rss_kib` as the client process only and the eight-process contract in section 7.4 |
| 8 cycle limit not enforced under CUDA | REVISE | recorded as `cycle_limit_requested` with the note in every receipt and manifest; the execute step establishes counts first (sections 2.3, 6) |
| 9 receipts and completeness | REVISE | receipt schema v3, manifest v3 written durably after every row with `complete`, retained attempts, outcome classes; strict merger; the fsync claim corrected (section 6) |
| 10 negative controls | REVISE | `zkdiff-batch controls` (23 witness-level controls, relation vs policy), `zkdiff-verify --controls` (proof-level), SDK tamper controls with error text (section 4.6) |
| 11 held-out description | REVISE | the claim boundary below, verbatim |
| 12 numbers | REVISE | r4 counts, row-600 breakdown, RSS 15.93 GB / 14.84 GiB, 54 tests, 43.7-55.2 min per row and 10.2-12.9 h for 112 on 8 GPUs marked extrapolation (sections 1, 4.4, 5) |

### 11.1 Claim boundary after successful verification (Astra r5 finding 11, verbatim)

Weight-training exclusion is supported. However, quantisation calibration used August targets 600, 616, 632, 648,
664, 680, 696, each with its own and +15 conditioning (`g1_integer/int_ref.py` `default_calib_rows`,
`final/constants_int16.json` calibration rows). Thus seven raw targets and fourteen conditioning identities influenced
the integer scales. "Untouched test set" would be false. Astra's three paragraphs:

> We publish one independently verified Groth16 proof for each August target row 600–711, including every signed outcome and any clipping. Each proof establishes execution binding of an integer diffusion evaluator adapted from the frozen ARM-C protocol: whole-frame preprocessing of a committed raw frame, authenticated conditioning from the declared row states, and two evaluations at timestep 150 sharing one noisy frame and one hash-bound normative noise target. The comparison uses the published single-offset rule, including its boundary mirrors.
>
> Model weights were trained on August rows 0–599 plus the d2/v10 training blocks. August rows 600–711 were held out from weight training; quantisation calibration used seven targets from this set and their own/+15 hints, listed in the release manifest. The repeatedly consulted d2/v10 evaluation blocks are development validation.
>
> These proofs establish the specified integer computations and bindings. They establish no physical-capture, realness, liveness, illumination-causality, adversarial-resistance or unseen-session-generalisation claim. They do not reproduce the original published checkpoint, five-offset aggregate, eight-seed AUROC or full diffusion sampling. Noise generation remains external provenance; the proof binds the normative bytes and computes forward noising.

## Log

- 1.0 (2026-09-07, BOSUN) — adapter, layout amendments, complete guest built and pinned (ELF `395d376e…`),
  parity on d2 1328 (both constant sets), FINAL layer-by-layer, August rows 600-603 in the guest against the Python
  oracle; instruction count 14.25 G per row; batch manifest under the two-part rule; node runbook written.
- 1.1 (2026-09-07, BOSUN) — Astra r4 applied to the kernel crate (FINAL saturation contract, masks, transport,
  representability, attention multiplier), 42 boundary fixtures wired in, clip count published (bytes 749..752),
  reproducible build driver with inherited offline config and a demonstrated second-build reproduction (ELF
  `0f1fd524…`, vkey `0x0009823f…`), CYCLES.md numbers corrected, pilot-proof step added to the node procedure,
  timing estimate corrected for the double-counted Groth16 tail; rows 600-603 re-executed with the r4 guest.
- 1.2 (2026-09-07, BOSUN, Astra r5) — mirrored -30 admitted where the rule needs it and nowhere else; the rule as
  one function; acceptance verifier and frozen expected identities; fail-closed driver; runbook and checksums over the
  payload; receipts/manifest v3 with durable writes, attempts and outcome classes; strict merger; negative controls in
  two layers; claim boundary and calibration disclosure; r4 numbers filled in; the ELF made path-independent
  (`-Cstrip=symbols`) after the node reproduced the vkey but not the file hash at a different absolute path, and the
  new pin (`51b7bc35…`, 396,200 B, vkey `0x00f01894…`) reproduced on the development machine, in a the development machine copy at another path and on the
  node (`g2_guest_r5`). The /tmp probe log, quoted: `guest_elf_bytes=396200
  guest_elf_sha256=51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc`,
  `sp1_vkey=0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027`. Nothing proved.
