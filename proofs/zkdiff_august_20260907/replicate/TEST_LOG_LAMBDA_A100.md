---
version: 1.1
updated: 2026-09-09
status: active
author: Cathal Ryan Hynes (author of record); drafted with BOSUN, the project's automated research assistant
---

# Test log: replicate.sh, the whole ladder with `prove`, on a freshly launched Lambda A100-SXM4-40GB

> Published copy of the release desk's record of 8 September 2026. The rented instance's paths are redacted by the package's rule
> (`../REDACTION.md`) with labels of their own: `[package copy]/` is the instance's local copy of this package, `[work]/` its work
> directory, and `[home]`, `[cargo home]`, `[rustup home]`, `[sp1 home]` and `[local bin]` the installation targets. The hostname
> the batch tools stamped into the receipts and attempt ids reads `replication-box`; the instance was rented for this run and is
> not the batch's node. The GPU's UUID is left as recorded. Nothing else is changed; the private and published digests of every
> redacted artefact are in `lambda_a100_20260908/REDACTION_LEDGER.tsv`.

## The machine and the package

A Lambda `gpu_1x_a100_sxm4` instance launched for this run: Ubuntu 22.04.5 LTS, kernel 6.8.0-60-generic, glibc 2.35, 30 threads,
216 GiB RAM, one NVIDIA A100-SXM4-40GB (driver 570.148.08), 471 GB free on `/`, no container, uid 1000, and no Rust, SP1, protoc
or cargo home present. The earlier timing pilot and the batch itself ran on 80 GB cards (`../RESULTS.md` sections 5 and 6).

The package was copied in locally (`--from-local`) as staged at 16:50Z that day: a `SHA256SUMS` of 3,092 entries and
`expected_identities_august.json` at its as-frozen digest `6822cdce…d613` (this revision publishes the redacted copy and records
both digests in `PINS.json`). Every pin the run checked, the guest ELF, the program key, the circuit key, the constants blob, the
chain log's SHA-256 and BLAKE3, the 112 noise digests and the 112 statements, is a pin of this revision; the proofs, source, model,
noise, chain log and frames are the same bytes, and what changed after that hour is the redacted copies, the capsule rebuild, the
build kit, the audit texts and the papers (`../REDACTION.md`, the Logs). The row-600 frame was passed with `--frame` from a local
copy of the published `frame_000600.raw`; the re-executed and the re-proved statements bind its digest and both equal the published
statement byte for byte. `--repo-only` skipped the data-layer fetch, so the parity step did not run here; it was rehearsed in the
container (`TEST_LOG.md`).

## The run: 17:05:02Z to 18:07:28Z, `ALL DONE in 62m26s`

| step | measured | result |
|---|---|---|
| fetch (local copy), ledger, pins | 2 s | 3,092 ledger entries present and matching, no unlisted file; every pin agrees between the script, `PINS.json` and the frozen files |
| toolchain: rustup 1.29.1, Rust 1.98.0, b3sum 1.8.7, cargo-prove 6.4.0, succinct toolchain, protoc 21.12 | 27 s | every download at its pinned sha256; `cargo-prove sp1 (f66b4bf 2026-08-12)`, succinct rustc 1.94.0-dev with LLVM 21.1.8, libprotoc 3.21.12 |
| build (CPU features) | 2m34s | `BUILD_REPRODUCED_OK`: ELF `51b7bc35…75cc`, 396,200 bytes, vkey `0x00f01894…a027`, circuit key `4388a21c…e696`; lockfiles unchanged |
| verify | 0m52s | 112/112 proofs accepted by `zkdiff-verify` under the pinned key, circuit and constants; controls behaved; 112 noise files match `PINS.json` |
| quick | 3m25s | 112/112 `VERIFIED` by the standalone verifier with the circuit key embedded in `sp1-verifier` 6.4.0; both tamper controls rejected per proof |
| execute row 600: frame-independent legs | 22 s | `prepared_native`, 33 checks, beacons verified, noise BLAKE3 equal to the frozen table |
| execute row 600: the complete guest in the SP1 executor | 6m37s | `R_correct` 4,435,539,299, `R_wrong` 11,254,163,581, `D` +6,818,624,282, clip events 0; 14,400,363,198 instructions, 269,904 syscalls, max RSS 17,447,080 kB; 33 acceptance checks PASS; 752 public bytes byte-identical to the published statement (`EXECUTE PASS in 6m59s`, both legs) |
| CUDA prover: `sp1-gpu-server` 6.4.0, Groth16 v6.1.0 circuit cache, rebuild with the `cuda` feature | 4m34s | tarball `2946b0b4…c596`, binary `f68b85dc…d97c`; circuit tarball 6,211,807,514 bytes, sha256 `18beebb6…7810`, its seven files at their pinned identities; `BUILD PASS in 1m23s` reproducing the same ELF and key |
| prove row 600 on CUDA device 0 | 43m06s | a fresh Groth16 proof, 2,446 bytes wrapped (356 raw), sha256 `a381b80b…8be`; `prove_elapsed_ms` 2,539,814 (42.3 min), `setup_elapsed_ms` 1,249, CUDA setup 20.7 s, 15,972,262 constraints; GPU memory peak 28,435 MiB of 40,960 (30 s samples), `zkdiff-batch` max RSS 7,353,628 kB; verified and accepted cold under the pinned identities, all 35 acceptance checks PASS; its 752 public bytes byte-identical to the published statement (the proof bytes differ from the batch's, as Groth16 proofs are randomised) |

The pinned `sp1-cuda` client exited 134 from its destructor panic after the manifest and receipt were written, the behaviour the
batch showed on every row (`../FAQ.md` 61); the script judges the run by the receipt and by the cold verification, and both pass.

## What is published here

`lambda_a100_20260908/` holds the run's small artefacts, redacted as described above: the two build logs (`build_cuda0.stdout`
for the CPU build, `build_cuda1.stdout` for the `cuda` rebuild), `prepare_600/` and `execute_600/` (their batch manifests,
receipts, public values and progress logs), `prove_600/` (the batch manifest, the acceptance report `row_000600.verify.json`, the GPU
identity and memory samples, and under `row_000600/` the manifest, the receipt, the fresh proof in wrapped and raw form and its
public values), and from `verify/` the row-600 control report, the raw-form acceptance report and the noise digest lists. The
prover's own progress log and exit diagnostics stay on the release desk, as the batch's do (`../receipts/README.md`, `../FAQ.md`
61); the exit status, the panic and the `time` summary they carry are quoted above. The witness directories (derivable from the
published noise, chain log and frame), the 112 per-row `quick/` result files (their content is the table in the log below) and the
112 `verify/` acceptance reports of the published proofs (the same checks `capsule/verify_offline.sh` repeats) are not copied. The
full log follows.

## The full log

