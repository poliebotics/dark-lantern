> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

# Outside-agent audit of the zkdiff August proof package

Read-only pass over `the package root`. No files were modified and no verifier, rebuild, or proof was run. Commands below are taken from the package; whether they would succeed is judged from the files, not from execution.

---

## 1. What I understood the package claims, in five plain sentences

**1.** For each of the 112 rows 600–711 of the 712-row projector-camera session of 22 August 2026, one SP1 6.4.0 Groth16 proof (356-byte raw proof, 752-byte public statement, no pixels) is said to establish that a frozen integer diffusion denoiser, adapted from the ARM-C protocol, produced the published residual sums on the whole sensor frame of that row under the row’s own emission and under a declared wrong row’s emission.  
Stated: `README.md` lines 8–24 and 58–65; `CLAIM_BOUNDARY.md` lines 15–16.

**2.** All 112 proofs are said to have been verified and accepted under frozen identities, with 112 positive signed outcomes, 0 zero, 0 negative, and 0 rows with a nonzero clip count.  
Stated: `README.md` lines 10–12; `RESULTS.md` lines 198–199 and 324.

**3.** An accepting proof under the pinned program verifying key `0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027`, guest ELF SHA-256 `51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc` (396,200 bytes), and constants blob SHA-256 `73310ddab603cab5588d05e9ac4deb7e56466a6fae4bbf89244c32f2bd1a8b92` is said to establish only that the published `R_correct`, `R_wrong`, and `D = R_wrong - R_correct` are what that frozen integer network produced on the committed frame bytes, with the published clip count.  
Stated: `README.md` lines 109–120; `VERIFY.md` lines 424–430; `STATEMENT.md` lines 237–244.

**4.** The three paragraphs of `CLAIM_BOUNDARY.md` govern every other sentence: the proofs “establish the specified integer computations and bindings” and “establish no physical-capture, realness, liveness, illumination-causality, adversarial-resistance or unseen-session-generalisation claim”; they “do not reproduce the original published checkpoint, five-offset aggregate, eight-seed AUROC or full diffusion sampling”; “Noise generation remains external provenance; the proof binds the normative bytes and computes forward noising.”  
Stated: `CLAIM_BOUNDARY.md` lines 10–19; `README.md` lines 122–129.

**5.** August rows 600–711 “were held out from weight training”; “quantisation calibration used seven targets from this set and their own/+15 hints”; the d2/v10 evaluation blocks “are development validation”; the 112 rows “must not be described as an untouched test set.”  
Stated: `CLAIM_BOUNDARY.md` lines 17–18 and 21–34; `README.md` lines 51–56.

---

## 2. The verification path

`P` is the absolute path of this directory, as `VERIFY.md` lines 28–35 require.

### (a) Verify one proof

**Offline, no toolchain (the route the package now puts first):**

```
bash "$P/capsule/verify_offline.sh"
```

That script verifies all 112, not one. To check a single row with the shipped static binary (`VERIFY.md` lines 171–174, adapted to the capsule copies in `capsule/README.md` lines 37–38 and `capsule/verify_offline.sh` lines 38–40):

```
"$P/capsule/zkdiff-verify" --proof "$P/capsule/proofs/row_000600_groth16.bin" \
    --expect "$P/capsule/expected_identities_august.json" \
    --report /tmp/row_000600.verify.json
```

Raw 356+752 form (`VERIFY.md` lines 180–183; `capsule/verify_offline.sh` lines 57–59):

```
"$P/capsule/zkdiff-verify" --proof-bytes "$P/capsule/proofs/row_000600_groth16_proof.bin" \
    --public "$P/capsule/public_values/row_000600_public_values.bin" \
    --expect "$P/capsule/expected_identities_august.json"
```

Standalone Groth16 layer only (`VERIFY.md` lines 75–80), using the capsule binary so cargo is not required:

```
"$P/capsule/zeebeam-standalone-verifier" \
    "$P/proofs/row_000600_groth16_proof.bin" \
    "$P/public_values/row_000600_public_values.bin" \
    0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027
```

