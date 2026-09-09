# Dark Lantern: Zero-Knowledge Light, Shuttered by Design

Dark Lantern is the privacy and zero-knowledge research programme behind ZeeBeam, the Zero-knowledge Evidence Emitter Beam. The ZeeBeam release
(`poliebotics/zeebeam`) is the programme's core result: one zkVM relation, proved for every anchored row of a
projector-camera session. This repository is a curated public subset of the programme record beyond ZeeBeam:
selected standalone proof outputs, diagnostics, notes, audit prompts and verdicts, and retained fixtures, under the
programme's publication rule of 6 September 2026: positive, patent-supporting results only, disclosed as fully as the
record allows.
Publication-subset notices identify omitted and non-rebuildable material.

Historical notes preserve language current when written. Opening notices identify later supersession, and the ZeeBeam
manuscript (v3.20, in the ZeeBeam repository) controls every current claim. Where a note's own status line says
`historical`, `withdrawn` or `superseded`, read it as a record of what was thought at the time.

## What is here

| path | what | status |
|------|------|--------|
| `notes/zeebeam_uncropped_pose_proof_20260901.md` | the uncropped pose Groth16 proof (2,094 B): a frozen-classifier verdict over supplied committed bytes | proof/result v1.0 audited PASS; post-audit prose additions withdrawn |
| `notes/zeebeam_pose_proof_state_20260830.md` | the earlier cropped pose proof (2,184 B): ceiling and filed erratum; its section on a withdrawn discriminator line is held by a logged publication edit | historical standalone proof; ceiling and filed erratum remain current |
| `notes/zeebeam_nocrop_diffusion_8seed_20260830.md` | uncropped conditional-diffusion row conditioning, eight seeds, two sessions | settled ML result; the claim text that passed the fourth audit round (`audits/diffusion_8seed_audit/CLAIM_DRAFT.md`, whose own heading still reads v3), not every broader interpretation in this note, received the PASS audit |
| `notes/zeebeam_realness_study_prereg_20260828.md` | the realness study preregistration | historical frozen preregistration; premise corrected; execution deviated |
| `notes/zeebeam_realness_results_20260901.md` | the exploratory realness measurement: one generator-based class; one generator-free diagnostic reported without preserved records; classes 2 and 4 unrun | exploratory |
| `proofs/coupling/` (87 files) | the coupling Groth16 proof (2,038 B, verifies in 0.445 s) and PLONK proof, receipts and packet metadata | historical public subset of the frozen packet (51 of 64 manifested paths, 29 with their historical digest); see `proofs/PUBLICATION_SUBSET.md` |
| `proofs/pose_cropped/` (35 files), `proofs/pose_uncropped/` (6 files) | the two pose Groth16 proofs with receipts and public values | proof-output and receipt subsets; not rebuildable from this tree |
| `proofs/typed_root/` (3 files) | the typed-tile-root Groth16 proof (1,759 B) with its results | proof-output subset; not rebuildable from this tree |
| `proofs/conditional_micro/` (52 files) | two conditional micro-PLONK proofs of 23 August over one committed 4×4 tensor collection, revalidated 6 September: verification keys, proofs, publics, retained negative artefacts, synthetic zero-margin tests, `verify.sh`; the failed direction inside each passing aggregate is disclosed | development-data arithmetic fixture; audited MAY BE STAGED |
| `results/train_free_coupling_20260906/` (114 files) | the train-free grid-correlation statistic on the 975 held-out tail frames of d2 and v10, reproduced from the public frames to 1e-6, with five recorded within-session derangements and four hard-negative families registered before scoring (50 of 50 and 40 of 40 above the 0.60 floor) | retrospective positive on previously inspected frames; every protocol deviation stated |
| `proofs/train_free_grid_correlation_20260906/` (42 files) | two CPU PLONK proofs that Poseidon-committed 4×4 RGB cell-sum grids of a real public capture correlate above 1/8 with its own emission and below 1/8 with its recorded mismatch; circuit, keys, proofs, fixtures, self-contained replay, 13 controls with failure layers | engineering demonstration on public data; retrospective threshold |
| `proofs/row96_membership/` (5 files) | the row-96 membership Groth16 proof (2,391 B) of 27 August with the memo-binding and beacon recomputations and the byte-map notes; superseded by the joined relation in ZeeBeam | history; its timing receipts, audit reports and a retired staging manifest are held (see `proofs/PUBLICATION_SUBSET.md`) |
| `proofs/zkdiff_august_20260907/` | *A Tale of Two Conditionings*: one Groth16 proof (356 B raw, 752-byte public statement) per August row 600 to 711 of an integer diffusion evaluator adapted from the frozen ARM-C protocol, whole-frame preprocessing and two conditional evaluations at timestep 150 inside the joined relation; 112 proofs, 112 positive, 0 zero, 0 negative signed outcomes, every one published; frozen source, oracle, model and receipts; the raw frames, the August tensors and an offline build kit on the data layer; an offline verification capsule and a one-pull replication kit; ten GPT-6 Astra audit rounds and nine outside-agent readability reports, texts published | execution binding only (`CLAIM_BOUNDARY.md`); August rows 600 to 711 held out from weight training, seven of them used for quantisation calibration, as disclosed; the d2/v10 evaluation blocks are development validation |
| `results/old_light_20260909/` | *The Light of Other Days*: emission-recording correspondence in the April 2023 and December 2024 Truth Beam recordings, measured three ways on 9 September 2026: a train-free grid statistic with projected-region alignment (the correct recording preferred to one random same-session alternative in all 1,032 tested comparisons across fifteen sessions, no model), pix2pixHD models trained on the recordings (the correct light pattern favoured in all 64 two-choice comparisons from the held-out December session; exploratory) and ARM-I, the image-conditioned sibling of the ARM-C diffusion evaluator trained on the 2026 recordings (447 of 448 December 2024 frames zero-shot, paired 0.998, pooled AUROC 0.657; a unified three-rig model at AUROC 1.000 on the held-out aligned 2023 trailer and 0.788 / 0.726 on the held-out 2024 session); four GPT-6 Astra results audits applied, texts published; the checkpoints, per-row scores, run records and contact sheets on the data layer | emission-recording correspondence within these recordings only (`CLAIM_BOUNDARY.md`); nothing proved in zero knowledge; held-out sessions excluded from weight training, with monitoring, exploratory reuse and target-fitted alignment disclosed |
| `vectors/drand_quicknet/quicknet_vectors.json` | seven sampled quicknet vectors, verified 7/7; the JSON separately records an aggregate 712/712 assertion that cannot be recomputed from this fixture | verified |
| `audits/audit_packets/results_docs_20260901/` (2 files) | the two retained primary-evidence files: the realness ROC JSON (`REALNESS_ROC_generated_fa_v1_step100k.json`, cited by the realness note) and the uncropped-pose integer-parity vectors (`PARITY_VECTORS.json`: 461 calibration rows without saturation or overflow, 114 of 116 float and integer agreements) | evidence; the audit briefs, verdicts, predeclaration and prove logs of the two BLOCK audits are held |
| `audits/diffusion_8seed_audit/` (48 files) | the four-round audit of the 8-seed conditioning result, v1 BLOCK to v4 PASS, with claim drafts, evidence, recomputation and raw score arrays | sanitised extracts from completed audits; primary-evidence limitations remain as stated in the verdicts |
| `audits/forgery_rejection_receipts/` (13 files) | 23 August diagnostic receipts: the fixed Phase-G scorer's scores on 81 F-A-v1 generated rows, cue compliance, and zero-shot Phase-G runs | diagnostics; no proof or general forgery-rejection claim; the row-level pose annotations are held |
| `LICENSE` | the Dark Lantern Research and Private Use Licence 1.2, adapted from the ZeeBeam licence | |
| `THIRD_PARTY_NOTICES.md`, `licenses/` | the third-party material actually distributed here (SP1 verifier and key artefacts, public beacon and chain data, and the circomlib-derived WebAssembly witness generators with their Circom-emitted JavaScript helpers, under GPL-3.0) | |
| `CITATION.cff`, `SHA256SUMS` | citation; the digest of every other file in this tree | |

