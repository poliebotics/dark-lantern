#!/usr/bin/env python3
"""Format-only closure of the v2 exhaustive pass: NaN -> null strict JSON, recompute every
summary and denominator from the strict artifact, sensitivity interval on equal blocks,
provenance bindings, receipt. No inference. Fails closed on any mismatch."""
import hashlib, json, math, os, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
RAW = HERE / "zeroshot_v2_exhaustive.json"
STRICT = HERE / "zeroshot_v2_exhaustive.strict.json"
HANDOFF = HERE.parent / "coord" / "handoff"
VSRC = Path("<machine path redacted>")
TAKE = Path("[machine path redacted]")
EXPECTED_SCRIPT = "af3e1b67a5393790a1dff8c8ba12b37bb5c7ee31f413c7f9e73d5e4199ee1454"
EXPECTED_MODEL_SRC = "f1241c1e4b7d042397d314207a45becd24066d9ed672ec759fbc14fd9e0c3beb"
EXPECTED_INIT = "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b"
EXPECTED_CKPT = "b9d93050bfeb1a5cdbf620c38210f3ab6c6fd7af1f61eb45cc17ac269341f055"
DEV_ROOT_BLAKE3 = "8db2dfc51396d763f7b89629745b3d6609c5d3290ada9f59e2eda9e2cadefc17"
INCIDENT_JSON = Path("<repo>/scratch/zeebeam_sciencemaxxing_20260823/VERIFICATION_SEARCH_ACCESS_INCIDENT_20260823.json")
INCIDENT_JSON_SHA = "aeac750b0fb07eed3cd8b7932a6d47cfa12901cb99ae1a420d295d06e560c568"
INCIDENT_MD_SHA = "92639e7f506d195012d7a751c6dba30b6be47b7b3d9bf35eb49fa8703a82a4db"
DEV_MANIFEST = Path("<repo>/scratch/zeebeam_sciencemaxxing_20260823/development_export_manifest.content-verified.json")
DEV_MANIFEST_SHA = "6f21f8b6437987102d528806d484cfc10ec06eecb415d4d118c371d84a0fbf4e"
DEV_MANIFEST_ROOT = "c49ec1b0deef5d69258041a469b8006d335eced0a514884c5ecab1b309145891"
OFFSETS = (-2, 2, -15, 15, 30)
EXPECTED_DENOM = {"correct": 712, "wrong_-2": 710, "wrong_+2": 710, "wrong_-15": 697, "wrong_+15": 697, "wrong_+30": 682, "uncond": 712}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def fail(msg):
    print("FAIL:", msg); sys.exit(1)


def nan_to_null(o):
    if isinstance(o, float):
        return None if not math.isfinite(o) else o
    if isinstance(o, list):
        return [nan_to_null(x) for x in o]
    if isinstance(o, dict):
        return {k: nan_to_null(v) for k, v in o.items()}
    return o


