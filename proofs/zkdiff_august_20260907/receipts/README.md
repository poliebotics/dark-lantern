# receipts/: the proof batch's evidence, and what stayed on-box

Every file here is copied from the node's proof collection or from the development machine's acceptance run under the
evidence allowlist of the release tooling (`tools_release/evidence_allowlist.py` in the staging repository; its rules are
reproduced in the tables that follow). The rule is positive: a file kind enters this directory only if it is listed, and the whole collection
must be classified as included or withheld before anything is copied. `SHA256SUMS_RUNS` is the node's own ledger over its
collection as it stood at the `merge` step (13:41Z on 8 September), withheld files included, so the digests of the withheld
originals are on record here; the section Using SHA256SUMS_RUNS states its coverage. The published text records (receipts,
ceremony manifests, acceptance reports, per-GPU manifests, launch records) pass through the publication redaction rule
(`REDACTION.md`): the node's paths read as package locators (`node_runs/...` for the collection as published on the data
layer, `source/...` for the mirrored source tree, `[frames directory]` for the frames' location on the node) and its hostname
reads `prover-node`, in the attempt identifiers too; nothing else changes, and the release tooling re-parses every JSON
record to check that only path-like strings moved. `REDACTION_LEDGER.tsv` in this directory lists each redacted copy with
the digest of the node's original (the value `SHA256SUMS_RUNS` carries) and of the published bytes.

## Included

