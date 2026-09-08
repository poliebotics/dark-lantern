---
version: 1.3
date: 2026-09-08
status: every published hash and what it is the hash of, one line each, with the exact input bytes and where to recompute it; added after the outside-agent readability audits (AUDIT_TRAIL.md, the first reading, A1)
author: BOSUN for Cathal Ryan Hynes
---

# What every hash is a hash of

Algorithms: **SHA-256** where a file or a key is pinned for verification tooling and ledgers; **BLAKE3** (32-byte output,
the pure-Rust `blake3p` in `source/armc-relation/b3xof/`, cross-checked against the upstream crate) inside the relation,
where the recording's own digests live. `H(DOMAIN, [a, b, ...])` means BLAKE3 over the domain string followed by each part
with a 4-byte big-endian length prefix (`source/armc-relation/relation/src/membership.rs` `domain_hash`). `S_0` and `S_N`
are 32-byte chain states, not digests of a file. Values abbreviated here are complete in `PINS.json`.

## The program

| hash | of | recompute |
|---|---|---|
| program verifying key `0x00f01894…a027` | the SP1 verifying key of the guest ELF, as `SP1VerifyingKey::bytes32()`: SP1's 32-byte commitment to the program (a hash of its preprocessed data), derived from the ELF by the SDK | `source/armc-relation/build_reproducible.sh` (asserts it); `zkdiff-ceremony vkey` |
| guest ELF SHA-256 `51b7bc35…75cc` | the 396,200-byte RISC-V ELF `zkdiff-guest` the reproducible build produces | the build; `zkdiff-verify --identity` prints the digest of the ELF it embeds |
| circuit key SHA-256 `4388a21c…e696` | the 492-byte `groth16_vk.bin` of SP1's Groth16 wrapping circuit v6.1.0, embedded in `sp1-verifier` 6.4.0 as `GROTH16_VK_BYTES` | `sha256sum capsule/groth16_vk.bin`; `zkdiff-verify --identity` |
| vk root `002f850e…5352` | `sp1_verifier::VK_ROOT_BYTES`: the root of the Merkle tree of SP1 6.4.0's recursion verifying keys, a constant of that release; the Groth16 verifier requires the proof's committed root to equal it | `zkdiff-verify --identity`; the constant in the `sp1-verifier` 6.4.0 crate source |
| constants SHA-256 `73310dda…8b92` (`constants_sha256`, statement offset 564) | the 3,476,866-byte constants blob `source/blobs/final_int16/constants_int16.blob` (`ARMCINT1 v2`), hashed in circuit | `sha256sum` |
| network-spec SHA-256 `02872ec2…073b` (offset 596) | the canonical JSON string `ARMC_INT_SPEC_CANONICAL_JSON` compiled into the adapter (`source/armc-relation/adapter/src/lib.rs`), which names the arithmetic contract | `sha256sum` of that exact string; a unit test pins it |
| preprocessing-spec SHA-256 `025de070…f4a5` (offset 628) | the canonical JSON string `PREPROCESS_SPEC_CANONICAL_JSON` in `source/armc-relation/relation/src/spec.rs` | as above |
| expected identities SHA-256 `182870aa…6eb2` (published) and `6822cdce…d613` (as frozen) | the file `source/expected_identities_august.json`: the published copy, whose `sources` block carries redacted provenance paths, and the file as frozen on 7 September 2026, which every receipt and acceptance report of the batch names; the two differ in that block alone (`REDACTION.md`; `PINS.json` `program.expected_identities_sha256_frozen`) | `sha256sum` |

## The session and the chain

