#!/usr/bin/env python3
"""Merge the BATCH_MANIFEST.json files of several zkdiff-batch processes (one per GPU, disjoint --rows ranges) into
one manifest sorted by row (Astra r5 finding 9: strict).

The merger REFUSES (exit 1, nothing written unless --allow-incomplete):
  * inputs that disagree on the guest ELF, vkey, circuit version, circuit key, constants blob, spec digests, session
    (id, root, context, chain log, row count) or rule text;
  * a row present twice with different public values / proof hashes;
  * a collection that does not cover exactly the 112 rows 600..711 once each;
  * any row that is not `proved` with `acceptance.accepted == true`;
  * a stale manifest entry: the receipt.json, the proof artifact and the public-values file named by the entry must
    exist beside the manifest and hash to what the entry says (--no-files skips this when merging away from the run
    directory).
With --allow-incomplete the merged file is still written, but with `complete: false`, the missing / failed rows
listed, and the status is 1, so a pipeline that forgot the flag cannot mistake a partial set for the proof set.
Nothing is inherited blindly from the first input: every carried field is one the inputs were checked to agree on.

usage: merge_batch_manifests.py OUT.json IN1/BATCH_MANIFEST.json IN2/BATCH_MANIFEST.json ... [--allow-incomplete] [--no-files]
"""
import hashlib, json, os, sys
from collections import Counter
from pathlib import Path

