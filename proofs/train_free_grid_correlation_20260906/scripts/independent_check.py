#!/usr/bin/env python3
"""Independent replay for the N7 integer positive, runnable from the package root (python3 scripts/independent_check.py) or from the
working directory. Checks, with a code path separate from reference.py: (1) the six source PNGs' file and decoded-RGB SHA-256 against
the pairs manifest and RECEIPT; (2) the 4x4 cell-sum grids recomputed from the PNGs against the frozen openings in EXAMPLES.json and
the witness inputs, and their canonical uint32-little-endian digests; (3) the exact signed channel quotients and z values against the
public signals; (4) the commitments reconstructed from the disclosed nonces and grids through the shipped witness generator against
ROOTS.json and the public signals; (5) both proofs with snarkjs against the shipped verification key. SNARKJS may point at an
independent snarkjs 0.7.6 (default: the `snarkjs` on PATH). Exit 0 only if everything agrees."""
import hashlib, json, math, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == 'scripts' else HERE
SNARK = os.environ.get('SNARKJS', 'snarkjs').split(); S = 65536
def P(*a): return os.path.join(ROOT, *a)
def sha(b): return hashlib.sha256(b).hexdigest()
spec = json.load(open(P('SPEC_FREEZE.json'))); ex = json.load(open(P('EXAMPLES.json'))); roots = json.load(open(P('ROOTS.json'))); receipt = json.load(open(P('RECEIPT.json')))
pm = json.load(open(P('fixtures', 'PAIRS_MANIFEST.json'))); by_name = {p['name']: p for p in pm['pairs']}
mdig = int.from_bytes(hashlib.sha256(open(P('MANIFEST.json'), 'rb').read()).digest(), 'big')
fails = []
def check(name, ok, detail=''):
    print(('ok  ' if ok else 'FAIL'), name, detail); (ok or fails.append(name))
def grid(path):
    im = Image.open(path).convert('RGB'); assert im.size == (2048, 1152); px = np.asarray(im).astype(np.int64); out = []
    for r in range(4):
        for c in range(4):
            block = px[r * 288:(r + 1) * 288, c * 512:(c + 1) * 512, :]
            for ch in range(3):
                out.append(int(block[:, :, ch].sum()))
    return out, sha(np.asarray(im).tobytes())
def signed_q(x, y):
    n = 16; sx = sum(x); sy = sum(y); C = n * sum(a * b for a, b in zip(x, y)) - sx * sy; Vx = n * sum(a * a for a in x) - sx * sx; Vy = n * sum(b * b for b in y) - sy * sy
    assert Vx > 0 and Vy > 0; Pxy = Vx * Vy; q = math.isqrt(S * S * C * C // Pxy); assert q * q * Pxy <= S * S * C * C < (q + 1) * (q + 1) * Pxy
    return (-1 if C < 0 else 1) * q
# manifest hash pin
check('MANIFEST.json sha256 equals RESULTS/RECEIPT pin', sha(open(P('MANIFEST.json'), 'rb').read()) == receipt['manifest_sha256'], receipt['manifest_sha256'][:16])
check('SPEC_FREEZE.json sha256 equals the manifest pin', sha(open(P('SPEC_FREEZE.json'), 'rb').read()) == json.load(open(P('MANIFEST.json')))['spec_freeze_sha256'])
for s, e in spec['examples'].items():
    src = ex[s]['source']; grids = {}
    for role, (side, fname) in dict(capture=('test_B', e['target']), matched_emission=('test_A', e['target']), recorded_mismatch=('test_A', e['mismatch_emission'])).items():
        path = P('fixtures', side, fname); fb = open(path, 'rb').read()
        rec = by_name[fname]; want_png = rec['pair_B_sha256'] if side == 'test_B' else rec['pair_A_sha256']; want_px = rec['pair_B_pixels_sha256'] if side == 'test_B' else rec['pair_A_pixels_sha256']
        g, pxsha = grid(path)
        check(f'{s} {role}: PNG sha256 equals the pairs manifest and RECEIPT', sha(fb) == want_png == src[role]['png_sha256'], fname)
        check(f'{s} {role}: decoded RGB sha256 equals the pairs manifest and RECEIPT', pxsha == want_px == src[role]['pixels_sha256'])
        check(f'{s} {role}: recomputed grid equals the frozen opening', g == ex[s]['grids'][role])
        check(f'{s} {role}: canonical grid digest equals EXAMPLES/RECEIPT', sha(np.array(g, dtype='<u4').tobytes()) == ex[s]['grid_digests'][role] == receipt['examples'][s]['grid_digests_uint32_le'][role])
        grids[role] = g
    inp = json.load(open(P('build', f'{s}_main_input.json')))
    check(f'{s}: witness input grids equal the recomputed grids', [int(v) for v in inp['cap']] == grids['capture'] and [int(v) for v in inp['em']] == grids['matched_emission'] and [int(v) for v in inp['mis']] == grids['recorded_mismatch'])
    check(f'{s}: witness nonces equal ROOTS.json', [inp['nonce_cap'], inp['nonce_em'], inp['nonce_mis']] == roots['roots'][s]['nonces'])
    Qm = sum(signed_q(grids['capture'][c::3], grids['matched_emission'][c::3]) for c in range(3)); Qx = sum(signed_q(grids['capture'][c::3], grids['recorded_mismatch'][c::3]) for c in range(3))
    pub = json.load(open(P('build', f'{s}_main_public.json')))
    check(f'{s}: recomputed z values equal the public signals', int(pub[3]) == 196608 + Qm and int(pub[4]) == 196608 + Qx, f'{196608 + Qm} {196608 + Qx}')
    check(f'{s}: public manifest halves equal SHA-256(MANIFEST.json)', int(pub[5]) == mdig >> 128 and int(pub[6]) == mdig & ((1 << 128) - 1))
    check(f'{s}: guards hold on the public z values', int(pub[3]) >= 221187 and int(pub[4]) <= 221180)
    # commitments reconstructed from the disclosed openings through the shipped witness generator
    with tempfile.TemporaryDirectory() as td:
        r = subprocess.run(['node', P('build', 'n7_triplet_js', 'generate_witness.js'), P('build', 'n7_triplet_js', 'n7_triplet.wasm'), P('build', f'{s}_main_input.json'), f'{td}/w.wtns'], capture_output=True, text=True)
        ok = r.returncode == 0
        if ok:
            r2 = subprocess.run(SNARK + ['wtns', 'export', 'json', f'{td}/w.wtns', f'{td}/w.json'], capture_output=True, text=True); w = json.load(open(f'{td}/w.json')) if r2.returncode == 0 else None
            ok = w is not None and w[1:4] == [roots['roots'][s]['commitments'][k] for k in ('capture', 'matched_emission', 'recorded_mismatch')] and w[1:4] == pub[0:3]
        check(f'{s}: commitments reconstructed from the openings equal ROOTS.json and the public signals', ok, (r.stderr or '')[-120:])
    r = subprocess.run(SNARK + ['plonk', 'verify', P('build', 'verification_key.json'), P('build', f'{s}_main_public.json'), P('build', f'{s}_main_proof.json')], capture_output=True, text=True)
    check(f'{s}: proof verifies with the shipped verification key', 'OK!' in r.stdout, (r.stdout + r.stderr).strip()[-80:])
check('verification key sha256 equals RECEIPT pin', sha(open(P('build', 'verification_key.json'), 'rb').read()) == receipt['circuit']['verification_key_sha256'])
print('INDEPENDENT CHECK', 'PASS' if not fails else f'FAIL ({len(fails)}: {fails[:3]})'); sys.exit(0 if not fails else 1)
