---
version: 1.3
date: 2026-09-10
status: the claim boundary of this package: emission-recording correspondence within the recordings named, and nothing wider; the four paragraphs govern every sentence in this directory
author: Cathal Ryan Hynes (author of record); drafted with BOSUN, the project's automated research assistant
---

# Claim boundary

The paragraphs below bound what this package claims. Every other document in this directory, the three desk reports
included, is read under them, and a sentence elsewhere that seems to say more than they do is to be read as saying no more.

**What is measured.** Each result asks whether a camera frame of a Truth Beam session carries a measurable trace of the
pattern that was projected when it was taken: whether a statistic or a model, given the frame, prefers the true pattern to
a wrong pattern drawn from the same session. The answer is reported as two numbers that travel together, the paired
fraction (the share of frames on which the true pairing scored better) and the pooled AUROC (how well one threshold
separates all matched from all mismatched scores), with bootstrap intervals over frames that condition on the recorded
scores, the fixed negatives, the fixed geometry and the fixed models, ignore serial dependence, and describe these
recordings only. We call this **emission-recording correspondence**. It is a property of these recordings as measured by
these methods.

**What is not claimed.** Nothing here establishes that any recording is real, live, or was physically captured; that a
scene was lit by the pattern paired with it; that a forgery, replay or substitution would be detected; that any method
resists an adversary who chooses the emission or the capture; or that any result transfers to a scene, a rig or a session
other than the ones tested. The negatives are random or prescribed same-session alternatives (the ARM-I controls add
exhaustive, matched-period and colour-matched alternatives); hard temporal negatives are largely untested and adversarial
negatives entirely so. Discriminators and generators that rank a matched pair above a within-session swap are verifiers of
nothing beyond that swap. No image-quality claim is made: the pix2pixHD generators' fidelity stays below a constant
baseline. The "unseen configuration" tested by ARM-I is a different rig configuration of the same instrument family; the
2023 and 2024 sessions share a room and a bookshelf, and no test with a third, held-out scene exists.

**Nothing here is proved in zero knowledge.** The ZeeBeam release and the zkdiff August package
(`dark-lantern/proofs/zkdiff_august_20260907/`) prove the execution of the specified ARM-C evaluator on committed bytes of
the 2026 August session, and their claim boundary is theirs. ARM-I is an image-conditioned sibling of ARM-C with a
different conditioning input; no proof binds it, and no proof binds the pix2pixHD models or the grid statistic. The
in-distribution AUROC 1.000 of ARM-I on the 2026 evaluation blocks is a development-validation figure on blocks the
programme has scored repeatedly, not a test-set result.

**Holdout discipline and calibration, disclosed exactly.** Every held-out session named in `RESULTS.md` was excluded from
weight training. Three qualifications stand. First, ARM-I's training monitored small samples of the held-out sessions
(no gradient, no checkpoint selection; the runs stop at a fixed step), and the desk reports name every monitored subset.
Second, the pix2pixHD results are exploratory: the held-out scores were read during the night and steered the recipe
changes and the choice of reported variants. Third, the alignments that recover the 2023 transfer are retrospective
calibrations fitted from the target sessions' own emission/recording pairs by the data-look desk (25 pairs for the
trailer; the grid statistic's own crop uses recordings alone, with the orientation chosen on four matched frames per
session); the reports quantify what removing the fitted pairs changes, and the benefit of a target-fitted geometry that
transforms every remaining frame is not bounded by those checks. The raw-2023 null of ARM-I is a limit of the zero-shot
transfer result and is published as such.

## Where this boundary comes from

It is the ZeeBeam manuscript's boundary (Sections 3.4 and 8.3: a learned component's semantic label may be disregarded
while the measured behaviour stands; any physical reading needs assumptions no measurement supplies) applied to three
measurements that carry no proof at all, and the second-model results audits' wording for each result
(`AUDIT_TRAIL.md`): "correspondence against the chosen random same-session negatives" for the statistic, "emission-recording
correspondence within these recordings ... exploratory" for the pix2pixHD work, and "emission-recording correspondence
results within this recorded corpus ... the published ZK proofs bind the specified ARM-C execution only" for ARM-I. Each result is
disclosed as fully as the record allows, which is why the limits inside each result are stated here (`RESULTS.md`).

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-09 | BOSUN | First version, drafted from the three audited reports before the package audit. |
| 1.1 | 2026-09-09 | BOSUN | Package audit round 1 applied: the closing sentence names no unpublished measurement. |
| 1.2 | 2026-09-09 | BOSUN | authorship line, 9 September 2026. |
| 1.3 | 2026-09-10 | BOSUN | Wording: the closing paragraph revised; no boundary changed. |
