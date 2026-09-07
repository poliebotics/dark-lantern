> **Publication note (5 September 2026).** The figures and acceptance commands below describe the unredacted 24 August freeze. They do not describe or validate this trimmed publication and will fail against it. Use the repository-root `SHA256SUMS` for publication integrity; see the publication-subset notices for omissions.

# L1-1 coupling proof — receipt narrative

Written 2026-08-24T15:11Z by the BOSUN-worker post (BOSUN face, receipt worker), [internal name redacted] BOSUN,
on the Lambda 8xA100 host that ran the proof. Status: **final receipt narrative for the
completed and frozen L1-1 coupling proof stage of 2026-08-23/24.**

Every hash, byte count, wall time and log line quoted below was recomputed or re-read
directly from the bytes on disk on 2026-08-24 (14:45–15:11 UTC), not copied from any
earlier report. Where a statement rests on a desk record rather than on frozen bytes,
that is said explicitly. One correction to the working story is flagged in section 5.

Locations:

- Local frozen stage: `<box path redacted>`
- Durable NFS packet root: `[machine path redacted]`
- Canonical durable artifact: `[machine path redacted]`
  (sealed 2026-08-24T05:36Z; re-verified 64/64 with exact path contract while writing
  this narrative)

---

## 1. What was proved — and the claim ceiling

A zero-knowledge proof (SP1 Groth16, bn254) now attests the following relation, and only
the following relation:

> A hidden, committed 458,752-byte preprocessed camera-plus-emission tensor
> ("frozen development architecture position 0"), when consumed by the frozen guest
> program (guest ELF SHA-256 `8a275c57b7b6d1db14103af0b530bb594ac772983937065bf3172d25b52234b6`),
> yields role-typed root
> `8ee3eefa1027cc02d955b65f06840fe624ce07077f8d52f7e9e9f4eb309043b2`
> and the exact integer score **56835791/4** from the frozen trained-r32 PTQ-v2 integer
> discriminator, committed in 344 public bytes binding root, score and model lineage.

**Claim ceiling — do not exceed it.** The proof does NOT establish:
raw-file or session membership; preprocessing correctness; physical capture or custody;
chronology; pose; liveness; authenticity, physical coupling, or reality; adversarial
robustness; or any scientific threshold. The private input is one development-architecture
row. No verification-take rows were used or present on this host
(`PACKET_SCOPE.json: "verification_rows_accessed": false`). The witness blob commitment
observed in every stage log is `blob_sha256=0188b5c0f4ea08e81940aef1a8cb303c00b24e7f8b7730a64bf5080d4030353a`.

The Groth16 run was a **separate, second full prover request** over the same pinned guest
and private input. It is not a recursive wrap of, nor a cryptographic derivation from, the
saved core STARK proof; their linkage is the common guest ELF, input, typed root, score and
public journal (peer-review wording, Sol, desk 2026-08-24 05:32/05:58 UTC; command lines
in `results/*/time.txt` confirm independent `--mode core` and `--mode groth16` invocations).

## 2. Artifacts, all hashes recomputed 2026-08-24

Stage integrity:

| item | value (recomputed) |
|---|---|
| stage manifest `SHA256SUMS` self-hash | `50259940280c85c7ff5f947301c5d5d5c3f04cf83bb3cb38c21ce787dce15791` (11 entries, 11/11 verify) |
| frozen run manifest `RUN_SHA256SUMS` self-hash | `e6e6aabca413388869ba87390ed586eae9f17eb0b18b2923f7a7af8b5a2e63ab` (33 entries, 33/33 verify against local bytes) |
| receipts cross-check | `receipts/stage_manifest_sha256.txt` records the same `50259940…` value |

Proof products:

| artifact | bytes | SHA-256 (recomputed) |
|---|---:|---|
| `results/core/trained_r32_core.proof.bin` | 35,253,193 | `dd09c38e45560456eeaeedcf27f4eb3495800ad3cd6b1e9f8084f4f1961b3e12` |
| `results/groth16/trained_r32_groth16.proof.bin` | 2,038 (356 on-chain proof bytes) | `4dcdadb1ae766b22aeeeaa62c37d607e3f9bde7fa1af0bfbcc9408a835e69079` |

Both proof files are byte-identical in the local stage, the NFS packet root `results/`,
and `packet_v1/stage/results/` (hashes recomputed at all three).

Stage results, from the frozen logs and `/usr/bin/time -v` receipts:

