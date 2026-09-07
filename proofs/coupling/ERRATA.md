> **Publication status (5 September 2026).** Historical public subset of the frozen packet. 51 of the 64 paths listed in `packet_v1/PACKET_SHA256SUMS` ship; 13 are absent. Of the 51 present paths, 29 retain their historical digest and 22 differ because of redaction or repacking. `packet_v1/` also contains 1 publication note not listed in that historical manifest. Historical manifests do not validate this publication; root `SHA256SUMS` alone controls publication bytes. This subset permits inspection of the supplied proof, but not rebuilding or full reproduction.

> **Publication note (5 September 2026).** The figures and acceptance commands below describe the unredacted 24 August freeze. They do not describe or validate this trimmed publication and will fail against it. Use the repository-root `SHA256SUMS` for publication integrity; see the publication-subset notices for omissions.

# ERRATA — coupling_20260823 (proof 1 / L1-1), packet_v1 scope record

Filed 2026-08-24T18:40Z by BOSUN-worker/BOSUN (Lambda BOSUN sub-mind), shipping-artifact audit.

**THE ARTIFACT'S BYTES ARE UNCHANGED BY DESIGN.** `packet_v1/PACKET_SCOPE.json` is entry 2 of
`packet_v1/PACKET_SHA256SUMS`; its own sha256 is
`9f85f8ec4908c9024f4c217af5f512765a5696f547d98988c8279ecf29c27ad2` and the manifest's is
`c7460c360ad5dfa62ec044da2795519ff27a07eb32ab54674a2c377aac40564c` (both recomputed today; an
earlier sweep note attached `c7460c36…` to the wrong file — it is the manifest's hash, since the
manifest excludes itself). `RESULTS_PACKET_v1.md` and `RECEIPT_NARRATIVE.md` both advertise
**64/64 OK**, and `NARRATIVE.md` makes acceptance require *both* `sha256sum -c
PACKET_SHA256SUMS` *and* exact equality between its listed paths and the packet's regular-file
set. An in-place edit would break the hash check; a new file inside `packet_v1/` would break the
path-set check. **That is why this errata sits one level up, beside `packet_v1/`, and not
inside it.** Both packet acceptance tests passed unchanged on the unredacted freeze; they fail against this publication (publication status above).

**How to cite.** Anyone reading `relation.sp1_instructions` from `PACKET_SCOPE.json` must read
this errata with it.

---

## 1. `relation.sp1_instructions` states a row-specific count as a property of the relation (material)

Offending text, `packet_v1/PACKET_SCOPE.json` line 54, verbatim:

```
    "sp1_instructions": 203004795,
```

It sits inside the `"relation": { … }` object (lines 51–59), beside `private_input_bytes`,
`public_values_bytes`, `typed_root`, `score_numerator` and `score_denominator`. In
machine-readable form that says "the relation is 203,004,795 instructions", and
`relation.sp1_instructions` is exactly the field a tooled verifier or an llms.txt agent would
parse as the relation's expected instruction count. The object deliberately mixes two kinds of
value — `private_input_bytes` 458752 and `public_values_bytes` 344 are structural invariants,
identical on every witness, while the count, the root and the score belong to one row — with no
annotation distinguishing them. Nothing anywhere in the 81-line file names the witness row: a
grep for `august|712|row` returns only `verification_rows_accessed`. The file's own
`"status": "SEALED_FOR_COLD_VERIFY"` declares its audience to be the cold third-party
replicator.

The count is row 96's. Measured under the same frozen ELF (source of record
`experiments/proof6_aggregation_v1/FEAS_new-witnesses.md`, sha256
`92c769d8d250a2974d3b9f6483f842e7f6bf31b43d4bc4a0b198f956c7b66914`): row 96 = 203,004,795
(typed root `8ee3eefa1027cc02…`, score numerator 56,835,791 — which is why this packet is
provably the row-96 witness); row 97 = 203,004,719; row 108 = 203,004,778; row 400 =
203,004,684. All 111 of the spread is inside `reduction_and_inference` (182,849,120 for row 96);
`model_binding` (5,376,112), `typed_root` (14,748,143) and `public_commitment` (25,012) are
bit-identical across rows. The count also comes from the **unproven execute replay**
(`results/execute/stdout.log`, `total_instruction_count=203004795`), not from the proof — which
matters in a file whose sibling objects carry `"verified": true`.

