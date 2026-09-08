> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

# Astra brief r6: pre-publication audit of the finished zkdiff August package (BOSUN, 2026-09-08)

Read-only audit; nothing is published yet. Rounds 1-5 are under (on-box) zk_diffusion_demo_20260907 (ASTRA_VERDICT_zkdiff_r1.md, astra_r2/, astra_r3/, astra_r4/, astra_r5/). The 112-row batch has run and the publication package is filled and frozen. Judge whether the package may be prepared for publication, and what must change first.

The batch (measured, on the node [node address], now terminated):
- g2_guest/batch/BATCH_REPORT.md (per-row table, resources, controls), BATCH_LOG.md (every 10-minute cycle), node_runs/ (eight gpu*/row_*/ directories with proof, public values, receipt; BATCH_MANIFEST.json = strict merge: complete=true, 112 unique rows 600-711, status proved 112, outcomes positive 112, accepted 112/112, problems 0, mirrored rows 10; SHA256SUMS_RUNS verified on the development machine; SHA256SUMS_BATCH over 2146 files), logs/independent_verify/ (zkdiff-verify --expect on the development machine: accepted 112, rejected 0), logs/node_controls_600.log (22 controls, behaved=false 0), pilot/ (timing pilot on the superseded ELF, labelled not-for-publication).
- Pins: ELF 51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc (396,200 B), vkey 0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027, circuit v6.1.0 vk 4388a21c…, expected_identities_august.json 6822cdce…, constants blob 73310dda…; build records under g2_guest/armc-relation/runs/ and the node build record T215855Z.

The package (release_pkg/):
- dark-lantern/proofs/zkdiff_august_20260907/: README.md (title candidate 1 applied: "A Tale of Two Conditionings"; alternatives in ../../TITLE_CANDIDATES.json), STATEMENT.md, VERIFY.md, RESULTS.md (development validation tables, integer agreement, the filled 112-row batch table and counts), AUDIT_TRAIL.md, CLAIM_BOUNDARY.md (your r5 finding-11 paragraphs verbatim), PINS.json (with the batch section), REDACTION.md, LARGE_FILES.md, tools/decode_zbdiff01.py, proofs/ public_values/ receipts/ (filled), source/ oracle/ model/ (frozen snapshots), SHA256SUMS (2565 entries, sha256 0da62cdb…).
- r2_bundle/publish_package/ (3641 objects, 364,745,911 bytes, draft=false, with _control/ and RELEASE.json) for the data-layer prefix results/zkdiff_august_20260907/v1/.
- transmit_drafts/032_zkdiff_darklantern_commit.{sh,body.md,preview.md} (+032_README_PATCH.json) and 033_zkdiff_r2_bundle.{sh,body.md,preview.md}: pins frozen by fill_results.py --freeze; the scripts refuse on any mismatch; 032 prepares the Dark Lantern commit in a private snapshot and stops before the push; 033 uploads and downloads every object back and hashes it before writing a receipt. They are NOT yet in scratch/transmit/.
- fill_results.py, build_r2_bundle.py, tools_release/ (stage_package.py, make_pins.py, make_ledger.py, freeze_transmit.py, REHEARSAL.md), SHELF_LINE.md, OPEN_ITEMS.md, TITLE_CANDIDATES.json.
BATCH_SUMMARY (from the package): {"rows": [{"row": 600, "offset": -2, "rule": "direct", "wrong_row": 598, "r_correct": 4435539299, "r_wrong": 11254163581, "difference": 6818624282, "mse": 0.00944990881197598, "outcome": "positive", "clip": 0, "prove_ms": 3917343, "proof_sha": "12ae264c24a3617bd21a19e9448ace85b9a5cd3e6d20e7740fd621b0f329bc27", "public_sha": "26b5b2d36f9211511bd3e3adff5a71f0700007f2b619440bb9d3603c4154e01b", "raw_sha": "f9b2f91a28551a5eb91de008c9c1cf7a6ab3226d293bc7d300ad66fc15602537", "gpu": "node_runs/gpu0/BATCH_MANIFEST.json", "cold_accept": true}, {"row": 601, "offse

[The release desk's standing publication rules for this package are redacted as private editorial policy; the scientific disclosures they required (the selection procedure and all 112 outcomes, the claim boundary, the calibration rows, the validation status of d2 and v10, the held-out status of the August rows) are stated in the package.]

Questions:
1. Does every number in README.md, RESULTS.md, SHELF_LINE.md and PINS.json trace to a file in node_runs/, g1_integer/final/, node_results/ or g2_guest/ (spot-check the batch counts, the per-row table against receipts, the pins against the build records and the manifests, the integer agreement figures, the ladder tables)? List any mismatch.
2. Is the claim boundary honoured everywhere, including the shelf line and the README's first paragraph? Any overclaim, any omission of a required disclosure?
3. Are VERIFY.md's instructions sufficient for an outsider with the package alone plus the SP1 6.4.0 toolchain to (a) verify one proof and all 112 with the pinned program vkey and circuit key and expected identities, (b) rebuild the ELF and vkey reproducibly? What is missing?
4. Do the two transmit scripts fail closed on every mismatch, match the documented publication process, and match the fired items' conventions? Any way they could publish more or different bytes than the preview describes?
5. Is the R2 bundle consistent with the repository package (same hashes for shared files, RELEASE.json draft=false, controls present) and is the proposed prefix sensible next to the existing published paths?
6. Title: rank the three candidates in TITLE_CANDIDATES.json for clarity and accuracy and flag any that fail it.
7. Anything in the batch evidence that weakens the result (the 65-minute rows under contention, the destructor-panic exits, the unmeasured items marked [confirm]) that the package must state or that should stop staging.

Answer with numbered findings, each with a verdict and file/line, then one line: VERDICT: STAGE / REVISE / STOP with the single most important change before publication.
