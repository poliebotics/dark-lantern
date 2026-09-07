# Verdicts of the four-round 8-seed conditioning audit

Second-model audits by Sol (OpenAI GPT-5.6 through `codex exec`, ultra effort) of the claim drafts in this
directory. The raw transcripts are not published: they repeat the operator's private desk instructions. Verdict
lines, as returned:

| round | brief | claim text audited | verdict |
|---|---|---|---|
| 1 | `AUDIT_BRIEF.md` | `CLAIM_DRAFT_v1_asaudited.md` with `EVIDENCE_v1_asaudited.md` | `VERDICT: BLOCK (1, 2, 3, 4)` |
| 2 | `AUDIT_BRIEF_v2.md` | revised claim | `VERDICT: BLOCK (4)` |
| 3 | `AUDIT_BRIEF_v3.md` | revised claim | `VERDICT: BLOCK (4)` |
| 4 | `AUDIT_BRIEF_v4.md` | `CLAIM_DRAFT.md` with `EVIDENCE.md`, `INDEPENDENT_RECOMPUTE.json`, `ATTESTATION.json` | `VERDICT: PASS` |

The PASS covers the v4 claim text only, not every broader interpretation in the note
`notes/zeebeam_nocrop_diffusion_8seed_20260830.md`. Primary-evidence limitations remain as stated in the verdicts.
These are model reviews, not independent validation.
