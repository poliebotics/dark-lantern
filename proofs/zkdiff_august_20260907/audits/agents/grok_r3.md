> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

# Outside-agent audit of the zkdiff August proof package

Read-only pass over `the package root`. No files were modified. No verifier, rebuild, residual recompute, or proof was run. Commands below are taken from the package; whether they would succeed is judged from the files, not from execution.

---

## 1. What I understood the package claims, in five plain sentences

**1.** For each of the 112 August rows 600–711 of the 712-row projector-camera session of 22 August 2026, one SP1 6.4.0 Groth16 proof (356-byte raw proof, 752-byte public statement, no pixels) is said to establish that a frozen integer diffusion evaluator, adapted from the ARM-C protocol, produced the published residual sums on the whole sensor frame of that row under the row’s own emission and under a declared wrong row’s emission.

Stated: `README.md` lines 8–24 and 57–64; `CLAIM_BOUNDARY.md` lines 15–16 (“We publish one independently verified Groth16 proof for each August target row 600–711… Each proof establishes execution binding of an integer diffusion evaluator adapted from the frozen ARM-C protocol”).

**2.** All 112 proofs are said to have been verified and accepted under frozen identities, with 112 positive signed outcomes, 0 zero, 0 negative, and 0 rows with a nonzero clip count.

Stated: `README.md` lines 10–12 (“112 proofs, one per row 600 to 711, every one verified and accepted under the frozen identities: 112 positive, 0 zero and 0 negative signed outcomes; 0 rows with a nonzero clip count”); `RESULTS.md` lines 202–204 and 328.

**3.** An accepting proof under the pinned program verifying key `0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027`, guest ELF SHA-256 `51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc` (396,200 bytes), and constants blob SHA-256 `73310ddab603cab5588d05e9ac4deb7e56466a6fae4bbf89244c32f2bd1a8b92` is said to establish only that the published `R_correct`, `R_wrong`, and `D = R_wrong - R_correct` are what that frozen integer network produced on the committed frame bytes, with the published clip count.

Stated: `README.md` lines 111–122; `VERIFY.md` lines 467–475; `STATEMENT.md` lines 237–245.

**4.** The three paragraphs of `CLAIM_BOUNDARY.md` govern every other sentence: the proofs “establish the specified integer computations and bindings” and “establish no physical-capture, realness, liveness, illumination-causality, adversarial-resistance or unseen-session-generalisation claim”; they “do not reproduce the original published checkpoint, five-offset aggregate, eight-seed AUROC or full diffusion sampling”; “Noise generation remains external provenance; the proof binds the normative bytes and computes forward noising.”

Stated: `CLAIM_BOUNDARY.md` lines 10–19; `README.md` lines 125–131.

**5.** August rows 600–711 “were held out from weight training”; “quantisation calibration used seven targets from this set and their own/+15 hints”; the d2/v10 evaluation blocks “are development validation”; the 112 rows “must not be described as an untouched test set.”

Stated: `CLAIM_BOUNDARY.md` lines 17–18 and 21–31; `README.md` lines 50–55.

---

## 2. The verification path

`P` is the absolute path of this directory. `VERIFY.md` lines 28–35 set `P=/absolute/path/to/zkdiff_august_20260907` and say “never `cd` into a subdirectory between steps.” This copy sits at `zkdiff_agent_audit_pkg`, not that name (`FAQ.md` 60: “`P` is the absolute path of your copy of the package, wherever it sits”).

### (a) Verify one proof

Offline, no toolchain, using the shipped static binary (`VERIFY.md` lines 181–184 adapted to `capsule/README.md` lines 37–38 and `capsule/verify_offline.sh` lines 38–40):

```
"$P/capsule/zkdiff-verify" --proof "$P/proofs/row_000600_groth16.bin" \
    --expect "$P/source/expected_identities_august.json" \
    --report /tmp/row_000600.verify.json
```

Raw 356+752 form (`capsule/verify_offline.sh` lines 57–59):

```
"$P/capsule/zkdiff-verify" --proof-bytes "$P/proofs/row_000600_groth16_proof.bin" \
    --public "$P/public_values/row_000600_public_values.bin" \
    --expect "$P/source/expected_identities_august.json"
```

Standalone Groth16 layer only (`VERIFY.md` lines 81–85), using the capsule binary so cargo is not required:

