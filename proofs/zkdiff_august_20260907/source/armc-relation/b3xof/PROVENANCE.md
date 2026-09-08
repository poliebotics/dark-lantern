---
version: 1.0
date: 2026-09-07
status: verbatim-copy-of-proved-source
author: BOSUN
---

# zeebeam-b3xof-relation, copied verbatim from the proved tree

Source directory (read-only, the tree from which the 2 September 2026 proofs were built):
`[zeebeam repository clone]/bundle/proofs_20260902/source/deps/BOSUN/scratch/zeebeam_lambda_artifacts_20260824/reviews/post_hold_followup_closure_20260825T0446Z/b3xof_experiment_snapshot/source/sp1/relation/`

| file | sha256 (identical here and at the source) |
|---|---|
| `Cargo.toml` | `593c7f2ea00abf713df918a7ae53d87d193b6fe2491d3de8d426b7481b9280f7` |
| `src/lib.rs` | `6e3d873caa999053c449bff563227b4e99738e5a906653f5ed807ab15b5b43f3` |
| `src/blake3p.rs` | `d7be7b1c874fa4ba9b993ee9957c532219f6f133e5e84f91370badd97ce241b2` |
| `tests/counts.rs` | `d9b3dfbd788cfd5188d443fe967c9a4c59c80536454bdc6840699b4539a93f3e` |
| `tests/crosscheck.rs` | `26ff17768f7c3642755b2cfb285a9f84b03353b0d2b1d584618a76bc8f7a6433` |

Nothing in this directory other than this note was edited. What the relation crate uses from it: `blake3p::{hash, hash2, xof,
Hasher}` (pure-Rust BLAKE3, cross-checked against the upstream `blake3` crate in `tests/crosscheck.rs`), `derive_seeds`,
`expand_all` (the three 43,110-byte channel streams of a chain state), `octave_offset`, `GRID_H`, `GRID_W`, `RenderTables`,
`render_row_rgb` (the four-octave integer renderer, bit-exact to `tile_cpu.gen_channel_v2`), `advance_chain` (the v9 chain
advance), `META_BYTES`, `TILE_W`, `TILE_H`, `CHANNELS`, `TOTAL_BYTES_PER_CHANNEL`, `CONDITIONING_BYTES`.

## Log

- 1.0 (2026-09-07, BOSUN) — copied with `cp`, digests recorded with `sha256sum` on both sides.