```text

[2026-09-08T17:05:02Z] ==> environment
  date        2026-09-08T17:05:02Z
  os          Ubuntu 22.04.5 LTS  kernel 6.8.0-60-generic x86_64  glibc 2.35
  cpu/mem     30 threads, 216 GiB RAM, 214 GiB available
  disk        471G free on /
  container   no   user uid 1000   HOME [home]
  gpu         GPU 0: NVIDIA A100-SXM4-40GB (UUID: GPU-54def825-67ad-1d7d-19d2-84ee7fd4fbb9);
  work        [work]
  log         [work]/out/replicate.log

[2026-09-08T17:05:02Z] ==> fetch: repository package proofs/zkdiff_august_20260907
[2026-09-08T17:05:03Z]  ok  copied from the local tree [package source copy] (no network)

[2026-09-08T17:05:03Z] ==> package ledger
[2026-09-08T17:05:04Z]  ok  SHA256SUMS: 3092 entries, every listed file present and matching, no unlisted file (build outputs and data-layer files excepted)

[2026-09-08T17:05:04Z] ==> pins: this script against PINS.json, the expected identities and the frozen files
   program vkey 0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027
   guest ELF sha256 51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc (396200 bytes), circuit v6.1.0, circuit key sha256 4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696
   constants blob sha256 73310ddab603cab5588d05e9ac4deb7e56466a6fae4bbf89244c32f2bd1a8b92 (3476866 bytes); expected identities sha256 6822cdcefa9a8833460287a3bb619fa63d0f3755d46dccc7db5418b261d6d613
   chain log sha256 5d9af297ae37119df15412f516a4543ee9f54b6aa66186abe478512fe9a1ff48, BLAKE3 754e5716e65a065e5ad3146131609a1fd12e8310d966fb6bf2d3de6c568e7f8b; 112 noise files, 112 expected rows, batch complete over 112 rows
   outcome counts recorded in PINS.json: {'positive': 112, 'zero': 0, 'negative': 0}
[2026-09-08T17:05:04Z]  ok  every pin agrees between this script, PINS.json and the frozen files
[2026-09-08T17:05:04Z]  ..  no repository root README.md here (a package-only copy); the data-layer control digests are not cross-checked against it
[2026-09-08T17:05:04Z]  ..  --repo-only: data-layer objects not fetched (parity needs them; nothing else does)

[2026-09-08T17:05:04Z] ==> toolchain: host Rust 1.98.0
[2026-09-08T17:05:04Z]  ..  download https://static.rust-lang.org/rustup/archive/1.29.1/x86_64-unknown-linux-gnu/rustup-init
[2026-09-08T17:05:04Z]  ok  downloaded, sha256 dda7234360b7f578ca8b0ddcb80145646fa61a67c1720a5abc7051b35c9fcb71: [work]/downloads/rustup-init
[2026-09-08T17:05:04Z]  ok  rustup 1.29.1 installed in [cargo home] and [rustup home] (pinned installer)
[2026-09-08T17:05:13Z]  ok  rustc 1.98.0 (88d9e12ae 2026-08-18); cargo 1.98.0 (797e8a9bc 2026-08-05) (rustup-verified channel download)
[2026-09-08T17:05:13Z]  ..  installing b3sum 1.8.7 from crates.io (independent BLAKE3 tool for the noise files and chain log)
[2026-09-08T17:05:19Z]  ok  b3sum b3sum 1.8.7

[2026-09-08T17:05:19Z] ==> toolchain: SP1 6.4.0 (cargo-prove, succinct guest toolchain, protoc)
[2026-09-08T17:05:19Z]  ..  download https://github.com/succinctlabs/sp1/releases/download/v6.4.0/cargo_prove_v6.4.0_linux_amd64.tar.gz
[2026-09-08T17:05:19Z]  ok  downloaded, sha256 8ad88ebd4d970f0b9b7561f9b5899242f01c7da6d04ec4bd5d09f4cf044a541b, 21210386 bytes: [work]/downloads/cargo_prove_v6.4.0_linux_amd64.tar.gz
[2026-09-08T17:05:20Z]  ok  cargo-prove installed, sha256 d8835f80b386d5025420d6b09e73ad825b822ac143e8ed09312b2e08018ff106
[2026-09-08T17:05:20Z]  ok  cargo-prove sp1 (f66b4bf 2026-08-12T14:40:11.709680161Z)
[2026-09-08T17:05:20Z]  ..  download https://github.com/succinctlabs/rust/releases/download/succinct-1.94.0-64bit/rust-toolchain-x86_64-unknown-linux-gnu.tar.gz
[2026-09-08T17:05:22Z]  ok  downloaded, sha256 12c94435d41bfe4e20131bbcce40b35abd32270ad792befc653af4e3fabc192f, 384963362 bytes: [sp1 home]/rust-toolchain-x86_64-unknown-linux-gnu.tar.gz
[2026-09-08T17:05:22Z]  ..  extracting the succinct toolchain to [sp1 home]/toolchains/succinct-1.94.0-64bit
[2026-09-08T17:05:31Z]  ok  rustup toolchain 'succinct' linked to [sp1 home]/toolchains/succinct-1.94.0-64bit: rustc 1.94.0-dev, LLVM 21.1.8
[2026-09-08T17:05:31Z]  ok  cargo +succinct resolves to cargo 1.98.0 (797e8a9bc 2026-08-05); target riscv64im-succinct-zkvm-elf and bundled ld.lld present
[2026-09-08T17:05:31Z]  ..  download https://github.com/protocolbuffers/protobuf/releases/download/v21.12/protoc-21.12-linux-x86_64.zip
[2026-09-08T17:05:31Z]  ok  downloaded, sha256 3a4c1e5f2516c639d3079b1586e703fc7bcfa2136d58bda24d1d54f949c315e8, 1585982 bytes: [work]/downloads/protoc-21.12-linux-x86_64.zip
[2026-09-08T17:05:31Z]  ok  protoc installed to [local bin]: libprotoc 3.21.12
[2026-09-08T17:05:31Z]  ..  cargo fetch --locked for the four lockfiles (the workspace's .cargo/config.toml is offline; overridden for this step only)
[2026-09-08T17:05:37Z]  ..  nested sp1-core-executor-runner-6.4.0: 352 locked packages fetched
[2026-09-08T17:05:37Z]  ..  nested sp1-core-executor-runner-binary-6.4.0: 342 locked packages fetched
[2026-09-08T17:05:38Z]  ok  crates fetched in 0m07s with every lockfile unchanged (--locked)

[2026-09-08T17:05:38Z] ==> build: reproducible rebuild of the guest ELF and the four host binaries (CUDA=0)
[2026-09-08T17:05:38Z]  ..  driver: source/armc-relation/build_reproducible.sh (offline, --locked, lockfiles compared before and after, ELF size / sha256 / vkey / circuit key asserted)
   build wall=129.90 s maxrss=3001344 KiB
   guest_elf_bytes=396200 guest_elf_sha256=51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc
   sp1_vkey=0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027
   sp1_circuit_version=v6.1.0 embedded_groth16_vk_sha256=4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696 verifier_sees_elf_sha256=51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc
   BUILD_REPRODUCED_OK sha256=51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc vkey=0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027 bytes=396200 groth16_vk_sha256=4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696 circuit=v6.1.0
[2026-09-08T17:08:12Z]  ok  BUILD PASS in 2m34s: ELF sha256 51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc, 396200 bytes; vkey 0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027 (derived from the rebuilt ELF by zkdiff-ceremony); embedded circuit key 4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696 (v6.1.0); record [package copy]/source/armc-relation/runs/build_record_20260908T170538Z.txt

[2026-09-08T17:08:12Z] ==> verify: acceptance verification of 112 proofs (Groth16 under the pinned key and circuit, then every frozen identity)
    row    u  off rule         R_correct       R_wrong             D class    clips noise BLAKE3     checks  result
    600  598   -2 direct      4435539299   11254163581   +6818624282 positive     0 bd4d83ec376a6990  35/35  ACCEPTED
    601  603   +2 direct      4823951305   11932687322   +7108736017 positive     0 0b87ded868d2dc01  35/35  ACCEPTED
    602  587  -15 direct      4590007358   12130484180   +7540476822 positive     0 cc30cefa7392c2db  35/35  ACCEPTED
    603  618  +15 direct      5122027412   10802701224   +5680673812 positive     0 23774fc9aad892b0  35/35  ACCEPTED
    604  634  +30 direct      6087916494   13965371628   +7877455134 positive     0 98cfdfbe0dabbf81  35/35  ACCEPTED
    605  603   -2 direct      4916531444   11288421007   +6371889563 positive     0 df909d68974210cc  35/35  ACCEPTED
    606  608   +2 direct      5024470742   11104550773   +6080080031 positive     0 abe2466de19d3d8e  35/35  ACCEPTED
    607  592  -15 direct      4735687836   11554387355   +6818699519 positive     0 73c39971afe7777e  35/35  ACCEPTED
    608  623  +15 direct      4871001070   11908069780   +7037068710 positive     0 96bb58310c40c666  35/35  ACCEPTED
    609  639  +30 direct      4507374860   11130879841   +6623504981 positive     0 b453e8a16070c857  35/35  ACCEPTED
    610  608   -2 direct      4666536664   11186278937   +6519742273 positive     0 48d2ba88340f2d2d  35/35  ACCEPTED
    611  613   +2 direct      4575288521   10983802241   +6408513720 positive     0 dff147f1d0ae98fb  35/35  ACCEPTED
    612  597  -15 direct      5358209283   12954561242   +7596351959 positive     0 ea19c97c75058527  35/35  ACCEPTED
    613  628  +15 direct      4824158933   11257462199   +6433303266 positive     0 4ece8350a2a817de  35/35  ACCEPTED
    614  644  +30 direct      4572016948   11845443551   +7273426603 positive     0 a2008f3cef3c9156  35/35  ACCEPTED
    615  613   -2 direct      4523859619   10490701351   +5966841732 positive     0 f3c42e0ff45685e1  35/35  ACCEPTED
    616  618   +2 direct      4385706399   10431058590   +6045352191 positive     0 33095c5539fa1731  35/35  ACCEPTED
    617  602  -15 direct      4559463982   11843717253   +7284253271 positive     0 9b9ccd3a9bc96c65  35/35  ACCEPTED
    618  633  +15 direct      4902469556   11633425888   +6730956332 positive     0 56e5b2405f396c6e  35/35  ACCEPTED
    619  649  +30 direct      5067769469   11067017234   +5999247765 positive     0 d70a62dab3082ed7  35/35  ACCEPTED
    620  618   -2 direct      4975330749   10815397450   +5840066701 positive     0 047b4b19b53e8848  35/35  ACCEPTED
    621  623   +2 direct      5078590739   11613945121   +6535354382 positive     0 86fdc96708b07fda  35/35  ACCEPTED
    622  607  -15 direct      4543818957   10585596819   +6041777862 positive     0 176c664df2ddaa07  35/35  ACCEPTED
    623  638  +15 direct      4949557373   11748174166   +6798616793 positive     0 1a65db4e25ca83dc  35/35  ACCEPTED
    624  654  +30 direct      4613443525   10838962138   +6225518613 positive     0 5d377eeeb6751f38  35/35  ACCEPTED
    625  623   -2 direct      5159255376   11331522376   +6172267000 positive     0 67a5d7f388e94dc4  35/35  ACCEPTED
    626  628   +2 direct      4843714129   10935809038   +6092094909 positive     0 05dc3255b7809042  35/35  ACCEPTED
    627  612  -15 direct      4558621865   11969286046   +7410664181 positive     0 964857d0c8f3254a  35/35  ACCEPTED
    628  643  +15 direct      4935201030   10418339413   +5483138383 positive     0 e6939dc6f8c01e6e  35/35  ACCEPTED
    629  659  +30 direct      5125105340   11961003020   +6835897680 positive     0 8b804a87dadc28ab  35/35  ACCEPTED
    630  628   -2 direct      5309320039   12604837717   +7295517678 positive     0 15201ca454bf4b39  35/35  ACCEPTED
    631  633   +2 direct      5466745821   11825143468   +6358397647 positive     0 d9cd359bd574a64c  35/35  ACCEPTED
    632  617  -15 direct      5265645292   12677834296   +7412189004 positive     0 c8e2e2df84107158  35/35  ACCEPTED
    633  648  +15 direct      4726823114   10639899484   +5913076370 positive     0 63bbbdc992042e9e  35/35  ACCEPTED
    634  664  +30 direct      5346587528   12284667227   +6938079699 positive     0 d655664afd441adb  35/35  ACCEPTED
    635  633   -2 direct      5062785011   12528591567   +7465806556 positive     0 f7b77d222f47035d  35/35  ACCEPTED
    636  638   +2 direct      5443361617   11779201602   +6335839985 positive     0 69903d4f7f9176ca  35/35  ACCEPTED
    637  622  -15 direct      4916494426   11310239419   +6393744993 positive     0 e55c0d379d48b6e1  35/35  ACCEPTED
    638  653  +15 direct      5285402432   11305743967   +6020341535 positive     0 78b345b61a2e49dd  35/35  ACCEPTED
    639  669  +30 direct      5126532295   12608218338   +7481686043 positive     0 dc940335809a21c0  35/35  ACCEPTED
    640  638   -2 direct      4897285821   11342739182   +6445453361 positive     0 97813246806712d6  35/35  ACCEPTED
    641  643   +2 direct      5075860465   11457031477   +6381171012 positive     0 2da42cab08fb8478  35/35  ACCEPTED
    642  627  -15 direct      4749560133   12091512892   +7341952759 positive     0 688feb37b7f73465  35/35  ACCEPTED
    643  658  +15 direct      4898813215   11684457167   +6785643952 positive     0 85345af9c79b00d6  35/35  ACCEPTED
    644  674  +30 direct      5533324021   11818908152   +6285584131 positive     0 5e19030f71c9f0e0  35/35  ACCEPTED
    645  643   -2 direct      5026142343   11492366229   +6466223886 positive     0 a62b3ffa04a71764  35/35  ACCEPTED
    646  648   +2 direct      5767880674   13499792315   +7731911641 positive     0 520787dcf3d1be06  35/35  ACCEPTED
    647  632  -15 direct      5186397509   13035407960   +7849010451 positive     0 804bcd520f1aad2a  35/35  ACCEPTED
    648  663  +15 direct      5192224437   12040281607   +6848057170 positive     0 8f5c6987b43d99f2  35/35  ACCEPTED
    649  679  +30 direct      5444954965   12830258671   +7385303706 positive     0 f00bc35994b37370  35/35  ACCEPTED
    650  648   -2 direct      5317378656   12210640988   +6893262332 positive     0 042851cc1a0a0615  35/35  ACCEPTED
    651  653   +2 direct      4998333707   12481092964   +7482759257 positive     0 b1e176000b3fb308  35/35  ACCEPTED
    652  637  -15 direct      5160303390   13088436257   +7928132867 positive     0 0a15a731f8102dee  35/35  ACCEPTED
    653  668  +15 direct      4868330663   11106040261   +6237709598 positive     0 c775145d27fae893  35/35  ACCEPTED
    654  684  +30 direct      5710721466   12644696292   +6933974826 positive     0 186c4109da2c78c0  35/35  ACCEPTED
    655  653   -2 direct      5750839157   12632159459   +6881320302 positive     0 b0c8a7dbbab9615e  35/35  ACCEPTED
    656  658   +2 direct      5285557464   12035687299   +6750129835 positive     0 22daca6a0d6a1107  35/35  ACCEPTED
    657  642  -15 direct      5434716713   12449114115   +7014397402 positive     0 50c7a5fdb282abf4  35/35  ACCEPTED
    658  673  +15 direct      4854121203   11334099797   +6479978594 positive     0 d80b1e1c1dcc9009  35/35  ACCEPTED
    659  689  +30 direct      5725459276   12359208397   +6633749121 positive     0 1ad2f388d2e7c61a  35/35  ACCEPTED
    660  658   -2 direct      4896376335   11118396387   +6222020052 positive     0 519fa26a51b32955  35/35  ACCEPTED
    661  663   +2 direct      4775594281   12091317850   +7315723569 positive     0 6e7221eadfdfc63f  35/35  ACCEPTED
    662  647  -15 direct      5245969995   11859249110   +6613279115 positive     0 b79f29da60e6b277  35/35  ACCEPTED
    663  678  +15 direct      4899953330   10977918290   +6077964960 positive     0 fcc75e65095c4ba2  35/35  ACCEPTED
    664  694  +30 direct      5302706732   12450397245   +7147690513 positive     0 5dc12fedc7c9cec7  35/35  ACCEPTED
    665  663   -2 direct      5181317442   12954927915   +7773610473 positive     0 78a33a8fe61ffe29  35/35  ACCEPTED
    666  668   +2 direct      5169597840   11458654389   +6289056549 positive     0 a56e083614b7d653  35/35  ACCEPTED
    667  652  -15 direct      5102556492   11530346080   +6427789588 positive     0 56214281422530ed  35/35  ACCEPTED
    668  683  +15 direct      5243871174   11602504638   +6358633464 positive     0 cbbaa8e0298ccccb  35/35  ACCEPTED
    669  699  +30 direct      4561795402   10899698512   +6337903110 positive     0 c232c743089e990f  35/35  ACCEPTED
    670  668   -2 direct      5083533811   11508376620   +6424842809 positive     0 a0009e6abc00a6a4  35/35  ACCEPTED
    671  673   +2 direct      4981975532   11895556447   +6913580915 positive     0 cb7101f1e8dd88ab  35/35  ACCEPTED
    672  657  -15 direct      5181038543   12691816337   +7510777794 positive     0 e088ea8513604ce2  35/35  ACCEPTED
    673  688  +15 direct      5280787775   11825438406   +6544650631 positive     0 22765e56ffafcd34  35/35  ACCEPTED
    674  704  +30 direct      5534719262   11436194599   +5901475337 positive     0 c3c6cd5511a17a1a  35/35  ACCEPTED
    675  673   -2 direct      5214035176   11396534755   +6182499579 positive     0 150c7faee1bc356a  35/35  ACCEPTED
    676  678   +2 direct      4932609170   10230152149   +5297542979 positive     0 ad99c884e9ec4c5a  35/35  ACCEPTED
    677  662  -15 direct      5081773770   12188252622   +7106478852 positive     0 38a47be9fad9dbb3  35/35  ACCEPTED
    678  693  +15 direct      4730558431   11337324504   +6606766073 positive     0 90dde9570905a7a1  35/35  ACCEPTED
    679  709  +30 direct      4934802437   10638182610   +5703380173 positive     0 996ffa2baea113e4  35/35  ACCEPTED
    680  678   -2 direct      5167916147   12493115473   +7325199326 positive     0 461892c0bc4ce93d  35/35  ACCEPTED
    681  683   +2 direct      5409733980   12939181488   +7529447508 positive     0 16b93b37a7248f29  35/35  ACCEPTED
    682  667  -15 direct      4838438931   10824907194   +5986468263 positive     0 31d3348037efb830  35/35  ACCEPTED
    683  698  +15 direct      4946939590   11311675823   +6364736233 positive     0 11ed31ec04c7eb65  35/35  ACCEPTED
    684  654  -30 mirrored    4587519841   11036216072   +6448696231 positive     0 ea4ac2f60b7322a7  35/35  ACCEPTED
    685  683   -2 direct      5548150908   12066201663   +6518050755 positive     0 8021647e506acc75  35/35  ACCEPTED
    686  688   +2 direct      5314167746   11842860114   +6528692368 positive     0 c0f5855bf08f49ed  35/35  ACCEPTED
    687  672  -15 direct      4963242017   11551274827   +6588032810 positive     0 baba5881f94a7a20  35/35  ACCEPTED
    688  703  +15 direct      4841581778   11239994291   +6398412513 positive     0 488bad3ce1b40c87  35/35  ACCEPTED
    689  659  -30 mirrored    4894556588   11147659620   +6253103032 positive     0 127ad851415ad019  35/35  ACCEPTED
    690  688   -2 direct      5442657796   12698876657   +7256218861 positive     0 eaf7f2b01116c680  35/35  ACCEPTED
    691  693   +2 direct      4917509079   11284160401   +6366651322 positive     0 ef8a4c5a70e20f21  35/35  ACCEPTED
    692  677  -15 direct      5143008198   12639906190   +7496897992 positive     0 3db5da16c633c6c6  35/35  ACCEPTED
    693  708  +15 direct      5269412499   11596141233   +6326728734 positive     0 d9ddce8112b41b78  35/35  ACCEPTED
    694  664  -30 mirrored    4783512956   12460530813   +7677017857 positive     0 a7fd8bbcf48b6940  35/35  ACCEPTED
    695  693   -2 direct      5239161374   11858520142   +6619358768 positive     0 d439c887631df3e7  35/35  ACCEPTED
    696  698   +2 direct      4967286323   11816796984   +6849510661 positive     0 3d339ad596ebd243  35/35  ACCEPTED
    697  682  -15 direct      4749653576   10738646493   +5988992917 positive     0 49afc7d1171c7631  35/35  ACCEPTED
    698  683  -15 mirrored    4952752881   11624188359   +6671435478 positive     0 091d2d38523da760  35/35  ACCEPTED
    699  669  -30 mirrored    4955936276   11525632550   +6569696274 positive     0 eb480d9f82fd6ab7  35/35  ACCEPTED
    700  698   -2 direct      4724044249   11513220408   +6789176159 positive     0 e88955d729eec989  35/35  ACCEPTED
    701  703   +2 direct      5300940198   12432585107   +7131644909 positive     0 cb1750b853e9fccd  35/35  ACCEPTED
    702  687  -15 direct      4474020640   11234185532   +6760164892 positive     0 3b63905144a4cff5  35/35  ACCEPTED
    703  688  -15 mirrored    4612875137   10855286722   +6242411585 positive     0 b0291412902858fc  35/35  ACCEPTED
    704  674  -30 mirrored    5342528676   11789818198   +6447289522 positive     0 1f7d7f7717f120dc  35/35  ACCEPTED
    705  703   -2 direct      5164179528   11807086631   +6642907103 positive     0 5507838cefc3feee  35/35  ACCEPTED
    706  708   +2 direct      5143459521   11972542769   +6829083248 positive     0 e33a74065542dd39  35/35  ACCEPTED
    707  692  -15 direct      5204111678   11733691667   +6529579989 positive     0 fec2cdeb85db2b74  35/35  ACCEPTED
    708  693  -15 mirrored    5886097238   12742354656   +6856257418 positive     0 c3f996f5cd4c3eab  35/35  ACCEPTED
    709  679  -30 mirrored    4799388897   10087236535   +5287847638 positive     0 f5584161c4ee06bb  35/35  ACCEPTED
    710  708   -2 direct      5017897337   12287619416   +7269722079 positive     0 5c9316a75b39876b  35/35  ACCEPTED
    711  709   -2 mirrored    5349837529   12264037322   +6914199793 positive     0 569e640200c5c893  35/35  ACCEPTED
   112/112 accepted; outcome classes {'positive': 112, 'zero': 0, 'negative': 0}; every accepted statement equals its receipt and its PINS.json entry
[2026-09-08T17:08:54Z]  ..  negative controls on row 600 (mutated public fields, proof bytes and program key must be rejected; mutated expected identities must be refused at the named check)
   18 controls, all behaved: policy, relation
[2026-09-08T17:09:04Z]  ok  raw form accepted: proofs/row_000600_groth16_proof.bin (356 bytes) + public_values/row_000600_public_values.bin (752 bytes)
[2026-09-08T17:09:04Z]  ok  112 noise files match PINS.json by sha256
[2026-09-08T17:09:04Z]  ok  b3sum: chain log BLAKE3 754e5716e65a065e5ad3146131609a1fd12e8310d966fb6bf2d3de6c568e7f8b and 112 noise-file BLAKE3 digests match the frozen expected identities
[2026-09-08T17:09:04Z]  ok  VERIFY PASS in 0m52s: 112/112 proofs accepted under vkey 0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027, circuit v6.1.0 (key 4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696), constants 73310ddab603cab5588d05e9ac4deb7e56466a6fae4bbf89244c32f2bd1a8b92; controls behaved; reports in [work]/out/verify/

[2026-09-08T17:09:04Z] ==> toolchain: host Rust 1.98.0
[2026-09-08T17:09:04Z]  ok  rustup present: rustup 1.29.1 (d95a37b6a 2026-08-13)
[2026-09-08T17:09:04Z]  ok  rustc 1.98.0 (88d9e12ae 2026-08-18); cargo 1.98.0 (797e8a9bc 2026-08-05) (rustup-verified channel download)
[2026-09-08T17:09:04Z]  ok  b3sum present: b3sum 1.8.7

[2026-09-08T17:09:04Z] ==> quick: Groth16 verification of 112 proofs under the pinned program key with the vendored standalone verifier
[2026-09-08T17:09:04Z]  ..  building the standalone verifier (209 locked crates: sp1-verifier 6.4.0 and sha2)
[2026-09-08T17:09:24Z]  ok  built in 0m20s: [package copy]/tools/standalone_verifier/target/release/zeebeam-standalone-verifier
    row    u  off rule         R_correct       R_wrong             D class    clips  raw proof sha256  result
    600  598   -2 direct      4435539299   11254163581   +6818624282 positive     0  f9b2f91a28551a5e  VERIFIED (2 tamper controls rejected)
    601  603   +2 direct      4823951305   11932687322   +7108736017 positive     0  422ab6528be31cb9  VERIFIED (2 tamper controls rejected)
    602  587  -15 direct      4590007358   12130484180   +7540476822 positive     0  f2fa24533dcbeed9  VERIFIED (2 tamper controls rejected)
    603  618  +15 direct      5122027412   10802701224   +5680673812 positive     0  9253de75e0297559  VERIFIED (2 tamper controls rejected)
    604  634  +30 direct      6087916494   13965371628   +7877455134 positive     0  345690d67d52bbb8  VERIFIED (2 tamper controls rejected)
    605  603   -2 direct      4916531444   11288421007   +6371889563 positive     0  d5c79936de3dc1e0  VERIFIED (2 tamper controls rejected)
    606  608   +2 direct      5024470742   11104550773   +6080080031 positive     0  0ce2a167e4aac668  VERIFIED (2 tamper controls rejected)
    607  592  -15 direct      4735687836   11554387355   +6818699519 positive     0  19cbf9a095558d4e  VERIFIED (2 tamper controls rejected)
    608  623  +15 direct      4871001070   11908069780   +7037068710 positive     0  b058fa4a29cd74c4  VERIFIED (2 tamper controls rejected)
    609  639  +30 direct      4507374860   11130879841   +6623504981 positive     0  dc39dcabe199c1a7  VERIFIED (2 tamper controls rejected)
    610  608   -2 direct      4666536664   11186278937   +6519742273 positive     0  be08dceba70c2d21  VERIFIED (2 tamper controls rejected)
    611  613   +2 direct      4575288521   10983802241   +6408513720 positive     0  798e11346e5b9420  VERIFIED (2 tamper controls rejected)
    612  597  -15 direct      5358209283   12954561242   +7596351959 positive     0  c2e9e47ea74a9291  VERIFIED (2 tamper controls rejected)
    613  628  +15 direct      4824158933   11257462199   +6433303266 positive     0  c06431910eec77c4  VERIFIED (2 tamper controls rejected)
    614  644  +30 direct      4572016948   11845443551   +7273426603 positive     0  5751e6cda3dd4c6e  VERIFIED (2 tamper controls rejected)
    615  613   -2 direct      4523859619   10490701351   +5966841732 positive     0  94efc878d74257a0  VERIFIED (2 tamper controls rejected)
    616  618   +2 direct      4385706399   10431058590   +6045352191 positive     0  c525a98d2ae4d6d6  VERIFIED (2 tamper controls rejected)
    617  602  -15 direct      4559463982   11843717253   +7284253271 positive     0  8b5a9347873b61c1  VERIFIED (2 tamper controls rejected)
    618  633  +15 direct      4902469556   11633425888   +6730956332 positive     0  2e3989e040dbab42  VERIFIED (2 tamper controls rejected)
    619  649  +30 direct      5067769469   11067017234   +5999247765 positive     0  4953147488dd6429  VERIFIED (2 tamper controls rejected)
    620  618   -2 direct      4975330749   10815397450   +5840066701 positive     0  899eb9935522b3fc  VERIFIED (2 tamper controls rejected)
    621  623   +2 direct      5078590739   11613945121   +6535354382 positive     0  197074ecc91a40ae  VERIFIED (2 tamper controls rejected)
    622  607  -15 direct      4543818957   10585596819   +6041777862 positive     0  ccc6c2d8102a6fd9  VERIFIED (2 tamper controls rejected)
    623  638  +15 direct      4949557373   11748174166   +6798616793 positive     0  77bbdb1df39d864f  VERIFIED (2 tamper controls rejected)
    624  654  +30 direct      4613443525   10838962138   +6225518613 positive     0  1cbc3736778efc2f  VERIFIED (2 tamper controls rejected)
    625  623   -2 direct      5159255376   11331522376   +6172267000 positive     0  d37989c8d1020a5b  VERIFIED (2 tamper controls rejected)
    626  628   +2 direct      4843714129   10935809038   +6092094909 positive     0  1b38fa804dce6880  VERIFIED (2 tamper controls rejected)
    627  612  -15 direct      4558621865   11969286046   +7410664181 positive     0  b7d8e6838b2eda34  VERIFIED (2 tamper controls rejected)
    628  643  +15 direct      4935201030   10418339413   +5483138383 positive     0  0367a1861cb8df8e  VERIFIED (2 tamper controls rejected)
    629  659  +30 direct      5125105340   11961003020   +6835897680 positive     0  ff72697dcd8e0ece  VERIFIED (2 tamper controls rejected)
    630  628   -2 direct      5309320039   12604837717   +7295517678 positive     0  b04bda23f712dfa0  VERIFIED (2 tamper controls rejected)
    631  633   +2 direct      5466745821   11825143468   +6358397647 positive     0  1641d17c4f82ff62  VERIFIED (2 tamper controls rejected)
    632  617  -15 direct      5265645292   12677834296   +7412189004 positive     0  6844cb5782730675  VERIFIED (2 tamper controls rejected)
    633  648  +15 direct      4726823114   10639899484   +5913076370 positive     0  0ee2e586b76bbe0e  VERIFIED (2 tamper controls rejected)
    634  664  +30 direct      5346587528   12284667227   +6938079699 positive     0  ff69ce8e041c98b6  VERIFIED (2 tamper controls rejected)
    635  633   -2 direct      5062785011   12528591567   +7465806556 positive     0  596faa01b40ccbbe  VERIFIED (2 tamper controls rejected)
    636  638   +2 direct      5443361617   11779201602   +6335839985 positive     0  e816bc97b5c60a17  VERIFIED (2 tamper controls rejected)
    637  622  -15 direct      4916494426   11310239419   +6393744993 positive     0  6050bb4c9de7bece  VERIFIED (2 tamper controls rejected)
    638  653  +15 direct      5285402432   11305743967   +6020341535 positive     0  dcc9d20399add051  VERIFIED (2 tamper controls rejected)
    639  669  +30 direct      5126532295   12608218338   +7481686043 positive     0  81f8232af1ee0726  VERIFIED (2 tamper controls rejected)
    640  638   -2 direct      4897285821   11342739182   +6445453361 positive     0  451d49a077374f06  VERIFIED (2 tamper controls rejected)
    641  643   +2 direct      5075860465   11457031477   +6381171012 positive     0  c30dd3414f6983f7  VERIFIED (2 tamper controls rejected)
    642  627  -15 direct      4749560133   12091512892   +7341952759 positive     0  72628e8e088aa771  VERIFIED (2 tamper controls rejected)
    643  658  +15 direct      4898813215   11684457167   +6785643952 positive     0  0397d666bd7ffdcf  VERIFIED (2 tamper controls rejected)
    644  674  +30 direct      5533324021   11818908152   +6285584131 positive     0  d9c536c0fba6752d  VERIFIED (2 tamper controls rejected)
    645  643   -2 direct      5026142343   11492366229   +6466223886 positive     0  9fea53614ed22f01  VERIFIED (2 tamper controls rejected)
    646  648   +2 direct      5767880674   13499792315   +7731911641 positive     0  0f816416b1204542  VERIFIED (2 tamper controls rejected)
    647  632  -15 direct      5186397509   13035407960   +7849010451 positive     0  4198fded1ceb02b7  VERIFIED (2 tamper controls rejected)
    648  663  +15 direct      5192224437   12040281607   +6848057170 positive     0  acbce3a0f00a5e44  VERIFIED (2 tamper controls rejected)
    649  679  +30 direct      5444954965   12830258671   +7385303706 positive     0  37c441d6331b6d7f  VERIFIED (2 tamper controls rejected)
    650  648   -2 direct      5317378656   12210640988   +6893262332 positive     0  4bf6b95b25f380af  VERIFIED (2 tamper controls rejected)
    651  653   +2 direct      4998333707   12481092964   +7482759257 positive     0  ca927c51478437c1  VERIFIED (2 tamper controls rejected)
    652  637  -15 direct      5160303390   13088436257   +7928132867 positive     0  cefc3e696813209e  VERIFIED (2 tamper controls rejected)
    653  668  +15 direct      4868330663   11106040261   +6237709598 positive     0  f8c8a1d93ceec189  VERIFIED (2 tamper controls rejected)
    654  684  +30 direct      5710721466   12644696292   +6933974826 positive     0  4f7c5b915f83ac6c  VERIFIED (2 tamper controls rejected)
    655  653   -2 direct      5750839157   12632159459   +6881320302 positive     0  61fc1d18f97e765d  VERIFIED (2 tamper controls rejected)
    656  658   +2 direct      5285557464   12035687299   +6750129835 positive     0  4508f4f5b46b7082  VERIFIED (2 tamper controls rejected)
    657  642  -15 direct      5434716713   12449114115   +7014397402 positive     0  fab1518c78ebc41e  VERIFIED (2 tamper controls rejected)
    658  673  +15 direct      4854121203   11334099797   +6479978594 positive     0  109e32bc295b76de  VERIFIED (2 tamper controls rejected)
    659  689  +30 direct      5725459276   12359208397   +6633749121 positive     0  2af7362ccc2ea7ee  VERIFIED (2 tamper controls rejected)
    660  658   -2 direct      4896376335   11118396387   +6222020052 positive     0  bb643028afe757f0  VERIFIED (2 tamper controls rejected)
    661  663   +2 direct      4775594281   12091317850   +7315723569 positive     0  1742c4ff3d2355d9  VERIFIED (2 tamper controls rejected)
    662  647  -15 direct      5245969995   11859249110   +6613279115 positive     0  d044d11a28442f5f  VERIFIED (2 tamper controls rejected)
    663  678  +15 direct      4899953330   10977918290   +6077964960 positive     0  017d623a312fcd82  VERIFIED (2 tamper controls rejected)
    664  694  +30 direct      5302706732   12450397245   +7147690513 positive     0  b14c325bbad40ac8  VERIFIED (2 tamper controls rejected)
    665  663   -2 direct      5181317442   12954927915   +7773610473 positive     0  425a541857146b3d  VERIFIED (2 tamper controls rejected)
    666  668   +2 direct      5169597840   11458654389   +6289056549 positive     0  80fea872c6fd8998  VERIFIED (2 tamper controls rejected)
    667  652  -15 direct      5102556492   11530346080   +6427789588 positive     0  e6953376bed209ed  VERIFIED (2 tamper controls rejected)
    668  683  +15 direct      5243871174   11602504638   +6358633464 positive     0  3aabf7d4860e6a86  VERIFIED (2 tamper controls rejected)
    669  699  +30 direct      4561795402   10899698512   +6337903110 positive     0  81d0b3c799b0773e  VERIFIED (2 tamper controls rejected)
    670  668   -2 direct      5083533811   11508376620   +6424842809 positive     0  4344a0b35832275f  VERIFIED (2 tamper controls rejected)
    671  673   +2 direct      4981975532   11895556447   +6913580915 positive     0  2405283b295194c4  VERIFIED (2 tamper controls rejected)
    672  657  -15 direct      5181038543   12691816337   +7510777794 positive     0  5c3bdd1cf684115d  VERIFIED (2 tamper controls rejected)
    673  688  +15 direct      5280787775   11825438406   +6544650631 positive     0  a36cdfd93d1f406b  VERIFIED (2 tamper controls rejected)
    674  704  +30 direct      5534719262   11436194599   +5901475337 positive     0  af0b97709550c48d  VERIFIED (2 tamper controls rejected)
    675  673   -2 direct      5214035176   11396534755   +6182499579 positive     0  bad80a204945dfe1  VERIFIED (2 tamper controls rejected)
    676  678   +2 direct      4932609170   10230152149   +5297542979 positive     0  6be8097aa00a71ec  VERIFIED (2 tamper controls rejected)
    677  662  -15 direct      5081773770   12188252622   +7106478852 positive     0  1105d91e552b92a4  VERIFIED (2 tamper controls rejected)
    678  693  +15 direct      4730558431   11337324504   +6606766073 positive     0  cf7ea52596e44d38  VERIFIED (2 tamper controls rejected)
    679  709  +30 direct      4934802437   10638182610   +5703380173 positive     0  b77788af73209c18  VERIFIED (2 tamper controls rejected)
    680  678   -2 direct      5167916147   12493115473   +7325199326 positive     0  bcbf09f0305935e3  VERIFIED (2 tamper controls rejected)
    681  683   +2 direct      5409733980   12939181488   +7529447508 positive     0  b4733b6ffa87993e  VERIFIED (2 tamper controls rejected)
    682  667  -15 direct      4838438931   10824907194   +5986468263 positive     0  0671480dbdd580a7  VERIFIED (2 tamper controls rejected)
    683  698  +15 direct      4946939590   11311675823   +6364736233 positive     0  9b0aa8c851c43671  VERIFIED (2 tamper controls rejected)
    684  654  -30 mirrored    4587519841   11036216072   +6448696231 positive     0  57659d042d055b7f  VERIFIED (2 tamper controls rejected)
    685  683   -2 direct      5548150908   12066201663   +6518050755 positive     0  47eaa117b141219f  VERIFIED (2 tamper controls rejected)
    686  688   +2 direct      5314167746   11842860114   +6528692368 positive     0  377fcbf46b11e0bf  VERIFIED (2 tamper controls rejected)
    687  672  -15 direct      4963242017   11551274827   +6588032810 positive     0  cf54121987f3f07f  VERIFIED (2 tamper controls rejected)
    688  703  +15 direct      4841581778   11239994291   +6398412513 positive     0  df1dcd8ac09511de  VERIFIED (2 tamper controls rejected)
    689  659  -30 mirrored    4894556588   11147659620   +6253103032 positive     0  82ee8bfdee655bcd  VERIFIED (2 tamper controls rejected)
    690  688   -2 direct      5442657796   12698876657   +7256218861 positive     0  1bab19c070698390  VERIFIED (2 tamper controls rejected)
    691  693   +2 direct      4917509079   11284160401   +6366651322 positive     0  1585c8f5843a6da7  VERIFIED (2 tamper controls rejected)
    692  677  -15 direct      5143008198   12639906190   +7496897992 positive     0  870db23944dc5e4f  VERIFIED (2 tamper controls rejected)
    693  708  +15 direct      5269412499   11596141233   +6326728734 positive     0  d2fc4b305b320854  VERIFIED (2 tamper controls rejected)
    694  664  -30 mirrored    4783512956   12460530813   +7677017857 positive     0  8aba61de7763752d  VERIFIED (2 tamper controls rejected)
    695  693   -2 direct      5239161374   11858520142   +6619358768 positive     0  2a574db1fb3cc233  VERIFIED (2 tamper controls rejected)
    696  698   +2 direct      4967286323   11816796984   +6849510661 positive     0  55768ebd8e056c93  VERIFIED (2 tamper controls rejected)
    697  682  -15 direct      4749653576   10738646493   +5988992917 positive     0  fde931bce67532fb  VERIFIED (2 tamper controls rejected)
    698  683  -15 mirrored    4952752881   11624188359   +6671435478 positive     0  8ae0cc40fd9fdbf9  VERIFIED (2 tamper controls rejected)
    699  669  -30 mirrored    4955936276   11525632550   +6569696274 positive     0  88db67e499833940  VERIFIED (2 tamper controls rejected)
    700  698   -2 direct      4724044249   11513220408   +6789176159 positive     0  20012ed34ea8f68e  VERIFIED (2 tamper controls rejected)
    701  703   +2 direct      5300940198   12432585107   +7131644909 positive     0  403026c3a8e565d6  VERIFIED (2 tamper controls rejected)
    702  687  -15 direct      4474020640   11234185532   +6760164892 positive     0  31529b4cee1c0cf4  VERIFIED (2 tamper controls rejected)
    703  688  -15 mirrored    4612875137   10855286722   +6242411585 positive     0  9c349ac20cc2648a  VERIFIED (2 tamper controls rejected)
    704  674  -30 mirrored    5342528676   11789818198   +6447289522 positive     0  803e447a5d16f003  VERIFIED (2 tamper controls rejected)
    705  703   -2 direct      5164179528   11807086631   +6642907103 positive     0  720f9e13c897670a  VERIFIED (2 tamper controls rejected)
    706  708   +2 direct      5143459521   11972542769   +6829083248 positive     0  cd8f133b2303d714  VERIFIED (2 tamper controls rejected)
    707  692  -15 direct      5204111678   11733691667   +6529579989 positive     0  6a2793659590b8cd  VERIFIED (2 tamper controls rejected)
    708  693  -15 mirrored    5886097238   12742354656   +6856257418 positive     0  d42b7b04525fe3a0  VERIFIED (2 tamper controls rejected)
    709  679  -30 mirrored    4799388897   10087236535   +5287847638 positive     0  c435bd0db62ccbd8  VERIFIED (2 tamper controls rejected)
    710  708   -2 direct      5017897337   12287619416   +7269722079 positive     0  b21eb4016760d1a5  VERIFIED (2 tamper controls rejected)
    711  709   -2 mirrored    5349837529   12264037322   +6914199793 positive     0  ab89837de15e4c15  VERIFIED (2 tamper controls rejected)
   112/112 proofs verified under 0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027
[2026-09-08T17:12:49Z]  ok  QUICK PASS in 3m25s: 112/112 Groth16 proofs verify under 0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027 with the circuit key embedded in sp1-verifier 6.4.0; the statements' identities are checked by verify

[2026-09-08T17:12:49Z] ==> execute: August row 600, frame-independent legs (chain log, beacons, tree, noise) natively
   status=prepared_native offset=-2 rule=direct wrong_row=598 raw_blake3_expected=9d4a0745dd0990b12ab8c94d524430dd3b3559face4d7d4d621c481a72087d4a
   beacons 31521690 and 31521690 verify and bind
   both patterns render to the chain log's digests
   leaf_r c8a1f369f1bce4d8e0313750681dd4cb95612532f2fac9a1e6f0b252b7ae9c59 and leaf_u c883a5a6723f394d2bd388045a274f979d0e5dd5a5b6083a7e462abddc66cc50 open to the committed root
   noise BLAKE3 equals the frozen normative table entry
   native statement accepted (33 checks): R_correct 4435539299 R_wrong 11254163581 D +6818624282 (positive), clip events 0
[2026-09-08T17:13:11Z]  ok  row 600 prepared: beacons verified and bound, chain advance and both emission renders reproduce the chain log, noise BLAKE3 equals the frozen table

[2026-09-08T17:13:11Z] ==> execute: August row 600 through the complete guest in the SP1 executor (about 14.4 G instructions, 6 to 7 minutes, 15 to 17 GB of RAM)
   R_correct 4435539299  R_wrong 11254163581  D +6818624282 (positive)  clip events 0
   instructions 14,400,363,198  syscalls 269,904  oracle native_reexecution  host peak RSS 16.6 GiB
   public values sha256 26b5b2d36f9211511bd3e3adff5a71f0700007f2b619440bb9d3603c4154e01b == the published receipt's; acceptance 33 checks PASS
   Elapsed (wall clock) time (h:mm:ss or m:ss): 6:37.23
   Maximum resident set size (kbytes): 17447080
[2026-09-08T17:19:48Z]  ok  EXECUTE PASS in 6m59s: row 600 re-executed on the CPU; its 752 public bytes are byte-identical to the published statement the proof commits to
[2026-09-08T17:19:48Z]  ..  parity skipped (--repo-only)

[2026-09-08T17:19:48Z] ==> toolchain: host Rust 1.98.0
[2026-09-08T17:19:48Z]  ok  rustup present: rustup 1.29.1 (d95a37b6a 2026-08-13)
[2026-09-08T17:19:48Z]  ok  rustc 1.98.0 (88d9e12ae 2026-08-18); cargo 1.98.0 (797e8a9bc 2026-08-05) (rustup-verified channel download)
[2026-09-08T17:19:48Z]  ok  b3sum present: b3sum 1.8.7

[2026-09-08T17:19:48Z] ==> toolchain: SP1 6.4.0 (cargo-prove, succinct guest toolchain, protoc)
[2026-09-08T17:19:49Z]  ok  cargo-prove present, sha256 d8835f80b386d5025420d6b09e73ad825b822ac143e8ed09312b2e08018ff106
[2026-09-08T17:19:49Z]  ok  cargo-prove sp1 (f66b4bf 2026-08-12T14:40:11.709680161Z)
[2026-09-08T17:19:50Z]  ok  present, sha256 12c94435d41bfe4e20131bbcce40b35abd32270ad792befc653af4e3fabc192f: [sp1 home]/rust-toolchain-x86_64-unknown-linux-gnu.tar.gz
[2026-09-08T17:19:50Z]  ok  rustup toolchain 'succinct' present: rustc 1.94.0-dev, LLVM 21.1.8
[2026-09-08T17:19:50Z]  ok  cargo +succinct resolves to cargo 1.98.0 (797e8a9bc 2026-08-05); target riscv64im-succinct-zkvm-elf and bundled ld.lld present
[2026-09-08T17:19:50Z]  ok  protoc present: libprotoc 3.21.12 ([local bin]/protoc)

[2026-09-08T17:19:50Z] ==> toolchain: CUDA prover (sp1-gpu-server 6.4.0, Groth16 circuit cache v6.1.0)
[2026-09-08T17:19:50Z]  ok  libcudart.so.12 on the library path (sp1-gpu-server links it)
[2026-09-08T17:19:50Z]  ..  download https://github.com/succinctlabs/sp1/releases/download/v6.4.0/sp1_gpu_server_v6.4.0_x86_64.tar.gz
[2026-09-08T17:19:51Z]  ok  downloaded, sha256 2946b0b46026b8689181eb05561ed0be2798114196893d5ef38e46f93c14c596, 133469274 bytes: [work]/downloads/sp1_gpu_server_v6.4.0_x86_64.tar.gz
[2026-09-08T17:19:55Z]  ok  sp1-gpu-server installed, sha256 f68b85dc3cff776a613df897ba6e7f8592d08482330b4165d46a8ee87aafd97c
[2026-09-08T17:19:57Z]  ok  sp1-gpu-server --version: 6.4.0
[2026-09-08T17:19:57Z]  ..  the Groth16 v6.1.0 circuit cache is absent or incomplete; fetching https://sp1-circuits.s3-us-east-2.amazonaws.com/v6.1.0-groth16.tar.gz (6211807514 bytes, about 5.8 GiB)
[2026-09-08T17:21:39Z]  ..  circuit tarball sha256 18beebb6cd0cc9b4d4a240ee4f49511da6c2a7e51724bad4232de538a9147810 (recorded; the seven files inside are the pinned identities)
tar: Ignoring unknown extended header keyword 'LIBARCHIVE.xattr.com.apple.provenance'
tar: Ignoring unknown extended header keyword 'LIBARCHIVE.xattr.com.apple.provenance'
tar: Ignoring unknown extended header keyword 'LIBARCHIVE.xattr.com.apple.provenance'
tar: Ignoring unknown extended header keyword 'LIBARCHIVE.xattr.com.apple.provenance'
tar: Ignoring unknown extended header keyword 'LIBARCHIVE.xattr.com.apple.provenance'
tar: Ignoring unknown extended header keyword 'LIBARCHIVE.xattr.com.apple.provenance'
tar: Ignoring unknown extended header keyword 'LIBARCHIVE.xattr.com.apple.provenance'
tar: Ignoring unknown extended header keyword 'LIBARCHIVE.xattr.com.apple.provenance'
[2026-09-08T17:22:57Z]  ok  Groth16 circuit cache installed and pinned: [sp1 home]/circuits/groth16/v6.1.0; tarball kept at [work]/downloads/v6.1.0-groth16.tar.gz

[2026-09-08T17:22:57Z] ==> toolchain: host Rust 1.98.0
[2026-09-08T17:22:57Z]  ok  rustup present: rustup 1.29.1 (d95a37b6a 2026-08-13)
[2026-09-08T17:22:57Z]  ok  rustc 1.98.0 (88d9e12ae 2026-08-18); cargo 1.98.0 (797e8a9bc 2026-08-05) (rustup-verified channel download)
[2026-09-08T17:22:57Z]  ok  b3sum present: b3sum 1.8.7

[2026-09-08T17:22:57Z] ==> toolchain: SP1 6.4.0 (cargo-prove, succinct guest toolchain, protoc)
[2026-09-08T17:22:57Z]  ok  cargo-prove present, sha256 d8835f80b386d5025420d6b09e73ad825b822ac143e8ed09312b2e08018ff106
[2026-09-08T17:22:57Z]  ok  cargo-prove sp1 (f66b4bf 2026-08-12T14:40:11.709680161Z)
[2026-09-08T17:22:59Z]  ok  present, sha256 12c94435d41bfe4e20131bbcce40b35abd32270ad792befc653af4e3fabc192f: [sp1 home]/rust-toolchain-x86_64-unknown-linux-gnu.tar.gz
[2026-09-08T17:22:59Z]  ok  rustup toolchain 'succinct' present: rustc 1.94.0-dev, LLVM 21.1.8
[2026-09-08T17:22:59Z]  ok  cargo +succinct resolves to cargo 1.98.0 (797e8a9bc 2026-08-05); target riscv64im-succinct-zkvm-elf and bundled ld.lld present
[2026-09-08T17:22:59Z]  ok  protoc present: libprotoc 3.21.12 ([local bin]/protoc)
[2026-09-08T17:22:59Z]  ok  crates already fetched (stamp [work]/out/cargo_fetch.v2.ok)

[2026-09-08T17:22:59Z] ==> build: reproducible rebuild of the guest ELF and the four host binaries (CUDA=1)
[2026-09-08T17:22:59Z]  ..  driver: source/armc-relation/build_reproducible.sh (offline, --locked, lockfiles compared before and after, ELF size / sha256 / vkey / circuit key asserted)
   build wall=57.88 s maxrss=3028860 KiB
   guest_elf_bytes=396200 guest_elf_sha256=51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc
   sp1_vkey=0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027
   sp1_circuit_version=v6.1.0 embedded_groth16_vk_sha256=4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696 verifier_sees_elf_sha256=51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc
   BUILD_REPRODUCED_OK sha256=51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc vkey=0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027 bytes=396200 groth16_vk_sha256=4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696 circuit=v6.1.0
[2026-09-08T17:24:22Z]  ok  BUILD PASS in 1m23s: ELF sha256 51b7bc3548d0a4fdb822aa8ed8c8982b5fe707900133d67d664fa3a732fc75cc, 396200 bytes; vkey 0x00f0189431f373a5a931f1db0c6abd9673e4176e653e0f84f97724d302fda027 (derived from the rebuilt ELF by zkdiff-ceremony); embedded circuit key 4388a21c687fdd5f218d7e3d13190cac4c5355818d3605fd5fb811df468ee696 (v6.1.0); record [package copy]/source/armc-relation/runs/build_record_20260908T172259Z.txt

[2026-09-08T17:24:22Z] ==> prove: August row 600 on CUDA device 0 (the timing pilot took 45.9 min on one A100-SXM4-80GB alone; the batch 61 to 67 min with eight processes sharing a node; VRAM peak about 28.5 GiB)
   index, uuid, name, driver_version, memory.total [MiB], memory.used [MiB]
   0, GPU-54def825-67ad-1d7d-19d2-84ee7fd4fbb9, NVIDIA A100-SXM4-40GB, 570.148.08, 40960 MiB, 0 MiB
[2026-09-08T18:07:28Z]  ..  zkdiff-batch exited 134 (the pinned sp1-cuda client panics in a destructor after the manifest is written; the receipt and the cold verification below decide)
   R_correct 4435539299  R_wrong 11254163581  D +6818624282 (positive)  clip events 0
   prove_elapsed_ms 2,539,814 = 42.3 min; setup_elapsed_ms 1249; proof 2446 bytes (raw 356); proof sha256 a381b80bd2b6c6fa0d697ead900771a4ca961153c0192bed110fef8660b9c8be
   GPU memory peak (30 s samples) 28435 MiB
   Elapsed (wall clock) time (h:mm:ss or m:ss): 43:05.55
   Maximum resident set size (kbytes): 7353628
[2026-09-08T18:07:28Z]  ok  PROVE PASS in 43m06s: a fresh Groth16 proof of row 600 verifies and is accepted cold under the pinned identities, and its 752 public bytes are byte-identical to the published statement (the proof bytes differ, as Groth16 proofs are randomised)
[2026-09-08T18:07:28Z]  ok  ALL DONE in 62m26s; log [work]/out/replicate.log
```

— BOSUN ⚓

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-08 | BOSUN | First version: the fresh-machine run of 17:05Z to 18:07Z, its artefacts and the redaction applied to them. |
| 1.1 | 2026-09-09 | BOSUN | authorship line, 9 September 2026. |
