---
version: 1.4
date: 2026-09-09
status: the statement each proof establishes: public inputs, witness, relation, layout and the declared offset rule, as frozen before proving; section 1a and the field notes added after the outside-agent readability audits
author: Cathal Ryan Hynes (author of record); drafted with BOSUN, the project's automated research assistant
---

# The statement

Every number and layout below is copied from the frozen source and its records: `source/armc-relation/RELATION.md` v1.2
(sections 1 to 2, as amended for the complete guest), `source/FULL_GUEST.md` v1.2 (sections 2 and 5), the acceptance
verifier `source/armc-relation/script/src/accept.rs`, the rule `source/armc-relation/relation/src/rule.rs`, and the oracle's
contract `oracle/final/README_FINAL.md` (sections 3 and 5). What the statement means and does not mean is fixed in
`CLAIM_BOUNDARY.md`.

## 1. In words

For the pinned August session (context digest and ordered-session root of the 712-row session recorded on 22 August 2026),
a proved row `r` in 600 to 711 and a declared wrong row `u = r + d`, the guest program (SP1 6.4.0, ELF and verifying key
in `PINS.json`) does the following inside the proof, in this order.

1. It hashes the complete raw Bayer frame of row `r` (24,472,000 bytes) with BLAKE3 and re-derives the chain advance
   `S_{r+1}` from the row's state, the frame digest, the row metadata and the beacon.
2. It verifies the drand quicknet BLS signatures of rows `r` and `r-1` under the compiled-in quicknet public key,
   requires `SHA-256(signature)` to equal the randomness each advance consumed, and re-derives `S_r` from row `r-1`'s
   record, so the proved state is the successor of an authenticated predecessor.
3. It regenerates both emission patterns from `S_r` and `S_u` (BLAKE3 XOF seeds, four-octave integer render), digests
   them, and requires row `u`'s digest to equal the field of its witnessed leaf; row `r`'s digest enters its own leaf.
4. It opens both leaves to the same committed ordered-session root under the session context.
5. It derives the integer network inputs from the frame and the two XOF streams: the whole-frame area reduction of the
   four CFA planes to 4 x 96 x 112 (the trained pipeline's float32, float16 and bfloat16 path, reproduced bit for bit in
   software floating point), the twelve XOF octave channels and two coordinate channels of each conditioning, and the
   forward-noised frame `C_t` at timestep 150 from the frame and the pinned noise tensor.
6. It evaluates the pinned integer denoiser once under each conditioning with the same `C_t` and the same noise target,
   and publishes `R_correct`, `R_wrong`, `D = R_wrong - R_correct`, the sign of `D`, the common denominator, the count of
   saturating operations, and every binding digest.

The direct offset `d` lies in the protocol's set {-2, +2, -15, +15, +30}. Where `r + d` would leave the session the
mirrored offset `-d` is used and flagged (section 7). Zero crop: the whole sensor frame enters the reduction; nothing is
cropped. The proof is a Groth16 proof over the SP1 program's execution; a verifier holds the 356-byte raw proof, the
752-byte public statement, the program's verifying key and the circuit's verifier key, and nothing else from the prover.

## 1a. The beacon rounds, plainly

Item 2 says the guest verifies the beacons of rows `r` and `r-1`. Those are usually the same beacon. Quicknet publishes one
round every 3 seconds and the camera captured a row every 400 ms (median 400.05 ms over the session), so consecutive rows
share a round most of the time: 646 of the 711 consecutive pairs of the session carry the same round, the 712 rows carry 66
distinct rounds (2 to 19 rows per round, median 9), and across the proof rows 600 to 711 there are 10 distinct rounds, with
103 of the 112 proofs carrying the same round for `r` and `r-1` (the nine whose predecessor sits in an earlier round are 604,
614, 623, 633, 643, 662, 671, 690 and 699). Row 600's statement carries round 31521690 twice. All of these are counted from
`source/vectors_relation/august/chain_log.csv` (`PINS.json` `drand`; `tools/check_identities.py` recounts them).