- **Execute replay** (`results/execute/`): exact. `total_instruction_count=203004795`,
  `typed_root=8ee3eefa…`, `score_numerator=56835791`, `score_denominator=4`,
  `public_values_bytes=344`, `verified_public_values=true`, `proof_generated=false`.
  Wall 0:37.23, exit 0.
- **Core STARK** (`results/core/`): wall **3:04:10**, peak RSS **44,293,344 kB (~44.3 GB)**
  against a systemd cgroup cap of `MemoryMax=512G` with `MemorySwapMax=0` (512 GiB, no
  swap; `Swaps: 0` in the time receipt), 23 core shards, exit 0.
- **Groth16** (`results/groth16/`): wall **3:46:49**, peak RSS **52,695,024 kB (~52.7 GB)**
  against `MemoryMax=1200G` with `MemorySwapMax=0` (`Swaps: 0`), exit 0. In-run verifier
  time 0.445 s.

Verification and negative-control lines, quoted verbatim from the frozen stdout logs
(ANSI codes stripped from the timestamped line):

`results/core/stdout.log`:

```
2026-08-24T01:25:18.970711Z ERROR committed value digest doesnt match
mode=core_stark_proof
verified_public_values=true
verified_proof=true
tampered_public_values_rejected_by_verifier=true
proof_file_bytes=35253193
```

`results/groth16/stdout.log`:

```
mode=groth16_zk_snark
onchain_proof_bytes=356
verified_public_values=true
verified_proof=true
tampered_public_values_rejected_by_verifier=true
proof_file_bytes=2038
```

Note for the stranger: the single `ERROR committed value digest doesnt match` line in the
core log is the **deliberate negative control succeeding** — the host mutates the public
values and confirms the verifier rejects them; the rejection is then reported as
`tampered_public_values_rejected_by_verifier=true`. It is not a fault.

Timestamps (from `receipts/` and the chain log): stage preflight/start
2026-08-23T22:17:28Z; core attempt 2 verified 01:25Z; Groth16 launched 01:27:32Z;
Groth16 verified 05:17–05:20Z; receipts completed 2026-08-24T05:21:50Z; freeze
(`RUN_SHA256SUMS` written and self-checked) logged 05:22:14Z. Host binary
`zeebeam-trained-r32-ptq-v2-script 0.1.0`; SP1 SDK 6.4.0, circuit v6.1.0
(pins in `PROOF_STAGE.json`, itself covered by the verified `SHA256SUMS`).

## 3. Incident 1 — core attempt 1 SIGSEGV, and the one declared deviation

The first core STARK attempt, run from the frozen wrapper `run_frozen_proof_stage.sh`
(no `RUST_MIN_STACK` in its environment), died early. From the preserved record
`attempts/core_attempt1_sigsegv/time.txt` (bytes re-read today):

- `Command terminated by signal 11` (SIGSEGV)
- wall **1:22.80** (82.8 s into proving)
- peak RSS **26,585,656 kB (~26.6 GB)** — nowhere near the 512 GiB cap; `Swaps: 0`
- `stderr.log` is empty; `stdout.log` ends immediately after the cycle-span accounting,
  i.e. during shard proving. No proof file was produced.

Live observations recorded at the time (desk, BOSUN-worker/Sol adversarial review,
2026-08-23 22:40 UTC) but **not present in the frozen byte record**: zero cgroup OOM/max
events, no kernel OOM or segfault record, and no core file because `RLIMIT_CORE=0`. The
sealed packet is explicit that the hash-pinned attempt record contains no
`memory.events` snapshot or backtrace, **so the crash cause is not established by
preserved evidence.**

Attempt 2 was launched from a copied wrapper, preserved at
`run_core_attempt2.sh` (NFS root and `packet_v1/provenance/attempt2/`, both recomputed
today to SHA-256 `e97c9e3c69b3ee5c537b0788a9319ae41e708f5f02263d69933af85744398e58`),
with exactly **one declared environment deviation**:

```
RUST_MIN_STACK=33554432   (32 MiB worker stacks)
```

Its only other differences from the frozen wrapper are the absolute stage path and an
`-a2` suffix on the systemd unit names; binary, guest ELF, caps and check gauntlet are
unchanged. Peer review (Sol, desk 2026-08-23 22:40 UTC) inspected the live process and
counted **471 exact 32 MiB RW worker-stack mappings** (475 threads, 467 named
`tokio-rt-worker`), confirming the setting took effect and was not overridden by
Rayon/SP1 in this binary.

