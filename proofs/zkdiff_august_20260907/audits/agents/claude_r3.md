> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

# Outside-agent readability audit, round three: "A Tale of Two Conditionings" (`the package root`)

Auditor: an outside AI agent (Claude), reading only the files under the package directory, 8 September 2026.

Method. Every top-level document was read in full (`README.md`, `CLAIM_BOUNDARY.md`, `STATEMENT.md`, `VERIFY.md`, `FAQ.md`,
`GLOSSARY.md`, `HASHES.md`, `RESULTS.md`, `FRAMES.md`, `REDACTION.md`, `AUDIT_TRAIL.md`, `LARGE_FILES.md`, `LICENSE`, `MODES`),
with `capsule/`, `replicate/`, `receipts/README.md`, `audits/README.md`, the six earlier agent reports, the Astra r6 and r8 briefs
and verdicts, the banners of the copied engineering records (`source/armc-relation/RELATION.md`, `source/FULL_GUEST.md`,
`oracle/final/README_FINAL.md`, `source/CYCLES.md`), the three Python tools, the capsule scripts, `build_reproducible.sh`, the
receipts of row 600 and the control records. Read-only commands were run over the package: `sha256sum -c` on the three ledgers,
`VERIFY.md` section 0's unlisted-files command, the `MODES` comparison, SHA-256 and BLAKE3 of every file whose digest is quoted
in prose, a recount of the drand statistics from the chain log, a cross-check of the `RESULTS.md` and `FRAMES.md` tables against
the statements, receipts, chain log and `PINS.json`, and the package's own `tools/decode_zbdiff01.py`, `tools/check_identities.py`
and `tools/regen_noise.py` (standard library and numpy; they write nothing). No shipped binary, build, proof or network command
was run. One slip to declare: an ad-hoc script of mine imported `tools/decode_zbdiff01.py` without `dont_write_bytecode`, which
created `tools/__pycache__/decode_zbdiff01.cpython-314.pyc`; I deleted it and re-ran the ledger and unlisted-files checks
(`LEDGER_OK`, `NO_UNLISTED_FILES`, 3,129 files, the 3,128 ledger entries plus `SHA256SUMS` itself), so the tree is as I found it.

What checked out, so the rest of this report does not repeat it: `SHA256SUMS` (3,128 entries), `capsule/SHA256SUMS` and
`capsule/reexecute/SHA256SUMS` verify; no file is unlisted; `MODES` matches the executable bits exactly; every digest quoted in
`README.md`, `VERIFY.md` section 4, `HASHES.md`, `capsule/README.md`, `capsule/reexecute/README.md`, `RESULTS.md` section 6,
`REDACTION.md`, `audits/README.md`, `FRAMES.md` (all 112 rows against the chain log, the receipts and `PINS.json` `frames`) and
`PINS.json` (`program`, `capsule.binaries`, `licence`, `redaction`, `batch.proofs` for all 112 rows, `noise_files` for all 112)
equals the file it names; all 249 `REDACTION_LEDGER.tsv` and all 357 `receipts/REDACTION_LEDGER.tsv` published digests match
the files present; the 112-row table of `RESULTS.md` agrees field by field with the decoded statements and the receipts
(including the prove minutes and the first sixteen hex digits of both digests); `check_identities.py` reports 112/112 and
`regen_noise.py` 112/112 from the package alone; the drand counts of `STATEMENT.md` section 1a (646 of 711 pairs, 66 rounds,
2 to 19 rows per round with median 9, 10 rounds across the proof set, 103 of 112 sharing a round, the nine exceptions, row 600's
round 31521690 twice, staleness 1,363 to 10,799 ms, spacing 395.004/400.051/533.827 ms) reproduce from `chain_log.csv`; the
framed-proof size histogram (2,444 x1, 2,445 x12, 2,446 x59, 2,447 x40) is what `ls` gives; `capsule/reexecute/frame_000600.raw`
hashes to the chain log's BLAKE3 `9d4a0745…7d4a` and the receipt's SHA-256 `5c8e7856…211c`. No IP address, e-mail address or
terminal control byte exists in any text file of the package, and `strings` finds no `/home`, `/lambda` or staging path in the
three static binaries or the checkpoint.

---

## 1. What I understood the package claims

1. For each of the 112 rows 600 to 711 of the 712-row projector-camera session of 22 August 2026 there is one SP1 6.4.0 Groth16
   proof (356 raw bytes, 752-byte public statement) that "an integer diffusion denoiser, adapted from the frozen ARM-C protocol and
   run in exact fixed point, produced the published residual sums on the whole sensor frame of that row" once under the row's own
   emission pattern and once under the emission of a wrong row chosen by the declared rule `OFFSETS[(r - 600) mod 5]` with boundary
   mirroring (`README.md:14-22`; `STATEMENT.md:18-36`, `:195`; `CLAIM_BOUNDARY.md:15`).
