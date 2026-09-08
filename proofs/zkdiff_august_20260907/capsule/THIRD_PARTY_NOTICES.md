# Third-party material in capsule/

The two executables and `reexecute/zkdiff-batch` are compiled from the first-party Rust sources published in this package
(`source/`, `tools/standalone_verifier/`) together with the Rust crates they depend on and the GNU C Library, statically
linked. Their sources and lockfiles are in this package and the rebuild is described in `README.md`; the vendored crates are
published on the data layer in the offline build kit (`build_kit/`, `LARGE_FILES.md`), so the binaries can be rebuilt without
the network.

**Rust crates.** The crates, their versions and their declared licences (from `cargo metadata` on the locked dependency
graphs) are listed in `THIRD_PARTY_CRATES_zkdiff-verify.tsv` (522 packages; `zkdiff-batch` shares the same graph) and
`THIRD_PARTY_CRATES_standalone_verifier.tsv` (209 packages); the five packages without a declared licence are this package's
own crates. Where a crate offers a choice of licences, the material is used under the first permissive option in the order
MIT, Apache-2.0, BSD. The licences relied on are MIT, Apache-2.0 (in three crates with the LLVM exception), BSD-2-Clause,
BSD-3-Clause (`subtle`, `sha1_smol`, `matchit` together with MIT), ISC, Zlib (`const_format`, `konst`, `foldhash` and their
macro crates), Unicode-3.0 (the `icu4x` crates, `unicode-ident`, `yoke`, `zerovec`, `zerofrom`, `zerotrie`, `tinystr`,
`litemap`, `writeable`, `potential_utf`), MPL-2.0 (`dynasm`, `dynasmrt`, `option-ext`), Unlicense (`memchr`, `aho-corasick`,
`byteorder`, at the user's option with MIT), CC0-1.0 and CDLA-Permissive-2.0 (declared by single crates). Each crate's own
licence file and copyright notice travel with its source in the build kit; the texts of the licence families are in the
repository's root `licenses/`. The SP1 crates (Succinct Labs) are MIT or Apache-2.0 at the user's option.

**The GNU C Library.** glibc 2.43 (Ubuntu 26.04, package `libc6-dev` 2.43-2ubuntu2.3) is linked statically into all three
binaries. glibc is licensed under the GNU Lesser General Public License, version 2.1 or later, with some files under other
free licences; the text is `licenses/LGPL-2.1.txt` in the repository root. Section 6 of the LGPL permits this static linking
provided the recipient can relink with a modified library: the first-party object code is reproducible from the published
source and lockfiles with the pinned toolchain (`README.md` here, `VERIFY.md` section 2, the build kit), and a reader who wants
the binaries against another glibc rebuilds them the same way on a system carrying that glibc. The glibc source of the Ubuntu
package is `apt source glibc` on Ubuntu 26.04 or https://www.gnu.org/software/libc/. The locale metadata compiled into glibc
(the ISO 14652 identification block naming its maintainer) is upstream glibc content and is left as distributed.

**`groth16_vk.bin`.** Succinct Labs' SP1 v6.1.0 Groth16 verifying-key artefact (MIT or Apache-2.0 at the user's option), the
same 492-byte file the Dark Lantern repository already distributes under `proofs/coupling/`; the licence texts are
`licenses/MIT-Succinct-Labs.txt` and `licenses/Apache-2.0-Succinct-Labs.txt` in the repository root. The same key is embedded
in both verifier binaries through the `sp1-verifier` crate.

The repository's root `THIRD_PARTY_NOTICES.md` carries the rows for these binaries and this key.