```
"$P/capsule/zeebeam-standalone-verifier" \
    "$P/proofs/row_000600_groth16_proof.bin" \
    "$P/public_values/row_000600_public_values.bin" \
    0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027
```

**Does the package give everything needed?** Yes for Groth16-plus-identities on one row, **if** the machine is x86_64 Linux and the reader accepts a prebuilt static binary. The capsule ships `zkdiff-verify`, `zeebeam-standalone-verifier`, the framed and raw proofs, the 752-byte statement, `expected_identities_august.json`, `PROGRAM_VKEY.txt`, and `groth16_vk.bin`. `capsule/STATIC_LINK_RECORD.txt` lines 18–19: both binaries are “ELF 64-bit LSB pie executable, x86-64 … static-pie linked”. `capsule/verify_offline.sh` line 28: failure is “is this an x86_64 Linux machine?”. `capsule/README.md` lines 77–80: “Trusting the capsule’s `zkdiff-verify` means trusting that the binary embeds what its record says; a reader who does not want to trust a shipped binary rebuilds it.” Rebuild is path (c), which this directory alone does not close.

The cargo route in `VERIFY.md` lines 80–85 is **not** self-contained: “for the first build, either the network or a cargo home that already holds the 209 locked crates.” Those crates are not in the tree.

### (b) Verify all 112

```
bash "$P/capsule/verify_offline.sh"
```

(`README.md` lines 74–76; `VERIFY.md` lines 257–259; `capsule/README.md` lines 16–26.) Expected: exit 0, “112 of 112 accepted by `zkdiff-verify`” and “112 of 112 `VERIFIED` by the standalone verifier.”

Identity-only check that does **not** verify a proof (`VERIFY.md` lines 295–297):

```
python3 "$P/tools/check_identities.py" "$P"
```

**Does the package give everything needed?** Same as (a): yes for checking the 112 Groth16 proofs under the pinned key and frozen identities, on x86_64 Linux, if the shipped binaries are trusted. The 112 framed proofs, 112 raw proofs, and 112 statements are in `proofs/`, `public_values/`, and `capsule/`. Missing for a reader who will not trust those binaries: a rebuild of `zkdiff-verify` from source (path (c)). The Python identity tool is in the tree and uses only the standard library; it “verifies no proof” (`VERIFY.md` line 300).

### (c) Rebuild the program and compare its identity to the pinned one

```
(cd "$P/source/armc-relation" && ./build_reproducible.sh)
```

(`VERIFY.md` lines 169–177.) The driver “exits non-zero unless … the ELF is 396,200 bytes with SHA-256 `51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc` and verifying key `0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027`”; last line `BUILD_REPRODUCED_OK`.

Then:

```
"$P/source/armc-relation/script/target/release/zkdiff-verify" --identity
```

**Does the package give everything needed?** No. The guest ELF is “not shipped” (`PINS.json` line 6). The rebuild needs, and this directory does not contain:

| Missing | Where the package says it lives |
|---|---|
| Rust 1.98.0, `cargo-prove` 6.4.0, succinct guest toolchain, `protoc` | `VERIFY.md` lines 113–142; downloads are URLs, not files here |
| 209+ locked crates (the workspace sets `offline = true`) | `VERIFY.md` lines 149–164; fetch needs the network |
| C compiler, linker, `pkg-config`, GNU time, binutils | `VERIFY.md` lines 115–126; “from the operating system” |
| The offline build kit (`build_kit/`: vendored crates, toolchain tarballs, Groth16 circuit files; 26 files, 9,279,781,352 bytes) | `LARGE_FILES.md` lines 28–39; `VERIFY.md` section 2b. **Not in this directory.** Served from the data layer. |

`replicate/replicate.sh build` is specified but “fetch[es] and hash-check[s] every toolchain” (`README.md` lines 77–79). That needs the network, which this audit does not have. `FAQ.md` 65: “the OS packages … still come from the operating system.”

### (d) Reproduce one row’s residual sums

Toolchain-free, row 600, shipped frame (`capsule/README.md` lines 61–64; `VERIFY.md` lines 273–275):

```
bash "$P/capsule/reexecute/reexecute_row.sh"
```

Expected (rehearsal, `VERIFY.md` line 511): `R_correct` 4,435,539,299, `R_wrong` 11,254,163,581, `D` +6,818,624,282, 14,400,363,198 instructions, statement byte-identical. Needs about 17 GB of RAM (`capsule/README.md` line 57). The batch driver “refuses a frame whose BLAKE3 differs from the chain log’s before it runs anything” (`capsule/reexecute/reexecute_row.sh` lines 12–13).

