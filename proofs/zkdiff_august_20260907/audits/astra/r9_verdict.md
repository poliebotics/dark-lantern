> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

**The freeze matches, but the privacy STOP is not closed.** No files were changed.

All 3,128 repository entries and 5,669 bundle payload objects validate, with no missing or unlisted payloads. The four additional bundle files are its declared controls. Both previews match their prepared payloads. Fresh verification accepted **112/112 proofs with both verifiers**, and the control run passed.

References: **R** = repository package (the package root), **D** = data-layer bundle (on-box: `publish_package`), **T** = transmit drafts (on-box: `transmit_drafts`). Findings in top-level R documents also occur in their identical `D/repository_package_front_matter/` copies.

1. **STOP: private infrastructure and desk instructions remain.** Round 7 cannot be certified as fully applied.

   | File:line | Remaining material |
   |---|---|
   | `D/build_kit/offline_build_test/DOWNLOADS.log:27` | `[download staging]` |
   | `R/audits/astra/r6_brief.md:12`; `audits/agents/claude_r1.md:53`, `claude_r2.md:64`, `grok_r1.md:99` | A retired private directory name |
   | `R/audits/astra/r6_brief.md:22` | “Standing rules”, including private attribution and patent-disclosure instructions |
   | `R/audits/astra/r1_brief.md:35` | A private storage instruction |
   | `R/source/FULL_GUEST.md:536` | GPU allocation stated as a pending decision at launch |
   | `R/audits/agents/claude_r2.md:124,145`; `codex_r2.md:161`; `grok_r2.md:139,196,252,291,327`; `R/AUDIT_TRAIL.md:43` | Reintroduced operator-command wording |
   | `R/audits/agents/claude_r2.md:137`; `grok_r2.md:260` | Reintroduced patent-detail requests and the pending-decision label |

   Apply the same public-copy redactions to the newly added reports and build logs.

2. **REVISE: the required participant disclosure is missing from `FRAMES.md` line 23.** It still describes only the programme’s rig. Add the round-7 masked-participant, recognisable-setting and non-anonymisation disclosure. README, FAQ and the data-layer frame notice already contain it.

3. **REVISE: the blanket assertion about offline-kit binary paths is false.** The three rebuilt capsule binaries are clean. Upstream toolchain binaries retain upstream build paths:

   | D path/member | Zero-based byte offset | Example |
   |---|---:|---|
   | `build_kit/toolchains/cargo_prove_v6.4.0_linux_amd64.tar.gz::cargo-prove` | 29,287,485; 29,386,034 | `/home/runner/.cargo/…`; `/build/src/build.rs` |
   | `build_kit/toolchains/sp1_gpu_server_v6.4.0_x86_64.tar.gz::sp1-gpu-server` | 4,066,425 | `/home/runner/.cargo/…` |
   | `build_kit/toolchains/rust-toolchain-x86_64-unknown-linux-gnu.tar.gz::./lib/rustlib/x86_64-unknown-linux-gnu/bin/gcc-ld/ld.lld` | 36,447 | `/home/runner/.cargo/…` |
   | `build_kit/toolchains/rustup-init` | 14,295,597 | `/build/openssl-sys-…` |

   Qualify the assurance to distinguish sanitised project binaries from unchanged upstream downloads. These examples expose upstream build environments, not owner infrastructure.

4. **REVISE: PINS still presents original hashes beside published-file locators.** The redaction ledgers explain the changes, but these fields need separate original and published digests:

   | `R/PINS.json` lines | Affected files |
   |---|---|
   | 821, 826 | Two historical build records |
   | 983 | Model evaluator JSON |
   | 3688 | Merged batch manifest |
   | 3698 | Proof controls |
   | 3702, 3712, 3722, 3732, 3742, 3752, 3762, 3772 | Eight GPU manifests |

   For example, the merged manifest now hashes to **`4617085dc9c8db2044dfc3a633704152b465df1526203743822114e953d2d95b`**, while `PINS.json:3688`, `HASHES.md:68` and `RESULTS.md:328` still give `e406e998…fffb`. The evaluator JSON now hashes to **`4f690865e28f8a2386f90bf69c0d528aef3557950e37a1317b5030fd31da8e09`**, against `871fa609…6496` in PINS.

