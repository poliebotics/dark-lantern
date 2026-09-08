# capsule/reexecute/: recompute a row's statement from its raw frame

| file | what |
|---|---|
| `zkdiff-batch` | the batch driver (`source/armc-relation/script/src/batch.rs`), statically linked (SHA-256 `005c2665fe4175bf52bc792cf1fdd4078904556a093dc500d420ffad9c02f2a0`, 47,789,192 bytes); its `execute` mode runs the complete guest program in the SP1 executor on the CPU (the pinned RISC-V ELF, executed but not proved), checks the guest's statement against the host's native re-evaluation of the same relation (`oracle_mode: native_reexecution` in the receipt) and writes the row's 752-byte statement and a receipt |
| `frame_000600.raw` | the raw Bayer frame of row 600, 24,472,000 bytes; BLAKE3 `9d4a0745…7d4a` (the chain log's and the statement's), SHA-256 `5c8e7856…211c` (the receipt's `raw_sha256`) |
| `row_000600.npz` | the Python oracle's input arrays for row 600 (`C_int`, `noise_int`, `noise_f32`, `Ct_int`, `E_correct`, `E_wrong`), SHA-256 `25cc926b…5276`; the same file for every row is on the data layer (`oracle/final/august_inputs/`) |
| `reexecute_row.sh` | `reexecute_row.sh` for row 600 with the shipped frame; `reexecute_row.sh ROW --frames-dir DIR` for any row with a frame from the data layer (`FRAMES.md`) |
| `BUILD_RECORD.txt`, `STATIC_LINK_RECORD.txt` | the rebuild and relink records (the same rebuild as `../BUILD_RECORD.txt`) |
| `SHA256SUMS` | every file above; the script checks it first |

The script needs bash, coreutils, about 17 GB of RAM and 4 to 7 minutes per row, and the package around it (chain log, noise,
constants blob, expected identities, the published statements). It writes under `$CAPSULE_OUT` (default `/tmp/zkdiff_capsule_out`).
Exit 0 means the recomputed statement is byte-identical to the published one. The batch driver refuses a frame whose BLAKE3
differs from the chain log's for that row. These frames and arrays were held in an earlier revision of this package and are
published by the principal's decision of 8 September 2026 (`REDACTION.md`). The August frames depict a masked participant in a
recognisable indoor setting. Camera-derived tensors retain images of participants and their surroundings, including
earlier-session examples. These materials are not anonymised; identity may be inferred from clothing, movement or context.