Attempt 2 passed every frozen check. **Required interpretation, adopted from the
adversarial review and not to be strengthened:** the success is
**mitigation-associated, consistent with worker-stack exhaustion** — it is **not** a
confirmed root cause. If the failure ever recurs, the standing guidance is to enable
core capture/backtrace and reduce `RAYON_NUM_THREADS` before increasing stacks again.

## 4. Incident 3 (taken next for chronology) — the automated success-only chain

After attempt 2 was launched by hand, the remainder of the stage ran unattended as a
cron-driven, flock- and marker-guarded, success-only chain
(`packet_v1/provenance/sequencer/groth16_chain.sh`, with its `groth16_chain.log`,
runner log, and the `groth16_launched` / `freeze_done` sentinels preserved):

1. **Core success sentinel:** `results/core/proof_sha256.txt`, written by the wrapper only
   after the full gauntlet (proof non-empty, typed root, exact score, self-verify, tamper
   rejection) passed. A stage ending without its sentinel would halt the chain with no
   retry.
2. **Groth16 launch, memory-gated:** the chain refused to fire below
   `MemAvailable` of 1,468,006,400 KiB (**1400 GiB**), so the frozen 1200G wrap cap could
   never squeeze the concurrently training uncapped ARM-A trainer. The chain log shows no
   deferral ticks: the gate passed on first evaluation and Groth16 launched at
   2026-08-24T01:27:32Z.
3. **Freeze:** after the Groth16 sentinel appeared, the chain ran the wrapper's `freeze`
   step exactly once: `RUN_SHA256SUMS` written last, then self-checked
   (`freeze complete; RUN_SHA256SUMS sha256 e6e6aabc…` at 05:22:14Z).

To repeat the structural point: the chain's Groth16 step ran the wrapper's `groth16`
mode — **a separate full Groth16 proving run over the same relation and input — not a
recursive wrap of the already-saved core proof.**

## 5. Incident 2 — Groth16 circuit-archive EOF, with a correction to the working story

What the preserved bytes show (all recomputed/re-read today):

- The first preparation path's log (`packet_v1/provenance/sequencer/groth16_chain_runner.log`)
  records a pinned fetch of `v6.1.0-groth16.tar.gz` whose curl progress ran ~2:01 and
  ended at 100% of 5924M, followed by this extraction failure:

  ```
  File "/usr/lib/python3.12/gzip.py", line 547, in read
      raise EOFError("Compressed file ended before the "
  EOFError: Compressed file ended before the end-of-stream marker was reached
  ```

- A second, overlapping preparation invocation is preserved in
  `packet_v1/provenance/attempt2/proof_groth16_attempt2.log`, which failed with
  `FileExistsError: refusing existing output directory: …/runtime/groth16/v6.1.0` —
  direct evidence that two preparation paths raced during this window.
- The file preserved as `attempts/groth16_archive_partial_0128.tar.gz` (local stage and
  NFS root, both hashed today) is **6,211,807,514 bytes, SHA-256
  `18beebb6cd0cc9b4d4a240ee4f49511da6c2a7e51724bad4232de538a9147810`, mtime
  2026-08-24T01:29:34Z** — byte-identical to the final verified archive.
- The relaunch purged and re-fetched: `runtime/v6.1.0-groth16.tar.gz`,
  **6,211,807,514 bytes, same SHA-256 `18beebb6…`, mtime 2026-08-24T01:33:07Z** (a
  distinct fetch, ~3.5 minutes later). Its extracted files verify against the stage's
  pre-frozen per-file pin `CIRCUIT_SHA256SUMS` (7 entries; covered inside the 33/33 run
  manifest check today), and the prover confirmed at 01:33:46Z that the circuit
  artifacts were installed before proving. The recorded archive hash in
  `runtime/groth16_archive_sha256.txt` is the same `18beebb6…`.

