# Receipt: Phase G zero-shot, 109-row thinned diagnostic, 2026-08-23

Label: 109-row thinned diagnostic. Not the exhaustive pass (that is v2, running).
Execution record only; v1 loaded the checkpoint with weights_only=False (pickle path) and ran fp32 weights under bf16 autocast, so it is an approximate, not exact, numeric replay of the published evaluator.

| item | value |
|---|---|
| result file | publication copy `20260823_phase_g_zeroshot_109row_thinned.json`, SHA-256 `f86c3a68a0b9f6593a4ee8ec5166436c24b53d2d78e22d62fb844297faf30176`; historical pre-redaction result SHA-256 `e46410d610d204f4f38411eb3a87be42361a4cd0fdad6fbf0dae7995d37b7eed` |
| script | publication copy `20260823_run_zeroshot_v1.py`, SHA-256 `6a1367ff41ac2ac2828b50c9158e644a244cadb8723480d68931e4a20fd7db4f`; executed pre-redaction script SHA-256 `c8847d92aa8aab706229b617ef169f1e7cf08b609d4138cfa98824c8af174b58`, retained as `script_sha256` in the result |
| checkpoint | `model_final.pt` SHA-256 `b9d93050bfeb1a5cdbf620c38210f3ab6c6fd7af1f61eb45cc17ac269341f055` (matches truthbeam_public/SHA256SUMS:13), 39,769,828 params |
| data | `[machine path redacted]` only: the 712-row development take, seal evidence root BLAKE3 `8db2dfc51396d763f7b89629745b3d6609c5d3290ada9f59e2eda9e2cadefc17` (FINAL_RECORDING_HANDOFF.md); the v1 runner references only this path and does not enumerate, decode, hash, score or use verification-take content. No global "not accessed" claim: see the Codex custody-incident report of 2026-08-23 (audit-agent recursive search under the evidence root, disclosed at coord 17:01 UTC) |
| rows | 109: range(30, 682, 6); blocks of 100 rows -> [12,17,16,17,17,16,14] |
| protocol | Phase G locked contract (pack R,G1,G2,B; crop y[0:1704] x[155:2433]; /255; area resize 768x1024; E full frame area resize; 11-ch hint); t in (150,300,500); K=2; seed 20260823+row; same noise across conditions; wrong offsets (-2,+2,-15,+15,+30); uncond arm |
| device | RTX 5090 Laptop, torch 2.11.0+cu130, bf16 autocast; 1,234 s |

Result (mean eps-MSE): correct 0.003709; wrong -2/+2/-15/+15/+30 = 0.005078/0.005101/0.005093/0.005093/0.005112; uncond 0.002821.
delta_wrong = +0.001386, block-bootstrap 95% CI [+0.001332, +0.001448]. delta_uncond = -0.000888 [-0.000936, -0.000839].
AUROC correct-vs-wrong = 1.0000 at every offset and pooled; paired fraction correct < wrong = 1.000 (109/109).
Per timestep: t=150 delta 0.002290 AUROC 1.0; t=300 0.001251, 1.0; t=500 0.000618, 1.0.
AUROC correct-vs-uncond = 0.0000: the unconditioned residual is lower than the correctly conditioned one on every row.

Reading: the April verifier, never fitted to this August take, separates matched from crossed August pairs perfectly; the coupling transfers to this take. The unconditioned arm beating correct is the opposite of April (where uncond > correct); a geometry or rig mismatch between the April sessions and this take is a candidate explanation, with August rig identity unconfirmed [confirm]. Under that reading the hint costs accuracy on average, but the right hint costs least. Delta is about a third of April's (+0.0040). Claim boundary: same person, same take, 109 dependent rows, no cross-session independence, descriptive.