**Does the package give everything needed?** Yes for Groth16-plus-identities on one row, **if** the machine is x86_64 Linux and the reader accepts a prebuilt static binary. The capsule ships `zkdiff-verify` and `zeebeam-standalone-verifier`, the framed and raw proofs, the 752-byte statement, `expected_identities_august.json`, `PROGRAM_VKEY.txt`, and `groth16_vk.bin`. `capsule/STATIC_LINK_RECORD.txt` lines 10–11: both binaries are “ELF 64-bit LSB pie executable, x86-64 … static-pie linked”. `capsule/verify_offline.sh` line 28: failure is “is this an x86_64 Linux machine?”. `capsule/README.md` lines 75–78: “Trusting the capsule’s `zkdiff-verify` means trusting that the binary embeds what its record says; a reader who does not want to trust a shipped binary rebuilds it.” Rebuild is path (c), which this package alone does not close.

The cargo route in `VERIFY.md` lines 75–80 is **not** self-contained: “for the first build, either the network or a cargo home that already holds the 209 locked crates.” Those crates are not in the tree.

### (b) Verify all 112

```
bash "$P/capsule/verify_offline.sh"
```

(`README.md` lines 74–75; `VERIFY.md` lines 214–216; `capsule/README.md` lines 16–26.) Expected: exit 0, “112 of 112 accepted by `zkdiff-verify`” and “112 of 112 `VERIFIED` by the standalone verifier.”

The loop form with a rebuilt `zkdiff-verify` is `VERIFY.md` lines 187–192.

Identity-only check with no binary (`VERIFY.md` lines 250–255):

```
python3 "$P/tools/check_identities.py" "$P"
```

`tools/check_identities.py` lines 1–16: standard library only; “What this does NOT do: verify a Groth16 proof.”

**Does the package give everything needed?** Same as (a): yes for all 112 Groth16+identity checks on x86_64 Linux with the shipped binaries; no if the reader refuses those binaries, because rebuild needs the network. `tools/check_identities.py` is complete for the identity half. The 112 framed proofs, 112 raw proofs, and 112 public-value files are in `proofs/`, `public_values/`, and `capsule/`.

### (c) Rebuild the program and compare its identity to the pinned one

Ledger first (`VERIFY.md` lines 43–46), then fetch locked crates (`VERIFY.md` lines 146–154), then:

```
(cd "$P/source/armc-relation" && ./build_reproducible.sh)
```

(`VERIFY.md` lines 159–167.) The driver asserts ELF 396,200 bytes, SHA-256 `51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc`, vkey `0x00f01894…a027`, last line `BUILD_REPRODUCED_OK`. Then `"$S/zkdiff-verify" --identity` (`VERIFY.md` lines 171–177).

One-pull form: `replicate/replicate.sh build` (`replicate/README.md` lines 23 and 86–89).

**Does the package give everything needed?** No. Missing from the tree:

| missing | where the package says so |
|---|---|
| Guest ELF itself | `PINS.json` lines 6–7: “not shipped” |
| Rust 1.98.0, rustup 1.29.1 | `VERIFY.md` lines 110, 127 |
| `cargo-prove` 6.4.0 and the succinct RISC-V toolchain | `VERIFY.md` lines 111–113, 128–129; tarballs are GitHub URLs, not files here |
| `protoc` 21.12 and protobuf includes | `VERIFY.md` lines 114–116, 130 |
| GNU time, binutils | `VERIFY.md` lines 117–118 |
| The 209 locked crates (and the two nested `sp1-core-executor-runner` lockfile trees) | `VERIFY.md` lines 133, 139–144; `replicate/README.md` lines 112–116. Workspace is `offline = true` |
| Network, unless a populated cargo home already exists | `VERIFY.md` lines 82–83, 139–140 |

The source, four lockfiles, pins, and `build_reproducible.sh` **are** here. The toolchains and crates they consume are not. `replicate/README.md` lines 107–111 lists rustup, SP1 GitHub assets, Succinct S3 circuit files, protoc, and crates.io as remaining external.

### (d) Reproduce one row’s residual sums

**Native re-execution of row 600 (shipped frame):**

```
bash "$P/capsule/reexecute/reexecute_row.sh"
```

(`VERIFY.md` lines 223–228; `capsule/README.md` lines 59–61; `capsule/reexecute/reexecute_row.sh` lines 6–8, 36–48.) Compares the recomputed 752 bytes with `public_values/row_000600_public_values.bin`. Needs ~17 GB RAM and 4–7 minutes.

**Python oracle (row 600 and 684 as written):**

```
(cd "$P/source" && python3 -B tools/python_oracle_rows.py 600 684)
```