2. Every input is bound inside the proof rather than trusted: the raw frame is hashed in circuit and opened to the committed
   session tree, the chain state is re-derived from the previous row's record under verified drand quicknet signatures, both
   patterns are re-rendered from their chain states, the noise tensor is bound by its BLAKE3 and the network constants by their
   SHA-256, and the statement "carries no pixels" (`README.md:17-23`; `STATEMENT.md:22-36`, `:104`; `HASHES.md:16-57`).
3. All 112 proofs "verified and accepted under the frozen identities: 112 positive, 0 zero and 0 negative signed outcomes; 0 rows
   with a nonzero clip count", with `D = R_wrong - R_correct` in MSE units between 0.007328 and 0.010988, median 0.009161
   (`README.md:11`, `:63`; `RESULTS.md:203`, `:328`).
4. The proof rows gave no gradient to weight training, but seven of them (and fourteen conditioning identities) calibrated the
   integer scales and four were scored by the trainer's quick screen, so they "must not be described as an untouched test set";
   the d2 and v10 evaluation blocks are "development validation" (`CLAIM_BOUNDARY.md:17`, `:23-31`; `README.md:52-55`).
5. The claim is execution binding and nothing wider: the proofs "establish no physical-capture, realness, liveness,
   illumination-causality, adversarial-resistance or unseen-session-generalisation claim", "do not reproduce the original published
   checkpoint, five-offset aggregate, eight-seed AUROC or full diffusion sampling", and the noise is bound as normative bytes, not by
   a generator (`CLAIM_BOUNDARY.md:19`; `README.md:64`, `:126-131`; `STATEMENT.md:239-245`).

---

## 2. The verification path

`P` is the absolute path of the package (`VERIFY.md:29-36`). "Plain" means the exact command is printed in the package at the
place cited; "implied" means the reader must compose it from parts.

### (a) Verify one proof (row 600)

| # | step | command | stated? where |
|---|---|---|---|
| a0 | ledger | `(cd "$P" && sha256sum -c --quiet SHA256SUMS && echo LEDGER_OK)` then the unlisted-files command | plain, `VERIFY.md:46-61`; `README.md:136` |
| a1 | verifier identity, no toolchain | `"$P/capsule/zkdiff-verify" --identity` (expects ELF `51b7bc35…75cc`, circuit key `4388a21c…e696`, `v6.1.0`) | plain for the source-built binary at `VERIFY.md:182-188`; for the capsule binary only inside `capsule/verify_offline.sh:28-32` |
| a2 | full acceptance of one framed proof | `"$P/capsule/zkdiff-verify" --proof "$P/proofs/row_000600_groth16.bin" --expect "$P/source/expected_identities_august.json" --report /tmp/row_000600.verify.json`; stdout ends `verified_and_accepted=true`; 35 checks PASS | plain with the rebuilt binary `$S/zkdiff-verify` (`VERIFY.md:182-189`); with the capsule binary it is implied by `VERIFY.md:249-258` ("One script runs both routes") and by the loop in `capsule/verify_offline.sh:37-51`, never written out as a single command |
| a3 | the raw form | `… --proof-bytes "$P/proofs/row_000600_groth16_proof.bin" --public "$P/public_values/row_000600_public_values.bin" --expect …` | plain, `VERIFY.md:192-194`; capsule form in `verify_offline.sh:57-59` |
| a4 | Groth16 layer alone | `"$P/capsule/zeebeam-standalone-verifier" "$P/proofs/row_000600_groth16_proof.bin" "$P/public_values/row_000600_public_values.bin" 0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027`; ends `tamper_public_byte_87_rejected=true`, `wrong_vkey_rejected=true`, `VERIFIED` | plain for the cargo-built binary (`VERIFY.md:80-91`); the capsule binary form is inside `verify_offline.sh:62-67` |
| a5 | read the statement | `python3 "$P/tools/decode_zbdiff01.py" "$P/public_values/row_000600_public_values.bin"` and compare with `RESULTS.md:215` and the receipt's `decoded` object | plain, `VERIFY.md:283-291`; I ran it: row 600, wrong row 598, offset -2 direct, 4,435,539,299 / 11,254,163,581, no framing problems |
| a6 | negative controls | `… --proof … --expect … --controls --report /tmp/controls.json` (18 controls: 12 relation, 6 policy) | plain, `VERIFY.md:209-213`; the node's record is `receipts/proof_controls.json` |