| collection path | published here as | what |
|---|---|---|
| `gpuN/row_XXXXXX/row_XXXXXX_groth16.bin` | `../proofs/row_XXXXXX_groth16.bin` | framed SP1 Groth16 artifact |
| `gpuN/row_XXXXXX/row_XXXXXX_proof_bytes.bin` | `../proofs/row_XXXXXX_groth16_proof.bin` | raw Groth16 proof, 356 bytes |
| `gpuN/row_XXXXXX/row_XXXXXX_public_values.bin, .hex` | `../public_values/` | the 752-byte statement |
| `gpuN/row_XXXXXX/receipt.json` | `row_XXXXXX_receipt.json` | the prover's row receipt |
| `gpuN/row_XXXXXX/manifest.json` | `row_XXXXXX_manifest.json` | the ceremony manifest |
| `gpuN/row_XXXXXX/row_XXXXXX_groth16.verify.json` | `row_XXXXXX_verify.json` | the node's cold acceptance report |
| `BATCH_MANIFEST.json` | `BATCH_MANIFEST_merged.json` | the strict merge of the eight manifests (zbdiff-batch/v3-merged) |
| `SHA256SUMS_RUNS` | `SHA256SUMS_RUNS` | the node's ledger over the complete collection, withheld files included |
| `controls_600/CONTROLS.json` | `controls_600_CONTROLS.json` | witness-level and proof-level controls report |
| `execute_684/BATCH_MANIFEST.json` | `execute_684_BATCH_MANIFEST.json` | the node's complete-guest execution of the mirrored row 684 (manifest) |
| `execute_684/row_000684/public_values.bin` | `execute_684_row_000684_public_values.bin` | row 684's execute receipt and public bytes |
| `execute_684/row_000684/public_values.hex` | `execute_684_row_000684_public_values.hex` | row 684's execute receipt and public bytes |
| `execute_684/row_000684/receipt.json` | `execute_684_row_000684_receipt.json` | row 684's execute receipt and public bytes |
| `gpu0/BATCH_MANIFEST.json` | `gpu0_BATCH_MANIFEST.json` | per-process batch manifest (zbdiff-batch/v3) |
| `gpu0/gpu_identity.csv` | `gpu0_gpu_identity.csv` | the GPU's index, UUID, name, driver and bus id at launch |
| `gpu0/gpu_mem.csv` | `gpu0_gpu_mem.csv` | nvidia-smi 30 s samples of the GPU: memory, utilisation, power, temperature |
| `gpu0/inputs_identity_launch.txt` | `gpu0_inputs_identity_launch.txt` | SHA-256 of the binary, ELF, blob, chain log, expected identities and build record at launch |
| `gpu1/BATCH_MANIFEST.json` | `gpu1_BATCH_MANIFEST.json` | per-process batch manifest (zbdiff-batch/v3) |
| `gpu1/gpu_identity.csv` | `gpu1_gpu_identity.csv` | the GPU's index, UUID, name, driver and bus id at launch |
| `gpu1/gpu_mem.csv` | `gpu1_gpu_mem.csv` | nvidia-smi 30 s samples of the GPU: memory, utilisation, power, temperature |
| `gpu1/inputs_identity_launch.txt` | `gpu1_inputs_identity_launch.txt` | SHA-256 of the binary, ELF, blob, chain log, expected identities and build record at launch |
| `gpu2/BATCH_MANIFEST.json` | `gpu2_BATCH_MANIFEST.json` | per-process batch manifest (zbdiff-batch/v3) |
| `gpu2/gpu_identity.csv` | `gpu2_gpu_identity.csv` | the GPU's index, UUID, name, driver and bus id at launch |
| `gpu2/gpu_mem.csv` | `gpu2_gpu_mem.csv` | nvidia-smi 30 s samples of the GPU: memory, utilisation, power, temperature |
| `gpu2/inputs_identity_launch.txt` | `gpu2_inputs_identity_launch.txt` | SHA-256 of the binary, ELF, blob, chain log, expected identities and build record at launch |
| `gpu3/BATCH_MANIFEST.json` | `gpu3_BATCH_MANIFEST.json` | per-process batch manifest (zbdiff-batch/v3) |
| `gpu3/gpu_identity.csv` | `gpu3_gpu_identity.csv` | the GPU's index, UUID, name, driver and bus id at launch |
| `gpu3/gpu_mem.csv` | `gpu3_gpu_mem.csv` | nvidia-smi 30 s samples of the GPU: memory, utilisation, power, temperature |
| `gpu3/inputs_identity_launch.txt` | `gpu3_inputs_identity_launch.txt` | SHA-256 of the binary, ELF, blob, chain log, expected identities and build record at launch |
| `gpu4/BATCH_MANIFEST.json` | `gpu4_BATCH_MANIFEST.json` | per-process batch manifest (zbdiff-batch/v3) |
| `gpu4/gpu_identity.csv` | `gpu4_gpu_identity.csv` | the GPU's index, UUID, name, driver and bus id at launch |
| `gpu4/gpu_mem.csv` | `gpu4_gpu_mem.csv` | nvidia-smi 30 s samples of the GPU: memory, utilisation, power, temperature |
| `gpu4/inputs_identity_launch.txt` | `gpu4_inputs_identity_launch.txt` | SHA-256 of the binary, ELF, blob, chain log, expected identities and build record at launch |
| `gpu5/BATCH_MANIFEST.json` | `gpu5_BATCH_MANIFEST.json` | per-process batch manifest (zbdiff-batch/v3) |
| `gpu5/gpu_identity.csv` | `gpu5_gpu_identity.csv` | the GPU's index, UUID, name, driver and bus id at launch |
| `gpu5/gpu_mem.csv` | `gpu5_gpu_mem.csv` | nvidia-smi 30 s samples of the GPU: memory, utilisation, power, temperature |
| `gpu5/inputs_identity_launch.txt` | `gpu5_inputs_identity_launch.txt` | SHA-256 of the binary, ELF, blob, chain log, expected identities and build record at launch |
| `gpu6/BATCH_MANIFEST.json` | `gpu6_BATCH_MANIFEST.json` | per-process batch manifest (zbdiff-batch/v3) |
| `gpu6/gpu_identity.csv` | `gpu6_gpu_identity.csv` | the GPU's index, UUID, name, driver and bus id at launch |
| `gpu6/gpu_mem.csv` | `gpu6_gpu_mem.csv` | nvidia-smi 30 s samples of the GPU: memory, utilisation, power, temperature |
| `gpu6/inputs_identity_launch.txt` | `gpu6_inputs_identity_launch.txt` | SHA-256 of the binary, ELF, blob, chain log, expected identities and build record at launch |
| `gpu7/BATCH_MANIFEST.json` | `gpu7_BATCH_MANIFEST.json` | per-process batch manifest (zbdiff-batch/v3) |
| `gpu7/gpu_identity.csv` | `gpu7_gpu_identity.csv` | the GPU's index, UUID, name, driver and bus id at launch |
| `gpu7/gpu_mem.csv` | `gpu7_gpu_mem.csv` | nvidia-smi 30 s samples of the GPU: memory, utilisation, power, temperature |
| `gpu7/inputs_identity_launch.txt` | `gpu7_inputs_identity_launch.txt` | SHA-256 of the binary, ELF, blob, chain log, expected identities and build record at launch |
| `gpus_at_launch.csv` | `gpus_at_launch.csv` | the eight GPUs before the first launch |
| `launch_schedule.txt` | `launch_schedule.txt` | the launch schedule: one prover per GPU, 90 s apart |
| `proof_controls.json` | `proof_controls.json` | proof-level negative controls on row 600's proof |
| (development machine) `row_XXXXXX.verify.json`, `summary.txt` | `independent_verify/` | the development machine's cold acceptance of every proof, 112 accepted, each report's `artifact_sha256` equal to the proof's |

