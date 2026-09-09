---
version: 1.1
date: 2026-09-09
status: the public archive control files the statistic desk verified its inputs against, by URL and digest
author: Cathal Ryan Hynes (author of record); drafted with BOSUN, the project's automated research assistant
---

# Control inputs

`code/select_2023.py` and the two verification scripts read the archives' `_control/` files (manifests, digest lists, validation and release records).
They are public objects of the Truth Beam data layer and are not copied here; the desk's copies had these digests and sizes, and the
public URL answered the status shown when this package was staged (a HEAD request from the release desk).

| archive | file | SHA-256 | bytes | public URL | HEAD |
|---|---|---|---:|---|---|
| unanchored_2024 | `CODE_PROVENANCE.json` | `ff28581a509eea2633ff037565d039151635694b3a3e6b1cdaf1a2b3e500cfd4` | 1,715 | https://data.truthbeam.com/archive/2024/truth_beam_20241219_unanchored/v1/_control/CODE_PROVENANCE.json | 200 |
| unanchored_2024 | `HDF5_VALIDATION.json` | `f5b420a6e905237d24f11d9d6da46210e691f40a7a8a0306d50b0e6bbbdf5992` | 8,639 | https://data.truthbeam.com/archive/2024/truth_beam_20241219_unanchored/v1/_control/HDF5_VALIDATION.json | 200 |
| unanchored_2024 | `MANIFEST.jsonl` | `ca80a33fc3b99d795809beb0cdb0facfbdd012f117c2d07750b35b5e77ecc8c2` | 2,064 | https://data.truthbeam.com/archive/2024/truth_beam_20241219_unanchored/v1/_control/MANIFEST.jsonl | 200 |
| unanchored_2024 | `PUBLICATION_RECEIPT.json` | `9c8e9e8c73ce736a8bf45519dfc1ec9cea274f9775608b846d77a4a2be97e66a` | 3,119 | https://data.truthbeam.com/archive/2024/truth_beam_20241219_unanchored/v1/_control/PUBLICATION_RECEIPT.json | 200 |
| unanchored_2024 | `README.md` | `aeedbd2950da9bb608234741a7c50317c42693e5cecbde8ffe9bb334c1cdcc8c` | 2,555 | https://data.truthbeam.com/archive/2024/truth_beam_20241219_unanchored/v1/_control/README.md | 200 |
| unanchored_2024 | `RELEASE.json` | `05e26978bb931d0f41bbfc520ba30210267de2b3322059ce08c12f141063f914` | 2,812 | https://data.truthbeam.com/archive/2024/truth_beam_20241219_unanchored/v1/_control/RELEASE.json | 200 |
| unanchored_2024 | `SHA256SUMS` | `a9377b72922a0050bfd83e374f432f4dee7720a2e9f3d88413258674d3b5dc8d` | 540 | https://data.truthbeam.com/archive/2024/truth_beam_20241219_unanchored/v1/_control/SHA256SUMS | 200 |
| old_truth_beams | `MANIFEST.jsonl` | `33a91c67db91849887004674f8b875be13ea01ba47c26adc9790b159863213db` | 2,508,136 | https://data.truthbeam.com/archive/2023/old_truth_beams/v1/_control/MANIFEST.jsonl | 200 |
| old_truth_beams | `NPY_VALIDATION.json` | `ab9b2d8df800b1b320fd44f53fdb5e5a3e9d07bb57df1420301979ef0182ae8e` | 8,306 | https://data.truthbeam.com/archive/2023/old_truth_beams/v1/_control/NPY_VALIDATION.json | 200 |
| old_truth_beams | `PUBLICATION_RECEIPT.json` | `f3f13b2cb9cfa7c0546fa5b5172095014391e784602ca96273f5b16457a33146` | 3,216 | https://data.truthbeam.com/archive/2023/old_truth_beams/v1/_control/PUBLICATION_RECEIPT.json | 200 |
| old_truth_beams | `README.md` | `00de36d36f60cbbd7c401c5f1f5291f410a845a9f4048d39c006d69f740be4dd` | 1,879 | https://data.truthbeam.com/archive/2023/old_truth_beams/v1/_control/README.md | 200 |
| old_truth_beams | `RELEASE.json` | `8a7efc1a1accea21ee61e2f7e9d817e50f3513dd1bdfe3deaa31d1f845d1d7fc` | 1,409 | https://data.truthbeam.com/archive/2023/old_truth_beams/v1/_control/RELEASE.json | 200 |
| old_truth_beams | `SHA256SUMS` | `b1abf59c2be99e9b885bddaa56ac39fa15fed0725bec12384ffeeeb7c89f0acb` | 850,753 | https://data.truthbeam.com/archive/2023/old_truth_beams/v1/_control/SHA256SUMS | 200 |
| trailer | `CID_REPRODUCTION.json` | `e314145d53d116b6fe062f21652f096ea2d813e43559bb84a42158d1cdfda457` | 1,396 | https://data.truthbeam.com/archive/2023/truth_beam_poliepals_trailer/v1/_control/CID_REPRODUCTION.json | 200 |
| trailer | `MANIFEST.jsonl` | `4feaedaf31162c434684450ebb06e746a87d7e32cfea4a40ab5d81f290a026cc` | 762,605 | https://data.truthbeam.com/archive/2023/truth_beam_poliepals_trailer/v1/_control/MANIFEST.jsonl | 200 |
| trailer | `NPY_VALIDATION.json` | `b31bcda5a2b67180dba32f2b06b7f81f4c7139b7357c549fe9e2cdb3c0e02c9d` | 1,433 | https://data.truthbeam.com/archive/2023/truth_beam_poliepals_trailer/v1/_control/NPY_VALIDATION.json | 200 |
| trailer | `PUBLICATION_RECEIPT.json` | `5842699805c83338131522b7737132ca978d6991a560a0efd909193c802692dd` | 3,117 | https://data.truthbeam.com/archive/2023/truth_beam_poliepals_trailer/v1/_control/PUBLICATION_RECEIPT.json | 200 |
| trailer | `README.md` | `447abd78524a3ea17ac0edf7786352830ab75a4eb7f33da5e997fb5d11bd591b` | 2,436 | https://data.truthbeam.com/archive/2023/truth_beam_poliepals_trailer/v1/_control/README.md | 200 |
| trailer | `RELEASE.json` | `4141267a695c47120a85d0b6ecbdeec4741a4054b3b948945d31aae169212d01` | 2,904 | https://data.truthbeam.com/archive/2023/truth_beam_poliepals_trailer/v1/_control/RELEASE.json | 200 |
| trailer | `SHA256SUMS` | `2ae6263b2bcee4740205b5c9722e73ba673fb6004b2e4fec1ec0c954fc25b3b8` | 251,849 | https://data.truthbeam.com/archive/2023/truth_beam_poliepals_trailer/v1/_control/SHA256SUMS | 200 |

The 2023 recorder source the report cites (`truth_beam_2023_REDACTED.py`) is published on the Truth Beam downloads page under
`recovery/recorder-source/`; the 2024 recorder (`secure_record.py`, `perlin.py`, `data_persistence.py`, `utils.py` at commit `bc8d2603`) is
`github.com/poliebotics/TruthBeam-2024`, and the 2024 archive's `CODE_PROVENANCE.json` carries the digests of those files.

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-09 | BOSUN | First version, rendered by the staging script. |
| 1.1 | 2026-09-09 | BOSUN | authorship line, 9 September 2026. |