Everything a1 to a6 needs is in the package for x86-64 Linux, trusting the shipped static binaries (`capsule/README.md:76-80`
says so plainly) or rebuilding them under (c).

### (b) Verify all 112

| # | step | command | stated? where |
|---|---|---|---|
| b1 | both routes, offline | `bash "$P/capsule/verify_offline.sh"`; exit 0 means 112/112 accepted by `zkdiff-verify`, 112/112 `VERIFIED` by the standalone verifier, 18 controls, raw form, copies equal to the package's | plain, `VERIFY.md:257-265`; `capsule/README.md:16-26`; `README.md:75` |
| b2 | identities without a binary | `python3 "$P/tools/check_identities.py" "$P"` | plain, `VERIFY.md:296-300`; I ran it: 112/112, exit 0 |
| b3 | the noise rule | `python3 "$P/tools/regen_noise.py" "$P"` (numpy; `blake3` module optional) | plain, `VERIFY.md:323-328`; I ran it: 112/112 |
| b4 | source-built loops | the `for` loops of `VERIFY.md:93-97` (standalone) and `:198-202` (acceptance), each asserting `n -eq 112` | plain |

### (c) Rebuild the program and compare its identity to the pinned one

| # | step | command | stated? where |
|---|---|---|---|
| c1 | OS packages and toolchain | `build-essential pkg-config`, Rust 1.98.0 via rustup 1.29.1, `sp1up --version v6.4.0` (or the tarballs), `protoc` 21.12 with includes, GNU `time`, binutils; every download URL with SHA-256 and size | plain, `VERIFY.md:113-147` (table at `:135-143`); `replicate.sh:59-97` carries the same pins |
| c2 | crates | the five `cargo fetch --locked` commands (no `--target` on the guest fetch; the two nested `sp1-core-executor-runner*` trees) | plain, `VERIFY.md:149-167`, with the reasons from `replicate/TEST_LOG.md:42-75` |
| c3 | build and assert | `(cd "$P/source/armc-relation" && ./build_reproducible.sh)`; last line `BUILD_REPRODUCED_OK sha256=51b7bc35…75cc vkey=0x00f01894…a027 bytes=396200 groth16_vk_sha256=4388a21c…e696 circuit=v6.1.0` | plain, `VERIFY.md:170-179`; the pins are hard-coded and asserted at `build_reproducible.sh:15-18`, `:105-109` |
| c4 | compare | `"$P/source/armc-relation/script/target/release/zkdiff-verify" --identity` against `PINS.json` `program`, `source/expected_identities_august.json` lines 4 to 8, `capsule/BUILD_RECORD.txt:51-54`, `source/node_prep/r5/build_record_20260907T215855Z.txt`, `receipts/gpu0_inputs_identity_launch.txt` | plain, `VERIFY.md:182-188`, `:345-358` |
| c5 | with no network | the offline build kit (`build_kit/` on the data layer, 26 files, 9,279,781,352 bytes, manifest `ebb4c4ca…246b`): extract the vendored crates into a `CARGO_HOME`, install the six toolchain downloads offline, run `build_reproducible.sh` unchanged | paraphrased in `VERIFY.md:215-247`; the procedure itself is `build_kit/BUILD_KIT.md`, which is not in the package |
| c6 | one pull | `"$P/replicate/replicate.sh" --from-local "$P" --repo-only build` | the subcommand and options are plain (`replicate/README.md:23`, `:150-154`); this exact composition is mine |

Rehearsed on two machines, at two absolute paths, in a fresh container from an empty cargo home, from the offline kit twice, and
on a freshly rented A100 box (`VERIFY.md:345-358`, `:477-550`; `replicate/TEST_LOG.md`; `replicate/TEST_LOG_LAMBDA_A100.md`).

### (d) Reproduce one row's residual sums