`BATCH_SUMMARY.json` is rendered by the filler from the merged manifest and the receipts. The data-layer companion carries the
same allowlisted files at their collection paths under `node_runs/`, plus the bulkier resource samples (`gpu_procs.csv`,
`host_rss.csv`, `gpus_all.csv`).

## Withheld (on-box, pinned by `SHA256SUMS_RUNS`)

| pattern | files | why |
|---|---:|---|
| `(^|/)host_procs\.log$` | 8 | process listings of the node (sidecar) |
| `(^|/)launch_times\.txt$` | 8 | per-GPU launcher log (exit codes of the prover pipeline; the launch schedule is published instead) |
| `(^|/)nvidia_smi_sidecar\.pid$` | 8 | a process id |
| `(^|/)prove\.stderr$` | 8 | prover stderr: the client's exit diagnostics (a nonzero status during cleanup after the final manifest and receipts were written; infrastructure diagnostics, not evidence about the proofs) |
| `(^|/)prove\.stdout$` | 8 | prover progress log; every fact it carries is in the manifests and receipts |
| `(^|/)row_\d{6}_groth16\.verify\.(stdout|stderr)$` | 224 | the acceptance report's stdout duplicate and empty stderr |
| `(^|/)rss_sidecar\.log$` | 8 | sidecar start and stop lines |
| `(^|/)witness/` | 1017 | witness inputs: the normative noise is source/noise_august/, the chain material is the chain log |
| `^controls_600/stdout\.log$` | 1 | controls run log; CONTROLS.json is the record |
| `^execute_684/(stdout|stderr)\.log$` | 2 | execute run logs; the manifest and receipt are the record |
| `^host_sys\.log$` | 1 | system load and disk samples of the node (sidecar) |
| `^launch_gpu\d\.log$` | 8 | per-GPU launcher log, duplicate of launch_times.txt |
| `^sys_sidecar\.out$` | 1 | empty sidecar output |
| `^tmp_state\.log$` | 1 | listings of the node's /tmp |

Each prover client returned a nonzero status during cleanup after writing its final manifest (the manifests say
`finished: true, complete: true`; every proof had already been accepted cold and is accepted again here and on the
development machine). The stderr files that carry the exit diagnostics are infrastructure diagnostics, not evidence about
the proofs, and stay on-box with the other logs, pinned by digest in `SHA256SUMS_RUNS`.

## Using `SHA256SUMS_RUNS`

