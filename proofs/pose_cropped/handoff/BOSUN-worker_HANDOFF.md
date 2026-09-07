---
version: 1.0
updated: 2026-08-24
status: historical-source-handoff-record; source-model-and-fixture-absent-from-publication
author: BOSUN
---

# BOSUN-worker source handoff for the joined pose proof

This publication retains only the historical handoff description, receipt schema and digest list. The Rust source, locked dependencies, frozen blob, fixture, scripts and guest ELF described below are absent; this subset is not rebuildable.

The relation takes a private preprocessed camera tensor
`uint8[4,256,256]` and sixteen private emission leaf hashes. It recomputes the
camera leaves in the existing typed camera-plus-emission tree, checks their
membership by producing the public typed pair root, performs the exact 8-by-8
ties-to-even reduction, and runs the frozen pose model. It commits 490 public
bytes containing the typed context, typed pair root, eleven integer logits,
the first-maximum verdict, saturation count, logit scale, and exact model and
reduction bindings.

The frozen development vector is row 52. Its public typed pair root is
`efd35d054df639c3b07acff6ebab5d2ebec59a85ed0dcde5c0e99aa95006d395`.
The integer logits are
`8403,8677,184,-1435,6346,-4488,-1564,2047,2253,413,583`, the verdict is
class 1, and its saturation count is zero. The true-class value 0 is a
development diagnostic outside the proof relation.

## Proven locally before handoff

Native Rust matches all 1,276 Python integer logits and all 116 Python
verdicts. Seven model, native, and relation tests pass. Two host contract tests
pass. The SP1 guest executes the joined relation in 16,611,240 instructions
with zero syscalls, returns all 490 expected public bytes, and rejects changed
public bytes in the host contract.

The local Groth16 attempt did not finish. It began at 2026-08-23 21:55:56 UTC
under a 70 GiB cgroup cap with proof swap disabled. The last guard observation
showed a 37,200,207,872-byte cgroup peak lower bound, 73,902,180 KiB host memory
available, and zero proof-cgroup swap. The host then rebooted. The cause of the
reboot is not established. No completion record or proof file exists, so no
cryptographic or zero-knowledge proof is claimed locally.

## BOSUN-worker command

BOSUN-worker must have SP1 crates 6.4.0, cargo-prove
`f66b4bf 2026-08-12T14:40:11.709680161Z`, and local Groth16 circuit material
installed before this source handoff runs. It must not overlap another
high-memory proof. The remote guest build must reproduce the 236,760-byte ELF
with SHA-256
`9c5f53522c588024c3c20068f49958e31fa0192d7647e9443f75dc25e8487525`
or the runner stops before proving. From the copied handoff root, run exactly:

```sh
chmod 755 tools/run_bosun-worker_groth16_bounded.sh
tools/run_bosun-worker_groth16_bounded.sh "$PWD"
```

The runner first verifies `BOSUN-worker_SOURCE_SHA256SUMS`, refuses an existing
proof path, requires at least 85 GiB `MemAvailable`, builds from `Cargo.lock`,
and reruns all local tests. It then starts one direct Groth16 proof under these
hard bounds:

- `MemoryMax=70G`, exactly 75,161,927,680 bytes;
- `MemorySwapMax=0`;
- `RuntimeMaxSec=5400`, with an independent 5,400-second timeout;
- eight Rayon threads;
- two trace chunk slots;
- one worker and one buffer at each enumerated SP1 pipeline stage;
- a guard that stops the unit below 15 GiB host `MemAvailable` or on any proof
  cgroup swap use.

The host binary verifies the proof, compares all public bytes, and requires the
verifier to reject a one-bit public-value change before it saves
`results/pose_join_groth16.proof.bin`. A nonempty file alone is not success.
Success requires a receipt matching `BOSUN-worker_RECEIPT_SCHEMA.json` with all six
checks true. `BOSUN-worker_SOURCE_SHA256SUMS` binds the files that may travel.

## Claim ceiling

A verified proof establishes knowledge of private, already-preprocessed camera
pixels and emission leaf hashes consistent with the public typed pair root,
plus the exact frozen model's logits and verdict over those camera pixels. It
does not establish raw sensor origin, preprocessing correctness, row or session
membership, capture time, chronology, physical pose ground truth, or liveness.
The model verdict is evidence about committed pixels, not proof of physical
reality.

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-24 | BOSUN | Froze the joined pose source handoff, bounded Groth16 runner, receipt contract, and honest local interruption record. |