| # | route | command | stated? where |
|---|---|---|---|
| d1 | row 600, no toolchain | `bash "$P/capsule/reexecute/reexecute_row.sh"` (about 17 GB RAM, 4 to 7 minutes; `cmp`s the recomputed 752 bytes with `public_values/row_000600_public_values.bin`) | plain, `VERIFY.md:272-274`; `capsule/README.md:61-64`; `reexecute_row.sh:8-10`, `:48` |
| d2 | any other row | download `results/zkdiff_august_20260907/v1/frames/frame_NNNNNN.raw` from `https://data.truthbeam.com/`, check it against `FRAMES.md`, then `bash "$P/capsule/reexecute/reexecute_row.sh" 684 --frames-dir /path/to/frames` | plain, `FRAMES.md:25-30`; `VERIFY.md:272-278` (rehearsed for 684) |
| d3 | independent Python implementation | `(cd "$P/source" && python3 -B tools/python_oracle_rows.py 600 684)` with torch, numpy and the data-layer `oracle/final/august_inputs/row_NNNNNN.npz` and d2 vector sets placed (for row 600 alone, copy `capsule/reexecute/row_000600.npz` into place, `FAQ.md:397-401`) | plain, `VERIFY.md:438-445`; needs the data layer in any case, as `FAQ.md` 70 says |
| d4 | through the kit | `replicate.sh execute ROW [--frame PATH]` (shipped frame for 600, else fetched and checked against `FRAMES.md`) | plain, `replicate/README.md:25`; `replicate.sh:11-13` |

### (e) Reproduce a proof

| # | step | command | stated? where |
|---|---|---|---|
| e1 | GPU stack | `replicate.sh toolchain gpu`: `sp1-gpu-server` 6.4.0 (binary `f68b85dc…d97c`) and the Groth16 v6.1.0 circuit cache (6,211,807,514-byte tarball, SHA-256 `18beebb6…7810`, seven files pinned) into `~/.sp1`; an A100-class card (peak about 28.5 GiB) | plain, `replicate/README.md:59-66`; `VERIFY.md:141-147`, `:224-226` |
| e2 | prove | `./replicate.sh prove 600 --device 0` (frame shipped for 600; any other row fetches its published frame) | plain, `replicate/README.md:52-56`; the node's own command is the `command` field of `receipts/row_000600_receipt.json` |
| e3 | what to expect | a fresh 2,44x-byte artifact with different proof bytes and the identical 752 public bytes, accepted cold under all 35 checks; about 42 to 46 minutes on one A100, 61 to 67 with eight sharing a node; the pinned `sp1-cuda` client exits 134 after writing the receipt | plain, `FAQ.md` 51 and 78; `VERIFY.md:548-554`; `RESULTS.md:185-198`; rehearsed once on a rented A100-SXM4-40GB |

---

## 3. Questions I could not answer from the package alone

`FAQ.md` was checked first; none of the following is answered there (1 to 78).

1. **What was "Astra round 9"?** Five Logs cite it (`FAQ.md:451`, `VERIFY.md:565`, `HASHES.md:98`, `REDACTION.md:140`,
   `AUDIT_TRAIL.md:234`) and `REDACTION.md:23` attributes the stripping of terminal colour codes to it, but `AUDIT_TRAIL.md`'s
   table (`:28-43`) ends at round 8, `audits/astra/` has no `r9_*` files, `README.md:70` says Astra "audited the work in eight
   rounds", and `AUDIT_TRAIL.md:4` says "the eight second-model audit rounds". Its verdict line and findings are nowhere. Expected in
   `AUDIT_TRAIL.md` and `audits/README.md`.
2. **What is "round 7b"?** `LARGE_FILES.md:31` cites "`AUDIT_TRAIL.md` round 7b and round 9"; neither label exists in
   `AUDIT_TRAIL.md`. Expected in `AUDIT_TRAIL.md`.
3. **Which data-layer byte total is right?** `LARGE_FILES.md:59`: "4664 files, 633,286,043 bytes in all";
   `replicate/README.md:21` and `:47`: "633,315,259 bytes of data-layer files (`LARGE_FILES.md`)". The difference is 29,216
   bytes. `LARGE_FILES_SHA256SUMS` carries no sizes, so the package cannot settle it. Expected in `LARGE_FILES.md`.
4. **Why do acceptance reports count 35 checks in verify mode and 33 in execute mode?** `RESULTS.md:172` and
   `VERIFY.md:548` say "33 checks" for the re-executions; `VERIFY.md:243`, `:550` and `replicate/TEST_LOG.md:90` say 35. From the
   receipts I can see the two absent in execute mode are `circuit.groth16_vk_sha256` and `groth16.verify`, which is sensible
   (nothing was proved), but no document says so. Expected in `STATEMENT.md` section 9 or `receipts/README.md`.
5. **Four or eight "policy-only" rows?** `VERIFY.md:102` and `FAQ.md:214-215` speak of "the four policy-only rows (698, 703,
   708, 711)"; `STATEMENT.md:202-204` says "Eight rows admit a coherent alternative flag under the generic check alone (697, 702,
   707, 710 flipped to mirrored; 698, 703, 708, 711 flipped to direct)", and `source/armc-relation/relation/src/rule.rs:149-150`
   asserts "the policy-only rows are exactly those eight". Which set does the standalone route fail to distinguish? By the source,
   all eight. Expected in `STATEMENT.md` section 7 and `VERIFY.md` section 1.
