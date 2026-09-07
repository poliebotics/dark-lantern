# Byte-sensitivity map: authoritative counts (2026-08-28, families separated)

Supersedes all earlier counts. The earlier discrepancies (desk 11,412/32; Sol's audit
11,413/31; a mixed-glob reading 11,410/34) all came from ONE cause: the CSV glob
`part_*.csv` matches BOTH the bit-0 map (`part_N.*.csv`) and the later bit-7 pass
(`part_msbN.*.csv`). Keyed by offset, the two experiments overwrote each other.
Counts must always be computed per family.

**Bit-0 (LSB) map — the declared experiment:** 11,444 offsets. **0 accepted;
11,412 clean verifier rejections; 32 operational failures** (exit -6/101 — reproducible
tooling/resource limits on those offsets, re-run 2026-08-28, not verifier decisions).

**Bit-7 (MSB) pass — supplementary, partial:** 9,274 offsets measured.
**0 accepted; 9,271 clean rejections; 3 operational failures.** Incomplete coverage;
report as supplementary only.

Supported wording: "no accepted mutation among the 11,444 tested bit-0 offsets (and none
among the 9,274 bit-7 offsets measured); a small number of offsets hit a reproducible
verifier tooling limit and are reported as such."
NOT supported: "all mutations cryptographically rejected", "byte-tight", any
whole-artifact/all-bits soundness claim, or any single pooled count across the two families.