Python oracle (`VERIFY.md` lines 438–440):

```
(cd "$P/source" && python3 -B tools/python_oracle_rows.py 600)
```

**Does the package give everything needed?** For **row 600 via the static batch driver**, yes on x86_64 Linux with ~17 GB RAM, again if the shipped `capsule/reexecute/zkdiff-batch` is trusted: `frame_000600.raw`, the chain log, `source/noise_august/`, the constants blob, and the frozen identities are in the tree.

For the **Python** route, no, even for row 600. `source/tools/python_oracle_rows.py` lines 75–79 load `oracle/final/vectors/vectors_int16_d2_1328_{correct,wrong_p2}.npz` as a hard positive control before any August row; those `.npz` files are on the data layer (`LARGE_FILES.md` line 51), not here (only the JSON manifests sit under `oracle/final/vectors/`). `FAQ.md` 70: “the Python route needs the data-layer files in any case.” Copying `capsule/reexecute/row_000600.npz` to `oracle/final/august_inputs/` does not close that hole. The script also imports `torch` (line 33).

For **any row other than 600**: `reexecute_row.sh 684 --frames-dir DIR` needs `frame_000684.raw` from the data layer (`FRAMES.md`). Those 111 frames are not in this directory. The 112 `oracle/final/august_inputs/row_NNNNNN.npz` files are listed as 68,125,752 bytes on the data layer (`LARGE_FILES.md` line 50); this tree has only `manifest.json` and `coord_int.npy` there, plus the one shipped `capsule/reexecute/row_000600.npz`.

### (e) Reproduce a proof

```
"$P/replicate/replicate.sh" prove 600 --device 0
```

(`replicate/README.md` lines 29 and 56–57; `VERIFY.md` lines 549–550.) Frame defaults to the shipped row-600 file. Expected: a fresh Groth16 proof, public bytes identical to the published statement, proof bytes different (“Groth16 is randomised”, `FAQ.md` 51).

**Does the package give everything needed?** No.

| Missing | Where named |
|---|---|
| A CUDA GPU with enough memory (observed peak “about 28.5 GiB”; “a 24 GB part … is expected to fail **[untested]**”) | `replicate/README.md` lines 64–66 |
| `sp1-gpu-server` 6.4.0 (tarball 133,469,274 bytes) | `VERIFY.md` line 141 |
| Groth16 v6.1.0 circuit files (tarball 6,211,807,514 bytes; `groth16_pk.bin` 5,862,173,061 bytes) | `VERIFY.md` lines 142, 223–226; `FAQ.md` 67: “The tarball itself is not mirrored; its seven members are, under `build_kit/`.” `build_kit/` is not in this directory. |
| Host rebuild with `--features cuda` | `VERIFY.md` line 549 |
| Network, unless the offline kit has been placed | `replicate/README.md` lines 109–113 |

Proving “is not part of verification” (`VERIFY.md` line 552). It was rehearsed once on a rented A100-SXM4-40GB (`VERIFY.md` lines 549–550).

---

## 3. Every question I could not answer from the package alone

The package answers most of the topics named in the brief (`GLOSSARY.md`, `FAQ.md`, `HASHES.md`, `STATEMENT.md`). What follows is only what this directory does not settle. Each item names the file where the answer was expected.

### Hashes whose preimage is not here, or that cannot be recomputed from this tree

1. **What are the bytes of the authority manifest whose SHA-256 `740d752d…d783` sits at statement offset 228?** Only the digest is published; the guest “carries it into the context and does not recompute it.” Publishing the file is “**not decided at publication**.” Expected: `HASHES.md` line 36; `FAQ.md` 2.

2. **How was `S_0` `74e3a131…384c` chosen?** “the seed the recorder chose; how it was chosen is not in this package.” Expected: `FAQ.md` 3; `GLOSSARY.md` line 43.

3. **What is the SHA-256 of this directory’s `SHA256SUMS` as pinned by the Dark Lantern root `README.md`?** `HASHES.md` line 84: “the ledger’s own SHA-256 is what the Dark Lantern root `README.md` and the release records pin.” That root file is not in this directory. Expected: `HASHES.md`; `FAQ.md` 49.