6. **Of what bytes are the provenance digests inside the frozen table's `sources` block?** `source/expected_identities_august.json`
   `sources.build_record.sha256` is `f09c8dae…`, but the published `source/armc-relation/runs/build_record_20260907T214246Z.txt`
   hashes to `ac451a7b…` (`REDACTION_LEDGER.tsv:205` shows `f09c8dae…` is the private digest); `sources.g1_manifest.sha256` is
   `3e69c6cd…`, the private digest of `oracle/final/august_inputs/manifest.json` (published `95fcf7ec…`, `REDACTION.md:85`).
   `HASHES.md:27` and `PINS.json` `path_conventions` say the block's paths were redacted; nothing says its digests are of the
   pre-redaction bytes (`FAQ.md` 71 covers `prepare_manifest` only). Expected in `HASHES.md` or `PINS.json` `path_conventions`.
7. **What is the ZeeBeam row-96 artifact used for the twelve proof-level relation controls, and where can it be obtained?**
   `RESULTS.md:180-182` names "the ZeeBeam row-96 proof"; `source/logs/verify_groth16_only_row096_20260907.json:2-4` records a
   2,779-byte artifact, SHA-256 `62f113ec…f936`, at a private path. It is not in the package and the ZeeBeam release path is not
   given. Expected in `RESULTS.md` section 4.
8. **Can the checkpoint be retrained from published material?** The trainer (`oracle/trainer/train_lean.py`), `train.log` and
   the evaluation-row caches are published, but the frames of rows 0 to 599 are not (`FRAMES.md:15`), the d2 and v10 frames are
   not, and whether the training-block caches (4,432 + 3,003 + 600 rows) are among the data-layer `oracle/rows/` files
   (`LARGE_FILES.md:53-57` lists 324 d2, 120 v10 and 232 August files) is not stated. Expected in `RESULTS.md` section 1 or
   `LARGE_FILES.md`.
9. **What exactly does the offline build kit's procedure run?** `VERIFY.md:227-230` paraphrases it (`crates/offline_cargo_home.sh`,
   `rustup-init --default-toolchain none`, `rustup toolchain link`); the procedure, `build_kit/BUILD_KIT.md`, its section 7 on
   third-party terms, `frames/README.md`, the prefix `README.md` and `_control/RELEASE.json` all live only on the data layer.
   Expected in `VERIFY.md` section 2b or as a copy in `replicate/`.
10. **Is the `frames/FRAMES.json` pin current?** `PINS.json` `frames.frames_json_sha256_in_bundle` reads `6247f41b…143fc`;
    Astra round 8 finding 4 (`audits/astra/r8_verdict.md:13`) found an earlier pin stale (`eea81f67…` against an actual
    `5350e485…`), so this is the third value, and the file it pins is not in the package. Expected in `FRAMES.md`.
11. **What are "transmit item 033" and "032", and what is "the release desk"?** `LARGE_FILES.md:11` ("transmit item 033"),
    `AUDIT_TRAIL.md:37` ("fix 033's overriding stdin redirection"), `audits/astra/r6_brief.md:16-19` and `r8_brief.md:9` use them
    without definition; `GLOSSARY.md` has no entry. Expected in `GLOSSARY.md`.
12. **Why does the audit table date round 8 (18:01) before round 7 (18:08)?** `AUDIT_TRAIL.md:36-37`. Were the privacy sweep and
    the confirmation re-read run concurrently on the same bytes, and did round 8 see round 7's dispositions? Expected in
    `AUDIT_TRAIL.md`.
13. **How much memory does the development machine have, and does it have a GPU?** `GLOSSARY.md:254-255`: "16 cores, 128 GB
    RAM"; `replicate/TEST_LOG.md:16`: "32 threads, 91 GiB RAM"; `source/CYCLES.md:244`: "91 GiB visible";
    `source/armc-relation/RELATION.md:377`: "(no GPU, no Go)"; `replicate/TEST_LOG.md:26`: "the development machine's 5090 is not a
    proving target". The 17 GB re-execution footprint is stated against the smaller figure. Expected in `GLOSSARY.md`.
14. **Does anything in the package let a reader confirm that `deps/BOSUN/scratch/…/b3xof_experiment_snapshot/…`
    (`source/armc-relation/b3xof/PROVENANCE.md:11`; `RELATION.md:223`) is a path inside the public ZeeBeam repository bundle rather
    than an on-box path?** `FAQ.md` 63 asserts it; only a clone of that repository could show it. Expected in `PROVENANCE.md`.