5. **REVISE: nine PINS entries identify the wrong delivery location.** `R/PINS.json:1823,1827,1831,1835,1839,1843,1847,1851,1855` lists fixture NPZs under `large_files_sha256_data_layer`. They are present in `R/oracle/final/fixtures/`, already covered by the repository ledger, and absent from the bundle. Correct that classification.

6. **REVISE: the offline kit’s own verification instructions contain stale pins.** BUILD_KIT.md:289 (on-box: `BUILD_KIT.md` line 289) gives an obsolete manifest digest and size; line 309 does the same for `OFFLINE_BUILD_TEST.md`. Correct values:

   | File | Bytes | SHA-256 |
   |---|---:|---|
   | `KIT_MANIFEST.json` | 14,538 | `9069f217fb48b0296319a34b74d2be74e0bd476a5e006c0b718e83608cfa3937` |
   | `offline_build_test/OFFLINE_BUILD_TEST.md` | 10,894 | `a2e3e31be0da902a98f579eb2286882a9ac9f17555090371cb974a0f53fc5fa8` |

   Line 44’s total also needs updating to **9,279,814,132 bytes** across 27 files. All 25 actual kit-manifest entries agree with MANIFEST.jsonl; its two exclusions are explicit.

7. **REVISE: downloaded kit objects lack executable-mode restoration.** `D/build_kit/BUILD_KIT.md:109` directly executes downloaded `rustup-init`; line 164 directly executes `offline_cargo_home.sh`. HTTP download does not restore their executable bits. Add `chmod +x` for the binary and invoke the helper with `bash`, or explicitly restore both modes. The rehearsal’s mounted local kit bypassed this problem.

8. **REVISE: the offline rehearsal does not establish reproduction from the current source bytes.** `D/build_kit/offline_build_test/build_record_20260908T175020Z.txt:36` records source-inventory digest `d6343ce8…cf74`. Recomputing the driver’s exact 54-entry inventory gives **`000e25a86c1eb057ddc8fbb4e243151e174ea7e156962a80edbf758f39cfa997`**. The inventory named at line 37 is absent.

   Supply that inventory and explain the differences, or rehearse the current frozen sources. All seven lockfiles resolve against the shipped 674 registry crates and two git crates; all 32,661 vendor files validate. No missing Rust dependency was found. This is an evidence gap, not a demonstrated ELF mismatch. A rebuild was not executed during this read-only review.

9. **REVISE: round-8 finding 6 remains partly open.** `VERIFY.md` line 476 through line 478 still asserts that source, oracle and model bytes are unchanged since the afternoon rehearsal. Subsequent privacy edits changed all three, including the checkpoint. Restrict that assertion explicitly to the historical revision.

10. **REVISE: the copied Grok report contains terminal output.** `R/audits/agents/grok_r2.md:328` contains **149,330 characters**, including **10,019 ESC bytes**, of terminal-control output. Remove that line before refreezing.

11. **REVISE: audit-summary counts are wrong.** `R/AUDIT_TRAIL.md:71,194` says round 8 had seven REVISE findings; it had **eleven**. Line 74 says three unrehearsed steps remain; the current VERIFY correctly identifies **two**.

