---
version: 1.9
date: 2026-09-08
status: the second-model audit rounds (five before the proofs, the sixth on the finished package, the seventh a privacy sweep of the payloads, the eighth and later ones confirmation re-reads) and the readings by three outside agents, with their verdict lines, the subjects of every finding, what changed after each, and the texts in audits/
author: BOSUN for Cathal Ryan Hynes
---

# Audit trail

Five audit rounds by the programme's second model, GPT-6 Astra through `codex exec` (model `gpt-6-astra`, ultra
reasoning effort), read the plan, the trained candidates, the integer oracle, the Rust kernels and the complete guest
before anything was proved. Each round was a read-only audit of files on the development machine; none generated a proof
or edited a file. The verdict line of each round is reproduced verbatim in the table that follows, and the full texts, the
brief the desk gave and the verdict returned, are published in `audits/astra/` by the principal's decision of 8 September
2026, with on-box paths trimmed to package paths and the alias rule applied (`audits/README.md`). These are model reviews,
not independent validation. The five rounds took place on 7 September 2026 (file times, Irish Standard Time). A sixth round,
on 8 September 2026, read the finished package, the 112-proof collection and the two release scripts after the batch, again
read-only from the staging tree. Three outside agents (a Claude model, a Codex model and a Grok model) then each read a copy
of the revised package with no other context and reported what they could follow, what they could check and what they could
not answer (the first reading); after the principal's decision to publish the frames, the August tensors and the audit texts,
the second model read the augmented payloads twice more the same evening, as a privacy and embarrassment sweep (round 7) and as
a confirmation re-read of the round-6 dispositions (round 8), and the three outside agents read the augmented package a second
time. Their reports are `audits/agents/`, their verdict lines are in the table, and `FAQ.md` answers their questions. Where a
verdict line named the principal, the published audit copies and this table read "publication" instead, as the redaction of
the privacy sweep requires; nothing else in the lines is changed. The text of round 7 itself is not published: it quotes the
material it asked to remove; its dispositions and their application are summarised in the section on rounds 7 and 8.