4. **What are the data-layer `_control/` manifest digests, object count, and byte total?** They are “published outside both payloads, in the Dark Lantern root `README.md` provenance paragraph.” Expected: `FAQ.md` 66; `LARGE_FILES.md` lines 20–26.

5. **What are the bytes of the as-trained checkpoint `c6955192…fab8` and of the frozen expected-identities file `6822cdce…d613`?** The shipped files are documented derivatives (three path strings; a redacted `sources` block). The originals are not here. Expected: `HASHES.md` lines 27 and 63; `REDACTION.md` lines 40–44.

6. **What are the withheld files listed in `receipts/SHA256SUMS_RUNS` (prover stderr, sidecar logs, `NODE_PROVE_READY.md`)?** Digests are a “commitment”; the files “stay on-box.” Expected: `FAQ.md` 8, 54, 61; `receipts/README.md`.

7. **Can the program verifying key be recomputed from this tree without a rebuild?** `HASHES.md` line 20: recompute is `build_reproducible.sh` / `zkdiff-ceremony vkey`. The ELF is not shipped. Path (c) is not closed. Expected: `HASHES.md`; `PINS.json` line 6.

8. **What is the preimage of `vk_root` `002f850e…5352` as source, not as a printed constant?** It is `sp1_verifier::VK_ROOT_BYTES` of crate 6.4.0. The crate source is not vendored except as linked into the binaries. Expected: `HASHES.md` line 23; `FAQ.md` 1.

9. **What are the Groth16 v6.1.0 circuit-file bytes other than `groth16_vk.bin`?** Seven files, including a 5.86 GB proving key; not in this directory. Expected: `VERIFY.md` line 142; `PINS.json` `prover_node.groth16_circuit_files_v6_1_0`.

10. **Do the truncated private digests in `oracle/final/FREEZE_SUMMARY.md` lines 35–48 (`AGREEMENT.md sha256 28d8764dea2e45f5…`) match any published file?** `REDACTION.md` lines 32–34 say those are “the private digests”; published `AGREEMENT.md` is `78d7c48e…` in `PINS.json`. A reader of `FREEZE_SUMMARY.md` alone cannot tell. Expected: `FAQ.md` 57; `oracle/final/FREEZE_SUMMARY.md`.

### Public-output fields whose meaning is not fully in this package

`STATEMENT.md` section 2 and `tools/decode_zbdiff01.py` name every 752-byte field. Remaining gaps:

11. **What is protocol `TB-v0.9` beyond “the Truth Beam capture-protocol revision the session followed”?** “defined in the ZeeBeam manuscript section 4”; “There is no registry beyond the manuscript and the source.” The manuscript is not in this directory. Expected: `FAQ.md` 11; `GLOSSARY.md` lines 96–98; `CLAIM_BOUNDARY.md` lines 54–56.

12. **What is ABI 1 a version of, other than “the version of this statement’s byte layout”?** No ABI 0 (or later) is specified. Expected: `STATEMENT.md` line 78; `FAQ.md` 11.

13. **What is denoiser kind 0 (“stub”)?** Kind 1 is `armc-int`; kind 0 is named and unused. The stub is not specified. Expected: `STATEMENT.md` line 80.

14. **What does the context-digest “terminal flag” `[terminal=1]` mean in English?** `HASHES.md` line 37 and `GLOSSARY.md` line 88 name it; `membership.rs` requires `terminal_committed == 1`. No prose definition of “terminal” is given. Expected: `HASHES.md`; `GLOSSARY.md`.

15. **What is the fourth 4-byte field of the 28-byte `meta` that “reads 64000 on every row”?** “its meaning is not stated in any record in the package **[confirm]**.” Expected: `FAQ.md` 5; `GLOSSARY.md` lines 71–75.

### Where each dataset comes from

16. **Where can the d2 (5,992 rows) and v10 (3,743 rows) frames be obtained, and when were those sessions recorded?** Block bounds are in `FAQ.md` 17; “does not carry the public location of those frames or their recording dates: **not decided at publication**.” Expected: `FAQ.md` 17; `GLOSSARY.md` (d2, v10).

17. **Where are the August training-row frames 0–599?** “Not published (`FRAMES.md`).” Expected: `FAQ.md` 68; `FRAMES.md` line 15.