What the predecessor leg does for such a row is not a second beacon: it re-derives `S_r` from row `r-1`'s complete record
(its state, its frame digest, its `meta`, its round and its value) and requires the result to equal the state row `r`
carries, so the proved state is the successor of an authenticated predecessor record and not a free choice of the prover;
the signature verification is repeated on the same bytes. When the rounds differ, the leg additionally verifies a second
signature. The rounds a statement publishes are those of the chain log for rows `r` and `r-1`, and the acceptance verifier
pins both to that log (checks `row.own_drand_round`, `row.prev_drand_round`). The guest checks no round monotonicity; the
chain log's rounds are non-decreasing along the session, a property of the log, not a circuit check. The quicknet public key
the guest verifies under is compiled into `source/armc-relation/relation/src/beacon.rs` (its hex is in `PINS.json` `drand`);
comparing it with the public quicknet chain information, and checking that a round's signature is the one the relay
published, are the out-of-band steps no proof supplies (`VERIFY.md` section 4).

The chain log's `drand_staleness_ms` column is the recorder's own measure, in milliseconds, of how old the beacon was when
the row was captured: 1,363 to 10,799 ms over the session, median 6,100 ms, and 6,486 ms for row 600. It is informational,
read by nothing in the guest and bound by nothing in the statement; the ZeeBeam release's referee record notes that the log
therefore does not support a "newest round" reading, and this package makes none.

## 2. Public statement `ZBDIFF01`, 752 bytes

Little-endian unless stated. Offsets are byte offsets. Source: `RELATION.md` section 1.1 as amended by `FULL_GUEST.md`
section 2.2 (byte 11 and bytes 749 to 752), reproduced from `source/armc-relation/relation/src/statement.rs`
(`PublicOutput`). `tools/decode_zbdiff01.py` decodes a statement into these fields.

| offset | bytes | field | how constrained |
|---:|---:|---|---|
| 0 | 8 | magic `ZBDIFF01` | fixed |
| 8 | 1 | ABI = 1 | fixed |
| 9 | 1 | protocol = 9 (TB-v0.9) | fixed |
| 10 | 1 | denoiser kind (0 stub, 1 armc-int) | from the network implementation; every proof here carries 1 |
| 11 | 1 | offset-rule flag: 0 direct, 1 mirrored | witness item 10; validated together with `d` (section 7) |
| 12 | 4 | public length = 752 | fixed |
| 16 | 4 | row `r` | header; `1 <= r < row_count` |
| 20 | 4 | row `u` | `u = r + d`, `0 <= u < row_count`, equals the witnessed leaf's row |
| 24 | 4 | declared offset `d` (i32) | direct: `d` in {-2, 2, -15, 15, 30}; mirrored: `-d` in that set and `r - d` outside `[0, row_count)` |
| 28 | 4 | row count | session context |
| 32 | 2 | tree depth | minimal for the row count |
| 34 | 2 | session id length; 36 to 164 session id, zero padded to 128 | session context |
| 164 | 128 | `S_0` (164), `S_N` (196), authority-manifest SHA-256 (228), chain-log BLAKE3 (260): the session seed, the state after the last advance, the digest of the recorder's session manifest (only its digest is published, `FAQ.md` 2) and the digest of `chain_log.csv` | inputs to the context digest |
| 292 | 32 | context digest: `H(CONTEXT, [b"TB-v0.9", session id, u32be(row count), [1], S_0, S_N, manifest SHA-256, chain-log BLAKE3])`, where `CONTEXT` is the domain string `ZEEBEAM_ORDERED_SESSION_CONTEXT_V1\0` and `ROW` below is `ZEEBEAM_ORDERED_SESSION_ROW_V1\0` (`HASHES.md` gives every domain string and the length-prefix rule) | recomputed |
| 324 | 32 | ordered-session root (wrapped) | both leaves open to it |
| 356 | 64 | `leaf_r`, `leaf_u`: `H(ROW, [context, u32be(row), S_row, BLAKE3(raw_row), meta_row, u64be(round_row), value_row, S_{row+1}, BLAKE3(E_row)])` (`HASHES.md`) | recomputed |
| 420 | 32 | `BLAKE3(raw_r)` | recomputed from the frame |
| 452 | 64 | emission digests of `r` and `u` | recomputed by the render |
| 516 | 16 | previous and own drand rounds (u64, big-endian) | both signatures verified |
| 532 | 32 | drand leg digest `BLAKE3("ZBDIFF:DRAND:v1\0" ‖ round_{r-1} ‖ v_{r-1} ‖ round_r ‖ v_r ‖ quicknet chain hash)` | recomputed |
| 564 | 96 | constants SHA-256 (the network blob), network spec SHA-256, preprocessing spec SHA-256 | the blob is hashed in circuit; the specs are compiled constants |
| 660 | 32 | noise BLAKE3 | recomputed from the witness |
| 692 | 4+8+8+1+1+1+1 | timestep 150 (u32), SA 63540 (i64), SO 16053 (i64), then four single bytes: shift 16, F_CT 12, F_HINT 14, F_EPS 12 (the fractional bits of the reduced frame `C`, the hint and the network output `eps`: Q12, Q14, Q12); `tools/decode_zbdiff01.py` and `statement.rs` give the order | fixed |
| 716 | 8+8+8+8 | `R_correct`, `R_wrong` (u64), `D` (i64), denominator 43008 · 2^24 = 721,554,505,728 (4 x 96 x 112 = 43,008 output values, each a squared difference of two Q12 numbers, so 24 fractional bits; `R / denominator` is the residual in the float model's MSE units) | outputs |
| 748 | 1 | sign (1 if `D > 0`) | derived |
| 749 | 1+2 | clip flag (1 iff the count is nonzero), clip-event count (u16, saturating at 65535) | noising clamps plus both network passes' clamps and masked-table hits (a table look-up landing on an entry the table builder had to clip to the int16 range, flagged in the table's mask; `source/armc-int/src/blob.rs`) |