| round | time | subject | verdict line |
|---|---|---|---|
| 1 | 16:12 | the engineering plan: statement, network, proving stack, integerisation, gates, claims | "VERDICT: A lean zero-crop diffusion execution-binding demo is plausibly achievable in about one engineering week and comfortably under $1,000 GPU spend [estimate], conditional on G0 passing. My working budget is 4–7 engineering days and $25–150 GPU. Full-resolution ARM-C through the current SP1 guest is outside those bounds." |
| 2 | 18:51 | the candidate switch after the first training sweep (G0) | "VERDICT: REVISE: retain ARM-C, but require end-to-end residual-error validation and byte-exact complete-guest parity at G1." |
| 3 | 19:41 | the integer reference (G1) | "VERDICT: REVISE — freeze one internally consistent integer execution contract, especially effective scales and input-rounding/noise bytes, before Rust treats G1 as authoritative." |
| 4 | 20:32 | the Rust integer kernels and the SP1 bench guest (G2-A) | "VERDICT: REVISE: make the proof guest execute one authenticated FINAL integer contract with oracle-matching saturation semantics before proving." |
| 5 | 21:32 | the complete guest before proving (G2-D) | "VERDICT: REVISE: fix and regression-test the complete mirrored-offset rule, including −30, then freeze the rebuilt ELF and vkey before the pilot proof." |
| 6 | 8 Sep 15:29 | the finished package, the 112-proof collection and the release scripts (G3) | "VERDICT: REVISE: exclude on-box incident material from both public payloads and regenerate their frozen inventories before publication." |
| 7 | 8 Sep 18:08 | privacy and embarrassment sweep of both payloads and the transmit texts, after the publication decision (text not published) | "VERDICT: STOP. Regenerate both payloads with private infrastructure and desk disclosures removed from the actual shipped bytes, including the audit briefs and compiled binaries, before publication." |
| 8 | 8 Sep 18:01 | confirmation re-read of the round-6 dispositions on the augmented package (nineteen findings: 8 PASS, 11 REVISE) | "VERDICT: REVISE: fix 033’s overriding stdin redirection so landed-object verification actually executes before any upload is attempted." |
| 9 | 8 Sep 20:03 | confirmation read of the package as re-frozen after rounds 7 and 8 and the fresh-machine replication (twelve findings: 1 STOP, 10 REVISE, 1 PASS) | "VERDICT: STOP: remove the remaining private infrastructure and desk-policy text from the shipped copies, then re-freeze." |
| 10 | 8 Sep 20:43 | confirmation read after round 9 (seven findings: 1 STOP, 2 REVISE, 4 PASS) | "VERDICT: STOP: remove the wrapped private desk phrases and make their residue checks whitespace-aware before re-freezing." |
| A1 Claude | 8 Sep 16:49 | readability of the round-6 package for an outside agent, first reading | "**YES WITH EFFORT** for checking the proofs, **NO** for recomputing what they prove: given a network-fetched Rust/SP1 toolchain, the two rehearsed routes let an agent verify all 112 Groth16 proofs under the pinned key and every frozen identity, but the residual sums can only be compared with the prover's own oracle table because the frames and August tensors are held, and the session, the emission, ARM-C, d2/v10, the roles and the fact that rows r-1 and r usually share one drand round must be inferred from source. **Single most important fix:** add a one-page primer to `README.md` …" |
| A1 Codex | 8 Sep 16:49 | the same (Codex) | "**NO — the single most important fix is to ship a self-contained offline row-600 reproduction capsule containing its raw frame, required oracle inputs, verifier/prover dependencies and circuit assets, with one package-root script that verifies, re-executes, and reproves it.**" |
| A1 Grok | 8 Sep 16:49 | the same (Grok) | "**NO** — an agent with this package alone cannot follow and check all the proofs: Groth16 checking still needs a network (or a cargo cache this tree does not contain) and a Rust/SP1 toolchain; residual-sum reproduction and proof reproduction need held camera tensors and raw frames that the package itself says are absent. **Single most important fix:** ship a prebuilt standalone verifier (or a `cargo vendor` of the 209 locked crates) **and** the August integer input tensors `oracle/final/august_inputs/row_*.npz` …" |
| A2 Claude | 8 Sep 18:34 | readability of the augmented package (frames, tensors, capsule, audit texts), second reading | "**YES WITH EFFORT.** With this package alone, on an x86_64 Linux box with about 17 GB of RAM and no network, an agent can verify all 112 Groth16 proofs under the pinned key and every frozen identity, decode and cross-check every statement in Python, regenerate the normative noise from its rule, and recompute row 600's residual sums from its raw frame; rebuilding the program, recomputing any other row and re-proving are fully specified with pinned, sourced downloads but need the network and a data layer whose live state the package itself leaves in doubt. **Single most important fix:** remove every surviving 'frames are not published / tensors are held' sentence … and replace `FAQ.md:281` with one dated statement of what is live …, then let `replicate.sh execute` and `prove` take a frame from `frames/` on the data layer or default to `capsule/reexecute/frame_000600.raw` …" |
| A2 Codex | 8 Sep 17:59 | the same (Codex) | "**NO — the single most important fix is to bundle a hash-pinned offline source-to-vkey build environment, including all locked crates and SP1 toolchains, so the shipped verifier and proved program can be independently rebuilt rather than trusted as binaries.**" |
| A2 Grok | 8 Sep 18:00 | the same (Grok) | "**YES WITH EFFORT** — an agent on x86_64 Linux can check all 112 Groth16 proofs and their frozen identities with `bash capsule/verify_offline.sh`, and can recompute row 600's residual sums from the shipped frame; the same agent cannot rebuild the guest, cannot re-prove, and cannot recompute the other 111 rows from this directory alone. **Single most important fix:** Delete or update every leftover 'frames are held / not published' sentence … so they match `FRAMES.md`, and either put the remaining 111 frames and `august_inputs/row_*.npz` files in the tree the way row 600 already is, or strike FAQ 49's 'Until the upload is released the prefix is empty' once that prefix actually holds the bytes …" |
| A3 Codex | 8 Sep 20:42 | readability of the round-9 revision for an outside agent, third reading (Codex) | "**NO — the single most important fix is to bundle the complete data-layer payload, including `build_kit/`, all 112 frames, and all oracle inputs, inside the publication package rather than referring to external storage.**" |
| A3 Grok | 8 Sep 20:43 | the same (Grok) | "**YES WITH EFFORT** — on x86_64 Linux, with ~17 GB RAM, an agent can follow the claims from the primer, glossary, FAQ, and statement, and can check all 112 Groth16 proofs under the pinned key and frozen identities with `bash capsule/verify_offline.sh`, if that agent accepts the shipped static binaries; … **Single most important fix:** Put the offline build kit (`build_kit/`: vendored lockfile crates and the pinned toolchains) **inside this directory** …" |
| A3 Claude | 8 Sep 20:55 | the same (Claude) | "**YES WITH EFFORT.** With this package alone, on x86-64 Linux with about 17 GB of RAM and no network, an agent can verify all 112 Groth16 proofs under the pinned key and every frozen identity, cross-check every statement and regenerate the noise in Python, and recompute row 600's residual sums from its raw frame; rebuilding the program, recomputing the other 111 rows and re-proving are fully pinned and rehearsed but need the network or the data layer and, for proving, an A100-class GPU. **Single most important fix:** make the audit bookkeeping agree with itself …" |