15. **What do the `[derived]`, `[confirm]`, `[measured]` and `[estimate]` tags mean where they appear outside the file that defines
    them?** `RESULTS.md:61` and `FAQ.md:192` use `**[derived]**`; `VERIFY.md:38` defines `[confirm]` only; the full tag set is
    defined in `source/FULL_GUEST.md:22-24`. Expected in `GLOSSARY.md`.

Items 7, 8, 9 and 10 are inherent to a repository-plus-data-layer split and are listed for completeness; 1 to 6 and 11 to 13 are
internal inconsistencies the package could settle in a line each.

---

## 4. Obstacles, ranked by severity

Severity 1 (would send a careful agent down the wrong path, or leaves a published statement undeterminable)

1. **The audit history's numbering contradicts itself.** "Round 7" means the outside agents' readability reading in
   `GLOSSARY.md:4`, `HASHES.md:4`, `FAQ.md:448`, `capsule/README.md:11` ("`AUDIT_TRAIL.md` round 7, Codex"), `VERIFY.md:504`
   and `AUDIT_TRAIL.md:181` ("**After round 7.** The three reports agreed…"), but the privacy sweep in `AUDIT_TRAIL.md`'s own
   table (`:36`), where the agents are rows `A1` and `A2`. A ninth Astra round is cited in five Logs and `REDACTION.md:23` but
   recorded nowhere (question 1); "round 7b" exists nowhere (question 2); `README.md:70` and `AUDIT_TRAIL.md:4` count eight.
   The document whose job is to make the history legible ("with their verdict lines and what changed after each",
   `README.md:93`) cannot be reconciled with the Logs that cite it.
2. **Two documents state two byte totals for the same data-layer set** (question 3). A reader who fetches the set and finds
   633,286,043 bytes will believe `replicate/README.md:21` describes a different upload, or the reverse.

Severity 2 (misleads or stalls a careful reader)

3. **The scope of what the standalone route cannot detect is misstated.** `VERIFY.md:102` and `FAQ.md:214-218` say four rows;
   `STATEMENT.md:202-204` and `rule.rs:149-150` say eight (question 5). Since `VERIFY.md` section 1 is the route a Rust-only
   reader takes, the smaller number understates what only the acceptance verifier catches.
4. **Provenance digests inside the frozen identities table point at private bytes** (question 6). A reader who hashes
   `build_record_20260907T214246Z.txt` or `august_inputs/manifest.json` and compares with the table's `sources` block gets a
   mismatch with no in-package explanation; `HASHES.md:27` explains only why the table's own digest differs.
5. **A malformed path in a copied manifest.** `source/vectors_relation/MANIFEST.json:561`: `"path":
   "oracle/rows[preprocessed-row cache]/d2/C_001328.npy"`: the redaction placeholder was inserted mid-path, so the string is
   neither the published locator `oracle/rows/d2/C_001328.npy` nor a clean placeholder.
6. **The 33-against-35 check counts are never explained** (question 4); an agent comparing a re-execution report with an
   acceptance report has to infer which two checks are absent.
7. **`GLOSSARY.md` promises "every term and acronym used in the prose of this package" (`:4`) and does not deliver it.**
   Used in the top-level prose without a glossary entry: ABI (explained only inside `FAQ.md:78`), BLS (named but not expanded),
   RSS (`RESULTS.md:194`), gnark (`RESULTS.md:192-193`), Box-Muller (`STATEMENT.md:215`), bf16 and autocast (`RESULTS.md:19`),
   GenICam and Aravis (`FAQ.md:108-109`, `README.md:29`), LLVM, static-pie, rustup, crates.io, UUID, the `[derived]` tag
   (question 15). The roles of most are clear from context; the promise is the problem.
8. **Historical records are left saying the GPU path is untested.** `replicate/TEST_LOG.md:26` and `:174` say "GPU path:
   **[untested here]**"; the banner at `:10-13` does not mention the later Lambda rehearsal that `TEST_LOG_LAMBDA_A100.md`, beside
   it, records. A reader of the first file alone stops early.
9. **The single-proof capsule commands are never written out.** `VERIFY.md` sections 1 and 2 print the single-proof commands with
   the cargo-built binaries (`$S/zkdiff-verify`, `target/release/zeebeam-standalone-verifier`); the capsule route offers only the
   all-112 script (`VERIFY.md:257`; `capsule/README.md:17`), so a reader who wants one proof, offline, has to lift the command out
   of `verify_offline.sh:39` or `:64`.

Severity 3 (friction)

