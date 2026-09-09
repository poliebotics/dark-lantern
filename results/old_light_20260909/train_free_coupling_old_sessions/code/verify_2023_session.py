#!/usr/bin/env python3
"""Verify the selected files of one or more 2023 sessions against the archive manifest (sha256). Exit 1 on any failure."""
import hashlib, json, os, sys
W = os.environ.get("COUPLING_PKG", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); D = os.environ.get("NPY_2023_DIR", "npy_2023")
sel = json.load(open(f"{W}/selection_2023.json"))["sessions"]
man = {}
for arch, path in (("old_truth_beams", f"{W}/control/old_truth_beams/MANIFEST.jsonl"), ("truth_beam_poliepals_trailer", f"{W}/control/trailer/MANIFEST.jsonl")):
    for l in open(path):
        if l.strip():
            r = json.loads(l); man[(arch, r["relative_path"])] = r
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""): h.update(b)
    return h.hexdigest()
bad = 0
for s in sys.argv[1:]:
    v = sel[s]; arch = v["archive"]; ok = 0; n = 0
    for p in v["pairs"]:
        for rel in (p["emission"], p["report"]):
            n += 1; dst = f"{D}/{arch}/{rel}"; r = man[(arch, rel)]
            if os.path.isfile(dst) and os.path.getsize(dst) == r["size"] and sha(dst) == r["sha256"]:
                ok += 1
            else:
                bad += 1
    print(f"{s}: {ok}/{n} selected files verified", flush=True)
sys.exit(1 if bad else 0)