12. **PASS with classified residuals: the requested literal grep was rerun over both payloads and all six transmit files, following symlinks and scanning binary bytes.** It returned **704 occurrences in 146 files**: six `[home-path literal]`, two `the principal`, 271 `129.`, 413 `141.`, and twelve `10.66`. Every occurrence is listed below. The eight private-script matches are permitted by round 7. All remaining matches are numerical text, line references, or coincidental binary bytes. The other requested terms returned zero hits. No former-owner reference was established.

   ```text
   T/032_zkdiff_darklantern_commit.sh
     [home-path literal]: 32,34
     the principal: 232
   T/033_zkdiff_r2_bundle.sh
     [home-path literal]: 22,24,138,139
     the principal: 4

   R/audits/agents/grok_r2.md
     129.: 25
   R/oracle/final/agreement.json
     10.66: 18317,20088,20115,21786
   R/replicate/TEST_LOG_LAMBDA_A100.md
     129.: 121
   R/replicate/lambda_a100_20260908/build_cuda0.stdout
     129.: 43
   R/source/vectors_relation/august/chain_log.csv
     129.: 132
     141.: 144
   R/source/vectors_relation/gen_vectors.py
     129.: 125

   D/build_kit/circuits/groth16/v6.1.0/groth16_pk.bin
     129.: 19529289
   D/build_kit/toolchains/rust-1.98.0-x86_64-unknown-linux-gnu.tar.xz
     129.: 671844
   D/repository_package_large_files/oracle/rows/d2/C_003096.npy
     141.: 116
   D/repository_package_large_files/oracle/rows/v10/C_002510.npy
     141.: 18

   D/node_runs/gpu0/gpu_procs.csv
     10.66: 714
   D/node_runs/gpu3/gpu_procs.csv
     10.66: 1163
   D/node_runs/gpu5/gpu_procs.csv
     10.66: 1779
   D/node_runs/gpu6/gpu_procs.csv
     10.66: 1646
   D/node_runs/gpus_all.csv
     129.: 123,930,2101,2577,2591,2803,3019,3288,3578,3885,4284,4880,
           5244,5566,5950,6134,6306,6830,7357,7513,7611,7781,8249,
           9114,9398,9868,10465,10688,11459,11600,12375,12491,12746,13986
     141.: 99,433,962,1247,1946,2613,2688,3119,3228,3733,4153,4373,
           4705,6452,7163,7176,8101,8125,8430,8459,8914,9617,10035,
           10382,10517,11391,11553,11730,12986,13224,13495,13773,14084
   ```

   Each GPU row below applies to **both** `R/receipts/gpuN_gpu_mem.csv` and `D/node_runs/gpuN/gpu_mem.csv`.

   ```text
   N | 129. lines                                  | 141. lines
   0 | 149,681,918,1292,1474                        | 64,168,1034,1169,1582
   1 | 124,338,443,601,1393,1394,1596,1671           | 523,653,802,839,965,1540,1660
   2 | 330,1103,1314,1660                           | 588,965
   3 | 527,1258                                    | 341,490,566,970,1608,1657
   4 | 63,776,827,860,1290,1521,1638,1718            | 1064,1186
   5 | 383,890,1253,1585,1800                       | 312,943,1711
   6 | 1180,1590                                   | 93,1157,1410
   7 | 254,255,293,587,1053,1233,1617                | 16,59,819,842
   ```

   Frame rows identify `D/frames/frame_NNNNNN.raw`. Row 600 also applies to `R/capsule/reexecute/frame_000600.raw`. These are grep’s newline counts within binary data, not meaningful image lines; repeated numbers record multiple occurrences on one line.

   ```text
   Row | 129. lines              | 141. lines                          | 10.66 lines
   600 | 158                     | 121,156,177,278                      | -
   601 | 278                     | -                                    | -
   602 | 255                     | 135,153,159,254,275                  | 147
   603 | -                       | 126,157,193,195,202                  | -
   604 | -                       | 167,297                              | -
   605 | -                       | 213                                  | -
   606 | -                       | 189,220,304                          | -
   607 | 297,304                 | 127,127,137,163,172,280,288          | 166
   608 | 151                     | 117,128,162,278                      | -
   609 | 219                     | -                                    | -
   610 | 172,296                 | 205                                  | -
   611 | 260                     | 133,164                              | -
   612 | 224                     | 183,260                              | -
   613 | 151,174                 | 168                                  | -
   614 | -                       | 141,157,199                          | -
   615 | 159,271                 | -                                    | -
   616 | 130,134                 | 151,267                              | -
   617 | 112                     | 116,158                              | -
   618 | 171                     | 124,132,155,173,265                  | -
   619 | 137                     | 119,120,120,147,148,162,166,260      | -
   620 | -                       | 142,142,145,152,166,187              | -
   621 | 107                     | 106,143,266,275                      | -
   622 | -                       | 129,137,163,197                      | -
   623 | 176,179,184             | 304                                  | -
   624 | 341,362                 | 135,143,186,191,358                  | -
   625 | 217                     | 168,195                              | -
   626 | -                       | 145,280                              | -
   627 | 172                     | 257,275                              | -
   628 | -                       | 103,118,288                          | -
   629 | 182                     | 120                                  | -
   630 | 112,149                 | 73,129,145,149,169                   | -
   631 | 101,107,148             | 137                                  | -
   632 | 165                     | 90,102,110,111,121,223               | -
   633 | -                       | 138                                  | -
   634 | 119,281                 | 126,132,135                          | -
   635 | 176                     | 137                                  | -
   636 | 129                     | 268                                  | -
   637 | -                       | 275,283                              | -
   638 | -                       | 144,201                              | -
   639 | 107,125,128             | 131,253                              | -
   640 | 290                     | 115,272                              | -
   641 | 120,282                 | 122                                  | -
   642 | 145                     | 114,144,148,210                      | -
   643 | -                       | 125,207                              | -
   644 | 134,146                 | 122                                  | -
   645 | -                       | 109,176                              | -
   646 | -                       | 123,281                              | -
   647 | 120,142,167             | 289,317                              | -
   648 | 124                     | 107,115,119,256,297                  | -
   649 | 154,342                 | 149,255                              | -
   650 | 139,195                 | 136,227,277,297                      | -
   651 | 157                     | 101,104,120,228,295,299              | -
   652 | -                       | 124,127,138                          | -
   653 | 131                     | 192                                  | -
   654 | 135,139,276             | 305                                  | -
   655 | 125,159                 | 57                                   | -
   656 | 306                     | 120,126,133                          | -
   657 | -                       | 201,235                              | -
   658 | -                       | 152,279                              | -
   659 | 114,115,155,157,213     | 109,117,117,122,131,250,275          | -
   660 | 300                     | 144,159,178,191,204,211,308,347,349  | -
   661 | 132                     | 136,141,160,207,310                  | -
   662 | -                       | 106,107,115,154,221,238,273          | -
   663 | -                       | 118,153,324                          | -
   664 | 110,231                 | 121,151                              | -
   665 | 164                     | 148,154,303                          | -
   666 | 302                     | 94,113,117,129,131,152,174,182       | -
   667 | 116                     | 145                                  | -
   668 | 188                     | 252                                  | -
   669 | 155,185                 | 203,212,243                          | 262
   670 | 145,292                 | 152,292                              | -
   671 | -                       | 165                                  | -
   672 | 134                     | 278                                  | -
   673 | -                       | 147                                  | -
   674 | 123,125,156             | 110,142,163,169                      | -
   675 | 187                     | 140,204                              | 185
   676 | 190,196                 | 113,201                              | -
   677 | 250                     | 156                                  | -
   678 | 170,181,200,210,323     | 164,200,210,342,343                  | -
   679 | 301                     | 121,150                              | -
   680 | 155,167                 | -                                    | -
   681 | 125,149,292             | 107,126,190,285,286                  | -
   682 | -                       | 205                                  | -
   683 | 114,137                 | 167,296                              | -
   684 | 163                     | 175,300,321                          | -
   685 | 150                     | 268                                  | -
   686 | 185,281,332             | 148,234,310                          | -
   687 | 148,148,166             | 116,133                              | -
   688 | 279                     | 164,179,282,287                      | -
   689 | -                       | 98,98,107,146,159,211,237,237        | -
   690 | 158                     | 114,115,156,197                      | -
   691 | 127                     | -                                    | -
   692 | 178,277                 | -                                    | -
   693 | 293                     | 133,142,249                          | -
   694 | -                       | 115,125,161                          | -
   695 | 109,123,251,257         | 107,136,141,213                      | -
   696 | 190,352                 | 155,194,194,282                      | -
   697 | 127                     | 186                                  | -
   698 | 149,287                 | 207,317,341                          | -
   699 | 180,288                 | 144,191                              | -
   700 | 199                     | -                                    | -
   701 | 299                     | 103,107,108,111,120,162,163,260      | -
   702 | 131                     | 91,124                               | -
   703 | 213,331,333             | 146                                  | -
   704 | 150,159,174,197         | 133,155,208,209                      | -
   705 | 118,127,166             | 132,171                              | -
   706 | 312                     | -                                    | -
   707 | 162                     | 157,270                              | -
   708 | 118,142                 | 120,129,167                          | -
   709 | 125,189                 | 126,131                              | -
   710 | 144                     | 109,110,150,153                      | -
   711 | -                       | 187                                  | -
   ```

VERDICT: STOP: remove the remaining private infrastructure and desk-policy text from the shipped copies, then re-freeze.
hook: Stop
hook: Stop Completed