(`VERIFY.md` lines 393–394.) Needs torch, numpy, and `oracle/final/august_inputs/row_NNNNNN.npz`.

**Does the package give everything needed for one row?** For **row 600 via the static batch driver: yes**, on x86_64 Linux with ~17 GB RAM. Present: `capsule/reexecute/zkdiff-batch`, `frame_000600.raw` (24,472,000 bytes), `row_000600.npz`, chain log, `source/noise_august/`, `source/blobs/final_int16/constants_int16.blob`, `source/expected_identities_august.json`.

For **any other row, or for the Python route: no.** `oracle/final/august_inputs/` in this tree contains only `manifest.json` and `coord_int.npy` — not `row_*.npz`. `oracle/rows/` and `source/oracle_final/` do not exist. Frames 601–711 are not in the tree; `FRAMES.md` lines 10–15 puts them on `https://data.truthbeam.com/` under `results/zkdiff_august_20260907/v1/frames/`. `FAQ.md` lines 278–281: “Until the upload is released the prefix is empty.” Python needs torch/numpy, which are not in the package.

### (e) Reproduce a proof

```
./replicate.sh prove 600 --device 0 --frame /path/to/frame_000600.raw
```

(`replicate/README.md` lines 28, 55–56; `replicate/replicate.sh` lines 889–903.) Rebuilds the host with the `cuda` feature, runs `zkdiff-batch prove --prover cuda`, then cold-verifies. `FAQ.md` lines 287–289: a fresh proof has different proof bytes and the same 752-byte statement (Groth16 wrapping is randomised).

**Does the package give everything needed?** No.

| missing | where stated |
|---|---|
| CUDA GPU with ~28.5 GiB VRAM | `VERIFY.md` lines 137–138; `replicate/README.md` lines 64–66. 24 GB cards “expected to fail **[untested]**” |
| `sp1-gpu-server` 6.4.0 (250,950,472-byte binary) | `VERIFY.md` line 131 |
| Groth16 v6.1.0 circuit files, including `groth16_pk.bin` 5,862,173,061 bytes | `VERIFY.md` line 132; `HASHES.md` line 80 |
| CUDA rebuild of the host (`CUDA=1`) | `source/armc-relation/build_reproducible.sh` line 13 |
| A rehearsed GPU wrapper | `replicate/README.md` lines 119–121, 178–179: “The GPU path was not rehearsed here” / “**[untested here]**” |
| Frame for rows other than 600 | same hole as (d); `replicate.sh` line 893 still says “raw frames are not published (REDACTION.md)” |

Row 600’s frame is in `capsule/reexecute/`, so the frame argument for that one row exists. The proving stack does not.

---

## 3. Every question I could not answer from the package alone

Grouped under the topics you named. Each item is something the files do not settle. Where the package itself marks the gap, that is quoted.

### Identity of hashes

1. **What bytes hash to the authority-manifest SHA-256 `740d752d…d783`?** Only the digest is published. `HASHES.md` line 36: “not recomputable from the package.” `FAQ.md` lines 26–31: publishing the manifest is “**not decided at publication**.” Expected: `HASHES.md`, `PINS.json` `session.authority_manifest_sha256`.

2. **Of what, if anything, is `S_0` `74e3a131…384c` the hash?** `GLOSSARY.md` line 41: “how it was chosen is not in this package.” `FAQ.md` lines 33–36. Expected: `HASHES.md` “The session and the chain.”

3. **What is the SHA-256 of the Groth16 v6.1.0 tarball `v6.1.0-groth16.tar.gz`?** `VERIFY.md` line 132: “the tarball is 6,211,807,514 bytes and is recorded by size, its seven files by digest.” `replicate/README.md` line 108: “the tarball itself is recorded, not pinned.” Expected: `PINS.json` `prover_node.groth16_circuit_files_v6_1_0`.

4. **What are the SHA-256 values of the data-layer `_control/MANIFEST.jsonl` and `_control/SHA256SUMS`?** `LARGE_FILES.md` lines 22–25 says those digests “are fixed at publication in the Dark Lantern repository’s root `README.md`,” which is not in this directory. Expected: `LARGE_FILES.md` or `PINS.json`.

5. **Can `BLAKE3(raw_r)` and receipt `raw_sha256` be recomputed here for rows 601–711?** `HASHES.md` lines 41 and 53 still say “needs the frame (held).” `FRAMES.md` says those frames are on the data layer; they are not in this tree except row 600. Expected: `FRAMES.md` vs `HASHES.md`.

