# audits/: the audit texts, published

`astra/`: the review briefs supplied to GPT-6 Astra (`codex exec`, ultra reasoning effort) and the verdicts it returned, rounds 1 to 6
(five before proving, one on the finished package) and rounds 8 to 10 (the confirmation re-reads of the augmented package and its
re-frozen revisions). Round 7, the
privacy and embarrassment sweep of the payloads, is not published as text because it quotes the material it asked to remove; its
verdict line and the application of its dispositions are recorded in `AUDIT_TRAIL.md`. `agents/`: the outside-agent readability
audits of 8 September 2026, round 1 (`*_r1.md`, on the round-6 package), round 2 (`*_r2.md`, on the augmented package) and round 3
(`*_r3.md`, on the round-9 revision), each
agent reading a copy of the package with no other context. `AUDIT_TRAIL.md` at the package root carries the verdict lines, the
dispositions and what changed after each round; `FAQ.md` answers the agents' questions.

Every copy carries the banner at its head: personal identifiers, private instructions and development infrastructure are redacted
(exact substitutions listed in the release desk's record, the publication redaction rule of `REDACTION.md`, absolute paths trimmed
to package paths or marked `(on-box)` or `(repository root)`, salutations dropped, markdown links rewritten as file-and-line text);
scientific findings, negative findings and the auditors' criticism are preserved as written, and line numbers are as at audit time.

| file | source record | sha256 of the published copy |
|---|---|---|
| `audits/astra/r1_brief.md` | `ASTRA_BRIEF_zkdiff_r1.md` | `aecc9f569dc76ffec91980fabc2cb3313d9fec068cd784147163aa45422b9e86` |
| `audits/astra/r1_verdict.md` | `ASTRA_VERDICT_zkdiff_r1.md` | `faabb2da58b4818d3f76b9231ad05bfed0294810a9e0baa2ca5acc25f82e3c76` |
| `audits/astra/r2_brief.md` | `ASTRA_BRIEF_zkdiff_r2.md` | `c94a5a00a5304dde962d27f463250748e9e715208131afadfbd747b14c04f5ae` |
| `audits/astra/r2_verdict.md` | `ASTRA_VERDICT_zkdiff_r2.md` | `9bd3e57557566edb70b2d496139429271583311b222155a520c5ab5bea6a767c` |
| `audits/astra/r3_brief.md` | `ASTRA_BRIEF_g1_r3.md` | `6f93c09ed3b9fabffde1ebe8e03170455e0334a81015a8737e1e379b41ba8186` |
| `audits/astra/r3_verdict.md` | `ASTRA_VERDICT_g1_r3.md` | `c5d589ed63d63328bfa4bb47536fa2a82b2e89a0a15915fbfe8192d6a5622511` |
| `audits/astra/r4_brief.md` | `ASTRA_BRIEF_g2a_r4.md` | `7c198b907b7d7299bbc4dfbf1baee628d42ccea0d78fea14fbfb0e34f83d1f7e` |
| `audits/astra/r4_verdict.md` | `ASTRA_VERDICT_g2a_r4.md` | `5202eeb8ddabbab605ef4fedab6ab463dd59b6daf92a75893a16eddaca2672f7` |
| `audits/astra/r5_brief.md` | `ASTRA_BRIEF_fullguest_r5.md` | `57c13cd9cc132bb6b6e648eff3497f1176b761621ccd247963bd0443a5825a08` |
| `audits/astra/r5_verdict.md` | `ASTRA_VERDICT_fullguest_r5.md` | `5c1f98629667ceda44ea43493e077c6f006fa78b434c7f002b2cab18df3e3166` |
| `audits/astra/r6_brief.md` | `ASTRA_BRIEF_package_r6.md` | `c912c6e74ba10547b144da9c27c28cd594966374f360c5bff9f6afde99a4934b` |
| `audits/astra/r6_verdict.md` | `ASTRA_VERDICT_package_r6.md` | `a484f0f79bc44242c86019deeda9544073f009f8dd4ad0d9496b76d8ac1a112b` |
| `audits/astra/r8_brief.md` | `ASTRA_BRIEF_confirm_r8.md` | `155349af53a84124a7696597b8db9418d9e279cc9afadca9ce417f1b757ba074` |
| `audits/astra/r8_verdict.md` | `ASTRA_VERDICT_confirm_r8.md` | `586506f1f04a9117407374fbdcfe1cf06af21c8d595ce0bb071a62d67271a17a` |
| `audits/astra/r9_brief.md` | `ASTRA_BRIEF_confirm_r9.md` | `850c239102d794aa5e3755544ffaeff55bdc5adc26eb8ea15ea2623091857ccb` |
| `audits/astra/r9_verdict.md` | `ASTRA_VERDICT_confirm_r9.md` | `deff4fe904c3aeb360d13d8c58aed1c972198c3ce97ea0549b4989777aa0eefd` |
| `audits/astra/r10_brief.md` | `ASTRA_BRIEF_confirm_r10.md` | `282c26b17fcc9b797b7f8bfd280c996a018935e86b5dc7917abd5fba55ece2bd` |
| `audits/astra/r10_verdict.md` | `ASTRA_VERDICT_confirm_r10.md` | `58797f0a63499e8d0e1260a61eec75ed0720950badd3b5156024499139edf42b` |
| `audits/agents/claude_r1.md` | `claude_r1.md` | `38e880f0a640e1eb62523e12ebbc19e50bf0c1765edc6498a9ded42d2ccf5cf0` |
| `audits/agents/codex_r1.md` | `codex_r1.md` | `4b6a9e4c53e8e7c04d7c6d090cace05dc18ce8706d3d813974191a6380a92775` |
| `audits/agents/grok_r1.md` | `grok_r1.md` | `c3a59ef8fa38b3ddda4983873a0a8805953e7864b3dc95d0b948ddd471189d51` |
| `audits/agents/claude_r2.md` | `claude_r2.md` | `647718ac66e7f557c382f24f0173aa6c89fe462a46bcfd77f494e5210d6f4818` |
| `audits/agents/codex_r2.md` | `codex_r2.md` | `1d90c8c75a2b4bf64d575ab9bc73c128e45083f03e64fd0d78345442cb0097bc` |
| `audits/agents/grok_r2.md` | `grok_r2.md` | `68fbc94c88c137f5e1c1d7dbd0b1bf6d316f7367a2e5393f3caa872fe43d0b7d` |
| `audits/agents/codex_r3.md` | `codex_r3.md` | `60b7df6d26ec88cb5fa499dd798f301afe10d6122ce65bef9f58398635ce9201` |
| `audits/agents/grok_r3.md` | `grok_r3.md` | `dab3cb1cdc96eb98c76494a14ff58a21858c107d8e0c22f5d22c91456393eb6f` |
| `audits/agents/claude_r3.md` | `claude_r3.md` | `ae274f5069babb0e5a1f3f4a8a236a0a6b60830e83e00d0f27c17adecac5cd71` |