18. **Where physically was the 22 August 2026 session recorded (site, camera model, lens, projector model)?** The primer gives resolution, Bayer RGGB, Aravis, ~300 s, 712 rows. Sensor model, lens, projector model, and site are not given. Expected: `README.md` lines 28–34; `FAQ.md` 16.

19. **Is the data-layer prefix `https://data.truthbeam.com/results/zkdiff_august_20260907/v1/` actually populated?** `FAQ.md` 49: “The prefix is populated by the release that publishes this package.” This audit has no network and no Dark Lantern root `README.md` to check the control digests. Expected: `FAQ.md` 49; `LARGE_FILES.md`.

20. **Where are `fill_results.py`, `stage_package.py`, `make_pins.py`, and `evidence_allowlist.py`?** “In the release desk’s staging repository, not in the package”; publishing them is “**not decided at publication**.” Expected: `FAQ.md` 50.

### “Held out”

The package does define this. `GLOSSARY.md` lines 135–138: “Held out from weight training” means “the rows contributed no gradient.” Four proof rows (606, 630, 654, 678) were among the trainer’s quick screen; seven were calibration targets. Remaining:

21. **Would the proved residuals differ under a scale map calibrated without the seven August rows?** “Not measured.” Expected: `FAQ.md` 24.

### Results tables: meaning, and whether the numbers are “good”

Meaning is given (`RESULTS.md` sections 1–6; `GLOSSARY.md` AUROC, paired fraction, MSE units, `D`). Remaining:

22. **Are the numbers good relative to a null?** “The package carries no random-network or shuffled-hint baseline and no confidence interval on the 112 August margins”; “A baseline study is not in the record.” Chance level of AUROC and paired fraction is 0.5. Expected: `FAQ.md` 26; `RESULTS.md` lines 46–47.

23. **Why are the August margins about half the d2/v10 margins?** “Reported, not explained; no explanation is on record.” Expected: `FAQ.md` 27; `RESULTS.md` lines 127–132.

24. **By what written criterion was the 24,000-step seed-20260908 checkpoint chosen over later arms with larger margins?** “No written criterion”; the ordering is “**[derived]**” from timestamps. Expected: `FAQ.md` 30; `RESULTS.md` lines 56–61.

25. **Why did the batch’s `.groth16()` times run 61–67 min against the pilot’s 46 min?** “contention is an interpretation, not a measured cause.” Expected: `FAQ.md` 32; `RESULTS.md` line 334.

26. **What does the unresolved bf16 fidelity at 1.1e-3 imply for the float development-validation scores?** Bounded, “does not touch the proofs”; the exact A100 rounding-point fidelity “remains unverified.” Expected: `FAQ.md` 29; `oracle/final/README_FINAL.md` lines 84–92.

### Wrong-row offset rule, including mirrored cases

The rule itself is fully stated (`STATEMENT.md` section 7; `source/armc-relation/relation/src/rule.rs` `RULE_TEXT`; ten mirrored rows 684, 689, 694, 698, 699, 703, 704, 708, 709, 711; four training-row hints 600→598, 602→587, 607→592, 612→597; eight policy-only rows 697, 702, 707, 710 / 698, 703, 708, 711). Remaining:

27. **Why these five offsets, why cycle by `(r - 600) mod 5`, and why mirror rather than skip?** “The principal set the rule; no further rationale is recorded.” Expected: `FAQ.md` 33; `STATEMENT.md` lines 204–207.

### Noise, and why it is a witness

The generation rule is fully stated (`STATEMENT.md` section 8; `tools/regen_noise.py`). Remaining:

28. **Does the Philox/Box-Muller stream equal a CUDA generator on any named GPU/toolkit?** “The exported bytes are normative”; “correspondence to a CUDA generator is approximate and is not what the proof binds.” Expected: `STATEMENT.md` lines 217–218; `FAQ.md` 39.

### Calibration disclosure

The fifteen rows, fourteen August identities, and “not an untouched test set” are stated (`CLAIM_BOUNDARY.md` lines 21–34; `PINS.json` line 1001). Remaining is question 21 above.

### Integer contract, and why int16

The contract is in `oracle/final/README_FINAL.md` section 3 (scale map, two rounding rules, saturation, noising, convolution, GroupNorm, LUTs). Remaining:

29. **Why int16 rather than int8, when both pass `D_q > 3η`?** int16 was “the fidelity baseline before the oracle ran”; it “passes with a margin of 80 against the reference error where int8 passes with 19.” “The proving cost of int8 was not measured.” Expected: `FAQ.md` 41; `RESULTS.md` section 3.

