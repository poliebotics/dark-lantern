> **Publication status (5 September 2026).** Historical public subset of the frozen packet. 51 of the 64 paths listed in `packet_v1/PACKET_SHA256SUMS` ship; 13 are absent. Of the 51 present paths, 29 retain their historical digest and 22 differ because of redaction or repacking. `packet_v1/` also contains 1 publication note not listed in that historical manifest. Historical manifests do not validate this publication; root `SHA256SUMS` alone controls publication bytes. This subset permits inspection of the supplied proof, but not rebuilding or full reproduction.

> **Publication note (5 September 2026).** The figures and acceptance commands below describe the unredacted 24 August freeze. They do not describe or validate this trimmed publication and will fail against it. Use the repository-root `SHA256SUMS` for publication integrity; see the publication-subset notices for omissions.

# L1-1 trained-r32 coupling proof — durable packet v1

Status as written on 24 August: **complete reproducibility packet at the stated development-only
ceiling** (see the publication status above). `stage/` is a byte-for-byte regular-file copy of the frozen local
stage. `provenance/` preserves the failed first core attempt, the declared
attempt-2 wrapper and launch logs, and the success-only Groth16 chain record.

## Proven relation and proof products

The fixed guest privately consumes one 458,752-byte development architecture
tensor, computes its role-typed root, applies the exact 256-to-32 reduction,
and runs the frozen trained-r32 PTQ-v2 integer discriminator. Its 344 public
bytes bind typed root
`8ee3eefa1027cc02d955b65f06840fe624ce07077f8d52f7e9e9f4eb309043b2`,
score numerator `56835791` over denominator four, and frozen model lineage.
The execute replay measured exactly `203004795` SP1 instructions.

- Core STARK: 35,253,193 bytes, SHA-256
  `dd09c38e45560456eeaeedcf27f4eb3495800ad3cd6b1e9f8084f4f1961b3e12`;
  verified proof and exact public values; mutated public values rejected;
  wall `3:04:10`, peak RSS `44293344 KiB`, no swap, exit 0.
- Groth16: 2,038 serialized bytes / 356 on-chain proof bytes, SHA-256
  `4dcdadb1ae766b22aeeeaa62c37d607e3f9bde7fa1af0bfbcc9408a835e69079`;
  verified proof and exact public values; mutated public values rejected;
  wall `3:46:49`, peak RSS `52695024 KiB`, no swap, exit 0.

The Groth16 run is a **second complete prover request over the same pinned
guest and private input**. It is not a wrapper around, or a cryptographic
derivation from, the saved core STARK proof. Their linkage is the common guest
ELF, host/model lineage, input, typed root, score, and public journal.

## Attempt and deviation record

Core attempt 1 terminated by signal 11 after 82.80 seconds at peak RSS
`26585656 KiB`, with no swap. The frozen 512 GiB memory ceiling was nowhere
near exhausted. The available hash-pinned attempt record does not include a
cgroup `memory.events` snapshot or a core/backtrace, so it does not establish
the crash cause.

Attempt 2 used `provenance/attempt2/run_core_attempt2.sh`, SHA-256
`e97c9e3c69b3ee5c537b0788a9319ae41e708f5f02263d69933af85744398e58`,
with `RUST_MIN_STACK=33554432`. Relative to the frozen wrapper, its other
changes only resolve the stage to its absolute host path and suffix the
systemd unit with `a2`; the relation binary and guest ELF were unchanged.
Attempt 2 succeeded, but the proper conclusion is only **mitigation-associated
and consistent with worker-stack exhaustion, not a confirmed root cause**.

The first Groth16 preparation path observed an EOF while extracting an
in-flight archive, and the chain subsequently performed a clean re-fetch and
hash-verified extraction. The preserved file named
`stage/attempts/groth16_archive_partial_0128.tar.gz` now has SHA-256
`18beebb6cd0cc9b4d4a240ee4f49511da6c2a7e51724bad4232de538a9147810`,
which equals the final verified archive. It is therefore evidence of the
attempt path and filename, not a presently truncated byte object. The EOF and
successful recovery are retained in
`provenance/sequencer/groth16_chain_runner.log`.

## Claim ceiling

The Groth16 proof establishes zero-knowledge execution of the frozen relation
over the committed preprocessed bytes. It does not prove raw-source or session
membership, preprocessing correctness, capture, custody, chronology, pose,
liveness, authenticity, physical coupling, reality, adversarial robustness,
or a scientific threshold. The input is one development architecture row; no
verification-take rows were used. This packet contains reproducibility
material and is not an operational witness-confidentiality demonstration.

`PACKET_SHA256SUMS` covers every regular file in this packet except itself.
Acceptance requires both `sha256sum -c PACKET_SHA256SUMS` and exact equality
between its listed paths and the packet's regular-file set excluding the
manifest.