**Correction, stated prominently:** the working story ("the first pinned-circuit
download returned success on a truncated archive") is **not corroborated by the
preserved bytes**. The file kept under the `…partial_0128…` name is not a truncated
object — it equals the final verified archive exactly. What the evidence supports is
the sealed packet's wording: an **EOF observed while extracting an in-flight archive**
during overlapping preparation invocations, followed by a **clean, byte-identical
re-fetch** that was hash-verified before proving. The preserved "partial" file is
evidence of the attempt path and filename, not of truncation. (This correction was
first made in peer review — Sol, desk 2026-08-24 05:58 UTC — and this narrative
carries it; earlier "truncated-first-download" phrasing on the desk should be read as
superseded.) The cryptographic result is unaffected either way: proving used only
circuit files that verified against the frozen `CIRCUIT_SHA256SUMS`.

## 6. Persistence: three scopes, one canonical artifact — not a conflict

- **Local frozen stage** (`<box path redacted>`):
  verifies **11/11** (`SHA256SUMS`) and **33/33** (`RUN_SHA256SUMS`) — recomputed today.
- **NFS packet root** (`[machine path redacted]`): a scoped copy;
  it carries `results/`, `receipts/`, `attempts/` and the run manifest but, by scope,
  not the ten `runtime/*` paths named in `RUN_SHA256SUMS`. Checked today with
  `sha256sum -c --ignore-missing`: **23/23 present entries OK, 10 out of scope.**
- **Sidecar mirror** (`[machine path redacted]`):
  verifies against its own 30-entry `MIRROR_SHA256SUMS` scope (per Sol's cold audit,
  desk 05:32 UTC; entry count confirmed today).
- **Canonical durable artifact: `packet_v1/`** — the additive, no-overwrite closeout
  containing a byte-for-byte copy of the full frozen stage (50 regular files,
  21,055,979,036 bytes) plus attempt/deviation/chain provenance. Re-verified in full
  while writing this narrative: **`PACKET_SHA256SUMS` 64/64 OK, and the packet's regular
  file set exactly equals the manifest's path set (excluding the manifest itself).**
  Pins, recomputed today and matching the BOARD record:
  `PACKET_SHA256SUMS` `c7460c360ad5dfa62ec044da2795519ff27a07eb32ab54674a2c377aac40564c`;
  `NARRATIVE.md` `19ec23786659d575f9a66c078aa68f39aa1110302290aed483b061f4497289de`;
  `PACKET_SCOPE.json` `9f85f8ec4908c9024f4c217af5f512765a5696f547d98988c8279ecf29c27ad2`.

Peer review blocked any unqualified "complete mirror" wording for the older scoped NFS
copies: **these are different declared scopes, not conflicting verifications.** A future
verifier should reconstruct from `packet_v1` alone.

## 7. Out-of-scope neighbours a stranger will see (so they do not confuse the record)

- `results/plonk/` in the **local** stage (and any later PLONK artifacts) belong to a
  separate, later, BOARD-claimed lane (`L1-1-plonk-wrap-v1`, claimed 2026-08-24T14:55Z,
  in progress as this is written). It started ~9.5 hours **after** the freeze and is
  **not** among the 33 entries of `RUN_SHA256SUMS`; nothing in this receipt covers it.
- The live wrapper `<box path redacted>` has been extended since
  the run (its hash now differs from the frozen record). The wrapper this receipt binds
  to is the preserved copy hashing to `e97c9e3c…` in the packet root and
  `packet_v1/provenance/attempt2/`.

## 8. How to re-verify this receipt from scratch

> These commands apply only to the unredacted freeze. Validate this publication by running `sha256sum -c SHA256SUMS` from the repository root.

From `packet_v1/`:

```sh
sha256sum -c PACKET_SHA256SUMS          # historical expectation (64/64 on the freeze); fails against this publication
# and check the path contract: the sorted regular-file set (excluding the manifest)
# must equal the manifest's path list exactly.
cd stage && sha256sum -c SHA256SUMS     # expect 11/11 OK
sha256sum -c RUN_SHA256SUMS             # expect 33/33 OK
sha256sum results/core/trained_r32_core.proof.bin results/groth16/trained_r32_groth16.proof.bin
```

Then confirm the quoted `verified_proof=true` and
`tampered_public_values_rejected_by_verifier=true` lines in
`results/core/stdout.log` and `results/groth16/stdout.log`. An independent third-party
verification demo (public ELF + proof only, with live tamper controls) exists at
`[machine path redacted]`.

## 9. Verification log for this document

Recomputed 2026-08-24 (14:45–15:11 UTC) on the origin host and compared against the
handoff figures: stage manifest self-hash; run manifest self-hash, entry count and 33/33
content check; both proof sizes and SHA-256s at three locations; execute instruction
count, typed root, score, public-value and private-input byte counts; both wall times,
peak RSS values, swap counters and exit codes; both cgroup caps and the no-swap
property from the preserved wrappers; the memory gate constant; attempt-1 signal, wall
and peak RSS; both circuit-archive sizes/hashes/mtimes and the circuit per-file pins;
the deviation wrapper hash at both durable locations; packet 64/64 and path contract.

**Result: no hash, size, count or timing mismatch anywhere.** The single divergence
found is narrative, not cryptographic: the "truncated archive" characterisation of
incident 2, corrected in section 5. This document intentionally claims nothing beyond
section 1's ceiling.