Corrected record. Read the `relation` object as if it were:

```
  "relation_invariant": {
    "private_input_bytes": 458752,
    "public_values_bytes": 344
  },
  "this_witness": {
    "witness_row": "august_dev_712 row 96 (frozen development architecture position 0)",
    "sp1_instructions_this_witness": 203004795,
    "sp1_instructions_source": "unproven execute replay, not attested by the proof",
    "sp1_instructions_row_specific": true,
    "sp1_instructions_measured_range_four_witnesses": [203004684, 203004795],
    "typed_root": "8ee3eefa1027cc02d955b65f06840fe624ce07077f8d52f7e9e9f4eb309043b2",
    "score_numerator": 56835791,
    "score_denominator": 4
  },
```

If the packet is ever re-manifested rather than errata'd, this reshaping changes the shape of
`zeebeam-l1-1-coupling-durable-packet/v1`, so bump the schema string in the same change.
That the committed witness is row 96 is fixture-level lineage, not proven in-circuit.

## 2. Examined and CLEARED — do not "fix" these

Recorded so a later pass does not break a pinned file to correct a non-error.

- `packet_v1/NARRATIVE.md` line 16, "The execute replay measured exactly `203004795` SP1
  instructions." **Not an error.** It is the third sentence of a single paragraph whose previous
  sentence identifies the witness by typed root `8ee3eefa…` and score numerator `56835791`,
  and it is a past-tense report of one measured run, in the same register as the packet's other
  run figures (35,253,193 bytes, wall 3:04:10, peak RSS 44,293,344 KiB). This is the sanctioned
  form, not the prohibited one. Editing it would break `PACKET_SHA256SUMS` entry 1
  (`19ec2378…`) and the packet's 64/64 for no gain. What is genuinely missing from the packet is
  a record of row-specificity — which is this errata, not a rewrite.
- `RECEIPT_NARRATIVE.md` line 71 (`total_instruction_count=203004795` under the execute-replay
  stage) is correctly scoped to one run's replay and is likewise cleared.

## 3. Pre-existing errata for this lane, still standing

Not found by this pass; repeated here because a reader of the packet needs all of them in one
place (both from `publication/ULTRA_AUDIT_v1.md`):

- Purge item 5: `RECEIPT_NARRATIVE.md` line 40 (pinned at `e049f5bb…`) mislabels
  `0188b5c0…` as "the witness blob commitment". It is the sha256 of the 90,552-byte frozen
  model blob; the witness commitment is the typed root `8ee3eefa…`.
- Purge item 20: the fixture manifest field `primary_pair_sha256=7d894eed…` does not recompute
  from the embedded pair (actual `da6238d5…`) and must not be quoted. The four-arm
  `results/RESULT.json` labels the same value correctly as
  `row_96_archived_primary_commitment`; the field name is the defect, not the value.

---

## Numbers a reader may already have cited

| quantity | previously recorded | status now |
|---|---|---|
| `relation.sp1_instructions` = 203004795 | presented as the relation's count | unchanged as a measurement; it is **row 96's**, from the unproven execute replay |
| four-witness span | not recorded | **203,004,684–203,004,795** (rows 96/97/108/400), new figure |
| `private_input_bytes` 458752, `public_values_bytes` 344 | relation fields | unchanged, and genuinely relation-invariant |
| typed root `8ee3eefa…43b2`, score 56835791/4 | relation fields | unchanged, but per-witness, not per-relation |

Consolidated index: `[machine path redacted]`.