def auroc_pooled(c, w):
    c = -np.asarray(c, float).ravel(); w = -np.asarray(w, float).ravel()
    c = c[np.isfinite(c)]; w = w[np.isfinite(w)]
    n1, n2 = c.size, w.size
    s = np.concatenate([c, w]); order = np.argsort(s, kind="stable"); ss = s[order]
    rs = np.empty(len(s)); i = 0
    while i < len(ss):
        j = i
        while j + 1 < len(ss) and ss[j + 1] == ss[i]:
            j += 1
        rs[i:j + 1] = (i + j) / 2.0 + 1.0; i = j + 1
    ranks = np.empty_like(rs); ranks[order] = rs
    return float((ranks[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n2))


def block_ci(values, block_lengths, n_boot=1000, alpha=0.05, seed=0):
    rng = np.random.RandomState(seed)
    b = [0]
    for L in block_lengths:
        b.append(b[-1] + L)
    blocks = [values[b[i]:b[i + 1]] for i in range(len(block_lengths))]
    boot = np.zeros(n_boot)
    for i in range(n_boot):
        idx = rng.randint(0, len(blocks), size=len(blocks))
        boot[i] = np.nanmean(np.concatenate([blocks[j] for j in idx]))
    return float(np.nanmean(values)), float(np.nanquantile(boot, alpha / 2)), float(np.nanquantile(boot, 1 - alpha / 2))


def main():
    if sys.flags.optimize != 0:
        fail("optimised interpreter")
    if not RAW.is_file():
        fail("raw result missing")
    raw_bytes = RAW.read_bytes()
    raw = json.loads(raw_bytes)  # permissive: accepts bare NaN
    # validate the non-strict raw artifact before any conversion
    RP = raw["per_row"]
    if not isinstance(RP, list) or len(RP) != 712:
        fail("raw per_row length")
    for p in RP:
        r = p.get("row")
        if not isinstance(r, int) or not (0 <= r < 712):
            fail("raw row id")
        for c in ("correct", "uncond"):
            v = p[c][0][0]
            if not isinstance(v, float) or not math.isfinite(v):
                fail(f"raw non-finite {c} row {r}")
        for o in OFFSETS:
            v = p[f"wrong_{o:+d}"][0][0]
            inside = 0 <= r + o < 712
            if inside:
                if not isinstance(v, float) or not math.isfinite(v):
                    fail(f"raw in-range wrong cell not finite row {r} offset {o}")
            else:
                if not (isinstance(v, float) and math.isnan(v)):
                    fail(f"raw boundary cell is not a float NaN row {r} offset {o}: {v!r}")
    strict = nan_to_null(raw)
    def _reject_const(x):
        raise ValueError(f"JSON constant {x} present after conversion")
    strict_text = json.dumps(strict, indent=1, allow_nan=False)
    strict = json.loads(strict_text, parse_constant=_reject_const)  # strict re-parse, in memory
    S = strict["summary"]; P = strict["per_row"]
    # --- identity and scope ---
    if S["n_rows"] != 712 or len(P) != 712 or [p["row"] for p in P] != list(range(712)):
        fail("row set is not exactly 0..711")
    if S["timesteps"] != [150] or S["K"] != 1 or S["offsets"] != [-2, 2, -15, 15, 30]:
        fail("protocol drift")
    if S.get("script_sha256") != EXPECTED_SCRIPT:
        fail("script hash drift")
    if S["model"]["ckpt_sha256"] != EXPECTED_CKPT:
        fail("checkpoint hash drift")
    if "live_120s_verification_001" in json.dumps(strict):
        fail("verification take referenced by the runner output")
    if sha(VSRC / "diffusion_diagnostic_model.py") != EXPECTED_MODEL_SRC or sha(VSRC / "__init__.py") != EXPECTED_INIT:
        fail("model source drift")
    if sha(INCIDENT_JSON) != INCIDENT_JSON_SHA or sha(INCIDENT_JSON.with_suffix(".md")) != INCIDENT_MD_SHA:
        fail("incident record hash drift")
    n_raw = len(list((TAKE / "Recordings").glob("frame_*.raw")))
    if n_raw != 712:
        fail("development inventory count")
    # --- per-row structure ---
    conds_exp = ["correct"] + [f"wrong_{o:+d}" for o in OFFSETS] + ["uncond"]
    seen = set()
    for p in P:
        if set(p.keys()) != {"row", "block", *conds_exp}:
            fail(f"row keys {sorted(p.keys())}")
        r = p["row"]
        if r in seen or not (0 <= r < 712) or p["block"] != r // 100:
            fail(f"row identity {r}")
        seen.add(r)
        for c in conds_exp:
            v = p[c]
            if not (isinstance(v, list) and len(v) == 1 and isinstance(v[0], list) and len(v[0]) == 1):
                fail(f"shape row {r} {c}")
            cell = v[0][0]
            if c in ("correct", "uncond"):
                if not isinstance(cell, float) or not math.isfinite(cell):
                    fail(f"non-finite {c} row {r}")
            else:
                o = int(c.split("_")[1]); inside = 0 <= r + o < 712
                if inside and not (isinstance(cell, float) and math.isfinite(cell)):
                    fail(f"missing in-range wrong cell row {r} {c}")
                if not inside and cell is not None:
                    fail(f"imputed boundary cell row {r} {c}")
    if len(seen) != 712:
        fail("row count")
    if S["stride"] != 1 or S["rows_first_last"] != [0, 711] or S["blocks"] != [100] * 7 + [12]:
        fail("execution contract drift")
    if sha(DEV_MANIFEST) != DEV_MANIFEST_SHA:
        fail("development manifest hash drift")
    dm = json.loads(DEV_MANIFEST.read_text())
    if dm.get("status") != "CONTENT_VERIFIED" or dm.get("inventory_sha256_without_self") != DEV_MANIFEST_ROOT \
            or [e["ordinal"] for e in dm["entries"]] != list(range(712)):
        fail("development manifest content")
    # --- recompute from strict artifact ---
    conds = ["correct", "wrong_-2", "wrong_+2", "wrong_-15", "wrong_+15", "wrong_+30", "uncond"]
    def arr(c):
        return np.array([np.nan if p[c][0][0] is None else p[c][0][0] for p in P], float)
    A = {c: arr(c) for c in conds}
    denom = {c: int(np.isfinite(A[c]).sum()) for c in conds}
    if denom != EXPECTED_DENOM or denom != S["arm_denominators"]:
        fail(f"denominators {denom} vs summary {S['arm_denominators']}")
    wrongs = np.stack([A[f"wrong_{o:+d}"] for o in (-2, 2, -15, 15, 30)], 1)
    wavg = np.nanmean(wrongs, 1)
    rec = {"conditions": {c: float(np.nanmean(A[c])) for c in conds},
           "auroc": {"correct_vs_wrong_avg": auroc_pooled(A["correct"], wavg),
                     **{f"correct_vs_wrong_{o:+d}": auroc_pooled(A["correct"], A[f"wrong_{o:+d}"]) for o in (-2, 2, -15, 15, 30)},
                     "correct_vs_uncond": auroc_pooled(A["correct"], A["uncond"])},
           "paired_frac_correct_lt_wrong_avg": float(np.nanmean(A["correct"] < wavg))}
    for c in conds:
        if abs(rec["conditions"][c] - S["conditions"][c]) > 1e-12:
            fail(f"condition mean mismatch {c}")
    for k, v in rec["auroc"].items():
        if abs(v - S["auroc"][k]) > 1e-12:
            fail(f"auroc mismatch {k}")
    blocks_primary = [100] * 7 + [12]
    m, lo, hi = block_ci(wavg - A["correct"], blocks_primary)
    if any(abs(x - y) > 1e-12 for x, y in zip((m, lo, hi), (S["delta_wrong_mean"]["mean"], *S["delta_wrong_mean"]["ci95"]))):
        fail("primary wrong interval mismatch")
    mu, lou, hiu = block_ci(A["uncond"] - A["correct"], blocks_primary)
    if any(abs(x - y) > 1e-12 for x, y in zip((mu, lou, hiu), (S["delta_uncond_mean"]["mean"], *S["delta_uncond_mean"]["ci95"]))):
        fail("primary uncond interval mismatch")
    if abs(rec["paired_frac_correct_lt_wrong_avg"] - S["paired_frac_correct_lt_wrong_avg"]) > 1e-12:
        fail("paired fraction mismatch")
    t150 = S["per_timestep"]["150"]
    rec_t150 = {"correct": float(np.nanmean(A["correct"])), "wrong": float(np.nanmean(wavg)),
                "delta": float(np.nanmean(wavg - A["correct"])), "auroc": auroc_pooled(A["correct"], wavg)}
    if set(S["per_timestep"].keys()) != {"150"} or set(t150.keys()) != {"correct", "wrong", "delta", "auroc"} \
            or any(abs(rec_t150[k] - t150[k]) > 1e-12 for k in rec_t150):
        fail("t=150 record mismatch")
    # sensitivity: 8 equal contiguous blocks of 89
    ms, los, his = block_ci(wavg - A["correct"], [89] * 8)
    msu, losu, hisu = block_ci(A["uncond"] - A["correct"], [89] * 8)
    runner_bytes = (HERE / "run_zeroshot_v2.py").read_bytes()
    if hashlib.sha256(runner_bytes).hexdigest() != EXPECTED_SCRIPT:
        fail("runner on disk does not match the bound hash")
    finaliser_bytes = Path(__file__).read_bytes()
    if S["model"].get("checkpoint_load_mode") != "torch_weights_only_true_fail_closed" or S["model"].get("parameter_dtype") != "torch.bfloat16":
        fail("load mode or dtype fields")
    if S.get("take") != str(TAKE):
        fail("take string")
    if "seed" in S and S["seed"] != 20260823:
        fail("seed")
    EXPECTED_EC = {"stride": 1, "inset": 0, "K": 1, "timesteps": [150], "offsets": [-2, 2, -15, 15, 30], "block": 100, "seed": 20260823}
    if S.get("execution_contract") != EXPECTED_EC:
        fail(f"execution contract {S.get('execution_contract')} != {EXPECTED_EC}")
    EXPECTED_ARGV = ["run_zeroshot_v2.py", "--out", "zeroshot_v2_exhaustive.json"]
    if S.get("command_argv") != EXPECTED_ARGV:
        fail(f"argv {S.get('command_argv')} != {EXPECTED_ARGV}")
    mp = S["model"]
    if (mp.get("n_params") != 39769828 or list(mp.get("mults", [])) != [1, 2, 4, 4] or mp.get("base_ch") != 96
            or [bool(x) for x in mp.get("attn_at", [])] != [False, False, False, True]
            or mp.get("model_source_sha256") != EXPECTED_MODEL_SRC
            or mp.get("published_ipfs_cid_v0") != "QmPthdv3CvW2dyRRYJ7Aqgvwc5qN5D2ujLRVr8e1wWMoAY"):
        fail("model provenance fields")
    if (HERE / "model_final.pt").stat().st_size != 477531127 or sha(HERE / "model_final.pt") != EXPECTED_CKPT:
        fail("checkpoint bytes")
    if mp.get("ckpt_bytes") != 477531127:
        fail("runner-recorded checkpoint byte count")
    if mp.get("model_source_path") != str(VSRC / "diffusion_diagnostic_model.py"):
        fail(f"runner-recorded model source path {mp.get('model_source_path')}")
    receipt = {
        "label": "712-row exhaustive diagnostic, t=150, K=1; format-only closure, no inference in this step",
        "raw_result_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "raw_result_note": "raw execution output is NOT strict JSON (bare NaN for absent boundary cells); retained as the execution record only; the strict artifact is the authoritative result",
        "strict_result_sha256": hashlib.sha256(strict_text.encode()).hexdigest(),
        "converter_sha256": hashlib.sha256(finaliser_bytes).hexdigest(),
        "script_sha256": EXPECTED_SCRIPT, "model_source_sha256": EXPECTED_MODEL_SRC,
        "phase_g_init_sha256": EXPECTED_INIT, "checkpoint_sha256": EXPECTED_CKPT,
        "checkpoint_load_mode": S["model"].get("checkpoint_load_mode"),
        "development_take_root_blake3": DEV_ROOT_BLAKE3, "development_rows_present": n_raw,
        "development_content_manifest": {"path": str(DEV_MANIFEST), "sha256": DEV_MANIFEST_SHA,
                                         "inventory_sha256_without_self": DEV_MANIFEST_ROOT,
                                         "status": "CONTENT_VERIFIED", "entries": 712, "ordered": True,
                                         "note": "external content-verified manifest for the same take path; not evidence that the inference process hashed these bytes at runtime"},
        "verification_take_scope": "The v1 and v2 runners and this finaliser reference only the 712-row development path and do not enumerate, decode, hash, score or use any verification-take content. No bytes read from the verification tree were returned to any agent or pipeline; previously recorded local verification metadata did appear in retained output; process-level access remains UNKNOWN_POSSIBLE. No global claim that no process accessed the verification tree is made: see the separate local custody-incident report frozen by Codex on 2026-08-23 (an audit agent's unrestricted recursive search under [machine path redacted], disclosed at coord 17:01 UTC). The formal one-look was not claimed, opened or performed.",
        "custody_incident_record": {"json_path": str(INCIDENT_JSON), "json_sha256": INCIDENT_JSON_SHA,
                                    "markdown_companion_sha256": INCIDENT_MD_SHA,
                                    "note": "Codex record of 2026-08-23. No bytes read from the verification tree were returned to any agent or pipeline; previously recorded local verification metadata did appear in retained output; process-level path and byte access remain UNKNOWN_POSSIBLE."},
        "arm_denominators": denom,
        "recomputed": rec,
        "delta_wrong": {"primary_blocks_100x7_plus_12": [m, lo, hi], "sensitivity_blocks_89x8": [ms, los, his]},
        "delta_uncond": {"primary_blocks_100x7_plus_12": [mu, lou, hiu], "sensitivity_blocks_89x8": [msu, losu, hisu]},
        "per_timestep_150": S["per_timestep"]["150"],
        "elapsed_s": S["elapsed_s"], "device": S["device"], "torch": S["torch"],
        "claim_ceiling": "April verifier never fitted to this August take; coupling transfers to this take; uncond-below-correct has geometry or rig mismatch as a candidate explanation with August rig identity unconfirmed [confirm]; same person, same take, 712 dependent rows, descriptive.",
    }
    receipt_text = json.dumps(receipt, indent=1, allow_nan=False)
    json.loads(receipt_text, parse_constant=_reject_const)
    HANDOFF.mkdir(exist_ok=True)
    plan = [("20260823_bosun_phase_g_zeroshot_712row_exhaustive.strict.json", strict_text.encode()),
            ("20260823_bosun_phase_g_zeroshot_712row_exhaustive.raw_execution_output.json", raw_bytes),
            ("20260823_bosun_phase_g_zeroshot_712row_RECEIPT.json", receipt_text.encode()),
            ("20260823_bosun_run_zeroshot_v2.py", runner_bytes),
            ("20260823_bosun_finalize_v2.py", finaliser_bytes)]
    SUMS = "20260823_bosun_phase_g_zeroshot_712row_SHA256SUMS"  # written last: its absence marks an incomplete handoff
    for name, _ in plan + [(SUMS, b"")]:
        if (HANDOFF / name).exists() or (HANDOFF / (name + ".tmp")).exists():
            fail(f"no-clobber: {name} exists")
    for local in (STRICT, HERE / "zeroshot_v2_RECEIPT.json"):
        if local.exists():
            fail(f"no-clobber: {local.name} exists")
    manifest_lines = []
    for name, data in plan:
        tmp = HANDOFF / (name + ".tmp")
        with open(tmp, "xb") as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, HANDOFF / name)
        if sha(HANDOFF / name) != hashlib.sha256(data).hexdigest():
            fail(f"published copy mismatch {name}")
        manifest_lines.append(f"{hashlib.sha256(data).hexdigest()}  {name}")
    mtext = "\n".join(manifest_lines) + "\n"
    def atomic_write(path, data):
        tmp = path.with_name(path.name + ".tmp")
        with open(tmp, "xb") as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
        if sha(path) != hashlib.sha256(data).hexdigest():
            fail(f"write verify {path.name}")
    atomic_write(HANDOFF / SUMS, mtext.encode())
    atomic_write(STRICT, strict_text.encode())
    atomic_write(HERE / "zeroshot_v2_RECEIPT.json", receipt_text.encode())
    print(json.dumps(receipt, indent=1))


if __name__ == "__main__":
    main()