### Meaning of public-output fields

The 752-byte layout is named field-by-field in `STATEMENT.md` lines 75–102 and decoded by `tools/decode_zbdiff01.py`. Remaining gaps:

6. **What is protocol byte 9 / `TB-v0.9` beyond “the Truth Beam capture-protocol revision the session followed”?** `FAQ.md` lines 73–77: “defined in the ZeeBeam manuscript section 4”; “There is no registry beyond the manuscript and the source.” The manuscript is not in this package. Expected: `STATEMENT.md` section 2, `GLOSSARY.md` “TB-v0.9.”

7. **What does the session-id reading “anchored to Zcash mainnet” refer to in this package?** `FAQ.md` lines 123–125: this package “makes no use of the anchor.” The ZeeBeam release’s anchor transactions are not here. Expected: `GLOSSARY.md` session identifier; `CLAIM_BOUNDARY.md` line 38.

8. **What file is the authority-manifest digest a hash of?** Same as question 1. Public bytes 228–259. Expected: `STATEMENT.md` line 89; `FAQ.md` 2.

### Where each dataset comes from

9. **What did the August scene contain?** `README.md` lines 32–33: “What the scene contained is not described here.” `FAQ.md` lines 106–109. Expected: `README.md` primer; `FRAMES.md`.

10. **When were d2 and v10 recorded, and where are their frames?** `FAQ.md` lines 111–115: “does not carry the public location of those frames or their recording dates: **not decided at publication**.” Expected: `GLOSSARY.md` “d2, v10”; `RESULTS.md` section 1.

11. **Where are the 111 frames of rows 601–711 in this directory?** They are not. `FRAMES.md` points at the data layer. `FAQ.md` line 281: “Until the upload is released the prefix is empty.” Expected: `FRAMES.md`; `capsule/reexecute/` (only `frame_000600.raw` is present).

12. **Where are `oracle/final/august_inputs/row_*.npz` for rows other than 600, `oracle/rows/`, `oracle/rows_august/`, and `source/oracle_final/`?** Listed in `LARGE_FILES.md` lines 29–44; none of those directories exist here except `august_inputs/{manifest.json,coord_int.npy}`. Expected: `LARGE_FILES.md`; `VERIFY.md` sections 6–7.

13. **Where are the training-row frames 0–599?** `FRAMES.md` line 15: “The frames of the training rows 0 to 599 are not part of this package.” Four proofs take hints from rows 598, 587, 592, 597 (`STATEMENT.md` lines 196–197). Expected: `FRAMES.md`; `STATEMENT.md` section 7.

14. **Where is `NODE_PROVE_READY.md`?** `REDACTION.md` lines 99–101: not published; “it describes the rented node’s address, login, filesystem layout and backups.” Expected: `source/FULL_GUEST.md` as named companion.

15. **Where are `fill_results.py`, `stage_package.py`, `make_pins.py`, `evidence_allowlist.py`?** `FAQ.md` lines 283–285: “In the release desk’s staging repository, not in the package … **not decided at publication**.” Expected: `tools/`; `RESULTS.md` line 6.

### What “held out” means

The phrase itself is defined (`GLOSSARY.md` lines 134–136; `FAQ.md` 23–25). Remaining:

16. **Would the proved residual sums differ if the scale map were calibrated without the seven August rows?** `FAQ.md` lines 152–155: “Not measured.” Expected: `CLAIM_BOUNDARY.md` calibration disclosure; `VERIFY.md` section 7.

### What the results-table numbers mean, and whether they are good

Meanings of AUROC, paired fraction, `D`, `D_q`, `η`, MSE units, and the 112-row table columns are in `RESULTS.md` and `GLOSSARY.md`. Remaining:

17. **Are the numbers good relative to a null?** `RESULTS.md` lines 44–45; `FAQ.md` lines 165–169: “The package carries no random-network or shuffled-hint baseline and no confidence interval on the 112 August margins.” Expected: `RESULTS.md` section 1.

18. **Why are the August margins about half the d2/v10 margins?** `FAQ.md` line 171: “Reported, not explained; no explanation is on record.” Expected: `RESULTS.md` lines 125–131.