### What the audits found

Verdict lines and most texts are here (`AUDIT_TRAIL.md`; `audits/astra/`; `audits/agents/`). Remaining:

30. **What is the full text of Astra round 7?** “not published as text because it quotes the material it asked to remove.” Expected: `audits/README.md` lines 3–5; `AUDIT_TRAIL.md` lines 25–26, 79–94.

31. **What did Astra round 9 find, finding by finding?** Logs mention “Astra round 9” (`VERIFY.md` line 565; `FAQ.md` line 451; `AUDIT_TRAIL.md` line 234; `REDACTION.md` line 23). There is no `audits/astra/r9_brief.md` or `r9_verdict.md`, and the audit-trail table has no round-9 row. Expected: `AUDIT_TRAIL.md`; `audits/README.md`.

32. **Has the published revision itself been re-read?** “This revision has not itself been re-read.” Expected: `AUDIT_TRAIL.md` lines 198, 212–213; `FAQ.md` 43.

33. **What is “GPT-6 Astra” as a system, beyond “the second model … run through `codex exec` at ultra reasoning effort”?** No model card, checkpoint, or vendor artefact is in the tree. Expected: `FAQ.md` 44; `GLOSSARY.md` lines 246–248.

### Patent

34. **What was filed on 6 September 2026 (office, application number, title, claims)?** The package states only “Patent filing date: 6 September 2026.” `LICENSE` section 5: “No patent licence is granted, except that the copyright holder will not assert patent claims against the non-commercial uses that section 2 permits.” Expected: `README.md` lines 159–162; `FAQ.md` 46; `LICENSE` lines 63–65.

### Who BOSUN is

This **is** answered: “the project’s automated research assistant, a Claude-family language model running the project’s desk”; “not a person, holds no authority”; principal is Cathal Ryan Hynes. (`README.md` lines 66–68; `GLOSSARY.md` lines 241–244; `FAQ.md` 34, 48.) No remaining question on identity. What is not here is any unredacted machine identity the alias replaced (`REDACTION.md` lines 11–12).

### Other questions this directory does not answer

35. **What is the ZeeBeam manuscript *ZeeBeam: The Zero-Knowledge Beam* v3.20 Sections 3.4, 4, and 8.3, which the claim boundary and TB-v0.9 rest on?** Cited as `github.com/poliebotics/zeebeam`, `paper/zeebeam.md`. Not in this directory. Expected: `CLAIM_BOUNDARY.md` lines 54–56.

36. **What are the eight-seed AUROC, five-offset aggregate, original published checkpoint, coupling packet, and sealed 288-row verification take, as artefacts?** Named as external referents this package “neither reproduces nor inherits.” Expected: `FAQ.md` 20; `GLOSSARY.md` lines 24–25, 29–30.

37. **What does `MAINNET` in the session identifier mean as a proved fact?** The proof “binds the bytes of the identifier; the reading is the programme’s.” The ZeeBeam release “anchored a prefix … in Zcash mainnet transactions”; “this package … makes no use of the anchor.” Expected: `FAQ.md` 12, 19; `GLOSSARY.md` lines 80–83.

38. **What caused the single 533.8 ms frame gap against a median of 400.05 ms?** “the cause of the single long gap is not recorded.” Expected: `FAQ.md` 72; `PINS.json` lines 81–85.

39. **What is guest heap / proving memory footprint under proving?** “not measured”; `source/CYCLES.md` lines 240–241, 361. Expected: `source/CYCLES.md`.

40. **What torch version ran on the node when the preprocessed-row cache was made?** “the node’s torch version is unrecorded **[confirm]**.” Expected: `source/armc-relation/RELATION.md` (cited line in that file’s table).

41. **Do the `sp1-gpu-server`, `cargo-prove`, and succinct toolchain tarballs carry licence files?** “carry no licence file and are redistributed as Succinct released them **[confirm]**.” Expected: `VERIFY.md` lines 245–247.

42. **Where are `THIRD_PARTY_NOTICES.md`, `licenses/`, and `CITATION.cff` that `LICENSE` sections 1, 3(f), and 4 name?** “files of the repository root, beside this package; a standalone copy of the package lacks them.” `capsule/THIRD_PARTY_NOTICES.md` is present; the root files are not. Expected: `FAQ.md` 47; `LICENSE` lines 8–12, 53–61.

