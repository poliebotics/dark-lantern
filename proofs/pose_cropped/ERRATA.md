# ERRATA — pose_verdict_20260824 (proof 4 / pose verdict)

Filed 2026-08-24T18:40Z by BOSUN-worker/BOSUN (Lambda BOSUN sub-mind), shipping-artifact audit.

**Historical freeze statement.** In the unredacted freeze, `RECEIPT_NARRATIVE.md` was manifest entry 1 at `3859acaf…`, and `RUN_SHA256SUMS` was pinned at `fd340162…`. In this publication both files were redacted or path-normalised and no longer have those digests. Root `SHA256SUMS` controls the published bytes.
`sha256sum -c RUN_SHA256SUMS` passed on the unredacted freeze; in this publication it returns 12 OK, 21 redaction mismatches and 1 missing path (`./results/guest.elf`). This ERRATA file is deliberately unlisted.

**How to cite.** §3's tamper controls may not be quoted without the scope statement below.

---

## 1. §3 "Tamper rejection, live, twice over" lists only the rejecting controls (material)

Offending text, `RECEIPT_NARRATIVE.md` §3b (the sentence runs from the previous line), verbatim:

> one-bit proof-byte flip REJECTED (receipts/independent_verify/verify.log).

Every clause in §3 is literally true. The defect is scope, in a shipped receipt under a heading
that reads as general tamper-evidence, and the project's own C1 obligation
(`ULTRA_AUDIT_v1.md`, "…and any receipt echo") requires the non-rejecting classes to travel in
the same paragraph as any tamper claim. Two specifics:

1. The flip was of the final byte of the **extracted on-chain proof**, in memory — the demo's
   `--tamper proof` mode does `proof_bytes[len-1] ^= 0x01` on `proof.bytes()`, which is a
   4-byte circuit selector plus the decoded 352-byte blob. It was **not** a flip of the
   2,184-byte proof FILE. `results/pose_join_groth16.proof.bin` ships in this same packet and
   has the same envelope layout as the coupling proof, including a second hex blob at offsets
   991..1640 that verification never consumes.
2. This receipt used the very verifier binary
   (`88c29b1740a5c2db9648a37b6a1e396231e50fe8077b9634776a92a9d4561a01`, per
   `receipts/independent_verify/inputs_sha256.txt`) on which proof-FILE single-bit flips were
   measured **ACCEPTED**, exit 0, identical verifying key.

Corrected statement, replacing that clause:

> one-bit flip of the final byte of the extracted on-chain proof REJECTED
> (receipts/independent_verify/verify.log). Scope of these controls, stated as part of the
> claim: sampled bit positions, not a census, and the classes that do NOT reject travel with
> them. Measured on the L1-1 coupling artifacts by this same verifier binary and codepath
> (guest ELF 8a275c57…, 311,456 B; envelope 4dcdadb1…, 2,038 B): a one-bit flip in non-loaded
> ELF metadata (110,268 B, 35.404% of that file) left the derived key and the ACCEPT verdict
> unchanged; a one-bit flip in loaded code made key derivation panic or fail to terminate
> rather than reject; and one-bit flips at three of four sampled offsets in proof-FILE regions
> that verification never reads were ACCEPTED with exit 0 and a changed file sha256. Neither
> class was re-measured on this pose ELF or this pose envelope, and both are structurally
> present here: this guest ELF (9c5f5352…, 236,760 B) has 110,404 B, 46.631%, outside its
> PT_LOAD file images, and results/pose_join_groth16.proof.bin carries the same never-consumed
> second hex blob at offsets 991..1640. No exhaustive single-bit census was run.

The two ELF partitions were recomputed from the program headers by this errata (both ELFs have
6 program headers; coupling PT_LOAD file images (0,110980) (110980,90200) (201184,8); pose
(0,34924) (34924,91424) (126352,8)). **The 35.404% figure belongs to the COUPLING ELF and must
not be quoted next to this proof** — an earlier draft of this correction made exactly that
mistake. The pose figure is 46.631%.

`verify.log` records two tamper modes only (publics, proof byte). The audit's third, novel
tamper on this proof — an in-envelope typed-root byte flip, REJECTED — was a separate audit run
with **no recorded verify_ms**; cite it as that run, and do not attach a timing to it.

## 2. Pre-existing errata for this lane

These were filed against the unredacted freeze. The publication copy of
`RECEIPT_NARRATIVE.md` corrects item 6; item 7 remains a qualification on
the retained 426 ms measurement.

- Purge item 6: The unredacted freeze called the BOSUN-authored cue assignment
  "human". No blind or human per-row pose label of this take exists. The
  publication copy now says `BOSUN-authored cue assignment`.
- Purge item 7: "third-party cold-verify in 426 ms" (receipts). The verifier was operator-built
  and operator-run on the same host, and 426 ms excludes the ~50 s verifying-key derivation.

---

## Numbers a reader may already have cited

| quantity | previously recorded | status now |
|---|---|---|
| proof-byte flip REJECTED | "one-bit proof-byte flip" | unchanged as a measurement; it is the final byte of the **extracted on-chain proof**, not of the 2,184-byte proof file |
| clean ACCEPT 426 ms, publics flip REJECTED | as recorded | unchanged |
| pose guest ELF non-loaded share | not stated | **110,404 / 236,760 bytes = 46.631%** (new figure, recomputed here from the program headers) |
| coupling guest ELF non-loaded share | not stated | **110,268 / 311,456 bytes = 35.404%** (new figure; belongs to the coupling ELF only) |

Consolidated index: `[machine path redacted]`.