The statement carries no pixels. It publishes the raw and emission digests and both leaves because the August
`chain_log.csv` is public and carries them (the ZeeBeam release's `final_relation/chain/chain_log.csv`, SHA-256
`5d9af297ae37119df15412f516a4543ee9f54b6aa66186abe478512fe9a1ff48`, is byte-identical to `source/vectors_relation/august/chain_log.csv`).

## 3. Private witness

Ten `read_vec` items in order, then the constants blob as an eleventh private input (`RELATION.md` section 1.2,
`FULL_GUEST.md` section 2.2).

| # | item | bytes | content |
|---|---|---:|---|
| 1 | `header_r` | 120 | `ZBROWW01`: row `r`, `S_r`, meta (28: big-endian row index u32, camera device timestamp ns u64, capture wall-clock ns u64, a u32 reading 64000 on every row of this session, the ASCII pixel-format tag `RG08`), drand round, drand value |
| 2 | `membership` | 184 + id + 32·depth | `ZBOSM001`: session context, committed root, siblings of row `r` |
| 3 | `raw_r` | 24,472,000 | the row's raw Bayer frame |
| 4 | `sig_r` | 48 | quicknet signature of row `r`'s round |
| 5 | `previous` | 188 | `ZBDPRV01`: `S_{r-1}`, `BLAKE3(raw_{r-1})`, meta, round, value, signature of row `r-1` |
| 6 | `leaf_u` | 208 | `ZBDLFU01`: row `u`'s leaf fields (`S_u`, raw digest, meta, round, value, `S_{u+1}`, emission digest) |
| 7 | `siblings_u` | 32·depth | row `u`'s path |
| 8 | `noise` | 86,016 | int16 little-endian Q12, 4 x 96 x 112: the normative noise of row `r` (section 8) |
| 9 | `offset` | 4 | i32 little-endian `d` |
| 10 | `offset_rule` | 1 | 0 direct, 1 mirrored; an empty item reads as direct |
| 11 | constants blob | 3,476,866 | the armc-int int16 constants, blob format v2 with the clipping masks; SHA-256 published at offset 564 |

Row `u`'s raw frame is never needed: its leaf commits it. The previous-row record is an explicit witness, so the same leg
serves any session whose beacon signatures are known.