43. **What is `OPEN_ITEMS`?** “the release desk’s own record and is not in the package.” Expected: `FAQ.md` 76.

44. **Why does one nested SP1 helper build need extra `cargo fetch` of `sp1-core-executor-runner-6.4.0`?** Described as a fact of that crate (`VERIFY.md` lines 151–154; `replicate/README.md` lines 114–118). Why that crate is structured that way is not explained here. Expected: `VERIFY.md` section 2.

---

## 4. Obstacles ranked by severity

**1. Cryptographic close of the loop is not in this directory (high).** Checking a proof under a pinned key is specified and, on x86_64 Linux, scripted. Knowing that key is the published source requires `build_reproducible.sh`. The ELF is “not shipped.” The offline build kit that would rebuild with no network is on the data layer, not here. A reader who will not trust `capsule/zkdiff-verify` cannot finish path (c) from this tree.

**2. Independent residual-sum reproduction for 111 of 112 rows is not in this directory (high).** Row 600’s frame is shipped. The other 111 frames and the 112 `august_inputs/row_*.npz` files “belong to this package by layout” (`LARGE_FILES.md` line 10) but live at `https://data.truthbeam.com/`. This audit was forbidden the web. Path (d) therefore stops at one row, and only if the static `zkdiff-batch` is trusted. The Python oracle cannot even do row 600: it first loads d2 vector `.npz` files that are also on the data layer (`source/tools/python_oracle_rows.py` lines 75–79; `FAQ.md` 70).

**3. Proof reproduction is not in this directory (high for the request, not for verification).** Path (e) needs an A100-class GPU, `sp1-gpu-server`, and a 6.2 GB circuit cache. None of those are in the tree. The package itself says proving “is not part of verification.”

**4. Steps that assume knowledge or files not in the package (high).** `VERIFY.md` line 10: “Everything a verifier needs is in this directory or in `PINS.json`.” Later sections send the reader to the data layer, crates.io, GitHub, S3, `api.drand.sh`, and the Dark Lantern root `README.md`. The drand out-of-band check “needs the network” and is “not exercised from this package” (`VERIFY.md` lines 334–338). TB-v0.9 and the claim-boundary’s “ZeeBeam manuscript … Sections 3.4 and 8.3” are outside the tree.

**5. Paths that do not resolve in this copy (medium–high).**

| Path named in the package | What is here |
|---|---|
| `build_kit/` | absent |
| `frames/frame_NNNNNN.raw` (111 of 112) | only `capsule/reexecute/frame_000600.raw` |
| `oracle/final/august_inputs/row_*.npz` | only `manifest.json`, `coord_int.npy`; one npz in the capsule |
| `oracle/final/vectors/*.npz` | only `*.json` manifests |
| `source/oracle_final/` | absent |
| `oracle/rows/`, `oracle/rows_august/` | absent |
| `oracle/ckpt/final/…` (`FREEZE_SUMMARY.md` line 4; `august_inputs/manifest.json` lines 3–8) | checkpoint is under `model/` |
| `../src/lean_pubproto_eval.py`, `../node_results/G0.log` (`oracle/final/README_FINAL.md` lines 55–57) | trainer is `oracle/trainer/`; `node_results/` is absent |
| `THIRD_PARTY_NOTICES.md`, `licenses/`, `CITATION.cff` at package root (`LICENSE` §4) | absent; capsule notices only |
| `audits/astra/r7_*.md`, `r9_*.md` | absent |
| guest ELF path in `PINS.json` line 6 | “not shipped” |

**6. Platform and trust assumptions (medium).** Capsule binaries are x86_64 Linux static-pie (`capsule/STATIC_LINK_RECORD.txt` lines 18–19). `capsule/verify_offline.sh` line 28 treats any other machine as failure. Re-execution wants ~17 GB RAM. The standalone cargo route needs Rust 1.98 and 209 crates.

**7. Inconsistencies between files (medium).** The leftover “frames are not published / tensors are held” sentences that the second-reading reports quoted (`audits/agents/grok_r2.md` lines 284–290) are **gone** from the current `VERIFY.md`, `FAQ.md`, `HASHES.md`, and `replicate/README.md`. What remains:

