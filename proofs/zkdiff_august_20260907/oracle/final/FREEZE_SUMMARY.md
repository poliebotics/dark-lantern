# FREEZE SUMMARY: g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pt

- checkpoint sha256 `c6955192067c8df1f46960f4803b32eac1c037b84a0f40de3b265b739d85fab8` (verified against `g0e_armc_b16_96x112_cd0_aug_s20260908_24k.pubproto_eval.json`), step 24000; evaluator raw scores from `oracle/ckpt/final/g0e_armc_b16_96x112_cd0_aug_s20260908_24k`
- generated 2026-09-07 20:49 UTC on torch '2.11.0+cu130' numpy '2.3.5'

## Positive control against the frozen evaluator (222 scores)

| variant | rel median | rel max | signed mean (std) |
|---|---|---|---|
| fp32 | 3.27e-03 | 1.10e-02 | -3.85e-03 (2.02e-03) |
| bf16em | 1.13e-03 | 6.20e-03 | -5.39e-04 (1.50e-03) |
| bf16em_v2 | 1.14e-03 | 4.74e-03 | -5.86e-04 (1.50e-03) |

Closer emulation variant: **bf16em**. Evaluator on the 37 rows: paired 37/37, margin min 0.019623.

## Integer vs evaluator (185 pairs)

| scheme | sign agree | paired | D_q/eta min / median / max | pass 3eta | score err rel median / max (signed) | eta median | weakest pair | clips | conv acc bound | requant bound |
|---|---|---|---|---|---|---|---|---|---|---|
| int16 | 185/185 | 37/37 | 79.79 / 128.83 / 288.16 | 185/185 | 3.13e-03 / 1.02e-02 (-3.57e-03) | 1.73e-04 | d2 2866 +2 (D_q 0.023552, eta 2.95e-04) | 0 | 353,174,814,720 | 3,812,976,885,203,206,144 |
| int8 | 185/185 | 37/37 | 19.23 / 32.66 / 68.95 | 185/185 | 1.10e-02 / 4.70e-02 (+1.39e-02) | 6.97e-04 | d2 1608 -15 (D_q 0.020142, eta 1.05e-03) | 0 | 1,368,850,432 | 22,661,745,809,484,953 |

## August proof rows 600-711 (rule offset, integer int16 and fp32; no evaluator)

- `int16`: rule pairs available 112/112 (missing wrong-hint rows: []); D_q min 0.007328, p5 0.008141, median 0.009161, max 0.010988; integer correct<wrong 112/112, fp32 112/112; negative integer rows none; all-offset pairs int c<w 507/507; clips 0
- `int8`: rule pairs available 112/112 (missing wrong-hint rows: []); D_q min 0.007321, p5 0.008166, median 0.009174, max 0.010998; integer correct<wrong 112/112, fp32 112/112; negative integer rows none; all-offset pairs int c<w 507/507; clips 0

## Calibration disclosure

The fixed-point scales were calibrated on 15 rows x 2 conditionings (own E and E of row+15): protocol rows d2 1328, d2 1528, d2 2866, d2 3066, d2 4404, d2 4604, v10 1260, v10 2495 and August targets [600, 616, 632, 648, 664, 680, 696], i.e. 7 raw August targets and 14 August conditioning identities [600, 615, 616, 631, 632, 647, 648, 663, 664, 679, 680, 695, 696, 711]. August rows 600-711 were held out from weight training (august_train_rows 600) but were NOT untouched by calibration; they must not be described as an untouched test set. The proof set remains the complete 112 rows.


## Artifact files

- `AGREEMENT.md` sha256 `28d8764dea2e45f5...`
- `FREEZE_SUMMARY.md` sha256 `5f0c4232704d49f2...`
- `README_FINAL.md` sha256 `ec4e44b8d30b93ae...`
- `agreement.json` sha256 `db5e42e68f412dad...`
- `agreement_int16.json` sha256 `7d3bfe5d6eab7a25...`
- `agreement_int16_august.json` sha256 `a59d59a08a4603d1...`
- `agreement_int8.json` sha256 `39dc2c2ccda177d8...`
- `agreement_int8_august.json` sha256 `3b37812ae8b8ce6d...`
- `constants_int16.json` sha256 `af077d12e5e6167f...`
- `constants_int8.json` sha256 `4273010715749fd0...`
- `float_repro.json` sha256 `aebfe95bf643c9d2...`
- `positive_control.json` sha256 `6d7b6fd9bca917a6...`
- `run_final.sh` sha256 `06190cbd3b77e450...`
- `vectors/`: 16 files
- `august_inputs/`: 114 files as frozen; in this package `manifest.json` and `coord_int.npy`, the 112 `row_NNNNNN.npz` inputs being on the data layer (`LARGE_FILES.md`)
