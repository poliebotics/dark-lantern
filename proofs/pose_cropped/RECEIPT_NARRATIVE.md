# PROOF 4 — pose-verdict Groth16, receipt narrative
2026-08-24 ~16:05 UTC — BOSUN-worker/BOSUN pose-proof worker (task L1-5-pose-verdict-proof-v1, BOARD CLAIM 15:19Z).
Scope authority: [machine path redacted] (GO). Handoff: source-only SP1 tree, manifest self-hash
`a1b04262272123595572937e0d2da3a6b6bc200c981608eb52758799dd6d0a53`, verified 28/28 entry-by-entry from bytes, both in the
read-only context packet and again in the working stage. The context packet was never modified.

## What was proved
One SP1 6.4.0 Groth16 zero-knowledge proof that the frozen r32 integer pose classifier returns its exact recorded verdict
on a hidden, committed camera crop bound to a typed pair root. Concretely, the guest takes a private preprocessed camera
tensor uint8[4,256,256] plus sixteen private emission leaf sibling hashes, recomputes the camera leaves in the existing
typed camera-plus-emission tree to produce the public typed pair root, performs the exact 8x8 ties-to-even reduction, runs
the frozen integer model, and commits 490 public bytes (typed context digest, typed pair root, 11 integer logits,
first-max verdict, saturation count, logit scale, model and reduction bindings).

Frozen exemplar: development row 52 of the August development take (verification_row=false in the frozen fixture).
Public typed pair root `efd35d054df639c3b07acff6ebab5d2ebec59a85ed0dcde5c0e99aa95006d395`, typed context
`9d99a1f294eb4e7d1d8b87e21498cf1b598354a9f79b130a227fe6621d794789`, integer logits
`8403,8677,184,-1435,6346,-4488,-1564,2047,2253,413,583`, verdict class 1, saturation count 0.

## Row 52: the proven verdict DISAGREES with the BOSUN-authored cue assignment — say this everywhere
The frozen exemplar row 52 is one of the 4-of-116 evaluation rows where the model's verdict (class 1) DIFFERS from the
BOSUN-authored cue assignment (class 0). The annotation is a diagnostic outside the proof relation. The proof is
exactly as valid as on an agreement row — it proves what the model returns on the committed pixels, not what is true —
and it makes the "binds the verdict, whatever it is" property vivid. No presentation of this proof may let a reader
assume verdict==label. Spoken-cue assignment is a separate public comparator, never a pixel-derived label or model input.

## Claim ceiling (handoff text, verbatim — never exceed it)
"A verified proof establishes knowledge of private, already-preprocessed camera pixels and emission leaf hashes
consistent with the public typed pair root, plus the exact frozen model's logits and verdict over those camera pixels. It
does not establish raw sensor origin, preprocessing correctness, row or session membership, capture time, chronology,
physical pose ground truth, or liveness. The model verdict is evidence about committed pixels, not proof of physical
reality."
In the tasking's words: it does NOT establish physical pose truth, liveness, identity, sensor origin, or reality.
Also outside this artifact by design: any row/session-membership join beyond the typed pair root, any blind-annotation
agreement claim, any multi-frame/temporal claim (the temporal arm closed negative). Science-side caveat carried from the
scope doc: the underlying eval has a one-subject/one-room/one-rig/one-occurrence-per-cue confound (within-occurrence
generalisation); this bounds the science claim, not this cryptographic claim.

## Artifact identities (recomputed from bytes at freeze)
- Guest ELF (relation-binding): sha256 `9c5f53522c588024c3c20068f49958e31fa0192d7647e9443f75dc25e8487525`, 236,760 B —
  REPRODUCED on this box from the locked source with pinned cargo-prove `f66b4bf 2026-08-12T14:40:11.709680161Z`.
- Frozen model blob: `c1f16af543f1140dc98944c0343955603fc38f25519784a33c8ff7c34f468d68`, 13,312 B (embedded in guest,
  hash-asserted in-guest).