Not here, by decision or by size: raw sensor-frame files; the sealed 288-row verification session; derived imagery
showing a person, except the six public capture and emission fixtures under
`proofs/train_free_grid_correlation_20260906/fixtures/`, which are copies of frames already published on the data gateway
(two contact sheets and two row-level annotation files remain held for the principal's separate clearance); the non-ZK Core proof and the guest binary (`proofs/PUBLICATION_SUBSET.md`); the five
operational state logs of the programme (they mix private operations with design material awaiting the principal's
intellectual-property review); the row-96 timing, cadence and rate receipts and their three audit reports; the fake
table (90 GB), the forgery-rejection circuits (8 GB) and the coupling reconstruction archive (6 GB), which belong on a
data gateway; the 2,453-byte forgery-rejection Groth16 wrap with its gate and errata, not staged here; the held design
notes; student-ladder material, which the programme's 1 September directive set aside. Held notes and student-ladder
material are absent from this tree. Also held, under the programme's publication rule of 6 September 2026 (positive,
patent-supporting results only; within that frame, maximal disclosure): the two pose-confound notes and the temporal
split's predeclaration and evidence; the PairNet null result; the withdrawn August realness framing; the Monero
compatibility note (a negative verdict); the persist-before-judge incident note; the cheap-proof fixture note whose
diffusion route was closed as a negative; the 1 September results-audit briefs, verdicts and prove logs (two BLOCK
audits); the row-400 witness and Python oracle of the earlier relation; and, pending the principal's decision, the
draft cross-rig position and the neural-only training constraint note. Superseded but valid positives stay: the cropped
pose proof with its state note, and the row-96 membership proof. The 8-seed conditioning audit trail stays because it
ends in a PASS. Limits stated inside the kept notes are scope, not negatives, and stay.

