#!/usr/bin/env python3
"""Export the G1 FINAL August guest inputs (g1_integer/final/august_inputs/row_NNNNNN.npz) as raw int16 LE files.

  noise_august/noise_{r:06d}.i16      the NORMATIVE noise target and noising input (README_FINAL.md section 5),
                                      86,016 bytes each; the batch driver reads this directory (--noise-dir)
  august_inputs_i16/row_{r:06d}_{C_int,Ct_int,E_correct[,E_wrong]}.i16   for the cross-checks against the guest
  noise_august/MANIFEST.json          sha256 per file, asserted equal to G1's manifest hash for that array, plus the
                                      byte comparison with the earlier proposal set (vectors_relation/august/noise_proposal)
"""
import hashlib, json
from pathlib import Path
import numpy as np

G2 = Path(__file__).resolve().parent.parent
SRC = (G2.parent / "g1_integer" if (G2.parent / "g1_integer").is_dir() else G2.parent / "oracle") / "final" / "august_inputs"   # published layout (Astra r6 finding 8)
NOISE = G2 / "noise_august"
INP = G2 / "august_inputs_i16"
PROP = G2 / "vectors_relation" / "august" / "noise_proposal"
NOISE.mkdir(exist_ok=True); INP.mkdir(exist_ok=True)
g1 = json.load(open(SRC / "manifest.json"))
files, same_as_proposal, differ = {}, 0, []
for r in range(600, 712):
    rec = g1["rows"][str(r)]
    z = np.load(SRC / rec["file"])
    for key in ("C_int", "noise_int", "Ct_int", "E_correct", "E_wrong"):
        if key not in z.files:
            continue
        a = z[key]
        assert a.dtype == np.int16, (r, key, a.dtype)
        raw = np.ascontiguousarray(a.astype("<i2")).tobytes()
        h = hashlib.sha256(raw).hexdigest()
        assert h == rec["sha256"][key], (r, key, h, rec["sha256"][key])
        if key == "noise_int":
            assert len(raw) == 86016
            p = NOISE / f"noise_{r:06d}.i16"
            p.write_bytes(raw)
            prop = PROP / f"noise_{r:06d}.i16"
            if prop.is_file():
                if prop.read_bytes() == raw:
                    same_as_proposal += 1
                else:
                    differ.append(r)
            files[p.name] = {"sha256": h, "bytes": len(raw), "row": r, "g1_noise_call_index": rec["noise_call_index"]}
        else:
            (INP / f"row_{r:06d}_{key}.i16").write_bytes(raw)
man = {"artifact": "normative August noise for the proof set, exported byte for byte from g1_integer/final/august_inputs (G1 FINAL)",
       "source_manifest": str(SRC / "manifest.json"), "checkpoint_sha256": g1["checkpoint_sha256"],
       "noise_derivation": g1["noise_derivation"], "rows": 112,
       "proposal_set_comparison": {"dir": str(PROP), "identical_files": same_as_proposal, "differing_rows": differ},
       "files": files}
(NOISE / "MANIFEST.json").write_text(json.dumps(man, indent=1) + "\n")
print(f"wrote {len(files)} noise files; identical to the proposal set: {same_as_proposal}/112, differing rows {differ}")
print("also wrote", len(list(INP.glob('*.i16'))), "input files to", INP)
