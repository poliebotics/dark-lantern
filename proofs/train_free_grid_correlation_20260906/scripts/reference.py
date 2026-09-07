#!/usr/bin/env python3
"""N7 integer positive (Astra's A' specification, 6 September 2026): exact 4x4 RGB cell-sum grids from the public pairs, the
signed per-channel Pearson bounds in integer arithmetic (S = 65536), the fixed examples (lexicographically first target of each
session in the seed-2026090601 map; mismatch = the emission whose recorded edge ends at that capture, i.e. the inverse map),
tau = 1/8 (retrospective), guard constants, expected public outputs. Pure Python integers throughout. Writes the frozen
SPEC_FREEZE.json (before any circuit work) and the grids/expected values for the two examples."""
import hashlib, json, math, os, sys, time
import numpy as np
from PIL import Image
PAIRS = 'n7_raw_20260906/pairs'; MAP = 'n7_raw_20260906/package/results/maps/random_seed2026090601.json'
PM = 'n7_raw_20260906/package/PAIRS_MANIFEST.json'; OUT = 'n7_integer_positive_20260906'
S = 65536; N = 16; MAXV = 37601280; TAU_NUM, TAU_DEN = 1, 8
Z_OFFSET = 3 * S  # 196608; z = Z_OFFSET + Q with Q in [-3S, 3S]
GUARD_MATCHED_MIN_Q = 24579   # Q_matched >= 3*S/8 + 3 : the mathematical mean correlation exceeds 1/8 despite the 1/S rounding per channel
GUARD_MISMATCH_MAX_Q = 24572  # Q_mismatch + 3 < 24576 : the mathematical mean correlation is below 1/8
sha = lambda b: hashlib.sha256(b).hexdigest(); fsha = lambda p: sha(open(p, 'rb').read())


def grid(path):
    a = np.asarray(Image.open(path).convert('RGB'), dtype=np.uint64)
    assert a.shape == (1152, 2048, 3), a.shape
    cells = a.reshape(4, 288, 4, 512, 3).sum(axis=(1, 3), dtype=np.uint64)  # 4x4 cells x RGB, row-major cells, interleaved RGB
    flat = [int(v) for v in cells.reshape(-1)]
    assert len(flat) == 48 and all(0 <= v <= MAXV for v in flat)
    return flat, a


def moments(x, y):
    sx, sy = sum(x), sum(y); sxx = sum(v * v for v in x); syy = sum(v * v for v in y); sxy = sum(u * v for u, v in zip(x, y))
    C = N * sxy - sx * sy; Vx = N * sxx - sx * sx; Vy = N * syy - sy * sy
    return C, Vx, Vy