## The subjects of the round-6 findings

Cited by number elsewhere in the package; the texts are `audits/astra/r6_verdict.md`. 1 PASS, batch evidence and numerical
traceability (112 of 112 re-verified, every table row and digest reconciled). 2 REVISE, two numerical statements (the
framed-artifact size distribution; the residual-ratio sentence). 3 PASS, the claim boundary honoured. 4 REVISE, incident
material inside both payloads (the prover clients' exit diagnostics; a synthetic-session outcome described as published). 5 PASS,
the build pins match (the node's final build record to be added). 6 REVISE, the verification instructions (working-directory
changes, missing requirements, no rehearsal). 7 REVISE, the standalone route external and unpinned. 8 REVISE, the oracle
regeneration's concrete failures (import paths, withheld stages, the scale map). 9 REVISE, the repository commit script's
ledger generation. 10 REVISE, malformed frozen publication text. 11 REVISE, the upload script's download checks and failure
semantics. 12 REVISE, validated bytes could change before consumption (snapshot first). 13 PASS on data-layer consistency,
REVISE its ledger description. 14 REVISE, operational context of the batch. 15 REVISE, editorial corrections in copied prose
(the finding's text is redacted in the published verdict as private editorial policy). 16 TITLE, candidate 1 kept. Their application is recorded in the release desk's record (on-box) and, in the package, in
each document's Log.

## The subjects of the round-8 findings, and the round-7 dispositions

Round 8 (`audits/astra/r8_verdict.md`) confirmed the round-6 dispositions on the augmented package: PASS on the proof-size
distribution and residual ratios, the evidence allowlist, the node build record and vendored verifier, the ledgers and bundle
manifest, the published frames and tensors (all 112 frames, all 672 tensor hashes, 224 residual sums reconciled), the capsule
(112/112, 112/112, 18 controls, rows 600 and 684 reproduced), the drand counts and the quick-screen correction; REVISE on the
upload script's landed check (its file list overrode the checker's own source, so it never ran), the commit script's file
modes (the capsule executables would have entered Git as 0644), the unsnapshotted README patch, a stale frames pin in
`PINS.json`, the regeneration wrapper's private paths, `VERIFY.md`'s blanket rehearsal claim and missing C toolchain
requirement, malformed preview text, the capsule descriptions (the re-execution runs the guest in the SP1 executor, not
natively; glibc 2.43, not 2.39), leftover held-data wording, unusable trimmed links in the audit copies, and the root notices
the commit must carry. All eleven were applied: the landed check is one function run against the snapshot in `--preflight`; the
package carries `MODES` and the commit script applies and verifies it; the drafts are snapshotted before use; the frames pin is
refreshed from the bundle and checked at freeze; `run_final.sh` resolves the published layout; `VERIFY.md` names its
remaining unrehearsed steps (three then, two since the fresh-machine replication) and the C toolchain; the previews are rendered from the package and the manifest; the capsule
descriptions are corrected; every held-data sentence is replaced (`FRAMES.md`, `FAQ.md`, `GLOSSARY.md`, `HASHES.md`,
`VERIFY.md`, `replicate/`); the audit copies' links read as file-and-line text; the commit adds the notices rows and licence
texts.

Round 7 (the privacy sweep, text not published) listed 133 dispositions over both payloads and the transmit texts. Its
findings: private spending and desk instructions in the audit copies (removed or reworded, with a common banner on every copy
and the auditors' salutations dropped); agent chatter and broken path trims (repaired); the imagery, which the auditor viewed
in full, is not anonymous and the release did not say so (the disclosure now in `README.md`, `FRAMES.md`, `FAQ.md` and the
data-layer README: a masked participant in a recognisable indoor setting; camera-derived tensors retaining images of
participants and their surroundings; not anonymised); statements that still called the images withheld (replaced); the
development machine's and the node's paths and hostnames throughout the copied records, receipts, build records, the checkpoint's
argument record and the compiled binaries (every text record passes through one redaction rule with both digests recorded in
`REDACTION_LEDGER.tsv` and `receipts/REDACTION_LEDGER.tsv`; the checkpoint is a documented derivative; the three binaries were
rebuilt with every dependency under a path remap and re-pinned); the machine identities (role labels); the transmit texts
(private paths and the operator's name removed from the public previews and bodies); scientific and claim wording (the
quick-screen rows, the four training-row hints, the rehearsal claims, the timings, the sizes, the incident language, the rule
called the declared offset rule, the patent notice reduced to the filing date, the mark, the data-layer licence statement); and
the legal findings on glibc and the missing licence texts, met by the notices rows, `capsule/THIRD_PARTY_NOTICES.md` and the
licence texts the commit adds. KEEP items (the historical cost estimates, the authorship credits, technical terms such as
`panic!`, upstream contact strings inside glibc) were left as they were.

## What changed after each round

**After round 1.** The plan was set as four gates: a learning and integer-feasibility screen with no cloud spend beyond
one authorised session (G0), exact guest execution on the development machine's CPU with byte-exact agreement against an
independent integer oracle (G1), one real proof on one A100 (G2), and audit and release (G3). The statement was fixed
as the two-conditioning residual comparison with the complete input binding retained (frame hash and session membership,
whole-frame reduction derived inside the guest, both conditioning rows and both renders bound, one pinned noise tensor
for both passes, integer weights, scales and arithmetic bound by digest, a final Groth16 proof with tampered controls).
The proving stack stayed SP1 6.4.0 with the CUDA prover and the explicit `.groth16()` path. The publishable claim was
fixed as execution binding and the list of things not to claim was written down (`CLAIM_BOUNDARY.md`). The cost
coefficients were corrected (54.6 GPU-hours covers the 257 fleet proofs; 0.0512 A100-hours per billion instructions) and
the recommended candidate, a dense width-16 network at 96 x 112, was trained alongside other lean candidates in the
G0 sweep on a rented eight-GPU node under the frozen ARM-C protocol evaluator.

**After round 2.** The programme switched to the ARM-C architecture cut to width 16 at 96 x 112, which had separated
correct from wrong conditioning on the frozen protocol (development validation, `RESULTS.md` section 1) where the leaner
families had not; the smaller ARM-C widths were kept running as candidates under the rule that only an actual integer
export meeting the per-session criteria could replace it. The integer gate was tightened: residual-unit error with
`D_q > 3η` on every pair, sign agreement counted by session and offset, and byte-exact oracle-to-Rust parity including
the residual sums; int16 weights became the first fidelity baseline; a fixed-point GroupNorm, table, softmax, pooling
and interpolation specification with overflow bounds was required. Three provenance gaps were closed: the trainer seeds
before model construction from the G0e sweep onwards (earlier sweeps' seed labels did not fix initial weights and are
recorded as such), the frozen evaluator's per-session noise stream positions were kept for every scored row, and the
cache's float16 step was included in the reference path. The attention products were added to the cost table. The
public description was fixed as "integer diffusion evaluator adapted from the frozen ARM-C protocol", with float and
integer results reported separately and the d2/v10 blocks named development validation.

**After round 3.** The integer contract was frozen for the final checkpoint (`oracle/final/README_FINAL.md`, its section 8
lists the dispositions): one effective scale map recorded from execution and asserted at every run, replacing a declared
table that disagreed on seven inherited-scale tensors; two rounding rules stated (conversion ties to even, runtime ties
toward positive infinity, exact left shift for non-positive shifts), with a Rust port required to import the frozen
tables rather than regenerate them; the admitted domain widened to the full int16 range with every clipping event counted
by name and the clipped table entries enumerated; static bounds recomputed from the authenticated constants with the
factor 32768 and exported; tie, endpoint, constant-group and border fixtures added; the exported noise bytes made
normative with the CUDA correspondence stated as approximate; the bilinear-promotion variant of the bf16 emulation
implemented and measured (indistinguishable at the 1.1e-3 level, recorded as unresolved); the width-12 arithmetic
specified; the whole artifact regenerated for the final checkpoint by one command and every comparison rerun; and the
README numbers corrected as listed.

**After round 4.** The Rust kernel crate was brought onto the FINAL contract (`source/FULL_GUEST.md` section 2.4): the
full int16 domain admitted with every out-of-domain clamp counted (the noising counterexample `C = noise = -32767 →
-39795 → -32768` became a test and a fixture); a 65,536-bit clipping mask per activation table, authenticated against
the oracle and consulted on every lookup; the transport updated to the FINAL artifact's filenames and arrays; every
fractional-bit field bounded at parse and every left shift checked to round-trip; the 42 differential boundary fixtures
generated from the oracle and run as tests; an offline cargo configuration inherited by every child build and a
reproducible build driver asserting the ELF size, digest and verifying key; the cycle figures corrected. The relation
guest was completed around the kernel crate: the constants blob hashed in circuit and its digest published, the offset
and mirror flag published, the noise BLAKE3 published, the clip count published, and the whole guest executed on four
August rows with byte-exact agreement against the native re-execution and the Python oracle.

**After round 5.** The mirrored-offset defect was fixed and regression-tested (`FULL_GUEST.md` section 11): the guest
validates direct and mirrored offsets together, so -30 is admitted exactly for the six rows whose base +30 leaves the
session and nowhere else; the rule became one pure function shared by the batch driver, the acceptance verifier and a
112-row regression test; a synthetic 40-row session with a -30 mirror ran through the complete guest. An acceptance
verifier was added that enforces the frozen expected identities (program key, circuit key, kind, constants, spec and
preprocessing digests, session, rule, per-row noise BLAKE3, chain-log digests, leaves, oracle residuals) rather than
deriving a key from whatever ELF is at hand; the normative noise mapping is enforced before execution and at acceptance.
The build driver became fail-closed (cargo's status preserved, fresh outputs asserted, environment and toolchain
identities recorded); the transfer and node runbook were repaired; receipts and manifests were given a schema that
supports independent completeness checks, retained attempts, outcome classes and durable writes, with a strict merger
that refuses incomplete or stale collections; negative controls were separated into relation rejections and policy
rejections, 23 witness-level and 12 proof-level; the saturation wording was fixed; the held-out description became the
claim boundary of `CLAIM_BOUNDARY.md`; the numbers were corrected. The ELF was then made path-independent
(`-Cstrip=symbols`) after the node reproduced its verifying key but not its file hash at a different absolute path, and
the final pin (ELF `51b7bc35…75cc`, 396,200 bytes, vkey `0x00f01894…a027`) was reproduced on the development machine, in
a copy of the sources at another absolute path, and on the node.

**After round 6.** The round found the batch evidence sound (112 of 112 proofs accepted on a fresh verification, every
table row, artifact digest, ladder row and agreement figure reconciled with its record, the principal pins and the claim
boundary honoured, the data-layer bundle consistent) and the package in need of revision. What changed: the prover logs
carrying the prover clients' exit diagnostics, the process listings and the sidecar logs were taken out of both
payloads under an explicit evidence allowlist (`receipts/README.md`), the node's ledger over its complete collection
staying in so the withheld originals remain pinned; a synthetic-session test statement described as a published outcome
was reworded (`RESULTS.md` section 4); the framed artifact size, stated as a constant 2,445 bytes, became the measured
distribution (2,444 to 2,447 bytes) and a mis-stated residual ratio was corrected (`RESULTS.md` section 3); the node's
final build record and its digest list were added (`source/node_prep/r5/`); the verification instructions were anchored to
a package root and given their full requirements, the standalone verifier was vendored at a pinned revision, and the
sequence was rehearsed on a copy of the published tree (`VERIFY.md`); the published oracle tree was made self-consistent
in its import paths and the regeneration claim narrowed to what the public rows allow (`REDACTION.md`, `VERIFY.md`
section 7); the two release scripts were repaired (root ledger generated outside the tree, counts interpolated where a
count belongs, snapshot-first validation, every downloaded object compared with the frozen pins, post-upload failures
classified as uncertain rather than as nothing sent); the data-layer README states which ledger covers which objects; the
operational context of the batch was added to `RESULTS.md` section 6; the remaining minor editorial corrections to the copied
prose were made; the title stayed with the first candidate.

**After the first outside reading (A1).** The three reports agreed on the obstacles: a reader with the package alone could verify nothing without a
network-fetched toolchain, could recompute no residual sum because the frames and the August tensors were held, and had to
infer the recording, the pattern, ARM-C, d2 and v10, the roles, the beacon rounds and most hashes from the source. What
changed: `GLOSSARY.md`, `HASHES.md`, `FAQ.md` and a primer in `README.md` were added; `STATEMENT.md` gained section 1a (the
shared beacon rounds) and the field notes the readers requested; `capsule/` was added with statically linked verifiers and
tested in a fresh container with no network; `tools/check_identities.py` and `tools/regen_noise.py` give a Python-only check
of every statement's identities and of the noise rule; `VERIFY.md` gained the toolchain download sources and hashes, the
offline route and the one-pull `replicate/` kit's facts; every inconsistency the readers listed in the copied records was
corrected in the published copies (`REDACTION.md`); `LICENSE` was added. The principal then decided (8 September, 16:40Z)
to publish the 112 raw frames and the August camera-derived tensors, so the re-execution of any row is part of the package
(`capsule/reexecute/`, `FRAMES.md`), and to publish the audit texts (`audits/`).

**After rounds 7 and 8 and the second reading.** The privacy sweep's dispositions were applied as summarised above and the
confirmation re-read's eleven REVISE findings closed. The second reading's three requests were met: the offline build kit on the
data layer (Codex: every locked crate and toolchain, hash-pinned; rehearsed in a container with no network, `VERIFY.md` section
2b), the last held-data sentences removed and one dated statement of what the release publishes (Claude and Grok; `FAQ.md` 49),
and `replicate.sh execute` and `prove` taking the shipped or a published frame by themselves. The remaining questions of the
second reading are answered in `FAQ.md` 65 to 78. This revision has not itself been re-read.

**After the second reading: the fresh-machine replication (8 September, 17:05Z to 18:07Z).** The test the readers' question
implied was run: the one-pull kit on a freshly launched Lambda A100-SXM4-40GB instance (Ubuntu 22.04.5, no toolchain installed)
against a local copy of the package as staged at 16:50Z. Every toolchain download arrived at its pinned digest, the guest rebuilt
to the pinned ELF and key, 112/112 proofs verified under both verifiers, row 600 re-executed to the identical statement on the CPU
and was re-proved on the GPU in 42.3 minutes, and the fresh proof was accepted cold under the pinned identities. The GPU prove
path thereby lost its [confirm] tag; the redacted log and the run's artefacts are published under `replicate/` (`VERIFY.md`
section 9, `replicate/TEST_LOG_LAMBDA_A100.md`).

**After round 9.** The eleven remaining items of desk text and infrastructure were removed from the copied records and their
classes added to the redaction rule and its residue check (`REDACTION.md`); `FRAMES.md` gained the participant disclosure; the
offline kit's upstream binaries were described as shipped downloads that keep their own build-path strings; `PINS.json`
separated published from as-recorded digests and placed the fixtures in the repository; `BUILD_KIT.md` renders its table and
total from the kit manifest; downloaded objects are made executable before use; the offline kit test was re-run against the
frozen sources with its inventory shipped; this document's round-8 counts were corrected.

**After round 10 and the third reading.** The redaction rule's phrase substitutions and residue checks match across line
breaks (two phrases had survived wrapped); the last operator-command wording in source comments reads "the release step", which
changed two host-source files and so the offline kit test was run again against the frozen sources (a fourth run; the
third had used a staging copy the release tooling left incompletely adapted, caught by comparing inventories); the data-layer upload
script takes its snapshot directory from the environment; `RELEASE.json` counts the kit manifest; and the third reading's
small inconsistencies were corrected (`HASHES.md`, `LARGE_FILES.md` against `replicate/README.md`, `VERIFY.md`, `GLOSSARY.md`,
`source/tools/python_oracle_rows.py`, `oracle/final/FREEZE_SUMMARY.md`, `tools/check_identities.py`,
`source/vectors_relation/README.md`). Codex's NO verdict rests on the data layer being elsewhere, and the two YES WITH EFFORT
verdicts carry the same reservation; `README.md` and `VERIFY.md` now say in one place that the publication is two-part and where
the bundle's controls are fixed. The third reading's residues (whole on-box paths surviving behind a redacted prefix, the
development machine's codename) are caught by rule; "round 7" has one meaning, the privacy sweep, and the outside readings are
A1 to A3; the eight policy-only rows are stated everywhere as `STATEMENT.md` section 7 states them; `FAQ.md` 79 to 83 answer
the reading's one-line questions. Rounds 9 and 10 and the third reading are published under `audits/`. This revision has not
itself been re-read.

## What was not audited before the proofs

The proofs themselves, the batch collection and this package were made after round 5 and audited in round 6, whose
dispositions are above; the round-6 revision was read by the three outside agents (first reading); the augmented package was
read by the second model in rounds 7 and 8 and by the three outside agents a second time, and its re-frozen successors in
rounds 9 and 10 and by the three readers a third time. The revision that applies round 10 and the third reading, the one
published here, has not itself been re-read; the changes it made are recorded in each document's Log,
`REDACTION.md` and the redaction ledgers. The node timing pilot ran on the round-4 ELF that round 5 superseded; its proof is not part of this package and only
its timing measurements are quoted, labelled as such (`RESULTS.md` section 5).

## Revisions

| revision | date | change | published as |
|---|---|---|---|
| 1.0 | 8 September 2026 | the package as audited through round 11 and read three times by the outside agents | Dark Lantern commit `d8cd9278a21dc636bb5c0233276d3cf4beeafd70`; data layer `results/zkdiff_august_20260907/v1/` (manifest `e1bca0243dda85d8431c9091ba81fb3313609123fc1b7730f9781bf210df3f88`) |
| 1.1 | 9 September 2026 | d2/v10 reference: `FAQ.md` 17 and `GLOSSARY.md` name the public Truth Beam session bundles of d2 and v10 (their locations, recording dates, frame counts, protocol versions and the frame path rule), which the package had called not decided at publication; the revision is recorded in `README.md`, this table and `PINS.json`; the package ledger and the root ledger are regenerated; nothing else changes | one commit on `d8cd9278…` (item 034) and the changed front-matter copies on the data layer (item 035), both staged for the publisher |

## Sources

The verdict lines are the closing lines of the verdict files, published as `audits/astra/r1_verdict.md` to `r6_verdict.md`
and `r8_verdict.md` to `r10_verdict.md` with their briefs beside them, and of the agent reports
`audits/agents/{claude,codex,grok}_r{1,2,3}.md`;
round 7's verdict line is quoted from the release desk's record, its text being unpublished. The dispositions are
`source/FULL_GUEST.md` sections 2.4 and 11, `oracle/final/README_FINAL.md` section 8, `source/armc-relation/RELATION.md`
Log, the round-1 and round-2 verdicts, and, for the later rounds, `FAQ.md`, `REDACTION.md` and the Log of every touched document.

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-07 | BOSUN | First version, rounds 1 to 5. |
| 1.1 | 2026-09-08 | BOSUN | Round 6 (the finished package) added with its dispositions. |
| 1.2 | 2026-09-08 | BOSUN | Round 7 (three outside agents, readability) added with verdict lines and dispositions; the round-6 findings' subjects listed; the audit texts published in audits/ by the principal's decision. |
| 1.3 | 2026-09-08 | BOSUN | Rounds 7 (privacy sweep) and 8 (confirmation re-read) and the outside agents' second reading added with verdict lines, subjects and dispositions; the agents' rows relabelled A1 and A2; the principal's handle in verdict lines reads "publication" as the published copies do. |
| 1.4 | 2026-09-08 | BOSUN | The fresh-machine replication of 8 September (Lambda A100-SXM4-40GB) recorded; FAQ range 65 to 78. |
| 1.5 | 2026-09-08 | BOSUN | Astra round 9: the round-8 counts corrected (11 REVISE, 8 PASS); the remaining unrehearsed steps; a quoted desk phrase neutralised. |
| 1.6 | 2026-09-08 | BOSUN | Astra rounds 9 and 10 and the third outside reading: table rows, what changed after each, sources. |
| 1.7 | 2026-09-08 | BOSUN | The third reading's Claude row; the first outside reading named as such (A1), not round 7; ten rounds. |
| 1.8 | 2026-09-08 | BOSUN | Astra round 11: the status line carries no counts (the table is the inventory). |
| 1.9 | 2026-09-09 | BOSUN | Revision 1.1: the Revisions section (1.0 as published, 1.1 the d2/v10 reference). |
