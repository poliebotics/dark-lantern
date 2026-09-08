#!/usr/bin/env python3
"""Stage the G1 FINAL differential boundary fixtures (g1_integer/final/fixtures/) for the Rust tests: copy every
fixture JSON verbatim and unpack every npz array into a raw little-endian .bin beside it (Rust reads JSON and raw
bytes only). Every JSON's sha256 is checked against the fixtures manifest, every unpacked array's sha256 against the
hash the fixture declares for it. Output: g2_guest/fixtures_final/ with index.json.
"""
import hashlib, json, shutil
from pathlib import Path
import numpy as np

G2 = Path(__file__).resolve().parent.parent
SRC = (G2.parent / "g1_integer" if (G2.parent / "g1_integer").is_dir() else G2.parent / "oracle") / "final" / "fixtures"   # published layout (Astra r6 finding 8)
OUT = G2 / "fixtures_final"
OUT.mkdir(exist_ok=True)
man = json.load(open(SRC / "manifest.json"))
index = {"source": str(SRC), "manifest_sha256": hashlib.sha256(open(SRC / "manifest.json", "rb").read()).hexdigest(),
         "checkpoint_sha256": man["checkpoint_sha256"], "fixtures": {}}
shutil.copy(SRC / "manifest.json", OUT / "manifest.json")
for name in man["fixtures"]:
    jf = SRC / f"{name}.json"
    raw = jf.read_bytes()
    h = hashlib.sha256(raw).hexdigest()
    assert man["files"][f"{name}.json"] == h, (name, "json hash")
    (OUT / f"{name}.json").write_bytes(raw)
    d = json.loads(raw)
    entry = {"json_sha256": h, "kernel": d["kernel"], "arrays": {}}
    if d.get("npz"):
        z = np.load(SRC / d["npz"])
        declared = {}
        for sec in ("inputs", "expected"):
            for k, v in d[sec].items():
                if isinstance(v, dict) and "npz_key" in v:
                    declared[v["npz_key"]] = v
        for key in z.files:
            a = z[key]
            dt = declared[key]["dtype"] if key in declared else None
            if dt == "<i2" or a.dtype == np.int16:
                b = np.ascontiguousarray(a.astype("<i2")).tobytes(); dtype = "i16"
            elif dt == "u1" or a.dtype == np.uint8 or a.dtype == np.bool_:
                b = np.ascontiguousarray(a.astype("u1")).tobytes(); dtype = "u8"
            elif a.dtype == np.int64:
                b = np.ascontiguousarray(a.astype("<i8")).tobytes(); dtype = "i64"
            else:
                raise SystemExit(f"{name}: unexpected dtype {a.dtype} for {key}")
            hb = hashlib.sha256(b).hexdigest()
            if key in declared:
                assert declared[key]["sha256"] == hb, (name, key, "array hash")
                assert list(a.shape) == declared[key]["shape"], (name, key, "shape")
            fname = f"{name}__{key}.bin"
            (OUT / fname).write_bytes(b)
            entry["arrays"][key] = {"file": fname, "dtype": dtype, "shape": list(a.shape), "sha256": hb}
    index["fixtures"][name] = entry
json.dump(index, open(OUT / "index.json", "w"), indent=1)
print(f"staged {len(index['fixtures'])} fixtures to {OUT}; arrays: {sum(len(e['arrays']) for e in index['fixtures'].values())}")
