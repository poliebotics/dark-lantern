# Byte-sensitivity map: FINAL SUMMARY

All 11444 declared single-bit mutants of the row-96 Core artifact measured
(852,628,903 bytes, sha 582824bc...), each presented with its OWN correct length and
SHA-256 so only SP1-level sensitivity is tested. Coverage: [0,4096), [L-4096,L),
stride 262144 across the body, [23,152) dense.

**RESULT: 0 accepted mutations out of 11444.** Together with the
framing suite (8/8 rejections, byte-87 repro drew a genuine cryptographic error), the
26 Aug cold-ladder n3/n5 "acceptances" are conclusively attributed to the old ladder
harness, not the verifier. Claim scope: tested offsets, bit 0 (ULTRA_AUDIT MEDIUM-5);
stride gaps are not asserted. Written 2026-08-28T01:10:56Z,
desk finish pass after the thread-storm lesson (RAYON defaults, ledger 2026-08-28).
