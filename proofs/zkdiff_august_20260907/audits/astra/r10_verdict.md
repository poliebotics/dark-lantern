> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

**The frozen hashes match, but the privacy STOP remains open.** All seven supplied hashes matched before and after review. No files were changed.

References: **R** = repository package (the package root), **D** = data-layer bundle (on-box: `publish_package`), **T** = transmit drafts (on-box: `transmit_drafts`).

1. **STOP: two prohibited phrases survive across line breaks.** claude_r2.md:134 (on-box: `audits/agents/claude_r2.md` line 134) retains the pending-decision label wrapped across lines 134 and 135. Line 195 (on-box: `audits/agents/claude_r2.md` line 195) retains the operator-command phrase wrapped across lines 195 and 196. Exact single-line substitutions missed both. The other specifically named round-9 STOP targets are removed or reworded, including the three patent-detail questions. Apply whitespace-aware redaction and residue checks.

2. **REVISE: additional private operating language remains.** An operator-command phrase survives at `R/source/FULL_GUEST.md:505`, `R/source/armc-relation/script/src/ceremony.rs:2`, `ceremony_core.rs:7`, and `R/source/node_prep/G2D_NODE_RUNBOOK.sh:8`. These retain private launch mechanics. `T/033_zkdiff_r2_bundle.sh:26` also retains `[release staging]/snapshots` as its default, despite round 7’s explicit replacement with `SNAPROOT=${ZKDIFF_SNAPROOT:?}`. Neutralise the source comments and complete that replacement.

3. **REVISE: metadata descriptions disagree with the verified inventory.** RELEASE.json:3 (on-box: `RELEASE.json` line 3) reports the build kit as **27 files / 9,279,809,075 bytes**. Its complete total is **28 / 9,279,824,278**, correctly stated in `D/build_kit/BUILD_KIT.md:45` and `T/033_zkdiff_r2_bundle.preview.md:35,52`. The difference is `KIT_MANIFEST.json`, 15,203 bytes; no exclusion is stated in RELEASE. Also correct `R/HASHES.md:86` from **two** static binaries to **three**, and qualify `:89`: KIT_MANIFEST explicitly excludes itself and BUILD_KIT.md.

4. **PASS: round-9 findings 2–11 are closed.**

   | Prior finding | Verified closure and location |
   |---|---|
   | 2 | Participant, recognisable-setting and non-anonymisation disclosure: `R/FRAMES.md:17`. |
   | 3 | Upstream downloads distinguished from remapped project binaries: `D/build_kit/BUILD_KIT.md:392`, `R/VERIFY.md:231`, `R/PINS.json:1964`. |
   | 4 | Original/published digests separated and verified: `R/PINS.json:819,826,985,3697,3710,3712`; evaluator/merged-manifest descriptions corrected at `R/HASHES.md:64,68`, `R/RESULTS.md:328`. |
   | 5 | Nine NPZ fixtures correctly classified and hashed in the repository: `R/PINS.json:1861,1899`. |
   | 6–7 | Kit table, total and digests match; downloaded binary receives executable mode and helper uses bash: `D/build_kit/BUILD_KIT.md:45,112,168,295,317`. |
   | 8 | Current-source rehearsal evidence closes the gap: `D/build_kit/offline_build_test/build_record_20260908T191536Z.txt:36,58`. The shipped 54-entry inventory recomputes byte-for-byte to `000e25a86c1eb057ddc8fbb4e243151e174ea7e156962a80edbf758f39cfa997`. No rebuild was performed during this review. |
   | 9 | Unchanged-bytes assertion restricted to the historical round-6 revision: `R/VERIFY.md:481`. |
   | 10 | Grok report now ends at `R/audits/agents/grok_r2.md:327`; zero ESC/control bytes in shipped audit Markdown. Staging refuses surviving controls at `release_pkg/tools_release/stage_audits.py:167,171`. |
   | 11 | Eleven REVISE findings and two remaining unrehearsed steps: `R/AUDIT_TRAIL.md:71,74,194`. |