- `VERIFY.md` line 35 still names the directory `zkdiff_august_20260907`; this copy is `zkdiff_agent_audit_pkg` (`FAQ.md` 60 explains, but the command block does not).
- `source/tools/python_oracle_rows.py` lines 5–12 still document `g1_integer/final/august_inputs/` and `g2_guest/runs/`; the code has a fallback (`lines 19–21`), the docstring does not.
- `oracle/final/FREEZE_SUMMARY.md` line 49 says `august_inputs/`: 114 files; this tree has two files there.
- `tools/check_identities.py` line 8 still says “the owner rule”; published prose uses “declared offset rule” (`GLOSSARY.md` lines 237–239).
- Receipts say `sp1_version: v6.1.0` while the package says SP1 6.4.0. `FAQ.md` 10 explains this; a reader of receipts alone will misread it.
- Two digests for expected identities, checkpoint, merged manifest, and proof controls (`HASHES.md` 1.2). Explained, but easy to treat as a mismatch.
- `AUDIT_TRAIL.md` logs “Astra round 9” without a round-9 row or published text.

**8. Ambiguous wording and leftover private-tree vocabulary (low–medium).** `README.md` line 14: “the session whose anchored rows the ZeeBeam release proves” — “anchored” is not the claim of *these* proofs (`FAQ.md` 19). `CLAIM_BOUNDARY.md` line 15: “independently verified” does not mean an independent organisation (`FAQ.md` 45). Copied notes still say `g1_integer/`, `ckpt/final/`, `standard` in historical sentences even where banners say to read `oracle/`, `model/`, `direct`. `replicate/README.md` line 10: “Hoy. BOSUN here.”

**9. Undefined or external acronyms (low, after the glossary).** ARM-C, SP1, Groth16, AUROC, PTQ, QAT, CFA, XOF, d2, v10, G0–G3 are defined in `GLOSSARY.md`. Still external: TB-v0.9 as a protocol body (manuscript), “GPT-6”, “League of Entropy”, “gnark”. The `meta` field 64000 is explicitly undefined.

**10. Unrehearsed steps tagged `[confirm]` (low for verification, material for regeneration).** `VERIFY.md` lines 38–44 and 553–554: two remaining `[confirm]` steps are regeneration of the August export sets and complete oracle regeneration with August rows placed. Not needed to verify a proof.

---

## 5. Three things the package does well

**1. A claim boundary written before the proofs, and applied.** `CLAIM_BOUNDARY.md` lines 10–13: the three paragraphs “were written by the programme’s second-model auditor … after it had read the complete guest, the oracle and the calibration record” and “Every other document in this directory is read under them.” The calibration disclosure names the seven August targets and the four quick-screen rows rather than calling 600–711 an untouched test set.

**2. An offline check of all 112 proofs that does not need Rust, Python, or the network.** `capsule/verify_offline.sh` is a single command; it pins the embedded ELF and circuit key, accepts every framed proof against frozen identities, runs controls, and cross-checks the standalone Groth16 layer. `tools/decode_zbdiff01.py` and `tools/check_identities.py` let a reader without a binary decode every statement and recompute the offset rule from the row number.

**3. A glossary, hash ledger, and FAQ that answer outsider questions from files.** `HASHES.md` says of what each published hash is the hash, with a recompute column. `STATEMENT.md` section 2 is a byte-offset table of the 752-byte statement; section 7 quotes `RULE_TEXT` and lists the ten mirrored rows; section 8 gives the Philox rule. `FAQ.md` records the previous outside-agent questions and, where the package cannot answer, says so (“**not decided at publication**”, “**[confirm]**”) instead of filling the gap.

---

## 6. Verdict

**YES WITH EFFORT** — on x86_64 Linux, with ~17 GB RAM, an agent can follow the claims from the primer, glossary, FAQ, and statement, and can check all 112 Groth16 proofs under the pinned key and frozen identities with `bash capsule/verify_offline.sh`, if that agent accepts the shipped static binaries; the same agent cannot, from this directory alone, rebuild the guest to the pinned ELF, recompute 111 of 112 residual sums from raw frames, or make a fresh proof.

**Single most important fix:** Put the offline build kit (`build_kit/`: vendored lockfile crates and the pinned toolchains) **inside this directory**, so a reader who will not trust the shipped `zkdiff-verify` can rebuild the guest ELF and verifying key without the network or a data-layer fetch whose live state this tree cannot demonstrate.