19. **By what written criterion was the 24,000-step seed-20260908 checkpoint chosen?** `RESULTS.md` lines 56–59: “No written criterion”; the ordering is “**[derived]**” from timestamps (`FAQ.md` 30). Expected: `RESULTS.md` section 2.

20. **What does the unresolved bf16 fidelity at 1.1e-3 imply for the float tables?** The package says it does not touch the proofs (`FAQ.md` 29; `oracle/final/README_FINAL.md` lines 84–92). It does not say how a reader should treat section 1’s float scores given that residual. Expected: `RESULTS.md` section 1; `README_FINAL.md` section 2.

### The wrong-row offset rule, including mirrors

The rule, the ten mirrored rows, the four training-row hints, and the guest/verifier split are specified (`STATEMENT.md` lines 189–206; `source/armc-relation/relation/src/rule.rs` lines 5–36). Remaining:

21. **Why these five offsets, why `(r - 600) mod 5`, and why mirror rather than skip?** `STATEMENT.md` lines 204–206; `FAQ.md` lines 201–205: “The principal set the rule; no further rationale is recorded.” Expected: `STATEMENT.md` section 7.

### The noise, and why it is a witness

The Philox rule, seed 20260823, call index `r-600`, and “bytes are normative” are stated (`STATEMENT.md` lines 208–220; `FAQ.md` 38–39). Remaining:

22. **What is the numerical difference between these bytes and a real CUDA `randn`?** `STATEMENT.md` lines 216–217: “Their correspondence to a CUDA generator is approximate and is not what the proof binds.” No measured discrepancy is given. Expected: `STATEMENT.md` section 8; `oracle/final/README_FINAL.md` section 5.

### Calibration disclosure

Who was used (15 rows, seven August, fourteen identities) is listed (`CLAIM_BOUNDARY.md` lines 21–34). Remaining: question 16 above.

23. **Which of the 188 tensors had their fractional bits set by the seven August rows, and by how much?** Histogram with vs without August is in `VERIFY.md` lines 375–377; per-tensor contribution is not. Expected: `oracle/final/constants_int16.json`; `FREEZE_SUMMARY.md`.

### The integer contract, and why int16

The contract (int16 weights/activations, i64 accumulation, two rounding rules, saturation, tables) is in `oracle/final/README_FINAL.md` section 3 and `STATEMENT.md` section 6. Remaining:

24. **Why int16 rather than int8, beyond “fidelity baseline” and `D_q/η` 80 vs 19?** `FAQ.md` lines 247–249: “The proving cost of int8 was not measured.” Expected: `AUDIT_TRAIL.md` round 2; `RESULTS.md` section 3.

### What the audits found

Verdict lines and round-6 finding subjects are in `AUDIT_TRAIL.md`. Remaining:

25. **Has the package as it stands after round 7 and the publication decision been re-read by Astra?** `AUDIT_TRAIL.md` lines 149–152; `FAQ.md` lines 255–260: no; “a publication decision.” Expected: `AUDIT_TRAIL.md`.

26. **What is in the withheld `prove.stderr` destructor-panic backtraces?** `receipts/README.md` lines 68–76; `RESULTS.md` lines 330–331: withheld, pinned only by digest in `receipts/SHA256SUMS_RUNS`. Expected: `receipts/README.md`.

27. **Where is `ASTRA_R6_APPLIED.md`?** `AUDIT_TRAIL.md` line 49: “on-box.” Expected: `audits/`.

### The patent mention

