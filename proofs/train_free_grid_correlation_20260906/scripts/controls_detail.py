#!/usr/bin/env python3
"""Rerun the witness-layer controls capturing the actual assertion message and circuit line (the first record kept only truncated
stack tails). Writes CONTROLS_DETAIL.json; the original CONTROLS.json is kept as the first-run record."""
import json, secrets, subprocess, sys, time
sys.path.insert(0, 'n7_integer_positive_20260906')
from pipeline import witness_inputs, B, O
from reference import MAXV
EX = json.load(open(f'{O}/EXAMPLES.json')); ROOTS = json.load(open(f'{O}/ROOTS.json')); m_hi, m_lo = int(ROOTS['manifest_hi']), int(ROOTS['manifest_lo'])
g = EX['d2']['grids']; cap, em, mis = g['capture'], g['matched_emission'], g['recorded_mismatch']
def attempt(name, c, e, x, override=None, zero=False):
    if zero:
        inp = dict(manifest_hi=str(m_hi), manifest_lo=str(m_lo), cap=['0'] * 48, em=['0'] * 48, mis=['0'] * 48, nonce_cap='1', nonce_em='2', nonce_mis='3', vinv_cap=['0'] * 3, vinv_em=['0'] * 3, vinv_mis=['0'] * 3, b_m=[0, 0, 0], a_m=['0'] * 3, q_m=[0, 0, 0], b_x=[0, 0, 0], a_x=['0'] * 3, q_x=[0, 0, 0])
    else:
        inp = witness_inputs(c, e, x, m_hi, m_lo, [secrets.randbits(128) for _ in range(3)], override=override)
    ip = f'{B}/detail_{name}.json'; json.dump(inp, open(ip, 'w'))
    r = subprocess.run(['node', f'{B}/n7_triplet_js/generate_witness.js', f'{B}/n7_triplet_js/n7_triplet.wasm', ip, f'{B}/detail_{name}.wtns'], capture_output=True, text=True)
    text = r.stdout + r.stderr; line = next((l.strip() for l in text.splitlines() if 'Assert Failed' in l), '')
    where = next((l.strip() for l in text.splitlines() if 'line:' in l.lower() or 'template' in l.lower()), '')
    return dict(control=name, returncode=r.returncode, assertion=line[:200], circuit_location=where[:300], stderr_tail=text.strip()[-700:], failed_at_witness=(r.returncode != 0 and 'Assert Failed' in text))
out = [attempt('donor_in_matched_role', cap, mis, mis), attempt('emissions_exchanged', cap, mis, em), attempt('complement_matched_emission', cap, [MAXV - v for v in em], mis),
       attempt('constant_zero_grids_circuit', None, None, None, zero=True)]
for d, nm in ((1, 'quotient_witness_plus_one'), (-1, 'quotient_witness_minus_one')):
    def qo(inp, d=d):
        inp['q_m'] = [inp['q_m'][0] + d, inp['q_m'][1], inp['q_m'][2]]
    out.append(attempt(nm, cap, em, mis, override=qo))
def big_val(inp):
    inp['cap'][0] = str(1 << 26)
out.append(attempt('grid_value_2_pow_26', cap, em, mis, override=big_val))
def big_nonce(inp):
    inp['nonce_cap'] = str(1 << 128)
out.append(attempt('nonce_2_pow_128', cap, em, mis, override=big_nonce))
def wrong_sign(inp):
    inp['b_m'] = [1 - inp['b_m'][0], inp['b_m'][1], inp['b_m'][2]]
out.append(attempt('wrong_covariance_sign', cap, em, mis, override=wrong_sign))
json.dump(dict(schema='n7-integer-positive-controls-detail/v1', run_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), note='rerun of the witness-layer controls with the assertion message and circuit location retained; CONTROLS.json is the first-run record', controls=out, all_failed_at_witness=all(o['failed_at_witness'] for o in out)), open(f'{O}/CONTROLS_DETAIL.json', 'w'), indent=1)
for o in out:
    print(('ok  ' if o['failed_at_witness'] else 'BAD '), o['control'], '|', o['assertion'][:90], '|', o['circuit_location'][-60:])
print('all failed at witness:', all(o['failed_at_witness'] for o in out))