10. `receipts/README.md:109` still lists "the 10 published files … not in the ledger" with a trailing "…" after six names.
11. `tools/check_identities.py:8` and `:70` say "the owner rule"; every other published text reads "declared offset rule"
    (`REDACTION.md:63`); `GLOSSARY.md:239` covers copied records, but this tool was written for the package.
12. `receipts/independent_verify/row_000600.verify.json` `artifact` reads `source/batch/node_runs/gpu0/row_000600/…`, a locator
    that resolves nowhere (there is no `source/batch/`); `receipts/README.md:131-133` says this of the receipts' paths but not of
    the development machine's reports.
13. `STATEMENT.md:65`, `GLOSSARY.md:59` and `PINS.json` `drand.drand_staleness_ms_min_median_max` give the median staleness as
    6,100 ms; over the 712 values of `chain_log.csv` the median (mean of the 356th and 357th) is 6,099.5 ms. Immaterial, but a
    reader who recomputes it will pause.
14. The evidence policy withholds `nvidia_smi_sidecar.pid` as "a process id" (`receipts/README.md:80`) while
    `receipts/launch_schedule.txt:2-10` publishes nine process ids; harmless, but the stated rationale does not hold.
15. Reading load: eighteen top-level documents, a 628-line `FULL_GUEST.md`, a 433-line `RELATION.md` and a 435-line
    `README_FINAL.md`, each frozen at a different hour with a banner; the reader reconstructs the chronology from the Logs. The
    banners are good; a one-table timeline in `AUDIT_TRAIL.md` (revision, time, what changed, who read it) would replace much of it.

---

## 5. Private operator infrastructure, personal data, on-box paths, internal instructions, control bytes

None of the following is an IP address, credential or control byte (none exists in the package). Items 1 to 4 are residues the
package's own redaction rule (`REDACTION.md:12-17`) says should not be there; items 5 to 11 are disclosed or deliberate and are
listed so the caller can judge them.

1. `source/logs/verify_groth16_only_row096_20260907.json:2`, `source/logs/verify_groth16_only_row096_final_20260907.json:2`,
   `source/logs/verify_groth16_only_row096_20260907.stdout:2`: `"artifact":
   "[private development path]"`. The home
   prefix is redacted; the on-box directory layout after it (`Documents/BOSUN/scratch/joined_build_20260901/…`) is not.
2. `source/vectors_relation/MANIFEST.json:565`: `"[private development path]"`. Same pattern.
3. `replicate/TEST_LOG.md:181` ("the development machine's root was at 12 GB free at the end"), `source/tools/make_sha256sums_g2d.sh:5`
   ("the development machine's build artefacts"), `source/CYCLES.md:244` ("the development machine had 91 GiB visible"), `source/armc-relation/RELATION.md:377`
   ("the development machine (no GPU, no Go)"): the development machine's private codename, which `REDACTION.md:12-13` says is replaced by a role
   label everywhere.
4. `source/armc-relation/b3xof/PROVENANCE.md:11` and `source/armc-relation/RELATION.md:223`:
   `deps/BOSUN/scratch/zeebeam_lambda_artifacts_20260824/reviews/post_hold_followup_closure_20260825T0446Z/…`. `FAQ.md` 63 says
   this is a path inside the public ZeeBeam bundle, in which case it is already public; it still exposes the `BOSUN/scratch`
   layout and cannot be checked offline (question 14).
5. `replicate/TEST_LOG_LAMBDA_A100.md:73` (`GPU-54def825-67ad-1d7d-19d2-84ee7fd4fbb9`, declared "left as recorded" at `:14`),
   `replicate/lambda_a100_20260908/prove_600/gpu_identity.csv` and `receipts/gpu0_gpu_identity.csv` to `gpu7_gpu_identity.csv`
   (GPU UUIDs and PCI bus ids of the rented node): hardware identifiers of rented machines; disclosed by `receipts/README.md:34`.
6. `PINS.json` `prover_node.instance`: "Lambda gpu_8x_a100_80gb_sxm4, us-east-1, driver 570.148.08 …": cloud vendor, instance
   type and region; disclosed.
7. `receipts/launch_schedule.txt:2-10` and every `attempt_id` (for example `20260907T221500Z-prover-node-163253`): process ids of
   the node; trivial, but see obstacle 14.
8. `audits/astra/r1_brief.md:36`, `:66` and `r1_verdict.md:46-52`, `:141`, `:163`: hourly GPU prices and the spend budget
   ("$22.32/h … under about $1,000"). `AUDIT_TRAIL.md:93-94` records these as deliberate KEEP items.