It is the node's `sha256sum` ledger over its collection, paths relative to the collection root (`./gpu0/row_000600/receipt.json`
and so on), written by the runbook's `merge` step over the files matching `*.bin`, `*.json`, `*.hex`, `*.log`, `*.csv` and
`prove.*` at that moment. Two uses. First, every published file the ledger lists was checked against it by the release tooling
before it was copied: 815 files (per row the framed proof, the raw proof, the statement in both forms, the receipt, the
ceremony manifest and the node's acceptance report; the merge, the proof-level controls, the per-GPU manifests and memory samples)
equal their ledger entries, so what is here is what the node wrote and, for the text records, the redaction of it recorded in
`REDACTION_LEDGER.tsv` (the binary proof and statement files are byte-identical). 10 published files are not in
the ledger and are pinned by the package `SHA256SUMS` instead: `controls_600/CONTROLS.json` and row 684's execution record were
written after the ledger (the `controls` step followed `merge` by twenty seconds), and the launch schedule, the launch-time input
digests, the GPU identity CSVs and the GPUs-at-launch CSV lie outside the ledger's file pattern (controls_600/CONTROLS.json, gpu0/inputs_identity_launch.txt, gpu1/inputs_identity_launch.txt, gpu2/inputs_identity_launch.txt, gpu3/inputs_identity_launch.txt, gpu4/inputs_identity_launch.txt, …). To repeat the check for one row by hand,
hash the published file and look its collection path up in the ledger: `sha256sum receipts/row_000600_receipt.json` against the
line ending `gpu0/row_000600/receipt.json`. Second, 1061 of the withheld files are pinned by digest in it (the other
242 withheld files, the acceptance reports' stdout and stderr duplicates, the launcher logs, the sidecar pid files
and the like, lie outside its pattern), so if a pinned one is published later (the evidence allowlist is the release tooling's
`evidence_allowlist.py`) it can be checked against the ledger that was published first; until then their digests are a
commitment, not something a reader can inspect.

## Reading a receipt (`row_XXXXXX_receipt.json`, schema `zbdiff-row-receipt/v3`)

- `sp1_version`: the artifact's circuit-version string, `v6.1.0`, which the SP1 6.4.0 SDK writes into every Groth16 artifact
  (`source/armc-relation/script/src/verify.rs`); it names the Groth16 circuit release, and `sp1_circuit_version` repeats it. The
  SDK, prover and verifier crates are release 6.4.0 (`PINS.json` `program.sp1_version`); the two numbers describe different things.
- `acceptance.checks`: the ordered layers of `zkdiff-verify` (`STATEMENT.md` section 9), each PASS with its detail. The
  `groth16.verify` detail names the program vkey and the `vk root` `002f850e…5352`: `sp1_verifier::VK_ROOT_BYTES`, the root of
  SP1 6.4.0's recursion-key Merkle tree, a constant of the verifier crate that the proof's committed root must equal (`PINS.json`
  `program.vk_root_note`).
- `verification.sdk_tamper_controls`: three mutations checked by the prover with the SDK at proving time: `sdk.public_byte_716`
  flips one byte of `R_correct`; `sdk.proof_nibble_96` flips one hex nibble inside the Groth16 proof; `sdk.wrong_vkey` verifies
  under a wrong program key, made by rotating the verifying key's preprocessed commitment by one element
  (`ceremony_core.rs` `verify_original_and_tamper`), whose hash `0x007fb8c7…` is printed. All three must be rejected.
- `decoded`: the statement's fields as the prover decoded them, equal to `tools/decode_zbdiff01.py` on the published statement.
- `command`, `frame`, `noise`, `expected_identities.path`, `build_record.path`, `proof_file`: the paths the prover ran with, redacted
  to package locators (`node_runs/...` is the collection root as published on the data layer, `source/...` the mirrored source
  tree, `[frames directory]` the node's frames directory); they are provenance and resolve nowhere in this package. `binary_sha256` is
  the prover binary's digest (`PINS.json` `reproducible_build.host_binaries_node_final_build_20260907T215855Z`) and
  `build_record.sha256` the digest of `../source/node_prep/r5/build_record_20260907T215855Z.txt`.
- `oracle_mode: native_reexecution`: the host re-ran the same `evaluate` natively and compared the 752 bytes with the guest's.
- `attempt_id`, `attempts`: the run's identifier (timestamp, host label, process id; the host label reads `prover-node` in the published
  copies) and any retained earlier attempts on the row (none in this batch). `host` likewise reads `prover-node`.
- `outcome_class`: positive, zero or negative from the signed `D`; nothing is filtered by class.