5. **PASS: file identities, inventories, modes and previews reconcile**, apart from finding 3’s descriptions. `R/SHA256SUMS:1` validates all **3,128 entries**, with exactly **3,129 files** including the ledger. `D/_control/MANIFEST.jsonl:1` validates **5,670 payload objects / 12,671,379,071 bytes**, with exactly **5,674 files** including the four declared controls. No missing or unlisted files. All **4,664 large files**, **18 front-matter copies**, **1,116 current pin comparisons**, and **21 executable modes** agree. The 032 ledger/mode checks (`.sh:77,147,219`) and 033 upload checks (`.sh:69,115`) match these inventories. Both previews match their bodies, frozen pins, totals and rendered changes (`032.preview.md:62,99,128`; `033.preview.md:27,52`). Both scripts pass syntax checking; neither was executed.

6. **PASS: no scientific-claim or renamed-reference regression identified.** All 112 decoded statements match the RESULTS table: 112 positive outcomes, zero clipping, unchanged reported residual statistics (`R/RESULTS.md:215,328`). The three boundary paragraphs remain verbatim in FULL_GUEST (`R/CLAIM_BOUNDARY.md:15,17,19`); STATEMENT retains execution binding and its stated limits (`R/STATEMENT.md:239`). No retired a retired private directory name reference or broken package-local Markdown link was found.