| hash | of | recompute |
|---|---|---|
| `S_0` `74e3a131…384c`, `S_N` `aeea9f4d…398e` | chain states: the seed the recorder chose, and the state after the 712th advance | `S_N`: walk the chain log with `advance_chain` (`source/vectors_relation/gen_vectors.py`; the relation tests) |
| chain-log BLAKE3 `754e5716…7f8b` | the 367,429-byte `source/vectors_relation/august/chain_log.csv`, whole file | `b3sum`, or the Python `blake3` module |
| chain-log SHA-256 `5d9af297…1ff48` | the same file (the ZeeBeam release pins it by SHA-256) | `sha256sum` |
| authority manifest SHA-256 `740d752d…d783` | the recorder's session manifest, a file of the ZeeBeam recording that is not published (only its digest is, in ZeeBeam and here); an input to the context digest, carried, not recomputed, by the guest | not recomputable from the package |
| context digest `f5eba65f…1ee0` | `H(ZEEBEAM_ORDERED_SESSION_CONTEXT_V1\0, [b"TB-v0.9", session_id, u32be(712), [terminal=1], S_0, S_N, manifest_sha256, chain_log_blake3])` | `membership.rs` `context_digest`; the relation tests reproduce it |
| `leaf_r`, `leaf_u` (offsets 356, 388) | `H(ZEEBEAM_ORDERED_SESSION_ROW_V1\0, [context, u32be(row), S_row, BLAKE3(raw_row), meta_row, u64be(round_row), value_row, S_{row+1}, BLAKE3(E_row)])`; `leaf_r` recomputed in circuit from the frame and the chain advance, `leaf_u` from the witnessed fields | `membership.rs` `row_leaf_hash`; every input of `leaf_u` is a chain-log column |
| tree node | `H(ZEEBEAM_ORDERED_SESSION_NODE_V1\0, [context, u16be(level), u32be(parent_index), left, right])`; padding leaf for index i in 712..1023: `H(ZEEBEAM_ORDERED_SESSION_PADDING_V1\0, [context, u32be(712), u32be(i)])` | `membership.rs` `node_hash`, `padding_leaf` |
| ordered-session root `38a484b8…6572` (offset 324) | the wrapped root `H(ZEEBEAM_ORDERED_SESSION_ROOT_V1\0, [context, u32be(712), u16be(10), internal_root])`; both leaves open to it along their sibling paths | `membership.rs` `wrapped_root_hash`; `source/vectors_relation/gen_vectors.py` builds the tree from the chain log |
| `BLAKE3(raw_r)` (offset 420) | the 24,472,000-byte raw frame of row r, hashed in circuit; equals the chain log's `bayer_blake3_hex` | `b3sum` over the published frame (`FRAMES.md`; row 600's is `capsule/reexecute/frame_000600.raw`) |
| emission digests (offsets 452, 484) | BLAKE3 over the 1,920 x 1,080 x 3 interleaved RGB bytes of the rendered pattern of row r and row u, recomputed in circuit from `S_r` and `S_u`; equal the chain log's `emission_live_pixel_blake3_hex` | `expand_and_digest` in `source/armc-relation/relation/src/emission.rs`; a unit test reproduces row 96's |
| drand value `v_t` (chain-log `drand_round_value_hex`) | SHA-256 of the round's 48-byte BLS signature (`drand_signature_hex`); checked in circuit after the signature verifies under the quicknet key | `sha256sum` of the signature bytes |
| drand leg digest (offset 532) | `BLAKE3("ZBDIFF:DRAND:v1\0" ‖ u64be(round_{r-1}) ‖ v_{r-1} ‖ u64be(round_r) ‖ v_r ‖ quicknet chain hash 52db9ba7…e971)` | `beacon.rs` `drand_leg_digest` |
| chain advance `S_{t+1}` | `BLAKE3("TB:ROW:v9" ‖ S_t ‖ u32be(32) ‖ BLAKE3(raw_t) ‖ u32be(28) ‖ meta_t ‖ u32be(8) ‖ u64be(round_t) ‖ u32be(32) ‖ v_t)` | `source/armc-relation/b3xof/src/lib.rs` `advance_chain`; all 711 advances of the chain log reproduce |

## The rows

