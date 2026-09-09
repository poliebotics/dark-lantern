# audits/: the second-model results audits, published

`astra/`: the review briefs supplied to GPT-6 Astra (`codex exec`, ultra reasoning effort) and the verdicts it returned on
9 September 2026, one round on the train-free statistic, one on the pix2pixHD (Old Light) work and two on ARM-I (the second on
the follow-up runs and the round-1 fixes). Each audit read the desk's report, code and results files on the development machine,
read-only, and recomputed the reported numbers from the saved per-frame or per-row scores; `AUDIT_TRAIL.md` at the package root
carries the verdict lines, what each round reproduced and what changed after it. The raw transcripts of the runs and the scripts
that invoked the model are not published (they quote the operator's private instructions).

Every copy carries the banner at its head: personal identifiers, private instructions and development infrastructure are redacted
(the release desk's standing publication rule at the head of each brief is replaced by a bracketed note; the sentences of the
pix2pixHD brief and verdict on the January 2025 comparison are replaced by bracketed notes; the publication redaction
rule of `REDACTION.md` maps absolute paths to package locators or placeholders; salutations and tool-runner lines dropped; markdown
links rewritten as file-and-line text); scientific findings, negative findings and the auditors' criticism are preserved as
written, and line numbers are as at audit time. Both ARM-I verdicts state that one bookshelf appears in all three eras; the owner
correction of 9 September (`AUDIT_TRAIL.md`) supersedes that sentence.

| file | source record | subject | sha256 of the published copy |
|---|---|---|---|
| `audits/astra/armi_r1_brief.md` | `ASTRA_BRIEF_results_r1.md` | ARM-I results audit, round 1, the brief | `4a1dda361f02309b64a8f4f8a2631668399c1ad813e140c58fa23d8a6a4b2800` |
| `audits/astra/armi_r1_verdict.md` | `ASTRA_VERDICT_results_r1.md` | ARM-I results audit, round 1, the verdict | `9158e3e8b17e5faf8a51aeafab5ef5f31fb98fc205d961a14eda12dfd6c65460` |
| `audits/astra/armi_r2_brief.md` | `ASTRA_BRIEF_results_r2.md` | ARM-I results audit, round 2 (follow-up and round-1 fixes), the brief | `248e5fccaf1e7941707f6949e93933b8e8ce8a46a356f009abae4fa5bee7f427` |
| `audits/astra/armi_r2_verdict.md` | `ASTRA_VERDICT_results_r2.md` | ARM-I results audit, round 2, the verdict | `4d01829710e7311aa75afb23d076413866a22afd12cc0b2cf6e8b9c695558a7d` |
| `audits/astra/coupling_r1_brief.md` | `ASTRA_BRIEF_results_r1.md` | train-free statistic results audit, the brief | `0bfa47f1d4cf0dbc101370cd94d157f59dccc95497545cc63782cd19ff52282a` |
| `audits/astra/coupling_r1_verdict.md` | `ASTRA_VERDICT_results_r1.md` | train-free statistic results audit, the verdict | `a73ae216f75c358b741c564f01d94464ec26b336c3b149f0a1dcf3c93aac57ec` |
| `audits/astra/oldlight_r1_brief.md` | `ASTRA_BRIEF_results_r1.md` | pix2pixHD (Old Light) results audit, the brief | `da855a2b63f49d554c5e9c10e549d6a5fff528c8d82105cf5558bf8aee932593` |
| `audits/astra/oldlight_r1_verdict.md` | `ASTRA_VERDICT_results_r1.md` | pix2pixHD (Old Light) results audit, the verdict | `cb0aa9d37836553abd0b7d5313672c41227c35e236b5630773de9be61955537d` |