9. `audits/astra/r6_brief.md:16-19` and `r8_brief.md:9`: names of unpublished internal release-desk artefacts and scripts
   (`transmit_drafts/032_zkdiff_darklantern_commit.{sh,body.md,preview.md}`, `033_zkdiff_r2_bundle.*`, `SHELF_LINE.md`,
   `OPEN_ITEMS.md`, `TITLE_CANDIDATES.json`, `ASTRA_R6_APPLIED.md`, `release_pkg/`, `g2_guest/batch/BATCH_REPORT.md`), and
   `LARGE_FILES.md:11` ("transmit item 033"). These briefs are, by nature, internal instructions to a model; `audits/README.md:11-14`
   declares their publication and redaction, but the references mean nothing to an outside reader (question 11).
10. `source/FULL_GUEST.md:474-478` and `source/node_prep/G2D_NODE_RUNBOOK.sh:8`, `:129`: `ssh`/`rsync` operational commands with
    `[node user]@[node address]` placeholders: an internal runbook, published deliberately with the placeholders in place.
11. `model/g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pubproto_eval.json:2`: `"checkpoint":
    "experiments/zk_lean_20260907/…/latest.pt"`, a relative path of the node's private experiment tree; trivial.
12. Personal data, disclosed: `capsule/reexecute/frame_000600.raw` is a photograph of a masked participant in a recognisable
    indoor setting, shipped inside the package by the principal's decision and described as not anonymised
    (`FRAMES.md:17-22`; `capsule/reexecute/README.md:15-18`; `README.md:32`). The principal's name appears twenty times as the
    stated author and licensor. Nothing else personal was found.

---

## 6. Three things the package does well

1. **It is internally consistent where it counts, and it lets a reader prove that without trusting anyone.** Every digest quoted
   in prose that I could hash matched (the constants blob, both copies of the expected identities, the chain log by SHA-256, the
   three static binaries, the circuit key, the checkpoint, the merged manifest, the licence, the row-600 frame and inputs, every
   proof and statement, all 112 noise files, all 249 + 357 redaction-ledger entries, the audit copies); the 112-row table agrees
   with the statements and receipts to the last digit; and `tools/check_identities.py` and `tools/regen_noise.py` reproduce the
   identity half of the acceptance check and the noise rule with Python alone, in seconds, from the package alone.
2. **The claim boundary is fixed before the evidence and enforced by construction.** `CLAIM_BOUNDARY.md:10-19` quotes the three
   paragraphs verbatim with the rule that "a sentence elsewhere that seems to say more than they do is to be read as saying no
   more"; the calibration and quick-screen disclosures name the rows; the acceptance verifier "never derives a key from an ELF it
   is handed" (`STATEMENT.md:235`); the negative controls are split into relation and policy layers with their error text kept;
   and the six earlier outside reports, three of them with verdict `NO`, are published verbatim with the answers in `FAQ.md`.
3. **Every route is rehearsed and the rehearsal is on the record with numbers.** Static verifiers tested in a `--network none`
   container, a row re-executed from its frame and `cmp`'d byte for byte, a rebuild reproducing the ELF on two machines, at two
   paths, from an empty cargo home and from an offline kit, and one fresh proof made on a machine that started with nothing
   (`VERIFY.md` section 9; `replicate/TEST_LOG_LAMBDA_A100.md`), with the two remaining unrehearsed steps tagged where they stand.

---

## 7. Verdict

**YES WITH EFFORT.** With this package alone, on x86-64 Linux with about 17 GB of RAM and no network, an agent can verify all
112 Groth16 proofs under the pinned key and every frozen identity, cross-check every statement and regenerate the noise in Python,
and recompute row 600's residual sums from its raw frame; rebuilding the program, recomputing the other 111 rows and re-proving are
fully pinned and rehearsed but need the network or the data layer and, for proving, an A100-class GPU. **Single most important
fix:** make the audit bookkeeping agree with itself, by recording the ninth Astra round (cited in `FAQ.md:451`, `VERIFY.md:565`,
`HASHES.md:98`, `REDACTION.md:23`, `:140`, `AUDIT_TRAIL.md:234`) and the "round 7b" of `LARGE_FILES.md:31` in `AUDIT_TRAIL.md`'s
table and `audits/`, and giving "round 7" one meaning across `GLOSSARY.md:4`, `HASHES.md:4`, `capsule/README.md:11`,
`VERIFY.md:504` and `AUDIT_TRAIL.md:36`, `:181`; then correct `VERIFY.md:102` and `FAQ.md:214` to the eight policy-only rows of
`STATEMENT.md:202-204`, and strip the four `Documents/BOSUN/scratch` and "the development machine" residues of section 5 before publication.