## Redaction

Files in this publication are sanitised or repacked; they are not byte-identical copies of the private tree. Internal
identities are normalised according to the public alias map. Historical nested manifests retain pre-redaction digests,
but some path names were alias-normalised; none of those historical manifests validates publication bytes. The three
package ledgers added on 6 September (`proofs/conditional_micro/SHA256SUMS`, `results/train_free_coupling_20260906/SHA256SUMS`,
`proofs/train_free_grid_correlation_20260906/SHA256SUMS`) are regenerated over the published bytes and do validate their
subtrees; the root `SHA256SUMS` remains the authority for the whole tree.

The alias map: the principal is named as such or as Cathal Ryan Hynes; the assistant's three machines appear as
`BOSUN-desk`, `BOSUN-worker` and `BOSUN-second`; historical run-name suffixes `boxA` and `boxB` are anonymous machine
aliases, with `boxB` collapsing two former control-host labels. Other internal identity tokens are `BOSUN` or bracketed
placeholders. Network addresses, personal source paths, provider instance identifiers and opaque invocation identifiers
are placeholders. Experiment run names and historical service, cgroup, runtime, toolchain, device and working-tree paths
remain where they form part of the evidence. Second-model transcripts are not published because they repeat the
operator's private instructions; their verdicts are reproduced. The root `SHA256SUMS` alone inventories and hashes the
published tree.

## Provenance

Principal: Cathal Ryan Hynes (PolieBotics). Drafted, built, proved and verified with BOSUN, the project's automated
research assistant, under the principal's direction. Second-model audits by Sol (OpenAI GPT-5.6) and, from 6 September, GPT-6 Astra, both through `codex exec`, with their
verdicts attached; these are model reviews, not independent validation.

Eleventh tree, 6 September 2026: re-staged under the programme's publication rule of that day (positive, patent-supporting
results only; maximal disclosure within that frame). The held material is listed in the "Not here" paragraph above; the
build history is in the initial commit message.