def channel_q(C, Vx, Vy):
    """b, a, q with C = (1-2b) a, a >= 0, q = floor(S*|rho|) certified by q^2 P <= S^2 a^2 < (q+1)^2 P, P = Vx*Vy."""
    assert Vx > 0 and Vy > 0
    b = 1 if C < 0 else 0; a = abs(C); P = Vx * Vy
    q = math.isqrt(S * S * a * a // P)  # floor(sqrt(S^2 a^2 / P)) = floor(S |rho|)
    assert q * q * P <= S * S * a * a < (q + 1) * (q + 1) * P and 0 <= q <= S
    return b, a, q, P


def triplet(cap, em, ex):
    """Signed channel values for (capture, emission): Q = sum (1-2b) q; z = Z_OFFSET + Q; exact float Pearson for reference."""
    out = dict(channels=[], Q=0)
    for c in range(3):
        x = cap[c::3]; y = em[c::3]; C, Vx, Vy = moments(x, y); b, a, q, P = channel_q(C, Vx, Vy)
        rho = C / math.sqrt(Vx * Vy)
        out['channels'].append(dict(channel='RGB'[c], C=str(C), Vx=str(Vx), Vy=str(Vy), b=b, a=str(a), q=q, signed_q=(1 - 2 * b) * q, rho_exact=rho))
        out['Q'] += (1 - 2 * b) * q
    out['z'] = Z_OFFSET + out['Q']; out['mean_rho_exact'] = sum(ch['rho_exact'] for ch in out['channels']) / 3
    out['bound_check'] = abs(out['Q'] / (3 * S) - out['mean_rho_exact']) < 1 / S
    return out


def main():
    t0 = time.time(); os.makedirs(OUT, exist_ok=True)
    M = json.load(open(MAP)); pm = json.load(open(PM)); by_name = {p['name']: p for p in pm['pairs']}
    examples = {}
    for s in ('d2', 'v10'):
        sm = M[s]; target = min(sm['targets']); donor = sm['targets'][sm['partners'].index(target)]  # inverse map: the recorded edge E_donor -> B_target
        examples[s] = dict(target=target, mismatch_emission=donor, directed_edge='recorded N7 edge E_donor -> B_target (map inverted at the target capture)')
    spec = dict(schema='n7-integer-positive-spec/v1', frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), status='retrospective engineering demonstration on public data; tau chosen after inspecting the two examples',
                statistic='per-channel Pearson correlation of 4x4 RGB cell sums (each cell 512x288 pixels of the 2048x1152 pair image; equal areas so identical to cell-mean correlation), mean over channels',
                grid=dict(rows=4, cols=4, channels=3, order='row-major cells, interleaved RGB', cell_pixels=147456, value_bits=26, max_value=MAXV), S=S, N=N, tau=f'{TAU_NUM}/{TAU_DEN}',
                z_offset=Z_OFFSET, guards=dict(Q_matched_min=GUARD_MATCHED_MIN_Q, Q_mismatch_max=GUARD_MISMATCH_MAX_Q, z_matched_min=Z_OFFSET + GUARD_MATCHED_MIN_Q, z_mismatch_max=Z_OFFSET + GUARD_MISMATCH_MAX_Q),
                error_bound='|Q/(3S) - mean_rho| < 1/S', selection_rule='lexicographically first target of each session in the seed-2026090601 random map; mismatch emission by inverting the map at that target',
                map_path=MAP.replace('', ''), map_sha256=fsha(MAP), pairs_manifest_sha256=fsha(PM), examples=examples,
                commitment=dict(hash='Poseidon(11) from circomlib', tag_domain='BOSUN_N7_G4_SUM_V1', roles={'capture': 0, 'matched_emission': 1, 'recorded_mismatch': 2}, packing='nine 26-bit values per field word, 6 words (last holds 3)',
                                inputs='manifest_hi128, manifest_lo128, nonce_role, 48, tag_role, p0..p5'))
    json.dump(spec, open(os.path.join(OUT, 'SPEC_FREEZE.json'), 'w'), indent=1)
    data = {}
    for s, ex in examples.items():
        cap, cap_arr = grid(os.path.join(PAIRS, 'test_B', ex['target'])); em, em_arr = grid(os.path.join(PAIRS, 'test_A', ex['target'])); mis, mis_arr = grid(os.path.join(PAIRS, 'test_A', ex['mismatch_emission']))
        for role, name, arr in (('capture', ex['target'], cap_arr), ('matched_emission', ex['target'], em_arr), ('recorded_mismatch', ex['mismatch_emission'], mis_arr)):
            side = 'test_B' if role == 'capture' else 'test_A'; rec = by_name[name]
            assert sha(np.ascontiguousarray(arr.astype(np.uint8)).tobytes()) == rec[f"pair_{'B' if side == 'test_B' else 'A'}_pixels_sha256"], (role, name)
        tm, tx = triplet(cap, em, ex), triplet(cap, mis, ex)
        ok = tm['Q'] >= GUARD_MATCHED_MIN_Q and tx['Q'] <= GUARD_MISMATCH_MAX_Q
        data[s] = dict(example=ex, grids=dict(capture=cap, matched_emission=em, recorded_mismatch=mis),
                       grid_digests={k: sha(np.array(v, dtype='<u4').tobytes()) for k, v in dict(capture=cap, matched_emission=em, recorded_mismatch=mis).items()},
                       source=dict(capture=dict(file=ex['target'], side='test_B', png_sha256=by_name[ex['target']]['pair_B_sha256'], pixels_sha256=by_name[ex['target']]['pair_B_pixels_sha256']),
                                   matched_emission=dict(file=ex['target'], side='test_A', png_sha256=by_name[ex['target']]['pair_A_sha256'], pixels_sha256=by_name[ex['target']]['pair_A_pixels_sha256']),
                                   recorded_mismatch=dict(file=ex['mismatch_emission'], side='test_A', png_sha256=by_name[ex['mismatch_emission']]['pair_A_sha256'], pixels_sha256=by_name[ex['mismatch_emission']]['pair_A_pixels_sha256'])),
                       matched=tm, mismatch=tx, guards_satisfied=ok)
        print(f"{s}: target {ex['target']} mismatch {ex['mismatch_emission']} | matched Q {tm['Q']} z {tm['z']} rho {tm['mean_rho_exact']:.12f} | mismatch Q {tx['Q']} z {tx['z']} rho {tx['mean_rho_exact']:.12f} | guards {ok} | signed q matched {[c['signed_q'] for c in tm['channels']]} mismatch {[c['signed_q'] for c in tx['channels']]}")
    json.dump(data, open(os.path.join(OUT, 'EXAMPLES.json'), 'w'), indent=1)
    print(f'spec frozen {fsha(os.path.join(OUT, "SPEC_FREEZE.json"))} in {time.time() - t0:.1f} s')


if __name__ == '__main__':
    main()