| hash | of | recompute |
|---|---|---|
| noise BLAKE3 (offset 660; `expected_identities_august.json` `rows[r].noise_blake3`; `PINS.json` `noise_files[r].blake3`) | the 86,016 bytes of `source/noise_august/noise_{r:06d}.i16` (int16 little-endian Q12, 4 x 96 x 112), recomputed in circuit from the witness | `b3sum`; `tools/regen_noise.py` regenerates the bytes from the rule |
| noise SHA-256 (`PINS.json` `noise_files[r].sha256`) | the same file | `sha256sum`; `tools/regen_noise.py` |
| `raw_sha256` in a receipt | the raw frame's SHA-256 (a second digest of the frame beside its BLAKE3), recorded by the prover | `sha256sum` over the published frame (`FRAMES.md`) |
| framed proof SHA-256 (`proof_sha256` in receipts and manifests; `PINS.json` `batch.proofs[r].framed_sha256`) | `proofs/row_{r:06d}_groth16.bin`, the bincode-framed SP1 artifact | `sha256sum` |
| raw proof SHA-256 (`proof_raw_bytes_sha256`; `batch.proofs[r].raw_sha256`) | `proofs/row_{r:06d}_groth16_proof.bin`, the 356-byte Groth16 proof | `sha256sum` |
| public values SHA-256 (`public_values_sha256`; `batch.proofs[r].public_values_sha256`) | `public_values/row_{r:06d}_public_values.bin`, the 752-byte statement | `sha256sum` |
| `mutated_artefact_sha256` in a control record | the mutated bytes that control fed the verifier (a tampered statement, a tampered artifact, or the wrong key's `bytes32()` as ASCII) | for the record; the mutation is described beside it |

## The oracle and the model

| hash | of | recompute |
|---|---|---|
| checkpoint SHA-256 `9cf16eae…fa35` (published) and `c6955192…fab8` (as trained) | `model/g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pt`, the PyTorch checkpoint: the published file is a documented derivative of the as-trained one (three private path strings in its training arguments rewritten; every tensor, the optimizer state, the RNG states and the step verified equal, `REDACTION.md`); the evaluator record and the frozen expected identities name the as-trained digest | `sha256sum`; `PINS.json` `model` |
| `evaluator_output_sha256` `4f690865…8a09` (the published copy) and `evaluator_output_sha256_as_written` `871fa609…6496` (the private original, before its recorded paths were redacted); `pubproto_raw` SHA-256s | `model/…pubproto_eval.json` and the two per-row score files `model/pubproto_raw/pubproto_raw.npz_{d2,v10}.npz` (`PINS.json` `model.pubproto_raw` names them) | `sha256sum` |
| `oracle_g1_final.files_sha256` | every published file under `oracle/final/` (the corrected copies where `REDACTION.md` says so) | `sha256sum` |
| `oracle_g1_final.large_files_sha256_data_layer` | the `.npz` arrays of `oracle/final/`: the d2 and August vector sets and the August input arrays, on the data layer | `sha256sum` after fetching |
| array `sha256` fields inside `oracle/final/august_inputs/manifest.json` and `oracle/final/vectors/*.json` | the individual arrays (`C_int`, `noise_int`, `Ct_int`, `E_correct`, `E_wrong`, layer outputs) as raw little-endian bytes | `source/tools/export_oracle.py` checks them where the arrays are present |
| `merged_manifest_sha256` `4617085d…d95b` (the published copy) and `merged_manifest_sha256_as_recorded` `e406e998…fffb` (the node's bytes) | `receipts/BATCH_MANIFEST_merged.json`, a redacted copy (`receipts/REDACTION_LEDGER.tsv`) | `sha256sum` |
| `sha256sums_runs_sha256`, `proof_controls_sha256` (published copy) and `proof_controls_sha256_as_recorded` (the node's bytes) | `receipts/SHA256SUMS_RUNS` (the node's ledger over its complete collection, byte-identical) and `receipts/proof_controls.json` (a redacted copy) | `sha256sum` |
| `batch.merged_from[].sha256` and `sha256_published` | the eight per-GPU manifests: the digest the merge recorded on the node, and the digest of the data-layer copy `node_runs/gpuN/BATCH_MANIFEST.json` (redacted) | `sha256sum` after fetching |
| `oracle_g1_final.fixtures_sha256_repository` | the nine fixture `.npz` files under `oracle/final/fixtures/`, in this package and its `SHA256SUMS` | `sha256sum` |

## The build, the toolchain and the ledgers

| hash | of | recompute |
|---|---|---|
| lockfile SHA-256s (`reproducible_build.lockfiles`) | the four `Cargo.lock` files under `source/` | `sha256sum` |
| `source_digest_list_sha256` | the text output of `sha256sum` over every first-party source file, LC_ALL=C sorted, as `build_reproducible.sh` writes it to `runs/SOURCE_DIGESTS_<stamp>.txt`; the private lists differ from a list over the published files where `REDACTION.md` records a substitution | the driver writes a new list on every build |
| build record SHA-256s (`asserting_build_record`, `final_build_record`, `host_binaries_node_final_build_…record_sha256`) | the `build_record_<stamp>.txt` files, whole | `sha256sum` |
| host binary SHA-256s | the four host executables the driver produced on each machine (not relation-binding; the guest ELF is) | the build |
| `cargo_prove_sha256` `d8835f80…f106`, `succinct_toolchain_tarball_sha256` `12c94435…192f`, `sp1_gpu_server_sha256` `f68b85dc…d97c` | the `cargo-prove` executable, the succinct Rust toolchain tarball and the `sp1-gpu-server` executable, whole files | `sha256sum` after downloading from the sources in `VERIFY.md` section 2 |
| `groth16_circuit_files_v6_1_0` | the seven files of SP1's Groth16 v6.1.0 circuit release (`groth16_pk.bin` 5,862,173,061 bytes and the rest), whole files | `sha256sum` after downloading (`VERIFY.md` section 2) |
| `standalone_verifier.files_sha256` | the three vendored files of the ZeeBeam standalone verifier | `sha256sum`; `git show <commit>:<path>` in the ZeeBeam repository |
| `SHA256SUMS` (the ledger) | every other file in this directory; the ledger's own SHA-256 is what the Dark Lantern root `README.md` and the release records pin | `sha256sum -c SHA256SUMS`; `sha256sum SHA256SUMS` |
| `LARGE_FILES_SHA256SUMS` | the data-layer files at their package-relative paths | `sha256sum -c` after placing them |
| `capsule/SHA256SUMS`, `capsule.binaries` | every file of the offline capsule; the three static binaries | `capsule/verify_offline.sh` checks the first |
| `licence.sha256` | the `LICENSE` file, byte-identical to the Dark Lantern repository's root `LICENSE` | `sha256sum` |
| `redaction.sha256`, `REDACTION_LEDGER.tsv` | the ledger of every published file under `source/`, `oracle/` and `model/` whose bytes differ from the private original, with both digests (`receipts/REDACTION_LEDGER.tsv` does the same for the receipts) | `sha256sum` |
| `build_kit.kit_manifest_sha256` | `build_kit/KIT_MANIFEST.json` on the data layer, which lists every file of the offline build kit with its SHA-256 except itself and `BUILD_KIT.md`, both covered by the bundle's `_control/MANIFEST.jsonl` (`LARGE_FILES.md`) | `sha256sum` after fetching |
| `MODES` | the list of executable files of the package (every other file is mode 0644); listed in `SHA256SUMS` and applied by the repository commit | `find -perm /111` against the list |

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-08 | BOSUN | First version, after the outside-agent readability audits (the first reading, A1). |
| 1.1 | 2026-09-08 | BOSUN | The published frames replace the held wording; the expected identities and the checkpoint carry both digests; the redaction ledger, the build kit manifest and MODES added. |
| 1.2 | 2026-09-08 | BOSUN | Astra round 9: published and as-recorded digests told apart for the merged manifest, the proof controls, the per-GPU manifests, the evaluator output and the build records; the fixtures' location. |
| 1.3 | 2026-09-08 | BOSUN | Astra round 10: three static binaries; the kit manifest's two exclusions stated. |
