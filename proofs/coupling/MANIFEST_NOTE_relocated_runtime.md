> **Publication status (5 September 2026).** Historical public subset of the frozen packet. 51 of the 64 paths listed in `packet_v1/PACKET_SHA256SUMS` ship; 13 are absent. Of the 51 present paths, 29 retain their historical digest and 22 differ because of redaction or repacking. `packet_v1/` also contains 1 publication note not listed in that historical manifest. Historical manifests do not validate this publication; root `SHA256SUMS` alone controls publication bytes. This subset permits inspection of the supplied proof, but not rebuilding or full reproduction.

> **Publication note (5 September 2026).** The figures and acceptance commands below describe the unredacted 24 August freeze. They do not describe or validate this trimmed publication and will fail against it. Use the repository-root `SHA256SUMS` for publication integrity; see the publication-subset notices for omissions.

# `RUN_SHA256SUMS` exits 1, and here is why (as of 25 August; see the publication status above)

**Verified 2026-08-25 01:0xZ by BOSUN-worker.** `sha256sum -c RUN_SHA256SUMS` in this
directory returns **23 OK, 10 "FAILED open or read", 0 hash mismatches** — so it exits non-zero.

**Nothing was lost at the time of writing.** All ten paths then absent were the Groth16 **proving** runtime:

```
runtime/groth16/v6.1.0/{.complete, Groth16Verifier.sol, SP1VerifierGroth16.sol,
                        constraints.json, groth16_circuit.bin, groth16_pk.bin,
                        groth16_vk.bin, groth16_witness.json}
runtime/groth16_archive_sha256.txt
runtime/v6.1.0-groth16.tar.gz
```

All ten were located under **`packet_v1/stage/runtime/`** and re-hashed: **10 of 10 are
byte-identical to the hashes this manifest declares.** The manifest's paths are stale after a
relocation; the bytes are intact and present.

**Verification does not need any of them.** They are the *proving* runtime, not the *verifying*
inputs. All three Groth16 proofs in this release were cold-verified on a box with **no `[machine path redacted]`
directory at all** — 3 of 3 accepted, 16 of 16 negative paths correct, verifying key **derived** from
the shipped ELF rather than read from a file. So a replicator who never obtains these ten files can
still verify every proof.

**Why this note exists rather than a manifest edit.** Rewriting paths inside a frozen proof-packet
manifest changes that manifest's own hash and every reference to it. Given a replicator is not
blocked — only alarmed — the honest fix is to explain the exit code where it will be encountered.
Recorded because a non-zero exit on the **headline** proof's manifest is exactly the kind of thing
that stops someone an hour in and looks like data loss when it is a stale path.
