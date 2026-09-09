#!/usr/bin/env python3
"""Verify the 2024 HDF5 copies in the other desk's read-only pull directory: wait until no .partial remains and each file
has the manifest size, then sha256 against _control/SHA256SUMS (six sessions) and RELEASE.json payload_sha256 (050046).
Writes verify_2024.json. Never modifies anything under the HDF5 directory."""
import hashlib, json, os, time, glob
C = os.environ.get("HDF5_2024_DIR", "hdf5_2024")
W = os.environ.get("COUPLING_PKG", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
expected = {}
for l in open(f"{C}/_control/SHA256SUMS"):
    h, p = l.split(); expected[p.split("/")[0]] = h
expected["20241219_050046"] = json.load(open(f"{C}/_control/RELEASE.json"))["existing_ipfs_packages"]["payload_sha256"]
SIZE = 5096765440
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()
res = {}
pending = set(expected)
while pending:
    for s in sorted(pending):
        p = f"{C}/{s}/data.h5"
        if glob.glob(f"{C}/{s}/*.partial") or not os.path.isfile(p):
            continue
        sz = os.path.getsize(p)
        if sz != SIZE:
            continue
        time.sleep(2)
        if os.path.getsize(p) != SIZE:
            continue
        h = sha(p)
        res[s] = {"path": p, "size": sz, "sha256": h, "expected": expected[s], "match": h == expected[s], "checked": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                  "expected_source": "RELEASE.json existing_ipfs_packages.payload_sha256" if s == "20241219_050046" else "_control/SHA256SUMS"}
        print(time.strftime("%H:%M:%SZ", time.gmtime()), s, "match" if res[s]["match"] else "MISMATCH", h, flush=True)
        pending.discard(s)
        json.dump(res, open(f"{W}/verify_2024.json", "w"), indent=1)
    if pending:
        time.sleep(30)
print("VERIFY2024_DONE", sum(r["match"] for r in res.values()), "of", len(res), "match")