## 4. The relation, leg by leg

The order the guest runs (`statement.rs` `evaluate`); the labels are the cycle-tracker regions of `RESULTS.md` section 4.

| # | leg | region |
|---|---|---|
| 1 | parse the ten items; `r >= 1`, `r < n`; `check_offset_rule(r, n, d, flag)`; `0 <= u = r + d < n`; `leaf_u.row == u`; `meta_{r-1}` names `r-1` | `parse_witness` |
| 2 | digests: preprocessing spec, network constants and spec | `constants` |
| 3 | `verify_quicknet_beacon(round_r, sig_r)`, `SHA-256(sig_r) == v_r` | `drand_verify` |
| 4 | `BLAKE3(raw_r)`; `S_{r+1} = advance_chain(S_r, BLAKE3(raw_r), meta_r, round_r, v_r)` | `raw_blake3_24MB` |
| 5 | verify and bind `sig_{r-1}`; `advance_chain(S_{r-1}, ...) == S_r`; row 0 refused | `previous_advance_leg` |
| 6 | `expand_all(S_r)`, render 1080 rows, streaming BLAKE3 | `emission_render_r` |
| 7 | the same for `S_u`; digest must equal `leaf_u.emission_blake3` | `emission_render_u` |
| 8 | `leaf_r = H(ROW, [context, u32be(r), S_r, BLAKE3(raw_r), meta_r, u64be(round_r), v_r, S_{r+1}, emission_r])`, `leaf_u` from the witness; both open to the root (`HASHES.md`) | `ordered_session_membership` |
| 9 | whole-frame reduction to `C_int` | `frame_reduce` |
| 10 | `E_int` for both streams, coordinates, 14-channel hints | `hints` |
| 11 | `BLAKE3(noise)`, `C_t = clamp16((SA·C + SO·noise + 2^15) >> 16)`; saturations counted into the public clip count | `noise` |
| 12 | `eps_r = f(C_t, hint_r)`, `R_correct = Σ(eps_r - noise)^2` | `denoiser_correct` |
| 13 | `eps_u = f(C_t, hint_u)`, `R_wrong` | `denoiser_wrong` |
| 14 | encode and commit the 752 bytes | `public_commitment` |

Every check fails closed with a static message. The host oracle calls the same `evaluate` natively, so a divergence
between the zkVM and native execution is detectable; every receipt records `oracle_mode: native_reexecution`.

## 5. Preprocessing, exactly

The frame (`source/armc-relation/relation/src/frame.rs`; pipeline `oracle/trainer/train_lean.py` `load_C`): the raw
frame is read as 4600 x 5320, split into the four CFA planes (R, G1, G2, B), divided by 255 in float32, and area-reduced
to 96 x 112 with the trained pipeline's kernel, which accumulates each bin sequentially in float32 in row-major order and
divides by the bin height and then the bin width; the result passes through float16 (the cache), float32 and bfloat16 and
is quantised to Q12 with ties to even and clamped to int16. This path was pinned empirically: on a random full-size frame
it reproduces torch 2.11.0's output in all 43,008 positions, whereas the exact rational mean cast to float32 differs in
39,094 (`RELATION.md` section 2.1). The guest executes the same order in software floating point, which SP1's target
provides with IEEE round-to-nearest-even.

The hint (`hint.rs`): for each conditioning state the three channel seeds `BLAKE3("TB:SEED:{R,G,B}:v8" ‖ S)` are expanded
with the BLAKE3 XOF to 43,110 bytes, laid out as the four octave grids (17 x 30, 34 x 60, 68 x 120, 135 x 240), divided
by 255, area-resized to 96 x 112 with the same kernel, quantised to Q14 through the same float16 and bfloat16 casts, and
concatenated with two coordinate channels `rint(linspace(-1, 1, n) · 2^14)`: fourteen channels of int16 Q14.

