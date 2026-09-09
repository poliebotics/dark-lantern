#!/usr/bin/env python3
"""Select the 2023 pairs to pull, from the archive manifests (local copies in control/).

Rules (desk brief, 2026-09-09):
  old_truth_beams: a session whose total manifest bytes are under 3 GB is pulled whole; otherwise a spaced 64-pair sample
                   (np.linspace over the indices that have both an emission and a report, rounded, unique).
  trailer 1682718815: every 4th index from 1 (1, 5, ..., 777) = 195 pairs.
Also pulls every agent_data log and receipt.txt (small) for pairing verification.
Writes selection_2023.json and pull_old_truth_beams.txt / pull_trailer.txt (rclone --files-from lists).
"""
import json, re, collections
import numpy as np

CTRL = "control"
sel = {"rules": __doc__, "sessions": {}}

def load_manifest(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    return rows

def index_of(relpath):
    m = re.match(r"(\d+)_", relpath.rsplit("/", 1)[1])
    return int(m.group(1)) if m else None

def build(rows, session):
    em, rp, extra = {}, {}, []
    for r in rows:
        parts = r["relative_path"].split("/")
        if parts[0] != session:
            continue
        if len(parts) >= 3 and parts[1] == "emissions" and parts[-1].endswith(".npy"):
            em[index_of(r["relative_path"])] = r
        elif len(parts) >= 3 and parts[1] == "reports" and parts[-1].endswith(".npy"):
            rp[index_of(r["relative_path"])] = r
        else:
            extra.append(r)
    common = sorted(set(em) & set(rp))
    return em, rp, common, extra

def pick(common, n):
    if len(common) <= n:
        return list(common)
    idx = np.unique(np.round(np.linspace(0, len(common) - 1, n)).astype(int))
    return [common[i] for i in idx]

# old_truth_beams
rows = load_manifest(f"{CTRL}/old_truth_beams/MANIFEST.jsonl")
bytes_by_session = collections.Counter()
for r in rows:
    bytes_by_session[r["relative_path"].split("/")[0]] += r["size"]
pull_old = []
for s in sorted(k for k in bytes_by_session if k != "_control"):
    em, rp, common, extra = build(rows, s)
    whole = bytes_by_session[s] < 3e9
    chosen = list(common) if whole else pick(common, 64)
    pairs = [{"index": i, "emission": em[i]["relative_path"], "report": rp[i]["relative_path"],
              "emission_sha256": em[i]["sha256"], "report_sha256": rp[i]["sha256"],
              "emission_size": em[i]["size"], "report_size": rp[i]["size"]} for i in chosen]
    sel["sessions"][s] = {"archive": "old_truth_beams", "session_bytes": bytes_by_session[s], "mode": "whole" if whole else "spaced_64",
                          "n_pairs_available": len(common), "n_pairs_selected": len(pairs), "index_min": common[0], "index_max": common[-1],
                          "pairs": pairs, "extra": [e["relative_path"] for e in extra],
                          "pull_bytes": sum(p["emission_size"] + p["report_size"] for p in pairs) + sum(e["size"] for e in extra)}
    for p in pairs:
        pull_old += [p["emission"], p["report"]]
    pull_old += [e["relative_path"] for e in extra]

# trailer
rows_t = load_manifest(f"{CTRL}/trailer/MANIFEST.jsonl")
s = "1682718815"
em, rp, common, extra = build(rows_t, s)
chosen = [i for i in common if (i - 1) % 4 == 0]
pairs = [{"index": i, "emission": em[i]["relative_path"], "report": rp[i]["relative_path"],
          "emission_sha256": em[i]["sha256"], "report_sha256": rp[i]["sha256"],
          "emission_size": em[i]["size"], "report_size": rp[i]["size"]} for i in chosen]
sel["sessions"][s] = {"archive": "truth_beam_poliepals_trailer", "session_bytes": sum(r["size"] for r in rows_t if r["relative_path"].startswith(s + "/")),
                      "mode": "every_4th_from_1", "n_pairs_available": len(common), "n_pairs_selected": len(pairs),
                      "index_min": common[0], "index_max": common[-1], "pairs": pairs, "extra": [e["relative_path"] for e in extra],
                      "pull_bytes": sum(p["emission_size"] + p["report_size"] for p in pairs) + sum(e["size"] for e in extra)}
pull_tr = []
for p in pairs:
    pull_tr += [p["emission"], p["report"]]
pull_tr += [e["relative_path"] for e in extra]

json.dump(sel, open("selection_2023.json", "w"), indent=1)
open("pull_old_truth_beams.txt", "w").write("\n".join(pull_old) + "\n")
open("pull_trailer.txt", "w").write("\n".join(pull_tr) + "\n")
tot = 0
for s, v in sel["sessions"].items():
    print(f"{s}: {v['mode']:16s} avail {v['n_pairs_available']:4d} idx {v['index_min']}..{v['index_max']} selected {v['n_pairs_selected']:4d} pull {v['pull_bytes']/1e9:.3f} GB extra {v['extra']}")
    tot += v["pull_bytes"]
print(f"total pull {tot/1e9:.2f} GB; files {len(pull_old)} + {len(pull_tr)}")
