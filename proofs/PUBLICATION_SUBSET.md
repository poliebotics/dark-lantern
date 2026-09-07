# What is not in `proofs/`, and why

- `row400/`: the row-400 witness and Python oracle of the earlier relation are held from this tree under the programme's
  publication rule of 6 September 2026 (they are not proof receipts).
- `pose_uncropped/proofs_out/uncr64_core.proof.bin` (56 MB): a Core-mode proof, which is not zero-knowledge and is
  derived from the private witness. The Groth16 proof, its public values and the receipt remain.
- `pose_cropped/results/guest.elf`: the guest program binary embedded development-machine paths; the Groth16 proof,
  receipts, logs and handoff records remain. The source is recorded by digest in the handoff manifest.
- `coupling/packet_v1/stage/source/*.tar`: repacked without `fixtures/architecture_r32_parity_v2.bin`, a private
  preprocessed camera and emission tensor with 72 reduced rows; textual files inside the archive carry bracketed
  placeholders for machine paths and its README carries a publication status. The archive's internal `SHA256SUMS`
  therefore no longer verifies; it is kept as the historical manifest.
- `coupling/packet_v1/stage/runtime/groth16/v6.1.0/`: see its `PUBLICATION_SUBSET.md`.
- `row96_membership/`: the operational backups, per-box receipts and experiment runs are removed, and the timing,
  cadence and rate receipts and the three audit reports are held: they read the Profile-R receipt as a timing upper
  bound, a reading the ZeeBeam manuscript withdraws. The proof, the memo-binding and beacon recomputations and the
  byte-map notes remain. The retired staging manifest `OTS_STAGE_MANIFEST.json` (its own text: the timing-receipt hash is
  stale; retired; do not cite) is held from the tenth tree.

Nested digest lists (`RUN_SHA256SUMS`, `PACKET_SHA256SUMS`, `CIRCUIT_SHA256SUMS`, `SHA256SUMS` inside packets) retain
pre-redaction digests, but some path names were alias-normalised and some entries name omitted or relocated files.
They are redacted derivatives of historical manifests, not byte-identical originals, and do not validate publication
bytes. Root `SHA256SUMS` alone controls this publication.

Publication note, 6 September 2026: the row-400 bullet above was added for the eighth tree; the row-96 bullet was amended
for the tenth tree to record the held retired staging manifest. All remaining bullets and the nested-digest warning are
unchanged from the sixth tree.
