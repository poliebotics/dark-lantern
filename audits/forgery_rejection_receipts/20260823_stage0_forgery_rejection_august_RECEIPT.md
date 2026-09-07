# Receipt: Stage-0 forgery rejection on the August take, 81-row sample, 2026-08-23

Proof 5, empirical half. Public F-A v1 forger (step 100,000, 42,305,140 params, SHA-256 2bf156d07b1ddf72ec53dab500cc0df2344596edd40890f904a60901217ad92e) renders C_fake = F(C_(r-2), E_(r-2), E_r) at native 4x2300x2660 for every 8th development row from 32 to 672 (81 rows). The published Phase G verifier (SHA-256 b9d93050bfeb1a5cdbf620c38210f3ab6c6fd7af1f61eb45cc17ac269341f055, weights-only load, bf16 path, t=150, K=1, one shared noise tensor per row) scores real and fake under the same emission.

| arm | mean eps-MSE |
|---|---:|
| real_correct (C_r, E_r) | 0.006849 |
| real_shuffled (C_r, E_far) | 0.009158 |
| fake_correct (C_fake, E_r) | 0.008028 |
| fake_shuffled (C_fake, E_far) | 0.008476 |
| fake_source (C_fake, E_(r-2)) | 0.008536 |
| fake_uncond (C_fake, zero E) | 0.005012 |

AUROC real_correct vs fake_correct = 0.9997 (paired real below fake on 81/81 rows); real_correct vs real_shuffled = 1.0000; fake_correct vs fake_shuffled = 0.8778; fake_correct vs fake_source = 0.9026. Fake pixel MAE to its source 0.0303, to the real target 0.0293 (real-to-source 0.0223): the forger changes the frame by more than the real motion does.

Reading: On this 81-row dependent development sample, the April forger, applied zero-shot to August, produced frames ranked as more coupled to target than wrong emissions (fake-correct versus fake-shuffled AUROC 0.8778). Real-correct and fake-correct scores were separable in this uncalibrated scorer's ranking (AUROC 0.9997). These are descriptive ranking diagnostics, not rejection rates or evidence of raw physical realism. One checkpoint; same take; the 288-row verification take was not opened; fake frames were not written to disk.

Files in this publication: result `20260823_stage0_forgery_rejection_august_81row.json` SHA-256 `917a85e1f34743a1a1747f4939b432018e0d156fe24f6a63f84ed1a646353daa`; runner `20260823_run_stage0_august.py` SHA-256 `548a03fe0ec5d91a9370cb5ed08e778f6d44a02cb609f2c00dd2f9174a7e7d09`. Historical execution bindings before publication redaction: result SHA-256 `0f4474d9a1ced445a3c8b43f25c0fcdf36478e854d5da575b18c90d788c579ee`; executed runner SHA-256 `13a8d27587ef388056bfe1118e9565cc47a7d6d3da82d5c7432f34c3de66a673`, also recorded as `script_sha256` in the result; torchvision shim and timm 1.0.28 staged under scratch/forger_stage0_20260823/pkgs on PYTHONPATH, locked environment unmodified. 157 s on the RTX 5090.
