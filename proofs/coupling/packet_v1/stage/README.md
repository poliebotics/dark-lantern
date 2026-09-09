---
version: 1.1
updated: 2026-09-09
status: historical-frozen-stage; publication-subset-not-runnable
author: Cathal Ryan Hynes (author of record); drafted with BOSUN, the project's automated research assistant
---

> **Publication note (5 September 2026).** The figures and acceptance commands below describe the unredacted 24 August freeze. They do not describe or validate this trimmed publication and will fail against it. Use the repository-root `SHA256SUMS` for publication integrity; see the publication-subset notices for omissions.

# BOSUN-worker trained-r32 joined-proof stage

This self-contained stage is the exact handoff for proving the already executed
trained-r32 discriminator relation on BOSUN's externally operated high-memory
BOSUN-worker host. Codex prepared and tested the bytes locally and does not operate
the provider machine.

The guest privately consumes one 458,752-byte development architecture tensor,
computes its typed root, performs the exact 256-to-32 reduction and frozen
integer discriminator, and publicly commits 344 bytes binding the root, score
and model lineage. The guest ELF SHA-256 is
`8a275c57b7b6d1db14103af0b530bb594ac772983937065bf3172d25b52234b6`.
The local zk-wrap host replayed the exact root, numerator and 203,004,795
instructions before staging.

The host binary is a convenience executable, not the canonical relation
identifier. Native host builds can differ while embedding the same guest. The
proof and verifying key bind the guest ELF.

## Exact operator command

After copying this directory byte-for-byte to BOSUN-worker, from its root run:

```sh
sha256sum -c SHA256SUMS
./run_frozen_proof_stage.sh all
```

The one command performs a host/cgroup/disk preflight, exact execute replay,
core STARK proof, safely extracts and verifies the pinned SP1 v6.1.0 Groth16
circuit files, reruns the joined relation for a Groth16 proof, verifies both
proofs and a public-value mutation rejection, then writes `RUN_SHA256SUMS`
last. Core and Groth16 are separate full prover requests; the latter cannot
wrap the saved core proof through this SP1 SDK surface.

The core job has a 512 GiB cgroup ceiling, no swap and a four-hour timeout.
Groth16 has a 1,200 GiB ceiling, no swap and a twelve-hour timeout. Both use
224 Rayon threads and one-worker/one-buffer SP1 queues. A timeout, OOM, missing
proof, failed verification or hash mismatch is an attempt record, not a proof
receipt. No undocumented SP1 knobs are used. `SHARD_SIZE` is deliberately
unset because it is only record preallocation in SP1 6.4.0, not the actual
split boundary.

The Groth16 circuit archive is fetched from the exact release URL named in the
pinned SP1 6.4.0 source. The archive itself is treated as untrusted: the stage
extracts only seven required regular files and requires their locally measured
SHA-256 values before the prover sees them.

## Return packet

Return the complete `results/`, `receipts/`, `runtime/groth16_archive_sha256.txt`,
`RUN_SHA256SUMS` and a strict receipt matching `RECEIPT_SCHEMA.json`. Include
the exact commands, environment, host facts, `/usr/bin/time -v` records, proof
sizes and hashes, circuit verification, and the final run-manifest hash.

## Claim ceiling

A successful core proof establishes the joined hidden-tensor-to-typed-root and
exact frozen-score relation. A successful Groth16 result establishes that same
relation in zero knowledge. Neither proves capture, chronology, liveness,
physical pose, reality or a scientific threshold. The embedded input is a
development architecture row; the sealed 288-row verification take is not
present or opened. No chain action or timestamp is part of this stage.

## Log

- 1.1 (2026-09-09, BOSUN) — authorship line, 9 September 2026.