7. **PASS: requested literal scan completed, with residual dispositions below.** Following symlinks and scanning binary bytes yielded **3,060 occurrences in 189 files**:

   | Literal | Occurrences |
   |---|---:|
   | `[home-path literal]` | 6 |
   | `the principal` | 2 |
   | `/data/` | 2,249 |
   | `principal` | 107 |
   | `129.` | 271 |
   | `141.` | 413 |
   | `10.66` | 12 |

   Every other requested literal returned zero. The **696 numeric-prefix matches** comprise 223 measurement/duration values, two line references, two public tile filenames and 469 incidental binary sequences. None is an infrastructure IP address.

   Every non-numeric matching location follows. Ranges are inclusive. Repeated matches on one line share that location.

   **KEEP: private-script wiring explicitly permitted previously.**

   ```text
   T/032_zkdiff_darklantern_commit.sh
     [home-path literal]: 32,34
     the principal: 232
   T/033_zkdiff_r2_bundle.sh
     [home-path literal]: 22,24,138-139
     the principal: 4
   ```

   **REVISE: private snapshot default**, as finding 2:

   ```text
   T/033_zkdiff_r2_bundle.sh
     /data/: 26
   ```

   **KEEP: relative source, ledger and upstream filenames containing `/data/`.**

   ```text
   R/SHA256SUMS:541-542
   D/repository_package_front_matter/SHA256SUMS:541-542
   R/source/armc-relation/RELATION.md:187
   R/source/armc-relation/relation/src/hint.rs:3
   R/source/vectors_relation/MANIFEST.json:569
   R/source/vectors_relation/gen_vectors.py:15

   D/build_kit/crates/VENDOR_SHA256SUMS:
     66-71,2282-2283,2884,4375-4376,6722-6732,7082-7125,
     7226-7242,7251,7261-7268,7293,7302-7439,8052,9808,
     10974,14135,14834-14848,14860-14879,14895-14897,
     15721-15726,24208-24210,31496,32535
   ```

   **KEEP: public attribution, publication/selection history and redaction provenance containing `principal`.** Each location in this block applies explicitly to **both `R/<file>` and `D/repository_package_front_matter/<file>`**. AUDIT_TRAIL:164 uses “principal” to mean “main”; FAQ:211 contains two occurrences.

   ```text
   AUDIT_TRAIL.md:14,20,24,164,189,231-232
   FAQ.md:4,15-16,117,208,211,307,316
   FRAMES.md:4,14,155
   GLOSSARY.md:100,234,236,238,243-244
   LARGE_FILES.md:67
   PINS.json:3662
   README.md:4,66,68,149-150,157
   REDACTION.md:13-14,63,105,137
   STATEMENT.md:191
   VERIFY.md:504,562
   ```

   **KEEP: remaining historical quotations, role attribution and publication provenance.** The two r6-verdict occurrences mean “main”.

   ```text
   R/audits/agents/claude_r1.md:78,203,279,299
   R/audits/agents/claude_r2.md:125,164,227
   R/audits/agents/grok_r1.md:209
   R/audits/agents/grok_r2.md:228
   R/audits/astra/r6_verdict.md:13,17
   R/audits/astra/r8_brief.md:9
   R/capsule/README.md:117
   R/capsule/reexecute/README.md:16
   R/oracle/final/README_FINAL.md:14
   D/README.md:12,30
   D/frames/FRAMES.json:2
   D/frames/README.md:6
   T/033_zkdiff_r2_bundle.body.md:16
   ```

   **STOP/REVISE: remaining `principal` occurrences**, as findings 1–2:

   ```text
   STOP   R/audits/agents/claude_r2.md:195
   REVISE R/source/FULL_GUEST.md:505
   REVISE R/source/armc-relation/script/src/ceremony.rs:2
   REVISE R/source/armc-relation/script/src/ceremony_core.rs:7
   REVISE R/source/node_prep/G2D_NODE_RUNBOOK.sh:8
   ```

   **KEEP: checkpoint ZIP member names.** All **1,956 `/data/` occurrences** in `R/model/g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pt` are exactly the local-header and central-directory names of its 978 `data/0`–`data/977` members. They are not filesystem paths. Every matching LF-counted binary position is listed below; these are grep positions, not meaningful document lines.

   ```text
   335,347-348,386-387,390,419,478-480,712-715,1230-1232,
   1235-1236,1244,1300-1301,1346,1348,1373,1387-1388,
   1422-1423,1449,1458,1488,1541-1542,1559-1561,1688,
   1693-1694,1820,1847,1979,1981-1983,2231-2232,2280,2283,
   2808,2849-2850,3343,3347,3384,3386,3388,3928-3929,4433,
   4485,4487,4985-4986,4989,5501-5502,5549-5550,6061,6211,
   6215,6256,6259,6812-6813,6877,6879,7350,7352,7355,7500,
   7504,7555-7556,7558,8119-8120,8170,8663,8665-8666,9711,
   9750-9751,10259,10262,10351-10352,10354-10355,10834-10835,
   10871-10873,11369-11370,11373,11377,12431-12432,12470-12471,
   12971,12973,13074,13076,13535,13538,13590,13593-13595,
   14132,14135-14137,14517,14542-14543,14663,14665,14691,
   14813-14814,14840,14958-14959,15053,15064,15094-15095,
   15100-15101,15138,15153,15183-15184,15337,15339,15379-15380,
   15392,15400,15411-15413,15462,15529,15536,15540,15557,
   15589-15591,15653,15704-15706,15950,16178-16181,16666,
   17123,17125,17127,17130,17134,17136,17150,17164-17166,
   17225,17262-17264,17315,17374-17376,17399,17435,17437,
   17447,17466-17467,17500,17525-17527,17563,17595-17596,
   17609,17621-17622,17649,17675,17677-17678,17737,17809,
   17811,17842,17868,17871-17872,17874,18014,18134,18142,
   18145-18147,18255,18346,18348,18385,18419-18422,18551,
   18670-18672,18895,19132,19184,19243,19245-19247,19694,
   20150-20152,20181,20205-20209,20211,20669,21169-21171,
   21246,21309-21310,21312,21314,21831,22372-22375,22377-22378,
   22835,23317-23318,23364,23419-23422,23424,23868,24392-24394,
   24878,25386,25443,25497-25500,25973,26482-26483,26486-26487,
   26653,26815-26816,26819,26874,26933-26936,26938,27446,
   27916-27917,27970,28021-28023,28025,28463,28895,28897-28899,
   29059,29194,29196,29199,29250,29301-29304,29779,30267-30268,
   30321,30375-30376,30379-30380,30859,31354-31355,31357-31358,
   31360,31365,32295,33293-33295,33333,33376-33377,33379-33380,
   33886,34340-34341,34444,34541-34543,35028,35476-35478,
   35538,35596,35599,35601-35602,36065,36603,36606-36607,
   36609,37551,38494-38496,38539,38593,38595-38597,39081,
   39584-39585,39688,39794-39796,39800,40256,40706,40756,
   40805-40807,41293,41782-41785,41787,42117,42447-42449,
   42474,42498-42501,42630,42746-42747,42781,42820-42821,
   42824,42826,42937,43077-43079,43109,43135-43136,43262,
   43361-43363,43365-43366,43451,43528,43546,43554,43585,
   43616,43623,43627-43628,43660,43692,43695,43708,43741,
   43777-43778,43928,44063-44064,44113,44176-44179,44185,
   44191,44198,44200-44214
   ```

VERDICT: STOP: remove the wrapped private desk phrases and make their residue checks whitespace-aware before re-freezing.
hook: Stop
hook: Stop Completed