The noising (`noise.rs`; `README_FINAL.md` section 3): `SA = 63540 = rint(0.9695360064506531 · 2^16)`,
`SO = 16053 = rint(0.24494898319244385 · 2^16)`, the trainer's float32 `sqrt_alphas_cum[150]` and
`sqrt_one_minus_alphas_cum[150]` on the cosine schedule; `C_t = clamp16((63540 · C_int + 16053 · noise_int + 2^15) >> 16)`;
`R = Σ(eps_int - noise_int)^2` exact in u64 (below 2^48); MSE units are `R / (43008 · 2^24)`.

## 6. The denoiser

`armc-int`, kind 1: the ARM-C architecture (`DiffusionDiagnosticUNet`) at base width 16, channel multipliers (1, 2, 4, 4),
fourteen hint channels, 1,114,500 parameters, with the timestep-150 embedding folded into the ResBlock biases, executed
in fixed point: int16 weights with per-output-channel scales, int16 activations, exact i64 accumulation, per-layer
requantisation (shift in [38, 43], 23- to 24-bit multipliers), integer GroupNorm with a floor integer square root,
65,536-entry activation tables (GELU, SiLU) with clipping masks, integer attention with an exponent table, nearest-exact
bilinear and average-pool kernels, and every value saturated to [-32768, 32767] with each saturation counted. The exact
contract (rounding rules, static bounds, tables, the saturation semantics) is `oracle/final/README_FINAL.md` section 3,
and the executed arithmetic is stated in the canonical spec JSON whose SHA-256 is public at offset 596
(`ARMC_INT_SPEC_V2`, `source/armc-relation/adapter/src/lib.rs`). The constants blob hashed at offset 564 carries every
weight, multiplier, folded bias, GroupNorm parameter, table, mask, exponent table, coordinate plane and scale entry, so
the proved function is identified by two published digests and the ELF.

## 7. The declared offset rule (which wrong row)

The rule was declared by the principal, Cathal Ryan Hynes, on 7 September 2026 (`GLOSSARY.md`; copied records that say
"owner rule" mean this rule, and the test identifiers keep that name). Verbatim, `source/armc-relation/relation/src/rule.rs`
`RULE_TEXT`:

> one proof per held-out August row r in 600..=711; base = OFFSETS[(r - 600) mod 5], OFFSETS = [-2, +2, -15, +15, +30]; offset = base when 0 <= r + base < 712 (offset_rule = direct, public byte 11 = 0), else offset = -base (offset_rule = mirrored, byte 11 = 1; rows 684, 689, 694, 699, 704, 709 at +30 mirror to -30, 698, 703, 708 at +15 to -15, 711 at +2 to -2); u = r + offset; every outcome published, negative and zero differences included

The ten mirrored rows are 684, 689, 694, 698, 699, 703, 704, 708, 709 and 711. Four rows take their wrong hint from a
training row below 600 (600 → 598, 602 → 587, 607 → 592, 612 → 597). Division of labour: the guest checks the generic
admissibility of the offset and flag together (`statement::check_offset_rule`: a direct `d` lies in the set; a mirrored
`-d` lies in the set and the direct wrong row `r - d` lies outside the session; `u = r + d` lies inside), because the
guest does not know the batch of which it is part; the exact modulo assignment anchored at row 600 is enforced by the
acceptance verifier on the public fields `r`, `u`, `d` and byte 11. Eight rows admit a coherent alternative flag under
the generic check alone (697, 702, 707, 710 flipped to mirrored; 698, 703, 708, 711 flipped to direct) and are refused by
the acceptance verifier's rule check; the negative controls record this (`RESULTS.md` section 4). The five offsets are the
frozen protocol's; cycling them by `(r - 600) mod 5` gives one proof per row with each offset on 22 or 23 rows, and mirroring
keeps the ten boundary rows in the set at the same distance in the other direction rather than dropping them. That much is
the rule's effect; no further rationale is on record (`FAQ.md` 33).

## 8. The normative noise