REQUIRED_ROWS = list(range(600, 712))


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def die(msg):
    print(f"MERGE REFUSED: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    allow_incomplete = "--allow-incomplete" in sys.argv
    check_files = "--no-files" not in sys.argv
    if len(args) < 2:
        die(__doc__)
    out_path, inputs = args[0], args[1:]
    mans = []
    for p in inputs:
        m = json.load(open(p))
        if m.get("schema") != "zbdiff-batch/v3":
            die(f"{p}: schema {m.get('schema')!r} is not zbdiff-batch/v3")
        mans.append((p, m))

    def agree(getter, name):
        vals = {json.dumps(getter(m), sort_keys=True) for _, m in mans}
        if len(vals) != 1:
            die(f"inputs disagree on {name}: {sorted(vals)}")
        return getter(mans[0][1])

    agreed = {
        "guest_elf_sha256": agree(lambda m: m["guest_elf_sha256"], "guest_elf_sha256"),
        "guest_elf_bytes": agree(lambda m: m["guest_elf_bytes"], "guest_elf_bytes"),
        "sp1_vkey": agree(lambda m: m.get("sp1_vkey"), "sp1_vkey"),
        "sp1_circuit_version": agree(lambda m: m.get("sp1_circuit_version"), "sp1_circuit_version"),
        "groth16_vk_sha256": agree(lambda m: m.get("groth16_vk_sha256"), "groth16_vk_sha256"),
        "preprocess_spec_sha256": agree(lambda m: m["preprocess_spec_sha256"], "preprocess_spec_sha256"),
        "denoiser": agree(lambda m: {k: m["denoiser"][k] for k in ("kind", "constants_sha256", "spec_sha256", "constants_blob_bytes")}, "denoiser identity"),
        "session": agree(lambda m: {k: m["session"][k] for k in ("name", "session_id", "row_count", "chain_log_blake3", "context_digest", "ordered_session_root")}, "session"),
        "rule_text": agree(lambda m: m["rule"]["text"], "rule text"),
        "rule": agree(lambda m: {k: m["rule"][k] for k in ("row_start", "offsets", "offset_formula", "rule_constants_row_start", "rule_constants_row_end_inclusive")}, "rule constants"),
        "expected_identities": agree(lambda m: m.get("expected_identities"), "expected_identities"),
        "noise_rule": agree(lambda m: m["noise"]["rule"], "noise rule"),
        "mode": agree(lambda m: m["mode"], "mode"),
    }
    if agreed["mode"] != "prove":
        die(f"inputs are {agreed['mode']} manifests, not prove manifests")
    if agreed["expected_identities"] is None:
        die("inputs carry no expected_identities: proofs were not accepted against the frozen table")

    rows, problems, stale = {}, [], []
    for p, m in mans:
        base = Path(p).parent
        for e in m["rows"]:
            r = e["row"]
            if r in rows:
                a = rows[r]
                for k in ("public_values_sha256", "proof_sha256", "r_correct", "r_wrong", "offset", "wrong_row", "offset_rule"):
                    if a.get(k) != e.get(k):
                        die(f"row {r} appears in {a['source_manifest']} and {p} with different {k}")
                problems.append(f"row {r} appears in two inputs ({a['source_manifest']}, {p}); kept the first")
                continue
            e = dict(e, source_manifest=p)
            if e.get("status") != "proved":
                problems.append(f"row {r}: status {e.get('status')} ({e.get('error', '')[:120]})")
            elif not (e.get("acceptance") or {}).get("accepted"):
                problems.append(f"row {r}: proved but not accepted ({(e.get('acceptance') or {}).get('failed_check')})")
            elif check_files:
                rd = base / f"row_{r:06d}"
                receipt = rd / "receipt.json"
                if not receipt.is_file():
                    stale.append(f"row {r}: receipt.json missing under {rd}")
                else:
                    rj = json.load(open(receipt))
                    if rj.get("public_values_sha256") != e.get("public_values_sha256") or rj.get("proof_sha256") != e.get("proof_sha256") or rj.get("attempt_id") != e.get("attempt_id"):
                        stale.append(f"row {r}: receipt.json disagrees with the manifest entry (stale collection)")
                pf = Path(e.get("proof_file", ""))
                if not pf.is_absolute():
                    pf = rd / pf.name
                if not pf.is_file():
                    stale.append(f"row {r}: proof file {pf} missing")
                elif sha256_file(pf) != e.get("proof_sha256") or pf.stat().st_size != e.get("proof_bytes"):
                    stale.append(f"row {r}: proof file {pf} hash/size differs from the manifest entry")
                pv = Path(e.get("public_values_file", ""))
                if not pv.is_absolute():
                    pv = rd / pv.name
                if not pv.is_file():
                    stale.append(f"row {r}: public values file {pv} missing")
                elif sha256_file(pv) != e.get("public_values_sha256"):
                    stale.append(f"row {r}: public values file {pv} differs from the manifest entry")
            rows[r] = e
    missing = [r for r in REQUIRED_ROWS if r not in rows]
    extra = sorted(r for r in rows if r not in REQUIRED_ROWS)
    if missing:
        problems.append(f"missing rows: {missing}")
    if extra:
        problems.append(f"rows outside 600..711: {extra}")
    problems.extend(stale)
    complete = not problems and len(rows) == 112

    entries = [rows[r] for r in sorted(rows)]
    counts = Counter(e["status"] for e in entries)
    outcomes = Counter(e.get("outcome_class", "n/a") for e in entries)
    accepted = sum(1 for e in entries if (e.get("acceptance") or {}).get("accepted"))
    mirrored = sorted({r for _, m in mans for r in m["rule"].get("mirrored_rows_in_this_run", [])})
    merged = {
        "schema": "zbdiff-batch/v3-merged",
        "complete": complete,
        "problems": problems,
        "merged_from": [{"path": p, "sha256": sha256_file(p), "attempt_id": m.get("attempt_id"), "host": m.get("host"), "prover_name": m.get("prover_name"), "cuda_device_id": m.get("cuda_device_id"), "rows_processed": m["rule"]["rows_processed"], "complete": m.get("complete")} for p, m in mans],
        "required_rows": REQUIRED_ROWS, "rows_required": 112, "rows_unique": len(rows), "rows_proved_and_accepted": accepted,
        "status_counts": dict(counts), "outcome_counts": dict(outcomes),
        "mirrored_rows": mirrored,
        "rule": dict(agreed["rule"], text=agreed["rule_text"]),
        "session": agreed["session"], "denoiser": agreed["denoiser"], "noise_rule": agreed["noise_rule"],
        "guest_elf_sha256": agreed["guest_elf_sha256"], "guest_elf_bytes": agreed["guest_elf_bytes"], "sp1_vkey": agreed["sp1_vkey"],
        "sp1_circuit_version": agreed["sp1_circuit_version"], "groth16_vk_sha256": agreed["groth16_vk_sha256"], "preprocess_spec_sha256": agreed["preprocess_spec_sha256"],
        "expected_identities": agreed["expected_identities"],
        "files_checked": check_files,
        "rows": entries,
        "elapsed_ms_max": max(m.get("elapsed_ms", 0) for _, m in mans),
    }
    if not complete and not allow_incomplete:
        for pr in problems:
            print(f"  {pr}", file=sys.stderr)
        die(f"collection is not the complete accepted proof set ({len(rows)} unique rows, {accepted} proved+accepted); pass --allow-incomplete to write a partial merge marked complete=false")
    tmp = out_path + ".pending"
    with open(tmp, "w") as f:
        json.dump(merged, f, indent=1)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, out_path)
    print(f"merged {len(entries)} rows from {len(inputs)} manifests -> {out_path}; complete={complete}; status {dict(counts)}; outcomes {dict(outcomes)}; accepted {accepted}/112; problems {len(problems)}")
    sys.exit(0 if complete else 1)


if __name__ == "__main__":
    main()