- Witness fixture (embeds full row-52 private witness + 116 golden vectors): `5b48ec93a73dfc7f2714cdbc4ba1af1f10fa04e588b10eff1a4deb450389e600`, 741,056 B.
- Cargo.lock: `a227ff4c1e53f1ed587260665e8c8adf03a25724d704135e71dec2d4d64c0257`.
- Groth16 proof envelope: `results/pose_join_groth16.proof.bin`, 2,184 B, sha256
  `762f91c0016f5746769292c2f9045ca491ace3c0c7920bcfa585cd191a7ac53e` (on-chain Groth16 proof proper: 356 B).
- Program verification key hash (derived from the ELF by an independent verifier):
  `0x00ca89d51c93402cec467415f9a938dc93911baffd9878d39382dfb56d0a8084`.
- Host prover binary (NOT relation-binding, reproducibility not assumed): `122968ef2b6d8898e559720e86ca1edae65a1fbfe1047a1a8b99fce64e8297cf`, 88,265,656 B.
- Groth16 circuit files v6.1.0: installed at [machine path redacted] from proof-1's already-verified local set,
  7/7 re-verified against CIRCUIT_SHA256SUMS before use; no download occurred.
- Receipt: receipts/pose_groth16_receipt.json — validates against the frozen BOSUN-worker_RECEIPT_SCHEMA.json, status
  GROTH16_PROOF_VERIFIED, all six checks true.

## Run record (all on this box, 2026-08-24 UTC; CPU only, no GPU touched)
1. Execute replay (bounded unit pose-execute-replay-20260824, 34 GiB/1800 s caps, nice 5, 8 threads):
   total_instruction_count=16,611,240 EXACT; 0 syscalls; 490 public bytes; all recorded publics reproduced; span cycles
   bit-identical to the desk-recorded run (model_binding 795,109; typed_pair_camera_membership 8,480,000;
   reduction_and_pose_inference 7,292,310; public_commitment 36,964); host_elapsed 1,143 ms.
2. Frozen bounded Groth16 (unit bosun-zeebeam-pose-groth16-20260824T153833Z.service, started 15:38:33Z):
   the runner re-verified the manifest (28/28), the pinned cargo-prove version string, the reproduced ELF hash+size,
   fmt, all 7 model/native/relation tests, both host contract tests, then ran ONE proof attempt under the frozen caps
   MemoryMax=70G (75,161,927,680 B), MemorySwapMax=0, RuntimeMaxSec=5400, RAYON_NUM_THREADS=8, one worker/buffer per SP1
   stage, with the live MemAvailable/swap guard. Result: exit 0 in wall 20:09.09 (setup 4,189 ms, prove 1,154,097 ms,
   verify 482 ms), ~611% CPU (~6.1 effective cores of the 8-thread budget), cgroup memory peak 35,630,157,824 B
   (33.2 GiB; systemd reported 33.1G; time(1) MaxRSS 34,617,848 KiB), swap peak 0. The 90-minute cap was NOT hit; the
   scope doc's R1 timeout contingency was NOT needed; no cap was amended. Note: SP1's groth16 mode performs the core
   shard proving, compress, shrink, and wrap internally in this one bounded unit; per the frozen contract there is no
   separate standalone core-STARK artifact for this relation.
3. Tamper rejection, live, twice over:
   a. In-run (frozen host, required before save): verified_public_values=true, verified_proof=true,
      tampered_public_values_rejected_by_verifier=true; "proof relation self-verified and tampered public values were
      rejected before save".
   b. Independent cold verifier (pinned sp1-verifier demo binary `88c29b1740a5c2db9648a37b6a1e396231e50fe8077b9634776a92a9d4561a01`,
      built for L1-1, generic over ELF+proof): clean ACCEPT in 426 ms from ELF+proof bytes alone; one-bit public-values
      flip REJECTED; one-bit proof-byte flip REJECTED (receipts/independent_verify/verify.log).