`oracle/final/README_FINAL.md` section 5, binding: for proof row `r` in 600 to 711 the noise tensor is
`randn_cuda_emul(seed=20260823, call_index=r-600)`: Philox4x32-10 with the Random123 and cuRAND constants (multipliers
0xD2511F53 and 0xCD9E8D57, key bumps 0x9E3779B9 and 0xBB67AE85, ten rounds), key (20260823, 0), and for element `e` in
0 to 43007 of the flattened (4, 96, 112) tensor the counter `(r - 600, 0, e, 0)`; of the four output words the sample is
the Box-Muller lane x in float32, `u = x · 2^-32 + 2^-33`, `v = y · (2^-32 · 2π) + 2^-33 · 2π`, `sample = sqrt(-2 ln u) · sin(v)`
with numpy float32 `log` and `sin`; `noise_int = rint(sample · 2^12)` with ties to even, clamped to int16. The exported
bytes are normative (`source/noise_august/noise_{r:06d}.i16`, 86,016 bytes each); their correspondence to a CUDA
generator is approximate and is not what the proof binds. The guest takes the bytes as witness item 8 and publishes their
BLAKE3 at offset 660; the acceptance verifier compares that digest with the frozen per-row table
(`source/expected_identities_august.json`, `PINS.json` `noise_files`), and the batch driver refuses to execute or prove
a row whose noise file's BLAKE3 differs from the table.

## 9. What the acceptance verifier checks

`zkdiff-verify` (`source/armc-relation/script/src/accept.rs`) accepts a statement only if every layer passes, in order:
(1) the embedded circuit verifier key's SHA-256 equals the pin; (2) `sp1_verifier::Groth16Verifier::verify` with the
pinned program vkey and the embedded circuit key; (3) layout: 752 bytes, magic, ABI, protocol, length, zero-padded
session id, timestep 150, SA 63540, SO 16053, shift 16, F_CT 12, F_HINT 14, F_EPS 12, `D = R_wrong - R_correct`,
denominator 721,554,505,728, sign byte, clip flag and count consistent, offset rule admissible, `u = r + d`; (4) program:
kind 1, constants, network-spec and preprocessing digests; (5) session: id, row count 712, tree depth 10, `S_0`, `S_N`,
authority manifest, chain-log BLAKE3, context digest, ordered-session root; (6) rule: `600 <= r <= 711` and `(d, flag, u)`
equal to `rule::august_assignment(r)`; (7) row: the normative noise BLAKE3, the chain log's raw BLAKE3, both emission
digests, both drand rounds, `leaf_r`, `leaf_u`; (8) oracle: `R_correct` and `R_wrong` equal the oracle's expected int16
residual sums for the row and its rule offset; (9) outcome class positive, zero or negative from the signed `D`,
recorded and never filtered. The verifier never derives a key from an ELF it is handed; the key is the pin.

## 10. What an outcome means

`D > 0` means the frozen integer network, run on the committed frame noised with the normative noise, predicted that
noise with a smaller squared residual under the row's own emission than under the declared wrong row's emission. The
sign is published whatever it is. A nonzero clip count marks a statement outside the zero-clipping regime covered by the
reported validation; the proof remains valid for the specified saturating computation; 65535 means at least 65535; a
count of zero covers the counted runtime sites (the noising clamp, the network clamps and the masked-table hits), not the
off-circuit input conversion, whose clip counters are recorded in the oracle manifests (all zero). Nothing here is a
statement about the physical world; `CLAIM_BOUNDARY.md` governs.

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-07 | BOSUN | First version, from RELATION.md v1.2, FULL_GUEST.md v1.2, accept.rs, rule.rs and README_FINAL.md v2.4. |
| 1.1 | 2026-09-08 | BOSUN | Minor editorial correction; no change of substance. |
| 1.2 | 2026-09-08 | BOSUN | Agent audits round 1: section 1a (shared beacon rounds, the predecessor leg, staleness, the quicknet key), the `meta` fields, the leaf and context formulas, the fractional bits, the denominator, masked-table hits, the roles behind "owner" and "coordinator". |
| 1.3 | 2026-09-08 | BOSUN | The declared offset rule named as such; the domain strings of the context and leaf digests and the byte order of the fixed noising fields stated (second reading). |
| 1.4 | 2026-09-09 | BOSUN | authorship line, 9 September 2026. |