28. [Question about the patent filing's details redacted; the package states the filing by date only (`README.md`, `LICENSE`).]

### Who BOSUN is

The role is defined (`README.md` lines 67–70, 146–147; `GLOSSARY.md` lines 239–242). Remaining:

29. **Which Claude-family model, at what revision, and what was the replaced machine identity `BOSUN`?** `REDACTION.md` line 12: the box identity “reads `BOSUN`.” No model snapshot id is given. Expected: `GLOSSARY.md` “BOSUN”; `README.md` Provenance.

### Other facts the files say they do not contain

30. **What does the 28-byte `meta` field that “reads 64000 on every row” mean?** `GLOSSARY.md` lines 70–74; `FAQ.md` lines 42–46: “The meaning of the constant 64000 is not stated in any record in the package **[confirm]**.” Expected: `STATEMENT.md` line 115; `GLOSSARY.md` “`meta`.”

31. **Where is `CITATION.cff`, and where is `licenses/`?** `LICENSE` lines 35–36 and 58–61 name both; neither exists in this directory. Capsule notices are in `capsule/THIRD_PARTY_NOTICES.md`. Expected: package root, as `LICENSE` states.

32. **Is the data-layer prefix populated?** `FAQ.md` line 281 says it is empty until upload; `FRAMES.md`, `VERIFY.md` section 2a, and `capsule/README.md` tell the reader to download from it. This directory cannot settle which sentence is current. Expected: `FAQ.md` 49 vs `FRAMES.md`.

33. **How would a reader check that a drand round’s signature is the one the relay published, without the network?** `VERIFY.md` lines 287–293; `FAQ.md` 14: both the key comparison and the relay check “need the network.” Expected: `VERIFY.md` section 4; `PINS.json` `drand`.

---

## 4. Obstacles ranked by severity

**1. Contradictory publication status of the frames and August tensors (high).** After the 8 September decision, `FRAMES.md`, `REDACTION.md` lines 86–94, `VERIFY.md` section 2a, and `capsule/README.md` say the 112 frames and August tensors are published on the data layer. In the same tree:

- `VERIFY.md` lines 294–298: “the frames themselves are not published (`REDACTION.md`).”
- `FAQ.md` line 109: “the frames are held, so a reader cannot see it here.”
- `HASHES.md` lines 41 and 53: “needs the frame (held).”
- `HASHES.md` line 66: “the August input and vector sets held.”
- `replicate/README.md` lines 101–105: “**Raw frames are not published** (programme rule; `../REDACTION.md`).” and “**The August camera-derived tensors are held pending clearance**.”
- `replicate/replicate.sh` line 893: “raw frames are not published (REDACTION.md).”
- `REDACTION.md` line 63 still says python_oracle_rows.py’s “August inputs are held regardless.”
- `FAQ.md` line 281: “Until the upload is released the prefix is empty.”

In this copy, only `capsule/reexecute/frame_000600.raw` and `row_000600.npz` are present. An agent following one file is told to fetch 111 frames; following another is told they are held; following FAQ 49 is told the fetch URL is empty.

**2. Rebuild and re-prove assume a network and a GPU this package does not contain (high).** `VERIFY.md` section 2 and `replicate/README.md` “Honest limits” require rustup, cargo-prove, the succinct toolchain, crates.io, protoc, and (for prove) a 5.8 GiB circuit cache and an A100-class GPU. The guest ELF is “not shipped” (`PINS.json` line 6). The GPU prove wrapper is “**[untested here]**.” Checking proofs without trusting `capsule/zkdiff-verify` is therefore not possible from the tree alone.

**3. Capsule binaries are x86_64 Linux-only and must be trusted, or path (c) is required (high).** `capsule/STATIC_LINK_RECORD.txt` lines 10–11; `capsule/verify_offline.sh` line 28; `capsule/README.md` lines 75–78. No other architecture is provided.

**4. Steps that assume knowledge or files not in the package (high).** `oracle/final/README_FINAL.md` line 37 still starts `cd oracle/`. `build_reproducible.sh` line 21 comments `g2_guest/`. `LICENSE` names `CITATION.cff` and `licenses/`, which are absent. `regen_noise.py` needs numpy (`tools/regen_noise.py` line 15). `python_oracle_rows.py` needs torch, numpy, and data-layer npz files (`VERIFY.md` lines 369, 393–394). Quicknet signature checks need `https://api.drand.sh/…` (`VERIFY.md` lines 290–293). The ZeeBeam manuscript, eight-seed note, coupling packet, and sealed 288-row take are named as external (`CLAIM_BOUNDARY.md` lines 48–56; `FAQ.md` 20).

**5. Inconsistencies between files (medium–high).** FAQ 16 (“frames are held”) vs FAQ 17/55/62a (frames published). `HASHES.md` vs `FRAMES.md` on whether `BLAKE3(raw_r)` can be recomputed. `replicate/README.md` vs `capsule/README.md` on frames. `STATEMENT.md` line 89 shorthand `H(CONTEXT, …)` vs `HASHES.md` line 37 exact domain `ZEEBEAM_ORDERED_SESSION_CONTEXT_V1\0`. Receipts say `sp1_version: v6.1.0` while the package says SP1 6.4.0 (`FAQ.md` 10 explains this; a reader of receipts alone will misread it).

**6. Ambiguous or leftover wording (medium).** “Independently verified” “does not mean an independent organisation” (`FAQ.md` 45). “Held out” vs “untouched” needs `GLOSSARY.md` and `FAQ.md` 23–25 to avoid the earlier misreading that all 28 screen rows were held-out. `offset_rule` `standard` was renamed `direct` in published copies (`REDACTION.md` line 57); older audit texts still say `standard`. `VERIFY.md` line 34 names the directory `zkdiff_august_20260907`; this copy is `zkdiff_agent_audit_pkg`. Several `[confirm]` tags remain: August export regeneration (`VERIFY.md` line 360), full oracle regeneration (`VERIFY.md` line 420), meaning of meta 64000.

**7. Undefined or external acronyms and referents, even with a glossary (medium).** ARM-C is defined as “not an acronym” (`GLOSSARY.md` line 17). Remaining referents that the glossary sends outside the package: TB-v0.9 (manuscript §4), eight-seed AUROC, five-offset aggregate, original published checkpoint, coupling packet, sealed 288-row take, Dark Lantern, ZeeBeam 1.0.0 commit `ef686b33…48bd` (vendored verifier; `VERIFY.md` lines 68–71 says checking the lockfile digest needs a clone of that repository).

**8. Paths that do not resolve in this tree (medium).** `oracle/rows/`, `oracle/rows_august/`, `source/oracle_final/`, `oracle/final/august_inputs/row_*.npz`, `frames/frame_*.raw` except row 600 in the capsule, `licenses/`, `CITATION.cff`, `g1_integer/`, `ckpt/final/`, `../src/train_lean.py` as frozen in `README_FINAL.md` section 1. Copied scripts are said to resolve published locations when private ones are absent (`REDACTION.md` lines 43–46); the data those scripts then need is still on the empty-or-external data layer.

**9. Glossary and FAQ exist, but some terms stay marked unknown (low–medium).** `meta` 64000 (`GLOSSARY.md` line 72). `S_0` choice. Patent number. BOSUN’s model revision. Scene contents.

---

## 5. Three things the package does well

**1. A hard claim boundary, then a primer that a reader with no context can actually start from.** `CLAIM_BOUNDARY.md` lines 10–13: the three Astra paragraphs “govern every sentence,” and “a sentence elsewhere that seems to say more than they do is to be read as saying no more.” `README.md` lines 26–78 then define a row, the chain, ARM-C, held-out, BOSUN, and “where to start” (`bash capsule/verify_offline.sh`) without requiring the ZeeBeam manuscript first.

**2. An offline checking path that does not need crates.io.** `capsule/verify_offline.sh` (bash and coreutils only) runs Groth16 verification and every frozen-identity check on all 112 proofs; `capsule/reexecute/reexecute_row.sh` recomputes row 600’s 752-byte statement from a shipped 24,472,000-byte frame and compares it byte-for-byte. `tools/check_identities.py` and `tools/decode_zbdiff01.py` are standard-library. `tools/regen_noise.py` regenerates all 112 noise tensors from the stated Philox rule.

**3. The statement, the rule, and the hashes are written so they can be followed without guessing.** `STATEMENT.md` section 2 is a byte-offset table of the 752-byte `ZBDIFF01` layout; section 7 quotes `RULE_TEXT` and names the ten mirrored rows and the four training-row hints; `source/armc-relation/relation/src/rule.rs` is a pure function with a 112-row test. `HASHES.md` says of what each published hash is a hash, with the exact domain strings. `FAQ.md` answers the previous outside-agent round from the files and marks what remains “not decided at publication” instead of filling the gap.

---

## 6. Verdict

**YES WITH EFFORT** — an agent on x86_64 Linux can check all 112 Groth16 proofs and their frozen identities with `bash capsule/verify_offline.sh`, and can recompute row 600’s residual sums from the shipped frame; the same agent cannot rebuild the guest, cannot re-prove, and cannot recompute the other 111 rows from this directory alone.

**Single most important fix:** Delete or update every leftover “frames are held / not published” sentence (`VERIFY.md` 298, `FAQ.md` 109, `HASHES.md` 41 and 53, `replicate/README.md` 101–105, `replicate.sh` 893) so they match `FRAMES.md`, and either put the remaining 111 frames and `august_inputs/row_*.npz` files in the tree the way row 600 already is, or strike FAQ 49’s “Until the upload is released the prefix is empty” once that prefix actually holds the bytes those documents tell the reader to fetch.