## Concurrency and the no-starvation record
By explicit tasking, this proof ran CONCURRENTLY with the active L1-1 PLONK prover (unit zeebeam-r32-plonk-a2-20260823,
224 rayon threads, nice 5) under the pose handoff's frozen 8-thread profile — a declared exception to the handoff's
no-overlap operator rule, safe on this host (240 vCPU / 1.77 TiB; runner's own >=85 GiB MemAvailable gate passed with
~1.66 TiB available; its process-pattern overlap guard was dry-run clear before launch). Starvation evidence
(receipts/plonk_before_runner.txt, plonk_after_runner.txt, pose_unit_monitor.csv): PLONK averaged 68.8 effective cores
during the 20-minute pose window vs 65.9 at the pre-launch baseline, memory 34.8->36.4 GB (normal growth), zero swap,
active before and after. The PLONK job was not stopped, throttled, or starved. ARM-A kept all 8 GPUs; no trainer or run
directory was touched.

## Declared deviations and accommodations (complete list; relation, publics, ELF, and caps unchanged)
1. GOMAXPROCS=8 supplied via the systemd user-manager environment for the unit's lifetime (set 15:38:30Z, unset
   15:58:43Z). The frozen runner leaves GOMAXPROCS unset, which on this 240-core host would have let the gnark wrap tail
   use every core — exactly the full-thread competition the tasking forbids. Bound-tightening only.
2. <box path redacted> -> <stage>/results symlink for the unit's lifetime (created 15:38:30Z, removed 15:58:43Z).
   Latent path quirk found in the frozen runner: systemd --user units default CWD to $HOME while the runner passes the
   RELATIVE --proof-out results/pose_join_groth16.proof.bin and then checks it relative to the handoff root. BOSUN-desk's
   interrupted attempt never reached save, so this was never observed before. Without the symlink the finished proof
   would have failed at save. Future re-freeze should add --working-directory or an absolute --proof-out.
3. ELF reproducibility required CARGO_HOME=<machine path redacted> (symlink to <box path redacted>, [machine path redacted] created for this).
   Root cause, evidence-backed: six dependency panic-path strings (sp1-zkvm x4, embedded-alloc, blake3) embed the
   absolute cargo registry prefix; bosun-desk's coupling ELF (8a275c57..., durable in the zk-magic demo) shows bosun-desk's prefix
   <machine path redacted> A first build under <box path redacted> produced a
   236,776-B non-matching ELF; under the corrected prefix the ELF reproduced byte-exactly (9c5f5352..., 236,760 B).
   Scope-doc risk R2 closed without any re-freeze. Future handoffs should record CARGO_HOME as part of the repro recipe.
4. BINDGEN_EXTRA_CLANG_ARGS="-isystem /usr/lib/gcc/x86_64-linux-gnu/13/include" for the host zk-wrap build only (this
   box has libclang-18 without clang builtin headers). Affects host-binary compilation, never the hash-gated guest ELF.
5. Box tool provisioning, no new downloads beyond rustfmt: pinned cargo-prove and go1.27.0 extracted from proof-1's
   hash-verified archives (8ad88ebd... / 675c26c4...; extracted cargo-prove byte-identical d8835f80... to the existing
   <box path redacted> copy); succinct guest toolchain (rustc 1.94.0-dev, already unpacked at
   [machine path redacted]) linked into rustup as "succinct"; rustfmt component added to the stable toolchain via
   rustup (the one network component fetch); Go module fetches during the FFI build are go.sum-locked inside the pinned
   sp1-recursion-gnark-ffi 6.4.0 crate; cargo deps fetched under the locked Cargo.lock.
6. Declared concurrency with the PLONK prover (previous section) — ordered by the tasking, evidenced harmless.
NOT needed: RUST_MIN_STACK (no SIGSEGV at 8 threads), any cap amendment, any GPU, any rental, any re-freeze.

## Data boundary
Development-take material only (row 52 of the August development take; fixture records verification_rows_loaded=0).
The sealed 288-row verification take was not present, requested, or referenced. authority: verification_open=false,
chain_transaction=false, publication=false.

## Freeze
In the unredacted freeze, `RUN_SHA256SUMS` was written last over every file except itself and verified. In this publication, see `ERRATA.md` for changed, absent and deliberately unlisted paths.
Working stage: <box path redacted> (local NVMe scratch; this NFS packet is the durable record).