Twelfth and thirteenth trees, 6 September 2026 (evening): three positive packages added after GPT-6 Astra audits of their exact bytes: the
conditional micro-PLONK extract, the train-free coupling package and the grid-correlation proofs (`proofs/conditional_micro/`,
`results/train_free_coupling_20260906/`, `proofs/train_free_grid_correlation_20260906/`). A cross-rig compact-verifier candidate
run the same evening did not meet its registered criteria and is held, not published. Each package was audited on its exact bytes by
GPT-6 Astra (`codex exec`) before it was added; the packages' own records summarise the outcomes and the corrections applied,
while the audit texts stay on-box because they quote the operator's private instructions. The closing pass on this tree is
recorded in the private build record.

Proof package `proofs/zkdiff_august_20260907/`, batch of 2026-09-07: 112 Groth16 proofs of the two-evaluation diffusion statement, one per August row 600 to 711, proved on a rented eight-GPU node and each accepted cold against the frozen identities on the node and again on the development machine; the package carries its own `SHA256SUMS` (revision 1.1 of 9 September 2026: 3135 entries, SHA-256 `88193edbcd4b55fdf0e422e9e3a1778ad09f6ace1f772d8a7200af89322cfffb`; revision 1.0 as first published: `40bb69a54eee08a74598aba8b8e0c50d00db747e9fdaaf17875d5253421790b8`). Its large files, the 112 raw frames of the proof rows, the August camera-derived tensors, an offline build kit and the allowlisted proof-run collection sit on the data layer under `results/zkdiff_august_20260907/v1/`: 5,670 manifest-listed payload objects, 12,671,401,166 payload bytes, plus the root ledger and three control files, fixed by that prefix's `_control/MANIFEST.jsonl` (SHA-256 `3702e36ab85a2b9f650ce838f2cd79d35919764ca25e1ec3dfa32f78ca688f65`), `_control/SHA256SUMS` (`edfb98119a487742b5fef274b0bf286683559434280ab046ab9db20c02619d25`) and `_control/RELEASE.json` (`b1e3aac6578c527173d1a7ce29353912fd9460fc885af3388d5cfbdd29db8799`); revision 1.1 replaced only the six front-matter copies, the root ledger and these three controls (revision 1.0's controls were `e1bca0243dda85d8431c9091ba81fb3313609123fc1b7730f9781bf210df3f88`, `12774760f4c8874c8adaf3e116f9c4b4caa31ba50a79fa7e899aaca7bba6c1aa` and `cf716a7225863770404be403ecdc6b2c1acf8c59aa53af57deea35d6564cfc62`). Audit rounds one to ten (GPT-6 Astra, `codex exec`; five before proving, one on the finished package, a privacy sweep and three confirmation re-reads) and the nine outside-agent readability reports (three readings) are summarised in its `AUDIT_TRAIL.md` and published in full in its `audits/` (the privacy sweep by its verdict and dispositions).

Results package `results/old_light_20260909/`, 9 September 2026: three positive results on the April 2023 and December 2024 Truth Beam recordings (the train-free grid statistic with projected-region alignment, pix2pixHD models trained on the recordings, and ARM-I, the image-conditioned diffusion evaluator trained on the 2026 recordings and tested across rig configurations), each audited by GPT-6 Astra before packaging; the package carries its own `SHA256SUMS` (325 entries, SHA-256 `296df690008ac294f6523ef9490f47579b5a6eccae0f7917cc840240d59da427`). Its large objects, the fourteen checkpoints as documented derivatives, every per-row score array, the pix2pixHD run records with every contact sheet, the cached grids of the statistic and the data-look alignment atlas, sit on the data layer under `results/old_light_20260909/v1/`: 874 manifest-listed objects, 868,823,018 bytes, plus the root ledger and three control files, fixed by that prefix's `_control/MANIFEST.jsonl` (SHA-256 `dfe707e955509eb02ce519cb660cf5bbe1d1339acb2bb114b6fd6054e3d258b7`), `_control/SHA256SUMS` (`070a81e648ff5ab82eff0a2d88920b569f94558104255d75201f9d4be8319ee3`) and `_control/RELEASE.json` (`db1bddfedc7456994b8a2e4fd2051449b19d56e31ac3f2790a6f1936a15c0e4d`). The four results audits are summarised in its `AUDIT_TRAIL.md` and published in its `audits/`; the images published show a masked participant, as its `README.md` states.

— BOSUN ⚓
